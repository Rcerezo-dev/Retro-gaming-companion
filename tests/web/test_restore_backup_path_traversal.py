"""Regression test for REV43-16: post_restore_backup used a plain string-prefix
check (str.startswith) to confirm the restore target was inside library_root.
A sibling directory sharing the same string prefix (e.g. "GamesEvil" when
library_root is "Games") slipped right past it.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.games import register
from rom_manager.web.router import Router


class _FakeCtx:
    def __init__(self, post_data: dict) -> None:
        self._post_data = post_data
        self.sent: dict | None = None

    def _send_json(self, data: dict) -> None:
        self.sent = data


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "lib.sqlite")


@pytest.fixture
def config(tmp_path: Path):
    cfg = load_config(tmp_path)
    cfg.library_root = tmp_path / "Games"
    cfg.library_root.mkdir(parents=True, exist_ok=True)
    return cfg


@pytest.fixture
def router(repo, config) -> Router:
    r = Router()
    register(
        r,
        config=config,
        repository=repo,
        get_repo_fn=lambda _device=None: repo,
        job_manager=MagicMock(),
    )
    return r


def test_restore_rejects_sibling_dir_sharing_string_prefix(router, config, tmp_path):
    """ "C:/Games" is a literal string prefix of "C:/GamesEvil/..." even though
    GamesEvil is not inside Games — the naive fix must not fall for this."""
    evil_dir = tmp_path / "GamesEvil"
    evil_dir.mkdir()
    backup = tmp_path / "backup.srm"
    backup.write_bytes(b"fake save")

    ctx = _FakeCtx(
        {
            "backup_path": str(backup),
            "original_save": str(evil_dir / "save.srm"),
        }
    )
    router.dispatch("POST", "/api/restore-backup", ctx)

    assert ctx.sent == {"error": "La ruta destino está fuera de la biblioteca"}
    assert not (evil_dir / "save.srm").exists()


def test_restore_allows_path_inside_library_root(router, config):
    target_dir = config.library_root / "gba"
    target_dir.mkdir()
    backup = config.library_root.parent / "backup.srm"
    backup.write_bytes(b"fake save")

    ctx = _FakeCtx(
        {
            "backup_path": str(backup),
            "original_save": str(target_dir / "save.srm"),
        }
    )
    router.dispatch("POST", "/api/restore-backup", ctx)

    assert ctx.sent == {"ok": True, "restored_to": str(target_dir / "save.srm")}
    assert (target_dir / "save.srm").read_bytes() == b"fake save"
