from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath

from rom_manager.hashing.hash_calculator import calculate_hashes
from rom_manager.retroachievements.ra_hash_psx import compute_psx_ra_hash, detect_bin_cue_mode
from rom_manager.utils.trash import TRASH_DIR_NAME


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

    Only the *basename* of the referenced token is trusted -- real .cue
    files found in this library can carry a stale absolute path from
    whatever tool ripped them originally (e.g. ``FILE "C:\\CRASH 2.BIN"
    BINARY``), which would otherwise resolve to that literal (nonexistent)
    path instead of the sibling file that's actually next to the .cue.
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
            bins.append(cue_dir / PureWindowsPath(m.group(1)).name)
            continue
        # Unquoted filename: FILE name.bin BINARY
        m = re.match(r"FILE\s+(\S+)", stripped, re.IGNORECASE)
        if m:
            bins.append(cue_dir / PureWindowsPath(m.group(1)).name)
    return bins


def find_pre_migration_orphan_cues(directory: Path) -> list[Path]:
    """Return ``.cue`` files sitting loose next to an already-migrated
    subfolder of the same game (``Game.cue`` next to ``Game/``).

    REPAIR-TOOL-2: after a subfolder-per-game migration
    (``operation_planner.py:_DISC_SUBFOLDER_PLATFORMS``), a `.cue` left behind
    at the old flat location is residue from before the migration, not a
    second "set" — 17 of 31 "sets rotos" audited by hand in one real session
    were exactly this, inflating any health-check that treats a loose `.cue`
    as broken.
    """
    return [cue for cue in find_cue_files(directory) if (cue.parent / cue.stem).is_dir()]


def is_broken_cue_set(cue_path: Path) -> bool:
    """True if *cue_path* is missing, or references a ``.bin`` missing from
    disk.

    Shared primitive behind REPAIR-TOOL-4
    (``web/builders/duplicates.py::_is_broken_disc_entry``) and DISC-HEALTH-1
    (``utils/health_checker.py::check_disc_set_health``) -- one definition of
    "broken" for both the duplicate-resolution tiebreak and the standalone
    health report.
    """
    if not cue_path.exists():
        return True
    return any(not b.exists() for b in parse_bins_from_cue(cue_path))


def _unclaimed_bins(directory: Path) -> list[Path]:
    """.bin files under *directory* not referenced by any .cue there, and
    not inside a ``_descartados/`` trash folder -- a file already discarded
    should never come back as a "recoverable" bare bin."""
    claimed: set[Path] = set()
    for cue in find_cue_files(directory):
        claimed.update(parse_bins_from_cue(cue))
    return [
        f
        for f in sorted(directory.rglob("*.bin"))
        if f not in claimed and TRASH_DIR_NAME not in f.parts
    ]


def find_bare_bin_files(directory: Path) -> list[Path]:
    """Return .bin files under *directory* not referenced by any .cue there
    -- the common shape in this library, where most PS1 dumps are
    single-track raw rips with no sidecar .cue at all. Only bins with a
    real, readable PS1 filesystem are returned (``detect_bin_cue_mode`` +
    an actual RA hash computed successfully) -- an orphan audio-track .bin
    left over from some other multi-track set has no filesystem and is
    silently excluded here, never guessed at.
    """
    return [
        f
        for f in _unclaimed_bins(directory)
        if detect_bin_cue_mode(f) is not None and compute_psx_ra_hash(f) is not None
    ]


def bin_size_is_sector_aligned(size_bytes: int) -> bool:
    """True if *size_bytes* is an exact multiple of a standard CD sector size
    (2352 raw, 2048 Mode 1 payload).

    REPAIR-TOOL-6: one-line check done by hand to triage loose `.bin` files
    during `PSX-STRUCTURE-2`/session repairs, worth exposing instead of
    re-deriving every time. `find_bins_needing_cue()` already requires a
    *detected* geometry (2352/2048/2336, see `_CUE_MODE_BY_GEOMETRY`), so this
    mostly flags the rarer MODE2/2336 case as non-standard for extra scrutiny.
    """
    return size_bytes % 2352 == 0 or size_bytes % 2048 == 0


def find_bins_matching_arcade_crc(
    directory: Path, arcade_crc_index: dict[str, set[str]]
) -> dict[Path, set[str]]:
    """REPAIR-TOOL-5: cross loose ``.bin`` files under *directory* (no
    sidecar ``.cue``) against an arcade CRC index (``load_arcade_crc_index``)
    to catch an arcade chip that ended up in a console platform folder.

    Two separate manual audits (`Día52` section 9, and a later session
    sections 14-15) were needed to find exactly this by hand -- with the CRC
    index already built for ZIP routing (ZIP-ROUTE-2), the same lookup works
    unpacked. Returns only bins with at least one CRC hit, mapped to the
    candidate arcade set name(s) (a CRC can be shared by parent/clone sets).
    """
    hits: dict[Path, set[str]] = {}
    if not arcade_crc_index:
        return hits
    for bin_path in _unclaimed_bins(directory):
        crc = calculate_hashes(bin_path).crc32
        sets = arcade_crc_index.get(crc)
        if sets:
            hits[bin_path] = sets
    return hits


