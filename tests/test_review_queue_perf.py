"""REVIEW-QUEUE-PERF-1b/1e: lectura de extensión sin Path y caché de la cola de revisión."""

from __future__ import annotations

from pathlib import Path, PureWindowsPath

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.utils.paths import is_device_path
from rom_manager.web.builders import duplicates as dup
from rom_manager.web.review_queue_cache import ReviewQueueCache

_PATHS = [
    "E:/RetroVault/ROMS/psx/Game (USA).bin",
    "E:/RetroVault/ROMS/psx/Game (USA).BIN",
    "E:/RetroVault/ROMS/psx/Game (USA).cue",
    "E:/RetroVault/ROMS/psx/Game.img",
    "E:/RetroVault/ROMS/psx/Game.SUB",
    "E:/RetroVault/ROMS/psx/.bin",  # fichero oculto: Path.suffix == ""
    "E:/RetroVault/ROMS/dir.bin/Game",  # directorio con extensión, archivo sin ella
    "/storage/1234-5678/ROMs/psx/Game (USA).bin",
    "Game.tar.bin",
    "Game",
]


@pytest.mark.parametrize("path", _PATHS)
def test_disc_data_sibling_matches_pathlib_reference(path: str) -> None:
    """Misma decisión que la versión con Path.suffix: solo una ruta de dispositivo se resuelve
    con `known_paths`; una ruta local mira el disco (aquí no existe nada)."""
    ext = PureWindowsPath(path).suffix.lower()
    sibling = {".bin": ".cue", ".img": ".ccd", ".sub": ".ccd"}.get(ext)
    stem = path.rsplit(".", 1)[0]
    known = frozenset({(stem + sibling).lower()}) if sibling else frozenset()
    assert dup._is_disc_data_sibling(path, known) is (sibling is not None and is_device_path(path))
    assert dup._is_disc_data_sibling(path, frozenset()) is False


def test_disc_data_sibling_uses_the_real_filesystem_for_pc_paths(tmp_path: Path) -> None:
    (tmp_path / "Game.bin").write_bytes(b"x")
    assert dup._is_disc_data_sibling(str(tmp_path / "Game.bin")) is False  # sin .cue
    (tmp_path / "Game.cue").write_text("FILE")
    assert dup._is_disc_data_sibling(str(tmp_path / "Game.bin")) is True
    (tmp_path / "Other.img").write_bytes(b"x")
    assert dup._is_disc_data_sibling(str(tmp_path / "Other.img")) is False
    (tmp_path / "Other.ccd").write_text("[CloneCD]")
    assert dup._is_disc_data_sibling(str(tmp_path / "Other.img")) is True


def _repos(tmp_path: Path) -> tuple[LibraryRepository, LibraryRepository]:
    return LibraryRepository(tmp_path / "pc.db"), LibraryRepository(tmp_path / "an.db")


def test_cache_reuses_value_until_a_db_changes(tmp_path: Path) -> None:
    repos = _repos(tmp_path)
    cache = ReviewQueueCache()
    calls: list[int] = []

    def build() -> dict:
        calls.append(1)
        return {"n": len(calls)}

    assert cache.get_or_build(repos, build) == {"n": 1}
    assert cache.get_or_build(repos, build) == {"n": 1}  # cacheado
    assert len(calls) == 1

    repos[0].exclude_duplicate_group("some-group")  # cualquier escritura cambia la BD
    assert cache.get_or_build(repos, build) == {"n": 2}


def test_cache_expires_after_ttl_and_on_config_change(tmp_path: Path) -> None:
    repos = _repos(tmp_path)
    now = [0.0]
    cache = ReviewQueueCache(ttl=10.0, clock=lambda: now[0])
    calls: list[int] = []

    def build() -> int:
        calls.append(1)
        return len(calls)

    assert cache.get_or_build(repos, build, extra="cfg-a") == 1
    now[0] = 5.0
    assert cache.get_or_build(repos, build, extra="cfg-a") == 1  # dentro del TTL
    assert cache.get_or_build(repos, build, extra="cfg-b") == 2  # otra config
    now[0] = 20.0
    assert cache.get_or_build(repos, build, extra="cfg-b") == 3  # caducada
