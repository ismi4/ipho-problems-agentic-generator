"""OpenAI client wrapper: prices actual usage, enforces budget, logs every call."""

from __future__ import annotations

import base64
import json
import time
import uuid
from pathlib import Path
from typing import Any

from openai import OpenAI

from .budget import Budget, CallRecord

PRICES_PATH = Path(__file__).with_name("prices.json")


def load_prices() -> dict[str, dict[str, float]]:
    data = json.loads(PRICES_PATH.read_text())
    return data["per_million_tokens"]


def price_usage(model: str, usage: Any, prices: dict[str, dict[str, float]]) -> tuple[float, dict[str, int]]:
    p = prices[model]
    input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    details = getattr(usage, "prompt_tokens_details", None)
    cached = int(getattr(details, "cached_tokens", 0) or 0) if details else 0
    cdet = getattr(usage, "completion_tokens_details", None)
    reasoning = int(getattr(cdet, "reasoning_tokens", 0) or 0) if cdet else 0
    uncached = max(0, input_tokens - cached)
    cost = (
        uncached * p["input"]
        + cached * p.get("cached_input", p["input"])
        + output_tokens * p["output"]
    ) / 1_000_000.0
    return cost, {
        "input_tokens": input_tokens,
        "cached_tokens": cached,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning,
    }


class TrackedClient:
    def __init__(self, budget: Budget, batch_mode: bool = False):
        self.client = OpenAI()
        self.budget = budget
        self.prices = load_prices()
        self.batch_mode = batch_mode  # if True, apply 50% discount to reported cost (S1)

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        purpose: str,
        response_format: dict[str, Any] | None = None,
        max_completion_tokens: int = 4096,
        reasoning_effort: str | None = "medium",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.budget.check()
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_completion_tokens": max_completion_tokens,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format
        # gpt-5.x family accepts reasoning_effort on chat completions for reasoning models
        if reasoning_effort is not None:
            kwargs["reasoning_effort"] = reasoning_effort

        t0 = time.time()
        last_err: Exception | None = None
        resp = None
        for attempt in range(6):
            try:
                resp = self.client.chat.completions.create(**kwargs)
                last_err = None
                break
            except TypeError:
                # Older SDK / model combo may reject reasoning_effort
                kwargs.pop("reasoning_effort", None)
                continue
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                if response_format is not None and "response_format" in msg and attempt == 0:
                    kwargs.pop("response_format", None)
                    continue
                # Retry transient rate limits; do not spin on insufficient_quota
                if "insufficient_quota" in msg:
                    raise
                if "rate_limit" in msg or "429" in msg:
                    time.sleep(min(60, 2 ** attempt))
                    continue
                raise
        if resp is None:
            assert last_err is not None
            raise last_err
        elapsed = time.time() - t0

        cost, toks = price_usage(model, resp.usage, self.prices)
        if self.batch_mode:
            cost *= 0.5
        call_id = str(uuid.uuid4())
        self.budget.record(
            CallRecord(
                call_id=call_id,
                model=model,
                purpose=purpose,
                cost_usd=cost,
                meta={**(meta or {}), "elapsed_s": elapsed, "batch_discounted": self.batch_mode},
                **toks,
            )
        )
        content = resp.choices[0].message.content or ""
        return {
            "call_id": call_id,
            "model": model,
            "content": content,
            "cost_usd": cost,
            "usage": toks,
            "elapsed_s": elapsed,
            "raw": resp,
        }


def encode_image_png(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def image_message_parts(image_paths: list[Path], detail: str = "high") -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = []
    for p in image_paths:
        b64 = encode_image_png(p)
        parts.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}", "detail": detail},
            }
        )
    return parts
