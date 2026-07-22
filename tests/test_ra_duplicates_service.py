from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.services.ra_duplicates_service import (
    apply_all_review_recommendations,
    discard_all_ra_duplicates,
    discard_no_support,
    discard_ra_duplicate,
    get_ra_hash_lib,
    resolve_duplicate_ra,
)

# TABS-FIX-1's device-path detection only applies on Windows — a bare leading
# "/" is a normal, verifiable local path on POSIX (see utils/paths.is_device_path).
_windows_only = pytest.mark.skipif(os.name != "nt", reason="Windows-only device-path detection")

_TS = "2024-01-01T00:00:00"


def _insert_game(repo: LibraryRepository, *, source_path: str) -> None:
    repo.upsert_game(
        original_filename="game.gb",
        source_path=source_path,
        platform="Game Boy",
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gb",
        size_bytes=1024,
        mtime=0,
        sha1="S" * 40,
        md5="M" * 32,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp=_TS,
    )


def _count(repo: LibraryRepository) -> int:
    with repo.connect() as conn:
        return int(conn.execute("SELECT COUNT(*) AS n FROM games").fetchone()["n"])


# ── discard_ra_duplicate ──────────────────────────────────────────────────────


def test_discard_ra_duplicate_moves_to_descartados(tmp_path: Path) -> None:
    rom = tmp_path / "dup.gb"
    rom.write_bytes(b"data")
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(rom))

    result = discard_ra_duplicate(repo, str(rom))

    assert result == {"ok": True}
    assert not rom.exists()
    assert (tmp_path / "_descartados" / "dup.gb").exists()
    assert _count(repo) == 0


def test_discard_ra_duplicate_file_already_gone(tmp_path: Path) -> None:
    rom = tmp_path / "ghost.gb"  # never created
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(rom))

    result = discard_ra_duplicate(repo, str(rom))

    assert result == {"ok": True, "note": "file already missing; removed from DB"}
    assert _count(repo) == 0


@_windows_only
def test_discard_ra_duplicate_device_path_unreachable_does_not_touch_db(
    tmp_path: Path,
) -> None:
    """TABS-FIX-1: a device path (ADB scan) is never reachable via Path.exists()
    on Windows even when the file is alive on the console — must not silently
    delete the DB row and report success."""
    device_path = "/storage/emulated/0/RetroArch/roms/gb/dup.gb"
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=device_path)

    result = discard_ra_duplicate(repo, device_path)

    assert "error" in result
    assert _count(repo) == 1


@_windows_only
def test_discard_ra_duplicate_device_path_with_adb_transport_deletes_via_adb(
    tmp_path: Path,
) -> None:
    """TABS-FIX-1a: with a connected device, the file is deleted for real via
    ADB before the DB row is touched."""
    from types import SimpleNamespace

    device_path = "/storage/emulated/0/RetroArch/roms/gb/dup.gb"
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=device_path)
    adb = SimpleNamespace(removed=[])
    adb.remove = lambda path: adb.removed.append(path)

    result = discard_ra_duplicate(repo, device_path, adb)

    # missing=True because Path.exists() is always False for a device path on
    # Windows — the "note" is a pre-existing quirk unrelated to this fix.
    assert result["ok"] is True
    assert adb.removed == [device_path]
    assert _count(repo) == 0


@_windows_only
def test_discard_ra_duplicate_device_path_adb_remove_fails_does_not_touch_db(
    tmp_path: Path,
) -> None:
    from types import SimpleNamespace

    device_path = "/storage/emulated/0/RetroArch/roms/gb/dup.gb"
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=device_path)

    def _boom(path):
        raise RuntimeError("device offline")

    adb = SimpleNamespace(remove=_boom)

    result = discard_ra_duplicate(repo, device_path, adb)

    assert "error" in result
    assert _count(repo) == 1


