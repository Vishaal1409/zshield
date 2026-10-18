# ZShield ML Pipeline: Context for Coding Agents

What was built, how it works, and why each choice was made. Read this before you change anything in `model/` or `scorer/`. [Plan.md](Plan.md) is the spec. The user's standing rule is to **follow Plan.md exactly**. If a change is needed, update Plan.md first and tell the user.

---

## 1. Purpose

ZShield is a real-time fraud interception system (IBM Z Datathon, Challenge 1). This repo part is the **ML layer**:

- **Module 1 (`model/`)** trains an XGBoost fraud model on PaySim and exports it as a portable artifact that backends and UIs can load.
- **Module 2 (`scorer/`)** is a CLI wrapper. It takes an **external** model path plus an input CSV and writes a scored CSV. It contains no model.

Every transaction gets a `confidence_score` in [0, 1] and a `fraud_class` in {LOW, MEDIUM, HIGH}. For the API, the classes map to APPROVE / STEP_UP / HOLD.

---

## 2. Repository layout

```
IBM Z Shield/
├── PS_20174392719_1491204439457_log.csv   # PaySim dataset, ~470 MB. Never commit.
├── Plan.md                                # Approved spec (source of truth)
├── explanation.md                         # This file
├── .venv/                                 # Local virtualenv (Python 3.13.7). Never commit.
├── model/                                 # MODULE 1
│   ├── __init__.py
│   ├── features.py                        # Shared feature builder (training + serving)
│   ├── train.py                           # Full training pipeline + export
│   ├── predictor.py                       # FraudModel loader/predictor (onnxruntime only)
│   └── requirements.txt                   # Pinned dependencies
├── scorer/                                # MODULE 2
│   └── score_csv.py                       # Batch CSV scoring CLI
├── artifacts/                             # Output of train.py = the external model folder
│   ├── model.onnx                         # Portable model (API / IBM Z)
│   ├── model.json                         # Native XGBoost model (SHAP, retraining)
│   ├── model_meta.json                    # Feature order, thresholds, beta, version
│   └── metrics.json                       # Full validation + test evaluation
└── scored.csv                             # Output of scorer on the full dataset (109 MB). Never commit.
```

Not a git repo yet. If one is created, add `.venv/`, `*.csv`, `scored.csv` and probably `artifacts/model.json` (large) to `.gitignore`.

---

## 3. Environment

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r model/requirements.txt   # Windows path; use .venv/bin/python on Linux/s390x
```

Pinned versions: `numpy 2.5.4, pandas 3.0.6, scikit-learn 1.9.1, xgboost 3.4.1, onnx 1.23.2, onnxmltools 1.16.0, onnxruntime 1.31.0`.

- **Training** needs all of the packages above.
- **Inference** (`predictor.py`, `score_csv.py`) only needs `numpy`, `pandas`, `onnxruntime`. xgboost is NOT needed at serving time. This matters on IBM Z / LinuxONE, where xgboost may not install.

---

## 4. Dataset facts (PaySim)

- 6,362,620 rows, 8,213 fraud (~0.13%).
- Columns: `step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig, nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud`.
- `step` is an hour index (1–743). Activity drops sharply after about step 400, so the later splits are small.
- **Fraud only appears in `TRANSFER` and `CASH_OUT`.** `PAYMENT`, `CASH_IN` and `DEBIT` have 0 fraud.
- There is **no transaction ID column**. The pipeline generates `txn_id = "T" + <0-based row index of the original file>`. Training and scoring use the same rule, so IDs line up.

---

## 5. Module 1: how training works (`model/train.py`)

Run:
```bash
.venv/Scripts/python model/train.py --data PS_20174392719_1491204439457_log.csv --out artifacts/
```
CLI options (defaults): `--neg_ratio 1.0`, `--seed 42`, `--c_stepup 10`, `--c_hold 50`, `--stepup_miss 0.5`. It runs in about 12 seconds on a 16-core laptop.

### Steps, in order
1. **Load** with explicit dtypes and `usecols` (drops `nameOrig`, `nameDest`, `isFlaggedFraud` at read time), then add `txn_id`.
2. **Filter** to `TRANSFER` + `CASH_OUT` → 2,770,409 rows, all 8,213 fraud.
3. **Time split by `step`**, never random: train ≤ 500, validation 501–620, test 621–743.
4. **Balance the train split only**: keep all fraud (5,561) and randomly undersample non-fraud 1:1 (5,561) → 11,122 rows. Validation (86,155 rows / 1,286 fraud) and test (38,475 / 1,366) keep the **natural** class ratio, so their metrics are honest.
5. **Build features** with `features.build_features()` (Section 7).
6. **Train XGBoost**: `n_estimators=600, learning_rate=0.05, max_depth=6, subsample=0.8, colsample_bytree=0.8, tree_method="hist"`, with early stopping (50 rounds) on **validation log-loss**. The best iteration was 591.
7. **Train the LR baseline**: `StandardScaler + LogisticRegression` on raw columns only (`is_transfer, amount`, the 4 balances), on the same balanced train set. It is the "before" comparison.
8. **Prior correction**: undersampling inflates probabilities, so scores are mapped back to real-world probabilities with
   `p = β·p_s / (β·p_s − p_s + 1)`, where `β = kept_negatives / total_train_negatives` (= 0.002106).
   All thresholds and reported scores use **corrected** scores.
9. **Pick thresholds** on validation (Section 8).
10. **Evaluate** XGBoost and the baseline on validation and test (Section 9).
11. **Export** `model.json` (native), `model.onnx` (via `onnxmltools.convert_xgboost`), `model_meta.json` and `metrics.json`.
12. **Parity check**: reload through `FraudModel` and compare ONNX vs native on 10k test rows. The max abs diff is 5.3e-07, under the plan's 1e-5 tolerance.

---

## 6. Module 1: loading the model from other systems (`model/predictor.py`)

```python
import sys; sys.path.insert(0, "<project root>")
from model.predictor import FraudModel

