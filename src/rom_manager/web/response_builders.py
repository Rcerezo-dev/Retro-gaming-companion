"""Response-builder functions for the Retro Vault web server.

All functions here are pure — they take typed parameters and return dicts
ready to be JSON-serialised. They do NOT access any global job state.

Extracted from server.py (Session 18) to reduce the monolith size.
"""
from __future__ import annotations

import json
from pathlib import Path

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository
from rom_manager.planner import build_plan
from rom_manager.planner.operation_planner import FormatOptions


# ---------------------------------------------------------------------------
# HTTP / path utilities
# ---------------------------------------------------------------------------

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
                    label_buf   = ctypes.create_unicode_buffer(261)
                    fs_buf      = ctypes.create_unicode_buffer(261)
                    ctypes.windll.kernel32.GetVolumeInformationW(  # type: ignore[attr-defined]
                        f"{letter}:\\", label_buf, 261,
                        None, None, None, fs_buf, 261,
                    )
                    label = label_buf.value or ""
                    usage = ctypes.c_ulonglong(0)
                    free_c = ctypes.c_ulonglong(0)
                    total_c = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(  # type: ignore[attr-defined]
                        f"{letter}:\\",
                        ctypes.byref(usage),
                        ctypes.byref(total_c),
                        ctypes.byref(free_c),
                    )
                    drives.append({
                        "letter": f"{letter}:\\",
                        "label": label,
                        "total_bytes": total_c.value,
                        "free_bytes": free_c.value,
                    })
                except OSError:
                    drives.append({"letter": f"{letter}:\\", "label": "", "total_bytes": 0, "free_bytes": 0})
    else:
        try:
            for line in Path("/proc/mounts").read_text().splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[1].startswith("/media"):
                    drives.append({"letter": parts[1], "label": parts[1].split("/")[-1], "total_bytes": 0, "free_bytes": 0})
        except OSError:
            pass
    return {"drives": drives}


def _utc_now_str() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _parse_format_opts(qs: dict) -> FormatOptions:
    return FormatOptions(
        include_region=qs.get("include_region", ["1"])[0] != "0",
        include_revision=qs.get("include_revision", ["1"])[0] != "0",
        include_platform=qs.get("include_platform", ["0"])[0] != "0",
        include_sha=qs.get("include_sha", ["0"])[0] != "0",
        sha_length=min(40, max(4, int(qs.get("sha_length", ["8"])[0]))),
    )


def _repo_for_path(
    path_str: str,
    repository: LibraryRepository,
    repository_android: LibraryRepository,
    config: AppConfig,
) -> LibraryRepository:
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

    def _norm_lower(p: str) -> str:
        return p.replace("/", _os.sep).replace("\\", _os.sep).lower().rstrip(_os.sep)

    lib_root_norm = _norm_lower(lib_root_raw)
    path_norm = _norm_lower(path_str)
    if path_norm.startswith(lib_root_norm):
        return repository
    return repository_android


