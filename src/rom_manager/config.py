from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

_logger = logging.getLogger(__name__)

# Default Android emulator save/savestate path mappings.
# Verified live on Anbernic RG556 (serial: RG556006101273).
# Source: docs/android-save-paths-RG556.md
# Keys are Android package names. Users can override entries via [[emulator_paths]] in config.toml.
EMULATOR_SAVE_PATHS_DEFAULT: dict[str, dict] = {
    "com.retroarch.aarch64": {
        "name": "RetroArch",
        "saves_path": "/storage/emulated/0/RetroArch/saves",
        "states_path": "/storage/emulated/0/RetroArch/states",
        "adb_required": False,
        "notes": "Saves/states are per-core subfolder (e.g. saves/Beetle PSX/)",
    },
    "org.ppsspp.ppsspp": {
        "name": "PPSSPP",
        "saves_path": "/storage/emulated/0/PSP/SAVEDATA",
        "states_path": "/storage/emulated/0/PSP/PPSSPP_STATE",
        "adb_required": False,
    },
    "com.github.stenzek.duckstation": {
        "name": "DuckStation (PS1)",
        "saves_path": "/storage/emulated/0/Android/data/com.github.stenzek.duckstation/files/memcards",
        "states_path": "/storage/emulated/0/Android/data/com.github.stenzek.duckstation/files/savestates",
        "adb_required": True,
        "save_extensions": [".mcd", ".mcr", ".srm"],
        "state_extensions": [".sav"],
    },
    "xyz.aethersx2.android": {
        "name": "AetherSX2 / NetherSX2 (PS2)",
        "saves_path": "/storage/emulated/0/Android/data/xyz.aethersx2.android/files/memcards",
        "states_path": "/storage/emulated/0/Android/data/xyz.aethersx2.android/files/sstates",
        "adb_required": True,
        "save_extensions": [".ps2"],
        "state_extensions": [".p2s", ".p2s.backup"],
    },
    "org.dolphinemu.dolphinemu": {
        "name": "Dolphin (GC/Wii)",
        "saves_path": "/storage/emulated/0/Android/data/org.dolphinemu.dolphinemu/files/GC",
        "states_path": "/storage/emulated/0/Android/data/org.dolphinemu.dolphinemu/files/StateSaves",
        "adb_required": True,
        "notes": "Permission denied via ADB without root — use Dolphin in-app backup instead",
        "accessible": False,
    },
    "org.dolphinemu.mmjr": {
        "name": "Dolphin MMJ (GC/Wii)",
        "saves_path": "/storage/emulated/0/Android/data/org.dolphinemu.mmjr/files/GC",
        "states_path": "/storage/emulated/0/Android/data/org.dolphinemu.mmjr/files/StateSaves",
        "adb_required": True,
        "notes": "Permission denied via ADB without root",
        "accessible": False,
    },
    "org.citra.emu": {
        "name": "Citra (3DS)",
        "saves_path": "/storage/emulated/0/Android/data/org.citra.emu/files/citra-emu/sdmc/Nintendo 3DS",
        "states_path": None,
        "adb_required": True,
    },
    "io.github.lime3ds.android": {
        "name": "Lime3DS (3DS)",
        "saves_path": "/storage/emulated/0/Android/data/io.github.lime3ds.android/files",
        "states_path": None,
        "adb_required": True,
    },
    "io.recompiled.redream": {
        "name": "Redream (Dreamcast)",
        "saves_path": "/storage/emulated/0/Android/data/io.recompiled.redream/files",
        "states_path": "/storage/emulated/0/Android/data/io.recompiled.redream/files/states",
        "adb_required": True,
        "state_extensions": [".sav"],
        "notes": "VMU saves: vmu0.bin–vmu3.bin at saves_path root",
    },
    "com.flycast.emulator": {
        "name": "Flycast (Dreamcast)",
        "saves_path": "/storage/emulated/0/Android/data/com.flycast.emulator/files",
        "states_path": None,
        "adb_required": True,
    },
    "org.devmiyax.yabasanshioro2.pro": {
        "name": "Yaba Sanshiro 2 (Saturn)",
        "saves_path": "/storage/emulated/0/Android/data/org.devmiyax.yabasanshioro2.pro/files/yabause/memory",
        "states_path": "/storage/emulated/0/Android/data/org.devmiyax.yabasanshioro2.pro/files/yabause/state",
        "adb_required": True,
    },
    "com.explusalpha.Snes9xPlus": {
        "name": "Snes9x EX+ (SNES)",
        "saves_path": "/storage/emulated/0/Android/data/com.explusalpha.Snes9xPlus/files/EmuEx/SFC-SNES/saves",
        "states_path": None,
        "adb_required": True,
        "state_extensions": [".frz"],
        "notes": "State format: <GameTitle>.<slot>.frz",
    },
    "com.explusalpha.GbaEmu": {
        "name": "GBA.emu (GBA)",
        "saves_path": "/storage/emulated/0/Android/data/com.explusalpha.GbaEmu/files/EmuEx/GBA/saves",
        "states_path": None,
        "adb_required": True,
        "state_extensions": [".frz"],
    },
    "com.explusalpha.GbcEmu": {
        "name": "GBC.emu (GBC)",
        "saves_path": "/storage/emulated/0/Android/data/com.explusalpha.GbcEmu/files/EmuEx/GBC/saves",
        "states_path": None,
        "adb_required": True,
        "state_extensions": [".frz"],
    },
    "com.explusalpha.NesEmu": {
        "name": "NES.emu (NES)",
        "saves_path": "/storage/emulated/0/Android/data/com.explusalpha.NesEmu/files/EmuEx/NES/saves",
        "states_path": None,
        "adb_required": True,
        "state_extensions": [".frz"],
    },
    "com.explusalpha.MdEmu": {
        "name": "MD.emu (Mega Drive)",
        "saves_path": "/storage/emulated/0/Android/data/com.explusalpha.MdEmu/files/EmuEx/MD/saves",
        "states_path": None,
        "adb_required": True,
        "state_extensions": [".frz"],
    },
    "me.magnum.melonds": {
        "name": "melonDS (Nintendo DS)",
        "saves_path": "/storage/emulated/0/Android/data/me.magnum.melonds/files",
        "states_path": None,
        "adb_required": True,
        "notes": "Save location may vary; may be alongside ROMs",
    },
    "org.mupen64plusae.v3.fzurita.pro": {
        "name": "Mupen64Plus FZ (N64)",
        "saves_path": None,
        "states_path": None,
        "adb_required": True,
        "notes": "Save location unknown — may be alongside ROMs or user-configured sdcard path",
    },
}


