"""CABLE-SYNC-WATCH-1: lanzar un cable-sync cuando un emulador Android vigilado
se cierra mientras la Anbernic está conectada por USB.

``_closed_watched_processes`` (la lógica de detección de cierre en sí) ya está
cubierta por ``test_emulator_sync_watcher.py`` — es la misma función genérica,
reutilizada aquí. Esto solo cubre lo específico de Android: parsear
``adb shell ps -A``.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from rom_manager.web.cable_sync_daemon import _list_running_android_packages, _poll_android_watch

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


def test_list_running_android_packages_returns_none_on_failure() -> None:
    """A probe failure (timeout, adb error) must be distinguishable from a
    successful query that found nothing running — collapsing both into an
    empty set would let a transient ADB hiccup masquerade as "the emulator
    closed" and fire a real cable-sync while it's still open (see
    _auto_sync_loop, which must skip close-detection on None rather than
    treat it as everything having closed)."""
    with patch("subprocess.run", side_effect=OSError("adb not found")):
        assert _list_running_android_packages("adb", "serial") is None


def test_list_running_android_packages_empty_output() -> None:
    fake_result = MagicMock(stdout="")
    with patch("subprocess.run", return_value=fake_result):
        assert _list_running_android_packages("adb", "serial") == set()


# ── _poll_android_watch ──────────────────────────────────────────────────────


def test_poll_android_watch_detects_close() -> None:
    with patch(
        "rom_manager.web.cable_sync_daemon._list_running_android_packages",
        return_value=set(),
    ):
        closed, new_previous = _poll_android_watch(
            "adb", "serial", {"com.retroarch"}, {"com.retroarch"}
        )
    assert closed == {"com.retroarch"}
    assert new_previous == set()


def test_poll_android_watch_probe_failure_reports_no_closure_and_keeps_state() -> None:
    """The exact bug this guards: an ADB probe failure (timeout, error) must
    never be collapsed into "everything closed" — that would fire a real
    cable-sync while the watched emulator is actually still open, risking a
    sync over an unflushed save (CLAUDE.md Pilar 3)."""
    with patch(
        "rom_manager.web.cable_sync_daemon._list_running_android_packages",
        return_value=None,
    ):
        closed, new_previous = _poll_android_watch(
            "adb", "serial", {"com.retroarch"}, {"com.retroarch"}
        )
    assert closed == set()
    assert new_previous == {"com.retroarch"}  # untouched, not reset to empty


def test_poll_android_watch_no_device_resets_state() -> None:
    closed, new_previous = _poll_android_watch("adb", None, {"com.retroarch"}, {"com.retroarch"})
    assert closed == set()
    assert new_previous == set()


def test_poll_android_watch_nothing_watched_resets_state() -> None:
    closed, new_previous = _poll_android_watch("adb", "serial", set(), {"com.retroarch"})
    assert closed == set()
    assert new_previous == set()
