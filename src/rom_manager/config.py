from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class SyncSource:
    """One emulator's save directory paired with its cloud remote path."""
    name: str
    local_dir: str
    remote: str
    sync_all: bool = False  # True → sync every file (no extension filter); use for PPSSPP/Dolphin etc.


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
    save_extensions: tuple[str, ...]
    # From config.toml (optional)
    library_root: Path | None   # root of the ROM+saves library on this PC
    rclone_remote: str
    rclone_binary: str
    chdman: str
    adb: str
    web_host: str
    web_port: int
    web_pin_hash: str   # SHA-256(pin+salt); empty = no auth
    web_pin_salt: str   # random hex salt for the PIN hash
    web_session_ttl: int  # session cookie TTL in seconds (default 86400 = 24h)
    screenscraper_user: str
    screenscraper_pass: str
    screenscraper_dev_id: str
    screenscraper_dev_pass: str
    ra_api_key: str
    # Auto-sync daemon settings
    auto_sync_enabled: bool
    auto_sync_direction: str        # "newest" | "pc_to_anbernic" | "anbernic_to_pc"
    auto_sync_android_path: str     # Android RetroArch root path
    auto_sync_known_devices: list   # serial numbers; empty = any device
    conflict_policy: str            # "newest" | "keep_pc" | "keep_android" | "ask"
    anbernic_root: str              # SD card / Android console filesystem path (e.g. E:\Carpetas anbernic)
    device_name: str                # display name for the Android device (e.g. "Consola Android", "Steam Deck")
    # Inbox (Pilar 2) settings
    inbox_path: str                 # folder to watch for new files
    inbox_target_root: str          # where to place organized files (defaults to library_root)
    inbox_auto_process: bool        # auto-process when files detected
    inbox_delete_source: bool       # delete original ZIP after organizing
    # Multi-source cloud sync
    sync_sources: list[SyncSource]  # one entry per emulator; populated from [[sync.sources]] in config.toml
    # Launcher (S28)
    retroarch_path: str             # path to retroarch.exe
    launcher_cores: dict            # platform → libretro core path
    # Save backup (S29)
    backup_saves_enabled: bool      # True = auto-backup before sync/rename overwrites
    backup_saves_keep_n: int        # max versions per save file (default 5)


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
host = "127.0.0.1"
port = 7777
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

    library_root_raw = lib.get("library_root")
    library_root = Path(library_root_raw) if library_root_raw else None
    anbernic_root = str(lib.get("anbernic_root", ""))
    device_name = str(android_cfg.get("device_name", "Consola Android")) or "Consola Android"

    # Parse [[sync.sources]] — multi-emulator save directories
    raw_sources = sync.get("sources", [])
    sync_sources: list[SyncSource] = []
    for s in raw_sources:
        if isinstance(s, dict) and s.get("local_dir") and s.get("remote"):
            sync_sources.append(SyncSource(
                name=str(s.get("name", s.get("local_dir", "?"))),
                local_dir=str(s["local_dir"]),
                remote=str(s["remote"]),
                sync_all=bool(s.get("sync_all", False)),
            ))
    # Backward compat: if no [[sync.sources]] defined, create one from library_root + sync.remote
    if not sync_sources:
        legacy_remote = sync.get("remote", "")
        if legacy_remote and library_root:
            sync_sources.append(SyncSource(
                name="RetroArch",
                local_dir=str(library_root),
                remote=legacy_remote,
            ))

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
        rclone_remote=sync.get("remote", ""),
        rclone_binary=sync.get("rclone", "rclone"),
        chdman=tools.get("chdman", "chdman"),
        adb=tools.get("adb", "adb"),
        web_host=web.get("host", "127.0.0.1"),
        web_port=int(web.get("port", 7777)),
        web_pin_hash=str(web.get("pin_hash", "")),
        web_pin_salt=str(web.get("pin_salt", "")),
        web_session_ttl=int(web.get("session_ttl", 86400)),
        screenscraper_user=ss.get("user", ""),
        screenscraper_pass=ss.get("pass", ""),
        screenscraper_dev_id=ss.get("dev_id", ""),
        screenscraper_dev_pass=ss.get("dev_pass", ""),
        ra_api_key=ra.get("api_key", ""),
        auto_sync_enabled=bool(sync.get("auto_sync_enabled", True)),
        auto_sync_direction=str(sync.get("auto_sync_direction", "newest")),
        auto_sync_android_path=str(sync.get("auto_sync_android_path", "/storage/emulated/0/RetroArch")),
        auto_sync_known_devices=auto_sync_known_devices,
        conflict_policy=str(sync.get("conflict_policy", "newest")),
        inbox_path=str(inbox_cfg.get("path", "")),
        inbox_target_root=str(inbox_cfg.get("target_root", "")),
        inbox_auto_process=bool(inbox_cfg.get("auto_process", False)),
        inbox_delete_source=bool(inbox_cfg.get("delete_source", False)),
        sync_sources=sync_sources,
        retroarch_path=str(launchers_cfg.get("retroarch", tools.get("retroarch", ""))),
        launcher_cores={k: str(v) for k, v in launchers_cfg.items() if k != "retroarch"},
        backup_saves_enabled=bool(backup_cfg.get("saves_enabled", True)),
        backup_saves_keep_n=int(backup_cfg.get("saves_keep_n", 5)),
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
            ".dat",
            ".sgm",
            ".brm",
            ".nv",
            ".hi",
            ".fs",
            ".state1",
            ".state2",
            ".brmc",
            ".ml1",
            # Standalone emulators
            ".mcd",   # DuckStation (PSX memory card)
            ".ps2",   # PCSX2 (PS2 memory card)
            ".gci",   # Dolphin (GameCube memory card slot file)
            ".ppst",  # PPSSPP save state
        ),
    )


