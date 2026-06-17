from __future__ import annotations

import hashlib
import secrets
import threading
import time

# ── Constantes ────────────────────────────────────────────────────────────────
SESSION_COOKIE = "rvm_session"
_AUTH_MAX_ATTEMPTS = 10
_AUTH_LOCKOUT_SECS = 300

# ── Almacenes de sesión y fallos (estado de módulo) ───────────────────────────
_sessions: dict[str, float] = {}  # {token: expires_at (monotonic)}
_sessions_lock = threading.Lock()

_auth_failures: dict[str, list] = {}  # {ip: [monotonic_timestamp, ...]}
_auth_failures_lock = threading.Lock()


# ── PIN ───────────────────────────────────────────────────────────────────────


def hash_pin(pin: str, salt: str) -> str:
    return hashlib.sha256((pin + salt).encode()).hexdigest()


# ── Rate limiting ─────────────────────────────────────────────────────────────


def check_rate_limit(ip: str) -> bool:
    now = time.monotonic()
    with _auth_failures_lock:
        window = [t for t in _auth_failures.get(ip, []) if now - t < _AUTH_LOCKOUT_SECS]
        _auth_failures[ip] = window
        return len(window) >= _AUTH_MAX_ATTEMPTS


def record_failure(ip: str) -> None:
    with _auth_failures_lock:
        _auth_failures.setdefault(ip, []).append(time.monotonic())


def clear_failures(ip: str) -> None:
    with _auth_failures_lock:
        _auth_failures.pop(ip, None)


# ── Sesiones ──────────────────────────────────────────────────────────────────


def create_session(ttl: int) -> str:
    token = secrets.token_urlsafe(32)
    with _sessions_lock:
        _sessions[token] = time.monotonic() + ttl
    return token


def destroy_session(token: str) -> None:
    with _sessions_lock:
        _sessions.pop(token, None)


def validate_session(token: str) -> bool:
    with _sessions_lock:
        exp = _sessions.get(token)
        if exp is None:
            return False
        if time.monotonic() > exp:
            del _sessions[token]
            return False
        return True


def invalidate_all() -> None:
    with _sessions_lock:
        _sessions.clear()


# ── Página de login ───────────────────────────────────────────────────────────

LOGIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Retro Vault — Acceso</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:#0f0f0f;color:#d4d4d4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{background:#1e1e2e;border:1px solid #2a2a3a;border-radius:12px;padding:40px 36px;width:320px;text-align:center}
h1{color:#4ec9b0;font-family:Consolas,monospace;font-size:22px;letter-spacing:2px;margin-bottom:8px}
p{color:#555;font-size:13px;margin-bottom:28px}
input[type=password]{width:100%;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:12px 16px;border-radius:6px;font:inherit;font-size:18px;text-align:center;letter-spacing:8px;margin-bottom:16px;outline:none}
input[type=password]:focus{border-color:#4ec9b0}
button{width:100%;background:#1e1e2e;border:1px solid #4ec9b0;color:#4ec9b0;padding:10px;border-radius:6px;cursor:pointer;font:inherit;font-size:14px;transition:background .15s,color .15s}
button:hover{background:#4ec9b0;color:#0f0f0f}
.err{color:#f44747;font-size:12px;margin-top:10px;min-height:18px}
</style>
</head>
<body>
<div class="box">
  <h1>RETRO VAULT</h1>
  <p>Introduce el PIN para acceder</p>
  <form id="f">
    <input type="password" id="pin" placeholder="••••" maxlength="10" autocomplete="off" autofocus>
    <button type="submit">Entrar</button>
    <div class="err" id="err"></div>
  </form>
</div>
<script>
document.getElementById('f').addEventListener('submit',async function(e){
  e.preventDefault();
  const pin=document.getElementById('pin').value;
  const r=await fetch('/api/auth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin})});
  const d=await r.json();
  if(d.ok){location.href='/';}
  else{const el=document.getElementById('err');el.textContent=d.error||'PIN incorrecto';document.getElementById('pin').select();}
});
</script>
</body>
</html>"""
