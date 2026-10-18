# ZShield

**Real-time AI that scores every payment as it happens, stops dangerous ones before settlement, explains why in plain language, and keeps a human in control.**

IBM Z Datathon 2026, Challenge 1: Real-Time AI for Critical Decisions. Event code: SSF2026.

> **Not running on LinuxONE, and why.** ZShield is designed for IBM Z / LinuxONE, but we are **not running it there**. We registered for the IBM LinuxONE Community Cloud and tried to deploy, but the portal failed (the server stayed stuck in "spawning" with no IP, and the portal returned "unknown error" and "service unavailable" pages) and we contacted IBM LinuxONE support without a fix before the deadline. The demo therefore runs locally on x86, and all numbers below were measured on x86 laptops with synthetic data. See [IBM Z status](#ibm-z--linuxone-status).

## The problem

Digital payments are instant and irreversible. A scam or account drain pays out in seconds, but most fraud alerts arrive later. Customers (often elderly or first-time digital users) lose savings, and bank analysts drown in alerts they cannot explain.

**Our question:** How can we score every payment as it happens, stop the dangerous ones before settlement, explain the decision in plain language, and keep a human in control, without blocking honest customers?

## What it does

| Decision | Meaning |
|---|---|
| APPROVE | Low risk. Goes through instantly. |
| STEP-UP | Medium risk. Extra check (warning, OTP or call-back) before money moves. |
| HOLD | High risk. Paused and sent to a human analyst with reasons and a case summary. |

If scoring fails, the system falls back to STEP-UP and logs it. It never silently approves.

## Architecture

1. **Stream simulator** (`api/producer.py`) replays transactions in time order at adjustable speed.
2. **Scoring API** (FastAPI) receives each transaction on `POST /score`.
3. **Live feature builder** computes features from past events only (balance mismatch, full-drain flag, new recipient, sender velocity, recipient inbound count). Training and serving use the same feature logic.
4. **ONNX model** (gradient-boosted trees) returns a fraud probability. ONNX keeps the model portable.
5. **Decision engine** maps the score to APPROVE / STEP-UP / HOLD using thresholds from `artifacts/model_meta.json`, plus a rule for mule-style bursts.
6. **GenAI alert layer** (`genai/`) rewrites the reasons into a short customer message and an analyst summary. It only rephrases supplied facts, cannot change the decision, is length-limited, and falls back to a template on timeout or failed check.
7. **Audit log** (SQLite) stores every decision, score, reasons, alert text, latency and analyst action.
8. **Dashboard** (Streamlit) shows the live feed, flagged cases, value intercepted, latency, and Approve / Block / Escalate actions.

## Results

Measured on PaySim, a **synthetic** dataset, with a time-based split (train on early steps, validate on middle steps, test on the latest steps) and no leakage. Full numbers are in `artifacts/metrics.json` and `model/model_card.md`.

| Metric (test period) | Baseline | ZShield model |
|---|---|---|
| PR-AUC | 0.752 | 0.99999 |
| Recall at 0.1% false-positive rate | see metrics.json | 100% |
| False-positive rate at the HOLD threshold | n/a | 0.12% |

**Read these with care.** PaySim is synthetic and fairly easy, so these scores will be higher than on real payment data. We report PR-AUC and recall at a fixed false-positive rate, not accuracy. The model misses the "Mule Burst" pattern, so a separate rule covers it.

Latency (p50, p95, p99): [CONFIRM: paste Joshua's benchmark table, and say it was measured on x86, not IBM Z].

## IBM Z / LinuxONE status

| Level | What | Status |
|---|---|---|
| 1 | Z-ready design: portable ONNX model, in-transaction scoring architecture, latency benchmark | Done (benchmarked on x86) |
| 2 | Run the scoring API on IBM LinuxONE / IBM Z | **Not done, because of LinuxONE Community Cloud issues.** Our server never finished provisioning and the portal returned errors; we emailed IBM LinuxONE support. Evidence: `docs/screenshots/`. We did not substitute an emulator or claim a Z run. [EDIT: if a server did come up, replace this row with what ran, plus `uname -m` showing `s390x`, `/health` and p95 latency.] |
| 3 | Compile the model with the IBM Z Deep Learning Compiler / use Telum acceleration | Not attempted |

**Why IBM Z for this problem (design rationale, not a measured claim):** core payments already run on IBM Z, so scoring next to the transaction avoids sending sensitive data to an outside ML server and avoids a network round trip. Telum-class processors include on-chip AI acceleration aimed at in-transaction inference.

## Run it

Requirements: Python 3.11. [CONFIRM every command below against the repo before publishing.]

```bash
git clone https://github.com/Vishaal1409/zshield.git
cd zshield
pip install -r requirements.txt

# 1. start the scoring API
uvicorn api.main:app --port 8000

# 2. start the dashboard (new terminal)
streamlit run dashboard/app.py

# 3. replay the demo stream (new terminal)
python api/producer.py --file demo_stream.csv --rate 100
```

Or with Docker: `docker compose up` [CONFIRM this works, or delete this line].

The PaySim data is not in the repo. Download it from Kaggle (link below) into `data/`.

## API

| Endpoint | Purpose |
|---|---|
| `POST /score` | Request: txn_id, step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig, nameDest, oldbalanceDest, newbalanceDest. Response: txn_id, risk_score, decision, reasons, alert_text, latency_ms |
| `GET /stats` | total_processed, flagged_count, held_count, value_intercepted, avg_latency_ms, p95_latency_ms |
| `GET /alerts` | Flagged transactions with score, reasons, alert_text, analyst_status |
| `GET /recent?limit=N` | Newest-first recent transactions for the live feed |
| `POST /analyst_action` | txn_id, action (APPROVE / BLOCK / ESCALATE) |
| `POST /admin/reset` | Demo helper, not part of the contract. Clears the audit log and in-memory state. Has no password. Do not expose it. |
| `GET /health` | Liveness |

## Responsible AI

- **Privacy:** synthetic data only. No names, phone numbers or demographics as features. Account IDs are pseudonymous. Only minimal facts go to the language model.
- **Fairness:** no protected attributes used. Error rates compared by transaction type and amount band; results and gaps in `docs/fairness_robustness.md`. [CONFIRM: say whether the full-test-split run was finished, otherwise say "proxy check on the demo file only".]
- **Transparency:** every flagged payment shows its top reasons and a plain-language explanation.
- **Human oversight:** held payments go to an analyst who can approve, block or escalate. The AI recommends; a person decides.
- **Safe GenAI:** only rephrases supplied facts, cannot change decisions, has a timeout and a template fallback.
- **Robustness:** if scoring fails, the system steps up and logs it.
- **Accountability:** every decision and analyst action is in the audit log.

See `docs/responsible_ai.md`.

## Limitations

- Synthetic data and an easy benchmark. Real-world performance would be lower.
- Not run or benchmarked on IBM Z hardware: LinuxONE Community Cloud access failed on our side of the portal (see above).
- Reasons are the top contributing factors; SHAP explanations are not implemented yet.
- Fraudsters adapt and data drifts. We have not tested long-term drift.
- The mule-burst pattern relies on a rule, not the model.
- `POST /admin/reset` is unauthenticated and for demos only.

## Repository layout

| Folder | Contents |
|---|---|
| `features/` | Shared feature code, data card |
| `model/` | Training, predictor, model card |
| `artifacts/` | model.onnx, model_meta.json, metrics.json |
| `api/` | FastAPI app, decision engine, state store, producer |
| `genai/` | Alert generation, templates, tests |
| `dashboard/` | Streamlit app |
| `docs/` | Deck, responsible-AI pages, charts, screenshots |

## Data and open-source credits

PaySim (synthetic mobile-money transactions): https://www.kaggle.com/datasets/ealaxi/paysim1. Built with pandas, scikit-learn, XGBoost / LightGBM, ONNX and ONNX Runtime, FastAPI, Uvicorn, Streamlit, Plotly, SQLite and Docker. [EDIT: keep only what you used; add the language model Arun used.]

## Team

Vishaal (lead, architecture, IBM Z, integration), Balaa (data and features), Joshua (machine learning), Abhinava (real-time backend), Armaan (dashboard), Arun (GenAI, responsible AI, deck, video).
