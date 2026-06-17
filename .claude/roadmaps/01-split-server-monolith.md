# Roadmap — `refactor/split-server-monolith`

Objetivo: reducir `server.py` (1 446 líneas) a un ensamblador de ~200 líneas extrayendo cuatro responsabilidades a módulos propios, sin romper nada en el proceso.

**Estrategia:** movimientos incrementales, el servidor arranca y funciona después de **cada paso**. Nunca borrar código del original hasta que el destino esté importando correctamente.

---

## Mapa del archivo actual

| Bloque | Líneas | Destino |
|--------|--------|---------|
| Estado global (dicts de progreso, cancel events, jobs) | 42–179 | `web/state.py` |
| S25 auth: hashing, sesiones, rate-limit, LOGIN_HTML | 181–279 | `web/auth.py` |
| Daemons (auto-sync, SD, inbox watcher, health scheduler) | 282–289, 1157–1358 | `web/daemons.py` |
| Helpers sueltos (rclone, cloud, library doctor, setup.sh, system_status, retroarch_check) | 291–796 | `web/handlers/system.py` |
| `make_handler()` + clase `Handler` | 799–1154 | se queda en `server.py` (simplificado) |
| `serve()` | 1266–1446 | se queda en `server.py` (simplificado) |

---

## Paso 0 — Crear rama y punto de control

```bash
git checkout -b refactor/split-server-monolith
git stash  # por si hay cambios sin commitear
```

**Verificación:** `python -m rom_manager serve` arranca sin errores.

---

## Paso 1 — Extraer estado global a `web/state.py`

**Qué mover:** todo lo que hay entre las líneas 42–179 de `server.py` (dicts de progreso, cancel events, jobs, auto-sync status).

**Crear** `src/rom_manager/web/state.py`:

```python
from __future__ import annotations
import threading
from rom_manager.web.jobs.manager import JobManager

# ── Background job state ──────────────────────────────────────────────────
_job_lock = threading.Lock()
_jobs: dict[str, bool] = {
    "scan": False, "match": False, "sync": False,
    "convert_chd": False, "convert_cso": False, "scrape": False,
    "extract_zip": False, "health_check": False,
    "ra_check": False, "cable_sync": False,
    "apply": False, "inbox": False, "setup": False,
    "backup_now": False, "tree_diff": False, "verify_chd": False,
}
_job_results: dict[str, dict] = {}
_job_manager = JobManager()

# ── Progress dicts ────────────────────────────────────────────────────────
_chd_progress: dict = {}
_cso_progress: dict = {}
_scrape_progress: dict = {}
_zip_progress: dict = {}
_health_progress: dict = {}
_ra_progress: dict = {}
_cable_progress: dict = {}
_scan_progress: dict = {}
_apply_progress: dict = {}
_inbox_progress: dict = {}
_setup_progress: dict = {}
_verify_chd_progress: dict = {}
_inbox_watcher_status: dict = {
    "watching": False, "last_check": None,
    "pending_files": 0, "trigger_ts": 0,
}

# ── Cancel events ─────────────────────────────────────────────────────────
_scan_cancel   = threading.Event()
_cable_cancel  = threading.Event()
_chd_cancel    = threading.Event()
_verify_chd_cancel = threading.Event()
_cso_cancel    = threading.Event()
_zip_cancel    = threading.Event()
_health_cancel = threading.Event()
_ra_cancel     = threading.Event()
_scrape_cancel = threading.Event()
_match_cancel  = threading.Event()
_ss_last_quota: dict = {}

# ── Auto-sync / SD daemon state ───────────────────────────────────────────
_auto_sync_enabled: bool = True
_auto_sync_last_devices: set = set()
_auto_sync_status: dict = {
    "state": "waiting", "last_sync_at": None,
    "last_device": None, "last_error": None,
}
_sd_sync_status: dict = {
    "state": "waiting", "last_sync_at": None, "drive": None,
}

# ── HTTP/tray instances ───────────────────────────────────────────────────
_tray_instance = None
_httpd_instance = None
```

