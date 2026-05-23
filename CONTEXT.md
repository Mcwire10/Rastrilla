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

---

## 2. Estructura de archivos

```
rastrilla/
├── app.py                    # Router: auth guard + st.navigation() + sidebar global
├── auth.py                   # Auth + CRUD usuarios/abogados/expedientes (SQLite)
├── estilo.py                 # CSS global inyectado con st.markdown()
├── bcra.py                   # Carga/descarga del índice BCRA (diar_ind.xls)
├── calculos.py               # Motor de cálculo puro (sin UI)
├── parsear_pdf.py            # Parsers: BlueCorp PDF, Jauregui DOCX/Excel/CSV
├── exportar.py               # Exportación Excel (.xlsx) y PDF (reportlab)
├── pages/
│   ├── home.py               # Pantalla principal: 3 cards de calculadoras
│   ├── ampliacion.py         # Calculadora: Ampliación de Ejecución (multi-período)
│   ├── intereses_cobro.py    # Calculadora: Intereses Aprobados hasta Cobro
│   └── admin.py              # Panel admin: usuarios + suscripciones + letrados
├── data/
│   └── diar_ind.xls          # Índice BCRA (diario, actualizable desde la app)
├── .streamlit/
│   └── config.toml           # theme.primaryColor = "#16a34a", base = "light"
├── requirements.txt
├── DOCUMENTACION.md          # Docs técnica interna
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
.calc-card-badge     → pill "Próximamente" gris uppercase

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
    dia_pago          INTEGER NOT NULL DEFAULT 1,  -- día del mes acordado (1-10)
    fecha_ultimo_pago TEXT,                    -- ISO date último pago
    bloqueado         INTEGER NOT NULL DEFAULT 0   -- 0|1
)
```

Cuentas por defecto (se crean si no existen):
- `admin` / `Admin2025!` / rol: admin
- `testuser` / `Test2025` / rol: cliente

### Tabla `abogados`
```sql
CREATE TABLE abogados (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo  TEXT    NOT NULL,         -- en MAYÚSCULAS
    cuil             TEXT    NOT NULL UNIQUE,
    activo           INTEGER NOT NULL DEFAULT 1  -- 0|1
)
```

Registros por defecto:
- `GONZALEZ PONDAL JUAN MANUEL` · CUIL `20/26436117/7`
- `MOYANO MATIAS ISMAEL` · CUIL `23-38001381-9`

### Tabla `expedientes` (log de cálculos)
```sql
CREATE TABLE expedientes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo          TEXT    NOT NULL,   -- 'ampliacion' | 'cobro' | 'ejecucion'
    letrado_id    INTEGER,            -- FK → abogados.id
    expediente    TEXT,               -- número de expediente
    caratula      TEXT,
    capital_total REAL,
    interes_total REAL,
    total         REAL,
    fecha_calculo TEXT    NOT NULL    -- ISO date
)
```

### Funciones en `auth.py`
```python
# Usuarios
get_user(username)            → dict | None
list_users()                  → list[dict]
create_user(username, password, nombre, rol, dia_pago)
set_bloqueado(username, bool)
registrar_pago(username)       # actualiza fecha_ultimo_pago + desbloquea

# Abogados
list_abogados()               → list[dict]  # solo activos
create_abogado(nombre, cuil)
set_abogado_activo(id, bool)

# Expedientes
log_calculo(tipo, letrado_id, expediente, caratula, capital_total, interes_total, total)

# Auth
login(username, password)     → 'ok' | 'no_user' | 'bad_pass' | 'bloqueado'
logout()
get_session_user()            → dict | None  (lee st.session_state["usuario"])
render_login()                # UI del login split-screen
init_db()                     # crea tablas + inserta defaults
```

Auto-bloqueo: si `hoy.day > 10` y `fecha_ultimo_pago < primer día del mes actual` → bloquea al intentar login.

---

## 6. Navegación (app.py)

