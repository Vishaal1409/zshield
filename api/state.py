"""In-memory state store: per-account recent activity and seen recipients.

All features, including the history ones (new_recipient, sender_txn_count_recent,
recipient_inbound_count_recent), come from Balaa's compute_live_features(txn, state) in
features/features.py. Training uses the same function via build_feature_frame(), so training and
serving features match exactly. This store only holds the state dict and makes access thread-safe.
"""
import threading

from features.features import WINDOW_STEPS, compute_live_features


class StateStore:
    def __init__(self, window_steps: int = WINDOW_STEPS):
        self.window = window_steps
        self.lock = threading.Lock()
        self.data: dict = {}

    def build_features(self, txn: dict) -> dict:
        """Compute features for one payment, then record it. Thread-safe."""
        with self.lock:
            return compute_live_features(txn, self.data, self.window)

    def clear(self) -> None:
        with self.lock:
            self.data.clear()
