# Definition of Correctness for IPhO-Mechanics Solution Verification

*A cost-optimized specification of what it means for a **reference solution to be correct**, for an automated verifier inside a physics-olympiad problem-set generation pipeline.*

> **Scope note.** This defines correctness of the **reference solution itself** — i.e. given a generated problem statement `P` and a generated reference solution `S`, what would it mean to *assert `S` is correct*. This is **not** grading a student answer against a key. The "official answer," where one exists, is a **consistency oracle, not ground truth** — the physics is the authority.

Synthesized from three inputs (2026-07-19 run):
- **(A) Empirical** — full read of problem + solution PDFs of the recent genuine IPhO mechanics theory problems.
- **(B) First-principles** — a domain-agnostic, structured definition of solution correctness (no problems seen).
- **(C) Adversarial debate** — general-physics ("Class G") vs IPhO-mechanics ("Class M") correctness, reconciled into a minimal, cost-optimal spec.

Source archive: https://ipho.olimpicos.net/ (PDFs at `IPhO_YYYY_Q{n}.pdf` / `IPhO_YYYY_S{n}.pdf`).

---

## 0. The object being verified

`S`'s correctness is **conditional on `P`** — a solution is never correct in isolation, only *as a solution to a particular problem*. So the target is a **relation** between `P` and `S` plus intrinsic properties of each, decomposing into three logically distinct verdicts that must not be conflated:

| Verdict | Question | Output on failure |
|---|---|---|
| **V_P — Well-posedness of `P`** | Does a correct solution exist at all, and is the target well-defined? | **"ILL-POSED"** — fix `P`, not `S` (correctness of `S` is *undefined*) |
| **V_S — Intrinsic soundness of `S`** | Is the reasoning inside `S` physically & mathematically valid? | "UNSOUND" |
| **V_{P→S} — Faithfulness** | Does `S` solve the problem `P` actually poses (same system, data, all parts)? | "UNFAITHFUL" |

> **The generated-content headline.** For a *generation pipeline*, the dominant failure mode is **V_{P→S}**: `S` is internally beautiful but solves a *slightly different* problem than the one rendered (a number changed in `P` but not propagated to `S`, a dropped boundary condition, a figure contradicting the prose). No amount of intrinsic checking of `S` reveals this. **Faithfulness gets no discount from mechanics structure and must be established independently.**

---

## 1. Empirical grounding — the anchor problems

The recent genuine mechanics theory problems, pulled and read in full. **2022 "Scaling Laws"** partly leaks into special relativity and **2021 "Planetary Physics" Part B** is seismic-ray/wave propagation; **2020 "Anisotropic Friction"** is the purest classical-mechanics anchor and is retained as a fifth.

| # | Problem | Year | Q/S | Mechanics content |
|---|---------|------|-----|-------------------|
| 1 | Cox's Timepiece | 2025 | Q2/S2 | Hydrostatics + buoyancy + rigid-body/pulley + Coulomb (dry) friction + PV energy cycle |
| 2 | Black Widow Pulsar | 2024 | Q3/S3 | Orbital dynamics (effective potential, Lagrange points, orbital decay, bound/unbound) + stellar hydrostatic stability (SHM) |
| 3 | Water and Objects | 2023 | Q3/S3 | Energy-conservation drop + capillary/surface-tension statics + floating-body force balance |
| 4 | Scaling Laws | 2022 | Q3/S3 | Beam statics + capillary statics + damped-oscillator hydrodynamics (Part C is SR — flagged) |
| 5 | Planetary Physics | 2021 | Q1/S1 | Hydrostatic equilibrium/isostasy (Part B is seismic-ray propagation — flagged) |
| — | Anisotropic Friction | 2020 | Q2/S2 | *(purest anchor)* direction-dependent friction, EOMs, radius of curvature, rigid-rod rotation, stick/slip thresholds |

