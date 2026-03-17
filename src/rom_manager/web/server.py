from __future__ import annotations

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository
from rom_manager.planner import build_plan
from rom_manager.planner.operation_planner import FormatOptions
from rom_manager.reports import build_report, to_csv, to_json
from rom_manager.web.frontend import HTML
from rom_manager.web.response_builders import (
    _json_response, _test_path, _list_drives, _utc_now_str,
    _parse_format_opts, _repo_for_path,
    _build_junk_scan, _build_library_report, _build_status,
    _build_games, _count_companion_saves, _build_plan,
    _build_duplicates, _build_library_diff, _build_duplicates_two_repos,
    _build_folder_analysis, _build_ra_duplicates,
    _build_assets, _build_sync_log, _build_config,
    _build_scrape_summary, _build_cable_sync_preview,
)
from rom_manager.web.cable_sync_daemon import _auto_sync_loop, _sd_card_sync_loop
from rom_manager.web.inbox_pipeline import (
    _build_inbox_scan, _run_setup_pipeline, _run_inbox_pipeline, _watcher_now,
)

# ── Background job state ──────────────────────────────────────────────────────
_job_lock = threading.Lock()
_jobs: dict[str, bool] = {
    "scan": False, "match": False, "sync": False,
    "convert_chd": False, "scrape": False,
    "extract_zip": False, "health_check": False,
    "ra_check": False, "cable_sync": False,
    "apply": False, "inbox": False, "setup": False,
}
_job_results: dict[str, dict] = {}


def _start_job(name: str, fn: "Callable[[], None]") -> dict:
    """Start a background job if not already running.

    Returns ``{"status": "started"}`` or ``{"status": "already_running"}``.
    *fn* is responsible for setting ``_job_results[name]`` and clearing
    ``_jobs[name]`` in its own finally block.
    """
    from typing import Callable  # noqa: F401
    with _job_lock:
        if _jobs[name]:
            return {"status": "already_running"}
        _jobs[name] = True
    threading.Thread(target=fn, daemon=True).start()
    return {"status": "started"}


# Canonical ES-DE platform folder names (platform detector name → ES folder)
_ES_PLATFORM_FOLDERS: dict[str, str] = {
    "NES":              "nes",
    "SNES":             "snes",
    "Nintendo 64":      "n64",
    "Game Boy":         "gb",
    "Game Boy Color":   "gbc",
    "Game Boy Advance": "gba",
    "Nintendo DS":      "nds",
    "Nintendo 3DS":     "3ds",
    "GameCube":         "gamecube",
    "Wii":              "wii",
    "Wii U":            "wiiu",
    "Nintendo Switch":  "switch",
    "Master System":    "mastersystem",
    "Game Gear":        "gamegear",
    "Sega Genesis":     "megadrive",
    "Sega Mega Drive":  "megadrive",
    "Dreamcast":        "dreamcast",
    "PlayStation":      "psx",
    "PlayStation 2":    "ps2",
    "PlayStation 3":    "ps3",
    "PSP":              "psp",
    "PS Vita":          "psvita",
    "Sega Saturn":      "saturn",
    "Saturn":           "saturn",      # alias legacy
    "Atari 2600":       "atari2600",
    "Atari 5200":       "atari5200",
    "Atari 7800":       "atari7800",
    "Atari Lynx":       "atarilynx",
    "Atari Jaguar":     "atarijaguar",
    "Neo Geo":          "neogeo",
    "PC Engine":        "pcengine",
    "Sega 32X":         "sega32x",
    "Sega CD":          "segacd",
    "Arcade":           "arcade",
}

_STANDARD_PLATFORM_FOLDERS: tuple[str, ...] = (
    # Nintendo
    "nes", "snes", "n64", "gb", "gbc", "gba", "nds", "3ds",
    "gamecube", "wii", "wiiu", "switch",
    # Sony
    "psx", "ps2", "ps3", "psp", "psvita",
    # Sega
    "megadrive", "mastersystem", "gamegear", "dreamcast", "saturn", "sega32x", "segacd",
    # Atari
    "atari2600", "atari5200", "atari7800", "atarilynx", "atarijaguar",
    # Otros
    "neogeo", "pcengine",
    # Arcade
    "arcade",
)

_chd_progress: dict = {}     # {"current": int, "total": int, "current_file": str}
_scrape_progress: dict = {}  # {"current": int, "total": int, "found": int, "current_game": str}
_zip_progress: dict = {}     # {"current": int, "total": int, "current_file": str}
_health_progress: dict = {}  # {"current": int, "total": int, "current_file": str}
_ra_progress: dict = {}      # {"current": int, "total": int, "current_file": str}
_cable_progress: dict = {}   # {"copied": int, "total_files": int, "bytes_copied": int, "bytes_total": int, "speed_bps": float, "current_file": str}
_scan_progress: dict = {}    # {"files_seen": int, "roms_detected": int, "current_path": str}
_apply_progress: dict = {}   # {"current": int, "total": int, "current_file": str}
_inbox_progress: dict = {}    # {"step": str, "step_num": int, "total_steps": int, "current_file": str, "processed": int, "total": int}
_inbox_watcher_status: dict = {"watching": False, "last_check": None, "pending_files": 0}
_setup_progress: dict = {}   # {"step": str, "step_num": int, "total_steps": int, "current_file": str, "pct": int}
_scan_cancel:   threading.Event = threading.Event()
_cable_cancel:  threading.Event = threading.Event()
_chd_cancel:    threading.Event = threading.Event()
_zip_cancel:    threading.Event = threading.Event()
_health_cancel: threading.Event = threading.Event()
_ra_cancel:     threading.Event = threading.Event()
_scrape_cancel: threading.Event = threading.Event()
_match_cancel:  threading.Event = threading.Event()
_logger = logging.getLogger(__name__)

# ── Auto-sync daemon state ─────────────────────────────────────────────────────
_auto_sync_enabled: bool = True
_auto_sync_last_devices: set = set()   # serial numbers seen in last poll
_auto_sync_status: dict = {"state": "waiting", "last_sync_at": None, "last_device": None, "last_error": None}

# ── SD card daemon state ────────────────────────────────────────────────────────
_sd_sync_status: dict = {"state": "waiting", "last_sync_at": None, "drive": None}


def _handle_catalog_status(config: AppConfig) -> dict:
    """List DAT files in the nointro/redump catalog directories with quick entry counts."""
    def _scan_dir(directory: Path) -> list[dict]:
        files: list[dict] = []
        if not directory.exists():
            return files
        for f in sorted(directory.iterdir()):
            if f.suffix.lower() not in (".dat", ".xml") or not f.is_file():
                continue
            try:
                data = f.read_bytes()
                count = data.count(b"<game")
            except OSError:
                count = 0
            try:
                size = f.stat().st_size
            except OSError:
                size = 0
            files.append({"name": f.name, "size_bytes": size, "entries": count})
        return files

    nointro = _scan_dir(config.catalogs_nointro_dir)
    redump = _scan_dir(config.catalogs_redump_dir)
    return {
        "nointro": nointro,
        "redump": redump,
        "total_nointro_entries": sum(f["entries"] for f in nointro),
        "total_redump_entries": sum(f["entries"] for f in redump),
        "nointro_dir": str(config.catalogs_nointro_dir),
        "redump_dir": str(config.catalogs_redump_dir),
    }


def _handle_import_dats(data: dict, config: AppConfig) -> dict:
    """Copy DAT/XML files from source_folder to the appropriate catalog subdirectory."""
    import shutil

    source = Path(data.get("source_folder", "")).expanduser()
    if not source.exists() or not source.is_dir():
        return {"error": f"Carpeta no encontrada: {source}"}

    imported: list[dict] = []
    errors: list[dict] = []

    for f in sorted(source.iterdir()):
        if f.suffix.lower() not in (".dat", ".xml") or not f.is_file():
            continue
        try:
            with f.open("rb") as fh:
                sample = fh.read(2048)
            # Must look like a Logiqx DAT
            if b"<datafile" not in sample and b"<game" not in sample:
                continue
            # Heuristic: filename contains "redump" → Redump, else No-Intro
            fname_lower = f.name.lower()
            if "redump" in fname_lower:
                dest_dir = config.catalogs_redump_dir
                catalog_type = "redump"
            else:
                dest_dir = config.catalogs_nointro_dir
                catalog_type = "nointro"
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest_dir / f.name)
            imported.append({"name": f.name, "catalog": catalog_type})
        except Exception as exc:
            errors.append({"name": f.name, "error": str(exc)})

    return {"imported": imported, "errors": errors, "total": len(imported)}


def _handle_rclone_status(config: AppConfig) -> dict:
    """Check if rclone is installed and list configured remotes."""
    import subprocess

    installed = False
    version = ""
    remotes: list[str] = []

    try:
        proc = subprocess.run(
            [config.rclone_binary, "version"],
            capture_output=True, text=True, timeout=8,
        )
        installed = proc.returncode == 0
        if installed:
            version = proc.stdout.split("\n")[0].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    if installed:
        try:
            rem_proc = subprocess.run(
                [config.rclone_binary, "listremotes"],
                capture_output=True, text=True, timeout=8,
            )
            remotes = [r.strip() for r in rem_proc.stdout.strip().split("\n") if r.strip()]
        except Exception:
            pass

    return {
        "installed": installed,
        "version": version,
        "remotes": remotes,
        "binary": config.rclone_binary,
    }


def _handle_wizard_detect(config: AppConfig) -> dict:
    """Auto-detect RetroArch installation and connected ADB devices for the first-run wizard."""
    import os
    import re

    # --- 1. Scan common RetroArch installation paths ---
    candidates: list[Path] = []
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        candidates.append(Path(appdata) / "RetroArch")
    for drive_letter in ("C", "D", "E"):
        candidates += [
            Path(f"{drive_letter}:\\RetroArch-Win64"),
            Path(f"{drive_letter}:\\RetroArch"),
            Path(f"{drive_letter}:\\Program Files\\RetroArch"),
            Path(f"{drive_letter}:\\Program Files (x86)\\RetroArch"),
        ]

    library_root_suggestion = None
    for ra_dir in candidates:
        cfg_path = ra_dir / "retroarch.cfg"
        if not cfg_path.exists():
            continue
        try:
            text = cfg_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = re.search(r'^content_directory\s*=\s*"(.+)"', text, re.MULTILINE)
        if m:
            candidate = m.group(1).strip()
            if candidate not in ("", "default"):
                library_root_suggestion = candidate
                break
        # Fallback: use the RetroArch dir itself as a hint
        if library_root_suggestion is None:
            library_root_suggestion = str(ra_dir)

    # --- 2. Check ADB for connected devices ---
    android_suggestion = None
    device_display = None
    adb_ok = False
    try:
        from rom_manager.sync.adb_transport import list_devices
        devs = list_devices(config.adb)
        adb_ok = True
        ready_devs = [d for d in devs if d.ready]
        if ready_devs:
            dev = ready_devs[0]
            device_display = dev.display or dev.serial
            # Use config android path if set, else a sensible default
            android_suggestion = config.anbernic_root or "/storage/emulated/0/RetroArch/roms"
    except Exception:
        pass

    return {
        "library_root_suggestion": library_root_suggestion,
        "android_suggestion": android_suggestion,
        "device_display": device_display,
        "adb_ok": adb_ok,
    }


