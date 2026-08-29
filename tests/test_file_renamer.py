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


def test_rename_backs_up_current_save_even_with_leftover_bak(tmp_path: Path) -> None:
    """REV43-25: a stale .bak left over from a previous attempt used to make
    the backup step a no-op (os.replace(bak, bak)) — the save about to be
    overwritten was never actually preserved before the overwrite."""
    source = tmp_path / "Old.nes"
    source.write_bytes(b"rom")
    (tmp_path / "Old.srm").write_bytes(b"new save content")
    # New.srm already exists (different content) — triggers the backup path.
    (tmp_path / "New.srm").write_bytes(b"current save about to be overwritten")
    # A leftover .bak from a previous failed/retried attempt.
    (tmp_path / "New.srm.bak").write_bytes(b"stale backup from an earlier attempt")

    outcome = rename_rom_with_saves(source, tmp_path / "New.nes", SAVE_EXTS)

    assert outcome.success is True
    assert (tmp_path / "New.srm").read_bytes() == b"new save content"
    # The stale .bak must survive untouched, and the just-overwritten save
    # must land in a *different* backup file — not silently discarded.
    assert (tmp_path / "New.srm.bak").read_bytes() == b"stale backup from an earlier attempt"
    assert (tmp_path / "New.srm.bak1").read_bytes() == b"current save about to be overwritten"


def test_rename_rollback_restores_original_state_on_save_failure(
    tmp_path: Path, monkeypatch
) -> None:
    """TEST-GAP-1: rename_rom_with_saves' rollback path (companion save move
    fails mid-way) had no direct test — only exercised indirectly through the
    apply handler. Whichever companion fails, everything already renamed must
    end up back at its original name/location, and the ROM/save contents must
    be untouched (this is the "never lose a save" guarantee CLAUDE.md calls
    out as the highest-priority failure mode)."""
    import rom_manager.renamer.file_renamer as fr

    source = tmp_path / "Old.nes"
    source.write_bytes(b"rom data")
    srm = tmp_path / "Old.srm"
    srm.write_bytes(b"save data")
    state = tmp_path / "Old.state"
    state.write_bytes(b"state data")
    target = tmp_path / "New.nes"

    real_move = fr.shutil.move

    def _flaky_move(src, dst):
        if Path(src).name == "Old.state":
            raise OSError("simulated save move failure")
        return real_move(src, dst)

    monkeypatch.setattr(fr.shutil, "move", _flaky_move)

    outcome = rename_rom_with_saves(source, target, SAVE_EXTS)

    assert outcome.success is False
    assert "Old.state" in outcome.error
    assert source.exists()
    assert source.read_bytes() == b"rom data"
    assert not target.exists()
    assert srm.exists()
    assert srm.read_bytes() == b"save data"
    assert not (tmp_path / "New.srm").exists()
    assert state.exists()
    assert state.read_bytes() == b"state data"


def test_move_disc_set_moves_all_bins_intact(tmp_path: Path) -> None:
    """TEST-GAP-1: multi-track disc set (2+ .bin) must move as one atomic unit,
    keeping each BIN's original filename and content — only the CUE is renamed."""
    cue = tmp_path / "Game (Disc 1-2).cue"
    bin1 = tmp_path / "Game (Disc 1).bin"
    bin2 = tmp_path / "Game (Disc 2).bin"
    bin1.write_bytes(b"disc1 data")
    bin2.write_bytes(b"disc2 data")
    cue.write_text(f'FILE "{bin1.name}" BINARY\nFILE "{bin2.name}" BINARY\n')
    target_cue = tmp_path / "Game (USA)" / "Game (USA).cue"

    outcome = move_disc_set_to_subfolder(cue, target_cue, SAVE_EXTS)

    assert outcome.success is True
    assert target_cue.exists()
    assert (target_cue.parent / bin1.name).read_bytes() == b"disc1 data"
    assert (target_cue.parent / bin2.name).read_bytes() == b"disc2 data"
    assert not bin1.exists()
    assert not bin2.exists()
    assert not cue.exists()


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


