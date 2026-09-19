"""ANDROID-DUP-2: sha1_recursive/md5_recursive compute hashes on the device
itself (find … -exec {tool} {} +, one round trip) -- same shape as
ls_recursive, and must apply the same _descartados/hidden filtering plus
tolerate junk lines (find/stat errors, a tool's own warnings) mixed into
the output.
"""

from __future__ import annotations

from rom_manager.sync.adb_transport import AdbTransport


def _make_transport(monkeypatch, output: str) -> AdbTransport:
    transport = AdbTransport("adb.exe", "SERIAL123")
    monkeypatch.setattr(transport, "_shell", lambda *a, **kw: output)
    return transport


def test_sha1_recursive_parses_hash_and_path(monkeypatch) -> None:
    output = (
        "a1ff192436bcbfc73cb58e494976b0ea6cd45d16  /sdcard/roms/gb/game.gb\n"
        "FF22AE4CBE9BE068BAA5904000BD041F95E15B07  /sdcard/roms/gb/other.gb\n"
    )
    transport = _make_transport(monkeypatch, output)

    result = transport.sha1_recursive("/sdcard/roms")

    assert result == {
        "/sdcard/roms/gb/game.gb": "a1ff192436bcbfc73cb58e494976b0ea6cd45d16",
        "/sdcard/roms/gb/other.gb": "ff22ae4cbe9be068baa5904000bd041f95e15b07",
    }


def test_md5_recursive_parses_hash_and_path(monkeypatch) -> None:
    output = "d41d8cd98f00b204e9800998ecf8427e  /sdcard/roms/psx/game.chd\n"
    transport = _make_transport(monkeypatch, output)

    result = transport.md5_recursive("/sdcard/roms")

    assert result == {"/sdcard/roms/psx/game.chd": "d41d8cd98f00b204e9800998ecf8427e"}


def test_hash_recursive_skips_descartados_and_hidden(monkeypatch) -> None:
    """Same guard as ls_recursive (TRASH-FIX-2) -- a hash for a file already
    discarded, or a dotfile, must never end up in the map."""
    output = (
        "a" * 40
        + "  /sdcard/roms/psx/game.chd\n"
        + "b" * 40
        + "  /sdcard/roms/psx/_descartados/old.bin\n"
        + "c" * 40
        + "  /sdcard/roms/.hidden/junk.zip\n"
    )
    transport = _make_transport(monkeypatch, output)

    result = transport.sha1_recursive("/sdcard/roms")

    assert result == {"/sdcard/roms/psx/game.chd": "a" * 40}


def test_hash_recursive_ignores_malformed_lines(monkeypatch) -> None:
    """find/sha1sum error lines ("Permission denied", a bare filename with
    no hash) must be skipped, not crash the parse or leak a bogus entry."""
    output = (
        "find: /sdcard/roms/private: Permission denied\n"
        "not-a-valid-hash  /sdcard/roms/gb/weird.gb\n"
        "\n" + "d" * 40 + "  /sdcard/roms/gb/real.gb\n"
    )
    transport = _make_transport(monkeypatch, output)

    result = transport.sha1_recursive("/sdcard/roms")

    assert result == {"/sdcard/roms/gb/real.gb": "d" * 40}


def test_hash_recursive_handles_filenames_with_spaces(monkeypatch) -> None:
    output = "e" * 40 + "  /sdcard/roms/psx/Crash Bandicoot (USA).bin\n"
    transport = _make_transport(monkeypatch, output)

    result = transport.sha1_recursive("/sdcard/roms")

    assert result == {"/sdcard/roms/psx/Crash Bandicoot (USA).bin": "e" * 40}
