"""ZShield real-time scoring API (Abhinava).

Flow per payment:  validate -> duplicate check -> live features (state store) -> scorer (ONNX or
placeholder rule) -> thresholds -> [flagged only: reasons + alert text] -> SQLite audit log.

Run ONE worker only (state is in memory):  uvicorn api.main:app --port 8000
Env vars: ZSHIELD_DB (sqlite path), ZSHIELD_ALERT_TIMEOUT_S (GenAI timeout), ZSHIELD_WINDOW_STEPS.
"""
import importlib
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.db import AuditDB
from api.decision import FAILSAFE_REASON, FAILSAFE_SCORE, Thresholds, rule_reasons
from api.model_runtime import load_scorer
from api.schemas import AnalystAction, ScoreResponse, Txn
from api.state import StateStore
from genai.explain import generate_alert, template_alert

log = logging.getLogger("zshield.api")
DEFAULT_DB = str(Path(__file__).resolve().parent.parent / "zshield_audit.db")


def _load_explainer():
    """Optional hook for Joshua's SHAP reasons: model/explain.py -> explain_top3(features) -> list[str].
    TODO: confirm the real function name/signature with Joshua. Falls back to rule reasons."""
    try:
        return importlib.import_module("model.explain").explain_top3
    except Exception:
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rt = SimpleNamespace(
        db=AuditDB(os.getenv("ZSHIELD_DB", DEFAULT_DB)),
        state=StateStore(),
        scorer=load_scorer(),
        thresholds=Thresholds.load(),
        explainer=_load_explainer(),
        pool=ThreadPoolExecutor(max_workers=4, thread_name_prefix="alert"),
        alert_timeout=float(os.getenv("ZSHIELD_ALERT_TIMEOUT_S", "2.0")),
    )
    log.info("ZShield ready: scorer=%s thresholds=(%s, %s)", app.state.rt.scorer.name,
             app.state.rt.thresholds.step_up, app.state.rt.thresholds.hold)
    yield
    app.state.rt.pool.shutdown(wait=False, cancel_futures=True)
    app.state.rt.db.close()


app = FastAPI(title="ZShield scoring API", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    """422 with a compact error list. The default handler echoes the bad input back, which crashes
    (HTTP 500) when the input is NaN/inf because those are not valid JSON."""
    errs = [{"field": ".".join(str(p) for p in e["loc"][1:]) or "body", "problem": e["msg"]}
            for e in exc.errors()]
    return JSONResponse(status_code=422, content={"ok": False, "error": "invalid request", "details": errs})


def _alert_text(rt, facts: dict) -> str:
    """GenAI alert with a hard timeout and a template fallback. The text can never change the decision."""
    fut = rt.pool.submit(generate_alert, facts)
    try:
        text = fut.result(timeout=rt.alert_timeout)
        return text if isinstance(text, str) and text.strip() else template_alert(facts)
    except (FutureTimeout, Exception):
        log.warning("generate_alert failed or timed out; using template")
        return template_alert(facts)


def _response_from_row(row: dict) -> ScoreResponse:
    return ScoreResponse(txn_id=row["txn_id"], risk_score=row["risk_score"], decision=row["decision"],
                         reasons=row["reasons"], alert_text=row["alert_text"], latency_ms=row["latency_ms"])


@app.get("/health")
def health():
    rt = app.state.rt
    return {"status": "ok", "scorer": rt.scorer.name}   # "scorer" is an additive field


@app.post("/score", response_model=ScoreResponse)
def score(txn: Txn):
    rt = app.state.rt

    # Duplicate txn_id: return the original decision, do not re-score or touch state.
    prior = rt.db.get(txn.txn_id)
    if prior:
        return _response_from_row(prior)

    t0 = time.perf_counter()
    data = txn.model_dump()
    feats: dict = {}
    error = None
    try:
        feats = rt.state.build_features(data)
        s = float(rt.scorer.score(feats))
        decision = rt.thresholds.decide(s)
    except Exception as e:                       # fail safe: never a silent approve
        log.exception("Scoring failed for %s", txn.txn_id)
        s, decision, error = FAILSAFE_SCORE, "STEP_UP", repr(e)
    latency_ms = (time.perf_counter() - t0) * 1000   # decision latency: features + model + thresholds

    # Explanation only for flagged payments, so normal payments stay fast.
    t1 = time.perf_counter()
    reasons, alert = [], ""
    if decision != "APPROVE":
        if error:
            reasons = [FAILSAFE_REASON]
        else:
            try:
                reasons = list(rt.explainer(feats))[:3] if rt.explainer else rule_reasons(feats)
            except Exception:
                log.exception("explain failed; using rule reasons")
                reasons = rule_reasons(feats)
        alert = _alert_text(rt, {"decision": decision, "amount": data["amount"], "reasons": reasons})
    explain_ms = (time.perf_counter() - t1) * 1000

    resp = ScoreResponse(txn_id=txn.txn_id, risk_score=round(s, 4), decision=decision, reasons=reasons,
                         alert_text=alert, latency_ms=round(latency_ms, 3))
    try:
        rt.db.insert({**resp.model_dump(), "step": data["step"], "amount": data["amount"],
                      "explain_ms": round(explain_ms, 3), "scorer": rt.scorer.name, "error": error})
    except Exception:
        log.exception("Audit log write failed for %s", txn.txn_id)   # never block a payment decision
    return resp


@app.get("/stats")
def stats():
    return app.state.rt.db.stats()


@app.get("/alerts")
def alerts():
    return app.state.rt.db.alerts(50)


@app.post("/analyst_action")
def analyst_action(a: AnalystAction):
    if app.state.rt.db.set_status(a.txn_id, a.action):
        return {"ok": True}
    return JSONResponse(status_code=404, content={"ok": False, "error": "txn_id not found"})


@app.post("/admin/reset")
def reset():
    """Demo helper (not in the contract): clears audit log and state so a story can be replayed."""
    rt = app.state.rt
    rt.db.reset()
    rt.state.clear()
    return {"ok": True}
