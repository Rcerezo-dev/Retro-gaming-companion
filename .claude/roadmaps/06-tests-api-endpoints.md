# Roadmap 06 — `tests/api-endpoints`

**Rama:** `tests/api-endpoints`
**Base:** `refactor/consolidate-platform-dict`
**Prioridad:** 🟠 P2
**Esfuerzo estimado:** ~3-4 h
**Riesgo:** Bajo — solo añade tests, no toca código de producción

---

## Problema

Los ~390 tests actuales cubren lógica de dominio (config, pipeline, CUE, hash, health, planner) pero casi nada de la capa web:

- `tests/test_web_server.py` ya tiene una infraestructura mínima (`FakeSocket` + `TestHandler` + `_make_request`) que ejecuta `do_GET()` sin socket real, pero **solo cubre 9 rutas GET** y no existe equivalente para `POST`.
- `Router` (`web/router.py`) no tiene tests propios: dispatch exacto, prefijo, 404 y método incorrecto no están verificados de forma aislada.
- `JobManager` (`web/jobs/manager.py`) no tiene tests propios, a pesar de ser el componente central de todos los jobs en background.
- `auth.py` (PIN, rate limit, sesiones) no tiene tests — S25 quedó sin cobertura.
- Un cambio en `router.py` o en cualquier handler puede romper la UI sin que ningún test falle.

---

## Objetivo

Crear `tests/web/` con tests aislados (sin servidor real) para: router, jobs manager, auth y los handlers HTTP más importantes (config, scan/match). Extender la infraestructura de `test_web_server.py` para soportar `POST` con cuerpo JSON.

No se requiere mock de WSGI: el patrón `FakeSocket` + subclase del `handler_class` ya funciona para `do_GET`; solo hay que generalizarlo a `do_POST`.

---

## Archivos afectados / nuevos

```
tests/
  test_web_server.py        → se mantiene (GET de alto nivel), o se migra a tests/web/test_smoke.py
  web/
    __init__.py              → vacío, para que pytest descubra el paquete
    conftest.py              → TestClient (GET + POST), fixtures repo/config
    test_router.py           → Router: dispatch, prefijos, 404, método incorrecto
    test_jobs_manager.py      → JobManager: start/already_running/progress/finish/cancel
    test_auth.py             → auth.py: hash_pin, rate limit, sesiones
    test_handlers_config.py  → GET/POST /api/config, /api/auth/status
    test_handlers_scan.py    → GET /api/job-status, POST /api/scan, POST /api/match
```

---

## Pasos

### Paso 1 — `tests/web/conftest.py`: TestClient con GET + POST

Generalizar `_make_request` de `test_web_server.py` (FakeSocket + subclase de `handler_class`) para soportar ambos verbos y devolver JSON ya decodificado:

```python
# tests/web/conftest.py
from __future__ import annotations
import io, json
from pathlib import Path
from unittest.mock import MagicMock
import pytest
from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.server import make_handler


class FakeSocket:
    def makefile(self, mode):
        return io.BytesIO(b"")


class TestClient:
    def __init__(self, repository, config):
        self._handler_class = make_handler(repository, config)

    def _request(self, method, path, json_body=None):
        body = json.dumps(json_body or {}).encode()
        captured: dict = {}

        class H(self._handler_class):
            def __init__(self):
                self.command = method
                self.path = path
                self.headers = {"Content-Length": str(len(body))}
                self.rfile = io.BytesIO(body)
                self._buf = io.BytesIO()
                self.wfile = self._buf
                self.server = MagicMock()
                self.request = FakeSocket()
                self.client_address = ("127.0.0.1", 0)

            def send_response(self, code, message=""):
                captured["code"] = code

            def send_header(self, key, value):
                if key == "Content-Type":
                    captured["content_type"] = value

            def end_headers(self):
                pass

            def log_message(self, fmt, *args):
                pass

        h = H()
        (h.do_GET if method == "GET" else h.do_POST)()
        return captured.get("code", 0), captured.get("content_type", ""), h._buf.getvalue()

    def get(self, path):
        return self._request("GET", path)

    def post(self, path, json_body=None):
        return self._request("POST", path, json_body)

    def get_json(self, path):
        _, _, body = self.get(path)
        return json.loads(body)

    def post_json(self, path, json_body=None):
        _, _, body = self.post(path, json_body)
        return json.loads(body)


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "lib.sqlite")


@pytest.fixture
def config(tmp_path: Path):
    cfg = load_config(Path(__file__).parent.parent.parent)
    cfg.library_root = str(tmp_path / "library")
    return cfg


@pytest.fixture
def client(repo, config) -> TestClient:
    return TestClient(repo, config)
```

`config.web_pin_hash` está vacío en `load_config()` por defecto → `_is_authenticated()` devuelve `True` → no hace falta simular login para los POST de test.

