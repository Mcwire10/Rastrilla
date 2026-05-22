# RASTRILLA — Documentación técnica

Calculadora de intereses moratorios judiciales contra ANSES (reajuste previsional).  
**Deploy:** `rastrilla-production.up.railway.app` (privado, Railway)  
**Repo:** `https://github.com/Mcwire10/Rastrilla` (privado)  
**Stack:** Python · Streamlit · pdfplumber · python-docx · reportlab · pandas

---

## 1. Doctrina RASTRILLA

Cada diferencia mensual de haber es una obligación independiente.  
Los intereses corren desde el **1° del mes siguiente** al período liquidado.

| Período | Intereses desde |
|---|---|
| 04/2021 | 01/05/2021 |
| 12/2024 | 01/01/2025 |

---

## 2. Algoritmo de cálculo

### Fuente de datos: índice BCRA
- Archivo: `data/diar_ind.xls` (bundleado en el repo, actualizable con botón en la app)
- URL de descarga: `https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/diar_ind.xls`
- Columna usada: col 9 (índice 0-based), datos desde fila 27
- Serie: tasa pasiva acumulada (Ley 27.802, art. 55, Res. 45/26)
- Valores actuales: ~25.500 (acumulado desde 1991)

### Fórmula (BCRA Resolución 45/26)

```
T0  = índice del día ANTERIOR a fecha_desde
Tm  = índice del día de pago (fecha_hasta)

coeficiente = (100 + Tm) / (100 + T0) - 1

interes = capital × coeficiente
total   = capital + interes
```

**T0 es el día anterior a fecha_desde**, no el día mismo. Así lo establece la sección C de la Resolución 45/26: *"T0 es el valor de la serie correspondiente al día anterior a partir del cual se devengan los intereses"*.

### Caso de prueba validado contra calculadora oficial BCRA

| Campo | Valor |
|---|---|
| Capital | $313.665,13 |
| Desde | 01/02/2024 |
| Hasta | 03/03/2026 |
| Tasa acumulada | 94,13% |
| Interés | **$295.240,88** ✓ (coincide al centavo) |

---

## 3. Capital de cada período

```
Capital = Haber Reajustado − Haber Percibido
```

Esta diferencia es la base de intereses para cada mes. **No se usa**:
- La columna `Dif.Neta` (incluye SAC/aguinaldo semestral)
- La columna `Capital` del PDF BlueCorp (incluye HAC y descuenta OS)

---

## 4. Formatos de entrada soportados

| Extensión | Sistema | Capital leído |
|---|---|---|
| `.pdf` | BlueCorp / Ius Asociados | col[3]−col[2] = Reajustado−Percibido |
| `.docx` | Jauregui | col[3]−col[2] = Reajustado−Percibido |
| `.xlsx` / `.xls` | Jauregui | col[Reajustado]−col[Percibido] (detectado por nombre) |
| `.csv` | Estándar | columnas `periodo`, `capital`, `fecha_desde` |

### BlueCorp PDF
- **Página 1:** texto libre con `"calcularon hasta el DD/MM/YYYY"` → fecha sugerida
- **Páginas 2 en adelante:** tabla de datos (sin límite de páginas)
- Columnas: `[0]Mes [1]Año [2]Percibido [3]Reajustado [4]DifImporte [5]Dif% [6]Dif-Deducción [7]HAC [8]OS [9]Difer+HAC-OS [10]Capital [11]Interés`

### Jauregui DOCX
- Tabla principal → fila 78 → tabla anidada (`<w:tbl>`)
- Columnas: `[0]Mes [1]Año [2]Percibido [3]Reajustado [4]Tope [5]%Conf [6]LuegoTope [7]Difer. [8]SAC [9]Subtotal [10]OS [11]DifNeta [12]Intereses [13]Total [14]Texto`

