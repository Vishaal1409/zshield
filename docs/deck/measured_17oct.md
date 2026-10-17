### Load test: Arun laptop, Intel i7-8850H  (2026-10-17 23:58)

Scorer: `placeholder_rule` | requests: 5000 | concurrency: 1 | errors: 0 | decisions: {'APPROVE': 4921, 'HOLD': 30, 'STEP_UP': 49}

| Metric | End-to-end (client, ms) | API-reported decision latency (ms) |
|---|---|---|
| mean | 2.64 | 0.034 |
| p50 | 2.52 | 0.032 |
| p95 | 3.23 | 0.043 |
| p99 | 4.19 | 0.061 |

Throughput: **375 transactions/s** (5000 in 13.3s).

End-to-end includes HTTP and JSON on the same machine as the client. API-reported latency is features + model + thresholds only (alert text is timed separately in the audit log).

### Load test: Arun laptop, Intel i7-8850H  (2026-10-17 23:58)

Scorer: `placeholder_rule` | requests: 5000 | concurrency: 8 | errors: 0 | decisions: {'APPROVE': 4921, 'STEP_UP': 49, 'HOLD': 30}

| Metric | End-to-end (client, ms) | API-reported decision latency (ms) |
|---|---|---|
| mean | 10.59 | 0.033 |
| p50 | 10.19 | 0.033 |
| p95 | 13.44 | 0.041 |
| p99 | 16.12 | 0.052 |

Throughput: **718 transactions/s** (5000 in 7.0s).

End-to-end includes HTTP and JSON on the same machine as the client. API-reported latency is features + model + thresholds only (alert text is timed separately in the audit log).

