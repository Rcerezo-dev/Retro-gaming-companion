"""Auto-sync ADB daemon and SD card sync daemon threads.

Extracted from server.py (Session 19). Shared mutable state now lives in
``rom_manager.web.state`` (imported at module top as ``_state``); the old
per-function late imports of ``server`` are no longer needed.
"""

from __future__ import annotations

import logging
from pathlib import Path

import rom_manager.web.state as _state
from rom_manager.config import AppConfig

_logger = logging.getLogger(__name__)


def _auto_sync_loop(config: AppConfig, get_repo_fn) -> None:
    """Daemon thread: polls ADB every 10 s, triggers Cable Sync when a device connects."""
    import datetime as _dt
    import time as _time

    _jm = _state._job_manager

    _POLL_INTERVAL = 10  # seconds between ADB polls
    _COOLDOWN = 30  # seconds to wait after a sync before syncing again
    _last_sync_ts: float = 0.0

    while True:
        try:
            _time.sleep(_POLL_INTERVAL)

            # Don't poll if a cable_sync job is already running
            if _jm.get_status()["cable_sync_running"]:
                continue

            # Cooldown: avoid re-triggering immediately after a sync
            if _time.monotonic() - _last_sync_ts < _COOLDOWN:
                continue

            # Require library_root to be configured
            if not config.library_root:
                continue

            # Poll ADB devices (always, even when auto-sync is disabled, for UI prompt)
            try:
                from rom_manager.sync.adb_transport import list_devices

                devices = list_devices(config.adb, timeout=8)
            except Exception:
                # adb not found or timed out — skip this poll cycle
                _logger.debug("ADB no disponible en el sondeo de auto-sync", exc_info=True)
                continue

            current_serials = {d.serial for d in devices if d.ready}

            # Clear device_prompt when the device disconnects
            if not current_serials and _state._auto_sync_status.get("state") == "device_prompt":
                _state._auto_sync_status["state"] = "waiting"

            # Detect newly connected devices
            new_serials = current_serials - _state._auto_sync_last_devices
            _state._auto_sync_last_devices = current_serials

            if not new_serials:
                continue

            # If known_devices filter is set, only react to those
            known = config.sync.auto_sync_known_devices
            if known:
                new_serials = {s for s in new_serials if s in known}
            if not new_serials:
                continue

            serial = next(iter(new_serials))

            if not _state._auto_sync_enabled:
                # Auto-sync disabled: show prompt in UI, let user decide
                _logger.info(
                    "Auto-sync: new device %s — auto-sync disabled, showing prompt", serial
                )
                _state._auto_sync_status = {
                    "state": "device_prompt",
                    "last_device": serial,
                    "last_sync_at": _state._auto_sync_status.get("last_sync_at"),
                    "last_error": None,
                }
                continue

            _logger.info("Auto-sync: new device %s — starting sync", serial)

            # CABLE-UX-1: mismo guard de reloj que el sync manual (AUD-1) — el
            # auto-sync dispara "newest" en cada conexión sin pedir confirmación,
            # así que aquí no hay usuario que decida "continuar de todos modos".
            if config.sync.auto_sync_direction == "newest":
                from rom_manager.web.handlers.sync_cable import _build_sync_doctor

                try:
                    _doc = _build_sync_doctor(
                        config, None, serial, config.sync.auto_sync_android_path, "", quick=True
                    )
                except Exception:
                    _logger.debug("Pre-flight de reloj de auto-sync falló", exc_info=True)
                    _doc = {"skew_exceeded": False}
                if _doc.get("skew_exceeded"):
                    _logger.warning(
                        "Auto-sync: reloj desviado %.0fs en %s — sync abortado",
                        _doc.get("skew_seconds", 0),
                        serial,
                    )
                    _state._auto_sync_status = {
                        "state": "idle",
                        "last_device": serial,
                        "last_sync_at": _state._auto_sync_status.get("last_sync_at"),
                        "last_error": (
                            f"Reloj desviado {_doc.get('skew_seconds', 0):.0f}s — "
                            "ajusta la hora de la consola"
                        ),
                    }
                    continue

            now_str = _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            _state._auto_sync_status = {
                "state": "syncing",
                "last_device": serial,
                "last_sync_at": now_str,
                "last_error": None,
            }

            def _run_auto_sync(serial: str = serial) -> None:
                import datetime as _dt2
                import os
                from pathlib import PurePosixPath

                _log_file = None
                job_result: dict | None = None
                try:
                    from rom_manager.config import get_adb_sync_sources

                    pc_root = config.library_root
                    direction = config.sync.auto_sync_direction
                    save_exts = frozenset(config.save_extensions)
                    state_exts = frozenset(config.state_extensions)
                    # Build per-emulator sync sources from mapped paths (SYNC-A3)
                    adb_sources = get_adb_sync_sources(config)
                    # Fallback: if no mapped sources, use old single-root behaviour
                    if not adb_sources:
                        adb_sources = [
                            {
                                "name": "RetroArch (legacy)",
                                "package": "com.retroarch.aarch64",
                                "android_saves": config.sync.auto_sync_android_path.rstrip("/"),
                                "android_states": None,
                                "local_saves": pc_root,
                                "local_states": None,
                                "save_extensions": None,
                                "state_extensions": None,
                            }
                        ]

                    log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                    _log_file = open(log_path, "a", encoding="utf-8", buffering=1)
                    ts0 = _dt2.datetime.now(tz=_dt2.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
                    _log_file.write(
                        f"\n=== AUTO-SYNC {ts0} | device={serial} direction={direction} ===\n"
                    )

                    def _log(tag: str, src: str, dst: str = "", note: str = "") -> None:
                        ts = _dt2.datetime.now(tz=_dt2.UTC).strftime("%H:%M:%S")
                        arrow = (" -> " + dst) if dst else ""
                        note_part = (" | " + note) if note else ""
                        _log_file.write(f"[{ts}] [{tag:5s}] {src}{arrow}{note_part}\n")

                    # REV43-33: la sync automática por ADB tampoco escribía en
                    # save_sync_log — mismo hueco que el cable sync manual y el
                    # SD-auto (sync_cable.py / cable_sync_daemon._run_sd_auto_sync).
                    from rom_manager.sync.sync_log import log_sync_event

                    _adb_repo = get_repo_fn(str(pc_root))

                    def _sql_log(
                        direction_: str,
                        local_path: str,
                        remote_path: str,
                        result: str,
                        message: str | None = None,
                    ) -> None:
                        try:
                            with _adb_repo.connect() as conn:
                                log_sync_event(
                                    conn,
                                    local_path=local_path,
                                    remote_path=remote_path,
                                    direction=direction_,
                                    local_mtime=None,
                                    remote_mtime=None,
                                    result=result,
                                    message=message,
                                    created_at=_dt2.datetime.now(tz=_dt2.UTC).strftime(
                                        "%Y-%m-%dT%H:%M:%S"
                                    ),
                                )
                                conn.commit()
                        except Exception:
                            _logger.debug(
                                "No se pudo escribir en save_sync_log (auto-sync ADB)",
                                exc_info=True,
                            )

                    copied = skipped = errors = 0
                    copied_bytes = 0

                    def _update_prog(fname: str = "") -> None:
                        _jm.update_progress(
                            "cable_sync",
                            {
                                "copied": copied,
                                "bytes_copied": copied_bytes,
                                "speed_bps": 0.0,
                                "current_file": fname,
                            },
                        )

                    from rom_manager.sync.adb_transport import AdbTransport, should_verify

                    transport = AdbTransport(config.adb, serial, timeout=60)

                    def _adb_copy_to_pc(adb_info, local_root: Path, android_prefix: str) -> None:
                        nonlocal copied, errors, copied_bytes
                        name = PurePosixPath(adb_info.android_path).name
                        rel_posix = adb_info.android_path.removeprefix(android_prefix)
                        local_dst = local_root / Path(rel_posix.replace("/", os.sep))
                        try:
                            size = transport.pull(
                                adb_info.android_path,
                                local_dst,
                                dry_run=False,
                                verify=should_verify(name, effective_exts),
                            )
                            _log("ADB←", adb_info.android_path, str(local_dst))
                            _sql_log("download", str(local_dst), adb_info.android_path, "ok")
                            copied += 1
                            copied_bytes += size
                            _update_prog(name)
                        except OSError as exc:
                            _log("ERROR", adb_info.android_path, str(local_dst), str(exc))
                            _sql_log(
                                "download", str(local_dst), adb_info.android_path, "error", str(exc)
                            )
                            errors += 1

                    def _adb_copy_to_device(
                        local_src: Path, local_root: Path, android_root: str
                    ) -> None:
                        nonlocal copied, errors, copied_bytes
                        rel = local_src.relative_to(local_root)
                        android_dst = android_root.rstrip("/") + "/" + rel.as_posix()
                        try:
                            size = transport.push(
                                local_src,
                                android_dst,
                                dry_run=False,
                                verify=should_verify(local_src.name, effective_exts),
                            )
                            _log("ADB→", str(local_src), android_dst)
                            _sql_log("upload", str(local_src), android_dst, "ok")
                            copied += 1
                            copied_bytes += size
                            _update_prog(local_src.name)
                        except OSError as exc:
                            _log("ERROR", str(local_src), android_dst, str(exc))
                            _sql_log("upload", str(local_src), android_dst, "error", str(exc))
                            errors += 1

                    _jm.update_progress(
                        "cable_sync",
                        {
                            "copied": 0,
                            "bytes_copied": 0,
                            "speed_bps": 0.0,
                            "current_file": "Auto-sync: listando saves en el dispositivo…",
                        },
                    )

                    # Sync each emulator source — saves and states paths separately
                    for src_info in adb_sources:
                        for path_type in ("saves", "states"):
                            android_root = src_info[f"android_{path_type}"]
                            local_root_p = src_info[f"local_{path_type}"]
                            if not android_root or not local_root_p:
                                continue
                            # Extension filter: use emulator-specific if defined, else global
                            exts_for_type = src_info[
                                "save_extensions" if path_type == "saves" else "state_extensions"
                            ]
                            effective_exts = (
                                exts_for_type
                                if exts_for_type is not None
                                else (save_exts if path_type == "saves" else state_exts)
                            )

                            def _wanted_src(name: str, _exts=effective_exts) -> bool:
                                return (
                                    not name.startswith(".") and Path(name).suffix.lower() in _exts
                                )

                            android_prefix = android_root.rstrip("/") + "/"
                            _log_file.write(
                                f"  [source] {src_info['name']} {path_type}: {android_root} → {local_root_p}\n"
                            )

                            ab_files = transport.ls_recursive(android_root)

                            def _iter_local():
                                if not local_root_p.exists():
                                    return
                                for dp, dirs, files in os.walk(local_root_p):
                                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                                    for fname in files:
                                        yield Path(dp) / fname

                            if direction == "pc_to_anbernic":
                                for lf in _iter_local():
                                    if _wanted_src(lf.name):
                                        _adb_copy_to_device(lf, local_root_p, android_root)

                            elif direction == "anbernic_to_pc":
                                for af in ab_files:
                                    if _wanted_src(PurePosixPath(af.android_path).name):
                                        _adb_copy_to_pc(af, local_root_p, android_prefix)

                            else:  # newest
                                ab_idx = {
                                    af.android_path.removeprefix(android_prefix): af
                                    for af in ab_files
                                    if _wanted_src(PurePosixPath(af.android_path).name)
                                }
                                pc_idx: dict = {}
                                for lf in _iter_local():
                                    if _wanted_src(lf.name):
                                        pc_idx[lf.relative_to(local_root_p).as_posix()] = lf

                                for rel_posix in sorted(set(pc_idx) | set(ab_idx)):
                                    pc_f = pc_idx.get(rel_posix)
                                    ab_f = ab_idx.get(rel_posix)
                                    if pc_f and ab_f:
                                        if pc_f.stat().st_mtime > ab_f.mtime:
                                            _adb_copy_to_device(pc_f, local_root_p, android_root)
                                        elif ab_f.mtime > pc_f.stat().st_mtime:
                                            _adb_copy_to_pc(ab_f, local_root_p, android_prefix)
                                        else:
                                            skipped += 1
                                    elif pc_f:
                                        _adb_copy_to_device(pc_f, local_root_p, android_root)
                                    elif ab_f:
                                        _adb_copy_to_pc(ab_f, local_root_p, android_prefix)

                    ts1 = _dt2.datetime.now(tz=_dt2.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
                    _log_file.write(
                        f"=== Auto-sync fin {ts1} | copied={copied} skipped={skipped} errors={errors} ===\n"
                    )

                    job_result = {
                        "dry_run": False,
                        "direction": direction,
                        "use_adb": True,
                        "copied": copied,
                        "skipped": skipped,
                        "sha1_skipped": 0,
                        "safe_mode_skipped_overwrites": 0,
                        "errors": errors,
                        "copied_bytes": copied_bytes,
                        "cancelled": False,
                        "details": [],
                        "pc_file_count": 0,
                        "ab_file_count": 0,
                        "auto_sync": True,
                    }

                    finish_ts = _dt2.datetime.now(tz=_dt2.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
                    _state._auto_sync_status = {
                        "state": "idle",
                        "last_device": serial,
                        "last_sync_at": finish_ts,
                        "last_error": None if errors == 0 else f"{errors} errores",
                    }

                except Exception as exc:
                    _logger.exception("Auto-sync error: %s", exc)
                    _state._auto_sync_status = {
                        "state": "idle",
                        "last_device": serial,
                        "last_sync_at": _state._auto_sync_status.get("last_sync_at"),
                        "last_error": str(exc),
                    }
                    job_result = {"error": str(exc), "auto_sync": True}
                finally:
                    if _log_file is not None:
                        try:
                            _log_file.close()
                        except Exception:
                            _logger.debug("No se pudo cerrar el log de auto-sync", exc_info=True)
                    _jm.finish("cable_sync", job_result)

            if _jm.start("cable_sync", _run_auto_sync).get("status") == "started":
                _last_sync_ts = _time.monotonic()
            else:
                _state._auto_sync_status["state"] = "waiting"

        except Exception as exc:
            # Never crash the daemon
            _logger.debug("Auto-sync daemon exception: %s", exc)
            try:
                _state._auto_sync_status["state"] = "waiting"
            except Exception:
                _logger.debug("No se pudo restaurar el estado de auto-sync", exc_info=True)


# ── SD card auto-sync daemon ───────────────────────────────────────────────────


def _run_sd_auto_sync(config: AppConfig, get_repo_fn) -> None:
    """Run a filesystem Cable Sync triggered by SD card insertion."""
    import datetime as _dt2
    import shutil

    from rom_manager.sync import cable_engine
    from rom_manager.sync.sync_log import log_sync_event

    _sd_sync_status = _state._sd_sync_status
    _jm = _state._job_manager

    _log_file = None
    job_result: dict | None = None
    copied = 0
    skipped = 0
    errors = 0
    copied_bytes = 0

    try:
        pc_root = config.library_root
        ab_root = Path(config.anbernic_root)
        direction = config.sync.auto_sync_direction or "newest"
        save_exts = frozenset(ext.lower() for ext in config.save_extensions)

        log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        _log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        ts0 = _dt2.datetime.now(tz=_dt2.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        _log_file.write(
            f"\n=== SD-AUTO-SYNC {ts0} | direction={direction} | ab={config.anbernic_root} ===\n"
        )

        if pc_root is None:
            _log_file.write("ERROR: library_root not configured\n")
            return

        def _wanted(p: Path) -> bool:
            return p.suffix.lower() in save_exts

        # CABLE-UX-9a: backup del destino antes de sobrescribirlo — el SD
        # auto-sync no tenía red de seguridad (regla "ante duda, no
        # sobreescribir").
        backup_dir = (
            config.project_root / ".rommgr" / "cable_sync_backups" / _dt2.date.today().isoformat()
        )

        # CABLE-UX-9c: motor compartido (CABLE-UX-9b) en vez de walk+compare+
        # copy propios.
        items = list(cable_engine.plan_direction(pc_root, ab_root, direction, _wanted))
        policy = cable_engine.CopyPolicy()
        repository = get_repo_fn(str(pc_root))

        # REV43-33: este daemon solo dejaba rastro en el .log de texto, nunca
        # en save_sync_log — mismo hueco que el cable sync manual (sync_cable.py).
        def _sql_log(
            item: cable_engine.CopyPlanItem, result: str, message: str | None = None
        ) -> None:
            to_anbernic = item.arrow.startswith("->")
            local_path = str(item.src if to_anbernic else item.dst)
            remote_path = str(item.dst if to_anbernic else item.src)
            try:
                with repository.connect() as conn:
                    log_sync_event(
                        conn,
                        local_path=local_path,
                        remote_path=remote_path,
                        direction="upload" if to_anbernic else "download",
                        local_mtime=None,
                        remote_mtime=None,
                        result=result,
                        message=message,
                        created_at=_dt2.datetime.now(tz=_dt2.UTC).strftime("%Y-%m-%dT%H:%M:%S"),
                    )
                    conn.commit()
            except Exception:
                _logger.debug("No se pudo escribir en save_sync_log (SD auto-sync)", exc_info=True)

        def _on_event(tag: str, item: cable_engine.CopyPlanItem, note: str) -> None:
            nonlocal errors
            if tag == "ERROR":
                errors += 1
                _log_file.write(f"ERROR {item.src} -> {item.dst}: {note}\n")
                _sql_log(item, "error", note)
            else:
                _log_file.write(f"COPY {item.arrow} {item.src} -> {item.dst}\n")
                if tag == "COPY":
                    _sql_log(item, "ok")

        for item in items:
            if item.dst.exists():
                side = "anbernic" if item.dst.is_relative_to(ab_root) else "pc"
                rel = item.dst.relative_to(ab_root if side == "anbernic" else pc_root)
                backup_path = backup_dir / side / rel
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item.dst, backup_path)
                _log_file.write(f"BACKUP {side} {rel} -> {backup_path}\n")
            tag, size = cable_engine.copy_item(item, policy, on_event=_on_event)
            if tag == "COPY":
                copied += 1
                copied_bytes += size

        # ponytail: recorre ambos árboles una vez más solo para reportar
        # "Omitidos" (empates de mtime en modo "newest", que plan_direction
        # ya excluye del plan). Árboles de saves son pequeños; si esto pesa,
        # exponer el conteo desde plan_direction en vez de recalcularlo aquí.
        if direction == "newest":
            pc_index = {
                f.relative_to(pc_root): f for f in cable_engine.iter_files(pc_root) if _wanted(f)
            }
            for f in cable_engine.iter_files(ab_root):
                if not _wanted(f):
                    continue
                try:
                    rel = f.relative_to(ab_root)
                except ValueError:
                    continue
                pc_f = pc_index.get(rel)
                if pc_f is not None and pc_f.stat().st_mtime == f.stat().st_mtime:
                    skipped += 1

        finish_ts = _dt2.datetime.now(tz=_dt2.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        _log_file.write(
            f"=== DONE copied={copied} skipped={skipped} errors={errors} bytes={copied_bytes} ===\n"
        )

        job_result = {
            "dry_run": False,
            "direction": direction,
            "use_adb": False,
            "copied": copied,
            "skipped": skipped,
            "sha1_skipped": 0,
            "safe_mode_skipped_overwrites": 0,
            "errors": errors,
            "copied_bytes": copied_bytes,
            "cancelled": False,
            "details": [],
            "pc_file_count": 0,
            "ab_file_count": 0,
            "auto_sync": True,
            "source": "sd_card",
        }

        _sd_sync_status.update(
            {
                "state": "idle",
                "last_sync_at": finish_ts,
            }
        )

    except Exception as exc:
        _logger.exception("SD auto-sync error: %s", exc)
        _sd_sync_status.update({"state": "idle"})
        job_result = {"error": str(exc), "auto_sync": True, "source": "sd_card"}
    finally:
        if _log_file is not None:
            try:
                _log_file.close()
            except Exception:
                _logger.debug("No se pudo cerrar el log de cable-sync", exc_info=True)
        _jm.finish("cable_sync", job_result)


def _sd_card_sync_loop(config: AppConfig, get_repo_fn) -> None:
    """Daemon thread: polls for SD card drive letter, triggers Cable Sync when inserted."""
    import time as _time

    _sd_sync_status = _state._sd_sync_status
    _jm = _state._job_manager

    _last_available = False
    _last_sync_at = 0.0
    COOLDOWN = 60.0
    POLL_INTERVAL = 8.0

    while True:
        try:
            _time.sleep(POLL_INTERVAL)
            if (
                not config.anbernic_root
                or not config.library_root
                or not config.sync.auto_sync_enabled
            ):
                _sd_sync_status["state"] = "disabled"
                _last_available = False
                continue

            ab_path = Path(config.anbernic_root)
            try:
                currently_available = ab_path.exists() and ab_path.is_dir()
            except Exception:
                _logger.debug("No se pudo comprobar disponibilidad de %s", ab_path, exc_info=True)
                currently_available = False

            just_inserted = currently_available and not _last_available
            _last_available = currently_available

            if currently_available:
                _sd_sync_status["state"] = "watching"
                _sd_sync_status["drive"] = config.anbernic_root
            else:
                _sd_sync_status["state"] = "waiting"
                _sd_sync_status.pop("drive", None)

            if just_inserted:
                now = _time.monotonic()
                if now - _last_sync_at < COOLDOWN:
                    continue
                started = _jm.start("cable_sync", lambda: _run_sd_auto_sync(config, get_repo_fn))
                if started.get("status") == "already_running":
                    continue

                _sd_sync_status["state"] = "syncing"
                import datetime as _dt_sd

                _sd_sync_status["last_sync_at"] = _dt_sd.datetime.now(tz=_dt_sd.UTC).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                _last_sync_at = now

        except Exception as exc:
            _logger.debug("SD sync daemon exception: %s", exc)
            try:
                _sd_sync_status["state"] = "waiting"
            except Exception:
                _logger.debug("No se pudo restaurar el estado de SD-sync", exc_info=True)
