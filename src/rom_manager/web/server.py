from __future__ import annotations

import hashlib
import json
import logging
import secrets
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository
from rom_manager.planner import build_plan
from rom_manager.planner.operation_planner import FormatOptions
from rom_manager.reports import build_report, to_csv, to_json
from rom_manager.web.frontend import HTML
from rom_manager.web.response_builders import (
    _json_response, _test_path, _list_drives, _utc_now_str,
    _parse_format_opts, _repo_for_path,
    _build_junk_scan, _build_library_report, _build_status,
    _build_games, _count_companion_saves, _build_plan,
    _build_duplicates, _build_library_diff, _build_duplicates_two_repos,
    _build_folder_analysis, _build_ra_duplicates,
    _build_assets, _build_sync_log, _build_config,
    _build_scrape_summary, _build_cable_sync_preview,
)
from rom_manager.web.cable_sync_daemon import _auto_sync_loop, _sd_card_sync_loop
from rom_manager.web.inbox_pipeline import (
    _build_inbox_scan, _run_setup_pipeline, _run_inbox_pipeline, _watcher_now,
)

# ── Tray icon instance (set by serve() when --tray is passed) ─────────────────
_tray_instance = None  # type: ignore[assignment]

# ── Background job state ──────────────────────────────────────────────────────
_job_lock = threading.Lock()
_jobs: dict[str, bool] = {
    "scan": False, "match": False, "sync": False,
    "convert_chd": False, "convert_cso": False, "scrape": False,
    "extract_zip": False, "health_check": False,
    "ra_check": False, "cable_sync": False,
    "apply": False, "inbox": False, "setup": False,
    "backup_now": False,
}
_job_results: dict[str, dict] = {}


def _start_job(name: str, fn: "Callable[[], None]") -> dict:
    """Start a background job if not already running.

    Returns ``{"status": "started"}`` or ``{"status": "already_running"}``.
    *fn* is responsible for setting ``_job_results[name]`` and clearing
    ``_jobs[name]`` in its own finally block.
    """
    from typing import Callable  # noqa: F401
    with _job_lock:
        if _jobs[name]:
            return {"status": "already_running"}
        _jobs[name] = True
    threading.Thread(target=fn, daemon=True).start()
    return {"status": "started"}


# Canonical ES-DE platform folder names (platform detector name → ES folder)
_ES_PLATFORM_FOLDERS: dict[str, str] = {
    "NES":              "nes",
    "SNES":             "snes",
    "Nintendo 64":      "n64",
    "Game Boy":         "gb",
    "Game Boy Color":   "gbc",
    "Game Boy Advance": "gba",
    "Nintendo DS":      "nds",
    "Nintendo 3DS":     "3ds",
    "GameCube":         "gamecube",
    "Wii":              "wii",
    "Wii U":            "wiiu",
    "Nintendo Switch":  "switch",
    "Master System":    "mastersystem",
    "Game Gear":        "gamegear",
    "Sega Genesis":     "megadrive",
    "Sega Mega Drive":  "megadrive",
    "Dreamcast":        "dreamcast",
    "PlayStation":      "psx",
    "PlayStation 2":    "ps2",
    "PlayStation 3":    "ps3",
    "PSP":              "psp",
    "PS Vita":          "psvita",
    "Sega Saturn":      "saturn",
    "Saturn":           "saturn",      # alias legacy
    "Atari 2600":       "atari2600",
    "Atari 5200":       "atari5200",
    "Atari 7800":       "atari7800",
    "Atari Lynx":       "atarilynx",
    "Atari Jaguar":     "atarijaguar",
    "Neo Geo":          "neogeo",
    "PC Engine":        "pcengine",
    "Sega 32X":         "sega32x",
    "Sega CD":          "segacd",
    "Arcade":           "arcade",
}

_STANDARD_PLATFORM_FOLDERS: tuple[str, ...] = (
    # Nintendo
    "nes", "snes", "n64", "gb", "gbc", "gba", "nds", "3ds",
    "gamecube", "wii", "wiiu", "switch",
    # Sony
    "psx", "ps2", "ps3", "psp", "psvita",
    # Sega
    "megadrive", "mastersystem", "gamegear", "dreamcast", "saturn", "sega32x", "segacd",
    # Atari
    "atari2600", "atari5200", "atari7800", "atarilynx", "atarijaguar",
    # Otros
    "neogeo", "pcengine",
    # Arcade
    "arcade",
)

_chd_progress: dict = {}     # {"current": int, "total": int, "current_file": str}
_cso_progress: dict = {}     # {"current": int, "total": int, "current_file": str}
_scrape_progress: dict = {}  # {"current": int, "total": int, "found": int, "current_game": str}
_zip_progress: dict = {}     # {"current": int, "total": int, "current_file": str}
_health_progress: dict = {}  # {"current": int, "total": int, "current_file": str}
_ra_progress: dict = {}      # {"current": int, "total": int, "current_file": str}
_cable_progress: dict = {}   # {"copied": int, "total_files": int, "bytes_copied": int, "bytes_total": int, "speed_bps": float, "current_file": str}
_scan_progress: dict = {}    # {"files_seen": int, "roms_detected": int, "current_path": str}
_apply_progress: dict = {}   # {"current": int, "total": int, "current_file": str}
_inbox_progress: dict = {}    # {"step": str, "step_num": int, "total_steps": int, "current_file": str, "processed": int, "total": int}
_inbox_watcher_status: dict = {"watching": False, "last_check": None, "pending_files": 0}
_setup_progress: dict = {}   # {"step": str, "step_num": int, "total_steps": int, "current_file": str, "pct": int}
_scan_cancel:   threading.Event = threading.Event()
_cable_cancel:  threading.Event = threading.Event()
_chd_cancel:    threading.Event = threading.Event()
_cso_cancel:    threading.Event = threading.Event()
_zip_cancel:    threading.Event = threading.Event()
_health_cancel: threading.Event = threading.Event()
_ra_cancel:     threading.Event = threading.Event()
_scrape_cancel: threading.Event = threading.Event()
_match_cancel:  threading.Event = threading.Event()
_ss_last_quota: dict = {}   # last ScreenScraper quota snapshot from any scrape run

# ── S25: Session auth ─────────────────────────────────────────────────────────
_SESSION_COOKIE = "rvm_session"
_sessions: dict[str, float] = {}   # {token: expires_at (monotonic)}
_sessions_lock = threading.Lock()

def _get_local_ip() -> str:
    """Best-effort: return the machine's LAN IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def _hash_pin(pin: str, salt: str) -> str:
    return hashlib.sha256((pin + salt).encode()).hexdigest()

def _create_session(ttl: int) -> str:
    token = secrets.token_urlsafe(32)
    with _sessions_lock:
        _sessions[token] = time.monotonic() + ttl
    return token

def _destroy_session(token: str) -> None:
    with _sessions_lock:
        _sessions.pop(token, None)

def _validate_session(token: str) -> bool:
    with _sessions_lock:
        exp = _sessions.get(token)
        if exp is None:
            return False
        if time.monotonic() > exp:
            del _sessions[token]
            return False
        return True

_LOGIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Retro Vault — Acceso</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:#0f0f0f;color:#d4d4d4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{background:#1e1e2e;border:1px solid #2a2a3a;border-radius:12px;padding:40px 36px;width:320px;text-align:center}
h1{color:#4ec9b0;font-family:Consolas,monospace;font-size:22px;letter-spacing:2px;margin-bottom:8px}
p{color:#555;font-size:13px;margin-bottom:28px}
input[type=password]{width:100%;background:#0f0f0f;border:1px solid #444;color:#d4d4d4;padding:12px 16px;border-radius:6px;font:inherit;font-size:18px;text-align:center;letter-spacing:8px;margin-bottom:16px;outline:none}
input[type=password]:focus{border-color:#4ec9b0}
button{width:100%;background:#1e1e2e;border:1px solid #4ec9b0;color:#4ec9b0;padding:10px;border-radius:6px;cursor:pointer;font:inherit;font-size:14px;transition:background .15s,color .15s}
button:hover{background:#4ec9b0;color:#0f0f0f}
.err{color:#f44747;font-size:12px;margin-top:10px;min-height:18px}
</style>
</head>
<body>
<div class="box">
  <h1>RETRO VAULT</h1>
  <p>Introduce el PIN para acceder</p>
  <form id="f">
    <input type="password" id="pin" placeholder="••••" maxlength="10" autocomplete="off" autofocus>
    <button type="submit">Entrar</button>
    <div class="err" id="err"></div>
  </form>
</div>
<script>
document.getElementById('f').addEventListener('submit',async function(e){
  e.preventDefault();
  const pin=document.getElementById('pin').value;
  const r=await fetch('/api/auth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin})});
  const d=await r.json();
  if(d.ok){location.href='/';}
  else{const el=document.getElementById('err');el.textContent=d.error||'PIN incorrecto';document.getElementById('pin').select();}
});
</script>
</body>
</html>"""
_logger = logging.getLogger(__name__)

# ── Auto-sync daemon state ─────────────────────────────────────────────────────
_auto_sync_enabled: bool = True
_auto_sync_last_devices: set = set()   # serial numbers seen in last poll
_auto_sync_status: dict = {"state": "waiting", "last_sync_at": None, "last_device": None, "last_error": None}

# ── SD card daemon state ────────────────────────────────────────────────────────
_sd_sync_status: dict = {"state": "waiting", "last_sync_at": None, "drive": None}


def _handle_catalog_status(config: AppConfig) -> dict:
    """List DAT files in the nointro/redump/arcade catalog directories with quick entry counts."""
    def _scan_dir(directory: Path, is_arcade: bool = False) -> list[dict]:
        files: list[dict] = []
        if not directory.exists():
            return files
        for f in sorted(directory.iterdir()):
            if f.suffix.lower() not in (".dat", ".xml") or not f.is_file():
                continue
            try:
                data = f.read_bytes()
                if is_arcade and f.suffix.lower() == ".xml":
                    # MAME listxml uses <machine> tags
                    count = data.count(b"<machine ")
                else:
                    count = data.count(b"<game")
            except OSError:
                count = 0
            try:
                size = f.stat().st_size
            except OSError:
                size = 0
            files.append({"name": f.name, "size_bytes": size, "entries": count})
        return files

    nointro = _scan_dir(config.catalogs_nointro_dir)
    redump = _scan_dir(config.catalogs_redump_dir)
    arcade = _scan_dir(config.catalogs_arcade_dir, is_arcade=True)
    return {
        "nointro": nointro,
        "redump": redump,
        "arcade": arcade,
        "total_nointro_entries": sum(f["entries"] for f in nointro),
        "total_redump_entries": sum(f["entries"] for f in redump),
        "total_arcade_entries": sum(f["entries"] for f in arcade),
        "nointro_dir": str(config.catalogs_nointro_dir),
        "redump_dir": str(config.catalogs_redump_dir),
        "arcade_dir": str(config.catalogs_arcade_dir),
    }


def _build_missing_data(config: "AppConfig", repository) -> list[dict]:
    """Load all DAT files and compute missing ROMs vs. the library.

    Returns a list of dicts, one per DAT platform:
    {
        "platform": str,
        "total": int,
        "in_library": int,
        "missing": int,
        "coverage_pct": float,
        "entries": [{"sha1": str, "title": str}, ...]  — only the missing ones
    }
    """
    from rom_manager.catalog.catalog_loader import load_dat_files_by_platform

    platforms = load_dat_files_by_platform(
        config.catalogs_nointro_dir,
        config.catalogs_redump_dir,
    )
    if not platforms:
        return []

    library_sha1s = repository.get_all_rom_sha1s()

    results: list[dict] = []
    for platform_label, entries in platforms:
        missing_entries = [
            {"sha1": sha1, "title": entry.title}
            for sha1, entry in entries.items()
            if sha1 not in library_sha1s
        ]
        total = len(entries)
        missing = len(missing_entries)
        in_lib = total - missing
        results.append({
            "platform": platform_label,
            "total": total,
            "in_library": in_lib,
            "missing": missing,
            "coverage_pct": round(100.0 * in_lib / total, 1) if total > 0 else 0.0,
            "entries": missing_entries,
        })

    results.sort(key=lambda r: r["platform"])
    return results


def _handle_import_dats(data: dict, config: AppConfig) -> dict:
    """Copy DAT/XML files from source_folder to the appropriate catalog subdirectory."""
    import shutil

    source = Path(data.get("source_folder", "")).expanduser()
    if not source.exists() or not source.is_dir():
        return {"error": f"Carpeta no encontrada: {source}"}

    imported: list[dict] = []
    errors: list[dict] = []

    for f in sorted(source.iterdir()):
        if f.suffix.lower() not in (".dat", ".xml") or not f.is_file():
            continue
        try:
            with f.open("rb") as fh:
                sample = fh.read(2048)
            # Must look like a Logiqx DAT
            if b"<datafile" not in sample and b"<game" not in sample:
                continue
            # Heuristic: filename contains "redump" → Redump, else No-Intro
            fname_lower = f.name.lower()
            if "redump" in fname_lower:
                dest_dir = config.catalogs_redump_dir
                catalog_type = "redump"
            else:
                dest_dir = config.catalogs_nointro_dir
                catalog_type = "nointro"
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest_dir / f.name)
            imported.append({"name": f.name, "catalog": catalog_type})
        except Exception as exc:
            errors.append({"name": f.name, "error": str(exc)})

    return {"imported": imported, "errors": errors, "total": len(imported)}


def _handle_import_arcade_catalog(data: dict, config: AppConfig) -> dict:
    """Copy MAME XML or FBNeo DAT files to the arcade catalog directory.

    Accepts either a single file path or a folder path.
    When a folder is given, all .xml and .dat files inside are copied.
    """
    import shutil
    from rom_manager.catalog.mame_loader import load_mame_xml, load_fbneo_dat

    src = Path(data.get("path", "")).expanduser()
    if not src.exists():
        return {"error": f"Ruta no encontrada: {src}"}

    dest_dir = config.catalogs_arcade_dir
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Collect candidate files
    if src.is_dir():
        candidates = sorted(f for f in src.iterdir() if f.is_file() and f.suffix.lower() in (".dat", ".xml"))
    elif src.is_file():
        candidates = [src]
    else:
        return {"error": f"La ruta no es un archivo ni una carpeta: {src}"}

    if not candidates:
        return {"error": "No se encontraron archivos .xml o .dat en la ruta indicada."}

    imported: list[dict] = []
    errors: list[dict] = []

    for f in candidates:
        try:
            with f.open("rb") as fh:
                sample = fh.read(4096)
            if b"<mame" in sample or (b"<machine" in sample and b"<datafile" not in sample):
                fmt = "mame_xml"
                entries = load_mame_xml(f)
            elif b"<datafile" in sample or b"<game" in sample:
                fmt = "fbneo_dat"
                entries = load_fbneo_dat(f)
            else:
                errors.append({"name": f.name, "error": "Formato no reconocido"})
                continue

            if not entries:
                errors.append({"name": f.name, "error": "Sin entradas válidas"})
                continue

            shutil.copy2(f, dest_dir / f.name)
            imported.append({"name": f.name, "format": fmt, "entries": len(entries)})
        except Exception as exc:
            errors.append({"name": f.name, "error": str(exc)})

    if not imported:
        return {"error": "No se importó ningún archivo. " + (errors[0]["error"] if errors else "")}

    return {
        "ok": True,
        "imported": imported,
        "errors": errors,
        "total_files": len(imported),
        "total_entries": sum(x["entries"] for x in imported),
    }


def _handle_detect_cloud_folder() -> dict:
    """Detect locally-installed cloud clients (Dropbox, OneDrive, Google Drive)."""
    import json as _json
    import os as _os
    from pathlib import Path as _P

    detected: list[dict] = []

    # Dropbox — reads actual sync folder from client config
    try:
        info_path = _P(_os.environ.get("LOCALAPPDATA", "")) / "Dropbox" / "info.json"
        if info_path.exists():
            info = _json.loads(info_path.read_text(encoding="utf-8"))
            for key in ("personal", "business"):
                folder = (info.get(key) or {}).get("path", "")
                if folder and _P(folder).exists():
                    detected.append({
                        "service": "Dropbox",
                        "local_folder": folder,
                        "suggested_remote": folder.replace("\\", "/") + "/RetroVault/saves",
                    })
                    break
    except Exception:
        pass

    # OneDrive — env var set by the client
    for env_var in ("OneDriveConsumer", "OneDrive"):
        folder = _os.environ.get(env_var, "")
        if folder and _P(folder).exists():
            detected.append({
                "service": "OneDrive",
                "local_folder": folder,
                "suggested_remote": folder.replace("\\", "/") + "/RetroVault/saves",
            })
            break

    # Google Drive for Desktop — typical install path
    try:
        gdrive = _P(_os.environ.get("LOCALAPPDATA", "")) / "Google" / "Drive File Stream"
        if not gdrive.exists():
            gdrive = _P(_os.environ.get("USERPROFILE", "")) / "Google Drive"
        if gdrive.exists():
            detected.append({
                "service": "Google Drive",
                "local_folder": str(gdrive),
                "suggested_remote": str(gdrive).replace("\\", "/") + "/RetroVault/saves",
            })
    except Exception:
        pass

    return {"detected": detected}


def _handle_rclone_export_config(config: AppConfig) -> tuple[bytes, str]:
    """Return the local rclone config file contents as bytes, or an error message."""
    import subprocess as _sp, shutil as _sh
    # Locate config file via `rclone config file`
    rclone_bin = config.rclone_binary or "rclone"
    if not _sh.which(rclone_bin) and not __import__("pathlib").Path(rclone_bin).exists():
        return b"# rclone not found on this machine\n", "text/plain; charset=utf-8"
    try:
        r = _sp.run([rclone_bin, "config", "file"], capture_output=True, text=True, timeout=8)
        config_path = None
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if line and line != "Configuration file is stored at:":
                config_path = line
                break
        if config_path:
            from pathlib import Path as _P
            p = _P(config_path)
            if p.exists():
                return p.read_bytes(), "text/plain; charset=utf-8"
        return b"# rclone config file not found\n", "text/plain; charset=utf-8"
    except Exception as exc:
        return f"# error reading rclone config: {exc}\n".encode(), "text/plain; charset=utf-8"


def _build_anbernic_setup_sh(config: AppConfig) -> str:
    """Generate a personalised Android/Termux setup shell script."""
    ip = _get_local_ip()
    port = config.web_port
    base_url = f"http://{ip}:{port}"
    rclone_remote = config.rclone_remote or "dropbox:/RetroSync/saves"
    library_root = str(config.library_root or "/storage/emulated/0/RetroArch").replace("\\", "/")

    # Detect if we have a cloud folder configured too
    cloud_info = _handle_detect_cloud_folder()
    has_cloud = bool(cloud_info.get("detected"))
    cloud_folder = cloud_info["detected"][0]["local_folder"].replace("\\", "/") if has_cloud else ""
    cloud_service = cloud_info["detected"][0]["service"] if has_cloud else ""

    lines: list[str] = [
        "#!/data/data/com.termux/files/usr/bin/bash",
        "# ──────────────────────────────────────────────────────",
        "# Retro Vault — Script de auto-configuración para Android",
        f"# Generado por: {base_url}",
        "# ──────────────────────────────────────────────────────",
        "set -e",
        "",
        'echo "╔══════════════════════════════════════╗"',
        'echo "║   Retro Vault — Setup para Android   ║"',
        'echo "╚══════════════════════════════════════╝"',
        'echo ""',
        "",
        "RA_SAVES=/storage/emulated/0/RetroArch/saves",
        "RA_STATES=/storage/emulated/0/RetroArch/states",
        f"RETROVAULT_URL={base_url}",
        f"RCLONE_REMOTE=\"{rclone_remote}\"",
        "",
        "# ── Permisos de almacenamiento ────────────────────────",
        'echo "[1/5] Solicitando permisos de almacenamiento..."',
        "termux-setup-storage 2>/dev/null || true",
        'echo ""',
        "",
        "# ── Dependencias ─────────────────────────────────────",
        'echo "[2/5] Instalando dependencias (wget, openssh)..."',
        "pkg install -y wget openssh 2>/dev/null",
        "",
    ]

    # ── Option A: rclone ──────────────────────────────────────
    lines += [
        "# ══════════════════════════════════════════════════════",
        "# OPCIÓN A — Sync via rclone (requiere WiFi al PC)",
        "# ══════════════════════════════════════════════════════",
        'echo "[3a/5] Instalando rclone desde Termux..."',
        "pkg install -y rclone 2>/dev/null",
        "",
        f'echo "[4a/5] Descargando configuración rclone del PC ({base_url})..."',
        "mkdir -p ~/.config/rclone",
        f"wget -q -O ~/.config/rclone/rclone.conf \"{base_url}/api/rclone-export-config\" && \\",
        '  echo "  ✓ Config rclone descargada." || \\',
        '  echo "  ✗ No se pudo descargar la config rclone. Asegúrate de que el PC esté encendido y conectado a la misma red WiFi."',
        "",
        '# Crear script de sync',
        "SYNC_SCRIPT=~/retrovault-sync.sh",
        "cat > $SYNC_SCRIPT << 'SYNCEOF'",
        "#!/data/data/com.termux/files/usr/bin/bash",
        "# Retro Vault — Sync de saves",
        "SAVES=/storage/emulated/0/RetroArch/saves",
        "STATES=/storage/emulated/0/RetroArch/states",
        f'REMOTE="{rclone_remote}"',
        "# Subir saves al cloud",
        'echo "Subiendo saves..."',
        'rclone copy "$SAVES" "$REMOTE/saves" --update --transfers 4',
        'rclone copy "$STATES" "$REMOTE/states" --update --transfers 4',
        "# Bajar saves del cloud (sin sobreescribir más nuevos)",
        'echo "Bajando saves..."',
        'rclone copy "$REMOTE/saves" "$SAVES" --update --transfers 4',
        'rclone copy "$REMOTE/states" "$STATES" --update --transfers 4',
        'echo "✓ Sync completado."',
        "SYNCEOF",
        "chmod +x $SYNC_SCRIPT",
        'echo "  ✓ Script de sync creado en ~/retrovault-sync.sh"',
        "",
    ]

    if has_cloud:
        lines += [
            "# ══════════════════════════════════════════════════════",
            f"# OPCIÓN B — Sync via {cloud_service} (app Android)",
            "# ══════════════════════════════════════════════════════",
            f'echo "[3b/5] Buscando carpeta {cloud_service} en Android..."',
            "# Rutas típicas de los clientes Android de cloud",
            "CLOUD_PATHS=(",
            '  "/storage/emulated/0/Dropbox"',
            '  "/storage/emulated/0/OneDrive"',
            '  "/storage/emulated/0/Google Drive"',
            ")",
            "CLOUD_DIR=\"\"",
            "for p in \"${CLOUD_PATHS[@]}\"; do",
            "  if [ -d \"$p\" ]; then CLOUD_DIR=\"$p\"; break; fi",
            "done",
            "",
            "if [ -n \"$CLOUD_DIR\" ]; then",
            f'  echo "  ✓ {cloud_service} encontrado en $CLOUD_DIR"',
            "  CLOUD_SYNC_SCRIPT=~/retrovault-cloud-sync.sh",
            "  cat > $CLOUD_SYNC_SCRIPT << 'CLOUDSYNCEOF'",
            "#!/data/data/com.termux/files/usr/bin/bash",
            "# Retro Vault — Sync via carpeta cloud local",
            "SAVES=/storage/emulated/0/RetroArch/saves",
            "STATES=/storage/emulated/0/RetroArch/states",
            "CLOUD_DIR=\"\"",
            "for p in \"/storage/emulated/0/Dropbox\" \"/storage/emulated/0/OneDrive\" \"/storage/emulated/0/Google Drive\"; do",
            "  if [ -d \"$p\" ]; then CLOUD_DIR=\"$p\"; break; fi",
            "done",
            "if [ -z \"$CLOUD_DIR\" ]; then echo \"No se encontró carpeta cloud.\"; exit 1; fi",
            "DEST=\"$CLOUD_DIR/RetroVault\"",
            "mkdir -p \"$DEST/saves\" \"$DEST/states\"",
            "rsync -av --update \"$SAVES/\" \"$DEST/saves/\"",
            "rsync -av --update \"$STATES/\" \"$DEST/states/\"",
            "rsync -av --update \"$DEST/saves/\" \"$SAVES/\"",
            "rsync -av --update \"$DEST/states/\" \"$STATES/\"",
            'echo "✓ Sync cloud local completado."',
            "CLOUDSYNCEOF",
            "  chmod +x $CLOUD_SYNC_SCRIPT",
            '  echo "  ✓ Script cloud sync creado en ~/retrovault-cloud-sync.sh"',
            "else",
            f'  echo "  ✗ No se encontró carpeta {cloud_service} en el dispositivo."',
            f'  echo "    Instala la app {cloud_service} en Android y asegúrate de que haya sincronizado al menos una vez."',
            "fi",
            "",
        ]

    # ── Termux:Boot ──────────────────────────────────────────
    lines += [
        "# ══════════════════════════════════════════════════════",
        "# Auto-arranque con Termux:Boot",
        "# ══════════════════════════════════════════════════════",
        'echo "[5/5] Configurando auto-sync al arrancar..."',
        "BOOT_DIR=~/.termux/boot",
        "mkdir -p $BOOT_DIR",
        "cat > $BOOT_DIR/retrovault-sync.sh << 'BOOTEOF'",
        "#!/data/data/com.termux/files/usr/bin/bash",
        "sleep 30  # Esperar a que el sistema cargue",
        "~/retrovault-sync.sh >> ~/retrovault-sync.log 2>&1",
        "BOOTEOF",
        "chmod +x $BOOT_DIR/retrovault-sync.sh",
        'echo "  ✓ Auto-sync configurado (Termux:Boot)"',
        "",
        'echo ""',
        'echo "╔══════════════════════════════════════════════════╗"',
        'echo "║  ✓ Configuración completada                      ║"',
        'echo "║                                                  ║"',
        'echo "║  Ejecuta ~/retrovault-sync.sh para sincronizar   ║"',
        'echo "║  El sync se ejecutará automáticamente al arrancar ║"',
        'echo "║  (requiere Termux:Boot desde F-Droid)            ║"',
        'echo "╚══════════════════════════════════════════════════╝"',
        "",
    ]

    return "\n".join(lines) + "\n"


