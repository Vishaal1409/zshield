# Responsible AI checklist

ZShield scores payments and recommends an action. A person decides on the risky ones.
Everything below is built and can be checked in the repo. The API runs a rule-based scorer (`placeholder_score` in `api/model_runtime.py`); `GET /health` reports which scorer is loaded.

| Area | What we do | How a judge can see it |
|---|---|---|
| **Privacy** | Synthetic data only. No names, phones or demographics used as features. Account IDs are pseudonymous codes, and the audit log stores none of them. Only these facts reach the alert text: amount, type, decision, risk score, reasons. The transaction ID is used for logs only; account IDs never reach the alert step. | `features/features.py` (feature list), `api/db.py` (`SCHEMA`), `genai/sanitize.py`, test `test_only_allowed_keys_reach_prompt`. |
| **Fairness** | No protected or demographic attributes exist in the data or the features, so no decision can use them. | `features/features.py`, `api/state.py`. |
| **Transparency** | Every flagged payment shows up to 3 plain-language reasons, produced from the payment's features, and a short alert text. | `POST /score` response (`reasons`, `alert_text`); `rule_reasons` in `api/decision.py`; `GET /alerts`; the dashboard table. |
| **Human oversight** | HOLD payments go to an analyst who can Approve, Block or Escalate. The AI recommends; a person decides. The action is stored, and "Value intercepted" excludes payments an analyst approved. | `POST /analyst_action` (try it at `/docs`), `AuditDB.set_status` and `stats()` in `api/db.py`; test `test_alerts_stats_and_analyst_action`. |
| **Safe GenAI** | Alert text only rephrases facts we give it and cannot change the decision. Alerts come from fixed templates. Every alert is checked by `genai/validate.py`: 40 words max, amount matches, no other numbers, no account IDs, decision wording matches, no promises such as "your money is safe", no names, no request for an OTP or PIN. Text from an optional language model must also use only an allowed word list; any failure, error or a 1.5 s timeout falls back to the template and is logged. Reason text is treated as untrusted data. The checks are strict, but they are pattern checks, not proof. | `genai/validate.py`, `genai/rules.py`, `genai/tests/test_alerts.py` (119 offline tests), `genai/DESIGN.md`; `_alert_text` in `api/main.py`; test `test_alert_timeout_falls_back_to_template`. |
| **Robustness** | If scoring raises any error, the decision is STEP_UP (score 0.5), never a silent approve, and the error is stored. Bad input (negative amount, NaN, missing field) gets HTTP 422. A repeated transaction ID returns the first decision. A failed audit write never blocks a decision. | `FAILSAFE_SCORE` in `api/decision.py`; `score()` in `api/main.py`; tests `test_model_failure_fails_safe_to_step_up_and_is_logged`, `test_bad_input_rejected_422`, `test_duplicate_txn_id_returns_original_and_is_not_rescored` in `api/tests/test_api.py`. |
| **Accountability** | Every decision is written to a SQLite audit log: score, decision, reasons, alert text, latency, scorer name, error, analyst status. | `api/db.py`; `GET /alerts`, `GET /stats`; test `test_audit_log_persists_on_disk`. |
| **Limits** | The data is synthetic and PaySim is relatively easy, so real-world performance is unknown. Patterns drift over time, and fraudsters adapt. Thresholds trade customer friction against missed fraud. With no demographic data, fairness can only be checked through proxies such as payment type and amount. | This page, and slide 9 of the deck. |

IBM Z: the system is designed for IBM Z / LinuxONE.

## Short version for the dashboard

- Synthetic data only. No names or demographics.
- Every flagged payment shows its reasons.
- A person decides on held payments.
- GenAI only rephrases facts. Checked, with fallback.
- If scoring fails, we step up, never silently approve.
- Every decision is logged. Limits stated openly.

<!-- word count: 42 words -->
