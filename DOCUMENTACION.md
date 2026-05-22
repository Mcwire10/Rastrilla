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
├── app.py                  # Router principal: auth guard + st.navigation() + sidebar global
├── auth.py                 # Autenticación, usuarios SQLite, sesión Streamlit
├── estilo.py               # CSS global (Rake UI — taste-skill DV=8 MI=6 VD=4)
├── bcra.py                 # Carga y descarga del índice BCRA
├── calculos.py             # Motor de cálculo puro (sin UI)
├── parsear_pdf.py          # Parsers por formato: BlueCorp, Jauregui DOCX/Excel/CSV
├── exportar.py             # Exportación Excel y PDF judicial
├── pages/
│   ├── calculadora.py      # UI de cálculo: cargar datos → calcular → exportar
│   └── admin.py            # Panel admin: usuarios, suscripciones, bloqueos
├── data/
│   └── diar_ind.xls        # Serie BCRA bundleada (actualizable desde la app)
├── .streamlit/
│   └── config.toml         # Tema base: light, primaryColor #16a34a
├── requirements.txt
└── DOCUMENTACION.md
```

### Responsabilidades por archivo

| Archivo | Qué hace |
|---|---|
| `app.py` | `set_page_config` · `init_db` · `aplicar_estilos` · auth guard · `st.navigation()` · logo sidebar · footer sidebar |
| `auth.py` | Hash/verify de passwords · CRUD usuarios SQLite · auto-bloqueo por pago · `render_login()` |
| `estilo.py` | CSS inyectado via `st.markdown()`: login split-screen, sidebar oscuro, métricas, animaciones, responsive |
| `bcra.py` | Lee `data/diar_ind.xls`, descarga desde BCRA, expone `cargar_indice()` y `fecha_ultimo_dato()` |
| `calculos.py` | `calcular_intereses(df, indice)` y `primer_dia_mes_siguiente(periodo)` |
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

### Credenciales por defecto (se crean si no existen)

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin2025!` | admin |
| `testuser` | `Test2025` | cliente |

### Auto-bloqueo
Si el día del mes > 10 y el último pago registrado es de un mes anterior al actual, el cliente queda bloqueado automáticamente al intentar login. El admin puede desbloquearlo manualmente o registrar un pago desde el panel de administración.

### Flujo de sesión
```
login() → verifica hash → auto-bloqueo si corresponde → st.session_state["usuario"] = user_dict
logout() → st.session_state.pop("usuario") → st.rerun()
get_session_user() → st.session_state.get("usuario")
```

---

## 3. Navegación (st.navigation)

`app.py` usa `st.navigation(pages, position="hidden")` para ocultar la barra de navegación nativa de Streamlit y construir la propia en el sidebar.

```python
pages = [st.Page("pages/calculadora.py", title="Calculadora", default=True)]
if usuario["rol"] == "admin":
    pages.append(st.Page("pages/admin.py", title="Admin"))

pg = st.navigation(pages, position="hidden")
```

**Estructura del sidebar** (orden de renderizado):

```
⚖️ Rake              ← logo: st.page_link() → siempre navega a calculadora
──────────────────
[contenido de la página activa, ej: Índice BCRA en calculadora.py]
──────────────────
🔧 Administración    ← solo si rol == admin
📊 Calculadora       ← visible siempre (botón de "volver a home")
──────────────────
👤 Nombre · rol
[Cerrar sesión]
```

Ventajas del modelo:
- Los clientes **nunca ven ni pueden acceder** a `admin.py` (la página no existe en su árbol de navegación).
- El logo "Rake" es el botón de "volver al inicio" desde cualquier página.
- El botón `📊 Calculadora` es el back-button explícito desde el panel de admin.

---

## 4. Sistema de diseño (Rake UI)

Implementado íntegramente en `estilo.py` via `st.markdown(_CSS, unsafe_allow_html=True)`.  
Filosofía: **taste-skill** con diales `DESIGN_VARIANCE=8 / MOTION_INTENSITY=6 / VISUAL_DENSITY=4`.

