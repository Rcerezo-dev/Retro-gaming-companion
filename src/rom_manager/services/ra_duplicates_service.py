"""Business logic for RetroAchievements-driven duplicate resolution (ARC-SVC-1).

Pure functions decoupled from the HTTP layer. Unlike ``duplicates_service`` (hard
delete), these *soft-discard* losers into a sibling ``_descartados/`` folder so a
mistaken removal can be recovered. No web ``ctx`` here: callers pass plain inputs
(or pre-built report dicts) and receive result dicts ready to serialize.
"""

from __future__ import annotations

import json as _json
import logging
import shutil
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from rom_manager.database.repositories.games import cascade_delete_games_by_source_path
from rom_manager.utils.paths import is_device_path
from rom_manager.utils.trash import discard_to_trash

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.sync.adb_transport import AdbTransport

_log = logging.getLogger(__name__)


def _delete_row(repository: LibraryRepository, source_path: str) -> None:
    with repository.connect() as conn:
        cascade_delete_games_by_source_path(conn, source_path)
        conn.commit()


def _discard_file(
    repository: LibraryRepository,
    source_path: str,
    adb_transport: AdbTransport | None = None,
) -> tuple[bool, str | None]:
    """Soft-discard one file: move it into ``_descartados/`` and delete its DB row.

    *adb_transport*: when *source_path* lives on a connected device
    (TABS-FIX-1a), deletes it there via ADB before touching the DB row.
    ``None`` falls back to the explicit "conecta el dispositivo" error.

    Returns ``(ok, error)``. Semantics, preserved across all RA discard endpoints:
      * file already gone → just clean the DB row.
      * otherwise         → move the source into _descartados/ (AUD-3: shared
        helper; a same-named file there gets a numeric suffix — nothing is
        permanently deleted anymore).
    On a DB failure *after* a successful move, the file is restored (rollback).
    """
    p = Path(source_path)

    # File already gone: just clean the DB row.
    if not p.exists():
        # TABS-FIX-1: a device path (ADB scan, e.g. /storage/...) is never a
        # valid Windows path — Path.exists() is always False here even when
        # the file is alive on the console. Treating that as "genuinely gone"
        # deleted the DB row and reported success while the real duplicate
        # stayed on the device and reappeared on the next ADB scan.
        if is_device_path(source_path):
            if adb_transport is None:
                return False, (
                    f"{p.name}: ruta de consola — conecta el dispositivo para verificar "
                    "si el archivo sigue ahí; no se ha tocado la fila de la base de datos"
                )
            try:
                adb_transport.remove(source_path)
            except Exception as exc:
                return False, f"{p.name}: no se pudo borrar en el dispositivo — {exc}"
            try:
                _delete_row(repository, source_path)
                return True, None
            except Exception as exc:
                return False, f"{p.name}: archivo eliminado en consola pero error en BD — {exc}"
        try:
            _delete_row(repository, source_path)
            return True, None
        except Exception as exc:
            return False, f"{p.name}: {exc}"

    dest: Path | None = None
    try:
        dest = discard_to_trash(p)
        _delete_row(repository, source_path)
        return True, None
    except Exception as exc:
        if dest is not None and dest.exists():
            try:
                shutil.move(str(dest), str(p))
                _log.warning("RA discard rollback: restored %s after DB error", p.name)
                return False, f"{p.name}: DB error (file restored) — {exc}"
            except Exception as rb_exc:
                _log.error("RA discard rollback FAILED for %s: %s", p.name, rb_exc)
                return (
                    False,
                    f"{p.name}: DB error AND rollback failed — file may be lost | {exc} | {rb_exc}",
                )
        return False, f"{p.name}: {exc}"


