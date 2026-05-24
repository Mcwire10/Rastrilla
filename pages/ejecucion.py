"""
ejecucion.py — Ejecución de Sentencia
120 días hábiles judiciales · Tramo A (sum capital → interés único) · Tramo B (por período).
Tasa pasiva BCRA Com. 14290.
"""
from datetime import date

import pandas as pd
import streamlit as st

from auth import list_abogados, list_feriados_extra, log_calculo, importar_puentes_anio, log_uso, get_session_user
from bcra import cargar_indice, descargar_indice, fecha_ultimo_dato
from calculos import calcular_ejecucion, primer_dia_mes_siguiente
from calendario import dia_habil_n
from exportar import exportar_excel_ejecucion, exportar_pdf_ejecucion, generar_docx_ejecucion
from parsear_pdf import parsear_archivo

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


# ── Feriados extra (inhábiles judiciales adicionales) ───────────────────────
_feriados_raw  = list_feriados_extra()
_extras_tuple  = tuple(date.fromisoformat(f["fecha"]) for f in _feriados_raw)


# ── Título ──────────────────────────────────────────────────────────────────
st.title("📋 Ejecución de Sentencia")
st.caption("Tasa pasiva BCRA · 120 días hábiles judiciales · División automática Tramo A / Tramo B")
st.divider()

# ── 1. Letrado presentante ────────────────────────────────────────────────────
st.subheader("1. Letrado presentante")

abogados = list_abogados()
if not abogados:
    st.error("No hay abogados configurados. Contactá al administrador.")
    st.stop()

opciones_ab = {f"{a['nombre_completo']}  —  CUIL {a['cuil']}": a for a in abogados}
seleccion_ab = st.selectbox(
    "Seleccioná el letrado", list(opciones_ab.keys()), label_visibility="collapsed"
)
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

exp = {}
if texto_exp.strip():
    for linea in texto_exp.strip().splitlines():
        if ":" in linea:
            clave, _, valor = linea.partition(":")
            exp[clave.strip()] = valor.strip()

if exp:
    c_e1, c_e2 = st.columns(2)
    with c_e1:
        st.markdown(f"**Expediente:** {exp.get('Expediente', '—')}")
        st.markdown(f"**Carátula:** {exp.get('Carátula', exp.get('Caratula', '—'))}")
    with c_e2:
        st.markdown(f"**Jurisdicción:** {exp.get('Jurisdicción', exp.get('Jurisdiccion', '—'))}")
        st.markdown(f"**Situación:** {exp.get('Sit. Actual', '—')}")

st.divider()

# ── 3. Fechas clave ────────────────────────────────────────────────────────────
st.subheader("3. Fecha de devolución")

# Session state
if "eje_fecha_devolucion" not in st.session_state:
    st.session_state.eje_fecha_devolucion = None
if "eje_fecha_hasta" not in st.session_state:
    st.session_state.eje_fecha_hasta = date.today()

st.session_state.eje_fecha_devolucion = st.date_input(
    "Fecha de devolución del expediente",
    value=st.session_state.eje_fecha_devolucion,
    format="DD/MM/YYYY",
    help="Desde esta fecha se cuentan los 120 días hábiles judiciales.",
)

# Preview: muestra Día 120 / Día 121 en tiempo real
if st.session_state.eje_fecha_devolucion:
    try:
        dia_120_prev = dia_habil_n(st.session_state.eje_fecha_devolucion, 120, _extras_tuple)
        dia_121_prev = dia_habil_n(st.session_state.eje_fecha_devolucion, 121, _extras_tuple)
        st.info(
            f"📅 **Día 120** hábil judicial: **{dia_120_prev.strftime('%d/%m/%Y')}** &nbsp;·&nbsp; "
            f"**Día 121** (inicio intereses Tramo A): **{dia_121_prev.strftime('%d/%m/%Y')}**"
        )
    except Exception:
        pass

st.divider()

# ── 4. Planilla de liquidación ────────────────────────────────────────────────
st.subheader("4. Planilla de liquidación")


if "eje_filas" not in st.session_state:
    st.session_state.eje_filas = pd.DataFrame(columns=["periodo", "capital", "fecha_desde"])
if "eje_resultado" not in st.session_state:
    st.session_state.eje_resultado = None

