from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rom_manager.utils.m3u_generator import find_disc_groups


@dataclass(slots=True)
class DiscIssue:
    base_name: str
    issue_type: str   # "gap" | "mixed_ext" | "missing_file" | "unmatched"
    detail: str


@dataclass(slots=True)
class MultidiscSummary:
    groups_ok: int = 0
    groups_with_issues: int = 0
    issues: list[DiscIssue] = field(default_factory=list)


def verify_multidisc(
    directory: Path,
    repository=None,  # LibraryRepository | None
) -> MultidiscSummary:
    """Verify all multi-disc groups under *directory*.

    Checks:
    - All disc numbers are consecutive (no gaps)
    - All discs share the same file extension
    - All disc files exist on disk
    - All discs are matched in the catalog (if repository provided)
    """
    from rom_manager.utils.m3u_generator import _DISC_RE  # noqa: PLC0415

    summary = MultidiscSummary()

    for group in find_disc_groups(directory):
        group_issues: list[DiscIssue] = []

        # Check all files exist
        for disc in group.discs:
            if not disc.exists():
                group_issues.append(DiscIssue(
                    base_name=group.base_name,
                    issue_type="missing_file",
                    detail=f"Archivo no encontrado: {disc.name}",
                ))

        # Check extension homogeneity
        extensions = {d.suffix.lower() for d in group.discs}
        if len(extensions) > 1:
            group_issues.append(DiscIssue(
                base_name=group.base_name,
                issue_type="mixed_ext",
                detail=f"Extensiones mezcladas: {', '.join(sorted(extensions))}",
            ))

        # Check consecutive disc numbers
        import re
        disc_numbers = []
        for disc in group.discs:
            m = _DISC_RE.match(disc.stem)
            if m:
                disc_numbers.append(int(m.group(2)))
        disc_numbers.sort()
        expected = list(range(disc_numbers[0], disc_numbers[0] + len(disc_numbers)))
        if disc_numbers != expected:
            missing_nums = sorted(set(expected) - set(disc_numbers))
            group_issues.append(DiscIssue(
                base_name=group.base_name,
                issue_type="gap",
                detail=f"Discos faltantes: {missing_nums}",
            ))

        # Check catalog match
        if repository is not None:
            unmatched = []
            matched_games = {g.source_path for g in repository.get_matched_games()}
            for disc in group.discs:
                if str(disc.resolve()) not in matched_games:
                    unmatched.append(disc.name)
            if unmatched:
                group_issues.append(DiscIssue(
                    base_name=group.base_name,
                    issue_type="unmatched",
                    detail=f"Sin match en catálogo: {', '.join(unmatched)}",
                ))

        if group_issues:
            summary.groups_with_issues += 1
            summary.issues.extend(group_issues)
        else:
            summary.groups_ok += 1

    return summary
