from __future__ import annotations

import hashlib
import logging
import os
import threading
import zlib
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

CHUNK_SIZE = 1024 * 1024

_logger = logging.getLogger(__name__)


class HashingCancelled(Exception):
    """Raised when hashing is interrupted because *stop_event* became set."""


@dataclass(slots=True)
class FileHashes:
    sha1: str
    md5: str
    crc32: str


def calculate_hashes(path: Path, *, stop_event: threading.Event | None = None) -> FileHashes:
    """Compute SHA1, MD5 and CRC32 of *path* in a single streamed pass.

    If *stop_event* is provided and becomes set, the read loop aborts at the
    next chunk boundary (≤ ``CHUNK_SIZE`` bytes) by raising ``HashingCancelled``,
    so a scan of a multi-GB file can be cancelled responsively instead of
    blocking until the whole file has been read.
    """
    sha1 = hashlib.sha1()
    md5 = hashlib.md5()
    crc = 0

    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            if stop_event is not None and stop_event.is_set():
                raise HashingCancelled(str(path))
            sha1.update(chunk)
            md5.update(chunk)
            crc = zlib.crc32(chunk, crc) & 0xFFFFFFFF

    return FileHashes(
        sha1=sha1.hexdigest().upper(),
        md5=md5.hexdigest().upper(),
        crc32=f"{crc & 0xFFFFFFFF:08X}",
    )


def _default_workers() -> int:
    return min(8, os.cpu_count() or 2)


def calculate_hashes_batch(
    paths: Sequence[Path],
    *,
    stop_event: threading.Event | None = None,
    max_workers: int | None = None,
) -> dict[Path, FileHashes]:
    """Hash several files concurrently and return ``{path: FileHashes}``.

    ``hashlib`` releases the GIL while updating digests, so a thread pool yields
    real parallelism on multi-core machines for the (CPU-bound) hashing of large
    ROMs. Files that are cancelled via *stop_event* or fail with ``OSError`` are
    omitted from the result — the caller decides how to treat an absence
    (cancellation vs. read error, distinguishable by checking *stop_event*).
    """
    results: dict[Path, FileHashes] = {}
    if not paths or (stop_event is not None and stop_event.is_set()):
        return results

    workers = max_workers if max_workers is not None else _default_workers()
    workers = max(1, min(workers, len(paths)))

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="hash") as pool:
        futures = {pool.submit(calculate_hashes, p, stop_event=stop_event): p for p in paths}
        for future in as_completed(futures):
            path = futures[future]
            try:
                results[path] = future.result()
            except HashingCancelled:
                continue
            except OSError:
                _logger.warning("Failed to hash %s", path, exc_info=True)
    return results
