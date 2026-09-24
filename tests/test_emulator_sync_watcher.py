"""EMU-SYNC-WATCH-1: lanzar un cloud sync cuando un emulador vigilado se cierra."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from rom_manager.web.daemons import _closed_watched_processes, _list_running_process_names


def test_closed_watched_processes_detects_exit() -> None:
    previous = {"retroarch.exe", "explorer.exe", "pcsx2-qt.exe"}
    current = {"explorer.exe", "pcsx2-qt.exe"}
    watched = {"retroarch.exe", "dolphin.exe"}
    assert _closed_watched_processes(previous, current, watched) == {"retroarch.exe"}


def test_closed_watched_processes_ignores_unwatched_exits() -> None:
    previous = {"explorer.exe", "notepad.exe"}
    current = {"explorer.exe"}
    watched = {"retroarch.exe"}
    assert _closed_watched_processes(previous, current, watched) == set()


def test_closed_watched_processes_empty_when_nothing_closed() -> None:
    previous = {"retroarch.exe"}
    current = {"retroarch.exe"}
    watched = {"retroarch.exe"}
    assert _closed_watched_processes(previous, current, watched) == set()


def test_closed_watched_processes_new_process_is_not_a_close() -> None:
    """A process appearing (not disappearing) must never count as "closed"."""
    previous = {"explorer.exe"}
    current = {"explorer.exe", "retroarch.exe"}
    watched = {"retroarch.exe"}
    assert _closed_watched_processes(previous, current, watched) == set()


def test_list_running_process_names_parses_tasklist_csv() -> None:
    fake_stdout = (
        '"System Idle Process","0","Services","0","8 K"\r\n'
        '"RetroArch.exe","12345","Console","1","150,000 K"\r\n'
        '"pcsx2-qt.exe","999","Console","1","1,024 K"\r\n'
    )
    fake_result = MagicMock(stdout=fake_stdout)
    with patch("subprocess.run", return_value=fake_result) as mock_run:
        names = _list_running_process_names()
    mock_run.assert_called_once()
    assert names == {"system idle process", "retroarch.exe", "pcsx2-qt.exe"}


def test_list_running_process_names_returns_empty_set_on_failure() -> None:
    with patch("subprocess.run", side_effect=OSError("tasklist not found")):
        assert _list_running_process_names() == set()
