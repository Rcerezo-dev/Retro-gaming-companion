"""ES-DE library maintenance routes: health check, ZIP/cue+bin cleanup, junk delete.

Registered onto the shared router by ``register_maintenance``; the orchestrator
in ``esde/__init__.py`` calls it. The health check runs as a background job via
the JobManager; the cleanup/junk routes are synchronous filesystem operations.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router

_logger = logging.getLogger(__name__)


def register_maintenance(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    job_manager: JobManager,
) -> None:
    """Register health-check, cleanup-zips, cleanup-cue-bin and junk-delete routes."""

    # ── GET /api/trash-status (AUD-3) ─────────────────────────────────────────
    @router.get("/api/trash-status")
    def get_trash_status(ctx) -> None:
        from rom_manager.utils.trash import trash_roots, trash_stats

        stats = trash_stats(trash_roots(config))
        stats["purge_days"] = config.trash_purge_days
        ctx._send_json(stats)

    # ── POST /api/trash-empty (AUD-3) ─────────────────────────────────────────
    @router.post("/api/trash-empty")
    def post_trash_empty(ctx) -> None:
        from rom_manager.utils.trash import purge_trash, trash_roots

        ctx._send_json(purge_trash(trash_roots(config), older_than_days=0))

    # ── POST /api/health-check ────────────────────────────────────────────────
    @router.post("/api/health-check")
    def post_health_check(ctx) -> None:
        _cancel = job_manager.cancel_event("health_check")
        # AUD-6: verificación profunda de CHDs (chdman verify) — off por defecto, lenta
        _deep_chd = bool(getattr(ctx, "_post_data", {}).get("deep_chd", False))

        def run() -> None:
            job_result = None
            try:
                from rom_manager.scanner.rom_scanner import utc_now
                from rom_manager.utils.health_checker import check_library_health

                def progress_cb(current: int, total: int, filename: str) -> None:
                    job_manager.update_progress(
                        "health_check",
                        {"current": current, "total": total, "current_file": filename},
                    )

                summary = check_library_health(
                    repository,
                    progress_cb=progress_cb,
                    cancel_event=_cancel,
                    chd_verify=_deep_chd,
                    chdman_path=config.chdman,
                )
                job_result = {
                    "ok": summary.ok,
                    "corrupted": summary.corrupted,
                    "missing": summary.missing,
                    "chd_invalid": summary.chd_invalid,
                    "cancelled": _cancel.is_set(),
                    "issues": [
                        {
                            "source_path": r.source_path,
                            "status": r.status,
                            "stored_sha1": r.stored_sha1[:12],
                            "computed_sha1": r.computed_sha1[:12] if r.computed_sha1 else "",
                            "platform": r.platform,
                            "canonical_title": r.canonical_title,
                        }
                        for r in summary.results
                    ],
                    "result_ts": utc_now(),
                }
                from rom_manager.web.daemons import _write_health_schedule

                _write_health_schedule(
                    config, ok=summary.ok, corrupted=summary.corrupted, missing=summary.missing
                )
                if not _cancel.is_set() and config.notify_desktop:
                    from rom_manager.utils.notifier import notify

                    if summary.corrupted or summary.missing:
                        notify(
                            "Retro Vault — Health Check",
                            f"⚠ {summary.corrupted} corruptos, {summary.missing} desaparecidos — revisa la pestaña Tools",
                        )
                    else:
                        notify(
                            "Retro Vault — Health Check",
                            f"✓ {summary.ok} ROMs verificados, sin problemas",
                        )
            except Exception as exc:
                job_result = {"error": str(exc)}
            finally:
                job_manager.finish("health_check", job_result)

        ctx._send_json(job_manager.start("health_check", run))

    # ── POST /api/cleanup-zips ────────────────────────────────────────────────
    @router.post("/api/cleanup-zips")
    def post_cleanup_zips(ctx) -> None:
        data = ctx._post_data
        source_path_str = data.get("source_path", "").strip()
        if not source_path_str:
            ctx._send_json({"error": "source_path is required"})
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
        ctx._send_json({"deleted": deleted, "failed": failed, "freed_bytes": freed_bytes})

    # ── POST /api/cleanup-cue-bin ─────────────────────────────────────────────
    @router.post("/api/cleanup-cue-bin")
    def post_cleanup_cue_bin(ctx) -> None:
        data = ctx._post_data
        source_path_str = data.get("source_path", "").strip()
        if not source_path_str:
            ctx._send_json({"error": "source_path is required"})
            return
        source = Path(source_path_str).resolve()
        deleted = failed = skipped = 0
        freed_bytes = 0
        for cue in source.rglob("*.cue"):
            chd = cue.with_suffix(".chd")
            if not chd.exists():
                skipped += 1
                continue
            from rom_manager.converters.chd_converter import parse_bins_from_cue

            bins = parse_bins_from_cue(cue)
            for f in [cue, *bins]:
                try:
                    freed_bytes += f.stat().st_size
                    os.remove(f)
                    deleted += 1
                except OSError:
                    failed += 1
        ctx._send_json(
            {"deleted": deleted, "failed": failed, "skipped": skipped, "freed_bytes": freed_bytes}
        )

    def _full_junk_scan(folder: str) -> dict:
        """Junk-scan con todos los índices (catálogos + BD), compartido por
        /api/junk-scan y /api/library-extras."""
        from rom_manager.catalog.mame_loader import (
            load_arcade_crc_index,
            load_arcade_dir,
            load_arcade_infra_names,
        )
        from rom_manager.catalog.matcher import CatalogMatcher
        from rom_manager.web.builders.folders import _build_junk_scan
        from rom_manager.web.inbox_pipeline import _KNOWN_BIOS_MAP

        # JUNK-SMART-1: rutas con match de catálogo — evidencia de "no es basura"
        with repository.connect() as conn:
            rows = conn.execute(
                "SELECT source_path FROM games WHERE canonical_title IS NOT NULL"
            ).fetchall()
        matched = {os.path.normpath(r[0]).lower() for r in rows}
        # JUNK-SMART-2: conocimiento arcade para clasificar ZIPs sueltos
        # ponytail: se parsea el catálogo en cada scan; cachear si algún día duele
        arcade_dir = config.catalogs_arcade_dir
        arcade_names = set(load_arcade_dir(arcade_dir)) if arcade_dir else set()
        infra_names = load_arcade_infra_names(arcade_dir) if arcade_dir else set()
        known_bios = {k for k in _KNOWN_BIOS_MAP if k.endswith(".zip")}
        # ZIP-ROUTE-1: CRC32 de No-Intro/Redump para identificar ZIPs de
        # consola por el header del ZIP, sin descomprimir
        crc_index = CatalogMatcher(
            nointro_dir=config.catalogs_nointro_dir,
            redump_dir=config.catalogs_redump_dir,
        ).crc_index()
        # ZIP-ROUTE-2: CRC de los DAT arcade para identificar sets renombrados
        arcade_crcs = load_arcade_crc_index(arcade_dir) if arcade_dir else {}
        return _build_junk_scan(
            folder,
            matched_paths=matched,
            arcade_names=arcade_names,
            mame_infra_names=infra_names,
            known_bios_files=known_bios,
            crc_index=crc_index,
            arcade_crc_index=arcade_crcs,
        )

    # ── POST /api/junk-scan ───────────────────────────────────────────────────
    @router.post("/api/junk-scan")
    def post_junk_scan(ctx) -> None:
        # ponytail: síncrono como el original pre-refactor; es un walk local rápido
        folder = ctx._post_data.get("path", "").strip() or (
            str(config.library_root) if config.library_root else ""
        )
        if not folder:
            ctx._send_json({"error": "path required"})
            return
        ctx._send_json(_full_junk_scan(folder))

    # ── GET /api/library-extras (INICIO-UX-5) ─────────────────────────────────
    # El junk-scan completo parsea catálogos y recorre todo el árbol — caro
    # para cada carga de Inicio. La sección es informativa: un conteo con unos
    # minutos de retraso no importa.
    # ponytail: caché por proceso con TTL, sin invalidación; si molesta,
    # invalidar desde junk-delete / zip-route-apply.
    _extras_cache: dict[str, tuple[float, dict]] = {}
    _EXTRAS_TTL_SECONDS = 900

    @router.get("/api/library-extras")
    def get_library_extras(ctx) -> None:
        """Conteos agregados de archivos no-gaming para la pestaña Inicio:
        BIOS (carpeta bios/ + ZIPs sueltos identificados), infraestructura MAME
        (suelta y ya colocada en carpetas arcade) y basura borrable
        (categorías safe_delete del junk-scan)."""
        import time

        from rom_manager.catalog.mame_loader import load_arcade_infra_names
        from rom_manager.converters.zip_extractor import _ARCADE_FOLDER_NAMES
        from rom_manager.web.builders.folders import _ZIP_CAT_BIOS, _ZIP_CAT_INFRA

        folder = ctx._qs.get("root", [""])[0] or (
            str(config.library_root) if config.library_root else ""
        )
        empty = {"bios": 0, "mame_infra": 0, "junk_files": 0, "junk_bytes": 0}
        if not folder or not Path(folder).is_dir():
            ctx._send_json(empty)
            return
        cached = _extras_cache.get(folder)
        if cached and time.time() - cached[0] < _EXTRAS_TTL_SECONDS:
            ctx._send_json(cached[1])
            return
        bios_dir = Path(folder) / "bios"
        bios = sum(1 for f in bios_dir.rglob("*") if f.is_file()) if bios_dir.is_dir() else 0
        scan = _full_junk_scan(folder)
        mame_infra = 0
        junk_files = 0
        junk_bytes = 0
        for cat in scan.get("categories", []):
            if cat["category"] == _ZIP_CAT_BIOS:
                bios += cat["count"]
            elif cat["category"] == _ZIP_CAT_INFRA:
                mame_infra = cat["count"]
            elif cat["confidence"] == "safe_delete":
                junk_files += cat["count"]
                junk_bytes += cat["total_bytes"]
        # El junk-scan solo ve ZIPs *sueltos* (dentro de carpeta de plataforma
        # los salta): la infra ya colocada en arcade\/mame\/… se cuenta aparte
        # cruzando los stems con las bios/devices del XML de MAME.
        infra_names = load_arcade_infra_names(config.catalogs_arcade_dir)
        if infra_names:
            root_p = Path(folder)
            for dirpath, _dirs, files in os.walk(root_p):
                parts = Path(dirpath).relative_to(root_p).parts
                if not any(part.lower() in _ARCADE_FOLDER_NAMES for part in parts):
                    continue
                mame_infra += sum(
                    1 for f in files if f.lower().endswith(".zip") and f[:-4].lower() in infra_names
                )
        payload = {
            "bios": bios,
            "mame_infra": mame_infra,
            "junk_files": junk_files,
            "junk_bytes": junk_bytes,
        }
        _extras_cache[folder] = (time.time(), payload)
        ctx._send_json(payload)

    # ── POST /api/zip-route-apply ─────────────────────────────────────────────
    @router.post("/api/zip-route-apply")
    def post_zip_route_apply(ctx) -> None:
        """ZIP-ROUTE-4: colocar en un solo paso los ZIPs identificados.

        Job en background bajo el nombre "inbox" (la UI ya sabe mostrarlo):
        arcade directo a arcade\\, colecciones extraídas, el resto vía Inbox.
        """
        folder = ctx._post_data.get("path", "").strip() or (
            str(config.library_root) if config.library_root else ""
        )
        if not folder:
            ctx._send_json({"error": "path required"})
            return
        from rom_manager.web.zip_router import _run_zip_route_apply

        def run() -> None:
            _run_zip_route_apply(folder, repository, config, job_manager)

        ctx._send_json(job_manager.start("inbox", run))

    # ── POST /api/junk-delete ─────────────────────────────────────────────────
    @router.post("/api/junk-delete")
    def post_junk_delete(ctx) -> None:
        data = ctx._post_data
        paths_to_delete = data.get("paths", [])
        dry_run = bool(data.get("dry_run", True))
        deleted = failed = 0
        freed_bytes = 0
        errors: list[str] = []
        for fp in paths_to_delete:
            try:
                p = Path(fp)
                if p.is_file():
                    sz = p.stat().st_size
                    if not dry_run:
                        # AUD-3: soft-discard — nada se borra con unlink()
                        from rom_manager.utils.trash import discard_to_trash

                        discard_to_trash(p)
                    deleted += 1
                    freed_bytes += sz
            except OSError as exc:
                failed += 1
                errors.append(str(exc))
        ctx._send_json(
            {
                "deleted": deleted,
                "failed": failed,
                "freed_bytes": freed_bytes,
                "dry_run": dry_run,
                "errors": errors[:10],
            }
        )