@dataclass(slots=True)
class SyncSource:
    """One emulator's save directory paired with its cloud remote path."""

    name: str
    local_dir: str
    remote: str
    sync_all: bool = (
        False  # True → sync every file (no extension filter); use for PPSSPP/Dolphin etc.
    )


@dataclass(slots=True)
class SyncConfig:
    """Save-sync settings: cloud remotes, auto-sync daemon, conflict policy (ARC-CFG-1).

    Extracted from the flat fields of ``AppConfig`` so sync concerns live in one
    cohesive unit. Mutable — handlers update these fields in place under
    ``_config_lock`` after a config save.
    """

    rclone_remote: str = ""  # legacy single-remote rclone path (e.g. "dropbox:/RetroSync/saves")
    # Auto-sync daemon settings
    auto_sync_enabled: bool = True
    auto_sync_direction: str = "newest"  # "newest" | "pc_to_anbernic" | "anbernic_to_pc"
    auto_sync_android_path: str = "/storage/emulated/0/RetroArch"  # Android RetroArch root path
    auto_sync_known_devices: list = field(default_factory=list)  # serials; empty = any device
    conflict_policy: str = "newest"  # "newest" | "keep_pc" | "keep_android" | "ask"
    # Dual-remote cloud sync (D2)
    saves_remote: str = ""  # rclone remote for permanent saves
    states_remote: str = ""  # rclone remote for savestates
    # Multi-source cloud sync — one entry per emulator, from [[sync.sources]] in config.toml
    sync_sources: list[SyncSource] = field(default_factory=list)
    # RetroArch core config sync (.opt files)
    ra_config_dir: str = ""    # path to RetroArch/config/ folder
    ra_config_remote: str = "" # rclone remote for .opt files (e.g. "dropbox:/RetroSync/ra-config")


