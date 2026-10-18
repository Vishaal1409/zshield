import streamlit as st

from data import sample_data, stats, replay_story
from theme import apply_theme

st.set_page_config(page_title="ZShield | Transaction Intelligence", layout="wide", initial_sidebar_state="expanded")
apply_theme()
sample_data()

with st.sidebar:
    st.markdown("### Demo controls")
    st.caption("Replay a sample transaction story")
    for label in ["Scam Drain", "Mule Burst", "Normal Day"]:
        if st.button(label, width="stretch"):
            replay_story(label)
            st.toast(f"{label} replay added to the feed")
    st.slider("Stream speed", min_value=1, max_value=50, value=12, format="%d tx/s")
    c1, c2 = st.columns(2)
    if c1.button("Stop", width="stretch"):
        st.session_state.active_story = "Stopped"
        st.toast("Demo replay stopped")
    if c2.button("Reset", width="stretch"):
        st.session_state.pop("transactions", None)
        st.session_state.pop("active_story", None)
        st.rerun()
    st.divider()
    st.caption("Synthetic data · no personal information")

df = sample_data()
metrics = stats(df)
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
