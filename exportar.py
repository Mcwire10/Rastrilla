import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from docx import Document
from docx.shared import Pt, Cm as DCm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


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

        # Tabla 3: resultado final (intereses A + B) y fecha hasta
        int_a_xls = float(res_a.get("interes", 0) or 0) if not res_a.get("error") else 0.0
        int_b_xls = float(res_b["interes"].sum()) if not res_b.empty and "interes" in res_b.columns else 0.0
        startrow_final = startrow_calc + len(df_calc) + 3
        df_final = pd.DataFrame([
            {
                "Concepto": "RESULTADO FINAL — Suma intereses moratorios Tramo A + Tramo B",
                "Valor":    int_a_xls + int_b_xls,
            },
            {
                "Concepto": "Calculado hasta — Efectivo pago conforme recibo que consta en autos",
                "Valor":    fecha_hasta.strftime("%d/%m/%Y"),
            },
        ])
        df_final.to_excel(writer, index=False, sheet_name="Tramo A", startrow=startrow_final)

        ws_a = writer.sheets["Tramo A"]
        for col in ws_a.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws_a.column_dimensions[col[0].column_letter].width = min(max_len + 3, 55)

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

    # ── Resultado final ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.6 * cm))
    int_a_val = float(resultado.get("resultado_a", {}).get("interes", 0) or 0)
    int_b_val = float(res_b["interes"].sum()) if not res_b.empty and "interes" in res_b.columns else 0.0
    int_total = int_a_val + int_b_val

    rows_final = [
        [
            "RESULTADO FINAL — Suma intereses moratorios Tramo A + Tramo B",
            f"$ {_fmt(int_total)}",
        ],
        [
            "Calculado hasta — Efectivo pago conforme recibo que consta en autos",
            fecha_hasta.strftime("%d/%m/%Y"),
        ],
    ]
    available_w = 27.7 * cm
    t_final = Table(rows_final, colWidths=[available_w * 0.72, available_w * 0.28])
    t_final.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#052e16")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  10),
        ("BACKGROUND",    (0, 1), (-1, 1),  colors.HexColor("#f0fdf4")),
        ("TEXTCOLOR",     (0, 1), (-1, 1),  colors.HexColor("#052e16")),
        ("FONTNAME",      (0, 1), (-1, 1),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 1), (-1, 1),  9),
        ("ALIGN",         (1, 0), (1, -1),  "RIGHT"),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#16a34a")),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(t_final)

    doc.build(story)
    return buf.getvalue()


# ── Intereses hasta el Cobro — DOCX (Escrito judicial) ───────────────────────

