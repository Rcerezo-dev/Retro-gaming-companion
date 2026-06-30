from __future__ import annotations

from typing import TYPE_CHECKING

import rom_manager.web.state as _state

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router


def register_cloud(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    repo_android: LibraryRepository,
    job_manager: JobManager,
) -> None:
    """Register rclone / cloud-sync / auto-sync routes on *router*."""

    # ── GET /api/rclone-export-config ────────────────────────────────────────
    @router.get("/api/rclone-export-config")
    def get_rclone_export_config(ctx) -> None:
        lan_exposed = config.web_host not in ("127.0.0.1", "localhost")
        if lan_exposed and not config.credentials.web_pin_hash and not config.web_allow_lan:
            ctx._send_json(
                {
                    "error": "Activa un PIN en Settings antes de exportar la config rclone cuando el servidor es accesible por red."
                }
            )
            return
        body, ct = _handle_rclone_export_config(config)
        ctx._send(200, ct, body)

    # ── GET /s ── bootstrap script para Termux/Anbernic ──────────────────────
    @router.get("/s")
    def get_bootstrap_script(ctx) -> None:
        """Serve a one-liner bootstrap shell script for Termux on the Anbernic.

        Usage on the Anbernic (Termux):
            curl -s http://<PC-IP>:7777/s | bash
        """
        from rom_manager.web.lan import get_lan_ip

        server_ip = get_lan_ip() or "192.168.1.160"
        server_url = f"http://{server_ip}:{config.web_port}"
        script = _build_bootstrap_script(server_url)
        ctx._send(200, "text/plain; charset=utf-8", script.encode())

    # ── GET /api/rclone-status ───────────────────────────────────────────────
    @router.get("/api/rclone-status")
    def get_rclone_status(ctx) -> None:
        ctx._send_json(_handle_rclone_status(config))

    # ── POST /api/rclone-open-config ─────────────────────────────────────────
    @router.post("/api/rclone-open-config")
    def post_rclone_open_config(ctx) -> None:
        ctx._send_json(_handle_rclone_open_config(config))

    # ── POST /api/rclone-test-remote ─────────────────────────────────────────
    @router.post("/api/rclone-test-remote")
    def post_rclone_test_remote(ctx) -> None:
        remote = ctx._post_data.get("remote", "").strip()
        ctx._send_json(_handle_rclone_test_remote(config, remote))

    # ── GET /api/auto-sync-status ────────────────────────────────────────────
    @router.get("/api/auto-sync-status")
    def get_auto_sync_status(ctx) -> None:
        ctx._send_json(
            {
                "enabled": _state._auto_sync_enabled,
                "status": dict(_state._auto_sync_status),
                "config": {
                    "direction": config.sync.auto_sync_direction,
                    "conflict_policy": config.sync.conflict_policy,
                    "android_path": config.sync.auto_sync_android_path,
                },
            }
        )

    # ── GET /api/sd-sync-status ──────────────────────────────────────────────
    @router.get("/api/sd-sync-status")
    def get_sd_sync_status(ctx) -> None:
        ctx._send_json(dict(_state._sd_sync_status))

    # ── POST /api/sync ───────────────────────────────────────────────────────
    @router.post("/api/sync")
    def post_sync(ctx) -> None:
        _do_sync(ctx, ctx._post_data, config, repository, job_manager)

    # ── POST /api/auto-sync-toggle ───────────────────────────────────────────
    @router.post("/api/auto-sync-toggle")
    def post_auto_sync_toggle(ctx) -> None:
        _state._auto_sync_enabled = not _state._auto_sync_enabled
        config.sync.auto_sync_enabled = _state._auto_sync_enabled
        ctx._send_json({"enabled": _state._auto_sync_enabled})

    # ── POST /api/auto-sync-save ─────────────────────────────────────────────
    @router.post("/api/auto-sync-save")
    def post_auto_sync_save(ctx) -> None:
        _do_auto_sync_save(ctx, ctx._post_data, config)

    # ── POST /api/migrate-split-db ───────────────────────────────────────────
    @router.post("/api/migrate-split-db")
    def post_migrate_split_db(ctx) -> None:
        _do_migrate_split_db(ctx, config, repository, repo_android)


