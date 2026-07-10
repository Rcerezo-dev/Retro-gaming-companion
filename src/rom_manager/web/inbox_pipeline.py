"""Inbox (Pilar 2) and setup wizard pipeline functions.

Extracted from server.py (Session 19). Progress/state is reported through the
``JobManager`` passed in by the caller; this module no longer imports ``server``.
"""

from __future__ import annotations

import logging
from pathlib import Path

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository
from rom_manager.detection.platform_detector import PLATFORM_BY_FOLDER
from rom_manager.web.handlers.system import _ES_PLATFORM_FOLDERS

_logger = logging.getLogger(__name__)


def _same_content(a: Path, b: Path) -> bool:
    """True only if *a* and *b* are byte-identical (size check first, then SHA1).

    A shared filename is NOT evidence of duplicate content — two different ROM
    dumps/revisions can legitimately share a name. Never delete on a filename
    match alone (INBOX-FIX-5).
    """
    from rom_manager.hashing.hash_calculator import calculate_hashes

    try:
        if a.stat().st_size != b.stat().st_size:
            return False
        return calculate_hashes(a).sha1 == calculate_hashes(b).sha1
    except OSError:
        return False


# ── Inbox (Pilar 2) ───────────────────────────────────────────────────────────

_DISC_EXTENSIONS_INBOX = frozenset({".cue", ".bin", ".iso", ".img", ".mdf", ".mds", ".ccd", ".chd"})
_ROM_EXTENSIONS_INBOX = frozenset(
    {
        ".nes",
        ".sfc",
        ".smc",
        ".n64",
        ".z64",
        ".v64",
        ".gb",
        ".gbc",
        ".gba",
        ".nds",
        ".3ds",
        ".cia",
        ".gcm",
        ".wbfs",
        ".sms",
        ".gg",
        ".gen",
        ".pbp",
        ".cso",
        ".a26",
        ".a52",
        ".a78",
        ".lnx",
        ".j64",
        ".jag",
        ".md",
    }
)

_KNOWN_BIOS_MAP: dict[str, str] = {
    # Sony
    "scph1001.bin": "psx",
    "scph5500.bin": "psx",
    "scph5501.bin": "psx",
    "scph5502.bin": "psx",
    "scph7001.bin": "psx",
    "scph7502.bin": "psx",
    "psxonpsp660.bin": "psx",
    "scph10000.bin": "ps2",
    "scph39001.bin": "ps2",
    "scph39001.mec": "ps2",
    # Sega
    "bios_cd_e.bin": "segacd",
    "bios_cd_j.bin": "segacd",
    "bios_cd_u.bin": "segacd",
    "dc_boot.bin": "dreamcast",
    "dc_flash.bin": "dreamcast",
    "mpr-17933.bin": "saturn",
    "mpr-18811-mx.ic1": "saturn",
    "mpr-19367-mx.ic1": "saturn",
    "sega_101.bin": "saturn",
    "stvbios.zip": "saturn",
    "qtsza.bin": "saturn",
    "bios.gg": "gamegear",
    # Nintendo
    "gba_bios.bin": "gba",
    "bios7.bin": "nds",
    "bios9.bin": "nds",
    "firmware.bin": "nds",
    "fst.bin": "wii",
    "misc.bin": "wii",
    "sysconf": "wii",
    "wiimmfi.bin": "wii",
    "nwc24dl.bin": "wii",
    "nwc24fl.bin": "wii",
    "nwc24fls.bin": "wii",
    "disksys.rom": "fds",
    "sgb_bios.bin": "snes",
    "sgb2_bios.bin": "snes",
    "bios.min": "pokemini",
    # PC Engine / NEC
    "syscard3.pce": "pcenginecd",
    "syscard2.pce": "pcenginecd",
    "syscard1.pce": "pcenginecd",
    "pcfx.rom": "pcfx",
    # Otros
    "ym2608_adpcm_rom.bin": "neogeocd",
    "neogeo.zip": "neogeo",
    "kick34005.a500": "amiga",
    "kick40063.a600": "amiga",
    "kick40068.a1200": "amiga",
    "kick40068.a4000": "amiga",
    "coleco.rom": "colecovision",
    "exec.bin": "intellivision",
    "grom.bin": "intellivision",
    "awbios.zip": "naomi",
    "naomi_boot.bin": "naomi",
    # Arcade system BIOS (INBOX-FIX-3 — hallados sueltos en Unknown\ en JUNK-REVIEW-1;
    # slug = nombre del propio ZIP, ya que cada uno es un sistema arcade distinto)
    "naomi.zip": "naomi",
    "chihiro.zip": "chihiro",
    "triforce.zip": "triforce",
    "hikaru.zip": "hikaru",
    "aristmk5.zip": "aristmk5",
    "aristmk6.zip": "aristmk6",
    "hod2bios.zip": "hod2bios",
    "lindbios.zip": "lindbios",
    "f355bios.zip": "f355bios",
    "galgbios.zip": "galgbios",
    "airlbios.zip": "airlbios",
    "ar_bios.zip": "ar_bios",
    "cdibios.zip": "cdibios",
    "macsbios.zip": "macsbios",
    "alg_bios.zip": "alg_bios",
    "crysbios.zip": "crysbios",
    "v4bios.zip": "v4bios",
}