### Empirical facts that drove the definition
1. **Answers are dominantly symbolic closed-forms** → correctness = **algebraic equivalence** (CAS), never string-match, judged **up to the problem's sanctioned approximation** (e.g. leading-order in a small parameter), and **only in the mandated symbol set** (2025 A.1 restricts to `P₀,ρ,m,S,h,g`).
2. **Numerics graded against explicit tolerance intervals with mandatory units** (2025 `F_max ∈ [14.6, 15] N`; units are load-bearing — 2022: "units must be shown to get points"; ≥2 s.f. common).
3. **A right number obtained from a wrong formula earns nothing** (2022 general rule). For a *reference* solution, **right-answer-wrong-reasoning counts as INCORRECT** — the value must arise *because of* the reasoning.
4. **Answer types cluster into ~6 pre-declarable forms**: symbolic-closed-form / numeric+units+tolerance / threshold-inequality+direction / graph-as-feature-list / scaling-exponent+mechanism / "show-that"-derive-to-given-form.
5. **Cheap checks are unusually powerful in mechanics**: dimensional analysis (sometimes *is* the whole answer — 2021 A.5, 2024 B-3), limiting cases, plug-back into the EOM, symmetry, and **independent conservation-law re-derivation**.
6. **Some items are irreducibly semantic/expensive**: sketches & qualitative plots (shape/asymptote/monotonicity/break-points), piecewise-graph geometry, regime classification.
7. **Mechanics-specific failure modes dominate**: sign/**direction** errors, **regime/contact-condition case-splits** (stick/slip, static/kinetic, bound/unbound, cavitation/lift-off), **wrong root branch**, dropping the wrong term in an approximation, frame/coordinate errors (rotating-frame centrifugal term), conservation-constraint violations, wrong integration constants from BCs, and **geometric/combinatorial factors that don't change dimensions but change the number**.

---

## 2. The five correctness conditions (invariant definition)

`S` is **correct for `P`** iff, for every sub-part:

- **(I) Well-posedness of `P`** *(precondition)* — data + standard canon are mutually consistent (across prose/figure/numbers), physically admissible under stated idealizations, dimensionally coherent, notationally/frame-unambiguous, and **determine** each requested quantity uniquely on the intended branch (or explicitly enumerate cases). *If (I) fails → emit **ILL-POSED**; correctness of `S` is undefined.*
- **(II) Physical soundness** — correct governing laws for the system, applied within valid regime, with legitimate self-consistent approximations, violating no conservation law or symmetry the setup obeys.
- **(III) Derivational validity** — a gap-free chain of individually valid inferences from givens to each answer; dimensional homogeneity throughout; correct numerics/constants/units/precision. No step justified only by asserting the target.
- **(IV) Faithfulness `P→S`** — `S` addresses the *same* system, data, geometry, boundary/initial conditions, and quantities `P` actually specifies. **(Dominant generated-content failure mode.)**
- **(V) Completeness** — every part answered; every non-excluded case resolved and correctly bounded; each quantity delivered in the *demanded form* with units.

Plus **(VI) Certification-consistency** — a *derived* property, not an independent requirement: a correct `S` necessarily passes the self-consistency battery (dimensions, limiting cases, symmetry, order-of-magnitude, conservation) and equals the physics-forced value. This makes (VI) usable as a **cheap, high-precision test** of the conjunction (I)–(V).

**Necessity/sufficiency:** (I) makes correctness *definable*; (II)–(V) are each independently necessary (dropping any admits a distinct wrong solution — unphysical-but-valid / valid-but-unfaithful / sound-but-incomplete / right-number-wrong-reasoning). (I)∧(II)∧(III)∧(IV)∧(V) are jointly sufficient.

---

## 3. The central reconciliation — mechanics is a *cost migration*, not a *definition reduction*

Going from general physics (Class G) to IPhO mechanics (Class M), **no condition is deleted.** Several migrate from expensive-expert to cheap-mechanizable; a hard core stays expensive. Every cheap check is **conditional on a correct frame/constraint model and a faithful read of `P`** — the two things that never cheapen.

| Class-G condition | Class-M treatment | Why |
|---|---|---|
| **(I) Well-posedness — determinacy core** (§1.1–1.2,1.5) | **Cheapen** → dimensional-determinacy + DOF-vs-constraint counting + conservation-budget (falsifiers, *necessary not sufficient*) | Finite-DOF ⇒ determinacy is an integer count |
| **(I) Well-posedness — modality consistency, frame/semantic unambiguity** (§1.3,1.6) | **Unchanged (expert)** | Figure↔prose contradiction & frame ambiguity are live mechanics failures |
| **(II) Soundness — conservation/symmetry slice** | **Cheapen** → conservation oracle (partial *certifier* for the constrained projection) | Cheap **independent** re-derivation is a distinctive finite-DOF affordance |
| **(II) Soundness — law-choice, regime validity, law-applicability** | **Unchanged (expert)** | Deciding *which* law applies / whether regime holds is judgment |
| **(III) Derivational validity** | **Largely cheapen** → per-step dimensional homogeneity + CAS symbolic-equivalence + numeric-vs-tolerance | Mechanics steps are algebraic/CAS-tractable; empirically decisive |
| **(IV) Faithfulness `P→S`** | **Unchanged (expert)** — the dominant generated-content risk | Semantic `P↔S` relation; mechanics gives zero leverage |
| **(V) Completeness — parts & demanded form** | **Cheapen** form/value via pre-compiled per-type checkers; "answered-in-substance" unchanged | ~6 declarable answer types |
| **(V) Completeness — case-completeness** | **Cheapen** → structured case-menu checklist over enumerated contacts/constraints/roots/regimes; **residue unchanged** for non-menu bifurcations | Finite enumerable case taxonomy |

**Irreducible core (expert cost in every domain, incl. mechanics):** faithfulness `P→S`; frame/constraint/free-body semantic validity; law-choice & approximation-regime legitimacy; non-menu case-completeness + constraint-inventory completeness; novel-path validation; **provenance** (right value *because of* the reasoning).

---

## 4. Recommended layered definition (drives the verifier)

Layers are **ordered**: the expert gate is a precondition for trusting the cheap core.

### Layer 0 — Expert GATE (small, structured, runs first; load-bearing)
- Faithful extraction of each sub-part's **demand** (system, data, geometry, BCs, requested quantity + demanded answer type) — this is **faithfulness (IV)** and answer-type selection.
- Correct **free-body / constraint / frame** model; declaration of intended regime & idealizations — **(II) upstream**.
- *If Layer 0 is wrong, all Layer-1 results are void.*

### Layer 1 — Cheap operational core (mechanizable; exploits mechanics structure)
1. **Well-posedness screen** — dimensional determinacy + DOF-vs-constraint count + conservation budget (falsify under/over-determination).
2. **Derivational validity** — per-step dimensional homogeneity; CAS symbolic-equivalence of final + key intermediates (**up to sanctioned approximation**, via numeric-substitution); numeric recompute within tolerance/units/sig-figs.
3. **Conservation oracle** — independent re-derivation of the target via energy/work, linear & angular momentum, incompressible volume-mass; require **symbolic** (not just point-numeric) agreement across *all applicable independent* laws. Falsifier first; multi-law agreement is a soundness-confidence booster.
4. **Consistency battery** — limiting/special cases, symmetry, sign/direction, order-of-magnitude, cross-part chaining (downstream uses the *actual* upstream result).
5. **Answer-form check (per-type, pre-compiled)** — symbolic-equiv + **symbol-whitelist** / numeric-tolerance+units+sigfigs / threshold inequality+**direction**+side / graph **enumerated-feature list** / scaling exponent+mechanism / show-that **term-by-term** match of mandated intermediates.
6. **Case-menu checklist** — for every enumerated contact/constraint/root-branch/regime-boundary, verify `S` resolves the branch or justifies excluding it.

### Layer 2 — Expert residue (expensive; only where Layer 1 is silent or Layer 0 flags risk)
- Faithfulness confirmation + "answered-in-substance" per part.
- Frame/constraint/**law-applicability** soundness (incl.: *is each invoked conservation law actually valid here?*).
- Approximation-regime legitimacy & retained-order correctness.
- Residual case-completeness: non-menu bifurcations, constraint-inventory completeness.
- Novel/alternative-path validation.
- **Provenance** adjudication; resolve any answer-vs-derivation conflict.

**Verdict** = Layer-0 gate ∧ Layer-1 core ∧ Layer-2 residue pass, per sub-part, **path-independently** (non-uniqueness tolerance — multiple valid methods accepted). Well-posedness failure ⇒ distinct **ILL-POSED** output.

---

## 5. Cost-optimized verifier cascade

Legend: **[C]** cheap-mechanical · **[E]** expensive-semantic · **(F)** falsifier (can only reject) · **(±C)** partial certifier.

> **Doctrine:** cheap checks **refute** with high precision but low recall; only expensive reasoning **confirms**. Never let the cheap layer *certify* on its own.

### Tier 0 — cheap falsifiers, run on every candidate, fail-fast
- 0.1 **[C](F)** Dimensional consistency of final answer + key intermediates.
- 0.2 **[C](F)** Units present + correct on all numerics (missing unit = fail).
- 0.3 **[C](F)** Sign/direction correct on all vector quantities.
- 0.4 **[C](F)** Numeric within explicit tolerance interval.
- 0.5 **[C](±C)** Symbolic equivalence to reference form **up to sanctioned approximation** + **symbol-whitelist** respected.

### Tier 1 — cheap near-certifiers, run when Tier 0 passes
- 1.1 **[C](±C)** Limiting-case checks (small-parameter, heavy/light mass, frictionless…).
- 1.2 **[C](±C)** Plug-back / EOM-residual using the solver's own governing equations (≈ 0).
- 1.3 **[C](±C)** Conservation residuals (energy / momentum / angular-momentum / mass / volume) — **symbolic across the form**, and **only after checking the law is applicable**.
- 1.4 **[C](±C)** Cross-method agreement when a second method exists.
- 1.5 **[C](F)** Correct governing law *identified*.

**Acceptance rule (intrinsic):** Tier 0 all-pass **AND** ≥2 independent Tier-1 checks pass (one must be plug-back or conservation) ⇒ intrinsically sound, unless an escalation trigger fires. **Acceptance still requires Layer-0 faithfulness/model gate to have passed** — intrinsic soundness ≠ correctness.

### Tier 2 — expensive semantic, ESCALATION-ONLY (never default)
Trigger if ANY: (a) answer is **dimensionless / bare number / geometric factor** (dim-analysis blind); (b) plug-back is **circular** and no second method exists; (c) Tier-0/1 checks **disagree**; (d) deliverable is **qualitative** (sketch/plot/piecewise geometry) or a **regime classification**; (e) Layer-0 flagged faithfulness/frame/constraint risk; (f) a **case-menu** boundary could change sign over the domain but `S` didn't split there.

Then run: 2.1 step-logic re-derivation to localize compensating errors · 2.2 qualitative-item grading (shape/asymptotes/monotonicity/break-points/slopes) · 2.3 regime/threshold classification (all-or-nothing) · 2.4 approximation-application legitimacy · 2.5 **faithfulness deep-check** (P↔S datum/BC/figure reconciliation) · 2.6 **conservation-law applicability** audit.

---

## 6. What is dropped/made optional — and the residual risk

| Dropped/optional | Rationale | Risk | Mitigation |
|---|---|---|---|
| Full model-adequacy verification | Model is given by `P`, not selected | Low | Cheap "used stated model" check (Layer 0) |
| Semantic step-logic on every candidate | Redundant when EOM-residual + conservation + 2nd method pin it | Medium (memorized-answer/fake-work if plug-back circular) | Tier-2 trigger on the exception set |
| Completeness as graph-reachability | Collapses to a checklist of requested sub-parts | Low | Checklist |
| General compensating-error scan | Mostly covered by 2nd method + conservation | **Highest residual: dimensionless/geometric factors** | Force Tier-2 on dimensionless answers |
| Approximation-*validity* judgment | `P` sanctions it; verifier checks correct *application* only | Low in-distribution | N/A |

### Added specifically for this setting
- **Faithfulness `P→S` as a first-class, non-discountable verdict** (the #1 generated-content failure) — Layer 0 + Tier 2.5.
- **Well-posedness as a separate ILL-POSED output** — never silently reported as "S wrong."
- **Right-answer-wrong-reasoning ⇒ incorrect** (provenance is Layer 2, never certified by endpoint checks).
- Direction/sign as a first-class falsifier (mechanics' #1 intrinsic failure mode).
- Conservation residuals as cheap independent constraints — **falsifier-first, partial-certifier only symbolically & only when applicable**.
- EOM-residual / plug-back using the solver's own equations.
- Sanctioned-approximation-aware symbolic equivalence + symbol-whitelist.
- Structured **case-menu checklist** (stick/slip, static/kinetic, bound/unbound, cavitation, root-branch) converting expert bifurcation-hunting into a bounded check.
- Qualitative-item semantic check (the irreducibly expensive addition).

---

## 7. Explicit caveats — where the mechanics simplification is UNSAFE
1. **Right-number-wrong-reasoning survives the cheap core** (all endpoint checks). Never certify on Layer 1 alone.
2. **Conservation oracle as a false certifier** — if the law is silently inapplicable (open system, external impulse/torque, non-conservative contact, only-approximate incompressibility), a "pass" certifies nothing. Applicability is a Layer-2 precondition.
3. **Missed non-menu case** — the checklist has zero recall outside the standard taxonomy (parametric resonance, geometric degeneracy, post-state-change constraint activation). Checklist silence ≠ completeness.
4. **Corrupted constraint inventory poisons everything downstream** — a wrong Layer-0 model makes conservation, case-menu, and DOF count all "pass" while wrong. The gate is load-bearing.
5. **Unfaithful `S` passing all intrinsic checks** — an `S` that soundly solves a *different* problem than `P` passes soundness/derivation/conservation entirely. Faithfulness is orthogonal and receives **no** discount.
6. **Answer mis-typing silently drops requirements** — wrong per-type checker (e.g. "show-that" treated as free symbolic; missed symbol-whitelist) applies a weaker test than demanded.
7. **Point-numeric conservation agreement over-trusted** — single-input agreement can be coincidental; require symbolic-across-the-form before treating the oracle as a soundness booster.

---

## 8. Open decisions (next steps)
1. **Verdict shape** — structured multi-axis verdict (per-condition pass/fail + first-point-of-failure + separate ILL-POSED/UNFAITHFUL/UNSOUND channels) vs. scalar. Structured favored for a training/reward signal.
2. **Validation** — run the Layer-1 stack against the anchor solutions as a labeled set; measure the fraction of sub-parts cheap checks alone adjudicate (expected: majority) and the false-accept rate on injected faults (esp. faithfulness drifts & dimensionless-factor errors).
3. **Faithfulness harness** — design the `P→S` extraction+reconciliation check (datum/BC/figure/quantity matching) as its own module, since it carries the dominant risk and no cheap discount.
4. **Schema** — draft the verifier's structured-verdict output schema.

---

### Provenance
Combined 2026-07-19 from three parallel analyses (first-principles, empirical PDF read, adversarial Class-G-vs-Class-M debate). Anchor PDFs: `IPhO_{2025,2024,2023,2022,2021,2020}_{Q,S}{n}.pdf` from https://ipho.olimpicos.net/. Supersedes the prior `DEFINITION.MD`; principal additions over it are the faithfulness-first framing for generated content, the separate ILL-POSED verdict, the Layer-0 gate, and the explicit cost-migration table.
