"""
estilo.py — CSS global de Rake
Taste-skill: DESIGN_VARIANCE=8, MOTION_INTENSITY=6, VISUAL_DENSITY=4
- Outfit font (Inter banned)
- Login split-screen con brand panel fijo (DV:8 — asymmetric)
- Fade-in + cubic-bezier + tactile buttons (MI:6 — fluid CSS)
- Daily-app spacing con métricas con respiro (VD:4)
- Sidebar específico sin wildcard * (fix toggle arrow + code size)
"""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap');

/* ── Tipografía global — Outfit (taste-skill: Inter banned) ─────────────────── */
/* IMPORTANT: do NOT include button/span/svg here — breaks Material Symbols icons */
body, input, textarea, select, p, li, .stMarkdown {
    font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}


/* ══════════════════════════════════════════════════════════════════════════════ */
/*  LOGIN SPLIT-SCREEN  (DESIGN_VARIANCE: 8 — asymmetric, left-aligned)         */
/* ══════════════════════════════════════════════════════════════════════════════ */

/* Fondo dividido: verde oscuro izquierda / gris muy suave derecha */
body:has(.login-bg-panel) {
    background: linear-gradient(90deg, #14532d 50%, #f9fafb 50%) !important;
    min-height: 100vh !important;
}

/* Transparentar todos los contenedores de Streamlit para que muestre el fondo */
body:has(.login-bg-panel) [data-testid="stApp"],
body:has(.login-bg-panel) [data-testid="stAppViewContainer"],
body:has(.login-bg-panel) [data-testid="stMain"],
body:has(.login-bg-panel) [data-testid="stMainBlockContainer"],
body:has(.login-bg-panel) section.main {
    background: transparent !important;
}

/* Sin padding horizontal — split edge-to-edge */
body:has(.login-bg-panel) [data-testid="stMainBlockContainer"] {
    padding: 0 !important;
    max-width: 100vw !important;
}

/* Ocultar sidebar, header y footer durante el login */
body:has(.login-bg-panel) [data-testid="stSidebar"],
body:has(.login-bg-panel) [data-testid="stSidebarCollapseButton"],
body:has(.login-bg-panel) [data-testid="stSidebarCollapsedControl"],
body:has(.login-bg-panel) [data-testid="stHeader"],
body:has(.login-bg-panel) [data-testid="stToolbar"],
body:has(.login-bg-panel) footer,
body:has(.login-bg-panel) [data-testid="stBottom"] {
    display: none !important;
}

/* Panel de marca — fijo sobre la mitad izquierda */
.login-bg-panel {
    position: fixed;
    top: 0;
    left: 0;
    width: 50vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 0 4rem;
    pointer-events: none;
    z-index: 1;
}

.login-brand-eyebrow {
    font-size: 0.65rem;
    font-weight: 600;
    color: #4ade80;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    margin-bottom: 1.5rem;
    font-family: 'Outfit', sans-serif;
}

.login-brand-name {
    font-size: 5.5rem;
    font-weight: 700;
    color: #f0fdf4;
    letter-spacing: -0.05em;
    line-height: 0.9;
    margin-bottom: 2rem;
    font-family: 'Outfit', sans-serif;
}

.login-brand-desc {
    font-size: 1rem;
    color: rgba(134, 239, 172, 0.85);
    line-height: 1.75;
    font-weight: 400;
    margin-bottom: 2.5rem;
    font-family: 'Outfit', sans-serif;
}

.login-brand-tag {
    font-size: 0.62rem;
    color: rgba(187, 247, 208, 0.3);
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-weight: 500;
    font-family: 'Outfit', sans-serif;
}

/* Espaciador vertical antes del formulario (desktop = 22vh, se sobreescribe en mobile) */
.login-spacer {
    height: 22vh;
}

/* Header del formulario — derecha */
.login-form-area {
    position: relative;
    z-index: 2;
    padding: 0 0.25rem;
    margin-bottom: -0.25rem;
}

.login-form-heading {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #111827 !important;
    letter-spacing: -0.02em !important;
    margin: 0 0 0.3rem 0 !important;
    font-family: 'Outfit', sans-serif !important;
    line-height: 1.2 !important;
}

.login-form-sub {
    font-size: 0.875rem !important;
    color: #6b7280 !important;
    margin: 0 0 1rem 0 !important;
    font-family: 'Outfit', sans-serif !important;
}


/* ══════════════════════════════════════════════════════════════════════════════ */
/*  SIDEBAR — verde oscuro permanente                                             */
/* ══════════════════════════════════════════════════════════════════════════════ */

[data-testid="stSidebar"] {
    background-color: #14532d !important;
}

/* Selectores específicos — sin wildcard * (evita romper toggle y code) */
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

/* Headings del sidebar — pequeños, sin el h2 gigante */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: #86efac !important;
    font-size: 0.65rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    margin-bottom: 0.5rem !important;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.1) !important;
}

