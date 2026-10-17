# Handoffs (drafts for Arun to send on WhatsApp)

These are drafts. Arun sends them. Paths are on branch `arun/genai`, which is local until Arun pushes it.

---

## To Abhinava (GenAI function)

Hi Abhinava, the GenAI module is ready in `genai/` (branch arun/genai). No change is needed for it to work: your import `from genai.explain import generate_alert, template_alert` still works, and 18/18 api tests pass with it.

How to call:
- `generate_alert(facts) -> str`: customer alert, 40 words max. Returns "" for APPROVE.
- `analyst_summary(facts) -> str`: exactly 3 lines (what happened / why flagged / action).
- `facts` = `{"txn_id", "amount", "type", "decision", "risk_score", "reasons"}`. Any extra keys are dropped. Never pass nameOrig or nameDest; they'd be ignored anyway.

One small ask: in `api/main.py` line 128 you pass only decision, amount and reasons. Please also add `"txn_id": txn.txn_id, "type": data["type"], "risk_score": s`, so the summary shows type and score and fallback logs carry the txn id.

Fallback: the default is `GENAI_PROVIDER=template`, which needs no keys or network. If we switch on watsonx or openai_compat, any timeout (GENAI_TIMEOUT_S, default 2 s), error or failed output check returns the template text and logs a warning on `zshield.genai`. Neither function ever raises.

Optional, needs Vishaal's OK since it changes the contract: add `analyst_summary` as an extra field on `/alerts` for the Alert Detail page.

Tests: `python -m pytest genai/tests -q` (49 pass, offline). Details are in `genai/README.md`.

---

## To Armaan (Under the Hood copy and alert text)

Hi Armaan, here's the copy for the dashboard.

Responsible AI (Under the Hood page), 6 bullets, 42 words:
- Synthetic data only. No names or demographics.
- Every flagged payment shows its reasons.
- A person decides on held payments.
- GenAI only rephrases facts. Checked, with fallback.
- If scoring fails, we step up, never silently approve.
- Every decision is logged. Limits stated openly.

Alert copy (this is the exact text the code produces; amounts are synthetic PaySim values shown with ₹):
- HOLD: "We paused a payment of ₹9,000 for a safety review. Reason: account emptied in one transfer, large payment at an unusual hour, new recipient. Our team will contact you. Never share your OTP or PIN."
- STEP_UP: "Please confirm this payment of ₹4,200 in your app. We noticed: new recipient, rapid repeat payments from this account. If someone asked you to send this, stop and call your bank."

Please show `alert_text` from the API as it comes; don't retype it. Can you send me by 4 PM: screenshots of Live Feed, Alert Detail (the Scam Drain HOLD with the Block button) and Impact, saved to `docs/screenshots/`? The demo script is in `docs/deck/demo_script.md`, with a 60 s backup version for your backup clip.

---

## To Vishaal (deck review and abstract question)

Hi Vishaal, the deck draft is in `docs/deck/ZShield_deck_draft.pptx` (storyline in `docs/deck/storyline.md`; rebuild with `python docs/deck/build_deck.py`).

Can you review slide 6 (Why IBM Z)? It only says "designed for / deployable on" IBM Z / LinuxONE. It also says Telum-class processors include on-chip AI acceleration and that ZShield is "designed to use it". Please check that wording, and tell me exactly what ran on LinuxONE (with a screenshot and p95 latency), and I'll update it.

Two questions:
1. Does the portal require an abstract? If yes, what's the word limit? Drafts at about 100, 150 and 250 words are in `docs/abstract/abstract_draft.md`.
2. The architecture diagram for slide 5: are you doing it, or should I?

Also: I filled the two README sections marked for me (problem and responsible AI) on my branch.

---

## To Joshua (fairness template and charts)

Hi Joshua, the fairness and robustness template is in `docs/fairness_robustness_template.md`. Every `[[NEEDS: ...]]` is a blank for your real numbers: FP rate and miss rate by transaction type and by amount band (with n and n_fraud), early vs late step drift (PSI or KS), and a plain-language line on the biggest gaps. I need it filled by 5:30 PM.

Charts I need by 4 PM for the deck:
1. PR curve, model vs logistic regression baseline
2. Confusion matrix (test split)
3. SHAP summary plot
4. Latency table (p50/p95/p99, with the machine named)

Numbers too: PR-AUC (model and baseline), recall at your fixed FPR, and the two-sentence threshold logic.

One format note for your reason strings (`explain_top3`): keep each one short (80 characters max), with no digits and none of the words approve, block, safe, refund or complete. Otherwise the GenAI safety filter swaps it for "Unusual activity". Example of a good one: "Account emptied in one transfer".

---

## To Balaa (EDA charts and methodology text)

Hi Balaa, for the deck I need these by 4 PM:
1. EDA charts in `docs/eda/`: class balance, fraud by transaction type, amount distribution, activity over time (step). One clear chart for slide 7 is the minimum.
2. The one-page data methodology text: source, size, fraud rate, time split by step, leakage prevention, class imbalance, limits.
3. Please confirm from the EDA whether fraud appears only in TRANSFER and CASH_OUT. The fairness template marks this as unconfirmed.
4. Amount band edges for the fairness table (for example from quantiles); agree them with Joshua.

Also, is `demo_stream.csv` and the three story files on track? The demo script depends on them.

---

## To the team group (problem, personas, stats)

Problem statement (use this exact line in the deck):
"How can we score every payment as it happens, stop the dangerous ones before settlement, explain the decision in plain language, and keep a human in control, without blocking honest customers?"

Personas (illustrative composites, not real people), in `docs/problem/personas.md`:
1. Meera, a bank fraud analyst drowning in false alerts. Maps to all stories and the Block click.
2. Kamla, 68, a first-time UPI user targeted by a scam. Maps to Scam Drain.
3. "The Caller", the fraudster who targets Kamla. Relies on speed, irreversibility and late alerts. ZShield holds the drain payment and flags the mule burst. Maps to Scam Drain and Mule Burst.

Verified stats (each re-checked on its source page on 17 Oct; full quotes in `docs/problem/stats.md`):
1. Opener: in 2025, 28 lakh digital payment frauds worth ₹22,931 crore were reported on NCRP. RBI says "the scope for timely intervention and recovery of funds becomes limited". (RBI Discussion Paper, 9 Apr 2026)
2. More than ₹11,158 crore saved in more than 32.80 lakh complaints through CFCFRMS, till 30.06.2026. (PIB/MHA, 21 Jul 2026)
3. UPI: 2,366 crore transactions in July 2026. (PIB, 24 Aug 2026, figures from NPCI)
4. Card/internet frauds: 13,516 cases in 2024-25, 56.5% of all bank fraud cases by number. (RBI Annual Report 2024-25)
5. Cyber fraud amount reported: ₹22,845.73 crore in 2024, up from ₹7,465.18 crore in 2023. (MHA, Lok Sabha reply, 2 Dec 2025)

Say "reported", not "lost". Different releases give different 2024 numbers, so never mix them on one slide.
