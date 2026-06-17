from __future__ import annotations

import logging
import os
import shutil
import stat
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import types

    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router


# ── Public entry point ────────────────────────────────────────────────────────

def register(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    repo_android: LibraryRepository,
    srv_mod: types.ModuleType,
    job_manager: JobManager,
) -> None:
    """Register duplicate-management routes on *router*."""
    from rom_manager.web.response_builders import _build_duplicates_two_repos, _build_ra_duplicates

    # ── GET /api/duplicates ───────────────────────────────────────────────────
    @router.get("/api/duplicates")
    def get_duplicates(ctx) -> None:
        qs          = getattr(ctx, "_qs", {})
        source_root = qs.get("source_root", [None])[0] or None
        pc_root     = qs.get("pc_root",     [None])[0] or None
        ab_root     = qs.get("ab_root",     [None])[0] or None
        ctx._send_json(
            _build_duplicates_two_repos(
                repository, repo_android, config,
                source_root=source_root, pc_root=pc_root, ab_root=ab_root,
            )
        )

    # ── GET /api/ra-duplicates ────────────────────────────────────────────────
    @router.get("/api/ra-duplicates")
    def get_ra_duplicates(ctx) -> None:
        ctx._send_json(_build_ra_duplicates(repository, config))

    # ── POST /api/duplicates/delete ───────────────────────────────────────────
    @router.post("/api/duplicates/delete")
    def post_delete_duplicate(ctx) -> None:
        _delete_duplicate(ctx, ctx._post_data, repository)

    # ── POST /api/duplicates/delete-all ──────────────────────────────────────
    @router.post("/api/duplicates/delete-all")
    def post_delete_all_duplicates(ctx) -> None:
        _delete_all_duplicates(ctx, repository)

    # ── POST /api/duplicates/exclude ──────────────────────────────────────────
    @router.post("/api/duplicates/exclude")
    def post_exclude_duplicate(ctx) -> None:
        sha1 = ctx._post_data.get("sha1", "")
        if sha1:
            repository.exclude_duplicate_sha1(sha1)
            ctx._send_json({"ok": True})
        else:
            ctx._send_error(400, "sha1 required")

    # ── POST /api/apply-ra-conflicts ──────────────────────────────────────────
    @router.post("/api/apply-ra-conflicts")
    def post_apply_ra_conflicts(ctx) -> None:
        _apply_ra_conflicts(ctx, ctx._post_data, config, repository)

    # ── POST /api/ra-duplicates/discard ───────────────────────────────────────
    @router.post("/api/ra-duplicates/discard")
    def post_ra_duplicate_discard(ctx) -> None:
        _ra_duplicate_discard(ctx, ctx._post_data, repository)

    # ── POST /api/ra-duplicates/discard-all ──────────────────────────────────
    @router.post("/api/ra-duplicates/discard-all")
    def post_ra_duplicate_discard_all(ctx) -> None:
        _ra_duplicate_discard_all(ctx, config, repository)

    # ── POST /api/ra-check/discard-no-support ────────────────────────────────
    @router.post("/api/ra-check/discard-no-support")
    def post_ra_discard_no_support(ctx) -> None:
        _ra_discard_no_support(ctx, repository, srv_mod)

    # ── POST /api/resolve-duplicate-ra ───────────────────────────────────────
    @router.post("/api/resolve-duplicate-ra")
    def post_resolve_duplicate_ra(ctx) -> None:
        _resolve_duplicate_ra(ctx, ctx._post_data, repository)


# ── Handler logic (moved from server.py) ──────────────────────────────────────

_log = logging.getLogger(__name__)


def _force_remove(path: Path) -> None:
    """Remove a file, clearing the read-only attribute first if needed (WinError 5)."""
    try:
        os.remove(str(path))
    except PermissionError:
        # Clear read-only flag and retry (common on drives formatted by consoles)
        os.chmod(str(path), stat.S_IWRITE)
        os.remove(str(path))


