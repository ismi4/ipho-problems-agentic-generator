#!/usr/bin/env python3
"""Execute SYSTEMS.md experiments on the 2023 clean/faulty S3 pair under a $25 cap.

Phases:
  1) Ingestion cost experiment (I1 text; I2/I4 vision on both S PDFs)
  2) Optional sol-vs-terra escalation arm on A.1 only (settles SYSTEMS.md §0)
  3) S3, S2, S1 verification on clean + faulty
  4) Write results JSON under systems_bench/results/
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDFS = ROOT / "pdfs"
OUT = Path(__file__).resolve().parent / "results"
WORK = Path(__file__).resolve().parent / "_work"

from .budget import Budget, BudgetExceeded
from .client import TrackedClient
from .deterministic import run_deterministic
from .ingest import ingest_i1, ingest_vision
from .systems import escalate_agent, judge_subpart, run_system, score_against_labels


CLEAN_S = PDFS / "IPhO_2023_S3.pdf"
FAULTY_S = PDFS / "faulty" / "IPhO_2023_S3_FAULTY.pdf"
PROBLEM = PDFS / "IPhO_2023_Q3.pdf"


def _dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str))
    print(f"  wrote {path}")


def phase_ingestion(client: TrackedClient) -> dict:
    print("\n=== PHASE 1: Ingestion ladder on 2023 pair ===")
    out = {"i1": {}, "i4_terra": {}, "i2_mini": {}, "notes": []}
    for label, path in [("clean", CLEAN_S), ("faulty", FAULTY_S), ("problem", PROBLEM)]:
        out["i1"][label] = ingest_i1(path)
        print(f"  I1 {label}: {out['i1'][label]['n_chars']} chars")

    # I4 with terra on the two solution PDFs (the open question in SYSTEMS.md §1)
    for label, path in [("clean", CLEAN_S), ("faulty", FAULTY_S)]:
        print(f"  I4 terra ingest {label}...")
        try:
            out["i4_terra"][label] = ingest_vision(
                client,
                path,
                model="gpt-5.6-terra",
                rung="I4",
                work_dir=WORK / "i4",
                purpose="ingest.I4.terra",
                typed_ir=True,
                max_retries=1,
                reasoning_effort="low",
            )
            print(
                f"    cost=${out['i4_terra'][label]['cost_usd']:.4f} "
                f"retries={out['i4_terra'][label]['retries']} "
                f"sub_parts={len(out['i4_terra'][label].get('sub_parts') or [])}"
            )
        except BudgetExceeded:
            raise
        except Exception as e:
            out["i4_terra"][label] = {"error": str(e), "cost_usd": 0.0}
            out["notes"].append(f"I4 {label} failed: {e}")

    # I2 with mini on both solutions (S1 ingestion rung)
    for label, path in [("clean", CLEAN_S), ("faulty", FAULTY_S)]:
        print(f"  I2 mini ingest {label}...")
        try:
            out["i2_mini"][label] = ingest_vision(
                client,
                path,
                model="gpt-5.4-mini",
                rung="I2",
                work_dir=WORK / "i2",
                purpose="ingest.I2.mini",
                typed_ir=False,
                max_retries=0,
                reasoning_effort="low",
            )
            print(f"    cost=${out['i2_mini'][label]['cost_usd']:.4f}")
        except BudgetExceeded:
            raise
        except Exception as e:
            out["i2_mini"][label] = {"error": str(e), "cost_usd": 0.0}
            out["notes"].append(f"I2 {label} failed: {e}")

    # Summarize I4 cost answer
    i4_costs = [v.get("cost_usd", 0) for v in out["i4_terra"].values() if isinstance(v, dict)]
    out["i4_mean_cost_usd"] = sum(i4_costs) / len(i4_costs) if i4_costs else None
    out["i4_total_cost_usd"] = sum(i4_costs)
    out["spend_after_phase"] = client.budget.summary()
    return out


def phase_sol_vs_terra(client: TrackedClient, problem_text: str, faulty_text: str) -> dict:
    """SYSTEMS.md §0 arm: does sol catch A.1 geometric-factor fault that terra might miss?"""
    print("\n=== PHASE 2: sol vs terra escalation arm on faulty A.1 ===")
    det = run_deterministic(faulty_text)
    det_note = "; ".join(
        f"{c['check_id']}={c['status']}: {c['detail']}" for c in det["checks"] if c["subpart"] == "A.1"
    )
    results = {}
    for model in ("gpt-5.6-terra", "gpt-5.6-sol"):
        print(f"  escalate A.1 with {model}...")
        # cheap prior judge on luna to keep arm focused on escalation tier
        prior = judge_subpart(
            client,
            model="gpt-5.6-luna",
            problem_text=problem_text,
            solution_text=faulty_text,
            subpart="A.1",
            purpose="arm.prior_luna",
            det_note=det_note,
            reasoning_effort="low",
        )
        esc = escalate_agent(
            client,
            model=model,
            problem_text=problem_text,
            solution_text=faulty_text,
            subpart="A.1",
            prior=prior,
            purpose=f"arm.escalate.{model}",
        )
        results[model] = {
            "prior_verdict": prior.get("verdict"),
            "escalation_verdict": esc.get("verdict"),
            "refutation": esc.get("refutation"),
            "first_point_of_failure": esc.get("first_point_of_failure"),
            "fault_type_guess": esc.get("fault_type_guess"),
            "cost_usd": float(prior.get("_cost_usd") or 0) + float(esc.get("_cost_usd") or 0),
        }
        print(
            f"    prior={results[model]['prior_verdict']} "
            f"esc={results[model]['escalation_verdict']} "
            f"cost=${results[model]['cost_usd']:.4f}"
        )
    results["spend_after_phase"] = client.budget.summary()
    return results


def phase_systems(client: TrackedClient, problem_text: str, clean_text: str, faulty_text: str) -> dict:
    print("\n=== PHASE 3: S3 / S2 / S1 on clean + faulty ===")
    instances = [
        ("clean", clean_text, "ACCEPT"),
        ("faulty", faulty_text, "REJECT"),
    ]
    systems = ["S3", "S2", "S1"]
    runs = []
    for system in systems:
        for inst_id, sol_text, label in instances:
            print(f"  Running {system} on {inst_id} (spend so far ${client.budget.spent_usd:.4f})...")
            t0 = time.time()
            try:
                result = run_system(
                    client,
                    system=system,
                    problem_text=problem_text,
                    solution_text=sol_text,
                    instance_id=inst_id,
                )
            except BudgetExceeded as e:
                print(f"  BUDGET STOP during {system}/{inst_id}: {e}")
                runs.append(
                    {
                        "system": system,
                        "instance_id": inst_id,
                        "error": str(e),
                        "aborted": True,
                    }
                )
                return {"runs": runs, "aborted": True, "spend_after_phase": client.budget.summary()}
            scored = score_against_labels(result, label)
            row = {**result, "scoring": scored, "wall_s": time.time() - t0}
            runs.append(row)
            print(
                f"    verdict={row['doc_verdict']} expected={label} "
                f"correct={scored['doc_correct']} "
                f"escalation_rate={row['escalation_rate']:.2f} "
                f"cost=${row['cost_usd']:.4f} "
                f"faults={scored.get('faults_caught')}/{scored.get('faults_total')}"
            )
            _dump(OUT / f"run_{system}_{inst_id}.json", row)
    return {"runs": runs, "aborted": False, "spend_after_phase": client.budget.summary()}


def build_summary(ingestion, arm, systems_out, budget: Budget) -> dict:
    runs = systems_out.get("runs") or []
    table = []
    for r in runs:
        if r.get("aborted"):
            continue
        sc = r["scoring"]
        table.append(
            {
                "system": r["system"],
                "instance": r["instance_id"],
                "doc_verdict": r["doc_verdict"],
                "expected": sc["expected_label"],
                "doc_correct": sc["doc_correct"],
                "false_reject": sc["false_reject"],
                "false_accept": sc["false_accept"],
                "escalation_rate": r["escalation_rate"],
                "escalated_subparts": r["escalated_subparts"],
                "failed_subparts": r["failed_subparts"],
                "faults_caught": sc.get("faults_caught"),
                "fault_hits": sc.get("fault_hits"),
                "cost_usd": r["cost_usd"],
                "deterministic_fails": r["deterministic"]["failed_subparts"],
            }
        )

    # Cost comparison: mean over instances per system
    by_sys = {}
    for row in table:
        by_sys.setdefault(row["system"], []).append(row)
    cost_quality = {}
    for sys, rows in by_sys.items():
        costs = [r["cost_usd"] for r in rows]
        clean = next((r for r in rows if r["instance"] == "clean"), None)
        faulty = next((r for r in rows if r["instance"] == "faulty"), None)
        cost_quality[sys] = {
            "mean_cost_usd": sum(costs) / len(costs) if costs else None,
            "clean_accept_ok": bool(clean and clean["doc_correct"]),
            "faulty_reject_ok": bool(faulty and faulty["doc_correct"]),
            "faults_caught": faulty["faults_caught"] if faulty else None,
            "fault_hits": faulty["fault_hits"] if faulty else None,
            "mean_escalation_rate": sum(r["escalation_rate"] for r in rows) / len(rows),
        }

    # Relative to S3
    s3_cost = (cost_quality.get("S3") or {}).get("mean_cost_usd")
    for sys, cq in cost_quality.items():
        if s3_cost and cq["mean_cost_usd"] is not None:
            cq["cost_vs_S3"] = cq["mean_cost_usd"] / s3_cost
            cq["savings_vs_S3"] = 1.0 - cq["cost_vs_S3"]

    return {
        "corpus": {
            "problem": str(PROBLEM),
            "clean": str(CLEAN_S),
            "faulty": str(FAULTY_S),
            "injected_errors": ["ERR-1", "ERR-2", "ERR-3", "ERR-4", "ERR-5"],
            "held_out": "2021 pair not run (per SYSTEMS.md + user scope)",
        },
        "ingestion": {
            "i4_mean_cost_usd": ingestion.get("i4_mean_cost_usd"),
            "i4_total_cost_usd": ingestion.get("i4_total_cost_usd"),
            "i2_costs": {
                k: v.get("cost_usd") for k, v in (ingestion.get("i2_mini") or {}).items()
            },
            "notes": ingestion.get("notes"),
        },
        "sol_vs_terra_arm": arm,
        "per_run": table,
        "cost_quality_by_system": cost_quality,
        "spend": budget.summary(),
        "systems_md_estimates": {
            "S4": 2.79,
            "S3": 1.24,
            "S2": 0.63,
            "S1": 0.20,
        },
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hard-cap", type=float, default=25.0)
    ap.add_argument("--skip-ingestion-vision", action="store_true")
    ap.add_argument("--skip-sol-arm", action="store_true")
    ap.add_argument("--systems", default="S3,S2,S1", help="comma list")
    args = ap.parse_args(argv)

    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)

    budget = Budget(hard_cap_usd=args.hard_cap, log_path=OUT / "api_calls.jsonl")
    client = TrackedClient(budget)

    print(f"Hard cap: ${args.hard_cap:.2f}")
    print(f"PDFs: clean={CLEAN_S.name} faulty={FAULTY_S.name} problem={PROBLEM.name}")

    # Always load I1 texts for verification path (render-text of official PDFs)
    problem_i1 = ingest_i1(PROBLEM)
    clean_i1 = ingest_i1(CLEAN_S)
    faulty_i1 = ingest_i1(FAULTY_S)
    problem_text = problem_i1["text"]
    clean_text = clean_i1["text"]
    faulty_text = faulty_i1["text"]

    # Sanity: deterministic layer alone on both
    det_clean = run_deterministic(clean_text)
    det_faulty = run_deterministic(faulty_text)
    _dump(
        OUT / "deterministic_baseline.json",
        {"clean": det_clean, "faulty": det_faulty},
    )
    print(
        f"Deterministic baseline: clean_fails={det_clean['failed_subparts']} "
        f"faulty_fails={det_faulty['failed_subparts']}"
    )

    ingestion = {"i1": {"clean": clean_i1, "faulty": faulty_i1, "problem": problem_i1}}
    if not args.skip_ingestion_vision:
        try:
            ingestion = phase_ingestion(client)
            # keep i1 texts
            ingestion["i1"] = {"clean": clean_i1, "faulty": faulty_i1, "problem": problem_i1}
        except BudgetExceeded as e:
            print(f"Budget exceeded in ingestion: {e}")
            _dump(OUT / "spend_summary.json", budget.summary())
            return 2
        # strip bulky raw fields before saving
        slim = json.loads(json.dumps(ingestion, default=str))
        for bucket in ("i4_terra", "i2_mini"):
            for lab, payload in list((slim.get(bucket) or {}).items()):
                if isinstance(payload, dict):
                    payload.pop("raw_content", None)
                    if isinstance(payload.get("ir"), dict):
                        # keep sub_parts + notes, trim giant markdown in summary file
                        md = payload["ir"].get("markdown") or payload.get("markdown") or ""
                        payload["markdown_chars"] = len(md)
                        payload["ir"] = {
                            "sub_parts": payload["ir"].get("sub_parts"),
                            "notes": payload["ir"].get("notes"),
                            "markdown_preview": md[:1500],
                        }
                        payload.pop("markdown", None)
        _dump(OUT / "ingestion.json", slim)
    else:
        _dump(OUT / "ingestion.json", ingestion)

    arm = {}
    if not args.skip_sol_arm:
        try:
            arm = phase_sol_vs_terra(client, problem_text, faulty_text)
            _dump(OUT / "sol_vs_terra_arm.json", arm)
        except BudgetExceeded as e:
            print(f"Budget exceeded in sol arm: {e}")
            arm = {"error": str(e)}
            _dump(OUT / "sol_vs_terra_arm.json", arm)

    # Optionally filter systems
    wanted = [s.strip() for s in args.systems.split(",") if s.strip()]
    # Monkeypatch by wrapping run — simplest: temporarily filter inside phase
    original_phase = phase_systems

    def filtered_phase(client, problem_text, clean_text, faulty_text):
        print("\n=== PHASE 3: selected systems", wanted, "===")
        instances = [("clean", clean_text, "ACCEPT"), ("faulty", faulty_text, "REJECT")]
        runs = []
        for system in wanted:
            for inst_id, sol_text, label in instances:
                print(f"  Running {system} on {inst_id} (spend ${client.budget.spent_usd:.4f})...")
                t0 = time.time()
                try:
                    result = run_system(
                        client,
                        system=system,
                        problem_text=problem_text,
                        solution_text=sol_text,
                        instance_id=inst_id,
                    )
                except BudgetExceeded as e:
                    print(f"  BUDGET STOP: {e}")
                    runs.append({"system": system, "instance_id": inst_id, "error": str(e), "aborted": True})
                    return {"runs": runs, "aborted": True, "spend_after_phase": client.budget.summary()}
                scored = score_against_labels(result, label)
                row = {**result, "scoring": scored, "wall_s": time.time() - t0}
                runs.append(row)
                print(
                    f"    verdict={row['doc_verdict']} expected={label} "
                    f"correct={scored['doc_correct']} "
                    f"esc_rate={row['escalation_rate']:.2f} cost=${row['cost_usd']:.4f} "
                    f"faults={scored.get('faults_caught')}/{scored.get('faults_total')}"
                )
                _dump(OUT / f"run_{system}_{inst_id}.json", row)
        return {"runs": runs, "aborted": False, "spend_after_phase": client.budget.summary()}

    systems_out = filtered_phase(client, problem_text, clean_text, faulty_text)
    _dump(OUT / "systems_runs.json", systems_out)

    summary = build_summary(ingestion, arm, systems_out, budget)
    _dump(OUT / "summary.json", summary)
    _dump(OUT / "spend_summary.json", budget.summary())

    print("\n=== DONE ===")
    print(json.dumps(summary.get("cost_quality_by_system"), indent=2))
    print("Spend:", json.dumps(budget.summary(), indent=2))
    return 0


if __name__ == "__main__":
    # Allow `python -m systems_bench.run_experiments` from verifier_experiments/
    sys.exit(main())
