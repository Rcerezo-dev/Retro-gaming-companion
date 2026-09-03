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


def test_arcade_zip_in_unaudited_folder_caught_by_crc(tmp_path: Path) -> None:
    """DECOMPRESS-ARCADE-GAP-3: folder name alone misses a set sitting outside
    a recognized arcade/MAME folder — the CRC index must still catch it."""
    misplaced_dir = tmp_path / "psx"  # not an arcade-named folder
    misplaced_dir.mkdir()
    zip_path = misplaced_dir / "pacman.zip"
    _make_zip(zip_path, {"pacman.6e": b"chip"})
    crc = zipfile.ZipFile(zip_path).infolist()[0].CRC
    arcade_crc_index = {f"{crc:08X}": {"pacman"}}

    result = extract_zip(
        zip_path, dry_run=False, delete_source=True, arcade_crc_index=arcade_crc_index
    )

    assert not result.success
    assert result.skipped_reason
    assert zip_path.exists()
    assert not (misplaced_dir / "pacman.6e").exists()


def test_cue_bin_set_is_not_extracted(tmp_path: Path) -> None:
    """A multi-track set needs chdman, not a raw unzip of its .cue/.bin."""
    zip_path = tmp_path / "Game (USA).zip"
    _make_zip(zip_path, {"Game (USA).cue": b"cue", "Game (USA) (Track 1).bin": b"bin"})

    result = extract_zip(zip_path, dry_run=False, delete_source=True)

    assert not result.success
    assert result.skipped_reason
    assert zip_path.exists()


def test_lone_iso_is_extracted(tmp_path: Path) -> None:
    """INBOX-FIX-6: a single-file disc image (PS2/GameCube) has no set to
    reconstruct — extracting it plain makes it playable, unlike a cue/bin set."""
    zip_path = tmp_path / "Game (USA).zip"
    _make_zip(zip_path, {"Game (USA).iso": b"isodata"})

    result = extract_zip(zip_path, dry_run=False, delete_source=True)

    assert result.success
    assert (tmp_path / "Game (USA).iso").read_bytes() == b"isodata"
    assert not zip_path.exists()
