# Design Paradigms — Agentic vs. Alternatives

The real design axis is **forward vs. backward generation**, which determines how much
agency you need. Below, paradigms are rated on the four properties that trade off.

## Comparison

| Paradigm | Correctness | Novelty | Cost/Latency | Debuggability |
|---|---|---|---|---|
| Single-shot prompt | low | medium | cheap | easy |
| Fixed pipeline (DAG, no loops) | medium | medium | moderate | easy |
| **Agentic (loops + tools + multi-agent)** | **high\*** | **high** | expensive | hard |
| Template + parameter sampling | very high | low | cheap | easy |
| RAG over existing banks | medium | derivative | moderate | medium |
| Fine-tuned model | medium | medium | high upfront | hard |

\* *only if the loop closes on a real external verifier (SymPy/sim), not an LLM judge.*

## Where agentic genuinely earns its cost

1. **Generate → solve → verify → repair** loop. Physics correctness is iterative; you
   cannot get it in one shot. This is the core justification.
2. **Tool use** — SymPy (symbolic solve, dimensional analysis), numerical simulation,
   web/arXiv/YouTube retrieval for ideation, figure rendering (TikZ/matplotlib).
3. **Committee-style role decomposition** — Proposer, Solver, Reviewer, Difficulty
   Calibrator, Aesthetic Critic. Mirrors how real olympiad problems are vetted.
4. **Open-ended ideation** — "go find interesting physics" is a genuinely agentic task.

## Where agentic is a liability

- **Error compounding / rationalization** — agents can talk themselves into wrong
  physics. Mitigation: the verifier must be external and non-negotiable.
- **Cost & latency** — dozens of LLM calls per problem.
- **Non-determinism** — hard to reproduce and regression-test.
- **Overkill risk** — if you only need reliable-but-plain problems, template sampling
  beats a 12-agent graph on every axis that matters.

## The core tension

- **Templates** give bulletproof correctness but low novelty (recognizable problems).
- **Forward LLM generation** gives high novelty but poor correctness.

A good design buys novelty from the *ideation/seeding* layer and correctness from a
*backward-construction + external-verifier* core — getting both without paying the
full price of either extreme. See `03-architecture-options.md`, option D.