# ---------------------------------------------------------------------------
# Response builders — library / games
# ---------------------------------------------------------------------------

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
    # If source_root is an Android-style path (starts with /) and we have an Android
    # repository, query it instead of the PC repository so ADB-scanned stats show up.
    _is_android_root = bool(source_root and source_root.startswith("/") and repository_android is not None and repository_android is not repository)
    active_repo = repository_android if _is_android_root else repository
    summary = active_repo.get_summary(source_root)
    dup_groups = repository.get_duplicate_groups()
    from rom_manager.reports.reporter import _get_all_games
    games = _get_all_games(active_repo)
    if source_root:
        prefix = source_root.rstrip("/\\")
        matched = sum(1 for g in games if g.canonical_title is not None and g.source_path.startswith(prefix))
    else:
        matched = sum(1 for g in games if g.canonical_title is not None)
    wasted = sum(g.wasted_bytes for g in dup_groups)
    last_scans = active_repo.get_last_scan_by_root()
    # Android DB counts (separate DB)
    android_summary = None
    if repository_android is not None and repository_android is not repository:
        try:
            android_summary = repository_android.get_summary()
        except Exception:
            pass

    # compute per-root scan staleness
    scan_days_ago: int | None = None
    stale = False
    if source_root:
        root_norm = source_root.lower()
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

    # check for cached report
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

    # first_run / setup_complete / setup_checklist
    scan_count = 0
    matched_count = 0
    try:
        with repository.connect() as _sc:
            scan_count = _sc.execute("SELECT COUNT(*) FROM scan_runs").fetchone()[0]
            _m = _sc.execute("SELECT COUNT(*) FROM games WHERE canonical_title IS NOT NULL").fetchone()
            matched_count = _m[0] if _m else 0
    except Exception:
        pass

    first_run = not bool(library_root)
    setup_complete = scan_count > 0 and matched_count > 0

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

    return {
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
        "android_total_games": android_summary.total_games if android_summary else None,
        "android_total_saves": android_summary.total_saves if android_summary else None,
        "android_last_scan_at": android_summary.last_scan_at if android_summary else None,
        "pc_db": "library_pc.db",
        "android_db": "library_android.db",
        "first_run": first_run,
        "setup_complete": setup_complete,
        "setup_checklist": setup_checklist,
        "recently_played": recently_played,
    }


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
    favorite: bool = False,
    tag: str | None = None,
    genre: str | None = None,
    year: str | None = None,
    region: str | None = None,
    sort_by: str | None = None,
) -> dict:
    games, total = repository.get_games_paginated(
        offset=offset, limit=limit, platform=platform, status=status,
        source_root=source_root, file_type=file_type, search=search,
        play_status=play_status, favorite=favorite, tag=tag,
        genre=genre, year=year, region=region, sort_by=sort_by,
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
    _lib_root_lower = library_root.lower() if library_root else None

    pending_rows = []
    total_saves = 0
    for op in pending_ops:
        companions = _count_companion_saves(op.source_path, exts)
        total_saves += companions
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
    unmatched_games = repository.get_unresolved_games()
    if source_root:
        root_lower = source_root.lower()
        unmatched_games = [g for g in unmatched_games if g.source_path.lower().startswith(root_lower)]

    with repository.connect() as _conn:
        _matched_plats = {
            row[0] for row in _conn.execute(
                "SELECT DISTINCT platform FROM games WHERE match_confidence IS NOT NULL AND platform IS NOT NULL"
            ).fetchall()
        }

    def _unmatched_reason(g) -> str:
        if not g.sha1:
            return "no_sha1"
        if g.platform and g.platform not in _matched_plats:
            return "no_dat"
        return "hash_not_found"

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
                "reason": op.conflict_reason,
            }
            for op in conflict_ops
        ],
        "total_saves_affected": total_saves,
        "unmatched_count": len(unmatched_rows),
        "unmatched": unmatched_rows,
    }


def _annotate_duplicates_with_ra(title_groups: list[dict], config: "AppConfig") -> list[dict]:
    """B1-4: Annotate title_groups entries with RA achievements count if available."""
    from collections import defaultdict
    import json as _json
    from pathlib import Path as _Path
    from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id
    from rom_manager.retroachievements.ra_client import _parse_game_list

    cache_dir = config.project_root / ".rommgr" / "ra_cache"

    # Build platform → {md5 → achievements} map
    platform_hash_map: dict[str, dict[str, int]] = {}
    for group in title_groups:
        plat = group.get("platform") or "unknown"
        if plat in platform_hash_map:
            continue
        console_id = get_ra_console_id(plat)
        if not console_id:
            continue
        cache_file = cache_dir / f"ra_hashes_{console_id}.json"
        if not cache_file.exists():
            continue
        try:
            data = _json.loads(cache_file.read_text(encoding="utf-8"))
            hash_lib = _parse_game_list(data)
            platform_hash_map[plat] = {md5: game.achievements for md5, game in hash_lib.items()}
        except Exception:
            continue

    # Get MD5 mapping: id → md5 from database
    id_to_md5: dict[int, str] = {}
    try:
        from rom_manager.database.repository import LibraryRepository
        repo = LibraryRepository(config.project_root)
        with repo.connect() as conn:
            rows = conn.execute("SELECT id, md5 FROM games").fetchall()
            id_to_md5 = {r["id"]: r["md5"] for r in rows}
    except Exception:
        pass

    # Annotate each entry
    result = []
    for group in title_groups:
        plat = group.get("platform")
        hash_map = platform_hash_map.get(plat, {})
        annotated_entries = []
        for entry in group.get("entries", []):
            md5 = id_to_md5.get(entry["id"], "")
            md5_lower = (md5 or "").lower()
            achievements = hash_map.get(md5_lower, 0)
            annotated_entry = {**entry, "ra_achievements": achievements}
            annotated_entries.append(annotated_entry)
        result.append({**group, "entries": annotated_entries})

    return result


