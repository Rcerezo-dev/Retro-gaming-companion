"""Patch manager — list and apply IPS/IPS32 patches (NEW-1).

Routes:
  GET  /api/patches/list    — patches in inbox_path + retroarch_path parent
  POST /api/patches/apply   — apply IPS patch to a ROM
"""
from __future__ import annotations

from datetime import UTC, datetime  # noqa: TC003
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.router import Router

_PATCH_EXTS = frozenset({".ips", ".ips32", ".bps", ".ups"})


def register(router: Router, *, config: AppConfig, repository: LibraryRepository) -> None:

    @router.get("/api/patches/list")
    def get_patches_list(ctx) -> None:
        """Scan known directories for patch files."""
        search_dirs: list[Path] = []
        if config.inbox.path:
            search_dirs.append(Path(config.inbox.path))
        if config.retroarch_path:
            search_dirs.append(Path(config.retroarch_path).parent / "patches")
        patches = []
        seen: set[str] = set()
        for d in search_dirs:
            if not d.is_dir():
                continue
            for f in sorted(d.rglob("*")):
                if f.suffix.lower() not in _PATCH_EXTS:
                    continue
                key = str(f)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    stat = f.stat()
                except OSError:
                    continue
                patches.append({
                    "filename": f.name,
                    "path": str(f),
                    "ext": f.suffix.lower(),
                    "size_bytes": stat.st_size,
                })
        ctx._send_json({"patches": patches})

    @router.post("/api/patches/apply")
    def post_apply(ctx) -> None:
        """Apply an IPS/IPS32 patch to a ROM file."""
        from rom_manager.patch.ips_applier import PatchError, apply_ips

        data = ctx._post_data
        patch_path_s = (data.get("patch_path") or "").strip()
        rom_path_s   = (data.get("rom_path")   or "").strip()

        if not patch_path_s or not rom_path_s:
            ctx._send_json({"error": "Faltan patch_path y/o rom_path"})
            return

        patch_path = Path(patch_path_s)
        rom_path   = Path(rom_path_s)

        if not patch_path.exists():
            ctx._send_json({"error": f"Patch no encontrado: {patch_path.name}"})
            return
        if not rom_path.exists():
            ctx._send_json({"error": f"ROM no encontrada: {rom_path.name}"})
            return
        if patch_path.suffix.lower() not in {".ips", ".ips32"}:
            ctx._send_json({"error": f"Formato no soportado aún: {patch_path.suffix} (solo IPS/IPS32)"})
            return

        output_path = rom_path.parent / (rom_path.stem + "_patched" + rom_path.suffix)

        try:
            records = apply_ips(rom_path, patch_path, output_path)
        except PatchError as exc:
            ctx._send_json({"error": str(exc)})
            return
        except OSError as exc:
            ctx._send_json({"error": f"Error de lectura/escritura: {exc}"})
            return

        # Log the operation (non-fatal)
        ts = datetime.now(UTC).isoformat()
        try:
            with repository.connect() as conn:
                conn.execute(
                    "INSERT INTO file_operations "
                    "(game_id, operation_type, source_path, target_path, result, message, created_at) "
                    "VALUES (NULL, 'patch_apply', ?, ?, 'ok', ?, ?)",
                    (str(rom_path), str(output_path), f"IPS: {patch_path.name} → {records} registros", ts),
                )
                conn.commit()
        except Exception:
            pass

        ctx._send_json({
            "ok": True,
            "output": str(output_path),
            "records": records,
            "output_name": output_path.name,
        })
