# Día 14 — Roadmap: Retro Vault para cualquier jugador

> Evolución de `Roadmap-App-Universal.md` — añadida auditoría arquitectural completa.
> Fecha: 2026-03-17

---

## El problema central

Ahora mismo la app asume demasiado:
- Que tienes Python y Conda instalados
- Que sabes editar un `config.toml`
- Que conoces las rutas de RetroArch, de tus ROMs, de tu consola
- Que tienes DATs de No-Intro descargados
- Que entiendes qué es un "core" o un "save state"

Un jugador normal no tiene nada de eso. El objetivo es que pueda pasar de cero a jugando en menos de 15 minutos, sin tocar ningún archivo de texto.

---

## Estado arquitectural actual (auditoría 2026-03-17)

| Archivo | Líneas | Estado |
|---------|--------|--------|
| `web/frontend.py` | 5.788 | 🔴 Monolito — HTML+CSS+JS en una sola cadena Python |
| `web/server.py` | 5.014 | 🔴 Monolito — 76 endpoints, lógica de negocio mezclada |
| `database/repository.py` | 945 | 🟡 Bien estructurado pero sin tests |
| `cli.py` | 756 | 🟡 3 funciones, demasiado comprimido |
| Resto de módulos | <300 c/u | ✅ Arquitectura modular correcta |

**Fortalezas que conservar:** sin imports circulares, separación data/lógica fuera de web/, patrón repository limpio, jobs thread-safe.

---

## Bugs críticos (resolver antes que cualquier otra cosa)

| # | Problema | Síntoma |
|---|---------|---------|
| **B1** | Rutas no persisten entre sesiones | Hay que volver a escribir `library_root` etc. cada vez que se abre la app |
| **B2** | Batch run de Tools incompleto | Solo corre 3 de los 8 tools disponibles |
| **B3** | Bibliotecas PC y Android no llegan a ser idénticas | Solo se sincronizan saves, no ROMs |

---

## Fase 0 — Parches funcionales (para uso diario tuyo ahora)

### 0A — Batch run completo en Tools

El botón "Ejecutar todo" debe lanzar todos los tools en orden lógico, respetando el contexto PC/Android activo:

1. Escanear biblioteca (Scan)
2. Comparar contra catálogos DAT (Match)
3. Comprobar salud de archivos (Health Check)
4. Buscar saves huérfanos (Orphan Finder)
5. Descomprimir ZIPs (Extract ZIP)
6. Convertir a CHD (Convert CHD)
7. Scraper de metadatos y carátulas
8. Comprobar RetroAchievements

Cada tool ya existe — solo hay que añadirlos al batch run y respetar que cada uno espera al anterior.

### 0B — Bibliotecas exactamente iguales

El sync no debería terminar hasta que PC y Android tengan exactamente los mismos ROMs:

- **Comparador de bibliotecas**: pantalla que muestra qué hay en PC y no en Android, y viceversa
- **Sync bidireccional de ROMs** (no solo saves)
- **Verificación post-sync**: re-comparar tras el sync y confirmar igualdad
- **Política de conflictos para ROMs**: si el mismo juego existe en ambos lados con SHA1 distinto, mostrar al usuario — nunca decidir solo

### 0C — Persistencia de rutas

Investigar tres puntos concretos:
1. ¿Se escribe `config.toml` en `project_root/config.toml`?
2. ¿La UI carga los valores al abrir Settings (no solo al arrancar el servidor)?
3. ¿El servidor recarga `config.toml` al arrancar en vez de usar valores en memoria?

---

## Fase 1 — Deuda técnica y arquitectura

Esta fase no la ve el usuario final, pero sin ella el proyecto se vuelve imposible de mantener y de distribuir.

### 1A — Partir `server.py` en módulos (5.014 → ~500 líneas por módulo)

El servidor tiene 76 endpoints agrupados informalmente. Extraer en submódulos:

