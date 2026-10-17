"""Scoring backends. The ONNX model is loaded ONCE at startup, never per request.

Handover contract expected from Joshua (agree with him, change here if his export differs):
  model/model.onnx            single float32 input of shape [1, n_features]
  model/feature_columns.json  JSON list of feature names, in the exact order of the model input
If either file is missing, the API runs the placeholder rule and reports scorer="placeholder_rule"
on /health, so we never claim a model that is not loaded.
"""
import json
import logging
from pathlib import Path

import numpy as np

log = logging.getLogger("zshield.model")
MODEL_DIR = Path(__file__).resolve().parent.parent / "model"


def placeholder_score(f: dict) -> float:
    """Rule used until the real model arrives, so the pipeline can run end to end."""
    score = 0.05
    if f.get("is_full_drain"):
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

    def score(self, f: dict) -> float:
        return placeholder_score(f)


class OnnxScorer:
    name = "onnx"

    def __init__(self, model_path: Path, columns: list):
        import onnxruntime as ort
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 1      # single small rows: threading only adds overhead
        opts.inter_op_num_threads = 1
        self.sess = ort.InferenceSession(str(model_path), sess_options=opts,
                                         providers=["CPUExecutionProvider"])
        self.columns = columns
        self.input_name = self.sess.get_inputs()[0].name
        outs = [o.name for o in self.sess.get_outputs()]
        self.prob_name = next((n for n in outs if "prob" in n.lower()), outs[-1])

    def score(self, f: dict) -> float:
        x = np.asarray([[float(f.get(c, 0.0)) for c in self.columns]], dtype=np.float32)
        out = self.sess.run([self.prob_name], {self.input_name: x})[0]
        if isinstance(out, list):                       # zipmap output: [{0: p0, 1: p1}]
            row = out[0]
            return float(row[1] if 1 in row else row["1"])
        out = np.asarray(out)
        return float(out[0, 1] if out.ndim == 2 and out.shape[1] > 1 else out.ravel()[0])


def load_scorer(model_dir: Path = MODEL_DIR):
    model_path = model_dir / "model.onnx"
    cols_path = model_dir / "feature_columns.json"
    if model_path.exists() and cols_path.exists():
        try:
            scorer = OnnxScorer(model_path, json.loads(cols_path.read_text()))
            log.info("Loaded ONNX model %s (%d features)", model_path, len(scorer.columns))
            return scorer
        except Exception:
            log.exception("ONNX model failed to load; using placeholder rule")
    elif model_path.exists():
        log.warning("model.onnx found but model/feature_columns.json missing; using placeholder rule")
    return PlaceholderScorer()
