"""Win32 system-tray icon — zero external dependencies (ctypes + stdlib only).

Usage::

    tray = TrayIcon(
        port=7777,
        on_sync=lambda: ...,
        on_quit=lambda: ...,
    )
    tray.start()                         # non-blocking; runs Win32 loop in daemon thread
    tray.show_balloon("Title", "Text")   # toast notification
    tray.set_status("Sync OK 14:32")     # tooltip line
    tray.stop()                          # post WM_QUIT to message loop
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as W
import os
import sys
import threading
import webbrowser
import winreg
from collections.abc import Callable
from pathlib import Path

if sys.platform != "win32":
    raise ImportError("tray_icon is Windows-only")

# ── WinAPI bindings ───────────────────────────────────────────────────────────
_shell32 = ctypes.windll.shell32
_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32

# Messages
_WM_DESTROY = 0x0002
_WM_QUIT = 0x0012
_WM_RBUTTONUP = 0x0205
_WM_LBUTTONDBLCLK = 0x0203
_WM_USER = 0x0400
_TRAY_CALLBACK = _WM_USER + 20

# Shell_NotifyIcon ops / flags
_NIM_ADD = 0
_NIM_MODIFY = 1
_NIM_DELETE = 2
_NIF_MESSAGE = 0x01
_NIF_ICON = 0x02
_NIF_TIP = 0x04
_NIF_INFO = 0x10
_NIIF_INFO = 0x01
_NIIF_NOSOUND = 0x10

# Menu
_MF_STRING = 0x00000000
_MF_SEPARATOR = 0x00000800
_MF_GRAYED = 0x00000001
_TPM_RIGHTBUTTON = 0x0002
_TPM_RETURNCMD = 0x0100
_TPM_NONOTIFY = 0x0080

# LoadImage
_IMAGE_ICON = 1
_LR_LOADFROMFILE = 0x0010
_LR_DEFAULTSIZE = 0x0040
_IDI_APPLICATION = ctypes.cast(32512, W.LPCWSTR)


class _NOTIFYICONDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("hWnd", W.HWND),
        ("uID", W.UINT),
        ("uFlags", W.UINT),
        ("uCallbackMessage", W.UINT),
        ("hIcon", W.HICON),
        ("szTip", ctypes.c_wchar * 128),
        ("dwState", ctypes.c_ulong),
        ("dwStateMask", ctypes.c_ulong),
        ("szInfo", ctypes.c_wchar * 256),
        ("uVersion", ctypes.c_uint),
        ("szInfoTitle", ctypes.c_wchar * 64),
        ("dwInfoFlags", ctypes.c_ulong),
    ]


class _WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", W.UINT),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", W.HINSTANCE),
        ("hIcon", W.HICON),
        ("hCursor", W.HANDLE),
        ("hbrBackground", W.HANDLE),
        ("lpszMenuName", W.LPCWSTR),
        ("lpszClassName", W.LPCWSTR),
    ]


_WNDPROCTYPE = ctypes.WINFUNCTYPE(ctypes.c_long, W.HWND, W.UINT, W.WPARAM, W.LPARAM)

# ── Autostart helpers ─────────────────────────────────────────────────────────
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "RetroVault"


def get_autostart_status() -> bool:
    """Return True if RetroVault is in the Windows startup registry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, _APP_NAME)
        winreg.CloseKey(key)
        return True
    except OSError:
        return False


