# Four Verifier Systems — Cost/Quality Ladder

*Four candidate architectures for the IPhO-mechanics solution verifier, ordered most → least sophisticated, with a cost model calibrated to OpenAI pricing as of 2026-07-18. Companion to [DEFINITION.MD](DEFINITION.MD), which defines what "correct" means; this document is about what it costs to check.*

> **Scope.** These systems verify the **reference solution `S`** against the problem `P` (per DEFINITION.MD §0). Divergent-`P` / well-posedness work (`V_P`) is explicitly out of scope for now — `P` is treated as given and trusted. Generator-side changes (proof-carrying DSL emission) are also out of scope.

---

## 0. Model selection policy

Per the cost-optimization constraint, **`gpt-5.6-terra` is the model everywhere** — ingestion, judging, agentic loops, and the expert-escalation tier alike. `gpt-5.6-luna` and `gpt-5.4-mini` carry bulk and mechanical work in the cheaper systems. **The frontier tier (`gpt-5.6-sol`) is not used at all.**

| Model | Input $/MTok | Cached input | Output $/MTok | Role in these systems |
|---|---|---|---|---|
| `gpt-5.6-terra` | $2.50 | $0.25 | $15.00 | **Everything** — ingestion, judging, agentic loops, escalation |
| `gpt-5.6-luna` | $1.00 | $0.10 | $6.00 | Bulk per-sub-part judging in the cheap tiers |
| `gpt-5.4-mini` | $0.75 | — | $4.50 | Degraded-mode ingestion |
| `gpt-5.6-sol` | $5.00 | $0.50 | $30.00 | **Not used** — see below |
| `gpt-5.4-nano` | $0.20 | — | $1.25 | Not used (insufficient for any tier here) |

> **The `sol` decision is a deliberate, unvalidated bet.** Capping at `terra` roughly halves the cost of the escalation tier, which is the dominant line item in every system below. But escalation is exactly where DEFINITION.MD §3 says the *irreducible expert core* lives — faithfulness, frame/constraint validity, law-applicability, non-menu case completeness, provenance. Those are the judgments most likely to be capability-limited rather than prompt-limited. **The mutation harness (§6) should test a `sol` escalation tier as an explicit arm**: if `terra` and `sol` catch the same injected faults, the saving is free; if `sol` catches faults `terra` misses, the ~2× on that tier alone is likely worth paying, since it is a small fraction of sub-parts.

**Cost mechanics that shape the architectures:**

- **Prompt caching is automatic** — cached input bills at 10% of standard rate. There is no `cache_control` plumbing; you earn it purely by prompt layout (stable prefix first, volatile content last). Reported 1.25× cache-write premium and ~30-minute minimum cache lifetime on the 5.6 family — **verify this before relying on it**, it was not on the official pricing page.
- **Batch API is a flat 50%** discount, at the cost of async latency.
- **Reasoning tokens bill as output tokens.** Every output figure below therefore carries reasoning spend, and **reasoning effort is a first-class cost lever** on par with model choice. The output estimates here assume moderate effort; they are the least certain numbers in this document.

---

## 1. Ingestion ladder

Every system below picks a rung. This choice caps the ceiling of everything downstream.

| | Ingestion | Loses |
|---|---|---|
| **I0** | **Don't ingest the PDF.** Tap the pre-render artifact (LaTeX/MD + figure source) from the generator | Nothing — but doesn't verify what was *rendered* |
| **I1** | `pymupdf` raw text | All math structure, figures, layout |
| **I2** | Vision-model page images → Markdown+LaTeX transcription | Figure semantics; silent transcription hallucination |
| **I3** | I2 + round-trip check (re-render, diff against original, retry on mismatch) | Little — catches transcription drift |
| **I4** | I3 + **typed semantic IR**: sub-parts, givens with units, equations as parseable trees, BCs, asked-quantity + answer-type, figure descriptions, each with a provenance span | This is the real deliverable |

**I0 is the highest-leverage decision available.** You control the generator, so you should not be OCR-ing your own output. Keep the PDF path alive only as a *render-fidelity* check — did the PDF a student sees still say what `S` assumed? A figure that didn't regenerate or an overfull box eating a subscript is a genuine `V_{P→S}` failure, and it is the only reason to touch the PDF at all.

> ### ⚠️ Open question: what does I4 actually cost?
> The cost model below assumes I4 transcribes in roughly one pass. **This is unvalidated and it moves every number in this document.** If IPhO solution PDFs need 2–3 vision round-trips for dense math and figures, ingestion triples.
>
> **Settle this first**, using the two files named in §6 — the clean/faulty 2023 pair. It costs a few dollars of API spend and pins the input cost for all four systems. Prior: I4 is cheap, because image tokens dominate either way and the marginal cost of a richer output schema is output tokens only.

