# RAKE — Documento de contexto completo (handoff)

> Este documento está escrito para que un agente de IA pueda retomar el proyecto
> desde cero sin perder contexto. Incluye arquitectura, código clave, identidad
> visual, algoritmo validado y estado exacto de cada sprint.

---

## 1. Identidad del proyecto

| Campo | Valor |
|---|---|
| **Nombre público** | Rake |
| **Propósito** | Calculadora de intereses moratorios judiciales contra ANSES (reajuste previsional). Doctrina Rastrilla · Vega — Cámara Federal de Apelaciones de Mendoza. |
| **Usuarios** | Estudio jurídico interno. 2 abogados activos (CUIL hardcodeados en DB). |
| **Deploy** | Railway (privado). Rama `main` → producción automática. |
| **Repo** | `https://github.com/Mcwire10/Rastrilla` (privado) |
| **Rama activa** | `dev` — pendiente merge a `main` tras UAT completo |
| **Stack** | Python 3.11 · Streamlit ≥ 1.36 · SQLite · pandas · pdfplumber · python-docx · reportlab · openpyxl |
| **Checkpoint** | `31d014a` — rama `dev` — Sprint 4 + MODs escritos (Calibri, PDF escrito, parseo limpio) |

---

## 2. Estructura de archivos

```
rastrilla/
├── app.py                    # Router: auth guard + st.navigation() + sidebar global
├── auth.py                   # Auth + CRUD usuarios/abogados/expedientes/feriados_extra (SQLite)
├── estilo.py                 # CSS global inyectado con st.markdown()
├── bcra.py                   # Carga/descarga del índice BCRA (diar_ind.xls)
├── calculos.py               # Motor de cálculo puro (sin UI)
├── calendario.py             # Calendario judicial: días hábiles, feriados, ferias
├── parsear_pdf.py            # Parsers: BlueCorp PDF, Jauregui DOCX/Excel/CSV
├── exportar.py               # Exportación Excel (.xlsx), PDF (reportlab) y DOCX (python-docx)
├── pages/
│   ├── home.py               # Pantalla principal: 3 cards de calculadoras (todas activas)
│   ├── ejecucion.py          # Calculadora: Ejecución de Sentencia (Tramo A / Tramo B)
│   ├── ampliacion.py         # Calculadora: Ampliación de Ejecución (multi-período)
│   ├── intereses_cobro.py    # Calculadora: Intereses Aprobados hasta Cobro
│   └── admin.py              # Panel admin: uso de calculadoras + letrados + log errores + cambio pass
├── data/
│   └── diar_ind.xls          # Índice BCRA (diario, actualizable desde la app)
├── .streamlit/
│   └── config.toml           # theme.primaryColor = "#16a34a", base = "light"
├── requirements.txt
└── CONTEXT.md                # Este archivo (handoff para IA)
```

---

## 3. Identidad visual

### Filosofía: taste-skill
```
DESIGN_VARIANCE  = 8   (alto: split-screen login, cards, asimetría)
MOTION_INTENSITY = 6   (fluido: cubic-bezier, fade-up, tactile buttons)
VISUAL_DENSITY   = 4   (respiro: métricas con padding, sin información densa)
```

### Paleta de colores

| Rol | Color | Uso |
|---|---|---|
| Primary | `#16a34a` | Botón primario, focus ring, hover cards |
| Sidebar bg | `#14532d` | Fondo sidebar permanente |
| Sidebar text | `#dcfce7` | Texto general en sidebar |
| Sidebar heading | `#86efac` | Headings uppercase en sidebar |
| Sidebar button bg | `rgba(255,255,255,0.92)` | Botones blancos en sidebar |
| Sidebar button text | `#052e16` | Texto en botones del sidebar |
| Brand panel | `#14532d` | Panel izquierdo del login |
| Brand eyebrow | `#4ade80` | Texto "Sistema de liquidación" |
| Brand name | `#f0fdf4` | Logo "Rake" (5.5rem, -0.05em tracking) |
| Metric bg | `#f0fdf4` | Fondo tarjetas de métrica |
| Metric border | `#bbf7d0` | Borde tarjetas de métrica |
| Card border | `#e5e7eb` | Borde calc-cards en home |
| Card border hover | `#16a34a` | Borde hover calc-cards |

### Tipografía
- **Fuente:** Outfit (Google Fonts). **Inter está prohibido** por taste-skill.
- Importada vía `@import url('https://fonts.googleapis.com/...')` en el CSS.
- **CRÍTICO:** El selector CSS de Outfit NO incluye `button` ni `span`.
  Razón: Streamlit usa Material Symbols Rounded (CSS ligatures) para íconos en esos elementos.
  Si se aplica Outfit a `button`/`span`, el texto "keyboard_double_arrow_left" aparece literal.
  Selector seguro: `body, input, textarea, select, p, li, .stMarkdown`

### Animaciones
- Entry: `fadeUp` 0.45s `cubic-bezier(0.16, 1, 0.3, 1)` en `[data-testid="stMain"]`
- Métricas: stagger cols 1/2/3 con delay 0.05s / 0.12s / 0.19s
- Botones: `translateY(-1px)` hover, `scale(0.98) translateY(1px)` active

### Login split-screen
- Desktop (≥768px): `background: linear-gradient(90deg, #14532d 50%, #f9fafb 50%)`
  - Panel izquierdo: `.login-bg-panel` position fixed, 50vw
  - Columna derecha: formulario de login
- Mobile (<768px): panel se convierte en banner superior (position: relative), columna izquierda oculta, formulario a 100%
- `body:has(.login-bg-panel)` para detectar la pantalla de login y aplicar estilos específicos

### Clases CSS custom en `estilo.py`
```css
/* Home cards */
.calc-card           → card blanca, border #e5e7eb, radius 14px, hover verde
.calc-card-icon      → emoji 2.25rem
.calc-card-title     → 1rem bold #111827
.calc-card-desc      → 0.8rem #6b7280
.calc-card-badge     → pill "Próximamente" gris uppercase (ya no se usa)

/* Login */
.login-bg-panel      → panel fijo izquierda
.login-brand-eyebrow → etiqueta verde claro uppercase
.login-brand-name    → "Rake" enorme
.login-brand-desc    → descripción semitransparente
.login-brand-tag     → tag inferior muy sutil
.login-spacer        → 22vh desktop / 1.5rem mobile
.login-form-area     → wrapper heading formulario
.login-form-heading  → "Bienvenido"
.login-form-sub      → subtítulo gris

/* Ocultar UI de Streamlit */
[data-testid="stMainMenu"] { display: none !important; }
#MainMenu                   { visibility: hidden !important; }
footer                      { visibility: hidden !important; }
```

---

## 4. Configuración Streamlit

```toml
# .streamlit/config.toml
[theme]
base = "light"
primaryColor = "#16a34a"
```

Streamlit ≥ 1.36 requerido para `st.navigation()`, `st.Page()`, `position="hidden"`.

---

## 5. Base de datos (SQLite)

