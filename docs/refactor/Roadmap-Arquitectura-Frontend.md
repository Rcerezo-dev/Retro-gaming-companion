# Retro Vault — Roadmap Arquitectura & Migración Frontend JS

> Documento de diseño para la evolución arquitectural del backend y la migración del frontend a JavaScript puro.
> Redactado el 2026-03-25 tras análisis del estado actual del código.

---

## 1. Diagnóstico del estado actual

### 1.1 Backend — `server.py` (5.447 líneas)

| Problema | Impacto |
|---|---|
| 138 endpoints en un único `if/elif` ladder en `do_GET` + `do_POST` | Imposible razonar o navegar; cualquier bug afecta a todo |
| Sin router: matching manual por `path.startswith(...)` | Rutas ambiguas, solapamientos silenciosos |
| Estado global de jobs como 11 variables sueltas (`_job_lock`, `_jobs`, `_scan_progress`, etc.) | Race conditions silenciosas, testeo imposible, sin lifecycle |
| Handlers como métodos de clase HTTP, no funciones puras | No se pueden testear sin levantar un servidor |
| Dependencia circular via late-import: `cable_sync_daemon` e `inbox_pipeline` importan `server` | Frágil, dificulta extracción de módulos |
| `frontend.py` genera HTML como strings Python (1 sola cadena gigante) | Ningún IDE da autocompletado, imposible hacer diff de la UI |

### 1.2 Frontend — App.js (~6.000 líneas) + frontend.py

| Problema | Impacto |
|---|---|
| HTML embebido en Python como string | No hay separación vista/lógica, cualquier cambio de HTML requiere tocar Python |
| Un único `app.js` monolítico | Sin treeshaking, sin módulos, todo en scope global |
| Estado de UI como variables globales sueltas | Difícil razonar sobre estado, duplicaciones |
| Sin tipo en JS | Bugs de typo silenciosos |
| Comunicación server→client solo por polling (2s) | Latencia innecesaria, 30 req/min por sesión abierta |

### 1.3 Lo que funciona bien (no tocar sin motivo)

- `response_builders.py` — funciones puras bien aisladas, fácil testeo
- Arquitectura de jobs con polling (simple, sin dependencias, funciona en stdlib)
- SQLite con `repository.py` — patrón limpio
- Filosofía sin dependencias externas de runtime (preservar para el servidor Python)

---

## 2. Arquitectura objetivo

### 2.1 Backend

```
src/rom_manager/
  web/
    server.py          ← solo: setup HTTP, routing, main loop (~200 líneas)
    router.py          ← NEW: tabla de rutas {method+path → handler fn}
    jobs/
      manager.py       ← NEW: JobManager class (lock, jobs dict, progress, results)
      types.py         ← NEW: dataclasses JobStatus, JobResult, ProgressDict
    handlers/
      scan.py          ← GET/POST /api/scan*, /api/quick-scan
      collection.py    ← GET /api/collection, /api/stats, /api/missing*
      duplicates.py    ← GET /api/duplicates, POST /api/delete-duplicate*
      organize.py      ← GET/POST /api/conflicts, /api/rename*
      sync.py          ← GET/POST /api/sync*, /api/cable-sync*
      inbox.py         ← GET/POST /api/inbox*
      scraper.py       ← GET/POST /api/scraper*
      config.py        ← GET/POST /api/config*, /api/wizard*
      esde.py          ← GET/POST /api/esde*
      games.py         ← GET/POST /api/games*, /api/playtime*
    response_builders.py  ← sin cambios (ya es bueno)
    frontend.py           ← solo: sirve index.html desde static/
    static/
      index.html        ← NEW: HTML real separado de Python
      app.css           ← sin cambios
      app.js → js/      ← migrar a módulos ES
        js/
          main.js       ← punto de entrada, inicialización
          router.js     ← hash-router client-side (#collection, #scan…)
          state.js      ← estado global de UI (un objeto, no 40 variables)
          api.js        ← todas las llamadas fetch() centralizadas
          jobs.js       ← polling de jobs, startPolling, applyJobStatus
          tabs/
            collection.js
            scan.js
            duplicates.js
            organize.js
            sync.js
            inbox.js
            scraper.js
            config.js
            esde.js
            games.js
          components/
            toast.js
            modal.js
            gamePanel.js
            sidebar.js
```

### 2.2 Frontend (sin build step — ES Modules nativos)

La opción más alineada con la filosofía del proyecto (sin dependencias de runtime) es usar **ES Modules nativos del navegador** (`type="module"`). Esto no requiere npm, webpack ni vite para funcionar.

