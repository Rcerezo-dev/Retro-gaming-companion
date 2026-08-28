"""ANBERNIC-PICK-2: Cable Sync respeta `only_tagged` — con el filtro activo,
solo los ROMs marcados con el tag "anbernic" (game_tags, ver ANBERNIC-PICK-1)
salen del PC hacia la consola. Por defecto (only_tagged ausente/False) el
comportamiento no cambia respecto a antes.
"""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import rom_manager.web.state as _state
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.sync_cable import register_cable
from rom_manager.web.router import Router

_TS = "2024-01-01T00:00:00"


def _config(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        adb="adb",
        project_root=tmp_path,
        data_dir=tmp_path / ".rommgr",
        library_root=None,
        anbernic_root=None,
        save_extensions=(".sav",),
        excluded_directories=frozenset(),
        notify_desktop=False,
        sync=SimpleNamespace(clock_skew_threshold_s=120),
        backup=SimpleNamespace(saves_enabled=False),
    )


class _FakeCtx:
    def __init__(self, post_data: dict) -> None:
        self._post_data = post_data
        self.out: dict | None = None

    def _send_json(self, obj: dict) -> None:
        self.out = obj


def _write(root: Path, *parts: str, content: bytes = b"x") -> Path:
    p = root.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p


def _insert_game(repo: LibraryRepository, *, source_path: str, platform: str = "Arcade") -> int:
    repo.upsert_game(
        original_filename=Path(source_path).name,
        source_path=source_path,
        platform=platform,
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=Path(source_path).suffix,
        size_bytes=1,
        mtime=0,
        sha1=source_path,  # único por archivo, valor real irrelevante aquí
        md5="M" * 32,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp=_TS,
    )
    with repo.connect() as conn:
        row = conn.execute("SELECT id FROM games WHERE source_path = ?", (source_path,)).fetchone()
    return int(row["id"])


def _run_sync(tmp_path: Path, data: dict, repository: LibraryRepository | None) -> dict:
    _state._job_manager.finish("cable_sync", None)
    router = Router()
    register_cable(
        router, config=_config(tmp_path), repository=repository, job_manager=_state._job_manager
    )
    ctx = _FakeCtx(data)
    router.dispatch("POST", "/api/cable-sync", ctx)
    assert ctx.out.get("status") == "started", ctx.out

    for _ in range(100):
        if not _state._job_manager.get_status()["cable_sync_running"]:
            break
        time.sleep(0.02)
    return _state._job_manager.get_status()["cable_sync_result"]


def test_only_tagged_skips_untagged_roms(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    marked = _write(pc, "arcade", "sf2.zip")
    unmarked = _write(pc, "arcade", "dino.zip")
    ab.mkdir()

    repo = LibraryRepository(tmp_path / "pc.sqlite")
    marked_id = _insert_game(repo, source_path=str(marked))
    _insert_game(repo, source_path=str(unmarked))
    repo.add_tag(marked_id, "anbernic")

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["roms"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
            "only_tagged": True,
        },
        repo,
    )

    assert res["copied"] == 1
    assert (ab / "arcade" / "sf2.zip").exists()
    assert not (ab / "arcade" / "dino.zip").exists()


def test_only_tagged_false_copies_everything_as_before(tmp_path: Path) -> None:
    """Sin el checkbox activado, el comportamiento no cambia — ni falta la
    marca ni hace falta un `repository` real (pasa None, como antes)."""
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(pc, "arcade", "sf2.zip")
    _write(pc, "arcade", "dino.zip")
    ab.mkdir()

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["roms"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
        },
        None,
    )

    assert res["copied"] == 2
    assert (ab / "arcade" / "sf2.zip").exists()
    assert (ab / "arcade" / "dino.zip").exists()


def test_only_tagged_does_not_filter_saves(tmp_path: Path) -> None:
    """El filtro solo aplica a ROMs — un save nunca lleva tag y no debe
    bloquearse aunque only_tagged esté activo."""
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(pc, "gba", "mario.sav")
    ab.mkdir()

    repo = LibraryRepository(tmp_path / "pc.sqlite")

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["saves"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
            "only_tagged": True,
        },
        repo,
    )

    assert res["copied"] == 1
    assert (ab / "gba" / "mario.sav").exists()


def test_only_tagged_does_not_block_anbernic_to_pc(tmp_path: Path) -> None:
    """El filtro solo decide qué SALE del PC — tirar de la consola hacia el
    PC (backup) no debe verse afectado por marcas del lado PC."""
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    pc.mkdir()
    _write(ab, "arcade", "sf2.zip")

    repo = LibraryRepository(tmp_path / "pc.sqlite")

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["roms"],
            "direction": "anbernic_to_pc",
            "dry_run": False,
            "only_tagged": True,
        },
        repo,
    )

    assert res["copied"] == 1
    assert (pc / "arcade" / "sf2.zip").exists()
