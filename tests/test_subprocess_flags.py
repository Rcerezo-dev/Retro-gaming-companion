"""NO_WINDOW must never crash on import/reference outside Windows — this is
exactly what broke CI (Linux) after EMU-SYNC-WATCH-1 used the raw
``subprocess.CREATE_NO_WINDOW`` attribute directly in several modules."""

from __future__ import annotations

import importlib
import subprocess
import sys


def test_no_window_is_zero_off_windows(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    import rom_manager.utils.subprocess_flags as mod

    importlib.reload(mod)
    try:
        assert mod.NO_WINDOW == 0
    finally:
        importlib.reload(mod)  # restore the real platform-derived value


def test_no_window_matches_create_no_window_on_windows(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)
    import rom_manager.utils.subprocess_flags as mod

    importlib.reload(mod)
    try:
        assert mod.NO_WINDOW == 0x08000000
    finally:
        importlib.reload(mod)


def test_creationflags_zero_is_safe_on_posix_subprocess() -> None:
    """The actual bug: passing creationflags=0 must never raise, unlike a
    real Windows-only flag would on POSIX."""
    result = subprocess.run(
        [sys.executable, "-c", "print('ok')"],
        capture_output=True,
        text=True,
        creationflags=0,
    )
    assert result.stdout.strip() == "ok"