Archivo: `rastrilla.db` (local) o `/data/rastrilla.db` (Railway, via `DB_PATH` env var).

### Tabla `usuarios`
```sql
CREATE TABLE usuarios (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    username          TEXT    UNIQUE NOT NULL,
    password_hash     TEXT    NOT NULL,        -- formato: "salt:sha256(salt+password)"
    rol               TEXT    NOT NULL DEFAULT 'cliente',  -- 'admin' | 'cliente'
    nombre            TEXT    NOT NULL DEFAULT '',
    fecha_contrato    TEXT    NOT NULL,        -- ISO date alta
    dia_pago          INTEGER NOT NULL DEFAULT 1,
    fecha_ultimo_pago TEXT,
    bloqueado         INTEGER NOT NULL DEFAULT 0,
    primer_login      INTEGER NOT NULL DEFAULT 0   -- 1 = forzar cambio de contraseña
)
```

**Usuarios activos:**
| username | contraseña inicial | rol | nombre |
|---|---|---|---|
| `admin` | `Admin2025!` | admin | Administrador |
| `gonzalez` | `Pndl#R4k3J` | cliente | GONZALEZ PONDAL JUAN MANUEL |
| `moyano` | `Myn#R4k3M` | cliente | MOYANO MATIAS ISMAEL |

`gonzalez` y `moyano` tienen `primer_login = 1` → al primer ingreso se les fuerza el cambio de contraseña. Una vez que cambian, `primer_login` queda en 0 definitivamente. Las contraseñas iniciales no se conocen ni se pueden recuperar una vez cambiadas (hash SHA-256 con salt).

### Tabla `abogados`
```sql
CREATE TABLE abogados (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo  TEXT    NOT NULL,         -- en MAYÚSCULAS
    cuil             TEXT    NOT NULL UNIQUE,
    activo           INTEGER NOT NULL DEFAULT 1  -- 0|1
)
```

### Tabla `expedientes` (log de cálculos)
```sql
CREATE TABLE expedientes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo          TEXT    NOT NULL,   -- 'ampliacion' | 'cobro' | 'ejecucion'
    letrado_id    INTEGER,            -- FK → abogados.id
    expediente    TEXT,
    caratula      TEXT,
    capital_total REAL,
    interes_total REAL,
    total         REAL,
    fecha_calculo TEXT    NOT NULL    -- ISO date
)
```

### Tabla `feriados_extra`
```sql
CREATE TABLE feriados_extra (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha       TEXT    NOT NULL UNIQUE,   -- ISO date
    descripcion TEXT    NOT NULL DEFAULT ''
)
```

**Uso**: días inhábiles judiciales adicionales que no forman parte del calendario base
(fijos + trasladables + ferias). Principalmente para **puentes turísticos por decreto anual**.

Ejemplo: para 2024 (Decreto 106/2023): 01/04/2024 y 21/06/2024.
El admin los carga manualmente o con el botón de importación automática desde la API.

### Tabla `errores` (log del sistema)
```sql
CREATE TABLE errores (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp  TEXT    NOT NULL,
    tipo       TEXT    NOT NULL DEFAULT '',
    mensaje    TEXT    NOT NULL,
    traceback  TEXT    NOT NULL DEFAULT '',
    mail_ok    INTEGER NOT NULL DEFAULT 0   -- 1 = mail de alerta enviado
)
```

### Tabla `uso_documentos` (tracking de descargas)
```sql
CREATE TABLE uso_documentos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,              -- ISO datetime "YYYY-MM-DD HH:MM:SS"
    username    TEXT    NOT NULL,
    calculadora TEXT    NOT NULL,              -- 'ejecucion' | 'ampliacion' | 'cobro'
    tipo_doc    TEXT    NOT NULL               -- 'excel' | 'pdf' | 'docx'
)
```

Se registra **cada vez que el usuario hace clic en un botón de descarga** (Excel, PDF o DOCX).
El panel Admin muestra métricas mensuales por usuario y calculadora.

### Funciones en `auth.py`
```python
# Usuarios
get_user(username) → dict | None
change_password(username, new_password)  # actualiza hash + primer_login = 0

# Abogados
list_abogados() → list[dict]  # solo activos
create_abogado(nombre, cuil)
set_abogado_activo(id, bool)

# Expedientes
log_calculo(tipo, letrado_id, expediente, caratula, capital_total, interes_total, total)

# Feriados extra
list_feriados_extra() → list[dict]
add_feriado_extra(fecha: date, descripcion: str)
delete_feriado_extra(feriado_id: int)
importar_puentes_anio(year: int) → list[dict]  # API argentinadatos.com, filtra tipo='puente'

# Errores del sistema
log_error(tipo, mensaje, tb="")   # guarda en DB + envía mail si SMTP configurado
list_errores(limit=50) → list[dict]
clear_errores()

# Uso de calculadoras
log_uso(username, calculadora, tipo_doc)   # silencioso ante errores de DB
get_uso_mensual(meses=12) → dict           # ver estructura abajo

# Auth
login(username, password) → 'ok' | 'no_user' | 'bad_pass'
logout()
get_session_user() → dict | None
render_login()
render_cambio_password()  # pantalla de primer ingreso (mismo diseño split-screen)
init_db()
```

### `get_uso_mensual(meses=12)` → dict

```python
{
  "por_mes_calc":     [{"mes": "2026-05", "calculadora": "ejecucion", "cantidad": 3}, ...],
  "por_usuario":      [{"mes": "2026-05", "username": "gonzalez", "calculadora": ..., "tipo_doc": ..., "cantidad": 2}, ...],
  "resumen_usuarios": [{"username": "gonzalez", "mes": 3, "total": 12}, ...],  # ordenado por total DESC
  "total_mes":        int,   # total documentos en el mes actual
  "total_hist":       int,   # total histórico
  "top_usuario":      str,   # "gonzalez (12)"
}
```

Constantes exportadas:
- `_CALC_LABELS = {"ejecucion": "Ejecución", "ampliacion": "Ampliación", "cobro": "Hasta Cobro"}`
- `_DOC_LABELS  = {"excel": "Excel", "pdf": "PDF", "docx": "DOCX"}`

### Importación automática de puentes (`importar_puentes_anio`)

```python
def importar_puentes_anio(year: int) -> list[dict]:
    import requests
    url = f"https://api.argentinadatos.com/v1/feriados/{year}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    # Estructura real de la API: {"fecha": "YYYY-MM-DD", "tipo": "puente", "nombre": "..."}
    puentes = [f for f in resp.json() if f.get("tipo") == "puente"]
    resultado = []
    for p in puentes:
        fecha = date.fromisoformat(p["fecha"])
        desc  = p.get("nombre", "Puente turístico")
        try:
            add_feriado_extra(fecha, desc)
            resultado.append({"fecha": fecha, "descripcion": desc, "nuevo": True})
        except Exception:
            resultado.append({"fecha": fecha, "descripcion": desc, "nuevo": False})
    return resultado
```

### Log de errores y alertas por mail

