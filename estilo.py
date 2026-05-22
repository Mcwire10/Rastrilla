"""
estilo.py — CSS global de RASTRILLA
Llamar aplicar_estilos() al inicio de cada página, antes del auth guard.
"""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Tipografía global ────────────────────────────────────────────────────── */
html, body, [class*="css"], .stMarkdown, p, span, label, li {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ── Sidebar — verde oscuro siempre ─────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #14532d !important;
}
[data-testid="stSidebar"] * {
    color: #dcfce7 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #bbf7d0 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #166534 !important;
}
[data-testid="stSidebar"] code {
    background: rgba(255,255,255,0.12) !important;
    color: #86efac !important;
    border-radius: 4px !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid #4ade80 !important;
    color: #dcfce7 !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    transition: background 0.15s ease, border-color 0.15s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(74, 222, 128, 0.12) !important;
    border-color: #86efac !important;
}

/* ── Headings ─────────────────────────────────────────────────────────────── */
h1 {
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
}
h2 {
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
}
h3 {
    font-weight: 600 !important;
}

/* ── Botones ─────────────────────────────────────────────────────────────── */
.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    border-radius: 6px !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important;
}

/* ── Métricas ─────────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background-color: #f0fdf4 !important;
    border: 1px solid #bbf7d0 !important;
    border-radius: 10px !important;
    padding: 1rem 1.25rem !important;
}
[data-testid="stMetricValue"] {
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    font-weight: 500 !important;
    color: #374151 !important;
}

/* ── Formularios ─────────────────────────────────────────────────────────── */
[data-testid="stForm"] {
    border-radius: 10px !important;
    border: 1px solid #e5e7eb !important;
    padding: 1.25rem 1.25rem 0.75rem !important;
}

/* ── Contenedores con borde ───────────────────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 10px !important;
    border-color: #e5e7eb !important;
}

/* ── Alertas ─────────────────────────────────────────────────────────────── */
[data-testid="stNotification"],
.stAlert > div {
    border-radius: 8px !important;
}

/* ── DataEditor / DataFrame ───────────────────────────────────────────────── */
[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* ── Dark mode ───────────────────────────────────────────────────────────── */
[data-theme="dark"] [data-testid="stMetric"] {
    background-color: #1f2937 !important;
    border-color: #374151 !important;
}
[data-theme="dark"] [data-testid="stMetricLabel"] {
    color: #9ca3af !important;
}
[data-theme="dark"] [data-testid="stForm"] {
    border-color: #374151 !important;
}
[data-theme="dark"] [data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #374151 !important;
}
[data-theme="dark"] [data-testid="stSidebar"] {
    background-color: #111f17 !important;
}
</style>
"""


def aplicar_estilos() -> None:
    """Inyecta el CSS de RASTRILLA. Llamar al inicio de cada página."""
    st.markdown(_CSS, unsafe_allow_html=True)