@dataclass(slots=True)
class CredentialsConfig:
    """Secrets: ScreenScraper + RetroAchievements credentials and the web PIN (ARC-CFG-2).

    Extracted from the flat fields of ``AppConfig`` so all secrets live in one
    unit. Secret-bearing fields use ``repr=False`` so they never leak into logs
    or tracebacks; non-secret identifiers (usernames, dev_id) stay visible.
    Mutable — handlers update these in place under ``_config_lock``.
    """

    screenscraper_user: str = ""
    screenscraper_pass: str = field(default="", repr=False)
    screenscraper_dev_id: str = ""
    screenscraper_dev_pass: str = field(default="", repr=False)
    ra_api_key: str = field(default="", repr=False)
    ra_username: str = ""
    web_pin_hash: str = field(default="", repr=False)  # SHA-256(pin+salt); empty = no auth
    web_pin_salt: str = field(default="", repr=False)  # random hex salt for the PIN hash


@dataclass(slots=True)
class InboxConfig:
    """Inbox watcher settings (Pilar 2) extracted from AppConfig (ARC-CFG-4)."""

    path: str = ""  # folder to watch for new files
    target_root: str = ""  # where to place organized files (defaults to library_root)
    auto_process: bool = False  # auto-process when files detected
    delete_source: bool = False  # delete original ZIP after organizing


@dataclass(slots=True)
class BackupConfig:
    """Save-backup settings (S29 / QoL-11) extracted from AppConfig (ARC-CFG-4)."""

    saves_enabled: bool = True  # True = auto-backup before sync/rename overwrites
    saves_keep_n: int = 5  # max versions per save file
    pre_sync: bool = True  # True = crear ZIP de saves antes de cada sync (QoL-11)


@dataclass(slots=True)
class AppConfig:
    project_root: Path
    data_dir: Path
    database_path: Path
    database_path_android: Path
    logs_dir: Path
    catalogs_nointro_dir: Path
    catalogs_redump_dir: Path
    catalogs_arcade_dir: Path
    excluded_directories: tuple[str, ...]
    frontend_asset_extensions: tuple[str, ...]
    save_extensions: tuple[str, ...]  # permanent saves only (.sav, .srm, …)
    state_extensions: tuple[str, ...]  # savestates (.state, .st0, …)
    # From config.toml (optional)
    library_root: Path | None  # root of the ROM+saves library on this PC
    rclone_binary: str
    chdman: str
    adb: str
    web_host: str
    web_port: int
    web_allow_lan: bool  # True = skip PIN guard when binding to a non-loopback address
    web_session_ttl: int  # session cookie TTL in seconds (default 86400 = 24h)
    # Secrets (ScreenScraper + RetroAchievements creds, web PIN) — see CredentialsConfig
    credentials: CredentialsConfig
    # Save-sync settings (cloud remotes, auto-sync daemon, conflict policy) — see SyncConfig
    sync: SyncConfig
    anbernic_root: str  # SD card / Android console filesystem path (e.g. E:\Carpetas anbernic)
    device_name: str  # display name for the Android device (e.g. "Consola Android", "Steam Deck")
    # Inbox watcher settings (Pilar 2) — see InboxConfig
    inbox: InboxConfig
    # Launcher (S28)
    retroarch_path: str  # path to retroarch.exe
    esde_path: str  # path to ES-DE install dir or exe (overrides auto-detect)
    launcher_cores: dict  # platform → libretro core path
    # Save-backup settings (S29 / QoL-11) — see BackupConfig
    backup: BackupConfig
    # Desktop notifications (S37)
    notify_desktop: bool  # True = show Windows toast on sync/health/inbox completion
    # Android emulator path mappings (SYNC-A2)
    # Merged from EMULATOR_SAVE_PATHS_DEFAULT + user [[emulator_paths]] overrides in config.toml
    emulator_paths: dict  # package_name → {name, saves_path, states_path, adb_required, ...}


# Device connectivity check (UX-1/2) extracted to sync/device_detector.py (ARC-CFG-3).