```html
<!-- static/index.html -->
<script type="module" src="/static/js/main.js"></script>
```

```js
// static/js/main.js
import { initRouter }    from './router.js';
import { initSidebar }   from './components/sidebar.js';
import { initJobs }      from './jobs.js';
// ...
```

**Ventajas:**
- Sin build step: los archivos se sirven directamente por el servidor Python existente
- El servidor solo necesita añadir `Content-Type: text/javascript` para `.js` (ya lo hace)
- Navegadores modernos soportan ES Modules desde 2018
- Permite migración incremental: mover tab a tab

**Si en el futuro se quiere bundle (opcional, no requerido):**
- Añadir `esbuild` como devDependency (binario único, sin node_modules en runtime)
- Output a `static/bundle.js` — el servidor sirve igual

---

## 3. Plan de migración por fases

### FASE 0 — Preparación (1-2 sesiones) ⚡ mínimo riesgo

**Objetivo:** infraestructura sin romper nada.

- [x] **ARCH-0a** — Crear `web/router.py` con clase `Router`:
  ```python
  class Router:
      def __init__(self):
          self._routes: dict[tuple[str,str], Callable] = {}
      def get(self, path): ...   # decorator
      def post(self, path): ...
      def dispatch(self, method, path, handler_ctx): ...
  ```
- [x] **ARCH-0b** — Crear `web/jobs/manager.py` con clase `JobManager`:
  ```python
  class JobManager:
      def __init__(self):
          self._lock = threading.Lock()
          self._jobs: dict[str, str] = {}
          self._progress: dict[str, dict] = {}
          self._results: dict[str, dict] = {}
      def start(self, job_id, label): ...
      def update_progress(self, job_id, data): ...
      def finish(self, job_id, result): ...
      def get_status(self) -> dict: ...
  ```
- [x] **ARCH-0c** — Crear `static/index.html` con el HTML extraído de `frontend.py`
  - `frontend.py` queda como: `HTML = (_STATIC_DIR / 'index.html').read_text(encoding='utf-8')`
- [x] **ARCH-0d** — Crear `static/js/api.js` con todas las llamadas fetch centralizadas
  - Sin modificar ningún handler Python todavía

**Tests:** todos los tests existentes deben seguir pasando.

---

### FASE 1 — Router backend (2-3 sesiones) ✂️ extracción sin reescritura

**Objetivo:** eliminar el `if/elif` ladder de `server.py` sin cambiar la lógica de los handlers.

Estrategia: mover handlers de `server.py` a módulos en `handlers/` **uno a uno**, registrándolos en el router. El `do_GET`/`do_POST` queda como:

```python
def do_GET(self):
    result = _router.dispatch('GET', self.path, self)
    if result is None:
        self._send_404()

def do_POST(self):
    result = _router.dispatch('POST', self.path, self)
    if result is None:
        self._send_404()
```

**Patrón de dependencias establecido:**
- Router instanciado en `make_handler()`, `self._post_data = data` y `self._qs = qs` adjuntos antes del dispatch
- Cada handler module recibe deps por closure en `register(router, *, config, ...)`
- `_auto_sync_enabled` (global) se muta via `_srv_mod._auto_sync_enabled = val`

