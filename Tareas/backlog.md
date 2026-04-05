# Retro Vault — Backlog

> Single source of truth for pending work. Updated every session.
> Last updated: 2026-04-05 (Archived all completed tasks to `archivo.md`)
> Completed tasks → `Tareas/archivo.md`
> Architecture reference: `docs/architecture/Roadmap-Arquitectura-Frontend.md`

---

## Now

| ID | Task | Where |
|----|------|-------|
| B-test-4 | Test `_apply_ra_conflicts` with real data: verify winner renamed, loser in `_descartados/`, DB updated | Run full scenario: RA Check → Build Plan → Apply RA → Verify |

---

## Bug Fixes — Active

| ID | Task | Priority | Status |
|----|------|----------|--------|
| BUG-ASSETS-1 | **Assets tab shows "not found"** — Routes ARE registered but dispatcher returns 404 | High | 🔍 DEBUGGING: Endpoint code exists, routes registered in exact dict, but dispatch fails to match. Root cause TBD |
| BUG-ROUTING-404 | **Router dispatch returns False for registered GET routes** | Critical | 🔍 DIAGNOSTICS ADDED: Enhanced router.dispatch() and server.py startup logging to identify root cause. Suspected causes: path encoding, handler exceptions, or registration failure |

### Debug instructions for BUG-ROUTING-404

1. Start server: `python -m rom_manager web 2>&1 | grep -E "\[DEBUG\]|\[DISPATCH"` to capture diagnostic output
2. Check if asset routes are registered at startup:
   - Should see: `[DEBUG] Registered asset routes: [('GET', '/api/assets'), ('GET', '/api/asset-image'), ...]`
   - If none, registration failed - check for `[ERROR] Failed to register`
3. Make a request to `/api/assets` and check stderr:
   - If dispatch succeeds: handler is called, check response in browser/curl
   - If dispatch fails: check `[DISPATCH-FAIL]` log for why key doesn't match

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
