"""
admin.py — Panel de administración
El router (app.py) ya hizo auth guard; aquí solo comprobamos rol admin.
"""
from datetime import date

import streamlit as st

from auth import (
    create_user, list_users, registrar_pago, set_bloqueado,
    list_abogados, create_abogado, set_abogado_activo,
    list_feriados_extra, add_feriado_extra, delete_feriado_extra,
)

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

# ── Feriados judiciales extra ─────────────────────────────────────────────────
st.subheader("Feriados judiciales extra")
st.caption(
    "Días inhábiles adicionales que no son feriados nacionales ni feria judicial oficial. "
    "Se aplican al cálculo de los 120 días hábiles de Ejecución de Sentencia."
)

feriados_extra = list_feriados_extra()

if not feriados_extra:
    st.info("No hay feriados extra cargados.")
else:
    for fe in feriados_extra:
        with st.container(border=True):
            col_fe_info, col_fe_del = st.columns([5, 1])
            with col_fe_info:
                fecha_fe = date.fromisoformat(fe["fecha"])
                st.markdown(
                    f"**{fecha_fe.strftime('%d/%m/%Y')}** — {fe['descripcion'] or '(sin descripción)'}"
                )
            with col_fe_del:
                if st.button("🗑️ Eliminar", key=f"del_fe_{fe['id']}", use_container_width=True):
                    delete_feriado_extra(fe["id"])
                    st.success("Feriado eliminado.")
                    st.rerun()

st.markdown("**Agregar feriado extra**")
with st.form("nuevo_feriado_extra"):
    col_fe1, col_fe2 = st.columns(2)
    with col_fe1:
        nueva_fecha_fe = st.date_input(
            "Fecha del día inhábil", value=None, format="DD/MM/YYYY"
        )
    with col_fe2:
        nueva_desc_fe = st.text_input(
            "Descripción", placeholder="Ej: Asueto decretado por resolución X"
        )
    if st.form_submit_button("Agregar feriado", use_container_width=True):
        if not nueva_fecha_fe:
            st.error("Seleccioná una fecha.")
        else:
            try:
                add_feriado_extra(nueva_fecha_fe, nueva_desc_fe.strip())
                st.success(f"Feriado **{nueva_fecha_fe.strftime('%d/%m/%Y')}** agregado.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

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
