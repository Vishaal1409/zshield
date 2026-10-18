"""Scoring backends. The ONNX model is loaded ONCE at startup, never per request.

Preferred: Joshua's trained model in artifacts/ (override with env ZSHIELD_MODEL_DIR):
  model.onnx        XGBoost exported to ONNX, float32 input in the order of meta["features"]
  model_meta.json   feature order, beta (prior correction), t_low / t_high, scored types
The score returned is the PRIOR-CORRECTED probability (same maths as model/predictor.py), and the
model's own cut-offs are used for the decision: score < t_low APPROVE, < t_high STEP_UP, else HOLD.
Types the model was not trained on (everything except TRANSFER and CASH_OUT) score 0.0, as in
model/predictor.py. This module needs only numpy and onnxruntime (no pandas), so it installs on s390x.

Fallbacks: legacy model/model.onnx + model/feature_columns.json, then the placeholder rule.
/health reports which one is live (scorer), so we never claim a model that is not loaded.
"""
import json
import logging
import os
from pathlib import Path

import numpy as np

log = logging.getLogger("zshield.model")
REPO = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = REPO / "artifacts"
MODEL_DIR = REPO / "model"          # legacy location


def placeholder_score(f: dict) -> float:
    """Rule used when no model is loaded, so the pipeline can still run end to end."""
    score = 0.05
    if f.get("full_drain"):
        score += 0.6
    if f.get("new_recipient"):
        score += 0.15
    if f.get("type_TRANSFER") or f.get("type_CASH_OUT"):
        score += 0.15
    if f.get("recipient_inbound_count_recent", 0) >= 5:      # mule burst
        score += 0.4
    if f.get("sender_txn_count_recent", 0) >= 10:            # rapid repeats from one account
        score += 0.2
    return min(score, 0.99)


class PlaceholderScorer:
    name = "placeholder_rule"
    thresholds = None          # use model/thresholds.json

    def score(self, f: dict) -> float:
        return placeholder_score(f)


def _prob_of_fraud(sess, input_name: str, prob_name: str, row) -> float:
    x = np.asarray([row], dtype=np.float32)
    out = sess.run([prob_name], {input_name: x})[0]
    if isinstance(out, list):                       # zipmap output: [{0: p0, 1: p1}]
        d = out[0]
        return float(d[1] if 1 in d else d["1"])
    out = np.asarray(out)
    return float(out[0, 1] if out.ndim == 2 and out.shape[1] > 1 else out.ravel()[0])


def _session(model_path: Path):
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 1      # one small row at a time: threads only add overhead
    opts.inter_op_num_threads = 1
    sess = ort.InferenceSession(str(model_path), sess_options=opts, providers=["CPUExecutionProvider"])
    outs = [o.name for o in sess.get_outputs()]
    prob = next((n for n in outs if "prob" in n.lower()), outs[-1])
    return sess, sess.get_inputs()[0].name, prob


class TrainedModelScorer:
    """artifacts/model.onnx + model_meta.json (Joshua's export)."""
    name = "onnx"

    def __init__(self, model_path: Path, meta: dict):
        from features.features import MODEL_FEATURES
        if meta.get("features") != MODEL_FEATURES:
            raise ValueError("model_meta.json features do not match features/features.py MODEL_FEATURES")
        self.columns = meta["features"]
        self.beta = float(meta["beta"])
        self.scored_types = tuple(meta.get("scored_types", ("TRANSFER", "CASH_OUT")))
        t_low, t_high = float(meta["t_low"]), float(meta["t_high"])
        if not (0.0 <= t_low < t_high <= 1.0):
            raise ValueError(f"bad model thresholds t_low={t_low} t_high={t_high}")
        self.thresholds = (t_low, t_high)
        self.version = meta.get("model_version", "")
        self.sess, self.input_name, self.prob_name = _session(model_path)

    def score(self, f: dict) -> float:
        if not any(f.get(f"type_{t}") for t in self.scored_types):
            return 0.0                                  # fraud never occurs in other types (PaySim)
        p_s = _prob_of_fraud(self.sess, self.input_name, self.prob_name,
                             [float(f[c]) for c in self.columns])
        return self.beta * p_s / (self.beta * p_s - p_s + 1.0)     # undo negative undersampling


class OnnxScorer:
    """Legacy: model/model.onnx + model/feature_columns.json, uncorrected probability, thresholds.json."""
    name = "onnx"
    thresholds = None

    def __init__(self, model_path: Path, columns: list):
        self.columns = columns
        self.sess, self.input_name, self.prob_name = _session(model_path)

    def score(self, f: dict) -> float:
        return _prob_of_fraud(self.sess, self.input_name, self.prob_name,
                              [float(f.get(c, 0.0)) for c in self.columns])


def load_scorer(model_dir=None):
    env = os.getenv("ZSHIELD_MODEL_DIR")
    explicit = Path(model_dir) if model_dir else (Path(env) if env else None)
    for d in ([explicit] if explicit else [ARTIFACTS_DIR, MODEL_DIR]):
        onnx, meta, cols = d / "model.onnx", d / "model_meta.json", d / "feature_columns.json"
        try:
            if onnx.exists() and meta.exists():
                s = TrainedModelScorer(onnx, json.loads(meta.read_text(encoding="utf-8")))
                log.info("Loaded trained model %s v%s (%d features, thresholds %s)",
                         onnx, s.version, len(s.columns), s.thresholds)
                return s
            if onnx.exists() and cols.exists():
                s = OnnxScorer(onnx, json.loads(cols.read_text()))
                log.info("Loaded legacy ONNX model %s (%d features)", onnx, len(s.columns))
                return s
            if onnx.exists():
                log.warning("%s found but no model_meta.json / feature_columns.json next to it", onnx)
        except Exception:
            log.exception("Model in %s failed to load; trying next option", d)
    log.warning("No usable model found; running the placeholder rule")
    return PlaceholderScorer()
