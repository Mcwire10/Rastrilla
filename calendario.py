"""
calendario.py — Calendario judicial para cálculo de días hábiles.

Feriados incluidos:
  - Nacionales inamovibles (fijos por ley)
  - Nacionales trasladables (Aug 17, Oct 12, Nov 20) — trasladados al lunes más cercano
  - Semana Santa (Viernes Santo) y Carnaval — calculados desde Pascua
  - Feria judicial de verano: 15-31 enero
  - Feria judicial de invierno: 1-15 julio
  - Feriados extra manuales (tabla DB, pasados como parámetro)
"""
from datetime import date, timedelta
from functools import lru_cache


# ── Feriados fijos (día, mes) ─────────────────────────────────────────────────
_FIJOS = [
    (1,  1),   # Año Nuevo
    (2,  4),   # Día del Veterano y los Caídos en Malvinas
    (1,  5),   # Día del Trabajador
    (25, 5),   # Revolución de Mayo
    (20, 6),   # Paso a la Inmortalidad del General Belgrano
    (9,  7),   # Día de la Independencia
    (8,  12),  # Inmaculada Concepción de María
    (25, 12),  # Navidad
]

# Feriados trasladables: si no caen lunes, se trasladan al lunes más cercano
_TRASLADABLES_BASE = [
    (17, 8),   # Paso a la Inmortalidad del General San Martín
    (12, 10),  # Día del Respeto a la Diversidad Cultural
    (20, 11),  # Día de la Soberanía Nacional
]


def _pascua(year: int) -> date:
    """Calcula el Domingo de Pascua (algoritmo de Butcher)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day   = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _lunes_mas_cercano(d: date) -> date:
    """
    Traslada una fecha al lunes más cercano (regla argentina para trasladables):
      - Lunes              → queda igual
      - Martes o Miércoles → lunes anterior
      - Jueves en adelante → lunes siguiente
    """
    dow = d.weekday()   # 0=Lun … 6=Dom
    if dow == 0:
        return d
    if dow <= 2:                     # Martes/Miércoles → lunes anterior
        return d - timedelta(days=dow)
    return d + timedelta(days=7 - dow)   # Jueves…Domingo → lunes siguiente


def fin_de_mes(d: date) -> date:
    """Retorna el último día del mes de la fecha dada."""
    if d.month == 12:
        return date(d.year + 1, 1, 1) - timedelta(days=1)
    return date(d.year, d.month + 1, 1) - timedelta(days=1)


@lru_cache(maxsize=32)
def feriados_del_anio(year: int, extras: tuple = ()) -> frozenset:
    """
    Retorna frozenset de fechas feriadas/inhábiles para el año dado.

    Parameters
    ----------
    year   : año a calcular
    extras : tuple de date objects — feriados extra de la DB (debe ser hashable)
    """
    f: set[date] = set()

    # Fijos
    for dia, mes in _FIJOS:
        f.add(date(year, mes, dia))

    # Trasladables
    for dia, mes in _TRASLADABLES_BASE:
        f.add(_lunes_mas_cercano(date(year, mes, dia)))

    # Semana Santa y Carnaval (calculados desde Pascua)
    pascua = _pascua(year)
    f.add(pascua - timedelta(days=48))  # Lunes de Carnaval
    f.add(pascua - timedelta(days=47))  # Martes de Carnaval
    f.add(pascua - timedelta(days=2))   # Viernes Santo

    # Feria judicial de verano: 15-31 enero
    d = date(year, 1, 15)
    while d.month == 1:
        f.add(d)
        d += timedelta(days=1)

    # Feria judicial de invierno: 1-15 julio
    d = date(year, 7, 1)
    while d.day <= 15:
        f.add(d)
        d += timedelta(days=1)

    # Feriados extra de la DB
    for extra in extras:
        f.add(extra)

    return frozenset(f)


def es_dia_habil(d: date, extras: tuple = ()) -> bool:
    """True si el día es hábil judicial (lun–vie, no feriado, no feria judicial)."""
    if d.weekday() >= 5:   # sábado o domingo
        return False
    return d not in feriados_del_anio(d.year, extras)


def dia_habil_n(fecha_inicio: date, n: int, extras: tuple = ()) -> date:
    """
    Retorna la fecha del día hábil judicial N contando desde el día SIGUIENTE
    a fecha_inicio (día 1 = primer hábil posterior a fecha_inicio).
    """
    count = 0
    d = fecha_inicio + timedelta(days=1)
    while True:
        if es_dia_habil(d, extras):
            count += 1
            if count == n:
                return d
        d += timedelta(days=1)


def contar_dias_habiles(fecha_inicio: date, fecha_fin: date, extras: tuple = ()) -> int:
    """Cuenta los días hábiles judiciales entre dos fechas (ambas inclusive)."""
    count = 0
    d = fecha_inicio
    while d <= fecha_fin:
        if es_dia_habil(d, extras):
            count += 1
        d += timedelta(days=1)
    return count
