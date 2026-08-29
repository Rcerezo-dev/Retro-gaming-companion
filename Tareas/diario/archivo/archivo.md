# Retro Vault — Archivo de Tareas Completadas

> Archivo de tareas terminadas. Movidas de `backlog.md` para optimizar tokens.
> Última actualización: 2026-08-29

---

## Phase 2 Frontend Migration — COMPLETADA ✅

Migración de code de `app.js` a módulos JavaScript separados. Completada 2026-04-02.

### 2a — State management ✅

| ID | Task | Status |
|----|------|--------|
| 2a-1 | Create state.js: imports, state object, basic exports | ✅ |
| 2a-2 | Migrate all game/TV/sidebar/settings state into state object | ✅ |
| 2a-3 | Wire into main.js: import state, export to window | ✅ |

### 2b — ES-DE tab ✅

| ID | Task | Status |
|----|------|--------|
| 2b-1 | Create esde.js scaffold | ✅ |
| 2b-2 | Migrate all ES-DE functions (8 handlers + socket code) | ✅ |
| 2b-3 | Wire into main.js | ✅ |

### 2c — Games tab ✅

| ID | Task | Status |
|----|------|--------|
| 2c-1 | Scaffold games.js: imports, state vars, column picker | ✅ |
| 2c-2 | Migrate filter helpers | ✅ |
| 2c-3 | Migrate core load/render | ✅ |
| 2c-4 | Migrate game panel | ✅ |
| 2c-5 | Migrate TV mode | ✅ |
| 2c-6 | Wire into main.js | ✅ |
| 2c-7 | Remove migrated code from app.js | ✅ |

### 2d — Overview tab ✅

| ID | Task | Status |
|----|------|--------|
| 2d-1 | Scaffold overview.js: imports + small helpers | ✅ |
| 2d-2 | Migrate heatmap + charts | ✅ |
| 2d-3 | Migrate overview load + platform grid | ✅ |
| 2d-4 | Migrate wizard | ✅ |
| 2d-5 | Wire into main.js | ✅ |
| 2d-6 | Remove migrated code from app.js | ✅ |

### 2e — ES-DE extended ✅

| ID | Task | Status |
|----|------|--------|
| 2e-1 | Scaffold esde.js + migrate 3 functions | ✅ |
| 2e-2 | Wire into main.js | ✅ |
| 2e-3 | Remove migrated code from app.js | ✅ |

### 2f — Tools tab ✅

| ID | Task | Status |
|----|------|--------|
| 2f | Create tools.js | ✅ |

### 2g — RA helpers ✅

| ID | Task | Status |
|----|------|--------|
| 2g | Extend esde.js with RA helpers | ✅ |

### 2h — Health checks ✅

| ID | Task | Status |
|----|------|--------|
| 2h | Extend esde.js with health checks | ✅ |

### 2i — Junk & orphans ✅

| ID | Task | Status |
|----|------|--------|
| 2i | Extend esde.js with junk, orphans, doctor | ✅ |

### 2j — Library report ✅

| ID | Task | Status |
|----|------|--------|
| 2j | Extend esde.js with library report | ✅ |

### 2k — Sync leftovers ✅

| ID | Task | Status |
|----|------|--------|
| 2k | Move sync functions to sync.js | ✅ |

### 2l — Global infra ✅

| ID | Task | Status |
|----|------|--------|
| 2l | Move global infra to main.js / state.js | ✅ |

### 2-final — Delete app.js ✅

| ID | Task | Status |
|----|------|--------|
| 2-final | Delete app.js | ✅ |

---

## Session — 2026-03-31 / 2026-04-02 ✅

### B-test — RA conflicts flow (subtasks completadas)

| ID | Task | Files |
|----|------|-------|
| B-test-1 ✅ | UI warning: confirmation dialog before RA Check | `static/js/tabs/duplicates.js::doResolveRaConflicts` |
| B-test-2 ✅ | Auto-rename winner after discarding loser | `handlers/duplicates.py::_apply_ra_conflicts` |
| B-test-3 ✅ | Better diagnostics: hint text, cache status, next_step field | `handlers/duplicates.py` |

| ID | Task | Status |
|----|------|--------|
| D2 ✅ | rclone handler: route files to `saves_remote` or `states_remote` by extension | Done: routing, diagnostics, edge cases |

### UX-1 & UX-2 — Device connectivity ✅

| ID | Task | File |
|----|------|------|
| UX-1/2-1 ✅ | Create `is_device_connected()` — checks ADB + SD card mount | `config.py` |
| UX-1/2-2 ✅ | Add `/api/device-status` endpoint | `web/handlers/config.py` |
| UX-1/2-3 ✅ | Frontend polling every 4s, update state | `static/js/state.js` + `main.js` |
| UX-1/2-4 ✅ | Startup cards: status badge when offline | `static/js/tabs/overview.js` + `index.html` |
| UX-1/2-5 ✅ | Disable rename button when offline + targeting Android | `static/js/tabs/organize.js` |

| ID | Task |
|----|------|
| UX-1 ✅ | Device connectivity indicator on startup cards |
| UX-2 ✅ | Block operations on inactive device |
| DB-1 ✅ | Metadata cache flag — `metadata_scraped` column, schema migration, scraper updates |
| DB-2 ✅ | Orphaned record cleanup — enhanced `prune_stale_entries()`, cleanup count in CLI |
| DUP-3 ✅ | Delete option for "Colisión de plan" — "Eliminar duplicados" button in conflict resolution |
| DUP-4 ✅ | Clarify delete-all counts — breakdown: deleted / skipped / failed |

### Bug fixes ✅

| ID | Bug | Fix |
|----|-----|-----|
| BUG-ASSET-IMAGE-404 ✅ | Game cover images 404 — missing `/api/asset-image` | Added endpoint to `collection.py` |
| BUG-ORG-1 ✅ | Organizar tab `window._h` error | Added `_h` to window exports |
| BUG-COL-1 ✅ | Coleccion tab `window._h` error | Added `_h` to window exports |
| BUG-DUP-FALSE ✅ | Duplicados shows false empty state | All cascading issues resolved |
| BUG-ORG-RA-RENAME-PLAN ✅ | "Resolver por RA" button error — RenamePlan missing `operations` | Changed `plan.operations` → `plan.pending` in `duplicates.py` |
| BUG-PLATBADGE ✅ | `window._platBadge is not a function` in Organizar | Exported from `games.js` + added to `main.js` |
| BUG-ORG-DELETE-COLLISION ✅ | "Eliminar duplicados" button broken DOM selector | Updated selector to find collision div correctly |
| BUG-DELETE-DUPLICATES-MISMATCH ✅ | Delete-all reports 550 deleted but files still exist | Fixed; Duplicados tab shows no duplicates after delete-all |

### Features ✅

| ID | Task |
|----|------|
| B2 ✅ | Batch run: checkboxes per tool, logical order, PC/Android context selector — `doBatchRun()` wired |
| B3 ✅ | Library comparator PC vs Android — diff screen + `POST /api/sync-roms` + conflict policy (B3-1…B3-5) |
| P1 ✅ | Inbox file watcher — polling 30s → auto-pipeline → toast with `trigger_ts` stamp |
| P3 ✅ | Disk usage panel per platform — `GET /api/disk-usage`, per-platform bars + drive bar |
| P5 ✅ | Collection completeness — cross with DATs, % per platform (📋 Completitud toggle panel) |

### Sync — Android emulator path mapping ✅

| ID | Task |
|----|------|
| SYNC-A1 ✅ | Documented save/savestate paths for all target emulators — `docs/sync/android-save-paths-RG556.md` |
| SYNC-A2 ✅ | `EMULATOR_SAVE_PATHS_DEFAULT` in `config.py` (18 emulators), `[[emulator_paths]]` overrides in `config.toml` |
| SYNC-A3 ✅ | `get_adb_sync_sources()` in `config.py`; `_run_auto_sync()` loops per-emulator sources instead of single root |
| SYNC-PS1PS2 ✅ | ADB access to PSX/PS2 hidden save paths — DuckStation + AetherSX2 paths verified and mapped |

---

## Session — 2026-04-09 ✅

### B3/0B — Comparador PC vs Android ✅

Completado. `/api/library-diff` + `/api/sync-roms` + UI con checkboxes, select-all y "Sincronizar todo →" por columna.

### Bug Fixes ✅

| ID | Bug | Fix |
|----|-----|-----|
| BUG-DUP-PERM ✅ | Duplicate deletion fails with WinError 5 (Access Denied) on `E:\Carpetas anbernic\gb\` | Added `_force_remove()` helper in `handlers/duplicates.py` — clears read-only attribute (`os.chmod(S_IWRITE)`) before retrying deletion |
| BUG-MISSING-ROUTES ✅ | Frontend calls 5 unregistered API routes — `DISPATCH-FAIL` logged on every page load | Added all 5 handlers: `auth/status`, `health-schedule`, `test-chdman`, `test-maxcso` → `handlers/config.py`; `disc-folders` → `handlers/esde.py` |
| BUG-ASSETS-1 ✅ | Assets tab shows "not found" | Root cause was BUG-MISSING-ROUTES polluting dispatch. `/api/assets` already existed; all routes verified 200 |
| BUG-ROUTING-404 ✅ | Router dispatch returns False for registered GET routes | Added 13 missing routes: `system-status`, `detect-cloud-folder`, `library-doctor`, `retroarch-check`, `bios-status`, `n64-scan` → `handlers/esde.py`; `autostart-status`, `autostart-toggle` → `handlers/config.py`. Total: 132 routes |
| BUG-INBOX-SIDEBAR ✅ | Sidebar renders at bottom in Inbox tab | Two stray `</div>` tags in `tab-collection` (index.html ~L1499) were prematurely closing `content-area` and `app-body`, breaking flex layout for all subsequent tabs |
| BUG-TOOLS-SIDEBAR ✅ | Sidebar hides in Tools subtabs | Same root cause as BUG-INBOX-SIDEBAR — resolved by the same fix |

### RENAME-CONFLICT — Name collision: prefer RA version ✅

| ID | Task | File |
|----|------|------|
| RENAME-CONFLICT-1 ✅ | Collision/disk conflict detection | `planner/operation_planner.py` (build_plan) |
| RENAME-CONFLICT-2 ✅ | RA resolution | `handlers/duplicates.py::_apply_ra_conflicts` (B-test-4 passing) |
| RENAME-CONFLICT-3 ✅ | Plan view preview with RA badges | `response_builders.py::_annotate_conflicts_with_ra` |
| RENAME-CONFLICT-4 ✅ | Frontend winner/loser labels | `static/js/tabs/organize.js` |

### RA-COPY-LINK — "Copy download link" per game ✅

Fixed underlying bug: `result.results` was missing from serialized job result (RA table always rendered empty). Added `"results"` key to `_job_results["ra_check"]` in `server.py`. Also fixed `achievements_count` → `achievements` field name mismatch.

| ID | Task | File |
|----|------|------|
| RA-COPY-LINK-1 ✅ | `ra_id` serialized inline in `results` array | `server.py` |
| RA-COPY-LINK-2 ✅ | 🔗 button per row copies RA game URL | `static/js/tabs/esde.js` |
| RA-COPY-LINK-3 ✅ | Toast via existing `_copyText()` utility | `static/js/tabs/esde.js` |

---

# Backlog archivado — poda ONB-8 (2026-07-04)

> Secciones 100% completadas movidas desde `Tareas/backlog.md` para dejar el backlog
> solo con trabajo pendiente. Contexto de cada sesión: `Tareas/diario/archivo/Día*.md`.

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
| ~~`feature/design-polish`~~ ✅ | DESIGN-10 + 11 + 12 (+13, +14, +15) | PRs #40 #43 #58 — tokenización completa |

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

### ANBERNIC-TV — TV-friendly UI for console browsing ✅ COMPLETADO

| ID | Task | Estado |
|----|------|--------|
| ANBERNIC-TV-1 | Diseño: 3 pasos — Status → Sync → Results, touch targets grandes | ✅ |
| ANBERNIC-TV-2 | CSS responsive — `.tv-step`, `.tv-btn`, media query 600px | ✅ `app.css` |
| ANBERNIC-TV-3 | Paso 1: connection OK + último sync desde `/api/auto-sync-status` | ✅ `sync.js:tvCheckStatus()` |
| ANBERNIC-TV-4 | Paso 2: trigger `/api/do-sync` + polling con barra animada | ✅ `sync.js:tvStartSync()` |
| ANBERNIC-TV-5 | Paso 3: resumen ↑ enviados / ↓ recibidos / errores + botón "Sync de nuevo" | ✅ `sync.js:tvShowResult()` |


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
| DESIGN-12 | Convert remaining hardcoded colors to variables | ✅ | 17 tokens semánticos `--c-*` mapean la paleta VS Code; 742 instancias inline migradas. |
| DESIGN-13 | Test light theme with new fonts | ✅ | 71 backgrounds oscuros → 4 clases `.rv-tint-{neutral,warn,ok,info}` (theme-aware). Inter + Exo 2 legibles. |
| DESIGN-14 | Performance audit | ✅ | Lucide `@latest` → `@1.21.0`; `preconnect` + `dns-prefetch` + `preload` (PR #43) |
| DESIGN-15 | Tokenización completa de colores inline (follow-up DESIGN-12/13) | ✅ | Día33: 8 nuevos tokens `--c-{strong,soft,muted,hint,dim,ghost}` + `--rv-tint-amber-*`; ~640 instancias hardcodeadas en 44 archivos JS/HTML migradas a variables. Solo quedan: colores de marca (wizard purple), blanco/negro sobre fondo coloreado, y heatmap de actividad. CI ruff corregido (7 archivos). PRs #58 + commits en develop. |

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

## UX — Fixes post-audit (2026-06-29)

| ID | Task | Archivo | Estado |
|----|------|---------|--------|
| UX-FIX-1 | Eliminar sección "Apariencia" duplicada en Settings (radio buttons vs botones) | `tab-settings.html` | ✅ |
| UX-FIX-2 | Tildes en Autostart (×5) + "④ Apply"→"④ Aplicar" + typo "Ambernic"→"Anbernic" | `tab-settings.html`, `tab-overview.html`, `tab-cable.html` | ✅ |
| UX-FIX-3 | Error de sync con enlace accionable a Settings → rclone | `sync.js` | ✅ |

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

## NEW-FEAT — Nuevas funciones (2026-06-30)

| ID | Task | Estado |
|----|------|--------|
| NEW-1 | **Gestor de patches (IPS/BPS/UPS)** — Inbox acepta `.ips`/`.bps`/`.ups`, los vincula al ROM base y aplica el patch. Nueva tabla `patches`; aplicador Python puro (stdlib). | ✅ IPS/IPS32/BPS (Día34) |
| NEW-2 | **Galería de screenshots** — endpoint `GET /api/screenshots` lista capturas de RetroArch (`screenshots/` de RetroArch); visor en panel de detalle del juego o en tab Colección. Requiere DB-FIX-4 (hecho). | ✅ Día34 |
| NEW-3 | **Game status tracker** — selector "Jugando / Completado / Abandonado / Pendiente" por juego en el panel de detalle. | ✅ `gp-status-sel` en `_foot.html`, `gpSetStatus()` en `games.js`, `POST /api/set-play-status` |
| NEW-4 | **Visor de save states** — extrae thumbnail PNG embebido en archivos `.state` de RetroArch (stdlib `struct`+`zlib`); grid "dónde lo dejé" por juego. | ✅ Día34 |
| NEW-5 | **Completitud de colección por plataforma** — `total_in_dat / owned`; widget en tab Overview. | ✅ `GET /api/collection-completeness` + barras en Overview (Día33) |
| NEW-6 | **Validador de BIOS** — tabla estática de hashes, escanea dir BIOS, panel en Herramientas. | ✅ `detection/bios_checker.py` + endpoint + UI en tab-settings.html (Día33) |
| NEW-7 | **Progreso de logros RA por juego** — barra progreso en panel detalle. | ✅ `GET /api/ra-user-progress` + `gp-ra-user-progress` en panel (Día33) |
| NEW-8 | **Backup de configs de core RetroArch** — sync de `.opt` vía `SyncSource(sync_all=True)`. | ✅ `SyncConfig.ra_config_dir/remote` + inyección en `sync_cloud.py` (Día33) |

---

## SYNC-SETUP — Wizard de conexión cloud sin setup manual (2026-06-30)

Objetivo: el usuario hace clic en "Conectar Dropbox", autoriza en el navegador, y el sync funciona. Sin terminal, sin `rclone config`, sin instalar nada. `rclone.exe` va bundleado en `tools/` igual que `adb.exe`.

| ID | Task | Archivo | Estado |
|----|------|---------|--------|
| SYNC-SETUP-1 | **Bundlear `rclone.exe` en `tools/`** — descargar el binario Windows de rclone y añadirlo a `tools/`; actualizar `RetroVault.spec` para incluirlo en el build; actualizar `config.py` default para apuntar a `tools/rclone.exe` si `rclone` no está en PATH | `tools/`, `RetroVault.spec`, `config.py` | ✅ Día37 (ver D37-1/2/3) |
| SYNC-SETUP-2 | **Backend wizard** — `cloud_auth.py` con 5 rutas: status/start/poll/finalize/disconnect; `rclone authorize <provider>` en thread; polling cada 2s | `web/handlers/cloud_auth.py` | ✅ Día34 |
| SYNC-SETUP-3 | **Frontend: panel "Conexión cloud"** — tarjetas Dropbox/Google Drive con badges Conectado/No configurado + botones Conectar/Desconectar + polling | `tab-sync.html`, `sync.js` | ✅ Día34 |
| SYNC-SETUP-4 | **Detectar remotes configurados** — `GET /api/cloud-auth/status` → `rclone listremotes` | `cloud_auth.py` | ✅ Día34 |

> **Orden:** SYNC-SETUP-1 → SYNC-SETUP-2 → SYNC-SETUP-4 → SYNC-SETUP-3

---

## DB-FIX — Limpieza de schema (audit 2026-06-30)

| ID | Task | Archivo | Estado |
|----|------|---------|--------|
| DB-FIX-1 | **Añadir `idx_games_md5`** | `database/schema.py` | ✅ Día33 |
| DB-FIX-2 | **`metadata_scraped` en CREATE TABLE** | `database/schema.py` | ✅ Día33 |
| DB-FIX-3 | **Columnas DEPRECATED muertas** — `games.status`, `games.library_path`, `assets.game_id` borradas del schema + `_drop_deprecated_columns()` migration (SQLite 3.35+) | `database/schema.py` | ✅ Día34 |
| DB-FIX-4 | **`saves.game_id FK → games.id`** — migration + `upsert_save(game_id=None)` con COALESCE | `database/schema.py`, `database/repositories/sync.py` | ✅ Día34 |

---

## DÍA35 — Features UX / Patches / Overview (2026-06-30)

| ID | Task | Rama | Estado |
|----|------|------|--------|
| D35-F | **Notas auto-save indicator** — debounce ya existía; añadir `…` / `✓ guardado` / `⚠ error` junto al label | `feature/notes-autosave` | ✅ Día35 |
| D35-B | **Historial de patches** — `GET /api/patch-log` desde `file_operations`; tabla ROM/mensaje/fecha en tab-tools | `feature/patch-log` | ✅ Día35 |
| D35-A | **Soporte UPS patches** — `patch/ups_applier.py` stdlib puro + 6 tests; `.ups` en handler + UI badge teal | `feature/patch-ups` | ✅ Día35 |
| D35-E | **Comparador PC vs Android en Sync** — panel reutiliza `doLibraryDiff()` y `/api/library-diff` ya existentes | `feature/library-diff` | ✅ Día35 |
| D35-D | **Heatmap actividad 52 semanas** — `GET /api/activity-heatmap` + grid 364 celdas 3 niveles teal en Overview | `feature/activity-heatmap` | ✅ Día35 |
| D35-C | **Búsqueda global sidebar** — `#global-search` en sidebar + debounce 300ms + Ctrl+K → filtra tab Juegos | `feature/global-search` | ✅ Día35 |

---

## Sesión archivada 2026-08-29

Movidas desde `backlog.md` por estar 100% completadas — reduce el backlog activo
de ~119k a bastante menos. Contenido íntegro sin reescribir.

### JUNK-SMART — Clasificador de basura basado en evidencia (diseño 2026-07-08)

Origen: Día39 demostró que la whitelist de extensiones de `_build_junk_scan`
(`web/builders/folders.py:37`) falla en las dos direcciones — falsos positivos
que exigieron 3 rondas de parches (JUNK-FIX-1/2/3: `.rvz`, `.sms`, `.sgm`,
`.nv`…) y falsos negativos (3.309 chips arcade con extensión gaming
`.bin`/`.rom` pasaron limpios y hubo que borrarlos con criterio manual:
≤8 MB + nombre de chip + cero `.cue` en el árbol). La app ya tiene el
conocimiento para decidir sola; hoy no lo usa.

**Fuentes de evidencia ya existentes (todas gratis, sin hashear de nuevo):**

1. **BD `games`** — `sha1` indexado (`database/schema.py:41,62`) para todo
   archivo con extensión gaming ya escaneado. Un archivo con match de catálogo
   (`canonical_title`/`catalog_source`) **nunca** es basura.
2. **Catálogos DAT** — tablas keyed por SHA1 (`database/schema.py:178,185`).
   SHA1 presente en No-Intro/Redump → ROM real, da igual la extensión.
3. **MAME XML** — `catalog/mame_loader.py:32` parsea `isbios`/`isdevice`/
   `runnable=no` y los **descarta**. Guardarlos en un set aparte identifica
   directamente la categoría 5 de JUNK-REVIEW-1 (`c1541.zip`,
   `kb_pcat101.zip`, `sb16.zip`… = infraestructura MAME, no juegos).
4. **`_KNOWN_BIOS_MAP`** (`web/inbox_pipeline.py`) — ZIPs BIOS con destino
   conocido → "mover a bios/", no borrar.
