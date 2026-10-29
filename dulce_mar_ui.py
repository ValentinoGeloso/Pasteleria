"""Visual language for Dulce Mar, with no data, authentication or secret access.

Call ``apply_design`` once after page configuration. The rendering helpers only
emit presentation markup. Dynamic text is escaped before it reaches HTML.
"""

from html import escape

import streamlit as st


COLORS = {
    "paper": "#F7FAF9",
    "sea_mist": "#E9F3F0",
    "marine": "#183C42",
    "teal": "#176B65",
    "butter": "#F0D99A",
    "muted": "#576F72",
    "line": "#D5E3DF",
}


_CSS = """
<style>
:root {
  --dm-paper:#F7FAF9; --dm-surface:#FFFFFF; --dm-mist:#E9F3F0;
  --dm-ink:#183C42; --dm-accent:#176B65; --dm-accent-dark:#10544F;
  --dm-muted:#576F72; --dm-line:#D5E3DF; --dm-butter:#F0D99A;
}
[data-testid="stAppViewContainer"] {
  background:var(--dm-paper); color:var(--dm-ink);
}
[data-testid="stHeader"] {background:rgba(247,250,249,.96);}
[data-testid="stMainBlockContainer"] {
  max-width:1460px; padding:2.2rem 3rem 4rem;
}
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] input,
[data-testid="stAppViewContainer"] textarea {
  font-family:"Aptos","Segoe UI",Arial,sans-serif;
}
[data-testid="stMarkdownContainer"] p {line-height:1.65; text-wrap:pretty;}
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
  color:var(--dm-ink); letter-spacing:-.035em; text-wrap:balance;
}
[data-testid="stMarkdownContainer"] h1 {font-size:2.2rem; font-weight:650;}
[data-testid="stMarkdownContainer"] h2 {font-size:1.6rem; font-weight:650;}
[data-testid="stMarkdownContainer"] h3 {font-size:1.13rem; font-weight:650;}
[data-testid="stCaptionContainer"] {color:var(--dm-muted);}
[data-testid="stCaptionContainer"] p {line-height:1.5; color:var(--dm-muted); opacity:1;}
[data-testid="stSidebar"] {
  background:var(--dm-mist); border-right:1px solid var(--dm-line);
}
[data-testid="stSidebarContent"] {padding:1.35rem 1rem;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap:.9rem;}
[data-testid="stSidebar"] [data-testid="stRadio"],
[data-testid="stSidebar"] [data-testid="stRadioGroup"] {width:100%;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {gap:.3rem;}
[data-testid="stSidebar"] label[data-baseweb="radio"] {
  min-height:45px; padding:.6rem .7rem; margin:0; border-radius:8px;
  border:1px solid transparent; transition:background-color 160ms ease;
}
[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {background:#F5FAF8;}
[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {
  color:var(--dm-ink); background:white; border-color:#CBDDD7;
  box-shadow:inset 3px 0 0 var(--dm-accent);
}
[data-testid="stSidebar"] label[data-baseweb="radio"] p {font-size:.94rem; font-weight:550;}
[data-testid="stSidebar"] [data-testid="stRadioOption"] {
  width:100%; box-sizing:border-box;
  min-height:44px; padding:.6rem .8rem; margin:.1rem 0;
  border-radius:7px; border:1px solid transparent;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover {background:#F5FAF8;}
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] {
  background:white; border-color:#CBDDD7; box-shadow:inset 3px 0 0 var(--dm-accent);
}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div > div:first-child {display:none;}
[data-testid="stSidebar"] [data-testid="stRadioOption"] p {font-weight:550; font-size:.94rem;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {font-size:.78rem;}
[data-testid="stButton"] button,
[data-testid="stFormSubmitButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stLinkButton"] a {
  min-height:44px; border-radius:9px; font-weight:600;
  box-shadow:none; transition:background-color 160ms ease,border-color 160ms ease;
}
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"] {
  background:var(--dm-accent); border-color:var(--dm-accent); color:white;
}
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover {
  background:var(--dm-accent-dark); border-color:var(--dm-accent-dark); color:white;
}
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-secondaryFormSubmit"] {
  background:white; border-color:var(--dm-line); color:var(--dm-ink);
}
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-secondaryFormSubmit"]:hover {
  background:var(--dm-mist); border-color:#9DBEB3; color:var(--dm-ink);
}
[data-testid="stAppViewContainer"] button:focus-visible,
[data-testid="stAppViewContainer"] a:focus-visible,
[data-testid="stAppViewContainer"] input:focus-visible,
[data-testid="stAppViewContainer"] summary:focus-visible,
[data-testid="stSidebar"] label:has(input:focus-visible) {
  outline:3px solid #488D83; outline-offset:3px;
}
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stNumberInput"] [data-baseweb="input"],
[data-testid="stDateInput"] [data-baseweb="input"],
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div {
  background:white; border-color:var(--dm-line); border-radius:9px;
}
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
[data-testid="stNumberInput"] [data-baseweb="input"]:focus-within,
[data-testid="stDateInput"] [data-baseweb="input"]:focus-within,
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div {
  border-color:var(--dm-accent); box-shadow:0 0 0 2px #176B6518;
}
[data-testid="stWidgetLabel"] p {font-size:.86rem; font-weight:600;}
[data-testid="stMetric"] {
  padding:.9rem 1rem; min-height:96px; background:white;
  border:1px solid var(--dm-line); border-radius:12px;
}
[data-testid="stMetricLabel"] p {font-size:.8rem; font-weight:550; color:var(--dm-muted);}
[data-testid="stMetricValue"] {
  font-family:"Aptos","Segoe UI",Arial,sans-serif;
  font-size:clamp(1.45rem,2.25vw,2.2rem); color:var(--dm-ink);
  font-weight:650; letter-spacing:-.045em; font-variant-numeric:tabular-nums;
}
[data-testid="stMetricDelta"] {font-variant-numeric:tabular-nums;}
[data-testid="stMetricValue"] p {line-height:1.15; margin:0;}
[data-testid="stExpander"] {border:1px solid var(--dm-line); border-radius:11px; background:white;}
[data-testid="stExpander"] details summary {padding:.8rem 1rem;}
[data-testid="stExpander"] details summary:hover {background:#F1F7F4;}
[data-testid="stForm"] {border-color:var(--dm-line); border-radius:13px; background:white;}
[data-testid="stAlert"] {border-radius:10px;}
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {min-width:0; border-radius:9px;}
[data-testid="stTabs"] [role="tablist"] {border-color:var(--dm-line); gap:1.1rem;}
[data-testid="stTabs"] [role="tab"] {font-weight:600; min-height:44px;}
[data-testid="stMarkdownContainer"] hr {border-color:var(--dm-line); margin:1.5rem 0;}
.dm-brand {display:flex; align-items:center; gap:.75rem; margin:.25rem 0 1.3rem;}
.dm-brand-mark {width:44px; height:44px; color:var(--dm-accent); flex:none;}
.dm-brand-name {
  display:block; color:var(--dm-ink); font-family:Georgia,"Times New Roman",serif;
  font-size:2rem; line-height:1; font-weight:500; letter-spacing:-.055em;
}
.dm-brand-caption {display:block; margin-top:.4rem; color:var(--dm-muted); font-size:.73rem;}
.dm-brand--sidebar {gap:.6rem; margin:.2rem 0 1.2rem;}
.dm-brand--sidebar .dm-brand-name {font-size:1.8rem;}
.dm-brand--sidebar .dm-brand-mark {width:38px; height:38px;}
.dm-page-header {padding:.2rem 0 1.15rem; margin-bottom:.5rem; border-bottom:1px solid var(--dm-line);}
.dm-page-header h1 {
  margin:0 0 .45rem; padding:0; color:var(--dm-ink);
  font-family:Georgia,"Times New Roman",serif; font-size:clamp(2rem,3.2vw,2.8rem);
  line-height:1.15; letter-spacing:-.045em; font-weight:500;
}
.dm-page-header p {max-width:68ch; margin:0; color:var(--dm-muted); font-size:.95rem; line-height:1.6;}
.dm-page-section {display:block; color:var(--dm-accent); font-size:.8rem; font-weight:600; margin:0 0 .5rem;}
.dm-welcome {padding:1.25rem 1.5rem 1.8rem 0;}
.dm-welcome h1 {
  font-family:Georgia,"Times New Roman",serif; font-weight:500; color:var(--dm-ink);
  font-size:clamp(2.65rem,4.6vw,4.65rem); line-height:1.07; letter-spacing:-.065em;
  max-width:12ch; margin:1.5rem 0 1.15rem;
}
.dm-welcome .dm-lede {max-width:43ch; color:var(--dm-muted); font-size:1.05rem; line-height:1.7;}
.dm-ledger {margin-top:2.3rem; max-width:380px; padding-top:1.15rem; border-top:1px solid #ADCAC1;}
.dm-ledger-row {display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.65rem 0;}
.dm-ledger-label {font-size:.88rem; color:var(--dm-ink);}
.dm-ledger-line {height:6px; width:42%; max-width:145px; background:#D6E8E1; border-radius:2px;}
.dm-ledger-row:last-child .dm-ledger-line {width:27%; background:var(--dm-butter);}
.dm-ledger-note {color:var(--dm-muted); font-size:.78rem; margin-top:.8rem;}
.dm-access-title {font-family:Georgia,"Times New Roman",serif; color:var(--dm-ink); font-size:1.8rem; letter-spacing:-.035em; margin:.4rem 0 .65rem;}
.dm-access-description {color:var(--dm-muted); font-size:.94rem; max-width:38ch; margin-bottom:1.5rem;}
.dm-context {padding:.7rem 1rem; border-left:3px solid var(--dm-accent); background:var(--dm-mist); color:var(--dm-muted); font-size:.87rem; margin:.25rem 0 1rem;}
.dm-footer {color:var(--dm-muted); font-size:.75rem; padding-top:1rem; margin-top:1rem; border-top:1px solid var(--dm-line);}
.card-resumen {background:white; border:1px solid var(--dm-line); border-radius:12px; padding:1.2rem; margin:.3rem 0 1rem;}
.card-title {font-size:.82rem; color:var(--dm-muted); font-weight:550; margin-bottom:.35rem;}
.card-value {font-size:1.8rem; color:var(--dm-ink); font-weight:650; font-variant-numeric:tabular-nums; letter-spacing:-.04em;}
.venta-item {background:white; border:1px solid var(--dm-line); border-left:3px solid #83B3A5; border-radius:8px; padding:.9rem 1rem; margin-bottom:.55rem; color:var(--dm-ink);}
.small-muted {color:var(--dm-muted); font-size:.8rem;}
.positive {color:#216C50;}
.negative {color:#A23743;}
.dm-receipt-row {display:flex; justify-content:space-between; align-items:baseline; gap:1rem; padding:.75rem 0; font-size:.9rem; color:var(--dm-muted);}
.dm-receipt-row strong {color:var(--dm-ink); font-size:1.05rem; font-variant-numeric:tabular-nums; white-space:nowrap;}
.dm-receipt-margin {border-top:1px solid var(--dm-line); margin-bottom:.6rem;}
.st-key-venta_resumen [data-testid="stVerticalBlock"] {gap:.65rem;}
.st-key-venta_resumen [data-testid="stMetric"] {padding:.5rem 0; border:0; background:transparent; min-height:0;}
.st-key-venta_resumen [data-testid="stMetricValue"] {white-space:nowrap; font-size:2.2rem;}
.st-key-venta_resumen [data-testid="stMarkdownContainer"] hr {margin:.35rem 0;}
.st-key-resumen_principal {background:var(--dm-mist); border-radius:12px;}
.st-key-resumen_principal [data-testid="stMetric"] {border:0; background:transparent; min-height:88px;}
.st-key-login_access {background:white; padding:1.5rem; border-radius:14px;}
@media (min-width:641px) and (max-width:1200px) {
  .st-key-resumen_secundario [data-testid="stHorizontalBlock"] {
    display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem;
  }
  .st-key-resumen_secundario [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    width:100%; min-width:0;
  }
  .st-key-resumen_secundario [data-testid="stMetricValue"] {font-size:1.45rem; white-space:nowrap;}
}
@media (max-width:900px) {
  [data-testid="stMainBlockContainer"] {padding:1.6rem 1.4rem 3rem;}
  .dm-welcome {padding:0;}
  .dm-welcome h1 {font-size:3.1rem;}
  .dm-ledger {margin-top:1.25rem;}
}
@media (max-width:640px) {
  .st-key-resumen_principal [data-testid="stHorizontalBlock"],
  .st-key-resumen_secundario [data-testid="stHorizontalBlock"] {
    display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.8rem;
  }
  .st-key-resumen_principal [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
  .st-key-resumen_secundario [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    width:100%; min-width:0;
  }
  .st-key-resumen_principal [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {grid-column:1/-1;}
  .st-key-resumen_principal [data-testid="stMetric"] {padding:.4rem 0; min-height:unset;}
  .st-key-resumen_principal [data-testid="stMetricValue"] {font-size:1.1rem; white-space:nowrap;}
  .st-key-resumen_principal [data-testid="stColumn"]:first-child [data-testid="stMetricValue"] {font-size:1.8rem;}
  .st-key-resumen_secundario [data-testid="stMetricValue"] {font-size:1.05rem; white-space:nowrap;}
  [data-testid="stMainBlockContainer"] {padding:1.2rem 1rem 2.5rem;}
  .dm-page-header {padding-bottom:1rem;}
  .dm-page-header h1 {font-size:2rem;}
  .dm-welcome h1 {font-size:2.65rem; max-width:14ch; margin:1rem 0;}
  .dm-welcome .dm-lede {font-size:.96rem;}
  .dm-welcome {padding-bottom:.5rem;}
  .dm-ledger {display:none;}
  [data-testid="stMetric"] {padding:.9rem 1rem; min-height:100px;}
  [data-testid="stMetricValue"] {font-size:1.7rem;}
}
@media (prefers-reduced-motion:reduce) {
  [data-testid="stAppViewContainer"] button,
  [data-testid="stAppViewContainer"] a,
  [data-testid="stSidebar"] label {transition:none;}
}
</style>
"""


