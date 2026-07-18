"""Solution C — Context & decoding efficiency (lever: HOW efficiently you call
the SAME model). The model tier is held fixed (strong = gpt-5) across V0/V1/V2 so
savings are attributable purely to context/decoding efficiency, not model swaps.

C.V0  full problem + full solution context, HIGH reasoning_effort, ONE LLM call
      PER sub-part, verbose.
C.V1  context PRUNING (only the sub-part + its reference, boilerplate stripped) +
      Structured Outputs, MEDIUM reasoning_effort.
C.V2  prompt CACHING of the shared problem/rubric prefix across the sub-part calls
      (static prefix placed first) + LOW reasoning_effort. (Batch API would add a
      further ~50% discount for the offline sweep; see report.)
"""
from __future__ import annotations

from verifier.common.base import aggregate_subparts, run_subpart
from verifier.common.client import STRONG_MODEL
from verifier.common.schema import Verdict


class CV0:
    name = "C.V0"
    solution, version = "C", "V0"

    def verify(self, client, instance, problem, rubric) -> Verdict:
        results = {}
        for sp in problem["subparts"]:
            cand = instance["subpart_answers"][sp["id"]]
            results[sp["id"]] = run_subpart(
                client, STRONG_MODEL, problem, rubric, sp, cand,
                reasoning_effort="high", use_cache_prefix=False, prune_context=False,
                instance_id=instance["id"],
            )
        return aggregate_subparts(problem, results)


class CV1:
    name = "C.V1"
    solution, version = "C", "V1"

    def verify(self, client, instance, problem, rubric) -> Verdict:
        results = {}
        for sp in problem["subparts"]:
            cand = instance["subpart_answers"][sp["id"]]
            results[sp["id"]] = run_subpart(
                client, STRONG_MODEL, problem, rubric, sp, cand,
                reasoning_effort="medium", prune_context=True,
                instance_id=instance["id"],
            )
        return aggregate_subparts(problem, results)


class CV2:
    name = "C.V2"
    solution, version = "C", "V2"

    def verify(self, client, instance, problem, rubric) -> Verdict:
        results = {}
        # Shared static prefix placed first in every call -> automatic prompt
        # caching yields discounted cached-input tokens after the first call.
        for sp in problem["subparts"]:
            cand = instance["subpart_answers"][sp["id"]]
            results[sp["id"]] = run_subpart(
                client, STRONG_MODEL, problem, rubric, sp, cand,
                reasoning_effort="low", use_cache_prefix=True,
                instance_id=instance["id"],
            )
        return aggregate_subparts(problem, results)
