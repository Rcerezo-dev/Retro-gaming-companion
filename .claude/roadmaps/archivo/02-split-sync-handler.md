# Roadmap 02 — `refactor/split-sync-handler`

**Rama:** `refactor/split-sync-handler`  
**Base:** `refactor/split-server-monolith`  
**Prioridad:** 🔴 P1  
**Esfuerzo estimado:** ~2 h  
**Riesgo:** Medio — sync es la funcionalidad más crítica del app

---

## Problema

`handlers/sync.py` tiene 1 283 líneas y mezcla tres responsabilidades distintas:

| Responsabilidad | Líneas aprox. |
|----------------|---------------|
| Sincronización por cable / ADB | 560-1 096 |
| Sincronización en la nube (rclone) + auto-sync | 350-556, 260-345, 1 169-1 282 |
| RetroAchievements check | 176-255 |
| Registro de rutas (`register()`) | 17-172 |

Esto viola SRP y hace difícil leer, testear y modificar cualquiera de las tres funcionalidades de forma independiente.

---

## Objetivo

Dividir `handlers/sync.py` en tres archivos con responsabilidad única:

```
handlers/
  sync.py         — registro de rutas (thin orchestrator) + _do_ra_check
  sync_cable.py   — ADB/cable sync: _do_cable_sync, _do_tree_diff
  sync_cloud.py   — rclone/cloud + auto-sync: _do_sync, rclone helpers,
                    _do_auto_sync_save, _do_migrate_split_db
```

`sync.py` queda como fachada pública que delega en los dos nuevos módulos.

---

## Archivos afectados

| Archivo | Cambio |
|---------|--------|
| `handlers/sync.py` | Reducir a ~130 líneas: `register()` delegante + `_do_ra_check` |
| `handlers/sync_cable.py` | **Nuevo** — ~560 líneas |
| `handlers/sync_cloud.py` | **Nuevo** — ~650 líneas |

---

## Pasos

### Paso 1 — Crear `handlers/sync_cable.py`

Extraer las siguientes funciones de `sync.py`:
- `register_cable(router, *, config, repository, srv_mod, job_manager)` — rutas ADB/cable:
  `adb-devices`, `test-adb-path`, `sync-log`, `cable-sync-preview`, `cable-sync-log`, `cable-sync`, `rom-tree-diff`
- `_do_cable_sync(ctx, data, config, repository, srv_mod)` (líneas 559-1 096)
- `_do_tree_diff(ctx, data, config, job_manager)` (líneas 1 099-1 166)

```python
# handlers/sync_cable.py
from __future__ import annotations
import threading, os, shutil
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.router import Router
    from rom_manager.web.jobs.manager import JobManager
    import types


def register_cable(
    router: "Router",
    *,
    config: "AppConfig",
    repository: "LibraryRepository",
    srv_mod: "types.ModuleType",
    job_manager: "JobManager",
) -> None:
    """Register ADB / cable-sync routes on *router*."""
    ...  # route closures que llaman a _do_cable_sync y _do_tree_diff


def _do_cable_sync(...) -> None:
    ...

def _do_tree_diff(...) -> None:
    ...
```

**Verificación:** `python -c "from rom_manager.web.handlers.sync_cable import register_cable"`

---

### Paso 2 — Crear `handlers/sync_cloud.py`

Extraer las siguientes funciones de `sync.py`:
- `register_cloud(router, *, config, repository, repo_android, srv_mod, job_manager)` — rutas cloud:
  `rclone-export-config`, `rclone-status`, `rclone-open-config`, `rclone-test-remote`,
  `auto-sync-status`, `sd-sync-status`, `sync`, `auto-sync-toggle`, `auto-sync-save`, `migrate-split-db`
