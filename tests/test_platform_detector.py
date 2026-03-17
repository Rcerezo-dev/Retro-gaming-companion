"""Tests for platform_detector.py — extension and folder-based platform detection."""
from __future__ import annotations

from pathlib import Path

import pytest

from rom_manager.detection.platform_detector import (
    AMBIGUOUS_EXTENSIONS,
    PLATFORM_BY_EXTENSION,
    PLATFORM_BY_FOLDER,
    ROM_EXTENSIONS,
    detect_platform,
    is_rom_file,
    normalize_extension,
)


# ── normalize_extension ────────────────────────────────────────────────────────

class TestNormalizeExtension:
    def test_lowercase(self, tmp_path: Path) -> None:
        assert normalize_extension(Path("game.GBA")) == ".gba"

    def test_already_lower(self, tmp_path: Path) -> None:
        assert normalize_extension(Path("game.sfc")) == ".sfc"

    def test_no_extension(self, tmp_path: Path) -> None:
        assert normalize_extension(Path("README")) == ""

    def test_mixed_case(self, tmp_path: Path) -> None:
        assert normalize_extension(Path("GAME.NES")) == ".nes"


# ── is_rom_file ────────────────────────────────────────────────────────────────

class TestIsRomFile:
    def test_unambiguous_rom(self) -> None:
        assert is_rom_file(Path("game.gba")) is True

    def test_save_extension_not_rom(self) -> None:
        assert is_rom_file(Path("game.sav")) is False

    def test_md_in_megadrive_folder(self) -> None:
        assert is_rom_file(Path("/roms/megadrive/Sonic.md")) is True

    def test_md_without_folder_context(self) -> None:
        # .md in a random folder should NOT be classified as ROM
        assert is_rom_file(Path("/docs/README.md")) is False

    def test_md_in_genesis_folder(self) -> None:
        assert is_rom_file(Path("/roms/genesis/Sonic.md")) is True

    def test_zip_is_rom(self) -> None:
        # Ambiguous but still in ROM_EXTENSIONS
        assert is_rom_file(Path("game.zip")) is True

    def test_txt_not_rom(self) -> None:
        assert is_rom_file(Path("readme.txt")) is False


# ── detect_platform — unambiguous extensions ──────────────────────────────────

class TestDetectPlatformUnambiguous:
    @pytest.mark.parametrize("ext,expected", [
        (".nes",  "NES"),
        (".sfc",  "SNES"),
        (".smc",  "SNES"),
        (".gb",   "Game Boy"),
        (".gbc",  "Game Boy Color"),
        (".gba",  "Game Boy Advance"),
        (".nds",  "Nintendo DS"),
        (".3ds",  "Nintendo 3DS"),
        (".cia",  "Nintendo 3DS"),
        (".gcm",  "GameCube"),
        (".wbfs", "Wii"),
        (".wud",  "Wii U"),
        (".nsp",  "Nintendo Switch"),
        (".xci",  "Nintendo Switch"),
        (".sms",  "Master System"),
        (".gg",   "Game Gear"),
        (".gen",  "Sega Genesis"),
        (".cdi",  "Dreamcast"),
        (".gdi",  "Dreamcast"),
        (".pbp",  "PlayStation"),
        (".cso",  "PSP"),
        (".vpk",  "PS Vita"),
        (".a26",  "Atari 2600"),
        (".a52",  "Atari 5200"),
        (".a78",  "Atari 7800"),
        (".lnx",  "Atari Lynx"),
        (".j64",  "Atari Jaguar"),
        (".jag",  "Atari Jaguar"),
    ])
    def test_extension(self, ext: str, expected: str) -> None:
        assert detect_platform(Path(f"game{ext}")) == expected

    def test_uppercase_extension(self) -> None:
        assert detect_platform(Path("game.GBA")) == "Game Boy Advance"

    def test_unknown_extension_returns_none(self) -> None:
        assert detect_platform(Path("game.xyz")) is None


# ── detect_platform — .md files (context-dependent) ──────────────────────────

class TestDetectPlatformMd:
    def test_md_in_megadrive_folder(self) -> None:
        assert detect_platform(Path("/roms/megadrive/Sonic.md")) == "Sega Mega Drive"

    def test_md_in_genesis_folder(self) -> None:
        assert detect_platform(Path("/roms/genesis/Sonic.md")) == "Sega Mega Drive"

    def test_md_in_md_folder(self) -> None:
        assert detect_platform(Path("/roms/md/game.md")) == "Sega Mega Drive"

    def test_md_without_context_returns_none(self) -> None:
        assert detect_platform(Path("/docs/notes.md")) is None

    def test_md_in_unrelated_folder(self) -> None:
        assert detect_platform(Path("/mygames/game.md")) is None


# ── detect_platform — ambiguous extensions (folder context) ───────────────────

