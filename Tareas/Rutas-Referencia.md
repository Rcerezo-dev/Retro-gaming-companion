# Rutas de Referencia — Retro Vault

> Archivo de referencia para no tener que buscar rutas en cada sesión.
> Actualizar si cambia algo.

---

## Biblioteca de ROMs

| Descripción | Ruta |
|-------------|------|
| Raíz de la biblioteca | `E:\Carpetas anbernic\` |
| PSX | `E:\Carpetas anbernic\psx\` |
| PS2 | `E:\Carpetas anbernic\ps2\` |
| PSP | `E:\Carpetas anbernic\psp\` |
| NES | `E:\Carpetas anbernic\nes\` |
| SNES | `E:\Carpetas anbernic\snes\` |
| N64 | `E:\Carpetas anbernic\n64\` |
| GB | `E:\Carpetas anbernic\gb\` |
| GBC | `E:\Carpetas anbernic\gbc\` |
| GBA | `E:\Carpetas anbernic\gba\` |
| NDS | `E:\Carpetas anbernic\nds\` |
| 3DS | `E:\Carpetas anbernic\3ds\` |
| GameCube | `E:\Carpetas anbernic\gamecube\` |
| Wii | `E:\Carpetas anbernic\wii\` |
| Sega Master System | `E:\Carpetas anbernic\mastersystem\` |
| Mega Drive | `E:\Carpetas anbernic\megadrive\` |
| Game Gear | `E:\Carpetas anbernic\gamegear\` |
| Saturn | `E:\Carpetas anbernic\saturn\` |
| Dreamcast | `E:\Carpetas anbernic\dreamcast\` |
| Arcade (FBNeo) | `E:\Carpetas anbernic\arcade\` |

### Assets (carátulas scrapeadas)
Las imágenes se guardan junto a los ROMs, en subcarpeta `media/images/`:
- Ejemplo PSX: `E:\Carpetas anbernic\psx\media\images\NombreJuego.jpg`
- Formato: `{stem del ROM}.png` o `.jpg` según ScreenScraper

---

## Emuladores (PC)

| Plataforma | Ejecutable |
|-----------|------------|
| RetroArch (PC) | `C:\RetroArch-Win64\retroarch.exe` |
| Cores RetroArch | `C:\RetroArch-Win64\cores\` |
| PSX — DuckStation | `E:\Emuladores\Duckstation\duckstation-qt-x64-ReleaseLTCG.exe` |
| PS2 — PCSX2 | `E:\Emuladores\PCSX2\pcsx2-qt.exe` |
| GameCube/Wii — Dolphin | `E:\Emuladores\Dolphin (GC, Wii)\Dolphin.exe` |

---

## EmulationStation DE (ES-DE)

| Descripción | Ruta |
|-------------|------|
| Config ES-DE (gamelists, settings) | `C:\Users\rammu\.emulationstation\` |
| es_systems.cfg (sistemas definidos) | `C:\Users\rammu\.emulationstation\es_systems.cfg` |
| es_settings.xml | `C:\Users\rammu\.emulationstation\es_settings.xml` |
| Gamelists | `C:\Users\rammu\.emulationstation\gamelists\{sistema}\gamelist.xml` |
| Gamelist PSX | `C:\Users\rammu\.emulationstation\gamelists\psx\gamelist.xml` |
| Themes | `C:\Users\rammu\.emulationstation\themes\` |

### Notas sobre gamelists
- `gamelist_writer.py` escribe **dos copias** por plataforma:
  1. `E:\Carpetas anbernic\{plataforma}\gamelist.xml` — paths relativos (para ES-DE y Pegasus)
  2. `C:\Users\rammu\.emulationstation\gamelists\{plataforma}\gamelist.xml` — paths absolutos (EmulationStation clásico)
- Las imágenes se referencian como `./media/images/NombreJuego.jpg` en la copia junto a ROMs

---

## Extensiones por plataforma (es_systems.cfg)

| Sistema | Extensiones |
|---------|-------------|
| PSX | `.cue .chd .pbp .m3u .img .bin` (y mayúsculas) |
| PS2 | `.iso .chd .bin .img .cso .zso .m3u` |
| PSP | `.iso .cso .pbp .chd .zip` |
| Saturn | `.cue .chd .iso .m3u .bin .mdf .img` |
| Dreamcast | `.cdi .gdi .chd .m3u .bin .iso .elf` |
| N64 | `.z64 .n64 .v64` |

---

## Retro Vault (la app)

| Descripción | Ruta |
|-------------|------|
| Proyecto | `C:\Users\rammu\Documents\projects\Retro_gaming_app\` |
| Config | `C:\Users\rammu\Documents\projects\Retro_gaming_app\config.toml` |
| Base de datos SQLite | `C:\Users\rammu\Documents\projects\Retro_gaming_app\.rommgr\library.db` |
| Caché RetroAchievements | `C:\Users\rammu\Documents\projects\Retro_gaming_app\.rommgr\ra_cache\` |
| Entorno Conda | `C:\Users\rammu\anaconda3\envs\rom_manager\` |
| Lanzador | `C:\Users\rammu\Documents\projects\Retro_gaming_app\scripts\rommgr.cmd` |
| chdman | `C:\Users\rammu\Documents\projects\Retro_gaming_app\tools\chdman.exe` |
| adb | `C:\Users\rammu\Documents\projects\Retro_gaming_app\tools\adb.exe` |
| Interfaz web | `http://127.0.0.1:7777` |

---

## Android (Anbernic RG 556)

| Descripción | Ruta en Android |
|-------------|-----------------|
| Saves RetroArch | `/storage/emulated/0/RetroArch/saves/` |
| States RetroArch | `/storage/emulated/0/RetroArch/states/` |
| ROMs | `/storage/emulated/0/ROMs/{plataforma}/` |

---

## Sync (rclone)

| Descripción | Valor |
|-------------|-------|
| Remote configurado | `dropbox:/RetroSync/saves` |
| Config rclone | Detectado automáticamente por rclone |

---

## Notas sobre PSX

- La mayoría de los juegos PSX tienen formato `.cue` + múltiples `.bin` (tracks CD)
- Los `.img` son formato de disco alternativo (Crash Bandicoot, Chrono Cross CD1, etc.)
- Los `.chd` son el formato destino tras conversión (todo en un archivo)
- Los `.pbp` son formato PSP/PS3 comprimido
- **Scraping**: las carátulas se guardan en `E:\Carpetas anbernic\psx\media\images\`
- **Para que ES-DE muestre metadatos**: hay que raspar primero desde Retro Vault (tab Scraping → PSX) y luego exportar el gamelist