def _handle_system_status(config: AppConfig) -> dict:
    """Aggregate status of all external tools and data dependencies."""
    import subprocess as _sp
    from pathlib import Path as _P

    def _test_binary(path_str: str, flag: str = "--version") -> tuple[bool, str]:
        p = _P(path_str) if path_str else None
        if not p or not p.exists():
            # Try in PATH
            import shutil
            found = shutil.which(path_str or "")
            if not found:
                return False, ""
            p = _P(found)
        try:
            r = _sp.run([str(p), flag], capture_output=True, text=True, timeout=5)
            ver = (r.stdout or r.stderr or "").strip().splitlines()[0][:60]
            return True, ver
        except Exception:
            return True, ""  # exists but failed to run version

    chdman_ok, chdman_ver = _test_binary(str(config.chdman) if config.chdman else "")
    adb_ok, adb_ver = _test_binary(str(config.adb) if config.adb else "")
    rclone_st = _handle_rclone_status(config)
    cats = _handle_catalog_status(config)
    cat_total = len(cats.get("nointro", [])) + len(cats.get("redump", [])) + len(cats.get("arcade", []))

    return {
        "chdman":   {"ok": chdman_ok, "version": chdman_ver, "path": str(config.chdman or "tools/chdman.exe")},
        "adb":      {"ok": adb_ok,    "version": adb_ver,    "path": str(config.adb or "tools/adb.exe")},
        "rclone":   {"ok": rclone_st["installed"], "version": rclone_st.get("version", ""), "remotes": rclone_st.get("remotes", [])},
        "ra_key":   {"ok": bool(config.ra_api_key)},
        "catalogs": {"ok": cat_total > 0, "total": cat_total,
                     "nointro": len(cats.get("nointro", [])), "redump": len(cats.get("redump", []))},
        "library":  {"ok": bool(config.library_root), "path": str(config.library_root or "")},
    }


def _handle_rclone_status(config: AppConfig) -> dict:
    """Check if rclone is installed and list configured remotes."""
    import subprocess

    installed = False
    version = ""
    remotes: list[str] = []

    try:
        proc = subprocess.run(
            [config.rclone_binary, "version"],
            capture_output=True, text=True, timeout=8,
        )
        installed = proc.returncode == 0
        if installed:
            version = proc.stdout.split("\n")[0].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    if installed:
        try:
            rem_proc = subprocess.run(
                [config.rclone_binary, "listremotes"],
                capture_output=True, text=True, timeout=8,
            )
            remotes = [r.strip() for r in rem_proc.stdout.strip().split("\n") if r.strip()]
        except Exception:
            pass

    return {
        "installed": installed,
        "version": version,
        "remotes": remotes,
        "binary": config.rclone_binary,
    }


def _handle_library_doctor(config: "AppConfig", repository: "LibraryRepository") -> dict:
    """Scan library_root for common issues: misplaced ROMs, incomplete CUE sets, empty dirs."""
    import re as _re
    if not config.library_root:
        return {"error": "library_root no configurado"}
    root = Path(config.library_root)
    issues: list[dict] = []

    # (a) Misplaced ROMs — games not in their expected platform subfolder
    try:
        with repository.connect() as _conn:
            _rows = _conn.execute(
                "SELECT source_path, platform, original_filename FROM games "
                "WHERE file_type='rom' AND platform IS NOT NULL AND source_path IS NOT NULL"
            ).fetchall()
        for _row in _rows:
            _sp, _plat, _fname = _row[0], _row[1], _row[2]
            _expected_slug = _ES_PLATFORM_FOLDERS.get(_plat, "")
            if not _expected_slug:
                continue
            _expected_dir = str(root / _expected_slug)
            if not _sp.startswith(_expected_dir):
                issues.append({
                    "type": "misplaced_rom",
                    "severity": "warning",
                    "file": _fname,
                    "path": _sp,
                    "platform": _plat,
                    "expected_dir": _expected_dir,
                    "action": f"Mover a {_expected_slug}/",
                })
    except Exception:
        pass

    # (b) Incomplete CUE sets — .cue file references .bin files that don't exist
    _cue_bin_re = _re.compile(r'^\s*FILE\s+"?([^"]+)"?\s+BINARY', _re.IGNORECASE | _re.MULTILINE)
    for _cue in root.rglob("*.cue"):
        try:
            _text = _cue.read_text(encoding="utf-8", errors="replace")
            _refs = _cue_bin_re.findall(_text)
            _missing = [r for r in _refs if not (_cue.parent / r).exists()]
            if _missing:
                issues.append({
                    "type": "incomplete_cue",
                    "severity": "error",
                    "file": _cue.name,
                    "path": str(_cue),
                    "platform": None,
                    "missing_bins": _missing[:5],
                    "action": f"Faltan {len(_missing)} .bin — set incompleto",
                })
        except Exception:
            pass

    # (c) Empty platform directories
    for _d in root.iterdir():
        if _d.is_dir() and _d.name not in ("saves", "bios", "inbox", "states", "screenshots", "_descartados"):
            try:
                _files = [f for f in _d.rglob("*") if f.is_file()]
                if not _files:
                    issues.append({
                        "type": "empty_dir",
                        "severity": "info",
                        "file": _d.name,
                        "path": str(_d),
                        "platform": None,
                        "action": "Carpeta vacía — puedes eliminarla",
                    })
            except Exception:
                pass

    # Group by type for summary
    by_type: dict[str, int] = {}
    for iss in issues:
        by_type[iss["type"]] = by_type.get(iss["type"], 0) + 1

    return {
        "issues": issues[:200],
        "total": len(issues),
        "by_type": by_type,
    }


def _handle_copy_assets_to_esde(config: "AppConfig") -> dict:
    """Copy scraped box art from library_root/{platform}/media/images/ to ES-DE gamelists dir."""
    import os as _os
    import shutil as _shutil
    esde = _handle_esde_status(config)
    if not esde.get("gamelists_dir"):
        return {"error": "ES-DE no detectado"}
    if not config.library_root:
        return {"error": "library_root no configurado"}
    gamelists_dir = Path(esde["gamelists_dir"])
    root = Path(config.library_root)
    copied = 0
    skipped = 0
    errors: list[str] = []
    for platform_dir in root.iterdir():
        if not platform_dir.is_dir():
            continue
        img_src = platform_dir / "media" / "images"
        if not img_src.exists():
            continue
        img_dst = gamelists_dir / platform_dir.name / "images"
        img_dst.mkdir(parents=True, exist_ok=True)
        for img in img_src.iterdir():
            if img.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                dst = img_dst / img.name
                try:
                    _shutil.copy2(str(img), str(dst))
                    copied += 1
                except Exception as exc:
                    errors.append(str(exc))
                    skipped += 1
    return {"copied": copied, "skipped": skipped, "errors": errors[:5]}


def _handle_esde_status(config: AppConfig) -> dict:
    """Detect ES-DE installation and return status + suggested gamelist paths."""
    import os
    appdata = os.environ.get("APPDATA", "")
    localappdata = os.environ.get("LOCALAPPDATA", "")
    home = os.environ.get("USERPROFILE", os.path.expanduser("~"))

    candidates: list[Path] = []
    if appdata:
        candidates.append(Path(appdata) / "ES-DE")
    if localappdata:
        candidates.append(Path(localappdata) / "ES-DE")
    candidates += [
        Path(home) / ".emulationstation",
        Path(home) / "ES-DE",
    ]
    for drive in ("C", "D"):
        candidates += [
            Path(f"{drive}:\\Program Files\\ES-DE"),
            Path(f"{drive}:\\ES-DE"),
        ]

    found_dir: str = ""
    roms_path: str = ""
    for c in candidates:
        if c.exists():
            found_dir = str(c)
            # Look for es_settings.xml to extract ROMsDirectory
            settings = c / "settings" / "es_settings.xml"
            if not settings.exists():
                settings = c / "es_settings.xml"
            if settings.exists():
                try:
                    text = settings.read_text(encoding="utf-8", errors="replace")
                    import re as _re
                    m = _re.search(r'name="ROMsDirectory"[^>]*value="([^"]+)"', text)
                    if m:
                        roms_path = m.group(1)
                except OSError:
                    pass
            break

    gamelists_dir = str(Path(found_dir) / "gamelists") if found_dir else ""
    return {
        "installed": bool(found_dir),
        "install_dir": found_dir,
        "roms_path": roms_path,
        "gamelists_dir": gamelists_dir,
    }


def _handle_retroarch_check(config: AppConfig) -> dict:
    """B6-1/B6-6: Diagnostic check for RetroArch configuration and ES-DE integration."""
    import re

    result: dict = {
        "exe_configured": False,
        "exe_exists": False,
        "exe_path": "",
        "cfg_exists": False,
        "cores_dir_exists": False,
        "cores_count": 0,
        "key_cores": {},
        "savefile_dir": "",
        "savestate_dir": "",
        "esde_ra_path": "",
        "esde_ra_match": None,
        "issues": [],
        "ok": False,
    }

    # 1. Check configured exe
    ra_exe = (config.retroarch_path or "").strip()
    result["exe_path"] = ra_exe
    result["exe_configured"] = bool(ra_exe)
    if not ra_exe:
        result["issues"].append("RetroArch no está configurado en Settings (launchers.retroarch).")
        return result

    ra_path = Path(ra_exe)
    result["exe_exists"] = ra_path.exists()
    if not ra_path.exists():
        result["issues"].append(f"Ejecutable no encontrado: {ra_exe}")

    # 2. retroarch.cfg in same directory
    ra_dir = ra_path.parent if ra_path.exists() else ra_path.parent
    cfg = ra_dir / "retroarch.cfg"
    result["cfg_exists"] = cfg.exists()
    if not cfg.exists():
        result["issues"].append(f"retroarch.cfg no encontrado en {ra_dir}")

    # 3. Read retroarch.cfg for save dirs
    if cfg.exists():
        try:
            text = cfg.read_text(encoding="utf-8", errors="replace")
            for key, field in (("savefile_directory", "savefile_dir"), ("savestate_directory", "savestate_dir")):
                m = re.search(rf'^{key}\s*=\s*"(.+)"', text, re.MULTILINE)
                if m:
                    val = m.group(1).strip()
                    if val not in ("", "default"):
                        result[field] = val
        except OSError:
            pass

    # 4. Cores directory
    cores_dir = ra_dir / "cores"
    result["cores_dir_exists"] = cores_dir.exists()
    if cores_dir.exists():
        dlls = list(cores_dir.glob("*_libretro.dll"))
        result["cores_count"] = len(dlls)
        if len(dlls) == 0:
            result["issues"].append("Carpeta cores/ existe pero no contiene cores (_libretro.dll).")
        # Check key cores
        key_map = {
            "mgba": "GBA",
            "snes9x": "SNES",
            "genesis_plus_gx": "Mega Drive",
            "pcsx_rearmed": "PSX",
            "duckstation": "PSX (DuckStation)",
            "flycast": "Dreamcast",
            "mupen64plus_next": "N64",
            "mame": "MAME/Arcade",
        }
        for core_prefix, label in key_map.items():
            found = any(d.name.startswith(core_prefix) for d in dlls)
            result["key_cores"][label] = found
    else:
        result["issues"].append(f"Carpeta cores/ no encontrada en {ra_dir}")

    # 5. ES-DE configured emulator path (check es_settings.xml for RetroArch path)
    esde_info = _handle_esde_status(config)
    if esde_info.get("installed") and esde_info.get("install_dir"):
        esde_cfg = Path(esde_info["install_dir"]) / "es_systems.xml"
        settings_xml = Path(esde_info["install_dir"]) / "es_settings.xml"
        # Look for RetroArch path in es_settings.xml (EmulatorPath or similar)
        for xml_path in (settings_xml, esde_cfg):
            if xml_path.exists():
                try:
                    text = xml_path.read_text(encoding="utf-8", errors="replace")
                    m = re.search(r'retroarch[^"<\n]*\.exe', text, re.IGNORECASE)
                    if m:
                        result["esde_ra_path"] = m.group(0)
                        break
                except OSError:
                    pass

    if result["esde_ra_path"] and ra_exe:
        # Normalize for comparison
        a = Path(result["esde_ra_path"]).resolve() if Path(result["esde_ra_path"]).exists() else None
        b = ra_path.resolve() if ra_path.exists() else None
        result["esde_ra_match"] = (str(a).lower() == str(b).lower()) if (a and b) else None

    result["ok"] = result["exe_exists"] and result["cfg_exists"] and result["cores_dir_exists"] and len(result["issues"]) == 0
    return result


def _handle_wizard_detect(config: AppConfig) -> dict:
    """Auto-detect RetroArch installation and connected ADB devices for the first-run wizard."""
    import os
    import re

    # --- 1. Scan common RetroArch installation paths ---
    candidates: list[Path] = []
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        candidates.append(Path(appdata) / "RetroArch")
    for drive_letter in ("C", "D", "E"):
        candidates += [
            Path(f"{drive_letter}:\\RetroArch-Win64"),
            Path(f"{drive_letter}:\\RetroArch"),
            Path(f"{drive_letter}:\\Program Files\\RetroArch"),
            Path(f"{drive_letter}:\\Program Files (x86)\\RetroArch"),
        ]

    library_root_suggestion = None
    for ra_dir in candidates:
        cfg_path = ra_dir / "retroarch.cfg"
        if not cfg_path.exists():
            continue
        try:
            text = cfg_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = re.search(r'^content_directory\s*=\s*"(.+)"', text, re.MULTILINE)
        if m:
            candidate = m.group(1).strip()
            if candidate not in ("", "default"):
                library_root_suggestion = candidate
                break
        # Fallback: use the RetroArch dir itself as a hint
        if library_root_suggestion is None:
            library_root_suggestion = str(ra_dir)

    # --- 2. Check ADB for connected devices ---
    android_suggestion = None
    device_display = None
    adb_ok = False
    try:
        from rom_manager.sync.adb_transport import list_devices
        devs = list_devices(config.adb)
        adb_ok = True
        ready_devs = [d for d in devs if d.ready]
        if ready_devs:
            dev = ready_devs[0]
            device_display = dev.display or dev.serial
            # Use config android path if set, else a sensible default
            android_suggestion = config.anbernic_root or "/storage/emulated/0/RetroArch/roms"
    except Exception:
        pass

    return {
        "library_root_suggestion": library_root_suggestion,
        "android_suggestion": android_suggestion,
        "device_display": device_display,
        "adb_ok": adb_ok,
    }


