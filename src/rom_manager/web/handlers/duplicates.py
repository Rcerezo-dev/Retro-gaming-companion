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
    import types


# ── Public entry point ────────────────────────────────────────────────────────

def register(
    router: "Router",
    *,
    config: "AppConfig",
    repository: "LibraryRepository",
    repo_android: "LibraryRepository",
    srv_mod: "types.ModuleType",
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


def _delete_duplicate(ctx, data: dict, repository: "LibraryRepository") -> None:
    game_id     = data.get("game_id")
    source_path = data.get("source_path", "").strip()
    if not game_id or not source_path:
        ctx._send_json({"error": "game_id y source_path son obligatorios"})
        return
    p = Path(source_path)
    if p.exists():
        try:
            os.remove(str(p))
        except Exception as exc:
            ctx._send_json({"error": f"No se pudo eliminar el archivo: {type(exc).__name__}: {exc}"})
            return
    try:
        repository.delete_game(int(game_id))
    except Exception as exc:
        ctx._send_json({"error": f"Archivo eliminado pero error en BD: {type(exc).__name__}: {exc}"})
        return
    ctx._send_json({"deleted": source_path})


def _delete_all_duplicates(ctx, repository: "LibraryRepository") -> None:
    groups       = repository.get_duplicate_groups()
    deleted      = 0
    failed       = 0
    freed_bytes  = 0
    errors: list[str] = []

    for group in groups:
        for entry in group.entries[1:]:
            p = Path(entry.source_path)
            if not p.exists():
                try:
                    repository.delete_game(entry.id)
                    deleted += 1
                except Exception as exc:
                    failed += 1
                    _log.warning("Could not remove DB entry for missing file %s: %s", p, exc)
                    if len(errors) < 20:
                        errors.append(f"{p.name}: DB error — {type(exc).__name__}: {exc}")
                continue

            try:
                os.remove(str(p))
            except Exception as exc:
                failed += 1
                _log.warning("Could not delete duplicate file %s: %s", p, exc)
                if len(errors) < 20:
                    errors.append(f"{p.name}: no se pudo eliminar el archivo — {type(exc).__name__}: {exc}")
                continue

            try:
                repository.delete_game(entry.id)
                deleted     += 1
                freed_bytes += entry.size_bytes
            except Exception as exc:
                failed += 1
                _log.warning("File deleted but DB update failed for %s: %s", p, exc)
                if len(errors) < 20:
                    errors.append(f"{p.name}: archivo eliminado pero error en BD — {type(exc).__name__}: {exc}")

    ctx._send_json({"deleted": deleted, "failed": failed, "freed_bytes": freed_bytes, "errors": errors})


def _apply_ra_conflicts(ctx, data: dict, config: "AppConfig", repository: "LibraryRepository") -> None:
    """Resolve plan conflicts by keeping the RA winner and moving the loser to _descartados/."""
    from rom_manager.planner.operation_planner import FormatOptions
    from rom_manager.planner import build_plan
    import json as _json

    opts = FormatOptions()
    plan = build_plan(repository, opts)

    resolved       = 0
    skipped_no_ra  = 0
    errors: list[str] = []

    cache_dir = config.project_root / ".rommgr" / "ra_cache"
    cache_dir_exists   = cache_dir.exists()
    cache_files_exist  = cache_dir_exists and any(cache_dir.iterdir()) if cache_dir_exists else False

    for op in plan.conflicts:
        if not op.source_path.exists():
            continue

        src_md5: str | None = None
        tgt_md5: str | None = None
        try:
            with repository.connect() as _c:
                _src_row = _c.execute(
                    "SELECT md5 FROM games WHERE source_path = ?", (str(op.source_path),)
                ).fetchone()
                _tgt_row = _c.execute(
                    "SELECT md5 FROM games WHERE source_path = ?", (str(op.target_path),)
                ).fetchone()
            if _src_row:
                src_md5 = _src_row["md5"]
            if _tgt_row:
                tgt_md5 = _tgt_row["md5"]
        except Exception:
            pass

        from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id
        from rom_manager.retroachievements.ra_client import _parse_game_list as _pgl

        plat       = op.game.platform or ""
        console_id = get_ra_console_id(plat)
        src_ra = tgt_ra = -1
        if console_id:
            cache_file = cache_dir / f"ra_hashes_{console_id}.json"
            if cache_file.exists():
                try:
                    _hash_lib = _pgl(_json.loads(cache_file.read_text(encoding="utf-8")))
                    if src_md5:
                        src_entry = _hash_lib.get(src_md5.lower())
                        src_ra    = src_entry.achievements if src_entry else -1
                    if tgt_md5:
                        tgt_entry = _hash_lib.get(tgt_md5.lower())
                        tgt_ra    = tgt_entry.achievements if tgt_entry else -1
                except Exception:
                    pass

        if src_ra <= 0 and tgt_ra <= 0:
            skipped_no_ra += 1
            continue

        loser_path = op.target_path if tgt_ra > src_ra else op.source_path
        discard_dir = loser_path.parent / "_descartados"
        try:
            discard_dir.mkdir(parents=True, exist_ok=True)
            dest = discard_dir / loser_path.name
            if not dest.exists():
                shutil.move(str(loser_path), dest)
            else:
                loser_path.unlink()
            with repository.connect() as _c:
                _c.execute("DELETE FROM games WHERE source_path = ?", (str(loser_path),))
                _c.execute("PRAGMA optimize")
            resolved += 1
        except Exception as exc:
            errors.append(f"{loser_path.name}: {exc}")

    ctx._send_json({
        "resolved":      resolved,
        "skipped_no_ra": skipped_no_ra,
        "errors":        errors[:10],
        "no_cache":      not cache_files_exist,
    })


def _ra_duplicate_discard(ctx, data: dict, repository: "LibraryRepository") -> None:
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


def _ra_duplicate_discard_all(ctx, config: "AppConfig", repository: "LibraryRepository") -> None:
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


def _ra_discard_no_support(ctx, repository: "LibraryRepository", srv_mod) -> None:
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


def _resolve_duplicate_ra(ctx, data: dict, repository: "LibraryRepository") -> None:
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
