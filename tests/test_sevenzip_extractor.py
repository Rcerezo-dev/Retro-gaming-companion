"""JUNK-SCAN-RUBEN-1: extractor de .7z con las mismas garantías de seguridad
que zip_extractor.extract_zip() -- no sobreescribe, solo borra el origen
cuando todos los miembros quedan confirmados en disco."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from rom_manager.converters.sevenzip_extractor import (
    extract_7z,
    extract_7z_directory,
    find_7z_files,
    list_7z_members,
)
from rom_manager.utils.subprocess_flags import NO_WINDOW

_SEVENZIP = Path(__file__).resolve().parent.parent / "tools" / "7z.exe"
_skip_no_7z = pytest.mark.skipif(not _SEVENZIP.exists(), reason="7z.exe no disponible en tools/")


def _make_7z(path: Path, members: dict[str, bytes]) -> None:
    """Build a real .7z archive via the bundled binary itself -- there is no
    stdlib writer for this format, same reasoning as needing it to read one.
    Runs with cwd=src_dir and relative member names so they land at the
    archive root (not nested under the throwaway source folder)."""
    src_dir = path.parent / f"_src_{path.stem}"
    src_dir.mkdir(exist_ok=True)
    for name, data in members.items():
        member_path = src_dir / name
        member_path.parent.mkdir(parents=True, exist_ok=True)
        member_path.write_bytes(data)
    args = [str(_SEVENZIP), "a", str(path), *members.keys()]
    subprocess.run(args, check=True, capture_output=True, cwd=str(src_dir), creationflags=NO_WINDOW)


@_skip_no_7z
def test_partial_collision_extracts_the_rest(tmp_path: Path) -> None:
    archive = tmp_path / "collection.7z"
    _make_7z(archive, {"a.rom": b"a", "b.rom": b"b", "c.rom": b"c"})
    (tmp_path / "b.rom").write_bytes(b"already here")  # collision

    result = extract_7z(archive, sevenzip=str(_SEVENZIP), dry_run=False, delete_source=False)

    assert result.success
    assert (tmp_path / "a.rom").read_bytes() == b"a"
    assert (tmp_path / "c.rom").read_bytes() == b"c"
    assert (tmp_path / "b.rom").read_bytes() == b"already here"  # untouched, not overwritten
    assert {p.name for p in result.extracted_files} == {"a.rom", "c.rom"}
    assert {p.name for p in result.skipped_existing} == {"b.rom"}


@_skip_no_7z
def test_delete_source_after_full_resolution(tmp_path: Path) -> None:
    archive = tmp_path / "collection.7z"
    _make_7z(archive, {"a.rom": b"a", "b.rom": b"b"})
    (tmp_path / "b.rom").write_bytes(b"already here")  # collision, but content is present

    result = extract_7z(archive, sevenzip=str(_SEVENZIP), dry_run=False, delete_source=True)

    assert result.success
    assert not archive.exists()


@_skip_no_7z
def test_dry_run_does_not_touch_disk(tmp_path: Path) -> None:
    archive = tmp_path / "collection.7z"
    _make_7z(archive, {"a.rom": b"a"})

    result = extract_7z(archive, sevenzip=str(_SEVENZIP), dry_run=True, delete_source=True)

    assert result.success
    assert not (tmp_path / "a.rom").exists()
    assert archive.exists()


@_skip_no_7z
def test_arcade_folder_7z_is_never_extracted(tmp_path: Path) -> None:
    arcade_dir = tmp_path / "mame"
    arcade_dir.mkdir()
    archive = arcade_dir / "pacman.7z"
    _make_7z(archive, {"pacman.6e": b"chip"})

    result = extract_7z(archive, sevenzip=str(_SEVENZIP), dry_run=False, delete_source=True)

    assert not result.success
    assert result.skipped_reason
    assert archive.exists()
    assert not (arcade_dir / "pacman.6e").exists()


@_skip_no_7z
def test_gdi_disc_set_is_not_extracted(tmp_path: Path) -> None:
    """A single-disc Dreamcast GDI set has no "(Disc N)" in its filename but
    is still a multi-track set that needs the CHD converter, not a raw unzip
    -- real case found in this library's Unknown/ (JUNK-7Z-SUPPORT-1)."""
    archive = tmp_path / "Jet Set Radio (Europe).7z"
    _make_7z(
        archive,
        {
            "Jet Set Radio (Europe) (Track 1).bin": b"t1",
            "Jet Set Radio (Europe) (Track 2).bin": b"t2",
            "Jet Set Radio (Europe).gdi": b"gdi",
        },
    )

    result = extract_7z(archive, sevenzip=str(_SEVENZIP), dry_run=False, delete_source=True)

    assert not result.success
    assert result.skipped_reason
    assert archive.exists()
    assert not (tmp_path / "Jet Set Radio (Europe).gdi").exists()


