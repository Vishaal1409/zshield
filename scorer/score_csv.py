"""Batch CSV scorer (Module 2). Contains no model: the model is loaded from --model at runtime.

Run: python scorer/score_csv.py --model artifacts/ --input transactions.csv --output scored.csv
Output columns: transID, confidence_score, fraud_class (LOW / MEDIUM / HIGH)
"""
import argparse
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model.features import REQUIRED_COLUMNS  # noqa: E402
from model.predictor import FraudModel  # noqa: E402

ID_COLUMN = "txn_id"
CHUNK_ROWS = 500_000


def main():
    ap = argparse.ArgumentParser(description="Score a transactions CSV with an external ZShield model.")
    ap.add_argument("--model", required=True, help="Path to the artifacts folder or model.onnx")
    ap.add_argument("--input", required=True, help="Input transactions CSV")
    ap.add_argument("--output", required=True, help="Output CSV path")
    args = ap.parse_args()

    try:
        model = FraudModel.load(args.model)
    except (FileNotFoundError, ValueError) as e:
        sys.exit(f"ERROR: could not load model from '{args.model}': {e}")

    in_path = Path(args.input)
    if not in_path.is_file():
        sys.exit(f"ERROR: input file not found: {in_path}")

    header = pd.read_csv(in_path, nrows=0).columns
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        sys.exit(f"ERROR: input is missing required columns: {missing}")
    has_id = ID_COLUMN in header
    usecols = REQUIRED_COLUMNS + ([ID_COLUMN] if has_id else [])  # label columns are ignored

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    t0, total, counts = time.time(), 0, {"LOW": 0, "MEDIUM": 0, "HIGH": 0}

    for i, chunk in enumerate(pd.read_csv(in_path, usecols=usecols, chunksize=CHUNK_ROWS)):
        pred = model.predict(chunk)
        trans_id = chunk[ID_COLUMN].astype(str) if has_id else "T" + chunk.index.astype(str)
        out = pd.DataFrame({
            "transID": trans_id,
            "confidence_score": pred["confidence_score"].round(4),
            "fraud_class": pred["fraud_class"],
        })
        out.to_csv(out_path, mode="w" if i == 0 else "a", header=(i == 0), index=False)
        total += len(out)
        for k, v in out["fraud_class"].value_counts().items():
            counts[k] += int(v)
        print(f"  scored {total:,} rows", end="\r")

    print(f"\nWrote {total:,} rows to {out_path} in {time.time() - t0:.1f}s | {counts}")


if __name__ == "__main__":
    main()
