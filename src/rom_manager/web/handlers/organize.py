from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Callable

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
    get_repo_fn: "Callable[[str], LibraryRepository]",
    srv_mod: "types.ModuleType",
) -> None:
    """Register organize / plan / apply routes on *router*."""
    from rom_manager.web.response_builders import _parse_format_opts, _build_plan

    # ── GET /api/plan ─────────────────────────────────────────────────────────
    @router.get("/api/plan")
    def get_plan(ctx) -> None:
        qs          = getattr(ctx, "_qs", {})
        opts        = _parse_format_opts(qs)
        source_root = qs.get("source_root", [None])[0] or None
        plan_repo   = get_repo_fn(source_root or "")
        ctx._send_json(
            _build_plan(
                plan_repo, opts, frozenset(config.save_extensions),
                source_root=source_root,
                library_root=str(config.library_root) if config.library_root else None,
            )
        )

    # ── POST /api/apply ───────────────────────────────────────────────────────
    @router.post("/api/apply")
    def post_apply(ctx) -> None:
        _do_apply(ctx, ctx._post_data, config, get_repo_fn, srv_mod)

    # ── POST /api/fix-platforms ───────────────────────────────────────────────
    @router.post("/api/fix-platforms")
    def post_fix_platforms(ctx) -> None:
        from rom_manager.detection.platform_detector import detect_platform
        updated = repository.backfill_platforms(detect_platform)
        ctx._send_json({"updated": updated})

    # ── POST /api/create-library-structure ────────────────────────────────────
    @router.post("/api/create-library-structure")
    def post_create_library_structure(ctx) -> None:
        _do_create_library_structure(ctx, ctx._post_data, config, srv_mod)

    # ── POST /api/organize-library ────────────────────────────────────────────
    @router.post("/api/organize-library")
    def post_organize_library(ctx) -> None:
        _do_organize_library(ctx, ctx._post_data, config, repository, srv_mod)

    # ── POST /api/migrate-saves-structure ─────────────────────────────────────
    @router.post("/api/migrate-saves-structure")
    def post_migrate_saves_structure(ctx) -> None:
        _do_migrate_saves_structure(ctx, ctx._post_data, config)


# ── Handler logic (moved from server.py) ──────────────────────────────────────

