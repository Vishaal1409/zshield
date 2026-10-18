import pandas as pd
import streamlit as st
from data import APIError, fetch_alerts, record_analyst_action

try:
    alerts = fetch_alerts().sort_values("time", ascending=False, na_position="last")
except APIError as exc:
    st.error(str(exc))
    st.stop()

st.markdown('<div class="eyebrow">Analyst workspace</div>', unsafe_allow_html=True)
st.title("Alert Detail")
st.markdown('<div class="page-intro">Review API-scored risk context and record an analyst action.</div>', unsafe_allow_html=True)
if alerts.empty:
    st.info("The API has no flagged transactions available yet.")
else:
    options = alerts.txn_id.fillna("").astype(str).tolist()
    selected_id = st.selectbox("Flagged transaction", options)
    row = alerts[alerts.txn_id.astype(str) == selected_id].iloc[0]
    left, right = st.columns([1, 1.3])
    with left:
        with st.container(border=True, key="card-alert-risk"):
            st.subheader("Risk assessment")
            score = float(row.risk_score) if pd.notna(row.risk_score) else 0.0
            st.metric("Risk score", f"{score:.1%}", str(row.decision or "").replace("_", " "))
            st.progress(max(0.0, min(1.0, score)))
            st.markdown("**Transaction facts**")
            amount = f"{float(row.amount):,.2f} units" if pd.notna(row.amount) else "Not supplied by API"
            latency = f"{float(row.latency_ms):.3f} ms" if pd.notna(row.latency_ms) else "Not supplied by API"
            st.write(f"Type: {row.type or 'Not supplied by API'}  \nAmount: {amount}  \nTransaction ID: {selected_id}  \nLatency: {latency}")
            if pd.notna(row.time):
                st.write(f"Time: {row.time}")
            st.caption(f"Analyst status: {row.analyst_status or 'Pending'}")
    with right:
        with st.container(border=True, key="card-alert-reasons"):
            st.subheader("Top reasons")
            reasons = row.reasons if isinstance(row.reasons, list) else []
            if reasons:
                for i, reason in enumerate(reasons[:3], 1):
                    st.markdown(f"**{i}.** {reason}")
            else:
                st.caption("No reasons were supplied by the API.")
            st.divider()
            st.subheader("Alert summary")
            st.write(row.alert_text or "No alert summary was supplied by the API.")
    st.markdown("### Analyst action")
    cols = st.columns(3)
    for col, action, label in zip(cols, ["APPROVE", "BLOCK", "ESCALATE"], ["Approve", "Block", "Escalate"]):
        if col.button(label, width="stretch", type="primary" if action == "BLOCK" else "secondary"):
            try:
                record_analyst_action(selected_id, action)
                st.toast(f"{selected_id}: {label.lower()} recorded by API")
                st.rerun()
            except APIError as exc:
                st.error(str(exc))
