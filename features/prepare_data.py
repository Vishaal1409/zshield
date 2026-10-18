"""Data preparation (Balaa): quality checks, features, time-based splits, demo stream, demo stories.

Usage (from the repo root, PaySim CSV in data/):
  python -m features.prepare_data data/paysim.csv

Writes:
  data/train.parquet, data/val.parquet, data/test.parquet   raw columns + features + isFraud (not committed)
  docs/demo/demo_stream.csv          20,000 test-period payments in step order, incl. all test fraud
  docs/demo/story_scam_drain.csv     Story 1: night-time full drain to a new recipient (real PaySim rows)
  docs/demo/story_mule_burst.csv     Story 2: many senders -> one recipient (SYNTHETIC, see data card)
  docs/demo/story_normal_day.csv     Story 3: 200 ordinary payments (real PaySim rows)
  docs/demo/data_summary.json        numbers quoted in the data card
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from features.features import ALL_FEATURES, build_feature_frame

TRAIN_MAX_STEP, VAL_MAX_STEP = 500, 620     # train 1-500, val 501-620, test 621-743 (same as model/train.py)
RAW = ["step", "type", "amount", "nameOrig", "oldbalanceOrg", "newbalanceOrig", "nameDest",
       "oldbalanceDest", "newbalanceDest"]
DEMO_SIZE = 20_000
SEED = 42
DEMO_DIR = Path("docs/demo")
DATA_DIR = Path("data")


def quality_report(df: pd.DataFrame) -> dict:
    fraud = df[df.isFraud == 1]
    tc = df[df.type.isin(["TRANSFER", "CASH_OUT"])]
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "steps": [int(df.step.min()), int(df.step.max())],
        "fraud_count": int(df.isFraud.sum()),
        "fraud_rate": float(df.isFraud.mean()),
        "fraud_by_type": {k: int(v) for k, v in df.groupby("type").isFraud.sum().items()},
        "rows_by_type": {k: int(v) for k, v in df.type.value_counts().items()},
        "isFlaggedFraud_count": int(df.isFlaggedFraud.sum()),
        "null_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "negative_amounts": int((df.amount < 0).sum()),
        "zero_amounts": int((df.amount == 0).sum()),
        "senders_seen_once_share": float((df.nameOrig.value_counts() == 1).mean()),
        "max_payments_into_one_fraud_recipient": int(fraud.nameDest.value_counts().max()),
        "fraud_full_drain_share": float(((fraud.amount >= fraud.oldbalanceOrg) & (fraud.oldbalanceOrg > 0)).mean()),
        "transfer_cashout_orig_balance_error_share": float(
            (np.abs(tc.newbalanceOrig + tc.amount - tc.oldbalanceOrg) > 0.01).mean()),
        "transfer_cashout_dest_balance_error_share": float(
            (np.abs(tc.oldbalanceDest + tc.amount - tc.newbalanceDest) > 0.01).mean()),
        "dest_balances_both_zero_share_fraud": float(
            ((fraud.oldbalanceDest == 0) & (fraud.newbalanceDest == 0)).mean()),
        "dest_balances_both_zero_share_legit_transfer_cashout": float(
            ((tc[tc.isFraud == 0].oldbalanceDest == 0) & (tc[tc.isFraud == 0].newbalanceDest == 0)).mean()),
    }


def make_splits(df: pd.DataFrame, feats: pd.DataFrame) -> dict:
    full = pd.concat([df[RAW + ["isFraud"]], feats.drop(columns=[c for c in RAW if c in feats])], axis=1)
    parts = {
        "train": full[full.step <= TRAIN_MAX_STEP],
        "val": full[(full.step > TRAIN_MAX_STEP) & (full.step <= VAL_MAX_STEP)],
        "test": full[full.step > VAL_MAX_STEP],
    }
    out = {}
    for name, part in parts.items():
        part.to_parquet(DATA_DIR / f"{name}.parquet", index=True)
        out[name] = {"rows": len(part), "fraud": int(part.isFraud.sum()), "fraud_rate": float(part.isFraud.mean()),
                     "steps": [int(part.step.min()), int(part.step.max())]}
    return out


def with_ids(rows: pd.DataFrame, prefix: str) -> pd.DataFrame:
    rows = rows.copy()
    rows.insert(0, "txn_id", [f"{prefix}{i}" for i in rows.index])
    return rows


def demo_stream(df: pd.DataFrame) -> pd.DataFrame:
    """All test-period fraud plus a random sample of test-period legit payments, in step order.
    Fraud share is higher than reality on purpose (stated in the data card)."""
    test = df[df.step > VAL_MAX_STEP]
    fraud = test[test.isFraud == 1]
    legit = test[test.isFraud == 0].sample(DEMO_SIZE - len(fraud), random_state=SEED)
    out = pd.concat([fraud, legit]).sort_index()          # PaySim file order is step order
    return with_ids(out[RAW + ["isFraud"]], "D")


def story_scam_drain(df: pd.DataFrame) -> pd.DataFrame:
    """The 12 ordinary payments just before it, then a real night-time fraud: full-drain TRANSFER followed by the
    CASH_OUT that moves the money on (PaySim fraud comes as this pair, same amount, same step)."""
    test = df[(df.step > VAL_MAX_STEP) & (df.step % 24 < 6)]
    fr = test[test.isFraud == 1]
    transfers = fr[(fr.type == "TRANSFER") & (fr.amount >= fr.oldbalanceOrg) & (fr.oldbalanceOrg > 0)]
    for idx, t in transfers.iterrows():
        follow = fr[(fr.type == "CASH_OUT") & (fr.step == t.step) & (np.isclose(fr.amount, t.amount))
                    & (fr.index > idx)]
        if len(follow):
            break
    else:
        raise RuntimeError("no TRANSFER + CASH_OUT fraud pair found at night in the test period")
    normal = df[(df.step > VAL_MAX_STEP) & (df.isFraud == 0) & (df.index < idx)].tail(12)
    out = pd.concat([normal, df.loc[[idx]], df.loc[[follow.index[0]]]])
    return with_ids(out[RAW + ["isFraud"]], "S1-")


def story_mule_burst(df: pd.DataFrame) -> pd.DataFrame:
    """SYNTHETIC. PaySim has no mule accounts (no fraud recipient gets more than 2 payments), so we
    take 20 real legit test-period TRANSFERs from different senders and redirect them to one new
    recipient within 2 steps, keeping the recipient's balance consistent. Marked synthetic=1."""
    base = df[(df.step > VAL_MAX_STEP) & (df.type == "TRANSFER") & (df.isFraud == 0)
              & (df.amount < 50_000) & (df.oldbalanceOrg >= df.amount)]
    base = base.drop_duplicates("nameOrig").sample(20, random_state=SEED).sort_index().copy()
    step0 = int(base.step.min())
    base["step"] = [step0] * 10 + [step0 + 1] * 10
    base["newbalanceOrig"] = base.oldbalanceOrg - base.amount
    base["nameDest"] = "C_MULE_DEMO"
    bal = 0.0
    olds, news = [], []
    for a in base.amount:
        olds.append(round(bal, 2))
        bal += a
        news.append(round(bal, 2))
    base["oldbalanceDest"], base["newbalanceDest"] = olds, news
    base["isFraud"] = 1                      # the demo treats the burst as a mule pattern
    out = with_ids(base[RAW + ["isFraud"]], "S2-")
    out["synthetic"] = 1
    return out


