"""Base helpers shared by verifier configurations."""
from __future__ import annotations

from typing import Any

from .client import LLMClient, parse_verdict_text
from .prompts import (
    SYSTEM,
    answer_text,
    full_solution_user_prompt,
    subpart_static_prefix,
    subpart_user_prompt,
)
from .schema import SUBPART_JSON_SCHEMA, VERDICT_JSON_SCHEMA, Verdict


def run_full_solution(
    client: LLMClient,
    model: str,
    problem: dict[str, Any],
    rubric: str,
    candidate: str,
    *,
    reasoning_effort: str | None = None,
    emphasize_arithmetic: bool = False,
    instance_id: str | None = None,
    step: str = "full",
) -> Verdict:
    """One structured full-solution verification call -> Verdict."""
    messages = [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": full_solution_user_prompt(
                problem["statement"], rubric, candidate,
                emphasize_arithmetic=emphasize_arithmetic,
            ),
        },
    ]
    res = client.chat(
        model=model,
        messages=messages,
        json_schema=VERDICT_JSON_SCHEMA,
        reasoning_effort=reasoning_effort,
        instance_id=instance_id,
        step=step,
    )
    return Verdict.from_dict(parse_verdict_text(res.text))


def run_subpart(
    client: LLMClient,
    model: str,
    problem: dict[str, Any],
    rubric: str,
    subpart: dict[str, Any],
    cand_answer: dict[str, Any],
    *,
    reasoning_effort: str | None = None,
    use_cache_prefix: bool = False,
    prune_context: bool = False,
    instance_id: str | None = None,
) -> dict[str, Any]:
    """Verify one sub-part -> {passed, points_est, reason, confidence}."""
    if prune_context:
        header = f"PROBLEM CONTEXT (pruned to this sub-part): {problem['title']}."
        prompt = subpart_user_prompt(
            subpart["id"], subpart["statement"],
            answer_text(subpart["answer"]), answer_text(cand_answer),
            pruned_context=header,
        )
    elif use_cache_prefix:
        prefix = subpart_static_prefix(problem["statement"], rubric)
        prompt = subpart_user_prompt(
            subpart["id"], subpart["statement"],
            answer_text(subpart["answer"]), answer_text(cand_answer),
            static_prefix=prefix,
        )
    else:
        prefix = subpart_static_prefix(problem["statement"], rubric)
        prompt = subpart_user_prompt(
            subpart["id"], subpart["statement"],
            answer_text(subpart["answer"]), answer_text(cand_answer),
            static_prefix=prefix,
        )
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": prompt},
    ]
    res = client.chat(
        model=model,
        messages=messages,
        json_schema=SUBPART_JSON_SCHEMA,
        reasoning_effort=reasoning_effort,
        instance_id=instance_id,
        step=f"subpart:{subpart['id']}",
    )
    return parse_verdict_text(res.text)


def aggregate_subparts(problem: dict[str, Any], subpart_results: dict[str, dict]) -> Verdict:
    """Combine per-sub-part results into an instance-level Verdict.

    ACCEPT iff every sub-part passed; quality_score = fraction of points earned.
    """
    total_pts = sum(sp["points"] for sp in problem["subparts"])
    earned = 0.0
    per = []
    all_pass = True
    fpof = None
    confs = []
    for sp in problem["subparts"]:
        r = subpart_results.get(sp["id"], {"passed": False, "points_est": 0.0,
                                            "reason": "missing", "confidence": 0.0})
        passed = bool(r.get("passed", False))
        pts = sp["points"] if passed else 0.0
        earned += pts
        confs.append(float(r.get("confidence", 0.5)))
        per.append({"id": sp["id"], "passed": passed,
                    "points_est": float(r.get("points_est", pts)),
                    "reason": str(r.get("reason", ""))})
        if not passed and all_pass:
            all_pass = False
            fpof = sp["id"]
    return Verdict.from_dict({
        "verdict": "ACCEPT" if all_pass else "REJECT",
        "quality_score": earned / total_pts if total_pts else 0.0,
        "per_subpart": per,
        "first_point_of_failure": fpof,
        "confidence": sum(confs) / len(confs) if confs else 0.5,
    })
