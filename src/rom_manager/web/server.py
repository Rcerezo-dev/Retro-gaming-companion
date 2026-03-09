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
}
_job_results: dict[str, dict] = {}
_chd_progress: dict = {}     # {"current": int, "total": int, "current_file": str}
_scrape_progress: dict = {}  # {"current": int, "total": int, "found": int, "current_game": str}
_zip_progress: dict = {}     # {"current": int, "total": int, "current_file": str}
_health_progress: dict = {}  # {"current": int, "total": int, "current_file": str}
_logger = logging.getLogger(__name__)


def _json_response(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode()


def _build_status(repository: LibraryRepository) -> dict:
    summary = repository.get_summary()
    dup_groups = repository.get_duplicate_groups()
    from rom_manager.reports.reporter import _get_all_games
    games = _get_all_games(repository)
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
) -> dict:
    games, total = repository.get_games_paginated(
        offset=offset, limit=limit, platform=platform, status=status
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
    pending_rows = []
    total_saves = 0
    for op in plan.pending:
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
    return {
        "total": plan.total,
        "already_correct": len(plan.already_correct),
        "pending": pending_rows,
        "conflicts": [
            {
                "source_name": op.source_path.name,
                "target_name": op.target_path.name,
            }
            for op in plan.conflicts
        ],
        "total_saves_affected": total_saves,
    }


def _build_duplicates(repository: LibraryRepository) -> dict:
    groups = repository.get_duplicate_groups()
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


def _build_assets(repository: LibraryRepository) -> dict:
    return {"stats": repository.get_asset_platform_stats()}


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
                    self._send_json(_build_status(repository))
                elif path == "/api/games":
                    qs = parse_qs(parsed.query)
                    offset = int(qs.get("offset", ["0"])[0])
                    limit = min(int(qs.get("limit", ["100"])[0]), 500)
                    plat = qs.get("platform", [None])[0] or None
                    st = qs.get("status", [None])[0] or None
                    self._send_json(_build_games(repository, offset=offset, limit=limit, platform=plat, status=st))
                elif path == "/api/plan":
                    opts = _parse_format_opts(qs)
                    self._send_json(_build_plan(repository, opts, frozenset(config.save_extensions)))
                elif path == "/api/duplicates":
                    self._send_json(_build_duplicates(repository))
                elif path == "/api/assets":
                    self._send_json(_build_assets(repository))
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
                        })
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

            def run() -> None:
                try:
                    from rom_manager.scanner import scan_library
                    from rom_manager.scanner.rom_scanner import ScanResult
                    total = ScanResult()
                    for raw in raw_paths:
                        source = Path(raw).resolve()
                        r = scan_library(source, config, repository, logger, quick=quick)
                        total.files_seen += r.files_seen
                        total.roms_detected += r.roms_detected
                        total.roms_skipped += r.roms_skipped
                        total.saves_detected += r.saves_detected
                        total.errors += r.errors
                    _job_results["scan"] = {
                        "files_seen": total.files_seen,
                        "roms_detected": total.roms_detected,
                        "roms_skipped": total.roms_skipped,
                        "saves_detected": total.saves_detected,
                        "errors": total.errors,
                        "paths_scanned": len(raw_paths),
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
            self._send_json({"saved": list(updates.keys())})

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
                    extracted = skipped = failed = 0
                    results = []
                    for idx, zp in enumerate(zip_files, 1):
                        _zip_progress.update({"current": idx, "total": total, "current_file": zp.name})
                        r = extract_zip(zp, dry_run=dry_run, delete_source=delete_source)
                        if r.skipped_reason:
                            skipped += 1
                        elif r.error:
                            failed += 1
                        else:
                            extracted += 1
                        results.append({
                            "zip": zp.name,
                            "success": r.success,
                            "skipped_reason": r.skipped_reason,
                            "error": r.error,
                            "extracted": [f.name for f in r.extracted_files],
                        })
                    _job_results["extract_zip"] = {
                        "dry_run": dry_run,
                        "extracted": extracted,
                        "skipped": skipped,
                        "failed": failed,
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
                            result = client.search(
                                crc32=game["crc32"],
                                md5=game["md5"],
                                sha1=game["sha1"],
                                filename=game["original_filename"],
                                size_bytes=game["size_bytes"],
                                system_id=get_system_id(game["platform"]),
                            )
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

            save_exts = frozenset(config.save_extensions)
            plan = build_plan(repository, opts)
            renamed = failed = saves_renamed = 0
            timestamp = utc_now()
            for op in plan.pending:
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
                    saves_renamed += outcome.saves_renamed
                else:
                    failed += 1

            self._send_json({
                "renamed": renamed,
                "failed": failed,
                "saves_renamed": saves_renamed,
                "conflicts": len(plan.conflicts),
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
