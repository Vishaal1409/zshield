# Assumptions

- The dashboard is a standalone Streamlit prototype alongside the repository API; it currently uses synthetic data and does not send analyst actions to the backend.
- “Landing page” means a default Overview page with summary metrics, recent flagged activity, and direct navigation into the Live Feed.
- The visual direction in the user's current request takes precedence over the older Rustic Teal direction in the planning material: the interface uses a flat blue, teal, and neutral palette with no gradients.
- The MUI reference is interpreted as Material-style surfaces, spacing, typography hierarchy, outlined controls, and restrained status colors; the app remains native Streamlit.
- Until a backend is available, demo interactions use synthetic sample data. Analyst actions update the displayed session only.
- Impact metrics show `n/a` when matching ground-truth labels are unavailable. Included sample labels only match the stable initial transaction IDs.
- The transaction table is intentionally scrollable, and charts retain Plotly's hover, zoom, and pan interactions.