_CONFIG_TOML_TEMPLATE = """\
# ROM Manager Local — user configuration
# Place this file at the root of your project folder (next to .rommgr/).
# All settings are optional; hardcoded defaults are used when omitted.

[library]
# Root folder of your ROM library on this PC.
# Save files (.sav, .srm, .state, etc.) are expected to live alongside the ROMs.
# Used by 'rommgr sync-saves' and 'rommgr sync-status'.
# library_root = "E:/ROMs"

[sync]
# rclone remote path where saves will be mirrored in the cloud.
# The folder structure under library_root is preserved, but only save files are synced.
# remote = "dropbox:/RetroSync/saves"
# Path to the rclone binary (default: "rclone", assumes it is in PATH)
rclone = "rclone"

[screenscraper]
# Your ScreenScraper.fr account credentials (free registration at screenscraper.fr)
# user = "your_username"
# pass = "your_password"

[tools]
# Path to the chdman binary (default: "chdman", assumes it is in PATH)
chdman = "chdman"
# Path to the adb binary from Android Platform Tools (needed for ADB sync mode)
# Download from: developer.android.com/tools/releases/platform-tools
# adb = "tools/adb.exe"

[web]
# Bind to all network interfaces so any device on your LAN can reach the UI.
# Change to "127.0.0.1" to allow only this PC.
host = "0.0.0.0"
port = 7777
# Allow LAN access without a PIN (safe on a trusted home network).
# Set to false and configure a PIN in Settings → Seguridad for public networks.
allow_lan = true

# Android emulator path overrides — one entry per emulator you want to customise.
# Defaults for all known emulators are built-in (see EMULATOR_SAVE_PATHS_DEFAULT in config.py).
# Use this section only when a path differs from the defaults.
# Example:
# [[emulator_paths]]
# package = "com.github.stenzek.duckstation"
# saves_path = "/storage/emulated/0/Android/data/com.github.stenzek.duckstation/files/memcards"
# states_path = "/storage/emulated/0/Android/data/com.github.stenzek.duckstation/files/savestates"
"""