def find_bins_needing_cue(directory: Path) -> list[Path]:
    """Bare .bin files under *directory* with valid sector geometry but no
    sidecar .cue -- unlike ``find_bare_bin_files``, this does NOT require a
    successful RA hash. That gate exists there to protect an irreversible
    action (CHD conversion + optional source deletion); adding a .cue
    sidecar is fully reversible, so a disc whose RA hash can't be computed
    yet (e.g. a boot path RA's hasher doesn't resolve) is still included.
    """
    return [f for f in _unclaimed_bins(directory) if detect_bin_cue_mode(f) is not None]


def synthesize_cue_text(bin_path: Path) -> str | None:
    """Minimal single-track .cue text for a bare .bin, or None if its sector
    geometry isn't one ``detect_bin_cue_mode`` recognizes."""
    mode = detect_bin_cue_mode(bin_path)
    if mode is None:
        return None
    return f'FILE "{bin_path.name}" BINARY\nTRACK 01 {mode}\n  INDEX 01 00:00:00\n'


def generate_missing_cues(directory: Path, *, dry_run: bool = True) -> list[Path]:
    """Write a minimal single-track .cue sidecar next to every bare .bin
    under *directory* with valid sector geometry. Never touches the .bin
    itself. Returns the .cue paths written (or that would be written, in
    dry-run mode)."""
    written = []
    for bin_path in find_bins_needing_cue(directory):
        cue_path = bin_path.with_suffix(".cue")
        if cue_path.exists():
            continue
        written.append(cue_path)
        if not dry_run:
            cue_path.write_text(synthesize_cue_text(bin_path), encoding="utf-8")
    return written


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


def _stage_corrected_cue(cue_path: Path, bin_paths: list[Path]) -> Path:
    """Write a throwaway copy of *cue_path* next to it with every FILE line
    replaced by the plain basename of the real, verified-existing sibling in
    *bin_paths* -- chdman reads the .cue's raw text itself, so a stale
    absolute FILE reference (e.g. "C:\\CRASH 2.BIN", found live in this
    library) is never actually fixed by a ``cwd=`` alone; it has to be
    rewritten before chdman ever sees the file."""
    text = cue_path.read_text(encoding="utf-8", errors="replace")
    names = iter(b.name for b in bin_paths)
    out_lines = []
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.upper().startswith("FILE "):
            newline = "\n" if line.endswith("\n") else ""
            rest = re.sub(r"^FILE\s+(?:\"[^\"]+\"|\S+)", "", stripped, flags=re.IGNORECASE)
            out_lines.append(f'FILE "{next(names)}"{rest}{newline}')
        else:
            out_lines.append(line)
    staged = cue_path.with_name(f"{cue_path.stem}.staged.cue")
    staged.write_text("".join(out_lines), encoding="utf-8")
    return staged


def _run_chdman_createcd(staged_cue: Path, chd_path: Path, chdman: str) -> str | None:
    """Run ``chdman createcd``; returns an error message, or None on success."""
    try:
        subprocess.run(
            [chdman, "createcd", "-i", str(staged_cue), "-o", str(chd_path)],
            check=True,
            capture_output=True,
            cwd=str(staged_cue.parent),
        )
    except FileNotFoundError:
        return f"chdman binary not found: {chdman!r}"
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode(errors="replace").strip()
        return stderr or f"chdman exited with code {exc.returncode}"

    if not chd_path.exists() or chd_path.stat().st_size == 0:
        if chd_path.exists():
            chd_path.unlink(missing_ok=True)
        return "chdman terminó sin error pero el .chd resultante falta o está vacío"
    return None


def _verify_ra_hash(source_for_hash: Path, chd_path: Path, chdman: str) -> tuple[str | None, bool]:
    """Compare the RetroAchievements hash of *source_for_hash* (a .cue or a
    bare .bin -- ``compute_psx_ra_hash`` dispatches on extension) against the
    freshly-created *chd_path*. Returns ``(error, verified)``: *error* is set
    on mismatch/failure (and the bad .chd is deleted), None if they match or
    if no hash could be computed at all. *verified* is True only when both
    hashes were computed and matched -- callers must not delete the source
    unless this is True: a None source hash is not proof of anything, just
    an unsupported/undetectable disc (e.g. a bin whose geometry looked valid
    but whose filesystem couldn't be read -- see ``find_bins_needing_cue``,
    which -- unlike ``find_bare_bin_files`` -- accepts exactly such bins)."""
    source_hash = compute_psx_ra_hash(source_for_hash)
    chd_hash = compute_psx_ra_hash(chd_path, chdman_path=Path(chdman))
    if source_hash is not None and source_hash != chd_hash:
        chd_path.unlink(missing_ok=True)
        error = f"el hash RA no coincide tras la conversión (origen={source_hash}, chd={chd_hash}) — no se toca el original"
        return error, False
    return None, source_hash is not None and source_hash == chd_hash


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

    staged_cue = _stage_corrected_cue(cue_path, bin_paths)
    try:
        error = _run_chdman_createcd(staged_cue, chd_path, chdman)
    finally:
        staged_cue.unlink(missing_ok=True)
    if error:
        return ConversionResult(
            cue_path=cue_path, chd_path=chd_path, bin_paths=bin_paths, success=False, error=error
        )

    error, verified = _verify_ra_hash(cue_path, chd_path, chdman)
    if error:
        return ConversionResult(
            cue_path=cue_path, chd_path=chd_path, bin_paths=bin_paths, success=False, error=error
        )

    if delete_source and verified:
        for bin_path in bin_paths:
            bin_path.unlink(missing_ok=True)
        cue_path.unlink(missing_ok=True)

    return ConversionResult(
        cue_path=cue_path,
        chd_path=chd_path,
        bin_paths=bin_paths,
        success=True,
    )