def _do_apply(
    ctx,
    data: dict,
    config: "AppConfig",
    get_repo_fn: "Callable[[str], LibraryRepository]",
    srv_mod,
) -> None:
    from rom_manager.planner.operation_planner import FormatOptions
    from rom_manager.planner import build_plan

    m = srv_mod
    with m._job_lock:
        if m._jobs["apply"]:
            ctx._send_json({"status": "already_running"})
            return
        m._jobs["apply"] = True

    fmt  = data.get("format_opts", {})
    opts = FormatOptions(
        include_region=fmt.get("include_region", True),
        include_revision=fmt.get("include_revision", True),
        include_platform=fmt.get("include_platform", False),
        include_sha=fmt.get("include_sha", False),
        sha_length=min(40, max(4, int(fmt.get("sha_length", 8)))),
    )
    source_root = data.get("source_root") or None
    keep_both   = bool(data.get("keep_both", False))

    def run() -> None:
        try:
            from rom_manager.renamer.file_renamer import rename_rom_with_saves
            from rom_manager.scanner.rom_scanner import utc_now

            save_exts  = frozenset(config.save_extensions)
            apply_repo = get_repo_fn(source_root or "")
            plan       = build_plan(apply_repo, opts, keep_both=keep_both)
            pending_ops = plan.pending
            if source_root:
                root_lower  = source_root.lower()
                pending_ops = [op for op in pending_ops if str(op.source_path).lower().startswith(root_lower)]

            total      = len(pending_ops)
            renamed = failed = skipped = saves_renamed = 0
            skip_details: list[str] = []
            timestamp = utc_now()
            m._apply_progress.update({"current": 0, "total": total, "current_file": ""})

            for idx, op in enumerate(pending_ops, 1):
                m._apply_progress.update({"current": idx, "total": total, "current_file": op.source_path.name})
                if not op.source_path.exists():
                    skipped += 1
                    skip_details.append(f"{op.source_path.name}: source not found (outdated DB entry)")
                    continue
                try:
                    bk = config.data_dir if config.backup_saves_enabled else None
                    op.target_path.parent.mkdir(parents=True, exist_ok=True)
                    if op.source_path.suffix.lower() in {".cue", ".gdi"}:
                        from rom_manager.renamer.file_renamer import move_disc_set_to_subfolder
                        outcome = move_disc_set_to_subfolder(
                            op.source_path, op.target_path, save_exts,
                            backup_root=bk,
                            backup_keep_n=config.backup_saves_keep_n,
                        )
                    else:
                        outcome = rename_rom_with_saves(
                            op.source_path, op.target_path, save_exts,
                            backup_root=bk,
                            backup_keep_n=config.backup_saves_keep_n,
                        )
                except Exception as exc:
                    skipped += 1
                    skip_details.append(f"{op.source_path.name}: unexpected error — {exc}")
                    continue

                if outcome.success:
                    op_repo = get_repo_fn(str(op.source_path))
                    op_repo.apply_rename(
                        game_id=op.game.id,
                        old_source_path=str(op.source_path),
                        new_source_path=str(op.target_path),
                        new_filename=op.target_path.name,
                        timestamp=timestamp,
                    )
                    renamed       += 1
                    saves_renamed += outcome.saves_renamed
                else:
                    err_lower = outcome.error.lower()
                    if "not found" in err_lower or "no such file" in err_lower:
                        skipped += 1
                    else:
                        failed += 1
                    skip_details.append(f"{op.source_path.name}: {outcome.error}")

            m._job_results["apply"] = {
                "renamed":       renamed,
                "failed":        failed,
                "skipped":       skipped,
                "saves_renamed": saves_renamed,
                "conflicts":     len(plan.conflicts),
                "skip_details":  skip_details[:20],
                "error_details": skip_details[:50],
                "result_ts":     utc_now(),
            }
        except Exception as exc:
            m._job_results["apply"] = {"error": str(exc), "result_ts": ""}
        finally:
            with m._job_lock:
                m._apply_progress.clear()
                m._jobs["apply"] = False

    threading.Thread(target=run, daemon=True).start()
    ctx._send_json({"status": "started"})


def _do_create_library_structure(ctx, data: dict, config: "AppConfig", srv_mod) -> None:
    if not config.library_root:
        ctx._send_json({"error": "library_root no configurado"})
        return

    std_folders = srv_mod._STANDARD_PLATFORM_FOLDERS
    also_android    = bool(data.get("also_android"))
    android_root_str = config.anbernic_root or None

    def _create_tree(root: Path) -> tuple[list[str], list[str]]:
        created: list[str] = []
        skipped: list[str] = []
        for folder in std_folders:
            plat_dir = root / folder
            if not plat_dir.exists():
                plat_dir.mkdir(parents=True, exist_ok=True)
                created.append(folder)
            else:
                skipped.append(folder)
            for sub in ("media/images", "media/videos"):
                sub_dir = plat_dir / Path(sub)
                if not sub_dir.exists():
                    sub_dir.mkdir(parents=True, exist_ok=True)
                    created.append(f"{folder}/{sub}")
        for special in ("saves", "states", "bios", "inbox", "screenshots"):
            d = root / special
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                created.append(special)
            else:
                skipped.append(special)
        for folder in std_folders:
            for special_sub in ("saves", "states"):
                sub_dir = root / special_sub / folder
                if not sub_dir.exists():
                    sub_dir.mkdir(parents=True, exist_ok=True)
                    created.append(f"{special_sub}/{folder}")
        return created, skipped

    pc_root              = Path(config.library_root)
    pc_created, pc_skipped = _create_tree(pc_root)

    android_result: dict = {}
    if also_android and android_root_str:
        android_root = Path(android_root_str)
        if android_root.exists():
            ab_created, ab_skipped = _create_tree(android_root)
            android_result = {"root": str(android_root), "created": ab_created, "skipped": ab_skipped}
        else:
            android_result = {
                "root": str(android_root),
                "error": "Ruta no accesible — conecta la tarjeta SD o el dispositivo primero",
            }

    ctx._send_json({
        "created": pc_created,
        "skipped": pc_skipped,
        "root":    str(pc_root),
        "android": android_result,
    })