def _numero_a_palabras(monto: float) -> str:
    """Convierte monto a palabras en castellano (mayúsculas) para escritos judiciales.
    Ej: 250000.50 → 'DOSCIENTOS CINCUENTA MIL CON 50/100'
    """
    _UNI = ["", "UN", "DOS", "TRES", "CUATRO", "CINCO",
            "SEIS", "SIETE", "OCHO", "NUEVE"]
    _ESP = ["DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE",
            "DIECISÉIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE"]
    _DEC = ["", "DIEZ", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA",
            "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"]
    _CEN = ["", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS",
            "QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]
    _VTI = {21: "VEINTIÚN", 22: "VEINTIDÓS", 23: "VEINTITRÉS", 24: "VEINTICUATRO",
            25: "VEINTICINCO", 26: "VEINTISÉIS", 27: "VEINTISIETE",
            28: "VEINTIOCHO", 29: "VEINTINUEVE"}

    def _bloque(n: int) -> str:
        if n == 0:
            return ""
        if n == 100:
            return "CIEN"
        partes = []
        c, resto = divmod(n, 100)
        if c:
            partes.append(_CEN[c])
        if 10 <= resto <= 19:
            partes.append(_ESP[resto - 10])
        elif 21 <= resto <= 29:
            partes.append(_VTI[resto])
        elif resto == 20:
            partes.append("VEINTE")
        else:
            d, u = divmod(resto, 10)
            if d:
                partes.append(_DEC[d])
            if u:
                if d:
                    partes.append("Y")
                partes.append(_UNI[u])
        return " ".join(p for p in partes if p)

    entero = int(monto)
    cents  = round((monto - entero) * 100)

    if entero == 0:
        palabras = "CERO"
    else:
        millones   = entero // 1_000_000
        resto_mill = entero % 1_000_000
        miles      = resto_mill // 1_000
        resto_mil  = resto_mill % 1_000
        partes = []
        if millones == 1:
            partes.append("UN MILLÓN")
        elif millones > 1:
            partes.append(f"{_bloque(millones)} MILLONES")
        if miles == 1:
            partes.append("MIL")
        elif miles > 1:
            partes.append(f"{_bloque(miles)} MIL")
        if resto_mil:
            partes.append(_bloque(resto_mil))
        palabras = " ".join(p for p in partes if p)

    if cents:
        palabras += f" CON {cents:02d}/100"
    return palabras


def _docx_shade_cell(cell, fill: str) -> None:
    """Aplica color de fondo a una celda DOCX (fill sin #)."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def _docx_set_col_widths(table, widths_cm: list) -> None:
    """Establece el ancho de cada columna de una tabla DOCX."""
    for row in table.rows:
        for j, cell in enumerate(row.cells):
            if j < len(widths_cm):
                cell.width = DCm(widths_cm[j])


def _docx_add_table_header(table, headers: list, fill: str = "1E3A5F") -> None:
    """Escribe la fila de encabezado con fondo oscuro y texto blanco."""
    hdr_row = table.rows[0]
    for i, txt in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.text = ""
        _docx_shade_cell(cell, fill)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(txt)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.size = Pt(8)


def _docx_add_data_row(table, row_idx: int, values: list,
                       bold: bool = False, fill: str | None = None) -> None:
    """Escribe una fila de datos en la tabla DOCX."""
    row = table.rows[row_idx]
    for j, val in enumerate(values):
        cell = row.cells[j]
        cell.text = ""
        if fill:
            _docx_shade_cell(cell, fill)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(str(val))
        run.bold = bold
        run.font.size = Pt(8)


def generar_docx_cobro(
    resultado: dict,
    letrado: dict,
    caratula: str,
    expediente: str,
) -> bytes:
    """Genera escrito judicial DOCX — Intereses hasta el Cobro."""

    # ── Datos ────────────────────────────────────────────────────────────────
    capital      = resultado["capital"]
    interes      = resultado["interes"]
    fecha_desde  = resultado["fecha_desde"]
    fecha_hasta  = resultado["fecha_hasta"]
    fecha_t0     = resultado["fecha_t0"]
    ind_ini      = resultado["indice_inicial"]
    ind_fin      = resultado["indice_final"]
    coef         = resultado["coeficiente"]

    monto_total    = interes
    nombre_letrado = letrado.get("nombre_completo", "").upper()
    cuil_letrado   = letrado.get("cuil", "")

    # ── Documento ────────────────────────────────────────────────────────────
    doc = Document()
    sec = doc.sections[0]
    sec.page_width    = DCm(21.0)
    sec.page_height   = DCm(29.7)
    sec.left_margin   = DCm(3.0)
    sec.right_margin  = DCm(2.0)
    sec.top_margin    = DCm(2.5)
    sec.bottom_margin = DCm(2.5)
    doc.styles["Normal"].font.name = "Arial"
    doc.styles["Normal"].font.size = Pt(12)

    def _par_mixed(parts: list, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                   indent: float = 1.25, space_after: float = 6) -> None:
        """Párrafo con runs de distintos formatos. parts: [(text, bold, underline)]."""
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.first_line_indent = DCm(indent)
        p.paragraph_format.space_after = Pt(space_after)
        for text, bold, underline in parts:
            r = p.add_run(text)
            r.bold = bold
            r.underline = underline
            r.font.size = Pt(12)

    def _par(text: str, bold: bool = False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
             indent: float = 1.25, space_after: float = 6) -> None:
        _par_mixed([(text, bold, False)], align=align, indent=indent, space_after=space_after)

    def _spacer(pt: float = 4) -> None:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(pt)
        p.paragraph_format.space_before = Pt(0)

    # ── TÍTULO ───────────────────────────────────────────────────────────────
    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.first_line_indent = DCm(0)
    p_tit.paragraph_format.space_after = Pt(8)
    r = p_tit.add_run("PRACTICA LIQUIDACION – INTERESES")
    r.bold = True
    r.underline = True
    r.font.size = Pt(12)

    # ── SEÑOR JUEZ FEDERAL ───────────────────────────────────────────────────
    p_juez = doc.add_paragraph()
    p_juez.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_juez.paragraph_format.first_line_indent = DCm(0)
    p_juez.paragraph_format.space_after = Pt(6)
    r2 = p_juez.add_run("SEÑOR JUEZ FEDERAL:")
    r2.bold = True
    r2.font.size = Pt(12)

    # ── Párrafo letrado + carátula ───────────────────────────────────────────
    p_intro = doc.add_paragraph()
    p_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_intro.paragraph_format.first_line_indent = DCm(1.25)
    p_intro.paragraph_format.space_after = Pt(10)
    for text, bold in [
        (nombre_letrado, True),
        (f", CUIL {cuil_letrado}, abogado, con personería acreditada en autos caratulados: «", False),
        (f"{caratula} - EXPTE. {expediente}", True),
        ("», con domicilio legal y electrónico constituido, a V.S. respetuosamente digo:", False),
    ]:
        r3 = p_intro.add_run(text)
        r3.bold = bold
        r3.font.size = Pt(12)

    # ── I. OBJETO ────────────────────────────────────────────────────────────
    _par_mixed([("I. OBJETO:", True, True)], indent=1.25, space_after=4)
    _par(
        "Que vengo por el presente a practicar liquidación de los intereses devengados "
        "hasta el efectivo pago del crédito reconocido en autos, conforme las pautas "
        "oportunamente establecidas y el criterio emergente de la sentencia firme.",
        space_after=10,
    )

    # ── II. LIQUIDACION PRACTICADA ────────────────────────────────────────────
    _par_mixed([("II. LIQUIDACION PRACTICADA:", True, True)], indent=1.25, space_after=4)
    _par(
        "Para la confección de la presente liquidación se aplicó la Tasa Pasiva Promedio "
        "del Banco Central de la República Argentina desde el día siguiente al que quedó "
        "aprobada la liquidación precedente y hasta la fecha de efectivo pago, entendiendo "
        "por tal aquella en que los fondos fueron efectivamente acreditados en la cuenta "
        "bancaria del actor, todo ello conforme constancias de autos.",
        space_after=6,
    )

    monto_palabras = _numero_a_palabras(monto_total)
    monto_numero   = _fmt(monto_total)
    _par_mixed([
        ("En consecuencia, la diferencia resultante a favor de la parte actora en concepto "
         "de intereses devengados hasta su efectivo pago asciende a la suma de PESOS ", False, False),
        (f"{monto_palabras} ($ {monto_numero})", True, False),
        (".", False, False),
    ], space_after=10)

    # ── PLANILLA ─────────────────────────────────────────────────────────────
    p_pl = doc.add_paragraph()
    p_pl.paragraph_format.first_line_indent = DCm(0)
    p_pl.paragraph_format.space_after = Pt(3)
    rpl = p_pl.add_run("PLANILLA DE LIQUIDACIÓN")
    rpl.bold = True
    rpl.font.size = Pt(9)

    # Tabla de cálculo: 7 columnas, fila única de datos
    tbl = doc.add_table(rows=2, cols=7)
    tbl.style = "Table Grid"
    _docx_set_col_widths(tbl, [2.5, 2.3, 2.3, 2.0, 2.0, 2.4, 2.5])
    _docx_add_table_header(
        tbl,
        ["Capital ($)", "Int. desde", "Int. hasta",
         "Índice T₀", "Índice Tₘ", "Coeficiente", "Interés moratorio ($)"],
    )
    _docx_add_data_row(tbl, 1, [
        f"$ {_fmt(capital)}",
        fecha_desde.strftime("%d/%m/%Y"),
        fecha_hasta.strftime("%d/%m/%Y"),
        f"{ind_ini:,.4f}",
        f"{ind_fin:,.4f}",
        f"{coef:.6f}",
        f"$ {_fmt(interes)}",
    ], bold=True, fill="D8F3DC")
    _spacer(10)

    # ── III. DERECHO ─────────────────────────────────────────────────────────
    _par_mixed([("III. DERECHO:", True, True)], indent=1.25, space_after=4)
    _par(
        "La presente liquidación encuentra sustento en lo dispuesto en autos y en el "
        "criterio de sentencia firme que reconoce la procedencia de los intereses devengados "
        "hasta la íntegra satisfacción del crédito reconocido judicialmente.",
        space_after=6,
    )
    _par(
        "Asimismo, corresponde la aplicación de la tasa pasiva promedio del Banco Central "
        "de la República Argentina para el período comprendido entre la aprobación de la "
        "liquidación precedente y la efectiva acreditación de los fondos, en tanto durante "
        "dicho lapso subsistió impaga la obligación a cargo de la demandada.",
        space_after=10,
    )

    # ── IV. PETITUM ──────────────────────────────────────────────────────────
    _par_mixed([
        ("IV. PETITUM:", True, True),
        (" Por lo expuesto a V.S., solicito:", False, False),
    ], indent=1.25, space_after=4)
    _par(
        "a) Tenga por practicada la liquidación de intereses devengados hasta su efectivo "
        "pago conforme planilla que se acompaña.",
        space_after=4,
    )
    _par("b) Oportunamente, apruebe la misma en cuanto por derecho corresponda.", space_after=4)
    _par("c) Intime a la demandada al pago de las sumas resultantes.", space_after=10)

    # ── Cierre ───────────────────────────────────────────────────────────────
    _par("Proveer de conformidad,", indent=1.25, space_after=4)
    _par("SERÁ JUSTICIA.", bold=True, indent=1.25, space_after=0)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
