# Retro Vault

**Gestiona, organiza y sincroniza tu colección de ROMs retro.**

Retro Vault es una herramienta local en Python con interfaz web que convierte una carpeta caótica de ROMs en una biblioteca identificada, organizada por plataforma, con metadatos, carátulas y — lo más importante — con los **saves sincronizados automáticamente** entre tu PC y tu consola portátil Android.

```
http://127.0.0.1:7777
```

---

## ¿Qué hace?

### El flujo habitual

```
ROM nueva en inbox/
    ↓  Inbox: identifica plataforma, descomprime, renombra
    ↓  Scan: hashea SHA1+MD5+CRC32, inventaría en SQLite
    ↓  Match: cruza con catálogos No-Intro / Redump
    ↓  Plan → Apply: renombra a nombre canónico (atómico, con rollback)
    ↓  Scraper: descarga metadatos + carátulas de ScreenScraper
    ↓  gamelist.xml para EmulationStation / ES-DE
    ↓  RetroAchievements: comprueba compatibilidad de logros por MD5
Biblioteca organizada
    ↓  Cloud Sync: saves ↔ Dropbox ↔ consola Android (vía rclone)
    ↓  Cable Sync: ROMs + saves ↔ consola por USB (sin WiFi)
Colección en todos tus dispositivos
```

---

## Características

### Escaneo e inventario
- Escaneo recursivo con clasificación automática: ROM / save / asset / BIOS / desconocido
- Hashing triple: **SHA1 + MD5 + CRC32** por cada ROM
- **Incremental**: omite el re-hasheo si mtime y tamaño no cambiaron
- Base de datos SQLite en `.rommgr/library_pc.db` — sobrevive re-escaneos mediante upsert
- Limpieza automática de entradas huérfanas al finalizar cada escaneo
- Modo rápido (`--quick`) sin hashing para escaneos instantáneos

### Identificación y renombrado
- Matching por SHA1 contra catálogos **No-Intro** y **Redump** en formato DAT XML Logiqx
- `Plan` para previsualizar, `Apply` para ejecutar — nunca sobreescribe sin confirmar
- Renombrado **atómico con rollback**: si algo falla, los archivos vuelven a su estado original
- Los saves se renombran junto al ROM (mismo stem) para no perder el progreso
- **PSX**: nunca renombra `.bin` sin reescribir el `.cue`; genera `.m3u` para sets multi-disco
- Detección y resolución de conflictos de nombre (mismo título canónico, ROMs distintos)

### Conversión y herramientas de biblioteca
- Conversión `.cue+.bin` → `.chd` vía `chdman` (sets PSX, Saturn, Dreamcast)
- Extracción de `.zip`
- Generador de playlists `.m3u` para sets multi-disco
- Verificación de integridad de sets multi-disco
- Búsqueda de saves huérfanos (sin ROM asociada)
- Health check: re-hashea ROMs contra el SHA1 almacenado para detectar corrupción
- **Escaneo de archivos basura**: detecta y elimina `.DS_Store`, thumbs, temporales, etc.

### Estructura de biblioteca (ES-DE compatible)
- Crea automáticamente la estructura de carpetas estándar ES-DE/EmulationStation:
  `psx/ gba/ snes/ megadrive/ ...` + `saves/ bios/ inbox/ media/`
- **Organizar biblioteca**: mueve ROMs existentes a su carpeta de plataforma y actualiza la BD
- `gamelist.xml` en cada carpeta de plataforma con metadatos y rutas de carátulas

### Metadatos y logros
- Scraping desde **ScreenScraper** (título, año, género, publisher, portadas, vídeos)
- Exportación de `gamelist.xml` formato EmulationStation / ES-DE
- Comprobación de compatibilidad con **RetroAchievements** por MD5
  - Caché local de 1 semana para no agotar la API
  - Filtro por plataforma en los resultados
  - Identifica qué versión de tus ROMs es la compatible con logros
  - Exportación CSV

### Sincronización en la nube
- **Multi-fuente**: cada emulador tiene su propia carpeta de saves y su propio path remoto
- Política de conflictos: el archivo más reciente gana; ante ambigüedad, se guardan ambas versiones con sufijo timestamp
- Soporte para Dropbox, OneDrive, Google Drive y cualquier remoto rclone
- Log de operaciones de sync almacenado en SQLite

