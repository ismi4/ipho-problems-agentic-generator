"""Solution B — Deterministic-check offload (lever: WHETHER to call a model).

B.V0  single strong-model call does everything, including arithmetic/dimensional/
      symbolic reasoning in-prompt.
B.V1  Tier-0 deterministic falsifiers (Pint units/dimension + numeric tolerance)
      short-circuit obvious rejects for ~$0 before any LLM call; otherwise a
      single strong-model call resolves the rest.
B.V2  add Tier-1 symbolic checks (SymPy equivalence). Machine-checkable sub-parts
      are resolved deterministically; the LLM (cheapest adequate = nano) is invoked
      ONLY on the Tier-2 escalation set (qualitative deliverables / parse failures).
"""
from __future__ import annotations

import time

from verifier.common.base import aggregate_subparts, run_full_solution, run_subpart
from verifier.common.client import STRONG_MODEL, NANO_MODEL
from verifier.common.deterministic import check_subpart, FAIL, PASS, ESCALATE
from verifier.common.schema import Verdict


class BV0:
    name = "B.V0"
    solution, version = "B", "V0"

    def verify(self, client, instance, problem, rubric) -> Verdict:
        return run_full_solution(
            client, STRONG_MODEL, problem, rubric, instance["candidate_solution"],
            reasoning_effort="medium", emphasize_arithmetic=True,
            instance_id=instance["id"], step="B.V0",
        )


class BV1:
    name = "B.V1"
    solution, version = "B", "V1"

    def verify(self, client, instance, problem, rubric) -> Verdict:
        t0 = time.process_time()
        for sp in problem["subparts"]:
            cand = instance["subpart_answers"][sp["id"]]
            r = check_subpart(sp, cand, tier0_only=True)
            if r.outcome == FAIL:
                client.log_deterministic(
                    instance_id=instance["id"], step=f"B.V1:tier0:{sp['id']}",
                    cpu_s=time.process_time() - t0,
                    detail={"outcome": r.outcome, "reason": r.detail},
                )
                return Verdict.reject(f"Tier-0 falsifier: {sp['id']} {r.detail}")
        client.log_deterministic(
            instance_id=instance["id"], step="B.V1:tier0-pass",
            cpu_s=time.process_time() - t0, detail={"outcome": "no-tier0-reject"},
        )
        # Tier-0 found no obvious reject -> one strong LLM call for the rest.
        return run_full_solution(
            client, STRONG_MODEL, problem, rubric, instance["candidate_solution"],
            reasoning_effort="medium", instance_id=instance["id"], step="B.V1:llm",
        )


class BV2:
    name = "B.V2"
    solution, version = "B", "V2"

    def verify(self, client, instance, problem, rubric) -> Verdict:
        t0 = time.process_time()
        subpart_results: dict[str, dict] = {}
        escalate = []
        for sp in problem["subparts"]:
            cand = instance["subpart_answers"][sp["id"]]
            r = check_subpart(sp, cand, tier0_only=False)
            client.log_deterministic(
                instance_id=instance["id"], step=f"B.V2:det:{sp['id']}",
                cpu_s=r.cpu_s, detail={"outcome": r.outcome, "method": r.method,
                                       "reason": r.detail},
            )
            if r.outcome == FAIL:
                return Verdict.reject(f"Deterministic falsifier: {sp['id']} {r.detail}")
            if r.outcome == PASS:
                subpart_results[sp["id"]] = {
                    "passed": True, "points_est": sp["points"],
                    "reason": f"deterministic {r.method}: {r.detail}", "confidence": 1.0}
            else:  # ESCALATE
                escalate.append(sp)
        # LLM only on the Tier-2 escalation set (cheapest adequate model = nano).
        for sp in escalate:
            cand = instance["subpart_answers"][sp["id"]]
            subpart_results[sp["id"]] = run_subpart(
                client, NANO_MODEL, problem, rubric, sp, cand,
                reasoning_effort="low", use_cache_prefix=True,
                instance_id=instance["id"],
            )
        return aggregate_subparts(problem, subpart_results)