fm = FraudModel.load("artifacts/")        # folder, OR path to model.onnx (meta must be beside it)
out = fm.predict(df)                      # df = pandas DataFrame with raw PaySim columns
# out: DataFrame indexed like df, columns: confidence_score (float 0-1), fraud_class (LOW/MEDIUM/HIGH)
```

Behaviour:
- `load()` raises `ValueError` for an empty path and `FileNotFoundError` if `model.onnx` or `model_meta.json` is missing. It raises `ValueError` if `meta["features"]` doesn't match `features.FEATURES`, which catches a stale model or changed code.
- `predict()` gives rows whose `type` is not TRANSFER/CASH_OUT a score of **0.0 → LOW** (a documented rule, not the model). Other rows go through `build_features → ONNX → prior_correct → classify`.
- `raw_scores(X)` returns uncorrected ONNX probabilities for a float32 matrix. It is used for the parity check.
- Helpers: `prior_correct(p_s, beta)`, `classify(scores, t_low, t_high)`.
- ONNX signature: input `"input"`, float32 `[N, 11]`. Outputs `"label"` `[N]` and `"probabilities"` `[N, 2]` (column 1 = fraud). The predictor finds the output whose name contains "prob".
- Required input columns: `step, type, amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest`. `nameOrig`, `nameDest`, `isFraud` and `isFlaggedFraud` are ignored if present.

To score a single transaction from an API, wrap it in a one-row DataFrame: `fm.predict(pd.DataFrame([txn_dict]))`. The team API contract fields (`txn_id, step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig, nameDest, oldbalanceDest, newbalanceDest`) already cover the required columns. Load the model **once at startup**, not per request.

---

## 7. Features (`model/features.py`): the only place features are defined

`FEATURES` (exact model input order, saved in meta):

| # | Feature | Definition |
|---|---|---|
| 0 | `is_transfer` | 1 if `type == "TRANSFER"`, else 0 (CASH_OUT) |
| 1 | `amount` | raw |
| 2 | `oldbalanceOrg` | raw |
| 3 | `newbalanceOrig` | raw |
| 4 | `oldbalanceDest` | raw |
| 5 | `newbalanceDest` | raw |
| 6 | `err_bal_orig` | `newbalanceOrig + amount − oldbalanceOrg` |
| 7 | `err_bal_dest` | `oldbalanceDest + amount − newbalanceDest` |
| 8 | `full_drain` | 1 if `amount ≥ oldbalanceOrg` and `oldbalanceOrg > 0` |
| 9 | `amt_to_bal` | `amount / (oldbalanceOrg + 1)` |
| 10 | `hour` | `step % 24` |

Dropped columns and why: `nameOrig` / `nameDest` (IDs, high cardinality, privacy), `isFlaggedFraud` (output of an existing rule, leaks the label), raw `step` (replaced by `hour`; still used for the split), `isFraud` (the target).

Every feature uses only the current row, so there is no look-ahead leakage and training and serving match by construction (one shared function). **If you add or reorder features, you must retrain.** The meta check in `FraudModel` refuses a mismatched model.

---

## 8. LOW / MEDIUM / HIGH thresholds

- `score < t_low` → LOW (APPROVE) · `t_low ≤ score < t_high` → MEDIUM (STEP_UP) · `score ≥ t_high` → HIGH (HOLD)
- Chosen on **validation** by a grid search (about 1,000 quantile candidates, vectorised over all pairs) that minimises:
  `cost = Σ amount(LOW fraud) + stepup_miss·Σ amount(MEDIUM fraud) + c_stepup·#MEDIUM_legit + c_hold·#HIGH_legit`
- Current values: `t_low = 0.000104`, `t_high = 0.000174`.
- These are tiny because PaySim fraud amounts run into the millions, so missing even rare fraud costs far more than friction. Raise `--c_stepup` / `--c_hold` to widen MEDIUM and shrink HIGH.

---

## 9. Evaluation (`artifacts/metrics.json`)

