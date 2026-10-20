# Retro Vault — Plan de mejoras por rama

Análisis realizado: 2026-06-15. Basado en escaneo completo del código fuente (~20 k líneas Python, ~10 k JS).

---

## Índice de ramas propuestas

| Rama | Prioridad | Esfuerzo | Riesgo |
|------|-----------|----------|--------|
| [refactor/split-server-monolith](#1-refactorsplit-server-monolith) | 🔴 P1 | 3-4 h | Alto |
| [refactor/split-sync-handler](#2-refactorsplit-sync-handler) | 🔴 P1 | 2-3 h | Medio |
| [refactor/eliminate-late-imports](#3-refactoreliminate-late-imports) | 🟠 P2 | 2-3 h | Medio |
| [refactor/consolidate-state](#4-refactorconsolidate-state) | 🟠 P2 | 2-3 h | Medio |
| [refactor/consolidate-platform-dict](#5-refactorconsolidate-platform-dict) | 🟠 P2 | 1 h | Bajo |
| [tests/api-endpoints](#6-testsapi-endpoints) | 🟠 P2 | 3-4 h | Bajo |
| [fix/remove-debug-prints](#7-fixremove-debug-prints) | 🟡 P3 | 30 min | Bajo |
| [fix/error-handling](#8-fixerror-handling) | 🟡 P3 | 2 h | Bajo |
| [refactor/config-handler-split](#9-refactorconfig-handler-split) | 🟡 P3 | 1-2 h | Bajo |
| [i18n/translate-remaining-strings](#10-i18ntranslate-remaining-strings) | 🟡 P3 | 1 h | Bajo |

---

## 1. `refactor/split-server-monolith`

**Problema:** `server.py` tiene 1 446 líneas y viola SRP: contiene router, autenticación PIN, daemons de background (auto-sync, inbox watcher, health scheduler), ~15 diccionarios de estado global y helpers que generan scripts shell.

**Acción:**

```
web/
  server.py          → solo entry point: importa y ensambla
  auth.py            → S25: PIN, sesiones, rate limit, logout
  daemons.py         → auto-sync loop, inbox watcher, health scheduler
  state.py           → definición de todos los dicts de progreso y jobs
```

**Archivos afectados:**
- `src/rom_manager/web/server.py` (principal)
- `src/rom_manager/web/handlers/*.py` (importan `_srv`)
- `src/rom_manager/cable_sync_daemon.py` (importa `_srv`)
- `src/rom_manager/inbox_pipeline.py` (importa `_srv`)

**Criterio de éxito:** `server.py` < 200 líneas. Todos los tests existentes pasan. Los late imports a `_srv` se reducen a cero o apuntan solo a `state.py`.

---

## 2. `refactor/split-sync-handler`

**Problema:** `handlers/sync.py` tiene 1 282 líneas con lógica mezclada de ADB (cable sync), rclone (cloud) y auto-sync.

**Acción:**

```
handlers/
  sync.py            → punto de registro: importa y re-exporta rutas
  sync_cable.py      → ADB devices, cable sync progress, ops log
  sync_cloud.py      → rclone config, remote list, auto-sync toggle
```

**Archivos afectados:**
- `src/rom_manager/web/handlers/sync.py`
- `src/rom_manager/web/router.py` (registro de rutas)

**Criterio de éxito:** Cada nuevo archivo < 450 líneas. Ninguna función de cable toca lógica rclone y viceversa.

---

## 3. `refactor/eliminate-late-imports`

**Problema:** Hay al menos 8 late imports de `rom_manager.web.server` dentro de funciones, síntoma de dependencias circulares. Dificulta testing unitario porque importar un módulo tiene efectos secundarios.

**Puntos concretos:**
- `cable_sync_daemon.py` líneas 21, 336, 486
- `handlers/sync.py` líneas 143, 357, 550, 1172
- `handlers/scraper.py` línea 87

**Acción:** Extraer el estado compartido a `web/state.py` (ver rama #1) y que cada módulo importe solo desde `state.py`, eliminando la circularidad.

**Criterio de éxito:** `grep -r "import rom_manager.web.server"` devuelve 0 resultados en módulos que no son entry points.

---

## 4. `refactor/consolidate-state`

**Problema:** ~15 diccionarios de estado global en `server.py` (líneas 44–177) son accedidos directamente desde múltiples módulos, sin contrato claro ni sincronización documentada.

```python
# Situación actual — disperso en server.py
_jobs = {}
_job_results = {}
_chd_progress = {}
_cable_progress = {}
_scan_progress = {}
# ...
```

**Acción:** Crear `web/state.py` con una clase `AppState` o simplemente un módulo-singleton con todos los dicts documentados. Las funciones que los mutan reciben `state` como argumento (inyección) en lugar de importar el módulo global.

**Criterio de éxito:** Todas las referencias a `_jobs`, `_cable_progress`, etc. pasan por `state.*` o se inyectan como parámetros. El estado puede resetearse en tests sin side effects.

---

## 5. `refactor/consolidate-platform-dict`

**Problema:** El diccionario de plataformas/carpetas (`_PLATFORM_FOLDERS` o equivalente) aparece duplicado en al menos 3 archivos:
- `server.py` ~línea 77
- `inbox_pipeline.py` líneas 19–47
- posiblemente `collection.py`

Cada copia puede divergir silenciosamente.

**Acción:** Mover la definición canónica a `config.py` o a un nuevo `platforms.py` compartido. Todos los módulos importan de ahí.

**Criterio de éxito:** Una sola definición. `grep "_PLATFORM_FOLDERS"` (o el nombre real) devuelve una definición y N importaciones.

---

## 6. `tests/api-endpoints`

**Problema:** Los tests actuales cubren lógica de dominio (config, pipeline, CUE, hash, health, operaciones) pero no los endpoints web. Un cambio en `router.py` o en un handler puede romper la UI sin que ningún test falle.

**Acción:** Crear `tests/web/` con:
- `test_router.py` — dispatching correcto, 404, métodos no permitidos
- `test_handlers_scan.py` — GET/POST `/api/scan`, `/api/match`
- `test_handlers_config.py` — GET/POST `/api/config`, validaciones
- `test_jobs.py` — `JobManager`: start, progress, finish, cancel, timeout
- `test_auth.py` — login correcto, login fallido, rate limit, sesión expirada

**Criterio de éxito:** Coverage de handlers > 60 %. Los tests corren sin servidor real (mock de WSGI o TestClient).

---

## 7. `fix/remove-debug-prints`

**Problema:** `server.py` líneas 831–835 contienen 4 sentencias `print()` con prefijo `[DEBUG]` en código de producción.

**Acción:** Reemplazar cada `print(f"[DEBUG] ...")` por `_logger.debug(...)`. Auditar el resto del proyecto con `grep -rn "print(" src/` para detectar más casos.

**Criterio de éxito:** Cero `print()` en código de producción fuera de scripts de desarrollo.

---

## 8. `fix/error-handling`

**Problema:** Varios bloques `except Exception` tragan el error sin logging útil ni propagación:
- `cable_sync_daemon.py` línea 322: `except Exception: _logger.debug(...)` (nivel debug insuficiente para errores)
- `handlers/sync.py`: múltiples bloques que capturan `Exception` genérica
- `inbox_pipeline.py`: varios `.get()` sin validación de claves

**Acción:**
1. Cambiar `_logger.debug` a `_logger.exception` en bloques de error (incluye stack trace)
2. Capturar excepciones específicas donde sea posible (`OSError`, `KeyError`, etc.)
3. Añadir validación de claves con mensajes de error claros en `inbox_pipeline.py`

**Criterio de éxito:** Ningún `except Exception: pass` o `except Exception: logger.debug`. Todos los errores producen al menos un log de nivel WARNING con stack trace.

---

## 9. `refactor/config-handler-split`

**Problema:** `handlers/config.py` (372 líneas) mezcla responsabilidades: settings generales, PIN/auth, gestión de logs, herramientas externas (adb, rclone).

**Acción:**

```
handlers/
  config.py          → settings generales, library root, web port
  config_tools.py    → verificación de adb, rclone, chdman
```

La lógica de PIN puede moverse a `auth.py` (rama #1).

**Criterio de éxito:** Cada archivo < 200 líneas, responsabilidad única verificable.

---

## 10. `i18n/translate-remaining-strings`

**Problema:** Algunos strings de la UI siguen en inglés:
- `js/tabs/esde.js` líneas 447, 651, 708, 713: comentarios `// TODO: Implement...`
- Mensajes de error generados en Python que llegan al frontend en inglés
- `main.js` línea 655: comentario en inglés en código de producción

**Acción:**
1. Pasar el script `/localization-pass` sobre `frontend.py` y los `.js`
2. Reemplazar mensajes de error en `handlers/*.py` que usen inglés
3. Eliminar o traducir los TODO de `esde.js`

**Criterio de éxito:** `grep -rn '"[A-Z][a-z]' src/rom_manager/web/static/js/` no devuelve strings de UI en inglés (solo identificadores técnicos aceptables como SHA1, ADB, API).

---

## Orden de trabajo recomendado

```
Semana 1 (deuda técnica crítica):
  1. fix/remove-debug-prints         ← 30 min, bajo riesgo, resultado inmediato
  2. refactor/consolidate-platform-dict  ← 1 h, bajo riesgo
  3. refactor/split-server-monolith  ← hacerlo antes que los demás para desbloquear

Semana 2 (refactoring medio):
  4. refactor/split-sync-handler
  5. refactor/eliminate-late-imports  ← depende de #3 (state.py ya existe)
  6. refactor/consolidate-state       ← depende de #3

Semana 3 (calidad y cobertura):
  7. fix/error-handling
  8. refactor/config-handler-split
  9. tests/api-endpoints
  10. i18n/translate-remaining-strings
```

---

## Fortalezas que hay que preservar

Al hacer cambios, respetar estos patrones que ya funcionan bien:

- `repository.connect()` / `.batch()` — contextmanagers limpios, no romper
- `JobManager` — ya está bien diseñado, usarlo más extensivamente
- `response_builders.py` — funciones puras, mantener así
- `js/tabs/*.js` — separación por feature, mantener la convención
- `@dataclass(slots=True)` — usado correctamente para structs de bajo nivel
- `logging.getLogger(__name__)` — patrón consistente en todo el proyecto
