# Rutas de Referencia — Retro Vault

> Archivo de referencia para no tener que buscar rutas en cada sesión.
> Actualizar si cambia algo.

---

## Biblioteca de ROMs

> Nombres canónicos = nombre interno ES-DE (minúsculas, sin espacios).
> Carpetas fusionadas el 2026-03-30: "Game Boy Advance" → `gba`, "Game Boy" → `gb`, etc.

| Plataforma | Carpeta canónica | Ruta completa |
|------------|-----------------|---------------|
| Raíz | — | `E:\Carpetas anbernic\` |
| NES / Famicom | `nes` | `E:\Carpetas anbernic\nes\` |
| Famicom Disk System | `fds` | `E:\Carpetas anbernic\fds\` |
| SNES | `snes` | `E:\Carpetas anbernic\snes\` |
| Nintendo 64 | `n64` | `E:\Carpetas anbernic\n64\` |
| Nintendo 64DD | `n64dd` | `E:\Carpetas anbernic\n64dd\` |
| Game Boy | `gb` | `E:\Carpetas anbernic\gb\` |
| Game Boy Color | `gbc` | `E:\Carpetas anbernic\gbc\` |
| Game Boy Advance | `gba` | `E:\Carpetas anbernic\gba\` |
| Nintendo DS | `nds` | `E:\Carpetas anbernic\nds\` |
| Nintendo 3DS | `n3ds` | `E:\Carpetas anbernic\3ds\` |
| GameCube | `gc` | `E:\Carpetas anbernic\gamecube\` |
| Wii | `wii` | `E:\Carpetas anbernic\wii\` |
| PlayStation | `psx` | `E:\Carpetas anbernic\psx\` |
| PlayStation 2 | `ps2` | `E:\Carpetas anbernic\ps2\` |
| PSP | `psp` | `E:\Carpetas anbernic\psp\` |
| Mega Drive | `megadrive` | `E:\Carpetas anbernic\megadrive\` |
| Master System | `mastersystem` | `E:\Carpetas anbernic\mastersystem\` |
| Game Gear | `gamegear` | `E:\Carpetas anbernic\gamegear\` |
| Saturn | `saturn` | `E:\Carpetas anbernic\saturn\` |
| Dreamcast | `dreamcast` | `E:\Carpetas anbernic\dreamcast\` |
| PC Engine | `pcengine` | `E:\Carpetas anbernic\pcengine\` |
| Arcade FBNeo | `fbneo` | `E:\Carpetas anbernic\fbneo\` |
| Arcade MAME | `mame` | `E:\Carpetas anbernic\mame\` |
| Arcade (genérico) | `arcade` | `E:\Carpetas anbernic\arcade\` |

> **Nota ES-DE:** GameCube es `gc` y 3DS es `n3ds` internamente, pero las carpetas en disco son `gamecube\` y `3ds\`. ES-DE usa `es_find_rules.xml` para mapear el nombre interno a la carpeta real.

### Assets (carátulas scrapeadas)
Las imágenes se guardan junto a los ROMs, en subcarpeta `media/images/`:
- Ejemplo PSX: `E:\Carpetas anbernic\psx\media\images\NombreJuego.jpg`
- Formato: `{stem del ROM}.png` o `.jpg` según ScreenScraper

---

## Emuladores (PC)

| Plataforma | Ejecutable |
|-----------|------------|
| RetroArch (PC) | `E:\Emuladores\Retroarch\retroarch.exe` |
| Cores RetroArch | `E:\Emuladores\Retroarch\cores\` |
| PSX — DuckStation | `E:\Emuladores\Duckstation\duckstation-qt-x64-ReleaseLTCG.exe` |
| PS2 — PCSX2 | `E:\Emuladores\PCSX2\pcsx2-qt.exe` |
| GameCube/Wii — Dolphin | `E:\Emuladores\Dolphin (GC, Wii)\Dolphin.exe` |

### RetroArch — config de saves/states

| Clave (`retroarch.cfg`) | Ruta real |
|------------------------|-----------|
| `savefile_directory` | `E:\Emuladores\Retroarch\saves\` |
| `savestate_directory` | `E:\Emuladores\Retroarch\states\` |
| `screenshot_directory` | `E:\Emuladores\Retroarch\screenshots\` |
| `system_directory` | `E:\Emuladores\Retroarch\system\` |

> El valor en `retroarch.cfg` es `":\saves"` — en RetroArch para Windows `:\` significa relativo a la carpeta de instalación.
> Subcarpetas por core: `saves\mGBA\`, `saves\Gambatte\`, `states\mGBA\`, etc.

---

## EmulationStation DE (ES-DE)

> ES-DE no usa `es_systems.cfg` — sus sistemas están definidos internamente. Solo se personaliza con `es_find_rules.xml`.

| Descripción | Ruta |
|-------------|------|
| Raíz ES-DE | `C:\Users\rammu\ES-DE\` |
| Settings | `C:\Users\rammu\ES-DE\settings\es_settings.xml` |
| Gamelists | `C:\Users\rammu\ES-DE\gamelists\{sistema}\gamelist.xml` |
| Sistemas personalizados | `C:\Users\rammu\ES-DE\custom_systems\es_find_rules.xml` |
| Media descargada | `C:\Users\rammu\ES-DE\downloaded_media\{sistema}\` |

### Notas sobre gamelists
- `gamelist_writer.py` escribe **dos copias** por plataforma:
  1. `E:\Carpetas anbernic\{plataforma}\gamelist.xml` — paths relativos (para ES-DE junto a ROMs)
  2. `C:\Users\rammu\ES-DE\gamelists\{plataforma}\gamelist.xml` — para ES-DE en PC
- Las imágenes se referencian como `./media/images/NombreJuego.jpg` en la copia junto a ROMs

---

## Extensiones por plataforma (ES-DE — Windows)

> Fuente: `C:\Program Files\ES-DE\resources\systems\windows\es_systems.xml`
> Nota: ES-DE usa el nombre interno del sistema, no siempre coincide con el nombre de carpeta.
> Solo se listan las extensiones más relevantes (sin mayúsculas duplicadas ni `.zip`/`.7z`).

| Sistema | Nombre interno ES-DE | Extensiones principales |
|---------|---------------------|------------------------|
| NES | `nes` | `.nes .fds .unf .unif` |
| SNES | `snes` | `.sfc .smc .fig .bs .bsx .swc` |
| N64 | `n64` | `.z64 .n64 .v64 .bin` |
| GB | `gb` | `.gb .cgb .dmg .sgb` |
| GBC | `gbc` | `.gbc .gb .cgb .dmg` |
| GBA | `gba` | `.gba .agb .gb .gbc` |
| NDS | `nds` | `.nds .bin` |
| 3DS | `n3ds` | `.3ds .3dsx .cci .cxi .elf` |
| Mega Drive | `megadrive` | `.md .smd .gen .bin .68k .32x` |
| Master System | `mastersystem` | `.sms .sg .bin` |
| Game Gear | `gamegear` | `.gg .bin` |
| GameCube | `gc` | `.iso .gcm .gcz .rvz .ciso .dol .elf` |
| Wii | `wii` | `.iso .wbfs .gcm .gcz .rvz .wia .ciso .dol .wad` |
| PSX | `psx` | `.cue .chd .bin .img .iso .pbp .mdf .m3u .ecm` |
| PS2 | `ps2` | `.iso .chd .bin .img .mdf .cso .zso .m3u` |
| PSP | `psp` | `.iso .cso .pbp .chd .elf` |
| Saturn | `saturn` | `.cue .chd .iso .bin .mdf .toc .m3u` |
| Dreamcast | `dreamcast` | `.cdi .gdi .chd .cue .iso .elf .lst .m3u` |
| Arcade (FBNeo) | `fbneo` | `.zip .7z` |

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

## Estructura de saves — diseño definitivo

La carpeta de saves está **centralizada en la raíz**, separada de las ROMs. Es el único punto de sync.

```
E:\Carpetas anbernic\
  ├── saves\            ← sync completo con Dropbox
  │   ├── gba\
  │   ├── psx\
  │   ├── nds\
  │   └── ...
  ├── states\           ← sync separado (archivos grandes, menos frecuente)
  │   ├── gba\
  │   └── ...
  ├── gba\              ← solo ROMs + media
  ├── psx\
  └── ...
