"""Tune cascade confidence thresholds on the DEV split only (never reported).

Runs the nano verifier on the dev instances, records (confidence, correct?), and
picks the lowest confidence threshold at which every trusted (early-exit) nano
verdict on dev is correct. Writes results/tuning.json consumed by the registry.
"""
from __future__ import annotations

import json
import os

from verifier.common.base import run_full_solution
from verifier.common.client import LLMClient, NANO_MODEL
from bench.problems_data import PROBLEMS

HERE = os.path.dirname(__file__)
DATASET = os.path.join(HERE, "..", "dataset", "instances.jsonl")
RUBRICS = os.path.join(HERE, "..", "dataset", "rubrics.json")
RESULTS_DIR = os.path.join(HERE, "..", "results")
OUT = os.path.join(RESULTS_DIR, "tuning.json")


def main() -> None:
    rubrics = json.load(open(RUBRICS))
    dev = [json.loads(line) for line in open(DATASET) if json.loads(line)["split"] == "dev"]
    cli = LLMClient(run_tag="tune_dev", config="tune")

    records = []
    for inst in dev:
        problem = PROBLEMS[inst["problem"]]
        v = run_full_solution(cli, NANO_MODEL, problem, rubrics[inst["problem"]],
                              inst["candidate_solution"], reasoning_effort="low",
                              instance_id=inst["id"], step="tune:nano")
        correct = v.verdict == inst["label"]
        records.append({"id": inst["id"], "conf": v.confidence,
                        "pred": v.verdict, "gold": inst["label"], "correct": correct})
        print(f"{inst['id']:34s} conf={v.confidence:.2f} pred={v.verdict} "
              f"gold={inst['label']} correct={correct}")

    # Lowest threshold such that all trusted (conf>=thr) dev verdicts are correct.
    candidate_thrs = sorted({round(r["conf"], 2) for r in records} | {0.5, 0.8, 0.9, 0.95})
    chosen = 0.95
    for thr in candidate_thrs:
        trusted = [r for r in records if r["conf"] >= thr]
        if trusted and all(r["correct"] for r in trusted):
            chosen = thr
            break

    tuning = {
        "A.V1": {"conf_threshold": chosen},
        "A.V2": {"conf_threshold": chosen},
        "composed": {"conf_threshold": max(chosen, 0.9)},
        "_dev_records": records,
        "_note": "Threshold = lowest dev confidence at which all early-exit nano "
                 "verdicts were correct. Dev split only; never used for reporting.",
    }
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(tuning, f, indent=2)
    print(f"\nChosen threshold={chosen} -> {OUT}")


if __name__ == "__main__":
    main()