5. **Señales de contexto validadas en JUNK-CLEAN-1**: nombre de chip
   (`u082.bin`, `c1`, `ic12`…), tamaño ≤8 MB, ausencia de `.cue` hermano.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| JUNK-SMART-1 | **Tier de evidencia sobre la whitelist** — mantener la whitelist actual como filtro barato (tier 0: `.pdf`, `.exe`… siguen siendo basura obvia); añadir tier 1 para extensiones ambiguas (`.bin`, `.rom`, `.zip` fuera de carpeta de plataforma): join por ruta contra `games` → con match = skip; sin match + patrón de nombre de chip + sin `.cue` en el árbol → categoría nueva "Chips sueltos (sin match en catálogo)". `_build_junk_scan` recibe `repository` como parámetro (sigue siendo función pura, el handler se lo pasa). | `web/builders/folders.py`, `web/handlers/` (call-site) | ✅ rama `feature/junk-smart-1-evidence-tier` — el builder recibe `matched_paths` (set de rutas con `canonical_title` en BD, lo consulta el handler; con `None` el tier queda apagado → el setup pipeline, que borra lo devuelto, no cambia). Señales: sin match + stem de chip + sin `.cue` en la carpeta + ≤8 MB. Verificado contra biblioteca real: 93 chips `.rom` en `arcade\` detectados (antes invisibles), 0 falsos positivos. 3 tests nuevos (625 pass) |
| JUNK-SMART-2 | **Clasificar ZIPs sueltos por nombre de set MAME** — `load_mame_xml` devuelve además el set de nombres bios/device excluidos (o loader hermano); el junk-scan clasifica `.zip` de `Unknown\`: stem en catálogo arcade jugable → "ROM arcade sin organizar (no borrar)"; stem en set bios/device → "Infraestructura MAME"; stem en `_KNOWN_BIOS_MAP` → "BIOS (mover)"; patrón `Vendor - Plataforma.zip` o >1 GB → "Colección fuente (revisar)". Resuelve de raíz la categoría más grande del scan actual ("ZIPs no-ROM", 5.852 falsos en Día38). | `catalog/mame_loader.py`, `web/builders/folders.py` | ✅ rama `feature/junk-smart-2-mame-zip-classes` (apilada sobre JUNK-SMART-1) — loader nuevo `load_arcade_infra_names()` (los nombres que `load_mame_xml` descarta); el builder recibe `arcade_names`/`mame_infra_names`/`known_bios_files` (los construye el handler; con `None` no cambia nada). Verificado contra biblioteca real: los 1.305 "ZIPs no-ROM" se separan en 1.036 infraestructura MAME + 56 colecciones (27 GB) + 5 arcade + 208 genuinamente sin identificar. 5 tests nuevos (630 pass) |
| JUNK-SMART-3 | **Confianza por categoría en la UI** — cada categoría lleva etiqueta `safe_delete` / `review` / `misplaced` (esto es "no borrar, organizar/mover"); el botón de borrado masivo solo se habilita para `safe_delete`, el resto exige expandir y confirmar. Evita repetir el susto de INBOX-FIX-5. | `web/builders/folders.py`, `web/static/js/tabs/esde.js` | ✅ rama `feature/junk-smart-3-confidence-labels` (apilada sobre JUNK-SMART-2) — campo `confidence` en cada categoría (`_CATEGORY_CONFIDENCE`, default `safe_delete`); en la UI: badge por categoría, checkbox deshabilitado para `misplaced`, las `review` se habilitan solo al abrir "Ver archivos" (`junkRevealCat`), "Seleccionar todo" solo coge habilitadas y el confirm avisa si la selección incluye categorías `review`. 1 test nuevo (631 pass) |

> Orden: 1 → 2 → 3 (cada una es útil sola; 3 depende de que 1-2 emitan la etiqueta).

---

### TABS-FIX — Revisión UX/lógica pestañas Juegos/Organizar/Duplicados (2026-07-13)

Revisión pedida por el usuario: solapes entre Organizar y Duplicados, y "borra de la BD
pero no de la carpeta". Juegos está limpia (sin acciones destructivas ni solapes — solo
metadatos/tags/launch). El resto confirmado con archivo:línea. Orden: 1, 5 y 7 primero
(borrados engañosos y saves huérfanos al renombrar); 6 (pantalla única "Revisar copias")
absorbe 2 y 3 — si se hace 6, saltar 2/3; 4 es cosmético y puede ir dentro de 6.

**TABS-FIX-1/2/3/4/5/6/7 completos.** TABS-FIX-6 (rama
`feature/tabs-fix-6-revisar-copias`, sin mergear a `develop` todavía) — pantalla
"Revisar copias" en Organizar, pestaña Duplicados eliminada. Descubrió
**TABS-FIX-6-DISC** (bug preexistente del planner con sets multi-disco),
arreglado en la misma rama en una sesión posterior (ver detalle abajo).

| ID | Task | Pilar | Esfuerzo | Estado |
|----|------|-------|----------|--------|
| TABS-FIX-1 | **Borrado fantasma: si el archivo no existe localmente, se borra solo la fila de BD y se reporta éxito** — `delete_duplicate` (`services/duplicates_service.py:49-59`): `if p.exists()` → mueve a papelera; si no existe, borra la fila igualmente y devuelve `{"deleted": path}`. Mismo patrón en `_discard_file` (`ra_duplicates_service.py:45-51`, "file already gone → clean DB row") y `delete_all_duplicates` (`duplicates_service.py:114-127`, cuenta "skipped"). Las entradas Android escaneadas por ADB guardan rutas de consola (`/storage/...`, `handlers/scan.py:451`) que **nunca** existen como `Path` en Windows → todo "Eliminar" sobre ellas borra solo la BD, el archivo queda en la consola y el siguiente scan lo re-añade (mismo síntoma de reaparición que VAL-FIX-1). También aplica a rutas PC obsoletas. Fix: (a) entradas con ruta de dispositivo → borrar vía ADB (`tools/adb.exe shell rm` con confirmación) o deshabilitar el botón con tooltip "solo accesible con la consola conectada"; (b) ruta local inexistente → devolver aviso "el archivo ya no está en esa ruta; ejecuta un scan" en vez de éxito silencioso | Seguridad | M | ✅ (a) rama `fix/tabs-fix-1a` — `AdbTransport.remove()`/`file_exists()` (verifica que el archivo desaparece de verdad, el exit code de `rm` sobre `adb shell` no es fiable) + `resolve_single_device_transport()` (auto-detecta el único dispositivo conectado; `None` si hay 0 o >1, mismo mensaje explícito de antes). Threading de `adb_transport` opcional por los 3 sitios de (b) (PR #147) y sus 11 call-sites totales (incluye los 5 wrappers de `ra_duplicates_service.py` + `apply_ra_conflicts`), resuelto una vez por request en `web/handlers/duplicates.py`. De paso: `deleteDuplicate()` en el frontend no comprobaba `d.error` (el backend responde 200 incluso en error) — la fila desaparecía de la UI aunque no se hubiera borrado nada; `deleteAllDuplicates()` no mencionaba el contador `unreachable` en su toast. Verificado end-to-end contra la consola real conectada (RG556): archivo de prueba desechable push→delete_duplicate()→confirmado borrado en el dispositivo con `adb shell`, limpiado después. 15 tests nuevos (`test_adb_transport_remove.py` + ampliaciones en `test_duplicates_service.py`/`test_ra_duplicates_service.py`). (b) ya cerrado en PR #147 |
| TABS-FIX-2 | **"Quedarse con la versión con logros RA" existe 3 veces con 3 endpoints** — (1) Organizar → botón "Resolver con RA" (`tab-plan.html:38` → `doResolveRaConflicts`, `duplicates.js:277` → `/api/apply-ra-conflicts`); (2) Duplicados → sección "Duplicados por versión — sin logros RA" (`tab-duplicates.html:14-24` → `/api/ra-duplicates` + discard/discard-all); (3) Duplicados → duplicados semánticos con "Resolver: mantener éste" (`duplicates.js:140-166,424-462` → `/api/resolve-duplicate-ra`). (2) y (3) detectan lo mismo (mismo título normalizado, distinto hash, uno con RA) en la **misma pestaña** con dos UIs y dos endpoints. Fix: fusionar (2)+(3) en una sola lista "mismo juego, versiones distintas" con el criterio RA integrado (lógica canónica ya en `ra_duplicates_service.py`); (1) se queda en Organizar (resuelve conflictos del plan, contexto distinto) pero mover `doResolveRaConflicts` de `duplicates.js` a `organize.js` | UX | M | ✅ implementado de golpe por TABS-FIX-6 |
| TABS-FIX-3 | **Dos botones vecinos con criterio de conservación contradictorio en colisiones** — en el aviso de colisión de Organizar, "Eliminar duplicados" (`organize.js:364-425`, `deleteCollisionDuplicates`) conserva el índice 0 del DOM **arbitrariamente**, ignorando RA, mientras el botón "Resolver con RA" de al lado prioriza logros (preferencia registrada del usuario). Además borra en bucle llamando a `/api/duplicates/delete` por fila. Fix: eliminar el botón "Eliminar duplicados" (el flujo RA + "Descartar" por fila ya cubren el caso) o hacer que conserve por criterio RA | UX | S | ✅ implementado de golpe por TABS-FIX-6 — `deleteCollisionDuplicates()` eliminada de `organize.js` |
| TABS-FIX-4 | **Los textos de borrado mienten desde AUD-3** — "Se eliminarán N archivos del disco… Esta operación no se puede deshacer" (`duplicates.js:70,117,145`, `tab-duplicates.html:4,9,20`) cuando en realidad todo va a `_descartados/` (recuperable, purga a 30 días); solo el confirm de `deleteRaDuplicate` (`duplicates.js:255`) lo dice bien. Y el toast "Liberados: X" (`duplicates.js:89`) usa `freed_bytes` que no se libera hasta la purga (mover dentro del mismo volumen no libera nada). Fix: unificar todos los confirms/toasts a "se moverán a `_descartados/` (recuperable 30 días)" y renombrar "Liberados" a "Recuperables tras purga" | UX | S | ✅ alcance real menor de lo que parecía al verificarlo: `tools.js:174,194`, `esde.js:854`, `config.js:923` son borrados genuinamente permanentes (zips, papelera, limpieza post-CHD) y ya estaban bien redactados — el único texto engañoso era `duplicates.js:99` ("Liberados"), corregido a "Recuperables tras purga" en `review_copies.js` (la pestaña Duplicados entera desapareció con TABS-FIX-6) |
| TABS-FIX-5 | **"Eliminar todos los duplicados" ignora el filtro de plataforma** — el confirm cuenta los botones visibles en el DOM (`duplicates.js:65`) pero envía siempre `source_root: ''` (`duplicates.js:76`) → `delete_all_duplicates_multi` recorre TODOS los grupos de ambas BDs (`handlers/duplicates.py:87-93`). Con el filtro en "SNES" el usuario confirma "3 archivos" y se descartan los duplicados de todas las plataformas. Fix: pasar la plataforma filtrada al endpoint y filtrar en `delete_all_duplicates`, o contar server-side antes del confirm | Seguridad | S | ✅ duplicado de **DUPLICADOS-UX-1** (mismo bug, mismas líneas) — ya cerrado en PR #132 (`fix/duplicados-ux`, `023aafe`): `deleteAllDuplicates()` manda `platform` en el payload (`duplicates.js:74-86`), el handler lo reenvía (`handlers/duplicates.py:98-99`) y `delete_all_duplicates()` filtra los grupos por esa plataforma antes de borrar (`duplicates_service.py:140-142`). Entrada dejada como referencia histórica |
| TABS-FIX-6 | **Pantalla única "Revisar copias" (diseño 2026-07-13)** — fusionar en una sola vista los 4 solapes actuales (duplicados SHA1, duplicados semánticos, versiones RA, colisiones del plan): una cola de revisión agrupada **por juego**, cada grupo con sus copias listadas (badge del motivo: "idéntico SHA1" / "otra versión" / "colisión de nombre", badge 🏆 RA, badge dispositivo), una **recomendación precalculada** con criterio único (RA gana > mejor nombrada > primera; lógica ya en `ra_duplicates_service.py`) y acciones [Aplicar] [Elegir otra] [Copia intencional] + "Aplicar todas las recomendaciones (N)" arriba. Organizar pasa a 2 pasos: "Renombrar" y "Revisar copias"; la pestaña Duplicados desaparece. Backend: endpoint agregador que fusione `/api/duplicates` + `/api/ra-duplicates` + conflictos del plan; los endpoints de acción actuales sirven tal cual. **Implementa TABS-FIX-2 y TABS-FIX-3 de golpe** y resuelve de paso TABS-FIX-5 (el "aplicar todo" opera sobre los grupos renderizados). Diseño detallado: sesión 2026-07-13 | UX | L | ✅ rama `feature/tabs-fix-6-revisar-copias` — `_build_review_queue()`/`_review_groups_for_repo()` (`web/builders/duplicates.py`), Union-Find por repo (PC/Android nunca se mezclan): dos archivos son "el mismo juego" si comparten SHA1 **o** `(plataforma, canonical_title exacto)`. `excluded_duplicate_groups` (tabla nueva, mismo patrón que `excluded_duplicates`) para "copia intencional" por grupo. `apply_all_review_recommendations()` compone `resolve_duplicate_ra` (grupos sha1/title/ra) + `apply_ra_conflicts` (grupos disk/collision, sin tocar su lógica). Endpoints: `GET /api/review-queue`, `POST /api/review-queue/exclude`, `POST /api/review-queue/apply-all`. Frontend: `tabs/review_copies.js` (nuevo) montado como sección "2. Revisar copias" en `tab-plan.html`; `tab-duplicates.html` + nav eliminados; `duplicates.js` reducido al selector de contexto de Herramientas (lo único que seguía vivo). **2 bugs de severidad alta encontrados y corregidos probando contra la biblioteca real (no sintética) antes de dar la tarea por cerrada**: (1) agrupar por título *normalizado* (sin tags de región, como haría RA) fusionó 18 versiones regionales distintas de Final Fantasy VII en un solo grupo "duplicado" — se cambió a coincidencia **exacta** de `canonical_title` (mismo criterio que ya usaba `get_title_duplicate_groups()`); (2) la recomendación de un grupo con reason `disk`/`collision` usaba `conflict_role` en vez del `ra_supported` ya calculado, y `conflict_role` depende de que el archivo exista físicamente en disco — podía quedar `None` y la recomendación caía a orden alfabético. `_review_entry_sort_key()` simplificado a un único criterio uniforme. 22 tests nuevos (897 total). Ver también **TABS-FIX-6-DISC** abajo (hallazgo relacionado, no arreglado en esta rama) |
| TABS-FIX-7 | **El rename no renombra saves/states en carpetas centrales de RetroArch** — `rename_rom_with_saves` solo busca compañeros en `source.parent` (`renamer/file_renamer.py:49-53`); si RetroArch usa Savefile/Savestate Directory central (su default, y lo que pide STRUCT-4: `E:\Carpetas anbernic\saves\`), el save/state conserva el stem viejo → huérfano, RetroArch crea uno vacío = pérdida de progreso percibida (Pilar 3). La app ya conoce esas rutas (`_state_search_dirs`, `handlers/games.py:22-35`, busca en `retroarch_path/states` para miniaturas) pero el renamer no. Extras: `.state.auto` nunca casa (suffix parseado `.auto`, stem `X.state`) y solo hay `.state1`/`.state2` en la lista (`config.py:529-530`) — slots 3+ huérfanos. Fix: en `rename_rom_with_saves`, buscar compañeros también en las carpetas centrales de config (saves/states de RetroArch + `local_dir` del sync), y matching por prefijo de stem para cubrir `.state.auto`/`.stateN` | Sync/Seguridad | M | ✅ |
| DUP-RA-COLLISION-1 | **`apply_ra_conflicts` seguía pudiendo descartar discos reales de un set multi-disco** — residual de TABS-FIX-6-DISC: su fix preserva el tag `(Disc N)` cuando está presente en `original_filename`, pero si ni el DAT ni el nombre de origen lo traen (fuente desordenada, sin ese tag reconocible), los discos siguen colisionando en el mismo `target_path` y "Resolver con RA" se queda con el de más logros, descartando los demás a `_descartados/` como si fueran copias alternativas — pérdida de datos real, aunque hoy no se dispara porque ningún disco de la biblioteca tiene RA. Hallado documentando PR #213, sin implementar en ese momento | `services/ra_duplicates_service.py:apply_ra_conflicts` | ✅ dos capas: (1) **detección ampliada** — `utils/disc_tag.py` nuevo (`find_disc_tag`/`has_disc_tag`, usado por `operation_planner._canonical_filename` y `duplicates._is_disc_set`, sustituye los 3 regex `\(disc\s*\d+\)` duplicados en el código) reconoce también "Disc1", "cd2", "Disco 2" sin paréntesis — la mayoría de los casos reales ya ni llegan a colisionar; (2) **red de seguridad** — para lo que aun así colisione (nombre totalmente opaco, sin ningún tag reconocible), ambas ramas de `apply_ra_conflicts` (`disk` y `collision`) saltan la resolución automática por RA cuando `game.platform` está en `_DISC_SUBFOLDER_PLATFORMS` (psx/saturn/ps2/dreamcast/gamecube/wii) — nunca se descarta nada, se cuenta en `skipped_multi_disc` y queda para revisión manual (mismo principio "ante duda, no se toca" que INBOX-FIX-5/ARCADE-RECON-4). Toast de `review_copies.js` avisa del conteo. Tests nuevos: `test_disc_tag.py`, `test_multidisc_set_messy_tags_do_not_collide`, `test_collision_on_disc_platform_is_never_auto_resolved` |
| TABS-FIX-6-DISC | **El planner de renombrado colisiona discos de un mismo set multi-disco** — `_canonical_filename` (`planner/operation_planner.py:70-90`) usa `game.canonical_title` tal cual para el nombre destino; en DATs No-Intro/Redump el `canonical_title` de un set multi-disco (PSX típicamente) es idéntico para todos los discos (`"Final Fantasy VII (Europe)"`, sin `(Disc N)`) — sus 3 archivos calculan el mismo `target_path`, y `collision_resolver.resolve()` los marca "collision" (`operation_planner.py:150`). Hoy eso ya se resuelve con "Resolver con RA" (`apply_ra_conflicts`, `services/ra_duplicates_service.py:268`), que se queda con el disco de mayor logros RA y **descarta los demás a `_descartados/`** — para un set multi-disco eso significa borrar Disc 2/3 pensando que son "copias alternativas". Descubierto probando TABS-FIX-6 contra la biblioteca real (`Final Fantasy VII (Disc 1/2/3).cue`, 3 entradas). No es un bug nuevo de TABS-FIX-6 (el mecanismo de resolución ya existía vía el botón "Resolver con RA" de Organizar) — TABS-FIX-6 solo lo hace más visible al mostrarlo en la cola unificada. Mitigado parcialmente: la detección de "otra versión" (`title`) de TABS-FIX-6 ya excluye sets multi-disco genuinos vía tag `(Disc N)` en el nombre (`_is_disc_set()`, `web/builders/duplicates.py`) — pero el conflicto de **plan** (`disk`/`collision`) sigue sin distinguirlos. Fix real: que `_canonical_filename` conserve el tag `(Disc N)` del `original_filename` cuando el DAT no lo incluya en `canonical_title`, o que `collision_resolver`/`apply_ra_conflicts` detecten sets multi-disco (mismo patrón `_is_disc_set`) y los excluyan de la resolución automática | Seguridad | M | ✅ implementada la primera opción del fix real: `_canonical_filename()` (`operation_planner.py`) ahora preserva el tag `(Disc N)` del `original_filename` cuando `canonical_title` no lo trae, con un parámetro `include_disc_tag=False` para derivar la carpeta compartida del juego (que debe seguir siendo disc-agnostic). Efecto: cada disco calcula un `target_path` distinto → `collision_resolver` ya no los marca "collision" en absoluto, así que `apply_ra_conflicts` nunca los ve como grupo a resolver — **fix en la raíz, sin tocar `collision_resolver.py` ni `ra_duplicates_service.py`**. Test nuevo en `test_operation_planner.py` reproduce el caso real (3 discos, mismo `canonical_title`, sin tag): 0 conflictos, 3 pendientes con nombre de archivo distinto y misma carpeta |

---

### DEVSEL-FIX — Selector de dispositivo (auditoría 2026-07-12)

El selector global PC / Sistema completo / Consola (`_nav.html:69-71`, `setDevice()` en
`main.js:412`, `_deviceRoot()` en `main.js:428`) filtra por `source_root`; el backend elige
BD con `_repo_for_path()` (`builders/common.py:141`): **path vacío → BD del PC**. De ahí
salen todos los fallos. Orden: 1→2 son pérdida de datos potencial, prioridad absoluta.

| ID | Task | Pilar | Esfuerzo | Estado |
|----|------|-------|----------|--------|
| DEVSEL-FIX-1 | **Acciones de duplicados ignoran el dispositivo** — la vista sí lee ambas BDs (`_build_duplicates_two_repos`, `handlers/duplicates.py:50`) pero TODAS las acciones usan `repository` (PC) fijo: `/api/duplicates/delete` (`duplicates.py:70` → `delete_duplicate` borra el archivo por path pero `delete_game(game_id)` contra la BD PC con un id de la BD Android, `services/duplicates_service.py:65`); `/api/duplicates/delete-all` (`duplicates.py:80`) — **en modo consola la UI muestra y confirma duplicados Android pero el backend borra los del PC** (`delete_all_duplicates` recorre `repository.get_duplicate_groups()`); `/api/duplicates/exclude` y los 6 endpoints RA-duplicates, ídem. Fix: enrutar por `get_repo_fn(source_path)` en delete, y pasar `source_root` a delete-all/exclude | Seguridad | M | ✅ PR #118 mergeada — `register()` recibe `get_repo_fn`; delete enruta por `source_path`, delete-all/exclude por `source_root` del body (vacío → ambas BDs: `delete_all_duplicates_multi()`, exclude en ambas con INSERT OR IGNORE); RA discard/resolve enrutan por path. Tras FIX-3 el frontend envía siempre `source_root: ''` (la vista muestra ambos dispositivos). 6 tests handler con 2 repos reales |
| DEVSEL-FIX-2 | **Favoritos/tags/notas/metadatos escriben siempre en la BD del PC** — `/api/toggle-favorite` (`handlers/games.py:502`), `/api/tag` (`games.py:516-519`), `/api/set-metadata` (`games.py:482-491`) usan `repository` fijo; en modo consola el `game_id` viene de la BD Android → escriben en el juego equivocado del PC o en ninguno. El frontend ni envía `source_path` (`games.js:160,686,715,725,784,818`). `/api/set-play-status` sí enruta bien (`games.py:468`) pero el panel de juego llama con `source_path: ''` (`games.js:659`) → siempre PC. Fix: enviar `source_path` desde el frontend y usar `get_repo_fn()` en los 3 handlers | Biblioteca | S-M | ✅ PR #119 mergeada — los 3 handlers enrutan con `get_repo_fn(data["source_path"])`; el panel de juego envía `_gpSrc()` en favorite/tag/notes/metadata/play-status, y la estrella de la lista lleva `data-path`. 4 tests con 2 repos y mismo game_id en ambas BDs |
| DEVSEL-FIX-3 | **"Sistema completo" = solo PC en la práctica** — `_deviceRoot()` devuelve `null` en modo `both` → sin `source_root` → `get_repo_fn("")` → BD PC. Afecta a `/api/plan` y `/api/apply` (`handlers/organize.py:35,107` — la barra dice "Viendo: Sistema completo (PC + consola)", `organize.js:68`, pero solo planifica/renombra el PC), `/api/games` (`games.py:121`), platform-stats/assets/export/disk-usage (`collection.py:35,64,126,159,181,348`), unmatched/completeness (`games.py:640,701`). Única vista correcta: duplicados. **Decisión (2026-07-13): eliminar el modo** — el usuario solo lo usa para duplicados, y esa vista ya cruza ambas BDs por sí sola (`_build_duplicates_two_repos`). Quitar "Sistema completo" del selector (`_nav.html:69-71`, `setDevice()`/`_deviceRoot()` en `main.js:412,428`) y verificar que duplicados no depende del modo `both`. Si algún día se quiere visión global fusionada, se reabre como feature | Biblioteca | S | ✅ PR #120 mergeada — botón eliminado, `setDevice`/estado solo `pc\|anbernic`, duplicados cruza siempre ambas BDs; delete-all/exclude envían `source_root: ''` (ambas BDs), integración con FIX-1 aplicada en el merge |
| DEVSEL-FIX-4 | **Botón "Consola" habilitado por ruta, no por detección** — `dev-anbernic` se habilita si hay `abPath` configurada (`overview.js:424-425`, `config.js:709`) aunque la consola no esté conectada; `deviceConnected` (polling `/api/device-status`, `state.js:52`) solo gatea el badge del Overview, el botón Apply (`organize.js:27-46`) y `doApply` (`organize.js:455`) — `applyKeepBoth` (`organize.js:309`) no comprueba nada. Fix pedido: deshabilitar "Consola" cuando `!deviceConnected`, con tooltip del motivo; decidir si se permite modo solo-lectura de la BD Android offline. (El modo "Sistema completo"/`dev-both` ya no existe — eliminado en FIX-3). **Hecho (2026-07-13)**: gating centralizado en `state.js::updateDeviceButton()` (ruta configurada Y `deviceConnected`, tooltip con el motivo); Overview/Settings marcan `data-has-path`, el polling refresca. Decisión: sin modo solo-lectura offline explícito — si la consola se desconecta estando seleccionada, la vista actual se mantiene pero el botón queda deshabilitado | UX | S | ✅ |

---

---

### ARCADE-RECON — Reconstruir sets MAME sueltos por cobertura CRC (diseño 2026-08-13)

Origen: INBOX-CFG-2. 3.526 archivos sueltos en la raíz del Inbox (`01.u12`,
`02.u11`, `.epr`, `.047`, extensiones numéricas sin estandarizar) — chips
individuales de sets MAME/arcade descomprimidos, **sin carpeta que agrupe qué
chips pertenecen a qué máquina**. `classify_path` los ignora (`unknown`,
ninguna extensión de ningún catálogo de consola). El ZIP-ROUTE existente
(`web/zip_router.py`) asume que un set arcade siempre llega como ZIP intacto
— "el ZIP es el ROM", nunca se extrae — así que no hay ruta de código para
reconstituir chips ya sueltos.

**Prueba de viabilidad** (script `feasibility_mame.py`, contra el Inbox real):
de 2.000 archivos sueltos, **1.964 (98 %)** tienen un CRC32 que matchea al
menos un nombre de máquina en `MAME 0.286 (arcade).dat` vía
`load_arcade_crc_index()` — el mismo índice que ya usa ZIP-ROUTE-2 para
identificar ZIPs de arcade renombrados. Cada CRC puede votar a varias
máquinas (ROM compartido entre parent/clones — p. ej. `asteroid`/`asteroid2`/
`aerolitol` comparten el mismo chip): la identidad de un archivo aislado es
ambigua, pero la del **conjunto** no lo es — solo una máquina tendrá el 100 %
de sus roms esperados presentes entre los sueltos.

| ID | Task | Notas |
|----|------|-------|
| ARCADE-RECON-1 | **`load_arcade_manifest()`** — nueva función en `catalog/mame_loader.py`, hermana de `load_arcade_crc_index()` (mismo `iterparse` de los `.dat`, sin segundo parseo del archivo de 75 MB): `machine_name → [(rom_name, crc, size), …]`. Necesaria para calcular cobertura por máquina, no solo pertenencia por CRC | Reutiliza el bucle existente — ampliarlo para devolver también el manifest en la misma pasada, en vez de una función independiente que vuelva a `iterparse` |
| ARCADE-RECON-2 | **Identificación por cobertura** — nuevo paso en `web/inbox_pipeline.py` (mismo hueco que `_intercept_bios_files`/`_resolve_ambiguous_md`, Step 1.x): candidatos = archivos sueltos en la raíz del Inbox con `classify_path` = `UNKNOWN`; CRC32 de cada uno (misma rutina que `_resolve_ambiguous_md`); por cada máquina votada por ≥1 archivo, `coverage = roms_presentes / roms_totales_de_la_máquina`; **solo se reclama al 100 %** (mismo umbral que ZIP-ROUTE-2 ya usa para "identificado, mover directo" vs. "revisar a mano"). Procesar las máquinas 100 %-cubiertas de mayor a menor nº de roms primero — un set grande completo consume sus chips antes de que un subconjunto compartido se lo dispute una máquina más pequeña; un archivo consumido sale del pool | Sin heurística de nombre — igual que el resto de ZIP-ROUTE, el contenido manda |
| ARCADE-RECON-3 | **Empaquetar y entregar al pipeline arcade existente** — por cada máquina reclamada: escribir `<machine>.zip` en `inbox/_arcade_staging/`, verificar que el ZIP contiene exactamente los miembros esperados, y moverlo directo a `target_root/arcade/` reutilizando el mismo paso que `zip_router._route_identified()` ya usa para ZIPs arcade identificados — **nunca por el Inbox normal** (un set arcade extraído está roto). Solo tras confirmar el ZIP final en su destino, los sueltos originales van a `_descartados/` (AUD-3, nunca borrado directo) | `web/inbox_pipeline.py`, reutiliza `web/zip_router.py` |
| ARCADE-RECON-4 | **Restos sin reclamar quedan intactos** — cobertura <100 % (chips faltantes, set incompleto) se deja sin tocar en el Inbox, logueado para revisión manual — mismo principio "ante duda, no se toca" que el resto del pipeline (INBOX-FIX-5, RA-CONFLICT-1) | — |

> Estado: ✅ implementado (rama pendiente de nombrar — trabajo hecho directo
> sobre `develop` en esta sesión) y **ejecutado de verdad 2026-08-13** contra
> el Inbox real (3.526 sueltos): `load_arcade_manifest()` en `catalog/mame_loader.py`
> (932 tests pass, incl. `tests/test_arcade_recon.py` y 2 nuevos en
> `tests/test_mame_loader.py`); paso nuevo `_reconstruct_loose_arcade_sets()`
> en `web/inbox_pipeline.py` (Step 1.8, antes del scan). Prueba controlada
> primero en sandbox (copia, Inbox real intacto) → **15 sets, 106 chips**
> reconstruidos correctamente (`polepos2` 44 chips, `tekken3je1`/`tekkenac`
> 13+12, `mwalkbl2` 23, `seawolf` 4, y 10 más de 1 chip). Confirmado el mismo
> resultado tras ejecutar de verdad (watcher `auto_process`, reinicio del
> servidor): **15/15 ZIPs verificados en `E:\Carpetas anbernic\arcade\`**,
> quedan **3.431 sueltos** sin reclamar (sets incompletos — se dejan
> intactos, ante duda no se toca). UI: contador "Sets arcade reconstruidos"
> añadido a `web/static/js/tabs/inbox.js`.

---

### INBOX-UX — Auditoría de la pestaña Inbox: UX/UI (2026-07-13)

Auditoría de la pestaña Inbox (`tab-inbox.html` + `js/tabs/inbox.js`,
Pilar 2). Cierra el hilo abierto en
`Tareas/diario/archivo/Roadmap-Plan-UX-completado.md`: **no se
fusiona con Plan** — el pipeline de Inbox incluye pasos que Plan no tiene
(extraer, escanear, cotejar) precisamente porque parte de archivos aún no
escaneados; son dos pilares distintos, no una duplicación. Hallazgo
principal propio: "Organizar todo" es la única acción masiva de todo el
proyecto auditado hasta ahora sin ningún paso de confirmación. Detalle,
archivo:línea y fases en `Tareas/diario/archivo/Roadmap-Inbox-UX-completado.md`.
**Completado** — ver INBOX-UX-1..6 arriba.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| INBOX-UX-1 | **"Organizar todo" sin ninguna confirmación** — `runInbox()` (`inbox.js:160-186`) lanza extraer+escanear+cotejar+renombrar+organizar sobre toda la carpeta Inbox sin `confirm()`/`_showConfirm`, a diferencia de toda acción masiva equivalente ya auditada (Duplicados, Plan, Formatos) | Bug | S | ✅ `inbox.js:198,202-204` — `_showConfirm('¿Organizar el Inbox?', ...)` antes de lanzar `_launchInbox` |
| INBOX-UX-2 | **"Analizar carpeta" no muestra un plan real, solo clasificación** — sin nombres de destino ni conflictos previstos, a diferencia de la tabla equivalente en Plan; conviene resolver junto con INBOX-UX-1 (la confirmación necesita estos datos) | UX | M | ✅ `inbox.js:147-153` (`scanInbox()`) — muestra destino previsto (`dest_folder`) y marca conflictos (`dest_exists`) |
| INBOX-UX-3 | **`confirm()` nativo en `resolveInboxConflict`** (`inbox.js:321-336`) — mismo patrón ya señalado en Duplicados y Plan | UX | XS | ✅ `inbox.js:364-367` — usa `_showConfirm` |
| INBOX-UX-4 | **Checkbox "Procesar automáticamente" sin relación visible con "Guardar ajustes"** — toggle silencioso que no hace nada hasta pulsar un botón en otra fila (`tab-inbox.html:31-34,40`) | UX | XS | ✅ `tab-inbox.html:28,32` — `onchange="autoSaveInboxToggle()"` guarda automáticamente (`inbox.js:402-403`) |
| INBOX-UX-5 | **"No reconocidos" sin explicar qué pasará con esos archivos** (`inbox.js:128`) | UX | XS | ✅ `inbox.js:133` — añade "(no se tocan, se quedan en el Inbox)" |
| INBOX-UX-6 | **Errores sin guía en `loadInboxConflicts`** (`inbox.js:314-316`) | UX | XS | ✅ `inbox.js:355-357` — guía accionable en el catch |

---

### INBOX-CFG — `target_root` apuntaba fuera de la biblioteca + gap de arcade suelto (2026-08-13)

Origen: el usuario reportó que el Inbox "solo detecta zips" tras soltar juegos de
Mega Drive, Dreamcast, MAME2003 y Nintendo DS. Investigación: `.rommgr/library_pc.db`
(`scan_runs`) mostraba 8 corridas del pipeline ese mismo día con `roms_detected`
bajando de 1719 a 0 — el Inbox sí procesaba y organizaba, pero no en
`E:\Carpetas anbernic`.

| ID | Prioridad | Hallazgo | Dónde | Estado |
|----|-----------|----------|-------|--------|
| INBOX-CFG-1 | 🔴 Crítico | **`inbox.target_root = "Este equipo\\RG556\\Ambernic"`** (ruta MTP del móvil, no un path real) se resolvía como relativa contra el cwd del proceso → `Path.resolve()` creaba `Retro_gaming_app\Este equipo\RG556\Ambernic\` dentro del propio repo, en C:. El pipeline organizaba correctamente por plataforma (megadrive/, dreamcast/, nds/…) pero en ese destino fantasma — de ahí que el usuario no viera nada organizado en `E:\Carpetas anbernic` y que C: llegara a 0 GB libres (1.527 archivos, 48,96 GB) | `config.toml:40` | ✅ `target_root` vaciado (cae al fallback `config.library_root` en `inbox_pipeline.py:727`) — servidor reiniciado. 1.024 archivos reubicados a `E:\Carpetas anbernic\<plataforma>\`, 482 duplicados exactos eliminados, 21 conflictos (mismo nombre/contenido distinto) dejados sin tocar para revisión manual — ver lista en el diario de hoy |
| INBOX-CFG-4 | 🟡 Medio | **El Inbox extrae CUALQUIER ZIP suelto sin distinguir arcade de consola** — a diferencia de `zip_router.py` (que nunca extrae un ZIP arcade, lo mueve directo a `arcade/`), el watcher normal (`_run_inbox_pipeline` Step 1, `find_zip_files`+`extract_zip`) no tiene ese filtro — es el mecanismo de siempre, no algo nuevo de esta sesión, pero el primer arranque del servidor en esta sesión lo disparó sobre los ZIPs que ya había en el Inbox, reventando **75 sets arcade** en chips sueltos. Recuperado sin pérdida: los ZIPs originales seguían en `_descartados/` (AUD-3, nunca borrado directo) — 39 eran redundantes (la biblioteca ya tenía versión igual o más completa en `arcade/`, sin tocar) y **36 se restauraron directos a `arcade/`** (sin re-extraer, sin colisión, íntegros). Verificado con búsqueda exhaustiva: los 114 ZIPs de consola del mismo lote sí se procesaron bien (extraídos → organizados correctamente en su plataforma) — el problema era solo arcade | `web/inbox_pipeline.py` Step 1 (`find_zip_files`) | ✅ nueva comprobación `_is_arcade_zip_container()` antes de `extract_zip()`: si el 100% de las entradas del ZIP coinciden con CRCs conocidos de `load_arcade_crc_index()`, se mueve intacto a `arcade/` sin extraer (mismo criterio que `zip_router.py`, ahora también aplicado al watcher automático). Tests en `tests/test_inbox_arcade_zip_route.py` |
| INBOX-CFG-2 | 🟡 Medio | **~3.526 archivos sueltos de sets MAME/arcade** (`.u12`, `.epr`, `.rom`, extensiones numéricas) en la raíz del Inbox, sin agrupar por juego — `classify_path` no los reconoce (no están en ningún catálogo de consola) y quedan como `unknown_files_detected`. Diseño actual (`ZIP-ROUTE`) asume que un set arcade siempre llega como ZIP intacto; no hay ruta de código para reconstituir chips sueltos | `web/inbox_pipeline.py` (`classify_path` los ignora), `catalog/mame_loader.py:load_arcade_crc_index()` ya da `CRC32→{set names}` reutilizable | ✅ implementado como ARCADE-RECON (`_reconstruct_loose_arcade_sets` en `web/inbox_pipeline.py:429`, PR #160): CRC32 de cada chip suelto, cobertura contra `load_arcade_crc_index()`+`load_arcade_manifest()`, solo reclama una máquina al 100% de cobertura, re-empaqueta en `<set>.zip` con verificación de contenido antes de mover a `arcade/`, descarta los chips sueltos usados (papelera, AUD-3) solo tras confirmar el ZIP en destino. Tests en `tests/test_arcade_recon.py` |
| INBOX-CFG-3 | 🟢 Menor | **21 conflictos** (mismo nombre, contenido distinto) que quedaron en la carpeta fantasma de C: | `amiga/`, `atari2600/`, `atarilynx/`, `c64/`, `gba/`, `msx/`, `nds/`, `psx/`, `unknown/` | ✅ movidos a `E:\Carpetas anbernic\<plataforma>\` con sufijo ` (conflicto-inbox 2026-08-13)` — nada se sobreescribió, quedan pendientes de comparar/elegir a mano. Carpeta fantasma de C: eliminada por completo |

---

### INBOX-ORPHAN-1 — Saves sueltos en el Inbox + notificación en bucle (hallazgo 2026-08-14)

Un `.sav` suelto en la raíz del Inbox (sin ROM acompañante en el mismo lote,
p. ej. copiado suelto desde la Anbernic) nunca casaba con nada — `scan_library`
no lo reconoce como ROM, así que quedaba "pendiente" para siempre y el
watcher lo redetectaba cada 30s, disparando notificación de escritorio en
bucle infinito.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| INBOX-ORPHAN-1 | **Reunir el save con su ROM ya organizado** — nuevo paso 1.9 del pipeline, `_route_orphan_saves()`: empareja por coincidencia EXACTA de stem contra `games` (fuera del propio Inbox); solo mueve si hay un único match y el destino no existe ya — nunca sobreescribe, nunca descarta un save sin match único, se deja intacto para revisión manual antes que arriesgar la única copia | `web/inbox_pipeline.py` | ✅ verificado en real: el `.sav` de "Kid Dracula" se reunió con su ROM en `nes\`. Test `tests/test_inbox_orphan_saves.py` (4 casos: match único, sin match, match ambiguo, destino ya existe) |
| INBOX-ORPHAN-2 | **Causa raíz de la notificación en bucle** — el watcher notificaba al *detectar* archivos pendientes, no al *terminar* el job; un `.sav` huérfano que nunca completa quedaba pendiente para siempre. Fix: notifica solo al completar el job; el watcher barre saves huérfanos en cada ciclo sin depender del pipeline pesado ni contarlos como "pendiente" | `web/daemons.py` | ✅ |

---

---

### CLOUD-UX — Wizard "Conexión cloud" poco claro (auditoría 2026-07-12)

El asistente OAuth existe (Sync → "Conexión cloud") pero no comunica qué hace ni para qué sirve.

- [x] **CLOUD-UX-1** — El panel no explica nada: solo "Dropbox — No configurado \[Conectar\]".
  Añadir una línea de contexto: "Conecta tu cuenta para sincronizar saves con la nube.
  Se abrirá el navegador para autorizar — no necesitas API key propia."
  (`web/static/partials/tab-sync.html:3-14`)
  ✅ (fix/cloud-ux — línea de contexto añadida en el paso 1 del setup)
- [x] **CLOUD-UX-2** — El badge "✓ Conectado" solo comprueba que el remote existe en rclone,
  no que su nombre coincida con `saves_remote`/`states_remote` del config. Puedes estar
  "conectado" y que el sync use otro remoto (o ninguno). Mostrar aviso si el remote
  conectado no aparece en las rutas del config. (`web/static/js/tabs/sync.js:1400-1415`)
  ✅ (fix/cloud-ux — cubierto por CLOUD-UX-9: la tarjeta muestra el destino de sync activo o avisa si falta)
- [x] **CLOUD-UX-3** — **Bug**: `_pollCloudAuth()` finaliza con "el primer provider no
  configurado" en vez del que el usuario pulsó. Con Dropbox y GDrive ambos sin configurar,
  pulsar "Conectar" en Google Drive guardaría el token bajo el remote `dropbox`.
  Fix: guardar el `providerId` en `startCloudAuth()` (variable de módulo) y usarlo en el
  finalize. (`web/static/js/tabs/sync.js:1453`)
  ✅ (fix/cloud-ux — es el mismo bug que CLOUD-UX-4 de la auditoría 2026-07-13, resuelto ahí)

---

### CLOUD-UX — Auditoría de la pestaña Cloud: UX/UI y lógica (2026-07-13)

Auditoría de la pestaña Cloud (`tab-sync.html`, `js/tabs/sync.js`, `main.js`,
`jobs.js`, `handlers/sync_cloud.py`, `handlers/cloud_auth.py`). Hallazgo
central: **el camino recomendado está roto de punta a punta** — el botón
"Usar para saves + states (recomendado)" lanza ReferenceError; si existiera,
guardaría un remote sin `:`; y si guardara bien, "Sincronizar" fallaría porque
el backend exige `[[sync.sources]]` antes de mirar los remotes implícitos.
Detalle, archivos y criterios de "hecho" en `Tareas/Roadmap-Cloud-UX.md`.
Orden: 1-6 son bugs, 7-12 UX. Todo pilar 3.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| CLOUD-UX-1 | **Tres funciones inexistentes en `window`** — `applyRcloneSavesStates()` (botón "recomendado", `tab-sync.html:165`) existe en `sync.js:556` pero no está exportada ni en `main.js`; `backupNow()` (`tab-sync.html:42`) no existe (solo `API.backupNow`, `api.js:142`); `loadManualBackups` no existe → `main.js:479` lanza ReferenceError (`?.()` no protege identificadores no declarados) y **`loadCloudAuthStatus()` nunca corre al abrir la pestaña** ("Comprobando…" eterno); `jobs.js:439` TypeError tras cada backup. Fix: escribir `backupNow`/`loadManualBackups`, exportar las tres + window | Bug | S | ✅ (fix/cloud-ux — backupNow/loadManualBackups escritas, las 3 exportadas + window) |
| CLOUD-UX-2 | **Los botones "Guardar" del panel rclone escriben remotes sin `:`** — `/api/rclone-status` devuelve remotes con `rstrip(":")` (`sync_cloud.py:143`) y `applyRcloneRemote`/`applyRcloneSavesStates` concatenan `remote + path` (`sync.js:543,562-563`) → guardan `dropboxRetroSync/saves`. "Verificar conexión" sí funciona (backend re-añade `:`, `sync_cloud.py:196`): test OK + guardado roto. La preselección (`sync.js:489-491`) compara con `:` y nunca coincide | Bug | XS | ✅ (fix/cloud-ux — el value del select conserva ':' y la preselección usa split(':')) |
| CLOUD-UX-3 | **"Sincronizar" falla con la config recomendada** — `_do_sync` corta con "No hay fuentes de sync configuradas… [[sync.sources]]" (`sync_cloud.py:246-251`) ANTES del bloque D2 de remotes implícitos `saves_remote`/`states_remote` (`:346-366`). El aviso del frontend tiene el mismo punto ciego (`sync.js:34-43`). Fix: error solo si no hay ni sources ni remotes implícitos | Bug | S | ✅ (fix/cloud-ux — remotes implícitos cuentan como fuentes; context bar los muestra; test nuevo) |
| CLOUD-UX-4 | **El wizard OAuth puede escribir el token en el provider equivocado** — `_pollCloudAuth` finaliza contra "el primer provider no configurado" (`sync.js:1532-1543`); con ambos sin configurar, conectar Google Drive escribe el token bajo el remote `dropbox` (`_PROVIDERS` lista dropbox primero, `cloud_auth.py:23-26`). Fix: retener el provider iniciado (mejor en `/api/cloud-auth/poll`); de paso, guard de flujo concurrente y cancel que mate el subprocess | Bug | S | ✅ (fix/cloud-ux — poll devuelve provider/remote_name; guard de flujo concurrente + /cancel mata el subprocess; 3 tests) |
| CLOUD-UX-5 | **`sync_result` sin guard `result_ts`** — `jobs.js:104-105` llama `_renderSyncResult` en cada tick (scan/match/backup sí usan `_shownResultTs`); la notificación de escritorio "Sync completado" (`sync.js:1452-1462`) se re-dispara cada 2 s mientras el polling siga vivo por otro job. Fix: mismo guard + refrescar `loadSync()` al consumir resultado | Bug | XS | ✅ (fix/cloud-ux — guard _shownResultTs.sync + loadSync() al consumir resultado real) |
| CLOUD-UX-6 | **Modo TV roto** — `tvStartSync` postea a `/api/do-sync` (`sync.js:334`); el endpoint real es `/api/sync` (`sync_cloud.py:90`). El flujo táctil ANBERNIC-TV muere con error siempre | Bug | XS | ✅ (arreglado en feature/anbernic-ux — `/api/sync`) |
| CLOUD-UX-7 | **Script bootstrap Termux hardcodea `dropbox:/RetroSync/saves`** — `_build_bootstrap_script` (`sync_cloud.py:666`) ignora `config.sync.saves_remote` y `save_extensions`; con gdrive u otra carpeta la consola bisync-ea contra un remote inexistente. Además `rclone bisync` vs `SaveSyncer` = dos motores con políticas de conflicto distintas. Fix mínimo: inyectar remote y extensiones reales | Sync | S | ✅ (resuelto por ANBERNIC-UX-1: generador canónico con remotes de config y `copy --update`) |
| CLOUD-UX-8 | **Reordenar la pestaña** — la config imprescindible (remote+carpeta) está al fondo tras "⚙ Verificar rclone" (`tab-sync.html:106-178`); 4 superficies de configuración solapadas; los comparadores PC-vs-consola (`:62-104`) son herramientas de dispositivo, no de cloud. Fix: checklist de setup arriba (Conectar → Carpeta → Probar, colapsable cuando todo verde), luego Sincronizar+estado, backup al final; comparadores a Cable/Herramientas | UX | M | ✅ (fix/cloud-ux — setup checklist colapsable arriba (Conectar→Carpeta→Probar), comparadores en <details> al fondo) |
| CLOUD-UX-9 | **"Conectado" ≠ "sync configurado"** — el wizard OAuth acaba en "✓ Conectado" pero nadie configura `saves_remote`: verde + error de fuentes al sincronizar. Fix: tras finalize, ofrecer "Usar `<remote>:RetroSync` para saves+states" a un clic (reutiliza `applyRcloneSavesStates` tras CLOUD-UX-1/2) y mostrar el destino activo en la tarjeta (`_rcloneActiveTargetHtml` ya lo calcula, `sync.js:447-459`) | UX | S | ✅ (fix/cloud-ux — destino de sync en la tarjeta + useRemoteForSync() a un clic) |
| CLOUD-UX-10 | **Mensajes que mandan a editar config.toml / a Settings** — "configura [[sync.sources]] en config.toml" (`sync.js:38,43`) y el error de `loadSync` enlaza a Settings (`sync.js:65`) cuando el panel rclone está en esta misma pestaña. Fix (tras CLOUD-UX-3): apuntar al bloque de setup de la propia pestaña | UX | XS | ✅ (fix/cloud-ux — openCloudSetup(); config.toml solo para el modo avanzado) |
| CLOUD-UX-11 | **"Estado de saves" y backups no cargan solos** — exigen clic "↻ Cargar" (`tab-sync.html:56`) siendo lecturas locales baratas (`/api/save-comparison`, `games.py:367`). Fix: auto-cargar en `showTab('sync')`, ↻ queda para refrescar | UX | XS | ✅ (fix/cloud-ux — auto-carga en showTab('sync')) |
| CLOUD-UX-12 | **`sync-decisions` muerto: el resultado no dice qué archivos se movieron** — el backend envía las decisiones por archivo (`sync_cloud.py:323-327`) y el div existe (`tab-sync.html:33`) pero nadie lo rellena; `_renderSyncResult` solo pinta totales (`sync.js:1440-1466`). Fix: listar acción+ruta por fuente, conflictos destacados; en dry run es el "plan" antes de sincronizar | UX | S | ✅ (fix/cloud-ux — decisiones por fuente con dirección y conflictos destacados) |

---

---

### INICIO-UX — Auditoría de la pestaña Inicio (2026-07-13)

Auditoría UX de Inicio (`tab-overview.html`, `js/tabs/overview.js`) desde la
perspectiva de un usuario nuevo. Detalle completo, archivo:línea y fases en
`Tareas/diario/archivo/Roadmap-Inicio-UX.md` (archivado 2026-07-16, implementado
en la rama `fix/inicio-ux`). Hallazgos clave: los 3 botones rápidos del
dashboard están **rotos** (comillas `\'` estilo Python servidas tal cual al
navegador → SyntaxError), los canvas usan `var(--c-*)` como fillStyle (canvas
no resuelve variables CSS → heatmap y gráfico mensual pintan colores
incorrectos), y hay dos heatmaps de actividad duplicados. Incluye la petición
del usuario: tarjetas explicando los archivos no-gaming (BIOS, assets, saves,
infra MAME, basura) reutilizando las categorías de `builders/folders.py`.

