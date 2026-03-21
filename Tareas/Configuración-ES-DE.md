# Configuración ES-DE — Setup desde cero

## Contexto

Este archivo contiene toda la configuración de EmulationStation DE (ES-DE) necesaria para configurarlo en un ordenador nuevo. Basado en los cambios realizados en el Día 16 (2026-03-21).

---

## 1. Rutas principales (Windows 11)

```
ES-DE config:      C:\Users\[USER]\.emulationstation\
Wrappers emuladores: E:\Emuladores\*\run_*.bat
ROMs:              E:\Carpetas anbernic\[plataforma]\
```

**Importante:** Los archivos `.bat` en `C:\Users\[USER]\.emulationstation\gamelists\*/gamelist.xml` deben **eliminarse completamente** — ES-DE los ignora y causan problemas.

---

## 2. Extensiones válidas por plataforma

Después del Día 16, las extensiones están limpias (sin `.bin`, `.img`, `.mdf` que duplicaban juegos).

### Consolas Nintendo

| Sistema | Extensiones válidas |
|---------|-------------|
| NES / Famicom | `.nes` `.unf` `.unif` `.nsf` |
| Famicom Disk System | `.fds` |
| SNES / Super Famicom | `.smc` `.sfc` `.fig` `.swc` `.bs` `.st` |
| Nintendo 64 | `.z64` `.v64` `.n64` `.ndd` `.u1` |
| GameCube | `.iso` `.gcm` `.rvz` `.wia` `.wbfs` `.ciso` `.gcz` `.m3u` |
| Wii | `.iso` `.rvz` `.wia` `.wbfs` `.ciso` `.gcz` `.wad` `.m3u` |
| Game Boy | `.gb` `.gbc` `.sgb` |
| Game Boy Color | `.gbc` `.gb` |
| Game Boy Advance | `.gba` `.agb` `.gbz` |
| Nintendo DS | `.nds` `.dsi` `.ids` `.srl` `.app` |
| Nintendo 3DS | `.3ds` `.3dsx` `.cia` `.csu` `.cci` `.cxi` `.app` |
| Virtual Boy | `.vb` `.vboy` `.bin` |
| Pokémon Mini | `.min` |

### Consolas Sony

| Sistema | Extensiones válidas |
|---------|-------------|
| PlayStation (PSX) | `.cue` `.chd` `.pbp` `.m3u` |
| PlayStation 2 | `.iso` `.chd` `.cso` `.zso` `.m3u` |
| PlayStation 3 | `.pkg` `.ps3` `.ps3dir` |
| PSP | `.iso` `.cso` `.pbp` `.elf` `.prx` `.ppdmp` `.chd` |
| PS Vita | `.vpk` `.psvita` |

### Consolas Sega

| Sistema | Extensiones válidas |
|---------|-------------|
| Master System / Mark III | `.sms` `.bin` `.sg` |
| Game Gear | `.gg` `.bin` |
| Mega Drive / Genesis | `.md` `.bin` `.smd` `.gen` `.68k` `.sgd` `.chd` |
| Mega-CD / Sega CD | `.bin` `.cue` `.iso` `.chd` `.m3u` |
| 32X | `.32x` `.bin` `.smd` |
| Saturn | `.cue` `.chd` `.iso` `.m3u` |
| Dreamcast | `.cdi` `.gdi` `.chd` `.m3u` `.iso` `.elf` |
| SG-1000 | `.sg` `.bin` `.sc` `.sf7` |

### Consolas Atari

| Sistema | Extensiones válidas |
|---------|-------------|
| Atari 2600 | `.a26` `.bin` `.rom` `.cart` |
| Atari 5200 | `.a52` `.bin` `.car` |
| Atari 7800 | `.a78` `.bin` |
| Atari Lynx | `.lnx` `.lyx` `.o` |
| Atari Jaguar | `.j64` `.jag` `.rom` `.abs` `.cof` `.bin` |
| Atari Jaguar CD | `.bin` `.cue` `.chd` |
| Atari ST / STE / TT / Falcon | `.st` `.msa` `.stx` `.dim` `.ipf` `.m3u` |
| Atari XL/XE | `.xex` `.atr` `.xfd` `.atx` `.cdm` `.cas` `.car` `.bin` `.a8s` |

### Neo Geo / SNK

