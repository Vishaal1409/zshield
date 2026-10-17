# ZShield: Problem Statement

## The problem line

> How can we score every payment as it happens, stop the dangerous ones before settlement, explain the decision in plain language, and keep a human in control, without blocking honest customers?

## README version (as used in README.md)

Instant payments cannot be called back. In its April 2026 discussion paper, the Reserve Bank of India says that because of the instantaneous nature of payments, "the scope for timely intervention and recovery of funds becomes limited". The same paper shows 28 lakh digital payment frauds, worth ₹22,931 crore, reported on the National Cyber Crime Reporting Portal in 2025. Today's checks often act after the money has gone, analysts drown in false alerts, and customers see blocks with no explanation.

Source for the quote: RBI, "Discussion Paper - Exploring safeguards in digital payments to curb frauds", 9 Apr 2026. See `stats.md`, stat 2.

## Why current checks fail (short list)

- Payments are instant and cannot be reversed in practice.
- Alerts often arrive after the money has gone.
- Analysts face many false alerts and lose time on honest customers.
- Blocks are unexplained, so customers and analysts cannot trust or learn from them.

## What ZShield does

- Scores each payment in milliseconds (FastAPI; a boosted-tree model exported to ONNX is planned, a placeholder rule scores today).
- Routes it to APPROVE, STEP_UP or HOLD before settlement.
- Gives the top 3 reasons (rule-based today; SHAP when the model lands) and a short plain-language alert for flagged payments.
- Keeps the analyst in control: the AI explains, a human decides.
- Designed for, and deployable on, IBM Z / LinuxONE.
