"""Business logic for duplicate-ROM deletion (ARC-SVC-1).

Pure functions decoupled from the HTTP layer: they take a repository plus plain
inputs and return result dicts ready to serialize. No web ``ctx`` here, so they
can be unit-tested and reused outside the web server.
"""

from __future__ import annotations

import logging
import os
import stat
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.database.repository import LibraryRepository

_log = logging.getLogger(__name__)


def _force_remove(path: Path) -> None:
    """Remove a file, clearing the read-only attribute first if needed (WinError 5)."""
    try:
        os.remove(str(path))
    except PermissionError:
        # Clear read-only flag and retry (common on drives formatted by consoles)
        os.chmod(str(path), stat.S_IWRITE)
        os.remove(str(path))


def delete_duplicate(
    repository: LibraryRepository,
    *,
    game_id,
    source_path: str = "",
) -> dict:
    """Delete one duplicate ROM file and its DB record.

    Returns a result dict ready to serialize: ``{"deleted": path}`` on success,
    or ``{"error": msg}`` on failure.
    """
    if not game_id:
        return {"error": "game_id es obligatorio"}
    source_path = (source_path or "").strip()
    if not source_path:
        # Derive from DB so callers don't need to pass it
        try:
            with repository.connect() as _c:
                row = _c.execute(
                    "SELECT source_path FROM games WHERE id = ?", (int(game_id),)
                ).fetchone()
            if not row or not row["source_path"]:
                return {"error": f"Juego {game_id} no encontrado en la base de datos"}
            source_path = row["source_path"]
        except Exception as exc:
            return {"error": f"Error consultando BD: {type(exc).__name__}: {exc}"}
    p = Path(source_path)
    if p.exists():
        try:
            _force_remove(p)
        except Exception as exc:
            return {"error": f"No se pudo eliminar el archivo: {type(exc).__name__}: {exc}"}
    try:
        repository.delete_game(int(game_id))
    except Exception as exc:
        return {"error": f"Archivo eliminado pero error en BD: {type(exc).__name__}: {exc}"}
    return {"deleted": source_path}


def delete_all_duplicates(repository: LibraryRepository) -> dict:
    """Delete every non-canonical duplicate (all but the first entry per group).

    Returns a result dict ready to serialize with deleted/skipped/failed counts,
    freed bytes, a human summary, and per-file diagnostics.
    """
    groups = repository.get_duplicate_groups()
    deleted = 0
    skipped = 0  # Files that don't exist (already deleted or moved)
    failed = 0  # Files that exist but couldn't be deleted (perms, device unmounted, etc.)
    freed_bytes = 0
    errors: list[str] = []
    diagnostics: list[dict] = []  # Detailed log of each attempt

    for group in groups:
        for entry in group.entries[1:]:
            p = Path(entry.source_path)
            diag = {
                "path": str(p),
                "exists": p.exists(),
                "deleted_file": False,
                "deleted_db": False,
            }

            if not p.exists():
                _log.info(f"Skipping missing file (file gone, cleaning DB): {p}")
                try:
                    repository.delete_game(entry.id)
                    skipped += 1  # Count as skipped (file already gone, just cleaned up DB)
                    diag["deleted_db"] = True
                except Exception as exc:
                    failed += 1
                    diag["db_error"] = str(exc)
                    _log.warning("Could not remove DB entry for missing file %s: %s", p, exc)
                    if len(errors) < 20:
                        errors.append(f"{p.name}: DB error — {type(exc).__name__}: {exc}")
                diagnostics.append(diag)
                continue

            try:
                _log.info(f"Deleting file: {p}")
                _force_remove(p)
                diag["deleted_file"] = True
                _log.info(f"File deleted successfully: {p}")
            except Exception as exc:
                failed += 1
                diag["file_error"] = str(exc)
                _log.warning("Could not delete duplicate file %s: %s", p, exc)
                if len(errors) < 20:
                    errors.append(
                        f"{p.name}: no se pudo eliminar el archivo — {type(exc).__name__}: {exc}"
                    )
                diagnostics.append(diag)
                continue

            try:
                repository.delete_game(entry.id)
                deleted += 1
                freed_bytes += entry.size_bytes
                diag["deleted_db"] = True
                _log.info(f"DB record deleted for: {p}")
            except Exception as exc:
                failed += 1
                diag["db_error"] = str(exc)
                _log.warning("File deleted but DB update failed for %s: %s", p, exc)
                if len(errors) < 20:
                    errors.append(
                        f"{p.name}: archivo eliminado pero error en BD — {type(exc).__name__}: {exc}"
                    )

            diagnostics.append(diag)

    return {
        "deleted": deleted,
        "skipped": skipped,
        "failed": failed,
        "freed_bytes": freed_bytes,
        "errors": errors,
        "summary": f"{deleted} eliminados, {skipped} omitidos (no existen), {failed} errores",
        "diagnostics": diagnostics[:10],  # Return first 10 for debugging
    }
