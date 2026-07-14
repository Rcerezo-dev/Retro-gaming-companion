"""ANBERNIC-UX-1/3/4: generador canónico /s y token efímero de setup."""

from __future__ import annotations

import time
from types import SimpleNamespace

import rom_manager.web.state as _state
from rom_manager.web.handlers.sync_cloud import (
    _build_bootstrap_script,
    _mint_setup_token,
    _setup_token_ok,
)


def _ctx(client_ip: str, token: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        client_address=(client_ip, 12345),
        _qs={"t": [token]} if token else {},
    )


def test_loopback_always_allowed() -> None:
    _state._anbernic_setup_token = {"value": None, "expires": 0.0}
    assert _setup_token_ok(_ctx("127.0.0.1"))


def test_lan_without_token_denied() -> None:
    _state._anbernic_setup_token = {"value": None, "expires": 0.0}
    assert not _setup_token_ok(_ctx("192.168.1.50"))


def test_lan_with_valid_token_allowed() -> None:
    token = _mint_setup_token()
    assert _setup_token_ok(_ctx("192.168.1.50", token))


def test_lan_with_wrong_or_expired_token_denied() -> None:
    token = _mint_setup_token()
    assert not _setup_token_ok(_ctx("192.168.1.50", "wrong"))
    _state._anbernic_setup_token["expires"] = time.time() - 1
    assert not _setup_token_ok(_ctx("192.168.1.50", token))


def test_bootstrap_script_uses_config_remotes_and_token() -> None:
    config = SimpleNamespace(
        sync=SimpleNamespace(
            rclone_remote="",
            saves_remote="gdrive:/RetroSync/saves",
            states_remote="gdrive:/RetroSync/states",
        )
    )
    script = _build_bootstrap_script("http://10.0.0.2:7777", config, "tok123")
    assert 'SAVES_REMOTE="gdrive:/RetroSync/saves"' in script
    assert 'STATES_REMOTE="gdrive:/RetroSync/states"' in script
    assert "rclone-export-config?t=$TOKEN" in script
    assert 'TOKEN="tok123"' in script
    # Crea el script que documenta la pestaña, con copy --update (no bisync)
    assert "retrovault-sync.sh" in script
    assert "bisync" not in script
    # Sin IP personal hardcodeada (ANBERNIC-UX-4)
    assert "192.168.1.160" not in script


def test_bootstrap_script_falls_back_to_legacy_remote() -> None:
    config = SimpleNamespace(
        sync=SimpleNamespace(rclone_remote="dropbox:/RetroSync", saves_remote="", states_remote="")
    )
    script = _build_bootstrap_script("http://10.0.0.2:7777", config, "t")
    assert 'SAVES_REMOTE="dropbox:/RetroSync/saves"' in script
    assert 'STATES_REMOTE="dropbox:/RetroSync/states"' in script
