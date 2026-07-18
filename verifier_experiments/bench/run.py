"""Run one or more verifier configs over the dataset, N reps, logging real cost.

Cost per verify() call is measured by snapshotting the process-wide spend tracker
(fed from actual OpenAI usage) before/after each call. Raw per-call usage is also
persisted to runs/<config>.jsonl by the client. Results -> results/raw_results.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from verifier.common.client import BudgetExceeded, LLMClient, SPEND
from verifier.registry import ALL_CONFIGS, build_registry

from bench.problems_data import PROBLEMS

HERE = os.path.dirname(__file__)
DATASET = os.path.join(HERE, "..", "dataset", "instances.jsonl")
RUBRICS = os.path.join(HERE, "..", "dataset", "rubrics.json")
RESULTS_DIR = os.path.join(HERE, "..", "results")
RAW_OUT = os.path.join(RESULTS_DIR, "raw_results.jsonl")


def load_instances(split: str) -> list[dict]:
    insts = [json.loads(l) for l in open(DATASET)]
    if split == "all":
        return insts
    return [i for i in insts if i["split"] == split]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--configs", nargs="+", default=ALL_CONFIGS)
    ap.add_argument("--split", default="report", choices=["report", "dev", "all"])
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0, help="cap #instances (smoke test)")
    ap.add_argument("--hard-cap", type=float, default=None, help="override spend cap USD")
    ap.add_argument("--out", default=RAW_OUT)
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--workers", type=int, default=6, help="concurrent verify() workers")
    ap.add_argument("--prior-spend", type=float, default=0.0,
                    help="seed cumulative spend from earlier runs so the cap is global")
    args = ap.parse_args()

    if args.hard_cap is not None:
        SPEND.hard_cap_usd = args.hard_cap
    if args.prior_spend:
        SPEND.total_usd = args.prior_spend

    rubrics = json.load(open(RUBRICS))
    instances = load_instances(args.split)
    if args.limit:
        # Deterministic subset: keep problem/label balance by taking a stride.
        instances = instances[: args.limit]

    registry = build_registry()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    mode = "a" if args.append else "w"
    out = open(args.out, mode)
    out_lock = threading.Lock()
    counter = {"n": 0}
    stop = threading.Event()

    def task(cfg_name, verifier, cli, inst, rep):
        if stop.is_set():
            return
        problem = PROBLEMS[inst["problem"]]
        rubric = rubrics[inst["problem"]]
        cli.begin_scope()
        t0 = time.time()
        try:
            v = verifier.verify(cli, inst, problem, rubric)
        except BudgetExceeded as e:
            stop.set()
            print(f"\n[BUDGET STOP] {e}")
            return
        wall = time.time() - t0
        cost = cli.end_scope()
        row = {
            "config": cfg_name, "instance_id": inst["id"], "problem": inst["problem"],
            "rep": rep, "label": inst["label"], "injected_fault": inst["injected_fault"],
            "pred_verdict": v.verdict, "pred_quality": v.quality_score,
            "confidence": v.confidence, "cost_usd": cost, "wall_s": wall,
        }
        with out_lock:
            out.write(json.dumps(row) + "\n")
            out.flush()
            counter["n"] += 1
            print(f"{cfg_name:9s} {inst['id']:34s} rep{rep} "
                  f"pred={v.verdict:6s} gold={inst['label']:6s} "
                  f"${cost:.5f}  cum=${SPEND.total_usd:.4f}")

    try:
        for cfg_name in args.configs:
            verifier = registry[cfg_name]()
            cli = LLMClient(run_tag=cfg_name.replace(".", "_"), config=cfg_name)
            with ThreadPoolExecutor(max_workers=args.workers) as ex:
                futs = [ex.submit(task, cfg_name, verifier, cli, inst, rep)
                        for inst in instances for rep in range(args.reps)]
                for _ in as_completed(futs):
                    pass
            if stop.is_set():
                break
    finally:
        out.close()
    _summary(counter["n"])


def _summary(n_written: int) -> None:
    s = SPEND.summary()
    print(f"\nWrote {n_written} result rows. Spend summary:")
    print(json.dumps(s, indent=2))
    with open(os.path.join(RESULTS_DIR, "spend_summary.json"), "w") as f:
        json.dump(s, f, indent=2)


if __name__ == "__main__":
    main()
