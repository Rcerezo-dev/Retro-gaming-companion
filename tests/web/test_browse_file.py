"""Unit tests for the file-picker handler (HERR-UX-11).

`_browse_file` opens a native tkinter dialog, so we mock tkinter via
``sys.modules`` rather than hitting the real endpoint (which would block on a
GUI dialog and fails on headless CI). Same pattern as test_browse_folder.py.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest import mock

from rom_manager.web.handlers import config as cfg_handler


class _Ctx:
    """Minimal stand-in for the request context: captures the JSON payload."""

    def __init__(self) -> None:
        self.payload: dict | None = None

    def _send_json(self, data: dict) -> None:
        self.payload = data


def _fake_tkinter(askopen_return: str) -> dict[str, types.ModuleType]:
    tk_mod = types.ModuleType("tkinter")
    fd_mod = types.ModuleType("tkinter.filedialog")
    tk_mod.Tk = mock.MagicMock()  # type: ignore[attr-defined]
    fd_mod.askopenfilename = mock.MagicMock(return_value=askopen_return)  # type: ignore[attr-defined]
    tk_mod.filedialog = fd_mod  # type: ignore[attr-defined]
    return {"tkinter": tk_mod, "tkinter.filedialog": fd_mod}


def test_browse_file_returns_selected_path() -> None:
    ctx = _Ctx()
    chosen = str(Path.home() / "roms" / "game.gba")
    with mock.patch.dict(sys.modules, _fake_tkinter(chosen)):
        cfg_handler._browse_file(ctx, {"title": ["Elige ROM"]})
    assert ctx.payload == {"ok": True, "path": str(Path(chosen))}


def test_browse_file_cancelled_returns_flag() -> None:
    ctx = _Ctx()
    # askopenfilename returns "" when the user cancels the dialog.
    with mock.patch.dict(sys.modules, _fake_tkinter("")):
        cfg_handler._browse_file(ctx, {})
    assert ctx.payload == {"ok": False, "cancelled": True}


def test_browse_file_degrades_when_tkinter_unavailable() -> None:
    ctx = _Ctx()
    # sys.modules entry set to None makes `import tkinter` raise ImportError.
    with mock.patch.dict(sys.modules, {"tkinter": None}):
        cfg_handler._browse_file(ctx, {})  # must not raise
    assert ctx.payload is not None
    assert ctx.payload["ok"] is False
    assert "error" in ctx.payload
