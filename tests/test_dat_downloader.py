"""Tests for dat_downloader.py — DAT-DL-1 + DAT-DL-2."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from rom_manager.catalog.dat_downloader import (
    _PLATFORM_DAT_MAP,
    _SUBDIR,
    dat_url,
    download_dat,
    known_platforms,
)

# ---------------------------------------------------------------------------
# Minimal valid DAT payloads (used as fake HTTP response bodies)
# ---------------------------------------------------------------------------

_XML_DAT_BYTES = b"""\
<?xml version="1.0"?>
<datafile>
  <header><name>Test Platform</name></header>
  <game name="Tetris (World)">
    <rom name="Tetris (World).gb" size="32768" crc="46df91ad"
         md5="aabb" sha1="CCDD00112233445566778899AABBCCDD00112233"/>
  </game>
</datafile>
"""

_CLRMAME_DAT_BYTES = b"""\
clrmamepro (
\tname "No-Intro: Test"
)

game (
\tname "Driver 2 (USA)"
\trom ( name "Driver 2 (USA).bin" size 1024 crc aabbccdd md5 11223344 sha1 AABBCCDDEEFF00112233445566778899AABBCCDD )
)
"""

_EMPTY_XML_BYTES = b"""\
<?xml version="1.0"?>
<datafile><header><name>Empty</name></header></datafile>
"""


def _fake_urlopen(payload: bytes):
    """Return a context-manager mock that yields *payload* bytes."""
    resp = MagicMock()
    resp.read.return_value = payload
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ---------------------------------------------------------------------------
# DAT-DL-1: mapping table
# ---------------------------------------------------------------------------


class TestPlatformDatMap:
    def test_well_known_platforms_present(self) -> None:
        must_have = [
            "NES",
            "SNES",
            "Game Boy",
            "Game Boy Color",
            "Game Boy Advance",
            "Nintendo DS",
            "Nintendo 64",
            "Sega Mega Drive",
            "Master System",
            "Game Gear",
            "Sega Saturn",
            "Dreamcast",
            "PlayStation",
            "PlayStation 2",
            "PSP",
            "PC Engine",
            "Atari 2600",
        ]
        for plat in must_have:
            assert plat in _PLATFORM_DAT_MAP, f"Missing mapping for '{plat}'"

    def test_sources_are_valid(self) -> None:
        valid = {"no-intro", "redump"}
        for plat, (source, _) in _PLATFORM_DAT_MAP.items():
            assert source in valid, f"Unknown source '{source}' for '{plat}'"

    def test_stems_are_non_empty(self) -> None:
        for plat, (_, stem) in _PLATFORM_DAT_MAP.items():
            assert stem.strip(), f"Empty stem for '{plat}'"

    def test_url_format(self) -> None:
        url = dat_url("PlayStation")
        assert url is not None
        assert url.startswith("https://raw.githubusercontent.com/libretro/")
        assert url.endswith(".dat")
        assert "redump" in url

    def test_no_intro_url_path(self) -> None:
        url = dat_url("NES")
        assert url is not None
        assert "/no-intro/" in url

    def test_unknown_platform_returns_none(self) -> None:
        assert dat_url("Ouya") is None

    def test_known_platforms_sorted(self) -> None:
        platforms = known_platforms()
        assert platforms == sorted(platforms)
        assert len(platforms) == len(_PLATFORM_DAT_MAP)

    def test_subdir_mapping_complete(self) -> None:
        sources_in_map = {src for src, _ in _PLATFORM_DAT_MAP.values()}
        for source in sources_in_map:
            assert source in _SUBDIR, f"No _SUBDIR entry for source '{source}'"


# ---------------------------------------------------------------------------
# DAT-DL-2: download_dat()
# ---------------------------------------------------------------------------


class TestDownloadDat:
    def test_unknown_platform_fails_gracefully(self, tmp_path: Path) -> None:
        result = download_dat("Ouya", tmp_path)
        assert not result.success
        assert "Ouya" in result.error
        assert result.path is None

    def test_successful_xml_download(self, tmp_path: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(_XML_DAT_BYTES)):
            result = download_dat("Game Boy", tmp_path)
        assert result.success
        assert result.entries == 1
        assert result.path is not None
        assert result.path.exists()

    def test_successful_clrmamepro_download(self, tmp_path: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(_CLRMAME_DAT_BYTES)):
            result = download_dat("PlayStation", tmp_path)
        assert result.success
        assert result.entries == 1

    def test_file_placed_in_correct_subdir(self, tmp_path: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(_XML_DAT_BYTES)):
            result = download_dat("Game Boy", tmp_path)
        assert result.path is not None
        assert result.path.parent.name == "nointro"

    def test_redump_platform_in_redump_subdir(self, tmp_path: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(_XML_DAT_BYTES)):
            result = download_dat("PlayStation", tmp_path)
        assert result.path is not None
        assert result.path.parent.name == "redump"

    def test_subdir_created_if_missing(self, tmp_path: Path) -> None:
        dest = tmp_path / "catalogs"
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(_XML_DAT_BYTES)):
            result = download_dat("NES", dest)
        assert result.success
        assert (dest / "nointro").is_dir()

    def test_network_error_graceful(self, tmp_path: Path) -> None:
        import urllib.error

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            result = download_dat("SNES", tmp_path)
        assert not result.success
        assert "red" in result.error.lower()
        assert result.path is None

    def test_empty_dat_fails_gracefully(self, tmp_path: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(_EMPTY_XML_BYTES)):
            result = download_dat("Game Boy", tmp_path)
        assert not result.success
        assert "0 entradas" in result.error
        # file should be cleaned up
        assert not any(tmp_path.rglob("*.dat"))

    def test_corrupt_dat_fails_gracefully(self, tmp_path: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(b"not xml not clrm")):
            result = download_dat("Game Boy", tmp_path)
        assert not result.success
        assert result.path is None
