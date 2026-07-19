"""Process-wide OpenAI spend tracker with a hard abort cap."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class CallRecord:
    call_id: str
    model: str
    purpose: str
    input_tokens: int
    cached_tokens: int
    output_tokens: int
    reasoning_tokens: int
    cost_usd: float
    meta: dict[str, Any] = field(default_factory=dict)


class Budget:
    def __init__(self, hard_cap_usd: float = 25.0, log_path: Path | None = None):
        self.hard_cap_usd = hard_cap_usd
        self._lock = threading.Lock()
        self.spent_usd = 0.0
        self.calls: list[CallRecord] = []
        self.log_path = log_path
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if not log_path.exists():
                log_path.write_text("")

    def remaining(self) -> float:
        return self.hard_cap_usd - self.spent_usd

    def check(self, projected_extra: float = 0.0) -> None:
        if self.spent_usd + projected_extra >= self.hard_cap_usd:
            raise BudgetExceeded(
                f"OpenAI spend would reach ${self.spent_usd + projected_extra:.4f} "
                f"(hard cap ${self.hard_cap_usd:.2f})"
            )

    def record(self, rec: CallRecord) -> None:
        with self._lock:
            if self.spent_usd + rec.cost_usd > self.hard_cap_usd + 1e-9:
                # Still record the overshooting call for audit, then abort.
                self.spent_usd += rec.cost_usd
                self.calls.append(rec)
                self._append_log(rec)
                raise BudgetExceeded(
                    f"OpenAI spend hit ${self.spent_usd:.4f} after call {rec.call_id} "
                    f"(hard cap ${self.hard_cap_usd:.2f})"
                )
            self.spent_usd += rec.cost_usd
            self.calls.append(rec)
            self._append_log(rec)

    def _append_log(self, rec: CallRecord) -> None:
        if not self.log_path:
            return
        with self.log_path.open("a") as f:
            f.write(json.dumps(rec.__dict__, default=str) + "\n")

    def summary(self) -> dict[str, Any]:
        by_model: dict[str, float] = {}
        by_purpose: dict[str, float] = {}
        for c in self.calls:
            by_model[c.model] = by_model.get(c.model, 0.0) + c.cost_usd
            by_purpose[c.purpose] = by_purpose.get(c.purpose, 0.0) + c.cost_usd
        return {
            "hard_cap_usd": self.hard_cap_usd,
            "spent_usd": round(self.spent_usd, 6),
            "remaining_usd": round(self.remaining(), 6),
            "n_calls": len(self.calls),
            "by_model_usd": {k: round(v, 6) for k, v in by_model.items()},
            "by_purpose_usd": {k: round(v, 6) for k, v in by_purpose.items()},
            "input_tokens": sum(c.input_tokens for c in self.calls),
            "cached_tokens": sum(c.cached_tokens for c in self.calls),
            "output_tokens": sum(c.output_tokens for c in self.calls),
            "reasoning_tokens": sum(c.reasoning_tokens for c in self.calls),
        }
