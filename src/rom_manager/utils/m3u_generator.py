from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Matches "Game Title (Disc 1)" or "Game Title (Disk 2)" etc.
_DISC_RE = re.compile(r"^(.+?)\s*\(Dis[ck]\s*(\d+)\)", re.IGNORECASE)


@dataclass(slots=True)
class DiscGroup:
    base_name: str
    discs: list[Path]   # sorted by disc number
    m3u_path: Path


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
        if not path.is_file():
            continue
        m = _DISC_RE.match(path.stem)
        if not m:
            continue
        base = m.group(1).strip()
        num = int(m.group(2))
        key = f"{path.parent}/{base}"
        buckets.setdefault(key, []).append((num, path))

    groups: list[DiscGroup] = []
    for key, entries in buckets.items():
        if len(entries) < 2:
            continue
        entries.sort(key=lambda x: x[0])
        base_name = entries[0][1].stem
        base_name = _DISC_RE.match(base_name).group(1).strip()  # type: ignore[union-attr]
        parent = entries[0][1].parent
        m3u_path = parent / f"{base_name}.m3u"
        groups.append(DiscGroup(
            base_name=base_name,
            discs=[p for _, p in entries],
            m3u_path=m3u_path,
        ))

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