- `log_error()` se llama desde el `try/except` global en `app.py` que envuelve `pg.run()`
- Requiere variables de entorno en Railway: `SMTP_USER` (Gmail) + `SMTP_PASSWORD` (App Password de Google)
- Sin esas vars el error se guarda en DB pero no se envía mail
- Destinatario fijo: `leandro.moyano7@gmail.com`

---

## 6. Navegación y flujo de auth (app.py)

```python
# 1. Auth guard — muestra login si no hay sesión
usuario = get_session_user()
if usuario is None:
    render_login(); st.stop()

# 2. Primer login — fuerza cambio de contraseña antes de entrar
if usuario.get("primer_login", 0):
    render_cambio_password(); st.stop()

# 3. Navegación normal
home            = st.Page("pages/home.py",             title="Inicio",         default=True)
ejecucion       = st.Page("pages/ejecucion.py",        title="Ejecución de Sentencia")
ampliacion      = st.Page("pages/ampliacion.py",       title="Ampliación de Ejecución")
intereses_cobro = st.Page("pages/intereses_cobro.py",  title="Intereses hasta Cobro")
pages = [home, ejecucion, ampliacion, intereses_cobro]

if usuario["rol"] == "admin":
    pages.append(st.Page("pages/admin.py", title="Admin"))

pg = st.navigation(pages, position="hidden")

# 4. Captura global de errores
try:
    pg.run()
except Exception as _exc:
    log_error(type(_exc).__name__, str(_exc), traceback.format_exc())
    st.error("⚠️ Ocurrió un error inesperado. El equipo fue notificado automáticamente.")
    with st.expander("Detalle del error"):
        st.code(traceback.format_exc())
```

---

## 7. Pantalla principal (home.py)

Tres columnas con cards HTML. Las tres tienen botón `▶ Iniciar`:
- col1: `📋 Ejecución de Sentencia` → `st.switch_page("pages/ejecucion.py")`
- col2: `📎 Ampliación de Ejecución` → `st.switch_page("pages/ampliacion.py")`
- col3: `💰 Intereses Aprobados hasta Cobro` → `st.switch_page("pages/intereses_cobro.py")`

---

## 8. Algoritmo de cálculo — FÓRMULA DEFINITIVA (validada al centavo vs CM CABA)

### Índice BCRA
- Archivo: `data/diar_ind.xls`
- URL: `https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/diar_ind.xls`
- Lectura: `pd.read_excel(path, sheet_name=0, header=None)` → `iloc[27:, [0, 9]]`
- `cargar_indice()` → `pd.Series` con DatetimeIndex ordenado
- Lookup: `indice.asof(pd.Timestamp(fecha))` → último valor ≤ fecha

### Fórmula universal (BCRA CM 14290 / Res. 45/26)

```
coeficiente = (100 + Tₘ) / (100 + T₀) - 1
interés     = capital × coeficiente
total       = capital + interés
```

**⚠️ CRÍTICO:** La fórmula es `(100+Tₘ)/(100+T₀)-1`, **NUNCA** `Tₘ/T₀-1`.

### Regla de T₀

| Calculadora | T₀ |
|---|---|
| Ampliación (`calcular_fila`) | índice del día **anterior** a `fecha_desde` |
| Intereses hasta Cobro (`calcular_interes_simple`) | índice del día **anterior** a `fecha_aprobacion` |
| Ejecución Tramo A (`calcular_fila`) | índice del `dia_120` (= día 121 − 1) |
| Ejecución Tramo B (`calcular_intereses`) | igual a Ampliación |

### Casos de validación (al centavo contra CM CABA)

| Capital | Aprobación | Cobro | T₀ fecha | Interés |
|---|---|---|---|---|
| $15.000.028 | 01/05/2025 | 21/05/2026 | 30/04/2025 | **$4.799.878,63** |
| $15.000.105,32 | 01/05/2023 | 21/05/2026 | 30/04/2023 | **$41.799.289,16** |

---

## 9. Calendario judicial (`calendario.py`)

### Feriados incluidos (hardcodeados)

**Fijos (día/mes):**
- 01/01 Año Nuevo · 02/04 Malvinas · 01/05 Trabajador · 25/05 Revolución
- **17/06 Güemes (Ley 26.813)** · 20/06 Belgrano · 09/07 Independencia
- 08/12 Inmaculada · 25/12 Navidad

**Trasladables** (al lunes más cercano, regla argentina):
- 17/08 San Martín · 12/10 Diversidad Cultural · 20/11 Soberanía Nacional
- Regla: lun=queda, mar/mié=lunes anterior, jue/vie/sáb/dom=lunes siguiente

**Móviles (calculados desde Pascua):**
- Lunes Carnaval (Pascua − 48d) · Martes Carnaval (Pascua − 47d)
- **Jueves Santo (Pascua − 3d)** · Viernes Santo (Pascua − 2d)
- Algoritmo de Pascua: Butcher (implementado en `_pascua(year)`)

**Ferias judiciales (fuero federal CSJN):**
- Verano: **01-31 enero** (todo enero completo)
- Invierno: **15-31 julio** (segunda quincena)

**Feriados extra:** tabla DB `feriados_extra` → pasados como `tuple[date]` al llamar las funciones.

### ⚠️ Puentes turísticos (decreto anual)
Los puentes establecidos por decreto cada año (ej: Decreto 106/2023 para 2024: 01/04 y 21/06)
**NO están hardcodeados**. El admin debe cargarlos en `feriados_extra` al inicio de cada año
(manualmente o con el botón de importación desde la API en el panel Admin).

### Caso de validación del calendario
```
Inicio: 29/11/2023
Extras: (01/04/2024, 21/06/2024)   ← puentes Decreto 106/2023
Día 120 esperado:  03/07/2024  ✓
Día 121 esperado:  04/07/2024  ✓  (= dia_120 + 1 día calendario, NO hábil siguiente)
```
Sin los puentes extra: día 120 = 01/07/2024 (2 días antes).

### API de `calendario.py`
```python
feriados_del_anio(year, extras=()) → frozenset[date]  # lru_cache(32)
es_dia_habil(d, extras=()) → bool
dia_habil_n(fecha_inicio, n, extras=()) → date   # N-ésimo hábil POSTERIOR a fecha_inicio
contar_dias_habiles(fecha_inicio, fecha_fin, extras=()) → int
fin_de_mes(d) → date
```

---

## 10. Motor de cálculo (`calculos.py`)

```python
def primer_dia_mes_siguiente(periodo: str) -> date:
    """'04/2021' → date(2021, 5, 1)"""

def calcular_fila(capital, fecha_desde, fecha_pago, indice) -> dict:
    """T0 = fecha_desde - 1 día. Retorna: indice_inicial, indice_final,
    coeficiente, interes, total, error"""

def calcular_interes_simple(capital, fecha_aprobacion, fecha_cobro, indice) -> dict:
    """T0 = fecha_aprobacion - 1 día. Retorna: capital, fecha_t0, fecha_desde,
    fecha_hasta, indice_inicial, indice_final, coeficiente, interes, total"""

def calcular_intereses(df, indice) -> pd.DataFrame:
    """Itera filas del df con calcular_fila(). Columnas requeridas:
    periodo, capital, fecha_desde, fecha_pago"""

def calcular_ejecucion(df_planilla, fecha_devolucion, fecha_hasta, indice,
                       feriados_extra=()) -> dict:
    """
    Retorna:
      dia_120, dia_121          : date
      fecha_devolucion, fecha_hasta : date
      filas_a                   : list[dict] — {periodo, capital, fecha_desde}
      capital_a_total           : float
      resultado_a               : dict (de calcular_fila) o {'error': str}
      resultado_b               : pd.DataFrame (de calcular_intereses)
    """
```

