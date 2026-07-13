"""Tests for DEVSEL-FIX-1: duplicate actions must route to the device's DB.

Before the fix every action used the PC repository, so in console mode the UI
showed Android duplicates but the backend deleted the PC ones (data loss).
"""

from __future__ import annotations

from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers import duplicates as _h_duplicates
from rom_manager.web.router import Router

_TS = "2024-01-01T00:00:00"
_SHA1_A = "A" * 40
_SHA1_B = "B" * 40


class _Ctx:
    def __init__(self, post_data: dict | None = None) -> None:
        self._post_data = post_data or {}
        self.payload: dict | None = None
        self.error: tuple | None = None

    def _send_json(self, data: dict) -> None:
        self.payload = data

    def _send_error(self, code: int, msg: str) -> None:
        self.error = (code, msg)


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


def _count_games(repo: LibraryRepository) -> int:
    with repo.connect() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM games").fetchone()["n"]


def _setup(tmp_path: Path):
    """Two repos (PC + Android), a duplicate pair on each, and the wired router."""
    pc_root = tmp_path / "pc"
    ab_root = tmp_path / "android"
    pc_root.mkdir()
    ab_root.mkdir()
    repo_pc = LibraryRepository(tmp_path / "pc.sqlite")
    repo_ab = LibraryRepository(tmp_path / "ab.sqlite")

    files = {}
    for root, repo, tag in ((pc_root, repo_pc, "pc"), (ab_root, repo_ab, "ab")):
        for n in ("a1.gb", "a2.gb"):
            f = root / n
            f.write_bytes(b"data")
            files[f"{tag}-{n}"] = (f, _insert_game(repo, source_path=str(f), sha1=_SHA1_A))

    def get_repo_fn(path_str: str) -> LibraryRepository:
        # Same contract as server._get_repo: under pc_root (or empty) → PC
        if path_str and str(ab_root).lower() in path_str.lower():
            return repo_ab
        return repo_pc

    router = Router()
    _h_duplicates.register(
        router,
        config=load_config(tmp_path),
        repository=repo_pc,
        repo_android=repo_ab,
        get_repo_fn=get_repo_fn,
        job_manager=None,  # only used by /api/ra-check/discard-no-support
    )
    return router, repo_pc, repo_ab, files, ab_root


def test_delete_routes_to_android_repo(tmp_path: Path) -> None:
    router, repo_pc, repo_ab, files, _ = _setup(tmp_path)
    ab_file, ab_id = files["ab-a2.gb"]

    ctx = _Ctx({"game_id": ab_id, "source_path": str(ab_file)})
    router.dispatch("POST", "/api/duplicates/delete", ctx)

    assert ctx.payload == {"deleted": str(ab_file)}
    assert not ab_file.exists()
    assert _count_games(repo_ab) == 1  # solo se borró el registro Android
    assert _count_games(repo_pc) == 2  # la BD del PC queda intacta


def test_delete_all_with_android_root_leaves_pc_untouched(tmp_path: Path) -> None:
    router, repo_pc, repo_ab, files, ab_root = _setup(tmp_path)

    ctx = _Ctx({"source_root": str(ab_root)})
    router.dispatch("POST", "/api/duplicates/delete-all", ctx)

    assert ctx.payload["deleted"] == 1
    assert files["pc-a2.gb"][0].exists()  # el duplicado del PC sigue en disco
    assert not files["ab-a2.gb"][0].exists()
    assert _count_games(repo_pc) == 2


def test_delete_all_without_root_purges_both_repos(tmp_path: Path) -> None:
    router, repo_pc, repo_ab, files, _ = _setup(tmp_path)

    ctx = _Ctx({})
    router.dispatch("POST", "/api/duplicates/delete-all", ctx)

    assert ctx.payload["deleted"] == 2
    assert _count_games(repo_pc) == 1
    assert _count_games(repo_ab) == 1


def test_exclude_routes_by_source_root(tmp_path: Path) -> None:
    router, repo_pc, repo_ab, _, ab_root = _setup(tmp_path)

    ctx = _Ctx({"sha1": _SHA1_A, "source_root": str(ab_root)})
    router.dispatch("POST", "/api/duplicates/exclude", ctx)

    assert ctx.payload == {"ok": True}
    assert repo_ab.get_duplicate_groups() == []
    assert len(repo_pc.get_duplicate_groups()) == 1  # el PC sigue mostrando su grupo


def test_exclude_without_root_excludes_in_both(tmp_path: Path) -> None:
    router, repo_pc, repo_ab, _, _ = _setup(tmp_path)

    ctx = _Ctx({"sha1": _SHA1_A})
    router.dispatch("POST", "/api/duplicates/exclude", ctx)

    assert ctx.payload == {"ok": True}
    assert repo_pc.get_duplicate_groups() == []
    assert repo_ab.get_duplicate_groups() == []


def test_exclude_without_sha1_is_400(tmp_path: Path) -> None:
    router, *_ = _setup(tmp_path)
    ctx = _Ctx({})
    router.dispatch("POST", "/api/duplicates/exclude", ctx)
    assert ctx.error == (400, "sha1 required")
