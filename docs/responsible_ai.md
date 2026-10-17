# Responsible AI checklist

ZShield scores payments and recommends an action. A person decides on the risky ones.
Status key: **Built** = in the repo now. **Partly built** = works, with a gap named. **Planned (owner)** = not done yet.
Model results do not exist yet: the API runs a placeholder rule scorer (`api/model_runtime.py`, `placeholder_score`) until Joshua's ONNX model lands. `GET /health` reports which scorer is loaded.

| Area | What we do | How a judge can see it | Status |
|---|---|---|---|
| **Privacy** | Synthetic data only (PaySim). No names, phones or demographics used as features. Account IDs are pseudonymous codes. The audit log stores no account IDs. Only the minimum facts go to the GenAI step: amount, type, decision, risk score, reasons (not the transaction ID, not account IDs). | `features/features.py` (feature list), `api/db.py` (`SCHEMA`), `features/data_card.md`, `genai/DESIGN.md`. | Partly built. Data card is a stub (Balaa). GenAI input limit depends on Arun's `genai/` rewrite. |
| **Fairness** | No protected or demographic attributes exist in the data or model. We compare false-positive and miss rates by transaction type and amount band, and report gaps. | `docs/fairness_robustness_template.md` (structure for the results). | Planned (Joshua: numbers; Balaa: type and band definitions). |
| **Transparency** | Every flagged payment shows up to 3 plain-language reasons and an alert text. Today the reasons come from rules that read the features. SHAP reasons replace them when Joshua's `model.explain.explain_top3` exists. | `POST /score` response (`reasons`, `alert_text`); `rule_reasons` in `api/decision.py`; `_load_explainer` in `api/main.py`; `GET /alerts`. | Partly built. Rule reasons live; SHAP pending (Joshua). |
| **Human oversight** | HOLD payments go to an analyst who can Approve, Block or Escalate. The AI recommends; a person decides. The analyst action is stored. "Value intercepted" excludes payments an analyst approved. | `POST /analyst_action`, `AuditDB.set_status` and `stats()` in `api/db.py`; test `test_alerts_stats_and_analyst_action` in `api/tests/test_api.py`. | Partly built. API done. Dashboard buttons pending (Armaan). |
| **Safe GenAI** | The text model only rephrases facts we give it. It cannot change the decision. Output is length-limited (40 words) and checked by `genai/validate.py`: amount matches, no other numbers, no account-ID patterns, decision wording matches, no promises such as "your money is safe", no names. Any failure falls back to a fixed template and is logged. Reason text is treated as untrusted data. ~2 s timeout. Default provider is offline templates. | `genai/validate.py`, `genai/tests/test_alerts.py`, `genai/DESIGN.md`. API side: `_alert_text` in `api/main.py`; test `test_alert_timeout_falls_back_to_template`. | Partly built. API timeout and fallback done. Validator and tests are Arun's `genai/` rewrite, in progress. |
| **Robustness** | If scoring raises any error, the decision is STEP_UP (score 0.5), never a silent approve. The error is logged and stored. Bad input (negative amount, NaN, missing field) gets HTTP 422. Duplicate transaction IDs return the first decision. A failed audit write never blocks a decision. | `FAILSAFE_SCORE` in `api/decision.py`; `score()` in `api/main.py`; tests `test_model_failure_fails_safe_to_step_up_and_is_logged`, `test_bad_input_rejected_422`, `test_duplicate_txn_id_returns_original_and_is_not_rescored` in `api/tests/test_api.py`. | Built |
| **Accountability** | Every decision is written to a SQLite audit log: score, decision, reasons, alert text, latency, scorer name, error, analyst status. | `api/db.py`; `GET /alerts`, `GET /stats`; test `test_audit_log_persists_on_disk`. | Built |
| **Limits** | We say plainly: data is synthetic and PaySim is relatively easy, so real-world performance is unknown. Patterns drift over time. Fraudsters adapt. Thresholds trade customer friction against missed fraud. With no demographic data, fairness is checked only through proxies (type, amount). | Section (g) of `docs/fairness_robustness_template.md`; `model/model_card.md`. | Partly built. Written in the template; model card is a stub (Joshua). |

IBM Z: we describe the system as designed for and deployable on IBM Z / LinuxONE. What actually ran there is Vishaal's to confirm (README, IBM Z section).

## Short version for the dashboard (Under the Hood page)

- Synthetic data only. No names or demographics.
- Every flagged payment shows its reasons.
- A person decides on held payments.
- GenAI only rephrases facts. Checked, with fallback.
- If scoring fails, we step up, never silently approve.
- Every decision is logged. Limits stated openly.

<!-- word count: 42 words -->