```
web/
  server.py          ← solo enrutador HTTP (~300 líneas)
  handlers/
    scan.py          ← scan, match, fix-platforms
    organize.py      ← structure, organize, inbox
    sync.py          ← cloud sync, cable sync, auto-sync
    tools.py         ← CHD, ZIP, health, orphans, M3U, RA
    scraper.py       ← scrape, gamelists, Pegasus
    games.py         ← games list, plan, apply, duplicates, assets
    config.py        ← config GET/POST, status, drives
    reports.py       ← library report, junk scan, DB backup
  jobs.py            ← JobRunner (ver 1B)
  response_builders.py ← funciones _build_* extraídas
```

Beneficio: de un archivo de 5.000 líneas a 8 módulos de ~500. Cada uno testeable por separado.

### 1B — Patrón JobRunner (eliminar ~300 líneas duplicadas)

Los 13 handlers de jobs en background son todos idénticos en estructura:

```python
# Patrón actual — repetido 13 veces:
def _handle_xxx(self, data):
    with _job_lock:
        if _jobs["xxx"]: return already_running
        _jobs["xxx"] = True
    def run():
        try: ... lógica ...
        except: _job_results["xxx"] = {"error": ...}
        finally: _jobs["xxx"] = False
    threading.Thread(target=run, daemon=True).start()
```

Extraer un `JobRunner` que reciba el nombre del job y un callable:

```python
# Objetivo:
def _handle_xxx(self, data):
    _job_runner.start("xxx", lambda: self._do_xxx(data))
```

Beneficio: -300 líneas de boilerplate, patrón consistente, más fácil añadir nuevos jobs.

### 1C — Partir `frontend.py` (5.788 líneas)

El frontend es una sola cadena Python con HTML, CSS y JS mezclados. El objetivo no es reescribirlo — es organizarlo sin cambiar el comportamiento:

```
web/
  frontend.py        ← solo ensambla las piezas (~100 líneas)
  static/
    style.css        ← CSS extraído
    app.js           ← JS extraído y dividido por sección:
      api.js         ← apiFetch, startPolling, _applyJobStatus
      tabs/
        games.js     ← loadGames, renderGame, filters
        tools.js     ← doBatchRun, loadTools, setToolsContext
        sync.js      ← doSync, doCableSync, loadSyncStatus
        settings.js  ← saveSettings, loadSettings
        ...
```

El servidor sirve los archivos estáticos con un handler simple. El HTML sigue generándose en Python pero referenciando archivos externos.

Beneficio: JS testeable con Jest/Vitest, CSS editable sin buscar entre cadenas Python, contribuciones externas posibles.

### 1D — Validación en `config.py`

`AppConfig` tiene 37 campos y cero validación. Añadir un método `validate()` que compruebe:
- Rutas existentes (`library_root`, `chdman`, `adb`)
- Puerto en rango válido (1–65535)
- Extensiones con formato correcto (empiezan por `.`)
- Credenciales no vacías si el servicio está configurado

Devuelve lista de warnings (no errores fatales) que la UI muestra en Settings.

### 1E — Tests para `repository.py`

Es el corazón de la app (945 líneas, 33 funciones) y no tiene ningún test. Mínimo imprescindible:
- Tests de CRUD: `upsert_game`, `upsert_save`, `get_unresolved_games`
- Tests de queries críticas: `get_duplicate_groups`, `get_matched_games`
- Tests de `apply_rename` y `backfill_platforms`
- Test de `prune_stale_entries` (regresión — este causó bugs en el pasado)

Usar SQLite en memoria (`:memory:`) para que los tests no toquen datos reales.

---

## Fase 2 — Primer arranque sin fricción

| Tarea | Descripción | Esfuerzo |
|-------|-------------|---------|
| **Wizard en la web** | Pantalla de bienvenida si no existe `config.toml`. Pasos: detectar biblioteca → RetroArch → dispositivo → crear estructura | Alto |
| **Auto-detección de RetroArch** | Buscar `retroarch.exe` en rutas comunes y ofrecer la encontrada | Medio |
| **Auto-detección de cores** | Leer `cores/` y mapear qué sistemas están disponibles. Avisar si falta algún core. | Medio |
| **Generador de `es_systems.cfg`** | Generar el config de EmulationStation automáticamente basándose en los cores detectados | Medio |
| **Auto-detección de dispositivo Android** | Al conectar USB, detectar vía ADB y proponer rutas automáticamente | Medio |
| **Selector de carpeta** | Botón "Examinar" que abre el explorador de Windows en vez de escribir rutas a mano | Bajo |

