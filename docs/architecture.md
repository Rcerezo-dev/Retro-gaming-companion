# Arquitectura técnica — Retro Vault

> Documentación técnica del proyecto. Ver `CLAUDE.md` para reglas de trabajo y patrones críticos.

---

## Stack técnico

- **Python 3.12** (Conda: `C:\Users\rammu\anaconda3\envs\rom_manager`)
- **SQLite** via `sqlite3` stdlib — BD en `.rommgr/library.db`
- **tomllib** para `config.toml`
- **rclone** — binario externo para cloud sync
- **chdman** — `tools/chdman.exe` v0.286 (NO en PATH)
- **adb** — `tools/adb.exe` para Cable Sync
- **Sin dependencias externas de runtime** (solo stdlib)
- Lanzador: `scripts\rommgr.cmd`
- Ejecución directa: `C:\Users\rammu\anaconda3\envs\rom_manager\python.exe -m rom_manager <cmd>`

---

## Estructura de módulos

```
src/rom_manager/
  cli.py                          # Entrypoint CLI
  config.py                       # AppConfig; carga config.toml
  database/
    schema.py                     # tablas: scan_runs, games, saves, assets, ...
    repository.py                 # LibraryRepository — toda la lógica BD
  detection/
    file_classifier.py            # ROM / save / asset / system / unknown
    platform_detector.py          # GBA, PSX, SNES... por extensión/carpeta
    region_parser.py              # (USA), [Europe], etc.
  hashing/hash_calculator.py      # SHA1+MD5+CRC32, chunks 1 MB
  scanner/rom_scanner.py          # scan_library(); incremental por mtime
  catalog/
    catalog_loader.py             # DAT XML Logiqx (No-Intro/Redump)
    matcher.py                    # CatalogMatcher; confianza high/medium/low
  planner/operation_planner.py    # build_plan(); FormatOptions
  renamer/file_renamer.py         # rename_rom_with_saves() — atómico con rollback
  converters/
    chd_converter.py              # cue→chd vía chdman
    zip_extractor.py              # extrae .zip; omite disc sets (→CHD)
  utils/
    m3u_generator.py              # genera .m3u para multi-disco
    multidisc_verifier.py
    orphan_finder.py              # saves sin ROM asociada
    health_checker.py             # re-hashea ROMs vs SHA1 almacenado
  sync/
    rclone_transport.py           # wrapper rclone
    save_syncer.py                # lógica de sync con política de conflictos
    conflict_resolver.py
    sync_log.py
    adb_transport.py              # ADB pull/push para Cable Sync
  scraper/
    screenscraper.py              # REST ScreenScraper; fallback búsqueda por nombre
    platform_ids.py               # plataforma → ScreenScraper ID
    gamelist_writer.py            # genera gamelist.xml (formato EmulationStation)
    pegasus_writer.py             # genera metadata.pegasus.txt (Pegasus frontend)
  retroachievements/
    ra_client.py                  # API_GetGameList; caché .rommgr/ra_cache/ 1 semana
    ra_checker.py                 # cross-reference MD5 + búsqueda por título
    ra_platform_ids.py            # plataforma → RA console ID (~30 plataformas)
  web/
    server.py                     # HTTP server stdlib; todos los endpoints
    frontend.py                   # SPA HTML+JS inline (una sola cadena Python)
```

---

## Estructura de biblioteca en disco

```
<library_root>/           (PC: E:\Carpetas anbernic\)
│
├── nes/   snes/   n64/   gb/   gbc/   gba/   nds/   3ds/
├── gamecube/   wii/   wiiu/   switch/
├── psx/   ps2/   ps3/   psp/   psvita/
├── megadrive/   mastersystem/   gamegear/   sega32x/   segacd/
├── dreamcast/   saturn/
├── atari2600/   atari5200/   atari7800/   atarilynx/   atarijaguar/
├── neogeo/   pcengine/
│   └── (cada carpeta tiene media/images/ y media/videos/)
│
├── saves/
│   ├── gba/       ← saves de Game Boy Advance (Game.sav, Game.srm…)
│   ├── psx/       ← saves de PlayStation
│   ├── snes/      ← saves de SNES
│   └── …          ← una subcarpeta por cada plataforma (27 en total)
│
├── states/
│   ├── gba/       ← savestates de GBA (Game.state, Game.state0…)
│   ├── psx/
│   └── …          ← misma estructura que saves/
│
├── bios/          ← BIOS (scph1001.bin, gba_bios.bin…) — no sincronizadas
├── inbox/         ← ZIPs nuevos sin organizar (Pilar 2)
└── screenshots/   ← capturas en-juego
```

**Regla crítica:** los saves NUNCA van en `saves/` directamente — siempre en `saves/{platform}/`.
Esto garantiza que los saves de distintas consolas no se mezclen y que el sync sea auditable.

La consola Android debe replicar la misma estructura bajo su `android_root`.
RetroArch Android guarda en `/storage/emulated/0/RetroArch/saves/` y `.../states/` por defecto (plano).
Para que coincida con esta estructura, configura en RetroArch → Ajustes → Directorio:
- "Directorio de archivos de guardado" → activar "Usar directorio del sistema" (crea subcarpetas por core automáticamente)

---

## config.toml de referencia

