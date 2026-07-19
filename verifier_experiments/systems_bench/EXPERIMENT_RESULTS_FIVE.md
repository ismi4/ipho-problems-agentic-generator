# Five-problem experiment results (complete)

**Spend (this process):** $2.4647 / $9.50 hard cap  
**Prior partial (quota-aborted attempt):** $1.1382  
**Total OpenAI for five-problem effort:** $3.6028  
**Calls (this process):** 161 · **Matrix:** 30/30 complete

## Cost / quality

| System | Mean $/sol | vs S3 | Clean accept | Faulty reject | Faults localized |
|---|---|---|---|---|---|
| S3 | $0.2093 | baseline | 40% | 100% | 14/17 |
| S2 | $0.1155 | −44.8% | 60% | 100% | 12/17 |
| S1 | $0.0262 | −87.5% | 60% | 80% | 10/17 |

## Verdict
S2 ≈ **44.8% cheaper** than S3 at equal (100%) faulty-document reject rate, with fewer false rejects on cleans. S1 is cheapest but false-accepted 2025 faulty.
