# ZShield abstract (draft)

**Vishaal to confirm whether the portal requires an abstract and its word limit.**

Every sentence describes what exists in the repo today. Work still in progress is listed in `docs/TODO.md`, with the sentences to add once it is done. Counts exclude headings.

## Short (about 100 words): 93 words

Instant payments cannot be called back. In 2025, 28 lakh digital payment frauds were reported on India's cybercrime portal (RBI, April 2026). ZShield scores each payment as it arrives and routes it before settlement to APPROVE, STEP_UP (an extra check) or HOLD (a human analyst). Flagged payments come with plain reasons and a checked, plain-language alert. The AI explains and a person decides. ZShield is designed for IBM Z / LinuxONE. In a laptop test, it scored 5,000 payments with a p95 of 3.2 ms. Data is synthetic, and every decision is logged.

## Medium (about 150 words): 143 words

Instant payments cannot be called back. In 2025, 28 lakh digital payment frauds were reported on India's National Cyber Crime Reporting Portal (RBI discussion paper, April 2026). ZShield is a FastAPI service that scores every payment as it arrives, using features built only from the payment and past events. It routes each payment before settlement to APPROVE, STEP_UP (a warning, OTP or call-back) or HOLD (paused for a human analyst). Flagged payments show up to three reasons and a short alert from fixed templates, and every word of every alert is checked. If scoring fails, the result is STEP_UP. Every decision and analyst action goes to an audit log. ZShield is designed for IBM Z / LinuxONE, to decide inside the payment flow. In a laptop test with our rule-based scorer, it handled 375 payments per second with a p95 of 3.2 ms.

## Long (about 250 words): 252 words

Instant payments cannot be called back. In 2025, 28 lakh digital payment frauds were reported on India's National Cyber Crime Reporting Portal, worth ₹22,931 crore (RBI discussion paper, 9 April 2026). The RBI notes that the scope for timely intervention and recovery of funds becomes limited. Checks after settlement come too late, and customers see blocks with no explanation.

ZShield scores every payment as it happens. A FastAPI service builds features from the payment and from past events only, scores it, and routes it before settlement to APPROVE, STEP_UP (a plain warning, OTP or call-back) or HOLD (paused for a human analyst). Flagged payments come with up to three plain reasons and a short customer alert. Alerts come from fixed templates. Every word is checked against the facts, and the alert can never change a decision. If scoring fails, the result is STEP_UP, never a silent approve. Every decision is written to an audit log, and an analyst can approve, block or escalate each held payment through the API.

We use synthetic PaySim-format data, with no names or demographics. In a replay of 252 sample payments, both full-drain payments were held, a burst of payments into one account was flagged, and 245 payments went straight through. In a laptop load test, ZShield scored 5,000 payments with a p95 of 3.2 ms and 375 payments per second.

ZShield is designed for IBM Z / LinuxONE, to decide inside the payment flow, before settlement. Limits: the data is synthetic, and real-world performance is unknown.
