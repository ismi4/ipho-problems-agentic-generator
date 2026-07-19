# SYSTEMS.md experiment harness

Runs the cost/quality ladder in [`../SYSTEMS.md`](../SYSTEMS.md) on the **2023 Water-and-Objects** clean/faulty solution pair only.

## Quick start

```bash
source /workspace/.venv/bin/activate   # or create a venv + pip install -r requirements.txt
export OPENAI_API_KEY=...
cd verifier_experiments
python -m systems_bench.run_experiments --hard-cap 25.0
python -m systems_bench.build_submission_report
```

Outputs land in `results/` and `../../report/SUBMISSION_REPORT.pdf`.

## What was measured

See [`EXPERIMENT_RESULTS.md`](EXPERIMENT_RESULTS.md) and `results/summary.json`.
Actual OpenAI spend for the reported run: **~$1.31** under a **$25** hard cap.
