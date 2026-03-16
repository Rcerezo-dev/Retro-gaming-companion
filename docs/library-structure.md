# Estructura de biblioteca — Referencia ES-DE

Retro Vault organiza tu biblioteca en una estructura de carpetas compatible con **EmulationStation / ES-DE** tanto en PC como en la consola Android. La misma estructura funciona en ambos dispositivos — solo cambia la ruta raíz.

---

## Estructura completa

```
library_root/                          PC: E:\ROMs\
│                                      Android: /storage/emulated/0/ROMs/
│
├── nes/                               Nintendo Entertainment System
│   ├── gamelist.xml                   ← generado por Scraper
│   ├── media/
│   │   ├── images/                    ← carátulas (.png, mismo nombre que el ROM)
│   │   └── videos/                    ← vídeos gameplay (.mp4)
│   └── Super Mario Bros (USA).nes
│
├── snes/                              Super Nintendo
├── n64/                               Nintendo 64
├── gb/                                Game Boy
├── gbc/                               Game Boy Color
├── gba/                               Game Boy Advance
├── nds/                               Nintendo DS
├── 3ds/                               Nintendo 3DS
├── gamecube/                          GameCube (ISOs o .rvz)
├── wii/                               Wii
├── wiiu/                              Wii U
│
├── psx/                               PlayStation
│   ├── gamelist.xml
│   ├── media/images/
│   ├── Final Fantasy VII (USA).m3u    ← playlist multi-disco
│   ├── Final Fantasy VII (USA) (Disc 1).chd
│   └── Final Fantasy VII (USA) (Disc 2).chd
│
├── ps2/                               PlayStation 2
├── ps3/                               PlayStation 3
├── psp/                               PSP (ISOs, .cso)
├── psvita/                            PS Vita
│
├── megadrive/                         Sega Mega Drive / Genesis
├── mastersystem/                      Master System
├── gamegear/                          Game Gear
├── saturn/                            Sega Saturn
├── segacd/                            Sega CD / Mega CD
├── sega32x/                           Sega 32X
├── dreamcast/                         Dreamcast
│
├── neogeo/                            Neo Geo
├── pcengine/                          PC Engine / TurboGrafx-16
├── atari2600/                         Atari 2600
├── atarilynx/                         Atari Lynx
│
├── saves/                             ← TODOS los saves de RetroArch (planos)
│   ├── Super Mario Bros (USA).srm
│   ├── Metroid Fusion (USA).srm
│   └── Final Fantasy VII (USA).state1
│
├── bios/                              ← BIOS (nunca sincronizadas, nunca escaneadas como ROMs)
│   ├── scph1001.bin                   ← PSX BIOS
│   ├── dc_boot.bin                    ← Dreamcast BIOS
│   └── gba_bios.bin
│
└── inbox/                             ← ZIPs nuevos sin organizar → Pilar 2
    └── Castlevania Collection.zip
```

---

## Nombres de carpeta → plataforma

Estos son los nombres exactos que usa Retro Vault (y EmulationStation / ES-DE):

| Carpeta | Plataforma | Extensiones principales |
|---------|-----------|------------------------|
| `nes` | Nintendo Entertainment System | `.nes` `.unf` |
| `snes` | Super Nintendo | `.sfc` `.smc` |
| `n64` | Nintendo 64 | `.z64` `.n64` `.v64` |
| `gb` | Game Boy | `.gb` |
| `gbc` | Game Boy Color | `.gbc` |
| `gba` | Game Boy Advance | `.gba` |
| `nds` | Nintendo DS | `.nds` |
| `3ds` | Nintendo 3DS | `.3ds` `.cia` |
| `gamecube` | Nintendo GameCube | `.iso` `.rvz` `.gcm` |
| `wii` | Nintendo Wii | `.iso` `.rvz` `.wbfs` |
| `psx` | PlayStation | `.chd` `.cue` `.m3u` `.pbp` |
| `ps2` | PlayStation 2 | `.iso` `.chd` |
| `psp` | PlayStation Portable | `.iso` `.cso` |
| `megadrive` | Sega Mega Drive / Genesis | `.md` `.gen` `.bin` |
| `mastersystem` | Sega Master System | `.sms` |
| `gamegear` | Sega Game Gear | `.gg` |
| `saturn` | Sega Saturn | `.chd` `.cue` |
| `segacd` | Sega CD / Mega CD | `.chd` `.cue` |
| `dreamcast` | Sega Dreamcast | `.chd` `.cdi` `.gdi` |
| `neogeo` | Neo Geo | `.neo` `.zip` |
| `pcengine` | PC Engine / TurboGrafx | `.pce` |
| `atari2600` | Atari 2600 | `.a26` |
| `atarilynx` | Atari Lynx | `.lnx` |

---

## Crear la estructura automáticamente

En la interfaz web → **Herramientas** → **Estructura de biblioteca** → **Crear carpetas**

Esto crea todas las carpetas de la lista anterior + `saves/` + `bios/` + `inbox/` + `media/images/` y `media/videos/` dentro de cada carpeta de plataforma.

---

## Organizar una biblioteca existente

Si ya tienes ROMs en la carpeta raíz o mezclados sin estructura, usa:

**Herramientas** → **Estructura de biblioteca** → **Previsualizar organización**

Verás adónde iría cada ROM sin mover nada. Cuando estés conforme:

**Herramientas** → **Estructura de biblioteca** → **Organizar biblioteca**

Esto:
1. Lee todos los juegos de la base de datos
2. Mueve cada ROM a `library_root/<plataforma>/`
3. Actualiza la ruta en la BD automáticamente

> Los saves no se mueven con esta herramienta. Muévelos manualmente a `saves/` la primera vez, luego configura RetroArch PC para que use esa carpeta (Settings → Saving → Savefile Directory).

---

## EmulationStation / ES-DE — configuración

### ES-DE (recomendado)

En `es_systems.xml` o en la configuración de ES-DE, apunta cada sistema a su carpeta:

```
ROMs path: E:\ROMs\   (PC)
           /storage/emulated/0/ROMs/   (Android)
```

ES-DE detecta automáticamente los sistemas que tengan su carpeta con ROMs.

### gamelist.xml

Retro Vault genera `gamelist.xml` en el formato EmulationStation con:
- `<path>` relativo al ROM
- `<name>` = título canónico del catálogo
- `<image>` relativa a `media/images/`
- `<desc>`, `<genre>`, `<developer>`, `<publisher>`, `<releasedate>`, `<rating>`

Para generarlo: **Scraper** → scraping completado → botón **Exportar gamelists**.

---

## Estructura en la consola Android

La misma estructura en `/storage/emulated/0/ROMs/`:

```
/storage/emulated/0/
  ROMs/
    psx/     gba/     snes/    ...
  RetroArch/
    saves/   ← RetroArch guarda aquí por defecto (plano)
    states/
  BIOS/
    scph1001.bin
    gba_bios.bin
```

Los saves de RetroArch en Android ya son planos por defecto — no hay nada que configurar.
El cloud sync los empareja con los del PC por nombre de archivo.
