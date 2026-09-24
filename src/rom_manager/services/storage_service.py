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


def block_and_delete_game(
    repository: LibraryRepository,
    repository_android: LibraryRepository,
    sha1: str,
    canonical_title: str = "",
    reason: str = "",
    adb_transport: AdbTransport | None = None,
) -> dict:
    """GAME-BLOCKLIST-1/2: mark *sha1* as permanently excluded, then delete any
    copy currently on PC and/or Android.

    Marks the blocklist row in BOTH repositories BEFORE touching any file —
    each is a separate SQLite DB (PC/Android), and if a delete below fails
    halfway the sha1 is already blocked on both sides either way, so a later
    sync/scan/Inbox pass never silently re-adopts it (Paso 2 of the roadmap:
    "confirmar que la operación marca ANTES de borrar").

    PC delete goes through ``_descartados/`` (never a direct unlink, AUD-3),
    same as ``delete_storage_items``. Android delete needs a connected
    device — without one the mark still stands and the PC side (if present)
    is still deleted; the Android copy is left for the next `adb remove`
    opportunity, same "avisa y sigue sin bloquear" behaviour
    ``delete_storage_items`` already uses for a missing cable.
    """
    sha1 = (sha1 or "").strip().upper()
    if not sha1:
        return {
            "blocked": False,
            "trashed": False,
            "deleted_device": False,
            "errors": ["sha1 vacío"],
        }

    repository.block_sha1(sha1, canonical_title, reason)
    repository_android.block_sha1(sha1, canonical_title, reason)

    trashed = False
    deleted_device = False
    errors: list[str] = []

    with repository.connect() as conn:
        pc_row = conn.execute(
            "SELECT source_path FROM games WHERE sha1 = ? AND file_type = 'rom' LIMIT 1",
            (sha1,),
        ).fetchone()
    if pc_row and pc_row["source_path"]:
        p = Path(pc_row["source_path"])
        if not p.exists():
            errors.append(f"{p.name}: no existe en PC")
        else:
            try:
                discard_to_trash(p)
                trashed = True
            except Exception as exc:
                errors.append(f"{p.name}: {type(exc).__name__}: {exc}")
            if trashed:
                try:
                    with repository.connect() as conn:
                        cascade_delete_games_by_source_path(conn, str(p))
                        conn.commit()
                except Exception as exc:
                    errors.append(
                        f"{p.name}: borrado pero fallo en BD PC: {type(exc).__name__}: {exc}"
                    )

    with repository_android.connect() as conn:
        android_row = conn.execute(
            "SELECT source_path FROM games WHERE sha1 = ? AND file_type = 'rom' LIMIT 1",
            (sha1,),
        ).fetchone()
    if android_row and android_row["source_path"]:
        source_path = android_row["source_path"]
        if adb_transport is None:
            errors.append(f"{source_path}: dispositivo no conectado, borrado en consola pendiente")
        else:
            try:
                adb_transport.remove(source_path)
                deleted_device = True
            except Exception as exc:
                errors.append(f"{source_path}: {type(exc).__name__}: {exc}")
            if deleted_device:
                try:
                    with repository_android.connect() as conn:
                        cascade_delete_games_by_source_path(conn, source_path)
                        conn.commit()
                except Exception as exc:
                    errors.append(
                        f"{source_path}: borrado pero fallo en BD Android: "
                        f"{type(exc).__name__}: {exc}"
                    )

    return {"blocked": True, "trashed": trashed, "deleted_device": deleted_device, "errors": errors}
