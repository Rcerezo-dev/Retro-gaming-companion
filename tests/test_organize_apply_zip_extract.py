"""INBOX-FIX-6: a console .zip placed in its platform folder by apply must be
extracted right away (PCSX2/AetherSX2 etc. can't load an .iso inside a .zip),
while an arcade/MAME .zip must stay zipped (the ZIP is the ROM).
"""

from __future__ import annotations

import time
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import rom_manager.web.state as _state
from rom_manager.database.repository import MatchedGame
from rom_manager.web.handlers.organize import _do_apply


class _FakeCtx:
    def __init__(self, post_data: dict) -> None:
        self._post_data = post_data
        self.out = None

    def _send_json(self, obj) -> None:
        self.out = obj


def _config(tmp_path: Path):
    return SimpleNamespace(
        save_extensions=(".sav",),
        backup=SimpleNamespace(saves_enabled=False, saves_keep_n=5),
        data_dir=tmp_path / "data",
        retroarch_path="",
        sync=SimpleNamespace(sync_sources=[]),
    )


def _make_zip_game(source_path: Path, *, platform: str, canonical_title: str) -> MatchedGame:
    return MatchedGame(
        id=1,
        original_filename=source_path.name,
        source_path=str(source_path),
        platform=platform,
        extension=".zip",
        canonical_title=canonical_title,
        match_confidence="high",
    )


def _wait_done() -> dict:
    for _ in range(50):
        status = _state._job_manager.get_job("apply")
        if not status["running"]:
            return status["result"]
        time.sleep(0.05)
    raise AssertionError("apply job never finished")


def test_apply_extracts_console_zip(tmp_path: Path) -> None:
    lib = tmp_path / "lib"
    (lib / "ps2").mkdir(parents=True)
    zip_path = lib / "ps2" / "wrongname.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("Game (USA).iso", b"ISODATA")

    game = _make_zip_game(zip_path, platform="PlayStation 2", canonical_title="Game (USA)")
    repo = MagicMock()
    repo.get_matched_games.return_value = [game]

    _state._job_manager.finish("apply", None)
    ctx = _FakeCtx({})
    _do_apply(ctx, ctx._post_data, _config(tmp_path), lambda _root: repo, _state._job_manager)
    result = _wait_done()

    assert result["renamed"] == 1
    assert result["zips_extracted"] == 1
    target_zip = lib / "ps2" / "Game (USA).zip"
    assert not target_zip.exists()  # extracted then deleted
    assert (lib / "ps2" / "Game (USA).iso").read_bytes() == b"ISODATA"


def test_apply_leaves_arcade_zip_zipped(tmp_path: Path) -> None:
    lib = tmp_path / "lib"
    (lib / "arcade").mkdir(parents=True)
    zip_path = lib / "arcade" / "wrongname.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("rom.bin", b"ROMDATA")

    game = _make_zip_game(zip_path, platform="Arcade", canonical_title="sf2")
    repo = MagicMock()
    repo.get_matched_games.return_value = [game]

    _state._job_manager.finish("apply", None)
    ctx = _FakeCtx({})
    _do_apply(ctx, ctx._post_data, _config(tmp_path), lambda _root: repo, _state._job_manager)
    result = _wait_done()

    assert result["renamed"] == 1
    assert result["zips_extracted"] == 0
    target_zip = lib / "arcade" / "sf2.zip"
    assert target_zip.exists()
    assert not (lib / "arcade" / "rom.bin").exists()
