"""Test de GET /api/library-extras (INICIO-UX-5): conteos agregados de
archivos no-gaming (BIOS, infraestructura MAME, basura borrable) para la
sección "Además de juegos…" de la pestaña Inicio.
"""

from __future__ import annotations

from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.esde.maintenance import register_maintenance
from rom_manager.web.jobs.manager import JobManager
from rom_manager.web.router import Router


class _FakeCtx:
    def __init__(self, qs: dict | None = None) -> None:
        self._qs = qs or {}
        self.sent: dict | None = None

    def _send_json(self, data: dict) -> None:
        self.sent = data


def _dispatch(tmp_path: Path, qs: dict) -> dict:
    config = load_config(project_root=tmp_path)
    router = Router()
    register_maintenance(
        router,
        config=config,
        repository=LibraryRepository(tmp_path / "library.db"),
        job_manager=JobManager(),
    )
    ctx = _FakeCtx(qs)
    assert router.dispatch("GET", "/api/library-extras", ctx)
    assert ctx.sent is not None
    return ctx.sent


def test_library_extras_counts(tmp_path: Path) -> None:
    lib = tmp_path / "lib"
    (lib / "bios").mkdir(parents=True)
    (lib / "bios" / "scph1001.bin").write_bytes(b"x")
    (lib / "bios" / "gba_bios.bin").write_bytes(b"x")
    (lib / "doc.pdf").write_bytes(b"x" * 100)  # safe_delete
    (lib / "juego.gba").write_bytes(b"x")  # gaming → no cuenta

    result = _dispatch(tmp_path, {"root": [str(lib)]})
    assert result["bios"] == 2
    assert result["mame_infra"] == 0
    assert result["junk_files"] == 1
    assert result["junk_bytes"] == 100


def test_library_extras_missing_root(tmp_path: Path) -> None:
    result = _dispatch(tmp_path, {"root": [str(tmp_path / "no-existe")]})
    assert result == {"bios": 0, "mame_infra": 0, "junk_files": 0, "junk_bytes": 0}
