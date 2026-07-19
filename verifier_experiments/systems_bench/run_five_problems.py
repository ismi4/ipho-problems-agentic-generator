#!/usr/bin/env python3
"""Run S3/S2/S1 on five IPhO mechanics clean/faulty pairs under a $25 cap."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .budget import Budget, BudgetExceeded
from .client import TrackedClient
from .ingest import ingest_i1
from .systems import escalate_agent, judge_subpart, score_against_labels

ROOT = Path(__file__).resolve().parents[1]
PDFS = ROOT / "pdfs"
OUT = Path(__file__).resolve().parent / "results_five"
CORPUS = Path(__file__).resolve().parent / "corpus.json"


def load_corpus() -> list[dict]:
    return json.loads(CORPUS.read_text())["problems"]


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str))
    print(f"  wrote {path.name}")


def truncate(text: str, n: int) -> str:
    if len(text) <= n:
        return text
    return text[:n] + f"\n…[truncated {len(text)-n} chars]"


def run_system_on_instance(
    client: TrackedClient,
    *,
    system: str,
    problem_text: str,
    solution_text: str,
    subparts: list[str],
    instance_id: str,
    problem_id: str,
) -> dict:
    from .deterministic import run_deterministic

    # Deterministic layer is 2023-specialized; still run for signal when applicable
    det = run_deterministic(solution_text) if problem_id == "2023_Q3" else {
        "checks": [],
        "n_fail": 0,
        "failed_subparts": [],
        "verdict_hint": "NO_DETERMINISTIC_REJECT",
    }

    judge_model = {"S1": "gpt-5.6-luna", "S2": "gpt-5.6-luna", "S3": "gpt-5.6-terra"}[system]
    allow_esc = system in {"S2", "S3"}
    reasoning = "low" if system == "S1" else "medium"
    prev_batch = client.batch_mode
    if system == "S1":
        client.batch_mode = True

    # Cap context: large PDFs (2025) blow token budgets
    p_txt = truncate(problem_text, 10000)
    s_txt = truncate(solution_text, 14000)

    per = []
    escalated = []
    cost = 0.0
    try:
        for sp in subparts:
            det_note = "; ".join(
                f"{c['check_id']}={c['status']}: {c['detail']}"
                for c in det.get("checks", [])
                if c.get("subpart") == sp
            )
            judge = judge_subpart(
                client,
                model=judge_model,
                problem_text=p_txt,
                solution_text=s_txt,
                subpart=sp,
                purpose=f"{system}.judge.{problem_id}",
                det_note=det_note,
                reasoning_effort=reasoning,
            )
            cost += float(judge.get("_cost_usd") or 0)

            esc = None
            should = False
            if allow_esc:
                if judge.get("escalate") is True or judge.get("verdict") == "UNCERTAIN":
                    should = True
                if float(judge.get("confidence") or 0) < 0.55:
                    should = True
                # Always escalate dimensionless / threshold / faithfulness-ish tags
                if any(k in sp.upper() for k in ("A.1", "A1", "A-3", "C.1", "A.5")):
                    should = True
            if should:
                # Keep escalations lean
                if len(escalated) >= 3 and system == "S2":
                    should = False
                if len(escalated) >= 4 and system == "S3":
                    should = False
            if should:
                escalated.append(sp)
                esc = escalate_agent(
                    client,
                    model="gpt-5.6-terra",
                    problem_text=p_txt,
                    solution_text=s_txt,
                    subpart=sp,
                    prior=judge,
                    purpose=f"{system}.escalate.{problem_id}",
                )
                cost += float(esc.get("_cost_usd") or 0)
                final = esc.get("verdict", judge.get("verdict"))
                fail = esc.get("first_point_of_failure") or judge.get("first_point_of_failure")
            else:
                final = judge.get("verdict", "UNCERTAIN")
                if sp in det.get("failed_subparts", []) and final == "PASS":
                    final = "FAIL"
                fail = judge.get("first_point_of_failure")

            per.append(
                {
                    "id": sp,
                    "judge": {k: v for k, v in judge.items() if not k.startswith("_")},
                    "escalated": esc is not None,
                    "escalation": (
                        {k: v for k, v in esc.items() if not k.startswith("_")} if esc else None
                    ),
                    "final_verdict": final,
                    "first_point_of_failure": fail,
                    "cost_usd": float(judge.get("_cost_usd") or 0)
                    + (float(esc.get("_cost_usd") or 0) if esc else 0),
                }
            )
    finally:
        client.batch_mode = prev_batch

    failed = [p["id"] for p in per if p["final_verdict"] == "FAIL"]
    failed = sorted(set(failed) | set(det.get("failed_subparts") or []))
    if failed:
        doc_verdict = "REJECT"
    elif any(p["final_verdict"] == "UNCERTAIN" for p in per):
        doc_verdict = "UNCERTAIN"
    else:
        doc_verdict = "ACCEPT"

    return {
        "system": system,
        "problem_id": problem_id,
        "instance_id": instance_id,
        "deterministic": det,
        "per_subpart": per,
        "escalated_subparts": escalated,
        "escalation_rate": len(escalated) / max(1, len(subparts)),
        "doc_verdict": doc_verdict,
        "failed_subparts": failed,
        "cost_usd": round(cost, 6),
    }


def score_faults(result: dict, problem: dict, expected: str) -> dict:
    base = {
        "expected_label": expected,
        "doc_verdict": result["doc_verdict"],
        "doc_correct": (
            result["doc_verdict"] == "ACCEPT"
            if expected == "ACCEPT"
            else result["doc_verdict"] == "REJECT"
        ),
        "false_reject": expected == "ACCEPT" and result["doc_verdict"] == "REJECT",
        "false_accept": expected == "REJECT" and result["doc_verdict"] == "ACCEPT",
    }
    hits = {}
    if expected == "REJECT":
        failed = set(result.get("failed_subparts") or [])
        for f in problem["injected_faults"]:
            sp = f["subpart"]
            caught = sp in failed
            tier = None
            if caught:
                for p in result["per_subpart"]:
                    if p["id"] == sp:
                        if p.get("escalated") and (p.get("escalation") or {}).get("verdict") == "FAIL":
                            tier = "escalation"
                        else:
                            tier = "bulk_judge"
            hits[f["id"]] = {
                "subpart": sp,
                "caught": caught,
                "caught_at": tier,
                "type": f["type"],
            }
    base["fault_hits"] = hits
    base["faults_caught"] = sum(1 for v in hits.values() if v["caught"])
    base["faults_total"] = len(hits)
    return base


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hard-cap", type=float, default=25.0)
    ap.add_argument("--systems", default="S3,S2,S1")
    ap.add_argument("--problems", default="", help="comma ids, default all")
    ap.add_argument("--resume", action="store_true", help="skip instance cells that already have run_*.json")
    args = ap.parse_args(argv)

    OUT.mkdir(parents=True, exist_ok=True)
    budget = Budget(hard_cap_usd=args.hard_cap, log_path=OUT / "api_calls.jsonl")
    client = TrackedClient(budget)
    corpus = load_corpus()
    if args.problems.strip():
        want = {x.strip() for x in args.problems.split(",")}
        corpus = [p for p in corpus if p["id"] in want]

    systems = [s.strip() for s in args.systems.split(",") if s.strip()]
    print(f"Hard cap ${args.hard_cap:.2f} | problems={len(corpus)} | systems={systems}")

    # Load texts
    texts = {}
    for p in corpus:
        texts[p["id"]] = {
            "problem": ingest_i1(PDFS / p["problem_pdf"])["text"],
            "clean": ingest_i1(PDFS / p["clean_pdf"])["text"],
            "faulty": ingest_i1(PDFS / p["faulty_pdf"])["text"],
            "meta": p,
        }
        print(
            f"  loaded {p['id']}: P={len(texts[p['id']]['problem'])} "
            f"S={len(texts[p['id']]['clean'])} F={len(texts[p['id']]['faulty'])}"
        )

    # Light ingestion cost probe: I2 mini on smallest solution only (2020, 4pp)
    ingestion = {"note": "Full I4 skipped on 5-problem sweep to reserve budget for judges; I1 used for cascade."}
    dump(OUT / "ingestion_note.json", ingestion)

    runs = []
    aborted = False
    for system in systems:
        for p in corpus:
            for inst, label in [("clean", "ACCEPT"), ("faulty", "REJECT")]:
                out_path = OUT / f"run_{system}_{p['id']}_{inst}.json"
                if args.resume and out_path.exists():
                    print(f"  skip existing {out_path.name}")
                    runs.append(json.loads(out_path.read_text()))
                    continue
                print(
                    f"\n>>> {system} {p['id']} {inst} | spent ${budget.spent_usd:.4f} remaining ${budget.remaining():.4f}"
                )
                t0 = time.time()
                try:
                    result = run_system_on_instance(
                        client,
                        system=system,
                        problem_text=texts[p["id"]]["problem"],
                        solution_text=texts[p["id"]][inst],
                        subparts=p["subparts"],
                        instance_id=inst,
                        problem_id=p["id"],
                    )
                except BudgetExceeded as e:
                    print("BUDGET STOP:", e)
                    runs.append(
                        {
                            "system": system,
                            "problem_id": p["id"],
                            "instance_id": inst,
                            "aborted": True,
                            "error": str(e),
                        }
                    )
                    aborted = True
                    break
                scored = score_faults(result, p, label)
                row = {**result, "scoring": scored, "wall_s": time.time() - t0, "problem_name": p["name"]}
                runs.append(row)
                dump(OUT / f"run_{system}_{p['id']}_{inst}.json", row)
                print(
                    f"    {row['doc_verdict']} (exp {label}) ok={scored['doc_correct']} "
                    f"faults={scored.get('faults_caught')}/{scored.get('faults_total')} "
                    f"esc={row['escalation_rate']:.2f} ${row['cost_usd']:.4f}"
                )
            if aborted:
                break
        if aborted:
            break

    # Summarize
    by_sys: dict = {}
    for r in runs:
        if r.get("aborted"):
            continue
        by_sys.setdefault(r["system"], []).append(r)

    cost_quality = {}
    for sys, rows in by_sys.items():
        costs = [r["cost_usd"] for r in rows]
        cleans = [r for r in rows if r["instance_id"] == "clean"]
        faulties = [r for r in rows if r["instance_id"] == "faulty"]
        cost_quality[sys] = {
            "mean_cost_usd": sum(costs) / len(costs) if costs else None,
            "n_instances": len(rows),
            "clean_accept_rate": sum(1 for r in cleans if r["scoring"]["doc_correct"]) / max(1, len(cleans)),
            "faulty_reject_rate": sum(1 for r in faulties if r["scoring"]["doc_correct"]) / max(1, len(faulties)),
            "false_rejects": sum(1 for r in cleans if r["scoring"]["false_reject"]),
            "false_accepts": sum(1 for r in faulties if r["scoring"]["false_accept"]),
            "faults_caught_total": sum(r["scoring"].get("faults_caught") or 0 for r in faulties),
            "faults_total": sum(r["scoring"].get("faults_total") or 0 for r in faulties),
            "mean_escalation_rate": sum(r["escalation_rate"] for r in rows) / max(1, len(rows)),
            "per_problem": {
                r["problem_id"] + "/" + r["instance_id"]: {
                    "verdict": r["doc_verdict"],
                    "correct": r["scoring"]["doc_correct"],
                    "cost": r["cost_usd"],
                    "faults": f"{r['scoring'].get('faults_caught')}/{r['scoring'].get('faults_total')}",
                }
                for r in rows
            },
        }

    s3 = (cost_quality.get("S3") or {}).get("mean_cost_usd")
    for sys, cq in cost_quality.items():
        if s3 and cq["mean_cost_usd"] is not None:
            cq["cost_vs_S3"] = cq["mean_cost_usd"] / s3
            cq["savings_vs_S3"] = 1.0 - cq["cost_vs_S3"]

    summary = {
        "corpus": corpus,
        "systems": systems,
        "aborted": aborted,
        "cost_quality_by_system": cost_quality,
        "spend": budget.summary(),
        "n_runs": len([r for r in runs if not r.get("aborted")]),
    }
    dump(OUT / "systems_runs.json", {"runs": runs, "aborted": aborted})
    dump(OUT / "summary.json", summary)
    dump(OUT / "spend_summary.json", budget.summary())
    print("\n=== SUMMARY ===")
    print(json.dumps(cost_quality, indent=2))
    print("Spend:", json.dumps(budget.summary(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