---

## 2. The deterministic layer is not a system

SymPy + Pint over the IR — dimensional homogeneity, units present, sig-figs, numeric-in-tolerance, symbol-whitelist, sign/direction fields populated — plus CAS symbolic equivalence and EOM plug-back residual.

This runs in milliseconds and costs **$0** at inference time. It is present in **all four systems below** and is **never one of them**. It has no semantics: it cannot connect `P`'s physical model to `S`'s, so it can only refute, never certify. Its cost sits entirely in the LLM pass that produces the IR.

One caveat on CAS: "sanctioned approximation" handling is not purely mechanical. Deciding *which* small parameter to expand in and to what order is a judgment call that the IR extraction must carry — $0 of new spend, but it adds requirements to the extraction schema.

---

## 3. Prompt-engineering techniques for the judge tier

These apply to S3/S2/S1, where a model adjudicates a sub-part directly.

1. **Answer-type routing.** DEFINITION.MD §1.4 identifies ~6 pre-declarable answer forms. Select the type in a separate cheap call, then dispatch to a *type-specific* judge prompt — a "show-that" checker and a "graph feature list" checker share almost no rubric. This directly addresses §7.6 (answer mis-typing silently applies a weaker test) by making the type an explicit, auditable decision.

2. **Schema-as-CoT.** Rather than free-form "think step by step," force a structured output whose *field order is the reasoning order*: `governing_law_identified → regime_assumed → dimensional_check → case_branches_found → first_point_of_failure → verdict`. The schema performs the decomposition, and every field is independently inspectable when a verdict is wrong — far better than prose CoT as a training/reward signal.

3. **Extract-then-adjudicate split.** Two calls: one produces the IR from `S`, one judges the IR against `P`. Combined, the model launders its own extraction errors into the verdict — it reads what it expected to read, then confirms it. Splitting makes extraction faults visible *as* extraction faults.

4. **Refuter framing.** "Produce one concrete falsifying instance — a limiting case where this breaks, a case split it skipped, a datum it ignored — or state that you failed to find one" beats "is this correct?". Models generate counterexamples far better than they render global verdicts. Default the frame to *refuted unless refutation failed*.

5. **Mutation-derived few-shots.** Once the mutation harness (§5) exists, injected faults become the exemplar set: a sign flip, a dropped factor of 2, a missed stick/slip branch. Real in-distribution negatives rather than synthetic ones. Highest-leverage prompt change available, and free once the harness exists.

**Cross-cutting (cost, not quality):** lay every prompt out **stable-prefix-first** — `P` and `S` at the front, the sub-part question at the very end. OpenAI's caching is automatic and prefix-matched, so this single layout rule is worth roughly 3× on the judge tier. Twelve sub-part calls that each re-read a 16k prefix at full price is pure waste.

---

## 4. The four systems

**Costing assumptions.** ~12 sub-parts per problem; `P` ≈ 4k tokens and `S` ≈ 12k tokens post-ingestion (16k shared context); ~11 PDF pages ≈ 18k image tokens. Automatic prefix caching assumed throughout. **These are order-of-magnitude estimates, not quotes** — the ingestion experiment (§1) and reasoning-token spend (§0) both move them.

### S4 — Agentic verifier, per-sub-part tool loop — **~$2.79/problem**

I4 ingestion with round-trip verification. For each sub-part, a `terra` agent with a SymPy/NumPy sandbox writes and executes its own checks — dimensional, limiting-case, conservation residual, plug-back — then adjudicates on execution results rather than assertion. Findings go to a 3-vote adversarial refuter panel.

| Component | Model | Cost |
|---|---|---|
| Ingestion (I4 + round-trip, ~1.4× retry factor) | `terra` | ~$0.39 |
| 12 × agent loop (~60k cached input / 8k output each) | `terra` | ~$2.04 |
| Adversarial verify, 3 votes × ~4 flagged sub-parts | `terra` | ~$0.36 |

**What you get:** the model builds a verifier optimized per problem, and every pass/fail is grounded in execution. Best quality, and — importantly — the best *early-eval signal*: it tells you which checks each problem actually needed, information the other three architectures cannot produce.

**What you pay for:** a code sandbox, a script-quality gate (a script that trivially passes everything is the failure mode), and ~2.2× S3.

### S3 — Structured cascade with escalation — **~$1.24/problem**

