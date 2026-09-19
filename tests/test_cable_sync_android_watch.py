"""CABLE-SYNC-WATCH-1: lanzar un cable-sync cuando un emulador Android vigilado
se cierra mientras la Anbernic está conectada por USB.

``_closed_watched_processes`` (la lógica de detección de cierre en sí) ya está
cubierta por ``test_emulator_sync_watcher.py`` — es la misma función genérica,
reutilizada aquí. Esto solo cubre lo específico de Android: parsear
``adb shell ps -A``.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from rom_manager.web.cable_sync_daemon import _list_running_android_packages

_FAKE_PS_OUTPUT = (
    "USER           PID  PPID     VSZ    RSS WCHAN            ADDR S NAME\n"
    "root             1     0 10910976  3912 0                   0 S init\n"
    "u0_a123      12345   567  2048000 150000 0                   0 S com.retroarch\n"
    "u0_a456      12399   567  1048000  80000 0                   0 S xyz.aethersx2.android\n"
)


def test_list_running_android_packages_parses_ps_output() -> None:
    fake_result = MagicMock(stdout=_FAKE_PS_OUTPUT)
    with patch("subprocess.run", return_value=fake_result) as mock_run:
        names = _list_running_android_packages("tools/adb.exe", "RG556006101273")
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args == ["tools/adb.exe", "-s", "RG556006101273", "shell", "ps", "-A"]
    assert names == {"init", "com.retroarch", "xyz.aethersx2.android"}


def test_list_running_android_packages_skips_header_row() -> None:
    fake_result = MagicMock(stdout=_FAKE_PS_OUTPUT)
    with patch("subprocess.run", return_value=fake_result):
        names = _list_running_android_packages("adb", "serial")
    assert "NAME" not in names


def test_list_running_android_packages_returns_empty_set_on_failure() -> None:
    with patch("subprocess.run", side_effect=OSError("adb not found")):
        assert _list_running_android_packages("adb", "serial") == set()


def test_list_running_android_packages_empty_output() -> None:
    fake_result = MagicMock(stdout="")
    with patch("subprocess.run", return_value=fake_result):
        assert _list_running_android_packages("adb", "serial") == set()
