"""INBOX-FIX-1: a single colliding member must not abort the whole ZIP."""

from __future__ import annotations

import zipfile
from pathlib import Path

from rom_manager.converters.zip_extractor import extract_zip


def _make_zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)


def test_partial_collision_extracts_the_rest(tmp_path: Path) -> None:
    """One pre-existing member used to abort extraction of the other 2 (old bug)."""
    zip_path = tmp_path / "collection.zip"
    _make_zip(zip_path, {"a.rom": b"a", "b.rom": b"b", "c.rom": b"c"})
    (tmp_path / "b.rom").write_bytes(b"already here")  # collision

    result = extract_zip(zip_path, dry_run=False, delete_source=False)

    assert result.success
    assert (tmp_path / "a.rom").read_bytes() == b"a"
    assert (tmp_path / "c.rom").read_bytes() == b"c"
    assert (tmp_path / "b.rom").read_bytes() == b"already here"  # untouched, not overwritten
    assert {p.name for p in result.extracted_files} == {"a.rom", "c.rom"}
    assert {p.name for p in result.skipped_existing} == {"b.rom"}


def test_delete_source_after_full_resolution(tmp_path: Path) -> None:
    """Source ZIP is only deleted once every member is confirmed on disk."""
    zip_path = tmp_path / "collection.zip"
    _make_zip(zip_path, {"a.rom": b"a", "b.rom": b"b"})
    (tmp_path / "b.rom").write_bytes(b"already here")  # collision, but content is present

    result = extract_zip(zip_path, dry_run=False, delete_source=True)

    assert result.success
    assert not zip_path.exists()


def test_dry_run_does_not_touch_disk(tmp_path: Path) -> None:
    zip_path = tmp_path / "collection.zip"
    _make_zip(zip_path, {"a.rom": b"a"})

    result = extract_zip(zip_path, dry_run=True, delete_source=True)

    assert result.success
    assert not (tmp_path / "a.rom").exists()
    assert zip_path.exists()


def test_arcade_folder_zip_is_never_extracted(tmp_path: Path) -> None:
    arcade_dir = tmp_path / "mame"
    arcade_dir.mkdir()
    zip_path = arcade_dir / "pacman.zip"
    _make_zip(zip_path, {"pacman.6e": b"chip"})

    result = extract_zip(zip_path, dry_run=False, delete_source=True)

    assert not result.success
    assert result.skipped_reason
    assert zip_path.exists()
    assert not (arcade_dir / "pacman.6e").exists()
