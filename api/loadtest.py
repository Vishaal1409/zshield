"""Load test for POST /score. Measures end-to-end latency (client side), the latency the API itself
reports, and throughput. Saves a markdown table for the deck and for Vishaal's IBM Z comparison.

  # API running on :8000 (single worker). From the repo root:
  python -m api.loadtest --n 5000 --concurrency 8 --label "laptop"
  python -m api.loadtest --csv data/demo_stream.csv --n 5000 --label "LinuxONE"

Run it on each machine (laptop, then LinuxONE) with a different --label and compare the tables.
It POSTs /admin/reset first (disable with --no-reset) and uses unique txn_ids per run.
"""
import argparse
import csv
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import httpx

from api.producer import row_to_body

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "docs" / "loadtest_results.md"


def synthetic(n: int, run: str) -> list:
    rnd = random.Random(1)
    out = []
    for i in range(n):
        bal = rnd.uniform(1_000, 90_000)
        drain = rnd.random() < 0.02
        amt = bal if drain else rnd.uniform(10, 0.3 * bal)
        out.append({"txn_id": f"LT{run}-{i}", "step": 1 + i // 50,
                    "type": rnd.choice(["PAYMENT", "TRANSFER", "CASH_OUT", "DEBIT", "CASH_IN"]),
                    "amount": round(amt, 2), "nameOrig": f"C{i}", "oldbalanceOrg": round(bal, 2),
                    "newbalanceOrig": round(bal - amt, 2), "nameDest": f"M{i % 500}",
                    "oldbalanceDest": 0.0, "newbalanceDest": round(amt, 2)})
    return out


def from_csv(path: str, n: int, run: str) -> list:
    with open(path, newline="") as fh:
        rows = [row_to_body(r, i, f"LT{run}-") for i, r in zip(range(n), csv.DictReader(fh))]
    for r in rows:
        r["txn_id"] = f"LT{run}-{r['txn_id']}"
    return rows


def pct(sorted_vals: list, p: float) -> float:
    return sorted_vals[min(len(sorted_vals) - 1, int(p / 100 * len(sorted_vals)))]


def worker(args):
    base, chunk = args
    rtt, srv, dec, errs = [], [], {}, 0
    with httpx.Client(timeout=15.0) as c:
        for body in chunk:
            t0 = time.perf_counter()
            try:
                r = c.post(f"{base}/score", json=body)
                rtt.append((time.perf_counter() - t0) * 1000)
                if r.status_code == 200:
                    j = r.json()
                    srv.append(j["latency_ms"])
                    dec[j["decision"]] = dec.get(j["decision"], 0) + 1
                else:
                    errs += 1
            except Exception:
                errs += 1
    return rtt, srv, dec, errs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--concurrency", type=int, default=1, help="1 = strictly one at a time")
    ap.add_argument("--csv", help="replay this CSV instead of synthetic payments")
    ap.add_argument("--label", default="local", help="machine label, e.g. laptop or LinuxONE")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--no-reset", action="store_true")
    args = ap.parse_args(argv)

    base = args.url.rstrip("/")
    run = datetime.now().strftime("%H%M%S")
    with httpx.Client(timeout=10.0) as c:
        health = c.get(f"{base}/health").json()
        if not args.no_reset:
            c.post(f"{base}/admin/reset")
    txns = from_csv(args.csv, args.n, run) if args.csv else synthetic(args.n, run)
    n = len(txns)
    k = max(1, args.concurrency)
    chunks = [(base, txns[i::k]) for i in range(k)]   # note: interleaved, so per-account order is not kept

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=k) as ex:
        results = list(ex.map(worker, chunks))
    wall = time.perf_counter() - t0

    rtt = sorted(x for r in results for x in r[0])
    srv = sorted(x for r in results for x in r[1])
    errs = sum(r[3] for r in results)
    dec = {}
    for r in results:
        for d, v in r[2].items():
            dec[d] = dec.get(d, 0) + v
    if not rtt:
        print("No successful requests.")
        return 1

    table = (
        f"### Load test: {args.label}  ({datetime.now():%Y-%m-%d %H:%M})\n\n"
        f"Scorer: `{health.get('scorer')}` | requests: {n} | concurrency: {k} | errors: {errs} | "
        f"decisions: {dec}\n\n"
        "| Metric | End-to-end (client, ms) | API-reported decision latency (ms) |\n|---|---|---|\n"
        f"| mean | {statistics.mean(rtt):.2f} | {statistics.mean(srv):.3f} |\n"
        f"| p50 | {pct(rtt, 50):.2f} | {pct(srv, 50):.3f} |\n"
        f"| p95 | {pct(rtt, 95):.2f} | {pct(srv, 95):.3f} |\n"
        f"| p99 | {pct(rtt, 99):.2f} | {pct(srv, 99):.3f} |\n\n"
        f"Throughput: **{n / wall:.0f} transactions/s** ({n} in {wall:.1f}s).\n\n"
        "End-to-end includes HTTP and JSON on the same machine as the client. API-reported latency is "
        "features + model + thresholds only (alert text is timed separately in the audit log).\n"
    )
    print(table)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a") as fh:
        fh.write(table + "\n")
    print(f"appended to {out}")
    return 0 if errs == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
