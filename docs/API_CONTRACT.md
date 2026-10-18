# API contract (do not change without telling Vishaal)

Last updated: added GET /recent and the extra alert fields agreed with Armaan.

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
decision is one of APPROVE, STEP_UP, HOLD. reasons are plain strings (no weights).

## GET /health
{"status": "ok"}

## GET /stats
```json
{
  "total_processed": 1200,
  "flagged_count": 34,
  "held_count": 11,
  "value_intercepted": 183000.0,
  "avg_latency_ms": 3.1,
  "p95_latency_ms": 6.4
}
```
- flagged_count = STEP_UP + HOLD
- held_count = HOLD
- approved = total_processed - flagged_count

## GET /alerts
Flagged payments only (STEP_UP and HOLD), newest first. A list of objects:
```json
{
  "txn_id": "T1",
  "risk_score": 0.97,
  "decision": "HOLD",
  "reasons": ["Account emptied in one transfer"],
  "alert_text": "We paused a payment ...",
  "analyst_status": "PENDING",
  "amount": 9000.0,
  "type": "TRANSFER",
  "step": 12,
  "nameOrig": "C123",
  "nameDest": "C456",
  "latency_ms": 4.2
}
```
analyst_status is one of PENDING, APPROVE, BLOCK, ESCALATE.

## GET /recent?limit=50
Latest decisions of ALL types (including APPROVE), newest first. Same fields as /alerts.
Used by the dashboard live feed and the latency chart (latency_ms per transaction).

## POST /analyst_action
{"txn_id": "T1", "action": "APPROVE" | "BLOCK" | "ESCALATE"}
Response: {"ok": true}

## Ground truth (dashboard evaluation view only)
The API never sees fraud labels. The dashboard joins txn_id to isFraud in demo_stream.csv to show
false-positive rate and value missed. That page is labelled "evaluation view, uses ground-truth labels".
