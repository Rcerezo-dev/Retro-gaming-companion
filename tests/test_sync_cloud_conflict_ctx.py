"""SAVES-CONFLICT-CTX-1: el payload de un conflicto de Cloud Sync debe llevar
mtimes/tamaños de cada lado y, si hay un juego con el mismo stem en la BD,
su playtime por origen — sin romper el flujo cuando no hay match."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.sync.conflict_resolver import SyncDecision
from rom_manager.web.handlers.sync_cloud import _decision_payload

TS = "2026-01-01T00:00:00"


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "library.db")


def _upsert(repo: LibraryRepository, **overrides) -> None:
    defaults = dict(
        original_filename="Mario.gba",
        source_path="/roms/gba/Mario.gba",
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


def _decision(
    action: str, *, local_size: int | None = None, remote_size: int | None = None
) -> SyncDecision:
    d = SyncDecision(
        action=action,
        relative="gba/mario.srm",
        local_mtime=datetime(2026, 1, 1, tzinfo=UTC),
        remote_mtime=datetime(2026, 1, 2, tzinfo=UTC),
        last_sync_at=None,
    )
    d.local_size = local_size
    d.remote_size = remote_size
    return d


def test_non_conflict_gets_no_extra_context(repo: LibraryRepository) -> None:
    payload = _decision_payload(_decision("upload"), repo)
    assert payload == {"action": "upload", "relative": "gba/mario.srm"}


def test_conflict_includes_mtimes_and_sizes(repo: LibraryRepository) -> None:
    payload = _decision_payload(_decision("conflict", local_size=100, remote_size=200), repo)
    assert payload["local_mtime"] == "2026-01-01T00:00:00+00:00"
    assert payload["remote_mtime"] == "2026-01-02T00:00:00+00:00"
    assert payload["local_size"] == 100
    assert payload["remote_size"] == 200


def test_conflict_with_matching_game_includes_playtime(repo: LibraryRepository) -> None:
    _upsert(repo, original_filename="mario.gba", source_path="/roms/gba/mario.gba")
    repo.set_playtime_minutes("mario", 42, "pc")
    repo.set_playtime_minutes("mario", 7, "android")

    payload = _decision_payload(_decision("conflict"), repo)

    assert payload["playtime_minutes_pc"] == 42
    assert payload["playtime_minutes_android"] == 7


def test_conflict_without_matching_game_omits_playtime(repo: LibraryRepository) -> None:
    payload = _decision_payload(_decision("conflict"), repo)

    assert "playtime_minutes_pc" not in payload
    assert "playtime_minutes_android" not in payload