def story_normal_day(df: pd.DataFrame) -> pd.DataFrame:
    """200 real ordinary test-period payments from one busy daytime step, all types."""
    test = df[(df.step > VAL_MAX_STEP) & (df.step % 24 >= 9) & (df.step % 24 <= 17)]
    step = int(test.step.value_counts().idxmax())
    out = df[(df.step == step) & (df.isFraud == 0)].head(200)
    return with_ids(out[RAW + ["isFraud"]], "S3-")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path")
    ap.add_argument("--skip-splits", action="store_true", help="only rebuild the demo files")
    args = ap.parse_args(argv)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    df = pd.read_csv(args.csv_path)
    print(f"loaded {len(df):,} rows in {time.time() - t0:.1f}s")
    summary = {"quality": quality_report(df)}

    if not args.skip_splits:
        t0 = time.time()
        feats = build_feature_frame(df)
        print(f"features ({len(ALL_FEATURES)}) for all rows in {time.time() - t0:.1f}s")
        summary["splits"] = make_splits(df, feats)
        print("splits:", summary["splits"])

    files = {
        "demo_stream.csv": demo_stream(df),
        "story_scam_drain.csv": story_scam_drain(df),
        "story_mule_burst.csv": story_mule_burst(df),
        "story_normal_day.csv": story_normal_day(df),
    }
    summary["demo_files"] = {}
    for name, part in files.items():
        part.to_csv(DEMO_DIR / name, index=False)
        summary["demo_files"][name] = {"rows": len(part), "fraud": int(part.isFraud.sum()),
                                       "steps": [int(part.step.min()), int(part.step.max())]}
        print(f"wrote {DEMO_DIR / name}: {summary['demo_files'][name]}")

    if args.skip_splits and (DEMO_DIR / "data_summary.json").exists():
        old = json.loads((DEMO_DIR / "data_summary.json").read_text())
        summary.setdefault("splits", old.get("splits"))
    (DEMO_DIR / "data_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
