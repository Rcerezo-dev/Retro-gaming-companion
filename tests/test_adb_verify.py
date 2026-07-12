"""Tests de la verificación MD5 post-transferencia (AUD-2).

Transporte fake: se sobreescriben ``_run``/``_shell`` para simular el
dispositivo sin ADB real.
"""

from __future__ import annotations

import hashlib
import sqlite3
import subprocess

import pytest

from rom_manager.sync.adb_transport import AdbTransport, AdbVerifyError

CONTENT = b"save data"
GOOD_MD5 = hashlib.md5(CONTENT).hexdigest()
BAD_MD5 = "0" * 32


class FakeTransport(AdbTransport):
    """Simula pull/push: escribe/lee archivos locales y responde md5sum."""

    def __init__(self, *, remote_md5: str, pulled_content: bytes = CONTENT):
        super().__init__("adb", "FAKE")
        self.remote_md5 = remote_md5
        self.pulled_content = pulled_content
        self.shell_calls: list[str] = []

    def _run(self, *args, timeout=None):
        if args[0] == "pull":
            # adb pull escribe el destino
            from pathlib import Path

            Path(args[2]).write_bytes(self.pulled_content)
            return subprocess.CompletedProcess(args, 0, stdout=b"", stderr=b"")
        if args[0] == "push":
            return subprocess.CompletedProcess(args, 0, stdout=b"", stderr=b"")
        if args[0] == "shell":
            self.shell_calls.append(" ".join(args[1:]))
            cmd = args[1]
            if cmd.startswith("md5sum"):
                out = f"{self.remote_md5}  /device/file.srm\n"
            elif cmd.startswith("stat"):
                out = f"{len(self.pulled_content)}\n"
            else:
                out = ""
            return subprocess.CompletedProcess(args, 0, stdout=out.encode(), stderr=b"")
        return subprocess.CompletedProcess(args, 0, stdout=b"", stderr=b"")


def test_pull_verify_ok(tmp_path):
    t = FakeTransport(remote_md5=GOOD_MD5)
    dst = tmp_path / "sub" / "file.srm"
    t.pull("/device/file.srm", dst, verify=True)
    assert dst.read_bytes() == CONTENT
    assert t.last_verified is True
    assert not dst.with_name("file.srm.part").exists()


def test_pull_verify_mismatch_leaves_destination_untouched(tmp_path):
    t = FakeTransport(remote_md5=BAD_MD5)
    dst = tmp_path / "file.srm"
    dst.write_bytes(b"previous good save")  # el save bueno que ya estaba
    with pytest.raises(AdbVerifyError):
        t.pull("/device/file.srm", dst, verify=True)
    assert dst.read_bytes() == b"previous good save"  # intacto
    assert not dst.with_name("file.srm.part").exists()  # .part limpiado


def test_pull_md5sum_unavailable_does_not_block(tmp_path):
    t = FakeTransport(remote_md5="md5sum: not found")
    dst = tmp_path / "file.srm"
    t.pull("/device/file.srm", dst, verify=True)
    assert dst.read_bytes() == CONTENT  # la transferencia se completa
    assert t.last_verified is None  # pero queda sin verificar


def test_push_verify_ok(tmp_path):
    t = FakeTransport(remote_md5=GOOD_MD5)
    src = tmp_path / "file.srm"
    src.write_bytes(CONTENT)
    t.push(src, "/device/file.srm", verify=True)
    assert t.last_verified is True


def test_push_verify_mismatch_raises(tmp_path):
    t = FakeTransport(remote_md5=BAD_MD5)
    src = tmp_path / "file.srm"
    src.write_bytes(CONTENT)
    with pytest.raises(AdbVerifyError):
        t.push(src, "/device/file.srm", verify=True)


def test_pull_without_verify_keeps_old_behaviour(tmp_path):
    t = FakeTransport(remote_md5=BAD_MD5)  # md5 malo, pero no se consulta
    dst = tmp_path / "file.srm"
    t.pull("/device/file.srm", dst, verify=False)
    assert dst.read_bytes() == CONTENT
    assert t.last_verified is None
    assert not any(c.startswith("md5sum") for c in t.shell_calls)


def test_sync_log_verified_column_migrated():
    """Una BD vieja sin la columna verified la gana al inicializar (AUD-2)."""
    from rom_manager.database.schema import initialize_database

    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE save_sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            local_path TEXT NOT NULL, remote_path TEXT NOT NULL,
            direction TEXT NOT NULL, local_mtime TEXT, remote_mtime TEXT,
            result TEXT NOT NULL, message TEXT, created_at TEXT NOT NULL
        )
        """
    )
    initialize_database(conn)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(save_sync_log)")}
    assert "verified" in cols


def test_log_sync_event_writes_verified():
    from rom_manager.sync.sync_log import (
        adb_sync_log_entry,
        ensure_sync_log_schema,
        log_sync_event,
    )

    conn = sqlite3.connect(":memory:")
    ensure_sync_log_schema(conn)
    entry = adb_sync_log_entry("C:/saves/a.srm", "/dev/a.srm", "upload", "ok", None, True)
    log_sync_event(conn, **entry)
    row = conn.execute("SELECT result, verified FROM save_sync_log").fetchone()
    assert row == ("ok", 1)
