from __future__ import annotations

import time
from pathlib import Path

import pytest

from rom_manager.converters.chd_converter import synthesize_cue_text
from tests.test_ra_hash_psx import _build_psx_image

_CHDMAN = Path(__file__).resolve().parent.parent.parent / "tools" / "chdman.exe"

pytestmark = pytest.mark.skipif(not _CHDMAN.exists(), reason="chdman.exe no disponible en tools/")


def _wait_job(client, key, timeout=15.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = client.get_json("/api/job-status")
        if not status[f"{key}_running"]:
            return status
        time.sleep(0.02)
    raise TimeoutError(f"{key} job did not finish in {timeout}s")


def test_convert_chd_dry_run_counts_bare_bins_and_cue_sets(client, config, tmp_path):
    """CHD-CLEANUP-1: /api/convert-chd must see bare .bin files too, not only
    .cue+.bin sets -- the common shape for PS1 dumps in this library."""
    config.chdman = str(_CHDMAN)
    source = tmp_path / "psx"

    bare_dir = source / "bare"
    bare_dir.mkdir(parents=True)
    _build_psx_image(bare_dir)  # bare/game.bin, no sidecar .cue

    set_dir = source / "set"
    set_dir.mkdir(parents=True)
    set_bin = _build_psx_image(set_dir)
    (set_dir / "game.cue").write_text(synthesize_cue_text(set_bin), encoding="utf-8")

    resp = client.post_json("/api/convert-chd", {"source_path": str(source), "dry_run": True})
    assert resp["status"] == "started"
    status = _wait_job(client, "convert_chd")
    result = status["convert_chd_result"]
    assert result["converted"] == 2, result
    assert result["failed"] == 0


def test_convert_chd_apply_deletes_bare_bin_when_verified(client, config, tmp_path):
    """CHD-CLEANUP-1: with delete_source=True and a verified .chd, the source
    .bin (the 93 GB PSX gap found in the real library) must actually go."""
    config.chdman = str(_CHDMAN)
    source = tmp_path / "psx"
    source.mkdir()
    bin_path = _build_psx_image(source)

    resp = client.post_json(
        "/api/convert-chd",
        {"source_path": str(source), "dry_run": False, "delete_source": True},
    )
    assert resp["status"] == "started"
    status = _wait_job(client, "convert_chd")
    result = status["convert_chd_result"]
    assert result["converted"] == 1, result

    assert not bin_path.exists()
    assert (source / "game.chd").exists()


def test_convert_chd_apply_keeps_bare_bin_without_delete_source(client, config, tmp_path):
    config.chdman = str(_CHDMAN)
    source = tmp_path / "psx"
    source.mkdir()
    bin_path = _build_psx_image(source)

    resp = client.post_json(
        "/api/convert-chd",
        {"source_path": str(source), "dry_run": False, "delete_source": False},
    )
    assert resp["status"] == "started"
    status = _wait_job(client, "convert_chd")
    result = status["convert_chd_result"]
    assert result["converted"] == 1, result

    assert bin_path.exists()
    assert (source / "game.chd").exists()
