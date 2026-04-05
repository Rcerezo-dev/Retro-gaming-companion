# Retro Vault — Backlog

> Single source of truth for pending work. Updated every session.
> Last updated: 2026-04-05 (Idea_final.md triage — expanded into roadmap tasks)
> Completed Phase 2 tasks moved to `Tareas/archivo.md` to save tokens.
> Active bug tracking: `Tareas/bugs/duplicados.md`
> Architecture reference: `docs/refactor/Roadmap-Arquitectura-Frontend.md`

---

## Now — Quick fixes (carry-over from Day 23)

| ID | Task | Where |
|----|------|-------|
| B-test | Verify `_apply_ra_conflicts`: winner gets renamed, loser goes to `_descartados/` | `handlers/duplicates.py` — see `bugs/duplicados.md` |

**B-test subtasks:**

| ID | Task | Functions/Files |
|----|------|----|
| B-test-1 ✅ | UI warning: show confirmation dialog that RA Check will run and may take time | `static/js/tabs/duplicates.js::doResolveRaConflicts` — warn user, trigger RA Check if needed |
| B-test-2 ✅ | Auto-rename winner: after discarding loser, move winner to canonical name | `handlers/duplicates.py::_apply_ra_conflicts` — rename source → target, update DB |
| B-test-3 ✅ | Better diagnostics: improve hint text, show cache status, guide next steps | `handlers/duplicates.py` — added `next_step` field in response |
| B-test-4 | Test with real data: verify winner renamed + moved, loser in _descartados/, DB updated | Run full scenario: RA Check → Build Plan → Apply RA → Verify |

| ID | Task | Where | Status |
|----|------|-------|--------|
| D2 ✅ | rclone handler: route files to `saves_remote` or `states_remote` by extension | `sync/rclone_transport.py` + 4 callers | Done: routing, diagnostics, edge cases |

---

## User feedback — Device connectivity & Database issues

Extracted from testing session (2026-03-31). These are design/UX issues affecting core workflows.

### UX-1 & UX-2 — Device Connectivity (in progress)

Device is "connected" if EITHER:
- ADB device available (USB Android device), OR
- SD card mounted at configured `anbernic_root` path

**Subtasks:**
| ID | Task | File |
|----|------|------|
| UX-1/2-1 ✅ | Create `is_device_connected()` function — checks both ADB + SD card mount | `config.py` |
| UX-1/2-2 ✅ | Add `/api/device-status` endpoint — returns `{connected: bool, reason: str}` | `web/handlers/config.py` |
| UX-1/2-3 ✅ | Frontend polling — call `/api/device-status` every 4s, update state | `static/js/state.js` + `main.js` |
| UX-1/2-4 ✅ | Update startup cards — show status badge (✗ No conectado when offline) | `static/js/tabs/overview.js` + `index.html` |
| UX-1/2-5 ✅ | Disable rename button when offline + targeting Android — prevent offline operations | `static/js/tabs/organize.js` |

| ID | Task | Priority | Status |
|----|------|----------|--------|
| UX-1 ✅ | **Device connectivity indicator** — Show on startup cards if Android SD is NOT plugged in | High | Complete |
| UX-2 ✅ | **Block operations on inactive device** — Prevent "Ejecutar cambios" when target device (consola android) is not plugged in | High | Complete |
| DB-1 ✅ | **Metadata cache flag** — Add boolean in games table to mark files already scraped (found no metadata) | Medium | Complete: Added metadata_scraped flag to avoid re-scraping. Schema migration + repository method + scraper updates. |
| DB-2 ✅ | **Orphaned record cleanup** — Clean up DB entries when files are deleted from disk | Medium | Complete: Enhanced prune_stale_entries() to clean up metadata, tags, and operation logs. Display cleanup count in CLI. |
| DUP-3 ✅ | **Delete option for "Colisión de plan"** — If 2 files have same canonical name, offer delete-from-duplicates button alongside rename | Medium | Complete: Added "Eliminar duplicados" button to conflict resolution in plan view |
| DUP-4 | **Clarify delete-all counts** — Show breakdown: X disk duplicates deleted, Y skipped (no source), Z failed | Low | ✅ FIXED: Enhanced response to show deleted/skipped/failed breakdown |