def _do_organize_library(
    ctx,
    data: dict,
    config: "AppConfig",
    repository: "LibraryRepository",
    srv_mod,
) -> None:
    """Move ROMs → platform folders, saves → saves/{platform}/, BIOS candidates → bios/."""
    import shutil

    from rom_manager.web.response_builders import _utc_now_str

    es_folders  = srv_mod._ES_PLATFORM_FOLDERS
    dry_run     = data.get("dry_run", True)
    if not config.library_root:
        ctx._send_json({"error": "library_root no configurado"})
        return

    root      = Path(config.library_root)
    saves_dir = root / "saves"
    bios_dir  = root / "bios"

    save_exts = frozenset(getattr(config, "save_extensions", [
        ".sav", ".srm", ".state", ".ogg", ".rtc",
    ]))
    _known_bios_names = frozenset({
        "scph1001.bin", "scph5500.bin", "scph5501.bin", "scph5502.bin",
        "scph7001.bin", "scph7502.bin", "scph10000.bin",
        "bios_CD_E.bin", "bios_CD_J.bin", "bios_CD_U.bin",
        "dc_boot.bin", "dc_flash.bin",
        "gba_bios.bin",
        "bios7.bin", "bios9.bin", "firmware.bin",
        "ym2608_adpcm_rom.bin",
    })

    moves_roms:  list[dict] = []
    moves_saves: list[dict] = []
    moves_bios:  list[dict] = []
    errors:      list[str]  = []

    # 1. ROMs + their associated saves
    with repository.connect() as conn:
        rows = conn.execute(
            "SELECT id, source_path, platform FROM games WHERE source_path IS NOT NULL"
        ).fetchall()

    for row in rows:
        game_id, src_str, platform = row[0], row[1], row[2] or ""
        src = Path(src_str)
        if not src.exists():
            continue
        es_folder  = es_folders.get(platform, "")
        if not es_folder:
            continue
        target_dir = root / es_folder
        target     = target_dir / src.name
        if src != target:
            moves_roms.append({"source": str(src), "target": str(target), "platform": platform, "filename": src.name})
            if not dry_run:
                try:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    if target.exists():
                        errors.append(f"Conflicto ROM: {src.name} ya existe en {es_folder}/")
                    else:
                        shutil.move(str(src), str(target))
                        with repository.connect() as conn:
                            conn.execute(
                                "UPDATE games SET source_path = ?, updated_at = ? WHERE source_path = ?",
                                (str(target), _utc_now_str(), src_str),
                            )
                            conn.commit()
                except Exception as exc:
                    errors.append(f"ROM {src.name}: {exc}")

        # Move sibling saves → saves/{platform}/
        plat_save_dir = saves_dir / es_folder if es_folder else saves_dir
        for save_ext in save_exts:
            sibling = src.with_suffix(save_ext)
            if sibling.exists() and sibling.parent != plat_save_dir:
                save_target = plat_save_dir / sibling.name
                moves_saves.append({"source": str(sibling), "target": str(save_target), "platform": platform})
                if not dry_run:
                    try:
                        plat_save_dir.mkdir(parents=True, exist_ok=True)
                        if not save_target.exists():
                            shutil.move(str(sibling), str(save_target))
                    except Exception as exc:
                        errors.append(f"Save {sibling.name}: {exc}")

    # 2. BIOS candidates
    with repository.connect() as conn:
        known_paths = {row[0] for row in conn.execute("SELECT source_path FROM games").fetchall()}

    for candidate in list(root.rglob("*.bin")):
        if candidate.parent.name in ("bios", "saves", "states", "inbox", "screenshots"):
            continue
        if any(p.name in ("saves", "states") for p in candidate.parents):
            continue
        if str(candidate) in known_paths:
            continue
        if candidate.name.lower() not in _known_bios_names:
            continue
        bios_target = bios_dir / candidate.name
        if candidate == bios_target:
            continue
        moves_bios.append({"source": str(candidate), "target": str(bios_target), "filename": candidate.name})
        if not dry_run:
            try:
                bios_dir.mkdir(parents=True, exist_ok=True)
                if not bios_target.exists():
                    shutil.move(str(candidate), str(bios_target))
            except Exception as exc:
                errors.append(f"BIOS {candidate.name}: {exc}")

    total_preview = (moves_roms + moves_saves + moves_bios)[:40]
    ctx._send_json({
        "dry_run":     dry_run,
        "moves_roms":  len(moves_roms),
        "moves_saves": len(moves_saves),
        "moves_bios":  len(moves_bios),
        "errors":      errors,
        "preview":     total_preview if dry_run else [],
    })


