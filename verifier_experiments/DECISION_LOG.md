# Decision Log

Chronological register of material decisions. Format: **decision** — alternatives rejected — one-line rationale.

## Scoping
1. **Scope the "AI execution system" to a solution verifier for IPhO-mechanics problems, and "inference cost" to OpenAI $/token per verification.** — (rej: verify a full generation pipeline; optimize a generic chatbot) — the verifier is the recurring cost surface of the generation pipeline described in `DEFINITION.MD`, and it is the workload where "equal quality" is falsifiable.
2. **Define "equal quality" as a non-inferiority gate on balanced accuracy of ACCEPT/REJECT vs a labeled set, plus a secondary scoring-fidelity MAE.** — (rej: eyeball a few examples; use only raw accuracy) — cost cuts are meaningless without a falsifiable quality gate; balanced accuracy handles the REJECT-heavy class balance.

## Dataset
3. **Build the gold set by injecting exactly one documented fault into a faithful transcription of each official solution.** — (rej: hand-label LLM outputs; scrape existing graded solutions) — ground truth is true *by construction* (known injected fault → REJECT + failing sub-part), giving trustworthy labels without human grading.
4. **Curate every fault with the deterministic checker; discard any fault that does not actually falsify against the reference; log discards.** — (rej: assume all injections are valid) — guards against ECF-masked or still-correct "faults" (0 discards this run; see `dataset/discards.log`).
5. **Reserve a ~20% dev split for threshold tuning, never used for reporting.** — (rej: tune on the full set) — avoids optimistic bias from tuning on reported data. (Threat: dev split here is all-REJECT; see `REPORT.md`.)
6. **Provide the verifier the reference answer key (rubric) but hide the gold label / injected fault.** — (rej: fully blind, no reference) — matches a real generation-pipeline verifier that has a reference/rubric; keeps the ACCEPT/REJECT label hidden so the task stays honest.

## Metric & measurement
7. **Measure cost from actual logged OpenAI usage (incl. cached + reasoning tokens) against a pinned `prices.json`.** — (rej: estimate from token counts) — reasoning tokens are billed as output and dominate cost; only real usage is defensible.
8. **Snapshot the process-wide spend tracker before/after each verify() call for exact per-call cost, and hard-abort at $8 (headroom under the $10 cap).** — (rej: no kill-switch; estimate afterwards) — a hard guardrail is required by the budget constraint.
9. **Per-problem 50% gate (not averaged): cost(V2,p) ≤ 0.5·cost(V0,p) for all 3 problems.** — (rej: average across problems) — averaging can hide a problem that fails; per-problem is stricter and more honest.

## Model ladder
10. **Pin the gpt-5 family: strong=`gpt-5`, mid=`gpt-5-mini`, nano=`gpt-5-nano`, with dated prices.** — (rej: newer gpt-5.x tiers) — gpt-5 family has stable, well-documented pricing and the full strong/mid/nano ladder the levers need; newer tiers add price volatility without changing the mechanism.

## The three levers (kept orthogonal for attribution)
11. **Solution A = model right-sizing/cascade (which model); B = deterministic offload (whether to call a model); C = context/decoding efficiency (how efficiently).** — (rej: three prompt-tweak variants) — orthogonal levers give clean attribution and compose into the bonus system.
12. **A.V2 = calibrated router: trust confident cheap REJECTs, but guard ACCEPTs on problems with dimensionless/qualitative sub-parts by escalating to strong.** — (rej: coarse per-problem "hard→strong" gate) — every problem here contains a hard sub-part, so the coarse gate would route everything to strong and save nothing; the accept-guard captures the real false-accept risk while keeping the savings on rejects.
13. **B escalates to the LLM only on genuinely qualitative deliverables (no algebraic form); machine-checkable sub-parts (incl. dimensionless numerics with a reference value) are resolved deterministically.** — (rej: force every dimensionless answer to the LLM) — with a reference numeric value, dimensionless factors *are* machine-checkable via tolerance; only plot/sketch/regime items truly lack an algebraic handle. Documented as a refinement of the DEFINITION.MD Tier-2 trigger.
14. **Solution C holds the model tier fixed (strong) across V0/V1/V2.** — (rej: let C also drop to mini) — C's lever is efficiency of calling the *same* model; changing tier would confound it with Solution A.

## Budget-driven execution
15. **N=2 reps for the three strong-model V0 baselines, N=3 for the cheaper configs.** — (rej: uniform N=3) — keeps total spend well under the $10 cap while preserving clean majority-vote quality on the cheap configs; per-instance costs are rep-averaged so the 50% gate is unaffected. Documented as a threat to validity.
