from __future__ import annotations

from rom_manager.utils.paths import is_device_path


def test_posix_path_is_device_path():
    assert is_device_path("/storage/emulated/0/RetroArch/roms/game.zip") is True


def test_windows_path_is_not_device_path():
    assert is_device_path("F:\\Juegos Retro\\CPS3\\game.zip") is False
    assert is_device_path("C:\\Users\\Ruben\\Documents\\game.zip") is False


def test_path_under_anbernic_root_is_device_path():
    assert (
        is_device_path("H:\\RetroArch\\roms\\snes\\game.sfc", anbernic_root="H:\\RetroArch") is True
    )


def test_path_outside_anbernic_root_is_not_device_path():
    assert (
        is_device_path("F:\\Juegos Retro\\snes\\game.sfc", anbernic_root="H:\\RetroArch") is False
    )


def test_case_insensitive():
    assert is_device_path("h:\\retroarch\\roms\\game.sfc", anbernic_root="H:\\RetroArch") is True
