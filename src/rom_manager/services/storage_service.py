"""Business logic for STORAGE-MGR bulk delete (PC/Android combined library view).

Pure function decoupled from the HTTP layer, same shape as duplicates_service:
takes repositories + plain inputs, returns a result dict ready to serialize.
Keyed by (sha1, location) -- same identity the /api/library-diff checkboxes
already use for /api/sync-roms (collection.js:401-404) -- not by game_id.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from rom_manager.database.repositories.games import cascade_delete_games_by_source_path
from rom_manager.utils.trash import discard_to_trash

if TYPE_CHECKING:
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.sync.adb_transport import AdbTransport

_log = logging.getLogger(__name__)


def delete_storage_items(
    repository: LibraryRepository,
    repository_android: LibraryRepository,
    items: list[dict],
    adb_transport: AdbTransport | None = None,
) -> dict:
    """Bulk-delete selected /api/library-diff entries.

    *items*: ``[{"sha1": str, "location": "pc"|"android"}, ...]``.

    PC files go through ``_descartados/`` (AUD-3, undoable). Android files are
    removed via ADB -- a hard delete, no on-device trash exists (decision taken
    with the user 2026-08-14: adding one would eat SD space for an edge case).
    The two success counters are kept separate on purpose so the caller can
    show which side is undoable and which isn't -- merging them into one
    "deleted" number would hide that.

    Returns ``{"trashed": n, "deleted_device": n, "errors": [str, ...]}``.
    """
    trashed = 0
    deleted_device = 0
    errors: list[str] = []

    for item in items:
        sha1 = (item.get("sha1") or "").strip().upper()
        location = item.get("location") or ""
        if not sha1 or location not in ("pc", "android"):
            errors.append(f"item inválido: {item!r}")
            continue

        repo = repository if location == "pc" else repository_android
        with repo.connect() as conn:
            row = conn.execute(
                "SELECT source_path FROM games WHERE sha1 = ? AND file_type = 'rom' LIMIT 1",
                (sha1,),
            ).fetchone()
        if not row or not row["source_path"]:
            errors.append(f"{sha1}: no encontrado en biblioteca {location}")
            continue
        source_path = row["source_path"]

        if location == "pc":
            p = Path(source_path)
            if not p.exists():
                errors.append(f"{p.name}: no existe en PC")
                continue
            try:
                discard_to_trash(p)
            except Exception as exc:
                errors.append(f"{p.name}: {type(exc).__name__}: {exc}")
                continue
            trashed += 1
        else:
            if adb_transport is None:
                errors.append(f"{source_path}: dispositivo no conectado")
                continue
            try:
                adb_transport.remove(source_path)
            except Exception as exc:
                errors.append(f"{source_path}: {type(exc).__name__}: {exc}")
                continue
            deleted_device += 1

        try:
            with repo.connect() as conn:
                cascade_delete_games_by_source_path(conn, source_path)
                conn.commit()
        except Exception as exc:
            errors.append(f"{source_path}: borrado pero fallo en BD: {type(exc).__name__}: {exc}")

    return {"trashed": trashed, "deleted_device": deleted_device, "errors": errors}
