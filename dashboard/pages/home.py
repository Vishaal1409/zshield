import streamlit as st
from charts import activity_chart, decision_chart
from data import APIError, fetch_alerts, fetch_recent, fetch_stats, format_units

try:
    s = fetch_stats()
    recent = fetch_recent()
    flagged = fetch_alerts()
except APIError as exc:
    st.error(str(exc))
    st.stop()

st.title("Payment risk overview")
st.markdown('<div class="page-intro">Monitor decisions as payments arrive, review flagged activity, and understand current system impact.</div>', unsafe_allow_html=True)
st.markdown("### At a glance")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Processed", f"{int(s.get('total_processed', 0)):,}", "transactions")
c2.metric("Flagged", f"{int(s.get('flagged_count', 0)):,}")
c3.metric("Value held", format_units(s.get("value_intercepted", 0)), "pending analyst review")
c4.metric("Avg latency", f"{float(s.get('avg_latency_ms', 0)):.3f} ms", f"p95 {float(s.get('p95_latency_ms', 0)):.3f} ms")

with st.container(border=True):
    st.subheader("Recent flagged activity")
    flagged = flagged.sort_values("time", ascending=False, na_position="last").head(6)
    if flagged.empty:
        st.info("The API has no flagged transactions to show.")
    else:
        st.dataframe(flagged[["time", "txn_id", "type", "amount", "risk_score", "decision", "latency_ms"]], hide_index=True, width="stretch", height=300, column_config={"time": st.column_config.DatetimeColumn("Time", format="HH:mm:ss"), "amount": st.column_config.NumberColumn("Amount (units)", format="%.2f units"), "risk_score": st.column_config.ProgressColumn("Risk score", min_value=0, max_value=1, format="%.2f"), "latency_ms": st.column_config.NumberColumn("Latency", format="%.3f ms")})

left, right = st.columns([1.6, 1])
with left:
    with st.container(border=True):
        st.subheader("Recent transaction activity")
        st.plotly_chart(activity_chart(recent), width="stretch", config={"displaylogo": False})
with right:
    with st.container(border=True):
        st.subheader("Decision mix")
        st.plotly_chart(decision_chart(recent), width="stretch", config={"displaylogo": False})