I4 ingestion → deterministic Tier-0 ($0) → per-sub-part `terra` judge using techniques 1/2/4 → escalate ~25% of sub-parts to an S4-style `terra` agent loop. Escalation triggers per DEFINITION.MD §5: dimensionless/bare-number answers, circular plug-back with no second method, Tier-0/Tier-1 disagreement, qualitative deliverables, case-menu boundary risk.

| Component | Model | Cost |
|---|---|---|
| Ingestion (I4) | `terra` | ~$0.28 |
| Deterministic Tier-0 (SymPy + Pint + CAS + plug-back) | — | $0 |
| 12 × sub-part judge (cached prefix, ~2k output each) | `terra` | ~$0.45 |
| ~3 × escalated agent runs | `terra` | ~$0.51 |

**This is the natural V1.** Full architecture; escalation is now a *capability* difference (tools + multi-turn reasoning) rather than a *model-tier* difference, and it fires only where the cheap layer is provably silent.

### S2 — S3 with the bulk tier cheapened — **~$0.63 (51% of S3)**

Identical architecture and identical escalation logic. Two changes:

- **Judge tier drops `terra` → `luna`.** A wrong verdict on this tier escalates anyway, so the quality exposure is bounded.
- **Ingestion drops to `luna`,** with `terra` invoked only when the round-trip check fails.

The escalation tier **stays on `terra`** — deliberately. This is the design principle: cheapen the bulk, never the expert residue.

| Component | Model | Cost |
|---|---|---|
| Ingestion (I4) | `luna` | ~$0.11 |
| 12 × sub-part judge (cached prefix) | `luna` | ~$0.18 |
| ~2 × escalated agent runs | `terra` | ~$0.34 |

### S1 — Single-pass, no escalation — **~$0.20 (32% of S2)**

I2 ingestion (no round-trip, no full IR — **so the deterministic layer is gone**). One `luna` pass per sub-part with the rubric schema, submitted via the Batch API at 50% off. No escalation tier, no adversarial pass.

| Component | Model | Cost |
|---|---|---|
| Ingestion (I2) | `gpt-5.4-mini` | ~$0.05 |
| 12 × sub-part judge, batched | `luna` | ~$0.09 |
| Escalation | — | $0 |
| Deterministic Tier-0 | — | unavailable (no IR) |

**What you lost:** the entire DEFINITION.MD §5 Tier-2 trigger list. Dimensionless and geometric-factor answers, qualitative deliverables, and Tier-0/Tier-1 disagreements now receive the same treatment as a clean symbolic answer. Per §6, that is the **highest residual risk in the whole spec**. Plus batch latency (minutes to an hour) — fine for offline generation, fatal for interactive use.

---

## 5. What "half cost" actually means here

| Step | Factor | What it cost in quality |
|---|---|---|
| S4 → S3 | **2.2×** | Agentic checks only where triggered, not everywhere. Real but bounded. |
| S3 → S2 | **2.0×** | **Almost nothing.** Model-tier drop on a bulk layer that escalates on doubt. |
| S2 → S1 | **3.2×** | The entire expert residue *and* the deterministic layer. This is where you eat the definition. |

The first two steps are clean halvings and the third is not, for one reason:

> **With prefix caching and a single model tier, bulk judging is nearly free. The money is in how many sub-parts escalate to an agent loop.**

In S2, escalation is **54% of total cost** ($0.34 of $0.63) while adjudicating ~2 of 12 sub-parts. Twelve fully-cached `luna` judgments cost $0.18 — roughly half of two agent runs. That reframes the cost question. It is not "which model do we use" (the bulk tier is a rounding error anywhere from `luna` to `terra`); it is **"how many sub-parts escalate, and can we predict which ones cheaply?"**

Three consequences:

1. **The S3 → S2 saving is nearly free and should just be taken.** Prefix-cache layout costs one prompt reordering; the `terra` → `luna` drop on the bulk tier is bounded by escalation.
2. **Tightening the escalation trigger is worth more than any model swap.** A trigger that fires on 2 sub-parts instead of 3 saves more than moving the entire bulk tier from `terra` to `nano`. Conversely, a trigger that fires on 6 sub-parts roughly doubles system cost regardless of what the judge tier runs on.
3. **Because escalation is now `terra` rather than `sol`, the escalation tier is cheap enough that the trigger can afford to be generous** — over-escalating is no longer a 2× penalty on those sub-parts. If the mutation harness shows recall is trigger-limited rather than capability-limited, widening the trigger is the cheapest available quality gain.

---

## 6. First experiment — inputs

