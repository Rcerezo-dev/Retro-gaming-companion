from __future__ import annotations

from pathlib import Path

from rom_manager.renamer.cue_rewriter import rewrite_cue


def _write_cue(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_rewrite_single_bin(tmp_path: Path) -> None:
    cue = _write_cue(
        tmp_path / "game.cue",
        'FILE "game.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n',
    )
    changed = rewrite_cue(cue, "game.bin", "Game Title (USA).bin")
    assert changed is True
    text = cue.read_text(encoding="utf-8")
    assert 'FILE "Game Title (USA).bin" BINARY' in text
    assert "game.bin" not in text


def test_rewrite_multi_bin(tmp_path: Path) -> None:
    content = (
        'FILE "disc1.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n'
        'FILE "disc1_audio.bin" BINARY\n  TRACK 02 AUDIO\n    INDEX 01 00:00:00\n'
    )
    cue = _write_cue(tmp_path / "disc1.cue", content)
    changed = rewrite_cue(cue, "disc1.bin", "Game (USA).bin")
    assert changed is True
    text = cue.read_text(encoding="utf-8")
    assert 'FILE "Game (USA).bin" BINARY' in text
    assert 'FILE "disc1_audio.bin" BINARY' in text  # untouched


def test_no_change_when_bin_not_referenced(tmp_path: Path) -> None:
    cue = _write_cue(
        tmp_path / "game.cue",
        'FILE "other.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n',
    )
    changed = rewrite_cue(cue, "game.bin", "New Name.bin")
    assert changed is False
    assert "other.bin" in cue.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Case-insensitive matching
# ---------------------------------------------------------------------------

def test_case_insensitive_match(tmp_path: Path) -> None:
    cue = _write_cue(
        tmp_path / "game.cue",
        'FILE "GAME.BIN" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n',
    )
    changed = rewrite_cue(cue, "game.bin", "New Game.bin")
    assert changed is True
    assert 'FILE "New Game.bin" BINARY' in cue.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Subdirectory guard
# ---------------------------------------------------------------------------

def test_skips_subdirectory_bin(tmp_path: Path) -> None:
    """If old_bin has a path component, rewrite_cue must do nothing."""
    cue = _write_cue(
        tmp_path / "game.cue",
        'FILE "subdir/game.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n',
    )
    changed = rewrite_cue(cue, "subdir/game.bin", "New.bin")
    assert changed is False


# ---------------------------------------------------------------------------
# Newline preservation
# ---------------------------------------------------------------------------

def test_newlines_preserved(tmp_path: Path) -> None:
    content = 'FILE "a.bin" BINARY\r\n  TRACK 01 MODE2/2352\r\n    INDEX 01 00:00:00\r\n'
    cue = _write_cue(tmp_path / "game.cue", content)
    rewrite_cue(cue, "a.bin", "B.bin")
    result = cue.read_text(encoding="utf-8")
    assert 'FILE "B.bin" BINARY' in result