---

## Fase 3 — DATs sin esfuerzo

| Tarea | Descripción | Esfuerzo |
|-------|-------------|---------|
| **Descarga guiada de DATs** | Botón "Descargar catálogos" — explica qué son y descarga los relevantes para los sistemas detectados | Alto |
| **DATs mínimos incluidos** | DATs para NES, SNES, GBA, PSX incluidos en el instalador. Matching funciona sin configuración. | Alto |
| **Indicador de calidad del match** | Dejar claro en la UI cuándo el match es "con DAT" vs "por nombre de archivo" | Bajo |

---

## Fase 4 — Sync sin configuración

| Tarea | Descripción | Esfuerzo |
|-------|-------------|---------|
| **Wizard de sync cloud** | Elige proveedor → abre navegador para autorizar → genera config de rclone automáticamente | Alto |
| **WiFi sync directo** | Sync PC ↔ consola en la misma red vía SFTP (Termux + sshd). Sin pasar por internet. | Medio |
| **Sync automático al conectar** | Al detectar el dispositivo, preguntar "¿Sincronizar ahora?". Un clic. | Bajo |
| **Estado de sync siempre visible** | "Último sync hace 2h · 3 archivos actualizados" en la cabecera. | Bajo |

---

## Fase 5 — UX para no-técnicos

| Tarea | Descripción | Esfuerzo |
|-------|-------------|---------|
| **Errores en lenguaje humano** | Ningún stack trace. Cada error tiene mensaje claro y acción concreta. | Medio |
| **Ayuda contextual** | Tooltips `?` en cada sección. Sin necesidad de leer docs externas. | Medio |
| **UI responsive** | Funciona desde el navegador de la consola Android. | Medio |
| **Nombres sin jerga** | "Catálogos DAT" → "Base de datos de juegos", "SHA1" → "Identificación automática" | Bajo |
| **Notificaciones de sistema** | Toast de Windows al terminar sync o detectar juegos en inbox | Bajo |

---

## Fase 6 — Autenticación y acceso remoto

| Tarea | Descripción | Esfuerzo |
|-------|-------------|---------|
| **PIN de acceso** | Al exponer `host = 0.0.0.0`, pedir PIN antes de mostrar la UI | Bajo |
| **QR de acceso** | QR en pantalla principal con `http://{ip_local}:7777` para conectar desde la consola | Bajo |

---

## Fase 7 — Skills y agentes de Claude

Skills que añadir a `.claude/commands/` para acelerar el trabajo con la app:

| Skill | Descripción |
|-------|-------------|
| **`/batch-run`** | Lanza el batch run completo (todos los tools en orden) sobre la biblioteca y espera resultados |
| **`/diff-libraries`** | Compara la biblioteca PC vs Android y muestra qué falta en cada lado |
| **`/fix-config`** | Detecta problemas en `config.toml` (rutas inaccesibles, campos vacíos) y propone correcciones |
| **`/gen-es-config`** | Genera `es_systems.cfg` leyendo los cores instalados de RetroArch automáticamente |

Agentes a añadir a `.claude/agents/`:

| Agente | Descripción |
|--------|-------------|
| **`job-runner-refactor`** | Aplica el patrón JobRunner a todos los handlers de server.py de una pasada |
| **`server-splitter`** | Divide server.py en los submódulos de handlers/, creando los archivos y actualizando imports |
| **`frontend-splitter`** | Extrae CSS y JS de frontend.py a archivos estáticos en `web/static/` |
| **`repo-test-writer`** | Genera tests para todos los métodos de repository.py usando SQLite en memoria |

---

## Fase 8 — Distribución (la última)

No tiene sentido empaquetar hasta que todo lo anterior funcione para ti.

