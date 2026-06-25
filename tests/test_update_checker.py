"""Tests for PHASE6-3a: update_checker module."""

from __future__ import annotations

import json
import threading
from unittest.mock import MagicMock, patch

import pytest

from rom_manager.utils import update_checker as _uc


def _reset() -> None:
    """Reset module-level state between tests."""
    with _uc._lock:
        _uc._result.clear()
        _uc._check_started = False


@pytest.fixture(autouse=True)
def reset_state():
    _reset()
    yield
    _reset()


def _fake_urlopen(payload: dict):
    body = json.dumps(payload).encode()
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ── _parse_version ────────────────────────────────────────────────────────────


class TestParseVersion:
    def test_plain_semver(self) -> None:
        assert _uc._parse_version("1.2.3") == (1, 2, 3)

    def test_v_prefix(self) -> None:
        assert _uc._parse_version("v0.2.0") == (0, 2, 0)

    def test_capital_v(self) -> None:
        assert _uc._parse_version("V1.0.0") == (1, 0, 0)

    def test_invalid_falls_back(self) -> None:
        assert _uc._parse_version("not-a-version") == (0,)


# ── _do_check ────────────────────────────────────────────────────────────────


class TestDoCheck:
    def test_update_available(self) -> None:
        payload = {
            "tag_name": "v0.2.0",
            "html_url": "https://github.com/x/y/releases/tag/v0.2.0",
            "name": "v0.2.0",
        }
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(payload)):
            _uc._do_check("0.1.0")

        r = _uc.get_result()
        assert r["update_available"] is True
        assert r["latest"] == "0.2.0"
        assert r["release_url"] == payload["html_url"]
        assert r["checked"] is True
        assert r["error"] is None

    def test_no_update_when_already_latest(self) -> None:
        payload = {"tag_name": "v0.1.0", "html_url": "https://example.com", "name": "v0.1.0"}
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(payload)):
            _uc._do_check("0.1.0")

        assert _uc.get_result()["update_available"] is False

    def test_older_release_not_flagged(self) -> None:
        payload = {"tag_name": "v0.0.9", "html_url": "https://example.com", "name": "old"}
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(payload)):
            _uc._do_check("0.1.0")

        assert _uc.get_result()["update_available"] is False

    def test_network_error_graceful(self) -> None:
        import urllib.error

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            _uc._do_check("0.1.0")

        r = _uc.get_result()
        assert r["checked"] is True
        assert r["update_available"] is False
        assert r["error"] is not None

    def test_missing_tag_graceful(self) -> None:
        payload = {"tag_name": "", "html_url": "", "name": ""}
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(payload)):
            _uc._do_check("0.1.0")

        r = _uc.get_result()
        assert r["checked"] is True
        assert r["update_available"] is False

    def test_patch_update_detected(self) -> None:
        payload = {"tag_name": "v0.1.1", "html_url": "https://example.com", "name": "patch"}
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(payload)):
            _uc._do_check("0.1.0")

        assert _uc.get_result()["update_available"] is True

    def test_assets_are_captured(self) -> None:
        payload = {
            "tag_name": "v0.2.0",
            "html_url": "https://example.com",
            "name": "v0.2.0",
            "assets": [
                {
                    "name": "RetroVault-Setup.exe",
                    "browser_download_url": "https://x/Setup.exe",
                    "size": 123,
                },
            ],
        }
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(payload)):
            _uc._do_check("0.1.0")

        assets = _uc.get_result()["assets"]
        assert assets == [
            {"name": "RetroVault-Setup.exe", "url": "https://x/Setup.exe", "size": 123}
        ]


# ── get_result / start_background_check ──────────────────────────────────────


class TestGetResult:
    def test_empty_before_check(self) -> None:
        assert _uc.get_result() == {}

    def test_returns_copy(self) -> None:
        """Mutating the returned dict must not affect the internal state."""
        payload = {"tag_name": "v1.0.0", "html_url": "", "name": "v1.0.0"}
        with patch("urllib.request.urlopen", return_value=_fake_urlopen(payload)):
            _uc._do_check("0.1.0")

        r = _uc.get_result()
        r["update_available"] = False
        assert _uc.get_result()["update_available"] is True


class TestStartBackgroundCheck:
    def test_fires_only_once(self) -> None:
        threads_started = []

        original_thread = threading.Thread

        def counting_thread(*args, **kwargs):
            t = original_thread(*args, **kwargs)
            threads_started.append(t)
            return t

        with patch("threading.Thread", side_effect=counting_thread):
            _uc.start_background_check("0.1.0")
            _uc.start_background_check("0.1.0")
            _uc.start_background_check("0.1.0")

        assert len(threads_started) == 1