def _delete_duplicate(ctx, data: dict, repository: LibraryRepository) -> None:
    game_id = data.get("game_id")
    if not game_id:
        ctx._send_json({"error": "game_id es obligatorio"})
        return
    source_path = data.get("source_path", "").strip()
    if not source_path:
        # Derive from DB so callers don't need to pass it
        try:
            with repository.connect() as _c:
                row = _c.execute(
                    "SELECT source_path FROM games WHERE id = ?", (int(game_id),)
                ).fetchone()
            if not row or not row["source_path"]:
                ctx._send_json({"error": f"Juego {game_id} no encontrado en la base de datos"})
                return
            source_path = row["source_path"]
        except Exception as exc:
            ctx._send_json({"error": f"Error consultando BD: {type(exc).__name__}: {exc}"})
            return
    p = Path(source_path)
    if p.exists():
        try:
            _force_remove(p)
        except Exception as exc:
            ctx._send_json({"error": f"No se pudo eliminar el archivo: {type(exc).__name__}: {exc}"})
            return
    try:
        repository.delete_game(int(game_id))
    except Exception as exc:
        ctx._send_json({"error": f"Archivo eliminado pero error en BD: {type(exc).__name__}: {exc}"})
        return
    ctx._send_json({"deleted": source_path})


def _delete_all_duplicates(ctx, repository: LibraryRepository) -> None:
    groups       = repository.get_duplicate_groups()
    deleted      = 0
    skipped      = 0  # Files that don't exist (already deleted or moved)
    failed       = 0  # Files that exist but couldn't be deleted (perms, device unmounted, etc.)
    freed_bytes  = 0
    errors: list[str] = []
    diagnostics: list[dict] = []  # Detailed log of each attempt

    for group in groups:
        for entry in group.entries[1:]:
            p = Path(entry.source_path)
            diag = {"path": str(p), "exists": p.exists(), "deleted_file": False, "deleted_db": False}

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
                    errors.append(f"{p.name}: no se pudo eliminar el archivo — {type(exc).__name__}: {exc}")
                diagnostics.append(diag)
                continue

            try:
                repository.delete_game(entry.id)
                deleted     += 1
                freed_bytes += entry.size_bytes
                diag["deleted_db"] = True
                _log.info(f"DB record deleted for: {p}")
            except Exception as exc:
                failed += 1
                diag["db_error"] = str(exc)
                _log.warning("File deleted but DB update failed for %s: %s", p, exc)
                if len(errors) < 20:
                    errors.append(f"{p.name}: archivo eliminado pero error en BD — {type(exc).__name__}: {exc}")

            diagnostics.append(diag)

    ctx._send_json({
        "deleted": deleted,
        "skipped": skipped,
        "failed": failed,
        "freed_bytes": freed_bytes,
        "errors": errors,
        "summary": f"{deleted} eliminados, {skipped} omitidos (no existen), {failed} errores",
        "diagnostics": diagnostics[:10]  # Return first 10 for debugging
    })


