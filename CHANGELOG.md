# Changelog — Retro Vault

## [1.2.0] — 2026-09-19 (borrador, pendiente de confirmar el tag)

Release grande: ~100 PRs mergeadas desde v1.1.0 (2026-07-23 → hoy, poco menos
de dos meses). Resumen orientado a usuario, agrupado por capacidad y no por
commit; el detalle línea por línea vive en `Tareas/backlog.md` y en el
historial de Git.

### ✨ Nuevas funcionalidades

- **App Android nativa de sync de saves**: instalable directamente en la
  Anbernic, sincroniza saves/states con Dropbox sin depender de que el PC
  esté encendido — permisos de almacenamiento, escaneo, autenticación OAuth
  de Dropbox, resolución de conflictos por fecha, sync manual y periódico
  cada 15 min desde una pantalla de Ajustes propia.
- **Perfil del dispositivo**: catálogo único de cores y BIOS por plataforma,
  escritura automática de las carpetas de saves/savestates en
  `retroarch.cfg`, manifiesto exportable + restauración, y detección de
  cuándo el layout real de saves se ha desviado de lo esperado.
- **Editor de overrides de RetroArch por juego** (`.opt`): auto-detección,
  listado, edición y copia entre PC y Android sin tocar archivos a mano.
- **Envío/eliminación en bloque a la Anbernic**: marcar juegos con una
  etiqueta reutilizable, filtrar el Cable Sync para que solo copie lo
  marcado, y dos botones nuevos en Juegos para enviar o retirar por lote
  directamente sobre el filtro activo (con copia de seguridad del save antes
  de borrar el ROM).
- **Sync automático al cerrar un emulador** — ya no hace falta sincronizar a
  mano ni esperar al ciclo periódico: al cerrar RetroArch/PCSX2/DuckStation/
  Dolphin en el PC se dispara un cloud sync real en segundos, y **hoy mismo**
  se extendió a la propia Anbernic (cerrar un emulador ahí, con el cable
  puesto, dispara un cable-sync igual de inmediato) — ambos opt-in y
  verificados en vivo con partidas reales.
- **El Inbox puede enviar a la Anbernic lo que acaba de organizar**,
  checkbox opt-in, sin pasar por un cable-sync completo aparte.
- **Carátulas y capturas ya scrapeadas, también en RetroArch**: un botón
  publica la misma imagen que ya usan ES-DE y la propia app en la carpeta
  que RetroArch necesita, sin volver a descargar nada — enlace directo si el
  formato ya es compatible, conversión automática y cacheada si no.
- **Duplicados por región** (p. ej. "USA" vs "Spain" del mismo juego) ahora
  se detectan y se recomiendan con criterio configurable (regiones
  favoritas, o la opción de no tocarlos nunca).
- **Duplicados que cruzan formato de archivo** (mismo juego en `.zip` y sin
  comprimir, o en formatos distintos) se agrupan igual que los duplicados
  normales.
- **Hash real de RetroAchievements para más consolas de disco** (Saturn,
  Dreamcast, GameCube, Wii, además de PSX) — permite descartar copias
  duplicadas sin logros con la misma fiabilidad que ya tenía PSX.
- **Chequeo repetible de sets de disco rotos**, para detectar `.cue`/`.bin`
  dañados antes de que den problemas al jugar.
- **Detección y reubicación de ROMs mal ubicados**, y exclusión de
  plataformas enteras al hacer Cable Sync.
- **Reconstrucción de sets arcade sueltos** por cobertura de CRC, cuando los
  chips de un mismo juego están repartidos sin organizar.
- **Filtro alfabético en Juegos** para bibliotecas grandes por plataforma.
- **Informe del Inbox** con duplicados descartados y conflictos sin resolver
  contados aparte, no solo mezclados en el log.
- **Escáner de fragmentación de saves**: detecta cuando el mismo juego tiene
  copias de save divergentes repartidas por distintos nombres/carpetas.
- **Consolidación de carpetas duplicadas** (Title Case legado vs. slug
  canónico Android) en 11 plataformas, más un aviso automático si el mismo
  patrón vuelve a aparecer con una plataforma nueva.
- Comandos CLI nuevos: generar `.cue` para PSX sueltos sanos,
  `organize-source`/`decompress`/`resolve-duplicates`.
- Se guardan géneros completos y número de jugadores de ScreenScraper (antes
  solo el primer género).

### 🐛 Bugs corregidos

- **Ventanas de consola parpadeando cada 8-10 segundos** con el auto-arranque
  en segundo plano — ninguna herramienta externa (`adb`/`rclone`/`chdman`...)
  pasaba el flag para ocultar su consola salvo una.
- **Traducciones y parches heredaban el título del juego original** en el
  catálogo, contaminando tanto el matching como la detección de duplicados.
- El Cable Sync en modo "espejo completo" podía **borrar carátulas/metadatos
  o archivos no marcados** que no debía tocar.
- El hash de RetroAchievements para PSX/GameCube/Wii usa ahora el disco real
  en vez del archivo completo, evitando falsos "sin logros".
- El paso "mover archivo + actualizar base de datos" del Inbox ya es
  atómico — un fallo a mitad ya no deja el archivo movido sin reflejar en la
  BD.
- El job de emparejamiento (`match`) podía colgarse decenas de minutos con un
  CHD de PSX ambiguo; ahora tiene timeout corto y progreso visible.
- Varios fixes de precisión en el matching de plataforma/arcade (nombre de
  set corto vs. descriptivo, catálogos de núcleo filtrados del índice
  arcade, resolución de rutas de arranque en subcarpetas...).
- El daemon de auto-sync y el de SD-sync se caían por una función interna
  con la firma equivocada.
- Mejor tolerancia de ADB al almacenamiento con permisos restringidos de
  Android 11+.
