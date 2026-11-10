from __future__ import annotations

import html
from contextlib import contextmanager

import streamlit as st

# ----------------------------- Design tokens -----------------------------
DARK_GREEN = "#14532D"
GREEN = "#16A34A"
MINT = "#A7DDB5"
LIGHT_GREEN = "#DCFCE7"
BG = "#F1F8F2"
WHITE = "#FFFFFF"
TEXT = "#1F2937"
MUTED = "#64748B"

GREEN_SEQ = [GREEN, DARK_GREEN, "#22C55E", "#4ADE80", "#86EFAC", "#A7DDB5"]
GREEN_CONTINUOUS = ["#DCFCE7", "#A7DDB5", "#4ADE80", "#16A34A", "#14532D"]
GREEN_HEATMAP = [
    [0.0, "#F7FDF9"],
    [0.35, "#DCFCE7"],
    [0.70, "#A7DDB5"],
    [1.0, "#4ADE80"],
]

ICONS = {
    "wallet": '<rect x="3" y="6" width="18" height="14" rx="2"/><path d="M3 10h18"/><path d="M16 15h2"/>',
    "cart": '<circle cx="9" cy="20" r="1"/><circle cx="18" cy="20" r="1"/><path d="M3 4h2l2.4 11.2a2 2 0 0 0 2 1.6h7.7a2 2 0 0 0 2-1.6L21 8H6"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "receipt": '<path d="M6 2h12v20l-3-2-3 2-3-2-3 2V2z"/><path d="M9 7h6"/><path d="M9 11h6"/>',
    "repeat": '<path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>',
    "star": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    "alert": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "trending": '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    "chart": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "map": '<path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
}


def svg_icon(name: str, size: int = 18) -> str:
    path = ICONS.get(name, ICONS["chart"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round">{path}</svg>'
    )


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --dark-green: #14532D;
  --green: #16A34A;
  --mint: #A7DDB5;
  --light-green: #DCFCE7;
  --bg: #F1F8F2;
  --white: #FFFFFF;
  --text: #1F2937;
  --muted: #64748B;
}

html, body, .stApp, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: #1F2937;
}

#MainMenu, header[data-testid="stHeader"], footer,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], .stDeployButton,
[data-testid="stSidebar"], [data-testid="collapsedControl"] {
  display: none !important;
}

[data-testid="stAppViewContainer"] { background: #F1F8F2; }
[data-testid="stMainBlockContainer"], .block-container {
  max-width: 1480px;
  padding: 1.1rem 2.2rem 2.4rem;
}
[data-testid="stVerticalBlock"] { gap: 0.7rem; }
[data-testid="stHorizontalBlock"] { gap: 0.7rem; }

/* ------------------------------- Hero ------------------------------- */
.hero {
  background: #064E3B;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 30px 24px;
  min-height: 108px;
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  margin-bottom: 4px;
  box-shadow: 0 8px 24px rgba(6, 78, 59, 0.16);
}
.hero-title {
  font-size: 34px; font-weight: 800; color: #FFFFFF !important;
  margin: 0; letter-spacing: -0.03em; line-height: 1.12;
}
.hero-title span { color: #6EE7B7 !important; }

/* ------------------------------ Cards ------------------------------- */
.card-marker { display: none; }
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .card-marker) {
  background: #FFFFFF !important;
  border: 1px solid #DCFCE7 !important;
  border-radius: 16px !important;
  padding: 14px 16px 12px !important;
  gap: 0.55rem !important;
  box-shadow: 0 1px 3px rgba(20, 83, 45, 0.06);
}
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .card-marker) > div[data-testid="stLayoutWrapper"] {
  padding: 0 !important;
}