def _apply_ra_conflicts(ctx, data: dict, config: AppConfig, repository: LibraryRepository) -> None:
    """Resolve plan conflicts by keeping the RA winner and moving the loser to _descartados/.

    Handles both conflict types:
    - "disk":      source wants target path already occupied by a different file.
                   Compare source vs target RA; discard the loser, rename winner to target.
    - "collision": two pending ops share the same target path (two ROMs → same canonical name).
                   Group by target, compare all sources' RA; discard all but the winner.
    """
    import json as _json
    from collections import defaultdict

    from rom_manager.planner import build_plan
    from rom_manager.planner.operation_planner import FormatOptions
    from rom_manager.renamer.file_renamer import rename_rom_with_saves
    from rom_manager.retroachievements.ra_client import _parse_game_list as _pgl
    from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id

    opts = FormatOptions()
    plan = build_plan(repository, opts)

    resolved       = 0
    skipped_no_ra  = 0
    errors: list[str] = []

    cache_dir = config.project_root / ".rommgr" / "ra_cache"
    cache_dir_exists  = cache_dir.exists()
    cache_files_exist = cache_dir_exists and any(cache_dir.iterdir()) if cache_dir_exists else False

    # Build per-platform hash→achievements lookup (lazily cached)
    _hash_lib_cache: dict[str, dict] = {}

    def _hash_lib_for(plat: str) -> dict:
        if plat in _hash_lib_cache:
            return _hash_lib_cache[plat]
        console_id = get_ra_console_id(plat)
        if not console_id:
            _hash_lib_cache[plat] = {}
            return {}
        cache_file = cache_dir / f"ra_hashes_{console_id}.json"
        if not cache_file.exists():
            _hash_lib_cache[plat] = {}
            return {}
        try:
            lib = _pgl(_json.loads(cache_file.read_text(encoding="utf-8")))
        except Exception:
            lib = {}
        _hash_lib_cache[plat] = lib
        return lib

    def _ra_for_path(path: Path, plat: str) -> int:
        """Return achievement count for a file (-1 = unknown / no cache)."""
        try:
            with repository.connect() as _c:
                row = _c.execute(
                    "SELECT md5 FROM games WHERE source_path = ?", (str(path),)
                ).fetchone()
            if not row:
                return -1
            md5 = (row["md5"] or "").lower()
        except Exception:
            return -1
        if not md5:
            return -1
        entry = _hash_lib_for(plat).get(md5)
        return entry.achievements if entry else -1

    def _discard(path: Path) -> None:
        discard_dir = path.parent / "_descartados"
        discard_dir.mkdir(parents=True, exist_ok=True)
        dest = discard_dir / path.name
        if not dest.exists():
            shutil.move(str(path), dest)
        else:
            path.unlink()
        with repository.connect() as _c:
            _c.execute("DELETE FROM games WHERE source_path = ?", (str(path),))
            _c.commit()

    # ── Disk conflicts ────────────────────────────────────────────────────────
    # source wants to rename to target_path but target_path already holds a different file.
    for op in (o for o in plan.conflicts if o.conflict_reason == "disk"):
        if not op.source_path.exists():
            continue
        plat   = op.game.platform or ""
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

        try:
            _discard(loser_path)
            if winner_path and winner_target and winner_path.exists():
                # Rename winner to canonical target path
                save_exts = frozenset(config.save_extensions) if config.save_extensions else frozenset()
                outcome = rename_rom_with_saves(winner_path, winner_target, save_exts)
                if not outcome.success:
                    errors.append(f"{winner_path.name}: rename failed — {outcome.error}")
                else:
                    # Update DB with new path
                    with repository.connect() as _c:
                        _c.execute(
                            "UPDATE games SET source_path = ? WHERE source_path = ?",
                            (str(winner_target), str(winner_path))
                        )
                        _c.commit()
            resolved += 1
        except Exception as exc:
            errors.append(f"{loser_path.name}: {exc}")

    # ── Collision conflicts ───────────────────────────────────────────────────
    # Multiple source files all want to rename to the same canonical target.
    # Group by target_path so we compare all contenders at once.
    collision_groups: dict[str, list] = defaultdict(list)
    for op in (o for o in plan.conflicts if o.conflict_reason == "collision"):
        collision_groups[str(op.target_path)].append(op)

    for _target_str, ops in collision_groups.items():
        plat = ops[0].game.platform or ""
        scored = [
            (op, _ra_for_path(op.source_path, plat))
            for op in ops
            if op.source_path.exists()
        ]
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
            try:
                _discard(loser_op.source_path)
                resolved += 1
            except Exception as exc:
                errors.append(f"{loser_op.source_path.name}: {exc}")

        # Rename winner to canonical target path
        if winner_op.source_path.exists() and winner_op.source_path != winner_op.target_path:
            try:
                save_exts = frozenset(config.save_extensions) if config.save_extensions else frozenset()
                outcome = rename_rom_with_saves(winner_op.source_path, winner_op.target_path, save_exts)
                if not outcome.success:
                    errors.append(f"{winner_op.source_path.name}: rename failed — {outcome.error}")
                else:
                    # Update DB with new path
                    with repository.connect() as _c:
                        _c.execute(
                            "UPDATE games SET source_path = ? WHERE source_path = ?",
                            (str(winner_op.target_path), str(winner_op.source_path))
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
                    (str(op.source_path),)
                ).fetchone()
            debug_samples.append(dict(row) if row else {"not_found": str(op.source_path)})
        except Exception as _e:
            debug_samples.append({"error": str(_e)})

    next_step = "Si hay errores de rename, verifica que los archivos de guardado existan y sean accesibles. Luego ejecuta 'rommgr scan' para actualizar la BD si es necesario."
    ctx._send_json({
        "resolved":      resolved,
        "skipped_no_ra": skipped_no_ra,
        "errors":        errors[:10],
        "no_cache":      not cache_files_exist,
        "debug_samples": debug_samples,
        "hint":          "Si resolved=0 y skipped_no_ra>0: ejecuta primero el Check RA para poblar los MD5. Si debug_samples muestra 'not_found', la ruta en BD no coincide con la del plan.",
        "next_step":     next_step,
    })


