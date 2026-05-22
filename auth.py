"""
auth.py — Autenticación y gestión de usuarios RASTRILLA
SQLite + Railway Volume (/data/rastrilla.db en producción)
"""
import hashlib
import os
import secrets
import sqlite3
from datetime import date
from pathlib import Path

import streamlit as st

# En Railway: variable de entorno DB_PATH=/data/rastrilla.db + Volume montado en /data
DB_PATH = Path(os.getenv("DB_PATH", "rastrilla.db"))


# ── Base de datos ─────────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Crea la tabla de usuarios si no existe. Inserta admin y testuser por defecto."""
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
                bloqueado         INTEGER NOT NULL DEFAULT 0
            )
        """)
        hoy = date.today().isoformat()
        for username, password, rol, nombre in [
            ("admin",    "Admin2025!", "admin",   "Administrador"),
            ("testuser", "Test2025",   "cliente", "Usuario de Prueba"),
        ]:
            existe = c.execute(
                "SELECT 1 FROM usuarios WHERE username = ?", (username,)
            ).fetchone()
            if not existe:
                c.execute(
                    """INSERT INTO usuarios
                       (username, password_hash, rol, nombre, fecha_contrato, dia_pago)
                       VALUES (?, ?, ?, ?, ?, 1)""",
                    (username, _hash(password), rol, nombre, hoy),
                )


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


def set_bloqueado(username: str, bloqueado: bool) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE usuarios SET bloqueado = ? WHERE username = ?",
            (int(bloqueado), username),
        )


def registrar_pago(username: str) -> None:
    """Marca el pago del mes actual y desbloquea la cuenta."""
    with _conn() as c:
        c.execute(
            "UPDATE usuarios SET fecha_ultimo_pago = ?, bloqueado = 0 WHERE username = ?",
            (date.today().isoformat(), username),
        )


# ── Auto-bloqueo ──────────────────────────────────────────────────────────────

def _debe_autobloquear(user: dict) -> bool:
    """True si el cliente no pagó este mes y ya pasó el día 10."""
    if user["rol"] == "admin":
        return False
    today = date.today()
    if today.day <= 10:
        return False
    if not user["fecha_ultimo_pago"]:
        return True
    last = date.fromisoformat(user["fecha_ultimo_pago"])
    return last < date(today.year, today.month, 1)


# ── Sesión ────────────────────────────────────────────────────────────────────

def get_session_user() -> dict | None:
    return st.session_state.get("usuario")


def login(username: str, password: str) -> str:
    """
    Retorna: 'ok' | 'no_user' | 'bad_pass' | 'bloqueado'
    Aplica auto-bloqueo si corresponde.
    """
    user = get_user(username)
    if not user:
        return "no_user"
    if not _verify(password, user["password_hash"]):
        return "bad_pass"
    if _debe_autobloquear(user):
        set_bloqueado(username, True)
        user["bloqueado"] = 1
    if user["bloqueado"]:
        return "bloqueado"
    st.session_state["usuario"] = user
    return "ok"


def logout() -> None:
    st.session_state.pop("usuario", None)
    st.rerun()


# ── UI de login ───────────────────────────────────────────────────────────────

def render_login() -> None:
    """Muestra el formulario de login. El caller debe llamar st.stop() después."""
    col = st.columns([1, 2, 1])[1]
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## ⚖️ RASTRILLA")
        st.markdown("**Intereses Moratorios — Uso Interno**")
        st.divider()
        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)
        if submitted:
            result = login(username.strip(), password)
            if result == "ok":
                st.rerun()
            elif result == "bloqueado":
                st.error("⛔ Cuenta bloqueada. Contactá al administrador.")
            else:
                st.error("Usuario o contraseña incorrectos.")
