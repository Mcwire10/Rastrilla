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
calculadora = st.Page("pages/calculadora.py", title="Calculadora", default=True)
pages = [calculadora]

if usuario["rol"] == "admin":
    pages.append(st.Page("pages/admin.py", title="Admin"))

pg = st.navigation(pages, position="hidden")

# ── Logo — tope del sidebar, siempre visible, click = volver a home ───────────
with st.sidebar:
    st.page_link("pages/calculadora.py", label="Rake", icon="⚖️")

# ── Contenido de la página activa (calculadora agrega sección BCRA al sidebar) ─
pg.run()

# ── Sidebar: navegación + footer ──────────────────────────────────────────────
with st.sidebar:
    st.divider()

    # Botón de admin solo para el rol admin
    if usuario["rol"] == "admin":
        if st.button("🔧 Administración", key="btn_admin", use_container_width=True):
            st.switch_page("pages/admin.py")

    # Botón siempre visible para volver a la calculadora (útil desde admin)
    if st.button("📊 Calculadora", key="btn_calc", use_container_width=True):
        st.switch_page("pages/calculadora.py")

    st.divider()

    nombre_corto = usuario["nombre"].split()[0]
    st.caption(f"👤 {nombre_corto} · {usuario['rol']}")

    if st.button("Cerrar sesión", key="btn_logout", use_container_width=True):
        logout()