def test_move_disc_set_rollback_restores_original_state(tmp_path: Path, monkeypatch) -> None:
    """TEST-GAP-1: the companion to test_move_disc_set_rollback_failure_is_reported
    — that one forces the rollback itself to fail; this one checks the common
    case where rollback succeeds: bin2's move fails, and bin1 must end up back
    at its original path with its original content, with nothing left in the
    target directory."""
    import rom_manager.renamer.file_renamer as fr

    cue = tmp_path / "Game.cue"
    bin1 = tmp_path / "Game (Disc 1).bin"
    bin2 = tmp_path / "Game (Disc 2).bin"
    bin1.write_bytes(b"data1")
    bin2.write_bytes(b"data2")
    cue.write_text(f'FILE "{bin1.name}" BINARY\nFILE "{bin2.name}" BINARY\n')
    target_cue = tmp_path / "Game (USA)" / "Game (USA).cue"

    real_rename = fr.os.rename

    def _flaky_rename(src, dst):
        if Path(src).name == bin2.name:
            raise OSError("simulated move failure")
        return real_rename(src, dst)

    monkeypatch.setattr(fr.os, "rename", _flaky_rename)

    outcome = move_disc_set_to_subfolder(cue, target_cue, SAVE_EXTS)

    assert outcome.success is False
    assert "rollback INCOMPLETE" not in outcome.error
    assert bin1.exists()
    assert bin1.read_bytes() == b"data1"
    assert bin2.exists()
    assert bin2.read_bytes() == b"data2"
    assert cue.exists()  # CUE itself is renamed last — never touched here
    assert not target_cue.parent.exists()  # empty target dir cleaned up


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


def test_rename_removes_now_empty_sibling_source_subfolder(tmp_path: Path) -> None:
    """INBOX-ORPHAN-3: a rematch that renames a per-game subfolder (e.g.
    wii/Old Name/Old Name.iso -> wii/New Name/New Name.iso) must not leave the
    old, now-empty subfolder behind."""
    platform = tmp_path / "wii"
    old_dir = platform / "Old Name"
    old_dir.mkdir(parents=True)
    source = old_dir / "Old Name.iso"
    source.write_bytes(b"rom")
    target = platform / "New Name" / "New Name.iso"

    outcome = rename_rom_with_saves(source, target, frozenset({".srm"}))

    assert outcome.success is True
    assert target.exists()
    assert not old_dir.exists(), "empty source subfolder must be removed"
    assert platform.exists()


def test_rename_keeps_source_subfolder_if_not_empty(tmp_path: Path) -> None:
    """A leftover unrelated file in the old subfolder must block cleanup —
    os.rmdir only ever removes a truly empty directory."""
    platform = tmp_path / "wii"
    old_dir = platform / "Old Name"
    old_dir.mkdir(parents=True)
    source = old_dir / "Old Name.iso"
    source.write_bytes(b"rom")
    (old_dir / "manual.txt").write_bytes(b"notes")
    target = platform / "New Name" / "New Name.iso"

    outcome = rename_rom_with_saves(source, target, frozenset({".srm"}))

    assert outcome.success is True
    assert old_dir.exists(), "must not touch a subfolder holding other files"


def test_move_disc_set_removes_now_empty_sibling_source_subfolder(tmp_path: Path) -> None:
    """Same cleanup for the CUE/GDI disc-set path (psx/saturn/dreamcast)."""
    platform = tmp_path / "psx"
    old_dir = platform / "Old Name"
    old_dir.mkdir(parents=True)
    cue = old_dir / "Old Name.cue"
    bin_ = old_dir / "Old Name.bin"
    bin_.write_bytes(b"disc data")
    cue.write_text(f'FILE "{bin_.name}" BINARY\n')
    target_cue = platform / "New Name" / "New Name.cue"

    outcome = move_disc_set_to_subfolder(cue, target_cue, SAVE_EXTS)

    assert outcome.success is True
    assert target_cue.exists()
    assert not old_dir.exists(), "empty source subfolder must be removed"


def test_rename_never_removes_platform_root(tmp_path: Path) -> None:
    """Flat-platform renames (no subfolder) must never touch the platform
    root folder itself, even though it becomes momentarily 'emptier'."""
    platform = tmp_path / "gamecube"
    platform.mkdir()
    source = platform / "old-name.iso"
    source.write_bytes(b"rom")
    target = platform / "New Title (USA).iso"

    outcome = rename_rom_with_saves(source, target, frozenset({".srm"}))

    assert outcome.success is True
    assert platform.exists()
