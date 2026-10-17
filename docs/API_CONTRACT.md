# API contract (do not change without telling Vishaal)

## POST /score
Request:
```json
{
  "txn_id": "T1",
  "step": 12,
  "type": "TRANSFER",
  "amount": 9000.0,
  "nameOrig": "C123",
  "oldbalanceOrg": 9000.0,
  "newbalanceOrig": 0.0,
  "nameDest": "C456",
  "oldbalanceDest": 0.0,
  "newbalanceDest": 0.0
}
```
Response:
```json
{
  "txn_id": "T1",
  "risk_score": 0.97,
  "decision": "HOLD",
  "reasons": ["Account emptied in one transfer", "New recipient", "Unusual amount"],
  "alert_text": "Short plain-language message",
  "latency_ms": 4.2
}
```
decision is one of APPROVE, STEP_UP, HOLD.

## GET /health
{"status": "ok"}

## GET /stats
total_processed, flagged_count, held_count, value_intercepted, avg_latency_ms, p95_latency_ms

## GET /alerts
Latest flagged transactions: txn_id, amount, risk_score, decision, reasons, alert_text, analyst_status

## POST /analyst_action
{"txn_id": "T1", "action": "APPROVE" | "BLOCK" | "ESCALATE"}