**Verificación:** `pytest tests/web/conftest.py` (sin tests propios, solo que importe sin error).

---

### Paso 2 — `test_router.py` (unit puro, sin HTTP)

`Router` se puede testear directamente, sin `make_handler`:

```python
from rom_manager.web.router import Router

def test_exact_match_dispatch():
    router = Router()
    called = []
    @router.get("/api/config")
    def handler(ctx): called.append(ctx)
    assert router.dispatch("GET", "/api/config", "ctx") is True
    assert called == ["ctx"]

def test_no_match_returns_false():
    router = Router()
    assert router.dispatch("GET", "/api/does-not-exist", "ctx") is False

def test_prefix_match():
    router = Router()
    called = []
    @router.get("/api/games", prefix=True)
    def handler(ctx): called.append(ctx)
    assert router.dispatch("GET", "/api/games/123", "ctx") is True

def test_wrong_method_no_match():
    router = Router()
    @router.get("/api/config")
    def handler(ctx): ...
    assert router.dispatch("POST", "/api/config", "ctx") is False

def test_routes_introspection():
    router = Router()
    @router.get("/api/a")
    def h1(ctx): ...
    @router.post("/api/b", prefix=True)
    def h2(ctx): ...
    assert router.routes() == [("GET", "/api/a"), ("POST", "/api/b*")]

def test_handler_exception_propagates():
    router = Router()
    @router.get("/api/boom")
    def handler(ctx): raise ValueError("boom")
    import pytest
    with pytest.raises(ValueError):
        router.dispatch("GET", "/api/boom", "ctx")
```

### Paso 3 — `test_jobs_manager.py` (unit puro)

```python
from rom_manager.web.jobs.manager import JobManager

def test_start_returns_started():
    jm = JobManager()
    result = jm.start("scan", lambda: None)
    assert result == {"status": "started"}

def test_start_while_running_returns_already_running():
    jm = JobManager()
    import threading
    gate = threading.Event()
    jm.start("scan", gate.wait)  # bloquea hasta que se libere
    assert jm.start("scan", lambda: None) == {"status": "already_running"}
    gate.set()

def test_update_progress_and_finish():
    jm = JobManager()
    jm.update_progress("scan", {"files_seen": 10})
    status = jm.get_status()
    assert status["scan_progress"] == {"files_seen": 10}
    jm.finish("scan", {"ok": True})
    status = jm.get_status()
    assert status["scan_progress"] is None
    assert status["scan_result"] == {"ok": True}

def test_cancel_event():
    jm = JobManager()
    assert jm.is_cancel_requested("scan") is False
    jm.cancel("scan")
    assert jm.is_cancel_requested("scan") is True

def test_get_status_shape_has_all_job_names():
    jm = JobManager()
    status = jm.get_status()
    for name in ("scan", "match", "sync", "cable_sync", "apply", "inbox"):
        assert f"{name}_running" in status
```

Usar `threading.Event` o `time.sleep` corto para el caso "already_running" — evitar condiciones de carrera frágiles (preferible un `Event` que el hilo espera explícitamente, como en el ejemplo).

### Paso 4 — `test_auth.py` (unit puro, con reset de estado de módulo)

`auth.py` tiene estado global (`_sessions`, `_auth_failures`). Usar un fixture `autouse` que lo limpie antes/después de cada test:

```python
import pytest
from rom_manager.web import auth

@pytest.fixture(autouse=True)
def _reset_auth_state():
    auth.invalidate_all()
    with auth._auth_failures_lock:
        auth._auth_failures.clear()
    yield
    auth.invalidate_all()
    with auth._auth_failures_lock:
        auth._auth_failures.clear()


def test_hash_pin_deterministic():
    assert auth.hash_pin("1234", "salt") == auth.hash_pin("1234", "salt")
    assert auth.hash_pin("1234", "salt") != auth.hash_pin("1234", "other")


def test_session_create_and_validate():
    token = auth.create_session(ttl=60)
    assert auth.validate_session(token) is True
    auth.destroy_session(token)
    assert auth.validate_session(token) is False


def test_session_expires(monkeypatch):
    import time
    token = auth.create_session(ttl=0)
    # token.expires_at == now; cualquier avance de monotonic lo expira
    monkeypatch.setattr(time, "monotonic", lambda: time.monotonic() + 1)
    assert auth.validate_session(token) is False


def test_rate_limit_blocks_after_max_attempts():
    ip = "10.0.0.1"
    for _ in range(auth._AUTH_MAX_ATTEMPTS):
        auth.record_failure(ip)
    assert auth.check_rate_limit(ip) is True
    auth.clear_failures(ip)
    assert auth.check_rate_limit(ip) is False
```

### Paso 5 — `test_handlers_config.py` (vía TestClient)

