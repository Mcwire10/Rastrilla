import pandas as pd
from datetime import date, timedelta

from calendario import dia_habil_n, fin_de_mes


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

    # i = (100 + Tm) / (100 + T0) - 1  — Metodología BCRA (Res. 45/26 / CM 14290)
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
    T0 = índice del día ANTERIOR a la aprobación (intereses corren desde el día de aprobación).
    Tm = índice del día de cobro efectivo.
    Fórmula: (100 + Tm) / (100 + T0) - 1  — igual que calcular_fila (CM 14290).
    """
    t0_fecha = pd.Timestamp(fecha_aprobacion) - pd.Timedelta(days=1)
    tm_fecha = pd.Timestamp(fecha_cobro)
    idx_inicial = indice.asof(t0_fecha)
    idx_final   = indice.asof(tm_fecha)

    if pd.isna(idx_inicial):
        raise ValueError(
            f"Sin índice BCRA para {t0_fecha.strftime('%d/%m/%Y')}. "
            "Actualizá el índice desde el sidebar."
        )
    if pd.isna(idx_final):
        raise ValueError(
            f"Sin índice BCRA para {fecha_cobro.strftime('%d/%m/%Y')}. "
            "Actualizá el índice desde el sidebar."
        )

    # i = (100 + Tm) / (100 + T0) - 1  — Metodología BCRA (Res. 45/26 / CM 14290)
    coeficiente = (100 + float(idx_final)) / (100 + float(idx_inicial)) - 1
    interes = round(capital * coeficiente, 2)
    return {
        "capital":         capital,
        "fecha_t0":        t0_fecha.date(),
        "fecha_desde":     fecha_aprobacion,
        "fecha_hasta":     fecha_cobro,
        "indice_inicial":  round(float(idx_inicial), 4),
        "indice_final":    round(float(idx_final), 4),
        "coeficiente":     round(coeficiente, 6),
        "interes":         interes,
        "total":           round(capital + interes, 2),
    }


def calcular_ejecucion(
    df_planilla: pd.DataFrame,
    fecha_devolucion: date,
    fecha_hasta: date,
    indice: pd.Series,
    feriados_extra: tuple = (),
) -> dict:
    """
    Calcula intereses para Ejecución de Sentencia (120 días hábiles judiciales).

    Tramo A: períodos cuya fecha_desde ≤ dia_120.
             Los capitales se suman y se calcula UN único interés desde dia_121.
             Si dia_120 cae dentro de un mes → split proporcional de ese capital.
    Tramo B: períodos con fecha_desde > dia_120.
             Igual a Ampliación: cada período corre desde su propia fecha_desde.

    Parameters
    ----------
    df_planilla   : DataFrame con columnas periodo, capital, fecha_desde
    fecha_devolucion : fecha desde la que se cuentan los 120 días hábiles
    fecha_hasta   : fecha efectiva de pago (extremo final de todos los intereses)
    indice        : Serie BCRA (asof)
    feriados_extra: tuple de date — inhábiles extra cargados en la DB
    """
    dia_120 = dia_habil_n(fecha_devolucion, 120, feriados_extra)
    dia_121 = dia_120 + timedelta(days=1)  # día siguiente calendario (no necesariamente hábil)

    filas_a: list[dict] = []
    filas_b: list[dict] = []

    for _, row in df_planilla.iterrows():
        periodo = row["periodo"]
        capital = float(row["capital"])
        fd = row["fecha_desde"]
        fecha_desde: date = fd.date() if hasattr(fd, "date") else fd

        fin_mes = fin_de_mes(fecha_desde)

        if fecha_desde > dia_120:
            # Todo en Tramo B
            capital_a, capital_b = 0.0, capital
        elif fin_mes <= dia_120:
            # Todo en Tramo A (el mes entero cae dentro de los 120 días)
            capital_a, capital_b = capital, 0.0
        else:
            # Día 120 cae dentro del mes → split proporcional
            dias_en_a   = (dia_120 - fecha_desde).days + 1
            dias_totales = (fin_mes - fecha_desde).days + 1
            capital_a = round(capital * dias_en_a / dias_totales, 2)
            capital_b = round(capital - capital_a, 2)

        if capital_a > 0:
            filas_a.append({"periodo": periodo, "capital": capital_a, "fecha_desde": fecha_desde})
        if capital_b > 0:
            filas_b.append({"periodo": periodo, "capital": capital_b, "fecha_desde": fecha_desde})

    # ── Tramo A: capital acumulado, interés único desde dia_121 ──────────────
    capital_a_total = round(sum(f["capital"] for f in filas_a), 2)
    if capital_a_total > 0:
        # calcular_fila usa T0 = fecha_desde - 1 día = dia_121 - 1 = dia_120 ✓
        res_a = calcular_fila(
            capital_a_total,
            pd.Timestamp(dia_121),
            pd.Timestamp(fecha_hasta),
            indice,
        )
    else:
        res_a = {"error": "No hay períodos en Tramo A para este rango de fechas."}

    # ── Tramo B: igual a Ampliación ───────────────────────────────────────────
    if filas_b:
        df_b = pd.DataFrame(filas_b)
        df_b["fecha_pago"] = pd.Timestamp(fecha_hasta)
        res_b = calcular_intereses(df_b.reset_index(drop=True), indice)
    else:
        cols = ["periodo", "capital", "fecha_desde", "fecha_pago",
                "indice_inicial", "indice_final", "coeficiente", "interes", "total", "error"]
        res_b = pd.DataFrame(columns=cols)

    return {
        "fecha_devolucion": fecha_devolucion,
        "fecha_hasta":      fecha_hasta,
        "dia_120":          dia_120,
        "dia_121":          dia_121,
        "filas_a":          filas_a,
        "capital_a_total":  capital_a_total,
        "resultado_a":      res_a,
        "resultado_b":      res_b,
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