def _build_duplicates(
    repository: LibraryRepository,
    source_root: str | None = None,
    pc_root: str | None = None,
    ab_root: str | None = None,
) -> dict:
    import os as _os
    from rom_manager.database.repository import DuplicateGroup

    def _norm(p: str) -> str:
        return _os.path.normcase(_os.path.normpath(p)).rstrip(_os.sep) + _os.sep

    groups = repository.get_duplicate_groups()
    if source_root:
        root_norm = _norm(source_root)
        filtered = []
        for g in groups:
            entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(root_norm)]
            if len(entries) >= 2:
                filtered.append(DuplicateGroup(sha1=g.sha1, entries=entries))
        groups = filtered
    elif pc_root and ab_root:
        pc_norm = _norm(pc_root)
        ab_norm = _norm(ab_root)
        filtered = []
        for g in groups:
            pc_entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(pc_norm)]
            ab_entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(ab_norm)]
            if len(pc_entries) >= 2 or len(ab_entries) >= 2:
                filtered.append(g)
        groups = filtered
    elif pc_root:
        pc_norm = _norm(pc_root)
        filtered = []
        for g in groups:
            entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(pc_norm)]
            if len(entries) >= 2:
                filtered.append(DuplicateGroup(sha1=g.sha1, entries=entries))
        groups = filtered
    groups = sorted(groups, key=lambda g: g.wasted_bytes, reverse=True)
    total_files = sum(len(g.entries) for g in groups)
    total_wasted = sum(g.wasted_bytes for g in groups)

    # Semantic duplicates: same canonical_title+platform but different SHA1
    title_groups = repository.get_title_duplicate_groups()

    # Annotate title_groups with RA achievements if available
    title_groups = _annotate_duplicates_with_ra(title_groups, config)

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
        "title_groups": title_groups,
    }


def _build_library_diff(
    repository: LibraryRepository,
    repository_android: LibraryRepository,
    config: AppConfig,
) -> dict:
    """Compare PC vs Android libraries by SHA1 and return three-way diff."""
    def _fetch_roms(repo: LibraryRepository) -> dict[str, dict]:
        result: dict[str, dict] = {}
        with repo.connect() as conn:
            rows = conn.execute(
                "SELECT sha1, platform, canonical_title, original_filename, source_path "
                "FROM games WHERE file_type = 'rom' AND sha1 IS NOT NULL AND sha1 != ''"
            ).fetchall()
        for row in rows:
            sha1, platform, title, fname, spath = row
            result[sha1] = {
                "platform": platform or "",
                "title": title or fname or "",
                "source_path": spath or "",
            }
        return result

    pc_roms  = _fetch_roms(repository)
    and_roms = _fetch_roms(repository_android)
    pc_sha1s  = set(pc_roms)
    and_sha1s = set(and_roms)

    only_pc  = sorted(
        [{"sha1": s, **pc_roms[s], "location": "pc"}  for s in pc_sha1s - and_sha1s],
        key=lambda x: (x["platform"], x["title"]),
    )
    only_and = sorted(
        [{"sha1": s, **and_roms[s], "location": "android"} for s in and_sha1s - pc_sha1s],
        key=lambda x: (x["platform"], x["title"]),
    )
    in_both  = sorted(
        [{"sha1": s, **pc_roms[s], "location": "both"}  for s in pc_sha1s & and_sha1s],
        key=lambda x: (x["platform"], x["title"]),
    )

    return {
        "only_pc":      only_pc,
        "only_android": only_and,
        "in_both":      in_both,
        "total_pc":     len(pc_roms),
        "total_android": len(and_roms),
        "parity": len(only_pc) == 0 and len(only_and) == 0,
    }


