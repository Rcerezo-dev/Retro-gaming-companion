from __future__ import annotations

import logging
import socket
from pathlib import Path

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.sync_cloud import _handle_rclone_status

_logger = logging.getLogger(__name__)

# ── Tablas de plataformas ─────────────────────────────────────────────────────
# Canonical ES-DE platform folder names (platform detector name → ES folder)
_ES_PLATFORM_FOLDERS: dict[str, str] = {
    "NES": "nes",
    "SNES": "snes",
    "Nintendo 64": "n64",
    "Game Boy": "gb",
    "Game Boy Color": "gbc",
    "Game Boy Advance": "gba",
    "Nintendo DS": "nds",
    "Nintendo 3DS": "3ds",
    "GameCube": "gamecube",
    "Wii": "wii",
    "Wii U": "wiiu",
    "Nintendo Switch": "switch",
    "Master System": "mastersystem",
    "Game Gear": "gamegear",
    "Sega Genesis": "megadrive",
    "Sega Mega Drive": "megadrive",
    "Dreamcast": "dreamcast",
    "PlayStation": "psx",
    "PlayStation 2": "ps2",
    "PlayStation 3": "ps3",
    "PSP": "psp",
    "PS Vita": "psvita",
    "Sega Saturn": "saturn",
    "Saturn": "saturn",  # alias legacy
    "Atari 2600": "atari2600",
    "Atari 5200": "atari5200",
    "Atari 7800": "atari7800",
    "Atari Lynx": "atarilynx",
    "Atari Jaguar": "atarijaguar",
    "Neo Geo": "neogeo",
    "Neo Geo Pocket Color": "ngpc",
    "PC Engine": "pcengine",
    "Sega 32X": "sega32x",
    "Sega CD": "segacd",
    "Arcade": "arcade",
    # Nintendo extras
    "Virtual Boy": "virtualboy",
    "Nintendo 64DD": "n64dd",
    "Famicom Disk System": "fds",
    "Pokemon Mini": "pokemini",
    "Game & Watch": "gameandwatch",
    # Sega extras
    "SuperGrafx": "supergrafx",
    # Atari extras
    "Atari ST": "atarist",
    "Atari XL/XE": "atari800",
    # Portable / retro micros
    "WonderSwan": "wonderswan",
    "WonderSwan Color": "wonderswancolor",
    "Watara Supervision": "supervision",
    # Home computers
    "Amiga": "amiga",
    "Commodore 64": "c64",
    "ZX Spectrum": "zxspectrum",
    "MSX": "msx",
    "DOS": "dos",
    "ScummVM": "scummvm",
    # Other consoles
    "ColecoVision": "colecovision",
    "Intellivision": "intellivision",
    "PC-FX": "pcfx",
}

_STANDARD_PLATFORM_FOLDERS: tuple[str, ...] = (
    # Nintendo
    "nes",
    "snes",
    "n64",
    "gb",
    "gbc",
    "gba",
    "nds",
    "3ds",
    "gamecube",
    "wii",
    "wiiu",
    "switch",
    # Sony
    "psx",
    "ps2",
    "ps3",
    "psp",
    "psvita",
    # Sega
    "megadrive",
    "mastersystem",
    "gamegear",
    "dreamcast",
    "saturn",
    "sega32x",
    "segacd",
    # Atari
    "atari2600",
    "atari5200",
    "atari7800",
    "atarilynx",
    "atarijaguar",
    # Otros
    "neogeo",
    "pcengine",
    # Arcade
    "arcade",
)


# ── Helpers de sistema ────────────────────────────────────────────────────────