def make_handler(repository: LibraryRepository, config: AppConfig, repository_android: LibraryRepository | None = None):
    logger = logging.getLogger(__name__)
    # If no android repo is provided (e.g. called from CLI), use a no-op fallback = same as PC repo
    _repo_android: LibraryRepository = repository_android if repository_android is not None else repository

    def _get_repo(path_str: str) -> LibraryRepository:
        return _repo_for_path(path_str, repository, _repo_android, config)

    def _start_ra_check_bg(api_key: str) -> bool:
        """Start RA check in background. Returns True if started, False if already running."""
        with _job_lock:
            if _jobs.get("ra_check"):
                return False
            _jobs["ra_check"] = True

        def _run() -> None:
            _ra_cancel.clear()
            try:
                from rom_manager.retroachievements.ra_checker import check_library, to_csv

                cache_dir = config.data_dir / "ra_cache"

                def _prog(current: int, total: int, filename: str) -> None:
                    _ra_progress.update({"current": current, "total": total, "current_file": filename})
                    if _ra_cancel.is_set():
                        raise InterruptedError("RA check cancelled")

                try:
                    summary = check_library(repository, api_key, cache_dir=cache_dir, progress_cb=_prog)
                except InterruptedError:
                    _job_results["ra_check"] = {
                        "cancelled": True, "total": 0, "supported": 0,
                        "no_support_alternative": 0, "no_support": 0,
                        "no_md5": 0, "platform_unknown": 0,
                        "alternatives_csv": "", "alternatives": [],
                    }
                    return
                alternatives_csv = to_csv(summary) if summary.no_support_alternative > 0 else ""
                _job_results["ra_check"] = {
                    "total": summary.total,
                    "supported": summary.supported,
                    "no_support_alternative": summary.no_support_alternative,
                    "no_support": summary.no_support,
                    "no_md5": summary.no_md5,
                    "platform_unknown": summary.platform_unknown,
                    "cancelled": _ra_cancel.is_set(),
                    "alternatives_csv": alternatives_csv,
                    "alternatives": [
                        {
                            "platform": r.platform,
                            "filename": r.original_filename,
                            "our_md5": r.our_md5[:12],
                            "ra_id": r.alternative.id,
                            "ra_title": r.alternative.title,
                            "ra_achievements": r.alternative.achievements,
                            "ra_points": r.alternative.points,
                        }
                        for r in summary.results
                        if r.status == "no_support_alternative" and r.alternative
                    ],
                    "no_support_entries": [
                        {"source_path": r.source_path, "filename": r.original_filename, "platform": r.platform}
                        for r in summary.results
                        if r.status == "no_support"
                    ],
                }
            except Exception as exc:
                _job_results["ra_check"] = {"error": str(exc)}
            finally:
                with _job_lock:
                    _ra_progress.clear()
                    _jobs["ra_check"] = False

        threading.Thread(target=_run, daemon=True).start()
        return True

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass  # suppress default request logging

        # ── S25: Auth helpers ─────────────────────────────────────────────────

        def _auth_required(self) -> bool:
            """True when PIN protection is active (pin_hash is set in config)."""
            return bool(config.web_pin_hash)

        def _session_token(self) -> str | None:
            raw = self.headers.get("Cookie", "")
            if not raw:
                return None
            c = SimpleCookie()
            c.load(raw)
            morsel = c.get(_SESSION_COOKIE)
            return morsel.value if morsel else None

        def _is_authenticated(self) -> bool:
            if not self._auth_required():
                return True
            token = self._session_token()
            return bool(token and _validate_session(token))

        def _redirect_to_login(self) -> None:
            self._send(302, "text/plain", b"", extra_headers={"Location": "/login"})

        def _set_session_header(self, token: str) -> dict[str, str]:
            cookie = f"{_SESSION_COOKIE}={token}; HttpOnly; SameSite=Strict; Path=/"
            return {"Set-Cookie": cookie}

        # ── GET ──────────────────────────────────────────────────────────────

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)

            try:
                # S25: serve login page and static assets without auth
                if path == "/login":
                    self._send(200, "text/html; charset=utf-8", _LOGIN_HTML.encode())
                    return
                if path.startswith("/static/") or path == "/favicon.ico":
                    pass  # fall through to normal handling (no auth on static)
                elif not self._is_authenticated():
                    self._redirect_to_login()
                    return

                if path == "/":
                    self._send(200, "text/html; charset=utf-8", HTML.encode())
                elif path.startswith("/static/"):
                    filename = path[len("/static/"):]
                    # Security: only allow simple filenames, no path traversal
                    if "/" in filename or "\\" in filename or not filename:
                        self._send(404, "text/plain", b"Not found")
                    else:
                        import sys as _sys
                        if getattr(_sys, "frozen", False) and hasattr(_sys, "_MEIPASS"):
                            static_dir = Path(_sys._MEIPASS) / "rom_manager" / "web" / "static"
                        else:
                            static_dir = Path(__file__).parent / "static"
                        file_path = static_dir / filename
                        if not file_path.exists() or not file_path.is_file():
                            self._send(404, "text/plain", b"Not found")
                        else:
                            ext = file_path.suffix.lower()
                            content_type = {
                                ".css": "text/css; charset=utf-8",
                                ".js":  "application/javascript; charset=utf-8",
                            }.get(ext, "application/octet-stream")
                            self._send(200, content_type, file_path.read_bytes())
                elif path == "/api/status":
                    src_root = qs.get("root", [None])[0] or None
                    self._send_json(_build_status(repository, src_root, project_root=config.project_root, repository_android=_repo_android, library_root=config.library_root))
                elif path == "/api/test-path":
                    self._send_json(_test_path(qs.get("path", [""])[0]))
                elif path == "/api/list-drives":
                    self._send_json(_list_drives())
                elif path == "/api/adb-devices":
                    try:
                        from rom_manager.sync.adb_transport import list_devices
                        devs = list_devices(config.adb)
                        self._send_json({
                            "devices": [
                                {"serial": d.serial, "state": d.state,
                                 "model": d.model, "product": d.product,
                                 "ready": d.ready, "display": d.display}
                                for d in devs
                            ],
                            "adb_path": config.adb,
                        })
                    except RuntimeError as exc:
                        self._send_json({"error": str(exc), "devices": []})
                elif path == "/api/test-adb-path":
                    serial  = qs.get("serial", [""])[0]
                    ap      = qs.get("path", ["/storage/emulated/0"])[0]
                    if not serial:
                        self._send_json({"accessible": False, "error": "serial requerido"})
                    else:
                        try:
                            from rom_manager.sync.adb_transport import AdbTransport
                            t = AdbTransport(config.adb, serial)
                            self._send_json(t.test_path(ap))
                        except Exception as exc:
                            self._send_json({"accessible": False, "error": str(exc)})
                elif path == "/api/library-report":
                    rpt_path = qs.get("path", [None])[0] or str(config.library_root or "")
                    if not rpt_path:
                        self._send_json({"error": "path parameter required (or set library_root in config)"})
                    else:
                        _rpt_repo = _get_repo(rpt_path)
                        rpt = _build_library_report(rpt_path, _rpt_repo, config)
                        rpt["retroachievements"] = _job_results.get("ra_check") or {"note": "Ejecuta primero la comprobación de RetroAchievements en la pestaña Tools"}
                        rpt["chd"] = _job_results.get("convert_chd") or {"note": "Ejecuta primero la conversión CHD en la pestaña Tools"}
                        self._send_json(rpt)
                elif path == "/api/setup-status":
                    with _job_lock:
                        self._send_json({
                            "setup_running": _jobs["setup"],
                            "setup_progress": dict(_setup_progress) if _setup_progress else None,
                            "setup_result": _job_results.get("setup"),
                        })
                elif path == "/api/ra-duplicates":
                    self._send_json(_build_ra_duplicates(repository, config))
                elif path == "/api/report/html":
                    rpt_path = qs.get("path", [None])[0] or str(config.library_root or "")
                    if not rpt_path:
                        self._send(400, "text/plain; charset=utf-8",
                                   b"path parameter required (or set library_root in config)")
                    else:
                        from rom_manager.utils.library_report_html import generate_html_report
                        _rpt_repo = _get_repo(rpt_path)
                        rpt = _build_library_report(rpt_path, _rpt_repo, config)
                        rpt["retroachievements"] = _job_results.get("ra_check") or {}
                        rpt["chd"] = _job_results.get("convert_chd") or {}
                        html = generate_html_report(rpt)
                        self._send(200, "text/html; charset=utf-8", html.encode("utf-8"))
                elif path == "/api/games":
                    qs = parse_qs(parsed.query)
                    offset = int(qs.get("offset", ["0"])[0])
                    limit = min(int(qs.get("limit", ["100"])[0]), 500)
                    plat = qs.get("platform", [None])[0] or None
                    st = qs.get("status", [None])[0] or None
                    root = qs.get("root", [None])[0] or None
                    ft = qs.get("filetype", ["rom"])[0]
                    file_type = ft if ft in ("rom", "", "save") else None
                    search = qs.get("search", [None])[0] or None
                    play_status = qs.get("play_status", [None])[0] or None
                    favorite = qs.get("favorite", ["0"])[0] == "1"
                    tag_filter = qs.get("tag", [None])[0] or None
                    genre_filter = qs.get("genre", [None])[0] or None
                    year_filter = qs.get("year", [None])[0] or None
                    region_filter = qs.get("region", [None])[0] or None
                    sort_by = qs.get("sort_by", [None])[0] or None
                    _games_repo = _get_repo(root or "")
                    self._send_json(_build_games(_games_repo, offset=offset, limit=limit, platform=plat, status=st, source_root=root, file_type=file_type, search=search, play_status=play_status, favorite=favorite, tag=tag_filter, genre=genre_filter, year=year_filter, region=region_filter, sort_by=sort_by))
                elif path == "/api/games/filter-options":
                    self._send_json(repository.get_filter_options())
                elif path == "/api/tags":
                    self._send_json({"tags": repository.get_all_tags()})
                elif path == "/api/game-tags":
                    game_id = qs.get("id", [None])[0]
                    if not game_id:
                        self._send_json({"error": "id required"})
                    else:
                        self._send_json({"tags": repository.get_tags(int(game_id))})
                elif path == "/api/stateshot":
                    game_id = qs.get("id", [None])[0]
                    if not game_id:
                        self._send_json({"error": "id required"})
                    else:
                        with repository.connect() as conn:
                            row = conn.execute(
                                "SELECT source_path FROM games WHERE id = ?", (int(game_id),)
                            ).fetchone()
                        if not row:
                            self._send_json({"found": False})
                        else:
                            rom_path = Path(row["source_path"])
                            # RetroArch saves state screenshots as <rom_stem>.state0.png or <rom_stem>.state.png
                            candidates = list(rom_path.parent.glob(rom_path.stem + ".state*.png"))
                            if not candidates:
                                # Try RetroArch saves dir from config
                                if config.library_root:
                                    candidates = list(Path(config.library_root).rglob(rom_path.stem + ".state*.png"))
                            if candidates:
                                png = sorted(candidates)[-1]  # most recent alphabetically
                                import base64
                                img_b64 = base64.b64encode(png.read_bytes()).decode()
                                self._send_json({"found": True, "data": img_b64, "filename": png.name})
                            else:
                                self._send_json({"found": False})
                elif path == "/api/save-backups":
                    # List versioned backups for a game's save files
                    game_id = qs.get("id", [None])[0]
                    if not game_id:
                        self._send_json({"error": "id required"})
                    else:
                        from rom_manager.backup.save_backup import list_backups
                        with repository.connect() as conn:
                            row = conn.execute(
                                "SELECT source_path FROM games WHERE id = ?", (int(game_id),)
                            ).fetchone()
                        if not row:
                            self._send_json({"backups": []})
                        else:
                            rom_path = Path(row["source_path"])
                            # Collect backups for all save extensions found alongside the ROM
                            all_entries = []
                            for ext in config.save_extensions:
                                save_path = rom_path.parent / (rom_path.stem + ext)
                                entries = list_backups(save_path, config.data_dir)
                                for e in entries:
                                    all_entries.append({
                                        "backup_path": str(e.backup_path),
                                        "timestamp": e.timestamp,
                                        "extension": e.extension,
                                        "size": e.size,
                                        "original_save": str(save_path),
                                    })
                            all_entries.sort(key=lambda x: x["timestamp"], reverse=True)
                            self._send_json({
                                "backups": all_entries,
                                "backup_enabled": config.backup_saves_enabled,
                                "keep_n": config.backup_saves_keep_n,
                            })
                elif path == "/api/manual-backups":
                    from rom_manager.backup.save_backup import list_manual_zips
                    self._send_json({"zips": list_manual_zips(config.data_dir)})
                elif path == "/api/plan":
                    opts = _parse_format_opts(qs)
                    source_root = qs.get("source_root", [None])[0] or None
                    _plan_repo = _get_repo(source_root or "")
                    self._send_json(_build_plan(_plan_repo, opts, frozenset(config.save_extensions), source_root=source_root, library_root=str(config.library_root) if config.library_root else None))
                elif path == "/api/library-diff":
                    self._send_json(_build_library_diff(repository, _repo_android, config))
                elif path == "/api/duplicates":
                    source_root = qs.get("source_root", [None])[0] or None
                    pc_root     = qs.get("pc_root",     [None])[0] or None
                    ab_root     = qs.get("ab_root",     [None])[0] or None
                    self._send_json(_build_duplicates_two_repos(repository, _repo_android, config, source_root=source_root, pc_root=pc_root, ab_root=ab_root))
                elif path == "/api/assets":
                    src_root = qs.get("root", [None])[0] or None
                    _assets_repo = _get_repo(src_root or "")
                    self._send_json(_build_assets(_assets_repo, src_root))
                elif path == "/api/sync-log":
                    self._send_json(_build_sync_log(repository))
                elif path == "/api/config":
                    self._send_json(_build_config(config))
                elif path == "/api/scrape-summary":
                    self._send_json(_build_scrape_summary(repository))
                elif path == "/api/job-status":
                    with _job_lock:
                        self._send_json({
                            "scan_running": _jobs["scan"],
                            "match_running": _jobs["match"],
                            "sync_running": _jobs["sync"],
                            "convert_chd_running": _jobs["convert_chd"],
                            "convert_cso_running": _jobs["convert_cso"],
                            "scrape_running": _jobs["scrape"],
                            "scan_result": _job_results.get("scan"),
                            "match_result": _job_results.get("match"),
                            "sync_result": _job_results.get("sync"),
                            "convert_chd_result": _job_results.get("convert_chd"),
                            "convert_cso_result": _job_results.get("convert_cso"),
                            "scrape_result": _job_results.get("scrape"),
                            "chd_progress": dict(_chd_progress) if _chd_progress else None,
                            "cso_progress": dict(_cso_progress) if _cso_progress else None,
                            "scrape_progress": dict(_scrape_progress) if _scrape_progress else None,
                            "extract_zip_running": _jobs["extract_zip"],
                            "zip_progress": dict(_zip_progress) if _zip_progress else None,
                            "health_check_running": _jobs["health_check"],
                            "health_progress": dict(_health_progress) if _health_progress else None,
                            "health_check_result": _job_results.get("health_check"),
                            "extract_zip_result": _job_results.get("extract_zip"),
                            "ra_check_running": _jobs["ra_check"],
                            "ra_progress": dict(_ra_progress) if _ra_progress else None,
                            "ra_check_result": _job_results.get("ra_check"),
                            "cable_sync_running": _jobs["cable_sync"],
                            "cable_progress": dict(_cable_progress) if _cable_progress else None,
                            "cable_sync_result": _job_results.get("cable_sync"),
                            "scan_progress": dict(_scan_progress) if _scan_progress else None,
                            "apply_running": _jobs["apply"],
                            "apply_progress": dict(_apply_progress) if _apply_progress else None,
                            "apply_result": _job_results.get("apply"),
                            "inbox_running": _jobs["inbox"],
                            "inbox_progress": dict(_inbox_progress) if _inbox_progress else None,
                            "inbox_result": _job_results.get("inbox"),
                            "setup_running": _jobs["setup"],
                            "setup_progress": dict(_setup_progress) if _setup_progress else None,
                            "setup_result": _job_results.get("setup"),
                            "backup_now_running": _jobs.get("backup_now", False),
                            "backup_now_result": _job_results.get("backup_now"),
                            "inbox_pending_files": _inbox_watcher_status.get("pending_files", 0),
                        })
                elif path == "/api/test-chdman":
                    import subprocess
                    try:
                        r = subprocess.run(
                            [config.chdman],
                            capture_output=True, timeout=5,
                        )
                        # chdman exits with non-zero when called with no args but prints version
                        out = (r.stdout or r.stderr or b"").decode(errors="replace").strip()
                        first_line = out.splitlines()[0] if out else ""
                        self._send_json({"ok": True, "version": first_line, "path": config.chdman})
                    except FileNotFoundError:
                        self._send_json({"ok": False, "error": f"No encontrado: {config.chdman!r}"})
                    except Exception as exc:
                        self._send_json({"ok": False, "error": str(exc)})
                elif path == "/api/test-maxcso":
                    import subprocess
                    maxcso_path = str(config.project_root / "tools" / "maxcso.exe")
                    try:
                        r = subprocess.run(
                            [maxcso_path, "--help"],
                            capture_output=True, timeout=5,
                        )
                        out = (r.stdout or r.stderr or b"").decode(errors="replace").strip()
                        first_line = out.splitlines()[0] if out else "maxcso disponible"
                        self._send_json({"ok": True, "version": first_line, "path": maxcso_path})
                    except FileNotFoundError:
                        self._send_json({"ok": False, "error": f"No encontrado: {maxcso_path!r}"})
                    except Exception as exc:
                        self._send_json({"ok": False, "error": str(exc)})
                elif path == "/api/logs":
                    # B7-9: list available log files and return last N lines of each
                    _lines_n = int(qs.get("lines", ["200"])[0])
                    _log_files = {
                        "rommgr":     config.logs_dir / "rommgr.log",
                        "cable_sync": config.project_root / ".rommgr" / "cable_sync_ops.log",
                    }
                    _logs_out = {}
                    for _key, _lp in _log_files.items():
                        if _lp.exists():
                            try:
                                _raw = _lp.read_text(encoding="utf-8", errors="replace")
                                _tail = _raw.splitlines()[-_lines_n:]
                                _logs_out[_key] = {
                                    "path": str(_lp),
                                    "lines": _tail,
                                    "total_lines": len(_raw.splitlines()),
                                    "size_bytes": _lp.stat().st_size,
                                }
                            except Exception as _exc:
                                _logs_out[_key] = {"path": str(_lp), "error": str(_exc)}
                        else:
                            _logs_out[_key] = {"path": str(_lp), "lines": [], "total_lines": 0, "size_bytes": 0}
                    self._send_json({"logs": _logs_out})
                elif path == "/api/disc-folders":
                    # Return subfolders of library_root that look like disc-based platforms
                    _DISC_PLATFORMS = {
                        "psx", "ps1", "ps2", "ps3", "saturn", "dreamcast",
                        "gamecube", "gc", "wii", "wiiu", "3do", "cdi",
                        "pce-cd", "pcenginecd", "segacd", "megacd",
                        "neogeocd", "lynx",
                    }
                    _DISC_EXTS = frozenset({".cue", ".chd", ".iso", ".bin", ".mdf", ".img", ".ccd"})
                    root = config.library_root
                    if root and root.exists():
                        folders = []
                        for f in sorted(root.iterdir()):
                            if not f.is_dir():
                                continue
                            name_key = f.name.lower().replace(" ", "").replace("-", "")
                            if name_key not in {p.replace("-", "") for p in _DISC_PLATFORMS}:
                                continue
                            # Only include if folder actually contains disc files
                            has_disc = any(
                                child.suffix.lower() in _DISC_EXTS
                                for child in f.rglob("*") if child.is_file()
                            )
                            if has_disc:
                                folders.append(str(f))
                        self._send_json({"folders": folders, "library_root": str(root)})
                    else:
                        self._send_json({"folders": [], "library_root": None})
                elif path == "/api/orphaned-saves":
                    source = qs.get("path", [None])[0]
                    if not source:
                        self._send_json({"error": "path parameter required"})
                    else:
                        import re as _re
                        from rom_manager.utils.orphan_finder import find_orphaned_saves
                        orphans = find_orphaned_saves(Path(source).resolve(), config.save_extensions)

                        def _norm(s: str) -> str:
                            s = s.lower()
                            s = _re.sub(r"\s*[\(\[][^\)\]]+[\)\]]", "", s)
                            return s.strip()

                        # Load all ROMs from DB for fuzzy stem matching
                        with repository.connect() as _conn:
                            _all_games = _conn.execute(
                                "SELECT id, original_filename, source_path, platform "
                                "FROM games WHERE file_type='rom'"
                            ).fetchall()
                        _game_stems = [
                            (g, _norm(Path(g["original_filename"]).stem))
                            for g in _all_games
                        ]

                        orphan_list = []
                        for o in orphans:
                            norm_o = _norm(o.stem)
                            suggestions: list[dict] = []
                            if len(norm_o) >= 5:
                                for game, norm_g in _game_stems:
                                    if len(norm_g) >= 5 and (
                                        norm_g.startswith(norm_o[:6]) or
                                        norm_o.startswith(norm_g[:6])
                                    ):
                                        suggestions.append({
                                            "game_id": game["id"],
                                            "filename": game["original_filename"],
                                            "source_path": game["source_path"],
                                            "platform": game["platform"] or "",
                                        })
                                        if len(suggestions) >= 3:
                                            break
                            orphan_list.append({
                                "save_path": o.save_path, "stem": o.stem,
                                "extension": o.extension, "size_bytes": o.size_bytes,
                                "suggestions": suggestions,
                            })

                        self._send_json({"orphans": orphan_list, "total": len(orphans)})
                elif path == "/api/db-backup":
                    db_path = config.database_path
                    if not db_path.exists():
                        self._send(404, "text/plain", b"Database not found")
                    else:
                        self._send(200, "application/octet-stream", db_path.read_bytes(),
                                   extra_headers={"Content-Disposition": 'attachment; filename="library.sqlite"'})
                elif path == "/api/folder-analysis":
                    folder_path = qs.get("path", [None])[0] or None
                    if not folder_path:
                        self._send(400, "text/plain; charset=utf-8", b"path parameter required")
                    else:
                        self._send_json(_build_folder_analysis(folder_path, config))
                elif path == "/api/ra-check.csv":
                    result = _job_results.get("ra_check")
                    if not result or result.get("error") or not result.get("alternatives_csv"):
                        self._send(404, "text/plain", b"No RA check result available")
                    else:
                        body = result["alternatives_csv"].encode()
                        self._send(200, "text/csv; charset=utf-8", body,
                                   extra_headers={"Content-Disposition": 'attachment; filename="ra_alternatives.csv"'})
                elif path == "/api/asset-image":
                    gid = qs.get("game_id", [None])[0]
                    if not gid:
                        self._send(404, "text/plain; charset=utf-8", b"game_id required")
                        return
                    try:
                        with repository.connect() as _ic:
                            row = _ic.execute(
                                "SELECT box_art_path FROM game_metadata WHERE game_id = ?", (int(gid),)
                            ).fetchone()
                        if not row or not row["box_art_path"]:
                            self._send(404, "text/plain; charset=utf-8", b"no image")
                            return
                        img_path = Path(row["box_art_path"])
                        if not img_path.exists():
                            self._send(404, "text/plain; charset=utf-8", b"file not found")
                            return
                        ext = img_path.suffix.lower()
                        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png" if ext == ".png" else "image/octet-stream"
                        data_bytes = img_path.read_bytes()
                        self.send_response(200)
                        self.send_header("Content-Type", mime)
                        self.send_header("Content-Length", str(len(data_bytes)))
                        self.send_header("Cache-Control", "max-age=3600")
                        self.end_headers()
                        self.wfile.write(data_bytes)
                    except Exception as exc:
                        self._send(500, "text/plain; charset=utf-8", str(exc).encode())
                elif path == "/api/platform-stats":
                    src_root = qs.get("root", [None])[0] or None
                    _ps_repo = _get_repo(src_root or "")
                    with _ps_repo.connect() as _pc:
                        if src_root:
                            rows = _pc.execute(
                                "SELECT platform, COUNT(*) AS cnt FROM games "
                                "WHERE source_path LIKE ? AND file_type = 'rom' "
                                "GROUP BY platform ORDER BY cnt DESC",
                                [src_root.rstrip("/\\") + "%"],
                            ).fetchall()
                        else:
                            rows = _pc.execute(
                                "SELECT platform, COUNT(*) AS cnt FROM games "
                                "WHERE file_type = 'rom' "
                                "GROUP BY platform ORDER BY cnt DESC"
                            ).fetchall()
                    self._send_json({"platforms": [{"platform": r["platform"] or "?", "count": r["cnt"]} for r in rows]})
                elif path == "/api/junk-scan":
                    folder = qs.get("path", [None])[0] or None
                    if not folder:
                        self._send_json({"error": "path required"})
                    else:
                        self._send_json(_build_junk_scan(folder))
                elif path == "/api/cable-sync-preview":
                    self._send_json(_build_cable_sync_preview(qs, config))
                elif path == "/api/cable-sync-log":
                    log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
                    if log_path.exists():
                        with open(log_path, "r", encoding="utf-8", errors="replace") as _lf:
                            lines = _lf.readlines()
                        tail = "".join(lines[-500:])
                        self._send_json({"log": tail, "lines": len(lines)})
                    else:
                        self._send_json({"log": "", "lines": 0})
                elif path == "/api/game":
                    game_id = qs.get("id", [None])[0]
                    if not game_id:
                        self._send_json({"error": "id required"})
                    else:
                        with repository.connect() as conn:
                            row = conn.execute("""
                                SELECT g.id, g.original_filename, g.source_path, g.platform,
                                       g.region, g.extension, g.size_bytes, g.sha1, g.md5, g.crc32,
                                       g.canonical_title, g.match_confidence, g.catalog_source,
                                       g.play_status, g.last_played_at, g.file_type,
                                       g.notes, g.is_favorite,
                                       m.title AS ss_title, m.year, m.genre, m.publisher,
                                       m.developer, m.description, m.rating, m.box_art_url,
                                       m.box_art_path, m.scraped_at, m.ss_game_id
                                FROM games g
                                LEFT JOIN game_metadata m ON m.game_id = g.id
                                WHERE g.id = ?
                            """, (int(game_id),)).fetchone()
                        if not row:
                            self._send_json({"error": "not found"})
                        else:
                            result = dict(row)
                            # UI-4: RA data lookup from local cache
                            try:
                                import json as _json
                                from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id
                                from rom_manager.retroachievements.ra_client import _parse_game_list
                                _plat = result.get("platform") or ""
                                _md5  = result.get("md5") or ""
                                if _plat and _md5:
                                    _cid = get_ra_console_id(_plat)
                                    if _cid:
                                        _cf = config.project_root / ".rommgr" / "ra_cache" / f"ra_hashes_{_cid}.json"
                                        if _cf.exists():
                                            _hl = _parse_game_list(_json.loads(_cf.read_text(encoding="utf-8")))
                                            _rg = _hl.get(_md5.lower())
                                            if _rg:
                                                result["ra_game_id"]      = _rg.id
                                                result["ra_title"]        = _rg.title
                                                result["ra_achievements"] = _rg.achievements
                                                result["ra_points"]       = _rg.points
                            except Exception:
                                pass
                            # UI-4: saves count by stem matching
                            try:
                                import os as _os2
                                _sp  = result.get("source_path") or ""
                                _stem = _os2.path.splitext(_os2.path.basename(_sp))[0]
                                if _stem:
                                    with repository.connect() as _sc2:
                                        _row2 = _sc2.execute(
                                            "SELECT COUNT(*) FROM saves WHERE original_path LIKE ?",
                                            (f"%{_stem}%",),
                                        ).fetchone()
                                        result["saves_count"] = _row2[0] if _row2 else 0
                            except Exception:
                                result["saves_count"] = 0
                            self._send_json(result)
                elif path == "/api/ss-quota":
                    has_dev = bool(config.screenscraper_dev_id and config.screenscraper_dev_pass)
                    self._send_json({**_ss_last_quota, "has_dev_account": has_dev})
                elif path == "/api/auth/status":
                    self._send_json({
                        "authenticated": self._is_authenticated(),
                        "pin_configured": bool(config.web_pin_hash),
                    })
                elif path == "/api/local-url":
                    ip = _get_local_ip()
                    self._send_json({"url": f"http://{ip}:{config.web_port}", "ip": ip, "port": config.web_port})
                elif path == "/api/wizard-detect":
                    self._send_json(_handle_wizard_detect(config))
                elif path == "/api/catalog-status":
                    self._send_json(_handle_catalog_status(config))
                elif path == "/api/system-status":
                    self._send_json(_handle_system_status(config))
                elif path == "/api/detect-cloud-folder":
                    self._send_json(_handle_detect_cloud_folder())
                elif path == "/s":
                    # Short redirect to the Android setup script (easy to type in Termux)
                    ip = _get_local_ip()
                    long_url = f"http://{ip}:{config.web_port}/api/anbernic-setup.sh"
                    self._send(302, "text/plain", b"", extra_headers={"Location": long_url})
                elif path == "/api/anbernic-setup.sh":
                    script = _build_anbernic_setup_sh(config)
                    ua = self.headers.get("User-Agent", "")
                    # If accessed from Android, force download; otherwise serve inline
                    extra: dict[str, str] = {}
                    if "Android" not in ua:
                        extra["Content-Disposition"] = "attachment; filename=\"retrovault-setup.sh\""
                    self._send(200, "text/x-sh; charset=utf-8", script.encode(), extra_headers=extra or None)
                elif path == "/api/rclone-export-config":
                    body, ct = _handle_rclone_export_config(config)
                    self._send(200, ct, body)
                elif path == "/api/autostart-status":
                    import sys as _sys
                    if _sys.platform == "win32":
                        from rom_manager.utils.tray_icon import get_autostart_status
                        self._send_json({"enabled": get_autostart_status(), "tray_running": _tray_instance is not None})
                    else:
                        self._send_json({"enabled": False, "tray_running": False})
                elif path == "/api/collection-stats":
                    data = _build_missing_data(config, repository)
                    self._send_json({
                        "platforms": [
                            {k: v for k, v in p.items() if k != "entries"}
                            for p in data
                        ]
                    })
                elif path == "/api/missing":
                    data = _build_missing_data(config, repository)
                    platform_filter = parsed_url.query  # e.g. "platform=Game+Boy+Advance"
                    pf = ""
                    for part in platform_filter.split("&"):
                        if part.startswith("platform="):
                            import urllib.parse
                            pf = urllib.parse.unquote_plus(part[len("platform="):])
                    if pf:
                        data = [p for p in data if p["platform"] == pf]
                    self._send_json({"platforms": data})
                elif path == "/api/wishlist":
                    self._send_json({"wishlist": repository.get_wishlist()})
                elif path == "/api/inbox-count":
                    inbox_p = config.inbox_path
                    count = 0
                    if inbox_p:
                        _ib = Path(inbox_p)
                        if _ib.exists():
                            count = sum(1 for f in _ib.iterdir() if f.is_file())
                    self._send_json({"count": count})
                elif path == "/api/operations-timeline":
                    _limit = int(qs.get("limit", ["50"])[0])
                    with repository.connect() as conn:
                        _rows = conn.execute(
                            "SELECT id, operation_type, source_path, target_path, result, message, created_at "
                            "FROM file_operations ORDER BY id DESC LIMIT ?",
                            (_limit,),
                        ).fetchall()
                    self._send_json({"operations": [dict(r) for r in _rows]})
                elif path == "/api/rclone-status":
                    self._send_json(_handle_rclone_status(config))
                elif path == "/api/auto-sync-status":
                    self._send_json({
                        "enabled": _auto_sync_enabled,
                        "status": dict(_auto_sync_status),
                        "config": {
                            "direction": config.auto_sync_direction,
                            "conflict_policy": config.conflict_policy,
                            "android_path": config.auto_sync_android_path,
                        },
                    })
                elif path == "/api/health-schedule":
                    import datetime as _dt
                    sched = _read_health_schedule(config)
                    last_raw = sched.get("last_run_at")
                    next_raw = None
                    overdue = True
                    if last_raw:
                        try:
                            last_dt = _dt.datetime.fromisoformat(last_raw.replace("Z", "+00:00"))
                            next_dt = last_dt + _dt.timedelta(days=_HEALTH_CHECK_INTERVAL_DAYS)
                            next_raw = next_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                            overdue = _dt.datetime.now(tz=_dt.timezone.utc) >= next_dt
                        except Exception:
                            pass
                    self._send_json({
                        "last_run_at": last_raw,
                        "next_run_at": next_raw,
                        "last_ok": sched.get("last_ok"),
                        "last_corrupted": sched.get("last_corrupted"),
                        "last_missing": sched.get("last_missing"),
                        "interval_days": _HEALTH_CHECK_INTERVAL_DAYS,
                        "overdue": overdue,
                    })
                elif path == "/api/openapi.json":
                    from rom_manager.web.openapi_spec import build_spec
                    spec = build_spec(config.web_host, config.web_port)
                    import json as _json
                    body = _json.dumps(spec, ensure_ascii=False, indent=2).encode()
                    self._send(200, "application/json; charset=utf-8", body)
                elif path == "/api/docs":
                    spec_url = f"http://{config.web_host}:{config.web_port}/api/openapi.json"
                    html = (
                        "<!doctype html><html><head><meta charset='utf-8'>"
                        "<title>Retro Vault — API Docs</title>"
                        "<style>body{font-family:monospace;background:#02020e;color:#00e5ff;padding:2rem}"
                        "a{color:#c800ff} h1{text-shadow:0 0 12px #00e5ff}</style></head><body>"
                        "<h1>Retro Vault REST API</h1>"
                        f"<p>OpenAPI 3.0 spec: <a href='/api/openapi.json'>/api/openapi.json</a></p>"
                        f"<p>Import in Postman / Insomnia / Swagger UI:</p>"
                        f"<pre>{spec_url}</pre>"
                        "<p><a href='/'>← Back to app</a></p>"
                        "</body></html>"
                    )
                    self._send(200, "text/html; charset=utf-8", html.encode())
                elif path == "/api/sd-sync-status":
                    self._send_json(dict(_sd_sync_status))
                elif path == "/api/report.json":
                    report = build_report(repository)
                    body = to_json(report).encode()
                    self._send(200, "application/json; charset=utf-8", body,
                               extra_headers={"Content-Disposition": 'attachment; filename="report.json"'})
                elif path == "/api/report.csv":
                    report = build_report(repository)
                    body = to_csv(report).encode()
                    self._send(200, "text/csv; charset=utf-8", body,
                               extra_headers={"Content-Disposition": 'attachment; filename="report.csv"'})
                elif path == "/api/export-missing":
                    import io as _io, csv as _csv
                    missing_data = _build_missing_data(config, repository)
                    buf = _io.StringIO()
                    writer = _csv.writer(buf)
                    writer.writerow(["platform", "title", "sha1", "search_query"])
                    for plat in missing_data:
                        plat_label = plat["platform"]
                        for entry in plat["entries"]:
                            query = f'{entry["title"]} {plat_label} No-Intro site:archive.org'
                            writer.writerow([plat_label, entry["title"], entry["sha1"], query])
                    body = buf.getvalue().encode("utf-8-sig")
                    self._send(200, "text/csv; charset=utf-8", body,
                               extra_headers={"Content-Disposition": 'attachment; filename="missing_roms.csv"'})
                elif path == "/api/bios-status":
                    from rom_manager.detection.bios_checker import check_bios
                    search_dirs = []
                    if config.library_root:
                        search_dirs.append(config.library_root)
                        search_dirs.append(config.library_root / "bios")
                        search_dirs.append(config.library_root / "system")
                    if config.retroarch_path:
                        ra = Path(config.retroarch_path)
                        search_dirs.append(ra.parent / "system")
                        search_dirs.append(ra.parent / "BIOS")
                    self._send_json({"bios": check_bios(search_dirs)})
                elif path == "/api/n64-scan":
                    folder = qs.get("path", [""])[0].strip()
                    if not folder:
                        self._send_json({"error": "path required"})
                    else:
                        from rom_manager.converters.n64_converter import scan_n64_roms
                        self._send_json({"roms": scan_n64_roms(Path(folder))})
                elif path == "/api/esde-status":
                    self._send_json(_handle_esde_status(config))
                elif path == "/api/retroarch-check":
                    self._send_json(_handle_retroarch_check(config))
                elif path == "/api/copy-assets-to-esde":
                    self._send_json(_handle_copy_assets_to_esde(config))
                elif path == "/api/library-doctor":
                    self._send_json(_handle_library_doctor(config, repository))
                elif path == "/api/export-library":
                    fmt = qs.get("format", ["csv"])[0]
                    rows = repository.get_library_export()
                    if fmt == "json":
                        body = json.dumps(rows, ensure_ascii=False, default=str).encode("utf-8")
                        self._send(200, "application/json; charset=utf-8", body,
                                   extra_headers={"Content-Disposition": 'attachment; filename="library.json"'})
                    else:
                        import io as _io2, csv as _csv2
                        buf = _io2.StringIO()
                        writer = _csv2.writer(buf)
                        if rows:
                            writer.writerow(rows[0].keys())
                            for r in rows:
                                writer.writerow(r.values())
                        body = buf.getvalue().encode("utf-8-sig")
                        self._send(200, "text/csv; charset=utf-8", body,
                                   extra_headers={"Content-Disposition": 'attachment; filename="library.csv"'})
                elif path == "/api/collection-stats-v2":
                    root = qs.get("root", [""])[0]
                    stats_repo = _get_repo(root or "")
                    with stats_repo.connect() as conn:
                        # Totales por platform
                        by_plat = conn.execute(
                            "SELECT platform, COUNT(*) as n FROM games GROUP BY platform ORDER BY n DESC"
                        ).fetchall()
                        # Totales por play_status
                        by_status = conn.execute(
                            "SELECT COALESCE(play_status,'Sin estado') as s, COUNT(*) as n FROM games GROUP BY s ORDER BY n DESC"
                        ).fetchall()
                        # Totales por region
                        by_region = conn.execute(
                            "SELECT COALESCE(region,'?') as r, COUNT(*) as n FROM games GROUP BY r ORDER BY n DESC"
                        ).fetchall()
                        total = sum(r['n'] for r in by_plat)
                        favs = conn.execute("SELECT COUNT(*) as n FROM games WHERE favorite=1").fetchone()['n']
                    self._send_json({
                        'total': total, 'favorites': favs,
                        'by_platform': [dict(r) for r in by_plat],
                        'by_status': [dict(r) for r in by_status],
                        'by_region': [dict(r) for r in by_region],
                    })
                elif path == "/api/export-wishlist":
                    root = qs.get("root", [""])[0]
                    export_repo = _get_repo(root or "")
                    rows = export_repo.get_wishlist()
                    import io as _io3, csv as _csv3
                    buf = _io3.StringIO()
                    writer = _csv3.writer(buf)
                    writer.writerow(["Title", "Platform", "Region", "Notes"])
                    for r in rows:
                        writer.writerow([
                            r.get("title", ""),
                            r.get("platform", ""),
                            r.get("region", ""),
                            r.get("notes", "")
                        ])
                    body = buf.getvalue().encode("utf-8-sig")
                    self._send(200, "text/csv; charset=utf-8", body,
                               extra_headers={"Content-Disposition": 'attachment; filename="wishlist.csv"'})
                elif path == "/api/save-comparison":
                    self._send_json({"saves": repository.get_save_comparison()})
                elif path == "/api/game-sync-history":
                    sp = qs.get("source_path", [""])[0]
                    if not sp:
                        self._send_json({"error": "source_path required"})
                    else:
                        self._send_json({"history": repository.get_save_sync_history(sp)})
                elif path == "/api/inbox-scan":
                    inbox_path_str = qs.get("path", [""])[0].strip() or config.inbox_path
                    if not inbox_path_str:
                        self._send_json({"error": "path parameter required (or set inbox.path in config.toml)"})
                    else:
                        self._send_json(_build_inbox_scan(inbox_path_str))
                elif path == "/api/inbox-status":
                    self._send_json({
                        "running": _jobs["inbox"],
                        "progress": dict(_inbox_progress) if _inbox_progress else None,
                        "result": _job_results.get("inbox"),
                    })
                elif path == "/api/inbox-watcher-status":
                    self._send_json(dict(_inbox_watcher_status))
                else:
                    self._send(404, "text/plain", b"Not found")
            except Exception as exc:
                body = json.dumps({"error": str(exc)}).encode()
                self._send(500, "application/json", body)

        # ── POST ─────────────────────────────────────────────────────────────

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path

            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"

            # Handle multipart file uploads before JSON parse
            _ct = self.headers.get("Content-Type", "")
            if _ct.startswith("multipart/form-data") and path == "/api/inbox-upload":
                self._handle_inbox_upload(_ct, raw)
                return

            try:
                data: dict = json.loads(raw) if raw else {}
            except Exception:
                data = {}

            try:
                # S25: auth endpoints bypass session check
                if path == "/api/auth":
                    pin = str(data.get("pin", "")).strip()
                    if not config.web_pin_hash:
                        self._send_json({"ok": True})   # no PIN set → open access
                        return
                    if not pin:
                        self._send_json({"ok": False, "error": "PIN requerido"})
                        return
                    expected = _hash_pin(pin, config.web_pin_salt)
                    if secrets.compare_digest(expected, config.web_pin_hash):
                        token = _create_session(config.web_session_ttl)
                        self._send(200, "application/json; charset=utf-8",
                                   _json_response({"ok": True}),
                                   extra_headers=self._set_session_header(token))
                    else:
                        self._send_json({"ok": False, "error": "PIN incorrecto"})
                    return
                elif path == "/api/auth/logout":
                    token = self._session_token()
                    if token:
                        _destroy_session(token)
                    self._send(200, "application/json; charset=utf-8",
                               _json_response({"ok": True}),
                               extra_headers={"Set-Cookie": f"{_SESSION_COOKIE}=; Max-Age=0; Path=/"})
                    return
                elif path == "/api/set-pin":
                    # Authenticated OR no PIN configured yet (first-time setup)
                    if not self._is_authenticated():
                        self._send_json({"error": "No autorizado"})
                        return
                    pin = str(data.get("pin", "")).strip()
                    if len(pin) < 4 or len(pin) > 10:
                        self._send_json({"error": "El PIN debe tener entre 4 y 10 dígitos"})
                        return
                    salt = secrets.token_hex(16)
                    pin_hash = _hash_pin(pin, salt)
                    from rom_manager.config import write_config_toml
                    write_config_toml(config.project_root, {
                        "web.pin_hash": pin_hash,
                        "web.pin_salt": salt,
                    })
                    config.web_pin_hash = pin_hash
                    config.web_pin_salt = salt
                    # Invalidate all existing sessions so new PIN takes effect
                    with _sessions_lock:
                        _sessions.clear()
                    self._send_json({"ok": True})
                    return
                elif path == "/api/clear-pin":
                    if not self._is_authenticated():
                        self._send_json({"error": "No autorizado"})
                        return
                    from rom_manager.config import write_config_toml
                    write_config_toml(config.project_root, {
                        "web.pin_hash": "",
                        "web.pin_salt": "",
                    })
                    config.web_pin_hash = ""
                    config.web_pin_salt = ""
                    with _sessions_lock:
                        _sessions.clear()
                    self._send_json({"ok": True})
                    return

                # All other POST endpoints require auth
                if not self._is_authenticated():
                    self._send_json({"error": "No autorizado", "auth_required": True})
                    return

                if path == "/api/scan":
                    self._handle_scan(data)
                elif path == "/api/adb-scan":
                    self._handle_adb_scan(data)
                elif path == "/api/match":
                    self._handle_match()
                elif path == "/api/apply":
                    self._handle_apply(data)
                elif path == "/api/fix-platforms":
                    self._handle_fix_platforms()
                elif path == "/api/duplicates/delete":
                    self._handle_delete_duplicate(data)
                elif path == "/api/duplicates/delete-all":
                    self._handle_delete_all_duplicates()
                elif path == "/api/duplicates/exclude":
                    sha1 = data.get("sha1", "")
                    if sha1:
                        repository.exclude_duplicate_sha1(sha1)
                        self._send_json({"ok": True})
                    else:
                        self._send_error(400, "sha1 required")
                elif path == "/api/convert-n64":
                    src = data.get("source_path", "").strip()
                    dst = data.get("target_path", "").strip() or None
                    if not src:
                        self._send_json({"error": "source_path required"})
                    else:
                        from rom_manager.converters.n64_converter import convert_to_z64
                        res = convert_to_z64(Path(src), Path(dst) if dst else None)
                        self._send_json({
                            "success": res.success, "source_format": res.source_format,
                            "target_path": res.target_path, "error": res.error,
                        })
                elif path == "/api/export-lpl":
                    if not config.library_root:
                        self._send_json({"error": "library_root not configured"})
                    else:
                        from rom_manager.utils.lpl_generator import generate_lpl_playlists
                        try:
                            result = generate_lpl_playlists(
                                Path(config.library_root),
                                repository,
                                output_dir=Path(data["output_dir"]) if data.get("output_dir") else None,
                            )
                            self._send_json(result)
                        except Exception as exc:
                            self._send_json({"error": str(exc)})
                elif path == "/api/wishlist":
                    sha1 = (data.get("sha1") or "").strip().upper()
                    if not sha1:
                        self._send_error(400, "sha1 required")
                    elif data.get("remove"):
                        repository.remove_wishlist_entry(sha1)
                        self._send_json({"ok": True, "removed": sha1})
                    else:
                        repository.upsert_wishlist_entry(
                            sha1=sha1,
                            title=data.get("title", ""),
                            platform=data.get("platform", ""),
                            status=data.get("status", "searching"),
                            region=data.get("region", ""),
                            year=data.get("year", ""),
                            dat_source=data.get("dat_source", ""),
                        )
                        self._send_json({"ok": True})
                # D8-3: resolve conflicts keeping RA winner
                elif path == "/api/apply-ra-conflicts":
                    self._handle_apply_ra_conflicts(data)
                # D8-4: discard a single RA-duplicate file
                elif path == "/api/ra-duplicates/discard":
                    self._handle_ra_duplicate_discard(data)
                # D8-4: discard all files without RA support in every version group
                elif path == "/api/ra-duplicates/discard-all":
                    self._handle_ra_duplicate_discard_all()
                # Bulk discard games with NO RA support at all (from RA check)
                elif path == "/api/ra-check/discard-no-support":
                    self._handle_ra_discard_no_support()
                # B1-4: resolve title-based duplicates by keeping the one with RA support
                elif path == "/api/resolve-duplicate-ra":
                    self._handle_resolve_duplicate_ra(data)
                elif path == "/api/sync":
                    self._handle_sync(data)
                elif path == "/api/convert-chd":
                    self._handle_convert_chd(data)
                elif path == "/api/convert-cso":
                    self._handle_convert_cso(data)
                elif path == "/api/scrape":
                    self._handle_scrape(data)
                elif path == "/api/export-gamelists":
                    self._handle_export_gamelists(data)
                elif path == "/api/config":
                    self._handle_save_config(data)
                elif path == "/api/notify-test":
                    from rom_manager.utils.notifier import notify
                    import sys as _sys
                    if _sys.platform != "win32":
                        self._send_json({"ok": False, "error": "Solo disponible en Windows"})
                    else:
                        notify("Retro Vault — Prueba", "Las notificaciones funcionan correctamente ✓")
                        self._send_json({"ok": True})
                elif path == "/api/extract-zip":
                    self._handle_extract_zip(data)
                elif path == "/api/generate-m3u":
                    self._handle_generate_m3u(data)
                elif path == "/api/verify-multidisc":
                    self._handle_verify_multidisc(data)
                elif path == "/api/orphaned-saves/delete":
                    self._handle_delete_orphaned_saves(data)
                elif path == "/api/orphaned-saves/move":
                    self._handle_move_orphaned_save(data)
                elif path == "/api/orphaned-saves/move-to-archive":
                    self._handle_move_orphaned_saves_to_archive(data)
                elif path == "/api/doctor-move-rom":
                    # B7-7: move a misplaced ROM to its expected folder
                    _src = data.get("path", "")
                    _dst_dir = data.get("expected_dir", "")
                    if not _src or not _dst_dir:
                        self._send_json({"error": "path y expected_dir requeridos"})
                    else:
                        import shutil as _shl
                        _src_p = Path(_src)
                        _dst_p = Path(_dst_dir) / _src_p.name
                        if not _src_p.exists():
                            self._send_json({"error": "Archivo no encontrado"})
                        elif _dst_p.exists():
                            self._send_json({"error": f"Ya existe en destino: {_dst_p.name}"})
                        else:
                            try:
                                Path(_dst_dir).mkdir(parents=True, exist_ok=True)
                                _shl.move(str(_src_p), str(_dst_p))
                                self._send_json({"ok": True, "new_path": str(_dst_p)})
                            except Exception as _exc:
                                self._send_json({"error": str(_exc)})
                elif path == "/api/doctor-delete-dir":
                    # B7-7: delete an empty directory
                    _dir = data.get("path", "")
                    if not _dir:
                        self._send_json({"error": "path requerido"})
                    else:
                        _dir_p = Path(_dir)
                        if not _dir_p.exists():
                            self._send_json({"error": "Carpeta no encontrada"})
                        elif not _dir_p.is_dir():
                            self._send_json({"error": "No es una carpeta"})
                        else:
                            try:
                                _dir_p.rmdir()
                                self._send_json({"ok": True})
                            except Exception as _exc:
                                self._send_json({"error": str(_exc)})
                elif path == "/api/health-check":
                    self._handle_health_check(data)
                elif path == "/api/cleanup-zips":
                    self._handle_cleanup_zips(data)
                elif path == "/api/cleanup-cue-bin":
                    self._handle_cleanup_cue_bin(data)
                elif path == "/api/stop-job":
                    job_name = data.get("job", "")
                    _cancel_map = {
                        "scan":         _scan_cancel,
                        "cable_sync":   _cable_cancel,
                        "convert_chd":  _chd_cancel,
                        "extract_zip":  _zip_cancel,
                        "health_check": _health_cancel,
                        "ra_check":     _ra_cancel,
                        "scrape":       _scrape_cancel,
                        "match":        _match_cancel,
                    }
                    if job_name in _cancel_map:
                        _cancel_map[job_name].set()
                    with _job_lock:
                        if job_name in _jobs:
                            _jobs[job_name] = False
                        _scan_progress.clear()
                    self._send_json({"status": "stopped", "job": job_name})
                elif path == "/api/ra-check":
                    self._handle_ra_check(data)
                elif path == "/api/cable-sync":
                    self._handle_cable_sync(data)
                elif path == "/api/auto-sync-toggle":
                    global _auto_sync_enabled
                    _auto_sync_enabled = not _auto_sync_enabled
                    config.auto_sync_enabled = _auto_sync_enabled
                    self._send_json({"enabled": _auto_sync_enabled})
                elif path == "/api/auto-sync-save":
                    self._handle_auto_sync_save(data)
                elif path == "/api/migrate-split-db":
                    self._handle_migrate_split_db()
                elif path == "/api/junk-delete":
                    paths_to_delete = data.get("paths", [])
                    dry_run = bool(data.get("dry_run", True))
                    deleted = 0
                    failed = 0
                    freed_bytes = 0
                    errors: list[str] = []
                    for fp in paths_to_delete:
                        try:
                            p = Path(fp)
                            if p.is_file():
                                sz = p.stat().st_size
                                if not dry_run:
                                    p.unlink()
                                deleted += 1
                                freed_bytes += sz
                        except OSError as exc:
                            failed += 1
                            errors.append(str(exc))
                    self._send_json({"deleted": deleted, "failed": failed, "freed_bytes": freed_bytes, "dry_run": dry_run, "errors": errors[:10]})
                elif path == "/api/set-play-status":
                    game_id = data.get("game_id")
                    status  = data.get("status") or None
                    if not game_id:
                        self._send_json({"error": "game_id required"})
                        return
                    _status_repo = _get_repo(data.get("source_path", ""))
                    _status_repo.set_play_status(int(game_id), status)
                    self._send_json({"ok": True})
                elif path == "/api/set-metadata":
                    # S30: manual metadata editor
                    game_id = data.get("game_id")
                    if not game_id:
                        self._send_json({"error": "game_id required"})
                        return
                    gid = int(game_id)
                    if "notes" in data:
                        repository.set_notes(gid, data["notes"] or None)
                    if "canonical_title" in data:
                        repository.set_canonical_title(gid, data["canonical_title"])
                    _meta_fields = {k: v for k, v in data.items()
                                    if k in {"year", "genre", "publisher", "developer", "description", "rating"}}
                    if _meta_fields:
                        repository.upsert_metadata_manual(gid, **_meta_fields)
                    self._send_json({"ok": True})
                elif path == "/api/scrape-single":
                    # S30: scrape a single game (preview or apply)
                    game_id = data.get("game_id")
                    preview = bool(data.get("preview", False))
                    download_images = bool(data.get("images", False))
                    if not game_id:
                        self._send_json({"error": "game_id required"})
                        return
                    if not config.screenscraper_user:
                        self._send_json({"error": "Credenciales de ScreenScraper no configuradas"})
                        return
                    try:
                        from rom_manager.scraper.screenscraper import ScreenScraperClient, download_image
                        from rom_manager.scraper.platform_ids import get_system_id
                        from rom_manager.scanner.rom_scanner import utc_now
                        with repository.connect() as _conn:
                            _grow = _conn.execute(
                                "SELECT g.id, g.original_filename, g.source_path, g.platform, "
                                "g.crc32, g.md5, g.sha1, g.size_bytes, g.canonical_title "
                                "FROM games g WHERE g.id = ?", (int(game_id),)
                            ).fetchone()
                        if not _grow:
                            self._send_json({"error": "Juego no encontrado"})
                            return
                        _game = dict(_grow)
                        _client = ScreenScraperClient(
                            user=config.screenscraper_user,
                            password=config.screenscraper_pass,
                            dev_id=config.screenscraper_dev_id,
                            dev_password=config.screenscraper_dev_pass,
                        )
                        _sys_id = get_system_id(_game["platform"])
                        _result = _client.search(
                            crc32=_game["crc32"], md5=_game["md5"], sha1=_game["sha1"],
                            filename=_game["original_filename"], size_bytes=_game["size_bytes"],
                            system_id=_sys_id,
                        )
                        if _result is None:
                            _name_hint = _game.get("canonical_title") or _game["original_filename"]
                            _result = _client.search_by_name(_name_hint, system_id=_sys_id)
                        if _client.last_quota:
                            _ss_last_quota.update(_client.last_quota)
                        if _result is None:
                            self._send_json({"found": False, "error": "No encontrado en ScreenScraper"})
                            return
                        _preview_data = {
                            "found": True,
                            "ss_game_id": _result.ss_game_id,
                            "title": _result.title,
                            "year": _result.year,
                            "genre": _result.genre,
                            "publisher": _result.publisher,
                            "developer": _result.developer,
                            "description": _result.description,
                            "rating": _result.rating,
                            "box_art_url": _result.box_art_url,
                        }
                        if preview:
                            self._send_json(_preview_data)
                            return
                        # Apply
                        _box_art_path = ""
                        _screenshot_path = ""
                        _wheel_path = ""
                        if download_images:
                            _src_parent = Path(_game["source_path"]).parent
                            _stem = Path(_game["original_filename"]).stem
                            if _result.box_art_url:
                                _ext = ".png" if ".png" in _result.box_art_url.lower() else ".jpg"
                                _dest = _src_parent / "media" / "images" / f"{_stem}{_ext}"
                                download_image(_result.box_art_url, _dest)
                                _box_art_path = str(_dest)
                            if _result.screenshot_url:  # B6-7
                                _ext = ".png" if ".png" in _result.screenshot_url.lower() else ".jpg"
                                _dest = _src_parent / "media" / "screenshots" / f"{_stem}{_ext}"
                                try:
                                    download_image(_result.screenshot_url, _dest)
                                    _screenshot_path = str(_dest)
                                except Exception:
                                    pass
                            if _result.wheel_url:  # B6-7
                                _ext = ".png" if ".png" in _result.wheel_url.lower() else ".jpg"
                                _dest = _src_parent / "media" / "wheels" / f"{_stem}{_ext}"
                                try:
                                    download_image(_result.wheel_url, _dest)
                                    _wheel_path = str(_dest)
                                except Exception:
                                    pass
                        with repository.batch() as _bconn:
                            repository.upsert_metadata(
                                game_id=int(game_id),
                                ss_game_id=_result.ss_game_id,
                                title=_result.title, year=_result.year,
                                genre=_result.genre, publisher=_result.publisher,
                                developer=_result.developer, description=_result.description,
                                rating=_result.rating, box_art_url=_result.box_art_url,
                                box_art_path=_box_art_path,
                                screenshot_path=_screenshot_path,
                                wheel_path=_wheel_path,
                                scraped_at=utc_now(),
                                connection=_bconn,
                            )
                        self._send_json({**_preview_data, "applied": True})
                    except Exception as _exc:
                        self._send_json({"error": str(_exc)})
                elif path == "/api/toggle-favorite":
                    game_id = data.get("game_id")
                    if not game_id:
                        self._send_json({"error": "game_id required"})
                        return
                    new_val = repository.toggle_favorite(int(game_id))
                    self._send_json({"ok": True, "is_favorite": new_val})
                elif path == "/api/tag":
                    game_id = data.get("game_id")
                    tag = str(data.get("tag", "")).strip()
                    action = data.get("action", "add")  # "add" | "remove"
                    if not game_id or not tag:
                        self._send_json({"error": "game_id and tag required"})
                        return
                    if action == "remove":
                        repository.remove_tag(int(game_id), tag)
                    else:
                        repository.add_tag(int(game_id), tag)
                    self._send_json({"ok": True, "tags": repository.get_tags(int(game_id))})
                elif path == "/api/open-folder":
                    import os as _os_of
                    import subprocess as _sp_of
                    folder_path = data.get("path", "").strip()
                    if not folder_path:
                        self._send_json({"ok": False, "error": "path required"})
                    else:
                        try:
                            p = _os_of.path.abspath(folder_path)
                            folder = p if _os_of.path.isdir(p) else _os_of.path.dirname(p)
                            if sys.platform == "win32":
                                _sp_of.Popen(["explorer", folder])
                            else:
                                _sp_of.Popen(["xdg-open", folder])
                            self._send_json({"ok": True})
                        except Exception as _exc_of:
                            self._send_json({"ok": False, "error": str(_exc_of)})
                elif path == "/api/launch":
                    import subprocess
                    game_id = data.get("game_id")
                    if not game_id:
                        self._send_json({"error": "game_id required"})
                        return
                    with repository.connect() as conn:
                        row = conn.execute(
                            "SELECT source_path, platform FROM games WHERE id = ?", (int(game_id),)
                        ).fetchone()
                    if not row:
                        self._send_json({"error": "game not found"})
                        return
                    retroarch_exe = config.retroarch_path or ""
                    if not retroarch_exe or not Path(retroarch_exe).exists():
                        self._send_json({"error": "RetroArch no configurado. Ajusta retroarch_path en Settings."})
                        return
                    platform = row["platform"] or ""
                    core = (config.launcher_cores or {}).get(platform, "")
                    rom = row["source_path"]
                    cmd = [retroarch_exe]
                    if core:
                        cmd += ["--libretro", core]
                    cmd.append(rom)
                    try:
                        subprocess.Popen(cmd)
                        self._send_json({"ok": True, "cmd": cmd})
                    except Exception as exc:
                        self._send_json({"error": str(exc)})
                elif path == "/api/restore-backup":
                    backup_path_str  = data.get("backup_path", "").strip()
                    original_save_str = data.get("original_save", "").strip()
                    if not backup_path_str or not original_save_str:
                        self._send_json({"error": "backup_path and original_save required"})
                        return
                    from rom_manager.backup.save_backup import restore_backup
                    bp = Path(backup_path_str)
                    tp = Path(original_save_str)
                    # Safety: target must be inside library_root
                    if config.library_root and not str(tp).startswith(str(config.library_root)):
                        self._send_json({"error": "La ruta destino está fuera de la biblioteca"})
                        return
                    ok = restore_backup(bp, tp)
                    if ok:
                        self._send_json({"ok": True, "restored_to": str(tp)})
                    else:
                        self._send_json({"error": f"Backup no encontrado: {bp.name}"})
                elif path == "/api/backup-now":
                    # Manual full saves backup — runs in background
                    def _do_backup_now():
                        try:
                            import rom_manager.web.server as _srv
                            from rom_manager.backup.save_backup import create_saves_zip
                            saves_dirs = []
                            if config.library_root and config.library_root.exists():
                                saves_dirs.append(config.library_root)
                            for src in config.sync_sources:
                                p = Path(src.local_dir)
                                if p.exists() and p not in saves_dirs:
                                    saves_dirs.append(p)
                            zip_path = create_saves_zip(
                                saves_dirs,
                                set(config.save_extensions),
                                config.data_dir / "saves-backup" / "saves-zips",
                            )
                            import time as _t
                            _srv._job_results["backup_now"] = {
                                "ok": True,
                                "zip": str(zip_path),
                                "size": zip_path.stat().st_size,
                                "result_ts": str(_t.time()),
                            }
                        except Exception as exc:
                            import time as _t
                            import rom_manager.web.server as _srv
                            _srv._job_results["backup_now"] = {
                                "ok": False, "error": str(exc), "result_ts": str(_t.time()),
                            }
                        finally:
                            import rom_manager.web.server as _srv
                            with _srv._job_lock:
                                _srv._jobs["backup_now"] = False

                    with _job_lock:
                        if _jobs.get("backup_now"):
                            self._send_json({"status": "already_running"})
                            return
                        _jobs["backup_now"] = True
                    threading.Thread(target=_do_backup_now, daemon=True).start()
                    self._send_json({"status": "started"})
                elif path == "/api/export-pegasus":
                    if not config.library_root:
                        self._send_json({"error": "library_root not configured"})
                        return
                    try:
                        from rom_manager.scraper.pegasus_writer import write_pegasus_metadata
                        result_peg = write_pegasus_metadata(config.library_root, repository)
                        self._send_json({"ok": True, "platforms": result_peg["platforms"], "games": result_peg["games"]})
                    except Exception as exc:
                        self._send_json({"error": str(exc)})
                elif path == "/api/import-dats":
                    self._send_json(_handle_import_dats(data, config))
                elif path == "/api/import-arcade-catalog":
                    self._send_json(_handle_import_arcade_catalog(data, config))
                elif path == "/api/inbox-run":
                    self._handle_inbox_run(data)
                elif path == "/api/setup-run":
                    self._handle_setup_run(data)
                elif path == "/api/create-library-structure":
                    self._handle_create_library_structure(data)
                elif path == "/api/organize-library":
                    self._handle_organize_library(data)
                elif path == "/api/autostart-toggle":
                    import sys as _sys
                    if _sys.platform != "win32":
                        self._send_json({"error": "Solo disponible en Windows"})
                        return
                    from rom_manager.utils.tray_icon import (
                        get_autostart_status, set_autostart, _default_launch_cmd,
                    )
                    currently_on = get_autostart_status()
                    ok = set_autostart(not currently_on, "" if currently_on else _default_launch_cmd())
                    new_state = get_autostart_status()
                    self._send_json({"ok": ok, "enabled": new_state})
                else:
                    self._send(404, "text/plain", b"Not found")
            except Exception as exc:
                body = json.dumps({"error": str(exc)}).encode()
                self._send(500, "application/json", body)

        # ── POST handlers ────────────────────────────────────────────────────

        def _handle_scan(self, data: dict) -> None:
            # Accept either a single source_path or a list source_paths
            raw_paths = data.get("source_paths") or []
            single = data.get("source_path", "").strip()
            if single and not raw_paths:
                raw_paths = [single]
            raw_paths = [p.strip() for p in raw_paths if str(p).strip()]
            if not raw_paths:
                self._send_json({"error": "source_path is required"})
                return
            quick = bool(data.get("quick", False))

            with _job_lock:
                if _jobs["scan"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["scan"] = True

            _scan_cancel.clear()
            _scan_progress.clear()

            def run() -> None:
                try:
                    from rom_manager.scanner import scan_library
                    from rom_manager.scanner.rom_scanner import ScanResult
                    total = ScanResult()

                    def _progress_cb(files_seen: int, roms: int, current_file: str = "") -> None:
                        _scan_progress.update({
                            "files_seen": files_seen,
                            "roms_detected": roms,
                            "current_path": str(source),
                            "current_file": current_file,
                        })

                    for raw in raw_paths:
                        source = Path(raw).resolve()
                        _scan_progress["current_path"] = str(source)
                        # Route to the correct DB based on whether path is under library_root
                        _scan_repo = _get_repo(str(source))
                        r = scan_library(
                            source, config, _scan_repo, logger, quick=quick,
                            stop_event=_scan_cancel, progress_cb=_progress_cb,
                        )
                        total.files_seen += r.files_seen
                        total.roms_detected += r.roms_detected
                        total.roms_skipped += r.roms_skipped
                        total.saves_detected += r.saves_detected
                        total.errors += r.errors
                    _job_results["scan"] = {
                        "result_ts": utc_now(),
                        "files_seen": total.files_seen,
                        "roms_detected": total.roms_detected,
                        "roms_skipped": total.roms_skipped,
                        "saves_detected": total.saves_detected,
                        "errors": total.errors,
                        "paths_scanned": len(raw_paths),
                        "pruned": total.pruned,
                        "cancelled": _scan_cancel.is_set(),
                    }
                    # D8-7: auto-generate library report cache after scan (background, non-blocking)
                    # Generate a cached report for every scanned path (PC and Android)
                    # Auto-trigger RA check after scan if API key is configured
                    if not _scan_cancel.is_set():
                        if config.ra_api_key:
                            _start_ra_check_bg(config.ra_api_key)
                        for _rpt_path in raw_paths:
                            if not _rpt_path:
                                continue
                            def _cache_report(_p=_rpt_path):
                                try:
                                    _rpt_data = _build_library_report(_p, _get_repo(_p), config)
                                    _cache_dir = config.project_root / ".rommgr"
                                    _cache_dir.mkdir(parents=True, exist_ok=True)
                                    (_cache_dir / "last_report.json").write_text(
                                        json.dumps(_rpt_data, ensure_ascii=False), encoding="utf-8"
                                    )
                                except Exception:
                                    pass
                            threading.Thread(target=_cache_report, daemon=True).start()
                except Exception as exc:
                    _job_results["scan"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _scan_progress.clear()
                        _jobs["scan"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started"})

        def _handle_adb_scan(self, data: dict) -> None:
            """Scan files on an Android device via ADB and register them in the DB."""
            adb_serial   = data.get("adb_serial", "").strip()
            android_path = data.get("android_path", "/storage/emulated/0").strip().rstrip("/")

            if not adb_serial:
                self._send_json({"error": "adb_serial is required"})
                return

            with _job_lock:
                if _jobs["scan"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["scan"] = True

            def run() -> None:
                try:
                    from pathlib import PurePosixPath
                    from rom_manager.sync.adb_transport import AdbTransport
                    from rom_manager.detection.platform_detector import detect_platform
                    from rom_manager.detection.region_parser import parse_region_from_name
                    from rom_manager.detection.set_detector import detect_set_type
                    from rom_manager.scanner.rom_scanner import utc_now

                    transport  = AdbTransport(config.adb, adb_serial, timeout=120)
                    timestamp  = utc_now()
                    save_exts  = frozenset(config.save_extensions)
                    asset_exts = frozenset(config.frontend_asset_extensions)
                    excluded   = frozenset(d.lower() for d in config.excluded_directories)

                    # ADB scan always goes to the Android repository
                    _adb_repo = _repo_android
                    scan_run_id = _adb_repo.create_scan_run(android_path, timestamp)
                    roms = saves = assets = errors = 0
                    seen_paths: set[str] = set()

                    # Fetch the file list from the device (~1 round-trip)
                    all_files = transport.ls_recursive(android_path, timeout=180)

                    with _adb_repo.batch() as conn:
                        for fi in all_files:
                            ap = fi.android_path
                            seen_paths.add(ap)
                            parts = ap.split("/")
                            # Skip excluded directories (e.g. Android/, DCIM/, BIOS/)
                            if any(seg.lower() in excluded for seg in parts):
                                continue

                            name   = PurePosixPath(ap).name
                            suffix = PurePosixPath(ap).suffix.lower()
                            # Relative parent = the folder containing the file, relative to android_path
                            try:
                                rel_parent = str(PurePosixPath(ap).parent.relative_to(android_path))
                            except ValueError:
                                rel_parent = ""

                            try:
                                if suffix in save_exts:
                                    _adb_repo.upsert_save(
                                        original_path=ap,
                                        relative_parent=rel_parent,
                                        extension=suffix,
                                        size_bytes=fi.size,
                                        timestamp=timestamp,
                                        connection=conn,
                                    )
                                    saves += 1
                                elif suffix in asset_exts or name.lower() == "gamelist.xml":
                                    assets += 1  # don't store assets for ADB scan
                                elif suffix in {
                                    ".zip", ".7z", ".rar",          # archives
                                    ".xml", ".txt", ".log", ".db",  # data files
                                    ".apk", ".sh", ".py",           # executables
                                } or not suffix:
                                    pass  # ignore
                                else:
                                    # Treat as ROM — detect platform from path
                                    fake_path = Path(ap)
                                    platform  = detect_platform(fake_path)
                                    _adb_repo.upsert_game(
                                        original_filename=name,
                                        source_path=ap,
                                        platform=platform,
                                        file_type="rom",
                                        relative_parent=rel_parent,
                                        region=parse_region_from_name(name),
                                        extension=suffix,
                                        size_bytes=fi.size,
                                        mtime=int(fi.mtime),
                                        sha1="",
                                        md5="",
                                        crc32="",
                                        set_type=detect_set_type(fake_path),
                                        timestamp=timestamp,
                                        connection=conn,
                                    )
                                    roms += 1
                            except Exception as exc:
                                errors += 1
                                logger.error("ADB scan error for %s: %s", ap, exc)

                    pruned = _adb_repo.prune_stale_entries(android_path, seen_paths)
                    finished_at = utc_now()
                    _adb_repo.complete_scan_run(
                        scan_run_id,
                        finished_at=finished_at,
                        files_seen=len(all_files),
                        roms_detected=roms,
                        saves_detected=saves,
                        assets_detected=assets,
                        system_files_detected=0,
                        unknown_files_detected=0,
                        errors=errors,
                    )
                    _job_results["scan"] = {
                        "result_ts": utc_now(),
                        "files_seen": len(all_files),
                        "roms_detected": roms,
                        "roms_skipped": 0,
                        "saves_detected": saves,
                        "errors": errors,
                        "paths_scanned": 1,
                        "pruned": pruned,
                        "source": "adb",
                        "android_path": android_path,
                    }
                except Exception as exc:
                    _job_results["scan"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _jobs["scan"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started"})

        def _handle_match(self) -> None:
            def run() -> None:
                _match_cancel.clear()
                try:
                    from rom_manager.catalog.matcher import CatalogMatcher
                    matcher = CatalogMatcher(
                        nointro_dir=config.catalogs_nointro_dir,
                        redump_dir=config.catalogs_redump_dir,
                        arcade_dir=config.catalogs_arcade_dir,
                    )
                    games = repository.get_unresolved_games()
                    matched_high = matched_low = unmatched = 0
                    with repository.batch() as conn:
                        for game in games:
                            if _match_cancel.is_set():
                                break
                            result = matcher.match(game.sha1, game.original_filename)
                            if result is not None:
                                repository.update_match(
                                    game.source_path,
                                    canonical_title=result.title,
                                    match_confidence=result.confidence,
                                    catalog_source=result.catalog_source,
                                    platform=result.platform,
                                    connection=conn,
                                )
                                if result.confidence == "high":
                                    matched_high += 1
                                else:
                                    matched_low += 1
                            else:
                                unmatched += 1
                    _job_results["match"] = {
                        "total": len(games),
                        "matched_high": matched_high,
                        "matched_low": matched_low,
                        "unmatched": unmatched,
                        "cancelled": _match_cancel.is_set(),
                    }
                except Exception as exc:
                    _job_results["match"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _jobs["match"] = False

            self._send_json(_start_job("match", run))

        def _handle_fix_platforms(self) -> None:
            from rom_manager.detection.platform_detector import detect_platform
            updated = repository.backfill_platforms(detect_platform)
            self._send_json({"updated": updated})

        def _handle_create_library_structure(self, data: dict) -> None:
            """Create the canonical ES-DE folder structure under library_root (and optionally android_root)."""
            from pathlib import Path as _Path
            if not config.library_root:
                self._send_json({"error": "library_root no configurado"})
                return

            also_android = bool(data.get("also_android"))
            android_root_str = config.anbernic_root or None

            def _create_tree(root: _Path) -> tuple[list[str], list[str]]:
                created: list[str] = []
                skipped: list[str] = []
                for folder in _STANDARD_PLATFORM_FOLDERS:
                    plat_dir = root / folder
                    if not plat_dir.exists():
                        plat_dir.mkdir(parents=True, exist_ok=True)
                        created.append(folder)
                    else:
                        skipped.append(folder)
                    for sub in ("media/images", "media/videos"):
                        sub_dir = plat_dir / _Path(sub)
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
                # Per-platform saves/ and states/ subfolders — keeps each console's saves separate
                for folder in _STANDARD_PLATFORM_FOLDERS:
                    for special_sub in ("saves", "states"):
                        sub_dir = root / special_sub / folder
                        if not sub_dir.exists():
                            sub_dir.mkdir(parents=True, exist_ok=True)
                            created.append(f"{special_sub}/{folder}")
                return created, skipped

            pc_root = _Path(config.library_root)
            pc_created, pc_skipped = _create_tree(pc_root)

            android_result: dict = {}
            if also_android and android_root_str:
                android_root = _Path(android_root_str)
                if android_root.exists():
                    ab_created, ab_skipped = _create_tree(android_root)
                    android_result = {"root": str(android_root), "created": ab_created, "skipped": ab_skipped}
                else:
                    android_result = {"root": str(android_root), "error": "Ruta no accesible — conecta la tarjeta SD o el dispositivo primero"}

            self._send_json({
                "created": pc_created,
                "skipped": pc_skipped,
                "root": str(pc_root),
                "android": android_result,
            })

        def _handle_organize_library(self, data: dict) -> None:
            """Move ROMs → platform folders, saves → saves/{platform}/, BIOS candidates → bios/. Updates DB."""
            import shutil as _shutil
            from pathlib import Path as _Path
            dry_run = data.get("dry_run", True)
            if not config.library_root:
                self._send_json({"error": "library_root no configurado"})
                return
            root = _Path(config.library_root)
            saves_dir = root / "saves"
            bios_dir = root / "bios"

            save_exts = frozenset(getattr(config, "save_extensions", [
                ".sav", ".srm", ".state", ".ogg", ".rtc",
            ]))
            # BIOS heuristic: .bin files not matched as ROMs, or known BIOS filenames
            _known_bios_names = frozenset({
                "scph1001.bin", "scph5500.bin", "scph5501.bin", "scph5502.bin",
                "scph7001.bin", "scph7502.bin", "scph10000.bin",
                "bios_CD_E.bin", "bios_CD_J.bin", "bios_CD_U.bin",
                "dc_boot.bin", "dc_flash.bin",
                "gba_bios.bin",
                "bios7.bin", "bios9.bin", "firmware.bin",
                "ym2608_adpcm_rom.bin",
            })

            moves_roms: list[dict] = []
            moves_saves: list[dict] = []
            moves_bios: list[dict] = []
            errors: list[str] = []

            # 1. ROMs + their associated saves
            with repository.connect() as conn:
                rows = conn.execute(
                    "SELECT id, source_path, platform FROM games WHERE source_path IS NOT NULL"
                ).fetchall()
            for row in rows:
                game_id, src_str, platform = row[0], row[1], row[2] or ""
                src = _Path(src_str)
                if not src.exists():
                    continue
                es_folder = _ES_PLATFORM_FOLDERS.get(platform, "")
                if not es_folder:
                    continue
                target_dir = root / es_folder
                target = target_dir / src.name
                if src == target:
                    # ROM already in place — still check for sibling saves to centralise
                    pass
                else:
                    moves_roms.append({"source": str(src), "target": str(target), "platform": platform, "filename": src.name})
                    if not dry_run:
                        try:
                            target_dir.mkdir(parents=True, exist_ok=True)
                            if target.exists():
                                errors.append(f"Conflicto ROM: {src.name} ya existe en {es_folder}/")
                            else:
                                _shutil.move(str(src), str(target))
                                with repository.connect() as conn:
                                    conn.execute(
                                        "UPDATE games SET source_path = ?, updated_at = ? WHERE source_path = ?",
                                        (str(target), _utc_now_str(), src_str),
                                    )
                                    conn.commit()
                        except Exception as exc:
                            errors.append(f"ROM {src.name}: {exc}")

                # Move sibling saves (same stem, save extensions) → saves/{platform}/
                # Each platform gets its own subfolder so saves never mix across consoles.
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
                                    _shutil.move(str(sibling), str(save_target))
                            except Exception as exc:
                                errors.append(f"Save {sibling.name}: {exc}")

            # 2. BIOS candidates: scan root + immediate subdirs for known BIOS filenames or .bin not in DB
            with repository.connect() as conn:
                known_paths = {row[0] for row in conn.execute("SELECT source_path FROM games").fetchall()}
            for candidate in list(root.rglob("*.bin")):
                if candidate.parent.name in ("bios", "saves", "states", "inbox", "screenshots"):
                    continue  # already in special folder
                if any(p.name in ("saves", "states") for p in candidate.parents):
                    continue  # inside saves/{platform}/ or states/{platform}/
                if str(candidate) in known_paths:
                    continue  # it's a ROM we know about
                if candidate.name.lower() not in _known_bios_names:
                    continue  # unknown .bin — don't touch it silently
                bios_target = bios_dir / candidate.name
                if candidate == bios_target:
                    continue
                moves_bios.append({"source": str(candidate), "target": str(bios_target), "filename": candidate.name})
                if not dry_run:
                    try:
                        bios_dir.mkdir(parents=True, exist_ok=True)
                        if not bios_target.exists():
                            _shutil.move(str(candidate), str(bios_target))
                    except Exception as exc:
                        errors.append(f"BIOS {candidate.name}: {exc}")

            total_preview = (moves_roms + moves_saves + moves_bios)[:40]
            self._send_json({
                "dry_run": dry_run,
                "moves_roms": len(moves_roms),
                "moves_saves": len(moves_saves),
                "moves_bios": len(moves_bios),
                "errors": errors,
                "preview": total_preview if dry_run else [],
            })

        def _handle_sync(self, data: dict) -> None:
            dry_run = data.get("dry_run", True)
            with _job_lock:
                if _jobs["sync"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["sync"] = True

            def run() -> None:
                # QoL-13: tray icon status while syncing
                import rom_manager.web.server as _srv13
                if _srv13._tray_instance:
                    _srv13._tray_instance.set_status("Sincronizando…")
                try:
                    from rom_manager.sync.rclone_transport import RcloneTransport
                    from rom_manager.sync.save_syncer import sync_saves
                    from pathlib import Path as _Path

                    sources = config.sync_sources
                    if not sources:
                        _job_results["sync"] = {
                            "error": "No hay fuentes de sync configuradas. "
                                     "Añade [[sync.sources]] en config.toml."
                        }
                        return

                    # QoL-11: pre-sync backup (creates a timestamped ZIP of all saves)
                    if not dry_run and config.pre_sync_backup and config.library_root:
                        try:
                            from rom_manager.backup.save_backup import create_saves_zip
                            _zip_dest = config.data_dir / "saves-backup"
                            create_saves_zip(
                                saves_dirs=[_Path(str(config.library_root))],
                                save_extensions=set(config.save_extensions),
                                output_dir=_zip_dest,
                            )
                        except Exception as _bk_exc:
                            _logger.warning("Pre-sync backup failed (non-fatal): %s", _bk_exc)

                    transport = RcloneTransport(rclone=config.rclone_binary)
                    all_results = []
                    for source in sources:
                        saves_dir = _Path(source.local_dir)
                        if not saves_dir.exists():
                            all_results.append({
                                "name": source.name,
                                "local_dir": source.local_dir,
                                "remote": source.remote,
                                "error": f"Directorio no encontrado: {source.local_dir}",
                                "uploaded": 0, "downloaded": 0,
                                "up_to_date": 0, "conflicts": 0, "errors": 0,
                                "decisions": [],
                            })
                            continue
                        # sync_all=True → pass empty tuple so list_local_saves includes all files
                        exts = tuple() if source.sync_all else config.save_extensions
                        try:
                            _bk_root = config.data_dir if config.backup_saves_enabled else None
                            from rom_manager.sync.delta_cache import DeltaCache as _DeltaCache
                            _delta = _DeltaCache(config.data_dir) if not dry_run else None
                            result, decisions = sync_saves(
                                saves_dir,
                                source.remote,
                                transport=transport,
                                repository=repository,
                                save_extensions=exts,
                                dry_run=dry_run,
                                backup_root=_bk_root,
                                backup_keep_n=config.backup_saves_keep_n,
                                delta_cache=_delta,
                            )
                            all_results.append({
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
                                    for d in decisions if d.action != "up_to_date"
                                ],
                            })
                        except Exception as exc:
                            all_results.append({
                                "name": source.name,
                                "local_dir": source.local_dir,
                                "remote": source.remote,
                                "error": str(exc),
                                "uploaded": 0, "downloaded": 0,
                                "up_to_date": 0, "conflicts": 0, "errors": 0,
                                "decisions": [],
                            })

                    _up   = sum(r.get("uploaded",   0) for r in all_results)
                    _down = sum(r.get("downloaded", 0) for r in all_results)
                    _errs = sum(r.get("errors",     0) for r in all_results)
                    _job_results["sync"] = {
                        "dry_run": dry_run,
                        "sources": all_results,
                        # Aggregated totals
                        "uploaded":   _up,
                        "downloaded": _down,
                        "up_to_date": sum(r.get("up_to_date", 0) for r in all_results),
                        "conflicts":  sum(r.get("conflicts",  0) for r in all_results),
                        "errors":     _errs,
                    }
                    if not dry_run and config.notify_desktop:
                        from rom_manager.utils.notifier import notify
                        _parts = []
                        if _up:   _parts.append(f"{_up} subidos")
                        if _down: _parts.append(f"{_down} descargados")
                        if not _parts: _parts.append("Todo al día")
                        _body = ", ".join(_parts)
                        if _errs: _body += f" ({_errs} errores)"
                        notify("Retro Vault — Sync completado", _body)
                    # QoL-13: tray icon status after sync
                    if not dry_run:
                        _total_conflicts = sum(r.get("conflicts", 0) for r in all_results)
                        if _errs:
                            _srv13._tray_instance and _srv13._tray_instance.set_status(f"✗ Sync: {_errs} errores")
                        elif _total_conflicts:
                            _srv13._tray_instance and _srv13._tray_instance.set_status(f"⚠ Conflictos: {_total_conflicts}")
                        else:
                            _ts = _utc_now_str()[:16].replace("T", " ")
                            _srv13._tray_instance and _srv13._tray_instance.set_status(f"Sync OK {_ts}")
                except Exception as exc:
                    _job_results["sync"] = {"error": str(exc)}
                    import rom_manager.web.server as _srv13e
                    _srv13e._tray_instance and _srv13e._tray_instance.set_status("✗ Error en sync")
                finally:
                    with _job_lock:
                        _jobs["sync"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started", "dry_run": dry_run})

        def _handle_convert_chd(self, data: dict) -> None:
            source_path_str = data.get("source_path", "").strip()
            if not source_path_str:
                self._send_json({"error": "source_path is required"})
                return
            dry_run = data.get("dry_run", True)
            delete_source = data.get("delete_source", False)

            with _job_lock:
                if _jobs["convert_chd"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["convert_chd"] = True

            def run() -> None:
                _chd_cancel.clear()
                try:
                    from rom_manager.converters.chd_converter import (
                        find_cue_files, convert_to_chd, parse_bins_from_cue,
                        ConversionResult, ConversionSummary,
                    )
                    source = Path(source_path_str).resolve()
                    cue_files = find_cue_files(source)
                    total = len(cue_files)
                    _chd_progress.update({"current": 0, "total": total, "current_file": ""})

                    summary = ConversionSummary()
                    for idx, cue_path in enumerate(cue_files, 1):
                        if _chd_cancel.is_set():
                            break
                        _chd_progress.update({"current": idx, "total": total, "current_file": cue_path.name})
                        chd_path = cue_path.with_suffix(".chd")
                        bin_paths = parse_bins_from_cue(cue_path)
                        if dry_run:
                            if chd_path.exists():
                                summary.skipped += 1
                                summary.results.append(ConversionResult(
                                    cue_path=cue_path, chd_path=chd_path, bin_paths=bin_paths,
                                    success=False, error="Output .chd already exists — would skip."))
                            else:
                                # Validate that all .bin files referenced by the .cue exist
                                missing_bins = [b for b in bin_paths if not b.exists()]
                                if missing_bins:
                                    summary.failed += 1
                                    summary.results.append(ConversionResult(
                                        cue_path=cue_path, chd_path=chd_path, bin_paths=bin_paths,
                                        success=False,
                                        error="Bin file(s) not found: " + ", ".join(b.name for b in missing_bins)))
                                else:
                                    summary.converted += 1
                                    summary.results.append(ConversionResult(
                                        cue_path=cue_path, chd_path=chd_path, bin_paths=bin_paths,
                                        success=True))
                        else:
                            result = convert_to_chd(cue_path, chdman=config.chdman, delete_source=delete_source)
                            summary.results.append(result)
                            if result.success:
                                summary.converted += 1
                                # B6-2: mark .cue as disc_auxiliary immediately so it stops
                                # appearing as a duplicate alongside the new .chd (no scan needed)
                                try:
                                    cue_str = str(cue_path.resolve())
                                    with repository.connect() as _dc:
                                        _dc.execute(
                                            "UPDATE games SET set_type = 'disc_auxiliary' WHERE source_path = ?",
                                            (cue_str,),
                                        )
                                        _dc.commit()
                                except Exception:
                                    pass  # non-critical — next scan will fix it via set_detector
                            elif result.error and "already exists" in result.error:
                                summary.skipped += 1
                            else:
                                summary.failed += 1

                    _job_results["convert_chd"] = {
                        "dry_run": dry_run,
                        "converted": summary.converted,
                        "skipped": summary.skipped,
                        "failed": summary.failed,
                        "cancelled": _chd_cancel.is_set(),
                        "results": [
                            {
                                "cue": r.cue_path.name,
                                "chd": r.chd_path.name,
                                "success": r.success,
                                "error": r.error or "",
                                "bin_count": len(r.bin_paths),  # B5-1: per-game bin count
                            }
                            for r in summary.results
                        ],
                    }
                except Exception as exc:
                    _job_results["convert_chd"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _chd_progress.clear()
                        _jobs["convert_chd"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started", "dry_run": dry_run})

        def _handle_convert_cso(self, data: dict) -> None:
            source_path_str = data.get("source_path", "").strip()
            if not source_path_str:
                self._send_json({"error": "source_path is required"})
                return
            delete_source = data.get("delete_source", False)

            with _job_lock:
                if _jobs["convert_cso"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["convert_cso"] = True

            def run() -> None:
                import subprocess
                _cso_cancel.clear()
                try:
                    source = Path(source_path_str).resolve()
                    maxcso_path = str(config.project_root / "tools" / "maxcso.exe")

                    # Find all .cso and .zso files recursively
                    cso_files = list(source.rglob("*.cso")) + list(source.rglob("*.zso"))

                    # Filter out MAME/arcade ROMs — they are native ZIP format
                    arcade_platforms = {"arcade", "fbneo", "mame", "neogeo"}
                    def _is_arcade(p: Path) -> bool:
                        return any(plat in str(p).lower() for plat in arcade_platforms)

                    cso_files = [c for c in cso_files if not _is_arcade(c)]
                    total = len(cso_files)
                    _cso_progress.update({"current": 0, "total": total, "current_file": ""})

                    converted = 0
                    skipped = 0
                    failed = 0
                    results = []

                    for idx, cso_path in enumerate(cso_files, 1):
                        if _cso_cancel.is_set():
                            break
                        _cso_progress.update({"current": idx, "total": total, "current_file": cso_path.name})
                        iso_path = cso_path.with_suffix(".iso")

                        # Check if output already exists
                        if iso_path.exists():
                            skipped += 1
                            results.append({
                                "file": cso_path.name,
                                "success": False,
                                "error": "Output .iso already exists"
                            })
                            continue

                        # Run maxcso --decompress
                        try:
                            r = subprocess.run(
                                [maxcso_path, "--decompress", f"--output={iso_path}", str(cso_path)],
                                capture_output=True, timeout=300,
                            )
                            if r.returncode == 0:
                                converted += 1
                                results.append({
                                    "file": cso_path.name,
                                    "success": True,
                                    "error": None,
                                })
                                # Delete source if requested
                                if delete_source:
                                    cso_path.unlink()
                            else:
                                failed += 1
                                err = (r.stderr or b"").decode(errors="replace").strip()
                                results.append({
                                    "file": cso_path.name,
                                    "success": False,
                                    "error": err or "maxcso failed with non-zero exit"
                                })
                        except FileNotFoundError:
                            failed += 1
                            results.append({
                                "file": cso_path.name,
                                "success": False,
                                "error": f"maxcso not found: {maxcso_path}"
                            })
                        except subprocess.TimeoutExpired:
                            failed += 1
                            results.append({
                                "file": cso_path.name,
                                "success": False,
                                "error": "Timeout (>300s)"
                            })
                        except Exception as e:
                            failed += 1
                            results.append({
                                "file": cso_path.name,
                                "success": False,
                                "error": str(e)
                            })

                    _job_results["convert_cso"] = {
                        "converted": converted,
                        "skipped": skipped,
                        "failed": failed,
                        "cancelled": _cso_cancel.is_set(),
                        "results": results,
                    }
                except Exception as exc:
                    _job_results["convert_cso"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _cso_progress.clear()
                        _jobs["convert_cso"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started"})

        def _handle_save_config(self, data: dict) -> None:
            from rom_manager.config import write_config_toml, load_config
            allowed = {
                "library.library_root", "library.anbernic_root", "sync.remote",
                "screenscraper.user", "screenscraper.pass",
                "screenscraper.dev_id", "screenscraper.dev_pass",
                "tools.chdman", "tools.adb",
                "retroachievements.api_key",
                "sync.auto_sync_enabled", "sync.auto_sync_direction",
                "sync.auto_sync_android_path", "sync.conflict_policy",
                "inbox.path", "inbox.target_root",
                "inbox.auto_process", "inbox.delete_source",
                "android.device_name",
                "web.host",
                "launchers.retroarch",
                "backup.saves_enabled", "backup.saves_keep_n",
                "notifications.desktop",
            }
            updates = {k: v for k, v in data.items() if k in allowed}
            if not updates:
                self._send_json({"error": "No recognised fields to update"})
                return
            write_config_toml(config.project_root, updates)
            # Reload in-memory config so changes take effect without restart
            global _auto_sync_enabled
            new_cfg = load_config(config.project_root)
            config.library_root = new_cfg.library_root
            config.anbernic_root = new_cfg.anbernic_root
            config.device_name = new_cfg.device_name
            config.rclone_remote = new_cfg.rclone_remote
            config.screenscraper_user = new_cfg.screenscraper_user
            config.screenscraper_pass = new_cfg.screenscraper_pass
            config.screenscraper_dev_id = new_cfg.screenscraper_dev_id
            config.screenscraper_dev_pass = new_cfg.screenscraper_dev_pass
            config.chdman = new_cfg.chdman
            config.adb = new_cfg.adb
            config.ra_api_key = new_cfg.ra_api_key
            config.auto_sync_enabled = new_cfg.auto_sync_enabled
            config.auto_sync_direction = new_cfg.auto_sync_direction
            config.auto_sync_android_path = new_cfg.auto_sync_android_path
            config.conflict_policy = new_cfg.conflict_policy
            config.inbox_path = new_cfg.inbox_path
            config.inbox_target_root = new_cfg.inbox_target_root
            config.inbox_auto_process = new_cfg.inbox_auto_process
            config.inbox_delete_source = new_cfg.inbox_delete_source
            config.sync_sources = new_cfg.sync_sources
            config.web_host = new_cfg.web_host
            config.retroarch_path = new_cfg.retroarch_path
            config.launcher_cores = new_cfg.launcher_cores
            config.backup_saves_enabled = new_cfg.backup_saves_enabled
            config.backup_saves_keep_n = new_cfg.backup_saves_keep_n
            config.pre_sync_backup = new_cfg.pre_sync_backup
            config.notify_desktop = new_cfg.notify_desktop
            _auto_sync_enabled = new_cfg.auto_sync_enabled
            self._send_json({"saved": list(updates.keys())})

        def _handle_auto_sync_save(self, data: dict) -> None:
            """Save auto-sync settings to config.toml and update in-memory config."""
            from rom_manager.config import write_config_toml, load_config
            global _auto_sync_enabled

            updates: dict = {}
            if "sync.auto_sync_direction" in data:
                updates["sync.auto_sync_direction"] = data["sync.auto_sync_direction"]
                config.auto_sync_direction = data["sync.auto_sync_direction"]
            if "sync.auto_sync_android_path" in data:
                updates["sync.auto_sync_android_path"] = data["sync.auto_sync_android_path"]
                config.auto_sync_android_path = data["sync.auto_sync_android_path"]
            if "sync.conflict_policy" in data:
                updates["sync.conflict_policy"] = data["sync.conflict_policy"]
                config.conflict_policy = data["sync.conflict_policy"]
            if "sync.auto_sync_enabled" in data:
                val = bool(data["sync.auto_sync_enabled"])
                updates["sync.auto_sync_enabled"] = val
                config.auto_sync_enabled = val
                _auto_sync_enabled = val

            if updates:
                write_config_toml(config.project_root, updates)

            self._send_json({"saved": list(updates.keys()), "enabled": _auto_sync_enabled})

        def _handle_cleanup_zips(self, data: dict) -> None:
            import os
            source_path_str = data.get("source_path", "").strip()
            if not source_path_str:
                self._send_json({"error": "source_path is required"})
                return
            source = Path(source_path_str).resolve()
            deleted = failed = 0
            freed_bytes = 0
            for zp in source.rglob("*.zip"):
                try:
                    freed_bytes += zp.stat().st_size
                    os.remove(zp)
                    deleted += 1
                except OSError:
                    failed += 1
            self._send_json({"deleted": deleted, "failed": failed, "freed_bytes": freed_bytes})

        def _handle_cleanup_cue_bin(self, data: dict) -> None:
            import os
            source_path_str = data.get("source_path", "").strip()
            if not source_path_str:
                self._send_json({"error": "source_path is required"})
                return
            source = Path(source_path_str).resolve()
            deleted = failed = skipped = 0
            freed_bytes = 0
            for cue in source.rglob("*.cue"):
                chd = cue.with_suffix(".chd")
                if not chd.exists():
                    skipped += 1
                    continue
                # Delete the .cue and all .bin files it references
                from rom_manager.converters.chd_converter import parse_bins_from_cue
                bins = parse_bins_from_cue(cue)
                for f in [cue, *bins]:
                    try:
                        freed_bytes += f.stat().st_size
                        os.remove(f)
                        deleted += 1
                    except OSError:
                        failed += 1
            self._send_json({"deleted": deleted, "failed": failed, "skipped": skipped, "freed_bytes": freed_bytes})

        def _handle_extract_zip(self, data: dict) -> None:
            source_path_str = data.get("source_path", "").strip()
            if not source_path_str:
                self._send_json({"error": "source_path is required"})
                return
            dry_run = bool(data.get("dry_run", True))
            delete_source = bool(data.get("delete_source", False))

            with _job_lock:
                if _jobs["extract_zip"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["extract_zip"] = True

            def run() -> None:
                _zip_cancel.clear()
                try:
                    from rom_manager.converters.zip_extractor import find_zip_files, extract_zip
                    source = Path(source_path_str).resolve()
                    zip_files = find_zip_files(source)
                    total = len(zip_files)
                    _zip_progress.update({"current": 0, "total": total, "current_file": ""})
                    extracted = skipped = failed = disc_sets = 0
                    results = []
                    for idx, zp in enumerate(zip_files, 1):
                        if _zip_cancel.is_set():
                            break
                        try:
                            rel = str(zp.relative_to(source))
                        except ValueError:
                            rel = zp.name
                        _zip_progress.update({"current": idx, "total": total, "current_file": rel})
                        r = extract_zip(zp, dry_run=dry_run, delete_source=delete_source)
                        if r.is_disc_set:
                            disc_sets += 1
                            skipped += 1
                        elif r.skipped_reason:
                            skipped += 1
                        elif r.error:
                            failed += 1
                        else:
                            extracted += 1
                        results.append({
                            "zip": rel,
                            "success": r.success,
                            "skipped_reason": r.skipped_reason,
                            "is_disc_set": r.is_disc_set,
                            "error": r.error,
                            "extracted": [f.name for f in r.extracted_files],
                        })
                    _job_results["extract_zip"] = {
                        "dry_run": dry_run,
                        "extracted": extracted,
                        "skipped": skipped,
                        "failed": failed,
                        "disc_sets": disc_sets,
                        "cancelled": _zip_cancel.is_set(),
                        "results": results,
                    }
                except Exception as exc:
                    _job_results["extract_zip"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _zip_progress.clear()
                        _jobs["extract_zip"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started", "dry_run": dry_run})

        def _handle_generate_m3u(self, data: dict) -> None:
            source_path_str = data.get("source_path", "").strip()
            if not source_path_str:
                self._send_json({"error": "source_path is required"})
                return
            dry_run = bool(data.get("dry_run", True))
            from rom_manager.utils.m3u_generator import generate_m3u_playlists
            source = Path(source_path_str).resolve()
            summary = generate_m3u_playlists(source, dry_run=dry_run)
            self._send_json({
                "dry_run": dry_run,
                "created": summary.created,
                "skipped": summary.skipped,
                "groups": [
                    {
                        "base_name": g.base_name,
                        "discs": [d.name for d in g.discs],
                        "m3u": g.m3u_path.name,
                    }
                    for g in summary.groups
                ],
            })

        def _handle_verify_multidisc(self, data: dict) -> None:
            source_path_str = data.get("source_path", "").strip()
            if not source_path_str:
                self._send_json({"error": "source_path is required"})
                return
            from rom_manager.utils.multidisc_verifier import verify_multidisc
            source = Path(source_path_str).resolve()
            summary = verify_multidisc(source, repository)
            self._send_json({
                "groups_ok": summary.groups_ok,
                "groups_with_issues": summary.groups_with_issues,
                "issues": [
                    {"base_name": i.base_name, "issue_type": i.issue_type,
                     "detail": i.detail, "platform": i.platform}
                    for i in summary.issues
                ],
            })

        def _handle_delete_orphaned_saves(self, data: dict) -> None:
            import os
            paths = data.get("paths", [])
            if not paths:
                self._send_json({"error": "paths list is required"})
                return
            deleted = failed = 0
            freed_bytes = 0
            for p in paths:
                try:
                    size = Path(p).stat().st_size if Path(p).exists() else 0
                    os.remove(p)
                    deleted += 1
                    freed_bytes += size
                except OSError:
                    failed += 1
            self._send_json({"deleted": deleted, "failed": failed, "freed_bytes": freed_bytes})

        def _handle_move_orphaned_save(self, data: dict) -> None:
            """Move an orphaned save file to sit alongside a matched ROM."""
            import shutil
            save_path = data.get("save_path", "").strip()
            game_path = data.get("game_path", "").strip()
            if not save_path or not game_path:
                self._send_json({"error": "save_path and game_path are required"})
                return
            save_file = Path(save_path)
            game_file = Path(game_path)
            if not save_file.exists():
                self._send_json({"error": f"Save file not found: {save_path}"})
                return
            if not game_file.parent.exists():
                self._send_json({"error": f"Game directory not found: {game_file.parent}"})
                return
            target = game_file.parent / (game_file.stem + save_file.suffix)
            if target.exists():
                self._send_json({"error": f"Target already exists: {target.name}"})
                return
            try:
                shutil.move(str(save_file), str(target))
            except OSError as exc:
                self._send_json({"error": str(exc)})
                return
            self._send_json({"moved": str(target), "from": save_path})

        def _handle_move_orphaned_saves_to_archive(self, data: dict) -> None:
            """Move orphaned save files to _huerfanos/ folder."""
            import shutil
            paths = data.get("paths", [])
            library_root = data.get("library_root", "").strip()
            if not paths:
                self._send_json({"error": "paths list is required"})
                return
            if not library_root:
                self._send_json({"error": "library_root is required"})
                return

            archive_dir = Path(library_root) / "_huerfanos"
            try:
                archive_dir.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                self._send_json({"error": f"Could not create _huerfanos folder: {exc}"})
                return

            moved = failed = 0
            moved_bytes = 0
            for p in paths:
                try:
                    src = Path(p)
                    if not src.exists():
                        failed += 1
                        continue
                    size = src.stat().st_size
                    # Get filename with extension
                    target = archive_dir / src.name
                    # Handle duplicates
                    counter = 1
                    stem = target.stem
                    suffix = target.suffix
                    while target.exists():
                        target = archive_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    shutil.move(str(src), str(target))
                    moved += 1
                    moved_bytes += size
                except OSError:
                    failed += 1

            self._send_json({
                "moved": moved,
                "failed": failed,
                "moved_bytes": moved_bytes,
                "archive_dir": str(archive_dir)
            })

        def _handle_inbox_upload(self, content_type: str, body: bytes) -> None:
            """Save multipart file-upload(s) directly to inbox_path."""
            import re as _re
            bm = _re.search(r"boundary=([^\s;]+)", content_type)
            if not bm:
                self._send_error(400, "Missing multipart boundary")
                return
            inbox_path = config.inbox_path
            if not inbox_path:
                self._send_json({"error": "inbox_path not configured"})
                return
            inbox_dir = Path(inbox_path)
            inbox_dir.mkdir(parents=True, exist_ok=True)
            boundary = ("--" + bm.group(1)).encode()
            saved: list[str] = []
            errors: list[str] = []
            for part in body.split(boundary)[1:]:
                if part[:2] == b"--":
                    break
                if part.startswith(b"\r\n"):
                    part = part[2:]
                if b"\r\n\r\n" not in part:
                    continue
                hdr_bytes, file_data = part.split(b"\r\n\r\n", 1)
                if file_data.endswith(b"\r\n"):
                    file_data = file_data[:-2]
                hdr_text = hdr_bytes.decode("utf-8", errors="replace")
                fm = _re.search(r'filename="([^"]+)"', hdr_text)
                if not fm:
                    continue
                fname = Path(fm.group(1)).name  # strip any dir components
                if not fname:
                    continue
                try:
                    (inbox_dir / fname).write_bytes(file_data)
                    saved.append(fname)
                except OSError as exc:
                    errors.append(f"{fname}: {exc}")
            self._send_json({"saved": saved, "errors": errors, "count": len(saved)})

        def _handle_health_check(self, data: dict) -> None:
            def run() -> None:
                _health_cancel.clear()
                try:
                    from rom_manager.utils.health_checker import check_library_health

                    def progress_cb(current: int, total: int, filename: str) -> None:
                        _health_progress.update({"current": current, "total": total, "current_file": filename})

                    summary = check_library_health(repository, progress_cb=progress_cb, cancel_event=_health_cancel)
                    _job_results["health_check"] = {
                        "ok": summary.ok,
                        "corrupted": summary.corrupted,
                        "missing": summary.missing,
                        "cancelled": _health_cancel.is_set(),
                        "issues": [
                            {"source_path": r.source_path, "status": r.status,
                             "stored_sha1": r.stored_sha1[:12], "computed_sha1": r.computed_sha1[:12] if r.computed_sha1 else "",
                             "platform": r.platform, "canonical_title": r.canonical_title}
                            for r in summary.results
                        ],
                    }
                    _write_health_schedule(config, ok=summary.ok,
                                           corrupted=summary.corrupted, missing=summary.missing)
                    if not _health_cancel.is_set() and config.notify_desktop:
                        from rom_manager.utils.notifier import notify
                        if summary.corrupted or summary.missing:
                            notify(
                                "Retro Vault — Health Check",
                                f"⚠ {summary.corrupted} corruptos, {summary.missing} desaparecidos — revisa la pestaña Tools",
                            )
                        else:
                            notify("Retro Vault — Health Check", f"✓ {summary.ok} ROMs verificados, sin problemas")
                except Exception as exc:
                    _job_results["health_check"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _health_progress.clear()
                        _jobs["health_check"] = False

            self._send_json(_start_job("health_check", run))

        def _handle_scrape(self, data: dict) -> None:
            with _job_lock:
                if _jobs["scrape"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["scrape"] = True

            platform = data.get("platform") or None
            download_images = bool(data.get("images", False))
            limit = int(data.get("limit", 0))

            def run() -> None:
                _scrape_cancel.clear()
                try:
                    from rom_manager.scraper.screenscraper import ScreenScraperClient, download_image
                    from rom_manager.scraper.platform_ids import get_system_id
                    from rom_manager.scanner.rom_scanner import utc_now

                    if not config.screenscraper_user:
                        _job_results["scrape"] = {"error": "screenscraper credentials not configured"}
                        return

                    client = ScreenScraperClient(
                        user=config.screenscraper_user,
                        password=config.screenscraper_pass,
                        dev_id=config.screenscraper_dev_id,
                        dev_password=config.screenscraper_dev_pass,
                    )
                    games = repository.get_games_for_scraping(platform=platform)
                    if limit:
                        games = games[:limit]
                    total = len(games)
                    found = skipped = network_errors = 0
                    failed_games: list[str] = []
                    _RETRY_DELAYS = [5, 15, 30]
                    _scrape_progress.update({"current": 0, "total": total, "found": 0, "network_errors": 0, "current_game": ""})
                    # B6-3: use connect() + per-game commit instead of batch()
                    # batch() commits once at exit and rolls back everything on exception —
                    # a single network error mid-scrape was losing all metadata scraped so far.
                    with repository.connect() as conn:
                        for idx, game in enumerate(games, 1):
                            if _scrape_cancel.is_set():
                                break
                            _scrape_progress.update({
                                "current": idx,
                                "total": total,
                                "found": found,
                                "network_errors": network_errors,
                                "current_game": game["original_filename"],
                            })
                            sys_id = get_system_id(game["platform"])
                            # B6-4: retry with backoff on transient network errors
                            result = None
                            last_error = ""
                            for attempt in range(3):
                                if _scrape_cancel.is_set():
                                    break
                                try:
                                    result = client.search(
                                        crc32=game["crc32"],
                                        md5=game["md5"],
                                        sha1=game["sha1"],
                                        filename=game["original_filename"],
                                        size_bytes=game["size_bytes"],
                                        system_id=sys_id,
                                    )
                                    if result is None:
                                        # Fallback: search by cleaned name (no hash)
                                        name_hint = game.get("canonical_title") or game["original_filename"]
                                        result = client.search_by_name(name_hint, system_id=sys_id)
                                    last_error = ""
                                    break  # success
                                except PermissionError:
                                    raise  # fatal: wrong credentials or quota exceeded
                                except Exception as exc:
                                    last_error = str(exc)
                                    if attempt < 2 and not _scrape_cancel.is_set():
                                        time.sleep(_RETRY_DELAYS[attempt])
                            if _scrape_cancel.is_set():
                                break
                            # Persist quota snapshot from client
                            if client.last_quota:
                                _ss_last_quota.update(client.last_quota)
                            if last_error:
                                network_errors += 1
                                failed_games.append(game["original_filename"])
                                continue
                            if result is None:
                                skipped += 1
                                continue
                            box_art_path = ""
                            screenshot_path = ""
                            wheel_path = ""
                            if download_images:
                                _src_parent = Path(game["source_path"]).parent
                                _stem = Path(game["original_filename"]).stem
                                if result.box_art_url:
                                    _ext = ".png" if ".png" in result.box_art_url.lower() else ".jpg"
                                    _dest = _src_parent / "media" / "images" / f"{_stem}{_ext}"
                                    try:
                                        download_image(result.box_art_url, _dest)
                                        box_art_path = str(_dest)
                                    except Exception:
                                        pass
                                if result.screenshot_url:  # B6-7
                                    _ext = ".png" if ".png" in result.screenshot_url.lower() else ".jpg"
                                    _dest = _src_parent / "media" / "screenshots" / f"{_stem}{_ext}"
                                    try:
                                        download_image(result.screenshot_url, _dest)
                                        screenshot_path = str(_dest)
                                    except Exception:
                                        pass
                                if result.wheel_url:  # B6-7
                                    _ext = ".png" if ".png" in result.wheel_url.lower() else ".jpg"
                                    _dest = _src_parent / "media" / "wheels" / f"{_stem}{_ext}"
                                    try:
                                        download_image(result.wheel_url, _dest)
                                        wheel_path = str(_dest)
                                    except Exception:
                                        pass
                            repository.upsert_metadata(
                                game_id=game["id"],
                                ss_game_id=result.ss_game_id,
                                title=result.title, year=result.year,
                                genre=result.genre, publisher=result.publisher,
                                developer=result.developer, description=result.description,
                                rating=result.rating, box_art_url=result.box_art_url,
                                box_art_path=box_art_path,
                                screenshot_path=screenshot_path,
                                wheel_path=wheel_path,
                                scraped_at=utc_now(),
                                connection=conn,
                            )
                            conn.commit()  # B6-3: persist immediately — don't lose on interruption
                            found += 1
                    # Auto-export gamelists to ROM dir (alongside ROMs — ES-DE reads them there)
                    _gamelist_written: list[dict] = []
                    try:
                        from rom_manager.scraper.gamelist_writer import write_gamelist
                        _out_root = Path(config.library_root) if config.library_root else None
                        if _out_root:
                            _plat_filter = platform  # may be None (all)
                            _plats = repository.get_scraped_platform_summary()
                            if _plat_filter:
                                _plats = [p for p in _plats if p["platform"] == _plat_filter]
                            for _plat in _plats:
                                if _plat["scraped"] == 0:
                                    continue
                                _entries = repository.get_metadata_for_platform(_plat["platform"])
                                if not _entries:
                                    continue
                                _slug = _ES_PLATFORM_FOLDERS.get(_plat["platform"], _plat["platform"].lower().replace(" ", "").replace("/", "_"))
                                _pdir = _out_root / _slug
                                _pdir.mkdir(parents=True, exist_ok=True)
                                write_gamelist(_pdir, _entries)
                                _gamelist_written.append(_plat["platform"])
                    except Exception:
                        pass  # gamelist export is best-effort, don't fail the scrape result

                    _job_results["scrape"] = {
                        "total": total, "found": found, "skipped": skipped,
                        "network_errors": network_errors,
                        "failed_games": failed_games[:20],
                        "cancelled": _scrape_cancel.is_set(),
                        "gamelists_written": _gamelist_written,
                    }
                except Exception as exc:
                    _job_results["scrape"] = {"error": str(exc)}
                finally:
                    with _job_lock:
                        _scrape_progress.clear()
                        _jobs["scrape"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started"})

        def _handle_export_gamelists(self, data: dict) -> None:
            from rom_manager.scraper.gamelist_writer import write_gamelist
            output_root = Path(data.get("output_dir") or "").resolve() if data.get("output_dir") else config.library_root
            if output_root is None:
                self._send_json({"error": "library_root not configured"})
                return
            platform_filter = data.get("platform") or None
            platforms = repository.get_scraped_platform_summary()
            if platform_filter:
                platforms = [p for p in platforms if p["platform"] == platform_filter]

            written = []
            for plat in platforms:
                if plat["scraped"] == 0:
                    continue
                entries = repository.get_metadata_for_platform(plat["platform"])
                if not entries:
                    continue
                slug = _ES_PLATFORM_FOLDERS.get(plat["platform"], plat["platform"].lower().replace(" ", "").replace("/", "_"))
                platform_dir = Path(output_root) / slug
                platform_dir.mkdir(parents=True, exist_ok=True)
                # ES-DE reads gamelist.xml from the ROM directory (relative paths) — no secondary copy needed
                out = write_gamelist(platform_dir, entries)
                written.append({
                    "platform": plat["platform"],
                    "path": str(out),
                    "entries": len(entries),
                })
            self._send_json({"written": written})

        def _handle_delete_duplicate(self, data: dict) -> None:
            import os
            from pathlib import Path as _Path
            game_id = data.get("game_id")
            source_path = data.get("source_path", "").strip()
            if not game_id or not source_path:
                self._send_json({"error": "game_id y source_path son obligatorios"})
                return
            p = _Path(source_path)
            if p.exists():
                try:
                    os.remove(str(p))
                except Exception as exc:
                    self._send_json({"error": f"No se pudo eliminar el archivo: {type(exc).__name__}: {exc}"})
                    return
            # Clean up DB even if file was already missing
            try:
                repository.delete_game(int(game_id))
            except Exception as exc:
                self._send_json({"error": f"Archivo eliminado pero error en BD: {type(exc).__name__}: {exc}"})
                return
            self._send_json({"deleted": source_path})

        def _handle_delete_all_duplicates(self) -> None:
            import os
            import logging as _logging
            from pathlib import Path as _Path
            _dup_log = _logging.getLogger(__name__)
            groups = repository.get_duplicate_groups()
            deleted = 0
            failed = 0
            freed_bytes = 0
            errors: list[str] = []
            for group in groups:
                for entry in group.entries[1:]:
                    p = _Path(entry.source_path)
                    if not p.exists():
                        try:
                            repository.delete_game(entry.id)
                            deleted += 1
                        except Exception as exc:
                            failed += 1
                            _dup_log.warning("Could not remove DB entry for missing file %s: %s", p, exc)
                            if len(errors) < 20:
                                errors.append(f"{p.name}: DB error — {type(exc).__name__}: {exc}")
                        continue
                    file_deleted = False
                    try:
                        os.remove(str(p))
                        file_deleted = True
                    except Exception as exc:
                        failed += 1
                        msg = f"{p.name}: no se pudo eliminar el archivo — {type(exc).__name__}: {exc}"
                        _dup_log.warning("Could not delete duplicate file %s: %s", p, exc)
                        if len(errors) < 20:
                            errors.append(msg)
                        continue
                    try:
                        repository.delete_game(entry.id)
                        deleted += 1
                        freed_bytes += entry.size_bytes
                    except Exception as exc:
                        # File was deleted from disk but DB update failed
                        failed += 1
                        msg = f"{p.name}: archivo eliminado pero error en BD — {type(exc).__name__}: {exc}"
                        _dup_log.warning("File deleted but DB update failed for %s: %s", p, exc)
                        if len(errors) < 20:
                            errors.append(msg)
            self._send_json({"deleted": deleted, "failed": failed, "freed_bytes": freed_bytes, "errors": errors})

        def _handle_ra_check(self, data: dict) -> None:
            api_key = data.get("api_key", "").strip() or config.ra_api_key
            if not api_key:
                self._send_json({"error": "RetroAchievements API key not configured"})
                return
            if _start_ra_check_bg(api_key):
                self._send_json({"status": "started"})
            else:
                self._send_json({"status": "already_running"})

        def _handle_cable_sync(self, data: dict) -> None:
            import os
            import shutil

            pc_path_str       = data.get("pc_path", "").strip()
            anbernic_path_str = data.get("anbernic_path", "").strip()
            what              = data.get("what", ["saves"])   # ["roms"], ["saves"], or both
            direction         = data.get("direction", "pc_to_anbernic")
            dry_run           = bool(data.get("dry_run", True))
            skip_sha1_dups    = bool(data.get("skip_sha1_dups", False))
            skip_existing     = bool(data.get("skip_existing", False))
            safe_mode         = bool(data.get("safe_mode", True))
            use_adb           = bool(data.get("use_adb", False))
            adb_serial        = data.get("adb_serial", "").strip()
            android_path      = data.get("android_path", "/storage/emulated/0").strip()

            if not pc_path_str:
                self._send_json({"error": "pc_path is required"})
                return
            if use_adb and not adb_serial:
                self._send_json({"error": "adb_serial is required when use_adb is true"})
                return
            if not use_adb and not anbernic_path_str:
                self._send_json({"error": "anbernic_path is required"})
                return

            with _job_lock:
                if _jobs["cable_sync"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["cable_sync"] = True

            def run() -> None:
                _cable_cancel.clear()
                _log_file = None
                try:
                    import time as _time
                    from pathlib import PurePosixPath
                    import datetime as _dt
                    pc_root   = Path(pc_path_str)
                    save_exts = frozenset(config.save_extensions)

                    # Open persistent operation log
                    log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                    _log_file = open(log_path, "a", encoding="utf-8", buffering=1)
                    _ts0 = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    _log_file.write(
                        f"\n=== Cable Sync {_ts0} | direction={direction} dry_run={dry_run} safe_mode={safe_mode} ===\n"
                    )

                    def _log(tag: str, src: str, dst: str = "", note: str = "") -> None:
                        ts = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%H:%M:%S")
                        _log_file.write(f"[{ts}] [{tag:5s}] {src}{(' -> ' + dst) if dst else ''}{(' | ' + note) if note else ''}\n")

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
                        # B7-3: assets (media/ images) and gamelists
                        if "assets" in what and p.suffix.lower() in _ASSET_EXTS:
                            # Only sync files inside a media/ subdirectory
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

                    copied = skipped = errors = sha1_skipped = safe_mode_skipped = 0
                    copied_bytes = 0
                    details: list[dict] = []

                    _sync_start_time = _time.monotonic()
                    _last_speed_update = _time.monotonic()
                    _last_speed_bytes = 0

                    def _update_progress(file_name: str = "") -> None:
                        nonlocal _last_speed_update, _last_speed_bytes
                        now = _time.monotonic()
                        dt = now - _last_speed_update
                        speed = 0.0
                        if dt >= 0.5:
                            speed = (copied_bytes - _last_speed_bytes) / dt
                            _last_speed_update = now
                            _last_speed_bytes = copied_bytes
                        elif _cable_progress.get("speed_bps") is not None:
                            speed = _cable_progress.get("speed_bps", 0.0)
                        _cable_progress.update({
                            "copied": copied,
                            "bytes_copied": copied_bytes,
                            "speed_bps": speed,
                            "current_file": file_name,
                        })

                    def _copy(src: Path, dst: Path, arrow: str) -> None:
                        nonlocal copied, skipped, errors, copied_bytes, safe_mode_skipped
                        if _cable_cancel.is_set():
                            return
                        try:
                            src_stat = src.stat()
                            size = src_stat.st_size
                            # Safe mode: never overwrite existing destination
                            if safe_mode and dst.exists():
                                safe_mode_skipped += 1
                                skipped += 1
                                _log("SAFE", str(src), str(dst), "destino existe — omitido por modo seguro")
                                if len(details) < 300:
                                    details.append({"file": "SAFE", "path": str(src.name)})
                                return
                            # Skip if destination already exists with same size
                            if skip_existing and dst.exists():
                                try:
                                    if dst.stat().st_size == size:
                                        skipped += 1
                                        _log("SKIP", str(src), str(dst), "mismo tamaño")
                                        if len(details) < 300:
                                            details.append({"file": "EXISTS", "path": str(src.name)})
                                        return
                                except OSError:
                                    pass
                            if not dry_run:
                                dst.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(src, dst)
                            _log("COPY" if not dry_run else "DRYRUN", str(src), str(dst))
                            copied += 1
                            copied_bytes += size
                            if len(details) < 300:
                                details.append({"file": arrow, "path": str(src.name)})
                            _update_progress(src.name)
                        except OSError as exc:
                            errors += 1
                            _log("ERROR", str(src), str(dst), str(exc))
                            if len(details) < 300:
                                details.append({"file": f"ERROR: {exc}", "path": str(src.name)})

                    # ── ADB mode ──────────────────────────────────────────────
                    if use_adb:
                        from rom_manager.sync.adb_transport import AdbTransport
                        transport = AdbTransport(config.adb, adb_serial)

                        def _adb_copy_to_pc(adb_info, rel_posix: str, arrow: str) -> None:
                            nonlocal copied, errors, copied_bytes
                            if _cable_cancel.is_set():
                                return
                            name = PurePosixPath(adb_info.android_path).name
                            local_dst = pc_root / Path(rel_posix.replace("/", os.sep))
                            try:
                                size = transport.pull(adb_info.android_path, local_dst, dry_run=dry_run)
                                _log("ADB←" if not dry_run else "DRY←", adb_info.android_path, str(local_dst))
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
                            if _cable_cancel.is_set():
                                return
                            android_dst = android_path.rstrip("/") + "/" + rel_posix
                            try:
                                size = transport.push(local_src, android_dst, dry_run=dry_run)
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

                        _cable_progress.update({"copied": 0, "current_file": "Listando archivos en el dispositivo…"})
                        ab_adb_files = transport.ls_recursive(android_path)
                        # Compute total bytes from ADB listing
                        try:
                            _pre_files = sum(1 for info in ab_adb_files if _wanted_name(PurePosixPath(info.android_path).name))
                            _pre_total = sum(info.size for info in ab_adb_files if _wanted_name(PurePosixPath(info.android_path).name))
                            _cable_progress.update({"bytes_total": _pre_total, "total_files": _pre_files, "copied": 0, "bytes_copied": 0, "speed_bps": 0.0})
                        except Exception:
                            pass
                        android_prefix = android_path.rstrip("/") + "/"

                        if direction == "pc_to_anbernic":
                            for src in _iter_files(pc_root):
                                if _cable_cancel.is_set():
                                    break
                                if not _wanted(src):
                                    continue
                                rel = src.relative_to(pc_root)
                                rel_posix = rel.as_posix()
                                _adb_copy_to_device(src, rel_posix, "→ ADB")

                        elif direction == "anbernic_to_pc":
                            use_sha1 = skip_sha1_dups and "roms" in what
                            if use_sha1:
                                from rom_manager.hashing.hash_calculator import calculate_hashes
                            for info in ab_adb_files:
                                if _cable_cancel.is_set():
                                    break
                                name = PurePosixPath(info.android_path).name
                                if not _wanted_name(name):
                                    continue
                                rel_posix = info.android_path.removeprefix(android_prefix)
                                if use_sha1 and _cat_name(name) == "rom":
                                    local_tmp = pc_root / Path(rel_posix.replace("/", os.sep))
                                    _update_progress(f"[SHA1] {name}")
                                    # For SHA1 check we need the file locally; pull to temp first
                                    import tempfile
                                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(name).suffix) as tf:
                                        tmp_path = Path(tf.name)
                                    try:
                                        transport.pull(info.android_path, tmp_path, dry_run=False)
                                        from rom_manager.hashing.hash_calculator import calculate_hashes
                                        h = calculate_hashes(tmp_path)
                                        # SHA1 check against PC repository (destination)
                                        if repository.sha1_exists(h.sha1):
                                            sha1_skipped += 1
                                            skipped += 1
                                            if len(details) < 300:
                                                details.append({"file": "DUP", "path": name})
                                            tmp_path.unlink(missing_ok=True)
                                            continue
                                        # Move temp file to final destination
                                        dst = pc_root / Path(rel_posix.replace("/", os.sep))
                                        if not dry_run:
                                            dst.parent.mkdir(parents=True, exist_ok=True)
                                            shutil.move(str(tmp_path), dst)
                                        else:
                                            tmp_path.unlink(missing_ok=True)
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

                        elif direction == "newest":
                            # Build index of device files by relative posix path
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
                                if _cable_cancel.is_set():
                                    break
                                pc_f   = pc_index.get(rel_posix)
                                ab_inf = ab_index.get(rel_posix)
                                if pc_f and ab_inf:
                                    if pc_f.stat().st_mtime > ab_inf.mtime:
                                        _adb_copy_to_device(pc_f, rel_posix, "→ ADB (PC más reciente)")
                                    elif ab_inf.mtime > pc_f.stat().st_mtime:
                                        _adb_copy_to_pc(ab_inf, rel_posix, "← ADB (Anbernic más reciente)")
                                    else:
                                        skipped += 1
                                elif pc_f:
                                    _adb_copy_to_device(pc_f, rel_posix, "→ ADB (solo en PC)")
                                elif ab_inf:
                                    _adb_copy_to_pc(ab_inf, rel_posix, "← ADB (solo en Anbernic)")

                    # ── Filesystem mode ───────────────────────────────────────
                    else:
                        ab_root = Path(anbernic_path_str)

                        # Pre-scan to get total bytes (best effort)
                        try:
                            _pre_total = 0
                            _pre_files = 0
                            if direction == "pc_to_anbernic":
                                for _f in _iter_files(pc_root):
                                    if _wanted(_f):
                                        try: _pre_total += _f.stat().st_size
                                        except OSError: pass
                                        _pre_files += 1
                            elif direction == "anbernic_to_pc":
                                for _f in _iter_files(ab_root):
                                    if _wanted(_f):
                                        try: _pre_total += _f.stat().st_size
                                        except OSError: pass
                                        _pre_files += 1
                            elif direction == "newest":
                                for _f in _iter_files(pc_root):
                                    if _wanted(_f):
                                        try: _pre_total += _f.stat().st_size
                                        except OSError: pass
                                        _pre_files += 1
                                for _f in _iter_files(ab_root):
                                    if _wanted(_f):
                                        try: _pre_total += _f.stat().st_size
                                        except OSError: pass
                                        _pre_files += 1
                            _cable_progress.update({"bytes_total": _pre_total, "total_files": _pre_files, "copied": 0, "bytes_copied": 0, "speed_bps": 0.0})
                        except Exception:
                            pass

                        if direction == "pc_to_anbernic":
                            for src in _iter_files(pc_root):
                                if _cable_cancel.is_set():
                                    break
                                if not _wanted(src):
                                    continue
                                rel = src.relative_to(pc_root)
                                dst = ab_root / rel
                                _copy(src, dst, "→ Anbernic")

                        elif direction == "anbernic_to_pc":
                            use_sha1 = skip_sha1_dups and "roms" in what
                            if use_sha1:
                                from rom_manager.hashing.hash_calculator import calculate_hashes
                            for src in _iter_files(ab_root):
                                if _cable_cancel.is_set():
                                    break
                                if not _wanted(src):
                                    continue
                                try:
                                    rel = src.relative_to(ab_root)
                                except ValueError:
                                    continue
                                if use_sha1 and _category(src) == "rom":
                                    _update_progress(f"[SHA1] {src.name}")
                                    try:
                                        h = calculate_hashes(src)
                                        # Check PC repository (destination) for SHA1 duplicates
                                        if repository.sha1_exists(h.sha1):
                                            sha1_skipped += 1
                                            skipped += 1
                                            if len(details) < 300:
                                                details.append({"file": "DUP", "path": src.name})
                                            continue
                                    except OSError:
                                        pass
                                dst = pc_root / rel
                                _copy(src, dst, "← PC")

                        elif direction == "newest":
                            pc_files: dict[Path, Path] = {}
                            for f in _iter_files(pc_root):
                                if _wanted(f):
                                    pc_files[f.relative_to(pc_root)] = f

                            ab_files: dict[Path, Path] = {}
                            for f in _iter_files(ab_root):
                                if _wanted(f):
                                    try:
                                        ab_files[f.relative_to(ab_root)] = f
                                    except ValueError:
                                        pass

                            all_rels = sorted(set(pc_files) | set(ab_files), key=lambda p: str(p))
                            for rel in all_rels:
                                if _cable_cancel.is_set():
                                    break
                                pc_f = pc_files.get(rel)
                                ab_f = ab_files.get(rel)
                                if pc_f and ab_f:
                                    pc_mt = pc_f.stat().st_mtime
                                    ab_mt = ab_f.stat().st_mtime
                                    if pc_mt > ab_mt:
                                        _copy(pc_f, ab_root / rel, "→ Anbernic (PC más reciente)")
                                    elif ab_mt > pc_mt:
                                        _copy(ab_f, pc_root / rel, "← PC (Anbernic más reciente)")
                                    else:
                                        skipped += 1
                                elif pc_f:
                                    _copy(pc_f, ab_root / rel, "→ Anbernic (solo en PC)")
                                elif ab_f:
                                    _copy(ab_f, pc_root / rel, "← PC (solo en Anbernic)")

                    _ts1 = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    _log_file.write(
                        f"=== Fin {_ts1} | copied={copied} skipped={skipped} safe_skipped={safe_mode_skipped} errors={errors} cancelled={_cable_cancel.is_set()} ===\n"
                    )
                    # D8-6: count actual files on disk for both sides (best effort)
                    _pc_file_count = 0
                    _ab_file_count = 0
                    if not dry_run and not use_adb:
                        try:
                            _ab_r = Path(anbernic_path_str)
                            for _ff in _iter_files(pc_root):
                                if _wanted(_ff):
                                    _pc_file_count += 1
                        except Exception:
                            pass
                        try:
                            for _ff in _iter_files(_ab_r):
                                if _wanted(_ff):
                                    _ab_file_count += 1
                        except Exception:
                            pass
                    _job_results["cable_sync"] = {
                        "dry_run": dry_run,
                        "direction": direction,
                        "use_adb": use_adb,
                        "copied": copied,
                        "skipped": skipped,
                        "sha1_skipped": sha1_skipped,
                        "safe_mode_skipped_overwrites": safe_mode_skipped,
                        "errors": errors,
                        "copied_bytes": copied_bytes,
                        "cancelled": _cable_cancel.is_set(),
                        "details": details,
                        "pc_file_count": _pc_file_count,
                        "ab_file_count": _ab_file_count,
                    }
                    if not dry_run and not _cable_cancel.is_set() and config.notify_desktop:
                        from rom_manager.utils.notifier import notify
                        _via = "ADB" if use_adb else "SD"
                        _body = f"{copied} archivos copiados vía {_via}"
                        if errors: _body += f" ({errors} errores)"
                        notify("Retro Vault — Cable Sync completado", _body)
                except Exception as exc:
                    _job_results["cable_sync"] = {"error": str(exc)}
                finally:
                    if _log_file is not None:
                        try:
                            _log_file.close()
                        except Exception:
                            pass
                    with _job_lock:
                        _cable_progress.clear()
                        _jobs["cable_sync"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started", "dry_run": dry_run})

        # ── Two-DB migration ───────────────────────────────────────────────────

        def _handle_migrate_split_db(self) -> None:
            """One-time migration: move Android-path games from PC repo to Android repo.

            Reads all games in PC repository whose source_path does NOT start with
            library_root, moves their records to the Android repository, and deletes
            them from the PC repository.  Safe to run multiple times (idempotent).
            """
            lib_root = str(config.library_root or "").lower().rstrip("/\\")
            if not lib_root:
                self._send_json({"error": "library_root not configured — cannot determine which paths are Android"})
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

                # Insert Android games into android repo, delete from PC repo
                with _repo_android.batch() as _android_conn:
                    for row in android_rows:
                        try:
                            _repo_android.upsert_game(
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

                # Delete migrated games from PC repo
                with repository.batch() as _pc_conn:
                    for row in android_rows:
                        _pc_conn.execute("DELETE FROM games WHERE source_path = ?", (row["source_path"],))

                # Also migrate saves
                with repository.connect() as _conn:
                    save_rows = _conn.execute(
                        "SELECT original_path, relative_parent, extension, size_bytes, created_at "
                        "FROM saves"
                    ).fetchall()

                android_saves = [r for r in save_rows if not r["original_path"].lower().startswith(lib_root)]
                if android_saves:
                    with _repo_android.batch() as _android_conn:
                        for row in android_saves:
                            try:
                                _repo_android.upsert_save(
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
                            _pc_conn.execute("DELETE FROM saves WHERE original_path = ?", (row["original_path"],))

            except Exception as exc:
                self._send_json({"error": str(exc)})
                return

            self._send_json({
                "migrated_games": migrated,
                "errors": errors[:20],
                "pc_db": str(config.database_path),
                "android_db": str(config.database_path_android),
            })

        # ── D8-3: RA conflict resolver ─────────────────────────────────────────

        def _handle_apply_ra_conflicts(self, data: dict) -> None:
            """Resolve plan conflicts by keeping RA winner and moving loser to _descartados/."""
            import shutil as _shutil
            from rom_manager.planner.operation_planner import FormatOptions as _FO
            opts = _FO()
            plan = build_plan(repository, opts)
            resolved = 0
            skipped_no_ra = 0
            errors: list[str] = []
            cache_dir_exists = (config.project_root / ".rommgr" / "ra_cache").exists()
            cache_files_exist = cache_dir_exists and any((config.project_root / ".rommgr" / "ra_cache").iterdir()) if cache_dir_exists else False
            for op in plan.conflicts:
                if not op.source_path.exists():
                    continue
                # Look up both source and target in repository by MD5/path
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

                # Check RA support for both
                from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id
                from rom_manager.retroachievements.ra_client import _parse_game_list as _pgl
                import json as _json
                cache_dir = config.project_root / ".rommgr" / "ra_cache"
                plat = op.game.platform or ""
                console_id = get_ra_console_id(plat)
                src_ra = tgt_ra = -1
                if console_id:
                    cache_file = cache_dir / f"ra_hashes_{console_id}.json"
                    if cache_file.exists():
                        try:
                            _hash_lib = _pgl(_json.loads(cache_file.read_text(encoding="utf-8")))
                            if src_md5:
                                src_entry = _hash_lib.get(src_md5.lower())
                                src_ra = src_entry.achievements if src_entry else -1
                            if tgt_md5:
                                tgt_entry = _hash_lib.get(tgt_md5.lower())
                                tgt_ra = tgt_entry.achievements if tgt_entry else -1
                        except Exception:
                            pass

                if src_ra <= 0 and tgt_ra <= 0:
                    skipped_no_ra += 1
                    continue

                # Decide which to keep: higher RA wins; if equal keep source
                if tgt_ra > src_ra:
                    loser_path = op.source_path
                else:
                    loser_path = op.target_path  # target exists but source would replace it

                discard_dir = loser_path.parent / "_descartados"
                try:
                    discard_dir.mkdir(parents=True, exist_ok=True)
                    dest = discard_dir / loser_path.name
                    if not dest.exists():
                        _shutil.move(str(loser_path), dest)
                    else:
                        loser_path.unlink()
                    # Remove from DB
                    with repository.connect() as _c:
                        _c.execute("DELETE FROM games WHERE source_path = ?", (str(loser_path),))
                        _c.execute("PRAGMA optimize")
                    resolved += 1
                except Exception as exc:
                    errors.append(f"{loser_path.name}: {exc}")

            self._send_json({
                "resolved": resolved,
                "skipped_no_ra": skipped_no_ra,
                "errors": errors[:10],
                "no_cache": not cache_files_exist,
            })

        # ── D8-4: RA version duplicate discard ─────────────────────────────────

        def _handle_ra_duplicate_discard(self, data: dict) -> None:
            import shutil as _shutil
            import logging as _logging
            _disc_log = _logging.getLogger(__name__)
            source_path = data.get("path", "").strip()
            if not source_path:
                self._send_json({"error": "path required"})
                return
            p = Path(source_path)
            if not p.exists():
                # Already gone — remove from DB if present
                with repository.connect() as _c:
                    _c.execute("DELETE FROM games WHERE source_path = ?", (source_path,))
                    _c.commit()
                self._send_json({"ok": True, "note": "file already missing; removed from DB"})
                return
            discard_dir = p.parent / "_descartados"
            dest: Path | None = None
            moved = False
            try:
                discard_dir.mkdir(parents=True, exist_ok=True)
                dest = discard_dir / p.name
                # Step 1: move/delete the file
                permanently_deleted = False
                if dest.exists():
                    # Destination already occupied — delete the source directly (no rollback possible)
                    p.unlink()
                    dest = None
                    permanently_deleted = True
                else:
                    _shutil.move(str(p), dest)
                    moved = True
                # Step 2: delete from DB — if this fails, roll back the file move
                with repository.connect() as _c:
                    _c.execute("DELETE FROM games WHERE source_path = ?", (source_path,))
                    _c.commit()
            except Exception as exc:
                if moved and dest is not None and dest.exists():
                    try:
                        _shutil.move(str(dest), str(p))
                        _disc_log.warning("RA discard rollback: restored %s after DB error", p.name)
                    except Exception as rb_exc:
                        _disc_log.error("RA discard rollback FAILED for %s: %s", p.name, rb_exc)
                        self._send_json({"error": f"DB error AND rollback failed — {p.name} may be lost: {exc} | rollback: {rb_exc}"})
                        return
                elif permanently_deleted:
                    _disc_log.error("File %s was permanently deleted but DB delete failed: %s", p.name, exc)
                    self._send_json({"error": f"File was deleted but DB update failed — stale entry will be removed on next scan: {exc}"})
                    return
                self._send_json({"error": str(exc)})
                return
            self._send_json({"ok": True})

        def _handle_ra_duplicate_discard_all(self) -> None:
            """Discard ALL entries without RA support from version-duplicate groups."""
            import shutil as _shutil
            import logging as _logging
            _dall_log = _logging.getLogger(__name__)
            ra_dups = _build_ra_duplicates(repository, config)
            # Pass through the note (e.g. "no RA cache") so the frontend can show it
            if ra_dups.get("note"):
                self._send_json({"discarded": 0, "failed": 0, "errors": [], "note": ra_dups["note"]})
                return
            discarded = 0
            failed = 0
            errors: list[str] = []
            for group in ra_dups.get("groups", []):
                for entry in group.get("entries", []):
                    if entry.get("ra_supported"):
                        continue
                    src_path_str = entry.get("source_path", "")
                    if not src_path_str:
                        continue
                    p = Path(src_path_str)
                    discard_dir = p.parent / "_descartados"
                    dest_file: Path | None = None
                    moved = False
                    permanently_deleted = False
                    try:
                        discard_dir.mkdir(parents=True, exist_ok=True)
                        if p.exists():
                            dest_file = discard_dir / p.name
                            if dest_file.exists():
                                p.unlink()
                                dest_file = None
                                permanently_deleted = True
                            else:
                                _shutil.move(str(p), dest_file)
                                moved = True
                        # DB delete only after file is safely moved
                        with repository.connect() as _c:
                            _c.execute("DELETE FROM games WHERE source_path = ?", (src_path_str,))
                            _c.commit()
                        discarded += 1
                    except Exception as exc:
                        failed += 1
                        # Roll back file move if DB failed
                        if moved and dest_file is not None and dest_file.exists():
                            try:
                                _shutil.move(str(dest_file), str(p))
                                _dall_log.warning("RA discard-all rollback: restored %s", p.name)
                                errors.append(f"{p.name}: DB error (file restored) — {exc}")
                            except Exception as rb_exc:
                                _dall_log.error("RA discard-all rollback FAILED for %s: %s", p.name, rb_exc)
                                errors.append(f"{p.name}: DB error AND rollback failed — file may be lost | {exc} | {rb_exc}")
                        elif permanently_deleted:
                            _dall_log.error("File %s permanently deleted but DB delete failed: %s", p.name, exc)
                            errors.append(f"{p.name}: deleted but DB not updated (stale entry — will be removed on next scan)")
                        else:
                            errors.append(f"{p.name}: {exc}")
            self._send_json({
                "discarded": discarded,
                "failed": failed,
                "errors": errors[:10],
            })

        def _handle_ra_discard_no_support(self) -> None:
            """Bulk-discard all games that have NO RA support at all (status='no_support').

            Reads the stored `no_support_entries` from the last RA check result.
            Moves files to `<parent>/_descartados/` and removes from DB.
            """
            import shutil as _shutil
            import logging as _logging
            _dns_log = _logging.getLogger(__name__)

            result = _job_results.get("ra_check")
            if not result:
                self._send_json({"error": "No RA check result available. Run RA check first."})
                return
            entries = result.get("no_support_entries", [])
            if not entries:
                self._send_json({"discarded": 0, "failed": 0, "errors": [], "note": "No games to discard."})
                return

            discarded = 0
            failed = 0
            errors: list[str] = []
            for entry in entries:
                src_path_str = entry.get("source_path", "")
                if not src_path_str:
                    continue
                p = Path(src_path_str)
                discard_dir = p.parent / "_descartados"
                dest_file: Path | None = None
                moved = False
                permanently_deleted = False
                try:
                    discard_dir.mkdir(parents=True, exist_ok=True)
                    if p.exists():
                        dest_file = discard_dir / p.name
                        if dest_file.exists():
                            p.unlink()
                            permanently_deleted = True
                        else:
                            _shutil.move(str(p), dest_file)
                            moved = True
                    # DB delete only after file is safely moved
                    with repository.connect() as _c:
                        _c.execute("DELETE FROM games WHERE source_path = ?", (src_path_str,))
                    discarded += 1
                except Exception as exc:
                    failed += 1
                    if moved and dest_file is not None and dest_file.exists():
                        try:
                            _shutil.move(str(dest_file), str(p))
                            _dns_log.warning("RA discard-no-support rollback: restored %s", p.name)
                            errors.append(f"{p.name}: DB error (file restored) — {exc}")
                        except Exception as rb_exc:
                            _dns_log.error("RA discard-no-support rollback FAILED for %s: %s", p.name, rb_exc)
                            errors.append(f"{p.name}: DB error AND rollback failed — file may be lost | {exc} | {rb_exc}")
                    elif permanently_deleted:
                        _dns_log.error("File %s permanently deleted but DB delete failed: %s", p.name, exc)
                        errors.append(f"{p.name}: deleted from disk but DB error — {exc}")
                    else:
                        errors.append(f"{p.name}: {exc}")
            self._send_json({
                "discarded": discarded,
                "failed": failed,
                "errors": errors[:10],
            })

        def _handle_resolve_duplicate_ra(self, data: dict) -> None:
            """B1-4: Resolve title-based duplicates by keeping the one with RA support."""
            import shutil as _shutil
            import logging as _logging
            _b14_log = _logging.getLogger(__name__)
            keep_path = data.get("keep_path", "").strip()
            discard_paths = data.get("discard_paths", [])
            if not keep_path or not discard_paths:
                self._send_json({"error": "keep_path and discard_paths required"})
                return

            discarded = 0
            failed = 0
            errors = []

            for src_path_str in discard_paths:
                p = Path(src_path_str)
                if not p.exists():
                    # Already gone — remove from DB
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
                        _shutil.move(str(p), str(dest_file))
                    # Delete from DB
                    with repository.connect() as _c:
                        _c.execute("DELETE FROM games WHERE source_path = ?", (src_path_str,))
                        _c.commit()
                    discarded += 1
                except Exception as exc:
                    failed += 1
                    _b14_log.error("Failed to discard duplicate %s: %s", p.name, exc)
                    if dest_file and dest_file.exists():
                        try:
                            _shutil.move(str(dest_file), str(p))
                        except Exception:
                            pass
                    errors.append(f"{p.name}: {exc}")

            self._send_json({
                "discarded": discarded,
                "failed": failed,
                "errors": errors[:10],
            })

        def _handle_apply(self, data: dict) -> None:
            with _job_lock:
                if _jobs["apply"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["apply"] = True

            fmt = data.get("format_opts", {})
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

                    save_exts = frozenset(config.save_extensions)
                    # Use the correct repo for the apply operation
                    _apply_repo = _get_repo(source_root or "")
                    plan = build_plan(_apply_repo, opts, keep_both=keep_both)
                    pending_ops = plan.pending
                    if source_root:
                        root_lower = source_root.lower()
                        pending_ops = [op for op in pending_ops if str(op.source_path).lower().startswith(root_lower)]

                    total = len(pending_ops)
                    renamed = failed = skipped = saves_renamed = 0
                    skip_details: list[str] = []
                    timestamp = utc_now()
                    _apply_progress.update({"current": 0, "total": total, "current_file": ""})

                    for idx, op in enumerate(pending_ops, 1):
                        _apply_progress.update({"current": idx, "total": total, "current_file": op.source_path.name})
                        if not op.source_path.exists():
                            skipped += 1
                            skip_details.append(f"{op.source_path.name}: source not found (outdated DB entry)")
                            continue
                        try:
                            _bk = config.data_dir if config.backup_saves_enabled else None
                            # Ensure target directory exists (needed for disc subfolders)
                            op.target_path.parent.mkdir(parents=True, exist_ok=True)
                            if op.source_path.suffix.lower() in {".cue", ".gdi"}:
                                from rom_manager.renamer.file_renamer import move_disc_set_to_subfolder
                                outcome = move_disc_set_to_subfolder(
                                    op.source_path, op.target_path, save_exts,
                                    backup_root=_bk,
                                    backup_keep_n=config.backup_saves_keep_n,
                                )
                            else:
                                outcome = rename_rom_with_saves(
                                    op.source_path, op.target_path, save_exts,
                                    backup_root=_bk,
                                    backup_keep_n=config.backup_saves_keep_n,
                                )
                        except Exception as exc:
                            skipped += 1
                            skip_details.append(f"{op.source_path.name}: unexpected error — {exc}")
                            continue
                        if outcome.success:
                            # Route the DB update to the same repo where the file lives
                            _op_repo = _get_repo(str(op.source_path))
                            _op_repo.apply_rename(
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

                    from rom_manager.scanner.rom_scanner import utc_now as _now
                    _job_results["apply"] = {
                        "renamed": renamed,
                        "failed": failed,
                        "skipped": skipped,
                        "saves_renamed": saves_renamed,
                        "conflicts": len(plan.conflicts),
                        "skip_details": skip_details[:20],
                        "error_details": skip_details[:50],  # D8-2: full error list for UI
                        "result_ts": _now(),
                    }
                except Exception as exc:
                    _job_results["apply"] = {"error": str(exc), "result_ts": ""}
                finally:
                    with _job_lock:
                        _apply_progress.clear()
                        _jobs["apply"] = False

            threading.Thread(target=run, daemon=True).start()
            self._send_json({"status": "started"})

        def _handle_setup_run(self, data: dict) -> None:
            """Launch the first-time setup wizard pipeline as a background job."""
            lib_root = data.get("library_root", "").strip() or (str(config.library_root) if config.library_root else "")
            if not lib_root:
                self._send_json({"error": "library_root is required"})
                return
            # Persist paths to config.toml so they survive restarts
            from rom_manager.config import write_config_toml, load_config
            updates: dict = {}
            if not config.library_root or str(config.library_root) != lib_root:
                updates["library.library_root"] = lib_root
            android_root = data.get("android_root", "").strip()
            if android_root and (not config.anbernic_root or str(config.anbernic_root) != android_root):
                updates["library.anbernic_root"] = android_root
            if updates:
                write_config_toml(config.project_root, updates)
                new_cfg = load_config(config.project_root)
                config.library_root = new_cfg.library_root
                if android_root:
                    config.anbernic_root = new_cfg.anbernic_root
                config.device_name = new_cfg.device_name
            with _job_lock:
                if _jobs["setup"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["setup"] = True
            _setup_progress.clear()
            _job_results.pop("setup", None)
            options = {
                "clean_junk": bool(data.get("clean_junk", False)),
                "extract_zips": bool(data.get("extract_zips", True)),
                "scan": bool(data.get("scan", True)),
                "match": bool(data.get("match", True)),
            }
            threading.Thread(
                target=_run_setup_pipeline,
                args=(lib_root, options, repository, config),
                daemon=True,
            ).start()
            self._send_json({"status": "started"})

        def _handle_inbox_run(self, data: dict) -> None:
            inbox_path_str = data.get("path", "").strip() or config.inbox_path
            if not inbox_path_str:
                self._send_json({"error": "path is required (or set inbox.path in config.toml)"})
                return
            target_root_str = data.get("target_root", "").strip() or config.inbox_target_root or (str(config.library_root) if config.library_root else "")
            delete_source = bool(data.get("delete_source", config.inbox_delete_source))

            with _job_lock:
                if _jobs["inbox"]:
                    self._send_json({"status": "already_running"})
                    return
                _jobs["inbox"] = True

            threading.Thread(
                target=_run_inbox_pipeline,
                args=(inbox_path_str, target_root_str, delete_source, repository, config),
                daemon=True,
            ).start()
            self._send_json({"status": "started"})

        # ── Helpers ──────────────────────────────────────────────────────────

        def _send(
            self,
            code: int,
            content_type: str,
            body: bytes,
            extra_headers: dict[str, str] | None = None,
        ) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra_headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, data: object) -> None:
            body = _json_response(data)
            self._send(200, "application/json; charset=utf-8", body)

    return Handler


# ── Health-check scheduler (S37-1) ────────────────────────────────────────────

_HEALTH_CHECK_INTERVAL_DAYS = 7


def _health_schedule_path(config: "AppConfig") -> "Path":
    return config.data_dir / "health_schedule.json"


def _read_health_schedule(config: "AppConfig") -> dict:
    """Return the stored schedule dict, or empty dict if not found."""
    import json as _json
    p = _health_schedule_path(config)
    try:
        return _json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_health_schedule(config: "AppConfig", *, ok: int, corrupted: int, missing: int) -> None:
    """Persist health check completion time and summary."""
    import json as _json
    import datetime as _dt
    data = {
        "last_run_at": _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_ok": ok,
        "last_corrupted": corrupted,
        "last_missing": missing,
    }
    p = _health_schedule_path(config)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(_json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        _logger.debug("Could not write health schedule: %s", exc)


def _health_scheduler_loop(config: "AppConfig", get_repo_fn) -> None:  # type: ignore[type-arg]
    """Daemon: trigger an automatic health check once per week."""
    import datetime as _dt
    import time as _time

    _time.sleep(60)  # let the server finish startup before first check

    while True:
        try:
            schedule = _read_health_schedule(config)
            last_run_raw = schedule.get("last_run_at")
            overdue = True
            if last_run_raw:
                try:
                    last_run = _dt.datetime.fromisoformat(last_run_raw.replace("Z", "+00:00"))
                    elapsed = (_dt.datetime.now(tz=_dt.timezone.utc) - last_run).days
                    overdue = elapsed >= _HEALTH_CHECK_INTERVAL_DAYS
                except Exception:
                    pass

            if overdue:
                # Only run if no health check is already in progress
                with _job_lock:
                    already = _jobs.get("health_check", False)
                if not already:
                    repository = get_repo_fn()
                    _logger.info("Scheduled health check starting (overdue by %s days)", "?" if not last_run_raw else elapsed)

                    def _scheduled_run(_repo=repository) -> None:
                        _health_cancel.clear()
                        try:
                            from rom_manager.utils.health_checker import check_library_health

                            def _prog(current: int, total: int, filename: str) -> None:
                                _health_progress.update({"current": current, "total": total, "current_file": filename})

                            summary = check_library_health(_repo, progress_cb=_prog, cancel_event=_health_cancel)
                            _job_results["health_check"] = {
                                "ok": summary.ok,
                                "corrupted": summary.corrupted,
                                "missing": summary.missing,
                                "cancelled": _health_cancel.is_set(),
                                "auto": True,
                                "issues": [
                                    {"source_path": r.source_path, "status": r.status,
                                     "stored_sha1": r.stored_sha1[:12],
                                     "computed_sha1": r.computed_sha1[:12] if r.computed_sha1 else "",
                                     "platform": r.platform, "canonical_title": r.canonical_title}
                                    for r in summary.results
                                ],
                            }
                            _write_health_schedule(config, ok=summary.ok,
                                                   corrupted=summary.corrupted, missing=summary.missing)
                            if not _health_cancel.is_set() and config.notify_desktop:
                                from rom_manager.utils.notifier import notify
                                if summary.corrupted or summary.missing:
                                    notify("Retro Vault — Health Check",
                                           f"⚠ {summary.corrupted} corruptos, {summary.missing} desaparecidos")
                                else:
                                    notify("Retro Vault — Health Check",
                                           f"✓ {summary.ok} ROMs verificados, sin problemas")
                        except Exception as exc:
                            _logger.error("Scheduled health check error: %s", exc)
                        finally:
                            with _job_lock:
                                _health_progress.clear()
                                _jobs["health_check"] = False

                    _start_job("health_check", _scheduled_run)

        except Exception as exc:
            _logger.debug("Health scheduler error: %s", exc)

        _time.sleep(3600)  # check every hour


def serve(
    *,
    host: str,
    port: int,
    repository: LibraryRepository,
    config: AppConfig,
    repository_android: LibraryRepository | None = None,
    tray: bool = False,
) -> None:
    global _auto_sync_enabled, _tray_instance
    _auto_sync_enabled = config.auto_sync_enabled

    # S34-1: reload platform tables with user override if present
    from rom_manager.detection.platform_detector import reload_platforms
    user_platforms = config.data_dir / "platforms.toml"
    reload_platforms(user_platforms if user_platforms.exists() else None)

    if config.auto_sync_enabled:
        t = threading.Thread(
            target=_auto_sync_loop,
            args=(config, lambda: repository),
            daemon=True,
        )
        t.name = "auto-sync-daemon"
        t.start()
        _logger.info("Auto-sync daemon started (polling every 10 s)")

    # SD card daemon always runs (checks config.anbernic_root internally)
    sd_t = threading.Thread(
        target=_sd_card_sync_loop,
        args=(config, lambda: repository),
        daemon=True,
    )
    sd_t.name = "sd-sync-daemon"
    sd_t.start()
    _logger.info("SD card sync daemon started (polling every 8 s)")

    # Inbox watcher daemon (runs only when inbox_auto_process is True)
    def _inbox_watcher_with_repo() -> None:
        import time as _time
        while True:
            try:
                _time.sleep(30)
                if not config.inbox_path or not config.inbox_auto_process:
                    _inbox_watcher_status.update({"watching": False, "last_check": None, "pending_files": 0})
                    continue
                inbox = Path(config.inbox_path).resolve()
                if not inbox.exists():
                    _inbox_watcher_status.update({"watching": True, "last_check": _watcher_now(), "pending_files": 0})
                    continue
                pending: list[Path] = [
                    e for e in inbox.iterdir()
                    if e.is_file() and not e.name.startswith(".") and not e.name.startswith("_")
                ]
                _inbox_watcher_status.update({
                    "watching": True,
                    "last_check": _watcher_now(),
                    "pending_files": len(pending),
                })
                if pending:
                    with _job_lock:
                        already = _jobs.get("inbox", False)
                    if not already:
                        _logger.info("Inbox watcher: %d files detected, launching pipeline", len(pending))
                        with _job_lock:
                            _jobs["inbox"] = True
                        target_root_str = config.inbox_target_root or (str(config.library_root) if config.library_root else "")
                        threading.Thread(
                            target=_run_inbox_pipeline,
                            args=(config.inbox_path, target_root_str, config.inbox_delete_source, repository, config),
                            daemon=True,
                        ).start()
            except Exception as exc:
                _logger.debug("Inbox watcher error: %s", exc)

    tw = threading.Thread(target=_inbox_watcher_with_repo, daemon=True)
    tw.name = "inbox-watcher-daemon"
    tw.start()
    _logger.info("Inbox watcher daemon started")

    # Health check scheduler (S37-1)
    ht = threading.Thread(
        target=_health_scheduler_loop,
        args=(config, lambda: repository),
        daemon=True,
    )
    ht.name = "health-check-scheduler"
    ht.start()
    _logger.info("Health check scheduler started (interval: %d days)", _HEALTH_CHECK_INTERVAL_DAYS)

    # S39-3: system tray icon (Windows only)
    if tray:
        import sys as _sys
        if _sys.platform == "win32":
            try:
                from rom_manager.utils.tray_icon import TrayIcon

                def _on_sync_from_tray() -> None:
                    import rom_manager.web.server as _srv
                    sources = config.sync_sources
                    if not sources:
                        return
                    from rom_manager.sync.rclone_transport import RcloneTransport
                    from rom_manager.sync.save_syncer import sync_saves
                    from pathlib import Path as _Path
                    transport = RcloneTransport(rclone=config.rclone_binary)
                    for src in sources:
                        saves_dir = _Path(src.local_dir)
                        if not saves_dir.exists():
                            continue
                        try:
                            sync_saves(
                                saves_dir, src.remote,
                                transport=transport,
                                repository=repository,
                                save_extensions=config.save_extensions,
                                dry_run=False,
                            )
                        except Exception:
                            pass
                    if _tray_instance:
                        _tray_instance.set_status(f"Sync OK {_utc_now_str()[:16]}")
                        _tray_instance.show_balloon("Retro Vault", "Sync completado.")

                def _on_quit_from_tray() -> None:
                    import threading as _threading
                    _threading.Thread(target=httpd.shutdown, daemon=True).start()

                _tray_instance = TrayIcon(
                    port=port,
                    on_sync=_on_sync_from_tray,
                    on_quit=_on_quit_from_tray,
                )
                _tray_instance.start()
                _logger.info("Tray icon started")
            except Exception as _te:
                _logger.warning("Could not start tray icon: %s", _te)

    handler = make_handler(repository, config, repository_android=repository_android)
    with ThreadingHTTPServer((host, port), handler) as httpd:
        httpd.serve_forever()

    # Clean up tray when server exits
    if _tray_instance is not None:
        try:
            _tray_instance.stop()
        except Exception:
            pass
