import streamlit as st

from charts import amount_by_type, latency_chart
from data import format_money, sample_data, stats

df = sample_data()
s = stats(df)
st.markdown('<div class="eyebrow">Evaluation</div>', unsafe_allow_html=True)
st.title("Impact")
st.warning("EVALUATION VIEW: uses ground-truth labels. A real bank does not have labels at decision time.")
st.markdown('<div class="page-intro">Explore held value, decision patterns, transaction types, and processing latency.</div>', unsafe_allow_html=True)

held = df[df.decision == "HOLD"].amount.sum()
missed = None
fp_rate = None
labels_path = "../dev/demo_stream_sample.csv"
try:
    import os
    labels = __import__("pandas").read_csv(os.path.join(os.path.dirname(__file__), labels_path))
    labels.columns = [c.lower() for c in labels.columns]
    if {"txn_id", "isfraud"}.issubset(labels.columns):
        merged = df.merge(labels[["txn_id", "isfraud"]], on="txn_id", how="inner")
        if not merged.empty:
            fraud = merged.isfraud.astype(bool)
            missed = merged.loc[fraud & merged.decision.eq("APPROVE"), "amount"].sum()
            legitimate = merged[~fraud]
            fp_rate = legitimate.decision.isin(["STEP_UP", "HOLD"]).mean() if len(legitimate) else None
except (OSError, ValueError):
    pass

c1, c2, c3 = st.columns(3)
c1.metric("Fraud intercepted", format_money(s["value_intercepted"]))
c2.metric("Fraud missed", format_money(missed) if missed is not None else "n/a")
c3.metric("False-positive rate", f"{fp_rate:.1%}" if fp_rate is not None else "n/a")

left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.subheader("Value by transaction type")
        st.plotly_chart(amount_by_type(df), width="stretch", config={"displaylogo": False})
with right:
    with st.container(border=True):
        st.subheader("Latency over time")
        st.plotly_chart(latency_chart(df, s["p95_latency_ms"]), width="stretch", config={"displaylogo": False})
with st.container(border=True):
    st.subheader("Decisions by transaction type")
    st.dataframe(df.pivot_table(index="type", columns="decision", values="txn_id", aggfunc="count", fill_value=0).reset_index(), hide_index=True, width="stretch")
st.caption("Labels are joined on txn_id (isFraud).")
