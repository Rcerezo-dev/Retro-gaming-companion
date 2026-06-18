"""ES-DE "library doctor" routes: orphaned-save handling and on-disk fixes.

Registered onto the shared router by ``register_doctor``; the orchestrator in
``esde/__init__.py`` calls it. Covers delete/move/archive of orphaned saves,
the doctor move-rom / delete-dir fixes and the library-doctor report.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.router import Router

_logger = logging.getLogger(__name__)


def register_doctor(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
) -> None:
    """Register orphaned-saves, doctor-move/delete and library-doctor routes."""

    from rom_manager.web.handlers.system import _handle_library_doctor

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

    # ── GET /api/library-doctor ───────────────────────────────────────────────
    @router.get("/api/library-doctor")
    def get_library_doctor(ctx) -> None:
        ctx._send_json(_handle_library_doctor(config, repository))
