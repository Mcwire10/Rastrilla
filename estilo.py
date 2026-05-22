"""
estilo.py — CSS global de Rake
Llamar aplicar_estilos() al inicio de cada página, antes del auth guard.

Taste-skill applied:
- Outfit font (Inter banned for premium feel)
- Specific sidebar selectors (no wildcard *) → fixes toggle arrow + code blowup
- Tactile button feedback (scale on active)
- Metric labels uppercase + tracking
"""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap');

/* ── Tipografía global — Outfit (Inter banned per taste-skill) ─────────────── */
html, body, button, input, textarea, select,
[class*="css"], .stMarkdown, p, span, li {
    font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ── Sidebar — verde oscuro ─────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #14532d !important;
}

/* Textos: selectores específicos — sin wildcard * para no romper toggle ni code */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #dcfce7 !important;
}

/* Headings del sidebar: pequeños y discretos, no h2 gigante */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: #86efac !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    margin-bottom: 0.5rem !important;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.12) !important;
}

/* Code inline en el sidebar: pequeño, no rompas el layout */
[data-testid="stSidebar"] code {
    background: rgba(255,255,255,0.12) !important;
    color: #86efac !important;
    border-radius: 4px !important;
    font-size: 0.75em !important;
    display: inline !important;
    padding: 0.1em 0.35em !important;
    vertical-align: baseline !important;
}

/* ── Botón colapsar/expandir sidebar — flecha visible sobre fondo oscuro ────── */
[data-testid="stSidebarCollapseButton"] button {
    color: #dcfce7 !important;
    background: transparent !important;
    border: none !important;
}
[data-testid="stSidebarCollapseButton"] button:hover {
    background: rgba(255,255,255,0.1) !important;
    border-radius: 6px !important;
}
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapseButton"] path {
    fill: #dcfce7 !important;
    stroke: #dcfce7 !important;
}

/* Control de expansión cuando el sidebar está colapsado (en el área principal) */
[data-testid="stSidebarCollapsedControl"] button {
    background: #f0fdf4 !important;
    border: 1px solid #bbf7d0 !important;
    border-radius: 6px !important;
}
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] path {
    fill: #14532d !important;
}

/* Botones del sidebar (Cerrar sesión, Actualizar índice) */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid rgba(74, 222, 128, 0.5) !important;
    color: #dcfce7 !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    transition: background 0.15s ease, border-color 0.15s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(74, 222, 128, 0.1) !important;
    border-color: #86efac !important;
}

/* ── Headings principales (contenido, no sidebar) ───────────────────────────── */
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

/* ── Botones — tactile feedback (taste-skill: scale on active) ──────────────── */
.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    border-radius: 6px !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
.stButton > button:hover:not(:active),
.stDownloadButton > button:hover:not(:active),
.stFormSubmitButton > button:hover:not(:active) {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12) !important;
}
.stButton > button:active,
.stDownloadButton > button:active,
.stFormSubmitButton > button:active {
    transform: scale(0.98) translateY(1px) !important;
    box-shadow: none !important;
}

/* ── Métricas (taste-skill: uppercase labels + tracking) ────────────────────── */
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
    font-weight: 600 !important;
    color: #6b7280 !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* ── Formularios ────────────────────────────────────────────────────────────── */
[data-testid="stForm"] {
    border-radius: 10px !important;
    border: 1px solid #e5e7eb !important;
    padding: 1.25rem 1.25rem 0.75rem !important;
}

/* ── Contenedores con borde (admin cards) ───────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 10px !important;
    border-color: #e5e7eb !important;
}

/* ── File uploader — texto duplicado: ocultar la copia interna ──────────────── */
[data-testid="stFileUploaderDropzoneInstructions"] span + small,
[data-testid="stFileUploaderDropzone"] small {
    display: none !important;
}
/* Si el label aparece repetido dentro del dropzone */
[data-testid="stFileUploaderDropzoneInstructions"] > div > span:not(:first-child) {
    display: none !important;
}

/* ── DataEditor / DataFrame ──────────────────────────────────────────────────── */
[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* ── Dark mode ───────────────────────────────────────────────────────────────── */
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
    background-color: #0f1f14 !important;
}
</style>
"""


def aplicar_estilos() -> None:
    """Inyecta el CSS de Rake. Llamar al inicio de cada página."""
    st.markdown(_CSS, unsafe_allow_html=True)
