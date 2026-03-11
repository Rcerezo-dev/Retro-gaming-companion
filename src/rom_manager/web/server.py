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
}
_job_results: dict[str, dict] = {}
_chd_progress: dict = {}     # {"current": int, "total": int, "current_file": str}
_scrape_progress: dict = {}  # {"current": int, "total": int, "found": int, "current_game": str}
_zip_progress: dict = {}     # {"current": int, "total": int, "current_file": str}
_health_progress: dict = {}  # {"current": int, "total": int, "current_file": str}
_ra_progress: dict = {}      # {"current": int, "total": int, "current_file": str}
_cable_progress: dict = {}   # {"copied": int, "current_file": str}
_scan_progress: dict = {}    # {"files_seen": int, "roms_detected": int, "current_path": str}
_scan_cancel: threading.Event = threading.Event()
_logger = logging.getLogger(__name__)


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


def _build_library_report(
    source_path_str: str,
    repository: LibraryRepository,
    config: AppConfig,
) -> dict:
    """Generate a full library health report for the given source path."""
    source = Path(source_path_str).resolve()

    # ── ZIPs ──────────────────────────────────────────────────────────────────
    from rom_manager.converters.zip_extractor import find_zip_files, _DISC_RE as _ZIP_DISC_RE
    zip_files = find_zip_files(source)
    zip_list = []
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
    groups = find_disc_groups(source)
    playlist_groups = [
        {
            "base_name": g.base_name,
            "disc_count": len(g.discs),
            "discs": [d.name for d in g.discs],
            "m3u_exists": g.m3u_path.exists(),
            "m3u_name": g.m3u_path.name,
        }
        for g in groups
    ]
    multidisc = verify_multidisc(source, repository)
    multidisc_data = {
        "groups_ok": multidisc.groups_ok,
        "groups_with_issues": multidisc.groups_with_issues,
        "issues": [
            {"base_name": i.base_name, "issue_type": i.issue_type, "detail": i.detail}
            for i in multidisc.issues
        ],
    }

    # ── Orphaned saves ────────────────────────────────────────────────────────
    from rom_manager.utils.orphan_finder import find_orphaned_saves
    orphans = find_orphaned_saves(source, config.save_extensions)
    orphan_data = {
        "total": len(orphans),
        "total_bytes": sum(o.size_bytes for o in orphans),
        "saves": [
            {"path": o.save_path, "stem": o.stem, "extension": o.extension, "size_bytes": o.size_bytes}
            for o in orphans
        ],
    }

    return {
        "source_path": str(source),
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


def _build_status(repository: LibraryRepository, source_root: str | None = None) -> dict:
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
    return {
        "total_games": summary.total_games,
        "total_saves": summary.total_saves,
        "total_assets": summary.total_assets,
        "matched_games": matched,
        "unmatched_games": summary.total_games - matched,
        "duplicate_groups": len(dup_groups),
        "wasted_bytes": wasted,
        "last_scan_at": summary.last_scan_at,
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
) -> dict:
    games, total = repository.get_games_paginated(
        offset=offset, limit=limit, platform=platform, status=status,
        source_root=source_root, file_type=file_type, search=search,
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
    pending_rows = []
    total_saves = 0
    for op in pending_ops:
        companions = _count_companion_saves(op.source_path, exts)
        total_saves += companions
        pending_rows.append({
            "platform": op.game.platform,
            "source": str(op.source_path),
            "source_name": op.source_path.name,
            "target": str(op.target_path),
            "target_name": op.target_path.name,
            "companion_saves": companions,
        })
    # Unmatched games (no canonical_title) filtered by source_root
    unmatched_games = repository.get_unresolved_games()
    if source_root:
        root_lower = source_root.lower()
        unmatched_games = [g for g in unmatched_games if g.source_path.lower().startswith(root_lower)]
    unmatched_rows = [
        {"original_filename": g.original_filename, "platform": g.platform}
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
    from rom_manager.database.repository import DuplicateGroup
    groups = repository.get_duplicate_groups()
    if source_root:
        # Single-device mode: only entries under this root
        root_lower = source_root.lower()
        filtered = []
        for g in groups:
            entries = [e for e in g.entries if e.source_path.lower().startswith(root_lower)]
            if len(entries) >= 2:
                filtered.append(DuplicateGroup(sha1=g.sha1, entries=entries))
        groups = filtered
    elif pc_root and ab_root:
        # "Sistema completo" mode: exclude groups where every entry is an
        # intentional cross-device copy (one from PC, rest from Anbernic or
        # vice versa). Real duplicates have ≥2 entries on the SAME device.
        pc_lower = pc_root.lower().rstrip("/\\")
        ab_lower = ab_root.lower().rstrip("/\\")
        filtered = []
        for g in groups:
            pc_entries = [e for e in g.entries if e.source_path.lower().startswith(pc_lower)]
            ab_entries = [e for e in g.entries if e.source_path.lower().startswith(ab_lower)]
            # Keep group only if there are ≥2 entries on at least one device
            if len(pc_entries) >= 2 or len(ab_entries) >= 2:
                filtered.append(g)
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
    return {
        "library_root": str(config.library_root) if config.library_root else None,
        "rclone_remote": config.rclone_remote or None,
        "web_host": config.web_host,
        "web_port": config.web_port,
        "screenscraper_user": config.screenscraper_user or None,
        "screenscraper_pass": config.screenscraper_pass or None,
        "chdman": config.chdman,
        "adb": config.adb,
        "ra_api_key": config.ra_api_key or None,
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


def make_handler(repository: LibraryRepository, config: AppConfig):
    logger = logging.getLogger(__name__)

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
                    self._send_json(_build_status(repository, src_root))
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
                        rpt = _build_library_report(rpt_path, repository, config)
                        rpt["retroachievements"] = _job_results.get("ra_check") or {"note": "Ejecuta primero la comprobación de RetroAchievements en la pestaña Tools"}
                        rpt["chd"] = _job_results.get("convert_chd") or {"note": "Ejecuta primero la conversión CHD en la pestaña Tools"}
                        self._send_json(rpt)
                elif path == "/api/ra-duplicates":
                    self._send_json(_build_ra_duplicates(repository, config))
                elif path == "/api/report/html":
                    rpt_path = qs.get("path", [None])[0] or str(config.library_root or "")
                    if not rpt_path:
                        self._send(400, "text/plain; charset=utf-8",
                                   b"path parameter required (or set library_root in config)")
                    else:
                        from rom_manager.utils.library_report_html import generate_html_report
                        rpt = _build_library_report(rpt_path, repository, config)
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
                    file_type = ft if ft in ("rom", "") else None
                    search = qs.get("search", [None])[0] or None
                    self._send_json(_build_games(repository, offset=offset, limit=limit, platform=plat, status=st, source_root=root, file_type=file_type, search=search))
                elif path == "/api/plan":
                    opts = _parse_format_opts(qs)
                    source_root = qs.get("source_root", [None])[0] or None
                    self._send_json(_build_plan(repository, opts, frozenset(config.save_extensions), source_root=source_root))
                elif path == "/api/duplicates":
                    source_root = qs.get("source_root", [None])[0] or None
                    pc_root     = qs.get("pc_root",     [None])[0] or None
                    ab_root     = qs.get("ab_root",     [None])[0] or None
                    self._send_json(_build_duplicates(repository, source_root=source_root, pc_root=pc_root, ab_root=ab_root))
                elif path == "/api/assets":
                    src_root = qs.get("root", [None])[0] or None
                    self._send_json(_build_assets(repository, src_root))
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
                        from rom_manager.utils.orphan_finder import find_orphaned_saves
                        orphans = find_orphaned_saves(Path(source).resolve(), config.save_extensions)
                        self._send_json({
                            "orphans": [
                                {"save_path": o.save_path, "stem": o.stem,
                                 "extension": o.extension, "size_bytes": o.size_bytes}
                                for o in orphans
                            ],
                            "total": len(orphans),
                        })
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
                elif path == "/api/health-check":
                    self._handle_health_check(data)
                elif path == "/api/cleanup-zips":
                    self._handle_cleanup_zips(data)
                elif path == "/api/cleanup-cue-bin":
                    self._handle_cleanup_cue_bin(data)
                elif path == "/api/stop-job":
                    job_name = data.get("job", "")
                    if job_name == "scan":
                        _scan_cancel.set()
                    with _job_lock:
                        if job_name in _jobs:
                            _jobs[job_name] = False
                    _scan_progress.clear()
                    self._send_json({"status": "stopped", "job": job_name})
                elif path == "/api/ra-check":
                    self._handle_ra_check(data)
                elif path == "/api/cable-sync":
                    self._handle_cable_sync(data)
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
                        r = scan_library(
                            source, config, repository, logger, quick=quick,
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
                except Exception as exc:
                    _job_results["scan"] = {"error": str(exc)}
                finally:
                    _scan_progress.clear()
                    with _job_lock:
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

                    scan_run_id = repository.create_scan_run(android_path, timestamp)
                    roms = saves = assets = errors = 0
                    seen_paths: set[str] = set()

                    # Fetch the file list from the device (~1 round-trip)
                    all_files = transport.ls_recursive(android_path, timeout=180)

                    with repository.batch() as conn:
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
                                    repository.upsert_save(
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
                                    repository.upsert_game(
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

                    pruned = repository.prune_stale_entries(android_path, seen_paths)
                    finished_at = utc_now()
                    repository.complete_scan_run(
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

        def _handle_sync(self, data: dict) -> None:
            dry_run = data.get("dry_run", True)
            with _job_lock:
                if _jobs["sync"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["sync"] = True

            def run() -> None:
                try:
                    from rom_manager.sync.rclone_transport import RcloneTransport, RcloneError
                    from rom_manager.sync.save_syncer import sync_saves
                    saves_dir = config.library_root
                    if saves_dir is None:
                        _job_results["sync"] = {"error": "library_root not configured"}
                        return
                    remote = config.rclone_remote
                    if not remote:
                        _job_results["sync"] = {"error": "rclone remote not configured"}
                        return
                    transport = RcloneTransport(rclone=config.rclone_binary)
                    result, decisions = sync_saves(
                        saves_dir,
                        remote,
                        transport=transport,
                        repository=repository,
                        save_extensions=config.save_extensions,
                        dry_run=dry_run,
                    )
                    _job_results["sync"] = {
                        "dry_run": dry_run,
                        "uploaded": result.uploaded,
                        "downloaded": result.downloaded,
                        "up_to_date": result.up_to_date,
                        "conflicts": result.conflicts,
                        "errors": result.errors,
                        "decisions": [
                            {"action": d.action, "relative": d.relative}
                            for d in decisions if d.action != "up_to_date"
                        ],
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
                    _chd_progress.clear()
                    with _job_lock:
                        _jobs["convert_chd"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started", "dry_run": dry_run})

        def _handle_save_config(self, data: dict) -> None:
            from rom_manager.config import write_config_toml, load_config
            allowed = {
                "library.library_root", "sync.remote",
                "screenscraper.user", "screenscraper.pass",
                "tools.chdman", "tools.adb",
                "retroachievements.api_key",
            }
            updates = {k: v for k, v in data.items() if k in allowed}
            if not updates:
                self._send_json({"error": "No recognised fields to update"})
                return
            write_config_toml(config.project_root, updates)
            # Reload in-memory config so changes take effect without restart
            new_cfg = load_config(config.project_root)
            config.library_root = new_cfg.library_root
            config.rclone_remote = new_cfg.rclone_remote
            config.screenscraper_user = new_cfg.screenscraper_user
            config.screenscraper_pass = new_cfg.screenscraper_pass
            config.chdman = new_cfg.chdman
            config.adb = new_cfg.adb
            config.ra_api_key = new_cfg.ra_api_key
            self._send_json({"saved": list(updates.keys())})

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
                try:
                    from rom_manager.converters.zip_extractor import find_zip_files, extract_zip
                    source = Path(source_path_str).resolve()
                    zip_files = find_zip_files(source)
                    total = len(zip_files)
                    _zip_progress.update({"current": 0, "total": total, "current_file": ""})
                    extracted = skipped = failed = disc_sets = 0
                    results = []
                    for idx, zp in enumerate(zip_files, 1):
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
                        "results": results,
                    }
                except Exception as exc:
                    _job_results["extract_zip"] = {"error": str(exc)}
                finally:
                    _zip_progress.clear()
                    with _job_lock:
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
                    {"base_name": i.base_name, "issue_type": i.issue_type, "detail": i.detail}
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

        def _handle_health_check(self, data: dict) -> None:
            with _job_lock:
                if _jobs["health_check"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["health_check"] = True

            def run() -> None:
                try:
                    from rom_manager.utils.health_checker import check_library_health

                    def progress_cb(current: int, total: int, filename: str) -> None:
                        _health_progress.update({"current": current, "total": total, "current_file": filename})

                    summary = check_library_health(repository, progress_cb=progress_cb)
                    _job_results["health_check"] = {
                        "ok": summary.ok,
                        "corrupted": summary.corrupted,
                        "missing": summary.missing,
                        "issues": [
                            {"source_path": r.source_path, "status": r.status,
                             "stored_sha1": r.stored_sha1[:12], "computed_sha1": r.computed_sha1[:12] if r.computed_sha1 else ""}
                            for r in summary.results
                        ],
                    }
                except Exception as exc:
                    _job_results["health_check"] = {"error": str(exc)}
                finally:
                    _health_progress.clear()
                    with _job_lock:
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
                    }
                except Exception as exc:
                    _job_results["scrape"] = {"error": str(exc)}
                finally:
                    _scrape_progress.clear()
                    with _job_lock:
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
            game_id = data.get("game_id")
            source_path = data.get("source_path", "").strip()
            if not game_id or not source_path:
                self._send_json({"error": "game_id and source_path are required"})
                return
            try:
                os.remove(source_path)
            except OSError as exc:
                self._send_json({"error": f"Could not delete file: {exc}"})
                return
            repository.delete_game(int(game_id))
            self._send_json({"deleted": source_path})

        def _handle_delete_all_duplicates(self) -> None:
            import os
            groups = repository.get_duplicate_groups()
            deleted = 0
            failed = 0
            freed_bytes = 0
            for group in groups:
                # Keep first entry (index 0), delete the rest
                for entry in group.entries[1:]:
                    try:
                        os.remove(entry.source_path)
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
                try:
                    from rom_manager.retroachievements.ra_checker import check_library, to_csv

                    cache_dir = config.data_dir / "ra_cache"

                    def progress_cb(current: int, total: int, filename: str) -> None:
                        _ra_progress.update({"current": current, "total": total, "current_file": filename})

                    summary = check_library(
                        repository,
                        api_key,
                        cache_dir=cache_dir,
                        progress_cb=progress_cb,
                    )

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
                    }
                except Exception as exc:
                    _job_results["ra_check"] = {"error": str(exc)}
                finally:
                    _ra_progress.clear()
                    with _job_lock:
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
                try:
                    from pathlib import PurePosixPath
                    pc_root   = Path(pc_path_str)
                    save_exts = frozenset(config.save_extensions)

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

                    copied = skipped = errors = sha1_skipped = 0
                    copied_bytes = 0
                    details: list[dict] = []

                    def _copy(src: Path, dst: Path, arrow: str) -> None:
                        nonlocal copied, skipped, errors, copied_bytes
                        try:
                            src_stat = src.stat()
                            size = src_stat.st_size
                            # Skip if destination already exists with same size
                            if skip_existing and dst.exists():
                                try:
                                    if dst.stat().st_size == size:
                                        skipped += 1
                                        if len(details) < 300:
                                            details.append({"file": "EXISTS", "path": str(src.name)})
                                        return
                                except OSError:
                                    pass
                            if not dry_run:
                                dst.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(src, dst)
                            copied += 1
                            copied_bytes += size
                            if len(details) < 300:
                                details.append({"file": arrow, "path": str(src.name)})
                            _cable_progress.update({"copied": copied, "current_file": src.name})
                        except OSError as exc:
                            errors += 1
                            if len(details) < 300:
                                details.append({"file": f"ERROR: {exc}", "path": str(src.name)})

                    # ── ADB mode ──────────────────────────────────────────────
                    if use_adb:
                        from rom_manager.sync.adb_transport import AdbTransport
                        transport = AdbTransport(config.adb, adb_serial)

                        def _adb_copy_to_pc(adb_info, rel_posix: str, arrow: str) -> None:
                            nonlocal copied, errors, copied_bytes
                            name = PurePosixPath(adb_info.android_path).name
                            local_dst = pc_root / Path(rel_posix.replace("/", os.sep))
                            try:
                                size = transport.pull(adb_info.android_path, local_dst, dry_run=dry_run)
                                copied += 1
                                copied_bytes += size
                                if len(details) < 300:
                                    details.append({"file": arrow, "path": name})
                                _cable_progress.update({"copied": copied, "current_file": name})
                            except OSError as exc:
                                errors += 1
                                if len(details) < 300:
                                    details.append({"file": f"ERROR: {exc}", "path": name})

                        def _adb_copy_to_device(local_src: Path, rel_posix: str, arrow: str) -> None:
                            nonlocal copied, errors, copied_bytes
                            android_dst = android_path.rstrip("/") + "/" + rel_posix
                            try:
                                size = transport.push(local_src, android_dst, dry_run=dry_run)
                                copied += 1
                                copied_bytes += size
                                if len(details) < 300:
                                    details.append({"file": arrow, "path": local_src.name})
                                _cable_progress.update({"copied": copied, "current_file": local_src.name})
                            except OSError as exc:
                                errors += 1
                                if len(details) < 300:
                                    details.append({"file": f"ERROR: {exc}", "path": local_src.name})

                        _cable_progress.update({"copied": 0, "current_file": "Listando archivos en el dispositivo…"})
                        ab_adb_files = transport.ls_recursive(android_path)
                        android_prefix = android_path.rstrip("/") + "/"

                        if direction == "pc_to_anbernic":
                            for src in _iter_files(pc_root):
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
                                name = PurePosixPath(info.android_path).name
                                if not _wanted_name(name):
                                    continue
                                rel_posix = info.android_path.removeprefix(android_prefix)
                                if use_sha1 and _cat_name(name) == "rom":
                                    local_tmp = pc_root / Path(rel_posix.replace("/", os.sep))
                                    _cable_progress.update({"copied": copied, "current_file": f"[SHA1] {name}"})
                                    # For SHA1 check we need the file locally; pull to temp first
                                    import tempfile
                                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(name).suffix) as tf:
                                        tmp_path = Path(tf.name)
                                    try:
                                        transport.pull(info.android_path, tmp_path, dry_run=False)
                                        from rom_manager.hashing.hash_calculator import calculate_hashes
                                        h = calculate_hashes(tmp_path)
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
                                        _cable_progress.update({"copied": copied, "current_file": name})
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

                        if direction == "pc_to_anbernic":
                            for src in _iter_files(pc_root):
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
                                if not _wanted(src):
                                    continue
                                try:
                                    rel = src.relative_to(ab_root)
                                except ValueError:
                                    continue
                                if use_sha1 and _category(src) == "rom":
                                    _cable_progress.update({"copied": copied, "current_file": f"[SHA1] {src.name}"})
                                    try:
                                        h = calculate_hashes(src)
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

                    _job_results["cable_sync"] = {
                        "dry_run": dry_run,
                        "direction": direction,
                        "use_adb": use_adb,
                        "copied": copied,
                        "skipped": skipped,
                        "sha1_skipped": sha1_skipped,
                        "errors": errors,
                        "copied_bytes": copied_bytes,
                        "details": details,
                    }
                except Exception as exc:
                    _job_results["cable_sync"] = {"error": str(exc)}
                finally:
                    _cable_progress.clear()
                    with _job_lock:
                        _jobs["cable_sync"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started", "dry_run": dry_run})

        def _handle_apply(self, data: dict) -> None:
            from rom_manager.renamer.file_renamer import rename_rom_with_saves
            from rom_manager.scanner.rom_scanner import utc_now

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

            save_exts = frozenset(config.save_extensions)
            plan = build_plan(repository, opts, keep_both=keep_both)
            pending_ops = plan.pending
            if source_root:
                root_lower = source_root.lower()
                pending_ops = [op for op in pending_ops if str(op.source_path).lower().startswith(root_lower)]
            renamed = failed = skipped = saves_renamed = 0
            skip_details: list[str] = []
            timestamp = utc_now()
            for op in pending_ops:
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
                    repository.apply_rename(
                        game_id=op.game.id,
                        old_source_path=str(op.source_path),
                        new_source_path=str(op.target_path),
                        new_filename=op.target_path.name,
                        timestamp=timestamp,
                    )
                    renamed += 1
                    saves_renamed += outcome.saves_renamed
                else:
                    # Check if it's an unexpected-file / permission issue vs a hard error
                    err_lower = outcome.error.lower()
                    if "not found" in err_lower or "no such file" in err_lower:
                        skipped += 1
                        skip_details.append(f"{op.source_path.name}: {outcome.error}")
                    else:
                        failed += 1
                        skip_details.append(f"{op.source_path.name}: {outcome.error}")

            self._send_json({
                "renamed": renamed,
                "failed": failed,
                "skipped": skipped,
                "saves_renamed": saves_renamed,
                "conflicts": len(plan.conflicts),
                "skip_details": skip_details[:20],
            })

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
) -> None:
    handler = make_handler(repository, config)
    with ThreadingHTTPServer((host, port), handler) as httpd:
        httpd.serve_forever()