def set_autostart(enabled: bool, launch_cmd: str = "") -> bool:
    """Add or remove RetroVault from Windows startup. Returns success."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _RUN_KEY,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
        )
        if enabled:
            winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, launch_cmd)
        else:
            try:
                winreg.DeleteValue(key, _APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except OSError:
        return False


def _default_launch_cmd() -> str:
    """Best-effort: figure out the command that started this process."""
    # If frozen (PyInstaller)
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --tray'
    # Running via rommgr.cmd / Python
    Path(sys.executable).parent / "Scripts"
    cmd_script = Path(__file__).resolve().parents[3] / "scripts" / "rommgr.cmd"
    if cmd_script.exists():
        return f'"{cmd_script}" serve --tray'
    return f'"{sys.executable}" -m rom_manager serve --tray'


# ── TrayIcon ──────────────────────────────────────────────────────────────────
class TrayIcon:
    """Minimal Win32 system-tray icon.  Runs its message loop on a daemon thread."""

    _ID_OPEN = 1001
    _ID_SYNC = 1002
    _ID_SEP1 = 0
    _ID_START = 1004
    _ID_SEP2 = 0
    _ID_QUIT = 1005

    def __init__(
        self,
        port: int = 7777,
        icon_path: str | None = None,
        on_sync: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
    ) -> None:
        self._port = port
        self._icon_path = icon_path
        self._on_sync = on_sync
        self._on_quit = on_quit
        self._hwnd: W.HWND | None = None
        self._nid: _NOTIFYICONDATA | None = None
        self._status = "Servidor activo"
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the tray icon (non-blocking)."""
        self._thread = threading.Thread(target=self._run, daemon=True, name="tray-icon")
        self._thread.start()
        self._ready.wait(timeout=3)  # wait for hwnd to be created

    def stop(self) -> None:
        if self._hwnd:
            _user32.PostMessageW(self._hwnd, _WM_QUIT, 0, 0)

    def set_status(self, text: str) -> None:
        self._status = text
        if self._nid and self._hwnd:
            self._nid.szTip = f"Retro Vault — {text}"[:127]
            self._nid.uFlags = _NIF_TIP
            _shell32.Shell_NotifyIconW(_NIM_MODIFY, ctypes.byref(self._nid))

    def show_balloon(self, title: str, text: str, *, sound: bool = False) -> None:
        if not (self._nid and self._hwnd):
            return
        self._nid.uFlags = _NIF_INFO
        self._nid.szInfoTitle = title[:63]
        self._nid.szInfo = text[:255]
        self._nid.dwInfoFlags = _NIIF_INFO | (0 if sound else _NIIF_NOSOUND)
        _shell32.Shell_NotifyIconW(_NIM_MODIFY, ctypes.byref(self._nid))

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load_icon(self) -> W.HICON:
        if self._icon_path and os.path.exists(self._icon_path):
            h = _user32.LoadImageW(
                None,
                self._icon_path,
                _IMAGE_ICON,
                0,
                0,
                _LR_LOADFROMFILE | _LR_DEFAULTSIZE,
            )
            if h:
                return h
        return _user32.LoadIconW(None, _IDI_APPLICATION)

    def _make_menu(self) -> W.HMENU:
        autostart = get_autostart_status()
        menu = _user32.CreatePopupMenu()
        _user32.AppendMenuW(menu, _MF_STRING, self._ID_OPEN, "Abrir Retro Vault")
        _user32.AppendMenuW(menu, _MF_STRING, self._ID_SYNC, "Sync ahora")
        _user32.AppendMenuW(menu, _MF_SEPARATOR, 0, None)
        label_start = (
            "Inicio automatico: ACTIVADO  [clic para desactivar]"
            if autostart
            else "Inicio automatico: desactivado  [clic para activar]"
        )
        _user32.AppendMenuW(menu, _MF_STRING, self._ID_START, label_start)
        _user32.AppendMenuW(menu, _MF_SEPARATOR, 0, None)
        _user32.AppendMenuW(menu, _MF_STRING, self._ID_QUIT, "Salir")
        return menu

    def _show_menu(self) -> None:
        menu = self._make_menu()
        pt = W.POINT()
        _user32.GetCursorPos(ctypes.byref(pt))
        _user32.SetForegroundWindow(self._hwnd)
        cmd = _user32.TrackPopupMenu(
            menu,
            _TPM_RIGHTBUTTON | _TPM_RETURNCMD | _TPM_NONOTIFY,
            pt.x,
            pt.y,
            0,
            self._hwnd,
            None,
        )
        _user32.DestroyMenu(menu)
        self._dispatch(cmd)

    def _dispatch(self, cmd: int) -> None:
        if cmd == self._ID_OPEN:
            webbrowser.open(f"http://127.0.0.1:{self._port}")
        elif cmd == self._ID_SYNC:
            if self._on_sync:
                threading.Thread(target=self._on_sync, daemon=True).start()
        elif cmd == self._ID_START:
            currently_on = get_autostart_status()
            if currently_on:
                set_autostart(False)
                self.show_balloon("Retro Vault", "Inicio automatico desactivado.")
            else:
                set_autostart(True, _default_launch_cmd())
                self.show_balloon(
                    "Retro Vault", "Inicio automatico activado.\nRetro Vault arrancara con Windows."
                )
        elif cmd == self._ID_QUIT:
            self._remove_icon()
            if self._on_quit:
                self._on_quit()
            _user32.PostQuitMessage(0)

    def _wndproc(self, hwnd: W.HWND, msg: int, wparam: int, lparam: int) -> int:
        if msg == _TRAY_CALLBACK:
            event = lparam & 0xFFFF
            if event == _WM_RBUTTONUP:
                self._show_menu()
            elif event == _WM_LBUTTONDBLCLK:
                webbrowser.open(f"http://127.0.0.1:{self._port}")
            return 0
        if msg == _WM_DESTROY:
            self._remove_icon()
            _user32.PostQuitMessage(0)
            return 0
        return _user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _remove_icon(self) -> None:
        if self._nid and self._hwnd:
            self._nid.uFlags = 0
            _shell32.Shell_NotifyIconW(_NIM_DELETE, ctypes.byref(self._nid))
            self._nid = None

    def _run(self) -> None:
        import random

        class_name = f"RetroVaultTray_{random.randint(10000, 99999)}"

        # Keep the WNDPROC ref alive for the lifetime of this method
        wndproc_cb = _WNDPROCTYPE(self._wndproc)

        wc = _WNDCLASSW()
        wc.lpfnWndProc = ctypes.cast(wndproc_cb, ctypes.c_void_p)
        wc.hInstance = _kernel32.GetModuleHandleW(None)
        wc.lpszClassName = class_name

        if not _user32.RegisterClassW(ctypes.byref(wc)):
            self._ready.set()
            return

        hwnd = _user32.CreateWindowExW(
            0,
            class_name,
            "RetroVault Tray",
            0,
            0,
            0,
            0,
            0,
            None,
            None,
            wc.hInstance,
            None,
        )
        if not hwnd:
            self._ready.set()
            return

        self._hwnd = hwnd
        icon = self._load_icon()

        nid = _NOTIFYICONDATA()
        nid.cbSize = ctypes.sizeof(_NOTIFYICONDATA)
        nid.hWnd = hwnd
        nid.uID = 1
        nid.uFlags = _NIF_ICON | _NIF_MESSAGE | _NIF_TIP
        nid.uCallbackMessage = _TRAY_CALLBACK
        nid.hIcon = icon
        nid.szTip = f"Retro Vault — {self._status}"[:127]
        self._nid = nid

        _shell32.Shell_NotifyIconW(_NIM_ADD, ctypes.byref(nid))
        self._ready.set()  # signal start() that hwnd is ready

        # Startup toast (slight delay so Windows registers the icon first)
        threading.Timer(
            1.5,
            self.show_balloon,
            args=("Retro Vault", "Servidor iniciado.\nDoble-clic para abrir la interfaz."),
        ).start()

        msg = W.MSG()
        while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            _user32.TranslateMessage(ctypes.byref(msg))
            _user32.DispatchMessageW(ctypes.byref(msg))

        self._remove_icon()
