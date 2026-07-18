"""Phase 4 — tables + plots + summary from raw_results.jsonl.

Outputs (results/):
  cost_per_config_problem.csv, quality_metrics.csv, savings_gate.csv, summary.json
  plots/cost_bars_per_solution.png  (per-problem V0->V2 cost bars)
  plots/pareto_cost_quality.png     (cost vs balanced accuracy, all configs)
  plots/marginal_attribution.png    (marginal savings of V1 and V2)
Plots use hatches/markers so they stay legible in grayscale.
"""
from __future__ import annotations

import csv
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from bench.cost import load_rows, per_problem_cost, savings_gate, total_cost
from bench.score import metrics_by_config

HERE = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(HERE, "..", "results")
PLOTS_DIR = os.path.join(RESULTS_DIR, "plots")
ASSETS_DIR = os.path.join(HERE, "..", "presentation", "assets")

PROBLEM_ORDER = ["cox_timepiece_2025", "black_widow_pulsar_2024", "water_and_objects_2023"]
PROBLEM_SHORT = {"cox_timepiece_2025": "Cox 2025",
                 "black_widow_pulsar_2024": "Pulsar 2024",
                 "water_and_objects_2023": "Water 2023"}
CONFIG_ORDER = ["A.V0", "A.V1", "A.V2", "B.V0", "B.V1", "B.V2",
                "C.V0", "C.V1", "C.V2", "composed"]


def _save(fig, name):
    os.makedirs(PLOTS_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)
    for d in (PLOTS_DIR, ASSETS_DIR):
        fig.savefig(os.path.join(d, name), dpi=140, bbox_inches="tight")
    plt.close(fig)