_MARK = """<svg class="dm-brand-mark" viewBox="0 0 48 48" fill="none" aria-hidden="true">
<path d="M24 3.5 42 14v20L24 44.5 6 34V14L24 3.5Z" stroke="currentColor" stroke-width="1.5"/>
<path d="M14 22c4.4-5.1 6.2 5.1 10.5 0s6.2 5.1 10.5 0M14 29c4.4-5.1 6.2 5.1 10.5 0s6.2 5.1 10.5 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
</svg>"""


def apply_design():
    """Apply the shared visual system without touching application state."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_brand(sidebar=False):
    """Render Dulce Mar's typographic mark in the main page or sidebar."""
    variant = " dm-brand--sidebar" if sidebar else ""
    markup = (
        f'<div class="dm-brand{variant}">{_MARK}<div>'
        '<span class="dm-brand-name">dulce mar</span>'
        '<span class="dm-brand-caption">Gestión de pastelería</span>'
        '</div></div>'
    )
    target = st.sidebar if sidebar else st
    target.markdown(markup, unsafe_allow_html=True)


def render_page_header(title, description, section=None):
    """Render one clear page title and its useful supporting description."""
    section_html = f'<span class="dm-page-section">{escape(str(section))}</span>' if section else ""
    st.markdown(
        f'<header class="dm-page-header">{section_html}'
        f'<h1>{escape(str(title))}</h1><p>{escape(str(description))}</p></header>',
        unsafe_allow_html=True,
    )


