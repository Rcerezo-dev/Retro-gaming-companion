"""GET/POST /api/retroarch-override (CFG-PORGAME-7): raw .opt read/write endpoint."""

from __future__ import annotations

from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.collection import register
from rom_manager.web.router import Router


class _FakeCtx:
    def __init__(self, qs: dict | None = None, post_data: dict | None = None) -> None:
        self._qs = qs or {}
        self._post_data = post_data or {}
        self.sent: dict | None = None
        self.status: int | None = None

    def _send_json(self, data: dict) -> None:
        self.sent = data
        self.status = 200

    def _send_error(self, code: int, message: str) -> None:
        self.sent = {"error": message}
        self.status = code


def _make_router(tmp_path: Path, ra_config_dir: Path | None = None) -> Router:
    repo = LibraryRepository(tmp_path / "library.db")
    config = load_config(project_root=tmp_path)
    if ra_config_dir is not None:
        config.sync.ra_config_dir = str(ra_config_dir)
    router = Router()
    register(
        router,
        config=config,
        repository=repo,
        repo_android=repo,
        get_repo_fn=lambda _root: repo,
    )
    return router


def _get(router: Router, qs: dict) -> _FakeCtx:
    ctx = _FakeCtx(qs=qs)
    assert router.dispatch("GET", "/api/retroarch-override", ctx)
    return ctx


def _post(router: Router, body: dict) -> _FakeCtx:
    ctx = _FakeCtx(post_data=body)
    assert router.dispatch("POST", "/api/retroarch-override", ctx)
    return ctx


def test_pc_read_existing_override(tmp_path: Path) -> None:
    ra_dir = tmp_path / "ra-config"
    (ra_dir / "Snes9x").mkdir(parents=True)
    (ra_dir / "Snes9x" / "Super Mario World.opt").write_text('foo = "bar"\n', encoding="utf-8")
    router = _make_router(tmp_path, ra_dir)

    ctx = _get(router, {"rom": ["Super Mario World"], "core": ["Snes9x"], "side": ["pc"]})

    assert ctx.status == 200
    assert ctx.sent == {
        "rom": "Super Mario World",
        "core": "Snes9x",
        "side": "pc",
        "content": 'foo = "bar"\n',
    }


def test_pc_read_missing_override_404(tmp_path: Path) -> None:
    ra_dir = tmp_path / "ra-config"
    ra_dir.mkdir()
    router = _make_router(tmp_path, ra_dir)

    ctx = _get(router, {"rom": ["Ghost Game"], "core": ["Snes9x"], "side": ["pc"]})

    assert ctx.status == 404


def test_pc_write_then_read_roundtrip(tmp_path: Path) -> None:
    ra_dir = tmp_path / "ra-config"
    ra_dir.mkdir()
    router = _make_router(tmp_path, ra_dir)

    post_ctx = _post(
        router,
        {"rom": "Tetris", "core": "Gambatte", "side": "pc", "content": "x = 1\n"},
    )
    assert post_ctx.sent == {"ok": True}
    assert (ra_dir / "Gambatte" / "Tetris.opt").read_text(encoding="utf-8") == "x = 1\n"

    get_ctx = _get(router, {"rom": ["Tetris"], "core": ["Gambatte"], "side": ["pc"]})
    assert get_ctx.sent["content"] == "x = 1\n"


def test_invalid_side_rejected(tmp_path: Path) -> None:
    router = _make_router(tmp_path)

    ctx = _get(router, {"rom": ["Tetris"], "core": ["Gambatte"], "side": ["cloud"]})

    assert ctx.status == 400


def test_android_side_without_device_rejected(tmp_path: Path) -> None:
    router = _make_router(tmp_path)

    ctx = _get(router, {"rom": ["Tetris"], "core": ["Gambatte"], "side": ["android"]})

    assert ctx.status == 400
    assert "ADB" in ctx.sent["error"]


def test_path_traversal_in_rom_rejected(tmp_path: Path) -> None:
    ra_dir = tmp_path / "ra-config"
    ra_dir.mkdir()
    router = _make_router(tmp_path, ra_dir)

    ctx = _get(router, {"rom": ["../../evil"], "core": ["Snes9x"], "side": ["pc"]})

    assert ctx.status == 400


def test_post_missing_content_rejected(tmp_path: Path) -> None:
    router = _make_router(tmp_path, tmp_path / "ra-config")

    ctx = _post(router, {"rom": "Tetris", "core": "Gambatte", "side": "pc"})

    assert ctx.status == 400