def _handle_rclone_export_config(config: AppConfig) -> tuple[bytes, str]:
    """Return the local rclone config file contents as bytes, or an error message."""
    import shutil as _sh
    import subprocess as _sp

    rclone_bin = config.rclone_binary or "rclone"
    if not _sh.which(rclone_bin) and not __import__("pathlib").Path(rclone_bin).exists():
        return b"# rclone not found on this machine\n", "text/plain; charset=utf-8"
    try:
        r = _sp.run([rclone_bin, "config", "file"], capture_output=True, text=True, timeout=8)
        cfg_path = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        cfg_file = __import__("pathlib").Path(cfg_path)
        if cfg_file.exists():
            return cfg_file.read_bytes(), "text/plain; charset=utf-8"
        return b"# rclone config file not found\n", "text/plain; charset=utf-8"
    except Exception as exc:
        return f"# error reading rclone config: {exc}\n".encode(), "text/plain; charset=utf-8"


def _handle_rclone_status(config: AppConfig) -> dict:
    """Check if rclone is installed and list configured remotes."""
    import shutil as _sh
    import subprocess as _sp

    rclone_bin = config.rclone_binary or "rclone"
    if not _sh.which(rclone_bin) and not __import__("pathlib").Path(rclone_bin).exists():
        return {"installed": False, "version": None, "remotes": [], "binary": rclone_bin}
    try:
        r = _sp.run([rclone_bin, "version"], capture_output=True, text=True, timeout=8)
        version_line = r.stdout.strip().splitlines()[0] if r.stdout.strip() else "unknown"
        remotes_r = _sp.run([rclone_bin, "listremotes"], capture_output=True, text=True, timeout=8)
        remotes = [ln.rstrip(":") for ln in remotes_r.stdout.strip().splitlines() if ln.strip()]
        return {
            "installed": True,
            "version": version_line,
            "remotes": remotes,
            "binary": rclone_bin,
        }
    except Exception as exc:
        return {
            "installed": False,
            "version": None,
            "remotes": [],
            "binary": rclone_bin,
            "error": str(exc),
        }


