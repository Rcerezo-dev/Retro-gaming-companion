# Roadmap 09 — `refactor/config-handler-split`

**Rama:** `refactor/config-handler-split`
**Base:** `develop`
**Prioridad:** 🟡 P3
**Esfuerzo estimado:** ~1-1.5 h
**Riesgo:** Muy bajo — mueve código sin cambiar lógica, ninguna ruta HTTP
cambia de URL ni de forma; `server.py` no necesita tocarse (ver Objetivo)

---

## Origen

`.claude/mejoras-por-rama.md` (sección 9) describía `handlers/config.py` como
372 líneas mezclando "settings generales, PIN/auth, gestión de logs,
herramientas externas (adb, rclone)". Siguiendo la regla del proyecto
"investigar antes de arreglar" (`CLAUDE.md`) y el precedente de los roadmaps
07/08 (verificar contra el código real, no contra el documento viejo): hoy
el archivo tiene **485 líneas** (creció, no encogió) y la mezcla real de
responsabilidades es distinta a la descrita — no hay lógica de PIN/auth aquí
(solo un booleano en `/api/auth/status`; la verificación real del PIN vive
en `server.py`, fuera del alcance de esta rama) ni "gestión de logs".

Leído el archivo completo (`src/rom_manager/web/handlers/config.py`), la
mezcla real es:

1. **Configuración general** — `/api/config` (GET/POST), `_save_config()`
   (persistir `config.toml` + recargar en memoria, patrón `CLEAN-1` ya
   documentado en `CLAUDE.md`), `/api/device-status`, `/api/auth/status`.
2. **Detección de herramientas/hardware** — `_detect_retroarch_install()`
   (81 líneas: escanea rutas de RetroArch en Windows, Steam vdf, RetroBat),
   `_detect_android_ra_config_dir()` (ADB), `_test_binary_status()`
   (versión de un binario externo, usado por chdman/maxcso),
   `_detect_wizard()` (combina las dos detecciones anteriores para el
   asistente de primer arranque).
3. **Selectores de archivo nativos** — `_browse_folder()`/`_browse_file()`
   (diálogos tkinter), sin relación semántica con "configuración" — son un
   utility de UI que la config solo usa de paso.
4. **Estado de salud programado** — `_read_health_schedule()` (calcula
   `next_run_at`/`overdue` para `/api/health-schedule`).
5. **Autostart** — toggle de arranque con Windows (`utils.tray_icon`).

**Hallazgo adicional no documentado en el plan original**: `_read_health_schedule()`
está **duplicada** — existe una segunda implementación independiente en
`src/rom_manager/web/daemons.py:25` (usada por el daemon de health-check
programado, `S37-1`). No son idénticas: la de `daemons.py` devuelve el JSON
crudo; la de `config.py` añade el cálculo de `next_run_at`/`overdue` para la
respuesta de la API. Pero ambas re-implementan el mismo "leer
`health_schedule.json`, `except Exception: _logger.debug(...)`" — viola
DRY/SRP (`CLAUDE.md`: "Usa siempre los principios SOLID"). Se corrige de paso
en el Paso 3 sin cambiar el contrato de `/api/health-schedule`.

El patrón de split ya tiene precedente exacto en el proyecto — el roadmap 02
(`refactor/split-sync-handler`, completado) dejó `handlers/sync.py` como
punto de entrada fino que delega en `register_cable()`/`register_cloud()`/
`register_cloud_auth()` de módulos hermanos, todo llamado desde un único
`register()` que es lo único que `server.py` conoce. Este roadmap replica
exactamente ese patrón para `config.py`.

---

## Objetivo

Dividir `config.py` en 3 archivos por responsabilidad, sin que `server.py`
note la diferencia — sigue llamando `_h_config.register(router, config=config,
set_auto_sync_fn=...)` exactamente igual que hoy (línea 118 de
`web/server.py`), porque `config.py::register()` es quien delega
internamente, igual que ya hace `handlers/sync.py::register()`.

No tocar: la lógica de PIN (vive en `server.py`, fuera de alcance — el plan
original lo asignaba a la rama `#1`, ya completada, y no lo hizo; no es
trabajo de esta rama arreglarlo), ningún contrato de API (mismas rutas,
mismos parámetros, misma forma de respuesta), `wizard.py` (CLI, archivo
distinto, no relacionado).

---

## Pasos

