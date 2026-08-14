"""CABLE-ROM-FIX-2: espacio libre en el dispositivo antes de empujar ROMs."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from rom_manager.sync.adb_transport import AdbTransport


def _proc(stdout: bytes) -> MagicMock:
    p = MagicMock()
    p.stdout = stdout
    p.returncode = 0
    return p


def test_free_bytes_parses_df_available_column():
    t = AdbTransport("adb", "serial1")
    df_out = (
        b"Filesystem     1K-blocks      Used Available Use% Mounted on\n"
        b"/dev/fuse      488610816 406642944  81967872  84% /storage/521D-04EA\n"
    )
    with patch("subprocess.run", return_value=_proc(df_out)):
        assert t.free_bytes("/storage/521D-04EA") == 81967872 * 1024


def test_free_bytes_raises_on_unexpected_output():
    t = AdbTransport("adb", "serial1")
    with patch("subprocess.run", return_value=_proc(b"df: not found\n")):
        with pytest.raises(RuntimeError, match="espacio libre"):
            t.free_bytes("/storage/521D-04EA")