```python
# app.py — estructura completa
st.set_page_config(page_title="Intereses Moratorios · Rake", page_icon="⚖️", layout="wide")
init_db()
aplicar_estilos()

usuario = get_session_user()
if usuario is None:
    render_login()
    st.stop()

home            = st.Page("pages/home.py",             title="Inicio",                  default=True)
ampliacion      = st.Page("pages/ampliacion.py",       title="Ampliación de Ejecución")
intereses_cobro = st.Page("pages/intereses_cobro.py",  title="Intereses hasta Cobro")
pages = [home, ampliacion, intereses_cobro]

if usuario["rol"] == "admin":
    pages.append(st.Page("pages/admin.py", title="Admin"))

pg = st.navigation(pages, position="hidden")

with st.sidebar:
    st.page_link("pages/home.py", label="Rake", icon="⚖️")  # logo clickeable

pg.run()

with st.sidebar:
    st.divider()
    if usuario["rol"] == "admin":
        if st.button("🔧 Administración", key="btn_admin", use_container_width=True):
            st.switch_page("pages/admin.py")
    if st.button("🏠 Inicio", key="btn_home", use_container_width=True):
        st.switch_page("pages/home.py")
    st.divider()
    nombre_corto = usuario["nombre"].split()[0]
    st.caption(f"👤 {nombre_corto} · {usuario['rol']}")
    if st.button("Cerrar sesión", key="btn_logout", use_container_width=True):
        logout()
```

---

## 7. Pantalla principal (home.py)

Tres columnas con cards HTML. Cards 1 y 3 tienen botón `▶ Iniciar`, card 2 (Ejecución) tiene badge "Próximamente":

```python
col1, col2, col3 = st.columns(3, gap="large")
# col1: 📋 Ejecución de Sentencia → badge "Próximamente" (Sprint 3)
# col2: 📎 Ampliación de Ejecución → st.button → st.switch_page("pages/ampliacion.py")
# col3: 💰 Intereses Aprobados hasta Cobro → st.button → st.switch_page("pages/intereses_cobro.py")
```

Cuando Ejecución esté lista: eliminar el badge y agregar el botón igual que las otras dos.

---

## 8. Algoritmo de cálculo — FÓRMULA DEFINITIVA (validada al centavo vs CM CABA)

### Índice BCRA
- Archivo: `data/diar_ind.xls`
- URL: `https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/diar_ind.xls`
- Lectura: `pd.read_excel(path, sheet_name=0, header=None)` → `iloc[27:, [0, 9]]`
- Columnas resultado: `["fecha", "indice"]` — fechas diarias, valores acumulados (~3.000 en 2021 → ~25.000 en 2026)
- `cargar_indice()` → `pd.Series` con DatetimeIndex, ordenado por fecha
- Lookup: `indice.asof(pd.Timestamp(fecha))` → último valor conocido ≤ fecha

### Fórmula universal (BCRA CM 14290 / Res. 45/26)

```
coeficiente = (100 + Tₘ) / (100 + T₀) - 1
interés     = capital × coeficiente
total       = capital + interés
```

**⚠️ ADVERTENCIA CRÍTICA:** La fórmula es `(100+Tₘ)/(100+T₀)-1`, **NO** `Tₘ/T₀-1`.
Aunque los valores del índice son grandes (~19.000), la metodología BCRA prescribe esta fórmula.
Cambiarla a `Tₘ/T₀-1` produce errores sistemáticos que solo se detectan con capitales grandes o fechas lejanas.

### Regla de T₀ para cada calculadora

**Ampliación de Ejecución** (`calcular_fila`):
```python
t0_fecha    = pd.Timestamp(fecha_desde) - pd.Timedelta(days=1)
idx_inicial = indice.asof(t0_fecha)
idx_final   = indice.asof(pd.Timestamp(fecha_pago))
coeficiente = (100 + float(idx_final)) / (100 + float(idx_inicial)) - 1
```
- `fecha_desde` = 1° del mes siguiente al período (ej: período 04/2021 → fecha_desde 01/05/2021)
- T₀ = índice del **30/04/2021** (día anterior)

