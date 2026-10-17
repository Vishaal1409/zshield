### Load test: laptop  (2026-10-17 13:55)

Scorer: `placeholder_rule` | requests: 5000 | concurrency: 1 | errors: 0 | decisions: {'APPROVE': 4921, 'HOLD': 30, 'STEP_UP': 49}

| Metric | End-to-end (client, ms) | API-reported decision latency (ms) |
|---|---|---|
| mean | 2.60 | 0.033 |
| p50 | 1.92 | 0.030 |
| p95 | 3.01 | 0.050 |
| p99 | 3.62 | 0.061 |

Throughput: **376 transactions/s** (5000 in 13.3s).

End-to-end includes HTTP and JSON on the same machine as the client. API-reported latency is features + model + thresholds only (alert text is timed separately in the audit log).

### Load test: laptop  (2026-10-17 13:55)

Scorer: `placeholder_rule` | requests: 5000 | concurrency: 8 | errors: 0 | decisions: {'APPROVE': 4921, 'STEP_UP': 49, 'HOLD': 30}

| Metric | End-to-end (client, ms) | API-reported decision latency (ms) |
|---|---|---|
| mean | 14.13 | 0.035 |
| p50 | 10.47 | 0.034 |
| p95 | 14.97 | 0.052 |
| p99 | 19.08 | 0.063 |

Throughput: **528 transactions/s** (5000 in 9.5s).

End-to-end includes HTTP and JSON on the same machine as the client. API-reported latency is features + model + thresholds only (alert text is timed separately in the audit log).

