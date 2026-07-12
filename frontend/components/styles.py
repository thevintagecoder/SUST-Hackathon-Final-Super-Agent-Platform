"""Ops Center visual theme for the liquidity desk."""

from __future__ import annotations

import streamlit as st


APP_CSS = """
<style>
/* ── Hide default Streamlit chrome ───────────────────────────── */
header[data-testid="stHeader"]           { display: none !important; }
div[data-testid="stToolbar"]             { display: none !important; }
div[data-testid="stDecoration"]          { display: none !important; }
div[data-testid="stStatusWidget"]        { display: none !important; }
#MainMenu                                { display: none !important; }
footer                                   { display: none !important; }

/* ── Palette (inspired by mobile Ops Center) ───────────────── */
:root {
    --bg:           #f0f4f8;
    --surface:      #ffffff;
    --surface-soft: #f8fafc;
    --blue:         #2563eb;
    --blue-dark:    #1d4ed8;
    --blue-light:   #dbeafe;
    --blue-header:  linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
    --text:         #1e293b;
    --text-soft:    #64748b;
    --muted:        #94a3b8;
    --border:       #e2e8f0;
    --green:        #10b981;
    --green-bg:     #d1fae5;
    --red:          #ef4444;
    --red-bg:       #fee2e2;
    --orange:       #f97316;
    --orange-bg:    #ffedd5;
    --purple:       #8b5cf6;
    --purple-bg:    #ede9fe;
    --shadow:       0 4px 14px rgba(15, 23, 42, 0.06);
    --shadow-lg:    0 8px 24px rgba(37, 99, 235, 0.12);
}

html, body, .stApp {
    background-color: var(--bg) !important;
    color: var(--text);
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

.block-container {
    max-width: 920px !important;
    padding-top: 0 !important;
    padding-bottom: 5rem;
    background: transparent !important;
}

/* ── Typography ──────────────────────────────────────────────── */
h1, h2, h3 {
    color: var(--text) !important;
    letter-spacing: -0.02em;
    font-weight: 700 !important;
}
h1 { font-size: 1.5rem !important; }
p, li, label, .stMarkdown { color: var(--text); }

/* ── Site title (global entry branding) ─────────────────────── */
.site-title-wrap {
    margin: 0.5rem 0 1rem;
    padding: 0.25rem 0;
}
.site-title {
    color: var(--blue-dark);
    font-size: 1in;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -0.02em;
    text-align: center;
}

/* ── Ops Center hero header ──────────────────────────────────── */
.ops-hero {
    background: var(--blue-header);
    border-radius: 0 0 24px 24px;
    padding: 1.25rem 1.35rem 1.1rem;
    margin: -1rem -1rem 1.25rem -1rem;
    box-shadow: var(--shadow-lg);
}
.ops-hero-title {
    color: #ffffff;
    font-size: 1.45rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.03em;
}
.ops-hero-sub {
    color: rgba(255,255,255,0.82);
    font-size: 0.82rem;
    margin-top: 0.2rem;
}
.ops-hero-metrics {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.65rem;
    margin-top: 1rem;
}
.ops-hero-metric {
    background: rgba(255,255,255,0.14);
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 14px;
    padding: 0.75rem 0.9rem;
    position: relative;
}
.ops-hero-metric-label {
    color: rgba(255,255,255,0.78);
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.ops-hero-metric-value {
    color: #ffffff;
    font-size: 1.65rem;
    font-weight: 800;
    margin-top: 0.15rem;
    line-height: 1.1;
}
.ops-hero-metric-delta {
    font-size: 0.72rem;
    font-weight: 700;
    margin-top: 0.2rem;
}
.ops-hero-metric-delta.up { color: #6ee7b7; }
.ops-hero-metric-delta.alert { color: #fca5a5; }
.ops-badge-new {
    position: absolute;
    top: 0.5rem;
    right: 0.55rem;
    background: #f472b6;
    color: #fff;
    font-size: 0.62rem;
    font-weight: 800;
    padding: 0.15rem 0.45rem;
    border-radius: 999px;
}

/* ── Section headings ────────────────────────────────────────── */
.section-heading {
    color: var(--text);
    font-size: 1.05rem;
    font-weight: 800;
    margin: 1.1rem 0 0.65rem 0;
}

/* ── White cards ─────────────────────────────────────────────── */
.ops-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1rem 1.1rem;
    box-shadow: var(--shadow);
    margin-bottom: 0.75rem;
}
.ops-card-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.65rem;
    margin-bottom: 0.75rem;
}
.ops-mini-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 0.95rem 1rem;
    box-shadow: var(--shadow);
}
.ops-mini-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    margin-bottom: 0.45rem;
}
.ops-mini-icon.cash  { background: var(--blue-light); color: var(--blue); }
.ops-mini-icon.cases { background: var(--purple-bg); color: var(--purple); }
.ops-mini-label {
    color: var(--text-soft);
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.ops-mini-value {
    color: var(--text);
    font-size: 1.35rem;
    font-weight: 800;
    margin-top: 0.2rem;
}

/* ── Provider health rows ──────────────────────────────────────── */
.provider-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.65rem 0;
    border-bottom: 1px solid var(--border);
    gap: 0.75rem;
}
.provider-row:last-child { border-bottom: none; }
.provider-row-left {
    display: flex;
    align-items: center;
    gap: 0.65rem;
}
.provider-icon {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
    font-weight: 800;
}
.provider-icon.nagad { background: var(--orange-bg); color: var(--orange); }
.provider-icon.bkash { background: #fce7f3; color: #ec4899; }
.provider-name { font-weight: 700; color: var(--text); font-size: 0.92rem; }
.provider-meta { color: var(--text-soft); font-size: 0.78rem; margin-top: 0.1rem; }
.uptime-badge {
    background: var(--green-bg);
    color: #047857;
    font-size: 0.68rem;
    font-weight: 800;
    padding: 0.25rem 0.55rem;
    border-radius: 999px;
    white-space: nowrap;
}
.uptime-badge.warn {
    background: var(--orange-bg);
    color: #c2410c;
}

/* ── Investigate role filter ─────────────────────────────────── */
.investigate-role-filter-wrap {
    margin: 0 0 1rem 0;
    position: relative;
    z-index: 30;
    clear: both;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.75rem 0.9rem;
    box-shadow: var(--shadow);
}
.investigate-role-filter-wrap + div {
    position: relative;
    z-index: 1;
}
.investigate-role-filter-wrap div[data-testid="stSelectbox"] > div > div {
    border-radius: 10px !important;
}
div[data-baseweb="popover"] {
    z-index: 1000 !important;
}

/* ── Alert detail summary cards ──────────────────────────────── */
.alert-summary-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.6rem;
    margin: 0.35rem 0 1rem;
}
@media (max-width: 760px) {
    .alert-summary-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
.alert-summary-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.85rem 0.95rem;
    box-shadow: var(--shadow);
    min-width: 0;
}
.alert-summary-label {
    color: var(--text-soft);
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.alert-summary-value {
    color: var(--blue);
    font-size: clamp(0.82rem, 2.4vw, 1.15rem);
    font-weight: 800;
    line-height: 1.35;
    margin-top: 0.2rem;
    white-space: normal;
    overflow-wrap: anywhere;
    word-break: break-word;
}

/* ── Investigate agent list ──────────────────────────────────── */
.investigate-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.85rem 0;
    border-bottom: 1px solid var(--border);
    gap: 0.5rem;
}
.investigate-row:last-child { border-bottom: none; }
.investigate-left {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    min-width: 0;
}
.agent-avatar {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    background: var(--blue-light);
    color: var(--blue);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    flex-shrink: 0;
    position: relative;
}
.agent-avatar.alert::after {
    content: "";
    position: absolute;
    top: 2px;
    right: 2px;
    width: 10px;
    height: 10px;
    background: var(--red);
    border: 2px solid #fff;
    border-radius: 50%;
}
.investigate-code {
    font-weight: 800;
    color: var(--text);
    font-size: 0.9rem;
}
.investigate-status {
    font-size: 0.78rem;
    margin-top: 0.12rem;
}
.investigate-status.ok { color: var(--text-soft); }
.investigate-status.alert { color: var(--red); font-weight: 600; }
.investigate-chevron {
    color: var(--muted);
    font-size: 1.2rem;
    font-weight: 300;
}

/* ── Bottom nav bar ──────────────────────────────────────────── */
.bottom-nav {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.35rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 0.55rem 0.4rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}
.bottom-nav .stButton > button {
    background: transparent !important;
    border: none !important;
    color: var(--muted) !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    min-height: 2.6rem !important;
    border-radius: 12px !important;
    box-shadow: none !important;
    padding: 0.35rem 0.2rem !important;
}
.bottom-nav .stButton > button:hover {
    background: var(--surface-soft) !important;
    color: var(--blue) !important;
}
.bottom-nav .stButton > button[kind="primary"] {
    background: var(--blue-light) !important;
    color: var(--blue) !important;
    box-shadow: none !important;
}
.nav-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    background: var(--red);
    border-radius: 50%;
    margin-left: 2px;
    vertical-align: super;
}

/* ── Metrics ─────────────────────────────────────────────────── */
div[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.85rem 1rem;
    box-shadow: var(--shadow);
}
div[data-testid="stMetricLabel"] {
    color: var(--text-soft) !important;
    font-size: 0.72rem !important;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="stMetricValue"] {
    color: var(--blue) !important;
    font-size: 1.35rem !important;
    font-weight: 800;
}

/* ── Containers & forms ──────────────────────────────────────── */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 0.75rem 0.9rem !important;
    box-shadow: var(--shadow);
    margin-bottom: 0.75rem !important;
}

.stButton > button {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    min-height: 2.35rem;
}
.stButton > button:hover {
    border-color: var(--blue) !important;
    color: var(--blue) !important;
}
.stButton > button[kind="primary"] {
    background: var(--blue) !important;
    border-color: var(--blue) !important;
    color: #ffffff !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--blue-dark) !important;
}

div[data-testid="stForm"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 1rem !important;
    box-shadow: var(--shadow);
}

div[data-testid="stSelectbox"] > div > div,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background: var(--surface-soft) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
}

.stTabs [data-testid="stTab"][aria-selected="true"] {
    color: var(--blue) !important;
    border-bottom: 2px solid var(--blue) !important;
}
.stTabs [data-testid="stTab"] {
    color: var(--text-soft) !important;
    font-weight: 700;
}

div[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
}

div[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    background: var(--surface) !important;
}

hr { border-color: var(--border) !important; }

/* ── Brand (compact context bar) ─────────────────────────────── */
.brand-kicker {
    color: var(--blue);
    font-size: .68rem;
    font-weight: 800;
    letter-spacing: .12em;
    text-transform: uppercase;
}
.brand-title {
    color: var(--text);
    font-size: 1.15rem;
    font-weight: 800;
}
.brand-subtitle { color: var(--text-soft); font-size: .82rem; }

.status-pill {
    background: var(--surface-soft);
    border: 1px solid var(--border);
    border-radius: 999px;
    color: var(--text-soft);
    font-size: .72rem;
    font-weight: 700;
    padding: .3rem .65rem;
}
.status-pill.ok { border-color: #a7f3d0; color: #047857; background: var(--green-bg); }
.status-pill.bad { border-color: #fecaca; color: var(--red); background: var(--red-bg); }

.section-intro {
    color: var(--text-soft);
    font-size: .9rem;
    line-height: 1.55;
    margin-bottom: 1rem;
}

.notice {
    background: var(--blue-light);
    border: 1px solid #bfdbfe;
    border-left: 3px solid var(--blue);
    border-radius: 10px;
    color: var(--text-soft);
    font-size: .82rem;
    padding: .65rem .9rem;
    margin: .5rem 0 .85rem;
}

.balance-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    min-height: 150px;
    padding: 1rem;
    box-shadow: var(--shadow);
}
.balance-card.cash  { border-top: 3px solid var(--blue); }
.balance-card.bkash { border-top: 3px solid #ec4899; }
.balance-card.nagad { border-top: 3px solid var(--orange); }
.balance-card.other { border-top: 3px solid var(--muted); }

.card-eyebrow {
    color: var(--text-soft);
    font-size: .68rem;
    font-weight: 800;
    letter-spacing: .08em;
    text-transform: uppercase;
}
.card-title { color: var(--text); font-size: .95rem; font-weight: 700; margin-top: .3rem; }
.card-amount { color: var(--text); font-size: 1.6rem; font-weight: 800; margin: .25rem 0; }
.card-meta { color: var(--text-soft); font-size: .76rem; line-height: 1.45; }

.alert-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--muted);
    border-radius: 14px;
    margin-bottom: .6rem;
    padding: .85rem 1rem;
    box-shadow: var(--shadow);
}
.alert-card.high, .alert-card.critical {
    border-left-color: var(--red);
    background: #fff5f5;
}
.alert-card.medium { border-left-color: var(--orange); }
.alert-title { color: var(--text); font-size: .92rem; font-weight: 700; }
.alert-meta { color: var(--text-soft); font-size: .76rem; margin-top: .25rem; }

.recipe-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: .8rem .95rem;
    margin-bottom: .45rem;
    box-shadow: var(--shadow);
}
.recipe-card.danger { border-color: #fecaca; background: #fff5f5; }
.recipe-card.warn   { border-color: #fed7aa; background: #fffbeb; }
.recipe-card.ok     { border-color: #a7f3d0; background: #f0fdf4; }
.recipe-title { font-size: .86rem; font-weight: 800; color: var(--text); }
.recipe-desc  { font-size: .78rem; color: var(--text-soft); margin-top: .15rem; }
.recipe-expect { font-size: .74rem; margin-top: .3rem; font-weight: 700; }
.recipe-card.danger .recipe-expect { color: var(--red); }
.recipe-card.warn   .recipe-expect { color: #c2410c; }
.recipe-card.ok     .recipe-expect { color: #047857; }

.result-banner {
    border-radius: 14px;
    padding: 1rem 1.15rem;
    margin: .6rem 0 .85rem;
    font-size: 1rem;
    font-weight: 800;
}
.result-banner.pass { background: var(--green-bg); border: 1px solid #a7f3d0; color: #047857; }
.result-banner.fail { background: var(--red-bg); border: 1px solid #fecaca; color: #b91c1c; }
.result-banner.warn { background: var(--orange-bg); border: 1px solid #fed7aa; color: #c2410c; }

.empty-state {
    background: var(--surface);
    border: 1px dashed var(--border);
    border-radius: 14px;
    color: var(--text-soft);
    padding: 1.25rem;
    text-align: center;
    font-size: .88rem;
}

.resource-note {
    background: var(--surface-soft);
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--text-soft);
    font-size: .82rem;
    padding: .65rem .85rem;
    margin-top: .5rem;
}

.stCaption, small { color: var(--text-soft) !important; }
code, pre {
    background: var(--surface-soft) !important;
    border: 1px solid var(--border) !important;
    color: var(--blue-dark) !important;
    border-radius: 8px !important;
}
</style>
"""


def apply_app_styles() -> None:
    """Install the app-wide CSS theme."""

    st.markdown(APP_CSS, unsafe_allow_html=True)
