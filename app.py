import io
from datetime import date

import pandas as pd
import streamlit as st

from auth import get_session_user, init_db, logout, render_login
from bcra import cargar_indice, descargar_indice, fecha_ultimo_dato
from calculos import calcular_intereses, primer_dia_mes_siguiente
from exportar import exportar_excel, exportar_pdf
from estilo import aplicar_estilos
from parsear_pdf import parsear_archivo

st.set_page_config(
    page_title="Intereses Moratorios · RASTRILLA",
    page_icon="⚖️",
    layout="wide",
)

init_db()
aplicar_estilos()

usuario = get_session_user()
if usuario is None:
    render_login()
    st.stop()

# ── Sidebar: índice BCRA ────────────────────────────────────────────────────
with st.sidebar:
    st.caption(f"👤 {usuario['nombre']}  `{usuario['rol']}`")
    if st.button("Cerrar sesión", use_container_width=True):
        logout()
    st.divider()
    st.header("Índice BCRA")
    st.caption("Com. 14290 · Uso de la Justicia")

    @st.cache_resource(show_spinner="Cargando índice BCRA...")
    def get_indice():
        return cargar_indice()

    try:
        indice = get_indice()
        st.success(f"Datos hasta: **{fecha_ultimo_dato(indice)}**")
    except Exception as e:
        st.error(f"No se pudo cargar el índice: {e}")
        indice = None

    if st.button("Actualizar índice BCRA", use_container_width=True):
        with st.spinner("Descargando desde BCRA..."):
            try:
                descargar_indice()
                st.cache_resource.clear()
                st.success("Índice actualizado.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al descargar: {e}")

    st.divider()
    st.markdown("""
**Doctrina RASTRILLA**
Cada mensualidad es una obligación independiente.
Intereses desde: 1° del mes siguiente.
Fórmula: `Capital × ((100 + T_m) / (100 + T_0) − 1)`
T_0 = índice del día anterior al inicio · T_m = índice al día de pago
*(BCRA Res. 45/26 · Ley 27.802 art. 55)*
""")

# ── Estado de sesión ────────────────────────────────────────────────────────
if "filas" not in st.session_state:
    st.session_state.filas = pd.DataFrame(columns=["periodo", "capital", "fecha_desde"])

if "resultado" not in st.session_state:
    st.session_state.resultado = None

if "fecha_hasta" not in st.session_state:
    st.session_state.fecha_hasta = date.today()

# ── Título ──────────────────────────────────────────────────────────────────
st.title("⚖️ Intereses Moratorios — Doctrina RASTRILLA")
st.caption("Tasa pasiva BCRA Com. 14290 · Cálculo por coeficiente acumulado")

# ── Importar Excel / CSV ─────────────────────────────────────────────────────
st.subheader("1. Cargar datos")

col_import, col_auto = st.columns([2, 1])

with col_import:
    archivo = st.file_uploader(
        "Importar Excel, CSV, PDF (BlueCorp) o DOCX (Jauregui)",
        type=["xlsx", "xls", "csv", "pdf", "docx"],
    )
    if archivo:
        try:
            df_imp, formato = parsear_archivo(archivo, archivo.name)
            # Si el documento trae fecha sugerida, pre-llenar Fecha hasta
            if "fecha_pago" in df_imp.columns and df_imp["fecha_pago"].notna().any():
                st.session_state.fecha_hasta = df_imp["fecha_pago"].dropna().iloc[0]
            st.session_state.filas = df_imp[["periodo", "capital", "fecha_desde"]].copy()
            st.session_state.resultado = None
            st.success(f"Importado formato **{formato}**: {len(df_imp)} períodos")
        except Exception as e:
            st.error(f"Error al importar: {e}")

with col_auto:
    st.markdown("&nbsp;", unsafe_allow_html=True)
    if st.button("Auto-completar fechas desde períodos", use_container_width=True,
                 help="Calcula 'fecha desde' como el 1° del mes siguiente al período"):
        df = st.session_state.filas.copy()
        for i, row in df.iterrows():
            if pd.notna(row.get("periodo")) and str(row["periodo"]).count("/") == 1:
                try:
                    df.at[i, "fecha_desde"] = primer_dia_mes_siguiente(str(row["periodo"]))
                except Exception:
                    pass
        st.session_state.filas = df
        st.rerun()

