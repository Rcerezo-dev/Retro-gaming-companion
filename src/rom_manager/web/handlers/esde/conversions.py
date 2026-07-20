"""ES-DE conversion / extraction routes (CHD, CSO, N64, ZIP, m3u, multidisc).

Registered onto the shared router by ``register_conversions``; the orchestrator
in ``esde/__init__.py`` calls it. Each handler runs its work as a background job
via the JobManager.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router

_logger = logging.getLogger(__name__)


def register_conversions(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    job_manager: JobManager,
) -> None:
    """Register CHD/CSO/N64 conversion, ZIP extraction, m3u and multidisc routes."""

    @router.post("/api/convert-chd")
    def post_convert_chd(ctx) -> None:
        data = ctx._post_data
        source_path_str = data.get("source_path", "").strip()
        if not source_path_str:
            ctx._send_json({"error": "source_path is required"})
            return
        dry_run = data.get("dry_run", True)
        delete_source = data.get("delete_source", False)

        _cancel = job_manager.cancel_event("convert_chd")

        def run() -> None:
            job_result = None
            try:
                from rom_manager.converters.chd_converter import (
                    ConversionResult,
                    ConversionSummary,
                    convert_to_chd,
                    find_cue_files,
                    parse_bins_from_cue,
                )

                source = Path(source_path_str).resolve()
                cue_files = find_cue_files(source)
                total = len(cue_files)
                job_manager.update_progress(
                    "convert_chd", {"current": 0, "total": total, "current_file": ""}
                )

                summary = ConversionSummary()
                for idx, cue_path in enumerate(cue_files, 1):
                    if _cancel.is_set():
                        break
                    job_manager.update_progress(
                        "convert_chd",
                        {"current": idx, "total": total, "current_file": cue_path.name},
                    )
                    chd_path = cue_path.with_suffix(".chd")
                    bin_paths = parse_bins_from_cue(cue_path)
                    if dry_run:
                        if chd_path.exists():
                            summary.skipped += 1
                            summary.results.append(
                                ConversionResult(
                                    cue_path=cue_path,
                                    chd_path=chd_path,
                                    bin_paths=bin_paths,
                                    success=False,
                                    error="Output .chd already exists — would skip.",
                                )
                            )
                        else:
                            missing_bins = [b for b in bin_paths if not b.exists()]
                            if missing_bins:
                                summary.failed += 1
                                summary.results.append(
                                    ConversionResult(
                                        cue_path=cue_path,
                                        chd_path=chd_path,
                                        bin_paths=bin_paths,
                                        success=False,
                                        error="Bin file(s) not found: "
                                        + ", ".join(b.name for b in missing_bins),
                                    )
                                )
                            else:
                                summary.converted += 1
                                summary.results.append(
                                    ConversionResult(
                                        cue_path=cue_path,
                                        chd_path=chd_path,
                                        bin_paths=bin_paths,
                                        success=True,
                                    )
                                )
                    else:
                        result = convert_to_chd(
                            cue_path, chdman=config.chdman, delete_source=delete_source
                        )
                        summary.results.append(result)
                        if result.success:
                            summary.converted += 1
                            try:
                                cue_str = str(cue_path.resolve())
                                with repository.connect() as _dc:
                                    _dc.execute(
                                        "UPDATE games SET set_type = 'disc_auxiliary' WHERE source_path = ?",
                                        (cue_str,),
                                    )
                                    _dc.commit()
                            except Exception:
                                _logger.warning(
                                    "No se pudo marcar set_type tras conversión CHD", exc_info=True
                                )
                        elif result.error and "already exists" in result.error:
                            summary.skipped += 1
                        else:
                            summary.failed += 1

                job_result = {
                    "dry_run": dry_run,
                    "converted": summary.converted,
                    "skipped": summary.skipped,
                    "failed": summary.failed,
                    "cancelled": _cancel.is_set(),
                    "results": [
                        {
                            "cue": r.cue_path.name,
                            "chd": r.chd_path.name,
                            "success": r.success,
                            "error": r.error or "",
                            "bin_count": len(r.bin_paths),
                        }
                        for r in summary.results
                    ],
                }
            except Exception as exc:
                job_result = {"error": str(exc)}
            finally:
                job_manager.finish("convert_chd", job_result)

        ctx._send_json({**job_manager.start("convert_chd", run), "dry_run": dry_run})

    # ── POST /api/verify-chd (P6) ────────────────────────────────────────────
    @router.post("/api/verify-chd")
    def post_verify_chd(ctx) -> None:
        data = ctx._post_data
        source_path_str = (data.get("source_path") or "").strip()
        if not source_path_str:
            ctx._send_json({"error": "source_path is required"})
            return

        _cancel = job_manager.cancel_event("verify_chd")

        def run() -> None:
            job_result = None
            try:
                from rom_manager.converters.chd_converter import find_chd_files, verify_chd

                source = Path(source_path_str).resolve()
                chd_files = find_chd_files(source)
                total = len(chd_files)
                job_manager.update_progress(
                    "verify_chd", {"current": 0, "total": total, "current_file": ""}
                )

                results = []
                ok_count = 0
                fail_count = 0
                for idx, chd_path in enumerate(chd_files, 1):
                    if _cancel.is_set():
                        break
                    job_manager.update_progress(
                        "verify_chd",
                        {"current": idx, "total": total, "current_file": chd_path.name},
                    )
                    r = verify_chd(chd_path, chdman=str(config.chdman))
                    results.append({"file": chd_path.name, "ok": r.ok, "error": r.error or ""})
                    if r.ok:
                        ok_count += 1
                    else:
                        fail_count += 1

                job_result = {
                    "total": total,
                    "ok": ok_count,
                    "failed": fail_count,
                    "cancelled": _cancel.is_set(),
                    "results": results,
                }
            except Exception as exc:
                job_result = {"error": str(exc)}
            finally:
                job_manager.finish("verify_chd", job_result)

        ctx._send_json(job_manager.start("verify_chd", run))

    # ── POST /api/convert-cso ─────────────────────────────────────────────────
    @router.post("/api/convert-cso")
    def post_convert_cso(ctx) -> None:
        data = ctx._post_data
        source_path_str = data.get("source_path", "").strip()
        if not source_path_str:
            ctx._send_json({"error": "source_path is required"})
            return
        delete_source = data.get("delete_source", False)

        _cancel = job_manager.cancel_event("convert_cso")

        def run() -> None:
            import subprocess

            job_result = None
            try:
                source = Path(source_path_str).resolve()
                maxcso_path = str(config.project_root / "tools" / "maxcso.exe")

                cso_files = list(source.rglob("*.cso")) + list(source.rglob("*.zso"))

                arcade_platforms = {"arcade", "fbneo", "mame", "neogeo"}

                def _is_arcade(p: Path) -> bool:
                    return any(plat in str(p).lower() for plat in arcade_platforms)

                cso_files = [c for c in cso_files if not _is_arcade(c)]
                total = len(cso_files)
                job_manager.update_progress(
                    "convert_cso", {"current": 0, "total": total, "current_file": ""}
                )

                converted = 0
                skipped = 0
                failed = 0
                results = []

                for idx, cso_path in enumerate(cso_files, 1):
                    if _cancel.is_set():
                        break
                    job_manager.update_progress(
                        "convert_cso",
                        {"current": idx, "total": total, "current_file": cso_path.name},
                    )
                    iso_path = cso_path.with_suffix(".iso")

                    if iso_path.exists():
                        skipped += 1
                        results.append(
                            {
                                "file": cso_path.name,
                                "success": False,
                                "error": "Output .iso already exists",
                            }
                        )
                        continue

                    try:
                        r = subprocess.run(
                            [maxcso_path, "--decompress", f"--output={iso_path}", str(cso_path)],
                            capture_output=True,
                            timeout=300,
                        )
                        if r.returncode == 0:
                            converted += 1
                            results.append({"file": cso_path.name, "success": True, "error": None})
                            if delete_source:
                                cso_path.unlink()
                        else:
                            failed += 1
                            err = (r.stderr or b"").decode(errors="replace").strip()
                            results.append(
                                {
                                    "file": cso_path.name,
                                    "success": False,
                                    "error": err or "maxcso failed with non-zero exit",
                                }
                            )
                    except FileNotFoundError:
                        failed += 1
                        results.append(
                            {
                                "file": cso_path.name,
                                "success": False,
                                "error": f"maxcso not found: {maxcso_path}",
                            }
                        )
                    except subprocess.TimeoutExpired:
                        failed += 1
                        results.append(
                            {"file": cso_path.name, "success": False, "error": "Timeout (>300s)"}
                        )
                    except Exception as e:
                        failed += 1
                        results.append({"file": cso_path.name, "success": False, "error": str(e)})

                job_result = {
                    "converted": converted,
                    "skipped": skipped,
                    "failed": failed,
                    "cancelled": _cancel.is_set(),
                    "results": results,
                }
            except Exception as exc:
                job_result = {"error": str(exc)}
            finally:
                job_manager.finish("convert_cso", job_result)

        ctx._send_json(job_manager.start("convert_cso", run))

    # ── POST /api/extract-zip ─────────────────────────────────────────────────
    @router.post("/api/extract-zip")
    def post_extract_zip(ctx) -> None:
        data = ctx._post_data
        source_path_str = data.get("source_path", "").strip()
        if not source_path_str:
            ctx._send_json({"error": "source_path is required"})
            return
        dry_run = bool(data.get("dry_run", True))
        delete_source = bool(data.get("delete_source", False))

        _cancel = job_manager.cancel_event("extract_zip")

        def run() -> None:
            job_result = None
            try:
                from rom_manager.converters.zip_extractor import extract_zip, find_zip_files
                from rom_manager.scanner.rom_scanner import utc_now

                source = Path(source_path_str).resolve()
                zip_files = find_zip_files(source)
                total = len(zip_files)
                job_manager.update_progress(
                    "extract_zip", {"current": 0, "total": total, "current_file": ""}
                )
                extracted = skipped = failed = disc_sets = 0
                results = []
                for idx, zp in enumerate(zip_files, 1):
                    if _cancel.is_set():
                        break
                    try:
                        rel = str(zp.relative_to(source))
                    except ValueError:
                        rel = zp.name
                    job_manager.update_progress(
                        "extract_zip", {"current": idx, "total": total, "current_file": rel}
                    )
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
                    results.append(
                        {
                            "zip": rel,
                            "success": r.success,
                            "skipped_reason": r.skipped_reason,
                            "is_disc_set": r.is_disc_set,
                            "error": r.error,
                            "extracted": [f.name for f in r.extracted_files],
                        }
                    )
                job_result = {
                    "dry_run": dry_run,
                    "extracted": extracted,
                    "skipped": skipped,
                    "failed": failed,
                    "disc_sets": disc_sets,
                    "cancelled": _cancel.is_set(),
                    "results": results,
                    "result_ts": utc_now(),
                }
            except Exception as exc:
                job_result = {"error": str(exc)}
            finally:
                job_manager.finish("extract_zip", job_result)

        ctx._send_json({**job_manager.start("extract_zip", run), "dry_run": dry_run})

    # ── POST /api/generate-m3u ────────────────────────────────────────────────
    @router.post("/api/generate-m3u")
    def post_generate_m3u(ctx) -> None:
        data = ctx._post_data
        source_path_str = data.get("source_path", "").strip()
        if not source_path_str:
            ctx._send_json({"error": "source_path is required"})
            return
        dry_run = bool(data.get("dry_run", True))
        from rom_manager.utils.m3u_generator import generate_m3u_playlists

        source = Path(source_path_str).resolve()
        summary = generate_m3u_playlists(source, dry_run=dry_run)
        ctx._send_json(
            {
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
            }
        )

    # ── POST /api/verify-multidisc ────────────────────────────────────────────
    @router.post("/api/verify-multidisc")
    def post_verify_multidisc(ctx) -> None:
        data = ctx._post_data
        source_path_str = data.get("source_path", "").strip()
        if not source_path_str:
            ctx._send_json({"error": "source_path is required"})
            return
        from rom_manager.utils.multidisc_verifier import verify_multidisc

        source = Path(source_path_str).resolve()
        summary = verify_multidisc(source, repository)
        ctx._send_json(
            {
                "groups_ok": summary.groups_ok,
                "groups_with_issues": summary.groups_with_issues,
                "issues": [
                    {
                        "base_name": i.base_name,
                        "issue_type": i.issue_type,
                        "detail": i.detail,
                        "platform": i.platform,
                    }
                    for i in summary.issues
                ],
            }
        )

    # ── POST /api/folder-analysis ─────────────────────────────────────────────
    @router.post("/api/folder-analysis")
    def post_folder_analysis(ctx) -> None:
        data = ctx._post_data
        source_path_str = (data.get("source_path") or "").strip()
        if not source_path_str:
            ctx._send_json({"error": "source_path is required"})
            return

        source = Path(source_path_str)
        if not source.is_dir():
            ctx._send_json({"error": "Carpeta no encontrada"})
            return

        from collections import Counter

        from rom_manager.converters.chd_converter import find_cue_files
        from rom_manager.converters.n64_converter import scan_n64_roms
        from rom_manager.detection.cue_validator import validate_cue

        ext_counter: Counter[str] = Counter()
        for f in source.rglob("*"):
            if f.is_file():
                ext_counter[f.suffix.lower() or "(sin extensión)"] += 1

        psx_incomplete = []
        for cue_path in find_cue_files(source):
            errors = validate_cue(cue_path)
            if errors:
                psx_incomplete.append({"cue": cue_path.name, "errors": errors})

        n64_pending = [
            {"filename": r["filename"], "format": r["format"]}
            for r in scan_n64_roms(source)
            if r["needs_conversion"]
        ]

        cso_count = len(list(source.rglob("*.cso"))) + len(list(source.rglob("*.zso")))
        zip_count = len(list(source.rglob("*.zip")))

        ctx._send_json(
            {
                "extensions": [
                    {"ext": ext, "count": count}
                    for ext, count in sorted(ext_counter.items(), key=lambda kv: -kv[1])
                ],
                "psx_incomplete": psx_incomplete,
                "n64_pending": n64_pending,
                "cso_count": cso_count,
                "zip_count": zip_count,
            }
        )

    # ── POST /api/health-check ────────────────────────────────────────────────
    @router.post("/api/convert-n64")
    def post_convert_n64(ctx) -> None:
        data = ctx._post_data
        src = data.get("source_path", "").strip()
        dst = data.get("target_path", "").strip() or None
        if not src:
            ctx._send_json({"error": "source_path required"})
            return
        from rom_manager.converters.n64_converter import convert_to_z64

        res = convert_to_z64(Path(src), Path(dst) if dst else None)
        ctx._send_json(
            {
                "success": res.success,
                "source_format": res.source_format,
                "target_path": res.target_path,
                "error": res.error,
            }
        )

    # ── POST /api/orphaned-saves/delete ───────────────────────────────────────
