"""Phase 1 — build and freeze the labeled gold set.

For each problem: 1 CORRECT instance (official answers) + one instance per
injected single fault (REJECT, failing sub-part known by construction).

Curation: every fault is checked with the deterministic stack to confirm it
actually makes the answer differ from the reference (i.e. is genuinely wrong);
any fault that does NOT change the verdict is DISCARDED and logged. A dev split
(~20%) is reserved for threshold tuning and never used for reporting.
"""
from __future__ import annotations

import argparse
import json
import os
import random

from verifier.common.deterministic import check_subpart, FAIL

from bench.problems_data import (
    FAULTS,
    PROBLEMS,
    correct_subpart_answers,
    reference_rubric,
    render_candidate,
)

HERE = os.path.dirname(__file__)
DATASET_DIR = os.path.join(HERE, "..", "dataset")
OUT_PATH = os.path.join(DATASET_DIR, "instances.jsonl")
DISCARD_LOG = os.path.join(DATASET_DIR, "discards.log")
SEED = 20250718


def _instance(problem, variant, label, injected_fault, failing_subpart, answers):
    return {
        "id": None,  # assigned later
        "problem": problem["key"],
        "title": problem["title"],
        "year": problem["year"],
        "variant": variant,
        "label": label,
        "injected_fault": injected_fault,
        "failing_subpart": failing_subpart,
        "split": None,
        "subpart_answers": answers,
        "candidate_solution": render_candidate(problem, answers),
    }


def build() -> None:
    rng = random.Random(SEED)
    discards: list[str] = []
    instances: list[dict] = []

    for key, problem in PROBLEMS.items():
        # Correct instance
        correct = correct_subpart_answers(problem)
        instances.append(
            _instance(problem, "correct", "ACCEPT", None, None, correct)
        )
        # Fault instances (curated)
        for fdef in FAULTS[key]:
            answers = correct_subpart_answers(problem)
            answers[fdef["subpart"]] = fdef["answer"]
            subpart = next(s for s in problem["subparts"] if s["id"] == fdef["subpart"])
            # Curate: qualitative faults can't be machine-confirmed, keep them
            # (they are the LLM-escalation cases by design). Non-qualitative faults
            # must produce a deterministic FAIL to be trustworthy REJECT labels.
            if subpart["kind"] != "qualitative" and fdef["answer"]["type"] != "qualitative":
                res = check_subpart(subpart, fdef["answer"])
                if res.outcome != FAIL:
                    discards.append(
                        f"DISCARD {key} fault={fdef['fault']} subpart={fdef['subpart']}: "
                        f"deterministic outcome={res.outcome} ({res.detail}) — fault does "
                        f"not falsify against reference; relabel/skip."
                    )
                    continue
            instances.append(
                _instance(problem, f"fault_{fdef['fault']}", "REJECT",
                          fdef["fault"], fdef["subpart"], answers)
            )

    # Assign ids and dev/report split (~20% dev, stratified: keep 1 correct in report)
    by_problem: dict[str, list[dict]] = {}
    for inst in instances:
        by_problem.setdefault(inst["problem"], []).append(inst)

    for key, insts in by_problem.items():
        rejects = [i for i in insts if i["label"] == "REJECT"]
        rng.shuffle(rejects)
        n_dev = max(1, round(0.2 * len(insts)))
        dev_ids = set(id(i) for i in rejects[:n_dev])
        for idx, inst in enumerate(insts):
            inst["id"] = f"{key}__{idx:02d}"
            inst["split"] = "dev" if id(inst) in dev_ids else "report"

    os.makedirs(DATASET_DIR, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        for inst in instances:
            f.write(json.dumps(inst) + "\n")

    with open(DISCARD_LOG, "w") as f:
        f.write("\n".join(discards) if discards else "No discards: all injected faults "
                "were confirmed to falsify against the reference.\n")

    # Also persist the reference rubric per problem for the verifiers.
    rubrics = {key: reference_rubric(p) for key, p in PROBLEMS.items()}
    with open(os.path.join(DATASET_DIR, "rubrics.json"), "w") as f:
        json.dump(rubrics, f, indent=2)

    # Summary
    n_total = len(instances)
    n_correct = sum(1 for i in instances if i["label"] == "ACCEPT")
    n_reject = n_total - n_correct
    n_dev = sum(1 for i in instances if i["split"] == "dev")
    print(f"Wrote {n_total} instances -> {OUT_PATH}")
    print(f"  ACCEPT={n_correct}  REJECT={n_reject}  dev={n_dev}  report={n_total-n_dev}")
    print(f"  discards={len(discards)} (see {DISCARD_LOG})")
    for key, insts in by_problem.items():
        print(f"  {key}: {len(insts)} instances "
              f"({sum(1 for i in insts if i['split']=='report')} report)")


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    build()
