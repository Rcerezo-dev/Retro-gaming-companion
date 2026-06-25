"""Tests for clrmamepro DAT parser and format sniffer — DAT-DL-0."""

from __future__ import annotations

from pathlib import Path

from rom_manager.catalog.catalog_loader import (
    _detect_dat_format,
    load_clrmamepro_dat,
    load_dat_directory,
)

# Minimal clrmamepro DAT fixture (realistic subset of No-Intro PSX format)
_CLRMAME_DAT = """\
clrmamepro (
\tname "No-Intro: Sony - PlayStation"
\tdescription "No-Intro: Sony - PlayStation"
\tversion "20260502-190453"
\tauthor "no-intro"
)

game (
\tname "Oddworld - Abe's Oddysee (USA)"
\tdescription "Oddworld - Abe's Oddysee (USA)"
\trom ( name "Oddworld - Abe's Oddysee (USA).bin" size 622297088 crc f26d7a0b md5 aabbccdd sha1 AABBCCDDEEFF00112233445566778899AABBCCDD )
)

game (
\tname "Parasite Eve (USA) (Disc 1)"
\tdescription "Parasite Eve (USA) (Disc 1)"
\trom ( name "Parasite Eve (USA) (Disc 1).bin" size 697892864 crc 12345678 md5 11223344 sha1 1122334455667788990011223344556677889900 )
)

game (
\tname "No SHA1 Game"
\trom ( name "bad.bin" size 0 crc 00000000 md5 00000000 )
)
"""

_XML_DAT = """\
<?xml version="1.0"?>
<datafile>
  <header><name>No-Intro: Game Boy</name></header>
  <game name="Tetris (World)">
    <rom name="Tetris (World).gb" size="32768" crc="46df91ad" md5="aabb" sha1="CCDD00112233445566778899AABBCCDD00112233"/>
  </game>
</datafile>
"""


class TestFormatSniffer:
    def test_detects_xml(self, tmp_path: Path) -> None:
        f = tmp_path / "nointro.dat"
        f.write_text(_XML_DAT, encoding="utf-8")
        assert _detect_dat_format(f) == "xml"

    def test_detects_clrmamepro(self, tmp_path: Path) -> None:
        f = tmp_path / "nointro.dat"
        f.write_text(_CLRMAME_DAT, encoding="utf-8")
        assert _detect_dat_format(f) == "clrmamepro"

    def test_empty_file_defaults_to_xml(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.dat"
        f.write_bytes(b"")
        assert _detect_dat_format(f) == "xml"


class TestClrmamepro:
    def test_parses_game_count(self, tmp_path: Path) -> None:
        f = tmp_path / "psx.dat"
        f.write_text(_CLRMAME_DAT, encoding="utf-8")
        entries = load_clrmamepro_dat(f)
        assert len(entries) == 2  # "No SHA1 Game" skipped

    def test_sha1_key_uppercase(self, tmp_path: Path) -> None:
        f = tmp_path / "psx.dat"
        f.write_text(_CLRMAME_DAT, encoding="utf-8")
        entries = load_clrmamepro_dat(f)
        assert "AABBCCDDEEFF00112233445566778899AABBCCDD" in entries

    def test_title_extracted(self, tmp_path: Path) -> None:
        f = tmp_path / "psx.dat"
        f.write_text(_CLRMAME_DAT, encoding="utf-8")
        entries = load_clrmamepro_dat(f)
        entry = entries["AABBCCDDEEFF00112233445566778899AABBCCDD"]
        assert entry.title == "Oddworld - Abe's Oddysee (USA)"

    def test_md5_crc_extracted(self, tmp_path: Path) -> None:
        f = tmp_path / "psx.dat"
        f.write_text(_CLRMAME_DAT, encoding="utf-8")
        entries = load_clrmamepro_dat(f)
        entry = entries["AABBCCDDEEFF00112233445566778899AABBCCDD"]
        assert entry.md5 == "AABBCCDD"
        assert entry.crc32 == "F26D7A0B"

    def test_size_extracted(self, tmp_path: Path) -> None:
        f = tmp_path / "psx.dat"
        f.write_text(_CLRMAME_DAT, encoding="utf-8")
        entries = load_clrmamepro_dat(f)
        entry = entries["AABBCCDDEEFF00112233445566778899AABBCCDD"]
        assert entry.size_bytes == 622297088

    def test_game_without_sha1_skipped(self, tmp_path: Path) -> None:
        f = tmp_path / "psx.dat"
        f.write_text(_CLRMAME_DAT, encoding="utf-8")
        entries = load_clrmamepro_dat(f)
        titles = {e.title for e in entries.values()}
        assert "No SHA1 Game" not in titles


class TestLoadDatDirectoryMixedFormats:
    def test_loads_clrmamepro_alongside_xml(self, tmp_path: Path) -> None:
        (tmp_path / "psx.dat").write_text(_CLRMAME_DAT, encoding="utf-8")
        (tmp_path / "gb.dat").write_text(_XML_DAT, encoding="utf-8")
        merged = load_dat_directory(tmp_path)
        assert "AABBCCDDEEFF00112233445566778899AABBCCDD" in merged
        assert "CCDD00112233445566778899AABBCCDD00112233" in merged
