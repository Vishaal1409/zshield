# ZShield deck storyline (draft)

IBM Z Datathon 2026, Challenge 1: Real-Time AI for Critical Decisions. Owner: Arun. Draft of Sat 17 Oct 2026.

Rules for this deck: only the verified stats in `docs/problem/stats.md`; no model results yet (placeholders only); IBM Z wording is "designed for / deployable on" until Vishaal confirms what ran; personas are illustrative; the AI explains, a human decides.

`docs/deck/build_deck.py` reads this file. Keep the field names (`**Headline:**`, `**Bullets:**`, and so on) unchanged.

---

## Slide 1: Problem

**Headline:** Instant payments leave almost no time to stop a scam.
**Bullets:**
- In 2025, 28 lakh digital payment frauds were reported on the National Cyber Crime Reporting Portal, worth ₹22,931 crore.
- The RBI says the "scope for timely intervention and recovery of funds becomes limited".
- Checks that run after settlement come too late.
**Problem line:** How can we score every payment as it happens, stop the dangerous ones before settlement, explain the decision in plain language, and keep a human in control, without blocking honest customers?
**Small:** Source: Reserve Bank of India, "Discussion Paper - Exploring safeguards in digital payments to curb frauds", 9 Apr 2026. Figures are frauds reported on NCRP, not confirmed losses.
**Box:** PLACEHOLDER: stat card, NCRP frauds reported 2021 to 2025, from the RBI table only (Arun, by 4 PM)
**Visual:** Stat card: bar chart of the RBI table (2.6 lakh in 2021 up to 28 lakh in 2025) with the opener quote. Use only that one table. Do not add the MHA or PIB 2024 numbers.
**Supplier:** Arun
**Notes:** Open with the stat and say "reported", not "lost". Then read the problem line slowly. It is the question the rest of the deck answers.

---

## Slide 2: Insight

**Headline:** The decision must happen before settlement, and a score alone is not enough.
**Bullets:**
- Before settlement: after the money moves, recovery is limited.
- With reasons: Meera, the analyst, needs to know why a payment is different, not just a number.
- With a human in control: Kamla, a first-time UPI user, should not be blocked without a reason. The Caller relies on speed.
**Small:** Meera, Kamla and The Caller are illustrative composites, not real people. Source for the recovery point: RBI discussion paper, 9 Apr 2026.
**Box:** PLACEHOLDER: three persona cards, Meera / Kamla / The Caller, marked "illustrative" (Arun, by 4 PM)
**Visual:** Three persona cards, each with one line of pain point and one line of what changes. Text from `docs/problem/personas.md`.
**Supplier:** Arun
**Notes:** The insight has three parts: timing, reasons, human control. Say the personas are illustrative. Keep The Caller at the level of public scam patterns, no method.

---

## Slide 3: Solution

**Headline:** ZShield scores every payment in milliseconds and sends it to APPROVE, STEP_UP or HOLD.
**Bullets:**
- APPROVE: pass straight through. STEP_UP: an extra check (warning, OTP or call-back). HOLD: paused for a human analyst.
- Flagged payments get the top 3 reasons and a plain-language alert.
- The AI explains. A human decides. If scoring fails, the result is STEP_UP, never a silent approve.
**Small:** Alert text is made from fixed templates by default. A language model is optional, and every output is checked.
**Box:** PLACEHOLDER: three-lane routing graphic, APPROVE / STEP_UP / HOLD (Arun, by 4 PM)
**Visual:** One graphic: a payment enters, a score appears, three lanes. HOLD lane ends at "analyst: Approve, Block or Escalate".
**Supplier:** Arun
**Notes:** Explain the three lanes in one breath. Stress that STEP_UP is the middle path that protects honest customers. The GenAI never makes or changes a decision.

---

## Slide 4: Live demo

**Headline:** Three stories show the system working: a drain is held, a burst is flagged, a normal day flows.
**Bullets:**
- Scam Drain: at 2 AM the whole balance goes to a brand-new recipient. Result: HOLD.
- Mule Burst: one destination receives many transfers fast. Result: flagged.
- Normal Day: hundreds of honest payments pass in milliseconds. Then the analyst clicks Block.
**Small:** Scam Drain alert text, as produced by the code: "We paused a payment of ₹9,000 for a safety review. Reason: account emptied in one transfer, large payment at an unusual hour, new recipient. Our team will contact you. Never share your OTP or PIN."
**Box:** PLACEHOLDER: dashboard screenshots, Live Feed and Alert Detail with the Scam Drain HOLD (Armaan, by 4 PM)
**Visual:** Two screenshots: Live Feed during Normal Day, and Alert Detail for the held Scam Drain payment with the Block button.
**Supplier:** Armaan (docs/screenshots/)
**Notes:** Run the demo live. If it fails, play the backup clip and show the audit log. Replay each story after a reset so decisions are fresh. Full wording is in demo_script.md.

