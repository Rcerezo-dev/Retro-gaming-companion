# Retro Vault — Backlog

> Single source of truth for pending work. Updated every session.
> Last updated: 2026-06-27 (sección PONT añadida — reducción de código tras audit ponytail)
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

> **Día27 completado y archivado** (`Tareas/diario/archivo/Día27.md`): roadmap ARC
> cerrado (JM + CFG + SVC, PRs #22–#29). Plan de la sesión actual en
> `Tareas/diario/Día28.md` (UX Phase 4). Detalle del Día26 en
> `Tareas/diario/archivo/Día26.md`.

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
| PHASE1-3 | Generate `es_systems.cfg` from detected cores | ✅ `esde/systems_generator.py` (`generate_es_systems_xml`, formato moderno `custom_systems/es_systems.xml`) + `GET /api/generate-es-systems` + botón "Generar es_systems.xml" en Settings |
| PHASE1-4 | Auto-detect Android device via ADB on USB connect | ✅ `cable_sync_daemon.py` (commit 2a3c579) |
| PHASE1-5 | Folder picker with "Browse" button in Settings fields | ✅ `GET /api/browse-folder` (tkinter `askdirectory`, stdlib) + botón "Examinar" en `library_root` y `anbernic_root`; `browseFolder()` en `config.js`. Tests: `tests/web/test_browse_folder.py` |

### Phase 2 — DATs without effort

| ID | Task | Estado |
|----|------|--------|
| PHASE2-1 | Guided DAT download with contextual explanation | ✅ aviso contextual en paso ② Match del Overview + link directo a Settings → Catálogos DAT |
| PHASE2-2 | Clear UI for matching mode (with DAT vs by filename) | ✅ `tab-games.html` (commit ccb3a8e) |

### Phase 3 — Sync without config

| ID | Task | Estado |
|----|------|--------|
| PHASE3-1a | Research SFTP server options on Termux (dropbear vs openssh) | ✅ openssh recomendado (sftp-server integrado, puerto 8022); doc `docs/sync/sync-wifi-sftp.md` |
| PHASE3-1b | ~~Implement `sftp_transport.py`~~ — **descartado**: rclone ya soporta remotes `sftp` nativamente; el pipeline existente (`sync_saves` + `RcloneTransport`) reutiliza el remote sin código nuevo (regla stdlib-only). Ver `docs/sync/sync-wifi-sftp.md` | ❌ superseded |
| PHASE3-1c | ~~UI: WiFi sync toggle~~ → replanteado: mejoras UX del sync cloud existente (decisión: SFTP directo exige ambos dispositivos encendidos a la vez; el usuario prefiere async vía Dropbox/GDrive, que ya existe) — instrucciones Google Drive guiadas + botón "Usar para saves+states" (escribe `sync.saves_remote`/`states_remote` en un clic) + línea de estado con el remote activo. `tab-sync.html` + `sync.js`, sin cambios de backend | ✅ |
| PHASE3-2 | Auto-sync on connect — detect via ADB, prompt "Sync now?" | ✅ (commit 2a3c579) |
| PHASE3-3 | Sync status always visible in header | ✅ (commit 7eba736) |

### Phase 4 — Non-technical UX

| ID | Task | Estado |
|----|------|--------|
| PHASE4-1 | Human-readable errors — `_readable_error()` central en `server.py` mapea excepciones a mensaje legible + log de traceback; router simplificado | ✅ (rama `feature/phase4-1-readable-errors`) |
| PHASE4-2 | Contextual help — componente `.help-icon` (tooltip CSS-only) + hints en Overview/Settings | ✅ (rama `feature/phase4-2-contextual-help`) |
| PHASE4-3 | Responsive UI — breakpoint `≤480px` (sidebar icon-rail, grid 1 col, touch 44px) | ✅ (rama `feature/phase4-3-responsive`) |
| PHASE4-4 | Windows toast notifications en sync complete / inbox detected — `utils/notifier.py` (PowerShell `Windows.UI.Notifications`, stdlib-only, no-op off-Windows). Enganchado a sync (cloud+cable), CLI, health check e **inbox detectado** (`daemons.py`); gate `config.notify_desktop`. Tests: `tests/test_notifier.py` (escape + degradación) | ✅ (rama `feature/phase4-4-windows-toasts`) |
| PHASE4-5 | Renombrar jargon (conservador término + glosa): Match→Identificar, SHA1→Huella (SHA1), DAT→base de datos de juegos | ✅ (rama `feature/phase4-5-rename-jargon`) |

### Phase 5 — Auth

| ID | Task | Estado |
|----|------|--------|
| PHASE5-1 | Forzar PIN cuando `host != 127.0.0.1` (no solo advertir) | ✅ `serve()` lanza `InsecureExposureError` y aborta el arranque si se expone a la red sin PIN; escape hatch `--allow-insecure` (degrada al aviso). Tests: `tests/web/test_force_pin.py` |

### Phase 6 — Distribution

| ID | Task | Estado |
|----|------|--------|
| PHASE6-1a | Crear `RetroVault.spec` — PyInstaller con static assets, templates y `tools/` bundled | ✅ `RetroVault.spec` empaqueta `web/static` (incluye partials HTML), `tools/` (adb, dlls, chdman) e hiddenimports de subpaquetes (build no verificado aún → ver 6-1b) |
| PHASE6-1b | Probar ejecutable en máquina limpia (sin Python) | 🟡 Validado en este equipo (build, smoke test de `serve`, instalación/desinstalación silenciosa); falta una prueba en una máquina realmente sin Python instalado. Corregidos hiddenimports obsoletos de `RetroVault.spec` (`response_builders`→`builders/`, `cable_sync_daemon` movido a `web/`) y las DLLs de ADB ahora son opcionales (adb.exe moderno no las necesita) |
| PHASE6-2a | Escribir script Inno Setup — shortcut + Add/Remove Programs | ✅ `installer/RetroVault.iss` — instalador por usuario (`PrivilegesRequired=lowest`), shortcuts en menú + escritorio, desinstalador limpio. Compilado y probado con Inno Setup 6.7.3 → `RetroVault-Setup.exe` (~15 MB) |
| PHASE6-2b | Bundlear DATs mínimos en el installer | ⬜ |
| PHASE6-3a | Endpoint `/api/version` + check de actualizaciones al arrancar | ✅ `update_checker.py` + `GET /api/version` + banner en UI. 13 tests. PR #52. |
| PHASE6-3b | Descarga y aplicación de update desde GitHub Releases | ✅ `utils/update_installer.py` (`find_update_asset`, `download_update` con progreso, `launch_installer`); `web/handlers/update.py` (`/api/update/{status,download,apply}`); banner con botones "Descargar e instalar" / "Instalar y reiniciar" en `main.js`. Solo aplica a builds frozen (PyInstaller); en modo fuente solo enlaza al release. Aún sin probar contra un release real (ningún release publicado todavía — depende de 6-1b/6-2a). 30 tests nuevos. |
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
| EMULATOR-COMPAT-1 | Create compatibility matrix — PC emulator, Android emulator, save format, save path per platform | `docs/emulator-compat.md` ✅ |
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
| ARC-SVC-1c | | ↳ `services/ra_duplicates_service.py`: `apply_ra_conflicts`, `discard_ra_duplicate`, `discard_all_ra_duplicates`, `discard_no_support`, `resolve_duplicate_ra` (puras). Helper `_discard_file` unifica las 4 variantes de descarte a `_descartados/` y **corrige el commit ausente** de discard-no-support (fila no se borraba). Handler queda como router fino (~145 líneas, era 550). Tests: `tests/test_ra_duplicates_service.py` + `test_apply_ra_conflicts.py` migrado al service | `services/`, `web/handlers/duplicates.py` | ✅ |

---

## REPORT-FIX — Precisión del audit de biblioteca + acciones (detectados 2026-06-19)

Origen: revisión del informe `.rommgr/last_report.json` sobre `F:\Juegos Retro`.
El audit mezcla problemas reales con **falsos positivos de su propia lógica**.

### A — Falsos positivos del audit (bugs a corregir)

| ID | Severidad | Task | Archivo | Estado |
|----|-----------|------|---------|--------|
| RPT-A1 | 🟡 Medio | **`.bin`+`.cue` marcado como "extensiones mezcladas"** — `verify_disc_groups` marca `mixed_ext` ante cualquier grupo con >1 extensión, pero un set PSX es `.bin`+`.cue` por diseño (11 falsos positivos). Tratar `.cue`/`.m3u`/`.ccd`/`.sbi` como *sidecars*; solo marcar `mixed_ext` con 2+ extensiones de **imagen** (`.bin`/`.iso`/`.img`/`.chd`). Tests. | `utils/multidisc_verifier.py:57-67` | ✅ `_SIDECAR_EXTS` + `image_exts` filter; tests en `test_multidisc_verifier.py` |
| RPT-A2 | 🟡 Medio | **Orphan-finder recorre `BIOS\`, `System Volume Information\` y carpetas de datos de emulador** — `rglob("*")` sin exclusión de directorios; viola la regla "BIOS nunca se trata como ROM". Excluir dirs (BIOS, `System Volume Information`, ES-DE/assets, ocultos, `_descartados`). Quita ~12 de 35. Tests. | `utils/orphan_finder.py:27` | ✅ `_iter_files()` con `_EXCLUDED_DIR_NAMES` + skip de dirs ocultos; tests en `test_orphan_finder.py` |
| RPT-A3 | ⚪ Bajo | **Ficheros de datos de emulador (`.dat`, `.fs`) contados como "saves"** — p.ej. `scummvm\theme\*.dat`, `fbneo\*.fs`. Estrechar el set de extensiones de save del orphan-finder a saves reales (`.srm`/`.sav`/`.nv`/`.hi`/`.state`…), excluir `.dat`/`.fs`. Deja solo NVRAM arcade real. | `utils/orphan_finder.py` | ✅ `.dat` y `.fs` eliminados de `save_extensions` en `config.py`; tests en `test_orphan_finder.py` |

### B — Problemas reales de biblioteca (añadir acción de arreglo in-app)

| ID | Severidad | Task | Archivo | Estado |
|----|-----------|------|---------|--------|
| RPT-B1 | 🟡 Medio | **11 juegos multidisco sin `.m3u`** (Driver 2, Grandia, Koudelka [8 discos], Parasite Eve I/II, Oddworld…) — RetroArch necesita `.m3u` para cambiar de disco. Exponer acción "Generar .m3u (N)" desde el informe / tab Formatos (el generador ya existe en `m3u_generator`). | `web/handlers/esde/conversions.py`, partial del informe | ✅ `missing_m3u` issue type en `verify_multidisc`; botón "Generar .m3u (N)" en resultado de verificación; `generateM3uFromVerify()` en `tools.js`. 3 tests nuevos. |
| RPT-B2 | ⚪ Bajo | **"Discos faltantes" + "sin match en catálogo"** (gap ×11, unmatched ×4) — separar en el informe "set incompleto → adquirir" de "sin DAT → cargar DAT e Identificar"; enlazar el segundo al flujo de catálogos. Reverificar gap tras RPT-A1 (el doble conteo `.bin`/`.cue` interfiere). | `utils/multidisc_verifier.py`, partial del informe | ✅ Gap check filtra sidecars (fix falso positivo); UI separa gaps / otros / unmatched con acciones claras. 2 tests nuevos. |

### C — Auto-descarga de catálogos DAT faltantes (PHASE2 / RPT-B2)

> **Viable, stdlib-only.** Fuente: **`libretro/libretro-database`** en GitHub (espejo
> libre de No-Intro/Redump/MAME, mantenido — Redump PS1 confirmado en v2026.05.02 con
> sha1). `mame_loader.py` ya descarga DATs de libretro. No-Intro/Redump oficiales
> (DAT-o-MATIC) requieren descarga manual (CAPTCHA) → por eso PHASE2-1 fue "guiada";
> libretro-database elimina ese bloqueo.
>
> ⚠️ **Caveat de formato:** los DATs de `metadat/redump|no-intro` están en **texto
> clrmamepro** (`game ( name "..." rom ( ... ) )`), **no Logiqx XML**. `catalog_loader.py`
> solo hace `ET.parse()` (XML) → hay que **añadir un parser clrmamepro** (o un sniffer de
> formato) antes de poder ingerir lo descargado. ~30-40 líneas, sin deps.

| ID | Severidad | Task | Archivo | Estado |
|----|-----------|------|---------|--------|
| DAT-DL-0 | 🟡 Medio | **Parser clrmamepro** — `load_clrmamepro_dat(path)` (tokeniza `game (...)`/`rom (...)`) + sniffer en `load_dat_directory` que elige XML vs clrmamepro por contenido. Tests con un DAT de muestra de cada formato. **Prerrequisito de toda la auto-descarga.** | `catalog/catalog_loader.py` | ✅ `load_clrmamepro_dat` + `_detect_dat_format` + `_top_level_text`; sniffer integrado en `load_dat_directory` y `load_dat_files_by_platform`. 10 tests nuevos. |
| DAT-DL-1 | 🟡 Medio | **Mapa plataforma → fichero DAT en libretro-database** — tabla `platform → metadat/{no-intro,redump}/<archivo>.dat` (raw.githubusercontent.com). Apoyarse en `platforms.toml`/detección existente. | `catalog/dat_downloader.py` (nuevo) | ✅ `_PLATFORM_DAT_MAP` 46 plataformas + `dat_url()` + `known_platforms()`. PR #49. |
| DAT-DL-2 | 🟡 Medio | **`download_dat(platform)` con `urllib`** — descarga a `.rommgr/catalogs/{nointro,redump}/`, valida que parsea (via DAT-DL-0), degradación con gracia si falla la red. | `catalog/dat_downloader.py` | ✅ `download_dat()` → `DatDownloadResult`; captura URLError + parse vacío. 17 tests. PR #49. |
| DAT-DL-3 | 🟡 Medio | **Endpoint + UI** — `POST /api/download-dat` (por plataforma o "todas las que faltan"); botón en Settings → Catálogos DAT y en el aviso "sin match" del informe (cierra el loop con RPT-B2). Job en background. | `web/handlers/`, partials | ✅ URL corregida a `/metadat/{no-intro\|redump}/`; validación via `_load_dat_file`; fix `sys.present→downloaded` en scan.js; fix template literal en tools.js; botón unmatched scroll a `#dat-catalog-list`. PR #50. |
| DAT-DL-4 | ⚪ Bajo | **Caché/edad de DATs** — no re-descargar si el DAT local es reciente (TTL configurable); mostrar fecha de última actualización por plataforma. | `catalog/dat_downloader.py` | ✅ TTL 7d, `_is_dat_fresh`, `_build_dat_catalog_list` con `mtime_iso`/`age_days`/`stale`; UI ambar para obsoletos; 12 tests. PR #51. |

> **Orden sugerido:** RPT-A1 → RPT-A2 → RPT-A3 (precisión del informe, backend + tests,
> bajo riesgo) → RPT-B1 (acción m3u) → DAT-DL-0 (parser clrmamepro, prerreq) →
> DAT-DL-1…3 (auto-descarga) → RPT-B2/DAT-DL-4.

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
| DESIGN-10 | Update device selector bar styling | ✅ | `#device-selector` usa `var(--bg-nav)`/`var(--border)`; override light redundante eliminado |
| DESIGN-11 | Add description bar below device selector | ✅ | `#tab-desc-bar` bajo el device selector; `_TAB_DESC` + `_updateTabDesc()` en `main.js`; CSS en `app.css` (PR #43) |
| DESIGN-12 | Convert remaining hardcoded colors to variables | ✅ paleta núcleo | 17 tokens semánticos `--c-*` (valores dark exactos + variantes light) mapean la paleta VS Code; 742 instancias inline en partials+JS migradas (dark idéntico por construcción). Cola de tints one-off (<5×) y reglas de `app.css` quedan como follow-up. **Requiere QA visual del tema light antes de merge** |
| DESIGN-13 | Test light theme with new fonts | ✅ | Verificado con Playwright: 71 backgrounds oscuros hardcodeados rompían el tema light (no cubiertos por el parche de DESIGN-12). Sustituidos por 4 clases `.rv-tint-{neutral,warn,ok,info}` (theme-aware) en `app.css` + ~50 inline styles migrados en 9 partials. Inter + Exo 2 legibles, sin scanlines. |
| DESIGN-14 | Performance audit | ✅ | Lucide `@latest` → `@1.21.0`; `preconnect` + `dns-prefetch` + `preload` para unpkg en `<head>`; Google Fonts ya era óptimo (PR #43) |

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

## PONT — Reducción de código (Ponytail Audit 2026-06-27)

Resultado del audit ponytail sobre los 125 archivos `.py`. Ordenadas por líneas eliminadas.
Una rama por tarea → PR a `develop`. Sin cambios de API pública. CI verde obligatorio.

| ID | Tarea | Archivo(s) | Impacto | Estado |
|----|-------|-----------|---------|--------|
| PONT-1 | `openapi_spec.py` → `static/openapi.json` estático; servidor lee con `Path.read_text()` | `web/openapi_spec.py` → `web/static/openapi.json` | -~580 líneas, -1 archivo Python | ✅ |
| PONT-2 | Hoisting de 117 late imports stdlib (`json`, `datetime`, `time`, `threading`, `pathlib`) en `web/handlers/*` y `web/daemons.py` — mover a nivel de módulo | handlers, daemons, cable_sync_daemon | -117 speed-bumps de lectura | ✅ |
| PONT-3 | `_RepositoryBase`: extraer `_open_conn()` que centraliza las 4 líneas PRAGMA duplicadas entre `connect()` y `batch()` | `database/repositories/base.py:29-51` | -4 líneas duplicadas | ✅ |
| PONT-4 | `apply_ra_conflicts`: inner `_discard()` duplica `_discard_file()` — eliminar inner function y llamar a `_discard_file(repository, str(path))` directamente | `services/ra_duplicates_service.py:247-257` | -15 líneas | ✅ |
| PONT-5 | N64 word-swap loop manual (7 líneas) → `array.array('I', chunk).byteswap().tobytes()` (stdlib `array`) | `converters/n64_converter.py:101-108` | -7 líneas, usa stdlib | ✅ |
| PONT-6 | `database/play_history.py` (un solo `record_play_session`) → `PlayHistoryMixin` en `database/repositories/`; ensamblar en `LibraryRepository` | `database/play_history.py`, `database/repositories/` | -1 archivo suelto | ✅ |
| PONT-7 | Renombrar `planner/conflict_resolver.py` → `planner/collision_resolver.py` para eliminar colisión de nombre con `sync/conflict_resolver.py` | `planner/conflict_resolver.py` | -0 líneas, +claridad | ✅ |
| PONT-8 | `filename_normalizer.py`: regex de limpieza de caracteres → `unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()` (stdlib `unicodedata`) | `detection/filename_normalizer.py` | reemplaza regex hand-rolled | ✅ |

> Orden sugerido: PONT-1 → PONT-3 → PONT-4 → PONT-5 → PONT-6 → PONT-7 → PONT-2 → PONT-8

---

## User actions (no code needed)

| ID | Task |
|----|------|
| STRUCT-4 | Configure RetroArch PC: Saving → Savefile Directory → `E:\Carpetas anbernic\saves\` |
| STRUCT-3 | Update `config.toml`: `local_dir = "E:\\Carpetas anbernic\\saves"` (after STRUCT-4) |
| ES-1 | Download `genesis_plus_gx` core in RetroArch → Online Updater |
| ES-2 | Configure Citra (3DS) in EmulationStation |
