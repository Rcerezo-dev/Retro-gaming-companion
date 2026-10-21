"""DUP-CHD-RAW-1a: rawsha1 de la cabecera CHD v5 (parser, lectura por ADB y caché)."""

from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace

from rom_manager.retroachievements.ra_disc_hash_cache import (
    get_cached_chd_raw_sha1,
    load_chd_raw_cache,
    refresh_chd_raw_sha1_cache,
)
from rom_manager.sync.adb_transport import AdbTransport
from rom_manager.sync.chd_header import chd_v5_raw_sha1, read_chd_raw_sha1

RAW_A = bytes(range(20))
RAW_B = bytes(range(1, 21))


def chd_header(raw: bytes = RAW_A, *, version: int = 5, tag: bytes = b"MComprHD") -> bytes:
    h = bytearray(124)
    h[0:8] = tag
    h[8:12] = (124).to_bytes(4, "big")
    h[12:16] = version.to_bytes(4, "big")
    h[64:84] = raw
    return bytes(h)


def test_parses_raw_sha1_of_v5_header() -> None:
    assert chd_v5_raw_sha1(chd_header(RAW_A)) == RAW_A.hex()


def test_rejects_other_versions_bad_tag_short_or_empty_hash() -> None:
    assert chd_v5_raw_sha1(chd_header(version=4)) is None
    assert chd_v5_raw_sha1(chd_header(tag=b"NotAChd!")) is None
    assert chd_v5_raw_sha1(chd_header()[:100]) is None
    assert chd_v5_raw_sha1(chd_header(bytes(20))) is None


def test_read_chd_raw_sha1_from_local_file(tmp_path: Path) -> None:
    f = tmp_path / "a.chd"
    f.write_bytes(chd_header(RAW_B) + b"payload")
    assert read_chd_raw_sha1(f) == RAW_B.hex()
    assert read_chd_raw_sha1(tmp_path / "missing.chd") is None


def test_transport_reads_header_with_quoted_path() -> None:
    calls: list[tuple] = []

    def fake_run(*args, timeout=None):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout=chd_header(RAW_A))

    t = AdbTransport("adb", "SERIAL")
    t._run = fake_run  # type: ignore[method-assign]

    assert t.chd_raw_sha1("/storage/x/Tony Hawk's (USA).chd") == RAW_A.hex()
    assert calls[0][0] == "exec-out"
    assert "head -c 124 " in calls[0][1]
    assert "'\"'\"'" in calls[0][1]  # la comilla simple del nombre va escapada para la shell


def test_transport_returns_none_when_adb_fails() -> None:
    t = AdbTransport("adb", "SERIAL")
    t._run = lambda *a, timeout=None: SimpleNamespace(returncode=1, stdout=b"")  # type: ignore[method-assign]
    assert t.chd_raw_sha1("/storage/x/a.chd") is None


class _CountingTransport:
    def __init__(self, raws: dict[str, str | None]):
        self.raws = raws
        self.calls: list[str] = []

    def chd_raw_sha1(self, path: str) -> str | None:
        self.calls.append(path)
        return self.raws.get(path)


def test_refresh_reads_only_new_or_changed_files(tmp_path: Path) -> None:
    transport = _CountingTransport({"/d/a.chd": "aa", "/d/b.chd": "bb"})
    files = [("/d/a.chd", 100), ("/d/b.chd", 200)]

    stats = refresh_chd_raw_sha1_cache(files, tmp_path, transport)
    assert stats == {"read": 2, "cached": 0, "unreadable": 0}

    transport.calls.clear()
    stats = refresh_chd_raw_sha1_cache(files, tmp_path, transport)
    assert stats == {"read": 0, "cached": 2, "unreadable": 0}
    assert transport.calls == []

    # b.chd se reemplazó (otro tamaño) -> se vuelve a leer solo ese
    refresh_chd_raw_sha1_cache([("/d/a.chd", 100), ("/d/b.chd", 201)], tmp_path, transport)
    assert transport.calls == ["/d/b.chd"]


def test_refresh_remembers_unreadable_files_and_honours_cancel(tmp_path: Path) -> None:
    transport = _CountingTransport({"/d/bad.chd": None})
    stats = refresh_chd_raw_sha1_cache([("/d/bad.chd", 5)], tmp_path, transport)
    assert stats["unreadable"] == 1
    refresh_chd_raw_sha1_cache([("/d/bad.chd", 5)], tmp_path, transport)
    assert transport.calls == ["/d/bad.chd"]  # el fallo cacheado no se reintenta

    cancel = threading.Event()
    cancel.set()
    transport2 = _CountingTransport({"/d/c.chd": "cc"})
    refresh_chd_raw_sha1_cache([("/d/c.chd", 1)], tmp_path / "other", transport2, cancel=cancel)
    assert transport2.calls == []


def test_get_cached_requires_matching_size(tmp_path: Path) -> None:
    transport = _CountingTransport({"/d/a.chd": "aa"})
    refresh_chd_raw_sha1_cache([("/d/a.chd", 100)], tmp_path, transport)
    cache = load_chd_raw_cache(tmp_path)

    assert get_cached_chd_raw_sha1("/d/a.chd", 100, cache) == "aa"
    assert get_cached_chd_raw_sha1("/d/a.chd", 999, cache) is None
    assert get_cached_chd_raw_sha1("/d/other.chd", 100, cache) is None