def make_handler(repository: LibraryRepository, config: AppConfig, repository_android: LibraryRepository | None = None):
    logger = logging.getLogger(__name__)
    # If no android repo is provided (e.g. called from CLI), use a no-op fallback = same as PC repo
    _repo_android: LibraryRepository = repository_android if repository_android is not None else repository

    def _get_repo(path_str: str) -> LibraryRepository:
        return _repo_for_path(path_str, repository, _repo_android, config)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass  # suppress default request logging

        # ── GET ──────────────────────────────────────────────────────────────

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)

            try:
                if path == "/":
                    self._send(200, "text/html; charset=utf-8", HTML.encode())
                elif path.startswith("/static/"):
                    filename = path[len("/static/"):]
                    # Security: only allow simple filenames, no path traversal
                    if "/" in filename or "\\" in filename or not filename:
                        self._send(404, "text/plain", b"Not found")
                    else:
                        static_dir = Path(__file__).parent / "static"
                        file_path = static_dir / filename
                        if not file_path.exists() or not file_path.is_file():
                            self._send(404, "text/plain", b"Not found")
                        else:
                            ext = file_path.suffix.lower()
                            content_type = {
                                ".css": "text/css; charset=utf-8",
                                ".js":  "application/javascript; charset=utf-8",
                            }.get(ext, "application/octet-stream")
                            self._send(200, content_type, file_path.read_bytes())
                elif path == "/api/status":
                    src_root = qs.get("root", [None])[0] or None
                    self._send_json(_build_status(repository, src_root, project_root=config.project_root, repository_android=_repo_android, library_root=config.library_root))
                elif path == "/api/test-path":
                    self._send_json(_test_path(qs.get("path", [""])[0]))
                elif path == "/api/list-drives":
                    self._send_json(_list_drives())
                elif path == "/api/adb-devices":
                    try:
                        from rom_manager.sync.adb_transport import list_devices
                        devs = list_devices(config.adb)
                        self._send_json({
                            "devices": [
                                {"serial": d.serial, "state": d.state,
                                 "model": d.model, "product": d.product,
                                 "ready": d.ready, "display": d.display}
                                for d in devs
                            ],
                            "adb_path": config.adb,
                        })
                    except RuntimeError as exc:
                        self._send_json({"error": str(exc), "devices": []})
                elif path == "/api/test-adb-path":
                    serial  = qs.get("serial", [""])[0]
                    ap      = qs.get("path", ["/storage/emulated/0"])[0]
                    if not serial:
                        self._send_json({"accessible": False, "error": "serial requerido"})
                    else:
                        try:
                            from rom_manager.sync.adb_transport import AdbTransport
                            t = AdbTransport(config.adb, serial)
                            self._send_json(t.test_path(ap))
                        except Exception as exc:
                            self._send_json({"accessible": False, "error": str(exc)})
                elif path == "/api/library-report":
                    rpt_path = qs.get("path", [None])[0] or str(config.library_root or "")
                    if not rpt_path:
                        self._send_json({"error": "path parameter required (or set library_root in config)"})
                    else:
                        _rpt_repo = _get_repo(rpt_path)
                        rpt = _build_library_report(rpt_path, _rpt_repo, config)
                        rpt["retroachievements"] = _job_results.get("ra_check") or {"note": "Ejecuta primero la comprobación de RetroAchievements en la pestaña Tools"}
                        rpt["chd"] = _job_results.get("convert_chd") or {"note": "Ejecuta primero la conversión CHD en la pestaña Tools"}
                        self._send_json(rpt)
                elif path == "/api/setup-status":
                    with _job_lock:
                        self._send_json({
                            "setup_running": _jobs["setup"],
                            "setup_progress": dict(_setup_progress) if _setup_progress else None,
                            "setup_result": _job_results.get("setup"),
                        })
                elif path == "/api/ra-duplicates":
                    self._send_json(_build_ra_duplicates(repository, config))
                elif path == "/api/report/html":
                    rpt_path = qs.get("path", [None])[0] or str(config.library_root or "")
                    if not rpt_path:
                        self._send(400, "text/plain; charset=utf-8",
                                   b"path parameter required (or set library_root in config)")
                    else:
                        from rom_manager.utils.library_report_html import generate_html_report
                        _rpt_repo = _get_repo(rpt_path)
                        rpt = _build_library_report(rpt_path, _rpt_repo, config)
                        rpt["retroachievements"] = _job_results.get("ra_check") or {}
                        rpt["chd"] = _job_results.get("convert_chd") or {}
                        html = generate_html_report(rpt)
                        self._send(200, "text/html; charset=utf-8", html.encode("utf-8"))
                elif path == "/api/games":
                    qs = parse_qs(parsed.query)
                    offset = int(qs.get("offset", ["0"])[0])
                    limit = min(int(qs.get("limit", ["100"])[0]), 500)
                    plat = qs.get("platform", [None])[0] or None
                    st = qs.get("status", [None])[0] or None
                    root = qs.get("root", [None])[0] or None
                    ft = qs.get("filetype", ["rom"])[0]
                    file_type = ft if ft in ("rom", "", "save") else None
                    search = qs.get("search", [None])[0] or None
                    play_status = qs.get("play_status", [None])[0] or None
                    _games_repo = _get_repo(root or "")
                    self._send_json(_build_games(_games_repo, offset=offset, limit=limit, platform=plat, status=st, source_root=root, file_type=file_type, search=search, play_status=play_status))
                elif path == "/api/plan":
                    opts = _parse_format_opts(qs)
                    source_root = qs.get("source_root", [None])[0] or None
                    _plan_repo = _get_repo(source_root or "")
                    self._send_json(_build_plan(_plan_repo, opts, frozenset(config.save_extensions), source_root=source_root, library_root=str(config.library_root) if config.library_root else None))
                elif path == "/api/library-diff":
                    self._send_json(_build_library_diff(repository, _repo_android, config))
                elif path == "/api/duplicates":
                    source_root = qs.get("source_root", [None])[0] or None
                    pc_root     = qs.get("pc_root",     [None])[0] or None
                    ab_root     = qs.get("ab_root",     [None])[0] or None
                    self._send_json(_build_duplicates_two_repos(repository, _repo_android, source_root=source_root, pc_root=pc_root, ab_root=ab_root))
                elif path == "/api/assets":
                    src_root = qs.get("root", [None])[0] or None
                    _assets_repo = _get_repo(src_root or "")
                    self._send_json(_build_assets(_assets_repo, src_root))
                elif path == "/api/sync-log":
                    self._send_json(_build_sync_log(repository))
                elif path == "/api/config":
                    self._send_json(_build_config(config))
                elif path == "/api/scrape-summary":
                    self._send_json(_build_scrape_summary(repository))
                elif path == "/api/job-status":
                    with _job_lock:
                        self._send_json({
                            "scan_running": _jobs["scan"],
                            "match_running": _jobs["match"],
                            "sync_running": _jobs["sync"],
                            "convert_chd_running": _jobs["convert_chd"],
                            "scrape_running": _jobs["scrape"],
                            "scan_result": _job_results.get("scan"),
                            "match_result": _job_results.get("match"),
                            "sync_result": _job_results.get("sync"),
                            "convert_chd_result": _job_results.get("convert_chd"),
                            "scrape_result": _job_results.get("scrape"),
                            "chd_progress": dict(_chd_progress) if _chd_progress else None,
                            "scrape_progress": dict(_scrape_progress) if _scrape_progress else None,
                            "extract_zip_running": _jobs["extract_zip"],
                            "zip_progress": dict(_zip_progress) if _zip_progress else None,
                            "health_check_running": _jobs["health_check"],
                            "health_progress": dict(_health_progress) if _health_progress else None,
                            "health_check_result": _job_results.get("health_check"),
                            "extract_zip_result": _job_results.get("extract_zip"),
                            "ra_check_running": _jobs["ra_check"],
                            "ra_progress": dict(_ra_progress) if _ra_progress else None,
                            "ra_check_result": _job_results.get("ra_check"),
                            "cable_sync_running": _jobs["cable_sync"],
                            "cable_progress": dict(_cable_progress) if _cable_progress else None,
                            "cable_sync_result": _job_results.get("cable_sync"),
                            "scan_progress": dict(_scan_progress) if _scan_progress else None,
                            "apply_running": _jobs["apply"],
                            "apply_progress": dict(_apply_progress) if _apply_progress else None,
                            "apply_result": _job_results.get("apply"),
                            "inbox_running": _jobs["inbox"],
                            "inbox_progress": dict(_inbox_progress) if _inbox_progress else None,
                            "inbox_result": _job_results.get("inbox"),
                            "setup_running": _jobs["setup"],
                            "setup_progress": dict(_setup_progress) if _setup_progress else None,
                            "setup_result": _job_results.get("setup"),
                        })
                elif path == "/api/test-chdman":
                    import subprocess
                    try:
                        r = subprocess.run(
                            [config.chdman],
                            capture_output=True, timeout=5,
                        )
                        # chdman exits with non-zero when called with no args but prints version
                        out = (r.stdout or r.stderr or b"").decode(errors="replace").strip()
                        first_line = out.splitlines()[0] if out else ""
                        self._send_json({"ok": True, "version": first_line, "path": config.chdman})
                    except FileNotFoundError:
                        self._send_json({"ok": False, "error": f"No encontrado: {config.chdman!r}"})
                    except Exception as exc:
                        self._send_json({"ok": False, "error": str(exc)})
                elif path == "/api/disc-folders":
                    # Return subfolders of library_root that look like disc-based platforms
                    _DISC_PLATFORMS = {
                        "psx", "ps1", "ps2", "ps3", "saturn", "dreamcast",
                        "gamecube", "gc", "wii", "wiiu", "3do", "cdi",
                        "pce-cd", "pcenginecd", "segacd", "megacd",
                        "neogeocd", "lynx",
                    }
                    _DISC_EXTS = frozenset({".cue", ".chd", ".iso", ".bin", ".mdf", ".img", ".ccd"})
                    root = config.library_root
                    if root and root.exists():
                        folders = []
                        for f in sorted(root.iterdir()):
                            if not f.is_dir():
                                continue
                            name_key = f.name.lower().replace(" ", "").replace("-", "")
                            if name_key not in {p.replace("-", "") for p in _DISC_PLATFORMS}:
                                continue
                            # Only include if folder actually contains disc files
                            has_disc = any(
                                child.suffix.lower() in _DISC_EXTS
                                for child in f.rglob("*") if child.is_file()
                            )
                            if has_disc:
                                folders.append(str(f))
                        self._send_json({"folders": folders, "library_root": str(root)})
                    else:
                        self._send_json({"folders": [], "library_root": None})
                elif path == "/api/orphaned-saves":
                    source = qs.get("path", [None])[0]
                    if not source:
                        self._send_json({"error": "path parameter required"})
                    else:
                        import re as _re
                        from rom_manager.utils.orphan_finder import find_orphaned_saves
                        orphans = find_orphaned_saves(Path(source).resolve(), config.save_extensions)

                        def _norm(s: str) -> str:
                            s = s.lower()
                            s = _re.sub(r"\s*[\(\[][^\)\]]+[\)\]]", "", s)
                            return s.strip()

                        # Load all ROMs from DB for fuzzy stem matching
                        with repository.connect() as _conn:
                            _all_games = _conn.execute(
                                "SELECT id, original_filename, source_path, platform "
                                "FROM games WHERE file_type='rom'"
                            ).fetchall()
                        _game_stems = [
                            (g, _norm(Path(g["original_filename"]).stem))
                            for g in _all_games
                        ]

                        orphan_list = []
                        for o in orphans:
                            norm_o = _norm(o.stem)
                            suggestions: list[dict] = []
                            if len(norm_o) >= 5:
                                for game, norm_g in _game_stems:
                                    if len(norm_g) >= 5 and (
                                        norm_g.startswith(norm_o[:6]) or
                                        norm_o.startswith(norm_g[:6])
                                    ):
                                        suggestions.append({
                                            "game_id": game["id"],
                                            "filename": game["original_filename"],
                                            "source_path": game["source_path"],
                                            "platform": game["platform"] or "",
                                        })
                                        if len(suggestions) >= 3:
                                            break
                            orphan_list.append({
                                "save_path": o.save_path, "stem": o.stem,
                                "extension": o.extension, "size_bytes": o.size_bytes,
                                "suggestions": suggestions,
                            })

                        self._send_json({"orphans": orphan_list, "total": len(orphans)})
                elif path == "/api/db-backup":
                    db_path = config.database_path
                    if not db_path.exists():
                        self._send(404, "text/plain", b"Database not found")
                    else:
                        self._send(200, "application/octet-stream", db_path.read_bytes(),
                                   extra_headers={"Content-Disposition": 'attachment; filename="library.sqlite"'})
                elif path == "/api/folder-analysis":
                    folder_path = qs.get("path", [None])[0] or None
                    if not folder_path:
                        self._send(400, "text/plain; charset=utf-8", b"path parameter required")
                    else:
                        self._send_json(_build_folder_analysis(folder_path, config))
                elif path == "/api/ra-check.csv":
                    result = _job_results.get("ra_check")
                    if not result or result.get("error") or not result.get("alternatives_csv"):
                        self._send(404, "text/plain", b"No RA check result available")
                    else:
                        body = result["alternatives_csv"].encode()
                        self._send(200, "text/csv; charset=utf-8", body,
                                   extra_headers={"Content-Disposition": 'attachment; filename="ra_alternatives.csv"'})
                elif path == "/api/asset-image":
                    gid = qs.get("game_id", [None])[0]
                    if not gid:
                        self._send(404, "text/plain; charset=utf-8", b"game_id required")
                        return
                    try:
                        with repository.connect() as _ic:
                            row = _ic.execute(
                                "SELECT box_art_path FROM game_metadata WHERE game_id = ?", (int(gid),)
                            ).fetchone()
                        if not row or not row["box_art_path"]:
                            self._send(404, "text/plain; charset=utf-8", b"no image")
                            return
                        img_path = Path(row["box_art_path"])
                        if not img_path.exists():
                            self._send(404, "text/plain; charset=utf-8", b"file not found")
                            return
                        ext = img_path.suffix.lower()
                        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png" if ext == ".png" else "image/octet-stream"
                        data_bytes = img_path.read_bytes()
                        self.send_response(200)
                        self.send_header("Content-Type", mime)
                        self.send_header("Content-Length", str(len(data_bytes)))
                        self.send_header("Cache-Control", "max-age=3600")
                        self.end_headers()
                        self.wfile.write(data_bytes)
                    except Exception as exc:
                        self._send(500, "text/plain; charset=utf-8", str(exc).encode())
                elif path == "/api/platform-stats":
                    src_root = qs.get("root", [None])[0] or None
                    _ps_repo = _get_repo(src_root or "")
                    with _ps_repo.connect() as _pc:
                        if src_root:
                            rows = _pc.execute(
                                "SELECT platform, COUNT(*) AS cnt FROM games "
                                "WHERE source_path LIKE ? AND file_type = 'rom' "
                                "GROUP BY platform ORDER BY cnt DESC",
                                [src_root.rstrip("/\\") + "%"],
                            ).fetchall()
                        else:
                            rows = _pc.execute(
                                "SELECT platform, COUNT(*) AS cnt FROM games "
                                "WHERE file_type = 'rom' "
                                "GROUP BY platform ORDER BY cnt DESC"
                            ).fetchall()
                    self._send_json({"platforms": [{"platform": r["platform"] or "?", "count": r["cnt"]} for r in rows]})
                elif path == "/api/junk-scan":
                    folder = qs.get("path", [None])[0] or None
                    if not folder:
                        self._send_json({"error": "path required"})
                    else:
                        self._send_json(_build_junk_scan(folder))
                elif path == "/api/cable-sync-preview":
                    self._send_json(_build_cable_sync_preview(qs, config))
                elif path == "/api/cable-sync-log":
                    log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
                    if log_path.exists():
                        with open(log_path, "r", encoding="utf-8", errors="replace") as _lf:
                            lines = _lf.readlines()
                        tail = "".join(lines[-500:])
                        self._send_json({"log": tail, "lines": len(lines)})
                    else:
                        self._send_json({"log": "", "lines": 0})
                elif path == "/api/wizard-detect":
                    self._send_json(_handle_wizard_detect(config))
                elif path == "/api/catalog-status":
                    self._send_json(_handle_catalog_status(config))
                elif path == "/api/rclone-status":
                    self._send_json(_handle_rclone_status(config))
                elif path == "/api/auto-sync-status":
                    self._send_json({
                        "enabled": _auto_sync_enabled,
                        "status": dict(_auto_sync_status),
                        "config": {
                            "direction": config.auto_sync_direction,
                            "conflict_policy": config.conflict_policy,
                            "android_path": config.auto_sync_android_path,
                        },
                    })
                elif path == "/api/sd-sync-status":
                    self._send_json(dict(_sd_sync_status))
                elif path == "/api/report.json":
                    report = build_report(repository)
                    body = to_json(report).encode()
                    self._send(200, "application/json; charset=utf-8", body,
                               extra_headers={"Content-Disposition": 'attachment; filename="report.json"'})
                elif path == "/api/report.csv":
                    report = build_report(repository)
                    body = to_csv(report).encode()
                    self._send(200, "text/csv; charset=utf-8", body,
                               extra_headers={"Content-Disposition": 'attachment; filename="report.csv"'})
                elif path == "/api/inbox-scan":
                    inbox_path_str = qs.get("path", [""])[0].strip() or config.inbox_path
                    if not inbox_path_str:
                        self._send_json({"error": "path parameter required (or set inbox.path in config.toml)"})
                    else:
                        self._send_json(_build_inbox_scan(inbox_path_str))
                elif path == "/api/inbox-status":
                    self._send_json({
                        "running": _jobs["inbox"],
                        "progress": dict(_inbox_progress) if _inbox_progress else None,
                        "result": _job_results.get("inbox"),
                    })
                elif path == "/api/inbox-watcher-status":
                    self._send_json(dict(_inbox_watcher_status))
                else:
                    self._send(404, "text/plain", b"Not found")
            except Exception as exc:
                body = json.dumps({"error": str(exc)}).encode()
                self._send(500, "application/json", body)

        # ── POST ─────────────────────────────────────────────────────────────

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path

            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data: dict = json.loads(raw) if raw else {}
            except Exception:
                data = {}

            try:
                if path == "/api/scan":
                    self._handle_scan(data)
                elif path == "/api/adb-scan":
                    self._handle_adb_scan(data)
                elif path == "/api/match":
                    self._handle_match()
                elif path == "/api/apply":
                    self._handle_apply(data)
                elif path == "/api/fix-platforms":
                    self._handle_fix_platforms()
                elif path == "/api/duplicates/delete":
                    self._handle_delete_duplicate(data)
                elif path == "/api/duplicates/delete-all":
                    self._handle_delete_all_duplicates()
                elif path == "/api/duplicates/exclude":
                    sha1 = data.get("sha1", "")
                    if sha1:
                        repository.exclude_duplicate_sha1(sha1)
                        self._send_json({"ok": True})
                    else:
                        self._send_error(400, "sha1 required")
                # D8-3: resolve conflicts keeping RA winner
                elif path == "/api/apply-ra-conflicts":
                    self._handle_apply_ra_conflicts(data)
                # D8-4: discard a single RA-duplicate file
                elif path == "/api/ra-duplicates/discard":
                    self._handle_ra_duplicate_discard(data)
                # D8-4: discard all files without RA support in every version group
                elif path == "/api/ra-duplicates/discard-all":
                    self._handle_ra_duplicate_discard_all()
                # Bulk discard games with NO RA support at all (from RA check)
                elif path == "/api/ra-check/discard-no-support":
                    self._handle_ra_discard_no_support()
                elif path == "/api/sync":
                    self._handle_sync(data)
                elif path == "/api/convert-chd":
                    self._handle_convert_chd(data)
                elif path == "/api/scrape":
                    self._handle_scrape(data)
                elif path == "/api/export-gamelists":
                    self._handle_export_gamelists(data)
                elif path == "/api/config":
                    self._handle_save_config(data)
                elif path == "/api/extract-zip":
                    self._handle_extract_zip(data)
                elif path == "/api/generate-m3u":
                    self._handle_generate_m3u(data)
                elif path == "/api/verify-multidisc":
                    self._handle_verify_multidisc(data)
                elif path == "/api/orphaned-saves/delete":
                    self._handle_delete_orphaned_saves(data)
                elif path == "/api/orphaned-saves/move":
                    self._handle_move_orphaned_save(data)
                elif path == "/api/health-check":
                    self._handle_health_check(data)
                elif path == "/api/cleanup-zips":
                    self._handle_cleanup_zips(data)
                elif path == "/api/cleanup-cue-bin":
                    self._handle_cleanup_cue_bin(data)
                elif path == "/api/stop-job":
                    job_name = data.get("job", "")
                    _cancel_map = {
                        "scan":         _scan_cancel,
                        "cable_sync":   _cable_cancel,
                        "convert_chd":  _chd_cancel,
                        "extract_zip":  _zip_cancel,
                        "health_check": _health_cancel,
                        "ra_check":     _ra_cancel,
                        "scrape":       _scrape_cancel,
                        "match":        _match_cancel,
                    }
                    if job_name in _cancel_map:
                        _cancel_map[job_name].set()
                    with _job_lock:
                        if job_name in _jobs:
                            _jobs[job_name] = False
                        _scan_progress.clear()
                    self._send_json({"status": "stopped", "job": job_name})
                elif path == "/api/ra-check":
                    self._handle_ra_check(data)
                elif path == "/api/cable-sync":
                    self._handle_cable_sync(data)
                elif path == "/api/auto-sync-toggle":
                    global _auto_sync_enabled
                    _auto_sync_enabled = not _auto_sync_enabled
                    config.auto_sync_enabled = _auto_sync_enabled
                    self._send_json({"enabled": _auto_sync_enabled})
                elif path == "/api/auto-sync-save":
                    self._handle_auto_sync_save(data)
                elif path == "/api/migrate-split-db":
                    self._handle_migrate_split_db()
                elif path == "/api/junk-delete":
                    paths_to_delete = data.get("paths", [])
                    dry_run = bool(data.get("dry_run", True))
                    deleted = 0
                    failed = 0
                    freed_bytes = 0
                    errors: list[str] = []
                    for fp in paths_to_delete:
                        try:
                            p = Path(fp)
                            if p.is_file():
                                sz = p.stat().st_size
                                if not dry_run:
                                    p.unlink()
                                deleted += 1
                                freed_bytes += sz
                        except OSError as exc:
                            failed += 1
                            errors.append(str(exc))
                    self._send_json({"deleted": deleted, "failed": failed, "freed_bytes": freed_bytes, "dry_run": dry_run, "errors": errors[:10]})
                elif path == "/api/set-play-status":
                    game_id = data.get("game_id")
                    status  = data.get("status") or None
                    if not game_id:
                        self._send_json({"error": "game_id required"})
                        return
                    _status_repo = _get_repo(data.get("source_path", ""))
                    _status_repo.set_play_status(int(game_id), status)
                    self._send_json({"ok": True})
                elif path == "/api/export-pegasus":
                    if not config.library_root:
                        self._send_json({"error": "library_root not configured"})
                        return
                    try:
                        from rom_manager.scraper.pegasus_writer import write_pegasus_metadata
                        result_peg = write_pegasus_metadata(config.library_root, repository)
                        self._send_json({"ok": True, "platforms": result_peg["platforms"], "games": result_peg["games"]})
                    except Exception as exc:
                        self._send_json({"error": str(exc)})
                elif path == "/api/import-dats":
                    self._send_json(_handle_import_dats(data, config))
                elif path == "/api/inbox-run":
                    self._handle_inbox_run(data)
                elif path == "/api/setup-run":
                    self._handle_setup_run(data)
                elif path == "/api/create-library-structure":
                    self._handle_create_library_structure(data)
                elif path == "/api/organize-library":
                    self._handle_organize_library(data)
                else:
                    self._send(404, "text/plain", b"Not found")
            except Exception as exc:
                body = json.dumps({"error": str(exc)}).encode()
                self._send(500, "application/json", body)

        # ── POST handlers ────────────────────────────────────────────────────

        def _handle_scan(self, data: dict) -> None:
            # Accept either a single source_path or a list source_paths
            raw_paths = data.get("source_paths") or []
            single = data.get("source_path", "").strip()
            if single and not raw_paths:
                raw_paths = [single]
            raw_paths = [p.strip() for p in raw_paths if str(p).strip()]
            if not raw_paths:
                self._send_json({"error": "source_path is required"})
                return
            quick = bool(data.get("quick", False))

            with _job_lock:
                if _jobs["scan"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["scan"] = True

            _scan_cancel.clear()
            _scan_progress.clear()

            def run() -> None:
                try:
                    from rom_manager.scanner import scan_library
                    from rom_manager.scanner.rom_scanner import ScanResult
                    total = ScanResult()

                    def _progress_cb(files_seen: int, roms: int, current_file: str = "") -> None:
                        _scan_progress.update({
                            "files_seen": files_seen,
                            "roms_detected": roms,
                            "current_path": str(source),
                            "current_file": current_file,
                        })

                    for raw in raw_paths:
                        source = Path(raw).resolve()
                        _scan_progress["current_path"] = str(source)
                        # Route to the correct DB based on whether path is under library_root
                        _scan_repo = _get_repo(str(source))
                        r = scan_library(
                            source, config, _scan_repo, logger, quick=quick,
                            stop_event=_scan_cancel, progress_cb=_progress_cb,
                        )
                        total.files_seen += r.files_seen
                        total.roms_detected += r.roms_detected
                        total.roms_skipped += r.roms_skipped
                        total.saves_detected += r.saves_detected
                        total.errors += r.errors
                    _job_results["scan"] = {
                        "result_ts": utc_now(),
                        "files_seen": total.files_seen,
                        "roms_detected": total.roms_detected,
                        "roms_skipped": total.roms_skipped,
                        "saves_detected": total.saves_detected,
                        "errors": total.errors,
                        "paths_scanned": len(raw_paths),
                        "pruned": total.pruned,
                        "cancelled": _scan_cancel.is_set(),
                    }
                    # D8-7: auto-generate library report cache after scan (background, non-blocking)
                    # Generate a cached report for every scanned path (PC and Android)
                    if not _scan_cancel.is_set():
                        for _rpt_path in raw_paths:
                            if not _rpt_path:
                                continue
                            def _cache_report(_p=_rpt_path):
                                try:
                                    _rpt_data = _build_library_report(_p, _get_repo(_p), config)
                                    _cache_dir = config.project_root / ".rommgr"
                                    _cache_dir.mkdir(parents=True, exist_ok=True)
                                    (_cache_dir / "last_report.json").write_text(
                                        json.dumps(_rpt_data, ensure_ascii=False), encoding="utf-8"
                                    )
                                except Exception:
                                    pass
                            threading.Thread(target=_cache_report, daemon=True).start()
                except Exception as exc:
                    _job_results["scan"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _scan_progress.clear()
                        _jobs["scan"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started"})

        def _handle_adb_scan(self, data: dict) -> None:
            """Scan files on an Android device via ADB and register them in the DB."""
            adb_serial   = data.get("adb_serial", "").strip()
            android_path = data.get("android_path", "/storage/emulated/0").strip().rstrip("/")

            if not adb_serial:
                self._send_json({"error": "adb_serial is required"})
                return

            with _job_lock:
                if _jobs["scan"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["scan"] = True

            def run() -> None:
                try:
                    from pathlib import PurePosixPath
                    from rom_manager.sync.adb_transport import AdbTransport
                    from rom_manager.detection.platform_detector import detect_platform
                    from rom_manager.detection.region_parser import parse_region_from_name
                    from rom_manager.detection.set_detector import detect_set_type
                    from rom_manager.scanner.rom_scanner import utc_now

                    transport  = AdbTransport(config.adb, adb_serial, timeout=120)
                    timestamp  = utc_now()
                    save_exts  = frozenset(config.save_extensions)
                    asset_exts = frozenset(config.frontend_asset_extensions)
                    excluded   = frozenset(d.lower() for d in config.excluded_directories)

                    # ADB scan always goes to the Android repository
                    _adb_repo = _repo_android
                    scan_run_id = _adb_repo.create_scan_run(android_path, timestamp)
                    roms = saves = assets = errors = 0
                    seen_paths: set[str] = set()

                    # Fetch the file list from the device (~1 round-trip)
                    all_files = transport.ls_recursive(android_path, timeout=180)

                    with _adb_repo.batch() as conn:
                        for fi in all_files:
                            ap = fi.android_path
                            seen_paths.add(ap)
                            parts = ap.split("/")
                            # Skip excluded directories (e.g. Android/, DCIM/, BIOS/)
                            if any(seg.lower() in excluded for seg in parts):
                                continue

                            name   = PurePosixPath(ap).name
                            suffix = PurePosixPath(ap).suffix.lower()
                            # Relative parent = the folder containing the file, relative to android_path
                            try:
                                rel_parent = str(PurePosixPath(ap).parent.relative_to(android_path))
                            except ValueError:
                                rel_parent = ""

                            try:
                                if suffix in save_exts:
                                    _adb_repo.upsert_save(
                                        original_path=ap,
                                        relative_parent=rel_parent,
                                        extension=suffix,
                                        size_bytes=fi.size,
                                        timestamp=timestamp,
                                        connection=conn,
                                    )
                                    saves += 1
                                elif suffix in asset_exts or name.lower() == "gamelist.xml":
                                    assets += 1  # don't store assets for ADB scan
                                elif suffix in {
                                    ".zip", ".7z", ".rar",          # archives
                                    ".xml", ".txt", ".log", ".db",  # data files
                                    ".apk", ".sh", ".py",           # executables
                                } or not suffix:
                                    pass  # ignore
                                else:
                                    # Treat as ROM — detect platform from path
                                    fake_path = Path(ap)
                                    platform  = detect_platform(fake_path)
                                    _adb_repo.upsert_game(
                                        original_filename=name,
                                        source_path=ap,
                                        platform=platform,
                                        file_type="rom",
                                        relative_parent=rel_parent,
                                        region=parse_region_from_name(name),
                                        extension=suffix,
                                        size_bytes=fi.size,
                                        mtime=int(fi.mtime),
                                        sha1="",
                                        md5="",
                                        crc32="",
                                        set_type=detect_set_type(fake_path),
                                        timestamp=timestamp,
                                        connection=conn,
                                    )
                                    roms += 1
                            except Exception as exc:
                                errors += 1
                                logger.error("ADB scan error for %s: %s", ap, exc)

                    pruned = _adb_repo.prune_stale_entries(android_path, seen_paths)
                    finished_at = utc_now()
                    _adb_repo.complete_scan_run(
                        scan_run_id,
                        finished_at=finished_at,
                        files_seen=len(all_files),
                        roms_detected=roms,
                        saves_detected=saves,
                        assets_detected=assets,
                        system_files_detected=0,
                        unknown_files_detected=0,
                        errors=errors,
                    )
                    _job_results["scan"] = {
                        "result_ts": utc_now(),
                        "files_seen": len(all_files),
                        "roms_detected": roms,
                        "roms_skipped": 0,
                        "saves_detected": saves,
                        "errors": errors,
                        "paths_scanned": 1,
                        "pruned": pruned,
                        "source": "adb",
                        "android_path": android_path,
                    }
                except Exception as exc:
                    _job_results["scan"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _jobs["scan"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started"})

        def _handle_match(self) -> None:
            def run() -> None:
                _match_cancel.clear()
                try:
                    from rom_manager.catalog.matcher import CatalogMatcher
                    matcher = CatalogMatcher(
                        nointro_dir=config.catalogs_nointro_dir,
                        redump_dir=config.catalogs_redump_dir,
                    )
                    games = repository.get_unresolved_games()
                    matched_high = matched_low = unmatched = 0
                    with repository.batch() as conn:
                        for game in games:
                            if _match_cancel.is_set():
                                break
                            result = matcher.match(game.sha1, game.original_filename)
                            if result is not None:
                                repository.update_match(
                                    game.source_path,
                                    canonical_title=result.title,
                                    match_confidence=result.confidence,
                                    catalog_source=result.catalog_source,
                                    connection=conn,
                                )
                                if result.confidence == "high":
                                    matched_high += 1
                                else:
                                    matched_low += 1
                            else:
                                unmatched += 1
                    _job_results["match"] = {
                        "total": len(games),
                        "matched_high": matched_high,
                        "matched_low": matched_low,
                        "unmatched": unmatched,
                        "cancelled": _match_cancel.is_set(),
                    }
                except Exception as exc:
                    _job_results["match"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _jobs["match"] = False

            self._send_json(_start_job("match", run))

        def _handle_fix_platforms(self) -> None:
            from rom_manager.detection.platform_detector import detect_platform
            updated = repository.backfill_platforms(detect_platform)
            self._send_json({"updated": updated})

        def _handle_create_library_structure(self, data: dict) -> None:
            """Create the canonical ES-DE folder structure under library_root (and optionally android_root)."""
            from pathlib import Path as _Path
            if not config.library_root:
                self._send_json({"error": "library_root no configurado"})
                return

            also_android = bool(data.get("also_android"))
            android_root_str = getattr(config, "android_root", None) or getattr(config, "ab_path", None)

            def _create_tree(root: _Path) -> tuple[list[str], list[str]]:
                created: list[str] = []
                skipped: list[str] = []
                for folder in _STANDARD_PLATFORM_FOLDERS:
                    plat_dir = root / folder
                    if not plat_dir.exists():
                        plat_dir.mkdir(parents=True, exist_ok=True)
                        created.append(folder)
                    else:
                        skipped.append(folder)
                    for sub in ("media/images", "media/videos"):
                        sub_dir = plat_dir / _Path(sub)
                        if not sub_dir.exists():
                            sub_dir.mkdir(parents=True, exist_ok=True)
                            created.append(f"{folder}/{sub}")
                for special in ("saves", "states", "bios", "inbox", "screenshots"):
                    d = root / special
                    if not d.exists():
                        d.mkdir(parents=True, exist_ok=True)
                        created.append(special)
                    else:
                        skipped.append(special)
                # Per-platform saves/ and states/ subfolders — keeps each console's saves separate
                for folder in _STANDARD_PLATFORM_FOLDERS:
                    for special_sub in ("saves", "states"):
                        sub_dir = root / special_sub / folder
                        if not sub_dir.exists():
                            sub_dir.mkdir(parents=True, exist_ok=True)
                            created.append(f"{special_sub}/{folder}")
                return created, skipped

            pc_root = _Path(config.library_root)
            pc_created, pc_skipped = _create_tree(pc_root)

            android_result: dict = {}
            if also_android and android_root_str:
                android_root = _Path(android_root_str)
                if android_root.exists():
                    ab_created, ab_skipped = _create_tree(android_root)
                    android_result = {"root": str(android_root), "created": ab_created, "skipped": ab_skipped}
                else:
                    android_result = {"root": str(android_root), "error": "Ruta no accesible — conecta la tarjeta SD o el dispositivo primero"}

            self._send_json({
                "created": pc_created,
                "skipped": pc_skipped,
                "root": str(pc_root),
                "android": android_result,
            })

        def _handle_organize_library(self, data: dict) -> None:
            """Move ROMs → platform folders, saves → saves/{platform}/, BIOS candidates → bios/. Updates DB."""
            import shutil as _shutil
            from pathlib import Path as _Path
            dry_run = data.get("dry_run", True)
            if not config.library_root:
                self._send_json({"error": "library_root no configurado"})
                return
            root = _Path(config.library_root)
            saves_dir = root / "saves"
            bios_dir = root / "bios"

            save_exts = frozenset(getattr(config, "save_extensions", [
                ".sav", ".srm", ".state", ".ogg", ".rtc",
            ]))
            # BIOS heuristic: .bin files not matched as ROMs, or known BIOS filenames
            _known_bios_names = frozenset({
                "scph1001.bin", "scph5500.bin", "scph5501.bin", "scph5502.bin",
                "scph7001.bin", "scph7502.bin", "scph10000.bin",
                "bios_CD_E.bin", "bios_CD_J.bin", "bios_CD_U.bin",
                "dc_boot.bin", "dc_flash.bin",
                "gba_bios.bin",
                "bios7.bin", "bios9.bin", "firmware.bin",
                "ym2608_adpcm_rom.bin",
            })

            moves_roms: list[dict] = []
            moves_saves: list[dict] = []
            moves_bios: list[dict] = []
            errors: list[str] = []

            # 1. ROMs + their associated saves
            with repository.connect() as conn:
                rows = conn.execute(
                    "SELECT id, source_path, platform FROM games WHERE source_path IS NOT NULL"
                ).fetchall()
            for row in rows:
                game_id, src_str, platform = row[0], row[1], row[2] or ""
                src = _Path(src_str)
                if not src.exists():
                    continue
                es_folder = _ES_PLATFORM_FOLDERS.get(platform, "")
                if not es_folder:
                    continue
                target_dir = root / es_folder
                target = target_dir / src.name
                if src == target:
                    # ROM already in place — still check for sibling saves to centralise
                    pass
                else:
                    moves_roms.append({"source": str(src), "target": str(target), "platform": platform, "filename": src.name})
                    if not dry_run:
                        try:
                            target_dir.mkdir(parents=True, exist_ok=True)
                            if target.exists():
                                errors.append(f"Conflicto ROM: {src.name} ya existe en {es_folder}/")
                            else:
                                _shutil.move(str(src), str(target))
                                with repository.connect() as conn:
                                    conn.execute(
                                        "UPDATE games SET source_path = ?, updated_at = ? WHERE source_path = ?",
                                        (str(target), _utc_now_str(), src_str),
                                    )
                                    conn.commit()
                        except Exception as exc:
                            errors.append(f"ROM {src.name}: {exc}")

                # Move sibling saves (same stem, save extensions) → saves/{platform}/
                # Each platform gets its own subfolder so saves never mix across consoles.
                plat_save_dir = saves_dir / es_folder if es_folder else saves_dir
                for save_ext in save_exts:
                    sibling = src.with_suffix(save_ext)
                    if sibling.exists() and sibling.parent != plat_save_dir:
                        save_target = plat_save_dir / sibling.name
                        moves_saves.append({"source": str(sibling), "target": str(save_target), "platform": platform})
                        if not dry_run:
                            try:
                                plat_save_dir.mkdir(parents=True, exist_ok=True)
                                if not save_target.exists():
                                    _shutil.move(str(sibling), str(save_target))
                            except Exception as exc:
                                errors.append(f"Save {sibling.name}: {exc}")

            # 2. BIOS candidates: scan root + immediate subdirs for known BIOS filenames or .bin not in DB
            with repository.connect() as conn:
                known_paths = {row[0] for row in conn.execute("SELECT source_path FROM games").fetchall()}
            for candidate in list(root.rglob("*.bin")):
                if candidate.parent.name in ("bios", "saves", "states", "inbox", "screenshots"):
                    continue  # already in special folder
                if any(p.name in ("saves", "states") for p in candidate.parents):
                    continue  # inside saves/{platform}/ or states/{platform}/
                if str(candidate) in known_paths:
                    continue  # it's a ROM we know about
                if candidate.name.lower() not in _known_bios_names:
                    continue  # unknown .bin — don't touch it silently
                bios_target = bios_dir / candidate.name
                if candidate == bios_target:
                    continue
                moves_bios.append({"source": str(candidate), "target": str(bios_target), "filename": candidate.name})
                if not dry_run:
                    try:
                        bios_dir.mkdir(parents=True, exist_ok=True)
                        if not bios_target.exists():
                            _shutil.move(str(candidate), str(bios_target))
                    except Exception as exc:
                        errors.append(f"BIOS {candidate.name}: {exc}")

            total_preview = (moves_roms + moves_saves + moves_bios)[:40]
            self._send_json({
                "dry_run": dry_run,
                "moves_roms": len(moves_roms),
                "moves_saves": len(moves_saves),
                "moves_bios": len(moves_bios),
                "errors": errors,
                "preview": total_preview if dry_run else [],
            })

        def _handle_sync(self, data: dict) -> None:
            dry_run = data.get("dry_run", True)
            with _job_lock:
                if _jobs["sync"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["sync"] = True

            def run() -> None:
                try:
                    from rom_manager.sync.rclone_transport import RcloneTransport
                    from rom_manager.sync.save_syncer import sync_saves
                    from pathlib import Path as _Path

                    sources = config.sync_sources
                    if not sources:
                        _job_results["sync"] = {
                            "error": "No hay fuentes de sync configuradas. "
                                     "Añade [[sync.sources]] en config.toml."
                        }
                        return

                    transport = RcloneTransport(rclone=config.rclone_binary)
                    all_results = []
                    for source in sources:
                        saves_dir = _Path(source.local_dir)
                        if not saves_dir.exists():
                            all_results.append({
                                "name": source.name,
                                "local_dir": source.local_dir,
                                "remote": source.remote,
                                "error": f"Directorio no encontrado: {source.local_dir}",
                                "uploaded": 0, "downloaded": 0,
                                "up_to_date": 0, "conflicts": 0, "errors": 0,
                                "decisions": [],
                            })
                            continue
                        # sync_all=True → pass empty tuple so list_local_saves includes all files
                        exts = tuple() if source.sync_all else config.save_extensions
                        try:
                            result, decisions = sync_saves(
                                saves_dir,
                                source.remote,
                                transport=transport,
                                repository=repository,
                                save_extensions=exts,
                                dry_run=dry_run,
                            )
                            all_results.append({
                                "name": source.name,
                                "local_dir": source.local_dir,
                                "remote": source.remote,
                                "uploaded": result.uploaded,
                                "downloaded": result.downloaded,
                                "up_to_date": result.up_to_date,
                                "conflicts": result.conflicts,
                                "errors": result.errors,
                                "decisions": [
                                    {"action": d.action, "relative": d.relative}
                                    for d in decisions if d.action != "up_to_date"
                                ],
                            })
                        except Exception as exc:
                            all_results.append({
                                "name": source.name,
                                "local_dir": source.local_dir,
                                "remote": source.remote,
                                "error": str(exc),
                                "uploaded": 0, "downloaded": 0,
                                "up_to_date": 0, "conflicts": 0, "errors": 0,
                                "decisions": [],
                            })

                    _job_results["sync"] = {
                        "dry_run": dry_run,
                        "sources": all_results,
                        # Aggregated totals
                        "uploaded":   sum(r.get("uploaded",   0) for r in all_results),
                        "downloaded": sum(r.get("downloaded", 0) for r in all_results),
                        "up_to_date": sum(r.get("up_to_date", 0) for r in all_results),
                        "conflicts":  sum(r.get("conflicts",  0) for r in all_results),
                        "errors":     sum(r.get("errors",     0) for r in all_results),
                    }
                except Exception as exc:
                    _job_results["sync"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _jobs["sync"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started", "dry_run": dry_run})

        def _handle_convert_chd(self, data: dict) -> None:
            source_path_str = data.get("source_path", "").strip()
            if not source_path_str:
                self._send_json({"error": "source_path is required"})
                return
            dry_run = data.get("dry_run", True)
            delete_source = data.get("delete_source", False)

            with _job_lock:
                if _jobs["convert_chd"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["convert_chd"] = True

            def run() -> None:
                _chd_cancel.clear()
                try:
                    from rom_manager.converters.chd_converter import (
                        find_cue_files, convert_to_chd, parse_bins_from_cue,
                        ConversionResult, ConversionSummary,
                    )
                    source = Path(source_path_str).resolve()
                    cue_files = find_cue_files(source)
                    total = len(cue_files)
                    _chd_progress.update({"current": 0, "total": total, "current_file": ""})

                    summary = ConversionSummary()
                    for idx, cue_path in enumerate(cue_files, 1):
                        if _chd_cancel.is_set():
                            break
                        _chd_progress.update({"current": idx, "total": total, "current_file": cue_path.name})
                        chd_path = cue_path.with_suffix(".chd")
                        bin_paths = parse_bins_from_cue(cue_path)
                        if dry_run:
                            if chd_path.exists():
                                summary.skipped += 1
                                summary.results.append(ConversionResult(
                                    cue_path=cue_path, chd_path=chd_path, bin_paths=bin_paths,
                                    success=False, error="Output .chd already exists — would skip."))
                            else:
                                summary.converted += 1
                                summary.results.append(ConversionResult(
                                    cue_path=cue_path, chd_path=chd_path, bin_paths=bin_paths,
                                    success=True))
                        else:
                            result = convert_to_chd(cue_path, chdman=config.chdman, delete_source=delete_source)
                            summary.results.append(result)
                            if result.success:
                                summary.converted += 1
                            elif result.error and "already exists" in result.error:
                                summary.skipped += 1
                            else:
                                summary.failed += 1

                    _job_results["convert_chd"] = {
                        "dry_run": dry_run,
                        "converted": summary.converted,
                        "skipped": summary.skipped,
                        "failed": summary.failed,
                        "cancelled": _chd_cancel.is_set(),
                        "results": [
                            {
                                "cue": r.cue_path.name,
                                "chd": r.chd_path.name,
                                "success": r.success,
                                "error": r.error or "",
                            }
                            for r in summary.results
                        ],
                    }
                except Exception as exc:
                    _job_results["convert_chd"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _chd_progress.clear()
                        _jobs["convert_chd"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started", "dry_run": dry_run})

        def _handle_save_config(self, data: dict) -> None:
            from rom_manager.config import write_config_toml, load_config
            allowed = {
                "library.library_root", "library.anbernic_root", "sync.remote",
                "screenscraper.user", "screenscraper.pass",
                "screenscraper.dev_id", "screenscraper.dev_pass",
                "tools.chdman", "tools.adb",
                "retroachievements.api_key",
                "sync.auto_sync_enabled", "sync.auto_sync_direction",
                "sync.auto_sync_android_path", "sync.conflict_policy",
                "inbox.path", "inbox.target_root",
                "inbox.auto_process", "inbox.delete_source",
                "android.device_name",
                "web.host",
            }
            updates = {k: v for k, v in data.items() if k in allowed}
            if not updates:
                self._send_json({"error": "No recognised fields to update"})
                return
            write_config_toml(config.project_root, updates)
            # Reload in-memory config so changes take effect without restart
            global _auto_sync_enabled
            new_cfg = load_config(config.project_root)
            config.library_root = new_cfg.library_root
            config.anbernic_root = new_cfg.anbernic_root
            config.device_name = new_cfg.device_name
            config.rclone_remote = new_cfg.rclone_remote
            config.screenscraper_user = new_cfg.screenscraper_user
            config.screenscraper_pass = new_cfg.screenscraper_pass
            config.screenscraper_dev_id = new_cfg.screenscraper_dev_id
            config.screenscraper_dev_pass = new_cfg.screenscraper_dev_pass
            config.chdman = new_cfg.chdman
            config.adb = new_cfg.adb
            config.ra_api_key = new_cfg.ra_api_key
            config.auto_sync_enabled = new_cfg.auto_sync_enabled
            config.auto_sync_direction = new_cfg.auto_sync_direction
            config.auto_sync_android_path = new_cfg.auto_sync_android_path
            config.conflict_policy = new_cfg.conflict_policy
            config.inbox_path = new_cfg.inbox_path
            config.inbox_target_root = new_cfg.inbox_target_root
            config.inbox_auto_process = new_cfg.inbox_auto_process
            config.inbox_delete_source = new_cfg.inbox_delete_source
            config.sync_sources = new_cfg.sync_sources
            config.web_host = new_cfg.web_host
            _auto_sync_enabled = new_cfg.auto_sync_enabled
            self._send_json({"saved": list(updates.keys())})

        def _handle_auto_sync_save(self, data: dict) -> None:
            """Save auto-sync settings to config.toml and update in-memory config."""
            from rom_manager.config import write_config_toml, load_config
            global _auto_sync_enabled

            updates: dict = {}
            if "sync.auto_sync_direction" in data:
                updates["sync.auto_sync_direction"] = data["sync.auto_sync_direction"]
                config.auto_sync_direction = data["sync.auto_sync_direction"]
            if "sync.auto_sync_android_path" in data:
                updates["sync.auto_sync_android_path"] = data["sync.auto_sync_android_path"]
                config.auto_sync_android_path = data["sync.auto_sync_android_path"]
            if "sync.conflict_policy" in data:
                updates["sync.conflict_policy"] = data["sync.conflict_policy"]
                config.conflict_policy = data["sync.conflict_policy"]
            if "sync.auto_sync_enabled" in data:
                val = bool(data["sync.auto_sync_enabled"])
                updates["sync.auto_sync_enabled"] = val
                config.auto_sync_enabled = val
                _auto_sync_enabled = val

            if updates:
                write_config_toml(config.project_root, updates)

            self._send_json({"saved": list(updates.keys()), "enabled": _auto_sync_enabled})

        def _handle_cleanup_zips(self, data: dict) -> None:
            import os
            source_path_str = data.get("source_path", "").strip()
            if not source_path_str:
                self._send_json({"error": "source_path is required"})
                return
            source = Path(source_path_str).resolve()
            deleted = failed = 0
            freed_bytes = 0
            for zp in source.rglob("*.zip"):
                try:
                    freed_bytes += zp.stat().st_size
                    os.remove(zp)
                    deleted += 1
                except OSError:
                    failed += 1
            self._send_json({"deleted": deleted, "failed": failed, "freed_bytes": freed_bytes})

        def _handle_cleanup_cue_bin(self, data: dict) -> None:
            import os
            source_path_str = data.get("source_path", "").strip()
            if not source_path_str:
                self._send_json({"error": "source_path is required"})
                return
            source = Path(source_path_str).resolve()
            deleted = failed = skipped = 0
            freed_bytes = 0
            for cue in source.rglob("*.cue"):
                chd = cue.with_suffix(".chd")
                if not chd.exists():
                    skipped += 1
                    continue
                # Delete the .cue and all .bin files it references
                from rom_manager.converters.chd_converter import parse_bins_from_cue
                bins = parse_bins_from_cue(cue)
                for f in [cue, *bins]:
                    try:
                        freed_bytes += f.stat().st_size
                        os.remove(f)
                        deleted += 1
                    except OSError:
                        failed += 1
            self._send_json({"deleted": deleted, "failed": failed, "skipped": skipped, "freed_bytes": freed_bytes})

        def _handle_extract_zip(self, data: dict) -> None:
            source_path_str = data.get("source_path", "").strip()
            if not source_path_str:
                self._send_json({"error": "source_path is required"})
                return
            dry_run = bool(data.get("dry_run", True))
            delete_source = bool(data.get("delete_source", False))

            with _job_lock:
                if _jobs["extract_zip"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["extract_zip"] = True

            def run() -> None:
                _zip_cancel.clear()
                try:
                    from rom_manager.converters.zip_extractor import find_zip_files, extract_zip
                    source = Path(source_path_str).resolve()
                    zip_files = find_zip_files(source)
                    total = len(zip_files)
                    _zip_progress.update({"current": 0, "total": total, "current_file": ""})
                    extracted = skipped = failed = disc_sets = 0
                    results = []
                    for idx, zp in enumerate(zip_files, 1):
                        if _zip_cancel.is_set():
                            break
                        try:
                            rel = str(zp.relative_to(source))
                        except ValueError:
                            rel = zp.name
                        _zip_progress.update({"current": idx, "total": total, "current_file": rel})
                        r = extract_zip(zp, dry_run=dry_run, delete_source=delete_source)
                        if r.is_disc_set:
                            disc_sets += 1
                            skipped += 1
                        elif r.skipped_reason:
                            skipped += 1
                        elif r.error:
                            failed += 1
                        else:
                            extracted += 1
                        results.append({
                            "zip": rel,
                            "success": r.success,
                            "skipped_reason": r.skipped_reason,
                            "is_disc_set": r.is_disc_set,
                            "error": r.error,
                            "extracted": [f.name for f in r.extracted_files],
                        })
                    _job_results["extract_zip"] = {
                        "dry_run": dry_run,
                        "extracted": extracted,
                        "skipped": skipped,
                        "failed": failed,
                        "disc_sets": disc_sets,
                        "cancelled": _zip_cancel.is_set(),
                        "results": results,
                    }
                except Exception as exc:
                    _job_results["extract_zip"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _zip_progress.clear()
                        _jobs["extract_zip"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started", "dry_run": dry_run})

        def _handle_generate_m3u(self, data: dict) -> None:
            source_path_str = data.get("source_path", "").strip()
            if not source_path_str:
                self._send_json({"error": "source_path is required"})
                return
            dry_run = bool(data.get("dry_run", True))
            from rom_manager.utils.m3u_generator import generate_m3u_playlists
            source = Path(source_path_str).resolve()
            summary = generate_m3u_playlists(source, dry_run=dry_run)
            self._send_json({
                "dry_run": dry_run,
                "created": summary.created,
                "skipped": summary.skipped,
                "groups": [
                    {
                        "base_name": g.base_name,
                        "discs": [d.name for d in g.discs],
                        "m3u": g.m3u_path.name,
                    }
                    for g in summary.groups
                ],
            })

        def _handle_verify_multidisc(self, data: dict) -> None:
            source_path_str = data.get("source_path", "").strip()
            if not source_path_str:
                self._send_json({"error": "source_path is required"})
                return
            from rom_manager.utils.multidisc_verifier import verify_multidisc
            source = Path(source_path_str).resolve()
            summary = verify_multidisc(source, repository)
            self._send_json({
                "groups_ok": summary.groups_ok,
                "groups_with_issues": summary.groups_with_issues,
                "issues": [
                    {"base_name": i.base_name, "issue_type": i.issue_type,
                     "detail": i.detail, "platform": i.platform}
                    for i in summary.issues
                ],
            })

        def _handle_delete_orphaned_saves(self, data: dict) -> None:
            import os
            paths = data.get("paths", [])
            if not paths:
                self._send_json({"error": "paths list is required"})
                return
            deleted = failed = 0
            freed_bytes = 0
            for p in paths:
                try:
                    size = Path(p).stat().st_size if Path(p).exists() else 0
                    os.remove(p)
                    deleted += 1
                    freed_bytes += size
                except OSError:
                    failed += 1
            self._send_json({"deleted": deleted, "failed": failed, "freed_bytes": freed_bytes})

        def _handle_move_orphaned_save(self, data: dict) -> None:
            """Move an orphaned save file to sit alongside a matched ROM."""
            import shutil
            save_path = data.get("save_path", "").strip()
            game_path = data.get("game_path", "").strip()
            if not save_path or not game_path:
                self._send_json({"error": "save_path and game_path are required"})
                return
            save_file = Path(save_path)
            game_file = Path(game_path)
            if not save_file.exists():
                self._send_json({"error": f"Save file not found: {save_path}"})
                return
            if not game_file.parent.exists():
                self._send_json({"error": f"Game directory not found: {game_file.parent}"})
                return
            target = game_file.parent / (game_file.stem + save_file.suffix)
            if target.exists():
                self._send_json({"error": f"Target already exists: {target.name}"})
                return
            try:
                shutil.move(str(save_file), str(target))
            except OSError as exc:
                self._send_json({"error": str(exc)})
                return
            self._send_json({"moved": str(target), "from": save_path})

        def _handle_health_check(self, data: dict) -> None:
            def run() -> None:
                _health_cancel.clear()
                try:
                    from rom_manager.utils.health_checker import check_library_health

                    def progress_cb(current: int, total: int, filename: str) -> None:
                        _health_progress.update({"current": current, "total": total, "current_file": filename})

                    summary = check_library_health(repository, progress_cb=progress_cb, cancel_event=_health_cancel)
                    _job_results["health_check"] = {
                        "ok": summary.ok,
                        "corrupted": summary.corrupted,
                        "missing": summary.missing,
                        "cancelled": _health_cancel.is_set(),
                        "issues": [
                            {"source_path": r.source_path, "status": r.status,
                             "stored_sha1": r.stored_sha1[:12], "computed_sha1": r.computed_sha1[:12] if r.computed_sha1 else ""}
                            for r in summary.results
                        ],
                    }
                except Exception as exc:
                    _job_results["health_check"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _health_progress.clear()
                        _jobs["health_check"] = False

            self._send_json(_start_job("health_check", run))

        def _handle_scrape(self, data: dict) -> None:
            with _job_lock:
                if _jobs["scrape"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["scrape"] = True

            platform = data.get("platform") or None
            download_images = bool(data.get("images", False))
            limit = int(data.get("limit", 0))

            def run() -> None:
                _scrape_cancel.clear()
                try:
                    from rom_manager.scraper.screenscraper import ScreenScraperClient, download_image
                    from rom_manager.scraper.platform_ids import get_system_id
                    from rom_manager.scanner.rom_scanner import utc_now

                    if not config.screenscraper_user:
                        _job_results["scrape"] = {"error": "screenscraper credentials not configured"}
                        return

                    client = ScreenScraperClient(
                        user=config.screenscraper_user,
                        password=config.screenscraper_pass,
                        dev_id=config.screenscraper_dev_id,
                        dev_password=config.screenscraper_dev_pass,
                    )
                    games = repository.get_games_for_scraping(platform=platform)
                    if limit:
                        games = games[:limit]
                    total = len(games)
                    found = skipped = 0
                    _scrape_progress.update({"current": 0, "total": total, "found": 0, "current_game": ""})
                    with repository.batch() as conn:
                        for idx, game in enumerate(games, 1):
                            if _scrape_cancel.is_set():
                                break
                            _scrape_progress.update({
                                "current": idx,
                                "total": total,
                                "found": found,
                                "current_game": game["original_filename"],
                            })
                            sys_id = get_system_id(game["platform"])
                            result = client.search(
                                crc32=game["crc32"],
                                md5=game["md5"],
                                sha1=game["sha1"],
                                filename=game["original_filename"],
                                size_bytes=game["size_bytes"],
                                system_id=sys_id,
                            )
                            if result is None:
                                # Fallback: search by cleaned name (no hash)
                                name_hint = game.get("canonical_title") or game["original_filename"]
                                result = client.search_by_name(name_hint, system_id=sys_id)
                            if result is None:
                                skipped += 1
                                continue
                            box_art_path = ""
                            if download_images and result.box_art_url:
                                img_dir = Path(game["source_path"]).parent / "media" / "images"
                                stem = Path(game["original_filename"]).stem
                                ext = ".png" if ".png" in result.box_art_url.lower() else ".jpg"
                                dest = img_dir / f"{stem}{ext}"
                                download_image(result.box_art_url, dest)
                                box_art_path = str(dest)
                            repository.upsert_metadata(
                                game_id=game["id"],
                                ss_game_id=result.ss_game_id,
                                title=result.title, year=result.year,
                                genre=result.genre, publisher=result.publisher,
                                developer=result.developer, description=result.description,
                                rating=result.rating, box_art_url=result.box_art_url,
                                box_art_path=box_art_path, scraped_at=utc_now(),
                                connection=conn,
                            )
                            found += 1
                    _job_results["scrape"] = {
                        "total": total, "found": found, "skipped": skipped,
                        "cancelled": _scrape_cancel.is_set(),
                    }
                except Exception as exc:
                    _job_results["scrape"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _scrape_progress.clear()
                        _jobs["scrape"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started"})

        def _handle_export_gamelists(self, data: dict) -> None:
            from rom_manager.scraper.gamelist_writer import write_gamelist
            output_root = Path(data.get("output_dir") or "").resolve() if data.get("output_dir") else config.library_root
            if output_root is None:
                self._send_json({"error": "library_root not configured"})
                return
            platform_filter = data.get("platform") or None
            platforms = repository.get_scraped_platform_summary()
            if platform_filter:
                platforms = [p for p in platforms if p["platform"] == platform_filter]
            written = []
            for plat in platforms:
                if plat["scraped"] == 0:
                    continue
                entries = repository.get_metadata_for_platform(plat["platform"])
                if not entries:
                    continue
                slug = plat["platform"].lower().replace(" ", "").replace("/", "_")
                platform_dir = Path(output_root) / slug
                platform_dir.mkdir(parents=True, exist_ok=True)
                out = write_gamelist(platform_dir, entries)
                written.append({"platform": plat["platform"], "path": str(out), "entries": len(entries)})
            self._send_json({"written": written})

        def _handle_delete_duplicate(self, data: dict) -> None:
            import os
            from pathlib import Path as _Path
            game_id = data.get("game_id")
            source_path = data.get("source_path", "").strip()
            if not game_id or not source_path:
                self._send_json({"error": "game_id y source_path son obligatorios"})
                return
            p = _Path(source_path)
            if p.exists():
                try:
                    os.remove(str(p))
                except OSError as exc:
                    self._send_json({"error": f"No se pudo eliminar el archivo: {exc}"})
                    return
            # Clean up DB even if file was already missing
            repository.delete_game(int(game_id))
            self._send_json({"deleted": source_path})

        def _handle_delete_all_duplicates(self) -> None:
            import os
            from pathlib import Path as _Path
            groups = repository.get_duplicate_groups()
            deleted = 0
            failed = 0
            freed_bytes = 0
            for group in groups:
                for entry in group.entries[1:]:
                    p = _Path(entry.source_path)
                    if not p.exists():
                        repository.delete_game(entry.id)
                        deleted += 1
                        continue
                    try:
                        os.remove(str(p))
                        repository.delete_game(entry.id)
                        deleted += 1
                        freed_bytes += entry.size_bytes
                    except OSError:
                        failed += 1
            self._send_json({"deleted": deleted, "failed": failed, "freed_bytes": freed_bytes})

        def _handle_ra_check(self, data: dict) -> None:
            with _job_lock:
                if _jobs["ra_check"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["ra_check"] = True

            api_key = data.get("api_key", "").strip() or config.ra_api_key
            if not api_key:
                with _job_lock:
                    _jobs["ra_check"] = False
                self._send_json({"error": "RetroAchievements API key not configured"})
                return

            def run() -> None:
                _ra_cancel.clear()
                try:
                    from rom_manager.retroachievements.ra_checker import check_library, to_csv

                    cache_dir = config.data_dir / "ra_cache"

                    def progress_cb(current: int, total: int, filename: str) -> None:
                        _ra_progress.update({"current": current, "total": total, "current_file": filename})
                        if _ra_cancel.is_set():
                            raise InterruptedError("RA check cancelled")

                    try:
                        summary = check_library(
                            repository,
                            api_key,
                            cache_dir=cache_dir,
                            progress_cb=progress_cb,
                        )
                    except InterruptedError:
                        _job_results["ra_check"] = {"cancelled": True, "total": 0, "supported": 0,
                                                     "no_support_alternative": 0, "no_support": 0,
                                                     "no_md5": 0, "platform_unknown": 0,
                                                     "alternatives_csv": "", "alternatives": []}
                        return

                    alternatives_csv = ""
                    if summary.no_support_alternative > 0:
                        alternatives_csv = to_csv(summary)

                    _job_results["ra_check"] = {
                        "total": summary.total,
                        "supported": summary.supported,
                        "no_support_alternative": summary.no_support_alternative,
                        "no_support": summary.no_support,
                        "no_md5": summary.no_md5,
                        "platform_unknown": summary.platform_unknown,
                        "cancelled": _ra_cancel.is_set(),
                        "alternatives_csv": alternatives_csv,
                        # Only include first 50 "actionable" results to keep response size reasonable
                        "alternatives": [
                            {
                                "platform": r.platform,
                                "filename": r.original_filename,
                                "our_md5": r.our_md5[:12],
                                "ra_id": r.alternative.id,
                                "ra_title": r.alternative.title,
                                "ra_achievements": r.alternative.achievements,
                                "ra_points": r.alternative.points,
                            }
                            for r in summary.results
                            if r.status == "no_support_alternative" and r.alternative
                        ][:50],
                        # Full list of games with NO RA support (for bulk discard)
                        "no_support_entries": [
                            {"source_path": r.source_path, "filename": r.original_filename, "platform": r.platform}
                            for r in summary.results
                            if r.status == "no_support"
                        ],
                    }
                except Exception as exc:
                    _job_results["ra_check"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _ra_progress.clear()
                        _jobs["ra_check"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started"})

        def _handle_cable_sync(self, data: dict) -> None:
            import os
            import shutil

            pc_path_str       = data.get("pc_path", "").strip()
            anbernic_path_str = data.get("anbernic_path", "").strip()
            what              = data.get("what", ["saves"])   # ["roms"], ["saves"], or both
            direction         = data.get("direction", "pc_to_anbernic")
            dry_run           = bool(data.get("dry_run", True))
            skip_sha1_dups    = bool(data.get("skip_sha1_dups", False))
            skip_existing     = bool(data.get("skip_existing", False))
            safe_mode         = bool(data.get("safe_mode", True))
            use_adb           = bool(data.get("use_adb", False))
            adb_serial        = data.get("adb_serial", "").strip()
            android_path      = data.get("android_path", "/storage/emulated/0").strip()

            if not pc_path_str:
                self._send_json({"error": "pc_path is required"})
                return
            if use_adb and not adb_serial:
                self._send_json({"error": "adb_serial is required when use_adb is true"})
                return
            if not use_adb and not anbernic_path_str:
                self._send_json({"error": "anbernic_path is required"})
                return

            with _job_lock:
                if _jobs["cable_sync"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["cable_sync"] = True

            def run() -> None:
                _cable_cancel.clear()
                _log_file = None
                try:
                    import time as _time
                    from pathlib import PurePosixPath
                    import datetime as _dt
                    pc_root   = Path(pc_path_str)
                    save_exts = frozenset(config.save_extensions)

                    # Open persistent operation log
                    log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                    _log_file = open(log_path, "a", encoding="utf-8", buffering=1)
                    _ts0 = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    _log_file.write(
                        f"\n=== Cable Sync {_ts0} | direction={direction} dry_run={dry_run} safe_mode={safe_mode} ===\n"
                    )

                    def _log(tag: str, src: str, dst: str = "", note: str = "") -> None:
                        ts = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%H:%M:%S")
                        _log_file.write(f"[{ts}] [{tag:5s}] {src}{(' -> ' + dst) if dst else ''}{(' | ' + note) if note else ''}\n")

                    def _cat_name(name: str) -> str:
                        suffix = Path(name).suffix.lower()
                        return "save" if suffix in save_exts else "rom"

                    def _wanted_name(name: str) -> bool:
                        if name.startswith("."):
                            return False
                        cat = _cat_name(name)
                        return (cat == "save" and "saves" in what) or (cat == "rom" and "roms" in what)

                    def _category(p: Path) -> str:
                        return "save" if p.suffix.lower() in save_exts else "rom"

                    def _wanted(p: Path) -> bool:
                        return _wanted_name(p.name)

                    def _iter_files(root: Path):
                        for dirpath, dirs, files in os.walk(root):
                            dirs[:] = [d for d in dirs if not d.startswith(".")]
                            for fname in files:
                                yield Path(dirpath) / fname

                    copied = skipped = errors = sha1_skipped = safe_mode_skipped = 0
                    copied_bytes = 0
                    details: list[dict] = []

                    _sync_start_time = _time.monotonic()
                    _last_speed_update = _time.monotonic()
                    _last_speed_bytes = 0

                    def _update_progress(file_name: str = "") -> None:
                        nonlocal _last_speed_update, _last_speed_bytes
                        now = _time.monotonic()
                        dt = now - _last_speed_update
                        speed = 0.0
                        if dt >= 0.5:
                            speed = (copied_bytes - _last_speed_bytes) / dt
                            _last_speed_update = now
                            _last_speed_bytes = copied_bytes
                        elif _cable_progress.get("speed_bps") is not None:
                            speed = _cable_progress.get("speed_bps", 0.0)
                        _cable_progress.update({
                            "copied": copied,
                            "bytes_copied": copied_bytes,
                            "speed_bps": speed,
                            "current_file": file_name,
                        })

                    def _copy(src: Path, dst: Path, arrow: str) -> None:
                        nonlocal copied, skipped, errors, copied_bytes, safe_mode_skipped
                        if _cable_cancel.is_set():
                            return
                        try:
                            src_stat = src.stat()
                            size = src_stat.st_size
                            # Safe mode: never overwrite existing destination
                            if safe_mode and dst.exists():
                                safe_mode_skipped += 1
                                skipped += 1
                                _log("SAFE", str(src), str(dst), "destino existe — omitido por modo seguro")
                                if len(details) < 300:
                                    details.append({"file": "SAFE", "path": str(src.name)})
                                return
                            # Skip if destination already exists with same size
                            if skip_existing and dst.exists():
                                try:
                                    if dst.stat().st_size == size:
                                        skipped += 1
                                        _log("SKIP", str(src), str(dst), "mismo tamaño")
                                        if len(details) < 300:
                                            details.append({"file": "EXISTS", "path": str(src.name)})
                                        return
                                except OSError:
                                    pass
                            if not dry_run:
                                dst.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(src, dst)
                            _log("COPY" if not dry_run else "DRYRUN", str(src), str(dst))
                            copied += 1
                            copied_bytes += size
                            if len(details) < 300:
                                details.append({"file": arrow, "path": str(src.name)})
                            _update_progress(src.name)
                        except OSError as exc:
                            errors += 1
                            _log("ERROR", str(src), str(dst), str(exc))
                            if len(details) < 300:
                                details.append({"file": f"ERROR: {exc}", "path": str(src.name)})

                    # ── ADB mode ──────────────────────────────────────────────
                    if use_adb:
                        from rom_manager.sync.adb_transport import AdbTransport
                        transport = AdbTransport(config.adb, adb_serial)

                        def _adb_copy_to_pc(adb_info, rel_posix: str, arrow: str) -> None:
                            nonlocal copied, errors, copied_bytes
                            if _cable_cancel.is_set():
                                return
                            name = PurePosixPath(adb_info.android_path).name
                            local_dst = pc_root / Path(rel_posix.replace("/", os.sep))
                            try:
                                size = transport.pull(adb_info.android_path, local_dst, dry_run=dry_run)
                                _log("ADB←" if not dry_run else "DRY←", adb_info.android_path, str(local_dst))
                                copied += 1
                                copied_bytes += size
                                if len(details) < 300:
                                    details.append({"file": arrow, "path": name})
                                _update_progress(name)
                            except OSError as exc:
                                _log("ERROR", adb_info.android_path, str(local_dst), str(exc))
                                errors += 1
                                if len(details) < 300:
                                    details.append({"file": f"ERROR: {exc}", "path": name})

                        def _adb_copy_to_device(local_src: Path, rel_posix: str, arrow: str) -> None:
                            nonlocal copied, errors, copied_bytes
                            if _cable_cancel.is_set():
                                return
                            android_dst = android_path.rstrip("/") + "/" + rel_posix
                            try:
                                size = transport.push(local_src, android_dst, dry_run=dry_run)
                                _log("ADB→" if not dry_run else "DRY→", str(local_src), android_dst)
                                copied += 1
                                copied_bytes += size
                                if len(details) < 300:
                                    details.append({"file": arrow, "path": local_src.name})
                                _update_progress(local_src.name)
                            except OSError as exc:
                                _log("ERROR", str(local_src), android_dst, str(exc))
                                errors += 1
                                if len(details) < 300:
                                    details.append({"file": f"ERROR: {exc}", "path": local_src.name})

                        _cable_progress.update({"copied": 0, "current_file": "Listando archivos en el dispositivo…"})
                        ab_adb_files = transport.ls_recursive(android_path)
                        # Compute total bytes from ADB listing
                        try:
                            _pre_files = sum(1 for info in ab_adb_files if _wanted_name(PurePosixPath(info.android_path).name))
                            _pre_total = sum(info.size for info in ab_adb_files if _wanted_name(PurePosixPath(info.android_path).name))
                            _cable_progress.update({"bytes_total": _pre_total, "total_files": _pre_files, "copied": 0, "bytes_copied": 0, "speed_bps": 0.0})
                        except Exception:
                            pass
                        android_prefix = android_path.rstrip("/") + "/"

                        if direction == "pc_to_anbernic":
                            for src in _iter_files(pc_root):
                                if _cable_cancel.is_set():
                                    break
                                if not _wanted(src):
                                    continue
                                rel = src.relative_to(pc_root)
                                rel_posix = rel.as_posix()
                                _adb_copy_to_device(src, rel_posix, "→ ADB")

                        elif direction == "anbernic_to_pc":
                            use_sha1 = skip_sha1_dups and "roms" in what
                            if use_sha1:
                                from rom_manager.hashing.hash_calculator import calculate_hashes
                            for info in ab_adb_files:
                                if _cable_cancel.is_set():
                                    break
                                name = PurePosixPath(info.android_path).name
                                if not _wanted_name(name):
                                    continue
                                rel_posix = info.android_path.removeprefix(android_prefix)
                                if use_sha1 and _cat_name(name) == "rom":
                                    local_tmp = pc_root / Path(rel_posix.replace("/", os.sep))
                                    _update_progress(f"[SHA1] {name}")
                                    # For SHA1 check we need the file locally; pull to temp first
                                    import tempfile
                                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(name).suffix) as tf:
                                        tmp_path = Path(tf.name)
                                    try:
                                        transport.pull(info.android_path, tmp_path, dry_run=False)
                                        from rom_manager.hashing.hash_calculator import calculate_hashes
                                        h = calculate_hashes(tmp_path)
                                        # SHA1 check against PC repository (destination)
                                        if repository.sha1_exists(h.sha1):
                                            sha1_skipped += 1
                                            skipped += 1
                                            if len(details) < 300:
                                                details.append({"file": "DUP", "path": name})
                                            tmp_path.unlink(missing_ok=True)
                                            continue
                                        # Move temp file to final destination
                                        dst = pc_root / Path(rel_posix.replace("/", os.sep))
                                        if not dry_run:
                                            dst.parent.mkdir(parents=True, exist_ok=True)
                                            shutil.move(str(tmp_path), dst)
                                        else:
                                            tmp_path.unlink(missing_ok=True)
                                        copied += 1
                                        copied_bytes += info.size
                                        if len(details) < 300:
                                            details.append({"file": "← ADB", "path": name})
                                        _update_progress(name)
                                    except OSError as exc:
                                        tmp_path.unlink(missing_ok=True)
                                        errors += 1
                                        if len(details) < 300:
                                            details.append({"file": f"ERROR: {exc}", "path": name})
                                else:
                                    _adb_copy_to_pc(info, rel_posix, "← ADB")

                        elif direction == "newest":
                            # Build index of device files by relative posix path
                            ab_index = {
                                info.android_path.removeprefix(android_prefix): info
                                for info in ab_adb_files
                                if _wanted_name(PurePosixPath(info.android_path).name)
                            }
                            pc_index: dict[str, Path] = {}
                            for f in _iter_files(pc_root):
                                if _wanted(f):
                                    pc_index[f.relative_to(pc_root).as_posix()] = f

                            all_rels = sorted(set(pc_index) | set(ab_index))
                            for rel_posix in all_rels:
                                if _cable_cancel.is_set():
                                    break
                                pc_f   = pc_index.get(rel_posix)
                                ab_inf = ab_index.get(rel_posix)
                                if pc_f and ab_inf:
                                    if pc_f.stat().st_mtime > ab_inf.mtime:
                                        _adb_copy_to_device(pc_f, rel_posix, "→ ADB (PC más reciente)")
                                    elif ab_inf.mtime > pc_f.stat().st_mtime:
                                        _adb_copy_to_pc(ab_inf, rel_posix, "← ADB (Anbernic más reciente)")
                                    else:
                                        skipped += 1
                                elif pc_f:
                                    _adb_copy_to_device(pc_f, rel_posix, "→ ADB (solo en PC)")
                                elif ab_inf:
                                    _adb_copy_to_pc(ab_inf, rel_posix, "← ADB (solo en Anbernic)")

                    # ── Filesystem mode ───────────────────────────────────────
                    else:
                        ab_root = Path(anbernic_path_str)

                        # Pre-scan to get total bytes (best effort)
                        try:
                            _pre_total = 0
                            _pre_files = 0
                            if direction == "pc_to_anbernic":
                                for _f in _iter_files(pc_root):
                                    if _wanted(_f):
                                        try: _pre_total += _f.stat().st_size
                                        except OSError: pass
                                        _pre_files += 1
                            elif direction == "anbernic_to_pc":
                                for _f in _iter_files(ab_root):
                                    if _wanted(_f):
                                        try: _pre_total += _f.stat().st_size
                                        except OSError: pass
                                        _pre_files += 1
                            elif direction == "newest":
                                for _f in _iter_files(pc_root):
                                    if _wanted(_f):
                                        try: _pre_total += _f.stat().st_size
                                        except OSError: pass
                                        _pre_files += 1
                                for _f in _iter_files(ab_root):
                                    if _wanted(_f):
                                        try: _pre_total += _f.stat().st_size
                                        except OSError: pass
                                        _pre_files += 1
                            _cable_progress.update({"bytes_total": _pre_total, "total_files": _pre_files, "copied": 0, "bytes_copied": 0, "speed_bps": 0.0})
                        except Exception:
                            pass

                        if direction == "pc_to_anbernic":
                            for src in _iter_files(pc_root):
                                if _cable_cancel.is_set():
                                    break
                                if not _wanted(src):
                                    continue
                                rel = src.relative_to(pc_root)
                                dst = ab_root / rel
                                _copy(src, dst, "→ Anbernic")

                        elif direction == "anbernic_to_pc":
                            use_sha1 = skip_sha1_dups and "roms" in what
                            if use_sha1:
                                from rom_manager.hashing.hash_calculator import calculate_hashes
                            for src in _iter_files(ab_root):
                                if _cable_cancel.is_set():
                                    break
                                if not _wanted(src):
                                    continue
                                try:
                                    rel = src.relative_to(ab_root)
                                except ValueError:
                                    continue
                                if use_sha1 and _category(src) == "rom":
                                    _update_progress(f"[SHA1] {src.name}")
                                    try:
                                        h = calculate_hashes(src)
                                        # Check PC repository (destination) for SHA1 duplicates
                                        if repository.sha1_exists(h.sha1):
                                            sha1_skipped += 1
                                            skipped += 1
                                            if len(details) < 300:
                                                details.append({"file": "DUP", "path": src.name})
                                            continue
                                    except OSError:
                                        pass
                                dst = pc_root / rel
                                _copy(src, dst, "← PC")

                        elif direction == "newest":
                            pc_files: dict[Path, Path] = {}
                            for f in _iter_files(pc_root):
                                if _wanted(f):
                                    pc_files[f.relative_to(pc_root)] = f

                            ab_files: dict[Path, Path] = {}
                            for f in _iter_files(ab_root):
                                if _wanted(f):
                                    try:
                                        ab_files[f.relative_to(ab_root)] = f
                                    except ValueError:
                                        pass

                            all_rels = sorted(set(pc_files) | set(ab_files), key=lambda p: str(p))
                            for rel in all_rels:
                                if _cable_cancel.is_set():
                                    break
                                pc_f = pc_files.get(rel)
                                ab_f = ab_files.get(rel)
                                if pc_f and ab_f:
                                    pc_mt = pc_f.stat().st_mtime
                                    ab_mt = ab_f.stat().st_mtime
                                    if pc_mt > ab_mt:
                                        _copy(pc_f, ab_root / rel, "→ Anbernic (PC más reciente)")
                                    elif ab_mt > pc_mt:
                                        _copy(ab_f, pc_root / rel, "← PC (Anbernic más reciente)")
                                    else:
                                        skipped += 1
                                elif pc_f:
                                    _copy(pc_f, ab_root / rel, "→ Anbernic (solo en PC)")
                                elif ab_f:
                                    _copy(ab_f, pc_root / rel, "← PC (solo en Anbernic)")

                    _ts1 = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    _log_file.write(
                        f"=== Fin {_ts1} | copied={copied} skipped={skipped} safe_skipped={safe_mode_skipped} errors={errors} cancelled={_cable_cancel.is_set()} ===\n"
                    )
                    # D8-6: count actual files on disk for both sides (best effort)
                    _pc_file_count = 0
                    _ab_file_count = 0
                    if not dry_run and not use_adb:
                        try:
                            _ab_r = Path(anbernic_path_str)
                            for _ff in _iter_files(pc_root):
                                if _wanted(_ff):
                                    _pc_file_count += 1
                        except Exception:
                            pass
                        try:
                            for _ff in _iter_files(_ab_r):
                                if _wanted(_ff):
                                    _ab_file_count += 1
                        except Exception:
                            pass
                    _job_results["cable_sync"] = {
                        "dry_run": dry_run,
                        "direction": direction,
                        "use_adb": use_adb,
                        "copied": copied,
                        "skipped": skipped,
                        "sha1_skipped": sha1_skipped,
                        "safe_mode_skipped_overwrites": safe_mode_skipped,
                        "errors": errors,
                        "copied_bytes": copied_bytes,
                        "cancelled": _cable_cancel.is_set(),
                        "details": details,
                        "pc_file_count": _pc_file_count,
                        "ab_file_count": _ab_file_count,
                    }
                except Exception as exc:
                    _job_results["cable_sync"] = {"error": str(exc)}
                finally:
                    if _log_file is not None:
                        try:
                            _log_file.close()
                        except Exception:
                            pass
                    with _job_lock:
                        _cable_progress.clear()
                        _jobs["cable_sync"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started", "dry_run": dry_run})

        # ── Two-DB migration ───────────────────────────────────────────────────

        def _handle_migrate_split_db(self) -> None:
            """One-time migration: move Android-path games from PC repo to Android repo.

            Reads all games in PC repository whose source_path does NOT start with
            library_root, moves their records to the Android repository, and deletes
            them from the PC repository.  Safe to run multiple times (idempotent).
            """
            lib_root = str(config.library_root or "").lower().rstrip("/\\")
            if not lib_root:
                self._send_json({"error": "library_root not configured — cannot determine which paths are Android"})
                return

            migrated = 0
            errors: list[str] = []
            try:
                with repository.connect() as _conn:
                    rows = _conn.execute(
                        "SELECT id, original_filename, source_path, platform, file_type, "
                        "relative_parent, region, extension, size_bytes, mtime, sha1, md5, "
                        "crc32, set_type, created_at, updated_at, canonical_title, "
                        "match_confidence, catalog_source "
                        "FROM games"
                    ).fetchall()

                android_rows = [r for r in rows if not r["source_path"].lower().startswith(lib_root)]

                from rom_manager.scanner.rom_scanner import utc_now as _now
                ts = _now()

                # Insert Android games into android repo, delete from PC repo
                with _repo_android.batch() as _android_conn:
                    for row in android_rows:
                        try:
                            _repo_android.upsert_game(
                                original_filename=row["original_filename"],
                                source_path=row["source_path"],
                                platform=row["platform"],
                                file_type=row["file_type"],
                                relative_parent=row["relative_parent"] or "",
                                region=row["region"],
                                extension=row["extension"],
                                size_bytes=int(row["size_bytes"]),
                                mtime=int(row["mtime"] or 0),
                                sha1=row["sha1"] or "",
                                md5=row["md5"] or "",
                                crc32=row["crc32"] or "",
                                set_type=row["set_type"] or "",
                                timestamp=ts,
                                connection=_android_conn,
                            )
                            migrated += 1
                        except Exception as exc:
                            errors.append(f"{row['source_path']}: {exc}")

                # Delete migrated games from PC repo
                with repository.batch() as _pc_conn:
                    for row in android_rows:
                        _pc_conn.execute("DELETE FROM games WHERE source_path = ?", (row["source_path"],))

                # Also migrate saves
                with repository.connect() as _conn:
                    save_rows = _conn.execute(
                        "SELECT original_path, relative_parent, extension, size_bytes, created_at "
                        "FROM saves"
                    ).fetchall()

                android_saves = [r for r in save_rows if not r["original_path"].lower().startswith(lib_root)]
                if android_saves:
                    with _repo_android.batch() as _android_conn:
                        for row in android_saves:
                            try:
                                _repo_android.upsert_save(
                                    original_path=row["original_path"],
                                    relative_parent=row["relative_parent"] or "",
                                    extension=row["extension"],
                                    size_bytes=int(row["size_bytes"]),
                                    timestamp=ts,
                                    connection=_android_conn,
                                )
                            except Exception as exc:
                                errors.append(f"save:{row['original_path']}: {exc}")
                    with repository.batch() as _pc_conn:
                        for row in android_saves:
                            _pc_conn.execute("DELETE FROM saves WHERE original_path = ?", (row["original_path"],))

            except Exception as exc:
                self._send_json({"error": str(exc)})
                return

            self._send_json({
                "migrated_games": migrated,
                "errors": errors[:20],
                "pc_db": str(config.database_path),
                "android_db": str(config.database_path_android),
            })

        # ── D8-3: RA conflict resolver ─────────────────────────────────────────

        def _handle_apply_ra_conflicts(self, data: dict) -> None:
            """Resolve plan conflicts by keeping RA winner and moving loser to _descartados/."""
            import shutil as _shutil
            from rom_manager.planner.operation_planner import FormatOptions as _FO
            opts = _FO()
            plan = build_plan(repository, opts)
            resolved = 0
            skipped_no_ra = 0
            errors: list[str] = []
            cache_dir_exists = (config.project_root / ".rommgr" / "ra_cache").exists()
            cache_files_exist = cache_dir_exists and any((config.project_root / ".rommgr" / "ra_cache").iterdir()) if cache_dir_exists else False
            for op in plan.conflicts:
                if not op.source_path.exists():
                    continue
                # Look up both source and target in repository by MD5/path
                src_md5: str | None = None
                tgt_md5: str | None = None
                try:
                    with repository.connect() as _c:
                        _src_row = _c.execute(
                            "SELECT md5 FROM games WHERE source_path = ?", (str(op.source_path),)
                        ).fetchone()
                        _tgt_row = _c.execute(
                            "SELECT md5 FROM games WHERE source_path = ?", (str(op.target_path),)
                        ).fetchone()
                    if _src_row:
                        src_md5 = _src_row["md5"]
                    if _tgt_row:
                        tgt_md5 = _tgt_row["md5"]
                except Exception:
                    pass

                # Check RA support for both
                from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id
                from rom_manager.retroachievements.ra_client import _parse_game_list as _pgl
                import json as _json
                cache_dir = config.project_root / ".rommgr" / "ra_cache"
                plat = op.game.platform or ""
                console_id = get_ra_console_id(plat)
                src_ra = tgt_ra = -1
                if console_id:
                    cache_file = cache_dir / f"ra_hashes_{console_id}.json"
                    if cache_file.exists():
                        try:
                            _hash_lib = _pgl(_json.loads(cache_file.read_text(encoding="utf-8")))
                            if src_md5:
                                src_entry = _hash_lib.get(src_md5.lower())
                                src_ra = src_entry.achievements if src_entry else -1
                            if tgt_md5:
                                tgt_entry = _hash_lib.get(tgt_md5.lower())
                                tgt_ra = tgt_entry.achievements if tgt_entry else -1
                        except Exception:
                            pass

                if src_ra <= 0 and tgt_ra <= 0:
                    skipped_no_ra += 1
                    continue

                # Decide which to keep: higher RA wins; if equal keep source
                if tgt_ra > src_ra:
                    loser_path = op.source_path
                else:
                    loser_path = op.target_path  # target exists but source would replace it

                discard_dir = loser_path.parent / "_descartados"
                try:
                    discard_dir.mkdir(parents=True, exist_ok=True)
                    dest = discard_dir / loser_path.name
                    if not dest.exists():
                        _shutil.move(str(loser_path), dest)
                    else:
                        loser_path.unlink()
                    # Remove from DB
                    with repository.connect() as _c:
                        _c.execute("DELETE FROM games WHERE source_path = ?", (str(loser_path),))
                        _c.execute("PRAGMA optimize")
                    resolved += 1
                except Exception as exc:
                    errors.append(f"{loser_path.name}: {exc}")

            self._send_json({
                "resolved": resolved,
                "skipped_no_ra": skipped_no_ra,
                "errors": errors[:10],
                "no_cache": not cache_files_exist,
            })

        # ── D8-4: RA version duplicate discard ─────────────────────────────────

        def _handle_ra_duplicate_discard(self, data: dict) -> None:
            import shutil as _shutil
            import logging as _logging
            _disc_log = _logging.getLogger(__name__)
            source_path = data.get("path", "").strip()
            if not source_path:
                self._send_json({"error": "path required"})
                return
            p = Path(source_path)
            if not p.exists():
                # Already gone — remove from DB if present
                with repository.connect() as _c:
                    _c.execute("DELETE FROM games WHERE source_path = ?", (source_path,))
                self._send_json({"ok": True, "note": "file already missing; removed from DB"})
                return
            discard_dir = p.parent / "_descartados"
            dest: Path | None = None
            moved = False
            try:
                discard_dir.mkdir(parents=True, exist_ok=True)
                dest = discard_dir / p.name
                # Step 1: move/delete the file
                permanently_deleted = False
                if dest.exists():
                    # Destination already occupied — delete the source directly (no rollback possible)
                    p.unlink()
                    dest = None
                    permanently_deleted = True
                else:
                    _shutil.move(str(p), dest)
                    moved = True
                # Step 2: delete from DB — if this fails, roll back the file move
                with repository.connect() as _c:
                    _c.execute("DELETE FROM games WHERE source_path = ?", (source_path,))
            except Exception as exc:
                if moved and dest is not None and dest.exists():
                    try:
                        _shutil.move(str(dest), str(p))
                        _disc_log.warning("RA discard rollback: restored %s after DB error", p.name)
                    except Exception as rb_exc:
                        _disc_log.error("RA discard rollback FAILED for %s: %s", p.name, rb_exc)
                        self._send_json({"error": f"DB error AND rollback failed — {p.name} may be lost: {exc} | rollback: {rb_exc}"})
                        return
                elif permanently_deleted:
                    _disc_log.error("File %s was permanently deleted but DB delete failed: %s", p.name, exc)
                    self._send_json({"error": f"File was deleted but DB update failed — stale entry will be removed on next scan: {exc}"})
                    return
                self._send_json({"error": str(exc)})
                return
            self._send_json({"ok": True})

        def _handle_ra_duplicate_discard_all(self) -> None:
            """Discard ALL entries without RA support from version-duplicate groups."""
            import shutil as _shutil
            import logging as _logging
            _dall_log = _logging.getLogger(__name__)
            ra_dups = _build_ra_duplicates(repository, config)
            discarded = 0
            failed = 0
            errors: list[str] = []
            for group in ra_dups.get("groups", []):
                for entry in group.get("entries", []):
                    if entry.get("ra_supported"):
                        continue
                    src_path_str = entry.get("source_path", "")
                    if not src_path_str:
                        continue
                    p = Path(src_path_str)
                    discard_dir = p.parent / "_descartados"
                    dest_file: Path | None = None
                    moved = False
                    permanently_deleted = False
                    try:
                        discard_dir.mkdir(parents=True, exist_ok=True)
                        if p.exists():
                            dest_file = discard_dir / p.name
                            if dest_file.exists():
                                p.unlink()
                                dest_file = None
                                permanently_deleted = True
                            else:
                                _shutil.move(str(p), dest_file)
                                moved = True
                        # DB delete only after file is safely moved
                        with repository.connect() as _c:
                            _c.execute("DELETE FROM games WHERE source_path = ?", (src_path_str,))
                        discarded += 1
                    except Exception as exc:
                        failed += 1
                        # Roll back file move if DB failed
                        if moved and dest_file is not None and dest_file.exists():
                            try:
                                _shutil.move(str(dest_file), str(p))
                                _dall_log.warning("RA discard-all rollback: restored %s", p.name)
                                errors.append(f"{p.name}: DB error (file restored) — {exc}")
                            except Exception as rb_exc:
                                _dall_log.error("RA discard-all rollback FAILED for %s: %s", p.name, rb_exc)
                                errors.append(f"{p.name}: DB error AND rollback failed — file may be lost | {exc} | {rb_exc}")
                        elif permanently_deleted:
                            _dall_log.error("File %s permanently deleted but DB delete failed: %s", p.name, exc)
                            errors.append(f"{p.name}: deleted but DB not updated (stale entry — will be removed on next scan)")
                        else:
                            errors.append(f"{p.name}: {exc}")
            self._send_json({
                "discarded": discarded,
                "failed": failed,
                "errors": errors[:10],
            })

        def _handle_ra_discard_no_support(self) -> None:
            """Bulk-discard all games that have NO RA support at all (status='no_support').

            Reads the stored `no_support_entries` from the last RA check result.
            Moves files to `<parent>/_descartados/` and removes from DB.
            """
            import shutil as _shutil
            import logging as _logging
            _dns_log = _logging.getLogger(__name__)

            result = _job_results.get("ra_check")
            if not result:
                self._send_json({"error": "No RA check result available. Run RA check first."})
                return
            entries = result.get("no_support_entries", [])
            if not entries:
                self._send_json({"discarded": 0, "failed": 0, "errors": [], "note": "No games to discard."})
                return

            discarded = 0
            failed = 0
            errors: list[str] = []
            for entry in entries:
                src_path_str = entry.get("source_path", "")
                if not src_path_str:
                    continue
                p = Path(src_path_str)
                discard_dir = p.parent / "_descartados"
                dest_file: Path | None = None
                moved = False
                permanently_deleted = False
                try:
                    discard_dir.mkdir(parents=True, exist_ok=True)
                    if p.exists():
                        dest_file = discard_dir / p.name
                        if dest_file.exists():
                            p.unlink()
                            permanently_deleted = True
                        else:
                            _shutil.move(str(p), dest_file)
                            moved = True
                    # DB delete only after file is safely moved
                    with repository.connect() as _c:
                        _c.execute("DELETE FROM games WHERE source_path = ?", (src_path_str,))
                    discarded += 1
                except Exception as exc:
                    failed += 1
                    if moved and dest_file is not None and dest_file.exists():
                        try:
                            _shutil.move(str(dest_file), str(p))
                            _dns_log.warning("RA discard-no-support rollback: restored %s", p.name)
                            errors.append(f"{p.name}: DB error (file restored) — {exc}")
                        except Exception as rb_exc:
                            _dns_log.error("RA discard-no-support rollback FAILED for %s: %s", p.name, rb_exc)
                            errors.append(f"{p.name}: DB error AND rollback failed — file may be lost | {exc} | {rb_exc}")
                    elif permanently_deleted:
                        _dns_log.error("File %s permanently deleted but DB delete failed: %s", p.name, exc)
                        errors.append(f"{p.name}: deleted from disk but DB error — {exc}")
                    else:
                        errors.append(f"{p.name}: {exc}")
            self._send_json({
                "discarded": discarded,
                "failed": failed,
                "errors": errors[:10],
            })

        def _handle_apply(self, data: dict) -> None:
            with _job_lock:
                if _jobs["apply"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["apply"] = True

            fmt = data.get("format_opts", {})
            opts = FormatOptions(
                include_region=fmt.get("include_region", True),
                include_revision=fmt.get("include_revision", True),
                include_platform=fmt.get("include_platform", False),
                include_sha=fmt.get("include_sha", False),
                sha_length=min(40, max(4, int(fmt.get("sha_length", 8)))),
            )
            source_root = data.get("source_root") or None
            keep_both   = bool(data.get("keep_both", False))

            def run() -> None:
                try:
                    from rom_manager.renamer.file_renamer import rename_rom_with_saves
                    from rom_manager.scanner.rom_scanner import utc_now

                    save_exts = frozenset(config.save_extensions)
                    # Use the correct repo for the apply operation
                    _apply_repo = _get_repo(source_root or "")
                    plan = build_plan(_apply_repo, opts, keep_both=keep_both)
                    pending_ops = plan.pending
                    if source_root:
                        root_lower = source_root.lower()
                        pending_ops = [op for op in pending_ops if str(op.source_path).lower().startswith(root_lower)]

                    total = len(pending_ops)
                    renamed = failed = skipped = saves_renamed = 0
                    skip_details: list[str] = []
                    timestamp = utc_now()
                    _apply_progress.update({"current": 0, "total": total, "current_file": ""})

                    for idx, op in enumerate(pending_ops, 1):
                        _apply_progress.update({"current": idx, "total": total, "current_file": op.source_path.name})
                        if not op.source_path.exists():
                            skipped += 1
                            skip_details.append(f"{op.source_path.name}: source not found (outdated DB entry)")
                            continue
                        try:
                            outcome = rename_rom_with_saves(op.source_path, op.target_path, save_exts)
                        except Exception as exc:
                            skipped += 1
                            skip_details.append(f"{op.source_path.name}: unexpected error — {exc}")
                            continue
                        if outcome.success:
                            # Route the DB update to the same repo where the file lives
                            _op_repo = _get_repo(str(op.source_path))
                            _op_repo.apply_rename(
                                game_id=op.game.id,
                                old_source_path=str(op.source_path),
                                new_source_path=str(op.target_path),
                                new_filename=op.target_path.name,
                                timestamp=timestamp,
                            )
                            renamed += 1
                            saves_renamed += outcome.saves_renamed
                        else:
                            err_lower = outcome.error.lower()
                            if "not found" in err_lower or "no such file" in err_lower:
                                skipped += 1
                            else:
                                failed += 1
                            skip_details.append(f"{op.source_path.name}: {outcome.error}")

                    from rom_manager.scanner.rom_scanner import utc_now as _now
                    _job_results["apply"] = {
                        "renamed": renamed,
                        "failed": failed,
                        "skipped": skipped,
                        "saves_renamed": saves_renamed,
                        "conflicts": len(plan.conflicts),
                        "skip_details": skip_details[:20],
                        "error_details": skip_details[:50],  # D8-2: full error list for UI
                        "result_ts": _now(),
                    }
                except Exception as exc:
                    _job_results["apply"] = {"error": str(exc), "result_ts": ""}
                finally:
                    with _job_lock:
                        _apply_progress.clear()
                        _jobs["apply"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started"})

        def _handle_setup_run(self, data: dict) -> None:
            """Launch the first-time setup wizard pipeline as a background job."""
            lib_root = data.get("library_root", "").strip() or (str(config.library_root) if config.library_root else "")
            if not lib_root:
                self._send_json({"error": "library_root is required"})
                return
            # Persist paths to config.toml so they survive restarts
            from rom_manager.config import write_config_toml, load_config
            updates: dict = {}
            if not config.library_root or str(config.library_root) != lib_root:
                updates["library.library_root"] = lib_root
            android_root = data.get("android_root", "").strip()
            if android_root and (not config.anbernic_root or str(config.anbernic_root) != android_root):
                updates["library.anbernic_root"] = android_root
            if updates:
                write_config_toml(config.project_root, updates)
                new_cfg = load_config(config.project_root)
                config.library_root = new_cfg.library_root
                if android_root:
                    config.anbernic_root = new_cfg.anbernic_root
                config.device_name = new_cfg.device_name
            with _job_lock:
                if _jobs["setup"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["setup"] = True
            _setup_progress.clear()
            _job_results.pop("setup", None)
            options = {
                "clean_junk": bool(data.get("clean_junk", False)),
                "extract_zips": bool(data.get("extract_zips", True)),
                "scan": bool(data.get("scan", True)),
                "match": bool(data.get("match", True)),
            }
            threading.Thread(
                target=_run_setup_pipeline,
                args=(lib_root, options, repository, config),
                daemon=True,
            ).start()
            self._send_json({"status": "started"})

        def _handle_inbox_run(self, data: dict) -> None:
            inbox_path_str = data.get("path", "").strip() or config.inbox_path
            if not inbox_path_str:
                self._send_json({"error": "path is required (or set inbox.path in config.toml)"})
                return
            target_root_str = data.get("target_root", "").strip() or config.inbox_target_root or (str(config.library_root) if config.library_root else "")
            delete_source = bool(data.get("delete_source", config.inbox_delete_source))

            with _job_lock:
                if _jobs["inbox"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["inbox"] = True

            threading.Thread(
                target=_run_inbox_pipeline,
                args=(inbox_path_str, target_root_str, delete_source, repository, config),
                daemon=True,
            ).start()
            self._send_json({"status": "started"})

        # ── Helpers ──────────────────────────────────────────────────────────

        def _send(
            self,
            code: int,
            content_type: str,
            body: bytes,
            extra_headers: dict[str, str] | None = None,
        ) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra_headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, data: object) -> None:
            body = _json_response(data)
            self._send(200, "application/json; charset=utf-8", body)

    return Handler




def serve(
    *,
    host: str,
    port: int,
    repository: LibraryRepository,
    config: AppConfig,
    repository_android: LibraryRepository | None = None,
) -> None:
    global _auto_sync_enabled
    _auto_sync_enabled = config.auto_sync_enabled

    if config.auto_sync_enabled:
        t = threading.Thread(
            target=_auto_sync_loop,
            args=(config, lambda: repository),
            daemon=True,
        )
        t.name = "auto-sync-daemon"
        t.start()
        _logger.info("Auto-sync daemon started (polling every 10 s)")

    # SD card daemon always runs (checks config.anbernic_root internally)
    sd_t = threading.Thread(
        target=_sd_card_sync_loop,
        args=(config, lambda: repository),
        daemon=True,
    )
    sd_t.name = "sd-sync-daemon"
    sd_t.start()
    _logger.info("SD card sync daemon started (polling every 8 s)")

    # Inbox watcher daemon (runs only when inbox_auto_process is True)
    def _inbox_watcher_with_repo() -> None:
        import time as _time
        while True:
            try:
                _time.sleep(30)
                if not config.inbox_path or not config.inbox_auto_process:
                    _inbox_watcher_status.update({"watching": False, "last_check": None, "pending_files": 0})
                    continue
                inbox = Path(config.inbox_path).resolve()
                if not inbox.exists():
                    _inbox_watcher_status.update({"watching": True, "last_check": _watcher_now(), "pending_files": 0})
                    continue
                pending: list[Path] = [
                    e for e in inbox.iterdir()
                    if e.is_file() and not e.name.startswith(".") and not e.name.startswith("_")
                ]
                _inbox_watcher_status.update({
                    "watching": True,
                    "last_check": _watcher_now(),
                    "pending_files": len(pending),
                })
                if pending:
                    with _job_lock:
                        already = _jobs.get("inbox", False)
                    if not already:
                        _logger.info("Inbox watcher: %d files detected, launching pipeline", len(pending))
                        with _job_lock:
                            _jobs["inbox"] = True
                        target_root_str = config.inbox_target_root or (str(config.library_root) if config.library_root else "")
                        threading.Thread(
                            target=_run_inbox_pipeline,
                            args=(config.inbox_path, target_root_str, config.inbox_delete_source, repository, config),
                            daemon=True,
                        ).start()
            except Exception as exc:
                _logger.debug("Inbox watcher error: %s", exc)

    tw = threading.Thread(target=_inbox_watcher_with_repo, daemon=True)
    tw.name = "inbox-watcher-daemon"
    tw.start()
    _logger.info("Inbox watcher daemon started")

    handler = make_handler(repository, config, repository_android=repository_android)
    with ThreadingHTTPServer((host, port), handler) as httpd:
        httpd.serve_forever()
