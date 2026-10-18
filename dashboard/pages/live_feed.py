import streamlit as st
from charts import decision_chart, latency_chart
from data import APIError, fetch_recent, fetch_stats, format_units

try:
    df = fetch_recent().sort_values("time", ascending=False, na_position="last")
    s = fetch_stats()
except APIError as exc:
    st.error(str(exc))
    st.stop()

st.markdown('<div class="eyebrow">Operations</div>', unsafe_allow_html=True)
st.title("Live Feed")
st.markdown('<div class="page-intro">Recent decisions from the scoring API. Use refresh in the sidebar to reload.</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Processed", f"{int(s.get('total_processed', 0)):,}")
c2.metric("Flagged", f"{int(s.get('flagged_count', 0)):,}")
c3.metric("Value held", format_units(s.get("value_intercepted", 0)))
c4.metric("Avg latency", f"{float(s.get('avg_latency_ms', 0)):.3f} ms", f"p95 {float(s.get('p95_latency_ms', 0)):.3f} ms")

left, right = st.columns([1.8, 1])
with left:
    with st.container(border=True):
        st.subheader("Transaction stream")
        decisions = st.multiselect("Filter decisions", ["APPROVE", "STEP_UP", "HOLD"], default=["APPROVE", "STEP_UP", "HOLD"])
        view = df[df.decision.isin(decisions)]
        st.dataframe(view[["step", "txn_id", "time", "type", "amount", "risk_score", "decision", "latency_ms"]], hide_index=True, width="stretch", height=520, column_config={"time": st.column_config.DatetimeColumn("Time", format="HH:mm:ss"), "amount": st.column_config.NumberColumn("Amount (units)", format="%.2f units"), "risk_score": st.column_config.ProgressColumn("Risk score", min_value=0, max_value=1, format="%.2f"), "latency_ms": st.column_config.NumberColumn("Latency", format="%.3f ms")})
with right:
    with st.container(border=True):
        st.subheader("Decision mix")
        st.plotly_chart(decision_chart(df), width="stretch", config={"displaylogo": False})
        st.caption("Flagged includes STEP_UP and HOLD decisions.")
    with st.container(border=True):
        st.subheader("Latency")
        st.plotly_chart(latency_chart(df, s.get("p95_latency_ms")), width="stretch", config={"displaylogo": False})
    with st.container(border=True):
        st.subheader("Demo status")
        story = st.session_state.get("active_story", "No story submitted")
        st.write(f"Last submitted scenario: **{story}**")
        st.caption("Mule Burst is a constructed scenario." if story == "Mule Burst" else "Scenario rows are posted to the scoring API from CSV.")
