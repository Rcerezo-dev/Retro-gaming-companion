from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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
    get_repo_fn: Callable[[str], LibraryRepository],
    job_manager: JobManager,
) -> None:
    """Register organize / plan / apply routes on *router*."""
    from rom_manager.web.builders.common import _parse_format_opts
    from rom_manager.web.builders.library import _build_plan

    # ── GET /api/plan ─────────────────────────────────────────────────────────
    @router.get("/api/plan")
    def get_plan(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        opts = _parse_format_opts(qs)
        source_root = qs.get("source_root", [None])[0] or None
        plan_repo = get_repo_fn(source_root or "")
        ctx._send_json(
            _build_plan(
                plan_repo,
                opts,
                frozenset(config.save_extensions),
                source_root=source_root,
                library_root=str(config.library_root) if config.library_root else None,
                config=config,
            )
        )

    # ── POST /api/apply ───────────────────────────────────────────────────────
    @router.post("/api/apply")
    def post_apply(ctx) -> None:
        _do_apply(ctx, ctx._post_data, config, get_repo_fn, job_manager)

    # ── POST /api/fix-platforms ───────────────────────────────────────────────
    @router.post("/api/fix-platforms")
    def post_fix_platforms(ctx) -> None:
        from rom_manager.detection.platform_detector import detect_platform

        updated = repository.backfill_platforms(detect_platform)
        ctx._send_json({"updated": updated})

    # ── POST /api/create-library-structure ────────────────────────────────────
    @router.post("/api/create-library-structure")
    def post_create_library_structure(ctx) -> None:
        _do_create_library_structure(ctx, ctx._post_data, config)

    # ── POST /api/organize-library ────────────────────────────────────────────
    @router.post("/api/organize-library")
    def post_organize_library(ctx) -> None:
        _do_organize_library(ctx, ctx._post_data, config, repository)

    # ── POST /api/migrate-saves-structure ─────────────────────────────────────
    @router.post("/api/migrate-saves-structure")
    def post_migrate_saves_structure(ctx) -> None:
        _do_migrate_saves_structure(ctx, ctx._post_data, config)


# ── Handler logic (moved from server.py) ──────────────────────────────────────


def _do_apply(
    ctx,
    data: dict,
    config: AppConfig,
    get_repo_fn: Callable[[str], LibraryRepository],
    job_manager: JobManager,
) -> None:
    from rom_manager.planner import build_plan
    from rom_manager.planner.operation_planner import FormatOptions

    fmt = data.get("format_opts", {})
    opts = FormatOptions(
        include_region=fmt.get("include_region", True),
        include_revision=fmt.get("include_revision", True),
        include_platform=fmt.get("include_platform", False),
        include_sha=fmt.get("include_sha", False),
        sha_length=min(40, max(4, int(fmt.get("sha_length", 8)))),
    )
    source_root = data.get("source_root") or None
    keep_both = bool(data.get("keep_both", False))

    def run() -> None:
        job_result = None
        try:
            from rom_manager.renamer.file_renamer import central_save_dirs, rename_rom_with_saves
            from rom_manager.scanner.rom_scanner import utc_now

            save_exts = frozenset(config.save_extensions)
            extra_save_dirs = central_save_dirs(config)
            apply_repo = get_repo_fn(source_root or "")
            plan = build_plan(apply_repo, opts, keep_both=keep_both)
            pending_ops = plan.pending
            if source_root:
                root_lower = source_root.lower()
                pending_ops = [
                    op for op in pending_ops if str(op.source_path).lower().startswith(root_lower)
                ]

            total = len(pending_ops)
            renamed = failed = skipped = saves_renamed = 0
            skip_details: list[str] = []
            timestamp = utc_now()
            job_manager.update_progress("apply", {"current": 0, "total": total, "current_file": ""})

            for idx, op in enumerate(pending_ops, 1):
                job_manager.update_progress(
                    "apply", {"current": idx, "total": total, "current_file": op.source_path.name}
                )
                if not op.source_path.exists():
                    skipped += 1
                    skip_details.append(
                        f"{op.source_path.name}: source not found (outdated DB entry)"
                    )
                    continue
                try:
                    bk = config.data_dir if config.backup.saves_enabled else None
                    op.target_path.parent.mkdir(parents=True, exist_ok=True)
                    if op.source_path.suffix.lower() in {".cue", ".gdi"}:
                        from rom_manager.renamer.file_renamer import move_disc_set_to_subfolder

                        outcome = move_disc_set_to_subfolder(
                            op.source_path,
                            op.target_path,
                            save_exts,
                            backup_root=bk,
                            backup_keep_n=config.backup.saves_keep_n,
                            extra_dirs=extra_save_dirs,
                        )
                    else:
                        outcome = rename_rom_with_saves(
                            op.source_path,
                            op.target_path,
                            save_exts,
                            backup_root=bk,
                            backup_keep_n=config.backup.saves_keep_n,
                            extra_dirs=extra_save_dirs,
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
                    renamed += 1
                    saves_renamed += outcome.saves_renamed
                else:
                    err_lower = outcome.error.lower()
                    if "not found" in err_lower or "no such file" in err_lower:
                        skipped += 1
                    else:
                        failed += 1
                    skip_details.append(f"{op.source_path.name}: {outcome.error}")

            job_result = {
                "renamed": renamed,
                "failed": failed,
                "skipped": skipped,
                "saves_renamed": saves_renamed,
                "conflicts": len(plan.conflicts),
                "skip_details": skip_details[:20],
                "error_details": skip_details[:50],
                "result_ts": utc_now(),
            }
        except Exception as exc:
            job_result = {"error": str(exc), "result_ts": ""}
        finally:
            job_manager.finish("apply", job_result)

    ctx._send_json(job_manager.start("apply", run))


def _do_create_library_structure(ctx, data: dict, config: AppConfig) -> None:
    if not config.library_root:
        ctx._send_json({"error": "library_root no configurado"})
        return

    from rom_manager.web.handlers.system import _STANDARD_PLATFORM_FOLDERS

    std_folders = _STANDARD_PLATFORM_FOLDERS
    also_android = bool(data.get("also_android"))
    android_root_str = config.anbernic_root or None

    def _create_tree(root: Path) -> tuple[list[str], list[str]]:
        created: list[str] = []
        skipped: list[str] = []

        def _ensure(r_d: Path, label: str):
            if not r_d.exists():
                r_d.mkdir(parents=True, exist_ok=True)
                created.append(label)
            else:
                skipped.append(label)

        # 1. Rutas base
        for special in ("saves", "media", "configs", "bios", "inbox", "screenshots"):
            _ensure(root / special, special)

        _ensure(root / "bios" / "wii", "bios/wii")
        _ensure(root / "bios" / "shaders", "bios/shaders")

        # 2. Rutas por plataforma
        for folder in std_folders:
            _ensure(root / folder, folder)
            _ensure(root / "saves" / folder, f"saves/{folder}")
            _ensure(root / "saves" / folder / "states", f"saves/{folder}/states")
            _ensure(root / "media" / folder / "images", f"media/{folder}/images")
            _ensure(root / "media" / folder / "videos", f"media/{folder}/videos")
            _ensure(root / "configs" / folder, f"configs/{folder}")

        return created, skipped

    pc_root = Path(config.library_root)
    pc_created, pc_skipped = _create_tree(pc_root)

    android_result: dict = {}
    if also_android and android_root_str:
        android_root = Path(android_root_str)
        if android_root.exists():
            ab_created, ab_skipped = _create_tree(android_root)
            android_result = {
                "root": str(android_root),
                "created": ab_created,
                "skipped": ab_skipped,
            }
        else:
            android_result = {
                "root": str(android_root),
                "error": "Ruta no accesible — conecta la tarjeta SD o el dispositivo primero",
            }

    ctx._send_json(
        {
            "created": pc_created,
            "skipped": pc_skipped,
            "root": str(pc_root),
            "android": android_result,
        }
    )


def _do_organize_library(
    ctx,
    data: dict,
    config: AppConfig,
    repository: LibraryRepository,
) -> None:
    """Move ROMs → platform folders, saves → saves/{platform}/, BIOS candidates → bios/."""
    import shutil

    from rom_manager.web.builders.common import _utc_now_str
    from rom_manager.web.handlers.system import _ES_PLATFORM_FOLDERS

    es_folders = _ES_PLATFORM_FOLDERS
    dry_run = data.get("dry_run", True)
    if not config.library_root:
        ctx._send_json({"error": "library_root no configurado"})
        return

    root = Path(config.library_root)
    saves_dir = root / "saves"
    bios_dir = root / "bios"

    save_exts = frozenset(
        getattr(
            config,
            "save_extensions",
            [
                ".sav",
                ".srm",
                ".state",
                ".ogg",
                ".rtc",
            ],
        )
    )
    _known_bios_names = frozenset(
        {
            "scph1001.bin",
            "scph5500.bin",
            "scph5501.bin",
            "scph5502.bin",
            "scph7001.bin",
            "scph7502.bin",
            "scph10000.bin",
            "bios_CD_E.bin",
            "bios_CD_J.bin",
            "bios_CD_U.bin",
            "dc_boot.bin",
            "dc_flash.bin",
            "gba_bios.bin",
            "bios7.bin",
            "bios9.bin",
            "firmware.bin",
            "ym2608_adpcm_rom.bin",
        }
    )

    moves_roms: list[dict] = []
    moves_saves: list[dict] = []
    moves_bios: list[dict] = []
    errors: list[str] = []

    # 1. ROMs + their associated saves
    with repository.connect() as conn:
        rows = conn.execute(
            "SELECT id, source_path, platform FROM games WHERE source_path IS NOT NULL"
        ).fetchall()

    with repository.batch() as batch_conn:
        for row in rows:
            _game_id, src_str, platform = row[0], row[1], row[2] or ""
            src = Path(src_str)
            if not src.exists():
                continue
            es_folder = es_folders.get(platform, "")
            if not es_folder:
                continue
            target_dir = root / es_folder
            target = target_dir / src.name
            if src != target:
                moves_roms.append(
                    {
                        "source": str(src),
                        "target": str(target),
                        "platform": platform,
                        "filename": src.name,
                    }
                )
                if not dry_run:
                    try:
                        target_dir.mkdir(parents=True, exist_ok=True)
                        if target.exists():
                            errors.append(f"Conflicto ROM: {src.name} ya existe en {es_folder}/")
                        else:
                            shutil.move(str(src), str(target))
                            batch_conn.execute(
                                "UPDATE games SET source_path = ?, updated_at = ? WHERE source_path = ?",
                                (str(target), _utc_now_str(), src_str),
                            )
                    except Exception as exc:
                        errors.append(f"ROM {src.name}: {exc}")

            # Move sibling saves → saves/{platform}/
            plat_save_dir = saves_dir / es_folder if es_folder else saves_dir
            for save_ext in save_exts:
                sibling = src.with_suffix(save_ext)
                if sibling.exists() and sibling.parent != plat_save_dir:
                    save_target = plat_save_dir / sibling.name
                    moves_saves.append(
                        {
                            "source": str(sibling),
                            "target": str(save_target),
                            "platform": platform,
                        }
                    )
                    if not dry_run:
                        try:
                            plat_save_dir.mkdir(parents=True, exist_ok=True)
                            if not save_target.exists():
                                shutil.move(str(sibling), str(save_target))
                        except Exception as exc:
                            errors.append(f"Save {sibling.name}: {exc}")

    # 2. Flat saves/ → saves/{platform}/ (saves already in saves/ root, not yet in subfolders)
    if saves_dir.exists():
        stem_to_folder: dict[str, tuple[str, str]] = {}
        for row in rows:
            _, src_str, plat = row[0], row[1], row[2] or ""
            es_f = es_folders.get(plat, "")
            if src_str and es_f:
                stem_to_folder.setdefault(Path(src_str).stem.lower(), (plat, es_f))

        for save_file in saves_dir.iterdir():
            if not save_file.is_file():
                continue
            if save_file.suffix.lower() not in save_exts:
                continue
            match_ = stem_to_folder.get(save_file.stem.lower())
            if not match_:
                continue
            plat_name, es_f = match_
            plat_save_dir = saves_dir / es_f
            save_target = plat_save_dir / save_file.name
            if save_file == save_target:
                continue
            moves_saves.append(
                {"source": str(save_file), "target": str(save_target), "platform": plat_name}
            )
            if not dry_run:
                try:
                    plat_save_dir.mkdir(parents=True, exist_ok=True)
                    if not save_target.exists():
                        shutil.move(str(save_file), str(save_target))
                    else:
                        errors.append(
                            f"Conflicto save: {save_file.name} ya existe en saves/{es_f}/"
                        )
                except Exception as exc:
                    errors.append(f"Save {save_file.name}: {exc}")

    # 4. BIOS candidates
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
        moves_bios.append(
            {"source": str(candidate), "target": str(bios_target), "filename": candidate.name}
        )
        if not dry_run:
            try:
                bios_dir.mkdir(parents=True, exist_ok=True)
                if not bios_target.exists():
                    shutil.move(str(candidate), str(bios_target))
            except Exception as exc:
                errors.append(f"BIOS {candidate.name}: {exc}")

    total_preview = (moves_roms + moves_saves + moves_bios)[:40]
    ctx._send_json(
        {
            "dry_run": dry_run,
            "moves_roms": len(moves_roms),
            "moves_saves": len(moves_saves),
            "moves_bios": len(moves_bios),
            "errors": errors,
            "preview": total_preview if dry_run else [],
        }
    )


def _do_migrate_saves_structure(ctx, data: dict, config: AppConfig) -> None:
    """Migrate the entire root directory to the new standard format:
    - Normalizes folders (Game Boy Advance -> gba, ss -> saturn)
    - Moves states to saves/<plataforma>/states
    - Moves saves to saves/<plataforma>
    - Moves media to media/<plataforma>/{images,videos}
    - Moves configs to configs/<plataforma>
    - Moves shaders/sys files to bios/shaders
    """
    import shutil

    dry_run = bool(data.get("dry_run", True))
    if not config.library_root:
        ctx._send_json({"error": "library_root no configurado"})
        return

    root = Path(config.library_root)
    save_exts = frozenset(config.save_extensions)
    state_exts = frozenset(config.state_extensions)

    moves: list[dict] = []
    errors: list[str] = []

    # Map of folders to rename/merge
    folder_aliases = {"Game Boy Advance": "gba", "ss": "saturn", "Saturn": "saturn"}

    def _add_move(src: Path, dst: Path, cat: str):
        moves.append({"source": str(src), "target": str(dst), "category": cat})
        if not dry_run:
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if not dst.exists():
                    shutil.move(str(src), dst)
                else:
                    errors.append(f"Conflicto {cat}: {src.name} ya existe en {dst.parent.name}")
            except Exception as exc:
                errors.append(f"{src.name}: {exc}")

    # 1. Sweep platforms and sort bad files
    for plat_dir in list(root.iterdir()):
        if not plat_dir.is_dir() or plat_dir.name in (
            "saves",
            "states",
            "bios",
            "inbox",
            "screenshots",
            "media",
            "configs",
            "_descartados",
        ):
            continue

        actual_plat = plat_dir.name
        is_alias = actual_plat in folder_aliases
        target_plat = folder_aliases[actual_plat] if is_alias else actual_plat

        for f in list(plat_dir.iterdir()):
            if not f.is_file():
                continue
            ext = f.suffix.lower()
            name = f.name.lower()

            if ext in state_exts:
                _add_move(f, root / "saves" / target_plat / "states" / f.name, "states")
            elif ext in save_exts:
                _add_move(f, root / "saves" / target_plat / f.name, "saves")
            elif ext == ".mp4":
                _add_move(f, root / "media" / target_plat / "videos" / f.name, "media")
            elif ext in (".png", ".jpg", ".jpeg"):
                _add_move(f, root / "media" / target_plat / "images" / f.name, "media")
            elif ext == ".cfg":
                _add_move(f, root / "configs" / target_plat / f.name, "config")
            elif (
                actual_plat == "arcade"
                and ext == ".bin"
                and (name.startswith("fs_") or name.startswith("vs_"))
            ):
                _add_move(f, root / "bios" / "shaders" / f.name, "bios")
            elif (
                actual_plat == "wii"
                and ext == ".bin"
                and name
                in (
                    "fst.bin",
                    "misc.bin",
                    "nwc24dl.bin",
                    "nwc24fl.bin",
                    "nwc24fls.bin",
                    "wiimmfi.bin",
                )
            ):
                _add_move(f, root / "bios" / "wii" / f.name, "bios")
            elif is_alias:
                # If it's a valid ROM in an alias folder, move to standard folder
                _add_move(f, root / target_plat / f.name, "folder_merge")

    # 2. Legacy states folder cleanup
    old_states = root / "states"
    if old_states.exists() and old_states.is_dir():
        for plat_dir in old_states.iterdir():
            if plat_dir.is_dir():
                for f in plat_dir.iterdir():
                    if f.is_file():
                        _add_move(
                            f, root / "saves" / plat_dir.name / "states" / f.name, "states_legacy"
                        )

    ctx._send_json(
        {
            "dry_run": dry_run,
            "moves_total": len(moves),
            "errors": errors,
            "preview": moves[:40] if dry_run else [],
        }
    )
