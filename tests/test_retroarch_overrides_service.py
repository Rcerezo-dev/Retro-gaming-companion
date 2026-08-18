from __future__ import annotations

from pathlib import Path

import pytest

from rom_manager.services.retroarch_overrides_service import (
    list_overrides,
    read_override,
    write_override,
)
from rom_manager.sync.adb_transport import AdbFileInfo, AdbTransport


class _FakeAdbTransport:
    def __init__(self, files: list[AdbFileInfo]) -> None:
        self._files = files

    def ls_recursive(self, android_path: str, *, wanted_extensions=None, **_kw):
        matches = [f for f in self._files if f.android_path.startswith(android_path)]
        if wanted_extensions is None:
            return matches
        return [f for f in matches if Path(f.android_path).suffix.lower() in wanted_extensions]


def test_empty_config_dir_returns_nothing() -> None:
    assert list_overrides("") == {}


def test_pc_nonexistent_dir_returns_nothing(tmp_path: Path) -> None:
    assert list_overrides(str(tmp_path / "does-not-exist")) == {}


def test_pc_finds_overrides_grouped_by_core(tmp_path: Path) -> None:
    (tmp_path / "Snes9x").mkdir()
    (tmp_path / "Snes9x" / "Super Mario World.opt").write_text("", encoding="utf-8")
    (tmp_path / "Gambatte").mkdir()
    (tmp_path / "Gambatte" / "Tetris.opt").write_text("", encoding="utf-8")
    # Non-.opt files in the same folders must be ignored.
    (tmp_path / "Snes9x" / "notes.txt").write_text("", encoding="utf-8")

    result = list_overrides(str(tmp_path))

    assert result == {
        "Super Mario World": ["Snes9x"],
        "Tetris": ["Gambatte"],
    }


def test_pc_same_stem_under_two_cores_lists_both(tmp_path: Path) -> None:
    (tmp_path / "Snes9x").mkdir()
    (tmp_path / "Snes9x" / "Chrono Trigger.opt").write_text("", encoding="utf-8")
    (tmp_path / "Snes9x 2010").mkdir()
    (tmp_path / "Snes9x 2010" / "Chrono Trigger.opt").write_text("", encoding="utf-8")

    result = list_overrides(str(tmp_path))

    assert sorted(result["Chrono Trigger"]) == ["Snes9x", "Snes9x 2010"]


def test_android_via_adb_transport() -> None:
    files = [
        AdbFileInfo(
            android_path="/storage/emulated/0/RetroArch/config/mGBA/Pokemon Emerald.opt",
            size=64,
            mtime=0.0,
        ),
        AdbFileInfo(
            android_path="/storage/emulated/0/RetroArch/config/mGBA/notes.cfg",
            size=10,
            mtime=0.0,
        ),
    ]
    transport = _FakeAdbTransport(files)

    result = list_overrides("/storage/emulated/0/RetroArch/config", adb_transport=transport)

    assert result == {"Pokemon Emerald": ["mGBA"]}


def test_pc_read_and_write_roundtrip(tmp_path: Path) -> None:
    (tmp_path / "Snes9x").mkdir()
    path = tmp_path / "Snes9x" / "Super Mario World.opt"
    path.write_text('foo = "bar"\n', encoding="utf-8")

    assert read_override(str(tmp_path), "Super Mario World", "Snes9x") == 'foo = "bar"\n'

    write_override(str(tmp_path), "Super Mario World", "Snes9x", "baz = 1\n")
    assert path.read_text(encoding="utf-8") == "baz = 1\n"


def test_pc_write_creates_missing_core_dir(tmp_path: Path) -> None:
    write_override(str(tmp_path), "Tetris", "Gambatte", "x = 1\n")
    assert (tmp_path / "Gambatte" / "Tetris.opt").read_text(encoding="utf-8") == "x = 1\n"


@pytest.mark.parametrize("bad", ["../escape", "..", ".", "a/b", "a\\b"])
def test_rejects_path_traversal_in_rom_and_core(tmp_path: Path, bad: str) -> None:
    with pytest.raises(ValueError):
        read_override(str(tmp_path), bad, "Snes9x")
    with pytest.raises(ValueError):
        write_override(str(tmp_path), "Tetris", bad, "x")


def test_android_read_and_write_via_adb(monkeypatch) -> None:
    store: dict[str, str] = {
        "/storage/emulated/0/RetroArch/config/mGBA/Pokemon Emerald.opt": "orig = 1\n"
    }

    def fake_pull(self, android_src, local_dst, *, dry_run=False, verify=False):
        local_dst.write_text(store[android_src], encoding="utf-8")
        return len(store[android_src])

    def fake_push(self, local_src, android_dst, *, dry_run=False, verify=False):
        store[android_dst] = local_src.read_text(encoding="utf-8")
        return local_src.stat().st_size

    monkeypatch.setattr(AdbTransport, "pull", fake_pull)
    monkeypatch.setattr(AdbTransport, "push", fake_push)
    transport = AdbTransport("adb", "ABC123")
    config_dir = "/storage/emulated/0/RetroArch/config"

    content = read_override(config_dir, "Pokemon Emerald", "mGBA", adb_transport=transport)
    assert content == "orig = 1\n"

    write_override(config_dir, "Pokemon Emerald", "mGBA", "new = 2\n", adb_transport=transport)
    assert store[f"{config_dir}/mGBA/Pokemon Emerald.opt"] == "new = 2\n"
