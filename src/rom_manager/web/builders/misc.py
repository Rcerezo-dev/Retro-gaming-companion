"""Miscellaneous response builders: assets, sync log, config, scrape, cable preview.

Pure functions: typed params → JSON-ready dicts. No global job state.
"""

from __future__ import annotations

import os as _os
from pathlib import Path

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository


def _build_assets(repository: LibraryRepository, source_root: str | None = None) -> dict:
    return {"stats": repository.get_asset_platform_stats(source_root=source_root)}


def _build_sync_log(repository: LibraryRepository) -> dict:
    entries = repository.get_sync_log(limit=200)
    return {"entries": entries}


def _build_config(config: AppConfig) -> dict:
    from rom_manager.config import validate as _validate_config

    def _db_size(p: Path) -> int | None:
        try:
            return p.stat().st_size if p.exists() else 0
        except OSError:
            return None

    return {
        "warnings": _validate_config(config),
        "library_root": str(config.library_root) if config.library_root else None,
        "anbernic_root": config.anbernic_root or "",
        "device_name": config.device_name or "Consola Android",
        "rclone_remote": config.sync.rclone_remote or None,
        "web_host": config.web_host,
        "web_port": config.web_port,
        "screenscraper_user": config.credentials.screenscraper_user or None,
        "screenscraper_pass_set": bool(config.credentials.screenscraper_pass),
        "screenscraper_dev_id": config.credentials.screenscraper_dev_id or None,
        "screenscraper_dev_pass_set": bool(config.credentials.screenscraper_dev_pass),
        "chdman": config.chdman,
        "adb": config.adb,
        "ra_api_key_set": bool(config.credentials.ra_api_key),
        "ra_username": config.credentials.ra_username or None,
        "pc_db_path": str(config.database_path),
        "pc_db_size": _db_size(config.database_path),
        "android_db_path": str(config.database_path_android),
        "android_db_size": _db_size(config.database_path_android),
        "inbox_path": config.inbox.path or "",
        "inbox_target_root": config.inbox.target_root or "",
        "inbox_auto_process": config.inbox.auto_process,
        "inbox_delete_source": config.inbox.delete_source,
        "sync_sources": [
            {"name": s.name, "local_dir": s.local_dir, "remote": s.remote, "sync_all": s.sync_all}
            for s in config.sync.sync_sources
        ],
        "retroarch_path": config.retroarch_path or "",
        "esde_path": config.esde_path or "",
        "launcher_cores": config.launcher_cores or {},
        "backup_saves_enabled": config.backup.saves_enabled,
        "backup_saves_keep_n": config.backup.saves_keep_n,
        "notify_desktop": config.notify_desktop,
        "saves_remote": config.sync.saves_remote or "",
        "states_remote": config.sync.states_remote or "",
        "ra_config_dir": config.sync.ra_config_dir or "",
        "ra_config_remote": config.sync.ra_config_remote or "",
        "playtime_remote": config.sync.playtime_remote or "",
    }


def _build_scrape_summary(repository: LibraryRepository) -> dict:
    return {
        "platforms": repository.get_scraped_platform_summary(),
        "description_coverage": repository.get_description_coverage(),  # SAGE-1
    }


def _build_cable_sync_preview(qs: dict, config: AppConfig) -> dict:
    """Count saves on PC and Android side for a quick pre-sync summary."""
    mode = qs.get("mode", ["sd"])[0]
    direction = qs.get("direction", ["pc_to_anbernic"])[0]
    pc_path_s = (qs.get("pc_path", [None])[0] or "").strip() or str(config.library_root or "")
    ab_path_s = (qs.get("ab_path", [None])[0] or "").strip()

    save_exts: frozenset[str] = frozenset(config.save_extensions)

    def _count_saves(root: Path) -> int:
        count = 0
        try:
            for dirpath, dirs, files in _os.walk(root):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for fname in files:
                    if Path(fname).suffix.lower() in save_exts:
                        count += 1
        except OSError:
            pass
        return count

    pc_saves: int | None = None
    if pc_path_s:
        pc_root = Path(pc_path_s)
        if pc_root.is_dir():
            pc_saves = _count_saves(pc_root)

    android_saves: int | None = None
    android_message: str | None = None

    if mode == "adb":
        android_message = "no accesible en modo ADB (conecta y detecta el dispositivo)"
    elif ab_path_s:
        ab_root = Path(ab_path_s)
        if ab_root.is_dir():
            android_saves = _count_saves(ab_root)
        else:
            android_message = f"ruta no encontrada: {ab_path_s}"
    else:
        android_message = "introduce la ruta de la tarjeta SD / consola Android"

    to_copy: int | None = None
    if direction in ("pc_to_anbernic",) and pc_saves is not None and android_saves is not None:
        to_copy = max(0, pc_saves - android_saves)
    elif direction == "anbernic_to_pc" and pc_saves is not None and android_saves is not None:
        to_copy = max(0, android_saves - pc_saves)
    elif direction == "newest" and pc_saves is not None and android_saves is not None:
        to_copy = abs(pc_saves - android_saves)

    return {
        "pc_saves": pc_saves,
        "android_saves": android_saves,
        "android_message": android_message,
        "to_copy": to_copy,
        "mode": mode,
        "direction": direction,
    }
