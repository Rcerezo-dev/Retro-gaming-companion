from __future__ import annotations

from pathlib import Path

import pytest
from rom_manager.config import load_config
from rom_manager.detection.file_classifier import FileCategory, classify_path


@pytest.fixture
def config():
    return load_config()


@pytest.fixture
def source_root(tmp_path: Path) -> Path:
    return tmp_path


def _make_file(root: Path, *parts: str) -> Path:
    path = root.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path


# --- ROM detection ---

@pytest.mark.parametrize("filename", [
    "game.gb", "game.gbc", "game.gba", "game.nes", "game.sfc", "game.smc",
    "game.n64", "game.z64", "game.nds", "game.3ds",
    "game.bin", "game.iso", "game.cue", "game.zip", "game.chd",
    "game.img", "game.mdf", "game.mds", "game.ccd", "game.ecm",
])
def test_rom_extensions(tmp_path, config, filename):
    path = _make_file(tmp_path, filename)
    assert classify_path(path, config, tmp_path) is FileCategory.ROM


# --- Save detection ---

@pytest.mark.parametrize("filename", [
    "game.sav", "game.srm", "game.state", "game.st0", "game.mcr",
    "game.dsv", "game.eep", "game.nv",
])
def test_save_extensions(tmp_path, config, filename):
    path = _make_file(tmp_path, filename)
    assert classify_path(path, config, tmp_path) is FileCategory.SAVE


# --- Frontend asset detection ---

@pytest.mark.parametrize("filename", [
    "cover.png", "screenshot.jpg", "preview.jpeg", "video.mp4",
])
def test_frontend_asset_extensions(tmp_path, config, filename):
    path = _make_file(tmp_path, filename)
    assert classify_path(path, config, tmp_path) is FileCategory.FRONTEND_ASSET


def test_gamelist_xml_is_asset(tmp_path, config):
    path = _make_file(tmp_path, "gamelist.xml")
    assert classify_path(path, config, tmp_path) is FileCategory.FRONTEND_ASSET


def test_gamelist_xml_case_insensitive(tmp_path, config):
    path = _make_file(tmp_path, "Gamelist.XML")
    assert classify_path(path, config, tmp_path) is FileCategory.FRONTEND_ASSET


# --- Unknown ---

def test_unknown_extension(tmp_path, config):
    path = _make_file(tmp_path, "file.xyz")
    assert classify_path(path, config, tmp_path) is FileCategory.UNKNOWN


# --- Excluded directory → SYSTEM_SUPPORT ---

@pytest.mark.parametrize("excluded_dir", [
    "Android", "BIOS", "DCIM", "Documents", "Movies",
    "Music", "Notifications", "backup", "recovery_log",
])
def test_excluded_directory(tmp_path, config, excluded_dir):
    path = _make_file(tmp_path, excluded_dir, "game.gb")
    assert classify_path(path, config, tmp_path) is FileCategory.SYSTEM_SUPPORT


def test_excluded_directory_case_insensitive(tmp_path, config):
    path = _make_file(tmp_path, "android", "game.gb")
    assert classify_path(path, config, tmp_path) is FileCategory.SYSTEM_SUPPORT


def test_excluded_directory_nested(tmp_path, config):
    path = _make_file(tmp_path, "systems", "Android", "data", "game.gb")
    assert classify_path(path, config, tmp_path) is FileCategory.SYSTEM_SUPPORT
