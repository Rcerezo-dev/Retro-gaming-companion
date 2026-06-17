"""Content-hash delta cache for save sync (S37-2).

Stores the SHA1 of the last successfully-synced version of each save file.
Before uploading, we compare the current content hash with the cached one;
if they match the file content is genuinely unchanged (even if mtime differs)
and the upload can be skipped.

Typical scenario this prevents:
  - Emulator opens a .srm / .sav in write mode, updates internal timestamp but
    does not actually write new game data → mtime changes, content stays identical.
  - Without delta cache: unnecessary upload every sync cycle.
  - With delta cache:    recognised as unchanged, skipped.

Cache file: <data_dir>/delta_sync_cache.json
Format:
    {
      "relative/path/to/save.srm": {
          "hash": "<sha1>",
          "synced_at": "2026-01-01T12:00:00Z",
          "direction": "upload" | "download"
      },
      ...
    }
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

log = logging.getLogger(__name__)

_CACHE_FILE = "delta_sync_cache.json"
_CHUNK = 65536  # 64 KB read chunks for SHA1


def _sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while chunk := f.read(_CHUNK):
            h.update(chunk)
    return h.hexdigest()


class DeltaCache:
    """Persist the last-synced content hash for each save file.

    Thread-safety: designed for single-threaded use within one sync job.
    Writes are flushed to disk after every mutation.
    """

    def __init__(self, data_dir: Path) -> None:
        self._path = data_dir / _CACHE_FILE
        self._data: dict[str, dict] = self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def content_changed(self, relative: str, local_path: Path) -> bool:
        """Return True if the file content differs from the last-synced hash.

        Returns True (= needs sync) when:
        - No cache entry exists yet (first sync)
        - File cannot be read
        - Hash differs from cached value
        """
        entry = self._data.get(relative)
        if not entry:
            return True
        try:
            current = _sha1_file(local_path)
            changed = current != entry["hash"]
            if not changed:
                log.debug("delta cache: %s unchanged (SHA1 %s)", relative, current[:8])
            return changed
        except OSError as exc:
            log.warning("delta cache: cannot hash %s: %s", local_path.name, exc)
            return True  # assume changed if we can't read the file

    def mark_synced(self, relative: str, local_path: Path, direction: str) -> None:
        """Record the current content hash as successfully synced."""
        try:
            h = _sha1_file(local_path)
        except OSError as exc:
            log.warning("delta cache: cannot hash %s after sync: %s", local_path.name, exc)
            return
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._data[relative] = {"hash": h, "synced_at": now, "direction": direction}
        self._flush()

    def invalidate(self, relative: str) -> None:
        """Remove cache entry (use after a conflict so next sync re-evaluates)."""
        if relative in self._data:
            del self._data[relative]
            self._flush()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> dict[str, dict]:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            log.warning("delta cache: corrupt cache file %s, resetting", self._path)
            return {}

    def _flush(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        except OSError as exc:
            log.warning("delta cache: could not write cache: %s", exc)
