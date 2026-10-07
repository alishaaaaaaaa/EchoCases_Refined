"""
Authentication, role-based access control and audit logging for EchoCases.

- Users live in a local SQLite database (echocases.db) with salted, hashed
  passwords (werkzeug's scrypt). Nobody can sign up through the API: an admin
  creates accounts with manage_users.py or the admin API.
- Logging in returns a signed JWT that expires after TOKEN_HOURS. Every API
  request must send it as `Authorization: Bearer <token>`.
- Each request re-checks the user in the database, so deactivating a user,
  changing their role or resetting their password takes effect immediately
  (resets bump token_version, which invalidates older tokens).
- Two roles: "investigator" can read cases and run analysis; "admin" can also
  upload datasets, manage users and read the audit log.
- Every protected request, denied request and login attempt is written to an
  audit_log table.
"""

import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import g, has_request_context, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

ROLES = ("investigator", "admin")
TOKEN_HOURS = 8
MIN_PASSWORD_LENGTH = 12

# Login throttling: this many failures for one username from one IP within
# the window locks that pair out for the rest of the window.
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 15 * 60

DB_PATH = os.environ.get(
    "ECHOCASES_DB",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "echocases.db"),
)

# Used to spend the same time on unknown usernames as on wrong passwords, so
# response timing doesn't reveal which usernames exist.
_DUMMY_HASH = generate_password_hash("not-a-real-password")
_failed_logins = {}  # (username, ip) -> [timestamps]


# --- database ------------------------------------------------------------------

def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role          TEXT NOT NULL CHECK (role IN ('investigator', 'admin')),
                active        INTEGER NOT NULL DEFAULT 1,
                token_version INTEGER NOT NULL DEFAULT 0,
                created_at    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT NOT NULL,
                username  TEXT,
                role      TEXT,
                action    TEXT NOT NULL,
                target    TEXT,
                status    INTEGER,
                ip        TEXT
            );
        """)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_password(password):
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")


def create_user(username, password, role):
    username = username.strip()
    if not username:
        raise ValueError("Username is required.")
    if role not in ROLES:
        raise ValueError(f"Role must be one of: {', '.join(ROLES)}.")
    validate_password(password)
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (username, generate_password_hash(password), role, _now()),
            )
    except sqlite3.IntegrityError:
        raise ValueError(f"User '{username}' already exists.")


def get_user(username):
    with _connect() as conn:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def list_users():
    with _connect() as conn:
        rows = conn.execute(
            "SELECT username, role, active, created_at FROM users ORDER BY username"
        ).fetchall()
    return [dict(r) for r in rows]


def set_password(username, password):
    validate_password(password)
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE users SET password_hash = ?, token_version = token_version + 1 WHERE username = ?",
            (generate_password_hash(password), username),
        )
    if cur.rowcount == 0:
        raise ValueError(f"No user '{username}'.")


def set_active(username, active):
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE users SET active = ?, token_version = token_version + 1 WHERE username = ?",
            (1 if active else 0, username),
        )
    if cur.rowcount == 0:
        raise ValueError(f"No user '{username}'.")


def set_role(username, role):
    if role not in ROLES:
        raise ValueError(f"Role must be one of: {', '.join(ROLES)}.")
    with _connect() as conn:
        cur = conn.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
    if cur.rowcount == 0:
        raise ValueError(f"No user '{username}'.")


def audit(action, username=None, role=None, target=None, status=None):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO audit_log (ts, username, role, action, target, status, ip) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (_now(), username, role, action, target, status,
             request.remote_addr if has_request_context() else None),
        )


def recent_audit(limit=200):
    with _connect() as conn:
        rows = conn.execute(
            "SELECT ts, username, role, action, target, status, ip FROM audit_log "
            "ORDER BY id DESC LIMIT ?", (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


# --- tokens --------------------------------------------------------------------

def _secret():
    secret = os.environ.get("ECHOCASES_SECRET_KEY", "")
    if len(secret) < 32:
        raise RuntimeError(
            "ECHOCASES_SECRET_KEY must be set to a random value of at least 32 characters. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return secret


def issue_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["username"],
        "ver": user["token_version"],
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_HOURS),
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")


def _user_from_request():
    """The active user for this request's bearer token, or None."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(header[7:], _secret(), algorithms=["HS256"],
                             options={"require": ["exp", "sub", "ver"]})
    except jwt.InvalidTokenError:
        return None
    user = get_user(payload["sub"])
    if user is None or not user["active"] or user["token_version"] != payload["ver"]:
        return None
    return user


# --- login ---------------------------------------------------------------------

def _locked_out(key):
    cutoff = time.time() - LOCKOUT_SECONDS
    attempts = [t for t in _failed_logins.get(key, []) if t > cutoff]
    _failed_logins[key] = attempts
    return len(attempts) >= MAX_FAILED_LOGINS


def login():
    """POST /api/auth/login with JSON {username, password}."""
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    key = (username.lower(), request.remote_addr)

    if _locked_out(key):
        audit("login_locked", username=username, status=429)
        return jsonify({"error": "Too many failed attempts. Try again later."}), 429

    user = get_user(username) if username else None
    password_ok = check_password_hash(user["password_hash"] if user else _DUMMY_HASH, password)

    if not user or not password_ok or not user["active"]:
        _failed_logins.setdefault(key, []).append(time.time())
        audit("login_failed", username=username, status=401)
        return jsonify({"error": "Invalid username or password."}), 401

    _failed_logins.pop(key, None)
    audit("login", username=user["username"], role=user["role"], status=200)
    return jsonify({
        "token": issue_token(user),
        "user": {"username": user["username"], "role": user["role"]},
        "expires_in_hours": TOKEN_HOURS,
    })


# --- access control ------------------------------------------------------------

def require_role(*roles):
    """
    Route decorator. Requires a valid token; if roles are given, the user must
    have one of them (admins pass every check). Sets g.user.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            action = f"{request.method} {request.url_rule.rule if request.url_rule else request.path}"
            target = next(iter(kwargs.values()), None)
            user = _user_from_request()
            if user is None:
                audit(action, target=target, status=401)
                return jsonify({"error": "Authentication required."}), 401
            if roles and user["role"] not in roles and user["role"] != "admin":
                audit(action, username=user["username"], role=user["role"], target=target, status=403)
                return jsonify({"error": "You do not have permission to do this."}), 403
            g.user = user
            response = view(*args, **kwargs)
            status = response[1] if isinstance(response, tuple) else getattr(response, "status_code", 200)
            audit(action, username=user["username"], role=user["role"], target=target, status=status)
            return response
        return wrapper
    return decorator
