"""Tests with Joshua's trained model (artifacts/model.onnx + model_meta.json)."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api.main as m

ART = Path(__file__).resolve().parents[2] / "artifacts"
pytestmark = pytest.mark.skipif(not (ART / "model.onnx").exists(), reason="artifacts/model.onnx missing")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("ZSHIELD_MODEL_DIR", raising=False)
    monkeypatch.setenv("ZSHIELD_DB", str(tmp_path / "audit.db"))
    monkeypatch.setenv("ZSHIELD_ALERT_TIMEOUT_S", "0.3")
    with TestClient(m.app) as c:
        yield c


def txn(i, typ="TRANSFER", amount=9000.0, orig="C1", old_o=9000.0, new_o=0.0, dest="C2", step=626):
    return {"txn_id": i, "step": step, "type": typ, "amount": amount, "nameOrig": orig,
            "oldbalanceOrg": old_o, "newbalanceOrig": new_o, "nameDest": dest,
            "oldbalanceDest": 0.0, "newbalanceDest": amount}


def test_health_reports_the_trained_model(client):
    assert client.get("/health").json() == {"status": "ok", "scorer": "onnx"}
    meta = json.loads((ART / "model_meta.json").read_text())
    th = m.app.state.rt.thresholds
    assert (th.step_up, th.hold) == (meta["t_low"], meta["t_high"])      # the model's own cut-offs


def test_full_drain_transfer_is_held_with_a_high_score(client):
    j = client.post("/score", json=txn("D1")).json()
    assert j["decision"] == "HOLD" and j["risk_score"] > 0.5
    assert j["reasons"] and j["alert_text"]
    assert m.app.state.rt.db.get("D1")["scorer"] == "onnx"


def test_ordinary_payment_is_approved_and_unscored_types_get_zero(client):
    pay = client.post("/score", json=txn("P1", "PAYMENT", 50.0, "C3", 1000.0, 950.0, "M1")).json()
    assert pay["decision"] == "APPROVE" and pay["risk_score"] == 0.0 and pay["reasons"] == []


def test_mule_burst_is_raised_to_step_up_by_the_history_rule(client):
    out = []
    for k in range(8):                       # 8 different senders, ordinary transfers, one recipient
        out.append(client.post("/score", json=txn(f"M{k}", amount=300.0, orig=f"S{k}", old_o=9000.0,
                                                  new_o=8700.0, dest="MULE")).json())
    assert [o["decision"] for o in out[:5]] == ["APPROVE"] * 5          # the first five look normal
    for o in out[5:]:
        assert o["decision"] == "STEP_UP" and o["risk_score"] == 0.5
        assert "Many payments to this recipient in a short time" in o["reasons"]
    assert m.app.state.rt.db.get("M7")["scorer"] == "onnx+history_rule"


def test_history_rules_can_be_switched_off(client, monkeypatch):
    import api.decision as d
    import api.main as main_mod
    monkeypatch.setattr(d, "HISTORY_RULES", False)
    monkeypatch.setattr(main_mod, "history_rule", d.history_rule)
    for k in range(8):
        j = client.post("/score", json=txn(f"M{k}", amount=300.0, orig=f"S{k}", old_o=9000.0,
                                           new_o=8700.0, dest="MULE")).json()
    assert j["decision"] == "APPROVE"


def test_demo_story_files_end_to_end(client):
    """Balaa's three stories through the real model: drain is held, normal day is untouched."""
    import csv
    from api.producer import row_to_body
    root = Path(__file__).resolve().parents[2] / "docs" / "demo"
    if not (root / "story_scam_drain.csv").exists():
        pytest.skip("story files missing")
    def run(name):
        client.post("/admin/reset")
        res = []
        for i, row in enumerate(csv.DictReader(open(root / f"{name}.csv"))):
            res.append((row.get("isFraud"), client.post("/score", json=row_to_body(row, i, name)).json()["decision"]))
        return res
    assert all(d == "HOLD" for fr, d in run("story_scam_drain") if fr == "1")
    assert all(d == "APPROVE" for _, d in run("story_normal_day"))
    mule = [d for _, d in run("story_mule_burst")]
    assert mule[:5] == ["APPROVE"] * 5 and set(mule[5:]) == {"STEP_UP"}