### Tipografía
- **Fuente:** Outfit (Google Fonts) — Inter explícitamente prohibido por taste-skill.
- **Selector CSS:** solo `body, input, textarea, select, p, li, .stMarkdown` — **nunca `button` ni `span`**.
  - Motivo crítico: Streamlit usa **Material Symbols Rounded** (CSS ligatures) para íconos en `button` y `span`. Si se sobreescribe la fuente en estos elementos, el texto "keyboard_double_arrow_left" aparece literal en lugar del ícono de colapsar sidebar.

### Login split-screen (DV=8 — asimétrico)
```
desktop (>= 768px):
  fondo: linear-gradient(90deg, #14532d 50%, #f9fafb 50%)
  izquierda: .login-bg-panel (position: fixed, 50vw) → "Sistema de liquidación / Rake / descripción"
  derecha: st.columns([1,1]) → columna 2 tiene el formulario

mobile (< 768px):
  .login-bg-panel → position: relative, ancho 100%, banner verde superior compacto
  columna izquierda: display: none
  columna formulario: min-width 100%
  .login-spacer: 22vh → 1.5rem
  
tablet (768–1023px):
  split-screen mantenido, brand name reducido a 4rem
```

### Sidebar
- Fondo: `#14532d` (verde oscuro permanente).
- Botones: fondo `rgba(255,255,255,0.92)` + texto `#052e16` (verde muy oscuro para contraste máximo).
- Logo (`st.page_link`): 1.35rem, bold, `letter-spacing: -0.04em`, hover verde menta.
- Selectores **específicos** (sin wildcard `*`) para evitar romper toggle y code.

### Animaciones (MI=6 — cubic-bezier)
- `@keyframes fadeUp` en `[data-testid="stMain"]`: 0.45s, cubic-bezier(0.16, 1, 0.3, 1).
- Métricas con stagger: col1 → 0.05s delay, col2 → 0.12s, col3 → 0.19s.
- Botones: `transform: translateY(-1px)` en hover, `scale(0.98) translateY(1px)` en active.

### Métricas (VD=4)
- Fondo `#f0fdf4`, borde `#bbf7d0`, border-radius 10px.
- Labels en uppercase, `font-size: 0.65rem`, `letter-spacing: 0.08em`.

---

## 5. Algoritmo de cálculo

### Fuente de datos: índice BCRA
- Archivo: `data/diar_ind.xls` (bundleado en el repo)
- URL de descarga: `https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/diar_ind.xls`
- Columna usada: col 9 (índice 0-based), datos desde fila 27
- Serie: tasa pasiva acumulada (Ley 27.802, art. 55, BCRA Res. 45/26)

### Fórmula (BCRA Resolución 45/26)

```
T0  = índice del día ANTERIOR a fecha_desde
Tm  = índice del día de pago (fecha_hasta)

coeficiente = (100 + Tm) / (100 + T0) - 1

interes = capital × coeficiente
total   = capital + interes
```

**T0 es el día anterior a `fecha_desde`**, no el día mismo.  
Sección C de la Res. 45/26: *"T0 es el valor de la serie correspondiente al día anterior a partir del cual se devengan los intereses"*.

### Caso de prueba validado contra calculadora oficial BCRA

| Campo | Valor |
|---|---|
| Capital | $313.665,13 |
| Desde | 01/02/2024 |
| Hasta | 03/03/2026 |
| Tasa acumulada | 94,13% |
| Interés | **$295.240,88** ✓ (coincide al centavo) |

---

## 6. Doctrina de intereses

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

## 7. Formatos de entrada soportados

| Extensión | Sistema | Capital leído |
|---|---|---|
| `.pdf` | BlueCorp | col[3] − col[2] = Reajustado − Percibido |
| `.docx` | Jauregui | col[3] − col[2] = Reajustado − Percibido |
| `.xlsx` / `.xls` | Jauregui | col[Reajustado] − col[Percibido] (detectado por nombre) |
| `.csv` | Estándar | columnas `periodo`, `capital`, `fecha_desde` |

