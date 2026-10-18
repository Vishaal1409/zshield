# ZShield deck storyline (draft)

IBM Z Datathon 2026, Challenge 1: Real-Time AI for Critical Decisions. Owner: Arun. Draft of Sun 18 Oct 2026.

Rule for this deck: every line describes something that exists in the repo today or a verified source. Work that is still in progress is not mentioned. It is listed in `docs/TODO.md` with the text to add once it is done. Personas are illustrative.

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
**Box:** VISUAL: stat card, NCRP frauds reported 2021 to 2025, from the RBI table (Arun)
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
**Box:** VISUAL: three persona cards, Meera / Kamla / The Caller, marked "illustrative" (Arun)
**Visual:** Three persona cards, each with one line of pain point and one line of what changes. Text from `docs/problem/personas.md`.
**Supplier:** Arun
**Notes:** The insight has three parts: timing, reasons, human control. Say the personas are illustrative. Keep The Caller at the level of public scam patterns, no method.

---

## Slide 3: Solution

**Headline:** ZShield scores every payment in milliseconds and sends it to APPROVE, STEP_UP or HOLD.
**Bullets:**
- APPROVE: pass straight through. STEP_UP: an extra check (warning, OTP or call-back). HOLD: paused for a human analyst.
- Flagged payments get up to 3 plain reasons and a short customer alert.
- The AI explains. A human decides. If scoring fails, the result is STEP_UP, never a silent approve.
**Small:** The score and the reasons come from a rule-based scorer. Alerts come from fixed templates, and every alert is checked before it is used.
**Box:** VISUAL: three-lane routing graphic, APPROVE / STEP_UP / HOLD (Arun)
**Visual:** One graphic: a payment enters, a score appears, three lanes. HOLD lane ends at "analyst: Approve, Block or Escalate".
**Supplier:** Arun
**Notes:** Explain the three lanes in one breath. Stress that STEP_UP is the middle path that protects honest customers. The alert text never makes or changes a decision.

---

## Slide 4: Live demo

**Headline:** Three stories in one replay: a drain is held, a burst is flagged, a normal day flows.
**Bullets:**
- Scam Drain: at 2 AM, ₹48,000, the whole balance, goes to a brand-new recipient. Result: HOLD. The analyst blocks it.
- Mule Burst: ten payers send money to one account. From the sixth transfer on, each one is STEP_UP.
- Normal Day: 245 of 252 payments are approved with no extra step.
**Small:** Alert text for the held payment, as produced: "We paused a payment of ₹48,000 for a safety review. Reason: account emptied in one transfer, new recipient, large payment at an unusual hour. Our team will contact you. Never share your OTP or PIN." Data: the synthetic sample stream in the repo (docs/samples/sample_stream.csv).
**Box:** VISUAL: screenshot of the dashboard after the replay, with the two HOLD rows (Arun)
**Visual:** Screenshot of the current dashboard (Processed, Flagged, Value intercepted, Avg latency, and the flagged table with alert text and analyst status BLOCK).
**Supplier:** Arun
**Notes:** Run the replay live with the producer. Block the held payment from the API docs page, then show BLOCK in the dashboard table. If anything fails, show the audit log in /alerts. Full wording is in demo_script.md.

---

## Slide 5: Architecture

**Headline:** One short path from payment to decision, with every step logged.
**Bullets:**
- Stream (producer.py), then POST /score, live features, scorer, decision engine.
- Flagged payments get reasons and an alert. Every decision goes to a SQLite audit log, then the dashboard.
- If scoring fails, the result is STEP_UP and the error is stored.
**Small:** Live features use the payment itself and past events only. The API also loads an ONNX model file when one is provided (tested with a stand-in model).
**Box:** VISUAL: architecture diagram as built, stream to dashboard, with the alert step and fail-safe marked (Arun)
**Visual:** Block diagram: producer.py, FastAPI /score, live features (state store), scorer, decision engine, alert text (flagged only), audit log (SQLite), dashboard (Streamlit), analyst action (POST /analyst_action).
**Supplier:** Arun
**Notes:** Walk the path left to right. Point out that the alert step sits after the decision and cannot change it. Mention the fail-safe once.

---

## Slide 6: Why IBM Z

**Headline:** ZShield is designed for IBM Z / LinuxONE: decide inside the payment flow, before settlement.
**Bullets:**
- Designed to score next to the transaction, so sensitive payment data does not travel to an outside ML server.
- The decision step is small and fast: about 0.04 ms per payment in our laptop test.
- The scoring service needs only a short list of Python packages (requirements-api.txt).
**Small:** Scale: UPI recorded 2,366 crore transactions in July 2026 (PIB, key statistics attributed to NPCI). This is context, not a benchmark of ours. Laptop test: Intel i7, x86, rule-based scorer.
**Box:** VISUAL: diagram of ZShield inside the payment flow on IBM Z / LinuxONE, labelled "design" (Arun)
**Visual:** Simple diagram: payment switch, ZShield scoring step, settlement. Label it "design".
**Supplier:** Arun
**Notes:** Say "designed for". Do not say it runs on IBM Z or uses any IBM Z accelerator. The laptop number is a laptop number.

