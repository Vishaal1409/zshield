import streamlit as st

from config import API_BASE_URL
from data import APIError, api_health, replay_story
from theme import apply_theme

st.set_page_config(page_title="ZShield | Transaction Intelligence", layout="wide", initial_sidebar_state="expanded")
apply_theme()

with st.sidebar:
    st.markdown("### Demo controls")
    st.caption(f"Scoring API: {API_BASE_URL}")
    try:
        health = api_health()
        scorer = health.get("scorer")
        st.success(f"API connected{f' · {scorer}' if scorer else ''}")
    except APIError as exc:
        st.error(str(exc))
    st.caption("Replay CSV rows through the live scoring API")
    for label in ["Scam Drain", "Mule Burst", "Normal Day"]:
        display = "Mule Burst (constructed scenario)" if label == "Mule Burst" else label
        if st.button(display, width="stretch"):
            try:
                result = replay_story(label)
                if result["failed"]:
                    st.warning(f"Scored {result['sent']} rows; {result['failed']} failed.")
                    for error in result["errors"][:4]:
                        st.caption(error)
                else:
                    st.success(f"Sent {result['sent']} rows to /score.")
                st.session_state["active_story"] = label
                st.rerun()
            except APIError as exc:
                st.error(str(exc))
    if st.button("Refresh dashboard", width="stretch"):
        st.rerun()
    st.divider()
    st.caption("Demo CSV scenarios are scored by the configured API.")

pages = [
    st.Page("pages/live_feed.py", title="Live Feed"),
    st.Page("pages/home.py", title="Overview", default=True),
    st.Page("pages/alert_detail.py", title="Alert Detail"),
    st.Page("pages/impact.py", title="Impact"),
    st.Page("pages/under_hood.py", title="Under the Hood"),
]
pg = st.navigation(pages, position="top")

st.markdown(
    """
    <section class="hero-banner">
      <div class="hero-brand">◈ ZShield</div>
      <div class="hero-content">
        <div class="hero-kicker">REAL-TIME PAYMENT INTELLIGENCE</div>
        <div class="hero-message">Catch the unusual before money moves.</div>
        <div class="hero-detail">Explainable risk signals · Human review · Decisions in time</div>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)
pg.run()
