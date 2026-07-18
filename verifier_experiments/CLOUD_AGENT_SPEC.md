# Cloud-Agent Spec — "50% Cheaper Inference at Equal Quality" for an IPhO-Mechanics Verifier

**Audience:** an autonomous cloud coding agent.
**Deliverable in one line:** design **3 simple verifier solutions**, give **each 2 cumulative improvements**, and **prove that the 2nd improvement of every solution costs ≤50% of that solution's own baseline on all 3 IPhO mechanics problems, with no loss of verification quality** — under a **< $10 total budget, using only OpenAI models** — then package it as interview-grade evidence including a delivery-ready presentation.

Read `verifier_experiments/DEFINITION.MD` first; it defines what a "correct" IPhO-mechanics solution is and the failure-mode taxonomy you will use to build the test set. This spec is the experimental design that operationalizes it into a cost/quality benchmark.

---

## 0. Framing (the interview assignment being answered)

The assignment: *"Design an AI execution system capable of reducing inference costs by 50% while maintaining equal quality."* We scope the "AI execution system" to a **solution verifier** for IPhO-mechanics problems (the workload of our generation pipeline), and "inference cost" to the **OpenAI $/token cost of one verification**. Evaluators care about problem framing, assumption-testing, tradeoffs, credible demonstration, and AI use — not just a number. Optimize for *defensible evidence*, not the headline.

**Non-negotiable intellectual-honesty rules** (these are graded):
- Cost reductions are worthless unless **quality parity is demonstrated on a labeled set**. Never trade quality silently.
- Report **every** configuration, including improvements that fail parity or miss 50%. Negative results are evidence of good judgment.
- Measure cost from **actual logged token usage** (including cached-input and reasoning tokens), never estimate.
- State threats to validity explicitly (small N, self-labeled data, price volatility).

---

## 1. Objective and success criteria

Build a benchmark of **3 solutions × 3 configurations each = 9 verifier configurations**:

- Each **solution** `S ∈ {A, B, C}` is a distinct, independent *cost-reduction lever family* (§4).
- Each solution has a **baseline `V0`** (deliberately simple, genuine, not strawmanned) and **two cumulative improvements `V1 ⊂ V2`** (`V2` builds on `V1`).

**Primary success criterion (definition of "done"):**
> For **each** solution `S` and **each** of the 3 problems `p`:
> `cost(S.V2, p) ≤ 0.5 × cost(S.V0, p)`  **AND**  `quality(S.V2) ≥ quality(S.V0) − ε`
> where `ε` is the pre-registered non-inferiority margin (§3.3).

The 50% must hold **per problem on all 3** (no averaging away a bad problem) and **quality parity per solution** on the pooled labeled set. If a solution can't reach this honestly, say so, show how close it got, and why.

**Secondary (bonus):** a composed "best system" stacking the three levers, with its compounded cost reduction and quality, plus a cost-vs-quality Pareto over all configs.

---

## 2. Workload definition

**Task under test:** given `(problem_statement, candidate_solution)` for one IPhO mechanics problem, output a structured verdict:
```
{ verdict: ACCEPT | REJECT,
  quality_score: float in [0,1],           # normalized earned-marks estimate
  per_subpart: [ {id, pass: bool, points_est: float, reason: str} ],
  first_point_of_failure: str | null }
```
Verifiers run **blind** (never shown the gold label).

