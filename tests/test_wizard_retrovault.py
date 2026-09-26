from pathlib import Path

from rom_manager.wizard import _RETROVAULT_SIBLINGS, _ensure_retrovault_structure


def test_ensure_retrovault_structure_creates_roms_and_siblings(tmp_path: Path) -> None:
    library_root = tmp_path / "RetroVault" / "ROMS"

    _ensure_retrovault_structure(library_root)

    assert library_root.is_dir()
    for sibling in _RETROVAULT_SIBLINGS:
        assert (tmp_path / "RetroVault" / sibling).is_dir()


def test_ensure_retrovault_structure_is_idempotent(tmp_path: Path) -> None:
    library_root = tmp_path / "RetroVault" / "ROMS"

    _ensure_retrovault_structure(library_root)
    _ensure_retrovault_structure(library_root)  # no debe fallar si ya existen

    assert library_root.is_dir()
