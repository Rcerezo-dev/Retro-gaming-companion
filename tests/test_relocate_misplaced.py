"""REPAIR-TOOL-8 — reubicar archivos mal ubicados (extensión ≠ plataforma de
su carpeta) a la carpeta que les corresponde, sin renombrar.

Acción sobre lo que detecta ``check_misplaced_extensions_health()``
(LIB-MISPLACED-1): mueve sin tocar el nombre, y ante colisión en destino
decide por contenido (nunca por nombre) -- mismo espíritu que
``_same_content`` ya usa el resto del pipeline del Inbox.
"""

from __future__ import annotations

from pathlib import Path

from rom_manager.web.inbox_pipeline import relocate_misplaced_files


def test_no_misplaced_files_reports_nothing(tmp_path: Path) -> None:
    gba_dir = tmp_path / "gba"
    gba_dir.mkdir()
    (gba_dir / "Pokemon (USA).gba").touch()

    summary = relocate_misplaced_files(tmp_path)

    assert summary.moved == 0
    assert summary.duplicates_discarded == 0
    assert summary.conflicts == 0
    assert summary.actions == []


def test_dry_run_reports_but_does_not_move(tmp_path: Path) -> None:
    gba_dir = tmp_path / "gba"
    gba_dir.mkdir()
    misplaced = gba_dir / "Contra (USA).nes"
    misplaced.write_bytes(b"nes rom data")

    summary = relocate_misplaced_files(tmp_path, dry_run=True)

    assert summary.moved == 1
    assert misplaced.exists()  # nothing actually moved
    assert not (tmp_path / "nes").exists()
    action = summary.actions[0]
    assert action.source == str(misplaced)
    assert action.outcome == "moved"


def test_apply_moves_file_without_renaming(tmp_path: Path) -> None:
    gba_dir = tmp_path / "gba"
    gba_dir.mkdir()
    misplaced = gba_dir / "Contra (USA).nes"
    misplaced.write_bytes(b"nes rom data")

    summary = relocate_misplaced_files(tmp_path, dry_run=False)

    assert summary.moved == 1
    assert not misplaced.exists()
    dest = tmp_path / "nes" / "Contra (USA).nes"
    assert dest.exists()
    assert dest.read_bytes() == b"nes rom data"


def test_apply_creates_target_platform_folder_if_missing(tmp_path: Path) -> None:
    gba_dir = tmp_path / "gba"
    gba_dir.mkdir()
    (gba_dir / "Sonic (USA).sfc").write_bytes(b"snes rom")

    relocate_misplaced_files(tmp_path, dry_run=False)

    assert (tmp_path / "snes" / "Sonic (USA).sfc").exists()


def test_exact_duplicate_at_target_is_discarded_to_trash(tmp_path: Path) -> None:
    gba_dir = tmp_path / "gba"
    gba_dir.mkdir()
    misplaced = gba_dir / "Contra (USA).nes"
    misplaced.write_bytes(b"same bytes")

    nes_dir = tmp_path / "nes"
    nes_dir.mkdir()
    (nes_dir / "Contra (USA).nes").write_bytes(b"same bytes")

    summary = relocate_misplaced_files(tmp_path, dry_run=False)

    assert summary.duplicates_discarded == 1
    assert summary.moved == 0
    assert not misplaced.exists()
    assert (gba_dir / "_descartados" / "Contra (USA).nes").exists()
    # The already-correct copy in nes/ is never touched.
    assert (nes_dir / "Contra (USA).nes").read_bytes() == b"same bytes"


def test_different_content_at_target_is_left_untouched(tmp_path: Path) -> None:
    gba_dir = tmp_path / "gba"
    gba_dir.mkdir()
    misplaced = gba_dir / "Contra (USA).nes"
    misplaced.write_bytes(b"misplaced version")

    nes_dir = tmp_path / "nes"
    nes_dir.mkdir()
    existing = nes_dir / "Contra (USA).nes"
    existing.write_bytes(b"different existing version")

    summary = relocate_misplaced_files(tmp_path, dry_run=False)

    assert summary.conflicts == 1
    assert summary.moved == 0
    assert summary.duplicates_discarded == 0
    # Neither file was touched -- ante duda, no sobrescribir.
    assert misplaced.read_bytes() == b"misplaced version"
    assert existing.read_bytes() == b"different existing version"


def test_dry_run_never_touches_disk_on_collision(tmp_path: Path) -> None:
    gba_dir = tmp_path / "gba"
    gba_dir.mkdir()
    misplaced = gba_dir / "Contra (USA).nes"
    misplaced.write_bytes(b"same bytes")

    nes_dir = tmp_path / "nes"
    nes_dir.mkdir()
    (nes_dir / "Contra (USA).nes").write_bytes(b"same bytes")

    summary = relocate_misplaced_files(tmp_path, dry_run=True)

    assert summary.duplicates_discarded == 1
    assert misplaced.exists()
    assert not (gba_dir / "_descartados").exists()