| ID | Task | Esfuerzo | Estado |
|----|------|----------|--------|
| INICIO-UX-F1 | Fase 1 — bugs visibles: onclick rotos del dashboard (`tab-overview.html:26-28`), hex literales en canvas (`overview.js:166,270`), eliminar heatmap canvas duplicado (S36-2) | XS | ✅ (fix/inicio-ux) |
| INICIO-UX-F2 | Fase 2 — idioma: tarjetas "Games/Matched/Unmatched/wasted" → español (`overview.js:449-455,537-543`), unificar "Escanear", "Corregir plataformas" | S | ✅ (fix/inicio-ux) |
| INICIO-UX-F3 | Fase 3 ⭐ — sección "Además de juegos…": tarjetas explicativas de BIOS / assets / saves / infra MAME / basura con qué es + NO borrar/borrable + link al tab correspondiente; conteos desde `/api/status` y junk-scan (`builders/folders.py:51-96`) | M | ✅ (fix/inicio-ux) |
| INICIO-UX-F4 | Fase 4 — errores accionables: mensajes en español + Reintentar (`overview.js:514,546,668`), wizard sin `alert()` (`:811,836`), CTA en "salud: sin datos" | S | ✅ (fix/inicio-ux) |
| INICIO-UX-F5 | Fase 5 — rendimiento y pulido: un solo fetch de `/api/status` (hoy 3) y `/api/games?limit=10000` (hoy 3), hover en tarjetas clicables, placeholder de imagen | S-M | ✅ (fix/inicio-ux) |

