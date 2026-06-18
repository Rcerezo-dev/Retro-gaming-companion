from __future__ import annotations

import logging
import os
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import rom_manager.web.state as _state

if TYPE_CHECKING:
    import types

    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router


_logger = logging.getLogger(__name__)


# ── Public entry point ────────────────────────────────────────────────────────


def register(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    repo_android: LibraryRepository,
    get_repo_fn: Callable[[str], LibraryRepository],
    srv_mod: types.ModuleType,
    job_manager: JobManager,
) -> None:
    """Register ES-DE, export, report, utility and tool routes on *router*."""

    from rom_manager.web.builders.common import _list_drives, _test_path
    from rom_manager.web.builders.library import _build_status
    from rom_manager.web.handlers.esde.conversions import register_conversions
    from rom_manager.web.handlers.esde.maintenance import register_maintenance
    from rom_manager.web.handlers.esde.reports import register_reports
    from rom_manager.web.handlers.system import (
        _get_local_ip,
        _handle_detect_cloud_folder,
        _handle_library_doctor,
        _handle_retroarch_check,
        _handle_system_status,
    )

    # ── GET /api/local-url ────────────────────────────────────────────────────
    @router.get("/api/local-url")
    def get_local_url(ctx) -> None:
        ctx._send_json({"ip": _get_local_ip(), "port": config.web_port})

    # ── GET /api/status ───────────────────────────────────────────────────────
    @router.get("/api/status")
    def get_status(ctx) -> None:
        qs = ctx._qs
        src_root = qs.get("root", [None])[0] or None
        repo = get_repo_fn(src_root) if src_root else repository
        ctx._send_json(
            _build_status(
                repo,
                src_root,
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
        ctx._send_json(
            {
                "setup_running": status["setup_running"],
                "setup_progress": status.get("setup_progress"),
                "setup_result": status.get("setup_result"),
            }
        )

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

    # ── Library report + export routes (html/json/csv/lpl) ───────────────────
    register_reports(
        router,
        config=config,
        repository=repository,
        get_repo_fn=get_repo_fn,
        job_manager=job_manager,
    )

    # ── Conversion / extraction routes (CHD, CSO, N64, ZIP, m3u, multidisc) ───
    register_conversions(router, config=config, repository=repository, job_manager=job_manager)

    # ── Maintenance routes (health check, zip/cue+bin cleanup, junk delete) ───
    register_maintenance(router, config=config, repository=repository, job_manager=job_manager)

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

        ctx._send_json(
            {
                "moved": moved,
                "failed": failed,
                "moved_bytes": moved_bytes,
                "archive_dir": str(archive_dir),
            }
        )

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
            target=_state._httpd_instance.shutdown,
            daemon=True,
        ).start()

    # ── GET /api/system-status ────────────────────────────────────────────────
    @router.get("/api/system-status")
    def get_system_status(ctx) -> None:
        ctx._send_json(_handle_system_status(config))

    # ── GET /api/detect-cloud-folder ─────────────────────────────────────────
    @router.get("/api/detect-cloud-folder")
    def get_detect_cloud_folder(ctx) -> None:
        ctx._send_json(_handle_detect_cloud_folder())

    # ── GET /api/library-doctor ───────────────────────────────────────────────
    @router.get("/api/library-doctor")
    def get_library_doctor(ctx) -> None:
        ctx._send_json(_handle_library_doctor(config, repository))

    # ── GET /api/retroarch-check ──────────────────────────────────────────────
    @router.get("/api/retroarch-check")
    def get_retroarch_check(ctx) -> None:
        ctx._send_json(_handle_retroarch_check(config))

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


def _handle_esde_status(config: AppConfig) -> dict:
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


def _handle_copy_assets_to_esde(config: AppConfig) -> dict:
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
    "ps1",
    "psx",
    "playstation",
    "ps2",
    "psp",
    "saturn",
    "dreamcast",
    "segacd",
    "sega-cd",
    "mega-cd",
    "megacd",
    "pcenginecd",
    "pc-engine-cd",
    "turbografx-cd",
    "turbografxcd",
    "neogeocd",
    "neo-geo-cd",
    "3do",
    "cd-i",
    "cdi",
}


def _handle_generate_es_systems(config: AppConfig) -> dict:
    """Generate custom_systems/es_systems.xml based on detected RetroArch cores."""
    from rom_manager.esde.systems_generator import generate_es_systems_xml

    # Locate the cores/ directory from the configured RetroArch path
    ra_exe = (config.retroarch_path or "").strip()
    if not ra_exe:
        return {
            "ok": False,
            "error": "RetroArch no está configurado en Settings (launchers.retroarch).",
        }

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
            {
                "name": s.name,
                "fullname": s.fullname,
                "core_dll": s.core_dll,
                "core_label": s.core_label,
            }
            for s in result.generated_systems
        ],
        "missing": result.missing_systems,
        "cores_dir": str(cores_dir),
    }


def _handle_disc_folders(config: AppConfig) -> dict:
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
