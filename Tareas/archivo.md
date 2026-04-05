# Retro Vault — Archivo de Tareas Completadas

> Archivo de tareas terminadas. Movidas de `backlog.md` para optimizar tokens.
> Última actualización: 2026-04-05

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
