"""GET /api/download-rom (FTP-PICK rediseñado 2026-08-29): descarga un ROM
por HTTP desde el navegador de la Anbernic, reutilizando el servidor ya
existente en vez de un protocolo nuevo. Solo sirve rutas que ya están en la
BD como ROM, y que además resuelvan dentro de library_root/anbernic_root
(path traversal, mismo patrón que REV43-16)."""

from __future__ import annotations

from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.games import register
from rom_manager.web.jobs.manager import JobManager
from rom_manager.web.router import Router


class _FakeCtx:
    def __init__(self, qs: dict | None = None) -> None:
        self._qs = qs or {}
        self.sent_file: tuple[Path, str] | None = None
        self.status: int | None = None
        self.error_message: str | None = None

    def _send_file(self, path: Path, download_name: str) -> None:
        self.sent_file = (path, download_name)
        self.status = 200

    def _send_error(self, code: int, message: str) -> None:
        self.status = code
        self.error_message = message

    def _send_json(self, data: dict) -> None:
        self.status = 200


def _add_game(repo: LibraryRepository, path: Path, platform: str = "NES") -> None:
    now = "2026-01-01T00:00:00"
    with repo.connect() as conn:
        conn.execute(
            """INSERT INTO games
               (source_path, original_filename, sha1, md5, crc32, extension,
                size_bytes, file_type, platform, created_at, updated_at)
               VALUES (?, ?, '', '', '', ?, 0, 'rom', ?, ?, ?)""",
            (str(path), path.name, path.suffix.lower(), platform, now, now),
        )
        conn.commit()


def _make_router(tmp_path: Path, library_root: Path) -> tuple[Router, LibraryRepository]:
    repo = LibraryRepository(tmp_path / "library.db")
    cfg_text = f'[library]\nlibrary_root = "{str(library_root).replace(chr(92), "/")}"\n'
    (tmp_path / "config.toml").write_text(cfg_text, encoding="utf-8")
    config = load_config(project_root=tmp_path)
    router = Router()
    register(
        router,
        config=config,
        repository=repo,
        get_repo_fn=lambda _root: repo,
        job_manager=JobManager(),
    )
    return router, repo


def _get(router: Router, path: str) -> _FakeCtx:
    ctx = _FakeCtx(qs={"path": [path]})
    assert router.dispatch("GET", "/api/download-rom", ctx)
    return ctx


def test_downloads_a_tracked_rom(tmp_path: Path) -> None:
    library = tmp_path / "library"
    (library / "nes").mkdir(parents=True)
    rom = library / "nes" / "Metroid (USA).nes"
    rom.write_bytes(b"\x00" * 64)
    router, repo = _make_router(tmp_path, library)
    _add_game(repo, rom)

    ctx = _get(router, str(rom))
    assert ctx.status == 200
    assert ctx.sent_file == (rom.resolve(), "Metroid (USA).nes")


def test_missing_path_param_rejected(tmp_path: Path) -> None:
    router, _repo = _make_router(tmp_path, tmp_path / "library")
    ctx = _FakeCtx(qs={})
    assert router.dispatch("GET", "/api/download-rom", ctx)
    assert ctx.status == 400


def test_untracked_file_rejected_even_if_it_exists_on_disk(tmp_path: Path) -> None:
    library = tmp_path / "library"
    (library / "nes").mkdir(parents=True)
    rom = library / "nes" / "not-in-db.nes"
    rom.write_bytes(b"\x00")
    router, _repo = _make_router(tmp_path, library)

    ctx = _get(router, str(rom))
    assert ctx.status == 404
    assert ctx.sent_file is None


def test_path_traversal_outside_library_root_rejected(tmp_path: Path) -> None:
    library = tmp_path / "library"
    library.mkdir()
    outside = tmp_path / "outside.nes"
    outside.write_bytes(b"\x00")
    router, repo = _make_router(tmp_path, library)
    # Fila manipulada a mano en la BD con una ruta fuera de library_root —
    # ni siquiera si alguien logra insertarla, se debe servir.
    _add_game(repo, outside)

    ctx = _get(router, str(outside))
    assert ctx.status == 403
    assert ctx.sent_file is None


def test_deleted_file_returns_404(tmp_path: Path) -> None:
    library = tmp_path / "library"
    (library / "nes").mkdir(parents=True)
    rom = library / "nes" / "gone.nes"
    rom.write_bytes(b"\x00")
    router, repo = _make_router(tmp_path, library)
    _add_game(repo, rom)
    rom.unlink()

    ctx = _get(router, str(rom))
    assert ctx.status == 404
    assert ctx.sent_file is None
