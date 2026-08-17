"""Tests for _detect_retroarch_install — CFG-PORGAME (auto-detección de rutas).

Solo cubre el caso "encontrado" vía %APPDATA%/RetroArch: es multiplataforma
(Path(appdata)/"RetroArch" no depende de que exista una unidad C:/D:/E: real)
y es el primer candidato de la lista, así que un match ahí no llega a
evaluar los demás. No hay test de "no encontrado": la lista de candidatos
incluye rutas absolutas fuera de control del test (p. ej. el
`libraryfolders.vdf` real de Steam si está instalado) — aislarlo del todo
exigiría inyectar la lista de candidatos, refactor fuera de alcance aquí.
"""

from __future__ import annotations

from pathlib import Path

from rom_manager.web.handlers.config import _detect_retroarch_install


def test_found_derives_ra_config_dir_next_to_exe(monkeypatch, tmp_path: Path) -> None:
    ra_dir = tmp_path / "AppData" / "RetroArch"
    ra_dir.mkdir(parents=True)
    (ra_dir / "retroarch.exe").touch()

    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("USERPROFILE", raising=False)

    result = _detect_retroarch_install()

    assert result["found"] is True
    assert result["retroarch_path"] == str(ra_dir / "retroarch.exe")
    assert result["ra_config_dir"] == str(ra_dir / "config")


def test_ra_config_dir_derived_even_without_retroarch_cfg(monkeypatch, tmp_path: Path) -> None:
    """library_root needs retroarch.cfg to exist; ra_config_dir doesn't — it's
    just the standard sibling folder, populated lazily by RetroArch itself."""
    ra_dir = tmp_path / "AppData" / "RetroArch"
    ra_dir.mkdir(parents=True)
    (ra_dir / "retroarch.exe").touch()
    # No retroarch.cfg written on purpose.

    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("USERPROFILE", raising=False)

    result = _detect_retroarch_install()

    assert result["found"] is True
    assert result["library_root"] is None
    assert result["ra_config_dir"] == str(ra_dir / "config")


def test_library_root_read_from_retroarch_cfg(monkeypatch, tmp_path: Path) -> None:
    ra_dir = tmp_path / "AppData" / "RetroArch"
    ra_dir.mkdir(parents=True)
    (ra_dir / "retroarch.exe").touch()
    (ra_dir / "retroarch.cfg").write_text('content_directory = "E:\\ROMs"\n', encoding="utf-8")

    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("USERPROFILE", raising=False)

    result = _detect_retroarch_install()

    assert result["library_root"] == "E:\\ROMs"
    assert result["ra_config_dir"] == str(ra_dir / "config")