def discard_ra_duplicate(
    repository: LibraryRepository, source_path: str, adb_transport: AdbTransport | None = None
) -> dict:
    """Discard a single RA-version duplicate by path. Caller validates non-empty."""
    p = Path(source_path)
    missing = not p.exists()
    ok, error = _discard_file(repository, source_path, adb_transport)
    if not ok:
        return {"error": error}
    if missing:
        return {"ok": True, "note": "file already missing; removed from DB"}
    return {"ok": True}


def discard_all_ra_duplicates(
    repository: LibraryRepository, ra_dups: dict, adb_transport: AdbTransport | None = None
) -> dict:
    """Discard every entry without RA support across the RA-duplicate *ra_dups* report.

    *ra_dups* is the result of ``builders.duplicates._build_ra_duplicates`` (built by
    the handler so this layer stays independent of ``web``).
    """
    if ra_dups.get("note"):
        return {"discarded": 0, "failed": 0, "errors": [], "note": ra_dups["note"]}

    discarded = 0
    failed = 0
    errors: list[str] = []

    for group in ra_dups.get("groups", []):
        for entry in group.get("entries", []):
            if entry.get("ra_supported"):
                continue
            src_path_str = entry.get("source_path", "")
            if not src_path_str:
                continue
            ok, error = _discard_file(repository, src_path_str, adb_transport)
            if ok:
                discarded += 1
            else:
                failed += 1
                if error:
                    errors.append(error)

    return {"discarded": discarded, "failed": failed, "errors": errors[:10]}


def discard_no_support(
    repository: LibraryRepository, entries: list[dict], adb_transport: AdbTransport | None = None
) -> dict:
    """Bulk-discard all games with no RA support at all (RA check ``no_support_entries``)."""
    if not entries:
        return {"discarded": 0, "failed": 0, "errors": [], "note": "No games to discard."}

    discarded = 0
    failed = 0
    errors: list[str] = []

    for entry in entries:
        src_path_str = entry.get("source_path", "")
        if not src_path_str:
            continue
        ok, error = _discard_file(repository, src_path_str, adb_transport)
        if ok:
            discarded += 1
        else:
            failed += 1
            if error:
                errors.append(error)

    return {"discarded": discarded, "failed": failed, "errors": errors[:10]}


def resolve_duplicate_ra(
    repository: LibraryRepository,
    keep_path: str,
    discard_paths: list[str],
    adb_transport: AdbTransport | None = None,
) -> dict:
    """B1-4: resolve title-based duplicates by keeping *keep_path* and discarding the rest.

    Caller validates that *keep_path* and *discard_paths* are non-empty.
    """
    discarded = 0
    failed = 0
    errors: list[str] = []

    for src_path_str in discard_paths:
        ok, error = _discard_file(repository, src_path_str, adb_transport)
        if ok:
            discarded += 1
        else:
            failed += 1
            if error:
                errors.append(error)

    return {"discarded": discarded, "failed": failed, "errors": errors[:10]}


def get_ra_hash_lib(config: AppConfig, platform: str, cache: dict[str, dict]) -> dict:
    """md5(lower) → parsed RA game entry (with ``.achievements``) for *platform*.

    *cache* is a per-call dict the caller owns, so repeated lookups across many
    conflicts in the same run only touch disk once per platform.
    """
    if platform in cache:
        return cache[platform]
    import time as _time

    from rom_manager.retroachievements.ra_client import _CACHE_TTL_SECONDS
    from rom_manager.retroachievements.ra_client import _parse_game_list as _pgl
    from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id

    console_id = get_ra_console_id(platform)
    if not console_id:
        cache[platform] = {}
        return {}
    cache_file = config.project_root / ".rommgr" / "ra_cache" / f"ra_hashes_{console_id}.json"
    if not cache_file.exists():
        cache[platform] = {}
        return {}
    # Same TTL as ra_client.fetch_hash_library — a stale cache must not be
    # treated as authoritative for duplicate resolution.
    if _time.time() - cache_file.stat().st_mtime >= _CACHE_TTL_SECONDS:
        cache[platform] = {}
        return {}
    try:
        lib = _pgl(_json.loads(cache_file.read_text(encoding="utf-8")))
    except Exception:
        _log.warning("Caché RA corrupta o ilegible: %s", cache_file, exc_info=True)
        lib = {}
    cache[platform] = lib
    return lib