Structure: `metrics[split][model]` with `split ∈ {validation, test}` and `model ∈ {xgboost, lr_baseline}`, plus `onnx_vs_native_max_abs_diff`.
Each entry contains: `rows, fraud, pr_auc, roc_auc, recall_at_fpr_0.1pct, recall_at_fpr_1pct, precision_at_recall_90pct`, then `at_best_f1_threshold` and `at_t_high`, each with `{threshold, f1, f2, precision, recall, mcc, false_positive_rate, confusion_matrix{tn,fp,fn,tp}}`, and `bands{LOW,MEDIUM,HIGH: count, fraud, fraud_rate}`.
The best-F1 threshold is chosen on validation and applied unchanged to test.

Current results:

| | PR-AUC | ROC-AUC | F1 | F2 | Precision | Recall | MCC |
|---|---|---|---|---|---|---|---|
| XGBoost, validation | 1.0000 | 1.0000 | 0.9992 | 0.9992 | 0.9992 | 0.9992 | 0.9992 |
| XGBoost, test | 1.0000 | 1.0000 | 0.9993 | 0.9988 | 1.0000 | 0.9985 | 0.9992 |
| LR baseline, test | 0.7517 | 0.9578 | 0.6739 | 0.5930 | 0.8721 | 0.5490 | 0.6836 |

Test confusion matrix (XGBoost, best-F1 threshold): tn 37,109 · fp 0 · fn 2 · tp 1,364.

**Accuracy is deliberately not reported** (Plan.md). Calling every payment honest already scores 96–98% here, so accuracy can't tell a useless model from a good one. Computed on request: XGBoost 99.995% on test, against 96.45% for "always honest". The user was asked whether to add accuracy to `metrics.json` and has not decided.

**Caveat for any write-up:** the near-perfect scores come mostly from the balance-mismatch features (`err_bal_*`), a known flaw in how PaySim generates its data. Do not present them as real-world performance.

---

## 10. Module 2: batch scorer (`scorer/score_csv.py`)

```bash
.venv/Scripts/python scorer/score_csv.py --model artifacts/ --input <transactions.csv> --output <scored.csv>
```
- `--model`, `--input` and `--output` are **all required**. There is no default model path, and the model is never bundled inside this module (a hard user requirement).
- Loads through `FraudModel.load()`. On a bad path it exits with `ERROR: could not load model from ...`.
- Checks the input header against `REQUIRED_COLUMNS`. Reads only the needed columns, so label columns are ignored.
- Streams the input in chunks of 500k rows and appends to the output, which keeps memory bounded on the full 6.3M-row file (about 31 seconds).
- `transID` = the input's `txn_id` column if present, else `"T" + <0-based row index>`.
- Output columns: `transID, confidence_score, fraud_class`. The score is rounded to 4 decimals for output only; classification uses the unrounded score.

Full-dataset result: LOW 6,345,860 · MEDIUM 3,653 · HIGH 13,107. All 8,213 fraud rows are in HIGH (and 4,894 honest payments too). The median fraud score is 0.97.

---

## 11. Changes made during the build (all recorded in Plan.md)

1. **`stepup_miss` added to the threshold cost.** As first written, fraud in MEDIUM counted as fully caught, so HIGH could never cost less than MEDIUM and was always empty. "Missed fraud" now includes `stepup_miss` × MEDIUM fraud (default 0.5).
2. **Early stopping on log-loss, not PR-AUC.** PR-AUC saturated at 1.0 almost immediately, so training stopped at iteration 23 and every corrected score stayed below 0.012. Log-loss lets it train to iteration 591, which gives a sensible score spread.
3. **Validation-set evaluation added** at the user's request: F1, F2, precision, recall, MCC, PR-AUC, ROC-AUC, confusion matrices and band stats for validation and test.

---

## 12. Verification already done

| Check | Result |
|---|---|
| `train.py` runs, writes all 4 artifacts | ✅ |
| XGBoost beats the LR baseline on PR-AUC | ✅ 1.0000 vs 0.7517 (test) |
| ONNX vs native diff < 1e-5 | ✅ 5.3e-07 |
| Scorer without `--model` | ✅ argparse error |
| Scorer with a wrong model path | ✅ clear error, exit |
| Output row count = input row count; IDs match the row index | ✅ 6,362,620 |
| Scores in [0, 1] | ✅ 0.0 – 0.9968 |
| Fraud concentrated in HIGH | ✅ 8,213 / 8,213 |
| Feature parity (same row alone vs inside a batch) | ✅ identical |

---

## 13. Open items / next steps (not done)

- The user asked for the model "in an exportable .bat or similar file type". This is **undecided**: the options are `.bat` launcher scripts, a single-file model bundle, or a standalone PyInstaller `.exe`. Ask the user before building any of them.
- Whether to add accuracy to `metrics.json` (waiting on the user).
- SHAP top-3 reasons (`explain.py`, using `artifacts/model.json` + `shap.TreeExplainer`) is in the team plan but not in this Plan.md.
- No FastAPI integration yet. Use `FraudModel` as shown in Section 6.
- IBM Z / LinuxONE: `onnxruntime` + `pandas` are enough for inference there. Not yet tested on s390x.
