"""
auth.py — Autenticación y gestión de usuarios RASTRILLA
SQLite + Railway Volume (/data/rastrilla.db en producción)
"""
import hashlib
import os
import secrets
import smtplib
import sqlite3
import traceback as _traceback
from datetime import date, datetime
from email.mime.text import MIMEText
from pathlib import Path

import streamlit as st

# Destinatario fijo de alertas de error
_ERROR_MAIL_TO = "leandro.moyano7@gmail.com"

# En Railway: variable de entorno DB_PATH=/data/rastrilla.db + Volume montado en /data
DB_PATH = Path(os.getenv("DB_PATH", "rastrilla.db"))


# ── Base de datos ─────────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Crea todas las tablas si no existen e inserta datos por defecto."""
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                username          TEXT    UNIQUE NOT NULL,
                password_hash     TEXT    NOT NULL,
                rol               TEXT    NOT NULL DEFAULT 'cliente',
                nombre            TEXT    NOT NULL DEFAULT '',
                fecha_contrato    TEXT    NOT NULL,
                dia_pago          INTEGER NOT NULL DEFAULT 1,
                fecha_ultimo_pago TEXT,
                bloqueado         INTEGER NOT NULL DEFAULT 0,
                primer_login      INTEGER NOT NULL DEFAULT 0
            )
        """)
        # Migración: agregar primer_login a DBs existentes
        try:
            c.execute("ALTER TABLE usuarios ADD COLUMN primer_login INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass  # columna ya existe

        # Forzar primer_login=1 para usuarios que aún usan la contraseña por defecto
        for _uname, _default_pass in [
            ("gonzalez", "Pndl#R4k3J"),
            ("moyano",   "Myn#R4k3M"),
        ]:
            _row = c.execute(
                "SELECT password_hash FROM usuarios WHERE username = ? AND primer_login = 0",
                (_uname,)
            ).fetchone()
            if _row and _verify(_default_pass, _row["password_hash"]):
                c.execute(
                    "UPDATE usuarios SET primer_login = 1 WHERE username = ?", (_uname,)
                )

        hoy = date.today().isoformat()

        # Eliminar usuario de prueba si existe (setup inicial)
        c.execute("DELETE FROM usuarios WHERE username = 'testuser'")

        for username, password, rol, nombre, primer_login in [
            ("admin",    "Admin2025!",  "admin",   "Administrador",              0),
            ("gonzalez", "Pndl#R4k3J", "cliente", "GONZALEZ PONDAL JUAN MANUEL", 1),
            ("moyano",   "Myn#R4k3M",  "cliente", "MOYANO MATIAS ISMAEL",        1),
        ]:
            existe = c.execute(
                "SELECT 1 FROM usuarios WHERE username = ?", (username,)
            ).fetchone()
            if not existe:
                c.execute(
                    """INSERT INTO usuarios
                       (username, password_hash, rol, nombre, fecha_contrato,
                        dia_pago, primer_login)
                       VALUES (?, ?, ?, ?, ?, 1, ?)""",
                    (username, _hash(password), rol, nombre, hoy, primer_login),
                )

        # ── Abogados ──────────────────────────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS abogados (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_completo  TEXT    NOT NULL,
                cuil             TEXT    NOT NULL UNIQUE,
                activo           INTEGER NOT NULL DEFAULT 1
            )
        """)
        for nombre_ab, cuil_ab in [
            ("GONZALEZ PONDAL JUAN MANUEL", "20/26436117/7"),
            ("MOYANO MATIAS ISMAEL",         "23-38001381-9"),
        ]:
            existe = c.execute(
                "SELECT 1 FROM abogados WHERE cuil = ?", (cuil_ab,)
            ).fetchone()
            if not existe:
                c.execute(
                    "INSERT INTO abogados (nombre_completo, cuil) VALUES (?, ?)",
                    (nombre_ab, cuil_ab),
                )

        # ── Expedientes (log de cálculos) ─────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS expedientes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo          TEXT    NOT NULL,
                letrado_id    INTEGER,
                expediente    TEXT,
                caratula      TEXT,
                capital_total REAL,
                interes_total REAL,
                total         REAL,
                fecha_calculo TEXT    NOT NULL,
                FOREIGN KEY (letrado_id) REFERENCES abogados(id)
            )
        """)

        # ── Feriados extra (días inhábiles judiciales adicionales) ────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS feriados_extra (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha       TEXT    NOT NULL UNIQUE,
                descripcion TEXT    NOT NULL DEFAULT ''
            )
        """)

        # ── Log de errores del sistema ────────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS errores (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT    NOT NULL,
                tipo       TEXT    NOT NULL DEFAULT '',
                mensaje    TEXT    NOT NULL,
                traceback  TEXT    NOT NULL DEFAULT '',
                mail_ok    INTEGER NOT NULL DEFAULT 0
            )
        """)

        # ── Uso de calculadoras (documentos generados) ────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS uso_documentos (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    TEXT    NOT NULL,
                username     TEXT    NOT NULL,
                calculadora  TEXT    NOT NULL,
                tipo_doc     TEXT    NOT NULL
            )
        """)


