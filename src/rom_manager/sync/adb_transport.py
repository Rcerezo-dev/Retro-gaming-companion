"""ADB transport for ROM/save sync between PC and Android device.

Uses the ``adb`` CLI tool (Android Platform Tools) to transfer files without
needing the device to be mounted as a drive letter.

Requires:
  - adb.exe in tools/ or in PATH (download from developer.android.com/tools/releases/platform-tools)
  - USB Debugging enabled on the Android device:
      Settings → About phone → tap Build number 7 times
      Settings → Developer options → USB Debugging ✓
  - Device connected via USB cable (any mode works; "No transferir datos" is fine)
  - Accept the "Allow USB Debugging" prompt on the device
"""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(slots=True)
class AdbDevice:
    serial: str
    state: str  # "device" | "unauthorized" | "offline" | "no permissions"
    model: str = ""
    product: str = ""

    @property
    def ready(self) -> bool:
        return self.state == "device"

    @property
    def display(self) -> str:
        parts = [self.serial]
        if self.model:
            parts.append(self.model)
        if not self.ready:
            parts.append(f"[{self.state}]")
        return " — ".join(parts)


@dataclass(slots=True)
class AdbFileInfo:
    android_path: str  # full absolute Android path
    size: int  # bytes
    mtime: float  # unix timestamp (from stat)


def list_devices(adb_path: str, *, timeout: int = 10) -> list[AdbDevice]:
    """Return all devices visible to adb."""
    try:
        r = subprocess.run(
            [adb_path, "devices", "-l"],
            capture_output=True,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"adb no encontrado o no respondió: {exc}") from exc

    lines = r.stdout.decode(errors="replace").splitlines()
    devices: list[AdbDevice] = []
    for line in lines[1:]:  # skip "List of devices attached"
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial = parts[0]
        state = parts[1]
        model = ""
        product = ""
        for token in parts[2:]:
            if token.startswith("model:"):
                model = token[6:].replace("_", " ")
            elif token.startswith("product:"):
                product = token[8:]
        devices.append(AdbDevice(serial=serial, state=state, model=model, product=product))
    return devices


class AdbTransport:
    """File-transfer operations against a single ADB device."""

    DEFAULT_ANDROID_ROOT = "/storage/emulated/0"

    def __init__(self, adb_path: str, serial: str, *, timeout: int = 60):
        self.adb_path = adb_path
        self.serial = serial
        self.timeout = timeout

    # ── low-level ─────────────────────────────────────────────────────────────

    def _run(self, *args: str, timeout: int | None = None) -> subprocess.CompletedProcess:
        cmd = [self.adb_path, "-s", self.serial] + list(args)
        return subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout or self.timeout,
        )

    def _shell(self, *args: str, timeout: int | None = None) -> str:
        r = self._run("shell", *args, timeout=timeout)
        return r.stdout.decode(errors="replace")

    # ── device / path probing ─────────────────────────────────────────────────

    def test_path(self, android_path: str) -> dict:
        """Check whether *android_path* exists and is a directory on the device."""
        out = self._shell(f"test -d {shlex.quote(android_path)} && echo DIR || echo NODIR").strip()
        if "DIR" in out and "NO" not in out:
            # Count top-level entries
            ls_out = self._shell(f"ls {shlex.quote(android_path)}").strip()
            entries = len([ln for ln in ls_out.splitlines() if ln.strip()]) if ls_out else 0
            return {"accessible": True, "path": android_path, "entries": entries}
        return {
            "accessible": False,
            "error": f"La ruta {android_path!r} no existe en el dispositivo",
        }

    # ── file listing ──────────────────────────────────────────────────────────

    def ls_recursive(
        self,
        android_path: str,
        *,
        wanted_extensions: frozenset[str] | None = None,
        exclude_hidden: bool = True,
        timeout: int = 120,
    ) -> list[AdbFileInfo]:
        """Return all files under *android_path* with size and mtime.

        Uses ``find … -exec stat -c '%n|%s|%Y' {} +`` — single round-trip.
        Falls back to a slower path if the device's toybox doesn't support it.
        """
        find_cmd = f"find {shlex.quote(android_path)} -type f -exec stat -c '%n|%s|%Y' {{}} +"
        out = self._shell(find_cmd, timeout=timeout)

        results: list[AdbFileInfo] = []
        for line in out.splitlines():
            line = line.strip()
            if not line or line.startswith("find:") or line.startswith("stat:"):
                continue
            parts = line.rsplit("|", 2)
            if len(parts) != 3:
                continue
            path_str, size_str, mtime_str = parts
            if exclude_hidden and any(seg.startswith(".") for seg in path_str.split("/")):
                continue
            if wanted_extensions is not None:
                suffix = PurePosixPath(path_str).suffix.lower()
                if suffix not in wanted_extensions:
                    continue
            try:
                results.append(
                    AdbFileInfo(
                        android_path=path_str,
                        size=int(size_str),
                        mtime=float(mtime_str),
                    )
                )
            except ValueError:
                continue
        return results

    # ── transfer ──────────────────────────────────────────────────────────────

    def pull(
        self,
        android_src: str,
        local_dst: Path,
        *,
        dry_run: bool = False,
    ) -> int:
        """Pull a single file from device to PC. Returns file size in bytes."""
        if not dry_run:
            local_dst.parent.mkdir(parents=True, exist_ok=True)
            r = self._run("pull", android_src, str(local_dst))
            if r.returncode != 0:
                err = (r.stderr or r.stdout or b"").decode(errors="replace").strip()
                raise OSError(f"adb pull falló: {err}")
        # Return size (approximate from listing, or stat after pull)
        try:
            size_str = self._shell(f"stat -c '%s' {shlex.quote(android_src)}").strip()
            return int(size_str)
        except (ValueError, OSError):
            return 0

    def push(
        self,
        local_src: Path,
        android_dst: str,
        *,
        dry_run: bool = False,
    ) -> int:
        """Push a single file from PC to device. Returns file size in bytes."""
        size = local_src.stat().st_size if local_src.exists() else 0
        if not dry_run:
            parent = str(PurePosixPath(android_dst).parent)
            self._shell(f"mkdir -p {shlex.quote(parent)}")
            r = self._run("push", str(local_src), android_dst)
            if r.returncode != 0:
                err = (r.stderr or r.stdout or b"").decode(errors="replace").strip()
                raise OSError(f"adb push falló: {err}")
        return size