**The 3 problems** — the three most-recent genuine mechanics theory problems (pull from `https://ipho.olimpicos.net/`, PDF scheme `IPhO_YYYY_Q{n}.pdf` / `S{n}.pdf`; WebFetch can't parse — download and `pdftotext -layout`):

| # | Problem | Year | Q/S | Mechanics content |
|---|---------|------|-----|-------------------|
| 1 | Cox's Timepiece | 2025 | Q2/S2 | Hydrostatics + rigid-body/pulley + Coulomb friction + energy cycle |
| 2 | Black Widow Pulsar | 2024 | Q3/S3 | Orbital dynamics (effective potential, Lagrange points) + stellar hydrostatic stability |
| 3 | Water and Objects | 2023 | Q3/S3 | Capillary/surface-tension statics + energy conservation |

The 2025 solution carries a full step-level marking scheme — use it as the reference rubric anchor; 2024 and 2023 give per-sub-part point values.

---

## 3. Definitions and measurement

### 3.1 Cost (primary metric)
`cost(config, instance) = Σ_calls (input_tokens · price_in + cached_input_tokens · price_cached_in + output_tokens · price_out)` in USD, from **actual OpenAI usage records**, using a **pinned price table** committed to `prices.json` (model id → in / cached-in / out price per 1M tokens; record retrieval date).

- **Count reasoning tokens.** For OpenAI reasoning models, `completion_tokens_details.reasoning_tokens` are billed as output — include them. Read cached input from `prompt_tokens_details.cached_tokens` and price it at the cached rate.
- Deterministic (non-LLM) checks — CAS, dimensional analysis, regex — count as **$0 token cost**; log their **wall-clock/CPU time** separately so an all-deterministic verdict is transparently ~free of inference cost (the point of Solution B).
- `cost(config, p)` = **mean** cost over all labeled variants of problem `p`.
- Secondary (log, not gated): end-to-end **latency (s)**.

### 3.2 Quality
Measured against the **gold labels** (§3.4), pooled over all variants of all problems:
- **Primary quality = balanced accuracy** of `ACCEPT/REJECT` vs gold (also report F1, precision, recall, confusion matrix).
- **Secondary quality = scoring fidelity**: MAE and Spearman ρ between `quality_score` and the reference earned-marks fraction, on CORRECT + partially-correct variants.

### 3.3 Equal-quality (non-inferiority) gate — pre-register before running
- `ε_primary` = **0.02 balanced-accuracy** OR "no more than 1 additional misclassification vs V0 on the pooled set," whichever is more lenient (state which, given N).
- Secondary: V2's scoring MAE must not exceed V0's by more than `ε_score` (suggest 0.05); gates only if primary is a tie.
- **Bootstrap (≥1000 resamples)** over instances → report 95% CIs on balanced accuracy for every config; state honestly if CIs are wide (they will be — N is small).

### 3.4 Evaluation dataset (gold set) — build in Phase 1
For each of the 3 problems:
1. **1 CORRECT instance** = the official solution (label ACCEPT; reference sub-part scores = full marks).
2. **M INCORRECT/partial instances** (target `M ≈ 8–12` per problem, balanced across the taxonomy) generated by **injecting exactly one documented fault** into a faithful transcription of the official solution, drawn from `DEFINITION.MD` failure modes:
   - sign/direction flip · dropped/added term · wrong physical constant · **unit dropped** · illegitimate approximation (wrong term dropped) · **conservation-law violation** · wrong integration constant from BC · geometric/combinatorial factor error · dimensionless-factor error · wrong governing law.
   - Ground truth is **by construction** (known injected fault → label REJECT + which sub-part fails). Trustworthy labels without human grading.
   - Include a few **hard negatives** whose fault is a dimensionless/geometric factor or a qualitative-plot error — the cases `DEFINITION.MD` says cheap checks go blind on.
3. Freeze the set (`dataset/instances.jsonl` with `label`, `injected_fault`, `failing_subpart`, provenance) and a **held-out dev split** (≈20%) used only for tuning routing thresholds — never for reporting.
4. Curate: verify each injected fault actually makes the solution wrong (ECF can mask some); discard/relabel and **log discards**.

> Total ≈ 3 + ~30 = **~33 instances**. Small — say so, add CIs, and treat the demo as an *existence proof of the mechanism*, not a population statistic.

---

## 4. The three solutions (independent cost-reduction levers)

Recommended defaults. The agent **may refine/substitute a solution only with written justification**, subject to: the three must be **mutually independent levers** (attributable improvements) and each `V0` must be a **fair, simple, genuine** baseline. Improvements are **cumulative**. All models are OpenAI (§8).

### Solution A — Model right-sizing & cascading *(lever: which model)*
- **A.V0** — single call to a **strong OpenAI reasoning model** (top tier), full context, structured verdict. One model does everything.
- **A.V1** — **cheap-first cascade**: a **nano/mini-tier** model verifies first; **escalate to the strong model only** when its self-reported confidence is low or its internal checks disagree. Tune the escalation threshold on the dev split.
- **A.V2** — **calibrate the router** (confidence thresholds + a cheap heuristic gate on features like "answer is dimensionless" or "deliverable is a plot") and add **early-exit** on high-confidence accepts/rejects. Goal: recover A.V0 quality at ≤50% cost. *(Report an ablation showing the naive "just use the mini model" point, to expose the quality risk the cascade fixes.)*

### Solution B — Deterministic-check offload *(lever: whether to call a model at all — the DEFINITION.MD cascade)*
- **B.V0** — single strong-model call does everything, **including** arithmetic, dimensional, and algebraic reasoning in-prompt.
- **B.V1** — add **Tier-0 deterministic falsifiers** that short-circuit before any LLM call: dimensional analysis (Pint), unit-presence, numeric tolerance interval, sign/direction. Obvious rejects/accepts resolved for ~$0.
- **B.V2** — add **Tier-1 symbolic checks** (SymPy): symbolic-equivalence-by-numeric-substitution, plug-back into the solver's stated EOM (residual ≈ 0), conservation residuals; the LLM is invoked **only on the Tier-2 escalation set** (dimensionless/geometric factors, qualitative deliverables, check-disagreement), using the **cheapest adequate** OpenAI model.

### Solution C — Context & decoding efficiency *(lever: how efficiently you call the model — OpenAI-native)*
- **C.V0** — full problem + full solution + verbose reasoning, **high `reasoning_effort`**, **one LLM call per sub-part**, free-form output.
- **C.V1** — **context pruning** (only the relevant sub-part + dependencies; strip PDF boilerplate; compress the reference) **+ Structured Outputs** (`response_format` json_schema) to cut output tokens and drop a parsing pass.
- **C.V2** — **prompt caching** of the shared problem/rubric prefix across sub-parts and the many variants of a problem (order the prompt so the static prefix is first), **+ Batch API** for the eval sweep (50% discount), **+ lower `reasoning_effort`** where quality permits. Report cache-read vs cache-write costs separately.

> A, B, C are orthogonal (which model / whether to use one / how efficiently), so the bonus "best system" composes them and should **exceed** 50%. Make that argument with data.

---

## 5. Measurement methodology & anti-gaming rules

1. **Same everything across configs:** identical dataset, price table, seeds, gold labels. Only the verifier config changes.
2. **Determinism & reps:** temperature 0 (or lowest supported). Because outputs still vary, run **N = 3 repetitions** per (config, instance); report mean ± std cost and majority-vote (or mean) quality.
3. **Blind verification:** the verifier never receives `label`, `injected_fault`, or `failing_subpart`.
4. **No inflated baselines:** `V0` prompts must be reasonable, not padded to make savings look large. Reuse the same prompt skeleton across a solution's configs except for the improvement under test.
5. **Attribution:** improvements are cumulative — report the **marginal** cost/quality delta of V1 and of V2, not just V2.
6. **Cost from raw usage:** persist every OpenAI response's `usage` (incl. cached + reasoning token details) to `runs/*.jsonl`; compute cost from those logs.
7. **Caching honesty:** the 50% claim must hold under realistic cache-hit conditions (amortized over the variant set, not a single warm-cache call). Report cache-write vs cache-read.
8. **Per-problem gate:** the 50% check is evaluated for each of the 3 problems individually.

---

## 6. Acceptance criteria (definition of done — the agent self-checks)

- [ ] `dataset/` frozen: 3 correct + ~30 fault-injected instances, each with label + provenance; dev/report split recorded; discards documented.
- [ ] 9 verifier configs (A/B/C × V0–V2) implemented, each runnable via one command.
- [ ] `prices.json` pinned with retrieval date; cost computed from logged usage incl. cached + reasoning tokens.
- [ ] Results table: cost per (config × problem), quality per config (balanced acc, F1, scoring MAE/ρ), with bootstrap 95% CIs.
- [ ] **Primary criterion demonstrated:** for A, B, and C, `V2 ≤ 0.5 · V0` cost on **all 3 problems** AND quality parity within `ε`. If any solution misses, an explicit written analysis of why + closest result.
- [ ] Plots: (a) per-problem cost bars V0→V2 for each solution; (b) cost-vs-quality Pareto for all 9 + composed system; (c) marginal savings attribution per improvement.
- [ ] Report (`REPORT.md`): problem framing, assumptions + how tested, dataset method, per-solution rationale + tradeoffs, results, **threats to validity**, demonstrated vs extrapolated, composed-system bonus.
- [ ] `DECISION_LOG.md`: chronological register of every material decision — option chosen, alternatives rejected, one-line rationale. Raw material for the presentation; graded as "technical judgment."
- [ ] **`presentation/DECK.pdf`**: delivery-ready, pptx-like slide deck (§12) covering problem statement, reasoning, decisions, method, results, tradeoffs. Also emit editable source.
- [ ] `AI_USE_LOG.md`: every prompt/response the agent used (dataset gen, code, analysis), tagged AI-led / joint / human-led where possible (assignment requirement).
- [ ] `README.md`: exact reproduction steps, pinned OpenAI model ids/versions, seeds, **total budget spent (must be < $10)**.

---

## 7. Repo layout

```
verifier_experiments/
  DEFINITION.MD            # correctness spec (input)
  CLOUD_AGENT_SPEC.md      # this file
  dataset/
    problems/              # pdftotext -layout dumps + transcriptions
    instances.jsonl        # {id, problem, variant, label, injected_fault, failing_subpart, split}
  verifier/
    common/                # openai client + usage logging, structured-verdict schema
    solution_a/ v0..v2
    solution_b/ v0..v2     # + tier0 (pint), tier1 (sympy) modules
    solution_c/ v0..v2
    composed/              # bonus stacked system
  bench/
    run.py                 # run one config over dataset, N reps, log usage
    score.py               # quality metrics + bootstrap CIs
    cost.py                # cost from usage logs + prices.json (cached + reasoning tokens)
    report.py              # tables + plots
  prices.json
  runs/                    # raw per-call usage jsonl
  results/                 # tables (csv) + plots (png/svg)
  presentation/
    DECK.pdf               # delivery-ready pptx-like deck (primary presentation artifact)
    DECK.pptx | deck.md    # editable source (pptx or Marp/reveal)
    assets/                # exported plots reused as slide figures
  REPORT.md
  DECISION_LOG.md
  AI_USE_LOG.md
  README.md
```

---

## 8. Tech stack, models & budget

- **Language:** Python 3.11+; `pytest` harness; `numpy`/`pandas`; `matplotlib` (follow `dataviz` conventions).
- **Provider: OpenAI only.** Use the official `openai` Python SDK. Auth from env — read **`OPENAI_API_KEY`** (the SDK default); if only `OPEN_AI_API_KEY` is present, map it to `OPENAI_API_KEY` at startup. Never print the key.
- **Model ladder (verify current availability, then pin exact ids + prices in `prices.json`):**
  - **Strong tier** — a top OpenAI reasoning model (e.g. `gpt-5` / `o3`-class) for V0 baselines and cascade escalation.
  - **Mid/cheap tier** — a `*-mini` model for the cascade's first pass.
  - **Nano tier** — a `*-nano` model for the cheapest deterministic-adjacent calls.
  - Do **not** hardcode ids you can't confirm; query/verify, then pin. Record model version strings.
- **OpenAI features to exploit (Solution C especially):** automatic **prompt caching** (put the static problem/rubric prefix first; discounted cached-input tokens), the **Batch API** (~50% discount, async — use it for the eval sweep), **`reasoning_effort`** on reasoning models (minimal/low/medium/high), and **Structured Outputs** (`response_format` json_schema).
- **Budget guardrail — hard cap < $10 total.** Implement a **spend tracker** that accumulates cost from each response's usage and **aborts the run if projected spend exceeds $8** (leave headroom). Iterate on nano/mini; reserve strong-tier runs for final numbers; prefer the Batch API for the full sweep. With ~33 instances × 9 configs × 3 reps ≈ 900 calls, staying under $10 is comfortable on mini/nano and disciplined strong-tier use. Log running spend to `README.md`.
- **Deterministic-check libs:** `pint` (units/dimensions), `sympy` (symbolic equivalence, plug-back, conservation residuals).
- **Reproducibility:** fixed seeds, pinned model versions/dates, committed price table, deterministic dataset generation.

---

## 9. Execution plan (phases)

1. **Phase 0 — setup:** repo scaffold, `prices.json`, OpenAI client with usage logging + spend tracker/kill-switch, structured-verdict schema, README skeleton.
2. **Phase 1 — dataset:** pull 3 PDFs, transcribe, generate + curate fault-injected variants, freeze `instances.jsonl`, dev/report split.
3. **Phase 2 — baselines:** implement A.V0, B.V0, C.V0; run; establish reference cost/quality with CIs. Sanity-check baselines actually distinguish correct from injected-fault before optimizing.
4. **Phase 3 — improvements:** implement V1→V2 per solution; tune routers/thresholds on the **dev split only**; run all on the report split via the Batch API.
5. **Phase 4 — analysis:** cost & quality tables, bootstrap CIs, plots, per-improvement attribution; evaluate acceptance criteria; build composed bonus system.
6. **Phase 5 — write-up:** `REPORT.md`, `DECISION_LOG.md`, `AI_USE_LOG.md`, `presentation/DECK.pdf`, finalize `README.md`. Clearly separate demonstrated vs extrapolated.

---

## 10. Threats to validity the report MUST address

- **Small N (~33, 3 problems):** existence proof of mechanism, not a population estimate; mitigate with CIs and per-fault-type breakdown.
- **Self-labeled data:** labels are by-construction from injected faults; risk an injection is masked by ECF or still correct — hence Phase-1 curation + discard log.
- **Price volatility:** $-savings depend on the price table; also report **token-count reduction** (provider-independent) alongside $.
- **Caching realism:** amortize cache costs over the variant set; don't assume a warm cache.
- **Quality-metric coverage:** balanced accuracy can hide sub-part scoring errors; hence scoring MAE/ρ.
- **Generalization:** results are on mechanics; Solution B's determinism advantage is mechanics-specific (per DEFINITION.MD) and may not transfer.

---

## 11. What "good" looks like to the evaluators

Decisive design choices with stated reasoning; a labeled test set that makes "equal quality" falsifiable; cost measured from real usage; honest reporting of configs that fail; a clear separation of demonstrated vs extrapolated; a thorough AI-use log; and a clean, self-contained presentation. The 50%-at-equal-quality result is necessary, but the *reasoning and evidence around it* are what get graded.

---

## 12. Presentation deliverable (PDF, pptx-like)

The **primary hand-off artifact** to the interviewer is `presentation/DECK.pdf` — a slide deck (16:9, ~12–16 slides) that stands on its own without the repo. It must foreground **problem framing, reasoning, and decisions**, not just the final number. Emit an **editable source** too (`.pptx` via the `pptx` skill, or Marp/reveal markdown → PDF).

**Design rules:** one idea per slide; a plain-language takeaway line at the top of each results slide; every number traceable to `results/` (cite the file); charts follow `dataviz` conventions and stay legible in grayscale (it may be printed); no wall-of-text. Speaker notes welcome.

### Slide outline (adapt as needed, keep the arc)

1. **Title** — assignment name, one-line thesis ("50% cheaper IPhO-mechanics verification at equal quality"), candidate/date.
2. **Problem statement** — the assignment verbatim, then *our interpretation*: what "AI execution system", "inference cost", "equal quality" are scoped to, and **why that scoping is defensible**.
3. **The workload** — the IPhO-mechanics verifier + the 3 anchor problems; why verification is the right cost surface for a generation pipeline.
4. **The crux: what "equal quality" even means** — correctness axes + failure-mode taxonomy; cost cuts are meaningless without a quality gate. (Intellectual centerpiece.)
5. **Decision log (condensed)** — a table of 5–7 pivotal decisions: option chosen · alternatives rejected · rationale (scoping, cost metric, quality metric, labeled-dataset-by-injection, per-problem-50% rule, OpenAI ladder).
6. **Approach overview** — the three independent cost levers (A: which model · B: whether to call one · C: how efficiently) on one diagram; why independence matters for attribution and composition.
7. **Method — labeled test set & fair measurement** — correct + fault-injected variants, self-labeling, blind verification, cost-from-real-usage (incl. reasoning/cached tokens), N reps, anti-gaming.
8. **Solution A** — V0→V2 arc + per-problem cost bars + quality parity; call out where the naive mini-model swap *lost* quality and how the cascade recovered it.
9. **Solution B** — V0→V2 arc + result; the deterministic-offload story (the DEFINITION.MD cascade); mechanics-specific advantage.
10. **Solution C** — V0→V2 arc + result; pruning + caching + Batch + reasoning-effort savings; caching-realism caveat.
11. **Headline result** — per-problem 50% table across all 3 solutions (all 3 problems), with the pass/fail gate shown honestly.
12. **Cost-vs-quality Pareto** — all 9 configs + composed system; the tradeoff at a glance.
13. **Composed best system (bonus)** — stacking A+B+C; compounded savings and where they stop compounding.
14. **Tradeoffs & what's credibly demonstrated** — demonstrated vs extrapolated; where each lever breaks; generalization beyond mechanics.
15. **Threats to validity** — small N + wide CIs, self-labeled data, price volatility, caching assumptions — stated plainly.
16. **AI use, reproducibility & close** — how AI tools were used (AI-led/joint/human-led), budget spent (< $10), one-command repro; thesis restated with the evidence; next steps with more time.

### Tooling
Prefer the `pptx` skill for a native editable deck, or Marp/reveal.js markdown → PDF for a lighter path; either way `DECK.pdf` is the graded artifact. Reuse the exact plots from `results/` (don't redraw by hand — traceability). Keep the deck self-contained (embedded fonts/images) so it renders identically on the evaluator's machine.
