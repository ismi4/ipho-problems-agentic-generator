# 50% Cheaper IPhO-Mechanics Verification at Equal Quality — Report

**Thesis.** For an automated verifier of IPhO-mechanics solutions, three *independent*
cost-reduction levers each reach a **≥50% per-problem cost reduction** vs their own
baseline. Two of the three (**B: deterministic offload**, **C: context/decoding
efficiency**) do so **at equal-or-better verification quality**; the third
(**A: model right-sizing**) reaches the cost target but **misses the quality
non-inferiority gate** — a genuine negative result. A **composed A+B+C system** verifies
at **balanced accuracy 1.00 for ~$0.0025/instance**.

All numbers below are traceable to `results/` (CSV + `summary.json`) and computed from
**actual OpenAI usage logs** in `runs/`. Total OpenAI spend for the reported sweep:
**$5.48**; total incurred over the whole project incl. dev/smoke/aborted runs:
**$6.77** — both under the **$10** cap (hard kill-switch at $8/run).

---

## 1. Framing & scope
The assignment ("design an AI execution system that cuts inference cost 50% at equal
quality") is scoped to a **solution verifier** for IPhO-mechanics problems — the
recurring cost surface of a problem-generation pipeline (`DEFINITION.MD`) — and
"inference cost" to **OpenAI $/token per verification**. "Equal quality" is a
**non-inferiority gate** on ACCEPT/REJECT balanced accuracy against a labeled set.
See `DECISION_LOG.md` for the decisions and rejected alternatives.

## 2. Workload & dataset
**Task.** Given `(problem_statement, reference_answer_key, candidate_solution)`, emit a
structured verdict (`ACCEPT|REJECT`, `quality_score`, `per_subpart`,
`first_point_of_failure`, `confidence`). The verifier sees the reference rubric but is
**blind** to the gold label / injected fault.

**Gold set (by construction).** For each of 3 problems — Cox's Timepiece (2025),
Black Widow Pulsar (2024), Water and Objects (2023) — 1 CORRECT instance (official
answers) + 9 REJECT instances, each injecting **exactly one documented fault**
(sign flip, dropped/added term, wrong constant, unit dropped, geometric/dimensionless
factor, wrong BC constant, conservation violation, wrong law, regime misclassification).
**30 instances** total (`dataset/instances.jsonl`), a ~20% **dev** split (6, tuning
only) and 24 **report** instances. Every non-qualitative fault was **curated** with the
deterministic checker to confirm it truly falsifies against the reference:
**0 discards** (`dataset/discards.log`). Machine-checkable sub-part answers are stored
as SymPy/Pint objects; qualitative deliverables (e.g. Cox A.2 A/A/B regime) carry no
algebraic form and are the LLM-escalation set by design.

## 3. Measurement
`cost = Σ (uncached_in·p_in + cached_in·p_cached + out·p_out)` from each response's real
`usage` (reasoning tokens billed as output; cached tokens read from
`prompt_tokens_details`), priced from `prices.json` (pinned `gpt-5`/`gpt-5-mini`/
`gpt-5-nano`, retrieved 2026-07-18). Deterministic checks are **$0 token cost**, timed
separately. Cost per verify() is captured by a per-thread scope accumulator; a
process-wide tracker **aborts at $8**. Quality = **majority-vote verdict** over reps vs
gold; **balanced accuracy** primary (+ F1, accuracy, scoring MAE), with **bootstrap
95% CIs** (1000 resamples). **Reps: N=2** for the strong-model V0 baselines, **N=3** for
the cheaper configs (budget; see §7).

## 4. The three levers

### Solution A — model right-sizing & cascade (which model)
`A.V0` one `gpt-5` call · `A.V1` nano-first cascade, escalate if confidence < 0.7 ·
`A.V2` calibrated router (dev-tuned threshold + accept-guard: trust confident cheap
REJECTs, but re-check nano ACCEPTs on hard problems with `gpt-5`).

### Solution B — deterministic offload (whether to call a model)
`B.V0` one `gpt-5` call does everything in-prompt · `B.V1` Pint Tier-0 falsifiers
short-circuit obvious rejects, else `gpt-5` · `B.V2` + SymPy Tier-1 equivalence resolves
all machine-checkable sub-parts for ~$0; nano is called **only** on qualitative
deliverables.

### Solution C — context & decoding efficiency (how efficiently)
Model tier fixed = `gpt-5`. `C.V0` one call per sub-part, full context, high
`reasoning_effort` · `C.V1` pruned context + Structured Outputs, medium · `C.V2` cached
shared prefix (placed first) + low `reasoning_effort`.

## 5. Results

### 5.1 Primary gate — per-problem V2 ≤ 0.5·V0 cost (from `results/savings_gate.csv`)

| Solution | Cox 2025 | Pulsar 2024 | Water 2023 | Verdict |
|---|---|---|---|---|
| **A** | −73.2% | −67.6% | −97.3% | **PASS (all 3)** |
| **B** | −99.6% | −100% | −100% | **PASS (all 3)** |
| **C** | −71.9% | −64.9% | −62.4% | **PASS (all 3)** |

All three solutions meet the 50% cost reduction on **every** problem individually.

### 5.2 Quality (from `results/quality_metrics.csv`; ε = 0.02 BA or ≤1 extra miss)

| Config | Balanced acc | 95% CI | F1(reject) | Scoring MAE | Parity vs V0 |
|---|---|---|---|---|---|
| A.V0 | 0.952 | [0.87, 1.00] | 0.950 | 0.023 | (baseline) |
| A.V1 | 0.881 | [0.75, 0.97] | 0.865 | 0.054 | ✗ (−0.071, +3 miss) |
| **A.V2** | **0.881** | [0.75, 0.95] | 0.865 | 0.060 | **✗ misses gate** |
| B.V0 | 0.952 | [0.87, 1.00] | 0.950 | 0.024 | (baseline) |
| B.V1 | 1.000 | [1.00, 1.00] | 1.000 | 0.262 | ✓ (BA); coarse scoring |
| **B.V2** | **1.000** | [1.00, 1.00] | 1.000 | 0.000 | **✓ improves** |
| C.V0 | 0.952 | [0.88, 1.00] | 0.950 | 0.018 | (baseline) |
| C.V1 | 0.976 | [0.92, 1.00] | 0.976 | 0.008 | ✓ improves |
| **C.V2** | **0.976** | [0.92, 1.00] | 0.976 | 0.013 | **✓ improves** |
| **composed** | **1.000** | [1.00, 1.00] | 1.000 | 0.000 | **✓** |

### 5.3 Combined verdict (cost AND quality)
- **Solution B — SUCCESS:** ~100% cost reduction **and** quality *improves* (0.952→1.000).
- **Solution C — SUCCESS:** 62–72% cost reduction **and** quality *improves* (0.952→0.976).
- **Solution A — PARTIAL (honest negative):** ≥67% cost reduction but BA drops
  0.952→0.881 (3 extra misclassifications), **failing** the non-inferiority gate.

### 5.4 Why — the error analysis is the punchline
Every misclassification in the whole sweep is a **false ACCEPT** (a missed fault). The
**two faults the strong `gpt-5` baseline misses are both *unit-dropped* faults**
(`cox…__04`, `water…__02`): the LLM does not reliably penalize a missing unit. This is
exactly the DEFINITION.MD Tier-0 falsifier that **Pint** catches deterministically — so
**B.V1/B.V2 and the composed system reach BA = 1.000**. Solution A makes it *worse*:
`gpt-5-nano` misses additional subtle faults (geometric/sign), adding 3 more false
accepts — the quality risk of naive right-sizing that the cascade only partially
recovers. Solution C keeps the strong model, so it inherits only the single unit blind
spot (C.V2 misses just `water…__02`).

### 5.5 Marginal attribution & composition
Marginal savings (V0→V1, V1→V2) are in `results/plots/marginal_attribution.png`. Because
the levers are orthogonal (which / whether / how), they **compose**: the composed system
resolves machine-checkable sub-parts deterministically (B), prunes+caches the rest (C),
and verifies cheap-first (A), reaching **BA 1.000 at ~$0.0025/instance** (`composed`
total $0.060 over 24×3 = 72 verifications) — far beyond any single lever's 50%.

Plots: `results/plots/cost_bars_per_solution.png`, `pareto_cost_quality.png`,
`marginal_attribution.png` (also in `presentation/assets/`).

## 6. Acceptance-criteria self-check
- [x] Dataset frozen (3 correct + 27 faults), labels+provenance, dev/report split, discards logged (0).
- [x] 9 configs + composed, each runnable via one command (`bench/run.py`).
- [x] `prices.json` pinned+dated; cost from logged usage incl. cached+reasoning tokens.
- [x] Results tables: cost per (config×problem), quality per config, bootstrap 95% CIs.
- [x] Primary criterion evaluated per problem for A, B, C; misses reported (A).
- [x] Plots (cost bars, Pareto, marginal attribution).
- [x] `REPORT.md`, `DECISION_LOG.md`, `AI_USE_LOG.md`, `presentation/DECK.pdf`, `README.md`.
- [x] Total budget spent recorded (< $10).

## 7. Threats to validity
- **Small N (30 instances, 3 problems).** Existence proof of the *mechanism*, not a
  population estimate; CIs are wide (e.g. A.V2 [0.75, 0.95]). Reported honestly.
- **Self-labeled data.** Labels are by-construction; mitigated by curation + discard log,
  but an injection could in principle be ECF-masked (none detected here).
- **Dev split is all-REJECT.** Threshold calibration could not see ACCEPT confidences, so
  A's router is under-calibrated on the accept side — plausibly part of A's parity miss.
- **Reduced reps on strong V0 baselines (N=2, budget).** Per-instance costs are
  rep-averaged so the 50% gate is unaffected; residual reasoning-token variance may
  slightly move V0 means.
- **Price volatility.** $-savings depend on `prices.json`; token-count reductions (which
  drive them) are provider-independent and directionally identical.
- **Caching realism.** C.V2 relies on automatic prompt caching of the shared prefix across
  a problem's sub-part calls; savings are reported over the realized calls, not a single
  idealized warm cache. The Batch API would add a further ~50% for an offline sweep.
- **Generalization.** Solution B's determinism advantage is mechanics-specific (explicit
  EOMs, conserved quantities, tight [M,L,T] space); it may not transfer to general physics.

## 8. Bottom line
The **mechanism** is demonstrated: on mechanics verification, **deterministic offload (B)**
and **context/decoding efficiency (C)** deliver >50% cost cuts with **no quality loss**,
while **model right-sizing (A)** buys cost at a measurable quality cost here. The most
valuable, transferable finding is that a cheap deterministic Pint/SymPy layer removes a
*systematic LLM blind spot* (missing units / subtle factors), so combining it with the
efficiency lever yields a verifier that is **both cheaper and better** than the
strong-model baseline.
