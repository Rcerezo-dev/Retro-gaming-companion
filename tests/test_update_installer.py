"""Tests for PHASE6-3b: update_installer module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from rom_manager.utils import update_installer as _ui

# ── find_update_asset ───────────────────────────────────────────────────────────


class TestFindUpdateAsset:
    def test_no_assets_returns_none(self) -> None:
        assert _ui.find_update_asset([]) is None

    def test_no_exe_returns_none(self) -> None:
        assets = [{"name": "source.zip", "url": "https://x/source.zip"}]
        assert _ui.find_update_asset(assets) is None

    def test_prefers_setup_exe(self) -> None:
        assets = [
            {"name": "RetroVault-portable.exe", "url": "https://x/a.exe"},
            {"name": "RetroVault-Setup.exe", "url": "https://x/b.exe"},
        ]
        assert _ui.find_update_asset(assets)["name"] == "RetroVault-Setup.exe"

    def test_falls_back_to_any_exe(self) -> None:
        assets = [{"name": "RetroVault-portable.exe", "url": "https://x/a.exe"}]
        assert _ui.find_update_asset(assets)["name"] == "RetroVault-portable.exe"


# ── download_update ──────────────────────────────────────────────────────────────


def _fake_response(body: bytes, total: int | None = None):
    resp = MagicMock()
    chunks = [body[i : i + 4] for i in range(0, len(body), 4)] + [b""]
    resp.read.side_effect = chunks
    resp.headers = {"Content-Length": str(total if total is not None else len(body))}
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestDownloadUpdate:
    def test_writes_file_and_reports_progress(self, tmp_path: Path) -> None:
        body = b"x" * 20
        progress_calls = []
        with patch("urllib.request.urlopen", return_value=_fake_response(body)):
            dest = _ui.download_update(
                "https://x/file.exe",
                tmp_path,
                "file.exe",
                on_progress=lambda done, total: progress_calls.append((done, total)),
            )
        assert dest == tmp_path / "file.exe"
        assert dest.read_bytes() == body
        assert progress_calls[-1] == (20, 20)
        assert not dest.with_name("file.exe.part").exists()

    def test_creates_dest_dir(self, tmp_path: Path) -> None:
        target_dir = tmp_path / "updates"
        with patch("urllib.request.urlopen", return_value=_fake_response(b"abcd")):
            _ui.download_update("https://x/file.exe", target_dir, "file.exe")
        assert (target_dir / "file.exe").exists()


# ── is_frozen / launch_installer ─────────────────────────────────────────────────


class TestIsFrozen:
    def test_false_when_not_frozen(self) -> None:
        assert _ui.is_frozen() is False

    def test_true_when_frozen_attr_set(self) -> None:
        import sys

        with patch.object(sys, "frozen", True, create=True):
            assert _ui.is_frozen() is True


class TestLaunchInstaller:
    def test_launches_detached_process(self, tmp_path: Path) -> None:
        installer = tmp_path / "Setup.exe"
        installer.write_bytes(b"")
        with patch("subprocess.Popen") as popen:
            _ui.launch_installer(installer)
        popen.assert_called_once()
        assert popen.call_args[0][0] == [str(installer)]
