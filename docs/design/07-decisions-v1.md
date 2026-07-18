# v1 Decisions (locked)

Decided 2026-07-12. These constrain the architecture; revisit only with cause.

## D1 — Correctness bar: **Tiered**
- Problems that pass the deterministic verifier gate → **auto-ship**.
- Everything else → **human-review queue** (not discarded).
- Implication: build both the machine gate *and* a lightweight review queue/UI.
  Yield doesn't have to be high early — failures become review candidates, not waste.

## D2 — Domains for v1: **E&M + Circuits**
- Electrostatics, magnetostatics, induction, DC/AC & RLC circuits.
- Rationale: clean models, strong SymPy fit (linear ODEs, phasors, network equations),
  good backward-construction properties → aligns with Option D core.
- Out of scope for v1: mechanics, thermo, optics, modern. Add after the core is proven.

## D3 — Verifier: **Agentic solver + authoritative tools + deterministic gate**

The verifier is *not* an LLM opinion. Structure:

1. **Agentic solver** (LLM loop) sets up the physics and orchestrates tools:
   - `symbolic_solve` — SymPy: solve governing equations, simplify, check the candidate
     answer satisfies them.
   - `dimensional_check` — every quantity carries units; assert consistency.
   - `numeric_crosscheck` — evaluate symbolic result at sampled parameter values and
     compare against a direct numeric solve / simulation; assert residual < tol.
   It emits a **machine-checkable trace** (actual expressions, residuals, unit ledger).
2. **Deterministic verifier** (plain code, no LLM) re-runs the trace and returns a
   boolean. **This boolean is the ground truth** that gates auto-ship vs. queue.
3. **The LLM's prose is never authoritative** — only re-verified tool outputs are.

Optional (post-v1): an **independent re-solve** agent that solves the statement from
scratch and must match, to catch under/over-specification. Deferred to keep v1 lean.

## Consequences for architecture
- Start from **Option D** (backward construction + verifier core) restricted to E&M.
- The `verifier` and `resolver` nodes in `05-langgraph-mapping.md` merge into the
  agentic-solver-plus-deterministic-gate described above.
- The tiered bar means the LangGraph terminal edge routes on the gate boolean:
  `pass → auto-ship store`, `fail → review queue`.

## D4 — Prompt/eval infra: **Adopt Langfuse (self-hosted)**
- Langfuse owns: prompt versioning + labels, run tracing, **gold-set Datasets**, eval
  scores. Nodes resolve prompts by key + label from Langfuse at runtime; resolved
  version ids land in the trace (provenance).
- Supabase owns only **domain/app data**: generated problems, human-review queue,
  physics corpus. (The prompt_versions/labels/eval_runs tables in `08` are dropped —
  Langfuse provides them.)
- Consequence: the "thin Supabase registry" option in `08` is superseded; build against
  Langfuse's prompt + datasets API instead.

## D5 — Prompt synthesis: **Build early, but gold-set-first**
- Synthesis is a first-class subsystem from the start — BUT the scoring loop must exist
  before the optimizer. Mandatory build order:
  1. Hand-write v1 evaluator prompts.
  2. Create a small Langfuse gold **Dataset** per evaluator (human-labeled).
  3. Wire the **scorer** (run prompt vs. dataset → metrics).
  4. Only then add the automated **drafter/optimizer** on top of that harness.
- Guardrail: never run the optimizer against a missing/unstable gold set — that
  optimizes against a moving target (the premature-optimization trap).

## Next build step
Tools first: implement `symbolic_solve`, `dimensional_check`, `numeric_crosscheck` as
LangChain tools + the deterministic gate that consumes their trace. Prove them on 2–3
hand-written E&M problems before wiring the generator.
