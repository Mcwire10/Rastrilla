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
├── auth.py                   # Auth + CRUD usuarios/abogados/expedientes/feriados_extra (SQLite)
├── estilo.py                 # CSS global inyectado con st.markdown()
├── bcra.py                   # Carga/descarga del índice BCRA (diar_ind.xls)
├── calculos.py               # Motor de cálculo puro (sin UI)
├── calendario.py             # Calendario judicial: días hábiles, feriados, ferias
├── parsear_pdf.py            # Parsers: BlueCorp PDF, Jauregui DOCX/Excel/CSV
├── exportar.py               # Exportación Excel (.xlsx) y PDF (reportlab)
├── pages/
│   ├── home.py               # Pantalla principal: 3 cards de calculadoras (todas activas)
│   ├── ejecucion.py          # Calculadora: Ejecución de Sentencia (Tramo A / Tramo B)
│   ├── ampliacion.py         # Calculadora: Ampliación de Ejecución (multi-período)
│   ├── intereses_cobro.py    # Calculadora: Intereses Aprobados hasta Cobro
│   └── admin.py              # Panel admin: usuarios + letrados + feriados_extra
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

Ejemplo: cada 1° de enero el admin debe cargar los puentes del nuevo año.
Para 2024 (Decreto 106/2023): 01/04/2024 y 21/06/2024.

### Funciones en `auth.py`
```python
# Usuarios
get_user(username) → dict | None
list_users() → list[dict]
create_user(username, password, nombre, rol, dia_pago)
set_bloqueado(username, bool)
registrar_pago(username)

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

# Auth
login(username, password) → 'ok' | 'no_user' | 'bad_pass' | 'bloqueado'
logout()
get_session_user() → dict | None
render_login()
init_db()
```

---

## 6. Navegación (app.py)

```python
home            = st.Page("pages/home.py",             title="Inicio",         default=True)
ejecucion       = st.Page("pages/ejecucion.py",        title="Ejecución de Sentencia")
ampliacion      = st.Page("pages/ampliacion.py",       title="Ampliación de Ejecución")
intereses_cobro = st.Page("pages/intereses_cobro.py",  title="Intereses hasta Cobro")
pages = [home, ejecucion, ampliacion, intereses_cobro]

if usuario["rol"] == "admin":
    pages.append(st.Page("pages/admin.py", title="Admin"))

pg = st.navigation(pages, position="hidden")
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
- Verano: **01-31 enero** (todo enero)
- Invierno: **15-31 julio**

**Feriados extra:** tabla DB `feriados_extra` → pasados como `tuple[date]` al llamar las funciones.

### ⚠️ Puentes turísticos (decreto anual)
Los puentes establecidos por decreto cada año (ej: Decreto 106/2023 para 2024: 01/04 y 21/06)
**NO están hardcodeados**. El admin debe cargarlos en `feriados_extra` al inicio de cada año.

### Caso de validación del calendario
```
Inicio: 29/11/2023
Extras: (01/04/2024, 21/06/2024)   ← puentes Decreto 106/2023
Día 120 esperado:  03/07/2024  ✓
Día 121 esperado:  04/07/2024  ✓
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

### Algoritmo `calcular_ejecucion`

```python
dia_120 = dia_habil_n(fecha_devolucion, 120, feriados_extra)
dia_121 = dia_habil_n(fecha_devolucion, 121, feriados_extra)  # = primer hábil post-120

for cada fila en df_planilla:
    fin_mes = fin_de_mes(fecha_desde)

    if fecha_desde > dia_120:
        # Todo Tramo B
    elif fin_mes <= dia_120:
        # Todo Tramo A
    else:
        # Split proporcional (dia_120 cae dentro del mes)
        dias_en_a    = (dia_120 - fecha_desde).days + 1
        dias_totales = (fin_mes - fecha_desde).days + 1
        capital_a    = round(capital * dias_en_a / dias_totales, 2)
        capital_b    = capital - capital_a

# Tramo A: calcular_fila(capital_a_total, dia_121, fecha_hasta, indice)
#          → T0 = dia_121 - 1 = dia_120 ✓
# Tramo B: calcular_intereses(df_b, indice)
#          con fecha_pago = fecha_hasta para todas las filas
```

---

## 11. Calculadora Ejecución de Sentencia (`pages/ejecucion.py`)

### Flujo (en orden visual)
1. **Sidebar**: índice BCRA (idéntico a las demás calculadoras)
2. **Título**: `📋 Ejecución de Sentencia`
3. **Paso 1 — Letrado**
4. **Paso 2 — Expediente**
5. **Paso 3 — Fecha de devolución** + preview en tiempo real de Día 120 / Día 121
6. **Paso 4 — Planilla**: file_uploader + auto-fechas + `st.data_editor`
7. **Paso 5 — Fecha efectiva de pago** (va DESPUÉS de la planilla)
8. **Botón Calcular**
9. **Paso 6 — Resultado**: info día 120/121 · Tramo A (tabla + métricas + expander) · Tramo B (tabla + métricas) · Total general
10. **Paso 7 — Exportar**: 2 columnas (Excel 2 hojas | PDF)

### Session state (prefijo `eje_`)
- `eje_filas`: DataFrame planilla
- `eje_resultado`: dict resultado de `calcular_ejecucion()`
- `eje_fecha_devolucion`: date | None
- `eje_fecha_hasta`: date (default: `date.today()`)

