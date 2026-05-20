import pandas as pd
import requests
from pathlib import Path

BCRA_URL = "https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/diar_ind.xls"
DATA_PATH = Path(__file__).parent / "data" / "diar_ind.xls"


def descargar_indice() -> None:
    r = requests.get(BCRA_URL, timeout=60)
    r.raise_for_status()
    DATA_PATH.parent.mkdir(exist_ok=True)
    DATA_PATH.write_bytes(r.content)


def cargar_indice() -> pd.Series:
    df = pd.read_excel(DATA_PATH, sheet_name=0, header=None)
    datos = df.iloc[27:, [0, 9]].copy()
    datos.columns = ["fecha", "indice"]
    datos = datos.dropna(subset=["indice"])
    datos["fecha"] = pd.to_datetime(datos["fecha"], dayfirst=True, errors="coerce")
    datos = datos.dropna(subset=["fecha"]).set_index("fecha")["indice"]
    return datos.sort_index()


def fecha_ultimo_dato(indice: pd.Series) -> str:
    return indice.index.max().strftime("%d/%m/%Y")
