"""Cost computation from actual OpenAI usage records + pinned price table.

cost = input_tokens*price_in + cached_input_tokens*price_cached_in
       + output_tokens*price_out
where output_tokens already INCLUDES reasoning tokens (OpenAI bills reasoning
tokens as output). We store reasoning/cached breakdowns for transparency.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

_PRICES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "prices.json")


@lru_cache(maxsize=1)
def load_prices(path: str | None = None) -> dict[str, Any]:
    with open(path or _PRICES_PATH) as f:
        return json.load(f)


@dataclass
class Usage:
    """Normalized usage record extracted from an OpenAI response."""

    model: str
    prompt_tokens: int = 0
    cached_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    batch: bool = False

    @property
    def uncached_prompt_tokens(self) -> int:
        return max(0, self.prompt_tokens - self.cached_tokens)


def usage_from_response(resp: Any, model: str, batch: bool = False) -> Usage:
    """Extract a normalized Usage from a Chat Completions response object."""
    u = getattr(resp, "usage", None)
    if u is None:
        return Usage(model=model, batch=batch)
    prompt = getattr(u, "prompt_tokens", 0) or 0
    completion = getattr(u, "completion_tokens", 0) or 0
    cached = 0
    reasoning = 0
    ptd = getattr(u, "prompt_tokens_details", None)
    if ptd is not None:
        cached = getattr(ptd, "cached_tokens", 0) or 0
    ctd = getattr(u, "completion_tokens_details", None)
    if ctd is not None:
        reasoning = getattr(ctd, "reasoning_tokens", 0) or 0
    return Usage(
        model=model,
        prompt_tokens=prompt,
        cached_tokens=cached,
        completion_tokens=completion,
        reasoning_tokens=reasoning,
        batch=batch,
    )


def cost_of(usage: Usage, prices: dict[str, Any] | None = None) -> float:
    """USD cost of a single usage record from the pinned price table."""
    prices = prices or load_prices()
    m = prices["models"].get(usage.model)
    if m is None:
        # Unknown model: cost 0 but do not crash (deterministic checks etc.).
        return 0.0
    if usage.batch:
        p_in, p_cached, p_out = m["batch_in"], m["batch_cached_in"], m["batch_out"]
    else:
        p_in, p_cached, p_out = m["in"], m["cached_in"], m["out"]
    cost = (
        usage.uncached_prompt_tokens * p_in
        + usage.cached_tokens * p_cached
        + usage.completion_tokens * p_out
    ) / 1_000_000.0
    return cost
