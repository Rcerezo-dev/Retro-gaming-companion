"""AUD-2 — Verificación post-transferencia en el sync ADB.

Simula un dispositivo ADB (subprocess.run falso sobre un dict) y comprueba que
una transferencia corrupta (bytes truncados) se detecta por MD5 y NO se
propaga: en pull el archivo previo del PC queda intacto; en push el archivo
corrupto se elimina del dispositivo. También cubre la columna ``verified`` de
``save_sync_log`` (migración + escritura).
"""

from __future__ import annotations

import shlex
import sqlite3
import subprocess
from hashlib import md5
from pathlib import Path

import pytest

from rom_manager.sync import adb_transport as at
from rom_manager.sync.sync_log import ensure_sync_log_schema, log_sync_event


class _FakeDevice:
    """In-memory 'device': files dict + optional corruption on transfer."""

    def __init__(self):
        self.files: dict[str, bytes] = {}
        self.corrupt_pull = False  # truncate bytes written to the PC
        self.corrupt_push = False  # truncate bytes stored on the device

    def run(self, cmd, capture_output=True, timeout=None):
        rest = cmd[3:]  # strip [adb, -s, serial]
        out = b""
        rc = 0
        if rest[0] == "pull":
            src, dst = rest[1], rest[2]
            data = self.files[src]
            Path(dst).write_bytes(data[: len(data) // 2] if self.corrupt_pull else data)
        elif rest[0] == "push":
            src, dst = rest[1], rest[2]
            data = Path(src).read_bytes()
            self.files[dst] = data[: len(data) // 2] if self.corrupt_push else data
        elif rest[0] == "shell":
            args = shlex.split(rest[1])
            if args[0] == "md5sum":
                out = f"{md5(self.files[args[1]]).hexdigest()}  {args[1]}\n".encode()
            elif args[0] == "stat":
                out = str(len(self.files[args[-1]])).encode()
            elif args[0] == "rm":
                del self.files[args[1]]
            # mkdir -p → no-op
        return subprocess.CompletedProcess(cmd, rc, stdout=out, stderr=b"")


@pytest.fixture()
def device(monkeypatch):
    dev = _FakeDevice()
    monkeypatch.setattr(at.subprocess, "run", dev.run)
    return dev


def _transport() -> at.AdbTransport:
    return at.AdbTransport("adb", "SERIAL")


def test_pull_verified_ok(device, tmp_path) -> None:
    device.files["/sd/saves/mario.srm"] = b"SAVEDATA-OK"
    dst = tmp_path / "mario.srm"
    size = _transport().pull("/sd/saves/mario.srm", dst, verify=True)
    assert dst.read_bytes() == b"SAVEDATA-OK"
    assert size == len(b"SAVEDATA-OK")
    assert not dst.with_name("mario.srm.part").exists()


def test_pull_corruption_detected_and_not_propagated(device, tmp_path) -> None:
    device.files["/sd/saves/mario.srm"] = b"SAVEDATA-NUEVA"
    dst = tmp_path / "mario.srm"
    dst.write_bytes(b"SAVE-PREVIO-DEL-PC")  # el save que NO debe perderse
    device.corrupt_pull = True

    with pytest.raises(OSError, match="MD5"):
        _transport().pull("/sd/saves/mario.srm", dst, verify=True)

    assert dst.read_bytes() == b"SAVE-PREVIO-DEL-PC"  # intacto
    assert not dst.with_name("mario.srm.part").exists()  # sin restos


def test_pull_without_verify_keeps_old_behavior(device, tmp_path) -> None:
    device.files["/sd/saves/mario.srm"] = b"SAVEDATA"
    device.corrupt_pull = True  # sin verify no se detecta (comportamiento previo)
    dst = tmp_path / "mario.srm"
    _transport().pull("/sd/saves/mario.srm", dst)
    assert dst.read_bytes() == b"SAVE"


def test_push_verified_ok(device, tmp_path) -> None:
    src = tmp_path / "zelda.sav"
    src.write_bytes(b"ZELDA-SAVE")
    _transport().push(src, "/sd/saves/zelda.sav", verify=True)
    assert device.files["/sd/saves/zelda.sav"] == b"ZELDA-SAVE"


def test_push_corruption_deletes_remote_and_raises(device, tmp_path) -> None:
    src = tmp_path / "zelda.sav"
    src.write_bytes(b"ZELDA-SAVE")
    device.corrupt_push = True

    with pytest.raises(OSError, match="MD5"):
        _transport().push(src, "/sd/saves/zelda.sav", verify=True)

    # el archivo corrupto no queda en el dispositivo (su mtime nuevo propagaría
    # la corrupción de vuelta al PC en el siguiente sync "newest")
    assert "/sd/saves/zelda.sav" not in device.files
    assert src.read_bytes() == b"ZELDA-SAVE"  # el original del PC intacto


def test_sync_log_verified_column_and_migration(tmp_path) -> None:
    conn = sqlite3.connect(tmp_path / "t.db")
    # tabla antigua sin la columna → la migración la añade
    conn.execute(
        "CREATE TABLE save_sync_log (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "local_path TEXT NOT NULL, remote_path TEXT NOT NULL, direction TEXT NOT NULL, "
        "local_mtime TEXT, remote_mtime TEXT, result TEXT NOT NULL, message TEXT, "
        "created_at TEXT NOT NULL)"
    )
    ensure_sync_log_schema(conn)
    log_sync_event(
        conn,
        local_path="C:/pc/mario.srm",
        remote_path="dropbox:/saves/mario.srm",
        direction="upload",
        local_mtime=None,
        remote_mtime=None,
        result="ok",
        created_at="2026-07-12T10:00:00",
        verified=True,
    )
    row = conn.execute("SELECT result, verified FROM save_sync_log").fetchone()
    assert row == ("ok", 1)
    conn.close()