def write_tables(rows):
    ppc = per_problem_cost(rows)
    metrics = metrics_by_config(rows)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    with open(os.path.join(RESULTS_DIR, "cost_per_config_problem.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["config", "problem", "mean_cost_usd", "std_cost_usd", "n_instances"])
        for cfg in CONFIG_ORDER:
            for p in PROBLEM_ORDER:
                d = ppc.get(cfg, {}).get(p)
                if d:
                    w.writerow([cfg, p, f"{d['mean']:.6f}", f"{d['std']:.6f}", d["n"]])

    with open(os.path.join(RESULTS_DIR, "quality_metrics.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["config", "n", "balanced_accuracy", "ba_ci_lo", "ba_ci_hi",
                    "f1_reject", "precision_reject", "recall_reject", "accuracy",
                    "scoring_mae"])
        for cfg in CONFIG_ORDER:
            m = metrics.get(cfg)
            if m:
                w.writerow([cfg, m["n"], f"{m['balanced_accuracy']:.4f}",
                            f"{m['ba_ci95'][0]:.4f}", f"{m['ba_ci95'][1]:.4f}",
                            f"{m['f1_reject']:.4f}", f"{m['precision_reject']:.4f}",
                            f"{m['recall_reject']:.4f}", f"{m['accuracy']:.4f}",
                            f"{m['scoring_mae']:.4f}"])

    gate = savings_gate(rows)
    with open(os.path.join(RESULTS_DIR, "savings_gate.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["solution", "problem", "v0_cost", "v2_cost", "reduction_pct", "pass_50pct"])
        for sol, per_p in gate.items():
            for p in PROBLEM_ORDER:
                d = per_p.get(p)
                if d:
                    w.writerow([sol, p, f"{d['v0']:.6f}", f"{d['v2']:.6f}",
                                f"{d['reduction_pct']:.1f}", d["pass"]])
    return ppc, metrics, gate


def plot_cost_bars(ppc):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=False)
    for ax, sol in zip(axes, ("A", "B", "C")):
        versions = [f"{sol}.V0", f"{sol}.V1", f"{sol}.V2"]
        x = np.arange(len(PROBLEM_ORDER))
        width = 0.25
        hatches = ["", "//", "xx"]
        for i, v in enumerate(versions):
            vals = [ppc.get(v, {}).get(p, {}).get("mean", 0) for p in PROBLEM_ORDER]
            ax.bar(x + (i - 1) * width, vals, width, label=v, hatch=hatches[i],
                   edgecolor="black", color=["0.85", "0.6", "0.35"][i])
        ax.set_xticks(x)
        ax.set_xticklabels([PROBLEM_SHORT[p] for p in PROBLEM_ORDER], rotation=15)
        ax.set_title(f"Solution {sol}: cost per problem")
        ax.set_ylabel("mean cost / instance (USD)")
        ax.legend(fontsize=8)
    fig.suptitle("Per-problem verification cost, V0 -> V1 -> V2")
    fig.tight_layout()
    _save(fig, "cost_bars_per_solution.png")


def plot_pareto(ppc, metrics):
    tot = total_cost(load_rows())
    ni = {cfg: sum(v["n"] for v in ppc.get(cfg, {}).values()) for cfg in CONFIG_ORDER}
    fig, ax = plt.subplots(figsize=(7, 5))
    markers = {"A": "o", "B": "s", "C": "^", "composed": "*"}
    for cfg in CONFIG_ORDER:
        m = metrics.get(cfg)
        if not m or cfg not in tot or not ni.get(cfg):
            continue
        cost_per_inst = tot[cfg] / ni[cfg]
        sol = cfg.split(".")[0] if "." in cfg else "composed"
        ax.scatter(cost_per_inst, m["balanced_accuracy"], s=120,
                   marker=markers.get(sol, "o"), color="0.3",
                   edgecolor="black", zorder=3)
        ax.annotate(cfg, (cost_per_inst, m["balanced_accuracy"]),
                    textcoords="offset points", xytext=(6, 4), fontsize=8)
    ax.set_xscale("log")
    ax.set_xlabel("mean cost / instance (USD, log scale)")
    ax.set_ylabel("balanced accuracy")
    ax.set_title("Cost vs quality Pareto (all configs + composed)")
    ax.grid(True, which="both", ls=":", alpha=0.5)
    fig.tight_layout()
    _save(fig, "pareto_cost_quality.png")


def plot_attribution(ppc):
    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(3)
    width = 0.35
    for i, sol in enumerate(("A", "B", "C")):
        def tot(v):
            return sum(ppc.get(v, {}).get(p, {}).get("mean", 0) for p in PROBLEM_ORDER)
        c0, c1, c2 = tot(f"{sol}.V0"), tot(f"{sol}.V1"), tot(f"{sol}.V2")
        if c0 == 0:
            continue
        d1 = 100 * (c0 - c1) / c0
        d2 = 100 * (c1 - c2) / c0
        ax.bar(i, d1, width, color="0.6", edgecolor="black", hatch="//",
               label="V0->V1" if i == 0 else None)
        ax.bar(i, d2, width, bottom=d1, color="0.3", edgecolor="black", hatch="xx",
               label="V1->V2" if i == 0 else None)
    ax.set_xticks(x)
    ax.set_xticklabels(["Solution A", "Solution B", "Solution C"])
    ax.set_ylabel("cumulative cost reduction vs V0 (%)")
    ax.axhline(50, ls="--", color="black", label="50% target")
    ax.set_title("Marginal savings attribution (V1 and V2)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    _save(fig, "marginal_attribution.png")


def main():
    rows = load_rows()
    ppc, metrics, gate = write_tables(rows)
    plot_cost_bars(ppc)
    plot_pareto(ppc, metrics)
    plot_attribution(ppc)
    tot = total_cost(rows)
    summary = {
        "total_spend_usd": round(sum(tot.values()), 4),
        "per_config_total_usd": {k: round(v, 4) for k, v in tot.items()},
        "savings_gate": gate,
        "quality": {k: {"balanced_accuracy": v["balanced_accuracy"],
                        "ba_ci95": v["ba_ci95"], "f1_reject": v["f1_reject"],
                        "scoring_mae": v["scoring_mae"], "n": v["n"]}
                    for k, v in metrics.items()},
    }
    with open(os.path.join(RESULTS_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    print("\nWrote tables + plots to results/ and presentation/assets/")


if __name__ == "__main__":
    main()
