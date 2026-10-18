import streamlit as st

from charts import decision_chart
from data import format_money, sample_data, stats

df = sample_data().sort_values("time", ascending=False)
s = stats(df)
st.markdown('<div class="eyebrow">Operations</div>', unsafe_allow_html=True)
st.title("Live Feed")
st.markdown('<div class="page-intro">Recent decisions across approved, step-up, and held transactions.</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Processed", f"{s['total_processed']:,}")
c2.metric("Flagged", f"{s['flagged_count']:,}")
c3.metric("Value intercepted", format_money(s["value_intercepted"]))
c4.metric("Avg latency", f"{s['avg_latency_ms']:.0f} ms", f"p95 {s['p95_latency_ms']:.0f} ms")

left, right = st.columns([1.8, 1])
with left:
    with st.container(border=True):
        st.subheader("Transaction stream")
        decisions = st.multiselect("Filter decisions", ["APPROVE", "STEP_UP", "HOLD"], default=["APPROVE", "STEP_UP", "HOLD"])
        view = df[df.decision.isin(decisions)]
        st.dataframe(view[["step", "txn_id", "type", "amount", "risk_score", "decision", "latency_ms"]], hide_index=True, width="stretch", height=520, column_config={"amount": st.column_config.NumberColumn("Amount", format="$%.2f"), "risk_score": st.column_config.ProgressColumn("Risk score", min_value=0, max_value=1, format="%.2f"), "latency_ms": st.column_config.NumberColumn("Latency", format="%d ms")})
with right:
    with st.container(border=True):
        st.subheader("Decision mix")
        st.plotly_chart(decision_chart(df), width="stretch", config={"displaylogo": False})
        st.caption("Flagged includes STEP_UP and HOLD decisions.")
    with st.container(border=True):
        st.subheader("Demo status")
        story = st.session_state.get("active_story", "No story running")
        st.write(f"Current scenario: **{story}**")
        st.progress(1.0 if story in ("No story running", "Stopped") else .72)
        st.caption("Use the demo controls in the left panel to add a sample story to the stream.")
