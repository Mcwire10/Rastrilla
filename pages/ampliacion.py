"""
ampliacion.py — Ampliación de Ejecución
Múltiples períodos · Mora desde el 1° del mes siguiente · Tasa pasiva BCRA.
"""
from datetime import date

import pandas as pd
import streamlit as st

from auth import list_abogados, log_calculo, importar_puentes_anio
from bcra import cargar_indice, descargar_indice, fecha_ultimo_dato
from calculos import calcular_intereses, primer_dia_mes_siguiente
from exportar import exportar_excel, exportar_pdf
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

    _usuario_sidebar = st.session_state.get("usuario", {})
    if _usuario_sidebar.get("rol") == "admin":
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
st.title("📎 Ampliación de Ejecución")
st.caption("Tasa pasiva BCRA · Mora desde el 1° del mes siguiente al período")
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

# ── 3. Planilla de liquidación ────────────────────────────────────────────────
st.subheader("3. Planilla de liquidación")

# Session state
if "amp_filas" not in st.session_state:
    st.session_state.amp_filas = pd.DataFrame(columns=["periodo", "capital", "fecha_desde"])
if "amp_resultado" not in st.session_state:
    st.session_state.amp_resultado = None
if "amp_fecha_pago" not in st.session_state:
    st.session_state.amp_fecha_pago = date.today()

col_up, col_auto = st.columns([3, 1])

with col_up:
    archivo = st.file_uploader(
        "Importar planilla (PDF BlueCorp · DOCX Jauregui · Excel · CSV)",
        type=["pdf", "docx", "xlsx", "xls", "csv"],
    )
    if archivo:
        try:
            df_imp, formato = parsear_archivo(archivo, archivo.name)
            # Si el archivo trae fecha_pago, la usamos como valor por defecto
            if "fecha_pago" in df_imp.columns and df_imp["fecha_pago"].notna().any():
                fp = df_imp["fecha_pago"].dropna().iloc[0]
                st.session_state.amp_fecha_pago = fp.date() if isinstance(fp, pd.Timestamp) else fp
            st.session_state.amp_filas = df_imp[["periodo", "capital", "fecha_desde"]].copy()
            st.session_state.amp_resultado = None
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
        df = st.session_state.amp_filas.copy()
        for i, row in df.iterrows():
            if pd.notna(row.get("periodo")) and str(row["periodo"]).count("/") == 1:
                try:
                    df.at[i, "fecha_desde"] = primer_dia_mes_siguiente(str(row["periodo"]))
                except Exception:
                    pass
        st.session_state.amp_filas = df
        st.rerun()

# Tabla editable para revisión y corrección manual
st.caption("Revisá y corregí los períodos antes de calcular")
df_editor = st.data_editor(
    st.session_state.amp_filas,
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
    key="amp_editor_filas",
)
st.session_state.amp_filas = df_editor

# Fecha de pago — se ingresa manualmente después de revisar la planilla
st.session_state.amp_fecha_pago = st.date_input(
    "Fecha efectiva de pago (se aplica a toda la liquidación)",
    value=st.session_state.amp_fecha_pago,
    format="DD/MM/YYYY",
)

st.divider()

# ── Calcular ──────────────────────────────────────────────────────────────────
if st.button("▶ Calcular intereses", type="primary", use_container_width=True):
    errores = []
    if indice is None:
        errores.append("El índice BCRA no está disponible. Actualizalo desde el sidebar.")
    df_calc = st.session_state.amp_filas.dropna(subset=["periodo", "capital", "fecha_desde"]).copy()
    if df_calc.empty:
        errores.append("No hay períodos cargados. Importá una planilla o ingresá filas manualmente.")
    if not st.session_state.amp_fecha_pago:
        errores.append("Ingresá la fecha efectiva de pago.")

    if errores:
        for e in errores:
            st.error(e)
    else:
        try:
            df_calc["fecha_pago"] = pd.Timestamp(st.session_state.amp_fecha_pago)
            with st.spinner("Calculando..."):
                resultado = calcular_intereses(df_calc.reset_index(drop=True), indice)
            st.session_state.amp_resultado = resultado

            # Log en DB
            df_ok_log = resultado[resultado["error"].isna()]
            if not df_ok_log.empty:
                log_calculo(
                    tipo="ampliacion",
                    letrado_id=abogado["id"],
                    expediente=exp.get("Expediente", ""),
                    caratula=exp.get("Carátula", exp.get("Caratula", "")),
                    capital_total=float(df_ok_log["capital"].sum()),
                    interes_total=float(df_ok_log["interes"].sum()),
                    total=float(df_ok_log["total"].sum()),
                )
        except Exception as e:
            st.error(f"Error en el cálculo: {e}")

# ── Resultados ────────────────────────────────────────────────────────────────
if st.session_state.get("amp_resultado") is not None:
    res = st.session_state.amp_resultado
    df_ok = res[res["error"].isna()].copy()
    errores_filas = res[res["error"].notna()]

    if not errores_filas.empty:
        st.warning(f"{len(errores_filas)} período(s) con error:")
        for _, r in errores_filas.iterrows():
            st.write(f"  • {r['periodo']}: {r['error']}")

    if not df_ok.empty:
        st.subheader("4. Resultado")

        def fmt_ar(n: float) -> str:
            return f"$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        display = pd.DataFrame({
            "Período":      df_ok["periodo"],
            "Int. desde":   df_ok["fecha_desde"].dt.strftime("%d/%m/%Y"),
            "Capital ($)":  df_ok["capital"].apply(fmt_ar),
            "Índ. inicial": df_ok["indice_inicial"].map("{:,.4f}".format),
            "Índ. final":   df_ok["indice_final"].map("{:,.4f}".format),
            "Coeficiente":  df_ok["coeficiente"].map("{:.6f}".format),
            "Interés ($)":  df_ok["interes"].apply(fmt_ar),
            "Total ($)":    df_ok["total"].apply(fmt_ar),
        })
        st.dataframe(display, use_container_width=True, hide_index=True)

        t_cap = df_ok["capital"].sum()
        t_int = df_ok["interes"].sum()
        t_tot = df_ok["total"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Capital total", fmt_ar(t_cap))
        c2.metric("Intereses moratorios", fmt_ar(t_int))
        c3.metric("Total general", fmt_ar(t_tot))

        # ── Exportar ──────────────────────────────────────────────────────────
        st.subheader("5. Exportar")

        expediente_num = exp.get("Expediente", "")
        nombre_base = expediente_num.replace("/", "-") or "liquidacion"

        col_xl, col_pdf = st.columns(2)
        with col_xl:
            xlsx_bytes = exportar_excel(df_ok)
            st.download_button(
                "⬇ Descargar Excel",
                data=xlsx_bytes,
                file_name=f"ampliacion_{nombre_base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col_pdf:
            pdf_bytes = exportar_pdf(df_ok)
            st.download_button(
                "⬇ Descargar PDF",
                data=pdf_bytes,
                file_name=f"ampliacion_{nombre_base}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