| Tarea | Descripción | Esfuerzo |
|-------|-------------|---------|
| **Tests de integración sólidos** | Suite que valide el pipeline completo antes de cada release | Alto |
| **Ejecutable único** | PyInstaller → `RetroVault.exe` con Python embebido | Alto |
| **Instalador Windows** | Inno Setup: acceso directo, entrada en Programas y características | Medio |
| **Auto-arranque opcional** | Iniciar con Windows, bandeja del sistema | Bajo |
| **Auto-update** | Comprobar versión nueva en GitHub Releases al arrancar | Bajo |
| **Nombre definitivo** | Retro Vault o Retro Companion. README orientado al usuario final. | Bajo |

---

## Orden de prioridad

```
Bugs B1, B2, B3
      ↓
Fase 0 (batch run completo, bibliotecas iguales, persistencia)
      ↓
Fase 1 (arquitectura: partir monolitos, JobRunner, tests repo, validación config)
      ↓
Fase 2 (wizard) + Fase 5 (UX) ← en paralelo
      ↓
Fase 3 (DATs) + Fase 4 (sync completo) ← en paralelo
      ↓
Fase 6 (auth) → Fase 7 (skills/agentes) → Fase 8 (distribución)
```

La Fase 1 (arquitectura) debe ir antes del wizard y el UX — de lo contrario, cualquier cambio en la UI implica buscar código en 5.000 líneas sin estructura.

---

## Lo que ya funciona y no hay que rehacer

- Pipeline técnico completo: scan, match, rename, CHD, scraper, RA, sync de saves
- Estructura de biblioteca en disco correcta y compatible con RetroArch y EmulationStation
- Arquitectura de módulos limpia fuera de `web/` (sin imports circulares)
- Patrón repository en BD bien aplicado
- Jobs thread-safe con Lock

El trabajo arquitectural no es reescribir — es **reorganizar lo que existe** para que sea mantenible cuando la app crezca.

---

---

# Plan de sesiones

Estimación realista por sesión de trabajo (~2-4h). Las sesiones más largas del plan son las de refactor estructural — se puede pausar entre ellas sin problema porque cada una deja el código funcionando.

---

## Sesión 15 — Quick wins: persistencia y batch run completo ✅

**Objetivo:** eliminar los dos rozamientos más frecuentes del uso diario.

- [x] **B1 / 0C** — `saveOvPaths()` solo guardaba `anbernic_root` en localStorage. Corregido: ahora también escribe en `config.toml` vía `/api/config`. Las rutas persisten entre sesiones.
- [x] **B2 / 0A** — Añadidos Scan, Match y RA Check al batch run. Checkboxes con orden lógico: Escanear → Identificar (DAT) → ZIP → CHD → Health Check → RetroAchievements.

**Al terminar:** rutas persistentes en disco, Tools ejecuta 6 herramientas de una pasada.

---

## Sesión 16 — Comparador de bibliotecas (B3)

**Objetivo:** ver en un vistazo qué diferencia hay entre la biblioteca PC y la Android.

- [ ] Nuevo endpoint `GET /api/library-diff` — compara por SHA1 los juegos de ambas BDs y devuelve: solo en PC / solo en Android / en ambos
- [ ] Nueva sección en la UI (pestaña Sync o Games) que muestra la diff con columnas: plataforma, título, estado
- [ ] Botón "Copiar faltantes a Android" que lanza el sync de ROMs (no solo saves) en dirección pc→android para los elementos marcados
- [ ] Indicador de paridad: "✓ Bibliotecas sincronizadas" / "⚠ X juegos difieren"

**Al terminar:** siempre sabes si las dos bibliotecas son iguales y puedes igualarlascon un clic.

---

## Sesión 17 — Refactor contenido: JobRunner + validación de config

**Objetivo:** dos refactors quirúrgicos que no cambian el comportamiento pero limpian ~400 líneas de código frágil.

- [ ] **Fase 1B** — Extraer clase `JobRunner` en `web/jobs.py`. Reemplazar los 13 handlers duplicados por llamadas a `_job_runner.start(name, fn)`. Verificar que todos los jobs siguen funcionando igual.
- [ ] **Fase 1D** — Añadir método `AppConfig.validate()` en `config.py`. Devuelve lista de warnings. La UI los muestra en Settings como avisos amarillos (rutas inaccesibles, campos vacíos relevantes).

