"""RetroArch per-game override listing, PC vs Android (CFG-PORGAME-6).

Pure function: typed params → JSON-ready dict. No global job state. Mirrors
the PC/Android split of `_build_library_diff` (diff.py), but overrides are
never merged into a single set the way ROMs are — same core name in both
places is only ever surfaced as a hint, never auto-copied (CFG-PORGAME
design decision).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rom_manager.config import AppConfig
from rom_manager.services.retroarch_overrides_service import SHARED_CORES, list_overrides

if TYPE_CHECKING:
    from rom_manager.sync.adb_transport import AdbTransport


def _build_overrides(config: AppConfig, adb_transport: AdbTransport | None) -> dict:
    pc_overrides = list_overrides(config.sync.ra_config_dir)

    android_overrides: dict[str, list[str]] = {}
    android_message: str | None = None
    if adb_transport is None:
        android_message = "conecta el dispositivo Android por ADB para ver sus overrides"
    else:
        android_config_dir = f"{config.sync.auto_sync_android_path}/config"
        try:
            android_overrides = list_overrides(android_config_dir, adb_transport=adb_transport)
        except Exception as exc:
            android_message = f"error ADB: {exc}"

    stems = set(pc_overrides) | set(android_overrides)
    only_pc: list[dict] = []
    only_android: list[dict] = []
    in_both: list[dict] = []
    for stem in sorted(stems):
        pc_cores = sorted(pc_overrides.get(stem, []))
        android_cores = sorted(android_overrides.get(stem, []))
        if pc_cores and android_cores:
            in_both.append(
                {
                    "rom": stem,
                    "pc_cores": pc_cores,
                    "android_cores": android_cores,
                    "core_match": bool(set(pc_cores) & set(android_cores)),
                }
            )
        elif pc_cores:
            only_pc.append({"rom": stem, "cores": pc_cores})
        else:
            only_android.append({"rom": stem, "cores": android_cores})

    return {
        "only_pc": only_pc,
        "only_android": only_android,
        "in_both": in_both,
        "total_pc": len(pc_overrides),
        "total_android": len(android_overrides),
        "pc_configured": bool(config.sync.ra_config_dir),
        "android_message": android_message,
        # CFG-PORGAME-3/8: la UI decide si mostrar "Copiar" por core mirando
        # esta lista — evita duplicar el criterio de negocio en JS.
        "shared_cores": sorted(SHARED_CORES),
    }