---

## Bug Fixes — Active Issues

| ID | Task | Priority | Status |
|----|------|----------|--------|
| BUG-ASSETS-1 | **Assets tab shows "not found"** — Routes ARE registered but dispatcher returns 404 | High | 🔍 DEBUGGING: Endpoint code exists, routes registered in exact dict, but dispatch fails to match. Root cause TBD |
| BUG-ASSET-IMAGE-404 | **Game cover images show 404** — Missing `/api/asset-image` endpoint | High | ✅ FIXED: Added endpoint to collection.py |
| BUG-ORG-1 | **Organizar tab window._h error** | High | ✅ FIXED: Added _h to window exports |
| BUG-COL-1 | **Coleccion tab window._h error** | High | ✅ FIXED: Added _h to window exports |
| BUG-DUP-FALSE | **Duplicados shows false empty state** — Cascading error from related issues | High | ✅ FIXED: All cascading issues resolved |
| BUG-ORG-RA-RENAME-PLAN | **"Resolver por RA" button error** — RenamePlan missing operations attribute | High | ✅ FIXED: Changed plan.operations to plan.pending in duplicates.py |
| BUG-PLATBADGE | **Games list in Organizar — window._platBadge is not a function** — Missing export | High | ✅ FIXED: Exported from games.js + added to main.js |
| BUG-ORG-DELETE-COLLISION | **"Eliminar duplicados" button in collision section doesn't work** — Broken DOM selector | High | ✅ FIXED: Updated selector to find collision div correctly |
| BUG-DELETE-DUPLICATES-MISMATCH | **Delete-all reports 550 deleted but files still exist** — Files not actually deleted from disk | Critical | ✅ APPEARS FIXED: Duplicados tab now shows no duplicates after delete-all. Verify with fresh data + check diagnostics |
| BUG-ROUTING-404 | **Router dispatch returns False for registered GET routes** | Critical | 🔍 DIAGNOSTICS ADDED: Enhanced router.dispatch() and server.py startup logging to identify root cause. Check stderr output when server starts. Suspected causes: path encoding, handler exceptions, or registration failure |

---

---

## Debug Instructions for BUG-ROUTING-404

To identify root cause:
1. Start server: `python -m rom_manager web 2>&1 | grep -E "\[DEBUG\]|\[DISPATCH"` to capture diagnostic output
2. Check if asset routes are registered at startup:
   - Should see: `[DEBUG] Registered asset routes: [('GET', '/api/assets'), ('GET', '/api/asset-image'), ...]`
   - If none, registration failed - check for `[ERROR] Failed to register`
3. Make a request to `/api/assets` and check stderr:
   - If dispatch succeeds: handler is called, check response in browser/curl
   - If dispatch fails: check `[DISPATCH-FAIL]` log for why key doesn't match
4. Report findings to next session

---

## Next — Features

| ID | Task | Notes | Status |
|----|------|-------|--------|
| B2 ✅ | Batch run: add checkboxes per tool, respect logical order, context selector PC/Android | Tools tab | Complete: Wired context selector to batch run. doBatchRun() now respects PC/Android mode and resolves correct root path. |
| B3 ✅ | Library comparator PC vs Android — diff screen + `POST /api/sync-roms` + conflict policy | | Complete: B3-1 ✅ B3-2 ✅ B3-3 ✅ B3-4 ✅ B3-5 ✅ |
| P1 ✅ | Inbox file watcher — polling 30s → auto-pipeline → toast | | Complete: watcher + auto-pipeline already existed; added trigger_ts stamp on auto-trigger + _checkAutoTrigger() frontend poll (30s) that shows toast and starts job poller |
| P3 ✅ | Disk usage panel per platform — `GET /api/disk-usage` | | Complete: backend sums file sizes via Path.stat() grouped by platform + shutil.disk_usage for drive free/total; frontend panel with per-platform bars + disk bar, toggled via 💾 Disco button in collection toolbar |
| P5 ✅ | Collection completeness — cross with DATs, % per platform | | Complete: backend already existed (/api/collection-stats via _build_missing_data); restored UI as 📋 Completitud toggle panel in collection toolbar |