def test_discard_ra_duplicate_dest_collision_deletes_source(tmp_path: Path) -> None:
    rom = tmp_path / "dup.gb"
    rom.write_bytes(b"new")
    descartados = tmp_path / "_descartados"
    descartados.mkdir()
    (descartados / "dup.gb").write_bytes(b"old")  # name already taken
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(rom))

    result = discard_ra_duplicate(repo, str(rom))

    assert result == {"ok": True}
    # Source removed outright; the pre-existing discard is preserved
    assert not rom.exists()
    assert (descartados / "dup.gb").read_bytes() == b"old"
    assert _count(repo) == 0


# ── discard_all_ra_duplicates ─────────────────────────────────────────────────


def test_discard_all_ra_duplicates_only_unsupported(tmp_path: Path) -> None:
    supported = tmp_path / "keep.gb"
    unsupported = tmp_path / "drop.gb"
    supported.write_bytes(b"a")
    unsupported.write_bytes(b"b")
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(supported))
    _insert_game(repo, source_path=str(unsupported))

    ra_dups = {
        "groups": [
            {
                "entries": [
                    {"source_path": str(supported), "ra_supported": True},
                    {"source_path": str(unsupported), "ra_supported": False},
                ]
            }
        ]
    }
    result = discard_all_ra_duplicates(repo, ra_dups)

    assert result == {"discarded": 1, "failed": 0, "errors": []}
    assert supported.exists()
    assert not unsupported.exists()
    assert (tmp_path / "_descartados" / "drop.gb").exists()
    assert _count(repo) == 1


def test_discard_all_ra_duplicates_note_passthrough(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    result = discard_all_ra_duplicates(repo, {"note": "nothing"})
    assert result == {"discarded": 0, "failed": 0, "errors": [], "note": "nothing"}


# ── discard_no_support ────────────────────────────────────────────────────────


def test_discard_no_support_commits_db(tmp_path: Path) -> None:
    """Regression: the old handler forgot to commit, so rows survived. The
    service must actually persist the deletion."""
    rom = tmp_path / "ns.gb"
    rom.write_bytes(b"x")
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(rom))

    result = discard_no_support(repo, [{"source_path": str(rom)}])

    assert result == {"discarded": 1, "failed": 0, "errors": []}
    assert not rom.exists()
    assert (tmp_path / "_descartados" / "ns.gb").exists()
    # The row is gone AND committed (a fresh connection still sees it removed)
    assert _count(repo) == 0


def test_discard_no_support_empty(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    result = discard_no_support(repo, [])
    assert result == {"discarded": 0, "failed": 0, "errors": [], "note": "No games to discard."}


# ── resolve_duplicate_ra ──────────────────────────────────────────────────────


def test_resolve_duplicate_ra_discards_paths(tmp_path: Path) -> None:
    keep = tmp_path / "keep.gb"
    drop1 = tmp_path / "drop1.gb"
    drop2 = tmp_path / "drop2.gb"  # never created on disk
    keep.write_bytes(b"k")
    drop1.write_bytes(b"d")
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(keep))
    _insert_game(repo, source_path=str(drop1))
    _insert_game(repo, source_path=str(drop2))

    result = resolve_duplicate_ra(repo, str(keep), [str(drop1), str(drop2)])

    assert result == {"discarded": 2, "failed": 0, "errors": []}
    assert keep.exists()
    assert not drop1.exists()
    assert (tmp_path / "_descartados" / "drop1.gb").exists()
    assert _count(repo) == 1  # only keep survives


# ── get_ra_hash_lib TTL (REV43-28) ────────────────────────────────────────────


def _write_ra_cache(tmp_path: Path, console_id: int, *, age_seconds: float) -> Path:
    cache_dir = tmp_path / ".rommgr" / "ra_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"ra_hashes_{console_id}.json"
    cache_file.write_text(
        json.dumps([{"ID": 1, "Title": "Game", "NumAchievements": 10, "Hashes": ["m" * 32]}]),
        encoding="utf-8",
    )
    stale_time = time.time() - age_seconds
    os.utime(cache_file, (stale_time, stale_time))
    return cache_file