def load_config(project_root: Path | None = None) -> AppConfig:
    root = (project_root or Path.cwd()).resolve()
    data_dir = root / ".rommgr"
    logs_dir = data_dir / "logs"
    database_path = data_dir / "library_pc.db"
    database_path_android = data_dir / "library_android.db"
    catalogs_dir = data_dir / "catalogs"

    toml: dict = {}
    toml_path = root / "config.toml"
    if toml_path.exists():
        with open(toml_path, "rb") as fh:
            toml = tomllib.load(fh)

    lib = toml.get("library", {})
    sync = toml.get("sync", {})
    tools = toml.get("tools", {})
    web = toml.get("web", {})
    ss = toml.get("screenscraper", {})
    ra = toml.get("retroachievements", {})
    inbox_cfg = toml.get("inbox", {})
    android_cfg = toml.get("android", {})
    launchers_cfg = toml.get("launchers", {})
    backup_cfg = toml.get("backup", {})

    # Merge emulator path defaults with any user overrides from [[emulator_paths]]
    emulator_paths: dict = {k: dict(v) for k, v in EMULATOR_SAVE_PATHS_DEFAULT.items()}
    for entry in toml.get("emulator_paths", []):
        if isinstance(entry, dict) and entry.get("package"):
            pkg = entry["package"]
            override = {k: v for k, v in entry.items() if k != "package"}
            if pkg in emulator_paths:
                emulator_paths[pkg].update(override)
            else:
                emulator_paths[pkg] = override

    library_root_raw = lib.get("library_root")
    library_root = Path(library_root_raw) if library_root_raw else None
    anbernic_root = str(lib.get("anbernic_root", ""))
    device_name = str(android_cfg.get("device_name", "Consola Android")) or "Consola Android"

    # Parse [[sync.sources]] — multi-emulator save directories
    raw_sources = sync.get("sources", [])
    sync_sources: list[SyncSource] = []
    for s in raw_sources:
        if isinstance(s, dict) and s.get("local_dir") and s.get("remote"):
            sync_sources.append(
                SyncSource(
                    name=str(s.get("name", s.get("local_dir", "?"))),
                    local_dir=str(s["local_dir"]),
                    remote=str(s["remote"]),
                    sync_all=bool(s.get("sync_all", False)),
                )
            )
    # Backward compat: if no [[sync.sources]] defined, create one from library_root + sync.remote
    if not sync_sources:
        legacy_remote = sync.get("remote", "")
        if legacy_remote and library_root:
            sync_sources.append(
                SyncSource(
                    name="RetroArch",
                    local_dir=str(library_root),
                    remote=legacy_remote,
                )
            )

    # Parse auto_sync_known_devices — stored as comma-separated string or TOML array
    _known_raw = sync.get("auto_sync_known_devices", "")
    if isinstance(_known_raw, list):
        auto_sync_known_devices: list = [str(x).strip() for x in _known_raw if str(x).strip()]
    elif isinstance(_known_raw, str) and _known_raw.strip():
        auto_sync_known_devices = [s.strip() for s in _known_raw.split(",") if s.strip()]
    else:
        auto_sync_known_devices = []

    return AppConfig(
        project_root=root,
        data_dir=data_dir,
        database_path=database_path,
        database_path_android=database_path_android,
        logs_dir=logs_dir,
        catalogs_nointro_dir=catalogs_dir / "nointro",
        catalogs_redump_dir=catalogs_dir / "redump",
        catalogs_arcade_dir=catalogs_dir / "arcade",
        library_root=library_root,
        anbernic_root=anbernic_root,
        device_name=device_name,
        rclone_binary=sync.get("rclone", "rclone"),
        chdman=tools.get("chdman", "chdman"),
        adb=tools.get("adb", "adb"),
        web_host=web.get("host", "0.0.0.0"),
        web_port=int(web.get("port", 7777)),
        web_allow_lan=bool(web.get("allow_lan", True)),
        web_session_ttl=int(web.get("session_ttl", 86400)),
        credentials=CredentialsConfig(
            screenscraper_user=ss.get("user", ""),
            screenscraper_pass=ss.get("pass", ""),
            screenscraper_dev_id=ss.get("dev_id", ""),
            screenscraper_dev_pass=ss.get("dev_pass", ""),
            ra_api_key=ra.get("api_key", ""),
            ra_username=ra.get("username", ""),
            web_pin_hash=str(web.get("pin_hash", "")),
            web_pin_salt=str(web.get("pin_salt", "")),
        ),
        sync=SyncConfig(
            rclone_remote=sync.get("remote", ""),
            auto_sync_enabled=bool(sync.get("auto_sync_enabled", True)),
            auto_sync_direction=str(sync.get("auto_sync_direction", "newest")),
            auto_sync_android_path=str(
                sync.get("auto_sync_android_path", "/storage/emulated/0/RetroArch")
            ),
            auto_sync_known_devices=auto_sync_known_devices,
            conflict_policy=str(sync.get("conflict_policy", "newest")),
            saves_remote=str(sync.get("saves_remote", "")),
            states_remote=str(sync.get("states_remote", "")),
            ra_config_dir=str(sync.get("ra_config_dir", "")),
            ra_config_remote=str(sync.get("ra_config_remote", "")),
            sync_sources=sync_sources,
        ),
        inbox=InboxConfig(
            path=str(inbox_cfg.get("path", "")),
            target_root=str(inbox_cfg.get("target_root", "")),
            auto_process=bool(inbox_cfg.get("auto_process", False)),
            delete_source=bool(inbox_cfg.get("delete_source", False)),
        ),
        retroarch_path=str(launchers_cfg.get("retroarch", tools.get("retroarch", ""))),
        esde_path=str(launchers_cfg.get("esde", "")),
        launcher_cores={k: str(v) for k, v in launchers_cfg.items() if k not in ("retroarch", "esde")},
        backup=BackupConfig(
            saves_enabled=bool(backup_cfg.get("saves_enabled", True)),
            saves_keep_n=int(backup_cfg.get("saves_keep_n", 5)),
            pre_sync=bool(backup_cfg.get("pre_sync", True)),
        ),
        notify_desktop=bool(toml.get("notifications", {}).get("desktop", True)),
        emulator_paths=emulator_paths,
        excluded_directories=(  # noqa: E501
            "Android",
            "BIOS",
            "DCIM",
            "Documents",
            "Movies",
            "Music",
            "Notifications",
            "System Volume Information",
            "backup",
            "recovery_log",
            "media",
            "configs",
            "saves",
            "states",
            "bios",
            "inbox",
            "screenshots",
        ),
        frontend_asset_extensions=(
            ".png",
            ".jpg",
            ".jpeg",
            ".mp4",
            ".xml",
        ),
        save_extensions=(
            ".sav",
            ".srm",
            ".state",
            ".st0",
            ".st1",
            ".st2",
            ".st3",
            ".st4",
            ".st5",
            ".fcs",
            ".dsv",
            ".sps",
            ".psv",
            ".mcr",
            ".mem",
            ".vmp",
            ".eep",
            ".fla",
            ".sra",
            ".sgm",
            ".brm",
            ".nv",
            ".hi",
            ".state1",
            ".state2",
            ".brmc",
            ".ml1",
            # Standalone emulators
            ".mcd",  # DuckStation (PSX memory card)
            ".ps2",  # PCSX2 (PS2 memory card)
            ".gci",  # Dolphin (GameCube memory card slot file)
        ),
        state_extensions=(
            ".state",
            ".state1",
            ".state2",
            ".st0",
            ".st1",
            ".st2",
            ".st3",
            ".st4",
            ".st5",
            ".ppst",  # PPSSPP save state
            ".fcs",
            ".sps",
            ".psv",
            ".hi",
            ".brmc",
            ".ml1",
        ),
    )


