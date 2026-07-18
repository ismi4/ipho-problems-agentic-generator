# Mapping to LangChain / LangGraph

Why LangGraph fits *this* problem specifically, and how the pieces land.

## Why LangGraph over a plain chain

- The generate→solve→verify→**repair** loop is **cyclic**; chains are DAGs. LangGraph
  models cycles natively.
- **Stateful** — a shared graph state carries the seed, the model, the constructed
  solution, verification results, and the draft statement across nodes.
- **Checkpointing** — persist state between nodes; replay/resume a generation; essential
  for debugging non-deterministic multi-agent runs.
- **Human-in-the-loop** — interrupt nodes let an expert approve seeds or calibrate
  difficulty mid-run.
- **Conditional edges** — route on verifier outcome (pass → compose, fail → repair or
  discard) and on domain (backward vs. forward, per Option E).

## Suggested state shape (sketch, not final)

```
GenState = {
  seed: {strategy, raw_idea, source_refs},
  model: {assumptions, params, governing_eqs},
  solution: {symbolic, numeric, steps, units_ok},
  verification: {sympy_ok, sim_ok, independent_resolve_ok, notes},
  statement: {prose, givens, unknowns, subparts[]},
  quality: {difficulty_est, discrimination, novelty_score, critic_notes},
  artifacts: {figures[], marking_scheme},
  control: {attempt, status, route}
}
```

## Nodes → responsibilities

| Node | Role | Tools |
|---|---|---|
| `seeder` | pick strategy, produce raw idea | web/arXiv/YouTube search, vision |
| `modeler` | build model + constructed solution (backward) | LLM + SymPy |
| `verifier` | symbolic + numeric + dimensional checks | **SymPy, sim (no LLM authority)** |
| `composer` | write statement, design sub-part arc | LLM |
| `resolver` | independent re-solve of the statement | LLM + SymPy |
| `calibrator` | estimate difficulty/discrimination | student-simulator agents |
| `novelty` | reject near-duplicates | embeddings + corpus |
| `critic` | aesthetics, clarity, physicality | LLM |
| `figurer` | generate + check diagrams | TikZ/matplotlib |
| `rubricker` | solution write-up + marking scheme | from verified trace |

## Tools = LangChain tools

SymPy, the numeric simulator, retrieval sources, embedding search, and figure renderers
are all wrapped as LangChain tools so any node can call them. The **verifier's tools are
authoritative** — its pass/fail is not an LLM opinion.

## Build order

1. Tools first (SymPy solve + dimensional check + one sim harness).
2. Option A baseline agent using those tools.
3. Convert to the Option D LangGraph with the verifier core.
4. Add calibrator/novelty/figurer once the correctness core is trustworthy.