**Orden de extracción (de menor a mayor acoplamiento):**
1. [x] `handlers/config.py` — `GET/POST /api/config`, `GET /api/wizard-detect`
2. [x] `handlers/collection.py` — `GET /api/collection-stats`, `GET /api/missing`, `GET /api/library-diff`, `GET /api/operations-timeline`, `GET+POST /api/wishlist`
3. [x] `handlers/scan.py` — `/api/scan`, `/api/adb-scan`, `/api/match`, `/api/stop-job`, `/api/job-status`, `/api/catalog-status`, `/api/logs`, `/api/scrape-summary`, `/api/import-dats`, `/api/import-arcade-catalog`
4. [x] `handlers/duplicates.py` — `/api/duplicates`, `/api/duplicates/delete`, `/api/duplicates/delete-all`, `/api/duplicates/exclude`, `/api/ra-duplicates`, `/api/ra-duplicates/discard`, `/api/ra-duplicates/discard-all`, `/api/ra-check/discard-no-support`, `/api/resolve-duplicate-ra`, `/api/apply-ra-conflicts`
5. [x] `handlers/organize.py` — `/api/plan`, `/api/apply`, `/api/fix-platforms`, `/api/create-library-structure`, `/api/organize-library`
6. [x] `handlers/sync.py` — `/api/sync*`, `/api/cable-sync*`, `/api/rclone*`
7. [x] `handlers/inbox.py` — `/api/inbox*`
8. [x] `handlers/scraper.py` — `GET /api/ss-quota`; `POST /api/scrape`, `/api/scrape-single`, `/api/export-gamelists`, `/api/export-pegasus`
9. [x] `handlers/esde.py` — `/api/esde*`, `/api/export-*`, `/api/status`, `/api/local-url`, `/api/test-path`, `/api/list-drives`, `/api/setup-status`, `/api/library-report`, `/api/report/*`, converters, tools, orphaned-saves, doctor, shutdown
10. [x] `handlers/games.py` — `GET /api/games`, `/api/games/filter-options`, `/api/tags`, `/api/game-tags`, `/api/stateshot`, `/api/save-backups`, `/api/manual-backups`, `/api/save-comparison`, `/api/game-sync-history`, `/api/game`; `POST /api/set-play-status`, `/api/set-metadata`, `/api/toggle-favorite`, `/api/tag`, `/api/open-folder`, `/api/launch`, `/api/restore-backup`, `/api/backup-now`

**Cada extracción:** mover código → añadir test de humo → commit.

**Resolver dependencia circular:**
- `cable_sync_daemon` e `inbox_pipeline` inyectan estado via `JobManager` (pasar instancia, no importar `server`)
- Eliminar los late-imports de `server` en estos módulos

---

### FASE 2 — Módulos JS por tab (3-4 sesiones) 🧩 incrementa sin romper

**Sesión 2 completada (2026-03-28):**
- [x] `js/components/modal.js`: `_showConfirm`, `_closeConfirm`; wires confirm-ok button on DOMContentLoaded
- [x] `js/tabs/scan.js`: ADB helpers, `doScan`, `quickScanPC/Android`, `doFixPlatforms`, `doMatch`, `loadCatalogStatus`, `importDats`, `importArcadeCatalog`
- [x] `js/tabs/config.js`: actualizado — ahora importa `_showConfirm` de modal.js (eliminado `window._showConfirm`)
- [x] `app.js`: `let _devName` → `var _devName` (accesible como `window._devName` desde módulos); eliminados confirm modal, scan/match, DAT catalog (~300 líneas más)

**Métricas acumuladas (Sesiones 1+2):**
| Archivo | Líneas |
|---|---|
| app.js | 6.850 (era 7.799) |
| js/ módulos | 1.229 líneas (6 archivos) |

**Sesión 1 completada (2026-03-28):**
- [x] `server.py`: static serving soporta subdirectorios (`js/components/`, `js/tabs/`) con check `relative_to()` anti-traversal
- [x] `js/api.js`: añadidos exports `apiFetch`/`apiPost` para uso directo en módulos
- [x] `js/components/toast.js`: `showToast()` extraído; expuesto en `window.showToast`
- [x] `js/tabs/config.js`: tab Settings (~663 líneas) extraído con imports de api.js y toast.js
- [x] `js/main.js`: entry point `type="module"`; importa y expone todos los migrados en `window`
- [x] `index.html`: `<script type="module" src="/static/js/main.js">` antes de app.js (defer)
- [x] `app.js`: eliminados `showToast` y la sección Settings completa (~673 líneas menos)

**Métricas:**
| Archivo | Antes | Después |
|---|---|---|
| app.js | 7.799 líneas | ~7.126 líneas |
| js/ módulos | 168 líneas (api.js) | ~1.100 líneas (4 archivos) |

**Objetivo:** dividir `app.js` en módulos ES por tab, manteniendo `app.js` como legacy shim temporalmente.

Estrategia: crear `js/` con módulos nuevos. Cada tab que se migra:
1. Se crea `js/tabs/xxx.js` con la lógica del tab
2. `main.js` importa y expone funciones en `window`
3. En `app.js` se elimina el código equivalente
4. Se valida manualmente que el tab funciona igual

**Métricas acumuladas (Sesiones 1–6):**
| Archivo | Líneas |
|---|---|
| app.js | 3.947 (era 7.799) |
| js/ módulos | ~4.020 líneas (12 archivos) |

**Sesión 6 completada (2026-03-30):**
- [x] `js/tabs/scraper.js` — creado, cableado en main.js + eliminado de app.js (`loadScraperSummary`, `loadSsQuota`, `loadScrapePlatforms`, `doScrape`, `doExportGamelists`, `doExportGamelistsAll`, `_autoFillEsdeGamelistDir`, `useEsdeGamelistDir`, variable `_esdeGamelistsDir`)

