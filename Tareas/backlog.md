# Retro Vault — Backlog

> Single source of truth for pending work. Updated every session.
> Last updated: 2026-04-02 — Phase 2 Frontend Migration COMPLETE ✅ (2a-2l all done, app.js deleted)
> Active bug tracking: `Tareas/bugs/duplicados.md`
> Architecture reference: `docs/refactor/Roadmap-Arquitectura-Frontend.md`

---

## Now — Frontend migration Phase 2 (in progress)

Phase 2 status: 2a (state.js) ✅ 2b (esde.js) ✅ — continuing with 2c.

| ID | Task | File |
|----|------|------|
| 2c | Create `js/tabs/games.js` — game list, filters, pagination, game panel, TV mode | `static/js/tabs/games.js` |

**2c subtasks:**

| ID | Task | Functions |
|----|------|-----------|
| 2c-1 ✅ | Scaffold `games.js`: imports, state vars, column picker | `_COL_DEFAULTS`, `applyColVisibility`, `_initColPicker` + TV/games state |
| 2c-2 ✅ | Migrate filter helpers | `goToGames`, `onGamesFilter/SearchChange`, `loadFilterOptions`, `toggleFavoritesFilter`, `_refreshTagFilter`, `toggleRowFavorite` |
| 2c-3 ✅ | Migrate core load/render | `loadGames`, `renderPagination`, `_renderGamesGrid`, `setGamesView`, `setPlayStatus` |
| 2c-4 ✅ | Migrate game panel | `openGamePanel`, `closeGamePanel`, all `gp*` and `_gp*` functions, `loadSaveBackupsResult` |
| 2c-5 ✅ | Migrate TV mode | `enterTvMode`, `exitTvMode`, `loadTvGrid`, `_renderTvGrid`, `_tvMoveFocus`, `_updateTvInfoBar` |
| 2c-6 ✅ | Wire into `main.js` | import all exports + add to `Object.assign(window, {...})` |
| 2c-7 ✅ | Remove migrated code from `app.js` | Delete all migrated functions + state vars + `_initColPicker()` bottom call |
| 2d | Create `js/tabs/overview.js` — overview, wizard, heatmap, charts | `static/js/tabs/overview.js` |

**2d subtasks:**

| ID | Task | Functions |
|----|------|-----------|
| 2d-1 ✅ | Scaffold `overview.js`: imports + small helpers | `_relTime`, `_emptyState`, `card`, `_getPlatformLogo` |
| 2d-2 ✅ | Migrate heatmap + charts | `_renderActivityHeatmap`, `_getHeatmapColor`, `_handleHeatmapHover`, `_renderMonthlyChart`, `_loadNewGameSuggestion` |
| 2d-3 ✅ | Migrate overview load + platform grid | `loadOverview`, `_renderPlatformGrid` |
| 2d-4 ✅ | Migrate wizard | `showWizard`, `closeWizard`, `wizardAutoDetect`, `startSetup`, `_renderWizSteps`, `_pollSetupProgress`, `_showSetupResult`, `wizardGoToOrganize` |
| 2d-5 ✅ | Wire into `main.js` | import all exports + `Object.assign(window, {...})` |
| 2d-6 ✅ | Remove migrated code from `app.js` | Delete all migrated functions |
| 2e | Create `js/tabs/esde.js` — ES-DE status, BIOS checker, RetroArch check | `loadEsdeStatus`, `loadBiosStatus`, `loadRetroArchCheck` |
| 2f ✅ | Create `js/tabs/tools.js` — CHD, CSO, ZIP, M3U, multidisc, N64, LPL, library structure | `doConvertChd`, `doConvertCso`, `doCleanupZips`, `doCleanupCueBin`, `doExtractZip`, `doGenerateM3U`, `autodetectM3UFolders`, `doVerifyMultidisc`, `doN64Scan`, `doN64Convert`, `doExportLpl`, `createLibraryStructure`, `organizeLibrary` |
| 2g ✅ | Extend `esde.js` — RA check + all RA helpers | `doRaCheck`, `_renderRaResult`, `filterRaByPlatform`, `_raGoToPage`, `discardRaNoSupport`, `_copyText`, `_googleQuery`, `_archiveOrgUrl`, `_openArchiveOrg`, `_copyArchiveOrgLink` |

**2e subtasks:**

