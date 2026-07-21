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

import hashlib
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


def _md5_local(path: Path) -> str:
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, "md5").hexdigest()


def should_verify(name: str, verify_exts: frozenset[str]) -> bool:
    """CABLE-UX-9e: verify MD5 only for save-type files — ROMs are too big to
    hash on every sync. Shared by manual (`sync_cable.py`) and daemon
    (`cable_sync_daemon.py`) ADB transfers so the policy lives in one place.
    """
    return Path(name).suffix.lower() in verify_exts


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


def resolve_single_device_transport(adb_path: str) -> AdbTransport | None:
    """TABS-FIX-1a: auto-detect the connected device for on-device duplicate
    deletion. Returns None (caller falls back to the explicit "conecta el
    dispositivo" message) when zero or more than one ready device is
    connected — with several devices there's no way to know which one a
    stale DB row's ``/storage/...`` path actually refers to.
    """
    try:
        devices = [d for d in list_devices(adb_path, timeout=5) if d.ready]
    except RuntimeError:
        return None
    if len(devices) != 1:
        return None
    return AdbTransport(adb_path, devices[0].serial)


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

    def device_epoch(self) -> int:
        """Return the device clock as a unix timestamp (``date +%s``). AUD-1."""
        out = self._shell("date", "+%s", timeout=10).strip()
        try:
            return int(out)
        except ValueError as exc:
            raise RuntimeError(f"No se pudo leer el reloj del dispositivo: {out!r}") from exc

    def file_exists(self, android_path: str) -> bool:
        out = self._shell(
            f"test -e {shlex.quote(android_path)} && echo EXISTS || echo GONE"
        ).strip()
        return "EXISTS" in out and "GONE" not in out

    def remove(self, android_path: str) -> None:
        """Delete a single file on the device (TABS-FIX-1a).

        ``rm`` exit codes over ``adb shell`` aren't reliable enough to trust
        blindly before touching the DB row — verify the file is actually gone
        afterwards, and raise if it isn't.
        """
        self._shell(f"rm -f {shlex.quote(android_path)}")
        if self.file_exists(android_path):
            raise RuntimeError(f"No se pudo borrar {android_path} en el dispositivo")

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

    # ── hashing (AUD-2) ───────────────────────────────────────────────────────

    def md5(self, android_path: str, *, timeout: int = 300) -> str:
        """MD5 of a file on the device (``md5sum``)."""
        out = self._shell(f"md5sum {shlex.quote(android_path)}", timeout=timeout).strip()
        token = out.split()[0].lower() if out.split() else ""
        if len(token) != 32 or not all(c in "0123456789abcdef" for c in token):
            raise OSError(f"md5sum falló en el dispositivo para {android_path}: {out!r}")
        return token

    # ── transfer ──────────────────────────────────────────────────────────────

    def pull(
        self,
        android_src: str,
        local_dst: Path,
        *,
        dry_run: bool = False,
        verify: bool = False,
    ) -> int:
        """Pull a single file from device to PC. Returns file size in bytes.

        With ``verify=True`` (AUD-2) the file lands in a ``.part`` next to
        *local_dst* and only replaces it if the MD5 matches the device's copy —
        a corrupt transfer never overwrites a save in the library.
        """
        if not dry_run:
            local_dst.parent.mkdir(parents=True, exist_ok=True)
            target = local_dst.with_name(local_dst.name + ".part") if verify else local_dst
            r = self._run("pull", android_src, str(target))
            if r.returncode != 0:
                target.unlink(missing_ok=True)
                err = (r.stderr or r.stdout or b"").decode(errors="replace").strip()
                raise OSError(f"adb pull falló: {err}")
            if verify:
                try:
                    local_md5 = _md5_local(target)
                    remote_md5 = self.md5(android_src)
                    if local_md5 != remote_md5:
                        raise OSError(
                            f"verificación MD5 falló tras pull de {android_src} "
                            f"(local {local_md5} != dispositivo {remote_md5}) — "
                            "el archivo previo se conserva intacto"
                        )
                except OSError:
                    target.unlink(missing_ok=True)
                    raise
                target.replace(local_dst)
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
        verify: bool = False,
    ) -> int:
        """Push a single file from PC to device. Returns file size in bytes.

        With ``verify=True`` (REV43-1) the file lands in ``<android_dst>.part``
        and only replaces the real destination (atomic ``mv`` on the device)
        once its MD5 matches the local file — mirrors ``pull()``'s staging so
        a corrupt/truncated push never clobbers whatever save was already on
        the device before the transfer is confirmed good.
        """
        size = local_src.stat().st_size if local_src.exists() else 0
        if not dry_run:
            parent = str(PurePosixPath(android_dst).parent)
            self._shell(f"mkdir -p {shlex.quote(parent)}")
            target = f"{android_dst}.part" if verify else android_dst
            r = self._run("push", str(local_src), target)
            if r.returncode != 0:
                if verify:
                    self._shell(f"rm -f {shlex.quote(target)}")
                err = (r.stderr or r.stdout or b"").decode(errors="replace").strip()
                raise OSError(f"adb push falló: {err}")
            if verify:
                try:
                    local_md5 = _md5_local(local_src)
                    remote_md5 = self.md5(target)
                    if remote_md5 != local_md5:
                        raise OSError(
                            f"verificación MD5 falló tras push a {android_dst} "
                            f"(dispositivo {remote_md5} != local {local_md5}) — "
                            "el destino original en el dispositivo se conserva intacto"
                        )
                except OSError:
                    self._shell(f"rm -f {shlex.quote(target)}")
                    raise
                self._shell(f"mv -f {shlex.quote(target)} {shlex.quote(android_dst)}")
        return size
