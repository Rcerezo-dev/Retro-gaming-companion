from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.sync.adb_transport import AdbTransport
    from rom_manager.web.router import Router


# ── Public entry point ────────────────────────────────────────────────────────


def register_tools(router: Router, *, config: AppConfig) -> None:
    """Register hardware/tool detection routes on *router*."""

    @router.get("/api/wizard-detect")
    def get_wizard_detect(ctx) -> None:
        ctx._send_json(_detect_wizard(config))

    @router.get("/api/test-chdman")
    def get_test_chdman(ctx) -> None:
        ctx._send_json(
            _test_binary_status(
                str(config.chdman)
                if config.chdman
                else str(config.project_root / "tools" / "chdman.exe"),
            )
        )

    @router.get("/api/test-maxcso")
    def get_test_maxcso(ctx) -> None:
        ctx._send_json(
            _test_binary_status(
                str(config.project_root / "tools" / "maxcso.exe"),
            )
        )

    @router.get("/api/detect-retroarch")
    def get_detect_retroarch(ctx) -> None:
        ctx._send_json(_detect_retroarch_install())

    # ── GET /api/detect-android-ra-config-dir (B0-3c) ───────────────────────────
    @router.get("/api/detect-android-ra-config-dir")
    def get_detect_android_ra_config_dir(ctx) -> None:
        from rom_manager.sync.adb_transport import resolve_single_device_transport

        ctx._send_json(
            _detect_android_ra_config_dir(config, resolve_single_device_transport(config.adb))
        )


# ── Handler logic (moved from config.py, REFACTOR-9) ──────────────────────────


def _detect_retroarch_install() -> dict:
    """Scan common Windows paths for a RetroArch installation.

    Checks common install directories, Steam libraries (including non-default ones
    via libraryfolders.vdf), and RetroBat. Returns the first ``retroarch.exe`` found
    plus the ``content_directory`` from its ``retroarch.cfg`` if readable.
    """
    import os
    import re

    candidates: list[Path] = []

    appdata = os.environ.get("APPDATA", "")
    if appdata:
        candidates.append(Path(appdata) / "RetroArch")

    for drive in ("C", "D", "E"):
        candidates += [
            Path(f"{drive}:\\RetroArch-Win64"),
            Path(f"{drive}:\\RetroArch"),
            Path(f"{drive}:\\Program Files\\RetroArch"),
            Path(f"{drive}:\\Program Files (x86)\\RetroArch"),
            Path(f"{drive}:\\Program Files (x86)\\Steam\\steamapps\\common\\RetroArch"),
        ]

    # Steam — additional library folders from libraryfolders.vdf
    localappdata = os.environ.get("LOCALAPPDATA", "")
    vdf_paths = [
        Path(localappdata) / "Steam" / "steamapps" / "libraryfolders.vdf" if localappdata else None,
        Path("C:\\Program Files (x86)\\Steam\\steamapps\\libraryfolders.vdf"),
    ]
    for vdf in vdf_paths:
        if not vdf or not vdf.exists():
            continue
        try:
            text = vdf.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r'"path"\s+"([^"]+)"', text):
                lib_path = m.group(1).strip().replace("\\\\", "\\")
                candidates.append(Path(lib_path) / "steamapps" / "common" / "RetroArch")
        except OSError:
            pass

    # RetroBat
    user_profile = os.environ.get("USERPROFILE", "")
    if user_profile:
        candidates.append(Path(user_profile) / "RetroBat" / "emulators" / "retroarch")
    for drive in ("C", "D", "E"):
        candidates.append(Path(f"{drive}:\\RetroBat\\emulators\\retroarch"))

    retroarch_path: str | None = None
    library_root: str | None = None
    ra_config_dir: str | None = None

    for ra_dir in candidates:
        exe = ra_dir / "retroarch.exe"
        if not exe.exists():
            continue
        retroarch_path = str(exe)
        # CFG-PORGAME: config/ es la carpeta estándar de RetroArch junto al
        # ejecutable (mismo directorio que ya usa _handle_retroarch_check para
        # cores/ y retroarch.cfg) — de ahí cuelgan los .opt de opciones por core.
        ra_config_dir = str(ra_dir / "config")
        cfg_path = ra_dir / "retroarch.cfg"
        if cfg_path.exists():
            try:
                text = cfg_path.read_text(encoding="utf-8", errors="replace")
                m = re.search(r'^content_directory\s*=\s*"(.+)"', text, re.MULTILINE)
                if m:
                    val = m.group(1).strip()
                    if val not in ("", "default"):
                        library_root = val
            except OSError:
                pass
        break

    return {
        "found": retroarch_path is not None,
        "retroarch_path": retroarch_path,
        "library_root": library_root,
        "ra_config_dir": ra_config_dir,
    }


def _detect_android_ra_config_dir(config: AppConfig, adb_transport: AdbTransport | None) -> dict:
    """Probe the connected Android device for its RetroArch ``config/`` folder (B0-3c).

    Mirrors `_detect_retroarch_install()`'s response shape for the PC side, but
    there's no filesystem to scan directly here — ADB is the only way to know
    the folder is really there. Candidate: ``<auto_sync_android_path>/config``,
    the same RetroArch root already validated in production for this device's
    saves/states (``config.py`` ``EMULATOR_MAP``); `AdbTransport.test_path()`
    (already used for the same purpose elsewhere, e.g. cable-sync path checks)
    confirms it instead of assuming it's there.
    """
    if adb_transport is None:
        return {
            "found": False,
            "ra_config_dir": None,
            "error": "conecta el dispositivo Android por ADB primero",
        }

    candidate = f"{config.sync.auto_sync_android_path}/config"
    result = adb_transport.test_path(candidate)
    if result.get("accessible"):
        return {"found": True, "ra_config_dir": candidate}
    return {
        "found": False,
        "ra_config_dir": None,
        "error": result.get("error", f"No se encontró {candidate!r} en el dispositivo"),
    }


def _detect_wizard(config: AppConfig) -> dict:
    """Auto-detect RetroArch installation and connected ADB devices for the first-run wizard."""
    ra = _detect_retroarch_install()
    library_root_suggestion = ra["library_root"] or ra["retroarch_path"]

    # Check ADB for connected devices
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
            android_suggestion = config.anbernic_root or "/storage/emulated/0/RetroArch/roms"
    except Exception:
        _logger.debug("Detección de dispositivos ADB falló", exc_info=True)

    return {
        "library_root_suggestion": library_root_suggestion,
        "retroarch_path_suggestion": ra["retroarch_path"],
        "android_suggestion": android_suggestion,
        "device_display": device_display,
        "adb_ok": adb_ok,
    }


def _test_binary_status(path_str: str) -> dict:
    """Return {ok, version, path} for an external binary."""
    import shutil as _shutil
    import subprocess as _sp

    p = Path(path_str) if path_str else None
    if not p or not p.exists():
        found = _shutil.which(path_str or "")
        if not found:
            return {"ok": False, "version": "", "path": path_str}
        p = Path(found)
    try:
        r = _sp.run([str(p), "--version"], capture_output=True, text=True, timeout=5)
        ver = (r.stdout or r.stderr or "").strip().splitlines()[0][:60]
        return {"ok": True, "version": ver, "path": str(p)}
    except Exception:
        _logger.debug("No se pudo leer la versión del binario %s", p, exc_info=True)
        return {"ok": True, "version": "", "path": str(p)}
