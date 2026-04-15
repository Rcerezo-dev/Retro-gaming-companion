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
    _repo_for_path,
    _build_junk_scan, _build_library_report, _build_status,
    _build_games, _count_companion_saves,
    _build_folder_analysis,
    _build_assets, _build_sync_log,
    _build_cable_sync_preview,
)
from rom_manager.web.cable_sync_daemon import _auto_sync_loop, _sd_card_sync_loop
from rom_manager.web.inbox_pipeline import (
    _build_inbox_scan, _run_setup_pipeline, _run_inbox_pipeline, _watcher_now,
)

# ── Tray icon instance (set by serve() when --tray is passed) ─────────────────
_tray_instance = None  # type: ignore[assignment]

# ── HTTP server instance (set by serve(), used by /api/shutdown) ───────────────
_httpd_instance = None  # type: ignore[assignment]

# ── Background job state ──────────────────────────────────────────────────────
_job_lock = threading.Lock()
_jobs: dict[str, bool] = {
    "scan": False, "match": False, "sync": False,
    "convert_chd": False, "convert_cso": False, "scrape": False,
    "extract_zip": False, "health_check": False,
    "ra_check": False, "cable_sync": False,
    "apply": False, "inbox": False, "setup": False,
    "backup_now": False,
    "tree_diff": False,
    "verify_chd": False,
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
    # Nintendo extras
    "Virtual Boy":          "virtualboy",
    "Nintendo 64DD":        "n64dd",
    "Famicom Disk System":  "fds",
    "Pokemon Mini":         "pokemini",
    "Game & Watch":         "gameandwatch",
    # Sega extras
    "SuperGrafx":           "supergrafx",
    # Atari extras
    "Atari ST":             "atarist",
    "Atari XL/XE":          "atari800",
    # Portable / retro micros
    "WonderSwan":           "wonderswan",
    "WonderSwan Color":     "wonderswancolor",
    "Watara Supervision":   "supervision",
    # Home computers
    "Amiga":                "amiga",
    "Commodore 64":         "c64",
    "ZX Spectrum":          "zxspectrum",
    "MSX":                  "msx",
    "DOS":                  "dos",
    "ScummVM":              "scummvm",
    # Other consoles
    "ColecoVision":         "colecovision",
    "Intellivision":        "intellivision",
    "PC-FX":                "pcfx",
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
_inbox_watcher_status: dict = {"watching": False, "last_check": None, "pending_files": 0, "trigger_ts": 0}
_setup_progress: dict = {}   # {"step": str, "step_num": int, "total_steps": int, "current_file": str, "pct": int}
_verify_chd_progress: dict = {}  # {"current": int, "total": int, "current_file": str}
_scan_cancel:   threading.Event = threading.Event()
_cable_cancel:  threading.Event = threading.Event()
_chd_cancel:    threading.Event = threading.Event()
_verify_chd_cancel: threading.Event = threading.Event()
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
    from rom_manager.web.handlers.scan import _catalog_status
    cats = _catalog_status(config)
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
    from rom_manager.web.handlers.esde import _handle_esde_status
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



def make_handler(repository: LibraryRepository, config: AppConfig, repository_android: LibraryRepository | None = None):
    logger = logging.getLogger(__name__)
    # If no android repo is provided (e.g. called from CLI), use a no-op fallback = same as PC repo
    _repo_android: LibraryRepository = repository_android if repository_android is not None else repository

    # ── Phase 1: Router (replaces if/elif ladder incrementally) ───────────────
    from rom_manager.web.router import Router
    import rom_manager.web.server as _srv_mod  # used by set_auto_sync_fn

    _router = Router()

    def _set_auto_sync_fn(val: bool) -> None:
        _srv_mod._auto_sync_enabled = val

    import rom_manager.web.handlers.config as _h_config
    _h_config.register(_router, config=config, set_auto_sync_fn=_set_auto_sync_fn)

    # ── End Phase 1 router setup ───────────────────────────────────────────────

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
                        "alternatives_csv": "", "results": [], "alternatives": [],
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
                    "results": [
                        {
                            "status": r.status,
                            "original_filename": r.original_filename,
                            "platform": r.platform,
                            "source_path": r.source_path,
                            **({"alternative": {
                                "id": r.alternative.id,
                                "title": r.alternative.title,
                                "achievements": r.alternative.achievements,
                                "points": r.alternative.points,
                            }} if r.alternative else {}),
                        }
                        for r in summary.results
                    ],
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

    import rom_manager.web.handlers.collection as _h_collection
    import sys as _sys_dbg
    try:
        _h_collection.register(_router, config=config, repository=repository, repo_android=_repo_android, get_repo_fn=_get_repo)
        asset_routes = [r for r in _router.routes() if 'asset' in r[1].lower()]
        print(f"[DEBUG] Registered asset routes: {asset_routes}", file=_sys_dbg.stderr)
        print(f"[DEBUG] Total routes after collection: {len(_router.routes())}", file=_sys_dbg.stderr)
        if not asset_routes:
            print(f"[DEBUG] WARNING: No asset routes registered!", file=_sys_dbg.stderr)
            print(f"[DEBUG] All routes: {_router.routes()[:10]}", file=_sys_dbg.stderr)
    except Exception as _reg_err:
        print(f"[ERROR] Failed to register collection handlers: {_reg_err}", file=_sys_dbg.stderr)
        import traceback
        traceback.print_exc(file=_sys_dbg.stderr)
        raise

    import rom_manager.web.handlers.scan as _h_scan
    _h_scan.register(
        _router,
        config=config,
        repository=repository,
        repo_android=_repo_android,
        get_repo_fn=_get_repo,
        start_ra_check_fn=_start_ra_check_bg,
        srv_mod=_srv_mod,
    )

    import rom_manager.web.handlers.duplicates as _h_duplicates
    _h_duplicates.register(
        _router,
        config=config,
        repository=repository,
        repo_android=_repo_android,
        srv_mod=_srv_mod,
    )

    import rom_manager.web.handlers.organize as _h_organize
    _h_organize.register(
        _router,
        config=config,
        repository=repository,
        get_repo_fn=_get_repo,
        srv_mod=_srv_mod,
    )

    import rom_manager.web.handlers.sync as _h_sync
    _h_sync.register(
        _router,
        config=config,
        repository=repository,
        repo_android=_repo_android,
        start_ra_check_fn=_start_ra_check_bg,
        srv_mod=_srv_mod,
    )

    import rom_manager.web.handlers.inbox as _h_inbox
    _h_inbox.register(
        _router,
        config=config,
        repository=repository,
        srv_mod=_srv_mod,
    )

    import rom_manager.web.handlers.scraper as _h_scraper
    _h_scraper.register(
        _router,
        config=config,
        repository=repository,
        srv_mod=_srv_mod,
    )

    import rom_manager.web.handlers.games as _h_games
    _h_games.register(
        _router,
        config=config,
        repository=repository,
        get_repo_fn=_get_repo,
        srv_mod=_srv_mod,
    )

    import rom_manager.web.handlers.play_history as _h_play_history
    _h_play_history.register(
        _router,
        repository=repository,
    )

    import rom_manager.web.handlers.esde as _h_esde
    _h_esde.register(
        _router,
        config=config,
        repository=repository,
        repo_android=_repo_android,
        get_repo_fn=_get_repo,
        srv_mod=_srv_mod,
    )

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

                # Phase 1: try router before the legacy ladder
                self._qs = qs
                if _router.dispatch("GET", path, self):
                    return

                if path == "/":
                    self._send(200, "text/html; charset=utf-8", HTML.encode())
                elif path.startswith("/static/"):
                    filename = path[len("/static/"):]
                    import sys as _sys
                    if getattr(_sys, "frozen", False) and hasattr(_sys, "_MEIPASS"):
                        static_dir = Path(_sys._MEIPASS) / "rom_manager" / "web" / "static"
                    else:
                        static_dir = Path(__file__).parent / "static"
                    if not filename:
                        self._send(404, "text/plain", b"Not found")
                    else:
                        file_path = (static_dir / filename).resolve()
                        # Security: prevent path traversal while allowing subdirectories
                        try:
                            file_path.relative_to(static_dir.resolve())
                        except (ValueError, OSError):
                            self._send(404, "text/plain", b"Not found")
                            return
                        if not file_path.is_file():
                            self._send(404, "text/plain", b"Not found")
                        else:
                            ext = file_path.suffix.lower()
                            content_type = {
                                ".css": "text/css; charset=utf-8",
                                ".js":  "application/javascript; charset=utf-8",
                            }.get(ext, "application/octet-stream")
                            self._send(200, content_type, file_path.read_bytes())
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
                from rom_manager.web.handlers.inbox import handle_inbox_upload
                handle_inbox_upload(config, _ct, raw, self)
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

                # Phase 1: try router before the legacy ladder
                self._post_data = data
                if _router.dispatch("POST", path, self):
                    return

                else:
                    self._send(404, "text/plain", b"Not found")
            except Exception as exc:
                body = json.dumps({"error": str(exc)}).encode()
                self._send(500, "application/json", body)

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

        def _send_error(self, code: int, message: str) -> None:
            body = _json_response({"error": message})
            self._send(code, "application/json; charset=utf-8", body)

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
                        _inbox_watcher_status["trigger_ts"] = _time.time()
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
                                saves_dir,
                                saves_remote=src.remote,
                                transport=transport,
                                repository=repository,
                                save_extensions=config.save_extensions,
                                state_extensions=config.state_extensions,
                                states_remote=None,
                                dry_run=False,
                            )
                        except Exception:
                            pass
                    # D2: implicit saves/states remotes
                    _implicit_tray = []
                    if config.saves_remote and config.library_root:
                        _implicit_tray.append((_Path(config.library_root) / "saves", config.saves_remote, config.save_extensions))
                    if config.states_remote and config.library_root:
                        _implicit_tray.append((_Path(config.library_root) / "states", config.states_remote, config.state_extensions))
                    for _dir, _remote, _exts in _implicit_tray:
                        if not _dir.exists():
                            continue
                        try:
                            # D2: implicit tray sync with dual remotes
                            _is_states_tray = _exts == config.state_extensions
                            sync_saves(
                                _dir,
                                saves_remote=_remote if not _is_states_tray else None,
                                transport=transport,
                                repository=repository,
                                save_extensions=_exts,
                                state_extensions=_exts if _is_states_tray else tuple(),
                                states_remote=_remote if _is_states_tray else None,
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

    global _httpd_instance
    handler = make_handler(repository, config, repository_android=repository_android)
    with ThreadingHTTPServer((host, port), handler) as httpd:
        _httpd_instance = httpd
        httpd.serve_forever()

    # Clean up tray when server exits
    if _tray_instance is not None:
        try:
            _tray_instance.stop()
        except Exception:
            pass
