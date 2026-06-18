# Retro Vault — Backlog

> Single source of truth for pending work. Updated every session.
> Last updated: 2026-04-27 (tareas del Roadmap y ARC pendientes subdivididas en sub-pasos)
> Completed tasks → `Tareas/diario/archivo/archivo.md`
> Architecture reference: `docs/architecture/Roadmap-Arquitectura-Frontend.md`

---

## Agrupación en ramas (plan de branching)

Regla: una rama por tarea → PR a `develop`. Las sub-tareas que comparten fichero o
son la misma unidad de cambio se agrupan en una sola rama. Refactores grandes de un
fichero van **siempre separados**.

### Día26 — completado ✅ (robustez/perf/SRP)

| Orden | Rama | Tareas | Estado |
|-------|------|--------|--------|
| ✅ | `feature/obs-1c-lint-no-bare-except` | OBS-1c | mergeada (#13) |
| ✅ | `feature/perf-1-hashing` | PERF-1a + 1b + 1c | mergeada (#14) |
| ✅ | `test/test-1-sync-daemons` | TEST-1a + 1b + 1c | mergeada (#15) |
| ✅ | `chore/fix-build-conda` | FIX-1 + FIX-2 | en rama |
| ✅ | `refactor/srp-1{a,b,c}-*` | SRP-1a (PR #17) / 1b (PR #18) / 1c (PR #19) | ✅ |
| ✅ | `chore/clean-1-late-imports` | CLEAN-1 | PR #20 (handlers hoisted en server.py; docstrings de daemons al día) |

> **Día26 completado.** Plan de la sesión actual en `Tareas/diario/Día27.md`.
> Detalle/justificación del Día26 en `Tareas/diario/archivo/Día26.md`.

### Foco activo (Día27 — completar la migración al JobManager)

| Orden | Rama | Tareas | Estado |
|-------|------|--------|--------|
| ✅ | `refactor/arc-jm-cable` | ARC-JM-3a + 3b + 3c | mergeada (#22) — cable_sync → JobManager |
| ✅ | `refactor/arc-jm-cleanup` | ARC-JM-6a + 6b + 6c + 6d | mergeada (#23) — globales legados eliminados |
| ✅ | `refactor/arc-cfg-device-detector` | ARC-CFG-3a + 3b | mergeada (#24) — `is_device_connected` → `sync/device_detector.py` |
| ✅ | `refactor/arc-cfg-sync` | ARC-CFG-1a–1d | mergeada (#25) — dataclass `SyncConfig` |
| ✅ | `refactor/arc-cfg-credentials` | ARC-CFG-2a–2c | mergeada (#26) — dataclass `CredentialsConfig` (secretos con `repr=False`) |
| ✅ | `refactor/arc-cfg-inbox-backup` | ARC-CFG-4a–4c | en rama — `InboxConfig` + `BackupConfig` |

> **Migración al JobManager (ARC-JM 1→6) completa** y **split de `AppConfig` (ARC-CFG) completo**:
> `device_detector` extraído + dataclasses `SyncConfig` / `CredentialsConfig` / `InboxConfig` /
> `BackupConfig`. `AppConfig` ya no tiene campos planos de esos dominios. Resto de clusters abajo.

### Clusters del backlog (al retomar esas líneas)

| Rama | Tareas | Por qué juntas / bloqueo |
|------|--------|--------------------------|
| ~~`refactor/arc-jm-cable`~~ ✅ | ARC-JM-3a + 3b + 3c | Migración indivisible de `cable_sync` al JobManager (#22) |
| ~~`refactor/arc-jm-cleanup`~~ ✅ | ARC-JM-6a + 6b + 6c + 6d | Barrido de limpieza de globales (en rama) |
| ~~`refactor/arc-cfg-device-detector`~~ ✅ | ARC-CFG-3a + 3b | Extraído `device_detector.py` (#24) |
| ~~`refactor/arc-cfg-sync`~~ ✅ | ARC-CFG-1a–1d | Dataclass `SyncConfig` atómica (#25) |
| ~~`refactor/arc-cfg-credentials`~~ ✅ | ARC-CFG-2a–2c | Dataclass `CredentialsConfig` atómica (#26) |
| ~~`refactor/arc-cfg-inbox-backup`~~ ✅ | ARC-CFG-4a–4c | `InboxConfig` + `BackupConfig` (en rama) |
| ~~`refactor/arc-svc-duplicates`~~ ✅ | ARC-SVC-1a + 1b | Service + adelgazar handler (en rama) |
| `feature/design-polish` | DESIGN-10 + 11 + 12 (+13, +14) | Cosmético sobre `app.css` / `index.html` |

---

### SRP-1a — Desglose (rama `refactor/srp-1a-response-builders`) ✅ COMPLETADO (PR #17)

`web/response_builders.py` (1658 líneas) → paquete `web/builders/`; fachada eliminada
y 15 callers migrados. Detalle en `Tareas/diario/archivo/Día26.md §SRP-1a`.

- [x] SRP-1a-0 — crear `web/builders/` + fachada de re-export (sin mover lógica)
- [x] SRP-1a-1 — `builders/common.py` (helpers: json/paths/drives/repo/format)
- [x] SRP-1a-2 — `builders/library.py` (report/status/games/plan)
- [x] SRP-1a-3 — `builders/duplicates.py` (duplicates + RA annotate)
- [x] SRP-1a-4 — `builders/diff.py` + `builders/folders.py`
- [x] SRP-1a-5 — `builders/misc.py` (assets/sync_log/config/scrape/cable)
- [x] SRP-1a-6 — migrar imports de callers + eliminar fachada; tests + ruff

### SRP-1b — Desglose (rama `refactor/srp-1b-esde`) ✅ COMPLETADO (PR #18)

`web/handlers/esde.py` (1158 líneas; `register()` ≈965) → paquete `web/handlers/esde/` con
sub-registradores por dominio; `register()` orquesta. 7 sub-pasos; detalle en `Tareas/diario/archivo/Día26.md §SRP-1b`.

- [x] SRP-1b-0 — paquete `esde/` + esqueleto de sub-registradores; `register()` delega
- [x] SRP-1b-1 — conversiones (chd/cso/zip/m3u/n64/multidisc) → `esde/conversions.py`
- [x] SRP-1b-2 — reports/export (report html/json/csv, export_lpl) → `esde/reports.py`
- [x] SRP-1b-3 — health/cleanup/junk → `esde/maintenance.py`
- [x] SRP-1b-4 — orphaned saves + doctor → `esde/doctor.py`
- [x] SRP-1b-5 — ES-DE + sistema/misc + helpers `_handle_*` → `esde/system.py`
- [x] SRP-1b-6 — `register()` como orquestador puro; tests + ruff

### SRP-1c — Desglose (rama `refactor/srp-1c-repository`) ✅ COMPLETADO (PR #19)

`database/repository.py` (1455 líneas; clase única de ~50 métodos) → paquete
`database/repositories/` con un mixin por agregado; `LibraryRepository` los ensambla.
API pública intacta (dataclasses re-exportadas desde `repository.py`). Detalle en `Tareas/diario/archivo/Día26.md §SRP-1c`.

- [x] SRP-1c-0 — `repositories/` + `models.py` (dataclasses) + `base.py` (`_RepositoryBase`: connect/batch/scan-run/get_summary)
- [x] SRP-1c-1 — `GamesMixin` (`games.py`)
- [x] SRP-1c-2 — `MetadataMixin` (`metadata.py`: tags/favoritos/notas/NLP/scraping)
- [x] SRP-1c-3 — `SyncMixin` (`sync.py`: saves + sync log)
- [x] SRP-1c-4 — `AssetsMixin` (`assets.py`)
- [x] SRP-1c-5 — `DuplicatesMixin` (`duplicates.py`: duplicados + wishlist)
- [x] SRP-1c-6 — `LibraryRepository` ensambla los mixins; tests + ruff

---

## Debug Playbook

Checklist de puntos de entrada para diagnosticar cualquier problema en el app.

| ID | Técnica | Cómo | Dónde mirar |
|----|---------|------|-------------|
| DBG-1 | Lanzar servidor con logs en terminal | `scripts\rommgr.cmd serve` (o `-m rom_manager serve`) — stdout muestra requests, errores y jobs | Terminal |
| DBG-2 | Verificar esquema SQLite | `/db-check` skill, o `sqlite3` / DB Browser sobre `.rommgr/*.db` | `database/repository.py`, `schema.py` |
| DBG-3 | Testear pipeline por etapas | `rommgr.cmd scan --dry-run` → `plan` → (nunca `apply` sin plan) | CLI |
| DBG-4 | Diagnosticar jobs en background | DevTools → Network → `/api/job-status` cada 2s; buscar `result_ts` ausente en respuesta | `web/server.py`, `web/jobs/manager.py` |
| DBG-5 | Verificar ADB / sync | `tools\adb.exe devices`, `tools\adb.exe shell ls /sdcard/RetroArch/saves` | `sync/adb_transport.py` |
| DBG-6 | Logging puntual por módulo | `import logging; logging.basicConfig(level=logging.DEBUG)` en el módulo sospechoso | `logging_utils.py` |
| DBG-7 | Test integración completa | Skill `/test-pipeline` — scan → match → plan sobre datos sintéticos | — |

### Síntomas frecuentes

| Síntoma | Dónde mirar |
|---------|-------------|
| UI no actualiza | `frontend.py` polling + `result_ts` en `server.py` |
| Config no persiste tras guardar | `_handle_save_config()` en `handlers/config.py` (recarga obligatoria) |
| Renombrado PSX roto | `cue_rewriter.py` + `operation_planner.py` |
| ADB no encuentra saves | `adb_transport.py` (mapeo de rutas por emulador) |
| Circular import al arrancar | Late imports en `cable_sync_daemon.py` / `inbox_pipeline.py` |
| 404 en rutas registradas | `router.dispatch()` — ver BUG-ROUTING-404 en `archivo.md` |

---

## Roadmap App Universal

### Phase 1 — Frictionless first run

| ID | Task | Estado |
|----|------|--------|
| PHASE1-1 | Auto-detect RetroArch paths (common + Steam + RetroBat) | ✅ `GET /api/detect-retroarch` + botón en Settings |
| PHASE1-2 | Auto-detect cores from `cores/` folder; warn if missing | ✅ cores status inline en Settings + warnings en banner + key_cores ampliado (15 plataformas) |
| PHASE1-3 | Generate `es_systems.cfg` from detected cores | ⬜ |
| PHASE1-4 | Auto-detect Android device via ADB on USB connect | ✅ `cable_sync_daemon.py` (commit 2a3c579) |
| PHASE1-5 | Folder picker with "Browse" button in Settings fields | ⬜ |

### Phase 2 — DATs without effort

| ID | Task | Estado |
|----|------|--------|
| PHASE2-1 | Guided DAT download with contextual explanation | ✅ aviso contextual en paso ② Match del Overview + link directo a Settings → Catálogos DAT |
| PHASE2-2 | Clear UI for matching mode (with DAT vs by filename) | ✅ `tab-games.html` (commit ccb3a8e) |

### Phase 3 — Sync without config

| ID | Task | Estado |
|----|------|--------|
| PHASE3-1a | Research SFTP server options on Termux (dropbear vs openssh) | ⬜ prereq: V5 |
| PHASE3-1b | Implement `sftp_transport.py` (upload/download/list) | ⬜ |
| PHASE3-1c | UI: WiFi sync toggle + status en Settings | ⬜ |
| PHASE3-2 | Auto-sync on connect — detect via ADB, prompt "Sync now?" | ✅ (commit 2a3c579) |
| PHASE3-3 | Sync status always visible in header | ✅ (commit 7eba736) |

### Phase 4 — Non-technical UX

| ID | Task | Estado |
|----|------|--------|
| PHASE4-1 | Human-readable errors — capturar excepciones en handlers y devolver mensaje legible | ⬜ |
| PHASE4-2 | Contextual help — tooltips y `?` icons por sección | ⬜ |
| PHASE4-3 | Responsive UI — media queries para viewport 480px (Android browser) | ⬜ |
| PHASE4-4 | Windows toast notifications en sync complete / inbox detected | ⬜ |
| PHASE4-5 | Renombrar jargon: "DATs" → "Base de datos", "SHA1 match" → "Identificación automática" | ⬜ |

### Phase 5 — Auth

| ID | Task | Estado |
|----|------|--------|
| PHASE5-1 | Forzar PIN cuando `host != 127.0.0.1` (no solo advertir) | ⬜ prereq: SEC-3 ya avisa |

### Phase 6 — Distribution

| ID | Task | Estado |
|----|------|--------|
| PHASE6-1a | Crear `RetroVault.spec` — PyInstaller con static assets, templates y `tools/` bundled | ⬜ |
| PHASE6-1b | Probar ejecutable en máquina limpia (sin Python) | ⬜ |
| PHASE6-2a | Escribir script Inno Setup — shortcut + Add/Remove Programs | ⬜ |
| PHASE6-2b | Bundlear DATs mínimos en el installer | ⬜ |
| PHASE6-3a | Endpoint `/api/version` + check de actualizaciones al arrancar | ⬜ |
| PHASE6-3b | Descarga y aplicación de update desde GitHub Releases | ⬜ |
| PHASE6-4 | Decidir nombre final: Retro Vault vs Retro Companion | ⬜ |

---

## Roadmap — Ideas from Idea_final.md

Extracted from `docs/ideas/Idea_final.md` and broken into actionable tasks.

---

### COL-REVIEW — Decide fate of Colección tab ✅ COMPLETADO

| ID | Task | Estado |
|----|------|--------|
| COL-REVIEW-1 | Audit: decidido → KEEP Colección (gallery, missing ROMs, diff, disk usage son únicos) | ✅ |
| COL-REVIEW-2b | Playtime en galería: `last_played_at`, `play_count`, `user_rating` en tiles + sort "Jugados recientemente" | ✅ `collection.js` + `app.css` + `tab-collection.html` |
| COL-REVIEW-2a | **Descartado** — Colección tiene valor único, no se fusiona | — |
| COL-REVIEW-2c | RA sync — fetch logros del usuario por juego y mostrar en tab | ✅ tile badge `🏆N` + progreso en panel |

---

### FLOW-WIZARD — Unified "run all" wizard ✅ COMPLETADO

| ID | Task | Estado |
|----|------|--------|
| FLOW-WIZARD-1 | Backend: wizard-detect + plan-all | ✅ `flow_wizard.js` + `handlers/` |
| FLOW-WIZARD-2 | Frontend: modal shell con pasos | ✅ `flow_wizard.js` + partials |
| FLOW-WIZARD-3 | Per-step diff view | ✅ implementado |
| FLOW-WIZARD-4 | Ejecución secuencial + resumen | ✅ implementado |

---

### CLOUD-RESEARCH — rclone + Termux for Dropbox sync ✅ COMPLETADO

| ID | Task | Estado |
|----|------|--------|
| CLOUD-RESEARCH-1 | Document rclone setup on PC | ✅ `docs/sync/sync-cloud.md` |
| CLOUD-RESEARCH-2 | Document Termux setup on Anbernic RG556 | ✅ `docs/sync/Guia-Termux-Anbernic.md` |
| CLOUD-RESEARCH-3 | Define sync protocol + conflict policy | ✅ sync-cloud.md §6 |
| CLOUD-RESEARCH-4 | rclone_transport.py con upload/download/list_remote | ✅ implementado |
| CLOUD-RESEARCH-5 | Cloud sync UI con estado + último sync en header | ✅ sync.js |

---

### EMULATOR-COMPAT — Save compatibility PC ↔ Android

Verify that synced saves from PC actually load on Android and vice versa, for each emulator pair.

| ID | Task | Notes |
|----|------|-------|
| EMULATOR-COMPAT-1 | Create compatibility matrix — PC emulator, Android emulator, save format, save path per platform | `docs/emulator-compat.md` |
| EMULATOR-COMPAT-2 | Test PS1 round-trip: DuckStation PC → sync → DuckStation Android → load | Hardware test with RG556 |
| EMULATOR-COMPAT-3 | Test PS2 round-trip: PCSX2 PC → sync → AetherSX2/NetherSX2 Android → load | Hardware test |
| EMULATOR-COMPAT-4 | Test remaining platforms (GBA, SNES, GBC, NDS…) and document any format mismatches | Update matrix per result |

---

### ANBERNIC-TV — TV-friendly UI for console browsing ✅ COMPLETADO

| ID | Task | Estado |
|----|------|--------|
| ANBERNIC-TV-1 | Diseño: 3 pasos — Status → Sync → Results, touch targets grandes | ✅ |
| ANBERNIC-TV-2 | CSS responsive — `.tv-step`, `.tv-btn`, media query 600px | ✅ `app.css` |
| ANBERNIC-TV-3 | Paso 1: connection OK + último sync desde `/api/auto-sync-status` | ✅ `sync.js:tvCheckStatus()` |
| ANBERNIC-TV-4 | Paso 2: trigger `/api/do-sync` + polling con barra animada | ✅ `sync.js:tvStartSync()` |
| ANBERNIC-TV-5 | Paso 3: resumen ↑ enviados / ↓ recibidos / errores + botón "Sync de nuevo" | ✅ `sync.js:tvShowResult()` |

---

### ARCADE-SETUP — Research arcade ROM config (no code)

| ID | Task | Notes |
|----|------|-------|
| ARCADE-SETUP-1 | Research MAME vs FBNeo ROM set version compatible with Anbernic RG556 RetroArch | Check RG556 community guides |
| ARCADE-SETUP-2 | Identify target arcade systems and map each to the correct RetroArch core | e.g. CPS1/2/3, Neo-Geo, MAME 2003 Plus |
| ARCADE-SETUP-3 | Document config additions: `config.toml`, library-structure, DAT sources for arcade | `docs/arcade-setup.md` |
| ARCADE-SETUP-4 | Test a sample ROM end-to-end: scan → rename → launch on device | Hardware test |

---

### NLP-REC — Recomendador de juegos con NLP ✅ COMPLETADO

Infraestructura de datos en el ROM Manager para alimentar el modelo NLP de recomendación.

| ID | Task | Estado |
|----|------|--------|
| NLP-REC-1 | Schema: columnas `user_rating`, `play_count`, `first_played_at` en tabla `games` + migración retrocompatible | ✅ `database/schema.py` |
| NLP-REC-2 | Backend: poblar `play_count` + timestamps automáticamente al detectar saves en sync | ✅ `database/play_history.py` + `sync/save_syncer.py` |
| NLP-REC-3 | Backend: `GET /api/play-history`, `POST /api/play-history` (rating, status, tags, notes) | ✅ `handlers/play_history.py` |
| NLP-REC-4 | Frontend: widget de 5 estrellas (rating) + contador de sesiones en game panel | ✅ `_foot.html` + `games.js` + `app.css` |
| NLP-REC-5 | Export: `GET /api/export-history` — JSON con todos los juegos + metadatos para el modelo NLP | ✅ `handlers/play_history.py` |
| NLP-REC-6 | Import: `POST /api/recommendations` + `GET /api/recommendations` + panel "Recomendados" en tab Juegos | ✅ `handlers/play_history.py` + `tab-games.html` + `games.js` |

---

## ULTRAREVIEW-0421 — Bugs detectados por revisión automática (2026-04-21)

Origen: revisión de los 9 archivos cambiados en la rama `main` (420 ins / 230 del).

| ID | Severidad | Task | Archivo | Estado |
|----|-----------|------|---------|--------|
| UR-1 | 🔴 Normal | **SD daemon no arranca si se activa desde la UI tras el inicio** — quitar la condición de startup en `serve()` y dejar que el loop interno en `cable_sync_daemon.py:486` se autogestione (ya lo hace). | `server.py:1328-1336` | ✅ |
| UR-2 | 🔴 Normal | **RA: badges falsos por fallback de título** — `_enrich_games_with_ra` asigna 🏆N de una ROM regional distinta cuando falla el match MD5. Eliminar el fallback del listado, o propagar estado `"alternative"` con badge diferenciado y aplicarlo también al endpoint `/api/game` (detalle). | `handlers/games.py:57-69` | ✅ |
| UR-3 | 🔴 Normal | **RA: inconsistencia lista vs detalle** — `/api/games` usa fallback por título; `/api/game` es solo MD5. Un juego muestra badge en la grid pero lo pierde en la vista de detalle. Resolver junto con UR-2. | `handlers/games.py:~260` | ✅ |
| UR-4 | 🟡 Normal | **RA: caché de hashes re-parseada en cada request** — `hl_by_cid`/`ti_by_cid` son locales a `_enrich_games_with_ra`, se reconstruyen desde disco en cada `/api/games`. Mover a nivel módulo keyed por `(cid, mtime)`, siguiendo el patrón `_ra_progress_cache` (línea 17). | `handlers/games.py:44-55` | ✅ |
| UR-5 | ⚪ Nit | **RA: `try/except` demasiado amplio corta el enriquecimiento para todos los juegos** — un JSON corrupto o error en una plataforma aborta el loop entero. Mover el try/except dentro del cuerpo del loop con un `continue` en el except. | `handlers/games.py:65-71` | ✅ |

> **Orden recomendado:** UR-5 → UR-4 → UR-2+UR-3 (juntas) → UR-1

---

## SEC — Fallos de ciberseguridad (detectados 2026-04-22)

| ID | Severidad | Task | Archivo | Estado |
|----|-----------|------|---------|--------|
| SEC-1 | 🔴 Crítico | **Command injection en ADB** — Las rutas Android se interpolan con f-strings directamente en comandos shell (`find_cmd = f"find {android_path} ..."`). Un valor malicioso ejecuta comandos arbitrarios en el dispositivo. Fix: usar listas de argumentos separados o `shlex.quote()` sobre las rutas antes de interpolar. | `sync/adb_transport.py:131,177,193` | ✅ `shlex.quote()` en los 5 puntos de inyección |
| SEC-2 | 🔴 Crítico | **Credenciales en texto plano en la API** — `GET /api/config` devuelve `screenscraper_pass`, `screenscraper_dev_pass` y `ra_api_key` en claro. Fix: devolver solo `{configured: true/false}`, nunca el valor real. | `web/response_builders.py:1320-1326` | ✅ Devuelve `*_set: bool`; frontend muestra placeholder `••••••••` |
| SEC-3 | 🟠 Alto | **Sin autenticación por defecto** — El PIN es opcional; sin él, todos los endpoints (scan, sync, borrar, exportar config) son accesibles sin autenticación. Si el servidor escucha en `0.0.0.0`, toda la LAN tiene acceso libre. Fix: forzar PIN cuando `host != 127.0.0.1`, o activarlo por defecto. | `web/server.py:974-991` | ✅ Warning en arranque si host != 127.0.0.1 y sin PIN |
| SEC-4 | 🟠 Alto | **`rclone.conf` completo accesible vía API** — `GET /api/rclone-export-config` devuelve el archivo con tokens OAuth y secrets de todos los servicios cloud. Desprotegido si no hay PIN (ver SEC-3). Fix: exigir PIN siempre en este endpoint independientemente de la config global. | `web/handlers/sync.py:174-190` | ✅ Bloquea el endpoint si host != 127.0.0.1 y sin PIN |
| SEC-5 | 🟡 Medio | **Sin rate limiting en `POST /api/auth`** — Fuerza bruta al PIN sin ninguna limitación. Un PIN de 4 dígitos son solo 10.000 combinaciones. Fix: delay progresivo + bloqueo por IP tras N intentos fallidos. | `web/server.py:1080-1095` | ✅ Lockout por IP tras 10 intentos en 60s (5 min bloqueo) |
| SEC-6 | 🟡 Medio | **Cookie de sesión sin flag `Secure`** — La cookie tiene `HttpOnly` y `SameSite=Strict` pero no `Secure`. Si el servidor se expone via proxy HTTPS o túnel, el token viaja en claro. Fix: añadir `Secure` al header `Set-Cookie`. | `web/server.py:997-998` | N/A — app es HTTP-only; añadir `Secure` rompería las sesiones HTTP |
| SEC-7 | ⚪ Bajo | **Logs accesibles vía API sin límite de tamaño** — `GET /api/logs` acepta el parámetro `lines` sin valor máximo validado; un valor muy alto puede causar un pico de memoria si el log es grande. Fix: clamp a un máximo razonable (ej. 5000 líneas). | `web/handlers/scan.py:139-164` | ✅ `min(lines_n, 5000)` |

> **Orden recomendado:** SEC-1 → SEC-2 → SEC-3 → SEC-4 → SEC-5 → SEC-6 → SEC-7

---

## ARC — Fallos de arquitectura (detectados 2026-04-22)

### Completados

| ID | Severidad | Task | Archivo | Estado |
|----|-----------|------|---------|--------|
| ARC-4 | 🟡 Medio | **Config mutable desde handlers sin sincronización** — `_save_config` mutaba los campos de `AppConfig` sin lock mientras threads de background podían estar leyéndolos. | `web/handlers/config.py` | ✅ `_config_lock` en `_save_config`, todas las asignaciones dentro del lock |

### Pendientes — Migración al JobManager (ARC-1 + ARC-2)

> Contexto: ya existe `web/jobs/manager.py` (`JobManager`) con locking correcto. Sustituye los 12 dicts de progreso globales y `_jobs`/`_job_results` de `server.py`. Solo falta migrar los handlers a usarlo.

| ID | Severidad | Task | Archivo | Estado |
|----|-----------|------|---------|--------|
| ARC-JM-1 | 🟠 Alto | **Instanciar `JobManager` y exponerlo en `make_handler`** — Crear `_job_manager = JobManager()` a nivel de módulo en `server.py` y pasarlo a todos los handlers vía `register(router, ..., job_manager=_job_manager)`. | `web/server.py`, `web/jobs/manager.py` | ✅ Instanciado + cableado a los 8 handlers; `"tree_diff"` y `"verify_chd"` añadidos a `JOB_NAMES` |
| ARC-JM-2 | 🟠 Alto | **Migrar handlers de scan y apply al JobManager** — Reemplazar accesos a `m._scan_progress`, `m._apply_progress`, `m._jobs["scan"]`, `m._job_results["scan"]` por llamadas a `job_manager`. | `web/handlers/scan.py` | ✅ `_do_scan`, `_do_adb_scan`, `_do_match`, `_do_apply` migrados; `get_job_status` híbrido hasta ARC-JM-6 |
| ARC-JM-3 | 🟠 Alto | **Migrar handlers de sync y cable al JobManager** | `web/handlers/sync.py`, `sync_cable.py` | ✅ `sync`/`tree_diff` + `cable_sync` migrados (rama `refactor/arc-jm-cable`) |
| ARC-JM-3a | | ↳ Daemons de cable (`_auto_sync_loop`, `_run_sd_auto_sync`, `_sd_card_sync_loop`) usan `_state._job_manager` directamente (patrón inbox/health) | `web/cable_sync_daemon.py` | ✅ |
| ARC-JM-3b | | ↳ *(replanteado)* sin `on_progress` ni cableado en `server.py`: el patrón establecido es `_state._job_manager` directo | `web/cable_sync_daemon.py` | ✅ |
| ARC-JM-3c | | ↳ Handler `cable_sync` (en `sync_cable.py`, no `sync.py`) + hub `job-status`/`stop-job` en `scan.py` → `job_manager` | `web/handlers/sync_cable.py`, `scan.py` | ✅ |
| ARC-JM-4 | 🟡 Medio | **Migrar handlers de CHD, CSO, ZIP, scraper, health, RA al JobManager** — 6 handlers con patrón idéntico. | `handlers/organize.py`, `handlers/scraper.py`, `handlers/games.py` | ✅ ZIP + health en `esde.py`; RA en `sync.py` + scheduler en `server.py`; scraper/CHD/CSO/verifyChd ya migrados. `scan.py` híbrido limpiado. |
| ARC-JM-5 | 🟡 Medio | **Migrar handler de inbox y setup al JobManager** — Reemplazar `m._inbox_progress`, `m._setup_progress`. | `handlers/inbox.py`, `web/server.py` (setup) | ✅ `_run_inbox_pipeline` y `_run_setup_pipeline` usan `job_manager`; watcher migrado; `get_setup_status` e `inbox-status` limpios. |
| ARC-JM-6 | 🟡 Medio | **Eliminar los globales legados y `srv_mod`** | `web/state.py`, `server.py`, handlers | ✅ rama `refactor/arc-jm-cleanup` |
| ARC-JM-6a | | ↳ Auditados todos los globales legados en `web/` (grep exhaustivo) | — | ✅ |
| ARC-JM-6b | | ↳ Eliminados los 12 `_*_progress` + los 10 `_*_cancel` de `state.py` (muertos) | `web/state.py` | ✅ |
| ARC-JM-6c | | ↳ Eliminados `_jobs`/`_job_results`/`_job_lock` + helper muerto `_start_job`; repuntado `duplicates.py` (`ra_check`) a `job_manager` (arregla bug latente) | `web/state.py`, `server.py`, `duplicates.py` | ✅ |
| ARC-JM-6d | | ↳ Eliminado `srv_mod` de `make_handler` + 8 `register()` (+ alias `_srv_mod`); 7 accesos `srv_mod.X` → `_state.X` | `web/server.py`, handlers | ✅ |

> **Orden:** ARC-JM-1 → ARC-JM-2 → ARC-JM-3 → ARC-JM-4 → ARC-JM-5 → ARC-JM-6 — **todos ✅**

### Pendientes — Split de AppConfig (ARC-3)

| ID | Severidad | Task | Archivo | Estado |
|----|-----------|------|---------|--------|
| ARC-CFG-3 | 🟡 Medio | **Mover `is_device_connected()` fuera de `AppConfig`** | `sync/device_detector.py` | ✅ (#24) |
| ARC-CFG-3a | | ↳ Crear `sync/device_detector.py` con `is_device_connected(adb_path, android_root)` | `sync/device_detector.py` | ✅ |
| ARC-CFG-3b | | ↳ Eliminar método de `AppConfig`; actualizar callers a importar de `device_detector` | `config.py`, callers | ✅ |
| ARC-CFG-1 | 🟡 Medio | **Extraer `SyncConfig`** — `rclone_remote`, `auto_sync_*`, `conflict_policy`, `saves_remote`, `states_remote`, `sync_sources` | `config.py` | ✅ (#25) |
| ARC-CFG-1a | | ↳ Definir dataclass `SyncConfig` con defaults en `config.py` | `config.py` | ✅ |
| ARC-CFG-1b | | ↳ Sustituir campos planos en `AppConfig` por `sync: SyncConfig` | `config.py` | ✅ |
| ARC-CFG-1c | | ↳ Actualizar `load_config` (construcción anidada) | `config.py` | ✅ |
| ARC-CFG-1d | | ↳ Actualizar ~40 callers a `config.sync.X` (cli, server, daemons, handlers, builders) | varios | ✅ |
| ARC-CFG-2 | 🟡 Medio | **Extraer `CredentialsConfig`** — `screenscraper_*`, `ra_api_key`, `ra_username`, `web_pin_*` | `config.py` | ✅ (#26) |
| ARC-CFG-2a | | ↳ Definir dataclass `CredentialsConfig` (secretos con `repr=False`) | `config.py` | ✅ |
| ARC-CFG-2b | | ↳ Mover campos + `load_config` anidado; secretos no se filtran en logs/tracebacks | `config.py` | ✅ |
| ARC-CFG-2c | | ↳ Actualizar callers en scraper, RA, auth y server | handlers | ✅ |
| ARC-CFG-4 | ⚪ Bajo | **Extraer `InboxConfig` y `BackupConfig`** | `config.py` | ✅ (en rama) |
| ARC-CFG-4a | | ↳ Definir `InboxConfig`; mover campos `inbox_*` → `config.inbox.*` | `config.py` | ✅ |
| ARC-CFG-4b | | ↳ Definir `BackupConfig`; mover `backup_*`/`pre_sync_backup` → `config.backup.*` | `config.py` | ✅ |
| ARC-CFG-4c | | ↳ Actualizar callers (daemons, inbox, organize, sync_cloud, games, builders) | handlers | ✅ |

> **Orden:** ARC-CFG-3 → ARC-CFG-1 → ARC-CFG-2 → ARC-CFG-4 — **todos ✅** (split de `AppConfig` completo).

### Pendientes — Capa de servicio (ARC-5)

| ID | Severidad | Task | Archivo | Estado |
|----|-----------|------|---------|--------|
| ARC-SVC-1 | ⚪ Bajo | **Extraer lógica de negocio de `duplicates.py`** | `web/handlers/duplicates.py` | ✅ (en rama) |
| ARC-SVC-1a | | ↳ `services/duplicates_service.py` con `delete_duplicate` y `delete_all_duplicates` puras (sin `ctx`, devuelven dict serializable); `_force_remove` movido al service | `services/` (nuevo) | ✅ |
| ARC-SVC-1b | | ↳ Handler delega: rutas `/api/duplicates/delete{,-all}` llaman al service y hacen `_send_json`; tests unitarios en `tests/test_duplicates_service.py` | `web/handlers/duplicates.py` | ✅ |

---

## Hardware validation (requires console or SD card)

| ID | Task |
|----|------|
| V1 | SD card auto-sync — configure `anbernic_root`, insert SD, verify banner + log |
| V2 | Two-database migration — Settings → "Migrate DB" → verify separate PC/Android counts |
| V3 | Inbox end-to-end — configure `inbox_path`, drop ZIP, verify extraction + rename + move |
| V4 | RetroAchievements with real API key |
| V5 | Termux guide on console — prereq for WiFi sync |
| B1-hw | Android renamer doesn't reduce queue — test with SD inserted |

---

## Frontend redesign — Design system integration

**Scope**: Integrate new RetroVault UI design system (colors_and_type.css + Lucide icons) into existing vanilla JS frontend. Maintains backend compatibility; purely visual upgrade.

**Status**: Discovery complete. Design assets ready (`~/Desktop/ui_kits/`, `~/Desktop/preview/`, `colors_and_type.css`).

### Core tasks (Phase 1 — CSS + fonts)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| DESIGN-1 | Add `--rv-*` token variables to `app.css` | ✅ | Colors, typography, spacing, radius, shadow, transition, z-index. Alias to existing `--` vars where identical (e.g. `--rv-bg: var(--bg)`) |
| DESIGN-2 | Add Google Fonts import | ✅ | Exo 2 (display), Space Mono (mono), Inter (body). Via `<link>` tags in `index.html` + preconnect |
| DESIGN-3 | Update body font-family | ✅ | `font-family: var(--rv-font-body);` (Inter instead of system-ui) |
| DESIGN-4 | Add cyberpunk animations | ✅ | `@keyframes rv-glitch`, `rv-shimmer`, `rv-prog-slide`, `rv-tab-in`, `rv-toast-in`, `.rv-skeleton` |
| DESIGN-5 | Add `.rv-brand-glitch` class to header | ✅ | Logo already has glitch effect (cp-glitch), add rv variant + apply to `<h1>` |

### Lucide icons integration (Phase 2 — nav)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| DESIGN-6 | Add Lucide CDN + script initialization | ✅ | `<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>` + `lucide.createIcons()` call en `_foot.html` |
| DESIGN-7 | Replace emoji nav icons with Lucide | ✅ | 15 tabs mapeados (house, gamepad-2, layout-list, copy, image, star, cloud, usb, smartphone, wrench, disc, layers, inbox, tv, settings) |
| DESIGN-8 | Update `.nav-icon` CSS for SVG | ✅ | Ya estaba: `display:flex` + `.nav-icon svg { width:15px; height:15px }` |
| DESIGN-9 | Test icon rendering in sidebar (expanded + collapsed) | ✅ | Verificado visualmente — Lucide icons renderizan OK en expanded y collapsed |

### Optional (Phase 3 — polish)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| DESIGN-10 | Update device selector bar styling | ⬜ | Use CSS variables instead of hardcoded `#161626` / `#2a2a2a` |
| DESIGN-11 | Add description bar below device selector | ⬜ | Show current tab name + 1-sentence description (from `TABS` config) |
| DESIGN-12 | Convert remaining hardcoded colors to variables | ⬜ | Game panel, footer, inline styles (~100+ places) — low priority, cosmetic |
| DESIGN-13 | Test light theme with new fonts | ⬜ | Verify Inter + Exo 2 readable on light bg; no scanlines overlay ([data-theme="light"] already disabled it) |
| DESIGN-14 | Performance audit | ⬜ | Google Fonts CDN + Lucide CDN impact; consider preload/prefetch hints |

### Files to modify

- **`src/rom_manager/web/static/app.css`** — Add `--rv-*` tokens, animations, update fonts/border-radius
- **`src/rom_manager/web/static/index.html`** — Add Google Fonts `<link>` + Lucide `<script>`, add glitch class to `<h1>`
- **`src/rom_manager/web/static/partials/_nav.html`** — Replace emoji icons with Lucide `<i data-lucide>`
- **`src/rom_manager/web/static/partials/_foot.html`** — Add `lucide.createIcons()` initialization (non-module script before main.js)

### Design assets (reference only)

- `docs/design/ui_kits/retrovault/` — React prototype (FYI, not needed for integration)
- `docs/design/preview/` — 16 reference HTML files (component showcase)
- `docs/design/colors_and_type.css` — Source of truth for tokens + animations
- `.claude/plugins/retrovault-design/` — Design system skill (Claude)

---

## User actions (no code needed)

| ID | Task |
|----|------|
| STRUCT-4 | Configure RetroArch PC: Saving → Savefile Directory → `E:\Carpetas anbernic\saves\` |
| STRUCT-3 | Update `config.toml`: `local_dir = "E:\\Carpetas anbernic\\saves"` (after STRUCT-4) |
| ES-1 | Download `genesis_plus_gx` core in RetroArch → Online Updater |
| ES-2 | Configure Citra (3DS) in EmulationStation |
