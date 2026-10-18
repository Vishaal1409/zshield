from pathlib import Path
import pandas as pd
import streamlit as st
from charts import amount_by_type, latency_chart
from data import APIError, fetch_recent, fetch_stats, format_units

try:
    df = fetch_recent()
    s = fetch_stats()
except APIError as exc:
    st.error(str(exc))
    st.stop()

st.markdown('<div class="eyebrow">Evaluation</div>', unsafe_allow_html=True)
st.title("Impact")
st.warning("Evaluation labels are available only for matching sample transaction IDs. They are not available at decision time.")
st.markdown('<div class="page-intro">Explore value held, decision patterns, transaction types, and API processing latency.</div>', unsafe_allow_html=True)
missed = None
fp_rate = None
labels_path = Path(__file__).resolve().parent.parent / "dev" / "demo_stream_sample.csv"
try:
    labels = pd.read_csv(labels_path)
    labels.columns = [c.lower() for c in labels.columns]
    if {"txn_id", "isfraud"}.issubset(labels.columns):
        merged = df.merge(labels[["txn_id", "isfraud"]], on="txn_id", how="inner")
        if not merged.empty:
            fraud = pd.to_numeric(merged.isfraud, errors="coerce").fillna(0).astype(bool)
            missed = merged.loc[fraud & merged.decision.eq("APPROVE"), "amount"].sum()
            legitimate = merged[~fraud]
            fp_rate = legitimate.decision.isin(["STEP_UP", "HOLD"]).mean() if len(legitimate) else None
except (OSError, ValueError):
    pass
c1, c2, c3 = st.columns(3)
c1.metric("Value held", format_units(s.get("value_intercepted", 0)))
c2.metric("Labeled fraud missed", format_units(missed) if missed is not None else "n/a")
c3.metric("Labeled false-positive rate", f"{fp_rate:.1%}" if fp_rate is not None else "n/a")
left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.subheader("Value by transaction type")
        st.plotly_chart(amount_by_type(df), width="stretch", config={"displaylogo": False})
with right:
    with st.container(border=True):
        st.subheader("Latency over time")
        st.plotly_chart(latency_chart(df, s.get("p95_latency_ms")), width="stretch", config={"displaylogo": False})
with st.container(border=True):
    st.subheader("Decisions by transaction type")
    if df.empty:
        st.info("No recent transactions from the API.")
    else:
        table = df.pivot_table(index="type", columns="decision", values="txn_id", aggfunc="count", fill_value=0).reset_index()
        st.dataframe(table, hide_index=True, width="stretch")
st.caption("Evaluation labels are joined by transaction ID. Unmatched API rows are not labeled.")
