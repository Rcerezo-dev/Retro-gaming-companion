# ROM Manager Local

Herramienta local para escanear, identificar, organizar y sincronizar colecciones de ROMs de videojuegos retro.

Diseñada para un setup compartido: una única colección de ROMs compatible con PC (RetroArch de escritorio) y Anbernic RG 556 (RetroArch para Android), con sincronización de saves en la nube incluida.

---

## Características

### Escaneo e inventario
- Escaneo recursivo de cualquier carpeta — clasifica cada archivo como ROM, save, asset de frontend, soporte del sistema o desconocido
- Hashing SHA1 + MD5 + CRC32 para cada ROM
- Escaneo incremental: omite el re-hasheo de ROMs cuyo mtime y tamaño no han cambiado
- Inventario SQLite en `.rommgr/library.sqlite` — sobrevive re-escaneos mediante upsert
- Limpieza automática de entradas huérfanas: registros de archivos ya borrados del disco se eliminan de la BD tras cada escaneo
- Detección de plataforma por extensión de archivo
- Detección de región desde el nombre de archivo (estilo No-Intro/GoodTools)

### Identificación y renombrado
- Matching contra catálogos locales No-Intro y Redump en formato DAT XML Logiqx (por SHA1)
- `plan` para previsualizar renombrados, `apply` para ejecutar — nunca sobrescribe sin confirmar
- Renombrado atómico con rollback: si falla en mitad del proceso, deja los archivos en el estado original
- Los saves y save states se renombran junto al ROM (mismo stem)
- Soporte PSX completo: nunca renombra `.bin` sin reescribir el `.cue`
- Detección de duplicados exactos por SHA1

### Conversión y herramientas de biblioteca
- Conversión de sets PSX `.cue+.bin` a `.chd` vía `chdman`
- Extracción de archivos `.zip`
- Generación de playlists `.m3u` para sets multi-disco
- Verificación de integridad de sets multi-disco
- Búsqueda de saves huérfanos (sin ROM asociada)
- Health check: re-hashea ROMs contra el SHA1 almacenado para detectar corrupción
- Escaneo de múltiples carpetas a la vez
- Backup de la base de datos

### Metadatos y logros
- Scraping de metadatos (títulos, portadas, año, género) desde ScreenScraper
- Exportación de `gamelist.xml` formato EmulationStation (compatible con RetroArch/ES-DE)
- Comprobación de compatibilidad con RetroAchievements por MD5 (con caché local de 1 semana)
- Exportación de resultados de RA en CSV

### Sincronización
- Sincronización de saves entre PC y nube (Dropbox y otros) vía rclone
- Política de conflictos: el archivo más reciente gana; ante ambigüedad, se guardan ambas versiones con sufijo de timestamp
- **Cable Sync**: copia directa de ROMs y/o saves entre PC y Anbernic por USB (sin WiFi), con tres modos — PC→Anbernic, Anbernic→PC, y el más reciente gana

### Interfaz web local
- SPA embebida sin dependencias externas — solo Python stdlib
- Todos los escaneos y operaciones pesadas corren en background con barra de progreso en tiempo real

---

## Instalación

Requiere **Python 3.11+**.

```bash
git clone https://github.com/your-username/Retro_gaming_app.git
cd Retro_gaming_app
pip install -e .[dev]
```

> Con Conda:
> ```bash
> conda create -n rom_manager python=3.12
> conda activate rom_manager
> pip install -e .[dev]
> ```

En Windows hay un lanzador de conveniencia:

```bat
scripts\rommgr.cmd <comando>
```

---

## Configuración

```bash
rommgr init-config
```

Ejemplo de `config.toml`:

```toml
[library]
library_root = "E:\\ROMs"         # Raíz de toda la biblioteca (ROMs + saves)

[sync]
remote = "dropbox:/RetroSync/saves"
rclone = "rclone"

[tools]
chdman = "tools/chdman.exe"       # Ruta al binario chdman (v0.286+)

[web]
host = "127.0.0.1"
port = 7777

[screenscraper]
user = ""
pass = ""

[retroachievements]
api_key = ""                      # Obtener en retroachievements.org → Settings → Web API Key
```

---

## Uso

### Interfaz web (recomendado)

```bash
rommgr serve
# Abre http://127.0.0.1:7777/ en el navegador
```

La interfaz web cubre todas las funcionalidades del proyecto:

| Pestaña | Contenido |
|---------|-----------|
| Overview | Totales de juegos, saves, assets, % de match, duplicados y espacio desperdiciado. Botón de escaneo con progreso en tiempo real. |
| Games | Lista filtrable por plataforma y estado de match; descarga de reporte JSON/CSV |
| Plan | Preview de renombrados pendientes y conflictos; botón Apply |
| Duplicates | Grupos de ROMs con el mismo SHA1 y espacio recuperable |
| Sync | Sincronización de saves con Dropbox/rclone; log de operaciones |
| Cable Sync | Copia directa PC ↔ Anbernic por USB; tres modos de dirección; filtro por saves y/o ROMs |
| Scraper | Scraping de metadatos desde ScreenScraper; exportación gamelist.xml |
| RetroAchievements | Comprobación de compatibilidad de logros; exportación CSV; caché local |
| Settings | Configuración de rutas, credenciales y extensiones de save |
| Tools | Conversión a CHD, extracción ZIP, M3U, verificación multi-disco, health check, backup BD |
| Library | Gestión de carpetas de biblioteca; explorador de archivos |

### CLI