**Sesión 5 completada (2026-03-30):**
- [x] `js/tabs/inbox.js` — creado, cableado en main.js + eliminado de app.js (`updateInboxBadge`, `_initInboxBadge`, `inboxDragOver/Leave/Drop`, `loadInbox`, `fillInboxTarget`, `scanInbox`, `runInbox`, `_applyInboxProgress`, `_renderInboxResult`, `saveInboxSettings`, `_pollInboxWatcher`); `setInterval` de badge movido al módulo; `_shownResultTs.inbox` → `_lastInboxResultTs` privado

**Sesión 4 completada (2026-03-30):**
- [x] `js/tabs/sync.js` — ya existía creado y cableado en main.js; eliminado bloque Auto-sync UI duplicado de app.js (`_updateAutoSyncBanner`, `_updateAutoSyncToggleUI`, `toggleAutoSync`, `saveAutoSyncSettings`, `_pollAutoSync`, `startAutoSyncPolling`, variables `_autoSyncTimer`/`_autoSyncEnabled`); llamada de init movida a DOMContentLoaded

**Sesión 3 completada (2026-03-30):**
- [x] `js/tabs/collection.js` — cableado en main.js + eliminado de app.js
- [x] `js/tabs/duplicates.js` — cableado en main.js + eliminado de app.js
- [x] `js/tabs/organize.js` — creado, cableado, eliminado de app.js (`loadPlan`, `applyKeepBoth`, `doApply`, helpers)
- [x] `js/jobs.js` — creado, cableado, eliminado de app.js (`startPolling`, `_applyJobStatus`, `_showJobResult`)

**Orden de migración de tabs:**
1. `js/state.js` — extraer las ~40 variables globales a un objeto `AppState`
2. [x] `js/api.js` — centralizar todas las llamadas fetch ✅
3. [x] `js/jobs.js` — `startPolling()`, `_applyJobStatus()`, `_showJobResult` ✅
4. [x] `js/components/toast.js` — `showToast()` ✅
5. [x] `js/components/modal.js` — confirm modal ✅
6. [x] `js/tabs/config.js` — tab Settings ✅
7. [x] `js/tabs/scan.js` — tab Scan ✅
8. [x] `js/tabs/collection.js` — tab Colección ✅
9. [x] `js/tabs/duplicates.js` — Duplicados + RA Duplicados ✅
10. [x] `js/tabs/organize.js` — Organizar (plan, apply, helpers) ✅
11. [x] `js/tabs/sync.js` — Cable Sync + Cloud Sync + Auto-sync + Rclone ✅
12. [x] `js/tabs/inbox.js` — Inbox + drag & drop + watcher ✅
13. [x] `js/tabs/scraper.js` — Scraper + gamelists + Pegasus ✅
14. `js/tabs/esde.js` — ES-DE + Tools + RA check + Reports + Doctor + Junk
15. `js/tabs/games.js` — Lista de juegos + game panel + TV mode
16. `js/tabs/overview.js` — Overview + wizard + heatmap + charts (o queda en app.js)
17. Eliminar `app.js` legacy cuando todos los tabs estén migrados

---

### FASE 3 — Estado reactivo ligero (opcional, post-migración)

Una vez los módulos están separados, el siguiente nivel es añadir un store reactivo mínimo sin framework:

```js
// js/state.js
function createStore(initial) {
  const listeners = {};
  const state = { ...initial };
  return {
    get: key => state[key],
    set: (key, val) => {
      state[key] = val;
      listeners[key]?.forEach(fn => fn(val));
    },
    subscribe: (key, fn) => { (listeners[key] ??= []).push(fn); },
  };
}
export const store = createStore({ ... });
```

Esto elimina el polling innecesario de algunas secciones y hace el estado predecible.

---

### FASE 4 — SSE en lugar de polling (opcional)

Reemplazar `setInterval(2s)` para jobs por **Server-Sent Events**:

```python
# handlers/jobs.py
def handle_job_events(self):
    self._send_headers(200, 'text/event-stream')
    while True:
        data = job_manager.get_status()
        self.wfile.write(f"data: {json.dumps(data)}\n\n".encode())
        time.sleep(0.5)
```

```js
// js/jobs.js
const es = new EventSource('/api/job-events');
es.onmessage = e => applyJobStatus(JSON.parse(e.data));
```

