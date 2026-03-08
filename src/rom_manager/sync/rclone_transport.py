from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class RemoteEntry:
    relative: str       # path relative to the remote root
    mtime: datetime     # UTC
    size: int


class RcloneError(RuntimeError):
    pass


class RcloneTransport:
    """Thin wrapper around the rclone CLI binary."""

    def __init__(self, rclone: str = "rclone") -> None:
        self.rclone = rclone

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_remote(self, remote_root: str) -> list[RemoteEntry]:
        """Return all files under *remote_root* as RemoteEntry objects."""
        result = self._run(["lsjson", "--recursive", "--no-modtime-truncate", remote_root])
        entries: list[RemoteEntry] = []
        for item in json.loads(result):
            if item.get("IsDir"):
                continue
            entries.append(
                RemoteEntry(
                    relative=item["Path"].replace("\\", "/"),
                    mtime=_parse_rclone_time(item["ModTime"]),
                    size=int(item["Size"]),
                )
            )
        return entries

    def upload(self, local_path: Path, remote_root: str, relative: str) -> None:
        """Copy *local_path* to *remote_root*/*relative*."""
        remote_dest = f"{remote_root.rstrip('/')}/{relative}"
        self._run(["copyto", str(local_path), remote_dest])

    def download(self, remote_root: str, relative: str, local_path: Path) -> None:
        """Copy *remote_root*/*relative* to *local_path*."""
        remote_src = f"{remote_root.rstrip('/')}/{relative}"
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self._run(["copyto", remote_src, str(local_path)])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run(self, args: list[str]) -> str:
        cmd = [self.rclone, *args]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except FileNotFoundError:
            raise RcloneError(
                f"rclone binary not found: '{self.rclone}'. "
                "Install rclone and ensure it is in PATH, or pass --rclone <path>."
            )
        if proc.returncode != 0:
            raise RcloneError(
                f"rclone exited with code {proc.returncode}:\n{proc.stderr.strip()}"
            )
        return proc.stdout


def _parse_rclone_time(raw: str) -> datetime:
    """Parse the RFC-3339 / ISO-8601 timestamp returned by rclone lsjson.

    rclone uses nanosecond precision, e.g. '2024-01-15T10:30:00.123456789+00:00'.
    We truncate to microseconds for stdlib compatibility.
    """
    # Truncate sub-microsecond digits: keep at most 6 decimal places.
    if "." in raw:
        base, frac_and_tz = raw.split(".", 1)
        # Split fractional seconds from timezone offset
        for sep in ("+", "-", "Z"):
            if sep in frac_and_tz:
                idx = frac_and_tz.index(sep)
                frac = frac_and_tz[:idx][:6]
                tz = frac_and_tz[idx:]
                raw = f"{base}.{frac}{tz}"
                break
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).replace(tzinfo=timezone.utc)
