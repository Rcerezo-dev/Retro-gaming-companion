# Glosario — jerga retro-gaming para desarrolladores

Qué significa cada término y **por qué importa en este código**. Pensado para
leer en 10 minutos antes de tocar el pipeline. Complemento de
[`onboarding.md`](onboarding.md).

---

## Identificación de ROMs

**ROM** — Volcado (dump) de un cartucho o disco de juego a un archivo. La misma
ROM puede circular con mil nombres de archivo distintos; por eso aquí la identidad
de un juego es su **hash**, nunca su nombre.

**DAT** — Catálogo de ROMs "canónicas": para cada juego lista su nombre oficial,
tamaño y hashes (SHA1/MD5/CRC32). Es la referencia contra la que `matcher.py`
compara tu biblioteca. Viven en `.rommgr/catalogs/`.

**No-Intro / Redump** — Los dos grupos de preservación que publican los DATs de
referencia. **No-Intro** cubre cartuchos (NES, SNES, GBA…); **Redump** cubre
discos (PSX, PS2, Dreamcast…). De ahí las carpetas `catalogs/nointro/` y
`catalogs/redump/`.

**Logiqx XML / clrmamepro** — Los dos formatos de archivo DAT. Logiqx es XML;
clrmamepro es un formato de texto con paréntesis (`game ( name "..." rom (...) )`).
`catalog_loader.py` tiene un sniffer que detecta cuál es y un parser para cada uno.

**Match / confianza** — Cruce de tu ROM contra el DAT. Por SHA1 → confianza
`high` (identidad exacta). Si no hay hash coincidente se puede intentar por
nombre → confianza menor. El renombrado automático solo se fía del match exacto.

**Región** — `(USA)`, `(Europe)`, `(Japan)`… en el nombre canónico. Importa
porque la versión de cada región es una ROM distinta (hash distinto) y, p. ej.,
RetroAchievements suele soportar solo una de ellas.

**Header** — Algunos formatos (p. ej. NES) llevan una cabecera de metadatos
antes de los datos reales. Dos archivos "iguales" pueden diferir en hash solo
por el header; los DATs suelen hashear sin él.

## Formatos de disco y multi-disco

**`.bin` + `.cue`** — Formato clásico de imagen de CD (PSX): el `.bin` tiene los
datos y el `.cue` es un archivo de texto que describe las pistas **por nombre de
archivo**. De ahí la regla sagrada del proyecto: *nunca renombrar un `.bin` sin
reescribir su `.cue`* (`renamer/cue_rewriter.py`) — un `.cue` que apunta a un
nombre viejo deja el juego roto.

**Sidecar** — Archivo compañero que no contiene los datos del juego pero lo
acompaña (`.cue`, `.m3u`, `.ccd`, `.sbi`). El verificador multidisco los trata
aparte para no confundirlos con imágenes.

**CHD** — Formato comprimido de MAME para imágenes de disco ("Compressed Hunks
of Data"). Un set `.bin+.cue` de 700 MB queda en un solo `.chd` de ~450 MB que
RetroArch lee directamente. La conversión la hace el binario externo `chdman`
(`converters/chd_converter.py`).

**`.m3u`** — Playlist de texto plano. Para juegos de varios discos (FF VII son
3), RetroArch necesita un `.m3u` que liste los discos para poder "cambiar de
disco" en el emulador (`utils/m3u_generator.py`).

**IPS / BPS / UPS** — Formatos de parche binario (romhacks, traducciones). Se
aplican sobre una ROM base exacta — otra razón por la que la identidad por hash
importa (`patch/`).

## Saves y emulación

**Save (partida guardada)** — El guardado *del propio juego* (la batería del
cartucho o la memory card): `.srm`, `.sav`, `.mcd`… Es lo que el sync sincroniza
entre PC y consola.

**Savestate** — Foto exacta de la RAM del emulador en un instante (`.state`).
Solo funciona en el mismo emulador/core; por eso saves y states se tratan y
sincronizan por separado (`save_extensions` vs `state_extensions` en config).

**Core** — Un emulador empaquetado como plugin de **libretro** (la API que usa
RetroArch): `mgba_libretro.dll` emula GBA, `swanstation` PSX, etc. El formato del
save puede depender del core — usar el mismo core en PC y Android garantiza
compatibilidad 100%.

**RetroArch** — El frontend multi-emulador (ejecuta cores) disponible en PC y
Android. Emulador "standalone" = el que va por libre (DuckStation, PPSSPP,
Dolphin), cada uno con su propia carpeta de saves — por eso existe
`[[sync.sources]]` con una entrada por emulador.

**BIOS** — Firmware original de la consola que algunos emuladores necesitan
(`scph1001.bin` para PSX). No es una ROM y **nunca** se renombra ni se
sincroniza; vive en `bios/` (`detection/bios_checker.py` valida sus hashes).

**ES-DE (EmulationStation Desktop Edition)** — Frontend visual de biblioteca
(la "estantería" de juegos). Define la estructura de carpetas por plataforma
(`psx/`, `gba/`…) que este proyecto crea, y lee los `gamelist.xml`.

**gamelist.xml** — Archivo por plataforma con metadatos y rutas de carátulas que
ES-DE muestra. Lo genera `scraper/gamelist_writer.py`.

**Scraping** — Descargar metadatos y carátulas de una BD online
(**ScreenScraper.fr** aquí) identificando el juego por hash o nombre.

**RetroAchievements (RA)** — Servicio de logros para juegos retro. Identifica
las ROMs por **MD5** (no SHA1) y solo soporta versiones concretas — el checker
(`retroachievements/`) te dice qué ROM de tu colección es la compatible.

## Infraestructura del proyecto

**rclone** — CLI que habla con ~70 nubes (Dropbox, Drive…). Es el transporte del
cloud sync; un "remote" es una cuenta configurada (`dropbox:/RetroSync/saves`).

**ADB (Android Debug Bridge)** — CLI oficial para hablar con un dispositivo
Android por USB (`adb push/pull/shell`). Es el transporte del Cable Sync
(`sync/adb_transport.py`).

**Termux** — Emulador de terminal Linux para Android. En la consola se usa para
ejecutar rclone (cloud sync desde el lado Android) o un servidor SFTP.

**Anbernic RG556** — La consola Android de referencia del proyecto (pantalla
táctil + mandos). Cuando los docs dicen "la consola", es esto.

**Inbox** — Concepto propio del proyecto: carpeta vigilada (`inbox/`) donde
sueltas ZIPs nuevos; el pipeline los identifica, descomprime, renombra y archiva
solo (`web/inbox_pipeline.py`).