- El Cable Sync copiaba por error la propia papelera de descartes,
  anidándola dentro del destino.
- Un fallo de exportación rompía la pestaña Cloud con un error en consola.
- El primer sync de una cuenta o carpeta de Dropbox nueva siempre fallaba.
- La NVRAM de arcade nunca se sincronizaba desde la app Android.
- Sincronización de savestates `.fs` de FBNeo/CPS3, antes ignorados.
- Varios fixes de extracción/CRC/enrutado de ZIPs sueltos en el Inbox.

### 🔧 Mejoras técnicas

- Manejo de errores y logging con traceback real en los jobs del Pilar 3
  (sync de saves) — antes algunos fallos quedaban silenciosos.
- División de `web/handlers/config.py` por responsabilidad.
- Optimización de los workflows de GitHub Actions.
- Guard reutilizado (`is_non_canonical_variant`) tanto en el matching por
  título como en la resolución de duplicados, para no repetir el mismo tipo
  de contaminación en dos sitios distintos.

### ⚠️ Pendiente de probar en hardware

- El resto de la matriz de compatibilidad de saves PC↔Android
  (`EMULATOR-COMPAT-2/3/4`) sigue con verificaciones puntuales pendientes,
  ver `Tareas/backlog.md`.

## [1.1.0] — 2026-07-23

Release grande: 78 PRs mergeadas desde v1.0.0. Resumen orientado a usuario;
el detalle línea por línea vive en `Tareas/backlog.md` y en el historial de
Git.

### ✨ Nuevas funcionalidades

- **Pantalla "Revisar copias"**: duplicados por SHA1, versiones distintas y
  colisiones del plan ahora se resuelven en una sola cola, agrupada por
  juego, con una recomendación precalculada (logros RA gana, si no la mejor
  nombrada) y acciones claras — Aplicar / Elegir otra / Copia intencional.
- **Colocación automática de ZIPs sueltos**: los ZIPs que aparecían sin
  organizar en `Unknown\` ahora se identifican por el CRC32 de su contenido
  (sin descomprimir) y se colocan directamente en su carpeta de plataforma o
  como set arcade — sin depender del nombre del archivo, que a menudo miente.
- **Clasificador de basura "inteligente"**: usa lo que la app ya sabe (BD de
  catálogos, listas MAME de BIOS/chips) para separar ROMs reales de
  infraestructura arcade y colecciones fuente, en vez de una lista fija de
  extensiones.
- **Playtime real desde RetroArch**: el tiempo jugado se lee de los logs
  `.lrtl` de RetroArch (PC y consola) en vez de introducirse a mano.
- **"¿A qué juego hoy?"**: sugerencia ponderada en Overview (pendientes +
  valoración + tiempo sin jugar) con botón para abrir el juego directamente.
- **Deshacer último apply**: si un renombrado sale mal, un botón revierte el
  último lote completo sin tocar la base de datos a mano.
- **Backup automático de la base de datos** antes de cada apply.
- **Sync de cheats (`.cht`)** además de saves, config de core (`.opt`) y
  playtime — mismo mecanismo de carpeta + remoto rclone.
- **Resolución de duplicados por logros RA** integrada en el flujo de
  Organizar/Inbox, no solo como pantalla aparte.
- Auditorías UX completas de casi todas las pestañas (Inicio, Cloud, Anbernic,
  Herramientas, Formatos, Assets, Colección, Plan/Organizar, Scraper, Inbox,
  Modo TV, Settings) — decenas de mejoras de claridad y consistencia.
- Documentación de onboarding para desarrolladores: guía de arquitectura,
  glosario de dominio y guía de "primeros 30 minutos".

### 🐛 Bugs corregidos

- Duplicados fantasma que reaparecían tras cada scan (el escáner no excluía
  la papelera `_descartados/` ni `$RECYCLE.BIN`).
- Sets multi-disco PSX (`Disc 1/2/3`) que "Resolver con RA" podía descartar
  pensando que eran copias alternativas del mismo disco.
- Rutas de `tools/adb.exe` con `/` que rompían `subprocess` en Windows.
- Extracción de ZIP que abortaba el archivo completo por una sola colisión
  en vez de extraer el resto.
- El catálogo nunca escribía la plataforma de vuelta a la base de datos tras
  un match, dejando `Unknown\` con miles de archivos sin organizar.
- BIOS de arcade sin mapear que quedaban sueltas en vez de moverse a `bios/`.
- Borrado de "duplicados" que solo comparaba nombre de archivo, no
  contenido — podía borrar archivos genuinamente distintos.
- DuckStation Android: el auto-sync reintentaba en cada conexión un mapping
  con `Permission denied` en Android 11+ sin root; ahora se excluye con el
  workaround documentado.
- Preview del sync por cable en modo ADB siempre decía "no accesible" en
  vez de contar los saves remotos de verdad.
- `rommgr sync` headless (Task Scheduler) se saltaba en silencio las fuentes
  de config RetroArch / cheats / playtime que el sync desde la web sí incluye.

### 🔧 Mejoras técnicas

- Estado mutable global consolidado en `web/state.py` (antes disperso).
- Selector de dispositivo, wizard de cloud y flujo de Cable Sync simplificados.
- Cobertura de tests directa para los caminos de rollback de
  `rename_rom_with_saves`/`move_disc_set_to_subfolder` (antes solo se
  ejercitaban indirectamente).
- 927 tests automatizados (arrancó la release anterior con bastantes menos).

### ⚠️ Pendiente de probar en hardware

- Prueba en un PC limpio sin Python (`D37-8`) — el instalador se valida en
  este equipo, pero no se ha confirmado en una máquina totalmente ajena.
- Sync de cheats/config RetroArch/playtime con consola real conectada.