/* Inline code en sidebar — pequeño y controlado */
[data-testid="stSidebar"] code {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #86efac !important;
    border-radius: 4px !important;
    font-size: 0.75em !important;
    display: inline !important;
    padding: 0.1em 0.35em !important;
    vertical-align: baseline !important;
}

/* Botón colapsar sidebar — ícono visible sobre fondo verde oscuro */
[data-testid="stSidebarCollapseButton"] button {
    color: #dcfce7 !important;
    background: transparent !important;
    border: none !important;
}
[data-testid="stSidebarCollapseButton"] button:hover {
    background: rgba(255, 255, 255, 0.08) !important;
    border-radius: 6px !important;
}
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapseButton"] path {
    fill: #dcfce7 !important;
    color: #dcfce7 !important;
}

/* Botón expandir (sidebar colapsado) */
[data-testid="stSidebarCollapsedControl"] button {
    background: #f0fdf4 !important;
    border: 1px solid #bbf7d0 !important;
    border-radius: 6px !important;
}
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] path {
    fill: #14532d !important;
}

/* Botones del sidebar — blancos sobre verde oscuro */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255, 255, 255, 0.92) !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    color: #052e16 !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    transition: background 0.15s ease, border-color 0.15s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #ffffff !important;
    border-color: rgba(255, 255, 255, 0.6) !important;
    color: #052e16 !important;
}
/* Los <p> y <span> dentro del botón heredan el verde claro del sidebar —
   necesitan sobreescritura explícita para mantener texto oscuro sobre blanco */
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span,
[data-testid="stSidebar"] .stButton > button div {
    color: #052e16 !important;
}

/* Logo brand — st.page_link al tope del sidebar */
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.04em !important;
    color: #f0fdf4 !important;
    background: transparent !important;
    border-radius: 8px !important;
    padding: 0.3rem 0.5rem !important;
    text-decoration: none !important;
    transition: color 0.18s ease, background 0.18s ease !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.4rem !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
    color: #86efac !important;
    background: rgba(255, 255, 255, 0.06) !important;
}
/* Suprimir el highlight de "página activa" en el logo */
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current],
[data-testid="stSidebar"] [data-testid="stPageLink"] a[data-active="true"] {
    background: transparent !important;
    color: #4ade80 !important;
}


/* ══════════════════════════════════════════════════════════════════════════════ */
/*  TIPOGRAFÍA                                                                    */
/* ══════════════════════════════════════════════════════════════════════════════ */

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


/* ══════════════════════════════════════════════════════════════════════════════ */
/*  BOTONES — tactile feedback (MOTION_INTENSITY: 6)                              */
/* ══════════════════════════════════════════════════════════════════════════════ */

.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    border-radius: 6px !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
.stButton > button:hover:not(:active),
.stDownloadButton > button:hover:not(:active),
.stFormSubmitButton > button:hover:not(:active) {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12) !important;
}
.stButton > button:active,
.stDownloadButton > button:active,
.stFormSubmitButton > button:active {
    transform: scale(0.98) translateY(1px) !important;
    box-shadow: none !important;
}


/* ══════════════════════════════════════════════════════════════════════════════ */
/*  MÉTRICAS (taste-skill: uppercase labels + tracking, VD:4)                    */
/* ══════════════════════════════════════════════════════════════════════════════ */

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
    font-size: 0.65rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}


/* ══════════════════════════════════════════════════════════════════════════════ */
/*  FORMULARIOS Y CONTENEDORES                                                    */
/* ══════════════════════════════════════════════════════════════════════════════ */

[data-testid="stForm"] {
    border-radius: 10px !important;
    border: 1px solid #e5e7eb !important;
    padding: 1.25rem 1.25rem 0.75rem !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 10px !important;
    border-color: #e5e7eb !important;
}

/* Input focus ring (MI:6) */
[data-baseweb="input"] input:focus,
[data-baseweb="base-input"] input:focus {
    border-color: #16a34a !important;
    box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.15) !important;
    transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
    outline: none !important;
}

/* File uploader: ocultar texto duplicado bajo el dropzone */
[data-testid="stFileUploaderDropzoneInstructions"] span + small,
[data-testid="stFileUploaderDropzone"] small {
    display: none !important;
}

[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    border-radius: 8px !important;
    overflow: hidden !important;
}


/* ══════════════════════════════════════════════════════════════════════════════ */
/*  ANIMACIÓN DE ENTRADA (MOTION_INTENSITY: 6 — fluid CSS, cubic-bezier)         */
/* ══════════════════════════════════════════════════════════════════════════════ */

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0);    }
}

