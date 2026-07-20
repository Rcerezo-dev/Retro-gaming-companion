"""Test de GET /api/collection-stats-v2 (COLECCION-UX): endpoint restaurado.

Se perdió en el refactor 487aa91 (server.py monolítico → handlers) — el panel
Stats de la pestaña Análisis lo llamaba contra un 404 silencioso.
"""

from __future__ import annotations

from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.collection import register
from rom_manager.web.router import Router

TS = "2026-01-01T00:00:00"


class _FakeCtx:
    def __init__(self, qs: dict | None = None) -> None:
        self._qs = qs or {}
        self.sent: dict | None = None

    def _send_json(self, data: dict) -> None:
        self.sent = data


def _make_router(tmp_path: Path, repo: LibraryRepository) -> Router:
    router = Router()
    register(
        router,
        config=load_config(project_root=tmp_path),
        repository=repo,
        repo_android=repo,
        get_repo_fn=lambda _root: repo,
    )
    return router


def _upsert(repo: LibraryRepository, **overrides) -> None:
    defaults = dict(
        original_filename="Game.gba",
        source_path="/roms/gba/Game.gba",
        platform="Game Boy Advance",
        file_type="rom",
        relative_parent="gba",
        region="USA",
        extension=".gba",
        size_bytes=1024,
        mtime=1700000000,
        sha1="aabbccdd" * 5,
        md5="11223344" * 4,
        crc32="deadbeef",
        set_type="single",
        timestamp=TS,
    )
    defaults.update(overrides)
    repo.upsert_game(**defaults)


def _dispatch(router: Router, qs: dict | None = None) -> dict:
    ctx = _FakeCtx(qs or {})
    assert router.dispatch("GET", "/api/collection-stats-v2", ctx)
    assert ctx.sent is not None
    return ctx.sent


def test_stats_v2_aggregates(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "library.db")
    _upsert(repo, source_path="/roms/gba/A.gba", region="USA")
    _upsert(repo, source_path="/roms/gba/B.gba", region="Europe")
    _upsert(
        repo,
        source_path="/roms/snes/C.sfc",
        original_filename="C.sfc",
        platform="Super Nintendo",
        extension=".sfc",
        sha1="cc" * 20,
    )
    # Un save no cuenta como juego
    _upsert(
        repo,
        source_path="/roms/gba/A.srm",
        original_filename="A.srm",
        file_type="save",
        extension=".srm",
        sha1="dd" * 20,
    )

    d = _dispatch(_make_router(tmp_path, repo))

    assert d["total"] == 3
    assert d["favorites"] == 0
    plats = {r["p"]: r["n"] for r in d["by_platform"]}
    assert plats == {"Game Boy Advance": 2, "Super Nintendo": 1}
    regions = {r["r"]: r["n"] for r in d["by_region"]}
    assert regions == {"USA": 2, "Europe": 1}
    assert d["by_status"][0]["s"] == "Sin estado"


def test_stats_v2_root_filter(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "library.db")
    _upsert(repo, source_path="E:/pc/gba/A.gba")
    _upsert(repo, source_path="F:/otro/gba/B.gba", sha1="bb" * 20)

    d = _dispatch(_make_router(tmp_path, repo), {"root": ["E:/pc"]})
    assert d["total"] == 1


def test_stats_v2_empty_library(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "library.db")
    d = _dispatch(_make_router(tmp_path, repo))
    assert d["total"] == 0
    assert d["by_platform"] == []
