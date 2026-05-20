"""
Parsers específicos para cada formato de planilla de liquidación.
- parsear_bluecorp: PDF generado por BlueCorp / Ius Asociados
- parsear_jauregui: DOCX generado por Sistema Jauregui
"""
import re
from datetime import date

import pandas as pd
import pdfplumber
from docx import Document
from docx.oxml.ns import qn

from calculos import primer_dia_mes_siguiente


def _monto(val) -> float | None:
    if not val:
        return None
    val = re.sub(r'[^\d,.]', '', str(val)).strip()
    if not val:
        return None
    if ',' in val and '.' in val:
        val = val.replace('.', '').replace(',', '.')
    elif ',' in val:
        val = val.replace(',', '.')
    try:
        return float(val)
    except ValueError:
        return None


def _fecha(texto: str, patron: str) -> date | None:
    m = re.search(patron, texto, re.IGNORECASE)
    if not m:
        return None
    try:
        return pd.to_datetime(m.group(1), dayfirst=True, errors="coerce").date()
    except Exception:
        return None


def _fila(mes_str, anio_str, capital_str) -> dict | None:
    if not str(mes_str).strip().isdigit():
        return None
    try:
        mes = int(str(mes_str).strip())
        anio = int(str(anio_str).strip())
        capital = _monto(capital_str)
    except (ValueError, TypeError):
        return None
    if capital is None or capital <= 0:
        return None
    periodo = f"{mes:02d}/{anio}"
    return {
        "periodo": periodo,
        "capital": capital,
        "fecha_desde": primer_dia_mes_siguiente(periodo),
        "fecha_pago": None,
    }


# ── BlueCorp (PDF) ────────────────────────────────────────────────────────────

def parsear_bluecorp(file) -> pd.DataFrame:
    """
    PDF BlueCorp / Ius Asociados.
    Página 1: extrae fecha_pago del texto.
    Página 2: extrae tabla con columnas Mes | Año | ... | Capital | Interes.
    Capital = columna -2 (segunda desde el final).
    """
    filas = []
    fecha_pago = None

    with pdfplumber.open(file) as pdf:
        # fecha_pago en página 1
        texto_p1 = pdf.pages[0].extract_text() or ""
        fecha_pago = _fecha(texto_p1, r'calcularon hasta el\s+(\d{1,2}/\d{1,2}/\d{4})')

        # Tabla en página 2
        if len(pdf.pages) < 2:
            raise ValueError("El PDF BlueCorp debe tener al menos 2 páginas.")
        tables = pdf.pages[1].extract_tables()
        if not tables:
            raise ValueError("No se encontró tabla en la página 2 del PDF.")

        for row in tables[0]:
            if not row or len(row) < 3:
                continue
            f = _fila(row[0], row[1], row[-2])
            if f:
                f["fecha_pago"] = fecha_pago
                filas.append(f)

    if not filas:
        raise ValueError(
            "No se encontraron datos en el PDF BlueCorp.\n"
            "Verificá que el archivo sea una liquidación BlueCorp / Ius Asociados."
        )
    return pd.DataFrame(filas)


# ── Jauregui (DOCX) ──────────────────────────────────────────────────────────

def parsear_jauregui(file) -> pd.DataFrame:
    """
    DOCX Sistema Jauregui.
    Tabla principal fila 77: extrae fecha_pago del texto.
    Tabla anidada en fila 78: Mes | Año | ... | Dif.Neta (col 11) | ...
    """
    filas = []
    fecha_pago = None

    doc = Document(file)
    if len(doc.tables) < 2:
        raise ValueError("El DOCX Jauregui no tiene la estructura esperada.")

    main_table = doc.tables[1]

    # fecha_pago en fila 77
    try:
        texto_77 = main_table.rows[77].cells[0].text
        fecha_pago = _fecha(texto_77, r'calcularon hasta el:\s*(\d{1,2}/\d{1,2}/\d{4})')
    except IndexError:
        pass

    # Tabla anidada en fila 78
    try:
        cell_78 = main_table.rows[78].cells[0]
    except IndexError:
        raise ValueError("No se encontró la sección de liquidación (fila 78) en el DOCX.")

    nested = cell_78._element.findall('.//' + qn('w:tbl'))
    if not nested:
        raise ValueError("No se encontró tabla de datos en el DOCX Jauregui.")

    for row_el in nested[0].findall('.//' + qn('w:tr')):
        cells = row_el.findall('.//' + qn('w:tc'))
        vals = [''.join(t.text or '' for t in tc.findall('.//' + qn('w:t'))).strip()
                for tc in cells]
        if len(vals) < 12:
            continue
        f = _fila(vals[0], vals[1], vals[11])
        if f:
            f["fecha_pago"] = fecha_pago
            filas.append(f)

    if not filas:
        raise ValueError(
            "No se encontraron datos en el DOCX Jauregui.\n"
            "Verificá que el archivo sea una liquidación del Sistema Jauregui."
        )
    return pd.DataFrame(filas)


# ── Dispatcher ───────────────────────────────────────────────────────────────

def parsear_archivo(file, filename: str) -> tuple[pd.DataFrame, str]:
    """
    Detecta el formato y parsea. Devuelve (df, nombre_formato).
    """
    ext = filename.lower().rsplit('.', 1)[-1]
    if ext == 'pdf':
        return parsear_bluecorp(file), "BlueCorp"
    if ext == 'docx':
        return parsear_jauregui(file), "Jauregui"
    raise ValueError(f"Formato no soportado: .{ext}. Usá PDF (BlueCorp) o DOCX (Jauregui).")
