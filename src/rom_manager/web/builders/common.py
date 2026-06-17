"""HTTP/path utilities and shared helpers used across the response builders.

Pure functions: typed params → JSON-ready values. No global job state.
"""

from __future__ import annotations

import json
from datetime import UTC
from pathlib import Path

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository
from rom_manager.planner.operation_planner import FormatOptions


def _json_response(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode()


def _test_path(path_str: str) -> dict:
    """Check whether *path_str* is an accessible directory on the local filesystem.

    Also detects common MTP / shell-namespace patterns that look like real paths
    but are not accessible from Python.
    """
    raw = path_str.strip()
    if not raw:
        return {"accessible": False, "error": "Introduce una ruta primero"}

    # Heuristic: detect Windows MTP paths (not a drive letter, not a UNC share)
    is_drive_letter = len(raw) >= 2 and raw[1] == ":" and raw[0].isalpha()
    is_unc = raw.startswith("\\\\") or raw.startswith("//")
    looks_like_mtp = not is_drive_letter and not is_unc

    try:
        p = Path(path_str).resolve()
        if not p.exists():
            msg = (
                "Esta ruta no existe como carpeta del sistema de archivos. "
                "Si ves el dispositivo en 'Este equipo', está accediendo por MTP — "
                "eso no es compatible. Usa la SD card en un lector USB o Termux SFTP."
            )
            return {"accessible": False, "error": msg, "looks_like_mtp": looks_like_mtp}
        if not p.is_dir():
            return {"accessible": False, "error": "La ruta existe pero no es una carpeta"}
        try:
            entries = sum(1 for _ in p.iterdir())
        except PermissionError:
            return {"accessible": False, "error": "Sin permiso de lectura en esa carpeta"}
        return {
            "accessible": True,
            "path": str(p),
            "entries": entries,
        }
    except (OSError, ValueError) as exc:
        return {"accessible": False, "error": str(exc), "looks_like_mtp": looks_like_mtp}


def _list_drives() -> dict:
    """Return all accessible drive letters on Windows (A–Z), with label and free space."""
    import platform

    drives: list[dict] = []
    if platform.system() == "Windows":
        import ctypes
        import string

        for letter in string.ascii_uppercase:
            root = Path(f"{letter}:\\")
            if root.exists():
                try:
                    label_buf = ctypes.create_unicode_buffer(261)
                    fs_buf = ctypes.create_unicode_buffer(261)
                    ctypes.windll.kernel32.GetVolumeInformationW(  # type: ignore[attr-defined]
                        f"{letter}:\\",
                        label_buf,
                        261,
                        None,
                        None,
                        None,
                        fs_buf,
                        261,
                    )
                    label = label_buf.value or ""
                    usage = ctypes.c_ulonglong(0)
                    free_c = ctypes.c_ulonglong(0)
                    total_c = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(  # type: ignore[attr-defined]
                        f"{letter}:\\",
                        ctypes.byref(usage),
                        ctypes.byref(total_c),
                        ctypes.byref(free_c),
                    )
                    drives.append(
                        {
                            "letter": f"{letter}:\\",
                            "label": label,
                            "total_bytes": total_c.value,
                            "free_bytes": free_c.value,
                        }
                    )
                except OSError:
                    drives.append(
                        {"letter": f"{letter}:\\", "label": "", "total_bytes": 0, "free_bytes": 0}
                    )
    else:
        try:
            for line in Path("/proc/mounts").read_text().splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[1].startswith("/media"):
                    drives.append(
                        {
                            "letter": parts[1],
                            "label": parts[1].split("/")[-1],
                            "total_bytes": 0,
                            "free_bytes": 0,
                        }
                    )
        except OSError:
            pass
    return {"drives": drives}


def _utc_now_str() -> str:
    from datetime import datetime

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")


def _parse_format_opts(qs: dict) -> FormatOptions:
    return FormatOptions(
        include_region=qs.get("include_region", ["1"])[0] != "0",
        include_revision=qs.get("include_revision", ["1"])[0] != "0",
        include_platform=qs.get("include_platform", ["0"])[0] != "0",
        include_sha=qs.get("include_sha", ["0"])[0] != "0",
        sha_length=min(40, max(4, int(qs.get("sha_length", ["8"])[0]))),
    )


def _repo_for_path(
    path_str: str,
    repository: LibraryRepository,
    repository_android: LibraryRepository,
    config: AppConfig,
) -> LibraryRepository:
    """Return the correct repository based on whether path_str falls under library_root (PC) or not (Android).

    Normalizes path separators before comparison so that forward-slash and
    backslash variants of the same Windows path match correctly.
    """
    import os as _os

    if not path_str:
        return repository
    lib_root_raw = str(config.library_root or "")
    if not lib_root_raw:
        return repository

    def _norm_lower(p: str) -> str:
        return p.replace("/", _os.sep).replace("\\", _os.sep).lower().rstrip(_os.sep)

    lib_root_norm = _norm_lower(lib_root_raw)
    path_norm = _norm_lower(path_str)
    if path_norm.startswith(lib_root_norm):
        return repository
    return repository_android