def _build_duplicates_two_repos(
    repository: LibraryRepository,
    repository_android: LibraryRepository,
    source_root: str | None = None,
    pc_root: str | None = None,
    ab_root: str | None = None,
) -> dict:
    """Two-DB version of duplicate detection."""
    import os as _os
    from rom_manager.database.repository import DuplicateGroup, DuplicateEntry

    def _norm(p: str) -> str:
        return _os.path.normcase(_os.path.normpath(p)).rstrip(_os.sep) + _os.sep

    if repository_android is repository:
        return _build_duplicates(repository, source_root=source_root, pc_root=pc_root, ab_root=ab_root)

    pc_groups = repository.get_duplicate_groups()
    android_groups = repository_android.get_duplicate_groups()

    if source_root:
        root_norm = _norm(source_root)
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
        all_groups = sorted(filtered_pc + filtered_android, key=lambda g: g.wasted_bytes, reverse=True)
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

    pc_sha1_map: dict[str, list[DuplicateEntry]] = {g.sha1: g.entries for g in pc_groups}
    android_sha1_map: dict[str, list[DuplicateEntry]] = {g.sha1: g.entries for g in android_groups}
    combined: list[DuplicateGroup] = []

    if pc_root:
        pc_norm = _norm(pc_root)
        for g in pc_groups:
            entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(pc_norm)]
            if len(entries) >= 2:
                combined.append(DuplicateGroup(sha1=g.sha1, entries=entries))
    else:
        combined.extend(pc_groups)

    if ab_root:
        ab_norm = _norm(ab_root)
        for g in android_groups:
            entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(ab_norm)]
            if len(entries) >= 2:
                combined.append(DuplicateGroup(sha1=g.sha1, entries=entries))
    else:
        combined.extend(android_groups)

    for sha1 in set(pc_sha1_map) & set(android_sha1_map):
        combined.append(DuplicateGroup(sha1=sha1, entries=pc_sha1_map[sha1] + android_sha1_map[sha1]))

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
    bin_files: set[str] = set()

    for f in p.rglob("*"):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        ext_counter[ext] += 1
        if ext == ".cue":
            cue_files.append(f)
        elif ext == ".bin":
            bin_files.add(f.stem.lower())

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

    cue_stems = {c.stem.lower() for c in cue_files}
    bin_orphan = [
        f.name for f in p.rglob("*.bin")
        if f.is_file() and f.stem.lower() not in cue_stems
    ]
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
    """B1-4: Find title-based duplicates where one version has RA support and another doesn't.

    Conserva automáticamente la versión con logros activos en RetroAchievements.
    Las versiones sin logros se marcan como candidatas a eliminar.
    """
    from collections import defaultdict
    import json as _json
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
            data = _json.loads(cache_file.read_text(encoding="utf-8"))
            hash_lib = _parse_game_list(data)
            platform_hash_map[plat] = {md5: game.achievements for md5, game in hash_lib.items()}
        except Exception:
            continue

    if not platform_hash_map:
        return {"groups": [], "total_groups": 0, "wasted_bytes": 0,
                "note": "No hay caché de RetroAchievements. Ejecuta primero la comprobación RA en Tools."}

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
            achievements = hash_map.get(md5_lower, -1)
            annotated.append({**e, "ra_achievements": achievements, "ra_supported": achievements > 0})

        has_supported = any(a["ra_supported"] for a in annotated)
        has_unsupported = any(not a["ra_supported"] for a in annotated)
        if not (has_supported and has_unsupported):
            continue

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
    from rom_manager.config import validate as _validate_config

    def _db_size(p: Path) -> int | None:
        try:
            return p.stat().st_size if p.exists() else 0
        except OSError:
            return None

    return {
        "warnings": _validate_config(config),
        "library_root": str(config.library_root) if config.library_root else None,
        "anbernic_root": config.anbernic_root or "",
        "device_name": config.device_name or "Consola Android",
        "rclone_remote": config.rclone_remote or None,
        "web_host": config.web_host,
        "web_port": config.web_port,
        "screenscraper_user": config.screenscraper_user or None,
        "screenscraper_pass": config.screenscraper_pass or None,
        "screenscraper_dev_id": config.screenscraper_dev_id or None,
        "screenscraper_dev_pass": config.screenscraper_dev_pass or None,
        "chdman": config.chdman,
        "adb": config.adb,
        "ra_api_key": config.ra_api_key or None,
        "pc_db_path": str(config.database_path),
        "pc_db_size": _db_size(config.database_path),
        "android_db_path": str(config.database_path_android),
        "android_db_size": _db_size(config.database_path_android),
        "inbox_path": config.inbox_path or "",
        "inbox_target_root": config.inbox_target_root or "",
        "inbox_auto_process": config.inbox_auto_process,
        "inbox_delete_source": config.inbox_delete_source,
        "sync_sources": [
            {"name": s.name, "local_dir": s.local_dir, "remote": s.remote, "sync_all": s.sync_all}
            for s in config.sync_sources
        ],
        "retroarch_path": config.retroarch_path or "",
        "launcher_cores": config.launcher_cores or {},
        "backup_saves_enabled": config.backup_saves_enabled,
        "backup_saves_keep_n": config.backup_saves_keep_n,
    }


