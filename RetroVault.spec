# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Retro Vault
# Build with:  pyinstaller RetroVault.spec
#
# Output: dist/RetroVault/RetroVault.exe

from pathlib import Path

ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "src" / "rom_manager" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=[
        # ADB and its required DLLs
        (str(ROOT / "tools" / "adb.exe"),          "tools"),
        (str(ROOT / "tools" / "AdbWinApi.dll"),     "tools"),
        (str(ROOT / "tools" / "AdbWinUsbApi.dll"),  "tools"),
        # chdman
        (str(ROOT / "tools" / "chdman.exe"),        "tools"),
    ],
    datas=[
        # Static web assets (CSS + JS)
        (str(ROOT / "src" / "rom_manager" / "web" / "static"), "rom_manager/web/static"),
    ],
    hiddenimports=[
        # stdlib modules that PyInstaller sometimes misses
        "sqlite3",
        "tomllib",
        "winreg",
        "ctypes",
        "ctypes.wintypes",
        # All rom_manager subpackages (dynamic imports via late-import pattern)
        "rom_manager.web.inbox_pipeline",
        "rom_manager.web.response_builders",
        "rom_manager.sync.cable_sync_daemon",
        "rom_manager.sync.delta_cache",
        "rom_manager.utils.tray_icon",
        "rom_manager.utils.notifier",
        "rom_manager.retroachievements.ra_checker",
        "rom_manager.scraper.screenscraper",
        "rom_manager.backup",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Not needed at runtime
        "pytest",
        "setuptools",
        "pip",
        "tkinter",
        "_tkinter",
        "unittest",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RetroVault",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,   # Keep console so "rommgr serve" output is visible; tray icon handles minimise
    icon=None,      # Add icon path here when available, e.g. "assets/icon.ico"
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RetroVault",
)