### Algoritmo `calcular_ejecucion` — reglas definitivas

```python
dia_120 = dia_habil_n(fecha_devolucion, 120, feriados_extra)
dia_121 = dia_120 + timedelta(days=1)  # ← SIEMPRE día calendario siguiente, NO hábil siguiente

for cada fila en df_planilla:
    periodo = str(row["periodo"])  # "MM/AAAA"

    # El split se basa en el MES DEL PERÍODO (MM/AAAA), NO en fecha_desde
    mes_p, anio_p = int(periodo[:2]), int(periodo[3:])
    inicio_periodo = date(anio_p, mes_p, 1)          # 1° del mes del período
    fin_periodo    = fin_de_mes(inicio_periodo)        # último día del mes del período

    if inicio_periodo > dia_120:
        # El período empieza después del día 120 → todo Tramo B
        capital_a, capital_b = 0.0, capital
    elif fin_periodo <= dia_120:
        # El período termina en o antes del día 120 → todo Tramo A
        capital_a, capital_b = capital, 0.0
    else:
        # Día 120 cae dentro del mes del período → split proporcional
        dias_en_a    = (dia_120 - inicio_periodo).days + 1
        dias_totales = (fin_periodo - inicio_periodo).days + 1
        capital_a = round(capital * dias_en_a / dias_totales, 2)
        capital_b = round(capital - capital_a, 2)

# Tramo A: calcular_fila(capital_a_total, dia_121, fecha_hasta, indice)
#          → T0 = dia_121 - 1 = dia_120 ✓
# Tramo B: calcular_intereses(df_b, indice)
#          con fecha_pago = fecha_hasta para todas las filas
#          fecha_desde en Tramo B = fecha_desde original de cada fila
```

**⚠️ CRÍTICO — Split proporcional:** La proporción se calcula sobre el mes del campo
`periodo` (MM/AAAA), **no** sobre el mes de `fecha_desde`. Ambos suelen diferir en un mes.

---

## 11. Calculadora Ejecución de Sentencia (`pages/ejecucion.py`)

### Flujo (en orden visual)
1. **Sidebar**: índice BCRA (idéntico a las demás calculadoras)
2. **Título**: `📋 Ejecución de Sentencia`
3. **Paso 1 — Letrado**
4. **Paso 2 — Expediente**
5. **Paso 3 — Fecha de devolución** + preview en tiempo real de Día 120 / Día 121
6. **Paso 4 — Planilla**: file_uploader + auto-fechas + `st.data_editor`
7. **Paso 5 — Fecha efectiva de pago** ← va DESPUÉS de la planilla, no antes
8. **Botón Calcular**
9. **Resultado**:
   - Info día 120 / día 121
   - Tramo A: tabla de períodos + métrica capital agrupado + cálculo (coeficiente, interés)
   - Tramo B: tabla por período + métricas
   - **Box verde destacado**: "RESULTADO FINAL — Suma intereses moratorios Tramo A + Tramo B"
     con el monto total en tipografía grande, y leyenda "Calculado hasta DD/MM/YYYY —
     efectivo pago conforme recibo que consta en autos"
   - 3 métricas bajo el box: Capital total · Intereses Tramo A · Intereses Tramo B
10. **Exportar**: 3 columnas (Excel 2 hojas | PDF escrito | Word escrito)
    - Nombre PDF/DOCX: `INT1M - {APELLIDO}.pdf / .docx`

### Resultado final — box verde (HTML inline)
```python
st.markdown(f"""
<div style="background:#f0fdf4; border:2px solid #16a34a; border-radius:12px;
            padding:1.5rem 2rem; margin:0.5rem 0 1.5rem 0;">
  <div style="font-size:0.75rem; font-weight:700; color:#16a34a; ...">
    Resultado final — Suma intereses moratorios Tramo A + Tramo B
  </div>
  <div style="font-size:2.2rem; font-weight:700; color:#052e16; line-height:1.1;">
    {fmt_ar(_int_total)}
  </div>
  <div style="margin-top:1rem; font-size:0.85rem; color:#374151;">
    Calculado hasta: <strong>{res['fecha_hasta'].strftime('%d/%m/%Y')}</strong>
    &nbsp;—&nbsp; efectivo pago conforme recibo que consta en autos
  </div>
</div>
""", unsafe_allow_html=True)
```

### Session state (prefijo `eje_`)
- `eje_filas`: DataFrame planilla
- `eje_resultado`: dict resultado de `calcular_ejecucion()`
- `eje_fecha_devolucion`: date | None
- `eje_fecha_hasta`: date (default: `date.today()`)

### Exportación
```python
exportar_excel_ejecucion(resultado) → bytes
# Hoja "Tramo A": tabla de períodos Tramo A + cálculo único Tramo A + resultado final / fecha hasta
# Hoja "Tramo B": tabla de períodos Tramo B (estilo ampliación)

exportar_pdf_ejecucion(resultado, titulo=...) → bytes
# Sección A: tabla períodos + cálculo único
# Sección B: tabla por período
# Al final: tabla RESULTADO FINAL + fecha hasta (header verde oscuro #052e16)
```

---

## 12. Calculadora Ampliación de Ejecución (`pages/ampliacion.py`)

### Flujo
1. Sidebar BCRA · 2. Título · 3. Letrado · 4. Expediente
5. Planilla: file_uploader + auto-fechas + `st.data_editor`
6. **Fecha efectiva de pago** (DESPUÉS de la tabla) ← posición crítica
7. Calcular → `calcular_intereses(df, indice)`
8. Resultado: tabla + 3 métricas
9. Exportar: Excel | PDF

Session state: `amp_filas`, `amp_resultado`, `amp_fecha_pago`

---

## 13. Calculadora Intereses hasta Cobro (`pages/intereses_cobro.py`)

### Flujo
1. Sidebar BCRA · 2. Título · 3. Letrado · 4. Expediente
5. Datos: `capital` + `fecha_aprobacion` + `fecha_cobro`
6. Calcular → `calcular_interes_simple()`
7. Resultado: 3 métricas + expander (T₀=aprobacion-1día, T₀ fecha, Tₘ, coeficiente)
8. Exportar: **2 columnas** (PDF escrito | Word escrito)
   - Nombre de archivo: `INT M - {APELLIDO}.pdf / .docx` donde `apellido = caratula.split(",")[0]`
   - Excel eliminado de esta calculadora

Session state: `resultado_cobro`

---

