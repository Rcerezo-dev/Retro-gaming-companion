"""SAVE-CONSOLIDATOR-1 — detect save fragmentation without touching anything.

Groups save files by normalized game name (ignoring the per-core/per-platform
folder that causes the fragmentation, and the extension, since a VBA Next
``.srm`` and an mGBA ``.sav`` for the same game are never hash-comparable —
see ``Tareas/Informe-SAVES-FRAGMENT-1.md``), flags boot-time blank templates by
content (uniform byte fill, not by "same hash repeated" — that heuristic false-
positived on a real Metal Gear Solid memcard in the report), and reports which
groups are safe to dedupe vs. which have real, divergent progress. It never
merges, deletes or picks a winner — same principle as the ROM duplicates
service: report, let a human decide.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# ponytail: only strips RetroArch's own " (1)" copy-suffix. Alternate ROM
# names for the same game ("Metroid Fusion [E]" vs "...(Europe)...") land in
# separate groups — add alias-aware normalization if that turns out to matter
# in practice (report puts it at ~20 pairs, all already same-hash so they are
# harmless "single" groups today, just not merged into one).
_COPY_SUFFIX_RE = re.compile(r"\s\(\d+\)$")


def _normalize_stem(stem: str) -> str:
    return _COPY_SUFFIX_RE.sub("", stem)


def _is_blank_fill(data: bytes) -> bool:
    """True if *data* is a uniform byte fill — the template a core writes on boot."""
    return not data or len(set(data)) == 1


@dataclass(slots=True)
class SaveEntry:
    absolute: Path
    relative: str  # path relative to the scanned root, forward slashes
    stem: str  # normalized game name used for grouping
    extension: str
    size: int
    mtime: datetime
    sha1: str
    is_blank: bool


@dataclass(slots=True)
class SaveGroup:
    """All save entries that normalize to the same game name.

    ``status``:
      - "single": one non-blank copy, nothing to consolidate.
      - "blank": every copy (one or more) is a boot-time template — safe to discard.
      - "identical": every non-blank copy has the same content — dedup is safe.
      - "divergent": non-blank copies disagree — real progress at risk, needs a
        human decision (mtime is deliberately not used to pick a winner: the
        report shows a core rewriting the blank template *after* the real save,
        which makes "newest wins" pick the empty copy).
    """

    stem: str
    entries: list[SaveEntry]

    @property
    def status(self) -> str:
        non_blank = [e for e in self.entries if not e.is_blank]
        if not non_blank:
            return "blank"
        if len(self.entries) <= 1:
            return "single"
        if len({e.sha1 for e in non_blank}) == 1:
            return "identical"
        return "divergent"


def scan_save_groups(root: Path, save_extensions: tuple[str, ...]) -> list[SaveGroup]:
    """Walk *root* and group every save file under it by normalized game name.

    Pass a curated *battery-save-only* extension list, not the project-wide
    aggregate ``config.save_extensions`` — that superset also carries
    savestate-as-a-file extensions (``.ml1``, ``.hi``, ``.nv``) used by some
    cores/platforms, and merging those into the same group as a real ``.sav``
    reports a false "divergent" (different content by design, not fragmented
    progress). Validated 2026-08-27 against the real SAVES-FRAGMENT-1 RG556
    inventory: with the real battery-save extensions this reproduces the
    report's 8 divergent groups exactly (Earthbound, Mcd001.ps2, 5x GBA); the
    project-wide aggregate list adds ~9 false positives on top (NDS .ml1 vs
    .sav, arcade .hi vs .nv) — a known ceiling of stem-only grouping, not a
    bug here. Scan ``saves/`` and ``states/`` as two separate roots too.
    """
    ext_set = {e.lower() for e in save_extensions}
    by_stem: dict[str, list[SaveEntry]] = {}

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in ext_set:
            continue
        stat = path.stat()
        data = path.read_bytes()
        entry = SaveEntry(
            absolute=path,
            relative=path.relative_to(root).as_posix(),
            stem=_normalize_stem(path.stem),
            extension=path.suffix.lower(),
            size=stat.st_size,
            mtime=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            sha1=hashlib.sha1(data).hexdigest().upper(),
            is_blank=_is_blank_fill(data),
        )
        by_stem.setdefault(entry.stem, []).append(entry)

    return [
        SaveGroup(stem=stem, entries=sorted(entries, key=lambda e: e.relative))
        for stem, entries in sorted(by_stem.items())
    ]
