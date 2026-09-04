from __future__ import annotations

import json
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import rom_manager.web.state as _state
from rom_manager.web.jobs.manager import JOB_NAMES

# ── DAT auto-download catalog (libretro-database, MIT license) ────────────────
_LIBRETRO_DAT_CATALOG = [
    # Nintendo cartridge → nointro/
    {"name": "Nintendo - Nintendo Entertainment System", "short": "NES", "catalog": "nointro"},
    {
        "name": "Nintendo - Super Nintendo Entertainment System",
        "short": "SNES",
        "catalog": "nointro",
    },
    {"name": "Nintendo - Nintendo 64", "short": "N64", "catalog": "nointro"},
    {"name": "Nintendo - Game Boy", "short": "Game Boy", "catalog": "nointro"},
    {"name": "Nintendo - Game Boy Color", "short": "GBC", "catalog": "nointro"},
    {"name": "Nintendo - Game Boy Advance", "short": "GBA", "catalog": "nointro"},
    {"name": "Nintendo - Nintendo DS", "short": "DS", "catalog": "nointro"},
    {"name": "Nintendo - Nintendo 3DS", "short": "3DS", "catalog": "nointro"},
    {"name": "Nintendo - Virtual Boy", "short": "Virtual Boy", "catalog": "nointro"},
    # Sega cartridge → nointro/
    {"name": "Sega - Master System - Mark III", "short": "Master System", "catalog": "nointro"},
    {"name": "Sega - Mega Drive - Genesis", "short": "Mega Drive", "catalog": "nointro"},
    {"name": "Sega - Game Gear", "short": "Game Gear", "catalog": "nointro"},
    {"name": "Sega - 32X", "short": "32X", "catalog": "nointro"},
    # Atari → nointro/
    {"name": "Atari - 2600", "short": "Atari 2600", "catalog": "nointro"},
    {"name": "Atari - 7800", "short": "Atari 7800", "catalog": "nointro"},
    {"name": "Atari - Lynx", "short": "Lynx", "catalog": "nointro"},
    # NEC → nointro/ + redump/
    {"name": "NEC - PC Engine - TurboGrafx 16", "short": "PC Engine", "catalog": "nointro"},
    {"name": "NEC - PC Engine CD - TurboGrafx-CD", "short": "PC-CD", "catalog": "redump"},
    # SNK → nointro/
    {"name": "SNK - Neo Geo Pocket", "short": "NGP", "catalog": "nointro"},
    {"name": "SNK - Neo Geo Pocket Color", "short": "NGPC", "catalog": "nointro"},
    # Bandai → nointro/
    {"name": "Bandai - WonderSwan", "short": "WonderSwan", "catalog": "nointro"},
    {"name": "Bandai - WonderSwan Color", "short": "WSC", "catalog": "nointro"},
    # Sony → redump/
    {"name": "Sony - PlayStation", "short": "PS1", "catalog": "redump"},
    {"name": "Sony - PlayStation 2", "short": "PS2", "catalog": "redump"},
    {"name": "Sony - PlayStation Portable", "short": "PSP", "catalog": "redump"},
    # Sega optical → redump/
    {"name": "Sega - Saturn", "short": "Saturn", "catalog": "redump"},
    {"name": "Sega - Dreamcast", "short": "Dreamcast", "catalog": "redump"},
    # Nintendo optical → redump/
    {"name": "Nintendo - GameCube", "short": "GameCube", "catalog": "redump"},
    {"name": "Nintendo - Wii", "short": "Wii", "catalog": "redump"},
    # Microsoft → redump/
    {"name": "Microsoft - Xbox", "short": "Xbox", "catalog": "redump"},
    # Arcade → arcade/
    {"name": "FBNeo - Arcade Games", "short": "FBNeo Arcade", "catalog": "fbneo"},
    {"name": "MAME 2003-Plus", "short": "MAME 2003+", "catalog": "mame"},
    # listxml oficial de MAME (asset mameXXXXlx.zip de la última release en
    # GitHub) — única fuente de los flags isbios/isdevice/runnable que usan
    # load_arcade_infra_names y el junk-scan (JUNK-SMART-2). "file" fija el
    # nombre local en vez del patrón "{name}.dat".
    {
        "name": "MAME - Full listxml",
        "short": "MAME XML (bios/devices)",
        "catalog": "mame_xml",
        "file": "mame.xml",
    },
]