col_up, col_auto = st.columns([3, 1])

with col_up:
    archivo = st.file_uploader(
        "Importar planilla (PDF BlueCorp · DOCX Jauregui · Excel · CSV)",
        type=["pdf", "docx", "xlsx", "xls", "csv"],
    )
    if archivo:
        try:
            df_imp, formato = parsear_archivo(archivo, archivo.name)
            st.session_state.eje_filas = df_imp[["periodo", "capital", "fecha_desde"]].copy()
            st.session_state.eje_resultado = None
            st.success(f"Importado formato **{formato}**: {len(df_imp)} períodos")
        except Exception as e:
            st.error(f"Error al importar: {e}")

with col_auto:
    st.markdown("&nbsp;", unsafe_allow_html=True)
    if st.button(
        "🔄 Auto-fechas",
        use_container_width=True,
        help="Calcula 'fecha desde' como el 1° del mes siguiente al período",
    ):
        df = st.session_state.eje_filas.copy()
        for i, row in df.iterrows():
            if pd.notna(row.get("periodo")) and str(row["periodo"]).count("/") == 1:
                try:
                    df.at[i, "fecha_desde"] = primer_dia_mes_siguiente(str(row["periodo"]))
                except Exception:
                    pass
        st.session_state.eje_filas = df
        st.rerun()

st.caption("Revisá y corregí los períodos antes de calcular")
df_editor = st.data_editor(
    st.session_state.eje_filas,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "periodo": st.column_config.TextColumn(
            "Período (MM/AAAA)", help="Ej: 04/2021", width="small"
        ),
        "capital": st.column_config.NumberColumn(
            "Capital / Dif. neta ($)", format="%.2f", min_value=0, width="medium"
        ),
        "fecha_desde": st.column_config.DateColumn(
            "Intereses desde", format="DD/MM/YYYY", width="medium"
        ),
    },
    key="eje_editor_filas",
)
st.session_state.eje_filas = df_editor

st.divider()

# ── 5. Fecha efectiva de pago ─────────────────────────────────────────────────
st.subheader("5. Fecha efectiva de pago")
st.session_state.eje_fecha_hasta = st.date_input(
    "Fecha efectiva de pago (se aplica a toda la liquidación)",
    value=st.session_state.eje_fecha_hasta,
    format="DD/MM/YYYY",
    help="Fecha de cobro efectivo. Extremo final del período de intereses.",
)

st.divider()

# ── Calcular ──────────────────────────────────────────────────────────────────
if st.button("▶ Calcular intereses", type="primary", use_container_width=True):
    errores = []
    if indice is None:
        errores.append("El índice BCRA no está disponible. Actualizalo desde el sidebar.")
    if not st.session_state.eje_fecha_devolucion:
        errores.append("Ingresá la fecha de devolución del expediente.")
    if not st.session_state.eje_fecha_hasta:
        errores.append("Ingresá la fecha efectiva de pago.")
    elif st.session_state.eje_fecha_devolucion and st.session_state.eje_fecha_hasta <= st.session_state.eje_fecha_devolucion:
        errores.append("La fecha de pago debe ser posterior a la fecha de devolución.")

    df_calc = st.session_state.eje_filas.dropna(subset=["periodo", "capital", "fecha_desde"]).copy()
    if df_calc.empty:
        errores.append("No hay períodos cargados. Importá una planilla o ingresá filas manualmente.")

    if errores:
        for e in errores:
            st.error(e)
    else:
        try:
            with st.spinner("Calculando días hábiles y coeficientes BCRA..."):
                resultado = calcular_ejecucion(
                    df_calc.reset_index(drop=True),
                    st.session_state.eje_fecha_devolucion,
                    st.session_state.eje_fecha_hasta,
                    indice,
                    _extras_tuple,
                )
            st.session_state.eje_resultado = resultado

            # Log en DB
            res_a = resultado["resultado_a"]
            res_b = resultado["resultado_b"]
            cap_b = float(res_b["capital"].sum()) if not res_b.empty and "capital" in res_b.columns else 0.0
            int_b = float(res_b["interes"].sum()) if not res_b.empty and "interes" in res_b.columns else 0.0
            tot_b = float(res_b["total"].sum())   if not res_b.empty and "total"   in res_b.columns else 0.0
            int_a = float(res_a.get("interes", 0) or 0)
            tot_a = float(res_a.get("total",   0) or 0)
            log_calculo(
                tipo="ejecucion",
                letrado_id=abogado["id"],
                expediente=exp.get("Expediente", ""),
                caratula=exp.get("Carátula", exp.get("Caratula", "")),
                capital_total=float(resultado["capital_a_total"]) + cap_b,
                interes_total=int_a + int_b,
                total=tot_a + tot_b,
            )
        except Exception as e:
            st.error(f"Error en el cálculo: {e}")

