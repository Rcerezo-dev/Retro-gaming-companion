from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.web.router import Router


# ── Public entry point ────────────────────────────────────────────────────────


def register_dialogs(router: Router) -> None:
    """Register native OS file/folder picker routes on *router*."""

    @router.get("/api/browse-folder")
    def get_browse_folder(ctx) -> None:
        _browse_folder(ctx, getattr(ctx, "_qs", {}))

    @router.get("/api/browse-file")
    def get_browse_file(ctx) -> None:
        _browse_file(ctx, getattr(ctx, "_qs", {}))


# ── Handler logic (moved from config.py, REFACTOR-9) ──────────────────────────


def _browse_folder(ctx, qs: dict) -> None:
    """Open a native OS folder picker and return the selected path.

    Query params:
      - initial_dir: optional starting directory (falls back to user home)
      - title: optional dialog title
    """
    initial_dir = (qs.get("initial_dir", [None])[0] or "").strip() or None
    title = (qs.get("title", [None])[0] or "").strip() or "Seleccionar carpeta"

    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()  # hide blank root window
        root.wm_attributes("-topmost", True)  # bring dialog to front on Windows
        root.lift()
        folder = filedialog.askdirectory(
            parent=root,
            title=title,
            initialdir=initial_dir or Path.home(),
            mustexist=False,
        )
        root.destroy()
    except Exception as exc:
        ctx._send_json({"ok": False, "error": f"No se pudo abrir el selector: {exc}"})
        return

    if not folder:
        # User cancelled
        ctx._send_json({"ok": False, "cancelled": True})
        return

    # Normalize to OS-native separators
    ctx._send_json({"ok": True, "path": str(Path(folder))})


def _browse_file(ctx, qs: dict) -> None:
    """Open a native OS file picker and return the selected path.

    HERR-UX-11: the patch manager's ROM picker used to call
    :func:`_browse_folder` — a *directory* picker — to choose a single ROM
    *file*, which could only ever return a folder path. Same query params
    as ``_browse_folder``.
    """
    initial_dir = (qs.get("initial_dir", [None])[0] or "").strip() or None
    title = (qs.get("title", [None])[0] or "").strip() or "Seleccionar archivo"

    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()  # hide blank root window
        root.wm_attributes("-topmost", True)  # bring dialog to front on Windows
        root.lift()
        file_path = filedialog.askopenfilename(
            parent=root,
            title=title,
            initialdir=initial_dir or Path.home(),
        )
        root.destroy()
    except Exception as exc:
        ctx._send_json({"ok": False, "error": f"No se pudo abrir el selector: {exc}"})
        return

    if not file_path:
        # User cancelled
        ctx._send_json({"ok": False, "cancelled": True})
        return

    # Normalize to OS-native separators
    ctx._send_json({"ok": True, "path": str(Path(file_path))})
