from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.router import Router
    import types


# ── Public entry point ────────────────────────────────────────────────────────

def register(
    router: "Router",
    *,
    config: "AppConfig",
    repository: "LibraryRepository",
    repo_android: "LibraryRepository",
    get_repo_fn: "Callable[[str], LibraryRepository]",
    start_ra_check_fn: "Callable[[str], bool]",
    srv_mod: "types.ModuleType",
) -> None:
    """Register scan / catalog / job-status routes on *router*."""
    from rom_manager.web.response_builders import _build_scrape_summary

    # ── GET /api/job-status ───────────────────────────────────────────────────
    @router.get("/api/job-status")
    def get_job_status(ctx) -> None:
        m = srv_mod
        with m._job_lock:
            ctx._send_json({
                "scan_running":          m._jobs["scan"],
                "match_running":         m._jobs["match"],
                "sync_running":          m._jobs["sync"],
                "convert_chd_running":   m._jobs["convert_chd"],
                "convert_cso_running":   m._jobs["convert_cso"],
                "scrape_running":        m._jobs["scrape"],
                "scan_result":           m._job_results.get("scan"),
                "match_result":          m._job_results.get("match"),
                "sync_result":           m._job_results.get("sync"),
                "convert_chd_result":    m._job_results.get("convert_chd"),
                "convert_cso_result":    m._job_results.get("convert_cso"),
                "scrape_result":         m._job_results.get("scrape"),
                "chd_progress":          dict(m._chd_progress)    if m._chd_progress    else None,
                "cso_progress":          dict(m._cso_progress)    if m._cso_progress    else None,
                "scrape_progress":       dict(m._scrape_progress) if m._scrape_progress else None,
                "extract_zip_running":   m._jobs["extract_zip"],
                "zip_progress":          dict(m._zip_progress)    if m._zip_progress    else None,
                "health_check_running":  m._jobs["health_check"],
                "health_progress":       dict(m._health_progress) if m._health_progress else None,
                "health_check_result":   m._job_results.get("health_check"),
                "extract_zip_result":    m._job_results.get("extract_zip"),
                "ra_check_running":      m._jobs["ra_check"],
                "ra_progress":           dict(m._ra_progress)     if m._ra_progress     else None,
                "ra_check_result":       m._job_results.get("ra_check"),
                "cable_sync_running":    m._jobs["cable_sync"],
                "cable_progress":        dict(m._cable_progress)  if m._cable_progress  else None,
                "cable_sync_result":     m._job_results.get("cable_sync"),
                "scan_progress":         dict(m._scan_progress)   if m._scan_progress   else None,
                "apply_running":         m._jobs["apply"],
                "apply_progress":        dict(m._apply_progress)  if m._apply_progress  else None,
                "apply_result":          m._job_results.get("apply"),
                "inbox_running":         m._jobs["inbox"],
                "inbox_progress":        dict(m._inbox_progress)  if m._inbox_progress  else None,
                "inbox_result":          m._job_results.get("inbox"),
                "setup_running":         m._jobs["setup"],
                "setup_progress":        dict(m._setup_progress)  if m._setup_progress  else None,
                "setup_result":          m._job_results.get("setup"),
                "backup_now_running":    m._jobs.get("backup_now", False),
                "backup_now_result":     m._job_results.get("backup_now"),
                "tree_diff_running":     m._jobs.get("tree_diff", False),
                "tree_diff_result":      m._job_results.get("tree_diff"),
                "inbox_pending_files":   m._inbox_watcher_status.get("pending_files", 0),
                "verify_chd_running":    m._jobs.get("verify_chd", False),
                "verify_chd_progress":   dict(m._verify_chd_progress) if m._verify_chd_progress else None,
                "verify_chd_result":     m._job_results.get("verify_chd"),
            })

    # ── GET /api/catalog-status ───────────────────────────────────────────────
    @router.get("/api/catalog-status")
    def get_catalog_status(ctx) -> None:
        ctx._send_json(_catalog_status(config))

    # ── GET /api/logs ─────────────────────────────────────────────────────────
    @router.get("/api/logs")
    def get_logs(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        lines_n = int(qs.get("lines", ["200"])[0])
        log_files = {
            "rommgr":     config.logs_dir / "rommgr.log",
            "cable_sync": config.project_root / ".rommgr" / "cable_sync_ops.log",
        }
        logs_out: dict = {}
        for key, lp in log_files.items():
            if lp.exists():
                try:
                    raw = lp.read_text(encoding="utf-8", errors="replace")
                    all_lines = raw.splitlines()
                    logs_out[key] = {
                        "path": str(lp),
                        "lines": all_lines[-lines_n:],
                        "total_lines": len(all_lines),
                        "size_bytes": lp.stat().st_size,
                    }
                except Exception as exc:
                    logs_out[key] = {"path": str(lp), "error": str(exc)}
            else:
                logs_out[key] = {"path": str(lp), "lines": [], "total_lines": 0, "size_bytes": 0}
        ctx._send_json({"logs": logs_out})

    # ── GET /api/scrape-summary ───────────────────────────────────────────────
    @router.get("/api/scrape-summary")
    def get_scrape_summary(ctx) -> None:
        ctx._send_json(_build_scrape_summary(repository))

    # ── POST /api/scan ────────────────────────────────────────────────────────
    @router.post("/api/scan")
    def post_scan(ctx) -> None:
        _do_scan(ctx, ctx._post_data, config, repository, get_repo_fn, start_ra_check_fn, srv_mod)

    # ── POST /api/adb-scan ────────────────────────────────────────────────────
    @router.post("/api/adb-scan")
    def post_adb_scan(ctx) -> None:
        _do_adb_scan(ctx, ctx._post_data, config, repo_android, srv_mod)

    # ── POST /api/match ───────────────────────────────────────────────────────
    @router.post("/api/match")
    def post_match(ctx) -> None:
        _do_match(ctx, config, repository, srv_mod)

    # ── POST /api/stop-job ────────────────────────────────────────────────────
    @router.post("/api/stop-job")
    def post_stop_job(ctx) -> None:
        m = srv_mod
        job_name = ctx._post_data.get("job", "")
        cancel_map = {
            "scan":         m._scan_cancel,
            "cable_sync":   m._cable_cancel,
            "convert_chd":  m._chd_cancel,
            "extract_zip":  m._zip_cancel,
            "health_check": m._health_cancel,
            "ra_check":     m._ra_cancel,
            "scrape":       m._scrape_cancel,
            "match":        m._match_cancel,
        }
        if job_name in cancel_map:
            cancel_map[job_name].set()
        with m._job_lock:
            if job_name in m._jobs:
                m._jobs[job_name] = False
            m._scan_progress.clear()
        ctx._send_json({"status": "stopped", "job": job_name})

    # ── POST /api/import-dats ─────────────────────────────────────────────────
    @router.post("/api/import-dats")
    def post_import_dats(ctx) -> None:
        ctx._send_json(_import_dats(ctx._post_data, config))

    # ── POST /api/import-arcade-catalog ──────────────────────────────────────
    @router.post("/api/import-arcade-catalog")
    def post_import_arcade_catalog(ctx) -> None:
        ctx._send_json(_import_arcade_catalog(ctx._post_data, config))


# ── Handler logic (moved from server.py) ──────────────────────────────────────

def _catalog_status(config: "AppConfig") -> dict:
    """List DAT files in the nointro/redump/arcade catalog dirs with quick entry counts."""
    def _scan_dir(directory: Path, is_arcade: bool = False) -> list[dict]:
        files: list[dict] = []
        if not directory.exists():
            return files
        for f in sorted(directory.iterdir()):
            if f.suffix.lower() not in (".dat", ".xml") or not f.is_file():
                continue
            try:
                data = f.read_bytes()
                count = data.count(b"<machine ") if (is_arcade and f.suffix.lower() == ".xml") else data.count(b"<game")
            except OSError:
                count = 0
            try:
                size = f.stat().st_size
            except OSError:
                size = 0
            files.append({"name": f.name, "size_bytes": size, "entries": count})
        return files

    nointro = _scan_dir(config.catalogs_nointro_dir)
    redump  = _scan_dir(config.catalogs_redump_dir)
    arcade  = _scan_dir(config.catalogs_arcade_dir, is_arcade=True)
    return {
        "nointro":               nointro,
        "redump":                redump,
        "arcade":                arcade,
        "total_nointro_entries": sum(f["entries"] for f in nointro),
        "total_redump_entries":  sum(f["entries"] for f in redump),
        "total_arcade_entries":  sum(f["entries"] for f in arcade),
        "nointro_dir":           str(config.catalogs_nointro_dir),
        "redump_dir":            str(config.catalogs_redump_dir),
        "arcade_dir":            str(config.catalogs_arcade_dir),
    }


def _do_scan(
    ctx,
    data: dict,
    config: "AppConfig",
    repository: "LibraryRepository",
    get_repo_fn: "Callable[[str], LibraryRepository]",
    start_ra_check_fn: "Callable[[str], bool]",
    srv_mod,
) -> None:
    from rom_manager.web.response_builders import _build_library_report

    raw_paths = data.get("source_paths") or []
    single = data.get("source_path", "").strip()
    if single and not raw_paths:
        raw_paths = [single]
    raw_paths = [p.strip() for p in raw_paths if str(p).strip()]
    if not raw_paths:
        ctx._send_error(400, "source_path is required")
        return
    quick = bool(data.get("quick", False))

    m = srv_mod
    with m._job_lock:
        if m._jobs["scan"]:
            ctx._send_json({"status": "already_running"})
            return
        m._jobs["scan"] = True

    m._scan_cancel.clear()
    m._scan_progress.clear()

    import logging
    logger = logging.getLogger(__name__)

    def run() -> None:
        try:
            from rom_manager.scanner import scan_library
            from rom_manager.scanner.rom_scanner import ScanResult, utc_now

            total = ScanResult()

            def _progress_cb(files_seen: int, roms: int, current_file: str = "") -> None:
                m._scan_progress.update({
                    "files_seen": files_seen,
                    "roms_detected": roms,
                    "current_path": str(source),
                    "current_file": current_file,
                })

            for raw in raw_paths:
                source = Path(raw).resolve()
                m._scan_progress["current_path"] = str(source)
                _scan_repo = get_repo_fn(str(source))
                r = scan_library(
                    source, config, _scan_repo, logger, quick=quick,
                    stop_event=m._scan_cancel, progress_cb=_progress_cb,
                )
                total.files_seen      += r.files_seen
                total.roms_detected   += r.roms_detected
                total.roms_skipped    += r.roms_skipped
                total.saves_detected  += r.saves_detected
                total.errors          += r.errors

            m._job_results["scan"] = {
                "result_ts":     utc_now(),
                "files_seen":    total.files_seen,
                "roms_detected": total.roms_detected,
                "roms_skipped":  total.roms_skipped,
                "saves_detected":total.saves_detected,
                "errors":        total.errors,
                "paths_scanned": len(raw_paths),
                "pruned":        total.pruned,
                "cancelled":     m._scan_cancel.is_set(),
            }

            if not m._scan_cancel.is_set():
                if config.ra_api_key:
                    start_ra_check_fn(config.ra_api_key)
                for _rpt_path in raw_paths:
                    if not _rpt_path:
                        continue
                    def _cache_report(_p=_rpt_path):
                        try:
                            _rpt_data = _build_library_report(_p, get_repo_fn(_p), config)
                            cache_dir = config.project_root / ".rommgr"
                            cache_dir.mkdir(parents=True, exist_ok=True)
                            (cache_dir / "last_report.json").write_text(
                                json.dumps(_rpt_data, ensure_ascii=False), encoding="utf-8"
                            )
                        except Exception:
                            pass
                    threading.Thread(target=_cache_report, daemon=True).start()
        except Exception as exc:
            m._job_results["scan"] = {"error": str(exc)}
        finally:
            with m._job_lock:
                m._scan_progress.clear()
                m._jobs["scan"] = False

    threading.Thread(target=run, daemon=True).start()
    ctx._send_json({"status": "started"})


def _do_adb_scan(ctx, data: dict, config: "AppConfig", repo_android: "LibraryRepository", srv_mod) -> None:
    adb_serial   = data.get("adb_serial", "").strip()
    android_path = data.get("android_path", "/storage/emulated/0").strip().rstrip("/")

    if not adb_serial:
        ctx._send_error(400, "adb_serial is required")
        return

    m = srv_mod
    with m._job_lock:
        if m._jobs["scan"]:
            ctx._send_json({"status": "already_running"})
            return
        m._jobs["scan"] = True

    import logging
    logger = logging.getLogger(__name__)

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

            scan_run_id = repo_android.create_scan_run(android_path, timestamp)
            roms = saves = assets = errors = 0
            seen_paths: set[str] = set()

            all_files = transport.ls_recursive(android_path, timeout=180)

            with repo_android.batch() as conn:
                for fi in all_files:
                    ap    = fi.android_path
                    seen_paths.add(ap)
                    parts = ap.split("/")
                    if any(seg.lower() in excluded for seg in parts):
                        continue

                    name   = PurePosixPath(ap).name
                    suffix = PurePosixPath(ap).suffix.lower()
                    try:
                        rel_parent = str(PurePosixPath(ap).parent.relative_to(android_path))
                    except ValueError:
                        rel_parent = ""

                    try:
                        if suffix in save_exts:
                            repo_android.upsert_save(
                                original_path=ap,
                                relative_parent=rel_parent,
                                extension=suffix,
                                size_bytes=fi.size,
                                timestamp=timestamp,
                                connection=conn,
                            )
                            saves += 1
                        elif suffix in asset_exts or name.lower() == "gamelist.xml":
                            assets += 1
                        elif suffix in {
                            ".zip", ".7z", ".rar",
                            ".xml", ".txt", ".log", ".db",
                            ".apk", ".sh", ".py",
                        } or not suffix:
                            pass
                        else:
                            fake_path = Path(ap)
                            platform  = detect_platform(fake_path)
                            repo_android.upsert_game(
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

            pruned      = repo_android.prune_stale_entries(android_path, seen_paths)
            finished_at = utc_now()
            repo_android.complete_scan_run(
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
            m._job_results["scan"] = {
                "result_ts":     utc_now(),
                "files_seen":    len(all_files),
                "roms_detected": roms,
                "roms_skipped":  0,
                "saves_detected":saves,
                "errors":        errors,
                "paths_scanned": 1,
                "pruned":        pruned,
                "source":        "adb",
                "android_path":  android_path,
            }
        except Exception as exc:
            m._job_results["scan"] = {"error": str(exc)}
        finally:
            with m._job_lock:
                m._jobs["scan"] = False

    threading.Thread(target=run, daemon=True).start()
    ctx._send_json({"status": "started"})


def _do_match(ctx, config: "AppConfig", repository: "LibraryRepository", srv_mod) -> None:
    m = srv_mod

    def run() -> None:
        m._match_cancel.clear()
        try:
            from rom_manager.catalog.matcher import CatalogMatcher
            matcher = CatalogMatcher(
                nointro_dir=config.catalogs_nointro_dir,
                redump_dir=config.catalogs_redump_dir,
                arcade_dir=config.catalogs_arcade_dir,
            )
            games = repository.get_unresolved_games()
            matched_high = matched_low = unmatched = 0
            with repository.batch() as conn:
                for game in games:
                    if m._match_cancel.is_set():
                        break
                    result = matcher.match(game.sha1, game.original_filename)
                    if result is not None:
                        repository.update_match(
                            game.source_path,
                            canonical_title=result.title,
                            match_confidence=result.confidence,
                            catalog_source=result.catalog_source,
                            platform=result.platform,
                            connection=conn,
                        )
                        if result.confidence == "high":
                            matched_high += 1
                        else:
                            matched_low += 1
                    else:
                        unmatched += 1
            m._job_results["match"] = {
                "total":         len(games),
                "matched_high":  matched_high,
                "matched_low":   matched_low,
                "unmatched":     unmatched,
                "cancelled":     m._match_cancel.is_set(),
            }
        except Exception as exc:
            m._job_results["match"] = {"error": str(exc)}
        finally:
            with m._job_lock:
                m._jobs["match"] = False

    ctx._send_json(m._start_job("match", run))


def _import_dats(data: dict, config: "AppConfig") -> dict:
    import shutil

    source = Path(data.get("source_folder", "")).expanduser()
    if not source.exists() or not source.is_dir():
        return {"error": f"Carpeta no encontrada: {source}"}

    imported: list[dict] = []
    errors:   list[dict] = []

    for f in sorted(source.iterdir()):
        if f.suffix.lower() not in (".dat", ".xml") or not f.is_file():
            continue
        try:
            with f.open("rb") as fh:
                sample = fh.read(2048)
            if b"<datafile" not in sample and b"<game" not in sample:
                continue
            fname_lower = f.name.lower()
            if "redump" in fname_lower:
                dest_dir    = config.catalogs_redump_dir
                catalog_type = "redump"
            else:
                dest_dir    = config.catalogs_nointro_dir
                catalog_type = "nointro"
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest_dir / f.name)
            imported.append({"name": f.name, "catalog": catalog_type})
        except Exception as exc:
            errors.append({"name": f.name, "error": str(exc)})

    return {"imported": imported, "errors": errors, "total": len(imported)}


def _import_arcade_catalog(data: dict, config: "AppConfig") -> dict:
    import shutil
    from rom_manager.catalog.mame_loader import load_mame_xml, load_fbneo_dat

    src = Path(data.get("path", "")).expanduser()
    if not src.exists():
        return {"error": f"Ruta no encontrada: {src}"}

    dest_dir = config.catalogs_arcade_dir
    dest_dir.mkdir(parents=True, exist_ok=True)

    if src.is_dir():
        candidates = sorted(f for f in src.iterdir() if f.is_file() and f.suffix.lower() in (".dat", ".xml"))
    elif src.is_file():
        candidates = [src]
    else:
        return {"error": f"La ruta no es un archivo ni una carpeta: {src}"}

    if not candidates:
        return {"error": "No se encontraron archivos .xml o .dat en la ruta indicada."}

    imported: list[dict] = []
    errors:   list[dict] = []

    for f in candidates:
        try:
            with f.open("rb") as fh:
                sample = fh.read(4096)
            if b"<mame" in sample or (b"<machine" in sample and b"<datafile" not in sample):
                fmt     = "mame_xml"
                entries = load_mame_xml(f)
            elif b"<datafile" in sample or b"<game" in sample:
                fmt     = "fbneo_dat"
                entries = load_fbneo_dat(f)
            else:
                errors.append({"name": f.name, "error": "Formato no reconocido"})
                continue

            if not entries:
                errors.append({"name": f.name, "error": "Sin entradas válidas"})
                continue

            shutil.copy2(f, dest_dir / f.name)
            imported.append({"name": f.name, "format": fmt, "entries": len(entries)})
        except Exception as exc:
            errors.append({"name": f.name, "error": str(exc)})

    if not imported:
        return {"error": "No se importó ningún archivo. " + (errors[0]["error"] if errors else "")}

    return {
        "ok":           True,
        "imported":     imported,
        "errors":       errors,
        "total_files":  len(imported),
        "total_entries":sum(x["entries"] for x in imported),
    }