### BlueCorp PDF
- **Página 1:** texto libre con `"calcularon hasta el DD/MM/YYYY"` → fecha sugerida
- **Páginas 2+:** tabla de datos (sin límite de páginas)
- Columnas: `[0]Mes [1]Año [2]Percibido [3]Reajustado [4]DifImporte [5]Dif% [6]Dif-Deducción [7]HAC [8]OS [9]Difer+HAC-OS [10]Capital [11]Interés`

### Jauregui DOCX
- Tabla principal → fila 78 → tabla anidada (`<w:tbl>`)
- Columnas: `[0]Mes [1]Año [2]Percibido [3]Reajustado [4]Tope [5]%Conf [6]LuegoTope [7]Difer. [8]SAC [9]Subtotal [10]OS [11]DifNeta [12]Intereses [13]Total [14]Texto`

### Jauregui Excel
- Fila 0: encabezados (primera celda = `"Mes"`)
- Columnas detectadas por nombre: `Percibido` y `Reajustado`
- Fallback: columna `Difer.` o `Dif.Neta`

---

## 8. Flujo de la aplicación

```
1. Cargar datos
   ├─ Importar archivo (PDF / DOCX / Excel / CSV)
   │   └─ parsear_archivo() detecta formato y extrae períodos
   └─ O cargar/editar manualmente en la tabla (st.data_editor, dinámica)

2. Configurar fecha hasta
   └─ Ingresada por el usuario (única para toda la liquidación)
   └─ Pre-llenada desde el documento si trae fecha sugerida

3. Auto-completar fechas desde (botón)
   └─ 1° del mes siguiente al período

4. Calcular
   └─ calcular_intereses(df, indice)
   └─ Para cada fila: T0 = indice[fecha_desde − 1 día], Tm = indice[fecha_hasta]

5. Ver resultados
   └─ Tabla: período, índice T0, índice Tm, coeficiente, interés, total
   └─ Métricas: capital total · intereses totales · total general

6. Exportar
   └─ Excel (openpyxl): tabla completa con totales
   └─ PDF judicial A4 landscape (reportlab): encabezado + tabla + totales
```

---

## 9. Panel de administración

Accesible solo para `rol == "admin"` (guard doble: router no registra la página + guard interno en `admin.py`).

### Funciones
| Acción | Función |
|---|---|
| Ver todos los usuarios | `list_users()` |
| Estado de suscripción | `_estado(u)` → ✅ Al día / 🟠 Vencido / 🔴 Bloqueado / ⚠️ Sin pago |
| Registrar pago | `registrar_pago(username)` → actualiza `fecha_ultimo_pago`, desbloquea |
| Bloquear / Desbloquear | `set_bloqueado(username, bool)` |
| Crear usuario | `create_user(username, password, nombre, rol, dia_pago)` |

### Métricas de resumen
Total clientes · Al día · Vencidos · Bloqueados

---

## 10. Deploy

### Railway (producción)

```json
// railway.json
{
  "deploy": {
    "startCommand": "streamlit run app.py --server.port $PORT --server.headless true --server.address 0.0.0.0"
  }
}
```

**Variables de entorno en Railway:**

| Variable | Valor |
|---|---|
| `DB_PATH` | `/data/rastrilla.db` |

**Volume Railway:** montado en `/data` → persiste `rastrilla.db` entre reinicios y redeploys.

**Nota:** el índice BCRA (`data/diar_ind.xls`) vive en el repo → se mantiene entre deploys. Las actualizaciones del índice desde la app **no persisten** (filesystem efímero de Railway fuera del volume). Para persistir el índice actualizado: moverlo al volume (`/data/diar_ind.xls`) y ajustar `bcra.py`.

### Ramas

| Rama | Uso |
|---|---|
| `main` | Producción (Railway autodeploy) |
| `dev` | Desarrollo activo — merge a main tras UAT |

### Dependencias

```
streamlit>=1.36      # st.navigation() y st.Page() requieren esta versión mínima
pandas>=2.0
openpyxl>=3.1
xlrd>=2.0
reportlab>=4.0
requests>=2.28
pdfplumber>=0.10
python-docx>=1.1
```

---

## 11. Historial de decisiones técnicas