# ── Fecha hasta ──────────────────────────────────────────────────────────────
st.session_state.fecha_hasta = st.date_input(
    "Fecha hasta (fecha efectiva de pago — se aplica a toda la liquidación)",
    value=st.session_state.fecha_hasta,
    format="DD/MM/YYYY",
)

# ── Tabla editable ───────────────────────────────────────────────────────────
st.markdown("**Tabla de períodos** — editá directamente o importá desde Excel/CSV")

df_editor = st.data_editor(
    st.session_state.filas,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "periodo": st.column_config.TextColumn(
            "Período (MM/AAAA)",
            help="Ej: 04/2021",
            width="small",
        ),
        "capital": st.column_config.NumberColumn(
            "Capital / Dif. neta ($)",
            format="%.2f",
            min_value=0,
            width="medium",
        ),
        "fecha_desde": st.column_config.DateColumn(
            "Intereses desde",
            format="DD/MM/YYYY",
            width="medium",
        ),
    },
    key="editor_filas",
)
st.session_state.filas = df_editor

# ── Calcular ─────────────────────────────────────────────────────────────────
st.subheader("2. Calcular")

if st.button("▶ Calcular intereses moratorios", type="primary", use_container_width=True):
    if indice is None:
        st.error("El índice BCRA no está disponible.")
    else:
        df = st.session_state.filas.dropna(subset=["periodo", "capital", "fecha_desde"]).copy()
        df["fecha_pago"] = pd.Timestamp(st.session_state.fecha_hasta)
        if df.empty:
            st.warning("No hay filas completas para calcular.")
        else:
            with st.spinner("Calculando..."):
                resultado = calcular_intereses(df.reset_index(drop=True), indice)
            st.session_state.resultado = resultado

# ── Resultados ────────────────────────────────────────────────────────────────
if st.session_state.resultado is not None:
    st.subheader("3. Resultados")
    df_res = st.session_state.resultado

    errores = df_res[df_res["error"].notna()]
    if not errores.empty:
        st.warning(f"{len(errores)} fila(s) con error:")
        for _, r in errores.iterrows():
            st.write(f"  • {r['periodo']}: {r['error']}")

    df_ok = df_res[df_res["error"].isna()].copy()

    if not df_ok.empty:
        def fmt_ar(n):
            return f"$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        display = pd.DataFrame({
            "Período": df_ok["periodo"],
            "Intereses desde": df_ok["fecha_desde"].dt.strftime("%d/%m/%Y"),
            "Dif. neta": df_ok["capital"].apply(fmt_ar),
            "Índice inicial": df_ok["indice_inicial"].map("{:,.4f}".format),
            "Índice final": df_ok["indice_final"].map("{:,.4f}".format),
            "Coeficiente": df_ok["coeficiente"].map("{:.6f}".format),
            "Interés moratorio": df_ok["interes"].apply(fmt_ar),
            "Total": df_ok["total"].apply(fmt_ar),
        })
        st.dataframe(display, use_container_width=True, hide_index=True)

        # Totales
        t_cap = df_ok["capital"].sum()
        t_int = df_ok["interes"].sum()
        t_tot = df_ok["total"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Capital total", fmt_ar(t_cap))
        c2.metric("Intereses moratorios", fmt_ar(t_int))
        c3.metric("Total general", fmt_ar(t_tot))

        # ── Exportar ──────────────────────────────────────────────────────────
        st.subheader("4. Exportar")
        col_xl, col_pdf = st.columns(2)

        with col_xl:
            xlsx_bytes = exportar_excel(df_ok)
            st.download_button(
                "⬇ Descargar Excel",
                data=xlsx_bytes,
                file_name="liquidacion_rastrilla.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_pdf:
            pdf_bytes = exportar_pdf(df_ok)
            st.download_button(
                "⬇ Descargar PDF",
                data=pdf_bytes,
                file_name="liquidacion_rastrilla.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