def get_ra_achievements(config: AppConfig, platform: str, md5: str, cache: dict[str, dict]) -> int:
    """Achievement count for *md5* on *platform* — -1 if unknown or no cache."""
    if not md5:
        return -1
    entry = get_ra_hash_lib(config, platform, cache).get(md5.lower())
    return entry.achievements if entry else -1


def get_ra_achievements_for_path(
    repository: LibraryRepository,
    config: AppConfig,
    source_path: str,
    platform: str,
    cache: dict[str, dict],
) -> int:
    """Achievement count for the game stored at *source_path* — -1 if unknown."""
    try:
        with repository.connect() as conn:
            row = conn.execute(
                "SELECT md5 FROM games WHERE source_path = ?", (source_path,)
            ).fetchone()
    except Exception:
        _log.debug("Consulta RA por ruta falló: %s", source_path, exc_info=True)
        return -1
    if not row:
        return -1
    return get_ra_achievements(config, platform, (row["md5"] or ""), cache)


def apply_ra_conflicts(
    repository: LibraryRepository, config: AppConfig, adb_transport: AdbTransport | None = None
) -> dict:
    """Resolve plan conflicts by keeping the RA winner and moving the loser to _descartados/.

    Handles both conflict types:
    - "disk":      source wants target path already occupied by a different file.
                   Compare source vs target RA; discard the loser, rename winner to target.
    - "collision": two pending ops share the same target path (two ROMs → same canonical name).
                   Group by target, compare all sources' RA; discard all but the winner.
    """
    from rom_manager.planner import build_plan
    from rom_manager.planner.operation_planner import FormatOptions
    from rom_manager.renamer.file_renamer import central_save_dirs, rename_rom_with_saves

    opts = FormatOptions()
    plan = build_plan(repository, opts)
    extra_save_dirs = central_save_dirs(config)

    resolved = 0
    skipped_no_ra = 0
    errors: list[str] = []

    cache_dir = config.project_root / ".rommgr" / "ra_cache"
    cache_dir_exists = cache_dir.exists()
    cache_files_exist = cache_dir_exists and any(cache_dir.iterdir()) if cache_dir_exists else False

    # Build per-platform hash→achievements lookup (lazily cached)
    _hash_lib_cache: dict[str, dict] = {}

    def _ra_for_path(path: Path, plat: str) -> int:
        return get_ra_achievements_for_path(repository, config, str(path), plat, _hash_lib_cache)

    # ── Disk conflicts ────────────────────────────────────────────────────────
    # source wants to rename to target_path but target_path already holds a different file.
    for op in (o for o in plan.conflicts if o.conflict_reason == "disk"):
        if not op.source_path.exists():
            continue
        plat = op.game.platform or ""
        src_ra = _ra_for_path(op.source_path, plat)
        tgt_ra = _ra_for_path(op.target_path, plat)

        if src_ra <= 0 and tgt_ra <= 0:
            skipped_no_ra += 1
            continue

        # Lower RA (or unknown) is the loser; equal → discard source (keep existing)
        if tgt_ra < src_ra:
            # Target is loser; discard it and rename source to target
            loser_path = op.target_path
            winner_path = op.source_path
            winner_target = op.target_path
        else:
            # Source is loser; discard it (target stays in place)
            loser_path = op.source_path
            winner_path = None
            winner_target = None

        ok, err = _discard_file(repository, str(loser_path), adb_transport)
        if not ok:
            errors.append(err or f"{loser_path.name}: discard failed")
            continue
        if winner_path and winner_target and winner_path.exists():
            save_exts = frozenset(config.save_extensions) if config.save_extensions else frozenset()
            outcome = rename_rom_with_saves(
                winner_path, winner_target, save_exts, extra_dirs=extra_save_dirs
            )
            if not outcome.success:
                errors.append(f"{winner_path.name}: rename failed — {outcome.error}")
            else:
                with repository.connect() as _c:
                    _c.execute(
                        "UPDATE games SET source_path = ? WHERE source_path = ?",
                        (str(winner_target), str(winner_path)),
                    )
                    _c.commit()
        resolved += 1

    # ── Collision conflicts ───────────────────────────────────────────────────
    # Multiple source files all want to rename to the same canonical target.
    # Group by target_path so we compare all contenders at once.
    collision_groups: dict[str, list] = defaultdict(list)
    for op in (o for o in plan.conflicts if o.conflict_reason == "collision"):
        collision_groups[str(op.target_path)].append(op)

    for _target_str, ops in collision_groups.items():
        plat = ops[0].game.platform or ""
        scored = [(op, _ra_for_path(op.source_path, plat)) for op in ops if op.source_path.exists()]
        if not scored:
            continue

        any_has_ra = any(ra > 0 for _, ra in scored)
        if not any_has_ra:
            skipped_no_ra += 1
            continue

        # Highest RA wins; ties keep the first candidate (stable sort)
        scored.sort(key=lambda x: x[1], reverse=True)
        winner_op, winner_ra = scored[0]
        if winner_ra <= 0:
            skipped_no_ra += 1
            continue

        # Discard all non-winners and rename winner to canonical target
        for loser_op, _ in scored[1:]:
            ok, err = _discard_file(repository, str(loser_op.source_path), adb_transport)
            if ok:
                resolved += 1
            else:
                errors.append(err or loser_op.source_path.name)

        # Rename winner to canonical target path
        if winner_op.source_path.exists() and winner_op.source_path != winner_op.target_path:
            try:
                save_exts = (
                    frozenset(config.save_extensions) if config.save_extensions else frozenset()
                )
                outcome = rename_rom_with_saves(
                    winner_op.source_path,
                    winner_op.target_path,
                    save_exts,
                    extra_dirs=extra_save_dirs,
                )
                if not outcome.success:
                    errors.append(f"{winner_op.source_path.name}: rename failed — {outcome.error}")
                else:
                    # Update DB with new path
                    with repository.connect() as _c:
                        _c.execute(
                            "UPDATE games SET source_path = ? WHERE source_path = ?",
                            (str(winner_op.target_path), str(winner_op.source_path)),
                        )
                        _c.commit()
            except Exception as exc:
                errors.append(f"{winner_op.source_path.name}: rename error — {exc}")

    # Diagnostic: sample MD5 lookups from the first few conflicts (helps diagnose H1/H2)
    debug_samples: list[dict] = []
    for op in (list(plan.conflicts) + list(plan.pending))[:3]:
        try:
            with repository.connect() as _c:
                row = _c.execute(
                    "SELECT md5, source_path FROM games WHERE source_path = ?",
                    (str(op.source_path),),
                ).fetchone()
            debug_samples.append(dict(row) if row else {"not_found": str(op.source_path)})
        except Exception as _e:
            debug_samples.append({"error": str(_e)})

    next_step = "Si hay errores de rename, verifica que los archivos de guardado existan y sean accesibles. Luego ejecuta 'rommgr scan' para actualizar la BD si es necesario."
    return {
        "resolved": resolved,
        "skipped_no_ra": skipped_no_ra,
        "errors": errors[:10],
        "no_cache": not cache_files_exist,
        "debug_samples": debug_samples,
        "hint": "Si resolved=0 y skipped_no_ra>0: ejecuta primero el Check RA para poblar los MD5. Si debug_samples muestra 'not_found', la ruta en BD no coincide con la del plan.",
        "next_step": next_step,
    }
