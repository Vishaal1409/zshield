"""Runs Balaa's 10 edge cases (docs/demo/edge_cases.json) against the API."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api.main as m

SPEC = json.loads((Path(__file__).resolve().parents[2] / "docs/demo/edge_cases.json").read_text())


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ZSHIELD_DB", str(tmp_path / "audit.db"))
    monkeypatch.setenv("ZSHIELD_ALERT_TIMEOUT_S", "0.3")
    with TestClient(m.app) as c:
        yield c


def test_there_are_ten_cases():
    assert len(SPEC["cases"]) == 10


@pytest.mark.parametrize("case", SPEC["cases"], ids=lambda c: c["name"])
def test_edge_case(client, case):
    body = {**SPEC["base"], **case["patch"]}
    for k in case.get("remove", []):
        body.pop(k)
    r = client.post("/score", json=body)
    assert r.status_code == case["expect_status"], r.text
    if "expect_decision" in case:
        assert r.json()["decision"] == case["expect_decision"]
    if case.get("send_twice"):
        again = client.post("/score", json=body)
        assert again.json() == r.json()
        assert client.get("/stats").json()["total_processed"] == 1
    if r.status_code == 422:
        assert client.get("/stats").json()["total_processed"] == 0     # rejected input is never logged