**Use exactly these two files, as a matched clean/faulty pair:**

| Role | Path |
|---|---|
| **Clean (must PASS)** | `verifier_experiments/pdfs/IPhO_2023_S3.pdf` (5 pp.) |
| **Faulty (must FAIL)** | `verifier_experiments/pdfs/faulty/IPhO_2023_S3_FAULTY.pdf` (5 pp.) — errors deliberately injected |

Problem statement for both: `verifier_experiments/pdfs/IPhO_2023_Q3.pdf` (4 pp.).

**Why this pair.** 2023 Q3 "Water and Objects" is **entirely within Class M** — Part A is surface-energy→kinetic-energy conservation, Part B is hydrostatics plus surface-tension statics, Part C is floating-body force balance. Nothing leaks into SR or wave propagation, so every result is signal about the mechanics core rather than about out-of-distribution handling. It is also small (4 + 5 pages), which keeps the ingestion experiment cheap.

It happens to exercise several of the exact mechanisms DEFINITION.MD singles out:

- **Explicit symbol whitelists on nearly every sub-part** ("express 𝑃 in terms of 𝜌, 𝑔, 𝑧, and 𝑃₀") — direct test of the Tier-0.5 symbol-whitelist checker.
- **A sanctioned approximation with a stated regime** (B.5: assume \|𝑧′(𝑥)\| ≪ 1, expand cos 𝜃 to second order) — tests approximation-aware CAS equivalence and §7's retained-order correctness.
- **A bare dimensionless answer** (B.4: "determine the exponent 𝑎") — this is the §5(a) escalation trigger and, per §6, the **highest residual risk in the entire spec**. Having it in the primary eval pair is unusually lucky.
- **A numeric-with-units answer** (A.1, given 𝑎 = 100 μm, 𝜌, 𝛾) — tests tolerance-interval and unit checking.
- **A differential equation solved under boundary conditions** (B.5) — tests plug-back / EOM residual.

**Run both directions.** The clean solution measures **false-reject rate** — a verifier that fails a genuine IPhO reference solution is unusable regardless of what else it catches. The faulty solution measures **false-accept rate**, which is the number DEFINITION.MD §8.2 actually asks for.

**Hold `IPhO_2021_S1.pdf` / `faulty/IPhO_2021_S1_FAULTY.pdf` back** as the second pair (problem: `IPhO_2021_Q1.pdf`). Do not tune prompts against it — once you have iterated on the 2023 pair, it is your only uncontaminated estimate of whether the tuning generalized. When you do score it, **exclude Part B**: it is seismic-ray propagation rather than mechanics (DEFINITION.MD §1), so treat Part-B results as out-of-distribution rather than as a signal about the core.

**What to record per run**, so the numbers in §4 stop being estimates:
- Ingestion retry count and token spend (settles the §1 open question)
- Which injected faults each tier caught, and at which tier — deterministic Tier-0, bulk judge, or escalated agent
- Escalation rate: how many of the ~12 sub-parts fired a trigger (this is the dominant cost driver per §5)
- Any fault caught by `terra` escalation vs. missed — this is the arm that settles the `sol` question in §0

### Then

1. **Ingestion experiment** on the pair above. Cheap; unblocks every number in §4.
2. **Build the mutation harness** — generalize from the hand-injected 2021/2023 faults to systematic injection across all six anchors: flip a sign, drop a factor of 2, delete a case branch, perturb a datum, change a datum in `P` without propagating to `S`. This is **eval infrastructure, not a verifier tier**: it costs nothing at inference time, and without it you cannot tell whether DEFINITION.MD's correctness conditions are right — which is the actual open question. Build it alongside S3, not after.
3. **Build S3** as the reference architecture.
4. **Measure S2 and S1 against the same fault set.** If S2 catches what S3 catches, ship S2 and redirect the savings into wider escalation on the sub-parts that genuinely need it.
5. **Then** revisit the deferred approaches: N-version independent re-solve (attacks provenance / right-answer-wrong-reasoning), numerical ground-truth simulation (adjudicates the dimensionless and geometric-factor answers that are the highest residual risk), and adversarial prover/refuter debate. Each is an *improvement to a measured system*, not a standalone candidate — and where each fits should be learned from the harness results, not asserted up front.

---

### Provenance

Drafted 2026-07-18. Pricing and model IDs verified against [OpenAI API pricing](https://developers.openai.com/api/docs/pricing) on that date; re-verify before relying on the cost model. Architecture derives from the layered definition and cost-optimized cascade in [DEFINITION.MD](DEFINITION.MD) §4–§5.
