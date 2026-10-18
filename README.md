# ZShield

Real-time AI that stops fraudulent payments before the money leaves.
IBM Z Datathon 2026, Challenge 1: Real-Time AI for Critical Decisions.

## The problem
TODO (Arun): 3 to 4 sentences plus one verified statistic with its source.

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
TODO (Arun): link docs/responsible_ai.md

## Data
Synthetic transactions (PaySim). No real personal data. See features/data_card.md.

## Team
Vishaal (lead, IBM Z), Balaa (data), Joshua (ML), Abhinava (backend), Armaan (dashboard), Arun (GenAI, story)

## Git rules
- One branch per person: name/feature (example: joshua/train-model)
- Small commits, clear messages
- Open a pull request into main. Vishaal merges.
- Never commit data files, keys, or passwords
