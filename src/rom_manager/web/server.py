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
    "Saturn":           "saturn",
    "Atari 2600":       "atari2600",
    "Atari 5200":       "atari5200",
    "Atari 7800":       "atari7800",
    "Atari Lynx":       "atarilynx",
    "Atari Jaguar":     "atarijaguar",
    "Neo Geo":          "neogeo",
    "PC Engine":        "pcengine",
    "Sega 32X":         "sega32x",
    "Sega CD":          "segacd",
}

_STANDARD_PLATFORM_FOLDERS: tuple[str, ...] = (
    "nes", "snes", "n64", "gb", "gbc", "gba", "nds", "3ds",
    "gamecube", "wii", "psx", "ps2", "ps3", "psp",
    "dreamcast", "saturn", "megadrive", "mastersystem", "gamegear",
    "neogeo", "pcengine", "sega32x", "segacd",
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


def _json_response(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode()


def _test_path(path_str: str) -> dict:
    """Check whether *path_str* is an accessible directory on the local filesystem.

    Also detects common MTP / shell-namespace patterns that look like real paths
    but are not accessible from Python.
    """
    raw = path_str.strip()
    if not raw:
        return {"accessible": False, "error": "Introduce una ruta primero"}

    # Heuristic: detect Windows MTP paths (not a drive letter, not a UNC share)
    is_drive_letter = len(raw) >= 2 and raw[1] == ":" and raw[0].isalpha()
    is_unc          = raw.startswith("\\\\") or raw.startswith("//")
    looks_like_mtp  = not is_drive_letter and not is_unc

    try:
        p = Path(path_str).resolve()
        if not p.exists():
            msg = ("Esta ruta no existe como carpeta del sistema de archivos. "
                   "Si ves el dispositivo en 'Este equipo', está accediendo por MTP — "
                   "eso no es compatible. Usa la SD card en un lector USB o Termux SFTP.")
            return {"accessible": False, "error": msg, "looks_like_mtp": looks_like_mtp}
        if not p.is_dir():
            return {"accessible": False, "error": "La ruta existe pero no es una carpeta"}
        try:
            entries = sum(1 for _ in p.iterdir())
        except PermissionError:
            return {"accessible": False, "error": "Sin permiso de lectura en esa carpeta"}
        return {
            "accessible": True,
            "path": str(p),
            "entries": entries,
        }
    except (OSError, ValueError) as exc:
        return {"accessible": False, "error": str(exc), "looks_like_mtp": looks_like_mtp}


def _list_drives() -> dict:
    """Return all accessible drive letters on Windows (A–Z), with label and free space."""
    import platform
    drives: list[dict] = []
    if platform.system() == "Windows":
        import string
        import ctypes
        for letter in string.ascii_uppercase:
            root = Path(f"{letter}:\\")
            if root.exists():
                try:
                    stat = root.stat()
                    # GetVolumeInformation to get label
                    label_buf   = ctypes.create_unicode_buffer(261)
                    fs_buf      = ctypes.create_unicode_buffer(261)
                    ctypes.windll.kernel32.GetVolumeInformationW(  # type: ignore[attr-defined]
                        f"{letter}:\\", label_buf, 261,
                        None, None, None, fs_buf, 261,
                    )
                    label = label_buf.value or ""
                    total, free = 0, 0
                    usage = ctypes.c_ulonglong(0)
                    free_c = ctypes.c_ulonglong(0)
                    total_c = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(  # type: ignore[attr-defined]
                        f"{letter}:\\",
                        ctypes.byref(usage),
                        ctypes.byref(total_c),
                        ctypes.byref(free_c),
                    )
                    total = total_c.value
                    free  = free_c.value
                    drives.append({
                        "letter": f"{letter}:\\",
                        "label": label,
                        "total_bytes": total,
                        "free_bytes": free,
                    })
                except OSError:
                    drives.append({"letter": f"{letter}:\\", "label": "", "total_bytes": 0, "free_bytes": 0})
    else:
        # Non-Windows: return mount points from /proc/mounts or similar
        try:
            for line in Path("/proc/mounts").read_text().splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[1].startswith("/media"):
                    drives.append({"letter": parts[1], "label": parts[1].split("/")[-1], "total_bytes": 0, "free_bytes": 0})
        except OSError:
            pass
    return {"drives": drives}


def _build_junk_scan(folder_path: str) -> dict:
    """Scan a folder and classify non-gaming files as junk."""
    import os as _os
    from pathlib import Path as _Path

    _GAMING_EXTS = {
        ".gba", ".gb", ".gbc", ".nes", ".sfc", ".smc", ".md", ".smd", ".gen",
        ".n64", ".z64", ".v64", ".nds", ".3ds", ".iso", ".chd", ".cue", ".bin",
        ".cdi", ".gdi", ".pbp", ".gcm", ".nsp", ".xci", ".pce", ".ws", ".wsc",
        ".ngc", ".ngp", ".gg", ".lynx", ".a26", ".a52", ".a78", ".col", ".vb",
        ".img", ".mdf", ".ecm", ".nrg", ".ccd", ".rom", ".bios",
        ".sav", ".srm", ".state", ".sta", ".mcr", ".mc", ".mem", ".rtc",
        ".xml", ".m3u", ".png", ".jpg", ".jpeg", ".mp4", ".webp",
    }
    _CONFIG_EXTS = {
        ".cfg", ".ini", ".toml", ".json", ".txt", ".sh", ".bat", ".conf",
        ".opt", ".ovr", ".rmp",
    }
    _JUNK_CATEGORIES: dict[str, str] = {
        ".ipynb": "Jupyter Notebooks", ".py": "Scripts Python",
        ".js": "Scripts JavaScript", ".xlsx": "Excel", ".xls": "Excel",
        ".docx": "Word", ".doc": "Word", ".pptx": "PowerPoint", ".ppt": "PowerPoint",
        ".pdf": "PDFs", ".zip": "ZIPs no-ROM", ".rar": "RARs", ".7z": "7-Zips",
        ".tar": "Tarballs", ".gz": "Tarballs", ".bz2": "Tarballs",
        ".exe": "Ejecutables", ".dll": "Ejecutables", ".apk": "APKs Android",
        ".mp3": "Audio", ".flac": "Audio", ".ogg": "Audio", ".wav": "Audio",
        ".avi": "Vídeo (no-gaming)", ".mkv": "Vídeo (no-gaming)", ".mov": "Vídeo (no-gaming)",
        ".psd": "Imágenes editables", ".ai": "Imágenes editables", ".svg": "SVGs",
        ".html": "HTML/Web", ".css": "HTML/Web", ".log": "Logs",
        ".db": "Bases de datos", ".sqlite": "Bases de datos",
    }

    p = _Path(folder_path)
    if not p.is_dir():
        return {"error": f"Carpeta no encontrada: {folder_path}"}

    categories: dict[str, list[dict]] = {}
    total_junk_bytes = 0

    for dirpath, dirs, files in _os.walk(p):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            fpath = _Path(dirpath) / fname
            ext = fpath.suffix.lower()
            if ext in _GAMING_EXTS or ext in _CONFIG_EXTS:
                continue
            cat = _JUNK_CATEGORIES.get(ext, f"Otros ({ext or 'sin extensión'})")
            try:
                size = fpath.stat().st_size
            except OSError:
                size = 0
            total_junk_bytes += size
            if cat not in categories:
                categories[cat] = []
            try:
                rel = str(fpath.relative_to(p))
            except ValueError:
                rel = str(fpath)
            categories[cat].append({"path": rel, "full_path": str(fpath), "size_bytes": size})

    cat_list = []
    for cat, files_list in sorted(categories.items(), key=lambda x: -sum(f["size_bytes"] for f in x[1])):
        total = sum(f["size_bytes"] for f in files_list)
        cat_list.append({
            "category": cat,
            "count": len(files_list),
            "total_bytes": total,
            "files": sorted(files_list, key=lambda f: -f["size_bytes"])[:50],
        })

    return {
        "folder": folder_path,
        "total_junk_files": sum(c["count"] for c in cat_list),
        "total_junk_bytes": total_junk_bytes,
        "categories": cat_list,
    }


def _build_library_report(
    source_path_str: str,
    repository: LibraryRepository,
    config: AppConfig,
) -> dict:
    """Generate a full library health report for the given source path."""
    source = Path(source_path_str).resolve()
    path_accessible = source.exists() and source.is_dir()

    # ── ZIPs ──────────────────────────────────────────────────────────────────
    from rom_manager.converters.zip_extractor import find_zip_files, _DISC_RE as _ZIP_DISC_RE
    zip_list = []
    zip_files: list[Path] = []
    if path_accessible:
        try:
            zip_files = find_zip_files(source)
        except Exception:
            zip_files = []
        for zp in zip_files:
            try:
                rel = str(zp.relative_to(source))
            except ValueError:
                rel = zp.name
            try:
                size = zp.stat().st_size
            except OSError:
                size = 0
            is_disc = bool(_ZIP_DISC_RE.match(zp.stem))
            zip_list.append({"path": rel, "name": zp.name, "size_bytes": size, "is_disc_set": is_disc})

    # ── Playlists / Multi-disco ────────────────────────────────────────────────
    from rom_manager.utils.m3u_generator import find_disc_groups
    from rom_manager.utils.multidisc_verifier import verify_multidisc
    groups: list = []
    playlist_groups: list = []
    multidisc_data: dict = {"groups_ok": 0, "groups_with_issues": 0, "issues": []}
    if path_accessible:
        try:
            groups = find_disc_groups(source)
            playlist_groups = [
                {
                    "base_name": g.base_name,
                    "disc_count": len(g.discs),
                    "discs": [d.name for d in g.discs],
                    "m3u_exists": g.m3u_path.exists(),
                    "m3u_name": g.m3u_path.name,
                    "platform": g.platform,
                }
                for g in groups
            ]
        except Exception:
            pass
        try:
            multidisc = verify_multidisc(source, repository)
            multidisc_data = {
                "groups_ok": multidisc.groups_ok,
                "groups_with_issues": multidisc.groups_with_issues,
                "issues": [
                    {"base_name": i.base_name, "issue_type": i.issue_type, "detail": i.detail, "platform": i.platform}
                    for i in multidisc.issues
                ],
            }
        except Exception:
            pass

    # ── Orphaned saves ────────────────────────────────────────────────────────
    from rom_manager.utils.orphan_finder import find_orphaned_saves
    orphans = []
    if path_accessible:
        try:
            orphans = find_orphaned_saves(source, config.save_extensions)
        except Exception:
            pass
    orphan_data = {
        "total": len(orphans),
        "total_bytes": sum(o.size_bytes for o in orphans),
        "saves": [
            {"path": o.save_path, "stem": o.stem, "extension": o.extension, "size_bytes": o.size_bytes}
            for o in orphans
        ],
    }

    from datetime import datetime, timezone
    return {
        "source_path": str(source),
        "path_accessible": path_accessible,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "zips": {"total": len(zip_files), "files": zip_list},
        "playlists": {
            "total_groups": len(groups),
            "with_m3u": sum(1 for g in playlist_groups if g["m3u_exists"]),
            "without_m3u": sum(1 for g in playlist_groups if not g["m3u_exists"]),
            "groups": playlist_groups,
        },
        "multidisc": multidisc_data,
        "orphans": orphan_data,
    }


def _build_status(
    repository: LibraryRepository,
    source_root: str | None = None,
    project_root: Path | None = None,
    repository_android: LibraryRepository | None = None,
    library_root: Path | None = None,
) -> dict:
    from datetime import UTC, datetime as _dt_cls
    summary = repository.get_summary(source_root)
    dup_groups = repository.get_duplicate_groups()
    from rom_manager.reports.reporter import _get_all_games
    games = _get_all_games(repository)
    if source_root:
        prefix = source_root.rstrip("/\\")
        matched = sum(1 for g in games if g.canonical_title is not None and g.source_path.startswith(prefix))
    else:
        matched = sum(1 for g in games if g.canonical_title is not None)
    wasted = sum(g.wasted_bytes for g in dup_groups)
    last_scans = repository.get_last_scan_by_root()
    # Android DB counts (separate DB)
    android_summary = None
    if repository_android is not None and repository_android is not repository:
        try:
            android_summary = repository_android.get_summary()
        except Exception:
            pass

    # D8-1: compute per-root scan staleness
    scan_days_ago: int | None = None
    stale = False
    if source_root:
        root_norm = source_root.lower()
        # Find best matching scan root
        best_at: str | None = None
        for root_key, at_str in last_scans.items():
            if root_key.lower().startswith(root_norm) or root_norm.startswith(root_key.lower()):
                if best_at is None or at_str > best_at:
                    best_at = at_str
        if best_at is None:
            stale = True
        else:
            try:
                scanned_at = _dt_cls.fromisoformat(best_at.replace("Z", "+00:00"))
                now_utc = _dt_cls.now(UTC)
                delta = now_utc - scanned_at
                scan_days_ago = delta.days
                stale = scan_days_ago > 7
            except Exception:
                stale = True

    # D8-7: check for cached report
    last_report_at: str | None = None
    last_report_mins_ago: int | None = None
    if project_root is not None:
        try:
            import os as _os
            _rpt_cache = project_root / ".rommgr" / "last_report.json"
            if _rpt_cache.exists():
                _mtime = _rpt_cache.stat().st_mtime
                _now_ts = _dt_cls.now(UTC).timestamp()
                _mins = int((_now_ts - _mtime) / 60)
                last_report_at = _dt_cls.fromtimestamp(_mtime, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
                last_report_mins_ago = _mins
        except Exception:
            pass

    # ── D8-P1: first_run / setup_complete / setup_checklist ──────────────────
    scan_count = 0
    matched_count = 0
    try:
        with repository.connect() as _sc:
            scan_count = _sc.execute("SELECT COUNT(*) FROM scan_runs").fetchone()[0]
            _m = _sc.execute("SELECT COUNT(*) FROM games WHERE canonical_title IS NOT NULL").fetchone()
            matched_count = _m[0] if _m else 0
    except Exception:
        pass

    library_root_set = bool(library_root and library_root.exists())
    # first_run = library root not configured yet (path may not exist if drive is unmounted)
    first_run = not bool(library_root)
    setup_complete = scan_count > 0 and matched_count > 0

    # Count catalog files in .rommgr/dats/ (legacy) or catalogs dir
    catalogs_count = 0
    if project_root is not None:
        for _dat_dir in [
            project_root / ".rommgr" / "dats",
            project_root / ".rommgr" / "catalogs" / "nointro",
            project_root / ".rommgr" / "catalogs" / "redump",
        ]:
            try:
                catalogs_count += sum(
                    1 for f in _dat_dir.iterdir()
                    if f.suffix.lower() in {".dat", ".xml"}
                )
            except Exception:
                pass

    setup_checklist = {
        "library_root_set": bool(library_root),
        "scanned": scan_count > 0,
        "catalogs_loaded": catalogs_count > 0,
        "matched": matched_count > 0,
    }

    # Recently played games (last 5 by last_played_at)
    recently_played = []
    try:
        with repository.connect() as _rc:
            _rows = _rc.execute(
                "SELECT id, canonical_title, original_filename, platform, last_played_at FROM games "
                "WHERE last_played_at IS NOT NULL AND file_type = 'rom' "
                "ORDER BY last_played_at DESC LIMIT 5"
            ).fetchall()
            recently_played = [dict(r) for r in _rows]
    except Exception:
        pass

    result: dict = {
        "total_games": summary.total_games,
        "total_saves": summary.total_saves,
        "total_assets": summary.total_assets,
        "matched_games": matched,
        "unmatched_games": summary.total_games - matched,
        "duplicate_groups": len(dup_groups),
        "wasted_bytes": wasted,
        "last_scan_at": summary.last_scan_at,
        "last_scans_by_root": last_scans,
        "scan_days_ago": scan_days_ago,
        "stale": stale,
        "last_report_at": last_report_at,
        "last_report_mins_ago": last_report_mins_ago,
        # Two-DB: separate Android counts
        "android_total_games": android_summary.total_games if android_summary else None,
        "android_total_saves": android_summary.total_saves if android_summary else None,
        "android_last_scan_at": android_summary.last_scan_at if android_summary else None,
        "pc_db": "library_pc.db",
        "android_db": "library_android.db",
        # D8-P1: first-time setup
        "first_run": first_run,
        "setup_complete": setup_complete,
        "setup_checklist": setup_checklist,
        "recently_played": recently_played,
    }
    return result


def _build_games(
    repository: LibraryRepository,
    *,
    offset: int = 0,
    limit: int = 100,
    platform: str | None = None,
    status: str | None = None,
    source_root: str | None = None,
    file_type: str | None = "rom",
    search: str | None = None,
    play_status: str | None = None,
) -> dict:
    games, total = repository.get_games_paginated(
        offset=offset, limit=limit, platform=platform, status=status,
        source_root=source_root, file_type=file_type, search=search,
        play_status=play_status,
    )
    return {
        "games": games,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


def _count_companion_saves(source: Path, save_extensions: frozenset[str]) -> int:
    """Count save files alongside *source* that share its stem."""
    try:
        return sum(
            1 for f in source.parent.iterdir()
            if f != source and f.stem == source.stem and f.suffix.lower() in save_extensions
        )
    except OSError:
        return 0


def _build_plan(
    repository: LibraryRepository,
    opts: FormatOptions | None = None,
    save_extensions: frozenset[str] | None = None,
    source_root: str | None = None,
    library_root: str | None = None,
) -> dict:
    plan = build_plan(repository, opts)
    if plan.total == 0:
        return {
            "total": 0,
            "already_correct": 0,
            "pending": [],
            "conflicts": [],
            "total_saves_affected": 0,
        }
    exts = save_extensions or frozenset()
    pending_ops = plan.pending
    conflict_ops = plan.conflicts
    already_correct = plan.already_correct
    if source_root:
        root_lower = source_root.lower()
        pending_ops = [op for op in pending_ops if str(op.source_path).lower().startswith(root_lower)]
        conflict_ops = [op for op in conflict_ops if str(op.source_path).lower().startswith(root_lower)]
        already_correct = [op for op in already_correct if str(op.source_path).lower().startswith(root_lower)]
    # D8-2: determine library_root for device classification
    _lib_root_lower = library_root.lower() if library_root else None

    pending_rows = []
    total_saves = 0
    for op in pending_ops:
        companions = _count_companion_saves(op.source_path, exts)
        total_saves += companions
        # D8-2: tag each op with its device ("pc" or "android")
        src_lower = str(op.source_path).lower()
        if _lib_root_lower and src_lower.startswith(_lib_root_lower):
            device_tag = "pc"
        else:
            device_tag = "android"
        pending_rows.append({
            "platform": op.game.platform,
            "source": str(op.source_path),
            "source_name": op.source_path.name,
            "target": str(op.target_path),
            "target_name": op.target_path.name,
            "companion_saves": companions,
            "device": device_tag,
        })
    # Unmatched games (no canonical_title) filtered by source_root
    unmatched_games = repository.get_unresolved_games()
    if source_root:
        root_lower = source_root.lower()
        unmatched_games = [g for g in unmatched_games if g.source_path.lower().startswith(root_lower)]

    # Build set of platforms that have at least one matched game (catalog was loaded)
    with repository.connect() as _conn:
        _matched_plats = {
            row[0] for row in _conn.execute(
                "SELECT DISTINCT platform FROM games WHERE match_confidence IS NOT NULL AND platform IS NOT NULL"
            ).fetchall()
        }

    def _unmatched_reason(g) -> str:
        if not g.sha1:
            return "no_sha1"        # file wasn't hashed (quick scan?) — run full scan
        if g.platform and g.platform not in _matched_plats:
            return "no_dat"         # no DAT has been matched for this platform yet
        return "hash_not_found"     # hash computed but not in any loaded DAT

    unmatched_rows = [
        {"original_filename": g.original_filename, "platform": g.platform,
         "unmatched_reason": _unmatched_reason(g)}
        for g in unmatched_games
    ]

    return {
        "total": plan.total,
        "already_correct": len(already_correct),
        "pending": pending_rows,
        "conflicts": [
            {
                "source_name": op.source_path.name,
                "target_name": op.target_path.name,
                "reason": op.conflict_reason,  # "disk" | "collision"
            }
            for op in conflict_ops
        ],
        "total_saves_affected": total_saves,
        "unmatched_count": len(unmatched_rows),
        "unmatched": unmatched_rows,
    }


def _build_duplicates(
    repository: LibraryRepository,
    source_root: str | None = None,
    pc_root: str | None = None,
    ab_root: str | None = None,
) -> dict:
    import os as _os
    from rom_manager.database.repository import DuplicateGroup

    def _norm(p: str) -> str:
        """Normalize a path for cross-platform prefix comparison."""
        return _os.path.normcase(_os.path.normpath(p)).rstrip(_os.sep) + _os.sep

    groups = repository.get_duplicate_groups()
    if source_root:
        # Single-device mode: only entries under this root
        root_norm = _norm(source_root)
        filtered = []
        for g in groups:
            entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(root_norm)]
            if len(entries) >= 2:
                filtered.append(DuplicateGroup(sha1=g.sha1, entries=entries))
        groups = filtered
    elif pc_root and ab_root:
        # "Sistema completo" mode: exclude groups where every entry is an
        # intentional cross-device copy (one from PC, rest from Anbernic or
        # vice versa). Real duplicates have ≥2 entries on the SAME device.
        pc_norm = _norm(pc_root)
        ab_norm = _norm(ab_root)
        filtered = []
        for g in groups:
            pc_entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(pc_norm)]
            ab_entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(ab_norm)]
            # Keep group only if there are ≥2 entries on at least one device
            if len(pc_entries) >= 2 or len(ab_entries) >= 2:
                filtered.append(g)
        groups = filtered
    elif pc_root:
        # Only PC root given — show duplicates within that root
        pc_norm = _norm(pc_root)
        filtered = []
        for g in groups:
            entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(pc_norm)]
            if len(entries) >= 2:
                filtered.append(DuplicateGroup(sha1=g.sha1, entries=entries))
        groups = filtered
    # Sort by wasted bytes descending (largest duplicates first)
    groups = sorted(groups, key=lambda g: g.wasted_bytes, reverse=True)
    total_files = sum(len(g.entries) for g in groups)
    total_wasted = sum(g.wasted_bytes for g in groups)
    return {
        "groups": [
            {
                "sha1": g.sha1,
                "canonical_title": g.entries[0].canonical_title,
                "platform": g.entries[0].platform,
                "wasted_bytes": g.wasted_bytes,
                "entries": [
                    {"id": e.id, "source_path": e.source_path, "size_bytes": e.size_bytes}
                    for e in g.entries
                ],
            }
            for g in groups
        ],
        "total_files": total_files,
        "wasted_bytes": total_wasted,
    }


