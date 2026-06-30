"""Interactive setup wizard — rommgr init-config."""
from __future__ import annotations

import getpass
import shutil
import sys
from pathlib import Path

_COMMON_LIBRARY_ROOTS = [
    Path("D:/ROMs"),
    Path("E:/ROMs"),
    Path.home() / "ROMs",
    Path.home() / "Documents" / "ROMs",
]

_EMULATOR_PRESETS = [
    {
        "name": "RetroArch",
        "local": Path.home() / "AppData" / "Roaming" / "RetroArch" / "saves",
        "remote_suffix": "retroarch",
    },
    {
        "name": "DuckStation (PSX)",
        "local": Path.home() / "Documents" / "DuckStation" / "memcards",
        "remote_suffix": "duckstation",
    },
    {
        "name": "PCSX2 (PS2)",
        "local": Path.home() / "Documents" / "PCSX2" / "memcards",
        "remote_suffix": "pcsx2",
    },
    {
        "name": "PPSSPP (PSP)",
        "local": Path.home() / "Documents" / "PPSSPP" / "PSP" / "SAVEDATA",
        "remote_suffix": "ppsspp",
        "sync_all": True,
    },
    {
        "name": "Dolphin (GC/Wii)",
        "local": Path.home() / "Documents" / "Dolphin Emulator",
        "remote_suffix": "dolphin",
        "sync_all": True,
    },
]


def _ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        val = input(f"{prompt}{hint}: ").strip()
        return val or default
    except (EOFError, KeyboardInterrupt):
        print("\nCancelado.")
        sys.exit(0)


def _ask_yn(prompt: str, default: bool = False) -> bool:
    hint = "[S/n]" if default else "[s/N]"
    try:
        val = input(f"{prompt} {hint}: ").strip().lower()
        return (val in ("s", "si", "sí", "y", "yes")) if val else default
    except (EOFError, KeyboardInterrupt):
        print("\nCancelado.")
        sys.exit(0)


def _ask_secret(prompt: str) -> str:
    try:
        return getpass.getpass(f"{prompt} (Enter para omitir): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelado.")
        sys.exit(0)


def _detect_tool(name: str, project_root: Path) -> str:
    exe = name + (".exe" if sys.platform == "win32" else "")
    local = project_root / "tools" / exe
    if local.exists():
        return str(local)
    return name if shutil.which(name) else ""


def run_wizard(project_root: Path) -> int:
    toml_path = project_root / "config.toml"

    if toml_path.exists():
        print(f"Ya existe config.toml en {toml_path}")
        if not _ask_yn("¿Sobreescribir con nueva configuración?", default=False):
            print("Sin cambios. Ejecuta 'rommgr serve' para arrancar.")
            return 0

    print("\n=== Retro Vault — Configuración inicial ===\n")

    # ── 1. Biblioteca ─────────────────────────────────────────────────────────
    print("1. Biblioteca de ROMs")
    default_lib = next((str(p) for p in _COMMON_LIBRARY_ROOTS if p.exists()), "")
    library_root = _ask("   Carpeta raíz de ROMs", default_lib)
    print()

    # ── 2. Herramientas ───────────────────────────────────────────────────────
    print("2. Herramientas externas")
    chdman = _detect_tool("chdman", project_root)
    adb    = _detect_tool("adb",    project_root)
    rclone = _detect_tool("rclone", project_root)

    print(f"   chdman  → {chdman or 'no encontrado (ejecuta scripts\\download-tools.ps1)'}")
    print(f"   adb     → {adb    or 'no encontrado (solo necesario para Cable Sync por USB)'}")
    if rclone:
        print(f"   rclone  → {rclone}")
    else:
        rclone = _ask("   rclone no encontrado. Ruta al binario (Enter para omitir cloud sync)", "")
    print()

    # ── 3. ScreenScraper ──────────────────────────────────────────────────────
    print("3. ScreenScraper — metadatos y carátulas (cuenta gratuita en screenscraper.fr)")
    ss_user = _ask("   Usuario", "")
    ss_pass = _ask_secret("   Contraseña") if ss_user else ""
    print()

    # ── 4. RetroAchievements ──────────────────────────────────────────────────
    print("4. RetroAchievements — API key en retroachievements.org → Settings → Web API Key")
    ra_key  = _ask_secret("   API key")
    ra_user = _ask("   Usuario RA", "") if ra_key else ""
    print()

    # ── 5. Cloud Sync ─────────────────────────────────────────────────────────
    sync_sources: list[dict] = []
    detected = [p for p in _EMULATOR_PRESETS if p["local"].exists()]
    if detected:
        print("5. Cloud Sync — emuladores detectados en este PC")
        base_remote = ""
        for preset in detected:
            if not _ask_yn(f"   ¿Añadir sync para {preset['name']}? ({preset['local']})", default=True):
                continue
            if not base_remote:
                base_remote = _ask(
                    "   Remote rclone base (p. ej. dropbox:/RetroSync/saves)", ""
                )
            source: dict = {
                "name": preset["name"],
                "local_dir": str(preset["local"]),
                "remote": f"{base_remote}/{preset['remote_suffix']}" if base_remote else "",
            }
            if preset.get("sync_all"):
                source["sync_all"] = True
            sync_sources.append(source)
        print()
    else:
        print("5. Cloud Sync — ningún emulador detectado en rutas estándar.")
        print("   Añade fuentes de sync más tarde en Ajustes → Sync.\n")

    # ── Guardar ───────────────────────────────────────────────────────────────
    _write_toml(toml_path, library_root, chdman, adb, rclone or "rclone",
                ss_user, ss_pass, ra_key, ra_user, sync_sources)

    print(f"✓ Guardado en {toml_path}\n")
    print("Siguiente paso:")
    print("  rommgr serve   →  abre http://127.0.0.1:7777")
    return 0


def _write_toml(
    path: Path,
    library_root: str,
    chdman: str,
    adb: str,
    rclone: str,
    ss_user: str,
    ss_pass: str,
    ra_key: str,
    ra_user: str,
    sync_sources: list[dict],
) -> None:
    def q(s: str) -> str:
        return '"{}"'.format(s.replace("\\", "\\\\").replace('"', '\\"'))

    def kv(k: str, v: str) -> str:
        return f"{k} = {q(v)}\n" if v else f"# {k} = \"\"\n"

    lines = ["# Retro Vault — configuración generada por init-config\n"]
    lines += ["\n[library]\n",    kv("library_root", library_root)]
    lines += ["\n[tools]\n",      kv("chdman", chdman), kv("adb", adb)]
    lines += ["\n[sync]\n",       kv("rclone", rclone)]

    for src in sync_sources:
        lines.append("\n[[sync.sources]]\n")
        lines.append(f'name      = {q(src["name"])}\n')
        lines.append(f'local_dir = {q(src["local_dir"])}\n')
        lines.append(f'remote    = {q(src["remote"])}\n')
        if src.get("sync_all"):
            lines.append("sync_all  = true\n")

    lines += ["\n[screenscraper]\n",     kv("user", ss_user), kv("pass", ss_pass)]
    lines += ["\n[retroachievements]\n", kv("api_key", ra_key), kv("username", ra_user)]
    lines += ["\n[web]\n", 'host = "0.0.0.0"\n', "port = 7777\n", "allow_lan = true\n"]

    path.write_text("".join(lines), encoding="utf-8")