**Ventaja:** latencia media de 0.5s en lugar de 2s; 0 requests innecesarias cuando no hay jobs activos.

---

## 4. Decisiones que necesitan input del usuario

### D1 — ¿Build step o ES Modules nativos?

| Opción | Pros | Contras |
|---|---|---|
| **ES Modules nativos** | Sin npm, sin build, fiel a la filosofía del proyecto | Sin treeshaking, ~15 requests al cargar (aceptable en localhost) |
| **esbuild** (devDependency) | Bundle único, treeshaking, más rápido | Requiere Node.js en dev, paso de build manual |
| **Vite + Vue/Svelte** | DX excelente, reactividad gratis, HMR | Rompe la filosofía sin deps; requiere Node; bundle en dist/ |

**Recomendación:** ES Modules nativos. En localhost 15 requests no importan. Si en el futuro se quiere bundle, `esbuild` es una línea de script sin cambiar nada más.

### D2 — ¿Migrar HTML a `index.html` antes o después de los módulos JS?

- **Antes:** más limpio desde el inicio, pero toca Python y JS simultáneamente
- **Después:** menos riesgo, migrar JS primero, HTML al final

**Recomendación:** HTML primero (FASE 0c). Es un cambio mecánico (copiar string → archivo), de bajo riesgo, que desbloquea el autocompletado del IDE inmediatamente.

### D3 — ¿Hasta qué fase queremos llegar?

| Hasta fase | Resultado | Esfuerzo estimado |
|---|---|---|
| FASE 0 | HTML separado + infraestructura | 1-2 sesiones |
| FASE 1 | Backend modular, sin monolito | +4-6 sesiones |
| FASE 2 | JS por módulos, sin app.js monolito | +4-6 sesiones |
| FASE 3+4 | Estado reactivo + SSE | +2-3 sesiones |

---

## 5. Principios de migración

1. **Nunca big-bang.** Cada paso debe dejar el proyecto en estado funcional.
2. **Un módulo a la vez.** Extraer → validar → commit → siguiente.
3. **Los tests deben pasar en cada paso.** Si un extracción rompe un test, arreglarlo antes de continuar.
4. **No reescribir lógica al migrar.** Mover código, no mejorar. Las mejoras van en commits separados.
5. **Mantener compatibilidad de API.** Los endpoints no cambian de ruta ni de contrato durante la migración.
6. **Sin dependencias de runtime nuevas.** El servidor Python sigue siendo stdlib. JS puede usar ES Modules (nativos del navegador, no npm).

---

## 6. Quick wins antes de empezar la migración

Estos bugs/mejoras tienen alto valor y bajo riesgo de conflicto con la migración:

| Item | Esfuerzo | Impacto |
|---|---|---|
| BUG-I: Collection tab incompleta | Bajo | Alto |
| BUG-K: Conflictos por RA | Medio | Alto |
| QoL-15: ROMs no identificadas | Medio | Alto |
| BUG-F/G: ES-DE emuladores | Medio | Medio |
| QoL-12: Exportar colección | Bajo | Medio |

Recomendación: resolver estos bugs antes de empezar FASE 1, para no mezclar bug fixes con refactoring.

---

## 7. Guía para no iniciados — ¿qué hemos hecho y por qué?

> Esta sección explica en términos sencillos todo lo que se ha hecho en esta migración, sin asumir conocimientos previos de arquitectura de software.

---

### El problema de partida

Imagina que toda la lógica de una aplicación web — el servidor, las respuestas a cada petición, el estado interno, el HTML, el JavaScript — está escrita en **tres archivos enormes**:

- `server.py` → **5.447 líneas**. Un único archivo Python que hace absolutamente todo: recibe peticiones HTTP, decide qué hacer con cada una, ejecuta procesos en segundo plano, gestiona el estado, etc.
- `frontend.py` → **2.503 líneas**. Un archivo Python que contiene todo el HTML de la aplicación como una cadena de texto gigante dentro de una variable Python.
- `app.js` → **7.791 líneas**. Un único archivo JavaScript con toda la lógica del navegador.

Esto funciona, pero tiene un problema grave: **es imposible de mantener**. Cuando un archivo tiene miles de líneas, cualquier cambio pequeño puede romper algo inesperado, es difícil encontrar el código relevante, y dos personas no pueden trabajar en él a la vez sin conflictos.

---

### La estrategia: migración incremental

