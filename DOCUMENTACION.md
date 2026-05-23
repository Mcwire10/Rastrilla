# Rake — Documentación técnica

Calculadora de intereses moratorios judiciales contra ANSES (reajuste previsional).  
**Nombre público:** Rake  
**Deploy:** Railway (privado) — rama `main` → producción automática  
**Repo:** `https://github.com/Mcwire10/Rastrilla` (privado)  
**Stack:** Python 3.11 · Streamlit ≥1.36 · SQLite · pdfplumber · python-docx · reportlab · pandas

---

## 1. Arquitectura de archivos

```
rastrilla/
├── app.py                    # Router principal: auth guard + st.navigation() + sidebar global
├── auth.py                   # Autenticación, usuarios/abogados/expedientes SQLite, sesión
├── estilo.py                 # CSS global (Rake UI — taste-skill DV=8 MI=6 VD=4)
├── bcra.py                   # Carga y descarga del índice BCRA
├── calculos.py               # Motor de cálculo puro (sin UI)
├── parsear_pdf.py            # Parsers por formato: BlueCorp, Jauregui DOCX/Excel/CSV
├── exportar.py               # Exportación Excel y PDF judicial
├── pages/
│   ├── home.py               # Pantalla principal con 3 cards de calculadoras
│   ├── ampliacion.py         # Calculadora: Ampliación de Ejecución (multi-período)
│   ├── intereses_cobro.py    # Calculadora: Intereses Aprobados hasta Cobro (capital único)
│   └── admin.py              # Panel admin: usuarios, suscripciones, abogados, bloqueos
├── data/
│   └── diar_ind.xls          # Serie BCRA bundleada (actualizable desde la app)
├── .streamlit/
│   └── config.toml           # Tema base: light, primaryColor #16a34a
├── requirements.txt
└── DOCUMENTACION.md
```

### Responsabilidades por archivo

| Archivo | Qué hace |
|---|---|
| `app.py` | `set_page_config` · `init_db` · `aplicar_estilos` · auth guard · `st.navigation()` · logo sidebar · footer sidebar |
| `auth.py` | Hash/verify passwords · CRUD usuarios/abogados/expedientes SQLite · auto-bloqueo · `render_login()` |
| `estilo.py` | CSS inyectado via `st.markdown()`: login split-screen, sidebar oscuro, cards, métricas, animaciones, responsive |
| `bcra.py` | Lee `data/diar_ind.xls`, descarga desde BCRA, expone `cargar_indice()` y `fecha_ultimo_dato()` |
| `calculos.py` | Motor: `calcular_interes_simple()`, `calcular_intereses()`, `calcular_fila()`, `primer_dia_mes_siguiente()` |
| `parsear_pdf.py` | Detecta formato por extensión/contenido y retorna `(df, nombre_formato)` |
| `exportar.py` | `exportar_excel()` → bytes xlsx · `exportar_pdf()` → bytes PDF A4 landscape |

---

## 2. Sistema de autenticación

### Base de datos
SQLite en `rastrilla.db` (configurable via `DB_PATH` env var).  
En Railway: `DB_PATH=/data/rastrilla.db` + Volume montado en `/data` para persistencia.

### Tabla `usuarios`

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | Autoincrement |
| `username` | TEXT UNIQUE | Login |
| `password_hash` | TEXT | `salt:sha256(salt+password)` |
| `rol` | TEXT | `admin` o `cliente` |
| `nombre` | TEXT | Nombre completo |
| `fecha_contrato` | TEXT | ISO date del alta |
| `dia_pago` | INTEGER | Día del mes acordado (1–10) |
| `fecha_ultimo_pago` | TEXT | ISO date del último pago registrado |
| `bloqueado` | INTEGER | 0/1 |

### Tabla `abogados`

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | Autoincrement |
| `nombre_completo` | TEXT | En mayúsculas (ej: GONZALEZ PONDAL JUAN MANUEL) |
| `cuil` | TEXT UNIQUE | Formato libre (ej: 20/26436117/7) |
| `activo` | INTEGER | 0/1 — solo activos aparecen en las calculadoras |

**Letrados cargados por defecto:**
- GONZALEZ PONDAL JUAN MANUEL · CUIL 20/26436117/7
- MOYANO MATIAS ISMAEL · CUIL 23-38001381-9

