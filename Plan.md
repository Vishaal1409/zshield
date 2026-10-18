# Plan.md — ZShield ML Pipeline (Model + Batch Scoring Wrapper)

## Context
ZShield needs a fraud model that scores each PaySim transaction 0–1 and buckets it into LOW / MEDIUM / HIGH (→ APPROVE / STEP_UP / HOLD in the API). Two separate modules are needed: (1) a trained, **exportable** model that the API and UI can load, and (2) a **standalone wrapper** that takes an external model path plus an input CSV and writes a results CSV. The model is never bundled inside module 2.

Dataset: `PS_20174392719_1491204439457_log.csv` (PaySim, ~6.36M rows, columns: `step,type,amount,nameOrig,oldbalanceOrg,newbalanceOrig,nameDest,oldbalanceDest,newbalanceDest,isFraud,isFlaggedFraud`). No transaction ID column, so one is generated.

## Algorithm choice: XGBoost (`XGBClassifier`, `binary:logistic`)
- Outputs a probability in [0, 1] → used directly as the confidence score.
- Clean ONNX export (`onnxmltools`), runs in `onnxruntime`, and has s390x builds, so it works for IBM Z / LinuxONE.
- Native SHAP support (`TreeExplainer`) for the top 3 reasons later.
- Early stopping on validation **log-loss** (not PR-AUC: PR-AUC saturates at 1.0 within a few trees, which stops training too early and squashes the scores toward 0).

## Variables used (subset only)
| Kept / engineered | Dropped (and why) |
|---|---|
| `type` → `is_transfer` (0/1) | `nameOrig`, `nameDest`: IDs, high cardinality, privacy |
| `amount`, `oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, `newbalanceDest` | `isFlaggedFraud`: rule output, leaks the label |
| `err_bal_orig = newbalanceOrig + amount − oldbalanceOrg` | raw `step`: replaced by `hour` |
| `err_bal_dest = oldbalanceDest + amount − newbalanceDest` | `isFraud`: target only |
| `full_drain = (amount ≥ oldbalanceOrg) & (oldbalanceOrg > 0)` | |
| `amt_to_bal = amount / (oldbalanceOrg + 1)` | |
| `hour = step % 24` | |

Fraud exists only in `TRANSFER` and `CASH_OUT`, so the model trains on those two types only. Other types get score `0.0` → LOW through a documented rule in the predictor.

## Balanced training set (pipeline)
1. Load the CSV with pandas using explicit dtypes. Add `txn_id = "T" + row_index`.
2. Keep only `TRANSFER` and `CASH_OUT` rows.
3. **Time split by `step`**: train ≤ 500, val 501–620, test 621–743. Split first, then balance, so nothing leaks across.
4. **Balance only the train split**: keep all fraud rows and randomly undersample non-fraud to a configurable ratio (default 1:1, `--neg_ratio`, fixed seed).
5. Val and test keep the **natural** class ratio, so the metrics are honest.
6. Prior correction to recalibrate undersampled scores back to real-world probabilities: `p = β·p_s / (β·p_s − p_s + 1)`, where β is the negative sampling rate. β is saved in the metadata.

## Thresholds (LOW / MEDIUM / HIGH)
On validation, run a grid search over `t_low < t_high` and minimise the cost
`Σ amount(missed fraud) + c_stepup·#MEDIUM_legit + c_hold·#HIGH_legit` (friction costs are configurable; defaults `c_stepup=10`, `c_hold=50`).
"Missed fraud" = all LOW fraud + `stepup_miss` × MEDIUM fraud (default 0.5, `--stepup_miss`): the step-up check does not stop every scam. Without this term, HIGH can never cost less than MEDIUM and would always be empty.
`score < t_low` → LOW, `t_low ≤ score < t_high` → MEDIUM, `score ≥ t_high` → HIGH.

## Module 1: `model/` (training and exportable model)
```
model/
  features.py      # build_features(df) -> DataFrame[FEATURES]; shared by training + serving
  train.py         # load → split → balance → train → calibrate → thresholds → export
  predictor.py     # FraudModel.load(path); .predict(df) -> score, class  (onnxruntime only)
  requirements.txt # pinned: pandas, numpy, xgboost, scikit-learn, onnx, onnxmltools, onnxruntime
```
**Artifacts** (written to `--out artifacts/`; this is the external model folder):
- `model.onnx`: portable model for the API and IBM Z
- `model.json`: native XGBoost model (for SHAP and retraining)
- `model_meta.json`: feature order, `t_low`, `t_high`, β, model version, train date, metrics

**Eval report** (`artifacts/metrics.json`): PR-AUC, recall at FPR = 0.1% / 1%, precision at recall 90%, confusion matrix on test, and a logistic-regression baseline for comparison. Accuracy is not reported.

**Validation-set evaluation** (added on request): the validation split (steps 501–620, natural class ratio) is used to test the model. These metrics are reported for **both validation and test**, for XGBoost and the LR baseline:
- F1, precision, recall at the best-F1 threshold (and at `t_high`)
- F2 (recall-weighted F-score), PR-AUC (average precision), ROC-AUC, MCC
- Confusion matrix and LOW / MEDIUM / HIGH counts with the fraud rate in each band

They are printed to the console and saved under `"validation"` and `"test"` in `metrics.json`.

Run: `python model/train.py --data PS_...log.csv --out artifacts/`

## Module 2: `scorer/` (batch CSV wrapper)
```
scorer/
  score_csv.py     # CLI only; no model inside
```
- **Required args:** `--model <path to artifacts folder or model.onnx>`, `--input <csv>`, `--output <csv>`. It errors out if `--model` is missing or invalid; there is no default model path.
- Loads `model.onnx` + `model_meta.json` from the given path via `model.predictor.FraudModel.load()`.
- Reads the input in chunks (handles the full 6.3M-row file), builds features with the shared `features.py`, and scores.
- Uses `txn_id` if the input has it, otherwise generates `T<row_index>`.
- Checks the input schema: required columns must be present and the label columns are ignored.
- **Output CSV:** `transID,confidence_score,fraud_class` (score rounded to 4 decimals; class ∈ LOW/MEDIUM/HIGH).

Run: `python scorer/score_csv.py --model artifacts/ --input PS_...log.csv --output scored.csv`

## Verification
1. `train.py` completes, and the artifacts plus `metrics.json` exist. The model beats the LR baseline on PR-AUC.
2. ONNX vs native XGBoost predictions match (max abs diff < 1e-5) on 10k test rows.
3. `score_csv.py` with no `--model` → clear error. With a wrong path → clear error.
4. Score the full CSV and check: row count matches the input, scores are in [0, 1], the class distribution is sensible (most rows LOW), and fraud rows are concentrated in HIGH.
5. Feature parity check: `features.py` gives the same output for the same row in training and in scoring.

## Deliverable
After approval, this plan is saved as `Plan.md` in the project root (`IBM Z Shield/`), and the modules are built to match it.