## 14. Formatos de entrada (`parsear_pdf.py`)

```python
parsear_archivo(file, filename) → (pd.DataFrame, str)
```

| Extensión | Sistema | Capital correcto |
|---|---|---|
| `.pdf` con "bluecorp" | BlueCorp | `Reajustado − Percibido` (col[3] - col[2]) |
| `.pdf` sin "bluecorp" | Jauregui PDF | ídem |
| `.docx` | Jauregui DOCX | tabla anidada fila 78 |
| `.xlsx`/`.xls` | Jauregui Excel | columnas por nombre |
| `.csv` | Estándar | columnas: periodo, capital, fecha_desde, fecha_pago |

**Capital = Haber Reajustado − Haber Percibido. NUNCA Dif.Neta (incluye SAC).**

---

## 15. Exportación (`exportar.py`)

```python
# Ampliación (planilla tabulada)
exportar_excel(df) → bytes
exportar_pdf(df, titulo=...) → bytes

# Ejecución de Sentencia (planilla tabulada para Excel)
exportar_excel_ejecucion(resultado) → bytes   # 2 hojas: Tramo A / Tramo B
exportar_pdf_ejecucion(resultado, titulo=...) → bytes  # NO usado en prod (reemplazado por escrito)

# Escritos judiciales — DOCX
generar_docx_cobro(resultado, letrado, caratula, expediente) → bytes
generar_docx_ejecucion(resultado, letrado, caratula, expediente) → bytes

# Escritos judiciales — PDF (misma estructura que los DOCX, via ReportLab)
generar_pdf_cobro(resultado, letrado, caratula, expediente) → bytes
generar_pdf_ejecucion_escrito(resultado, letrado, caratula, expediente) → bytes

# Helpers de limpieza (aplicados en páginas Y dentro de cada función generadora)
_limpiar_caratula(caratula: str) → str   # elimina "(agregar/quitar...)" y similares
limpiar_expediente(valor: str) → str     # extrae solo SIGLA NUMERO/AÑO (ej: "FMZ 041824/2019")

# Helper interno
_numero_a_palabras(monto: float) → str   # 250000.50 → "DOSCIENTOS CINCUENTA MIL CON 50/100"
```

PDF planilla (exportar_pdf): reportlab, A4 landscape. Header azul `#1e3a5f`, filas alternadas, total en amarillo `#fef3cd`.
PDF escrito (generar_pdf_*): reportlab, A4 portrait, misma estructura que el DOCX.
PDF Ejecución Tramo A: header verde `#2d6a4f`, dato en verde claro `#d8f3dc`.
PDF Resultado final: header verde oscuro `#052e16`, fila dato en verde muy claro `#f0fdf4`.

### Registro de fuentes Calibri para PDF

Al importar `exportar.py` se intenta registrar Calibri desde rutas del sistema:
- Windows: `C:\Windows\Fonts\calibri.ttf` / `calibrib.ttf`
- Linux: `/usr/share/fonts/truetype/msttcorefonts/Calibri.ttf`

Variables de módulo: `_PDF_FONT` / `_PDF_FONT_BOLD` → `"Calibri"` si disponible, `"Helvetica"` como fallback.

### DOCX — `generar_docx_cobro` (Intereses hasta el Cobro)

Basado en `PUNTO 3.pdf` + MODs aplicados. Firma: `(resultado: dict, letrado: dict, caratula: str, expediente: str) → bytes`.

Campos dinámicos del `resultado`:
```python
{"capital", "interes", "total", "fecha_desde", "fecha_hasta", "fecha_t0",
 "indice_inicial", "indice_final", "coeficiente"}
```

Formato y reglas:
- **Fuente**: Calibri 12pt · **Interlineado**: 1.5 en todo el documento
- **Márgenes**: 3cm izq / 2cm der / 2.5cm sup-inf · A4 portrait
- **Título**: "PRACTICA LIQUIDACION – INTERESES" — negrita + subrayado + centrado
- **Carátula**: entre comillas dobles normales `"..."` (no `«»`)
- **"Proveer de conformidad,"**: negrita + centrado
- **"SERÁ JUSTICIA."**: negrita + centrado
- Tabla: `"Table Grid"`, colores via `_docx_shade_cell(cell, "RRGGBB")`
- Monto en palabras **UPPERCASE**: `PESOS DOSCIENTOS MIL ($ 200.000,00)`
- Secciones: I. OBJETO · II. LIQUIDACION PRACTICADA · III. DERECHO · IV. PETITUM
- Limpieza automática: `_limpiar_caratula()` + `limpiar_expediente()` al inicio

### DOCX — `generar_docx_ejecucion` (Ejecución de Sentencia)

Basado en `PUNTO 1.pdf` + MODs aplicados. Misma firma que `generar_docx_cobro`.

Campos dinámicos del `resultado` (estructura de `calcular_ejecucion()`):
```python
{"dia_120", "dia_121", "filas_a", "capital_a_total",
 "resultado_a", "resultado_b", "fecha_hasta"}
```

Formato y reglas:
- **Fuente**: Calibri 12pt · **Interlineado**: 1.5 en todo el documento
- **Título**: "PRACTICA LIQUIDACION DE INTERESES MORATORIOS" — negrita + subrayado + centrado
- **Carátula**: entre comillas dobles normales `"..."` (no `«»`)
- **Sección II título**: `CUMPLIMIENTO... EN FALLO "VEGA" y "RASTRILLA"` (FALLO fuera de comillas)
- **"Proveer de conformidad,"**: centrado (sin negrita — diferencia con cobro)
- **"SERÁ JUSTICIA."**: negrita + centrado
- `dia_120` en negrita en sección II.A · `dia_121` y `fecha_hasta` en negrita en II.B
- Monto en palabras **lowercase** en sección IV: `pesos quinientos mil... ($ 500.000,00)`
- Planilla Tramo A (tabla períodos + cálculo único) + Planilla Tramo B + resultado final
- Secciones: I.- OBJETO · II.- CUMPLIMIENTO · III.- PROCEDENCIA · IV.- PLANILLA · V.- PETITORIO
- Limpieza automática: `_limpiar_caratula()` + `limpiar_expediente()` al inicio

### PDF escritos — `generar_pdf_cobro` y `generar_pdf_ejecucion_escrito`

Generan exactamente el mismo contenido que los DOCX respectivos, usando ReportLab (A4 portrait).
Estructura de párrafos con `ParagraphStyle` — leading=18 (1.5 × 12pt), align=JUSTIFY, sangría 35pt.
Las tablas (planillas) se incluyen inline en el story de ReportLab.
Las páginas usan estas funciones en el botón "Descargar PDF" — **no** la función `exportar_pdf_ejecucion`.

### `limpiar_expediente` — regla de dos capas

```python
def limpiar_expediente(valor: str) -> str:
    """Extrae solo el número de expediente en formato SIGLA NUMERO/AÑO."""
    m = re.search(r"(?:[A-Za-z]{2,5}\s+)?\d+/\d{4}", valor)
    return m.group(0).strip() if m else valor.strip()
```