# ── Resultados ────────────────────────────────────────────────────────────────
if st.session_state.get("eje_resultado") is not None:
    res = st.session_state.eje_resultado
    res_a = res["resultado_a"]
    res_b = res["resultado_b"]

    def fmt_ar(n: float) -> str:
        return f"$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    st.subheader("6. Resultado")
    st.info(
        f"📅 **Día 120** hábil judicial: **{res['dia_120'].strftime('%d/%m/%Y')}** &nbsp;·&nbsp; "
        f"**Día 121** (inicio intereses Tramo A): **{res['dia_121'].strftime('%d/%m/%Y')}**"
    )

    # ── TRAMO A ────────────────────────────────────────────────────────────────
    st.markdown("#### Tramo A — Capital acumulado · Interés único desde el Día 121")

    if res["filas_a"]:
        display_a = pd.DataFrame({
            "Período":                   [f["periodo"] for f in res["filas_a"]],
            "Capital proporcional ($)":  [fmt_ar(f["capital"]) for f in res["filas_a"]],
        })
        st.dataframe(display_a, use_container_width=True, hide_index=True)

    if not res_a.get("error"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Capital Tramo A", fmt_ar(res["capital_a_total"]))
        c2.metric("Intereses moratorios", fmt_ar(res_a["interes"]))
        c3.metric("Total Tramo A", fmt_ar(res_a["total"]))

        with st.expander("Detalle del cálculo Tramo A"):
            cd1, cd2 = st.columns(2)
            with cd1:
                st.markdown(f"**Intereses desde (Día 121):** {res['dia_121'].strftime('%d/%m/%Y')}")
                st.markdown(f"**Hasta:** {res['fecha_hasta'].strftime('%d/%m/%Y')}")
                st.caption(f"T₀ = Día 120: {res['dia_120'].strftime('%d/%m/%Y')}")
            with cd2:
                st.markdown(f"**Índice T₀:** {res_a['indice_inicial']:,.4f}")
                st.markdown(f"**Índice Tₘ:** {res_a['indice_final']:,.4f}")
                st.markdown(f"**Coeficiente:** {res_a['coeficiente']:.6f}  ({res_a['coeficiente']*100:.4f}%)")
    else:
        st.warning(f"Tramo A: {res_a['error']}")

    st.divider()

    # ── TRAMO B ────────────────────────────────────────────────────────────────
    st.markdown("#### Tramo B — Períodos posteriores al Día 120 · Intereses por período")

    if not res_b.empty:
        df_b_ok = res_b[res_b["error"].isna()].copy()
        errores_b = res_b[res_b["error"].notna()]

        if not errores_b.empty:
            st.warning(f"{len(errores_b)} período(s) de Tramo B con error:")
            for _, r in errores_b.iterrows():
                st.write(f"  • {r['periodo']}: {r['error']}")

        if not df_b_ok.empty:
            display_b = pd.DataFrame({
                "Período":      df_b_ok["periodo"],
                "Int. desde":   df_b_ok["fecha_desde"].dt.strftime("%d/%m/%Y"),
                "Capital ($)":  df_b_ok["capital"].apply(fmt_ar),
                "Índ. T₀":      df_b_ok["indice_inicial"].map("{:,.4f}".format),
                "Índ. Tₘ":      df_b_ok["indice_final"].map("{:,.4f}".format),
                "Coeficiente":  df_b_ok["coeficiente"].map("{:.6f}".format),
                "Interés ($)":  df_b_ok["interes"].apply(fmt_ar),
                "Total ($)":    df_b_ok["total"].apply(fmt_ar),
            })
            st.dataframe(display_b, use_container_width=True, hide_index=True)

            t_cap_b = df_b_ok["capital"].sum()
            t_int_b = df_b_ok["interes"].sum()
            t_tot_b = df_b_ok["total"].sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("Capital Tramo B", fmt_ar(t_cap_b))
            c2.metric("Intereses moratorios", fmt_ar(t_int_b))
            c3.metric("Total Tramo B", fmt_ar(t_tot_b))
    else:
        st.info("No hay períodos en Tramo B para este rango de fechas.")
        t_tot_b = 0.0

    # ── Resultado final ────────────────────────────────────────────────────────
    st.divider()
    _int_a  = float(res_a.get("interes", 0) or 0)
    _tot_a  = float(res_a.get("total",   0) or 0)
    _cap_b  = float(res_b["capital"].sum()) if not res_b.empty and "capital" in res_b.columns else 0.0
    _int_b  = float(res_b["interes"].sum()) if not res_b.empty and "interes" in res_b.columns else 0.0
    _tot_b  = float(res_b["total"].sum())   if not res_b.empty and "total"   in res_b.columns else 0.0
    _cap_total  = float(res["capital_a_total"]) + _cap_b
    _int_total  = _int_a + _int_b
    _gran_total = _tot_a + _tot_b

    # Caja destacada: resultado final + fecha hasta
    st.markdown(f"""
<div style="background:#f0fdf4; border:2px solid #16a34a; border-radius:12px;
            padding:1.5rem 2rem; margin:0.5rem 0 1.5rem 0;">
  <div style="font-size:0.75rem; font-weight:700; color:#16a34a;
              text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.4rem;">
    Resultado final — Suma intereses moratorios Tramo A + Tramo B
  </div>
  <div style="font-size:2.2rem; font-weight:700; color:#052e16; line-height:1.1;">
    {fmt_ar(_int_total)}
  </div>
  <div style="margin-top:1rem; font-size:0.85rem; color:#374151;">
    Calculado hasta: <strong>{res['fecha_hasta'].strftime('%d/%m/%Y')}</strong>
    &nbsp;—&nbsp; efectivo pago conforme recibo que consta en autos
  </div>
</div>
""", unsafe_allow_html=True)

    cg1, cg2, cg3 = st.columns(3)
    cg1.metric("Capital total",        fmt_ar(_cap_total))
    cg2.metric("Intereses Tramo A",    fmt_ar(_int_a))
    cg3.metric("Intereses Tramo B",    fmt_ar(_int_b))

    # ── Exportar ──────────────────────────────────────────────────────────────
    st.subheader("7. Exportar")

    expediente_num = exp.get("Expediente", "")
    nombre_base    = expediente_num.replace("/", "-") or "liquidacion"

    _uname_eje    = (get_session_user() or {}).get("username", "desconocido")
    _caratula_e   = exp.get("Carátula", exp.get("Caratula", ""))
    _expediente_e = exp.get("Expediente", "")
    _apellido_e   = _caratula_e.split(",")[0].strip() if _caratula_e else "liquidacion"
    _nombre_doc_e = f"INT1M - {_apellido_e}"

    col_xl, col_pdf, col_docx = st.columns(3)
    with col_xl:
        xlsx_bytes = exportar_excel_ejecucion(res)
        if st.download_button(
            "⬇ Descargar Excel (2 hojas)",
            data=xlsx_bytes,
            file_name=f"ejecucion_{nombre_base}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        ):
            log_uso(_uname_eje, "ejecucion", "excel")
    with col_pdf:
        pdf_bytes = exportar_pdf_ejecucion(res)
        if st.download_button(
            "⬇ Descargar PDF",
            data=pdf_bytes,
            file_name=f"{_nombre_doc_e}.pdf",
            mime="application/pdf",
            use_container_width=True,
        ):
            log_uso(_uname_eje, "ejecucion", "pdf")
    with col_docx:
        docx_bytes = generar_docx_ejecucion(res, abogado, _caratula_e, _expediente_e)
        if st.download_button(
            "⬇ Descargar Word",
            data=docx_bytes,
            file_name=f"{_nombre_doc_e}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        ):
            log_uso(_uname_eje, "ejecucion", "docx")
