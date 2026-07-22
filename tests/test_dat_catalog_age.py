"""Tests for DAT-DL-4: TTL freshness check and catalog-list age metadata."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from rom_manager.web.handlers.scan import (
    _DAT_TTL_DAYS,
    _build_dat_catalog_list,
    _is_dat_fresh,
)
from rom_manager.web.jobs.manager import JobManager


def _touch(path: Path, age_days: float = 0.0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x00")
    if age_days:
        # -1s de margen: en Windows time.time() y datetime.now() comparten un
        # reloj que avanza en ticks (~15.6ms); dentro del mismo tick la resta
        # puede dar age_days*86400 - 1µs por redondeo float y .days cae en N-1.
        mtime = time.time() - age_days * 86_400 - 1
        import os

        os.utime(path, (mtime, mtime))
    return path


def _make_config(tmp_path: Path):
    cfg = MagicMock()
    cfg.catalogs_nointro_dir = tmp_path / "nointro"
    cfg.catalogs_redump_dir = tmp_path / "redump"
    return cfg


# ── _is_dat_fresh ─────────────────────────────────────────────────────────────


class TestIsDatFresh:
    def test_fresh_file_is_fresh(self, tmp_path: Path) -> None:
        f = _touch(tmp_path / "test.dat", age_days=0)
        assert _is_dat_fresh(f) is True

    def test_file_just_under_ttl_is_fresh(self, tmp_path: Path) -> None:
        f = _touch(tmp_path / "test.dat", age_days=_DAT_TTL_DAYS - 1)
        assert _is_dat_fresh(f) is True

    def test_file_at_ttl_is_stale(self, tmp_path: Path) -> None:
        f = _touch(tmp_path / "test.dat", age_days=_DAT_TTL_DAYS)
        assert _is_dat_fresh(f) is False

    def test_old_file_is_stale(self, tmp_path: Path) -> None:
        f = _touch(tmp_path / "test.dat", age_days=30)
        assert _is_dat_fresh(f) is False


# ── _build_dat_catalog_list ───────────────────────────────────────────────────


class TestBuildDatCatalogList:
    def test_missing_dat_has_no_age(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        result = _build_dat_catalog_list(cfg)
        missing = [s for s in result["systems"] if not s["downloaded"]]
        assert len(missing) > 0
        for s in missing:
            assert s["mtime_iso"] is None
            assert s["age_days"] is None
            assert s["stale"] is False

    def test_fresh_dat_not_stale(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        cfg.catalogs_nointro_dir.mkdir(parents=True)
        _touch(cfg.catalogs_nointro_dir / "Nintendo - Game Boy.dat", age_days=1)

        result = _build_dat_catalog_list(cfg)
        gb = next(s for s in result["systems"] if s["name"] == "Nintendo - Game Boy")
        assert gb["downloaded"] is True
        assert gb["age_days"] == 1
        assert gb["stale"] is False
        assert gb["mtime_iso"] is not None

    def test_stale_dat_marked_stale(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        cfg.catalogs_nointro_dir.mkdir(parents=True)
        _touch(cfg.catalogs_nointro_dir / "Nintendo - Game Boy.dat", age_days=_DAT_TTL_DAYS + 1)

        result = _build_dat_catalog_list(cfg)
        gb = next(s for s in result["systems"] if s["name"] == "Nintendo - Game Boy")
        assert gb["stale"] is True
        assert gb["age_days"] >= _DAT_TTL_DAYS

    def test_mtime_iso_format(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        cfg.catalogs_nointro_dir.mkdir(parents=True)
        _touch(cfg.catalogs_nointro_dir / "Nintendo - Game Boy.dat")

        result = _build_dat_catalog_list(cfg)
        gb = next(s for s in result["systems"] if s["name"] == "Nintendo - Game Boy")
        assert gb["mtime_iso"].endswith("Z")
        assert "T" in gb["mtime_iso"]

    def test_redump_dat_detected(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        cfg.catalogs_redump_dir.mkdir(parents=True)
        _touch(cfg.catalogs_redump_dir / "Sony - PlayStation.dat", age_days=2)

        result = _build_dat_catalog_list(cfg)
        ps = next(s for s in result["systems"] if s["name"] == "Sony - PlayStation")
        assert ps["downloaded"] is True
        assert ps["age_days"] == 2

    def test_missing_catalog_dirs_return_all_not_downloaded(self, tmp_path: Path) -> None:
        cfg = _make_config(tmp_path)
        # dirs don't exist
        result = _build_dat_catalog_list(cfg)
        assert all(not s["downloaded"] for s in result["systems"])


# ── _run_dat_download (TTL integration) ──────────────────────────────────────


class TestRunDatDownloadTtl:
    def _minimal_xml(self) -> bytes:
        return b"""\
