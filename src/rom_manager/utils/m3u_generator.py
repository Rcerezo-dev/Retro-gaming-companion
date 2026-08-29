from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Matches "Game Title (Disc 1)" or "Game Title (Disk 2)", optionally followed by
# another tag such as "(Rev 1)" or "(v1.1)" — PSX-ORPHAN-3: the old \s*$ anchor
# required "(Disc N)" to be the last thing in the filename, so a set like
# "Game (Disc 1) (Rev 1).cue" / "Game (Disc 2) (Rev 1).cue" was never grouped at all.
_DISC_RE = re.compile(r"^(.+?)\s*\(Dis[ck]\s*(\d+)\)\s*(.*)$", re.IGNORECASE)
# A "(Track N)" tag means this is one track of a single disc, not a separate disc —
# matching it as a disc would misreport multi-track PSX rips as missing discs.
_TRACK_TAG_RE = re.compile(r"^\(Track\s*\d+\)", re.IGNORECASE)

# Extensions that can legitimately be part of a multi-disc set: raw/compressed
# disc images, cue/gdi sheets and their sidecars. PSX-ORPHAN-3: without this
# filter, any file sharing the "(Disc N)" naming — a save, a savestate, cover
# art — was grouped as if it were a disc (real case: a stray .srm produced a
# false "Metal Gear Solid (USA)" multi-disc group).
_DISC_SET_EXTS = frozenset(
    {
        ".bin",
        ".img",
        ".iso",
        ".chd",
        ".gdi",
        ".pbp",
        ".ecm",
        ".cue",
        ".ccd",
        ".sub",
        ".mds",
        ".mdf",
        ".sbi",
    }
)


def _parse_disc(stem: str) -> tuple[str, int] | None:
    """Return (base_name, disc_number) if *stem* names one disc of a set, else None."""
    m = _DISC_RE.match(stem)
    if not m:
        return None
    before, num, after = m.group(1).strip(), int(m.group(2)), m.group(3).strip()
    if after and _TRACK_TAG_RE.match(after):
        return None
    base = f"{before} {after}".strip() if after else before
    return base, num


@dataclass(slots=True)
class DiscGroup:
    base_name: str
    discs: list[Path]  # sorted by disc number
    m3u_path: Path
    platform: str = ""  # parent folder name (e.g. "psx", "saturn")


@dataclass(slots=True)
class M3USummary:
    created: int = 0
    skipped: int = 0
    groups: list[DiscGroup] = field(default_factory=list)


def find_disc_groups(directory: Path) -> list[DiscGroup]:
    """Scan *directory* recursively and return groups of multi-disc files."""
    # Map base_name -> list[(disc_number, path)]
    buckets: dict[str, list[tuple[int, Path]]] = {}

    for path in directory.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _DISC_SET_EXTS:
            continue
        parsed = _parse_disc(path.stem)
        if not parsed:
            continue
        base, num = parsed
        key = f"{path.parent}/{base}"
        buckets.setdefault(key, []).append((num, path))

    groups: list[DiscGroup] = []
    for key, entries in buckets.items():
        if len(entries) < 2:
            continue
        entries.sort(key=lambda x: x[0])
        base_name, _num = _parse_disc(entries[0][1].stem)  # type: ignore[misc]
        parent = entries[0][1].parent
        m3u_path = parent / f"{base_name}.m3u"
        groups.append(
            DiscGroup(
                base_name=base_name,
                discs=[p for _, p in entries],
                m3u_path=m3u_path,
                platform=parent.name,
            )
        )

    return sorted(groups, key=lambda g: g.base_name)


def write_m3u(group: DiscGroup, *, dry_run: bool = True) -> bool:
    """Write the .m3u file for *group*. Returns True if created, False if skipped."""
    if group.m3u_path.exists():
        return False
    if dry_run:
        return True
    lines = [disc.name + "\n" for disc in group.discs]
    group.m3u_path.write_text("".join(lines), encoding="utf-8")
    return True


def generate_m3u_playlists(directory: Path, *, dry_run: bool = True) -> M3USummary:
    """Generate .m3u playlist files for all multi-disc groups under *directory*."""
    summary = M3USummary()
    for group in find_disc_groups(directory):
        summary.groups.append(group)
        created = write_m3u(group, dry_run=dry_run)
        if created:
            summary.created += 1
        else:
            summary.skipped += 1
    return summary
