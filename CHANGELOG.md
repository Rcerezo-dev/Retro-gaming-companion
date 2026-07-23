# Changelog — Retro Vault

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
