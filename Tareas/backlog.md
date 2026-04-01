# Retro Vault — Backlog

> Single source of truth for pending work. Updated every session.
> Last updated: 2026-04-02
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
| DB-1 | **Metadata cache flag** — Add boolean in games table to mark files already scraped (found no metadata) | Medium | Avoid re-scraping same files repeatedly. Allows "Check metadata BEFORE scraping" workflow. |
| DB-2 | **Orphaned record cleanup** — Clean up DB entries when files are deleted from disk | Medium | Currently unclear if `os.remove()` in delete workflows triggers DB cleanup. Verify and document cleanup policy. |
| DUP-3 ✅ | **Delete option for "Colisión de plan"** — If 2 files have same canonical name, offer delete-from-duplicates button alongside rename | Medium | Complete: Added "Eliminar duplicados" button to conflict resolution in plan view |
| DUP-4 | **Clarify delete-all counts** — Show breakdown: X disk duplicates deleted, Y skipped (no source), Z failed (Android unmounted) | Low | UX clarity. Currently "99 failed" out of 224 groups is confusing — users don't understand what happened to the rest. |

---

## Next — Features

| ID | Task | Notes |
|----|------|-------|
| B2 | Batch run: add checkboxes per tool, respect logical order, context selector PC/Android | Tools tab |
| B3 | Library comparator PC vs Android — diff screen + `POST /api/sync-roms` + conflict policy | |
| P1 | Inbox file watcher — polling 30s → auto-pipeline → toast | |
| P3 | Disk usage panel per platform — `GET /api/disk-usage` | |
| P5 | Collection completeness — cross with DATs, % per platform | |

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
| SYNC-A1 | Document save/savestate paths for all target emulators | DuckStation ✓ partially, AetherSX2 package name known — paths need verification |
| SYNC-A2 | Add emulator path mapping table to `config.toml` or hardcode as defaults | Keyed by package name; user can override |
| SYNC-A3 | Update sync logic to pull/push via ADB using mapped paths instead of assuming a configurable root | Replaces assumption that emulator paths are user-configurable |

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