```toml
[library]
library_root = "E:\\Carpetas anbernic"

[sync]
remote = "dropbox:/RetroSync/saves"   # legacy; usar [[sync.sources]] para multi-emulador

[[sync.sources]]
name      = "RetroArch"
local_dir = "E:\\Carpetas anbernic\\saves"
remote    = "dropbox:/RetroSync/saves"

[tools]
chdman = "tools/chdman.exe"

[web]
host = "127.0.0.1"   # cambiar a "0.0.0.0" para acceder desde la consola Android
port = 7777

[screenscraper]
user = "tu_usuario"
pass = "tu_contraseña"

[retroachievements]
api_key = ""   # retroachievements.org → Settings → Web API Key
```

---

## Base de datos

Tablas principales en `.rommgr/library.db`:

| Tabla | Propósito |
|-------|-----------|
| `games` | Un registro por archivo ROM/save/asset. Columnas clave: `source_path`, `platform`, `canonical_title`, `sha1`, `md5`, `crc32`, `match_confidence`, `play_status`, `last_played_at` |
| `scan_runs` | Historial de escaneos con timestamp y ruta |
| `assets` | Metadatos de ScreenScraper (carátulas, descripciones, etc.) |
| `save_sync_log` | Log de operaciones de sync |

Índices activos: `idx_games_sha1`, `idx_games_platform`, `idx_games_file_type`, `idx_games_canonical_title`, `idx_games_play_status`, `idx_games_match_confidence`, `idx_games_last_played`.

---

## Dispositivos

| Dispositivo | OS | Emulador | Conexión al PC |
|-------------|----|---------|----|
| PC (Windows 10/11) | Windows | RetroArch `C:\RetroArch-Win64\` + EmulationStation | — |
| Consola Android (RG 556) | Android puro (NO ArkOS/JELOS) | RetroArch Android | Cable USB (ADB) o SD card |

Rutas de RetroArch PC:
- Ejecutable: `C:\RetroArch-Win64\retroarch.exe`
- Cores: `C:\RetroArch-Win64\cores\`
- Saves configurados en: `E:\Carpetas anbernic\saves\` (ajustar en RetroArch → Ajustes → Directorio)

Rutas de RetroArch en Android:
- Saves: `/storage/emulated/0/RetroArch/saves/`
- States: `/storage/emulated/0/RetroArch/states/`

---

## EmulationStation (PC)

Frontend instalado en `C:\Program Files (x86)\EmulationStation\emulationstation.exe` (v2.0.1a).

Configuración en `C:\Users\rammu\.emulationstation\`:
- `es_systems.cfg` — sistemas, rutas de ROMs y comandos de lanzador
- `gamelists\{sistema}\gamelist.xml` — metadatos e imágenes por sistema
- `themes\` — temas visuales (tema activo: `simple`)

**Integración con Retro Vault:**
- `gamelist_writer.py` escribe `gamelist.xml` dentro de cada carpeta de plataforma (`E:\Carpetas anbernic\{sistema}\gamelist.xml`). ES lo lee desde ahí automáticamente.
- Las imágenes de carátulas se escriben en `E:\Carpetas anbernic\{sistema}\media\images\` y el `gamelist.xml` las referencia con rutas relativas.

**Sistemas configurados en ES y cores usados:**

| Sistema | Core RetroArch | Nota |
|---------|---------------|------|
| NES | `nestopia_libretro.dll` | |
| SNES | `snes9x2010_libretro.dll` | |
| GB / GBC | `gambatte_libretro.dll` | |
| GBA | `mgba_libretro.dll` | |
| N64 | `mupen64plus_next_libretro.dll` | |
| NDS | `melondsds_libretro.dll` | |
| 3DS | `citra_libretro.dll` | Sin tema propio; usa fallback `simple` |
| PSX | `mednafen_psx_libretro.dll` | |
| PS2 | `pcsx2_libretro.dll` | |
| PSP | `ppsspp_libretro.dll` | |
| Master System | `genesis_plus_gx_libretro.dll` | Descargar via RetroArch → Online Updater |
| Mega Drive | `blastem_libretro.dll` | |
| Game Gear | `genesis_plus_gx_libretro.dll` | Descargar via RetroArch → Online Updater |
| Saturn | `mednafen_saturn_libretro.dll` | |
| Dreamcast | `flycast_libretro.dll` | |
| Arcade | `fbneo_libretro.dll` | Tema ES: `mame` |

---

## RetroAchievements — detalles API

- Endpoint: `GET https://retroachievements.org/API/API_GetGameList.php?i={console_id}&h=1&f=1&y={api_key}`
- Hash principal: **MD5** (no SHA1)
- Caché: `.rommgr/ra_cache/ra_hashes_{console_id}.json`, TTL 1 semana
- Si juego no encontrado → búsqueda alternativa por título normalizado

---

## Convenciones de código

- `from __future__ import annotations` en todos los módulos
- `@dataclass(slots=True)` para estructuras de datos internas
- Extensiones de archivo siempre en minúsculas
- `source_path` siempre como `str(path.resolve())`
- Timestamps en UTC, ISO-8601, sin microsegundos
- `repository.connect()` para lecturas (no `_connect()`)
- `repository.batch()` para escrituras en bulk
