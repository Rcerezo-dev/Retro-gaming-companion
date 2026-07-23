# Matriz de compatibilidad de saves — PC ↔ Anbernic RG556

Referencia para saber si los saves sincronizan correctamente entre el emulador de PC
y el de Android. Basado en los emuladores de `docs/architecture/platforms-cores.md`
y las rutas verificadas en `docs/sync/android-save-paths-RG556.md`.

Leyenda de estado:
- ✅ Compatible — mismo formato, sync directo con Retro Vault
- ⚠️ Compatible con caveat — mismo formato pero requiere mapeo de rutas o ajuste manual
- ❌ Incompatible o sin acceso — formato diferente o ADB bloqueado

---

## Plataformas RetroArch ↔ RetroArch (mismos cores)

Las plataformas donde PC y Android usan el **mismo core** son las más seguras:
los archivos `.srm` / `.state` son intercambiables directamente.

| Plataforma | Core PC | Core Android | Ext. save | Ext. state | Sync | Notas |
|------------|---------|-------------|-----------|-----------|------|-------|
| NES | FCEUmm | FCEUmm | `.srm` | `.state` | ✅ cloud/SD | Mismo core, 100% compatible |
| SNES | Snes9x 2010 | Snes9x | `.srm` | `.state` | ✅ cloud/SD | PC usa 2010, Android usa actual — `.srm` idéntico |
| Game Boy | Gambatte | Gambatte | `.srm` | `.state` | ✅ cloud/SD | Mismo core |
| Game Boy Color | Gambatte | Gambatte | `.srm` | `.state` | ✅ cloud/SD | Mismo core |
| Game Boy Advance | mGBA | mGBA | `.srm` | `.state` | ✅ cloud/SD | Mismo core |
| Sega Master System | Genesis Plus GX | Genesis Plus GX | `.srm` | `.state` | ✅ cloud/SD | Mismo core |
| Sega Mega Drive | Genesis Plus GX | Genesis Plus GX | `.srm` | `.state` | ✅ cloud/SD | Mismo core |
| Game Gear | Genesis Plus GX | Genesis Plus GX | `.srm` | `.state` | ✅ cloud/SD | Mismo core |
| Nintendo DS | melonDS | melonDS | `.sav` | `.state` | ✅ cloud/SD | Requiere BIOS en `/RetroArch/system/` en ambos |
| Atari 2600 | Stella 2023 | Stella 2023 | `.srm` | `.state` | ✅ cloud/SD | Mismo core |
| Neo Geo | FBNeo | FBNeo | `.srm` | `.state` | ✅ cloud/SD | Mismo core |
| PSP | PPSSPP (core) | PPSSPP (core) | SAVEDATA/ | PPSSPP_STATE/ | ✅ SD | El core RA refleja en `/storage/emulated/0/PSP/` |

---

## PlayStation (PS1)

| | PC | Android |
|-|----|----|
| Emulador | DuckStation standalone | DuckStation (scoped storage) |
| Saves (memory cards) | `%AppData%\DuckStation\memcards\*.mcd` | `Android/data/com.github.stenzek.duckstation/files/memcards/*.mcd` |
| Save states | `%AppData%\DuckStation\savestates\*.sav` | `…/files/savestates/*.sav` |
| Formato save | `.mcd` / `.mcr` | `.mcd` / `.mcr` |
| Sync method | ADB cable | ❌ **No sincronizable** via ADB sin root (VAL-FIX-4) |
| Estado | ✅ Compatible en formato | `Android/data/...` es scoped storage en Android 11+ — ADB devuelve `Permission denied` aunque el paquete esté instalado y depurable |

> Naming: `SCUS-12345_1.mcd` (slot 1). El serial identifica el juego en ambas plataformas.
> Workaround: en DuckStation Android, cambiar Settings → Memory Cards → Directory a
> una carpeta pública (p.ej. `/sdcard/DuckStation/memcards`) — así queda fuera del
> sandbox de la app y accesible por ADB sin root.
> Alternativa en Android: RetroArch + Beetle PSX → saves en `/RetroArch/saves/Beetle PSX/`.

---

## PlayStation 2

| | PC | Android |
|-|----|----|
| Emulador | PCSX2 standalone | AetherSX2 / NetherSX2 |
| Saves (memory cards) | `Documents\PCSX2\memcards\*.ps2` | `Android/data/xyz.aethersx2.android/files/memcards/*.ps2` |
| Save states | `Documents\PCSX2\sstates\*.p2s` | `…/files/sstates/*.p2s` |
| Formato save | `.ps2` (2 MB memory card) | `.ps2` (mismo) |
| Sync method | ADB cable | ✅ ADB (Retro Vault → cable sync) |
| Estado | ✅ Compatible | `.ps2` es formato estándar; PCSX2 y AetherSX2 lo comparten |

> ⚠️ Verificar que el nombre del archivo de memory card es el mismo en ambos lados
> (p.ej. `Mcd001.ps2`). PCSX2 y AetherSX2 pueden diferir en el nombre por defecto.

---

## PSP

