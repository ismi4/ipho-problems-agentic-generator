# Five-problem experiment results (partial)

**Status:** ABORTED — OpenAI `insufficient_quota` after $1.1382 / $25.00 (40 calls).

## Corpus ready
Five mechanics problems with clean + faulty solutions (see `INJECTED_ERRORS_FIVE.md`).

## Completed cells (5)
- S3 `2020_Q2/clean`: verdict=REJECT correct=False faults=0/0 $0.2147
- S3 `2020_Q2/faulty`: verdict=REJECT correct=True faults=3/3 $0.2048
- S3 `2021_Q1/clean`: verdict=ACCEPT correct=True faults=0/0 $0.2168
- S3 `2021_Q1/faulty`: verdict=REJECT correct=True faults=4/5 $0.2778
- S3 `2023_Q3/clean`: verdict=ACCEPT correct=True faults=0/0 $0.1312

## Missing
25 cells (remaining S3 + all S2/S1).

## Resume
```bash
cd verifier_experiments
python -m systems_bench.run_five_problems --hard-cap 25 --resume
python -m systems_bench.build_submission_report
```
