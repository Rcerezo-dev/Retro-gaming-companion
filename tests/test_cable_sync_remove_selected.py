"""ANBERNIC-BULK-DEL: direction="remove_selected" borra ROMs elegidos por
filtro (mismo criterio que /api/tag-bulk) de la consola por ADB, pero SIEMPRE
copia primero el save al PC — si esa copia falla, el ROM no se toca. "los
saves habria que guardarlos siempre" es la garantia que cubre este test.
"""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import rom_manager.web.state as _state
from rom_manager.database.repository import LibraryRepository
from rom_manager.sync import adb_transport as at
from rom_manager.sync.adb_transport import AdbFileInfo
from rom_manager.web.handlers.sync_cable import _do_cable_sync


class _FakeCtx:
    def __init__(self, post_data: dict) -> None:
        self._post_data = post_data
        self.out = None

    def _send_json(self, obj) -> None:
        self.out = obj


def _config(tmp_path: Path):
    return SimpleNamespace(
        adb="adb",
        project_root=tmp_path,
        library_root=str(tmp_path / "pc"),
        anbernic_root=None,
        save_extensions=(".sav",),
        backup=SimpleNamespace(saves_enabled=False),
        data_dir=tmp_path / "data",
        notify_desktop=False,
        sync=SimpleNamespace(auto_sync_android_path="/storage/emulated/0"),
    )


def _wait_done() -> dict:
    for _ in range(50):
        status = _state._job_manager.get_status()
        if not status["cable_sync_running"]:
            return status["cable_sync_result"]
        time.sleep(0.05)
    raise AssertionError("cable_sync job never finished")


def _insert_game(repo: LibraryRepository, *, source_path: str) -> int:
    repo.upsert_game(
        original_filename=Path(source_path).name,
        source_path=source_path,
        platform="GBA",
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=Path(source_path).suffix,
        size_bytes=1,
        mtime=0,
        sha1=source_path,
        md5="M" * 32,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp="2024-01-01T00:00:00",
    )
    with repo.connect() as conn:
        row = conn.execute("SELECT id FROM games WHERE source_path = ?", (source_path,)).fetchone()
    return int(row["id"])


_DEVICE_FILES = [
    AdbFileInfo(android_path="/storage/emulated/0/gba/zelda.gba", size=10, mtime=0.0),
    AdbFileInfo(android_path="/storage/emulated/0/gba/zelda.sav", size=4, mtime=0.0),
]


def _base_request(pc: Path) -> dict:
    return {
        "pc_path": str(pc),
        "use_adb": True,
        "adb_serial": "SERIAL",
        "android_path": "/storage/emulated/0",
        "what": ["roms"],
        "direction": "remove_selected",
        "dry_run": False,
    }


def test_remove_selected_preserves_save_then_deletes_rom(tmp_path: Path, monkeypatch) -> None:
    pc = tmp_path / "pc"
    pc.mkdir()

    monkeypatch.setattr(at.AdbTransport, "ls_recursive", lambda self, *a, **kw: list(_DEVICE_FILES))
    removed: list[str] = []
    monkeypatch.setattr(at.AdbTransport, "remove", lambda self, path: removed.append(path))

    def _fake_pull(self, android_src, local_dst, *, dry_run=False, verify=False):
        local_dst.parent.mkdir(parents=True, exist_ok=True)
        local_dst.write_bytes(b"SAVE")
        return 4

    monkeypatch.setattr(at.AdbTransport, "pull", _fake_pull)

    _state._job_manager.finish("cable_sync", None)
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(pc / "gba" / "zelda.gba"))
    # No está en la consola -> debe saltarse sin tocar nada, sin contarlo como error.
    _insert_game(repo, source_path=str(pc / "gba" / "mario.gba"))

    ctx = _FakeCtx(_base_request(pc))
    _do_cable_sync(ctx, ctx._post_data, _config(tmp_path), repo, _state._job_manager)
    result = _wait_done()

    assert result["errors"] == 0
    assert result["copied"] == 1  # save preservado
    assert result["deleted_extra"] == 1  # rom eliminado
    assert removed == ["/storage/emulated/0/gba/zelda.gba"]
    assert (pc / "gba" / "zelda.sav").read_bytes() == b"SAVE"


def test_remove_selected_keeps_rom_when_save_pull_fails(tmp_path: Path, monkeypatch) -> None:
    pc = tmp_path / "pc"
    pc.mkdir()

    monkeypatch.setattr(at.AdbTransport, "ls_recursive", lambda self, *a, **kw: list(_DEVICE_FILES))
    removed: list[str] = []
    monkeypatch.setattr(at.AdbTransport, "remove", lambda self, path: removed.append(path))

    def _failing_pull(self, android_src, local_dst, *, dry_run=False, verify=False):
        raise OSError("verificación MD5 falló")

    monkeypatch.setattr(at.AdbTransport, "pull", _failing_pull)

    _state._job_manager.finish("cable_sync", None)
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(pc / "gba" / "zelda.gba"))

    ctx = _FakeCtx(_base_request(pc))
    _do_cable_sync(ctx, ctx._post_data, _config(tmp_path), repo, _state._job_manager)
    result = _wait_done()

    assert result["errors"] == 1
    assert removed == []  # nunca se borra el ROM si el save no se pudo preservar
    assert not (pc / "gba" / "zelda.sav").exists()