def test_get_ra_hash_lib_ignores_stale_cache(tmp_path: Path) -> None:
    """REV43-28: get_ra_hash_lib must respect the same 1-week TTL as
    ra_client.fetch_hash_library — a stale cache used for duplicate
    resolution is as wrong as a stale cache used for the RA check."""
    config = load_config(tmp_path)
    _write_ra_cache(tmp_path, console_id=4, age_seconds=8 * 24 * 3600)  # 8 days old

    lib = get_ra_hash_lib(config, "Game Boy Advance", {})

    assert lib == {}


def test_get_ra_hash_lib_uses_fresh_cache(tmp_path: Path) -> None:
    config = load_config(tmp_path)
    _write_ra_cache(tmp_path, console_id=4, age_seconds=3600)  # 1 hour old

    lib = get_ra_hash_lib(config, "Game Boy Advance", {})

    assert "m" * 32 in lib
    assert lib["m" * 32].achievements == 10


# ── apply_all_review_recommendations (TABS-FIX-6) ─────────────────────────────


def test_apply_all_resolves_sha1_group(tmp_path: Path) -> None:
    """A sha1/title/ra group: the non-recommended entries get discarded via
    resolve_duplicate_ra, exactly like a single-group 'Aplicar' click would."""
    from rom_manager.web.builders.duplicates import _build_review_queue

    keep = tmp_path / "tetris.gb"
    keep.write_bytes(b"keep")
    dupe = tmp_path / "backup" / "tetris.gb"
    dupe.parent.mkdir()
    dupe.write_bytes(b"dupe")
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    for path in (keep, dupe):
        repo.upsert_game(
            original_filename="tetris.gb",
            source_path=str(path),
            platform="Game Boy",
            file_type="rom",
            relative_parent="",
            region="USA",
            extension=".gb",
            size_bytes=4,
            mtime=0,
            sha1="A" * 40,
            md5="M" * 32,
            crc32="CCCCCCCC",
            set_type="single",
            timestamp=_TS,
        )

    queue = _build_review_queue(repo, repo, None)
    assert queue["total_groups"] == 1

    result = apply_all_review_recommendations(lambda _path: repo, [repo], config=None, queue=queue)

    assert result["errors"] == []
    assert result["resolved"] == 1
    assert _count(repo) == 1  # the discarded entry's row is gone
    with repo.connect() as conn:
        remaining = conn.execute("SELECT source_path FROM games").fetchall()
    assert remaining[0]["source_path"] in {str(keep), str(dupe)}


def test_apply_all_routes_plan_conflicts_to_apply_ra_conflicts(monkeypatch) -> None:
    """Groups flagged disk/collision must never go through resolve_duplicate_ra
    (there's no 'recommended entry to keep' semantics for a plan conflict) —
    they're routed to apply_ra_conflicts instead, once per repo."""
    import rom_manager.services.ra_duplicates_service as mod

    calls: list[object] = []
    monkeypatch.setattr(
        mod, "apply_ra_conflicts", lambda repo, config, adb_transport=None: calls.append(repo) or {}
    )
    resolve_calls: list[object] = []
    monkeypatch.setattr(
        mod,
        "resolve_duplicate_ra",
        lambda *a, **kw: resolve_calls.append(a) or {"discarded": 0, "errors": []},
    )

    queue = {
        "groups": [
            {
                "reasons": ["disk"],
                "entries": [{"source_path": "/roms/a.gb", "recommended": True}],
            }
        ]
    }
    repos = ["repo-pc", "repo-android"]

    result = mod.apply_all_review_recommendations(
        lambda _path: "repo-pc", repos, config=None, queue=queue
    )

    assert calls == ["repo-pc", "repo-android"]
    assert resolve_calls == []
    assert result == {"resolved": 0, "errors": []}
