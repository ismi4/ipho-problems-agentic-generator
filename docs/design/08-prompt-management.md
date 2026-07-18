# Prompt Management & Synthesis

Two separable ideas got bundled here. They have different build/buy answers.

## The split

1. **Prompt management (commodity):** versioning, editing, edit-tracking, labels, UI,
   storage. Solved space — Langfuse (OSS, self-hostable, has all of this + a UI),
   LangSmith (native LangChain), PromptLayer, Humanloop, Agenta. **Do not ship as a
   separate product first** — red ocean, and it delays the actual differentiator.
2. **Corpus-driven prompt synthesis + optimization (novel):** generate an evaluator's
   prompt *from* a corpus of existing IPhO problems, then measure and improve it. This
   is the defensible bit. Build it **internally**, and only once there's something to
   optimize against (see the gold-set catch below).

## The governing constraint: you can't optimize what you can't score

- "LLM writes the eval prompt from a corpus" produces **candidate** prompts.
- Selecting among candidates requires a **gold set** — a small human-labeled dataset
  (e.g. 20–30 problems labeled pass/fail for a format evaluator).
- Corpus → cheap candidates. Gold set → real selection. **The gold set is the cost and
  the moat.** Without it, prompt optimization is vibes.
- Ties directly to the eval-harness need in `04-key-challenges.md`.

## Prompt synthesis pipeline (per evaluator role)

```
corpus + task spec + few-shot  →  drafter (LLM)  →  candidate prompt
candidate prompt  →  scorer (run against gold set)  →  metrics
metrics  →  optimizer loop (critic / DSPy-style / manual)  →  best candidate
best candidate  →  register as new version (status=draft) → human promote → production
```

Start manual (human writes v1, gold set scores it). Add the automated drafter/optimizer
only after ≥3 evaluators exist and the gold sets are stable. Over-automating early
optimizes prompts against a moving target.

## How prompts bind into LangChain / LangGraph

**Decouple content from code.** Nodes reference prompts by key + label, resolved at
runtime from a registry — never inline strings.

```python
prompt = registry.get("eval.format_check", label="production")  # -> ChatPromptTemplate
```

- **Immutable versions + movable labels.** Never mutate a published version; an edit
  creates a new version with `parent_version_id`. `production`/`staging`/`latest` are
  pointers you *promote* — swap prompts without code changes. (git-tag / Docker-tag model.)
- **Provenance.** The resolved version id is written into each run's trace, so every
  generated problem records which prompt versions produced it → reproducibility
  (`04-key-challenges.md`).
- **Caching.** Cache resolved prompts by (key, label); invalidate on label move. Don't
  hit Supabase per node call.
- **Typed variables.** Each version declares its template variables + schema, so a node
  fails loudly if it passes the wrong inputs.

## Storage split (DECIDED — Langfuse adopted, see `07-decisions-v1.md` D4)

Langfuse (self-hosted) owns prompts + gold sets + scores. Supabase owns domain data only.

| Concern | Home |
|---|---|
| Prompt versions + labels (movable pointers) | **Langfuse Prompts** |
| Run tracing + provenance (which prompt made which problem) | **Langfuse Traces** |
| Gold-set datasets (human-labeled eval data) | **Langfuse Datasets** |
| Eval scores (version ↔ measured quality) | **Langfuse Scores** |
| Generated problems, human-review queue, physics corpus | **Supabase** |

The earlier `prompt_versions` / `prompt_labels` / `gold_sets` / `eval_runs` tables are
**dropped** — Langfuse provides all of them. Invariants Langfuse already enforces:
versions immutable, labels move, promotions auditable, quality is a joinable fact.

## Minimal UI (only when justified)

List prompts → view/diff versions → edit (creates draft) → run against gold set (see
score) → promote label. A thin Next.js + Supabase app. **Or** skip building it and use
Langfuse's existing UI, backing the synthesis pipeline onto its API.

## Sequencing recommendation

1. **Now (thin):** a `PromptRegistry` interface + Supabase tables for versions/labels +
   runtime resolution & provenance. ~1 table pair + a client. Needed from day one for
   reproducibility.
2. **After ≥3 evaluators + gold sets exist:** the synthesis/optimization pipeline.
3. **Only if the synthesis piece proves differentiated:** consider productizing. The
   generic management layer is not a product worth shipping first.

**Open decision:** adopt Langfuse (get versioning + UI + tracing for free, self-hosted)
vs. build a thin Supabase registry (full control, more code). See `06-open-questions.md`.
