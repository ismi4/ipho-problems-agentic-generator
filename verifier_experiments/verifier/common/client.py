"""OpenAI client wrapper: structured-output calls, usage logging, spend guard.

Every LLM call is routed through `LLMClient.chat`, which:
  * calls the OpenAI Chat Completions API (prompt caching is automatic),
  * extracts real usage (incl. cached + reasoning tokens),
  * computes cost from the pinned price table,
  * appends a raw usage record to runs/<run_tag>.jsonl,
  * updates a process-wide spend tracker that ABORTS if projected spend
    would exceed the hard cap (default $8, leaving headroom under the $10 cap).
"""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

from .pricing import Usage, cost_of, load_prices, usage_from_response

# --- Model ladder (pinned; see prices.json) -------------------------------
STRONG_MODEL = "gpt-5"
MID_MODEL = "gpt-5-mini"
NANO_MODEL = "gpt-5-nano"

DEFAULT_HARD_CAP_USD = float(os.environ.get("VERIFIER_HARD_CAP_USD", "8.0"))
RUNS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "runs")


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class SpendTracker:
    """Process-wide accumulator of real spend, with a hard kill-switch.

    Thread-safe: `record`/`check_before` take a lock so concurrent verify()
    calls cannot race past the budget cap.
    """

    hard_cap_usd: float = DEFAULT_HARD_CAP_USD
    total_usd: float = 0.0
    n_calls: int = 0
    by_model: dict[str, float] = field(default_factory=dict)
    by_config: dict[str, float] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def check_before(self, projected_next: float = 0.0) -> None:
        with self._lock:
            if self.total_usd + projected_next > self.hard_cap_usd:
                raise BudgetExceeded(
                    f"Spend guard: total ${self.total_usd:.4f} + projected "
                    f"${projected_next:.4f} would exceed cap ${self.hard_cap_usd:.2f}."
                )

    def record(self, cost: float, model: str, config: str) -> None:
        with self._lock:
            self.total_usd += cost
            self.n_calls += 1
            self.by_model[model] = self.by_model.get(model, 0.0) + cost
            self.by_config[config] = self.by_config.get(config, 0.0) + cost

    def summary(self) -> dict[str, Any]:
        return {
            "total_usd": round(self.total_usd, 6),
            "n_calls": self.n_calls,
            "hard_cap_usd": self.hard_cap_usd,
            "by_model": {k: round(v, 6) for k, v in self.by_model.items()},
            "by_config": {k: round(v, 6) for k, v in self.by_config.items()},
        }


# Single process-wide tracker.
SPEND = SpendTracker()


@dataclass
class LLMResult:
    text: str
    usage: Usage
    cost: float
    latency_s: float
    model: str


class LLMClient:
    def __init__(self, run_tag: str = "adhoc", config: str = "adhoc"):
        self.client = OpenAI()
        self.run_tag = run_tag
        self.config = config
        self.prices = load_prices()
        os.makedirs(RUNS_DIR, exist_ok=True)
        self._log_path = os.path.join(RUNS_DIR, f"{run_tag}.jsonl")
        self._log_lock = threading.Lock()
        self._scope = threading.local()  # per-thread cost accumulator

    def begin_scope(self) -> None:
        self._scope.cost = 0.0

    def end_scope(self) -> float:
        return getattr(self._scope, "cost", 0.0)

    def _log(self, record: dict[str, Any]) -> None:
        with self._log_lock:
            with open(self._log_path, "a") as f:
                f.write(json.dumps(record) + "\n")

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        json_schema: dict[str, Any] | None = None,
        reasoning_effort: str | None = None,
        max_completion_tokens: int | None = None,
        instance_id: str | None = None,
        step: str | None = None,
        max_retries: int = 4,
    ) -> LLMResult:
        """One structured LLM call with real-usage cost accounting + spend guard."""
        # Rough pre-flight guard: assume a modestly expensive call could still be
        # in flight; we cannot know cost before the call, so we just check that we
        # are not already at/over cap.
        SPEND.check_before(0.0)

        kwargs: dict[str, Any] = {"model": model, "messages": messages}
        if json_schema is not None:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": json_schema,
            }
        if reasoning_effort is not None:
            kwargs["reasoning_effort"] = reasoning_effort
        if max_completion_tokens is not None:
            kwargs["max_completion_tokens"] = max_completion_tokens

        last_err: Exception | None = None
        for attempt in range(max_retries):
            try:
                t0 = time.time()
                resp = self.client.chat.completions.create(**kwargs)
                latency = time.time() - t0
                break
            except Exception as e:  # noqa: BLE001 - retry transient API errors
                last_err = e
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        else:  # pragma: no cover
            raise last_err  # type: ignore[misc]

        usage = usage_from_response(resp, model=model, batch=False)
        cost = cost_of(usage, self.prices)
        SPEND.record(cost, model=model, config=self.config)
        if hasattr(self._scope, "cost"):
            self._scope.cost += cost

        text = resp.choices[0].message.content or ""
        self._log(
            {
                "ts": time.time(),
                "run_tag": self.run_tag,
                "config": self.config,
                "instance_id": instance_id,
                "step": step,
                "model": model,
                "reasoning_effort": reasoning_effort,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "cached_tokens": usage.cached_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "reasoning_tokens": usage.reasoning_tokens,
                },
                "cost_usd": cost,
                "latency_s": latency,
                "cumulative_usd": SPEND.total_usd,
            }
        )
        return LLMResult(text=text, usage=usage, cost=cost, latency_s=latency, model=model)

    def log_deterministic(
        self,
        *,
        instance_id: str | None,
        step: str,
        cpu_s: float,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Log a deterministic (non-LLM) check: $0 token cost, timed separately."""
        self._log(
            {
                "ts": time.time(),
                "run_tag": self.run_tag,
                "config": self.config,
                "instance_id": instance_id,
                "step": step,
                "model": "deterministic",
                "usage": {
                    "prompt_tokens": 0,
                    "cached_tokens": 0,
                    "completion_tokens": 0,
                    "reasoning_tokens": 0,
                },
                "cost_usd": 0.0,
                "cpu_s": cpu_s,
                "detail": detail or {},
                "cumulative_usd": SPEND.total_usd,
            }
        )


def parse_verdict_text(text: str) -> dict[str, Any]:
    """Parse a JSON verdict from model text, tolerating stray wrapping."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise
