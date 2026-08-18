"""Discovery, raw read/write, and cross-device copy of RetroArch per-game
option overrides (CFG-PORGAME-6/7/8).

RetroArch writes a game-options file as ``config/<core>/<rom stem>.opt`` the
moment the user saves options from its own Quick Menu — Retro Vault never
authors or interprets the keys inside. `list_overrides()` only needs to know
*which* games already have one, and under *which* core, so PC and Android
can be compared without ever merging them (CFG-PORGAME design decision:
never auto-copy an override between devices of different power).
`read_override()`/`write_override()` round-trip one file's content as opaque
text, for an editor that never parses the keys either. `copy_override()`
builds on both to push one override from PC to Android or vice versa, but
only when it's actually meaningful to do so — see `SHARED_CORES`.
"""

from __future__ import annotations

import datetime as _dt
import tempfile
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.sync.adb_transport import AdbTransport

_OPT_EXTENSIONS = frozenset({".opt"})

# CFG-PORGAME-3: cores that are the exact same libretro core on both PC and
# the RG556 (identical `config/<core>/` folder name on both sides) — see
# docs/architecture/platforms-cores.md. Every other platform uses a
# different core (or a different core name) per side, so an override from
# one is meaningless on the other — copying is only ever offered for these.
SHARED_CORES = frozenset(
    {
        "FCEUmm",
        "Gambatte",
        "mGBA",
        "melonDS",
        "Genesis Plus GX",
        "Yaba Sanshiro 2 Pro",
        "PPSSPP",
        "Stella 2023",
    }
)


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


def _read_raw(
    config_dir: str,
    core: str,
    filename: str,
    adb_transport: AdbTransport | None,
) -> str:
    if adb_transport is not None:
        android_path = f"{config_dir}/{core}/{filename}"
        with tempfile.TemporaryDirectory() as tmp_dir:
            local = Path(tmp_dir) / filename
            adb_transport.pull(android_path, local)
            return local.read_text(encoding="utf-8", errors="replace")

    path = Path(config_dir) / core / filename
    return path.read_text(encoding="utf-8", errors="replace")


def _write_raw(
    config_dir: str,
    core: str,
    filename: str,
    content: str,
    adb_transport: AdbTransport | None,
) -> None:
    if adb_transport is not None:
        android_path = f"{config_dir}/{core}/{filename}"
        with tempfile.TemporaryDirectory() as tmp_dir:
            local = Path(tmp_dir) / filename
            local.write_text(content, encoding="utf-8")
            adb_transport.push(local, android_path, verify=True)
        return

    path = Path(config_dir) / core / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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
    return _read_raw(config_dir, core, f"{rom}.opt", adb_transport)


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
    _write_raw(config_dir, core, f"{rom}.opt", content, adb_transport)


def copy_override(
    rom: str,
    core: str,
    *,
    source_config_dir: str,
    source_adb_transport: AdbTransport | None,
    dest_config_dir: str,
    dest_adb_transport: AdbTransport | None,
) -> dict:
    """Copy one override from one side to the other (CFG-PORGAME-8).

    Only allowed for `SHARED_CORES` — the same core folder name on PC and
    Android is what makes a copy meaningful at all. If the destination
    already has an override for this (*rom*, *core*), it's backed up first
    as ``<rom>.opt.bak-<timestamp>`` next to the original — same "ante duda,
    no sobrescribir; guardar backup primero" rule already used for saves.

    Returns ``{"backed_up": bool, "backup_filename": str | None}``.
    """
    if core not in SHARED_CORES:
        raise ValueError(
            f"{core!r} no es un core compartido entre PC y Android — "
            "copiar este override no tiene sentido en el otro lado"
        )

    content = read_override(source_config_dir, rom, core, adb_transport=source_adb_transport)

    backup_filename: str | None = None
    try:
        existing = read_override(dest_config_dir, rom, core, adb_transport=dest_adb_transport)
    except (FileNotFoundError, OSError):
        # PC raises FileNotFoundError for a missing file; the ADB path raises
        # a plain OSError either way (pull() doesn't distinguish "missing" from
        # other transfer failures) — either way there's nothing to back up.
        # A genuine connectivity problem surfaces anyway: write_override()
        # below does its own push() and fails the same way, so no data is
        # lost by treating this broadly.
        existing = None

    if existing is not None:
        safe_rom = _safe_component(rom, "rom")
        safe_core = _safe_component(core, "core")
        timestamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_filename = f"{safe_rom}.opt.bak-{timestamp}"
        _write_raw(dest_config_dir, safe_core, backup_filename, existing, dest_adb_transport)

    write_override(dest_config_dir, rom, core, content, adb_transport=dest_adb_transport)
    return {"backed_up": existing is not None, "backup_filename": backup_filename}