def _get_local_ip() -> str:
    """Best-effort: return the machine's LAN IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        _logger.debug("No se pudo determinar la IP local de la LAN", exc_info=True)
        return "127.0.0.1"


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
                    detected.append(
                        {
                            "service": "Dropbox",
                            "local_folder": folder,
                            "suggested_remote": folder.replace("\\", "/") + "/RetroVault/saves",
                        }
                    )
                    break
    except Exception:
        _logger.debug("Detección de carpeta Dropbox falló", exc_info=True)

    # OneDrive — env var set by the client
    for env_var in ("OneDriveConsumer", "OneDrive"):
        folder = _os.environ.get(env_var, "")
        if folder and _P(folder).exists():
            detected.append(
                {
                    "service": "OneDrive",
                    "local_folder": folder,
                    "suggested_remote": folder.replace("\\", "/") + "/RetroVault/saves",
                }
            )
            break

    # Google Drive for Desktop — typical install path
    try:
        gdrive = _P(_os.environ.get("LOCALAPPDATA", "")) / "Google" / "Drive File Stream"
        if not gdrive.exists():
            gdrive = _P(_os.environ.get("USERPROFILE", "")) / "Google Drive"
        if gdrive.exists():
            detected.append(
                {
                    "service": "Google Drive",
                    "local_folder": str(gdrive),
                    "suggested_remote": str(gdrive).replace("\\", "/") + "/RetroVault/saves",
                }
            )
    except Exception:
        _logger.debug("Detección de Google Drive falló", exc_info=True)

    return {"detected": detected}


def _handle_system_status(config: AppConfig) -> dict:
    """Aggregate status of all external tools and data dependencies."""
    import subprocess as _sp
    from pathlib import Path as _P

    def _test_binary(path_str: str, flag: str = "--version") -> tuple[bool, str]:
        p = _P(path_str) if path_str else None
        if not p or not p.exists():
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
            _logger.debug("No se pudo leer la versión de %s", p, exc_info=True)
            return True, ""

    chdman_ok, chdman_ver = _test_binary(str(config.chdman) if config.chdman else "")
    adb_ok, adb_ver = _test_binary(str(config.adb) if config.adb else "")
    rclone_st = _handle_rclone_status(config)
    from rom_manager.web.handlers.scan import _catalog_status

    cats = _catalog_status(config)
    cat_total = (
        len(cats.get("nointro", [])) + len(cats.get("redump", [])) + len(cats.get("arcade", []))
    )

    return {
        "chdman": {
            "ok": chdman_ok,
            "version": chdman_ver,
            "path": str(config.chdman or "tools/chdman.exe"),
        },
        "adb": {"ok": adb_ok, "version": adb_ver, "path": str(config.adb or "tools/adb.exe")},
        "rclone": {
            "ok": rclone_st["installed"],
            "version": rclone_st.get("version", ""),
            "remotes": rclone_st.get("remotes", []),
        },
        "ra_key": {"ok": bool(config.credentials.ra_api_key)},
        "catalogs": {
            "ok": cat_total > 0,
            "total": cat_total,
            "nointro": len(cats.get("nointro", [])),
            "redump": len(cats.get("redump", [])),
        },
        "library": {"ok": bool(config.library_root), "path": str(config.library_root or "")},
    }


def _handle_library_doctor(config: AppConfig, repository: LibraryRepository) -> dict:
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
                issues.append(
                    {
                        "type": "misplaced_rom",
                        "severity": "warning",
                        "file": _fname,
                        "path": _sp,
                        "platform": _plat,
                        "expected_dir": _expected_dir,
                        "action": f"Mover a {_expected_slug}/",
                    }
                )
    except Exception:
        _logger.warning("Escaneo de ROMs mal ubicadas falló en %s", root, exc_info=True)

    # (b) Incomplete CUE sets — .cue file references .bin files that don't exist
    _cue_bin_re = _re.compile(r'^\s*FILE\s+"?([^"]+)"?\s+BINARY', _re.IGNORECASE | _re.MULTILINE)
    for _cue in root.rglob("*.cue"):
        try:
            _text = _cue.read_text(encoding="utf-8", errors="replace")
            _refs = _cue_bin_re.findall(_text)
            _missing = [r for r in _refs if not (_cue.parent / r).exists()]
            if _missing:
                issues.append(
                    {
                        "type": "incomplete_cue",
                        "severity": "error",
                        "file": _cue.name,
                        "path": str(_cue),
                        "platform": None,
                        "missing_bins": _missing[:5],
                        "action": f"Faltan {len(_missing)} .bin — set incompleto",
                    }
                )
        except Exception:
            _logger.debug("No se pudo analizar el .cue en el escaneo de salud", exc_info=True)

    # (c) Empty platform directories
    for _d in root.iterdir():
        if _d.is_dir() and _d.name not in (
            "saves",
            "bios",
            "inbox",
            "states",
            "screenshots",
            "_descartados",
        ):
            try:
                _files = [f for f in _d.rglob("*") if f.is_file()]
                if not _files:
                    issues.append(
                        {
                            "type": "empty_dir",
                            "severity": "info",
                            "file": _d.name,
                            "path": str(_d),
                            "platform": None,
                            "action": "Carpeta vacía — puedes eliminarla",
                        }
                    )
            except Exception:
                _logger.debug("No se pudo inspeccionar el directorio %s", _d, exc_info=True)

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
        "savefile_drift": False,
        "esde_ra_path": "",
        "esde_ra_match": None,
        "issues": [],
        "ok": False,
    }

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

    ra_dir = ra_path.parent
    cfg = ra_dir / "retroarch.cfg"
    result["cfg_exists"] = cfg.exists()
    if not cfg.exists():
        result["issues"].append(f"retroarch.cfg no encontrado en {ra_dir}")

    if cfg.exists():
        from rom_manager.services.retroarch_cfg_writer import (
            default_savefile_layout,
            read_savefile_layout,
        )

        try:
            text = cfg.read_text(encoding="utf-8", errors="replace")
            layout = read_savefile_layout(text)
            result["savefile_dir"] = layout.savefile_dir
            result["savestate_dir"] = layout.savestate_dir
        except OSError:
            layout = None

        # DEVPROFILE-7: warn when the live cfg no longer matches the D2 sync
        # convention (library_root/saves + /states) — the most common way
        # today's saves silently stop syncing (fresh RetroArch install, a
        # manual edit, a stale path from before DEVPROFILE-2). Free once the
        # default layout convention exists (DEVPROFILE-2/2d).
        if layout is not None and config.library_root:

            def _norm(p: str) -> str:
                return str(Path(p)).lower().rstrip("\\/") if p else ""

            expected = default_savefile_layout(config.library_root)
            save_drift = _norm(layout.savefile_dir) != _norm(expected.savefile_dir)
            state_drift = _norm(layout.savestate_dir) != _norm(expected.savestate_dir)
            result["savefile_drift"] = save_drift or state_drift
            if save_drift:
                result["issues"].append(
                    f"savefile_directory no coincide con el layout de sync (D2): actual "
                    f"'{layout.savefile_dir or '(no configurado)'}', esperado "
                    f"'{expected.savefile_dir}' — tus partidas nuevas podrían no estar "
                    'sincronizándose. Pulsa "Aplicar layout de saves".'
                )
            if state_drift:
                result["issues"].append(
                    f"savestate_directory no coincide con el layout de sync (D2): actual "
                    f"'{layout.savestate_dir or '(no configurado)'}', esperado "
                    f"'{expected.savestate_dir}'."
                )

    cores_dir = ra_dir / "cores"
    result["cores_dir_exists"] = cores_dir.exists()
    if cores_dir.exists():
        dlls = list(cores_dir.glob("*_libretro.dll"))
        result["cores_count"] = len(dlls)
        if len(dlls) == 0:
            result["issues"].append("Carpeta cores/ existe pero no contiene cores (_libretro.dll).")
        key_map = {
            "mgba": "GBA",
            "gambatte": "GB/GBC",
            "snes9x": "SNES",
            "genesis_plus_gx": "Mega Drive",
            "fceumm": "NES",
            "nestopia": "NES (alt)",
            "pcsx_rearmed": "PSX",
            "duckstation": "PSX (DuckStation)",
            "pcsx2": "PS2",
            "flycast": "Dreamcast",
            "mupen64plus_next": "N64",
            "melonds": "NDS",
            "ppsspp": "PSP",
            "mame": "MAME/Arcade",
            "fbneo": "FBNeo/Arcade",
        }
        for core_prefix, label in key_map.items():
            result["key_cores"][label] = any(d.name.startswith(core_prefix) for d in dlls)
    else:
        result["issues"].append(f"Carpeta cores/ no encontrada en {ra_dir}")

    from rom_manager.web.handlers.esde import _handle_esde_status

    esde_info = _handle_esde_status(config)
    if esde_info.get("installed") and esde_info.get("install_dir"):
        settings_xml = Path(esde_info["install_dir"]) / "es_settings.xml"
        esde_cfg = Path(esde_info["install_dir"]) / "es_systems.xml"
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
        a = (
            Path(result["esde_ra_path"]).resolve()
            if Path(result["esde_ra_path"]).exists()
            else None
        )
        b = ra_path.resolve() if ra_path.exists() else None
        result["esde_ra_match"] = (str(a).lower() == str(b).lower()) if (a and b) else None

    result["ok"] = (
        result["exe_exists"]
        and result["cfg_exists"]
        and result["cores_dir_exists"]
        and len(result["issues"]) == 0
    )
    return result


def _handle_apply_retroarch_savefile_layout(config: AppConfig) -> dict:
    """DEVPROFILE-2d: manual trigger for apply_savefile_layout() from Settings.

    Botón manual, no automático (Tareas/Roadmap-DEVPROFILE-1-4.md §3) —
    reescribe un .cfg del usuario, así que solo se dispara si lo pide.
    Localiza retroarch.cfg igual que ``_handle_retroarch_check`` (junto al
    exe configurado, no ``_detect_retroarch_install()``) y usa
    ``library_root/saves`` + ``library_root/states`` como destino, el mismo
    convenio que ya asume el sync a la nube (D2, ``sync.saves_remote``).
    """
    from rom_manager.services.retroarch_cfg_writer import (
        apply_savefile_layout,
        default_savefile_layout,
    )

    ra_exe = (config.retroarch_path or "").strip()
    if not ra_exe:
        return {"applied": False, "error": "RetroArch no está configurado en Settings."}
    if not config.library_root:
        return {"applied": False, "error": "library_root no está configurado en Settings."}

    cfg = Path(ra_exe).parent / "retroarch.cfg"
    if not cfg.exists():
        return {"applied": False, "error": f"retroarch.cfg no encontrado en {cfg.parent}"}

    layout = default_savefile_layout(config.library_root)
    result = apply_savefile_layout(cfg, layout.savefile_dir, layout.savestate_dir)
    return {
        "applied": result.applied,
        "backup_path": result.backup_path,
        "changed_keys": result.changed_keys,
        "error": result.error,
        "savefile_dir": layout.savefile_dir,
        "savestate_dir": layout.savestate_dir,
    }


def _handle_device_profile_detect(config: AppConfig) -> dict:
    """DEVPROFILE-4a UI: Tier A source candidates for the "Perfil del
    dispositivo" confirm screen in Settings.

    Locates RetroArch the same way as ``_handle_retroarch_check`` (next to
    the configured exe) and reuses ``detect_tier_a_sources()``
    (services/device_profile.py), plus ``detect_data_sources()`` (DEVPROFILE-8,
    tool-owned data under ``.rommgr`` -- catalogs today -- independent of
    RetroArch being configured at all). Candidates already present in
    ``config.sync.sync_sources`` (by local_dir) are excluded — the screen
    only asks about *new* folders, confirming again on every visit would be
    noise.
    """
    from rom_manager.services.device_profile import detect_data_sources, detect_tier_a_sources

    remote = config.sync.saves_remote or config.sync.states_remote or ""
    remote_base = remote.rsplit("/", 1)[0] if "/" in remote else remote

    existing = config.sync.sync_sources
    existing_dirs = {str(Path(s.local_dir)) for s in existing}

    def _as_dict(s):
        return {
            "name": s.name,
            "local_dir": s.local_dir,
            "remote": s.remote,
            "sync_all": s.sync_all,
        }

    ra_exe = (config.retroarch_path or "").strip()
    detected = list(detect_data_sources(config.project_root, remote_base))
    if ra_exe:
        detected += detect_tier_a_sources(Path(ra_exe).parent, remote_base)
    elif not detected:
        return {
            "error": "RetroArch no está configurado en Settings.",
            "candidates": [],
            "existing": [],
        }

    candidates = [_as_dict(s) for s in detected if str(Path(s.local_dir)) not in existing_dirs]
    return {
        "candidates": candidates,
        "existing": [_as_dict(s) for s in existing],
        "remote_base": remote_base,
    }


def _handle_save_device_profile_manifest(config: AppConfig) -> dict:
    """DEVPROFILE-5a: manual "save profile to the cloud" trigger from the
    same "Perfil del dispositivo" panel.

    Uploads the already-confirmed ``config.sync.sync_sources`` (not the
    detect candidates — only what the user actually saved) as
    ``<remote_base>/device-profile.json``, closing the gap where
    DEVPROFILE-4's export/import functions had no production caller (see
    Tareas/Roadmap-DEVPROFILE-5-6.md §1). ``rommgr restore`` (DEVPROFILE-5b+)
    is the future reader of this file.
    """
    from rom_manager.services.device_profile import save_profile_manifest
    from rom_manager.sync.rclone_transport import RcloneError, RcloneTransport

    if not config.library_root:
        return {"saved": False, "error": "library_root no está configurado en Settings."}
    if not config.sync.sync_sources:
        return {
            "saved": False,
            "error": 'No hay fuentes de sync confirmadas todavía — usa "Guardar selección" primero.',
        }

    remote = config.sync.saves_remote or config.sync.states_remote or ""
    remote_base = remote.rsplit("/", 1)[0] if "/" in remote else remote
    if not remote_base:
        return {
            "saved": False,
            "error": "No hay remoto de sync configurado (saves_remote/states_remote).",
        }

    ra_exe = (config.retroarch_path or "").strip()
    system_dir = Path(ra_exe).parent / "system" if ra_exe else config.library_root / "system"

    transport = RcloneTransport(rclone=config.rclone_binary)
    try:
        remote_path = save_profile_manifest(
            config.sync.sync_sources,
            roms_dir=config.library_root,
            saves_dir=config.library_root / "saves",
            system_dir=system_dir,
            transport=transport,
            remote_base=remote_base,
            project_root=config.project_root,
        )
    except RcloneError as exc:
        return {"saved": False, "error": str(exc)}

    return {"saved": True, "remote_path": remote_path, "sources": len(config.sync.sync_sources)}
