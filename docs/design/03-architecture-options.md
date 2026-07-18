# Candidate Architectures (with complexity budgets)

Each option lists its flow, complexity, and the failure mode it trades against.
Rated 🟢 low / 🟡 medium / 🔴 high complexity.

---

## Option A — Single agent, tool-augmented (🟢)

One ReAct-style agent with SymPy + web tools; generates, self-checks in a loop.

- **Pros:** simplest; fast to build; good baseline.
- **Cons:** self-verification is weak (same model judges its own physics); limited
  novelty; hard to enforce the rising-difficulty arc.
- **Use as:** the v0 baseline to measure everything else against.

---

## Option B — Fixed pipeline / DAG (🟡)

Seed → Model → Draft statement → Solve → Verify → Format. No cycles.

- **Pros:** predictable, testable, cheap, easy to reason about.
- **Cons:** no repair loop — a failed verification just drops the problem (low yield);
  rigid; can't adapt difficulty.
- **Use when:** you want throughput and can tolerate discarding many candidates.

---

## Option C — Multi-agent committee, forward design (🔴)

Proposer → Solver → Reviewer → Calibrator → Critic, with a repair loop back to Proposer
on failure. Statement is written first; solution discovered after.

- **Pros:** mirrors real committees; strong QC; high novelty.
- **Cons:** correctness is *discovered*, not *guaranteed* → many expensive repair loops;
  agents can collude on wrong physics; highest cost/latency.
- **Risk:** the verifier is the single point of truth; if it's an LLM, the whole thing
  is unsound.

---

## Option D — Backward construction + verifier core (🟡–🔴)  ← current lean

Build from a **known solution outward**:

1. **Seed** (strategy interface, see `02`).
2. **Model builder** picks a physical model + parameters with a *constructed* solution
   (symbolic where possible).
3. **Verifier core** (SymPy + numeric sim + dimensional analysis) confirms the solution
   is self-consistent *before* any prose is written.
4. **Statement composer** obfuscates the solution into a problem (choose givens/unknowns,
   design the sub-part arc).
5. **Independent solver agent** re-solves the *statement from scratch* and must reach the
   same verified answer — catches under-/over-specification.
6. **Calibrator + Critic + Novelty check + Figure/rubric generation.**

- **Pros:** correctness is *cheap and structural* (you never guess solvability); still
  novel because seeding is diverse; the independent re-solve is a strong guarantee.
- **Cons:** the model builder is the hard engineering piece; not every physics area
  admits clean backward construction (some need forward + verify, i.e. a hybrid).

---

## Option E — Hybrid, per-domain routing (🔴)

Router picks Option D (backward) for domains with clean models (mechanics, circuits,
optics) and Option C (forward + heavy verify) for messier domains. Templates as a
safety net for guaranteed-valid fallback output.

- **Pros:** best correctness/novelty envelope; graceful degradation.
- **Cons:** most moving parts; only justified once A/D are proven.

---

## Complexity ledger (what each option costs you)

| Concern | A | B | C | D | E |
|---|---|---|---|---|---|
| # LLM roles | 1 | ~3 | 5+ | 5–7 | 7+ |
| Repair loops | 1 | 0 | many | few | few |
| Verifier soundness | weak | medium | **critical risk** | strong | strong |
| Novelty | low | medium | high | high | high |
| Build effort | 🟢 | 🟢 | 🔴 | 🟡 | 🔴 |
| Yield (kept/generated) | low | low | medium | **high** | high |

**Recommendation to evaluate (not yet commit):** ship **A** as a baseline, then build
**D**; consider **E** only if a real domain-coverage gap appears.