En lugar de reescribir todo desde cero (lo que se llama un "big bang" y suele acabar en desastre), decidimos **mover el código en pasos pequeños**, verificando en cada paso que todo sigue funcionando igual.

La regla de oro es: **mover código, no reescribirlo**. Si algo funciona, no se toca la lógica. Solo se cambia de sitio.

---

### Fase 0 — Preparar la infraestructura (sin romper nada)

Antes de mover código, creamos las "herramientas" que vamos a necesitar:

#### ARCH-0a: `web/router.py` — El encaminador

En el servidor original, cuando llega una petición HTTP, el código hace algo así:

```python
if path == "/api/config":
    # hacer cosa A
elif path == "/api/scan":
    # hacer cosa B
elif path == "/api/sync":
    # hacer cosa C
# ... 138 casos más ...
```

Esto se llama un **ladder if/elif** ("escalera de condiciones"). Con 138 casos, es imposible de leer.

Creamos un `Router`: una clase que actúa como un **directorio telefónico**. En lugar de recorrer 138 condiciones, el router tiene una tabla:

```
GET  /api/config    →  función handle_config
POST /api/config    →  función save_config
GET  /api/scan      →  función handle_scan
...
```

Cuando llega una petición, el router busca directamente en la tabla y llama a la función correcta.

#### ARCH-0b: `web/jobs/manager.py` — El gestor de tareas en segundo plano

El servidor lanza tareas largas en segundo plano (escanear ROMs, sincronizar saves, etc.). El estado de esas tareas se guardaba en **11 variables globales sueltas**:

```python
_job_lock = threading.Lock()
_jobs = {"scan": False, "sync": False, ...}
_scan_progress = {}
_chd_progress = {}
# ... 8 más ...
```

Variables globales sueltas son peligrosas: cualquier parte del código puede modificarlas accidentalmente, y son difíciles de testear.

Creamos un `JobManager`: una clase que **encapsula** todo ese estado en un solo objeto con métodos claros (`start()`, `update_progress()`, `finish()`). El resto del código solo habla con el `JobManager`, sin tocar variables globales directamente.

#### ARCH-0c: `static/index.html` — El HTML en su propio archivo

El HTML de la aplicación vivía así en `frontend.py`:

```python
HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
...
2.500 líneas de HTML...
</html>
"""
```

Un archivo HTML metido dentro de una variable de Python. Esto significa que **ningún editor sabe que es HTML**: no hay autocompletado, no hay validación, no hay coloreado de sintaxis correcto.

Extrajimos el HTML a `static/index.html`, un archivo real. `frontend.py` ahora tiene 8 líneas:

```python
HTML = (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")
```

El comportamiento es idéntico, pero ahora cualquier editor puede trabajar con el HTML como HTML.

#### ARCH-0d: `static/js/api.js` — Las llamadas a la API centralizadas

Creamos un fichero JavaScript (`api.js`) que es un **catálogo de todos los endpoints** de la API, con funciones con nombres legibles:

```javascript
// En lugar de esto disperso por 7.000 líneas:
await fetch('/api/config')
await fetch('/api/sync', { method: 'POST', body: ... })

// Tendremos esto en un solo sitio:
await api.config()
await api.sync(opciones)
```

Este archivo no se usa todavía — es infraestructura para la Fase 2.

---

### Fase 1 — Extraer handlers del monolito (en curso)

Ahora que tenemos el Router, empezamos a **vaciar** el `if/elif` ladder de `server.py`, moviendo cada grupo de rutas a su propio archivo en `web/handlers/`.

#### El patrón que seguimos

Cada archivo de handler tiene una función `register(router, *, dependencias...)`:

```python
# handlers/config.py
def register(router, *, config, set_auto_sync_fn):

    @router.get("/api/config")
    def get_config(ctx):
        ctx._send_json(_build_config(config))

    @router.post("/api/config")
    def post_config(ctx):
        _save_config(ctx, ctx._post_data, config, set_auto_sync_fn)
```

Y en el servidor principal, solo hay que registrarlo:

```python
# En make_handler():
import rom_manager.web.handlers.config as _h_config
_h_config.register(_router, config=config, set_auto_sync_fn=_set_auto_sync_fn)
```

Las dependencias (como `config` o `repository`) se pasan explícitamente — no hay magia ni variables globales ocultas.

#### Lo que se ha extraído hasta ahora

**`handlers/config.py`** (completado):
- `GET /api/config` — devuelve la configuración actual
- `POST /api/config` — guarda cambios en `config.toml` y recarga la configuración en memoria
- `GET /api/wizard-detect` — detecta RetroArch y dispositivos ADB para el asistente inicial

