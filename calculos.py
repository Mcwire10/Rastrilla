import pandas as pd
from datetime import date


def primer_dia_mes_siguiente(periodo: str) -> date:
    """'04/2021' -> date(2021, 5, 1)"""
    mes, anio = int(periodo[:2]), int(periodo[3:])
    if mes == 12:
        return date(anio + 1, 1, 1)
    return date(anio, mes + 1, 1)


def calcular_fila(
    capital: float,
    fecha_desde: pd.Timestamp,
    fecha_pago: pd.Timestamp,
    indice: pd.Series,
) -> dict:
    # T0 = día anterior a fecha_desde (BCRA Res. 45/26, art. 55 Ley 27.802, sección C)
    t0_fecha = pd.Timestamp(fecha_desde) - pd.Timedelta(days=1)
    idx_inicial = indice.asof(t0_fecha)
    idx_final = indice.asof(pd.Timestamp(fecha_pago))

    if pd.isna(idx_inicial):
        return {"error": f"Sin índice para fecha {t0_fecha.strftime('%d/%m/%Y')}"}
    if pd.isna(idx_final):
        return {"error": f"Sin índice para fecha {pd.Timestamp(fecha_pago).strftime('%d/%m/%Y')}"}

    # i = ((100 + Tm) / (100 + T0) - 1)  — Metodología BCRA Res. 45/26
    coeficiente = (100 + float(idx_final)) / (100 + float(idx_inicial)) - 1
    interes = round(capital * coeficiente, 2)
    total = round(capital + interes, 2)

    return {
        "indice_inicial": round(float(idx_inicial), 4),
        "indice_final": round(float(idx_final), 4),
        "coeficiente": round(coeficiente, 6),
        "interes": interes,
        "total": total,
        "error": None,
    }


def calcular_interes_simple(
    capital: float,
    fecha_aprobacion: date,
    fecha_cobro: date,
    indice: pd.Series,
) -> dict:
    """
    Intereses Aprobados hasta Cobro.
    T0 = índice del día de aprobación (intereses corren desde el día SIGUIENTE).
    Tm = índice del día de cobro efectivo.
    """
    t0_fecha = pd.Timestamp(fecha_aprobacion)
    tm_fecha = pd.Timestamp(fecha_cobro)
    idx_inicial = indice.asof(t0_fecha)
    idx_final   = indice.asof(tm_fecha)

    if pd.isna(idx_inicial):
        raise ValueError(
            f"Sin índice BCRA para {fecha_aprobacion.strftime('%d/%m/%Y')}. "
            "Actualizá el índice desde el sidebar."
        )
    if pd.isna(idx_final):
        raise ValueError(
            f"Sin índice BCRA para {fecha_cobro.strftime('%d/%m/%Y')}. "
            "Actualizá el índice desde el sidebar."
        )

    coeficiente = (100 + float(idx_final)) / (100 + float(idx_inicial)) - 1
    interes = round(capital * coeficiente, 2)
    return {
        "capital":         capital,
        "fecha_desde":     (t0_fecha + pd.Timedelta(days=1)).date(),
        "fecha_hasta":     fecha_cobro,
        "indice_inicial":  round(float(idx_inicial), 4),
        "indice_final":    round(float(idx_final), 4),
        "coeficiente":     round(coeficiente, 6),
        "interes":         interes,
        "total":           round(capital + interes, 2),
    }


def calcular_intereses(df: pd.DataFrame, indice: pd.Series) -> pd.DataFrame:
    """
    df debe tener columnas: periodo, capital, fecha_desde, fecha_pago
    Retorna df completo con columnas de resultado agregadas.
    """
    filas = []
    for _, row in df.iterrows():
        res = calcular_fila(
            float(row["capital"]),
            pd.Timestamp(row["fecha_desde"]),
            pd.Timestamp(row["fecha_pago"]),
            indice,
        )
        filas.append({
            "periodo": row["periodo"],
            "capital": float(row["capital"]),
            "fecha_desde": pd.Timestamp(row["fecha_desde"]),
            "fecha_pago": pd.Timestamp(row["fecha_pago"]),
            **res,
        })

    cols = ["periodo", "capital", "fecha_desde", "fecha_pago",
            "indice_inicial", "indice_final", "coeficiente", "interes", "total", "error"]
    return pd.DataFrame(filas)[cols]