---

### Hallazgos INICIO-UX (2026-07-16, prueba con biblioteca real)

| ID | Prioridad | Hallazgo | Dónde | Estado |
|----|-----------|----------|-------|--------|
| INICIO-FIX-1 | 🟡 Bajo | **`int(rom.get("size", 0))` revienta con `size=""`** — un DAT real (FBNeo/MAME en `catalogs/arcade/`) trae `<rom size="">` y el parser lanza `ValueError` (logueado, el catálogo se carga a medias). Su gemelo en la línea 190 ya tiene el fix `or 0`; se corrigió un sitio y no el otro | `catalog/catalog_loader.py:135` | ✅ rama `fix/inicio-ux` — `or 0` + test |
| INICIO-FIX-2 | 🟢 Menor | **`load_arcade_infra_names` parsea el `mame.xml` de 608 MB (~11 s) en cada llamada** — lo pagan cada junk-scan y cada refresh de `/api/library-extras` (TTL 15 min). El ponytail "cachear si algún día duele" (maintenance.py) ya duele: memoizar por `(path, mtime)` en `mame_loader` beneficia a todos los callers | `catalog/mame_loader.py:75-103` | ✅ rama `fix/inicio-ux` — memoización por firma (nombre, mtime, tamaño) + test |
| INICIO-FIX-3 | 🟢 Menor | **`mame0278.xml` vacío (0 bytes) en `catalogs/arcade/`** — descarga/generación fallida; cada loader lo abre y lo descarta en silencio. Borrarlo (acción de usuario o incluirlo en INICIO-FIX-2) | `.rommgr/catalogs/arcade/mame0278.xml` | ✅ borrado (2026-07-16) |
| INICIO-FIX-4 | ✨ Mejora | **El listxml de MAME ahora es descargable desde Ajustes → Catálogos** — entrada "MAME XML (bios/devices)" en el grupo Arcade: resuelve la última release vía API de GitHub, baja el asset `*lx.zip` (~19 MB) y lo extrae como `catalogs/arcade/mame.xml` (~320 MB, escritura atómica vía `.part`). Verificado E2E con red real (v0.288, 7.297 nombres de infra) | `web/handlers/scan.py` (`_download_mame_listxml`) | ✅ rama `fix/inicio-ux` |

---

### ASSETS-UX — Auditoría de la pestaña Assets: UX/UI (2026-07-13)

Auditoría de la pestaña Assets (`tab-assets.html` + `loadAssets()` en
`sync.js:70-111`, la pestaña más pequeña auditada hasta ahora). Hallazgo
central: `_deviceRoot()` (`main.js:430-435`) no tiene el mismo fallback a
localStorage que ya usa el texto de la barra de contexto (`sync.js:85`) —
la cabecera puede decir "Viendo: Android" mientras la tabla muestra datos
del PC, sin ninguna pista de que no coinciden. Es una función compartida:
el mismo bug aplica a Colección, Organizar y Juegos. Detalle, archivo:línea
y fases en `Tareas/diario/archivo/Roadmap-Assets-UX-completado.md`.
**Completado** — ver ASSETS-UX-1..5 arriba.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| ASSETS-UX-1 | **La ruta mostrada como "Viendo: X" puede no ser la que se consulta** — `_deviceRoot()` (`main.js:430-435`) no tiene fallback a `localStorage('anbernic_path')` a diferencia del texto de la barra (`sync.js:85`); afecta también a `collection.js`, `organize.js`, `games.js` que usan la misma función | Bug | S | ✅ `main.js:439` — `_deviceRoot()` ya incluye el fallback a `localStorage('anbernic_path')` |
| ASSETS-UX-2 | **"Ejecuta un Scan" también sale cuando el filtro simplemente no tiene resultados** — el filtro se aplica antes de comprobar vacío (`sync.js:92-94`); "Solo huérfanos" sin ninguno (buena noticia) muestra el mismo mensaje que "nunca escaneado" | UX | XS | ✅ `sync.js:122-128` — distingue "nunca escaneado" de "✓ Sin resultados para este filtro" |
| ASSETS-UX-3 | **Error sin guía, a diferencia del resto del mismo archivo** — catch de `loadAssets` (`sync.js:108-109`) solo muestra `e.message`; el catch de `loadSync` unas líneas arriba (`sync.js:65`) sí da pista + enlace a Ajustes | UX | XS | ✅ `sync.js:145` — catch da guía + enlace a Ajustes |
| ASSETS-UX-4 | **Columna "Huérfanos" sin ninguna acción asociada** — solo informativo, sin enlace para ver/mover/eliminar los archivos concretos (`sync.js:104`) | UX | S | ✅ `sync.js:139` (`showOrphanAssets()`) — acción "Ver" lista los archivos concretos |
| ASSETS-UX-5 | **Estado vacío sin enlace a la acción que lo resuelve** — "Ejecuta un Scan" es texto plano sin botón a Organizar (`sync.js:94`) | UX | XS | ✅ `sync.js:123` — enlace a `showTab('plan')` (Organizar) en el mismo mensaje |

---

### COLECCION-UX — Auditoría de la pestaña Colección + ¿fusión con Juegos? (2026-07-13)

El usuario preguntó si Colección y Juegos deberían fusionarse. Comparando el
código: ambas pintan una galería casi idéntica (mismo endpoint `/api/games`,
mismo panel de detalle `openGamePanel`), pero Colección solo expone 3 de los
9 filtros de Juegos — es un subconjunto duplicado, no una vista distinta. Lo
que Colección aporta de verdad son sus paneles de análisis agregado (Stats,
Disco, Diff PC/Android, Completitud, Wishlist), que no tienen sentido dentro
de la ficha de un juego. **Recomendación: no fusionar mecánicamente — retirar
la galería duplicada de Colección y dejar la pestaña como dashboard de
análisis puro.** Razonamiento completo y hallazgos de bugs en
`Tareas/diario/archivo/Roadmap-Coleccion-UX-completado.md`.
**Completado** — ver COLECCION-UX-1..5 arriba.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| COLECCION-UX-1 | **Botón "🏥 Health" no hace nada** — `togglePlatformHealth()` se llama sin argumento (`tab-collection.html:22`), nunca alterna el panel (a diferencia de sus hermanos en `collection.js`), y escribe en `#platform-health-content` que no existe (real: `#ph-table`); `loadPlatformHealth()` es además un TODO puro (`esde.js:632-661`). Cuarta ocurrencia del patrón HTML/JS-ID-mismatch (HERR-UX-1/2/3, FORMATOS-UX-2) | Bug | S | ✅ el panel y sus funciones (`togglePlatformHealth`/`loadPlatformHealth`) ya no existen — retirado al rehacer la pestaña como dashboard (COLECCION-UX-2) |
| COLECCION-UX-2 | **Dos galerías divergentes del mismo dato** — Colección (`col-grid`) y la vista cuadrícula de Juegos comparten endpoint y panel de detalle pero Colección solo tiene 3 de los 9 filtros de Juegos; decisión de producto antes de tocar código (ver recomendación de fusión) | Decisión | M | ✅ galería duplicada retirada (`tab-collection.html:5`, comentario explícito); `col-grid` ya no existe en el código — la pestaña es dashboard de análisis puro |
| COLECCION-UX-3 | **"Exportar CSV" da resultados distintos según la pestaña** — el export de Juegos no manda `root` (`tab-games.html:46-47`), el de Colección sí (`collection.js:311-313`); mismo botón, mismo texto, distinto resultado sin avisar | Bug | XS | ✅ único endpoint `/api/export-library` (`collection.py:180`), usado solo desde `tab-games.html:46-47`; `collection.js` ya no tiene export CSV propio |
| COLECCION-UX-4 | **"ROMs faltantes" es código muerto con mejor funcionalidad que el panel activo** — `missing-section`/`loadMissingRoms()` (`tab-collection.html:113-124`, `collection.js:65-88`) nunca se invoca desde ningún botón, pero tiene wishlist + enlace IA + copiar búsqueda que el panel "Completitud" vivo no tiene | UX | S | ✅ `tab-collection.html:38` — botón "📥 Ver ROMs faltantes" dentro de Completitud ya invoca `loadMissingRoms()` |
| COLECCION-UX-5 | **Pulido: 5 acordeones sin "cerrar todos" + filtro de plataforma duplicado con estilo distinto al de Juegos** (`collection.js:182-197` vs `games-platform` select) | UX | XS | ✅ `collection.js:23-28` (`_showOnlyPanel`) — acordeón exclusivo, abrir uno cierra los demás |

---

### DUPLICADOS-UX — Auditoría de la pestaña Duplicados: UX/UI (2026-07-13)

Auditoría de la pestaña Duplicados (`tab-duplicates.html` +
`js/tabs/duplicates.js`). A diferencia de otras pestañas, aquí no hay
botones muertos — el problema central es un desajuste real entre lo que se
confirma y lo que se borra: el filtro de plataforma es solo visual,
`deleteAllDuplicates()` cuenta filas del DOM ya filtrado para el diálogo de
confirmación pero el backend borra duplicados de **toda** la biblioteca sin
recibir ningún filtro. Detalle, archivo:línea y fases en
`Tareas/Roadmap-Duplicados-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| DUPLICADOS-UX-1 | **"Eliminar todos" borra más de lo que confirma con un filtro de plataforma activo** — el filtro solo afecta al render (`duplicates.js:381-386`); `deleteAllDuplicates()` cuenta filas del DOM filtrado para el diálogo pero llama a `/api/duplicates/delete-all` con `source_root:''` (`duplicates.js:64-109`), que borra duplicados de toda la biblioteca sin filtro de plataforma posible en el backend (`services/duplicates_service.py:90`) | Bug | S | ✅ |
| DUPLICADOS-UX-2 | **Toasts rotos: `showToast(msg, true/false)` en vez del string esperado** — `deleteAllDuplicates` (líneas 67,103) y `deleteDuplicate` (línea 134); el resto del mismo archivo usa `'ok'/'err'/'info'` correctamente | Bug | XS | ✅ |
| DUPLICADOS-UX-3 | **Mensajes contradictorios sobre si el borrado se puede deshacer** — 4 acciones dicen "no se puede deshacer" pese a usar la misma papelera `_descartados/` (AUD-3) que `deleteRaDuplicate`, cuyo mensaje sí lo menciona ("difícil de deshacer") | UX | S | ✅ |
| DUPLICADOS-UX-4 | **`confirm()` nativo en 2 de 6 sitios pese a tener `_showConfirm` ya importado** — `deleteRaDuplicate` (línea 255) y `discardAllRaDuplicates` (línea 323) | UX | XS | ✅ |
| DUPLICADOS-UX-5 | **"Copia intencional ✓" es permanente sin UI para revisarla o deshacerla** — `markAsIntentionalCopy` excluye un grupo para siempre; no existe ninguna lista de grupos excluidos en la app | UX | S | ✅ |
| DUPLICADOS-UX-6 | **"Tools" en inglés (y nombre de pestaña incorrecto) en 2 sitios** — `tab-duplicates.html:22` y `duplicates.js:331`; la pestaña real se llama "Herramientas" | UX | XS | ✅ |
| DUPLICADOS-UX-7 | **Estado vacío filtrado sin botón para quitar el filtro** — a diferencia del estado vacío general, que sí usa el componente `_emptyState` con CTA (`duplicates.js:390-392`) | UX | XS | ✅ |

---

### PLAN-UX — Auditoría de la pestaña Plan/Organizar: UX/UI (2026-07-13)

Auditoría de la pestaña Plan (`tab-plan.html` + `js/tabs/organize.js`) — la
más madura de las auditadas hasta ahora (resumen, progreso, panel de
errores, buena distinción colisión-de-plan vs conflicto-de-disco con enlace
a Duplicados). El usuario preguntó si podía fusionarse con otra pestaña:
**no hay una duplicación clara que lo justifique** — el solapamiento con
Duplicados ya está bien explicado en la propia UI; el candidato real para
una futura revisión es Inbox (su pipeline automático ya hace internamente
lo que Plan hace a mano), pendiente de auditar. Detalle, archivo:línea y
fases en `Tareas/diario/archivo/Roadmap-Plan-UX-completado.md`.
**Completado** — ver PLAN-UX-1..5 arriba.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| PLAN-UX-1 | **"La operación es reversible" sin que exista ningún "Deshacer"** — `doApply()` lo afirma en su confirmación (`organize.js:458`) pese a que `MEJ-2` (deshacer último apply) sigue pendiente; `applyKeepBoth()` ni lo menciona | UX | XS | ✅ `organize.js:453` — el modal ya no promete reversibilidad, comentario explícito citando MEJ-2 |
| PLAN-UX-2 | **Las dos acciones de mayor riesgo usan `confirm()` nativo; las de menor riesgo, el modal propio** — `doApply`/`applyKeepBoth` (líneas 458,310) vs `deleteCollisionDuplicates`/`_discardCollisionEntry` (líneas 401,429), mismo archivo | UX | XS | ✅ `organize.js:298,452` — ambas usan `_showConfirm` |
| PLAN-UX-3 | **"Filtrar por dispositivo" quedó sin función útil tras DEVSEL-FIX-3** — `/api/plan` ya resuelve un único repositorio por dispositivo activo; el dropdown (`tab-plan.html:29-34`) filtra sobre datos que ya son de un solo dispositivo, vaciando la tabla sin explicación si se elige el que no se está viendo | UX | S | ✅ `tab-plan.html:28` — dropdown retirado, comentario explícito (el selector global PC/Consola ya cumple esa función) |
| PLAN-UX-4 | **Mismo bug de `_deviceRoot()` que ASSETS-UX-1** — `organize.js:52,322,469`; se resuelve con el mismo fix compartido en `main.js` | Bug | — | ✅ cubierto por ASSETS-UX-1 — `organize.js` sigue llamando al mismo `window._deviceRoot()` ya arreglado |
| PLAN-UX-5 | **Conflictos "unknown" sin ninguna explicación** — a diferencia de los tipos `collision`/`disk`, que sí tienen contexto y acciones (`organize.js:164,265-272`) | UX | XS | ✅ `organize.js:156-161` — la rama `unknown` (código muerto) se retiró; solo quedan `collision`/`disk`, ambos con explicación |

---

### SCRAPER-UX — Auditoría de la pestaña Scraper: UX/UI (2026-07-13)

Auditoría de la pestaña Scraper (`tab-scraper.html` + `js/tabs/scraper.js`).
Sin botones muertos ni riesgo de datos (solo lee/escribe metadatos). El
problema central: la funcionalidad de ScreenScraper está repartida entre
Scraper y Settings sin puente entre ellas — la cuota de peticiones diarias
solo se ve en Settings, y exportar `gamelist.xml` existe por duplicado en
ambas pestañas con el mismo endpoint. Detalle, archivo:línea y fases en
`Tareas/Roadmap-Scraper-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| SCRAPER-UX-1 | **Cuota de ScreenScraper solo visible en Settings** — `loadSsQuota()` (`scraper.js:71-98`) solo se llama al abrir Settings (`main.js:483`); sus elementos no existen en `tab-scraper.html`, pese a que aquí es donde se necesita mientras se scrapea | UX | S | ✅ `loadSsQuota()` generalizada para actualizar ambos paneles (sufijo `-scraper` en los IDs); nuevo bloque en `tab-scraper.html`; se llama al abrir la pestaña |
| SCRAPER-UX-2 | **Exportar gamelist.xml duplicado en dos pestañas** — panel completo en Scraper (`tab-scraper.html:56-79`) + botón suelto en el widget ES-DE de Settings (`esde.js:29`, `doExportGamelistsAll`), mismo endpoint `/api/export-gamelists`, sin relación visible entre ambos | UX | S | ✅ nota junto al botón de ES-DE (`esde.js`) aclarando que es el mismo export que en Scraper, con más opciones allí |
| SCRAPER-UX-3 | **Sin comprobación proactiva de credenciales SS** — el usuario solo se entera de que faltan al pulsar "Iniciar scraping" y recibir un error (`doScrape`, `scraper.js:146-151`); Herramientas ya tiene este chequeo proactivo para la API key de RA como referencia | UX | S | ✅ nuevo `loadSsCredsStatus()` (mismo patrón que `ra-api-key-status`) + chequeo proactivo en `doScrape()` antes de lanzar el job |
| SCRAPER-UX-4 | **Mensajes de error sin guía** — `doScrape`/`doExportGamelists` (líneas 148,178) muestran `e.message` crudo | UX | XS | ✅ `_friendlyError()` traduce fallos de red/fetch a un mensaje guiado; resto de mensajes se mantienen sin cambios |
| SCRAPER-UX-5 | **Jerga interna "SAGE-1"/"Sage" filtrada a la UI** — tooltip (`tab-scraper.html:23`) y texto de cobertura (`scraper.js:63`) mencionan el código interno de una tarea del backlog sin explicarlo | UX | XS | ✅ ambas menciones eliminadas |
| SCRAPER-UX-6 | **`useEsdeGamelistDir()` es código muerto** — exportada pero ningún botón la llama (`scraper.js:28-33`) | UX | XS | ✅ eliminada junto con `_autoFillEsdeGamelistDir()`/`_esdeGamelistsDir` (dead code en cascada: sin `useEsdeGamelistDir()` tampoco tenían lector) |
| SCRAPER-UX-7 | **Exportar gamelists no deshabilita su botón durante la llamada** — inconsistente con `doScrape`, riesgo bajo | UX | XS | ✅ `doExportGamelists()` deshabilita el botón con texto "Exportando…" (patrón `try/finally`) |

---

### TV-UX — Auditoría del Modo TV: UX/UI (2026-07-13)

