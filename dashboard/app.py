"""Starter dashboard (Armaan owns). Run: streamlit run dashboard/app.py"""
import time

import pandas as pd
import requests
import streamlit as st

API = "http://localhost:8000"
st.set_page_config(page_title="ZShield", layout="wide")
st.title("ZShield: real-time payment protection")

try:
    s = requests.get(f"{API}/stats", timeout=2).json()
    a = requests.get(f"{API}/alerts", timeout=2).json()
except Exception:
    st.warning("API not reachable. Start it with: uvicorn api.main:app --port 8000")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Processed", s["total_processed"])
c2.metric("Flagged", s["flagged_count"])
c3.metric("Value intercepted", f"{s['value_intercepted']:,.0f}")
c4.metric("Avg latency (ms)", s["avg_latency_ms"])

st.subheader("Latest flagged payments")
if a:
    st.dataframe(pd.DataFrame(a)[["txn_id", "amount", "risk_score", "decision", "reasons", "alert_text", "analyst_status"]],
                 use_container_width=True)
else:
    st.info("No flagged payments yet. Run the producer.")

time.sleep(2)
st.rerun()
