import streamlit as st

st.markdown('<div class="eyebrow">System design</div>', unsafe_allow_html=True)
st.title("Under the Hood")
st.markdown('<div class="page-intro">How the decision flow works, why the platform matters, and the safeguards built into the design.</div>', unsafe_allow_html=True)

st.subheader("Decision flow")
steps = ["Transaction stream", "Scoring API", "Live features", "ONNX model", "Decision engine", "SHAP + GenAI", "Audit log", "Dashboard"]
for start in range(0, len(steps), 4):
    cols = st.columns(4)
    for col, label in zip(cols, steps[start:start + 4]):
        with col:
            with st.container(border=True, key=f"card-under-hood-step-{label.lower().replace(' ', '-')}"):
                st.markdown(f"**{label}**")
    if start == 0:
        st.caption("↓  Each payment is evaluated before settlement; explanations support review and do not make the decision.  ↓")

left, right = st.columns(2)
with left:
    with st.container(border=True, key="card-under-hood-ibm-z"):
        st.subheader("Why IBM Z")
        st.markdown("- Score near the transaction so sensitive data stays on the platform.\n- Keep decision latency low and predictable before settlement.\n- Use on-chip AI acceleration, security, and encryption capabilities.")
        st.info("Designed for IBM Z")
with right:
    with st.container(border=True, key="card-under-hood-limits"):
        st.subheader("Honest limits")
        st.write("This demo uses synthetic PaySim-style data. Results may not generalize to live payments; fraud patterns can drift, and fraudsters adapt. Platform deployment claims should reflect what has actually been run.")

st.subheader("Responsible AI")
principles = [
    ("Privacy", "Synthetic data only. No names, phone numbers, or demographics are used as features. Account IDs are pseudonymous; only minimum facts are shared with the language model."),
    ("Fairness", "Protected or demographic attributes are excluded. Compare false-positive and miss rates across transaction types and amount bands."),
    ("Transparency", "Flagged payments show their top three reasons and a plain-language explanation."),
    ("Human oversight", "High-risk payments go to an analyst who can override the recommendation."),
    ("Safe GenAI", "The language model rephrases supplied facts, cannot change a decision, and has a template fallback."),
    ("Robustness", "If the model or API fails, use a safe step-up decision and log the failure."),
    ("Accountability", "Record each decision, score, reason, latency, and analyst action in an audit log."),
    ("Limits", "Synthetic data, possible drift, and adapting fraudsters limit the claims this demo can support."),
]
cols = st.columns(4)
for i, (title, body) in enumerate(principles):
    with cols[i % 4]:
        with st.container(border=True, key=f"card-under-hood-ai-{title.lower().replace(' ', '-')}"):
            st.markdown(f"**{title}**")
            st.caption(body)
