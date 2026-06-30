"""Library / games response builders: report, status, games list, plan.

Pure functions: typed params → JSON-ready dicts. No global job state.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository
from rom_manager.planner import build_plan
from rom_manager.planner.operation_planner import FormatOptions

_logger = logging.getLogger(__name__)


def _build_library_report(
    source_path_str: str,
    repository: LibraryRepository,
    config: AppConfig,
) -> dict:
    """Generate a full library health report for the given source path."""
    source = Path(source_path_str).resolve()
    path_accessible = source.exists() and source.is_dir()

    # ── ZIPs ──────────────────────────────────────────────────────────────────
    from rom_manager.converters.zip_extractor import _DISC_RE as _ZIP_DISC_RE
    from rom_manager.converters.zip_extractor import find_zip_files

    zip_list = []
    zip_files: list[Path] = []
    if path_accessible:
        try:
            zip_files = find_zip_files(source)
        except Exception:
            _logger.warning("find_zip_files falló en %s", source, exc_info=True)
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
            zip_list.append(
                {"path": rel, "name": zp.name, "size_bytes": size, "is_disc_set": is_disc}
            )

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
            _logger.warning("find_disc_groups falló en %s", source, exc_info=True)
        try:
            multidisc = verify_multidisc(source, repository)
            multidisc_data = {
                "groups_ok": multidisc.groups_ok,
                "groups_with_issues": multidisc.groups_with_issues,
                "issues": [
                    {
                        "base_name": i.base_name,
                        "issue_type": i.issue_type,
                        "detail": i.detail,
                        "platform": i.platform,
                    }
                    for i in multidisc.issues
                ],
            }
        except Exception:
            _logger.warning("verify_multidisc falló en %s", source, exc_info=True)

    # ── Orphaned saves ────────────────────────────────────────────────────────
    from rom_manager.utils.orphan_finder import find_orphaned_saves

    orphans = []
    if path_accessible:
        try:
            orphans = find_orphaned_saves(source, config.save_extensions)
        except Exception:
            _logger.warning("find_orphaned_saves falló en %s", source, exc_info=True)
    orphan_data = {
        "total": len(orphans),
        "total_bytes": sum(o.size_bytes for o in orphans),
        "saves": [
            {
                "path": o.save_path,
                "stem": o.stem,
                "extension": o.extension,
                "size_bytes": o.size_bytes,
            }
            for o in orphans
        ],
    }

    return {
        "source_path": str(source),
        "path_accessible": path_accessible,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
    _dt_cls = datetime
    # If source_root is an Android-style path (starts with /) and we have an Android
    # repository, query it instead of the PC repository so ADB-scanned stats show up.
    _is_android_root = bool(
        source_root
        and source_root.startswith("/")
        and repository_android is not None
        and repository_android is not repository
    )
    active_repo = repository_android if _is_android_root else repository
    summary = active_repo.get_summary(source_root)
    dup_groups = repository.get_duplicate_groups()
    from rom_manager.reports.reporter import _get_all_games

    games = _get_all_games(active_repo)
    if source_root:
        prefix = source_root.rstrip("/\\")
        matched = sum(
            1 for g in games if g.canonical_title is not None and g.source_path.startswith(prefix)
        )
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
            _logger.debug("get_summary (Android) falló", exc_info=True)

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
                _logger.debug(
                    "No se pudo parsear la fecha del último scan (%r)", best_at, exc_info=True
                )
                stale = True

    # check for cached report
    last_report_at: str | None = None
    last_report_mins_ago: int | None = None
    if project_root is not None:
        try:
            _rpt_cache = project_root / ".rommgr" / "last_report.json"
            if _rpt_cache.exists():
                _mtime = _rpt_cache.stat().st_mtime
                _now_ts = _dt_cls.now(UTC).timestamp()
                _mins = int((_now_ts - _mtime) / 60)
                last_report_at = _dt_cls.fromtimestamp(_mtime, tz=UTC).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                last_report_mins_ago = _mins
        except Exception:
            _logger.debug("No se pudo leer la caché de last_report.json", exc_info=True)

    # first_run / setup_complete / setup_checklist
    scan_count = 0
    matched_count = 0
    try:
        with repository.connect() as _sc:
            scan_count = _sc.execute("SELECT COUNT(*) FROM scan_runs").fetchone()[0]
            _m = _sc.execute(
                "SELECT COUNT(*) FROM games WHERE canonical_title IS NOT NULL"
            ).fetchone()
            matched_count = _m[0] if _m else 0
    except Exception:
        _logger.warning("Consulta de scan_count/matched_count falló", exc_info=True)

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
                    1 for f in _dat_dir.iterdir() if f.suffix.lower() in {".dat", ".xml"}
                )
            except Exception:
                _logger.debug(
                    "No se pudo listar el directorio de catálogos %s", _dat_dir, exc_info=True
                )

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
        _logger.warning("Consulta de recently_played falló", exc_info=True)

    # UI-2: total_platforms
    total_platforms = 0
    try:
        with active_repo.connect() as _pp:
            _row = _pp.execute(
                "SELECT COUNT(DISTINCT platform) FROM games WHERE file_type='rom' AND platform IS NOT NULL AND platform != ''"
            ).fetchone()
            total_platforms = _row[0] if _row else 0
    except Exception:
        _logger.warning("Consulta de total_platforms falló", exc_info=True)

    # UI-2: last_sync_at (most recent save_sync_log entry)
    last_sync_at: str | None = None
    try:
        _sl = active_repo.get_sync_log(limit=1)
        if _sl:
            last_sync_at = _sl[0].get("created_at")
    except Exception:
        _logger.debug("No se pudo leer el último sync_log", exc_info=True)

    # Bloque 7: extra KPIs (size, play status counts)
    total_size_bytes = 0
    status_counts: dict[str, int] = {}
    try:
        with active_repo.connect() as _kc:
            _sz = _kc.execute("SELECT COALESCE(SUM(size_bytes),0) FROM games WHERE file_type='rom'").fetchone()
            total_size_bytes = int(_sz[0]) if _sz else 0
            for _row in _kc.execute(
                "SELECT COALESCE(play_status,'none') AS s, COUNT(*) AS n FROM games WHERE file_type='rom' GROUP BY s"
            ).fetchall():
                status_counts[_row["s"]] = _row["n"]
    except Exception:
        _logger.debug("Extra KPIs query failed", exc_info=True)

    # UI-2: health summary from health_schedule.json
    health: dict = {}
    if project_root is not None:
        try:
            import json as _json

            _hp = project_root / ".rommgr" / "health_schedule.json"
            if _hp.exists():
                health = _json.loads(_hp.read_text(encoding="utf-8"))
        except Exception:
            _logger.debug("No se pudo leer health_schedule.json", exc_info=True)

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
        "total_platforms": total_platforms,
        "last_sync_at": last_sync_at,
        "health": health,
        "total_size_bytes": total_size_bytes,
        "status_counts": status_counts,
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
        offset=offset,
        limit=limit,
        platform=platform,
        status=status,
        source_root=source_root,
        file_type=file_type,
        search=search,
        play_status=play_status,
        favorite=favorite,
        tag=tag,
        genre=genre,
        year=year,
        region=region,
        sort_by=sort_by,
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
            1
            for f in source.parent.iterdir()
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
    config=None,
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
        pending_ops = [
            op for op in pending_ops if str(op.source_path).lower().startswith(root_lower)
        ]
        conflict_ops = [
            op for op in conflict_ops if str(op.source_path).lower().startswith(root_lower)
        ]
        already_correct = [
            op for op in already_correct if str(op.source_path).lower().startswith(root_lower)
        ]
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
        pending_rows.append(
            {
                "platform": op.game.platform,
                "source": str(op.source_path),
                "source_name": op.source_path.name,
                "target": str(op.target_path),
                "target_name": op.target_path.name,
                "companion_saves": companions,
                "device": device_tag,
            }
        )
    unmatched_games = repository.get_unresolved_games()
    if source_root:
        root_lower = source_root.lower()
        unmatched_games = [
            g for g in unmatched_games if g.source_path.lower().startswith(root_lower)
        ]

    with repository.connect() as _conn:
        _matched_plats = {
            row[0]
            for row in _conn.execute(
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
        {
            "original_filename": g.original_filename,
            "platform": g.platform,
            "unmatched_reason": _unmatched_reason(g),
        }
        for g in unmatched_games
    ]

    # Late import: avoids a load-time dependency cycle between the library and
    # duplicates builder modules (the call graph crosses domains here).
    from rom_manager.web.builders.duplicates import _annotate_conflicts_with_ra

    conflict_rows = _annotate_conflicts_with_ra(conflict_ops, repository, config)

    return {
        "total": plan.total,
        "already_correct": len(already_correct),
        "pending": pending_rows,
        "conflicts": conflict_rows,
        "total_saves_affected": total_saves,
        "unmatched_count": len(unmatched_rows),
        "unmatched": unmatched_rows,
    }