**En `server.py`:** reemplazar el bloque 42–179 y las declaraciones de `_job_manager`, `_tray_instance`, `_httpd_instance` por:

```python
from rom_manager.web.state import (
    _job_lock, _jobs, _job_results, _job_manager,
    _chd_progress, _cso_progress, _scrape_progress, _zip_progress,
    _health_progress, _ra_progress, _cable_progress, _scan_progress,
    _apply_progress, _inbox_progress, _setup_progress,
    _verify_chd_progress, _inbox_watcher_status,
    _scan_cancel, _cable_cancel, _chd_cancel, _verify_chd_cancel,
    _cso_cancel, _zip_cancel, _health_cancel, _ra_cancel,
    _scrape_cancel, _match_cancel, _ss_last_quota,
    _auto_sync_enabled, _auto_sync_status, _sd_sync_status,
    _tray_instance, _httpd_instance,
)
import rom_manager.web.state as _state
```

> **Nota:** los handlers que hacen `import rom_manager.web.server as _srv` y luego acceden a `_srv._cable_progress`, `_srv._job_manager`, etc., siguen funcionando porque `server.py` re-exporta los nombres. No hay que tocar esos handlers todavía.

**Commit:** `refactor: extraer estado global a web/state.py`

**Verificación:** el servidor arranca, la UI responde, los jobs de scan/sync muestran progreso.

---

## Paso 2 — Extraer auth a `web/auth.py`

**Qué mover:** líneas 181–279 de `server.py` (constantes de sesión, funciones `_hash_pin`, `_check_auth_rate_limit`, `_record_auth_failure`, `_clear_auth_failures`, `_create_session`, `_destroy_session`, `_validate_session`, `_LOGIN_HTML`).

**Crear** `src/rom_manager/web/auth.py`:

```python
from __future__ import annotations
import hashlib
import secrets
import threading
import time

_SESSION_COOKIE = "rvm_session"
_sessions: dict[str, float] = {}
_sessions_lock = threading.Lock()

_auth_failures: dict[str, list] = {}
_auth_failures_lock = threading.Lock()
_AUTH_MAX_ATTEMPTS = 10
_AUTH_WINDOW_SECS  = 60
_AUTH_LOCKOUT_SECS = 300


def hash_pin(pin: str, salt: str) -> str:
    return hashlib.sha256((pin + salt).encode()).hexdigest()


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


LOGIN_HTML = """..."""  # copiar literalmente desde server.py líneas 239-279
```

**En `server.py`:** reemplazar el bloque 181–279 y todas las llamadas internas por:

```python
from rom_manager.web import auth as _auth
_SESSION_COOKIE        = _auth._SESSION_COOKIE
_hash_pin              = _auth.hash_pin
_check_auth_rate_limit = _auth.check_rate_limit
_record_auth_failure   = _auth.record_failure
_clear_auth_failures   = _auth.clear_failures
_create_session        = _auth.create_session
_destroy_session       = _auth.destroy_session
_validate_session      = _auth.validate_session
_LOGIN_HTML            = _auth.LOGIN_HTML
_sessions              = _auth._sessions
_sessions_lock         = _auth._sessions_lock
```

> Mantener los alias `_hash_pin`, `_validate_session`, etc., garantiza que el código del `Handler` no necesita ningún cambio todavía.

**Commit:** `refactor: extraer autenticación a web/auth.py`

**Verificación:** el flujo de login/logout y el PIN funcionan.

---

## Paso 3 — Extraer helpers sueltos a `web/handlers/system.py`

**Qué mover:** líneas 291–796 de `server.py`:
- `_handle_detect_cloud_folder()`
- `_handle_rclone_export_config(config)`
- `_build_anbernic_setup_sh(config)`
- `_handle_system_status(config)`
- `_handle_rclone_status(config)`
- `_handle_library_doctor(config, repository)`
- `_handle_retroarch_check(config)`

