from __future__ import annotations

from unittest import mock

from rom_manager.utils import notifier


def test_ps_escape_doubles_single_quotes() -> None:
    # Single quotes are doubled and the whole value is wrapped in quotes,
    # so a malicious title cannot break out of the PowerShell string literal.
    assert notifier._ps_escape("it's") == "'it''s'"
    assert notifier._ps_escape("plain") == "'plain'"
    assert notifier._ps_escape("'; rm -rf") == "'''; rm -rf'"


def test_notify_is_noop_off_windows() -> None:
    with (
        mock.patch.object(notifier.sys, "platform", "linux"),
        mock.patch.object(notifier.subprocess, "Popen") as popen,
    ):
        notifier.notify("Title", "Body")
        popen.assert_not_called()


def test_notify_spawns_powershell_on_windows() -> None:
    with (
        mock.patch.object(notifier.sys, "platform", "win32"),
        mock.patch.object(notifier.subprocess, "Popen") as popen,
    ):
        notifier.notify("Hola", "Sync completado")
        popen.assert_called_once()
        argv = popen.call_args.args[0]
        assert argv[0] == "powershell.exe"
        # The escaped title/body must reach the script body.
        script = argv[-1]
        assert "'Hola'" in script
        assert "'Sync completado'" in script


def test_notify_swallows_popen_failure() -> None:
    # Notifications are best-effort: a failure to spawn must never propagate.
    with (
        mock.patch.object(notifier.sys, "platform", "win32"),
        mock.patch.object(notifier.subprocess, "Popen", side_effect=OSError("boom")),
    ):
        notifier.notify("Title", "Body")  # must not raise
