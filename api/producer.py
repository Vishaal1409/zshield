"""Stream simulator: replays a CSV of transactions into POST /score, one at a time, at an adjustable rate.

Usage (from the repo root, API running on :8000):
  python -m api.producer docs/samples/sample_stream.csv --rate 100
  python -m api.producer data/demo_stream.csv --rate 200 --limit 5000 --reset

CSV columns (PaySim names): step,type,amount,nameOrig,oldbalanceOrg,newbalanceOrig,nameDest,
oldbalanceDest,newbalanceDest and optionally txn_id (generated as <prefix><row number> if absent).
Rows are sent in file order, so sort by step before replaying.
"""
import argparse
import csv
import time
from collections import Counter

import httpx

NUM = ["amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]


def row_to_body(row: dict, i: int, prefix: str) -> dict:
    body = {k: row[k] for k in ("type", "nameOrig", "nameDest")}
    body.update({k: float(row[k]) for k in NUM})
    body["step"] = int(float(row["step"]))
    body["txn_id"] = row.get("txn_id") or f"{prefix}{i}"
    return body


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path")
    ap.add_argument("--url", default="http://localhost:8000", help="API base URL")
    ap.add_argument("--rate", type=float, default=50, help="transactions per second (50 to 500)")
    ap.add_argument("--limit", type=int, default=1000)
    ap.add_argument("--prefix", default="T", help="txn_id prefix when the CSV has no txn_id column")
    ap.add_argument("--reset", action="store_true", help="POST /admin/reset before starting")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    if args.rate <= 0:
        ap.error("--rate must be > 0")

    base = args.url.rstrip("/")
    decisions, errors, sent = Counter(), 0, 0
    with httpx.Client(timeout=10.0) as client:
        try:
            client.get(f"{base}/health").raise_for_status()
        except Exception as e:
            print(f"API not reachable at {base}: {e}")
            return 1
        if args.reset:
            client.post(f"{base}/admin/reset")

        interval = 1.0 / args.rate
        start = time.perf_counter()
        with open(args.csv_path, newline="") as fh:
            for i, row in enumerate(csv.DictReader(fh)):
                if i >= args.limit:
                    break
                # Absolute schedule: a slow request does not permanently lower the rate.
                delay = start + i * interval - time.perf_counter()
                if delay > 0:
                    time.sleep(delay)
                try:
                    r = client.post(f"{base}/score", json=row_to_body(row, i, args.prefix))
                    if r.status_code == 200:
                        decisions[r.json()["decision"]] += 1
                    else:
                        errors += 1
                        print(f"row {i}: HTTP {r.status_code} {r.text[:120]}")
                except Exception as e:
                    errors += 1
                    print(f"row {i}: {e}")
                sent += 1
                if not args.quiet and sent % 100 == 0:
                    print(f"{sent} sent  {dict(decisions)}")
        wall = time.perf_counter() - start

    print(f"\nSent {sent} in {wall:.1f}s = {sent / wall:.0f}/s (target {args.rate:.0f}/s). "
          f"Decisions: {dict(decisions)}  errors: {errors}")
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
