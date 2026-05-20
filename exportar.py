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