def convert_bin_to_chd(
    bin_path: Path,
    *,
    chdman: str = "chdman",
    delete_source: bool = False,
) -> ConversionResult:
    """Convert a bare .bin (no sidecar .cue -- the common shape in this
    library) to .chd, via a synthesized single-track .cue. Mirrors
    ``convert_to_chd``'s result shape (``cue_path`` is where that synthetic
    .cue *would* live, ``bin_paths`` is just ``[bin_path]``)."""
    cue_path = bin_path.with_suffix(".cue")
    chd_path = bin_path.with_suffix(".chd")
    bin_paths = [bin_path]

    if chd_path.exists():
        if delete_source:
            bin_path.unlink(missing_ok=True)
            return ConversionResult(cue_path, chd_path, bin_paths, success=True)
        return ConversionResult(
            cue_path,
            chd_path,
            bin_paths,
            success=False,
            error="Output .chd already exists — skipping to avoid overwrite.",
        )

    cue_text = synthesize_cue_text(bin_path)
    if cue_text is None:
        return ConversionResult(
            cue_path,
            chd_path,
            bin_paths,
            success=False,
            error="geometría de sector no reconocida (no es un .bin de PS1 estándar)",
        )

    staged_cue = bin_path.with_name(f"{bin_path.stem}.staged.cue")
    staged_cue.write_text(cue_text, encoding="utf-8")
    try:
        error = _run_chdman_createcd(staged_cue, chd_path, chdman)
    finally:
        staged_cue.unlink(missing_ok=True)
    if error:
        return ConversionResult(cue_path, chd_path, bin_paths, success=False, error=error)

    error, verified = _verify_ra_hash(bin_path, chd_path, chdman)
    if error:
        return ConversionResult(cue_path, chd_path, bin_paths, success=False, error=error)

    if delete_source and verified:
        bin_path.unlink(missing_ok=True)

    return ConversionResult(cue_path, chd_path, bin_paths, success=True)


def _record(summary: ConversionSummary, result: ConversionResult) -> None:
    summary.results.append(result)
    if result.success:
        summary.converted += 1
    elif result.error and "already exists" in result.error:
        summary.skipped += 1
    else:
        summary.failed += 1


def convert_directory(
    directory: Path,
    *,
    chdman: str = "chdman",
    delete_source: bool = False,
    dry_run: bool = True,
) -> ConversionSummary:
    """Convert every PS1 disc image in a directory tree to .chd -- both
    existing .cue+.bin sets and bare .bin files with no .cue at all (the
    common shape in this library, see ``find_bare_bin_files``).

    In dry_run mode (the default) no files are touched — only a summary is
    returned; the RA-hash verification only runs when actually converting
    (dry-run has nothing to compare the not-yet-created .chd against).
    """
    summary = ConversionSummary()

    for cue_path in find_cue_files(directory):
        chd_path = cue_path.with_suffix(".chd")
        bin_paths = parse_bins_from_cue(cue_path)

        if dry_run:
            if chd_path.exists():
                _record(
                    summary,
                    ConversionResult(
                        cue_path,
                        chd_path,
                        bin_paths,
                        success=False,
                        error="Output .chd already exists — would skip.",
                    ),
                )
                continue
            missing = [b for b in bin_paths if not b.exists()]
            if missing:
                _record(
                    summary,
                    ConversionResult(
                        cue_path,
                        chd_path,
                        bin_paths,
                        success=False,
                        error=f"Bin file(s) not found: {', '.join(b.name for b in missing)}",
                    ),
                )
            else:
                _record(summary, ConversionResult(cue_path, chd_path, bin_paths, success=True))
            continue

        _record(summary, convert_to_chd(cue_path, chdman=chdman, delete_source=delete_source))

    for bin_path in find_bare_bin_files(directory):
        chd_path = bin_path.with_suffix(".chd")
        cue_path = bin_path.with_suffix(".cue")  # would-be synthetic .cue

        if dry_run:
            if chd_path.exists():
                _record(
                    summary,
                    ConversionResult(
                        cue_path,
                        chd_path,
                        [bin_path],
                        success=False,
                        error="Output .chd already exists — would skip.",
                    ),
                )
            else:
                _record(summary, ConversionResult(cue_path, chd_path, [bin_path], success=True))
            continue

        _record(summary, convert_bin_to_chd(bin_path, chdman=chdman, delete_source=delete_source))

    return summary