```python
def test_get_config_returns_expected_keys(client):
    data = client.get_json("/api/config")
    for key in ("library_root", "rclone_remote", "web_host", "web_port"):
        assert key in data

def test_get_auth_status_no_pin(client):
    data = client.get_json("/api/auth/status")
    assert data == {"pin_configured": False}

def test_post_config_updates_library_root(client, tmp_path):
    new_root = str(tmp_path / "new_library")
    resp = client.post_json("/api/config", {"library_root": new_root})
    assert resp.get("ok", True) is not False
    data = client.get_json("/api/config")
    assert data["library_root"] == new_root
```

> Confirmar el shape real de la respuesta de `POST /api/config` leyendo `_save_config()` en `handlers/config.py` antes de fijar el assert — puede devolver `{"ok": True}` o la config completa.

### Paso 6 — `test_handlers_scan.py` (vía TestClient + job en background)

`POST /api/scan` y `POST /api/match` lanzan un hilo vía `job_manager.start(...)`. Para no depender de timing real, usar polling corto sobre `/api/job-status` (la librería de prueba en `tmp_path` está vacía → el job termina en milisegundos):

```python
import time

def _wait_job(client, key, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = client.get_json("/api/job-status")
        if not status[f"{key}_running"]:
            return status
        time.sleep(0.02)
    raise TimeoutError(f"{key} job did not finish in {timeout}s")


def test_job_status_empty(client):
    status = client.get_json("/api/job-status")
    assert status["scan_running"] is False
    assert status["scan_result"] is None


def test_post_scan_empty_library(client, tmp_path, config):
    (tmp_path / "library").mkdir()
    resp = client.post_json("/api/scan", {})
    assert resp["status"] == "started"
    status = _wait_job(client, "scan")
    assert status["scan_result"] is not None


def test_post_match_empty_library(client):
    resp = client.post_json("/api/match", {})
    assert resp["status"] == "started"
    status = _wait_job(client, "match")
    assert status["match_result"] is not None
```

### Paso 7 — Verificación final

```bash
C:\Users\rammu\anaconda3\envs\rom_manager\python.exe -m pytest tests/web/ -v
C:\Users\rammu\anaconda3\envs\rom_manager\python.exe -m pytest tests/ -q   # 390 + nuevos, todos en verde
```

Opcional: medir cobertura de `web/` con `pytest --cov=rom_manager.web --cov-report=term-missing tests/` para confirmar el criterio de éxito (>60% en `handlers/`, `router.py`, `jobs/manager.py`, `auth.py`).

---

## Riesgos y notas

| Riesgo | Mitigación |
|--------|------------|
| `do_POST` para `/api/scan` lanza un hilo real (`threading.Thread`) | Librería de test vacía → termina casi instantáneo; usar `_wait_job` con timeout generoso (5 s) |
| Estado global de `auth.py` (`_sessions`, `_auth_failures`) contamina otros tests si se importa `rom_manager.web.server` en el mismo proceso | Fixture `autouse` que limpia antes/después (Paso 4) |
| `_job_manager` (`web/state.py`) es un **singleton de módulo** (desde rama 04), no por-instancia — todos los `WebClient` del proceso comparten el mismo `JobManager` | Fixture `autouse` `_reset_job_manager` en `conftest.py` limpia `_running`/`_results`/`_progress`/`_cancel` antes de cada test |
| El fixture `config` original (`load_config(Path(__file__).parent.parent.parent)`) usaría el **`config.toml` real del repo** como `project_root` — `POST /api/config` lo sobreescribiría | `config` usa `load_config(tmp_path)` → `write_config_toml` escribe en `tmp_path/config.toml`, aislado por test. `library_root` se asigna como `Path`, no `str` (si no, `_validate_config` falla con `'str' object has no attribute 'exists'`) |
| `TestClient` como nombre de clase dispara un `PytestCollectionWarning` (pytest la trata como clase de test por el prefijo `Test`) | Renombrada a `WebClient` |
| Dos tests fallando ya en `tests/test_scanner.py` y `tests/test_library_structure.py` (preexistentes, no relacionados) | No deben confundirse con regresiones de esta rama — ya fallan en `main` |

---

## Checklist

- [x] Paso 1 — `tests/web/conftest.py` con `WebClient` (GET + POST)
- [x] Paso 2 — `test_router.py`
- [x] Paso 3 — `test_jobs_manager.py`
- [x] Paso 4 — `test_auth.py` con reset de estado global
- [x] Paso 5 — `test_handlers_config.py`
- [x] Paso 6 — `test_handlers_scan.py`
- [x] Paso 7 — suite completa en verde (412 tests, 2 fallos preexistentes no relacionados). Cobertura opcional omitida (`pytest-cov` no instalado)
- [ ] Commit en rama, PR a main
