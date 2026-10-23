"""REVIEW-QUEUE-PERF-1a: _annotate_conflicts_with_ra looked up each path's md5/platform with its
own SQLite connection (16.958 of them on the real library = 65 % of the review queue's
build time). It must do one batched lookup and give the same RA roles as before."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from rom_manager.database.repository import LibraryRepository
from rom_manager.web.builders import duplicates as dup


def _add_game(repo: LibraryRepository, path: Path, md5: str) -> int:
    repo.upsert_game(
        original_filename=path.name,
        source_path=str(path),
        platform="Game Boy Advance",
        file_type="rom",
        relative_parent="",
        region=None,
        extension=".gba",
        size_bytes=1,
        mtime=1,
        sha1="",
        md5=md5,
        crc32="",
        set_type="single",
        timestamp="2026-01-01T00:00:00",
    )
    with repo.connect() as c:
        return c.execute("SELECT id FROM games WHERE source_path = ?", (str(path),)).fetchone()[0]


def _op(game_id: int, source: Path, target: Path, reason: str):
    return SimpleNamespace(
        game=SimpleNamespace(id=game_id),
        source_path=source,
        target_path=target,
        conflict_reason=reason,
    )


def test_disk_conflict_roles_and_single_connection(tmp_path, monkeypatch) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    src = tmp_path / "a.gba"
    blocker = tmp_path / "b.gba"
    nomd5 = tmp_path / "c.gba"
    for f in (src, blocker, nomd5):
        f.write_bytes(b"x")
    gid = _add_game(repo, src, "A" * 32)
    gid_b = _add_game(repo, blocker, "b" * 32)
    gid_c = _add_game(repo, nomd5, "")
    monkeypatch.setattr(dup, "_load_ra_hash_map", lambda *_a: {"a" * 32: 12, "b" * 32: 3})

    connects = {"n": 0}
    real_connect = repo.connect

    def counting_connect():
        connects["n"] += 1
        return real_connect()

    monkeypatch.setattr(repo, "connect", counting_connect)

    config = SimpleNamespace(project_root=tmp_path)
    rows = dup._annotate_conflicts_with_ra(
        [
            _op(gid, src, blocker, "disk"),  # source 12 vs blocker 3 -> winner
            _op(gid_b, blocker, src, "disk"),  # reversed -> loser
            _op(gid_c, nomd5, src, "disk"),  # no md5 -> no data, but blocker has 12
        ],
        repo,
        config,
    )

    assert connects["n"] == 1
    assert [r["ra_achievements"] for r in rows] == [12, 3, None]
    assert [r["ra_target_achievements"] for r in rows] == [3, 12, 12]
    assert [r["ra_role"] for r in rows] == ["winner", "loser", "loser"]


def test_lookup_failure_degrades_to_no_data(tmp_path, monkeypatch) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    src = tmp_path / "a.gba"
    monkeypatch.setattr(dup, "_load_ra_hash_map", lambda *_a: {"a" * 32: 12})

    def boom():
        raise RuntimeError("db gone")

    monkeypatch.setattr(repo, "connect", boom)

    rows = dup._annotate_conflicts_with_ra(
        [_op(1, src, tmp_path / "b.gba", "disk")], repo, SimpleNamespace(project_root=tmp_path)
    )

    assert rows[0]["ra_achievements"] is None
    assert rows[0]["ra_role"] is None