**Intereses Aprobados hasta Cobro** (`calcular_interes_simple`):
```python
t0_fecha    = pd.Timestamp(fecha_aprobacion) - pd.Timedelta(days=1)
idx_inicial = indice.asof(t0_fecha)
idx_final   = indice.asof(pd.Timestamp(fecha_cobro))
coeficiente = (100 + float(idx_final)) / (100 + float(idx_inicial)) - 1
```
- T₀ = índice del día **anterior** a la aprobación judicial

### Casos de validación (al centavo contra CM CABA, 23/05/2026)

| Capital | Aprobación | Cobro | T₀ fecha | T₀ valor | Tₘ valor | Coef | Interés |
|---|---|---|---|---|---|---|---|
| $15.000.028 | 01/05/2025 | 21/05/2026 | 30/04/2025 | 19.365,4179 | 25.594,1825 | 31,9991% | **$4.799.878,63** |
| $15.000.105,32 | 01/05/2023 | 21/05/2026 | 30/04/2023 | 6.685,5555 | 25.594,1825 | 278,6600% | **$41.799.289,16** |

---

## 9. Motor de cálculo (`calculos.py`)

```python
def primer_dia_mes_siguiente(periodo: str) -> date:
    """'04/2021' → date(2021, 5, 1)"""

def calcular_fila(capital, fecha_desde, fecha_pago, indice) -> dict:
    """Una fila de Ampliación. T0 = fecha_desde - 1 día."""
    # Retorna: indice_inicial, indice_final, coeficiente, interes, total, error

def calcular_interes_simple(capital, fecha_aprobacion, fecha_cobro, indice) -> dict:
    """Intereses hasta Cobro. T0 = fecha_aprobacion - 1 día."""
    # Retorna: capital, fecha_t0, fecha_desde (=aprobacion), fecha_hasta (=cobro),
    #          indice_inicial, indice_final, coeficiente, interes, total

def calcular_intereses(df, indice) -> pd.DataFrame:
    """Itera filas del df llamando a calcular_fila(). df necesita:
    periodo, capital, fecha_desde, fecha_pago"""
```

---

## 10. Calculadora Ampliación de Ejecución (`pages/ampliacion.py`)

### Flujo (en orden visual)
1. **Sidebar**: índice BCRA con `@st.cache_resource` + botón actualizar
2. **Título**: `📎 Ampliación de Ejecución`
3. **Paso 1 — Letrado**: `st.selectbox` con `list_abogados()`, formato: `"NOMBRE — CUIL X"`
4. **Paso 2 — Expediente**: `st.text_area` copy-paste del sistema judicial.
   Parser: cada línea se divide por primer `:` con `.partition(":")`.
   Claves usadas: `Expediente`, `Carátula`/`Caratula`, `Jurisdicción`/`Jurisdiccion`, `Sit. Actual`
5. **Paso 3 — Planilla**:
   - `st.file_uploader` (PDF BlueCorp · DOCX Jauregui · Excel · CSV)
   - Al importar: si el archivo trae `fecha_pago`, se guarda en `st.session_state.amp_fecha_pago`
   - Botón `🔄 Auto-fechas`: llena `fecha_desde` = `primer_dia_mes_siguiente(periodo)` para cada fila
   - `st.data_editor` editable (columnas: periodo, capital, fecha_desde)
   - **Fecha efectiva de pago** (`st.date_input`) — va DESPUÉS de la tabla
6. **Calcular**: `calcular_intereses(df, indice)` → `st.session_state["amp_resultado"]`
7. **Resultado**: tabla + 3 métricas (capital · intereses · total)
8. **Exportar**: 2 columnas — Excel (`exportar_excel(df_ok)`) | PDF (`exportar_pdf(df_ok)`)

### Session state keys
- `amp_filas`: DataFrame en tabla
- `amp_resultado`: resultado del cálculo
- `amp_fecha_pago`: date, default = `date.today()`