### Fuente Outfit — por qué `button` y `span` están excluidos del selector CSS
Streamlit renderiza íconos usando **CSS ligatures** con la fuente `Material Symbols Rounded`. El texto "keyboard_double_arrow_left" en un `<button>` o `<span>` con esa fuente se convierte en el ícono visual. Si se aplica `font-family: 'Outfit' !important` a `button` o `span`, la ligature se rompe y el texto aparece literalmente (bug: ícono de colapsar sidebar aparece como texto; bug: ícono de upload aparece duplicado con texto). La solución: solo aplicar Outfit a `body, input, textarea, select, p, li, .stMarkdown`.

### Fórmula de cálculo (BCRA Res. 45/26)
La fórmula correcta es `(100 + Tm) / (100 + T0) - 1`, no `Tm / T0 - 1`. Más importante: **T0 debe ser el día anterior** a `fecha_desde` (no el día mismo). Para el caso de prueba ($313k, Feb 2024 → Mar 2026), el error de la fórmula vieja era +$1.098,17.

### Capital = Reajustado − Percibido
Las planillas tienen varias columnas similares con nombres engañosos:
- `Dif.Neta` / `Capital` del PDF: incluyen el SAC semestral → **incorrecto para intereses mensuales**
- `Difer.` del DOCX/Excel y `Diferencia - Deducción` del PDF: equivalen a Reajustado − Percibido → **correcto**

### Multi-página BlueCorp
El parser original solo leía la página 2. Si la liquidación tiene muchos períodos y el PDF tiene más de 2 páginas se perdían datos. El parser actual itera todas las páginas desde la 2 en adelante.

### Deduplicación por período
Jauregui agrega una fila de totales con el mismo Mes/Año que el último período real. Se descarta comparando con un `set` de períodos ya vistos.

### st.navigation() — requerimiento ≥ 1.36
La API `st.navigation()` + `st.Page()` + `position="hidden"` permite:
- Título de página personalizado (elimina el "app" de la navbar nativa)
- Navegación por rol (las páginas no registradas simplemente no existen para ese usuario)
- Control total del sidebar sin depender de la navbar automática de Streamlit
Requiere `streamlit>=1.36` (actualizado de `>=1.28` en esta iteración).

### Sidebar sin wildcard `*`
El CSS original usaba `[data-testid="stSidebar"] * { color: ... }` lo que sobreescribía el color del ícono SVG del botón toggle y el tamaño de fuente del `<code>` inline. Se reemplazó por selectores específicos: `p, span, small, li, label, .stMarkdown, .stCaption`.

### Login responsive — por qué las columnas no colapsan solas
`st.columns()` en Streamlit siempre es side-by-side, sin media queries automáticas. En mobile, la columna izquierda vacía (placeholder del panel fixed) ocupaba 50% del ancho dejando el formulario en un espacio inutilizable. Solución CSS:
- `< 767px`: `.login-bg-panel → position: relative` (sale del flujo fixed y pasa a banner superior), columna izquierda `display: none`, columna derecha `min-width: 100%`.
- El espaciador vertical usa clase `.login-spacer` controlada por CSS (22vh en desktop → 1.5rem en mobile).

---

## 12. Estado actual (rama `dev`) — pending UAT

**Listo para testing de usuario:**
- ✅ Login responsive (mobile / tablet / desktop)
- ✅ Navegación por rol (clientes no ven admin)
- ✅ Logo "⚖️ Rake" clickeable → home
- ✅ Botón "📊 Calculadora" para volver desde admin
- ✅ Íconos Material Symbols correctos (flecha sidebar, ícono upload)
- ✅ Botones sidebar blancos con texto verde oscuro (#052e16)
- ✅ Panel admin: gestión de usuarios, suscripciones, bloqueos
- ✅ Cálculo de intereses validado contra calculadora BCRA
- ✅ Exportación Excel + PDF judicial
- ✅ Auto-completado de fechas desde períodos

**Pendiente hasta que termine el UAT:**
- ⏳ Pulido fino según feedback de usuarios
- ⏳ Merge `dev` → `main` + verificación de autodeploy Railway