**Crear** `src/rom_manager/web/handlers/system.py` con esas siete funciones y sus imports locales.

**En `server.py`:** reemplazar el bloque con:

```python
from rom_manager.web.handlers.system import (
    _handle_detect_cloud_folder,
    _handle_rclone_export_config,
    _build_anbernic_setup_sh,
    _handle_system_status,
    _handle_rclone_status,
    _handle_library_doctor,
    _handle_retroarch_check,
)
```

> Estas funciones no tocan estado global, solo reciben `config`/`repository` como argumentos — el movimiento es puro copy-paste más el import.

**Commit:** `refactor: extraer helpers de sistema a web/handlers/system.py`

**Verificación:** las páginas de System Status, Library Doctor y Retroarch Check responden correctamente.

---

## Paso 4 — Extraer daemons a `web/daemons.py`

**Qué mover:**
- `_health_schedule_path()`, `_read_health_schedule()`, `_write_health_schedule()`, `_health_scheduler_loop()` (líneas 1157–1263)
- La función `_inbox_watcher_with_repo` (línea 1311–1343 dentro de `serve()`) — extraerla como función de módulo
- La lógica de arranque de daemons en `serve()` (líneas 1291–1358)

**Crear** `src/rom_manager/web/daemons.py`:

```python
from __future__ import annotations
import logging
import threading
from pathlib import Path
from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository
import rom_manager.web.state as _state

_logger = logging.getLogger(__name__)
_HEALTH_CHECK_INTERVAL_DAYS = 7


def _health_schedule_path(config: AppConfig) -> Path: ...
def _read_health_schedule(config: AppConfig) -> dict: ...
def _write_health_schedule(config: AppConfig, *, ok, corrupted, missing) -> None: ...
def _health_scheduler_loop(config: AppConfig, get_repo_fn) -> None: ...
def _inbox_watcher_loop(config: AppConfig, repository: LibraryRepository) -> None: ...


def start_all(config: AppConfig, repository: LibraryRepository) -> None:
    """Arrancar todos los daemons de background. Llamado desde serve()."""
    from rom_manager.web.cable_sync_daemon import _auto_sync_loop, _sd_card_sync_loop

    if config.auto_sync_enabled:
        t = threading.Thread(target=_auto_sync_loop, args=(config, lambda: repository), daemon=True)
        t.name = "auto-sync-daemon"
        t.start()

    t_sd = threading.Thread(target=_sd_card_sync_loop, args=(config, lambda: repository), daemon=True)
    t_sd.name = "sd-sync-daemon"
    t_sd.start()

    t_inbox = threading.Thread(target=_inbox_watcher_loop, args=(config, repository), daemon=True)
    t_inbox.name = "inbox-watcher-daemon"
    t_inbox.start()

    t_health = threading.Thread(target=_health_scheduler_loop, args=(config, lambda: repository), daemon=True)
    t_health.name = "health-check-scheduler"
    t_health.start()
```

**En `serve()`** de `server.py`, reemplazar los bloques de arranque de daemons (líneas 1291–1358) por:

```python
from rom_manager.web.daemons import start_all
start_all(config, repository)
```

**Commit:** `refactor: extraer daemons de background a web/daemons.py`

**Verificación:** el inbox watcher, auto-sync y health scheduler siguen apareciendo en los logs al arrancar.

---

## Paso 5 — Limpiar `server.py`

Con los cuatro módulos ya creados, `server.py` queda como ensamblador:

```
server.py (~180 líneas):
  imports desde state, auth, daemons
  _start_job() — helper de threading
  _ES_PLATFORM_FOLDERS / _STANDARD_PLATFORM_FOLDERS — (mover a platforms.py en la rama #5)
  make_handler() — registra el router con todos los handlers
  Handler (clase HTTP) — _send, _send_json, _send_error, do_GET, do_POST
  serve() — crea el httpd, llama start_all(), arranca el tray si --tray
```

