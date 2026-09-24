"""ANBERNIC-BULK-SEND: direction="send_selected" es la contraparte de
remove_selected — envía a la consola por ADB los ROMs de los juegos que
cumplen el filtro actual (mismo criterio que /api/tag-bulk), sin pasar por
el tag "anbernic" ni por un árbol de directorios completo.
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


def _base_request(pc: Path) -> dict:
    return {
        "pc_path": str(pc),
        "use_adb": True,
        "adb_serial": "SERIAL",
        "android_path": "/storage/emulated/0",
        "what": ["roms"],
        "direction": "send_selected",
        "dry_run": False,
    }


def test_send_selected_pushes_filtered_roms(tmp_path: Path, monkeypatch) -> None:
    pc = tmp_path / "pc"
    (pc / "gba").mkdir(parents=True)
    (pc / "gba" / "zelda.gba").write_bytes(b"ROMDATA")

    monkeypatch.setattr(at.AdbTransport, "ls_recursive", lambda self, *a, **kw: [])
    pushed: list[tuple[str, str]] = []

    def _fake_push(self, local_src, android_dst, *, dry_run=False, verify=False):
        pushed.append((str(local_src), android_dst))
        return local_src.stat().st_size

    monkeypatch.setattr(at.AdbTransport, "push", _fake_push)

    _state._job_manager.finish("cable_sync", None)
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(pc / "gba" / "zelda.gba"))
    # No existe en el PC -> se salta sin contarlo como error.
    _insert_game(repo, source_path=str(pc / "gba" / "mario.gba"))

    ctx = _FakeCtx(_base_request(pc))
    _do_cable_sync(ctx, ctx._post_data, _config(tmp_path), repo, _state._job_manager)
    result = _wait_done()

    assert result["errors"] == 0
    assert result["copied"] == 1
    assert pushed == [(str(pc / "gba" / "zelda.gba"), "/storage/emulated/0/gba/zelda.gba")]


def test_send_selected_skip_existing_same_size(tmp_path: Path, monkeypatch) -> None:
    pc = tmp_path / "pc"
    (pc / "gba").mkdir(parents=True)
    (pc / "gba" / "zelda.gba").write_bytes(b"ROMDATA")  # 7 bytes

    monkeypatch.setattr(
        at.AdbTransport,
        "ls_recursive",
        lambda self, *a, **kw: [
            AdbFileInfo(android_path="/storage/emulated/0/gba/zelda.gba", size=7, mtime=0.0)
        ],
    )
    pushed: list[str] = []
    monkeypatch.setattr(
        at.AdbTransport,
        "push",
        lambda self, local_src, android_dst, **kw: pushed.append(android_dst),
    )

    _state._job_manager.finish("cable_sync", None)
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(pc / "gba" / "zelda.gba"))

    data = _base_request(pc)
    data["skip_existing"] = True
    ctx = _FakeCtx(data)
    _do_cable_sync(ctx, ctx._post_data, _config(tmp_path), repo, _state._job_manager)
    result = _wait_done()

    assert result["errors"] == 0
    assert result["copied"] == 0
    assert result["skipped"] == 1
    assert pushed == []
