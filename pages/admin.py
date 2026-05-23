"""
admin.py — Panel de administración
El router (app.py) ya hizo auth guard; aquí solo comprobamos rol admin.
"""
import streamlit as st

from auth import (
    list_abogados, create_abogado, set_abogado_activo,
    list_errores, clear_errores,
)

usuario = st.session_state.get("usuario")

if usuario is None or usuario["rol"] != "admin":
    st.error("⛔ Acceso denegado. Esta sección es solo para administradores.")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔧 Panel de Administración")
st.caption(f"Sesión: **{usuario['nombre']}** ({usuario['username']})")
st.divider()

# ── Letrados / Abogados ───────────────────────────────────────────────────────
st.subheader("Letrados")

def _list_abogados_all() -> list[dict]:
    """Lista todos los abogados (activos e inactivos) para el panel admin."""
    from auth import _conn
    with _conn() as c:
        rows = c.execute("SELECT * FROM abogados ORDER BY nombre_completo").fetchall()
        return [dict(r) for r in rows]

todos_abogados = _list_abogados_all()

if not todos_abogados:
    st.info("No hay letrados registrados aún.")
else:
    for ab in todos_abogados:
        with st.container(border=True):
            col_ab_info, col_ab_toggle = st.columns([5, 2])
            with col_ab_info:
                estado_ab = "✅ Activo" if ab["activo"] else "🔴 Inactivo"
                st.markdown(f"**{ab['nombre_completo']}** &nbsp; {estado_ab}")
                st.caption(f"CUIL: {ab['cuil']}")
            with col_ab_toggle:
                if ab["activo"]:
                    if st.button("🔴 Desactivar", key=f"ab_des_{ab['id']}", use_container_width=True):
                        set_abogado_activo(ab["id"], False)
                        st.rerun()
                else:
                    if st.button("✅ Activar", key=f"ab_act_{ab['id']}", use_container_width=True):
                        set_abogado_activo(ab["id"], True)
                        st.rerun()

st.markdown("**Agregar letrado**")
with st.form("nuevo_abogado"):
    col_ab1, col_ab2 = st.columns(2)
    with col_ab1:
        nuevo_nombre = st.text_input("Nombre completo (en mayúsculas)", placeholder="APELLIDO NOMBRE")
    with col_ab2:
        nuevo_cuil = st.text_input("CUIL", placeholder="20/12345678/9")
    if st.form_submit_button("Agregar letrado", use_container_width=True):
        if not nuevo_nombre.strip() or not nuevo_cuil.strip():
            st.error("Completá nombre y CUIL.")
        else:
            try:
                create_abogado(nuevo_nombre.strip().upper(), nuevo_cuil.strip())
                st.success(f"Letrado **{nuevo_nombre.upper()}** agregado.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

st.divider()

# ── Log de errores del sistema ────────────────────────────────────────────────
st.subheader("Log de errores")
st.caption("Errores capturados automáticamente por la aplicación. Se envía mail de alerta a leandro.moyano7@gmail.com si el servidor SMTP está configurado.")

errores = list_errores()

if not errores:
    st.success("✅ Sin errores registrados.")
else:
    col_err_hdr, col_err_clear = st.columns([5, 1])
    with col_err_hdr:
        st.markdown(f"**{len(errores)} error(es) registrado(s)**")
    with col_err_clear:
        if st.button("🗑️ Limpiar", use_container_width=True, help="Eliminar todos los registros"):
            clear_errores()
            st.success("Log limpiado.")
            st.rerun()

    for err in errores:
        mail_tag = "✉️ mail enviado" if err["mail_ok"] else "⚠️ mail no enviado"
        with st.expander(
            f"**{err['timestamp']}** — `{err['tipo']}` — {mail_tag}",
            expanded=False,
        ):
            st.markdown(f"**Mensaje:** {err['mensaje']}")
            if err["traceback"]:
                st.code(err["traceback"], language="python")
