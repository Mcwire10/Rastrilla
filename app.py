"""
app.py — Router principal de Rake
Gestiona auth, estilos, navegación por rol y sidebar footer.
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

# ── Sidebar footer — usuario + engranaje + cerrar sesión ─────────────────────
# Se añade DESPUÉS de pg.run() para que aparezca al final del sidebar,
# debajo del contenido que cada página agrega (ej: índice BCRA en calculadora).

pg.run()

with st.sidebar:
    st.divider()

    nombre_corto = usuario["nombre"].split()[0]
    col_nombre, col_gear, col_out = st.columns([5, 1, 1])

    with col_nombre:
        st.markdown(
            f"<p style='color:#dcfce7;font-weight:600;font-size:0.875rem;"
            f"margin:0;line-height:1.3'>{nombre_corto}</p>"
            f"<p style='color:rgba(187,247,208,0.55);font-size:0.7rem;"
            f"margin:0'>{usuario['rol']}</p>",
            unsafe_allow_html=True,
        )

    with col_gear:
        if usuario["rol"] == "admin":
            if st.button("⚙️", key="btn_admin", help="Panel de administración"):
                st.switch_page("pages/admin.py")

    with col_out:
        if st.button("↩", key="btn_logout", help="Cerrar sesión"):
            logout()