def _build_duplicates_two_repos(
    repository: LibraryRepository,
    repository_android: LibraryRepository,
    source_root: str | None = None,
    pc_root: str | None = None,
    ab_root: str | None = None,
) -> dict:
    """Two-DB version of duplicate detection.

    When both repos are the same object (no android DB configured), falls back to
    the single-repo implementation.  When they are different objects, performs
    within-repo duplicate detection separately and cross-repo detection via SHA1
    intersection.
    """
    import os as _os
    from rom_manager.database.repository import DuplicateGroup, DuplicateEntry

    def _norm(p: str) -> str:
        return _os.path.normcase(_os.path.normpath(p)).rstrip(_os.sep) + _os.sep

    # If only one DB (android repo == pc repo), delegate to original logic
    if repository_android is repository:
        return _build_duplicates(repository, source_root=source_root, pc_root=pc_root, ab_root=ab_root)

    # Collect groups from each repo independently
    pc_groups = repository.get_duplicate_groups()
    android_groups = repository_android.get_duplicate_groups()

    # If source_root supplied, filter to that root on the right repo
    if source_root:
        root_norm = _norm(source_root)
        lib_root = str(repository.database_path.parent.parent)  # approximate; use proper filter
        # Determine which repo the source_root belongs to
        # We just filter whichever has matching entries
        filtered_pc = []
        for g in pc_groups:
            entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(root_norm)]
            if len(entries) >= 2:
                filtered_pc.append(DuplicateGroup(sha1=g.sha1, entries=entries))
        filtered_android = []
        for g in android_groups:
            entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(root_norm)]
            if len(entries) >= 2:
                filtered_android.append(DuplicateGroup(sha1=g.sha1, entries=entries))
        all_groups = filtered_pc + filtered_android
        all_groups = sorted(all_groups, key=lambda g: g.wasted_bytes, reverse=True)
        total_files = sum(len(g.entries) for g in all_groups)
        total_wasted = sum(g.wasted_bytes for g in all_groups)
        return {
            "groups": [
                {
                    "sha1": g.sha1,
                    "canonical_title": g.entries[0].canonical_title,
                    "platform": g.entries[0].platform,
                    "wasted_bytes": g.wasted_bytes,
                    "entries": [
                        {"id": e.id, "source_path": e.source_path, "size_bytes": e.size_bytes}
                        for e in g.entries
                    ],
                }
                for g in all_groups
            ],
            "total_files": total_files,
            "wasted_bytes": total_wasted,
        }

    # Cross-device: find SHA1s present in both repos (intentional copies) and within-device dups
    pc_sha1_map: dict[str, list[DuplicateEntry]] = {}
    for g in pc_groups:
        pc_sha1_map[g.sha1] = g.entries

    android_sha1_map: dict[str, list[DuplicateEntry]] = {}
    for g in android_groups:
        android_sha1_map[g.sha1] = g.entries

    combined: list[DuplicateGroup] = []

    # Within-PC duplicates
    if pc_root:
        pc_norm = _norm(pc_root)
        for g in pc_groups:
            entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(pc_norm)]
            if len(entries) >= 2:
                combined.append(DuplicateGroup(sha1=g.sha1, entries=entries))
    else:
        combined.extend(pc_groups)

    # Within-Android duplicates
    if ab_root:
        ab_norm = _norm(ab_root)
        for g in android_groups:
            entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(ab_norm)]
            if len(entries) >= 2:
                combined.append(DuplicateGroup(sha1=g.sha1, entries=entries))
    else:
        combined.extend(android_groups)

    # Cross-device duplicates: SHA1 appears in both repos
    cross_sha1s = set(pc_sha1_map) & set(android_sha1_map)
    for sha1 in cross_sha1s:
        all_entries = pc_sha1_map[sha1] + android_sha1_map[sha1]
        combined.append(DuplicateGroup(sha1=sha1, entries=all_entries))

    # Deduplicate groups by sha1 (cross-device may overlap with within-device)
    seen: set[str] = set()
    deduped: list[DuplicateGroup] = []
    for g in combined:
        if g.sha1 not in seen:
            seen.add(g.sha1)
            deduped.append(g)

    deduped = sorted(deduped, key=lambda g: g.wasted_bytes, reverse=True)
    total_files = sum(len(g.entries) for g in deduped)
    total_wasted = sum(g.wasted_bytes for g in deduped)
    return {
        "groups": [
            {
                "sha1": g.sha1,
                "canonical_title": g.entries[0].canonical_title,
                "platform": g.entries[0].platform,
                "wasted_bytes": g.wasted_bytes,
                "entries": [
                    {"id": e.id, "source_path": e.source_path, "size_bytes": e.size_bytes}
                    for e in g.entries
                ],
            }
            for g in deduped
        ],
        "total_files": total_files,
        "wasted_bytes": total_wasted,
    }