---

## Sync — Android emulator path mapping

Android emulators use fixed paths under `Android/Data/<package>/` (scoped storage, cannot be changed). The app must know these paths and use ADB to pull/push files. Paths confirmed so far:

| Emulator | Package | Saves path | Savestates path |
|----------|---------|------------|-----------------|
| DuckStation (PS1) | `com.github.stenzek.duckstation` | `.../files/memcards` | `.../files/savestates` |
| AetherSX2 / NetherSX2 (PS2) | `xyz.aethersx2.android` | TBD | TBD |

**Tasks:**

| ID | Task | Notes |
|----|------|-------|
| SYNC-A1 ✅ | Document save/savestate paths for all target emulators | Verified live on RG556 via ADB. Full reference: `docs/android-save-paths-RG556.md` |
| SYNC-A2 ✅ | Add emulator path mapping table to `config.toml` or hardcode as defaults | Keyed by package name; user can override. Done: `EMULATOR_SAVE_PATHS_DEFAULT` in config.py (18 emulators), `[[emulator_paths]]` overrides in config.toml, merged into `AppConfig.emulator_paths` |
| SYNC-A3 ✅ | Update sync logic to pull/push via ADB using mapped paths instead of assuming a configurable root | Done: `get_adb_sync_sources()` in config.py builds 13 per-emulator sources from `emulator_paths`; `_run_auto_sync()` in cable_sync_daemon.py loops sources instead of single root. Saves to `library_root/emulator_saves/<package>/saves\|states/`. SD-card emulators (RetroArch/PPSSPP) handled by SD daemon as before. |

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
- WiFi sync PC ↔ console via SFTP (prereq: Termux guide at `Tareas/guias/Guia-Termux-Anbernic.md`)
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

Extracted from `docs/refactor/Idea_final.md` and broken into actionable tasks.

---

### RENAME-CONFLICT — Name collision: prefer RA version

When two games map to the same canonical name during rename, discard the non-RA version instead of appending `_1`/`_2`. Reuses `_apply_ra_conflicts` logic.

| ID | Task | File |
|----|------|------|
| RENAME-CONFLICT-1 | Detect name collisions in rename planner — flag pairs where two sources share the same canonical target | `renamer/operation_planner.py` |
| RENAME-CONFLICT-2 | For each collision pair, run RA check to determine which file has RetroAchievements support | `handlers/organize.py` — reuse existing RA cache |
| RENAME-CONFLICT-3 | Auto-resolve: rename RA winner to canonical name, move loser to `_descartados/` | `handlers/organize.py` + `_apply_ra_conflicts` |
| RENAME-CONFLICT-4 | Show collision resolution in plan view — label winner and loser clearly before user confirms | `static/js/tabs/organize.js` |

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
| CLOUD-RESEARCH-1 | Document rclone setup on PC — install path, Dropbox OAuth config, test push/pull | `docs/cloud-sync-setup.md` |
| CLOUD-RESEARCH-2 | Document Termux setup on Anbernic RG556 — install rclone, auth, verify it can reach Dropbox | `docs/cloud-sync-setup.md` |
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

### BUG-TOOLS-SIDEBAR — Sidebar hides in Tools subtabs

| ID | Task | File |
|----|------|------|
| BUG-TOOLS-SIDEBAR-1 | Reproduce: identify exactly which Tools subtabs hide the left nav | Browser + dev tools |
| BUG-TOOLS-SIDEBAR-2 | Find root cause — likely a full-width container, missing class, or JS toggling sidebar state | `static/js/tabs/tools.js` + `app.css` |
| BUG-TOOLS-SIDEBAR-3 | Fix and verify all Tools subtabs show sidebar consistently | same files |

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

### SYNC-PS1PS2 ✅ — ADB access to PSX/PS2 hidden save paths

Completed. DuckStation and AetherSX2 paths verified and mapped in `EMULATOR_SAVE_PATHS_DEFAULT`.

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
