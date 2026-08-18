"""Read-only discovery of RetroArch per-game option overrides (CFG-PORGAME-6).

RetroArch writes a game-options file as ``config/<core>/<rom stem>.opt`` the
moment the user saves options from its own Quick Menu — Retro Vault never
authors or interprets the keys inside, it only needs to know *which* games
already have one, and under *which* core, so PC and Android can be compared
without ever merging them (CFG-PORGAME design decision: never auto-copy an
override between devices of different power).
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.sync.adb_transport import AdbTransport

_OPT_EXTENSIONS = frozenset({".opt"})


def list_overrides(
    config_dir: str,
    adb_transport: AdbTransport | None = None,
) -> dict[str, list[str]]:
    """Scan a RetroArch ``config/`` folder for per-game ``.opt`` overrides.

    *config_dir* is a local filesystem path when *adb_transport* is ``None``
    (PC), or an Android path read via ADB otherwise. Returns
    ``{rom_stem: [core_name, ...]}`` — a ROM can appear under more than one
    core if the user switched cores over time; both are reported rather than
    picking one.
    """
    if not config_dir:
        return {}

    overrides: dict[str, list[str]] = {}

    if adb_transport is not None:
        for info in adb_transport.ls_recursive(config_dir, wanted_extensions=_OPT_EXTENSIONS):
            p = PurePosixPath(info.android_path)
            overrides.setdefault(p.stem, []).append(p.parent.name)
        return overrides

    base = Path(config_dir)
    if not base.is_dir():
        return {}
    for opt_file in base.glob("*/*.opt"):
        overrides.setdefault(opt_file.stem, []).append(opt_file.parent.name)
    return overrides