---

## Slide 5: Architecture

**Headline:** One short path from payment to decision, with every step logged.
**Bullets:**
- Stream, then POST /score, live features, ONNX model, decision engine.
- Flagged payments get reasons and an alert. Every decision goes to an audit log, then the dashboard.
- If any step fails, the result is STEP_UP and the error is stored.
**Small:** The backend latency measured so far is from a placeholder rule scorer, not the real model.
**Box:** PLACEHOLDER: architecture diagram, stream to dashboard, with the GenAI step and fail-safe marked (Vishaal, by 4 PM)
**Visual:** Block diagram: stream, FastAPI /score, live features, ONNX model, decision engine, audit log (SQLite), dashboard (Streamlit). GenAI alert branch off the decision engine.
**Supplier:** Vishaal (diagram), Arun (labels)
**Notes:** Walk the path left to right. Point out that the GenAI sits after the decision and cannot change it. Mention the fail-safe once.

---

## Slide 6: Why IBM Z

**Headline:** ZShield is designed for IBM Z and deployable on LinuxONE, next to where payments already run.
**Bullets:**
- Core payments already run on IBM Z. Scoring next to the transaction avoids moving sensitive data across networks.
- Low, predictable latency matters before settlement. Telum-class processors include on-chip AI acceleration for in-transaction inference. ZShield is designed to use it.
- ONNX keeps the model portable to s390x. IBM Z security and reliability match our responsible-AI design.
**Small:** Scale: UPI recorded 2,366 crore transactions in July 2026 (PIB, key statistics attributed to NPCI). This is context, not a benchmark of ours.
**Box:** PLACEHOLDER: [[NEEDS: Vishaal: what actually ran on LinuxONE, with screenshot]]
**Visual:** Screenshot of /health and a /score call on LinuxONE, plus one line stating exactly what ran. If nothing ran, keep the "designed for / deployable on" wording and say so.
**Supplier:** Vishaal
**Notes:** Use "designed for" and "deployable on". Do not say we used the on-chip accelerator unless Vishaal confirms it. If LinuxONE ran the API, say exactly that and show the screenshot.

---

## Slide 7: Data and method

**Headline:** We test the way a bank would: time-based split, no leakage, and honest metrics.
**Bullets:**
- PaySim synthetic payments (Kaggle). No real personal data. Split by time (step), no leakage.
- Class weights for rare fraud. Metrics: PR-AUC and recall at a fixed false-positive rate. No accuracy.
- Logistic regression baseline. Thresholds set by cost: a missed fraud costs more than an extra check.
**Small:** PaySim is synthetic and relatively easy, so real-world performance is unknown.
**Box:** PLACEHOLDER: EDA chart, fraud by type and over time (Balaa, docs/eda/, by 4 PM)
**Visual:** One EDA chart that shows how rare fraud is and which transaction types carry it.
**Supplier:** Balaa
**Notes:** Say why accuracy is misleading when fraud is rare. Say the baseline exists so the boosted-tree model has to earn its place. Name the limit: synthetic data.

---

## Slide 8: Results

**Headline:** We report ranking quality, catch rate at a fixed false-alarm rate, and latency, all measured, none assumed.
**Bullets:**
- PR-AUC: [[NEEDS: PR-AUC from Joshua]] against baseline [[NEEDS: baseline PR-AUC from Joshua]].
- Recall at fixed FPR: [[NEEDS: recall at fixed FPR from Joshua]]. Confusion matrix and SHAP summary: [[NEEDS: charts from Joshua]].
- Latency: p95 [[NEEDS: p95 latency on LinuxONE from Vishaal/Abhinava]].
**Small:** Honest note: the backend latency measured so far comes from a placeholder rule scorer on x86, not the real model and not IBM Z. We do not quote it as a result.
**Box:** PLACEHOLDER: PR curve, model vs baseline; confusion matrix; SHAP summary; latency table (Joshua, by 4 PM)
**Visual:** Four items: PR curve against the baseline, confusion matrix, SHAP summary, latency table labelled with the machine.
**Supplier:** Joshua (charts), Abhinava and Vishaal (latency table)
**Notes:** Fill every number from a real run and label the machine. If the real model is not in by the deadline, say so on this slide. Never show the placeholder scorer's numbers as model results.