_LIBRETRO_METADAT_BASE = (
    "https://raw.githubusercontent.com/libretro/libretro-database/master/metadat"
)
_CATALOG_TO_SOURCE = {"nointro": "no-intro", "redump": "redump", "fbneo": "fbneo", "mame": "mame"}
_DAT_TTL_DAYS = 7  # re-download if the local DAT is older than this

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router


# ── Public entry point ────────────────────────────────────────────────────────


def register(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    repo_android: LibraryRepository,
    get_repo_fn: Callable[[str], LibraryRepository],
    start_ra_check_fn: Callable[[str], bool],
    job_manager: JobManager,
) -> None:
    """Register scan / catalog / job-status routes on *router*."""
    from rom_manager.web.builders.misc import _build_scrape_summary

    # ── GET /api/job-status ───────────────────────────────────────────────────
    @router.get("/api/job-status")
    def get_job_status(ctx) -> None:
        # All background jobs (including cable_sync) are managed by job_manager.
        status = job_manager.get_status()
        status["inbox_pending_files"] = _state._inbox_watcher_status.get("pending_files", 0)
        ctx._send_json(status)

    # ── GET /api/catalog-status ───────────────────────────────────────────────
    @router.get("/api/catalog-status")
    def get_catalog_status(ctx) -> None:
        ctx._send_json(_catalog_status(config))

    # ── GET /api/logs ─────────────────────────────────────────────────────────
    @router.get("/api/logs")
    def get_logs(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        lines_n = min(int(qs.get("lines", ["200"])[0]), 5000)
        log_files = {
            "rommgr": config.logs_dir / "rommgr.log",
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
        _do_scan(
            ctx, ctx._post_data, config, repository, get_repo_fn, start_ra_check_fn, job_manager
        )

    # ── POST /api/adb-scan ────────────────────────────────────────────────────
    @router.post("/api/adb-scan")
    def post_adb_scan(ctx) -> None:
        _do_adb_scan(ctx, ctx._post_data, config, repo_android, job_manager)

    # ── POST /api/match ───────────────────────────────────────────────────────
    @router.post("/api/match")
    def post_match(ctx) -> None:
        _do_match(ctx, config, repository, job_manager, ctx._post_data or {})

    # ── POST /api/stop-job ────────────────────────────────────────────────────
    @router.post("/api/stop-job")
    def post_stop_job(ctx) -> None:
        # All background jobs are managed by job_manager.
        job_name = ctx._post_data.get("job", "")
        if job_name in JOB_NAMES:
            job_manager.cancel(job_name)
        ctx._send_json({"status": "stopped", "job": job_name})

    # ── POST /api/import-dats ─────────────────────────────────────────────────
    @router.post("/api/import-dats")
    def post_import_dats(ctx) -> None:
        ctx._send_json(_import_dats(ctx._post_data, config))

    # ── POST /api/import-arcade-catalog ──────────────────────────────────────
    @router.post("/api/import-arcade-catalog")
    def post_import_arcade_catalog(ctx) -> None:
        ctx._send_json(_import_arcade_catalog(ctx._post_data, config))

    # ── GET /api/dat-catalog-list ─────────────────────────────────────────────
    @router.get("/api/dat-catalog-list")
    def get_dat_catalog_list(ctx) -> None:
        """Return the downloadable DAT catalog with download status and age per entry."""
        ctx._send_json(_build_dat_catalog_list(config))

    # ── GET /api/download-dats-status ─────────────────────────────────────────
    @router.get("/api/download-dats-status")
    def get_download_dats_status(ctx) -> None:
        job = job_manager.get_job("download_dats")
        progress = job["progress"] or {}
        ctx._send_json(
            {
                "running": job["running"],
                "total": progress.get("total", 0),
                "done": progress.get("done", 0),
                "current": progress.get("current", ""),
                "result": job["result"],
            }
        )

    # ── POST /api/download-dats ───────────────────────────────────────────────
    @router.post("/api/download-dats")
    def post_download_dats(ctx) -> None:
        data = ctx._post_data or {}
        all_sys = data.get("all", False)
        names = set(data.get("systems", []))
        systems = (
            _LIBRETRO_DAT_CATALOG
            if all_sys
            else [s for s in _LIBRETRO_DAT_CATALOG if s["name"] in names]
        )
        if not systems:
            ctx._send_json({"status": "error", "error": "No se han seleccionado sistemas"})
            return

        result = job_manager.start(
            "download_dats", lambda: _run_dat_download(systems, config, job_manager)
        )
        if result["status"] == "already_running":
            ctx._send_json(result)
            return
        ctx._send_json({"status": "started", "total": len(systems)})


# ── Handler logic (moved from server.py) ──────────────────────────────────────


def _catalog_status(config: AppConfig) -> dict:
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
                count = (
                    data.count(b"<machine ")
                    if (is_arcade and f.suffix.lower() == ".xml")
                    else data.count(b"<game")
                )
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
    arcade = _scan_dir(config.catalogs_arcade_dir, is_arcade=True)
    return {
        "nointro": nointro,
        "redump": redump,
        "arcade": arcade,
        "total_nointro_entries": sum(f["entries"] for f in nointro),
        "total_redump_entries": sum(f["entries"] for f in redump),
        "total_arcade_entries": sum(f["entries"] for f in arcade),
        "nointro_dir": str(config.catalogs_nointro_dir),
        "redump_dir": str(config.catalogs_redump_dir),
        "arcade_dir": str(config.catalogs_arcade_dir),
    }


def _do_scan(
    ctx,
    data: dict,
    config: AppConfig,
    repository: LibraryRepository,
    get_repo_fn: Callable[[str], LibraryRepository],
    start_ra_check_fn: Callable[[str], bool],
    job_manager: JobManager,
) -> None:
    from rom_manager.web.builders.library import _build_library_report

    raw_paths = data.get("source_paths") or []
    single = data.get("source_path", "").strip()
    if single and not raw_paths:
        raw_paths = [single]
    raw_paths = [p.strip() for p in raw_paths if str(p).strip()]
    if not raw_paths and config.library_root:
        raw_paths = [str(config.library_root)]
    if not raw_paths:
        ctx._send_error(400, "source_path is required")
        return
    quick = bool(data.get("quick", False))

    import logging

    logger = logging.getLogger(__name__)
    _cancel = job_manager.cancel_event("scan")

    def run() -> None:
        job_result = None
        try:
            from rom_manager.scanner import scan_library
            from rom_manager.scanner.rom_scanner import ScanResult, utc_now

            total = ScanResult()

            def _progress_cb(files_seen: int, roms: int, current_file: str = "") -> None:
                job_manager.update_progress(
                    "scan",
                    {
                        "files_seen": files_seen,
                        "roms_detected": roms,
                        "current_path": str(source),
                        "current_file": current_file,
                    },
                )

            for raw in raw_paths:
                source = Path(raw).resolve()
                job_manager.update_progress("scan", {"current_path": str(source)})
                _scan_repo = get_repo_fn(str(source))
                r = scan_library(
                    source,
                    config,
                    _scan_repo,
                    logger,
                    quick=quick,
                    stop_event=_cancel,
                    progress_cb=_progress_cb,
                )
                total.files_seen += r.files_seen
                total.roms_detected += r.roms_detected
                total.roms_skipped += r.roms_skipped
                total.saves_detected += r.saves_detected
                total.errors += r.errors

            job_result = {
                "result_ts": utc_now(),
                "files_seen": total.files_seen,
                "roms_detected": total.roms_detected,
                "roms_skipped": total.roms_skipped,
                "saves_detected": total.saves_detected,
                "errors": total.errors,
                "paths_scanned": len(raw_paths),
                "pruned": total.pruned,
                "cancelled": _cancel.is_set(),
            }

            if not _cancel.is_set():
                if config.credentials.ra_api_key:
                    start_ra_check_fn(config.credentials.ra_api_key)
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
                            logger.debug(
                                "No se pudo cachear last_report.json tras el scan", exc_info=True
                            )

                    threading.Thread(target=_cache_report, daemon=True).start()
        except Exception as exc:
            job_result = {"error": str(exc)}
        finally:
            job_manager.finish("scan", job_result)

    ctx._send_json(job_manager.start("scan", run))


def _do_adb_scan(
    ctx, data: dict, config: AppConfig, repo_android: LibraryRepository, job_manager: JobManager
) -> None:
    adb_serial = data.get("adb_serial", "").strip()
    android_path = data.get("android_path", "/storage/emulated/0").strip().rstrip("/")

    if not adb_serial:
        ctx._send_error(400, "adb_serial is required")
        return

    import logging

    logger = logging.getLogger(__name__)
    _cancel = job_manager.cancel_event("scan")

    def run() -> None:
        job_result = None
        try:
            from pathlib import PurePosixPath

            from rom_manager.detection.platform_detector import detect_platform
            from rom_manager.detection.region_parser import parse_region_from_name
            from rom_manager.detection.set_detector import detect_set_type
            from rom_manager.scanner.rom_scanner import utc_now
            from rom_manager.sync.adb_transport import AdbTransport

            transport = AdbTransport(config.adb, adb_serial, timeout=120)
            timestamp = utc_now()
            save_exts = frozenset(config.save_extensions)
            asset_exts = frozenset(config.frontend_asset_extensions)
            excluded = frozenset(d.lower() for d in config.excluded_directories)

            scan_run_id = repo_android.create_scan_run(android_path, timestamp)
            roms = saves = assets = errors = 0
            seen_paths: set[str] = set()

            all_files = transport.ls_recursive(android_path, timeout=180)

            with repo_android.batch() as conn:
                for fi in all_files:
                    if _cancel.is_set():
                        break
                    ap = fi.android_path
                    seen_paths.add(ap)
                    parts = ap.split("/")
                    if any(seg.lower() in excluded for seg in parts):
                        continue

                    name = PurePosixPath(ap).name
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
                        elif (
                            suffix
                            in {
                                ".zip",
                                ".7z",
                                ".rar",
                                ".xml",
                                ".txt",
                                ".log",
                                ".db",
                                ".apk",
                                ".sh",
                                ".py",
                            }
                            or not suffix
                        ):
                            pass
                        else:
                            fake_path = Path(ap)
                            platform = detect_platform(fake_path)
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

            pruned = repo_android.prune_stale_entries(android_path, seen_paths)
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
            job_result = {
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
                "cancelled": _cancel.is_set(),
            }
        except Exception as exc:
            job_result = {"error": str(exc)}
        finally:
            job_manager.finish("scan", job_result)

    ctx._send_json(job_manager.start("scan", run))


def _do_match(
    ctx,
    config: AppConfig,
    repository: LibraryRepository,
    job_manager: JobManager,
    data: dict | None = None,
) -> None:
    _cancel = job_manager.cancel_event("match")
    include_low_confidence = bool((data or {}).get("include_low_confidence"))

    def run() -> None:
        job_result = None
        try:
            from rom_manager.catalog.matcher import CatalogMatcher

            matcher = CatalogMatcher(
                nointro_dir=config.catalogs_nointro_dir,
                redump_dir=config.catalogs_redump_dir,
                arcade_dir=config.catalogs_arcade_dir,
                chdman_path=config.chdman,
            )
            games = repository.get_unresolved_games(include_low_confidence=include_low_confidence)
            matched_high = matched_low = unmatched = 0
            with repository.batch() as conn:
                for game in games:
                    if _cancel.is_set():
                        break
                    match = matcher.match(game.sha1, game.original_filename, game.source_path)
                    if match is not None:
                        repository.update_match(
                            game.source_path,
                            canonical_title=match.title,
                            match_confidence=match.confidence,
                            catalog_source=match.catalog_source,
                            platform=match.platform,
                            connection=conn,
                        )
                        if match.confidence == "high":
                            matched_high += 1
                        else:
                            matched_low += 1
                    else:
                        unmatched += 1
            job_result = {
                "total": len(games),
                "matched_high": matched_high,
                "matched_low": matched_low,
                "unmatched": unmatched,
                "cancelled": _cancel.is_set(),
            }
        except Exception as exc:
            job_result = {"error": str(exc)}
        finally:
            job_manager.finish("match", job_result)

    ctx._send_json(job_manager.start("match", run))


def _import_dats(data: dict, config: AppConfig) -> dict:
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
            if b"<datafile" not in sample and b"<game" not in sample:
                continue
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


def _run_dat_download(systems: list[dict], config: AppConfig, job_manager: JobManager) -> None:
    """Download DAT files from libretro-database and save to the catalog dirs."""
    import urllib.error
    import urllib.parse
    import urllib.request as _urlreq

    from rom_manager.catalog.catalog_loader import load_dat_file

    downloaded: list[str] = []
    skipped: list[str] = []
    errors: list[dict] = []

    job_manager.update_progress("download_dats", {"total": len(systems), "done": 0, "current": ""})

    for i, entry in enumerate(systems):
        name = entry["name"]
        catalog = entry["catalog"]
        filename = entry.get("file") or (name + ".dat")
        dest_dir = {
            "redump": config.catalogs_redump_dir,
            "fbneo": config.catalogs_arcade_dir,
            "mame": config.catalogs_arcade_dir,
            "mame_xml": config.catalogs_arcade_dir,
        }.get(catalog, config.catalogs_nointro_dir)
        dest_file = dest_dir / filename

        job_manager.update_progress("download_dats", {"current": name, "done": i})

        if dest_file.exists() and _is_dat_fresh(dest_file):
            skipped.append(name)
            continue

        if catalog == "mame_xml":
            err = _download_mame_listxml(dest_file)
            if err:
                errors.append({"name": name, "error": err})
            else:
                downloaded.append(name)
            continue

        source = _CATALOG_TO_SOURCE.get(catalog, "no-intro")
        url = f"{_LIBRETRO_METADAT_BASE}/{source}/{urllib.parse.quote(filename)}"
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            with _urlreq.urlopen(url, timeout=30) as resp:  # noqa: S310 — URL is a hardcoded constant
                data = resp.read()
            dest_file.write_bytes(data)
            try:
                entries = load_dat_file(dest_file)
            except Exception:
                entries = {}
            if not entries:
                dest_file.unlink(missing_ok=True)
                errors.append({"name": name, "error": "DAT sin entradas válidas"})
                continue
            downloaded.append(name)
        except urllib.error.URLError as exc:
            errors.append({"name": name, "error": str(exc.reason)})
        except Exception as exc:
            errors.append({"name": name, "error": str(exc)})

    job_manager.finish(
        "download_dats", {"downloaded": downloaded, "skipped": skipped, "errors": errors}
    )


def _download_mame_listxml(dest_file: Path) -> str:
    """Descarga el listxml oficial de MAME y lo extrae como *dest_file*.

    Resuelve la última release vía la API de GitHub (el asset ``*lx.zip``,
    ~19 MB comprimido / ~300 MB extraído). Devuelve "" si todo fue bien o el
    mensaje de error — nunca lanza, como el resto del descargador.
    """
    import io
    import os
    import shutil
    import urllib.error
    import urllib.request as _urlreq
    import zipfile

    api_url = "https://api.github.com/repos/mamedev/mame/releases/latest"
    try:
        with _urlreq.urlopen(api_url, timeout=30) as resp:  # noqa: S310 — constante
            release = json.load(resp)
        asset = next(
            (a for a in release.get("assets", []) if a.get("name", "").endswith("lx.zip")),
            None,
        )
        if not asset:
            return "La última release de MAME no incluye el asset *lx.zip"
        with _urlreq.urlopen(asset["browser_download_url"], timeout=600) as resp:  # noqa: S310
            data = resp.read()
        # Extraer a .part y renombrar al final: un fallo a mitad no debe dejar
        # un mame.xml corrupto pisando el que ya funcionaba
        part = dest_file.with_name(dest_file.name + ".part")
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            inner = next((n for n in z.namelist() if n.lower().endswith(".xml")), None)
            if not inner:
                return "El ZIP de la release no contiene ningún .xml"
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            with z.open(inner) as src, open(part, "wb") as out:
                shutil.copyfileobj(src, out)
        # El DTD inicial ocupa unos pocos KB; si en 256 KB no hay <machine>,
        # el formato no es el esperado
        if b"<machine" not in part.read_bytes()[:262_144]:
            part.unlink(missing_ok=True)
            return "XML descargado pero sin elementos <machine> — formato inesperado"
        os.replace(part, dest_file)
        return ""
    except urllib.error.URLError as exc:
        return f"Error de red: {exc.reason}"
    except Exception as exc:  # noqa: BLE001 — el resultado viaja al frontend
        return str(exc)


def _is_dat_fresh(path: Path) -> bool:
    """Return True if *path* was modified within _DAT_TTL_DAYS."""
    import time

    return (time.time() - path.stat().st_mtime) < (_DAT_TTL_DAYS * 86_400)


def _build_dat_catalog_list(config: AppConfig) -> dict:
    """Return catalog list with downloaded status, mtime, age and stale flag per entry."""
    import datetime as _dt

    def _index_dir(directory: Path) -> dict[str, Path]:
        if not directory.exists():
            return {}
        # .xml además de .dat: el listxml de MAME se guarda como mame.xml
        return {f.stem: f for f in directory.iterdir() if f.suffix.lower() in (".dat", ".xml")}

    nointro_files = _index_dir(config.catalogs_nointro_dir)
    redump_files = _index_dir(config.catalogs_redump_dir)
    arcade_files = _index_dir(config.catalogs_arcade_dir)

    _catalog_dir = {"nointro": nointro_files, "redump": redump_files}

    now = _dt.datetime.now(_dt.UTC)
    result = []
    for entry in _LIBRETRO_DAT_CATALOG:
        files = _catalog_dir.get(entry["catalog"], arcade_files)
        stem = Path(entry["file"]).stem if "file" in entry else entry["name"]
        dat_path = files.get(stem)
        if dat_path is None:
            result.append(
                {
                    **entry,
                    "downloaded": False,
                    "mtime_iso": None,
                    "age_days": None,
                    "stale": False,
                }
            )
        else:
            mtime = _dt.datetime.fromtimestamp(dat_path.stat().st_mtime, tz=_dt.UTC)
            age_days = (now - mtime).days
            result.append(
                {
                    **entry,
                    "downloaded": True,
                    "mtime_iso": mtime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "age_days": age_days,
                    "stale": age_days >= _DAT_TTL_DAYS,
                }
            )
    return {"systems": result}


def _import_arcade_catalog(data: dict, config: AppConfig) -> dict:
    import shutil

    from rom_manager.catalog.mame_loader import load_fbneo_dat, load_mame_xml

    src = Path(data.get("path", "")).expanduser()
    if not src.exists():
        return {"error": f"Ruta no encontrada: {src}"}

    dest_dir = config.catalogs_arcade_dir
    dest_dir.mkdir(parents=True, exist_ok=True)

    if src.is_dir():
        candidates = sorted(
            f for f in src.iterdir() if f.is_file() and f.suffix.lower() in (".dat", ".xml")
        )
    elif src.is_file():
        candidates = [src]
    else:
        return {"error": f"La ruta no es un archivo ni una carpeta: {src}"}

    if not candidates:
        return {"error": "No se encontraron archivos .xml o .dat en la ruta indicada."}

    imported: list[dict] = []
    errors: list[dict] = []

    for f in candidates:
        try:
            with f.open("rb") as fh:
                sample = fh.read(4096)
            if b"<mame" in sample or (b"<machine" in sample and b"<datafile" not in sample):
                fmt = "mame_xml"
                entries = load_mame_xml(f)
            elif b"<datafile" in sample or b"<game" in sample:
                fmt = "fbneo_dat"
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
        "ok": True,
        "imported": imported,
        "errors": errors,
        "total_files": len(imported),
        "total_entries": sum(x["entries"] for x in imported),
    }
