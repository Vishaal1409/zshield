import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --page: #e9e2d8; --surface: #fffaf2; --ink: #2c2530;
          --muted: #6d626b; --line: #c8bbb0; --plum: #71566d;
          --moss: #758066; --green: #66765b; --amber: #aa7840;
          --red: #965460; --shadow: 0 1px 3px rgba(48, 42, 51, .08);
        }
        html { font-size: 17px; }
        html, body, [data-testid="stAppViewContainer"] { background: var(--page); color: var(--ink); }
        [data-testid="stHeader"] { background: var(--page); }
        [data-testid="stSidebar"] { background: #e3dbd1; border-right: 1.5px solid #cfc3b9; }
        [data-testid="stSidebarContent"] { padding-top: 1rem; }
        [data-testid="stAppViewContainer"] .main .block-container { max-width: 1500px; padding: 1.15rem 2rem 3rem; }
        [data-testid="stHorizontalBlock"] { gap: 1rem; }
        [data-testid="stMetric"] { background: #cbb9a6 !important; border: 2px solid #a99482 !important; border-top: 2.5px solid #a99482 !important; border-radius: 8px; padding: 1rem 1.1rem; box-shadow: var(--shadow); }
        [data-testid="stMetricLabel"] { color: var(--muted); font-weight: 600; }
        [data-testid="stMetricValue"] { color: var(--ink); }
        div[data-testid="stVerticalBlockBorderWrapper"] { background: #cbb9a6 !important; border: 2px solid #a99482 !important; border-radius: 8px; box-shadow: var(--shadow); }
        [class*="st-key-card-"] { background: #cbb9a6 !important; border: 2px solid #a99482 !important; border-radius: 8px !important; }
        [class*="st-key-card-"] div[data-testid="stVerticalBlockBorderWrapper"] { background: #cbb9a6 !important; border: 2px solid #a99482 !important; border-radius: 8px !important; }
        h1, h2, h3 { letter-spacing: -.02em; color: var(--ink); }
        .eyebrow { color: var(--plum); font-size: .84rem; font-weight: 700; letter-spacing: .11em; text-transform: uppercase; margin-bottom: .35rem; }
        .page-intro { color: var(--muted); margin-top: -.5rem; margin-bottom: 1.15rem; font-size: 1rem; }
        .status-pill { display:inline-block; border:2px solid #cbd2bf; border-radius:999px; padding:.25rem .65rem; background:#edf0e7; color:#566249; font-weight:700; font-size:.86rem; }
        [data-testid="stCaptionContainer"] p,
        [data-testid="stMetricLabel"],
        [data-testid="stMetricDelta"],
        [data-testid="stWidgetLabel"] p,
        [data-testid="stMarkdownContainer"] small { font-size: .94rem; }
        .decision-approved { color:#566b4c; font-weight:700; }
        .decision-step-up { color:#94602f; font-weight:700; }
        .decision-hold { color:#8b4b58; font-weight:700; }
        [data-testid="stDataFrame"] { border:2px solid var(--line); border-radius:8px; overflow:hidden; }
        [data-testid="stPlotlyChart"] { border:2px solid #a99482; border-radius:8px; background:#cbb9a6; padding:.25rem; }
        .hero-banner {
          display:flex; align-items:center; gap:1.35rem;
          min-height:100px; margin:-4.5rem 0 .7rem; padding:1rem 1.35rem;
          border:2px solid rgba(44,37,48,.24); border-radius:10px;
          background:linear-gradient(112deg,#352b39 0%,#594353 52%,#806044 100%);
          color:#fbf4e9; box-shadow:0 5px 14px rgba(44,37,48,.18);
        }
        .hero-brand { flex:0 0 auto; padding-right:1.25rem; border-right:1px solid rgba(251,244,233,.35); color:#fffaf2; font-size:1.55rem; font-weight:750; letter-spacing:-.035em; white-space:nowrap; }
        .hero-content { min-width:0; }
        .hero-kicker { color:#e2d0b9; font-size:.8rem; font-weight:700; letter-spacing:.14em; }
        .hero-message { margin:.3rem 0 .2rem; color:#fffaf2; font-size:clamp(1.25rem,2.2vw,1.8rem); font-weight:650; letter-spacing:-.025em; }
        .hero-detail { color:#e9ded5; font-size:.96rem; }
        [data-testid="stTopNav"] a,
        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarNavLink"],
        [data-testid="stNavigation"] a,
        a[data-testid="stPageLink-NavLink"] {
          border: 2px solid transparent;
          border-radius: 7px;
          box-shadow: 0 3px 8px rgba(48, 42, 51, .18);
          transition: background-color .15s ease, box-shadow .15s ease, transform .15s ease;
        }
        [data-testid="stTopNav"] a:hover,
        [data-testid="stSidebarNav"] a:hover,
        [data-testid="stSidebarNavLink"]:hover,
        [data-testid="stNavigation"] a:hover,
        a[data-testid="stPageLink-NavLink"]:hover {
          background: #eee7ed;
          border-color: #d8cbd6;
          box-shadow: 0 5px 11px rgba(48, 42, 51, .21);
          transform: translateY(-1px);
        }
        [data-testid="stTopNav"] a[aria-current="page"],
        [data-testid="stSidebarNav"] a[aria-current="page"],
        [data-testid="stSidebarNavLink"][aria-current="page"],
        [data-testid="stNavigation"] a[aria-current="page"] {
          background: #e8dfe7;
          border-color: #cbb9c7;
          color: #563e54;
          box-shadow: 0 3px 8px rgba(48, 42, 51, .18);
          font-weight: 650;
        }
        [data-testid="stMainBlockContainer"] { overflow-x: hidden; }
        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: #e6dfd7; border-radius: 8px; }
        ::-webkit-scrollbar-thumb { background: #b2a6ad; border: 2px solid #e6dfd7; border-radius: 8px; }
        ::-webkit-scrollbar-thumb:hover { background: #8f7e89; }
        @media (max-width: 760px) {
          [data-testid="stAppViewContainer"] .main .block-container { padding: .75rem .8rem 2rem; }
          [data-testid="stHorizontalBlock"] { gap: .5rem; }
          .hero-banner { min-height:92px; margin:-3.25rem 0 .6rem; padding:.8rem .85rem; gap:.8rem; }
          .hero-brand { padding-right:.8rem; font-size:1.25rem; }
          .hero-detail { font-size:.88rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
