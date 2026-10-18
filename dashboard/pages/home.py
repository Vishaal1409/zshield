import streamlit as st

from charts import activity_chart, decision_chart
from data import format_money, sample_data, stats

df = sample_data()
s = stats(df)
st.title("Payment risk overview")
st.markdown('<div class="page-intro">Monitor decisions as payments arrive, review flagged activity, and understand current system impact.</div>', unsafe_allow_html=True)

st.markdown("### At a glance")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Processed", f"{s['total_processed']:,}", "transactions")
c2.metric("Flagged", f"{s['flagged_count']:,}", f"{s['flagged_count'] / max(1,s['total_processed']):.1%} of volume")
c3.metric("Value held", format_money(s["value_intercepted"]), "pending analyst review")
c4.metric("Avg latency", f"{s['avg_latency_ms']:.0f} ms", f"p95 {s['p95_latency_ms']:.0f} ms")

with st.container(border=True):
    st.subheader("Recent flagged activity")
    flagged = df[df.decision.isin(["STEP_UP", "HOLD"])].sort_values("time", ascending=False).head(6)
    st.dataframe(flagged[["time", "txn_id", "type", "amount", "risk_score", "decision", "latency_ms"]], hide_index=True, width="stretch", height=300, column_config={"time": st.column_config.DatetimeColumn("Time", format="HH:mm:ss"), "amount": st.column_config.NumberColumn("Amount", format="$%.2f"), "risk_score": st.column_config.ProgressColumn("Risk score", min_value=0, max_value=1, format="%.2f"), "latency_ms": st.column_config.NumberColumn("Latency", format="%d ms")})

left, right = st.columns([1.6, 1])
with left:
    with st.container(border=True):
        st.subheader("Transaction activity")
        st.plotly_chart(activity_chart(df), width="stretch", config={"displaylogo": False})
with right:
    with st.container(border=True):
        st.subheader("Decision mix")
        st.plotly_chart(decision_chart(df), width="stretch", config={"displaylogo": False})
