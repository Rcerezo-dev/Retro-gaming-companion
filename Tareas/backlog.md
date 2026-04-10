# Retro Vault — Backlog

> Single source of truth for pending work. Updated every session.
> Last updated: 2026-04-09 (sesión routing bugs + tools sidebar)
> Completed tasks → `Tareas/archivo.md`
> Architecture reference: `docs/architecture/Roadmap-Arquitectura-Frontend.md`

---

## Now

| ID | Task | Where |
|----|------|-------|
| B3/0B | ✅ DONE — Comparador PC vs Android completo: `/api/library-diff` + `/api/sync-roms` + UI con checkboxes, select-all y "Sincronizar todo →" por columna | `Collection` tab → botón 🔀 Comparar |

---

## Bug Fixes — Active

| ID | Task | Priority | Status |
|----|------|----------|--------|
| BUG-DUP-PERM | **Duplicate deletion fails with WinError 5 (Access Denied)** on `E:\Carpetas anbernic\gb\` — all `os.remove()` calls silently fail; duplicates not deleted | High | ✅ FIXED: Added `_force_remove()` helper in `handlers/duplicates.py` that clears the read-only attribute (`os.chmod(S_IWRITE)`) before retrying deletion. Applied to `_delete_duplicate` and `_delete_all_duplicates`. |
| BUG-MISSING-ROUTES | **Frontend calls 5 unregistered API routes** — `DISPATCH-FAIL` logged on every page load | Medium | ✅ FIXED: Added all 5 handlers. `auth/status`, `health-schedule`, `test-chdman`, `test-maxcso` → `handlers/config.py`. `disc-folders` → `handlers/esde.py`. |
| BUG-ASSETS-1 | **Assets tab shows "not found"** | High | ✅ FIXED: Root cause was missing route registration. `/api/assets` always existed in collection.py; the 404 was caused by BUG-MISSING-ROUTES polluting dispatch. All routes verified returning 200. |
| BUG-ROUTING-404 | **Router dispatch returns False for registered GET routes** | Critical | ✅ FIXED: Root cause identified — 13 routes called by the frontend were never registered in handlers. Added `system-status`, `detect-cloud-folder`, `library-doctor`, `retroarch-check`, `bios-status`, `n64-scan` → `handlers/esde.py`. Added `autostart-status`, `autostart-toggle` → `handlers/config.py`. Total routes now 132 (was 119). |

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
| 404 en rutas registradas | `router.dispatch()` — ver BUG-ROUTING-404 arriba |

---

## Roadmap App Universal

### Phase 1 — Frictionless first run
- Auto-detect RetroArch (common paths + Steam + RetroBat)
- Auto-detect cores from `cores/` folder; warn if missing
- Generate `es_systems.cfg` from detected cores
- Auto-detect Android device via ADB on USB connect
- Folder picker with "Browse" button (Settings fields)

### Phase 2 — DATs without effort
- Guided DAT download with contextual explanation
- Clear UI for matching mode (with DAT vs by filename)

### Phase 3 — Sync without config
- WiFi sync PC ↔ console via SFTP (prereq: `docs/sync/Guia-Termux-Anbernic.md`)
- Auto-sync on connect — detect via ADB, prompt "Sync now?"
- Sync status always visible in header

### Phase 4 — Non-technical UX
- Human-readable errors (no stack traces in UI)
- Contextual help — tooltips and `?` icons per section
- Responsive UI (works from Android browser)
- Windows toast notifications on sync complete / inbox detected
- Rename jargon: "DATs" → "Game database", "SHA1 match" → "Auto-identification"

### Phase 5 — Auth
- PIN when `host = 0.0.0.0`

### Phase 6 — Distribution
- PyInstaller executable (`RetroVault.exe`)
- Windows installer (Inno Setup) — shortcut, Add/Remove Programs, minimal DATs
- Auto-update via GitHub Releases
- Decide final name: Retro Vault vs Retro Companion

---

## Roadmap — Ideas from Idea_final.md

Extracted from `docs/ideas/Idea_final.md` and broken into actionable tasks.

---

### RENAME-CONFLICT — Name collision: prefer RA version ✅

✅ DONE: All 4 tasks complete.
- Collision/disk conflict detection: `planner/operation_planner.py` (build_plan)
- RA resolution: `handlers/duplicates.py::_apply_ra_conflicts` (B-test-4 passing)
- Plan view preview: `response_builders.py::_annotate_conflicts_with_ra` — adds `ra_achievements`, `ra_target_achievements`, `ra_role` per conflict row
- Frontend badges: `static/js/tabs/organize.js` — winner/loser labels shown in conflict tables when RA cache is available

---

### COL-REVIEW — Decide fate of Colección tab

Currently overlaps heavily with Juegos. Options: merge it away, or add unique value.

| ID | Task | Notes |
|----|------|-------|
| COL-REVIEW-1 | Audit: list what Colección shows that Juegos doesn't — make a decision | Design/discussion task before any code |
| COL-REVIEW-2a | **If merging**: remove Colección tab, move any unique data into Juegos tab | `index.html` + `static/js/tabs/collection.js` |
| COL-REVIEW-2b | **If keeping**: add playtime source — read RetroArch `.lpl` playlist timestamps or save file mtime as proxy | `handlers/collection.py` |
| COL-REVIEW-2c | **If keeping**: add RA sync — fetch user's earned achievements per game via RA API and display in tab | `handlers/collection.py` + `static/js/tabs/collection.js` |

---

### RA-COPY-LINK — "Copy download link" per game (RetroAchievements)

For games where a RA-compatible version exists, a copy button lets JDownloader pick up the link directly.

| ID | Task | File |
|----|------|------|
| RA-COPY-LINK-1 | Backend: `/api/ra-game-url?game_id=X` — return the RA game page URL and the no-intro/redump entry link | `handlers/retroachievements.py` |
| RA-COPY-LINK-2 | Frontend: add "Copiar link" button per game row in RA results table — uses `navigator.clipboard` | `static/js/tabs/tools.js` or relevant RA tab |
| RA-COPY-LINK-3 | Show a small toast confirming the link was copied | shared toast utility |

---

### FLOW-WIZARD — Unified "run all" wizard

One button runs scan + rename plan + duplicate detection + sync, then walks the user tab-by-tab to approve or skip each step.

| ID | Task | File |
|----|------|------|
| FLOW-WIZARD-1 | Backend: `POST /api/plan-all` — runs scan, rename plan, and duplicate detection; returns a combined summary object | `handlers/wizard.py` (new) |
| FLOW-WIZARD-2 | Frontend: wizard modal shell — step list (Escanear → Organizar → Duplicados → Sync) with Next/Skip buttons | `static/js/wizard.js` (new) + `index.html` |
| FLOW-WIZARD-3 | Per-step diff view — show pending changes for each step; user approves or skips | `static/js/wizard.js` |
| FLOW-WIZARD-4 | Execute approved steps in sequence via existing endpoints; show combined progress + results summary | `static/js/wizard.js` |

---

### CLOUD-RESEARCH — rclone + Termux for Dropbox sync

Prerequisite for the Cloud sync tab. Must work on both PC (rclone binary) and Android (Termux + rclone).

| ID | Task | Notes |
|----|------|-------|
| CLOUD-RESEARCH-1 | Document rclone setup on PC — install path, Dropbox OAuth config, test push/pull | `docs/sync/sync-cloud.md` |
| CLOUD-RESEARCH-2 | Document Termux setup on Anbernic RG556 — install rclone, auth, verify it can reach Dropbox | `docs/sync/Guia-Termux-Anbernic.md` |
| CLOUD-RESEARCH-3 | Define sync protocol — which direction is authoritative, conflict policy, file filter (saves only) | Design doc before code |
| CLOUD-RESEARCH-4 | Prototype: extend `rclone_transport.py` with cloud push/pull calls | `sync/rclone_transport.py` |
| CLOUD-RESEARCH-5 | Cloud sync UI — status panel, last sync timestamp, manual trigger button in Cloud tab | `static/js/tabs/sync.js` |

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

### BUG-INBOX-SIDEBAR — Sidebar renders at bottom in Inbox tab

✅ FIXED: Two stray `</div>` tags inside `tab-collection` (index.html ~line 1499) were prematurely closing `content-area` and `app-body`. This broke the flex layout for every tab from `tab-tv` onwards (tv, scraper, tools, formats, inbox, settings), pushing the sidebar outside the flex row. Removed the 2 extra closing tags.

---

### BUG-TOOLS-SIDEBAR — Sidebar hides in Tools subtabs

✅ FIXED: La causa raíz era la misma que BUG-INBOX-SIDEBAR. Los dos `</div>` extra en `tab-collection` cerraban `.content-area` y `.app-body` prematuramente, rompiendo el flex layout para todas las tabs posteriores (tv, scraper, tools, formats, inbox, settings). Al eliminar esos tags (commit del BUG-INBOX-SIDEBAR), el sidebar volvió a ser visible en todas las tabs afectadas. Verificado: `tab-collection` Delta=0, `.content-area` cierra en L2522 después de todos los tabs.

---

### ANBERNIC-TV — TV-friendly UI for console browsing

A simplified guided flow usable from the Anbernic screen without a keyboard.

| ID | Task | File |
|----|------|------|
| ANBERNIC-TV-1 | Design guided flow — steps: Connect check → Sync → Results; large touch targets, minimal text input | Design task |
| ANBERNIC-TV-2 | Responsive CSS for small/touch screens — Anbernic RG556 browser resolution | `static/app.css` |
| ANBERNIC-TV-3 | TV UI step 1: device status check + connect prompt | `static/js/tabs/anbernic.js` |
| ANBERNIC-TV-4 | TV UI step 2: one-tap sync trigger with live progress bar | `static/js/tabs/anbernic.js` |
| ANBERNIC-TV-5 | TV UI step 3: results summary in large readable format | `static/js/tabs/anbernic.js` |

---

### ARCADE-SETUP — Research arcade ROM config (no code)

| ID | Task | Notes |
|----|------|-------|
| ARCADE-SETUP-1 | Research MAME vs FBNeo ROM set version compatible with Anbernic RG556 RetroArch | Check RG556 community guides |
| ARCADE-SETUP-2 | Identify target arcade systems and map each to the correct RetroArch core | e.g. CPS1/2/3, Neo-Geo, MAME 2003 Plus |
| ARCADE-SETUP-3 | Document config additions: `config.toml`, library-structure, DAT sources for arcade | `docs/arcade-setup.md` |
| ARCADE-SETUP-4 | Test a sample ROM end-to-end: scan → rename → launch on device | Hardware test |

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

## User actions (no code needed)

| ID | Task |
|----|------|
| STRUCT-4 | Configure RetroArch PC: Saving → Savefile Directory → `E:\Carpetas anbernic\saves\` |
| STRUCT-3 | Update `config.toml`: `local_dir = "E:\\Carpetas anbernic\\saves"` (after STRUCT-4) |
| ES-1 | Download `genesis_plus_gx` core in RetroArch → Online Updater |
| ES-2 | Configure Citra (3DS) in EmulationStation |