def _intercept_bios_files(inbox: Path, target_root: Path, logger: logging.Logger) -> int:
    """Move known BIOS files out of *inbox* into ``target_root/bios/<slug>/``.

    Shared by both the Inbox pipeline and the first-time setup wizard so BIOS
    routing doesn't depend on which pipeline happened to touch the library
    (INBOX-FIX-3 — the setup wizard never ran this step before).
    """
    import shutil as _shutil

    bios_moved = 0
    for ext_file in list(inbox.rglob("*")):
        if not ext_file.is_file():
            continue
        if any(part.startswith("_") for part in ext_file.relative_to(inbox).parts[:-1]):
            continue
        name_lower = ext_file.name.lower()
        if name_lower in _KNOWN_BIOS_MAP:
            plat = _KNOWN_BIOS_MAP[name_lower]
            dst = target_root / "bios" / plat / ext_file.name
            if ext_file.resolve() == dst.resolve():
                continue  # already in place (e.g. setup wizard re-scanning target_root == inbox)
            if dst.exists():
                # INBOX-FIX-5: same filename is not proof of duplicate content —
                # only delete the source if it's byte-identical to what's there.
                if _same_content(ext_file, dst):
                    ext_file.unlink()
                    bios_moved += 1
                    logger.info("BIOS duplicada (mismo contenido): %s eliminada", ext_file.name)
                else:
                    logger.warning(
                        "BIOS %s ya existe en bios/%s con contenido distinto — no se toca, revisar a mano",
                        ext_file.name,
                        plat,
                    )
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            _shutil.move(str(ext_file), dst)
            bios_moved += 1
            logger.info("BIOS interceptada: %s -> bios/%s", ext_file.name, plat)
    return bios_moved


