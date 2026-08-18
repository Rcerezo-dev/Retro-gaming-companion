"""POST /api/retroarch-override/copy (CFG-PORGAME-8): single-game copy PC<->Android."""

from __future__ import annotations

from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.sync.adb_transport import AdbDevice, AdbTransport
from rom_manager.web.handlers.collection import register
from rom_manager.web.router import Router


class _FakeCtx:
    def __init__(self, post_data: dict) -> None:
        self._post_data = post_data
        self.sent: dict | None = None
        self.status: int | None = None

    def _send_json(self, data: dict) -> None:
        self.sent = data
        self.status = 200

    def _send_error(self, code: int, message: str) -> None:
        self.sent = {"error": message}
        self.status = code


def _make_router(tmp_path: Path, ra_config_dir: Path) -> Router:
    repo = LibraryRepository(tmp_path / "library.db")
    config = load_config(project_root=tmp_path)
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


def _copy(router: Router, body: dict) -> _FakeCtx:
    ctx = _FakeCtx(body)
    assert router.dispatch("POST", "/api/retroarch-override/copy", ctx)
    return ctx


def _fake_one_ready_device(monkeypatch, android_store: dict[str, str]) -> None:
    from rom_manager.sync import adb_transport as adb_transport_module

    monkeypatch.setattr(
        adb_transport_module,
        "list_devices",
        lambda adb_path, **kw: [AdbDevice(serial="ABC123", state="device")],
    )

    def fake_pull(self, android_src, local_dst, *, dry_run=False, verify=False):
        if android_src not in android_store:
            raise OSError(f"adb pull falló: no such file: {android_src}")
        local_dst.write_text(android_store[android_src], encoding="utf-8")
        return len(android_store[android_src])

    def fake_push(self, local_src, android_dst, *, dry_run=False, verify=False):
        android_store[android_dst] = local_src.read_text(encoding="utf-8")
        return local_src.stat().st_size

    monkeypatch.setattr(AdbTransport, "pull", fake_pull)
    monkeypatch.setattr(AdbTransport, "push", fake_push)


def test_invalid_direction_rejected(tmp_path: Path) -> None:
    router = _make_router(tmp_path, tmp_path / "ra-config")

    ctx = _copy(router, {"rom": "Tetris", "core": "Gambatte", "direction": "sideways"})

    assert ctx.status == 400


def test_pc_to_android_without_device_rejected(tmp_path: Path) -> None:
    ra_dir = tmp_path / "ra-config"
    (ra_dir / "Gambatte").mkdir(parents=True)
    (ra_dir / "Gambatte" / "Tetris.opt").write_text("x = 1\n", encoding="utf-8")
    router = _make_router(tmp_path, ra_dir)

    ctx = _copy(router, {"rom": "Tetris", "core": "Gambatte", "direction": "pc_to_android"})

    assert ctx.status == 400
    assert "ADB" in ctx.sent["error"]


def test_non_shared_core_rejected_before_requiring_a_device(tmp_path: Path) -> None:
    """The core check must win even with no ADB device connected — a
    non-shared core is invalid regardless of device state, so the user
    shouldn't be told to "connect ADB" for a copy that could never work."""
    ra_dir = tmp_path / "ra-config"
    (ra_dir / "Snes9x").mkdir(parents=True)
    (ra_dir / "Snes9x" / "Chrono Trigger.opt").write_text("x = 1\n", encoding="utf-8")
    router = _make_router(tmp_path, ra_dir)

    ctx = _copy(router, {"rom": "Chrono Trigger", "core": "Snes9x", "direction": "pc_to_android"})

    assert ctx.status == 400
    assert "ADB" not in ctx.sent["error"]
    assert "Snes9x" in ctx.sent["error"]


def test_pc_to_android_copies_and_reports_no_backup(tmp_path: Path, monkeypatch) -> None:
    ra_dir = tmp_path / "ra-config"
    (ra_dir / "Gambatte").mkdir(parents=True)
    (ra_dir / "Gambatte" / "Tetris.opt").write_text("x = 1\n", encoding="utf-8")
    router = _make_router(tmp_path, ra_dir)

    store: dict[str, str] = {}
    _fake_one_ready_device(monkeypatch, store)

    ctx = _copy(router, {"rom": "Tetris", "core": "Gambatte", "direction": "pc_to_android"})

    assert ctx.sent == {"ok": True, "backed_up": False, "backup_filename": None}
    assert store["/storage/emulated/0/RetroArch/config/Gambatte/Tetris.opt"] == "x = 1\n"


def test_android_to_pc_backs_up_existing_pc_override(tmp_path: Path, monkeypatch) -> None:
    ra_dir = tmp_path / "ra-config"
    (ra_dir / "Gambatte").mkdir(parents=True)
    (ra_dir / "Gambatte" / "Tetris.opt").write_text("old = 1\n", encoding="utf-8")
    router = _make_router(tmp_path, ra_dir)

    store = {"/storage/emulated/0/RetroArch/config/Gambatte/Tetris.opt": "new = 2\n"}
    _fake_one_ready_device(monkeypatch, store)

    ctx = _copy(router, {"rom": "Tetris", "core": "Gambatte", "direction": "android_to_pc"})

    assert ctx.sent["ok"] is True
    assert ctx.sent["backed_up"] is True
    backup_path = ra_dir / "Gambatte" / ctx.sent["backup_filename"]
    assert backup_path.read_text(encoding="utf-8") == "old = 1\n"
    assert (ra_dir / "Gambatte" / "Tetris.opt").read_text(encoding="utf-8") == "new = 2\n"