def _ra_duplicate_discard(ctx, data: dict, repository: LibraryRepository) -> None:
    source_path = data.get("path", "").strip()
    if not source_path:
        ctx._send_error(400, "path required")
        return

    p = Path(source_path)
    if not p.exists():
        with repository.connect() as _c:
            _c.execute("DELETE FROM games WHERE source_path = ?", (source_path,))
            _c.commit()
        ctx._send_json({"ok": True, "note": "file already missing; removed from DB"})
        return

    discard_dir = p.parent / "_descartados"
    dest: Path | None = None
    moved              = False
    permanently_deleted = False
    try:
        discard_dir.mkdir(parents=True, exist_ok=True)
        dest = discard_dir / p.name
        if dest.exists():
            p.unlink()
            dest = None
            permanently_deleted = True
        else:
            shutil.move(str(p), dest)
            moved = True
        with repository.connect() as _c:
            _c.execute("DELETE FROM games WHERE source_path = ?", (source_path,))
            _c.commit()
    except Exception as exc:
        if moved and dest is not None and dest.exists():
            try:
                shutil.move(str(dest), str(p))
                _log.warning("RA discard rollback: restored %s after DB error", p.name)
            except Exception as rb_exc:
                _log.error("RA discard rollback FAILED for %s: %s", p.name, rb_exc)
                ctx._send_json({"error": f"DB error AND rollback failed — {p.name} may be lost: {exc} | rollback: {rb_exc}"})
                return
        elif permanently_deleted:
            _log.error("File %s was permanently deleted but DB delete failed: %s", p.name, exc)
            ctx._send_json({"error": f"File was deleted but DB update failed — stale entry will be removed on next scan: {exc}"})
            return
        ctx._send_json({"error": str(exc)})
        return
    ctx._send_json({"ok": True})


def _ra_duplicate_discard_all(ctx, config: AppConfig, repository: LibraryRepository) -> None:
    """Discard ALL entries without RA support from version-duplicate groups."""
    from rom_manager.web.response_builders import _build_ra_duplicates

    ra_dups = _build_ra_duplicates(repository, config)
    if ra_dups.get("note"):
        ctx._send_json({"discarded": 0, "failed": 0, "errors": [], "note": ra_dups["note"]})
        return

    discarded = 0
    failed    = 0
    errors: list[str] = []

    for group in ra_dups.get("groups", []):
        for entry in group.get("entries", []):
            if entry.get("ra_supported"):
                continue
            src_path_str = entry.get("source_path", "")
            if not src_path_str:
                continue
            p           = Path(src_path_str)
            discard_dir = p.parent / "_descartados"
            dest_file: Path | None = None
            moved               = False
            permanently_deleted = False
            try:
                discard_dir.mkdir(parents=True, exist_ok=True)
                if p.exists():
                    dest_file = discard_dir / p.name
                    if dest_file.exists():
                        p.unlink()
                        dest_file           = None
                        permanently_deleted = True
                    else:
                        shutil.move(str(p), dest_file)
                        moved = True
                with repository.connect() as _c:
                    _c.execute("DELETE FROM games WHERE source_path = ?", (src_path_str,))
                    _c.commit()
                discarded += 1
            except Exception as exc:
                failed += 1
                if moved and dest_file is not None and dest_file.exists():
                    try:
                        shutil.move(str(dest_file), str(p))
                        _log.warning("RA discard-all rollback: restored %s", p.name)
                        errors.append(f"{p.name}: DB error (file restored) — {exc}")
                    except Exception as rb_exc:
                        _log.error("RA discard-all rollback FAILED for %s: %s", p.name, rb_exc)
                        errors.append(f"{p.name}: DB error AND rollback failed — file may be lost | {exc} | {rb_exc}")
                elif permanently_deleted:
                    errors.append(f"{p.name}: deleted but DB not updated (stale entry — will be removed on next scan)")
                else:
                    errors.append(f"{p.name}: {exc}")

    ctx._send_json({"discarded": discarded, "failed": failed, "errors": errors[:10]})


