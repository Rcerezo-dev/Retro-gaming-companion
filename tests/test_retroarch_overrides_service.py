from __future__ import annotations

from pathlib import Path

import pytest

from rom_manager.services.retroarch_overrides_service import (
    copy_override,
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


def test_copy_rejects_non_shared_core(tmp_path: Path) -> None:
    src = tmp_path / "pc"
    (src / "Snes9x").mkdir(parents=True)
    (src / "Snes9x" / "Chrono Trigger.opt").write_text("x = 1\n", encoding="utf-8")
    dest = tmp_path / "android"

    with pytest.raises(ValueError):
        copy_override(
            "Chrono Trigger",
            "Snes9x",
            source_config_dir=str(src),
            source_adb_transport=None,
            dest_config_dir=str(dest),
            dest_adb_transport=None,
        )
    assert not (dest / "Snes9x").exists()


def test_copy_creates_override_with_no_backup_when_destination_empty(tmp_path: Path) -> None:
    src = tmp_path / "pc"
    (src / "Gambatte").mkdir(parents=True)
    (src / "Gambatte" / "Tetris.opt").write_text("x = 1\n", encoding="utf-8")
    dest = tmp_path / "android"

    result = copy_override(
        "Tetris",
        "Gambatte",
        source_config_dir=str(src),
        source_adb_transport=None,
        dest_config_dir=str(dest),
        dest_adb_transport=None,
    )

    assert result == {"backed_up": False, "backup_filename": None}
    assert (dest / "Gambatte" / "Tetris.opt").read_text(encoding="utf-8") == "x = 1\n"


def test_copy_backs_up_existing_destination_before_overwrite(tmp_path: Path) -> None:
    src = tmp_path / "pc"
    (src / "Gambatte").mkdir(parents=True)
    (src / "Gambatte" / "Tetris.opt").write_text("new = 2\n", encoding="utf-8")
    dest = tmp_path / "android"
    (dest / "Gambatte").mkdir(parents=True)
    (dest / "Gambatte" / "Tetris.opt").write_text("old = 1\n", encoding="utf-8")

    result = copy_override(
        "Tetris",
        "Gambatte",
        source_config_dir=str(src),
        source_adb_transport=None,
        dest_config_dir=str(dest),
        dest_adb_transport=None,
    )

    assert result["backed_up"] is True
    backup_path = dest / "Gambatte" / result["backup_filename"]
    assert backup_path.read_text(encoding="utf-8") == "old = 1\n"
    assert (dest / "Gambatte" / "Tetris.opt").read_text(encoding="utf-8") == "new = 2\n"


def test_copy_android_to_pc_via_adb(tmp_path: Path, monkeypatch) -> None:
    store = {"/storage/emulated/0/RetroArch/config/mGBA/Pokemon Emerald.opt": "src = 1\n"}

    def fake_pull(self, android_src, local_dst, *, dry_run=False, verify=False):
        local_dst.write_text(store[android_src], encoding="utf-8")
        return len(store[android_src])

    monkeypatch.setattr(AdbTransport, "pull", fake_pull)
    transport = AdbTransport("adb", "ABC123")
    dest = tmp_path / "pc"

    result = copy_override(
        "Pokemon Emerald",
        "mGBA",
        source_config_dir="/storage/emulated/0/RetroArch/config",
        source_adb_transport=transport,
        dest_config_dir=str(dest),
        dest_adb_transport=None,
    )

    assert result == {"backed_up": False, "backup_filename": None}
    assert (dest / "mGBA" / "Pokemon Emerald.opt").read_text(encoding="utf-8") == "src = 1\n"
