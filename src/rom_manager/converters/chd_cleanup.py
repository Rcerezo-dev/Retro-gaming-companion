"""Find and safely remove a raw .cue/.bin PSX dump once its .chd conversion
already exists under the exact same name — the classic "converted, never
cleaned up the source" leftover. Found live 2026-09-29 auditing the Anbernic
real device: 195 PSX titles with this shape (Final Fantasy VII/VIII, Metal
Gear Solid, Xenogears, Grandia, Valkyrie Profile, Parasite Eve...), several
GB each. Deliberately scoped to *exact same stem* only — a same-title-
different-region pair (see GDI-ORGANIZE-1's Final Fantasy VII writeup, or
DUP-CROSSFMT-VERIFY-1) is a different, higher-risk decision that still needs
a human, never auto-resolved here.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from rom_manager.converters.chd_converter import parse_bins_from_cue, verify_chd
from rom_manager.retroachievements.ra_hash_psx import compute_psx_ra_hash


@dataclass(slots=True)
class RedundantChdSourceCandidate:
    """A .cue with a same-stem .chd already present in the same directory —
    e.g. "Final Fantasy VIII (USA) (Disc 1).cue" next to "...(Disc 1).chd"."""

    directory: str  # posix dir, no trailing slash
    cue_path: str  # full posix path
    chd_path: str  # full posix path, same directory + stem as cue_path


def find_redundant_chd_sources(files: list[str]) -> list[RedundantChdSourceCandidate]:
    """Pure — *files* is a flat list of full posix paths (as returned by
    ``AdbTransport.ls_recursive`` or any directory walk, no I/O here). Groups
    by (directory, stem) and returns one candidate per .cue that has a
    same-stem .chd in the same directory. Bin resolution and content
    verification happen later, once the .cue is actually pulled/read —
    trusting only the filename here would repeat the exact "Europe" .cue
    mismatch found in GDI-ORGANIZE-1 (referenced a differently-named .bin).
    """
    by_dir_stem: dict[tuple[str, str], dict[str, str]] = {}
    for f in files:
        p = PurePosixPath(f)
        key = (str(p.parent), p.stem)
        bucket = by_dir_stem.setdefault(key, {})
        suffix = p.suffix.lower()
        if suffix in (".cue", ".chd"):
            bucket.setdefault(suffix, f)

    candidates = []
    for (directory, _stem), bucket in sorted(by_dir_stem.items()):
        if ".cue" in bucket and ".chd" in bucket:
            candidates.append(
                RedundantChdSourceCandidate(
                    directory=directory, cue_path=bucket[".cue"], chd_path=bucket[".chd"]
                )
            )
    return candidates


@dataclass(slots=True)
class CleanupResult:
    candidate: RedundantChdSourceCandidate
    verified: bool
    freed_bytes: int = 0
    removed_paths: list[str] = field(default_factory=list)
    error: str = ""


def verify_and_clean_one(
    candidate: RedundantChdSourceCandidate,
    *,
    pull_to: Path,
    chdman: str,
    remove_remote,  # Callable[[str], None] — e.g. AdbTransport.remove, or a PC-side discard
    pull_file=None,  # Callable[[str, Path], None] | None — None means files are already local
    dry_run: bool = True,
) -> CleanupResult:
    """Verify one candidate (chdman integrity + RA hash of source == RA hash
    of .chd, same check ``convert_to_chd(delete_source=True)`` already trusts
    for a same-machine conversion) and, only if it matches, remove the raw
    .cue + its referenced .bin(s) via *remove_remote*.

    *pull_file* is None for an already-local repo (PC): *pull_to* is then
    read directly from the real filesystem, nothing is copied. For a remote
    repo (Android/ADB), pass a puller (e.g. ``lambda src, dst:
    transport.pull(src, dst)``) — files land under *pull_to* and are deleted
    again after verification either way, successful or not.
    """
    pull_to.mkdir(parents=True, exist_ok=True)
    local_cue = pull_to / PurePosixPath(candidate.cue_path).name
    local_chd = pull_to / PurePosixPath(candidate.chd_path).name

    try:
        try:
            if pull_file is not None:
                pull_file(candidate.cue_path, local_cue)
            bin_names = [Path(b).name for b in parse_bins_from_cue(local_cue)]
            remote_bins = [str(PurePosixPath(candidate.directory) / name) for name in bin_names]

            if pull_file is not None:
                for remote_bin, name in zip(remote_bins, bin_names, strict=True):
                    pull_file(remote_bin, pull_to / name)
                pull_file(candidate.chd_path, local_chd)
        except OSError as exc:
            # A .cue referencing a .bin that doesn't actually exist on the
            # device is a real, seen-live shape (GDI-ORGANIZE-1's "Europe"
            # .gdi had the same problem) — one broken/incomplete candidate
            # must never abort the whole batch.
            return CleanupResult(candidate, verified=False, error=f"pull falló: {exc}")

        missing = [b for b in bin_names if not (pull_to / b).exists()]
        if missing:
            return CleanupResult(
                candidate, verified=False, error=f"bin(s) no encontrados: {missing}"
            )

        integrity = verify_chd(local_chd, chdman=chdman)
        if not integrity.ok:
            return CleanupResult(
                candidate, verified=False, error=f"chdman verify falló: {integrity.error}"
            )

        source_hash = compute_psx_ra_hash(local_cue)
        chd_hash = compute_psx_ra_hash(local_chd, chdman_path=Path(chdman))
        if source_hash is None or source_hash != chd_hash:
            return CleanupResult(
                candidate,
                verified=False,
                error=f"hash RA no coincide (origen={source_hash}, chd={chd_hash})",
            )

        freed = sum((pull_to / b).stat().st_size for b in bin_names) + local_cue.stat().st_size
        removed = [candidate.cue_path, *remote_bins]
        if not dry_run:
            for remote_path in removed:
                remove_remote(remote_path)
        return CleanupResult(candidate, verified=True, freed_bytes=freed, removed_paths=removed)
    finally:
        # Only clean up when the files were pulled as temporary staging
        # copies (pull_file is not None) -- for an already-local repo
        # (pull_file=None) local_cue/local_chd/*.bin ARE the real library
        # files, never touched directly here; their removal, if any, goes
        # exclusively through remove_remote() above.
        if pull_file is not None:
            shutil.rmtree(pull_to, ignore_errors=True)
