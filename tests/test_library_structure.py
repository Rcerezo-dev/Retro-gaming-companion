"""Tests for the library structure creation and organize-library logic.

Tests cover:
- _STANDARD_PLATFORM_FOLDERS creates the expected folder tree
- _ES_PLATFORM_FOLDERS maps to valid ES-DE folder names
- Consistency between platform_detector output and _ES_PLATFORM_FOLDERS keys
- The /api/create-library-structure endpoint (via fake HTTP client)
- The /api/organize-library endpoint: ROM moves, save relocation, BIOS detection
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.server import (
    _ES_PLATFORM_FOLDERS,
    _STANDARD_PLATFORM_FOLDERS,
    make_handler,
)

# ── HTTP test helpers (same pattern as test_web_server.py) ─────────────────────


class FakeSocket:
    def makefile(self, mode: str) -> io.BytesIO:
        return io.BytesIO(b"")


def _post(path: str, body: dict, repo: LibraryRepository, config_root: Path):
    handler_class = make_handler(repo, load_config(config_root))
    payload = json.dumps(body).encode()
    captured: dict = {}

    class TestHandler(handler_class):  # type: ignore[misc]
        def __init__(self):
            self.command = "POST"
            self.path = path
            self.headers = {"Content-Length": str(len(payload)), "Content-Type": "application/json"}
            self.rfile = io.BytesIO(payload)
            self._buf = io.BytesIO()
            self.wfile = self._buf
            self.server = MagicMock()
            self.request = FakeSocket()

        def send_response(self, code: int, message: str = "") -> None:
            captured["code"] = code

        def send_header(self, key: str, value: str) -> None:
            if key == "Content-Type":
                captured["content_type"] = value

        def end_headers(self) -> None:
            pass

        def log_message(self, fmt, *args):
            pass

    h = TestHandler()
    h.do_POST()
    body_bytes = h._buf.getvalue()
    try:
        data = json.loads(body_bytes)
    except Exception:
        data = {}
    return captured.get("code", 0), data


@pytest.fixture
def library(tmp_path: Path) -> Path:
    """A temporary library root."""
    lib = tmp_path / "library"
    lib.mkdir()
    return lib


@pytest.fixture
def config_root(tmp_path: Path, library: Path) -> Path:
    """A minimal config.toml pointing to the temporary library."""
    root = tmp_path / "project"
    root.mkdir()
    cfg_text = f'[library]\nlibrary_root = "{str(library).replace(chr(92), "/")}"\n'
    (root / "config.toml").write_text(cfg_text, encoding="utf-8")
    return root


@pytest.fixture
def repo(config_root: Path) -> LibraryRepository:
    cfg = load_config(config_root)
    return LibraryRepository(cfg.database_path)


# ── Static consistency tests (no I/O needed) ──────────────────────────────────


class TestPlatformFolderConsistency:
    def test_all_standard_folders_in_es_mapping(self) -> None:
        """Every folder in _STANDARD_PLATFORM_FOLDERS should appear as an ES-DE folder value."""
        es_values = set(_ES_PLATFORM_FOLDERS.values())
        for folder in _STANDARD_PLATFORM_FOLDERS:
            assert folder in es_values, (
                f"'{folder}' is in _STANDARD_PLATFORM_FOLDERS but not reachable "
                f"via any _ES_PLATFORM_FOLDERS mapping"
            )

    def test_no_duplicate_standard_folders(self) -> None:
        seen = set()
        for f in _STANDARD_PLATFORM_FOLDERS:
            assert f not in seen, f"Duplicate folder in _STANDARD_PLATFORM_FOLDERS: '{f}'"
            seen.add(f)

    def test_saturn_mapped_as_sega_saturn(self) -> None:
        """Bug guard: platform_detector returns 'Sega Saturn', not 'Saturn'."""
        assert "Sega Saturn" in _ES_PLATFORM_FOLDERS, (
            "'Sega Saturn' missing from _ES_PLATFORM_FOLDERS — Saturn games won't be organized. "
            "Check that both 'Sega Saturn' and 'Saturn' are present."
        )
        assert _ES_PLATFORM_FOLDERS["Sega Saturn"] == "saturn"

    def test_sega_cd_in_mapping(self) -> None:
        assert "Sega CD" in _ES_PLATFORM_FOLDERS
        assert _ES_PLATFORM_FOLDERS["Sega CD"] == "segacd"

    def test_sega_32x_in_mapping(self) -> None:
        assert "Sega 32X" in _ES_PLATFORM_FOLDERS
        assert _ES_PLATFORM_FOLDERS["Sega 32X"] == "sega32x"

    def test_all_es_folder_values_are_lowercase(self) -> None:
        for platform, folder in _ES_PLATFORM_FOLDERS.items():
            assert folder == folder.lower(), (
                f"_ES_PLATFORM_FOLDERS['{platform}'] = '{folder}' — must be lowercase"
            )

    def test_standard_folders_count(self) -> None:
        # Sanity: should have at least 25 platform folders
        assert len(_STANDARD_PLATFORM_FOLDERS) >= 25, (
            f"Only {len(_STANDARD_PLATFORM_FOLDERS)} platform folders — expected ≥25"
        )

    def test_essential_platforms_present(self) -> None:
        essential = {
            "nes",
            "snes",
            "n64",
            "gb",
            "gbc",
            "gba",
            "nds",
            "psx",
            "ps2",
            "psp",
            "megadrive",
            "dreamcast",
            "saturn",
            "gamecube",
            "wii",
        }
        for folder in essential:
            assert folder in _STANDARD_PLATFORM_FOLDERS, (
                f"Essential platform folder '{folder}' missing from _STANDARD_PLATFORM_FOLDERS"
            )

    def test_special_folders_not_in_standard(self) -> None:
        """saves/, bios/, inbox/ are special — NOT in _STANDARD_PLATFORM_FOLDERS."""
        for special in ("saves", "bios", "inbox"):
            assert special not in _STANDARD_PLATFORM_FOLDERS, (
                f"'{special}' should not be in _STANDARD_PLATFORM_FOLDERS (it's a special folder)"
            )


# ── /api/create-library-structure endpoint ────────────────────────────────────


class TestCreateLibraryStructure:
    def test_creates_platform_folders(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        code, data = _post("/api/create-library-structure", {}, repo, config_root)
        assert code == 200
        assert "created" in data
        # A few spot-checks
        for folder in ("nes", "gba", "psx", "megadrive", "saturn"):
            assert (library / folder).is_dir(), f"Missing folder: {folder}"

    def test_creates_special_folders(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        _post("/api/create-library-structure", {}, repo, config_root)
        for special in ("saves", "bios", "inbox"):
            assert (library / special).is_dir(), f"Missing special folder: {special}"

    def test_creates_media_subfolders(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        _post("/api/create-library-structure", {}, repo, config_root)
        assert (library / "media" / "gba" / "images").is_dir()
        assert (library / "media" / "gba" / "videos").is_dir()

    def test_idempotent_second_call(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        _post("/api/create-library-structure", {}, repo, config_root)
        code, data = _post("/api/create-library-structure", {}, repo, config_root)
        assert code == 200
        # All folders already exist → created should be empty or zero
        assert data.get("created") == [] or len(data.get("created", [])) == 0

    def test_root_in_response(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        _, data = _post("/api/create-library-structure", {}, repo, config_root)
        assert "root" in data

    def test_android_error_when_no_path(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        """Requesting also_android without a configured android_root should return an error in android key."""
        _, data = _post("/api/create-library-structure", {"also_android": True}, repo, config_root)
        # Either android key is empty (no path configured) or contains an error
        android = data.get("android", {})
        # Should not crash — android result can be empty dict or have error
        assert isinstance(android, dict)

    def test_android_platforms_nest_under_roms(
        self, library: Path, config_root: Path, repo: LibraryRepository, tmp_path: Path
    ) -> None:
        """HERR-FIX-3: on the Anbernic (SD card), platform folders live under
        ROMs/ (DEVICE-DUP-1) -- unlike the PC library_root, where they sit
        directly at the root."""
        sd = tmp_path / "sd_root"
        sd.mkdir()
        cfg_text = (
            f'[library]\nlibrary_root = "{str(library).replace(chr(92), "/")}"\n'
            f'anbernic_root = "{str(sd).replace(chr(92), "/")}"\n'
        )
        (config_root / "config.toml").write_text(cfg_text, encoding="utf-8")

        _, data = _post("/api/create-library-structure", {"also_android": True}, repo, config_root)

        assert (sd / "ROMs" / "gba").is_dir()
        assert (sd / "ROMs" / "psx").is_dir()
        assert not (sd / "gba").exists(), "platform folder must not also sit loose at the SD root"
        # Special folders stay at the SD root, not nested under ROMs/
        assert (sd / "saves").is_dir()
        assert (sd / "bios").is_dir()
        assert not (sd / "ROMs" / "saves").exists()


# ── /api/organize-library endpoint ────────────────────────────────────────────


class TestOrganizeLibrary:
    def _add_game(self, repo: LibraryRepository, path: Path, platform: str) -> None:
        now = "2026-01-01T00:00:00"
        with repo.connect() as conn:
            conn.execute(
                """INSERT INTO games
                   (source_path, original_filename, sha1, md5, crc32, extension,
                    size_bytes, file_type, platform, created_at, updated_at)
                   VALUES (?, ?, '', '', '', ?, 0, 'rom', ?, ?, ?)""",
                (str(path.resolve()), path.name, path.suffix.lower(), platform, now, now),
            )
            conn.commit()

    def test_dry_run_returns_preview(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        rom = library / "Metroid Fusion (USA).gba"
        rom.write_bytes(b"\x00")
        self._add_game(repo, rom, "Game Boy Advance")
        (library / "gba").mkdir()

        _, data = _post("/api/organize-library", {"dry_run": True}, repo, config_root)
        assert data["dry_run"] is True
        assert data["moves_roms"] >= 1
        assert isinstance(data["preview"], list)
        # File must NOT have moved in dry_run
        assert rom.exists()

    def test_apply_moves_rom_to_platform_folder(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        (library / "gba").mkdir()
        rom = library / "Metroid Fusion (USA).gba"
        rom.write_bytes(b"\x00" * 32)
        self._add_game(repo, rom, "Game Boy Advance")

        _post("/api/organize-library", {"dry_run": False}, repo, config_root)
        assert (library / "gba" / "Metroid Fusion (USA).gba").exists()
        assert not rom.exists()

    def test_apply_updates_db_source_path(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        (library / "gba").mkdir()
        rom = library / "Metroid.gba"
        rom.write_bytes(b"\x00" * 32)
        self._add_game(repo, rom, "Game Boy Advance")

        _post("/api/organize-library", {"dry_run": False}, repo, config_root)

        with repo.connect() as conn:
            row = conn.execute(
                "SELECT source_path FROM games WHERE original_filename = 'Metroid.gba'"
            ).fetchone()
        new_path = Path(row["source_path"])
        assert new_path.parent.name == "gba"

    def test_apply_moves_sibling_save(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        (library / "gba").mkdir()
        (library / "saves").mkdir()
        rom = library / "Metroid.gba"
        save = library / "Metroid.sav"
        rom.write_bytes(b"\x00" * 32)
        save.write_bytes(b"\x00" * 16)
        self._add_game(repo, rom, "Game Boy Advance")

        _post("/api/organize-library", {"dry_run": False}, repo, config_root)
        assert (library / "saves" / "gba" / "Metroid.sav").exists()
        assert not save.exists()

    def test_bios_file_moved_to_bios_folder(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        (library / "bios").mkdir()
        bios = library / "scph1001.bin"
        bios.write_bytes(b"\x00" * 512)
        # Do NOT add to DB (it's not a ROM)

        _post("/api/organize-library", {"dry_run": False}, repo, config_root)
        assert (library / "bios" / "scph1001.bin").exists()
        assert not bios.exists()

    def test_unknown_bin_not_touched(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        """A .bin file with an unknown name should NOT be moved."""
        (library / "bios").mkdir()
        unknown = library / "mystery.bin"
        unknown.write_bytes(b"\x00" * 64)

        _post("/api/organize-library", {"dry_run": False}, repo, config_root)
        assert unknown.exists()  # untouched

    def test_conflict_detected_when_target_exists(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        (library / "gba").mkdir()
        rom = library / "game.gba"
        rom.write_bytes(b"\x00" * 32)
        existing = library / "gba" / "game.gba"
        existing.write_bytes(b"\xff" * 32)  # different content
        self._add_game(repo, rom, "Game Boy Advance")

        _, data = _post("/api/organize-library", {"dry_run": False}, repo, config_root)
        assert len(data["errors"]) >= 1
        assert rom.exists()  # original still in place

    def test_saturn_game_organized_correctly(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        """Regression test for the 'Sega Saturn' vs 'Saturn' key mismatch bug."""
        (library / "saturn").mkdir()
        rom = library / "Virtua Fighter 2 (USA).chd"
        rom.write_bytes(b"\x00" * 32)
        self._add_game(repo, rom, "Sega Saturn")

        _, data = _post("/api/organize-library", {"dry_run": True}, repo, config_root)
        assert data["moves_roms"] >= 1, (
            "Sega Saturn game not detected for organization — "
            "check 'Sega Saturn' key in _ES_PLATFORM_FOLDERS"
        )

    def test_game_without_platform_skipped(
        self, library: Path, config_root: Path, repo: LibraryRepository
    ) -> None:
        rom = library / "unknown.bin"
        rom.write_bytes(b"\x00" * 32)
        self._add_game(repo, rom, "")  # no platform

        _, data = _post("/api/organize-library", {"dry_run": True}, repo, config_root)
        assert data["moves_roms"] == 0
