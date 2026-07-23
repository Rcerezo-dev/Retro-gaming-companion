"""MEJ-2: undo the most recent apply batch by reversing each rename.

Sets up the library as it looks right after a real apply (file at the new
path, games row and file_operations row already updated by apply_rename),
then checks that undo restores the pre-apply state and leaves a matching
history row behind.
"""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import rom_manager.web.state as _state
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.organize import _do_undo_last_apply


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


def _wait_done() -> dict:
    for _ in range(50):
        status = _state._job_manager.get_job("undo_apply")
        if not status["running"]:
            return status["result"]
        time.sleep(0.05)
    raise AssertionError("undo_apply job never finished")


def test_undo_restores_original_filename_and_path(tmp_path: Path) -> None:
    lib = tmp_path / "lib"
    (lib / "gba").mkdir(parents=True)
    old_path = lib / "gba" / "Game (Unl).gba"
    new_path = lib / "gba" / "Game (USA).gba"
    new_path.write_bytes(b"ROMDATA")  # apply already happened: file is at new_path

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    now = "2026-07-23T10:00:00"
    with repo.connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO games
                (original_filename, source_path, file_type, extension, size_bytes,
                 sha1, md5, crc32, created_at, updated_at)
            VALUES (?, ?, 'rom', '.gba', 7, 'a', 'b', 'c', ?, ?)
            """,
            ("Game (Unl).gba", str(old_path), now, now),
        )
        game_id = cur.lastrowid
        conn.commit()
    # Mirrors what _do_apply's loop does on a successful rename.
    repo.apply_rename(
        game_id=game_id,
        old_source_path=str(old_path),
        new_source_path=str(new_path),
        new_filename=new_path.name,
        timestamp=now,
    )

    _state._job_manager.finish("undo_apply", None)
    ctx = _FakeCtx({})
    _do_undo_last_apply(
        ctx, ctx._post_data, _config(tmp_path), lambda _root: repo, _state._job_manager
    )
    result = _wait_done()

    assert result["undone"] == 1
    assert result["failed"] == 0
    assert old_path.exists()
    assert not new_path.exists()
    assert old_path.read_bytes() == b"ROMDATA"

    with repo.connect() as conn:
        row = conn.execute("SELECT source_path, original_filename FROM games").fetchone()
        history = conn.execute(
            "SELECT source_path, target_path FROM file_operations ORDER BY id"
        ).fetchall()
    assert row["source_path"] == str(old_path)
    assert row["original_filename"] == old_path.name
    # Original apply row + the undo's own reversed row.
    assert len(history) == 2
    assert history[-1]["source_path"] == str(new_path)
    assert history[-1]["target_path"] == str(old_path)


def test_undo_with_nothing_to_undo_reports_message(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _state._job_manager.finish("undo_apply", None)
    ctx = _FakeCtx({})
    _do_undo_last_apply(
        ctx, ctx._post_data, _config(tmp_path), lambda _root: repo, _state._job_manager
    )
    result = _wait_done()
    assert result["undone"] == 0
    assert result["message"] == "No hay ningún apply para deshacer"
