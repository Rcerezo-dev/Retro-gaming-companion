"""Discovery + raw read/write of RetroArch per-game option overrides
(CFG-PORGAME-6/7).

RetroArch writes a game-options file as ``config/<core>/<rom stem>.opt`` the
moment the user saves options from its own Quick Menu — Retro Vault never
authors or interprets the keys inside. `list_overrides()` only needs to know
*which* games already have one, and under *which* core, so PC and Android
can be compared without ever merging them (CFG-PORGAME design decision:
never auto-copy an override between devices of different power).
`read_override()`/`write_override()` round-trip one file's content as opaque
text, for an editor that never parses the keys either.
"""

from __future__ import annotations

import tempfile
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.sync.adb_transport import AdbTransport

_OPT_EXTENSIONS = frozenset({".opt"})


def _safe_component(name: str, label: str) -> str:
    """Reject path-traversal attempts in a *rom*/*core* name used to build a path.

    Both values normally come straight from a prior `list_overrides()` call
    (real filenames already on disk), but the HTTP layer can't assume that —
    treat them as untrusted input the same way any other file-path parameter
    from a request would be.
    """
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError(f"{label} inválido: {name!r}")
    return name


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


def read_override(
    config_dir: str,
    rom: str,
    core: str,
    adb_transport: AdbTransport | None = None,
) -> str:
    """Read the raw text of one ``<config_dir>/<core>/<rom>.opt`` (CFG-PORGAME-7).

    Content is never parsed — RetroArch owns the key format, Retro Vault only
    round-trips whatever the user already saved from its Quick Menu.
    """
    core = _safe_component(core, "core")
    rom = _safe_component(rom, "rom")

    if adb_transport is not None:
        android_path = f"{config_dir}/{core}/{rom}.opt"
        with tempfile.TemporaryDirectory() as tmp_dir:
            local = Path(tmp_dir) / "override.opt"
            adb_transport.pull(android_path, local)
            return local.read_text(encoding="utf-8", errors="replace")

    path = Path(config_dir) / core / f"{rom}.opt"
    return path.read_text(encoding="utf-8", errors="replace")


def write_override(
    config_dir: str,
    rom: str,
    core: str,
    content: str,
    adb_transport: AdbTransport | None = None,
) -> None:
    """Write *content* back to ``<config_dir>/<core>/<rom>.opt`` (CFG-PORGAME-7).

    Overwrites in place — same "ante duda, no sobrescribir" caution as saves
    is the caller's job (confirm with the user before calling this), not
    this function's: it always writes what it's given.
    """
    core = _safe_component(core, "core")
    rom = _safe_component(rom, "rom")

    if adb_transport is not None:
        android_path = f"{config_dir}/{core}/{rom}.opt"
        with tempfile.TemporaryDirectory() as tmp_dir:
            local = Path(tmp_dir) / "override.opt"
            local.write_text(content, encoding="utf-8")
            adb_transport.push(local, android_path, verify=True)
        return

    path = Path(config_dir) / core / f"{rom}.opt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
