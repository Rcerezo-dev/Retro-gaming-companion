"""ZIP-ROUTE-FIX-1: rename_rom_with_saves must create the target directory.

TABS-FIX-7: companions matched by stem prefix (savestates .stateN/.state.auto)
and searched also in central save/state directories, renamed in place there.
"""

from __future__ import annotations

from pathlib import Path

from rom_manager.renamer.file_renamer import (
    central_save_dirs,
    move_disc_set_to_subfolder,
    rename_rom_with_saves,
)

SAVE_EXTS = frozenset({".srm", ".sav", ".state", ".state1", ".state2"})


def test_rename_creates_missing_target_dir(tmp_path: Path) -> None:
    source = tmp_path / "Game (USA).nes"
    source.write_bytes(b"rom data")
    target = tmp_path / "Virtual Console" / "Game (USA).nes"

    outcome = rename_rom_with_saves(source, target, frozenset({".srm"}))

    assert outcome.success is True
    assert target.exists()
    assert not source.exists()


def test_rename_same_dir_still_works(tmp_path: Path) -> None:
    source = tmp_path / "Old Name.nes"
    source.write_bytes(b"rom data")
    target = tmp_path / "New Name.nes"

    outcome = rename_rom_with_saves(source, target, frozenset({".srm"}))

    assert outcome.success is True
    assert target.exists()


def test_rename_covers_savestate_slots_and_auto(tmp_path: Path) -> None:
    """.state3 (slot fuera de la lista) y .state.auto deben renombrarse."""
    source = tmp_path / "Old.snes"
    source.write_bytes(b"rom")
    for name in ("Old.srm", "Old.state3", "Old.state.auto"):
        (tmp_path / name).write_bytes(b"s")

    outcome = rename_rom_with_saves(source, tmp_path / "New.snes", SAVE_EXTS)

    assert outcome.success is True
    assert outcome.saves_renamed == 3
    assert (tmp_path / "New.srm").exists()
    assert (tmp_path / "New.state3").exists()
    assert (tmp_path / "New.state.auto").exists()


def test_rename_does_not_touch_other_games_with_same_prefix(tmp_path: Path) -> None:
    """ "Game 2.srm" no es compañero de "Game" (el prefijo exige punto)."""
    source = tmp_path / "Game.nes"
    source.write_bytes(b"rom")
    other = tmp_path / "Game 2.srm"
    other.write_bytes(b"s")

    outcome = rename_rom_with_saves(source, tmp_path / "Game (USA).nes", SAVE_EXTS)

    assert outcome.success is True
    assert outcome.saves_renamed == 0
    assert other.exists()


def test_rename_central_dir_save_renamed_in_place(tmp_path: Path) -> None:
    """Un save en la carpeta central (RetroArch saves/) se renombra sin moverse."""
    rom_dir = tmp_path / "roms"
    rom_dir.mkdir()
    central = tmp_path / "saves"
    central.mkdir()
    source = rom_dir / "Old.gba"
    source.write_bytes(b"rom")
    (central / "Old.srm").write_bytes(b"s")
    (central / "Old.state.auto").write_bytes(b"s")

    outcome = rename_rom_with_saves(source, rom_dir / "New.gba", SAVE_EXTS, extra_dirs=[central])

    assert outcome.success is True
    assert outcome.saves_renamed == 2
    assert (central / "New.srm").exists()
    assert (central / "New.state.auto").exists()
    assert not (central / "Old.srm").exists()


def test_rename_same_dir_save_follows_rom_to_target_dir(tmp_path: Path) -> None:
    """Si el ROM se mueve de carpeta, su save contiguo se va con él."""
    source = tmp_path / "Old.nes"
    source.write_bytes(b"rom")
    (tmp_path / "Old.srm").write_bytes(b"s")
    target = tmp_path / "sub" / "New.nes"

    outcome = rename_rom_with_saves(source, target, SAVE_EXTS)

    assert outcome.success is True
    assert (tmp_path / "sub" / "New.srm").exists()
    assert not (tmp_path / "Old.srm").exists()


def test_move_disc_set_renames_central_save_in_place(tmp_path: Path) -> None:
    cue = tmp_path / "Game.cue"
    bin_ = tmp_path / "Game.bin"
    bin_.write_bytes(b"data")
    cue.write_text(f'FILE "{bin_.name}" BINARY\n')
    central = tmp_path / "memcards"
    central.mkdir()
    (central / "Game.srm").write_bytes(b"s")
    target_cue = tmp_path / "Game (USA)" / "Game (USA).cue"

    outcome = move_disc_set_to_subfolder(cue, target_cue, SAVE_EXTS, extra_dirs=[central])

    assert outcome.success is True
    assert target_cue.exists()
    assert (target_cue.parent / "Game.bin").exists()  # los .bin conservan su nombre
    assert (central / "Game (USA).srm").exists()  # renombrado en su sitio


def test_move_disc_set_rollback_failure_is_reported(tmp_path: Path, monkeypatch) -> None:
    """REV43-24: if undoing a partial move fails, the caller must be told which
    file couldn't be restored — the old _rollback() swallowed OSError silently
    and the returned error never mentioned an incomplete rollback."""
    import rom_manager.renamer.file_renamer as fr

    cue = tmp_path / "Game.cue"
    bin1 = tmp_path / "Game (Disc 1).bin"
    bin2 = tmp_path / "Game (Disc 2).bin"
    bin1.write_bytes(b"data1")
    bin2.write_bytes(b"data2")
    cue.write_text(f'FILE "{bin1.name}" BINARY\nFILE "{bin2.name}" BINARY\n')
    target_cue = tmp_path / "Game (USA)" / "Game (USA).cue"

    real_rename = fr.os.rename
    call_count = {"n": 0}

    def _flaky_rename(src, dst):
        call_count["n"] += 1
        if call_count["n"] == 2:  # bin2's move fails, triggering rollback of bin1
            raise OSError("simulated move failure")
        return real_rename(src, dst)

    monkeypatch.setattr(fr.os, "rename", _flaky_rename)
    monkeypatch.setattr(
        fr.shutil,
        "move",
        lambda *_a, **_k: (_ for _ in ()).throw(OSError("simulated rollback failure")),
    )

    outcome = move_disc_set_to_subfolder(cue, target_cue, SAVE_EXTS)

    assert outcome.success is False
    assert "rollback INCOMPLETE" in outcome.error
    assert bin1.name in outcome.error


def test_central_save_dirs_only_returns_existing(tmp_path: Path) -> None:
    class _Src:
        def __init__(self, d: str) -> None:
            self.local_dir = d

    class _Sync:
        def __init__(self, dirs: list[str]) -> None:
            self.sync_sources = [_Src(d) for d in dirs]

    class _Cfg:
        retroarch_path = str(tmp_path / "RetroArch" / "retroarch.exe")

        def __init__(self, dirs: list[str]) -> None:
            self.sync = _Sync(dirs)

    (tmp_path / "RetroArch" / "saves").mkdir(parents=True)
    existing = tmp_path / "central_saves"
    existing.mkdir()

    dirs = central_save_dirs(_Cfg([str(existing), str(tmp_path / "missing")]))

    assert tmp_path / "RetroArch" / "saves" in dirs
    assert existing in dirs
    assert all(d.is_dir() for d in dirs)
