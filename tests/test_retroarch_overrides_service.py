from __future__ import annotations

from pathlib import Path

from rom_manager.services.retroarch_overrides_service import list_overrides
from rom_manager.sync.adb_transport import AdbFileInfo


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
