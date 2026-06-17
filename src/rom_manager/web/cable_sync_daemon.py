"""Auto-sync ADB daemon and SD card sync daemon threads.

Extracted from server.py (Session 19). Global state in server.py is accessed
via late imports inside each function to avoid circular imports at load time.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from rom_manager.config import AppConfig

_logger = logging.getLogger(__name__)


def _auto_sync_loop(config: AppConfig, get_repo_fn) -> None:
    """Daemon thread: polls ADB every 10 s, triggers Cable Sync when a device connects."""
    import datetime as _dt
    import time as _time

    import rom_manager.web.server as _srv

    _job_lock = _srv._job_lock
    _jobs = _srv._jobs
    _cable_progress = _srv._cable_progress
    _job_results = _srv._job_results

    _POLL_INTERVAL = 10  # seconds between ADB polls
    _COOLDOWN = 30  # seconds to wait after a sync before syncing again
    _last_sync_ts: float = 0.0

    while True:
        try:
            _time.sleep(_POLL_INTERVAL)

            # Don't poll if a cable_sync job is already running
            with _job_lock:
                cable_running = _jobs.get("cable_sync", False)
            if cable_running:
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
                # adb not found or timed out — silently skip
                continue

            current_serials = {d.serial for d in devices if d.ready}

            # Clear device_prompt when the device disconnects
            if not current_serials and _srv._auto_sync_status.get("state") == "device_prompt":
                _srv._auto_sync_status["state"] = "waiting"

            # Detect newly connected devices
            new_serials = current_serials - _srv._auto_sync_last_devices
            _srv._auto_sync_last_devices = current_serials

            if not new_serials:
                continue

            # If known_devices filter is set, only react to those
            known = config.auto_sync_known_devices
            if known:
                new_serials = {s for s in new_serials if s in known}
            if not new_serials:
                continue

            serial = next(iter(new_serials))

            if not _srv._auto_sync_enabled:
                # Auto-sync disabled: show prompt in UI, let user decide
                _logger.info(
                    "Auto-sync: new device %s — auto-sync disabled, showing prompt", serial
                )
                _srv._auto_sync_status = {
                    "state": "device_prompt",
                    "last_device": serial,
                    "last_sync_at": _srv._auto_sync_status.get("last_sync_at"),
                    "last_error": None,
                }
                continue

            _logger.info("Auto-sync: new device %s — starting sync", serial)

            now_str = _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            _srv._auto_sync_status = {
                "state": "syncing",
                "last_device": serial,
                "last_sync_at": now_str,
                "last_error": None,
            }

            # Mark cable_sync job as running
            with _job_lock:
                if _jobs.get("cable_sync"):
                    _srv._auto_sync_status["state"] = "waiting"
                    continue
                _jobs["cable_sync"] = True

            _last_sync_ts = _time.monotonic()

            def _run_auto_sync(serial: str = serial) -> None:
                import datetime as _dt2
                import os
                from pathlib import PurePosixPath

                _log_file = None
                try:
                    from rom_manager.config import get_adb_sync_sources

                    pc_root = config.library_root
                    direction = config.auto_sync_direction
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
                                "android_saves": config.auto_sync_android_path.rstrip("/"),
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

                    copied = skipped = errors = 0
                    copied_bytes = 0

                    def _update_prog(fname: str = "") -> None:
                        _cable_progress.update(
                            {
                                "copied": copied,
                                "bytes_copied": copied_bytes,
                                "speed_bps": 0.0,
                                "current_file": fname,
                            }
                        )

                    from rom_manager.sync.adb_transport import AdbTransport

                    transport = AdbTransport(config.adb, serial, timeout=60)

                    def _adb_copy_to_pc(adb_info, local_root: Path, android_prefix: str) -> None:
                        nonlocal copied, errors, copied_bytes
                        name = PurePosixPath(adb_info.android_path).name
                        rel_posix = adb_info.android_path.removeprefix(android_prefix)
                        local_dst = local_root / Path(rel_posix.replace("/", os.sep))
                        try:
                            size = transport.pull(adb_info.android_path, local_dst, dry_run=False)
                            _log("ADB←", adb_info.android_path, str(local_dst))
                            copied += 1
                            copied_bytes += size
                            _update_prog(name)
                        except OSError as exc:
                            _log("ERROR", adb_info.android_path, str(local_dst), str(exc))
                            errors += 1

                    def _adb_copy_to_device(
                        local_src: Path, local_root: Path, android_root: str
                    ) -> None:
                        nonlocal copied, errors, copied_bytes
                        rel = local_src.relative_to(local_root)
                        android_dst = android_root.rstrip("/") + "/" + rel.as_posix()
                        try:
                            size = transport.push(local_src, android_dst, dry_run=False)
                            _log("ADB→", str(local_src), android_dst)
                            copied += 1
                            copied_bytes += size
                            _update_prog(local_src.name)
                        except OSError as exc:
                            _log("ERROR", str(local_src), android_dst, str(exc))
                            errors += 1

                    _cable_progress.update(
                        {
                            "copied": 0,
                            "bytes_copied": 0,
                            "speed_bps": 0.0,
                            "current_file": "Auto-sync: listando saves en el dispositivo…",
                        }
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

                    _job_results["cable_sync"] = {
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
                    _srv._auto_sync_status = {
                        "state": "idle",
                        "last_device": serial,
                        "last_sync_at": finish_ts,
                        "last_error": None if errors == 0 else f"{errors} errores",
                    }

                except Exception as exc:
                    _logger.exception("Auto-sync error: %s", exc)
                    _srv._auto_sync_status = {
                        "state": "idle",
                        "last_device": serial,
                        "last_sync_at": _srv._auto_sync_status.get("last_sync_at"),
                        "last_error": str(exc),
                    }
                    _job_results["cable_sync"] = {"error": str(exc), "auto_sync": True}
                finally:
                    if _log_file is not None:
                        try:
                            _log_file.close()
                        except Exception:
                            pass
                    with _job_lock:
                        _cable_progress.clear()
                        _jobs["cable_sync"] = False

            threading.Thread(target=_run_auto_sync, daemon=True).start()

        except Exception as exc:
            # Never crash the daemon
            _logger.debug("Auto-sync daemon exception: %s", exc)
            try:
                _srv._auto_sync_status["state"] = "waiting"
            except Exception:
                pass


# ── SD card auto-sync daemon ───────────────────────────────────────────────────


def _run_sd_auto_sync(config: AppConfig, get_repo_fn) -> None:  # noqa: ARG001
    """Run a filesystem Cable Sync triggered by SD card insertion."""
    import datetime as _dt2
    import os
    import shutil

    import rom_manager.web.server as _srv

    _sd_sync_status = _srv._sd_sync_status
    _job_results = _srv._job_results
    _job_lock = _srv._job_lock
    _jobs = _srv._jobs
    _cable_progress = _srv._cable_progress

    _log_file = None
    copied = 0
    skipped = 0
    errors = 0
    copied_bytes = 0

    try:
        pc_root = config.library_root
        ab_root = Path(config.anbernic_root)
        direction = config.auto_sync_direction or "newest"
        save_exts = frozenset(config.save_extensions)

        log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        _log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        ts0 = _dt2.datetime.now(tz=_dt2.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        _log_file.write(
            f"\n=== SD-AUTO-SYNC {ts0} | direction={direction} | ab={config.anbernic_root} ===\n"
        )

        def _iter_files(root: Path):
            try:
                for entry in os.scandir(root):
                    if entry.is_dir(follow_symlinks=False):
                        yield from _iter_files(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        yield Path(entry.path)
            except PermissionError:
                pass

        def _wanted(p: Path) -> bool:
            return p.suffix.lower() in save_exts

        def _rel(p: Path, root: Path) -> Path:
            try:
                return p.relative_to(root)
            except ValueError:
                return p

        def _mtime(p: Path) -> float:
            try:
                return p.stat().st_mtime
            except OSError:
                return 0.0

        def _copy(src: Path, dst: Path) -> None:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        if pc_root is None:
            _log_file.write("ERROR: library_root not configured\n")
            return

        if direction in ("pc_to_anbernic", "newest"):
            for f in _iter_files(pc_root):
                if not _wanted(f):
                    continue
                rel = _rel(f, pc_root)
                dst = ab_root / rel
                if dst.exists():
                    if direction == "newest" and _mtime(f) <= _mtime(dst):
                        skipped += 1
                        continue
                    elif direction == "pc_to_anbernic":
                        pass  # always overwrite
                try:
                    sz = f.stat().st_size
                    _copy(f, dst)
                    copied += 1
                    copied_bytes += sz
                    _log_file.write(f"COPY pc→ab  {rel}\n")
                except Exception as e:
                    errors += 1
                    _log_file.write(f"ERROR pc→ab {rel}: {e}\n")

        if direction in ("anbernic_to_pc", "newest"):
            for f in _iter_files(ab_root):
                if not _wanted(f):
                    continue
                rel = _rel(f, ab_root)
                dst = pc_root / rel
                if dst.exists():
                    if direction == "newest" and _mtime(f) <= _mtime(dst):
                        skipped += 1
                        continue
                    elif direction == "anbernic_to_pc":
                        pass
                try:
                    sz = f.stat().st_size
                    _copy(f, dst)
                    copied += 1
                    copied_bytes += sz
                    _log_file.write(f"COPY ab→pc  {rel}\n")
                except Exception as e:
                    errors += 1
                    _log_file.write(f"ERROR ab→pc {rel}: {e}\n")

        finish_ts = _dt2.datetime.now(tz=_dt2.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        _log_file.write(
            f"=== DONE copied={copied} skipped={skipped} errors={errors} bytes={copied_bytes} ===\n"
        )

        _job_results["cable_sync"] = {
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
        _job_results["cable_sync"] = {"error": str(exc), "auto_sync": True, "source": "sd_card"}
    finally:
        if _log_file is not None:
            try:
                _log_file.close()
            except Exception:
                pass
        with _job_lock:
            _cable_progress.clear()
            _jobs["cable_sync"] = False


def _sd_card_sync_loop(config: AppConfig, get_repo_fn) -> None:
    """Daemon thread: polls for SD card drive letter, triggers Cable Sync when inserted."""
    import time as _time

    import rom_manager.web.server as _srv

    _sd_sync_status = _srv._sd_sync_status
    _job_lock = _srv._job_lock
    _jobs = _srv._jobs

    _last_available = False
    _last_sync_at = 0.0
    COOLDOWN = 60.0
    POLL_INTERVAL = 8.0

    while True:
        try:
            _time.sleep(POLL_INTERVAL)
            if not config.anbernic_root or not config.library_root or not config.auto_sync_enabled:
                _sd_sync_status["state"] = "disabled"
                _last_available = False
                continue

            ab_path = Path(config.anbernic_root)
            try:
                currently_available = ab_path.exists() and ab_path.is_dir()
            except Exception:
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
                with _job_lock:
                    if _jobs.get("cable_sync"):
                        continue
                    _jobs["cable_sync"] = True

                _sd_sync_status["state"] = "syncing"
                import datetime as _dt_sd

                _sd_sync_status["last_sync_at"] = _dt_sd.datetime.now(tz=_dt_sd.UTC).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                _last_sync_at = now

                threading.Thread(
                    target=_run_sd_auto_sync,
                    args=(config, get_repo_fn),
                    daemon=True,
                ).start()

        except Exception as exc:
            _logger.debug("SD sync daemon exception: %s", exc)
            try:
                _sd_sync_status["state"] = "waiting"
            except Exception:
                pass
