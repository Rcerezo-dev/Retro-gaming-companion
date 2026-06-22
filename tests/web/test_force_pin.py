"""PHASE5-1: refuse to start when exposed to the network without a PIN.

`serve()` does a lot (binds a socket, starts daemons), so we don't call it for
the happy paths — we only assert the *guard* at the top: it must raise
``InsecureExposureError`` before any of that when host != 127.0.0.1 and no PIN
is configured, unless ``allow_insecure`` is set.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.server import InsecureExposureError, serve


def _make(tmp_path: Path, *, pin: bool):
    config = load_config(tmp_path)
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    if pin:
        config.credentials.web_pin_hash = "deadbeef"
        config.credentials.web_pin_salt = "salt"
    return config, repo


def test_serve_refuses_network_exposure_without_pin(tmp_path: Path) -> None:
    config, repo = _make(tmp_path, pin=False)
    with pytest.raises(InsecureExposureError) as exc:
        serve(host="0.0.0.0", port=7777, repository=repo, config=config)
    # The message must point the user at the two ways forward.
    msg = str(exc.value)
    assert "PIN" in msg
    assert "--allow-insecure" in msg


def test_localhost_without_pin_is_allowed(tmp_path: Path, monkeypatch) -> None:
    config, repo = _make(tmp_path, pin=False)
    # Stop serve() right after the guard so we don't actually bind/run.
    sentinel = RuntimeError("reached startup")
    monkeypatch.setattr(
        "rom_manager.detection.platform_detector.reload_platforms",
        lambda *_a, **_k: (_ for _ in ()).throw(sentinel),
    )
    with pytest.raises(RuntimeError) as exc:
        serve(host="127.0.0.1", port=7777, repository=repo, config=config)
    assert exc.value is sentinel  # passed the guard, not blocked


def test_allow_insecure_bypasses_guard(tmp_path: Path, monkeypatch) -> None:
    config, repo = _make(tmp_path, pin=False)
    sentinel = RuntimeError("reached startup")
    monkeypatch.setattr(
        "rom_manager.detection.platform_detector.reload_platforms",
        lambda *_a, **_k: (_ for _ in ()).throw(sentinel),
    )
    with pytest.raises(RuntimeError) as exc:
        serve(
            host="0.0.0.0",
            port=7777,
            repository=repo,
            config=config,
            allow_insecure=True,
        )
    assert exc.value is sentinel  # warning path, not refusal


def test_network_exposure_with_pin_is_allowed(tmp_path: Path, monkeypatch) -> None:
    config, repo = _make(tmp_path, pin=True)
    sentinel = RuntimeError("reached startup")
    monkeypatch.setattr(
        "rom_manager.detection.platform_detector.reload_platforms",
        lambda *_a, **_k: (_ for _ in ()).throw(sentinel),
    )
    with pytest.raises(RuntimeError) as exc:
        serve(host="0.0.0.0", port=7777, repository=repo, config=config)
    assert exc.value is sentinel  # PIN set → guard passes