def render_login_intro():
    """A bakery-specific welcome; its ledger is decorative and contains no data."""
    render_brand()
    st.markdown(
        '<section class="dm-welcome">'
        '<h1>Tu negocio,<br>en su punto.</h1>'
        '<p class="dm-lede">Ventas, recetas y costos de Dulce Mar, reunidos para '
        'entender cómo va el negocio y decidir con más claridad.</p>'
        '<div class="dm-ledger" aria-hidden="true">'
        '<div class="dm-ledger-row"><span class="dm-ledger-label">Lo que vendés</span><span class="dm-ledger-line"></span></div>'
        '<div class="dm-ledger-row"><span class="dm-ledger-label">Lo que cuesta</span><span class="dm-ledger-line"></span></div>'
        '<div class="dm-ledger-row"><span class="dm-ledger-label">Lo que queda</span><span class="dm-ledger-line"></span></div>'
        '<p class="dm-ledger-note">De la receta al resultado.</p></div></section>',
        unsafe_allow_html=True,
    )


def style_chart(figure, *, money_axis="y", percentage_axis=None):
    """Give a Plotly figure the same restrained color and typography treatment."""
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Segoe UI, Arial, sans-serif", "color": COLORS["marine"], "size": 12},
        colorway=["#176B65", "#7BAA9C", "#F0D99A", "#6E90A1", "#A99576", "#B5CCC3"],
        margin={"l": 12, "r": 12, "t": 35, "b": 12},
        separators=",.",
        height=310,
        legend={"title_text": "", "bgcolor": "rgba(0,0,0,0)"},
        hoverlabel={"bgcolor": "#FFFFFF", "font_color": COLORS["marine"], "bordercolor": COLORS["line"]},
    )
    figure.update_xaxes(showgrid=False, linecolor=COLORS["line"], zeroline=False, title_font={"size": 12})
    figure.update_yaxes(gridcolor="#E2ECE7", zeroline=False, title_font={"size": 12})
    if money_axis in {"x", "y"}:
        update_axis = figure.update_xaxes if money_axis == "x" else figure.update_yaxes
        update_axis(tickprefix="$ ", tickformat=",.0f", hoverformat=",.2f")
    if percentage_axis in {"x", "y"}:
        update_axis = figure.update_xaxes if percentage_axis == "x" else figure.update_yaxes
        update_axis(tickprefix="", ticksuffix="%")
    return figure
