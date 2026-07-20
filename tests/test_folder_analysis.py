"""Tests for FORMATOS-UX-2: /api/folder-analysis.

The panel "Análisis de carpeta" used to be a pure stub that always rendered
"Funcionalidad pendiente" regardless of the folder — this covers the real
endpoint, built by reusing already-tested building blocks (find_cue_files +
validate_cue for PSX sets, scan_n64_roms for N64 conversion candidates).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.esde.conversions import register_conversions
from rom_manager.web.jobs.manager import JobManager
from rom_manager.web.router import Router

_MAGIC_V64 = b"\x37\x80\x40\x12"


class _FakeCtx:
    def __init__(self, post_data: dict) -> None:
        self._post_data = post_data
        self.out: dict | None = None

    def _send_json(self, obj: dict) -> None:
        self.out = obj


@pytest.fixture
def router(tmp_path: Path) -> Router:
    config = load_config(project_root=tmp_path)
    repo = LibraryRepository(tmp_path / "library.db")
    job_manager = JobManager()
    r = Router()
    register_conversions(r, config=config, repository=repo, job_manager=job_manager)
    return r


def _analyze(router: Router, path: Path) -> dict:
    ctx = _FakeCtx({"source_path": str(path)})
    router.dispatch("POST", "/api/folder-analysis", ctx)
    assert ctx.out is not None
    return ctx.out


def test_counts_extensions(router: Router, tmp_path: Path) -> None:
    (tmp_path / "a.gba").write_bytes(b"1")
    (tmp_path / "b.gba").write_bytes(b"1")
    (tmp_path / "c.zip").write_bytes(b"1")
    result = _analyze(router, tmp_path)
    counts = {e["ext"]: e["count"] for e in result["extensions"]}
    assert counts[".gba"] == 2
    assert counts[".zip"] == 1
    assert result["zip_count"] == 1


def test_psx_set_with_missing_bin_is_flagged(router: Router, tmp_path: Path) -> None:
    (tmp_path / "game.cue").write_text('FILE "game.bin" BINARY\n  TRACK 01 MODE2/2352\n')
    result = _analyze(router, tmp_path)
    assert len(result["psx_incomplete"]) == 1
    assert result["psx_incomplete"][0]["cue"] == "game.cue"
    assert "missing: game.bin" in result["psx_incomplete"][0]["errors"]


def test_psx_set_with_bin_present_is_not_flagged(router: Router, tmp_path: Path) -> None:
    (tmp_path / "game.bin").write_bytes(b"data")
    (tmp_path / "game.cue").write_text('FILE "game.bin" BINARY\n  TRACK 01 MODE2/2352\n')
    result = _analyze(router, tmp_path)
    assert result["psx_incomplete"] == []


def test_n64_rom_needing_conversion_is_flagged(router: Router, tmp_path: Path) -> None:
    (tmp_path / "rom.v64").write_bytes(_MAGIC_V64 + b"\xaa\xbb\xcc\xdd")
    result = _analyze(router, tmp_path)
    assert result["n64_pending"] == [{"filename": "rom.v64", "format": "v64"}]


def test_missing_folder_returns_error(router: Router, tmp_path: Path) -> None:
    result = _analyze(router, tmp_path / "does-not-exist")
    assert "error" in result


def test_empty_source_path_returns_error(router: Router) -> None:
    ctx = _FakeCtx({"source_path": ""})
    router.dispatch("POST", "/api/folder-analysis", ctx)
    assert "error" in ctx.out
