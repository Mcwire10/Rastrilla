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
    idx_inicial = indice.asof(fecha_desde)
    idx_final = indice.asof(fecha_pago)

    if pd.isna(idx_inicial):
        return {"error": f"Sin índice para fecha {fecha_desde.strftime('%d/%m/%Y')}"}
    if pd.isna(idx_final):
        return {"error": f"Sin índice para fecha {fecha_pago.strftime('%d/%m/%Y')}"}

    coeficiente = (idx_final / idx_inicial) - 1
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
