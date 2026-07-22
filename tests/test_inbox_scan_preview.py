"""Tests for INBOX-UX-2: destination preview in the inbox scan."""

from __future__ import annotations

from pathlib import Path

from rom_manager.web.inbox_pipeline import _build_inbox_scan, _platform_folder_name


def _make_inbox(tmp_path: Path) -> Path:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    return inbox


def test_scan_without_target_has_no_dest_exists(tmp_path: Path):
    inbox = _make_inbox(tmp_path)
    (inbox / "Game.gba").write_bytes(b"\x00" * 16)

    d = _build_inbox_scan(str(inbox))
    (f,) = d["files"]
    assert f["dest_folder"]  # plataforma detectada → carpeta conocida
    assert f["dest_exists"] is None


def test_scan_with_target_flags_existing_name(tmp_path: Path):
    inbox = _make_inbox(tmp_path)
    (inbox / "Game.gba").write_bytes(b"\x00" * 16)
    target = tmp_path / "library"

    # Primera pasada para conocer la carpeta de plataforma que usaría el paso 6
    d = _build_inbox_scan(str(inbox))
    folder = d["files"][0]["dest_folder"]
    (target / folder).mkdir(parents=True)
    (target / folder / "Game.gba").write_bytes(b"\x01" * 16)

    d = _build_inbox_scan(str(inbox), str(target))
    (f,) = d["files"]
    assert f["dest_exists"] is True

    (target / folder / "Game.gba").unlink()
    d = _build_inbox_scan(str(inbox), str(target))
    assert d["files"][0]["dest_exists"] is False


def test_scan_zip_never_checks_dest(tmp_path: Path):
    """Lo que llega a destino es el contenido del ZIP, no el ZIP — no aparentar."""
    import zipfile

    inbox = _make_inbox(tmp_path)
    with zipfile.ZipFile(inbox / "Game.zip", "w") as z:
        z.writestr("Game.gba", b"\x00" * 16)
    target = tmp_path / "library"
    target.mkdir()

    d = _build_inbox_scan(str(inbox), str(target))
    (f,) = d["files"]
    assert f["needs_extraction"] is True
    assert f["dest_exists"] is None


def test_scan_unknown_file_has_no_dest(tmp_path: Path):
    inbox = _make_inbox(tmp_path)
    (inbox / "notas.txt").write_text("hola", encoding="utf-8")
    target = tmp_path / "library"
    target.mkdir()

    d = _build_inbox_scan(str(inbox), str(target))
    (f,) = d["files"]
    assert f["type"] == "unknown"
    assert f["dest_folder"] is None
    assert f["dest_exists"] is None


def test_scan_missing_target_dir_is_ignored(tmp_path: Path):
    """Un target_root inexistente no rompe el scan — solo omite la preview."""
    inbox = _make_inbox(tmp_path)
    (inbox / "Game.gba").write_bytes(b"\x00" * 16)

    d = _build_inbox_scan(str(inbox), str(tmp_path / "no-existe"))
    assert d["files"][0]["dest_exists"] is None


def test_platform_folder_name_unknown_platform():
    assert _platform_folder_name("") == "unknown"
    assert _platform_folder_name("Plataforma Inventada") == "unknown"
