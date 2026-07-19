# IPhO-Mechanics Verifier — 50% Cheaper Inference at Equal Quality

A cost/quality benchmark for an automated **verifier** of IPhO-mechanics solutions.
It demonstrates **three independent cost-reduction levers**, each with a baseline and
two cumulative improvements (9 configs + a composed system), and tests whether the
2nd improvement of every solution costs **≤ 50% of its own baseline on all 3 problems
with no loss of verification quality** — under a **< $10** budget, using **OpenAI only**.

See `CLOUD_AGENT_SPEC.md` (experimental design) and `DEFINITION.MD` (correctness spec).
Full write-up in `REPORT.md`; decisions in `DECISION_LOG.md`; slides in
`presentation/DECK.pdf`.

## What's here

| Path | Purpose |
|---|---|
| `dataset/` | 3 IPhO problems (PDF dumps), `instances.jsonl` (30 labeled instances), `rubrics.json`, `discards.log` |
| `verifier/common/` | OpenAI client + usage logging + hard spend guard, verdict schema, Pint/SymPy deterministic checks, prompts |
| `verifier/solution_a\|b\|c/` | The three levers, V0→V2 |
| `verifier/composed/` | Bonus stacked A+B+C system |
| `bench/` | `build_dataset.py`, `tune.py`, `run.py`, `cost.py`, `score.py`, `report.py`, `make_deck.py` |
| `prices.json` | Pinned OpenAI price table (retrieval date recorded) |
| `runs/` | Raw per-call usage logs (cost from real usage) |
| `results/` | Tables (CSV), plots (PNG), `summary.json`, `spend_summary.json` |
| `presentation/` | `DECK.pdf` (+ editable `deck.md`, `assets/`) |

## Model ladder (pinned)

- Strong: `gpt-5` · Mid: `gpt-5-mini` · Nano: `gpt-5-nano` (see `prices.json`, retrieved 2026-07-18).
- Cost = input·price_in + cached_input·price_cached_in + output·price_out, from each
  response's actual `usage` (reasoning tokens billed as output; cached tokens priced at
  the cached rate). A process-wide spend tracker **aborts at $8** (headroom under $10).

## Reproduce

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install openai sympy pint pandas numpy matplotlib pytest reportlab
export OPENAI_API_KEY=...            # only secret required

cd verifier_experiments
python -m bench.build_dataset        # freeze dataset/instances.jsonl (deterministic)
python -m bench.tune                 # tune cascade thresholds on the dev split
python -m bench.run --configs A.V0 B.V0 C.V0 --reps 2 --workers 6 \
    --hard-cap 9.0 --out results/raw_results.jsonl
python -m bench.run --configs A.V1 A.V2 B.V1 B.V2 C.V1 C.V2 composed \
    --reps 3 --workers 6 --hard-cap 9.0 --prior-spend <prev_total> --append \
    --out results/raw_results.jsonl
python -m bench.report                # tables + plots + summary.json
python -m bench.make_deck            # presentation/DECK.pdf
```

Seeds: dataset generation seed `20250718`; bootstrap seed `7`; tuning is deterministic
given the dev split. OpenAI reasoning models are run at their default temperature
(gpt-5 does not accept a custom temperature); N reps capture residual variability.

## Budget spent

Total OpenAI spend for the reported run: **see `results/spend_summary.json`** (kept < $10;
hard kill-switch at $8 per run, made cumulative across runs via `--prior-spend`).

## Reps used (budget-driven)

- Strong-model V0 baselines (`A.V0`, `B.V0`, `C.V0`): **N=2**.
- All cheaper configs: **N=3**.
Per-instance costs are rep-averaged, so the per-problem 50% gate is unaffected; quality
uses majority-vote per instance. Documented as a threat to validity in `REPORT.md`.
