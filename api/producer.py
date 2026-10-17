"""Replays a CSV of transactions into the API. Usage:
python -m api.producer data/demo_stream.csv --rate 100 --limit 2000"""
import argparse
import csv
import time

import httpx

NUM = ["amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]

ap = argparse.ArgumentParser()
ap.add_argument("csv_path")
ap.add_argument("--url", default="http://localhost:8000/score")
ap.add_argument("--rate", type=float, default=50, help="transactions per second")
ap.add_argument("--limit", type=int, default=1000)
args = ap.parse_args()

with open(args.csv_path, newline="") as fh, httpx.Client() as client:
    for i, row in enumerate(csv.DictReader(fh)):
        if i >= args.limit:
            break
        body = {k: row[k] for k in ["type", "nameOrig", "nameDest"]}
        body.update({k: float(row[k]) for k in NUM})
        body["step"] = int(row["step"])
        body["txn_id"] = row.get("txn_id") or f"T{i}"
        r = client.post(args.url, json=body)
        if i % 100 == 0:
            print(i, r.json().get("decision"))
        time.sleep(1.0 / args.rate)
