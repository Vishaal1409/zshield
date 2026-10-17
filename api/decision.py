"""Decision engine: thresholds -> APPROVE / STEP_UP / HOLD, plus rule-based reasons.

Fail-safe rule (Responsible AI): if scoring fails for any reason the decision is STEP_UP,
never a silent approve.
"""
import json
import logging
from pathlib import Path

log = logging.getLogger("zshield.decision")
THRESHOLDS_PATH = Path(__file__).resolve().parent.parent / "model" / "thresholds.json"
DEFAULTS = {"step_up": 0.5, "hold": 0.9}

FAILSAFE_SCORE = 0.5
FAILSAFE_REASON = "Scoring unavailable, extra check applied"


class Thresholds:
    def __init__(self, step_up: float, hold: float):
        self.step_up = step_up
        self.hold = hold

    @classmethod
    def load(cls, path: Path = THRESHOLDS_PATH) -> "Thresholds":
        try:
            raw = json.loads(Path(path).read_text())
            step_up, hold = float(raw["step_up"]), float(raw["hold"])
            if not (0.0 <= step_up < hold <= 1.0):
                raise ValueError(f"need 0 <= step_up < hold <= 1, got {step_up}, {hold}")
            return cls(step_up, hold)
        except Exception:
            log.exception("Bad thresholds file %s; using defaults %s", path, DEFAULTS)
            return cls(**DEFAULTS)

    def decide(self, score: float) -> str:
        if score >= self.hold:
            return "HOLD"
        if score >= self.step_up:
            return "STEP_UP"
        return "APPROVE"


def rule_reasons(f: dict) -> list:
    """Plain-language reasons from features. Used until Joshua's SHAP explain function is wired in,
    and as the fallback if it fails. Never invents a reason that the features do not show."""
    r = []
    if f.get("is_full_drain"):
        r.append("Account emptied in one transfer")
    if f.get("recipient_inbound_count_recent", 0) >= 5:
        r.append("Many payments to this recipient in a short time")
    if f.get("new_recipient"):
        r.append("New recipient")
    if f.get("sender_txn_count_recent", 0) >= 10:
        r.append("Rapid repeat payments from this account")
    if f.get("hour_of_day", 12) < 6 and f.get("amount_to_balance", 0) > 0.5:
        r.append("Large payment at an unusual hour")
    if abs(f.get("error_balance_orig", 0)) > 1.0:   # tolerate cents-level rounding
        r.append("Balances do not add up")
    return r[:3] or ["Unusual activity"]