@_skip_no_7z
def test_nested_directory_members_extracted(tmp_path: Path) -> None:
    archive = tmp_path / "collection.7z"
    _make_7z(archive, {"sub/inner.rom": b"nested"})

    result = extract_7z(archive, sevenzip=str(_SEVENZIP), dry_run=False, delete_source=False)

    assert result.success
    assert (tmp_path / "sub" / "inner.rom").read_bytes() == b"nested"


@_skip_no_7z
def test_extract_7z_directory_processes_every_archive(tmp_path: Path) -> None:
    a = tmp_path / "a.7z"
    b = tmp_path / "sub" / "b.7z"
    b.parent.mkdir()
    _make_7z(a, {"a.rom": b"a"})
    _make_7z(b, {"b.rom": b"b"})

    assert set(find_7z_files(tmp_path)) == {a, b}

    summary = extract_7z_directory(
        tmp_path, sevenzip=str(_SEVENZIP), dry_run=False, delete_source=True
    )

    assert summary.extracted == 2
    assert not a.exists()
    assert not b.exists()
    assert (tmp_path / "a.rom").read_bytes() == b"a"
    assert (b.parent / "b.rom").read_bytes() == b"b"


@_skip_no_7z
def test_list_7z_members_excludes_directories(tmp_path: Path) -> None:
    archive = tmp_path / "collection.7z"
    _make_7z(archive, {"sub/inner.rom": b"nested", "top.rom": b"top"})

    members = list_7z_members(archive, sevenzip=str(_SEVENZIP))

    assert members is not None
    names = {Path(m).as_posix() for m in members}
    assert names == {"sub/inner.rom", "top.rom"}


def test_list_7z_members_returns_none_for_missing_binary(tmp_path: Path) -> None:
    archive = tmp_path / "whatever.7z"
    archive.write_bytes(b"not a real archive")

    assert list_7z_members(archive, sevenzip="nonexistent_7z_binary") is None


def test_extract_7z_reports_error_when_binary_missing(tmp_path: Path) -> None:
    archive = tmp_path / "collection.7z"
    archive.write_bytes(b"not a real archive")

    result = extract_7z(archive, sevenzip="nonexistent_7z_binary", dry_run=False)

    assert not result.success
    assert result.error


@_skip_no_7z
def test_size_mismatch_never_writes_partial_file_and_keeps_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: a truncated/incomplete member (real cause: 7z killed by a
    timeout, disk full, or a CRC error mid-write) must never land at the real
    target path, and the now-not-actually-redundant source must survive --
    the staging + size-verification in extract_7z() is what guarantees this,
    simulated here by making the archive's own listing lie about a member's
    size so the post-extraction check always fails it."""
    from rom_manager.converters import sevenzip_extractor as mod

    archive = tmp_path / "collection.7z"
    _make_7z(archive, {"a.rom": b"a"})

    real_list_entries = mod._list_7z_entries

    def _lying_entries(path: Path, *, sevenzip: str = "7z"):
        entries = real_list_entries(path, sevenzip=sevenzip)
        assert entries is not None
        return [(name, size + 999, is_dir) for name, size, is_dir in entries]

    monkeypatch.setattr(mod, "_list_7z_entries", _lying_entries)

    result = extract_7z(archive, sevenzip=str(_SEVENZIP), dry_run=False, delete_source=True)

    assert not result.success
    assert not (tmp_path / "a.rom").exists()  # no partial write at the real target
    assert archive.exists()  # source not deleted -- verification failed


@_skip_no_7z
def test_non_ascii_member_names_extract_correctly(tmp_path: Path) -> None:
    """Regression: without -sccUTF-8, 7-Zip on Windows pipes non-ASCII names
    in the console/OEM codepage, they decode as U+FFFD here, and the
    extraction can never find the file it just wrote at that mismatched
    name -- it gets reported as a missing member on every retry."""
    archive = tmp_path / "collection.7z"
    _make_7z(archive, {"Pokémon Amarillo.gb": b"data"})

    result = extract_7z(archive, sevenzip=str(_SEVENZIP), dry_run=False, delete_source=True)

    assert result.success
    assert (tmp_path / "Pokémon Amarillo.gb").read_bytes() == b"data"
    assert not archive.exists()