Auditoría del Modo TV (`tab-tv.html` + `games.js:904-976` +
`main.js:737-782`). Modo de navegación legítimamente distinto (foco por
teclado, pantalla completa) — no candidato a fusión. Dos hallazgos
críticos: la colección se corta en 120 juegos sin forma de cargar más
(`_TV_LIMIT`, paginación soportada por el backend pero nunca disparada), y
la barra de filtro por plataforma existe en el HTML pero ninguna función
la rellena jamás — planeada pero nunca conectada. Detalle, archivo:línea y
fases en `Tareas/Roadmap-TV-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| TV-UX-1 | **La colección se corta en 120 juegos sin forma de cargar más** — `loadTvGrid` soporta `offset` (`games.js:918-934`) pero nada lo dispara nunca con offset > 0; `_tvMoveFocus` simplemente deja de avanzar al llegar al final sin avisar | Bug | S | ✅ `_tvMoveFocus` carga la siguiente página automáticamente (`_tvHasMore`) al llegar al final; si de verdad no hay más, aviso "No hay más juegos por aquí" en `tv-info-keys`. Verificado en navegador: filtro Atari 2600 (175 juegos) cargó 2 páginas y mostró el aviso al final real |
| TV-UX-2 | **Barra de filtro por plataforma nunca rellenada** — `tv-platform-bar`/`tv-platform-label` (`tab-tv.html:3-4`) vacíos para siempre; `loadTvGrid` ya acepta `platform` pero `enterTvMode()` siempre llama con `''` (`games.js:905-910`) | Bug | S | ✅ `_tvLoadPlatformBar()` rellena los chips desde `/api/games/filter-options` (mismo endpoint que Juegos/Scraper); clic filtra la rejilla y resalta el chip activo. Verificado en navegador |
| TV-UX-3 | **"Salir" siempre vuelve a Colección, ignorando de dónde viniste** — `exitTvMode()` hace `showTab('collection')` fijo (`games.js:912-916`) pese a que `t` es un atajo global desde cualquier pestaña | UX | XS | ✅ `enterTvMode()` guarda la pestaña activa en `_tvSourceTab` (solo la primera vez, no si `t` se repite ya en TV); `exitTvMode()` vuelve ahí. Verificado en navegador: entrar desde Análisis y salir vuelve a Análisis |
| TV-UX-4 | **Fallo de red deja la rejilla en blanco sin ningún aviso** — catch de `loadTvGrid` solo hace `console.error` (`games.js:933`), sin mensaje visible en un modo a pantalla completa | UX | XS | ✅ mensaje visible en `tv-grid` en la carga inicial (offset 0); las cargas de paginación solo registran el error en consola, sin romper lo ya mostrado |
| TV-UX-5 | **Pulido: fallo de pantalla completa silencioso + `_tvCols` no se recalcula al redimensionar** (`games.js:908,959`) | UX | XS | ✅ toast de aviso si `requestFullscreen()` falla (Modo TV sigue funcionando en ventana); listener de `resize` recalcula `_tvCols` mientras `_tvActive`. Verificado en navegador (el toast salió en la propia sesión de prueba, sin fullscreen real disponible) |

---

### SETTINGS-UX — Auditoría de la pestaña Settings: UX/UI (2026-07-13)

Auditoría de la pestaña Settings (`tab-settings.html`, ~500 líneas/20+
paneles, + `js/tabs/config.js`, ~870 líneas) — la más grande de la app.
Hallazgo principal, verificado de forma independiente en frontend y
backend: el campo "ES-DE carpeta" nunca ha podido guardar nada porque el
backend filtra `launchers.esde` de su lista de claves permitidas (a
diferencia de `launchers.retroarch`, que sí está) — fix de una línea.
Detalle, archivo:línea y fases en `Tareas/Roadmap-Settings-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| SETTINGS-UX-1 | **"ES-DE carpeta" nunca se guarda, para nadie** — el frontend envía `launchers.esde` (`config.js:621-622`) pero el `allowed` set del backend no lo incluye (`handlers/config.py:242-272`, comparar con `launchers.retroarch` que sí está); se descarta en silencio antes de escribir `config.toml` | Bug | XS | ✅ `launchers.esde` añadido al set `allowed` (`config.py:274`) |
| SETTINGS-UX-2 | **4 campos se guardan bien pero nunca muestran "✓ Guardado"** — `sync.saves_remote`/`sync.states_remote`/`sync.ra_config_remote`/`retroachievements.username` faltan en el mapa `_CFG_CHECK` (`config.js:645-656`) pese a tener el mismo `<span class="cfg-saved">` que sus vecinos en el HTML | UX | XS | ✅ añadidos al mapa `_CFG_CHECK`; de paso se encontró un 5º campo con el mismo bug (`sync.playtime_remote`, no documentado aquí) y se corrigió junto con los demás |
| SETTINGS-UX-3 | **Panel "Configurar consola Android" (QR) — ya cubierto por ANBERNIC-UX-2** — mismo endpoint 404 (`/api/anbernic-setup.sh`), aplica también a esta copia del panel (`tab-settings.html:12-39`) | Bug | — | ✅ (panel eliminado en feature/anbernic-ux) |
| SETTINGS-UX-4 | **"Migrar BD a dos DBs" sin confirmación** — única operación de BD sin `confirm()`/`_showConfirm` en la pestaña, a diferencia de "Vaciar papelera" y "Cerrar Retro Vault" (`config.js:111-124`) | UX | XS | ✅ `migrateSplitDb()` envuelta en `_showConfirm(...)`, mismo patrón que `clearPin()` |
| SETTINGS-UX-5 | **Pulido: la mayoría de campos no tienen confirmación inline** — solo dependen del toast genérico al guardar | UX | XS | ✅ añadido `<span class="cfg-saved">` + entrada en `_CFG_CHECK` a los 8 campos restantes sin checkmark propio: `android.device_name`, `sync.ra_config_dir`, `web.host`, `launchers.retroarch`, `launchers.esde`, `backup.saves_enabled`, `backup.saves_keep_n`, `notifications.desktop` — ahora los 22 campos guardables de Settings tienen confirmación inline |

---

### HERR-UX — Auditoría de la pestaña Herramientas: UX/UI (2026-07-13)

Auditoría de la pestaña Herramientas (`tab-tools.html` + JS repartido en
`esde.js`, `config.js`, `duplicates.js`, `sync.js`, `jobs.js`). Patrón
dominante: **la migración de frontend.py a parciales dejó HTML y JS apuntando
a IDs distintos** — tres paneles enteros tienen botones que no hacen nada al
pulsarlos (`getElementById` → null → return silencioso): Informe de
biblioteca, Saves huérfanos y el render de resultados del Health Check.
Detalle, archivo:línea y fases: esta misma tabla (nunca se creó un
`Roadmap-Herramientas-UX.md` aparte, a diferencia de otras pestañas
auditadas ese día). **Completado 2026-07-20, rama `feature/herr-ux`.**

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| HERR-UX-1 | **Panel "Informe de biblioteca" desconectado** — `generateReport` renderiza en `library-report-content` (no existe en ningún parcial, `esde.js:1207-1348`); el HTML usa `report-content`/`rpt-tab-*` (`tab-tools.html:116-150`) y sus 6 sub-tabs pasan `'zips'…'chd'` mientras el switch JS solo maneja `'overview'…'orphans'`; `btn-export-report` nunca se des-oculta. "Generar informe" no hace nada visible. Fix: reconectar a una sola versión o dejar solo los botones de informe HTML servidor (que sí funcionan, `main.js:583`) | Bug | M | ✅ reescritos `generateReport`/`showReportTab`/`_renderReport*` para los IDs y datos reales (`zips`/`playlists`/`multidisc`/`orphans` de `/api/library-report`); RA y CHD añadidos reutilizando el mecanismo **ya existente** (resultados cacheados de los jobs de ra-check/convert-chd vía `job_manager`, el mismo dato que ya consume `utils/library_report_html.py` para el informe exportable) — descartado un intento inicial de recalcular RA/CHD desde cero por ser redundante con esto. `exportReportHtml` reescrito con colores hardcodeados (HERR-UX-11) |
| HERR-UX-2 | **"Buscar huérfanos" no hace nada** — `doFindOrphans` es un stub TODO que además escribe en `orphans-result-content` (HTML: `orphan-result`, `esde.js:903`); `orphan-path` no lo lee nadie; las acciones Mover/Eliminar existen pero son inalcanzables (`esde.js:916-980`). El dato ya está en `/api/library-report` (clave `orphans`) — reutilizar | Bug | S | ✅ reutiliza `/api/library-report`; corregido de paso `doMoveOrphansToArchive` (leía `window.AppState.config`, que no existe — siempre fallaba con "Biblioteca no configurada") |
| HERR-UX-3 | **Resultados del Health Check nunca se muestran** — todo el render va a `health-result-content`; el HTML tiene `health-result` (`esde.js:495,512,530` vs `tab-tools.html:75`). La barra de progreso funciona (jobs.js usa IDs correctos) y al terminar el resultado desaparece sin rastro. Fix de 1 línea: unificar el ID | Bug | XS | ✅ |
| HERR-UX-4 | **"Resolver todos" del Library Doctor invisible para siempre** — nace `class="btn hidden"` (`.hidden` con `!important`, `app.css:1225`) y el JS intenta mostrarlo con `style.display` (`esde.js:1039`), que no vence al `!important`. `doctorResolveAll` es código muerto. Fix: `classList.toggle('hidden', …)` | Bug | XS | ✅ |
| HERR-UX-5 | **"¿Qué catálogos me faltan?" descarga TODOS los DATs sin preguntar** — tras el diagnóstico lanza `POST /api/download-dats {all:true}` automáticamente (`esde.js:1160-1166`). Fix: dos pasos — diagnóstico puro + botón "Descargar catálogos que faltan (N)" + CTA hacia Identificar al acabar | UX | S | ✅ `downloadMissingDats()` extraída como paso explícito; CTA a Identificar al terminar |
| HERR-UX-6 | **Mojibake «ྠltimo»** — `&#xfa0;` (letra tibetana) en vez de `Ú` en la programación del Health Check (`config.js:241`) | Bug | XS | ✅ |
| HERR-UX-7 | **Contexto PC/Android incompleto** — `setToolsContext` (`duplicates.js:345-372`) rellena el ID inexistente `health-path`, toca inputs de la pestaña Formatos (`zip-path`, `chd-path`) sin que se vea, no actualiza `report-path`/`m3u-path`/`verify-multidisc-path`, y pisa rutas escritas a mano sin avisar. Mover la función a `tools.js` al tocarla | UX | S | ✅ el pisado sin avisar y `m3u-path`/`verify-multidisc-path` ya se arreglaron en FORMATOS-UX-1; esta sesión añade `report-path` a la lista de `_setIfEmpty`. `health-path` (ID muerto) ya se había eliminado |
| HERR-UX-8 | **Doctor: "✓ Resolución completada" aunque haya fallos** — `doctorResolveAll` traga errores y no recalcula el resumen; filas solo se atenúan (`esde.js:1095-1117`). Fix: contar ok/fallos y relanzar `doLibraryDoctor()` | UX | XS | ✅ |
| HERR-UX-9 | **Batch "Aplicar todo": sin cancelar ni progreso real** — `alert()` nativos, botón deshabilitado sin cambiar texto, sin "paso 2 de 5", polling sin timeout, Scraper sin validar credenciales SS (`config.js:312-395`) | UX | S | ✅ `showToast` en vez de `alert()`; chequeo proactivo de `screenscraper_pass_set`; botón con texto "Ejecutando…"; "Paso X/N" en el estado; timeout de 30 min en el polling |
| HERR-UX-10 | **Labels inconsistentes** — «Iniciar Health Check» vs «Comprobar biblioteca» (error path `esde.js:507,519`); «Settings» vs «Ajustes» (`tab-tools.html:92` vs `:183`); títulos en inglés (Library Doctor, Health Check) | UX | XS | ✅ unificado a "Iniciar Health Check"; "Settings"→"Ajustes". Los h3 "Library Doctor"/"Health Check" se dejan como nombres de feature ya asentados |
| HERR-UX-11 | **Estados de carga eternos + pulido** — «Verificando API key…» nunca cambia si `/api/config` falla (`config.js:302` catch silencioso); toasts con tipos inexistentes `'success'`/`'warn'` sin color (`app.css:646-648`); export HTML con `var(--c-*)` sin definir fuera de la app (`esde.js:1372`); patch list no auto-escanea y su 📂 abre selector de carpetas para elegir una ROM | UX | S | ✅ catch de `loadTools()` muestra error explícito; `.toast.warn` con color propio (`app.css`); único `showToast(...,'success')` normalizado a `'ok'`; `loadPatchList()` añadida a la carga de la pestaña; nuevo `GET /api/browse-file` (selector de archivo real, no de carpeta) + `browseFile()`, 4 tests nuevos |

---

### FORMATOS-UX — Auditoría de la pestaña Formatos: UX/UI (2026-07-13)

