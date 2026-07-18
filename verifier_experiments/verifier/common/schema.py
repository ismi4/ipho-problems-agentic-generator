"""Structured verdict schema shared by all verifier configurations.

The verifier is run BLIND (never shown the gold label). Its job: given
(problem_statement, candidate_solution) emit a structured verdict.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


# JSON schema handed to OpenAI Structured Outputs (response_format=json_schema).
# `strict` mode requires: every property listed in `required`, additionalProperties=false.
VERDICT_JSON_SCHEMA: dict[str, Any] = {
    "name": "verifier_verdict",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "verdict": {"type": "string", "enum": ["ACCEPT", "REJECT"]},
            "quality_score": {
                "type": "number",
                "description": "Normalized earned-marks estimate in [0,1].",
            },
            "per_subpart": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "id": {"type": "string"},
                        "passed": {"type": "boolean"},
                        "points_est": {"type": "number"},
                        "reason": {"type": "string"},
                    },
                    "required": ["id", "passed", "points_est", "reason"],
                },
            },
            "first_point_of_failure": {
                "type": ["string", "null"],
                "description": "Sub-part id or short phrase where the solution first fails; null if ACCEPT.",
            },
        },
        "required": [
            "verdict",
            "quality_score",
            "per_subpart",
            "first_point_of_failure",
        ],
    },
}


@dataclass
class SubpartVerdict:
    id: str
    passed: bool
    points_est: float
    reason: str


@dataclass
class Verdict:
    verdict: str  # "ACCEPT" | "REJECT"
    quality_score: float
    per_subpart: list[SubpartVerdict] = field(default_factory=list)
    first_point_of_failure: str | None = None

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Verdict":
        subs = [SubpartVerdict(**s) for s in d.get("per_subpart", []) or []]
        v = str(d.get("verdict", "REJECT")).upper()
        if v not in ("ACCEPT", "REJECT"):
            v = "REJECT"
        qs = d.get("quality_score", 0.0)
        try:
            qs = float(qs)
        except (TypeError, ValueError):
            qs = 0.0
        qs = max(0.0, min(1.0, qs))
        return Verdict(
            verdict=v,
            quality_score=qs,
            per_subpart=subs,
            first_point_of_failure=d.get("first_point_of_failure"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def reject(reason: str, quality_score: float = 0.0) -> "Verdict":
        return Verdict(
            verdict="REJECT",
            quality_score=quality_score,
            per_subpart=[],
            first_point_of_failure=reason,
        )

    @staticmethod
    def accept(quality_score: float = 1.0) -> "Verdict":
        return Verdict(
            verdict="ACCEPT",
            quality_score=quality_score,
            per_subpart=[],
            first_point_of_failure=None,
        )