def _build_folder_analysis(folder_path: str, config: AppConfig) -> dict:
    """Analyse a folder: count extensions, find broken PSX sets, flag conversion needs."""
    from pathlib import Path as _Path
    from collections import Counter

    _ROM_EXTS = {
        ".gba", ".gb", ".gbc", ".nes", ".snes", ".sfc", ".md", ".smd", ".gen",
        ".n64", ".z64", ".v64", ".nds", ".3ds", ".psx", ".ps1",
        ".iso", ".chd", ".cue", ".bin",
        ".cdi", ".gdi", ".pbp", ".elf",
        ".gcm", ".nkit", ".rvz", ".wbfs",
        ".nsp", ".xci",
    }
    _SAVE_EXTS = {".sav", ".srm", ".state", ".sta", ".mcr", ".mc"}
    _NEEDS_CONVERSION = {
        ".img":  "imagen de disco — puede ser CD-ROM (.img/.ccd) o HDD; verificar si acompaña .ccd/.sub",
        ".mdf":  "imagen Alcohol 120% — convertir a .chd o .cue/.bin con mdf2iso",
        ".mds":  "descriptor Alcohol 120% — acompaña .mdf",
        ".ccd":  "CloneCD descriptor — convertir a .chd con chdman",
        ".sub":  "datos de subcódigo CloneCD — acompaña .ccd/.img",
        ".nrg":  "imagen Nero — convertir a .iso o .chd",
        ".ecm":  "Error Code Modeler — descomprimir con ecmtools antes de convertir a CHD",
    }

    p = _Path(folder_path)
    if not p.is_dir():
        return {"error": f"Carpeta no encontrada: {folder_path}", "extensions": [], "cue_missing_bin": [], "bin_orphan": [], "needs_conversion": []}

    ext_counter: Counter[str] = Counter()
    cue_files: list[_Path] = []
    bin_files: set[str] = set()   # stems in lower case

    for f in p.rglob("*"):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        ext_counter[ext] += 1
        if ext == ".cue":
            cue_files.append(f)
        elif ext == ".bin":
            bin_files.add(f.stem.lower())

    # Classify extensions
    extensions = []
    for ext, count in sorted(ext_counter.items(), key=lambda x: -x[1]):
        if ext in _ROM_EXTS:
            cat = "rom"
        elif ext in _SAVE_EXTS:
            cat = "save"
        elif ext in _NEEDS_CONVERSION:
            cat = "needs_conversion"
        elif ext in {".jpg", ".jpeg", ".png", ".webp", ".xml", ".txt", ".cfg", ".db"}:
            cat = "asset/meta"
        else:
            cat = "unknown"
        extensions.append({"ext": ext or "(sin extensión)", "count": count, "category": cat})

    # Check CUE integrity: find .cue files whose referenced .bin is missing
    import re as _re
    cue_missing_bin: list[str] = []
    for cue in cue_files:
        try:
            text = cue.read_text(errors="replace")
            bins_referenced = _re.findall(r'FILE\s+"?([^"]+\.bin)"?', text, _re.IGNORECASE)
            for bin_name in bins_referenced:
                if not (cue.parent / bin_name).exists():
                    cue_missing_bin.append(cue.name)
                    break
        except OSError:
            pass

    # Orphan BINs: .bin files whose stem doesn't match any .cue file stem
    cue_stems = {c.stem.lower() for c in cue_files}
    bin_orphan = [
        f.name for f in p.rglob("*.bin")
        if f.is_file() and f.stem.lower() not in cue_stems
    ]

    # Formats needing conversion
    needs_conversion = [
        {"ext": ext, "note": note}
        for ext, note in _NEEDS_CONVERSION.items()
        if ext in ext_counter
    ]

    return {
        "folder": folder_path,
        "extensions": extensions,
        "cue_missing_bin": sorted(cue_missing_bin),
        "bin_orphan": sorted(bin_orphan),
        "needs_conversion": needs_conversion,
    }