def _ra_discard_no_support(ctx, repository: LibraryRepository, srv_mod) -> None:
    """Bulk-discard all games with NO RA support at all (status='no_support')."""
    result = srv_mod._job_results.get("ra_check")
    if not result:
        ctx._send_json({"error": "No RA check result available. Run RA check first."})
        return
    entries = result.get("no_support_entries", [])
    if not entries:
        ctx._send_json({"discarded": 0, "failed": 0, "errors": [], "note": "No games to discard."})
        return

    discarded = 0
    failed    = 0
    errors: list[str] = []

    for entry in entries:
        src_path_str = entry.get("source_path", "")
        if not src_path_str:
            continue
        p           = Path(src_path_str)
        discard_dir = p.parent / "_descartados"
        dest_file: Path | None = None
        moved               = False
        permanently_deleted = False
        try:
            discard_dir.mkdir(parents=True, exist_ok=True)
            if p.exists():
                dest_file = discard_dir / p.name
                if dest_file.exists():
                    p.unlink()
                    permanently_deleted = True
                else:
                    shutil.move(str(p), dest_file)
                    moved = True
            with repository.connect() as _c:
                _c.execute("DELETE FROM games WHERE source_path = ?", (src_path_str,))
            discarded += 1
        except Exception as exc:
            failed += 1
            if moved and dest_file is not None and dest_file.exists():
                try:
                    shutil.move(str(dest_file), str(p))
                    _log.warning("RA discard-no-support rollback: restored %s", p.name)
                    errors.append(f"{p.name}: DB error (file restored) — {exc}")
                except Exception as rb_exc:
                    _log.error("RA discard-no-support rollback FAILED for %s: %s", p.name, rb_exc)
                    errors.append(f"{p.name}: DB error AND rollback failed — file may be lost | {exc} | {rb_exc}")
            elif permanently_deleted:
                errors.append(f"{p.name}: deleted from disk but DB error — {exc}")
            else:
                errors.append(f"{p.name}: {exc}")

    ctx._send_json({"discarded": discarded, "failed": failed, "errors": errors[:10]})


def _resolve_duplicate_ra(ctx, data: dict, repository: LibraryRepository) -> None:
    """B1-4: Resolve title-based duplicates by keeping the one with RA support."""
    keep_path     = data.get("keep_path", "").strip()
    discard_paths = data.get("discard_paths", [])
    if not keep_path or not discard_paths:
        ctx._send_json({"error": "keep_path and discard_paths required"})
        return

    discarded = 0
    failed    = 0
    errors: list[str] = []

    for src_path_str in discard_paths:
        p = Path(src_path_str)
        if not p.exists():
            try:
                with repository.connect() as _c:
                    _c.execute("DELETE FROM games WHERE source_path = ?", (src_path_str,))
                    _c.commit()
                discarded += 1
            except Exception as exc:
                failed += 1
                errors.append(f"{p.name}: {exc}")
            continue

        discard_dir = p.parent / "_descartados"
        dest_file: Path | None = None
        try:
            discard_dir.mkdir(parents=True, exist_ok=True)
            dest_file = discard_dir / p.name
            if dest_file.exists():
                p.unlink()
            else:
                shutil.move(str(p), str(dest_file))
            with repository.connect() as _c:
                _c.execute("DELETE FROM games WHERE source_path = ?", (src_path_str,))
                _c.commit()
            discarded += 1
        except Exception as exc:
            failed += 1
            _log.error("Failed to discard duplicate %s: %s", p.name, exc)
            if dest_file and dest_file.exists():
                try:
                    shutil.move(str(dest_file), str(p))
                except Exception:
                    pass
            errors.append(f"{p.name}: {exc}")

    ctx._send_json({"discarded": discarded, "failed": failed, "errors": errors[:10]})