def _path_exists(p: str) -> bool:
    """Return True if p resolves to an existing path (handles relative paths too)."""
    try:
        return Path(p).exists()
    except Exception:
        return False


def validate(config: "AppConfig") -> list[dict]:
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
        warn("library_root", "Ruta de biblioteca no configurada. Las herramientas no podrán escanear ROMs.")
    elif not config.library_root.exists():
        warn("library_root", f"La carpeta de biblioteca no existe: {config.library_root}")

    # anbernic_root
    if config.anbernic_root and not _path_exists(config.anbernic_root):
        warn("anbernic_root", f"La ruta de la consola no existe o no está conectada: {config.anbernic_root}", "info")

    # chdman
    if config.chdman and config.chdman != "chdman" and not _path_exists(config.chdman):
        warn("chdman", f"chdman no encontrado en: {config.chdman}. La conversión CHD no funcionará.")

    # adb
    if config.adb and config.adb != "adb" and not _path_exists(config.adb):
        warn("adb", f"adb no encontrado en: {config.adb}. El Cable Sync no funcionará.")

    # web_port
    if not (1 <= config.web_port <= 65535):
        warn("web_port", f"Puerto inválido: {config.web_port}. Debe estar entre 1 y 65535.")

    # screenscraper — partial config
    if config.screenscraper_user and not config.screenscraper_pass:
        warn("screenscraper_pass", "Usuario de ScreenScraper configurado pero contraseña vacía.")
    if config.screenscraper_pass and not config.screenscraper_user:
        warn("screenscraper_user", "Contraseña de ScreenScraper configurada pero usuario vacío.")

    # retroachievements
    if not config.ra_api_key:
        warn("ra_api_key", "API key de RetroAchievements no configurada. Necesaria para el informe de logros.", "info")

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
                '"{}"'.format(str(x).replace("\\", "\\\\").replace('"', '\\"'))
                for x in v
            )
            return f"[{items}]"
        escaped = str(v).replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    def _emit(lines: list[str], k: str, v: object) -> None:
        fv = _fmt(v)
        lines.append(f"# {k} = \"\"\n" if fv is None else f"{k} = {fv}\n")

    # Serialise back to TOML (simple writer — no comment preservation)
    lines: list[str] = ["# ROM Manager Local — user configuration\n"]
    deferred_aot: list[tuple[str, str, list]] = []  # (section, key, list-of-dicts)

    for section, contents in existing.items():
        if isinstance(contents, dict):
            regular = {
                k: v for k, v in contents.items()
                if not (isinstance(v, list) and v and isinstance(v[0], dict))
            }
            aot = {
                k: v for k, v in contents.items()
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
            lines.append(f"# {section} = \"\"\n" if fv is None else f"{section} = {fv}\n")

    # Array-of-tables written after all regular sections (TOML requirement)
    for section, key, tables in deferred_aot:
        for table in tables:
            lines.append(f"\n[[{section}.{key}]]\n")
            for k, v in table.items():
                _emit(lines, k, v)

    toml_path.write_text("".join(lines), encoding="utf-8")
