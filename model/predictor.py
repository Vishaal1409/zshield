"""Portable predictor for the exported ZShield model (onnxruntime only, no xgboost needed).

Usage:
    from model.predictor import FraudModel
    fm = FraudModel.load("artifacts/")          # folder, or path to model.onnx
    result = fm.predict(df)                     # df has the raw PaySim columns
    # result columns: confidence_score (0-1), fraud_class (LOW / MEDIUM / HIGH)
"""
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pandas as pd

from model.features import FEATURES, SCORED_TYPES, build_features

MODEL_FILE = "model.onnx"
META_FILE = "model_meta.json"


def prior_correct(p_s: np.ndarray, beta: float) -> np.ndarray:
    """Undo negative undersampling: p = beta*p_s / (beta*p_s - p_s + 1)."""
    return beta * p_s / (beta * p_s - p_s + 1.0)


def classify(scores: np.ndarray, t_low: float, t_high: float) -> np.ndarray:
    """score < t_low -> LOW, t_low <= score < t_high -> MEDIUM, score >= t_high -> HIGH."""
    return np.where(scores >= t_high, "HIGH", np.where(scores >= t_low, "MEDIUM", "LOW"))


class FraudModel:
    def __init__(self, session: ort.InferenceSession, meta: dict):
        if meta.get("features") != FEATURES:
            raise ValueError("Model feature list does not match features.py; retrain or update code.")
        self.session = session
        self.meta = meta
        self.beta = float(meta["beta"])
        self.t_low = float(meta["t_low"])
        self.t_high = float(meta["t_high"])
        self._input_name = session.get_inputs()[0].name
        self._prob_output = next(o.name for o in session.get_outputs() if "prob" in o.name.lower())

    @classmethod
    def load(cls, path) -> "FraudModel":
        """Load from an artifacts folder or a model.onnx path (model_meta.json must sit next to it)."""
        if path is None or str(path).strip() == "":
            raise ValueError("A model path is required.")
        p = Path(path)
        if p.is_dir():
            onnx_path, meta_path = p / MODEL_FILE, p / META_FILE
        else:
            onnx_path, meta_path = p, p.parent / META_FILE
        if not onnx_path.is_file():
            raise FileNotFoundError(f"Model file not found: {onnx_path}")
        if not meta_path.is_file():
            raise FileNotFoundError(f"Model metadata not found: {meta_path}")

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        return cls(session, meta)

    def raw_scores(self, X: np.ndarray) -> np.ndarray:
        """Uncorrected model probability of fraud for a float32 feature matrix."""
        probs = self.session.run([self._prob_output], {self._input_name: X.astype(np.float32)})[0]
        return np.asarray(probs)[:, 1].astype(np.float64)

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score raw transactions. Returns confidence_score and fraud_class aligned with df.index."""
        scores = np.zeros(len(df), dtype=np.float64)
        # Rule: non-TRANSFER/CASH_OUT types never contain fraud in PaySim -> score 0.0 (LOW).
        mask = df["type"].isin(SCORED_TYPES).to_numpy()
        if mask.any():
            X = build_features(df.loc[mask]).to_numpy()
            scores[mask] = prior_correct(self.raw_scores(X), self.beta)
        return pd.DataFrame(
            {"confidence_score": scores, "fraud_class": classify(scores, self.t_low, self.t_high)},
            index=df.index,
        )