def _build_inbox_scan(inbox_path_str: str) -> dict:
    """Scan the inbox folder and return summary + file list."""
    import zipfile as _zf

    from rom_manager.detection.platform_detector import detect_platform as _detect_platform

    inbox = Path(inbox_path_str).resolve()
    if not inbox.exists() or not inbox.is_dir():
        return {"error": f"Carpeta no encontrada: {inbox_path_str}", "files": [], "total": 0}

    files_out: list[dict] = []
    total_bytes = 0
    by_platform: dict[str, int] = {}
    zips = 0
    unrecognized = 0

    for entry in sorted(inbox.iterdir()):
        # Skip hidden files and internal subfolders (_extracted, _processed)
        if entry.name.startswith(".") or entry.name.startswith("_"):
            continue
        if entry.is_dir():
            continue
        if not entry.is_file():
            continue

        ext = entry.suffix.lower()
        size_bytes = 0
        try:
            size_bytes = entry.stat().st_size
        except OSError:
            pass
        total_bytes += size_bytes

        # Determine type
        if ext == ".zip":
            file_type = "zip"
            zips += 1
            # Peek inside ZIP to guess platform
            platform_guess = None
            try:
                with _zf.ZipFile(entry, "r") as zobj:
                    names = zobj.namelist()
                    for inner in names:
                        inner_ext = Path(inner).suffix.lower()
                        if inner_ext in _DISC_EXTENSIONS_INBOX:
                            file_type = "zip"  # remains zip but disc content
                            break
                        if (
                            inner_ext in _ROM_EXTENSIONS_INBOX
                            or inner_ext in _DISC_EXTENSIONS_INBOX
                        ):
                            inner_path = inbox / inner
                            platform_guess = _detect_platform(inner_path)
                            if platform_guess:
                                break
                    # If still no guess, try folder context from zip name
                    if not platform_guess:
                        platform_guess = _detect_platform(entry)
            except Exception:
                _logger.debug(
                    "Inspección de ZIP para detectar plataforma falló: %s", entry, exc_info=True
                )
                platform_guess = _detect_platform(entry)
            needs_extraction = True
        elif ext in _DISC_EXTENSIONS_INBOX:
            file_type = "disc_image"
            platform_guess = _detect_platform(entry)
            needs_extraction = False
        elif ext in _ROM_EXTENSIONS_INBOX:
            file_type = "rom"
            platform_guess = _detect_platform(entry)
            needs_extraction = False
        else:
            file_type = "unknown"
            platform_guess = None
            unrecognized += 1
            needs_extraction = False

        if platform_guess:
            by_platform[platform_guess] = by_platform.get(platform_guess, 0) + 1

        files_out.append(
            {
                "name": entry.name,
                "path": str(entry),
                "size_bytes": size_bytes,
                "type": file_type,
                "platform_guess": platform_guess,
                "needs_extraction": needs_extraction,
            }
        )

    return {
        "files": files_out,
        "total": len(files_out),
        "total_bytes": total_bytes,
        "by_platform": by_platform,
        "zips": zips,
        "unrecognized": unrecognized,
        "inbox_path": str(inbox),
    }


