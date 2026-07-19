# Experiment Results — SYSTEMS.md on 2023 clean/faulty pair

**Hard cap:** $25.00 · **Actual spend:** $1.3055 · **Calls:** 71

## Corpus
- Clean: `pdfs/IPhO_2023_S3.pdf` (must ACCEPT)
- Faulty: `pdfs/faulty/IPhO_2023_S3_FAULTY.pdf` (must REJECT; ERR-1..5)
- Problem: `pdfs/IPhO_2023_Q3.pdf`
- Held out: 2021 pair (not run)

## Ingestion
- I4 terra mean: $0.1292/solution PDF (0 retries)
- I2 mini mean: $0.0221

## sol vs terra (faulty A.1)
- terra: FAIL ($0.0383)
- sol: FAIL ($0.0565)

## Systems
| System | Mean $/sol | vs S3 | Clean | Faults caught | Escalation |
|---|---|---|---|---|---|
| S3 | $0.2814 | 0.0% | ACCEPT | 5/5 | 33% |
| S2 | $0.1324 | 53.0% | ACCEPT | 5/5 | 17% |
| S1 | $0.0404 | 85.7% | ACCEPT | 5/5 | 0% |

## Verdict
S2 is **53% cheaper than S3** at equal quality on this pair (0 false rejects, 0 false accepts, 5/5 faults). Full JSON: `systems_bench/results/`. Submission PDF: `report/SUBMISSION_REPORT.pdf`.
