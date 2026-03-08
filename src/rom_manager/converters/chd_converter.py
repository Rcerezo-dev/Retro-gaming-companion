from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ConversionResult:
    cue_path: Path
    chd_path: Path
    bin_paths: list[Path]
    success: bool
    error: str | None = None


@dataclass(slots=True)
class ConversionSummary:
    converted: int = 0
    skipped: int = 0
    failed: int = 0
    results: list[ConversionResult] = field(default_factory=list)


def find_cue_files(directory: Path) -> list[Path]:
    """Return all .cue files under directory, sorted."""
    return sorted(directory.rglob("*.cue"))


def parse_bins_from_cue(cue_path: Path) -> list[Path]:
    """Return existing .bin files referenced inside a .cue file."""
    cue_dir = cue_path.parent
    bins: list[Path] = []
    try:
        text = cue_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return bins
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.upper().startswith("FILE "):
            continue
        parts = stripped.split('"')
        if len(parts) < 2:
            continue
        candidate = cue_dir / parts[1]
        if candidate.exists():
            bins.append(candidate)
    return bins


def convert_to_chd(
    cue_path: Path,
    *,
    chdman: str = "chdman",
    delete_source: bool = False,
) -> ConversionResult:
    """Convert a .cue set to a single .chd file using chdman.

    Args:
        cue_path: Path to the .cue file.
        chdman: Path or name of the chdman binary.
        delete_source: If True and conversion succeeded, delete the .cue and
            all referenced .bin files.
    """
    chd_path = cue_path.with_suffix(".chd")
    bin_paths = parse_bins_from_cue(cue_path)

    if chd_path.exists():
        return ConversionResult(
            cue_path=cue_path,
            chd_path=chd_path,
            bin_paths=bin_paths,
            success=False,
            error="Output .chd already exists — skipping to avoid overwrite.",
        )

    try:
        subprocess.run(
            [chdman, "createcd", "-i", str(cue_path), "-o", str(chd_path)],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        return ConversionResult(
            cue_path=cue_path,
            chd_path=chd_path,
            bin_paths=bin_paths,
            success=False,
            error=f"chdman binary not found: {chdman!r}",
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="replace").strip()
        return ConversionResult(
            cue_path=cue_path,
            chd_path=chd_path,
            bin_paths=bin_paths,
            success=False,
            error=stderr or f"chdman exited with code {exc.returncode}",
        )

    if delete_source:
        for bin_path in bin_paths:
            bin_path.unlink(missing_ok=True)
        cue_path.unlink(missing_ok=True)

    return ConversionResult(
        cue_path=cue_path,
        chd_path=chd_path,
        bin_paths=bin_paths,
        success=True,
    )


def convert_directory(
    directory: Path,
    *,
    chdman: str = "chdman",
    delete_source: bool = False,
    dry_run: bool = True,
) -> ConversionSummary:
    """Convert all .cue files in a directory tree.

    In dry_run mode (the default) no files are touched — only a summary is returned.
    """
    summary = ConversionSummary()
    cue_files = find_cue_files(directory)

    for cue_path in cue_files:
        chd_path = cue_path.with_suffix(".chd")
        bin_paths = parse_bins_from_cue(cue_path)

        if dry_run:
            if chd_path.exists():
                result = ConversionResult(
                    cue_path=cue_path,
                    chd_path=chd_path,
                    bin_paths=bin_paths,
                    success=False,
                    error="Output .chd already exists — would skip.",
                )
                summary.skipped += 1
            else:
                result = ConversionResult(
                    cue_path=cue_path,
                    chd_path=chd_path,
                    bin_paths=bin_paths,
                    success=True,
                )
                summary.converted += 1
            summary.results.append(result)
            continue

        result = convert_to_chd(cue_path, chdman=chdman, delete_source=delete_source)
        summary.results.append(result)
        if result.success:
            summary.converted += 1
        elif result.error and "already exists" in result.error:
            summary.skipped += 1
        else:
            summary.failed += 1

    return summary
