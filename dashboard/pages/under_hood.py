import streamlit as st
from config import API_BASE_URL

st.markdown('<div class="eyebrow">System design</div>', unsafe_allow_html=True)
st.title("Under the Hood")
st.markdown('<div class="page-intro">How the decision flow works, why the platform matters, and the safeguards built into the design.</div>', unsafe_allow_html=True)
st.caption(f"Dashboard API URL: {API_BASE_URL} (configured in config.py)")
st.info(
    "Current demo status: placeholder rule scoring and template explanations are active. "
    "ONNX scoring, SHAP explanations, GenAI rewriting, and IBM Z on-chip AI acceleration are planned; "
    "they are not active in this demo."
)
st.subheader("Decision flow")
steps = ["Transaction stream", "Scoring API", "Live features", "Placeholder rule (active)", "Decision engine", "Rule reasons (SHAP planned)", "Audit log", "Dashboard"]
for start in range(0, len(steps), 4):
    cols = st.columns(4)
    for col, label in zip(cols, steps[start:start + 4]):
        with col:
            with st.container(border=True, key=f"card-under-hood-step-{label.lower().replace(' ', '-')}"):
                st.markdown(f"**{label}**")
    if start == 0:
        st.caption("Each payment is scored by the configured API. Reasons support review; planned model and explanation components are not active.")
left, right = st.columns(2)
with left:
    with st.container(border=True, key="card-under-hood-ibm-z"):
        st.subheader("IBM Z deployment target")
        st.markdown("- Keep scoring close to transaction data.\n- Target predictable decision latency before settlement.\n- IBM Z security, encryption, and on-chip AI acceleration are deployment goals; on-chip acceleration is planned and not active in this demo.")
with right:
    with st.container(border=True, key="card-under-hood-limits"):
        st.subheader("Honest limits")
        st.write("Dashboard metrics come from the configured scoring API. Demo stories are constructed scenarios and do not represent measured live fraud performance.")
        st.warning("Mule Burst is a constructed scenario used to demonstrate repeated inbound activity.")
st.subheader("Responsible AI safeguards")
principles = [
    ("Privacy", "Synthetic data only. No names or demographics."),
    ("Transparency", "Every flagged payment shows its reasons."),
    ("Human oversight", "A person decides on held payments."),
    ("GenAI", "GenAI only rephrases facts. Checked, with fallback."),
    ("Robustness", "If scoring fails, we step up, never silently approve."),
    ("Accountability and fairness", "Every decision is logged. Fairness checked by proxy only."),
]
cols = st.columns(4)
for i, (title, body) in enumerate(principles):
    with cols[i % 4]:
        with st.container(border=True, key=f"card-under-hood-ai-{title.lower().replace(' ', '-')}"):
            st.markdown(f"**{title}**")
            st.caption(body)
