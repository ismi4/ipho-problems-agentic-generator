"""Cost aggregation from measured per-call spend (raw_results.jsonl).

cost(config, instance) = mean over reps of measured USD (real OpenAI usage).
cost(config, problem)  = mean over that problem's instances.
Also reports total cost and the per-problem V2<=0.5*V0 gate.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(HERE, "..", "results")
RAW = os.path.join(RESULTS_DIR, "raw_results.jsonl")


def load_rows(path: str = RAW) -> list[dict]:
    return [json.loads(line) for line in open(path)]


def per_instance_cost(rows: list[dict]) -> dict[tuple[str, str], float]:
    """(config, instance_id) -> mean cost over reps."""
    acc: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        acc[(r["config"], r["instance_id"])].append(r["cost_usd"])
    return {k: float(np.mean(v)) for k, v in acc.items()}


def per_problem_cost(rows: list[dict]) -> dict[str, dict[str, dict[str, float]]]:
    """config -> problem -> {mean, std, n} of per-instance mean cost."""
    inst_cost = per_instance_cost(rows)
    inst_problem = {(r["config"], r["instance_id"]): r["problem"] for r in rows}
    buckets: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (cfg, iid), c in inst_cost.items():
        buckets[cfg][inst_problem[(cfg, iid)]].append(c)
    out: dict[str, dict[str, dict[str, float]]] = {}
    for cfg, probs in buckets.items():
        out[cfg] = {}
        for p, cs in probs.items():
            out[cfg][p] = {"mean": float(np.mean(cs)), "std": float(np.std(cs)),
                           "n": len(cs), "total": float(np.sum(cs))}
    return out


def total_cost(rows: list[dict]) -> dict[str, float]:
    acc: dict[str, float] = defaultdict(float)
    for r in rows:
        acc[r["config"]] += r["cost_usd"]
    return dict(acc)


def savings_gate(rows: list[dict], solutions=("A", "B", "C")):
    """Per-problem V2<=0.5*V0 check for each solution."""
    ppc = per_problem_cost(rows)
    problems = sorted({r["problem"] for r in rows})
    result = {}
    for sol in solutions:
        v0, v2 = f"{sol}.V0", f"{sol}.V2"
        if v0 not in ppc or v2 not in ppc:
            continue
        per_p = {}
        for p in problems:
            c0 = ppc[v0].get(p, {}).get("mean")
            c2 = ppc[v2].get(p, {}).get("mean")
            if c0 is None or c2 is None:
                continue
            ratio = c2 / c0 if c0 else float("inf")
            per_p[p] = {"v0": c0, "v2": c2, "ratio": ratio,
                        "reduction_pct": 100 * (1 - ratio), "pass": ratio <= 0.5}
        result[sol] = per_p
    return result


if __name__ == "__main__":
    rows = load_rows()
    print("Total cost per config:")
    for c, v in sorted(total_cost(rows).items()):
        print(f"  {c:9s} ${v:.4f}")
    print("\nPer-problem V2<=0.5*V0 gate:")
    for sol, per_p in savings_gate(rows).items():
        print(f"  Solution {sol}:")
        for p, d in per_p.items():
            print(f"    {p:28s} V0=${d['v0']:.4f} V2=${d['v2']:.4f} "
                  f"reduction={d['reduction_pct']:5.1f}%  {'PASS' if d['pass'] else 'FAIL'}")
