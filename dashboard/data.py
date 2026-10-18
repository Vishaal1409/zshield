from __future__ import annotations
from pathlib import Path
from uuid import uuid4
import httpx
import pandas as pd
from config import API_BASE_URL

class APIError(RuntimeError):
    pass

def _request(method: str, path: str, **kwargs):
    try:
        response = httpx.request(method, f"{API_BASE_URL}{path}", timeout=12.0, **kwargs)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise APIError(f"API {path} returned HTTP {exc.response.status_code}: {exc.response.text[:400]}") from exc
    except httpx.RequestError as exc:
        raise APIError(f"Cannot reach the ZShield API at {API_BASE_URL}: {exc}") from exc
    try:
        return response.json()
    except ValueError as exc:
        raise APIError(f"API {path} did not return valid JSON.") from exc

def api_health() -> dict:
    value = _request("GET", "/health")
    if not isinstance(value, dict):
        raise APIError("API /health returned an unexpected response.")
    return value

def fetch_stats() -> dict:
    value = _request("GET", "/stats")
    if not isinstance(value, dict):
        raise APIError("API /stats returned an unexpected response.")
    return value

def _rows(payload, endpoint: str) -> list[dict]:
    rows = payload if isinstance(payload, list) else payload.get("items", payload.get(endpoint, [])) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        raise APIError(f"API /{endpoint} did not return a list of rows.")
    return [row for row in rows if isinstance(row, dict)]

def _frame(payload, endpoint: str) -> pd.DataFrame:
    df = pd.DataFrame(_rows(payload, endpoint))
    for target, source in {"timestamp": "ts", "created_at": "ts", "transaction_id": "txn_id", "transaction_type": "type"}.items():
        if target not in df.columns and source in df.columns:
            df[target] = df[source]
    if "time" not in df.columns and "ts" in df.columns:
        numeric = pd.to_numeric(df["ts"], errors="coerce")
        df["time"] = pd.to_datetime(numeric, unit="s", errors="coerce") if numeric.notna().any() else pd.to_datetime(df["ts"], errors="coerce")
    elif "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")
    for column in ("step", "type", "amount", "risk_score", "decision", "latency_ms", "time", "txn_id", "analyst_status", "reasons", "alert_text", "nameOrig", "nameDest"):
        if column not in df.columns:
            df[column] = None
    df["reasons"] = df["reasons"].apply(lambda value: value if isinstance(value, list) else [])
    return df

def fetch_alerts() -> pd.DataFrame:
    return _frame(_request("GET", "/alerts"), "alerts")

def fetch_recent(limit: int = 500) -> pd.DataFrame:
    return _frame(_request("GET", "/recent", params={"limit": limit}), "recent")

def record_analyst_action(txn_id: str, action: str):
    return _request("POST", "/analyst_action", json={"txn_id": txn_id, "action": action})

STORY_FILES = {"Scam Drain": "story_scam_drain.csv", "Mule Burst": "story_mule_burst.csv", "Normal Day": "story_normal_day.csv"}
SCORE_FIELDS = ("step", "type", "amount", "nameOrig", "oldbalanceOrg", "newbalanceOrig", "nameDest", "oldbalanceDest", "newbalanceDest")

def replay_story(story: str) -> dict:
    if story not in STORY_FILES:
        raise APIError(f"Unknown demo story: {story}")
    dashboard_root = Path(__file__).resolve().parent
    candidates = (
        dashboard_root / "docs" / "demo" / STORY_FILES[story],
        dashboard_root.parent / "docs" / "demo" / STORY_FILES[story],
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    if not path.is_file():
        raise APIError(f"Story CSV not found: {path}")
    try:
        rows = pd.read_csv(path).to_dict(orient="records")
    except (OSError, ValueError) as exc:
        raise APIError(f"Could not read {path.name}: {exc}") from exc
    if not rows:
        raise APIError(f"{path.name} has no transaction rows.")
    missing = [field for field in SCORE_FIELDS if field not in rows[0]]
    if missing:
        raise APIError(f"{path.name} is missing required fields: {', '.join(missing)}")
    run_id = uuid4().hex[:10]
    sent, failures = 0, []
    with httpx.Client(timeout=12.0) as client:
        for index, row in enumerate(rows, start=1):
            body = {field: row[field] for field in SCORE_FIELDS}
            body["step"] = int(float(body["step"]))
            for field in ("amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"):
                body[field] = float(body[field])
            original_id = str(row.get("txn_id") or f"{story.lower().replace(' ', '-')}-{index}")
            body["txn_id"] = f"{original_id[:48]}-{run_id}"
            try:
                response = client.post(f"{API_BASE_URL}/score", json=body)
                response.raise_for_status()
                sent += 1
            except httpx.HTTPStatusError as exc:
                failures.append(f"row {index}: HTTP {exc.response.status_code} {exc.response.text[:180]}")
            except httpx.RequestError as exc:
                failures.append(f"row {index}: {exc}")
                break
    return {"sent": sent, "failed": len(failures), "errors": failures}

def format_units(value) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):,.2f} units"
