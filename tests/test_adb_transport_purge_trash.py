"""TRASH-FIX-3: purge_trash() en el dispositivo Android borra solo los
archivos de _descartados/ más antiguos que el umbral, y nada fuera de ahí
(en particular, nunca debe tocar rutas de saves)."""

from __future__ import annotations

import time

from rom_manager.sync.adb_transport import AdbTransport

_NOW = time.time()
_OLD = _NOW - 40 * 86400  # 40 días
_RECENT = _NOW - 5 * 86400  # 5 días


def _fake_shell(commands: dict[str, str]):
    def _shell(*args, **kwargs):
        cmd = args[0] if args else ""
        for key, output in commands.items():
            if key in cmd:
                return output
        return ""

    return _shell


def test_purge_trash_deletes_only_files_older_than_threshold(monkeypatch) -> None:
    transport = AdbTransport("adb.exe", "SERIAL123")

    find_dirs = "find /sdcard/roms -type d -iname _descartados"
    find_files = "find /sdcard/roms/psx/_descartados -maxdepth 1 -type f"
    stat_output = (
        f"1000|{_OLD:.0f}|/sdcard/roms/psx/_descartados/old_game.chd\n"
        f"2000|{_RECENT:.0f}|/sdcard/roms/psx/_descartados/recent_game.chd\n"
    )

    rm_calls: list[str] = []

    def _shell(*args, **kwargs):
        cmd = args[0]
        if cmd == find_dirs:
            return "/sdcard/roms/psx/_descartados\n"
        if cmd.startswith(find_files):
            return stat_output
        if cmd.startswith("rm -f"):
            rm_calls.append(cmd)
            return ""
        if cmd.startswith("rmdir"):
            return ""
        return ""

    monkeypatch.setattr(transport, "_shell", _shell)

    result = transport.purge_trash(roots=["/sdcard/roms"], older_than_days=30)

    assert result == {"deleted": 1, "bytes": 1000}
    assert len(rm_calls) == 1
    assert "old_game.chd" in rm_calls[0]


def test_purge_trash_never_targets_save_paths(monkeypatch) -> None:
    """Solo actúa dentro de carpetas _descartados/ localizadas por find --
    una carpeta de saves nunca aparece en esa lista, así que nunca se toca."""
    transport = AdbTransport("adb.exe", "SERIAL123")
    seen_paths: list[str] = []

    def _shell(*args, **kwargs):
        cmd = args[0]
        seen_paths.append(cmd)
        if "find" in cmd and "-iname" in cmd:
            return "/sdcard/roms/psx/_descartados\n"
        if "find" in cmd and "-maxdepth 1 -type f" in cmd:
            return f"500|{_OLD:.0f}|/sdcard/roms/psx/_descartados/junk.bin\n"
        return ""

    monkeypatch.setattr(transport, "_shell", _shell)
    transport.purge_trash(roots=["/sdcard/roms"], older_than_days=30)

    assert not any("saves" in p or "states" in p for p in seen_paths)


def test_trash_stats_counts_without_deleting(monkeypatch) -> None:
    """trash_stats() es de solo lectura: cuenta todo lo que hay en la papelera
    (sin filtro de antigüedad) y nunca llama a rm/rmdir."""
    transport = AdbTransport("adb.exe", "SERIAL123")
    rm_calls: list[str] = []

    def _shell(*args, **kwargs):
        cmd = args[0]
        if cmd.startswith("rm ") or cmd.startswith("rm -f") or cmd.startswith("rmdir"):
            rm_calls.append(cmd)
            return ""
        if "-iname" in cmd:
            return "/sdcard/roms/psx/_descartados\n"
        if "-maxdepth 1 -type f" in cmd:
            return f"{1000}\n{2000}\n"
        return ""

    monkeypatch.setattr(transport, "_shell", _shell)

    result = transport.trash_stats(roots=["/sdcard/roms"])

    assert result == {"files": 2, "bytes": 3000}
    assert rm_calls == []