| Sistema | Extensiones válidas |
|---------|-------------|
| Neo Geo | `.neo` `.zip` `.bin` |
| Neo Geo CD | `.bin` `.cue` `.chd` `.m3u` |
| Neo Geo Pocket / Color | `.ngp` `.ngc` `.ngpc` `.npc` |

### NEC

| Sistema | Extensiones válidas |
|---------|-------------|
| PC Engine / TurboGrafx-16 | `.pce` `.tg16` |
| PC Engine CD | `.bin` `.cue` `.chd` `.m3u` |
| PC-FX | `.fx` `.img` `.iso` `.cue` `.chd` `.m3u` |
| SuperGrafx | `.pce` `.sgx` |

### Computadoras personales

| Sistema | Extensiones válidas |
|---------|-------------|
| DOS (DOSBox) | `.bat` `.com` `.exe` `.conf` |
| ScummVM | `.scummvm` |
| Amiga | `.adf` `.adz` `.dms` `.fdi` `.ipf` `.hdf` `.hdz` `.lha` `.slave` `.info` `.cue` `.ccd` `.nrg` `.mds` `.iso` `.m3u` |
| Commodore 64 | `.d64` `.d71` `.d80` `.d81` `.d82` `.g64` `.g41` `.x64` `.t64` `.tap` `.prg` `.p00` `.crt` `.bin` `.nib` `.nbz` |
| MSX / MSX2 | `.rom` `.ri` `.mx1` `.mx2` `.col` `.dsk` `.cas` `.sg` `.sc` `.m3u` |
| ZX Spectrum | `.tzx` `.tap` `.z80` `.rzx` `.scl` `.trd` `.dsk` |
| Amstrad CPC | `.dsk` `.sna` `.kcr` `.voc` `.cpr` `.m3u` |
| Sharp X68000 | `.dim` `.img` `.d88` `.88d` `.hdm` `.dup` `.2hd` `.xdf` `.hdf` `.cmd` `.m3u` |

### Handhelds y otros

| Sistema | Extensiones válidas |
|---------|-------------|
| WonderSwan / Color | `.ws` `.wsc` `.bin` `.pc2` |
| Game & Watch | `.mgw` |
| Vectrex | `.bin` `.gam` `.vec` |
| ColecoVision | `.bin` `.col` `.rom` |
| Intellivision | `.int` `.bin` `.rom` |
| 3DO | `.iso` `.bin` `.cue` `.chd` |

### Arcade

| Sistema | Extensiones válidas |
|---------|-------------|
| MAME (genérico) | `.zip` `.7z` `.chd` |
| FBNeo (FinalBurn Neo) | `.zip` `.7z` `.chd` |
| CPS-1 / CPS-2 / CPS-3 | `.zip` `.7z` |

> **Nota:** Todos los sistemas aceptan además `.zip` y `.7z`.

---

## 3. Wrappers .bat para emuladores (Windows 11)

**Problema:** El port Aloshi 2015 (32-bit) de ES usa `cmd.exe /c` que causa exit code 1 con emuladores 64-bit en Windows 11 (D3D11/audio).

**Solución:** Crear wrappers `.bat` que hacen `cd /d` al directorio del emulador antes de lanzarlo.

### Pasos:

1. Crear los siguientes archivos en las carpetas de emuladores:

```
E:\Emuladores\Retroarch\run_retroarch.bat
E:\Emuladores\Mupen64\run_mupen64.bat
E:\Emuladores\Duckstation\run_duckstation.bat
E:\Emuladores\PCSX2\run_pcsx2.bat
E:\Emuladores\Flycast\run_flycast.bat
E:\Emuladores\Dolphin (GC, Wii)\run_dolphin.bat
E:\Emuladores\MAME\run_mame.bat
```

2. Cada archivo debe tener contenido similar:

```batch
@echo off
cd /d "%~dp0"
start "" "%~dp0retroarch.exe" %*
exit /b %errorlevel%
```

Reemplazar `retroarch.exe` por el nombre del ejecutable correspondiente en cada wrapper.

3. En `es_systems.cfg`, actualizar los `<command>` para usar los wrappers:

```xml
<command>E:\Emuladores\Retroarch\run_retroarch.bat %ROM%</command>
```

---

## 4. es_systems.cfg — Cambios importantes

