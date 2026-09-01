"""Tests for services/retroarch_cfg_writer.py (DEVPROFILE-2)."""

from __future__ import annotations

from pathlib import Path

from rom_manager.services.retroarch_cfg_writer import (
    apply_savefile_layout,
    default_savefile_layout,
    read_key,
    read_savefile_layout,
)

_SAMPLE_CFG = """\
# comment RetroArch keeps
video_fullscreen = "false"
savefile_directory = "default"
some_other_key = "keep me"
"""


def test_read_key_missing_returns_none() -> None:
    assert read_key(_SAMPLE_CFG, "savestate_directory") is None


def test_read_key_default_treated_as_unset() -> None:
    assert read_key(_SAMPLE_CFG, "savefile_directory") is None


def test_read_key_returns_value() -> None:
    assert read_key(_SAMPLE_CFG, "video_fullscreen") == "false"


def test_read_savefile_layout() -> None:
    layout = read_savefile_layout(_SAMPLE_CFG)
    assert layout.savefile_dir == ""
    assert layout.savestate_dir == ""


def test_apply_writes_backup_and_all_four_keys(tmp_path: Path) -> None:
    cfg = tmp_path / "retroarch.cfg"
    cfg.write_text(_SAMPLE_CFG, encoding="utf-8")

    result = apply_savefile_layout(cfg, savefile_dir="E:/saves", savestate_dir="E:/states")

    assert result.applied
    assert result.error == ""
    assert Path(result.backup_path).read_text(encoding="utf-8") == _SAMPLE_CFG

    new_text = cfg.read_text(encoding="utf-8")
    assert read_key(new_text, "savefile_directory") == "E:/saves"
    assert read_key(new_text, "savestate_directory") == "E:/states"
    assert read_key(new_text, "sort_savefiles_by_content_enable") == "true"
    assert read_key(new_text, "sort_savestates_by_content_enable") == "true"
    # Untouched lines survive verbatim
    assert 'some_other_key = "keep me"' in new_text
    assert "# comment RetroArch keeps" in new_text


def test_apply_appends_missing_keys(tmp_path: Path) -> None:
    cfg = tmp_path / "retroarch.cfg"
    cfg.write_text('video_fullscreen = "false"\n', encoding="utf-8")

    result = apply_savefile_layout(cfg, savefile_dir="E:/saves", savestate_dir="E:/states")

    new_text = cfg.read_text(encoding="utf-8")
    assert read_key(new_text, "savefile_directory") == "E:/saves"
    assert 'video_fullscreen = "false"' in new_text
    assert result.changed_keys == {
        "savefile_directory": "E:/saves",
        "savestate_directory": "E:/states",
        "sort_savefiles_by_content_enable": "true",
        "sort_savestates_by_content_enable": "true",
    }


def test_apply_is_noop_when_already_correct(tmp_path: Path) -> None:
    cfg = tmp_path / "retroarch.cfg"
    cfg.write_text(
        'savefile_directory = "E:/saves"\n'
        'savestate_directory = "E:/states"\n'
        'sort_savefiles_by_content_enable = "true"\n'
        'sort_savestates_by_content_enable = "true"\n',
        encoding="utf-8",
    )

    result = apply_savefile_layout(cfg, savefile_dir="E:/saves", savestate_dir="E:/states")

    assert result.applied
    assert result.backup_path == ""  # no backup made — nothing changed
    assert result.changed_keys == {}


def test_apply_only_touches_keys_that_actually_changed(tmp_path: Path) -> None:
    cfg = tmp_path / "retroarch.cfg"
    cfg.write_text('savefile_directory = "E:/saves"\n', encoding="utf-8")

    result = apply_savefile_layout(cfg, savefile_dir="E:/saves", savestate_dir="E:/states")

    assert "savefile_directory" not in result.changed_keys
    assert result.changed_keys["savestate_directory"] == "E:/states"


def test_apply_missing_file_reports_error(tmp_path: Path) -> None:
    result = apply_savefile_layout(tmp_path / "nope.cfg", "E:/saves", "E:/states")
    assert not result.applied
    assert result.error


def test_default_savefile_layout_matches_d2_sync_convention(tmp_path: Path) -> None:
    layout = default_savefile_layout(tmp_path)
    assert layout.savefile_dir == str(tmp_path / "saves")
    assert layout.savestate_dir == str(tmp_path / "states")