### Exportación
```python
exportar_excel_ejecucion(resultado) → bytes   # 2 hojas: "Tramo A" y "Tramo B"
exportar_pdf_ejecucion(resultado, titulo=...) → bytes  # secciones A y B
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
8. Exportar: Excel detallado | PDF (fila única, `periodo = "Aprobado DD/MM/YYYY"`)

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
# Ampliación / Intereses hasta Cobro
exportar_excel(df) → bytes
exportar_pdf(df, titulo=...) → bytes

# Ejecución de Sentencia
exportar_excel_ejecucion(resultado) → bytes   # 2 hojas: Tramo A / Tramo B
exportar_pdf_ejecucion(resultado, titulo=...) → bytes
```

PDF: reportlab, A4 landscape. Header azul `#1e3a5f`, filas alternadas, total en amarillo `#fef3cd`.
PDF Tramo A calc: header verde `#2d6a4f`, dato en verde claro `#d8f3dc`.

---

## 16. Panel de administración (`pages/admin.py`)

Guard doble: router no registra la página para clientes + `if usuario["rol"] != "admin": st.stop()`.

### Secciones
1. **Usuarios y suscripciones**: estado (Al día / Vencido / Bloqueado), marcar pagado, bloquear/desbloquear, métricas
2. **Letrados**: listar activos+inactivos, toggle activar/desactivar, form agregar
3. **Feriados judiciales extra**: listar, eliminar, form agregar (fecha + descripción)
   - Usar para cargar puentes turísticos del decreto anual al inicio de cada año
4. **Agregar usuario**: form completo (nombre, username, password, rol, día pago)

---

## 17. Deploy (Railway)

```json
{"deploy": {"startCommand": "streamlit run app.py --server.port $PORT --server.headless true --server.address 0.0.0.0"}}
```

- `DB_PATH=/data/rastrilla.db` + Volume en `/data`
- `data/diar_ind.xls` vive en el repo (persiste entre deploys). Actualizaciones desde la app se pierden al redeploy — para persistir, mover a `/data/diar_ind.xls` y ajustar `DATA_PATH` en `bcra.py`.

---

## 18. Estado de sprints

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

### ✅ Fixes post-Sprint 3 (rama dev, pendiente commit)
**Bug crítico de calendario** — 4 errores en `calendario.py`:
1. ❌ Feria verano: era Jan 15-31 → ✅ ahora Jan 1-31 (todo enero, CSJN)
2. ❌ Feria invierno: era Jul 1-15 → ✅ ahora Jul 15-31 (CSJN)
3. ❌ Faltaba **17/06 Güemes** (Ley 26.813) en `_FIJOS`
4. ❌ Faltaba **Jueves Santo** (Pascua−3d) — solo se tenía Viernes Santo

Validado: inicio 29/11/2023 + extras (01/04/2024, 21/06/2024) → día 120 = **03/07/2024 ✓**

**UI fix** — `pages/ejecucion.py`:
- `fecha_hasta` movida del paso 3 al paso 5 (después de la planilla)

### 🔜 Sprint 4 (NO implementado)
- **DOCX escritos judiciales**: uno por calculadora (Ejecución, Ampliación, Intereses hasta Cobro)
  - Formato y estructura: pendiente ejemplos del usuario
- **Mecanismo anual de feriados**: recordatorio/banner en Admin para cargar puentes del nuevo año
- Merge `dev` → `main` cuando UAT esté completo

---

## 19. Gotchas críticos — leer antes de tocar el código

### 1. Fórmula BCRA
`(100 + Tₘ) / (100 + T₀) - 1`. **NUNCA** `Tₘ/T₀-1`. T₀ = siempre el día **anterior** al inicio de intereses.

### 2. Calendario judicial — períodos de feria
- Verano: **todo enero** (01-31), no solo la segunda quincena.
- Invierno: **15-31 julio**, no los primeros 15 días.
- Güemes (17/06) y Jueves Santo son feriados del calendario base.
- Puentes turísticos: **SIEMPRE** cargar en `feriados_extra` (varían cada año por decreto).

### 3. Material Symbols / CSS
Nunca aplicar Outfit a `button` ni `span`. Breaks íconos de Streamlit.

### 4. Sidebar wildcard
`[data-testid="stSidebar"] *` rompe SVG del toggle. Usar selectores específicos.

### 5. Capital = Reajustado − Percibido
NUNCA Dif.Neta (incluye SAC) ni la columna "Capital" de BlueCorp.

### 6. Parser expediente
`.partition(":")` en cada línea — preserva `:` en los valores.

### 7. IUS — prohibido en el código
La palabra "IUS" nunca debe aparecer en ningún archivo del proyecto.

### 8. Nombre
Nombre público: **Rake**. Contexto legal: "Doctrina Rastrilla · Vega" (fallo judicial, no nombre de la app).

### 9. fecha efectiva de pago
En **ampliacion.py** y **ejecucion.py**: el `st.date_input` de fecha de pago va **SIEMPRE después** de la tabla editable (`st.data_editor`), no antes.

### 10. lru_cache de calendario
`feriados_del_anio` usa `lru_cache(32)`. El parámetro `extras` debe ser un `tuple` de `date` (hashable). Convertir siempre: `extras = tuple(date.fromisoformat(f["fecha"]) for f in list_feriados_extra())`.

---

## 20. Git log (rama dev)

```
(pendiente commit) fix: calendario judicial + UI ejecucion fecha_hasta al paso 5
f96ff77  feat: Sprint 3 — Ejecucion de Sentencia (120 dias habiles judiciales)
cbe8a34  docs: CONTEXT.md handoff completo Sprint 1-3
86253fe  fix: correccion definitiva formula + fecha T0
4952570  feat: agregar exportacion PDF a ambas calculadoras
a3398c3  fix: fecha efectiva de pago va despues de la tabla en ampliacion
9b8c30f  feat: Sprint 2 — ampliacion.py + tabla expedientes + admin letrados
81bd123  feat: Sprint 1 — home 3 cards + intereses_cobro + tabla abogados
```
