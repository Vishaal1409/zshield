"""Shared feature code (Balaa). The SAME functions are used in training and in the live API, so
training and serving features cannot drift apart.

  compute_live_features(txn, state)  one payment, live in the API (api/state.py calls it)
  build_feature_frame(df)            a whole DataFrame for training: replays the rows in step order
                                     through compute_live_features, so the values are identical

Every feature uses only the current payment and payments that came BEFORE it in the stream.
isFraud and isFlaggedFraud are never read (isFlaggedFraud is PaySim's own rule output and leaks
the label).

MODEL_FEATURES matches the input order of Joshua's trained XGBoost/ONNX model (model/features.py on
the ML branch: same names, same formulas). Do not rename or change a formula without retraining.
"""
import os

TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]

# Input order of the trained model. Write this list to model/feature_columns.json for the API.
MODEL_FEATURES = [
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

# History features: used by the rules and the reasons. On PaySim they are almost always
# new_recipient=1 and counts=0 (99.85% of senders appear once), so the model is not trained on them.
HISTORY_FEATURES = ["new_recipient", "sender_txn_count_recent", "recipient_inbound_count_recent"]

ALL_FEATURES = MODEL_FEATURES + [f"type_{t}" for t in TYPES] + HISTORY_FEATURES

# Short-term window for the history counts, in PaySim steps (1 step = 1 hour).
WINDOW_STEPS = int(os.getenv("ZSHIELD_WINDOW_STEPS", "6"))


def base_features(txn: dict) -> dict:
    """Features computable from one transaction alone (no history needed)."""
    amount = float(txn["amount"])
    old_o = float(txn["oldbalanceOrg"])
    new_o = float(txn["newbalanceOrig"])
    old_d = float(txn["oldbalanceDest"])
    new_d = float(txn["newbalanceDest"])
    f = {
        "is_transfer": int(txn["type"] == "TRANSFER"),
        "amount": amount,
        "oldbalanceOrg": old_o,
        "newbalanceOrig": new_o,
        "oldbalanceDest": old_d,
        "newbalanceDest": new_d,
        "err_bal_orig": new_o + amount - old_o,     # should be 0 if the sender's books add up
        "err_bal_dest": old_d + amount - new_d,     # should be 0 if the recipient's books add up
        "full_drain": int(old_o > 0 and amount >= old_o),
        "amt_to_bal": amount / (old_o + 1.0),
        "hour": int(txn["step"]) % 24,
    }
    for t in TYPES:
        f[f"type_{t}"] = int(txn["type"] == t)
    return f


def _count_recent(times: list, step: int, window: int) -> int:
    """Drop events older than the window (in place) and count the rest."""
    cut = 0
    while cut < len(times) and times[cut] <= step - window:
        cut += 1
    if cut:
        del times[:cut]
    return len(times)


def compute_live_features(txn: dict, state: dict, window: int = WINDOW_STEPS) -> dict:
    """Base features plus history features, then records this payment in `state`.
    The counts cover payments in the last `window` steps BEFORE this one (the current payment is
    added after the features are computed). Feed transactions in step order."""
    f = base_features(txn)
    step = int(txn["step"])
    seen = state.setdefault("seen_pairs", set())
    sender = state.setdefault("sender_steps", {})
    dest = state.setdefault("dest_steps", {})

    pair = (txn["nameOrig"], txn["nameDest"])
    s_times = sender.setdefault(txn["nameOrig"], [])
    d_times = dest.setdefault(txn["nameDest"], [])
    f["new_recipient"] = int(pair not in seen)
    f["sender_txn_count_recent"] = _count_recent(s_times, step, window)
    f["recipient_inbound_count_recent"] = _count_recent(d_times, step, window)

    seen.add(pair)
    s_times.append(step)
    d_times.append(step)
    return f


def build_feature_frame(df, window: int = WINDOW_STEPS):
    """Training-side features: replay df in step order (stable, so file order is kept within a step)
    through compute_live_features. Returns a DataFrame with ALL_FEATURES, aligned to df.index.
    About 30 to 60 s for all 6.3M PaySim rows."""
    import pandas as pd

    order = df.sort_values("step", kind="stable")
    cols = ["step", "type", "amount", "nameOrig", "oldbalanceOrg", "newbalanceOrig",
            "nameDest", "oldbalanceDest", "newbalanceDest"]
    state: dict = {}
    rows = [compute_live_features(dict(zip(cols, r)), state, window)
            for r in order[cols].itertuples(index=False, name=None)]
    return pd.DataFrame(rows, index=order.index, columns=ALL_FEATURES).loc[df.index]
