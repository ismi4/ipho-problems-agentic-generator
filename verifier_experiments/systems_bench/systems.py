"""S1 / S2 / S3 verifier implementations per SYSTEMS.md §4."""

from __future__ import annotations

import json
import re
from typing import Any

from .client import TrackedClient
from .deterministic import SUBPARTS, run_deterministic

JUDGE_SCHEMA_HINT = """
Return ONLY JSON:
{
  "subpart_id": "A.1",
  "answer_type": "numeric_with_units|symbolic|dimensionless_exponent|show_that|other",
  "governing_law_identified": "...",
  "regime_assumed": "...",
  "dimensional_check": "pass|fail|unknown",
  "case_branches_found": ["..."],
  "refutation": "one concrete falsifying instance, or null if none found",
  "first_point_of_failure": null or short string,
  "verdict": "PASS|FAIL|UNCERTAIN",
  "confidence": 0.0,
  "escalate": false,
  "escalate_reason": null
}
Use a REFUTER frame: try to falsify the sub-part; PASS only if refutation failed.
Escalate (escalate=true) if: dimensionless/bare geometric factor; Tier disagreement;
circular plug-back; qualitative deliverable; case-menu boundary risk; low confidence.
""".strip()

ESCALATION_TRIGGERS = {
    "A.1": "dimensionless geometric factor / bare numeric from energy merge",
    "B.4": "dimensionless exponent-adjacent capillary length; dimensional risk",
    "B.5": "DE + BC / root-branch selection",
}


def _parse_json(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if not m:
            return {"verdict": "UNCERTAIN", "parse_error": content[:500]}
        return json.loads(m.group(0))


def _slice(text: str, sp: str) -> str:
    # Accept A.1 / A-3 / A1 style labels
    variants = {sp, sp.replace("-", "."), sp.replace(".", ""), sp.replace(".", "-")}
    m = None
    for v in variants:
        pat = re.compile(rf"(?:^|\n)\s*{re.escape(v)}\b", re.MULTILINE)
        m = pat.search(text)
        if m:
            break
    if not m:
        # fallback: first mention anywhere
        for v in variants:
            i = text.find(v)
            if i >= 0:
                return text[max(0, i - 80) : i + 4500]
        return text[:4000]
    start = m.start()
    next_pos = []
    # Cut at next sub-part-like header
    mo = re.search(
        r"(?:^|\n)\s*(?:Part\s+[A-Z]|[A-C](?:[.\-]?)\d+[a-z]?)\b",
        text[m.end() :],
        re.MULTILINE,
    )
    if mo:
        next_pos.append(m.end() + mo.start())
    end = min(next_pos) if next_pos else min(len(text), start + 6000)
    return text[start:end]


def judge_subpart(
    client: TrackedClient,
    *,
    model: str,
    problem_text: str,
    solution_text: str,
    subpart: str,
    purpose: str,
    det_note: str = "",
    reasoning_effort: str = "medium",
) -> dict[str, Any]:
    # Stable-prefix-first layout for caching: P then S then question last.
    prefix = (
        "You are verifying an IPhO-mechanics REFERENCE solution S against problem P.\n"
        "This is NOT student grading against a key — the physics is the authority.\n"
        "Focus ONLY on the requested sub-part.\n\n"
        f"=== PROBLEM P ===\n{problem_text[:12000]}\n\n"
        f"=== SOLUTION S (full) ===\n{solution_text[:16000]}\n"
    )
    question = (
        f"\n=== SUB-PART UNDER TEST: {subpart} ===\n"
        f"{_slice(solution_text, subpart)[:4500]}\n\n"
        f"Deterministic pre-check notes: {det_note or 'none'}\n\n"
        f"{JUDGE_SCHEMA_HINT}"
    )
    resp = client.chat(
        model=model,
        messages=[{"role": "user", "content": prefix + question}],
        purpose=purpose,
        max_completion_tokens=2500,
        reasoning_effort=reasoning_effort,
        meta={"subpart": subpart},
    )
    parsed = _parse_json(resp["content"])
    parsed["_cost_usd"] = resp["cost_usd"]
    parsed["_call_id"] = resp["call_id"]
    parsed["_model"] = model
    parsed.setdefault("subpart_id", subpart)
    return parsed


def escalate_agent(
    client: TrackedClient,
    *,
    model: str,
    problem_text: str,
    solution_text: str,
    subpart: str,
    prior: dict[str, Any],
    purpose: str,
) -> dict[str, Any]:
    """Lightweight S4-style escalation: multi-check reasoning without a code sandbox."""
    prompt = (
        "ESCALATION AGENT for IPhO reference-solution verification.\n"
        "Run an adversarial multi-check on ONE sub-part: dimensional, limiting-case,\n"
        "conservation residual, BC/root-branch, symbol-whitelist, faithfulness to P.\n"
        "Write brief executable-style reasoning (as if you had SymPy), then verdict.\n\n"
        f"=== PROBLEM P ===\n{problem_text[:10000]}\n\n"
        f"=== SOLUTION S ===\n{solution_text[:14000]}\n\n"
        f"=== SUB-PART {subpart} ===\n{_slice(solution_text, subpart)[:4500]}\n\n"
        f"=== PRIOR JUDGE ===\n{json.dumps(prior, ensure_ascii=False)[:2000]}\n\n"
        "Return ONLY JSON: {"
        '"checks_run":["..."], "refutation":null or str, '
        '"verdict":"PASS|FAIL", "confidence":0.0, "first_point_of_failure":null or str, '
        '"fault_type_guess":null or str}'
    )
    resp = client.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        purpose=purpose,
        max_completion_tokens=3500,
        reasoning_effort="medium",
        meta={"subpart": subpart, "escalation": True},
    )
    parsed = _parse_json(resp["content"])
    parsed["_cost_usd"] = resp["cost_usd"]
    parsed["_call_id"] = resp["call_id"]
    parsed["_model"] = model
    return parsed


