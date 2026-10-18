# Assumptions

- The dashboard now reads authoritative metrics from GET /stats, flagged rows from GET /alerts, and recent transactions from GET /recent.
- The dashboard connects to http://127.0.0.1:8000 by default. Change API_BASE_URL in config.py to use another server.
- The local repository API provides /recent and retains the type and account identifiers needed by dashboard tables.
- Story buttons submit every row from docs/demo/story_*.csv to POST /score. Replay IDs are suffixed per run because the API treats duplicate transaction IDs as the original decision.
- Mule Burst is a constructed scenario, not a measured fraud dataset or a claim about production performance.
- PaySim-style amounts have no currency and are shown in units.
- Impact evaluation statistics appear only where returned transaction IDs match the sample label file.
- If the API is unavailable, the dashboard displays the connection error; it does not substitute generated numbers.
- The transaction table remains scrollable, and Plotly charts retain hover, zoom, and pan interactions.