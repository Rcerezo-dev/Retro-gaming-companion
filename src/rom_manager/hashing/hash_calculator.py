from __future__ import annotations

import hashlib
import zlib
from dataclasses import dataclass
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


@dataclass(slots=True)
class FileHashes:
    sha1: str
    md5: str
    crc32: str


def calculate_hashes(path: Path) -> FileHashes:
    sha1 = hashlib.sha1()
    md5 = hashlib.md5()
    crc = 0

    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            sha1.update(chunk)
            md5.update(chunk)
            crc = zlib.crc32(chunk, crc) & 0xFFFFFFFF

    return FileHashes(
        sha1=sha1.hexdigest().upper(),
        md5=md5.hexdigest().upper(),
        crc32=f"{crc & 0xFFFFFFFF:08X}",
    )