También se movió la lógica de estas funciones fuera de `server.py` a `handlers/config.py`, donde tiene más sentido que viva.

**`handlers/collection.py`** (completado):
- `GET /api/collection-stats` — estadísticas de cobertura de la colección vs los DATs
- `GET /api/missing` — lista de ROMs que faltan en la biblioteca
- `GET /api/library-diff` — diferencias entre la biblioteca PC y la de Android
- `GET /api/operations-timeline` — historial de operaciones recientes
- `GET+POST /api/wishlist` — lista de deseos de ROMs buscadas

También se movió `_build_missing_data` (la función que calcula qué ROMs faltan comparando la biblioteca con los catálogos DAT).

**`handlers/scan.py`** (completado):
- `GET /api/job-status` — estado de todos los jobs en segundo plano (scan, sync, scrape, RA check…)
- `GET /api/catalog-status` — lista los archivos DAT cargados con conteo de entradas
- `GET /api/logs` — tail de los archivos de log del servidor
- `GET /api/scrape-summary` — resumen del último scraping
- `POST /api/scan` — lanza el escaneo de la biblioteca (job en background)
- `POST /api/adb-scan` — escanea un dispositivo Android vía ADB
- `POST /api/match` — lanza el matching de ROMs contra los catálogos DAT
- `POST /api/stop-job` — cancela cualquier job en ejecución
- `POST /api/import-dats` — importa archivos DAT desde una carpeta
- `POST /api/import-arcade-catalog` — importa catálogos MAME/FBNeo

Este handler necesita acceso a las variables globales de estado de jobs (`_jobs`, `_job_lock`, `_scan_progress`, etc.), así que recibe `srv_mod` (referencia al módulo `server.py`) — el mismo patrón que ya usaba `cable_sync_daemon`.

**`handlers/duplicates.py`** (completado):
- `GET /api/duplicates` — lista todos los grupos de ROMs duplicadas (por SHA1)
- `GET /api/ra-duplicates` — agrupa duplicados por título, marcando cuáles tienen logros RA
- `POST /api/duplicates/delete` — elimina un duplicado individual (archivo + entrada BD)
- `POST /api/duplicates/delete-all` — elimina todos los duplicados excepto el primero de cada grupo
- `POST /api/duplicates/exclude` — excluye un SHA1 de ser considerado duplicado
- `POST /api/apply-ra-conflicts` — en conflictos de renombrado, conserva la versión con más logros RA
- `POST /api/ra-duplicates/discard` — mueve un duplicado sin logros RA a `_descartados/`
- `POST /api/ra-duplicates/discard-all` — mueve todos los duplicados sin logros RA a `_descartados/`
- `POST /api/ra-check/discard-no-support` — descarta todos los juegos sin soporte RA del último check
- `POST /api/resolve-duplicate-ra` — conserva la versión con soporte RA y descarta las demás

Todas las operaciones de descarte tienen rollback atómico: si la base de datos falla después de mover el archivo, el archivo se restaura a su posición original.

#### Resultado medible

| Métrica | Antes | Tras handlers 1–4 |
|---|---|---|
**`handlers/organize.py`** (completado):
- `GET /api/plan` — calcula el plan de renombrado (qué ROMs hay que renombrar y a qué nombres canónicos)
- `POST /api/apply` — ejecuta el plan en segundo plano: renombra cada ROM con rollback atómico, mueve los saves asociados, registra cada operación en BD
- `POST /api/fix-platforms` — rellena las plataformas que faltan en la BD relanzando el detector automático
- `POST /api/create-library-structure` — crea la estructura de carpetas estándar ES-DE (una carpeta por plataforma, con subcarpetas `media/`, `saves/`, `states/`)
- `POST /api/organize-library` — mueve ROMs ya escaneadas a sus carpetas de plataforma, centraliza saves en `saves/{plataforma}/` y mueve BIOS conocidas a `bios/`

Este handler también usa `srv_mod` para acceder a `_apply_progress`, `_jobs["apply"]` y `_job_results["apply"]` (el job de aplicación del plan), y a las constantes `_ES_PLATFORM_FOLDERS` y `_STANDARD_PLATFORM_FOLDERS` que definen los nombres de carpeta por plataforma.