**Ubicación:** `C:\Users\[USER]\.emulationstation\es_systems.cfg`

### Cambios realizados en Día 16:

1. **Wrappers en `<command>`** — Todos usan los `.bat` wrappers
2. **Extensiones limpias** — Eliminar `.bin`, `.img`, `.mdf` que duplicaban juegos en PSX/PS2/Saturn/Dreamcast
3. **`<path>` correcto** — Deben apuntar a `E:\Carpetas anbernic\[plataforma]\`, no a `~/.emulationstation/gamelists/`

### Ejemplo para PSX (después de limpieza):

```xml
<system>
    <name>psx</name>
    <fullname>PlayStation</fullname>
    <path>E:\Carpetas anbernic\psx</path>
    <extension>.cue .chd .pbp .m3u .zip .7z</extension>
    <command>E:\Emuladores\Duckstation\run_duckstation.bat %ROM%</command>
</system>
```

---

## 5. Gamelists (gamelist.xml)

### ❌ QUÉ NO HACER

**Eliminar completamente estos archivos:**
```
C:\Users\[USER]\.emulationstation\gamelists\*/gamelist.xml
```

Tienen rutas rotas (`C:\Users\rammu\.emulationstation\gamelists\gba\Game.gba`) y causan que ES no encuentre los juegos.

### ✅ QUÉ HACER

1. Dejar que ES-DE escanee las carpetas directamente desde `es_systems.cfg`
2. Usar Retro Vault para exportar `gamelist.xml` con metadatos a `E:\Carpetas anbernic\[plataforma]/gamelist.xml` (si quieres)
3. ES-DE cargará automáticamente los metadatos desde ahí

---

## 6. Campos de media en gamelist.xml

Si exportas desde Retro Vault, los metadatos incluyen:

| Tag XML | Carpeta en disco | Uso en ES-DE |
|---------|------------------|--------------|
| `<image>` | `media/images/` | Portada (box art) |
| `<thumbnail>` + `<marquee>` | `media/wheels/` | Logo/wheel lateral |
| `<screenshot>` | `media/screenshots/` | Captura en detalle |

Estructura esperada:
```
E:\Carpetas anbernic\
  psx/
    Crash Bandicoot (USA)/
      Crash Bandicoot (USA).cue
      Crash Bandicoot (Track 1).bin
      ...
    media/
      images/
        Crash Bandicoot (USA).png
      wheels/
        Crash Bandicoot (USA).png
      screenshots/
        Crash Bandicoot (USA).png
    gamelist.xml
```

---

## 7. Duplicados por extensiones (SOLUCIONADO)

ES-DE mostraba cada track `.bin` de un juego multi-disc como un juego separado.

**Estado actual (Día 16):**

| Sistema | Antes | Después |
|---------|-------|---------|
| PSX | `.cue .chd .pbp .m3u .img .bin` | `.cue .chd .pbp .m3u` |
| PS2 | `.iso .chd .bin .img .cso .zso .m3u` | `.iso .chd .cso .zso .m3u` |
| Saturn | `.cue .chd .iso .m3u .bin .mdf .img` | `.cue .chd .iso .m3u` |
| Dreamcast | `.cdi .gdi .chd .m3u .bin .iso .elf` | `.cdi .gdi .chd .m3u .iso .elf` |

Esto ya está reflejado en la tabla de **Extensiones válidas por plataforma** (sección 2).

---

## 8. ROMs multi-fichero en subcarpetas

Cuando apliques renombres en Retro Vault, los juegos multi-disco se reorganizan automáticamente.

**Ejemplo PSX:**
```
ANTES:
  psx/Crash Bandicoot.cue
  psx/Crash Bandicoot (Track 1).bin
  psx/Crash Bandicoot (Track 2).bin

DESPUÉS:
  psx/Crash Bandicoot (USA)/
    Crash Bandicoot (USA).cue
    Crash Bandicoot (USA) (Track 1).bin
    Crash Bandicoot (USA) (Track 2).bin
