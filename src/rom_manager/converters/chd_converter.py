from __future__ import annotations

import re
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


@dataclass(slots=True)
class VerifyResult:
    chd_path: Path
    ok: bool
    error: str | None = None


def verify_chd(chd_path: Path, *, chdman: str = "chdman") -> VerifyResult:
    """Run ``chdman verify -i <file>`` and return whether the CHD is intact."""
    try:
        proc = subprocess.run(
            [chdman, "verify", "-i", str(chd_path)],
            capture_output=True,
            timeout=120,
        )
        if proc.returncode == 0:
            return VerifyResult(chd_path=chd_path, ok=True)
        stderr = proc.stderr.decode(errors="replace").strip()
        stdout = proc.stdout.decode(errors="replace").strip()
        return VerifyResult(
            chd_path=chd_path, ok=False, error=stderr or stdout or f"exit {proc.returncode}"
        )
    except FileNotFoundError:
        return VerifyResult(chd_path=chd_path, ok=False, error=f"chdman no encontrado: {chdman!r}")
    except subprocess.TimeoutExpired:
        return VerifyResult(chd_path=chd_path, ok=False, error="Timeout al verificar CHD (>120 s)")
    except Exception as exc:
        return VerifyResult(chd_path=chd_path, ok=False, error=str(exc))


def find_chd_files(directory: Path) -> list[Path]:
    """Return all .chd files under directory, sorted."""
    return sorted(directory.rglob("*.chd"))


def find_cue_files(directory: Path) -> list[Path]:
    """Return all .cue files under directory, sorted."""
    return sorted(directory.rglob("*.cue"))


def parse_bins_from_cue(cue_path: Path) -> list[Path]:
    """Return all files referenced inside a .cue file (existing or not).

    Handles both quoted (FILE "name.bin" BINARY) and unquoted (FILE name.bin BINARY) forms.
    """
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
        # Quoted filename: FILE "some name.bin" BINARY
        m = re.match(r'FILE\s+"([^"]+)"', stripped, re.IGNORECASE)
        if m:
            bins.append(cue_dir / m.group(1))
            continue
        # Unquoted filename: FILE name.bin BINARY
        m = re.match(r"FILE\s+(\S+)", stripped, re.IGNORECASE)
        if m:
            bins.append(cue_dir / m.group(1))
    return bins


def parse_tracks_from_gdi(gdi_path: Path) -> list[Path]:
    """Return all track files referenced inside a Dreamcast .gdi file.

    GDI format: first line is track count, then one track per line:
      <track_num> <offset> <type> <sectorsize> <filename> <unknown>
    """
    gdi_dir = gdi_path.parent
    tracks: list[Path] = []
    try:
        text = gdi_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return tracks
    lines = text.splitlines()
    for line in lines[1:]:  # skip first line (track count)
        parts = line.strip().split()
        if len(parts) >= 5:
            tracks.append(gdi_dir / parts[4])
    return tracks


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
        # B2-2: if delete_source is requested and the .chd already exists from a
        # previous successful conversion, clean up the originals now.
        if delete_source:
            for bin_path in bin_paths:
                bin_path.unlink(missing_ok=True)
            cue_path.unlink(missing_ok=True)
            return ConversionResult(
                cue_path=cue_path,
                chd_path=chd_path,
                bin_paths=bin_paths,
                success=True,
                error=None,
            )
        return ConversionResult(
            cue_path=cue_path,
            chd_path=chd_path,
            bin_paths=bin_paths,
            success=False,
            error="Output .chd already exists — skipping to avoid overwrite.",
        )

    # B2-3: pre-validate all referenced bins exist before calling chdman
    missing = [b for b in bin_paths if not b.exists()]
    if missing:
        return ConversionResult(
            cue_path=cue_path,
            chd_path=chd_path,
            bin_paths=bin_paths,
            success=False,
            error=f"Bin file(s) not found: {', '.join(b.name for b in missing)}",
        )

    try:
        subprocess.run(
            [chdman, "createcd", "-i", str(cue_path), "-o", str(chd_path)],
            check=True,
            capture_output=True,
            cwd=str(cue_path.parent),  # B2-1: resolve relative .bin paths in .cue correctly
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

    # B5-2: post-conversion validation — chdman can exit 0 and still produce no output
    if not chd_path.exists() or chd_path.stat().st_size == 0:
        if chd_path.exists():
            chd_path.unlink(missing_ok=True)  # remove empty/corrupt file
        return ConversionResult(
            cue_path=cue_path,
            chd_path=chd_path,
            bin_paths=bin_paths,
            success=False,
            error="chdman terminó sin error pero el .chd resultante falta o está vacío",
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
