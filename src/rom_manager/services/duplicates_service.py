"""Business logic for duplicate-ROM deletion (ARC-SVC-1).

Pure functions decoupled from the HTTP layer: they take a repository plus plain
inputs and return result dicts ready to serialize. No web ``ctx`` here, so they
can be unit-tested and reused outside the web server.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

# AUD-3: los duplicados ya no se eliminan con os.remove — van a _descartados/
from rom_manager.utils.paths import is_device_path
from rom_manager.utils.trash import discard_to_trash

if TYPE_CHECKING:
    from rom_manager.database.repository import LibraryRepository

_log = logging.getLogger(__name__)


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
            discard_to_trash(p)
        except Exception as exc:
            return {"error": f"No se pudo mover a _descartados/: {type(exc).__name__}: {exc}"}
    elif is_device_path(source_path):
        # TABS-FIX-1: ruta de consola (ADB) — Path.exists() siempre da False
        # en Windows aunque el archivo siga vivo en el dispositivo. No borrar
        # la fila ni reportar éxito silencioso.
        return {
            "error": (
                "Ruta de consola — conecta el dispositivo para verificar si el archivo "
                "sigue ahí; no se ha tocado la fila de la base de datos"
            )
        }
    try:
        repository.delete_game(int(game_id))
    except Exception as exc:
        return {"error": f"Archivo eliminado pero error en BD: {type(exc).__name__}: {exc}"}
    return {"deleted": source_path}


def delete_all_duplicates_multi(repositories: list[LibraryRepository], platform: str = "") -> dict:
    """Run :func:`delete_all_duplicates` over several repositories and merge the results.

    Used by "Sistema completo" mode, where the duplicates view shows both the PC
    and the Android DB: deleting only against the PC repo would purge files the
    user never saw confirmed (DEVSEL-FIX-1).
    """
    merged = {
        "deleted": 0,
        "skipped": 0,
        "failed": 0,
        "unreachable": 0,
        "freed_bytes": 0,
        "errors": [],
        "diagnostics": [],
    }
    for repo in repositories:
        result = delete_all_duplicates(repo, platform=platform)
        for key in ("deleted", "skipped", "failed", "unreachable", "freed_bytes"):
            merged[key] += result[key]
        merged["errors"] = (merged["errors"] + result["errors"])[:20]
        merged["diagnostics"] = (merged["diagnostics"] + result["diagnostics"])[:10]
    merged["summary"] = (
        f"{merged['deleted']} eliminados, {merged['skipped']} omitidos (no existen), "
        f"{merged['failed']} errores"
    )
    if merged["unreachable"]:
        merged["summary"] += (
            f", {merged['unreachable']} en el dispositivo (conecta la consola para revisarlos)"
        )
    return merged


def delete_all_duplicates(repository: LibraryRepository, platform: str = "") -> dict:
    """Delete every non-canonical duplicate (all but the first entry per group).

    If *platform* is given, only groups of that platform are touched — so the
    count the user confirmed in a filtered view matches what runs
    (DUPLICADOS-UX-1).

    Returns a result dict ready to serialize with deleted/skipped/failed counts,
    freed bytes, a human summary, and per-file diagnostics.
    """
    groups = repository.get_duplicate_groups()
    if platform:
        # Mismo criterio que la UI: la plataforma del grupo es la de su primera entrada
        groups = [g for g in groups if (g.entries[0].platform or "") == platform]
    deleted = 0
    skipped = 0  # Files that don't exist (already deleted or moved)
    failed = 0  # Files that exist but couldn't be deleted (perms, device unmounted, etc.)
    unreachable = 0  # Device paths (ADB) — can't verify from Windows, DB row untouched
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
                # TABS-FIX-1: una ruta de consola (ADB) nunca "existe" para
                # Path en Windows aunque el archivo siga vivo — no limpiar la
                # fila de BD, sería un borrado fantasma con éxito silencioso.
                if is_device_path(entry.source_path):
                    unreachable += 1
                    diag["unreachable_device"] = True
                    diagnostics.append(diag)
                    continue
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
                _log.info(f"Discarding file: {p}")
                discard_to_trash(p)
                diag["deleted_file"] = True
                _log.info(f"File moved to trash: {p}")
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

    summary = (
        f"{deleted} movidos a _descartados/, {skipped} omitidos (no existen), {failed} errores"
    )
    if unreachable:
        summary += f", {unreachable} en el dispositivo (conecta la consola para revisarlos)"
    return {
        "deleted": deleted,
        "skipped": skipped,
        "failed": failed,
        "unreachable": unreachable,
        "freed_bytes": freed_bytes,
        "errors": errors,
        "summary": summary,
        "diagnostics": diagnostics[:10],  # Return first 10 for debugging
    }
