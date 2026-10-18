# Fairness and robustness report (template)

Owner of the numbers: Joshua. Every `[[NEEDS: ...]]` is a blank to fill from real runs. Do not fill with estimates.

## (a) Setup
| Item | Value |
|---|---|
| Model version / file | [[NEEDS: model name, ONNX file hash or date from Joshua]] |
| Scorer reported by `GET /health` during the run | [[NEEDS: "onnx" or "placeholder_rule" from Joshua]] |
| Dataset | PaySim (synthetic). [[NEEDS: rows, fraud rate from Balaa]] |
| Test split (by `step`) | [[NEEDS: train steps, test steps from Joshua/Balaa]] |
| Thresholds | step_up = [[NEEDS: from model/thresholds.json]], hold = [[NEEDS: from model/thresholds.json]] |
| Definition of "flagged" | decision is STEP_UP or HOLD (as in `GET /stats`) |
| Definition of "miss" | fraud payment with decision APPROVE |
| Definition of "false positive" | non-fraud payment with decision STEP_UP or HOLD |

## (b) Error rates by transaction type
Fraud in PaySim appears only in TRANSFER and CASH_OUT: [[NEEDS: Balaa/Joshua to confirm from EDA]]. If confirmed, the other types will have n_fraud = 0 and the miss rate is undefined ("n/a"), not zero.

| Type | n | n_fraud | False-positive rate | Miss rate | Flagged rate |
|---|---|---|---|---|---|
| CASH_IN | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] |
| CASH_OUT | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] |
| DEBIT | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] |
| PAYMENT | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] |
| TRANSFER | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] |
| All | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] |

## (c) Error rates by amount band
Band edges are proposed, Joshua/Balaa to confirm after the EDA: [[NEEDS: band edges, for example 4 to 5 bands chosen from amount quantiles]].

| Band | Range | n | n_fraud | False-positive rate | Miss rate |
|---|---|---|---|---|---|
| 1 (lowest) | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] |
| 2 | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] |
| 3 | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] |
| 4 | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] |
| 5 (highest) | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] | [[NEEDS]] |

Largest gap between groups: type [[NEEDS]], amount band [[NEEDS]]. Gap threshold that triggers action: [[NEEDS: team decision]].

## (d) Early versus late steps (drift)
| Measure | Early steps | Late steps |
|---|---|---|
| Step range | [[NEEDS]] | [[NEEDS]] |
| n / n_fraud | [[NEEDS]] | [[NEEDS]] |
| Score distribution (median, 95th percentile) | [[NEEDS]] | [[NEEDS]] |
| Flagged rate | [[NEEDS]] | [[NEEDS]] |
| False-positive rate / miss rate | [[NEEDS]] | [[NEEDS]] |

Drift statistic between the two score distributions: PSI = [[NEEDS]] or KS = [[NEEDS]] (say which one was used).

## (e) Robustness checks
| Check | Test | Result |
|---|---|---|
| Model or scorer raises an error: decision is STEP_UP, error stored | `test_model_failure_fails_safe_to_step_up_and_is_logged` in `api/tests/test_api.py` | Pass (lead run, 17 Oct, 18/18, placeholder scorer) |
| Bad input (negative amount, NaN, missing field) gives 422, not 500 | `test_bad_input_rejected_422`, `test_missing_field_rejected_422` in `api/tests/test_api.py` | Pass (lead run, 17 Oct, 18/18, placeholder scorer) |
| Zero and huge amounts handled | `test_zero_and_huge_amounts_are_handled` | Pass (lead run, 17 Oct, 18/18, placeholder scorer) |
| Duplicate transaction ID is not re-scored | `test_duplicate_txn_id_returns_original_and_is_not_rescored` | Pass (lead run, 17 Oct, 18/18, placeholder scorer) |
| GenAI timeout falls back to template | `test_alert_timeout_falls_back_to_template` in `api/tests/test_api.py` | Pass (lead run, 17 Oct, 18/18, placeholder scorer) |
| GenAI output validation and fallback (wrong amount, extra numbers, promises, names, decision wording, OTP/PIN requests) | `genai/tests/test_alerts.py`, rules in `genai/validate.py` and `genai/rules.py` (Arun) | Pass (lead run, 17 Oct, 119 tests, offline) |
| ONNX loader returns the same probability as a stand-in sklearn model (not the fraud model) | `test_onnx_scorer_matches_sklearn` | Pass (lead run, 17 Oct, 18/18, placeholder scorer) |

## (f) How to read this
False-positive rate is the share of normal payments we flag, which is friction for honest customers. Miss rate is the share of fraud we approve, which is lost money. A group with a much higher rate than the others is a warning sign, but check n and n_fraud first: with few fraud cases a rate can swing widely and means little. Gaps by type or amount may reflect real differences in the data rather than unfair treatment, so a gap is a reason to investigate, not proof either way. Lowering thresholds cuts misses and raises false positives; raising them does the opposite.

## (g) Limits
All results come from synthetic PaySim data. PaySim is relatively easy compared with real bank fraud, so these numbers should not be read as real-world performance. The data has no demographic attributes, so we cannot test fairness across groups of people. We check only proxies: transaction type and amount band. That is a weak substitute. Patterns drift over time and fraudsters adapt to what gets blocked, so a model that works on a past period can fail later. Threshold choices trade customer friction against missed fraud and are a business decision, not a technical fact. Observed gaps: [[NEEDS: Joshua's plain-language summary of the largest gaps and drift found]].

## (h) What we would do with real bank data
- Get legal and privacy sign-off before any real data is used; keep it inside the bank's secured environment.
- Test fairness with approved group definitions and proper consent and governance, not only proxies.
- Re-fit thresholds on the bank's own fraud costs and customer-friction limits.
- Monitor drift and error rates continuously, with alerts and a retraining plan.
- Review analyst overrides (Approve/Block/Escalate) to find where the model is wrong.
- Run a shadow period (score but do not act) before going live, and keep a human in the loop on HOLD.
