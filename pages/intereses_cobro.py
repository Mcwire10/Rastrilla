"""
intereses_cobro.py — Intereses Aprobados hasta Cobro
Capital único · Desde el día siguiente a la aprobación hasta el efectivo cobro.
"""
from datetime import date

import streamlit as st

from auth import list_abogados, importar_puentes_anio, log_uso, get_session_user
from bcra import cargar_indice, descargar_indice, fecha_ultimo_dato
from calculos import calcular_interes_simple
from exportar import generar_pdf_cobro, generar_docx_cobro, limpiar_expediente

# ── Sidebar: índice BCRA ────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    st.markdown("**Índice BCRA**")
    st.caption("Com. 14290 · Uso de la Justicia")

    @st.cache_resource(show_spinner="Cargando índice BCRA...")
    def get_indice():
        return cargar_indice()

    try:
        indice = get_indice()
        st.success(f"Datos hasta: **{fecha_ultimo_dato(indice)}**")
    except Exception as e:
        st.error(f"No se pudo cargar: {e}")
        indice = None

    if st.button("Actualizar índice BCRA", use_container_width=True):
        with st.spinner("Descargando desde BCRA..."):
            try:
                descargar_indice()
                st.cache_resource.clear()
                st.success("Índice actualizado.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    if st.button("Actualizar feriados", use_container_width=True):
        with st.spinner("Importando puentes..."):
            try:
                _anio = date.today().year
                _res  = importar_puentes_anio(_anio)
                _new  = sum(1 for r in _res if r["nuevo"])
                if _new:
                    st.success(f"{_new} feriado(s) importado(s) para {_anio}.")
                elif _res:
                    st.info(f"Ya estaban cargados ({len(_res)}).")
                else:
                    st.info(f"Sin puentes para {_anio}.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")


# ── Título ──────────────────────────────────────────────────────────────────
st.title("💰 Intereses Aprobados hasta Cobro")
st.caption("Tasa pasiva BCRA · Intereses desde el día siguiente a la aprobación hasta el efectivo cobro")
st.divider()

# ── 1. Letrado presentante ────────────────────────────────────────────────────
st.subheader("1. Letrado presentante")

abogados = list_abogados()
if not abogados:
    st.error("No hay abogados configurados. Contactá al administrador.")
    st.stop()

opciones_ab = {f"{a['nombre_completo']}  —  CUIL {a['cuil']}": a for a in abogados}
seleccion_ab = st.selectbox("Seleccioná el letrado", list(opciones_ab.keys()), label_visibility="collapsed")
abogado = opciones_ab[seleccion_ab]

st.divider()

# ── 2. Datos del expediente ───────────────────────────────────────────────────
st.subheader("2. Datos del expediente")
st.caption("Pegá el texto copiado del sistema de consulta judicial — los campos se detectan automáticamente")

texto_exp = st.text_area(
    "Datos del expediente",
    height=155,
    label_visibility="collapsed",
    placeholder=(
        "Expediente:FMZ 041824/2019\n"
        "Jurisdicción:Justicia Federal de Mendoza\n"
        "Dependencia:JUZGADO FEDERAL DE VILLA MERCEDES - SECRETARIA CIVIL\n"
        "Sit. Actual:EN DESPACHO\n"
        "Carátula:FLORES, ROSA MERCEDES c/ ANSES s/REAJUSTES VARIOS"
    ),
)

# Parser: cada línea → clave:valor (partition en primer ":")
exp = {}
if texto_exp.strip():
    for linea in texto_exp.strip().splitlines():
        if ":" in linea:
            clave, _, valor = linea.partition(":")
            exp[clave.strip()] = valor.strip()

if exp:
    c_e1, c_e2 = st.columns(2)
    with c_e1:
        st.markdown(f"**Expediente:** {limpiar_expediente(exp.get('Expediente', '')) or '—'}")
        st.markdown(f"**Carátula:** {exp.get('Carátula', exp.get('Caratula', '—'))}")
    with c_e2:
        st.markdown(f"**Jurisdicción:** {exp.get('Jurisdicción', exp.get('Jurisdiccion', '—'))}")
        st.markdown(f"**Situación:** {exp.get('Sit. Actual', '—')}")

st.divider()

# ── 3. Datos del cálculo ──────────────────────────────────────────────────────
st.subheader("3. Datos del cálculo")

col1, col2, col3 = st.columns(3)
with col1:
    capital = st.number_input(
        "Capital aprobado ($)",
        min_value=0.01,
        value=None,
        format="%.2f",
        placeholder="0,00",
    )
with col2:
    fecha_aprobacion = st.date_input(
        "Fecha de aprobación judicial",
        value=None,
        format="DD/MM/YYYY",
    )
with col3:
    fecha_cobro = st.date_input(
        "Fecha de efectivo cobro",
        value=None,
        format="DD/MM/YYYY",
    )

st.divider()

# ── Calcular ──────────────────────────────────────────────────────────────────
if st.button("▶ Calcular intereses", type="primary", use_container_width=True):
    errores = []
    if not capital:
        errores.append("Ingresá el capital aprobado.")
    if not fecha_aprobacion:
        errores.append("Ingresá la fecha de aprobación.")
    if not fecha_cobro:
        errores.append("Ingresá la fecha de efectivo cobro.")
    elif fecha_aprobacion and fecha_cobro <= fecha_aprobacion:
        errores.append("La fecha de cobro debe ser posterior a la fecha de aprobación.")
    if indice is None:
        errores.append("El índice BCRA no está disponible. Actualizalo desde el sidebar.")

    if errores:
        for e in errores:
            st.error(e)
    else:
        try:
            res = calcular_interes_simple(capital, fecha_aprobacion, fecha_cobro, indice)
            st.session_state["resultado_cobro"] = res
        except Exception as e:
            st.error(f"Error en el cálculo: {e}")

# ── Resultados ────────────────────────────────────────────────────────────────
if st.session_state.get("resultado_cobro"):
    res = st.session_state["resultado_cobro"]

    st.subheader("4. Resultado")

    def fmt_ar(n: float) -> str:
        return f"$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    c1, c2, c3 = st.columns(3)
    c1.metric("Capital aprobado", fmt_ar(res["capital"]))
    c2.metric("Intereses moratorios", fmt_ar(res["interes"]))
    c3.metric("Total", fmt_ar(res["total"]))

    with st.expander("Detalle del cálculo"):
        cd1, cd2 = st.columns(2)
        with cd1:
            st.markdown(f"**Intereses desde:** {res['fecha_desde'].strftime('%d/%m/%Y')}")
            st.markdown(f"**Hasta:** {res['fecha_hasta'].strftime('%d/%m/%Y')}")
            st.caption(f"T₀ = día anterior: {res['fecha_t0'].strftime('%d/%m/%Y')}")
        with cd2:
            st.markdown(f"**Índice T₀ ({res['fecha_t0'].strftime('%d/%m/%Y')}):** {res['indice_inicial']:,.4f}")
            st.markdown(f"**Índice Tₘ ({res['fecha_hasta'].strftime('%d/%m/%Y')}):** {res['indice_final']:,.4f}")
            st.markdown(f"**Coeficiente:** {res['coeficiente']:.6f}  ({res['coeficiente']*100:.4f}%)")

    # ── Exportar ──────────────────────────────────────────────────────────────
    st.subheader("5. Exportar")

    caratula = exp.get("Carátula", exp.get("Caratula", ""))
    expediente_num = limpiar_expediente(exp.get("Expediente", ""))

    _uname_cob  = (get_session_user() or {}).get("username", "desconocido")
    _caratula_c = exp.get("Carátula", exp.get("Caratula", ""))
    _apellido   = _caratula_c.split(",")[0].strip() if _caratula_c else "liquidacion"

    pdf_bytes  = generar_pdf_cobro(res, abogado, _caratula_c, expediente_num)
    _nombre_doc = f"INT M - {_apellido}"

    col_pdf, col_docx = st.columns(2)
    with col_pdf:
        if st.download_button(
            "⬇ Descargar PDF",
            data=pdf_bytes,
            file_name=f"{_nombre_doc}.pdf",
            mime="application/pdf",
            use_container_width=True,
        ):
            log_uso(_uname_cob, "cobro", "pdf")
    with col_docx:
        docx_bytes = generar_docx_cobro(res, abogado, _caratula_c, expediente_num)
        if st.download_button(
            "⬇ Descargar Word",
            data=docx_bytes,
            file_name=f"{_nombre_doc}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        ):
            log_uso(_uname_cob, "cobro", "docx")
