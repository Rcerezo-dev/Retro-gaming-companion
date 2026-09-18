"""INBOX-ANBERNIC-1: checkbox opt-in para enviar lo recién organizado del
Inbox a la Anbernic por ADB. Cubre los dos caminos decididos en el roadmap
17 (Paso 3): dispositivo conectado (mock) -> se envía; sin dispositivo ->
aviso, nunca una excepción que tumbe el resto del job de Inbox."""

from __future__ import annotations

import logging
from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.inbox_pipeline import _send_organized_to_anbernic

_logger = logging.getLogger(__name__)


def _make_config(tmp_path: Path) -> object:
    cfg = load_config()
    cfg.project_root = tmp_path
    cfg.library_root = tmp_path / "library"
    cfg.sync.auto_sync_android_path = "/storage/emulated/0/RetroArch"
    cfg.save_extensions = (".sav",)
    return cfg


class _FakeTransport:
    def __init__(self) -> None:
        self.pushed: list[tuple[Path, str, bool]] = []

    def push(self, local_src: Path, android_dst: str, *, dry_run: bool, verify: bool) -> int:
        self.pushed.append((local_src, android_dst, verify))
        return local_src.stat().st_size


def test_sends_organized_files_when_device_connected(tmp_path, monkeypatch) -> None:
    target_root = tmp_path / "library"
    dest = target_root / "Game Boy" / "Tetris (USA).gb"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"rom data")

    fake_transport = _FakeTransport()
    monkeypatch.setattr(
        "rom_manager.sync.adb_transport.resolve_single_device_transport",
        lambda adb_path: fake_transport,
    )

    cfg = _make_config(tmp_path)
    repo = LibraryRepository(tmp_path / "lib.sqlite")

    result = _send_organized_to_anbernic(
        [dest], target_root, frozenset(cfg.save_extensions), repo, cfg, _logger
    )

    assert result == {"sent": 1, "errors": [], "warning": None}
    assert len(fake_transport.pushed) == 1
    local_src, android_dst, verify = fake_transport.pushed[0]
    assert local_src == dest
    # "Game Boy" (nombre de carpeta en el PC) -> "gb" (slug canónico Android),
    # misma traducción que usa send_selected en sync_cable.py.
    assert android_dst == "/storage/emulated/0/RetroArch/gb/Tetris (USA).gb"
    assert verify is False  # ROM, no save extension -> no MD5 verify (CABLE-UX-9e)


def test_warns_without_blocking_when_no_device(tmp_path, monkeypatch) -> None:
    target_root = tmp_path / "library"
    dest = target_root / "Game Boy" / "Tetris (USA).gb"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"rom data")

    monkeypatch.setattr(
        "rom_manager.sync.adb_transport.resolve_single_device_transport",
        lambda adb_path: None,
    )

    cfg = _make_config(tmp_path)
    repo = LibraryRepository(tmp_path / "lib.sqlite")

    result = _send_organized_to_anbernic(
        [dest], target_root, frozenset(cfg.save_extensions), repo, cfg, _logger
    )

    assert result["sent"] == 0
    assert result["errors"] == []
    assert result["warning"] == "sin dispositivo Anbernic conectado — organizado solo en el PC"


def test_no_organized_files_is_a_noop(tmp_path, monkeypatch) -> None:
    called = False

    def _boom(_adb_path):
        nonlocal called
        called = True
        raise AssertionError("no debería resolver dispositivo si no hay nada que enviar")

    monkeypatch.setattr("rom_manager.sync.adb_transport.resolve_single_device_transport", _boom)

    cfg = _make_config(tmp_path)
    repo = LibraryRepository(tmp_path / "lib.sqlite")

    result = _send_organized_to_anbernic(
        [], tmp_path / "library", frozenset(cfg.save_extensions), repo, cfg, _logger
    )

    assert result == {"sent": 0, "errors": [], "warning": None}
    assert called is False


def test_push_failure_is_captured_per_file_not_raised(tmp_path, monkeypatch) -> None:
    target_root = tmp_path / "library"
    dest = target_root / "Game Boy" / "Tetris (USA).gb"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"rom data")

    class _BoomTransport:
        def push(self, *args, **kwargs):
            raise OSError("adb push falló: device offline")

    monkeypatch.setattr(
        "rom_manager.sync.adb_transport.resolve_single_device_transport",
        lambda adb_path: _BoomTransport(),
    )

    cfg = _make_config(tmp_path)
    repo = LibraryRepository(tmp_path / "lib.sqlite")

    result = _send_organized_to_anbernic(
        [dest], target_root, frozenset(cfg.save_extensions), repo, cfg, _logger
    )

    assert result["sent"] == 0
    assert len(result["errors"]) == 1
    assert "Tetris (USA).gb" in result["errors"][0]
