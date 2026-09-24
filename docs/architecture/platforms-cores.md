# Plataformas y emuladores — PC y Anbernic RG556

> Referencia para saber qué emulador/core usar en cada sistema y qué configurar para calidad óptima.
> En PC se usa EmulationStation como frontend (`~/.emulationstation/es_systems.cfg`).
> En la Anbernic se usa RetroArch con los mismos cores que en PC donde sea posible.
>
> **DEVPROFILE-1 (2026-08-31)**: los cores PC candidatos (columna "Emulador /
> Core" de la tabla de abajo) y el BIOS requerido por plataforma ya no viven
> solo aquí — la fuente real que usa el código es
> `src/rom_manager/detection/platforms.toml` (`[cores.pc]` / `[[bios]]`). Esta
> página sigue siendo una guía humana (incluye la columna Android, que el
> código todavía no consume), pero si algo no coincide con el TOML, manda el
> TOML.

---

## PC — EmulationStation

| Sistema | Emulador / Core | Ejecutable |
|---------|----------------|------------|
| NES | RetroArch + **FCEUmm** | `E:/Emuladores/Retroarch/cores/fceumm_libretro.dll` |
| SNES | RetroArch + **Snes9x 2010** | `snes9x2010_libretro.dll` |
| Game Boy | RetroArch + **Gambatte** | `gambatte_libretro.dll` |
| Game Boy Color | RetroArch + **Gambatte** | `gambatte_libretro.dll` |
| Game Boy Advance | RetroArch + **mGBA** | `mgba_libretro.dll` |
| Nintendo DS | RetroArch + **melonDS** | `melonds_libretro.dll` |
| Nintendo 3DS | RetroArch + **Citra** | `citra_libretro.dll` |
| Nintendo 64 | **Mupen64Plus** standalone | `E:/Emuladores/Mupen64/mupen64plus-ui-console.exe` |
| GameCube | **Dolphin** standalone | `E:/Emuladores/Dolphin (GC, Wii)/Dolphin.exe` |
| Wii | **Dolphin** standalone | `E:/Emuladores/Dolphin (GC, Wii)/Dolphin.exe` |
| Metroid Prime (GC/Wii) | **PrimeHack** (fork Dolphin) | `E:/Emuladores/primehack/Dolphin.exe` — lanzar manualmente |
| Sega Master System | RetroArch + **Genesis Plus GX** | `genesis_plus_gx_libretro.dll` |
| Sega Mega Drive | RetroArch + **Genesis Plus GX** | `genesis_plus_gx_libretro.dll` |
| Sega Game Gear | RetroArch + **Genesis Plus GX** | `genesis_plus_gx_libretro.dll` |
| Sega Saturn | RetroArch + **Yaba Sanshiro 2 Pro** | `yabasanshiro_libretro.dll` |
| Sega Dreamcast | **Flycast** standalone | `E:/Emuladores/Flycast/flycast.exe` |
| PlayStation | **DuckStation** standalone | `E:/Emuladores/Duckstation/duckstation-qt-x64-ReleaseLTCG.exe` |
| PlayStation 2 | **PCSX2** standalone | `E:/Emuladores/PCSX2/pcsx2-qt.exe` |
| PSP | RetroArch + **PPSSPP** | `ppsspp_libretro.dll` |
| Arcade / MAME | **MAME** standalone | `E:/Emuladores/MAME/mame.exe` |
| FBNeo Arcade | **MAME** standalone | `E:/Emuladores/MAME/mame.exe` |
| Atari 2600 | RetroArch + **Stella 2023** | `stella2023_libretro.dll` |
| Atari 5200 | RetroArch + **a5200** | `a5200_libretro.dll` |
| Atari 7800 | RetroArch + **ProSystem** | `prosystem_libretro.dll` |
| Neo Geo | RetroArch + **Geolith** | `geolith_libretro.dll` |
| Neo Geo CD | RetroArch + **NeoCD** | `neocd_libretro.dll` |

---

## Anbernic RG556 — RetroArch (Android)

> Instalar los cores desde RetroArch > Menú principal > Online Updater > Core Downloader.
> Los saves se sincronizan automáticamente con el PC vía Retro Vault (cable ADB o rclone).

| Sistema | Core recomendado | Notas |
|---------|-----------------|-------|
| NES | **FCEUmm** | Sin límite de sprites, paleta smooth-fbx |
| SNES | **Snes9x** | Más preciso que Snes9x 2010 en hardware potente |
| Game Boy / Color | **Gambatte** | Activar colorización GBC para juegos GB |
| Game Boy Advance | **mGBA** | Corrección de color GBA activada |
| Nintendo DS | **melonDS** | Requiere BIOS de DS en `/RetroArch/system/` |
| Nintendo 3DS | **Citra** (si tiene potencia) | Muy exigente — en RG556 puede ir lento |
| Nintendo 64 | **Mupen64Plus-Next** | Plugin Glide64Mk2 o ParaLLEl-RDP |
| GameCube / Wii | **Dolphin** (core RA) | Muy exigente, resultados variables en RG556 |
| Master System | **Genesis Plus GX** | — |
| Mega Drive | **Genesis Plus GX** | Sin límite de sprites activado |
| Game Gear | **Genesis Plus GX** | — |
| Saturn | **Yaba Sanshiro 2 Pro** | Alternativa: Beetle Saturn (más lento) |
| Dreamcast | **Flycast** | Upscaling x2 disponible |
| PlayStation | **PCSX ReARMed** | Más rápido que DuckStation en ARM; activa PGXP si el hardware aguanta |
| PlayStation 2 | **AetherSX2 / NetherSX2** | No está en el downloader oficial — instalar APK aparte |
| PSP | **PPSSPP** | Excelente en RG556 |
| Arcade | **MAME 2003 Plus** | Usa romset 0.78; para sets modernos usar MAME actual |
| Atari 2600 | **Stella 2023** | — |
| Neo Geo | **FBNeo** | El mejor core para Neo Geo en Android |

---

## Overrides por juego en Retro Vault (CFG-PORGAME)

Retro Vault detecta, edita y copia entre PC/Android las opciones de core que
RetroArch guarda **por juego** — nunca importa ni autora configs de una
fuente externa; "verificado" siempre significa que el propio usuario las
guardó jugando (decisión de diseño, ver `Tareas/Roadmap-212-Ideas-Futuras.md`
frente B).

### Cómo las genera RetroArch

RetroArch permite guardar las opciones de un core (Quick Menu → Options) en
tres niveles de especificidad crecientes, todos bajo la misma carpeta
`config/<core>/`:

| Nivel | Acción en el menú | Archivo | Alcance |
|-------|-------------------|---------|---------|
| Core | Save Core Options | `config/<core>/<core>.opt` | Todos los juegos que usan ese core |
| Carpeta de contenido | Save Content Directory Options | `config/<core>/<carpeta rom>.opt` | Todos los juegos en esa carpeta |
| Juego | **Save Game Options** | `config/<core>/<nombre rom>.opt` | Solo ese juego — **el que gestiona Retro Vault** |

(Referencia: `docs.libretro.com/guides/overrides/` — documenta el mecanismo
hermano de "Overrides" en `.cfg` con la misma jerarquía de 3 niveles;
RetroArch aplica la misma jerarquía a "Options" con extensión `.opt`.)

Retro Vault solo lee/escribe/copia el tercer nivel (por juego) — nunca toca
`<core>.opt` (nivel core) ni interpreta ninguna clave dentro del archivo: lo
trata como texto opaco de principio a fin (`retroarch_overrides_service.py`).

### Formato del archivo

Texto plano `clave = "valor"`, una por línea — mismo formato que un `.cfg`
de RetroArch, sin comentarios propios. Ejemplo real (`Gambatte/Tetris.opt`):
```
input_max_users = "2"
gfx_ctx_scaling = "1"
```
Retro Vault nunca genera ni valida estas claves — cualquier contenido que
RetroArch haya escrito se respeta tal cual.

### Dónde vive por plataforma

- **PC**: `<ra_config_dir>/<core>/<rom>.opt`, con `ra_config_dir`
  auto-detectado o configurado en Settings (normalmente `<carpeta
  RetroArch>/config/`).
- **Android (RG556)**: `<auto_sync_android_path>/config/<core>/<rom>.opt` —
  mismo patrón, leído/escrito vía ADB (auto-detectado, B0-3c).

### Nombre de core: por qué importa

`<core>` es el nombre de carpeta que usa RetroArch (p. ej. `Gambatte`,
`Snes9x 2010`) — **no** el nombre de la plataforma. PC y Android pueden usar
cores distintos para la misma plataforma (ver tablas arriba); Retro Vault
solo permite copiar un override entre PC/Android cuando el core es
**exactamente el mismo en ambos lados** (mismo nombre de carpeta) — los 8
casos documentados en `SHARED_CORES`
(`src/rom_manager/services/retroarch_overrides_service.py`): FCEUmm,
Gambatte, mGBA, melonDS, Genesis Plus GX, Yaba Sanshiro 2 Pro, PPSSPP,
Stella 2023.

---

## Configuración de calidad aplicada en RetroArch (PC)

Los ficheros de config se aplican automáticamente al cargar cada core.
Ubicación: `E:/Emuladores/Retroarch/config/<Nombre Core>/`

| Core | Archivo | Cambio clave |
|------|---------|-------------|
| FCEUmm | `FCEUmm.cfg` | Integer scaling + aspect ratio correcto |
| FCEUmm | `FCEUmm.opt` | Sin límite sprites, paleta smooth-fbx, overscan recortado |
| Snes9x 2010 | `Snes9x 2010.cfg` | Integer scaling |
| Snes9x 2010 | `Snes9x 2010.opt` | Overclock compatible (sin slowdown), audio gaussiano |
| Gambatte | `Gambatte.cfg` | Integer scaling |
| Gambatte | `Gambatte.opt` | **Colorización GBC activada** para juegos GB originales |
| mGBA | `mGBA.cfg` | Integer scaling |
| mGBA | `mGBA.opt` | **Color correction "GBA Colors"** (LCD auténtico), GB colors "Corrected" |
| Genesis Plus GX | `Genesis Plus GX.cfg` | Integer scaling |

### Notas para Anbernic (configurar manualmente en RetroArch)

1. **Integer scaling**: Settings > Video > Scaling > Integer Scale: ON
2. **Aspect ratio**: Settings > Video > Aspect Ratio: Core provided
3. **Gambatte GB**: Quick Menu > Options > GB Colorization: GBC
4. **mGBA**: Quick Menu > Options > Color Correction: GBA Colors
5. **FCEUmm**: Quick Menu > Options > No Sprite Limit: enabled

---

## Gamelists (carátulas y metadatos)

Los gamelists generados por **Retro Vault** (scraper ScreenScraper) se exportan a:

**PC (EmulationStation):**
```
C:/Users/rammu/.emulationstation/gamelists/<sistema>/gamelist.xml
```

**Anbernic:**
- Copiar el mismo `gamelist.xml` a `/storage/emulated/0/RetroArch/roms/<sistema>/gamelist.xml`
- O sincronizar con rclone / cable ADB desde Retro Vault

---

## Notas adicionales

- **PrimeHack** (Metroid Prime con ratón): No está en EmulationStation — lanzar desde `E:/Emuladores/primehack/Dolphin.exe` directamente.
- **Saturn con BIOS**: Yaba Sanshiro necesita `saturn_bios.bin` en `E:/Emuladores/Retroarch/system/`.
- **PS1 CHD**: DuckStation lee `.chd` directamente — recomendado convertir todos los `.cue/.bin` (desde Retro Vault > Formatos > Convertir a CHD).
- **MAME romset**: La versión de MAME en `E:/Emuladores/MAME/` determina el romset compatible. Usar ROMs de la misma versión.
