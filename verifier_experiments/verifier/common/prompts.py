"""Shared prompt skeletons. The SAME skeleton is reused across a solution's
V0/V1/V2 (only the improvement under test changes) to avoid inflated baselines.

The verifier is given: problem statement + reference answer key (rubric) +
candidate solution. It is BLIND to the gold label / injected fault.
"""
from __future__ import annotations

from typing import Any

SYSTEM = (
    "You are an expert IPhO (International Physics Olympiad) mechanics grader acting as an "
    "automated solution VERIFIER inside a problem-generation pipeline. You are given a "
    "problem, an official reference answer key (full marks), and a candidate solution. "
    "Judge whether the candidate is CORRECT: each sub-part's final answer must be "
    "algebraically equivalent to the reference (up to the sanctioned approximation), with "
    "correct dimensions, sign/direction, and units where numeric. A single wrong sub-part "
    "makes the whole solution REJECT. Grade blind and be rigorous but fair. "
    "Return ONLY the requested JSON."
)


def full_solution_user_prompt(
    problem_statement: str, rubric: str, candidate: str, *, emphasize_arithmetic: bool = False
) -> str:
    extra = ""
    if emphasize_arithmetic:
        extra = (
            "\nDo ALL checking yourself in-prompt: verify dimensions, units, signs, numeric "
            "values within tolerance, and symbolic equivalence to the reference by hand.\n"
        )
    return (
        f"PROBLEM:\n{problem_statement}\n\n"
        f"REFERENCE ANSWER KEY (full marks):\n{rubric}\n\n"
        f"CANDIDATE SOLUTION TO VERIFY:\n{candidate}\n"
        f"{extra}\n"
        "Emit a JSON verdict with: verdict (ACCEPT/REJECT), quality_score in [0,1] "
        "(fraction of marks the candidate earns), per_subpart (id, passed, points_est, "
        "reason), first_point_of_failure (sub-part id or null), and confidence in [0,1]."
    )


def subpart_static_prefix(problem_statement: str, rubric: str) -> str:
    """Static prefix (problem + full rubric) shared across per-sub-part calls.

    Placed FIRST so OpenAI automatic prompt caching can reuse it across the many
    sub-part calls of the same problem/instance (Solution C.V2)."""
    return (
        f"PROBLEM (shared context):\n{problem_statement}\n\n"
        f"REFERENCE ANSWER KEY (full marks, shared):\n{rubric}\n"
    )


def subpart_user_prompt(
    subpart_id: str,
    subpart_statement: str,
    reference_answer_text: str,
    candidate_answer_text: str,
    *,
    static_prefix: str | None = None,
    pruned_context: str | None = None,
) -> str:
    header = static_prefix if static_prefix is not None else (pruned_context or "")
    return (
        f"{header}\n"
        f"Verify ONLY sub-part [{subpart_id}]: {subpart_statement}\n"
        f"Reference answer: {reference_answer_text}\n"
        f"Candidate answer: {candidate_answer_text}\n\n"
        "Is the candidate sub-part answer correct (equivalent to reference, correct "
        "dimensions/units/sign)? Emit JSON: passed (bool), points_est (number), reason "
        "(string), confidence in [0,1]."
    )


def answer_text(ans: dict[str, Any]) -> str:
    t = ans.get("type")
    if t == "symbolic":
        return ans["expr"]
    if t == "numeric":
        return f"{ans['value']} {ans.get('unit','')}".strip() or str(ans["value"])
    if t == "qualitative":
        return ans["desc"]
    return str(ans)
