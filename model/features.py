"""Shared feature builder used by both training (train.py) and serving (predictor.py).

Only a subset of PaySim columns is used. Dropped: nameOrig, nameDest (IDs, privacy),
isFlaggedFraud (rule output, leaks the label), raw step (replaced by hour), isFraud (target).
"""
import numpy as np
import pandas as pd

# Raw columns the features are computed from (required in any input file).
REQUIRED_COLUMNS = [
    "step", "type", "amount",
    "oldbalanceOrg", "newbalanceOrig",
    "oldbalanceDest", "newbalanceDest",
]

# Transaction types the model scores. Fraud only ever occurs in these two.
SCORED_TYPES = ("TRANSFER", "CASH_OUT")

# Model input order. Must never change without retraining.
FEATURES = [
    "is_transfer",
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
    "err_bal_orig",
    "err_bal_dest",
    "full_drain",
    "amt_to_bal",
    "hour",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a float32 DataFrame with columns FEATURES, row-aligned with df."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Input is missing required columns: {missing}")

    amount = df["amount"].astype("float64")
    old_org = df["oldbalanceOrg"].astype("float64")
    new_org = df["newbalanceOrig"].astype("float64")
    old_dest = df["oldbalanceDest"].astype("float64")
    new_dest = df["newbalanceDest"].astype("float64")

    out = pd.DataFrame(index=df.index)
    out["is_transfer"] = (df["type"] == "TRANSFER").astype("int8")
    out["amount"] = amount
    out["oldbalanceOrg"] = old_org
    out["newbalanceOrig"] = new_org
    out["oldbalanceDest"] = old_dest
    out["newbalanceDest"] = new_dest
    out["err_bal_orig"] = new_org + amount - old_org
    out["err_bal_dest"] = old_dest + amount - new_dest
    out["full_drain"] = ((amount >= old_org) & (old_org > 0)).astype("int8")
    out["amt_to_bal"] = amount / (old_org + 1.0)
    out["hour"] = df["step"].astype("int64") % 24

    return out[FEATURES].astype(np.float32)
