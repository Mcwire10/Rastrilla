import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _fmt(n: float) -> str:
    """Formato argentino: 1.234.567,89"""
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def exportar_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    out = pd.DataFrame({
        "Período": df["periodo"],
        "Capital ($)": df["capital"],
        "Intereses desde": df["fecha_desde"].dt.strftime("%d/%m/%Y"),
        "Fecha pago": df["fecha_pago"].dt.strftime("%d/%m/%Y"),
        "Índice inicial": df["indice_inicial"],
        "Índice final": df["indice_final"],
        "Coeficiente": df["coeficiente"],
        "Interés moratorio ($)": df["interes"],
        "Total ($)": df["total"],
    })

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        out.to_excel(writer, index=False, sheet_name="Liquidación")
        ws = writer.sheets["Liquidación"]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 3, 30)

    return buf.getvalue()


def exportar_pdf(df: pd.DataFrame, titulo: str = "PLANILLA DE LIQUIDACIÓN - INTERESES MORATORIOS - DOCTRINA RASTRILLA") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=1 * cm, rightMargin=1 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(titulo, styles["Title"]))
    story.append(Paragraph(
        "Tasa pasiva BCRA Com. 14290 · Cálculo por coeficiente acumulado · Criterio RASTRILLA",
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.5 * cm))

    headers = ["Mes/Año", "Int. desde", "Dif. neta", "Índ. inicial", "Índ. final", "Coeficiente", "Interés moratorio", "Total"]
    rows = [headers]

    for _, row in df.iterrows():
        rows.append([
            row["periodo"],
            row["fecha_desde"].strftime("%d/%m/%Y"),
            f"$ {_fmt(row['capital'])}",
            f"{row['indice_inicial']:,.4f}",
            f"{row['indice_final']:,.4f}",
            f"{row['coeficiente']:.6f}",
            f"$ {_fmt(row['interes'])}",
            f"$ {_fmt(row['total'])}",
        ])

    total_capital = df["capital"].sum()
    total_interes = df["interes"].sum()
    total_general = df["total"].sum()
    rows.append(["TOTAL GENERAL", "", f"$ {_fmt(total_capital)}", "", "", "", f"$ {_fmt(total_interes)}", f"$ {_fmt(total_general)}"])

    available_width = 27.7 * cm
    col_widths = [w * cm for w in [2.8, 2.5, 3.8, 3.2, 3.2, 3.2, 4.0, 4.0]]
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ("ALIGN", (6, 1), (7, -1), "RIGHT"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#eef2f7")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fef3cd")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, -1), (-1, -1), "CENTER"),
    ]))
    story.append(t)

    doc.build(story)
    return buf.getvalue()


# ── Ejecución de Sentencia — Excel (2 hojas) ───────────────────────────────────

