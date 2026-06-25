"""PHASE6-3b: download a GitHub release installer and hand off to it.

Only meaningful for frozen (PyInstaller) builds on Windows — running from
source has no executable to replace, so callers must check :func:`is_frozen`
before offering this flow.
"""

from __future__ import annotations

import subprocess
import sys
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

_TIMEOUT = 30
_CHUNK_SIZE = 1 << 16  # 64 KiB


def is_frozen() -> bool:
    """True when running from a PyInstaller-built executable."""
    return bool(getattr(sys, "frozen", False))


def find_update_asset(assets: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick the Windows installer asset from a release's asset list.

    Prefers a name containing "setup" (the Inno Setup convention used by
    PHASE6-2a); falls back to any other ``.exe`` asset. Returns ``None`` if
    the release has no executable attached.
    """
    exes = [a for a in assets if a.get("name", "").lower().endswith(".exe")]
    if not exes:
        return None
    for asset in exes:
        if "setup" in asset["name"].lower():
            return asset
    return exes[0]


def download_update(
    url: str,
    dest_dir: Path,
    filename: str,
    *,
    on_progress: Callable[[int, int], None] | None = None,
) -> Path:
    """Download *url* into ``dest_dir/filename``, reporting progress as it goes.

    Writes to a ``.part`` sibling first and renames on completion, so a
    half-downloaded file is never mistaken for a finished one. Network and
    filesystem errors propagate — callers decide how to report them.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    tmp = dest.with_name(dest.name + ".part")

    request = urllib.request.Request(url, headers={"User-Agent": "RetroVault"})
    with urllib.request.urlopen(request, timeout=_TIMEOUT) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        done = 0
        with tmp.open("wb") as f:
            while True:
                chunk = resp.read(_CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if on_progress:
                    on_progress(done, total)

    tmp.replace(dest)
    return dest


def launch_installer(installer_path: Path) -> None:
    """Launch *installer_path* detached from the current process.

    The caller must shut the app down afterwards so the installer can
    overwrite the running executable.
    """
    if sys.platform == "win32":
        detached = getattr(subprocess, "DETACHED_PROCESS", 0)
        new_group = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen([str(installer_path)], creationflags=detached | new_group, close_fds=True)
    else:
        subprocess.Popen([str(installer_path)], close_fds=True)