### Paso 1 — `web/handlers/config_tools.py` (nuevo, ~210 líneas)

Mover tal cual (sin cambios de lógica):
- `_detect_retroarch_install()` (líneas 139-219 actuales)
- `_detect_android_ra_config_dir()` (líneas 222-248)
- `_test_binary_status()` (líneas 392-409)
- `_detect_wizard()` (líneas 251-279) — depende de `_detect_retroarch_install`
  (misma función, ahora en el mismo archivo) y de `adb_transport.list_devices`

Nueva función `register_tools(router, *, config)` con las 5 rutas que hoy
registra `config.py::register()` para estas responsabilidades:
`GET /api/test-chdman`, `GET /api/test-maxcso`, `GET /api/detect-retroarch`,
`GET /api/detect-android-ra-config-dir`, `GET /api/wizard-detect` — mover
los cuerpos de esos closures tal cual desde `config.py:52-125` (imports
locales de `adb_transport` incluidos, sin cambios).

```python
# config_tools.py — forma esperada
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.sync.adb_transport import AdbTransport
    from rom_manager.web.router import Router


def register_tools(router: Router, *, config: AppConfig) -> None:
    @router.get("/api/wizard-detect")
    def get_wizard_detect(ctx) -> None:
        ctx._send_json(_detect_wizard(config))

    @router.get("/api/test-chdman")
    def get_test_chdman(ctx) -> None:
        ...  # cuerpo sin cambios

    @router.get("/api/test-maxcso")
    def get_test_maxcso(ctx) -> None:
        ...

    @router.get("/api/detect-retroarch")
    def get_detect_retroarch(ctx) -> None:
        ctx._send_json(_detect_retroarch_install())

    @router.get("/api/detect-android-ra-config-dir")
    def get_detect_android_ra_config_dir(ctx) -> None:
        ...


def _detect_retroarch_install() -> dict: ...
def _detect_android_ra_config_dir(config: AppConfig, adb_transport: AdbTransport | None) -> dict: ...
def _detect_wizard(config: AppConfig) -> dict: ...
def _test_binary_status(path_str: str) -> dict: ...
```

### Paso 2 — `web/handlers/config_dialogs.py` (nuevo, ~100 líneas)

Mover tal cual `_browse_folder()` y `_browse_file()` (líneas 412-485
actuales) más una nueva `register_dialogs(router)` con
`GET /api/browse-folder`/`GET /api/browse-file` (cuerpos de
`config.py:127-133`). No necesita `config` — son diálogos de SO puros, sin
estado de la app.

### Paso 3 — Trimear `config.py` a lo que de verdad es "configuración" (~170 líneas)

Se quedan: `register()` (ahora delega en los dos nuevos módulos, ver abajo),
`_save_config()`, `_read_health_schedule()`, y los closures inline de
`/api/config`, `/api/device-status`, `/api/auth/status`,
`/api/autostart-status`/`/api/autostart-toggle` (ya son pequeños, no
justifican archivo propio).

```python
# config.py — register() después del split
from rom_manager.web.handlers.config_dialogs import register_dialogs
from rom_manager.web.handlers.config_tools import register_tools


def register(router, *, config, set_auto_sync_fn) -> None:
    from rom_manager.web.builders.misc import _build_config

    register_tools(router, config=config)
    register_dialogs(router)

    @router.get("/api/config")
    def get_config(ctx) -> None: ...
    # ... resto de closures que se quedan, sin cambios
```

De paso, corregir la duplicación con `daemons.py` encontrada en el Origen:
`_read_health_schedule()` deja de releer el JSON a mano y reutiliza el
lector crudo ya existente.

```python
# Antes (config.py:357-368):
def _read_health_schedule(config: AppConfig) -> dict:
    import datetime as _dt
    import json as _json

    _INTERVAL_DAYS = 7
    p = config.data_dir / "health_schedule.json"
    try:
        data = _json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        _logger.debug("No se pudo leer health_schedule.json", exc_info=True)
        data = {}
    ...

# Después:
def _read_health_schedule(config: AppConfig) -> dict:
    import datetime as _dt

    from rom_manager.web.daemons import _read_health_schedule as _read_raw
    from rom_manager.web.daemons import _HEALTH_CHECK_INTERVAL_DAYS as _INTERVAL_DAYS

    data = _read_raw(config)
    ...  # el resto (cálculo de next_run_at/overdue) sin cambios
```