def get_adb_sync_sources(config: AppConfig) -> list[dict]:
    """Return ADB sync source descriptors derived from config.emulator_paths.

    Each entry is a dict with:
      - ``name``              : human-readable emulator name
      - ``package``           : Android package name
      - ``android_saves``     : absolute Android saves path, or None
      - ``android_states``    : absolute Android states path, or None
      - ``local_saves``       : local Path for saves (under library_root)
      - ``local_states``      : local Path for states (under library_root), or None
      - ``save_extensions``   : frozenset of save file extensions (or None = use config defaults)
      - ``state_extensions``  : frozenset of state file extensions (or None = use config defaults)

    Emulators with ``accessible: False`` (e.g. Dolphin) are excluded.
    Emulators that don't require ADB (RetroArch, PPSSPP) are excluded — they are
    handled by the SD card sync path.

    Local paths use ``library_root/emulator_saves/<package>/`` to keep each
    emulator's saves isolated and avoid clashing with the existing ROM/save tree.
    """
    if not config.library_root:
        return []

    sources: list[dict] = []
    for pkg, info in config.emulator_paths.items():
        if not info.get("accessible", True):
            continue  # Dolphin etc — ADB permission denied even with USB debugging
        if not info.get("adb_required", True):
            continue  # RetroArch/PPSSPP use SD card path, handled by SD sync daemon

        saves_path = info.get("saves_path")
        states_path = info.get("states_path")
        if not saves_path and not states_path:
            continue  # no known path yet (Mupen64Plus FZ etc.)

        local_root = config.library_root / "emulator_saves" / pkg
        raw_save_ext = info.get("save_extensions")
        raw_state_ext = info.get("state_extensions")

        sources.append(
            {
                "name": info.get("name", pkg),
                "package": pkg,
                "android_saves": saves_path,
                "android_states": states_path,
                "local_saves": local_root / "saves" if saves_path else None,
                "local_states": local_root / "states" if states_path else None,
                "save_extensions": frozenset(raw_save_ext) if raw_save_ext else None,
                "state_extensions": frozenset(raw_state_ext) if raw_state_ext else None,
            }
        )
    return sources


def _path_exists(p: str) -> bool:
    """Return True if p resolves to an existing path (handles relative paths too)."""
    try:
        return Path(p).exists()
    except Exception:
        return False