def _run_setup_pipeline(
    library_root: str,
    options: dict,
    repository: LibraryRepository,
    config: AppConfig,
    job_manager,
) -> None:
    """Background job: first-time setup wizard pipeline (junk → zip → scan → match → plan)."""
    from rom_manager.catalog.matcher import CatalogMatcher
    from rom_manager.converters.zip_extractor import extract_zip, find_zip_files
    from rom_manager.planner import build_plan
    from rom_manager.planner.operation_planner import FormatOptions
    from rom_manager.scanner import scan_library
    from rom_manager.web.builders.folders import _build_junk_scan

    logger = _logger
    source = Path(library_root).resolve()
    job_result = None

    def _upd(step: str, step_num: int, pct: int = 0, current_file: str = "") -> None:
        job_manager.update_progress(
            "setup",
            {
                "step": step,
                "step_num": step_num,
                "total_steps": 5,
                "current_file": current_file,
                "pct": pct,
            },
        )

    result: dict = {
        "junk_deleted": 0,
        "junk_freed_bytes": 0,
        "zips_extracted": 0,
        "bios_moved": 0,
        "games_found": 0,
        "games_matched": 0,
        "plan_pending": 0,
    }

    try:
        # ── Step 1: Junk cleaning ────────────────────────────────────────────
        _upd("Limpiando archivos no relacionados", 1, 5)
        if options.get("clean_junk", False):
            junk_data = _build_junk_scan(str(source))
            if "categories" in junk_data:
                all_junk: list[str] = []
                for cat in junk_data["categories"]:
                    all_junk.extend(f["full_path"] for f in cat.get("files", []))
                deleted = freed = 0
                for fp in all_junk:
                    try:
                        p = Path(fp)
                        if p.is_file():
                            sz = p.stat().st_size
                            p.unlink()
                            deleted += 1
                            freed += sz
                    except OSError:
                        pass
                result["junk_deleted"] = deleted
                result["junk_freed_bytes"] = freed

        # ── Step 2: ZIP extraction ───────────────────────────────────────────
        _upd("Extrayendo ZIPs", 2, 20)
        if options.get("extract_zips", True):
            zip_files = find_zip_files(source)
            extracted = 0
            total_zips = len(zip_files)
            for idx, zp in enumerate(zip_files, 1):
                try:
                    rel = str(zp.relative_to(source))
                except ValueError:
                    rel = zp.name
                pct = 20 + int((idx / max(total_zips, 1)) * 15)
                _upd("Extrayendo ZIPs", 2, pct, rel)
                r = extract_zip(zp, dry_run=False, delete_source=options.get("delete_zips", False))
                if r.success:
                    extracted += 1
            result["zips_extracted"] = extracted

        # ── Step 2.5: Intercept BIOS files (INBOX-FIX-3) ─────────────────────
        _upd("Moviendo BIOS conocidas", 2, 35)
        result["bios_moved"] = _intercept_bios_files(source, source, logger)

        # ── Step 3: Scan library ─────────────────────────────────────────────
        _upd("Escaneando biblioteca", 3, 35)
        if options.get("scan", True):

            def _scan_cb(files_seen: int, roms: int, current_file: str = "") -> None:
                _upd(
                    "Escaneando biblioteca",
                    3,
                    35 + min(25, int(roms / max(files_seen, 1) * 25)),
                    current_file,
                )

            scan_r = scan_library(
                source, config, repository, logger, quick=False, progress_cb=_scan_cb
            )
            result["games_found"] = scan_r.roms_detected

        # ── Step 4: Catalog match ────────────────────────────────────────────
        _upd("Cruzando con catálogos No-Intro/Redump", 4, 65)
        if options.get("match", True):
            matcher = CatalogMatcher(
                nointro_dir=config.catalogs_nointro_dir,
                redump_dir=config.catalogs_redump_dir,
            )
            unresolved = repository.get_unresolved_games()
            matched = 0
            total_unresolved = len(unresolved)
            with repository.batch() as conn:
                for idx, game in enumerate(unresolved, 1):
                    pct = 65 + int((idx / max(total_unresolved, 1)) * 20)
                    _upd("Cruzando con catálogos No-Intro/Redump", 4, pct, game.original_filename)
                    m = matcher.match(game.sha1, game.original_filename)
                    if m is not None:
                        repository.update_match(
                            game.source_path,
                            canonical_title=m.title,
                            match_confidence=m.confidence,
                            catalog_source=m.catalog_source,
                            platform=m.platform,
                            connection=conn,
                        )
                        matched += 1
            result["games_matched"] = matched

        # ── Step 5: Build plan ───────────────────────────────────────────────
        _upd("Preparando plan de renombrado", 5, 90)
        opts = FormatOptions()
        plan = build_plan(repository, opts)
        result["plan_pending"] = len(plan.pending)

        _upd("Completado", 5, 100)
        from rom_manager.scanner.rom_scanner import utc_now as _utc_now

        result["result_ts"] = _utc_now()
        job_result = result

    except Exception as exc:
        job_result = {"error": str(exc)}
        logger.exception("Setup pipeline error: %s", exc)
    finally:
        job_manager.finish("setup", job_result)


