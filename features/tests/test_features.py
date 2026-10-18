"""Feature tests (Balaa). Run from the repo root:  python -m pytest features/tests -q"""
import pandas as pd

from api.state import StateStore
from features.features import (ALL_FEATURES, MODEL_FEATURES, base_features, build_feature_frame,
                               compute_live_features)

STREAM = "docs/samples/sample_stream.csv"


def row(i="T1", step=2, typ="TRANSFER", amount=9000.0, orig="C1", old_o=9000.0, new_o=0.0,
        dest="C2", old_d=0.0, new_d=0.0):
    return {"txn_id": i, "step": step, "type": typ, "amount": amount, "nameOrig": orig,
            "oldbalanceOrg": old_o, "newbalanceOrig": new_o, "nameDest": dest,
            "oldbalanceDest": old_d, "newbalanceDest": new_d}


def test_model_feature_order_matches_trained_model():
    # Input order of Joshua's XGBoost/ONNX model (artifacts/model_meta.json on the ML branch).
    assert MODEL_FEATURES == ["is_transfer", "amount", "oldbalanceOrg", "newbalanceOrig",
                              "oldbalanceDest", "newbalanceDest", "err_bal_orig", "err_bal_dest",
                              "full_drain", "amt_to_bal", "hour"]


def test_training_and_serving_features_are_identical():
    """The same transactions give the same feature values offline (training) and in the live API."""
    df = pd.read_csv(STREAM)
    offline = build_feature_frame(df)
    store = StateStore()
    live = pd.DataFrame([store.build_features(r) for r in df.sort_values("step", kind="stable")
                         .to_dict("records")], columns=ALL_FEATURES)
    pd.testing.assert_frame_equal(offline.sort_index().reset_index(drop=True),
                                  live.reset_index(drop=True), check_dtype=False)


def test_scam_drain_values():
    f = base_features(row(step=26))
    assert f["full_drain"] == 1 and f["is_transfer"] == 1 and f["hour"] == 2
    assert f["err_bal_orig"] == 0.0 and f["err_bal_dest"] == 9000.0
    assert abs(f["amt_to_bal"] - 9000 / 9001) < 1e-12


def test_history_uses_past_payments_only():
    state = {}
    first = compute_live_features(row("A", step=5, dest="MULE", orig="S0"), state)
    assert first["new_recipient"] == 1 and first["recipient_inbound_count_recent"] == 0
    for k in range(1, 6):
        f = compute_live_features(row(f"B{k}", step=5, dest="MULE", orig=f"S{k}"), state)
    assert f["recipient_inbound_count_recent"] == 5          # 5 earlier payments, not itself
    again = compute_live_features(row("C", step=6, dest="MULE", orig="S0"), state)
    assert again["new_recipient"] == 0 and again["sender_txn_count_recent"] == 1


def test_history_window_expires():
    state = {}
    compute_live_features(row("A", step=1, dest="D"), state, window=6)
    assert compute_live_features(row("B", step=6, dest="D"), state, window=6)["recipient_inbound_count_recent"] == 1
    assert compute_live_features(row("C", step=13, dest="D"), state, window=6)["recipient_inbound_count_recent"] == 0


def test_no_lookahead():
    """Changing a later payment never changes an earlier payment's features."""
    df = pd.read_csv(STREAM).head(200)
    a = build_feature_frame(df)
    df2 = df.copy()
    df2.loc[150:, "nameDest"] = "SAME_DEST"
    b = build_feature_frame(df2)
    pd.testing.assert_frame_equal(a.loc[:149], b.loc[:149])


def test_label_columns_are_never_used():
    r = row()
    with_labels = {**r, "isFraud": 1, "isFlaggedFraud": 1}
    assert compute_live_features(with_labels, {}) == compute_live_features(r, {})
