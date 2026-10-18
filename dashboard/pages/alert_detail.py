import streamlit as st

from data import sample_data

df = sample_data()
alerts = df[df.decision.isin(["STEP_UP", "HOLD"])].sort_values("time", ascending=False)
st.markdown('<div class="eyebrow">Analyst workspace</div>', unsafe_allow_html=True)
st.title("Alert Detail")
st.markdown('<div class="page-intro">Review risk context and record an analyst action.</div>', unsafe_allow_html=True)
if alerts.empty:
    st.info("No flagged transactions are available yet.")
else:
    selected_id = st.selectbox("Flagged transaction", alerts.txn_id.tolist())
    row = alerts[alerts.txn_id == selected_id].iloc[0]
    left, right = st.columns([1, 1.3])
    with left:
        with st.container(border=True, key="card-alert-risk"):
            st.subheader("Risk assessment")
            st.metric("Risk score", f"{row.risk_score:.0%}", row.decision.replace("_", " "))
            st.progress(float(row.risk_score))
            st.markdown("**Transaction facts**")
            st.write(f"Type: {row.type}  \nAmount: ${row.amount:,.2f}  \nFrom: `{row.nameOrig}`  \nTo: `{row.nameDest}`  \nLatency: {row.latency_ms} ms")
            st.caption(f"Analyst status: {row.analyst_status}")
    with right:
        with st.container(border=True, key="card-alert-reasons"):
            st.subheader("Top reasons")
            for i, reason in enumerate(row.reasons, 1):
                st.markdown(f"**{i}.** {reason}")
            st.divider()
            st.subheader("Alert summary")
            st.write(row.alert_text)
    st.markdown("### Analyst action")
    cols = st.columns(3)
    for col, action, label in zip(cols, ["APPROVE", "BLOCK", "ESCALATE"], ["Approve", "Block", "Escalate"]):
        if col.button(label, width="stretch", type="primary" if action == "BLOCK" else "secondary"):
            df.loc[df.txn_id == selected_id, "analyst_status"] = {"APPROVE": "Approved by analyst", "BLOCK": "Blocked by analyst", "ESCALATE": "Escalated for review"}[action]
            st.session_state.transactions = df
            st.toast(f"{selected_id}: {label.lower()} recorded")
            st.rerun()
