"""Backend tests. Run from the repo root:  pip install pytest && python -m pytest api/tests -q"""
import json
import time

import pytest
from fastapi.testclient import TestClient

import api.main as m


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ZSHIELD_DB", str(tmp_path / "audit.db"))
    monkeypatch.setenv("ZSHIELD_ALERT_TIMEOUT_S", "0.3")
    with TestClient(m.app) as c:
        yield c


def txn(i="T1", step=2, typ="TRANSFER", amount=9000.0, orig="C1", old_o=9000.0, new_o=0.0,
        dest="C2", old_d=0.0, new_d=0.0):
    return {"txn_id": i, "step": step, "type": typ, "amount": amount, "nameOrig": orig,
            "oldbalanceOrg": old_o, "newbalanceOrig": new_o, "nameDest": dest,
            "oldbalanceDest": old_d, "newbalanceDest": new_d}


def normal(i, step=10):
    return txn(i, step, "PAYMENT", 100.0, f"C{i}", 5000.0, 4900.0, f"M{i}", 0.0, 0.0)


def test_health(client):
    j = client.get("/health").json()
    assert j["status"] == "ok" and j["scorer"] in ("placeholder_rule", "onnx")


def test_scam_drain_is_held_with_reasons_and_alert(client):
    j = client.post("/score", json=txn()).json()
    assert j["decision"] == "HOLD" and j["risk_score"] >= 0.9
    assert "Account emptied in one transfer" in j["reasons"] and len(j["reasons"]) <= 3
    assert j["alert_text"] and j["latency_ms"] >= 0


def test_normal_payment_approved_without_reasons(client):
    j = client.post("/score", json=normal("N1")).json()
    assert j["decision"] == "APPROVE" and j["reasons"] == [] and j["alert_text"] == ""


def test_mule_burst_flags_later_payments(client):
    last = None
    for k in range(8):
        last = client.post("/score", json=txn(f"M{k}", 5, "TRANSFER", 1000.0, f"S{k}", 9000.0,
                                              8000.0, "MULE", 0.0, 0.0)).json()
    assert last["decision"] in ("STEP_UP", "HOLD")
    assert any("recipient" in r.lower() for r in last["reasons"])


def test_duplicate_txn_id_returns_original_and_is_not_rescored(client):
    a = client.post("/score", json=txn()).json()
    b = client.post("/score", json=txn()).json()
    assert a == b
    assert client.get("/stats").json()["total_processed"] == 1


@pytest.mark.parametrize("patch", [
    {"amount": -5.0}, {"amount": "abc"}, {"step": -1}, {"txn_id": ""}, {"amount": float("nan")},
])
def test_bad_input_rejected_422(client, patch):
    body = {**txn(), **patch}
    r = client.post("/score", content=json.dumps(body, allow_nan=True),
                    headers={"content-type": "application/json"})
    assert r.status_code == 422


def test_missing_field_rejected_422(client):
    body = txn()
    del body["nameDest"]
    assert client.post("/score", json=body).status_code == 422
    assert client.get("/stats").json()["total_processed"] == 0


def test_zero_and_huge_amounts_are_handled(client):
    z = client.post("/score", json=txn("Z", amount=0.0, old_o=500.0, new_o=500.0, typ="PAYMENT")).json()
    h = client.post("/score", json=txn("H", amount=9.9e12, old_o=9.9e12, new_o=0.0,
                                       orig="C77", dest="C78")).json()
    assert z["decision"] == "APPROVE"
    assert h["decision"] == "HOLD"


def test_model_failure_fails_safe_to_step_up_and_is_logged(client):
    class Boom:
        name = "boom"
        def score(self, f): raise RuntimeError("model down")
    m.app.state.rt.scorer = Boom()
    j = client.post("/score", json=normal("F1")).json()
    assert j["decision"] == "STEP_UP" and j["risk_score"] == 0.5 and j["reasons"]
    row = m.app.state.rt.db.get("F1")
    assert "model down" in row["error"]


def test_alert_timeout_falls_back_to_template(client, monkeypatch):
    monkeypatch.setattr(m, "generate_alert", lambda facts: time.sleep(2) or "slow llm text")
    t0 = time.time()
    j = client.post("/score", json=txn("A1")).json()
    assert time.time() - t0 < 1.5
    assert "paused a payment" in j["alert_text"]          # template text, decision unchanged
    assert j["decision"] == "HOLD"