```bash
# Escanear una carpeta
rommgr scan <ruta>

# Ver resumen de la biblioteca
rommgr status

# Matchear contra catálogos DAT
rommgr match

# Renombrado (previsualizar + ejecutar)
rommgr plan
rommgr apply

# Duplicados y reportes
rommgr duplicates
rommgr report --format json --output report.json
rommgr report --format csv  --output report.csv

# Conversión PSX a CHD
rommgr convert-chd <ruta-psx> --apply --delete-source

# Sincronización de saves
rommgr sync-saves --apply
```

---

## Catálogos DAT

El matcher lee archivos `.dat` en formato XML Logiqx (estándar No-Intro y Redump).

Colócalos en:

```
.rommgr/
  catalogs/
    nointro/   ← DATs de cartuchos (GB, GBC, GBA, NES, SNES, N64, DS, …)
    redump/    ← DATs de disco (PSX, PS2, PSP, GameCube, Wii, Dreamcast, …)
```

Descarga los DATs desde [No-Intro](https://www.no-intro.org/) y [Redump](http://redump.org/).

---

## Cable Sync — Transferencia por USB

Para copiar archivos entre PC y Anbernic sin WiFi, Windows necesita acceder a la consola como una ruta normal del sistema de archivos. Hay tres opciones:

1. **Tarjeta SD en el PC** — sacar la SD de la Anbernic y conectarla directamente (método más rápido y fiable)
2. **Termux SFTP** — instalar `sshd` en Termux y montar la Anbernic como unidad de red en Windows
3. **WinFsp + SSHFS** — montar el almacenamiento Android por SSH como unidad de Windows

El modo MTP estándar (Android en "Transferencia de archivos") **no** expone una letra de unidad y no es compatible con la herramienta.

---

## Estructura del proyecto

```
src/rom_manager/
  cli.py                           # Comandos CLI
  config.py                        # AppConfig + lectura de config.toml
  logging_utils.py
  catalog/
    catalog_loader.py              # Parseo de DATs XML Logiqx → sha1→CatalogEntry
    matcher.py                     # CatalogMatcher: búsqueda SHA1 en todos los DATs
  database/
    schema.py                      # Esquema SQLite + migraciones automáticas
    repository.py                  # LibraryRepository (upsert, batch, prune, duplicados)
  detection/
    file_classifier.py             # ROM / save / asset / system / unknown
    platform_detector.py           # Plataforma desde extensión
    region_parser.py               # Región desde nombre de archivo
    filename_normalizer.py
    set_detector.py
  hashing/
    hash_calculator.py             # SHA1 + MD5 + CRC32, chunks de 1 MB
  scanner/
    rom_scanner.py                 # Bucle principal de escaneo (incremental + prune)
    asset_scanner.py
    save_scanner.py
  planner/
    operation_planner.py           # Genera RenamePlan con estados pending/correct/conflict
  renamer/
    file_renamer.py                # rename_rom_with_saves() — atómico con rollback
  converters/
    chd_converter.py               # Conversión PSX .cue+.bin → .chd vía chdman
    zip_extractor.py               # Extracción de .zip
  utils/
    m3u_generator.py               # Genera .m3u para sets multi-disco
    multidisc_verifier.py          # Verifica integridad de sets multi-disco
    orphan_finder.py               # Saves sin ROM asociada
    health_checker.py              # Re-hashea ROMs vs SHA1 almacenado
  scraper/
    screenscraper.py               # Cliente REST ScreenScraper
    platform_ids.py                # Mapa plataforma → ID ScreenScraper
    gamelist_writer.py             # Genera gamelist.xml formato EmulationStation
  retroachievements/
    ra_client.py                   # API_GetGameList; caché .rommgr/ra_cache/
    ra_checker.py                  # Cross-reference MD5 + búsqueda por título
    ra_platform_ids.py             # Mapa plataforma → RA console ID
  sync/
    rclone_transport.py            # Wrapper sobre el binario rclone
    conflict_resolver.py           # Lógica: el más reciente gana
    save_syncer.py                 # Orquestador de sync
    sync_log.py                    # Tabla save_sync_log en SQLite
  reports/
    reporter.py                    # LibraryReport → JSON / CSV
  web/
    server.py                      # ThreadingHTTPServer stdlib (sin deps externas)
    frontend.py                    # SPA embebida (HTML/CSS/JS)
tools/
  chdman.exe                       # Binario externo (v0.286); no incluido en el repo
docs/
  android-sync.md                  # Guía de sync en la Anbernic (Termux/FolderSync)
tests/
  test_catalog_matcher.py
  test_chd_converter.py
  test_conflict_resolver.py
  test_config.py
  test_duplicates.py
  test_file_classifier.py
  test_filename_normalizer.py
  test_operation_planner.py
  test_region_parser.py
  test_reporter.py
  test_save_syncer.py
  test_web_server.py
```

---

## Hoja de ruta

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | Escaneo, hashing, inventario SQLite, CLI básico | Completada |
| 2 | Matching por SHA1 contra catálogos No-Intro y Redump | Completada |
| 3 | Plan + Apply: renombrado seguro + conversión CHD para PSX | Completada |
| 4 | Detección de duplicados, escaneo incremental, reportes, interfaz web | Completada |
| 5 | Sincronización de saves (PC ↔ Anbernic RG 556) vía rclone | Completada |
| 6 | ScreenScraper, RetroAchievements, Cable Sync, herramientas de biblioteca | Completada |

---

## Tests

```bash
pytest
# o con el lanzador de Windows:
scripts\rommgr.cmd pytest tests/ -v
```

---

## Licencia

MIT
