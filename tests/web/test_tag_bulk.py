"""Tests for ANBERNIC-PICK-1: POST /api/tag-bulk applies/quita un tag a TODOS
los juegos que cumplen el filtro (no solo una página), reutilizando
get_games_paginated para calcular el conjunto.
"""

from __future__ import annotations

from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers import games as _h_games
from rom_manager.web.router import Router

_TS = "2024-01-01T00:00:00"


class _Ctx:
    def __init__(self, post_data: dict | None = None) -> None:
        self._post_data = post_data or {}
        self.payload: dict | None = None

    def _send_json(self, data: dict) -> None:
        self.payload = data


def _insert_game(repo: LibraryRepository, *, source_path: str, platform: str, sha1: str) -> int:
    repo.upsert_game(
        original_filename=Path(source_path).name,
        source_path=source_path,
        platform=platform,
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".zip",
        size_bytes=1024,
        mtime=0,
        sha1=sha1,
        md5="M" * 32,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp=_TS,
    )
    with repo.connect() as conn:
        row = conn.execute("SELECT id FROM games WHERE source_path = ?", (source_path,)).fetchone()
    return int(row["id"])


def _setup(tmp_path: Path):
    repo = LibraryRepository(tmp_path / "pc.sqlite")
    arcade_ids = [
        _insert_game(
            repo,
            source_path=str(tmp_path / f"arcade/g{i}.zip"),
            platform="Arcade",
            sha1=f"A{i}" * 10,
        )
        for i in range(3)
    ]
    nds_id = _insert_game(
        repo, source_path=str(tmp_path / "nds/g.nds"), platform="Nintendo DS", sha1="B" * 40
    )

    router = Router()
    _h_games.register(
        router,
        config=load_config(tmp_path),
        repository=repo,
        get_repo_fn=lambda _path: repo,
        job_manager=None,
    )
    return router, repo, arcade_ids, nds_id


def test_tag_bulk_add_filters_by_platform(tmp_path: Path) -> None:
    router, repo, arcade_ids, nds_id = _setup(tmp_path)

    ctx = _Ctx({"tag": "anbernic", "action": "add", "platform": "Arcade"})
    router.dispatch("POST", "/api/tag-bulk", ctx)

    assert ctx.payload == {"ok": True, "count": 3, "tag": "anbernic"}
    for gid in arcade_ids:
        assert repo.get_tags(gid) == ["anbernic"]
    assert repo.get_tags(nds_id) == []  # fuera del filtro, no se toca


def test_tag_bulk_remove(tmp_path: Path) -> None:
    router, repo, arcade_ids, nds_id = _setup(tmp_path)
    for gid in arcade_ids + [nds_id]:
        repo.add_tag(gid, "anbernic")

    ctx = _Ctx({"tag": "anbernic", "action": "remove", "platform": "Arcade"})
    router.dispatch("POST", "/api/tag-bulk", ctx)

    assert ctx.payload == {"ok": True, "count": 3, "tag": "anbernic"}
    for gid in arcade_ids:
        assert repo.get_tags(gid) == []
    assert repo.get_tags(nds_id) == ["anbernic"]  # fuera del filtro, se queda marcado


def test_tag_bulk_no_filter_hits_everything(tmp_path: Path) -> None:
    router, repo, arcade_ids, nds_id = _setup(tmp_path)

    ctx = _Ctx({"tag": "anbernic", "action": "add"})
    router.dispatch("POST", "/api/tag-bulk", ctx)

    assert ctx.payload["count"] == 4
    for gid in [*arcade_ids, nds_id]:
        assert repo.get_tags(gid) == ["anbernic"]


def test_tag_bulk_requires_tag(tmp_path: Path) -> None:
    router, repo, _arcade_ids, _nds_id = _setup(tmp_path)

    ctx = _Ctx({"action": "add", "platform": "Arcade"})
    router.dispatch("POST", "/api/tag-bulk", ctx)

    assert ctx.payload == {"error": "tag required"}


def test_add_tag_bulk_and_remove_tag_bulk_repository_methods(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "solo.sqlite")
    ids = [
        _insert_game(
            repo, source_path=str(tmp_path / f"g{i}.zip"), platform="Arcade", sha1=f"C{i}" * 10
        )
        for i in range(2)
    ]

    assert repo.add_tag_bulk(ids, " Anbernic ") == 2  # normaliza a lower/strip como add_tag
    assert repo.get_tags(ids[0]) == ["anbernic"]
    assert repo.get_tags(ids[1]) == ["anbernic"]

    assert repo.add_tag_bulk([], "anbernic") == 0
    assert repo.add_tag_bulk(ids, "") == 0

    assert repo.remove_tag_bulk(ids, "anbernic") == 2
    assert repo.get_tags(ids[0]) == []