def _build_ra_duplicates(repository: LibraryRepository, config: AppConfig) -> dict:
    """Find title-based duplicates where one version has RA support and another doesn't.

    Groups games with the same normalized title by platform. For each group with ≥2
    entries, checks RA cache to see which versions have achievements. Returns groups
    where at least one version has achievements and at least one doesn't.
    """
    from collections import defaultdict
    import json
    from pathlib import Path as _Path
    from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id
    from rom_manager.retroachievements.ra_client import _parse_game_list
    from rom_manager.retroachievements.ra_checker import _normalize_title

    cache_dir = config.project_root / ".rommgr" / "ra_cache"

    with repository.connect() as conn:
        rows = conn.execute(
            "SELECT id, original_filename, source_path, platform, md5, canonical_title, size_bytes "
            "FROM games WHERE file_type = 'rom' ORDER BY platform, original_filename"
        ).fetchall()

    # Build platform → md5 → achievements lookup from local RA cache
    platform_hash_map: dict[str, dict[str, int]] = {}
    platforms_seen = {r["platform"] for r in rows if r["platform"]}
    for plat in platforms_seen:
        console_id = get_ra_console_id(plat or "")
        if not console_id:
            continue
        cache_file = cache_dir / f"ra_hashes_{console_id}.json"
        if not cache_file.exists():
            continue
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            hash_lib = _parse_game_list(data)
            platform_hash_map[plat] = {md5: game.achievements for md5, game in hash_lib.items()}
        except Exception:
            continue

    if not platform_hash_map:
        return {"groups": [], "total_groups": 0, "wasted_bytes": 0,
                "note": "No hay caché de RetroAchievements. Ejecuta primero la comprobación RA en Tools."}

    # Group games by (platform, normalized_title)
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        plat = row["platform"] or "unknown"
        title = row["canonical_title"] or _Path(row["original_filename"]).stem
        key = (plat, _normalize_title(title))
        groups[key].append({
            "id": row["id"],
            "filename": row["original_filename"],
            "source_path": row["source_path"],
            "platform": row["platform"],
            "md5": row["md5"],
            "size_bytes": int(row["size_bytes"]),
        })

    result_groups = []
    for (plat, norm_title), entries in groups.items():
        if len(entries) < 2:
            continue
        hash_map = platform_hash_map.get(plat)
        if not hash_map:
            continue

        annotated = []
        for e in entries:
            md5_lower = (e["md5"] or "").lower()
            achievements = hash_map.get(md5_lower, -1)  # -1 = not in RA cache
            annotated.append({**e, "ra_achievements": achievements, "ra_supported": achievements > 0})

        has_supported = any(a["ra_supported"] for a in annotated)
        has_unsupported = any(not a["ra_supported"] for a in annotated)
        if not (has_supported and has_unsupported):
            continue

        # Sort: RA-supported first, then prefer Spanish/Spain region within each tier
        _SPANISH_TAGS = {"spain", "es", "spa", "español", "spanish", "s"}

        def _is_spanish(filename: str) -> bool:
            import re as _re
            tags = _re.findall(r"\(([^)]+)\)", filename.lower())
            return any(
                any(t.strip() == s for s in _SPANISH_TAGS)
                for tag in tags
                for t in tag.split(",")
            )

        def _sort_key(entry: dict) -> tuple:
            # (0 = RA supported, 1 = not), (0 = Spanish, 1 = not), filename
            ra_tier = 0 if entry["ra_supported"] else 1
            lang_tier = 0 if _is_spanish(entry["filename"]) else 1
            return (ra_tier, lang_tier, entry["filename"])

        annotated.sort(key=_sort_key)

        wasted = sum(a["size_bytes"] for a in annotated if not a["ra_supported"])
        result_groups.append({
            "platform": plat,
            "normalized_title": norm_title,
            "entries": annotated,
            "wasted_bytes": wasted,
        })

    result_groups.sort(key=lambda g: g["wasted_bytes"], reverse=True)
    return {
        "groups": result_groups,
        "total_groups": len(result_groups),
        "wasted_bytes": sum(g["wasted_bytes"] for g in result_groups),
    }


def _build_assets(repository: LibraryRepository, source_root: str | None = None) -> dict:
    return {"stats": repository.get_asset_platform_stats(source_root=source_root)}


def _build_sync_log(repository: LibraryRepository) -> dict:
    entries = repository.get_sync_log(limit=200)
    return {"entries": entries}


def _build_config(config: AppConfig) -> dict:
    def _db_size(p: Path) -> int | None:
        try:
            return p.stat().st_size if p.exists() else 0
        except OSError:
            return None

    return {
        "library_root": str(config.library_root) if config.library_root else None,
        "anbernic_root": config.anbernic_root or "",
        "device_name": config.device_name or "Consola Android",
        "rclone_remote": config.rclone_remote or None,
        "web_host": config.web_host,
        "web_port": config.web_port,
        "screenscraper_user": config.screenscraper_user or None,
        "screenscraper_pass": config.screenscraper_pass or None,
        "chdman": config.chdman,
        "adb": config.adb,
        "ra_api_key": config.ra_api_key or None,
        # Two-DB info
        "pc_db_path": str(config.database_path),
        "pc_db_size": _db_size(config.database_path),
        "android_db_path": str(config.database_path_android),
        "android_db_size": _db_size(config.database_path_android),
        # Inbox (Pilar 2)
        "inbox_path": config.inbox_path or "",
        "inbox_target_root": config.inbox_target_root or "",
        "inbox_auto_process": config.inbox_auto_process,
        "inbox_delete_source": config.inbox_delete_source,
        # Multi-source sync
        "sync_sources": [
            {"name": s.name, "local_dir": s.local_dir, "remote": s.remote, "sync_all": s.sync_all}
            for s in config.sync_sources
        ],
    }


def _build_scrape_summary(repository: LibraryRepository) -> dict:
    return {"platforms": repository.get_scraped_platform_summary()}


def _parse_format_opts(qs: dict) -> FormatOptions:
    return FormatOptions(
        include_region=qs.get("include_region", ["1"])[0] != "0",
        include_revision=qs.get("include_revision", ["1"])[0] != "0",
        include_platform=qs.get("include_platform", ["0"])[0] != "0",
        include_sha=qs.get("include_sha", ["0"])[0] != "0",
        sha_length=min(40, max(4, int(qs.get("sha_length", ["8"])[0]))),
    )