def exportar_excel_ejecucion(resultado: dict) -> bytes:
    """Excel con dos hojas: Tramo A (desglose + cálculo único) y Tramo B."""
    buf = io.BytesIO()

    dia_120          = resultado["dia_120"]
    dia_121          = resultado["dia_121"]
    filas_a          = resultado["filas_a"]
    capital_a_total  = resultado["capital_a_total"]
    res_a            = resultado["resultado_a"]
    res_b            = resultado["resultado_b"]
    fecha_hasta      = resultado["fecha_hasta"]

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:

        # ── Hoja Tramo A ──────────────────────────────────────────────────────
        # Tabla 1: aporte proporcional por período
        df_periodos = pd.DataFrame(
            [{"Período": f["periodo"], "Capital proporcional ($)": f["capital"]} for f in filas_a]
            + [{"Período": "TOTAL TRAMO A", "Capital proporcional ($)": capital_a_total}]
        )
        df_periodos.to_excel(writer, index=False, sheet_name="Tramo A", startrow=0)

        # Tabla 2: cálculo único de intereses sobre el total
        startrow_calc = len(df_periodos) + 3
        if not res_a.get("error"):
            df_calc = pd.DataFrame([{
                "Capital total ($)":     capital_a_total,
                "Intereses desde":       dia_121.strftime("%d/%m/%Y"),
                "Intereses hasta":       fecha_hasta.strftime("%d/%m/%Y"),
                "T₀ (Día 120)":          dia_120.strftime("%d/%m/%Y"),
                "Índice T₀":             res_a["indice_inicial"],
                "Índice Tₘ":             res_a["indice_final"],
                "Coeficiente":           res_a["coeficiente"],
                "Interés moratorio ($)": res_a["interes"],
                "Total ($)":             res_a["total"],
            }])
        else:
            df_calc = pd.DataFrame([{"Error": res_a["error"]}])
        df_calc.to_excel(writer, index=False, sheet_name="Tramo A", startrow=startrow_calc)

        ws_a = writer.sheets["Tramo A"]
        for col in ws_a.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws_a.column_dimensions[col[0].column_letter].width = min(max_len + 3, 35)

        # ── Hoja Tramo B ──────────────────────────────────────────────────────
        if not res_b.empty:
            df_b_ok = res_b[res_b["error"].isna()].copy()
            df_out = pd.DataFrame({
                "Período":               df_b_ok["periodo"],
                "Capital ($)":           df_b_ok["capital"],
                "Intereses desde":       df_b_ok["fecha_desde"].dt.strftime("%d/%m/%Y"),
                "Fecha pago":            df_b_ok["fecha_pago"].dt.strftime("%d/%m/%Y"),
                "Índice T₀":             df_b_ok["indice_inicial"],
                "Índice Tₘ":             df_b_ok["indice_final"],
                "Coeficiente":           df_b_ok["coeficiente"],
                "Interés moratorio ($)": df_b_ok["interes"],
                "Total ($)":             df_b_ok["total"],
            })
        else:
            df_out = pd.DataFrame(columns=[
                "Período", "Capital ($)", "Intereses desde", "Fecha pago",
                "Índice T₀", "Índice Tₘ", "Coeficiente", "Interés moratorio ($)", "Total ($)",
            ])

        df_out.to_excel(writer, index=False, sheet_name="Tramo B")
        ws_b = writer.sheets["Tramo B"]
        for col in ws_b.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws_b.column_dimensions[col[0].column_letter].width = min(max_len + 3, 30)

    return buf.getvalue()


# ── Ejecución de Sentencia — PDF ───────────────────────────────────────────────