# ── Password ──────────────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{h}"


def _verify(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split(":", 1)
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == h
    except Exception:
        return False


# ── CRUD usuarios ─────────────────────────────────────────────────────────────

def get_user(username: str) -> dict | None:
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM usuarios WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None


def list_users() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM usuarios ORDER BY fecha_contrato DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def create_user(username: str, password: str, nombre: str,
                rol: str, dia_pago: int) -> None:
    with _conn() as c:
        c.execute(
            """INSERT INTO usuarios
               (username, password_hash, rol, nombre, fecha_contrato, dia_pago)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username, _hash(password), rol, nombre,
             date.today().isoformat(), dia_pago),
        )



# ── CRUD abogados ─────────────────────────────────────────────────────────────

def list_abogados() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM abogados WHERE activo = 1 ORDER BY nombre_completo"
        ).fetchall()
        return [dict(r) for r in rows]


def create_abogado(nombre_completo: str, cuil: str) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO abogados (nombre_completo, cuil) VALUES (?, ?)",
            (nombre_completo, cuil),
        )


def set_abogado_activo(abogado_id: int, activo: bool) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE abogados SET activo = ? WHERE id = ?",
            (int(activo), abogado_id),
        )


# ── CRUD expedientes ──────────────────────────────────────────────────────────

def log_calculo(
    tipo: str,
    letrado_id: int | None,
    expediente: str,
    caratula: str,
    capital_total: float,
    interes_total: float,
    total: float,
) -> None:
    """Registra un cálculo realizado en el log de expedientes."""
    with _conn() as c:
        c.execute(
            """INSERT INTO expedientes
               (tipo, letrado_id, expediente, caratula,
                capital_total, interes_total, total, fecha_calculo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (tipo, letrado_id, expediente, caratula,
             capital_total, interes_total, total, date.today().isoformat()),
        )


# ── CRUD feriados extra ───────────────────────────────────────────────────────

def list_feriados_extra() -> list[dict]:
    """Lista todos los feriados/inhábiles judiciales extra, ordenados por fecha."""
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM feriados_extra ORDER BY fecha"
        ).fetchall()
        return [dict(r) for r in rows]


def add_feriado_extra(fecha: date, descripcion: str) -> None:
    """Agrega un día inhábil judicial extra (única por fecha)."""
    with _conn() as c:
        c.execute(
            "INSERT INTO feriados_extra (fecha, descripcion) VALUES (?, ?)",
            (fecha.isoformat(), descripcion),
        )


def delete_feriado_extra(feriado_id: int) -> None:
    """Elimina un feriado extra por su ID."""
    with _conn() as c:
        c.execute("DELETE FROM feriados_extra WHERE id = ?", (feriado_id,))


def importar_puentes_anio(year: int) -> list[dict]:
    """
    Descarga los feriados del año desde api.argentinadatos.com,
    filtra los de tipo 'puente' e inserta en feriados_extra.

    Retorna lista de dicts: {fecha, descripcion, nuevo (bool)}
      nuevo=True  → recién insertado
      nuevo=False → ya existía (UNIQUE constraint → ignorado)
    """
    import requests
    url = f"https://api.argentinadatos.com/v1/feriados/{year}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    # Respuesta: [{"fecha": "2024-04-01", "tipo": "puente", "nombre": "..."}]
    puentes = [f for f in resp.json() if f.get("tipo") == "puente"]
    resultado = []
    for p in puentes:
        fecha = date.fromisoformat(p["fecha"])
        desc  = p.get("nombre", "Puente turístico")
        try:
            add_feriado_extra(fecha, desc)
            resultado.append({"fecha": fecha, "descripcion": desc, "nuevo": True})
        except Exception:
            # Violación de UNIQUE → ya existía, lo ignoramos
            resultado.append({"fecha": fecha, "descripcion": desc, "nuevo": False})
    return resultado


# ── Log de errores ────────────────────────────────────────────────────────────

def _send_error_email(subject: str, body: str) -> bool:
    """
    Envía un mail de alerta a _ERROR_MAIL_TO.
    Requiere variables de entorno SMTP_USER y SMTP_PASSWORD (Gmail app password).
    Retorna True si el envío fue exitoso.
    """
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    if not smtp_user or not smtp_pass:
        return False
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = f"[Rake] Error: {subject}"
        msg["From"]    = smtp_user
        msg["To"]      = _ERROR_MAIL_TO
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as s:
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        return True
    except Exception:
        return False


def log_error(tipo: str, mensaje: str, tb: str = "") -> None:
    """
    Registra un error en la tabla errores y envía mail de alerta si está configurado.
    Llamar desde bloques except para capturar fallos del sistema.
    """
    ts = datetime.now().isoformat(sep=" ", timespec="seconds")
    body = (
        f"Timestamp : {ts}\n"
        f"Tipo      : {tipo}\n"
        f"Mensaje   : {mensaje}\n\n"
        f"Traceback :\n{tb}"
    )
    mail_ok = int(_send_error_email(tipo or "Error", body))
    with _conn() as c:
        c.execute(
            "INSERT INTO errores (timestamp, tipo, mensaje, traceback, mail_ok) "
            "VALUES (?, ?, ?, ?, ?)",
            (ts, tipo, mensaje, tb, mail_ok),
        )


def list_errores(limit: int = 50) -> list[dict]:
    """Retorna los últimos errores registrados, más recientes primero."""
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM errores ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def clear_errores() -> None:
    """Elimina todos los registros de la tabla errores."""
    with _conn() as c:
        c.execute("DELETE FROM errores")


# ── Uso de calculadoras ───────────────────────────────────────────────────────

_CALC_LABELS = {
    "ejecucion":  "Ejecución",
    "ampliacion": "Ampliación",
    "cobro":      "Hasta Cobro",
}
_DOC_LABELS = {
    "excel": "Excel",
    "pdf":   "PDF",
    "docx":  "DOCX",
}


def log_uso(username: str, calculadora: str, tipo_doc: str) -> None:
    """Registra la generación de un documento. Silencioso ante cualquier error."""
    try:
        ts = datetime.now().isoformat(sep=" ", timespec="seconds")
        with _conn() as c:
            c.execute(
                "INSERT INTO uso_documentos (timestamp, username, calculadora, tipo_doc) "
                "VALUES (?, ?, ?, ?)",
                (ts, username, calculadora, tipo_doc),
            )
    except Exception:
        pass


def get_uso_mensual(meses: int = 12) -> dict:
    """
    Retorna estadísticas de uso para el panel de administración.
    {
      'por_mes_calc':  [(mes, calculadora, cantidad), ...],   ← últimos `meses` meses
      'por_usuario':   [(mes, username, calculadora, tipo_doc, cantidad), ...],
      'total_mes':     int,
      'total_hist':    int,
      'top_usuario':   str | None,
    }
    """
    mes_actual = datetime.now().strftime("%Y-%m")
    with _conn() as c:
        por_mes_calc = c.execute("""
            SELECT strftime('%Y-%m', timestamp) AS mes,
                   calculadora, COUNT(*) AS cantidad
            FROM uso_documentos
            WHERE mes >= date('now', ?)
            GROUP BY mes, calculadora
            ORDER BY mes ASC
        """, (f"-{meses} months",)).fetchall()

        por_usuario = c.execute("""
            SELECT strftime('%Y-%m', timestamp) AS mes,
                   username, calculadora, tipo_doc, COUNT(*) AS cantidad
            FROM uso_documentos
            WHERE mes >= date('now', ?)
            GROUP BY mes, username, calculadora, tipo_doc
            ORDER BY mes DESC, username
        """, (f"-{meses} months",)).fetchall()

        total_mes = c.execute(
            "SELECT COUNT(*) FROM uso_documentos "
            "WHERE strftime('%Y-%m', timestamp) = ?", (mes_actual,)
        ).fetchone()[0]

        total_hist = c.execute(
            "SELECT COUNT(*) FROM uso_documentos"
        ).fetchone()[0]

        top_row = c.execute("""
            SELECT username, COUNT(*) AS n FROM uso_documentos
            GROUP BY username ORDER BY n DESC LIMIT 1
        """).fetchone()
        top_usuario = f"{top_row['username']} ({top_row['n']})" if top_row else None

    return {
        "por_mes_calc": [dict(r) for r in por_mes_calc],
        "por_usuario":  [dict(r) for r in por_usuario],
        "total_mes":    total_mes,
        "total_hist":   total_hist,
        "top_usuario":  top_usuario,
    }



# ── Sesión ────────────────────────────────────────────────────────────────────

def get_session_user() -> dict | None:
    return st.session_state.get("usuario")


def login(username: str, password: str) -> str:
    """Retorna: 'ok' | 'no_user' | 'bad_pass'"""
    user = get_user(username)
    if not user:
        return "no_user"
    if not _verify(password, user["password_hash"]):
        return "bad_pass"
    st.session_state["usuario"] = user
    return "ok"


def logout() -> None:
    st.session_state.pop("usuario", None)
    st.rerun()


def change_password(username: str, new_password: str) -> None:
    """Actualiza la contraseña y marca primer_login = 0."""
    with _conn() as c:
        c.execute(
            "UPDATE usuarios SET password_hash = ?, primer_login = 0 WHERE username = ?",
            (_hash(new_password), username),
        )


# ── UI de login ───────────────────────────────────────────────────────────────

def render_cambio_password() -> None:
    """
    Pantalla de cambio de contraseña en primer ingreso.
    Muestra el panel de marca igual que el login (mismo split-screen CSS).
    Tras guardar, actualiza session_state y hace rerun → entra directo a la app.
    """
    usuario = st.session_state.get("usuario", {})
    nombre = usuario.get("nombre", "")
    nombre_corto = nombre.split()[0].capitalize() if nombre else "Usuario"

    st.markdown("""
<div class="login-bg-panel" aria-hidden="true">
  <div class="login-brand-eyebrow">Sistema de liquidación</div>
  <div class="login-brand-name">Rake</div>
  <div class="login-brand-desc">
    Intereses moratorios<br>por reajuste previsional
  </div>
  <div class="login-brand-tag">Uso interno · Estudio jurídico</div>
</div>
""", unsafe_allow_html=True)

    _, col = st.columns([1, 1])
    with col:
        st.markdown("<div class='login-spacer'></div>", unsafe_allow_html=True)
        st.markdown(f"""
<div class="login-form-area">
  <p class="login-form-heading">👋 Bienvenido, {nombre_corto}</p>
  <p class="login-form-sub">Es tu primer ingreso. Creá tu contraseña personal para continuar.</p>
</div>
""", unsafe_allow_html=True)
        with st.form("form_cambio_pass"):
            nueva    = st.text_input("Nueva contraseña", type="password", placeholder="••••••••")
            confirma = st.text_input("Confirmar contraseña", type="password", placeholder="••••••••")
            submitted = st.form_submit_button(
                "Guardar y continuar", use_container_width=True, type="primary"
            )
        if submitted:
            if len(nueva) < 8:
                st.error("La contraseña debe tener al menos 8 caracteres.")
            elif nueva != confirma:
                st.error("Las contraseñas no coinciden.")
            else:
                change_password(usuario["username"], nueva)
                # Refrescar session_state con los datos actualizados
                st.session_state["usuario"] = get_user(usuario["username"])
                st.rerun()


def render_login() -> None:
    """
    Login split-screen (DESIGN_VARIANCE: 8).
    Panel verde fijo izquierda + formulario derecha.
    El caller debe llamar st.stop() después.
    """
    # Panel de marca fijo — posicionado via CSS sobre la mitad izquierda
    st.markdown("""
<div class="login-bg-panel" aria-hidden="true">
  <div class="login-brand-eyebrow">Sistema de liquidación</div>
  <div class="login-brand-name">Rake</div>
  <div class="login-brand-desc">
    Intereses moratorios<br>por reajuste previsional
  </div>
  <div class="login-brand-tag">Uso interno · Estudio jurídico</div>
</div>
""", unsafe_allow_html=True)

    # Dos columnas: izquierda vacía (cubierta por el panel fijo), derecha el form
    _, col = st.columns([1, 1])
    with col:
        st.markdown("<div class='login-spacer'></div>", unsafe_allow_html=True)
        st.markdown("""
<div class="login-form-area">
  <p class="login-form-heading">Bienvenido</p>
  <p class="login-form-sub">Ingresá con tu cuenta para continuar</p>
</div>
""", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="usuario")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            submitted = st.form_submit_button(
                "Ingresar", use_container_width=True, type="primary"
            )
        if submitted:
            result = login(username.strip(), password)
            if result == "ok":
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
