from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from rom_manager.sync import cable_engine

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router


_logger = logging.getLogger(__name__)


def register_cable(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    job_manager: JobManager,
) -> None:
    """Register ADB / cable-sync routes on *router*."""

    # ── GET /api/adb-devices ─────────────────────────────────────────────────
    @router.get("/api/adb-devices")
    def get_adb_devices(ctx) -> None:
        try:
            from rom_manager.sync.adb_transport import list_devices

            devs = list_devices(config.adb)
            ctx._send_json(
                {
                    "devices": [
                        {
                            "serial": d.serial,
                            "state": d.state,
                            "model": d.model,
                            "product": d.product,
                            "ready": d.ready,
                            "display": d.display,
                        }
                        for d in devs
                    ],
                    "adb_path": config.adb,
                }
            )
        except RuntimeError as exc:
            ctx._send_json({"error": str(exc), "devices": []})

    # ── GET /api/test-adb-path ───────────────────────────────────────────────
    @router.get("/api/test-adb-path")
    def get_test_adb_path(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        serial = qs.get("serial", [""])[0]
        ap = qs.get("path", ["/storage/emulated/0"])[0]
        if not serial:
            ctx._send_json({"accessible": False, "error": "serial requerido"})
        else:
            try:
                from rom_manager.sync.adb_transport import AdbTransport

                t = AdbTransport(config.adb, serial)
                ctx._send_json(t.test_path(ap))
            except Exception as exc:
                ctx._send_json({"accessible": False, "error": str(exc)})

    # ── GET /api/sync-doctor (AUD-1) ─────────────────────────────────────────
    @router.get("/api/sync-doctor")
    def get_sync_doctor(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        serial = qs.get("serial", [""])[0].strip()
        android_path = qs.get("android_path", [""])[0].strip() or config.sync.auto_sync_android_path
        pc_path = qs.get("pc_path", [""])[0].strip() or (
            str(config.library_root) if config.library_root else ""
        )
        quick = qs.get("quick", ["0"])[0] == "1"
        if not serial:
            ctx._send_json({"error": "serial requerido"})
            return
        try:
            ctx._send_json(
                _build_sync_doctor(config, repository, serial, android_path, pc_path, quick=quick)
            )
        except Exception as exc:
            ctx._send_json({"error": str(exc)})

    # ── GET /api/sync-log ────────────────────────────────────────────────────
    @router.get("/api/sync-log")
    def get_sync_log(ctx) -> None:
        from rom_manager.web.builders.misc import _build_sync_log

        ctx._send_json(_build_sync_log(repository))

    # ── GET /api/cable-sync-preview ──────────────────────────────────────────
    @router.get("/api/cable-sync-preview")
    def get_cable_sync_preview(ctx) -> None:
        from rom_manager.web.builders.misc import _build_cable_sync_preview

        ctx._send_json(_build_cable_sync_preview(getattr(ctx, "_qs", {}), config))

    # ── GET /api/cable-sync-log ──────────────────────────────────────────────
    @router.get("/api/cable-sync-log")
    def get_cable_sync_log(ctx) -> None:
        log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
        if log_path.exists():
            with open(log_path, encoding="utf-8", errors="replace") as _lf:
                lines = _lf.readlines()
            tail = "".join(lines[-500:])
            ctx._send_json({"log": tail, "lines": len(lines)})
        else:
            ctx._send_json({"log": "", "lines": 0})

    # ── POST /api/cable-sync ─────────────────────────────────────────────────
    @router.post("/api/cable-sync")
    def post_cable_sync(ctx) -> None:
        _do_cable_sync(ctx, ctx._post_data, config, repository, job_manager)

    # ── POST /api/rom-tree-diff ──────────────────────────────────────────────
    @router.post("/api/rom-tree-diff")
    def post_rom_tree_diff(ctx) -> None:
        _do_tree_diff(ctx, ctx._post_data, config, job_manager)


def _build_sync_doctor(
    config: AppConfig,
    repository: LibraryRepository,
    serial: str,
    android_path: str,
    pc_path: str,
    *,
    quick: bool = False,
) -> dict:
    """AUD-1 Sync Doctor: clock skew + anomalous saves diagnostics.

    With ``quick=True`` only the clock check runs (used as pre-flight before a
    mtime-based sync); the full report also joins local vs remote save listings
    and the last sync per file from ``save_sync_log``.
    """
    import time
    from pathlib import PurePosixPath

    from rom_manager.sync.adb_transport import AdbTransport

    transport = AdbTransport(config.adb, serial)
    pc_epoch = time.time()
    device_epoch = transport.device_epoch()
    skew = device_epoch - pc_epoch
    threshold = config.sync.clock_skew_threshold_s
    result: dict = {
        "ok": True,
        "pc_epoch": round(pc_epoch, 1),
        "device_epoch": device_epoch,
        "skew_seconds": round(skew, 1),
        "threshold_seconds": threshold,
        "skew_exceeded": abs(skew) > threshold,
    }
    if quick:
        return result

    save_exts = frozenset(config.save_extensions)
    android_prefix = android_path.rstrip("/") + "/"
    remote_index = {
        info.android_path.removeprefix(android_prefix): info
        for info in transport.ls_recursive(android_path, wanted_extensions=save_exts)
    }

    local_index: dict[str, object] = {}
    if pc_path and Path(pc_path).is_dir():
        from rom_manager.sync.save_syncer import list_local_saves

        local_index = {
            s.relative: s for s in list_local_saves(Path(pc_path), config.save_extensions)
        }

    # mtime in the future = symptom of a badly-set clock (margin: skew threshold)
    future_limit = pc_epoch + threshold
    future_local = sorted(
        rel for rel, s in local_index.items() if s.mtime.timestamp() > future_limit
    )
    future_remote = sorted(rel for rel, info in remote_index.items() if info.mtime > future_limit)
    only_local = sorted(set(local_index) - set(remote_index))
    only_remote = sorted(set(remote_index) - set(local_index))

    # Last sync per file, newest first (save_sync_log already exists — AUD-1 adds the view)
    last_syncs: list[dict] = []
    try:
        with repository.connect() as conn:
            rows = conn.execute(
                """
                SELECT local_path, direction, result, created_at, MAX(id)
                FROM save_sync_log
                GROUP BY local_path
                ORDER BY MAX(id) DESC
                LIMIT 100
                """
            ).fetchall()
        last_syncs = [
            {
                "file": PurePosixPath(str(r["local_path"]).replace("\\", "/")).name,
                "direction": r["direction"],
                "result": r["result"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    except Exception:
        _logger.debug("save_sync_log no disponible para Sync Doctor", exc_info=True)

    _CAP = 100
    result.update(
        {
            "pc_path": pc_path,
            "android_path": android_path,
            "local_total": len(local_index),
            "remote_total": len(remote_index),
            "in_both": len(set(local_index) & set(remote_index)),
            "future_local": future_local[:_CAP],
            "future_remote": future_remote[:_CAP],
            "only_local": only_local[:_CAP],
            "only_remote": only_remote[:_CAP],
            "only_local_total": len(only_local),
            "only_remote_total": len(only_remote),
            "last_syncs": last_syncs,
        }
    )
    return result


def _do_cable_sync(
    ctx, data: dict, config: AppConfig, repository: LibraryRepository, job_manager: JobManager
) -> None:
    pc_path_str = data.get("pc_path", "").strip()
    anbernic_path_str = data.get("anbernic_path", "").strip()
    what = data.get("what", ["saves"])
    direction = data.get("direction", "pc_to_anbernic")
    dry_run = bool(data.get("dry_run", True))
    skip_sha1_dups = bool(data.get("skip_sha1_dups", False))
    skip_existing = bool(data.get("skip_existing", False))
    safe_mode = bool(data.get("safe_mode", True))
    delete_extra = bool(data.get("delete_extra", False))
    use_adb = bool(data.get("use_adb", False))
    adb_serial = data.get("adb_serial", "").strip()
    android_path = data.get("android_path", "/storage/emulated/0").strip()

    if not pc_path_str:
        ctx._send_json({"error": "pc_path is required"})
        return
    if use_adb and not adb_serial:
        ctx._send_json({"error": "adb_serial is required when use_adb is true"})
        return
    if not use_adb and not anbernic_path_str:
        ctx._send_json({"error": "anbernic_path is required"})
        return

    # CABLE-UX-1: pre-flight de reloj en el backend (antes solo existía en el
    # frontend) — cubre tanto el sync manual como el botón "Sincronizar saves
    # ahora", que postea a este mismo endpoint.
    if use_adb and direction == "newest" and not dry_run:
        try:
            _doc = _build_sync_doctor(
                config, repository, adb_serial, android_path, pc_path_str, quick=True
            )
        except Exception as exc:
            ctx._send_json({"error": f"No se pudo comprobar el reloj de la consola: {exc}"})
            return
        if _doc.get("skew_exceeded"):
            ctx._send_json(
                {
                    "error": (
                        f"Reloj de la consola desviado {_doc['skew_seconds']:.0f}s "
                        f"(umbral {_doc['threshold_seconds']}s) — ajusta la hora de la "
                        'consola antes de sincronizar por fecha ("Igualar ambos dispositivos").'
                    )
                }
            )
            return

    def run() -> None:
        cancel_event = job_manager.cancel_event("cable_sync")
        _log_file = None
        job_result: dict | None = None
        try:
            import datetime as _dt
            import time as _time
            from pathlib import PurePosixPath

            from rom_manager.backup.save_backup import backup_save
            from rom_manager.utils.trash import discard_to_trash as _discard_to_trash

            pc_root = Path(pc_path_str)
            save_exts = frozenset(config.save_extensions)
            # REV43-2: backup versionado antes de sobrescribir un save existente
            # (mismo patrón que ya usa el SD-auto daemon, CABLE-UX-9a) — la ruta
            # manual de cable/ADB no tenía red de seguridad.
            _bk_root = config.data_dir if config.backup.saves_enabled else None

            log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            _log_file = open(log_path, "a", encoding="utf-8", buffering=1)
            _ts0 = _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            _log_file.write(
                f"\n=== Cable Sync {_ts0} | direction={direction} dry_run={dry_run} safe_mode={safe_mode} ===\n"
            )

            def _log(tag: str, src: str, dst: str = "", note: str = "") -> None:
                ts = _dt.datetime.now(tz=_dt.UTC).strftime("%H:%M:%S")
                _log_file.write(
                    f"[{ts}] [{tag:5s}] {src}{(' -> ' + dst) if dst else ''}{(' | ' + note) if note else ''}\n"
                )

            def _cat_name(name: str) -> str:
                suffix = Path(name).suffix.lower()
                return "save" if suffix in save_exts else "rom"

            _ASSET_EXTS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})

            def _wanted_name(name: str) -> bool:
                if name.startswith("."):
                    return False
                cat = _cat_name(name)
                return (cat == "save" and "saves" in what) or (cat == "rom" and "roms" in what)

            def _category(p: Path) -> str:
                return "save" if p.suffix.lower() in save_exts else "rom"

            def _wanted(p: Path) -> bool:
                if "assets" in what and p.suffix.lower() in _ASSET_EXTS:
                    if "media" in (part.lower() for part in p.parts):
                        return True
                if "gamelists" in what and p.name.lower() == "gamelist.xml":
                    return True
                return _wanted_name(p.name)

            def _iter_files(root: Path):
                for dirpath, dirs, files in os.walk(root):
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    for fname in files:
                        yield Path(dirpath) / fname

            copied = skipped = errors = sha1_skipped = safe_mode_skipped = deleted_extra = 0
            copied_bytes = 0
            details: list[dict] = []

            _last_speed_update = _time.monotonic()
            _last_speed_bytes = 0
            _last_speed = 0.0

            def _update_progress(file_name: str = "") -> None:
                nonlocal _last_speed_update, _last_speed_bytes, _last_speed
                now = _time.monotonic()
                dt = now - _last_speed_update
                if dt >= 0.5:
                    _last_speed = (copied_bytes - _last_speed_bytes) / dt
                    _last_speed_update = now
                    _last_speed_bytes = copied_bytes
                job_manager.update_progress(
                    "cable_sync",
                    {
                        "copied": copied,
                        "bytes_copied": copied_bytes,
                        "speed_bps": _last_speed,
                        "current_file": file_name,
                    },
                )

            # CABLE-UX-9d: copy_item del motor compartido (CABLE-UX-9b) hace
            # el trabajo de safe_mode/skip_existing/dry_run; aquí solo se
            # traducen sus eventos a los contadores/log/details de siempre.
            def _apply_copy(item: cable_engine.CopyPlanItem) -> None:
                nonlocal copied, skipped, errors, copied_bytes, safe_mode_skipped
                if cancel_event.is_set():
                    return

                def _on_event(tag: str, ev_item: cable_engine.CopyPlanItem, note: str) -> None:
                    nonlocal skipped, errors, safe_mode_skipped
                    src_name = str(ev_item.src.name)
                    if tag == "SAFE":
                        safe_mode_skipped += 1
                        skipped += 1
                        _log("SAFE", str(ev_item.src), str(ev_item.dst), note)
                        if len(details) < 300:
                            details.append({"file": "SAFE", "path": src_name})
                    elif tag == "SKIP":
                        skipped += 1
                        _log("SKIP", str(ev_item.src), str(ev_item.dst), note)
                        if len(details) < 300:
                            details.append({"file": "EXISTS", "path": src_name})
                    elif tag == "ERROR":
                        errors += 1
                        _log("ERROR", str(ev_item.src), str(ev_item.dst), note)
                        if len(details) < 300:
                            details.append({"file": f"ERROR: {note}", "path": src_name})
                    else:  # COPY / DRYRUN
                        _log(tag, str(ev_item.src), str(ev_item.dst))

                if (
                    _bk_root is not None
                    and not dry_run
                    and not safe_mode
                    and _category(item.src) == "save"
                    and item.dst.exists()
                ):
                    backup_save(item.dst, _bk_root)
                policy = cable_engine.CopyPolicy(
                    dry_run=dry_run, safe_mode=safe_mode, skip_existing=skip_existing
                )
                tag, size = cable_engine.copy_item(item, policy, on_event=_on_event)
                if tag in ("COPY", "DRYRUN"):
                    copied += 1
                    copied_bytes += size
                    if len(details) < 300:
                        details.append({"file": item.arrow, "path": item.src.name})
                    _update_progress(item.src.name)

            # ── ADB mode ──────────────────────────────────────────────────────
            if use_adb:
                from rom_manager.sync.adb_transport import AdbTransport, should_verify

                transport = AdbTransport(config.adb, adb_serial)

                def _adb_copy_to_pc(adb_info, rel_posix: str, arrow: str) -> None:
                    nonlocal copied, errors, copied_bytes
                    if cancel_event.is_set():
                        return
                    name = PurePosixPath(adb_info.android_path).name
                    local_dst = pc_root / Path(rel_posix.replace("/", os.sep))
                    is_save = should_verify(name, save_exts)
                    try:
                        if _bk_root is not None and not dry_run and is_save and local_dst.exists():
                            backup_save(local_dst, _bk_root)
                        size = transport.pull(
                            adb_info.android_path,
                            local_dst,
                            dry_run=dry_run,
                            verify=is_save,
                        )
                        _log(
                            "ADB←" if not dry_run else "DRY←", adb_info.android_path, str(local_dst)
                        )
                        copied += 1
                        copied_bytes += size
                        if len(details) < 300:
                            details.append({"file": arrow, "path": name})
                        _update_progress(name)
                    except OSError as exc:
                        _log("ERROR", adb_info.android_path, str(local_dst), str(exc))
                        errors += 1
                        if len(details) < 300:
                            details.append({"file": f"ERROR: {exc}", "path": name})

                def _adb_copy_to_device(local_src: Path, rel_posix: str, arrow: str) -> None:
                    nonlocal copied, errors, copied_bytes
                    if cancel_event.is_set():
                        return
                    android_dst = android_path.rstrip("/") + "/" + rel_posix
                    try:
                        size = transport.push(
                            local_src,
                            android_dst,
                            dry_run=dry_run,
                            verify=should_verify(local_src.name, save_exts),
                        )
                        _log("ADB→" if not dry_run else "DRY→", str(local_src), android_dst)
                        copied += 1
                        copied_bytes += size
                        if len(details) < 300:
                            details.append({"file": arrow, "path": local_src.name})
                        _update_progress(local_src.name)
                    except OSError as exc:
                        _log("ERROR", str(local_src), android_dst, str(exc))
                        errors += 1
                        if len(details) < 300:
                            details.append({"file": f"ERROR: {exc}", "path": local_src.name})

                job_manager.update_progress(
                    "cable_sync",
                    {"copied": 0, "current_file": "Listando archivos en el dispositivo…"},
                )
                ab_adb_files = transport.ls_recursive(android_path)
                try:
                    _pre_files = sum(
                        1
                        for info in ab_adb_files
                        if _wanted_name(PurePosixPath(info.android_path).name)
                    )
                    _pre_total = sum(
                        info.size
                        for info in ab_adb_files
                        if _wanted_name(PurePosixPath(info.android_path).name)
                    )
                    job_manager.update_progress(
                        "cable_sync",
                        {
                            "bytes_total": _pre_total,
                            "total_files": _pre_files,
                            "copied": 0,
                            "bytes_copied": 0,
                            "speed_bps": 0.0,
                        },
                    )
                except Exception:
                    _logger.debug(
                        "No se pudo actualizar el progreso de cable-sync (ADB)", exc_info=True
                    )
                android_prefix = android_path.rstrip("/") + "/"

                if direction == "pc_to_anbernic":
                    for src in _iter_files(pc_root):
                        if cancel_event.is_set():
                            break
                        if not _wanted(src):
                            continue
                        rel = src.relative_to(pc_root)
                        rel_posix = rel.as_posix()
                        _adb_copy_to_device(src, rel_posix, "→ ADB")

                    if delete_extra and not cancel_event.is_set():
                        _pc_rels = {
                            f.relative_to(pc_root).as_posix()
                            for f in _iter_files(pc_root)
                            if _wanted(f)
                        }
                        for _info in ab_adb_files:
                            _aname = PurePosixPath(_info.android_path).name
                            if not _wanted_name(_aname):
                                continue
                            _arel = _info.android_path.removeprefix(android_prefix)
                            if _arel not in _pc_rels:
                                if not dry_run:
                                    try:
                                        transport._shell("rm", _info.android_path, timeout=30)
                                        deleted_extra += 1
                                        _log(
                                            "DEL",
                                            _info.android_path,
                                            "",
                                            "espejo: extra en dispositivo",
                                        )
                                    except Exception as _exc:
                                        errors += 1
                                        _log("ERROR", _info.android_path, "", f"DEL: {_exc}")
                                else:
                                    deleted_extra += 1
                                    _log("DEL?", _info.android_path, "", "espejo (dry run)")

                elif direction == "anbernic_to_pc":
                    use_sha1 = skip_sha1_dups and "roms" in what
                    for info in ab_adb_files:
                        if cancel_event.is_set():
                            break
                        name = PurePosixPath(info.android_path).name
                        if not _wanted_name(name):
                            continue
                        rel_posix = info.android_path.removeprefix(android_prefix)
                        if use_sha1 and _cat_name(name) == "rom":
                            if dry_run:
                                # REV43-6: el chequeo SHA1 exige descargar el
                                # archivo para hashearlo — un dry-run no debe
                                # disparar transferencias ADB reales, así que
                                # el dedup no se evalúa aquí (se cuenta como
                                # "se copiaría", igual que el resto de rutas
                                # de previsualización).
                                copied += 1
                                if len(details) < 300:
                                    details.append(
                                        {"file": "DRY← (sin chequeo SHA1)", "path": name}
                                    )
                                _update_progress(name)
                                continue
                            _update_progress(f"[SHA1] {name}")
                            import tempfile

                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=Path(name).suffix
                            ) as tf:
                                tmp_path = Path(tf.name)
                            try:
                                transport.pull(info.android_path, tmp_path, dry_run=False)
                                from rom_manager.hashing.hash_calculator import calculate_hashes

                                h = calculate_hashes(tmp_path)
                                if repository.sha1_exists(h.sha1):
                                    sha1_skipped += 1
                                    skipped += 1
                                    if len(details) < 300:
                                        details.append({"file": "DUP", "path": name})
                                    tmp_path.unlink(missing_ok=True)
                                    continue
                                dst = pc_root / Path(rel_posix.replace("/", os.sep))
                                dst.parent.mkdir(parents=True, exist_ok=True)
                                shutil.move(str(tmp_path), dst)
                                copied += 1
                                copied_bytes += info.size
                                if len(details) < 300:
                                    details.append({"file": "← ADB", "path": name})
                                _update_progress(name)
                            except OSError as exc:
                                tmp_path.unlink(missing_ok=True)
                                errors += 1
                                if len(details) < 300:
                                    details.append({"file": f"ERROR: {exc}", "path": name})
                        else:
                            _adb_copy_to_pc(info, rel_posix, "← ADB")

                    if delete_extra and not cancel_event.is_set():
                        _ab_rels = {
                            _i.android_path.removeprefix(android_prefix)
                            for _i in ab_adb_files
                            if _wanted_name(PurePosixPath(_i.android_path).name)
                        }
                        for _f in _iter_files(pc_root):
                            if not _wanted(_f):
                                continue
                            _frel = _f.relative_to(pc_root).as_posix()
                            if _frel not in _ab_rels:
                                if not dry_run:
                                    try:
                                        _discard_to_trash(_f)  # AUD-3: soft-discard
                                        deleted_extra += 1
                                        _log("DEL", str(_f), "", "espejo: extra en PC")
                                    except OSError as _exc:
                                        errors += 1
                                        _log("ERROR", str(_f), "", f"DEL: {_exc}")
                                else:
                                    deleted_extra += 1
                                    _log("DEL?", str(_f), "", "espejo: extra en PC (dry run)")

                elif direction == "newest":
                    ab_index = {
                        info.android_path.removeprefix(android_prefix): info
                        for info in ab_adb_files
                        if _wanted_name(PurePosixPath(info.android_path).name)
                    }
                    pc_index: dict[str, Path] = {}
                    for f in _iter_files(pc_root):
                        if _wanted(f):
                            pc_index[f.relative_to(pc_root).as_posix()] = f

                    all_rels = sorted(set(pc_index) | set(ab_index))
                    for rel_posix in all_rels:
                        if cancel_event.is_set():
                            break
                        pc_f = pc_index.get(rel_posix)
                        ab_inf = ab_index.get(rel_posix)
                        if pc_f and ab_inf:
                            # REV43-4: misma tolerancia que cable_engine.plan_direction
                            # — sin ella, el redondeo de mtime de FAT32/exFAT elige un
                            # "ganador" arbitrario y puede sobrescribir la version buena.
                            diff = pc_f.stat().st_mtime - ab_inf.mtime
                            if diff > cable_engine.DEFAULT_MTIME_TOLERANCE_S:
                                _adb_copy_to_device(pc_f, rel_posix, "→ ADB (PC más reciente)")
                            elif diff < -cable_engine.DEFAULT_MTIME_TOLERANCE_S:
                                _adb_copy_to_pc(ab_inf, rel_posix, "← ADB (Anbernic más reciente)")
                            else:
                                skipped += 1
                        elif pc_f:
                            _adb_copy_to_device(pc_f, rel_posix, "→ ADB (solo en PC)")
                        elif ab_inf:
                            _adb_copy_to_pc(ab_inf, rel_posix, "← ADB (solo en Anbernic)")

            # ── Filesystem mode ───────────────────────────────────────────────
            else:
                ab_root = Path(anbernic_path_str)

                try:
                    _pre_total = 0
                    _pre_files = 0
                    if direction == "pc_to_anbernic":
                        for _f in _iter_files(pc_root):
                            if _wanted(_f):
                                try:
                                    _pre_total += _f.stat().st_size
                                except OSError:
                                    pass
                                _pre_files += 1
                    elif direction == "anbernic_to_pc":
                        for _f in _iter_files(ab_root):
                            if _wanted(_f):
                                try:
                                    _pre_total += _f.stat().st_size
                                except OSError:
                                    pass
                                _pre_files += 1
                    elif direction == "newest":
                        for _f in _iter_files(pc_root):
                            if _wanted(_f):
                                try:
                                    _pre_total += _f.stat().st_size
                                except OSError:
                                    pass
                                _pre_files += 1
                        for _f in _iter_files(ab_root):
                            if _wanted(_f):
                                try:
                                    _pre_total += _f.stat().st_size
                                except OSError:
                                    pass
                                _pre_files += 1
                    job_manager.update_progress(
                        "cable_sync",
                        {
                            "bytes_total": _pre_total,
                            "total_files": _pre_files,
                            "copied": 0,
                            "bytes_copied": 0,
                            "speed_bps": 0.0,
                        },
                    )
                except Exception:
                    _logger.debug(
                        "No se pudo actualizar el progreso de cable-sync (SD)", exc_info=True
                    )

                if direction == "pc_to_anbernic":
                    for item in cable_engine.plan_direction(pc_root, ab_root, direction, _wanted):
                        if cancel_event.is_set():
                            break
                        _apply_copy(item)

                    if delete_extra and not cancel_event.is_set():
                        _pc_rels = {
                            f.relative_to(pc_root) for f in _iter_files(pc_root) if _wanted(f)
                        }
                        for _f in _iter_files(ab_root):
                            if not _wanted(_f):
                                continue
                            try:
                                _frel = _f.relative_to(ab_root)
                            except ValueError:
                                continue
                            if _frel not in _pc_rels:
                                if not dry_run:
                                    try:
                                        _discard_to_trash(_f)  # AUD-3: soft-discard
                                        deleted_extra += 1
                                        _log("DEL", str(_f), "", "espejo: extra en destino")
                                    except OSError as _exc:
                                        errors += 1
                                        _log("ERROR", str(_f), "", f"DEL: {_exc}")
                                else:
                                    deleted_extra += 1
                                    _log("DEL?", str(_f), "", "espejo: extra en destino (dry run)")

                elif direction == "anbernic_to_pc":
                    use_sha1 = skip_sha1_dups and "roms" in what
                    if use_sha1:
                        from rom_manager.hashing.hash_calculator import calculate_hashes
                    for item in cable_engine.plan_direction(pc_root, ab_root, direction, _wanted):
                        if cancel_event.is_set():
                            break
                        if use_sha1 and _category(item.src) == "rom":
                            _update_progress(f"[SHA1] {item.src.name}")
                            try:
                                h = calculate_hashes(item.src)
                                if repository.sha1_exists(h.sha1):
                                    sha1_skipped += 1
                                    skipped += 1
                                    if len(details) < 300:
                                        details.append({"file": "DUP", "path": item.src.name})
                                    continue
                            except OSError:
                                pass
                        _apply_copy(item)

                    if delete_extra and not cancel_event.is_set():
                        _ab_rels: set[Path] = set()
                        for _f in _iter_files(ab_root):
                            if _wanted(_f):
                                try:
                                    _ab_rels.add(_f.relative_to(ab_root))
                                except ValueError:
                                    pass
                        for _f in _iter_files(pc_root):
                            if not _wanted(_f):
                                continue
                            _frel = _f.relative_to(pc_root)
                            if _frel not in _ab_rels:
                                if not dry_run:
                                    try:
                                        _discard_to_trash(_f)  # AUD-3: soft-discard
                                        deleted_extra += 1
                                        _log("DEL", str(_f), "", "espejo: extra en PC")
                                    except OSError as _exc:
                                        errors += 1
                                        _log("ERROR", str(_f), "", f"DEL: {_exc}")
                                else:
                                    deleted_extra += 1
                                    _log("DEL?", str(_f), "", "espejo: extra en PC (dry run)")

                elif direction == "newest":
                    for item in cable_engine.plan_direction(pc_root, ab_root, direction, _wanted):
                        if cancel_event.is_set():
                            break
                        _apply_copy(item)

                    # ponytail: recorre otra vez para contar empates de mtime
                    # (plan_direction ya los excluye del plan porque no hay
                    # nada que copiar). Mismo enfoque que CABLE-UX-9c.
                    if not cancel_event.is_set():
                        pc_index = {
                            f.relative_to(pc_root): f for f in _iter_files(pc_root) if _wanted(f)
                        }
                        for f in _iter_files(ab_root):
                            if not _wanted(f):
                                continue
                            try:
                                rel = f.relative_to(ab_root)
                            except ValueError:
                                continue
                            pc_f = pc_index.get(rel)
                            if pc_f is not None and pc_f.stat().st_mtime == f.stat().st_mtime:
                                skipped += 1

            import datetime as _dt

            _ts1 = _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            _log_file.write(
                f"=== Fin {_ts1} | copied={copied} skipped={skipped} safe_skipped={safe_mode_skipped} deleted_extra={deleted_extra} errors={errors} cancelled={cancel_event.is_set()} ===\n"
            )
            _pc_file_count = 0
            _ab_file_count = 0
            if not dry_run and not use_adb:
                try:
                    _ab_r = Path(anbernic_path_str)
                    for _ff in _iter_files(pc_root):
                        if _wanted(_ff):
                            _pc_file_count += 1
                except Exception:
                    _logger.debug(
                        "Conteo de archivos en PC para preview de sync falló", exc_info=True
                    )
                try:
                    for _ff in _iter_files(_ab_r):
                        if _wanted(_ff):
                            _ab_file_count += 1
                except Exception:
                    _logger.debug(
                        "Conteo de archivos en Android para preview de sync falló", exc_info=True
                    )
            job_result = {
                "dry_run": dry_run,
                "direction": direction,
                "use_adb": use_adb,
                "copied": copied,
                "skipped": skipped,
                "sha1_skipped": sha1_skipped,
                "safe_mode_skipped_overwrites": safe_mode_skipped,
                "errors": errors,
                "copied_bytes": copied_bytes,
                "cancelled": cancel_event.is_set(),
                "deleted_extra": deleted_extra,
                "details": details,
                "pc_file_count": _pc_file_count,
                "ab_file_count": _ab_file_count,
            }
            if not dry_run and not cancel_event.is_set() and config.notify_desktop:
                from rom_manager.utils.notifier import notify

                _via = "ADB" if use_adb else "SD"
                _body = f"{copied} archivos copiados vía {_via}"
                if errors:
                    _body += f" ({errors} errores)"
                notify("Retro Vault — Cable Sync completado", _body)
        except Exception as exc:
            job_result = {"error": str(exc)}
        finally:
            if _log_file is not None:
                try:
                    _log_file.close()
                except Exception:
                    _logger.debug("No se pudo cerrar el log de cable-sync", exc_info=True)
            job_manager.finish("cable_sync", job_result)

    result = job_manager.start("cable_sync", run)
    if result.get("status") == "started":
        result = {**result, "dry_run": dry_run}
    ctx._send_json(result)


def _do_tree_diff(ctx, data: dict, config: AppConfig, job_manager: JobManager) -> None:
    """Background job: compare the ROM file tree between PC and console."""
    from pathlib import Path as _Path

    source = data.get("source", "local")
    serial = data.get("serial", "").strip()
    pc_path_str = data.get("pc_path", "").strip() or (
        str(config.library_root) if config.library_root else ""
    )
    and_path_str = (
        data.get("android_path", "").strip()
        or config.anbernic_root
        or config.sync.auto_sync_android_path
    )

    def run() -> None:
        import time as _time

        job_result = None
        try:
            from rom_manager.utils.dir_diff import diff_trees, get_adb_tree, get_local_tree

            if not pc_path_str:
                job_result = {"error": "Ruta PC no configurada (library_root)"}
                return
            pc_root = _Path(pc_path_str)
            if not pc_root.exists():
                job_result = {"error": f"Ruta PC no existe: {pc_path_str}"}
                return

            skip = frozenset(config.excluded_directories)
            pc_tree = get_local_tree(pc_root, skip)

            if source == "adb":
                if not serial:
                    job_result = {"error": "serial ADB requerido"}
                    return
                if not and_path_str:
                    job_result = {"error": "Ruta Android no configurada"}
                    return
                from rom_manager.sync.adb_transport import AdbTransport

                transport = AdbTransport(config.adb, serial, timeout=60)
                android_tree = get_adb_tree(transport, and_path_str, timeout=300)
            else:
                if not and_path_str:
                    job_result = {"error": "Ruta consola no configurada (anbernic_root)"}
                    return
                and_root = _Path(and_path_str)
                if not and_root.exists():
                    job_result = {"error": f"Ruta consola no existe: {and_path_str}"}
                    return
                android_tree = get_local_tree(and_root, skip)

            diff = diff_trees(pc_tree, android_tree)
            MAX = 500
            job_result = {
                "ok": True,
                "pc_path": pc_path_str,
                "android_path": and_path_str,
                "source": source,
                "only_pc": diff.only_a[:MAX],
                "only_android": diff.only_b[:MAX],
                "only_pc_total": len(diff.only_a),
                "only_android_total": len(diff.only_b),
                "in_both": diff.in_both,
                "total_pc": diff.total_a,
                "total_android": diff.total_b,
                "result_ts": _time.time(),
            }
        except Exception as exc:
            job_result = {"error": str(exc)}
        finally:
            job_manager.finish("tree_diff", job_result)

    ctx._send_json(job_manager.start("tree_diff", run))
