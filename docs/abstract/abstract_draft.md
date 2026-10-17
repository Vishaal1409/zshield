# ZShield abstract (draft)

**Vishaal to confirm whether the portal requires an abstract and its word limit.**

Results are placeholders until Joshua, Vishaal and Abhinava supply real runs. Counts exclude headings. Each placeholder will add a few words once filled.

## Short (about 100 words): 105 words as written (96 without placeholders)

Instant payments cannot be called back. In 2025, 28 lakh digital payment frauds were reported on India's cybercrime portal (RBI, April 2026). ZShield scores each payment in milliseconds and routes it before settlement to APPROVE, STEP_UP (an extra check) or HOLD (a human analyst). Flagged payments come with reasons and a plain-language alert. The AI explains and a person decides. A boosted-tree model, exported to ONNX, will be served by FastAPI. The system is designed for and deployable on IBM Z / LinuxONE. Data is synthetic and every decision is logged. Result: [[NEEDS: PR-AUC from Joshua]], p95 latency [[NEEDS: p95 latency on LinuxONE from Vishaal/Abhinava]].

## Medium (about 150 words): 155 words as written (141 without placeholders)

Instant payments cannot be called back. In 2025, 28 lakh digital payment frauds were reported on India's National Cyber Crime Reporting Portal (RBI discussion paper, April 2026). ZShield scores every payment in milliseconds with a boosted-tree model, planned as ONNX served by FastAPI (a placeholder rule scorer runs today). It routes each payment before settlement to APPROVE, STEP_UP (a warning, OTP or call-back) or HOLD (paused for a human analyst). Flagged payments show the top three reasons and a short plain-language alert, written from templates by default, or optionally by an IBM watsonx.ai Granite model (integration written, not yet run live), with every output checked. The AI explains and a human decides. If scoring fails, the result is STEP_UP. ZShield is designed for and deployable on IBM Z / LinuxONE, next to where many banks run core payments. Results: [[NEEDS: PR-AUC and recall at fixed FPR from Joshua]]; [[NEEDS: p95 latency on LinuxONE from Vishaal/Abhinava]].

## Long (about 250 words): 260 words as written (241 without placeholders)

Instant payments cannot be called back. In 2025, 28 lakh digital payment frauds were reported on India's National Cyber Crime Reporting Portal, worth ₹22,931 crore (RBI discussion paper, 9 April 2026). The RBI notes that the scope for timely intervention and recovery of funds becomes limited. Checks after settlement come too late, and customers see blocks with no explanation.

ZShield scores every payment as it happens. A boosted-tree model, exported to ONNX and served by FastAPI, will produce a risk score in milliseconds. A decision engine routes the payment before settlement to APPROVE, STEP_UP (a plain warning, OTP or call-back) or HOLD (paused for a human analyst). Flagged payments come with the top three reasons and a short plain-language alert. Alerts come from templates, or optionally from an IBM watsonx.ai Granite model; every output is validated, and the GenAI never changes a decision. If scoring fails, the result is STEP_UP, never a silent approve. Every decision is written to an audit log, and an analyst can approve, block or escalate each held payment (API built; dashboard controls in progress).

We are training on synthetic PaySim data with a time-based split, class weights and a logistic regression baseline. We will report PR-AUC and recall at a fixed false-positive rate, not accuracy. Results: [[NEEDS: PR-AUC and recall at fixed FPR from Joshua]]; [[NEEDS: p95 latency on LinuxONE from Vishaal/Abhinava]]; [[NEEDS: value intercepted from demo run]].

ZShield is designed for and deployable on IBM Z / LinuxONE, where many banks run core payments. Limits: the data is synthetic, and real-world performance is unknown.
