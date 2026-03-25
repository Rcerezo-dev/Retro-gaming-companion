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

**Orden de extracción (de menor a mayor acoplamiento):**
1. `handlers/config.py` — `/api/config`, `/api/wizard*` (sin deps de job state)
2. `handlers/scan.py` — `/api/scan*` (usa JobManager)
3. `handlers/collection.py` — `/api/collection`, `/api/stats` (solo response_builders)
4. `handlers/duplicates.py` — `/api/duplicates`, `/api/delete-*`
5. `handlers/organize.py` — `/api/conflicts`, `/api/rename*`
6. `handlers/sync.py` — `/api/sync*`
7. `handlers/inbox.py` — `/api/inbox*`
8. `handlers/scraper.py` — `/api/scraper*`
9. `handlers/esde.py` — `/api/esde*`
10. `handlers/games.py` — `/api/games*`, `/api/playtime*`

**Cada extracción:** mover código → añadir test de humo → commit.

**Resolver dependencia circular:**
- `cable_sync_daemon` e `inbox_pipeline` inyectan estado via `JobManager` (pasar instancia, no importar `server`)
- Eliminar los late-imports de `server` en estos módulos

---

### FASE 2 — Módulos JS por tab (3-4 sesiones) 🧩 incrementa sin romper

**Objetivo:** dividir `app.js` en módulos ES por tab, manteniendo `app.js` como legacy shim temporalmente.

Estrategia: crear `js/` con módulos nuevos. Cada tab que se migra:
1. Se crea `js/tabs/collection.js` con la lógica del tab
2. `main.js` importa y llama `initCollectionTab()`
3. En `app.js` se elimina el código equivalente
4. Se valida manualmente que el tab funciona igual

**Orden de migración de tabs:**
1. `js/state.js` — extraer las ~40 variables globales a un objeto `AppState`
2. `js/api.js` — centralizar todas las llamadas fetch
3. `js/jobs.js` — `startPolling()`, `_applyJobStatus()`, `_shownResultTs`
4. `js/components/toast.js` — `showToast()`
5. `js/components/modal.js` — confirm modal, wizard modal
6. `js/tabs/config.js` — tab Settings (pocas deps)
7. `js/tabs/scan.js` — tab Scan
8. `js/tabs/collection.js` — tab Colección
9. `js/tabs/duplicates.js`
10. `js/tabs/organize.js`
11. `js/tabs/sync.js` — Cloud Sync
12. `js/tabs/inbox.js`
13. `js/tabs/scraper.js`
14. `js/tabs/esde.js`
15. `js/tabs/games.js`
16. Eliminar `app.js` legacy cuando todos los tabs estén migrados

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
