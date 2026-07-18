"""Composed best system (bonus) — stack the three orthogonal levers.

B: deterministic Tier-0/1 resolves every machine-checkable sub-part for ~$0.
C: for the residual escalation set, use pruned context + a cached shared prefix.
A: on that set, verify cheap-first (nano) and escalate to strong only on low
   confidence.
"""
from __future__ import annotations

import time

from verifier.common.base import aggregate_subparts, run_subpart
from verifier.common.client import STRONG_MODEL, NANO_MODEL
from verifier.common.deterministic import check_subpart, FAIL, PASS
from verifier.common.schema import Verdict


class Composed:
    name = "composed"
    solution, version = "composed", "ABC"

    def __init__(self, conf_threshold: float = 0.9):
        self.conf_threshold = conf_threshold

    def verify(self, client, instance, problem, rubric) -> Verdict:
        t0 = time.process_time()
        results: dict[str, dict] = {}
        escalate = []
        for sp in problem["subparts"]:
            cand = instance["subpart_answers"][sp["id"]]
            r = check_subpart(sp, cand, tier0_only=False)  # B lever
            client.log_deterministic(
                instance_id=instance["id"], step=f"composed:det:{sp['id']}",
                cpu_s=r.cpu_s, detail={"outcome": r.outcome, "reason": r.detail},
            )
            if r.outcome == FAIL:
                return Verdict.reject(f"Deterministic falsifier: {sp['id']} {r.detail}")
            if r.outcome == PASS:
                results[sp["id"]] = {"passed": True, "points_est": sp["points"],
                                     "reason": f"deterministic {r.method}", "confidence": 1.0}
            else:
                escalate.append(sp)
        for sp in escalate:  # C lever (cached prefix) + A lever (cheap-first)
            cand = instance["subpart_answers"][sp["id"]]
            r = run_subpart(client, NANO_MODEL, problem, rubric, sp, cand,
                            reasoning_effort="low", use_cache_prefix=True,
                            instance_id=instance["id"])
            if float(r.get("confidence", 0.0)) < self.conf_threshold:
                r = run_subpart(client, STRONG_MODEL, problem, rubric, sp, cand,
                                reasoning_effort="medium", use_cache_prefix=True,
                                instance_id=instance["id"])
            results[sp["id"]] = r
        return aggregate_subparts(problem, results)
