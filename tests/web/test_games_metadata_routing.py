"""Tests for DEVSEL-FIX-2: favorites/tags/notes/metadata must route to the device's DB.

Before the fix the three handlers wrote to the fixed PC repository, so in
console mode a game_id from the Android DB toggled/tagged the wrong PC game.
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


def _insert_game(repo: LibraryRepository, *, source_path: str, sha1: str) -> int:
    repo.upsert_game(
        original_filename=Path(source_path).name,
        source_path=source_path,
        platform="Game Boy",
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gb",
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
    """PC and Android repos, one game on each (same id=1), router wired like server.py."""
    repo_pc = LibraryRepository(tmp_path / "pc.sqlite")
    repo_ab = LibraryRepository(tmp_path / "ab.sqlite")
    ab_root = tmp_path / "android"
    pc_id = _insert_game(repo_pc, source_path=str(tmp_path / "pc" / "g.gb"), sha1="A" * 40)
    ab_id = _insert_game(repo_ab, source_path=str(ab_root / "g.gb"), sha1="B" * 40)
    assert pc_id == ab_id  # mismo id en ambas BDs: el enrutado es lo único que distingue

    def get_repo_fn(path_str: str) -> LibraryRepository:
        if path_str and str(ab_root).lower() in path_str.lower():
            return repo_ab
        return repo_pc

    router = Router()
    _h_games.register(
        router,
        config=load_config(tmp_path),
        repository=repo_pc,
        get_repo_fn=get_repo_fn,
        job_manager=None,
    )
    return router, repo_pc, repo_ab, str(ab_root / "g.gb"), ab_id


def _favorite(repo: LibraryRepository, gid: int) -> int:
    with repo.connect() as conn:
        return conn.execute("SELECT is_favorite FROM games WHERE id = ?", (gid,)).fetchone()[
            "is_favorite"
        ]


def test_toggle_favorite_routes_to_android(tmp_path: Path) -> None:
    router, repo_pc, repo_ab, ab_path, gid = _setup(tmp_path)

    ctx = _Ctx({"game_id": gid, "source_path": ab_path})
    router.dispatch("POST", "/api/toggle-favorite", ctx)

    assert ctx.payload == {"ok": True, "is_favorite": True}
    assert _favorite(repo_ab, gid) == 1
    assert _favorite(repo_pc, gid) == 0  # el juego del PC con el mismo id no se toca


def test_tag_routes_to_android(tmp_path: Path) -> None:
    router, repo_pc, repo_ab, ab_path, gid = _setup(tmp_path)

    ctx = _Ctx({"game_id": gid, "tag": "rpg", "source_path": ab_path})
    router.dispatch("POST", "/api/tag", ctx)

    assert ctx.payload == {"ok": True, "tags": ["rpg"]}
    assert repo_ab.get_tags(gid) == ["rpg"]
    assert repo_pc.get_tags(gid) == []


def test_set_metadata_routes_to_android(tmp_path: Path) -> None:
    router, repo_pc, repo_ab, ab_path, gid = _setup(tmp_path)

    ctx = _Ctx({"game_id": gid, "notes": "hola", "year": "1999", "source_path": ab_path})
    router.dispatch("POST", "/api/set-metadata", ctx)

    assert ctx.payload == {"ok": True}
    with repo_ab.connect() as conn:
        assert (
            conn.execute("SELECT notes FROM games WHERE id = ?", (gid,)).fetchone()["notes"]
            == "hola"
        )
    with repo_pc.connect() as conn:
        assert (
            conn.execute("SELECT notes FROM games WHERE id = ?", (gid,)).fetchone()["notes"] is None
        )


def test_without_source_path_defaults_to_pc(tmp_path: Path) -> None:
    router, repo_pc, repo_ab, _, gid = _setup(tmp_path)

    ctx = _Ctx({"game_id": gid})
    router.dispatch("POST", "/api/toggle-favorite", ctx)

    assert _favorite(repo_pc, gid) == 1
    assert _favorite(repo_ab, gid) == 0
