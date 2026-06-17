from __future__ import annotations

import logging
import threading
from pathlib import Path

import rom_manager.web.state as _state
from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository

_logger = logging.getLogger(__name__)
_HEALTH_CHECK_INTERVAL_DAYS = 7


# ── Health-check scheduler (S37-1) ────────────────────────────────────────────


def _health_schedule_path(config: AppConfig) -> Path:
    return config.data_dir / "health_schedule.json"


def _read_health_schedule(config: AppConfig) -> dict:
    import json as _json

    try:
        return _json.loads(_health_schedule_path(config).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_health_schedule(config: AppConfig, *, ok: int, corrupted: int, missing: int) -> None:
    import datetime as _dt
    import json as _json

    data = {
        "last_run_at": _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_ok": ok,
        "last_corrupted": corrupted,
        "last_missing": missing,
    }
    p = _health_schedule_path(config)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(_json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        _logger.debug("No se pudo escribir health_schedule: %s", exc)


def _health_scheduler_loop(config: AppConfig, get_repo_fn) -> None:  # type: ignore[type-arg]
    """Daemon: lanza un health check automático una vez a la semana."""
    import datetime as _dt
    import time as _time

    _time.sleep(60)  # esperar a que el servidor termine de arrancar

    while True:
        try:
            schedule = _read_health_schedule(config)
            last_run_raw = schedule.get("last_run_at")
            overdue = True
            elapsed = None
            if last_run_raw:
                try:
                    last_run = _dt.datetime.fromisoformat(last_run_raw.replace("Z", "+00:00"))
                    elapsed = (_dt.datetime.now(tz=_dt.UTC) - last_run).days
                    overdue = elapsed >= _HEALTH_CHECK_INTERVAL_DAYS
                except Exception:
                    pass

            if overdue and not _state._job_manager.get_status()["health_check_running"]:
                repository = get_repo_fn()
                _logger.info(
                    "Health check programado iniciando (días desde último: %s)",
                    elapsed if elapsed is not None else "?",
                )
                _cancel = _state._job_manager.cancel_event("health_check")

                def _scheduled_run(_repo=repository, _c=_cancel) -> None:
                    job_result = None
                    try:
                        from rom_manager.utils.health_checker import check_library_health

                        def _prog(current: int, total: int, filename: str) -> None:
                            _state._job_manager.update_progress(
                                "health_check",
                                {"current": current, "total": total, "current_file": filename},
                            )

                        summary = check_library_health(_repo, progress_cb=_prog, cancel_event=_c)
                        job_result = {
                            "ok": summary.ok,
                            "corrupted": summary.corrupted,
                            "missing": summary.missing,
                            "cancelled": _c.is_set(),
                            "auto": True,
                            "issues": [
                                {
                                    "source_path": r.source_path,
                                    "status": r.status,
                                    "stored_sha1": r.stored_sha1[:12],
                                    "computed_sha1": r.computed_sha1[:12]
                                    if r.computed_sha1
                                    else "",
                                    "platform": r.platform,
                                    "canonical_title": r.canonical_title,
                                }
                                for r in summary.results
                            ],
                        }
                        _write_health_schedule(
                            config,
                            ok=summary.ok,
                            corrupted=summary.corrupted,
                            missing=summary.missing,
                        )
                        if not _c.is_set() and config.notify_desktop:
                            from rom_manager.utils.notifier import notify

                            if summary.corrupted or summary.missing:
                                notify(
                                    "Retro Vault — Health Check",
                                    f"⚠ {summary.corrupted} corruptos, {summary.missing} desaparecidos",
                                )
                            else:
                                notify(
                                    "Retro Vault — Health Check",
                                    f"✓ {summary.ok} ROMs verificados, sin problemas",
                                )
                    except Exception as exc:
                        _logger.error("Error en health check programado: %s", exc)
                    finally:
                        _state._job_manager.finish("health_check", job_result)

                _state._job_manager.start("health_check", _scheduled_run)

        except Exception as exc:
            _logger.debug("Error en health scheduler: %s", exc)

        _time.sleep(3600)  # revisar cada hora


# ── Inbox watcher daemon ──────────────────────────────────────────────────────


def _inbox_watcher_loop(config: AppConfig, repository: LibraryRepository) -> None:
    """Daemon: vigila la carpeta inbox y lanza el pipeline cuando hay archivos."""
    import time as _time
    from pathlib import Path as _Path

    from rom_manager.web.inbox_pipeline import _run_inbox_pipeline, _watcher_now

    while True:
        try:
            _time.sleep(30)
            if not config.inbox_path or not config.inbox_auto_process:
                _state._inbox_watcher_status.update(
                    {
                        "watching": False,
                        "last_check": None,
                        "pending_files": 0,
                    }
                )
                continue

            inbox = _Path(config.inbox_path).resolve()
            if not inbox.exists():
                _state._inbox_watcher_status.update(
                    {
                        "watching": True,
                        "last_check": _watcher_now(),
                        "pending_files": 0,
                    }
                )
                continue

            pending = [
                e
                for e in inbox.iterdir()
                if e.is_file() and not e.name.startswith(".") and not e.name.startswith("_")
            ]
            _state._inbox_watcher_status.update(
                {
                    "watching": True,
                    "last_check": _watcher_now(),
                    "pending_files": len(pending),
                }
            )

            if pending and not _state._job_manager.get_status()["inbox_running"]:
                _logger.info(
                    "Inbox watcher: %d archivos detectados, lanzando pipeline", len(pending)
                )
                _state._inbox_watcher_status["trigger_ts"] = _time.time()
                target_root_str = config.inbox_target_root or (
                    str(config.library_root) if config.library_root else ""
                )

                def _watcher_run(_tr=target_root_str) -> None:
                    _run_inbox_pipeline(
                        config.inbox_path,
                        _tr,
                        config.inbox_delete_source,
                        repository,
                        config,
                        _state._job_manager,
                    )

                _state._job_manager.start("inbox", _watcher_run)

        except Exception as exc:
            _logger.debug("Error en inbox watcher: %s", exc)


# ── Punto de entrada único ────────────────────────────────────────────────────


def start_all(config: AppConfig, repository: LibraryRepository) -> None:
    """Arranca todos los daemons de background. Llamado desde serve()."""
    from rom_manager.web.cable_sync_daemon import _auto_sync_loop, _sd_card_sync_loop

    if config.auto_sync_enabled:
        t = threading.Thread(
            target=_auto_sync_loop,
            args=(config, lambda: repository),
            daemon=True,
        )
        t.name = "auto-sync-daemon"
        t.start()
        _logger.info("Auto-sync daemon arrancado (polling cada 10 s)")

    t_sd = threading.Thread(
        target=_sd_card_sync_loop,
        args=(config, lambda: repository),
        daemon=True,
    )
    t_sd.name = "sd-sync-daemon"
    t_sd.start()
    _logger.info("SD card sync daemon arrancado (polling cada 8 s)")

    t_inbox = threading.Thread(
        target=_inbox_watcher_loop,
        args=(config, repository),
        daemon=True,
    )
    t_inbox.name = "inbox-watcher-daemon"
    t_inbox.start()
    _logger.info("Inbox watcher daemon arrancado")

    t_health = threading.Thread(
        target=_health_scheduler_loop,
        args=(config, lambda: repository),
        daemon=True,
    )
    t_health.name = "health-check-scheduler"
    t_health.start()
    _logger.info(
        "Health check scheduler arrancado (intervalo: %d días)", _HEALTH_CHECK_INTERVAL_DAYS
    )
