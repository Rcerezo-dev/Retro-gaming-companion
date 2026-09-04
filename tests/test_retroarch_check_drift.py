"""DEVPROFILE-7: retroarch.cfg drift detection in _handle_retroarch_check()."""

from __future__ import annotations

from pathlib import Path

from rom_manager.config import load_config
from rom_manager.services.retroarch_cfg_writer import default_savefile_layout
from rom_manager.web.handlers.system import _handle_retroarch_check


def _make_ra_install(tmp_path: Path, savefile_dir: str, savestate_dir: str) -> Path:
    ra_dir = tmp_path / "RetroArch"
    (ra_dir / "cores").mkdir(parents=True)
    (ra_dir / "cores" / "fceumm_libretro.dll").touch()
    (ra_dir / "retroarch.cfg").write_text(
        f'savefile_directory = "{savefile_dir}"\nsavestate_directory = "{savestate_dir}"\n',
        encoding="utf-8",
    )
    return ra_dir


def test_flags_drift_when_savefile_dir_is_stale(tmp_path: Path) -> None:
    library_root = tmp_path / "Library"
    ra_dir = _make_ra_install(
        tmp_path, savefile_dir=str(tmp_path / "Old" / "saves"), savestate_dir=""
    )

    cfg = load_config()
    cfg.library_root = library_root
    cfg.retroarch_path = str(ra_dir / "retroarch.exe")

    result = _handle_retroarch_check(cfg)

    assert result["savefile_drift"] is True
    assert result["ok"] is False
    assert any("savefile_directory" in issue for issue in result["issues"])
    assert any("savestate_directory" in issue for issue in result["issues"])


def test_no_drift_once_default_layout_is_applied(tmp_path: Path) -> None:
    library_root = tmp_path / "Library"
    expected = default_savefile_layout(library_root)
    ra_dir = _make_ra_install(
        tmp_path, savefile_dir=expected.savefile_dir, savestate_dir=expected.savestate_dir
    )

    cfg = load_config()
    cfg.library_root = library_root
    cfg.retroarch_path = str(ra_dir / "retroarch.exe")

    result = _handle_retroarch_check(cfg)

    assert result["savefile_drift"] is False
    assert not any("no coincide con el layout" in issue for issue in result["issues"])