Eliminar en `server.py` los bloques ya migrados. Los alias de compatibilidad del Paso 2 se pueden mantener o eliminar según si algún handler los referencia directamente.

**Commit:** `refactor: server.py reducido a ensamblador (~180 líneas)`

---

## Paso 6 — Eliminar aliases de compatibilidad y limpiar imports

Buscar todos los usos de `_srv._cable_progress`, `_srv._job_manager`, etc. en los handlers y reemplazarlos por importaciones directas desde `state`:

```python
# Antes (en handlers/sync.py, etc.)
import rom_manager.web.server as _srv
_srv._cable_progress["current"] = ...

# Después
import rom_manager.web.state as _state
_state._cable_progress["current"] = ...
```

**Archivos a revisar:**
- `src/rom_manager/web/handlers/sync.py` (líneas 143, 357, 550, 1172)
- `src/rom_manager/web/handlers/scraper.py` (línea 87)
- `src/rom_manager/cable_sync_daemon.py` (líneas 21, 336, 486)
- `src/rom_manager/web/inbox_pipeline.py`

**Commit:** `refactor: handlers importan desde state.py en lugar de server.py`

**Verificación final:**
- `python -m rom_manager serve` arranca limpio
- `grep -r "import rom_manager.web.server" src/` devuelve solo `server.py`
- Todos los tests existentes pasan: `pytest tests/`
- La UI completa funciona: scan, sync, inbox, health, config, juegos

---

## Resultado final

```
src/rom_manager/web/
  state.py          (~80 líneas)  — toda la mutabilidad global
  auth.py           (~80 líneas)  — PIN, sesiones, rate-limit, LOGIN_HTML
  daemons.py        (~120 líneas) — health scheduler, inbox watcher, start_all()
  handlers/
    system.py       (~150 líneas) — rclone, library doctor, setup.sh, retroarch check
  server.py         (~180 líneas) — ensamblador, Handler HTTP, serve()
```

Reducción: de 1 446 líneas en un archivo a 5 archivos de <200 líneas cada uno.

---

## Consideraciones de riesgo

| Riesgo | Mitigación |
|--------|-----------|
| Los handlers acceden a `_srv.xxx` globales | Paso 6 los migra uno a uno; no romper hasta que el test pase |
| `_auto_sync_enabled` se muta en `serve()` con `global` | En `state.py` se convierte en variable de módulo; `serve()` usa `_state._auto_sync_enabled = val` |
| `_sessions` se muta directamente en `/api/set-pin` y `/api/clear-pin` | Usar `_auth.invalidate_all()` ya definido |
| Tests que parchean `server._jobs` | Actualizar los imports del mock a `state._jobs` |

---

## Checklist de progreso

- [x] Paso 0 — Rama creada, servidor arranca
- [x] Paso 1 — `web/state.py` creado, server.py importa desde él
- [x] Paso 2 — `web/auth.py` creado, login/PIN funcionan
- [x] Paso 3 — `web/handlers/system.py` creado, System Status responde
- [x] Paso 4 — `web/daemons.py` creado, daemons arrancan
- [x] Paso 5 — `server.py` 1446 → 542 líneas (re-exports de estado pendientes de limpiar en PR)
- [x] Paso 6 — Cero `import rom_manager.web.server` en handlers

---

## Estimación de tiempo

| Paso | Tiempo estimado |
|------|----------------|
| 0 — Rama y verificación | 5 min |
| 1 — `state.py` | 20 min |
| 2 — `auth.py` | 25 min |
| 3 — `handlers/system.py` | 20 min |
| 4 — `daemons.py` | 30 min |
| 5 — Limpieza de `server.py` | 15 min |
| 6 — Migrar imports de handlers | 30 min |
| **Total** | **~2.5 horas** |