def validate(config: AppConfig) -> list[dict]:
    """Return a list of configuration warnings (non-fatal issues).

    Each entry is a dict with keys:
      - ``level``: ``"warning"`` or ``"info"``
      - ``field``:  the config field name (for highlighting in the UI)
      - ``message``: human-readable Spanish description
    """
    warnings: list[dict] = []

    def warn(field: str, msg: str, level: str = "warning") -> None:
        warnings.append({"level": level, "field": field, "message": msg})

    # library_root
    if config.library_root is None:
        warn(
            "library_root",
            "Ruta de biblioteca no configurada. Las herramientas no podrán escanear ROMs.",
        )
    elif not config.library_root.exists():
        warn("library_root", f"La carpeta de biblioteca no existe: {config.library_root}")

    # anbernic_root
    if config.anbernic_root and not _path_exists(config.anbernic_root):
        warn(
            "anbernic_root",
            f"La ruta de la consola no existe o no está conectada: {config.anbernic_root}",
            "info",
        )

    # chdman
    if config.chdman and config.chdman != "chdman" and not _path_exists(config.chdman):
        warn(
            "chdman", f"chdman no encontrado en: {config.chdman}. La conversión CHD no funcionará."
        )

    # adb
    if config.adb and config.adb != "adb" and not _path_exists(config.adb):
        warn("adb", f"adb no encontrado en: {config.adb}. El Cable Sync no funcionará.")

    # web_port
    if not (1 <= config.web_port <= 65535):
        warn("web_port", f"Puerto inválido: {config.web_port}. Debe estar entre 1 y 65535.")

    # screenscraper — partial config
    if config.credentials.screenscraper_user and not config.credentials.screenscraper_pass:
        warn("screenscraper_pass", "Usuario de ScreenScraper configurado pero contraseña vacía.")
    if config.credentials.screenscraper_pass and not config.credentials.screenscraper_user:
        warn("screenscraper_user", "Contraseña de ScreenScraper configurada pero usuario vacío.")

    # retroachievements
    if not config.credentials.ra_api_key:
        warn(
            "ra_api_key",
            "API key de RetroAchievements no configurada. Necesaria para el informe de logros.",
            "info",
        )

    # retroarch_path — exe + cores
    if config.retroarch_path:
        ra_exe = Path(config.retroarch_path)
        if not ra_exe.exists():
            warn("retroarch_path", f"RetroArch no encontrado en: {config.retroarch_path}")
        else:
            cores_dir = ra_exe.parent / "cores"
            if not cores_dir.exists():
                warn(
                    "retroarch_path",
                    "Carpeta cores/ no encontrada. Instala cores desde RetroArch → Online Updater.",
                    "info",
                )
            elif not any(cores_dir.glob("*_libretro.dll")):
                warn(
                    "retroarch_path",
                    "No hay cores instalados en cores/. Descárgalos desde RetroArch → Online Updater.",
                    "info",
                )

    return warnings


def write_config_toml(project_root: Path, updates: dict) -> None:
    """Write (or update) config.toml with the given key→value pairs.

    *updates* is a flat dict of dotted keys, e.g.::

        {"library.library_root": "E:/ROMs", "sync.remote": "dropbox:/RetroSync/saves"}

    Sections/keys not present in *updates* are preserved as-is.
    """
    toml_path = project_root / "config.toml"

    # Read existing content (or empty dict)
    existing: dict = {}
    if toml_path.exists():
        with open(toml_path, "rb") as fh:
            existing = tomllib.load(fh)

    # Apply updates
    for dotted_key, value in updates.items():
        parts = dotted_key.split(".", 1)
        if len(parts) == 2:
            section, key = parts
            existing.setdefault(section, {})[key] = value
        else:
            existing[dotted_key] = value

    def _fmt(v: object) -> str | None:
        """Return TOML-formatted value string, or None to emit as a comment."""
        if v is None or v == "":
            return None
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, int):
            return str(v)
        if isinstance(v, list):
            items = ", ".join(
                '"{}"'.format(str(x).replace("\\", "\\\\").replace('"', '\\"')) for x in v
            )
            return f"[{items}]"
        escaped = str(v).replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    def _emit(lines: list[str], k: str, v: object) -> None:
        fv = _fmt(v)
        lines.append(f'# {k} = ""\n' if fv is None else f"{k} = {fv}\n")

    # Serialise back to TOML (simple writer — no comment preservation)
    lines: list[str] = ["# ROM Manager Local — user configuration\n"]
    deferred_aot: list[tuple[str, str, list]] = []  # (section, key, list-of-dicts)

    for section, contents in existing.items():
        if isinstance(contents, dict):
            regular = {
                k: v
                for k, v in contents.items()
                if not (isinstance(v, list) and v and isinstance(v[0], dict))
            }
            aot = {
                k: v
                for k, v in contents.items()
                if isinstance(v, list) and v and isinstance(v[0], dict)
            }
            if regular:
                lines.append(f"\n[{section}]\n")
                for k, v in regular.items():
                    _emit(lines, k, v)
            for k, tables in aot.items():
                deferred_aot.append((section, k, tables))
        else:
            fv = _fmt(contents)
            lines.append(f'# {section} = ""\n' if fv is None else f"{section} = {fv}\n")

    # Array-of-tables written after all regular sections (TOML requirement)
    for section, key, tables in deferred_aot:
        for table in tables:
            lines.append(f"\n[[{section}.{key}]]\n")
            for k, v in table.items():
                _emit(lines, k, v)

    toml_path.write_text("".join(lines), encoding="utf-8")