### Jauregui Excel
- Fila 0: encabezados. Primera celda = `"Mes"`
- Columnas relevantes detectadas por nombre: `Percibido` y `Reajustado`
- Fallback: columna `Difer.` o `Dif.Neta` si no existen los nombres anteriores
- La última fila suele ser un total con el mismo período → se descarta por deduplicación

---

## 5. Flujo de la aplicación

```
1. Cargar datos
   └─ Importar archivo (PDF / DOCX / Excel / CSV)
      └─ parsear_archivo() detecta formato y extrae períodos
   └─ O cargar manualmente en la tabla editable

2. Configurar fecha hasta
   └─ Ingresada por el usuario (única para toda la liquidación)
   └─ Pre-llenada desde el documento si tiene fecha sugerida

3. Auto-completar fechas desde (botón)
   └─ 1° del mes siguiente al período (Doctrina RASTRILLA)

4. Calcular
   └─ calcular_intereses(df, indice)
   └─ Para cada fila: T0 = índice[fecha_desde - 1 día], Tm = índice[fecha_hasta]

5. Ver resultados
   └─ Tabla con: período, índice T0, índice Tm, coeficiente, interés, total
   └─ Métricas: capital total, intereses totales, total general

6. Exportar
   └─ Excel (openpyxl)
   └─ PDF judicial landscape A4 (reportlab)
```

---

## 6. Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `app.py` | UI Streamlit completa |
| `calculos.py` | Motor de cálculo puro (sin UI) |
| `bcra.py` | Carga y descarga del índice BCRA |
| `parsear_pdf.py` | Parsers por formato: BlueCorp, Jauregui DOCX, Excel/CSV |
| `exportar.py` | Exportación Excel y PDF judicial |
| `data/diar_ind.xls` | Serie BCRA bundleada (actualizable) |
| `railway.json` | Configuración de deploy Railway |
| `requirements.txt` | Dependencias Python |

---

## 7. Deploy

### Railway (producción)
```json
// railway.json
{
  "deploy": {
    "startCommand": "streamlit run app.py --server.port $PORT --server.headless true --server.address 0.0.0.0"
  }
}
```
- Autodeploy desde `master` en GitHub
- El índice BCRA bundleado se usa en producción
- El índice actualizado **no persiste** entre reinicios (filesystem efímero de Railway)
- Para persistir actualizaciones del índice: usar Railway Volumes (opcional, no implementado)

### Ramas
| Rama | Uso |
|---|---|
| `master` | Producción (Railway autodeploy) |
| `dev` | Desarrollo activo |

---

## 8. Dependencias

```
streamlit>=1.28
pandas>=2.0
openpyxl>=3.1
xlrd>=2.0
reportlab>=4.0
requests>=2.28
pdfplumber>=0.10
python-docx>=1.1
```

---

## 9. Historial de decisiones técnicas

### Fórmula de cálculo (BCRA Res. 45/26)
La fórmula correcta es `(100 + Tm) / (100 + T0) - 1`, no `Tm / T0 - 1`.  
La diferencia es pequeña (los valores del índice ~25.000 >> 100) pero la fórmula es la oficial.  
Más importante: **T0 debe ser el día anterior** a fecha_desde (no el día mismo).  
Para el caso de prueba ($313k, Feb 2024 → Mar 2026), el error de la fórmula vieja era +$1.098,17.

### Capital = Reajustado − Percibido
Las planillas tienen varias columnas similares:
- `Dif.Neta` / `Capital` del PDF: incluye el SAC semestral → **incorrecto para intereses mensuales**
- `Difer.` del DOCX/Excel y `Diferencia - Deducción` del PDF: equivalen a Reajustado − Percibido → **correcto**

### Multi-página BlueCorp
El parser original solo leía la página 2. Si la liquidación tiene muchos períodos y el PDF tiene más de 2 páginas, se perdían datos. Ahora itera sobre todas las páginas desde la 2 en adelante.

### Deduplicación por período
Jauregui agrega una fila de totales con el mismo Mes/Año que el último período real. Se descarta comparando el período con un `set` de períodos ya vistos.
