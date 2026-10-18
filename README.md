# ZShield

Real-time AI that stops fraudulent payments before the money leaves.
IBM Z Datathon 2026, Challenge 1: Real-Time AI for Critical Decisions.

## The problem
Instant payments cannot be called back. In its April 2026 discussion paper, the Reserve Bank of India says that because of the instantaneous nature of payments, "the scope for timely intervention and recovery of funds becomes limited" ([RBI, 9 Apr 2026](https://www.rbi.org.in/Scripts/PublicationsView.aspx?id=23810)). The same paper shows 28 lakh digital payment frauds, worth ₹22,931 crore, reported on the National Cyber Crime Reporting Portal in 2025. Today's checks often act after the money has gone, analysts drown in false alerts, and customers see blocks with no explanation.

> How can we score every payment as it happens, stop the dangerous ones before settlement, explain the decision in plain language, and keep a human in control, without blocking honest customers?

More: [problem statement](docs/problem/problem_statement.md), [personas](docs/problem/personas.md), [sourced statistics](docs/problem/stats.md).

## What it does
Every payment is scored in milliseconds and routed to one of three actions:
APPROVE, STEP_UP (extra check), or HOLD (human analyst). Flagged payments come with
top reasons (SHAP) and a plain-language alert (GenAI). The AI explains, a human decides.

## Architecture
TODO (Vishaal): add diagram to docs/ and link it here.

stream -> POST /score -> live features -> ONNX model -> decision engine -> audit log -> dashboard

## Folder map
| Folder | Contents | Owner |
|---|---|---|
| data/ | Not committed. Local copy of shared data | Balaa |
| features/ | features.py, EDA notebook, data_card.md | Balaa |
| model/ | train.py, explain.py, model.onnx, thresholds.json, model_card.md | Joshua |
| api/ | FastAPI app, decision engine, state store, producer.py | Abhinava |
| genai/ | Prompts, generate_alert(), fallback templates, tests | Arun |
| dashboard/ | Streamlit app | Armaan |
| docs/ | README assets, API contract, responsible AI, deck, screenshots | Vishaal, Arun |

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-api.txt
uvicorn api.main:app --reload --port 8000
# in a second terminal:
curl http://localhost:8000/health
```

Dashboard (standalone synthetic-data prototype):
```bash
pip install -r requirements-dashboard.txt
streamlit run dashboard/app.py
```

Training / EDA environment:
```bash
pip install -r requirements-train.txt
```

## IBM Z / LinuxONE
TODO (Vishaal): what we actually ran on Z, with screenshots. Be exact, do not overclaim.

## Responsible AI
See the [responsible AI checklist](docs/responsible_ai.md). The GenAI alert layer only rephrases supplied facts and never changes a decision: [genai/DESIGN.md](genai/DESIGN.md).

## Data
Synthetic transactions (PaySim, 6.36M rows, 0.13% fraud). No real personal data.
- Data card, splits and limitations: [features/data_card.md](features/data_card.md)
- One-page methodology for the deck: [docs/data_methodology.md](docs/data_methodology.md)
- EDA charts: [docs/eda/](docs/eda/) (notebook: `features/eda.ipynb`)
- Demo stream, 3 demo stories and 10 edge cases: [docs/demo/](docs/demo/)
- Rebuild everything: `python -m features.prepare_data data/paysim.csv` (see [data/README.md](data/README.md))

## Team
Vishaal (lead, IBM Z), Balaa (data), Joshua (ML), Abhinava (backend), Armaan (dashboard), Arun (GenAI, story)

## Git rules
- One branch per person: name/feature (example: joshua/train-model)
- Small commits, clear messages
- Open a pull request into main. Vishaal merges.
- Never commit data files, keys, or passwords