| ID | Task | Functions |
|----|------|-----------|
| 2e-1 ✅ | Scaffold `esde.js` + migrate all 3 functions | `loadEsdeStatus`, `loadBiosStatus`, `loadRetroArchCheck` |
| 2e-2 ✅ | Wire into `main.js` | import all exports + `Object.assign(window, {...})` |
| 2e-3 ✅ | Remove migrated code from `app.js` | Delete all migrated functions |
| 2f | Create `js/tabs/tools.js` — CHD, CSO, ZIP, M3U, multidisc, N64, LPL, library structure | `doConvertChd`, `doConvertCso`, `doCleanupZips`, `doCleanupCueBin`, `doExtractZip`, `doGenerateM3U`, `autodetectM3UFolders`, `doVerifyMultidisc`, `doN64Scan`, `doN64Convert`, `doExportLpl`, `createLibraryStructure`, `organizeLibrary` |
| 2g ✅ | Extend `esde.js` — RA check + all RA helpers | `doRaCheck`, `_renderRaResult`, `filterRaByPlatform`, `_raGoToPage`, `discardRaNoSupport`, `_copyText`, `_googleQuery`, `_archiveOrgUrl`, `_openArchiveOrg`, `_copyArchiveOrgLink` |
| 2h ✅ | Extend `esde.js` — health check, platform health, operations timeline | `doHealthCheck`, `_renderHealthResult`, `_healthIssueRow`, `_filterHealthIssues`, `togglePlatformHealth`, `loadPlatformHealth`, `loadOperationsTimeline` |
| 2i ✅ | Extend `esde.js` — junk, orphaned saves, doctor, folder analysis, unmatched | `doJunkScan`, `junkToggleCat/SelectAll/CatCheck/Delete`, `doFindOrphans`, `doDeleteOrphans`, `doMoveOrphansToArchive`, `moveOrphanedSave`, `doFolderAnalysis`, `loadUnmatchedDiagnosis`, `doLibraryDoctor`, `doctorMoveRom/DeleteDir/ResolveAll` |
| 2j ✅ | Extend `esde.js` — library report | `generateReport`, `showReportTab`, all `_renderReport*`, `exportReportHtml` |
| 2k ✅ | Move sync leftovers → `sync.js` | `doSync`, `_renderSyncResult`, `loadSaveComparison`, `doLibraryDiff` |
| 2l ✅ | Move global infra → `main.js` / `state.js` | `showTab`, `setDevice`, `_applyDeviceName`, `_deviceRoot`, `toggleSidebar`, `onGlobalSearch`, `initTheme`, `setTheme`, `_applyTheme`, `toggleTheme`, `stopJob`, `openHtmlReport`, notifications, clipboard, init block |
| 2-final ✅ | Delete `app.js` | Only after 2e–2l are all done |

---

## Now — Quick fixes (carry-over from Day 23)

| ID | Task | Where |
|----|------|-------|
| B-test | Verify `_apply_ra_conflicts`: winner gets renamed, loser goes to `_descartados/` | `handlers/duplicates.py` — see `bugs/duplicados.md` |

**B-test subtasks:**

| ID | Task | Functions/Files |
|----|------|----|
| B-test-1 | UI prerequisite: disable "Resolver por RA" until RA Check runs | `static/js/tabs/duplicates.js` — check `ra_cache` exists, show hint |
| B-test-2 | Auto-rename winner: after discarding loser, move winner to canonical name | `handlers/duplicates.py::_apply_ra_conflicts` — rename source → target, update DB |
| B-test-3 | Better diagnostics: improve hint text, show cache status, guide next steps | `handlers/duplicates.py` — enhance response with `next_step` field |
| B-test-4 | Test with real data: verify winner renamed + moved, loser in _descartados/, DB updated | Run full scenario: RA Check → Build Plan → Apply RA → Verify |

| ID | Task | Where |
|----|------|-------|
| D2 | rclone handler: route files to `saves_remote` or `states_remote` by extension | `sync/rclone_transport.py` |

---

## User feedback — Device connectivity & Database issues

Extracted from testing session (2026-03-31). These are design/UX issues affecting core workflows.

| ID | Task | Priority | Notes |
|----|------|----------|-------|
| UX-1 | **Device connectivity indicator** — Show on startup cards if Android SD is NOT plugged in | High | Currently no visual feedback; app shows DB as connected even when unplugged. Prevents accidental operations on wrong device. |
| UX-2 | **Block operations on inactive device** — Prevent "Ejecutar cambios" when target device (consola android) is not plugged in | High | Safety guard. Currently UI allows applying changes to disconnected Android device. |
| DB-1 | **Metadata cache flag** — Add boolean in games table to mark files already scraped (found no metadata) | Medium | Avoid re-scraping same files repeatedly. Allows "Check metadata BEFORE scraping" workflow. |
| DB-2 | **Orphaned record cleanup** — Clean up DB entries when files are deleted from disk | Medium | Currently unclear if `os.remove()` in delete workflows triggers DB cleanup. Verify and document cleanup policy. |
| DUP-3 | **Rename "Colisión de plan" resolution** — If 2 files have same canonical name, offer delete-from-duplicates instead of rename | Medium | User feedback: rename-based conflict resolution is confusing for duplicates. Duplicates should just be deleted, not renamed to different canon names. |
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
