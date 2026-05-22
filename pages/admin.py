"""
admin.py — Panel de administración
El router (app.py) ya hizo auth guard; aquí solo comprobamos rol admin.
"""
from datetime import date

import streamlit as st

from auth import create_user, list_users, registrar_pago, set_bloqueado

usuario = st.session_state.get("usuario")

if usuario is None or usuario["rol"] != "admin":
    st.error("⛔ Acceso denegado. Esta sección es solo para administradores.")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔧 Panel de Administración")
st.caption(f"Sesión: **{usuario['nombre']}** ({usuario['username']})")
st.divider()

# ── Tabla de usuarios ─────────────────────────────────────────────────────────
st.subheader("Usuarios y suscripciones")

usuarios = list_users()
hoy = date.today()


def _estado(u: dict) -> str:
    if u["bloqueado"]:
        return "🔴 Bloqueado"
    if not u["fecha_ultimo_pago"]:
        return "⚠️ Sin pago registrado"
    last = date.fromisoformat(u["fecha_ultimo_pago"])
    if last >= date(hoy.year, hoy.month, 1):
        return "✅ Al día"
    if hoy.day > 10:
        return "🟠 Vencido"
    return "⏳ Pendiente"


for u in usuarios:
    with st.container(border=True):
        col_info, col_pago, col_bloqueo = st.columns([4, 2, 2])

        with col_info:
            estado = _estado(u)
            st.markdown(f"**{u['nombre']}** — `{u['username']}` &nbsp; {estado}")
            st.caption(
                f"Rol: {u['rol']} · "
                f"Contrato: {u['fecha_contrato']} · "
                f"Día de pago: {u['dia_pago']} · "
                f"Último pago: {u['fecha_ultimo_pago'] or '—'}"
            )

        with col_pago:
            if u["rol"] != "admin":
                if st.button(
                    "💰 Marcar pagado",
                    key=f"pago_{u['username']}",
                    use_container_width=True,
                ):
                    registrar_pago(u["username"])
                    st.success("Pago registrado.")
                    st.rerun()

        with col_bloqueo:
            if u["rol"] != "admin":
                if u["bloqueado"]:
                    if st.button(
                        "🔓 Desbloquear",
                        key=f"blq_{u['username']}",
                        use_container_width=True,
                    ):
                        set_bloqueado(u["username"], False)
                        st.success("Cuenta desbloqueada.")
                        st.rerun()
                else:
                    if st.button(
                        "🔒 Bloquear",
                        key=f"blq_{u['username']}",
                        use_container_width=True,
                    ):
                        set_bloqueado(u["username"], True)
                        st.warning("Cuenta bloqueada.")
                        st.rerun()

st.divider()

# ── Resumen ───────────────────────────────────────────────────────────────────
clientes = [u for u in usuarios if u["rol"] == "cliente"]
al_dia   = sum(1 for u in clientes if _estado(u) == "✅ Al día")
vencidos = sum(1 for u in clientes if "Vencido" in _estado(u))
bloq     = sum(1 for u in clientes if u["bloqueado"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total clientes", len(clientes))
c2.metric("Al día ✅", al_dia)
c3.metric("Vencidos 🟠", vencidos)
c4.metric("Bloqueados 🔴", bloq)

st.divider()

# ── Agregar usuario ───────────────────────────────────────────────────────────
st.subheader("Agregar usuario")

with st.form("nuevo_usuario"):
    col1, col2 = st.columns(2)
    with col1:
        nombre   = st.text_input("Nombre completo")
        username = st.text_input("Usuario (login)")
        password = st.text_input("Contraseña", type="password")
    with col2:
        rol      = st.selectbox("Rol", ["cliente", "admin"])
        dia_pago = st.number_input("Día de pago (1–10)", min_value=1, max_value=10, value=1)

    if st.form_submit_button("Crear usuario", use_container_width=True):
        if not username or not password or not nombre:
            st.error("Completá todos los campos.")
        else:
            try:
                create_user(username.strip(), password, nombre.strip(), rol, int(dia_pago))
                st.success(f"Usuario **{username}** creado correctamente.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