**`handlers/sync.py`** (completado):
- `GET /api/adb-devices` — lista los dispositivos Android conectados vía ADB
- `GET /api/test-adb-path` — comprueba si una ruta Android es accesible vía ADB
- `GET /api/sync-log` — historial de operaciones de sync en la BD
- `GET /api/cable-sync-preview` — vista previa de qué archivos se copiarían en el próximo cable sync
- `GET /api/cable-sync-log` — tail del fichero de log de operaciones de cable sync
- `GET /api/rclone-export-config` — devuelve el archivo de configuración rclone para copiarlo al Android
- `GET /api/rclone-status` — versión y remotos configurados en rclone
- `GET /api/auto-sync-status` — estado del daemon de auto-sync (activo/parado, último device visto)
- `GET /api/sd-sync-status` — estado del daemon de sync por SD card
- `POST /api/sync` — lanza sincronización rclone en segundo plano con múltiples fuentes
- `POST /api/cable-sync` — copia saves y/o ROMs entre PC y consola vía ADB o sistema de archivos; soporta 3 direcciones (PC→consola, consola→PC, más reciente gana); registro de operaciones en log
- `POST /api/auto-sync-toggle` — activa/desactiva el daemon de auto-sync
- `POST /api/auto-sync-save` — guarda configuración de auto-sync en `config.toml` y actualiza en memoria
- `POST /api/migrate-split-db` — migración única: mueve registros Android de la BD de PC a la BD de Android
- `POST /api/ra-check` — lanza la comprobación de soporte RetroAchievements

**Nota especial:** `_handle_cable_sync`, `_handle_ra_check` y `_handle_migrate_split_db` habían sido eliminados accidentalmente en la sesión anterior al borrar el bloque de duplicates. Los tres métodos se recuperaron desde el historial de git (`git show HEAD:...`) y se incluyeron correctamente en este handler.

#### Resultado medible

| Métrica | Antes | Tras handlers 1–6 |
|---|---|---|
**`handlers/inbox.py`** (completado):
- `GET /api/inbox-count` — número de archivos pendientes en el inbox
- `GET /api/inbox-scan` — lista el contenido del inbox con detección de plataforma y formato
- `GET /api/inbox-status` — estado del job de procesado (running, progreso, resultado)
- `GET /api/inbox-watcher-status` — estado del daemon de vigilancia automática del inbox
- `POST /api/inbox-run` — lanza el pipeline completo: extraer ZIPs → detectar plataforma → mover a carpeta correcta
- `POST /api/setup-run` — lanza el wizard de primera configuración (scan + match + estructura ES-DE)
- `POST /api/inbox-upload` (multipart) — recibe archivos subidos desde el navegador y los deposita en el inbox

**Nota de implementación:** la ruta `/api/inbox-upload` usa multipart en lugar de JSON, por lo que se intercepta antes del router en `do_POST`. La lógica se expone como `handle_inbox_upload(config, content_type, body, ctx)` desde el handler y se llama directamente, manteniendo el patrón limpio sin romper el flujo del router.

#### Resultado medible

| Métrica | Antes | Tras handlers 1–9 |
|---|---|---|
| `server.py` líneas | 5.447 | ~1.403 |
| `frontend.py` líneas | 2.503 | 8 |
| Archivos de handler | 0 | 9 |
| Rutas en el ladder (if/elif) | 138 | 3 (solo auth) |
| Tests pasando | 384/388 | 388/388 |

**FASE 1 completa.** El ladder ha sido eliminado. Los únicos `elif path ==` restantes son `/api/auth/logout`, `/api/set-pin` y `/api/clear-pin`, que están intencionalmente fuera del router porque requieren lógica de sesión antes del dispatch normal.

La reducción del ladder se acelera con cada handler. Los primeros (config, collection) requirieron crear la infraestructura del Router; los siguientes (scan, duplicates, organize, sync, inbox) solo necesitaron aplicar el patrón ya establecido.

---

### Por qué todo esto importa

**Para el desarrollador:**
- Cuando algo falla en `/api/collection-stats`, sabes exactamente dónde mirar: `handlers/collection.py`.
- Puedes testear `handlers/config.py` sin levantar un servidor HTTP completo.
- Dos personas pueden trabajar en `handlers/sync.py` y `handlers/games.py` al mismo tiempo sin conflictos de merge.

**Para el futuro:**
- Fase 2 dividirá `app.js` (7.791 líneas) de la misma forma: un archivo por sección de la UI.
- Al final, un cambio en la pantalla de configuración solo tocará `handlers/config.py` (Python) y `js/tabs/config.js` (JS) — dos archivos pequeños y enfocados, en lugar de dos monstruos de 5.000 líneas.
