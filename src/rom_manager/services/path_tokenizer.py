"""DEVPROFILE-3: portable path tokens for the device-profile manifest.

An absolute local path (``E:/ROMs/nes/game.zip``) is meaningless on another
device. ``tokenize()`` turns it into ``{ROMS}/nes/game.zip`` when saving a
profile; ``resolve()`` turns it back using the *target* device's own roots
when restoring. Pure functions, no I/O — the manifest (DEVPROFILE-4) is the
only caller, at export/import time between different devices (see
``Tareas/Roadmap-DEVPROFILE-1-4.md`` §4).
"""

from __future__ import annotations

from pathlib import Path

_TOKENS = ("ROMS", "SAVES", "SYSTEM", "PROJECT_ROOT")


def tokenize(
    path: Path,
    roms_dir: Path,
    saves_dir: Path,
    system_dir: Path,
    project_root: Path | None = None,
) -> str:
    """Replace whichever of *roms_dir*/*saves_dir*/*system_dir*/*project_root*
    contains *path* with its token. Falls back to the plain (untokenized) path
    if none do — that's expected for paths outside the watched roots, not an
    error.

    *project_root* (DEVPROFILE-8) covers tool-owned data outside the ROMs/
    saves/RetroArch install roots — e.g. ``.rommgr/catalogs`` (No-Intro/Redump
    DATs) — so a manifest saved on one PC still points at the right folder on
    another PC with a different install path. Optional and last-checked (after
    ROMS/SAVES/SYSTEM) since it's typically the shallowest of the roots.
    """
    roots = {"ROMS": roms_dir, "SAVES": saves_dir, "SYSTEM": system_dir}
    if project_root is not None:
        roots["PROJECT_ROOT"] = project_root
    path = Path(path)
    # Longest root first so a root nested inside another wins.
    for token, root in sorted(roots.items(), key=lambda kv: -len(str(kv[1]))):
        try:
            rel = path.resolve().relative_to(Path(root).resolve())
        except ValueError:
            continue
        rel_str = rel.as_posix()
        return f"{{{token}}}" if rel_str == "." else f"{{{token}}}/{rel_str}"
    return str(path)


def resolve(
    token_path: str,
    roms_dir: Path,
    saves_dir: Path,
    system_dir: Path,
    project_root: Path | None = None,
) -> Path:
    """Reverse of ``tokenize()``: substitute a leading ``{ROMS}``/``{SAVES}``/
    ``{SYSTEM}``/``{PROJECT_ROOT}`` with the given root. A path with no known
    token prefix is returned as-is (it never went through ``tokenize()``, e.g.
    a standalone emulator's own config dir — those sync between the same
    PC+Anbernic pair and never need re-rooting)."""
    roots = {"ROMS": roms_dir, "SAVES": saves_dir, "SYSTEM": system_dir}
    if project_root is not None:
        roots["PROJECT_ROOT"] = project_root
    for token in _TOKENS:
        if token not in roots:
            continue
        prefix = f"{{{token}}}"
        if token_path == prefix:
            return Path(roots[token])
        if token_path.startswith(prefix + "/"):
            return Path(roots[token]) / token_path[len(prefix) + 1 :]
    return Path(token_path)