def _should_escalate(sp: str, judge: dict[str, Any], det: dict[str, Any], system: str) -> bool:
    if judge.get("escalate") is True:
        return True
    if judge.get("verdict") == "UNCERTAIN":
        return True
    if float(judge.get("confidence") or 0) < 0.55:
        return True
    if sp in det.get("failed_subparts", []):
        # cheap layer already failed — still escalate hard cases for confirmation on S3/S2
        if sp in ("A.1", "B.5"):
            return True
    if sp in ESCALATION_TRIGGERS:
        # DEFINITION.MD §5 triggers — especially dimensionless A.1
        if sp == "A.1":
            return True
        if system == "S3" and sp in ("B.4", "B.5"):
            return True
    return False


def run_system(
    client: TrackedClient,
    *,
    system: str,
    problem_text: str,
    solution_text: str,
    instance_id: str,
) -> dict[str, Any]:
    """Run S1, S2, or S3 on one (P,S) pair."""
    assert system in {"S1", "S2", "S3"}

    det = run_deterministic(solution_text)
    judge_model = {"S1": "gpt-5.6-luna", "S2": "gpt-5.6-luna", "S3": "gpt-5.6-terra"}[system]
    allow_escalation = system in {"S2", "S3"}
    escalation_model = "gpt-5.6-terra"
    reasoning = "low" if system == "S1" else "medium"

    # For S1, apply batch 50% discount accounting
    prev_batch = client.batch_mode
    if system == "S1":
        client.batch_mode = True

    per_subpart: list[dict[str, Any]] = []
    escalated: list[str] = []
    cost = 0.0

    try:
        for sp in SUBPARTS:
            det_note = "; ".join(
                f"{c['check_id']}={c['status']}: {c['detail']}"
                for c in det["checks"]
                if c["subpart"] == sp
            )
            judge = judge_subpart(
                client,
                model=judge_model,
                problem_text=problem_text,
                solution_text=solution_text,
                subpart=sp,
                purpose=f"{system}.judge",
                det_note=det_note,
                reasoning_effort=reasoning,
            )
            cost += float(judge.get("_cost_usd") or 0)

            esc_result = None
            if allow_escalation and _should_escalate(sp, judge, det, system):
                escalated.append(sp)
                esc_result = escalate_agent(
                    client,
                    model=escalation_model,
                    problem_text=problem_text,
                    solution_text=solution_text,
                    subpart=sp,
                    prior=judge,
                    purpose=f"{system}.escalate",
                )
                cost += float(esc_result.get("_cost_usd") or 0)
                final_verdict = esc_result.get("verdict", judge.get("verdict"))
                final_fail = esc_result.get("first_point_of_failure") or judge.get(
                    "first_point_of_failure"
                )
            else:
                # Merge deterministic fails
                final_verdict = judge.get("verdict", "UNCERTAIN")
                if sp in det["failed_subparts"] and final_verdict == "PASS":
                    final_verdict = "FAIL"
                final_fail = judge.get("first_point_of_failure")
                if sp in det["failed_subparts"] and not final_fail:
                    failed_c = next(c for c in det["checks"] if c["subpart"] == sp and c["status"] == "fail")
                    final_fail = failed_c["detail"]

            per_subpart.append(
                {
                    "id": sp,
                    "judge": {k: v for k, v in judge.items() if not k.startswith("_")},
                    "escalated": esc_result is not None,
                    "escalation": (
                        {k: v for k, v in esc_result.items() if not k.startswith("_")}
                        if esc_result
                        else None
                    ),
                    "final_verdict": final_verdict,
                    "first_point_of_failure": final_fail,
                    "cost_usd": float(judge.get("_cost_usd") or 0)
                    + (float(esc_result.get("_cost_usd") or 0) if esc_result else 0),
                }
            )
    finally:
        client.batch_mode = prev_batch

    failed = [p for p in per_subpart if p["final_verdict"] == "FAIL"]
    # Document-level verdict: REJECT if any sub-part FAIL; ACCEPT only if all PASS
    if any(p["final_verdict"] == "UNCERTAIN" for p in per_subpart) and not failed:
        doc_verdict = "UNCERTAIN"
    elif failed or det["n_fail"] > 0:
        doc_verdict = "REJECT"
    else:
        doc_verdict = "ACCEPT"

    return {
        "system": system,
        "instance_id": instance_id,
        "deterministic": det,
        "per_subpart": per_subpart,
        "escalated_subparts": escalated,
        "escalation_rate": len(escalated) / len(SUBPARTS),
        "doc_verdict": doc_verdict,
        "failed_subparts": sorted({p["id"] for p in failed} | set(det["failed_subparts"])),
        "cost_usd": round(cost, 6),
    }