**Al terminar:** `server.py` pierde ~300 líneas, los errores de configuración se ven antes de que causen problemas en runtime.

---

## Sesión 18 — Partir `server.py` (parte 1 de 2)

**Objetivo:** extraer la mitad de los handlers a submódulos. `server.py` pasa de 5.000 a ~3.000 líneas.

- [ ] Crear `web/handlers/` con `__init__.py`
- [ ] Extraer a `handlers/scan.py`: scan, match, fix-platforms, adb-scan
- [ ] Extraer a `handlers/organize.py`: create-library-structure, organize-library, inbox
- [ ] Extraer a `handlers/tools.py`: CHD, ZIP, health-check, orphans, M3U, RA check, junk-scan
- [ ] Actualizar el enrutador en `server.py` para delegar a los nuevos módulos
- [ ] Verificar que todos los endpoints afectados responden igual (smoke test manual)

**Regla:** no cambiar comportamiento, solo mover código. Si algo no está claro, dejarlo en `server.py` y anotarlo.

---

## Sesión 19 — Partir `server.py` (parte 2 de 2)

**Objetivo:** terminar la extracción. `server.py` queda como enrutador puro de ~300 líneas.

- [ ] Extraer a `handlers/sync.py`: cloud sync, cable sync, auto-sync, SD daemon
- [ ] Extraer a `handlers/scraper.py`: scrape, export-gamelists, Pegasus
- [ ] Extraer a `handlers/games.py`: games list, plan, apply, duplicates, assets, play-status
- [ ] Extraer a `handlers/config_handler.py`: config GET/POST, status, drives, test-path
- [ ] Extraer a `handlers/reports.py`: library-report, DB backup, library-diff (sesión 16)
- [ ] Extraer funciones `_build_*` y `_test_*` a `web/response_builders.py`
- [ ] Smoke test de todos los endpoints

**Al terminar:** `server.py` es un enrutador legible. Cada área funcional tiene su propio archivo.

---

## Sesión 20 — Tests para `repository.py`

**Objetivo:** red de seguridad antes de tocar la BD en sesiones futuras.

- [ ] Fixture de BD en memoria (`:memory:`) — helper que crea el schema y devuelve un `LibraryRepository` limpio para cada test
- [ ] Tests de CRUD: `upsert_game`, `upsert_save`, `connect()`, `batch()`
- [ ] Tests de queries críticas: `get_duplicate_groups`, `get_matched_games`, `get_unresolved_games`
- [ ] Tests de operaciones: `apply_rename`, `backfill_platforms`, `prune_stale_entries`
- [ ] Objetivo mínimo: 25 test cases, todos en verde

**Al terminar:** cualquier cambio futuro en la BD tiene cobertura automática.

---

## Sesión 21 — Partir `frontend.py`

**Objetivo:** sacar CSS y JS de la cadena Python. El HTML sigue generándose en Python pero referenciando archivos externos.

- [ ] Añadir handler estático en `server.py`: `GET /static/{file}` sirve archivos de `web/static/`
- [ ] Extraer todo el CSS a `web/static/style.css`
- [ ] Extraer JS a módulos en `web/static/`: `api.js`, `games.js`, `tools.js`, `sync.js`, `settings.js`, `overview.js`
- [ ] `frontend.py` queda como plantilla HTML (~200 líneas) que incluye los `<script src>` y `<link>` correctos
- [ ] Verificar que la UI funciona igual en el navegador

**Nota:** esta es la sesión más delicada. Hacerla despacio, archivo a archivo, probando después de cada extracción.

---

## Sesión 22 — Wizard de primer arranque

**Objetivo:** la app se puede usar sin tocar ningún archivo de texto.

