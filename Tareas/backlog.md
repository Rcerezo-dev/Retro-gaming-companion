# Retro Vault — Backlog

> Single source of truth for pending work. Updated every session.
> Last updated: 2026-07-23 (MEJ-2/3/4/5, VAL-FIX-4/5/7, INBOX-FIX-4,
> REV43-52, TEST-GAP-1 cerrados; release v1.1.0 publicada)
> 2026-08-29: archivadas ~33 secciones completadas a archivo.md; triage de
> docs/ideas/ + docs/Feedback/29/8.md (DEDUP-RENAME, HERR-FIX, PSX-ORPHAN-5,
> ZIP-ROUTE-7, ANBERNIC-PICK-6/7, SAGE-4, GAME-BLOCKLIST, 5 filas nuevas en
> ROADMAP-IDEAS)
> 2026-08-30: INBOX-ORPHAN-3 arreglado (fix + limpieza de 104 carpetas huérfanas
> reales) — ver INBOX-ORPHAN-4/5, hallazgos nuevos derivados de la investigación
> 2026-08-30: INBOX-FIX-6 arreglado (ZIPs de consola ahora se descomprimen tras
> el apply; guard de `extract_zip` corregido para no bloquear `.iso` sueltos de PS2)
> 2026-08-30: INBOX-ORPHAN-4 resuelto (4 duplicados GameCube borrados, mismo
> dump peor comprimido) — hallazgo nuevo INBOX-RA-HASH-GAP (RA no compara discos)
> 2026-08-31: hallazgos LIBRARY-SYNC-STALE-1 (biblioteca corregida el 08-30 sin
> sincronizar a la Anbernic) y GBA-SAVE-PATH-1 (GBA no encuentra saves tras
> instalar emuladores nuevos, bloqueado por ADB unauthorized)
> 2026-09-01: auditoría LIBRARY-AUDIT (issue #275) — bug real en `rommgr
> duplicates` (agrupa archivos sin hash como duplicados falsos), 126,4 GB en
> `Unknown/` sin organizar, 96,4 GB de ZIPs de consola sin descomprimir, ~14,4 GB
> seguros de recuperar en duplicados de consola (arcade excluido a propósito)
> Completed tasks → `Tareas/diario/archivo/archivo.md`
> Arquitectura actual: `docs/architecture/architecture.md`
> Organizado por épica de GitHub (2026-08-15) — convención en `.claude/CLAUDE.md` § Gestión de tareas.

Regla de branching: una rama por tarea → PR a `develop`. Las sub-tareas que comparten
fichero o son la misma unidad de cambio se agrupan en una sola rama. Refactores
grandes de un fichero van **siempre separados**. Flujo completo: `CONTRIBUTING.md`.

---

## Debug Playbook

Checklist de puntos de entrada para diagnosticar cualquier problema en el app.

| ID | Técnica | Cómo | Dónde mirar |
|----|---------|------|-------------|
| DBG-1 | Lanzar servidor con logs en terminal | `scripts\rommgr.cmd serve` (o `-m rom_manager serve`) — stdout muestra requests, errores y jobs | Terminal |
| DBG-2 | Verificar esquema SQLite | `/db-check` skill, o `sqlite3` / DB Browser sobre `.rommgr/*.db` | `database/repository.py`, `schema.py` |
| DBG-3 | Testear pipeline por etapas | `rommgr.cmd scan --dry-run` → `plan` → (nunca `apply` sin plan) | CLI |
| DBG-4 | Diagnosticar jobs en background | DevTools → Network → `/api/job-status` cada 2s; buscar `result_ts` ausente en respuesta | `web/server.py`, `web/jobs/manager.py` |
| DBG-5 | Verificar ADB / sync | `tools\adb.exe devices`, `tools\adb.exe shell ls /sdcard/RetroArch/saves` | `sync/adb_transport.py` |
| DBG-6 | Logging puntual por módulo | `import logging; logging.basicConfig(level=logging.DEBUG)` en el módulo sospechoso | `logging_utils.py` |
| DBG-7 | Test integración completa | Skill `/test-pipeline` — scan → match → plan sobre datos sintéticos | — |

### Síntomas frecuentes

| Síntoma | Dónde mirar |
|---------|-------------|
| UI no actualiza | `frontend.py` polling + `result_ts` en `server.py` |
| Config no persiste tras guardar | `_handle_save_config()` en `handlers/config.py` (recarga obligatoria) |
| Renombrado PSX roto | `file_renamer.py` (`move_disc_set_to_subfolder` — mueve el set conservando nombres de `.bin`) + `operation_planner.py` |
| ADB no encuentra saves | `adb_transport.py` (mapeo de rutas por emulador) |
| Circular import al arrancar | Late imports en `cable_sync_daemon.py` / `inbox_pipeline.py` |
| 404 en rutas registradas | `router.dispatch()` — ver BUG-ROUTING-404 en `archivo.md` |
| ZIP suelto mal clasificado en el junk-scan | `web/builders/folders.py` — orden de passes: BIOS/infra/arcade por nombre → CRC consola (`matcher.crc_index()`) → colección por contenido → votación arcade (`load_arcade_crc_index()`) → extensión interna. Identificación completa de un caso: `Tareas/zip-route-identificacion.md` |
| "Organizar identificados" movió algo mal | `web/zip_router.py` (`_route_identified` — política: nunca sobreescribir, conflictos en `route_skipped` del resultado del job "inbox") |

---

## Pilar 1 — Limpieza y organización inicial de la biblioteca — → #202

Detectar basura, clasificar ZIPs sueltos y dejar la biblioteca organizada por
plataforma con nombre canónico.

### ANBERNIC-ROMTREE — Dos árboles de ROMs conviviendo en la SD (hallazgo 2026-08-29)

`ls` en vivo sobre `/storage/521D-04EA/` confirma que el árbol canónico
`ROMs/<plataforma-minúscula>/` (41 carpetas, el que usa la app) **convive** con 9 carpetas
huérfanas en mayúscula/nombre-humano en la raíz de la SD (`Game Boy Advance`, `Game Gear`,
`Nintendo DS`, `Atari 2600`, `Master System`, `Famicom Disk System`, `Game Boy`,
`Game Boy Color` + `NGC` sin confirmar hoy) — exactamente lo que ya listaba el pendiente
§7 de `docs/emulador-canonico-rg556.md` del 2026-08-25, pero **no está parado**: `Game Gear`
tiene mtime 2026-08-27 y `Game Boy Advance` 2026-08-13, ambas **posteriores** al día en que
se hizo la migración a `ROMs/`. Algo (Daijishō todavía apuntando a las rutas viejas, o un
ROM añadido a mano) sigue escribiendo en el árbol huérfano después de la reorganización.
No es un problema de esta herramienta (el scan/rename de rom_manager ya usa `ROMs/`) sino
de que el dispositivo tiene dos raíces válidas por SAF y nada impide que caigan ROMs en la
vieja. Pendiente: identificar qué app escribe ahí (probablemente Daijishō, ver pendiente
"Re-apuntar Daijishō a `SD:/ROMs/<plataforma>`" en el mismo doc) y mover el contenido de las
9 carpetas a `ROMs/` antes de borrarlas — revisar primero si hay progreso/ROMs sin duplicar.

| ID | Task | Notes |
|----|------|-------|
| ANBERNIC-ROMTREE-1 | Confirmar qué proceso sigue escribiendo en las carpetas huérfanas de la raíz de la SD tras la migración a `ROMs/` (2026-08-25) y cerrar esa fuente antes de mover nada | Hardware + investigación | XS | ⬜ documentado 2026-08-29 |
| ANBERNIC-ROMTREE-2 | **Hecho 2026-09-02**: `Game Boy Advance`, `Game Boy`, `Game Boy Color` ya no existían (resueltas en sesión anterior, esta fila estaba desactualizada); `NGC` nunca fue un caso real (NTFS/Windows trata `NGC` y `ngc` como la misma carpeta). Las 5 restantes (`Atari 2600`, `Game Gear`, `Nintendo DS`, `Master System`, `Famicom Disk System`) organizadas vía `rommgr organize-source --apply` tras el fix de `ARCADE-DAT-CONTAMINATION` — ninguna tenía ya ROMs sueltos reales (limpiadas por `resolve-duplicates` esa misma mañana o solo `media/`), `Master System` se autoborró al quedar vacía | ver `Día52.md` | ✅ 2026-09-02 |

---

### LIBRARY-AUDIT — Auditoría de biblioteca real: duplicados, ZIPs sin organizar, espacio desperdiciado — → #275

Origen: usuario conectó la Anbernic (`E:\Carpetas anbernic`) y detectó a ojo
duplicados (varias copias de un mismo juego GBA) y ZIPs mal colocados.
Auditoría real 2026-09-01 contra `library_pc.db` (scan del mismo día) — sin
tocar ningún archivo, solo investigación. Detalle completo de cifras y
metodología en el issue #275; aquí solo las tareas de implementación.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| LIBRARY-AUDIT-1 | **Bug confirmado y arreglado**: `get_duplicate_groups()` (`database/repositories/duplicates.py:15-38`) no filtraba `sha1 IS NULL OR sha1=''` → agrupaba los 750 archivos sin hash de la BD como un único "grupo duplicado" falso (mezcla ROMs de MAME sin relación entre sí). Filtro añadido (`sha1 IS NOT NULL AND sha1 != ''` en ambas partes de la query). Confirmado que era el único método afectado de los 6 puntos de llamada — `_review_groups_for_repo` ("Revisar copias") ya filtraba `if row["sha1"]:` por separado, sin tocar. Test nuevo `test_empty_sha1_rows_are_not_grouped_together` (`tests/test_duplicates.py`) | `database/repositories/duplicates.py:15-38` | ✅ (`feature/library-audit-1-duplicates-null-sha1`) |
| LIBRARY-AUDIT-2 | **Resuelto sin tocar el pipeline**: `_run_inbox_pipeline()` ya aceptaba cualquier ruta como origen (no atado a `config.inbox.path`). Solo faltaba un punto de entrada headless — nuevo subcomando `rommgr organize-source <path> [--target-root] [--delete-source] [--exclude-platform PLATFORM] [--apply]` (dry-run por defecto, mismo patrón que `convert-chd`) que lo invoca síncronamente con un `JobManager()` propio. `--exclude-platform` (repetible) aparta los archivos de esa plataforma a una carpeta temporal antes de correr el pipeline y los restaura a su ruta exacta al terminar — necesario porque el paso 1 (extracción) ya enruta sets arcade completos por CRC sin pasar por el paso 6, así que filtrar solo el movimiento final llegaría tarde. Añadido tras verificar en vivo contra la biblioteca real que el código actual manda MAME/FBNeo/Arcade a una única carpeta `arcade/`, distinta de las carpetas mame/fbneo/cps1-3 ya existentes — decisión del usuario 2026-09-01: organizar solo consolas por ahora, dejar arcade para decidir aparte. Tras un `--apply` sin archivos restantes, borra la carpeta de origen vacía. Cubre también `LIBRARY-AUDIT-6` (mismo comando, apuntado a las 6 carpetas huérfanas). **Ejecutado en real 2026-09-01** contra `E:\Carpetas anbernic\Unknown` (`--exclude-platform MAME FBNeo Arcade --apply`): 9.058 organizados, 7.493 duplicados exactos descartados, 1 conflicto resuelto por RA, 2.610 conflictos sin resolver (contenido distinto con mismo nombre, sin tocar), 13.803 archivos de arcade apartados y restaurados intactos tal como se pidió. **Hallazgo real durante la ejecución** (ver `LIBRARY-AUDIT-EXCLUDE-GAP` más abajo): 932 archivos sin identificar en la BD también resultaron ser arcade (detección CRC en vivo del paso 1, independiente de `--exclude-platform`) y sí se movieron a `arcade/` — decisión explícita del usuario 2026-09-01: dejarlos donde están, no revertir | `cli.py` (`organize-source`) | ✅ (`feature/library-audit-2-6-organize-source`), ejecutado en real |
| LIBRARY-AUDIT-3 | Nuevo subcomando `rommgr decompress <path> [--delete-source] [--apply]` (dry-run por defecto, patrón `convert-chd`). Reutiliza `extract_directory()` tal cual — ya excluye arcade por nombre de carpeta y sets multi-disco, no hizo falta tocar el extractor. **Ejecutado en real 2026-09-02** contra `E:\Carpetas anbernic`: 29.643 descomprimidos, 47.132 saltados, 2 fallidos (`Breath of Fire III (USA).zip`, `Spyro 2 - Ripto's Rage! (USA).zip` — ZIP inválido, ficheros dañados preexistentes, no es bug de código, pendiente revisión manual/re-descarga) | `cli.py` (`decompress`) | ✅ (`feature/library-audit-2-6-organize-source`), ejecutado en real |
| LIBRARY-AUDIT-4 | Nuevo subcomando `rommgr resolve-duplicates [--apply]` (dry-run por defecto). Reutiliza `_build_review_queue`+`apply_all_review_recommendations` (mismo mecanismo que "Revisar copias" en la web) tal cual — el gate de arcade no necesitó lógica nueva: los grupos MAME/FBNeo/Arcade se excluyen con `exclude_duplicate_group(reason="arcade_intentional")`, el mecanismo de "copia intencional" que ya existía, así que también dejan de aparecer en la pestaña web para siempre. **Ejecutado en real 2026-09-02** contra `E:\Carpetas anbernic` (tras el decompress, que generó más duplicados: ZIP + extraído): 18.986 grupos totales (10.403 arcade excluidos, 8.583 de consola, 814 con conflicto de nombre resueltos aparte) → **10.021 archivos descartados** (papelera vía `discard_to_trash`, no borrado permanente), 0 errores | `cli.py` (`resolve-duplicates`) | ✅ (`feature/library-audit-2-6-organize-source`), ejecutado en real |
| LIBRARY-AUDIT-5 | **Causa raíz encontrada y arreglada**: no era necesaria una nueva detección de "tamaño sospechoso" — la causa real es un bug de "skip pegajoso" en `rom_scanner.py:135-139`: `get_known_roms()` solo comparaba `(mtime, size)`, así que una fila con `sha1=''` (de un scan `--quick` o del scan ADB, que siempre graba `sha1=""`) nunca se re-hasheaba en un scan completo posterior porque su mtime/size no cambian. `get_known_roms()` ahora también expone si la fila ya tiene hash (`database/repositories/games.py:48-62`), y el scan completo ignora el "ya conocido" cuando falta. Una vez re-hasheado de verdad, si el contenido no matchea el catálogo simplemente queda "sin matchear" (mecanismo ya existente, `_unmatched_reason()` con motivo `"no_sha1"` en `web/builders/library.py:472-477`) — no hace falta un estado nuevo en `health_checker.py`. Tests: `test_get_known_roms_flags_missing_sha1` (`tests/test_repository.py`), `test_scan_backfills_hash_after_quick_scan` (`tests/test_scanner.py`) | `scanner/rom_scanner.py:135-144`, `database/repositories/games.py:48-62` | ✅ (`feature/library-audit-5-scanner-stale-hash`) |
| LIBRARY-AUDIT-6 | **Hecho 2026-09-02** — ver `ANBERNIC-ROMTREE-2` | ver `ANBERNIC-ROMTREE` arriba | ✅ 2026-09-02 |
| LIBRARY-AUDIT-7 | **Bug real encontrado y arreglado durante la ejecución de LIBRARY-AUDIT-3**: `decompress` crasheaba a mitad de biblioteca (`UnicodeEncodeError`) con nombres de ROM reales que traen caracteres fuera del codepage `cp1252` de la consola de Windows (ej. `├`, dibujo de caja) — Python usa el codepage de consola para `stdout` incluso con la salida redirigida a fichero/log. Fix: `main()` reconfigura `sys.stdout`/`sys.stderr` a UTF-8 con `errors="replace"` al arrancar, una sola vez para todos los subcomandos (no solo `decompress`) | `cli.py:371-378` (`main()`) | ✅ (`develop`, commit directo — fix de una línea bloqueante en el camino crítico de LIBRARY-AUDIT-3) |

---

### LIBRARY-AUDIT-EXCLUDE-GAP — `--exclude-platform` no cubre la detección arcade en vivo del paso 1 (hallazgo real 2026-09-01)

Origen: ejecución real de `organize-source "Unknown/" --exclude-platform MAME FBNeo Arcade --apply`
contra la biblioteca real. `--exclude-platform` aparta por adelantado los archivos cuya fila en
`games.platform` ya vale MAME/FBNeo/Arcade (13.803 archivos, correctamente apartados y
restaurados intactos). Pero el paso 1 del pipeline (`_run_inbox_pipeline`, extracción) hace su
propia detección de sets arcade completos **por CRC en vivo**, independiente de la columna
`platform` de la BD (`_is_arcade_zip_container()`, `inbox_pipeline.py`) — así que un archivo sin
identificar todavía en la BD (`platform IS NULL`, nunca escaneado/matcheado) puede reconocerse
como arcade *durante la propia ejecución* y moverse a `arcade/` sin que `--exclude-platform` lo
vea venir. Confirmado en real: **932 archivos** así movidos (verificado con
`grep -c "es un set arcade completo — movido sin extraer"` sobre el log de la ejecución), 438 más
detectados pero ya existentes en destino (no tocados, sin riesgo). Sin sobreescrituras ni pérdida
de datos en ningún caso — los 932 quedaron en una carpeta de plataforma válida (`arcade/`), solo
no es la que se pedía dejar intacta esta vez. Decisión del usuario 2026-09-01: dejarlos donde
están, no revertir.

| ID | Task | Notas |
|----|------|-------|
| LIBRARY-AUDIT-EXCLUDE-GAP-1 | Si se vuelve a usar `--exclude-platform` sobre una carpeta con archivos sin escanear/matchear todavía, avisar (o aplicar el mismo filtro) también en el paso 1 del pipeline — hoy solo protege lo que la BD ya sabía | `cli.py` (`organize-source`), `web/inbox_pipeline.py` (`_is_arcade_zip_container`) | 🔴 pendiente, no bloqueante |

---

### ARCADE-DAT-CONTAMINATION — DATs de consola mezclados en el catálogo arcade causan falsos positivos (hallazgo real 2026-09-02, BLOQUEANTE)

**BUG DE SEVERIDAD ALTA** — descubierto en vivo durante un piloto de `organize-source` contra
`H:\ROMs\amiga`, con datos reales movidos por error (revertido en el momento, sin pérdida).

Causa raíz: `.rommgr/catalogs/arcade/` contiene, junto a los DAT arcade legítimos (MAME,
"FinalBurn Neo (ClrMame Pro XML, Arcade only).dat"), **15 DAT de FBNeo que son núcleos de
CONSOLA, no arcade**: `FDS`, `Game Gear`, `Master System`, `SNES`, `Megadrive`, `NES`,
`PC-Engine`, `ColecoVision`, `Fairchild Channel F`, `MSX 1`, `NeoGeo Pocket`, `Neogeo`,
`SG-1000`, `SuprGrafx`, `TurboGrafx16`, `ZX Spectrum` — nombrados "(ClrMame Pro XML, X only)"
pero viviendo en la carpeta `arcade/`, probablemente descargados junto a los DAT arcade sin
reparar en que FBNeo también emula consolas.

`load_arcade_crc_index()` (`catalog/mame_loader.py:122-150`) lee **todos** los `.dat` de ese
directorio sin distinguir sistema — indexa cada CRC de cada DAT en un único diccionario
`crc32 -> {set names}`. `_is_arcade_zip_container()` (`web/inbox_pipeline.py:429-445`), usado por
el paso 1 del pipeline de Inbox/organize-source para decidir "esto es un set MAME completo, no
extraer, mover a `arcade/`", solo comprueba si el CRC de cada entrada del ZIP está en ese índice
contaminado — sin verificar de qué DAT viene.

**Reproducido en real**: `organize-source "H:\ROMs\amiga" --apply` movió 23 ZIPs a `arcade/`.
Inspeccionados uno a uno (contenido real del ZIP, no el nombre):
- **4 sí son arcade de verdad** (`batman.zip`, `Hook (Europe)...zip`, `legend.zip`,
  `Batman (Europe) (Budget - The Hit Squad) (conflicto-inbox 2026-08-13).zip` — sets multi-chip
  MAME reales) — correctamente en `arcade/`.
- **19 NO son arcade ni Amiga** — son ROMs de SNES (`.sfc`), Genesis (`.md`) y Master System
  (`.sms`)/PC Engine (`.pce`) con nombre "estilo Amiga" que mentía sobre el contenido real
  (`Aladdin (Europe) (AGA).zip` contenía literalmente `Aladdin (USA).sfc`). Revertidos a mano de
  vuelta a `amiga/` — **siguen mal ubicados ahí** (su plataforma real es SNES/Genesis/SMS/PCE, no
  Amiga), pendientes de mover a su carpeta correcta una vez ADT-2 esté resuelto.

**Por qué era bloqueante**: `Game Gear`, `Famicom Disk System` y `Master System` — 3 de los 4
huérfanos pendientes de `LIBRARY-AUDIT-6`/`ANBERNIC-ROMTREE` en `H:\ROMs` — son exactamente
plataformas cuyo DAT contaminaba el índice. **Resuelto 2026-09-02** (ARCADE-DAT-CONTAMINATION-1 y
-2): ya es seguro volver a ejecutar `organize-source`/Inbox contra cualquier carpeta.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ARCADE-DAT-CONTAMINATION-1 | **Hecho**: los 16 DAT de núcleos de consola (Neogeo y NeoGeo Pocket contados aparte) movidos de `.rommgr/catalogs/arcade/` a `.rommgr/catalogs/_fbneo_console_unused/` — dato local, no versionado (`.rommgr/catalogs/*` está en `.gitignore`), sin commit necesario para esta parte | `.rommgr/catalogs/arcade/*.dat` | ✅ 2026-09-02 |
| ARCADE-DAT-CONTAMINATION-2 | **Hecho**: `_is_console_only_dat()` nuevo filtra por nombre de fichero (`"...only)"` que no sea `"Arcade only)"`) en ambos bucles de `load_arcade_crc_index()`/`load_arcade_manifest()` — defensa en profundidad aunque el directorio vuelva a contaminarse. Verificado contra los ficheros reales que causaron el fallo (`Aladdin (Europe) (AGA).zip` ya no vota como arcade, `batman.zip` sigue detectándose bien). Tests: `test_arcade_crc_index_ignores_console_only_fbneo_dats`, `test_arcade_manifest_ignores_console_only_fbneo_dats` | `catalog/mame_loader.py:122-193` | ✅ (`fix/arcade-dat-contamination`) |
| ARCADE-DAT-CONTAMINATION-3 | **Hecho 2026-09-02**: los 19 ZIPs aislados en una carpeta temporal fuera de `amiga/` (para no sesgar la detección por ruta) y pasados por `organize-source --apply` — 8 a `snes/`, 2 a `mastersystem/`, 2 a `pcengine/`, 7 resultaron ser duplicados exactos de Genesis ya presente en `megadrive/` (descartados de forma segura a `megadrive/_descartados/`, nunca borrados). 0 falsos positivos de arcade. Verificado archivo por archivo contra el log real (el contador "Organizados: 31" del comando no cuadraba con los 19 originales — investigado y confirmado que no hay pérdida: son operaciones internas del pipeline, no archivos perdidos) | `H:\ROMs\amiga\` → `snes/`, `mastersystem/`, `pcengine/`, `megadrive/_descartados/` | ✅ 2026-09-02 |
| ARCADE-DAT-CONTAMINATION-4 | **Auditoría hecha 2026-09-02** (heurística: ZIPs de 1 sola entrada con extensión de consola no ambigua, sobre las carpetas `arcade/` de ambas bibliotecas — el sitio con más exposición histórica al bug). `H:\ROMs\arcade`: 1.372 ZIPs revisados, **0 sospechosos**. `E:\Carpetas anbernic\arcade`: 15.952 ZIPs revisados, **706 sospechosos** (661 NES, 17 SNES, 14 Nintendo 64DD, 5 Master System, 4 PC Engine, 3 Famicom Disk System, 2 Commodore 64). **47 de los 706 resultaron ser falsos positivos de la propia heurística de investigación** (no de la app): chips arcade reales nombrados con sufijo de socket tipo `.u1`/`.prg` que coincide por casualidad con extensión de N64DD/Commodore 64/NES — el pipeline real (CRC de verdad, ya con el fix) los identificó correctamente como arcade y los dejó donde estaban, confirmando que el fix funciona bien incluso con nombres engañosos. Los ~659 restantes eran genuinos, nombres estilo No-Intro/Goodtools sin mentir sobre el contenido (a diferencia de los de `amiga/`). **672 de los 706 originales tienen fecha de modificación 2026-08-28/29** (semanas antes de esta sesión) — confirma que el bug llevaba tiempo afectando también al Inbox del día a día (`zip_router.py` usa el mismo `load_arcade_crc_index()` contaminado, no solo `organize-source`), 9 del 2026-09-01. Sin auditar aún el resto de carpetas de ambas bibliotecas más allá de `arcade/` y `amiga/` | `E:\Carpetas anbernic\arcade\` | ✅ auditoría |
| ARCADE-DAT-CONTAMINATION-5 | **Hecho 2026-09-02**: los 706 aislados en carpeta temporal fuera de `arcade/` y pasados por `organize-source --apply`. Resultado real (verificado contra el log completo, no solo el resumen): **293 organizados** a su plataforma real, **753 duplicados exactos** descartados de forma segura (`_same_content()` verificado antes de descartar — quedan recuperables en `_ARCADE_CONFLICTOS_REVISAR_MANO/_descartados/`), **47 vueltos a `arcade/`** correctamente (ver -4, falsos positivos de mi heurística), **240 conflictos de nombre** (mismo nombre en destino, contenido distinto — no se tocan, dejados intactos para revisión manual). Carpeta temporal renombrada a `_ARCADE_CONFLICTOS_REVISAR_MANO` para que quede visible, sin borrar nada — sigue conteniendo los 240 conflictos + los duplicados descartados. 0 pérdida de datos | `E:\Carpetas anbernic\arcade\` → `nes/`, `snes/`, etc. + `_ARCADE_CONFLICTOS_REVISAR_MANO/` | ✅ 2026-09-02 |
| ARCADE-DAT-CONTAMINATION-6 | Revisar a mano los 240 conflictos de nombre dejados en `E:\Carpetas anbernic\_ARCADE_CONFLICTOS_REVISAR_MANO\` (mismo nombre que un archivo ya organizado, contenido distinto — puede ser una revisión/hack/versión diferente del mismo juego) | `E:\Carpetas anbernic\_ARCADE_CONFLICTOS_REVISAR_MANO\` | 🔴 pendiente, revisión manual del usuario |
| ARCADE-DAT-CONTAMINATION-7 | **Hecho 2026-09-03**: hallazgo de `DECOMPRESS-ARCADE-GAP-4` — 190 ZIPs intactos + 203 carpetas de residuo suelto (206 detectadas, 3 resultaron ser la raíz completa de `atari5200/`/`intellivision/`/`wonderswan/` — no se aislaron enteras, solo los 57 ficheros sueltos individuales que votaban arcade en esa raíz, para no arrastrar contenido legítimo) aislados en `E:\Carpetas anbernic\_ARCADE_MISFILED_STAGING\` (fuera de `Unknown/`, ver -8) y pasados por `organize-source --apply`: **190/190 ZIPs reclasificados** a `arcade/` sin incidentes (incluye `psx__Raystorm (Japan).zip` — confirma la corrección de `DECOMPRESS-ARCADE-GAP-1` de que el set base `raystorm` sí existe, solo estaba mal etiquetado), 26 conflictos de nombre sin resolver (ficheros sueltos tipo `1.bin`/`7.bin` con nombre duplicado en destino). Los residuos sueltos (`organize-source` no los reconoce — solo detecta arcade por CRC en ZIPs intactos, no en ficheros sueltos) se resolvieron en 2 pasadas con scripts de sesión: (1) 134/242 items con backup 100% íntegro en un único ZIP de `arcade/` → descartados a papelera; 26 carpetas vacías (residuo del propio aislamiento) → eliminadas tras confirmar que no tenían contenido. (2) Los 82 restantes, diagnosticados contra el DAT primario (`MAME 0.286`) con herencia `romof`/`cloneof` real, no solo comparación 1:1 de ZIP: **2 recuperados de verdad** (`grobda`, `sonson` — Wii Virtual Console, sets completos que nunca habían llegado a `arcade/`, re-empaquetados y movidos), **45 descartados** (confirmado que `arcade/` YA los cubre al 100% sin depender del residuo — split-set de MAME, chips compartidos con el padre/otro clon ya presentes). **Quedan 35 sin tocar** — **diagnóstico fino completado 2026-09-03** (sesión aparte, solo lectura: parseo completo del DAT primario con cadena `romof` resuelta hasta la raíz + CRC real de `arcade/` leído de cabecera de ZIP sin descomprimir, 16.101 ZIPs, 70.697 CRCs únicos). Los "6 sin nombre reconocido" bajan a **2**: los 3 `wii__*` usan el título del juego en vez del nombre de set MAME en el nombre de carpeta — 2 no calzaban por nombre literal (`Chelnov (Japan)...`, `Ironclad (USA)...`), identificados por votación de CRC de contenido real contra el índice del DAT primario (`chelnov`: 19/19 ficheros coinciden exacto, `ironclad`: 8/9); el tercero (`chelnovjbl`) ya llevaba el nombre de set correcto. Categorización final de los 35 (mismo criterio que los 47 ya resueltos: solo descartable si `arcade/` por sí solo, sin el residuo, ya cubre el 100% del set exigido por el DAT con herencia `romof`):
- **6 descartables** (`arcade/` ya cubre el 100% sin el residuo): `commandoj`, `firetrapbl`, `rastsagaa`, `springbd`, `chelnov` (identificado por CRC, `wii__Chelnov (Japan)...`) — 5/5 con `covered_by_arcade_alone=True` confirmado.
- **1 caso límite, NO descartado bajo el criterio estricto**: `ironclad` (`wii__Ironclad (USA)...`) — el residuo no aporta ningún chip único (0 de sus 9 ficheros son necesarios-y-ausentes-de-otro-sitio), pero el set completo sigue incompleto en toda la biblioteca (faltan 6 chips en cualquier parte) — `arcade/` solo no llega al 100%, así que no cumple el criterio estricto pese a que borrarlo no perdería nada real. Decisión pendiente del usuario: ¿aplicar aquí el mismo criterio de "sin aporte único = descartable" o tratarlo aparte?
- **15 recuperables por combinación** (residuo aporta chip(s) únicos + `arcade/` ya tiene el resto → juntos llegan al 100% del set exigido, mismo patrón que `grobda`/`sonson` pero sin ser autosuficientes solos — necesitan re-empaquetar combinando con chips ya existentes en el ZIP de `arcade/`): `badlandsb` (15/35 chips únicos), `eswatbl2` (38/53), `pangba` (16/25), `carnivalca` (15/35), `carnivalh` (8/29), `carnivalmm` (1/24), `popeyeb2` (1/25), `blasterkit` (8/29), `hydrap2` (9/51), `hustlerb2` (2/11), `hustlerb3` (2/11), `hustlerb4` (6/16), `hustlerb6` (3/12), `hustlerd` (3/11), `cadashso` (4/16).
- **14 realmente incompletos en toda la biblioteca** (ni el residuo ni `arcade/` juntos llegan al 100% exigido por el DAT — mismo patrón que `raystormj/o/u`, no recuperables sin re-descargar el chip que falta): `badlandsm` (falta 1 chip), `betafrce` (6), `pangbc` (15), `spinner` (13), `venture4` (8), `venture5a` (8), `venture5b` (15), `clowns1` (6), `starfirea` (11), `bsebman` (8), `bsebmanbl2` (8), `exerionb2` (6), `exerionba` (10), `chelnovjbl` (2).

Nada tocado en disco — solo lectura. Ver `ARCADE-DAT-CONTAMINATION-10` para ejecutar las 4 acciones derivadas | `E:\Carpetas anbernic\_ARCADE_MISFILED_STAGING\` | ✅ mayormente resuelto (277/312 items); 🟡 diagnóstico de los 35 restantes completo, ejecución pendiente (`ARCADE-DAT-CONTAMINATION-10`) |
| ARCADE-DAT-CONTAMINATION-10 | **✅ Hecho 2026-09-03** (confirmación del usuario "hazlas todas"), acciones 1-3 ejecutadas con script de sesión (solo lectura hasta el momento de escribir, verificación de CRC antes y después de cada escritura, nunca sobreescribe un ZIP existente): **(1) 6 descartados** — `commandoj`, `firetrapbl`, `rastsagaa`, `springbd`, `chelnov` (criterio estricto original) + `ironclad` (criterio ampliado: 0 aporte único, aunque el set siga incompleto en el resto de la biblioteca — tratado igual con el "sí, todas" del usuario) — movidos a `_ARCADE_MISFILED_STAGING\_descartados\` (papelera, recuperable, nunca borrados). **(2) 15 re-empaquetados**: para cada set, ZIP nuevo en `arcade/` combinando los chips únicos del residuo + los chips ya existentes en algún ZIP de `arcade/` (extraídos de su fuente real, sin descomprimir a disco), con el nombre interno exacto que exige el DAT — `badlandsb.zip` (35 roms: 15+20), `eswatbl2.zip` (53: 38+15), `pangba.zip` (25: 16+9), `carnivalca.zip` (35: 16+19), `carnivalh.zip` (29: 9+20), `carnivalmm.zip` (24: 4+20), `popeyeb2.zip` (25: 11+14), `blasterkit.zip` (29: 8+21), `hydrap2.zip` (51: 9+42), `hustlerb2.zip` (11: 2+9), `hustlerb3.zip` (11: 3+8), `hustlerb4.zip` (16: 8+8), `hustlerb6.zip` (12: 3+9), `hustlerd.zip` (11: 3+8), `cadashso.zip` (16: 4+12) — los 15 verificados íntegros (`zipfile.testzip()` sin corrupción) tras escribir, residuo original movido a `_descartados/` en cada caso. **(3) 14 aparcados** en `_ARCADE_MISFILED_STAGING\_incompletos_pendiente_redescarga\` (sin tocar contenido, solo reubicados para que el estado quede visible — mismo patrón que `raystormj/o/u`, ninguno recuperable sin re-descargar el chip que falta en toda la biblioteca): `badlandsm`, `betafrce`, `pangbc`, `spinner`, `venture4`, `venture5a`, `venture5b`, `clowns1`, `starfirea`, `bsebman`, `bsebmanbl2`, `exerionb2`, `exerionba`, `chelnovjbl`. `rommgr scan` de refresco: 100.909 archivos, 0 errores, 16 huérfanos limpiados. **(4) `H:\ROMs` sin ejecutar** — disco no montado en esta sesión (solo `C:`, `D:`, `E:`), queda igual que `ARCADE-DAT-CONTAMINATION-9` | `E:\Carpetas anbernic\_ARCADE_MISFILED_STAGING\`, `E:\Carpetas anbernic\arcade\` | 🟢 E: hecho (1-3), 🔴 H: pendiente (disco no conectado, ver -9) |
| ARCADE-DAT-CONTAMINATION-8 | `Unknown/` concentra **3.039** de los ZIPs con voto mayoritario arcade fuerte (de un total de 3.229 en toda `E:\Carpetas anbernic` fuera de `neogeo/`) — no se tocó, es la bandeja de no-identificados y necesita su propio análisis de por qué quedó ahí sin clasificar antes de decidir si reorganizar en bloque | `E:\Carpetas anbernic\Unknown\` | 🔴 pendiente |
| ARCADE-DAT-CONTAMINATION-9 | Repetir la auditoría completa de `DECOMPRESS-ARCADE-GAP-4`/`ARCADE-DAT-CONTAMINATION-7` contra `H:\ROMs` — no se pudo hacer el 2026-09-03 porque el lector SD no estaba conectado. **Nota del usuario**: esperar un volumen de contaminación parecido al de `E:\Carpetas anbernic` — son en gran parte las mismas ROMs (misma librería origen), no una biblioteca independiente sin relación | `H:\ROMs\` | 🔴 pendiente, requiere conectar el lector SD |

---

### DECOMPRESS-ARCADE-GAP — `decompress` dañó sets arcade mal ubicados fuera de carpetas arcade (hallazgo real 2026-09-02, causado por acciones de esta sesión)

**Encontrado auditando la estructura de `psx/`** a petición del usuario. `decompress`
(`converters/zip_extractor.py:41-54`, `_ARCADE_FOLDER_NAMES`) solo protege un ZIP arcade si
alguna carpeta ANCESTRA de su ruta se llama literalmente `mame`/`arcade`/`fbneo`/`fba`/`neogeo`/
`mame200X`/`mame_libretro` — a diferencia de `organize-source`, que verifica el CRC real
(`_is_arcade_zip_container`, ya arreglado hoy en `ARCADE-DAT-CONTAMINATION`). Si un ZIP arcade
está mal ubicado en una carpeta NO-arcade (p. ej. `psx/`, un caso de contaminación histórica
independiente y anterior a hoy), `decompress` no lo reconoce y lo extrae, destruyendo el
contenedor multi-chip que el core arcade necesita intacto.

`decompress --apply` se ejecutó hoy contra ambas bibliotecas completas (`E:\Carpetas anbernic` y
`H:\ROMs`) como parte de `LIBRARY-AUDIT-3`. Ambas tenían, desde antes de hoy, 7 sets arcade
mal ubicados directamente en `psx/` (mismos 7 juegos en las dos: `gunbirdj`, `gunbirdk`,
`raystormj`, `raystormo`, `raystormu`, `riotw`, `ryujina` — Gunbird, Raystorm y Ryujin/Riot, todos
con versión PSX también, probable origen de la confusión de plataforma original). `decompress` los
extrajo, dejando solo 2-3 chips sueltos por carpeta (un set real necesita bastantes más — el log
de hoy registró 16/11/9 archivos extraídos para copias de estos mismos juegos que sí estaban
protegidas en `arcade/`).

**Re-verificado a fondo 2026-09-02 (sesión siguiente) — la conclusión de `H:\ROMs` de arriba era
incorrecta, y `raystormj/o/u` nunca fueron sets completos, en ninguna de las dos bibliotecas**:

- **`gunbirdj`, `gunbirdk`, `riotw`, `ryujina` — CERO pérdida real, en las dos bibliotecas.**
  El backup de ayer solo se había buscado en `E:\arcade\`; en `H:\ROMs\arcade\mame\` también
  existen los 4 ZIP (`gunbirdj.zip`, `gunbirdk.zip`, `riotw.zip`, `ryujina.zip`), verificados con
  `unzip -t` (sin errores) y con nombres de chip idénticos a los ficheros sueltos de `psx/`. Los 4
  de `E:\arcade\` también verificados igual. Los ficheros sueltos en `psx/gunbirdj\`, `gunbirdk\`,
  `riotw\`, `ryujina\` (ambas bibliotecas) son puro residuo del bug de `decompress` — el ZIP
  canónico nunca se tocó, ya vive en su sitio correcto (`arcade/`). Solo falta limpieza.
- **`raystormj`/`raystormo`/`raystormu` — nunca fueron sets jugables completos, independientemente
  de hoy.** Verificado contra `MAME 0.286 (arcade).dat` (líneas 871105-871196): los 3 son
  **clones** (`cloneof="raystorm" romof="raystorm"`) de un set base `raystorm` que **no existe en
  ninguna biblioteca** (`find` sin resultados en `H:\` ni `E:\`, tampoco en `_descartados/`) —
  sin él faltan siempre `e24-02.1`, `e24-03.2`, `e24-04.27`, `e24-09.14`, `m534002c-14.ic353`,
  `tt01.ic652`, `tt04` (heredados por `merge=`), así que ningún core arcade puede arrancarlos aun
  con el ZIP del clon perfecto. Además `raystormo` y `raystormu` ya les faltaba `e24-06.3` (ROM
  propio del clon, sin `merge=`, dat exige 2 ficheros y solo había 1) **antes** de que `decompress`
  tocara nada — nunca fueron ni siquiera clones completos. `psx/Raystorm (Japan).zip` (10 MB, en
  ambas bibliotecas, intacto) **no cubre nada de esto**: es el port comercial de PS1 del juego, un
  producto distinto, no la ROM MAME (confirmado por tamaño/formato — la ROM MAME real pesaría
  ~13 MB en varios ficheros `.ic`/`.4`/`.1`, no un único ISO de 10 MB).

  **CORRECCIÓN 2026-09-03 (`DECOMPRESS-ARCADE-GAP-4`)**: esta conclusión era incorrecta —
  `psx/Raystorm (Japan).zip` se descartó solo por tamaño/nombre, sin abrir el ZIP. Inspección real
  de sus 11 entradas confirma que es un repack no oficial que SÍ contiene el set base `raystorm`
  completo (`e24-02.1`, `e24-03.2`, `e24-04.27`, `e24-09.14`, `tt04`... exactamente los ficheros que
  se daban por perdidos) más `raystormj/`, `raystormo/`, `raystormu/` en subcarpetas — mismo patrón
  que el repack de `Ryujin` ya identificado. El contenido nunca estuvo perdido, solo mal etiquetado;
  la eliminación de los 7×2 restos sueltos en `DECOMPRESS-ARCADE-GAP-1` no perdió nada real (la copia
  íntegra seguía en este ZIP), pero la conclusión "nunca recuperable" del punto 14 del `Día52` no era
  correcta. Ver `ARCADE-DAT-CONTAMINATION-7` — este ZIP se reclasificó junto con el resto del hallazgo.

No se ha tocado nada en la biblioteca real durante esta re-verificación (solo lectura:
`ls`/`find`/`unzip -t`/`sha1sum`, y consulta del `.dat`) — decisión de limpieza/descarte pendiente
del usuario.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DECOMPRESS-ARCADE-GAP-1 | ✅ **Resuelto 2026-09-02**: confirmado cero pérdida real en los 7 sets. Con confirmación del usuario, borrados los 7×2 restos de `psx/` (`gunbirdj`, `gunbirdk`, `riotw`, `ryujina` — ZIP canónico intacto y verificado con `unzip -t` en `arcade/` de LAS DOS bibliotecas; `raystormj/o/u` — nunca fueron sets completos ni antes de hoy, clones de un `raystorm` base inexistente en ninguna biblioteca, `raystormo`/`raystormu` además sin su propio ROM único `e24-06.3`). **Hallazgo adicional en la misma verificación**: un 8º caso no catalogado ayer — 10 chips sueltos de `ryujin` (el set *padre*, no `ryujina`) directamente en la raíz de `psx/` (sin subcarpeta) en ambas bibliotecas, residuo de extraer `psx/Ryujin (Japan) (v1.00).zip` (repack no oficial que bundlea `ryujin`+`ryujina`, aún intacto en `E:\`). Backup canónico verificado íntegro en `H:\ROMs\arcade\mame\ryujin.zip`. Borrados también los 10×2 chips sueltos tras verificar el respaldo. BD refrescada en ambas (`H:\ROMs` 1 huérfano limpiado, `E:\Carpetas anbernic` 27), 0 errores | `H:\ROMs\psx\` y `E:\Carpetas anbernic\psx\` (ya limpio) | ✅ hecho |
| DECOMPRESS-ARCADE-GAP-2 | ✅ Resuelto junto a GAP-1 — mismo borrado cubrió los restos redundantes de las dos bibliotecas (la nota original solo mencionaba `E:\`, en realidad `H:\` tenía el mismo problema y ya se limpió también) | `E:\Carpetas anbernic\psx\`, `H:\ROMs\psx\` | ✅ hecho |
| DECOMPRESS-ARCADE-GAP-3 | ✅ **Resuelto 2026-09-02**: `is_arcade_zip_container()` (movida de `inbox_pipeline.py` a `zip_extractor.py`, única fuente ahora — `organize-source` la reutiliza vía `_run_inbox_pipeline`) enchufada en `extract_zip()`/`extract_directory()` como parámetro opcional `arcade_crc_index`, chequeada además del nombre de carpeta ancestro. `decompress` (CLI) carga el índice con `load_arcade_crc_index(config.catalogs_arcade_dir)` y lo pasa. Test nuevo `test_arcade_zip_in_unaudited_folder_caught_by_crc` (ZIP arcade en carpeta `psx/`, solo detectable por CRC). 1140/1140 tests en verde, `ruff` limpio | `converters/zip_extractor.py`, `web/inbox_pipeline.py`, `cli.py` | ✅ hecho |
| DECOMPRESS-ARCADE-GAP-4 | ✅ **Auditoría hecha 2026-09-03**: el riesgo *futuro* ya estaba cerrado por GAP-3 (CRC real, no nombre de carpeta). Auditado si además queda contaminación *histórica* fuera de `arcade/` en `E:\Carpetas anbernic` con voto mayoritario (varias entradas/ficheros de una misma carpeta coincidiendo con el mismo set arcade, no un CRC suelto — un solo hit aislado con un índice de 147.813 CRCs es ruido estadístico esperable, no señal). Resultado: 190 ZIPs intactos + 203 carpetas de residuo ya extraído + 57 ficheros sueltos en raíz de plataforma (`atari5200/`, `intellivision/`, `wonderswan/`) fuera de `Unknown/` (que sola concentra 3.039 ZIPs adicionales, caso aparte — ver `ARCADE-DAT-CONTAMINATION-8`). Ver `ARCADE-DAT-CONTAMINATION-7` para la reclasificación. `H:\ROMs` sin auditar — lector SD no montado, pendiente para otra sesión (`ARCADE-DAT-CONTAMINATION-9`) | `E:\Carpetas anbernic\` (todas las plataformas) | ✅ auditoría |

---

### PSX-STRUCTURE — Auditoría de estructura de `psx/` (2026-09-02, a petición del usuario)

| ID | Task | Notas |
|----|------|-------|
| RA-HASH-SUBDIR-1 | **Bug encontrado 2026-09-02** verificando `Tekken 3 (USA).bin` (Anbernic) para reparación cruzada: `ra_hash_psx.py::_find_boot_executable` (línea 178) solo busca el ejecutable de arranque en el directorio raíz ISO9660. `SYSTEM.CNF` de Tekken 3 apunta a `cdrom:\TEKKEN3\SLUS_004.02;1` (subcarpeta) — `_parse_boot_exe_name` (línea 146) solo pela las barras invertidas *iniciales*, así que `exe_name` queda como `"TEKKEN3\SLUS_004.02"` con la barra interna intacta, y `_find_root_file` (línea 106, solo mira la raíz) nunca lo encuentra → `compute_psx_ra_hash` devuelve `None` en silencio para cualquier juego cuyo BOOT= viva en subcarpeta (patrón común en PS1, no es solo Tekken 3). Root cause confirmado leyendo el `SYSTEM.CNF` real del disco, no solo síntoma. **✅ Arreglado
2026-09-02** (rama `fix/ra-hash-psx-subdir-boot`, [PR #286](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/286), mergeado a `develop`): `_find_root_file` reescrito para
recorrer cada componente de ruta separado por `\` (nuevo `_root_dir_location` + `_find_entry`
genérico con flag de directorio) antes de buscar el fichero final, en vez de mirar solo el
directorio raíz. Verificado contra `Tekken 3 (USA)` real: el hash ahora coincide exactamente con la
entrada real de RA (id 11259, "Tekken 3", 81 logros) en vez de devolver `None`. Test nuevo
`test_compute_psx_ra_hash_boot_in_subdirectory`. 1132/1132 tests en verde, `ruff` limpio. Recálculo en frío contra la biblioteca PSX real (1.175 ROMs): 324 pasan a tener hash calculable y coincidente con RA | `src/rom_manager/retroachievements/ra_hash_psx.py:106-178` | ✅ arreglado y mergeado ([PR #286](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/286)) |
| PSX-STRUCTURE-1 | **Recuento exacto 2026-09-02** (parseo real de `FILE` en cada `.cue`, no solo conteo): `H:\ROMs\psx` tenía **78 `.cue` que referencian algún `.bin` inexistente**. Tras descartar los que ya tienen un `.chd` con el mismo nombre (cue obsoleto, juego ya convertido — 45 casos) y los que viven en `_descartados/` (copia ya perdedora, 6 casos), quedaban **33 sets realmente rotos/en riesgo**. **2 reparados el mismo día** usando `.bin` sanos hallados huérfanos en `E:\Carpetas anbernic\psx` (ver PSX-STRUCTURE-2): `Wild Arms (USA)` y `Tekken 3 (USA)` (ver `RA-HASH-SUBDIR-1`). Quedaban 31 sin tocar. **Revisión caso a caso completada 2026-09-02 (sesión siguiente)**: el hallazgo real es que **la inmensa mayoría (28/31) NO era pérdida de datos** — eran huérfanos de ANTES de la migración a subcarpeta-por-juego (`.cue` sueltos en la raíz de `psx/`, referenciando nombres de pista que ya no existen porque el juego se reorganizó en su subcarpeta con un `.bin` distinto), o casos donde `resolve-duplicates` de ayer descartó a `_descartados/` un `.chd` sano de otra región/edición mientras dejaba como "canónico" un set roto de otra edición — el juego seguía disponible, solo mal señalizado. Reparado con confirmación del usuario: **4 `.cue` de 1 pista regenerados** sobre `.bin` intactos que solo les faltaba el sidecar (`Hogs of War (Europe)`, `MediEvil 2 (Europe) (Es,It,Pt)`, `Dino Crisis (Spain)`, `Tomb Raider III - Adventures of Lara Croft (Spain)`); **11 `.chd` sanos restaurados** desde `_descartados/` a su propia subcarpeta (`Namco Museum Vol. 1/3/4 (USA)`, `Tekken 2 (USA) (Rev 1)`, `Twisted Metal III (USA) (Rev 1)`, `Resident Evil 2 - Dual Shock Ver. (USA) (Disc 1/2)`, `Theme Park (World)`, `Small Soldiers (USA, Europe)`, `Gundam Battle Assault (USA)`, `Darkstalkers - The Night Warriors (USA)`, `Street Fighter Alpha - Warriors' Dreams (Europe)`); **2 `.bin` de `Parasite Eve II (Spain)` Disc 1/2** reubicados desde carpetas mal nombradas a su carpeta correcta con `.cue` nuevo, más sus `.chd` USA de respaldo también restaurados. Todos los `.cue`/`.bin`/carpetas huérfanas ya superados movidos a `_descartados/` (nunca borrados). BD refrescada, 0 errores. **Quedan 3 sin tocar, documentados para re-descarga** (sin backup real en ninguna biblioteca, decisión del usuario de no mezclar pistas sueltas de otra región sin verificar): `Mortal Kombat 3 (Europe)` (59/62 pistas, sin `.chd` de respaldo en ninguna parte), `Street Fighter Collection (USA) (Disc 1) (v1.1)` y `Street Fighter Collection (Europe) (Disc 1)` (a ambos les falta justo la pista de datos; solo hay un fragmento `.chd` suelto de esa pista con nombre USA en `_descartados/`, no un disco completo verificado) | `H:\ROMs\psx\*.cue` | 🟡 en progreso, 30/33 reparados, 3 pendientes de re-descarga |
| PSX-STRUCTURE-2 | `E:\Carpetas anbernic\psx`: **0 archivos `.cue`** (formato dominante `.chd`, 214 — correcto) y tenía **93 `.bin` sueltos sin ningún `.cue`**. Clasificados 2026-09-02: **33 confirmados no-PSX por CRC32 real contra el `.dat` de MAME** (no solo por nombre) — 8 `gunbird` (backup íntegro ya en `H:\ROMs\arcade\mame\gunbird.zip`, verificado con `unzip -t`, residuo puro), y 25 más repartidos en `cosmos` (11/13 ROMs, Century Electronics 1981), `sub` (10/17 ROMs, "Submarine" de Sigma 1985), `viper` (solo EEPROM, Leland 1988), `ega` (BIOS de tarjeta gráfica compartida, no un juego) y `hc_u107.bin` (MCU compartida por ~10 juegos "hidden catch" de Universal, sin poder identificar cuál exactamente) — estos 25 sin backup en ninguna biblioteca y ya incompletos desde antes de hoy (faltaban PROMs/ROMs de programa, no es daño de `decompress`). **✅ Los 33 borrados 2026-09-02 con confirmación del usuario** (BD refrescada, 33 huérfanos limpiados, coincide exacto). Quedan **60 sí son juegos/demos PSX reales**, sin tocar. De esos 60, investigados a fondo 2026-09-02 (comprobación de tamaño de sector, no solo nombre): **59 son sectores raw MODE2/2352 válidos (tamaño múltiplo exacto de 2352 bytes)** — estructuralmente sanos, solo les falta el `.cue` sidecar, recuperables generando uno mínimo (1 pista). Solo **`D (Europe) (Disc 1).bin` está realmente roto — 1024 bytes**, no es una imagen de disco, pérdida real de ese archivo. Dos casos destacables por tamaño casi de CD completo y coinciden en nombre con sets ya rotos de `H:\ROMs\psx` (PSX-STRUCTURE-1): **`Wild Arms (USA).bin` (607,6 MB)** y **`Tekken 3 (USA).bin` (603,2 MB)** — candidatos fuertes para reparar esos mismos sets en el PC copiando el `.bin` de Anbernic. `Street Fighter Alpha - Warriors' Dreams (USA).bin` (7,7 MB) también coincide de nombre pero es demasiado pequeño para ser el mismo rip que el del PC (que usa pistas separadas) — revisar a mano antes de asumir que sirve. Wild Arms/Tekken 3 ya usados para reparar `H:\ROMs\psx` (ver PSX-STRUCTURE-1). **✅ `.cue` generados 2026-09-02 (sesión siguiente)**: nuevo comando `rommgr generate-cues <path> [--apply]` (dry-run por defecto, reutiliza `detect_bin_cue_mode`/`synthesize_cue_text` ya existentes en `chd_converter.py`, sin exigir hash RA verificado — a diferencia de `find_bare_bin_files`/`convert-chd`, aquí no hace falta porque un `.cue` sidecar es 100% reversible). Ejecutado en real: **33 `.cue` escritos** (no 59 — de los ~60 restantes, 2 ya tenían `.cue` de sesiones previas — Wild Arms, Tekken 3 — y ~24 más no aparecieron como bare-bin en esta pasada, pendiente de investigar por qué en `PSX-STRUCTURE-2b`). Bug real encontrado y arreglado de paso durante la verificación: `_detect_geometry` (`ra_hash_psx.py`) devolvía `MODE1/2048` por defecto para cualquier fichero sin evidencia real de geometría — reproducido con un chip de ROM arcade (`mpr-15574.bin`, dentro de `_descartados/`) que se detectaba como PSX válido; ahora devuelve un sentinel que hace que `detect_bin_cue_mode` devuelva `None`. También se excluyó `_descartados/` de los candidatos (nunca debe "recuperarse" algo ya descartado). Tests nuevos: `test_detect_bin_cue_mode_rejects_file_with_no_geometry_evidence`, `test_find_bins_needing_cue_*`, `test_generate_missing_cues_*`. 1137/1137 verde, ruff limpio | `E:\Carpetas anbernic\psx\*.bin`, `converters/chd_converter.py`, `retroachievements/ra_hash_psx.py`, `cli.py` | 🟡 en progreso (`feature/psx-structure-2-generate-cues`), 33 `.cue` generados, `D (Europe) (Disc 1).bin` roto sin decidir, ~24 restantes sin explicar (`PSX-STRUCTURE-2b`) |
| PSX-STRUCTURE-2b | ✅ **Investigado 2026-09-02, no es bug**: la cifra "59 sanos" (punto 12 del diario) se calculó **antes** de que los puntos 12-13 del mismo día borraran 26 demos/protos/betas + 1 stub corrupto y repararan Wild Arms/Tekken 3 — dejando ~31 candidatos reales, no 59. `generate-cues` encontró 33, dentro del margen de que la clasificación manual "sano" (múltiplo de 2352) es más laxa que el chequeo real de geometría (`detect_bin_cue_mode`). Verificado en vivo contra `E:\Carpetas anbernic\psx`: **0 `.bin` sueltos sin `.cue` restantes** (35 `.bin` totales, todos con `.cue`). `PSX-STRUCTURE-2` cerrada del todo, sin cambio de código necesario | `E:\Carpetas anbernic\psx\` | ✅ hecho |
| PSX-STRUCTURE-3 | **✅ `E:\Carpetas anbernic` resuelto 2026-09-03** (decisión del usuario: reclasificar). Recuento fresco (la biblioteca creció desde el `605` de hace unos días): **903 archivos mal ubicados por extensión** en 26 carpetas de plataforma (script ad-hoc, `PLATFORM_BY_EXTENSION`/`AMBIGUOUS_EXTENSIONS`/`PLATFORM_BY_FOLDER` de `detection/platform_detector.py`, extensión no ambigua ≠ plataforma real de la carpeta contenedora — `arcade/` excluida, se audita por CRC no por extensión). Se descartó usar `organize-source` a secas: su dry-run reprocesa y renombra **todo** el contenido de cada carpeta, no solo lo mal ubicado (p. ej. `gb/` mostraba 3176 "a organizar" cuando solo 73 eran NES mal puesto) — fuera de alcance de esta tarea, ver `LIBRARY-REPAIR-TOOLING`/`REPAIR-TOOL-8` más abajo. En su lugar, movimiento dirigido (mover sin renombrar, nunca sobreescribir): **362 movidos** a su carpeta de plataforma real ya existente (319 NES, 14 Master System, 10 SNES, 5 Game Boy, 4 PC Engine, 2 Famicom Disk System, 2 Game Boy Advance, 2 Game Gear, 2 GameCube, 1 Game Boy Color, 1 Nintendo 64 — `NES`→`nes/` y `GameCube`→`gamecube/` fijado a mano por tener 2 carpetas candidatas en disco, `NGC/` resultó ser solo scraper-art sin ROMs). **323 duplicados exactos** (mismo nombre, SHA1 idéntico al ya existente en la carpeta correcta) movidos a `<carpeta_origen>/_descartados/` (nunca borrados). `rommgr scan` de refresco tras el movimiento: 101.084 archivos, 0 errores, 561 huérfanos limpiados. **Quedan 42 sin tocar**, documentados para sesión aparte: **33 archivos `.nes`** con nombre igual a uno ya existente en `nes/` pero SHA1 distinto (repacks/(Virtual Console)/dumps regionales alternativos — requieren desambiguación por catálogo, no por extensión a ciegas) y **9 ficheros `.u1`** que `PLATFORM_BY_EXTENSION` mapea a "Nintendo 64DD" por coincidencia — inspección real: son chips arcade sueltos (mismo patrón que `REPAIR-TOOL-5`), no N64DD, no crear carpeta `n64dd/` para ellos. **✅ `H:\ROMs` resuelto 2026-09-04** (lector SD conectado, decisión del usuario confirmada para el caso ambiguo de `3ds/`). Recuento fresco al conectar: **24 mal ubicados** (más que los 8 catalogados el `Día52` — la biblioteca creció, mismo patrón que `E:`). Mismo ajuste manual de carpeta ambigua que en `E:`: `NES`→`nes/` (no `famicom/`, colección japonesa aparte confirmada: 5.184 archivos con assets de scraper) y `GameCube`→`gamecube/` (`ngc/` no existe en esta tarjeta). Con confirmación del usuario, los 4 "(Virtual Console)" de `3ds/` se trataron igual que el resto (movidos por contenido real, no dejados aparte). **19 movidos** a su carpeta real (6 GBC, 3 GameCube `.rvz`, 2 NES bootleg "Crash Bandicoot", 1 FDS, 7 `.nes` sueltos en `atari2600/atarilynx/atarist/c64/gb`). **0 duplicados exactos.** **5 conflictos reales sin tocar** (mismo nombre, SHA1 distinto — 3 de los "(Virtual Console)" de `3ds/` más `c64/Contra` y `c64/Jackal`, mismo patrón que los 33 `.nes` sin resolver de `E:`, requieren desambiguación por catálogo). `rommgr scan` de refresco: 27.076 archivos, 0 errores, 19 huérfanos limpiados (coincide con los 19 movidos) | `E:\Carpetas anbernic` (hecho), `H:\ROMs` (hecho) | ✅ E: hecho, ✅ H: hecho (5 conflictos reales documentados aparte) |
| PSX-STRUCTURE-4 | **Decisión confirmada 2026-09-02**: subcarpeta por juego para `psx/` (y el resto de `_DISC_SUBFOLDER_PLATFORMS` en `operation_planner.py:19-22` — saturn, dreamcast, wii), no carpeta plana. Ya es la convención implementada (`move_disc_set_to_subfolder`, `renamer/file_renamer.py:211`; target derivado en `operation_planner.py:159-168`). Bloqueos originales ya resueltos: PSX-STRUCTURE-1 (30/33, 3 restantes documentados para re-descarga, decisión del usuario de no mezclar), PSX-STRUCTURE-2 (✅ cerrado del todo, ver PSX-STRUCTURE-2b), DECOMPRESS-ARCADE-GAP-1 (✅ hecho), `CATALOG-MATCH-BUG-1`/`GBA-MISPLACED-2` (✅ 2026-09-03), `CATALOG-MATCH-REGION-1` (✅ 2026-09-04, PR #289 mergeada). **Re-medido 2026-09-04 tras el merge**: de los 456 casos PSX ambiguos originales, 167 (37%) ya resuelven región correcta; **quedan 289 (63%) sin resolver** (`CATALOG-MATCH-REGION-2`, diagnóstico hecho, sin arreglar). Migrar `psx/` ahora usaría el título ambiguo/incorrecto de esos 289 como nombre de carpeta destino — mismo riesgo original, alcance menor pero no cero. **Decisión pendiente del usuario**: ejecutar `apply` ya (aceptando que 289 sets quedarán con nombre de carpeta potencialmente erróneo, corregible después) vs. esperar a `CATALOG-MATCH-REGION-2` | `H:\ROMs\psx`, `E:\Carpetas anbernic\psx`, `catalog/matcher.py:270` | 🟡 desbloqueada parcialmente (37% resuelto), decisión de ejecución pendiente del usuario |

---

### LIBRARY-REPAIR-TOOLING — Automatizar lo que hoy se hizo a mano reparando `psx/` (2026-09-02)

Reparando `PSX-STRUCTURE-1` a mano (30 de 31 "sets rotos" resultaron ser recuperables, no
pérdida real) se repitió el mismo puñado de patrones una y otra vez. Documentado a petición
del usuario mientras se hacía la reparación — son candidatos a lógica reutilizable en
`rom_manager`, no implementados todavía. Falta crear el issue `epic` en GitHub para esta
sección (pendiente, ninguna tarea bloquea nada existente).

| ID | Idea | Por qué (evidencia de hoy) |
|----|------|------|
| REPAIR-TOOL-1 | Auto-generar `.cue` de 1 pista cuando un `.bin` está sector-alineado (múltiplo exacto de 2352 o 2048 bytes) y no tiene ningún `.cue` que lo referencie | Hecho a mano 6 veces hoy con el mismo patrón exacto (`Hogs of War`, `MediEvil 2`, `Dino Crisis (Spain)`, `Tomb Raider III (Spain)`, `Parasite Eve II (Spain)` Disc 1/2) — mecánico, cero criterio humano real involucrado |
| REPAIR-TOOL-2 | Detectar "`.cue` huérfano pre-migración": un `.cue` suelto en la raíz de una carpeta de plataforma cuyo nombre base coincide con una subcarpeta-por-juego ya existente casi siempre es residuo de antes de `PSX-STRUCTURE-4`, no un set adicional — ofrecer "descartar automáticamente" en vez de contarlo como "set roto" en auditorías | 17 de los 31 casos de hoy eran exactamente esto — infló el recuento de "sets rotos" sin ser pérdida real |
| REPAIR-TOOL-3 | Cualquier "health check" de sets rotos debería consultar `_descartados/` (local de la carpeta y global de la plataforma) ANTES de marcar algo como pérdida — buscar copia jugable de otra región/edición ya descartada por `resolve-duplicates` | 11 de los 31 casos de hoy tenían un `.chd` perfectamente sano esperando en `_descartados/`, a un `shutil.move` de distancia, y el diario de ayer los había dado por "posible pérdida real" sin comprobarlo |
| REPAIR-TOOL-4 | Root cause real detrás de REPAIR-TOOL-3: el "ganador" en dedup por título (`get_title_duplicate_groups`, `database/repositories/duplicates.py:55-96`, y la lógica que aplica ese resultado) no comprueba integridad del fichero — puede quedarse con un `.cue`+`.bin` roto de una edición y descartar un `.chd` sano de otra solo por criterio región/RA. Añadir un chequeo de integridad (¿el `.cue` referencia ficheros que existen? ¿`chdman verify` pasa?) al criterio de selección evitaría que esto vuelva a pasar | Explica por qué aparecieron 11 casos del mismo patrón en una sola sesión de `resolve-duplicates`, no fueron incidentes aislados |
| REPAIR-TOOL-5 | Cruzar `.bin` sueltos contra el índice CRC de arcade real (`_is_console_only_dat`, ya filtrado) como parte rutinaria de `scan` o de un comando `rommgr doctor`, no solo de auditorías puntuales a mano | Se necesitaron dos pasadas manuales distintas (`Día52` sección 9, y esta sesión secciones 14-15) para encontrar chips arcade sueltos en `psx/` — con el CRC ya indexado, esto podría salir solo |
| REPAIR-TOOL-6 | Incluir el sector-alignment (múltiplo de 2352/2048) como campo calculado en cualquier reporte de "`.bin` sueltos sin `.cue`", no solo como paso manual de investigación | Se calculó a mano para clasificar sanos/rotos tanto en `PSX-STRUCTURE-2` (Día52) como en los 4 casos reparados hoy — es una comprobación de una línea, no debería depender de que alguien la piense cada vez |
| REPAIR-TOOL-7 | Documentar claramente (código + `docs/`) que `library_pc.db` es la única BD real que usa `scan` para las dos unidades (`E:\` y `H:\`, pese al nombre) — `library_android.db` es una BD distinta, separada, que llevaba desde 2026-07-13 sin actualizarse. El nombre engaña y ya llevó a comparar contra datos de 2 meses de antigüedad sin darse cuenta (sección 6 del documento de revisión manual, corregido después) | `src/rom_manager/config.py:378-379`, `cli.py:391-393` | 🔴 pendiente, riesgo de confusión repetida |
| REPAIR-TOOL-8 | Nuevo comando "solo reubicar mal ubicados" (extensión no ambigua ≠ plataforma de carpeta, mover sin renombrar, verificar SHA1 en colisión → mover a `_descartados/` si es duplicado exacto, dejar en su sitio si el contenido difiere) — hecho a mano con script de sesión en `PSX-STRUCTURE-3` porque `organize-source` no cubre este caso: reprocesa/renombra **todo** el contenido de la carpeta (correcto incluido), no solo lo mal ubicado. Reutilizable para la próxima vez que `H:\ROMs` esté montado (mismos 8 casos ya catalogados) y para cualquier carpeta nueva que se contamine | `web/zip_router.py` o nuevo módulo, patrón en script de sesión (no versionado) | 🔴 pendiente, candidato a CLI propio |

---

### CATALOG-MATCH-BUG-1 — Falso positivo de matching entre plataformas distintas (hallazgo 2026-09-02)

Encontrado mientras se investigaba si se podían borrar de forma segura ROMs sin soporte RA que
tuvieran alternativa ya en la biblioteca (ver más abajo, "borrado de duplicados por RA — no
seguro"): `E:\Carpetas anbernic\megadrive\deer hunter.bin` tiene `canonical_title`/`platform` en
la BD emparejados con **"Deer Hunter (USA)" de Game Boy Color** — un juego completamente distinto.
Verificado con la cabecera real del fichero (`file` detecta "Sega Mega Drive / Genesis ROM image",
firma `@TomXie 2002.Nov`): es una ROM de Mega Drive genuina, sin relación real con el juego de GBC,
coincidencia pura de tamaño (1.048.576 bytes, tamaño muy común) y de parte del nombre.

**Causa raíz localizada (2026-09-02)**: `CatalogMatcher._match_by_title()`
(`catalog/matcher.py:258-263`) solo restringe los candidatos del índice de título a la plataforma
real del fichero cuando `PLATFORM_BY_EXTENSION.get(extensión)` devuelve algo — pero `.bin`, `.zip`,
`.chd`, `.md`, `.cue`, `.iso`, `.img`, `.7z`, `.rom`... están todos en `[ambiguous].extensions` de
`platforms.toml` (necesitan la carpeta para desambiguar), así que para ellos `ext_platform` es
siempre `None`, el filtro por plataforma (MATCH-FIX-2) nunca se aplica, y `candidates = hits` se
queda con **todos** los títulos coincidentes de cualquier plataforma — gana el primero por orden
alfabético de carga de `.dat` (`_load_dir`, `catalog/matcher.py:144`), no el que de verdad coincide
con la carpeta/extensión real. Con `.bin`, "Nintendo - Game Boy Color..." ordena antes que
"Sega - Mega Drive - Genesis...", de ahí el caso concreto. `match()` no recibe la ruta/carpeta del
fichero, solo el nombre — así que esta función no tiene forma de desambiguar una extensión ambigua
aunque quisiera.

**Alcance real, auditado contra `library_pc.db` (biblioteca `E:\Carpetas anbernic`)**: de las 53.444
filas con extensión ambigua y `platform` asignada, **1.142 son `confidence=low` (`ambiguous=True`)**
— el único nivel donde esto puede pasar (medio/alto solo tienen 1 candidato o SHA1 exacto, no hay
elección arbitraria que hacer). De esas, **428 están fuera de `arcade/`** — plataforma real de
carpeta vs. `platform` en BD no coincide, confirmado no-arcade: **234 `.bin`, 97 `.zip`, 57 `.chd`,
29 `.md`, 6 `.cue`, 3 `.iso`** (`.rommgr/library_pc.db`, query ad-hoc, no incluida en el repo). Las
otras 807 filas de baja confianza caen dentro de `arcade/` — mezcla de matcher confundido y ficheros
mal ubicados por otras vías, no auditado con el mismo detalle. No se ha tocado `library_android.db`
(`H:\ROMs`) en detalle: el mismo query solo encontró 0 mismatches ahí (biblioteca más pequeña/limpia,
menos exposición).

**Nota de riesgo real**: estos matches de baja confianza ya llevaban `ambiguous=True`, pero
`RA-DEDUP-UNSAFE-1` (más abajo) demuestra que sí llegan a lógica de negocio downstream (revisión de
duplicados) sin que ese flag los frene — el `canonical_title`/`platform` erróneo puede acabar
proponiendo un borrado real.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CATALOG-MATCH-BUG-1 | **✅ Parte cross-plataforma arreglada 2026-09-03** — ver `GBA-MISPLACED-2` arriba, mismo fix (`catalog/matcher.py`, rama `fix/catalog-match-ambiguous-extension`), incluye el caso original (`deer hunter.bin` GBC↔Mega Drive) verificado corregido en `library_pc.db` real. **La "evidencia nueva" del `Día53` (Tekken USA→Europe, etc.) resultó ser un bug DISTINTO, no cubierto por este fix** — re-verificado tras aplicarlo y re-matchear: 112/241 en la sección `PlayStation` de `rommgr plan` siguen siendo puro cambio de región. Causa raíz real: `detect_platform(source_path)` da la PLATAFORMA (psx/saturn/...), no la REGIÓN — no puede desambiguar entre "Tekken (USA)" y "Tekken (Europe)", ambos ya PlayStation. Ver `CATALOG-MATCH-REGION-1` (nueva sección) para el seguimiento | `catalog/matcher.py:196-283` | ✅ cross-plataforma arreglado; 🔴 ver `CATALOG-MATCH-REGION-1` para la región |

---

### CATALOG-MATCH-REGION-1 — El fallback por título no puede elegir la región correcta cuando el SHA1 no calza (hallazgo 2026-09-03, separado de `CATALOG-MATCH-BUG-1`)

Descubierto re-verificando el fix de `CATALOG-MATCH-BUG-1`/`GBA-MISPLACED-2` con `rommgr plan` real
contra `E:\Carpetas anbernic` (backup previo en `.rommgr/backup_catalog_match_fix_2026-09-03/`,
re-match de las 36.973 filas sin resolver/baja confianza con el matcher ya arreglado). El fix de
plataforma-por-carpeta **no toca este caso**: `normalize_for_match()` borra el tag de región junto
con el resto de anotaciones, así que "Tekken (USA)" y "Tekken (Europe)" colapsan a la misma clave de
título — ambos hits ya son PlayStation, `detect_platform(source_path)` no tiene nada que desempatar
(da la plataforma, no la región) y `_match_by_title()` sigue cayendo a `candidates[0]` (orden de carga
del `.dat`). **Causa raíz de fondo**: los formatos de disco reales de la biblioteca (`.chd` sobre todo,
también `.pbp`/multi-track `.bin`) nunca hacen match SHA1 exacto contra el DAT — el DAT hashea la
pista cruda sin comprimir, `.chd` es una compresión con cabecera propia, así que el SHA1 del fichero
en disco jamás coincide con ninguna entrada, y el título es la ÚNICA señal disponible. Verificado en
vivo: 112 de 241 renombrados propuestos en la sección `PlayStation` de `rommgr plan` (tras el fix y
re-match) cambian solo la región/tag, mismo patrón que antes del fix (`Alundra 2 (USA)→(Europe)`,
`Crash Bandicoot (USA)→(Europe)`, `Castlevania - Symphony of the Night (USA)→(France)`...).

**Bloqueaba `PSX-STRUCTURE-4`** (migración a subcarpeta-por-juego) — la migración habría usado estos
títulos con región incorrecta como nombre de carpeta destino.

**Resuelto (2026-09-03)** por el primero de los 3 caminos propuestos (hash RA de disco), pero
implementado vía el serial de arranque en vez de un hash MD5: `fetch_hash_library` (RA API) solo
guarda **un** hash por juego, sin variante por región (comprobado contra `ra_hashes_12.json` real —
"Tekken 3" tiene una sola entrada, un solo hash), así que comparar contra la librería de RA no
habría desambiguado nada. El Redump PS1 DAT (`Sony - PlayStation.dat`, formato clrmamepro) sí trae
el serial real por región como atributo del `game (...)` (`serial "SLUS-00402"`, presente en 13.323
de 13.592 entradas) — mismo dato que `SYSTEM.CNF` en el disco real (`BOOT = cdrom:\SLUS_004.02;1`,
o `cdrom:\TEKKEN3\SLUS_004.02` con subcarpeta). Comparando ambos normalizados (mayúsculas, sin
puntuación) se desambigua sin adivinar.

Cambios:
- `catalog_loader.py:CatalogEntry` — nuevo campo `serial` (solo poblado por `load_clrmamepro_dat`,
  las entradas XML/No-Intro no lo traen).
- `retroachievements/ra_hash_psx.py` — nueva `detect_psx_boot_serial()` (reutiliza `_CdImage`,
  `_find_boot_executable`, `_first_cue_bin`; `.chd` refactorizado a `_extract_chd_to_cue()`
  compartido con `_hash_chd_file()`).
- `catalog/matcher.py:_match_by_title()` — cuando la plataforma resuelta es PlayStation y quedan
  >1 candidatos tras el filtro por carpeta/extensión, lee el serial real del disco y filtra por
  `entry.serial` normalizado antes de caer a `candidates[0]`; si desambigua a 1, confianza `medium`
  (contenido real, no adivinado).
- `CatalogMatcher.__init__` gana `chdman_path` (opcional, `None` desactiva la desambiguación sin
  romper nada); cableado en `cli.py` (`match`), `web/handlers/scan.py` (`_do_match`) y
  `web/inbox_pipeline.py` (los dos flujos de Inbox/organize) vía `config.chdman`.

Verificado en vivo contra `E:\Carpetas anbernic\psx\Tekken 3 (USA).cue` (el caso exacto citado
arriba): antes del fix caía a `Tekken 3 (Europe) (Alt)` con confianza `low`/`ambiguous=True`; con
el fix resuelve `Tekken 3 (USA)`, confianza `medium`, `ambiguous=False`. Gap conocido: el lector de
disco (`_find_boot_executable`) no consigue leer todos los `.bin`/`.cue` reales — p. ej.
`Tekken 3 (Japan) (Rev 1).cue` devuelve `None` ya en `compute_psx_ra_hash` (comportamiento
preexistente, no introducido por este fix) — esos casos siguen cayendo al `candidates[0]` de
siempre, no hay regresión pero tampoco mejora ahí. Tests: `test_psx_region_disambiguated_by_real_boot_serial`
(`test_catalog_matcher.py`), `test_detect_psx_boot_serial` + `test_detect_psx_boot_serial_unsupported_format`
(`test_ra_hash_psx.py`). 1145/1145 tests en verde, `ruff` limpio.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CATALOG-MATCH-REGION-1 | Desambiguar región cuando el SHA1 de archivo no calza y varios candidatos del mismo título/plataforma difieren solo en región — bloqueaba `PSX-STRUCTURE-4`. Alcance medido originalmente: 112/241 (46%) de los renombrados propuestos en la sección `PlayStation` de `rommgr plan` sobre `E:\Carpetas anbernic`. **Re-medido 2026-09-04 tras mergear el fix (PR #289)**: `rommgr match` no re-encola filas `match_confidence='low'` (solo `NULL`, ver `MATCH-FIX-2`), así que se necesitó un re-match dirigido (script de sesión, backup previo en `.rommgr/backup_region_remeasure_2026-09-04/`) sobre las 456 filas PSX en `low`: **167/456 (37%) pasan a `medium` con la región correcta** (verificado en vivo: `Tekken 3 (USA).cue` — el caso original — pasa de `canonical_title=Tekken 3 (Europe) (Alt)` a `Tekken 3 (USA)`; mismo patrón confirmado en `Alundra 2` y `Crash Bandicoot`). **Quedan 289/456 sin resolver**, diagnosticado: **140 sin serial legible** (mismo gap conocido del lector de disco, ya documentado — `.bin/.cue` que `compute_psx_ra_hash` tampoco lee) y **149 con serial leído pero que no calza contra ningún `CatalogEntry.serial` de los candidatos** (hallazgo nuevo, sin investigar — ¿formato de serial distinto, disco no cubierto por el Redump DAT?). Ver `CATALOG-MATCH-REGION-2` para el seguimiento | `catalog/matcher.py:_match_by_title`, `retroachievements/ra_hash_psx.py:detect_psx_boot_serial`, `catalog_loader.py:CatalogEntry.serial` | ✅ arreglado y verificado en vivo; 63% de los casos originales siguen sin desambiguar (ver `CATALOG-MATCH-REGION-2`) |
| CATALOG-MATCH-REGION-2 | **Resuelto (2026-09-04)**: de los 289 casos PSX que `CATALOG-MATCH-REGION-1` no pudo resolver, 149 tenían serial leído del disco que no calzaba contra ningún `CatalogEntry.serial` candidato porque el serial del Redump DAT trae sufijos que el disco real no tiene (`SLES-02997-0`/`SLES-12997-1` por disco de una copia múltiple, `SLUS-00067GHA`/`SCUS-94244CE` por variante "Greatest Hits"/"Collector's Edition", `SLES-01480-P-0` por país de impresión) — la comparación en `_match_by_title` exigía igualdad exacta. Cambiado `_normalize_serial(h[0].serial) == real_norm` por `.startswith(real_norm)`; el check `len(serial_hits) == 1` ya existente sigue protegiendo contra colisiones (no se ha visto ningún caso con dos candidatos compartiendo prefijo). Test nuevo `test_psx_region_disambiguated_by_serial_prefix`. 1146/1146 tests en verde, `ruff` limpio. Gap conocido sin tocar: `Front Mission 2 (Japan)` (`SLPM87331` real vs `SLPS-01000`/`SLPM-87397` candidatos — ningún prefijo calza, hueco real de cobertura del DAT) y los 140/289 sin serial legible en absoluto (gap del lector de disco, ya documentado). Pendiente: re-medir en vivo contra `E:\Carpetas anbernic` para confirmar cuántos de los 149 quedan resueltos | `catalog/matcher.py:328-338` (`_match_by_title`), `retroachievements/ra_hash_psx.py:detect_psx_boot_serial`, `tests/test_catalog_matcher.py` | ✅ arreglado, pendiente de commit/PR y re-medición en vivo |

---

### RA-DEDUP-UNSAFE-1 — Borrar duplicados "sin soporte RA pero con alternativa" no se puede automatizar (hallazgo 2026-09-02)

A petición del usuario, se intentó borrar automáticamente los ROMs sin soporte RA cuando la versión
con logros ya está en la misma biblioteca (no solo "existe según RA"). Con el criterio más
conservador posible (misma unidad + mismo tamaño de fichero + sin palabra clave de hack/traducción
en el nombre) **igual aparecieron falsos positivos reales**: `deer hunter.bin` (ver
`CATALOG-MATCH-BUG-1` arriba), `show do milhao volume 2 (bra) (alt).bin` (etiqueta `(alt)` de
No-Intro = dump alternativo preservado a propósito, no basura), y varios más con mismo tamaño pero
MD5 distinto sin garantía real de ser el mismo contenido. Un primer intento sin restringir a "misma
unidad" habría borrado 7 ROMs de N64 de `H:\ROMs` (`Super Mario 64`, `Donkey Kong 64`...) usando
como excusa que `E:\` tenía la misma ROM en formato `.z64` (mismo juego, solo orden de bytes
distinto) — la Anbernic se habría quedado sin esos juegos jugables localmente. Todo restaurado
antes de que el usuario lo confirmara, nada se perdió.

**Conclusión: no implementar borrado automático de este tipo.** Después de `resolve-duplicates`,
cualquier pareja que comparta título canónico pero no SHA1 es, por definición, contenido distinto
de verdad (aunque a veces trivial) — distinguir "diferencia trivial" de "traducción que hay que
conservar" requiere abrir el fichero, no hay atajo fiable. El listado completo (204 candidatos)
queda en `.rommgr/ra_no_support_alternative.csv` (fuera del repo) para revisión manual del usuario.

| ID | Task | Notas |
|----|------|-------|
| RA-DEDUP-UNSAFE-1 | No implementar auto-borrado de "duplicado sin RA con alternativa en biblioteca" — documentado que no es seguro ni con el criterio más conservador probado. Si se quiere una herramienta de ayuda, debería presentar los pares candidatos para confirmación manual uno a uno (con tamaño, MD5 y ambos nombres visibles), nunca borrar sin esa confirmación | ⚪ decisión tomada, no implementar automatización |

---

### ARCADE-SETUP — Research arcade ROM config (no code)

| ID | Task | Notes |
|----|------|-------|
| ARCADE-SETUP-1 | Research MAME vs FBNeo ROM set version compatible with Anbernic RG556 RetroArch | ✅ `docs/arcade-setup.md` §1 — FBNeo primera opción, MAME 2003 Plus segunda |
| ARCADE-SETUP-2 | Identify target arcade systems and map each to the correct RetroArch core | ✅ `docs/arcade-setup.md` §2 — tabla sistema→core→ROM set |
| ARCADE-SETUP-3 | Document config additions: `config.toml`, library-structure, DAT sources for arcade | `docs/arcade-setup.md` ✅ + descarga de DATs arcade cableada (runtime: `_run_dat_download` en `web/handlers/scan.py` + `scan.js`; installer: `catalog/dat_downloader.py` vía `installer/download_dats.py`) |
| ARCADE-SETUP-4 | Test a sample ROM end-to-end: scan → rename → launch on device | Hardware test |

---

### PSX-ORPHAN — Carpetas huérfanas de scraping en `psx/` (hallazgo 2026-08-26)

Origen: el usuario, con la Anbernic conectada, pidió revisar por qué había
juegos PSX en subcarpetas y sospechó duplicados sueltos en la raíz que
pudieran borrarse. Auditoría real de contenido (no solo nombres) sobre
`E:\Carpetas anbernic\psx`:

- **125 subcarpetas de nivel superior, 0 contienen un ROM real**
  (`.bin/.cue/.chd/.pbp/.gdi/.iso`). Los ~450 ROMs reales de PSX están
  sueltos directamente en `psx/`. `move_disc_set_to_subfolder`
  (`renamer/file_renamer.py:211`) existe y funciona, pero no hay evidencia
  de que produjera estas carpetas.
- **De los 50 casos donde un archivo suelto en la raíz coincide de nombre
  con una subcarpeta, en NINGUNO la subcarpeta tiene el ROM** — el archivo
  suelto es la única copia real. **No borrar nada de la raíz basándose en
  el nombre de una carpeta homónima.**
- Desglose de las 125 carpetas: **98 totalmente vacías**; **17 con
  `_descartados/` conteniendo una versión alternativa de región/revisión ya
  descartada** (4.333,8 MB — p.ej. `Koudelka (Spain) (Disc 2)/_descartados/
  Koudelka (USA) (Disc 1).chd`), respeta el convenio del proyecto (AUD-3,
  `_descartados/` nunca se borra solo); el resto (~2.022 archivos, 445,7 MB)
  es `media/` (carátulas) y `.m3u` huérfanos.
- Hipótesis del origen (no confirmada): un pase de dedup por juego (ver
  `ra_duplicates_service.py`) creó una carpeta por juego, descartó la
  versión perdedora en `_descartados/` y dejó `media/`+`.m3u`, pero la
  versión ganadora se devolvió después a la raíz sin limpiar la carpeta.
- Verificado con `verify_multidisc()` (`utils/multidisc_verifier.py`, ya
  existente): 66 grupos sin `.m3u` (22 juegos únicos, probablemente por el
  mismo aplanado) + 4 "gap" + 1 "mixed_ext".
  - `Metal Gear Solid (USA)`: **falso positivo** — el disco 2 sí existe
    (`Metal Gear Solid (USA) (Disc 2) (Rev 1).bin`), pero `_DISC_RE`
    (`utils/m3u_generator.py:10`) exige que `(Disc N)` sea el sufijo final
    del nombre, así que no lo reconoce con `(Rev 1)` detrás. El
    `mixed_ext` (`.bin`+`.srm`) es el mismo problema: el save
    `... (Disc 1).srm` cae en el mismo bucket porque `find_disc_groups`
    no filtra por extensión de imagen antes de agrupar.
  - `Fear Effect (USA)`: **gap real** — discos 1/3/4 existen como `.bin`
    suelto (con su `.cue` correspondiente en `_descartados/`, íntegro y
    apuntando al `.bin` correcto — parece mal ubicado, no corrupto), disco
    2 no aparece en ningún sitio de la biblioteca (búsqueda recursiva
    completa).

| ID | Task | Notas |
|----|------|-------|
| PSX-ORPHAN-1 | Borrar las 98 subcarpetas totalmente vacías de `psx/` (0 archivos) | — | ✅ borrado 2026-08-26, ver `.rommgr/psx_orphan_cleanup_2026-08-26.log` |
| PSX-ORPHAN-2 | Limpiar `media/`+`.m3u` huérfanos del resto de subcarpetas (445,7 MB) | `psx/*/media`, `psx/*/*.m3u` | ✅ borrado 2026-08-26 junto con PSX-ORPHAN-1 (mismo script, mismo log) |
| PSX-ORPHAN-2b | **Excepción a AUD-3, decisión explícita del usuario 2026-08-26**: los 4,3 GB en `_descartados/` de las 17 subcarpetas (versiones de región/revisión ya descartadas por el dedup) también se borraron, pese a la advertencia de que es irreversible y de que no libera espacio en la Anbernic (psx nunca llegó a sincronizarse — ver `CABLE-ROM-FIX-3`). El `_descartados/` de nivel superior (`psx/_descartados/`, 180 items) **no se tocó**, sigue con la política normal | `.rommgr/psx_orphan_cleanup_2026-08-26.log` (manifiesto completo: rutas + tamaños de cada archivo borrado) | ✅ borrado, sin backup adicional más allá del manifiesto |
| DEVICE-DUP-1 | **Hallazgo 2026-08-27 en la propia Anbernic** (no en el PC): la raíz de la SD (`/storage/521D-04EA/`) tenía carpetas de plataforma en dos esquemas a la vez — nombres humanos sueltos (`NGC`, `Game Boy Advance`, `Nintendo DS`, etc.) y `ROMs/<código>` (`gamecube`, `gba`, `nds`...) que es lo que usa nuestro Cable Sync. `NGC/` y `ROMs/gamecube/` eran **duplicado exacto** (25 GB, 21/22 juegos idénticos) — sin relación con nada tocado en el PC. Verificado que no hay ninguna partida de GameCube en la consola (ni en `NGC/`/`ROMs/gamecube/`, ni en `saves/`, ni en los datos privados de `org.dolphinemu.dolphinemu`/`org.dolphinemu.mmjr` en SD e interno — `GC/`/`StateSaves/` vacíos, no se ha jugado nada aún). Usuario confirmó `ROMs/` como la carpeta real; `NGC/` borrado por `adb shell rm -rf` — **25 GB liberados, la SD pasó de 53 GB a 78 GB libres** | `/storage/521D-04EA/NGC` (borrado) | ✅ hecho 2026-08-27 |
| DEVICE-DUP-2 | **Auditado 2026-08-27, NO eran duplicados — tenían contenido único.** Comparado nombre a nombre contra `ROMs/<código>`: `Atari 2600` y `Game Boy` sí eran subconjunto completo (0 archivos únicos, redundantes de verdad, **sin tocar todavía**). El resto tenía 42 juegos que no existían en `ROMs/` (Nintendo DS: Mario Kart DS, New Super Mario Bros., Pokémon SoulSilver, Pokémon Mystery Dungeon, Super Mario 64 DS, Tetris DS; Master System: 24 juegos incl. Golden Axe/Shinobi/Sonic; Game Gear: 8 con traducciones fan; Game Boy Color: 2; Game Boy Advance: Mother 3 fan-trans; Famicom Disk System: 1) — **traídos al PC por `adb pull` a `inbox/` y procesados por el pipeline real (`/api/inbox-run`)**: 42 escaneados, 39 renombrados a nombre canónico, 0 errores, verificado en disco en `ROMs/nds` y `ROMs/mastersystem`. Las 6 carpetas sueltas de origen en la SD **siguen sin borrar** (quedan como backup hasta confirmar que todo llegó bien) | `E:\Carpetas anbernic\inbox` → `ROMs/nds`, `ROMs/mastersystem`, etc. | ✅ organizado 2026-08-27; pendiente solo borrar las 6 carpetas de origen en la SD una vez confirmado, y decidir si limpiar `Atari 2600`/`Game Boy` (100% redundantes) |
| IISU-MEDIA-1 | Investigado cómo evitar carátulas duplicadas entre launchers (Daijisho/iiSU/ES-DE). Daijisho guarda su caché en `/data/data/com.magneticchen.daijishou/` (privado, sin root no se puede leer ni exportar — confirmado con `run-as` fallando por app no depurable). iiSU sí soporta "link ES-DE metadata" en ROM Import (no duplica media), pero requiere instalar ES-DE (app de pago vía Patreon, sin root, no destructivo) y volver a scrapear una vez en ese formato estándar. Se evaluó rootear la consola (GammaOS Next) para acceder a las DBs privadas — **descartado**: implica desbloquear bootloader, que resetea de fábrica el almacenamiento interno (destruiría justo los datos de Daijisho/iiSU que se querían leer) | — | 🔵 en pausa, decisión del usuario: no rootear; ES-DE pendiente de que el usuario decida instalarlo |
| IISU-CONFIG-1 | El usuario ya abrió iiSU y apuntó la carpeta de ROMs a `ROMs/` en la SD — confirmado que escanea recursivamente (incluye nuestro propio `_descartados/`) y empieza a scrapear su propia media en `Android/media/com.iisulauncher/iiSULauncher/assets/media/roms/consoles/<shortName>/<rom>/` (formato público, sin root, editable por adb). Solo tenía 2 plataformas configuradas en `Emuladores/emulator_options.json` (`gb`→RetroArch, `nds`→melonDS). Se añadieron las 17 restantes de nuestra lista (`_SYSTEMS` de `esde/systems_generator.py`), cruzando el catálogo maestro `emuladores.json` con los emuladores standalone realmente instalados (`pm list packages`): `psx`→DuckStation, `gc`/`wii`→Dolphin, `ps2`→AetherSX2, `psp`→PPSSPP, `n64`→M64Plus FZ, `n3ds`→Citra MMJ (paquete instalado es `org.citra.emu`, que en el catálogo de iiSU corresponde al id `CITRA-MMJ`, no al `CITRA` genérico), `dreamcast`→Flycast; `gba/gbc/snes/megadrive/mastersystem/gamegear/mame/fbneo/neogeo` sin standalone instalado → RetroArch (core por defecto, `mame`→MAME 2003-Plus siguiendo la preferencia ya documentada en `docs/arcade-setup.md`). **Añadido 2026-08-27**: faltaba el shortName `arcade` (distinto de `mame`/`fbneo`/`neogeo` — es el que corresponde a nuestra carpeta real `ROMs/arcade`, mientras se sincronizaba por primera vez a la consola) → RetroArch/"FinalBurn Neo core", misma preferencia FBNeo-primero de `docs/arcade-setup.md`, backup en `emulator_options.json.bak-2026-08-27b`. **Completado 2026-08-27**: las 18 plataformas restantes de `ROMs/` también añadidas (`amiga`→PUAE, `atari2600`→Stella, `atari5200`→a5200, `atari7800`→ProSystem, `atari800`→Atari800, `atarijaguar`→Virtual Jaguar, `atarilynx`→Handy, `atarist`→Hatari, `c64`→VICE x64sc Accurate, `colecovision`→blueMSX, `cps1/2/3`→FinalBurn Neo, `easyrpg`→EasyRPG, `famicom`/`fds`/`nes`→FCEUmm siguiendo la preferencia ya establecida en `_SYSTEMS` de `esde/systems_generator.py`, `intellivision`→FreeIntv), todas vía RetroArch (ningún standalone instalado para estas). **`astrocde` (Bally Astrocade) se dejó sin configurar a propósito**: el catálogo de iiSU no ofrece ningún core de RetroArch para esa plataforma, solo MAME4droid standalone, que no está instalado — no hay emulador viable en este dispositivo todavía. Backup en `emulator_options.json.bak-2026-08-27c`. **Completado 2026-08-27**: usuario instaló MAME4droid Current (`com.seleuco.mame4d2024`) vía Play Store (ojo: primero instaló por error el clásico `com.seleuco.mame4droid`, no válido para `astrocde` en el catálogo — instaló también el Current a continuación) → `astrocde`→MAME4droid Current añadido, backup en `emulator_options.json.bak-2026-08-27d`. **Total: 39 de 39 carpetas de `ROMs/` configuradas**. **Confirmado 2026-08-27, no es un problema**: iiSU usa `shortName` `gc`/`n3ds` internamente pero traduce el nombre de carpeta real sin exigir coincidencia exacta — verificado en vivo: `ROMs/3ds` (nuestra convención, sin tocar) ya aparece scrapeado bajo su ID interno `n3ds`. No hace falta renombrar `gamecube`→`gc` ni `3ds`→`n3ds` en el PC/SD/ajustes de Retro Vault | `.../Emuladores/emulator_options.json` (backup en `emulator_options.json.bak-2026-08-27` en el propio dispositivo) | ✅ hecho 2026-08-27, con backup en el dispositivo |
| PSX-ORPHAN-3 | Arreglar `_DISC_RE` (`utils/m3u_generator.py:10`) para reconocer `(Disc N)` aunque le siga otro tag (`(Rev 1)`, `(v1.1)`), y excluir extensiones no-imagen (`.srm` y otras saves) del agrupado en `find_disc_groups` — evita falsos positivos como `Metal Gear Solid (USA)` | `utils/m3u_generator.py::find_disc_groups`, `_DISC_RE` | ✅ hecho 2026-08-27 — regex con 3er grupo captura el tag final (`_parse_disc()`), rechaza `(Track N)` explícitamente (evita resucitar el falso positivo de tracks multi-bin que el ancla `$` original prevenía), y `_DISC_SET_EXTS` (imágenes + sidecars: `.bin/.img/.iso/.chd/.gdi/.pbp/.ecm/.cue/.ccd/.sub/.mds/.mdf/.sbi`) filtra cualquier extensión no-disco antes de agrupar. 5 tests nuevos en `test_m3u_generator.py` (incluye el caso real MGS + `.srm`), suite completa 1033/1033 verde. `multidisc_verifier.py` (que reimporta `_DISC_RE`) sigue funcionando sin cambios — sus 33 tests también en verde |
| PSX-ORPHAN-4 | `Fear Effect (USA)` disco 2 — confirmar si nunca se tuvo o se perdió; mientras tanto, sacar los 3 `.cue` de `_descartados/` de vuelta a `psx/` (referencian bins que sí existen, no hay conflicto de nombre) | `psx/_descartados/Fear Effect (USA) (Disc {1,3,4}).cue` | 🔴 pendiente, confirmación del usuario |
| PSX-ORPHAN-5 | **Decisión pendiente (feedback usuario 2026-08-29)**: consenso sobre sets PSX con muchos archivos/tracks — evitarlos o no — y si cada juego debería vivir en su propia subcarpeta o con los archivos sueltos en `psx/`. Relacionado con `move_disc_set_to_subfolder` (`renamer/file_renamer.py:211`, patrón ya documentado en `.claude/CLAUDE.md`) y con el propio hallazgo de PSX-ORPHAN (125 subcarpetas huérfanas de un aplanado previo) | `docs/ideas/Idea_final.md` | 🔴 pendiente, decisión del usuario |

---

### DEDUP-RENAME — Colisiones de nombre en Organizar: sufijo _1/_2 en vez de borrar (feedback usuario 2026-08-29)

Origen: `docs/ideas/Idea_final.md` + `docs/Feedback/29/8.md` — el usuario reporta que,
cuando dos juegos piden el mismo nombre canónico, Organizar les añade sufijo `_1`/`_2`
en vez de quedarse con uno solo. Pide el mismo criterio que ya usa el resto de la app
para duplicados: conservar la versión con logros en RetroAchievements y descartar
la otra (patrón ya implementado en `ra_duplicates_service.py`/`apply_ra_conflicts`,
ver TABS-FIX-2/DUP-RA-COLLISION-1 en `archivo.md`). No investigado a fondo todavía —
puede ser que el flujo de colisión simple (mismo `canonical_title`, sin ser sets
multi-disco) nunca llegue a pasar por `apply_ra_conflicts`, a diferencia de los
casos `disk`/`collision` que sí lo hacen.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DEDUP-RENAME-1 | Investigar por qué una colisión de nombre simple (no multi-disco) en Organizar termina en sufijo `_1`/`_2` en vez de resolverse por RA — confirmar con archivo:línea si pasa por `collision_resolver`/`apply_ra_conflicts` o por una ruta distinta sin ese criterio. No arreglar en la misma sesión, documentar hallazgo | `planner/collision_resolver.py`, `services/ra_duplicates_service.py` | ✅ **investigado 2026-08-29 — no es un bug, el sufijo es una acción manual explícita, no automática**. `collision_resolver.resolve()` (`planner/collision_resolver.py:44-46`) por defecto (`keep_both=False`) marca las colisiones `status='conflict'` — **no** las renombra ni les pone sufijo; `_do_apply` (`web/handlers/organize.py:111,123`) llama a `build_plan(..., keep_both=keep_both)` con `keep_both` sacado del body de la request, `False` por defecto. El sufijo `_1`/`_2` solo se aplica si el usuario pulsa el botón explícito **"Renombrar (añadir sufijo _1 _2)"** (`organize.js:164` → `applyKeepBoth()`, `organize.js:285-303`, que confirma con un modal propio y manda `keep_both:true`) — un escape hatch a propósito para "quiero quedarme con ambas copias", no el camino por defecto. El camino RA ya existe en el mismo panel de colisiones, sin tener que ir a otro sitio: si hay datos de RA para el título (`hasRaData`, `organize.js:157`), la tabla ya muestra "✓ Ganador RA" / "→ _descartados/" por fila (`organize.js:167-190`) y el texto de ayuda dirige a "2. Revisar copias" (`organize.js:165`) para aplicarlo. Conclusión: si el usuario ve sufijo `_1`/`_2` es porque (a) pulsó ese botón a propósito, o (b) no había caché de RA para esa plataforma/hash (`hasRaData=false`) y por tanto no hay señal con la que decidir un ganador — comportamiento correcto, no un fallo de `apply_ra_conflicts`. Nada que arreglar en el mecanismo; si el usuario confirma que fue (b), el hueco real sería de cobertura de caché RA (relacionado con SAGE-1), no de esta lógica |
| DEDUP-RENAME-2 | **El usuario no encuentra cómo aplicar la función de duplicados a la Anbernic** (feedback 2026-08-29, aclarado tras TABS-FIX-6 archivar la pestaña Duplicados en favor de "Revisar copias" dentro de Organizar). `DEVSEL-FIX-1` (`archivo.md`) dice que las acciones de duplicados ya enrutan por dispositivo — investigar si "Revisar copias" realmente expone/filtra por Anbernic en la UI actual o si el selector de dispositivo lo oculta; confirmar con archivo:línea antes de arreglar | `web/builders/duplicates.py` (`_build_review_queue`), `web/static/js/tabs/review_copies.js` | 🔴 pendiente investigación |
| DEDUP-RENAME-3 | **Caso real encontrado 2026-08-29 buscando "Mario Kart DS" en Juegos**: 8 filas para el mismo juego, 3 con **el mismo SHA1** (`691E00D9A5...`). **Investigado — causa raíz encontrada, no es un bug de "Revisar copias"**: consulté `/api/review-queue` en vivo y el grupo SHA1 de Mario Kart DS **sí existe y sí tiene recomendación** (`reasons:["sha1"]`, `recommended:true` en la copia de `E:\Carpetas anbernic\nds\...(USA)...`) — el mecanismo funciona. El problema real es que de las 3 filas, **una es un registro fantasma**: `source_path` apunta a `C:\Users\rammu\Documents\projects\Retro_gaming_app\Este equipo\RG556\Ambernic\nds\Mario Kart DS (USA, Australia)...nds` — la ruta MTP fantasma del bug **INBOX-CFG-1** (`archivo.md`, "arreglado" 2026-08-13), que **ya no existe en disco** (confirmado, `ls` falla) pero la fila de BD nunca se borró. Motivo: `prune_stale_entries()` (`database/repositories/games.py:328-340`) solo borra filas bajo el `source_root` que se está escaneando — como esta fila vive bajo una ruta completamente distinta (dentro del propio repo del proyecto, nunca bajo `E:\Carpetas anbernic`), **ningún scan de la biblioteca real la toca jamás**, quedó huérfana para siempre. **Alcance real, no solo Mario Kart DS**: `SELECT COUNT(*) FROM games WHERE source_path LIKE '%Este equipo%'` → **1.508 filas fantasma** en `library_pc.db`. Estas mismas filas también explican **ZIP-ROUTE-7** (confirmado: `id=65864`, `unknown\10192n.rom`, aparece en `/api/games` con `canonical_title: null` — exactamente "entradas sin portada" que reportó el usuario) — mismo origen, no dos bugs distintos. **Purgado de verdad 2026-08-29** (backup previo en `.rommgr/backup_ghost_purge_2026-08-29/library_pc.db`): script one-off reutilizando `repository.delete_game(id)` ya existente (cascada limpia de `game_metadata`/`game_tags`/`file_operations`, mismo mecanismo de REV43-10) — verificado primero que ninguna de las 1.508 rutas existe en disco (`Path.exists()`) antes de borrar ninguna, cero falsos positivos. Resultado: **1.508/1.508 borradas**, 0 restantes. Verificado en vivo: el grupo de Mario Kart DS en `/api/review-queue` pasó de 3 a 2 entradas (las 2 reales); `total_groups` de la cola bajó de 13.969 a 13.545 (grupos que solo eran fantasma+1 real dejaron de contar como duplicado); `id=65864` (`10192n.rom`) ya no aparece en `/api/games` | `database/repositories/games.py:328-340` (`prune_stale_entries`, scoping por `source_root` — causa de que nunca se autolimpiaran) | ✅ causa raíz documentada y purga ejecutada; sin cambio de código (el diseño de `prune_stale_entries` es correcto para su propósito, el problema era datos huérfanos de un incidente ya cerrado) |

---

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: JUNK-SMART-1/2/3, TABS-FIX-1..7 (+ TABS-FIX-6-DISC, DUP-RA-COLLISION-1), DEVSEL-FIX-1..4 (clasificador de basura por evidencia, auditoría UX Juegos/Organizar/Duplicados, selector de dispositivo — completas, 2026-07-08 a 2026-07-13).

---

### DUP-DISC-RA-1 — Hash RA de discos (PS1 primero) para poder descartar copias sin logros (pedido usuario 2026-08-30)

Origen: tras DUP-REGION-1, el usuario pidió que las copias duplicadas en
plataformas de disco (PSX/Saturn/Dreamcast/Wii) también se puedan descartar
prefiriendo la que tiene soporte RetroAchievements — igual que ya se hace en
GBA. Investigado primero: **0 de 474 juegos PSX con MD5 calculado coincidían
con el caché de RA** (`ra_hashes_12.json`, 1.318 hashes) — 0/29 en Dreamcast
también. Causa: RA no hashea el archivo completo del disco para PS1/Saturn/
Dreamcast, usa un algoritmo específico (localiza `SYSTEM.CNF` en el
filesystem ISO9660, extrae el ejecutable de arranque de la línea `BOOT=`, y
hashea `nombre_exe + bytes_del_exe`) — nuestro MD5 de archivo completo nunca
iba a coincidir, independientemente de la lógica de agrupación.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-DISC-RA-1a | **Implementado y verificado 2026-08-30**: reimplementación en Python del algoritmo de hash PSX de RetroAchievements (`rc_hash_psx`, fuente consultada directamente en github.com/RetroAchievements/rcheevos `src/rhash/hash_disc.c`+`cdreader.c` — no es un port del C, pero fiel byte a byte, incluyendo sus particularidades case-sensitive en "BOOT"/"cdrom:", porque una reimplementación "más limpia" daría un hash *distinto* que nunca coincidiría con el de RA). Soporta `.bin` suelto, `.cue`+`.bin` (primer FILE) y `.chd` (vía `chdman extractcd`, `tools/chdman.exe` ya en el proyecto). **Validado contra caché RA real, no solo con datos sintéticos**: de 259 archivos `.bin`/`.cue` reales de la biblioteca PSX, 124 coincidieron EXACTAMENTE con un hash ya presente en `ra_hashes_12.json` (47,9%) — prueba directa de que el algoritmo es correcto. CHD también probado en vivo (3/15 de una muestra, el resto son juegos fuera del caché de 1.318 o casos sin `SYSTEM.CNF` estándar) — más lento (~7s/archivo, `chdman` descomprime el CHD entero a un `.bin` temporal cada vez, sin caché todavía). Test unitario con imagen ISO9660 sintética mínima construida a mano (`tests/test_ra_hash_psx.py`, 3/3) — no depende de archivos reales | `retroachievements/ra_hash_psx.py` (nuevo), `tests/test_ra_hash_psx.py` (nuevo) | ✅ algoritmo implementado y verificado contra datos reales |
| DUP-DISC-RA-1b | **Parte 1 implementada 2026-08-30**: `ra_checker.check_library()` ya usa el hash de disco (vía `ra_disc_hash_cache.get_psx_disc_hash`, cacheado en `.rommgr/ra_cache/psx_disc_hashes.json` por `(source_path, mtime, size)`) en vez de `row["md5"]` para consolas con `console_id in _DISC_HASH_CONSOLE_IDS` (por ahora solo PSX, 12). Wireado hasta `/api/ra-check` (`web/handlers/sync.py`, pasa `config.chdman`). Test `test_playstation_uses_disc_hash_not_stored_md5`. **Parte 2 (agrupado por edición completa en la cola de duplicados) sigue pendiente** — sin implementar todavía, alcance medido: 71 juegos PSX/Dreamcast/Saturn/Wii con ≥2 ediciones regionales completas en `library_pc.db` | `retroachievements/ra_checker.py`, `retroachievements/ra_disc_hash_cache.py` (nuevo), `web/handlers/sync.py` | 🟡 hash-check hecho, agrupado por edición pendiente |
| DUP-DISC-RA-1c | **Pendiente, no implementado**: mismo algoritmo pero para Saturn/Dreamcast (formatos de disco distintos — Saturn usa IP.BIN en vez de SYSTEM.CNF, Dreamcast usa IP.BIN también pero con su propio formato) — Wii no aplica (no es un CD, RA lo hashea distinto, wiiiso/formato propio). Solo PSX cubierto por ahora, pedido explícito del usuario ("el hash RA de disco primero") | — | 🔴 pendiente, no implementado |
| DUP-DISC-RA-2 | **Implementado y verificado 2026-08-30** (pedido explícito del usuario: "usa chd como formato de psx"). Recomendación confirmada: **CHD**, un archivo por disco, soportado nativamente por RetroArch/`chdman` (ya en `tools/`). Descubierto que ya existía un conversor sin usar (`rommgr convert-chd` / `converters/chd_converter.py`) que solo cubría `.cue`+`.bin` reales — **extendido** en vez de duplicado: (1) `find_bare_bin_files()` descubre `.bin` sueltos sin `.cue` (el caso mayoritario real, ver DUP-DISC-RA-2b) validando con `compute_psx_ra_hash()` que de verdad son un disco legible, no una pista de audio huérfana; (2) `synthesize_cue_text()` genera un `.cue` mínimo de una pista reutilizando `detect_bin_cue_mode()` (nuevo en `ra_hash_psx.py`); (3) `parse_bins_from_cue()` arreglado para resolver solo por nombre base (bug real encontrado: `.cue` con ruta absoluta rota, ver DUP-DISC-RA-2b, hacía que el `cwd=` existente no sirviera de nada); (4) **cada conversión se verifica comparando el hash RA de disco antes/después** (`_verify_ra_hash`) — si no coincide, se borra el `.chd` y el original queda intacto, nunca se sobreescribe a ciegas. `chdman createcd` necesita la palabra `BINARY` en la línea `FILE` del `.cue` sintético (bug propio encontrado y arreglado — sin ella da "Unhandled track type"). 13/13 tests en `test_chd_converter.py` (incluye conversión real de punta a punta con `chdman.exe` y un caso de mismatch de hash forzado). **Dry-run contra la biblioteca PSX real** (`rommgr convert-chd "E:\Carpetas anbernic\psx"`): **181 convertibles** (bare-bin + 0 cue reales, los 18-22 `.cue` reales están todos rotos, ver DUP-DISC-RA-2b), 22 fallos (cue roto), 1 ya convertido. **No ejecutado con `--apply`** contra la biblioteca real — pedido explícito del usuario de construir la herramienta y ejecutarla aparte; nota de rendimiento: un solo disco de ~600MB tardó >10 min con la compresión por defecto de `chdman` en esta máquina, así que los 181 son horas, no minutos — pensar en correrlo en background/durante la noche | `converters/chd_converter.py`, `retroachievements/ra_hash_psx.py` (`detect_bin_cue_mode`), `tests/test_chd_converter.py`, `cli.py` (ayuda actualizada) | ✅ herramienta lista y verificada; ejecución real pendiente, la lanza el usuario |
| DUP-DISC-RA-2b | **Hallazgo colateral real, no arreglado**: los 18-22 `.cue` reales en `psx/` (según se cuenten desde la BD o desde el filesystem) están **todos rotos** — cada uno referencia un `.bin` que no existe bajo ese nombre exacto. Caso más claro: `Chrono Cross (Japan).cue` referencia `Chrono Cross (USA) (Disc 2).bin`, pero el archivo real se llama `Chrono Cross (USA, Canada) (Disc 2).bin` (nombre distinto) — y además hay un `Chrono Cross CD1.img` suelto al lado, sin ningún `.cue` que lo reclame. Otro caso: `Crash 2.cue` referencia `C:\CRASH 2.BIN` (ruta absoluta de otra máquina) y **no existe ningún `.bin` de Crash 2 en la carpeta, con ningún nombre** — el juego está roto hoy, no es un problema de conversión. Parece la versión PSX del patrón ya documentado del proyecto ("PSX siempre por sets: nunca renombrar `.bin` sin reescribir el `.cue`") — probablemente de un renombrado/match anterior que tocó el `.bin` sin tocar el `.cue` o viceversa. No investigado caso a caso (son ~20 juegos, cada uno necesitaría decidir a mano cuál es el `.bin` correcto, si es que existe) | `psx/*.cue` (22 archivos) | 🔴 pendiente investigación caso a caso, no arreglado |

---

## Pilar 2 — Inbox automático — → #203

Soltar un juego sin organizar y que la app lo detecte, empareje con catálogo
y mueva sola, sin intervención manual.

### INBOX-FIX — Bugs del pipeline de extracción/organización (hallados en JUNK-REVIEW-1, 2026-07-08)

Origen: al categorizar los 5.774 ZIPs de `Unknown\` para JUNK-REVIEW-1 se detectaron
tres fallos de raíz en el pipeline de Inbox/setup que explican por qué tantos
archivos quedan varados sin extraer/organizar. Detalle de la investigación:
`Tareas/diario/Día39.md` (sección JUNK-REVIEW-1) y conversación 2026-07-08.
INBOX-FIX-1/2/3 → PRs #85/#87/#88, todas mergeadas. Aplicados manualmente sobre
la biblioteca real 2026-07-08 con el código de esas 3 ramas antes del merge:
20 BIOS movidas a `bios/<slug>/` (+20 filas basura eliminadas de `games`),
1.606 juegos con `platform` recuperado por backfill desde `catalog_source`,
4.515 archivos organizados a su carpeta de plataforma, 139 re-matches (solo 2
genuinamente nuevos, ambos correctos). `Unknown\` pasa de ~6.021 a 1.437 filas
en BD (mayoría categoría 5: componentes MAME + las 15 colecciones de categoría
2, aún pendientes de tu decisión). **INBOX-FIX-5** (PR #90) surgió al verificar
esa aplicación: el borrado por "duplicado" (organize + BIOS intercept) solo
comparaba nombre de archivo, no contenido — 22 archivos reales borrados sin ser
duplicados de verdad (SHA1 distinto). Ya arreglado: compara SHA1 antes de borrar.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| INBOX-FIX-1 | **`extract_zip` aborta el ZIP entero por una sola colisión + el setup wizard nunca borra el origen** — `converters/zip_extractor.py:106-114`: si un solo archivo de destino ya existe, se salta la extracción de **todo** el ZIP (sin avisar, sin extraer el resto). `web/inbox_pipeline.py:294` (`_run_setup_pipeline`) llama `extract_zip(..., delete_source=False)` hardcodeado. Confirmado en biblioteca real: `Nintendo - SNES.zip` (325 juegos) tiene algunos ya extraídos sueltos en `Unknown\` y el resto (`Blackthorne`, `BioMetal`...) nunca extraído por la colisión con uno solo. Fix: extraer archivo por archivo saltando solo los que colisionan (no abortar el ZIP completo); exponer `delete_source` como opción real del wizard. | `converters/zip_extractor.py`, `web/inbox_pipeline.py` | ✅ `extract_zip` ahora extrae miembro a miembro (solo salta los que colisionan, ya no aborta el ZIP); el original solo se borra si todo su contenido queda confirmado en disco sin errores. Checkbox nuevo "Borrar el ZIP original..." en el wizard (`wiz-delete-zips`, desmarcado por defecto). 4 tests nuevos (`tests/test_zip_extractor.py`) — PR #85 |
| INBOX-FIX-2 | **El catalog match nunca escribe `platform` en la BD** — `repository.update_match()` (`database/repositories/games.py:182`) ya soporta `platform=`, pero ninguno de los dos call-sites lo pasa (`web/inbox_pipeline.py:332` en setup, `:473` en inbox). Consecuencia: el 96% de los juegos individuales sueltos en `Unknown\` ya tienen `canonical_title` matched (1.658/1.727) pero quedan con `platform=NULL` para siempre, así que el paso "organize" nunca sabe a qué carpeta moverlos. Fix: derivar `platform` del nombre del DAT (`catalog_source`, p.ej. `"Nintendo - Super Nintendo Entertainment System.dat"`) vía un mapeo DAT→plataforma, poblar `MatchResult.platform` también en la rama No-Intro/Redump (hoy solo se pone en la rama arcade, `catalog/matcher.py:20`), y pasar `platform=m.platform` en ambos call-sites. | `catalog/matcher.py`, `web/inbox_pipeline.py` | ✅ `_platform_from_dat_name()` + 18 tests — PR #87 |
| INBOX-FIX-3 | **Categoría 5 de JUNK-REVIEW-1 (1.105 ZIPs sueltos en `Unknown\`) son mayoritariamente infraestructura MAME, no juegos** — `catalog/mame_loader.py:32` ya excluye `isbios`/`isdevice` al indexar, así que la mayoría (`c1541.zip`, `kb_pcat101.zip`, `sb16.zip`...) nunca podrá matchear porque no son juegos jugables por sí solos (mismo perfil que los chips ya borrados en JUNK-CLEAN-1, Día39). Los más grandes sí son BIOS de sistema con nombre reconocible (`naomi.zip`, `chihiro.zip`, `triforce.zip`, `hikaru.zip`, `aristmk5/6.zip`, `hod2bios.zip`, `lindbios.zip`, `f355bios.zip`, `galgbios.zip`, `airlbios.zip`, `ar_bios.zip`, `cdibios.zip`, `macsbios.zip`, `alg_bios.zip`, `crysbios.zip`, `v4bios.zip`) pero **faltan en `_KNOWN_BIOS_MAP`** (`web/inbox_pipeline.py:54-112` — hoy solo tiene `stvbios.zip`→saturn y `awbios.zip`→naomi de este grupo). Además el "Step 1.5: Intercept BIOS files" que mueve BIOS conocidas a `bios/<plataforma>/` **solo corre en `_run_inbox_pipeline`, no en `_run_setup_pipeline`** — el asistente de primera configuración (que probablemente procesó `Unknown\` originalmente) nunca ejecuta ese paso. Fix: ampliar `_KNOWN_BIOS_MAP` con estas entradas y extraer el intercept a una función compartida que también llame `_run_setup_pipeline`. Tras INBOX-FIX-2, re-lanzar el match arcade sobre el resto (los `.zip` sin nombre de BIOS conocido) para ver qué queda genuinamente sin identificar antes de decidir si se borra. | `web/inbox_pipeline.py` | ✅ `_intercept_bios_files()` compartida por ambos pipelines + 16 BIOS arcade nuevas en el mapa; 5 tests (`tests/test_bios_intercept.py`) — PR #88 |
| INBOX-FIX-4 | **`_run_setup_pipeline` construye el plan de renombrado pero nunca lo aplica** — a diferencia de `_run_inbox_pipeline` (extract→scan→match→plan→**rename→organize**→cleanup, todo automático), el asistente de primera configuración se para en "build plan" (Step 5) y deja el resto para una acción manual aparte. Es la razón de fondo por la que `Unknown\` quedó con miles de archivos sin categorizar tras el primer scan de la biblioteca real — nadie ejecutó nunca el equivalente de los Steps 5-6 del pipeline de Inbox sobre ella, así que hubo que aplicar los fixes con scripts manuales en vez de con la app. **Decisión de diseño (2026-07-23): NO auto-aplicar** — mantener la revisión manual (regla `rommgr plan siempre antes de apply` intacta); el wizard debe dirigir explícitamente al usuario a un botón "Aplicar plan" al terminar el Step 5 en vez de dejarlo ahí sin más pasos. | `web/inbox_pipeline.py` (`_run_setup_pipeline`) | ✅ **ya implementado, sin código nuevo** — verificado 2026-07-23: `_showSetupResult()` (`overview.js`) ya muestra en la página 3 del wizard "Siguiente paso: revisa el plan de renombrado y aprueba los cambios" + un botón primario destacado "Ir a Organizar y renombrar ▶" (`wizardGoToOrganize()`, `_banners.html`) que navega directo a la pestaña Organizar/Renombrar. Esta UI viene de FLOW-WIZARD (`2e4dba0`, 2026-04-14) — **anterior** a que se documentara este hallazgo (JUNK-REVIEW-1, 2026-07-08); el episodio real de `Unknown\` sin categorizar ocurrió con una versión de la app previa a que existiera este wizard. Nada que tocar hoy: el flujo actual ya cumple la decisión de diseño acordada |
| INBOX-FIX-5 | **El borrado por "duplicado" (organize + BIOS intercept) solo comparaba nombre de archivo, no contenido** — bug de pérdida de datos real: aplicado a la biblioteca real, 22 archivos "duplicados" borrados resultaron tener SHA1 distinto del superviviente (dumps/revisiones distintas que solo compartían nombre). `Path.unlink()` en Windows no pasa por la Papelera — no recuperable. | `web/inbox_pipeline.py` | ✅ `_same_content()` (tamaño + SHA1) antes de borrar en ambos sitios; si difiere, no se toca ninguno y se reporta para revisión manual. 8 tests — PR #90 |
| MATCH-FIX-1 | **`CatalogMatcher.match()` — Pass 2 (nombre) da falsos positivos en ficheros arcade sin tag de región** — nombres cortos estilo MAME (`flicky.zip`, `frogger.zip`, `dw.zip`…) sin `(Region)` colisionan por coincidencia de título normalizado contra catálogos No-Intro/Redump de plataformas completamente ajenas (`flicky.zip` → "Fujitsu - FM-7", `frogger.zip` → "APF - Imagination Machine") con confianza `low`, en vez de matchear contra el catálogo arcade correcto (Pass 3, que nunca llega a probarse porque Pass 2 ya "acertó"). Detectado 2026-07-08 al re-lanzar el match sobre `Unknown\` — son matches **preexistentes**, no introducidos hoy. Fix: para nombres sin región/paréntesis, probar primero el catálogo arcade (Pass 3) antes que el name-fallback No-Intro/Redump (Pass 2), o exigir una señal más fuerte que la sola coincidencia de título normalizado. | `catalog/matcher.py` | ✅ rama `fix/match-fix-1-arcade-before-name-fallback` — para `.zip` sin `(` en el nombre (estilo MAME) el pass arcade corre antes que el fallback por título; el resto conserva el orden actual. Passes 2/3 extraídos a `_match_by_title()`/`_match_arcade()`. 4 tests nuevos (caso real flicky.zip vs FM-7; 635 pass). **Pendiente aparte**: los falsos matches preexistentes en BD no se corrigen solos — re-lanzar el match sobre `Unknown\` tras mergear |
| MATCH-FIX-2 | **Caso real 2026-08-29, buscando "Final Fantasy III" en Juegos**: 36 archivos `.nes`/.zip completamente distintos (romhacks/traducciones fan en inglés v1.0, v3.1, francés, italiano, portugués de Brasil, uno con "Final Fantasy VI Font"…) reciben **el mismo** `canonical_title` — "Final Fantasy III (Japan) (Virtual Console)" — y encima **`platform: "Nintendo 3DS"` para archivos `.nes`**, con `match_confidence: "low"`. Causa raíz confirmada leyendo el código: `_build_title_index()` (`catalog/matcher.py:152-161`) mezcla entradas de **todos los DATs de todas las plataformas** en un único índice por título normalizado, sin separar por plataforma; `_match_by_title()` (`catalog/matcher.py:233-255`) cuando hay varios `hits` para la misma clave (ambiguo) **siempre devolvía `hits[0]`** — el que haya quedado primero en la lista, que depende de qué archivo `.dat` cargó antes en `sorted(directory.glob("*.dat"))` (`catalog/matcher.py:142`, orden alfabético) — "Nintendo - Nintendo **3**DS..." ordena antes que "Nintendo - Nintendo **E**ntertainment System...", así que el título del NES real perdía sistemáticamente contra el de la re-edición de 3DS. Mismo patrón de fondo que MATCH-FIX-1 (Pass 2 sin señal fuerte) pero más amplio: cualquier título reutilizado entre plataformas (remakes, Virtual Console, romhacks) heredaba la plataforma equivocada. | `catalog/matcher.py:152-161` (`_build_title_index`), `:233-262` (`_match_by_title`), `:142` (orden de carga de DATs) | ✅ `_match_by_title` ahora, ante ambigüedad, prefiere el `hit` cuya plataforma (`_platform_from_dat_name`) coincide con la extensión real del archivo vía `PLATFORM_BY_EXTENSION` (`detection/platform_detector.py`, ya existente, import a nivel de módulo — sin ciclo, `platform_detector.py` no importa nada de `rom_manager`); si ninguno coincide (p.ej. `.zip`, ambiguo por diseño — no está en `PLATFORM_BY_EXTENSION`) cae al comportamiento anterior (`hits[0]`). 2 tests nuevos en `tests/test_catalog_matcher.py` (reproducen el caso real con los mismos nombres de `.dat`; 1038 pass). **Verificado contra los DATs reales de la biblioteca**: `Final Fantasy III (J) [T+Bra1.0_Hexagon].nes` y `Final Fantasy III (Japan) (Virtual Console).nes` ahora resuelven a `platform: NES` / `Nintendo - Nintendo Entertainment System (Headered)...dat` (antes `Nintendo 3DS`); el mismo título en `.zip` (sin señal de extensión) sigue cayendo en 3DS, limitación conocida y documentada — necesitaría inspección de contenido, no solo nombre. **Ejecutado de verdad 2026-08-29** (backup previo en `.rommgr/backup_matchfix2_2026-08-29/library_pc.db`): `get_unresolved_games()` (`database/repositories/games.py`) ganó el parámetro `include_low_confidence` — sin él, `/api/match` solo re-evalúa filas con `match_confidence IS NULL`, así que las ya matcheadas mal (`match_confidence='low'`, como las 36 de Final Fantasy III) eran invisibles para siempre una vez matcheadas, por mucho que se relanzara "Identificar (catálogos)" desde la UI. `POST /api/match {"include_low_confidence": true}` (nuevo body opcional, mismo endpoint) re-evalúa también esas. Corrida real sobre la biblioteca completa: `total=26.152, matched_low=20.961, unmatched=5.191, matched_high=0` (esperado — estas filas ya habían fallado el Pass 1 SHA1 antes). Verificado en la propia BD: los 11 `.nes` de Final Fantasy III pasan de `platform: Nintendo 3DS` a `platform: NES` con título correcto `"Final Fantasy III (Japan)"`; los `.zip` del mismo juego (sin extensión que desambigüe) siguen en `Nintendo 3DS` — limitación conocida, no arreglada (necesitaría mirar el contenido, no el nombre) |

> Quedan pendientes: INBOX-FIX-4 (decisión de diseño sobre auto-apply del wizard)
> y la decisión del usuario sobre las 15 colecciones completas de
> JUNK-REVIEW-1 (categoría 2). MATCH-FIX-1/2 cerrados y re-match ya ejecutado
> sobre la biblioteca real (2026-08-29).

---

### ZIP-ROUTE — Colocar los ZIPs sueltos por CRC del header (diseño 2026-07-10)

Origen: tras JUNK-SMART quedaban 56 "colecciones" + 208 "ZIPs no-ROM" + 5
arcade en `Unknown\`. Investigación (informe completo con los 269 ZIPs y su
destino: `Tareas/zip-route-identificacion.md`): **el header de un ZIP ya trae
el CRC32 de cada entrada** (`zipfile.ZipInfo.CRC`, stdlib, cero
descompresión) y la app ya parsea el CRC de los DATs
(`CatalogEntry.crc32`, `catalog/catalog_loader.py:104`) — solo que el matcher
indexa únicamente por SHA1 (`catalog/matcher.py:112`). Cruzando ambos:
**268/269 identificados** — 95 juegos de consola con match exacto No-Intro/
Redump, 79 sets arcade al 100 % (votación de CRCs contra MAME 0.286 + FBNeo,
incluye sets disfrazados tipo `Lemmings (United Kingdom).zip` → `lemmings`),
29 sets arcade probables, 49 romhacks/T-En (plataforma inequívoca por la
extensión interna), 16 colecciones reales (zip-de-zips / .chd) y 1 resto.

Hallazgo extra: la heurística de colección `" - " in stem`
(`web/builders/folders.py:259`) tiene ~39 falsos positivos de 56 (juegos
sueltos con " - " en el título: `Fire Emblem - ...`, `Dragon Quest III - ...`)
— Día40 registró "un único falso positivo" y no era cierto. Con ZIP-ROUTE-1
la heurística por nombre sobra: colección = multi-entrada de `.zip`/`.chd`.

Los tags del nombre de archivo mienten sistemáticamente (`(XBLA)`, `(Disk 1)`,
`(Windows)`… envuelven ROMs de SNES/N64/GG normales): **el contenido es la
única evidencia fiable, nunca el nombre.**

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ZIP-ROUTE-1 | **Índice CRC32 en el matcher + pass consola para ZIPs** — índice `crc32 → (CatalogEntry, dat)` junto al de SHA1; para un `.zip` suelto con 1 entrada cuyo CRC matchea No-Intro/Redump → identidad exacta (nombre canónico + plataforma del DAT) sin extraer. En el junk-scan la categoría pasa a `misplaced` con destino conocido; plan/apply mueve y renombra. Cubre 95. Ojo: 4 matchean el DAT de Evercade además del de 2600 — preferir el DAT de la plataforma real si hay doble hit. | `catalog/matcher.py`, `web/builders/folders.py`, `web/handlers/esde/maintenance.py` | ✅ rama `feature/zip-route-1-crc-console-pass` — `CatalogMatcher.crc_index()` devuelve `crc32 → (título, dat, plataforma)`; CRC con dos títulos distintos se descarta como ambiguo (los 4 "Evercade" resultaron ser dumps solo-Evercade, sin colisión real). Categoría nueva "ROMs de consola identificadas (mover a su plataforma)" (`misplaced`), cada archivo lleva `identified_as`/`dat`/`platform`. Verificado contra biblioteca real: 95 identificados, colecciones 56→47, ZIPs no-ROM 208→122; índice +16 s por scan (cachear si duele). El mover/renombrar queda para cuando exista plan/apply de misplaced. 5 tests (634 pass) |
| DAT-FIX-1 | **El DAT de Wii U (Digital) nunca carga** — `load_nointro_dat` revienta con `int('')` en `catalog_loader.py:135` (`size=""` en algunos `<rom>`); `_load_dir` lo captura y **salta el DAT entero** con un warning. Fix trivial: `int(rom.get("size") or 0)`. Descubierto al verificar ZIP-ROUTE-1. | `catalog/catalog_loader.py:135` | ✅ duplicado de **INICIO-FIX-1** (mismo bug, misma línea) — corregido el 2026-07-16 en rama `fix/inicio-ux` (`int(rom.get("size", 0) or 0)`). Entrada dejada como referencia histórica |
| ZIP-ROUTE-2 | **Identificar sets arcade por votación de CRCs** — índice `crc → {sets}` de los DATs arcade (`MAME 0.286 (arcade).dat` + FBNeo, iterparse); cobertura 100 % → renombrar al nombre de set y mover a `arcade\` (79, incluye los 5 "arcade sin organizar" y los 48 clones mame-stem que el XML local no lista); 1-99 % → `review` con candidato sugerido (29, otra versión de romset). | `catalog/mame_loader.py` (o loader hermano), `web/builders/folders.py` | ✅ rama `feature/zip-route-2-arcade-crc-voting` (apilada sobre ROUTE-5) — `load_arcade_crc_index()` (solo `.dat`, iterparse, +2,4 s, 162k CRCs) + `_vote_arcade_set()` (ignora entradas vacías, CRC 0 espurio). Categorías nuevas: "ROMs arcade identificadas (renombrar al set y mover)" (`misplaced`, con `identified_as`) y "Sets arcade de otra versión (revisar)" (`review`, con `coverage`). Verificado contra biblioteca real: 78 al 100 % + 28 parciales; ZIPs no-ROM 153→47. **Ojo para el mover futuro**: los DATs FBNeo de consola también votan (Gleylancer [T-En]→`gleylance`) — el destino no siempre es `arcade\`, hay que mapear DAT→carpeta al mover. 4 tests (639 pass) |
| ZIP-ROUTE-3 | **Romhacks: plataforma por extensión interna** — sin match CRC pero 1 entrada con extensión inequívoca (`.nes`/`.sfc`/`.md`/`.gba`/`.gg`/`.pce`…) → mover a la carpeta de esa plataforma conservando el nombre (49 T-En/hacks; siguen sin `canonical_title`, correcto — no están en ningún DAT). | `web/builders/folders.py` | ✅ rama `feature/zip-route-3-romhack-inner-ext` (apilada sobre ROUTE-2) — `_single_rom_platform()` usa `PLATFORM_BY_EXTENSION` (vía módulo, no import directo — reload_platforms rebindea); `.md` y demás extensiones con contexto se excluyen (¿Mega Drive o markdown? sin carpeta no se desambigua). Categoría "ROMs/romhacks por extensión (mover a su plataforma)" (`misplaced`, con `platform`). Verificado: 44 romhacks con plataforma; **"ZIPs no-ROM" queda en 3** (2 romhacks `.md` + 1 addon) de los 208 originales. 2 tests nuevos + 2 adaptados (641 pass) |
| ZIP-ROUTE-4 | **Colecciones → extraer al Inbox** — para las 16 colecciones reales (multi-entrada `.zip`/`.chd`, ~26 GB: `Nintendo - GBA.zip` 150 zips, `Arcade - Mame 2003 Plus.zip` 375, `NEC - TurboGrafx CD.zip` 25 .chd…): botón "Extraer al Inbox" que descomprime los miembros en el Inbox y deja que el pipeline existente haga hash → match → rename → organize (el intercept de BIOS ya rutea `MAME BIOS 0.277.zip`). Guard de espacio libre ≥ tamaño descomprimido; borrar el contenedor solo tras extraer con éxito, una colección por job. **Requisito (usuario, 2026-07-10): cero duplicados** — tras organizar, ni el ZIP contenedor ni copias intermedias pueden quedar en el Inbox; verificar que el organize del pipeline mueve (no copia) y limpia el Inbox al terminar. **Requisito (usuario, 2026-07-10): UN solo paso** — el usuario no extrae ni pulsa un segundo botón. | `web/inbox_pipeline.py`, `web/handlers/esde/maintenance.py`, UI | ✅ rama `feature/zip-route-4-one-step-apply` (apilada sobre ROUTE-3) — módulo nuevo `web/zip_router.py`: `_route_identified()` (arcade → directo a `arcade\` renombrando al set, **nunca por el Inbox** — el pipeline extraería el ZIP y un set arcade extraído está roto; colecciones → por mayoría de miembros: sets arcade → extraer a `arcade\` [salva a `SNK - NEO GEO.zip` y `Arcade - Mame 2003 Plus.zip`], BIOS/infra → no tocar [`MAME BIOS 0.277.zip`], consola → extraer al Inbox; contenedor borrado solo con todos los miembros en disco; consola+romhacks → mover al Inbox) y `_run_zip_route_apply()` que encadena `_run_inbox_pipeline(delete_source=True)` bajo el mismo job "inbox" (nuevo param `extra_result`). Conflictos: destino existente → no tocar y reportar. Endpoint `POST /api/zip-route-apply` + botón "Organizar identificados (1 paso)" en el junk-scan (muestra `identified_as`/`platform` por archivo). Dry-run contra biblioteca real: 83 arcade directo, 2 colecciones a arcade, 13 al Inbox, 1 skip BIOS, 139 zips al Inbox. 4 tests (645 pass). **Ejecutado de verdad 2026-07-10** (backup previo de `library_pc.db`): 77 arcade movidos, 15/16 colecciones extraídas (1.746 miembros), 139 zips al Inbox, 1.636 zips extraídos de colecciones, 3.134 ROMs escaneados, 2.915 matched, 1.062 renombrados, 136 organizados (la mayoría del resto eran duplicados exactos ya en la biblioteca → borrados por política de deduplicación, no "organizados"). 6 conflictos arcade ya existentes + 1 pack BIOS omitidos (esperado). **3 hallazgos reales durante la ejecución → ver ZIP-ROUTE-FIX-1/2/3.** |
| ZIP-ROUTE-FIX-1 | **`rename_rom_with_saves` no crea el directorio destino** — a diferencia de `move_disc_set_to_subfolder` (que sí llama `target_dir.mkdir(parents=True, exist_ok=True)` antes de mover), `rename_rom_with_saves` va directo a `os.rename(source, target)` sin asegurar que `target.parent` existe. Cuando el plan de renombrado manda un ROM a una subcarpeta nueva (p. ej. "Virtual Console"), falla con `WinError 3` (ruta no encontrada). **Sin pérdida de datos** — el fallo es atómico, el archivo se queda donde estaba y el organize posterior lo mueve igualmente (con el nombre viejo, no el canónico). Descubierto al ejecutar ZIP-ROUTE-4 sobre la biblioteca real: 20 renombrados fallidos (límite de la lista de errores, puede haber más). | `renamer/file_renamer.py:76` (antes de `os.rename`) | ✅ rama `feature/zip-route-fix-1-mkdir-target-dir` — `target.parent.mkdir(parents=True, exist_ok=True)` antes de `os.rename`, mismo patrón que `move_disc_set_to_subfolder`. `tests/test_file_renamer.py` (nuevo, 2 tests: subcarpeta nueva + mismo directorio). 647 pass |
| ZIP-ROUTE-FIX-2 | **`UNIQUE constraint failed: games.source_path` al organizar** — el `UPDATE games SET source_path=...` tras mover el archivo (inbox_pipeline.py:646-650) falla cuando ya existe otra fila en `games` con ese `source_path` exacto, aunque el `dest_file.exists()` de la línea 622 no lo detectó antes de mover (filas "fantasma" que apuntan a una ruta sin archivo real, probablemente de una sesión anterior nunca limpiada). El archivo físico SÍ queda movido a su destino final — el problema es solo de consistencia de la BD (fila vieja huérfana + el `UPDATE` de la fila nueva no se aplica). Descubierto al ejecutar ZIP-ROUTE-4: 20 casos (límite de la lista, puede haber más). Investigar de dónde salen esas filas fantasma antes de decidir el fix (¿borrar huérfanas al detectarlas? ¿`INSERT OR REPLACE`?). | `web/inbox_pipeline.py:643-653` | ✅ rama `feature/zip-route-fix-2-ghost-row-cleanup` — `DELETE FROM games WHERE source_path=? AND id!=?` en la misma transacción `batch()` justo antes del `UPDATE`; el físico ya se había movido de todas formas, así que borrar la fila fantasma es seguro (no puede haber dos archivos reales en la misma ruta). `tests/test_inbox_pipeline_organize.py` (nuevo). 646 pass |
| ZIP-ROUTE-FIX-3 | **La ambigüedad de `.md` (ZIP-ROUTE-3) deja cientos de ROMs de Mega Drive sin clasificar, no solo "2-3"** — el diseño original asumía pocos casos (`"ZIPs no-ROM" queda en 3"`); al extraer de verdad las colecciones "Sega - Genesis"/"Sega - Genesis (Update 1)" sus miembros `.md` sueltos entran al Inbox y el pipeline normal hereda la misma ambigüedad (¿Mega Drive o markdown?) sin la ventaja de contexto de carpeta que sí tenía el ZIP. Resultado real: **345 archivos `.md`** quedaron sin organizar en el Inbox tras ZIP-ROUTE-4 (de un total de 458 archivos restantes). No hay pérdida — siguen en el Inbox — pero el "un solo paso" prometido no cubre este caso. Posible fix: dentro del Inbox (con contexto de carpeta/colección de origen conocido) desambiguar `.md`→Mega Drive cuando el resto de la carpeta ya se resolvió a esa plataforma. | `web/builders/folders.py` (`_single_rom_platform`), `web/inbox_pipeline.py` (platform detection) | ✅ rama `feature/zip-route-fix-3-md-context-tokenize` — causa raíz real: `_has_platform_context` (`detection/platform_detector.py:93`) exigía coincidencia EXACTA de una parte de la ruta contra "genesis"/"megadrive"/"md"/"sega genesis"; ZIP-ROUTE-4 extrae la colección a una carpeta con el nombre literal del ZIP ("Sega - Genesis"), que nunca iguala ninguno de esos nombres aunque los contenga. Fix: tokenizar cada parte de **carpeta** (`path.parent.parts`, nunca el nombre de archivo — si no, el propio ".md" del archivo se autoconfundiría con el token "md") por separadores no alfanuméricos. 2 tests nuevos + los 5 existentes de `.md` siguen en verde. 647 pass. **Ejecutado de verdad 2026-07-10** (backup previo de `library_pc.db`): 573 `.md` organizados en `megadrive\` (antes 0). Quedan 177 `.md` sueltos en la raíz del Inbox sin carpeta que los desambigüe — genuinamente ambiguos por diseño, no un bug; posible ZIP-ROUTE-FIX-4 futuro: identificarlos por CRC/tamaño en vez de contexto de carpeta. |
| RA-CONFLICT-1 | **Los conflictos "mismo nombre, contenido distinto" del organize del Inbox usan RA para decidir el ganador** — antes se limitaba a reportar en `organize_errors` y dejar todo para revisión manual. La lógica de "quedarse con la versión que tiene logros RA" ya existía para conflictos del *plan* (`apply_ra_conflicts` en `services/ra_duplicates_service.py`), pero el organize del Inbox usa su propio chequeo de colisión (`inbox_pipeline.py`, `dest_file.exists()` + `_same_content`) y no llamaba a esa lógica — rutas de código independientes. Petición del usuario 2026-07-10 tras encontrar 20 conflictos reales de este tipo en la biblioteca. | `services/ra_duplicates_service.py`, `web/inbox_pipeline.py` | ✅ rama `feature/ra-conflict-resolution-inbox-organize` — refactor: `apply_ra_conflicts` exponía la lógica de lookup RA como closures internos (`_hash_lib_for`/`_ra_for_path`); se extrajeron a funciones de módulo reutilizables `get_ra_hash_lib()`/`get_ra_achievements()`/`get_ra_achievements_for_path()` (mismo comportamiento, 4 tests existentes en verde sin cambios). Nueva función `_resolve_organize_conflict()` en `inbox_pipeline.py`: mismo criterio de desempate que `apply_ra_conflicts` (más logros gana; empate o ambos sin datos RA → sin resolver, igual que antes); reutiliza `_discard_file()` (soft-discard a `_descartados/` + borra fila BD) para el perdedor. Contador nuevo `ra_resolved` en el resultado del job "inbox". 3 tests nuevos (`test_inbox_ra_conflict.py`): source gana, dest gana, sin datos RA → sin tocar. 653 pass. **Ejecutado de verdad 2026-07-10** (backup previo de `library_pc.db`): `ra_resolved: 3` sobre los conflictos reales de la biblioteca; quedan 20 sin resolver por falta de datos RA para esa plataforma/hash — comportamiento idéntico al anterior para esos casos, nada perdido. |
| RA-CONFLICT-2 | **Revisar/resolver a mano desde la UI los conflictos que RA no puede decidir** — RA-CONFLICT-1 resuelve solo los que tienen datos RA; el resto (sin caché para esa plataforma/hash) quedaban solo como texto en `organize_errors`, sin forma de actuar salvo tocar archivos a mano. Petición del usuario 2026-07-10. | `web/inbox_pipeline.py`, `web/handlers/inbox.py`, `web/static/partials/tab-inbox.html`, `web/static/js/tabs/inbox.js`, `web/static/js/main.js` | ✅ rama `feature/ra-conflict-ui-resolution` — nuevas funciones puras `find_organize_conflicts()` (listado de solo lectura: recorre `games` bajo el Inbox, mismo cálculo de destino que el Step 6 real vía `_organize_dest_file()` extraído para no duplicarlo, incluye tamaños y logros RA de ambos lados) y `resolve_inbox_conflict()` (re-verifica que el conflicto sigue existiendo y llama a `_resolve_organize_conflict()` con el nuevo parámetro `force_keep` — mismo mecanismo de discard/move que la resolución automática, decisión inyectada en vez de calculada). Endpoints `GET /api/inbox-conflicts` + `POST /api/inbox-conflicts/resolve`. UI: sección nueva en la pestaña Inbox con botón "Revisar" → tabla (archivo, plataforma, tamaño+logros de cada lado, botones "Quedarme con Inbox"/"Quedarme con existente"). 5 tests nuevos (`test_inbox_conflicts_ui.py`), 658 pass. Verificado el endpoint de lectura contra la biblioteca real (40 conflictos con datos correctos); el de escritura solo verificado con tests (no se resolvió ningún conflicto real de la biblioteca desde este endpoint — queda para que el usuario lo use desde la UI). |
| ZIP-ROUTE-5 | **Retirar la heurística de colección por nombre** — sustituir `" - " in stem` + `>1 GB` (`web/builders/folders.py:259,276`) por "multi-entrada de `.zip`/`.chd`" (el ZIP ya se abre para ROUTE-1, es gratis). Elimina los ~39 falsos positivos. | `web/builders/folders.py` | ✅ rama `feature/zip-route-5-collection-by-content` (apilada sobre ROUTE-1) — colección = >1 entrada y mayoría `.zip`/`.chd` (`_is_source_collection`); fuera `" - "` y `_COLLECTION_MIN_BYTES`. Verificado contra biblioteca real: colecciones 47→**16, exactamente los contenedores reales** (incl. `MAME BIOS 0.277.zip`); los ~31 ex-falsos (T-En, FM77AV, Super Pocket) caen a "ZIPs no-ROM" (122→153) a la espera de ROUTE-2/3. 2 tests nuevos + 3 adaptados (635 pass) |
| ZIP-ROUTE-7 | **Feedback usuario 2026-08-29**: en la pestaña Juegos hay entradas sin portada, posiblemente `.zip` que no deberían aparecer como juego (mal clasificados: algunos se extraen y no deberían, otros deberían extraerse y no se hizo). **Causa parcial resuelta 2026-08-29 vía DEDUP-RENAME-3**: 1.508 filas fantasma (residuo del bug INBOX-CFG-1, `source_path` bajo una ruta MTP que ya no existe) purgadas de `library_pc.db` — `id=65864` (`unknown\10192n.rom`, sin portada) confirmado desaparecido de `/api/games` tras la purga. **Sigue sin confirmar** si esto cubre el 100% de las entradas sin portada reportadas o si además hay `.zip` genuinamente mal clasificados (extraídos cuando no debían, o al revés) — esa segunda mitad del hallazgo original sigue sin investigar | `web/builders/folders.py`, `web/zip_router.py` | 🟡 causa fantasma resuelta (ver DEDUP-RENAME-3); falta confirmar si queda algo real de `.zip` mal clasificados |
| ZIP-ROUTE-6 | **Colecciones con subcarpetas internas por sub-plataforma se extraen sin separar** — `_extract_collection` (`web/zip_router.py:47-72`) llama `zf.extract(m, dest_dir)` conservando la ruta interna de cada miembro (`m.filename`); para un contenedor plano (todos los `.zip` sueltos en la raíz, el único caso probado hasta ahora) da igual, pero para un bestset con subcarpetas por sub-sistema — caso real: `fbneo_1003_bestset` de archive.org, 4,67 GB / 636 sets bajo `games/<cps1\|cps2\|cps3\|neogeo\|fbneo\|toaplan_cave_stg>/` — el resultado sería `arcade/games/cps1/sf2.zip` en vez de separar por plataforma: mezcla cps1/cps2/cps3/neogeo (carpetas y sistemas Daijishō ya distintos hoy, ver `docs/arcade-setup.md`) todo anidado bajo `arcade/`, y `toaplan_cave_stg/` no tiene carpeta equivalente en la convención del proyecto. La clasificación previa (`_is_source_collection`) sí es correcta — cae en "Colección fuente (revisar)" como debe. Hallazgo del usuario 2026-08-28 con una descarga real, solo inspección de código + listado del ZIP (`Compress.ZipFile`), sin llegar a ejecutar el apply | `web/zip_router.py:47-72` (`_extract_collection`) | ⬜ documentado 2026-08-28, → #203 |

> Orden: 1 → 5 → 2 → 3 → 4 (1 crea el índice y el open del ZIP que reutilizan
> los demás; 4 es la única que toca disco en masa y va la última).
> Scripts de la investigación en scratchpad Día41: `identify_zips.py`,
> `identify_arcade.py` (reproducibles).

---

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: ARCADE-RECON-1..4, INBOX-UX-1..6, INBOX-CFG-1..4, INBOX-ORPHAN-1/2 (reconstrucción de sets MAME sueltos, auditoría UX Inbox, fix de target_root y saves huérfanos — completas, 2026-08-13 a 2026-08-14).

---

### INBOX-FIX-6 — ZIPs de consola (PS2 confirmado) se renombran/colocan pero nunca se descomprimen (hallazgo usuario 2026-08-29)

Origen: el usuario reporta que tras organizar la biblioteca con el Inbox, varios
`.zip` de PS2 (y sospecha que de otras plataformas) quedaron en su carpeta de
plataforma correcta, con nombre canónico, pero **sin descomprimir** — inútiles
para el emulador (PCSX2/AetherSX2 no leen un `.iso` dentro de un `.zip`).
Verificado en la biblioteca real (`library_pc.db`): 20 `.zip` en `ps2\` con
`platform: PlayStation 2` y nombre canónico correcto, `created_at` repartido en
varias tandas (2026-03-24, 2026-08-28 en tres lotes) — no es un caso aislado ni
antiguo, sigue ocurriendo con datos recientes.

Causa raíz confirmada leyendo el código: hay **dos únicos caminos que
descomprimen un ZIP** en toda la app — `_run_inbox_pipeline` (`web/inbox_pipeline.py:955`,
`find_zip_files(inbox)`) y `_run_setup_pipeline` (`:818`) — **ambos escanean
solo dentro de una carpeta concreta** (`inbox/`, o la carpeta de origen del
wizard). El flujo general de Organizar/Renombrar (`web/handlers/organize.py::_do_apply`,
líneas 92-162) **no tiene ninguna llamada a `extract_zip` en todo el archivo**
— solo `rename_rom_with_saves` (mover + renombrar, nunca descomprimir). Un
`.zip` de consola identificado por CRC (`CatalogMatcher.crc_index()`, ZIP-ROUTE-1)
o que ya vivía suelto dentro de `ps2\` antes de pasar por match/plan/apply
termina con nombre y ubicación correctos pero **sigue siendo un `.zip` para
siempre** — el diseño original de ZIP-ROUTE-1 ya lo advertía ("el mover/renombrar
queda para cuando exista plan/apply de misplaced") pero esa segunda mitad
(descomprimir tras colocar) nunca se cerró para el flujo general, solo para el
que pasa por el Inbox real.

**Respuesta a la pregunta del usuario sobre arcade**: no, con arcade NO hay que
descomprimir — es una decisión de diseño ya tomada y correcta (`zip_router.py`,
regla documentada en `.claude/CLAUDE.md`: "un ZIP arcade nunca se extrae, el ZIP
es el ROM" — los cores MAME/FBNeo leen el `.zip` directamente). El problema es
específico de plataformas que necesitan el archivo crudo (PS2, GameCube y
cualquier otra fuera de `arcade`/`mame`/`cps1-3`/`fbneo`/`neogeo`).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| INBOX-FIX-6 | `_do_apply` ahora llama a `extract_zip(target_path, delete_source=True)` tras cada rename exitoso a `.zip` — reutiliza el guard de `extract_zip` (arcade/MAME por carpeta destino, se auto-excluye). Causa raíz secundaria encontrada al testear con datos reales de PS2: el guard de `extract_zip` rechazaba **cualquier** ZIP con `.iso` dentro ("usa el conversor CHD"), que es exactamente el caso PS2 reportado — no hay pipeline de CHD para PS2/GameCube en la app (solo `.cue`/`.gdi` de PSX/Saturn/Dreamcast lo tienen), así que un `.iso` suelto sin `.cue`/`.gdi` compañero es un archivo reproducible por sí solo. Guard reducido a solo `.cue`/`.gdi` (sets multi-track reales) — un `.iso`/`.bin` sin ninguno de esos dos ya se extrae. 8 tests nuevos (`test_zip_extractor.py`, `test_organize_apply_zip_extract.py`), suite completa en verde salvo los 3 fallos preexistentes de ADB (dependen de que no haya dispositivo conectado) | `web/handlers/organize.py::_do_apply`, `converters/zip_extractor.py` (`extract_zip`, guard `_DISC_SET_EXTENSIONS`) | ✅ hecho 2026-08-30 |

---

### INBOX-ORPHAN-3 — Carpetas vacías con nombre de juego directamente en la raíz de la biblioteca (hallazgo usuario 2026-08-29)

Origen: el usuario encontró carpetas como `Legend of Zelda, The - Twilight
Princess (USA)` directamente en `E:\Carpetas anbernic\` (fuera de `gamecube\`),
vacías o con solo una subcarpeta `media\` residual, en vez de tener el juego
organizado dentro de su plataforma. Verificado: **~40 carpetas** de este tipo
en la biblioteca real, la mayoría creadas el 2026-08-13 22:10 (mismo incidente
de `INBOX-CFG-1`, ya archivado), pero **siguen apareciendo nuevas** — 3 el
2026-08-28 y **2 hoy mismo, 2026-08-29** (`Monster World IV`, `X-Men Legends II
- Rise of Apocalypse`, creadas justo después de la corrida real de re-match de
`MATCH-FIX-2` sobre toda la biblioteca) — no es solo un residuo histórico, el
mecanismo que las genera sigue activo.

Causa raíz confirmada leyendo el código: `_DISC_SUBFOLDER_PLATFORMS`
(`planner/operation_planner.py:15-24`) incluye `gamecube`, `ps2` y `wii` junto
a las plataformas que sí son sets multi-track (`psx`, `saturn`, `dreamcast`)
que necesitan una subcarpeta por juego (`psx/Juego/Juego.cue` + sus `.bin`).
GameCube/PS2/Wii casi siempre son una imagen única (`.iso`/`.rvz`/`.chd`) que
**no necesita ninguna subcarpeta** — al tratarlas igual, `build_plan()`
(`operation_planner.py:136-142`) calcula el destino como
`source.parent.parent / folder_name / new_filename` cuando el archivo ya vive
en una carpeta mal ubicada (ni bajo el nombre de la plataforma ni ya en
subcarpeta), lo que **preserva y reproduce la ubicación equivocada** en vez de
corregirla a `platform/Juego.ext` plano. Y como ningún código de renombrado
(`rename_rom_with_saves`, `move_disc_set_to_subfolder`) borra el directorio de
origen tras dejarlo vacío (comportamiento normal de mover un archivo, no un
bug en sí), cada vez que un juego mal ubicado se corrige a mano o se vuelve a
tocar (re-match, re-organize) la carpeta vieja se queda huérfana para siempre
en la raíz.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| INBOX-ORPHAN-3 | Quitar `gamecube`/`ps2` de `_DISC_SUBFOLDER_PLATFORMS` (Wii confirmado que sí necesita subcarpeta — mezcla real de Virtual Console + dumps nativos multi-archivo, se deja igual que psx/saturn/dreamcast). Causa raíz real: ningún código de rename limpiaba la carpeta origen tras dejarla vacía — se añadió `_cleanup_empty_source_dir()` en `file_renamer.py`, compartida por `rename_rom_with_saves`/`move_disc_set_to_subfolder`, con guard que solo actúa si origen y destino son hermanos dentro de la misma plataforma (nunca toca la carpeta raíz de una plataforma). Barrido one-off ejecutado sobre la biblioteca real: 63 carpetas vacías dentro de plataforma (`dreamcast` 7, `ps2` 2, `wii` 54) + 39 carpetas huérfanas en la **raíz** de la biblioteca (mismo bug, casos donde el juego ya vivía mal ubicado) + 2 carpetas con solo `media/` residual (artwork movido a `dreamcast/media/{images,wheels}/` antes de borrar, no descartado) — 104 carpetas eliminadas en total, 0 restantes. 8 tests nuevos (`test_operation_planner.py`, `test_file_renamer.py`), 1067 tests en verde (3 fallos preexistentes en `tests/web/test_retroarch_override_*`/`test_detect_android_ra_config_dir_endpoint.py` no relacionados — dependen de que NO haya un dispositivo ADB conectado, y la RG556 está conectada). | `planner/operation_planner.py:15-24`, `renamer/file_renamer.py` | ✅ hecho 2026-08-30 |
| INBOX-ORPHAN-4 | Confirmado leyendo el header RVZ (`iso_file_size` en offset 36, formato WIA/RVZ): las 4 parejas comparten el mismo tamaño de ISO original sin comprimir (1.459.978.240 B, tamaño estándar de disco GameCube) — mismo dump, la copia de la raíz solo está peor comprimida (nivel RVZ distinto, creada 2026-08-13 en el mismo incidente que INBOX-ORPHAN-3/CFG-1; la de `gamecube/` es de 2025-02-23). Comparación por RA descartada — ver hallazgo INBOX-RA-HASH-GAP, ningún `.rvz` de esta librería puede compararse por RA hoy. Backup de `library_pc.db` en `.rommgr/backup_inbox_orphan4_2026-08-30/` antes de tocar nada; borrados los 4 `.rvz` de la raíz + sus filas de BD (`cascade_delete_games_by_source_path`) + las 4 carpetas ya vacías. Copias de `gamecube/` verificadas intactas tras el borrado. | — | ✅ hecho 2026-08-30 |
| INBOX-RA-HASH-GAP | Hallazgo derivado de INBOX-ORPHAN-4: `games.md5` (`hashing/hash_calculator.py:41`, `hashlib.md5()` sobre los bytes crudos del archivo) es un hash de **archivo completo**, pero el hash que usa RetroAchievements para GameCube/Wii (y cualquier formato de disco comprimido: RVZ, CHD) se calcula sobre datos específicos extraídos del **disco descomprimido** (boot.bin/apploader/dol vía `rc_hash`), no sobre el contenedor comprimido. Verificado contra `ra_cache/ra_hashes_16.json` (236 juegos, 332 hashes únicos): ninguno de los 8 md5 de las 4 parejas de INBOX-ORPHAN-4 aparece en la caché — ni la copia "buena" ni la "mala". Consecuencia real: `ra_duplicates_service.py` (`get_ra_achievements`, `apply_ra_conflicts`, `filter_duplicate_winners`) siempre devuelve -1 (sin RA) para cualquier `.rvz`/`.chd` de disco, aunque el juego sí tenga logros en RA — la comparación por RA solo funciona hoy para ROMs de cartucho sin comprimir. Implementar el hash real de RA para discos requeriría parsear el filesystem GameCube/Wii (o el `.chd`) para extraer las regiones exactas que hashea `rc_hash` — feature nueva, no un fix puntual. | `hashing/hash_calculator.py`, `services/ra_duplicates_service.py` (`get_ra_achievements`) | 🔴 pendiente, sin implementar (investigado 2026-08-30) |
| INBOX-ORPHAN-5 | 9 carpetas sueltas en la raíz con nombre de plataforma en formato *display* de ES-DE (`Master System`, `Atari 2600`, `Famicom Disk System`, `Game Boy`, `Game Boy Advance`, `Game Boy Color`, `Game Gear`, `NGC`, `Nintendo DS`) en vez del slug real (`mastersystem`, `atari2600`, etc.) — cada una con un `media/{images,wheels}/` propio, aparentemente duplicado del `media/` de la carpeta de plataforma real. Sin investigar aún: no se sabe si son artwork huérfano seguro de descartar o si tienen archivos que la carpeta real no tiene. Mismo patrón que INBOX-ORPHAN-3 pero de otro origen (no es `operation_planner`, probablemente un scraper o `create-library-structure` viejo usando nombres display) — investigar antes de tocar. | — | 🔴 pendiente, sin investigar |

---

## Pilar 3 — Sync de saves PC ↔ Anbernic — → #204

Jugar en cualquiera de los dos lados y que la partida aparezca sola en el
otro, sin miedo a sobrescribir — el valor diferencial real del proyecto.

### ANDROID-SYNC — App Android nativa de sync de saves (diseño 2026-08-18)

Petición del usuario: sync de saves lo más automático posible, sin depender
de que el PC esté encendido. Decisión: app Android nativa instalada en la
propia Anbernic que sincroniza directamente con Dropbox (sustituye al script
Termux+rclone de `docs/sync/Guia-Termux-Anbernic.md`, que solo auto-corre al
arrancar). Vive en `android/` (carpeta nueva en este mismo repo), Kotlin,
Jetpack Compose, SDK oficial de Dropbox (OAuth PKCE, sin rclone embebido),
distribución APK sideload. Contrato de interoperabilidad con
`src/rom_manager/sync/` (paths remotos, semántica `client_modified`,
resolución de conflictos por mtime ±2s, extensiones save/state) diseñado y
verificado contra el código real antes de escribir nada — ver
`Tareas/Roadmap-Android-Sync.md` para el detalle completo. Permisos
`MANAGE_EXTERNAL_STORAGE` (API 30+) con fallback legacy storage (API < 30);
persistencia local en Room/SQLite. minSdk bajo (cubre otras consolas Android,
no solo la RG556).

**Alcance recortado (2026-08-18)**: la app es un complemento de la app PC, no
una reimplementación completa — lo que importa es poder gestionar desde la
consola el envío de saves a Dropbox. Se descartan el modo instantáneo
(`FileObserver`/foreground service, 9-11) y la fase de optimización/historial
(13-14): sync manual (8, ya en curso) + periódico cada 15 min (12) cubren el
caso de uso real sin la complejidad de un daemon en segundo plano.

| ID | Task | Fase | Esfuerzo | Estado |
|----|------|------|----------|--------|
| ANDROID-SYNC-1 | Scaffold Gradle Kotlin-DSL en `android/`, módulo `:app`, Compose, manifest con permisos placeholder, `MainActivity` vacía, `.gitignore` raíz, `android/README.md` | 0 — Scaffold | S | ✅ PR #226 — verificado con `./gradlew assembleDebug test` real (toolchain portable JDK17+SDK+Gradle 8.7 instalada fuera del repo, sin Android Studio) |
| ANDROID-SYNC-2 | Flujo de permisos de storage (rama API 30+ vs legacy) + `POST_NOTIFICATIONS` condicional a API 33+ | 1 — Local | S | ✅ PR #227 — `StoragePermissionPolicy` (puro, 4 tests JVM) + `StoragePermissionManager` + pantalla de permisos en `MainActivity` |
| ANDROID-SYNC-3 | `SaveExtensions` + `RemoteRouter` (precedencia state-antes-que-save) + `LocalFileScanner` (recorrido recursivo) | 1 — Local | S | ✅ PR #228 — 12 tests JVM nuevos, extensiones idénticas a `config.py:544-576` |
| ANDROID-SYNC-4 | Pantalla "Escaneo": conteo de archivos bajo saves/states, sin red | 1 — Local | XS | ✅ PR #229 — `ScanScreen` + `formatBytes` (Locale.ROOT, 3 tests). Primer intento de build falló de verdad (import faltante), corregido tras compilar |
| ANDROID-SYNC-5 | OAuth PKCE de Dropbox, `DropboxAuthManager`, credenciales en `EncryptedSharedPreferences` | 2 — Dropbox core | M | ✅ PR #231 |
| ANDROID-SYNC-6 | `DropboxTransport`: listado recursivo con `client_modified`, upload/download coherentes con mtime | 2 — Dropbox core | M | ✅ PR #232 |
| ANDROID-SYNC-7 | Puerto de `ConflictResolver` (tolerancia 2s, newest-wins, backup de conflicto) + `SyncEngine` + watermark Room `(relative, remote_root)` | 2 — Dropbox core | M | ✅ PR #233 |
| ANDROID-SYNC-8 | Pantalla de Ajustes: conectar/desconectar, paths remotos con auto-recorte de prefijo rclone, botón "Sincronizar ahora" | 2 — Dropbox core | S | ✅ PR #234 |
| ANDROID-SYNC-9 | ~~`SaveFileObserverManager`: `FileObserver` multi-path, debounce~~ | 3 — Instantáneo | M | ❌ descartado (2026-08-18) — la app es complemento del PC, no un daemon en segundo plano; sync manual + periódico (12) cubre el caso de uso real |
| ANDROID-SYNC-10 | ~~`SyncForegroundService` + notificación~~ | 3 — Instantáneo | S | ❌ descartado — depende de 9 |
| ANDROID-SYNC-11 | ~~`BootRestartReceiver`~~ | 3 — Instantáneo | XS | ❌ descartado — depende de 9/10 |
| ANDROID-SYNC-12 | `SyncWorker` (`CoroutineWorker`, 15 min mínimo, `NetworkType.CONNECTED`) + interruptor en Ajustes | 4 — Periódico | S | ✅ rama `feature/android-sync-12-periodic-sync` (PR #237) — `SyncOrchestrator` (nuevo, dependencias de `SyncEngine`/Dropbox/settings construidas desde un `Context`, punto compartido entre "Sincronizar ahora" y `SyncWorker`), `SyncWorker`/`PeriodicSyncScheduler`, `autoSyncEnabled` en `SettingsRepository`, interruptor en `SettingsScreen` (con la fase instantánea descartada, el "selector de modo" se simplifica a on/off). Permisos muertos de 9/10/11 (`FOREGROUND_SERVICE*`, `RECEIVE_BOOT_COMPLETED`) retirados del manifest. Verificado con `./gradlew test` y `./gradlew assembleDebug` reales (toolchain portable instalado en esta máquina, ver `Tareas/Roadmap-Android-Sync.md` §8) — ambos en verde, incluye 2 tests JVM nuevos de `SyncResult.plus()`. Falta el flujo manual en emulador/dispositivo (checklist: `Tareas/Validacion-ANDROID-SYNC-12.md`) |
| ANDROID-SYNC-13 | ~~`DeltaCache` (SHA1 skip-si-no-cambió)~~ | 5 — Optimización | S | ❌ descartado — optimización prematura sin datos de uso real que la justifiquen |
| ANDROID-SYNC-14 | ~~Pantalla de estado/historial~~ | 5 — Optimización | S | ❌ descartado — fuera del alcance mínimo (gestionar el envío de saves a Dropbox desde la consola); reconsiderar si hace falta depurar fallos de sync en el futuro |
| ANDROID-SYNC-15 | Checklist RG556: instalar, permisos, anidado real por-core, round-trip cruzado con `rommgr sync-saves`, reboot, batería | 6 — Validación hardware | M | ⬜ bloqueado — sin RG556 a mano |
| ANDROID-SYNC-FIX-1 | **Bug: el primer sync de una cuenta/carpeta Dropbox nueva fallaba siempre** — `DropboxTransport.listFolderRecursive()` propagaba `ListFolderErrorException` (`path/not_found`) como error fatal cuando la carpeta remota simplemente no existe todavía (cuenta nueva, nunca se subió nada ahí); eso es un listado vacío legítimo, no un fallo. Sin este fix ningún usuario Android nuevo podía completar su primer sync. Hallado validando Dropbox sync a mano contra una cuenta real (AVD `retrovault_test`, API 34) | `android/app/src/main/java/com/retrovault/android/sync/DropboxTransport.kt` | ✅ captura `ListFolderErrorException` y devuelve lista vacía si `errorValue.isPath && errorValue.pathValue.isNotFound`; cualquier otro error se relanza igual que antes. Verificado contra la cuenta real: antes "Errores: 2", después "Errores: 0" |

---

### EMULATOR-COMPAT — Save compatibility PC ↔ Android

Verify that synced saves from PC actually load on Android and vice versa, for each emulator pair.

| ID | Task | Notes |
|----|------|-------|
| EMULATOR-COMPAT-1 | Create compatibility matrix — PC emulator, Android emulator, save format, save path per platform | `docs/emulator-compat.md` ✅ |
| EMULATOR-COMPAT-2 | Test PS1 round-trip: DuckStation PC → sync → DuckStation Android → load | Hardware test with RG556 |
| EMULATOR-COMPAT-3 | Test PS2 round-trip: PCSX2 PC → sync → AetherSX2/NetherSX2 Android → load | Hardware test |
| EMULATOR-COMPAT-4 | Test remaining platforms (GBA, SNES, GBC, NDS…) and document any format mismatches | Update matrix per result |
| EMULATOR-COMPAT-6 | **Syncthing corría en paralelo sobre `RetroArch/saves` y `RetroArch/states` en la RG556** — hallazgo 2026-08-25 (`saves/.stfolder`, `states/.stfolder`, anidados en `saves/Beetle PSX/` y `states/LRPS2/`; tombstone `saves/.stfolder.removed-20250708-230136/DO_NOT_DELETE.txt` de un intento previo de desactivarlo sin completar). Dos motores de sync tocando los mismos archivos de save = riesgo de conflicto/corrupción. **Mitigado en caliente**: `com.github.catfriend1.syncthingandroid` parado (`am force-stop`) y deshabilitado (`pm disable-user`, reversible con `pm enable-user`) por ADB — cero archivos borrados. Pendiente: decidir si se reactiva alguna vez y para qué (no se investigó su propósito original). Hay además un tercer sync app instalado (`dk.tacit.android.foldersync.lite`, FolderSync Lite) — parado y deshabilitado también por ADB (misma operación reversible, cero borrados); propósito original sin investigar, posible origen de la carpeta huérfana `ra-saves` (ver ROADMAP-IDEAS / limpieza 2026-08-25) | Hardware | S | ✅ ambos apps mitigados |
| SAVES-FRAGMENT-1 | **Saves del mismo juego fragmentados entre esquemas por-core y por-plataforma dentro de RetroArch** — `sort_savefiles_by_content_enable` se ha activado/desactivado en distintos momentos en la RG556; conviven `saves/Snes9x 2010/Earthbound (1).srm`, `saves/bsnes2014/...`, `saves/Snes9x/...`, `saves/Snes9x 2005 Plus/...` Y `saves/snes/Earthbound.srm` — mismo juego, hasta 4-5 copias, sin saber cuál es la más reciente sin comparar fechas. NO fusionar a ciegas: puede pisar progreso más reciente (regla del proyecto — backup antes de mover). Alcance: comparar mtime/hash de cada grupo, consolidar en el esquema por-plataforma (el único que además es sincronizable de forma predecible), backup automático de lo descartado | Hardware + diseño propio | M | 🟡 **inventario y diagnóstico hechos 2026-08-25** → `Tareas/Informe-SAVES-FRAGMENT-1.md` (+ datos crudos `Tareas/SAVES-FRAGMENT-1-inventario-rg556.tsv`, 424 archivos con mtime/tamaño/md5). Nada movido ni borrado. Riesgo real acotado a **8 grupos divergentes** (Earthbound ×7 copias/3 versiones, `Mcd001.ps2`, 5 juegos GBA); 42 grupos idénticos + 3 todo-vacío + 2 con ganador obvio son dedupe seguro (~190 MB en `saves/nds/states/`). Tres hallazgos que invalidan el plan original: (a) la copia **más reciente de Earthbound está en el esquema por-core** (`saves/Snes9x/`), consolidar hacia `saves/snes/` a ciegas pisa progreso; (b) hay **dos ejes más** de fragmentación — extensión distinta por core (`.srm` VBA Next 139264 vs `.sav` mGBA 32/64/131072, md5 nunca comparable entre cores) y mismo juego con dos nombres de ROM; (c) 37 archivos son **plantillas en blanco `0xFF`** con mtime posterior al save real — un consolidador que solo mire fecha elige la copia vacía en 3 de 5 casos. `states/` NO está fragmentado. Pendiente: decisión del usuario sobre los 8 divergentes antes de mover nada |
| SAVES-FRAGMENT-2 | **Memcards PS2 duplicadas entre el core LRPS2 de RetroArch y AetherSX2 standalone** — `RetroArch/saves/LRPS2/Mcd00{1,2}.ps2`, `RetroArch/saves/ps2/Mcd00{1,2}.ps2` y `RetroArch/emulator_saves/xyz.aethersx2.android/saves/Mcd00{1,2}.ps2` — hasta 3 copias por memcard. AetherSX2 y LRPS2 comparten motor (PCSX2), así que el formato de memcard podría ser compatible entre ambos — verificar antes de decidir si unificar ruta o solo consolidar backups | Hardware + investigación | S | ⬜ documentado 2026-08-25 |
| SAVES-FRAGMENT-3 | **NVRAM de arcade repartido en 5 ubicaciones en la misma RG556** — `RetroArch/mame/*.nv` (junto a ROMs), `RetroArch/saves/mame/*.nv`, `RetroArch/saves/Unknown/*.nv` (~40 archivos que RetroArch no logró emparejar con ninguna plataforma — revisar también como síntoma de matching roto), `RetroArch/saves/mame2003/{nvram,hi,cfg}/`, `RetroArch/saves/cps1/`+`cps2/`. Ninguna se sincroniza hoy — ver EMULATOR-COMPAT-5 | Hardware + diseño propio | M | ⬜ documentado 2026-08-25 |
| SAVES-FRAGMENT-4 | **GameCube/Wii en 3 ubicaciones**: core Dolphin de RetroArch (`saves/gamecube/{EUR,USA}`, `saves/User/{GC,Wii}` — un perfil Dolphin completo anidado dentro de la carpeta de RetroArch) vs. standalone mmjr-revamp (`GC/{EUR,JAP,USA}`, `Wii/title/`) | Hardware + diseño propio | S | ⬜ documentado 2026-08-25 |
| SAVES-FRAGMENT-5 | **Cada standalone usa su propio path público/privado, ninguno coincide entre sí ni con RetroArch** — DuckStation (`/storage/emulated/0/duckstation/` + `Android/data/com.github.stenzek.duckstation/files/`), AetherSX2 (`Android/data/xyz.aethersx2.android/files/`), Redream (`Android/data/io.recompiled.redream/files/`), DraStic (`/storage/emulated/0/DraStic/backup/`, `savestates/`). Una vez resuelto DEVPROFILE-0 en su alcance reducido, decidir si el sync de Retro Vault amplía sus raíces vigiladas a estas carpetas o si se le pide al usuario redirigir cada app (vía su propio menú de ajustes) a una ruta pública común | Hardware + diseño propio | M | ⬜ documentado 2026-08-25, depende de DEVPROFILE-1 (mapa core→plataforma como base) |
| SAVES-FRAGMENT-6 | **Emulador canónico por plataforma + esquema de saves congelado** — mitad preventiva de SAVES-FRAGMENT-1: sin esto, cualquier consolidación se vuelve a fragmentar. Política completa en `docs/emulador-canonico-rg556.md` (tabla de 15 plataformas con emulador ganador, ruta de save y qué se jubila; decidida con `dumpsys usagestats` real del dispositivo, no por suposición). Hallazgos nuevos: (a) **hay DOS RetroArch instalados** (`com.retroarch` 19 h vs `com.retroarch.aarch64` 2 min, ambos arm64, cfg y cores separados) — segunda fuente de fragmentación, Daijishō debe apuntar al primero; (b) **PSX se juega en DuckStation standalone (68 h, 221 lanzamientos)** pero hay memcards del core Beetle PSX en `saves/psx/` — fragmentación PSX invisible al informe porque cae fuera de `saves/`; (c) **melonDS escribe junto a las ROMs en `RetroArch/nds/`** — sexta ubicación, mismo patrón que el `.nv` de EMULATOR-COMPAT-5; (d) hay **tres** juegos de memcards PS2, no dos (`saves/ps2/`, `saves/LRPS2/`, `emulator_saves/xyz.aethersx2.android/`). Ajustes RetroArch a congelar: `sort_savefiles_enable=false`, `sort_savefiles_by_content_enable=true`, `savefiles_in_content_dir_enable=false`, `savestates_in_content_dir_enable=false`; los de savestates NO se tocan (`states/` no está fragmentado, migrar 68 archivos a cambio de nada). ⚠️ **No automatizable por ADB**: `retroarch.cfg` y la config de Daijishō viven en `/data/data/`, sin root y sin copia pública (verificado con `find`) — hay que hacerlo en los menús. Vía alternativa documentada: Daijishō importa platform JSON con `playerList`/`amStartArguments`, se podrían generar los 15 archivos si el usuario exporta uno de muestra. **Ausencia de root confirmada** 2026-08-25 (`su` no existe, sin Magisk/KernelSU, `/data/data` = `Permission denied`, shell = `uid=2000`). **Requisito añadido por el usuario: RetroAchievements en todas las plataformas** — manda sobre el resto de criterios y cambia 4 filas: PS2 pasa de AetherSX2 a **ARMSX2** (RA soporta PCSX2/ARMSX2/XBSX2, AetherSX2 y NetherSX2 no están en la lista; hay que instalarlo); **PPSSPP 1.11.3 es de 2021 y no tiene RA** (actualizar); **GameCube pasa al standalone Dolphin 2606a** porque RA no existe en el core `dolphin-emu` — y eso implica renunciar al sync en esa plataforma (saves en `Android/data/`, sin root); **3DS queda fuera del criterio** (RetroAchievements no soporta 3DS como consola). DraStic, Redream y MMJR quedan descartados también por no tener RA. Nota: el modo hardcore de RA desactiva los save states, lo que refuerza dar prioridad al save de batería sobre `states/` | Hardware + diseño propio | S | 🟡 política documentada 2026-08-25 (v2 con RA) — pendiente aplicarla en el dispositivo (manual, sin root no hay alternativa) |
| SAVES-FRAGMENT-7 | **Los nombres de los saves ya no coinciden con los de las ROMs** — hallazgo 2026-08-25, bloquea toda consolidación automática. **69 saves** en carpetas por-plataforma no tienen ninguna ROM con ese nombre. Caso testigo: la ROM es `/storage/521D-04EA/snes/EarthBound (USA).sfc` (No-Intro) y los tres saves se llaman `Earthbound.srm`, `Earthbound (1).srm`, `Earthbound (World) (Virtual Console) (New 3DS).srm` — RetroArch busca `<nombre-ROM>.srm`, así que **ninguno se carga hoy**, ni antes ni después de tocar la config. No es fragmentación de carpetas: es un renombrado canónico hecho sin arrastrar los saves, justo lo que `rename_rom_with_saves()` (`renamer/file_renamer.py`) existe para evitar. Investigar si el renombrado se hizo con la herramienta (y entonces hay un bug o una ruta que no pasa por `rename_rom_with_saves`) o a mano fuera de ella. Hasta arreglarlo, consolidar carpetas no recupera esas partidas | Hardware + fix | M | ⬜ documentado 2026-08-25 |
| SAVES-FRAGMENT-8 | **Hay CINCO árboles de saves, no dos** — el informe SAVES-FRAGMENT-1 solo inventarió `RetroArch/saves` y `RetroArch/states`. Faltan: (1) **la microSD `/storage/521D-04EA/`, donde viven realmente las ROMs** (611 SNES, 1376 NES, 1115 PSX, 395 GBA, 378 NDS…) y que tiene **su propio `saves/` con 459 archivos**; (2) saves sueltos junto a las ROMs en la SD — 41 en `gba/`, 62 en `nds/`, 6 en `psx/`, 3 en `snes/`, 3 en `dreamcast/`; (3) `RetroArch/<plataforma>/` en memoria interna, restos de cuando `savefile_directory` apuntaba a `RetroArch/` en vez de `RetroArch/saves`. Rehacer el inventario cubriendo las cinco raíces antes de consolidar. Además: `/storage/521D-04EA/snes/_descartados/_descartados/…` anidado 7 niveles — posible bug de recursión en la herramienta de organización, revisar aparte | Hardware + fix | M | ⬜ documentado 2026-08-25 |
| SAVE-CONSOLIDATOR-1 | **Escáner de fragmentación de saves** — convierte la metodología manual de SAVES-FRAGMENT-1 en módulo reutilizable: agrupa por stem normalizado + extensión-por-familia-de-core (§2 del informe), detecta plantilla en blanco por relleno uniforme y no solo por hash repetido (§5, evita el falso positivo de Metal Gear Solid), reporta grupos divergentes sin tocarlos — mismo principio que Duplicados de ROM (nunca auto-resuelve, solo informa) | `sync/save_consolidator.py` (`scan_save_groups`), 11 tests en `tests/test_save_consolidator.py` | ✅ módulo hecho y validado 2026-08-27 contra el TSV real de la RG556 (`SAVES-FRAGMENT-1-inventario-rg556.tsv`, vía script de scratchpad, no commiteado): con una lista de extensiones de save-de-batería curada reproduce **exactamente** los 8 grupos divergentes del informe (Earthbound 7 copias, `Mcd001.ps2`, 5 GBA — mismos md5). **Hallazgo real**: usar el agregado global `config.save_extensions` en vez de una lista curada añade ~9 falsos positivos porque mezcla savestate-como-archivo (`.ml1`, `.hi`, `.nv`) con save de batería real bajo el mismo stem — documentado como contrato de la función, no arreglado con más código (ver docstring de `scan_save_groups`). **Job web hecho 2026-08-27**: `GET /api/save-fragmentation` (`web/handlers/sync.py` + `web/builders/save_consolidator.py`, escanea `library_root/saves` y `/states` como raíces separadas) + sección "Fragmentación de saves" en la pestaña Sync (`tab-sync.html`, botón "Analizar" → `doSaveFragmentation()` en `sync.js`). Probado de extremo a extremo contra la biblioteca real montada en `E:\Carpetas anbernic` (servidor real en `:7799`, `curl` al endpoint): 2,76 s, resultado correcto (`9 divergentes`, `29 solo-plantilla`, `32 idénticos`), HTML servido con el botón y el contenedor de resultado presentes. **Verificado en navegador real 2026-08-29** (Chrome vía extensión, servidor real `:7777`): clic real en "Analizar" en la pestaña Cloud → mismos contadores (`9 divergentes · 29 solo-plantilla · 32 idénticos`) y tabla con los grupos esperados (Donkey Kong - Jungle Climber, Castlevania - Dawn of Sorrow…) — ✅ listo para cerrar |
| SAVES-FRAGMENT-9 | **Progreso real de PS2 perdido en AetherSX2 — hallazgo 2026-08-29, en vivo en la RG556.** `dumpsys usagestats` confirma que el usuario sigue jugando en **AetherSX2** (sesión hoy 02:29-02:34, `appLaunchCount` alto histórico) y que **ARMSX2 nunca se ha abierto** (`idle=y`, sin `lastTimeUsed`) pese a estar instalado desde el 2026-08-25 — la migración de SAVES-FRAGMENT-6 no se aplicó de hecho. A las 02:29:41 AetherSX2 lanzó un `PickActivity` (SAF) justo antes de jugar. La memcard que hoy está activa en `/storage/521D-04EA/saves/memcards/Mcd001.ps2` (mtime 2026-08-27 13:35:58, junto a `Mcd002.ps2` y un tercer archivo `1.ps2` con el mismo mtime exacto → copia en bloque, no partidas jugadas) **no contiene ningún save de juego** (`grep -a -o -E "B[A-Z]?[SXE]LE?S-[0-9]{5}"` → 0 resultados), mientras que las dos copias ya conocidas por SAVES-FRAGMENT-2 (`RetroArch/saves/ps2/Mcd001.ps2` y `RetroArch/saves/LRPS2/Mcd001.ps2`) sí tienen 6 juegos cada una (BESLES-50386/51950/52445/52822/53777/54915). Esa misma carpeta `/storage/521D-04EA/saves/` replica 1:1 la estructura interna de AetherSX2 (`bios/`, `covers/`, `gamesettings/`, `sstates/`) y tiene al lado `duckstation_backup_2026-08-27.zip` (129 MB, 13:20) — es un **backup manual hecho el 27**, y ese backup ya capturó la memcard vacía. La memcard privada real de AetherSX2 (`Android/data/xyz.aethersx2.android/files/memcards/Mcd001.ps2`) tiene mtime 2026-08-13 pero su contenido es ilegible por ADB (scoped storage, `Permission denied` en `md5sum`/`grep`, igual que el resto de `/data/data` — no es root). No se ha tocado ni movido nada. **Hipótesis más probable, sin confirmar dentro de la app**: el progreso se perdió en AetherSX2 alrededor del 2026-08-13 (coincide con el mtime), no hoy — probablemente por crear/formatear una memcard nueva desde el menú de AetherSX2 sobre las mismas ranuras Mcd001/Mcd002, no por reinstalación (`versionName=v1.5-4248`, sin actualizar desde 2025-05-30). Pendiente: (1) abrir AetherSX2 y comprobar en Settings → Memory Cards qué carpeta usa hoy y si hay copias `.bak`/exportadas dentro de la app; (2) si se confirma que el progreso ya no existe en ningún sitio accesible, importar manualmente `RetroArch/saves/ps2/Mcd001.ps2` (la copia más reciente conocida, 2025-11-21) a AetherSX2 — backup previo obligatorio, memcard multi-juego = nunca automático (regla 7 de `docs/emulador-canonico-rg556.md` §5) | Hardware + investigación | S | ⬜ documentado 2026-08-29, sin fix aplicado |
| SAVES-FRAGMENT-9b | **Comprobado el mismo día que el caso de PS2 es aislado, no sistémico.** Mismo método (contenido real + `dumpsys usagestats`) aplicado a los otros 4 standalone: **DuckStation** (PSX) ok — 27 memcards en su sandbox privado, fechas repartidas todo el año hasta 2026-08-24, sin patrón de reseteo (pendiente real es el ya conocido de SAVES-FRAGMENT-5: nunca se redirigió a ruta pública). **melonDS** (NDS) ok — la sesión de hoy duró 19 s (abrir/cerrar, no hubo partida), saves reales más recientes de octubre 2025, normal. **Dolphin** (GC/Wii) — `files/GC/` y `files/Wii/` están completamente vacías, pero coincide con el uso total ya documentado (~4 min): nunca hubo progreso que perder, no es un caso de pérdida. **PPSSPP** (PSP) — señal débil, solo una carpeta de save (`ULES009150`, abril 2025) y uso histórico muy bajo; no hay suficiente para concluir pérdida ni descartarla, queda abierto si el usuario juega más PSP. Arcade NVRAM (`.nv`) también revisado: tamaños y fechas normales | Hardware + investigación | XS | ✅ verificado 2026-08-29, sin acción necesaria salvo PPSSPP (bajo uso, inconcluso) |
| EMULATOR-COMPAT-5 | **El progreso de arcade nunca se sincroniza** — confirmado en hardware real 2026-08-25 (RG556 conectada por cable). Las extensiones sí están cubiertas (`.nv` en `config.py:562` y `SaveExtensions.kt:16`), pero el problema es la **carpeta**: en esta RG556 el `.nv` (NVRAM/dipswitches) no vive en `saves/`, `states/` ni `system/<core>/` — vive **directamente en `RetroArch/<carpeta-de-plataforma>/`, junto a las propias ROMs** (verificado: 24 archivos en `RetroArch/mame/*.nv` — TMNT2, Simpsons, X-Men, Vendetta…; también `cps1/punisher.nv`, `cps1/wofch.nv`, `cps2/1944.nv` — patrón sistemático, no un caso aislado). El scanner de sync solo recorre `saves_path`/`states_path` (`config.py`) / `RetroArchPaths.kt:11-12` — nunca las carpetas de ROMs. Fix: el scan de arcade tiene que recorrer las carpetas de plataforma arcade completas (mame, fbneo, cps1, cps2, cps3…) filtrando por extensión, no asumir una raíz `saves/states` separada de las ROMs | Hardware + fix | S | 🟡 fix implementado 2026-08-29 en el lado Android (único que corría sin este fix — el sync PC↔consola por cable ya recorre árboles completos por extensión, sin este hueco): `RetroArchPaths.ARCADE_FOLDERS` (`android/.../sync/RetroArchPaths.kt`, mame/cps1/cps2/cps3/fbneo/arcade — mismas claves "Arcade" que `platforms.toml`) + `SyncOrchestrator.runFullSync` ahora sincroniza cada carpeta arcade contra `"$savesRemote/$platform"` (subcarpeta propia en Dropbox, sin colisión con `saves/`); `LocalFileScanner` ya filtraba por `SaveExtensions.isTracked`, así que las ROMs de esas carpetas nunca se suben — sin cambios ahí. Test nuevo `RetroArchPathsTest.kt`. **Sin verificar**: no hay JDK en esta sesión para compilar/ejecutar los tests de Android, y el fix no se ha probado en la RG556 real (haría falta rebuild + instalar APK) |

---

### CABLE-UX — Auditoría de Cable Sync: simplificar la experiencia (2026-07-13)

Auditoría del flujo completo de Cable Sync (`tab-cable.html`, `sync.js`,
`handlers/sync_cable.py`, `cable_sync_daemon.py`). El caso de uso del pilar 3
("conecto la consola y los saves aparecen solos") exige hoy ~10 decisiones:
qué sincronizar (4 checkboxes), dirección (3 radios), modo SD/ADB, 2-4 campos
de ruta, detección manual de dispositivo y 4 checkboxes de opciones — con un
bloque de instrucciones de ~80 líneas encima del formulario. Detalle, archivos
y criterios de "hecho" en `Tareas/Roadmap-Cable-UX.md`. Relacionado:
VAL-FIX-5/6 (ya registrados, no se duplican aquí). Orden: 1 es seguridad,
2-3 son el grueso de la simplificación, el resto elimina fricción menor.

| ID | Task | Pilar | Esfuerzo | Estado |
|----|------|-------|----------|--------|
| CABLE-UX-1 | **El pre-flight de reloj (AUD-1) solo existe en el frontend** — `doCableSync` hace el check quick antes de "newest" (`sync.js:863-871`), pero el daemon de auto-sync dispara sync "newest" por mtime en cada conexión SIN comprobar skew (`cable_sync_daemon.py:_auto_sync_loop` — cero referencias a skew/`device_epoch`), que es justo el escenario que AUD-1 quería proteger. Fix raíz: mover el check al backend — al inicio del job `cable_sync` con `direction=newest` (manual y auto); si `skew_exceeded`, abortar con error claro en vez de sincronizar. De paso se elimina el `confirm()` del frontend | Sync/Seguridad | S | ✅ (feature/cable-ux) |
| CABLE-UX-2 | **Un botón "Sincronizar saves ahora" como acción primaria** — la acción del día a día está enterrada al final del formulario. Nota: `promptSyncNow()` no era plumbing reutilizable — posteaba `/api/cable-sync` con body vacío, que siempre falla la validación de `pc_path` (bug latente sin usuarios afectados porque el resultado se tragaba en silencio). Fix real: nuevo `doQuickSync()` que arma el body con `library_root`/`anbernic_root` de config + dirección de la tarjeta auto-sync + primer dispositivo ADB listo, reutilizando `/api/cable-sync` (mismo motor, no uno nuevo); botón primario arriba de la pestaña; el formulario manual completo pasa a un `<details>` "Sincronización avanzada" | UX | M | ✅ (feature/cable-ux) |
| CABLE-UX-3 | **El modo SD/ADB se pregunta al usuario cuando la app ya lo sabe** — hay que elegir el radio `cable-ab-mode` a mano (`tab-cable.html:198-210`), pero el daemon ADB ya sondea dispositivos cada 10 s y el daemon SD ya detecta la unidad montada. Fix: al cargar la pestaña, preseleccionar ADB si `/api/adb-devices` devuelve un device ready (y autorellenar el select), o SD si `anbernic_root` existe como ruta; el radio queda como override manual. Resuelve de rebote VAL-FIX-6 (no se validaría la ruta SD en modo ADB) | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-4 | **El select "Conflictos" de la tarjeta auto-sync no hace nada en cable sync** — `conflict_policy` solo lo consume `save_syncer.py:270` (sync cloud); el daemon de cable ignora ese valor y resuelve siempre por mtime. Además "Dirección: Más reciente gana" y "Conflictos: Más reciente gana" lado a lado (`tab-cable.html:23-39`) es una duplicación que confunde. Fix: quitar el select de la tarjeta de cable (su sitio es la config de sync cloud). Verificado en vivo: era el único control de UI para `conflict_policy` en toda la app — se movió (no se borró) a `tab-sync.html`, nuevo `saveConflictPolicy()` vía `/api/config` (ya en el `allowed` set de `handlers/config.py:261`) | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-5 | **Campos duplicados para la misma ruta** — dos inputs "Ruta del PC" (`cable-pc-path` y `cable-adb-pc-path`, rellenados idénticos en `loadCableSync`, `sync.js:792-793`) y dos "Ruta Android" (tarjeta auto-sync `auto-sync-android-path` y sección ADB `cable-android-path`, defaults distintos). Fix: un solo input de PC fuera del bloque de modo; un solo input Android compartido con la config de auto-sync | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-6 | **Defaults contradictorios** — dirección por defecto "PC → Consola: *Sobrescribe los archivos de la consola*" (`tab-cable.html:170-173`) con "Modo seguro (*no sobreescribir*)" marcado (`:288-291`) → el resultado típico es "0 copiados / N omitidos" sin explicación. Y el checkbox dry-run empieza desmarcado pero su aviso "se copiarán realmente" empieza oculto (`:282,298` — solo aparece tras tocar el checkbox). Fix: default `direction=newest` (el caso saves), y sincronizar el aviso de dry-run con el estado inicial | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-7 | **Las instrucciones A/B/C/D ocupan la zona noble en cada visita** — ~80 líneas (`tab-cable.html:52-136`) con la opción A expandida siempre, encima del formulario. Fix: colapsar todo en un único `<details>` "¿Cómo conecto la consola?"; abrirlo solo si nunca hubo un sync exitoso (dato ya disponible en `/api/auto-sync-status.last_sync_at`) | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-8 | **Sync Doctor exige ritual previo** — `runSyncDoctor` falla con "Activa el Modo ADB y detecta un dispositivo primero" (`sync.js:759-762`) si no se pobló el select a mano. Fix: si no hay serial, llamar `/api/adb-devices` y usar el primer device ready antes de rendirse | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-9 | **Tres implementaciones divergentes del bucle de copia** — manual (`handlers/sync_cable.py:_do_cable_sync`), ADB auto (`cable_sync_daemon.py:_run_auto_sync`) y SD auto (`_run_sd_auto_sync`) reimplementan el walk+compare+copy con garantías distintas. Causa raíz de CABLE-UX-1. Dividido en subtareas (ver `Roadmap-Cable-UX.md`) | Sync | M-L | ✅ (feature/cable-ux) |
| CABLE-UX-9a | **SD auto sobrescribe sin backup** en `pc_to_anbernic`/`anbernic_to_pc` (`cable_sync_daemon.py:409-429`), rozando "ante duda, no sobreescribir". Fix: backup a `.rommgr/cable_sync_backups/<fecha>/` antes de overwrite | Sync | S | ✅ (feature/cable-ux) |
| CABLE-UX-9b | Extraer motor compartido de filesystem (walk, filtro, compare por mtime, copy con verify/safe/log) en `sync/cable_engine.py`, generalizando la rama no-ADB de `_do_cable_sync` sin cambiar comportamiento | Sync | S | ✅ (feature/cable-ux) |
| CABLE-UX-9c | Migrar `_run_sd_auto_sync` al motor de 9b | Sync | S | ✅ (feature/cable-ux) |
| CABLE-UX-9d | Migrar rama filesystem de `_do_cable_sync` al motor de 9b | Sync | S | ✅ (feature/cable-ux) |
| CABLE-UX-9e | Unificar política ADB (verify MD5 solo-saves) entre manual (`_adb_copy_to_pc/device`) y daemon (`_run_auto_sync`) | Sync | S | ✅ (feature/cable-ux) |
| CABLE-UX-9f | Tests del motor compartido (`test_cable_engine.py`): safe_mode/verify/skew en un solo sitio | Sync | S | ✅ (feature/cable-ux) |
| CABLE-UX-10 | **Cuatro fuentes de verdad para las rutas** — cascada `ovPc \|\| cfg.library_root \|\| localStorage` en `loadCableSync` (`sync.js:787-796`) mezclando inputs de Overview, config y `localStorage` (`anbernic_path`, `cable_pc_path` — escritos en `doCableSync:878-879`). Fix: config (`library_root`/`anbernic_root`) como única fuente; eliminar el localStorage | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-11 | **CABLE-UX-10 huérfano `localStorage['anbernic_path']`** — quitó el único `setItem` (era en `doCableSync`), pero 6 sitios seguían leyéndolo como fallback cuando `ov-ab-path` está vacío (normal en cualquier sesión hasta que se visita Inicio, porque `loadOverview()` no corre en el arranque): `config.js:318,322` (`doBatchRun`, Herramientas — bloqueaba con alert aunque `anbernic_root` estuviera configurado), `duplicates.js:25` (`loadDuplicates`), `duplicates.js:358` (`setToolsContext`), `scan.js:129` (`quickScanAndroid`), `main.js:587` (`openHtmlReportAndroid`), `sync.js:98` (barra de contexto de Assets). Conecta con ASSETS-UX-1 (`Roadmap-Assets-UX.md`), que documentaba este mismo fallback como si funcionara. Fix: los 6 sitios ahora consultan `cfg.anbernic_root` (fetch a `/api/config`, ya disponible en todos salvo `main.js`/`scan.js` donde se añadió) antes de caer a `localStorage`/`(no configurado)` — mismo patrón que ya usaba `overview.js:403` correctamente. No se resucita el `setItem`: sigue la filosofía de CABLE-UX-10 (config como única fuente de verdad) | Sync/UX | S | ✅ (feature/cable-ux) |

---

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: CLOUD-UX-1..3 (wizard, auditoría 2026-07-12) y CLOUD-UX-1..12 (auditoría de la pestaña Cloud, 2026-07-13) — ambas secciones completas.

---

### ANBERNIC-UX — Auditoría de la pestaña Anbernic: UX/UI, lógica y seguridad (2026-07-13)

Auditoría de la pestaña Anbernic (`tab-anbernic.html`, `js/tabs/sync.js`,
`_banners.html`, `handlers/sync_cloud.py`, `handlers/system.py`, `web/lan.py`).
Hallazgo central: **dos generadores de script de setup que se contradicen en
la misma pantalla, uno de ellos sin endpoint (404)**; y la instalación por
defecto sirve el rclone.conf con tokens OAuth a toda la LAN sin PIN.
Detalle, archivos y criterios de "hecho" en `Tareas/Roadmap-Anbernic-UX.md`.
Relacionadas (no duplicar): CLOUD-UX-6 (panel TV roto), CLOUD-UX-7 (remote
hardcodeado en `/s`). Todo pilar 3.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| ANBERNIC-UX-1 | **Dos generadores de setup contradictorios** — el comando del paso 5 usa `/s` (`sync.js:402`, crea `~/sync-saves.sh`, bisync, remote hardcodeado = CLOUD-UX-7); el botón "Descargar .sh" y el panel de Settings usan `/api/anbernic-setup.sh` (`_build_anbernic_setup_sh`, `system.py:218`, crea `~/retrovault-sync.sh`, `rclone copy --update`, lee config); la caja "Después del setup" (`tab-anbernic.html:156`) documenta el script que el comando recomendado NO crea. Fix: un solo generador canónico en `/s` con lo bueno de system.py (config + copy --update); borrar el otro | Bug | M | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-2 | **"Descargar .sh" y panel Settings → 404** — `/api/anbernic-setup.sh` no está registrado en ningún handler (solo `openapi.json:4597`; el builder de `system.py:218` es código muerto). Afecta al botón del paso 5 (`sync.js:415`) y a todo el Android setup panel de Settings (QR+curl, `sync.js:238-253`). Fix (tras -1): apuntar todo a `/s` y evaluar eliminar el panel de Settings (superficie duplicada) | Bug | S | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-3 | **Seguridad: rclone.conf (tokens OAuth) servido a toda la LAN sin auth** — el guard (`sync_cloud.py:27-34`) solo exige PIN si `web_allow_lan=false`, pero los defaults son `web_host="0.0.0.0"` + `web_allow_lan=true` (`config.py:430,432`): cualquier dispositivo de la red descarga los tokens por HTTP plano. Fix: token efímero de un uso embebido en el script `/s`, o PIN obligatorio para este endpoint en binding no-loopback | Seguridad | M | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-4 | **IP personal hardcodeada como fallback** — `get_bootstrap_script` usa `"192.168.1.160"` si `get_lan_ip()` falla (`sync_cloud.py:48`). Fix: usar el header `Host` de la request como fallback | Bug | XS | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-5 | **La promesa del paso 1 es falsa** — dice que al abrir la URL en la consola "aparecerá una guía de instalación con botones de descarga" (`tab-anbernic.html:30-32`); lo que aparece es `android-detected-panel` (`_banners.html:21-52`): panel de sync sin botones de instalación, "PC conectado" hardcodeado y botón roto (CLOUD-UX-6). Fix: estado "primera vez" con vista táctil de instalación + comprobación real del servidor | UX | M | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-6 | **QR en el paso 1** — teclear `http://ip:7777` en la consola es el paso más doloroso; `renderQR` ya existe (`config.js:499`) y no se usa aquí. Además "Copiar URL" copia al portapapeles del PC y el tip del paso 5 alude a un portapapeles-por-ADB que no existe (`tab-anbernic.html:147`). Fix: QR junto a `anb-ip-display`, quitar textos de funciones inexistentes | UX | XS | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-7 | **Sin check de prerequisitos** — la pestaña no consulta `/api/rclone-status` (sin remotes, el script descarga un rclone.conf vacío y la consola queda a medias) ni avisa de binding loopback / firewall Windows (`_check_firewall` existe en `lan.py:52` pero solo se usa en CLI, `cli.py:969`). Fix: banner arriba con ① cloud configurado ② servidor accesible por LAN | UX | S | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-8 | **Errores silenciosos y enlaces engañosos** — si `/api/local-url` falla, "Detectando…"/"Cargando…" quedan para siempre (`sync.js:418-420`); "Descargar Termux APK" abre la página de releases, no un APK (`tab-anbernic.html:82`). Fix: error visible con reintento + etiquetas honestas | UX | XS | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-9 | **`/api/local-url` gasta un `subprocess` en cada llamada** — `_check_firewall` (`web/lan.py:52`, invocado desde `handlers/esde/system.py:59,66`) lanza `netsh advfirewall firewall show rule` (spawn de proceso, decenas de ms en Windows) en cada `GET /api/local-url`; tras ANBERNIC-UX-7 ese endpoint se llama también desde `loadAnbernicTab()` y `tvToggleSetup()` (`sync.js:410,283`), no solo desde Settings. Fix: cachear el resultado unos segundos/minutos en memoria (el estado del firewall no cambia entre refrescos de pestaña) o solo comprobarlo si `lan_bound=true` y ha pasado un TTL desde la última comprobación | Rendimiento | XS | ✅ caché en memoria `_firewall_cache` (`web/lan.py`), TTL 60s por puerto — evita el `subprocess` en refrescos consecutivos de pestaña. 2 tests nuevos (`test_lan_firewall_cache.py`) |
| ANBERNIC-UX-10 | **Token de setup: un solo slot global, no por sesión** — `_mint_setup_token` (`handlers/sync_cloud.py:141`) sobreescribe `_state._anbernic_setup_token` (`web/state.py:40`) en cada llamada a `GET /api/anbernic-setup-token`; si se abre la pestaña Anbernic en dos pestañas del navegador a la vez, el segundo mint invalida el comando ya copiado del primero (403 al ejecutarlo). Bajo impacto (app de un solo usuario/escritorio) pero fix barato: token efímero por request en vez de global, o lista de tokens válidos con TTL en vez de un único slot | Bug | XS | ✅ `_state._anbernic_setup_tokens` pasa de dict único a lista de tokens vivos (`web/state.py`, `sync_cloud.py`); mintear uno nuevo poda los caducados pero conserva los que aún no expiraron — dos pestañas ya no se invalidan entre sí, cada token sigue caducando a los 10 min. Test nuevo `test_minting_new_token_does_not_invalidate_still_valid_ones` |

Validación en hardware pendiente: comprobar en la RG556 si Termux limpio trae
`curl` (el one-liner `curl -s …/s \| bash` falla si no; la guía manual
`docs/sync/Guia-Termux-Anbernic.md` no lo usa).

---

### CABLE-ROM-FIX — El sync de ROMs por cable no compara con el destino (hallazgo 2026-08-13)

Origen: el usuario pidió sincronizar biblioteca PC↔consola vía Cable Sync
(`what: ["roms"]`). Investigación con dry-run real contra la RG556
(serial `RG556006101273`, SD en `/storage/521D-04EA`, 49 GB libres de 466 GB):
pidió copiar **47.191 archivos / 516 GB** — la biblioteca del PC entera,
sin importar que la SD ya tenga casi todo (misma estructura de carpetas que
el PC). Repetido con `skip_existing: true` + `skip_sha1_dups: true`: **resultado
idéntico**, byte a byte.

Causa raíz: `web/handlers/sync_cable.py:597-605` (rama `direction ==
"pc_to_anbernic"`) itera todos los archivos del PC y llama a
`_adb_copy_to_device` para cada uno **sin comprobar nunca** el listado del
dispositivo (`ab_adb_files`, calculado en la línea 569 pero solo usado para
`delete_extra` y estadísticas de progreso — nunca para decidir qué copiar).
El parámetro `skip_existing` que acepta el endpoint no se referencia en
ningún punto de esta rama. `sync/adb_transport.py:278`
(`AdbTransport.push`) tampoco compara contenido/mtime antes de subir — en
`dry_run` ni siquiera llega a intentarlo, solo devuelve el tamaño local.
Contraste: la rama `anbernic_to_pc` (línea 636) sí usa `use_sha1`/hash para
saltar duplicados — la asimetría sugiere que `pc_to_anbernic` quedó a medias.

| ID | Task | Notas |
|----|------|-------|
| CABLE-ROM-FIX-1 | Implementar comparación real contra `ab_adb_files`/`pc_root` antes de copiar en ambas ramas ADB (`pc_to_anbernic` y `anbernic_to_pc`) — mismo criterio que ya usa `cable_engine.copy_item` en el modo sistema de archivos (tamaño) | `web/handlers/sync_cable.py:597-605,672-729` | ✅ rama `fix/cable-sync-rom-skip-existing` → PR #161 |
| CABLE-ROM-FIX-2 | Guard de espacio libre en destino antes de empezar (ya existe un patrón idéntico en `zip_router.py:_extract_collection` — `shutil.disk_usage(dest_dir).free`) — evita rellenar la SD a medias | `web/handlers/sync_cable.py` (rama ADB de `_do_cable_sync`) | ✅ `AdbTransport.free_bytes()` (`sync/adb_transport.py`, vía `df -k`) + guard antes de escribir en corridas reales (`dry_run=False`) |
| CABLE-ROM-FIX-3 | Sync por plataformas — con el fix, la SD (78 GB libres) sigue sin caber la biblioteca completa (305,9 GB). No hace falta código nuevo: el endpoint ya soporta `pc_path`/`android_path` apuntando a una subcarpeta. Desglose real por plataforma: `psx` 61,1 GB, `gamecube` 34,3 GB, `ps2` 29,9 GB, `Unknown` 25,2 GB (basura), `arcade` 17,6 GB no caben; el resto (~66 GB tras `skip_existing`) sí | — | ✅ ejecutado de verdad 2026-08-13/14: 50 carpetas, confirmado en `.rommgr/cable_sync_ops.log` — terminó sin errores reales (`errors=0` en todas las corridas de esa sesión salvo un reintento transitorio de daemon adb sobre un `.jpg` de wheel, sin relación con ROMs/saves ni con PSX). `psx`/`gamecube`/`ps2`/`Unknown`/`arcade` siguen sin sincronizar — pendientes de espacio en la SD |
| CABLE-ROM-FIX-5 | Sync real de `arcade` a la RG556 (2026-08-27): **ya terminó solo**, no hizo falta pausarlo — `copied=3192 skipped=49 errors=2`. Los 2 errores son el mismo hipo transitorio de daemon adb ya visto en Día49 (`daemon still not running`), no relacionado con los archivos en sí: `lresort.zip` y `Ring of Destruction_ Slammasters II (Europe 940902).zip` probablemente no llegaron. `arcade/_descartados` (1,13 GB de sets incompletos) se apartó temporalmente antes del sync para no llenar la SD de basura, y se restauró después — no se sincronizó. `gamecube` (34,3 GB) quedó sin lanzar, pendiente para la próxima sesión | `.rommgr/cable_sync_ops.log` (línea `Fin 2026-08-26T23:47:45Z`) | ✅ arcade hecho (verificar los 2 archivos concretos en el próximo sync); 🔴 gamecube pendiente |
| CABLE-ROM-FIX-4 | La allowlist de carpetas por plataforma usada en CABLE-ROM-FIX-3 fue manual/ad-hoc (script de orquestación de esa sesión, no persistido). Añadir selector de plataformas incluir/excluir en la UI de Cable Sync (o config), reutilizando `PLATFORM_BY_FOLDER`/`_ES_PLATFORM_FOLDERS` ya existentes, para no tener que rehacerla a mano cada vez que la SD no tenga espacio para todo | `web/handlers/sync_cable.py`, frontend Cable Sync | 🔴 pendiente — origen: sesión 2026-08-26, petición del usuario de "establecer un patrón" para plataformas que se quedan fuera |

> **CORRECCIÓN 2026-08-26** de la nota anterior (verificada solo por nombre,
> no por contenido — error propio): las 125 subcarpetas de `psx/` NO son
> sets multi-disco organizados, son carpetas huérfanas de scraping — 0
> ROMs reales dentro. Detalle completo y plan de limpieza en `PSX-ORPHAN`
> (sección Pilar 1, más abajo). No se ha borrado ni movido nada.
>
> Estado: ✅ implementado y validado con dry-run + ejecución real contra
> hardware conectado (RG556). Ver `Tareas/diario/Día49.md` para los
> números completos y el resultado final de la transferencia por
> plataformas.

---

### ANBERNIC-PICK — Selección manual de qué se lleva a la Anbernic — → #246

Origen: sesión 2026-08-28, tras organizar un bestset de FBNeo (636 juegos) y
encontrar 295 conflictos de versión de romset. `CABLE-ROM-FIX-4` (arriba)
ya cubre incluir/excluir por **plataforma entera**; esto es más fino —
juego a juego o colección a colección — reutilizando lo que ya existe en
vez de construir un selector nuevo. Decisión del usuario: manual explícito,
no automático por espacio libre/prioridad.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ANBERNIC-PICK-1 | **Marcar juegos para la Anbernic reutilizando `game_tags`** — sin esquema nuevo: tag reservado `"anbernic"` vía `add_tag_bulk`/`remove_tag_bulk` (`database/repositories/metadata.py`). `POST /api/tag-bulk` (`web/handlers/games.py`) reutiliza `get_games_paginated` con los mismos filtros que `/api/games` para aplicar el tag a todo lo que cumple el filtro actual | `database/repositories/metadata.py`, `web/handlers/games.py`, `web/static/js/tabs/games.js` | ✅ PR #248 — botones "Marcar para Anbernic"/"Desmarcar" en la pestaña Juegos, con confirmación mostrando el total. 5 tests nuevos (`tests/web/test_tag_bulk.py`). Verificado en vivo contra la biblioteca real |
| ANBERNIC-PICK-2 | **Cable Sync filtra por la marca en la rama de ROMs** — `_do_cable_sync` (`web/handlers/sync_cable.py:395`, `os.walk(root)`) no cruza contra ninguna marca hoy; añadir checkbox opt-in "solo juegos marcados" que, activo, salta cualquier archivo cuyo `games.source_path` no tenga el tag `"anbernic"` antes de copiarlo. Por defecto desactivado (comportamiento actual sin cambios) | `web/handlers/sync_cable.py:395`, frontend Cable Sync | ✅ `only_tagged` en `_do_cable_sync`: precalcula el set de `source_path` con tag `anbernic` una vez (join `games`+`game_tags`) y `_wanted()` lo consulta solo para archivos ROM del lado PC (no afecta a saves ni a `anbernic_to_pc`, que no tiene marcas que consultar). Checkbox "Solo ROMs marcados para la Anbernic" en `tab-cable.html`, visible solo con "ROMs" marcado. 4 tests nuevos (`tests/test_sync_cable_only_tagged.py`), 1047 pass |
| ANBERNIC-PICK-3 | **Informe de la corrida** — agregar en una vista legible los contadores que el pipeline ya calcula por corrida (organizados, duplicados exactos descartados, resueltos por RA, conflictos sin resolver) en vez de solo el log de texto — insumo directo para "qué se movió, qué no, qué se reemplazó, qué se renombró" que pidió el usuario. Base de datos real de la sesión 2026-08-28 ya disponible como caso de prueba: 13.211 organizados, 1.005 renombrados, 152 duplicados, 0 resueltos por RA, 295 conflictos (176 arcade) | `web/inbox_pipeline.py`, `web/static/js/tabs/inbox.js` | ✅ el paso "organize" no contaba duplicados exactos descartados ni conflictos sin resolver por separado (solo iban mezclados como texto en `organize_errors`) — dos contadores nuevos (`duplicates_removed`, `conflicts_unresolved`) en `_run_inbox_pipeline`, incrementados en las ramas ya existentes de `_same_content`/`_resolve_organize_conflict`. `_renderInboxResult()` (`inbox.js`) los añade a la línea de resumen junto a "Resueltos por RA" (ya se calculaba pero no se mostraba) |
| ANBERNIC-PICK-4 | **El sync también debe quitar de la consola lo que ya no está marcado** — petición del usuario 2026-08-29: al sincronizar, lo no marcado debería desaparecer de la Anbernic, no solo dejar de copiarse, para poder liberar espacio con el mismo flujo. Ya existía el checkbox "Espejo completo" (`delete_extra`) independiente de `only_tagged`; combinados, la rama ADB (cable) ya funcionaba bien (`_arel not in _pc_rels`, `_pc_rels` calculado con `_wanted()` que sí respeta el tag), pero la rama sistema de archivos (SD montada) no — su bucle de "extra en destino" llamaba a `_wanted(_f)` sobre archivos del lado Anbernic, que **siempre** devuelve `True` para ese lado (rama `except ValueError` de `_wanted`, necesaria para no romper `anbernic_to_pc`/`newest`, que sí deben ignorar el tag por diseño de ANBERNIC-PICK-2) | `web/handlers/sync_cable.py` (bucle `delete_extra` de `pc_to_anbernic`, modo sistema de archivos) | ✅ ese bucle ahora filtra por categoría (`_wanted_name`, igual que ya hacía la rama ADB) en vez de por `_wanted()` completo — "extra" sale de comparar contra `_pc_rels`, que ya respeta el tag; sin tocar `anbernic_to_pc`/`newest`. Tooltip de "Espejo completo" actualizado explicando la combinación. 1 test nuevo (`test_only_tagged_with_mirror_removes_untagged_from_device`), 1034 pass |

**Validado con dry-run real contra la RG556 (2026-08-29)**: 1 juego real
(`'96 Flag Rally.zip`, arcade) marcado `anbernic` vía `/api/tag`, sync
`pc_to_anbernic` por ADB, `what=roms`, `only_tagged=true`,
`delete_extra=true`, `dry_run=true` contra `/storage/521D-04EA/ROMs/arcade`.
Resultado: el marcado se detecta correctamente como ya presente (`SKIP —
mismo tamaño`, nunca entra en la lista de borrado) y **3.461 archivos sin
marcar** se listan como "se borrarían" (`.rommgr/cable_sync_ops.log`) — el
combo funciona tal como se diseñó. El tag de prueba se quitó al terminar
(sin residuo). Nota: el servidor llevaba corriendo desde antes del fix de
ANBERNIC-PICK-4 (Python no recarga módulos en caliente) — hubo que
reiniciarlo para probar la versión real del código; se esperó primero a que
terminara un job de Inbox en curso (15.105 ROMs) antes de reiniciar.

> **ANBERNIC-PICK-5 — hallazgo durante la validación anterior, bug real
> preexistente (no introducido por ANBERNIC-PICK-4)**: de los 3.461
> "extra" candidatos a borrar, **204 eran `.jpg` de `media/wheels/` (carátulas),
> más 2 `.txt`, 1 `.xml`, 1 `.ini`** — ninguno es un ROM, y el sync estaba
> acotado a `what=["roms"]` (sin "assets"/"media" marcado). Causa: `_cat_name()`
> (`web/handlers/sync_cable.py:372`) clasifica cualquier archivo que no sea
> una extensión de save como `"rom"` — no comprueba una lista real de
> extensiones de ROM, así que `_wanted_name()` (`:378`) acepta cualquier cosa
> que no sea un save cuando `"roms"` está en `what`. Con "Espejo completo"
> activo, esto borraría carátulas y metadatos junto con los ROMs de verdad.
> No afecta a copiar (solo se copian archivos que ya pasaron por el scan como
> ROM/save en la BD), pero si el "extra" del lado Anbernic no está en la BD
> —caso típico de `media/`, que nunca se escanea como juego— nada lo protege
> de aparecer como "extra". Pendiente: `_cat_name()` debería devolver una
> tercera categoría (`"other"`) para lo que no sea ni save ni ROM reconocido,
> y `_wanted_name()` debería excluirla salvo que `"assets"`/`"media"` esté en
> `what` explícitamente | `web/handlers/sync_cable.py:372-382` | 🔴 pendiente |
| ANBERNIC-PICK-8 | **Enviar/eliminar en bloque desde la pestaña Juegos, sin pasar por el tag `anbernic`** (renumerado desde una colision de ID con ANBERNIC-PICK-4 -- ambas ramas reclamaron el mismo numero en paralelo) — complementa ANBERNIC-PICK-1/2 (que exigen marcar antes): dos botones nuevos que actúan directo sobre **el filtro actual** de la pestaña (mismo criterio que "Marcar para Anbernic"), por ADB. `direction="send_selected"` resuelve los juegos del filtro (`get_games_paginated`), dedupea duplicados del mismo juego quedándose con el que tiene más logros RA (`filter_duplicate_winners`, reutilizado de Duplicados de ROM) y hace skip-existing por tamaño antes de empujar. `direction="remove_selected"` copia el save de cada juego al PC (verificado por MD5) **antes** de borrar el ROM — un save nunca se borra ni se pierde si falla la copia — y solo entonces elimina por ADB | `web/handlers/sync_cable.py` (`_do_cable_sync`, ramas `send_selected`/`remove_selected`), `services/ra_duplicates_service.py` (`filter_duplicate_winners` reutilizado), frontend `tabs/games.js` (`sendFilteredToAnbernic`/`removeFilteredFromAnbernic`) + `tab-games.html` | ✅ 6 tests nuevos (`test_cable_sync_send_selected.py`, `test_cable_sync_remove_selected.py`, `test_ra_bulk_send_dedup.py`) |

| ANBERNIC-PICK-6 | **Discoverabilidad (feedback usuario 2026-08-29)**: el usuario no encontró cómo copiar en bulk PC→Anbernic ni cómo marcar juegos para que se retiren de la consola — ambos ya existen (Cable Sync con "solo ROMs marcados" + "Espejo completo" quita de la Anbernic lo no marcado, ANBERNIC-PICK-2/4) pero no están enlazados/explicados desde donde el usuario los buscó (Herramientas). Falta UX de descubrimiento, no código nuevo | `web/static/partials/tab-tools.html`, `tab-cable.html` | ✅ panel nuevo "Enviar archivos a la Anbernic" al principio de Herramientas, con el resumen del flujo (marcar en Juegos → Cable Sync "solo marcados"/"Espejo completo") y dos botones: uno a Juegos (`showTab('games')`) y otro a Cable Sync que además abre y hace scroll a "Sincronización avanzada" (`goToCableSyncAdvanced()`, `tabs/sync.js` — nuevo `id="cable-advanced-details"` en el `<details>`). Sin endpoints nuevos, solo navegación. Verificado sirviendo la página real (`curl` contra `rommgr serve`); no probado clic a clic en navegador (extensión Chrome no disponible en esta sesión) |
| ANBERNIC-PICK-7 | **Ampliación de ANBERNIC-PICK-6 (aclarado 2026-08-29): sync guiado de primer uso** — el usuario quiere empezar a usar la Anbernic llevando plataformas pequeñas enteras (NDS, arcade) sin tocar nada más, y eligiendo juego a juego en plataformas grandes (PS2) por espacio. El mecanismo ya existe (`ANBERNIC-PICK-1`: `POST /api/tag-bulk` con los mismos filtros que `/api/games`, incluye `platform` → marcar "toda una plataforma" es 1 filtro + 1 botón; `ANBERNIC-PICK-2`: Cable Sync "solo ROMs marcados") — falta un asistente/wizard en Juegos o Cable Sync que lo guíe explícitamente ("¿Qué te llevas a la Anbernic?" → plataformas pequeñas con checkbox "todo", grandes con enlace a la selección juego a juego) en vez de que el usuario tenga que descubrir la combinación de filtro+tag+sync por su cuenta | `web/static/js/tabs/games.js`, `tab-cable.html` | ✅ botón "🧭 Asistente guiado" en Herramientas (`openAnbernicWizard()`, `games.js`) — modal con plataformas separadas en pequeñas (≤2 GiB, botón "Marcar toda" de un clic vía `/api/tag-bulk`) y grandes (botón "Elegir juego a juego →" que navega a Juegos filtrado por esa plataforma, orden "Fecha de añadido"). `/api/platform-stats` (ya existente) ampliado con `total_size`/`tagged_count` por plataforma, sin endpoint nuevo. Además, selector individual nuevo en Juegos: botón 📦 por fila (`toggleRowAnbernic()`, mismo patrón que la ★ de favorito, vía `/api/tag` ya existente) y orden nuevo "Fecha de añadido" (`sort_by=added`, `created_at` expuesto en `/api/games`). 1038 pass. Verificado en vivo: `/api/platform-stats` con tamaños reales (MAME 37,7 GB, Arcade 27,5 GB, FBNeo 8,1 GB...), toggle 📦 ida y vuelta sobre un juego real sin dejar residuo |

---

### FTP-PICK — Elegir ROMs desde el navegador de la Anbernic (petición usuario 2026-08-29)

Origen: `docs/Feedback/29/8.md` + petición directa del usuario en sesión — quiere
poder, desde la Anbernic, elegir qué ROMs traerse del PC mientras `rommgr serve`
está corriendo, sin pasar por Cable Sync/ADB. **Rediseñado a mitad de sesión**:
el plan original (servidor FTP a mano + app Android nativa en Kotlin) se
descartó por sugerencia del propio usuario — la Anbernic **ya abre un
navegador** para llegar al servidor (mismo flujo que la pestaña Anbernic de
setup guiado), así que un botón de descarga en la propia pestaña Juegos
reutiliza servidor, auth, buscador y filtros ya existentes, sin protocolo
nuevo ni código Kotlin sin compilar. La implementación FTP + app nativa
(`ftp/ftp_server.py`, `PcFtpClient.kt`, `PickScreen.kt`) se hizo, se verificó
contra la biblioteca real y **se borró entera** al cambiar de enfoque — nada
de eso queda en el repo.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| FTP-PICK-1 | **Endpoint de descarga por HTTP, reutilizable desde donde sea** — nuevo `GET /api/download-rom?path=<source_path>`: solo sirve rutas que ya están en la BD como ROM (`file_type='rom'`, nunca un archivo arbitrario del disco aunque exista físicamente) y que además resuelvan dentro de `library_root`/`anbernic_root` (`Path.resolve()` + `is_relative_to()`, mismo patrón de path traversal que REV43-16). Streaming real vía `shutil.copyfileobj` (nuevo `ctx._send_file()` en `web/server.py`) — nunca carga el archivo entero en memoria, a diferencia de `_send()`/`/api/asset-image` (pensados para JSON/imágenes pequeñas); necesario porque un ISO de PS2/GameCube puede pesar varios GB. `Content-Disposition: attachment` con el nombre real del juego. Enlace ⬇ en la tabla de Juegos (`games.js`) para uso directo desde el navegador | `web/handlers/games.py` (`get_download_rom`), `web/server.py` (`_send_file`), `web/static/js/tabs/games.js` | ✅ 5 tests nuevos (`tests/web/test_download_rom.py`: descarga normal, sin parámetro, archivo no trackeado en BD aunque exista en disco, traversal fuera de `library_root`, archivo borrado tras el scan) + **probado contra la biblioteca real**: descargado un `.nes` real por HTTP y comparado SHA1 byte a byte contra el original (coinciden); confirmado 404 para una ruta arbitraria del sistema no trackeada y 400 sin parámetro `path`, ambos contra el servidor real corriendo. 1042 pass |
| FTP-PICK-2 | **Pantalla "Elegir ROMs" en la app Android (ANDROID-SYNC)** — decisión final del usuario: quería el flujo dentro de la app nativa que ya se está construyendo, no solo un enlace en el navegador. En vez de repetir el error del primer intento (protocolo FTP a mano + cliente Kotlin a medida, descartado), la app llama por HTTP normal a los mismos dos endpoints ya probados en el lado Python (`GET /api/games` para buscar/filtrar, `GET /api/download-rom` para bajar) — cero protocolo nuevo, cero librería nueva (`HttpURLConnection`/`org.json` son parte de la plataforma Android, igual que el SDK de Dropbox ya en uso). `PcApiClient.kt` nuevo: `listPlatforms()`/`listGames()` parsean el JSON ya devuelto por el PC, `downloadRom()` guarda en `<romsDestPath>/<carpeta-de-plataforma-real-del-PC>/<nombre>` — la carpeta se deduce del propio `source_path` que ya devuelve `/api/games` (segmento inmediatamente anterior al nombre de archivo), sin necesitar conocer `library_root` del PC. Pantalla `ui/pick/PickScreen.kt` (formulario IP:puerto → lista de plataformas + buscador + lista de juegos con descarga y progreso), tercera pestaña en `MainActivity.kt`. Ajustes nuevos en `SettingsRepository.kt` (`pcHost`, `romsDestPath`). `usesCleartextTraffic="true"` en el manifest (HTTP plano, no HTTPS — mismo modelo de confianza de LAN doméstica que `allow_lan` en el PC; sin login, asume el PC sin PIN activo, limitación conocida documentada en el propio código) | `android/app/src/main/java/com/retrovault/android/sync/PcApiClient.kt` (nuevo), `ui/pick/PickScreen.kt` (nuevo), `data/prefs/SettingsRepository.kt`, `ui/MainActivity.kt`, `AndroidManifest.xml` | ✅ **compilado y verificado 2026-08-29** con toolchain portable (`JAVA_HOME`=jdk17, `./gradlew test assembleDebug`, ambos en verde). Encontrado y arreglado un bug real de compilación: `PickScreen.kt:9` importaba `androidx.compose.foundation.layout.weight` como función de paquete — `weight` es en realidad un método miembro de las interfaces `RowScope`/`ColumnScope` (no una función top-level importable), así que el import resolvía a un símbolo interno no relacionado y rompía `compileDebugKotlin`/`compileReleaseKotlin`. Fix: eliminar el import — los dos usos de `.weight(1f)` ya están dentro de lambdas `Row{}`/`Column{}`, se resuelven solos por receiver implícito sin necesitar import. `./gradlew test` (incluye `PcApiClientTest.kt`, 3 tests) en verde. Pendiente real: solo instrumented/manual contra el servidor vivo (`connectedAndroidTest`/emulador) — fuera de alcance sin dispositivo/emulador en esta sesión |

---

### GAME-BLOCKLIST — Eliminar un juego de ambas bibliotecas y evitar que un sync lo recupere (feedback usuario 2026-08-29)

Origen: `docs/Feedback/29/8.md`, aclarado por el usuario — caso de uso: "este juego
(ej. un Barbie) no me interesa, quiero borrarlo de PC y Anbernic a la vez, y que
ningún sync futuro me lo vuelva a colar". Distinto de `STORAGE-MGR` (archivado:
borrado en bloque puntual, sin bloqueo permanente) y de `ANBERNIC-PICK`
(el tag `"anbernic"` es opt-in por lo que SÍ debe estar en la consola, no un
"nunca más" global que también cubra el PC). Necesita una marca persistente
por identidad de juego (SHA1/`canonical_title`, no por ruta — la ruta difiere
entre PC y Anbernic y cambia al renombrar) que el scan/inbox/match respete.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| GAME-BLOCKLIST-1 | Diseñar la marca de exclusión permanente (tabla o tag reservado tipo `game_tags`, keyed por SHA1 para sobrevivir a renombrados y aplicar igual en ambas BDs) + acción "Eliminar de ambas bibliotecas" (PC → papelera `_descartados/`, Anbernic → `AdbTransport.remove`, mismo patrón de `STORAGE-MGR-3`/`services/storage_service.py`, pero marcando además de borrar) | `services/storage_service.py`, `database/repositories/metadata.py` (patrón `game_tags`) | 🔴 pendiente, sin diseñar |
| GAME-BLOCKLIST-2 | Hacer que el scan/match/Inbox respeten la marca — un archivo con SHA1 bloqueado no se re-organiza ni se re-cuenta como pendiente si reaparece (p. ej. tras un sync `anbernic_to_pc` o un `adb pull` manual); decidir si se auto-descarta en silencio o se avisa una vez y se deja para revisión | `scanner/rom_scanner.py` o `web/inbox_pipeline.py` (punto de entrada exacto por confirmar) | 🔴 pendiente, depende de GAME-BLOCKLIST-1 |

---

## UX — Auditorías por pestaña — → #206

Auditorías de UX/UI por pestaña que no pertenecen a un pilar concreto
(dashboard, tabs de biblioteca/herramientas/formatos, etc.).

> ✅ Archivado en Tareas/diario/archivo/archivo.md: INICIO-UX, ASSETS-UX, COLECCION-UX, DUPLICADOS-UX, PLAN-UX, SCRAPER-UX, TV-UX, SETTINGS-UX, HERR-UX, FORMATOS-UX, PSX-FIX, TRASH-FIX-1, JUEGOS-FIX-1, CLOUD-FIX-1, SYNC-FIX-2, SYNC-FIX-1 (auditorías UX completas, 2026-07-13 a 2026-08-27).

---

### HERR-FIX — Bugs en Herramientas hallados en feedback del usuario (2026-08-29)

Origen: `docs/Feedback/29/8.md`. No investigados a fondo todavía — documentar
archivo:línea antes de arreglar (regla del proyecto).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| HERR-FIX-1 | **"Descartar sin soporte" (RA) no hace nada al pulsarlo** — y el criterio pedido por el usuario es más estricto que "sin logros en RA": solo debería descartar un juego si existe una alternativa CON logros RA disponible, nunca todos los juegos sin soporte RA sin más. Relacionado con `discard_no_support`/`no_support_entries` (ver REV43-27 en `archivo.md`, sobre el mismo flujo) | `web/handlers/`, posible `services/ra_duplicates_service.py` | ✅ **dos bugs reales, no uno**: (1) `discardRaNoSupport()` (`web/static/js/tabs/esde.js:391`) integraba el modal de confirmación con `window._confirmCallback`, que `_showConfirm()` (`components/modal.js`) **nunca llama** — el callback real es el 4º argumento de `_showConfirm(title, body, okLabel, onConfirm)`, así que pulsar "Confirmar" no hacía nada (`_confirmOkHandler` quedaba `undefined`), el fetch a `/api/ra-check/discard-no-support` nunca se disparaba. (2) **el criterio ya estaba invertido**: `no_support_entries` (`web/handlers/sync.py:144-152`, dentro de `_do_ra_check`) se construía con `status == "no_support"` (sin alternativa — la única copia del juego) en vez de `status == "no_support_alternative"` (ya hay una copia mejor en la biblioteca) — de haber funcionado el botón, habría borrado justo los juegos que había que conservar. Fix: `sync.py` filtra ahora por `no_support_alternative`; `esde.js` usa `_showConfirm` con el callback correcto (4º argumento) y el botón/conteo pasan de `noSupport` a `alternative` ("Descartar con alternativa RA"). 1 test nuevo (`tests/web/test_ra_discard_no_support.py`, llama `_do_ra_check` con `check_library` mockeado, confirma que un juego sin alternativa nunca aparece en `no_support_entries`). 1039 pass (3 fallos preexistentes no relacionados, Anbernic conectada por USB en esta sesión) |
| HERR-FIX-2 | **Clic en "Consola Android" en Herramientas no actualiza las rutas a las de la consola automáticamente** — posible regresión o caso no cubierto por el fix ya archivado de `setToolsContext`/`_deviceRoot()` (ver HERR-UX-7/FORMATOS-UX-1/CABLE-UX-10/11 en `archivo.md`) | `web/static/js/tabs/duplicates.js` (`setToolsContext`), `main.js` (`_deviceRoot`) | ✅ regresión real de FORMATOS-UX-1: `_setIfEmpty` (`duplicates.js:9-38`) solo rellena inputs **vacíos** para no pisar una ruta escrita a mano — pero eso también bloqueaba el propio botón de contexto: tras rellenar la ruta de PC, el input ya no está vacío, así que pulsar "Consola Android" nunca la sobreescribía. Fix: cada input lleva `dataset.ctxAuto='1'` cuando el selector lo rellena, y se sobreescribe si está vacío **o** si sigue marcado como auto-rellenado; un listener de `input` solo borra esa marca en eventos `isTrusted` (edición real del usuario, nunca el `dispatchEvent` propio que ya disparaba el código) — así una ruta tecleada a mano se sigue respetando, pero cambiar de contexto sí actualiza lo que el propio selector puso. Import muerto de `_setIfEmpty` eliminado de `duplicates.js` (ya no se usa ahí). No verificado en navegador (extensión Chrome no disponible esta sesión) — revisado por lectura del código y trazado manual del flujo de eventos |
| HERR-FIX-3 | **"Estructura de biblioteca" no crea la estructura en la Anbernic** — no respeta la convención ya adoptada de carpeta `ROMs/` dentro de la raíz de la consola (ver DEVICE-DUP-1, `archivo.md`/PSX-ORPHAN) | `web/handlers/organize.py:319-395` (`_do_create_library_structure`, no `esde/maintenance.py`) | ✅ `_create_tree()` (línea 330) gana el parámetro `roms_subdir` — vacío para PC (comportamiento sin cambios), `"ROMs"` para el árbol Android: las carpetas de plataforma ahora se crean en `<raíz SD>/ROMs/<plataforma>` en vez de sueltas en la raíz. Decisión del usuario (confirmada, sin evidencia de hardware en contra): `saves/`, `media/`, `configs/`, `bios/`, `inbox/`, `screenshots/` se quedan en la raíz de la SD en ambos casos, no se anidan bajo `ROMs/`. 1 test nuevo (`tests/test_library_structure.py::test_android_platforms_nest_under_roms`, configura un `anbernic_root` de prueba y confirma `ROMs/gba`+`ROMs/psx` sí, `gba` suelto no, `saves`/`bios` en la raíz). 1037 pass. No verificado contra la SD real (no montada esta sesión) |
| HERR-FIX-4 | **UI: la pestaña "Herramientas" oculta el menú lateral de pestañas en algunos de sus paneles** — bug de layout, no investigado | `web/static/css/app.css` o partials de Herramientas | 🟡 **sin confirmar visualmente (extensión Chrome no disponible esta sesión) — hipótesis más probable documentada, no aplicada a ciegas**. `.sidebar` (`app.css:364-373`) tiene `flex-shrink:0` + `z-index:8005` dentro de `.app-body{display:flex}` — no debería taparse por z-index. El mecanismo más plausible es un desbordamiento horizontal: varias tablas de resultados en Herramientas (`esde.js:1500,1511,1520`, informe de biblioteca) se generan como `<table>` suelto sin ningún contenedor `overflow-x:auto` (a diferencia de Juegos, que sí envuelve su tabla en `#games-list-view{overflow-x:auto}`, `tab-games.html:63`); una ruta o nombre de archivo largo sin cortes fuerza el ancho de la tabla más allá del viewport, lo que puede desplazar/ocultar el sidebar al desbordar `.app-body`. No aplicado ningún cambio — falta reproducir en navegador para confirmar cuál panel exacto y si esta es la causa real antes de tocar CSS |

---

### JUEGOS-FIX-2 — El filtro de plataforma en Juegos es casi inútil en bibliotecas grandes (hallado 2026-08-29)

Origen: feedback del usuario tras probar el buscador — "no puedo filtrar por plataforma".

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| JUEGOS-FIX-2 | **El desplegable "Plataforma" de Juegos solo se rellena con las plataformas presentes en la página actual de resultados** (`loadGames()`, `games.js:452-460` aprox., máx. 100 filas) — con el orden por defecto (`platform, canonical_title, original_filename`) y una biblioteca de 28k+ juegos con muchos sin plataforma (`NULL` ordena primero en SQLite), **la primera página cae entera en "Unknown"** — verificado en vivo: `/api/games?limit=100` real devuelve una única plataforma distinta (`Unknown`) en sus 100 filas, así que el filtro no ofrecía ninguna otra opción. `GET /api/games/filter-options` ya devuelve las 43 plataformas reales distintas de la BD (usado para género/año, `games.py` repositorio, consulta `SELECT DISTINCT platform...`) pero `loadFilterOptions()` (`games.js:129-145`) nunca lo usaba para rellenar `games-platform` | `web/static/js/tabs/games.js:129-145` (`loadFilterOptions`) | ✅ `loadFilterOptions()` rellena también `games-platform` desde `r.platforms` (mismo endpoint ya usado para género/año, sin llamada nueva) y marca `platformsLoaded=true` para que el muestreo antiguo de `loadGames()` no lo pise; ese muestreo queda como fallback solo si `filter-options` fallara. Verificado contra la biblioteca real: `filter-options` devuelve las 43 plataformas reales (Amiga, Arcade, Atari 2600...). No verificado en navegador (extensión Chrome no disponible esta sesión) |

| JUEGOS-FIX-3 | **"El nombre del juego no aparece en la tabla del frontend"** (feedback usuario 2026-08-29, tras confirmar que no era caché de navegador). Causa raíz real: `applyColVisibility()` (`games.js`, columnas opcionales Región/Identificación/Tamaño/SHA1 del selector ⚙) ocultaba celdas por **índice fijo** (`tr.cells[3..6]`, comentario "0=platform,1=title,2=filename..." — ya desactualizado antes de esta sesión, no contaba ni con la ★ favorito ni con la miniatura). Al añadir hoy la columna 📦 Anbernic (`ANBERNIC-PICK-7`), cada índice se desplazó una posición más: `COL.match=4` pasó de apuntar al badge de Identificación a apuntar directamente a la celda de **Título canónico** — con la preferencia de columnas del usuario guardada en `localStorage` (p.ej. "Identificación" desmarcado en algún momento), `applyColVisibility()` ocultaba el título en cada render sin que nada más pareciera roto | `web/static/js/tabs/games.js` (`applyColVisibility`, fila de la tabla) | ✅ cada `<td>` opcional lleva ahora `data-col="region\|match\|size\|sha1"` fijo en el propio template de la fila; `applyColVisibility()` selecciona por ese atributo (`tr.querySelector('[data-col=...]')`) en vez de por índice — inmune a que se añadan o quiten columnas en el futuro. De paso confirmado con los valores por defecto (`size:false, sha1:false`) que el bug de índice YA escondía "Archivo original"/"Estado" en vez de "Tamaño"/"SHA1" para todo el mundo, no solo para quien tocara el selector ⚙ — corregido igual. 1037 pass |

### JUEGOS-FIX-1 — Vista de galería (grid) de la pestaña Juegos no renderiza tarjetas (hallado en vivo, 2026-08-27)

Al cambiar a vista de galería en Juegos (icono junto a CSV/JSON) con un
filtro activo ("Mario", 157 resultados), el contador de resultados es
correcto pero el área de tarjetas queda vacía (solo un emoji 🎮 centrado, sin
scroll ni error en consola visible). La vista de lista (tabla) sí funciona
con el mismo filtro. No investigado a fondo — candidatos: `games.js`/`main.js`
(`_renderGrid`/equivalente) no se dispara al cambiar de vista con un filtro ya
aplicado, o depende de datos (carátulas) que estas 157 entradas no tienen.
Pendiente de investigar causa raíz (`archivo:línea`) antes de arreglar. | `web/static/js/tabs/games.js`, `web/static/js/main.js` | ✅ PR [#243](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/243) — causa raíz doble: (1) `.games-grid` sin regla base `display:grid` en `app.css` (solo overrides `@media`), cada `.game-card` caía a ~1200px de alto apiladas; (2) bug separado y más grave: `onclick="openGamePanel(${JSON.stringify(g)...})"` en 6 sitios (galería, tabla, búsqueda global, recientes) solo escapaba `<`/`>`, nunca `"` — el primer `"` de `JSON.stringify` cerraba el atributo, dejando JS inválido. Abrir el panel de detalle estaba roto en toda la app, no solo en la galería. Fix: regla `display:grid` + reutilizar `_h()` (ya escapa comillas) en vez del `.replace` ad-hoc. Verificado en navegador con la biblioteca real

### GAMES-ALPHA-FILTER — Filtro por letra inicial en la pestaña Juegos

Con bibliotecas grandes por plataforma (cientos/miles de ROMs), el
desplegable de plataforma ya hace un primer corte pero dentro de una
plataforma sigue habiendo demasiado para hojear a mano. Barra alfabética
(A-Z + "#" para títulos que no empiezan por letra) sobre la lista, se
combina con búsqueda/género/año como un filtro más.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| GAMES-ALPHA-FILTER-1 | `get_games_paginated(initial=...)` filtra por la primera letra de `canonical_title` (o `original_filename` si no hay match), `"#"` agrupa lo que no empieza por A-Z | `database/repositories/games.py`, `web/builders/library.py`, `web/handlers/games.py` (`/api/games` + `/api/tag-bulk`) | ✅ 2 tests (`test_games_initial_filter.py`) |
| GAMES-ALPHA-FILTER-2 | Barra de botones A-Z/# sobre la tabla/galería, toggle (click de nuevo quita el filtro), se respeta en "Marcar para Anbernic" | `web/static/js/tabs/games.js` (`setInitialFilter`, `_renderAlphaBar`), `tab-games.html` | ✅ |

### CLOUD-FIX-1 — Error JS "badge is not defined" filtra al usuario en la pestaña Cloud (hallado en vivo, 2026-08-27)

Al abrir Cloud con Dropbox conectado pero sin remote de sync guardado
todavía, aparece una caja roja con el texto literal `badge is not defined —
Comprueba la configuración cloud de esta pestaña (rclone instalado y remote
conectado).` — es un `ReferenceError` de JS (variable `badge` no definida)
capturado por un `catch` genérico y mostrado como si fuera un mensaje de
validación normal, no un fallo del propio código. No investigado a fondo —
buscar el `catch` que arma ese mensaje y la variable `badge` sin declarar en
el flujo de estado de Cloud. | `web/static/js/tabs/sync.js` (o el módulo de
Cloud equivalente) | ✅ PR [#243](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/243) — causa raíz: `sync.js` llama a `badge()` esperando un helper global, pero `games.js` lo define sin `export` (módulos ES, scope propio por archivo). Fix: exportar `badge()` desde `games.js` e importarlo en `sync.js`, mismo patrón ya usado con `_platBadge`. Verificado en navegador: el log de sync ahora renderiza la tabla de 200 eventos con badges en vez del error

### SYNC-FIX-2 — Auto-sync ya no crashea (SYNC-FIX-1) pero reporta "15 errores" reales (hallado en vivo, 2026-08-27)

Tras aplicar SYNC-FIX-1 y reiniciar el servidor, el primer auto-sync que
corrió sin crashear terminó igualmente con `Ultimo sync: ... | Error: 15
errores` (visible en Cable Sync). Distinto del bug de aridad: ahora el daemon
sí se ejecuta y sí llega a intentar copiar/comparar archivos, pero algo falla
15 veces durante esa sincronización real. No investigado — el detalle de cada
uno de los 15 errores debería estar en el log de operaciones (botón "Ver log
de operaciones" en Cable Sync) o en `sync_log` (SQLite). | `sync/adb_transport.py` | ✅ PR [#242](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/242) — los 15 errores eran saves de Redream/AetherSX2 bajo `Android/data/<pkg>/` (scoped storage, Android 11+). `push()`: adb escribe el contenido pero el `fchown` final a la UID de la app falla sin root (exit code != 0 aunque el archivo llegó bien) — antes se borraba el `.part` a ciegas, ahora cae al chequeo MD5 existente y solo falla de verdad si el contenido no coincide. `pull()`: `Permission denied` es un bloqueo de lectura real sin margen de recuperación — mensaje ahora explica que es scoped storage, no un fallo transitorio. 4 tests nuevos

### SYNC-FIX-1 — Auto-sync crasheaba en cada intento por aridad incorrecta de `get_repo_fn` (hallado en vivo, 2026-08-27)

Al abrir la interfaz para las capturas del README apareció el banner de error
persistente `start_all.<locals>.<lambda>() takes 0 positional arguments but 1
was given`, visible también en Cable Sync ("Ultimo sync: ... Error: ..."), en
cada intento de auto-sync desde que arrancó el servidor. Prioridad absoluta
por ser bug de sync (regla del proyecto). Causa raíz: `start_all()`
(`web/daemons.py:262`) pasaba `lambda: repository` (0 argumentos) a
`_auto_sync_loop`/`_sd_card_sync_loop`, pero ambos ya esperan el contrato
`get_repo_fn(path)` de 1 argumento (`cable_sync_daemon.py:181,474`) que usa el
resto de la app (`web/builders/common.py::_repo_for_path`) para elegir la BD
correcta (PC vs Anbernic) — desajuste introducido en algún refactor de
multi-dispositivo que no llegó a `start_all()`/`serve()`. | `web/daemons.py`,
`web/server.py` | ✅ PR [#241](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/241) — rama `fix/auto-sync-daemon-get-repo-fn-arity` (worktree). `start_all()` recibe ahora `repository_android` y construye el mismo `get_repo_fn` de 1 argumento que `make_handler()`. 1 test nuevo de regresión (`test_daemons_start_all.py`). 1016/1019 pasan (3 fallos preexistentes no relacionados)

---

## Distribución / Release — → #207

Empaquetado, instalador y actualizaciones — llevar la app a un ejecutable
distribuible.

### Phase 6 — Distribution

| ID | Task | Estado |
|----|------|--------|
| PHASE6-1a | Crear `RetroVault.spec` — PyInstaller con static assets, templates y `tools/` bundled | ✅ `RetroVault.spec` empaqueta `web/static` (incluye partials HTML), `tools/` (adb, dlls, chdman) e hiddenimports de subpaquetes (build no verificado aún → ver 6-1b) |
| PHASE6-1b | Probar ejecutable en máquina limpia (sin Python) | 🟡 Validado en este equipo (build, smoke test de `serve`, instalación/desinstalación silenciosa); falta una prueba en una máquina realmente sin Python instalado. Corregidos hiddenimports obsoletos de `RetroVault.spec` (`response_builders`→`builders/`, `cable_sync_daemon` movido a `web/`) y las DLLs de ADB ahora son opcionales (adb.exe moderno no las necesita) |
| PHASE6-2a | Escribir script Inno Setup — shortcut + Add/Remove Programs | ✅ `installer/RetroVault.iss` — instalador por usuario (`PrivilegesRequired=lowest`), shortcuts en menú + escritorio, desinstalador limpio. Compilado y probado con Inno Setup 6.7.3 → `RetroVault-Setup.exe` (~15 MB) |
| PHASE6-2b | Bundlear DATs mínimos en el installer | ✅ (34 plataformas — `b4d2107`) |
| PHASE6-3a | Endpoint `/api/version` + check de actualizaciones al arrancar | ✅ `update_checker.py` + `GET /api/version` + banner en UI. 13 tests. PR #52. |
| PHASE6-3b | Descarga y aplicación de update desde GitHub Releases | ✅ `utils/update_installer.py` (`find_update_asset`, `download_update` con progreso, `launch_installer`); `web/handlers/update.py` (`/api/update/{status,download,apply}`); banner con botones "Descargar e instalar" / "Instalar y reiniciar" en `main.js`. Solo aplica a builds frozen (PyInstaller); en modo fuente solo enlaza al release. Aún sin probar contra un release real (ningún release publicado todavía — depende de 6-1b/6-2a). 30 tests nuevos. |
| PHASE6-4 | Decidir nombre final: Retro Vault vs Retro Companion | ✅ (Retro Vault confirmado — no-op, Día31) |

---

### DÍA37 — Distribuible completo + prueba en PC limpio (2026-07-02)

Objetivo cumplido salvo la validación en hardware ajeno: `RetroVault-Setup.exe`
autocontenido publicado en el release `v1.0.0` (detalle D37-1…D37-10 → archivo).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| D37-8 | **Prueba en PC limpio** — hardware test: instalar en máquina sin Python siguiendo la sección 0 de la guía; ejecutar checklist funcional (§5); valida PHASE6-1b | otro PC | ⬜ |

---

## RA, Scraper y Recomendador (SAGE) — → #208

Soporte a RetroAchievements, scraping de metadatos y el recomendador NLP
Retro Sage.

### SAGE — Soporte para Retro Sage (recomendador NLP)

Origen: `ROADMAP.md` de Retro Sage. SAGE-1 y SAGE-2 son **bloqueantes** para su
fase 2 (embeddings). Contexto adicional: `docs/ideas/propuestas-recomendador-nlp.md`.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| SAGE-1 | **Scraping masivo de descripciones** (bloqueante Sage v0.2) — completar las descripciones de la biblioteca por lotes desde la fuente del scraper puntual. Reanudable (no re-scrapear lo ya descargado), rate-limit razonable, descripciones visibles en `GET /api/export-history`. Hecho cuando >90% de los juegos tienen descripción no vacía en el export. | `database/repositories/metadata.py`, `web/handlers/scraper.py`, `web/builders/misc.py`, `tab-scraper.html`, `scraper.js` | 🟡 código listo (rama `feature/sage-1-mass-descriptions`): el job `/api/scrape` ya era reanudable+rate-limited; añadido modo `missing_descriptions` (re-scrapea metadata con descripción vacía sin machacar imágenes), cobertura en `/api/scrape-summary` + UI (hoy 70.0%). Pasada real 2026-07-07: 964 en cola, 860 match, 0 errores (tras fix `_loads_lenient`, PR #79) pero cobertura 70,0→70,1% — los re-scrapeados no tienen sinopsis en SS. Para >90% hay que resetear `metadata_scraped` de los ~4.700 sin match histórico y re-scrapear (~89% de acierto hoy), o usar otra fuente. **Experimento reset 2026-07-07: fallido** — la cola de 4.692 era basura no-juego (chips de romsets arcade, shaders RetroArch, restos de Papelera `$I*.iso`, firmware): 415 procesados, 6 match. Flags revertidos. **Camino real al >90%: limpiar la basura de la biblioteca** (junk-scan restaurado en PR #80) — al quitar ~4.700 no-juegos del denominador, 13.217/~14.150 ≈ 93%. **Limpieza ejecutada 2026-07-08 (Día39)**: 28.718 archivos borrados (chips arcade de `Unknown\`, ~15,4 GB) + fixes del clasificador (PRs #82/#83) → cobertura **70,1% → 84,3%** (13.136/15.591). **JUNK-REVIEW-1 resuelto (2026-08-14)**: la nota original (5.771 ZIPs, colecciones vs juegos individuales) estaba desactualizada — JUNK-SMART-1/2/3 ya la habían reducido a una cola mucho más pequeña y categorizada (1.522 archivos/1,18 GB en 6 categorías `review`, verificado con `/api/junk-scan` real). Decisión del usuario: borrar las 6 categorías. Aplicado vía `/api/junk-delete` (dry-run 1522/1522 OK, 0 fallos, luego real → `_descartados/`, AUD-3, deshacible 30 días — hasta ~2026-09-13). Rescan: 14.147→13.746 filas, cobertura **72,1%→75,5%**. Sin cambios de código, solo decisión + ejecución sobre la biblioteca real. Queda re-scrape de los sin descripción restantes para >90% |
| SAGE-2 | **Migración `genres_list` / `players` persistidos** (bloqueante Sage v0.2) — persistir ambos campos en la BD (hoy derivados al vuelo) con backfill de registros existentes, y exponerlos en el export. Hecho cuando aparecen estables en `/api/export-history` y el contrato queda documentado en `play_history.py`. Detalle: `docs/ideas/propuestas-recomendador-nlp.md`. | `database/`, `database/repositories/play_history.py` | ✅ columnas `genres_list`/`players` en `game_metadata` (`_METADATA_MIGRATIONS`, `schema.py`); backfill de `genres_list` desde `genre` para filas ya scrapeadas (`_migrate_genres_list_backfill`) — `players` no tiene fuente local, queda NULL hasta re-scrapear. `upsert_metadata()` acepta ambos campos; los 3 call-sites (`web/handlers/scraper.py` ×2, `cli.py`) ya pasan `result.genres_list`/`result.players`. Expuestos en `GET /api/export-history` (query + payload). Contrato documentado en `database/repositories/play_history.py` + docstring del endpoint. 4 tests nuevos (`tests/test_sage2_genres_players.py`), 949 pass |
| SAGE-3 | **Registro de recomendaciones mostradas/clicadas** (futuro, Sage v0.4) — para el bucle de feedback de Sage: registrar qué recomendaciones se mostraron en el panel y cuáles se clicaron, y exponerlo (export o endpoint nuevo). **No implementar todavía**: el diseño se negocia cuando Sage llegue a v0.4. | — | ⬜ |
| SAGE-4 | **Construir el recomendador en sí (aún sin empezar)** — SAGE-1/2 solo preparan los datos; ninguna propuesta de `docs/ideas/propuestas-recomendador-nlp.md` está implementada todavía. Camino recomendado por el propio documento: Propuesta A (Smart Filter con scoring, sin ML) + Propuesta C (perfil desde favoritos/completados) como MVP de una sesión, 0 dependencias nuevas; B (TF-IDF) y D (embeddings locales) quedan como extensión/salto cualitativo; E (chatbot Claude API) como bonus opcional | `src/rom_manager/recommender/` (nuevo) | ⬜ sin diseñar |

---

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: JUEGOS-UX-1..9 (logros individuales por juego + playtime automático PC/Anbernic — completo, 2026-07-13).

---

## Validación en hardware — → #211

Tareas que requieren consola real o SD card para verificarse — no ejecutables
solo con datos sintéticos.

### Hardware validation (requires console or SD card)

| ID | Task |
|----|------|
| V1 | SD card auto-sync — configure `anbernic_root`, insert SD, verify banner + log |
| V2 | Two-database migration — Settings → "Migrate DB" → verify separate PC/Android counts |
| V3 | Inbox end-to-end — configure `inbox_path`, drop ZIP, verify extraction + rename + move |
| V4 | RetroAchievements with real API key |
| V5 | Termux guide on console — prereq for WiFi sync |
| B1-hw | Android renamer doesn't reduce queue — test with SD inserted |

---

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: VAL-FIX-1..7 (hallazgos de la validación con consola real — completos, 2026-07-13/2026-07-20).

---

## Perfil de dispositivo — provisioning con un botón — → #238

Petición del usuario (2026-08-25): comprar un PC nuevo o una Anbernic nueva y
que se configuren todos los emuladores tras pulsar un botón.

**Idea central:** la config de un emulador es texto en disco. No hace falta un
motor de configuración — ya existe un motor de sync de archivos con resolución
de conflictos (`src/rom_manager/sync/`, `SyncEngine.kt`). Los `.cfg` son
archivos más, con dos diferencias frente a los saves: son **direccionales**
(restore, no merge) y llevan **rutas absolutas** que hay que reescribir.
Lo único nuevo de verdad es la tokenización (`"E:/…/saves"` → `"{SAVES}"` al
guardar, sustitución al restaurar).

**Perfil:** `RetroSync/profiles/<device_id>.json` + `…/<device_id>/files/`,
junto a los saves. Versionado por fecha, nunca sobrescrito — mismo criterio
que ya se usa en saves.

**Diseño de DEVPROFILE-1..4** (catálogo de plataformas único + tokenizador +
reutilización de `sync_sources`, verificado contra el código real): ver
`Tareas/Roadmap-DEVPROFILE-1-4.md`.

**Diseño de DEVPROFILE-5/6** (botones de restauración PC/Android,
verificado contra el código real — incluye un hueco real encontrado: nadie
sube el manifiesto de perfil al remoto todavía): ver
`Tareas/Roadmap-DEVPROFILE-5-6.md`.

| ID | Task | Esfuerzo | Estado |
|----|------|----------|--------|
| DEVPROFILE-0 | **Bloqueante**: verificar dónde vive `retroarch.cfg` en la RG556 (por cable, `tools/adb.exe`) | XS | ✅ resuelto 2026-08-25 en hardware real — **NO accesible sin root**: `/data/data/com.retroarch/` da `Permission denied`, `run-as` falla (`package not debuggable`, build Play Store), y no hay ningún `retroarch*.cfg` en almacenamiento público. Sí son accesibles `config/<Core>/*.opt`, `retroarch-core-options.cfg`, `config/remaps/` y `system/`. Ver comentario en #238 |
| DEVPROFILE-1 | `docs/architecture/platforms-cores.md` (prosa) → JSON de datos, fuente única de `lpl_generator.py`, `esde/systems_generator.py`, `bios_checker.py` y la asignación de core por defecto | S | ✅ 2026-08-31 — ver `Tareas/Roadmap-DEVPROFILE-1-4.md` §2 para el detalle. `lpl_generator.py` no necesitaba cambio (usa `DETECT` a propósito, no un hueco real). Migrados `bios_checker.KNOWN_BIOS` (22 entradas) y `systems_generator._SYSTEMS` (20 cores PC) a `platforms.toml` (`[[bios]]` / `[cores.pc]`), vía `platform_detector.bios_definitions()`/`pc_cores_by_system()`. `mame`/`fbneo` mantienen listas de cores distintas a propósito (comparten canónico "Arcade" pero no deben fusionarse). Verificado con 4 tests nuevos (`tests/test_systems_generator.py`) + paridad exacta de los 22 valores de BIOS; suite completa en verde (1094 pasan, mismos 3 fallos preexistentes de ADB sin relación) |
| DEVPROFILE-2 | Escribir `savefile_directory` / `savestate_directory` / `sort_savefiles_by_content_enable` / `sort_savestates_by_content_enable` en `retroarch.cfg` del **PC únicamente** (en Android no es viable sin root, ver DEVPROFILE-0). Sigue siendo el ítem de más valor en el lado PC: hoy el sync *adivina* el layout; escribir esas claves lo hace idéntico por construcción → prevención de pérdida de progreso, pilar 3 | S | ✅ 2026-09-01 — ver `Tareas/Roadmap-DEVPROFILE-1-4.md` §3. `retroarch_cfg_writer.py` (`apply_savefile_layout`/`default_savefile_layout`) + botón manual "Aplicar layout de saves" en Settings (`POST /api/retroarch-apply-savefile-layout`), destino `library_root/saves`+`/states` (mismo convenio que `sync.saves_remote`/`states_remote`). 11 tests en verde |
| DEVPROFILE-3 | Tokenizador de rutas: `{ROMS}` / `{SAVES}` / `{SYSTEM}` al guardar, sustitución por las del dispositivo destino al restaurar | S | ✅ 2026-09-01 — `services/path_tokenizer.py` (`tokenize`/`resolve`, puras). 6 tests. Ver `Tareas/Roadmap-DEVPROFILE-1-4.md` §4 |
| DEVPROFILE-4 | Manifiesto Tier A + backup del perfil al remoto — **alcance recortado tras DEVPROFILE-0**: `config/<core>/*.cfg`, `retroarch-core-options.cfg`, `config/remaps/`, `autoconfig/`, shaders, `.opt` en bulk, BIOS/`system/`; `retroarch.cfg` solo en el lado PC. Standalones de PC sin cambio: `duckstation/settings.ini`, `PCSX2/inis/`, `Dolphin/Config/`, `es_systems.cfg` | M | ✅ 2026-09-01 — backend (`services/device_profile.py`, 5 tests) + pantalla de Settings "Perfil del dispositivo" (`GET /api/device-profile-detect`, reusa `POST /api/config` con `sync.sources` para guardar). Rama `feature/devprofile-4a-settings-ui`. Ver Roadmap §5 |
| DEVPROFILE-5 | Botón PC — `rommgr restore`: `download-tools.ps1` → `config.toml` desde el perfil (sustituye media `wizard.py`) → Tier A con rutas reescritas → regenerar Tier B → `bios_checker` y reportar lo que falta | M | ✅ 2026-09-01, ver `Tareas/Roadmap-DEVPROFILE-5-6.md` — 5a (subir manifiesto) + 5b-5f (comando `rommgr restore` completo) en la misma rama `feature/devprofile-5a-export-manifest`. `restore` (nuevo subparser en `cli.py`) descarga `device-profile.json` (`RcloneTransport.download`, fallback-remote), pide `library_root`/ruta de RetroArch (reusa `_ask`/`_ask_yn`/`_detect_tool` de `wizard.py`), resuelve los tokens con `import_profile_sources()` (ya existía, sin caller hasta ahora) y escribe `config.toml` con `write_config_toml()` — mismo aviso de sobreescritura que el wizard. Crea cada `local_dir` con `mkdir(parents=True)` y llama a `sync_saves()` por fuente (dry-run por defecto, `--apply` para bajar de verdad — mismo patrón que `rommgr sync`). Si hay RetroArch configurado y ES-DE está instalado, regenera `custom_systems/es_systems.xml` con `generate_es_systems_xml()`. Termina con `check_bios()` sobre `library_root`/`library_root/bios`/`retroarch/system` y lista las BIOS requeridas que faltan. Test nuevo `tests/test_cli_restore.py` (manifiesto+config.toml de punta a punta con `RcloneTransport._run` fake, sin tocar rclone real). Suite completa 1127 en verde |
| DEVPROFILE-6 | Botón Android — "Restaurar este dispositivo" tras el login de Dropbox: restaura core options/remaps/BIOS (no el cfg global, ver DEVPROFILE-0); el sync periódico ya arranca solo (ANDROID-SYNC-12). El Core Downloader sigue siendo manual | S | ⬜ alcance reducido por DEVPROFILE-0 |
| DEVPROFILE-7 | Detección de deriva: comparar el `retroarch.cfg` vivo contra el del perfil y avisar si cambian los directorios de save ("tus partidas nuevas no se están sincronizando"). Sale gratis una vez existe DEVPROFILE-4 | S | ✅ 2026-09-01 — `_handle_retroarch_check()` compara `savefile_directory`/`savestate_directory` contra `default_savefile_layout(library_root)` (convenio D2, ya existente desde DEVPROFILE-2) y añade `savefile_drift`+issue accionable si no coincide. Sin endpoint ni UI nuevos — reusa `/api/retroarch-check` y el panel de issues ya existente. **Detectó deriva real en este PC**: `savefile_directory` apuntaba a `E:\ROMs\saves` (ruta obsoleta) en vez de `E:\Carpetas anbernic\saves` — pulsar "Aplicar layout de saves" en Settings lo corrige. 2 tests (`tests/test_retroarch_check_drift.py`) |
| DEVPROFILE-8 | Restaurar lo que evita retrabajo caro en un PC nuevo: BD SQLite (evita rehashear la biblioteca entera, horas), caché de ScreenScraper (cuota diaria de API) y DATs No-Intro/Redump | S | ⬜ |
| DEVPROFILE-9 | Datos de usuario que deberían seguirte entre dispositivos: `content_history.lpl` (recientes), `content_favorites.lpl`, `.lrtl` (playtime, ver MEJ-1), credenciales RA (`cheevos_*`, en almacenamiento cifrado) | S | ⬜ |

**Fuera de alcance (no automatizable, decidido 2026-08-25):** instalar
RetroArch o descargar cores en Android (viven en `/data/data/com.retroarch/`,
sin root no se entra); emparejar mandos Bluetooth y calibrar sticks; instalar
emuladores standalone en PC (parcial vía `winget`/`scoop` para RetroArch,
Dolphin, PCSX2 y DuckStation — no MAME ni Flycast).

---

## Roadmap — Ideas futuras — → #212

Propuestas del usuario sin diseñar todavía. Roadmap general de lo que queda
vivo aquí (STORAGE-MGR validación + CFG-PORGAME + MODS-AUTO), para trocear
en sesiones por día: `Tareas/Roadmap-212-Ideas-Futuras.md`.

### ROADMAP-IDEAS — Propuestas del usuario (2026-08-13, sin diseñar aún)

| ID | Idea | Notas |
|----|------|-------|
| CFG-PORGAME | Configuraciones específicas por juego (core options, overrides RetroArch), editables desde el PC | 🟢 Implementado 2026-08-18 (alcance decidido con el usuario, ver `Tareas/Roadmap-212-Ideas-Futuras.md` frente B) — "verificado" = confirmado por el propio usuario en el emulador, no importado de fuente externa (no existe ninguna para RG556). Hecho: auto-detección de `ra_config_dir` en PC y Android vía ADB (`_detect_retroarch_install()`/`_detect_android_ra_config_dir()`, `web/handlers/config.py`, botón "🔍 Detectar" en Settings y en Cable Sync — B0-3a/b/c/d, CFG-PORGAME-1/5); listado de overrides PC/Android con endpoint (`GET /api/retroarch-overrides`) y panel "⚙️ Overrides" en Colección (CFG-PORGAME-4/6); editor de un `.opt` (lectura/escritura sin interpretar claves) integrado en el mismo panel, cada core es un enlace que abre un textarea editable (CFG-PORGAME-7); copia puntual PC↔Android por juego (CFG-PORGAME-3/8/9) — botón ⇄ solo en los 8 cores compartidos (FCEUmm/Gambatte/mGBA/melonDS/Genesis Plus GX/Yaba Sanshiro 2 Pro/PPSSPP/Stella 2023), con backup automático `<rom>.opt.bak-<timestamp>` si el destino ya tiene override. Frente CFG-PORGAME completo (mergeado a `develop` vía PR #223) salvo CFG-PORGAME-10 (validación en RG556 real, sin consola a mano — bloqueado hasta tener el dispositivo) |
| MODS-AUTO | Añadir e instalar mods automáticamente — viable para PS1/PS2/N64/GameCube (formatos de parche/mod más estandarizados: `.pnach`, ISO patching, texture packs); no viable para consolas muy antiguas (sin ecosistema de mods) | Requiere investigar formato de mods por emulador/plataforma antes de diseñar; alcance grande, candidato a su propia fase de roadmap |
| STORAGE-MGR | Gestor de almacenamiento — decidir y borrar en bloque (PC, Anbernic o ambos) desde un menú dedicado | 🟢 Diseñado e implementado 2026-08-14, ver sección propia más abajo — subtareas STORAGE-MGR-1..5 |
| FTP-PICK | Elegir ROMs desde la Anbernic sin pasar por Cable Sync/ADB | 🟢 Backend HTTP implementado y probado 2026-08-29 (FTP-PICK-1); pantalla en la app Android (ANDROID-SYNC) implementada y compilada con `gradlew test assembleDebug` reales 2026-08-29 (FTP-PICK-2) — no se usó FTP, descartado a mitad de sesión. Falta solo validación manual contra hardware/emulador. Ver sección propia más arriba (Pilar 3) |
| GHA-OPT-1 | Optimizar el flujo de Claude Code GitHub Actions (`claude.yml` / `claude-code-review.yml`, instalados 2026-08-14 vía `/install-github-app`) | Repo público → minutos de runner gratis y autentica con `CLAUDE_CODE_OAUTH_TOKEN` (consume cuota Pro/Max, no API pay-as-you-go) — el coste real a acotar es esa cuota, no dinero. ✅ implementado (rama `chore/gha-opt-1-optimize-claude-workflows`, 2026-08-17): evidencia real antes de tocar nada — `claude-code-review.yml` se había disparado 5 veces seguidas sobre la misma rama en una sola sesión (2026-08-14, cada `synchronize` relanzaba la revisión sin cancelar la anterior). (a) `concurrency` por nº de PR + `cancel-in-progress: true` en `claude-code-review.yml`; (b) `paths-ignore` (`Tareas/**`, `**.md`) para no revisar PRs de solo-backlog, y `if: draft == false` para no revisar mientras el PR sigue en borrador; (c) `--max-turns 30` en `claude_args`; (d) mismo `concurrency` en `claude.yml` pero con `cancel-in-progress: false` (cada mención `@claude` es una petición distinta del usuario, se encola en vez de perderse) + `--max-turns 50` propio (más holgado que la revisión: puede implicar tareas más largas); (e) `CLAUDE.md` revisado — 145 líneas / ~7 KB, ya conciso, sin cambios |
| RA-DL-LINK | En el informe de RA (juegos sin logros en tu versión pero sí en otra), botón "copiar link de descarga" por juego, pensado para pegarlo en JDownloader | Idea del usuario 2026-08-29; el propio usuario advierte que meter un LLM local para generar el link sería costoso y poco fiable — valorar alternativa sin LLM (¿el link ya es derivable del nombre canónico + fuente conocida?) antes de descartarlo |
| TRUST-MODE | Simplificar el flujo de primera vez: aplicar todo de golpe y luego dejar que el usuario navegue las tabs revisando (o confiando sin revisar) los cambios ya hechos, en vez de plan→revisión manual→apply | Idea del usuario 2026-08-29; **tensión con INBOX-FIX-4** (`archivo.md`): decisión ya tomada 2026-07-23 de NO auto-aplicar y mantener `rommgr plan` siempre antes de `apply` — replantear con el usuario antes de diseñar, no revertir esa decisión sin más |
| ESDE-CONFIG-CHECK | Confirmar con el usuario qué falta exactamente de integración con ES-DE — el proyecto ya genera `gamelist.xml` (`scraper/gamelist_writer.py`), metadata Pegasus (`scraper/pegasus_writer.py`) y sistemas/cores (`esde/systems_generator.py`, usado hoy para iiSU en IISU-CONFIG-1) | Idea del usuario 2026-08-29 asumía que no existía nada — puede que el hueco real sea solo `es_systems.cfg`/rutas de ES-DE específicas (ver DEVPROFILE-4, "sin cambio") |
| LIBRARY-MANAGER-UI | Pantalla única "gestionar ambas bibliotecas a discreción" — copiar y borrar PC↔Anbernic con control fino, en vez de repartido entre Cable Sync (copiar), `ANBERNIC-PICK` (marcar) y `STORAGE-MGR` (borrar en bloque, archivado). El usuario pide explícitamente esto tras no encontrar cómo hacerlo hoy (2026-08-29) | Fusiona 3 mecanismos ya existentes en una sola UI — no es una feature nueva de backend, es una consolidación de UX; valorar junto con `ANBERNIC-PICK-7` (sync guiado) y `GAME-BLOCKLIST` (borrado permanente) antes de diseñar, pueden compartir la misma pantalla |

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: STORAGE-MGR-1..5 (gestor de almacenamiento PC/Android, borrado en bloque — completo y validado en hardware, 2026-08-14/2026-08-29).

---

## Transversal — Calidad de código, DX y referencia (sin epic)

Auditorías y limpieza que cruzan varios pilares a la vez (calidad de código,
onboarding, tests) — no tienen una épica de GitHub propia porque no son
roadmap de producto. Mayoría ya completada; se mantiene como referencia
histórica.

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: MEJORAS MEJ-1..6, AUD-1..6, TEST-CLEAN-1..3 + TEST-GAP-1, ONB-1..9, REV43-1..53 (calidad de código, onboarding, tests — completas, 2026-07-02 a 2026-07-15).

---

### User actions (no code needed)

| ID | Task |
|----|------|
| STRUCT-4 | Configure RetroArch PC: Saving → Savefile Directory → `E:\Carpetas anbernic\saves\` |
| STRUCT-3 | Update `config.toml`: `local_dir = "E:\\Carpetas anbernic\\saves"` (after STRUCT-4) |
| ES-1 | Download `genesis_plus_gx` core in RetroArch → Online Updater |
| ES-2 | Configure Citra (3DS) in EmulationStation |
| PC2-1 | Añadir el segundo PC (otra ciudad) al sync de saves vía Dropbox/rclone — seguir `Tareas/Guia-Segundo-PC.md` (no requiere código; NO sincronizar las BDs SQLite) |

---

### GBA-MISPLACED-1 — Archivos de otras plataformas mal ubicados en `gba/` con metadatos corruptos (hallazgo 2026-08-30)

Origen: al intentar limpiar "duplicados GBA sin RA" (pedido usuario tras DUP-REGION-1),
la cola de revisión mostraba grupos que resultaron NO ser duplicados de GBA en absoluto,
sino archivos de otras plataformas mal ubicados físicamente en `gba/`/`dreamcast/`, con
`platform`/`canonical_title` corruptos por el mismo bug de matching por título ambiguo
que ya afectaba a los `.chd` (fallback de título sin desambiguar por plataforma cuando
la extensión es ambigua — `.zip`/`.chd`/`.iso` no están en `PLATFORM_BY_EXTENSION`).
Confirmado que viene de marzo/abril 2026 (`created_at`/`updated_at` de las filas), no de
esta sesión. Verificado con `_build_review_queue` que **library_android.db no tiene esta
corrupción** — es solo del lado PC.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| GBA-MISPLACED-1a | **Corregido 2026-08-30**: 33 filas `.chd` con `platform` incorrecto en `library_pc.db` (23 en `psx/`, 9 en `arcade/`, 1 en `ps2/`) — `platform`/`canonical_title`/`match_confidence`/`catalog_source` reseteados al valor correcto derivado de la carpeta (`detect_platform()`, ya verificado fiable). Backup previo en `.rommgr/backup_chd_platform_fix_2026-08-30/library_pc.db` | `library_pc.db` (datos, no código) | ✅ corregido, backup guardado |
| GBA-MISPLACED-1b | **Corregido 2026-08-30**: 10 filas con `platform='Game Boy Advance'` y tamaño imposible para un cartucho GBA (>40MB — hasta 2,8 GB) reseteadas a `platform=NULL`/`canonical_title=NULL` (no se adivina la plataforma correcta en la fila, solo se limpia el dato corrupto). Backup en `.rommgr/backup_chd_platform_fix_2026-08-30/library_pc_before_gba_mismatch_fix.db`. Identificación real de cada archivo (abriendo el zip/leyendo el PVD ISO9660) — **plataforma correcta, sin mover el archivo todavía**: Tony Hawk's American Sk8land (contiene `.nds` → Nintendo DS), Crash of the Titans (ya estaba en `psp/`, solo el tag estaba mal → PSP), SEGA Rally Championship `.chd` (metadata `Tag='CHT2'` — CD-ROM estándar, no GD-ROM → **Sega Saturn** confirmado, no Dreamcast), Jet Grind Radio `.chd` (metadata `Tag='CHGD'` — formato GD-ROM, exclusivo de **Dreamcast** → confirmado), Tony Hawk's Pro Skater 3 (iso con volumen `SLUS_20013` → **PS2** confirmado), Harry Potter Prisoner of Azkaban (iso 3,5GB, con `SYSTEM.CNF`+`SLES_` → **PS2**, descarta PS1/GameCube por tamaño/marcadores), Harry Potter Chamber of Secrets ×2 copias idénticas del mismo iso 563MB (`SYSTEM.CNF`+`SLES_`/`SLUS_`/`SLPS_` → **PS2**) + 1 copia distinta con `.bin`/`.cue` (**PSX**), Harry Potter Sorcerer's Stone (`.bin`/`.cue` → **PSX**) | `library_pc.db` (datos) | 🟡 metadatos limpiados; reubicación física de los 10 archivos pendiente |
| GBA-MISPLACED-1c | **Hallazgo adicional, mismo origen**: 3 sha1 duplicados que parecían "GBA vs otra copia" en la cola de duplicados son en realidad romsets arcade/NES con una copia extra mal colocada en `gba/`/`dreamcast/` — **TMNT** (romset MAME de 16 chips con nombres tipo `963-x21.j15`, copia idéntica en `gba/TMNT (USA) (En,Fr,Es).zip` + restos sin organizar en `Unknown/arcade/tmnt.zip` y `Unknown/MAME/tmnt.zip` — **ninguna copia bien organizada en `arcade/` todavía**), **Super Donkey Kong 2** (cartucho NES/Famicom bootleg, un `.nes` dentro del zip — copia mal puesta en `gba/Super Donkey Kong 2 (Japan).zip`, resto sin organizar en `Unknown/NES-Famicom/~Unlicensed~ Super Donkey Kong 2/`), **Ganryu** (romset arcade de 5 chips tipo `252-c1.c1` — copia mal puesta en `dreamcast/Ganryu (USA, Japan) (Unl).zip`, pero esta SÍ tiene copia correcta ya en `arcade/Ganryu (USA, Japan) (Unl).zip`, más 2 copias sin organizar en `Unknown/arcade/` y `Unknown/MAME/`). No es un problema de "duplicados sin RA" — es contenido que nunca pasó bien por el pipeline de organizar/Inbox | `gba/TMNT...`, `gba/Super Donkey Kong 2...`, `dreamcast/Ganryu...`, restos en `Unknown/` | 🔴 identificado, sin mover ni limpiar |
| GBA-MISPLACED-2 | **✅ Arreglado 2026-09-03** (rama `fix/catalog-match-ambiguous-extension`), mismo bug que `CATALOG-MATCH-BUG-1`. `_match_by_title()` ahora recibe `source_path` (enchufado en los 4 call sites reales: `cli.py:665`, `web/inbox_pipeline.py:849,1019`, `web/handlers/scan.py:550`) y, cuando `ext_platform` es `None` (extensión ambigua) y hay >1 hit, usa `detect_platform(Path(source_path))` — la carpeta contenedora real — como criterio de desempate ANTES de caer a `candidates[0]`. Solo actúa si los hits pertenecen a plataformas distintas (para eso sirve `detect_platform`, que da la plataforma, no la región). **Bug relacionado encontrado y arreglado de paso**: `_load_dir()` (`catalog/matcher.py:139-152`) llamaba a `load_nointro_dat()` directamente (solo XML) en vez del dispatcher `load_dat_file()` (ya existente, usado en `web/handlers/games.py` y `catalog_loader.load_dat_directory()`) — descartaba en silencio cualquier `.dat` en formato clrmamepro (texto plano), **21/271 catálogos No-Intro y 9/22 Redump reales**, incluyendo Game Boy, GBA, NES, PS1, PS2, GameCube, Wii... Verificado en vivo contra `library_pc.db` (`E:\Carpetas anbernic`, backup previo en `.rommgr/backup_catalog_match_fix_2026-09-03/`): `megadrive/deer hunter.bin` (el caso original de `CATALOG-MATCH-BUG-1`) pasa de `platform=Game Boy Color, confidence=low` (equivocado) a `platform=Sega Mega Drive, confidence=high` (SHA1 exacto, ahora que el DAT de Mega Drive carga). Re-match de las 36.973 filas sin resolver/baja confianza de la biblioteca real: antes del segundo fix (loader) 53 altas/17656 medias/9337 bajas/9927 sin match con errores de parseo en 30 `.dat`; después, 0 errores, 178 altas/17686 medias/9381 bajas/9728 sin match. Tests nuevos: `test_ambiguous_extension_prefers_platform_of_containing_folder`, `test_matcher_loads_clrmamepro_format_dat`. 1142/1142 verde, ruff limpio | `catalog/matcher.py:10,146,196-283`, `cli.py:665`, `web/inbox_pipeline.py:849,1019`, `web/handlers/scan.py:550` | ✅ arreglado, sin PR todavía |

**Identificación completa de los 13 archivos** (ninguno movido todavía, solo metadatos de BD limpiados):

| Archivo | Ubicación actual | Plataforma real |
|---|---|---|
| Tony Hawk's American Sk8land (USA).zip | gba/ | Nintendo DS |
| Crash of the Titans (USA) (En,Fr).iso | psp/ (ya correcta) | PSP |
| SEGA Rally Championship (Japan) (En).chd | gba/ | Sega Saturn |
| Jet Grind Radio (USA).chd | gba/ | Dreamcast |
| Tony Hawk's Pro Skater 3 (USA, Europe).zip | gba/ | PS2 (SLUS_20013) |
| Harry Potter and the Prisoner of Azkaban....zip | gba/ | PS2 |
| Harry Potter and the Chamber of Secrets (USA, Europe)....zip | gba/ | PS2 |
| Harry Potter and the Chamber of Secrets (Europe).zip | gba/ | PS2 (mismo iso que el anterior) |
| Harry Potter and the Chamber of Secrets (USA) (En,Fr,Es).zip | gba/ | PSX (bin/cue) |
| Harry Potter and the Sorcerer's Stone....zip | gba/ | PSX (bin/cue) |
| TMNT (USA) (En,Fr,Es).zip | gba/ | Arcade/MAME (romset "963") |
| Super Donkey Kong 2 (Japan).zip | gba/ | NES/Famicom (bootleg) |
| Ganryu (USA, Japan) (Unl).zip | dreamcast/ | Arcade/MAME (romset "252") |

**Movidos 2026-08-30** (backup previo en `.rommgr/backup_chd_platform_fix_2026-08-30/library_pc_before_file_moves.db`): los 13 archivos de la tabla, a `ps2/`, `psx/`, `nds/`, `saturn/`, `dreamcast/`, `arcade/`, `nes/`. El de `dreamcast/Ganryu...` era duplicado exacto de uno ya en `arcade/` → descartado a `_descartados/` en vez de moverlo (para no sobreescribir). El re-escaneo de `gba/` reveló **12 archivos más** con el mismo problema (mal ubicados pero con `platform`/extensión ya correctos: 4× GameCube `.rvz`, 3× SNES `.sfc`, 1× GBC `.gbc`, 1× N64 `.z64`, más las versiones sueltas sin comprimir de Super Donkey Kong 2/Tony Hawk Sk8land) — movidos también; 6 de ellos ya tenían una copia en su carpeta destino (`Breath of Fire II`, `Donkey Kong Country`, `Earthworm Jim 2`, `Magi Nation`, `Ready 2 Rumble Boxing`, mismo tamaño → duplicado exacto, descartado) salvo `Mario Power Tennis` (tamaño distinto al ya existente en `gamecube/` → descartado sin sobreescribir, requiere revisión manual de cuál es la buena). **`gba/` verificado limpio**: 0 filas con plataforma distinta de GBA tras el movimiento. `arcade/` y `psx/` recibieron 1 archivo nuevo cada uno (TMNT sin organizar, restos en `Unknown/` pendientes de una limpieza aparte).

---

### GAMECUBE-DISC-BUG-1 — Juegos multi-disco de GameCube marcados como "duplicado" (bug serio, riesgo real de pérdida de datos)

Origen: pedido del usuario de revisar `gamecube/` por duplicados. `_build_review_queue`
mostró 6 grupos — **5 eran falsos positivos**, no duplicados reales.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| GAMECUBE-DISC-BUG-1a | **Corregido 2026-08-30**: `_DISC_SUBFOLDER_PLATFORMS` (`planner/operation_planner.py:19-26`) excluía GameCube desde INBOX-ORPHAN-3 ("dumps single-file"), y esa misma exclusión hacía que `apply_ra_conflicts` (`services/ra_duplicates_service.py:367,424`) no protegiera los GameCube multi-disco. Arreglo aplicado: nuevo `_MULTI_DISC_RISK_PLATFORMS = _DISC_SUBFOLDER_PLATFORMS \| {"gamecube"}` (`planner/operation_planner.py`), concepto separado de "vive en subcarpeta propia" — `ra_duplicates_service.py` ahora usa esta lista (no `_DISC_SUBFOLDER_PLATFORMS`) para el guard `skipped_multi_disc`. Verificado contra la BD real: los 4 conflictos reales (Twin Snakes disk, Resident Evil Zero disk, Resident Evil collision, Resident Evil 4 collision) ahora caen en `_MULTI_DISC_RISK_PLATFORMS` (`"gamecube" in _MULTI_DISC_RISK_PLATFORMS` → True) y quedarían en `skipped_multi_disc`, no auto-resueltos. Test de regresión nuevo `test_collision_on_gamecube_multi_disc_is_never_auto_resolved` en `tests/test_apply_ra_conflicts.py` (mismo patrón que el test PSX existente). 1073 tests, 1070 en verde (3 fallos preexistentes no relacionados, ver INBOX-ORPHAN-3). **Hallazgo nuevo durante la verificación, sin arreglar → ver GAMECUBE-DISC-BUG-1d** | `planner/operation_planner.py:19-33`, `services/ra_duplicates_service.py:339,367,424`, `tests/test_apply_ra_conflicts.py` | ✅ corregido 2026-08-30 |
| GAMECUBE-DISC-BUG-1b | **Corregido 2026-08-30**: mismo bug de plataforma-por-título-ambiguo que GBA-MISPLACED — 7 archivos `.rvz`/`.zip` mal etiquetados o mal ubicados relacionados con `gamecube/`: `hulk.zip` (en `gamecube/`, tag `MAME` → movido a `arcade/`, ya existía copia igual → descartado), `Luigi's Mansion (USA).rvz` (en `3ds/` — un `.rvz` nunca es 3DS → movido a `gamecube/`), `Resident Evil (World) (Proto 1) (Disc 1/2).rvz` (en `gbc/` → movidos a `gamecube/`), `Resident Evil 3 - Nemesis (Europe).rvz` (en `psx/` → movido a `gamecube/`), `Pikmin (Europe) (Wii).rvz` y `Pikmin 2 (Japan) (GCN) (Virtual Console).rvz` (en `wii/`, tag `GameCube` → son relanzamientos de Virtual Console, se quedan en `wii/` pero el tag se corrigió a `Wii`). Además, `Hulk (Germany).zip` en `gamecube/` (998KB, imposible para un disco GC) resultó ser — otra vez — el mismo romset arcade "The Incredible Hulk" (sha1 idéntico a `arcade/hulk.zip`) → descartado, ya había copia correcta | `library_pc.db` (datos), sistema de archivos | ✅ corregido |
| GAMECUBE-DISC-BUG-1c | **Descartado por el usuario 2026-08-30** — no se va a aplicar la recomendación (quedarse con el `.rvz`, descartar el `.iso`) sin la verificación byte a byte equivalente a `compute_psx_ra_hash`. Sigue habiendo 2 copias de `Metroid Prime 2 - Echoes (Europe)` en `gamecube/`, sin decisión pendiente por ahora | `gamecube/Metroid Prime 2 - Echoes (Europe) (En,Fr,De,Es,It).iso`, `....rvz` | ⬜ descartado, sin acción |
| GAMECUBE-DISC-BUG-1d | **Corregido 2026-08-30**: `_MULTI_DISC_RISK_PLATFORMS` comparaba `game.platform.lower()` contra códigos cortos (`"psx"`, `"saturn"`, `"ps2"`), pero `games.platform` en producción guarda el nombre de catálogo completo (`platforms.toml`): `"PlayStation"`, `"Sega Saturn"`, `"PlayStation 2"` — solo `"GameCube"`/`"Dreamcast"`/`"Wii"` casaban por casualidad. Arreglo: `_MULTI_DISC_RISK_PLATFORMS` (`operation_planner.py:28-45`) ahora es su propio frozenset con los 6 nombres de catálogo reales (`"playstation"`, `"playstation 2"`, `"sega saturn"`, `"dreamcast"`, `"gamecube"`, `"wii"`), desacoplado de `_DISC_SUBFOLDER_PLATFORMS` (que sigue comparando nombres de carpeta reales — `"psx"`, `"saturn"`... — ese uso es correcto y no se tocó, evita cambiar el layout de subcarpetas de la biblioteca real). Verificado contra la BD real: además de los 4 de GameCube, el guard ahora protege sets PSX/PS2 que **antes se resolvían en silencio por RA sin protección** — `Koudelka` (USA) Disc 2/3/4, `Tales of Destiny II` Disc 2, `Driver 2 - Back on the Streets` Disc 2, `Shadow Hearts - Covenant` (PS2) Disc 2, entre otros conflictos `disk`/`collision` de PlayStation/PlayStation 2 en la cola real. Tests: fixture existente `test_collision_on_disc_platform_is_never_auto_resolved` corregido (usaba `platform="psx"`, dato irreal — ahora `"PlayStation"`) + test nuevo `test_collision_on_ps2_multi_disc_is_never_auto_resolved` (caso real Shadow Hearts). `_DISC_SUBFOLDER_PLATFORMS` (layout de subcarpeta, `operation_planner.py:146,150`) tiene el mismo problema pero **no se tocó** — cambiarlo movería de verdad los PSX/Saturn reales (hoy planos en `psx/Juego.chd`) a subcarpetas por primera vez, un cambio de layout con blast radius grande que requiere decisión aparte, no un efecto colateral de este fix → ver GAMECUBE-DISC-BUG-1f. 1072/1075 tests en verde (3 fallos preexistentes no relacionados) | `planner/operation_planner.py:19-45`, `services/ra_duplicates_service.py:339,367,424`, `tests/test_apply_ra_conflicts.py` | ✅ corregido 2026-08-30 |
| GAMECUBE-DISC-BUG-1e | **Corregido 2026-08-30**: causa raíz real de por qué Disc 1 y Disc 2 colisionaban al mismo target. `normalize_for_match` (`detection/filename_normalizer.py:45`) borra `"(Disc N)"` junto con el resto de anotaciones al construir la clave del índice de títulos (`catalog/matcher.py::_build_title_index`), así que un set multi-disco colapsa a una sola clave con una entrada del DAT por disco (`_title_index[key]` = lista). `_match_by_title` (`catalog/matcher.py:234-270`) solo desempataba por plataforma (extensión de archivo) — nunca por disco — así que con varias entradas de la misma plataforma siempre ganaba la primera en orden de carga (normalmente Disc 1), asignando ese `canonical_title` también al Disc 2/3/4 real. Arreglo: tras el filtro por plataforma, nuevo desempate por número de disco usando `find_disc_number` (ya existente en `utils/disc_tag.py`, sin parsing nuevo) — si el nombre del archivo trae número de disco, se prefiere la entrada del DAT cuyo título tiene ese mismo número. Verificado con test sintético (falla sin el fix, pasa con él) y contra los catálogos reales del proyecto (`.rommgr/catalogs/`): los 4 casos de GameCube y `Shadow Hearts - Covenant` (PS2) ahora resuelven cada disco a su `canonical_title` correcto. **No aplicado a `library_pc.db` todavía** — el `canonical_title` ya guardado sigue siendo el incorrecto hasta re-escanear/re-emparejar la biblioteca real (pendiente, requiere backup previo). Nota aparte sin relación: ~20 `.dat` en `.rommgr/catalogs/` fallan al parsear (`ParseError: syntax error line 1 column 0` — probablemente placeholders sin descargar), no afectó la verificación pero puede explicar matches fallidos en otras plataformas | `catalog/matcher.py:9,234-270` | ✅ corregido 2026-08-30, pendiente re-aplicar a la BD real |
| GAMECUBE-DISC-BUG-1f | **Hallazgo 2026-08-30, sin arreglar a propósito** — mismo mismatch de nombres que 1d pero en `_DISC_SUBFOLDER_PLATFORMS` (`operation_planner.py:146,150`, layout de subcarpeta por juego): `game.platform.lower() in _DISC_SUBFOLDER_PLATFORMS` (línea 146) nunca coincide para PSX/Saturn reales (`"PlayStation"`/`"Sega Saturn"` ≠ `"psx"`/`"saturn"`) — confirmado en vivo que los PSX de la biblioteca real viven planos (`psx/Juego.chd`, `psx/Juego.cue`), nunca en subcarpeta (`psx/Juego/Juego.cue`) pese a que el código pretende crearla para "disc platforms". Arreglarlo (usar nombres de catálogo también aquí) haría que la próxima vez que se ejecute "Organizar" con PSX/Saturn reales, cientos de archivos empiecen a moverse a subcarpetas por primera vez — cambio de layout grande e intencional, no un bugfix silencioso. Requiere decisión explícita del usuario antes de tocarlo | `planner/operation_planner.py:19-26,146,150` | 🔴 pendiente decisión del usuario — cambio de layout, no autoaplicar |
| GAMECUBE-DISC-BUG-1g | **Hecho 2026-08-31** — pedido del usuario tras ver un toast de "Revisar copias" que nunca bajaba de contador: los grupos de conflicto (`disk`/`collision`) en plataforma multi-disco (`_MULTI_DISC_RISK_PLATFORMS`) no daban ninguna pista de por qué "Resolver con RA" no hacía nada con ellos, ni forma de descartarlos de la cola. Arreglo: `_review_groups_for_repo` (`web/builders/duplicates.py`) añade el reason `"multi_disc_risk"` a esos grupos; `review_copies.js::_renderReviewGroup` les pone insignia "Posible multi-disco" + nota explicativa + botón "Ya lo he revisado" (reutiliza `markReviewGroupIntentional`/`/api/review-queue/exclude` ya existente, sin endpoint nuevo). Verificado contra la BD real levantando el servidor local: 33 grupos reales marcados (`PlayStation`, `PlayStation 2`, `Dreamcast`, `Wii`, `GameCube`), incluidos los 4 de GameCube de 1a. 2 tests nuevos en `test_builders_duplicates.py` (caso real + caso negativo Game Boy). **No verificado visualmente en navegador** — la extensión de Claude in Chrome no estaba conectada en esta sesión; solo backend (API real) + sintaxis JS (`node --check`) confirmados | `web/builders/duplicates.py`, `web/static/js/tabs/review_copies.js`, `tests/test_builders_duplicates.py` | ✅ hecho 2026-08-31, pendiente verificación visual en navegador |

### HEALTH-CHECK-1 — 1.522 archivos "desaparecidos" en el último Health Check semanal (hallazgo, sin investigar)

Origen: el usuario preguntó por una notificación de escritorio que recordaba como "0 ROMs verificados, sin problemas" — viene de `web/daemons.py:113-125`, notificación nativa (no toast de la app) que manda el daemon `_health_scheduler_loop` una vez por semana (`_HEALTH_CHECK_INTERVAL_DAYS = 7`). El registro real (`.rommgr/health_schedule.json`) no tiene ningún "0" — la última corrida (2026-08-26T23:37:33Z) encontró `last_ok=11474, last_corrupted=2, last_missing=1522`. Lo del "0" que recuerda el usuario es casi seguro una ejecución mucho más antigua (p. ej. la primera, antes del escaneo inicial) cuyo popup de Windows ya desapareció — no hay nada raro en el mecanismo de scheduling en sí (funciona como está diseñado, cada 7 días).

Lo que sí es un hallazgo real y sin explicar: **1.522 archivos marcados "missing"**, ~12% de una biblioteca de ~13.000 juegos. `check_library_health` (`utils/health_checker.py:68-71`) solo comprueba la ruta guardada en `games.source_path` contra el disco (`path.exists()`) sobre el repo PC (`E:\Carpetas anbernic\`, confirmado montado y accesible ahora mismo) — no se ha verificado si esos 1.522 son missing real (archivos borrados/movidos fuera de la app) o un falso positivo (p. ej. el disco `E:\` desconectado justo durante esa corrida del 26/08, o una ruta relativa/de red que fallaba en ese momento). No investigado más a fondo esta sesión — un health check completo re-hashea toda la biblioteca (lento) y no se ha lanzado sin permiso explícito.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| HEALTH-CHECK-1a | Investigar los 1.522 "missing" del Health Check del 2026-08-26: ejecutar (con permiso del usuario, es lento) un Health Check nuevo desde la pestaña Herramientas y comparar — si el número baja mucho, confirma que fue un falso positivo transitorio (disco desconectado); si se mantiene, hay que mirar los `source_path` concretos que fallan (¿todos en una misma subcarpeta/plataforma? ¿rutas con caracteres especiales?) | `utils/health_checker.py`, `.rommgr/health_schedule.json` | 🔴 pendiente, requiere lanzar Health Check completo (con permiso) |

---

### ARCADE-RENAME-BUG-1 — MAME/FBNeo no cargan ~2.766 ROMs de `arcade/` por nombre de archivo (hallazgo 2026-08-31)

Origen: el usuario reportó que desde iiSU y Daijishou, cargar juegos de
MAME/FBNeo "es terrible" — en muchos casos el emulador no llega a abrir el
juego. Investigado contra la biblioteca real (`E:\Carpetas anbernic\arcade`,
10.420 `.zip`) y los catálogos reales (`.rommgr/catalogs/Arcade/`):

**Causa raíz #1 (la principal, confirmada con datos)**: MAME y FBNeo
identifican una ROM por el **nombre corto interno del set** (p. ej.
`silkwrm.zip`, `cclimber.zip`), no por un título descriptivo. **2.766 ZIPs
de `arcade/` (26,5% del total) tienen nombre descriptivo tipo No-Intro**
("Silkworm (Europe).zip", "Crazy Climber (US set 1).zip") — cruzados contra
el índice de nombres cortos de FBNeo (8.136 machines) + MAME 2003-Plus
(4.858 machines, ver bug de parseo abajo): **0 de esos 2.766 coinciden** —
ninguno puede cargar en ningún core de MAME/FBNeo tal como está nombrado
ahora mismo. Los otros 7.553 ZIPs ya usan nombre corto y sí funcionan.
Verificado en la BD (`library_pc.db`) que "Crazy Climber (US set 1).zip"
**sí está bien identificado como MAME** (`catalog_source='mame.xml'`) pero
el renombrado nunca lo llevó al nombre corto que el emulador necesita — la
misma lógica de "nombre canónico descriptivo" que usamos para
GBA/PSX/SNES... se aplicó también a arcade, donde es precisamente lo
contrario de lo que hace falta.

**Causa raíz #2 (bug de parseo encontrado de rebote)**: `load_mame_xml`
(`catalog/mame_loader.py:29`) asume que si `root.tag != "datafile"` los
juegos están en `<machine>`, pero `MAME 2003-Plus.dat` real (`.rommgr/catalogs/Arcade/MAME 2003-Plus.dat`)
tiene `root.tag == "mame"` con hijos `<game>` (no `<machine>`) — el parseo
no lanza error (el XML es válido) pero devuelve **0 machines siempre**,
silenciosamente. Cualquier feature que dependa de `load_mame_xml` contra
este dat real (matching, `ARCADE-RECON`, DAT-DL) ha estado funcionando sin
la mitad de la cobertura MAME sin que nada lo avisara.

**Causa raíz #3 (ya conocida, reconfirmada aquí)**: el mismo bug de
`_match_by_title` de `GBA-MISPLACED-2` también corrompe arcade — "Silkworm
(Europe).zip" y "Outzone (Europe).zip" (juegos arcade con versión
homónima en Atari ST/Amiga) quedaron etiquetados `platform='Atari ST'` /
`'Amiga'` en vez de Arcade, `match_confidence='low'`/`'medium'` — mismo
`hits[0]` arbitrario sin desambiguar por carpeta real.

**Config de iiSU (dato de contexto, no la causa principal)**: `arcade`,
`cps1`, `cps2`, `cps3` y `neogeo` en `emulator_options.json` del dispositivo
apuntan todos al mismo core FinalBurn Neo — no hay separación por core, así
que incluso arreglando el nombre, un set que sea genuinamente solo-MAME (44
casos confirmados: están en `MAME 2003-Plus.dat` pero no en el FBNeo dat)
seguiría sin cargar por esta vía.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ARCADE-RENAME-BUG-1a | Arreglar `load_mame_xml` para detectar el tag real de hijos (`<machine>` vs `<game>`) en vez de asumirlo por `root.tag` — comprobar con `root.find('machine') is not None` como ya se validó aquí, o iterar ambos tags | `catalog/mame_loader.py:18-45` | 🔴 pendiente |
| ARCADE-RENAME-BUG-1b | **La pieza que de verdad arregla la carga**: la lógica de renombrado/organización de arcade nunca debe convertir el nombre a un título descriptivo — debe conservar (o restaurar) el nombre corto de set (`name` del DAT, no `description`). Localizar dónde se decide `canonical_title` para plataforma Arcade (probablemente donde se aplica el resultado de `_match_by_title`/`_match_by_crc`) y forzar ahí el nombre corto para esta plataforma | `catalog/matcher.py`, `renamer/file_renamer.py` (punto exacto por confirmar) | 🔴 pendiente, causa raíz principal |
| ARCADE-RENAME-BUG-1c | Backfill: para los 2.766 ZIPs ya renombrados a título descriptivo, hay que recuperar su nombre corto real (por CRC contra FBNeo/MAME, ya tenemos `load_arcade_crc_index`/`load_arcade_manifest`) y renombrarlos de vuelta — **irreversible en apariencia pero no en datos** (el contenido no cambia, solo el nombre del zip) — requiere backup previo y plan (`rommgr plan`) antes de aplicar, mismo patrón que cualquier rename masivo | Biblioteca real (`arcade/`) | 🔴 pendiente, depende de 1b para no repetir el problema |
| ARCADE-RENAME-BUG-1d | Aplicar el mismo fix de `GBA-MISPLACED-2` (desambiguar por carpeta real cuando la extensión es ambigua) también cubre los casos arcade→Atari ST/Amiga de este hallazgo — no es tarea nueva, solo confirma que arcade también se beneficia de `GBA-MISPLACED-2` | `catalog/matcher.py:250-270` | 🔴 pendiente, mismo fix que GBA-MISPLACED-2 |
| ARCADE-RENAME-BUG-1e | Separar `arcade`/`cps1/2/3`/`neogeo` en `emulator_options.json` de iiSU por core real (FBNeo vs MAME 2003-Plus) en vez de forzar FBNeo para todo — solo tiene sentido después de 1b/1c, para los 44 sets confirmados solo-MAME | Config del dispositivo (iiSU) | 🔴 pendiente, depende de 1b/1c |

---

### LIBRARY-SYNC-STALE-1 — Biblioteca corregida el 08-30 (GBA/PSX/GameCube) nunca llegó a la Anbernic (hallazgo 2026-08-31)

Origen: el usuario reportó que se dejó "a medias" mandar las bibliotecas
arregladas de PSX y GBA (y posiblemente GameCube) a la consola. Verificado
contra `.rommgr/cable_sync_ops.log` (no contra suposiciones): el último Cable
Sync real de ROMs (`pc_to_anbernic`) corrió 2026-08-29T22:58→23:14Z —
**antes** de los hallazgos/fixes de `GBA-MISPLACED-1` y `GAMECUBE-DISC-BUG-1`
(fechados 2026-08-30). Desde entonces solo hay `AUTO-SYNC` de saves en el log,
ningún Cable Sync de ROMs nuevo. Además, ese último sync ya excluía a
propósito `psx/`, `gamecube/`, `ps2/`, `Unknown/` y `arcade/` por falta de
espacio (78 GB libres en la SD, esas carpetas suman 61+34+30+25+18 GB) — es
decir, PSX y GameCube nunca han llegado a la consola, no es que se cortara a
medias.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| LIBRARY-SYNC-STALE-1a | Re-lanzar Cable Sync `pc_to_anbernic` solo de `gba/` (cabe de sobra) para reflejar los 25 archivos movidos fuera/dentro de esa carpeta por `GBA-MISPLACED-1a/b/c` — hoy la consola tiene la versión vieja (con archivos mal ubicados que ya no están en el PC) | Cable Sync (pestaña Sync) | 🔴 pendiente, requiere ADB autorizado (ver `GBA-SAVE-PATH-1`) |
| LIBRARY-SYNC-STALE-1b | **Hecho 2026-08-31.** `psx/` marcaba 195 GB con `du`, pero solo 86,3 GB eran biblioteca real — el resto era limpieza pendiente. Verificado con `chdman extractcd` + `md5sum` (no solo por nombre) antes de mover nada: (1) **182 `.bin` sueltos (93,4 GB)** con nombre exacto de un `.chd` ya existente — hash idéntico confirmado en 3 muestras (Vagrant Story, Darkstalkers 3, Tony Hawk's Pro Skater 2), son el resto sin limpiar de conversiones `chdman` antiguas; (2) **47 grupos de duplicado por región/versión (15,8 GB)** dentro de los `.chd` reales — política aplicada: preferir USA > World > Europe > Spain > Germany > France > Italy > Japan > Asia > el más grande como último criterio (reversible, no es la lógica RA real de la app); (3) **41 `.zip` sueltos (13,5 GB)** que duplican un `.chd` ya existente. Todo movido a subcarpetas dentro de `psx/_descartados/` (excluidas del Cable Sync por diseño, `cable_engine.py:39`) con manifiesto en cada una — nada borrado de forma irreversible. Delta real de sync bajó de 139,5 GB → **75,1 GB**, cabe en los 84 GB libres de la SD. Sync real `pc_to_anbernic` de `psx/` lanzado y verificado | `E:\Carpetas anbernic\psx\_descartados\{bin-redundante-verificado-2026-08-31,duplicados-region-2026-08-31,zip-duplicado-de-chd-2026-08-31}` | ✅ hecho y verificado 2026-08-31 |
| LIBRARY-SYNC-STALE-1c | **Hecho 2026-08-31.** Los 22 `.cue` de `Tareas/psx-cue-rotos-2026-08-30.md` (ninguno funcional) movidos a `psx/_descartados/cue-rotos-investigados-2026-08-30/` con manifiesto que remite al informe. **Crash 2 sigue pendiente de volver a descargar** — no tiene copia de reemplazo, se movió igual porque el `.cue` en sí ya era inútil (referenciaba un `.bin` inexistente), pero el juego en sí sigue sin resolver | `Tareas/psx-cue-rotos-2026-08-30.md`, `psx/_descartados/cue-rotos-investigados-2026-08-30/` | 🟡 `.cue` rotos limpiados; Crash 2 pendiente de descargar |
| LIBRARY-SYNC-STALE-1e | **Hallazgo nuevo, sin tocar a propósito**: 42 `.zip` sueltos en `psx/` (8,6 GB) que NO duplican ningún `.chd` existente — probablemente contenido real sin organizar (mismo síntoma que `bagman.zip`/`donpachi.zip` vistos en los conflictos del Inbox al arrancar el servidor hoy). Y 61 `.bin` sueltos (2,75 GB) sin `.chd` ni `.cue` correspondiente — igual, posible contenido único. Ninguno de los dos se tocó (no son duplicados, podrían ser juegos que faltan) — requieren pasar por el Inbox normal, no por limpieza de duplicados | `psx/` (42 `.zip` + 61 `.bin` sueltos) | 🔴 pendiente, revisar vía Inbox, no es limpieza de duplicados |
| LIBRARY-SYNC-STALE-1d | Re-aplicar a la BD real el fix de `canonical_title` de `GAMECUBE-DISC-BUG-1e` (el código ya distingue bien Disc 1/Disc 2 por número, pero `library_pc.db` sigue con los valores incorrectos hasta un re-scan/re-match) | `library_pc.db` (requiere backup previo) | 🔴 pendiente, requiere backup + re-scan |

---

### GBA-SAVE-PATH-1 — GBA "no encuentra los saves anteriores" tras instalar emuladores nuevos (investigado en vivo 2026-08-31, sin repro confirmado)

Origen: el usuario reportó que tras instalar emuladores nuevos en la
Anbernic, GBA no arranca con la partida anterior. Investigado en vivo con
ADB ya autorizado (`RG556006101273 device`):

- **GBA.emu sigue siendo el único emulador de GBA instalado** (`pm list
  packages` — ningún GBA nuevo, standalone o núcleo). Instalaciones
  recientes reales: `com.armsx2` (2026-08-25, PS2 — parte de
  `SAVES-FRAGMENT-6`) y `com.seleuco.mame4d2024` (2026-08-27, `astrocde` —
  parte de `IISU-CONFIG-1`). Ninguna toca GBA.
- La ruta que asume `EMULATOR_SAVE_PATHS_DEFAULT` para GBA.emu
  (`config.py:107-113`, `Android/data/com.explusalpha.GbaEmu/files/EmuEx/GBA/saves`)
  **está vacía en el dispositivo real** — ese árbol `EmuEx/` ni existe.
  GBA.emu en esta Anbernic en realidad guarda los `.sav` **junto a las ROMs**
  en `/storage/521D-04EA/ROMs/gba/*.sav` (mismo patrón ya documentado en
  `SAVES-FRAGMENT-8`, sin arreglar) — es decir, la ruta configurada en
  `config.py` para el sync automático por ADB **nunca ha sido la correcta
  para GBA.emu en este dispositivo**; el mecanismo que sí ha mantenido esos
  saves sincronizados hasta ahora es el Cable Sync normal de la carpeta
  `gba/` completa (arrastra ROMs + `.sav` juntos), no el sync especial por
  paquete de `EMULATOR_SAVE_PATHS_DEFAULT`.
- Comparado el listado completo de `.sav` en `ROMs/gba/` (dispositivo) contra
  `gba/` (PC, `E:\Carpetas anbernic`): **coinciden casi 1:1**, incluso
  copias de 2014. El histórico está intacto y sigue en sync.
- Solo 2 archivos de hoy (2026-08-31 00:46-00:48, mismos minutos en que
  `dumpsys usagestats` registra a GBA.emu abierto con un `PickActivity` de
  selección de carpeta): `Pokemon WaterBlue.sav` (ROM nueva, añadida ayer
  23:06, sin partida previa — normal) y `Prince of Persia - The Sands of
  Time (USA) (En,Fr,Es).sav` (**0 bytes, plantilla en blanco** — pero no hay
  ningún `.sav` previo en el PC con ese nombre exacto tampoco, así que no es
  un caso de "nombre cambiado sin arrastrar el save" tipo `SAVES-FRAGMENT-7`
  — simplemente no había partida guardada de este juego en esta biblioteca).

**No se ha reproducido el síntoma exacto** con la evidencia disponible — el
histórico de saves de GBA está intacto y sincronizado. Sigue sin confirmarse
qué juego concreto perdió progreso, o si el problema fue puntual (un save en
blanco creado sobre la marcha por GBA.emu al perder el permiso SAF de la
carpeta tras la ronda de instalaciones del 08-25/08-27, y el usuario lo
interpretó como "no encuentra los saves") vs. sistémico.

**Causa raíz confirmada 2026-08-31**: el cambio de core/emulador de GBA en
RetroArch dejó dos esquemas de saves conviviendo — el viejo por-core
(`RetroArch/saves/VBA Next/`, con el progreso real) y el nuevo por-plataforma
(`RetroArch/saves/gba/`, el que lee el emulador/core actual). La migración
del 08-25 copió bien la mayoría, pero no todos los juegos:

| Juego | Verificación (diff de bytes real, no solo fecha) | Resultado |
|---|---|---|
| **Pokémon Rojo Fuego/FireRed (Rev 1)** | `saves/gba/` (partida de ayer) vs `saves/VBA Next/` (08-23): **13,2% de bytes distintos** → partida nueva, no continuación (el usuario confirmó: probó el juego y no encontró la vieja) | 🔴 progreso real sí estaba en riesgo de quedar "detrás" — **restaurado** |
| **Pokémon Pinball - Ruby & Sapphire (Japan) (Rev 1)** | 0,09% de bytes distintos entre 08-20 y 08-30 | ✅ es la misma partida, un poco más avanzada — sin acción |
| **Zelda - A Link to the Past** (ambas variantes de nombre) | 0% de diferencia, bytes idénticos | ✅ migración correcta — sin acción |
| **Metroid - Zero Mission [E]** | El save real (2025-06-29) nunca se copió a `saves/gba/` — no había nada que lo sobrescribiera todavía (el usuario no lo había probado) | 🔴 hueco real, mismo patrón que iba a repetir el caso de FireRed en cuanto se abriera — **restaurado antes de que pasara** |

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| GBA-SAVE-PATH-1a | **Hecho 2026-08-31**: backup del save de prueba descartado de FireRed en `.rommgr/backup_gba_save_restore_2026-08-31/` (con manifiesto), luego copiado en el dispositivo (`adb shell cp`, mismo filesystem) el save real de `saves/VBA Next/` → `saves/gba/` para **Pokémon Rojo Fuego/FireRed** (sobrescrito) y **Metroid - Zero Mission [E]** (no existía, sin sobrescritura). Verificado con `md5sum` en el propio dispositivo tras la copia: coincide exacto con el origen en ambos casos | Dispositivo (RG556006101273) + `.rommgr/backup_gba_save_restore_2026-08-31/` | ✅ hecho y verificado 2026-08-31 |
| GBA-SAVE-PATH-1b | **Hecho 2026-08-31 — auditoría completa, no solo los 4 juegos nombrados.** El usuario avisó que "todos los juegos deberían tener partidas más antiguas" — comparado por `md5sum` **el listado entero** de `RetroArch/saves/VBA Next/` (50 archivos) contra `RetroArch/saves/gba/` (74 antes de arreglar): 39 ya coincidían byte a byte, 1 (Pokémon Pinball Japan Rev 1) era continuación real (0,09% de diferencia, sin tocar), y **10 juegos no tenían ningún archivo en `saves/gba/`** (Castlevania - Harmony of Dissonance ×2 nombres, Megaman Zero 1, Pokémon Esmeralda/Rojo Fuego/Verde Hoja ×2 nombres cada uno, Pokémon Pinball ×2 nombres) — mismo hueco que Metroid. Copiados los 10 desde `VBA Next/` a `gba/` (script generado y ejecutado vía `adb shell sh`, sin sobrescribir nada — ninguno existía ya en destino). Verificado con `md5sum` tras la copia: **las 50 partidas de `VBA Next/` están ahora también en `saves/gba/`, 0 huecos, 0 discrepancias**. Nota informativa sin acción: la carpeta `saves/mGBA/` tiene 2 copias sueltas de mediados de 2025 (Metroid Zero Mission, Pokémon Rojo Fuego) de un experimento con ese core, más antiguas que las restauradas — no se tocaron | Dispositivo (RG556006101273), scripts en `.rommgr/backup_gba_save_restore_2026-08-31/` | ✅ hecho y verificado 2026-08-31 |
| GBA-SAVE-PATH-1c | Corregir `EMULATOR_SAVE_PATHS_DEFAULT["com.explusalpha.GbaEmu"]` (`config.py:107-113`) — la ruta real en esta Anbernic es "junto a las ROMs" (`ROMs/gba/`), no `Android/data/.../EmuEx/GBA/saves` (ese árbol no existe) — mismo patrón que `SAVES-FRAGMENT-8`, revisar si aplica también a GBC/NES/MD.emu (misma familia EmuEx) | `config.py` | 🔴 pendiente, confirmar si es un problema real (el Cable Sync normal de carpeta ya cubre este caso, el especial por-paquete puede que nunca haya hecho nada útil para GBA.emu) |

---

### LIBRARY-CLEANUP-GAPS-1 — Huecos reales encontrados al limpiar PSX a mano (hallazgo 2026-08-31)

Origen: para que `psx/` cupiera en la Anbernic (`LIBRARY-SYNC-STALE-1b/c`) se
hizo a mano una limpieza de 195 GB → 81 GB reales. La detección de saves
divergentes de GBA (`GBA-SAVE-PATH-1`) ya la hace la app
(`SAVE-CONSOLIDATOR-1`) — lo que no existe es la parte de actuar sobre ello.
Cuatro huecos concretos, ninguno cubierto hoy por ninguna feature existente:

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CHD-CLEANUP-1 | **El hueco más grande (93 GB solo en PSX real).** Tras convertir un `.bin`/`.cue` a `.chd` con `chdman`, el `.bin`/`.cue` original nunca se limpia — se queda para siempre ocupando espacio. Propuesta: paso opcional tras la conversión que verifica el `.chd` (extraer con `chdman extractcd` + comparar hash contra el `.bin` origen, mismo método usado hoy a mano) y mueve el origen a `_descartados/` solo si coincide — nunca objetivo automático sin verificar | Módulo de conversión CHD (buscar dónde vive hoy `chdman createcd`) | 🔴 pendiente, tarea nueva |
| DUP-CROSSFMT-1 | Detección de duplicados no compara entre formatos distintos del mismo juego — un `.zip` que contiene exactamente el mismo disco que ya existe como `.chd` no se detecta hoy (encontrados 41 casos, 13,5 GB, solo comparando título normalizado a mano). Extender `ra_duplicates_service`/`_build_review_queue` para que agrupe también por normalized_title+disco cruzando extensiones, no solo por SHA1 exacto dentro del mismo formato | `services/ra_duplicates_service.py`, `web/builders/duplicates.py` | 🔴 pendiente, tarea nueva |
| DISC-HEALTH-1 | No existe un chequeo repetible de "sets de disco rotos" — `Tareas/psx-cue-rotos-2026-08-30.md` fue investigación 100% manual (parsear `.cue`, comprobar que el `FILE` referenciado existe, y si no, buscar si ya hay un `.chd`/`.pbp` del mismo juego en la biblioteca). Convertir esto en una función reutilizable (mismo espíritu que `check_library_health`, pero para integridad de sets multi-archivo, no solo "existe la ruta") | `utils/health_checker.py` (candidato) o módulo nuevo | 🔴 pendiente, tarea nueva |
| LIB-MISPLACED-1 | El Inbox solo audita archivos **nuevos** que entran — nada revisa archivos ya sueltos dentro de una carpeta de plataforma ya organizada. Hoy mismo aparecieron chips de MAME sueltos en `gba/` (TMNT, `963-*.*`) y ROMs de otra plataforma (`.md`, `.nes`) mezclados en `gba/`, más una carpeta `_descartados/_descartados` con chips de arcade sueltos dentro de `psx/` — todo encontrado a mano antes de cada Cable Sync. Falta un escaneo de salud que recorra las carpetas de plataforma ya organizadas buscando extensiones que no pertenecen a esa plataforma (reutilizar `detect_platform()`/`PLATFORM_BY_EXTENSION`, ya fiables) | `scanner/rom_scanner.py` o `utils/health_checker.py` (punto de entrada exacto por confirmar) | 🔴 pendiente, tarea nueva |