---

## 11. Calculadora Intereses hasta Cobro (`pages/intereses_cobro.py`)

### Flujo (en orden visual)
1. **Sidebar**: índice BCRA (idéntico a ampliacion)
2. **Título**: `💰 Intereses Aprobados hasta Cobro`
3. **Paso 1 — Letrado**: igual que ampliacion
4. **Paso 2 — Expediente**: igual que ampliacion
5. **Paso 3 — Datos**:
   - `capital`: `st.number_input` (float, min 0.01)
   - `fecha_aprobacion`: `st.date_input` (DD/MM/YYYY)
   - `fecha_cobro`: `st.date_input` (DD/MM/YYYY)
6. **Calcular**: `calcular_interes_simple(capital, fecha_aprobacion, fecha_cobro, indice)`
7. **Resultado**:
   - 3 métricas: Capital aprobado · Intereses moratorios · Total
   - Expander "Detalle": fecha_t0 (día anterior a aprobación), fecha_hasta, T₀, Tₘ, coeficiente
8. **Exportar**: 2 columnas
   - Excel: DataFrame custom con letrado, CUIL, carátula, expediente, todos los índices
   - PDF: fila única compatible con `exportar_pdf()`, periodo = `"Aprobado DD/MM/YYYY"`

### Session state
- `resultado_cobro`: dict resultado

---

## 12. Formatos de entrada (parsear_pdf.py)

```python
parsear_archivo(file, filename) → (pd.DataFrame, str)  # dispatcher
```

| Extensión | Sistema detectado | Capital |
|---|---|---|
| `.pdf` con "bluecorp" en pág 1 | BlueCorp | `col[3] - col[2]` (Reajustado − Percibido) |
| `.pdf` sin "bluecorp" | Jauregui PDF | `col[3] - col[2]` |
| `.docx` | Jauregui DOCX | tabla anidada fila 78, `col[3] - col[2]` |
| `.xlsx`/`.xls` | Jauregui Excel | columnas Reajustado − Percibido (por nombre) |
| `.csv` | Estándar | columnas: periodo, capital, fecha_desde, fecha_pago |

**Capital correcto**: siempre `Haber Reajustado − Haber Percibido`. 
**NO usar** `Dif.Neta` (incluye SAC) ni la columna `Capital` del BlueCorp (incluye HAC, descuenta OS).

BlueCorp pág 1: extrae `fecha_pago` del texto `"calcularon hasta el DD/MM/YYYY"`.
El DataFrame resultante siempre tiene: `periodo (str)`, `capital (float)`, `fecha_desde (date)`, `fecha_pago (date|None)`.

---

## 13. Exportación (exportar.py)

```python
exportar_excel(df) → bytes   # openpyxl, sheet "Liquidación"
# df necesita: periodo, capital, fecha_desde(Timestamp), fecha_pago(Timestamp),
#              indice_inicial, indice_final, coeficiente, interes, total

exportar_pdf(df, titulo=...) → bytes  # reportlab, A4 landscape
# mismo df, título opcional
# headers: Mes/Año | Int. desde | Dif. neta | Índ. inicial | Índ. final | Coeficiente | Interés moratorio | Total
# Última fila: TOTAL GENERAL en amarillo
```

---

## 14. Panel de administración (pages/admin.py)

Guard doble: router no registra la página para clientes + `if usuario["rol"] != "admin": st.stop()`.

### Sección Usuarios
- Lista todos los usuarios con estado de suscripción
- Estado: ✅ Al día / 🟠 Vencido (si hoy.day > 10 y no pagó) / 🔴 Bloqueado / ⚠️ Sin pago
- Botones: 💰 Marcar pagado · 🔒 Bloquear / 🔓 Desbloquear
- Métricas resumen: total · al día · vencidos · bloqueados
- Form alta de usuario: username, password, nombre, rol, dia_pago