### Cable Sync (USB directo)
- Copia ROMs y/o saves entre PC y consola Android por USB, sin WiFi
- Tres modos: PC→Consola, Consola→PC, el más reciente gana
- Filtros: solo saves, solo ROMs, o todo
- Deduplicación por SHA1: nunca copia algo que ya está en el destino

### Interfaz web
- SPA embebida — **sin dependencias externas de runtime**, solo Python stdlib
- Operaciones pesadas en background con barra de progreso en tiempo real
- Dos bases de datos independientes: una para el PC y otra para la consola Android

---

## Emuladores compatibles (multi-sync)

| Plataformas | PC | Android (consola) | Saves compatibles |
|---|---|---|---|
| NES · SNES · MD · N64 · GB/GBC/GBA · DS · Dreamcast · Saturn | RetroArch | RetroArch | ✅ Mismos cores → 100% |
| PlayStation (PSX) | DuckStation | DuckStation Android | ✅ `.mcd` |
| PlayStation 2 | PCSX2 | NetherSX2 | ✅ `.ps2` |
| PSP | PPSSPP | PPSSPP Android | ✅ `SAVEDATA/` completo |
| Nintendo DS | MelonDS | MelonDS Android | ✅ `.sav` |
| GameCube / Wii | Dolphin | Dolphin Android | ✅ `.gci` + NAND |

---

## Instalación