Nombres iguales (`_read_health_schedule`, mismo módulo `daemons.py` ya sin
ciclo — `daemons.py` no importa `handlers/config.py`, confirmar con
`grep -n "^import\|^from" src/rom_manager/web/daemons.py` antes de aplicar
por si acaso). Sin este paso el split ya vale por sí solo — es una mejora
que aparece de encontrarse con el código, no un requisito del split; si al
verificar el import resulta más frágil de lo esperado, se puede dejar fuera
sin invalidar el resto de la rama.

### Paso 4 — Actualizar imports en tests existentes

Estos tests importan funciones "privadas" directamente del módulo viejo —
deben apuntar al nuevo:

- `tests/test_detect_android_ra_config_dir.py:10` —
  `from rom_manager.web.handlers.config import _detect_android_ra_config_dir`
  → `from rom_manager.web.handlers.config_tools import _detect_android_ra_config_dir`
- `tests/test_detect_retroarch.py:16` —
  `from rom_manager.web.handlers.config import _detect_retroarch_install`
  → `from rom_manager.web.handlers.config_tools import _detect_retroarch_install`
- `tests/web/test_browse_file.py:15` —
  `from rom_manager.web.handlers import config as cfg_handler`
  → `from rom_manager.web.handlers import config_dialogs as cfg_handler`
  (los usos posteriores, `cfg_handler._browse_file(...)`, no cambian —
  siguen siendo el mismo nombre de función en el nuevo módulo)
- `tests/web/test_browse_folder.py` — mismo cambio de import que arriba

`tests/web/test_handlers_config.py` usa el fixture HTTP `client` (sin
importar módulos internos) — no necesita ningún cambio, es la prueba de que
el contrato de API no se movió.

### Paso 5 — Verificación

```bash
grep -n "^import\|^from" src/rom_manager/web/daemons.py  # confirmar sin ciclo antes del Paso 3

wc -l src/rom_manager/web/handlers/config.py src/rom_manager/web/handlers/config_tools.py src/rom_manager/web/handlers/config_dialogs.py
# esperado: los 3 por debajo o cerca de 200 líneas (config_tools puede
# quedar unos ~10 por encima — no forzar un split artificial solo por la
# cifra exacta si la responsabilidad ya es coherente)

python -m pytest tests/ -q
ruff check src/rom_manager/web/handlers/config.py src/rom_manager/web/handlers/config_tools.py src/rom_manager/web/handlers/config_dialogs.py src/rom_manager/web/daemons.py
ruff format --check src/rom_manager/web/handlers/config.py src/rom_manager/web/handlers/config_tools.py src/rom_manager/web/handlers/config_dialogs.py src/rom_manager/web/daemons.py

python -m rom_manager serve  # arranque manual: confirmar que /api/config,
# /api/wizard-detect y /api/browse-folder siguen respondiendo (server.py no
# cambia, pero es la única forma de confirmar que el wiring real no se rompió)
```

No requiere hardware ni dispositivo Android conectado — todo el split es
reorganización de código puro sobre funciones ya testeadas.

---

## Fuera de alcance (documentado aparte, no entra en esta rama)

- Mover la lógica de PIN de `server.py` a un `auth.py` propio — trabajo de
  la rama `#1` (`refactor/split-server-monolith`, ya completada sin este
  punto) que nunca se hizo; decidir aparte si vale la pena abrirlo ahora.
- Autostart (`/api/autostart-status`/`toggle`) se queda en `config.py` — es
  pequeño (~20 líneas) y no encaja mejor en `config_tools.py` (no es
  detección de hardware externo) ni merece un 4º archivo por sí solo.
- Cualquier cambio de comportamiento en `_save_config()` (la lista
  `allowed` de campos, la recarga en memoria) — se mueve tal cual, cero
  cambios de lógica.

---

## Checklist

- [ ] Paso 1 — `config_tools.py` con `register_tools()` + las 4 funciones de detección/test
- [ ] Paso 2 — `config_dialogs.py` con `register_dialogs()` + `_browse_folder`/`_browse_file`
- [ ] Paso 3 — `config.py` trimeado, delega en los dos nuevos módulos; `_read_health_schedule()` reutiliza el lector crudo de `daemons.py`
- [ ] Paso 4 — imports de tests actualizados (4 archivos)
- [ ] Paso 5 — tests + ruff + format limpios, arranque manual confirmado
- [ ] Commit en rama, PR a `develop`
