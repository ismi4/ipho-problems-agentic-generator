# AI-Use Log

This project was built by an autonomous coding agent (Cursor Cloud Agent, "Opus 4.8"
class model) executing `CLOUD_AGENT_SPEC.md`. This log records how AI was used, tagged
**AI-led** / **joint** / **human-led**. The only human inputs were the two specs
(`CLOUD_AGENT_SPEC.md`, `DEFINITION.MD`) and the operating constraints (OpenAI-only,
<$10 budget). No line-by-line human authoring occurred; "human-led" therefore tags
decisions fixed by the specs.

| Activity | Mode | Notes |
|---|---|---|
| Problem framing & scoping (verifier as cost surface) | human-led | Fixed by `CLOUD_AGENT_SPEC.md` §0–§2. |
| Correctness definition & failure-mode taxonomy | human-led | From `DEFINITION.MD`. |
| Model ladder & budget guardrail policy | joint | Spec set the constraints; agent pinned exact ids/prices and implemented the kill-switch. |
| PDF retrieval + `pdftotext` transcription of 3 problems | AI-led | Agent found the correct URLs and extracted text. |
| Machine-checkable sub-part transcriptions (`problems_data.py`) | AI-led | Agent transcribed reference answers as SymPy/Pint-checkable objects from the official solution PDFs. |
| Fault catalogue (single-fault injections) | AI-led | Agent authored one documented fault per taxonomy category per problem. |
| Deterministic checkers (Pint/SymPy) | AI-led | Agent implemented Tier-0/1. |
| Verifier configs (A/B/C V0–V2 + composed) | AI-led | Agent implemented all 10 configurations. |
| Cost/usage logging + spend tracker | AI-led | Agent implemented real-usage accounting from OpenAI responses. |
| Threshold tuning on dev split | AI-led | Agent ran nano on dev and picked the threshold. |
| Running the benchmark (real OpenAI calls) | AI-led | ~x calls, logged to `runs/`. |
| Analysis, plots, CIs | AI-led | Agent implemented `score.py`/`cost.py`/`report.py`. |
| Report, decision log, deck | AI-led | Agent authored all write-ups from the measured results. |
| Intellectual-honesty checks (negative results, threats to validity) | joint | Spec mandated them; agent identified and reported the specific ones. |

The underlying reasoning models used *inside the product under test* are OpenAI
`gpt-5` / `gpt-5-mini` / `gpt-5-nano` (see `prices.json`). Every prompt sent to them is
constructed in `verifier/common/prompts.py`; every response's usage is logged to
`runs/*.jsonl`. Prompts are not reproduced verbatim here to keep the log readable, but
they are fully determined by the code and the frozen dataset (reproducible).
