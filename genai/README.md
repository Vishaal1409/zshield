# genai

Customer alert and analyst summary for flagged payments. Template by default (no keys, no network).

- `from genai.explain import generate_alert, analyst_summary, template_alert`; each takes one dict and returns a str.
- Pass `{"decision", "amount", "reasons"}`; better also `risk_score`, `type`, `txn_id` (txn_id is for logs only).
- Alert is `""` for APPROVE. Functions never raise; extra keys are ignored.
- Optional model: `GENAI_PROVIDER=watsonx` or `openai_compat` (see `DESIGN.md`); failures fall back to the template.
- Tests: `.venv/bin/python -m pytest genai/tests -q` (offline).

Input: `{"decision": "HOLD", "amount": 9000, "type": "TRANSFER", "risk_score": 0.99, "reasons": ["Account emptied in one transfer", "Large payment at an unusual hour", "New recipient"]}`

Alert:
```
We paused a payment of ₹9,000 for a safety review. Reason: account emptied in one transfer, large payment at an unusual hour, new recipient. Our team will contact you. Never share your OTP or PIN.
```
Analyst summary:
```
Payment held for review: TRANSFER of ₹9,000, risk score 0.99.
Flagged because: Account emptied in one transfer; Large payment at an unusual hour; New recipient.
Action: review the case and choose Approve, Block or Escalate.
```
