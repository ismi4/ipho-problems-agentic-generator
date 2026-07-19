"""Solution A — Model right-sizing & cascading (lever: WHICH model).

A.V0  single strong-model call (gpt-5), full context.
A.V1  cheap-first cascade: nano verifies first; escalate to strong when the
      nano verifier's self-reported confidence is below a threshold.
A.V2  calibrated router: a cheap heuristic gate routes intrinsically-hard
      sub-parts (dimensionless / qualitative deliverables) straight to strong,
      plus early-exit on high-confidence nano verdicts. Threshold tuned on dev.
"""
from __future__ import annotations

from typing import Any

from verifier.common.base import run_full_solution
from verifier.common.client import STRONG_MODEL, NANO_MODEL
from verifier.common.schema import Verdict


class AV0:
    name = "A.V0"
    solution, version = "A", "V0"

    def verify(self, client, instance, problem, rubric) -> Verdict:
        return run_full_solution(
            client, STRONG_MODEL, problem, rubric, instance["candidate_solution"],
            reasoning_effort="medium", instance_id=instance["id"], step="A.V0",
        )


class AV1:
    name = "A.V1"
    solution, version = "A", "V1"

    def __init__(self, conf_threshold: float = 0.85):
        self.conf_threshold = conf_threshold

    def verify(self, client, instance, problem, rubric) -> Verdict:
        v = run_full_solution(
            client, NANO_MODEL, problem, rubric, instance["candidate_solution"],
            reasoning_effort="low", instance_id=instance["id"], step="A.V1:nano",
        )
        if v.confidence >= self.conf_threshold:
            return v
        return run_full_solution(
            client, STRONG_MODEL, problem, rubric, instance["candidate_solution"],
            reasoning_effort="medium", instance_id=instance["id"], step="A.V1:escalate",
        )


class AV2:
    name = "A.V2"
    solution, version = "A", "V2"

    def __init__(self, conf_threshold: float = 0.9):
        self.conf_threshold = conf_threshold

    @staticmethod
    def _has_hard_subpart(problem: dict[str, Any]) -> bool:
        return any(sp["kind"] in ("qualitative", "dimensionless_numeric")
                   for sp in problem["subparts"])

    def verify(self, client, instance, problem, rubric) -> Verdict:
        # Calibrated router: nano verifies first; escalate to strong only when
        #   (a) nano confidence is below the (dev-tuned) threshold, OR
        #   (b) nano returns ACCEPT on a problem with an intrinsically-hard
        #       sub-part (dimensionless/qualitative) -- the false-accept risk the
        #       naive mini-swap gets wrong. Confident cheap REJECTs are trusted,
        #       which is where most of the savings come from.
        v = run_full_solution(
            client, NANO_MODEL, problem, rubric, instance["candidate_solution"],
            reasoning_effort="low", instance_id=instance["id"], step="A.V2:nano",
        )
        needs_accept_guard = v.verdict == "ACCEPT" and self._has_hard_subpart(problem)
        if v.confidence >= self.conf_threshold and not needs_accept_guard:
            return v
        return run_full_solution(
            client, STRONG_MODEL, problem, rubric, instance["candidate_solution"],
            reasoning_effort="medium", instance_id=instance["id"], step="A.V2:escalate",
        )