### Requisitos
- **Python 3.11+** (recomendado 3.12)
- **rclone** — para cloud sync ([rclone.org](https://rclone.org/))
- **chdman** v0.286+ — para convertir a CHD ([MAME tools](https://www.mamedev.org/tools/))
- **adb** — opcional, para Cable Sync por USB ([Android Platform Tools](https://developer.android.com/tools/releases/platform-tools))

### Instalación rápida

```bash
git clone https://github.com/Rcerezo-dev/Retro-gaming-companion.git
cd Retro-gaming-companion
pip install -e .
```

**Con Conda (recomendado en Windows):**

```bash
conda create -n rom_manager python=3.12
conda activate rom_manager
pip install -e .
```

**Lanzador Windows (sin activar entorno):**

```bat
scripts\rommgr.cmd serve
```

### Binarios externos

Coloca los binarios en `tools/` o añádelos al PATH:

```
tools/
  chdman.exe     ← descargar de mamedev.org/tools
  adb.exe        ← descargar de developer.android.com/tools
```

---

## Configuración

Crea `config.toml` en la raíz del proyecto (o ejecuta `rommgr init-config`):

```toml
[library]
library_root = "E:\\ROMs"           # Raíz de la biblioteca

[sync]
rclone = "rclone"                   # Binario rclone (o ruta completa)

# ── Una entrada por emulador ──────────────────────────────────────────────────
[[sync.sources]]
name      = "RetroArch"
local_dir = "E:\\ROMs\\saves"       # Después de centralizar saves con "Organizar biblioteca"
remote    = "dropbox:/RetroSync/saves/retroarch"

[[sync.sources]]
name      = "DuckStation (PSX)"
local_dir = "C:\\Users\\TU_USUARIO\\Documents\\DuckStation\\memcards"
remote    = "dropbox:/RetroSync/saves/duckstation"

[[sync.sources]]
name      = "PCSX2 (PS2)"
local_dir = "C:\\Users\\TU_USUARIO\\Documents\\PCSX2\\memcards"
remote    = "dropbox:/RetroSync/saves/pcsx2"

[[sync.sources]]
name      = "PPSSPP (PSP)"
local_dir = "C:\\Users\\TU_USUARIO\\Documents\\PPSSPP\\PSP\\SAVEDATA"
remote    = "dropbox:/RetroSync/saves/ppsspp"
sync_all  = true   # sincroniza todos los archivos (estructura de subcarpetas por juego)

[[sync.sources]]
name      = "Dolphin (GC/Wii)"
local_dir = "C:\\Users\\TU_USUARIO\\Documents\\Dolphin Emulator"
remote    = "dropbox:/RetroSync/saves/dolphin"
sync_all  = true

[tools]
chdman = "tools\\chdman.exe"
adb    = "tools\\adb.exe"

[web]
host = "127.0.0.1"
port = 7777

[screenscraper]
user = ""
pass = ""

[retroachievements]
api_key = ""   # retroachievements.org → Settings → Web API Key
```

---

## Uso

### Interfaz web (recomendado)

```bash
rommgr serve
# Abre http://127.0.0.1:7777
```

| Pestaña | Descripción |
|---------|-------------|
| **Inicio** | Dashboard: totales, % match, duplicados, espacio. Botón de escaneo con progreso en tiempo real. |
| **Juegos** | Tabla filtrable por plataforma, región y estado de match. Búsqueda por título o archivo. |
| **Organizar** | Preview de renombrados y conflictos. Botón Apply para ejecutar. |
| **Duplicados** | Grupos de ROMs con el mismo SHA1. Botón para eliminar los sobrantes. |
| **Sync** | Cloud sync multi-emulador. Estado por fuente (RetroArch, DuckStation, PPSSPP…). Log de operaciones. |
| **Cable Sync** | Copia directa PC ↔ consola Android por USB. Tres modos de dirección. |
| **Scraper** | Descarga metadatos y carátulas desde ScreenScraper. Exporta `gamelist.xml`. |
| **RetroAchievements** | Compatibilidad de logros por MD5. Filtro por plataforma. Export CSV. |
| **Herramientas** | CHD, ZIP, M3U, verificación multi-disco, health check, backup BD, estructura de carpetas. |
| **Inbox** | Procesa ZIPs nuevos: identifica plataforma, descomprime y organiza automáticamente. |
| **Ajustes** | Rutas, credenciales, extensiones de save, config de sync automático. |

### CLI

```bash
rommgr serve                            # Arranca la interfaz web
rommgr scan <ruta> [--quick]            # Escanea una carpeta
rommgr status                           # Resumen de la biblioteca
rommgr match                            # Cruza con catálogos DAT
rommgr plan                             # Previsualiza renombrados
rommgr apply                            # Ejecuta renombrados
rommgr duplicates                       # Lista duplicados por SHA1
rommgr report --format json             # Genera reporte de biblioteca
rommgr convert-chd <ruta> --apply       # Convierte PSX a CHD
rommgr sync-saves --apply               # Sincroniza saves con la nube
```

---

## Estructura de biblioteca recomendada

Compatible con **EmulationStation / ES-DE** en PC y Android:

```
library_root/
├── psx/
│   ├── gamelist.xml           ← generado por el Scraper
│   ├── media/
│   │   ├── images/            ← carátulas (mismo nombre que el ROM)
│   │   └── videos/
│   └── Final Fantasy VII (USA).chd
│   └── Final Fantasy VII (USA).m3u
├── gba/
│   └── Metroid Fusion (USA).gba
├── snes/
├── megadrive/
├── n64/
├── nds/
├── gamecube/
├── ...
├── saves/                     ← TODOS los saves de RetroArch (planos)
│   └── Metroid Fusion (USA).srm
├── bios/                      ← BIOS (scph1001.bin, etc.)
└── inbox/                     ← ZIPs nuevos sin organizar → Pilar 2
```

El botón **"Crear estructura"** en Herramientas → Estructura de biblioteca crea todas las carpetas automáticamente.

> **Nota sobre RetroArch PC:** configura Settings → Saving → Savefile Directory apuntando a `library_root/saves/` para que los saves queden centralizados y el cloud sync funcione sin fricción.

---

## Sincronización de saves

### Cloud sync (PC ↔ Nube ↔ Android)

1. Configura rclone con tu servicio preferido: `rclone config`
2. Añade las entradas `[[sync.sources]]` en `config.toml` (ver arriba)
3. En la pestaña **Sync** → pulsa **Sincronizar**

La Anbernic / consola Android usa la misma cuenta de rclone configurada en Termux para hacer el sync en la dirección contraria. Guía detallada: [`docs/sync-cloud.md`](docs/sync-cloud.md).

### Cable sync (PC ↔ Android por USB)

Opciones para montar el almacenamiento Android en Windows:
1. **Tarjeta SD en lector** — el método más rápido y fiable
2. **Termux SFTP** — `sshd` en Termux + WinFsp/SSHFS-Win o `rclone mount`
3. **ADB** — modo directo, no requiere montar unidad

El modo MTP estándar ("Transferencia de archivos") **no** expone una letra de unidad y no es compatible. Guía: [`docs/sync-cable.md`](docs/sync-cable.md).

---

## Catálogos DAT

```
.rommgr/
  catalogs/
    nointro/   ← DATs de cartuchos (GB, GBC, GBA, NES, SNES, N64, DS…)
    redump/    ← DATs de disco (PSX, PS2, PSP, GameCube, Dreamcast…)
```

Descarga los DATs desde [No-Intro](https://www.no-intro.org/) y [Redump](http://redump.org/).
El matcher usa SHA1 para encontrar coincidencias exactas.

---

## Estructura del proyecto

```
src/rom_manager/
  cli.py                     # Entrypoint CLI (argparse)
  config.py                  # AppConfig + SyncSource + lectura de config.toml
  catalog/
    catalog_loader.py        # Parseo DATs XML Logiqx → sha1 → CatalogEntry
    matcher.py               # Búsqueda SHA1 en todos los DATs cargados
  database/
    schema.py                # Tablas SQLite + migraciones automáticas de columnas
    repository.py            # LibraryRepository (upsert, batch, duplicates, prune)
  detection/
    file_classifier.py       # ROM / save / asset / system / unknown
    platform_detector.py     # Plataforma por extensión + contexto de carpeta
    region_parser.py         # Región desde nombre de archivo (No-Intro / GoodTools)
  hashing/
    hash_calculator.py       # SHA1 + MD5 + CRC32, chunks de 1 MB
  scanner/
    rom_scanner.py           # Bucle principal (incremental + stale prune)
  planner/
    operation_planner.py     # RenamePlan: pending / already_correct / conflicts
  renamer/
    file_renamer.py          # rename_rom_with_saves() — atómico con rollback
    cue_rewriter.py          # Reescribe .cue al renombrar sets PSX
  converters/
    chd_converter.py         # .cue+.bin → .chd vía chdman
    zip_extractor.py         # Extracción de .zip
  utils/
    m3u_generator.py         # Genera .m3u para multi-disco
    multidisc_verifier.py    # Verifica integridad de sets
    orphan_finder.py         # Saves sin ROM asociada
    health_checker.py        # Re-hashea ROMs vs SHA1 almacenado
  sync/
    rclone_transport.py      # Wrapper sobre el binario rclone
    save_syncer.py           # list_local_saves() + sync_saves() multi-fuente
    conflict_resolver.py     # El más reciente gana; backup ante ambigüedad
    sync_log.py              # Tabla save_sync_log en SQLite
  scraper/
    screenscraper.py         # Cliente REST ScreenScraper (CRC/MD5/SHA1 + fallback nombre)
    gamelist_writer.py       # gamelist.xml formato EmulationStation / ES-DE
    pegasus_writer.py        # metadata.pegasus.txt formato Pegasus Frontend
  retroachievements/
    ra_client.py             # API_GetGameList; caché .rommgr/ra_cache/ 1 semana
    ra_checker.py            # Cross-reference MD5 + búsqueda alternativa por título
  web/
    server.py                # ThreadingHTTPServer stdlib; todos los endpoints REST
    frontend.py              # SPA HTML+JS inline (sin deps externas)
scripts/
  rommgr.cmd                 # Lanzador Windows (Conda env)
  rommgr.ps1                 # Lanzador PowerShell
tools/
  chdman.exe                 # No incluido en el repo — descargar de mamedev.org
  adb.exe                    # No incluido — descargar de developer.android.com
docs/
  sync-cloud.md              # Guía de cloud sync con rclone
  sync-cable.md              # Guía de cable sync (ADB / SFTP / SD)
  library-structure.md       # Estructura de carpetas ES-DE reference
```

---

## Tests

```bash
pytest
# o con el lanzador Windows:
scripts\rommgr.cmd pytest tests/ -v
```

---

## Hoja de ruta

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | Escaneo, hashing, inventario SQLite, CLI básico | ✅ |
| 2 | Matching SHA1 contra catálogos No-Intro y Redump | ✅ |
| 3 | Plan + Apply — renombrado seguro + conversión CHD | ✅ |
| 4 | Duplicados, escaneo incremental, reportes, interfaz web | ✅ |
| 5 | Cloud sync · Cable Sync · ScreenScraper · RetroAchievements | ✅ |
| 6 | Multi-source sync · Estructura ES-DE · Inbox · Fix duplicados | ✅ |
| 7 | Tracker de tiempo de juego · Vista de cuadrícula · WiFi sync directo | 🔜 |

---

## Licencia

MIT