| | PC | Android |
|-|----|----|
| Emulador | PPSSPP standalone | PPSSPP standalone |
| Saves | `Documents\PPSSPP\PSP\SAVEDATA\` | `/storage/emulated/0/PSP/SAVEDATA/` |
| Save states | `Documents\PPSSPP\PSP\PPSSPP_STATE\` | `/storage/emulated/0/PSP/PPSSPP_STATE/` |
| Sync method | SD card / cloud | ✅ Sin ADB (ruta pública en SD) |
| Estado | ✅ Compatible | SAVEDATA tiene estructura de carpetas `ULUS-XXXXX/` idéntica en ambos |

---

## Nintendo 64

| | PC | Android |
|-|----|----|
| Emulador | Mupen64Plus standalone | RetroArch + Mupen64Plus-Next |
| Saves | Junto a las ROMs (`.sra`, `.mpk`, `.fla`, `.eep`) | `/storage/emulated/0/RetroArch/saves/Mupen64Plus-Next/` |
| Sync method | Cloud / SD | ⚠️ |
| Estado | ⚠️ Mismo formato de save pero diferente emulador. Probar antes de confiar en el sync |

> El archivo `.sra` (SRAM) es el save principal en la mayoría de juegos.
> Mupen64Plus y Mupen64Plus-Next comparten el mismo formato binario.
> **Pendiente verificar en hardware** (EMULATOR-COMPAT-4).

---

## Sega Saturn

| | PC | Android |
|-|----|----|
| Emulador | RetroArch + Yaba Sanshiro 2 | Yaba Sanshiro 2 Pro standalone |
| Saves | `/RetroArch/saves/Yabasanshiro/memory.ram` | `Android/data/org.devmiyax.yabasanshioro2.pro/files/yabause/memory/memory.ram` |
| Sync method | ADB cable | ✅ ADB (Retro Vault → cable sync) |
| Estado | ⚠️ Mismo archivo `memory.ram` pero verificar que Yaba Sanshiro 2 standalone y el core RA usan el mismo formato |

---

## Sega Dreamcast

| | PC | Android (opción A) | Android (opción B) |
|-|----|---|----|
| Emulador | Flycast standalone | RetroArch + Flycast | Redream standalone |
| VMU saves | `%AppData%\Flycast\data\vmu_save_*.bin` | `/RetroArch/saves/Flycast/` | `Android/data/io.recompiled.redream/files/vmu*.bin` |
| Sync method | ADB / cloud | ✅ SD (RetroArch) | ✅ ADB |
| Estado | ⚠️ Flycast PC ↔ Flycast Android: compatible. Redream usa formato VMU diferente (`vmu0.bin`) |

> Recomendado: usar Flycast en ambos lados para compatibilidad total.

---

## GameCube / Wii

| | PC | Android |
|-|----|----|
| Emulador | Dolphin standalone | Dolphin / MMJ standalone |
| GC memory cards | `Documents\Dolphin Emulator\GC\USA\*.raw` | `Android/data/org.dolphinemu.dolphinemu/files/GC/` |
| Sync method | ❌ ADB permission denied | — |
| Estado | ❌ **No sincronizable** via ADB sin root. Usar la función de backup integrada de Dolphin o conceder permisos especiales |

> Workaround: exportar saves desde Dolphin PC → importar en Dolphin Android manualmente.
> O usar el core RetroArch + Dolphin en Android (saves en SD card, accesibles sin ADB).

---

## Nintendo 3DS

| | PC | Android |
|-|----|----|
| Emulador | RetroArch + Citra | Citra / Lime3DS standalone |
| Saves | `…/Citra/saves/<titleid>/` | `…/citra-emu/sdmc/Nintendo 3DS/…/title/<titleid>/data/` |
| Sync method | ADB cable | ⚠️ ADB (estructura de directorios compleja) |
| Estado | ⚠️ Mismos datos pero estructura de rutas diferente entre core RA y Citra standalone |

---

## Resumen rápido

| Plataforma | Sync sin fricción | Método |
|------------|------------------|--------|
| NES / SNES / GB / GBC / GBA / MD / SMS / GG / DS / Neo Geo / Atari | ✅ | cloud o SD |
| PSP | ✅ | SD (sin ADB) |
| PS1 (DuckStation) | ❌ | Requiere root o mover el directorio de memcards a una carpeta pública (VAL-FIX-4) |
| PS2 (PCSX2 ↔ AetherSX2) | ✅ | ADB cable |
| Saturn (Yaba Sanshiro) | ⚠️ verificar | ADB cable |
| N64 | ⚠️ verificar | cloud o SD |
| Dreamcast (Flycast ↔ Flycast) | ⚠️ verificar | ADB cable |
| GameCube / Wii | ❌ | Requiere root o workaround manual |
| Nintendo 3DS | ⚠️ | ADB cable + mapeo de rutas |

---

*Verificado en hardware: plataformas RetroArch ↔ RetroArch (mismos cores), PS1 DuckStation, PS2 AetherSX2, PSP.*
*Pendiente verificar en hardware: N64, Saturn, Dreamcast, 3DS. Ver EMULATOR-COMPAT-2 a 4.*
*Última actualización: 2026-06-27*