def test_alerts_stats_and_analyst_action(client):
    client.post("/score", json=txn("H1", amount=9000.0))
    client.post("/score", json=normal("N1"))
    alerts = client.get("/alerts").json()
    assert [a["txn_id"] for a in alerts] == ["H1"]
    assert alerts[0]["analyst_status"] == "PENDING" and isinstance(alerts[0]["reasons"], list)
    s = client.get("/stats").json()
    assert s["total_processed"] == 2 and s["flagged_count"] == 1 and s["held_count"] == 1
    assert s["value_intercepted"] == 9000.0 and s["p95_latency_ms"] >= 0
    assert client.post("/analyst_action", json={"txn_id": "H1", "action": "BLOCK"}).json() == {"ok": True}
    assert client.get("/alerts").json()[0]["analyst_status"] == "BLOCK"
    assert client.get("/stats").json()["value_intercepted"] == 9000.0
    client.post("/analyst_action", json={"txn_id": "H1", "action": "APPROVE"})
    assert client.get("/stats").json()["value_intercepted"] == 0.0     # analyst released it
    r = client.post("/analyst_action", json={"txn_id": "nope", "action": "BLOCK"})
    assert r.status_code == 404 and r.json()["ok"] is False
    assert client.post("/analyst_action", json={"txn_id": "H1", "action": "DELETE"}).status_code == 422


def test_reset_allows_replay(client):
    client.post("/score", json=txn("R1"))
    assert client.post("/admin/reset").json() == {"ok": True}
    assert client.get("/stats").json()["total_processed"] == 0
    assert "New recipient" in client.post("/score", json=txn("R1")).json()["reasons"]
    assert client.get("/stats").json()["total_processed"] == 1


def test_audit_log_persists_on_disk(client, tmp_path):
    client.post("/score", json=txn("P1"))
    import sqlite3
    row = sqlite3.connect(tmp_path / "audit.db").execute(
        "select decision, latency_ms, analyst_status from decisions where txn_id='P1'").fetchone()
    assert row[0] == "HOLD" and row[1] > 0 and row[2] == "PENDING"


def test_onnx_scorer_matches_sklearn(tmp_path):
    """The loader works on a real ONNX file (a tiny stand-in model, NOT the fraud model)."""
    np = pytest.importorskip("numpy")
    skl = pytest.importorskip("skl2onnx")
    from sklearn.linear_model import LogisticRegression
    from skl2onnx.common.data_types import FloatTensorType
    from api.model_runtime import load_scorer
    cols = ["amount", "is_full_drain", "new_recipient"]
    X = np.array([[100, 0, 0], [5000, 1, 1], [200, 0, 1], [9000, 1, 1]] * 5, dtype=np.float32)
    y = np.array([0, 1, 0, 1] * 5)
    clf = LogisticRegression().fit(X, y)
    onx = skl.convert_sklearn(clf, initial_types=[("input", FloatTensorType([None, 3]))],
                              options={id(clf): {"zipmap": False}})
    (tmp_path / "model.onnx").write_bytes(onx.SerializeToString())
    (tmp_path / "feature_columns.json").write_text(json.dumps(cols))
    sc = load_scorer(tmp_path)
    assert sc.name == "onnx"
    f = {"amount": 7000.0, "is_full_drain": 1, "new_recipient": 1}
    assert abs(sc.score(f) - float(clf.predict_proba([[7000, 1, 1]])[0, 1])) < 1e-4


def test_concurrent_duplicate_txn_id_is_scored_once(client):
    """Two requests with the same new txn_id at the same moment: score once, same answer, state touched once."""
    import threading
    from api.schemas import Txn

    calls = []

    class Slow:
        name = "slow"
        def score(self, f):
            calls.append(1)
            time.sleep(0.3)                 # hold the first request open so the second one overlaps
            return 0.1
    m.app.state.rt.scorer = Slow()

    results = [None] * 4
    def hit(k):
        results[k] = m.score(Txn(**normal("RACE"))).model_dump()
    threads = [threading.Thread(target=hit, args=(k,)) for k in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(calls) == 1
    assert all(r == results[0] for r in results)
    assert len(m.app.state.rt.state._sender["CRACE"]) == 1
    assert client.get("/stats").json()["total_processed"] == 1
