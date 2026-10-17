"""In-memory state store: per-account recent activity and seen recipients.

Features come from Balaa's compute_live_features(txn, state) (features/features.py). That function
owns the keys it puts in `data` (e.g. "seen_pairs"). This store ALSO tracks short-window activity
and adds two history features IF compute_live_features did not already provide them:
  - sender_txn_count_recent        payments by this sender in the last WINDOW steps (before this one)
  - recipient_inbound_count_recent payments INTO this recipient in the last WINDOW steps (before this one)
Both use past events only (the current payment is added AFTER the features are computed).
TODO: agree the final names/window with Balaa so training and serving match exactly.
"""
import os
import threading
from collections import defaultdict, deque

from features.features import compute_live_features

WINDOW_STEPS = int(os.getenv("ZSHIELD_WINDOW_STEPS", "6"))


class StateStore:
    def __init__(self, window_steps: int = WINDOW_STEPS):
        self.window = window_steps
        self.lock = threading.Lock()
        self.data: dict = {}
        self._sender = defaultdict(deque)
        self._dest = defaultdict(deque)

    def _count_recent(self, dq: deque, step: int) -> int:
        while dq and dq[0] <= step - self.window:
            dq.popleft()
        return len(dq)

    def build_features(self, txn: dict) -> dict:
        """Compute features for one payment, then record it. Thread-safe."""
        step = int(txn["step"])
        with self.lock:
            f = compute_live_features(txn, self.data)
            s_dq = self._sender[txn["nameOrig"]]
            d_dq = self._dest[txn["nameDest"]]
            f.setdefault("sender_txn_count_recent", self._count_recent(s_dq, step))
            f.setdefault("recipient_inbound_count_recent", self._count_recent(d_dq, step))
            s_dq.append(step)
            d_dq.append(step)
        return f

    def clear(self) -> None:
        with self.lock:
            self.data.clear()
            self._sender.clear()
            self._dest.clear()