- `_do_sync(ctx, data, config, repository, job_manager)` (líneas 350-556)
- `_handle_rclone_export_config(config)` (líneas 260-276)
- `_handle_rclone_status(config)` (líneas 279-294)
- `_handle_rclone_open_config(config)` (líneas 297-319)
- `_handle_rclone_test_remote(config, remote)` (líneas 322-345)
- `_do_auto_sync_save(ctx, data, config, srv_mod)` (líneas 1 169-1 193)
- `_do_migrate_split_db(ctx, config, repository, repo_android)` (líneas 1 196-1 282)

```python
# handlers/sync_cloud.py
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.router import Router
    from rom_manager.web.jobs.manager import JobManager
    import types


def register_cloud(
    router: "Router",
    *,
    config: "AppConfig",
    repository: "LibraryRepository",
    repo_android: "LibraryRepository",
    srv_mod: "types.ModuleType",
    job_manager: "JobManager",
) -> None:
    """Register rclone / cloud-sync / auto-sync routes on *router*."""
    ...

def _do_sync(...) -> None: ...
def _handle_rclone_export_config(...): ...
def _handle_rclone_status(...): ...
def _handle_rclone_open_config(...): ...
def _handle_rclone_test_remote(...): ...
def _do_auto_sync_save(...) -> None: ...
def _do_migrate_split_db(...) -> None: ...
```

**Verificación:** `python -c "from rom_manager.web.handlers.sync_cloud import register_cloud"`

---

### Paso 3 — Reducir `handlers/sync.py` a thin orchestrator

`sync.py` pasa a:
1. Importar `register_cable` y `register_cloud`
2. La función `register()` llama a ambas
3. Conserva solo `_do_ra_check()` (función standalone, ~80 líneas)

```python
# handlers/sync.py  (después del refactor — ~130 líneas)
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    ...

from rom_manager.web.handlers.sync_cable import register_cable
from rom_manager.web.handlers.sync_cloud import register_cloud


def register(router, *, config, repository, repo_android,
             start_ra_check_fn, srv_mod, job_manager) -> None:
    register_cable(router, config=config, repository=repository,
                   srv_mod=srv_mod, job_manager=job_manager)
    register_cloud(router, config=config, repository=repository,
                   repo_android=repo_android, srv_mod=srv_mod,
                   job_manager=job_manager)

    # ── POST /api/ra-check ───────────────────────────────────────────
    @router.post("/api/ra-check")
    def post_ra_check(ctx) -> None:
        ...


def _do_ra_check(api_key, config, repository, job_manager) -> dict:
    ...
```

**Verificación:** el servidor arranca sin errores.

---

### Paso 4 — Tests y verificación final

```bash
# Arrancar servidor
scripts\rommgr.cmd serve

# En otro terminal: smoke test de los endpoints clave
curl -s http://127.0.0.1:7777/api/adb-devices
curl -s http://127.0.0.1:7777/api/rclone-status
curl -s http://127.0.0.1:7777/api/auto-sync-status

# Tests unitarios
C:\Users\rammu\anaconda3\envs\rom_manager\python.exe -m pytest tests/ -x -q
```

Criterio de éxito: 390+ tests pasan, servidor arranca, tres endpoints responden JSON.

---

## Tabla de riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| `srv_mod` referenciado en `_do_cable_sync` via `m = srv_mod` | Alta | Mantener la firma `srv_mod` en `register_cable` y `_do_cable_sync` |
| `import rom_manager.web.state as _srv13` dentro de `_do_sync` | Baja | Ya está migrado a `_state`, no hay circular import |
| Tests de integración que importen `_do_cable_sync` directamente desde `sync` | Baja | grep previo para confirmar — ninguno importa directamente |

---

## Checklist

- [x] Paso 1 — `sync_cable.py` creado, importa correctamente
- [x] Paso 2 — `sync_cloud.py` creado, importa correctamente
- [x] Paso 3 — `sync.py` reducido a ~130 líneas
- [x] Paso 4 — servidor arranca, smoke tests pasan, 390+ tests pasan
- [ ] Commit en rama, PR a main