### Sección Letrados
```python
def _list_abogados_all():  # definida en admin.py, lista activos + inactivos
    from auth import _conn
    with _conn() as c:
        rows = c.execute("SELECT * FROM abogados ORDER BY nombre_completo").fetchall()
        return [dict(r) for r in rows]
```
- Toggle ✅ Activar / 🔴 Desactivar por letrado
- Form agregar: nombre_completo (se convierte a .upper()), cuil

---

## 15. Deploy (Railway)

```json
{
  "deploy": {
    "startCommand": "streamlit run app.py --server.port $PORT --server.headless true --server.address 0.0.0.0"
  }
}
```

Variable de entorno: `DB_PATH=/data/rastrilla.db`
Volume Railway: montado en `/data` → persiste `rastrilla.db`.

**Nota índice BCRA**: `data/diar_ind.xls` vive en el repo (persiste entre deploys). Las actualizaciones desde la app usan el filesystem efímero de Railway y NO persisten. Para persistir actualizaciones: mover a `/data/diar_ind.xls` y ajustar `DATA_PATH` en `bcra.py`.

### Requirements
```
streamlit>=1.36
pandas>=2.0
openpyxl>=3.1
xlrd>=2.0
reportlab>=4.0
requests>=2.28
pdfplumber>=0.10
python-docx>=1.1
```

---

## 16. Estado de sprints

### ✅ Sprint 1 (commit `81bd123`)
- `pages/home.py`: 3 cards (Ampliación e Intereses operativas, Ejecución próximamente)
- `pages/intereses_cobro.py`: calculadora completa capital único
- `auth.py`: tabla `abogados` + CRUD
- `calculos.py`: `calcular_interes_simple()`
- `estilo.py`: clases CSS `.calc-card`

### ✅ Sprint 2 (commit `9b8c30f`)
- `pages/ampliacion.py`: calculadora multi-período completa
- `auth.py`: tabla `expedientes` + `log_calculo()`
- `pages/admin.py`: sección Letrados
- `pages/home.py`: card Ampliación activa con botón
- `pages/calculadora.py`: eliminado (absorbido)

### ✅ Fixes post-Sprint 2
- `a3398c3`: fecha efectiva de pago va después de la tabla en ampliacion.py
- `86253fe`: fórmula definitiva T₀=aprobacion-1día + (100+Tm)/(100+T0)-1 ← **USAR SIEMPRE ESTA**
- `4952570`: exportación PDF en ambas calculadoras

### 🔜 Sprint 3 — Ejecución de Sentencia (NO implementado)
**Archivo a crear:** `pages/ejecucion.py`

Requiere definir con el usuario:
- ¿Qué calcula Tramo A (120 días hábiles) y Tramo B (desde día 121)?
- ¿La tasa BCRA aplica desde el inicio o solo desde el día 121?
- ¿Qué feriados incluir? (nacionales + feria judicial verano/invierno + feriados_extra DB)
- ¿Estructura del wizard (cuántos pasos)?
- Necesita: `calendario_judicial.py` con lógica de días hábiles + tabla `feriados_extra` en DB

### 🔜 Sprint 4 — Generación DOCX + admin feriados (NO implementado)
- Escrito judicial en DOCX (python-docx)
- 2 planillas Excel separadas para Ejecución (Tramo A y Tramo B)
- Panel admin para gestión de feriados
- Mecanismo de actualización anual de feriados

---

## 17. Gotchas críticos — leer antes de tocar el código

### 1. Fórmula del índice BCRA
**Siempre:** `(100 + Tₘ) / (100 + T₀) - 1`. Nunca `Tₘ/T₀-1`.
T₀ = siempre el **día anterior** a la fecha de inicio de intereses.
Esta regla aplica a `calcular_fila()` Y a `calcular_interes_simple()`.

### 2. Material Symbols Rounded (íconos Streamlit)
Streamlit usa CSS ligatures con la fuente Material Symbols Rounded para íconos en `<button>` y `<span>`.
**Nunca** incluir `button` ni `span` en el selector de Outfit. Si se hace, el ícono de colapsar sidebar y el ícono de upload aparecen como texto literal.

