# Open Questions — decide before committing to one architecture

Grouped by how much they change the design. Answer the 🔴 ones first.

> **Resolved (see `07-decisions-v1.md`):** domains = E&M + Circuits; correctness bar =
> tiered (auto-ship verified / queue the rest); verifier = agentic solver + authoritative
> tools + deterministic gate. Remaining open items below.

## 🔴 Scope & correctness bar — *mostly resolved*
- ~~Physics domains~~ → **E&M + Circuits** (D2).
- ~~Correctness bar~~ → **Tiered** (D1).
- **Answer types (still open):** closed-form only, or also numeric/estimation/qualitative?
  Estimation problems need a different verification strategy. *Lean: closed-form + numeric
  for v1, defer estimation.*

## 🔴 Verification strategy — *resolved (D3)*
- Approach fixed: agentic solver + `symbolic_solve`/`dimensional_check`/`numeric_crosscheck`
  + deterministic gate. Independent re-solve **deferred** to post-v1.
- **Still open:** numeric residual **tolerance** value; how to handle E&M problems that
  only admit approximations/limits (rare in v1 scope, but flag them to the queue).

## 🟡 Novelty & corpus
- Do we have (or can we license/assemble) a **corpus** of past problems for the
  novelty check? Without it, anti-plagiarism is guesswork.

## 🟡 Difficulty calibration
- Trust **student-simulator agents**, or require **human calibration** on a sample?
- What's the target: pure IPhO level, or a difficulty *dial* for prep at many levels?

## 🟡 Human-in-the-loop
- Fully autonomous, or expert-approves at checkpoints (seed / final)? Changes the
  LangGraph interrupt design and the throughput target.

## 🟢 Output & delivery
- Output format: LaTeX / PDF / web? Figures required or optional for v1?
- Volume goal: a few gems per day, or a large bank? (Affects cost tolerance.)

## 🟢 Model & cost
- Which model tier per node (cheap for seeds, strong for modeling/verification)?
- Budget ceiling per accepted problem?

## Proposed first decision
Pick **domains + correctness bar + verification strategy** (the 🔴 block). Those three
alone determine whether we start with Option A→D (backward core) or need E (hybrid).
