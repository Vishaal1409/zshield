"""ZShield smoke test. Run with the API already started:
    python smoke_test.py                 (local)
    python smoke_test.py --url http://localhost:8000
Prints PASS / WARN / FAIL for each check and exits with code 1 if anything FAILS."""
import argparse
import sys
import time

import httpx

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://localhost:8000")
args = ap.parse_args()
BASE = args.url.rstrip("/")
fails = 0


def report(level, name, detail=""):
    global fails
    if level == "FAIL":
        fails += 1
    print(f"[{level}] {name}" + (f"  ->  {detail}" if detail else ""))


def txn(tid, **kw):
    base = dict(txn_id=tid, step=2, type="PAYMENT", amount=50.0, nameOrig="C_SMOKE_1",
                oldbalanceOrg=1000.0, newbalanceOrig=950.0, nameDest="M_SMOKE_9",
                oldbalanceDest=0.0, newbalanceDest=0.0)
    base.update(kw)
    return base


stamp = int(time.time())
drain_id, ok_id = f"SMOKE_DRAIN_{stamp}", f"SMOKE_OK_{stamp}"
c = httpx.Client(timeout=10)

try:
    r = c.get(f"{BASE}/health")
    report("PASS" if r.status_code == 200 else "FAIL", "GET /health", str(r.status_code))
except Exception as e:
    print(f"[FAIL] Cannot reach the API at {BASE}: {e}")
    print("Start it first:  uvicorn api.main:app --port 8000")
    sys.exit(1)

need_score = ["txn_id", "risk_score", "decision", "reasons", "alert_text", "latency_ms"]

# 1. a drain-style transfer should be flagged
r = c.post(f"{BASE}/score", json=txn(drain_id, type="TRANSFER", amount=9000.0, oldbalanceOrg=9000.0,
                                      newbalanceOrig=0.0, nameOrig="C_SMOKE_2", nameDest="C_SMOKE_3"))
if r.status_code != 200:
    report("FAIL", "POST /score (drain transfer)", f"status {r.status_code}: {r.text[:200]}")
else:
    j = r.json()
    missing = [k for k in need_score if k not in j]
    report("PASS" if not missing else "FAIL", "/score response has all contract fields", f"missing {missing}" if missing else "")
    report("PASS" if j.get("decision") in ("HOLD", "STEP_UP") else "FAIL",
           "drain transfer is flagged (HOLD or STEP_UP)", f"decision={j.get('decision')} score={j.get('risk_score')}")
    report("PASS" if j.get("reasons") else "FAIL", "flagged payment has reasons", str(j.get("reasons")))
    report("PASS" if j.get("alert_text") else "WARN", "flagged payment has alert_text")
    lat = j.get("latency_ms", 9e9)
    report("PASS" if lat < 100 else "WARN", "latency under 100 ms", f"{lat} ms")

# 2. a normal small payment should be approved
r = c.post(f"{BASE}/score", json=txn(ok_id))
if r.status_code != 200:
    report("FAIL", "POST /score (normal payment)", f"status {r.status_code}: {r.text[:200]}")
else:
    d = r.json().get("decision")
    report("PASS" if d == "APPROVE" else "WARN", "normal payment is approved", f"decision={d}")

# 3. stats
r = c.get(f"{BASE}/stats")
keys = ["total_processed", "flagged_count", "held_count", "value_intercepted", "avg_latency_ms", "p95_latency_ms"]
if r.status_code == 200:
    miss = [k for k in keys if k not in r.json()]
    report("PASS" if not miss else "FAIL", "GET /stats has all fields", f"missing {miss}" if miss else "")
else:
    report("FAIL", "GET /stats", str(r.status_code))

# 4. alerts
alert_keys = ["txn_id", "risk_score", "decision", "reasons", "alert_text", "analyst_status"]
r = c.get(f"{BASE}/alerts")
if r.status_code == 200 and isinstance(r.json(), list):
    rows = r.json()
    report("PASS" if any(x.get("txn_id") == drain_id for x in rows) else "FAIL", "/alerts contains the flagged smoke transaction")
    if rows:
        miss = [k for k in alert_keys if k not in rows[0]]
        report("PASS" if not miss else "FAIL", "/alerts rows have the agreed fields", f"missing {miss}" if miss else "")
        extra = [k for k in ["amount", "type", "step", "nameOrig", "nameDest", "latency_ms"] if k not in rows[0]]
        report("PASS" if not extra else "WARN", "/alerts rows have the optional dashboard fields", f"missing {extra}" if extra else "")
    report("PASS" if all(x.get("decision") != "APPROVE" for x in rows) else "FAIL", "/alerts contains only flagged payments")
else:
    report("FAIL", "GET /alerts returns a list", str(r.status_code))

# 5. recent (agreed with Armaan)
r = c.get(f"{BASE}/recent", params={"limit": 50})
if r.status_code == 200 and isinstance(r.json(), list):
    rows = r.json()
    report("PASS" if any(x.get("txn_id") == ok_id for x in rows) else "FAIL", "/recent includes approved payments too")
else:
    report("FAIL", "GET /recent?limit=50 (Abhinava still needs to add it)", str(r.status_code))

# 6. analyst action
r = c.post(f"{BASE}/analyst_action", json={"txn_id": drain_id, "action": "BLOCK"})
report("PASS" if r.status_code == 200 and r.json().get("ok") else "FAIL", "POST /analyst_action", r.text[:120])

# 7. bad input must not crash the server
r = c.post(f"{BASE}/score", json={"txn_id": "BAD"})
report("PASS" if r.status_code == 422 else "WARN", "bad input is rejected cleanly (422)", f"status {r.status_code}")

print("\nRESULT:", "ALL CRITICAL CHECKS PASSED" if fails == 0 else f"{fails} CHECK(S) FAILED")
sys.exit(1 if fails else 0)
