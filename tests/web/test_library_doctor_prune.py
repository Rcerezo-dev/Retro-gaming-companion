"""PRUNE-INCOMPLETE-1: Library Doctor con contexto PC / consola (ADB) y «retirar incompletos»."""

from __future__ import annotations

from pathlib import Path

from rom_manager.sync.adb_transport import AdbFileInfo


def _good_chd() -> bytes:
    h = bytearray(124)
    h[:8] = b"MComprHD"
    h[8:12] = (124).to_bytes(4, "big")
    h[12:16] = (5).to_bytes(4, "big")
    h[32:40] = (1000).to_bytes(8, "big")
    h[40:48] = (200).to_bytes(8, "big")
    h[48:56] = (300).to_bytes(8, "big")
    return bytes(h).ljust(600, bytes(1))


GOOD_CHD = _good_chd()


def _cue(*names: str) -> str:
    return "\n".join(f'FILE "{n}" BINARY\n  TRACK 01 MODE2/2352' for n in names)


def _make_pc_library(root: Path) -> None:
    psx = root / "psx"
    psx.mkdir(parents=True)
    (psx / "Lost (Europe).cue").write_text(_cue("Lost (Europe) (Track 1).bin"))
    (psx / "Fine (USA).chd").write_bytes(GOOD_CHD)
    (psx / "Stray (Track 9).bin").write_bytes(b"x" * 10)


class FakeTransport:
    """Consola en memoria con la superficie de AdbTransport que usa AdbLibraryFS."""

    def __init__(self, files: dict[str, str]):
        self.files = dict(files)
        self.discarded: list[str] = []

    def ls_recursive(self, android_path: str, **_kw):
        return [AdbFileInfo(p, len(t), 0.0) for p, t in self.files.items()]

    def read_text(self, android_path: str, **_kw) -> str:
        return self.files[android_path]

    def read_head(self, android_path: str, n: int, **_kw) -> bytes:
        return GOOD_CHD[:n]

    def discard(self, android_path: str) -> str:
        self.discarded.append(android_path)
        del self.files[android_path]
        return android_path


def test_pc_context_lists_lost_game_and_orphans_without_touching_disk(client, config):
    _make_pc_library(config.library_root)

    data = client.get_json("/api/library-doctor")

    types = {i["type"] for i in data["issues"]}
    assert {"lost_game", "orphan_tracks"} <= types
    assert data["removable"] == 2
    assert (config.library_root / "psx" / "Stray (Track 9).bin").exists()


def test_pc_prune_discards_and_returns_report(client, config):
    _make_pc_library(config.library_root)

    data = client.post_json("/api/library-doctor/prune-incomplete", {"context": "pc"})

    psx = config.library_root / "psx"
    assert data["discarded"] == 2 and "Lost (Europe).cue" in data["report"]
    assert not (psx / "Stray (Track 9).bin").exists()
    assert (psx / "_descartados" / "Stray (Track 9).bin").exists()
    assert (psx / "Fine (USA).chd").exists()  # el juego que funciona no se toca


def test_android_context_uses_adb_listing_and_discards_on_device(client, monkeypatch):
    root = "/storage/X/ROMs"
    fake = FakeTransport(
        {
            f"{root}/psx/Lost (Europe).cue": _cue("Lost (Europe) (Track 1).bin"),
            f"{root}/psx/Good (USA).chd": "x" * 600,
        }
    )
    monkeypatch.setattr(
        "rom_manager.sync.adb_transport.resolve_single_device_transport", lambda _adb: fake
    )

    seen = client.get_json(f"/api/library-doctor?context=android&root={root}")
    assert [i["type"] for i in seen["issues"]] == ["lost_game"]

    done = client.post_json(
        "/api/library-doctor/prune-incomplete", {"context": "android", "root": root}
    )
    assert done["discarded"] == 1
    assert fake.discarded == [f"{root}/psx/Lost (Europe).cue"]
    assert f"{root}/psx/Good (USA).chd" in fake.files


def test_android_without_device_reports_it_instead_of_scanning_the_pc(client, monkeypatch):
    monkeypatch.setattr(
        "rom_manager.sync.adb_transport.resolve_single_device_transport", lambda _adb: None
    )

    data = client.get_json("/api/library-doctor?context=android&root=/storage/X/ROMs")

    assert "Consola no disponible" in data["error"]


def test_android_without_root_reports_missing_path(client):
    data = client.get_json("/api/library-doctor?context=android")

    assert "Sin ruta de la consola" in data["error"]
