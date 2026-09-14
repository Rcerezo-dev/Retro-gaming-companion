"""ADB-TIMEOUT-1: push/pull must scale their subprocess timeout with file
size instead of using the flat 60s default meant for quick shell commands.

Confirmed live 2026-09-13: a 787 MB Dreamcast .cdi hit the 60s default and
aborted a whole cable-sync batch mid-transfer, even though the same file
completed fine moments later with a real ADB transfer at ~20 MB/s.
"""

from __future__ import annotations

import shlex
from hashlib import md5
from pathlib import Path

import pytest

from rom_manager.sync import adb_transport as at


class _RecordingDevice:
    """Fake device: stores files, and records the timeout passed to each
    push/pull subprocess.run call so tests can assert it scales with size."""

    def __init__(self):
        self.files: dict[str, bytes] = {}
        self.timeouts_seen: list[tuple[str, int | None]] = []

    def run(self, cmd, capture_output=True, timeout=None):
        rest = cmd[3:]  # strip [adb, -s, serial]
        out = b""
        if rest[0] == "push":
            src, dst = rest[1], rest[2]
            self.timeouts_seen.append(("push", timeout))
            self.files[dst] = Path(src).read_bytes()
        elif rest[0] == "pull":
            src, dst = rest[1], rest[2]
            self.timeouts_seen.append(("pull", timeout))
            Path(dst).write_bytes(self.files[src])
        elif rest[0] == "shell":
            args = shlex.split(rest[1])
            paths = [a for a in args[1:] if not a.startswith("-")]
            if args and args[0] == "stat":
                out = str(len(self.files[paths[-1]])).encode()
            elif args and args[0] == "md5sum":
                out = f"{md5(self.files[paths[0]]).hexdigest()}  {paths[0]}\n".encode()
            # mkdir -p → no-op
        import subprocess as _subprocess

        return _subprocess.CompletedProcess(cmd, 0, stdout=out, stderr=b"")


@pytest.fixture()
def device(monkeypatch):
    dev = _RecordingDevice()
    monkeypatch.setattr(at.subprocess, "run", dev.run)
    return dev


def _transport() -> at.AdbTransport:
    return at.AdbTransport("adb", "SERIAL")


def test_transfer_timeout_scales_with_size() -> None:
    small = at._transfer_timeout(1024)
    large = at._transfer_timeout(800 * 1024 * 1024)  # ~800 MB, the real incident size
    huge = at._transfer_timeout(8 * 1024 * 1024 * 1024)  # ~8 GB, a real PS2 ISO seen live
    assert small == 120  # floor, never shorter than the old default's ballpark
    assert large > 400  # comfortably above the 60s that aborted the real transfer
    assert huge > large > small


def test_push_uses_size_scaled_timeout_not_flat_default(device, tmp_path) -> None:
    big_file = tmp_path / "game.cdi"
    big_file.write_bytes(b"x" * (5 * 1024 * 1024))  # 5 MB stand-in for a large ROM

    _transport().push(big_file, "/sd/dreamcast/game.cdi")

    assert device.timeouts_seen == [("push", at._transfer_timeout(5 * 1024 * 1024))]
    assert device.timeouts_seen[0][1] > 60


def test_pull_uses_size_scaled_timeout_from_remote_stat(device, tmp_path) -> None:
    data = b"y" * (5 * 1024 * 1024)
    device.files["/sd/saves/game.srm"] = data

    _transport().pull("/sd/saves/game.srm", tmp_path / "game.srm")

    pull_calls = [t for op, t in device.timeouts_seen if op == "pull"]
    assert pull_calls == [at._transfer_timeout(len(data))]
    assert pull_calls[0] > 60


def test_small_file_still_gets_reasonable_floor_timeout(device, tmp_path) -> None:
    tiny = tmp_path / "save.srm"
    tiny.write_bytes(b"tiny save data")

    _transport().push(tiny, "/sd/saves/save.srm")

    assert device.timeouts_seen == [("push", 120)]