def _repo_for_path(path_str: str, repository: LibraryRepository, repository_android: LibraryRepository, config: AppConfig) -> LibraryRepository:
    """Return the correct repository based on whether path_str falls under library_root (PC) or not (Android).

    Normalizes path separators before comparison so that forward-slash and
    backslash variants of the same Windows path match correctly.
    """
    import os as _os
    if not path_str:
        return repository
    lib_root_raw = str(config.library_root or "")
    if not lib_root_raw:
        return repository
    # Normalize: lowercase + replace all separators to the OS sep
    def _norm_lower(p: str) -> str:
        return p.replace("/", _os.sep).replace("\\", _os.sep).lower().rstrip(_os.sep)
    lib_root_norm = _norm_lower(lib_root_raw)
    path_norm = _norm_lower(path_str)
    if path_norm.startswith(lib_root_norm):
        return repository
    return repository_android


def _utc_now_str() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


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
                elif path == "/api/cable-sync-log":
                    log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
                    if log_path.exists():
                        with open(log_path, "r", encoding="utf-8", errors="replace") as _lf:
                            lines = _lf.readlines()
                        tail = "".join(lines[-500:])
                        self._send_json({"log": tail, "lines": len(lines)})
                    else:
                        self._send_json({"log": "", "lines": 0})
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
                elif path == "/api/inbox-run":
                    self._handle_inbox_run(data)
                elif path == "/api/setup-run":
                    self._handle_setup_run(data)
                elif path == "/api/create-library-structure":
                    self._handle_create_library_structure()
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
            with _job_lock:
                if _jobs["match"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["match"] = True

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

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started"})

        def _handle_fix_platforms(self) -> None:
            from rom_manager.detection.platform_detector import detect_platform
            updated = repository.backfill_platforms(detect_platform)
            self._send_json({"updated": updated})

        def _handle_create_library_structure(self) -> None:
            """Create the canonical ES-DE folder structure under library_root."""
            from pathlib import Path as _Path
            if not config.library_root:
                self._send_json({"error": "library_root no configurado"})
                return
            root = _Path(config.library_root)
            created: list[str] = []
            skipped: list[str] = []
            # Platform folders + media subfolders
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
            # Special folders
            for special in ("saves", "bios", "inbox"):
                d = root / special
                if not d.exists():
                    d.mkdir(parents=True, exist_ok=True)
                    created.append(special)
                else:
                    skipped.append(special)
            self._send_json({"created": created, "skipped": skipped, "root": str(root)})

        def _handle_organize_library(self, data: dict) -> None:
            """Move ROMs to <library_root>/<es_platform_folder>/<filename> and update DB."""
            import shutil as _shutil
            from pathlib import Path as _Path
            dry_run = data.get("dry_run", True)
            if not config.library_root:
                self._send_json({"error": "library_root no configurado"})
                return
            root = _Path(config.library_root)
            with repository.connect() as conn:
                rows = conn.execute(
                    "SELECT id, source_path, platform FROM games WHERE source_path IS NOT NULL"
                ).fetchall()
            moves: list[dict] = []
            errors: list[str] = []
            for row in rows:
                game_id, src_str, platform = row[0], row[1], row[2] or ""
                src = _Path(src_str)
                if not src.exists():
                    continue
                es_folder = _ES_PLATFORM_FOLDERS.get(platform, "")
                if not es_folder:
                    continue  # Unknown platform — skip
                target_dir = root / es_folder
                target = target_dir / src.name
                if src == target:
                    continue  # Already in the right place
                moves.append({
                    "source": str(src),
                    "target": str(target),
                    "platform": platform,
                    "filename": src.name,
                })
                if not dry_run:
                    try:
                        target_dir.mkdir(parents=True, exist_ok=True)
                        if target.exists():
                            errors.append(f"Conflicto: {src.name} ya existe en {es_folder}/")
                            continue
                        _shutil.move(str(src), str(target))
                        with repository.connect() as conn:
                            conn.execute(
                                "UPDATE games SET source_path = ?, updated_at = ? WHERE source_path = ?",
                                (str(target), utc_now(), str(src))
                            )
                            conn.commit()
                    except Exception as exc:
                        errors.append(f"{src.name}: {exc}")
            self._send_json({
                "dry_run": dry_run,
                "moves": len(moves),
                "errors": errors,
                "preview": moves[:30] if dry_run else [],
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
            with _job_lock:
                if _jobs["health_check"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["health_check"] = True

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

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started"})

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


def _auto_sync_loop(config: AppConfig, get_repo_fn) -> None:
    """Daemon thread: polls ADB every 10 s, triggers Cable Sync when a device connects."""
    import time as _time
    import datetime as _dt

    global _auto_sync_enabled, _auto_sync_last_devices, _auto_sync_status

    _POLL_INTERVAL = 10        # seconds between ADB polls
    _COOLDOWN      = 30        # seconds to wait after a sync before syncing again
    _last_sync_ts: float = 0.0

    while True:
        try:
            _time.sleep(_POLL_INTERVAL)

            if not _auto_sync_enabled:
                continue

            # Don't poll if a cable_sync job is already running
            with _job_lock:
                cable_running = _jobs.get("cable_sync", False)
            if cable_running:
                continue

            # Cooldown: avoid re-triggering immediately after a sync
            if _time.monotonic() - _last_sync_ts < _COOLDOWN:
                continue

            # Require library_root to be configured
            if not config.library_root:
                continue

            # Poll ADB devices
            try:
                from rom_manager.sync.adb_transport import list_devices
                devices = list_devices(config.adb, timeout=8)
            except Exception:
                # adb not found or timed out — silently skip
                continue

            current_serials = {d.serial for d in devices if d.ready}

            # Detect newly connected devices
            new_serials = current_serials - _auto_sync_last_devices
            _auto_sync_last_devices = current_serials

            if not new_serials:
                continue

            # If known_devices filter is set, only react to those
            known = config.auto_sync_known_devices
            if known:
                new_serials = {s for s in new_serials if s in known}
            if not new_serials:
                continue

            serial = next(iter(new_serials))
            _logger.info("Auto-sync: new device %s — starting sync", serial)

            now_str = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            _auto_sync_status = {
                "state": "syncing",
                "last_device": serial,
                "last_sync_at": now_str,
                "last_error": None,
            }

            # Mark cable_sync job as running
            with _job_lock:
                if _jobs.get("cable_sync"):
                    _auto_sync_status["state"] = "waiting"
                    continue
                _jobs["cable_sync"] = True

            _last_sync_ts = _time.monotonic()

            def _run_auto_sync(serial: str = serial) -> None:
                import os
                import shutil
                import datetime as _dt2
                from pathlib import PurePosixPath

                global _auto_sync_status

                _log_file = None
                try:
                    pc_root   = config.library_root
                    direction = config.auto_sync_direction
                    android_path = config.auto_sync_android_path.rstrip("/")
                    save_exts = frozenset(config.save_extensions)
                    what = ["saves"]

                    log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                    _log_file = open(log_path, "a", encoding="utf-8", buffering=1)
                    ts0 = _dt2.datetime.now(tz=_dt2.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    _log_file.write(
                        f"\n=== AUTO-SYNC {ts0} | device={serial} direction={direction} ===\n"
                    )

                    def _log(tag: str, src: str, dst: str = "", note: str = "") -> None:
                        ts = _dt2.datetime.now(tz=_dt2.timezone.utc).strftime("%H:%M:%S")
                        arrow = (" -> " + dst) if dst else ""
                        note_part = (" | " + note) if note else ""
                        _log_file.write(f"[{ts}] [{tag:5s}] {src}{arrow}{note_part}\n")

                    def _wanted_name(name: str) -> bool:
                        if name.startswith("."):
                            return False
                        suffix = Path(name).suffix.lower()
                        return suffix in save_exts

                    copied = skipped = errors = 0
                    copied_bytes = 0

                    def _update_prog(fname: str = "") -> None:
                        _cable_progress.update({
                            "copied": copied,
                            "bytes_copied": copied_bytes,
                            "speed_bps": 0.0,
                            "current_file": fname,
                        })

                    from rom_manager.sync.adb_transport import AdbTransport
                    transport = AdbTransport(config.adb, serial, timeout=60)

                    def _adb_copy_to_pc(adb_info, rel_posix: str) -> None:
                        nonlocal copied, errors, copied_bytes
                        name = PurePosixPath(adb_info.android_path).name
                        local_dst = pc_root / Path(rel_posix.replace("/", os.sep))
                        try:
                            size = transport.pull(adb_info.android_path, local_dst, dry_run=False)
                            _log("ADB←", adb_info.android_path, str(local_dst))
                            copied += 1
                            copied_bytes += size
                            _update_prog(name)
                        except OSError as exc:
                            _log("ERROR", adb_info.android_path, str(local_dst), str(exc))
                            errors += 1

                    def _adb_copy_to_device(local_src: Path, rel_posix: str) -> None:
                        nonlocal copied, errors, copied_bytes
                        android_dst = android_path + "/" + rel_posix
                        try:
                            size = transport.push(local_src, android_dst, dry_run=False)
                            _log("ADB→", str(local_src), android_dst)
                            copied += 1
                            copied_bytes += size
                            _update_prog(local_src.name)
                        except OSError as exc:
                            _log("ERROR", str(local_src), android_dst, str(exc))
                            errors += 1

                    _cable_progress.update({
                        "copied": 0, "bytes_copied": 0, "speed_bps": 0.0,
                        "current_file": "Auto-sync: listando saves en el dispositivo…",
                    })

                    ab_adb_files = transport.ls_recursive(android_path)
                    android_prefix = android_path + "/"

                    def _iter_pc_files():
                        for dirpath, dirs, files in os.walk(pc_root):
                            dirs[:] = [d for d in dirs if not d.startswith(".")]
                            for fname in files:
                                yield Path(dirpath) / fname

                    if direction == "pc_to_anbernic":
                        for src in _iter_pc_files():
                            if not _wanted_name(src.name):
                                continue
                            rel = src.relative_to(pc_root)
                            _adb_copy_to_device(src, rel.as_posix())

                    elif direction == "anbernic_to_pc":
                        for info in ab_adb_files:
                            name = PurePosixPath(info.android_path).name
                            if not _wanted_name(name):
                                continue
                            rel_posix = info.android_path.removeprefix(android_prefix)
                            _adb_copy_to_pc(info, rel_posix)

                    else:  # newest
                        ab_index = {
                            info.android_path.removeprefix(android_prefix): info
                            for info in ab_adb_files
                            if _wanted_name(PurePosixPath(info.android_path).name)
                        }
                        pc_index: dict = {}
                        for f in _iter_pc_files():
                            if _wanted_name(f.name):
                                pc_index[f.relative_to(pc_root).as_posix()] = f

                        for rel_posix in sorted(set(pc_index) | set(ab_index)):
                            pc_f   = pc_index.get(rel_posix)
                            ab_inf = ab_index.get(rel_posix)
                            if pc_f and ab_inf:
                                if pc_f.stat().st_mtime > ab_inf.mtime:
                                    _adb_copy_to_device(pc_f, rel_posix)
                                elif ab_inf.mtime > pc_f.stat().st_mtime:
                                    _adb_copy_to_pc(ab_inf, rel_posix)
                                else:
                                    skipped += 1
                            elif pc_f:
                                _adb_copy_to_device(pc_f, rel_posix)
                            elif ab_inf:
                                _adb_copy_to_pc(ab_inf, rel_posix)

                    ts1 = _dt2.datetime.now(tz=_dt2.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    _log_file.write(
                        f"=== Auto-sync fin {ts1} | copied={copied} skipped={skipped} errors={errors} ===\n"
                    )

                    _job_results["cable_sync"] = {
                        "dry_run": False,
                        "direction": direction,
                        "use_adb": True,
                        "copied": copied,
                        "skipped": skipped,
                        "sha1_skipped": 0,
                        "safe_mode_skipped_overwrites": 0,
                        "errors": errors,
                        "copied_bytes": copied_bytes,
                        "cancelled": False,
                        "details": [],
                        "pc_file_count": 0,
                        "ab_file_count": 0,
                        "auto_sync": True,
                    }

                    finish_ts = _dt2.datetime.now(tz=_dt2.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    _auto_sync_status = {
                        "state": "idle",
                        "last_device": serial,
                        "last_sync_at": finish_ts,
                        "last_error": None if errors == 0 else f"{errors} errores",
                    }

                except Exception as exc:
                    _logger.exception("Auto-sync error: %s", exc)
                    _auto_sync_status = {
                        "state": "idle",
                        "last_device": serial,
                        "last_sync_at": _auto_sync_status.get("last_sync_at"),
                        "last_error": str(exc),
                    }
                    _job_results["cable_sync"] = {"error": str(exc), "auto_sync": True}
                finally:
                    if _log_file is not None:
                        try:
                            _log_file.close()
                        except Exception:
                            pass
                    with _job_lock:
                        _cable_progress.clear()
                        _jobs["cable_sync"] = False

            threading.Thread(target=_run_auto_sync, daemon=True).start()

        except Exception as exc:
            # Never crash the daemon
            _logger.debug("Auto-sync daemon exception: %s", exc)
            try:
                _auto_sync_status["state"] = "waiting"
            except Exception:
                pass


# ── SD card auto-sync daemon ───────────────────────────────────────────────────

def _run_sd_auto_sync(config: AppConfig, get_repo_fn) -> None:  # noqa: ARG001
    """Run a filesystem Cable Sync triggered by SD card insertion."""
    import os
    import shutil
    import datetime as _dt2

    global _sd_sync_status

    _log_file = None
    copied = 0
    skipped = 0
    errors = 0
    copied_bytes = 0

    try:
        pc_root = config.library_root
        ab_root = Path(config.anbernic_root)
        direction = config.auto_sync_direction or "newest"
        save_exts = frozenset(config.save_extensions)

        log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        _log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        ts0 = _dt2.datetime.now(tz=_dt2.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _log_file.write(
            f"\n=== SD-AUTO-SYNC {ts0} | direction={direction} | ab={config.anbernic_root} ===\n"
        )

        def _iter_files(root: Path):
            try:
                for entry in os.scandir(root):
                    if entry.is_dir(follow_symlinks=False):
                        yield from _iter_files(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        yield Path(entry.path)
            except PermissionError:
                pass

        def _wanted(p: Path) -> bool:
            return p.suffix.lower() in save_exts

        def _rel(p: Path, root: Path) -> Path:
            try:
                return p.relative_to(root)
            except ValueError:
                return p

        def _mtime(p: Path) -> float:
            try:
                return p.stat().st_mtime
            except OSError:
                return 0.0

        def _copy(src: Path, dst: Path) -> None:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        if pc_root is None:
            _log_file.write("ERROR: library_root not configured\n")
            return

        if direction in ("pc_to_anbernic", "newest"):
            for f in _iter_files(pc_root):
                if not _wanted(f):
                    continue
                rel = _rel(f, pc_root)
                dst = ab_root / rel
                if dst.exists():
                    if direction == "newest" and _mtime(f) <= _mtime(dst):
                        skipped += 1
                        continue
                    elif direction == "pc_to_anbernic":
                        pass  # always overwrite
                try:
                    sz = f.stat().st_size
                    _copy(f, dst)
                    copied += 1
                    copied_bytes += sz
                    _log_file.write(f"COPY pc→ab  {rel}\n")
                except Exception as e:
                    errors += 1
                    _log_file.write(f"ERROR pc→ab {rel}: {e}\n")

        if direction in ("anbernic_to_pc", "newest"):
            for f in _iter_files(ab_root):
                if not _wanted(f):
                    continue
                rel = _rel(f, ab_root)
                dst = pc_root / rel
                if dst.exists():
                    if direction == "newest" and _mtime(f) <= _mtime(dst):
                        skipped += 1
                        continue
                    elif direction == "anbernic_to_pc":
                        pass
                try:
                    sz = f.stat().st_size
                    _copy(f, dst)
                    copied += 1
                    copied_bytes += sz
                    _log_file.write(f"COPY ab→pc  {rel}\n")
                except Exception as e:
                    errors += 1
                    _log_file.write(f"ERROR ab→pc {rel}: {e}\n")

        finish_ts = _dt2.datetime.now(tz=_dt2.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _log_file.write(
            f"=== DONE copied={copied} skipped={skipped} errors={errors} bytes={copied_bytes} ===\n"
        )

        _job_results["cable_sync"] = {
            "dry_run": False,
            "direction": direction,
            "use_adb": False,
            "copied": copied,
            "skipped": skipped,
            "sha1_skipped": 0,
            "safe_mode_skipped_overwrites": 0,
            "errors": errors,
            "copied_bytes": copied_bytes,
            "cancelled": False,
            "details": [],
            "pc_file_count": 0,
            "ab_file_count": 0,
            "auto_sync": True,
            "source": "sd_card",
        }

        _sd_sync_status.update({
            "state": "idle",
            "last_sync_at": finish_ts,
        })

    except Exception as exc:
        _logger.exception("SD auto-sync error: %s", exc)
        _sd_sync_status.update({"state": "idle"})
        _job_results["cable_sync"] = {"error": str(exc), "auto_sync": True, "source": "sd_card"}
    finally:
        if _log_file is not None:
            try:
                _log_file.close()
            except Exception:
                pass
        with _job_lock:
            _cable_progress.clear()
            _jobs["cable_sync"] = False


def _sd_card_sync_loop(config: AppConfig, get_repo_fn) -> None:
    """Daemon thread: polls for SD card drive letter, triggers Cable Sync when inserted."""
    import time as _time

    global _sd_sync_status

    _last_available = False
    _last_sync_at = 0.0
    COOLDOWN = 60.0
    POLL_INTERVAL = 8.0

    while True:
        try:
            _time.sleep(POLL_INTERVAL)
            if not config.anbernic_root or not config.library_root or not config.auto_sync_enabled:
                _sd_sync_status["state"] = "disabled"
                _last_available = False
                continue

            ab_path = Path(config.anbernic_root)
            try:
                currently_available = ab_path.exists() and ab_path.is_dir()
            except Exception:
                currently_available = False

            just_inserted = currently_available and not _last_available
            _last_available = currently_available

            if currently_available:
                _sd_sync_status["state"] = "watching"
                _sd_sync_status["drive"] = config.anbernic_root
            else:
                _sd_sync_status["state"] = "waiting"
                _sd_sync_status.pop("drive", None)

            if just_inserted:
                now = _time.monotonic()
                if now - _last_sync_at < COOLDOWN:
                    continue
                with _job_lock:
                    if _jobs.get("cable_sync"):
                        continue
                    _jobs["cable_sync"] = True

                _sd_sync_status["state"] = "syncing"
                import datetime as _dt_sd
                _sd_sync_status["last_sync_at"] = _dt_sd.datetime.now(
                    tz=_dt_sd.timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
                _last_sync_at = now

                threading.Thread(
                    target=_run_sd_auto_sync,
                    args=(config, get_repo_fn),
                    daemon=True,
                ).start()

        except Exception as exc:
            _logger.debug("SD sync daemon exception: %s", exc)
            try:
                _sd_sync_status["state"] = "waiting"
            except Exception:
                pass


# ── Inbox (Pilar 2) ───────────────────────────────────────────────────────────

_PLATFORM_FOLDERS: dict[str, str] = {
    "gba": "Game Boy Advance",
    "gbc": "Game Boy Color",
    "gb": "Game Boy",
    "snes": "Super Nintendo",
    "nes": "NES",
    "n64": "Nintendo 64",
    "nds": "Nintendo DS",
    "psx": "PlayStation",
    "ps1": "PlayStation",
    "ps2": "PlayStation 2",
    "psp": "PSP",
    "megadrive": "Mega Drive",
    "genesis": "Mega Drive",
    "gg": "Game Gear",
    "sms": "Master System",
    "saturn": "Saturn",
    "dreamcast": "Dreamcast",
    "gamecube": "GameCube",
    "wii": "Wii",
    "wiiu": "Wii U",
    "3ds": "Nintendo 3DS",
    "mame": "Arcade",
    "neogeo": "Neo Geo",
    "lynx": "Atari Lynx",
    "jaguar": "Atari Jaguar",
    "atari2600": "Atari 2600",
    "atari7800": "Atari 7800",
}

_DISC_EXTENSIONS_INBOX = frozenset({".cue", ".bin", ".iso", ".img", ".mdf", ".mds", ".ccd", ".chd"})
_ROM_EXTENSIONS_INBOX = frozenset({
    ".nes", ".sfc", ".smc", ".n64", ".z64", ".v64", ".gb", ".gbc", ".gba",
    ".nds", ".3ds", ".cia", ".gcm", ".wbfs", ".sms", ".gg", ".gen", ".pbp",
    ".cso", ".a26", ".a52", ".a78", ".lnx", ".j64", ".jag", ".md",
})


def _platform_folder_name(platform: str) -> str:
    """Map a platform ID/name to a human-readable folder name."""
    if not platform:
        return "Unknown"
    key = platform.lower().replace(" ", "").replace("-", "")
    # Direct lookup first
    if platform.lower() in _PLATFORM_FOLDERS:
        return _PLATFORM_FOLDERS[platform.lower()]
    # Try stripped key
    for k, v in _PLATFORM_FOLDERS.items():
        if k.replace(" ", "").replace("-", "") == key:
            return v
    return platform


def _build_inbox_scan(inbox_path_str: str) -> dict:
    """Scan the inbox folder and return summary + file list."""
    import zipfile as _zf
    from rom_manager.detection.platform_detector import detect_platform as _detect_platform

    inbox = Path(inbox_path_str).resolve()
    if not inbox.exists() or not inbox.is_dir():
        return {"error": f"Carpeta no encontrada: {inbox_path_str}", "files": [], "total": 0}

    files_out: list[dict] = []
    total_bytes = 0
    by_platform: dict[str, int] = {}
    zips = 0
    unrecognized = 0

    for entry in sorted(inbox.iterdir()):
        # Skip hidden files and internal subfolders (_extracted, _processed)
        if entry.name.startswith(".") or entry.name.startswith("_"):
            continue
        if entry.is_dir():
            continue
        if not entry.is_file():
            continue

        ext = entry.suffix.lower()
        size_bytes = 0
        try:
            size_bytes = entry.stat().st_size
        except OSError:
            pass
        total_bytes += size_bytes

        # Determine type
        if ext == ".zip":
            file_type = "zip"
            zips += 1
            # Peek inside ZIP to guess platform
            platform_guess = None
            try:
                with _zf.ZipFile(entry, "r") as zobj:
                    names = zobj.namelist()
                    for inner in names:
                        inner_ext = Path(inner).suffix.lower()
                        if inner_ext in _DISC_EXTENSIONS_INBOX:
                            file_type = "zip"  # remains zip but disc content
                            break
                        if inner_ext in _ROM_EXTENSIONS_INBOX or inner_ext in _DISC_EXTENSIONS_INBOX:
                            inner_path = inbox / inner
                            platform_guess = _detect_platform(inner_path)
                            if platform_guess:
                                break
                    # If still no guess, try folder context from zip name
                    if not platform_guess:
                        platform_guess = _detect_platform(entry)
            except Exception:
                platform_guess = _detect_platform(entry)
            needs_extraction = True
        elif ext in _DISC_EXTENSIONS_INBOX:
            file_type = "disc_image"
            platform_guess = _detect_platform(entry)
            needs_extraction = False
        elif ext in _ROM_EXTENSIONS_INBOX:
            file_type = "rom"
            platform_guess = _detect_platform(entry)
            needs_extraction = False
        else:
            file_type = "unknown"
            platform_guess = None
            unrecognized += 1
            needs_extraction = False

        if platform_guess:
            by_platform[platform_guess] = by_platform.get(platform_guess, 0) + 1

        files_out.append({
            "name": entry.name,
            "path": str(entry),
            "size_bytes": size_bytes,
            "type": file_type,
            "platform_guess": platform_guess,
            "needs_extraction": needs_extraction,
        })

    return {
        "files": files_out,
        "total": len(files_out),
        "total_bytes": total_bytes,
        "by_platform": by_platform,
        "zips": zips,
        "unrecognized": unrecognized,
        "inbox_path": str(inbox),
    }


def _run_setup_pipeline(
    library_root: str,
    options: dict,
    repository: "LibraryRepository",
    config: "AppConfig",
) -> None:
    """Background job: first-time setup wizard pipeline (junk → zip → scan → match → plan)."""
    from rom_manager.scanner import scan_library
    from rom_manager.catalog.matcher import CatalogMatcher
    from rom_manager.planner import build_plan
    from rom_manager.planner.operation_planner import FormatOptions
    from rom_manager.converters.zip_extractor import find_zip_files, extract_zip

    logger = _logger
    source = Path(library_root).resolve()

    def _upd(step: str, step_num: int, pct: int = 0, current_file: str = "") -> None:
        _setup_progress.update({
            "step": step,
            "step_num": step_num,
            "total_steps": 5,
            "current_file": current_file,
            "pct": pct,
        })

    result: dict = {
        "junk_deleted": 0,
        "junk_freed_bytes": 0,
        "zips_extracted": 0,
        "games_found": 0,
        "games_matched": 0,
        "plan_pending": 0,
    }

    try:
        # ── Step 1: Junk cleaning ────────────────────────────────────────────
        _upd("Limpiando archivos no relacionados", 1, 5)
        if options.get("clean_junk", False):
            junk_data = _build_junk_scan(str(source))
            if "categories" in junk_data:
                all_junk: list[str] = []
                for cat in junk_data["categories"]:
                    all_junk.extend(f["full_path"] for f in cat.get("files", []))
                deleted = freed = 0
                for fp in all_junk:
                    try:
                        p = Path(fp)
                        if p.is_file():
                            sz = p.stat().st_size
                            p.unlink()
                            deleted += 1
                            freed += sz
                    except OSError:
                        pass
                result["junk_deleted"] = deleted
                result["junk_freed_bytes"] = freed

        # ── Step 2: ZIP extraction ───────────────────────────────────────────
        _upd("Extrayendo ZIPs", 2, 20)
        if options.get("extract_zips", True):
            zip_files = find_zip_files(source)
            extracted = 0
            total_zips = len(zip_files)
            for idx, zp in enumerate(zip_files, 1):
                try:
                    rel = str(zp.relative_to(source))
                except ValueError:
                    rel = zp.name
                pct = 20 + int((idx / max(total_zips, 1)) * 15)
                _upd("Extrayendo ZIPs", 2, pct, rel)
                r = extract_zip(zp, dry_run=False, delete_source=False)
                if r.success:
                    extracted += 1
            result["zips_extracted"] = extracted

        # ── Step 3: Scan library ─────────────────────────────────────────────
        _upd("Escaneando biblioteca", 3, 35)
        if options.get("scan", True):
            def _scan_cb(files_seen: int, roms: int, current_file: str = "") -> None:
                _upd("Escaneando biblioteca", 3, 35 + min(25, int(roms / max(files_seen, 1) * 25)), current_file)

            scan_r = scan_library(source, config, repository, logger, quick=False, progress_cb=_scan_cb)
            result["games_found"] = scan_r.roms_detected

        # ── Step 4: Catalog match ────────────────────────────────────────────
        _upd("Cruzando con catálogos No-Intro/Redump", 4, 65)
        if options.get("match", True):
            matcher = CatalogMatcher(
                nointro_dir=config.catalogs_nointro_dir,
                redump_dir=config.catalogs_redump_dir,
            )
            unresolved = repository.get_unresolved_games()
            matched = 0
            total_unresolved = len(unresolved)
            with repository.batch() as conn:
                for idx, game in enumerate(unresolved, 1):
                    pct = 65 + int((idx / max(total_unresolved, 1)) * 20)
                    _upd("Cruzando con catálogos No-Intro/Redump", 4, pct, game.original_filename)
                    m = matcher.match(game.sha1, game.original_filename)
                    if m is not None:
                        repository.update_match(
                            game.source_path,
                            canonical_title=m.title,
                            match_confidence=m.confidence,
                            catalog_source=m.catalog_source,
                            connection=conn,
                        )
                        matched += 1
            result["games_matched"] = matched

        # ── Step 5: Build plan ───────────────────────────────────────────────
        _upd("Preparando plan de renombrado", 5, 90)
        opts = FormatOptions()
        plan = build_plan(repository, opts)
        result["plan_pending"] = len(plan.pending)

        _upd("Completado", 5, 100)
        from rom_manager.scanner.rom_scanner import utc_now as _utc_now
        result["result_ts"] = _utc_now()
        _job_results["setup"] = result

    except Exception as exc:
        _job_results["setup"] = {"error": str(exc)}
        logger.exception("Setup pipeline error: %s", exc)
    finally:
        with _job_lock:
            _setup_progress.clear()
            _jobs["setup"] = False


def _run_inbox_pipeline(
    inbox_path_str: str,
    target_root_str: str,
    delete_source: bool,
    repository: LibraryRepository,
    config: "AppConfig",
) -> None:
    """Background job: extract → scan → match → plan → rename → move → cleanup."""
    import shutil as _shutil
    from rom_manager.converters.zip_extractor import find_zip_files, extract_zip
    from rom_manager.scanner import scan_library
    from rom_manager.catalog.matcher import CatalogMatcher
    from rom_manager.planner import build_plan
    from rom_manager.planner.operation_planner import FormatOptions
    from rom_manager.renamer.file_renamer import rename_rom_with_saves
    from rom_manager.scanner.rom_scanner import utc_now

    inbox = Path(inbox_path_str).resolve()
    target_root = Path(target_root_str).resolve() if target_root_str else (config.library_root or inbox)

    logger = _logger

    def _upd(step: str, step_num: int, processed: int = 0, total: int = 0, current_file: str = "") -> None:
        _inbox_progress.update({
            "step": step,
            "step_num": step_num,
            "total_steps": 6,
            "current_file": current_file,
            "processed": processed,
            "total": total,
        })

    try:
        # ── Step 1: Extract ZIPs ─────────────────────────────────────────────
        _upd("extracting", 1)
        zip_files = find_zip_files(inbox)
        extracted_count = 0
        source_zips: list[Path] = []
        for idx, zp in enumerate(zip_files, 1):
            # Skip internal folders
            if any(part.startswith("_") for part in zp.relative_to(inbox).parts[:-1]):
                continue
            _upd("extracting", 1, idx, len(zip_files), zp.name)
            result = extract_zip(zp, delete_source=False, dry_run=False)
            if result.success:
                extracted_count += 1
                source_zips.append(zp)
            else:
                logger.info("Inbox: skipped ZIP %s — %s", zp.name, result.skipped_reason or result.error)

        # ── Step 2: Scan inbox ───────────────────────────────────────────────
        _upd("scanning", 2)

        def _scan_progress_cb(files_seen: int, roms: int, current_file: str = "") -> None:
            _upd("scanning", 2, files_seen, 0, current_file)

        scan_result = scan_library(
            inbox, config, repository, logger,
            quick=False, progress_cb=_scan_progress_cb,
        )
        logger.info("Inbox scan: %d ROMs found", scan_result.roms_detected)

        # ── Step 3: Match catalog ────────────────────────────────────────────
        _upd("matching", 3)
        matcher = CatalogMatcher(
            nointro_dir=config.catalogs_nointro_dir,
            redump_dir=config.catalogs_redump_dir,
        )
        unresolved = repository.get_unresolved_games()
        matched = 0
        with repository.batch() as conn:
            for idx, game in enumerate(unresolved, 1):
                _upd("matching", 3, idx, len(unresolved), game.original_filename)
                match_result = matcher.match(game.sha1, game.original_filename)
                if match_result is not None:
                    repository.update_match(
                        game.source_path,
                        canonical_title=match_result.title,
                        match_confidence=match_result.confidence,
                        catalog_source=match_result.catalog_source,
                        connection=conn,
                    )
                    matched += 1

        # ── Step 4: Build plan ───────────────────────────────────────────────
        _upd("planning", 4)
        opts = FormatOptions()
        plan = build_plan(repository, opts)
        inbox_str_lower = str(inbox).lower()
        pending_ops = [
            op for op in plan.pending
            if str(op.source_path).lower().startswith(inbox_str_lower)
        ]
        logger.info("Inbox plan: %d operations", len(pending_ops))

        # ── Step 5: Apply renames ────────────────────────────────────────────
        _upd("renaming", 5, 0, len(pending_ops))
        save_exts = frozenset(config.save_extensions)
        timestamp = utc_now()
        renamed = 0
        rename_errors: list[str] = []
        for idx, op in enumerate(pending_ops, 1):
            _upd("renaming", 5, idx, len(pending_ops), op.source_path.name)
            if not op.source_path.exists():
                continue
            try:
                outcome = rename_rom_with_saves(op.source_path, op.target_path, save_exts)
                if outcome.success:
                    repository.apply_rename(
                        game_id=op.game.id,
                        old_source_path=str(op.source_path),
                        new_source_path=str(op.target_path),
                        new_filename=op.target_path.name,
                        timestamp=timestamp,
                    )
                    renamed += 1
                else:
                    rename_errors.append(f"{op.source_path.name}: {outcome.error}")
            except Exception as exc:
                rename_errors.append(f"{op.source_path.name}: {exc}")

        # ── Step 6: Move to platform folders ─────────────────────────────────
        _upd("organizing", 6, 0, 0)
        organized = 0
        organize_errors: list[str] = []

        # Get fresh game list from inbox area to move
        with repository.connect() as conn:
            rows = conn.execute(
                "SELECT id, source_path, platform, original_filename FROM games "
                "WHERE LOWER(source_path) LIKE ?",
                (inbox_str_lower + "%",),
            ).fetchall()

        for idx, row in enumerate(rows, 1):
            game_id, source_path_str_db, platform, orig_name = row
            source_file = Path(source_path_str_db)
            if not source_file.exists():
                continue

            folder_name = _platform_folder_name(platform or "Unknown")
            dest_folder = target_root / folder_name
            dest_folder.mkdir(parents=True, exist_ok=True)
            dest_file = dest_folder / source_file.name

            _upd("organizing", 6, idx, len(rows), source_file.name)

            # Avoid overwriting
            if dest_file.exists():
                organize_errors.append(f"{source_file.name}: ya existe en destino, omitido")
                continue

            try:
                _shutil.move(str(source_file), str(dest_file))
                # Update DB path
                with repository.batch() as conn:
                    conn.execute(
                        "UPDATE games SET source_path=?, original_filename=? WHERE id=?",
                        (str(dest_file.resolve()), dest_file.name, game_id),
                    )
                organized += 1
            except Exception as exc:
                organize_errors.append(f"{source_file.name}: {exc}")

        # ── Cleanup ───────────────────────────────────────────────────────────
        if delete_source:
            for zp in source_zips:
                try:
                    if zp.exists():
                        zp.unlink()
                except Exception:
                    pass

        # Remove _extracted temp folder if empty
        extracted_dir = inbox / "_extracted"
        if extracted_dir.exists():
            try:
                extracted_dir.rmdir()
            except Exception:
                pass

        _job_results["inbox"] = {
            "result_ts": utc_now(),
            "zips_extracted": extracted_count,
            "roms_scanned": scan_result.roms_detected,
            "matched": matched,
            "renamed": renamed,
            "organized": organized,
            "rename_errors": rename_errors[:20],
            "organize_errors": organize_errors[:20],
            "target_root": str(target_root),
        }

    except Exception as exc:
        logger.exception("Inbox pipeline error: %s", exc)
        _job_results["inbox"] = {"error": str(exc), "result_ts": ""}
    finally:
        with _job_lock:
            _inbox_progress.clear()
            _jobs["inbox"] = False


def _inbox_watcher_loop(get_config_fn: "Callable[[], AppConfig]") -> None:
    """Daemon thread: watch inbox folder and auto-process when files appear."""
    import time as _time
    while True:
        try:
            _time.sleep(30)
            cfg = get_config_fn()
            inbox_path_str = cfg.inbox_path
            if not inbox_path_str or not cfg.inbox_auto_process:
                _inbox_watcher_status.update({"watching": False, "last_check": None, "pending_files": 0})
                continue

            inbox = Path(inbox_path_str).resolve()
            if not inbox.exists():
                _inbox_watcher_status.update({"watching": True, "last_check": _watcher_now(), "pending_files": 0})
                continue

            # Count non-hidden, non-internal files
            pending: list[Path] = []
            for entry in inbox.iterdir():
                if entry.name.startswith(".") or entry.name.startswith("_"):
                    continue
                if entry.is_file():
                    pending.append(entry)

            _inbox_watcher_status.update({
                "watching": True,
                "last_check": _watcher_now(),
                "pending_files": len(pending),
            })

            if pending:
                with _job_lock:
                    already = _jobs.get("inbox", False)
                if not already:
                    _logger.info("Inbox watcher: %d files detected, starting auto-process", len(pending))
                    target_root_str = cfg.inbox_target_root or (str(cfg.library_root) if cfg.library_root else "")
                    # We need repository — use a late-binding approach via a shared mutable
                    # The watcher is started with a get_repo callable
                    pass  # actual launch is done in serve() via _inbox_watcher_loop_with_repo

        except Exception as exc:
            _logger.debug("Inbox watcher error: %s", exc)


def _watcher_now() -> str:
    import datetime as _dt_mod
    return _dt_mod.datetime.now(_dt_mod.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
