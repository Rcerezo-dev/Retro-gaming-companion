"""TRASH-FIX-2: ls_recursive() nunca debe devolver contenido bajo _descartados/
en modo ADB (mismo guard que TRASH-FIX-1 ya aplica al modo FS en
cable_engine.iter_files — sin esto, Cable Sync ADB + "Espejo completo" puede
recopiar/redescartar contenido ya descartado, reanidando la papelera)."""

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
    )
    transport = _make_transport(monkeypatch, output)

    found = {info.android_path for info in transport.ls_recursive("/sdcard/roms")}

    assert found == {"/sdcard/roms/psx/game.chd"}


def test_ls_recursive_raises_on_argument_list_too_long(monkeypatch) -> None:
    """ANDROID-SCAN-FIX-1f: un listado parcial no puede pasar por completo."""
    output = "/sdcard/roms/a.nes|1|1\nfind: exec stat: Argument list too long\n"
    transport = _make_transport(monkeypatch, output)

    with pytest.raises(OSError):
        transport.ls_recursive("/sdcard/roms")


def test_ls_recursive_uses_xargs_not_exec_plus(monkeypatch) -> None:
    seen: list[str] = []
    transport = AdbTransport("adb.exe", "SERIAL123")
    monkeypatch.setattr(transport, "_shell", lambda cmd, **kw: seen.append(cmd) or "")

    transport.ls_recursive("/sdcard/roms")

    assert "xargs -0" in seen[0] and "-exec" not in seen[0]
