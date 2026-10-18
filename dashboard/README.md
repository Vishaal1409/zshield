# ZShield Dashboard

This Streamlit dashboard reads metrics and transaction rows from the scoring API.

The API URL is set in config.py. It defaults to http://127.0.0.1:8000 and can be changed to the IBM Z server.

From the repository root, start the API with:
uvicorn api.main:app --host 0.0.0.0 --port 8000

From a second terminal at the repository root, start the dashboard with:
python -m streamlit run dashboard/app.py

The API should provide GET /health, GET /stats, GET /alerts, GET /recent, POST /score, and POST /analyst_action. Story CSVs are in docs/demo/story_*.csv. The dashboard posts each story row to /score. Mule Burst is a constructed scenario. Amounts are shown in units, without a currency symbol.