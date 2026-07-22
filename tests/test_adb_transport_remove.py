"""TABS-FIX-1a: real on-device deletion for duplicates, via ADB.

remove()/file_exists() drive real subprocess calls through AdbTransport._run —
mocked here via subprocess.run. resolve_single_device_transport() covers the
zero/one/many-devices auto-detect used by the duplicates web handler.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from rom_manager.sync.adb_transport import (
    AdbDevice,
    AdbTransport,
    resolve_single_device_transport,
)


def _proc(stdout: bytes) -> MagicMock:
    p = MagicMock()
    p.stdout = stdout
    p.returncode = 0
    return p


class TestFileExists:
    def test_true_when_device_reports_exists(self):
        t = AdbTransport("adb", "serial1")
        with patch("subprocess.run", return_value=_proc(b"EXISTS\n")):
            assert t.file_exists("/storage/emulated/0/roms/gb/dup.gb") is True

    def test_false_when_device_reports_gone(self):
        t = AdbTransport("adb", "serial1")
        with patch("subprocess.run", return_value=_proc(b"GONE\n")):
            assert t.file_exists("/storage/emulated/0/roms/gb/dup.gb") is False


class TestRemove:
    def test_remove_succeeds_when_file_confirmed_gone(self):
        t = AdbTransport("adb", "serial1")
        with patch("subprocess.run", side_effect=[_proc(b""), _proc(b"GONE\n")]) as mock_run:
            t.remove("/storage/emulated/0/roms/gb/dup.gb")
        assert mock_run.call_count == 2  # rm, then the verify test

    def test_remove_raises_when_file_still_there_after_rm(self):
        """rm's own exit code over adb shell isn't trustworthy — the real
        guarantee is the follow-up existence check."""
        t = AdbTransport("adb", "serial1")
        with patch("subprocess.run", side_effect=[_proc(b""), _proc(b"EXISTS\n")]):
            with pytest.raises(RuntimeError, match="No se pudo borrar"):
                t.remove("/storage/emulated/0/roms/gb/dup.gb")


class TestResolveSingleDeviceTransport:
    def test_returns_transport_for_single_ready_device(self):
        with patch(
            "rom_manager.sync.adb_transport.list_devices",
            return_value=[AdbDevice(serial="RG556006101273", state="device")],
        ):
            t = resolve_single_device_transport("adb")
        assert t is not None
        assert t.serial == "RG556006101273"

    def test_returns_none_when_no_device_connected(self):
        with patch("rom_manager.sync.adb_transport.list_devices", return_value=[]):
            assert resolve_single_device_transport("adb") is None

    def test_returns_none_when_multiple_devices_connected(self):
        """Ambiguous: a stale DB row's /storage/... path could belong to
        either device — safer to fall back to the explicit error message."""
        with patch(
            "rom_manager.sync.adb_transport.list_devices",
            return_value=[
                AdbDevice(serial="AAA", state="device"),
                AdbDevice(serial="BBB", state="device"),
            ],
        ):
            assert resolve_single_device_transport("adb") is None

    def test_ignores_not_ready_devices(self):
        with patch(
            "rom_manager.sync.adb_transport.list_devices",
            return_value=[AdbDevice(serial="AAA", state="unauthorized")],
        ):
            assert resolve_single_device_transport("adb") is None

    def test_returns_none_when_adb_unavailable(self):
        with patch(
            "rom_manager.sync.adb_transport.list_devices",
            side_effect=RuntimeError("adb no encontrado"),
        ):
            assert resolve_single_device_transport("adb") is None
