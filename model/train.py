"""Train the ZShield fraud model (Module 1).

Pipeline: load -> filter TRANSFER/CASH_OUT -> time split by step -> balance train only
-> train XGBoost (+ LR baseline) -> prior-correct scores -> pick LOW/MEDIUM/HIGH thresholds
on validation -> evaluate on validation and test -> export ONNX + native model + metadata.

Run: python model/train.py --data PS_20174392719_1491204439457_log.csv --out artifacts/
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from onnxmltools import convert_xgboost  # noqa: E402
from onnxmltools.convert.common.data_types import FloatTensorType  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    average_precision_score, confusion_matrix, f1_score, fbeta_score, matthews_corrcoef,
    precision_recall_curve, precision_score, recall_score, roc_auc_score, roc_curve,
)
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402
from xgboost import XGBClassifier  # noqa: E402

from model.features import FEATURES, SCORED_TYPES, build_features  # noqa: E402
from model.predictor import FraudModel, classify, prior_correct  # noqa: E402

MODEL_VERSION = "1.0.0"
TRAIN_MAX_STEP, VAL_MAX_STEP = 500, 620  # train <= 500, val 501-620, test 621-743
BASELINE_COLUMNS = ["is_transfer", "amount", "oldbalanceOrg", "newbalanceOrig",
                    "oldbalanceDest", "newbalanceDest"]  # raw columns only, no engineered features

DTYPES = {
    "step": "int32", "type": "category", "amount": "float64",
    "oldbalanceOrg": "float64", "newbalanceOrig": "float64",
    "oldbalanceDest": "float64", "newbalanceDest": "float64", "isFraud": "int8",
}


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=list(DTYPES), dtype=DTYPES)
    df.insert(0, "txn_id", "T" + df.index.astype(str))
    return df


def balance(train: pd.DataFrame, neg_ratio: float, seed: int):
    """Keep all fraud, undersample non-fraud to neg_ratio : 1. Returns (balanced_df, beta)."""
    pos = train[train["isFraud"] == 1]
    neg = train[train["isFraud"] == 0]
    n_neg = min(len(neg), int(round(len(pos) * neg_ratio)))
    neg_s = neg.sample(n=n_neg, random_state=seed)
    beta = n_neg / len(neg)
    return pd.concat([pos, neg_s]).sample(frac=1.0, random_state=seed), beta


def pick_thresholds(scores, y, amount, c_stepup, c_hold, stepup_miss, n_grid=1000):
    """Grid-search t_low < t_high on validation minimising
    sum(amount of missed fraud) + c_stepup * #MEDIUM_legit + c_hold * #HIGH_legit,
    where missed fraud = all LOW fraud + stepup_miss * MEDIUM fraud."""
    cand = np.unique(np.concatenate([np.quantile(scores, np.linspace(0, 1, n_grid + 1)), [1.0 + 1e-9]]))
    order = np.argsort(scores)
    s_sorted = scores[order]
    fraud_amt = np.where(y[order] == 1, amount[order], 0.0)
    legit = (y[order] == 0).astype(np.float64)
    cum_fa = np.concatenate([[0.0], np.cumsum(fraud_amt)])
    cum_l = np.concatenate([[0.0], np.cumsum(legit)])
    idx = np.searchsorted(s_sorted, cand, side="left")  # rows with score < cand
    fa_below, l_below = cum_fa[idx], cum_l[idx]
    total_l = cum_l[-1]

    a, b = np.meshgrid(np.arange(len(cand)), np.arange(len(cand)), indexing="ij")
    fa_low = fa_below[a]
    fa_med = fa_below[b] - fa_below[a]
    l_med = l_below[b] - l_below[a]
    l_high = total_l - l_below[b]
    cost = fa_low + stepup_miss * fa_med + c_stepup * l_med + c_hold * l_high
    cost = np.where(b > a, cost, np.inf)
    i, j = np.unravel_index(np.argmin(cost), cost.shape)
    return float(cand[i]), float(cand[j]), float(cost[i, j])


def best_f1_threshold(y, s):
    p, r, t = precision_recall_curve(y, s)
    f1 = 2 * p[:-1] * r[:-1] / np.clip(p[:-1] + r[:-1], 1e-12, None)
    return float(t[np.argmax(f1)])


def point_metrics(y, s, thr):
    pred = (s >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "threshold": thr,
        "f1": f1_score(y, pred, zero_division=0),
        "f2": fbeta_score(y, pred, beta=2, zero_division=0),
        "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred, zero_division=0),
        "mcc": matthews_corrcoef(y, pred),
        "false_positive_rate": fp / max(fp + tn, 1),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def evaluate(y, s, f1_thr, t_low, t_high):
    fpr, tpr, _ = roc_curve(y, s)
    p, r, _ = precision_recall_curve(y, s)
    bands = classify(s, t_low, t_high)
    band_stats = {}
    for b in ("LOW", "MEDIUM", "HIGH"):
        m = bands == b
        band_stats[b] = {"count": int(m.sum()), "fraud": int(y[m].sum()),
                         "fraud_rate": float(y[m].mean()) if m.any() else 0.0}
    return {
        "rows": int(len(y)), "fraud": int(y.sum()),
        "pr_auc": average_precision_score(y, s),
        "roc_auc": roc_auc_score(y, s),
        "recall_at_fpr_0.1pct": float(tpr[fpr <= 0.001].max()),
        "recall_at_fpr_1pct": float(tpr[fpr <= 0.01].max()),
        "precision_at_recall_90pct": float(p[r >= 0.9].max()),
        "at_best_f1_threshold": point_metrics(y, s, f1_thr),
        "at_t_high": point_metrics(y, s, t_high),
        "bands": band_stats,
    }


def to_native(o):
    if isinstance(o, dict):
        return {k: to_native(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_native(v) for v in o]
    if isinstance(o, np.generic):
        return o.item()
    return o


def print_report(name, m):
    f = m["at_best_f1_threshold"]
    print(f"  {name:<22} PR-AUC {m['pr_auc']:.4f} | ROC-AUC {m['roc_auc']:.4f} | "
          f"F1 {f['f1']:.4f} | F2 {f['f2']:.4f} | P {f['precision']:.4f} | R {f['recall']:.4f} | "
          f"MCC {f['mcc']:.4f} | R@FPR0.1% {m['recall_at_fpr_0.1pct']:.4f}")


def main():
    ap = argparse.ArgumentParser(description="Train the ZShield fraud model.")
    ap.add_argument("--data", required=True, help="PaySim CSV path")
    ap.add_argument("--out", required=True, help="Artifacts output folder")
    ap.add_argument("--neg_ratio", type=float, default=1.0, help="Non-fraud : fraud ratio in train")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--c_stepup", type=float, default=10.0, help="Friction cost per legit STEP-UP")
    ap.add_argument("--c_hold", type=float, default=50.0, help="Friction cost per legit HOLD")
    ap.add_argument("--stepup_miss", type=float, default=0.5,
                    help="Share of MEDIUM fraud the step-up check fails to stop")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    # 1. Load
    df = load(args.data)
    print(f"Loaded {len(df):,} rows, {int(df['isFraud'].sum()):,} fraud ({time.time() - t0:.1f}s)")

    # 2. Keep scored types only
    df = df[df["type"].isin(SCORED_TYPES)].copy()
    print(f"TRANSFER + CASH_OUT: {len(df):,} rows, {int(df['isFraud'].sum()):,} fraud")

    # 3. Time split
    train = df[df["step"] <= TRAIN_MAX_STEP]
    val = df[(df["step"] > TRAIN_MAX_STEP) & (df["step"] <= VAL_MAX_STEP)]
    test = df[df["step"] > VAL_MAX_STEP]

    # 4. Balance train only
    train_bal, beta = balance(train, args.neg_ratio, args.seed)
    for n, d in (("train (balanced)", train_bal), ("validation", val), ("test", test)):
        print(f"  {n:<17} {len(d):>9,} rows, {int(d['isFraud'].sum()):>6,} fraud")
    print(f"  beta (negative sampling rate) = {beta:.6f}")

    X_tr, y_tr = build_features(train_bal).to_numpy(), train_bal["isFraud"].to_numpy()
    X_va, y_va = build_features(val).to_numpy(), val["isFraud"].to_numpy()
    X_te, y_te = build_features(test).to_numpy(), test["isFraud"].to_numpy()

    # 5. Train XGBoost
    clf = XGBClassifier(
        objective="binary:logistic", n_estimators=600, learning_rate=0.05, max_depth=6,
        subsample=0.8, colsample_bytree=0.8, tree_method="hist", eval_metric="logloss",
        early_stopping_rounds=50, n_jobs=-1, random_state=args.seed,
    )
    clf.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], verbose=False)
    print(f"XGBoost trained, best iteration {clf.best_iteration}")

    # LR baseline on raw columns only
    bcols = [FEATURES.index(c) for c in BASELINE_COLUMNS]
    lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    lr.fit(X_tr[:, bcols], y_tr)

    # 6. Prior-corrected scores
    s_va = prior_correct(clf.predict_proba(X_va)[:, 1], beta)
    s_te = prior_correct(clf.predict_proba(X_te)[:, 1], beta)
    b_va = prior_correct(lr.predict_proba(X_va[:, bcols])[:, 1], beta)
    b_te = prior_correct(lr.predict_proba(X_te[:, bcols])[:, 1], beta)

    # 7. Thresholds on validation
    t_low, t_high, best_cost = pick_thresholds(
        s_va, y_va, val["amount"].to_numpy(), args.c_stepup, args.c_hold, args.stepup_miss)
    print(f"Thresholds: t_low={t_low:.6f}, t_high={t_high:.6f} (val cost {best_cost:,.0f})")
    f1_thr = best_f1_threshold(y_va, s_va)
    bf1_thr = best_f1_threshold(y_va, b_va)

    # 8. Evaluate on validation and test (thresholds fixed from validation)
    metrics = {
        "validation": {"xgboost": evaluate(y_va, s_va, f1_thr, t_low, t_high),
                       "lr_baseline": evaluate(y_va, b_va, bf1_thr, t_low, t_high)},
        "test": {"xgboost": evaluate(y_te, s_te, f1_thr, t_low, t_high),
                 "lr_baseline": evaluate(y_te, b_te, bf1_thr, t_low, t_high)},
    }
    for split in ("validation", "test"):
        print(f"[{split}]")
        print_report("XGBoost", metrics[split]["xgboost"])
        print_report("LR baseline", metrics[split]["lr_baseline"])
        print("  bands:", {k: (v["count"], v["fraud"]) for k, v in metrics[split]["xgboost"]["bands"].items()})

    # 9. Export
    clf.save_model(out / "model.json")
    onx = convert_xgboost(clf, initial_types=[("input", FloatTensorType([None, len(FEATURES)]))])
    (out / "model.onnx").write_bytes(onx.SerializeToString())

    meta = {
        "model_type": "xgboost.XGBClassifier",
        "model_version": MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "features": FEATURES,
        "scored_types": list(SCORED_TYPES),
        "t_low": t_low, "t_high": t_high, "beta": beta,
        "classes": {"LOW": "score < t_low", "MEDIUM": "t_low <= score < t_high", "HIGH": "score >= t_high"},
        "threshold_cost": {"c_stepup": args.c_stepup, "c_hold": args.c_hold, "stepup_miss": args.stepup_miss},
        "split": {"train_steps": f"1-{TRAIN_MAX_STEP}", "val_steps": f"{TRAIN_MAX_STEP + 1}-{VAL_MAX_STEP}",
                  "test_steps": f"{VAL_MAX_STEP + 1}-743", "neg_ratio": args.neg_ratio, "seed": args.seed},
        "test_summary": {k: metrics["test"]["xgboost"][k] for k in ("pr_auc", "roc_auc")}
        | {"f1": metrics["test"]["xgboost"]["at_best_f1_threshold"]["f1"]},
    }
    (out / "model_meta.json").write_text(json.dumps(to_native(meta), indent=2), encoding="utf-8")

    # ONNX vs native parity on 10k test rows
    fm = FraudModel.load(out)
    n = min(10_000, len(X_te))
    diff = float(np.max(np.abs(fm.raw_scores(X_te[:n]) - clf.predict_proba(X_te[:n])[:, 1])))
    metrics["onnx_vs_native_max_abs_diff"] = diff
    print(f"ONNX vs native max abs diff on {n:,} rows: {diff:.2e}")

    (out / "metrics.json").write_text(json.dumps(to_native(metrics), indent=2), encoding="utf-8")
    print(f"Artifacts written to {out.resolve()} ({time.time() - t0:.1f}s total)")


if __name__ == "__main__":
    main()