### Tabla `expedientes` (log de cálculos)

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | Autoincrement |
| `tipo` | TEXT | `ampliacion` o `cobro` |
| `letrado_id` | INTEGER | FK → abogados.id |
| `expediente` | TEXT | Número de expediente |
| `caratula` | TEXT | Carátula de la causa |
| `capital_total` | REAL | Suma de capitales |
| `interes_total` | REAL | Suma de intereses calculados |
| `total` | REAL | Capital + intereses |
| `fecha_calculo` | TEXT | ISO date del día del cálculo |

### Credenciales por defecto

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin2025!` | admin |
| `testuser` | `Test2025` | cliente |

### Auto-bloqueo
Si el día del mes > 10 y el último pago registrado es de un mes anterior, el cliente queda bloqueado al intentar login. El admin puede desbloquearlo o registrar pago desde el panel.

### Flujo de sesión
```
login() → verifica hash → auto-bloqueo si corresponde → st.session_state["usuario"] = user_dict
logout() → st.session_state.pop("usuario") → st.rerun()
get_session_user() → st.session_state.get("usuario")
```

---

## 3. Navegación (st.navigation)

`app.py` usa `st.navigation(pages, position="hidden")` para construir la navegación en el sidebar.

```python
pages = [
    st.Page("pages/home.py",            title="Inicio",                 default=True),
    st.Page("pages/ampliacion.py",      title="Ampliación de Ejecución"),
    st.Page("pages/intereses_cobro.py", title="Intereses hasta Cobro"),
]
if usuario["rol"] == "admin":
    pages.append(st.Page("pages/admin.py", title="Admin"))
```

**Estructura del sidebar** (orden de renderizado):

```
⚖️ Rake              ← logo: st.page_link() → siempre navega a home.py
──────────────────
[contenido de la página activa, ej: Índice BCRA en calculadoras]
──────────────────
🔧 Administración    ← solo si rol == admin
🏠 Inicio            ← visible siempre
──────────────────
👤 Nombre · rol
[Cerrar sesión]
```

Los clientes **nunca ven ni pueden acceder** a `admin.py`. El logo "⚖️ Rake" es el botón de "volver al home" desde cualquier página.

---

## 4. Pantalla principal (home.py)

Tres cards de calculadoras en columnas. Cada card tiene icono, título, descripción y botón "▶ Iniciar" (o badge "Próximamente" si no está implementada).

| Card | Estado | Destino |
|---|---|---|
| 📋 Ejecución de Sentencia | Próximamente (Sprint 3) | `pages/ejecucion.py` |
| 📎 Ampliación de Ejecución | ✅ Operativa | `pages/ampliacion.py` |
| 💰 Intereses Aprobados hasta Cobro | ✅ Operativa | `pages/intereses_cobro.py` |

---

## 5. Calculadoras

### 5.1 Ampliación de Ejecución (`ampliacion.py`)

**Caso de uso:** múltiples períodos de diferencia de haberes. Para cada período, el interés mora corre desde el 1° del mes siguiente.

**Flujo por pasos:**
1. **Letrado presentante** — `st.selectbox` con abogados activos de la DB
2. **Datos del expediente** — copy-paste del texto del sistema de consulta judicial; parser automático por `:` en cada línea
3. **Planilla de liquidación:**
   - `st.file_uploader` — acepta PDF BlueCorp, DOCX Jauregui, Excel, CSV
   - Si el archivo trae `fecha_pago` (ej: BlueCorp), se pre-llena el date_input
   - Botón "🔄 Auto-fechas" — calcula `fecha_desde` = 1° del mes siguiente al período
   - `st.date_input` — fecha efectiva de pago única para toda la liquidación
   - `st.data_editor` — tabla editable para revisión y corrección manual
4. **Calcular** → `calcular_intereses(df, indice)`; resultado en `st.session_state["amp_resultado"]`
5. **Resultado** — tabla detallada + métricas (capital · intereses · total)
6. **Exportar** — Excel `.xlsx` con nombre `ampliacion_{expediente}.xlsx`

Cada cálculo exitoso se loguea en la tabla `expedientes`.

### 5.2 Intereses Aprobados hasta Cobro (`intereses_cobro.py`)

**Caso de uso:** capital único aprobado judicialmente. Los intereses corren desde el día siguiente a la aprobación hasta el efectivo cobro.

**Flujo por pasos:**
1. **Letrado presentante** — igual que ampliación
2. **Datos del expediente** — igual que ampliación
3. **Datos del cálculo:**
   - Capital aprobado ($)
   - Fecha de aprobación judicial → T₀ = índice de este día (intereses desde el día siguiente)
   - Fecha de efectivo cobro → Tₘ = índice de este día
4. **Calcular** → `calcular_interes_simple(capital, fecha_aprobacion, fecha_cobro, indice)`
5. **Resultado** — 3 métricas + expander con detalle (T₀, Tₘ, coeficiente)
6. **Exportar** — Excel `.xlsx` con nombre `intereses_cobro_{expediente}.xlsx`

### 5.3 Ejecución de Sentencia (`ejecucion.py`) — Sprint 3

**Pendiente.** Requerirá:
- Calendario de 120 días hábiles judiciales (feriados fijos 2020–2028 + tabla `feriados_extra` en DB)
- Wizard 4 pantallas (datos → tramo A → tramo B → resultado)
- División automática Tramo A / Tramo B en el día hábil 121

---

## 6. Algoritmo de cálculo

### Fuente de datos: índice BCRA
- Archivo: `data/diar_ind.xls` (bundleado en el repo)
- URL de descarga: `https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/diar_ind.xls`
- Columna usada: col 9 (índice 0-based), datos desde fila 27
- Serie: tasa pasiva acumulada (Ley 27.802, art. 55) — **índice acumulado**, no tasa porcentual

### Fórmula (corregida — validada contra CM CABA)

```
T₀  = índice del día base (ver regla por calculadora)
Tₘ  = índice del día de pago o cobro efectivo