class TestDetectPlatformAmbiguous:
    @pytest.mark.parametrize("folder,expected", [
        ("psx",          "PlayStation"),
        ("ps1",          "PlayStation"),
        ("ps2",          "PlayStation 2"),
        ("ps3",          "PlayStation 3"),
        ("psp",          "PSP"),
        ("psvita",       "PS Vita"),
        ("saturn",       "Sega Saturn"),
        ("segasaturn",   "Sega Saturn"),
        ("dreamcast",    "Dreamcast"),
        ("megadrive",    "Sega Mega Drive"),
        ("genesis",      "Sega Mega Drive"),
        ("mastersystem", "Master System"),
        ("gamegear",     "Game Gear"),
        ("neogeo",       "Neo Geo"),
        ("gamecube",     "GameCube"),
        ("ngc",          "GameCube"),
        ("wii",          "Wii"),
        ("n64",          "Nintendo 64"),
        ("nds",          "Nintendo DS"),
        ("gba",          "Game Boy Advance"),
        ("gbc",          "Game Boy Color"),
        ("gb",           "Game Boy"),
        ("nes",          "NES"),
        ("snes",         "SNES"),
        ("atari2600",    "Atari 2600"),
        ("atarilynx",    "Atari Lynx"),
        ("segacd",       "Sega CD"),
        ("sega32x",      "Sega 32X"),
        ("32x",          "Sega 32X"),
    ])
    def test_iso_in_folder(self, folder: str, expected: str) -> None:
        assert detect_platform(Path(f"/roms/{folder}/game.iso")) == expected

    def test_chd_in_saturn_folder(self) -> None:
        assert detect_platform(Path("/roms/saturn/game.chd")) == "Sega Saturn"

    def test_bin_in_psx_folder(self) -> None:
        assert detect_platform(Path("/roms/psx/game.bin")) == "PlayStation"

    def test_case_insensitive_folder(self) -> None:
        assert detect_platform(Path("/ROMS/MEGADRIVE/Sonic.bin")) == "Sega Mega Drive"

    def test_ambiguous_no_known_folder_returns_none(self) -> None:
        assert detect_platform(Path("/roms/games/game.iso")) is None

    def test_nested_path_uses_any_ancestor(self) -> None:
        # The platform folder can be anywhere in the path
        assert detect_platform(Path("/library/psx/subdir/game.bin")) == "PlayStation"


# ── Platform consistency: _ES_PLATFORM_FOLDERS aligns with platform_detector ──

class TestEsPlatformFoldersConsistency:
    """Verify that platform_detector output strings match keys in _ES_PLATFORM_FOLDERS."""

    def test_saturn_mapped_correctly(self) -> None:
        """saturn folder → 'Sega Saturn' → should find 'saturn' in ES folder map."""
        from rom_manager.web.server import _ES_PLATFORM_FOLDERS
        platform = detect_platform(Path("/roms/saturn/game.chd"))
        assert platform == "Sega Saturn"
        assert _ES_PLATFORM_FOLDERS.get(platform) == "saturn", (
            f"'{platform}' not in _ES_PLATFORM_FOLDERS or maps to wrong folder"
        )

    def test_megadrive_mapped_correctly(self) -> None:
        from rom_manager.web.server import _ES_PLATFORM_FOLDERS
        platform = detect_platform(Path("/roms/megadrive/game.bin"))
        assert _ES_PLATFORM_FOLDERS.get(platform) == "megadrive"

    def test_psx_mapped_correctly(self) -> None:
        from rom_manager.web.server import _ES_PLATFORM_FOLDERS
        platform = detect_platform(Path("/roms/psx/game.bin"))
        assert platform == "PlayStation"
        assert _ES_PLATFORM_FOLDERS.get(platform) == "psx"

    def test_all_folder_platforms_have_es_mapping(self) -> None:
        """Every platform string returned by folder-based detection should have an ES-DE mapping."""
        from rom_manager.web.server import _ES_PLATFORM_FOLDERS

        # These platforms are intentionally not mapped (arcade, obscure platforms)
        unmapped_ok = {"Arcade", "Neo Geo Pocket Color"}

        folder_platforms = set(PLATFORM_BY_FOLDER.values())
        extension_platforms = set(PLATFORM_BY_EXTENSION.values())
        all_platforms = folder_platforms | extension_platforms

        missing = {
            p for p in all_platforms
            if p not in _ES_PLATFORM_FOLDERS and p not in unmapped_ok
        }
        assert missing == set(), (
            f"Platforms returned by detector but missing from _ES_PLATFORM_FOLDERS: {missing}\n"
            "Add them to server._ES_PLATFORM_FOLDERS to ensure organize-library works."
        )

    def test_standard_folders_subset_of_es_folders(self) -> None:
        """Every folder in _STANDARD_PLATFORM_FOLDERS must exist as a value in _ES_PLATFORM_FOLDERS."""
        from rom_manager.web.server import _ES_PLATFORM_FOLDERS, _STANDARD_PLATFORM_FOLDERS
        es_values = set(_ES_PLATFORM_FOLDERS.values())
        missing = set(_STANDARD_PLATFORM_FOLDERS) - es_values - {"saves", "bios", "inbox"}
        assert missing == set(), (
            f"Folders in _STANDARD_PLATFORM_FOLDERS not reachable via _ES_PLATFORM_FOLDERS: {missing}"
        )