### 3. Sidebar: el wildcard `*` rompe cosas
`[data-testid="stSidebar"] * { color: ... }` sobreescribe el SVG del toggle y el tamaño del `<code>` inline.
Usar selectores específicos: `p, span, small, li, label, .stMarkdown, .stCaption`.
Los `<p>` y `<span>` dentro de botones del sidebar heredan `color: #dcfce7` y necesitan sobreescritura explícita:
```css
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span,
[data-testid="stSidebar"] .stButton > button div { color: #052e16 !important; }
```

### 4. st.columns() no colapsa en mobile
`st.columns()` es siempre side-by-side. La responsividad del login se logra con CSS media queries, no con Streamlit.

### 5. st.cache_resource en páginas
`@st.cache_resource` se define dentro del bloque `with st.sidebar:` en cada calculadora. El botón "Actualizar índice" llama a `st.cache_resource.clear()` + `st.rerun()`.

### 6. Capital = Reajustado − Percibido
En todas las planillas (BlueCorp, Jauregui): el capital correcto es la diferencia entre haber reajustado y haber percibido. **No usar** Dif.Neta (incluye SAC) ni la columna "Capital" del BlueCorp.

### 7. Parser de expediente
Usa `.partition(":")` en cada línea para dividir por el **primer** `:`, preservando `:` en los valores.

### 8. IUS — prohibido en el código
El cliente anterior se llamaba "IUS Asociados". Esa palabra **nunca debe aparecer** en ningún archivo del proyecto: ni en comentarios, ni en mensajes de error, ni en strings, ni en documentación.

### 9. Nombre de la app
El nombre público es **Rake**. En contextos legales/técnicos puede aparecer "Doctrina Rastrilla · Vega" (es el nombre del fallo judicial, no de la app).

---

## 18. Convenciones de código

- Cada calculadora tiene su propia instancia de `@st.cache_resource` para el índice BCRA (Streamlit no comparte el cache entre páginas de la misma forma).
- Session state: prefijo por página (`amp_*` para ampliacion, `resultado_cobro` para intereses_cobro).
- Los resultados de `calcular_interes_simple()` se guardan en session state antes de renderizar para evitar recálculos en reruns.
- Validaciones: siempre lista de errores acumulados mostrados juntos, no uno por uno con early return.
- Formato AR de montos: `f"$ {n:,.2f}".replace(",","X").replace(".","," ).replace("X",".")` → `$ 1.234.567,89`
- Fechas en inputs: siempre `format="DD/MM/YYYY"`.

---

## 19. Git log reciente (rama dev)

```
a3398c3  fix: fecha efectiva de pago va despues de la tabla en ampliacion
86253fe  fix: correccion definitiva formula + fecha T0 — validado al centavo vs CM CABA
4952570  feat: agregar exportacion PDF a ambas calculadoras
15a6a28  fix: correccion formula indice BCRA + doc actualizada a Sprint 2
9b8c30f  feat: Sprint 2 — ampliacion.py + tabla expedientes + admin letrados
81bd123  feat: Sprint 1 — home 3 cards + intereses_cobro + tabla abogados
2004862  chore: eliminar todas las menciones de IUS del codebase
8de8a9f  fix: texto invisible en botones del sidebar
```

---

## 20. Próximos pasos sugeridos

Antes de implementar Sprint 3, aclarar con el usuario:
1. **Algoritmo Tramo A / Tramo B**: ¿corren intereses BCRA desde el día 0 o recién desde el día 121?
2. **Feriados**: ¿qué tipos? nacionales + feria judicial verano (2ª quincena enero) + feria invierno (1ª quincena julio) + `feriados_extra` DB
3. **Wizard**: estructura de pasos para ejecucion.py
4. **Outputs Sprint 4**: ¿2 Excel separados (Tramo A / Tramo B) o 1 con 2 hojas? ¿DOCX completo o resumen?