def _run_inbox_pipeline(
    inbox_path_str: str,
    target_root_str: str,
    delete_source: bool,
    repository: LibraryRepository,
    config: AppConfig,
    job_manager,
    extra_result: dict | None = None,
) -> None:
    """Background job: extract → scan → match → plan → rename → move → cleanup.

    *extra_result* (ZIP-ROUTE-4): contadores de las fases previas del zip_router
    que se mezclan en el resultado del job para que la UI los muestre juntos.
    """
    import shutil as _shutil

    from rom_manager.catalog.matcher import CatalogMatcher
    from rom_manager.converters.zip_extractor import extract_zip, find_zip_files
    from rom_manager.planner import build_plan
    from rom_manager.planner.operation_planner import FormatOptions
    from rom_manager.renamer.file_renamer import rename_rom_with_saves
    from rom_manager.scanner import scan_library
    from rom_manager.scanner.rom_scanner import utc_now

    inbox = Path(inbox_path_str).resolve()
    target_root = (
        Path(target_root_str).resolve() if target_root_str else (config.library_root or inbox)
    )

    logger = _logger
    job_result = None

    def _upd(
        step: str, step_num: int, processed: int = 0, total: int = 0, current_file: str = ""
    ) -> None:
        job_manager.update_progress(
            "inbox",
            {
                "step": step,
                "step_num": step_num,
                "total_steps": 6,
                "current_file": current_file,
                "processed": processed,
                "total": total,
            },
        )

    try:
        # ── Step 1: Extract ZIPs ─────────────────────────────────────────────
        _upd("extracting", 1)
        zip_files = find_zip_files(inbox)
        extracted_count = 0
        source_zips: list[Path] = []
        for idx, zp in enumerate(zip_files, 1):
            # Skip internal folders
            if any(part.startswith("_") for part in zp.relative_to(inbox).parts[:-1]):
                continue
            _upd("extracting", 1, idx, len(zip_files), zp.name)
            result = extract_zip(zp, delete_source=False, dry_run=False)
            if result.success:
                extracted_count += 1
                source_zips.append(zp)
            else:
                logger.info(
                    "Inbox: skipped ZIP %s — %s", zp.name, result.skipped_reason or result.error
                )

        # ── Step 1.5: Intercept BIOS files ───────────────────────────────────
        _upd("intercepting bios", 1)
        bios_moved = _intercept_bios_files(inbox, target_root, logger)

        # ── Step 2: Scan inbox ───────────────────────────────────────────────
        _upd("scanning", 2)

        def _scan_progress_cb(files_seen: int, roms: int, current_file: str = "") -> None:
            _upd("scanning", 2, files_seen, 0, current_file)

        scan_result = scan_library(
            inbox,
            config,
            repository,
            logger,
            quick=False,
            progress_cb=_scan_progress_cb,
        )
        logger.info("Inbox scan: %d ROMs found", scan_result.roms_detected)

        # ── Step 3: Match catalog ────────────────────────────────────────────
        _upd("matching", 3)
        matcher = CatalogMatcher(
            nointro_dir=config.catalogs_nointro_dir,
            redump_dir=config.catalogs_redump_dir,
        )
        unresolved = repository.get_unresolved_games()
        matched = 0
        with repository.batch() as conn:
            for idx, game in enumerate(unresolved, 1):
                _upd("matching", 3, idx, len(unresolved), game.original_filename)
                match_result = matcher.match(game.sha1, game.original_filename)
                if match_result is not None:
                    repository.update_match(
                        game.source_path,
                        canonical_title=match_result.title,
                        match_confidence=match_result.confidence,
                        catalog_source=match_result.catalog_source,
                        platform=match_result.platform,
                        connection=conn,
                    )
                    matched += 1

        # ── Step 4: Build plan ───────────────────────────────────────────────
        _upd("planning", 4)
        opts = FormatOptions()
        plan = build_plan(repository, opts)
        inbox_str_lower = str(inbox).lower()
        pending_ops = [
            op for op in plan.pending if str(op.source_path).lower().startswith(inbox_str_lower)
        ]
        logger.info("Inbox plan: %d operations", len(pending_ops))

        # ── Step 5: Apply renames ────────────────────────────────────────────
        _upd("renaming", 5, 0, len(pending_ops))
        save_exts = frozenset(config.save_extensions)
        timestamp = utc_now()
        renamed = 0
        rename_errors: list[str] = []
        for idx, op in enumerate(pending_ops, 1):
            _upd("renaming", 5, idx, len(pending_ops), op.source_path.name)
            if not op.source_path.exists():
                continue
            try:
                outcome = rename_rom_with_saves(op.source_path, op.target_path, save_exts)
                if outcome.success:
                    repository.apply_rename(
                        game_id=op.game.id,
                        old_source_path=str(op.source_path),
                        new_source_path=str(op.target_path),
                        new_filename=op.target_path.name,
                        timestamp=timestamp,
                    )
                    renamed += 1
                else:
                    rename_errors.append(f"{op.source_path.name}: {outcome.error}")
            except Exception as exc:
                rename_errors.append(f"{op.source_path.name}: {exc}")

        # ── Step 6: Move to platform folders ─────────────────────────────────
        _upd("organizing", 6, 0, 0)
        organized = 0
        organize_errors: list[str] = []

        # Get fresh game list from inbox area to move
        with repository.connect() as conn:
            rows = conn.execute(
                "SELECT id, source_path, platform, original_filename FROM games "
                "WHERE LOWER(source_path) LIKE ?",
                (inbox_str_lower + "%",),
            ).fetchall()

        for idx, row in enumerate(rows, 1):
            game_id, source_path_str_db, platform, orig_name = row
            source_file = Path(source_path_str_db)
            if not source_file.exists():
                continue

            canonical = PLATFORM_BY_FOLDER.get((platform or "").lower(), platform or "")
            folder_name = _ES_PLATFORM_FOLDERS.get(canonical, "unknown")
            dest_folder = target_root / folder_name
            dest_folder.mkdir(parents=True, exist_ok=True)
            dest_file = dest_folder / source_file.name

            _upd("organizing", 6, idx, len(rows), source_file.name)

            # Dest already exists — only treat as a duplicate if the content
            # actually matches (INBOX-FIX-5). A shared filename alone is not
            # proof: different dumps/revisions/regions can share a name, and
            # deleting the wrong one destroys data with no way back.
            if dest_file.exists():
                if _same_content(source_file, dest_file):
                    try:
                        source_file.unlink()
                        repository.delete_game(game_id)
                        logger.info(
                            "Inbox: removed exact duplicate %s (already in %s)",
                            source_file.name,
                            dest_folder,
                        )
                    except Exception as exc:
                        organize_errors.append(
                            f"{source_file.name}: duplicado exacto en destino, no se pudo eliminar fuente — {exc}"
                        )
                else:
                    organize_errors.append(
                        f"{source_file.name}: mismo nombre en {dest_folder} pero contenido distinto "
                        "— no se toca, revisar a mano"
                    )
                continue

            try:
                _shutil.move(str(source_file), str(dest_file))
                # Update DB path
                with repository.batch() as conn:
                    conn.execute(
                        "UPDATE games SET source_path=?, original_filename=? WHERE id=?",
                        (str(dest_file.resolve()), dest_file.name, game_id),
                    )
                organized += 1
            except Exception as exc:
                organize_errors.append(f"{source_file.name}: {exc}")

        # ── Cleanup ───────────────────────────────────────────────────────────
        # B6-5: always move processed ZIPs out of the active inbox area so they
        # are not re-extracted on subsequent runs. _processed/ starts with '_'
        # and is already excluded from ZIP scanning (line 347 filter).
        # If delete_source=True, delete them outright instead.
        processed_dir = inbox / "_processed"
        for zp in source_zips:
            if not zp.exists():
                continue
            try:
                if delete_source:
                    zp.unlink()
                else:
                    processed_dir.mkdir(parents=True, exist_ok=True)
                    dest_zp = processed_dir / zp.name
                    if dest_zp.exists():
                        zp.unlink()  # duplicate — already archived
                    else:
                        _shutil.move(str(zp), dest_zp)
            except Exception:
                _logger.warning("No se pudo archivar el ZIP procesado: %s", zp, exc_info=True)

        # Remove _extracted temp folder if empty
        extracted_dir = inbox / "_extracted"
        if extracted_dir.exists():
            try:
                extracted_dir.rmdir()
            except Exception:
                _logger.debug("No se pudo eliminar la carpeta temporal _extracted", exc_info=True)

        job_result = {
            **(extra_result or {}),
            "result_ts": utc_now(),
            "zips_extracted": extracted_count,
            "zips_archived": len(source_zips),
            "bios_moved": bios_moved,
            "roms_scanned": scan_result.roms_detected,
            "matched": matched,
            "renamed": renamed,
            "organized": organized,
            "rename_errors": rename_errors[:20],
            "organize_errors": organize_errors[:20],
            "target_root": str(target_root),
        }

    except Exception as exc:
        logger.exception("Inbox pipeline error: %s", exc)
        job_result = {"error": str(exc), "result_ts": ""}
    finally:
        job_manager.finish("inbox", job_result)


def _watcher_now() -> str:
    import datetime as _dt_mod

    return _dt_mod.datetime.now(_dt_mod.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
