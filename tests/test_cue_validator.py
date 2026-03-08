from __future__ import annotations

from pathlib import Path

import pytest

from rom_manager.detection.cue_validator import validate_cue


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Complete set (no errors expected)
# ---------------------------------------------------------------------------

def test_valid_cue_single_bin(tmp_path: Path) -> None:
    (tmp_path / "game.bin").write_bytes(b"\x00" * 8)
    cue = _write(tmp_path, "game.cue", 'FILE "game.bin" BINARY\n  TRACK 01 MODE2/2352\n')
    assert validate_cue(cue) == []


def test_valid_cue_multiple_bins(tmp_path: Path) -> None:
    for i in (1, 2, 3):
        (tmp_path / f"disc{i}.bin").write_bytes(b"\x00")
    cue = _write(
        tmp_path,
        "multi.cue",
        'FILE "disc1.bin" BINARY\nFILE "disc2.bin" BINARY\nFILE "disc3.bin" BINARY\n',
    )
    assert validate_cue(cue) == []


# ---------------------------------------------------------------------------
# Missing bins
# ---------------------------------------------------------------------------

def test_missing_single_bin(tmp_path: Path) -> None:
    cue = _write(tmp_path, "game.cue", 'FILE "game.bin" BINARY\n')
    errors = validate_cue(cue)
    assert len(errors) == 1
    assert "game.bin" in errors[0]


def test_missing_one_of_two_bins(tmp_path: Path) -> None:
    (tmp_path / "present.bin").write_bytes(b"\x00")
    cue = _write(
        tmp_path,
        "game.cue",
        'FILE "present.bin" BINARY\nFILE "missing.bin" BINARY\n',
    )
    errors = validate_cue(cue)
    assert len(errors) == 1
    assert "missing.bin" in errors[0]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_cue(tmp_path: Path) -> None:
    cue = _write(tmp_path, "empty.cue", "")
    assert validate_cue(cue) == []


def test_cue_with_no_file_lines(tmp_path: Path) -> None:
    cue = _write(tmp_path, "no_files.cue", "CATALOG 1234567890123\nTRACK 01 AUDIO\n")
    assert validate_cue(cue) == []


def test_nonexistent_cue_returns_empty(tmp_path: Path) -> None:
    cue = tmp_path / "ghost.cue"
    assert validate_cue(cue) == []


def test_case_insensitive_file_keyword(tmp_path: Path) -> None:
    """FILE keyword matching should be case-insensitive."""
    cue = _write(tmp_path, "game.cue", 'file "missing.bin" BINARY\n')
    errors = validate_cue(cue)
    assert len(errors) == 1
    assert "missing.bin" in errors[0]
