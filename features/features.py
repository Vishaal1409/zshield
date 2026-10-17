"""Shared feature code. The SAME function must be used in training and in the live API,
otherwise training and serving features drift apart. Balaa extends this file."""

TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]


def base_features(txn: dict) -> dict:
    """Features computable from one transaction alone (no history needed)."""
    amount = float(txn["amount"])
    old_o = float(txn["oldbalanceOrg"])
    new_o = float(txn["newbalanceOrig"])
    old_d = float(txn["oldbalanceDest"])
    new_d = float(txn["newbalanceDest"])
    f = {
        "amount": amount,
        "error_balance_orig": new_o + amount - old_o,
        "error_balance_dest": old_d + amount - new_d,
        "amount_to_balance": amount / old_o if old_o > 0 else 0.0,
        "is_full_drain": int(old_o > 0 and new_o == 0 and abs(amount - old_o) < 1e-6),
        "hour_of_day": int(txn["step"]) % 24,
    }
    for t in TYPES:
        f[f"type_{t}"] = int(txn["type"] == t)
    return f


def compute_live_features(txn: dict, state: dict) -> dict:
    """Base features plus history features from per-account state (Balaa + Abhinava).
    TODO: new_recipient flag, sender velocity, recipient inbound count."""
    f = base_features(txn)
    seen = state.setdefault("seen_pairs", set())
    pair = (txn["nameOrig"], txn["nameDest"])
    f["new_recipient"] = int(pair not in seen)
    seen.add(pair)
    return f
