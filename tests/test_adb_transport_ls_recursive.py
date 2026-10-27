"""TRASH-FIX-2: ls_recursive() nunca debe devolver contenido bajo _descartados/
en modo ADB (mismo guard que TRASH-FIX-1 ya aplica al modo FS en
cable_engine.iter_files — sin esto, Cable Sync ADB + "Espejo completo" puede
recopiar/redescartar contenido ya descartado, reanidando la papelera).

ANDROID-SCAN-FIX-2: un listado truncado nunca se devuelve como completo."""

from __future__ import annotations

import pytest

from rom_manager.sync.adb_transport import AdbTransport


def _make_transport(monkeypatch, output: str) -> AdbTransport:
    transport = AdbTransport("adb.exe", "SERIAL123")
    monkeypatch.setattr(transport, "_shell", lambda *a, **kw: output)
    return transport


def test_ls_recursive_skips_descartados(monkeypatch) -> None:
    output = (
        "/sdcard/roms/psx/game.chd|1000|100\n"
        "/sdcard/roms/psx/_descartados/old_game.bin|2000|100\n"
        "/sdcard/roms/psx/_descartados/_descartados/nested.zip|3000|100\n"
        "/sdcard/roms/.hidden/junk.txt|4000|100\n"
        "__RC=0\n"
    )
    transport = _make_transport(monkeypatch, output)

    found = {info.android_path for info in transport.ls_recursive("/sdcard/roms")}

    assert found == {"/sdcard/roms/psx/game.chd"}


def test_ls_recursive_raises_on_truncated_listing(monkeypatch) -> None:
    truncated = (
        "/sdcard/roms/gb/a.gb|1|100\n"
        "find: exec stat: Argument list too long\n"
        "__RC=126\n"
    )
    with pytest.raises(RuntimeError):
        _make_transport(monkeypatch, truncated).ls_recursive("/sdcard/roms")
    with pytest.raises(RuntimeError):  # sin marcador (timeout / adb caído)
        _make_transport(monkeypatch, "/sdcard/roms/gb/a.gb|1|100\n").ls_recursive("/sdcard/roms")


def test_ls_recursive_accepts_rc1_and_float_mtime(monkeypatch) -> None:
    out = (
        "/sdcard/roms/gb/a.gb|1|1788010868.0\n"
        "find: /sdcard/roms/x: Permission denied\n"
        "__RC=1\n"
    )
    found = _make_transport(monkeypatch, out).ls_recursive("/sdcard/roms")
    assert [(f.android_path, f.size, f.mtime) for f in found] == [
        ("/sdcard/roms/gb/a.gb", 1, 1788010868.0)
    ]
