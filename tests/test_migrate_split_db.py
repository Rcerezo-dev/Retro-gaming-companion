"""REV43-5: _do_migrate_split_db no debe borrar en el repo PC las filas cuyo
upsert al repo Android falló — antes se borraban todas las filas "Android"
incondicionalmente, perdiendo el catálogo (tags, RA, stats) de las que
fallaron."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.sync_cloud import _do_migrate_split_db


class _FakeCtx:
    def __init__(self) -> None:
        self.out: dict | None = None

    def _send_json(self, obj: dict) -> None:
        self.out = obj


def _config(tmp_path: Path, anbernic_root: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        library_root=tmp_path / "pc",
        anbernic_root=anbernic_root or str(tmp_path / "android"),
        database_path=tmp_path / "pc.db",
        database_path_android=tmp_path / "android.db",
    )


def _insert_game(repo: LibraryRepository, source_path: str, sha1: str) -> None:
    with repo.batch() as conn:
        repo.upsert_game(
            original_filename=Path(source_path).name,
            source_path=source_path,
            platform="gba",
            file_type="rom",
            relative_parent="",
            region=None,
            extension=".gba",
            size_bytes=1,
            mtime=0,
            sha1=sha1,
            md5="",
            crc32="",
            set_type="",
            timestamp="2026-01-01T00:00:00",
            connection=conn,
        )


def test_failed_upsert_keeps_source_row(tmp_path: Path) -> None:
    (tmp_path / "pc").mkdir()
    repo = LibraryRepository(tmp_path / "pc.db")
    repo_android = LibraryRepository(tmp_path / "android.db")

    ok_path = str(tmp_path / "android" / "ok.gba")
    fail_path = str(tmp_path / "android" / "fail.gba")
    _insert_game(repo, ok_path, sha1="ok-sha1")
    _insert_game(repo, fail_path, sha1="fail-sha1")

    ctx = _FakeCtx()
    config = _config(tmp_path)
    orig_upsert = repo_android.upsert_game

    def _flaky_upsert(**kwargs):
        if kwargs["source_path"] == fail_path:
            raise RuntimeError("simulated failure")
        return orig_upsert(**kwargs)

    with patch.object(repo_android, "upsert_game", side_effect=_flaky_upsert):
        _do_migrate_split_db(ctx, config, repo, repo_android)

    assert ctx.out["migrated_games"] == 1
    assert len(ctx.out["errors"]) == 1

    with repo.connect() as conn:
        remaining = {r["source_path"] for r in conn.execute("SELECT source_path FROM games")}
    assert ok_path not in remaining  # migrada con éxito -> borrada del origen
    assert fail_path in remaining  # fallo -> debe seguir en el origen (reintentable)

    with repo_android.connect() as conn:
        android_paths = {r["source_path"] for r in conn.execute("SELECT source_path FROM games")}
    assert ok_path in android_paths
    assert fail_path not in android_paths


def test_pc_row_outside_library_root_is_not_misclassified_as_android(tmp_path: Path) -> None:
    """VAL-FIX-2: the old heuristic ("not under library_root") migrated ANY
    PC row that wasn't exactly under library_root — a different drive, an
    old scan, mismatched casing — as if it were an Android row. Classifying
    by real device-path evidence (anbernic_root / POSIX path) instead must
    leave a genuine PC row (just outside library_root) in the PC repo."""
    (tmp_path / "pc").mkdir()
    repo = LibraryRepository(tmp_path / "pc.db")
    repo_android = LibraryRepository(tmp_path / "android.db")

    # A real PC path that happens to live outside the configured library_root
    # (e.g. a leftover scan of another drive) — must stay in the PC repo.
    other_drive_path = str(tmp_path / "other_pc_drive" / "game.gba")
    android_path = str(tmp_path / "android" / "game2.gba")
    _insert_game(repo, other_drive_path, sha1="pc-sha1")
    _insert_game(repo, android_path, sha1="android-sha1")

    ctx = _FakeCtx()
    config = _config(tmp_path)
    _do_migrate_split_db(ctx, config, repo, repo_android)

    assert ctx.out["migrated_games"] == 1

    with repo.connect() as conn:
        remaining = {r["source_path"] for r in conn.execute("SELECT source_path FROM games")}
    assert other_drive_path in remaining  # PC row outside library_root -> stays in PC repo
    assert android_path not in remaining  # real Android row -> migrated out

    with repo_android.connect() as conn:
        android_paths = {r["source_path"] for r in conn.execute("SELECT source_path FROM games")}
    assert android_path in android_paths
    assert other_drive_path not in android_paths
