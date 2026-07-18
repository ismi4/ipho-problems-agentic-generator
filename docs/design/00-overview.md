# IPhO-Style Problem Generator — Design Overview

**Goal:** an agentic system (LangChain/LangGraph) that generates novel, IPhO-grade
physics problems — with full solutions and marking schemes — for student prep.

**Status:** *exploration.* These docs map the design space and its complexities.
No architecture is chosen yet (see `06-open-questions.md`).

## What "IPhO-grade" actually demands

An acceptable output is not just a plausible physics prompt. It must be:

1. **Physically correct** — the stated setup obeys real physics.
2. **Solvable** — a well-defined, ideally closed-form (or clean numeric) answer exists.
3. **Uniquely determined** — enough givens, no ambiguity, no missing constraints.
4. **Well-arced** — multiple sub-parts of *rising* difficulty that build on each other.
5. **Calibrated** — hard but doable in the target time; discriminates strong students.
6. **Novel** — not a copy of an existing bank problem.
7. **Complete** — realistic numbers, figures where needed, official solution + rubric.

Requirements 1–3 are the ones LLMs fail silently. They drive the whole architecture.

## The one insight that shapes everything

An LLM **cannot self-certify** physical correctness or solvability. The load-bearing
component of any viable design is an **external ground-truth check** — symbolic math
(SymPy), numerical simulation, dimensional analysis — *not* another LLM asserting
"this looks right."

Corollary: prefer **backward design** (build from a known solution outward) over
**forward design** (write a statement, then hope it's solvable). See
`03-architecture-options.md`.

## Reading order

- `01-design-paradigms.md` — agentic vs. pipeline vs. template vs. RAG vs. hybrid.
- `02-human-process-and-ideation.md` — first-principles author loop + creative seeding.
- `03-architecture-options.md` — candidate architectures, each with a complexity budget.
- `04-key-challenges.md` — the hard sub-problems (verification, calibration, novelty…).
- `05-langgraph-mapping.md` — how these map onto LangGraph primitives.
- `06-open-questions.md` — decisions to make before committing to one design.
