"""INBOX-FIX-5: a shared filename must never be treated as proof of duplicate
content — only a SHA1 match may."""

from __future__ import annotations

from pathlib import Path

from rom_manager.web.inbox_pipeline import _same_content


def test_same_content_identical_bytes(tmp_path: Path) -> None:
    a = tmp_path / "a.nes"
    b = tmp_path / "b.nes"
    a.write_bytes(b"same rom data")
    b.write_bytes(b"same rom data")
    assert _same_content(a, b) is True


def test_same_content_different_bytes_same_size(tmp_path: Path) -> None:
    """Same name/size, different content — the exact scenario that caused real data loss."""
    a = tmp_path / "a.nes"
    b = tmp_path / "b.nes"
    a.write_bytes(b"revision one!")
    b.write_bytes(b"revision two!")
    assert len(a.read_bytes()) == len(b.read_bytes())
    assert _same_content(a, b) is False


def test_same_content_different_size_short_circuits(tmp_path: Path) -> None:
    a = tmp_path / "a.nes"
    b = tmp_path / "b.nes"
    a.write_bytes(b"short")
    b.write_bytes(b"much longer content here")
    assert _same_content(a, b) is False


def test_same_content_missing_file_returns_false(tmp_path: Path) -> None:
    a = tmp_path / "a.nes"
    a.write_bytes(b"x")
    assert _same_content(a, tmp_path / "missing.nes") is False