Aplicado en **2 capas**:
1. **Capa página**: `expediente_num = limpiar_expediente(exp.get("Expediente", ""))` — en las 3 calculadoras (display, log DB, exportación)
2. **Capa generadora**: al inicio de cada función `generar_docx_*` y `generar_pdf_*`, como garantía

Ejemplos:
- `"FMZ 041824/2019 (agregar/quitar a mis expedientes)"` → `"FMZ 041824/2019"` ✓
- `"041824/2019"` → `"041824/2019"` ✓

---

## 16. Sidebar — botones de actualización

Presente en las 3 calculadoras (ejecucion, ampliacion, intereses_cobro). Visible para **todos los usuarios**.

```
Índice BCRA
Com. 14290 · Uso de la Justicia
[Datos hasta: DD/MM/YYYY]
[Actualizar índice BCRA]     ← descarga diar_ind.xls desde BCRA, limpia cache
[Actualizar feriados]        ← importar_puentes_anio(año_actual), muestra cuántos se cargaron
```

---

## 17. Panel de administración (`pages/admin.py`)

Guard doble: router no registra la página para clientes + `if usuario["rol"] != "admin": st.stop()`.

### Secciones (en orden visual)

1. **📊 Uso de calculadoras**
   - 3 métricas globales: Documentos este mes / Total histórico / Más activo
   - Tarjeta por usuario: "este mes: X · total: Y" (una por cada username en `uso_documentos`)
   - Bar chart mensual agrupado por calculadora (últimos 12 meses, `st.bar_chart`)
   - Tabla detalle siempre visible: Mes · Usuario · Calculadora · Tipo · Docs

2. **Letrados**: listar activos+inactivos, toggle activar/desactivar, form agregar nuevo

3. **Log de errores**: lista de errores capturados (timestamp, tipo, mail enviado/no), expander con traceback, botón "Limpiar". Si no hay errores muestra `✅ Sin errores registrados`.

4. **🔑 Cambiar contraseña**: form con 3 campos (actual + nueva + confirmar). Verifica la contraseña actual antes de guardar. Solo cambia la del admin logueado (`usuario["username"]`).

---

## 18. Deploy (Railway)

```json
{"deploy": {"startCommand": "streamlit run app.py --server.port $PORT --server.headless true --server.address 0.0.0.0"}}
```

- `DB_PATH=/data/rastrilla.db` + Volume en `/data`
- `data/diar_ind.xls` vive en el repo (persiste entre deploys). Actualizaciones desde la app se pierden al redeploy — para persistir, mover a `/data/diar_ind.xls` y ajustar `DATA_PATH` en `bcra.py`.

---

## 19. Estado de sprints

### ✅ Sprint 1 (`81bd123`)
- `pages/home.py`, `pages/intereses_cobro.py`, `auth.py` tabla abogados, `calculos.py` calcular_interes_simple

### ✅ Sprint 2 (`9b8c30f`)
- `pages/ampliacion.py`, `auth.py` tabla expedientes + log_calculo, `pages/admin.py` letrados

### ✅ Fixes post-Sprint 2
- `a3398c3`: fecha efectiva de pago va después de la tabla en ampliacion
- `86253fe`: fórmula T₀=día-anterior + `(100+Tm)/(100+T0)-1` — **DEFINITIVA, validada al centavo**
- `4952570`: exportación PDF en ambas calculadoras

### ✅ Sprint 3 (`f96ff77`)
- `calendario.py`: calendario judicial completo
- `auth.py`: tabla `feriados_extra` + CRUD
- `calculos.py`: `calcular_ejecucion()` con split Tramo A/B
- `exportar.py`: `exportar_excel_ejecucion()` + `exportar_pdf_ejecucion()`
- `pages/ejecucion.py`: página completa con preview día 120/121
- `pages/admin.py`: sección feriados extra
- `app.py` + `pages/home.py`: ejecución activa en navegación

### ✅ Fixes post-Sprint 3

**`2eb185d` — Bug crítico calendario (4 errores) + UI:**
1. ❌ Feria verano: era Jan 15-31 → ✅ Jan 1-31 (todo enero, CSJN)
2. ❌ Feria invierno: era Jul 1-15 → ✅ Jul 15-31 (CSJN)
3. ❌ Faltaba 17/06 Güemes (Ley 26.813) en `_FIJOS`
4. ❌ Faltaba Jueves Santo (Pascua−3d)
5. UI: `fecha_hasta` movida al Paso 5 (después de la planilla)

Validado: inicio 29/11/2023 + extras (01/04/2024, 21/06/2024) → día 120 = **03/07/2024 ✓**

**`e268856` — Día 121 + importación de puentes:**
- `dia_121 = dia_120 + timedelta(days=1)` (día calendario, no hábil siguiente)
- `importar_puentes_anio(year)` en `auth.py` vía `api.argentinadatos.com`
- Admin: banner alerta + botón importación + selector año

**`5e28739` — Split proporcional por mes del período:**
- El split se basa en el campo `periodo` (MM/AAAA), no en `fecha_desde`
- `inicio_periodo = date(anio_p, mes_p, 1)`, `fin_periodo = fin_de_mes(inicio_periodo)`

**`186568f` — Ocultar menú hamburguesa de Streamlit:**
- 3 reglas CSS en `estilo.py`: `stMainMenu`, `#MainMenu`, `footer`

**`9ea2ba8` — Resultado final + fecha hasta en Ejecución:**
- Box verde destacado en `ejecucion.py`: suma intereses A+B + fecha efectiva de pago
- `exportar_pdf_ejecucion`: tabla resultado final al pie del PDF
- `exportar_excel_ejecucion`: filas resultado final en hoja "Tramo A"

### ✅ Refactors post-Sprint 3 (rama dev)

**`052d6ff` + `5febaef` — Botón "Actualizar feriados" en sidebar:**
- Movido del panel Admin al sidebar de las 3 calculadoras
- Visible para todos los usuarios (no solo admin)
- Importa puentes del año corriente con un click

**`9d03f00` — Usuarios letrados + log de errores:**
- Usuarios `gonzalez` y `moyano` creados por defecto en `init_db()`
- `testuser` eliminado automáticamente al arrancar
- Tabla `errores` + `log_error()` + `send_error_email()` + `list/clear_errores()`
- Admin simplificado: solo Letrados + Log de errores (sin usuarios/suscripciones)
- `app.py`: captura global de excepciones con `try/except` sobre `pg.run()`

**`90b42c8` — Cambio de contraseña obligatorio en primer ingreso:**
- Columna `primer_login` en tabla `usuarios`
- `render_cambio_password()`: mismo diseño split-screen que login, fuerza nueva contraseña (≥8 chars)
- Tras guardar: session_state actualizado, entra directo a la app sin re-login
- `gonzalez` y `moyano` arrancan con `primer_login = 1`

**`c7aaf1c` — Eliminar sistema de bloqueo/suscripción:**
- Removidos: `set_bloqueado`, `registrar_pago`, `_debe_autobloquear`
- `login()` solo retorna `'ok'` | `'no_user'` | `'bad_pass'`
- Cuentas siempre habilitadas