/* ------------------------------- KPI -------------------------------- */
.kpi-card {
  background: #FFFFFF;
  border: 1px solid #DCFCE7;
  border-radius: 16px;
  padding: 12px 14px;
  box-shadow: 0 1px 3px rgba(20, 83, 45, 0.06);
  min-height: 116px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.kpi-top { display: flex; align-items: center; gap: 9px; margin-bottom: 6px; }
.kpi-icon {
  width: 30px; height: 30px; flex: 0 0 30px;
  border-radius: 9px; background: #DCFCE7; color: #16A34A;
  display: flex; align-items: center; justify-content: center;
}
.kpi-label {
  font-size: 11px; font-weight: 600; color: #64748B;
  letter-spacing: 0.02em; line-height: 1.25;
}
.kpi-value {
  font-size: clamp(18px, 1.45vw, 25px);
  font-weight: 800; color: #14532D;
  line-height: 1.1; letter-spacing: -0.02em; white-space: nowrap;
}
.kpi-foot { display: flex; align-items: center; gap: 7px; margin-top: 6px; flex-wrap: wrap; }
.kpi-badge {
  background: #DCFCE7; color: #14532D;
  font-size: 10.5px; font-weight: 700;
  padding: 2px 8px; border-radius: 999px;
}
.kpi-badge.down { background: #FEF3C7; color: #92400E; }
.kpi-note { font-size: 10.5px; color: #94A3B8; line-height: 1.3; }

/* --------------------------- Section / chart ------------------------ */
.section-head { margin: 10px 0 0; }
.section-head h2 {
  font-size: 18px; font-weight: 700; color: #14532D;
  margin: 0; letter-spacing: -0.01em;
}

.chart-head { margin-bottom: 2px; }
.chart-head h3 { font-size: 14px; font-weight: 700; color: #1F2937; margin: 0; }
.chart-head p { font-size: 11px; color: #64748B; margin: 2px 0 0; }

.js-plotly-plot { border-radius: 10px; }

/* ------------------------------- Table ------------------------------ */
.table-wrap {
  overflow: auto;
  border: 1px solid #E5EFE7;
  border-radius: 12px;
}
table.data-table {
  width: 100%; border-collapse: collapse;
  font-size: 12px; min-width: 640px;
}
table.data-table thead th {
  position: sticky; top: 0;
  background: #F7FDF9; color: #64748B;
  font-size: 10px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.06em;
  text-align: left; padding: 8px 10px;
  border-bottom: 1px solid #DCFCE7; white-space: nowrap;
}
table.data-table tbody td {
  padding: 8px 10px;
  border-bottom: 1px solid #F1F5F9;
  color: #1F2937; vertical-align: middle; white-space: nowrap;
}
table.data-table tbody tr:hover { background: #F7FDF9; }
table.data-table tbody tr:last-child td { border-bottom: none; }
.cell-strong { font-weight: 700; color: #14532D; }
.cell-muted { color: #64748B; }
.chip {
  display: inline-block; padding: 2px 9px; border-radius: 999px;
  font-size: 10.5px; font-weight: 700; white-space: nowrap;
}
.chip-green { background: #DCFCE7; color: #14532D; }
.chip-amber { background: #FEF3C7; color: #92400E; }
.chip-red { background: #FEE2E2; color: #991B1B; }
.chip-gray { background: #F1F5F9; color: #475569; }

/* -------------------------------- Tabs ------------------------------ */
div[data-baseweb="tab-list"] {
  gap: 6px; background: #FFFFFF; padding: 6px;
  border-radius: 12px; border: 1px solid #DCFCE7;
  width: fit-content; box-shadow: 0 1px 3px rgba(20, 83, 45, 0.04);
}
button[data-baseweb="tab"] {
  border-radius: 9px; padding: 7px 16px;
  color: #64748B; font-weight: 600; font-size: 13px;
  background: transparent;
}
button[data-baseweb="tab"]:hover { background: #F1F8F2; color: #14532D; }
button[data-baseweb="tab"][aria-selected="true"] { background: #DCFCE7; color: #14532D; }
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display: none; }
[data-testid="stTabs"] { margin-top: 4px; }

/* ------------------------------ Widgets ----------------------------- */
label[data-testid="stWidgetLabel"] p {
  font-size: 11.5px; font-weight: 600; color: #64748B; letter-spacing: 0.02em;
}
div[data-baseweb="select"] > div {
  border-radius: 10px; border-color: #DCFCE7; background: #FFFFFF;
}
div[data-baseweb="select"] > div:hover { border-color: #A7DDB5; }
div[data-baseweb="input"] { border-radius: 10px; border-color: #DCFCE7; }
[data-testid="stDateInput"] input { border-radius: 10px; font-size: 13px; }
.stMultiSelect [data-baseweb="tag"] {
  background: #DCFCE7 !important; color: #14532D !important;
  border-radius: 6px !important;
}
/* ---------------------------- Scrollbar ----------------------------- */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: #A7DDB5; border-radius: 999px; }
::-webkit-scrollbar-track { background: #F1F8F2; }

/* ---------------------------- Responsive ---------------------------- */
@media (max-width: 900px) {
  [data-testid="stMainBlockContainer"], .block-container { padding: 1rem 1rem 2rem; }
  .hero { padding: 24px 16px; min-height: 96px; }
  .hero-title { font-size: 26px; }
  div[data-baseweb="tab-list"] {
    width: 100%; flex-wrap: wrap; overflow-x: auto;
  }
  button[data-baseweb="tab"] { padding: 7px 12px; font-size: 12px; }
  .js-plotly-plot .heatmap-label { font-size: 8px !important; }
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def page_header() -> None:
    st.markdown(
        """
        <div class="hero">
          <h1 class="hero-title">CRM <span>Analytics</span> Dashboard</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str) -> None:
    st.markdown(
        f'<div class="section-head"><h2>{html.escape(title)}</h2></div>',
        unsafe_allow_html=True,
    )


def kpi_card(
    icon: str,
    label: str,
    value: str,
    note: str = "",
    delta: float | None = None,
) -> None:
    badge = ""
    if delta is not None:
        tone = "" if delta >= 0 else " down"
        arrow = "&#9650;" if delta >= 0 else "&#9660;"
        badge = f'<span class="kpi-badge{tone}">{arrow} {abs(delta):.1f}%</span>'
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-top">
            <div class="kpi-icon">{svg_icon(icon, 17)}</div>
            <div class="kpi-label">{html.escape(label)}</div>
          </div>
          <div class="kpi-value">{html.escape(value)}</div>
          <div class="kpi-foot">{badge}<span class="kpi-note">{html.escape(note)}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(items: list[dict]) -> None:
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            kpi_card(**item)


@contextmanager
def panel(title: str, subtitle: str = ""):
    with st.container():
        sub = f"<p>{html.escape(subtitle)}</p>" if subtitle else ""
        st.markdown(
            f'<div class="chart-head"><span class="card-marker"></span>'
            f"<h3>{html.escape(title)}</h3>{sub}</div>",
            unsafe_allow_html=True,
        )
        yield


def chart_card(title: str, subtitle: str, fig, key: str | None = None) -> None:
    with panel(title, subtitle):
        st.plotly_chart(
            fig,
            width="stretch",
            config={"displayModeBar": False, "responsive": True},
            key=key,
        )


def chip(text: str, tone: str = "green") -> str:
    return f'<span class="chip chip-{tone}">{html.escape(str(text))}</span>'


def strong(text: str) -> str:
    return f'<span class="cell-strong">{html.escape(str(text))}</span>'


def muted(text: str) -> str:
    return f'<span class="cell-muted">{html.escape(str(text))}</span>'


SEGMENT_TONE = {
    "Champions": "green",
    "Loyal": "green",
    "Potensial Loyal": "green",
    "Pelanggan Baru": "green",
    "Perlu Perhatian": "amber",
    "Tidak Boleh Hilang": "amber",
    "Berisiko": "amber",
    "Hibernasi": "red",
    "Hilang": "red",
}


def segment_chip(segment: str) -> str:
    return chip(segment, SEGMENT_TONE.get(segment, "gray"))


def render_table(
    headers: list[str],
    rows: list[list[str]],
    max_height: int | None = None,
    min_width: int | None = None,
) -> None:
    style = f' style="max-height:{max_height}px"' if max_height else ""
    table_style = f' style="min-width:{min_width}px"' if min_width else ""
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows
    )
    st.markdown(
        f'<div class="table-wrap"{style}><table class="data-table"{table_style}>'
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def theme(fig, height: int = 360, legend: bool = False):
    fig.update_layout(
        height=height,
        font=dict(family="Inter, sans-serif", size=12, color=TEXT),
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        margin=dict(l=4, r=22, t=8, b=4),
        colorway=GREEN_SEQ,
        hoverlabel=dict(
            bgcolor=WHITE,
            bordercolor=LIGHT_GREEN,
            font=dict(color=TEXT, family="Inter", size=12),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.0,
            x=0,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=legend,
    )
    fig.update_xaxes(
        gridcolor="#EEF5EF",
        linecolor="#DCFCE7",
        zeroline=False,
        tickfont=dict(size=11),
        title_font=dict(size=11, color=MUTED),
        automargin=True,
    )
    fig.update_yaxes(
        gridcolor="#EEF5EF",
        linecolor="#DCFCE7",
        zeroline=False,
        tickfont=dict(size=11),
        title_font=dict(size=11, color=MUTED),
        automargin=True,
    )
    return fig
