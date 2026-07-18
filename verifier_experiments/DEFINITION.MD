# Definition of Correctness for IPhO-Mechanics Solution Verification

*A cost-optimized correctness specification for an automated verifier inside a physics-olympiad problem-set generation pipeline.*

Synthesized from three inputs:
- **(A) Empirical** — full read of the problem + solution PDFs of the 5 most-recent genuine IPhO mechanics theory problems.
- **(B) First-principles** — a domain-agnostic, structured definition of solution correctness.
- **(C) Adversarial debate** — general-physics vs IPhO-mechanics correctness, reconciled into a minimal, cost-optimal spec.

Source archive: https://ipho.olimpicos.net/ (PDFs at `IPhO_YYYY_Q{n}.pdf` / `IPhO_YYYY_S{n}.pdf`).

---

## 1. Empirical grounding — the 5 anchor problems

The 5 most-recent genuine mechanics theory problems. **2022 "Scaling Laws" was rejected** (special-relativity/estimation medley, not classical mechanics) and **2020 "Anisotropic Friction"** substituted in.

| # | Problem | Year | Q/S | Mechanics content |
|---|---------|------|-----|-------------------|
| 1 | Cox's Timepiece | 2025 | Q2/S2 | Hydrostatics + rigid-body/pulley + Coulomb friction + energy cycle |
| 2 | Black Widow Pulsar | 2024 | Q3/S3 | Orbital dynamics (effective potential, Lagrange points) + stellar hydrostatic stability |
| 3 | Water and Objects | 2023 | Q3/S3 | Capillary/surface-tension statics + energy conservation |
| 4 | Planetary Physics | 2021 | Q1/S1 | Hydrostatic equilibrium/buoyancy + seismic-ray (elastic-wave) propagation |
| 5 | Anisotropic Friction | 2020 | Q2/S2 | Direction-dependent friction, EOMs, radius of curvature, rigid rod |

### Seven empirical facts that drove the definition