**`f0b2270` — Fix primer_login para usuarios existentes:**
- La migración `ALTER TABLE` asignaba `DEFAULT 0` a usuarios ya en la DB
- `init_db()` verifica el hash: si coincide con la contraseña por defecto → fuerza `primer_login = 1`
- Una vez que cambian la contraseña, el hash no coincide más → no se vuelve a tocar

### ✅ Sprint 4 — rama `dev` (checkpoint original `65461f3`)

**`7f4a619` → `49aba84` → `65461f3` — Escritos judiciales DOCX:**
- `exportar.py`: `_numero_a_palabras()` para montos en palabras castellano (hasta millones + centavos)
- `exportar.py`: helpers DOCX internos (`_docx_shade_cell`, `_docx_set_col_widths`, `_docx_add_table_header`, `_docx_add_data_row`)
- `exportar.py`: `generar_docx_cobro()` — escrito "Intereses hasta el Cobro" (basado en PUNTO 3.pdf)
- `exportar.py`: `generar_docx_ejecucion()` — escrito "Ejecución de Sentencia" (basado en PUNTO 1.pdf)
- `pages/intereses_cobro.py`: 3ra columna "⬇ Descargar escrito DOCX"
- `pages/ejecucion.py`: 3ra columna "⬇ Descargar escrito DOCX"

**`387e4cd` + `fa5516e` — Panel de uso de calculadoras:**
- `auth.py`: tabla `uso_documentos` en DB + `log_uso()` + `get_uso_mensual()` + constantes `_CALC_LABELS`/`_DOC_LABELS`
- `pages/admin.py`: sección "Uso de calculadoras" con métricas globales, tarjetas por usuario, bar chart y tabla
- Las 3 calculadoras capturan el `True` del `st.download_button` para llamar `log_uso()`

**`d66b999` — Cambio de contraseña del admin:**
- `pages/admin.py`: sección "🔑 Cambiar contraseña" al final del panel (verifica pass actual antes de guardar)

### ✅ MODs escritos judiciales — rama `dev` (checkpoint actual `31d014a`)

**`91770c9` — cobro: MOD PASO #3**
- Carátula entre comillas normales `"..."` (no `«»`)
- Interlineado 1.5 en todo el documento DOCX
- "Proveer de conformidad," en negrita + centrado · "SERÁ JUSTICIA." negrita + centrado
- Exportar cobro: solo **2 columnas** (PDF + Word) — Excel eliminado
- Nombre de archivo: `INT M - {APELLIDO}.pdf / .docx`

**`e37213a` — ejecucion: MOD PASO 1**
- Título con negrita + **subrayado**
- Carátula entre comillas normales `"..."` (no `«»`)
- Sección II: `FALLO "VEGA" y "RASTRILLA"` (FALLO fuera de comillas, solo los fallos van entre comillas)
- Interlineado 1.5 en todo el documento DOCX
- Cierre centrado: "Proveer de conformidad," + "SERÁ JUSTICIA."
- Nombre de archivo: `INT1M - {APELLIDO}.pdf / .docx`

**`022b442` — cobro: tipografía + PDF como escrito**
- Fuente DOCX cambiada de Arial → **Calibri 12pt**
- Nuevo `generar_pdf_cobro()`: PDF con el escrito completo (igual que DOCX), vía ReportLab A4 portrait
- `_limpiar_caratula()` elimina "(agregar/quitar...)" automáticamente

**`af3a506` — ejecucion+cobro: PDF escrito + comillas sección II corregidas**
- Nuevo `generar_pdf_ejecucion_escrito()`: PDF con el escrito completo para ejecución
- Ambos PDFs incluyen planillas inline en el escrito (no reemplazan las tablas con el texto)
- `pages/ejecucion.py`: botón PDF ahora usa `generar_pdf_ejecucion_escrito`
- Sección II corregida definitivamente: `FALLO "VEGA" y "RASTRILLA"`

**`3053030` — parser: `limpiar_expediente`**
- Nueva función `limpiar_expediente(valor)` en `exportar.py`
- Regex `(?:[A-Za-z]{2,5}\s+)?\d+/\d{4}` — extrae solo `SIGLA NUMERO/AÑO`
- Aplicado en las 3 páginas: display, log DB, nombres de archivo

**`31d014a` — exportar: garantía doble en generadoras**
- `limpiar_expediente()` aplicado también dentro de las 4 funciones generadoras
- Las funciones nunca pueden producir un expediente sucio, independientemente de lo que pase en la página

### 🔜 Pendiente
- **DOCX + PDF Ampliación de Ejecución**: no hay ejemplo del usuario todavía
- Merge `dev` → `main` cuando UAT esté completo

---

## 20. Gotchas críticos — leer antes de tocar el código

### 1. Fórmula BCRA
`(100 + Tₘ) / (100 + T₀) - 1`. **NUNCA** `Tₘ/T₀-1`. T₀ = siempre el día **anterior** al inicio de intereses.

### 2. Calendario judicial — períodos de feria
- Verano: **todo enero** (01-31), no solo la segunda quincena.
- Invierno: **15-31 julio**, no los primeros 15 días.
- Güemes (17/06) y Jueves Santo son feriados del calendario base.
- Puentes turísticos: **SIEMPRE** cargar en `feriados_extra` (varían cada año por decreto).

### 3. Día 121 — regla definitiva
`dia_121 = dia_120 + timedelta(days=1)` — día calendario siguiente al 120, sin importar si es hábil.
Es un extremo de interés, no un día de notificación judicial.

### 4. Split proporcional Ejecución
Se calcula sobre el mes del campo `periodo` (MM/AAAA), **no** sobre `fecha_desde`.
`fecha_desde` es el 1° del mes siguiente al período y NO debe usarse para el split.

### 5. Material Symbols / CSS
Nunca aplicar Outfit a `button` ni `span`. Breaks íconos de Streamlit.

### 6. Sidebar wildcard
`[data-testid="stSidebar"] *` rompe SVG del toggle. Usar selectores específicos.

### 7. Capital = Reajustado − Percibido
NUNCA Dif.Neta (incluye SAC) ni la columna "Capital" de BlueCorp.

### 8. Parser expediente
`.partition(":")` en cada línea — preserva `:` en los valores.

### 9. IUS — prohibido en el código
La palabra "IUS" nunca debe aparecer en ningún archivo del proyecto.

### 10. Nombre público
**Rake**. Contexto legal: "Doctrina Rastrilla · Vega" (fallo judicial, no nombre de la app).

### 11. Fecha efectiva de pago — posición en UI
En **ampliacion.py** y **ejecucion.py**: el `st.date_input` de fecha de pago va **SIEMPRE después**
de la tabla editable (`st.data_editor`), no antes.

### 12. lru_cache de calendario
`feriados_del_anio` usa `lru_cache(32)`. El parámetro `extras` debe ser un `tuple` de `date` (hashable).
Convertir siempre: `extras = tuple(date.fromisoformat(f["fecha"]) for f in list_feriados_extra())`.