def exportar_pdf_ejecucion(
    resultado: dict,
    titulo: str = "EJECUCIÓN DE SENTENCIA — DOCTRINA RASTRILLA · VEGA",
) -> bytes:
    """PDF con sección Tramo A (desglose + cálculo único) y sección Tramo B."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=1 * cm, rightMargin=1 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    story  = []

    dia_120         = resultado["dia_120"]
    dia_121         = resultado["dia_121"]
    filas_a         = resultado["filas_a"]
    capital_a_total = resultado["capital_a_total"]
    res_a           = resultado["resultado_a"]
    res_b           = resultado["resultado_b"]
    fecha_hasta     = resultado["fecha_hasta"]

    # ── Encabezado ─────────────────────────────────────────────────────────────
    story.append(Paragraph(titulo, styles["Title"]))
    story.append(Paragraph(
        "Tasa pasiva BCRA Com. 14290 · Cálculo por coeficiente acumulado · Criterio RASTRILLA",
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.4 * cm))

    # ── Tramo A ─────────────────────────────────────────────────────────────────
    story.append(Paragraph(
        f"<b>TRAMO A</b> — Períodos dentro del plazo de 120 días hábiles judiciales &nbsp;|&nbsp; "
        f"Día 120: <b>{dia_120.strftime('%d/%m/%Y')}</b> &nbsp;·&nbsp; "
        f"Intereses desde (Día 121): <b>{dia_121.strftime('%d/%m/%Y')}</b> &nbsp;·&nbsp; "
        f"Hasta: <b>{fecha_hasta.strftime('%d/%m/%Y')}</b>",
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.2 * cm))

    # Tabla de aportes por período
    if filas_a:
        rows_a = [["Período", "Capital proporcional ($)"]]
        for f in filas_a:
            rows_a.append([f["periodo"], f"$ {_fmt(f['capital'])}"])
        rows_a.append(["TOTAL TRAMO A", f"$ {_fmt(capital_a_total)}"])
        t_a1 = Table(rows_a, colWidths=[4 * cm, 5 * cm])
        t_a1.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("ALIGN",         (1, 0), (1, -1),  "RIGHT"),
            ("ROWBACKGROUNDS",(0, 1), (-1, -2), [colors.white, colors.HexColor("#eef2f7")]),
            ("BACKGROUND",    (0, -1), (-1, -1), colors.HexColor("#fef3cd")),
            ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_a1)
        story.append(Spacer(1, 0.2 * cm))

    # Tabla del cálculo único de Tramo A
    if not res_a.get("error"):
        rows_calc = [
            ["Capital total ($)", "Int. desde", "Int. hasta",
             "Índ. T₀", "Índ. Tₘ", "Coeficiente", "Interés moratorio ($)", "Total ($)"],
            [
                f"$ {_fmt(capital_a_total)}",
                dia_121.strftime("%d/%m/%Y"),
                fecha_hasta.strftime("%d/%m/%Y"),
                f"{res_a['indice_inicial']:,.4f}",
                f"{res_a['indice_final']:,.4f}",
                f"{res_a['coeficiente']:.6f}",
                f"$ {_fmt(res_a['interes'])}",
                f"$ {_fmt(res_a['total'])}",
            ],
        ]
        col_w_calc = [w * cm for w in [3.5, 2.5, 2.5, 3.0, 3.0, 3.0, 4.5, 4.5]]
        t_a2 = Table(rows_calc, colWidths=col_w_calc)
        t_a2.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#2d6a4f")),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("BACKGROUND",    (0, 1), (-1, 1),  colors.HexColor("#d8f3dc")),
            ("FONTNAME",      (0, 1), (-1, 1),  "Helvetica-Bold"),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_a2)
    else:
        story.append(Paragraph(f"Sin datos para Tramo A: {res_a.get('error', '')}", styles["Normal"]))

    story.append(Spacer(1, 0.5 * cm))

    # ── Tramo B ─────────────────────────────────────────────────────────────────
    story.append(Paragraph(
        "<b>TRAMO B</b> — Períodos posteriores al día 120 · Intereses por período (criterio Ampliación)",
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.2 * cm))

    if not res_b.empty:
        df_b_ok = res_b[res_b["error"].isna()].copy()
        rows_b = [["Período", "Int. desde", "Capital ($)",
                   "Índ. T₀", "Índ. Tₘ", "Coeficiente", "Interés ($)", "Total ($)"]]
        for _, row in df_b_ok.iterrows():
            rows_b.append([
                row["periodo"],
                row["fecha_desde"].strftime("%d/%m/%Y"),
                f"$ {_fmt(row['capital'])}",
                f"{row['indice_inicial']:,.4f}",
                f"{row['indice_final']:,.4f}",
                f"{row['coeficiente']:.6f}",
                f"$ {_fmt(row['interes'])}",
                f"$ {_fmt(row['total'])}",
            ])
        t_cap_b = df_b_ok["capital"].sum()
        t_int_b = df_b_ok["interes"].sum()
        t_tot_b = df_b_ok["total"].sum()
        rows_b.append(["TOTAL TRAMO B", "", f"$ {_fmt(t_cap_b)}", "", "",
                        "", f"$ {_fmt(t_int_b)}", f"$ {_fmt(t_tot_b)}"])

        col_w_b = [w * cm for w in [2.8, 2.5, 3.8, 3.2, 3.2, 3.2, 4.0, 4.0]]
        t_b = Table(rows_b, colWidths=col_w_b, repeatRows=1)
        t_b.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0),  (-1, 0),  colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR",     (0, 0),  (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0),  (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0),  (-1, -1), 8),
            ("ALIGN",         (0, 0),  (-1, 0),  "CENTER"),
            ("ALIGN",         (2, 1),  (2, -1),  "RIGHT"),
            ("ALIGN",         (6, 1),  (7, -1),  "RIGHT"),
            ("ROWBACKGROUNDS",(0, 1),  (-1, -2), [colors.white, colors.HexColor("#eef2f7")]),
            ("BACKGROUND",    (0, -1), (-1, -1), colors.HexColor("#fef3cd")),
            ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID",          (0, 0),  (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("VALIGN",        (0, 0),  (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0),  (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0),  (-1, -1), 4),
            ("ALIGN",         (0, -1), (-1, -1), "CENTER"),
        ]))
        story.append(t_b)
    else:
        story.append(Paragraph("No hay períodos en Tramo B.", styles["Normal"]))

    doc.build(story)
    return buf.getvalue()
