# ZShield demo script (3 minutes)

Spoken words are about 150 per minute. Personas are illustrative. Everything on screen below runs in the repo today: the API, the producer, the one-page dashboard and the API docs page. The numbers are from the replay of `docs/samples/sample_stream.csv` (synthetic) with the rule-based scorer.

## Main version

### 0:00-0:30 Problem (73 words)

| What's said | What's on screen |
|---|---|
| In 2025, 28 lakh digital payment frauds were reported on India's cybercrime portal, worth ₹22,931 crore. The Reserve Bank says that because payments are instant, "the scope for timely intervention and recovery of funds becomes limited." So we asked: how can we score every payment as it happens, stop the dangerous ones before settlement, explain the decision in plain language, and keep a human in control, without blocking honest customers? This is ZShield. | Slide 1: the stat card and the problem line. Source in small text (RBI, 9 Apr 2026). |

### 0:30-2:00 Live demo (194 words)

| What's said | What's on screen |
|---|---|
| Here is a replay of 252 synthetic payments, sent to ZShield one by one, the way a payment switch would send them. Each one is scored as it arrives. | Terminal: `python -m api.producer docs/samples/sample_stream.csv --rate 20 --reset`. Dashboard beside it: the Processed tile climbs. |
| Story one, the Scam Drain. Think of Kamla, an illustrative user. At 2 AM a caller pushes her to send her whole balance, forty-eight thousand rupees, to a brand-new recipient. ZShield holds it before settlement, with three reasons: the account was emptied in one transfer, the recipient is new, and it is a large payment at an unusual hour. The alert says the payment is paused, our team will contact her, and she should never share her OTP or PIN. The alert only rephrases these facts. It cannot change the decision. | Dashboard, "Latest flagged payments": row T240, HOLD, risk 0.95, the three reasons and this alert text: "We paused a payment of ₹48,000 for a safety review. Reason: account emptied in one transfer, new recipient, large payment at an unusual hour. Our team will contact you. Never share your OTP or PIN." |
| Story two, the Mule Burst. Ten different payers send money to one account. After five transfers, ZShield sees the pattern and asks for an extra check on each new one. | Five STEP_UP rows, T247 to T251, with the reason "Many payments to this recipient in a short time". |
| Story three, a normal day. 245 of the 252 payments went straight through, with no extra step. | Tiles: Processed 252, Flagged 7. Avg latency tile in milliseconds. |
| Now Meera, our illustrative analyst. She blocks the held payment. The action goes into the audit log, and the dashboard shows it. The AI explains. She decides. | Browser tab `http://localhost:8000/docs`, POST /analyst_action, body `{"txn_id": "T240", "action": "BLOCK"}`, Execute. Back to the dashboard: T240 shows analyst status BLOCK. |

### 2:00-2:30 Architecture and IBM Z (63 words)

| What's said | What's on screen |
|---|---|
| Every payment takes one short path: live features from past events only, a scorer, then the decision engine. Every decision is written to an audit log. If scoring fails, the payment gets an extra check, never a silent approval. ZShield is designed for IBM Z and LinuxONE: to decide inside the payment flow, before settlement, without sending payment data to an outside server. | Slide 5 (architecture as built), then slide 6 (design for IBM Z / LinuxONE). |

### 2:30-3:00 Responsible AI and impact (66 words)

| What's said | What's on screen |
|---|---|
| We use synthetic data only, with no names or demographics. Every flagged payment shows its reasons, every alert is checked word by word, and a person makes the final call. In this replay, seventy-nine thousand five hundred rupees in two drain payments was held before settlement, and honest payments went straight through. Score every payment, stop it before settlement, keep a human in control. Thank you. | Slide 9, then slide 10 with the dashboard tiles (Value intercepted 79,500). |

Main version total: 396 words.

## Backup version (60 seconds, 125 words)

Use when the live replay fails. Play the backup clip and show the audit log. Say it once and move on.

| What's said | What's on screen |
|---|---|
| The live replay is not responding, so here is the recording. In 2025, 28 lakh digital payment frauds were reported in India, and the Reserve Bank says recovery becomes limited once payments are instant. ZShield decides before settlement. In this clip, 252 synthetic payments are replayed. A 2 AM payment that empties an account into a new recipient is held, with three plain reasons and a calm alert. A burst of payments into one account gets an extra check. 245 honest payments go straight through. The analyst blocks the held payment, and the audit log records it. If scoring ever fails, the payment gets an extra check, never a quiet approval. ZShield is designed for IBM Z and LinuxONE. The AI explains. A human decides. | Backup clip of one full run of the main version (recorded from the current dashboard). Then `http://localhost:8000/alerts` in the browser: the flagged decisions with score, reasons, alert text and analyst status. Close on slide 9. |

## Pre-flight checklist

- [ ] API running with ONE worker: `uvicorn api.main:app --port 8000`.
- [ ] `curl localhost:8000/health` shows `"scorer": "placeholder_rule"`. Call it "the rule-based scorer" when speaking.
- [ ] Dashboard open: `streamlit run dashboard/app.py`.
- [ ] Browser tab open at `http://localhost:8000/docs`, on POST /analyst_action.
- [ ] Replay with `--reset` every time, so the log is fresh and the held payment is T240.
- [ ] `GENAI_PROVIDER` not set, so alerts come from the templates and no network is needed.
- [ ] Backup clip recorded from one full run and saved locally.
- [ ] Time one run with a stopwatch. Target 3:00.