/* Fade-in del contenido principal al cargar la página */
[data-testid="stMain"] {
    animation: fadeUp 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* Métricas con stagger al aparecer (solo cuando la sección de resultados se monta) */
[data-testid="stColumn"]:nth-child(1) [data-testid="stMetric"] {
    animation: fadeUp 0.4s 0.05s cubic-bezier(0.16, 1, 0.3, 1) both;
}
[data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"] {
    animation: fadeUp 0.4s 0.12s cubic-bezier(0.16, 1, 0.3, 1) both;
}
[data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"] {
    animation: fadeUp 0.4s 0.19s cubic-bezier(0.16, 1, 0.3, 1) both;
}


/* ══════════════════════════════════════════════════════════════════════════════ */
/*  DARK MODE                                                                     */
/* ══════════════════════════════════════════════════════════════════════════════ */

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


/* ══════════════════════════════════════════════════════════════════════════════ */
/*  HOME CARDS — selección de módulo de cálculo                                  */
/* ══════════════════════════════════════════════════════════════════════════════ */

.calc-card {
    background: #ffffff;
    border: 1.5px solid #e5e7eb;
    border-radius: 14px;
    padding: 1.75rem 1.5rem 1.25rem;
    text-align: center;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
    margin-bottom: 0.75rem;
}
.calc-card:hover {
    border-color: #16a34a;
    box-shadow: 0 6px 20px rgba(22, 163, 74, 0.1);
}
.calc-card-icon {
    font-size: 2.25rem;
    margin-bottom: 0.875rem;
    display: block;
}
.calc-card-title {
    font-size: 1rem;
    font-weight: 700;
    color: #111827;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;
    font-family: 'Outfit', sans-serif;
}
.calc-card-desc {
    font-size: 0.8rem;
    color: #6b7280;
    line-height: 1.6;
    font-family: 'Outfit', sans-serif;
}
.calc-card-badge {
    display: inline-block;
    font-size: 0.62rem;
    font-weight: 600;
    color: #9ca3af;
    background: #f3f4f6;
    border-radius: 999px;
    padding: 0.2rem 0.7rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-top: 0.75rem;
}


/* ══════════════════════════════════════════════════════════════════════════════ */
/*  RESPONSIVE — login split-screen adaptable a todos los dispositivos           */
/* ══════════════════════════════════════════════════════════════════════════════ */

/* ── Tablet (768–1023 px) — split-screen pero compacto ──────────────────────── */
@media (max-width: 1023px) {
    .login-brand-name {
        font-size: 4rem !important;
    }
    .login-bg-panel {
        padding: 0 2.5rem !important;
    }
}

/* ── Mobile (< 768 px) — layout apilado vertical ────────────────────────────── */
@media (max-width: 767px) {
    /* Sin gradiente partido — fondo blanco limpio */
    body:has(.login-bg-panel) {
        background: #f9fafb !important;
    }

    /* Panel de marca: de posición fixed lateral → banner superior en flujo normal */
    .login-bg-panel {
        position: relative !important;
        top: unset !important;
        left: unset !important;
        width: 100% !important;
        height: auto !important;
        background: #14532d !important;
        padding: 2rem 1.5rem 1.75rem !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        pointer-events: auto !important;
        z-index: auto !important;
    }

    /* Mobile: solo eyebrow + nombre — ocultar descripción y tag */
    .login-brand-desc,
    .login-brand-tag {
        display: none !important;
    }
    .login-brand-eyebrow {
        margin-bottom: 0.75rem !important;
    }
    .login-brand-name {
        font-size: 3.25rem !important;
        margin-bottom: 0 !important;
    }

    /* Espaciador antes del form: reducir de 22vh a 1.5rem */
    .login-spacer {
        height: 1.5rem !important;
    }

    /* Columna izquierda vacía (placeholder del panel fixed) → colapsar */
    body:has(.login-bg-panel) [data-testid="stColumn"]:first-child {
        display: none !important;
        flex: 0 0 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
    }

    /* Columna del formulario → ancho completo con respiración lateral */
    body:has(.login-bg-panel) [data-testid="stColumn"]:last-child {
        min-width: 100% !important;
        max-width: 100% !important;
        flex: 1 1 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Sin padding cero en el contenedor principal — dejar que el panel fluya */
    body:has(.login-bg-panel) [data-testid="stMainBlockContainer"] {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
}

/* ── Responsive general (app) — métricas en mobile ──────────────────────────── */
@media (max-width: 600px) {
    /* Las 3 métricas de totales pueden ser un poco más compactas */
    [data-testid="stMetric"] {
        padding: 0.75rem 0.875rem !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
    }
}
</style>
"""


def aplicar_estilos() -> None:
    """Inyecta el CSS de Rake. Llamar al inicio de cada página."""
    st.markdown(_CSS, unsafe_allow_html=True)
