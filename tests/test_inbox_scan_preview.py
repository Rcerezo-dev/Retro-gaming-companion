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


def test_platform_folder_name_warns_on_legacy_folder_with_real_content(tmp_path, caplog):
    """DUALFOLDER-12: carpeta Title Case legada con ROMs reales -> aviso, sin bloquear."""
    legacy = tmp_path / "Game Boy"
    legacy.mkdir()
    (legacy / "Super Mario Land.gb").write_bytes(b"\x00")

    with caplog.at_level("WARNING"):
        slug = _platform_folder_name("Game Boy", tmp_path)

    assert slug == "gb"
    assert any("DUALFOLDER-12" in r.message for r in caplog.records)


def test_platform_folder_name_no_warn_when_legacy_only_has_media(tmp_path, caplog):
    """Una carpeta legada con solo media/ (sin ROMs) no cuenta como contenido real."""
    legacy = tmp_path / "Game Boy"
    (legacy / "media").mkdir(parents=True)
    (legacy / "media" / "cover.jpg").write_bytes(b"\x00")

    with caplog.at_level("WARNING"):
        slug = _platform_folder_name("Game Boy", tmp_path)

    assert slug == "gb"
    assert not any("DUALFOLDER-12" in r.message for r in caplog.records)


def test_platform_folder_name_no_warn_when_no_legacy_folder(tmp_path, caplog):
    """Sin carpeta Title Case legada, no hay nada que avisar."""
    with caplog.at_level("WARNING"):
        slug = _platform_folder_name("Game Boy", tmp_path)

    assert slug == "gb"
    assert not any("DUALFOLDER-12" in r.message for r in caplog.records)