<?xml version="1.0"?>
<datafile>
  <header><name>Test</name></header>
  <game name="Tetris">
    <rom name="Tetris.gb" size="32768" crc="46df91ad"
         md5="aabb" sha1="CCDD00112233445566778899AABBCCDD00112233"/>
  </game>
</datafile>
"""

    def _fake_urlopen(self, payload: bytes):
        resp = MagicMock()
        resp.read.return_value = payload
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    def _make_config(self, tmp_path: Path):
        cfg = MagicMock()
        cfg.catalogs_nointro_dir = tmp_path / "nointro"
        cfg.catalogs_redump_dir = tmp_path / "redump"
        return cfg

    def test_fresh_existing_dat_is_skipped(self, tmp_path: Path) -> None:
        from rom_manager.web.handlers.scan import _LIBRETRO_DAT_CATALOG, _run_dat_download

        cfg = self._make_config(tmp_path)
        cfg.catalogs_nointro_dir.mkdir(parents=True)
        entry = next(e for e in _LIBRETRO_DAT_CATALOG if e["catalog"] == "nointro")
        _touch(cfg.catalogs_nointro_dir / f"{entry['name']}.dat", age_days=1)

        jobs = JobManager()
        with patch("urllib.request.urlopen") as mock_open:
            _run_dat_download([entry], cfg, jobs)
            mock_open.assert_not_called()

        assert entry["name"] in jobs.get_job("download_dats")["result"]["skipped"]

    def test_stale_existing_dat_is_redownloaded(self, tmp_path: Path) -> None:
        from rom_manager.web.handlers.scan import _LIBRETRO_DAT_CATALOG, _run_dat_download

        cfg = self._make_config(tmp_path)
        cfg.catalogs_nointro_dir.mkdir(parents=True)
        entry = next(e for e in _LIBRETRO_DAT_CATALOG if e["catalog"] == "nointro")
        _touch(cfg.catalogs_nointro_dir / f"{entry['name']}.dat", age_days=_DAT_TTL_DAYS + 5)

        jobs = JobManager()
        with patch("urllib.request.urlopen", return_value=self._fake_urlopen(self._minimal_xml())):
            _run_dat_download([entry], cfg, jobs)

        assert entry["name"] in jobs.get_job("download_dats")["result"]["downloaded"]


# ── MAME listxml (catalog "mame_xml") ─────────────────────────────────────────


class TestMameListxmlEntry:
    def _cfg(self, tmp_path: Path):
        cfg = _make_config(tmp_path)
        cfg.catalogs_arcade_dir = tmp_path / "arcade"
        return cfg

    def test_detected_by_file_override(self, tmp_path: Path) -> None:
        cfg = self._cfg(tmp_path)
        _touch(cfg.catalogs_arcade_dir / "mame.xml", age_days=2)

        result = _build_dat_catalog_list(cfg)
        mx = next(s for s in result["systems"] if s["catalog"] == "mame_xml")
        assert mx["downloaded"] is True
        assert mx["age_days"] == 2

    def test_missing_xml_not_downloaded(self, tmp_path: Path) -> None:
        cfg = self._cfg(tmp_path)
        result = _build_dat_catalog_list(cfg)
        mx = next(s for s in result["systems"] if s["catalog"] == "mame_xml")
        assert mx["downloaded"] is False

    def test_download_resolves_release_and_extracts_zip(self, tmp_path: Path) -> None:
        import io
        import json
        import zipfile

        from rom_manager.web.handlers.scan import _LIBRETRO_DAT_CATALOG, _run_dat_download

        cfg = self._cfg(tmp_path)
        entry = next(e for e in _LIBRETRO_DAT_CATALOG if e["catalog"] == "mame_xml")
        xml = b'<?xml version="1.0"?><mame><machine name="neogeo" isbios="yes"/></mame>'
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("mame0288.xml", xml)
        api_json = json.dumps(
            {"assets": [{"name": "mame0288lx.zip", "browser_download_url": "https://x/lx.zip"}]}
        ).encode()

        def _resp(payload: bytes):
            resp = MagicMock()
            resp.read.return_value = payload
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        jobs = JobManager()
        with patch("urllib.request.urlopen", side_effect=[_resp(api_json), _resp(buf.getvalue())]):
            _run_dat_download([entry], cfg, jobs)

        result = jobs.get_job("download_dats")["result"]
        assert result["errors"] == []
        assert entry["name"] in result["downloaded"]
        assert (cfg.catalogs_arcade_dir / "mame.xml").read_bytes() == xml