1. **Answers are dominantly symbolic closed-forms** → correctness = algebraic equivalence, *never* string-match, judged **up to the problem's sanctioned approximation** (e.g. leading-order in a small parameter).
2. **Numerics are graded against explicit tolerance intervals with mandatory units.** The 2025 marking scheme withholds the point if the unit is missing (e.g. `F_max ∈ [14.6, 15] N`).
3. **Marking is step-decomposed partial credit**, split across *physical-law steps* (write the conservation law, use the right force law, obtain the key intermediate, final expression, numeric value).
4. **Error-carried-forward (ECF) is designed in.** 2021 explicitly says: if you couldn't find C and D, use `x₁ = C·cot θ₀` as given. Sub-parts are graded against the solver's *own* prior results.
5. **Cheap checks recur everywhere and are unusually powerful in mechanics**: dimensional analysis (sometimes *is* the whole answer — 2021 A.5, 2024 B-3), limiting cases, plug-back into the EOM, cross-method agreement.
6. **Some items are irreducibly expensive/semantic**: sketches, qualitative plots (shape/asymptote/monotonicity), piecewise-graph geometry, regime classification.
7. **Mechanics-specific failure modes dominate**: sign/**direction** errors, regime/threshold misclassification, dropping the wrong term in an approximation, conservation-constraint violations, wrong integration constants from boundary conditions, and geometric/combinatorial factors that don't change dimensions but change the number.

---

## 2. The central reconciliation

### Two gates, not one

| Gate | Purpose | Output type | Basis |
|------|---------|-------------|-------|
| **Acceptance gate** | keep vs. regenerate | near-boolean | cheap answer-equivalence **+ cheap method-consistency proxy** (plug-back + conservation) |
| **Scoring signal** | reward / ranking | graded | step-decomposed partial credit with ECF |

The acceptance gate must include a cheap *method-consistency proxy* because the anchor problems are public and an LLM can emit a memorized right answer with fabricated work. A pure answer-match gate rubber-stamps that; plug-back of the solver's own intermediates catches most of it without an expensive judge.

### The cost breakthrough

**In mechanics, "physical-law consistency" — the axis a general spec treats as expensive-semantic — collapses to cheap mechanical checks** (a conservation-law residual + an EOM plug-back residual). This is specific to mechanics' structural gifts:

- explicit **equations of motion** to plug back into,
- **conserved quantities** as free orthogonal constraints,
- a tight **[M, L, T] dimensional space** where dimensional analysis is highly discriminating,
- canonical **limiting cases**.

General physics (e.g. quantum many-body) does not hand you these, which is why a general verifier cannot skip expensive method-verification but a **mechanics** verifier can — by default.

---

## 3. Final operational definition

> A candidate IPhO-mechanics solution is **correct** when its answer — a symbolic closed-form in the named variables, or a numeric value with correct units inside the sanctioned tolerance — is **algebraically equivalent to the reference answer up to the problem's authorized approximation**, carries **correct dimensions and (for vectors) correct direction/sign**, invokes the **correct governing law**, and **survives the cheap mechanical certifier stack**: dimensional analysis, limiting cases, plug-back into its own equations of motion, and conservation-quantity residuals, with cross-method agreement where available. Such a candidate is **accepted without expensive semantic method-verification**, because in mechanics the conjunction of those cheap checks leaves near-zero room for surviving error — **with two carved-out exceptions that force an expensive semantic re-derivation: (i) dimensionless or bare geometric/combinatorial factors, where dimensional analysis is blind, and (ii) qualitative deliverables — sketches, plots, piecewise-graph geometry, regime classifications — which have no algebraic form to check.** Scoring, as distinct from acceptance, is **step-decomposed partial credit with error-carried-forward**: each sub-part is graded against the solver's own prior results, and discrete classifications are all-or-nothing.

---

## 4. The common core (irreducible correctness axes)

A solution is a candidate for "correct" only if all of:

1. **Answer-form match** — symbolic closed-form in named variables (numeric-substitution equivalence, not string-match) OR numeric-in-tolerance.
2. **Sanctioned-approximation equivalence** — equivalence judged *up to* the problem's authorized leading-order/small-parameter truncation, not exact.
3. **Dimensional consistency** — every expression dimensionally sound; final answer has correct dimensions.
4. **Units present and correct** (numeric answers) — point-bearing; missing unit = lost point.
5. **Sign/direction correct** — vector quantities carry explicit, correct direction.
6. **Governing-law correctness** — the correct conservation law / force law / EOM is invoked.
7. **Completeness against the (delimited) ask** — all requested sub-parts answered.

---

## 5. Cost-optimized verifier cascade

Legend: **[C]** cheap-mechanical · **[E]** expensive-semantic · **(F)** falsifier (can only reject) · **(±C)** partial certifier.

### Tier 0 — cheap falsifiers, run on every candidate, fail-fast
- 0.1 **[C](F)** Dimensional consistency of final answer and key intermediates.
- 0.2 **[C](F)** Units present + correct on all numeric answers (missing unit = auto-deduction).
- 0.3 **[C](F)** Sign/direction correct on all vector quantities.
- 0.4 **[C](F)** Numeric answer within explicit tolerance interval.
- 0.5 **[C](±C)** Symbolic equivalence to reference form **up to sanctioned approximation** (numeric-substitution test).

### Tier 1 — cheap near-certifiers, run when Tier 0 passes
- 1.1 **[C](±C)** Limiting-case checks (small-parameter, heavy/light-mass, frictionless, etc.).
- 1.2 **[C](±C)** Plug-back / EOM-residual using the solver's own governing equations (≈ 0).
- 1.3 **[C](±C)** Conservation residuals (energy / momentum / angular-momentum / mass / volume).
- 1.4 **[C](±C)** Cross-method agreement, when a second method is available.
- 1.5 **[C](F)** Correct governing law *identified*.

**Acceptance rule:** Tier 0 all-pass **AND** ≥ 2 independent Tier-1 checks pass (one must be plug-back or conservation) ⇒ **ACCEPT** without Tier 2, unless an escalation trigger fires.

### Tier 2 — expensive semantic, ESCALATION-ONLY (never default)
Trigger if ANY:
- (a) answer is **dimensionless / a pure number / a bare geometric factor** (dimensional analysis blind);
- (b) plug-back is **circular** (answer defined as the plugged quantity) and no second method exists;
- (c) Tier-0/1 checks **disagree**;
- (d) deliverable is **qualitative** (sketch/plot/piecewise geometry) or a **regime classification**.

Then run:
- 2.1 **[E](F/±C)** Step-logic re-derivation / independent recomputation to localize compensating errors.
- 2.2 **[E]** Qualitative-item grading: shape, asymptotes, monotonicity, break-points, slopes.
- 2.3 **[E]** Regime/threshold classification correctness (all-or-nothing).
- 2.4 **[E]** Approximation-application legitimacy (dropped the *right* term).

### Scoring (parallel to gating, for reward signal)
ECF step-decomposed partial credit — allocate points across {correct law written, correct force/EOM used, key intermediate, final expression, numeric value + unit}; grade each sub-part against the solver's own upstream results; discrete items all-or-nothing.

---

## 6. What was dropped/made optional, and the risk

| Dropped/optional | Rationale | Risk | Mitigation |
|---|---|---|---|
| Full Tier-2 model-adequacy verification | Model is given by the problem, not selected | Low | Cheap "used stated model" lexical check |
| Semantic step-logic re-derivation on every candidate | Redundant when EOM-residual + conservation + second method pin it | Medium (memorized-answer-fake-work if plug-back circular) | Trigger Tier-2 only on the exception set |
| Completeness as graph-reachability | Collapses to a checklist of requested sub-parts | Low | Checklist |
| General compensating-error scan | Mostly covered by second method + conservation | **Highest residual risk: dimensionless/geometric factors** | Force Tier-2 escalation on dimensionless answers |
| Approximation-*validity* judgment | Problem sanctions it; verifier checks only correct *application* | Low in-distribution | N/A |

### Added specifically for mechanics
- Direction/sign check as a first-class falsifier (mechanics' #1 recurring failure mode).
- Conservation residual checks as cheap independent constraints.
- EOM-residual / plug-back using the solver's own equations.
- Sanctioned-approximation-aware symbolic equivalence (leading-order-in-ε, not exact).
- ECF scoring against the solver's own intermediates.
- All-or-nothing handling for discrete items (regime classification, paired slope signs).
- Qualitative-item semantic check (the one irreducibly expensive addition).

---

## 7. Open decisions (next steps)

1. **Verdict shape** — emit a structured multi-axis verdict (per-axis pass/fail + first-point-of-failure) vs. a scalar. Structured is favored for a training/reward signal.
2. **Validation** — run the Tier 0/1 stack against the 5 anchor solutions as a labeled test set to measure how often cheap checks alone suffice (expected: majority of sub-parts).
3. **Schema** — draft the verifier's structured-verdict output schema.