```

**Por qué esta estructura y no `{plataforma}/saves/`:**
- Un solo `rclone sync` sincroniza todos los saves de todas las plataformas
- Encaja con RetroArch en Android: `/storage/emulated/0/RetroArch/saves/{plataforma}/`
- Mapping directo PC ↔ Android sin transformaciones
- Las ROMs (que son GBs) nunca se incluyen en el sync accidentalmente

**RetroArch PC** debe configurarse para apuntar aquí (pendiente):
- `savefile_directory = "E:\Carpetas anbernic\saves"`
- `savestate_directory = "E:\Carpetas anbernic\states"`

---

## Android (Anbernic RG 556)

| Descripción | Ruta en Android |
|-------------|-----------------|
| Saves RetroArch | `/storage/emulated/0/RetroArch/saves/{plataforma}/` |
| States RetroArch | `/storage/emulated/0/RetroArch/states/{plataforma}/` |
| ROMs | `/storage/emulated/0/ROMs/{plataforma}/` |

---

## Sync (rclone)

| Descripción | Valor |
|-------------|-------|
| Remote saves | `dropbox:/RetroSync/saves` → `E:\Carpetas anbernic\saves\` |
| Remote states | `dropbox:/RetroSync/states` → `E:\Carpetas anbernic\states\` |
| Config rclone | Detectado automáticamente por rclone |

---

## Notas sobre PSX

- La mayoría de los juegos PSX tienen formato `.cue` + múltiples `.bin` (tracks CD)
- Los `.img` son formato de disco alternativo (Crash Bandicoot, Chrono Cross CD1, etc.)
- Los `.chd` son el formato destino tras conversión (todo en un archivo)
- Los `.pbp` son formato PSP/PS3 comprimido
- **Scraping**: las carátulas se guardan en `E:\Carpetas anbernic\psx\media\images\`
- **Para que ES-DE muestre metadatos**: hay que raspar primero desde Retro Vault (tab Scraping → PSX) y luego exportar el gamelist

---

## Sesiones para completar este archivo

Cada sesión es independiente y se puede hacer en cualquier orden.
Marcar con ✅ cuando esté completa.

---

### Sesión 1 — Verificar rutas en disco ✅ (2026-03-30)

- [x] `E:\Carpetas anbernic\` — existe y tiene contenido
- [x] `E:\Emuladores\Retroarch\retroarch.exe` — presente *(ruta corregida: no estaba en C:)*
- [x] `E:\Emuladores\Duckstation\duckstation-qt-x64-ReleaseLTCG.exe` — presente
- [x] `E:\Emuladores\PCSX2\pcsx2-qt.exe` — presente
- [x] `E:\Emuladores\Dolphin (GC, Wii)\Dolphin.exe` — presente
- [x] `C:\Users\rammu\ES-DE\settings\es_settings.xml` — presente *(ruta corregida: ES-DE usa `C:\Users\rammu\ES-DE\`, no `.emulationstation`)*

---

### Sesión 2 — Añadir rutas de RetroArch ✅ (2026-03-30)

- [x] `savefile_directory` → `E:\Emuladores\Retroarch\saves\` (valor cfg: `":\saves"`)
- [x] `savestate_directory` → `E:\Emuladores\Retroarch\states\` (valor cfg: `":\states"`)
- [x] Sección añadida en la tabla de Emuladores (PC)

---

### Sesión 3 — Completar tabla de extensiones ✅ (2026-03-30)

- [x] Fuente: `C:\Program Files\ES-DE\resources\systems\windows\es_systems.xml`
- [x] 19 sistemas documentados (todos los relevantes de la biblioteca)
- [x] Corregido: GameCube es `gc` y 3DS es `n3ds` en ES-DE (no `gamecube`/`3ds`)

---

### Sesión 4 — Estado de la migración de saves ✅ (2026-03-30)

**Resultado: D1 ejecutada parcialmente — estructura mixta, requiere limpieza.**

**Lo que hay en disco:**

| Ubicación | Contenido | Estado |
|-----------|-----------|--------|
| `E:\Carpetas anbernic\gba\saves\` | 46 archivos `.sav`, `.sgm` | ✅ migrado |
| `E:\Carpetas anbernic\psx\saves\` | 6 archivos `.srm` | ✅ migrado |
| `E:\Carpetas anbernic\nds\saves\` | archivos `.ml1` | ✅ migrado |
| `E:\Carpetas anbernic\snes\saves\` | archivos presentes | ✅ migrado |
| `E:\Carpetas anbernic\gamegear\saves\` | archivos presentes | ✅ migrado |
| `E:\Carpetas anbernic\saves\gba\` | 16 archivos | ⚠️ estructura paralela (raíz) |
| `E:\Carpetas anbernic\saves\psx\` | 4 archivos | ⚠️ estructura paralela (raíz) |
| `E:\Carpetas anbernic\saves\` | subcarpetas para todas las plataformas | ⚠️ carpeta raíz legacy |
| Saves sueltos en `{plat}\` (sin subcarpeta) | ninguno encontrado | ✅ |

**Problema detectado:** existe una carpeta `E:\Carpetas anbernic\saves\` en la raíz con saves para todas las plataformas — probablemente un sync antiguo de RetroArch. Tiene menos archivos que `{plat}/saves/` (ej. 16 vs 46 en GBA), así que la versión en `{plat}/saves/` es más completa.

**Pendiente (apuntado en Día22-D1):**
- [ ] Revisar si los saves de `saves\gba\` están todos incluidos en `gba\saves\` — si sí, borrar la carpeta raíz `saves\`
- [ ] Actualizar `savefile_directory` y `savestate_directory` en RetroArch PC para apuntar a la nueva estructura

---

### Sesión 5 — Documentar sync completo ✅ (2026-03-30)

- [x] D2 implementado en `handlers/sync.py` y `server.py` (tray)
- [x] Sección Sync actualizada con ambos remotes (ver arriba)
- [x] Extensiones: saves → `config.save_extensions`, states → `config.state_extensions`
