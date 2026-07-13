"""AUD-6 — verificación profunda de CHDs en el health check.

Un CHD puede tener SHA1 de archivo estable y checksums internos inválidos
desde su creación; con ``chd_verify=True`` el health check ejecuta
``chdman verify`` sobre cada CHD cuyo hash coincide y reporta los fallos.
"""

from __future__ import annotations

import subprocess

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.hashing.hash_calculator import calculate_hashes
from rom_manager.utils.health_checker import check_library_health


@pytest.fixture()
def repo_with_chd(tmp_path):
    chd = tmp_path / "juego.chd"
    chd.write_bytes(b"CHD FILE CONTENT")
    hashes = calculate_hashes(chd)
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    repo.upsert_game(
        original_filename=chd.name,
        source_path=str(chd),
        platform="PlayStation",
        file_type="rom",
        relative_parent="",
        region="",
        extension=".chd",
        size_bytes=chd.stat().st_size,
        mtime=0,
        sha1=hashes.sha1,
        md5=hashes.md5,
        crc32=hashes.crc32,
        set_type="single",
        timestamp="2026-07-12T00:00:00",
    )
    return repo


def _fake_chdman(returncode: int):
    def run(cmd, capture_output=True, timeout=None):
        assert cmd[1] == "verify"
        return subprocess.CompletedProcess(cmd, returncode, stdout=b"", stderr=b"")

    return run


def test_chd_invalid_detected(repo_with_chd, monkeypatch) -> None:
    monkeypatch.setattr(subprocess, "run", _fake_chdman(1))
    s = check_library_health(repo_with_chd, chd_verify=True, chdman_path="chdman")
    assert s.chd_invalid == 1 and s.ok == 0
    assert s.results[0].status == "chd_invalid"


def test_chd_valid_counts_ok(repo_with_chd, monkeypatch) -> None:
    monkeypatch.setattr(subprocess, "run", _fake_chdman(0))
    s = check_library_health(repo_with_chd, chd_verify=True, chdman_path="chdman")
    assert s.ok == 1 and s.chd_invalid == 0


def test_off_by_default_skips_chdman(repo_with_chd, monkeypatch) -> None:
    def boom(*a, **k):
        raise AssertionError("chdman no debe ejecutarse sin chd_verify")

    monkeypatch.setattr(subprocess, "run", boom)
    s = check_library_health(repo_with_chd)  # default: chd_verify=False
    assert s.ok == 1 and s.chd_invalid == 0


def test_missing_chdman_does_not_flag_files(repo_with_chd, monkeypatch) -> None:
    def missing(*a, **k):
        raise FileNotFoundError("chdman.exe no encontrado")

    monkeypatch.setattr(subprocess, "run", missing)
    s = check_library_health(repo_with_chd, chd_verify=True, chdman_path="no-existe")
    assert s.ok == 1 and s.chd_invalid == 0  # sin chdman no se marca nada como inválido
