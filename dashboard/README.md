# ZShield dashboard

A Streamlit dashboard prototype for reviewing real-time payment risk decisions. It includes an Overview landing page, Live Feed, Alert Detail, Impact, and Under the Hood views. Navigation stays at the top of the page.

## Run locally

```powershell
cd dashboard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r ..\requirements-dashboard.txt
streamlit run app.py
```

The first run uses local synthetic transactions. Use the demo controls in the left panel to add a Scam Drain, Mule Burst, or Normal Day sequence. Reset restores the initial sample feed.

## Dashboard views

- **Overview:** headline metrics, recent activity, decision mix, and flagged transactions.
- **Live Feed:** scrollable transaction table with decision filters and a decision mix chart.
- **Alert Detail:** risk context, reasons, alert summary, and analyst action controls.
- **Impact:** value and latency charts with evaluation metrics when ground-truth labels are available.
- **Under the Hood:** decision flow, IBM Z rationale, system limits, and responsible AI principles.

## Data and integration

This prototype starts with deterministic, synthetic demo transactions and does not send analyst actions to the repository API. The API is available separately; connecting the dashboard to it is not part of this prototype. See [ASSUMPTIONS.md](ASSUMPTIONS.md) for implementation assumptions.