```

Plataformas afectadas:
- PSX (`.cue` + N×`.bin`)
- Saturn (`.cue` + N×`.bin`)
- Dreamcast (`.gdi` + N×`.bin`/`.raw`)
- PS2, GameCube, Wii (`.iso`/`.chd`/`.rvz` solo mkdir)

---

## 9. Temas recomendados

Basado en experiencia del Día 16, estos temas funcionan bien con la estructura de carpetas:

### Recomendados (en orden):
1. **Art Book Next** ⭐ — Portadas grandes, metadatos detallados
2. **Slate** — Limpio, buena navegación
3. **Rbsimple-DE** — Minimalista
4. **Modern** — Visual actual

Descargar desde:
- https://www.es-de.org/download-themes/
- O manual: descargar `.zip` y extraer en `~/.emulationstation/themes/`

---

## 10. Checklist de configuración ES-DE en ordenador nuevo

Usar este checklist cada vez que configures ES-DE en un ordenador diferente:

### Paso 1: Setup inicial
- [ ] Instalar ES-DE (compatible Windows 11)
- [ ] Primera ejecución genera `C:\Users\[USER]\.emulationstation\`
- [ ] Cerrar ES-DE

### Paso 2: Eliminar archivos rotos
- [ ] Eliminar todos los archivos en `C:\Users\[USER]\.emulationstation\gamelists\*/`
- [ ] Verificar que **NO exista** `C:\Users\[USER]\.emulationstation\gamelists/psx/gamelist.xml` (etc.)

### Paso 3: Configurar es_systems.cfg
- [ ] Editar `C:\Users\[USER]\.emulationstation\es_systems.cfg`
- [ ] Apuntar `<path>` a `E:\Carpetas anbernic\[plataforma]`
- [ ] Usar extensiones limpias de la sección 2 (sin `.bin`, `.img`, `.mdf`)
- [ ] Apuntar `<command>` a wrappers `.bat`

### Paso 4: Crear wrappers .bat
- [ ] Crear 7 wrappers `.bat` en `E:\Emuladores\*/run_*.bat`
- [ ] Cada uno hace `cd /d "%~dp0"` y luego lanza el emulador

### Paso 5: Verificar estructura de ROMs
- [ ] ROMs en `E:\Carpetas anbernic\[plataforma]/`
- [ ] Extensiones coinciden con las de sección 2
- [ ] Multi-disco en subcarpetas (`psx/Juego (USA)/juego.cue`)

### Paso 6: Descargar tema
- [ ] Descargar tema (recomendado: Art Book Next)
- [ ] Extraer en `~/.emulationstation/themes/`

### Paso 7: Primer scan
- [ ] Abrir ES-DE
- [ ] Dejar que escanee todas las carpetas de `es_systems.cfg`
- [ ] Verificar que encuentre todos los juegos (sin duplicados)

### Paso 8: Metadatos (opcional)
- [ ] Exportar desde Retro Vault `gamelist.xml` + `media/`
- [ ] Copiar a `E:\Carpetas anbernic\[plataforma]/`
- [ ] Presionar F5 en ES-DE para recargar

### Paso 9: Pruebas
- [ ] Seleccionar un juego y lanzar
- [ ] Verificar que el wrapper `.bat` arranca el emulador
- [ ] Reproducir un juego multi-disco (ej. PSX) — debe cargar la imagen completa, no un track individual

---

## 11. Troubleshooting

### Problema: "No se han encontrado archivos de juego"
**Solución:** Verificar que `<path>` en `es_systems.cfg` apunta a la carpeta correcta y contiene ROMs con extensiones válidas.

### Problema: Emulador no arranca (exit code 1)
**Solución:** Verificar que existe el wrapper `.bat` correspondiente y que el ejecutable del emulador existe en esa carpeta.

### Problema: Duplicados de juegos multi-disco
**Solución:** Verificar extensiones válidas. PSX no debe incluir `.bin` o `.img` — solo `.cue`, `.chd`, `.pbp`, `.m3u`.

### Problema: Gamelist con rutas incorrectas
**Solución:** Eliminar el archivo `gamelist.xml` de `~/.emulationstation/gamelists/`. ES escanea desde `es_systems.cfg`.

### Problema: Metadatos no se cargan
**Solución:** Verificar que `gamelist.xml` está en `E:\Carpetas anbernic\[plataforma]/` y que las rutas de `<image>`, `<thumbnail>`, `<screenshot>` son relativas a esa carpeta.

---

## Referencias

- ES-DE docs: https://www.es-de.org/
- Configuración manual: https://www.es-de.org/documentation/user-guide/configuration/
- Temas: https://www.es-de.org/download-themes/