- [ ] Detectar si `config.toml` no existe o está vacío al arrancar → mostrar pantalla de bienvenida
- [ ] Paso 1: selector de carpeta de biblioteca (botón Examinar)
- [ ] Paso 2: auto-detectar RetroArch en rutas comunes, mostrar la encontrada con opción de cambiar
- [ ] Paso 3: auto-detectar cores instalados → pre-rellenar qué sistemas están disponibles
- [ ] Paso 4: detectar dispositivo Android si hay uno conectado
- [ ] Paso 5: crear estructura de carpetas con un clic
- [ ] Guardar `config.toml` al terminar el wizard

---

## Sesión 23 — DATs + Sync sin configuración

**Objetivo:** matching y sync funcionan sin que el usuario sepa qué son un DAT o rclone.

- [ ] **Fase 3**: botón "Descargar catálogos" con lista de sistemas detectados. Descarga los DATs relevantes y los coloca en la carpeta correcta.
- [ ] **Fase 4**: wizard de sync cloud — selector de proveedor (Dropbox/OneDrive/GDrive) → abre navegador para autorizar → genera `rclone.conf` automáticamente
- [ ] Estado de sync siempre visible en la cabecera (último sync + nº archivos)

---

## Sesión 24 — UX y pulido

**Objetivo:** que alguien que nunca ha usado la app pueda orientarse solo.

- [ ] **Fase 5**: reemplazar todos los mensajes de error técnicos por mensajes en lenguaje humano con acción concreta
- [ ] Tooltips `?` en las secciones menos obvias (DATs, CHD, RA, Cable Sync)
- [ ] Renombrar secciones con jerga técnica por nombres descriptivos
- [ ] Verificar que la UI funciona en pantalla estrecha (consola Android en modo navegador)
- [ ] Notificación de sistema al terminar sync (PowerShell toast, sin dependencias externas)

---

## Sesión 25 — Auth, skills y agentes

**Objetivo:** acceso seguro desde la consola + herramientas de desarrollo acelerado.

- [ ] **Fase 6**: PIN de acceso cuando `host = 0.0.0.0`. QR con la URL local en la pantalla principal.
- [ ] **Fase 7**: crear skills `/batch-run`, `/diff-libraries`, `/fix-config`, `/gen-es-config` en `.claude/commands/`
- [ ] Crear agentes `server-splitter`, `repo-test-writer` en `.claude/agents/` para futuros refactors

---

## Sesión 26 — Distribución

**Solo cuando todo lo anterior funciona end-to-end.**

- [ ] Suite de tests de integración completa (pipeline scan → match → sync)
- [ ] PyInstaller: generar `RetroVault.exe` standalone
- [ ] Inno Setup: instalador con acceso directo y entrada en Programas
- [ ] GitHub Actions: pipeline que genera el instalador en cada tag
- [ ] README orientado al usuario final (no al developer)
- [ ] Nombre definitivo

---

## Vista de conjunto

| Sesión | Foco | Riesgo | Resultado visible |
|--------|------|--------|-------------------|
| 15 | Quick wins (persistencia + batch) | Bajo | Rutas se guardan, Tools funciona de una pasada |
| 16 | Comparador de bibliotecas | Medio | Ves en un vistazo si PC = Android |
| 17 | JobRunner + validación config | Bajo | Código más limpio, errores de config visibles |
| 18 | Partir server.py (mitad) | Medio | server.py a la mitad de tamaño |
| 19 | Partir server.py (resto) | Medio | server.py es solo un enrutador |
| 20 | Tests repository.py | Bajo | Red de seguridad para cambios futuros |
| 21 | Partir frontend.py | Alto | JS/CSS editables sin buscar en Python |
| 22 | Wizard primer arranque | Medio | Instalable por cualquiera |
| 23 | DATs + Sync wizard | Medio | Matching y sync sin configuración manual |
| 24 | UX y pulido | Bajo | Usable por alguien sin experiencia técnica |
| 25 | Auth + skills/agentes | Bajo | Acceso seguro, desarrollo más rápido |
| 26 | Distribución | Alto | Instalador `.exe` publicado |

**Total estimado: 12 sesiones** desde aquí hasta distribución.
Las sesiones 18-19 y 21 son las más largas y se pueden pausar a mitad sin dejar el proyecto roto — simplemente algunos handlers siguen en `server.py` hasta que se termina la extracción.
