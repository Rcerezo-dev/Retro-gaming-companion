from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.router import Router
    from rom_manager.web.jobs.manager import JobManager
    import types


# ── Public entry point ────────────────────────────────────────────────────────

def register(
    router: "Router",
    *,
    config: "AppConfig",
    repository: "LibraryRepository",
    repo_android: "LibraryRepository",
    get_repo_fn: "Callable[[str], LibraryRepository]",
    srv_mod: "types.ModuleType",
    job_manager: "JobManager",
) -> None:
    """Register ES-DE, export, report, utility and tool routes on *router*."""

    from rom_manager.web.response_builders import (
        _json_response, _test_path, _list_drives,
        _build_library_report, _build_status,
    )
    from rom_manager.reports import build_report, to_csv, to_json as _to_json

    # ── GET /api/local-url ────────────────────────────────────────────────────
    @router.get("/api/local-url")
    def get_local_url(ctx) -> None:
        from rom_manager.web.server import _get_local_ip
        ctx._send_json({"ip": _get_local_ip(), "port": config.web_port})

    # ── GET /api/status ───────────────────────────────────────────────────────
    @router.get("/api/status")
    def get_status(ctx) -> None:
        qs = ctx._qs
        src_root = qs.get("root", [None])[0] or None
        repo = get_repo_fn(src_root) if src_root else repository
        ctx._send_json(
            _build_status(
                repo, src_root,
                project_root=config.project_root,
                repository_android=repo_android,
                library_root=config.library_root,
            )
        )

    # ── GET /api/test-path ────────────────────────────────────────────────────
    @router.get("/api/test-path")
    def get_test_path(ctx) -> None:
        path = ctx._qs.get("path", [""])[0]
        ctx._send_json(_test_path(path))

    # ── GET /api/list-drives ──────────────────────────────────────────────────
    @router.get("/api/list-drives")
    def get_list_drives(ctx) -> None:
        ctx._send_json(_list_drives())

    # ── GET /api/setup-status ─────────────────────────────────────────────────
    @router.get("/api/setup-status")
    def get_setup_status(ctx) -> None:
        status = job_manager.get_status()
        ctx._send_json({
            "setup_running":  status["setup_running"],
            "setup_progress": status.get("setup_progress"),
            "setup_result":   status.get("setup_result"),
        })

    # ── GET /api/esde-status ──────────────────────────────────────────────────
    @router.get("/api/esde-status")
    def get_esde_status(ctx) -> None:
        ctx._send_json(_handle_esde_status(config))

    # ── GET /api/copy-assets-to-esde ─────────────────────────────────────────
    @router.get("/api/copy-assets-to-esde")
    def get_copy_assets_to_esde(ctx) -> None:
        ctx._send_json(_handle_copy_assets_to_esde(config))

    # ── GET /api/disc-folders ─────────────────────────────────────────────────
    @router.get("/api/disc-folders")
    def get_disc_folders(ctx) -> None:
        ctx._send_json(_handle_disc_folders(config))

    # ── GET /api/library-report ───────────────────────────────────────────────
    @router.get("/api/library-report")
    def get_library_report(ctx) -> None:
        qs = ctx._qs
        rpt_path = qs.get("path", [None])[0] or str(config.library_root or "")
        if not rpt_path:
            ctx._send_json({"error": "path parameter required (or set library_root in config)"})
            return
        _rpt_repo = get_repo_fn(rpt_path)
        rpt = _build_library_report(rpt_path, _rpt_repo, config)
        _st = job_manager.get_status()
        rpt["retroachievements"] = _st.get("ra_check_result") or {
            "note": "Ejecuta primero la comprobación de RetroAchievements en la pestaña Tools"
        }
        rpt["chd"] = _st.get("convert_chd_result") or {
            "note": "Ejecuta primero la conversión CHD en la pestaña Tools"
        }
        ctx._send_json(rpt)

    # ── GET /api/report/html ──────────────────────────────────────────────────
    @router.get("/api/report/html")
    def get_report_html(ctx) -> None:
        qs = ctx._qs
        rpt_path = qs.get("path", [None])[0] or str(config.library_root or "")
        if not rpt_path:
            ctx._send(400, "text/plain; charset=utf-8",
                      b"path parameter required (or set library_root in config)")
            return
        from rom_manager.utils.library_report_html import generate_html_report
        _rpt_repo = get_repo_fn(rpt_path)
        rpt = _build_library_report(rpt_path, _rpt_repo, config)
        _st = job_manager.get_status()
        rpt["retroachievements"] = _st.get("ra_check_result") or {}
        rpt["chd"] = _st.get("convert_chd_result") or {}
        html = generate_html_report(rpt)
        ctx._send(200, "text/html; charset=utf-8", html.encode("utf-8"))

    # ── GET /api/report.json ──────────────────────────────────────────────────
    @router.get("/api/report.json")
    def get_report_json(ctx) -> None:
        report = build_report(repository)
        body = _to_json(report).encode()
        ctx._send(200, "application/json; charset=utf-8", body,
                  extra_headers={"Content-Disposition": 'attachment; filename="report.json"'})

    # ── GET /api/report.csv ───────────────────────────────────────────────────
    @router.get("/api/report.csv")
    def get_report_csv(ctx) -> None:
        report = build_report(repository)
        body = to_csv(report).encode()
        ctx._send(200, "text/csv; charset=utf-8", body,
                  extra_headers={"Content-Disposition": 'attachment; filename="report.csv"'})

    # ── POST /api/export-lpl ──────────────────────────────────────────────────
    @router.post("/api/export-lpl")
    def post_export_lpl(ctx) -> None:
        data = ctx._post_data
        if not config.library_root:
            ctx._send_json({"error": "library_root not configured"})
            return
        from rom_manager.utils.lpl_generator import generate_lpl_playlists
        try:
            result = generate_lpl_playlists(
                Path(config.library_root),
                repository,
                output_dir=Path(data["output_dir"]) if data.get("output_dir") else None,
            )
            ctx._send_json(result)
        except Exception as exc:
            ctx._send_json({"error": str(exc)})

    # ── POST /api/convert-chd ─────────────────────────────────────────────────
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
                    find_cue_files, convert_to_chd, parse_bins_from_cue,
                    ConversionResult, ConversionSummary,
                )
                source = Path(source_path_str).resolve()
                cue_files = find_cue_files(source)
                total = len(cue_files)
                job_manager.update_progress("convert_chd", {"current": 0, "total": total, "current_file": ""})

                summary = ConversionSummary()
                for idx, cue_path in enumerate(cue_files, 1):
                    if _cancel.is_set():
                        break
                    job_manager.update_progress("convert_chd", {"current": idx, "total": total, "current_file": cue_path.name})
                    chd_path = cue_path.with_suffix(".chd")
                    bin_paths = parse_bins_from_cue(cue_path)
                    if dry_run:
                        if chd_path.exists():
                            summary.skipped += 1
                            summary.results.append(ConversionResult(
                                cue_path=cue_path, chd_path=chd_path, bin_paths=bin_paths,
                                success=False, error="Output .chd already exists — would skip."))
                        else:
                            missing_bins = [b for b in bin_paths if not b.exists()]
                            if missing_bins:
                                summary.failed += 1
                                summary.results.append(ConversionResult(
                                    cue_path=cue_path, chd_path=chd_path, bin_paths=bin_paths,
                                    success=False,
                                    error="Bin file(s) not found: " + ", ".join(b.name for b in missing_bins)))
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
                            try:
                                cue_str = str(cue_path.resolve())
                                with repository.connect() as _dc:
                                    _dc.execute(
                                        "UPDATE games SET set_type = 'disc_auxiliary' WHERE source_path = ?",
                                        (cue_str,),
                                    )
                                    _dc.commit()
                            except Exception:
                                pass
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
                job_manager.update_progress("verify_chd", {"current": 0, "total": total, "current_file": ""})

                results = []
                ok_count = 0
                fail_count = 0
                for idx, chd_path in enumerate(chd_files, 1):
                    if _cancel.is_set():
                        break
                    job_manager.update_progress("verify_chd", {"current": idx, "total": total, "current_file": chd_path.name})
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
                job_manager.update_progress("convert_cso", {"current": 0, "total": total, "current_file": ""})

                converted = 0
                skipped = 0
                failed = 0
                results = []

                for idx, cso_path in enumerate(cso_files, 1):
                    if _cancel.is_set():
                        break
                    job_manager.update_progress("convert_cso", {"current": idx, "total": total, "current_file": cso_path.name})
                    iso_path = cso_path.with_suffix(".iso")

                    if iso_path.exists():
                        skipped += 1
                        results.append({"file": cso_path.name, "success": False,
                                         "error": "Output .iso already exists"})
                        continue

                    try:
                        r = subprocess.run(
                            [maxcso_path, "--decompress", f"--output={iso_path}", str(cso_path)],
                            capture_output=True, timeout=300,
                        )
                        if r.returncode == 0:
                            converted += 1
                            results.append({"file": cso_path.name, "success": True, "error": None})
                            if delete_source:
                                cso_path.unlink()
                        else:
                            failed += 1
                            err = (r.stderr or b"").decode(errors="replace").strip()
                            results.append({"file": cso_path.name, "success": False,
                                             "error": err or "maxcso failed with non-zero exit"})
                    except FileNotFoundError:
                        failed += 1
                        results.append({"file": cso_path.name, "success": False,
                                         "error": f"maxcso not found: {maxcso_path}"})
                    except subprocess.TimeoutExpired:
                        failed += 1
                        results.append({"file": cso_path.name, "success": False, "error": "Timeout (>300s)"})
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
                from rom_manager.converters.zip_extractor import find_zip_files, extract_zip
                from rom_manager.scanner.rom_scanner import utc_now
                source = Path(source_path_str).resolve()
                zip_files = find_zip_files(source)
                total = len(zip_files)
                job_manager.update_progress("extract_zip", {"current": 0, "total": total, "current_file": ""})
                extracted = skipped = failed = disc_sets = 0
                results = []
                for idx, zp in enumerate(zip_files, 1):
                    if _cancel.is_set():
                        break
                    try:
                        rel = str(zp.relative_to(source))
                    except ValueError:
                        rel = zp.name
                    job_manager.update_progress("extract_zip", {"current": idx, "total": total, "current_file": rel})
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
        ctx._send_json({
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
        ctx._send_json({
            "groups_ok": summary.groups_ok,
            "groups_with_issues": summary.groups_with_issues,
            "issues": [
                {"base_name": i.base_name, "issue_type": i.issue_type,
                 "detail": i.detail, "platform": i.platform}
                for i in summary.issues
            ],
        })

    # ── POST /api/health-check ────────────────────────────────────────────────
    @router.post("/api/health-check")
    def post_health_check(ctx) -> None:
        _cancel = job_manager.cancel_event("health_check")

        def run() -> None:
            job_result = None
            try:
                from rom_manager.utils.health_checker import check_library_health
                from rom_manager.scanner.rom_scanner import utc_now

                def progress_cb(current: int, total: int, filename: str) -> None:
                    job_manager.update_progress("health_check", {"current": current, "total": total, "current_file": filename})

                summary = check_library_health(repository, progress_cb=progress_cb,
                                               cancel_event=_cancel)
                job_result = {
                    "ok": summary.ok,
                    "corrupted": summary.corrupted,
                    "missing": summary.missing,
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
                from rom_manager.web.server import _write_health_schedule
                _write_health_schedule(config, ok=summary.ok,
                                       corrupted=summary.corrupted, missing=summary.missing)
                if not _cancel.is_set() and config.notify_desktop:
                    from rom_manager.utils.notifier import notify
                    if summary.corrupted or summary.missing:
                        notify(
                            "Retro Vault — Health Check",
                            f"⚠ {summary.corrupted} corruptos, {summary.missing} desaparecidos — revisa la pestaña Tools",
                        )
                    else:
                        notify("Retro Vault — Health Check",
                               f"✓ {summary.ok} ROMs verificados, sin problemas")
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
        ctx._send_json({"deleted": deleted, "failed": failed, "skipped": skipped,
                         "freed_bytes": freed_bytes})

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
                        p.unlink()
                    deleted += 1
                    freed_bytes += sz
            except OSError as exc:
                failed += 1
                errors.append(str(exc))
        ctx._send_json({"deleted": deleted, "failed": failed, "freed_bytes": freed_bytes,
                         "dry_run": dry_run, "errors": errors[:10]})

    # ── POST /api/convert-n64 ─────────────────────────────────────────────────
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
        ctx._send_json({
            "success": res.success, "source_format": res.source_format,
            "target_path": res.target_path, "error": res.error,
        })

    # ── POST /api/orphaned-saves/delete ───────────────────────────────────────
    @router.post("/api/orphaned-saves/delete")
    def post_orphaned_saves_delete(ctx) -> None:
        data = ctx._post_data
        paths = data.get("paths", [])
        if not paths:
            ctx._send_json({"error": "paths list is required"})
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
        ctx._send_json({"deleted": deleted, "failed": failed, "freed_bytes": freed_bytes})

    # ── POST /api/orphaned-saves/move ─────────────────────────────────────────
    @router.post("/api/orphaned-saves/move")
    def post_orphaned_saves_move(ctx) -> None:
        data = ctx._post_data
        save_path = data.get("save_path", "").strip()
        game_path = data.get("game_path", "").strip()
        if not save_path or not game_path:
            ctx._send_json({"error": "save_path and game_path are required"})
            return
        save_file = Path(save_path)
        game_file = Path(game_path)
        if not save_file.exists():
            ctx._send_json({"error": f"Save file not found: {save_path}"})
            return
        if not game_file.parent.exists():
            ctx._send_json({"error": f"Game directory not found: {game_file.parent}"})
            return
        target = game_file.parent / (game_file.stem + save_file.suffix)
        if target.exists():
            ctx._send_json({"error": f"Target already exists: {target.name}"})
            return
        try:
            shutil.move(str(save_file), str(target))
        except OSError as exc:
            ctx._send_json({"error": str(exc)})
            return
        ctx._send_json({"moved": str(target), "from": save_path})

    # ── POST /api/orphaned-saves/move-to-archive ──────────────────────────────
    @router.post("/api/orphaned-saves/move-to-archive")
    def post_orphaned_saves_archive(ctx) -> None:
        data = ctx._post_data
        paths = data.get("paths", [])
        library_root = data.get("library_root", "").strip()
        if not paths:
            ctx._send_json({"error": "paths list is required"})
            return
        if not library_root:
            ctx._send_json({"error": "library_root is required"})
            return

        archive_dir = Path(library_root) / "_huerfanos"
        try:
            archive_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            ctx._send_json({"error": f"Could not create _huerfanos folder: {exc}"})
            return

        moved = failed = 0
        moved_bytes = 0
        for p in paths:
            try:
                src = Path(p)
                if not src.exists():
                    failed += 1
                    continue
                size = src.stat().st_size
                target = archive_dir / src.name
                counter = 1
                stem = target.stem
                suffix = target.suffix
                while target.exists():
                    target = archive_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                shutil.move(str(src), str(target))
                moved += 1
                moved_bytes += size
            except OSError:
                failed += 1

        ctx._send_json({
            "moved": moved,
            "failed": failed,
            "moved_bytes": moved_bytes,
            "archive_dir": str(archive_dir),
        })

    # ── POST /api/doctor-move-rom ─────────────────────────────────────────────
    @router.post("/api/doctor-move-rom")
    def post_doctor_move_rom(ctx) -> None:
        data = ctx._post_data
        _src = data.get("path", "")
        _dst_dir = data.get("expected_dir", "")
        if not _src or not _dst_dir:
            ctx._send_json({"error": "path y expected_dir requeridos"})
            return
        _src_p = Path(_src)
        _dst_p = Path(_dst_dir) / _src_p.name
        if not _src_p.exists():
            ctx._send_json({"error": "Archivo no encontrado"})
        elif _dst_p.exists():
            ctx._send_json({"error": f"Ya existe en destino: {_dst_p.name}"})
        else:
            try:
                Path(_dst_dir).mkdir(parents=True, exist_ok=True)
                shutil.move(str(_src_p), str(_dst_p))
                ctx._send_json({"ok": True, "new_path": str(_dst_p)})
            except Exception as _exc:
                ctx._send_json({"error": str(_exc)})

    # ── POST /api/doctor-delete-dir ───────────────────────────────────────────
    @router.post("/api/doctor-delete-dir")
    def post_doctor_delete_dir(ctx) -> None:
        data = ctx._post_data
        _dir = data.get("path", "")
        if not _dir:
            ctx._send_json({"error": "path requerido"})
            return
        _dir_p = Path(_dir)
        if not _dir_p.exists():
            ctx._send_json({"error": "Carpeta no encontrada"})
        elif not _dir_p.is_dir():
            ctx._send_json({"error": "No es una carpeta"})
        else:
            try:
                _dir_p.rmdir()
                ctx._send_json({"ok": True})
            except Exception as _exc:
                ctx._send_json({"error": str(_exc)})

    # ── POST /api/shutdown ────────────────────────────────────────────────────
    @router.post("/api/shutdown")
    def post_shutdown(ctx) -> None:
        ctx._send_json({"ok": True})
        import threading as _threading
        _threading.Thread(
            target=srv_mod._httpd_instance.shutdown,
            daemon=True,
        ).start()

    # ── GET /api/system-status ────────────────────────────────────────────────
    @router.get("/api/system-status")
    def get_system_status(ctx) -> None:
        ctx._send_json(srv_mod._handle_system_status(config))

    # ── GET /api/detect-cloud-folder ─────────────────────────────────────────
    @router.get("/api/detect-cloud-folder")
    def get_detect_cloud_folder(ctx) -> None:
        ctx._send_json(srv_mod._handle_detect_cloud_folder())

    # ── GET /api/library-doctor ───────────────────────────────────────────────
    @router.get("/api/library-doctor")
    def get_library_doctor(ctx) -> None:
        ctx._send_json(srv_mod._handle_library_doctor(config, repository))

    # ── GET /api/retroarch-check ──────────────────────────────────────────────
    @router.get("/api/retroarch-check")
    def get_retroarch_check(ctx) -> None:
        ctx._send_json(srv_mod._handle_retroarch_check(config))

    # ── GET /api/generate-es-systems ─────────────────────────────────────────
    @router.get("/api/generate-es-systems")
    def get_generate_es_systems(ctx) -> None:
        ctx._send_json(_handle_generate_es_systems(config))

    # ── GET /api/bios-status ──────────────────────────────────────────────────
    @router.get("/api/bios-status")
    def get_bios_status(ctx) -> None:
        from rom_manager.detection.bios_checker import check_bios
        search_dirs = []
        if config.library_root:
            search_dirs.append(config.library_root)
            search_dirs.append(config.library_root / "bios")
        if config.retroarch_path:
            ra_system = Path(config.retroarch_path).parent / "system"
            search_dirs.append(ra_system)
        ctx._send_json({"bios": check_bios(search_dirs)})

    # ── GET /api/n64-scan ─────────────────────────────────────────────────────
    @router.get("/api/n64-scan")
    def get_n64_scan(ctx) -> None:
        from rom_manager.converters.n64_converter import scan_n64_roms
        path_str = ctx._qs.get("path", [None])[0] or str(config.library_root or "")
        if not path_str:
            ctx._send_json({"roms": []})
            return
        scan_dir = Path(path_str)
        if not scan_dir.exists():
            ctx._send_json({"roms": [], "error": "Carpeta no encontrada"})
            return
        ctx._send_json({"roms": scan_n64_roms(scan_dir)})


# ── Module-level helpers (also used by server.py internals) ──────────────────

def _handle_esde_status(config: "AppConfig") -> dict:
    """Detect ES-DE installation and return status + suggested gamelist paths."""
    appdata = os.environ.get("APPDATA", "")
    localappdata = os.environ.get("LOCALAPPDATA", "")
    home = os.environ.get("USERPROFILE", os.path.expanduser("~"))

    candidates: list[Path] = []
    if appdata:
        candidates.append(Path(appdata) / "ES-DE")
    if localappdata:
        candidates.append(Path(localappdata) / "ES-DE")
    candidates += [
        Path(home) / ".emulationstation",
        Path(home) / "ES-DE",
    ]
    for drive in ("C", "D"):
        candidates += [
            Path(f"{drive}:\\Program Files\\ES-DE"),
            Path(f"{drive}:\\ES-DE"),
        ]

    found_dir: str = ""
    roms_path: str = ""
    for c in candidates:
        if c.exists():
            found_dir = str(c)
            settings = c / "settings" / "es_settings.xml"
            if not settings.exists():
                settings = c / "es_settings.xml"
            if settings.exists():
                try:
                    import re as _re
                    text = settings.read_text(encoding="utf-8", errors="replace")
                    m = _re.search(r'name="ROMsDirectory"[^>]*value="([^"]+)"', text)
                    if m:
                        roms_path = m.group(1)
                except OSError:
                    pass
            break

    gamelists_dir = str(Path(found_dir) / "gamelists") if found_dir else ""
    return {
        "installed": bool(found_dir),
        "install_dir": found_dir,
        "roms_path": roms_path,
        "gamelists_dir": gamelists_dir,
    }


def _handle_copy_assets_to_esde(config: "AppConfig") -> dict:
    """Copy scraped box art from library_root/{platform}/media/images/ to ES-DE gamelists dir."""
    esde = _handle_esde_status(config)
    if not esde.get("gamelists_dir"):
        return {"error": "ES-DE no detectado"}
    if not config.library_root:
        return {"error": "library_root no configurado"}
    gamelists_dir = Path(esde["gamelists_dir"])
    root = Path(config.library_root)
    copied = 0
    skipped = 0
    errors: list[str] = []
    for platform_dir in root.iterdir():
        if not platform_dir.is_dir():
            continue
        img_src = platform_dir / "media" / "images"
        if not img_src.exists():
            continue
        img_dst = gamelists_dir / platform_dir.name / "images"
        img_dst.mkdir(parents=True, exist_ok=True)
        for img in img_src.iterdir():
            if img.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                dst = img_dst / img.name
                try:
                    shutil.copy2(str(img), str(dst))
                    copied += 1
                except Exception as exc:
                    errors.append(str(exc))
                    skipped += 1
    return {"copied": copied, "skipped": skipped, "errors": errors[:5]}


# Keywords that identify disc-based platforms (multi-disc games common)
_DISC_PLATFORM_KEYWORDS = {
    "ps1", "psx", "playstation", "ps2", "psp",
    "saturn", "dreamcast",
    "segacd", "sega-cd", "mega-cd", "megacd",
    "pcenginecd", "pc-engine-cd", "turbografx-cd", "turbografxcd",
    "neogeocd", "neo-geo-cd",
    "3do", "cd-i", "cdi",
}


def _handle_generate_es_systems(config: "AppConfig") -> dict:
    """Generate custom_systems/es_systems.xml based on detected RetroArch cores."""
    import os
    from rom_manager.esde.systems_generator import generate_es_systems_xml

    # Locate the cores/ directory from the configured RetroArch path
    ra_exe = (config.retroarch_path or "").strip()
    if not ra_exe:
        return {"ok": False, "error": "RetroArch no está configurado en Settings (launchers.retroarch)."}

    cores_dir = Path(ra_exe).parent / "cores"

    # Locate the ES-DE custom_systems dir
    esde_info = _handle_esde_status(config)
    if not esde_info.get("installed"):
        return {"ok": False, "error": "ES-DE no detectado. Instala ES-DE y vuelve a intentarlo."}

    output_path = Path(esde_info["install_dir"]) / "custom_systems" / "es_systems.xml"

    result = generate_es_systems_xml(cores_dir, output_path)

    return {
        "ok": result.written and not result.error,
        "error": result.error,
        "output_path": result.output_path,
        "written": result.written,
        "generated": [
            {"name": s.name, "fullname": s.fullname, "core_dll": s.core_dll, "core_label": s.core_label}
            for s in result.generated_systems
        ],
        "missing": result.missing_systems,
        "cores_dir": str(cores_dir),
    }


def _handle_disc_folders(config: "AppConfig") -> dict:
    """Return subfolders of library_root whose name matches known disc-based platforms."""
    root = config.library_root
    if not root or not root.exists():
        return {"folders": [], "library_root": str(root or "")}

    folders: list[str] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        name_lower = entry.name.lower()
        if any(kw in name_lower for kw in _DISC_PLATFORM_KEYWORDS):
            folders.append(str(entry))

    return {"folders": folders, "library_root": str(root)}