---

## Slide 7: Data and features

**Headline:** Synthetic payments, and features built only from what is known at the moment of payment.
**Bullets:**
- PaySim-format synthetic data. No real customers, names or demographics.
- Features: balance mismatches, amount-to-balance ratio, full-drain flag, hour of day, payment type, new recipient.
- History features from past events only: sender's recent payments and recipient's recent inbound payments.
**Small:** PaySim is synthetic and relatively easy, so real-world performance is unknown. Code: features/features.py and api/state.py.
**Box:** VISUAL: feature table, name and plain meaning (Arun)
**Visual:** A two-column table of the features listed on this slide, from features/features.py and api/state.py.
**Supplier:** Arun
**Notes:** Stress "past events only": the current payment is added to history after its features are computed, so nothing leaks from the future.

---

## Slide 8: Results

**Headline:** Measured so far: decisions in milliseconds, and both drain payments held.
**Bullets:**
- Load test, 5,000 payments, 0 errors: p95 3.2 ms end to end; 375 payments per second one at a time, 718 with 8 clients.
- Sample replay, 252 payments: 245 approved, 5 STEP_UP, 2 HOLD. Both full-drain payments were held.
- Alert safety: 119 offline tests pass; 25,664 template cases checked with no false rejection.
**Small:** Measured 17 Oct 2026 on a laptop (Intel i7, x86) with the rule-based scorer, not on IBM Z. Tables: docs/deck/measured_17oct.md.
**Box:** VISUAL: latency and throughput table from docs/deck/measured_17oct.md (Arun)
**Visual:** Table: p50, p95, p99 end to end and inside the API, for 1 and 8 clients, with the machine named.
**Supplier:** Arun
**Notes:** Name the machine and the scorer every time you quote a number. These are pipeline numbers, not fraud-detection accuracy.

---

## Slide 9: Responsible AI

**Headline:** The AI explains and a human decides, and every limit is stated.
**Bullets:**
- Synthetic data only. No names or demographics. Every flagged payment shows its reasons.
- Alert text only rephrases facts we give it. Every word is checked, with a template fallback. It cannot change a decision.
- Fail-safe to STEP_UP. Every decision and analyst action is logged.
**Small:** See docs/responsible_ai.md. Limits: synthetic data, drift over time, fraudsters adapt.
**Box:** VISUAL: six-point responsible-AI checklist graphic (Arun)
**Visual:** Six icons for the six short-version bullets in docs/responsible_ai.md.
**Supplier:** Arun
**Notes:** Say what each point is and where a judge can see it in the repo. Name the limits plainly. Honesty here is a strength.

---

## Slide 10: Impact

**Headline:** Stopping a payment before settlement is the point where a scam can still be undone.
**Bullets:**
- In the sample replay, ₹79,500 in two drain payments was held before settlement.
- Honest customers: 245 of 252 payments went through with no extra step.
- Reporting after the fact still saves some money: more than ₹11,158 crore saved in more than 32.80 lakh complaints (till 30.06.2026). ZShield acts earlier.
**Small:** Replay amounts are synthetic. Source for the national figure: PIB, MHA, "National Cyber Crime Data", 21 Jul 2026. "Saved" covers complaints till 30.06.2026; we do not compute a recovery rate.
**Box:** VISUAL: impact panel, the dashboard's Value intercepted and Processed tiles after the replay (Arun)
**Visual:** Crop of the dashboard tiles after the sample replay.
**Supplier:** Arun
**Notes:** Quote only the replay numbers and the sourced figure. Close on the problem line: score, stop, explain, keep a human in control.

---

## Sources

- Stat 2 (opener): RBI, "Discussion Paper - Exploring safeguards in digital payments to curb frauds", 9 Apr 2026. https://www.rbi.org.in/Scripts/PublicationsView.aspx?id=23810 (accessed 2026-10-17)
- Stat 4 (slide 10): PIB / MHA, "National Cyber Crime Data", 21 Jul 2026. https://www.pib.gov.in/PressReleasePage.aspx?PRID=2287039&reg=48&lang=2 (accessed 2026-10-17)
- Stat 5 (slide 6): PIB, "UPI Completes 10 Years of Digital Payments Revolution", 24 Aug 2026, key statistics attributed to NPCI. https://www.pib.gov.in/PressReleasePage.aspx?PRID=2302657&reg=48&lang=2 (accessed 2026-10-17)
- Persona 3 reference: PIB (MHA), alert on "Digital Arrest" scams, 14 May 2024. https://www.pib.gov.in/PressReleasePage.aspx?PRID=2020570 (accessed 2026-10-17)
- Our measurements (slides 4, 6, 8, 10): docs/deck/measured_17oct.md, 17 Oct 2026, laptop (Intel i7, x86), rule-based scorer, synthetic sample stream.
- Units: lakh = 100,000; crore = 10 million. Figures are "reported", not confirmed losses.
