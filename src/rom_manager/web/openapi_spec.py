"""OpenAPI 3.0 specification for Retro Vault's REST API (S38-3).

Generated at runtime so the server URL reflects the actual host/port.
Served at GET /api/openapi.json.
"""
from __future__ import annotations


def build_spec(host: str, port: int) -> dict:
    server_url = f"http://{host}:{port}"

    # Reusable components
    job_status_resp = {
        "description": "Job started or already running",
        "content": {"application/json": {"schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["started", "already_running"]}
            }
        }}}
    }
    ok_resp = {
        "description": "Success",
        "content": {"application/json": {"schema": {"type": "object"}}}
    }
    error_resp = {
        "description": "Error",
        "content": {"application/json": {"schema": {
            "type": "object",
            "properties": {"error": {"type": "string"}}
        }}}
    }

    def get(summary: str, tags: list[str], params: list[dict] | None = None,
            resp_desc: str = "Success") -> dict:
        op: dict = {"summary": summary, "tags": tags,
                    "responses": {"200": {"description": resp_desc,
                                         "content": {"application/json": {"schema": {"type": "object"}}}}}}
        if params:
            op["parameters"] = params
        return op

    def post(summary: str, tags: list[str], body_desc: str = "JSON body") -> dict:
        return {
            "summary": summary, "tags": tags,
            "requestBody": {"required": False, "content": {
                "application/json": {"schema": {"type": "object", "description": body_desc}}
            }},
            "responses": {
                "200": ok_resp["content"] and ok_resp or ok_resp,
                "400": error_resp["content"] and error_resp or error_resp,
            }
        }

    def qs(*names: str) -> list[dict]:
        return [{"name": n, "in": "query", "schema": {"type": "string"}} for n in names]

    paths: dict = {

        # ── Status & jobs ─────────────────────────────────────────────────
        "/api/status": {"get": get(
            "Library summary (games, saves, assets, last scan)", ["Status"])},
        "/api/job-status": {"get": get(
            "Poll all background job states and results", ["Status"])},
        "/api/local-url": {"get": get(
            "Return the server's local URL (for QR generation)", ["Status"])},
        "/api/health-schedule": {"get": get(
            "Health check schedule: last run, next run, overdue flag", ["Health"])},
        "/api/stop-job": {"post": post(
            "Cancel a running background job", ["Status"], '{"job": "scan|health_check|scrape|…"}')},

        # ── Games ─────────────────────────────────────────────────────────
        "/api/games": {"get": get(
            "Paginated list of ROMs", ["Games"],
            params=qs("root", "page", "per_page", "q", "platform", "status", "fav", "tag", "sort"))},
        "/api/game": {"get": get(
            "Single game detail by id or source_path", ["Games"],
            params=qs("id", "source_path"))},
        "/api/games/filter-options": {"get": get(
            "Available filter values (platforms, tags, statuses)", ["Games"])},
        "/api/game-tags": {"get": get(
            "Tags for a specific game", ["Games"], params=qs("game_id"))},
        "/api/tags": {"get": get(
            "All tags in the library", ["Games"])},
        "/api/tag": {"post": post(
            "Add or remove a tag on a game", ["Games"], '{"game_id":1,"tag":"RPG","action":"add|remove"}')},
        "/api/toggle-favorite": {"post": post(
            "Toggle favorite flag on a game", ["Games"], '{"game_id":1}')},
        "/api/set-play-status": {"post": post(
            "Set play status (unplayed/playing/completed/…)", ["Games"],
            '{"game_id":1,"status":"completed"}')},
        "/api/set-metadata": {"post": post(
            "Save notes and custom metadata for a game", ["Games"],
            '{"game_id":1,"notes":"…","user_rating":4}')},
        "/api/stateshot": {"post": post(
            "Log a manual playtime session", ["Games"],
            '{"game_id":1,"minutes":45}')},
        "/api/game-sync-history": {"get": get(
            "Sync history for a specific game", ["Games"], params=qs("game_id"))},
        "/api/launch": {"post": post(
            "Launch a ROM with the configured RetroArch core", ["Games"],
            '{"source_path":"…"}')},

        # ── Library management ────────────────────────────────────────────
        "/api/platform-stats": {"get": get(
            "ROM count per platform", ["Library"], params=qs("root"))},
        "/api/plan": {"post": post(
            "Build a rename plan (dry-run)", ["Library"])},
        "/api/apply": {"post": post(
            "Execute the rename plan", ["Library"], '{"keep_both":false}')},
        "/api/match": {"post": post(
            "Match unresolved ROMs against No-Intro/Redump catalogs", ["Library"])},
        "/api/fix-platforms": {"post": post(
            "Backfill missing platform data from folder names", ["Library"])},
        "/api/duplicates": {"get": get(
            "List SHA1 duplicate groups", ["Library"])},
        "/api/duplicates/delete": {"post": post(
            "Delete a specific duplicate file", ["Library"], '{"source_path":"…"}')},
        "/api/duplicates/delete-all": {"post": post(
            "Delete all non-preferred duplicates in a group", ["Library"],
            '{"sha1":"…","keep_path":"…"}')},
        "/api/duplicates/exclude": {"post": post(
            "Exclude a path from duplicate detection", ["Library"], '{"source_path":"…"}')},
        "/api/missing": {"get": get(
            "ROMs in catalog not present in library (missing collection)",
            ["Library"], params=qs("platform"))},
        "/api/library-diff": {"get": get(
            "Compare PC vs Android library — files present on one side only",
            ["Library"])},
        "/api/library-doctor": {"get": get(
            "Diagnose misplaced ROMs and structural issues", ["Library"],
            params=qs("root"))},
        "/api/doctor-move-rom": {"post": post(
            "Move a ROM to its correct platform folder", ["Library"],
            '{"source_path":"…","target_dir":"…"}')},
        "/api/doctor-delete-dir": {"post": post(
            "Delete an empty or junk directory", ["Library"], '{"dir":"…"}')},
        "/api/organize-library": {"post": post(
            "Auto-organize library: move ROMs to correct platform folders", ["Library"])},
        "/api/library-report": {"get": get(
            "Full health report (multidisc, orphan saves, health check, CHD pending)",
            ["Library"], params=qs("root"))},
        "/api/junk-scan": {"post": post(
            "Scan for junk files (.tmp, .DS_Store, thumbs.db, …)", ["Library"],
            '{"path":"…"}')},
        "/api/junk-delete": {"post": post(
            "Delete a specific junk file", ["Library"], '{"source_path":"…"}')},
        "/api/folder-analysis": {"post": post(
            "Analyse a folder: file types, sizes, unknown files", ["Library"],
            '{"path":"…"}')},
        "/api/operations-timeline": {"get": get(
            "Rename/sync operation log (last N operations)", ["Library"],
            params=qs("limit"))},

        # ── Sync ─────────────────────────────────────────────────────────
        "/api/sync": {"post": post(
            "Sync all cloud save sources (rclone)", ["Sync"],
            '{"dry_run":true}')},
        "/api/sync-log": {"get": get(
            "Recent sync operations log", ["Sync"])},
        "/api/rclone-status": {"get": get(
            "Check rclone binary availability and version", ["Sync"])},
        "/api/auto-sync-status": {"get": get(
            "Auto-sync daemon state and last result", ["Sync"])},
        "/api/auto-sync-toggle": {"post": post(
            "Enable or disable the auto-sync daemon", ["Sync"],
            '{"enabled":true}')},
        "/api/auto-sync-save": {"post": post(
            "Save auto-sync settings (direction, path, policy)", ["Sync"])},
        "/api/save-comparison": {"get": get(
            "Compare local vs remote save timestamps", ["Sync"])},

        # ── Cable sync ────────────────────────────────────────────────────
        "/api/cable-sync": {"post": post(
            "Sync saves via USB cable (ADB or filesystem)", ["Cable Sync"],
            '{"direction":"pc_to_anbernic|anbernic_to_pc|newest","use_adb":true,"dry_run":false}')},
        "/api/cable-sync-preview": {"get": get(
            "Preview what cable sync would transfer", ["Cable Sync"],
            params=qs("direction", "pc_path", "ab_path", "use_adb"))},
        "/api/cable-sync-log": {"get": get(
            "Download cable sync operations log", ["Cable Sync"])},
        "/api/adb-devices": {"get": get(
            "List connected ADB devices", ["Cable Sync"])},
        "/api/adb-scan": {"post": post(
            "Scan Android device library via ADB", ["Cable Sync"],
            '{"android_path":"…"}')},
        "/api/test-adb-path": {"post": post(
            "Verify an ADB binary path", ["Cable Sync"], '{"adb":"…"}')},

        # ── Health ────────────────────────────────────────────────────────
        "/api/health-check": {"post": post(
            "Re-hash all ROMs and detect corruption (slow)", ["Health"])},
        "/api/notify-test": {"post": post(
            "Send a test Windows desktop toast notification", ["Health"])},

        # ── Scraper ───────────────────────────────────────────────────────
        "/api/scrape": {"post": post(
            "Batch-scrape metadata from ScreenScraper", ["Scraper"],
            '{"platform":"gba","limit":50}')},
        "/api/scrape-single": {"post": post(
            "Scrape a single ROM by id", ["Scraper"], '{"game_id":1}')},
        "/api/scrape-summary": {"get": get(
            "Scraped vs total counts per platform", ["Scraper"])},
        "/api/ss-quota": {"get": get(
            "ScreenScraper API quota for the current user", ["Scraper"])},

        # ── RetroAchievements ─────────────────────────────────────────────
        "/api/ra-check": {"post": post(
            "Cross-reference library MD5s against RetroAchievements", ["RetroAchievements"],
            '{"platform":"gba"}')},
        "/api/ra-check.csv": {"get": get(
            "Download last RA check results as CSV", ["RetroAchievements"])},
        "/api/ra-duplicates": {"get": get(
            "Duplicates where one version has RA support and the other doesn't",
            ["RetroAchievements"])},
        "/api/ra-duplicates/discard": {"post": post(
            "Delete the version without RA support from a duplicate pair",
            ["RetroAchievements"], '{"source_path":"…"}')},
        "/api/ra-duplicates/discard-all": {"post": post(
            "Delete all non-RA versions from all duplicate pairs",
            ["RetroAchievements"])},
        "/api/ra-check/discard-no-support": {"post": post(
            "Delete ROMs with no RA support (confirmed no achievements)",
            ["RetroAchievements"], '{"platform":"gba"}')},
        "/api/resolve-duplicate-ra": {"post": post(
            "Keep the RA-compatible version and discard the other",
            ["RetroAchievements"], '{"keep_path":"…","discard_path":"…"}')},
        "/api/apply-ra-conflicts": {"post": post(
            "Bulk-resolve all RA duplicate conflicts", ["RetroAchievements"])},

        # ── Inbox ─────────────────────────────────────────────────────────
        "/api/inbox-count": {"get": get(
            "Count of files waiting in the inbox folder", ["Inbox"])},
        "/api/inbox-status": {"get": get(
            "Last inbox pipeline run result", ["Inbox"])},
        "/api/inbox-watcher-status": {"get": get(
            "Inbox watcher daemon state", ["Inbox"])},
        "/api/inbox-scan": {"post": post(
            "Analyse inbox folder contents (detect platforms)", ["Inbox"],
            '{"inbox_path":"…"}')},
        "/api/inbox-run": {"post": post(
            "Process inbox: extract, detect, rename, place", ["Inbox"],
            '{"inbox_path":"…","target_root":"…","delete_source":false}')},

        # ── Tools ─────────────────────────────────────────────────────────
        "/api/convert-chd": {"post": post(
            "Convert CUE/BIN or GDI sets to CHD", ["Tools"],
            '{"source_path":"…","delete_source":false}')},
        "/api/convert-cso": {"post": post(
            "Convert CSO/ZSO to ISO (PSP)", ["Tools"],
            '{"source_path":"…","delete_source":false}')},
        "/api/convert-n64": {"post": post(
            "Convert N64 .v64/.n64 ROM to .z64", ["Tools"],
            '{"source_path":"…"}')},
        "/api/n64-scan": {"get": get(
            "Scan a folder and report N64 ROM formats", ["Tools"],
            params=qs("folder"))},
        "/api/extract-zip": {"post": post(
            "Extract ZIP files in a folder (skips MAME sets)", ["Tools"],
            '{"path":"…","delete_source":false}')},
        "/api/generate-m3u": {"post": post(
            "Generate .m3u playlists for multi-disc sets", ["Tools"],
            '{"path":"…"}')},
        "/api/verify-multidisc": {"post": post(
            "Verify multi-disc sets for completeness", ["Tools"],
            '{"path":"…"}')},
        "/api/orphaned-saves": {"get": get(
            "List save files with no matching ROM", ["Tools"],
            params=qs("root"))},
        "/api/orphaned-saves/delete": {"post": post(
            "Delete a specific orphaned save", ["Tools"], '{"source_path":"…"}')},
        "/api/orphaned-saves/move": {"post": post(
            "Move a save to match its ROM stem", ["Tools"],
            '{"source_path":"…","target_path":"…"}')},
        "/api/orphaned-saves/move-to-archive": {"post": post(
            "Move all orphaned saves to _huerfanos/ archive folder", ["Tools"],
            '{"root":"…"}')},
        "/api/test-chdman": {"post": post(
            "Verify chdman binary path", ["Tools"], '{"chdman":"…"}')},
        "/api/test-maxcso": {"post": post(
            "Verify maxcso binary path", ["Tools"], '{"maxcso":"…"}')},
        "/api/test-path": {"post": post(
            "Check if a filesystem path exists", ["Tools"], '{"path":"…"}')},
        "/api/catalog-status": {"get": get(
            "Loaded DAT catalog stats (No-Intro, Redump, Arcade)", ["Tools"])},
        "/api/import-dats": {"post": post(
            "Import DAT files from a folder into the catalog store", ["Tools"],
            '{"folder":"…"}')},
        "/api/import-arcade-catalog": {"post": post(
            "Import MAME/FBNeo arcade catalog DAT", ["Tools"], '{"folder":"…"}')},

        # ── ES-DE / Gamelists ─────────────────────────────────────────────
        "/api/export-gamelists": {"post": post(
            "Generate gamelist.xml per platform (EmulationStation format)", ["Gamelists"],
            '{"output_dir":"…","platform":"gba"}')},
        "/api/export-pegasus": {"post": post(
            "Export Pegasus Frontend metadata.pegasus.txt files", ["Gamelists"],
            '{"output_dir":"…"}')},
        "/api/export-lpl": {"post": post(
            "Export RetroArch .lpl playlist files", ["Gamelists"],
            '{"output_dir":"…"}')},
        "/api/esde-status": {"get": get(
            "ES-DE installation status and gamelist paths", ["Gamelists"])},
        "/api/create-library-structure": {"post": post(
            "Create standard ES-DE folder structure", ["Gamelists"],
            '{"base_path":"…"}')},
        "/api/copy-assets-to-esde": {"post": post(
            "Copy scraped images to ES-DE media folder", ["Gamelists"],
            '{"source_root":"…","esde_root":"…"}')},
        "/api/disc-folders": {"get": get(
            "List multi-disc platform folders in the library", ["Gamelists"])},
        "/api/bios-status": {"get": get(
            "BIOS file presence check per platform", ["Gamelists"],
            params=qs("root"))},

        # ── Backup & Reports ──────────────────────────────────────────────
        "/api/backup-now": {"post": post(
            "Create a versioned backup of all save files now", ["Backup"])},
        "/api/manual-backups": {"get": get(
            "List available manual save backups", ["Backup"], params=qs("game_id"))},
        "/api/save-backups": {"get": get(
            "List versioned backups for a specific game", ["Backup"],
            params=qs("id"))},
        "/api/restore-backup": {"post": post(
            "Restore a save file from a backup version", ["Backup"],
            '{"backup_path":"…","target_path":"…"}')},
        "/api/db-backup": {"get": get(
            "Download a copy of the SQLite database", ["Backup"])},
        "/api/report.json": {"get": get(
            "Full library report as JSON", ["Reports"])},
        "/api/report.csv": {"get": get(
            "Full library report as CSV", ["Reports"])},
        "/api/report/html": {"get": get(
            "HTML health report (multidisc, orphans, CHD pending, RA support)",
            ["Reports"], params=qs("root"))},
        "/api/export-library": {"get": get(
            "Export complete library metadata as JSON", ["Reports"])},
        "/api/export-missing": {"get": get(
            "Export missing ROMs list as CSV", ["Reports"],
            params=qs("platform"))},
        "/api/export-wishlist": {"post": post(
            "Export wishlist to CSV", ["Reports"])},
        "/api/wishlist": {
            "get": get("List wishlist entries", ["Reports"]),
            "post": post("Add a game to the wishlist", ["Reports"],
                         '{"title":"…","platform":"…","notes":"…"}'),
        },
        "/api/logs": {"get": get(
            "Download application log file", ["Reports"],
            params=qs("module"))},

        # ── Collection / Overview ─────────────────────────────────────────
        "/api/collection-stats": {"get": get(
            "Aggregated stats for the Overview dashboard", ["Collection"])},
        "/api/collection-stats-v2": {"get": get(
            "Extended stats including playtime heatmap data", ["Collection"])},
        "/api/platform-stats": {"get": get(
            "ROM count per platform", ["Collection"], params=qs("root"))},
        "/api/assets": {"get": get(
            "List scraped asset files per platform", ["Collection"],
            params=qs("root", "platform"))},
        "/api/asset-image": {"get": get(
            "Serve a scraped cover image", ["Collection"],
            params=qs("path"))},

        # ── Config & Auth ─────────────────────────────────────────────────
        "/api/config": {
            "get": get("Return current configuration", ["Config"]),
            "post": post("Update configuration fields", ["Config"],
                         '{"library.library_root":"E:/ROMs","notifications.desktop":true}'),
        },
        "/api/set-pin": {"post": post(
            "Set or change the web UI PIN", ["Auth"], '{"pin":"1234"}')},
        "/api/clear-pin": {"post": post(
            "Remove PIN authentication", ["Auth"])},
        "/api/auth/status": {"get": get(
            "Check authentication state of current session", ["Auth"])},
        "/api/auth/logout": {"post": post(
            "Invalidate current session cookie", ["Auth"])},

        # ── Setup ─────────────────────────────────────────────────────────
        "/api/wizard-detect": {"get": get(
            "Auto-detect RetroArch install, ADB device, and library path", ["Setup"])},
        "/api/setup-status": {"get": get(
            "First-run wizard completion state", ["Setup"])},
        "/api/setup-run": {"post": post(
            "Execute first-run setup pipeline", ["Setup"],
            '{"library_root":"…","retroarch_path":"…"}')},
        "/api/migrate-split-db": {"post": post(
            "Migrate legacy single-DB to split PC/Android databases", ["Setup"])},
        "/api/retroarch-check": {"get": get(
            "Detect installed RetroArch and available cores", ["Setup"])},
        "/api/system-status": {"get": get(
            "Aggregate status of all external tools and data dependencies", ["Status"])},
        "/api/detect-cloud-folder": {"get": get(
            "Detect locally-installed cloud clients (Dropbox, OneDrive, Google Drive)", ["Setup"])},
        "/api/anbernic-setup.sh": {"get": get(
            "Generate personalised Android/Termux setup shell script", ["Setup"])},
        "/api/rclone-export-config": {"get": get(
            "Export the local rclone configuration file for Termux import", ["Setup"])},
    }

    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Retro Vault API",
            "version": "1.0.0",
            "description": (
                "REST API for Retro Vault — local ROM library manager and save sync tool. "
                "All endpoints return JSON unless noted. "
                "Long-running operations start a background job; "
                "poll GET /api/job-status every 2 s until the job finishes."
            ),
            "contact": {"url": "https://github.com/Rcerezo-dev/Retro-gaming-companion"},
        },
        "servers": [{"url": server_url, "description": "Local server"}],
        "tags": [
            {"name": "Status",             "description": "Server and job status"},
            {"name": "Games",              "description": "ROM catalogue and game metadata"},
            {"name": "Library",            "description": "Scanning, renaming, duplicates, organisation"},
            {"name": "Sync",               "description": "Cloud save synchronisation (rclone)"},
            {"name": "Cable Sync",         "description": "USB/ADB direct sync to Android console"},
            {"name": "Health",             "description": "ROM integrity and desktop notifications"},
            {"name": "Scraper",            "description": "ScreenScraper metadata and cover art"},
            {"name": "RetroAchievements",  "description": "Achievement support cross-reference"},
            {"name": "Inbox",              "description": "Automatic inbox pipeline"},
            {"name": "Tools",              "description": "CHD/CSO/N64 conversion, ZIP extraction, M3U"},
            {"name": "Gamelists",          "description": "ES-DE, Pegasus and RetroArch gamelist export"},
            {"name": "Backup",             "description": "Save file versioned backup and restore"},
            {"name": "Reports",            "description": "Library exports and HTML health reports"},
            {"name": "Collection",         "description": "Overview stats, cover art, collection gallery"},
            {"name": "Config",             "description": "Application configuration"},
            {"name": "Auth",               "description": "PIN authentication"},
            {"name": "Setup",              "description": "First-run wizard and migration"},
        ],
        "paths": paths,
    }
