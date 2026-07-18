"""Quality metrics from raw_results.jsonl.

Verdict per instance = majority vote over reps. Metrics vs gold (pooled over all
report instances): balanced accuracy, F1, precision, recall, confusion matrix,
plus bootstrap 95% CIs on balanced accuracy. Secondary: scoring MAE between
predicted quality_score and the reference earned-marks fraction.
"""
from __future__ import annotations

import json
import os
from collections import Counter, defaultdict

import numpy as np

from bench.problems_data import PROBLEMS

HERE = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(HERE, "..", "results")
RAW = os.path.join(RESULTS_DIR, "raw_results.jsonl")
DATASET = os.path.join(HERE, "..", "dataset", "instances.jsonl")


def _instances():
    return {i["id"]: i for i in (json.loads(l) for l in open(DATASET))}


def reference_quality_fraction(inst: dict) -> float:
    """True earned-marks fraction: 1.0 if correct; else (total-failing)/total."""
    if inst["label"] == "ACCEPT":
        return 1.0
    problem = PROBLEMS[inst["problem"]]
    total = sum(sp["points"] for sp in problem["subparts"])
    fail_pts = next((sp["points"] for sp in problem["subparts"]
                     if sp["id"] == inst["failing_subpart"]), 0.0)
    return (total - fail_pts) / total if total else 0.0


def load_rows(path: str = RAW) -> list[dict]:
    return [json.loads(l) for l in open(path)]


def per_instance_pred(rows: list[dict]):
    """(config,instance)-> {verdict(majority), quality(mean)}."""
    verds: dict[tuple, list[str]] = defaultdict(list)
    quals: dict[tuple, list[float]] = defaultdict(list)
    for r in rows:
        verds[(r["config"], r["instance_id"])].append(r["pred_verdict"])
        quals[(r["config"], r["instance_id"])].append(r["pred_quality"])
    out = {}
    for k in verds:
        maj = Counter(verds[k]).most_common(1)[0][0]
        out[k] = {"verdict": maj, "quality": float(np.mean(quals[k]))}
    return out


def _balanced_accuracy(y_true, y_pred) -> float:
    # classes: ACCEPT / REJECT
    recalls = []
    for cls in ("ACCEPT", "REJECT"):
        idx = [i for i, t in enumerate(y_true) if t == cls]
        if not idx:
            continue
        tp = sum(1 for i in idx if y_pred[i] == cls)
        recalls.append(tp / len(idx))
    return float(np.mean(recalls)) if recalls else 0.0


def _prf(y_true, y_pred, positive="REJECT"):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p == positive)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != positive and p == positive)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p != positive)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1


def bootstrap_ci(y_true, y_pred, n=1000, seed=7):
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y_true))
    stats = []
    for _ in range(n):
        s = rng.choice(idx, size=len(idx), replace=True)
        stats.append(_balanced_accuracy([y_true[i] for i in s], [y_pred[i] for i in s]))
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def metrics_by_config(rows: list[dict]):
    insts = _instances()
    preds = per_instance_pred(rows)
    by_cfg: dict[str, list[tuple]] = defaultdict(list)
    for (cfg, iid), pv in preds.items():
        by_cfg[cfg].append((iid, pv))
    out = {}
    for cfg, items in by_cfg.items():
        y_true = [insts[iid]["label"] for iid, _ in items]
        y_pred = [pv["verdict"] for _, pv in items]
        ba = _balanced_accuracy(y_true, y_pred)
        lo, hi = bootstrap_ci(y_true, y_pred)
        prec, rec, f1 = _prf(y_true, y_pred)
        # confusion
        cm = Counter((t, p) for t, p in zip(y_true, y_pred))
        # scoring MAE
        errs = [abs(pv["quality"] - reference_quality_fraction(insts[iid]))
                for iid, pv in items]
        out[cfg] = {
            "n": len(items),
            "balanced_accuracy": ba, "ba_ci95": [lo, hi],
            "precision_reject": prec, "recall_reject": rec, "f1_reject": f1,
            "accuracy": sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(items),
            "scoring_mae": float(np.mean(errs)),
            "confusion": {f"{t}->{p}": c for (t, p), c in cm.items()},
        }
    return out


if __name__ == "__main__":
    rows = load_rows()
    m = metrics_by_config(rows)
    for cfg in sorted(m):
        d = m[cfg]
        print(f"{cfg:9s} BA={d['balanced_accuracy']:.3f} "
              f"CI[{d['ba_ci95'][0]:.2f},{d['ba_ci95'][1]:.2f}] "
              f"F1={d['f1_reject']:.3f} acc={d['accuracy']:.3f} "
              f"MAE={d['scoring_mae']:.3f} n={d['n']}")
