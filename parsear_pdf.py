import re
import pandas as pd
import pdfplumber


def _limpiar_periodo(val) -> str | None:
    if not val:
        return None
    val = str(val).strip()
    m = re.search(r'(\d{1,2})[/\-](\d{2,4})', val)
    if m:
        mes = m.group(1).zfill(2)
        anio = m.group(2)
        if len(anio) == 2:
            anio = "20" + anio
        return f"{mes}/{anio}"
    # Solo número de mes (columna separada)
    if re.fullmatch(r'\d{1,2}', val):
        return val.zfill(2)
    return None


def _limpiar_monto(val) -> float | None:
    if not val:
        return None
    val = re.sub(r'[^\d,.]', '', str(val)).strip()
    if not val:
        return None
    # Formato AR: 1.234,56
    if ',' in val and '.' in val:
        val = val.replace('.', '').replace(',', '.')
    elif ',' in val:
        val = val.replace(',', '.')
    try:
        return float(val)
    except ValueError:
        return None


def _limpiar_fecha(val) -> "date | None":
    if not val:
        return None
    try:
        ts = pd.to_datetime(str(val).strip(), dayfirst=True, errors="coerce")
        return None if pd.isna(ts) else ts.date()
    except Exception:
        return None


def _idx_col(headers: list, keywords: list) -> int | None:
    """Devuelve el índice de la primera columna cuyo header matchea alguna keyword."""
    for i, h in enumerate(headers):
        h_norm = str(h or "").lower().replace(".", "").replace("/", " ").strip()
        if any(k in h_norm for k in keywords):
            return i
    return None


def parsear_pdf(file) -> pd.DataFrame:
    """
    Extrae datos de liquidación de un PDF.
    Soporta:
      - Planilla con Mes/Año en una columna
      - Planilla con Mes y Año en columnas separadas + columna Dif. Neta
    Devuelve DataFrame con: periodo, capital, fecha_desde, fecha_pago
    """
    filas = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            for tabla in (page.extract_tables() or []):
                if not tabla or len(tabla) < 2:
                    continue

                # Buscar fila de encabezado
                header_idx = None
                for i, fila in enumerate(tabla):
                    texto = " ".join(str(c or "") for c in fila).lower()
                    if any(k in texto for k in ["mes", "período", "periodo", "dif", "capital"]):
                        header_idx = i
                        break
                if header_idx is None:
                    continue

                headers = [str(h or "").strip() for h in tabla[header_idx]]

                # Mapear columnas
                i_mes   = _idx_col(headers, ["mes"])
                i_anio  = _idx_col(headers, ["año", "ano"])
                i_per   = _idx_col(headers, ["período", "periodo"])
                i_cap   = _idx_col(headers, ["dif neta", "dif. neta", "diferencia neta", "capital"])
                i_desde = _idx_col(headers, ["intereses desde", "desde", "fecha desde"])
                i_pago  = _idx_col(headers, ["fecha pago", "pago"])

                # Necesitamos al menos periodo (o mes+año) y capital
                tiene_periodo = i_per is not None or (i_mes is not None and i_anio is not None)
                if not tiene_periodo or i_cap is None:
                    continue

                for fila in tabla[header_idx + 1:]:
                    if not fila or all(not c for c in fila):
                        continue

                    # Construir periodo
                    if i_per is not None:
                        periodo = _limpiar_periodo(fila[i_per])
                    else:
                        mes_str  = _limpiar_periodo(fila[i_mes])
                        anio_val = str(fila[i_anio] or "").strip()
                        if mes_str and re.fullmatch(r'\d{4}', anio_val):
                            periodo = f"{mes_str}/{anio_val}"
                        else:
                            periodo = None

                    capital    = _limpiar_monto(fila[i_cap])
                    fecha_desde = _limpiar_fecha(fila[i_desde]) if i_desde is not None else None
                    fecha_pago  = _limpiar_fecha(fila[i_pago])  if i_pago  is not None else None

                    if periodo and capital and capital > 0:
                        filas.append({
                            "periodo":     periodo,
                            "capital":     capital,
                            "fecha_desde": fecha_desde,
                            "fecha_pago":  fecha_pago,
                        })

    if not filas:
        raise ValueError(
            "No se encontraron datos válidos en el PDF.\n"
            "Verificá que el archivo tenga una tabla con columnas de período y capital/diferencia neta."
        )

    return pd.DataFrame(filas)