def _build_scrape_summary(repository: LibraryRepository) -> dict:
    return {"platforms": repository.get_scraped_platform_summary()}


def _build_cable_sync_preview(qs: dict, config: AppConfig) -> dict:
    """Count saves on PC and Android side for a quick pre-sync summary."""
    import os as _os

    mode       = qs.get("mode",      ["sd"])[0]
    direction  = qs.get("direction", ["pc_to_anbernic"])[0]
    pc_path_s  = (qs.get("pc_path",  [None])[0] or "").strip() or str(config.library_root or "")
    ab_path_s  = (qs.get("ab_path",  [None])[0] or "").strip()

    save_exts: frozenset[str] = frozenset(config.save_extensions)

    def _count_saves(root: Path) -> int:
        count = 0
        try:
            for dirpath, dirs, files in _os.walk(root):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for fname in files:
                    if Path(fname).suffix.lower() in save_exts:
                        count += 1
        except OSError:
            pass
        return count

    pc_saves: int | None = None
    if pc_path_s:
        pc_root = Path(pc_path_s)
        if pc_root.is_dir():
            pc_saves = _count_saves(pc_root)

    android_saves: int | None = None
    android_message: str | None = None

    if mode == "adb":
        android_message = "no accesible en modo ADB (conecta y detecta el dispositivo)"
    elif ab_path_s:
        ab_root = Path(ab_path_s)
        if ab_root.is_dir():
            android_saves = _count_saves(ab_root)
        else:
            android_message = f"ruta no encontrada: {ab_path_s}"
    else:
        android_message = "introduce la ruta de la tarjeta SD / consola Android"

    to_copy: int | None = None
    if direction in ("pc_to_anbernic",) and pc_saves is not None and android_saves is not None:
        to_copy = max(0, pc_saves - android_saves)
    elif direction == "anbernic_to_pc" and pc_saves is not None and android_saves is not None:
        to_copy = max(0, android_saves - pc_saves)
    elif direction == "newest" and pc_saves is not None and android_saves is not None:
        to_copy = abs(pc_saves - android_saves)

    return {
        "pc_saves":       pc_saves,
        "android_saves":  android_saves,
        "android_message": android_message,
        "to_copy":        to_copy,
        "mode":           mode,
        "direction":      direction,
    }