coeficiente = Tₘ / T₀ - 1          ← índice acumulado puro

interes = capital × coeficiente
total   = capital + interes
```

> ⚠️ **Nota crítica:** la fórmula es `Tₘ/T₀ - 1`, **NO** `(100+Tₘ)/(100+T₀) - 1`.  
> Los valores del índice BCRA son acumulados en miles (~19.000–25.000). La variante con `+100`  
> introduce un error sistemático de ~0,16pp. Ver sección 11 (Decisiones técnicas).

### Regla de T₀ según calculadora

| Calculadora | T₀ | fecha_desde (display) |
|---|---|---|
| **Ampliación** (`calcular_fila`) | índice del día **anterior** a `fecha_desde` | 1° del mes siguiente al período |
| **Intereses hasta Cobro** (`calcular_interes_simple`) | índice del **día de aprobación** | día siguiente a la aprobación |

### Validación contra CM CABA (23/05/2026)

| Campo | Valor |
|---|---|
| Capital | $15.000.028 |
| Fecha aprobación | 01/05/2025 |
| Fecha cobro | 20/05/2026 |
| T₀ (01/05/2025) | 19.379,0980 |
| Tₘ (20/05/2026) | 25.582,0246 |
| Coeficiente Rake | 32,0083% |
| CM CABA (hasta 21/05/2026) | 32,00% |

Diferencia residual (~0,008pp) = 1 día de fecha (el usuario usó 20/05 en Rake y 21/05 en CM CABA).  
Con misma fecha, los resultados coinciden al centavo.

---

## 7. Doctrina de intereses

Cada diferencia mensual de haber es una obligación independiente.  
Los intereses corren desde el **1° del mes siguiente** al período liquidado.

| Período | Intereses desde |
|---|---|
| 04/2021 | 01/05/2021 |
| 12/2024 | 01/01/2025 |

```
Capital = Haber Reajustado − Haber Percibido
```

**No se usa:**
- `Dif.Neta` (incluye SAC/aguinaldo semestral)
- `Capital` del PDF BlueCorp (incluye HAC y descuenta OS)

---

## 8. Formatos de entrada soportados

| Extensión | Sistema | Capital leído |
|---|---|---|
| `.pdf` (BlueCorp) | BlueCorp | col[3] − col[2] = Reajustado − Percibido |
| `.pdf` (Jauregui) | Jauregui PDF | col[3] − col[2] = Reajustado − Percibido |
| `.docx` | Jauregui DOCX | col[3] − col[2] = Reajustado − Percibido |
| `.xlsx` / `.xls` | Jauregui Excel | col[Reajustado] − col[Percibido] (por nombre) |
| `.csv` | Estándar | columnas `periodo`, `capital`, `fecha_desde` |

### BlueCorp PDF
- **Página 1:** texto libre con `"calcularon hasta el DD/MM/YYYY"` → fecha sugerida
- **Páginas 2+:** tabla de datos (sin límite de páginas)
- Detección: si página 1 contiene `"bluecorp"` → parser BlueCorp; si no → parser Jauregui PDF

### Jauregui DOCX
- Tabla principal → fila 77: fecha_pago · fila 78: tabla anidada (`<w:tbl>`) con datos

### Parser de expediente (copy-paste)
Cada línea del texto pegado se divide por el **primer** `":"` usando `.partition(":")`.  
Esto preserva los dos puntos en los valores (ej: carátula con `c/` o dependencia con `:` interno).

---

## 9. Panel de administración (`admin.py`)

Accesible solo para `rol == "admin"` (guard doble: router + guard interno).

### Sección Usuarios
| Acción | Función |
|---|---|
| Ver todos los usuarios | `list_users()` |
| Estado de suscripción | `_estado(u)` → ✅ Al día / 🟠 Vencido / 🔴 Bloqueado / ⚠️ Sin pago |
| Registrar pago | `registrar_pago(username)` → actualiza `fecha_ultimo_pago`, desbloquea |
| Bloquear / Desbloquear | `set_bloqueado(username, bool)` |
| Crear usuario | `create_user(username, password, nombre, rol, dia_pago)` |

### Sección Letrados
| Acción | Función |
|---|---|
| Ver todos (activos + inactivos) | `_list_abogados_all()` (consulta directa, sin filtro activo) |
| Activar / Desactivar | `set_abogado_activo(id, bool)` |
| Agregar letrado | `create_abogado(nombre_completo, cuil)` |

---

## 10. Deploy

### Railway (producción)

```json
{
  "deploy": {
    "startCommand": "streamlit run app.py --server.port $PORT --server.headless true --server.address 0.0.0.0"
  }
}
```

**Variables de entorno:**

| Variable | Valor |
|---|---|
| `DB_PATH` | `/data/rastrilla.db` |

**Volume Railway:** montado en `/data` → persiste `rastrilla.db` entre reinicios.

**Nota sobre el índice BCRA:** vive en el repo (`data/diar_ind.xls`) → se mantiene entre deploys. Las actualizaciones desde la app **no persisten** en Railway (filesystem efímero). Para persistir: mover a `/data/diar_ind.xls` y ajustar `bcra.py`.

### Ramas

| Rama | Uso |
|---|---|
| `main` | Producción (Railway autodeploy) |
| `dev` | Desarrollo activo — merge a main tras UAT |

### Dependencias

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

## 11. Decisiones técnicas

### Fórmula de cálculo: `Tₘ/T₀ - 1` (no `(100+Tₘ)/(100+T₀) - 1`)

El índice BCRA Com. 14290 es un **índice acumulado** cuyos valores están en el orden de miles (en mayo 2025: ~19.000; mayo 2026: ~25.000). Para índices de este tipo, la fórmula de retorno es simplemente `Tₘ/T₀ - 1`.

La variante con `+100` sería correcta si los valores fueran tasas porcentuales pequeñas (ej: T=2,5 = "2,5%"). Con valores en miles, el `+100` introduce un error sistemático de ~0,16pp que acumula error significativo sobre capitales grandes. Ejemplo: sobre $15M, el error era ~$23.000.

**Validación:** con `Tₘ/T₀ - 1` obtenemos 32,008% para el par de índices de mayo 2025 → mayo 2026, coincidente con el 32,00% de CM CABA (diferencia residual = 1 día de fecha).

### Fuente Outfit — exclusión de `button` y `span`

Streamlit renderiza íconos usando **CSS ligatures** con `Material Symbols Rounded`. Si se aplica `font-family: 'Outfit'` a `button` o `span`, la ligature se rompe y el texto "keyboard_double_arrow_left" aparece literalmente. Selector seguro: solo `body, input, textarea, select, p, li, .stMarkdown`.

### T₀ y display del índice en Intereses hasta Cobro

En `calcular_interes_simple()`:
- **T₀** = índice del **día de aprobación** (`fecha_aprobacion`). Los intereses comienzan el día siguiente, pero el índice se toma el mismo día de la aprobación.
- El resultado incluye tanto `fecha_t0` (día del índice T₀ = aprobación) como `fecha_desde` (día de inicio de intereses = aprobación + 1 día) para mostrar correctamente en el expander.

### Capital = Reajustado − Percibido (no Dif.Neta ni Capital del PDF)

`Dif.Neta` incluye SAC semestral → incorrecto para intereses mensuales.  
`Capital` del PDF BlueCorp incluye HAC y descuenta OS → incorrecto.  
La columna correcta es `col[3] − col[2]` en todos los formatos.

### Multi-página BlueCorp
El parser itera todas las páginas desde la 2 en adelante (sin límite), evitando pérdida de datos en liquidaciones con muchos períodos.

### Deduplicación por período
Jauregui agrega una fila de totales con el mismo Mes/Año que el último período real. Se descarta con un `set` de períodos ya vistos.

### st.navigation() — ≥ 1.36
Permite título de página personalizado, navegación por rol, y control total del sidebar sin depender de la navbar automática.

### Sidebar sin wildcard `*`
`[data-testid="stSidebar"] * { color: ... }` rompía el ícono SVG del toggle y el tamaño de `<code>` inline. Se reemplazó por selectores específicos.

### Login responsive
`st.columns()` nunca colapsa automáticamente. En mobile: `.login-bg-panel → position: relative` (banner superior), columna izquierda `display: none`, columna derecha `min-width: 100%`.

---

## 12. Sprints completados

### Sprint 1 — home + intereses_cobro + abogados (commit `81bd123`)
- `pages/home.py`: pantalla principal con 3 cards (Ampliación e Intereses operativas, Ejecución próximamente)
- `pages/intereses_cobro.py`: calculadora capital único — letrado, expediente, capital, fechas, Excel
- `auth.py`: tabla `abogados` + `list_abogados()` / `create_abogado()` / `set_abogado_activo()`
- `calculos.py`: `calcular_interes_simple()`
- `estilo.py`: clases CSS `.calc-card`

### Sprint 2 — ampliacion + expedientes log + admin letrados (commit `9b8c30f`)
- `pages/ampliacion.py`: calculadora multi-período — letrado, expediente, planilla BlueCorp/Jauregui, fecha_pago, tabla editable, calcular, Excel
- `auth.py`: tabla `expedientes` + `log_calculo()`
- `pages/admin.py`: sección Letrados (ver/activar/desactivar/agregar)
- `pages/home.py`: card Ampliación operativa
- `pages/calculadora.py`: eliminado (absorbido por `ampliacion.py`)

### Fix fórmula (commit pendiente)
- `calculos.py`: corrección de `(100+Tₘ)/(100+T₀)-1` → `Tₘ/T₀-1` en `calcular_fila()` y `calcular_interes_simple()`
- `calculos.py`: `calcular_interes_simple()` ahora retorna `fecha_t0` para display correcto
- `intereses_cobro.py`: display T₀ corregido (muestra `fecha_t0` = aprobación, no `fecha_desde`)

---

## 13. Estado actual — rama `dev`

### Calculadoras operativas
- ✅ Intereses Aprobados hasta Cobro — validado contra CM CABA
- ✅ Ampliación de Ejecución — parsers BlueCorp / Jauregui DOCX / Excel / CSV
- ⏳ Ejecución de Sentencia — Sprint 3

### Infraestructura
- ✅ Login responsive (mobile / tablet / desktop)
- ✅ Navegación por rol
- ✅ Sidebar: logo ⚖️ Rake, botones blancos texto verde oscuro
- ✅ Panel admin: usuarios + letrados
- ✅ Log de cálculos en tabla `expedientes`
- ✅ Índice BCRA actualizable desde la app

### Pendiente para pasar a `main`
- ⏳ UAT de Ampliación con planillas reales BlueCorp/Jauregui
- ⏳ Sprint 3: Ejecución de Sentencia + calendario judicial