### 13. API argentinadatos.com — estructura real
Respuesta: `[{"fecha": "YYYY-MM-DD", "tipo": "puente"|"inamovible"|..., "nombre": "..."}]`
Usar `date.fromisoformat(p["fecha"])` y `p.get("nombre", "Puente turístico")`.
**No** asumir campos `dia`, `mes`, `motivo` — esa estructura NO existe.

### 14. primer_login — lógica de migración
`init_db()` corre en cada arranque. Si un usuario tiene `primer_login = 0` pero su hash
coincide con la contraseña por defecto conocida → se fuerza `primer_login = 1`.
Esto garantiza que usuarios creados antes de agregar la columna también pasen por el cambio.
**No agregar esta lógica a usuarios nuevos** — solo aplica a `gonzalez` y `moyano`.

### 15. Sin bloqueo de cuentas
Las cuentas no se bloquean nunca. `login()` no llama a auto-bloqueo ni verifica `bloqueado`.
La columna `bloqueado` sigue en la DB pero es inerte. No reimplementar ese sistema.

### 16. SMTP para alertas de error
Variables de entorno en Railway: `SMTP_USER` + `SMTP_PASSWORD` (Gmail App Password).
Sin ellas el log a DB funciona igual, solo no envía mail. No hardcodear credenciales.

### 17. DOCX — tipografía, espaciado y monto en palabras
- **Fuente**: **Calibri 12pt** en ambos documentos (antes era Arial). Definido en `doc.styles["Normal"].font.name = "Calibri"`.
- **Interlineado 1.5**: `WD_LINE_SPACING.ONE_POINT_FIVE` aplicado párrafo a párrafo vía helper `_ls(p)`. No se aplica a celdas de tabla.
- **Cobro**: monto en **MAYÚSCULAS** (`_numero_a_palabras(monto)`)
- **Ejecución**: monto en **minúsculas** (`_numero_a_palabras(monto).lower()`)

### 18. `log_uso` — no lanza excepciones
`log_uso()` tiene `try/except` que suprime todo error silenciosamente.
Esto es intencional: un fallo de tracking nunca debe romper la descarga del usuario.

### 19. Tablas DOCX — estilo `"Table Grid"` de Word
Las tablas del DOCX usan `tbl.style = "Table Grid"` para que las líneas aparezcan visibles
al abrir en Word/LibreOffice. Sin ese estilo la tabla se ve sin bordes.
Los colores de fondo se aplican con `_docx_shade_cell(cell, "RRGGBB")` (sin #).

### 20. PDF cobro/ejecucion = escrito judicial (no planilla)
Los botones "Descargar PDF" en cobro y ejecucion llaman a **`generar_pdf_cobro`** y **`generar_pdf_ejecucion_escrito`** respectivamente — no a `exportar_pdf` ni a `exportar_pdf_ejecucion`.
Esas funciones "planilla" siguen existiendo pero solo las usa ampliacion.

### 21. Nombres de archivo de escritos
- **Cobro**: `INT M - {APELLIDO}.pdf / .docx` — apellido = `caratula.split(",")[0].strip()`
- **Ejecución**: `INT1M - {APELLIDO}.pdf / .docx` — ídem
- Nunca usar el número de expediente como nombre base en estos documentos.

### 22. Carátula — limpieza obligatoria
`_limpiar_caratula()` elimina `"(agregar/quitar...)"` del campo carátula en todos los escritos.
`limpiar_expediente()` extrae solo `SIGLA NUMERO/AÑO` del campo expediente.
Ambas funciones se aplican en la página (display + log) **y** dentro de cada función generadora (garantía doble).

### 23. "Proveer de conformidad," — negrita en cobro
En `generar_docx_cobro` y `generar_pdf_cobro`: **negrita**. En ejecución: sin negrita (plain text).
Diferencia dictada por los templates originales.

---

## 21. Git log (rama dev)

```
65461f3  Sprint 4: escrito DOCX Ejecucion de Sentencia (documento correcto PUNTO 1.pdf)
49aba84  Mover escrito DOCX de Ejecucion a Intereses hasta el Cobro
d66b999  Admin: seccion para cambiar contrasena propia con verificacion de pass actual
fa5516e  Panel de uso: metricas por usuario + tabla siempre visible
387e4cd  Panel de uso: tracking de documentos generados por calculadora y usuario
7f4a619  Sprint 4: generar escrito judicial DOCX para Ejecucion de Sentencia  ← (asignación inicial incorrecta, reemplazada por 49aba84 + 65461f3)
f0b2270  fix: forzar primer_login=1 para usuarios con contrasena por defecto
c7aaf1c  refactor: eliminar sistema de bloqueo y suscripcion
90b42c8  feat: cambio de contrasena obligatorio en primer ingreso
9d03f00  feat: usuarios letrados + log de errores con alerta por mail
5febaef  fix: boton actualizar feriados visible para todos los usuarios
052d6ff  refactor: mover actualizacion de feriados al sidebar (boton global)
a4e2eff  docs: CONTEXT.md actualizado al cierre de Sprint 3 + todos los fixes
9ea2ba8  feat: resultado final y fecha hasta en calculadora de ejecucion
186568f  fix: ocultar menu hamburguesa de streamlit
5e28739  fix: split proporcional basado en mes del periodo (no en fecha_desde)
e268856  feat: dia 121 como dia calendario + importar puentes desde API
2eb185d  fix: calendario judicial (ferias, Guemes, Jueves Santo) + UI fecha_hasta paso 5
f96ff77  feat: Sprint 3 — Ejecucion de Sentencia (120 dias habiles judiciales)
86253fe  fix: correccion definitiva formula + fecha T0
4952570  feat: agregar exportacion PDF a ambas calculadoras
a3398c3  fix: fecha efectiva de pago va despues de la tabla en ampliacion
9b8c30f  feat: Sprint 2 — ampliacion.py + tabla expedientes + admin letrados
81bd123  feat: Sprint 1 — home 3 cards + intereses_cobro + tabla abogados
```

### ↩️ Cómo volver al checkpoint `65461f3`

Si algo se rompe después de este punto:
```bash
git checkout dev
git log --oneline          # verificar que 65461f3 esté en el log
git reset --hard 65461f3   # ⚠️ destructivo — descarta commits posteriores locales
git push --force origin dev # solo si ya se pushearon commits malos
```

Estado exacto del checkpoint:
- `exportar.py`: contiene `generar_docx_cobro` + `generar_docx_ejecucion` + `_numero_a_palabras` + 4 helpers DOCX
- `auth.py`: tabla `uso_documentos` + `log_uso` + `get_uso_mensual` + `change_password`
- `pages/admin.py`: 4 secciones (uso + letrados + errores + cambio pass)
- `pages/ejecucion.py`: 3 columnas exportar (Excel | PDF | DOCX)
- `pages/intereses_cobro.py`: 3 columnas exportar (Excel | PDF | DOCX)
- `pages/ampliacion.py`: 2 columnas exportar (Excel | PDF) — DOCX pendiente