# Expected fault localization for the faulty 2023 PDF (ERR-1..5)
EXPECTED_FAULTS = {
    "ERR-1": {"subpart": "A.1", "cheapest_tier": "Tier2"},
    "ERR-2": {"subpart": "B.3", "cheapest_tier": "Tier0.3"},
    "ERR-3": {"subpart": "B.4", "cheapest_tier": "Tier0.1"},
    "ERR-4": {"subpart": "B.5", "cheapest_tier": "Tier1.2"},
    "ERR-5": {"subpart": "C.2", "cheapest_tier": "Tier0.5"},
}


def score_against_labels(result: dict[str, Any], expected_label: str) -> dict[str, Any]:
    """expected_label: ACCEPT for clean, REJECT for faulty."""
    doc = result["doc_verdict"]
    correct_doc = doc == expected_label or (expected_label == "REJECT" and doc == "REJECT")
    fault_hits = {}
    if expected_label == "REJECT":
        failed = set(result.get("failed_subparts") or [])
        det_failed = set(result.get("deterministic", {}).get("failed_subparts") or [])
        for err, meta in EXPECTED_FAULTS.items():
            sp = meta["subpart"]
            hit = sp in failed
            tier = None
            if sp in det_failed:
                tier = "deterministic"
            elif hit:
                # find which stage
                for p in result["per_subpart"]:
                    if p["id"] == sp:
                        if p.get("escalated") and (p.get("escalation") or {}).get("verdict") == "FAIL":
                            tier = "escalation"
                        else:
                            tier = "bulk_judge"
                if tier is None:
                    tier = "unknown"
            fault_hits[err] = {
                "subpart": sp,
                "caught": hit,
                "caught_at": tier,
                "expected_cheapest": meta["cheapest_tier"],
            }
    return {
        "expected_label": expected_label,
        "doc_verdict": doc,
        "doc_correct": bool(correct_doc) if expected_label == "ACCEPT" else doc == "REJECT",
        "false_reject": expected_label == "ACCEPT" and doc == "REJECT",
        "false_accept": expected_label == "REJECT" and doc == "ACCEPT",
        "fault_hits": fault_hits,
        "faults_caught": sum(1 for v in fault_hits.values() if v["caught"]),
        "faults_total": len(fault_hits),
    }
