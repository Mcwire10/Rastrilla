"""
app.py — Router principal de Rake
Gestiona auth, estilos, navegación por rol y sidebar.
"""
import streamlit as st

from auth import get_session_user, init_db, logout, render_login
from estilo import aplicar_estilos

st.set_page_config(
    page_title="Intereses Moratorios · Rake",
    page_icon="⚖️",
    layout="wide",
)

init_db()
aplicar_estilos()

# ── Auth guard ────────────────────────────────────────────────────────────────
usuario = get_session_user()
if usuario is None:
    render_login()
    st.stop()

# ── Navegación por rol ────────────────────────────────────────────────────────
home            = st.Page("pages/home.py",             title="Inicio",                  default=True)
ejecucion       = st.Page("pages/ejecucion.py",        title="Ejecución de Sentencia")
ampliacion      = st.Page("pages/ampliacion.py",       title="Ampliación de Ejecución")
intereses_cobro = st.Page("pages/intereses_cobro.py",  title="Intereses hasta Cobro")
pages = [home, ejecucion, ampliacion, intereses_cobro]

if usuario["rol"] == "admin":
    pages.append(st.Page("pages/admin.py", title="Admin"))

pg = st.navigation(pages, position="hidden")

# ── Logo — tope del sidebar, click = volver al home ──────────────────────────
with st.sidebar:
    st.page_link("pages/home.py", label="Rake", icon="⚖️")

# ── Contenido de la página activa ─────────────────────────────────────────────
pg.run()

# ── Sidebar: navegación + footer ──────────────────────────────────────────────
with st.sidebar:
    st.divider()

    if usuario["rol"] == "admin":
        if st.button("🔧 Administración", key="btn_admin", use_container_width=True):
            st.switch_page("pages/admin.py")

    if st.button("🏠 Inicio", key="btn_home", use_container_width=True):
        st.switch_page("pages/home.py")

    st.divider()

    nombre_corto = usuario["nombre"].split()[0]
    st.caption(f"👤 {nombre_corto} · {usuario['rol']}")

    if st.button("Cerrar sesión", key="btn_logout", use_container_width=True):
        logout()