def _do_migrate_saves_structure(ctx, data: dict, config: "AppConfig") -> None:
    """Move saves → <platform>/saves/ and savestates → <platform>/states/.

    Each ROM platform folder keeps its ROM files in place; sibling .sav/.srm etc.
    go into a 'saves' subfolder and .state/.st0 etc. go into a 'states' subfolder.
    """
    import shutil

    dry_run = bool(data.get("dry_run", True))
    if not config.library_root:
        ctx._send_json({"error": "library_root no configurado"})
        return

    root          = Path(config.library_root)
    save_exts     = frozenset(config.save_extensions)
    state_exts    = frozenset(config.state_extensions)
    all_save_like = save_exts | state_exts

    moves_saves:  list[dict] = []
    moves_states: list[dict] = []
    errors:       list[str]  = []

    for plat_dir in root.iterdir():
        if not plat_dir.is_dir():
            continue
        if plat_dir.name in ("saves", "states", "bios", "inbox", "screenshots", "_descartados"):
            continue

        saves_sub  = plat_dir / "saves"
        states_sub = plat_dir / "states"

        for f in list(plat_dir.iterdir()):
            if not f.is_file():
                continue
            ext = f.suffix.lower()
            if ext not in all_save_like:
                continue

            if ext in state_exts:
                target = states_sub / f.name
                moves_states.append({"source": str(f), "target": str(target), "platform": plat_dir.name})
                if not dry_run:
                    try:
                        states_sub.mkdir(parents=True, exist_ok=True)
                        if not target.exists():
                            shutil.move(str(f), target)
                        else:
                            errors.append(f"Conflicto state: {f.name} ya existe en {plat_dir.name}/states/")
                    except Exception as exc:
                        errors.append(f"{f.name}: {exc}")
            else:
                target = saves_sub / f.name
                moves_saves.append({"source": str(f), "target": str(target), "platform": plat_dir.name})
                if not dry_run:
                    try:
                        saves_sub.mkdir(parents=True, exist_ok=True)
                        if not target.exists():
                            shutil.move(str(f), target)
                        else:
                            errors.append(f"Conflicto save: {f.name} ya existe en {plat_dir.name}/saves/")
                    except Exception as exc:
                        errors.append(f"{f.name}: {exc}")

    preview = (moves_saves + moves_states)[:40]
    ctx._send_json({
        "dry_run":       dry_run,
        "moves_saves":   len(moves_saves),
        "moves_states":  len(moves_states),
        "errors":        errors,
        "preview":       preview if dry_run else [],
    })
