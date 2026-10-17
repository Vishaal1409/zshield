"""Starter scoring API with a DUMMY rule instead of the real model.
Abhinava replaces dummy_score() with the ONNX model, adds the state store and SQLite audit log."""
import json
import time
from pathlib import Path

from fastapi import FastAPI

from api.schemas import AnalystAction, ScoreResponse, Txn
from features.features import compute_live_features
from genai.explain import generate_alert

app = FastAPI(title="ZShield scoring API")

THRESHOLDS = json.loads((Path(__file__).parent.parent / "model" / "thresholds.json").read_text())
STATE: dict = {}          # per-account history (replace with a proper store if needed)
DECISIONS: list = []      # audit log in memory (replace with SQLite)


def dummy_score(f: dict) -> float:
    """Placeholder rule so the whole pipeline can be wired up before the model is ready."""
    score = 0.05
    if f["is_full_drain"]:
        score += 0.6
    if f["new_recipient"]:
        score += 0.15
    if f.get("type_TRANSFER") or f.get("type_CASH_OUT"):
        score += 0.15
    return min(score, 0.99)


def decide(score: float) -> str:
    if score >= THRESHOLDS["hold"]:
        return "HOLD"
    if score >= THRESHOLDS["step_up"]:
        return "STEP_UP"
    return "APPROVE"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/score", response_model=ScoreResponse)
def score(txn: Txn):
    t0 = time.perf_counter()
    data = txn.model_dump()
    feats: dict = {}
    try:
        feats = compute_live_features(data, STATE)
        s = dummy_score(feats)
        decision = decide(s)
    except Exception:
        s, decision = 0.5, "STEP_UP"   # fail safe: never silently approve
    reasons, alert = [], ""
    if decision != "APPROVE":
        if feats.get("is_full_drain"):
            reasons.append("Account emptied in one transfer")
        if feats.get("new_recipient"):
            reasons.append("New recipient")
        reasons = reasons or ["Unusual activity"]
        alert = generate_alert({"decision": decision, "amount": data["amount"], "reasons": reasons})
    latency = (time.perf_counter() - t0) * 1000
    resp = ScoreResponse(txn_id=txn.txn_id, risk_score=round(s, 4), decision=decision,
                         reasons=reasons[:3], alert_text=alert, latency_ms=round(latency, 3))
    DECISIONS.append({**resp.model_dump(), "amount": data["amount"], "analyst_status": "PENDING"})
    return resp


@app.get("/stats")
def stats():
    lat = sorted(d["latency_ms"] for d in DECISIONS)
    flagged = [d for d in DECISIONS if d["decision"] != "APPROVE"]
    held = [d for d in DECISIONS if d["decision"] == "HOLD"]
    p95 = lat[int(0.95 * (len(lat) - 1))] if lat else 0.0
    return {
        "total_processed": len(DECISIONS),
        "flagged_count": len(flagged),
        "held_count": len(held),
        "value_intercepted": sum(d["amount"] for d in held),
        "avg_latency_ms": round(sum(lat) / len(lat), 3) if lat else 0.0,
        "p95_latency_ms": round(p95, 3),
    }


@app.get("/alerts")
def alerts():
    flagged = [d for d in DECISIONS if d["decision"] != "APPROVE"]
    return flagged[-50:][::-1]


@app.post("/analyst_action")
def analyst_action(a: AnalystAction):
    for d in DECISIONS:
        if d["txn_id"] == a.txn_id:
            d["analyst_status"] = a.action
            return {"ok": True}
    return {"ok": False, "error": "txn_id not found"}