Auditoría de la pestaña Formatos (`tab-formats.html` + JS repartido en
`tools.js`, `esde.js`, `config.js`, `duplicates.js`). A diferencia de
Herramientas, aquí casi todos los botones sí están conectados; los problemas
son un panel-stub ("Análisis de carpeta"), el selector de contexto
PC/Android pisando rutas de esta pestaña sin avisar en cada apertura, y
diálogos nativos (`alert`/`confirm`) en vez de los componentes propios de la
app. Detalle, archivo:línea y fases en
`Tareas/diario/archivo/Roadmap-Formatos-UX-completado.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| FORMATOS-UX-1 | **Selector de contexto pisa rutas sin avisar** — `setToolsContext` (`duplicates.js:345-367`) sobrescribe incondicionalmente `zip-path`/`chd-path`/`folder-analysis-path` cada vez que se abre Formatos o Herramientas (`main.js:485-486`), rellena el ID muerto `health-path` y deja huérfanos `cso-path`/`verify-chd-path`/`m3u-path`. Relacionado con HERR-UX-7 (misma función). Fix: solo rellenar si está vacío + cubrir todos los paths | Bug | S | ✅ rama `feature/formatos-ux` — importa `_setIfEmpty` (ya exportado de `config.js`) en vez del overwrite incondicional; lista de IDs ampliada a `cso-path`/`verify-chd-path`/`m3u-path` y `health-path` (ID muerto, no existe en ningún partial) eliminado |
| FORMATOS-UX-2 | **"Análisis de carpeta" es un panel-stub** — `doFolderAnalysis` (`esde.js:1120-1131`) ignora la ruta y siempre renderiza «Funcionalidad pendiente», pese a tener input, botón y persistencia completos (`tab-formats.html:192-204`). Mismo patrón que HERR-UX-2. Fix: implementar `/api/folder-analysis` o retirar el panel | Bug | M | ✅ rama `feature/formatos-ux` — implementado (decisión del usuario: implementar, no retirar). Nuevo endpoint `POST /api/folder-analysis` (`web/handlers/esde/conversions.py`) reutilizando `find_cue_files`+`validate_cue` (sets PSX incompletos) y `scan_n64_roms` (ROMs N64 pendientes de convertir), más conteo de extensiones y `.cso`/`.zip` sueltos. Frontend reescrito con 3 bloques `<details>`. 6 tests nuevos (`tests/test_folder_analysis.py`), verificado también con curl contra el servidor real |
| FORMATOS-UX-3 | **`alert()`/`confirm()` nativos en 9+ sitios** — `doConvertChd/doConvertCso/doExtractZip/doCleanupZips/doCleanupCueBin/doGenerateM3U/doVerifyMultidisc/doVerifyChd` (`tools.js`) usan diálogos nativos pese a existir `showToast` y `_showConfirm` propios de la app. Fix: sustituir por los componentes propios | UX | S | ✅ rama `feature/formatos-ux` — 8 `alert()` de validación → `showToast(..., 'err')`; 2 `confirm()` destructivos (`doCleanupZips`/`doCleanupCueBin`) → `_showConfirm` con el cuerpo de la petición movido al callback. `organizeLibrary` (mismo archivo) queda fuera de alcance — no pertenece a Formatos |
| FORMATOS-UX-4 | **Botón "library_root" muestra el nombre de la variable interna** — literal en inglés/snake_case en 5 paneles (`tab-formats.html:16,58,88,148,198`) en vez de una etiqueta legible en español | UX | XS | ✅ rama `feature/formatos-ux` — texto cambiado a "Usar biblioteca" con tooltip, en los 5 sitios |
| FORMATOS-UX-5 | **Escaneos síncronos sin bloqueo de botón** — "Generar M3U", "Verificar" (multi-disco), "Escanear" (N64) y "Generar .lpl" no deshabilitan su botón durante el fetch, a diferencia de CHD/CSO/ZIP (jobs con polling) y de `autodetectM3UFolders`, que sí lo hace bien | UX | S | ✅ rama `feature/formatos-ux` — los 4 botones ahora se deshabilitan + cambian texto durante la llamada, mismo patrón que `autodetectM3UFolders` |
| FORMATOS-UX-6 | **Filtro "solo errores" con default distinto entre paneles gemelos** — CHD conversión: marcado solo si hay fallos; CHD verificación: siempre marcado (`tab-formats.html:75` vs `tools.js:76-78`) | UX | XS | ✅ rama `feature/formatos-ux` — quitado el `checked` estático; `_renderVerifyChdResult` fija `checked = result.failed > 0`, igual que `_renderChdResult` |
| FORMATOS-UX-7 | **Pulido: mensajes de error sin guía, resultados vacíos sin sugerencia, botón "library_root" silencioso en fallo, persistencia de rutas incompleta** — `doConvertChd/doConvertCso/doExtractZip/doVerifyChd` sin pista accionable en el catch (a diferencia de los cleanup); "sin resultados" en M3U/N64 sin sugerir revisar ruta o nomenclatura; `fillToolPath` traga errores en silencio (`config.js:406-411`); `_initToolPath` no cubre `cso-path/verify-chd-path/verify-multidisc-path/lpl-output-dir/n64-path` (`config.js:295-301`) | UX | S | ✅ rama `feature/formatos-ux` — pista añadida a los 4 catches; sugerencia añadida a los 2 mensajes vacíos; `fillToolPath` ahora muestra toast de error; `_initToolPath` cubre los 5 campos que faltaban |

---

### PSX-FIX — Hallazgos en `psx/` (PC + Anbernic RG556), investigación 2026-08-27

Origen: usuario pidió revisar por qué hay "muchos archivos para un mismo
juego" en la carpeta PSX. Limpieza de los 2 duplicados confirmados (ver abajo)
ya aplicada manualmente en PC y en el Anbernic (vía ADB — el dispositivo no
aparece como unidad `H:\`, hay que usar `tools/adb.exe`, ROMs en
`/storage/521D-04EA/ROMs/psx`). El resto queda documentado para decidir.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| PSX-FIX-1 | **`convert_directory()` en dry_run no valida que los `.bin` referenciados existan** — a diferencia de `convert_to_chd()` (que sí falla con "Bin file(s) not found" antes de llamar a chdman), la rama `dry_run` de `convert_directory` (`converters/chd_converter.py:231-249`) solo comprueba `chd_path.exists()` y marca "CONVERTIBLE" cualquier `.cue` sin `.chd`, aunque sus `.bin` no existan. Esto hizo que 4 `.cue` rotos (ver PSX-FIX-2) se reportaran como convertibles en el dry-run y solo fallaran al intentar la conversión real. | `converters/chd_converter.py` | ✅ rama `fix/psx-fix-1-chd-dryrun-bin-check` (worktree) — misma comprobación de `bin_paths` faltantes que ya tenía `convert_to_chd`, ahora también en el dry_run. 1 test nuevo de regresión. 1016/1019 pasan (3 fallos preexistentes no relacionados: tests que esperan "sin dispositivo Android" y la Anbernic está conectada de verdad en esta sesión). Pendiente de push + PR a `develop` |
| PSX-FIX-2 | **4 `.cue` huérfanos/rotos apuntan a pistas que no existen** — `WipEout 3 (USA).cue`, `Tomb Raider (World) (53510802) (Addon).cue`, `Tomb Raider II - Starring Lara Croft (Europe).cue` y `Street Fighter Collection (USA) (Disc 1).cue` referencian archivos `(Track NN).bin` (14/57/61/72 pistas resp.) de un dump distinto al que hay en disco — lo que hay realmente son `.bin` sueltos de otras revisiones (`Rev 6`, `Rev 2/3`, `v1.6`, `v1.1) (Track 01)` suelto). No son juegos multi-track reales en esta biblioteca; son restos de un `.cue` descargado sin su set de pistas correspondiente. | `E:\Carpetas anbernic\psx\` | ✅ movidos a `_descartados/` con `discard_to_trash()` y purgados (2026-08-27) |
| PSX-FIX-3 | **`Mortal Kombat 3 (Europe)` — dump multi-track muy incompleto, sin `.cue`** — 11 archivos `(Track NN).bin` con numeración muy dispersa (04,12,15,16,23,24,25,30,51,58,59 de un juego con más de 60 pistas de audio) + 1 `.bin` base, y ningún `.cue`. No se puede reconstruir de forma fiable sin conocer el orden/tipo exacto de cada pista — necesitaría redescargar el set completo (redump) si se quiere en el futuro. | `E:\Carpetas anbernic\psx\` | ✅ movidos a `_descartados/` con `discard_to_trash()` y purgados (2026-08-27) |
| PSX-FIX-4 | **Duplicado adicional de `Digimon Rumble Arena (Europe)` en el Anbernic, fuera del ya limpiado** — además de la copia dentro de `Digimon Rumble Arena [SLUS-01404] [bin]/` (cue+bin ya borrados, `.chd` verificado conservado), había una copia completa suelta en la raíz de `ROMs/psx/` (`.bin` 266.827.344 B + `.chd` 175.041.579 B, tamaños idénticos a la copia de la subcarpeta) — ~440 MB duplicados sin motivo aparente. | Anbernic `/storage/521D-04EA/ROMs/psx/` | ✅ decisión del usuario: conservar la copia de la raíz, subcarpeta `[SLUS-01404] [bin]/` eliminada por completo vía `adb shell rm -rf` (2026-08-27) |

**Ya aplicado (2026-08-27):** `Digimon Rumble Arena (Europe) (En,Fr,De,Es,It)` y
`Megaman - Battle & Chase (Europe)` tenían `.cue`+`.bin` originales sin borrar
tras una conversión a `.chd` ya hecha (`delete_source` no se usó en su momento).
Verificados ambos `.chd` con `chdman verify` (OK) y confirmado que la copia del
Anbernic es idéntica (mismo tamaño/fecha) antes de borrar el `.cue`+`.bin`
sobrante en PC y en el dispositivo.

**Papelera `_descartados/` (AUD-3, `utils/trash.py`) vaciada manualmente
(2026-08-27):** al revisar el espacio ocupado por juego se detectaron 31
carpetas `_descartados/` (una por plataforma + inbox + Unknown) sumando 23,64 GB
en el PC — comportamiento por diseño (soft-trash con purga automática a los
`library.trash_purge_days` días, default 30, vía daemon en `web/daemons.py`),
no un bug. El 100% de los archivos tenía menos de 30 días (grueso del
2026-08-14, presumiblemente de una limpieza masiva anterior), así que el
purgado automático todavía no aplicaba a nada. El usuario decidió saltarse la
ventana de seguridad y vaciar ya con `purge_trash(older_than_days=0)`:
**5.920 archivos, 22,44 GB liberados** (incluye los archivos de PSX-FIX-2/3
recién descartados). La papelera del Anbernic también se purgó por completo el
mismo día (vía `adb shell rm -rf` por carpeta, 43 carpetas top-level, 0
restantes tras la purga): **1,77 GB liberados**.

### TRASH-FIX-1 — `_descartados/` se anida hasta 7 niveles en el Anbernic (hallado al purgar, 2026-08-27)

Al listar las carpetas `_descartados/` del Anbernic antes de purgar aparecieron
cadenas anidadas tipo `_descartados/_descartados/_descartados/...` (hasta 7
niveles en `megadrive/`, 6 en `gb/GB official game ROM complete works/*/` y
`snes/`) — patrón que **no existe en el PC** (allí cada plataforma tiene un único
nivel `_descartados/`, tal como diseña `utils/trash.py`). El propio
`_iter_trash_files()` (`utils/trash.py:64-68`) ya evita este problema al leer
(`dirnames[:] = []` — no desciende dentro de un `_descartados` encontrado), así
que no es un bug de lectura; el anidamiento ya existe físicamente en el
dispositivo. Hipótesis más probable: el mecanismo que copia/organiza ROMs hacia
el Anbernic trata `_descartados/` como una carpeta de juegos más y la copia
entera dentro del `_descartados/` de destino en cada sincronización repetida,
añadiendo un nivel cada vez — el número de niveles por plataforma (7 en
`megadrive`, que es de las más sincronizadas; 1-2 en plataformas tocadas menos)
encaja con "una vez por sync". | `sync/cable_engine.py` (motor compartido),
`web/handlers/sync_cable.py`, `web/cable_sync_daemon.py` | ✅ PR [#244](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/244) — causa raíz: `iter_files()` en `cable_engine.py` solo saltaba dotfiles, no `_descartados/`; mismo gap corregido en los dos walkers ad-hoc que quedan fuera del motor compartido. 2 tests nuevos

### JUEGOS-FIX-1 — Vista de galería (grid) de la pestaña Juegos no renderiza tarjetas (hallado en vivo, 2026-08-27)

Al cambiar a vista de galería en Juegos (icono junto a CSV/JSON) con un
filtro activo ("Mario", 157 resultados), el contador de resultados es
correcto pero el área de tarjetas queda vacía (solo un emoji 🎮 centrado, sin
scroll ni error en consola visible). La vista de lista (tabla) sí funciona
con el mismo filtro. No investigado a fondo — candidatos: `games.js`/`main.js`
(`_renderGrid`/equivalente) no se dispara al cambiar de vista con un filtro ya
aplicado, o depende de datos (carátulas) que estas 157 entradas no tienen.
Pendiente de investigar causa raíz (`archivo:línea`) antes de arreglar. | `web/static/js/tabs/games.js`, `web/static/js/main.js` | ✅ PR [#243](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/243) — causa raíz doble: (1) `.games-grid` sin regla base `display:grid` en `app.css` (solo overrides `@media`), cada `.game-card` caía a ~1200px de alto apiladas; (2) bug separado y más grave: `onclick="openGamePanel(${JSON.stringify(g)...})"` en 6 sitios (galería, tabla, búsqueda global, recientes) solo escapaba `<`/`>`, nunca `"` — el primer `"` de `JSON.stringify` cerraba el atributo, dejando JS inválido. Abrir el panel de detalle estaba roto en toda la app, no solo en la galería. Fix: regla `display:grid` + reutilizar `_h()` (ya escapa comillas) en vez del `.replace` ad-hoc. Verificado en navegador con la biblioteca real

### CLOUD-FIX-1 — Error JS "badge is not defined" filtra al usuario en la pestaña Cloud (hallado en vivo, 2026-08-27)

Al abrir Cloud con Dropbox conectado pero sin remote de sync guardado
todavía, aparece una caja roja con el texto literal `badge is not defined —
Comprueba la configuración cloud de esta pestaña (rclone instalado y remote
conectado).` — es un `ReferenceError` de JS (variable `badge` no definida)
capturado por un `catch` genérico y mostrado como si fuera un mensaje de
validación normal, no un fallo del propio código. No investigado a fondo —
buscar el `catch` que arma ese mensaje y la variable `badge` sin declarar en
el flujo de estado de Cloud. | `web/static/js/tabs/sync.js` (o el módulo de
Cloud equivalente) | ✅ PR [#243](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/243) — causa raíz: `sync.js` llama a `badge()` esperando un helper global, pero `games.js` lo define sin `export` (módulos ES, scope propio por archivo). Fix: exportar `badge()` desde `games.js` e importarlo en `sync.js`, mismo patrón ya usado con `_platBadge`. Verificado en navegador: el log de sync ahora renderiza la tabla de 200 eventos con badges en vez del error

### SYNC-FIX-2 — Auto-sync ya no crashea (SYNC-FIX-1) pero reporta "15 errores" reales (hallado en vivo, 2026-08-27)

Tras aplicar SYNC-FIX-1 y reiniciar el servidor, el primer auto-sync que
corrió sin crashear terminó igualmente con `Ultimo sync: ... | Error: 15
errores` (visible en Cable Sync). Distinto del bug de aridad: ahora el daemon
sí se ejecuta y sí llega a intentar copiar/comparar archivos, pero algo falla
15 veces durante esa sincronización real. No investigado — el detalle de cada
uno de los 15 errores debería estar en el log de operaciones (botón "Ver log
de operaciones" en Cable Sync) o en `sync_log` (SQLite). | `sync/adb_transport.py` | ✅ PR [#242](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/242) — los 15 errores eran saves de Redream/AetherSX2 bajo `Android/data/<pkg>/` (scoped storage, Android 11+). `push()`: adb escribe el contenido pero el `fchown` final a la UID de la app falla sin root (exit code != 0 aunque el archivo llegó bien) — antes se borraba el `.part` a ciegas, ahora cae al chequeo MD5 existente y solo falla de verdad si el contenido no coincide. `pull()`: `Permission denied` es un bloqueo de lectura real sin margen de recuperación — mensaje ahora explica que es scoped storage, no un fallo transitorio. 4 tests nuevos

### SYNC-FIX-1 — Auto-sync crasheaba en cada intento por aridad incorrecta de `get_repo_fn` (hallado en vivo, 2026-08-27)

Al abrir la interfaz para las capturas del README apareció el banner de error
persistente `start_all.<locals>.<lambda>() takes 0 positional arguments but 1
was given`, visible también en Cable Sync ("Ultimo sync: ... Error: ..."), en
cada intento de auto-sync desde que arrancó el servidor. Prioridad absoluta
por ser bug de sync (regla del proyecto). Causa raíz: `start_all()`
(`web/daemons.py:262`) pasaba `lambda: repository` (0 argumentos) a
`_auto_sync_loop`/`_sd_card_sync_loop`, pero ambos ya esperan el contrato
`get_repo_fn(path)` de 1 argumento (`cable_sync_daemon.py:181,474`) que usa el
resto de la app (`web/builders/common.py::_repo_for_path`) para elegir la BD
correcta (PC vs Anbernic) — desajuste introducido en algún refactor de
multi-dispositivo que no llegó a `start_all()`/`serve()`. | `web/daemons.py`,
`web/server.py` | ✅ PR [#241](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/241) — rama `fix/auto-sync-daemon-get-repo-fn-arity` (worktree). `start_all()` recibe ahora `repository_android` y construye el mismo `get_repo_fn` de 1 argumento que `make_handler()`. 1 test nuevo de regresión (`test_daemons_start_all.py`). 1016/1019 pasan (3 fallos preexistentes no relacionados)

---

---

### JUEGOS-UX — Roadmap: logros por juego + playtime automático (2026-07-13)

Roadmap de feature nueva (no auditoría de bugs) para la pestaña Juegos.
Verificado en código: el resumen de logros (`X/Y logros`) ya existe vía
`/api/ra-user-progress`, pero RA devuelve la lista completa de logros
individuales y el backend la descarta (`games.py:507-514`) — nunca se
guardó ni parseó en ningún punto de `retroachievements/`. Y el control de
"Tiempo jugado" del panel de juego (`gp-playtime-wrap`) es una simulación
total: `gpLogPlaytime()` (`games.js:531-542`) no llama a ninguna API, solo
hace `alert()` y limpia los campos — no hay columna de minutos en la BD
(`play_history.py` solo tiene `play_count`/`last_played_at`). Detalle,
archivo:línea y fases en `Tareas/diario/archivo/Roadmap-Juegos-UX-completado.md`.
Sustituye/desarrolla `MEJ-1`. **Completado** — ver JUEGOS-UX-1..9 arriba.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| JUEGOS-UX-1 | **Backend: exponer logros individuales** — `/api/ra-user-progress` (`games.py:461-516`) ya recibe el array `Achievements` de RA (título, descripción, puntos, badge, fecha de desbloqueo) y lo descarta; añadirlo a la respuesta manteniendo el cache 1h existente | Feature | S | ✅ `games.py:486-514` construye el array `achievements` completo y lo incluye en la respuesta |
| JUEGOS-UX-2 | **Frontend: lista de logros desbloqueados/pendientes en el panel de juego** — nuevo bloque bajo `gp-ra-user-progress` (`_foot.html:138`), reutilizando el patrón de lista colapsable ya usado en `tools.js:444` (`_faCollapsibleList`) | Feature | M | ✅ `_foot.html:139-140` (`#gp-ra-achievements`) + `games.js:722` (`_gpRenderAchievements`) |
| JUEGOS-UX-3 | **Perf: lazy-load de iconos de logros** — `loading="lazy"` en los badges; reutilizar el patrón TTL de `.rommgr/ra_cache/` en vez de un cache nuevo | Feature | XS | ✅ `games.js:696` — `loading="lazy"` en los `<img>` de badges |
| JUEGOS-UX-4 | **🔴 El control manual de playtime no guarda nada** — `gpLogPlaytime()` solo hace `alert()`, sin `apiPost` (`games.js:531-542`); ocultarlo o marcarlo como no persistente hasta que exista el tracking automático | Bug | XS | ✅ `gpLogPlaytime()` ya no existe — sustituido por `gpShowPlaytimeInfo()` (JUEGOS-UX-8), sin input manual |
| JUEGOS-UX-5 | **Esquema de datos: minutos separados por origen (PC/Android)** — `playtime_minutes_pc` + `playtime_minutes_android` en vez de un total único, para poder sumar sin duplicar ni sobrescribir al sincronizar | Feature | S | ✅ `schema.py:59-60,222-223` — columnas `playtime_minutes_pc`/`playtime_minutes_android` |
| JUEGOS-UX-6 | **Scanner `.lrtl` de RetroArch (PC)** — módulo stdlib-json sobre `playlists/logs/<Core>/<rom>.lrtl`, mismo matching que `record_play_session` (`play_history.py:26-27`), como job de background con polling | Feature | M | ✅ `utils/lrtl_scanner.py`, invocado desde `games.py`/`play_history.py` |
| JUEGOS-UX-7 | **Sync de `.lrtl` desde Anbernic** — nuevo `SyncSource` (mismo patrón que MEJ-4 para `.cht`); los `.lrtl` de Android acumulan en `playtime_minutes_android`, nunca sobrescriben `_pc` | Feature | S | ✅ `sync_cloud.py:301-322,530-543,756-764` — `SyncSource` de `.lrtl` con `ingest_lrtl_dir` por origen |
| JUEGOS-UX-8 | **UI: total automático PC+Anbernic sin inputs** — sustituir `gp-playtime-wrap` (`_foot.html:163-175`) por "X h Y m totales · PC: A h · Anbernic: B h", recalculado solo tras cada sync/scan | Feature | S | ✅ `games.js:524-547` (`gpShowPlaytimeInfo`) — total automático sin inputs |
| JUEGOS-UX-9 | **No aparentar precisión mientras el scanner no esté completo** — indicar en la UI si el dato es parcial (solo PC, sin datos de Anbernic aún) | UX | XS | ✅ `games.js:540-541` — "PC: sin datos"/"Consola: sin datos" cuando falta un origen |

---

---

### VAL-FIX — Hallazgos de la validación con consola real (2026-07-13)

Origen: validación V-AUD-1/V-AUD-2 y smoke DEVSEL con la RG556 por USB (Día42,
sección "Continuación 2026-07-13"). AUD-1 y AUD-2 **validadas** con hardware:
Sync Doctor OK (desviación −1,9 s), sync por cable con 373 copiados / 0 errores
(~338 saves verificados MD5), sin `.part` residuales. Los fallos de abajo
salieron durante esa validación. Orden: 1→2 rompen borrado de duplicados y
papelera — prioridad alta.

| ID | Task | Pilar | Esfuerzo | Estado |
|----|------|-------|----------|--------|
| VAL-FIX-1 | **El scanner no excluye `_descartados/` ni `$RECYCLE.BIN`** — `scanner/rom_scanner.py` no tiene ninguna exclusión de directorios: la papelera de AUD-3 se re-indexa en cada scan (937 filas `_descartados\...` ya en la BD PC, 7-8 filas `$RECYCLE.BIN` en cada BD). Rompe el borrado de duplicados: "eliminar" mueve a `_descartados/`, el siguiente scan lo re-añade y el duplicado reaparece. Fix: excluir `_descartados`, `$RECYCLE.BIN` y `System Volume Information` en el walk del scanner + purga one-shot de las filas existentes | Seguridad | S | ✅ rama `fix/val-tabs-duplicados-fantasma` (PR #147) — `_is_excluded()` en `rom_scanner.py` excluye `TRASH_DIR_NAME`/`$RECYCLE.BIN`/`System Volume Information`. **Purga real ejecutada 2026-07-20** (backup previo en `.rommgr/backup_valfix_2026-07-20/`): `rommgr scan --quick` sobre la biblioteca real prunó las 220 filas `_descartados` existentes vía `prune_stale_entries` (ya no entran en `seen_paths`) → 0 tras el scan |
| VAL-FIX-2 | **`library_android.db` contaminada con filas del PC** — 13.164 de 13.376 filas tienen rutas `E:\` (solo 211 son de la SD `H:\`); 6.958 rutas están en AMBAS BDs; 100 % unmatched (el match nunca corrió ahí). Consecuencias: duplicados fantasma imposibles de borrar (la vista empareja el mismo archivo físico consigo mismo y el delete enruta por ruta `E:\` → siempre a la BD PC, la fila Android sobrevive) y acciones de FIX-2 no-op sobre filas contaminadas (la estrella "muerta" del smoke test — el código DEVSEL-FIX-2 funciona, verificado por API con un juego real `H:\`). Fix: (a) limpieza con backup previo — borrar de la BD android las filas cuya ruta no sea de consola (`NOT LIKE 'H:%'` y `NOT LIKE '/storage%'`); (b) investigar el origen (¿la migración V2 copió todo?); (c) guard de dominio al escribir: la BD android solo acepta rutas bajo `anbernic_root`/`/storage` | Seguridad | M | ✅ rama `fix/val-tabs-duplicados-fantasma` (PR #147) — **(b) causa raíz encontrada**: `_do_migrate_split_db` (`sync_cloud.py`) clasificaba con `not source_path.startswith(lib_root)` — heurística negativa, migraba cualquier fila de PC fuera de `library_root` aunque fuera válida. **(c) fix aplicado**: clasificación ahora por `is_device_path()` (pertenencia a `anbernic_root` o ruta POSIX estilo ADB, `utils/paths.py`). **(a) purga**: `library_android.db` real tenía 0 filas en el momento del fix (verificado) — nada que limpiar hoy; el fix de código evita que la contaminación original vuelva a producirse si se repite la migración |
| VAL-FIX-3 | **Rutas relativas de tools con `/` rompen `subprocess` en Windows** — `CreateProcess` no acepta `tools/adb.exe` (WinError 2 → "consola no conectada" con la consola conectada); sí acepta `tools\adb.exe` o `./tools/adb.exe`. El comentario de `config.py:305` sugiere justo la forma mala. Fix de raíz: normalizar a ruta absoluta contra `project_root` en `load_config()` (`config.py:427-429`, cubre adb/chdman/rclone de golpe). El `config.toml` local ya está parcheado a mano (`tools\\adb.exe`) | Sync | S | ✅ `_resolve_tool_path()` (`config.py`) — reemplaza `/` por `\` en Windows para adb/chdman/rclone leídos de `config.toml` (no-op en bare commands tipo `"rclone"` ni en no-Windows). Se descartó normalizar a absoluto contra `project_root` (lo que sugería el hallazgo original): la CI corre en `ubuntu-latest` donde `Path.resolve()` sobre rutas con letra de unidad (`C:/...`) no se comporta igual que en Windows real — el fix mínimo (solo separador) es portable y resuelve el WinError 2 real. 2 tests nuevos |
| VAL-FIX-4 | **Auto-sync: 96 `Permission denied` en memcards de DuckStation** — `Android/data/com.github.stenzek.duckstation/` no es accesible por ADB en Android 11+ sin root (scoped storage); el auto-sync lo reintenta en cada conexión (ya fallaba en marzo con 49). Sin pérdida: los pulls fallan y nada se sobreescribe. Fix: excluir/avisar ese mapping en modo ADB y documentar la alternativa (DuckStation Android → exportar memcards a carpeta pública) en `docs/emulator-compat.md` | Sync | S | ✅ `accessible: False` en el mapping de DuckStation (`config.py`, mismo patrón ya usado por Dolphin) — `get_adb_sync_sources()` lo excluye, cero reintentos. `notes` explica el workaround (cambiar Memory Cards → Directory a carpeta pública en DuckStation). Se evaluó `run-as` (sandbox sin root) y quedó descartado: solo funciona si la build es debuggable, no aplica al DuckStation de Play Store. `docs/emulator-compat.md` actualizado (tabla PS1 + resumen rápido). 1 test nuevo en `test_config.py` |
| VAL-FIX-5 | **Preview del sync por cable hardcodea "no accesible en modo ADB"** — `_build_cable_sync_preview` (`web/builders/misc.py:81`) nunca implementó el conteo remoto por ADB; el Sync Doctor de AUD-1 ya lo hace bien (226 saves). Fix: reutilizar ese conteo o esconder el preview en modo ADB | UX | S | ✅ `_build_cable_sync_preview` reutiliza `AdbTransport.ls_recursive()` (mismo método que Sync Doctor) cuando `mode == "adb"` y hay `serial`; sin serial muestra "conecta el dispositivo primero", con error de transporte muestra el mensaje. Frontend (`sync.js`, `loadCableSyncPreview`) manda `serial` (`#cable-adb-device`) y `android_path` (`#auto-sync-android-path`) en modo ADB. 3 tests nuevos (`tests/test_cable_sync_preview.py`) |
| VAL-FIX-6 | **El aviso de ruta SD/MTP se muestra en modo ADB** — al cargar la pestaña, `testCablePath('ab')` valida el campo de ruta SD aunque el Modo ADB esté activo (aviso "Este equipo\RG556\... NO es compatible" irrelevante en ADB). Fix: no validar/ocultar los avisos de la sección SD cuando `_isAdbMode()` (`sync.js:795-796`) | UX | S | ✅ `loadCableSync()` (`sync.js`) — causa raíz real: la auto-selección de modo (ADB vs SD) corría *después* de testear la ruta SD, así que `_isAdbMode()` aún reflejaba el radio por defecto. Reordenado: decidir el modo primero, testear rutas después; `testCablePath('ab')` ahora se salta por completo si el modo final es ADB |
| VAL-FIX-7 | **El sync por cable no registra en `save_sync_log`** — solo `SaveSyncer` (sync cloud) escribe esa tabla; el job de cable verifica MD5 en el transporte (`handlers/sync_cable.py:394,425`, solo saves) pero no deja rastro por archivo, así que el "último sync por juego" del Sync Doctor no refleja syncs por cable. Fix: llamar `log_sync_event(..., verified=)` también desde el job de cable (valor bajo, el resultado del job ya reporta) | Sync | S | ✅ el registro en `save_sync_log` ya existía desde REV43-33 (PR #153); lo que faltaba era `verified=`. `_sql_log()` (`handlers/sync_cable.py`) gana el parámetro; en `_adb_copy_to_pc`/`_adb_copy_to_device`, llegar a la línea "ok" implica que `pull()`/`push()` con `verify=True` ya comprobó el MD5 (un mismatch lanza `OSError` antes) — se pasa `verified=True` cuando el archivo era save, `None` cuando no aplicaba verificación. 1 test nuevo (`test_cable_sync_adb_verified_log.py`) |

---

---

### STORAGE-MGR — Gestor de almacenamiento (diseño e implementación 2026-08-14)

Origen: idea del usuario (`ROADMAP-IDEAS`) — vista combinada PC↔Android y
borrado en bloque desde un menú dedicado, siempre pasando por papelera.

**Decisiones tomadas con el usuario antes de diseñar:**

1. **Sin papelera en Android** — el borrado ADB de hoy (`AdbTransport.remove()`)
   es `rm -f` directo, sin equivalente a `_descartados/`. Se decidió NO añadir
   una papelera en el dispositivo (coste: ocuparía SD hasta purgar). Consecuencia
   de diseño: el modal de confirmación distingue explícitamente qué entra en
   papelera (PC, deshacible) de qué se borra sin vuelta atrás (Android) — nunca
   la misma advertencia genérica para ambos.
2. **Saves fuera de alcance** — v1 cubre solo ROMs (y de paso assets, mismo
   mecanismo). Los saves son el pilar de mayor riesgo del proyecto (ver
   CLAUDE.md — "cualquier bug aquí es prioridad absoluta"); no entran en un
   borrado masivo genérico.

Reutiliza infraestructura existente sin pestaña nueva: el panel "Comparar" de
Colección (`_build_library_diff()`, `web/builders/diff.py`) ya tenía la vista
combinada PC↔Android por SHA1 y el multi-select; `discard_to_trash()` (PC) y
`AdbTransport.remove()` (Android) ya existían como precedente de branching por
`is_device_path()` en `duplicates_service.delete_duplicate()`.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| STORAGE-MGR-1 | Backend: `size_bytes` por entrada en `_build_library_diff()` | `web/builders/diff.py` | ✅ |
| STORAGE-MGR-2 | Backend: resumen combinado PC/Android por plataforma (`total_pc_bytes`/`total_android_bytes`) | `web/builders/diff.py` | ✅ |
| STORAGE-MGR-3 | Backend: `delete_storage_items()` — borrado en bloque keyed por `(sha1, location)` (mismo shape que `/api/sync-roms`); PC → `discard_to_trash` (deshacible), Android → `AdbTransport.remove` (hard delete, decisión tomada con el usuario); `POST /api/storage/delete-bulk` | `services/storage_service.py` (nuevo), `web/handlers/collection.py` | ✅ |
| STORAGE-MGR-4 | Frontend: botón "Borrar seleccionados" en el panel "Comparar", junto al ya existente "Sincronizar seleccionados" — mismas checkboxes; confirm con nota de papelera para PC y nota de irreversibilidad separada para Android cuando la selección mezcla ambos lados | `web/static/js/tabs/collection.js`, `web/static/partials/tab-collection.html` | ✅ |
| STORAGE-MGR-5 | Frontend: cabecera con tamaño PC/Android junto a los conteos existentes | `web/static/js/tabs/collection.js` | ✅ |

Tests: `test_storage_service.py` (bulk delete, PC/Android no se cruzan, sha1
desconocido, sin transporte ADB) + `test_library_diff.py` (`size_bytes` en el
diff). **Validado contra hardware real 2026-08-29**: archivo `.gba`
desechable subido a `/storage/521D-04EA/_storage_mgr_validation/` en la
RG556 conectada, borrado con el código real (`delete_storage_items` +
`resolve_single_device_transport` + `AdbTransport.remove`) contra una BD
temporal (no la real), confirmado ausente por un segundo `adb shell`
independiente tras el borrado, carpeta de prueba limpiada — sin tocar la
biblioteca real de la consola. `POST /api/storage/delete-bulk` puede usarse
con confianza para un borrado real desde Android.

---

---

### MEJORAS — Propuestas 2026-07-02 (ordenadas por valor/esfuerzo)

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MEJ-1 | **Playtime real desde logs `.lrtl` de RetroArch** — scanner stdlib-json de `playlists/logs/<Core>/<rom>.lrtl` (`runtime` + `last_played`) que puebla `play_history`; elimina la entrada manual de horas (confirmado: `gpLogPlaytime()` hoy no persiste nada, solo hace `alert()`, `games.js:531-542`). Fase 2: sync de los `.lrtl` de Android (mismo pipeline que saves) → playtime unificado PC+consola. Alimenta el recomendador NLP. Diseño detallado en `Tareas/Roadmap-Juegos-UX.md` (JUEGOS-UX-4..9) | `scanner/` (nuevo módulo), `database/repositories/play_history.py`, endpoint | ✅ rama `feature/juegos-ux` — scanner `utils/lrtl_scanner.py`, columnas por origen `playtime_minutes_pc/_android`, endpoint `/api/playtime-scan` (job, PC + pull adb), UI automática sin inputs manuales. Pata cloud (rama `feature/juegos-ux-7-cloud`): `sync.playtime_remote` + SyncSources `/pc` y `/android` + ingesta post-sync + subida de `.lrtl` en el script Termux |
| MEJ-2 | **Deshacer último apply** — endpoint que invierte los renames de la última operación usando `file_operations` (ya registrado en SQLite); reutiliza `rename_rom_with_saves` en dirección inversa. | `planner/`, `web/handlers/` | ✅ `get_last_apply_batch()` (`database/repositories/games.py`) agrupa por el `created_at` compartido del último apply; `_do_undo_last_apply()` (`web/handlers/organize.py`) reproduce la misma rama cue/gdi vs archivo suelto que `_do_apply`, pero con `source`/`target` invertidos, y llama `apply_rename()` con las rutas invertidas — cada undo queda registrado como una fila nueva, así que un segundo undo revierte el undo (redo) en vez de no hacer nada. Backup de la BD (MEJ-3) antes de tocar nada. Job en background (`undo_apply` en `JOB_NAMES`, endpoints `POST /api/undo-last-apply` + `GET /api/undo-last-apply-status`, patrón moderno `job_manager.get_job()` sin tocar el `get_status()` compartido). Botón "Deshacer último apply" en Organizar (`organize.js`, `tab-plan.html`). 2 tests nuevos (`test_undo_last_apply.py`) |
| MEJ-3 | **Backup automático de la DB antes de apply/migraciones** — `sqlite3.Connection.backup()` (stdlib, ~5 líneas) antes de cada apply. | `planner/operation_planner.py` o `database/repository.py` | ✅ `backup_database()` en `_RepositoryBase` (`database/repositories/base.py`) — snapshot vía `sqlite3.Connection.backup()` (seguro con WAL, a diferencia de una copia de archivo cruda) a `<data_dir>/db-backup/`, poda a `keep_n=5`. Llamado desde `_do_apply` (`web/handlers/organize.py`) y `cli.py apply`, antes de construir el plan. 2 tests nuevos en `test_repository.py` |
| MEJ-4 | **Sync de cheats (`.cht`)** — un `SyncSource` más apuntando al dir `cheats/` de RetroArch, mismo patrón que NEW-8 (`.opt`). ~10 líneas. | `config.py`, `sync/sync_cloud.py` | ✅ mismo patrón dir+remote que `ra_config_dir`/`ra_config_remote`: campos `cheats_dir`/`cheats_remote` en `SyncConfig` (`config.py`), `_do_sync` (`sync_cloud.py`) añade el `SyncSource` "RetroArch Cheats (.cht)" cuando ambos están configurados. Wiring completo: `allowed` en `_save_config` (`web/handlers/config.py`), `_build_config` (`misc.py`), campos nuevos en Ajustes (`tab-settings.html`, `config.js`). 2 tests nuevos (917 en total) |
| MEJ-5 | **"¿A qué juego hoy?"** — botón en Overview: `random.choices` ponderado por status Pendiente + rating + no jugado recientemente. Recomendador v0 mientras no exista el modelo NLP. | `web/handlers/`, `tab-overview.html` | ✅ ya existía la tarjeta "Juego sugerido" (S36-4) pero con selección uniforme entre "no tocado en 6 meses" (sin ponderar por Pendiente/rating) y el botón "Abrir" estaba roto de raíz (`onclick="openGamePanel(window._currentGameSuggestion)"` — esa variable nunca se asignaba a `window`, solo al scope del módulo). Reemplazada la selección por `GET /api/suggest-game` → `services/recommend_service.py::pick_game_for_today()` (peso = 3x si Pendiente/sin tocar · `1+rating` · hasta 3x cuanto más tiempo sin jugar, tope a los 90 días) sobre `repository.get_recommendation_candidates()` (excluye completados/100%). "Abrir" corregido: pide `/api/game?id=` y llama `openGamePanel()` con el objeto completo. Verificado en navegador con la biblioteca real (sugerencia + reroll + Abrir abren el panel correcto). 4 tests nuevos en `test_recommend_service.py` + 1 en `test_repository.py` |
| MEJ-6 | **UI del junk-scan (tarea 2i-1)** — el endpoint `POST /api/junk-scan` fue restaurado (PR #80, se perdió en el refactor `487aa91`) pero el frontend sigue en stubs: `_renderJunkResult`, selección por categoría y borrado vía `/api/junk-delete` son TODOs en `esde.js`. | `web/static/js/tabs/esde.js` | ✅ rama `feature/mej-6-junk-scan-ui` — stubs implementados (render con `<details>`, selección por categoría, borrado con confirm + re-scan); `doJunkScan` corregido (id del contenedor, input `#junk-path`, endpoint síncrono sin job); builder expone `paths` completos por categoría (antes el borrado solo cubría los 50 mostrados). Verificado e2e con servidor real |

> **Orden sugerido:** MEJ-1 → MEJ-2 → MEJ-3 → MEJ-4 → MEJ-5

---

### AUD — Auditoría funcional (2026-07-12)

Funciones nuevas detectadas en auditoría de la app completa. Detalle, archivos
y criterios de "hecho" en `Tareas/diario/archivo/Roadmap-Auditoria.md`
(archivado — 6/6 completadas). Orden: 1→6.

| ID | Task | Pilar | Esfuerzo | Estado |
|----|------|-------|----------|--------|
| AUD-1 | **Sync Doctor** — detectar desviación de reloj PC↔consola (mtime gana → reloj mal = pérdida silenciosa), saves con mtime futuro, saves solo en un lado, último sync por juego | Sync | M | ✅ rama `aud-1-sync-doctor` — pendiente validar con consola real |
| AUD-2 | **Verificación post-transferencia** — hash origen/destino tras cada push/pull (`adb shell md5sum`); si difiere, no propagar y reportar; columna `verified` en `save_sync_log` | Sync | S-M | ✅ rama `aud-2-sync-verify` — pendiente validar con consola real |
| AUD-3 | **Papelera unificada con purga** — todo borrado masivo pasa por `_descartados/` (helper `_discard_file` ya existe); purga >30 días en el health-check daemon; contador+vaciar en Settings. Evita repetir INBOX-FIX-5 | Seguridad | M | ✅ rama `aud-3-papelera-unificada` |
| AUD-4 | **`.md` ambiguos del Inbox por CRC** — los 177 varados: lookup contra `crc_index()` ya existente; hit=Mega Drive, miss=quieto. Formaliza el "ZIP-ROUTE-FIX-4" informal | Inbox | S | ✅ rama `aud-4-md-por-crc` — ejecutar el pipeline sobre el Inbox real para los 177 |
| AUD-5 | **Informe de completitud por plataforma (1G1R)** — cruzar `games` matched vs DATs: "SNES: 412/1.748 (24 %)" + CSV de faltantes | Biblioteca | M | ✅ rama `aud-5-completitud-1g1r` (extendió `/api/collection-completeness` ya existente) |
| AUD-6 | **`chdman verify` en health check** — verificación interna de CHDs, checkbox off por defecto | Biblioteca | S | ✅ rama `aud-6-chdman-verify` |

---

### TEST-CLEAN — Tests que prueban código muerto (auditoría 2026-07-09)

Origen: auditoría de la suite (625 tests / 463 funciones; el resto es
parametrización de funciones puras — sano). Cero skips, todo pasa en ~12 s.
El único problema real: 3 módulos de `src/` sin **ningún** call-site en `src/`
(solo los referencian sus tests), es decir, 29 tests en verde validando código
que la app nunca ejecuta. **Corrección al implementar (2026-07-09)**: la
auditoría solo miró `src/` — `dat_downloader.py` sí tiene consumidor vivo en
`installer/download_dats.py` (build del instalador), así que TEST-CLEAN-1 se
re-alcanzó a solo corregir la doc. Moraleja: buscar consumidores en todo el
repo (installer/, scripts/), no solo en `src/`.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| TEST-CLEAN-1 | ~~Borrar `catalog/dat_downloader.py` + sus 17 tests~~ **Re-alcance: NO borrar** — la auditoría solo buscó consumidores en `src/`; el módulo lo usa `installer/download_dats.py:17` para bundlear DATs en el instalador (PHASE6-2b). Sus 17 tests protegen tooling vivo. Lo que sí era falso: la nota de ARCADE-SETUP-3 mezclaba runtime e installer — corregida. Queda como candidato de consolidación futura: `_run_dat_download` (`web/handlers/scan.py:590`) reimplementa descarga+TTL en runtime; podría importar de `dat_downloader` (refactor, valor bajo). | `catalog/dat_downloader.py` | ✅ (sin borrado — módulo vivo; nota ARCADE-SETUP-3 corregida, rama `chore/test-clean-dead-modules`) |
| TEST-CLEAN-2 | **Borrar `renamer/cue_rewriter.py` + sus 6 tests, y corregir la doc** — la estrategia PSX actual es `move_disc_set_to_subfolder` (`renamer/file_renamer.py:126`): mueve cue+bins a subcarpeta **conservando los nombres de los bins**, así que nunca reescribe el `.cue`. `rewrite_cue` es la estrategia antigua, sin call-sites. Ojo: el Debug Playbook (este archivo) aún decía "Renombrado PSX roto → `cue_rewriter.py`" — pista falsa. | `renamer/cue_rewriter.py`, `tests/test_cue_rewriter.py`, backlog, docs | ✅ módulo+tests borrados; Debug Playbook, `docs/architecture/architecture.md` (árbol + patrón PSX), `docs/glossary.md` y `docs/onboarding.md` actualizados a la estrategia real (rama `chore/test-clean-dead-modules`). `CLAUDE.md` no lo mencionaba |
| TEST-CLEAN-3 | **Borrar `scanner/save_scanner.py`** — sin referencias en `src/` ni tests; los saves los gestiona `sync/`. Código muerto sin más. | `scanner/save_scanner.py` | ✅ borrado + árbol de architecture.md actualizado (rama `chore/test-clean-dead-modules`) |
| TEST-GAP-1 | **`renamer/file_renamer.py` no tiene tests directos** — descubierto al borrar `test_cue_rewriter.py` (el único test "de renombrado PSX" probaba la estrategia muerta). `rename_rom_with_saves` (rename atómico con rollback, patrón crítico de CLAUDE.md) y `move_disc_set_to_subfolder` (sets de disco) solo se ejercitan indirectamente. Añadir tests directos: éxito, rollback ante fallo a mitad, y set cue+bin movido íntegro. | `tests/test_file_renamer.py` (nuevo) | ✅ `tests/test_file_renamer.py` ya existía con buena cobertura de éxito, pero le faltaban exactamente los 2 huecos que nombra la tarea: (1) rollback de `rename_rom_with_saves` cuando falla un save a mitad — nunca se probaba directamente, solo vía el handler de apply; (2) el caso normal de rollback en `move_disc_set_to_subfolder` (ya había un test, pero solo del caso "el rollback en sí falla"). Añadidos: rollback de `rename_rom_with_saves` (ROM+saves vuelven a su estado y contenido original), rollback exitoso de `move_disc_set_to_subfolder` (bin1 vuelve a su sitio, carpeta destino vacía se limpia), y un set de 2 discos movido íntegro (nombres y contenido de ambos `.bin` intactos). 3 tests nuevos (915 en total) |

---

### ONB — Onboarding / Developer Experience (audit 2026-07-04)

Origen: auditoría del proyecto desde la perspectiva de un desarrollador nuevo que no
conoce el proyecto ni el dominio retro-gaming. Roadmap detallado con orden y
estimaciones: `Tareas/diario/archivo/Roadmap-Onboarding.md` (archivado — completado).

| ID | Severidad | Task | Archivo | Estado |
|----|-----------|------|---------|--------|
| ONB-1 | 🔴 Alto | **Falta el archivo `LICENSE`** — el README declara "MIT" pero no existía `LICENSE` en la raíz. Sin él, legalmente el código NO es open source y GitHub no muestra la licencia. | `LICENSE` | ✅ texto MIT estándar (rama `chore/onb-phase1-license-docs-index`, PR #71) |
| ONB-2 | 🔴 Alto | **No hay `CONTRIBUTING.md`** — un dev nuevo no sabe que los PRs van a `develop` (no a `main`), ni los check names de CI, ni que hay pre-commit hooks. Esa info existe pero está en `docs/ci-cd.md` redactada "para Claude". | `CONTRIBUTING.md` | ✅ setup + ramas + checks CI + convenciones + checklist de PR; enlazado desde README (rama `chore/onb-phase2-contributing-config`, PR #72) |
| ONB-3 | 🟠 Medio | **`docs/architecture/architecture.md` desactualizado** — describía `web/response_builders.py` (hoy `web/builders/`), `repository.py` monolítico (hoy mixins), `app.js` monolítico (hoy `static/js/` + `partials/`), BD `library.db` (hoy `library_pc.db` + android), rutas de usuario hardcodeadas y patrones obsoletos (globales de jobs + late imports, sustituidos por `JobManager` + `web/state.py`). | `docs/architecture/architecture.md` | ✅ regenerado desde el código: árbol de módulos real, 2 BDs + 10 tablas, patrones actuales (JobManager, state, seguridad), API → `openapi.json`, historial de refactors (rama `chore/onb-phase3-arch-backlog`) |
| ONB-4 | 🟠 Medio | **`config.toml.example` incompleto** — faltaban secciones que `config.py` ya soporta: `retroachievements.username`, `[inbox]`, `[backup]`, `auto_sync_*`, `[launchers]`, `[notifications]`, `session_ttl`, `[[emulator_paths]]`. Además difería del ejemplo embebido en el README (dos fuentes de verdad, y el del README con el default `host` obsoleto). | `config.toml.example`, `README.md` | ✅ example regenerado desde `load_config()` con todas las claves; README reducido a snippet mínimo + enlace al example (rama `chore/onb-phase2-contributing-config`, PR #72) |
| ONB-5 | 🟡 Medio | **No hay guía de orientación para devs nuevos** — un recién llegado no sabe por dónde empezar a leer, ni que puede levantar el app con datos sintéticos. | `docs/onboarding.md` | ✅ "primeros 30 minutos": pipeline central, mapa de lectura en 6 pasos, flujo request→handler→service→repo, e2e sintético + `/test-pipeline`, Debug Playbook, tests como documentación, primer cambio (rama `chore/onb-phase4-onboarding-glossary`) |
| ONB-6 | 🟡 Medio | **Glosario de dominio inexistente** — el proyecto asume jerga retro que un dev nuevo no domina. | `docs/glossary.md` | ✅ ~30 términos en 4 bloques (identificación, formatos de disco, saves/emulación, infraestructura), cada uno con su "por qué importa en este código"; enlazado desde README, índice de docs y onboarding (rama `chore/onb-phase4-onboarding-glossary`) |
| ONB-7 | ⚪ Bajo | **Índice `docs/README.md` incompleto** — no listaba `ci-cd.md`, `SKILLS-QUICK-START.md`, `arcade-setup.md`, `emulator-compat.md` ni `sync-wifi-sftp.md`; el README raíz tampoco enlazaba al índice de docs. | `docs/README.md`, `README.md` | ✅ sección "Desarrollo" + docs faltantes en índice; sección "Documentación" + licencia enlazada en README (rama `chore/onb-phase1-license-docs-index`, PR #71) |
| ONB-8 | ⚪ Bajo | **Backlog difícil de escanear para alguien nuevo** — mezclaba secciones enteras ya completadas ✅ (SRP, ARC, SEC, UR, REPORT-FIX, DESIGN, PONT, NEW-FEAT…) con lo pendiente. | `Tareas/backlog.md` | ✅ ~440 líneas de secciones completadas movidas a `Tareas/diario/archivo/archivo.md`; el backlog queda solo con pendientes + Debug Playbook (rama `chore/onb-phase3-arch-backlog`) |
| ONB-9 | ⚪ Bajo | **Decisión de idioma/audiencia del README** — todo en español; si el repo también sirve de portfolio internacional, añadir un TL;DR en inglés al inicio (qué es, stack, screenshot) sin traducir el resto. Decisión del usuario. | `README.md` | ✅ TL;DR en inglés (qué es + stack) al inicio del README; sin screenshot porque el repo no tiene ninguno (rama `docs/onb9-readme-english-tldr`) |

> **Completado 9/9** (PRs #71–#74 + ONB-9). Detalle: `Tareas/diario/archivo/Roadmap-Onboarding.md`.

---

### REV43 — Auditoría de calidad de código (`/revisar`, 2026-07-15)

Origen: revisión completa de `src/rom_manager/` (26.9k líneas) con 6 agentes
en paralelo por área (sync, database, web/handlers core, web/server+builders,
detection/scanner/catalog/patch/converters/renamer, retroachievements/
scraper/utils/cli). Ningún fix aplicado todavía — solo documentado, según la
regla "investigar antes de arreglar" de `CLAUDE.md`. Prioridad de orden:
primero todo lo que toca sync de saves (Pilar 3 — riesgo de pérdida de
progreso), luego integridad de BD, luego web, luego el resto.

| ID | Severidad | Task | Archivo(s) | Estado |
|----|-----------|------|-----------|--------|
| REV43-1 | 🔴 Alto | **`AdbTransport.push` sin staging ni backup — borra el remoto si el MD5 no coincide** — a diferencia de `pull()` (que sí usa `.part`), un push corrupto destruye para siempre un save del Anbernic aún no bajado al PC | `sync/adb_transport.py:245-279` | ✅ rama `feature/cable-ux` — sube a `<dst>.part`, verifica MD5 y solo entonces mueve sobre el destino final (`mv -f`); si no coincide, borra solo el `.part` y el original queda intacto. 2 tests nuevos |
| REV43-2 | 🔴 Alto | **Ninguna ruta de sync por cable/ADB llama a `backup_save()`** — solo la ruta rclone (`save_syncer.py`) hace backup-antes-de-sobrescribir; `cable_engine.copy_item` y sus callers (`sync_cable.py`, `cable_sync_daemon.py`) no, violando "ante duda, no sobreescribir; guardar backup primero" | `sync/cable_engine.py:101-144` | ✅ rama `feature/cable-ux` — backup a nivel de caller en `web/handlers/sync_cable.py` (filesystem y pull ADB), mismo patrón que el SD-auto daemon (CABLE-UX-9a); push ADB sin backup remoto a propósito (evitaría un pull extra), mitigado por REV43-1. 1 test nuevo |
| REV43-3 | 🔴 Alto | **`UnboundLocalError` en el `except` de `sync_saves()`** — `remote_path` solo se asigna tras un upload/download exitoso; si el primer archivo falla, revienta toda la sincronización; en fallos posteriores registra en el log de auditoría la ruta remota de un archivo anterior | `sync/save_syncer.py:190,242` | ✅ rama `feature/cable-ux` — `remote_path` se calcula al principio de cada iteración, antes de cualquier transferencia; eliminadas las 3 asignaciones duplicadas/tardías. 1 test nuevo |
| REV43-4 | 🔴 Alto | **Rama `"newest"` compara `st_mtime` en crudo sin tolerancia de clock-skew** (a diferencia de `conflict_resolver.decide()`, que sí usa `tolerance_seconds`) — en SD FAT32/exFAT puede sobrescribir en silencio una partida más nueva sin marcarlo como conflicto | `sync/cable_engine.py:60-85` | ✅ rama `feature/cable-ux` — `plan_direction()` acepta `tolerance_seconds` (default `DEFAULT_MTIME_TOLERANCE_S=2`, igual que `conflict_resolver.decide()`). Hallazgo extra: el modo ADB "newest" en `sync_cable.py:623-650` es una segunda implementación independiente con el mismo bug — misma tolerancia aplicada ahí también; unificar ambas queda como limpieza futura. 2 tests nuevos |
| REV43-5 | 🔴 Alto | **Migración a dos BDs borra la fila origen aunque el upsert al destino haya fallado** — una fila cuya migración falló igualmente se elimina de la BD PC → pérdida permanente de metadatos de catálogo (tags, RA, stats) | `web/handlers/sync_cloud.py:602-657` | ✅ rama `feature/cable-ux` — `migrated_paths`/`migrated_save_paths` trackean éxito por fila; el DELETE en origen solo cubre esas rutas. 1 test nuevo |
| REV43-6 | 🔴 Alto | **`dry_run` ignorado en modo ADB con `skip_sha1_dups`** — `transport.pull(..., dry_run=False)` hardcodeado hace transferencias ADB reales aunque el usuario pidiera solo previsualizar | `web/handlers/sync_cable.py:554` | ✅ rama `feature/cable-ux` — en dry-run el chequeo SHA1 ya no se evalúa (exigiría pull real); se cuenta como "se copiaría" sin transferir nada. 1 test nuevo |
| REV43-7 | 🟠 Medio | **Sync filesystem no valida que `pc_root`/`ab_root` existan** — una SD no montada produce "sync exitoso" con `copied=0, errors=0` en vez de error explícito (inconsistente con `_do_tree_diff`, que sí valida) | `web/handlers/sync_cable.py:638` | ✅ rama `feature/cable-ux` — `raise OSError` explícito si `pc_root`/`ab_root` no existen, capturado por el except genérico de `run()`. 2 tests nuevos |
| REV43-8 | 🟠 Medio | **`_do_sync` (cloud) nunca setea `result_ts`** — el frontend (`flow_wizard.js:342`) hace check truthy sobre ese campo → el paso "Sync" del wizard nunca deja de hacer polling | `web/handlers/sync_cloud.py:497` | ✅ rama `feature/cable-ux` — `result_ts` añadido a los 3 `job_result` posibles (éxito, sin fuentes, except). 1 test nuevo |
| REV43-9 | 🔴 Alto | **`PRAGMA foreign_keys` nunca se activa en ningún sitio del proyecto** — las FKs de `schema.py` (`ON DELETE SET NULL`/cascada) son decorativas, sin integridad referencial real | `database/repositories/base.py` | ✅ rama `fix/db-integrity` — `PRAGMA foreign_keys=ON` en `_open_conn()`. Al comprobar la BD real (`.rommgr/library_pc.db`) aparecieron 4 sitios más con `DELETE FROM games` directo sin cascada (`ra_duplicates_service.py`, `inbox_pipeline.py` x2, `sync_cloud.py`) que habrían roto duplicados/inbox/migración cloud al activar el enforcement — mismo bug que REV43-10 replicado 4 veces; unificado en `cascade_delete_games_by_source_path()` (`games.py`), reutilizado por los 4. 1 test nuevo (`test_foreign_keys_enforced`) |
| REV43-10 | 🟠 Medio | **`delete_game()` solo borra la fila de `games`** — deja huérfanas `game_metadata`/`game_tags`/`file_operations`; se llama desde `duplicates_service.py` e `inbox_pipeline.py:868` al borrar duplicados/ROMs reemplazados | `database/repositories/games.py:309-313` | ✅ rama `fix/db-integrity` — `delete_game()` borra también `game_metadata`/`game_tags`/`file_operations` antes de `games` (helper compartido `_delete_game_children`). Decisión explícita del usuario: se borra el historial de `file_operations` del juego eliminado (no `SET NULL`) — prioriza limpieza sobre preservar auditoría de un archivo que ya no existe. 1 test nuevo (`test_delete_game_removes_children`) |
| REV43-11 | 🟠 Medio | **`get_games_paginated` revienta con `ambiguous column name: id`** al combinar filtro `tag` + `genre`/`year` a la vez (columna `id` sin cualificar choca entre `games` y `game_metadata`); reproducible desde `web/builders/library.py:346-374` | `database/repositories/games.py:410-443` | ✅ rama `fix/db-integrity` — la condición `"id IN"` ya no queda excluida del rewrite a `g.id IN` cuando hay JOIN con `game_metadata`. 1 test nuevo (`test_get_games_paginated_tag_and_genre_together`) |
| REV43-12 | 🟡 Bajo | **`get_save_sync_history` escapa `_`/`%` para LIKE pero la query no lleva `ESCAPE '\'`** — el escapado es un no-op silencioso (sí está bien hecho en `games.py:399-403`) | `database/repositories/sync.py:94-98` | ✅ rama `fix/db-integrity` — añadido `ESCAPE '\\'`. Hallazgo extra: el patrón de `games.py` no basta aquí porque `game_dir` es una ruta real de Windows con `\` como separador, que choca con el propio carácter de escape; se escapan primero las `\` literales del path antes de escapar `_`. 1 test nuevo (`test_get_save_sync_history_escapes_underscore`) |
| REV43-13 | 🔴 Alto | **`_httpd_instance` se guarda como global de `server.py`, no de `_state`** — `/api/shutdown` y `/api/update/apply` leen `_state._httpd_instance` (siempre `None`) → `AttributeError` al invocarlos | `web/server.py:612-615` (vs `web/state.py:44`) | ✅ rama `fix/web-httpd-shutdown` — `serve()` asigna `_state._httpd_instance = httpd` directamente (eliminado el `global _httpd_instance` local, que creaba un atributo de módulo distinto nunca leído por nadie). Smoke test manual: arrancado el servidor real, confirmado `AttributeError` antes del fix y `shutdown()` funcionando después |
| REV43-14 | 🟠 Medio | **Health Check (Tools) siempre falla** — importa `_write_health_schedule` desde `server.py`, pero esa función vive en `daemons.py`; el `ImportError` queda silenciado por el `except Exception` del propio job | `web/handlers/esde/maintenance.py:94` | ✅ rama `fix/web-health-check-import` — import corregido a `rom_manager.web.daemons`. Test nuevo (`tests/test_health_check_job.py`) que ejercita `/api/health-check` de extremo a extremo vía `Router`/`JobManager` reales; confirmado que reproduce el `ImportError` exacto sin el fix y pasa con él |
| REV43-15 | 🟠 Medio | **Con PIN activo, el setup de Anbernic se rompe** — el auth gate no exime `/s` ni `/api/rclone-export-config`, pero ambos están pensados para `curl` sin sesión desde Termux; con PIN, la respuesta es un 302 vacío en vez del script | `web/server.py:256-263` | ✅ rama `fix/web-pin-anbernic-setup` — `/s` y `/api/rclone-export-config` exentos del gate de sesión/PIN (mismo `if` que ya exime `/static/`); ambas rutas ya se protegían solas con `_setup_token_ok()` (loopback o `?t=` válido), así que no quedan abiertas. 4 tests nuevos (`tests/web/test_anbernic_setup_with_pin.py`) — confirmado que 3 reproducen el 302 real sin el fix, y uno confirma que el resto de rutas (`/api/config`) sigue exigiendo sesión |
| REV43-16 | 🟠 Medio | **`post_restore_backup` — path traversal por comparación de prefijo de string** — `not str(tp).startswith(str(config.library_root))` deja pasar `"C:\GamesEvil\..."` si `library_root="C:\Games"`; falta normalizar separador/límite de ruta | `web/handlers/games.py:653` | ✅ rama `fix/web-restore-path-traversal` — sustituido por `Path.resolve()` + `is_relative_to()`. 2 tests nuevos (`tests/web/test_restore_backup_path_traversal.py`); confirmado que sin el fix el caso `GamesEvil` no solo pasaba el check sino que restauraba de verdad el archivo fuera de la biblioteca (`ok: True`) |
| REV43-17 | 🟡 Bajo | **`/api/stop-job` no cancela un escaneo ADB en curso** — `_do_adb_scan` no comprueba el flag de cancelación, a diferencia de `_do_scan` (que sí pasa `stop_event`) | `web/handlers/scan.py:401-469` | ✅ rama `fix/web-adb-scan-cancel` — `_do_adb_scan` obtiene el mismo `cancel_event("scan")` que `_do_scan` (comparten job_id) y corta el bucle de archivos en el siguiente boundary; `cancelled` añadido al `job_result`. Test nuevo (`tests/web/test_adb_scan_cancel.py`) que simula `/api/stop-job` llegando a mitad del escaneo; confirmado que sin el fix el resultado ni siquiera trae la clave `cancelled` |
| REV43-18 | 🟡 Bajo | **`.ups` truncado lanza `IndexError` sin capturar** — `_read_vlq` no comprueba `pos >= len(data)`, a diferencia del mismo helper en `bps_applier.py` que sí lo hace; rompe el contrato de "error controlado, nunca corrupción silenciosa" | `patch/ups_applier.py:14-16` | ✅ rama `fix/patch-ups-truncated` — mismo guard que `bps_applier._read_vlq` (`raise PatchError` si `pos >= len(data)`). Test nuevo; confirmado que sin el fix lanza `IndexError` real, no `PatchError` |
| REV43-19 | 🟡 Bajo | **Offsets negativos de `SourceCopy`/`TargetCopy` no se validan** — un patch BPS corrupto con offset negativo indexa desde el final del array (válido en Python) en vez de fallar con `PatchError`, corrompiendo el resultado en silencio | `patch/bps_applier.py:87-103` | ✅ rama `fix/patch-bps-negative-offset` — `raise PatchError` si `src_rel`/`tgt_rel` quedan negativos tras aplicar el delta. 2 tests nuevos; confirmado que sin el fix no había ninguna excepción — el output salía mal en silencio (`source[-1]` envuelto al final del array) |
| REV43-20 | 🟡 Bajo | **Conversión N64 sobrescribe destino sin comprobar si ya existe** (a diferencia de `chd_converter`, que sí rechaza sobrescribir) | `converters/n64_converter.py:84-85` | ✅ rama `fix/n64-converter-overwrite` — `target.exists()` rechaza la conversión igual que `chd_converter`. 2 tests nuevos (`tests/test_n64_converter.py`, no existía archivo de test previo); confirmado que sin el fix el destino se sobrescribía de verdad (`success=True`) |
| REV43-21 | 🟢 Menor | **Padding de relleno del último chunk se escribe también al archivo de salida** — un `.v64`/`.n64` cuyo tamaño no es múltiplo de 2/4 produce un `.z64` con bytes basura al final | `converters/n64_converter.py:90-103` | ✅ rama `fix/n64-converter-padding` — el padding solo se usa para que el swap esté bien definido; se escriben solo los primeros `orig_len` bytes del resultado. 2 tests nuevos; confirmado que sin el fix el `.z64` salía con 1 byte de más (8 en vez de 7) |
| REV43-22 | 🟡 Bajo | **`LIKE` sin escapar `_`/`%` del propio nombre de archivo** puede actualizar `last_played_at` de un juego equivocado si el nombre contiene `_` | `scanner/rom_scanner.py:145-148` | ✅ rama `fix/scanner-like-escape` — escapado `\`/`%`/`_` + `ESCAPE '\'` (mismo ajuste de barras invertidas de rutas Windows que REV43-12). Test nuevo; confirmado que sin el fix un ROM señuelo (`ZeldaXofXTime.gba`) recibía `last_played_at` de un save de `Zelda_of_Time.srm` |
| REV43-23 | 🟢 Menor | **`cue_validator` no reconoce líneas `FILE` sin comillas** (a diferencia de `chd_converter.parse_bins_from_cue`, que sí) — un `.cue` con `.bin` ausente pasa sin warning durante el scan | `detection/cue_validator.py:6` | ✅ rama `fix/cue-validator-unquoted-file` — mismo patrón de dos regex (comillas → fallback sin comillas) que `chd_converter.parse_bins_from_cue`, sin crear una dependencia inversa `detection`→`converters`. 2 tests nuevos; confirmado que sin el fix un `.bin` ausente referenciado sin comillas pasaba con 0 errores |
| REV43-24 | 🟢 Menor | **Rollback de `move_disc_set_to_subfolder` traga `OSError` en silencio**, sin registrar qué archivo no pudo revertirse (a diferencia de `rename_rom_with_saves`, que sí reporta `rollback_failures`) | `renamer/file_renamer.py:264-273` | ✅ rama `fix/renamer-rollback-failures` — `_rollback()` devuelve la lista de fallos, incluida en el error con el mismo formato "rollback INCOMPLETE — manual fix needed" que `rename_rom_with_saves`. 1 test nuevo (rollback de un BIN forzado a fallar); confirmado que sin el fix el error no mencionaba nada del rollback fallido |
| REV43-25 | 🟢 Menor | **Backup de seguridad puede degenerar en no-op en reintentos** — si `bak` ya existe de un intento previo, `os.replace(bak, bak)` no respalda el save actual antes del siguiente intento de move | `renamer/file_renamer.py:169-171` | ✅ rama `fix/renamer-bak-retry-noop` — siempre busca un nombre `.bak`/`.bak1`/`.bak2`... libre en vez de reemplazar `bak` por sí mismo. 1 test nuevo; confirmado que sin el fix el save actual se sobrescribía sin backup real (`New.srm.bak1` ni siquiera se creaba) |
| REV43-26 | 🟡 Bajo | **`verify_multidisc()` revienta con `IndexError`** si un grupo de set tiene solo archivos sidecar (`.cue`/`.m3u` sin `.bin`/`.chd`/`.iso`) — rompe la verificación de toda la biblioteca, no solo ese set | `utils/multidisc_verifier.py:84` | ✅ rama `fix/multidisc-verifier-index-error` — el chequeo de gaps se salta si `disc_numbers` queda vacío (nada que comprobar sin imágenes reales). 1 test nuevo; confirmado que sin el fix un solo set roto abortaba la verificación de toda la biblioteca (incluido un segundo grupo sano en el mismo directorio) |
| REV43-27 | 🟠 Medio | **Fallo de red en RA trata la plataforma entera como "0 juegos con logros"** — `except Exception: hash_lib = {}` puede inducir a que la resolución de duplicados descarte la versión correcta por un error transitorio | `retroachievements/ra_checker.py:94-97` | ✅ rama `fix/ra-checker-network-failure` — nuevo status `"check_failed"` (distinto de `"no_support"`) para los juegos de una plataforma cuyo fetch falló; ya no entran en `no_support_entries` (`web/handlers/sync.py`), que alimenta el bulk-discard de `discard_no_support`. 2 tests nuevos; confirmado que sin el fix un `TimeoutError` simulado marcaba `no_support` a juegos con soporte RA real, elegibles para borrado masivo |
| REV43-28 | 🟡 Bajo | **Camino alternativo de lectura de caché RA bypasea el TTL de 1 semana** — `get_ra_hash_lib` solo comprueba `cache_file.exists()`, sin el chequeo de antigüedad que sí aplica `ra_client.fetch_hash_library` | `services/ra_duplicates_service.py:180-190` | ✅ rama `fix/ra-hash-lib-ttl` — mismo TTL (`_CACHE_TTL_SECONDS`, 1 semana) que `ra_client.fetch_hash_library`; caché caducada se trata como inexistente. 2 tests nuevos; confirmado que sin el fix una caché de 8 días se usaba igual. Hallazgo extra durante la investigación: `web/builders/duplicates.py:407-416` (`_build_ra_duplicates`) lee el mismo fichero de caché con idéntico bug (sin TTL) — no corregido en esta rama, documentado como **REV43-53** para su propia rama |
| REV43-29 | 🟡 Bajo | **Dedup de `gamelist_writer` colapsa discos distintos del mismo set**, no solo `.m3u` vs `.cue` individuales — la clave de dedup no incluye número de disco | `scraper/gamelist_writer.py:142-166` | ✅ rama `fix/gamelist-writer-disc-dedup` — dedup en dos niveles: si hay `.m3u` colapsa todo el set (comportamiento original preservado); si no, deduplica por número de disco extraído del nombre, no solo por título. 4 tests nuevos (no existía archivo de test); confirmado que sin el fix Disc 2/3 desaparecían del gamelist cuando ScreenScraper asigna el mismo título a todos los discos sin `.m3u` presente |
| REV43-30 | 🟢 Menor | **`except OSError: pass` al escribir `metadata.pegasus.txt`** — una plataforma entera puede no escribirse sin que el caller se entere | `scraper/pegasus_writer.py:76-77` | ✅ rama `fix/pegasus-writer-silent-oserror` — `errors: list[str]` en el resultado; `"platforms"` ahora cuenta solo las escritas con éxito. Handler (`/api/export-pegasus`) ya no reporta `ok: True` incondicional. 2 tests nuevos (no existía archivo de test); confirmado que sin el fix `platforms` mostraba el total sin descontar la que falló |
| REV43-31 | 🟢 Menor | **Contador `errors` del comando `scrape` nunca se incrementa** — el resumen final siempre imprime "Errors: 0" aunque el comando falle a mitad | `cli.py:737-784` | ✅ rama `fix/cli-scrape-error-counter` — causa real: `download_image()` ya devolvía `bool`, pero el valor se ignoraba y `box_art_path` se guardaba igual aunque la descarga fallase. Ahora se captura el resultado, se cuenta como error y no se guarda una ruta que nunca se escribió. 1 test nuevo (invocación real de `cli.main(["scrape"])`); confirmado que sin el fix imprimía "Errors: 0" y `[OK]` pese al fallo real de descarga |
| REV43-32 | 🟢 Menor | **`_EXCLUDED_DIR_NAMES`/`_iter_files` definidos dos veces (copia exacta) en el mismo archivo** — resto de un merge/copiado, la segunda definición pisa a la primera sin efecto funcional | `utils/orphan_finder.py:8-14,32-39` | ✅ rama `fix/rev43-cleanup-batch` — eliminada la definición duplicada |
| REV43-33 | 🟡 Bajo | **`cable_engine`/`adb_transport` nunca escriben en `save_sync_log`** — "toda operación sobre archivos se registra en SQLite" solo se cumple en la capa rclone | `sync/cable_engine.py`, `sync/adb_transport.py` | ✅ `cable_engine.py` sigue sin saber de logging a propósito (motor agnóstico, por diseño) — el fix va en los 3 callers reales que nunca escribían en SQL: `sync_cable.py` (`_do_cable_sync`, modo filesystem + ADB), `cable_sync_daemon.py` (`_run_sd_auto_sync` y `_run_auto_sync`/ADB). Los dry-run no se registran (mismo criterio que `save_syncer.py`). Verificado end-to-end contra el servidor real (carpetas de prueba, fila real en `save_sync_log` de `library_pc.db`, limpiada después). 2 tests nuevos |
| REV43-34 | 🟢 Menor | **Lógica de enrutado por extensión (states→saves→fallback) triplicada** entre `diagnose_routing`/`upload`/`download` | `sync/rclone_transport.py:52-123,199-252,323-376` | ✅ decisión de enrutado extraída a `_resolve_remote()` compartida; cada método reconstruye su propio texto de log/razón (que ya diferían entre sí antes del fix). 17 tests de caracterización nuevos (`tests/test_rclone_transport.py`) que fijan el comportamiento exacto antes y después del refactor — módulo sin tests previos |
| REV43-35 | 🟢 Menor | **Watermark de conflicto se busca solo por `local_path`, ignorando el remoto** — si `saves_remote`/`states_remote` cambian en config, puede usarse un `last_sync_at` que ya no corresponde | `sync/sync_log.py:100-117` | ✅ `get_last_sync()` acepta `remote_path` opcional y filtra por él; `save_syncer.py` calcula el remoto real con `_resolve_remote()` (REV43-34) en vez del placeholder fijo `<routed to saves/states remote>/...`, tanto para el watermark como para el log de auditoría. 1 test nuevo que reproduce el escenario exacto (watermark de un remoto antiguo no se reutiliza, conflicto real no se enmascara) |
| REV43-36 | 🟢 Menor | **Late import de `utc_now` para evitar ciclo** — invierte la dependencia (capa de datos dependiendo de la capa de escaneo) en vez de import a nivel de módulo | `database/repositories/metadata.py:149` | ✅ rama `fix/rev43-cleanup-batch` — `utc_now` extraído a `utils/time.py`, importado a nivel de módulo en ambos lados (`metadata.py` y `rom_scanner.py`) |
| REV43-37 | 🟢 Menor | **"Escape" de LIKE con `prefix.replace("%", "%%")` es un no-op** (`%%` sigue siendo dos comodines, no un `%` literal) — repetido en 3 sitios sin la corrección que sí existe en `games.py:399-403` | `database/repositories/base.py:117`, `assets.py:65`, `games.py:397` | ✅ rama `fix/rev43-cleanup-batch` — `escape_like_prefix()` compartido en `base.py`, reutilizado en los 3 sitios + `ESCAPE '\\'` en la query |
| REV43-38 | 🟢 Menor | **`record_play_session` no acepta `connection` opcional**, a diferencia del resto de métodos de escritura del paquete — no puede participar en un `batch()` externo | `database/repositories/play_history.py:13-47` | ✅ rama `fix/rev43-cleanup-batch` — parámetro `connection` opcional; 3 tests nuevos incluido uno que confirma participación en `batch()` externo |
| REV43-39 | 🟢 Menor | **Clasificación imagen/vídeo por extensión duplicada en 3 capas** | `database/repositories/assets.py:62-63`, `web/handlers/esde/system.py`, `web/builders/folders.py` | ✅ set canónico `utils/media_types.py` (`IMAGE_EXTS`/`VIDEO_EXTS`), reutilizado en los 3 sitios. De paso corrige inconsistencia real: `esde/system.py` y `folders.py` no reconocían `.tga`/`.bmp` como imagen |
| REV43-40 | 🟢 Menor | **Descarga de DATs implementa su propio sistema de jobs** (lock/dict/thread propios) en vez de registrarse en `job_manager`/`/api/job-status` | `web/handlers/scan.py:69-70,188-209` | ✅ `download_dats` añadido a `JOB_NAMES`; nuevo `JobManager.get_job()` genérico (para jobs con endpoint de estado propio en vez del `/api/job-status` compartido); `_run_dat_download` ya no usa lock/dict propios. `/api/download-dats-status` mantiene la misma forma de respuesta — sin cambios en frontend. 2 tests nuevos (`test_jobs_manager.py`) |
| REV43-41 | 🟢 Menor | **`_do_organize_library` hace `commit()` por fila** en vez de `repository.batch()`, contradice la convención documentada | `web/handlers/organize.py:330-366` | ✅ rama `fix/rev43-cleanup-batch` — todo el bucle de moves ahora corre dentro de un único `repository.batch()` |
| REV43-42 | 🟢 Menor | **Export/status de config rclone implementado dos veces con lógica divergente** | `web/handlers/sync_cloud.py:166-215` vs `web/handlers/system.py:193-256` | ✅ `system.py` reutiliza `_handle_rclone_status` de `sync_cloud.py` (la versión con ruta HTTP real) en vez de mantener su propia copia divergente; `_handle_rclone_export_config` de `system.py` era código muerto (sin caller) — eliminado |
| REV43-43 | 🟢 Menor | **Lookup de caché RA duplicado entre el enriquecido bulk y el individual** | `web/handlers/games.py:97-143` vs `:411-442` | ✅ rama `fix/rev43-cleanup-batch` — unificado en `_lookup_ra_game()`, reutilizado por ambos endpoints |
| REV43-44 | 🟢 Menor | **`print()` de depuración a nivel de módulo** en vez de `logging` | `web/handlers/collection.py:28` | ✅ rama `fix/rev43-cleanup-batch` — `logging.getLogger(__name__).debug(...)` |
| REV43-45 | 🟢 Menor | **Late import de `web.state`** dentro de la función, contradice CLEAN-1 | `web/handlers/update.py:90` | ✅ rama `fix/rev43-cleanup-batch` — import movido a nivel de módulo |
| REV43-46 | 🟢 Menor | **Bloque de serialización de grupos de duplicados duplicado 4 veces en el mismo archivo** | `web/builders/duplicates.py` | ✅ rama `fix/rev43-cleanup-batch` — unificado en `_load_ra_hash_map()` (también corrige REV43-53 de paso, misma función) |
| REV43-47 | 🟢 Menor | **`DatDownloadResult` sin `slots=True`** e importa el símbolo privado `_load_dat_file` de otro módulo | `catalog/dat_downloader.py:11,90` | ✅ rama `fix/rev43-cleanup-batch` — `@dataclass(slots=True)`; `_load_dat_file` renombrado a público `load_dat_file` (y sus 2 callers actualizados) |
| REV43-48 | 🟢 Menor | **`KNOWN_BIOS` modelado como `list[dict]`** en vez de `@dataclass(slots=True)` como el resto del archivo | `detection/bios_checker.py:17` | ✅ rama `fix/rev43-cleanup-batch` — `BiosDef` dataclass con slots |
| REV43-49 | 🟢 Menor | **`_same_file()` duplicado carácter por carácter** en dos archivos | `planner/operation_planner.py:11-21`, `renamer/file_renamer.py:98-102` | ✅ rama `fix/rev43-cleanup-batch` — extraído a `utils/paths.same_file()`, importado en ambos |
| REV43-50 | 🟢 Menor | **`pegasus_writer` no aplica dedup multi-disco** (a diferencia de `gamelist_writer`) — salidas incoherentes entre formatos para los mismos datos | `scraper/pegasus_writer.py` | ✅ rama `fix/rev43-cleanup-batch` — reutiliza `gamelist_writer._deduplicate()`. Test nuevo (2 discos sin `.m3u`, mismo `canonical_title`, confirmando que ninguno se colapsa) |
| REV43-51 | 🟢 Menor | **`GeneratedSystem`/`GeneratorResult` sin `slots=True`** | `esde/systems_generator.py:214-229` | ✅ rama `fix/rev43-cleanup-batch` — `@dataclass(slots=True)` en ambas |
| REV43-52 | 🟢 Menor | **`cli.py` mete lógica de negocio completa inline** (`scrape`, `convert-chd`, `sync`, `health`) en vez de delegar a `services/`, rompiendo el patrón ya establecido (ARC-SVC-1) | `cli.py` | ✅ alcance real tras revisar los 4 comandos: `convert-chd` y `health` ya delegaban a funciones reales (`convert_directory`, `check_library_health`) — solo imprimen resultados, no duplican lógica. `scrape` sí duplica un bucle no trivial con la versión del job web (`web/handlers/scraper.py`), pero unificarlo exigiría fusionar dos flujos con features distintas (resumable + rate-limit en el job web vs simple en CLI) — fuera de alcance "Menor", no tocado hoy. El hallazgo real y explotable era **`sync`**: `cli.py` usaba `config.sync.sync_sources` directo, sin las fuentes ra_config/cheats/playtime que sí incluye `_do_sync` (web) — el `rommgr sync` headless (pensado para Task Scheduler, S38-2) se saltaba en silencio esas fuentes. Extraído `build_cloud_sync_sources()` (`config.py`, mismo sitio que `get_adb_sync_sources`), usado ahora por `cli.py` y por `web/handlers/sync_cloud.py::_do_sync` — un único comportamiento para ambos entry points. 4 tests nuevos |
| REV43-53 | 🟡 Bajo | **`_build_ra_duplicates` lee la caché RA sin comprobar TTL** — mismo bug que REV43-28 (`get_ra_hash_lib`), pero en un lector independiente del mismo `.rommgr/ra_cache/*.json`; una caché caducada puede hacer que la vista de duplicados RA marque como "sin soporte" una versión que sí lo tiene | `web/builders/duplicates.py:407-416` | ✅ rama `fix/rev43-cleanup-batch` — mismo fix que REV43-46 (`_load_ra_hash_map()` comprueba `_CACHE_TTL_SECONDS`). 4 tests nuevos (`tests/test_duplicates_ra_cache.py`) |

> Orden sugerido de ataque: REV43-1…8 (sync, riesgo de pérdida de datos) →
> REV43-9…12 (integridad de BD) → REV43-13…17 (bugs de web) → resto por
> valor/esfuerzo. Cada fix en su propia rama, siguiendo el patrón ya usado en
> INBOX-FIX-*/ZIP-ROUTE-FIX-*/DEVSEL-FIX-*.

---
