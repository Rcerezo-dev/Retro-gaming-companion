"""Tests for rom_header.extract_internal_id (MATCH-HEADER-1)."""

from __future__ import annotations

from pathlib import Path

from rom_manager.detection.rom_header import extract_internal_id


def _write_nds(path: Path, title: bytes, code: bytes) -> None:
    data = bytearray(0x200)
    data[0x00 : 0x00 + len(title)] = title
    data[0x0C : 0x0C + len(code)] = code
    path.write_bytes(bytes(data))


def _write_gba(path: Path, title: bytes, code: bytes, *, fixed_byte: int = 0x96) -> None:
    data = bytearray(0x200)
    data[0xA0 : 0xA0 + len(title)] = title
    data[0xAC : 0xAC + len(code)] = code
    data[0xB2] = fixed_byte
    path.write_bytes(bytes(data))


def _gb_checksum(data: bytes) -> int:
    x = 0
    for byte in data[0x134:0x14D]:
        x = (x - byte - 1) & 0xFF
    return x


def _write_gb(path: Path, title: bytes, *, valid_checksum: bool = True) -> None:
    data = bytearray(0x200)
    data[0x134 : 0x134 + len(title)] = title
    if valid_checksum:
        data[0x14D] = _gb_checksum(bytes(data))
    path.write_bytes(bytes(data))


def test_nds_header_reads_game_code(tmp_path: Path) -> None:
    p = tmp_path / "game.nds"
    _write_nds(p, b"KIRBY USDX P", b"YKWP")
    assert extract_internal_id(p, ".nds") == "YKWP"


def test_gba_header_reads_game_code(tmp_path: Path) -> None:
    p = tmp_path / "game.gba"
    _write_gba(p, b"NARUTO US2", b"BN2E")
    assert extract_internal_id(p, ".gba") == "BN2E"


def test_gb_header_reads_internal_title(tmp_path: Path) -> None:
    p = tmp_path / "game.gb"
    _write_gb(p, b"TETRIS")
    internal_id = extract_internal_id(p, ".gb")
    assert internal_id is not None
    assert internal_id.startswith("TETRIS:")


def test_gbc_uses_same_reader_as_gb(tmp_path: Path) -> None:
    p = tmp_path / "game.gbc"
    _write_gb(p, b"POKEMON GOLD")
    internal_id = extract_internal_id(p, ".gbc")
    assert internal_id is not None
    assert internal_id.startswith("POKEMON GOLD:")


def test_gb_rejects_invalid_checksum(tmp_path: Path) -> None:
    """MATCH-FIX-14: a corrupt dump or a misclassified non-GB/GBC file could
    coincidentally have a plausible-looking title but real hardware would
    refuse to boot it if the header checksum doesn't match — same
    conservative treatment as the GBA fixed-byte check."""
    p = tmp_path / "game.gb"
    _write_gb(p, b"TETRIS", valid_checksum=False)
    assert extract_internal_id(p, ".gb") is None


def test_gb_same_title_different_config_gets_different_id(tmp_path: Path) -> None:
    """The checksum folds in cart type/ROM+RAM size/region/version, not just
    the title -- two different games that happen to share a truncated title
    but differ in any of those fields must not collide on the same id."""
    p1 = tmp_path / "a.gb"
    data1 = bytearray(0x200)
    data1[0x134 : 0x134 + len(b"SAME TITLE")] = b"SAME TITLE"
    data1[0x148] = 0x00  # ROM size field
    data1[0x14D] = _gb_checksum(bytes(data1))
    p1.write_bytes(bytes(data1))

    p2 = tmp_path / "b.gb"
    data2 = bytearray(0x200)
    data2[0x134 : 0x134 + len(b"SAME TITLE")] = b"SAME TITLE"
    data2[0x148] = 0x05  # different ROM size field -> different checksum
    data2[0x14D] = _gb_checksum(bytes(data2))
    p2.write_bytes(bytes(data2))

    id1 = extract_internal_id(p1, ".gb")
    id2 = extract_internal_id(p2, ".gb")
    assert id1 is not None and id2 is not None
    assert id1 != id2


def test_unsupported_extension_returns_none(tmp_path: Path) -> None:
    p = tmp_path / "game.zip"
    p.write_bytes(b"PK\x03\x04" + b"\x00" * 100)
    assert extract_internal_id(p, ".zip") is None


def test_missing_file_returns_none(tmp_path: Path) -> None:
    assert extract_internal_id(tmp_path / "nope.nds", ".nds") is None


def test_truncated_file_returns_none(tmp_path: Path) -> None:
    p = tmp_path / "tiny.nds"
    p.write_bytes(b"\x00" * 4)
    assert extract_internal_id(p, ".nds") is None


def test_empty_header_field_returns_none(tmp_path: Path) -> None:
    p = tmp_path / "blank.gba"
    p.write_bytes(b"\x00" * 0x200)
    assert extract_internal_id(p, ".gba") is None


def test_gba_rejects_file_with_wrong_fixed_byte(tmp_path: Path) -> None:
    """MATCH-HEADER-1 safety check: a file whose DB platform says "Game Boy
    Advance" but whose actual bytes are something else entirely (confirmed
    live 2026-09-12: 2 rows with platform="Game Boy Advance" whose
    source_path pointed at a real Sega Mega Drive .md file) must not have
    whatever garbage sits at the GBA game-code offset treated as a real
    code — the fixed validation byte (always 0x96 on a real GBA cart) is
    the cheap way to reject it."""
    p = tmp_path / "not_actually_gba.gba"
    _write_gba(p, b"SOMETHING", b"ABCD", fixed_byte=0x00)
    assert extract_internal_id(p, ".gba") is None


def test_gba_rejects_non_code_garbage_even_with_right_fixed_byte(tmp_path: Path) -> None:
    """Even with a coincidentally-correct fixed byte, 4 bytes that aren't a
    plausible Nintendo code (uppercase letters/digits only) are rejected —
    real garbage from an unrelated file is very unlikely to land on 4 clean
    A-Z0-9 characters by chance."""
    p = tmp_path / "game.gba"
    _write_gba(p, b"TITLE", b"\xff\x01\x02\x03")
    assert extract_internal_id(p, ".gba") is None


def test_nds_rejects_non_code_garbage(tmp_path: Path) -> None:
    p = tmp_path / "game.nds"
    _write_nds(p, b"TITLE", b"\x01\x02\x03\x04")
    assert extract_internal_id(p, ".nds") is None