def _handle_rclone_open_config(config: AppConfig) -> dict:
    """Open a terminal window running 'rclone config' so the user can add remotes."""
    import subprocess as _sp
    import sys as _sys

    rclone_bin = config.rclone_binary or "rclone"
    try:
        if _sys.platform == "win32":
            _sp.Popen(
                ["cmd", "/c", "start", "cmd", "/k", rclone_bin, "config"],
                creationflags=_sp.CREATE_NEW_CONSOLE,
            )
        elif _sys.platform == "darwin":
            _sp.Popen(["open", "-a", "Terminal", "--args", rclone_bin, "config"])
        else:
            for term in ("x-terminal-emulator", "xterm", "gnome-terminal", "konsole"):
                import shutil as _sh

                if _sh.which(term):
                    _sp.Popen([term, "-e", f"{rclone_bin} config"])
                    break
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _handle_rclone_test_remote(config: AppConfig, remote: str) -> dict:
    """Run 'rclone lsd <remote>:' to verify the connection is working."""
    import shutil as _sh
    import subprocess as _sp

    if not remote:
        return {"ok": False, "error": "remote requerido"}
    rclone_bin = config.rclone_binary or "rclone"
    if not _sh.which(rclone_bin) and not __import__("pathlib").Path(rclone_bin).exists():
        return {"ok": False, "error": "rclone no encontrado"}
    remote_arg = remote if remote.endswith(":") else remote + ":"
    try:
        r = _sp.run(
            [rclone_bin, "lsd", remote_arg, "--max-depth", "1"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 0:
            lines = [ln.strip() for ln in r.stdout.strip().splitlines() if ln.strip()]
            return {"ok": True, "remote": remote, "entries": len(lines), "sample": lines[:5]}
        return {"ok": False, "remote": remote, "error": r.stderr.strip() or "error desconocido"}
    except _sp.TimeoutExpired:
        return {
            "ok": False,
            "remote": remote,
            "error": "timeout — comprueba la conexión a internet",
        }
    except Exception as exc:
        return {"ok": False, "remote": remote, "error": str(exc)}


def _do_sync(
    ctx, data: dict, config: AppConfig, repository: LibraryRepository, job_manager: JobManager
) -> None:
    from rom_manager.web.builders.common import _utc_now_str

    dry_run = data.get("dry_run", True)

    def run() -> None:
        job_result = None
        if _state._tray_instance:
            _state._tray_instance.set_status("Sincronizando…")
        try:
            from pathlib import Path as _Path

            from rom_manager.config import SyncSource as _SyncSource
            from rom_manager.sync.rclone_transport import RcloneTransport
            from rom_manager.sync.save_syncer import sync_saves

            sources = list(config.sync.sync_sources)
            if config.sync.ra_config_dir and config.sync.ra_config_remote:
                sources.append(
                    _SyncSource(
                        name="RetroArch Config (.opt)",
                        local_dir=config.sync.ra_config_dir,
                        remote=config.sync.ra_config_remote,
                        sync_all=True,
                    )
                )
            if not sources:
                job_result = {
                    "error": "No hay fuentes de sync configuradas. "
                    "Añade [[sync.sources]] en config.toml."
                }
                return

            if not dry_run and config.backup.pre_sync and config.library_root:
                try:
                    from rom_manager.backup.save_backup import create_saves_zip

                    _zip_dest = config.data_dir / "saves-backup"
                    create_saves_zip(
                        saves_dirs=[_Path(str(config.library_root))],
                        save_extensions=set(config.save_extensions),
                        output_dir=_zip_dest,
                    )
                except Exception as _bk_exc:
                    import logging

                    logging.getLogger(__name__).warning(
                        "Pre-sync backup failed (non-fatal): %s", _bk_exc
                    )

            transport = RcloneTransport(rclone=config.rclone_binary)
            all_results = []
            for source in sources:
                saves_dir = _Path(source.local_dir)
                if not saves_dir.exists():
                    all_results.append(
                        {
                            "name": source.name,
                            "local_dir": source.local_dir,
                            "remote": source.remote,
                            "error": f"Directorio no encontrado: {source.local_dir}",
                            "uploaded": 0,
                            "downloaded": 0,
                            "up_to_date": 0,
                            "conflicts": 0,
                            "errors": 0,
                            "decisions": [],
                        }
                    )
                    continue
                exts = tuple() if source.sync_all else config.save_extensions
                try:
                    _bk_root = config.data_dir if config.backup.saves_enabled else None
                    from rom_manager.sync.delta_cache import DeltaCache as _DeltaCache

                    _delta = _DeltaCache(config.data_dir) if not dry_run else None
                    result, decisions = sync_saves(
                        saves_dir,
                        saves_remote=source.remote,
                        transport=transport,
                        repository=repository,
                        save_extensions=exts,
                        state_extensions=config.state_extensions
                        if not source.sync_all
                        else tuple(),
                        states_remote=None,
                        dry_run=dry_run,
                        backup_root=_bk_root,
                        backup_keep_n=config.backup.saves_keep_n,
                        delta_cache=_delta,
                        conflict_policy=config.sync.conflict_policy,
                    )
                    all_results.append(
                        {
                            "name": source.name,
                            "local_dir": source.local_dir,
                            "remote": source.remote,
                            "uploaded": result.uploaded,
                            "downloaded": result.downloaded,
                            "up_to_date": result.up_to_date,
                            "conflicts": result.conflicts,
                            "errors": result.errors,
                            "delta_skipped": result.delta_skipped,
                            "decisions": [
                                {"action": d.action, "relative": d.relative}
                                for d in decisions
                                if d.action != "up_to_date"
                            ],
                        }
                    )
                except Exception as exc:
                    all_results.append(
                        {
                            "name": source.name,
                            "local_dir": source.local_dir,
                            "remote": source.remote,
                            "error": str(exc),
                            "uploaded": 0,
                            "downloaded": 0,
                            "up_to_date": 0,
                            "conflicts": 0,
                            "errors": 0,
                            "decisions": [],
                        }
                    )

            # D2: implicit sync for saves/states remotes
            _bk_root = config.data_dir if config.backup.saves_enabled else None
            _implicit = []
            if config.sync.saves_remote and config.library_root:
                _implicit.append(
                    (
                        _Path(config.library_root) / "saves",
                        config.sync.saves_remote,
                        "Saves (permanentes)",
                        config.save_extensions,
                    )
                )
            if config.sync.states_remote and config.library_root:
                _implicit.append(
                    (
                        _Path(config.library_root) / "states",
                        config.sync.states_remote,
                        "States",
                        config.state_extensions,
                    )
                )
            for _dir, _remote, _name, _exts in _implicit:
                if not _dir.exists():
                    all_results.append(
                        {
                            "name": _name,
                            "local_dir": str(_dir),
                            "remote": _remote,
                            "error": f"Directorio no encontrado: {_dir}",
                            "uploaded": 0,
                            "downloaded": 0,
                            "up_to_date": 0,
                            "conflicts": 0,
                            "errors": 0,
                            "decisions": [],
                        }
                    )
                    continue
                try:
                    from rom_manager.sync.delta_cache import DeltaCache as _DeltaCache

                    _delta = _DeltaCache(config.data_dir) if not dry_run else None
                    # D2: For implicit saves/states sync, determine routing based on what type we're syncing
                    _is_states = "States" in _name
                    _saves_remote = _remote if not _is_states else None
                    _states_remote = _remote if _is_states else None
                    result, decisions = sync_saves(
                        _dir,
                        saves_remote=_saves_remote or _remote,
                        transport=transport,
                        repository=repository,
                        save_extensions=_exts,
                        state_extensions=_exts if _is_states else tuple(),
                        states_remote=_states_remote,
                        dry_run=dry_run,
                        backup_root=_bk_root,
                        backup_keep_n=config.backup.saves_keep_n,
                        delta_cache=_delta,
                        conflict_policy=config.sync.conflict_policy,
                    )
                    all_results.append(
                        {
                            "name": _name,
                            "local_dir": str(_dir),
                            "remote": _remote,
                            "uploaded": result.uploaded,
                            "downloaded": result.downloaded,
                            "up_to_date": result.up_to_date,
                            "conflicts": result.conflicts,
                            "errors": result.errors,
                            "delta_skipped": result.delta_skipped,
                            "decisions": [
                                {"action": d.action, "relative": d.relative}
                                for d in decisions
                                if d.action != "up_to_date"
                            ],
                        }
                    )
                except Exception as exc:
                    all_results.append(
                        {
                            "name": _name,
                            "local_dir": str(_dir),
                            "remote": _remote,
                            "error": str(exc),
                            "uploaded": 0,
                            "downloaded": 0,
                            "up_to_date": 0,
                            "conflicts": 0,
                            "errors": 0,
                            "decisions": [],
                        }
                    )

            _up = sum(r.get("uploaded", 0) for r in all_results)
            _down = sum(r.get("downloaded", 0) for r in all_results)
            _errs = sum(r.get("errors", 0) for r in all_results)
            job_result = {
                "dry_run": dry_run,
                "sources": all_results,
                "uploaded": _up,
                "downloaded": _down,
                "up_to_date": sum(r.get("up_to_date", 0) for r in all_results),
                "conflicts": sum(r.get("conflicts", 0) for r in all_results),
                "errors": _errs,
            }
            if not dry_run and config.notify_desktop:
                from rom_manager.utils.notifier import notify

                _parts: list[str] = []
                if _up:
                    _parts.append(f"{_up} subidos")
                if _down:
                    _parts.append(f"{_down} descargados")
                if not _parts:
                    _parts.append("Todo al día")
                _body = ", ".join(_parts)
                if _errs:
                    _body += f" ({_errs} errores)"
                notify("Retro Vault — Sync completado", _body)
            if not dry_run:
                _total_conflicts = sum(r.get("conflicts", 0) for r in all_results)
                if _errs:
                    _state._tray_instance and _state._tray_instance.set_status(
                        f"✗ Sync: {_errs} errores"
                    )
                elif _total_conflicts:
                    _state._tray_instance and _state._tray_instance.set_status(
                        f"⚠ Conflictos: {_total_conflicts}"
                    )
                else:
                    _ts = _utc_now_str()[:16].replace("T", " ")
                    _state._tray_instance and _state._tray_instance.set_status(f"Sync OK {_ts}")
                _state._auto_sync_status["last_sync_at"] = _utc_now_str()
                _state._auto_sync_status["last_error"] = (
                    (f"{_errs} errores en cloud sync") if _errs else None
                )
        except Exception as exc:
            job_result = {"error": str(exc)}
            _state._tray_instance and _state._tray_instance.set_status("✗ Error en sync")
        finally:
            job_manager.finish("sync", job_result)

    start_result = job_manager.start("sync", run)
    ctx._send_json({**start_result, "dry_run": dry_run})


def _do_auto_sync_save(ctx, data: dict, config: AppConfig) -> None:
    """Save auto-sync settings to config.toml and update in-memory config."""
    from rom_manager.config import write_config_toml

    updates: dict = {}
    if "sync.auto_sync_direction" in data:
        updates["sync.auto_sync_direction"] = data["sync.auto_sync_direction"]
        config.sync.auto_sync_direction = data["sync.auto_sync_direction"]
    if "sync.auto_sync_android_path" in data:
        updates["sync.auto_sync_android_path"] = data["sync.auto_sync_android_path"]
        config.sync.auto_sync_android_path = data["sync.auto_sync_android_path"]
    if "sync.conflict_policy" in data:
        updates["sync.conflict_policy"] = data["sync.conflict_policy"]
        config.sync.conflict_policy = data["sync.conflict_policy"]
    if "sync.auto_sync_enabled" in data:
        val = bool(data["sync.auto_sync_enabled"])
        updates["sync.auto_sync_enabled"] = val
        config.sync.auto_sync_enabled = val
        _state._auto_sync_enabled = val

    if updates:
        write_config_toml(config.project_root, updates)

    ctx._send_json({"saved": list(updates.keys()), "enabled": _state._auto_sync_enabled})


def _do_migrate_split_db(
    ctx, config: AppConfig, repository: LibraryRepository, repo_android: LibraryRepository
) -> None:
    """One-time migration: move Android-path games from PC repo to Android repo."""
    lib_root = str(config.library_root or "").lower().rstrip("/\\")
    if not lib_root:
        ctx._send_json(
            {"error": "library_root not configured — cannot determine which paths are Android"}
        )
        return

    migrated = 0
    errors: list[str] = []
    try:
        with repository.connect() as _conn:
            rows = _conn.execute(
                "SELECT id, original_filename, source_path, platform, file_type, "
                "relative_parent, region, extension, size_bytes, mtime, sha1, md5, "
                "crc32, set_type, created_at, updated_at, canonical_title, "
                "match_confidence, catalog_source "
                "FROM games"
            ).fetchall()

        android_rows = [r for r in rows if not r["source_path"].lower().startswith(lib_root)]

        from rom_manager.scanner.rom_scanner import utc_now as _now

        ts = _now()

        with repo_android.batch() as _android_conn:
            for row in android_rows:
                try:
                    repo_android.upsert_game(
                        original_filename=row["original_filename"],
                        source_path=row["source_path"],
                        platform=row["platform"],
                        file_type=row["file_type"],
                        relative_parent=row["relative_parent"] or "",
                        region=row["region"],
                        extension=row["extension"],
                        size_bytes=int(row["size_bytes"]),
                        mtime=int(row["mtime"] or 0),
                        sha1=row["sha1"] or "",
                        md5=row["md5"] or "",
                        crc32=row["crc32"] or "",
                        set_type=row["set_type"] or "",
                        timestamp=ts,
                        connection=_android_conn,
                    )
                    migrated += 1
                except Exception as exc:
                    errors.append(f"{row['source_path']}: {exc}")

        with repository.batch() as _pc_conn:
            for row in android_rows:
                _pc_conn.execute("DELETE FROM games WHERE source_path = ?", (row["source_path"],))

        with repository.connect() as _conn:
            save_rows = _conn.execute(
                "SELECT original_path, relative_parent, extension, size_bytes, created_at "
                "FROM saves"
            ).fetchall()

        android_saves = [
            r for r in save_rows if not r["original_path"].lower().startswith(lib_root)
        ]
        if android_saves:
            with repo_android.batch() as _android_conn:
                for row in android_saves:
                    try:
                        repo_android.upsert_save(
                            original_path=row["original_path"],
                            relative_parent=row["relative_parent"] or "",
                            extension=row["extension"],
                            size_bytes=int(row["size_bytes"]),
                            timestamp=ts,
                            connection=_android_conn,
                        )
                    except Exception as exc:
                        errors.append(f"save:{row['original_path']}: {exc}")
            with repository.batch() as _pc_conn:
                for row in android_saves:
                    _pc_conn.execute(
                        "DELETE FROM saves WHERE original_path = ?", (row["original_path"],)
                    )

    except Exception as exc:
        ctx._send_json({"error": str(exc)})
        return

    ctx._send_json(
        {
            "migrated_games": migrated,
            "errors": errors[:20],
            "pc_db": str(config.database_path),
            "android_db": str(config.database_path_android),
        }
    )


def _build_bootstrap_script(server_url: str) -> str:
    """Return the Termux bootstrap shell script with the server URL embedded."""
    return f"""\
#!/data/data/com.termux/files/usr/bin/bash
# Retro Vault — bootstrap para Termux en Anbernic
# Generado automáticamente por el servidor en {server_url}
set -e

SERVER="{server_url}"

echo ""
echo "=== Retro Vault — Configuración Anbernic ==="
echo ""

# 1. Instalar paquetes necesarios
echo "[1/4] Instalando paquetes (rclone, curl)..."
pkg update -y -o Dpkg::Options::="--force-confold" 2>/dev/null || pkg update -y
pkg install -y rclone curl

# 2. Permisos de almacenamiento
echo ""
echo "[2/4] Solicitando acceso al almacenamiento..."
echo "      (acepta el permiso en el diálogo de Android)"
termux-setup-storage
echo "      Esperando 3 segundos..."
sleep 3

# 3. Descargar config de rclone desde el PC
echo ""
echo "[3/4] Descargando configuración de rclone desde $SERVER..."
mkdir -p ~/.config/rclone
curl -sf "$SERVER/api/rclone-export-config" -o ~/.config/rclone/rclone.conf
if grep -q "\\[" ~/.config/rclone/rclone.conf 2>/dev/null; then
    echo "      rclone.conf instalado correctamente."
    rclone listremotes
else
    echo "      AVISO: el archivo descargado parece vacío o inválido."
    echo "      Revisa que el PC tiene rclone configurado (rclone config file)."
fi

# 4. Crear script de sync
echo ""
echo "[4/4] Creando ~/sync-saves.sh..."
cat > ~/sync-saves.sh << 'SCRIPT'
#!/data/data/com.termux/files/usr/bin/bash
LIBRARY="$HOME/storage/shared"
REMOTE="dropbox:/RetroSync/saves"
FILTERS=(
  --include "*.sav" --include "*.srm" --include "*.state"
  --include "*.state1" --include "*.state2" --include "*.sgm"
  --include "*.brm" --include "*.brmc" --include "*.nv"
  --include "*.hi" --include "*.fs" --include "*.ml1"
  --exclude "*"
)
echo "=== Sync saves Anbernic <-> Dropbox ==="
rclone bisync "$LIBRARY" "$REMOTE" "${{FILTERS[@]}}" --progress --log-level INFO "$@"
echo "=== Hecho ==="
SCRIPT
chmod +x ~/sync-saves.sh

echo ""
echo "=== Listo ==="
echo ""
echo "Para sincronizar saves:"
echo "  ~/sync-saves.sh"
echo ""
echo "Primera vez, añade --resync:"
echo "  ~/sync-saves.sh --resync"
echo ""
"""
