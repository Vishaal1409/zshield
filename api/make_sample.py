"""Generates a small SYNTHETIC sample stream (PaySim-style columns) so the pipeline can be tested
before Balaa's demo_stream.csv arrives. Not real data and not the demo data.

  python -m api.make_sample            -> docs/samples/sample_stream.csv
"""
import csv
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "samples" / "sample_stream.csv"
COLS = ["step", "type", "amount", "nameOrig", "oldbalanceOrg", "newbalanceOrig", "nameDest",
        "oldbalanceDest", "newbalanceDest"]


def row(step, typ, amount, orig, old_o, dest, old_d):
    amount, old_o, old_d = round(amount, 2), round(old_o, 2), round(old_d, 2)   # round first so balances add up
    return [step, typ, amount, orig, old_o, round(max(old_o - amount, 0), 2), dest, old_d, round(old_d + amount, 2)]


def build(seed: int = 7) -> list:
    rnd = random.Random(seed)
    rows = []
    for i in range(240):                                   # ordinary payments
        step = 1 + i // 12
        bal = rnd.uniform(2_000, 80_000)
        amt = rnd.uniform(50, 0.25 * bal)
        rows.append(row(step, rnd.choice(["PAYMENT", "PAYMENT", "CASH_OUT", "TRANSFER", "DEBIT"]),
                        amt, f"C{1000 + i}", bal, f"M{5000 + i % 40}", 0))
    rows.append(row(26, "TRANSFER", 48_000, "C9001", 48_000, "C7777", 0))      # scam drain
    rows.append(row(26, "CASH_OUT", 31_500, "C9002", 31_500, "C7778", 0))      # scam drain
    for k in range(10):                                    # mule burst: many payers, one destination
        bal = rnd.uniform(5_000, 20_000)
        rows.append(row(27, "TRANSFER", bal * 0.4, f"C92{k:02d}", bal, "C8888", 1_000 * k))
    rows.sort(key=lambda r: r[0])
    return rows


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        w.writerows(build())
    print(f"wrote {OUT}")
