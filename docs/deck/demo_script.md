# ZShield demo script (3 minutes)

Spoken words are about 150 per minute. Main version total: 448 words. Word counts exclude `[[NEEDS: ...]]` placeholders and stage directions. Personas are illustrative.

## Main version

### 0:00-0:30 Problem (73 words)

| What's said | What's on screen |
|---|---|
| In 2025, 28 lakh digital payment frauds were reported on India's cybercrime portal, worth ₹22,931 crore. The Reserve Bank says that because payments are instant, "the scope for timely intervention and recovery of funds becomes limited." So we asked: how can we score every payment as it happens, stop the dangerous ones before settlement, explain the decision in plain language, and keep a human in control, without blocking honest customers? This is ZShield. | Slide 1: the stat card and the problem line. Source in small text (RBI, 9 Apr 2026). |

### 0:30-2:00 Live demo (247 words)

| What's said | What's on screen |
|---|---|
| Story one, Scam Drain. Kamla is an illustrative user. A caller pressures her, and at 2 AM she sends her whole balance to a brand-new recipient. ZShield scores it in milliseconds. The result is HOLD, before settlement. Look at the detail. Three reasons: the account was emptied in one transfer, the payment is large for that hour, and the recipient is new. Below that is the alert. It says: we paused a payment of nine thousand rupees for a safety review, and we will contact you. It also tells her never to share her OTP or PIN. The alert is plain language. It only rephrases facts we give it. It cannot change the decision. | Dashboard, Live Feed. Run the Scam Drain story. The row turns HOLD. Open Alert Detail: top 3 reasons and this alert text: "We paused a payment of ₹9,000 for a safety review. Reason: account emptied in one transfer, large payment at an unusual hour, new recipient. Our team will contact you. Never share your OTP or PIN." |
| Story two, Mule Burst. One account suddenly receives many transfers, fast. ZShield flags the pattern and shows why. This is the account an analyst would want to see early, because stolen money is often moved on through accounts like it. The flag appears while the burst is still happening, not after. | Run the Mule Burst story. Flagged rows appear for the same destination. Point at the reasons. |
| Story three, a Normal Day. Hundreds of honest payments pass in milliseconds. Customers are not slowed down. Most payments are honest, so most of the screen is green. That matters as much as catching the bad ones, because every false alarm costs a real person time and trust. | Run Normal Day. The feed fills with APPROVE rows. |
| Now Meera, our illustrative analyst. She opens the held payment, reads the reasons, and clicks Block. The decision is logged. The AI explains. She decides. One click, and the audit log records her action. | Alert Detail for the Scam Drain payment. Click Block. Status changes to blocked. |

### 2:00-2:30 Architecture and IBM Z (67 words)

| What's said | What's on screen |
|---|---|
| Every payment takes one short path: features, the model, then a decision engine. Everything goes to an audit log. ZShield is designed for IBM Z and deployable on LinuxONE, next to where payments already run, so sensitive data stays put and decisions stay fast. The model is exported to ONNX, so it can move to s390x. We will show exactly what ran on LinuxONE, and nothing more. | Slide 5, then slide 6. Add: [[NEEDS: Vishaal: what actually ran on LinuxONE, with screenshot]] and [[NEEDS: p95 latency on LinuxONE from Vishaal/Abhinava]]. |

### 2:30-3:00 Responsible AI and impact (61 words)

| What's said | What's on screen |
|---|---|
| The GenAI only rephrases checked facts, with a template fallback. If scoring fails, ZShield steps up, and never silently approves. Every decision is logged, and we state our limits openly: the data is synthetic, and real-world results are unknown. In our demo run, value intercepted was [[NEEDS: value intercepted from demo run]]. Score every payment, stop it before settlement, keep a human in control. Thank you. | Slide 9, then the Impact page of the dashboard. Last frame: slide 1 problem line or team names. |

## Backup version (60 seconds, 132 words)

Use when the live demo fails. Play the backup clip and show the audit log. Do not apologise for long. Say it once and move on.

| What's said | What's on screen |
|---|---|
| The live feed is not responding, so here is the recording. In 2025, 28 lakh digital payment frauds were reported in India, and the Reserve Bank says recovery becomes limited once payments are instant. ZShield decides before settlement. In this clip, a 2 AM payment of the whole balance to a new recipient is held. The alert is plain language and the analyst clicks Block. Honest payments pass in milliseconds, so customers are not slowed down. Here is the audit log. Every decision is stored with its score, reasons, alert text, the time it took, and the analyst action. Nothing is silent. If scoring ever fails, the payment gets an extra check, never a quiet approval. ZShield is designed for IBM Z and deployable on LinuxONE. The AI explains. A human decides. | Backup clip (Armaan, docs/screenshots/ or the shared drive). Then the audit log: `GET /alerts` in the browser, or the Alert Detail history. Close on slide 9. |

## Pre-flight checklist

- [ ] API running with ONE worker: `uvicorn api.main:app --port 8000`.
- [ ] `GET /health` shows `"scorer"`. Say aloud which scorer: `onnx` is the real model, `placeholder_rule` is the stand-in. Do not call placeholder numbers model results.
- [ ] `POST /admin/reset` before each story replay. Without it, replays return old decisions and "New recipient" no longer fires.
- [ ] Dashboard open (`streamlit run dashboard/app.py`) and pointing at the API.
- [ ] Demo stream file in place (`data/demo_stream.csv`) and the three stories tested in order: Scam Drain, Mule Burst, Normal Day.
- [ ] Alert provider is the default template (no `GENAI_PROVIDER` set), so no network is needed. If using watsonx.ai Granite, test it first. Fallback to template is automatic.
- [ ] Backup clip downloaded locally. Audit log page ready in a tab.
- [ ] Placeholders replaced in the deck (PR-AUC, p95 latency, value intercepted, LinuxONE evidence). If any is missing, say "not measured yet" instead of guessing.
- [ ] Time the run with a stopwatch once. Target 3:00.
