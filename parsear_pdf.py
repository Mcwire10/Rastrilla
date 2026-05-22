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
            if not row or len(row) < 7:
                continue
            # col[6] = "Diferencia - Deducción" (diferencia bruta mensual, sin OS ni HAC)
            # col[-2] = "Capital" (incluye HAC semestral — no se usa)
            f = _fila(row[0], row[1], row[6])
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


# ── Excel / CSV ───────────────────────────────────────────────────────────────

def parsear_excel(file, csv: bool = False) -> pd.DataFrame:
    """
    Parsea Excel o CSV.
    Soporta dos formatos:
    - Jauregui Excel: Mes | Año | … | Dif.Neta  (columnas separadas)
    - Estándar: columnas periodo, capital, fecha_desde, fecha_pago
    """
    df_raw = pd.read_csv(file, header=None) if csv else pd.read_excel(file, header=None)

    if df_raw.empty:
        raise ValueError("El archivo está vacío.")

    first = df_raw.iloc[0].fillna("").astype(str).str.strip().str.lower().tolist()

    # Detectar formato Jauregui: primera celda "mes" y hay columna "dif.neta"
    es_jauregui = first[0] == "mes" and any(
        "dif" in v and "neta" in v for v in first
    )

    if es_jauregui:
        dif_idx = next(i for i, v in enumerate(first) if "dif" in v and "neta" in v)
        filas = []
        vistos = set()
        for i in range(1, len(df_raw)):
            row = df_raw.iloc[i]
            mes_str = str(row.iloc[0]).strip()
            if not mes_str.isdigit():
                continue
            try:
                mes  = int(mes_str)
                anio = int(float(str(row.iloc[1]).strip()))
                cap  = _monto(str(row.iloc[dif_idx]))
            except (ValueError, TypeError):
                continue
            if cap is None or cap <= 0:
                continue
            periodo = f"{mes:02d}/{anio}"
            if periodo in vistos:      # saltar fila de totales con mismo período
                continue
            vistos.add(periodo)
            filas.append({
                "periodo":     periodo,
                "capital":     cap,
                "fecha_desde": primer_dia_mes_siguiente(periodo),
                "fecha_pago":  None,
            })
        if not filas:
            raise ValueError("No se encontraron datos válidos en el Excel Jauregui.")
        return pd.DataFrame(filas)

    # Formato estándar: primera fila como encabezado
    df = df_raw.copy()
    df.columns = df.iloc[0].fillna("").astype(str).str.lower().str.strip().str.replace(" ", "_")
    df = df.iloc[1:].reset_index(drop=True)
    mapa = {
        "período": "periodo", "periodo": "periodo",
        "capital": "capital",
        "dif._neta": "capital", "dif_neta": "capital", "dif.neta": "capital",
        "fecha_desde": "fecha_desde", "desde": "fecha_desde", "intereses_desde": "fecha_desde",
        "fecha_pago": "fecha_pago", "pago": "fecha_pago",
    }
    df = df.rename(columns={c: mapa[c] for c in df.columns if c in mapa})
    for col in ["periodo", "capital", "fecha_desde", "fecha_pago"]:
        if col not in df.columns:
            df[col] = None
    df = df[["periodo", "capital", "fecha_desde", "fecha_pago"]]
    df["capital"]     = pd.to_numeric(df["capital"], errors="coerce")
    df["fecha_desde"] = pd.to_datetime(df["fecha_desde"], dayfirst=True, errors="coerce").dt.date
    df["fecha_pago"]  = pd.to_datetime(df["fecha_pago"],  dayfirst=True, errors="coerce").dt.date
    return df.dropna(subset=["periodo", "capital"])


# ── Dispatcher ───────────────────────────────────────────────────────────────

def parsear_archivo(file, filename: str) -> tuple[pd.DataFrame, str]:
    """Detecta el formato y parsea. Devuelve (df, nombre_formato)."""
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return parsear_bluecorp(file), "BlueCorp"
    if ext == "docx":
        return parsear_jauregui(file), "Jauregui"
    if ext in ("xlsx", "xls"):
        df = parsear_excel(file, csv=False)
        return df, "Excel Jauregui" if len(df) > 0 else "Excel"
    if ext == "csv":
        df = parsear_excel(file, csv=True)
        return df, "CSV"
    raise ValueError(f"Formato no soportado: .{ext}")