---

## Slide 9: Responsible AI

**Headline:** The AI explains and a human decides, and every limit is stated.
**Bullets:**
- Synthetic data only. No names or demographics. Every flagged payment shows its reasons.
- GenAI only rephrases facts we give it. Output is checked, with a template fallback. It cannot change a decision.
- Fail-safe to STEP_UP. Every decision is logged. Fairness is checked by type and amount band: [[NEEDS: fairness numbers from Joshua]].
**Small:** Status: validator, fail-safe and audit log are built. SHAP reasons and the fairness table are pending. See docs/responsible_ai.md.
**Box:** PLACEHOLDER: responsible-AI checklist graphic and fairness table (Arun graphic; Joshua numbers, by 4 PM)
**Visual:** Six icons for the six short-version bullets, plus the fairness table when Joshua's numbers arrive.
**Supplier:** Arun (graphic), Joshua (numbers)
**Notes:** Say what is built and what is pending. Name the limits: synthetic data, drift, fraudsters adapt, fairness checked only through proxies. Honesty here is a strength.

---

## Slide 10: Impact and next steps

**Headline:** Stopping a payment before settlement is the point where a scam can still be undone.
**Bullets:**
- In our demo run, value intercepted: [[NEEDS: value intercepted from demo run]]. It excludes payments an analyst approved.
- After-the-fact freezing helps: more than ₹11,158 crore saved in more than 32.80 lakh complaints (till 30.06.2026). ZShield acts earlier.
- Next: real model on LinuxONE, SHAP reasons, pilot with real review queues, drift monitoring.
**Small:** Source: PIB, MHA, "National Cyber Crime Data", 21 Jul 2026. "Saved" and "reported" cover different periods. We do not compute a recovery rate.
**Box:** PLACEHOLDER: impact panel, demo-run counts and value intercepted from /stats (Armaan, by 4 PM)
**Visual:** Dashboard Impact page screenshot.
**Supplier:** Armaan
**Notes:** Quote the demo number only from the real run. Do not say this recovers money at any rate. Close on the problem line: score, stop, explain, keep a human in control.

---

## Sources

- Stat 2 (opener): RBI, "Discussion Paper - Exploring safeguards in digital payments to curb frauds", 9 Apr 2026. https://www.rbi.org.in/Scripts/PublicationsView.aspx?id=23810 (accessed 2026-10-17)
- Stat 4 (slide 10): PIB / MHA, "National Cyber Crime Data", 21 Jul 2026. https://www.pib.gov.in/PressReleasePage.aspx?PRID=2287039&reg=48&lang=2 (accessed 2026-10-17)
- Stat 5 (slide 6): PIB, "UPI Completes 10 Years of Digital Payments Revolution", 24 Aug 2026, key statistics attributed to NPCI. https://www.pib.gov.in/PressReleasePage.aspx?PRID=2302657&reg=48&lang=2 (accessed 2026-10-17)
- Persona 3 reference: PIB (MHA), alert on "Digital Arrest" scams, 14 May 2024. https://www.pib.gov.in/PressReleasePage.aspx?PRID=2020570 (accessed 2026-10-17)
- Not used on slides: Stat 1 (RBI Annual Report 2024-25) and Stat 3 (MHA, Lok Sabha, 2 Dec 2025). Their 2024 numbers differ from other cuts and must not be mixed with the opener.
- Units: lakh = 100,000; crore = 10 million. Figures are "reported", not confirmed losses.

## Placeholders to fill

- [ ] PR-AUC, model and baseline: Joshua
- [ ] Recall at fixed FPR: Joshua
- [ ] PR curve, confusion matrix, SHAP summary charts: Joshua
- [ ] Fairness numbers by type and amount band: Joshua (band definitions: Balaa)
- [ ] p95 latency on LinuxONE (and the machine label): Vishaal / Abhinava
- [ ] What actually ran on LinuxONE, with screenshot: Vishaal
- [ ] Architecture diagram: Vishaal
- [ ] EDA chart in docs/eda/: Balaa
- [ ] Dashboard screenshots in docs/screenshots/ (Live Feed, Alert Detail, Impact): Armaan
- [ ] Value intercepted from the demo run: Armaan / Abhinava (from /stats after the real run)
- [ ] Stat card, persona cards, routing graphic, responsible-AI graphic: Arun
- [ ] Confirm the release date of the RBI Annual Report if Stat 1 is ever quoted: Vishaal
