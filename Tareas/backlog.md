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
> 2026-09-19: hallazgo `ANDROID-DUP-1` — duplicados reales confirmados por ADB
> en vivo contra la RG556 (PSX, GBA) + carpetas Title Case/slug paralelas nunca
> consolidadas en el dispositivo (patrón `DUALFOLDER-12`, solo aplicado en PC);
> `library_android.db` desactualizada (último scan 2026-09-12); relanzado el
> scrape completo (22.840 ROMs pendientes)
> 2026-09-22: 8 ideas de mejora propuestas por el usuario añadidas como tareas
> nuevas (SAVES-UX, INBOX-UX, LIBRARY-UX, MOBILE-UI, RA-LIVE en sus epics de
> pilar existentes → #202/#203/#204/#206/#208) + nuevo epic "Estandarización de
> biblioteca multi-launcher" (→ #337, ESDE-FOLDER-STD-1 fusiona
> ROADMAP-IDEAS/ESDE-CONFIG-CHECK, ROMHACK-ORG-1 nuevo). Ninguna implementada
> todavía — todas ⬜ sin diseñar. Roadmap por rama creado (`.claude/roadmaps/
> INDEX.md`, 6 ramas nuevas 25-30, fases 1-6). Añadida 9ª tarea
> `SYNC-CONFLICT-MANUAL-1` (revisión manual de conflictos de Cloud Sync) tras
> verificar contra el código real que hoy se auto-resuelve siempre por policy
> global — agrupada en la rama `feature/saves-ux-history-context` (roadmap 25)
> por compartir fichero con `SAVES-CONFLICT-CTX-1`, no rama nueva
> 2026-09-26: `NATIVE-SAVE-SYNC-1` — biblioteca, emuladores y juegos nativos
> consolidados en `E:\RetroVault\` (`ROMS`/`EMULADORES`/`JUEGOS NATIVOS`);
> 129.654 filas reescritas en `library_pc.db`; sync de saves extendido a
> juegos nativos (Dusklight/Twilight Princess) reutilizando `sync_sources`
> sin código nuevo
> 2026-09-29: `CHD-CLEANUP-1` nuevo comando `rommgr clean-redundant-chd`
> (PR #376) aplicado real contra `psx/` en la Anbernic — 17/19 candidatos
> verificados por hash RA y borrados, 11,49 GB liberados, 0 errores; 2
> saltados de forma segura (sheets `.cue` rotas). `GDI-ORGANIZE-1` bug 1
> arreglado (PR #377) — `build_plan()` ya no adivina mal el destino de
> PSX/Saturn/Dreamcast/Wii cuando el origen no está en su carpeta de
> plataforma
> 2026-09-30: rescatadas `feature/saves-ux-history-context` (roadmap 25,
> PR #338) y `feature/inbox-ux-summary-metadata` (roadmap 26, PR #339) —
> llevaban abiertas desde el 22-25/09 con trabajo completo, bloqueadas por
> conflictos reales contra los 5 días de `develop` que avanzaron mientras
> tanto; roadmaps 28/29/30 renumerados a 29/30/31 (28 ya lo ocupaba
> `android-gdrive-provider`, sesión aparte) y el roadmap 27 (ya completado
> vía PR #340) retirado del índice por duplicado
> 2026-09-30 (continuación): instancia real (puerto 7777) reiniciada con el
> código de hoy. `ANDROID-DUP-CROSSFMT-VERIFY-1` cerrado del todo (89 grupos
> PSX verificados por hash real, 2 seguros aplicados, 0,48 GB). Dedup GBC
> aplicado (1268 grupos, 1,95 GB) + Sega Mega Drive/SNES/Game Boy/N64DD/1 PSX
> sha1-puro (96 grupos, 0,145 GB) — ~2,58 GB liberados en total, 0 errores
> reales, verificado en el dispositivo real. Causa raíz de las filas fantasma
> de `ANDROID-DUP-PSX-1` encontrada (scan `psx` interrumpido el 28/09, nunca
> reconciliado) — documentada, sin arreglar
> Completed tasks → `Tareas/diario/archivo/archivo.md`
> Arquitectura actual: `docs/architecture/architecture.md`
> Organizado por épica de GitHub (2026-08-15) — convención en `.claude/CLAUDE.md` § Gestión de tareas.

Regla de branching: una rama por tarea → PR a `develop`. Las sub-tareas que comparten
fichero o son la misma unidad de cambio se agrupan en una sola rama. Refactores
grandes de un fichero van **siempre separados**. Flujo completo: `CONTRIBUTING.md`.

---

## Índice por rama

Vista rápida de qué rama toca qué tarea(s) de este backlog, para el flujo de trabajo
descrito en `.claude/roadmaps/INDEX.md` ("Cómo usar este roadmap"). El contenido
detallado de cada tarea sigue viviendo en su sección de epic más abajo — este índice
solo enlaza, no duplica. Se mantiene "a demanda": se actualiza cuando se trabaja una
rama de esta lista, no se re-audita el backlog entero en cada sesión.

**Ramas con roadmap específico pendiente** (`.claude/roadmaps/INDEX.md`, filas 14-20):

| Rama | Roadmap | Tarea(s) en este backlog | Epic |
|------|---------|---------------------------|------|
| `fix/matcher-coverage-gaps` | [14](../.claude/roadmaps/14-matcher-coverage-gaps.md) | [MATCH-FIX-3](#match-fix-3-descomprimir-y-rehashear-no-resuelve-las-colisiones-de-nombre-cuando-el-catálogo-tampoco-conoce-el-hash-real-hallazgo-2026-09-12) | Pilar 1 |
| `fix/cable-sync-format-gaps` | [16](../.claude/roadmaps/16-cable-sync-format-gaps.md) | [CABLE-ROM-FIX](#cable-rom-fix-el-sync-de-roms-por-cable-no-compara-con-el-destino-hallazgo-2026-08-13) | Pilar 3 |
| `feature/device-profile-loose-data` | [19](../.claude/roadmaps/19-device-profile-loose-data.md) | Sección "Hardware validation" (línea ~1284) | Perfil de dispositivo |
| — (acciones manuales/hardware) | [20](../.claude/roadmaps/20-rammu-machine-pending.md) | mixta, ver roadmap | mixta |
| — (limpieza de documentación, sin rama por defecto) | [24](../.claude/roadmaps/24-docs-audit-followups.md) | [DOCS-AUDIT-1](#docs-audit-1-seguimiento-de-la-auditoría-de-documentación-2026-09-20) | Transversal |
| `feature/inbox-ux-summary-metadata` | [26](../.claude/roadmaps/26-inbox-ux-summary-metadata.md) | `INBOX-SESSION-SUMMARY-1`, `INBOX-METADATA-INLINE-1` | Pilar 2 — fase 3 de 6 — ✅ completo, PR [#339](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/339) abierto |
| `feature/saves-ux-history-context` | [25](../.claude/roadmaps/25-saves-ux-history-context.md) | `SAVES-HISTORY-1`, `SAVES-CONFLICT-CTX-1`, `SYNC-CONFLICT-MANUAL-1` | Pilar 3 — fase 4 de 6 — ✅ completo, PR [#338](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/338) abierto |
| `feature/library-folder-standardization` | [29](../.claude/roadmaps/29-library-folder-standardization.md) | `ESDE-FOLDER-STD-1`, `ROMHACK-ORG-1` | Multi-launcher (#337) — fase 2 de 6 |
| `feature/mobile-responsive-ui` | [30](../.claude/roadmaps/30-mobile-responsive-ui.md) | `MOBILE-UI-1` | UX — fase 5 de 6 |
| `feature/ra-achievements-live-progress` | [31](../.claude/roadmaps/31-ra-achievements-live-progress.md) | `RA-PROGRESS-UI-1` | RA/Scraper/SAGE — fase 6 de 6, bloqueado (API key real) |
| `feature/android-drive-2-signin` (Fase 1 en `main`/`develop` vía PR #357) | [28](../.claude/roadmaps/28-android-gdrive-provider.md) | [ANDROID-DRIVE-1](#android-sync-app-android-nativa-de-sync-de-saves-diseño-2026-08-18) | Android Sync |

**Ramas mergeadas en esta sesión** (2026-09-18, ya reflejadas en `INDEX.md` filas 12/13/17/21/22):
`fix/catalog-match-subset-hack` (PR #317), `fix/dup-winners-non-canonical-guard` (PR #318),
`fix/dual-folder-title-case-slug` (PR #316), `feature/inbox-anbernic-1` (PR #315).

**Sin rama asignada todavía** — hallazgos documentados en el backlog (algunos son
operaciones directas sobre la biblioteca real, sin código; otros son bugs de código
sin rama abierta aún). Agrupados por epic, con el estado tal cual aparece en su sección
— no verificado línea a línea para este índice, ir a la sección para el detalle real:

| Epic | Tareas abiertas (🟡/🔴) sin rama confirmada |
|------|-----------------------------------------------|
| Pilar 1 | **Verificado 2026-10-04 contra cada sección:** `ANDROID-DUP-1`/`-2` 🟡 (lotes aplicados, quedan ~40 pares `.chd`+`.bin` y 5 MISMATCH reales); `ARCADE-RENAME-BUG-1` 🟡 (`-1c` 984/~10.400 procesados, `-1e` 🔴 depende de él); `LIBRARY-SYNC-STALE-1` 🔴🟡 (`-1a` requiere ADB, `-1c` falta Crash 2, `-1e` vía Inbox); `PSX-STRUCTURE-1` 🟡 (30/33, 3 por re-descargar), `PSX-STRUCTURE-4` 🟡 (decisión de ejecución del usuario); `PSX-CUE-DESYNC-1b` 🟡 (5 irrecuperables); `HEALTH-CHECK-1` 🔴 (`-1a` pide lanzar el Health Check completo); `GAMECUBE-DISC-BUG-1` 🟡 (todo ✅ salvo `-1f` sin arreglar a propósito y `-1c` descartado). **Retiradas por estar ✅**: `DUP-DISC-RA-1` (solo `-1e` cerrado sin implementar), `ARCADE-DAT-CONTAMINATION-10` (✅ 2026-09-03), `GBA-SAVE-PATH-1` (✅ todas las sub-tareas). Sin reverificar: `LIBRARY-CLEANUP-GAPS-1`, `LIBRARY-AUDIT-1`, `DUALFOLDER-12`, `JUNK-SCAN-RUBEN-1` (🟡 medido 2026-09-28, nada aplicado) |
| Pilar 2 | ~~`ZIP-ROUTE`~~ retirada 2026-10-04: `-1…-6` y `-8` ✅; solo `ZIP-ROUTE-7` 🟡 (causa fantasma resuelta, segunda mitad cubierta por `-8`) — cierre pendiente de confirmar |
| Pilar 3 | ~~`CABLE-ROOT-1`~~ retirada 2026-10-04: `-1a…-1e` ✅; solo `-1f` 🟡 (política de duplicados ya genérica, re-investigado 2026-09-14). Abiertas de verdad: `SAVES-FRAGMENT-3/4/5` (⬜ documentado, decisión de convenio pendiente) y `CABLE-ROM-FIX-5` (🔴 solo gamecube) |
| Distribución | Phase 6 (🟡) |
| RA/Scraper/SAGE | `SAGE` (🟡) |
| Android Sync (nativo, no cable) | Sección completa (786-830) tiene el mayor volumen de 🟡/🔴 del backlog — `feature/android-sync-12-periodic-sync` y PRs #226-237 ya mergeados cubren parte, pero quedan ítems abiertos sin verificar individualmente aquí |

**2026-10-04** (auditoría, roadmap 33): filas de Pilar 1/2/3 de la tabla de arriba contrastadas con las tablas de sus secciones (estado de las sub-tareas, no solo el título). `ANDROID-DUP-2` ya no es 🔴: el escaneo ADB tiene fase 3 aplicada (`ANDROID-DUP-2-APPLY-1`, 25,08 GB liberados). Quedan sin reverificar las filas de Distribución, RA/Scraper/SAGE y Android Sync.

**2026-09-28**: fila `UX | FTP-PICK (🔴🔴)` retirada de esta tabla —
desincronizada, `FTP-PICK-1`/`-2` ya están ✅ desde el 2026-08-29 (ver
`ROADMAP-IDEAS`, sección "Pilar 3"); solo queda validación manual en
hardware, que no es un 🔴/🟡 de código pendiente. También retirada
`Perfil de dispositivo | CHDMAN-TEST-COMPRESS-1 (🟡🔴)` — `CHDMAN-TEST-COMPRESS-1`
ya está ✅ desde el 2026-09-06 (causa raíz confirmada: bug de `chdman.exe`
comprimiendo discos sintéticos diminutos, fix vive solo en el fixture de
test, no en el código del proyecto). Mismo patrón de desincronización ya
documentado en `.claude/roadmaps/INDEX.md`.

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
| ARCADE-DAT-CONTAMINATION-6 | **✅ Resuelto 2026-09-04** (con confirmación del usuario). De los 232 ficheros en el nivel superior (240 nominales, 8 ya en `_processed/`): **64 `.zip`** resultaron NO ser arcade en absoluto — son ROMs NES/FDS de dump Goodtools (`[!]`) que por casualidad comparten nombre de fichero con un set MAME de `arcade/` (coincidencia de título entre plataformas, no contaminación). De esos 64: 10 con CRC de entrada idéntico a un `.zip` ya en `nes/`/`fds/` (duplicado exacto), y **54 verificados por `normalize_for_match()` contra toda la biblioteca — el mismo título ya existe** (casi siempre el mismo nombre+región exacto como `.nes` suelto, ej. `Donkey Kong (USA).zip` → `nes\Donkey Kong (USA).nes`). Los **168 no-`.zip` restantes** (`.nes`/`.fds`) verificados con el mismo método: **168/168 también tienen contraparte por título ya en la biblioteca**. **Resultado: 232/232 (100%) son redundantes**, ninguno resultó ser contenido nuevo. Movidos a `_ARCADE_CONFLICTOS_REVISAR_MANO\_descartados\` (ya existía esa subcarpeta desde `ARCADE-DAT-CONTAMINATION-5`, mismo criterio — nunca borrados, recuperables). `rommgr scan` de refresco: 232 huérfanos limpiados. Scripts de sesión, no versionados (candidato a `REPAIR-TOOL-8`/nuevo comando de "detectar redundante por título" reutilizando `normalize_for_match()`) | `E:\Carpetas anbernic\_ARCADE_CONFLICTOS_REVISAR_MANO\` | ✅ 232/232 descartados a `_descartados/`, 0 contenido nuevo encontrado |
| ARCADE-DAT-CONTAMINATION-7 | **Hecho 2026-09-03**: hallazgo de `DECOMPRESS-ARCADE-GAP-4` — 190 ZIPs intactos + 203 carpetas de residuo suelto (206 detectadas, 3 resultaron ser la raíz completa de `atari5200/`/`intellivision/`/`wonderswan/` — no se aislaron enteras, solo los 57 ficheros sueltos individuales que votaban arcade en esa raíz, para no arrastrar contenido legítimo) aislados en `E:\Carpetas anbernic\_ARCADE_MISFILED_STAGING\` (fuera de `Unknown/`, ver -8) y pasados por `organize-source --apply`: **190/190 ZIPs reclasificados** a `arcade/` sin incidentes (incluye `psx__Raystorm (Japan).zip` — confirma la corrección de `DECOMPRESS-ARCADE-GAP-1` de que el set base `raystorm` sí existe, solo estaba mal etiquetado), 26 conflictos de nombre sin resolver (ficheros sueltos tipo `1.bin`/`7.bin` con nombre duplicado en destino). Los residuos sueltos (`organize-source` no los reconoce — solo detecta arcade por CRC en ZIPs intactos, no en ficheros sueltos) se resolvieron en 2 pasadas con scripts de sesión: (1) 134/242 items con backup 100% íntegro en un único ZIP de `arcade/` → descartados a papelera; 26 carpetas vacías (residuo del propio aislamiento) → eliminadas tras confirmar que no tenían contenido. (2) Los 82 restantes, diagnosticados contra el DAT primario (`MAME 0.286`) con herencia `romof`/`cloneof` real, no solo comparación 1:1 de ZIP: **2 recuperados de verdad** (`grobda`, `sonson` — Wii Virtual Console, sets completos que nunca habían llegado a `arcade/`, re-empaquetados y movidos), **45 descartados** (confirmado que `arcade/` YA los cubre al 100% sin depender del residuo — split-set de MAME, chips compartidos con el padre/otro clon ya presentes). **Quedan 35 sin tocar** — **diagnóstico fino completado 2026-09-03** (sesión aparte, solo lectura: parseo completo del DAT primario con cadena `romof` resuelta hasta la raíz + CRC real de `arcade/` leído de cabecera de ZIP sin descomprimir, 16.101 ZIPs, 70.697 CRCs únicos). Los "6 sin nombre reconocido" bajan a **2**: los 3 `wii__*` usan el título del juego en vez del nombre de set MAME en el nombre de carpeta — 2 no calzaban por nombre literal (`Chelnov (Japan)...`, `Ironclad (USA)...`), identificados por votación de CRC de contenido real contra el índice del DAT primario (`chelnov`: 19/19 ficheros coinciden exacto, `ironclad`: 8/9); el tercero (`chelnovjbl`) ya llevaba el nombre de set correcto. Categorización final de los 35 (mismo criterio que los 47 ya resueltos: solo descartable si `arcade/` por sí solo, sin el residuo, ya cubre el 100% del set exigido por el DAT con herencia `romof`):
- **6 descartables** (`arcade/` ya cubre el 100% sin el residuo): `commandoj`, `firetrapbl`, `rastsagaa`, `springbd`, `chelnov` (identificado por CRC, `wii__Chelnov (Japan)...`) — 5/5 con `covered_by_arcade_alone=True` confirmado.
- **1 caso límite, NO descartado bajo el criterio estricto**: `ironclad` (`wii__Ironclad (USA)...`) — el residuo no aporta ningún chip único (0 de sus 9 ficheros son necesarios-y-ausentes-de-otro-sitio), pero el set completo sigue incompleto en toda la biblioteca (faltan 6 chips en cualquier parte) — `arcade/` solo no llega al 100%, así que no cumple el criterio estricto pese a que borrarlo no perdería nada real. Decisión pendiente del usuario: ¿aplicar aquí el mismo criterio de "sin aporte único = descartable" o tratarlo aparte?
- **15 recuperables por combinación** (residuo aporta chip(s) únicos + `arcade/` ya tiene el resto → juntos llegan al 100% del set exigido, mismo patrón que `grobda`/`sonson` pero sin ser autosuficientes solos — necesitan re-empaquetar combinando con chips ya existentes en el ZIP de `arcade/`): `badlandsb` (15/35 chips únicos), `eswatbl2` (38/53), `pangba` (16/25), `carnivalca` (15/35), `carnivalh` (8/29), `carnivalmm` (1/24), `popeyeb2` (1/25), `blasterkit` (8/29), `hydrap2` (9/51), `hustlerb2` (2/11), `hustlerb3` (2/11), `hustlerb4` (6/16), `hustlerb6` (3/12), `hustlerd` (3/11), `cadashso` (4/16).
- **14 realmente incompletos en toda la biblioteca** (ni el residuo ni `arcade/` juntos llegan al 100% exigido por el DAT — mismo patrón que `raystormj/o/u`, no recuperables sin re-descargar el chip que falta): `badlandsm` (falta 1 chip), `betafrce` (6), `pangbc` (15), `spinner` (13), `venture4` (8), `venture5a` (8), `venture5b` (15), `clowns1` (6), `starfirea` (11), `bsebman` (8), `bsebmanbl2` (8), `exerionb2` (6), `exerionba` (10), `chelnovjbl` (2).

Nada tocado en disco — solo lectura. Ver `ARCADE-DAT-CONTAMINATION-10` para ejecutar las 4 acciones derivadas | `E:\Carpetas anbernic\_ARCADE_MISFILED_STAGING\` | ✅ mayormente resuelto (277/312 items); 🟡 diagnóstico de los 35 restantes completo, ejecución pendiente (`ARCADE-DAT-CONTAMINATION-10`) |
| ARCADE-DAT-CONTAMINATION-10 | **✅ Hecho 2026-09-03** (confirmación del usuario "hazlas todas"), acciones 1-3 ejecutadas con script de sesión (solo lectura hasta el momento de escribir, verificación de CRC antes y después de cada escritura, nunca sobreescribe un ZIP existente): **(1) 6 descartados** — `commandoj`, `firetrapbl`, `rastsagaa`, `springbd`, `chelnov` (criterio estricto original) + `ironclad` (criterio ampliado: 0 aporte único, aunque el set siga incompleto en el resto de la biblioteca — tratado igual con el "sí, todas" del usuario) — movidos a `_ARCADE_MISFILED_STAGING\_descartados\` (papelera, recuperable, nunca borrados). **(2) 15 re-empaquetados**: para cada set, ZIP nuevo en `arcade/` combinando los chips únicos del residuo + los chips ya existentes en algún ZIP de `arcade/` (extraídos de su fuente real, sin descomprimir a disco), con el nombre interno exacto que exige el DAT — `badlandsb.zip` (35 roms: 15+20), `eswatbl2.zip` (53: 38+15), `pangba.zip` (25: 16+9), `carnivalca.zip` (35: 16+19), `carnivalh.zip` (29: 9+20), `carnivalmm.zip` (24: 4+20), `popeyeb2.zip` (25: 11+14), `blasterkit.zip` (29: 8+21), `hydrap2.zip` (51: 9+42), `hustlerb2.zip` (11: 2+9), `hustlerb3.zip` (11: 3+8), `hustlerb4.zip` (16: 8+8), `hustlerb6.zip` (12: 3+9), `hustlerd.zip` (11: 3+8), `cadashso.zip` (16: 4+12) — los 15 verificados íntegros (`zipfile.testzip()` sin corrupción) tras escribir, residuo original movido a `_descartados/` en cada caso. **(3) 14 aparcados** en `_ARCADE_MISFILED_STAGING\_incompletos_pendiente_redescarga\` (sin tocar contenido, solo reubicados para que el estado quede visible — mismo patrón que `raystormj/o/u`, ninguno recuperable sin re-descargar el chip que falta en toda la biblioteca): `badlandsm`, `betafrce`, `pangbc`, `spinner`, `venture4`, `venture5a`, `venture5b`, `clowns1`, `starfirea`, `bsebman`, `bsebmanbl2`, `exerionb2`, `exerionba`, `chelnovjbl`. `rommgr scan` de refresco: 100.909 archivos, 0 errores, 16 huérfanos limpiados. **(4) `H:\ROMs` sin ejecutar** — disco no montado en esta sesión (solo `C:`, `D:`, `E:`), queda igual que `ARCADE-DAT-CONTAMINATION-9` | `E:\Carpetas anbernic\_ARCADE_MISFILED_STAGING\`, `E:\Carpetas anbernic\arcade\` | 🟢 E: hecho (1-3), 🔴 H: pendiente (disco no conectado, ver -9) |
| ARCADE-DAT-CONTAMINATION-8 | **Diagnosticado 2026-09-08 — causa raíz confirmada**: `Unknown/` (11.090 items en la raíz + subcarpetas tipo `cprogolf18/`, `geminib/`, `MAME/`, `games/`, `roms 1/`... con chips arcade sueltos ya descomprimidos) no es una bandeja gestionada por ningún paso del pipeline — es solo un nombre de carpeta fuera de `_RECOGNIZED_PLATFORM_FOLDERS` (`web/builders/folders.py:33-35`), mismo caso que `_ARCADE_MISFILED_STAGING`/`_ARCADE_CONFLICTOS_REVISAR_MANO` antes de que `ARCADE-DAT-CONTAMINATION-5/7/9/10` corrieran `organize-source --apply` sobre ellas: nadie lo había ejecutado nunca contra `Unknown/`. `rommgr organize-source "E:\Carpetas anbernic\Unknown"` (dry-run, dato real) confirma que el pipeline ya sabe clasificar casi todo: de los archivos recorridos, **19.483 se organizarían** — `MAME` 8.605, `Arcade` 2.419, `FBNeo` 839 (11.863 arcade en total, más que los 3.039 *ZIPs* con voto mayoritario del hallazgo original porque el dry-run cuenta también los chips sueltos ya descomprimidos dentro de las subcarpetas tipo `cprogolf18/`, no solo ZIPs intactos), `Sega Mega Drive` 2.390, `NES` 1.002, `Game Gear` 490, y 16 plataformas más con volumen menor. **3.503 quedan `(sin identificar)`** — se quedan donde están, el pipeline nunca mueve algo sin match. **Aplicado 2026-09-08** (confirmación del usuario): `organize-source --apply` real sobre `Unknown/`. Resultado: **3.631 organizados** (movidos a su plataforma real), **15.750 duplicados exactos descartados** (ya existían en destino, soft-discard a `_descartados/`, recuperables — la mayor parte de lo que parecía "biblioteca por organizar" era en realidad una copia redundante ya existente), **3.648 conflictos sin resolver** (mismo nombre, contenido distinto — no se tocan, quedan para revisión manual, ejemplos: varios ZIPs arcade con hash distinto al ya presente en `arcade/`). Quedan 81.058 archivos en el origen (conflictos + no identificados + no-ROM). Rescan completo de la biblioteca tras aplicar (593 ROMs nuevos, 332 registros huérfanos podados).

**Conflictos resueltos 2026-09-09** (vía `find_organize_conflicts`/`_resolve_organize_conflict`, `force_keep`, solo lectura previa + backup de `library_pc.db` en `.rommgr/backup_arcade_dat_contamination8_conflicts_20260909/`): re-medidos en vivo, **3.589** conflictos reales (leve deriva desde el 08-09, ninguno con datos de RA en ningún lado — 0/3.589, el criterio habitual de prioridad RA no aplicaba). Agrupados por casuística y decididos por el usuario: **Arcade+MAME** (3.155, 88% — mayoría con tamaño muy distinto entre origen/destino, patrón de romsets MAME de versión distinta, ej. `bagman.zip` 23 KB vs 188 KB) → criterio "el archivo más grande gana"; **NES** (329 — 280 con tamaño exacto igual pero hash distinto, más compatible con header iNES/revisión que con versión de romset) → gana siempre lo ya organizado; **Resto** (105, 17 plataformas) → mismo criterio que Arcade. Aplicado: **544** ganó Unknown/ (reemplazó lo organizado, con soft-discard del perdedor a `_descartados/`), **2.896** ganó lo ya organizado (Unknown/ descartado a papelera), **145** empatados en tamaño exacto sin criterio aplicable → sin tocar, quedan para revisión manual caso a caso. 4 entradas duplicadas en el listado (mismo archivo aparecía dos veces) se saltaron sin dejar estado a medias — verificado con re-consulta tras aplicar (145 conflictos restantes, cuadra exacto con los empates) | `E:\Carpetas anbernic\Unknown\` | ✅ aplicado y verificado 2026-09-08/09 — los empates de tamaño exacto quedaron resueltos el 2026-09-09, ver `ARCADE-DAT-CONTAMINATION-12` |
| ARCADE-DAT-CONTAMINATION-12 | **Re-medición 2026-09-09 de los 145 empates pendientes — deriva y hallazgo nuevo.** `find_organize_conflicts()` en vivo ya no da 145: da **168** (109 con tamaño distinto + 59 empatados en tamaño exacto — composición distinta a ayer, deriva esperable tras cada rescan/organize). Al investigar por qué tantos casos "con tamaño distinto" seguían sin resolverse pese al criterio ya aprobado ("el más grande gana"), se encontró la causa: `_same_content()` (`web/inbox_pipeline.py:23-37`) compara SHA1 del ZIP completo (bytes crudos), no el CRC32 de cada entrada interna — así que dos ZIPs con **exactamente el mismo contenido de ROM pero re-empaquetados con otra herramienta/timestamp** (mismo patrón que el ZIP-ROUTE ya documentado para el resto de la app: "el header del ZIP ya trae el CRC32 de cada entrada, el contenido manda, no los bytes del contenedor") se marcan como "conflicto" cuando no lo son. Verificado abriendo cada `.zip` de los 168 con `zipfile` y comparando `{(nombre, CRC) por entrada}`: **90 de 168 (54%) son 100% idénticos por CRC interno** — falsos positivos puros, ninguna pérdida posible al quedarse con cualquiera de los dos. Solo **78 tienen contenido realmente distinto** (39 `.zip` con CRC interno distinto + 39 no-zip donde la comparación de bytes ya era correcta, todos con tamaño exacto igual — mismo patrón "header/revisión" que el bloque NES original de `ARCADE-DAT-CONTAMINATION-8`: `Sega Mega Drive` 32, `Nintendo 64DD` 5, `Famicom Disk System` 1, `Game Gear` 1). **Aplicado 2026-09-09** (confirmación del usuario, backup previo en `.rommgr/backup_arcade_dat_contamination12_20260909/library_pc.db`), criterio: CRC interno idéntico → gana lo ya organizado (sin riesgo, contenido probado idéntico); `NES` → gana siempre lo ya organizado (mismo criterio ya aprobado en `ARCADE-DAT-CONTAMINATION-8`); tamaño distinto (resto de plataformas) → gana el más grande; tamaño igual y contenido realmente distinto, no-NES → gana lo ya organizado por defecto (mismo criterio que NES, extendido por consistencia — ningún criterio de tamaño puede desempatar cuando literalmente son iguales). Resultado: **160 `kept_dest`** (90 CRC-idénticos + 5 NES + 52 empates no-NES + 13 del criterio de tamaño), **8 `kept_source`** (tamaño distinto, ganó Unknown/), **0 errores**. Re-consulta tras aplicar: **0 conflictos restantes** en `Unknown/` | `web/inbox_pipeline.py:23-37` (`_same_content`, sin arreglar — el bug de raíz sigue ahí para el próximo lote de conflictos), script de sesión no versionado | ✅ los 168 conflictos de hoy resueltos y verificados (0 restantes); 🔵 `_same_content()` documentado como causa raíz pero sin arreglar (afectaría también a la detección de conflictos genérica, no solo arcade) |
| ARCADE-DAT-CONTAMINATION-11 | **Pregunta abierta desde `Día51` resuelta 2026-09-04**: "¿fusionar `mame/`/`fbneo/`/`cps1-3/` con `arcade/`, o dejarlos separados?" — ya no aplica, el pipeline ya unificó todos los ROMs en `arcade/` sin que nadie lo decidiera explícitamente (`E:` 16.491 archivos en `arcade/` vs 25/1/77/96/26 en `mame/fbneo/cps1/cps2/cps3`; `H:` 11.045 vs 24/0/7/19/1). Verificado el contenido de las carpetas viejas: **0 ROMs**, solo saves (`.nv`/`.hi`/`.fs`), configs de mando (`.cfg`) y media de scraper — residuo de antes de la unificación. **Hallazgo real derivado**: el sync SÍ cubre esos saves hoy (`sync.sources` "RetroArch" apunta a la biblioteca entera, `sync_saves()` hace `rglob` recursivo filtrando solo por extensión — da igual la carpeta), pero **`.fs` (savestate de FBNeo para CPS3: `sfiii3.fs`, `redearth.fs`, `jojoba.fs`, `sfiii2.fs`) no estaba en `save_extensions` ni `state_extensions`** (`config.py`) — nunca se subía/bajaba. **Arreglado en la misma sesión** (fix de una línea, causa raíz clara): `.fs` añadido a `state_extensions` (`config.py:591-594`). 1157/1157 tests en verde, ruff limpio. `.cfg` (remap de mando, no progreso de partida) queda fuera a propósito, no es un gap | `config.py:591-594` | ✅ pregunta cerrada + gap `.fs` arreglado |
| ARCADE-DAT-CONTAMINATION-9 | **✅ Hecho 2026-09-04** (lector SD conectado). Auditoría de solo lectura (script de sesión, reutiliza `is_arcade_zip_container()` ya versionada — `DECOMPRESS-ARCADE-GAP-3` — en vez de reimplementar el voto CRC): **562 ZIPs fuera de `arcade/`** revisados, **118 con TODAS las entradas votando arcade**, 0 corruptos. **Hallazgo antes de tocar nada**: 89 de los 118 ya vivían dentro de `_descartados/` de su plataforma (basura ya perdedora del dedup, ej. `amiga\_descartados\Badlands (Europe).zip`) — no son contenido activo, se dejaron intactos en su sitio (no se "revive" basura). Solo **29 estaban en uso real** (sirviéndose desde la carpeta de plataforma). Aislados en `H:\ROMs\_ARCADE_MISFILED_STAGING\` y pasados por `organize-source --apply`: **19 movidos** directo a `arcade/` (set completo, sin extraer), **10 ya existían en `arcade/`** con ese nombre — de esos, 2 (`Phoenix`, `Pooyan`) el propio pipeline los descartó bien (SHA1 exacto ya conocido), pero **8 quedaron mal**: el resto del pipeline (scan+match+organize tras el paso de ruteo arcade) los reclasificó de vuelta a su carpeta de consola original en vez de descartarlos — bug de proceso, no de los datos (mismo contenido por CRC de entrada, SHA1 de archivo distinto por empaquetado/compresión, así que el dedup por SHA1 exacto no los pilla). Verificado 1 a 1 (SHA1 de cada par `arcade/` vs `consola/`, todos `DIFFERENT` a nivel de archivo pero coinciden en contenido por CRC) y movidos a mano a `_descartados/` de su plataforma (`atari2600`×3, `atari7800`×1, `atarilynx`×2, `c64`×2). `rommgr scan` de refresco sobre `H:\ROMs` completo: 27.068 archivos, 0 errores, 29 huérfanos limpiados. **Hallazgo de proceso para ARCADE-DAT-CONTAMINATION-10-like runs futuros**: cuando `organize-source` encuentra un ZIP arcade que "ya existe" en destino, el archivo se queda en el origen y el resto del pipeline lo reclasifica por plataforma de carpeta en vez de descartarlo — revisar a mano el resultado de cada "ya existe" (WARNING en el log) antes de dar la tarea por cerrada | `H:\ROMs\` | ✅ 118/118 procesados (89 basura ya descartada sin tocar, 29 activos reclasificados a `arcade/` o `_descartados/`) |

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
| PSX-STRUCTURE-3b | **✅ Resuelto 2026-09-04**: los 42 casos sin tocar de `E:` (reproducción fiel del criterio original — `PLATFORM_BY_EXTENSION` vs `PLATFORM_BY_FOLDER` de la carpeta contenedora, no ambigua, sobre las 47 carpetas de plataforma reconocidas excluyendo `arcade/` — dio 42 exacto, 33 `.nes` + 9 `.u1`, confirma que el criterio no cambió). **Los 33 `.nes`**: los 33 tienen un fichero con **nombre idéntico** ya en `nes/`/`fds/` (mismo tamaño en casi todos los casos, SHA1 distinto — típico de cabecera iNES distinta entre un rip de Virtual Console y el dump No-Intro estándar). Verificado con el matcher de catálogo (6 muestras): mismo título de catálogo en ambos lados en las 6 — confirma mismo juego, no mismatch; en `Darkwing Duck` la copia de `nes/` es la verificada por SHA1 exacto (`high`) y la mal ubicada no (`low`). **33/33 movidos** a `_descartados/` de su carpeta de origen. **Los 9 `.u1`**: NO todos son chips arcade — verificado contra `load_arcade_crc_index()`: solo **4/9** calzan (`epr-666.u1`→`carnival`, `epm7032.u1`→`rabbit`/variantes, `01.u1`→`candy`, `lh53882d.u1`→`mouja`); los otros 5 (4 en `megadrive/`, 1 en `gamegear/`) no calzan contra el índice cargado — 3 de ellos tienen un fichero hermano `.u2` al lado (patrón hi/lo de placa arcade), posible bootleg no cubierto por el DAT actual, sin confirmar, **dejados sin tocar**. De los 4 confirmados, verificado con `load_arcade_manifest()` cuántos ROMs exige cada set completo: `epm7032.u1` es **duplicado real** (el chip ya está cubierto por 3 sets `rabbit*` completos ya en `arcade/`) → descartado a `ps3/_descartados/`. `epr-666.u1`/`01.u1`/`lh53882d.u1` son el **único fragmento conocido** de sets (`carnival` 38 ROMs, `candy` 22, `mouja` 14) que **no existen en absoluto** en `arcade/` — no son duplicados, tratados igual que los "incompletos" de `ARCADE-DAT-CONTAMINATION-10`: movidos a `arcade/_incompletos_pendiente_redescarga/<set>/`, no descartados como basura. `rommgr scan` de refresco: 100.643 archivos, 0 errores, 37 huérfanos limpiados (33+4). **`H:\ROMs` (5 conflictos análogos) sin tocar** — pendiente de sesión aparte | `E:\Carpetas anbernic` | ✅ 37/42 resueltos (33 `.nes` + 4 `.u1`), 5 `.u1` dudosos documentados sin tocar |
| PSX-STRUCTURE-4 | **Decisión confirmada 2026-09-02**: subcarpeta por juego para `psx/` (y el resto de `_DISC_SUBFOLDER_PLATFORMS` en `operation_planner.py:19-22` — saturn, dreamcast, wii), no carpeta plana. Ya es la convención implementada (`move_disc_set_to_subfolder`, `renamer/file_renamer.py:211`; target derivado en `operation_planner.py:159-168`). Bloqueos originales ya resueltos: PSX-STRUCTURE-1 (30/33, 3 restantes documentados para re-descarga, decisión del usuario de no mezclar), PSX-STRUCTURE-2 (✅ cerrado del todo, ver PSX-STRUCTURE-2b), DECOMPRESS-ARCADE-GAP-1 (✅ hecho), `CATALOG-MATCH-BUG-1`/`GBA-MISPLACED-2` (✅ 2026-09-03), `CATALOG-MATCH-REGION-1` (✅ 2026-09-04, PR #289 mergeada). **Re-medido 2026-09-04 tras el merge**: de los 456 casos PSX ambiguos originales, 167 (37%) ya resuelven región correcta; **quedan 289 (63%) sin resolver** (`CATALOG-MATCH-REGION-2`, diagnóstico hecho, sin arreglar). Migrar `psx/` ahora usaría el título ambiguo/incorrecto de esos 289 como nombre de carpeta destino — mismo riesgo original, alcance menor pero no cero. **Decisión pendiente del usuario**: ejecutar `apply` ya (aceptando que 289 sets quedarán con nombre de carpeta potencialmente erróneo, corregible después) vs. esperar a `CATALOG-MATCH-REGION-2` | `H:\ROMs\psx`, `E:\Carpetas anbernic\psx`, `catalog/matcher.py:270` | 🟡 desbloqueada parcialmente (37% resuelto), decisión de ejecución pendiente del usuario |

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
| PSX-ORPHAN-4 | `Fear Effect (USA)` disco 2 — confirmar si nunca se tuvo o se perdió; mientras tanto, sacar los 3 `.cue` de `_descartados/` de vuelta a `psx/` (referencian bins que sí existen, no hay conflicto de nombre). **Re-verificado 2026-09-09**: la mitad de "sacar los .cue" ya no aplica — discos 1/3/4 están hoy en `psx/` como `.chd` (no `.bin`/`.cue`) y `psx/_descartados/` no tiene ningún `.cue` (0 en toda la carpeta); entre el hallazgo original (2026-08-26) y hoy, una conversión a CHD ya reubicó y limpió esos archivos sin que este ítem se cerrara. **Confirmado con el usuario 2026-09-09: nunca se tuvo el disco 2** — gap de origen, no una pérdida | `psx/_descartados/Fear Effect (USA) (Disc {1,3,4}).cue` | ✅ cerrado 2026-09-09 — nada que mover, disco 2 nunca existió en la colección |
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
| DEDUP-RENAME-2 | **El usuario no encuentra cómo aplicar la función de duplicados a la Anbernic** (feedback 2026-08-29, aclarado tras TABS-FIX-6 archivar la pestaña Duplicados en favor de "Revisar copias" dentro de Organizar). `DEVSEL-FIX-1` (`archivo.md`) dice que las acciones de duplicados ya enrutan por dispositivo — investigar si "Revisar copias" realmente expone/filtra por Anbernic en la UI actual o si el selector de dispositivo lo oculta; confirmar con archivo:línea antes de arreglar | `web/builders/duplicates.py` (`_build_review_queue`), `web/static/js/tabs/review_copies.js` | ✅ **investigado 2026-09-07 — no es un bug de filtrado: "Revisar copias" ya incluye los duplicados de la Anbernic automáticamente, sin selector que los oculte; la confusión probable es de UI/descubribilidad, documentada abajo.** `GET /api/review-queue` (`web/handlers/duplicates.py:161-165`) no acepta ningún parámetro de dispositivo/`source_root` — siempre llama a `_build_review_queue(repository, repo_android, config)` con ambos repos fijos (`repository_android` es `LibraryRepository(config.database_path_android)`, creado incondicionalmente en `cli.py:467`, nunca `None`). `_build_review_queue`/`_review_groups_for_repo` (`web/builders/duplicates.py:602-663`) consulta siempre los dos repos y **fusiona el resultado en una sola cola** — PC y Android nunca se agrupan como "el mismo duplicado" entre sí (ver docstring), pero sí aparecen juntos en la lista. `apiFetch` (`web/static/js/api.js:15-19`) es un `fetch()` desnudo, no inyecta ningún filtro de dispositivo. Confirmado que no hay ningún selector de dispositivo en `tab-plan.html` cerca de "Revisar copias" (`review-queue-content`, línea 68) que pudiera ocultar nada — la sección no tiene ningún control de filtro. **Causa probable real de la confusión (UX, no lógica)**: la sección "1. Plan de renombrado", justo encima en la misma pestaña, sí está filtrada por dispositivo y muestra un banner explícito "Viendo: PC — ..." / "Viendo: {consola} — ..." (`web/static/js/tabs/organize.js:48-67`, vía `window._activeDevice`/`_deviceRoot()`). "Revisar copias" no tiene ningún banner equivalente — el único indicio de que una entrada vive en la consola es una etiqueta pequeña por fila (`web/static/js/tabs/review_copies.js:111-113`, `e.is_device` → badge con `_devName`), fácil de pasar por alto. Un usuario viendo "PC" en la sección de arriba puede asumir razonablemente que la de abajo también está filtrada a PC. Otra causa probable, no descartable sin biblioteca real: si la Anbernic nunca se escaneó desde la app web (`/api/scan` con una ruta fuera de `library_root` — ver `_repo_for_path`, `web/builders/common.py:141-167`), `library_android.db` está vacío y "Revisar copias" no tendría nada de consola que mostrar, con razón. Sin cambio de código en esta sesión (regla del proyecto de investigar antes de arreglar) — posible follow-up de UX: un banner o nota en "Revisar copias" aclarando que ya cubre PC + Anbernic combinados, en vez de depender solo de la etiqueta por fila |
| DEDUP-RENAME-2b | **Follow-up de UX de `DEDUP-RENAME-2`**: banner explícito en "Revisar copias" aclarando que la sección combina PC + Anbernic (a diferencia de "1. Renombrar" arriba, que sí sigue el selector global de dispositivo) — para que el usuario no asuma que también está filtrada al dispositivo activo | `web/static/partials/tab-plan.html`, `web/static/js/tabs/review_copies.js` | ✅ implementado 2026-09-07 — nuevo `<div id="review-queue-context-bar">` en `tab-plan.html` (mismo patrón visual que `plan-context-bar`, oculto por defecto), poblado en `loadReviewQueue()` con "Combinando PC + {consola}" usando el `window._devName` global ya existente (sin fetch extra). Verificado sirviendo HTML/JS por curl (sin extensión de Chrome disponible en esta máquina para captura de pantalla). Sin tests nuevos — cambio puramente visual/textual, sin lógica que testear; suite completa 1228/1228 sin cambios |
| DEDUP-RENAME-3 | **Caso real encontrado 2026-08-29 buscando "Mario Kart DS" en Juegos**: 8 filas para el mismo juego, 3 con **el mismo SHA1** (`691E00D9A5...`). **Investigado — causa raíz encontrada, no es un bug de "Revisar copias"**: consulté `/api/review-queue` en vivo y el grupo SHA1 de Mario Kart DS **sí existe y sí tiene recomendación** (`reasons:["sha1"]`, `recommended:true` en la copia de `E:\Carpetas anbernic\nds\...(USA)...`) — el mecanismo funciona. El problema real es que de las 3 filas, **una es un registro fantasma**: `source_path` apunta a `C:\Users\rammu\Documents\projects\Retro_gaming_app\Este equipo\RG556\Ambernic\nds\Mario Kart DS (USA, Australia)...nds` — la ruta MTP fantasma del bug **INBOX-CFG-1** (`archivo.md`, "arreglado" 2026-08-13), que **ya no existe en disco** (confirmado, `ls` falla) pero la fila de BD nunca se borró. Motivo: `prune_stale_entries()` (`database/repositories/games.py:328-340`) solo borra filas bajo el `source_root` que se está escaneando — como esta fila vive bajo una ruta completamente distinta (dentro del propio repo del proyecto, nunca bajo `E:\Carpetas anbernic`), **ningún scan de la biblioteca real la toca jamás**, quedó huérfana para siempre. **Alcance real, no solo Mario Kart DS**: `SELECT COUNT(*) FROM games WHERE source_path LIKE '%Este equipo%'` → **1.508 filas fantasma** en `library_pc.db`. Estas mismas filas también explican **ZIP-ROUTE-7** (confirmado: `id=65864`, `unknown\10192n.rom`, aparece en `/api/games` con `canonical_title: null` — exactamente "entradas sin portada" que reportó el usuario) — mismo origen, no dos bugs distintos. **Purgado de verdad 2026-08-29** (backup previo en `.rommgr/backup_ghost_purge_2026-08-29/library_pc.db`): script one-off reutilizando `repository.delete_game(id)` ya existente (cascada limpia de `game_metadata`/`game_tags`/`file_operations`, mismo mecanismo de REV43-10) — verificado primero que ninguna de las 1.508 rutas existe en disco (`Path.exists()`) antes de borrar ninguna, cero falsos positivos. Resultado: **1.508/1.508 borradas**, 0 restantes. Verificado en vivo: el grupo de Mario Kart DS en `/api/review-queue` pasó de 3 a 2 entradas (las 2 reales); `total_groups` de la cola bajó de 13.969 a 13.545 (grupos que solo eran fantasma+1 real dejaron de contar como duplicado); `id=65864` (`10192n.rom`) ya no aparece en `/api/games` | `database/repositories/games.py:328-340` (`prune_stale_entries`, scoping por `source_root` — causa de que nunca se autolimpiaran) | ✅ causa raíz documentada y purga ejecutada; sin cambio de código (el diseño de `prune_stale_entries` es correcto para su propósito, el problema era datos huérfanos de un incidente ya cerrado) |

---

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: JUNK-SMART-1/2/3, TABS-FIX-1..7 (+ TABS-FIX-6-DISC, DUP-RA-COLLISION-1), DEVSEL-FIX-1..4 (clasificador de basura por evidencia, auditoría UX Juegos/Organizar/Duplicados, selector de dispositivo — completas, 2026-07-08 a 2026-07-13).

---

### DUP-REGION-1/2 — Duplicados por región (mismo juego, distinta release No-Intro) + preferencias configurables (WIP retomado, pausado durante el roadmap 12)

`DUP-DISC-RA-1` (abajo) ya lo cita como origen aunque nunca tuvo sección
propia — quedó como WIP sin commitear en `git stash` desde antes del Día64
(roadmap 12 tuvo prioridad), retomado en rama propia a petición del usuario.

En plataformas de un solo archivo (GBA/GB/GBC/NES/SNES/...) el mismo juego
publicado en varias regiones No-Intro (`Tetris (USA)` vs `Tetris (Spain)`)
nunca se agrupaba en "Revisar copias" porque `canonical_title` incluye el
tag de región — son strings distintas, así que la unión por título exacto
nunca los enlazaba. Deliberadamente **excluido en `_MULTI_DISC_RISK_PLATFORMS`**
(PSX/Saturn/Dreamcast/Wii...): el propio comentario de la unión por título
exacto documenta por qué la coincidencia difusa es insegura ahí — la única
vez que se probó sin ese guard fusionó 18 discos regionales reales de Final
Fantasy VII en un solo grupo "duplicado" falso positivo.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-REGION-1 | Detectar el grupo (título difuso + plataforma, solo fuera de `_MULTI_DISC_RISK_PLATFORMS`) y añadir el motivo `"region"` a la cola de revisión — nunca auto-fusiona ni borra, solo recomienda cuál conservar (empate: integridad > soporte RA > carpeta correcta > región preferida > nombre) | `web/builders/duplicates.py` (`_review_groups_for_repo`, `region_linked_idxs`, `has_region_dup`) | ✅ implementado — confirmado contra la biblioteca real (2026-09-15, mencionado en el hallazgo original de Día64): 94 títulos GBA / 188 archivos, solo pares de región, ninguna secuela distinta fusionada por error (el tag de región es siempre un grupo `(...)` final, nunca parte del título) |
| DUP-REGION-2 | El desempate por idioma de `_review_entry_sort_key` era fijo (solo "¿es español?"); para el motivo `"region"` se necesita un ranking configurable por el usuario, no solo español-o-no. Nueva `DuplicatesConfig` (`config.py`): `preferred_regions` (lista ordenada, por defecto `["Spain", "Europe"]`) y `keep_both_regions` (si `True`, el motivo `"region"` no se dispara nunca — el usuario conserva todas las regiones a propósito) | `config.py` (`DuplicatesConfig`), `detection/region_parser.py` (`KNOWN_REGIONS`, para el selector de la UI), `web/builders/duplicates.py` (`_review_entry_sort_key` con `region_tiebreak`/`preferred_regions`), `web/builders/misc.py` (`_build_config`), `web/handlers/config.py` (`_save_config`, campos `duplicates.*`), `web/static/js/tabs/config.js` + `tab-settings.html` (picker de regiones con reordenar/quitar, checkbox "mantener todas") | ✅ implementado con tests (`test_same_title_cross_region_flagged_for_review`, `test_keep_both_regions_config_suppresses_region_groups`, `test_preferred_regions_config_overrides_default_ranking`) — 1370 tests totales, ruff limpio. ✅ **mergeado** (PR #327, `2173ff1`) — el backlog seguía diciendo "sin PR todavía" pese a estar ya en `develop` |

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
| DUP-DISC-RA-1b | **Parte 1 implementada 2026-08-30**: `ra_checker.check_library()` ya usa el hash de disco (vía `ra_disc_hash_cache.get_psx_disc_hash`, cacheado en `.rommgr/ra_cache/psx_disc_hashes.json` por `(source_path, mtime, size)`) en vez de `row["md5"]` para consolas con `console_id in _DISC_HASH_CONSOLE_IDS` (por ahora solo PSX, 12). Wireado hasta `/api/ra-check` (`web/handlers/sync.py`, pasa `config.chdman`). Test `test_playstation_uses_disc_hash_not_stored_md5`. **Parte 2 implementada 2026-09-21** (rammu): nueva pasada de unión en `_review_groups_for_repo` (mismo patrón que `crossfmt`/`region`, pero uniendo por hash de disco RA en vez de título difuso) — dos filas de la cola de duplicados con el mismo hash de disco RA se tratan como la misma edición aunque no compartan SHA1 ni `canonical_title`. Alcance real: `_DISC_HASH_CONSOLE_IDS` (`ra_checker.py`) ya trae hash cacheado para PSX **y también GameCube/Wii** (`get_gamecube_wii_disc_hash`, más completo de lo que decía esta fila — Saturn/Dreamcast siguen sin cache wireada, `DUP-DISC-RA-1c` dejó explícitamente esa parte fuera). Nuevo motivo `"disc_hash"` en la cola (`reasons`), etiqueta añadida en `review_copies.js` (`_REASON_LABELS`). Cubre exactamente el caso real de `ANDROID-DUP-1` (`Crash Bandicoot (USA)` en `.bin+.cue`/`.chd`/carpeta CloneCD legacy con nombre de serial, sin `canonical_title` en la copia legacy — invisible a `sha1`/`title`/`crossfmt` hasta ahora). 2 tests nuevos (`test_disc_hash_union_links_legacy_dump_with_no_catalog_match`, `test_disc_hash_union_skips_when_hashes_differ`), suite completa 1424 tests (3 fallos son los ambientales ya conocidos de ADB conectado). **Validado contra `library_pc.db` real 2026-09-21** (345 PlayStation + 59 GameCube + 118 Wii, la biblioteca real de `E:\Carpetas anbernic`): 3 min de ejecución (la caché de hashes ya cubría casi todo), 1829 grupos totales en la cola, **1 grupo nuevo vía `disc_hash`** — `Resident Evil 3 - Nemesis (USA, Canada).chd` enlazado con `resident evil 3.chd` (nombre no canónico), confirmando que el hash de disco RA funciona en producción sin errores. **Matiz**: el escenario que motivó la tarea (`ANDROID-DUP-1` — volcado legacy CloneCD con nombre de serial `[SCUS-nnnnn]`, invisible a sha1/title/crossfmt) vive en la RG556 vía ADB (`/storage/521D-04EA/ROMs/`), un medio físico distinto de `E:\Carpetas anbernic` — validar ese caso exacto requeriría copiar esos archivos legacy localmente primero (el hash de disco RA necesita leer el archivo directo, ADB no sirve sin montar el dispositivo), sesión aparte, sin hacer todavía | `retroachievements/ra_checker.py`, `retroachievements/ra_disc_hash_cache.py`, `web/handlers/sync.py`, `web/builders/duplicates.py` (`_review_groups_for_repo`, parte 2 nueva), `web/static/js/tabs/review_copies.js` | ✅ hash-check + agrupado por edición implementados y validados contra datos reales; caso legacy CloneCD de la RG556 (ADB) sigue sin validar |
| DUP-DISC-RA-1c | **Implementado 2026-09-07**: mismo algoritmo pero para Saturn/Dreamcast — Wii sigue sin aplicar (no es un CD, RA lo hashea distinto, formato propio). Investigado directamente en la fuente de rcheevos (`github.com/RetroAchievements/rcheevos`, `src/rhash/hash_disc.c` — `rc_hash_sega_cd()` para Saturn, `rc_hash_dreamcast()` para Dreamcast — y `cdreader.c`, fetch directo con `curl`). Hallazgo que simplificó bastante el trabajo: Saturn NO hace boot-exe lookup como PSX — RA solo hashea el header crudo de 512 bytes al principio de la pista 1 (comentario propio de rcheevos: "hashing the volume and ROM headers is sufficient"), sin tocar el sistema de archivos. Dreamcast sí es más parecido a PSX: hashea 256 bytes de IP.BIN (pista 3, no la 1 — GD-ROM) + el ejecutable de arranque (nombre en el offset 96 de IP.BIN), localizado por el mismo lookup ISO9660 genérico que ya usaba PSX (confirmado en la fuente: `rc_cd_find_file_sector` es la misma función para todas las consolas, PSX incluida — nunca fue específica de PSX). **Refactor previo sin cambio de comportamiento**: el lector de sectores CD + el buscador ISO9660 (antes solo en `ra_hash_psx.py`) se extrajeron a `retroachievements/ra_cd_image.py` nuevo, compartido — evita triplicar la misma lógica ya que las tres consolas usan literalmente el mismo algoritmo de lectura de sectores/geometría. 7 tests de `ra_hash_psx` siguen en verde tras la extracción. Módulo nuevo `retroachievements/ra_hash_saturn_dreamcast.py`: `compute_saturn_ra_hash()` (`.bin`/`.cue`/`.chd`) y `compute_dreamcast_ra_hash()` (`.bin`/`.cue`/`.chd`/`.gdi` — parser propio de `.gdi` para resolver la pista 3 por número, ya que en GD-ROM cada pista es normalmente su propio archivo). 7 tests nuevos con imágenes sintéticas (mismo patrón que `test_ra_hash_psx.py`) — a diferencia de PSX, **sin verificar todavía contra caché RA real** (sin biblioteca Saturn/Dreamcast en esta máquina): la corrección del parseo de bytes está probada, la fidelidad al hash real de RA no. Wireado hasta `ra_checker.py`/`ra_disc_hash_cache.py` (equivalente a la "parte 1" de `DUP-DISC-RA-1b` para PSX) queda **fuera de esta tarea a propósito** — el pedido original decía "mismo algoritmo", no el wiring; candidato natural para una `DUP-DISC-RA-1d` si se quiere activar en la comprobación RA real. Suite completa 1235/1235 | `retroachievements/ra_cd_image.py` (nuevo), `retroachievements/ra_hash_saturn_dreamcast.py` (nuevo), `retroachievements/ra_hash_psx.py` (refactorizado, sin cambio de comportamiento), `tests/test_ra_hash_saturn_dreamcast.py` (nuevo) | ✅ algoritmo implementado y probado con datos sintéticos; sin verificar contra caché RA real ni wireado a `ra_checker.py` todavía |
| DUP-DISC-RA-1e | **Intento de validación real 2026-09-07 bloqueado por gap de formato**: al intentar validar `compute_saturn_ra_hash`/`compute_dreamcast_ra_hash` contra la biblioteca real (`F:\Juegos Retro`, sí montada en esta máquina) se encontró que Saturn no tiene ningún ROM real ahí (solo `saturn\media\images`/`videos`, artefactos del scraper) y que los 5 juegos reales de Dreamcast están **todos en `.cdi`** (`Crazy Taxi 2`, `Dead or Alive 2 (Beta)`, `Legacy of Kain - Soul Reaver`, `Marvel Vs Capcom 2` [además tiene `.A1.bin`, que es un save de VMU, no la imagen del disco], `Sonic Adventure`). `compute_dreamcast_ra_hash()` (`retroachievements/ra_hash_saturn_dreamcast.py:145-162`) solo reconoce `.gdi`/`.cue`/`.bin`/`.chd` — devuelve `None` para `.cdi` sin intentarlo siquiera, así que la validación contra la caché RA real de `DUP-DISC-RA-1c` sigue sin poder hacerse en esta máquina hasta que se añada un parser de `.cdi` (formato DiscJuggler — cabecera y layout de pistas distintos de un `.bin`/`.cue` crudo, no es un simple alias). **Investigado a fondo 2026-09-07 (segunda pasada) y cerrado sin implementar**: se probó primero convertir con `chdman createcd` (la propia herramienta del proyecto) — la conversión se quedó colgada sin avanzar (>15 min, salida de 124 bytes). Investigando la causa en el código fuente real de MAME (`src/tools/chdman.cpp` → `cdrom_file::parse_toc`, `src/lib/util/cdrom.cpp:2966-2990`, descargado con `curl` vía `raw.githubusercontent.com`): **`chdman` tampoco soporta `.cdi`** — el dispatcher por extensión solo reconoce `.gdi`/`.cue`/`.nrg`/`.iso`/`.cdr`/`.toast`; cualquier otra extensión cae al parser de texto genérico CDRDAO `.toc`, que intenta leer el archivo binario `.cdi` como líneas de texto (de ahí el cuelgue, no lentitud). Y **`rcheevos` (la librería de referencia de RA) tampoco soporta `.cdi`**: su propio dispatcher (`src/rhash/cdreader.c:777-788`, ya consultado para `DUP-DISC-RA-1c`) solo reconoce `.cue`/`.gdi` por extensión — cualquier otra cosa (incluido `.cdi`) se abre como `.bin` crudo de una sola pista, lo que daría un hash **silenciosamente incorrecto**, no un "no soportado" limpio. Con ni RA ni chdman soportando el formato, escribir un parser propio de DiscJuggler no tendría ningún oráculo contra el que validar que el hash resultante coincide con el real de RA — el riesgo de dar por buena una implementación que en realidad nunca coincidiría es alto. **Decisión (discutida con el usuario 2026-09-07): no implementar por ahora** — se retoma si aparece una vía de validación independiente (chdman añade soporte `.cdi` en una versión futura, o se publican hashes RA de Dreamcast conocidos de la comunidad) | `retroachievements/ra_hash_saturn_dreamcast.py:145-162` (`compute_dreamcast_ra_hash`) | ⚪ investigado y cerrado sin implementar — ni RA ni chdman soportan `.cdi`, sin oráculo para validar un parser propio; Saturn sigue sin ningún ROM real que validar en esta biblioteca |
| DUP-DISC-RA-2 | **Implementado y verificado 2026-08-30** (pedido explícito del usuario: "usa chd como formato de psx"). Recomendación confirmada: **CHD**, un archivo por disco, soportado nativamente por RetroArch/`chdman` (ya en `tools/`). Descubierto que ya existía un conversor sin usar (`rommgr convert-chd` / `converters/chd_converter.py`) que solo cubría `.cue`+`.bin` reales — **extendido** en vez de duplicado: (1) `find_bare_bin_files()` descubre `.bin` sueltos sin `.cue` (el caso mayoritario real, ver DUP-DISC-RA-2b) validando con `compute_psx_ra_hash()` que de verdad son un disco legible, no una pista de audio huérfana; (2) `synthesize_cue_text()` genera un `.cue` mínimo de una pista reutilizando `detect_bin_cue_mode()` (nuevo en `ra_hash_psx.py`); (3) `parse_bins_from_cue()` arreglado para resolver solo por nombre base (bug real encontrado: `.cue` con ruta absoluta rota, ver DUP-DISC-RA-2b, hacía que el `cwd=` existente no sirviera de nada); (4) **cada conversión se verifica comparando el hash RA de disco antes/después** (`_verify_ra_hash`) — si no coincide, se borra el `.chd` y el original queda intacto, nunca se sobreescribe a ciegas. `chdman createcd` necesita la palabra `BINARY` en la línea `FILE` del `.cue` sintético (bug propio encontrado y arreglado — sin ella da "Unhandled track type"). 13/13 tests en `test_chd_converter.py` (incluye conversión real de punta a punta con `chdman.exe` y un caso de mismatch de hash forzado). **Dry-run contra la biblioteca PSX real** (`rommgr convert-chd "E:\Carpetas anbernic\psx"`): **181 convertibles** (bare-bin + 0 cue reales, los 18-22 `.cue` reales están todos rotos, ver DUP-DISC-RA-2b), 22 fallos (cue roto), 1 ya convertido. **No ejecutado con `--apply`** contra la biblioteca real — pedido explícito del usuario de construir la herramienta y ejecutarla aparte; nota de rendimiento: un solo disco de ~600MB tardó >10 min con la compresión por defecto de `chdman` en esta máquina, así que los 181 son horas, no minutos — pensar en correrlo en background/durante la noche | `converters/chd_converter.py`, `retroachievements/ra_hash_psx.py` (`detect_bin_cue_mode`), `tests/test_chd_converter.py`, `cli.py` (ayuda actualizada) | ✅ herramienta lista y verificada; ejecución real pendiente, la lanza el usuario |
| DUP-DISC-RA-2b | **Ya no aplica — verificado 2026-09-08 contra `E:\Carpetas anbernic\psx` real**: los 18-22 `.cue` rotos del hallazgo original (2026-08-30) ya no existen tal cual. Reutilizando `parse_bins_from_cue()` (el mismo parser de `DUP-DISC-RA-2`, solo lectura) sobre los **33 `.cue` reales de hoy: 0 rotos** — confirmado además con `rommgr convert-chd "E:\Carpetas anbernic\psx"` (dry-run): `Would convert: 33 | Would skip: 0`. Los dos casos citados en el hallazgo original (`Chrono Cross (Japan).cue`, `Crash 2.cue`) ni siquiera existen ya en la carpeta — `Chrono Cross` ahora vive como `Chrono Cross (USA, Canada) (Disc 2).chd` (ya convertido). La biblioteca cambió entre el hallazgo y hoy (probable limpieza/conversión de otra sesión, sin diario que lo documente explícitamente) y el problema desapareció como efecto colateral — mismo patrón que `LIBRARY-SYNC-STALE-1d` esta misma sesión. Sin cambios de archivos en esta verificación (solo lectura) | `psx/*.cue` | ✅ verificado 2026-09-08 — ya no hay `.cue` rotos |

---

### ANDROID-DUP-1 — Duplicados reales en la propia Anbernic (DaijiShō/iSuu), nunca comprobados: dedup solo se ha ejecutado contra bibliotecas PC (hallazgo 2026-09-19, RG556 `RG556006101273`, ADB en vivo)

Origen: el usuario reporta duplicados visibles en DaijiShō e iSuu en la RG556
— PS2 con **todos** los juegos duplicados, y varios títulos sueltos en GBA/PSX
(ejemplos dados: Crash Bash, Crash 2). Sospecha propia del usuario, confirmada
por la investigación: **la función de duplicados nunca se ha ejecutado contra
la biblioteca Android real** — todo el trabajo de `DUP-REGION-1/2`,
`DUP-DISC-RA-1*`, `GBA-DUAL-FOLDER-1`, `DUALFOLDER-12` se hizo contra
bibliotecas **PC** (`F:\Juegos Retro` en "Ruben", `E:\Carpetas anbernic` en
"rammu"). El proyecto sí soporta un repo Android separado
(`library_android.db`, seleccionado por `_repo_for_path()` en
`web/builders/common.py:141-167` para cualquier ruta fuera de
`config.library_root`, documentado en `config.py:423-432`) y
`_review_groups_for_repo()` (`web/builders/duplicates.py:743`, invocado una
vez por repo en `web/builders/duplicates.py:519-537,714`) ya sabe iterar sobre
`repository_android` — pero **`library_android.db` lleva sin re-escanearse
desde 2026-09-12** (`.rommgr/library_android.db`, mtime confirmado), una
semana antes de esta sesión y antes de varios syncs recientes (GBA
2026-09-14, PSX CHD hasta 2026-09-13, PS2 hasta 2026-09-15) — cualquier pasada
de dedup contra ese snapshot habría estado desactualizada igualmente.

**Verificado en vivo por ADB contra `/storage/521D-04EA/ROMs/` de la RG556**
(no contra `library_android.db`, directamente contra el dispositivo):

| Plataforma | Hallazgo | Evidencia |
|---|---|---|
| **PSX** | El mismo disco coexiste en 2-3 formatos/nomenclaturas a la vez: `.bin`+`.cue` **y** `.chd` del mismo release (la limpieza post-conversión de `DUP-DISC-RA-2` nunca se ejecutó/completó en este dispositivo — esa tarea ya documentaba "ejecución real pendiente, la lanza el usuario"), más un tercer set de volcados **legacy con nombre de serial** (`[SCUS-94900]`, `[SCUS-94570] [bin]`, `[SCUS-94426] [bin]`, 39 entradas `[SCUS/SLUS/SCES/SLES-nnnnn]` en total) que preceden a este proyecto — mtimes de 2003/2006 en varios `.bin`/`.img`. Caso confirmado exacto del usuario: `Crash Bandicoot (USA)` existe como `.bin+.cue`, `.chd`, y carpeta legacy `Crash Bandicoot [U] [SCUS-94900]/` con `.ccd`/`.img`/`.sub` (CloneCD) — el mismo disco 3 veces. `Crash Bash` tiene además `.chd` (Europe) + `.chd` (USA) + carpeta legacy `[SCUS-94570] [bin]`. `Crash Team Racing` tiene `.chd` + carpeta legacy `[SCUS-94426] [bin]` + un tercer `CTR - Crash Team Racing (Europe).zip` sin descomprimir | 1231 entradas en `psx/`: 305 `.chd`, 490 `.bin`, 131 `.cue`, 46 CloneCD (`.img`/`.ccd`/`.sub`), 39 legacy serial, 89 subcarpetas (mayoría sets multi-disco legítimos, al menos 3 confirmadas como duplicados legacy) |
| **GBA** | Volcados legacy pre-No-Intro (formato `[E]`/`[U]`/[J]`, típico de sets GoodGBA anteriores a este proyecto — mtimes 2015, mucho antes de que existiera `rom_manager`) conviven con las copias renombradas canónicas No-Intro del mismo juego, más `.sav`/`.sgm` huérfanos ligados a esos volcados legacy. Además ZIPs sin descomprimir junto a su `.gba` ya extraído — violación del principio del Pilar 2 (aunque estos son archivos ya existentes en el dispositivo antes del proyecto, nunca pasaron por el Inbox) | 1490 entradas en `gba/`: 1297 `.gba`, 120 `.zip`, 91 con patrón `[E]`/`[U]`/`[J]` legacy, 45 `.sav`/`.sgm` |
| **Carpetas Title Case + slug paralelas** | Mismo patrón que `GBA-DUAL-FOLDER-1`/`PS2-DUAL-FOLDER-1`/`DUALFOLDER-12`, pero **nunca aplicado a este dispositivo** — esas tareas solo tocaron la máquina "Ruben". En la RG556 conviven `Atari 2600/`+`atari2600/`, `Famicom Disk System/`+`fds/`, `Game Gear/`+`gamegear/`, `Master System/`+`mastersystem/` | `ls /storage/521D-04EA/ROMs/` — 4 pares confirmados |
| **PS2 ("todos los juegos duplicados" en iSuu)** | **Sin duplicación de archivos** — `ps2/` es una sola carpeta plana, 26 `.iso`/`.chd`, sin nombres repetidos ni carpeta `PlayStation 2/` paralela. La causa no puede estar en los archivos de este proyecto; el síntoma ("todos" los juegos, no solo algunos) apunta a **configuración del propio launcher** (p. ej. dos perfiles de sistema/emulador en iSuu/DaijiShō apuntando ambos a `ROMs/ps2/`) — fuera del alcance de este repo, requiere revisar la config de iSuu en el dispositivo, no el código de `rom_manager` | `ls -la /storage/521D-04EA/ROMs/ps2/` — 26 archivos, sin duplicados |
| **Corrección 2026-09-19 (sesión de reparación)**: la afirmación original de este hallazgo ("`fds/` contiene un set casi completo de NES") era falsa — basada en un `ls` mal citado que mezcló la salida de dos comandos distintos. Re-verificado con comillas correctas: `fds/` tiene solo 27 entradas reales (mezcla de un par de ficheros tipo chip arcade sin identificar, `Balloon Fight`/`Ice Climber`/`Metroid`/`Super Mario Bros` en `.zip` y `.nes`, y 2 `.fds` genuinos), no un set NES completo. La carpeta `nes/` real sí tiene el problema — **~4022 entradas**, incluye volcados legacy `[!]`/`(J)`/`(U)` conviviendo con nombres canónicos No-Intro, parches de traducción `[T+...]` (legítimos, no son duplicados), pares `.nes`+`.zip` del mismo dump (viola Pilar 2), y ficheros sueltos tipo chip arcade (`1-5j.bin`, `10-9h.bin`) que no son NES en absoluto. Confirmado con el ejemplo del usuario: **42 entradas "Super Mario"** — algunas hacks legítimos (`[Hack] [Super Diego Bros]`, `Super Mario Bros. Extended`), pero varias duplicados reales del mismo juego bajo nomenclatura distinta (`Super Mario Bros. (W) [!].nes` vs `Super Mario Bros. (World).nes`). Un archivo está directamente mal clasificado: `Super Mario World (Asia) (En) (Pirate).nes` es un juego de **SNES**, no NES — mal colocado, ni siquiera es cuestión de duplicados | `ls /storage/521D-04EA/ROMs/nes/`, `ls /storage/521D-04EA/ROMs/fds/` |

**Por qué `DUP-REGION-1/2` y `DUP-DISC-RA-1*` no habrían bastado ni ejecutándose hoy mismo**:
`DUP-REGION-1` (`web/builders/duplicates.py`) agrupa por título difuso solo
para plataformas de un archivo, excluyendo PSX explícitamente
(`_MULTI_DISC_RISK_PLATFORMS`) — nunca iba a agrupar los casos PSX de arriba.
`DUP-DISC-RA-1b` (hash de disco RA para PSX) sí tiene el motor correcto para
esto, pero su "parte 2" (agrupar por edición completa en la cola de
duplicados) sigue **sin implementar**, tal cual quedó documentado en su
propia fila arriba. Y los volcados legacy con nombre de serial (`[SCUS-xxxx]`)
casi seguro ni siquiera matchean contra el catálogo por SHA1 (dumps de otra
fuente) — dependerían del hash de disco RA (`DUP-DISC-RA-1a`, ya implementado
y verificado) para reconocerse como el mismo juego, otra razón más para
completar `DUP-DISC-RA-1b` parte 2 antes de fiarse del todo de la cola de
duplicados en PSX.

**Recomendación (sin implementar, a decidir con el usuario)**:
1. Escanear `library_android.db` contra la RG556 real (vía ADB, ya que está
   conectada) para tener un snapshot actual antes de cualquier limpieza.
2. Completar `DUP-DISC-RA-1b` parte 2 (agrupado por edición vía hash RA en la
   cola de duplicados) — sin esto, los duplicados de formato/legacy en PSX
   seguirán invisibles para la herramienta aunque se re-escanee.
3. Extender `DUP-REGION-2`/la cola de revisión para reconocer volcados legacy
   pre-No-Intro (`[E]`/`[U]`/`[J]`, `[SCUS-nnnnn]`) como el mismo juego que su
   contraparte canónica — hoy dependen de que el matcher los reconozca, y no
   está confirmado que lo haga (`catalog/matcher.py::_match_by_title()`).
4. Verificar contenido real de `fds/` vs `Famicom Disk System/` antes de
   aplicar el criterio de `DUALFOLDER-12` a este par — no es un simple
   duplicado de nombre, puede haber NES mal ubicado.
5. `PS2` (iSuu) no es un bug de este repo — confirmar en el propio dispositivo
   si iSuu/DaijiShō tiene un sistema PS2 duplicado en su configuración.

**Primer fix en marcha** → rama `fix/duplicates-disc-format-set-integrity`
(PR #329): las comprobaciones de sibling/integridad (`_is_cue_sibling_bin`,
`_is_ccd_sibling_data`, `_is_broken_disc_entry`) usaban `Path.exists()` en el
propio `source_path` — siempre `False` para una fila escaneada por ADB, lo
que desactivaba en silencio toda la protección de siblings para el repo
Android. Explica directamente por qué el trío `.ccd`/`.img`/`.sub` de
`Crash Bandicoot [U] [SCUS-94900]` se agrupaba como si fueran 3 copias
independientes (recomendando conservar el `.ccd` de 790 bytes y descartar el
`.img`+`.sub`, los datos reales del disco), y por qué el trío
`.bin`/`.cue`/`.chd` de `Crash Bandicoot (USA)` caía al desempate
alfabético, prefiriendo el `.bin` sobre el `.chd` (contradice la decisión ya
tomada en `DUP-DISC-RA-2`). Corregido pasando un `known_paths` (los
`source_path` ya escaneados en ese repo) para verificar siblings contra la
BD en vez del filesystem local, más un tier explícito de formato de disco
(`.chd` > `.cue`/`.gdi` > `.ccd`). 4 tests nuevos, 1382 tests en verde. Sin
✅ mergeado 2026-09-19 (PR #329, squash, rama borrada) | `web/builders/common.py:141-167`
(`_repo_for_path`), `config.py:423-432` (`database_path_android`),
`web/builders/duplicates.py:519-537,714,743` (`_review_groups_for_repo`),
`retroachievements/ra_disc_hash_cache.py` (`DUP-DISC-RA-1b` parte 2
pendiente), `catalog/matcher.py::_match_by_title()` (sin confirmar
reconocimiento de volcados legacy) | 🔴 confirmado con evidencia real (ADB en
vivo), sin implementar — decisión de alcance y orden pendiente del usuario |

**Re-verificado 2026-09-30 contra `library_android.db` real (RG556 conectada), solo lectura:**

- **Causa raíz real de las filas fantasma** (los 2 discos españoles de Metal
  Gear Solid señalados en `ANDROID-DUP-PSX-1`, y probablemente más): la tabla
  `scan_runs` tiene un escaneo de `psx` (`id=19`) que **arrancó
  2026-09-28T16:09:52 y nunca terminó** (`finished_at: NULL`, `files_seen: 0`)
  — el último escaneo completo de `psx/` fue el `id=17` del 2026-09-20. Cualquier
  borrado hecho en el dispositivo entre esas dos fechas nunca se reconcilió
  contra la BD porque el escaneo que lo habría reflejado murió sin terminar.
  Causa del crash del `id=19` encontrada en `.rommgr/logs/rommgr.log`: **no
  fue un crash real** — un job de Inbox gigante (`zip-route-apply`, miles de
  operaciones) estaba corriendo justo a esa hora, y el proceso del servidor
  se reinició a las 17:16:50 (los daemons vuelven a arrancar en el log) con
  el scan de `psx/` todavía a medias — se quedó huérfano sin más.
  **Rescan de `psx/` relanzado 2026-09-30 con la Anbernic conectada**: 1579
  archivos, 1435 ROMs, 0 errores, hashes recalculados — pero **`pruned: 0`**
  pese a que el archivo de MGS España verificado seguía sin existir en el
  dispositivo (confirmado con `adb shell test -e` justo después del rescan).
  **Bug real encontrado y arreglado** (`fix/android-scan-prune-separator-bug`):
  `prune_stale_entries()` (`database/repositories/games.py:384`) construía
  `root_prefix = source_root + os.sep` — en Windows `os.sep` es `\`, pero las
  rutas de Android siempre usan `/`, así que `root_prefix` nunca coincidía
  con ninguna ruta real del dispositivo. **Esto significa que la poda nunca
  ha funcionado para ningún rescan de Android hecho desde esta máquina
  Windows**, sin ningún error visible — explica por completo por qué las
  filas fantasma se acumulan indefinidamente. Arreglado usando
  `is_device_path()` para elegir el separador correcto según el tipo de ruta,
  no según el SO anfitrión. 1 test nuevo
  (`test_prune_stale_removes_missing_android_path_on_windows`, reproduce el
  bug exacto), suite completa 1516/1516, ruff+format limpios. **Fix mergeado
  y verificado en real (PR #385)**: instancia real reiniciada con el código
  nuevo, rescan de `psx/` relanzado (sin recalcular hashes, solo listar) →
  **`pruned: 211`** (antes siempre 0). Las 8 filas fantasma de MGS España se
  quedaron en 4 — verificado que los 4 restantes (`.bin`+`.m3u` de cada
  disco) **sí existen de verdad en el dispositivo** (`adb shell test -e`); lo
  podado fueron exactamente los 4 `.chd`/`.cue` mal etiquetados como "(World)
  (4B4E083C) (Addon)" que ya se habían confirmado ausentes. Poda exacta,
  `ANDROID-DUP-PSX-1` queda resuelto del todo — no solo documentado.
- **Segundo bug real encontrado por error propio, sin arreglar todavía**: al
  verificar la poda con un segundo rescan `compute_hashes=False` (más rápido,
  solo para confirmar el fix anterior), las 1435 filas de `psx/` se quedaron
  sin `sha1`/`md5` — el upsert del scan (`web/handlers/scan.py:551-552`,
  `sha1=sha1_map.get(ap, "")`) sobrescribe siempre con cadena vacía cuando
  `compute_hashes=False`, en vez de conservar el hash ya guardado en la fila
  existente. Un rescan "rápido" (solo listar) después de uno completo borra
  todo el trabajo de hash del anterior sin avisar. Recuperado relanzando el
  rescan completo otra vez (`compute_hashes=True`) — sin arreglar el código
  todavía, candidato a tarea propia: el upsert debería hacer `COALESCE` con
  el `sha1`/`md5` ya existente en la fila cuando no se recalculan, no pisarlo
  con `""`.
  **`GAMEDB-HASH-COALESCE-1` -- arreglado 2026-10-02**: `upsert_game()`
  (`database/repositories/games.py:105-119`) ahora hace
  `sha1 = CASE WHEN excluded.sha1 != '' THEN excluded.sha1 ELSE games.sha1 END`
  (mismo patron para `md5` y `crc32`) en vez de pisar siempre con
  `excluded.*` -- un rescan rapido (`compute_hashes=False`) ya no borra el
  hash de un rescan completo anterior. Test nuevo
  (`test_upsert_game_quick_rescan_keeps_prior_hash` en `tests/test_repository.py`)
  reproduce el caso exacto (hash completo -> rescan rapido -> hash debe
  sobrevivir, otros campos si se actualizan). Sin commitear/pushear todavia.
- **Volcados legacy con nombre de serial — verificados por hash 2026-09-30**:
  tras la poda quedaron 40 filas `[SCUS-/SLUS-/SLES-/SCES-nnnnn]` en `psx/`
  (`LIKE '%[SCUS-%' OR ...`), de las cuales **solo 15 en formato hasheable**
  (`.chd`/`.bin`/`.cue` — `compute_psx_ra_hash` no soporta CloneCD
  `.img`/`.ccd`/`.sub` ni `.ecm`, los 25 restantes quedan sin poder
  verificarse con la herramienta actual). De esas 15, buscado un
  contrapartida canónica real en el resto de `psx/` para cada título:
  - **`Digimon Rumble Arena [SLUS-01404].chd`** vs `(USA).chd` — **verificado
    idéntico byte a byte, aplicado** (mismo hash MD5 RA real). 1 archivo
    descartado, verificado en el dispositivo real.
  - **`Driver 2 [Disc2of2] [SLUS-01318].chd`** vs `(USA) (Disc 2) (Rev 1).chd`
    — **MISMATCH real** pese al nombre y tamaño parecidos (342.200.657 vs
    342.287.667 bytes) — contenido genuinamente distinto, **no tocado**.
    Confirma que verificar antes de aplicar sigue mereciendo la pena incluso
    en candidatos que parecen obvios.
  - `Ehrgeiz - God Bless the Ring [SLUS-00809]` y `Crash Team Racing
    [SCUS-94426]`: cada uno tiene **2 copias, ambas con nombre legacy**, sin
    ninguna copia de nombre canónico en la biblioteca contra la que comparar
    — no hay "recomendado" obvio, sin tocar hasta decidir cuál de las dos
    conservar (o verificar si son idénticas entre sí).
  - `Crash Bash [SCUS-94570]` (USA, `.chd` de 4,4 MB sospechosamente pequeño +
    `.bin` de 178 MB) solo tiene una copia canónica de **otra región**
    (Europe, 61 MB) en la biblioteca — no comparable, regiones distintas se
    esperan distintas, sin tocar.
  - `Tekken 3 [SLUS-00402]` (set multi-pista con un `.cue` roto) sin una
    contrapartida canónica de un solo archivo clara — sin tocar.
  - Los 25 archivos `.ccd`/`.img`/`.sub`/`.ecm` restantes (CloneCD y formatos
    comprimidos con corrección de errores eliminada) quedan documentados sin
    verificar — soporte de esos formatos en `compute_psx_ra_hash` fuera de
    alcance de esta sesión.

**Estado al cerrar la sesión (2026-09-30, tarde)**: rescan completo de
`psx/` con `compute_hashes=True` **en curso** (relanzado para restaurar los
hashes borrados por el bug de arriba) — dejarlo terminar solo antes de tocar
nada más en `psx/`; comprobar con `GET /api/job-status` (`scan_running`).
**`Game Gear/` (rehash de los 28 archivos sin sha1) sin empezar** — pendiente
para la próxima sesión, una vez termine el rescan en curso (mismo job
"scan", no se puede lanzar en paralelo). Backups de `library_android.db`
hechos antes de cada tanda de borrado real de hoy, en
`.rommgr/library_android.db.bak-*`.
- **Carpetas Title Case + slug paralelas**: de los "4 pares confirmados" originales,
  hoy solo queda uno sin resolver — **`Game Gear/` (28 archivos) + `gamegear/`
  (736 archivos)**, 0% de solapamiento por SHA1 comprobado porque **las 28 filas
  de `Game Gear/` tienen `sha1=''`** (nunca se hashearon) — invisibles para
  cualquier deduplicación por hash, y sus nombres ya parecen No-Intro
  (`Ax Battler - A Legend of Golden Axe (USA, Europe, Brazil) (En).gg`), no
  claramente legacy — hace falta rehashear antes de decidir si son duplicados
  reales o contenido legítimo sin catalogar. `Atari 2600/`, `Master System/` y
  `Famicom Disk System/` ya no tienen su par Title Case (resuelto de rebote,
  mismo hallazgo que `SD-ORPHAN-FOLDERS-1` documentó para la raíz de la SD).
- **`famicom/` investigado a fondo 2026-09-30 — NO son duplicados triviales,
  sin consolidar a propósito**: 109 archivos, 0,02 GB, en paralelo a `nes/`
  (2972 archivos, 2,34 GB, ambas carpetas con `sha1` real ya calculado, a
  diferencia de `Game Gear/`). **0 coincidencias por SHA1** entre `famicom/` y
  `nes/`; **100/109 comparten nombre de archivo exacto** con algo en `nes/`,
  pero **contenido distinto** — verificado bajando un par real por ADB
  (`Little Nemo - The Dream Master (Europe).nes`, 262.160 bytes en ambas
  carpetas): cabecera iNES idéntica (mismo mapper/PRG/CHR), pero difieren a
  partir del byte 24.000 — no es una cuestión de cabecera, el contenido del
  ROM en sí es distinto pese al nombre y tamaño idénticos (revisión/hack
  distinto bajo el mismo nombre No-Intro, o un dump corrupto en alguna de las
  dos copias, sin determinar cuál). Otro caso (`Kung Fu (Europe).nes`) ni
  siquiera coincide en tamaño (40.976 vs 65.552 bytes) con el mismo nombre.
  **Conclusión: no consolidar `famicom/` en `nes/` sin revisar caso a caso**
  — mismo tipo de aviso que ya dio el hallazgo original de `ANDROID-DUP-3`
  para `fds/` ("no era lo que parecía"), confirmado ahora con datos reales
  para este par también. Los 9 archivos de `famicom/` sin ninguna
  coincidencia de nombre en `nes/` (varios dentro de subcarpetas de colección
  `# DYNAVISION #`/`# PT-BR #`/`top100`) tampoco tocados.
- **`ANDROID-DUP-CROSSFMT-VERIFY-1` repetido con la función ya integrada y
  completado 2026-09-30** (`verify_group_by_disc_hash`, PR #379): 89 grupos
  PSX `crossfmt`-only reales hoy (antes 83, la cola cambia con la biblioteca)
  — **2 verificados como seguros (mismo grupo, `Guilty Gear (Europe)`), 0
  mismatch, 102 rutas no verificables** (mismo patrón que el 2026-09-25: la
  inmensa mayoría de `.cue`/`.img` de esta biblioteca referencian un `.bin`
  que ya no existe tal cual en el dispositivo). Los 2 verificados **aplicados
  con confirmación explícita del usuario**: descartados `psx/Guilty Gear
  (Europe).chd` + `psx/Guilty Gear (Europe).bin` sueltos en la raíz,
  conservado `psx/Guilty Gear (Europe)/Guilty Gear (Europe).chd`, **0,48 GB
  liberados**, verificado en el dispositivo real. Con esto,
  `ANDROID-DUP-CROSSFMT-VERIFY-1` queda completamente cerrado — no queda
  ningún grupo PSX `crossfmt`-only sin comprobación de contenido real.
- **`ANDROID-DUP-1` GBC — aplicado 2026-09-30**: confirmado sin cambios desde
  Día71 (1268 grupos, 1,95 GB, todos `reasons == ["sha1"]` puro), mismo patrón
  ya probado en NES/Game Gear. Backup de `library_android.db` antes de tocar
  nada. **1268/1268 grupos, 1276 archivos descartados, 0 errores, ~1,95 GB
  liberados** — verificado en el dispositivo real (recomendado presente,
  descartes confirmados ausentes por `adb shell test -e`).
- **Resto de plataformas `sha1`-puro nunca aplicadas — aplicadas 2026-09-30**:
  mismo criterio estricto que GBC (solo `reasons == ["sha1"]`, nunca un grupo
  con `crossfmt` mezclado — ese patrón mixto es justo el que causó el problema
  real de `ANDROID-DUP-PSX-1`). Sega Mega Drive (65), SNES (5), Game Boy (25),
  Nintendo 64DD (1) y el único grupo PSX sin `crossfmt` en `reasons` (1) — **96
  grupos, 106 archivos descartados, 2 fallos** (el grupo PSX, bloqueado
  correctamente por el guard `DUP-CROSSFMT-6`: su "recomendado" ya no existe
  en el dispositivo, fila obsoleta, nada descartado), **~0,145 GB liberados**.
  Verificado en el dispositivo real (`adb shell test -e`) sobre una muestra.

---

### ANDROID-DUP-2 — El escaneo ADB nunca calcula SHA1/MD5: matcher nunca corre sobre `library_android.db`, duplicados legacy same-extension invisibles (hallazgo 2026-09-19, RG556, continuación de `ANDROID-DUP-1`)

Origen: comprobando por qué GBA solo tenía 1 grupo `crossfmt` detectado (91
volcados legacy `[E]`/`[U]` encontrados por ADB) pese al ejemplo del usuario
(`Final Fantasy Tactics [E].gba`, `Pokemon Pinball RZ [E].gba`, ambos con el
mismo `size_bytes` que su contraparte canónica No-Intro ya presente —
`Final Fantasy Tactics Advance (Europe)...gba` y
`Pokemon Pinball - Ruby & Sapphire (Europe)...gba`, 16.777.216 bytes cada
par — casi con toda seguridad el mismo dump, distinto nombre).

Causa raíz: `_do_adb_scan()` (`web/handlers/scan.py:494-495`) escribe
**`sha1=""` y `md5=""` incondicionalmente** para cada fila — el escaneo ADB
solo lee metadata (`ls_recursive`: nombre/tamaño/mtime), nunca contenido.
Confirmado contra `library_android.db` real: las 12 filas de GBA
consultadas (Pokemon/Final Fantasy Tactics) tienen `sha1`/`md5` vacíos **y**
`canonical_title = NULL` en el 100% de los casos — el matcher de catálogo
nunca se ha ejecutado contra este repo en ninguna sesión.

Efecto en cascada, tres roturas distintas del mismo origen:
1. **Unión por SHA1** (`_review_groups_for_repo`) nunca enlaza nada en
   Android — cadena vacía siempre.
2. **Unión por `canonical_title` exacto** tampoco — nunca hay título que
   comparar.
3. **`crossfmt`** (la única vía que sí detecta algo hoy) exige **dos
   extensiones distintas** compartiendo el título normalizado — un volcado
   legacy `[E].gba` duplicando un `.gba` canónico comparte la *misma*
   extensión, así que ni siquiera esa vía lo alcanza. Resultado: un volcado
   legacy same-extension es invisible a los tres mecanismos de detección a
   la vez, pese a ser, en apariencia (mismo tamaño exacto), el caso más
   fácil de detectar de todos.

Efecto colateral, no confundir con el "iSuu dice que no hay logros pero el
emulador sí los da" que reportó el usuario (ese es el propio hash-check de
iSuu, una app de terceros en el dispositivo, fuera del alcance de este
repo) — pero **nuestra propia** lógica de "qué copia tiene soporte RA"
(`ra_supported`, vía `_load_ra_hash_map(...).get(md5_lower, ...)` en
`web/builders/duplicates.py`) también queda permanentemente `False` para
cualquier fila Android, porque el `md5` del que depende nunca se calcula —
el desempate por RA en el ranking de duplicados (`_review_entry_sort_key`)
es un no-op silencioso ahí mismo.

**Por qué no es trivial arreglarlo sin criterio**: calcular SHA1/MD5 real
requiere leer el contenido — para un `.gba`/`.nes`/`.snes` (unos pocos MB)
es barato; para un `.iso`/`.chd` de PS2/PSX (GBs) traerlo por ADB solo para
hashear sería lentísimo (ya documentado en `DUP-DISC-RA-2`: un solo disco
de PSX tarda minutos solo para `chdman`, sin contar la transferencia ADB
completa). Alternativa más barata: la mayoría de builds de Android traen
`sha1sum`/`md5sum` en el propio dispositivo (`adb shell sha1sum <ruta>`,
hash calculado en el propio teléfono, sin transferir el archivo) — viable
para el `AdbTransport` existente, pero sigue sin ser gratis a escala
(13.554 ROMs detectados en el último scan) y no se ha medido el coste real
en esta sesión.

**Recomendación (sin implementar, a decidir con el usuario)**:
1. Medir coste real de `adb shell sha1sum` sobre una muestra de plataformas
   cart-based (GBA/NES/SNES/GBC — archivos pequeños) antes de decidir si
   hashear todo o solo por debajo de un umbral de tamaño.
2. Si se activa el hash on-device, correr el matcher de catálogo contra
   `library_android.db` al menos una vez para poblar `canonical_title` —
   hoy nunca se ha ejecutado.
3. Alternativa más barata a corto plazo, sin tocar el transporte ADB:
   extender la unión `crossfmt` (`_review_groups_for_repo`,
   `web/builders/duplicates.py`) para que el título normalizado también
   enlace **misma extensión** cuando ambos lados carecen de SHA1 — con más
   riesgo de falso positivo que la vía actual (exige distinta extensión
   precisamente para evitar eso), necesitaría su propio guard cuidadoso
   antes de recomendar borrado automático.

No implementado en esta sesión | `web/handlers/scan.py:494-495`
(`_do_adb_scan`, hardcodea sha1/md5 vacíos), `web/builders/duplicates.py`
(`_review_groups_for_repo` — unión por sha1/título/crossfmt, `_load_ra_hash_map`
+ `_review_entry_sort_key` — desempate RA silenciosamente inactivo en
Android) | ✅ **implementado 2026-09-19** (PR #330, `AdbTransport.sha1_recursive`/`md5_recursive`,
hash calculado en el propio dispositivo — ver commit `7be90a7`). ✅ **Fase 1 del
roadmap 23 ejecutada 2026-09-20** (rescan con hash real, 9 plataformas
cartucho — `gba`/`megadrive`/`gb`/`nes`/`famicom`/`gbc`/`gamegear`/`snes`/`n64`,
29.657 archivos, 0 errores; troceado por plataforma tras un primer intento
fallido de escanear todo `/storage/521D-04EA/ROMs` de una vez que murió a los
3600s exactos por timeout, sin dejar nada aprovechable — ver
`.claude/roadmaps/23-android-hash-rescan-dedup.md`). `_build_review_queue`
contra `library_android.db` real: **3.270 grupos `sha1` reales en esas 9
plataformas** (antes 0, ningún matcher corría con hash vacío), **4,23 GB
desperdiciados**. Confirmados agrupados los 2 casos que motivaron el
hallazgo (`Final Fantasy Tactics [E].gba`/`Final Fantasy Tactics Advance
(Europe)...gba`, `Pokemon Pinball RZ [E].gba`/`Pokemon Pinball - Ruby &
Sapphire (Europe)...gba`, ambos razón `sha1`). De los 3.270: **1.279 son la
misma causa ya conocida** (`gb\GB official game ROM complete works\` —
subcarpeta que duplica el contenido de `gb\`/`gbc\` un nivel más adentro,
mismo patrón que `DUP-CROSSFMT-1` en PC, aquí también presente en la
Anbernic); **1.991 son duplicados genuinos distintos** (mismo contenido,
convención de nombre distinta — volcado legacy `[E]`/`(U)` vs No-Intro
completo, o variante región `(USA)`/`(USA, Australia)`). **No se ha
aplicado nada** (`resolve-duplicates --apply`) — pendiente de decisión
explícita del usuario, mismo criterio de todo el backlog. NES (1.581) y
Game Boy Color (1.268) concentran la inmensa mayoría, casi toda explicada
por la carpeta anidada | ✅ **Fase 2 completada 2026-09-20**: escaneo ADB con hash real sobre
`/storage/521D-04EA/ROMs/arcade` — 10.616 archivos vistos (la mayoría chips
sueltos de sets MAME sin comprimir, no ROMs independientes), **388 ROMs
reconocidas**, hash SHA1/MD5 calculado en las 388, 0 errores.
`_build_review_queue`-equivalente (unión por SHA1 exacto) contra
`library_android.db`: **0 grupos duplicados** — resultado limpio, coincide
con que el catálogo FBNeo se arregló y 67 sets se renombraron en este mismo
dispositivo el mismo día (`MATCH-ARCADE-DAT-2`/`ARCADE-RENAME-BUG-1f`).
Fase 3 (discos, 382 GB, 3+ horas) sigue pendiente de decisión explícita del
usuario — no lanzada | ✅ **Fase 3 parcial completada 2026-09-21**: las 5
plataformas de disco medianas (`nds` 480 archivos/385 ROMs, `gamecube` 19,
`dreamcast` 61, `3ds` 37, `psp` 7 — 971 archivos, 0 errores, hash real
calculado vía `POST /api/adb-scan` una llamada por plataforma) escaneadas
contra la RG556 real. `_build_review_queue` contra `library_android.db`:
**7 grupos duplicados reales, todos en Dreamcast, 4,79 GB desperdiciados**
(nds/gamecube/3ds/psp salieron limpios) — coincide con los 5 juegos
Dreamcast ya confirmados en `.cdi` por `DUP-DISC-RA-1e`. Ejemplos: `Dead or
Alive 2 (Europe).cdi` duplicado literal (mismo nombre, 2 copias, +1 variante
Beta); `Legacy of Kain - Soul Reaver` con la copia `(USA).cdi` byte-idéntica
a `(Europe).cdi` (mismo SHA1 — probable mal etiquetado de región, no una
versión distinta real); `Crazy Taxi 2`/`Sonic Adventure (XBLA)`/`D2 (USA)`
duplicados literales por nombre. **Hallazgo colateral — implementado 2026-09-21**:
`vmu_save_A1.bin`/`vmu_save_A2.bin` (saves de memory card Dreamcast) se
clasificaban como ROM, no como save — `.bin` no está en `save_extensions`
(`config.py:606-629`, correcto para no romper discos reales `.bin`), así
que `_do_adb_scan` (`web/handlers/scan.py`, rama `else`) los trataba como
ROM por descarte. Arreglado con una rama nueva por nombre (`suffix ==
".bin" and name.lower().startswith("vmu_save_")` → `upsert_save`, antes de
la rama de asset/ROM), caso estrecho a propósito (solo Dreamcast usa esta
convención) sin tocar `save_extensions` global. Test nuevo
`test_adb_scan_classifies_vmu_save_bin_as_save_not_rom` en
`tests/web/test_adb_scan_hashing.py`.

**Fase 3 completada al 100% (7/7 plataformas) 2026-09-21**: `psx` (215G) —
1746 archivos, 1685 ROMs, 0 errores. `ps2` (89,5G) — 27 archivos, 26 ROMs,
0 errores. `_build_review_queue` contra `library_android.db` completo:
**149 grupos duplicados en psx/ps2, 19,6 GB desperdiciados** (motivos: 94
`crossfmt`, 67 `sha1`, solapados). Casos reales: `Xenogears`,
`Metal Gear Solid`, `Final Fantasy VIII`, `Suikoden II`, `Parasite Eve`,
`Final Fantasy Tactics` (mismo disco en `.chd`+`.cue`+`.bin`+`.pbp`, o
regiones distintas mezcladas con crossfmt). **`disc_hash` no aportó nada
aquí** — a diferencia de la validación contra `library_pc.db` (rutas
Windows reales de la SD montada por lector de tarjetas), las filas de
`library_android.db` tienen rutas Android (`/storage/521D-04EA/...`) que
`get_psx_disc_hash` no puede leer desde esta máquina Windows
(`Path(source_path).stat()` falla en silencio, `None` para cada fila) —
esperado, no un bug; el caso `ANDROID-DUP-1` (CloneCD legacy) seguiría sin
validarse sin copiar esos archivos localmente primero.

**Hallazgo nuevo, real y sin implementar (riesgo real al aplicar la cola de
duplicados en PSX)**: en el grupo `Xenogears`, `_is_disc_set()`
(`web/builders/duplicates.py:56-80`) no protegió un set multi-disco real —
`Xenogears (Japan).chd` (edición japonesa, un solo disco, **sin** tag
`(Disc N)` en el nombre) quedó unido en el mismo clúster que
`Xenogears (USA) (Disc 1).chd`/`(Disc 2).chd`. Causa raíz: `_is_disc_set`
devuelve `False` (guard desactivado, se trata como duplicado normal) en
cuanto **un solo miembro** no tiene número de disco parseable
(`find_disc_number` → `None`, línea 77-78) — protege sets donde todos los
miembros llevan tag de disco, pero no cuando una edición regional
single-disc (sin tag) se mezcla con los discos individuales de una edición
multi-disco. Con datos reales de PSX vía ADB por primera vez este patrón
aparece en varios juegos reales de la biblioteca — **no aplicar
`resolve-duplicates --apply` sobre los grupos PSX/PS2 sin revisión manual**
hasta que esto se arregle, riesgo real de descartar un disco necesario de
un set multi-disco | ✅ Fases 1-2 completas; Fase 3 100% (7/7 plataformas,
149 grupos psx/ps2, 19,6 GB); hallazgo colateral `vmu_save` arreglado y
testeado; hallazgo nuevo `_is_disc_set` documentado sin implementar,
bloquea aplicar duplicados en PSX/PS2 sin revisión manual |

**Re-verificado 2026-09-21 (Día68), tras `DUP-DISC-SET-1` y el primer lote
aplicado (ver `ANDROID-DUP-2 Fase 3 — aplicado...` más abajo)**: consulta
directa de `_build_review_queue` contra `library_android.db` en solitario
(no vía CLI/servidor) confirma de nuevo `disc_hash: 0` para PSX/PS2
puramente Android — mismo motivo ya documentado arriba (rutas
`/storage/...` no legibles desde Windows). Estado tras el apply de hoy:
**99 grupos, 36,36 GB "desperdiciados"** (54 `sha1` + 59 `crossfmt`) — cifra
más alta que la original (19,6 GB) porque incluye deliberadamente sin
aplicar los 6 grupos de alto riesgo de `DUP-DISC-SET-2` (varios GB cada
uno, ej. `Final Fantasy VIII` con 4 discos) y ~46 sospechosos de
`DUP-DISC-TRACK-1`, no porque haya crecido el problema real.

**Medición real del punto 1 (2026-09-19, sesión siguiente, tras mergear
`ANDROID-DUP-2`/PR #330)**: se lanzó el rescan ADB completo con hash real
(`scan_run_id=6`, 21.608 archivos, mismo comando que ejecuta
`sha1_recursive`: `adb shell find /storage/521D-04EA/ROMs -type f -exec
sha1sum {} +`) en background. **Falló por timeout tras exactamente 3600s**
(el propio límite que `_do_adb_scan` le pasa —
`web/handlers/scan.py:453`, `transport.sha1_recursive(android_path,
timeout=3600)` — coincide con el timeout por defecto documentado en el
docstring de `sha1_recursive`, `sync/adb_transport.py`, que estimaba
"~100ms/archivo... una biblioteca de 20k archivos queda holgada" — la
estimación era optimista, el comando real no había terminado a los 3600s
exactos para 21.608 archivos). **Sin escritura parcial**: `_do_adb_scan`
solo escribe en `library_android.db` al final, tras completar tanto
`sha1_recursive` como `md5_recursive` (`web/handlers/scan.py:450-457`) — un
timeout a mitad de la primera pasada no deja ningún dato aprovechable,
`scan_run_id=6` se queda con `finished_at=NULL` para siempre. Confirma
`crc32sum`/reconsiderar el enfoque de `_hash_recursive` antes de relanzar
sin más: o (a) subir el timeout (con qué margen, sin dato de cuánto faltaba
para terminar), o (b) trocear el escaneo por subcarpeta de plataforma en
vez de un único `find` sobre toda la raíz (permite además guardar progreso
incremental en vez de todo-o-nada), o (c) medir con un subconjunto pequeño
primero (la recomendación #1 original de esta misma tarea, nunca hecha
antes de lanzar el escaneo completo — la sesión se saltó ese paso e
intentó ir directa a la escala completa). **`ANDROID-DUP-3` (famicom/ vs
nes/, 1.313 candidatos) sigue sin confirmación por SHA1 real** — toda su
evidencia sigue siendo solo nombre+tamaño, sin cambios | `web/handlers/scan.py:453`,
`sync/adb_transport.py` (`sha1_recursive`, timeout por defecto optimista) |
✅ **decisión tomada y ejecutada 2026-09-20** — opción (b) de las tres
listadas arriba: trocear el escaneo por plataforma. Ver roadmap
`.claude/roadmaps/23-android-hash-rescan-dedup.md` y el resultado real
(Fases 1-2 completadas) en el párrafo `✅ Fase 2 completada 2026-09-20` más
arriba en esta misma tarea |

---

### DUP-DISC-SET-1 — `_is_disc_set()` no protege un set multi-disco cuando una edición regional sin tag `(Disc N)` se mezcla con los discos sueltos de otra edición (hallazgo 2026-09-21, datos PSX reales vía ADB, Fase 3 de `ANDROID-DUP-2`)

Origen: al correr `_build_review_queue` contra `library_android.db` con
hash real de PSX/PS2 por primera vez, el grupo `Xenogears` unió
`Xenogears (Japan).chd` (edición japonesa, un solo disco, sin tag `(Disc
N)` en el nombre) con `Xenogears (USA) (Disc 1).chd` y `(Disc 2).chd` —
tres discos con contenido distinto tratados como "duplicados", con riesgo
real de que "Aplicar recomendación" descarte un disco necesario del set
USA. Mismo patrón visto en `Metal Gear Solid`/`Final Fantasy VIII`/
`Parasite Eve` (149 grupos psx/ps2 en total, 94 `crossfmt` + 67 `sha1`).

Causa raíz confirmada: `_is_disc_set()` (`web/builders/duplicates.py:56-80`)
devuelve `False` (guard desactivado, el clúster se trata como duplicado
normal) en cuanto **un solo miembro** del clúster no tiene número de disco
parseable (`find_disc_number()` → `None`, línea 77-78). Protege bien un
set donde *todos* los miembros llevan tag de disco (`(Disc 1)`/`(Disc 2)`),
pero no cuando una edición regional single-disc (sin tag, p. ej. la
japonesa) queda unida al mismo clúster que los discos individuales de una
edición multi-disco vía `crossfmt`/`sha1` — el guard nunca llega a
evaluarse como "sí es un set multi-disco" porque el miembro sin tag rompe
la condición `for r in members: if num is None: return False`.

**Implementado (2026-09-21, Día68)**: `_is_disc_set()` ya no descarta el
guard de golpe ante un miembro sin número de disco parseable — ahora
excluye ese miembro del cómputo y sigue exigiendo ≥2 números distintos
*entre los miembros que sí llevan tag*. Test de regresión con el caso real
exacto (`Xenogears (Japan).chd` + `(USA) (Disc 1/2).chd`, mismo
`canonical_title`) confirmado en rojo contra el código anterior y en verde
tras el fix. Suite completa (1423 tests) sin regresiones nuevas (3 fallos
ambientales preexistentes, dispositivo ADB conectado).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-DISC-SET-1 | Arreglar `_is_disc_set()` para no perder la protección de set multi-disco cuando un miembro del clúster no lleva tag de disco (edición regional single-disc mezclada con discos sueltos de otra edición) | `web/builders/duplicates.py:56-84` (`_is_disc_set`), `tests/test_builders_duplicates.py` | ✅ hecho 2026-09-21 — desbloquea aplicar `resolve-duplicates --apply` sobre los 149 grupos psx/ps2 de `ANDROID-DUP-2` Fase 3 (revisión manual sigue recomendada antes de aplicar, no es automático) |

---

### DUP-DISC-SET-2 — `has_sha1_dup` no está protegido por `_is_disc_set()`: un duplicado real dentro de un clúster arrastra discos legítimos de un set multi-disco al mismo grupo "descartar" (hallazgo 2026-09-21, Día68, al aplicar `resolve-duplicates` real sobre los 149 grupos psx/ps2 recién desbloqueados)

Origen: tras `DUP-DISC-SET-1`, al inspeccionar el grupo real `Xenogears`
contra `library_android.db` (`_build_review_queue`), seguía recomendando
descartar `Xenogears (USA) (Disc 2).chd` — un disco real, no un duplicado.
Causa: `Xenogears (Japan).chd` y `Xenogears (USA) (Disc 1).chd` son
literalmente byte-idénticos (mismo SHA1, probable mal etiquetado regional)
— duplicado real y correcto de detectar. Pero `has_sha1_dup`
(`web/builders/duplicates.py:1151`) no está gateado por `_is_disc_set()`
como sí lo están `has_title_dup`/`has_crossfmt_dup`/`has_region_dup`/
`has_disc_hash_dup` — así que el union-find ya mezcló Disc 1 y Disc 2 en el
mismo componente (vía `crossfmt`, correctamente ignorado como *razón* por
el guard, pero el `union()` en sí ya ocurrió antes de que se evalúe
`_is_disc_set`), y el motor de recomendación elige UN solo "conservar"
para todo el componente, marcando Disc 2 como "descartar" pese a no ser
duplicado de nada.

**Medido en real (Día68)**: 6 de 156 grupos psx/ps2 tienen este patrón
compuesto (`Xenogears`, `Final Fantasy VIII`, `Parasite Eve` — perderían
Disc 2/3/4 reales — más 3 clústeres de pistas `.bin` sueltas sin tag de
disco, ver `DUP-DISC-TRACK-1`). **Excluidos manualmente del apply de hoy**
(`repository.exclude_duplicate_group` no usado — se filtraron fuera de la
`queue` pasada a `apply_all_review_recommendations`, ver
`DUP-DISC-SET-1`/Día68 para el detalle). Sin arreglar en el motor — la
detección de `_is_disc_set` necesita aplicarse también a la selección de
qué entradas puede marcar "descartar" dentro de un componente, no solo a
qué *razón* se etiqueta.

**Implementado (2026-09-22, Día69)**: cuando un clúster es un set multi-disco
real (`_is_disc_set()` True) Y además tiene un `has_sha1_dup` real, ya no se
trata el clúster entero como un único grupo de revisión. En su lugar se
agrupan los miembros por SHA1 dentro del propio clúster — solo los
subconjuntos con SHA1 realmente compartido (≥2 archivos) se emiten como su
propio grupo de duplicado (razón `sha1`, `group_key` con sufijo por SHA1 para
no colisionar); un miembro con SHA1 único dentro del set (un disco legítimo
sin duplicado) no entra en ningún grupo — nunca puede ser "recomendado
descartar". Refactor: la construcción de `entries`/`recommended`/`wasted`
(antes ~55 líneas inline por clúster) se extrajo a una función anidada
`emit_group()`, reutilizada tanto por el camino normal como por cada
sub-grupo SHA1 de un set multi-disco — evita duplicar esa lógica ya probada.
Test de regresión con el caso real exacto (Xenogears Japan+Disc1 mismo SHA1,
Disc2 SHA1 propio): confirmado en rojo contra el código anterior (`git
stash`) y en verde tras el fix — el grupo resultante contiene solo
Japan+Disc1, Disc2 no aparece en ningún grupo. Suite completa (1427 tests):
0 regresiones. `Final Fantasy VIII`/`Parasite Eve` (mismo patrón, sin caso de
test dedicado) quedan cubiertos por la misma lógica genérica, no por un fix
específico de Xenogears.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-DISC-SET-2 | Arreglar el motor de recomendación para que un componente que mezcla un duplicado SHA1 real con discos legítimos de un set multi-disco no marque esos discos como "descartar" — probablemente separar sub-clústeres por número de disco antes de elegir "recomendado" | `web/builders/duplicates.py` (`_review_groups_for_repo`, `emit_group` nuevo, rama `is_disc_set and has_sha1_dup`), `tests/test_builders_duplicates.py` | ✅ hecho 2026-09-22 — desbloquea revisar/aplicar `Xenogears`/`Final Fantasy VIII`/`Parasite Eve` sin riesgo de perder un disco real (revisión manual sigue recomendada antes de aplicar) |

---

### DUP-DISC-TRACK-1 — Pistas de audio CD silenciosas/genéricas en `.bin` sueltos (sin `.cue`/contexto de set) producen SHA1 idéntico entre juegos completamente distintos, falso positivo de duplicado (hallazgo 2026-09-21, Día68, mismo repaso que `DUP-DISC-SET-2`)

Origen: al revisar (muestreo manual, 35 de 146 grupos) los candidatos a
`resolve-duplicates --apply` antes de ejecutarlo, aparecieron varios
grupos donde dos **juegos sin relación** comparten SHA1 en un único
archivo `.bin` con sufijo `(Track N)` — ej. `Ninja - Shadow of Darkness
(Europe) (Track 44).bin` == `Ultraman Zearth (Japan).bin`; `Guilty Gear
(Europe) (Track 2).bin` == `Guilty Gear (USA) (Rev 1).bin` (aquí sí
mismo juego pero probablemente solo la pista coincide, no el disco
completo); `Magical World of Disney...(Track 3).bin` ==
`Nestle Disney Demo (Europe).bin`. Estos son volcados PSX multi-pista
donde cada pista de audio se trackeó como archivo independiente (sin
`.cue` que las agrupe) — una pista de audio silenciosa o genérica
(intro/logo) puede ser byte-idéntica entre discos de juegos distintos sin
que el contenido real (los datos del juego) tenga nada que ver.

**Medido en real (Día68)**: 46 de 146 grupos candidatos (~31%) tenían al
menos un miembro `.bin`; de esos, 39 llevaban sufijo `(Track N)` (patrón de
pista suelta, alto riesgo) y 7 eran `.bin` de archivo completo sin sufijo
de pista (mismo título que su `.chd`/`.cue` — esos sí se verificaron uno a
uno y se aplicaron). **Ninguno de los 46 se aplicó hoy** — se excluyeron
todos por precaución hasta diseñar una regla fiable.

**Implementado (2026-09-22, Día69)**: se eligió el segundo enfoque propuesto
(excluir pistas de audio del union-find por completo) por ser el más simple
y seguro — reordenar para exigir un link `crossfmt`/`canonical_title` previo
habría requerido mover el union por SHA1 después de esas pasadas, más riesgo
para el mismo resultado. Cualquier fichero cuyo nombre lleve un tag
`(Track N)` (`_is_loose_track_file()`, regex `\(track\s*\d+\)`) nunca entra
en el union por SHA1 (`web/builders/duplicates.py`, pase inicial de
`first_by_sha1`) — ni como primer miembro ni como candidato a unirse a otro.
No distingue Track 1 (dato) de Track N>1 (audio) porque el N por sí solo no
es fiable como señal (ver ejemplos reales arriba, algunos con Track bajo);
la protección se aplica a cualquier `(Track N)`. Test de regresión con el
caso real exacto (`Ninja - Shadow of Darkness (Track 44).bin` ==
`Ultraman Zearth (Japan).bin`, mismo SHA1): confirmado en rojo contra el
código anterior (`git stash`) y en verde tras el fix. Suite completa (1428
tests): 0 regresiones.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-DISC-TRACK-1 | Evitar que un SHA1 compartido entre pistas de audio CD sueltas (`.bin` con `(Track N)`, sin `.cue` de contexto) una en el mismo clúster de duplicados a juegos sin relación | `web/builders/duplicates.py` (`_is_loose_track_file`, union por sha1), `tests/test_builders_duplicates.py` | ✅ hecho 2026-09-22 — desbloquea revisar los 46 grupos excluidos en Día68 sin riesgo de falso positivo entre juegos sin relación (revisión manual sigue recomendada antes de aplicar) |

---

### ANDROID-DUP-2 Fase 3 — aplicado el primer lote seguro de duplicados psx/ps2/Dreamcast contra la Anbernic real (Día68, 2026-09-21)

Tras `DUP-DISC-SET-1`, revisión manual completa de los 149 grupos psx/ps2 +
7 Dreamcast desbloqueados: excluidos los 6 de `DUP-DISC-SET-2`, el grupo
`disc_hash` de Resident Evil 3 (pendiente decisión del usuario, Día67 punto
9), los 2 `vmu_save_*.bin` (necesitan rescan tras el fix de clasificación
de hoy), `Dead or Alive 2`/`Legacy of Kain` (nombres de región ambiguos,
mismo contenido pero el "recomendado" automático no siempre elige el
nombre correcto) y los 46 de `DUP-DISC-TRACK-1`. De los 108 grupos
restantes (105 PlayStation + 3 Dreamcast, todo `.chd`/`.cue`/`.ccd`
completos o duplicados literales byte-idénticos, verificados con 2
muestreos aleatorios de 15+20 grupos), se aplicó vía `apply_all_review_
recommendations` con `AdbTransport` real (cola filtrada a mano, sin pasar
por el endpoint web/CLI genérico para no tocar los ~1850 grupos restantes
de la biblioteca PC, fuera de alcance de hoy) — backup previo de
`library_pc.db`/`library_android.db`.

**Resultado**: 132 archivos borrados en la Anbernic, 13,02 GB liberados, 0
errores. Verificado por dos vías independientes (resultado de la función +
diff directo de `library_android.db` antes/después): ambas coinciden
exactamente en 132 archivos / 13,02 GB. Los 6 grupos de `DUP-DISC-SET-2`
confirmados intactos tras la operación (7/9 entradas cada uno, sin tocar).

**Pendiente**: quedan ~40 pares adicionales mismo-título `.chd`+`.bin`
(ej. `Vagrant Story`, `Crash Bandicoot`, `Tony Hawk's Pro Skater 2/4`) sin
aplicar — excluidos por el filtro conservador de hoy (cualquier grupo con
un miembro `.bin` quedó fuera salvo los 7 revisados a mano), candidatos
para una revisión uno-a-uno en otra sesión.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ANDROID-DUP-2-APPLY-1 | Revisar uno a uno y aplicar (si procede) los ~40 pares restantes mismo-título `.chd`+`.bin` no incluidos en el lote seguro de hoy | — (revisión manual + `apply_all_review_recommendations` con cola filtrada) | ✅ **hecho 2026-09-25** — 68 grupos aplicados en total (22 sha1 puro + 46 `.chd`+`.bin` verificados por hash RA real), 25,08 GB liberados, 0 errores. 5 MISMATCH reales y 2 no-hasheables sin tocar, ver `ANDROID-DUP-CROSSFMT-VERIFY-1` |

**Sesión 2026-09-25**: recalculada la cola (`/api/review-queue`, `library_android.db`
real con la Anbernic conectada) — **83 grupos solo-dispositivo, 35,88 GB**
(antes 96 el Día68; la bajada de 13 grupos es exactamente `DUP-CROSSFMT-10`
+ `DUP-SHA1-JUNK-1` ya resueltos, confirma que esos fixes surtieron efecto
sin regresión). De los 83: **22 tienen `reasons == ["sha1"]` puro** (par de
2 entradas, hash SHA1 verificado byte-idéntico entre `keep` y `discard`) —
aplicados con `POST /api/resolve-duplicate-ra` uno a uno (cola filtrada a
mano, backup previo de `library_android.db`): **22/22 borrados, 0 errores,
2,30 GB liberados**, verificado por fila de BD (0/22 filas descartadas
siguen en la BD) y por archivo real en el dispositivo (`adb shell test -e`
sobre 2 casos). Incluye los `Xenogears`/`Final Fantasy VIII`/`Parasite Eve`
que `DUP-DISC-SET-2` desbloqueó. **Hallazgo colateral, no bloqueante**: 3
de los 22 "keep" recomendados son el nombre correcto del juego pero viven
anidados dentro de la carpeta de OTRO juego (`Twisted Metal (Europe)/
AirAssault - The Red Mercury Missions (Japan).bin`, mismo patrón con
`Jet Moto '98`/`Interactive CD Sampler...`) — contenido verificado idéntico
así que no hay pérdida de datos, pero la ubicación final queda rara
(posible resto del mismo volcado sin explicar de `UNKNOWN-BULK-GROWTH-1`,
sin investigar más por ahora).

### ANDROID-DUP-CROSSFMT-VERIFY-1 — los 61 grupos `crossfmt` restantes (53 pares `.chd`+`.bin` + 8 más, ~26,5 GB) no tienen ninguna verificación de contenido, solo coincidencia de nombre (hallazgo 2026-09-25)

`reasons == ["crossfmt"]` en `_review_groups_for_repo` (`web/builders/
duplicates.py:992-1017`) agrupa por título normalizado (`normalize_title_
cross_format` sobre el stem) **sin comparar ningún hash** — a diferencia
de la unión por `sha1`. Mismo patrón de riesgo ya conocido en
`CHD-DELETE-NO-VERIFY-1` (lado PC), nunca corregido para esta cola.
Comprobación (solo lectura): para los 53 pares `.chd`+`.bin` mismo-título,
la ratio de tamaño `chd_bytes/bin_bytes` debería rondar 0,4–0,7× (compresión
CHD normal de un disco PSX) — en la práctica iba de **0,025× a 5,1×**, con
7 casos donde el `.chd` pesaba más que el `.bin` — geométricamente imposible
si fueran el mismo disco comprimido, indicio de que `crossfmt` empareja
contenido distinto bajo un título compartido | `web/builders/duplicates.py:
992-1017` (`crossfmt_groups` union, sin verificación de hash) | 🟡 **código
sin arreglar** (el bug de fondo sigue ahí para el resto de la biblioteca),
pero **los 53 pares ya verificados y resueltos con datos reales** — ver
abajo |

**Verificación real ejecutada 2026-09-25**: descargados los 53 pares completos
vía ADB (42 GB, ~17 min a 42 MB/s) y calculado el hash RA real
(`compute_psx_ra_hash`, el mismo que usa `PSX-CHD-REDUNDANT-1`/
`CHD-DELETE-NO-VERIFY-1` en PC) de cada `.chd` y cada `.bin` por separado,
comparados byte a byte (no solo tamaño):

- **46 coinciden de verdad** (hash RA idéntico) — aplicados con
  `resolve-duplicate-ra` (confirmación explícita del usuario antes de
  ejecutar, bloqueo del clasificador de modo automático por ser borrado
  irreversible en lote): **46/46 borrados, 0 errores, 22,78 GB liberados**,
  verificado por fila de BD (0/46 filas descartadas siguen en `library_
  android.db`). Sumado a los 22 del lote sha1 puro de hoy: **68 grupos
  aplicados, 25,08 GB liberados en total en la sesión de hoy.**
- **5 MISMATCH real** (hash RA distinto, contenido genuinamente distinto
  pese al nombre compartido) — **no tocados**: `Tenchu 2 - Birth of the
  Stealth Assassins (USA)`, `Spider-Man (USA)`, `Tony Hawk's Pro Skater 3
  (USA)`, `Legacy of Kain - Soul Reaver (USA)`, `Resident Evil (USA)`.
  Confirma que el riesgo era real, no teórico — un `apply-all` genérico sin
  esta verificación habría borrado contenido único en estos 5 casos.
- **2 no hasheables** (`compute_psx_ra_hash` devolvió `None`) —
  `Crash Bash (USA).chd` (el `.chd` no se pudo hashear; su `.bin` sí) y
  `Twisted Metal (Japan).bin` (el `.bin` no se pudo hashear; su `.chd` sí).
  **Hallazgo colateral en este segundo caso**: el hash del `.chd` de
  "Japan" (`31a6328a...`) es **idéntico** al de `Twisted Metal (Europe).chd`
  (par #48, ya confirmado `match` en el lote de arriba) — el archivo
  etiquetado "Japan" es casi con toda seguridad una copia mal nombrada del
  disco Europe, no una región real. Ninguno de los 2 se ha tocado.

**2026-09-29 — verificación convertida en función de backend real + botón en el frontend**
(petición explícita del usuario: "me gustaría que el backend lo hiciera" + "poder pedirlo
desde el frontend"): `services/ra_duplicates_service.py::verify_group_by_disc_hash()` —
descarga (ADB si es de consola, copia directa si es PC) el recomendado y cada candidato a
un directorio temporal, calcula `compute_psx_ra_hash` de cada uno y solo devuelve como
`safe_discard_paths` los que coinciden exactamente; nunca borra nada por sí misma. Nuevo
endpoint `POST /api/verify-duplicate-hash` (`web/handlers/duplicates.py`). En el frontend
(`review_copies.js`), el botón "Aplicar recomendación"/"Elegir esta" de cualquier grupo
`platform === 'PlayStation'` pasa primero por este endpoint (`_verifyThenResolve`) — solo
llama a `/api/resolve-duplicate-ra` con los paths ya verificados; el resto de plataformas
mantiene el flujo directo (sin el mismo riesgo confirmado). 4 tests nuevos (2 con `chdman.exe`
real + fixture PSX sintético de `test_ra_hash_psx.py`, incluido uno que reproduce el caso
exacto de 3 discos distintos con el mismo nombre mal resuelto) — suite completa 1496/1496.

Primera ejecución real (script de sesión, previa a esta implementación) contra los 89
grupos `crossfmt`-only restantes en la Anbernic: solo **1 verificado** (`Guilty Gear
(Europe)`, 0,48 GB), **0 mismatch**, **98 no verificables** — la inmensa mayoría de los
`.cue` de esta biblioteca referencian un `.bin` que ya no existe tal cual en el
dispositivo (mismo patrón de sheets rotas/legacy ya visto todo el día con FFVII/Lunar),
así que la función hace exactamente lo que debe: no tocar nada que no pueda confirmar de
verdad. Pendiente repetir con la función ya integrada (mismo resultado esperado, sin
cambios de lógica) y decidir manualmente los `.img`/`.mdf` sin soporte (`compute_psx_ra_hash`
no los reconoce, quedan siempre en `unverifiable_paths`).

**Alcance no cerrado**: el bug de fondo (`crossfmt` sin verificación de
hash) sigue sin arreglarse en `web/builders/duplicates.py` — los 8 grupos
`crossfmt`-only restantes (no `.chd`+`.bin`: `Guilty Gear (Europe).chd`,
`Driver (Europe).img`, `New (Slovakia) (Art Assets).img`, `Mortal Kombat 3
(Europe).bin` + otros del lado PC, ~1.828 grupos solo-PC nunca auditados
con este método) quedan pendientes de la misma verificación real antes de
cualquier apply.

---

### ANDROID-STVERSIONS-1 — `saves/.stversions/<core>/` (carpeta de versionado de Syncthing) se trata como save real, contamina la detección de duplicados legado (hallazgo 2026-09-21, `CABLE-SYNC-LEGACY-DUPS-1`)

Origen: al resolver por contenido (SHA1) los 130 grupos restantes de
`CABLE-SYNC-LEGACY-DUPS-1`, 2 grupos (`Metroid - Zero Mission [E].srm`,
`Sonic Advance 2 [E].srm`) tenían una copia bajo
`saves/.stversions/<core>/` — la carpeta de versionado automático de
Syncthing (herramienta de terceros instalada en el dispositivo, no creada
por este proyecto). No es un save real que el usuario gestione, es un
artefacto de sincronización ajeno a `rom_manager` — mismo tipo de ruido que
ya se excluyó para `_descartados/` (`TRASH_DIR_NAME`) y `emulator_saves/`
(`EMULATOR_SAVES_DIR_NAME`, `CABLE-SYNC-EMULATOR-SAVES-LEAK-1`).

**Re-verificado 2026-09-22 (Día69), contra el código real, no contra
suposiciones**: los 3 sitios señalados como candidatos ya excluyen
`.stversions/` hoy — no falta ningún guard nuevo.

- Los 3 walks **locales** (`cable_engine.py:56` `iter_files`,
  `cable_sync_daemon.py:432-437` `_iter_local`, `sync_cable.py:516-521`
  `_iter_files`) ya filtran `not d.startswith(".")` antes de mirar
  `TRASH_DIR_NAME`/`EMULATOR_SAVES_DIR_NAME` — cualquier directorio oculto,
  `.stversions` incluido, nunca entra.
- El lado **Android** (`sync/adb_transport.py`, `ls_recursive()` y
  `_hash_recursive()`/`sha1_recursive()`/`md5_recursive()`, usados por
  `cable_sync_daemon.py:421` y por `_do_adb_scan` en `web/handlers/scan.py:456`
  — el mismo scan que alimenta `library_android.db` para
  `DUP-DISC-SET-2`/`DUP-DISC-TRACK-1` arriba) ya excluye por defecto
  (`exclude_hidden=True`) cualquier segmento de ruta que empiece por `.`, y
  `.stversions` empieza por punto. Confirmado con `git log`: el filtro de
  `ls_recursive` existe desde marzo 2026 (`ebd9f54`) y el de
  `_hash_recursive` desde el 2026-09-19 (`7be90a7`, `ANDROID-DUP-2`) —
  **ambos ya estaban en el código antes** de que se encontrara el leak el
  2026-09-21, así que ningún camino de sync/escaneo persistente de este
  proyecto pudo haberlo producido.
- Causa real de los 2 casos encontrados: la comparación SHA1 de
  `CABLE-SYNC-LEGACY-DUPS-1` fue un script ad-hoc de esa sesión (no hay
  ningún endpoint/feature `legacy-dup*` en el código — la propia entrada de
  `CABLE-SYNC-LEGACY-DUPS-1` dice "limpieza manual en el dispositivo, sin
  tocar código"), que aparentemente sí leyó `.stversions/` sin pasar por
  `AdbTransport`. No es un gap del cable-sync/escaneo real.

**Obsoleto — sin fix de código que hacer** (mismo patrón que la rama 07 del
roadmap general, `.claude/roadmaps/INDEX.md`): el problema tal como está
descrito ya no existe en el cable-sync/escaneo persistente. Si se repite un
script ad-hoc de comparación de saves en el futuro, aplicar el mismo filtro
`exclude_hidden`/`startswith(".")` que ya usa el resto del proyecto.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ANDROID-STVERSIONS-1 | Medir el alcance real de `saves/.stversions/` en la Anbernic (ADB) y, si procede, excluirlo del cable-sync/escaneo de duplicados igual que `_descartados/`/`emulator_saves/` | `web/handlers/sync_cable.py`, `sync/cable_engine.py`, `web/cable_sync_daemon.py`, `sync/adb_transport.py` | ⚪ **obsoleto, verificado 2026-09-22** — los 3 sitios y `AdbTransport` ya excluyen directorios ocultos (`.stversions` incluido); el leak de Día67 vino de un script ad-hoc fuera del código persistente, no de un gap real |

---

### ANDROID-DUP-3 — `famicom/` es una segunda carpeta-plataforma paralela a `nes/` (86% de solapamiento por nombre+tamaño) con un pack de scraper (imágenes/vídeo) tratado como si fuera la librería; `fds/` duplica literalmente el contenido de `Famicom Disk System/` y además arrastra volcados de placa arcade y NES sueltos (hallazgo 2026-09-19, RG556, resuelve el punto 4 pendiente de `ANDROID-DUP-1`)

Origen: verificando el punto 4 de `ANDROID-DUP-1` ("verificar contenido real
de `fds/` vs `Famicom Disk System/` antes de aplicar `DUALFOLDER-12`"), por
ADB en vivo contra `/storage/521D-04EA/ROMs/` de la RG556 (misma consola,
misma sesión que `ANDROID-DUP-1/2`).

**Gotcha de tooling encontrado en el camino**: `adb.exe shell <args...>`
concatena todos sus argumentos con espacios y reenvía **una sola cadena** al
shell remoto — las comillas que Git Bash ya consumió al tokenizar no viajan.
Un comando como `adb.exe shell ls -la "/ruta/con espacios/"` llega partido en
3 tokens al dispositivo y falla o (peor) apunta a una ruta distinta que
coincide parcialmente por case-insensitivity de exFAT. Forma correcta:
pasar el comando remoto completo como **un único argumento** con sus propias
comillas simples: `adb.exe shell "ls -la 'ruta con espacios'"`. Así fue como
apareció por accidente el hallazgo de `famicom/` de abajo (un primer intento
mal citado listó esa carpeta por error, en vez de `Famicom Disk System/`).

**`fds/` vs `Famicom Disk System/` (27 vs 2 entradas)**:
`Famicom Disk System/` contiene exactamente 2 archivos reales: `Mysterious
Murasame Castle, The (Korea) (Virtual Console).fds` (131.000 bytes) y `Super
Mario Bros. 2 (Japan) (En).fds` (65.500 bytes). `fds/` (**26 entradas**,
recuento corregido — `ANDROID-DUP-1` decía 27 por un `ls` mal contado)
contiene los mismos 2 `.fds` duplicados, más **10** archivos que no son ROM
de ninguna plataforma de este proyecto (recuento corregido — se dijeron 7 en
un primer repaso: `400-a01.fse`, `400-a02.fse`, `400-a04.10l`, `400-a06.15l`,
`400-e03.5l`, `412-a05.12l`, `412-a07.17l`, `mds-gn chr e.u4`, `mds-gn prg
e.u7`, `rp2c04-0003.pal`), un `gamelist.xml` de frontend, 5 juegos NES con
pareja `.zip`+`.nes`, y 2 ZIPs adicionales sin pareja `.nes` visible
(`Goonies (Japan) (Disk Writer).zip`, `TwinBee (Japan) (En) (Disk
Writer).zip`).

**Verificación por SHA1 (no solo nombre/tamaño) — sesión de reparación,
todo el árbol de decisión de abajo confirmado con hash real, cero
suposiciones**:
- Los 6 ZIPs "regionales" (`Balloon Fight (Japan) (En) (Proto).zip`, `Ice
  Climber (Japan) (En) (Disk Writer).zip`, `Metroid (Japan) (Rev 1).zip`,
  `Super Mario Bros. (Japan) (En).zip`, `Super Mario Bros. 2 (Japan) (En).zip`,
  `Super Mario Bros. 2 (USA) (Rev 1).zip`) **no son dumps regionales
  distintos** — cada uno contiene, byte a byte (SHA1 idéntico), el mismo
  `.nes`/`.fds` que ya está suelto sin comprimir en la misma carpeta `fds/`.
  Repaquetados redundantes, nombre engañoso (el tag "(Japan)"/"(Proto)" no se
  corresponde con el contenido real).
- Los 10 "volcados de chip" **son exactamente el contenido interno,
  archivo por archivo (SHA1 idéntico), de `Goonies (Japan) (Disk
  Writer).zip` (3 ficheros: `mds-gn chr e.u4`, `mds-gn prg e.u7`,
  `rp2c04-0003.pal`) y `TwinBee (Japan) (En) (Disk Writer).zip` (7 ficheros:
  los `400-*`/`412-*`)** — ambos ZIPs son sets arcade MAME reales de Nintendo
  VS. System (VS. The Goonies / VS. TwinBee), no juegos de Famicom Disk
  System pese al tag "(Disk Writer)". Alguna herramienta los extrajo sueltos
  en `fds/` en algún momento — exactamente el patrón que el propio
  `CLAUDE.md` ya prohíbe (`ZIP-ROUTE`: "un ZIP arcade nunca se extrae, el ZIP
  es el ROM").
- Los 2 `.fds` de `fds/` son SHA1-idénticos a los de `Famicom Disk System/`.
- Los 5 `.nes` sueltos de `fds/` (`Balloon Fight (USA)`, `Ice Climber (USA,
  Europe, Korea)`, `Metroid (USA)`, `Super Mario Bros. (World)`, `Super
  Mario Bros. 2 (USA) (Rev 1)`) son SHA1-idénticos a copias ya existentes en
  `nes/` — 4 con el mismo nombre exacto, y `Ice Climber` con el mismo hash
  bajo un tag de región ligeramente distinto ya presente en `nes/`
  (`Ice Climber (USA, Europe, Asia) (En).nes`). Además, `Ice Climber (Japan)
  (En) (Disk Writer).nes` existe con SHA1 idéntico **tanto en `nes/` como en
  `famicom/`** — mismo patrón de duplicado de plataforma completa ya descrito
  más abajo.

**Conclusión**: `fds/` no tiene ni un solo byte de contenido único —
absolutamente todo lo que contiene es, o bien un duplicado confirmado por
hash de algo que ya existe en `Famicom Disk System/`/`nes/`, o bien un
repaquetado redundante de otro archivo de la misma carpeta, o bien un ZIP
arcade mal ubicado. No aplica `DUALFOLDER-12` tal cual (no es un par limpio
tipo `atari2600/`+`Atari 2600/`): hacen falta 3 acciones distintas — (a)
borrar los 6 ZIPs regionales + los 10 volcados de chip sueltos + los 2 `.fds`
+ los 5 `.nes`, todos con duplicado confirmado por hash, (b) mover
`Goonies...zip`/`TwinBee...zip` a `arcade/` (son ROM arcade legítimos, mal
ubicados, no basura), (c) dejar `gamelist.xml` tal cual (metadata de
frontend, fuera de alcance). Implementado en rama `fix/android-fds-cleanup`
— ver tarea `ANDROID-FDS-CLEANUP-1` más abajo.

**Hallazgo nuevo, mayor: `famicom/` duplica `nes/` a escala de plataforma
completa**. `famicom/` tiene **5.184 archivos** — no es solo un pack de ROMs:
3.092 `.png`, 1.530 `.nes`, 460 `.jpg`, 100 `.mp4`, 1 `.xml`, 1 `.db`, repartidos
en subcarpetas propias de un scraper de frontend: `media/` (412 `.jpg`),
`downloaded_images/` (2.992 archivos, el grueso de los `.png`),
`top100/` (18), más dos packs con nombre de curador: `# DYNAVISION #` (91
`.nes`) y `# PT-BR #` (199 `.nes`, romhacks de traducción al portugués de
Brasil, tags `[T-BR] [T-Balboa G-Monkey's Traducoes]` — **legítimos, no
duplicados**, mismo caso ya señalado en `ANDROID-DUP-1` para parches `[T+...]`).
De los 1.530 `.nes` de `famicom/` (recursivo), **1.313 (86%) comparten nombre
exacto con un archivo de `nes/`** (3.336 `.nes` en `nes/`). Muestreo de 3
coincidencias (`Bases Loaded (USA).nes`, `NFL (USA).nes`, `Championship Rally
(Europe).nes`) — mismo tamaño byte a byte en ambas carpetas. Las copias de
`nes/` datan de 2026-03-11 (pasada de renombrado canónico No-Intro de este
proyecto); las de `famicom/` son todas del mismo instante, 2026-09-09 13:16
— una única importación posterior en bloque, casi seguro un "pack" de
scraper para DaijiShō/iSuu que trajo sus propias copias de ROM junto con el
material gráfico. Como DaijiShō/iSuu normalmente mapean "Famicom" y "NES" al
mismo core/sistema, esta carpeta paralela completa es una explicación mucho
más directa de "todos los juegos NES aparecen duplicados" que el matiz de
nomenclatura legado `[!]`/`(U)` ya documentado — probablemente ambas causas
se suman.

**Recomendación (sin implementar, a decidir con el usuario)**:
1. Confirmar por SHA1 los 1.313 candidatos `famicom/`↔`nes/` en cuanto
   termine el rescan ADB con hash en curso (`ANDROID-DUP-1`/`ANDROID-DUP-2`)
   — la evidencia de esta sesión es solo nombre+tamaño, no hash.
2. Decidir con el usuario el tratamiento de `famicom/`: ¿carpeta redundante a
   fusionar/eliminar tras verificar hash (conservando el material gráfico si
   aporta valor), o cache activa de DaijiShō/iSuu que debe excluirse
   explícitamente de cualquier dedup/organize futuro (vía
   `excluded_directories` en `config.py`, ya usado para BIOS/Android)? No
   borrar unilateralmente sin confirmar que `media/`/`downloaded_images/`/
   `top100/` no los gestiona activamente un frontend de terceros.
3. Los 91 `# DYNAVISION #` y 199 `# PT-BR #` necesitan comparación de
   contenido (no solo nombre) antes de tocarlos — son candidatos a homebrew/
   romhacks legítimos, mismo criterio que los parches `[T+...]` de `nes/`.
4. Extender la recomendación de `DUALFOLDER-12` con un caso "carpeta mixta":
   ni `fds/`↔`Famicom Disk System/` ni `famicom/`↔`nes/` son pares limpios
   como `atari2600/`/`Atari 2600/` — ambos arrastran contenido ajeno a la
   plataforma nominal y necesitan triage antes de fusionar.

**Intento de investigar la config de DaijiShō/iSuu en el dispositivo (opción
elegida por el usuario para decidir el punto 1)**: bloqueado sin root.
`adb shell` corre como `shell` (uid 2000, grupo `ext_data_rw` incluido), y
`Android/data/{com.magneticchen.daijishou,com.iisulauncher}/files/` están
genuinamente vacías (no es un bloqueo de permisos — el propietario del
directorio coincide con un grupo al que `shell` pertenece). Ninguna de las
dos apps es depurable (`run-as` falla con "package not debuggable"), así que
su almacenamiento interno (`/data/data/<paquete>/databases`, donde
probablemente vive la config real de "sistemas") no es legible sin root.
Confirmar si `famicom`/`nes` (o `fds`/`Famicom Disk System`) están dados de
alta como sistemas duplicados en la propia app requiere mirarlo
**directamente en el dispositivo**, dentro de la UI de cada launcher — mismo
límite ya documentado para el caso PS2 en `ANDROID-DUP-1`.

Fds/famicom no implementado en esta sesión salvo lo indicado en
`ANDROID-FDS-CLEANUP-1` (más abajo) | Evidencia recogida por ADB en vivo
(`adb shell find/ls/sha1sum` contra `/storage/521D-04EA/ROMs/{fds,Famicom
Disk System,famicom,nes}/`) | 🟡 `fds/` resuelto y verificado por hash
(`ANDROID-FDS-CLEANUP-1`); `famicom/` vs `nes/` y la config de
DaijiShō/iSuu siguen sin decidir — pendiente de que el usuario revise la
app en el dispositivo |

---

### ANDROID-FDS-CLEANUP-1 — Limpieza de `fds/` verificada por SHA1: 0 bytes de contenido único, todo duplicado o mal ubicado (implementa la conclusión de `ANDROID-DUP-3`) → #TBD

**✅ Ejecutado 2026-09-19** directamente sobre la RG556 vía ADB (`adb shell
rm`/`mv`, sin pasar por `rommgr plan`/`apply` — no existe hoy un flujo de la
herramienta para operaciones ad hoc sobre `library_android.db`, ver
`ANDROID-ORGANIZE-ADB-1`; toda la evidencia de verificación por SHA1 queda
documentada en `ANDROID-DUP-3`):

1. **Borrados** 6 ZIPs regionales (`Balloon Fight (Japan) (En) (Proto).zip`,
   `Ice Climber (Japan) (En) (Disk Writer).zip`, `Metroid (Japan) (Rev
   1).zip`, `Super Mario Bros. (Japan) (En).zip`, `Super Mario Bros. 2
   (Japan) (En).zip`, `Super Mario Bros. 2 (USA) (Rev 1).zip`) — SHA1
   idéntico confirmado contra el `.nes`/`.fds` ya suelto en la misma carpeta.
2. **Borrados** los 10 volcados de chip sueltos (`400-*.fse/.10l/.15l/.5l/.12l/.17l`,
   `mds-gn chr e.u4`, `mds-gn prg e.u7`, `rp2c04-0003.pal`) — SHA1 idéntico
   confirmado contra el contenido interno de `Goonies...zip`/`TwinBee...zip`.
3. **Movidos** `Goonies (Japan) (Disk Writer).zip` y `TwinBee (Japan) (En)
   (Disk Writer).zip` a `arcade/mame/` — son ROM arcade MAME (Nintendo VS.
   System) legítimos, no basura ni contenido de FDS. Verificado que no
   chocaban con nada ya existente (`arcade/fbneo/vsgoonies.zip` es un `.nes`
   convertido para FBNeo, contenido distinto byte a byte; `arcade/mame/twinbee.zip`
   es el TwinBee normal no-VS, y `arcade/fbneo/twinbeeb.zip` es otro bootleg
   parcialmente solapado pero no idéntico — ningún nombre de fichero chocaba)
   y llegada confirmada con `ls -la` post-mv.
4. **Borrados** los 2 `.fds` duplicados de `fds/` (quedan en `Famicom Disk
   System/`, verificado intacto tras el borrado) y los 5 `.nes` duplicados
   de `fds/` (quedan en `nes/`, verificado intacto tras el borrado) — SHA1
   idéntico confirmado en ambos casos.
5. `gamelist.xml` sin tocar (metadata de frontend, fuera de alcance).

**Resultado verificado con `ls -la` tras la limpieza**: `fds/` solo contiene
`gamelist.xml` (3364 bytes) — 0 contenido propio, tal como predecía el
análisis. `Famicom Disk System/` conserva sus 2 `.fds`, `nes/` conserva las
5 copias canónicas, `arcade/mame/` tiene ahora `Goonies...zip` y
`TwinBee...zip`. 0 pérdida de datos, 23 archivos borrados + 2 movidos.

Pendiente: PR a `develop` con el commit de documentación ya hecho en
`fix/android-fds-cleanup` (`68a4563`) — confirmar con el usuario antes de
mergear, como de costumbre | Evidencia SHA1 completa en `ANDROID-DUP-3` |
✅ ejecutado y verificado 2026-09-19

---

### ANDROID-ORGANIZE-ADB-1 — `organize-source` ya tiene el motor de dedup+ruteo arcade necesario; el hueco real es que no existe transporte de escritura ADB, solo filesystem local → #275

Origen: el usuario preguntó en medio de la limpieza de `fds/`
(`ANDROID-FDS-CLEANUP-1`) si la función "organize" ya arregla este tipo de
casos, y si no, que se le añadiera.

**No hace falta construir un motor de dedup nuevo — ya existe y está muy
probado.** `organize-source` (CLI, `cli.py:258-286` registra el subcomando,
`cli.py:1133-1280` lo implementa reutilizando `_run_inbox_pipeline` de
`web/inbox_pipeline.py`) ya hace exactamente lo necesario: detecta ZIPs
arcade completos por CRC sin extraerlos (`_is_arcade_zip_container`), extrae
y organiza el resto, deduplica por SHA1/CRC interno, y resuelve conflictos de
nombre — es el mismo motor que resolvió toda la saga
`ARCADE-DAT-CONTAMINATION-*`/`PSX-STRUCTURE-*` (cientos de miles de archivos,
sesiones de 2026-09-02 a 09-04), incluida la propia Anbernic (`E:\Carpetas
anbernic`, máquina "rammu").

**El límite real es de transporte, no de lógica**: `organize-source` exige
`source_path.resolve().exists()` (`cli.py:1137-1138`) — un `pathlib.Path`
real del sistema de archivos. Eso funcionaba contra la Anbernic en la máquina
"rammu" porque ahí la SD se monta como letra de unidad. En esta máquina
("Ruben"), la RG556 no se monta como unidad (probable causa: Android
11+/MTP sin soporte de almacenamiento masivo) — el único acceso es `adb`, y
`AdbTransport` (`sync/adb_transport.py`) hoy **solo tiene lectura**
(`ls_recursive`, `sha1_recursive`, `md5_recursive`); no hay `mv`/`rm`/`push`
genérico. La versión web más simple, `_do_organize_library`
(`web/handlers/organize.py:410`), tampoco sirve de comparación — ni siquiera
tiene dedup de contenido, solo mueve por `platform` de la BD, y también
asume filesystem local (`shutil.move`).

**Dos caminos, sin implementar ninguno todavía**:
1. **Sin código nuevo**: si se puede extraer la tarjeta SD de la RG556 y
   leerla con un lector USB (monta como letra de unidad en Windows),
   `organize-source --apply` funciona hoy mismo tal cual, sin tocar una
   línea — sería la forma más rápida de limpiar `fds/`/`famicom/` con la
   herramienta real en vez de comandos `adb` sueltos como en
   `ANDROID-FDS-CLEANUP-1`.
2. **Con código nuevo**: añadir transporte de escritura a `AdbTransport`
   (`push`/`pull`/`mv`/`rm`) y un adaptador para que `organize-source` opere
   sobre él — o, más barato de construir, un modo "espejo": `adb pull` a un
   directorio temporal, correr `organize-source --apply` normal ahí (cero
   cambios a su lógica ya probada), y `adb push`+`adb rm` de vuelta solo de
   lo que cambió. El coste es red (round-trip de contenido que sí se mueve),
   no lógica nueva.

**Recomendación**: decidir con el usuario si la opción 1 (lector SD) resuelve
ya el caso concreto de esta sesión antes de invertir en la opción 2 — que sí
merecería su propio epic/issue si se decide construirla, dado que es una
pieza de infraestructura reutilizable (serviría para cualquier limpieza
futura sobre Android, no solo `fds/famicom`), no solo un fix puntual.

No implementado en esta sesión | `cli.py:1133-1280` (`organize-source`),
`web/inbox_pipeline.py` (`_run_inbox_pipeline`), `sync/adb_transport.py`
(solo lectura), `web/handlers/organize.py:410` (`_do_organize_library`, web,
tampoco sirve) | 🔵 investigado, decisión de alcance pendiente del usuario |

### GBA-DUAL-FOLDER-1 — `Game Boy Advance/` y `gba/` son dos carpetas activas paralelas con 881 títulos duplicados (hallazgo 2026-09-14, máquina "Ruben", `F:\Juegos Retro`)

Encontrado al preparar el envío de GBA a la Anbernic. `F:\Juegos Retro` tiene
**dos** carpetas con contenido GBA real (no confundir con `GBA-MISPLACED-1`,
que era sobre archivos de OTRAS plataformas coladas en `gba/` en la otra
biblioteca — aquí ambas carpetas son GBA legítimo): `Game Boy Advance/` (985
archivos, 7,5 GB, nombrado canónico) y `gba/` (1054 archivos, 11,9 GB, slug
en minúsculas — mismo patrón que usan RetroBat/EmulationStation, ambos
instalados en este mismo disco `F:\`). Ambas están indexadas bajo el mismo
`platform='Game Boy Advance'` en `library_pc.db` (2037 filas totales), y
**881 `canonical_title` distintos existen en ambas carpetas a la vez** —
probablemente `gba/` es la carpeta legada de antes de que este proyecto
organizara la biblioteca en carpetas de nombre canónico, nunca limpiada
después. No bloquea el envío de hoy (`filter_duplicate_winners`, ya genérico
por plataforma, colapsa correctamente estos duplicados antes de enviar por
RA), pero es 11,9 GB de posible redundancia real en el PC sin confirmar si
`gba/` tiene algo que `Game Boy Advance/` no tenga (173 títulos exclusivos de
`gba/`, sin verificar si son copias con otro nombre o contenido genuino
distinto) | `F:\Juegos Retro\gba\` vs `F:\Juegos Retro\Game Boy Advance\` |
✅ limpiado y purgado 2026-09-15 (diario Día63) — reutilizado
`filter_duplicate_winners()` (mismo motor que el envío GBA→Anbernic) para
identificar ganador/perdedor: 898 duplicados reales (11,57 GB) descartados a
`_descartados/` (reversible), y luego purgados de verdad a petición
explícita del usuario ("purga descartados, ya que son juegos repetidos") —
900 archivos, 11,58 GB (incluye 2 más antiguos de la misma carpeta). La
sospecha de que el patrón afectaba a más plataformas se confirmó: ver
`PS2-DUAL-FOLDER-1` y `DUALFOLDER-12` (11 pares más, resueltos 2026-09-17) |

### PS2-DUAL-FOLDER-1 — `organize-source` crea un segundo `ps2/` en vez de usar `PlayStation 2/` ya existente (hallazgo 2026-09-15, máquina "Ruben", `F:\Juegos Retro`)

Plan de implementación (medición de las 11 carpetas duplicadas restantes +
pasos) en `.claude/roadmaps/archivo/12-dual-folder-title-case-slug.md`, junto con
`GBA-DUAL-FOLDER-1`.

Confirma la predicción de `GBA-DUAL-FOLDER-1` ("verificar si hay pares
`ps2/`+`PlayStation 2/`"). Al organizar 21 juegos de PS2 encontrados sin
identificar en `Unknown\` (Kingdom Hearts, Kingdom Hearts II, GTA San Andreas,
Metal Gear Solid 2, Grandia II/III, Gradius V, Dark Cloud, Shadow Hearts, Dead
or Alive 2, Street Fighter III 3rd Strike — todos con `canonical_title`
poblado, `platform` seteado a mano vía `CatalogMatcher` directo tras un
cuelgue del job `match` general, ver más abajo), `rommgr organize-source
--apply` los movió (y renombró a su nombre canónico) a `F:\Juegos
Retro\ps2\` — carpeta que hasta hoy solo tenía un `media/` vacío — en vez de
`PlayStation 2\`, donde ya viven los otros 26 juegos de PS2 del PC.

**Causa raíz, no es un bug**: `web/handlers/system.py:34`
(`_ES_PLATFORM_FOLDERS["PlayStation 2"] = "ps2"`) es el mapeo que usa
`inbox_pipeline.py::_platform_folder_name()` (línea 40-43) para decidir dónde
organiza el Inbox — deliberadamente el slug en minúsculas que reconocen
RetroArch/EmulationStation (mismo criterio que ya usa `canonical_rel_posix()`
en el cable-sync tras `CABLE-ROOT-1`). La carpeta `PlayStation 2\` (Title
Case) con los 26 juegos existentes **no la creó este proyecto** —
`operation_planner.py::build_plan()` solo renombra el archivo dentro de su
carpeta actual (`target = source.parent / new_filename`, línea 181), nunca
mueve entre carpetas de plataforma — así que es una carpeta legada de antes
de esta herramienta, igual que `Game Boy Advance\` en `GBA-DUAL-FOLDER-1`.
El Inbox siempre va a preferir el slug Android; cualquier carpeta legada
Title Case queda huérfana y nunca vuelve a recibir contenido nuevo del
pipeline salvo consolidación manual.

**Corregido en caliente hoy** (sin cambiar código): los 21 archivos movidos a
mano de `ps2\` a `PlayStation 2\` (`shutil.move`, sin conflictos de nombre)
para mantener consistencia con el resto de la biblioteca PS2 del PC, y
`rommgr scan` re-corrido para actualizar `source_path` en la BD | `ps2\`
(vacío tras la consolidación, solo queda `media/`) vs `PlayStation 2\` (ahora
47 juegos) | `web/handlers/system.py:34` (`_ES_PLATFORM_FOLDERS`),
`web/inbox_pipeline.py:40-43` (`_platform_folder_name`),
`planner/operation_planner.py:181` (`build_plan`, nunca mueve entre
carpetas) | ✅ resuelto — decisión tomada 2026-09-15 (el slug Android es el
canónico también en el PC) y ejecutada en `DUALFOLDER-12` (2026-09-17): los
11 pares restantes consolidados + guard `_platform_folder_name()` en el
Inbox para que no vuelva a pasar en silencio con una plataforma futura |

### CATALOG-MATCH-SUBSET-1 — `_match_by_title()` no comprobaba `is_non_canonical_variant()`, asignando el `canonical_title` del original a hacks/parches de traducción (hallazgo 2026-09-17/18, máquina "Ruben", `F:\Juegos Retro`) → rama `fix/catalog-match-subset-hack`

Investigando un aviso del usuario ("Pokemon Fire Red ahora es el Professor
Oak Challenge, los logros son peores, también en la Anbernic"). Verificado
por hash MD5 que los `.gba` reales de Fire Red **no estaban tocados** ni en
PC ni en Anbernic (coinciden con los hashes conocidos del original) — el
hack nunca llegó al dispositivo, seguía sin organizar en `Unknown\`. El
Charizard negro en los logros de la Anbernic no se explica por nada de esta
biblioteca (probable caché de badges del lado RetroArch/RA, fuera del
alcance de esta herramienta).

Causa raíz real encontrada: `catalog/matcher.py::_match_by_title()` (Pass 2,
fallback por título cuando el SHA1 no está en el catálogo — el caso de
cualquier hack/parche, que nunca tiene su propio SHA1 en No-Intro/Redump) no
llamaba a `is_non_canonical_variant()` (`detection/filename_normalizer.py`),
el mismo guard que **sí** ya usan `planner/operation_planner.py:121` (evita
renombrar el hack con el nombre del original) y
`web/builders/duplicates.py:786,800` (evita agruparlo como duplicado en la
cola de revisión) — el guard existía pero solo se aplicaba río abajo, no en
el origen donde se asigna `canonical_title`. `normalize_for_match()` trata
`[Subset - Professor Oak Challenge]` como una anotación benigna más (igual
que `(USA)` o `[!]`), así que el hack matcheaba por título contra el
catálogo del original con confianza "medium".

Efecto ya real en la biblioteca (no solo teórico): `Pokemon - Ruby Version
[Subset - Professor Oak Challenge].gba` **ya estaba organizado** en `gba\`
con `canonical_title = "Pokemon - Ruby Version (Europe) (Rev 1)"` — el mismo
título que el Ruby real, sin organizar en `Unknown\`. El guard de
renombrado evitó que el hack robara el nombre de archivo del real, pero
`filter_duplicate_winners()` (`services/ra_duplicates_service.py`, usado por
el envío GBA→Anbernic y por el dedup de `DUALFOLDER-12`) tampoco comprobaba
`is_non_canonical_variant()` — un futuro dedup de GBA podría confundirlos.
✅ Arreglado en `fix/dup-winners-non-canonical-guard` (2026-09-18): el hack
ahora se trata como `single` (nunca entra en el grupo por título del
original), mismo guard que `_match_by_title()` y `duplicates.py`. Test
`test_filter_duplicate_winners_never_discards_real_copy_for_hack`, 1342
tests en verde.

**Arreglado en `fix/catalog-match-subset-hack`**: `_match_by_title()` ahora
llama a `is_non_canonical_variant()` al principio y devuelve `None` si el
filename es un hack/parche — no vuelve a pasar con archivos nuevos. Se
limpió a mano (sin mover/borrar nada) el `canonical_title` de los 4
registros ya afectados por los hacks de Pokémon (FireRed/Ruby/Emerald
"Professor Oak Challenge", el Ruby cuenta 2 veces: `Unknown\` + `gba\`).

**Alcance mayor detectado, fuera de esta rama**: al buscar todas las filas
con `canonical_title` poblado + `is_non_canonical_variant(original_filename)`
aparecieron **1183 filas** en toda la biblioteca — mayoría parches de
traducción NES (`[T+Por...]`, `[T-Por]`...), el mismo patrón que ya
documentó `CATALOG-MATCH-VARIANT-1` (hallazgo de 22 parches de Zelda,
2026-09-09) sin llegar a limpiarse en la BD. Decisión del usuario
2026-09-18: dejar esas 1179 filas restantes sin tocar por ahora — no hay
evidencia de que hayan causado daño real (a diferencia del Ruby, ninguna
está ya organizada bajo un nombre prestado). Revertida el mismo día: el
usuario pidió limpiarlas también | `catalog/matcher.py:281-296`
(`_match_by_title`), `detection/filename_normalizer.py:65-74`
(`is_non_canonical_variant`), `services/ra_duplicates_service.py`
(`filter_duplicate_winners`) | ✅ guard en `filter_duplicate_winners()`
arreglado en `fix/dup-winners-non-canonical-guard`. ✅ limpieza de las 1179
filas ejecutada 2026-09-18 sobre `library_pc.db` (`library_android.db`: 0
filas afectadas). Backup previo (`library_pc.db.bak-20260918-223238`,
gitignored). Verificado primero: de las 1179, **1175 eran del fallback por
título** (`match_confidence` `low`/`medium`, el bug real) y **4 eran matches
legítimos por SHA1** (`match_confidence high`, No-Intro sí cataloga esos 4
hacks `[h1]`/`[h3]` por su propio hash) — las 4 se dejaron intactas, solo se
limpiaron `canonical_title`/`match_confidence`/`catalog_source` (a `NULL`)
de las 1175 restantes. También verificado: **0 de las 1175 tenían el
archivo ya renombrado** en disco al nombre prestado (`source_path` basename
== `original_filename` en todos los casos) — el guard de
`operation_planner.py` ya las había protegido, a diferencia del caso Ruby.
Quedan sin `canonical_title` (correcto: un hack/parche no tiene entrada
propia en No-Intro/Redump, así que no debe matchear) |

### DUALFOLDER-12 — 11 pares Title Case/slug restantes consolidados + guard en el Inbox (2026-09-17, máquina "Ruben", `F:\Juegos Retro`) → roadmap 12

Plan e implementación completos en
`.claude/roadmaps/archivo/12-dual-folder-title-case-slug.md`. Resuelve la dirección
que `GBA-DUAL-FOLDER-1`/`PS2-DUAL-FOLDER-1` dejaron sin decidir: el slug es
el canónico también en el PC (misma tabla `_ES_PLATFORM_FOLDERS` que ya usa
el cable-sync).

5 pares triviales (`Game Boy`→`gb`, `Game Gear`→`gamegear`,
`Master System`→`mastersystem`, `Neo Geo`→`neogeo`, `PlayStation`→`psx`) +
6 pares con posible dedup (`Game Boy Color`, `Nintendo 3DS`, `Nintendo 64`,
`Nintendo DS`, `Sega Mega Drive`, `Super Nintendo`/`snes`). Hallazgo: 3 de
los 6 últimos no eran duplicados de ROM reales — `nds/` tenía 84 saves `.sav`
huérfanos + 2 ROMs (no "3 ROMs" como decía la medición de origen) mientras
los 338 ROMs reales vivían en `Nintendo DS/`; `3ds/Rockman X3...bin` es un
ROM de SNES mal clasificado, no un duplicado del `.3ds` real; `gbc/` tenía
13 betas/prototipos únicos sin solapar. Los otros 3 pares (168 archivos)
usaron `filter_duplicate_winners`/`resolve_duplicate_ra`
(`services/ra_duplicates_service.py`), el mismo motor que ya usa el sync
GBA→Anbernic, filtrando primero a solo grupos con **todas** sus entradas
dentro del par (una pasada inicial incluía por error cientos de grupos que
tocaban `Unknown/`, fuera de alcance).

Guard nuevo en `_platform_folder_name()` (`web/inbox_pipeline.py:40-43` →
ahora acepta `target_root` opcional): si el slug de destino tiene junto a él
una carpeta Title Case legada con contenido real, loguea un warning
(`DUALFOLDER-12`) sin bloquear — conectado en el Paso 6 real de organización.
3 tests nuevos en `test_inbox_scan_preview.py` | `web/inbox_pipeline.py`
(`_platform_folder_name`, `_folder_has_real_content`) |
✅ commit/PR a `develop` confirmado por el usuario 2026-09-18, rebasado sobre
`develop` (incluye `CATALOG-MATCH-SUBSET-1`, sin conflicto real de código).
**Corrección 2026-09-20**: el hallazgo original decía "SNES mal detectado"
para `3ds/Rockman X3 (Unl) [c][!].bin` — verificado a mano (tabla de
vectores 68k en offset 0x0 + firma `"SEGA"` en offset 0x100, tamaño 2 MiB),
en realidad es una ROM de **Sega Genesis/Mega Drive** (bootleg no
licenciado), no de SNES. Reclasificado y movido a `megadrive/` (carpeta
canónica, sin colisión de nombre), rescaneadas ambas carpetas (`3ds/`,
`megadrive/`) para que SQLite refleje la nueva ubicación. Fuera de alcance
del matcher (`(Unl)` sin `canonical_title` en el DAT, no renombrable) |

### MATCH-HANG-CHDMAN-1 — el job `match` (CLI y web) puede colgarse decenas de minutos sin avisar, sin poder cancelarse (hallazgo 2026-09-15)

Plan de implementación en `.claude/roadmaps/archivo/13-match-chdman-robustness.md`.

Al re-lanzar `POST /api/match` sobre las 7.738 filas sin resolver (tras añadir
el catálogo arcade), el job se quedó `running=true` más de 30 minutos sin
avance visible. `Get-Process python` mostró **CPU casi plano** (35,4s → 35,6s
en 10+ minutos reales) — el proceso Python en sí no estaba calculando nada,
solo bloqueado esperando un `subprocess.run()`; el trabajo real ocurre en un
`chdman.exe` hijo cuyo tiempo de CPU no aparece en `Get-Process python`.
`POST /api/stop-job` (`job_manager.cancel_event`) no lo paró — el bucle de
`match()` solo comprueba `_cancel.is_set()` entre filas, nunca dentro de una
llamada bloqueante. Mismo síntoma que la prueba de `.cdi` de hoy
(`DREAMCAST-FORMAT-MISMATCH-1`): `chdman` puede tardar minutos/no completar
nunca sobre un archivo concreto sin que el timeout individual (300s en
`_extract_chd`, `ra_cd_image.py:207`) ayude si hay **varias** filas PSX
ambiguas en la cola que disparan `detect_psx_boot_serial()` →
`_extract_chd()` una tras otra — cada una puede consumir hasta 5 min sin que
el job progrese ni pueda cancelarse antes de que termine la fila actual.
Recuperado matando el proceso del servidor y reiniciándolo (sin pérdida de
datos — `update_match` corre dentro de un único `batch()`/transacción por el
run completo, así que nada se comiteó a medias) | `catalog/matcher.py`
(`_match_by_title`, dispara `detect_psx_boot_serial` para desambiguar región
PSX), `retroachievements/ra_hash_psx.py:181-184`
(`detect_psx_boot_serial`, rama `.chd`), `retroachievements/ra_cd_image.py:207`
(`_extract_chd`, timeout de 300s por llamada, no por job), `web/handlers/scan.py`
(`_do_match`, el bucle solo comprueba `_cancel` entre filas) | ✅ arreglado
2026-09-15 (roadmap `13-match-chdman-robustness.md`, rama
`fix/match-chdman-robustness`). **(a)** `_extract_chd()` acepta ahora un
parámetro `timeout` (default 300s, sin cambios para la conversión real);
`detect_psx_boot_serial()` pasa `_BOOT_SERIAL_TIMEOUT = 60` — medido con
`chdman extractcd` real contra la biblioteca (~22s el disco de un solo track
más grande, ~17s el multi-track más grande), 60s deja margen de sobra sin
acercarse a los 300s de una conversión real. **(b)** `_do_match` reporta
`job_manager.update_progress("match", {"current", "total", "current_file"})`
por fila, expuesto como `match_progress` en `/api/job-status`
(`JobManager.get_status()`) — mismo patrón que `scan_progress`/`chd_progress`;
barra de progreso nueva en la pestaña Overview (`match-progress-wrap`,
`jobs.js`). **(c)** cancelación real: no hizo falta matar el subprocess —
con el timeout de (a) más el `_cancel.is_set()` que ya se comprueba entre
filas, la espera máxima por fila bajó de 300s a 60s, suficiente para que
cancelar sea cuestión de segundos, no de 30+ minutos. Verificado contra la
biblioteca real: `rommgr match` sobre las 6.518 filas sin resolver actuales
(42 PSX) terminó en 13.4s, sin cuelgue. 5 tests nuevos (`test_ra_hash_psx.py`
×2, `test_jobs_manager.py`, `test_handlers_scan.py`). 1330 tests totales,
ruff+format limpios. **Fuera de alcance deliberadamente**: localizar el
`.chd` exacto que disparó el cuelgue original — no reproducible ahora (la
cola de 7.738 filas de aquel momento ya no existe) y no bloqueante, según lo
previsto en el propio roadmap |

---

### LIBRARY-HEALTH-DASH-1 / DUP-VISUAL-UI-1 — Panel de salud + duplicados side-by-side (idea usuario 2026-09-22)

Consolidar en Inicio los números ya calculados en pestañas sueltas (% organizada,
GB en duplicados, carpetas huérfanas, ZIPs sin organizar) y mostrar los grupos de
duplicados con portada + flag RA en vez de solo tabla de texto. Roadmap:
`.claude/roadmaps/archivo/27-library-ux-dashboard-duplicates.md`, rama
`feature/library-ux-dashboard-duplicates` (PR #340).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| LIBRARY-HEALTH-DASH-1 | Panel de salud en Inicio: % organizada, GB duplicados, carpetas huérfanas, ZIPs sin organizar — cada tarjeta enlaza a su reporte existente | `web/handlers/esde/maintenance.py` (`misplaced_zips` nuevo en `/api/library-extras`), `web/static/partials/tab-overview.html` (`ov-health-dash`), `web/static/js/tabs/overview.js` (`_loadLibraryHealth`) | ✅ hecho 2026-09-22 — sin endpoint agregado nuevo, compone `/api/status` + `/api/library-doctor` + `/api/library-extras` en frontend; test `tests/web/test_library_extras.py::test_library_extras_misplaced_zips` |
| DUP-VISUAL-UI-1 | Vista side-by-side de duplicados con portada + flag RA (fallback a tabla de texto sin portada) | `web/static/js/tabs/review_copies.js` (`_renderReviewEntry` — la vista real de duplicados desde TABS-FIX-6, `duplicates.js` quedó solo como selector PC/Android), `web/builders/duplicates.py` (`id` nuevo en entries del review-queue) | ✅ hecho 2026-09-22 — el roadmap apuntaba a `duplicates.js` (desactualizado); flag RA ya existía, solo faltaba la portada. Sin portada en copias de la consola (limitación preexistente de `/api/asset-image`, solo resuelve contra la BD del PC) |

---

### JUNK-SCAN-RUBEN-1 — Primer junk-scan real de esta máquina: 6.072 archivos / 34,97 GB sin clasificar (hallazgo 2026-09-28, máquina "Ruben", `F:\Juegos Retro`)

**Por qué se lanzó**: durante `JUEGOS-FIX-4`/`SAGE-1` de hoy se vio que esta
máquina diverge fuerte de los números que ya tenía el backlog (cobertura de
scraper real 27,78% vs. 75-90% esperado; los 7 huérfanos de `$RECYCLE.BIN`
de `JUEGOS-FIX-4` resultaron ser de otra máquina, 0 aquí). Sospecha: esta
biblioteca nunca pasó por el junk-scan/limpieza inicial de Pilar 1 que sí
tuvieron otras (`JUNK-SMART-1/2/3`, `JUNK-REVIEW-1`, Día39 — todo eso corrió
contra bibliotecas de otras máquinas). Se lanzó `POST /api/junk-scan` real
(solo lectura, sin borrar/mover nada) para confirmarlo antes de asumir nada.

**Resultado real** (`F:\Juegos Retro`, 291 categorías agrupadas por
confianza):

| Confianza | Archivos | Tamaño | Qué es |
|---|---|---|---|
| `safe_delete` | 3.659 | 4,93 GB | Basura real: chips sueltos sin match, extensiones no-ROM residuales (`.app`, `.tmd`, `.tik`, numéricas sueltas tipo `.03`/`.04`...) — mismo patrón que Día39 |
| `misplaced` | 2.176 | 13,87 GB | ROMs identificadas por CRC pero en la carpeta equivocada — **1.825** por match directo de catálogo ("ROMs de consola identificadas"), **347** por extensión interna de romhack — mismo mecanismo ya construido en `ZIP-ROUTE-1`/`ZIP-ROUTE-3`, sin ejecutar nunca aquí |
| `review` | 237 | 16,18 GB | Necesita decisión: **120 "ZIPs no-ROM" (10,24 GB)** — probablemente colecciones reales (zip-de-zips), mismo caso que `ZIP-ROUTE-4`; **8 "7-Zips" (5,27 GB)** sin manejar por el pipeline actual (solo entiende `.zip`); **108 chips arcade sin match de catálogo**; 1 set arcade de otra versión (0,62 GB) |
| **Total** | **6.072** | **34,97 GB** | |

**Siguiente paso propuesto (sin ejecutar todavía, pendiente de tu confirmación)**:
1. `safe_delete` (4,93 GB): dry-run de `/api/junk-delete` primero, igual que
   Día39/`JUNK-REVIEW-1` — reporta qué borraría, confirmas, luego real
   (va a `_descartados/`, deshacible ~30 días, no es un borrado directo).
2. `misplaced` (13,87 GB): mismo motor de `ZIP-ROUTE-1`/`-3` ya construido
   — mover/renombrar a su carpeta de plataforma real. Sin riesgo de
   pérdida (son ROMs identificadas, no basura), pero sí mueve 2.176
   archivos de sitio.
3. `review` (16,18 GB): requiere mirar caso a caso — **revisados los
   nombres reales de ambos sub-buckets (2026-09-28), no son lo que
   parecían**:
   - **120 "ZIPs no-ROM" NO son colecciones** — son ZIPs de un solo juego
     con nombre canónico No-Intro/Redump ya puesto (`Crash Bandicoot 2 -
     Cortex Strikes Back (USA).zip`, `Bushido Blade (USA).zip`, `Jet Set
     Radio (Europe).zip`...), todos sueltos en `Unknown\` — candidato
     directo para `ZIP-ROUTE-1` (identificación por CRC32 del header, sin
     descomprimir), no para `ZIP-ROUTE-4` (extraer colección). El junk-scan
     los cuenta como "no-ROM" porque su extensión (`.zip`) no delata la
     plataforma por sí sola, no porque sean contenedores multi-juego.
   - **8 "7-Zips" confirmado hueco real**: `converters/zip_extractor.py`
     solo importa `zipfile` (stdlib) — cero soporte de `.7z`, y no hay
     ningún `7z*.exe` en `tools/` (solo `adb.exe`/`chdman.exe`/`rclone.exe`).
     Con la regla del proyecto de "sin dependencias externas de runtime
     (solo stdlib)", la vía correcta sería bundlear `7za.exe` (freeware,
     mismo patrón que `chdman.exe`) e invocarlo por `subprocess`, no una
     librería Python (`py7zr` violaría la regla) — sin implementar,
     documentado como hueco.

**Dry-run de `POST /api/junk-delete` confirmado (2026-09-28)**: los 3.659
paths de `safe_delete` (extraídos del propio `paths` de cada categoría del
junk-scan, no de `files` — ese último viene truncado a 50 por categoría
para la respuesta) → `{"deleted": 3659, "failed": 0, "freed_bytes":
4925918329, "dry_run": true, "errors": []}`. Coincide exacto con lo medido
(3.659 archivos, 4,93 GB), 0 fallos.

**Borrado real ejecutado (2026-09-28), con confirmación explícita del
usuario**: mismo payload con `dry_run: false` → `{"deleted": 3659,
"failed": 0, "freed_bytes": 4925918329, "errors": []}`, idéntico al
dry-run. Verificado: `discard_to_trash()` (`utils/trash.py:29`) mueve cada
archivo a una carpeta `_descartados/` **hermana** (junto a su propio
padre, no un único directorio en la raíz) — soft-discard, deshacible
~30 días (`library.trash_purge_days`, `purge_trash()`). 4,93 GB
liberados de `safe_delete`. Quedan `misplaced` (2.176 archivos/13,87 GB,
mover con el motor de `ZIP-ROUTE-1`/`-3`) y `review` (237/16,18 GB) sin
tocar — ver arriba.

**`misplaced` aplicado (2026-09-28), con confirmación explícita del
usuario**: el mecanismo real disponible no es `ZIP-ROUTE`/`zip-route-apply`
(eso es solo arcade + colecciones) sino el `plan`/`apply` general de la app
(`GET /api/plan` → `POST /api/apply`) — bastante más amplio de lo
documentado arriba: **13.298 juegos matched en total** (no solo los 2.176
de `Unknown\`), de los cuales **1.555 "pending"** (movibles solos, sin
ambigüedad) y **4.119 "conflicts"** (mismo destino propuesto por 2+
orígenes, o destino ya ocupado con contenido distinto — `_do_apply()`,
`web/handlers/organize.py:124`, **nunca los toca**, solo procesa
`plan.pending`). Decisión del usuario: aplicar solo lo sin conflicto.
`POST /api/apply` real (con backup automático de `library_pc.db` antes de
tocar nada, `apply_repo.backup_database()`) → `{"renamed": 1554, "failed":
0, "skipped": 1, "saves_renamed": 8, "zips_extracted": 1, "conflicts":
4119}`. El único `skipped` fue una fila de BD obsoleta (`Digimon World 3
[U] [SLUS-01436].sub`, el archivo de origen ya no existe en disco — no es
un fallo real). Reversible vía `POST /api/undo-last-apply` si hiciera
falta. **Los 4.119 conflictos siguen sin resolver** — requieren revisión
caso a caso (mismo destino propuesto por 2+ orígenes o colisión con
contenido distinto), no automatizable con este mecanismo.

**`review` — intentado con `zip-route-apply`, real y verificado contra un
segundo junk-scan (2026-09-28), con confirmación explícita del usuario**:
`POST /api/zip-route-apply` (job "inbox", extract→match→renombrar→
organizar→limpiar) → `{"zips_to_inbox": 2172, "roms_scanned": 4341,
"matched": 3980, "renamed": 1136, "organized": 3301,
"duplicates_removed": 1036, "conflicts_unresolved": 4}`. Solo 2
`route_skipped` (`Hook.zip`/`Tetris.zip`, ya existían en `arcade\`, no
sobreescritos) y 4 `organize_errors` reales (mismo nombre/carpeta,
contenido distinto — intactos, revisar a mano: `Pokemon - Emerald Version
(USA, Europe).gba`, `Premier Manager 97 (Europe).bin`, `Snow Bros. - Nick &
Tom (Japan).bin`, `Twinkle Tale (Japan).bin`).

**Efecto real, medido con un junk-scan de después contra el de antes**:

| Bucket | Antes | Después | |
|---|---|---|---|
| `safe_delete` | 3.659 / 4,93 GB | 3.699 / 4,95 GB | +40 archivos nuevos (residuos expuestos por las extracciones) |
| `misplaced` | 2.176 / 13,87 GB | 1.650 / 10,52 GB | -526, organizados entre `apply` + `zip-route-apply` |
| `review` | 237 / 16,18 GB | **237 / 16,18 GB — exactamente igual** | confirma que estos 237 no eran resolubles por CRC/contenido con el catálogo ya cargado, la hipótesis original de "candidato a ZIP-ROUTE-1" no se sostuvo con datos reales |

**Total: 6.072/34,97 GB → 5.586/31,65 GB.**

**Segunda ronda de `safe_delete` aplicada (2026-09-28), con confirmación
explícita del usuario**: los 3.699 `safe_delete` de después de
`zip-route-apply` (incluye los 40 nuevos expuestos por las extracciones) —
dry-run (`{"deleted": 3699, "failed": 0, "freed_bytes": 4949875483}`) seguido
del borrado real, idéntico (`dry_run: false`), 0 fallos. **4,95 GB
adicionales liberados** (soft-discard, mismo mecanismo que la primera
ronda). **Total acumulado de `safe_delete` borrado hoy: 7.358 archivos,
~9,88 GB.**

**`review` investigado a mano (2026-09-28), 2 hallazgos reales antes de
llegar a los archivos en sí:**

1. **Bug real en el propio junk-scan: no excluye `_descartados/`**
   (`web/builders/folders.py:321`, `_excluded_dirs = {"saves", "bios",
   "android", "system volume information"}` — falta `_descartados`).
   `utils/trash.py` sí se protege contra esto (`_iter_trash_files()`, línea
   65-66, corta el `os.walk` con el comentario `# no anidar` en cuanto entra
   en una carpeta `_descartados`), pero esa misma protección nunca se aplicó
   al walker del junk-scan. Consecuencia real, verificada: **94 de los 120
   "ZIPs no-ROM" ya estaban dentro de alguna `_descartados/`** (descartados
   en sesiones anteriores), re-contados como basura activa en cada scan —
   por eso el bucket `review` salió "exactamente igual" antes/después de
   `zip-route-apply`, nada de eso era realmente tocable. Peor: repetir
   `junk-delete`/extracciones sobre contenido ya descartado crea
   `_descartados/_descartados/` anidado (**111 carpetas así confirmadas
   hoy en la biblioteca real**) — esos archivos quedan **invisibles para
   `purge_trash()`** (mismo corte de `os.walk` que los protege de
   re-listarse también les impide ser vistos si están un nivel más
   adentro), huérfanos para siempre sin limpiarse solos. Sin pérdida de
   datos (nada se borra de verdad), pero desperdicia espacio en disco.
   Recuento real filtrando `_descartados/` de las 4 categorías: **142
   archivos activos de verdad, no 237** (26 ZIPs no-ROM activos, 8
   7-Zips, 108 chips arcade, 0 del set arcade "otra versión" — ese único
   ítem también estaba ya en `_descartados`). Sin arreglar el walker
   todavía — documentado, candidato a tarea propia (`JUNK-SCAN-EXCLUDE-TRASH-1`
   o similar).
2. **Causa raíz real de por qué las 26 ZIPs Dreamcast activas nunca
   matcheaban**: no eran basura sin catalogar — **el catálogo entero de
   Dreamcast cargaba 0 entradas** por un bug de BOM en
   `_detect_dat_format()` (`catalog/catalog_loader.py:22-28`): abría con
   `encoding="utf-8"`, un BOM inicial (común en exports de Redump) quedaba
   pegado a `<?xml`, así que `startswith("<")` daba `False` y el DAT XML
   real se clasificaba como clrmamepro, sin ningún error visible. Afectaba
   a **9 catálogos reales** (18 archivos, `nointro/`+`redump/`): Dreamcast
   (1.420 juegos), Naomi, Naomi 2, Triforce, PC (SBI Subchannels), Wii U
   (Disc Keys), PlayStation (SBI Subchannels), PlayStation 3 (Disc Keys
   ×2) — **arreglado y mergeado hoy** (`fix/catalog-bom-detection`,
   `encoding="utf-8-sig"`, test `test_detects_xml_with_leading_bom`, 9
   catálogos verificados con entradas reales tras el fix).

   **Re-aplicado contra la biblioteca real (2026-09-28), con confirmación
   explícita del usuario**: `rommgr serve` reiniciado (parado el proceso
   viejo, `python -m rom_manager serve` de nuevo — necesario para cargar
   el código nuevo) y `POST /api/match` real sobre los 11.532 juegos sin
   resolver → `{"total": 11532, "matched_high": 0, "matched_low": 2,
   "unmatched": 11530}`. **Confirmado con datos reales**: `Jet Set Radio
   (Europe).zip` (una de las ZIPs Dreamcast activas del bucket "review")
   pasó de `canonical_title=NULL` a `canonical_title="Jet Set Radio
   (Europe)"`, `match_confidence="medium"` — el catálogo Dreamcast
   arreglado sí funciona en producción. Rendimiento modesto en esta pasada
   (solo 2 matches nuevos de 11.532): la mayoría de la cola restante
   parece genuinamente difícil de identificar (hacks, dumps no estándar,
   sin equivalente en ningún DAT) — sesiones anteriores ya habían agotado
   los matches fáciles antes de que este catálogo existiera de verdad, así
   que el fix no iba a desbloquear miles de golpe, pero sí corrige la
   identificación de cualquier contenido Dreamcast/Naomi/Naomi2/Triforce
   futuro de forma permanente. `SAGE-1` relanzado tras el `match` (cola
   17.634→16.937→15.681, sin errores).

`review` recontado sin `_descartados/`: **142 archivos reales (~15,1 GB)**
de los cuales una parte desconocida (Dreamcast + arcade Naomi/Naomi2/
Triforce) probablemente se resuelva sola en el próximo `match` con el
catálogo ya arreglado. Los 8 `.7z` siguen siendo el único hueco confirmado
sin solución disponible (formato no soportado) — **actualizado**, ver
`JUNK-7Z-SUPPORT-1`.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| JUNK-7Z-SUPPORT-1 | **Soporte `.7z` en el Inbox** — `converters/zip_extractor.py` solo importa `zipfile` (stdlib), cero soporte de `.7z`; sin `7z*.exe` en `tools/` | `src/rom_manager/converters/sevenzip_extractor.py` (nuevo), `config.py` (campo `sevenzip`, mismo patrón `_default_tool`/`_resolve_tool_path` que `chdman`/`adb`), `web/inbox_pipeline.py` (`_run_inbox_pipeline`, extracción junto a los `.zip`), `cli.py` (`rommgr decompress` extrae también `.7z`), `scripts/download-tools.ps1` (descarga 7-Zip desde GitHub `ip7z/7zip`, extrae el `.msi` con `msiexec /a` sin necesitar 7z para desempaquetarlo — sin huevo-o-gallina) | ✅ implementado 2026-09-29 — `extract_7z()`/`find_7z_files()`/`list_7z_members()` (parseo de `7z l -slt`), mismas garantías que `extract_zip()`: nunca sobreescribe (`-aos`), solo borra el origen si todos los miembros quedan confirmados en disco. **Mismo guard de sets multi-disco que `extract_zip()`** (`.cue`/`.gdi` entre los miembros → skip, "usa el conversor CHD") — añadido tras verificar contra los archivos reales de esta biblioteca (ver abajo), no estaba en la primera versión. 10 tests (`tests/test_sevenzip_extractor.py`, contra el `7z.exe` real de `tools/`, skip si no está presente). Suite completa 1469/1469, ruff+format limpios. **Sin arcade-CRC-detection para `.7z`** (a diferencia de `is_arcade_zip_container` para ZIP) — solo el guard por nombre de carpeta, documentado como límite conocido |

**Aplicado contra la biblioteca real (2026-09-29), con confirmación explícita del usuario** — primero un dry-run de `rommgr decompress "F:\Juegos Retro"` para localizar los `.7z` reales (13 en total, no solo 8: 8 en `Unknown\` + **5 en `PlayStation 2\`**, estos últimos ya colocados en su carpeta correcta con nombre canónico, nunca contados por el junk-scan porque no son "review" — simplemente nadie los había extraído). Inspeccionado el contenido de cada uno con `7z l -slt` antes de tocar nada: **9 de los 13 son sets Dreamcast/Naomi multi-track** (`.gdi` + varios `.bin` de audio/datos) — `Crazy Taxi`, `Jet Set Radio`, `Marvel vs. Capcom`, `Mortal Kombat Gold`, `Resident Evil - Code Veronica (Disc 1)`, `Sonic Adventure` (Europe/USA), `Sonic Adventure 2`, `Street Fighter III - 3rd Strike` — el guard nuevo los saltó correctamente a los 9, tal cual se diseñó. **4 son `.7z` de un solo `.iso` de PS2** (`Dragon Ball Z - Budokai 3`, `Kingdom Hearts`, `Kingdom Hearts II`, `Metal Gear Solid 2`) — aplicados de verdad (`extract_7z_directory(..., delete_source=True)`, script de sesión acotado a `Unknown\`+`PlayStation 2\`, sin tocar el resto de la biblioteca ni los `.zip`): 3 resultaron ser contenedores completamente redundantes (el `.iso` ya existía en disco, subido por separado el 2026-09-15) — soft-discard a `_descartados/`, cero archivos nuevos; 1 (`Dragon Ball Z - Budokai 3`) extrajo un `.iso` nuevo y distinto del ya existente (`Dragon Ball Z - Budokai 3 (USA).iso`, 4,66 GB — la copia previa era "(Greatest Hits)", posible duplicado real a revisar con `DUP-REGION-2`/matcher, sin decidir todavía) antes de descartar el `.7z`. Los 9 sets Dreamcast/Naomi restantes se retoman a continuación en `GDI-ORGANIZE-1` — **corrección**: no hace falta `chdman`/CHD para ellos, el `.gdi`+`.bin` crudo ya es un formato de primera clase en este pipeline (`move_disc_set_to_subfolder`, `_DISC_SUBFOLDER_PLATFORMS`, RA hash vía `ra_hash_saturn_dreamcast.py`) — CHD es opcional (ahorro de espacio), no un requisito |

### GDI-ORGANIZE-1 — Organizar los 9 sets Dreamcast/Naomi extraídos: 2 bugs reales encontrados antes de poder mover nada (2026-09-29, continuación de `JUNK-7Z-SUPPORT-1`)

Tras extraer los 9 `.7z` Dreamcast/Naomi, `GET /api/plan` reveló dos bugs reales, ninguno introducido hoy:

1. **`operation_planner.build_plan()` calcula mal el destino para una plataforma "subfolder" (PSX/Saturn/Dreamcast/Wii) cuando el origen vive fuera de cualquier carpeta de plataforma** (`planner/operation_planner.py:195-201`, `_DISC_SUBFOLDER_PLATFORMS`/`_DISC_SUBFOLDER_CATALOG_PLATFORMS`): la rama `else` (`source.parent.parent / folder_name / new_filename`) asume que el origen ya vive *dentro* de la carpeta de plataforma (p. ej. corrigiendo un subcarpeta-por-juego mal hecho) — para un archivo suelto en `Unknown\`, `source.parent.parent` es la **raíz de la biblioteca**, no `dreamcast\`. Verificado contra la API real: los 8 títulos Dreamcast matched (7 en `Unknown\` + 1 en `PlayStation 2\`) proponían todos mover a `F:\Juegos Retro\<Título>\` en vez de `F:\Juegos Retro\dreamcast\<Título>\` — incluido un título Dreamcast preexistente no tocado por mí (`Skies of Arcadia (Europe)...(Disc 2).zip`), confirmando que no es un caso aislado de hoy. **Sin arreglar** — toca lógica compartida por las 4 plataformas subfolder, no es un fix para hacer con prisa; candidato a su propia rama con tests dedicados. Mientras tanto, cualquier `apply` sobre contenido recién llegado a estas 4 plataformas (vía Inbox parcial, extracción manual, etc.) debe revisarse a mano antes de confirmar — no fiarse del `target` que devuelve `/api/plan` para estos casos.
2. **`parse_tracks_from_gdi()` (`converters/chd_converter.py:237`) no soportaba nombres de pista entre comillas con espacios** — el formato real de un `.gdi` (`4 0 4 2352 "Crazy Taxi (USA) (Track 4).bin" 0`) casi siempre cita el nombre porque casi siempre tiene espacios; `line.split()` cortaba en el primer espacio (`'"Crazy'`), truncando la ruta real. Usada también por `renamer/file_renamer.py` (`move_disc_set_to_subfolder`, el mecanismo real de mover/renombrar sets Dreamcast) y `retroachievements/ra_hash_saturn_dreamcast.py` — sin ningún test hasta hoy (`tests/test_chd_converter.py` no tenía ni un caso de `.gdi`). **✅ arreglado** — regex que prioriza el nombre citado, con fallback al `split()` original para el formato sin comillas; 2 tests nuevos (`test_parse_tracks_from_gdi_quoted_filenames_with_spaces`, `..._unquoted_filename_fallback`). Suite completa 1472/1472 en verde.

**Aplicado contra la biblioteca real tras el fix del punto 2** (bug 1 evitado a mano, moviendo directamente por script de sesión en vez de vía `/api/apply`, con el mismo destino que un planner correcto habría calculado): **6 de los 9 movidos limpio** a `dreamcast\<Título>\` (`Crazy Taxi (USA)`, `Marvel vs. Capcom - Clash of Super Heroes (USA)`, `Resident Evil - Code - Veronica (USA) (Disc 1)`, `Sonic Adventure (USA) (En,Ja,Fr,De,Es)`, `Sonic Adventure 2 (Europe) (En,Ja,Fr,De,Es)`, `Street Fighter III - 3rd Strike - Fight for the Future (Japan)`). **3 sin resolver, dejados aparte a propósito**:
   - `Jet Set Radio (Europe).7z` — nunca extraído (ver `JUNK-7Z-SUPPORT-1`): tiene un `.zip` hermano con el mismo contenido exacto (mismos 3 tracks, sheet `.cue` en vez de `.gdi`) — duplicado real, decisión pendiente (cuál sheet conservar).
   - `Sonic Adventure (Europe) (En,Ja,Fr,De,Es).gdi` — extraído pero **no movido**: `dreamcast\Sonic Adventure (Europe) (En,Ja,Fr,De,Es)\` ya tiene un `.cdi` completo del mismo juego (formato distinto, mismo contenido presumible, sin verificar por hash) — duplicado real, sigue en `Unknown\`, decisión pendiente.
   - `Mortal Kombat Gold (USA).gdi` (53 tracks) — **sin match**, `match_confidence`/`canonical_title` siguen `NULL` (`unmatched_reason: hash_not_found` para las 54 filas, sheet + tracks) — causa no investigada todavía, candidato a revisar aparte (¿el catálogo Dreamcast no tiene esta entrada, o algo en el matcher falla con sets de tantas pistas?).

**Los 6 sets movidos, enviados a la Anbernic real por ADB (2026-09-29)** — `POST /api/cable-sync` (`direction=send_selected`, `search=<título exacto>`, uno a uno; verificado antes con un dry-run que el filtro no arrastraba ningún otro juego). 24 archivos, ~7,2 GB, 0 errores, verificado con `adb shell ls` en el dispositivo. **Gotcha real de la sesión, no del código**: pasar el cuerpo JSON con rutas Windows (`F:\Juegos Retro`) vía `curl -d '...'` inline falla silenciosamente en este entorno (Git Bash/curl en Windows) — cualquier backslash en el valor hace que el body llegue corrupto y el servidor lo interpreta como `{}` (así que `direction` cae a su default y el error engañoso "anbernic_path requerido" aparece aunque se haya mandado). Solución: escribir el JSON a un archivo y usar `curl --data-binary @archivo`. Dejar esto anotado para la próxima vez que alguien llame a esta API a mano desde esta máquina.

### GDI-ORGANIZE-1 (continuación) — `/api/review-queue` no responde en tiempo razonable contra la biblioteca real de hoy (hallazgo 2026-09-29)

Al intentar relanzar la limpieza de duplicados de la Anbernic (petición del usuario, pendiente de una sesión anterior sin cerrar) — 3 intentos reales de `GET /api/review-queue` (sin parámetro `repo=`, pese a que la UI antigua lo sugería: el endpoint siempre construye la cola contra `repository` PC + `repo_android` juntos, `web/handlers/duplicates.py:165`, `_build_review_queue`) **no devolvieron respuesta**: dos con timeout explícito de 60s/90s (`curl --max-time`, error 28 = timeout, no error de conexión), uno en background que tardó ~35 min y solo terminó porque maté el proceso `curl` a mano. Descartado que fuera el job `ra_check` (llevaba corriendo en paralelo, cancelado a mitad de la investigación) — el hang persistió igual después de pararlo. La CPU del proceso del servidor no se pudo comparar en dos instantes de forma concluyente (medición de sesión insuficiente, no una prueba real).

**Hipótesis más probable, sin confirmar todavía**: no necesariamente un cuelgue real — `_review_groups_for_repo`/`_build_review_queue` (`web/builders/duplicates.py`) construye varias uniones (crossfmt/sha1/región/disc_hash) sobre el PC + Android combinados; el PC pasó hoy de su tamaño habitual a **27.874 ROMs / 11.510+ ya-correctos** tras el rescan de esta sesión — si alguna de esas uniones es O(n²) o peor sobre el título normalizado, a esta escala podría tardar decenas de minutos de verdad, no estar bloqueado. Sin perfilar, así que sigue siendo hipótesis. Cualquiera que sea la causa, **un endpoint de UI que no contesta en 35+ minutos es un problema real de UX/rendimiento** para una biblioteca de este tamaño, no solo un contratiempo de esta sesión.

**✅ Causa raíz real encontrada y arreglada (2026-09-29, misma sesión, retomada tras el mensaje del usuario "no, ahora")**: perfilado `_review_groups_for_repo` directamente (sin HTTP, `cProfile` contra la BD PC real) — 245 s para el repo PC solo, nada patológico algorítmicamente (nada de O(n²) real). El verdadero bloqueo: **`ra_disc_hash_cache.get_psx_disc_hash()` encontró `psx_disc_hashes.json` corrupta** (`json.decoder.JSONDecodeError` real en el log) — con la caché ilegible, cada comparación de hash de disco PSX/GameCube/Wii recalculaba de cero vía `chdman` (~16,6 s cada extracción de `.chd` real, 6 de esas en el perfil = 100 s solo ahí) en vez de una lectura de caché instantánea.

**Causa de la corrupción, confirmada por el patrón temporal**: `_save()` (`retroachievements/ra_disc_hash_cache.py:44`) escribía con `Path.write_text()` directo, **no atómico** — el job `ra_check` (corriendo en paralelo toda la sesión) y mis propios intentos de `review-queue` escriben/leen el mismo archivo sin ningún lock; dos escrituras solapadas dejan un JSON a medio escribir. Mismo patrón de riesgo que `JOBS-SQLITE-LOCK-1` pero para un archivo JSON en vez de SQLite. **✅ arreglado**: `_save()` ahora escribe a un temporal y usa `os.replace()` (atómico en POSIX y Windows) — un lector nunca puede ver un archivo a medias. 4 tests nuevos (`tests/test_ra_disc_hash_cache.py`). Suite completa 1476/1476 en verde.

**Verificado en real tras el fix**: `GET /api/review-queue` real (con la caché ya regenerada, 1256 entradas válidas) → **200 OK en 28,7 segundos** (antes: sin respuesta en 3 intentos, uno de 35 min matado a mano). Sigue habiendo un coste real no-patológico de ~113 s (en el perfil PC-solo) en `extract_internal_id` (`MATCH-HEADER-1`, abre cada archivo `.nds`/`.gba` real de la biblioteca para leer su código interno) — candidato a cachear igual que los hashes de disco si se quiere bajar más, pero no bloqueante, sin tocar hoy.

**Resultado del pedido original (dedup PSX tipo "Final Fantasy VII, quedarse con la copia con logros")**: revisada la cola real (7.745 grupos, 55,46 GB desperdiciados combinando PC+Anbernic) — **no hay ningún grupo "Final Fantasy VII" de PSX pendiente** en `review-queue` (solo un romhack de NES con ese nombre, 2 copias, y un par no relacionado de **Final Fantasy VIII** PSX — `Final Fantasy VIII (Europe).chd` vs `(USA) (Disc 1).chd`, sha1 idéntico, 468 MB desperdiciados, **ninguna de las dos marca soporte RA** en la cola — no hay copia "con logros" que preferir en este par tal cual está hoy).

**El usuario aclaró: se refería a la Anbernic directamente, no a la cola de duplicados** — tiene sentido, `_review_groups_for_repo` **excluye a propósito** las variantes regionales PSX multi-disco de la unión difusa por región (comentario en `web/builders/duplicates.py:1019-1037`, el propio ejemplo documentado ahí es "18 discos reales de Final Fantasy VII fusionados por error" — la razón exacta por la que este caso es invisible para la herramienta). Revisado `psx/` en la Anbernic real por ADB — **más lío del recordado, no "3 copias" limpias**:

- `Final Fantasy VII (Disc 1/2/3).bin/.cue` — sin etiqueta de región, dump propio (tamaños ligeramente distintos a los demás).
- `Final Fantasy VII (Europe).cue` + `(2).cue` + `(3).cue` — **rotos**: apuntan a `"...(Spain)...(v1.1).bin"`, pero el `.bin` real se llama `(Rev 1).bin` — no coincide el nombre, nunca cargarían. No son una copia real, son sheets basura.
- `Final Fantasy VII (Spain) (Disc 1/2/3) (Rev 1).bin` — sin ningún `.cue` válido que los referencie (solo los rotos de arriba los mencionaban).
- `Final Fantasy VII (USA) (Disc 1/2/3)` — tiene **tanto** `.bin`+`.cue` crudo **como** `.chd` ya convertido (fecha posterior) — ~2 GB de crudo redundante con su propio `.chd`, sin limpiar tras la conversión.
- `Final Fantasy VII (USA) (Install Disc) (Rerelease).chd` — disco de instalación PC aparte, no es el juego.

**Aplicado, con confirmación explícita del usuario (2026-09-29)**: borrados por ADB los 3 `.cue` rotos de "Europe" (`rm` directo — Android no tiene papelera, irreversible, pero eran sheets sin ningún `.bin` real al que apuntar, cero riesgo de contenido jugable). Verificado que ya no están en el dispositivo.

**Crudo USA vs `.chd` — verificado y resuelto**: descargados los 3 discos completos (`.bin`+`.cue`+`.chd`, ~3,4 GB) a esta máquina para verificar antes de borrar nada, mismo patrón que `CHD-DELETE-NO-VERIFY-1`/`convert_to_chd(delete_source=True)` ya usa: `chdman verify` (integridad del `.chd`) + comparar el hash RA (`compute_psx_ra_hash`) del `.cue`/`.bin` crudo contra el del `.chd`. **Los 3 discos verifican perfecto** — `chdman verify: ok=True` e ídem hash RA exacto en los 3 (`665933b4...`/`22e74595...`/`f0bab449...`, origen y `.chd` coinciden byte a byte en contenido jugable). Borrados por ADB los 6 archivos crudos (`.bin`+`.cue` × 3 discos) de la Anbernic — confirmado que solo quedan los `.chd` ya verificados. **~2 GB liberados**, cero riesgo (contenido confirmado idéntico antes de borrar).

**Spain y el dump sin etiqueta — investigado y resuelto**: descargados los 6 `.bin` restantes (~4,3 GB) y comparado el hash RA de cada uno (`compute_psx_ra_hash`) contra el hash USA ya confirmado — **los 3 dumps (USA/Spain/sin etiqueta) tienen hash distinto entre sí en los 3 discos**: no son duplicados byte-a-byte del mismo contenido, son ediciones/revisiones genuinamente distintas (Spain casi seguro la edición europea traducida; el dump sin etiqueta no coincide con ninguno de los otros dos, identidad exacta sin determinar). Con confirmación explícita del usuario ("el que juego es el de USA, porque tiene logros" — no necesita las otras ediciones), **borrados por ADB los 6 archivos** (3 `.bin` de Spain + 3 `.bin`/`.cue` sin etiqueta). Verificado: solo quedan los 3 `.chd` de USA + el install disc. `psx/Final Fantasy VII` queda limpio del todo — de 4 ediciones + 3 sheets rotos a solo la USA verificada.

**Además, mientras se investigaba**: resueltos los 2 duplicados Dreamcast que había dejado pendientes arriba (`Jet Set Radio` y `Sonic Adventure (Europe)`) — verificado por SHA1 que las 3 pistas de `Jet Set Radio` (`.gdi` del `.7z` vs `.cue` del `.zip`) son **byte a byte idénticas**; sin diferencia real de contenido, se conserva el `.gdi` (formato que este proyecto sí soporta de fondo para organizar/renombrar/hashear Dreamcast — el soporte `.cue` coge el track 1, no el de datos, ver `ra_hash_saturn_dreamcast.py:154` `_first_cue_bin`). `.zip`/`.cdi` descartados a `_descartados/`, `.gdi` movido a `dreamcast\<Título>\` y enviado a la Anbernic (mismo mecanismo `send_selected` que los otros 6, 4 archivos cada uno, 0 errores).

**Hallazgo colateral verificando esto**: `_CdImage._detect_geometry()` (`retroachievements/ra_cd_image.py:44-69`) calcula mal `header_size` para un sector MODE1 de 2352 bytes cuando cae en su rama de respaldo por módulo exacto (línea 61-62: `if size % 2352 == 0: return 2352, 24, 0` — `24` es el header de MODE2 FORM1, un MODE1 real necesita `16`). Confirmado con el `.bin` de track 3 real de `Jet Set Radio`: el magic `"SEGA SEGAKATANA "` vive en el byte 16 exacto (sync 12 + header 4), pero con `header_size=24` la lectura cae 8 bytes tarde y el hash de logros de Dreamcast devuelve `None` incluso para un dump limpio y completo. Afecta potencialmente a cualquier dump MODE1 de PSX/Saturn/Dreamcast que no tenga un PVD ISO9660 detectable en el sector 16 (la ruta de detección primaria). **Arreglado 2026-10-02** (rama `fix/ra-cd-image-mode1-short-track`): el fallback ahora relee el sector 0 (garantizado si `size>0`) y mira el byte de modo real del header (offset 15, justo tras sync+MSF) en vez de asumir siempre `header_size=24`; si no hay patrón de sync ni en sector 16 ni en sector 0, mantiene el default antiguo (24) por no tener ninguna evidencia positiva de MODE1. 3 tests nuevos (`tests/test_ra_cd_image.py`): MODE1 corto detecta 16, MODE2 corto detecta 24, imagen sin evidencia mantiene el default. Suite PSX/Saturn/Dreamcast completa en verde (19 pass).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| GDI-ORGANIZE-1 | Ver descripción arriba | `planner/operation_planner.py:195-201` (bug 1), `converters/chd_converter.py:237-268` (bug 2) | ✅ **ambos bugs arreglados** — bug 2 el mismo día; bug 1 arreglado 2026-09-29 (PR #377, rama `fix/gdi-organize-1-subfolder-platform-target`): `build_plan()` acepta `library_root: Path \| None = None` (retrocompatible), con él calcula el destino de una plataforma subfolder directo como `library_root/<slug>/<carpeta>/<archivo>` en vez de adivinar por `source.parent`/`source.parent.parent` — conectado en los 7 puntos de llamada reales (`cli.py` plan/apply, `web/builders/library.py::_build_plan`, `web/handlers/organize.py::_do_apply`, `web/inbox_pipeline.py` ×2, `services/ra_duplicates_service.py`, `web/builders/duplicates.py`). 4 tests nuevos, suite 1488/1488. Jet Set Radio y Sonic Adventure Europe ya resueltos el mismo día (ver arriba); solo queda `Mortal Kombat Gold` sin match (causa no investigada) |
| CHD-CLEANUP-1 | Generalizar la limpieza de FFVII: 195 títulos PSX reales en la Anbernic con `.chd` convertido y su `.bin`/`.cue` crudo sin borrar tras la conversión | `converters/chd_cleanup.py` (nuevo), `cli.py` (`rommgr clean-redundant-chd <ruta-android> [--apply]`) | ✅ **implementado y aplicado 2026-09-29** (PR #376, mergeado en `feature/junk-7z-support-1`) — agrupa por (directorio, stem exacto) `.cue`+`.chd`, verifica `chdman verify` + hash RA del crudo contra el `.chd` antes de borrar nada; deliberadamente NO cruza ediciones/regiones distintas (decisión humana aparte). 2 bugs reales corregidos tras review de Claude en el PR (extracción truncada de `.7z` tratada como completa + charset no-ASCII en `sevenzip_extractor.py`, ver `JUNK-7Z-SUPPORT-1`). Ejecutado real contra `psx/` en la Anbernic (RG556006101273): 19 candidatos encontrados, **17 verificados y borrados (11,49 GB liberados, 0 errores)**, 2 saltados de forma segura sin tocar nada (`Lunar - Silver Star Story Complete (USA) (Disc 2)` y `Guilty Gear (Europe)`: sus `.cue` referencian un `(Track N).bin` que no existe en el dispositivo — sheets rotas, mismo patrón que las de FFVII). Verificado en el dispositivo real por ADB que solo quedan los `.chd`. Quedan ~176 títulos sin auditar del total de 195 (el resto de la biblioteca Android, no solo `psx/` explorado hoy) — candidato a repetir contra el resto de carpetas/plataformas en otra sesión |
| ANDROID-DUP-GBA-1 | Petición del usuario: comprobar si la lógica de duplicados detecta bien los legacy `[E]`/`[U]`/`[J]` de GBA en la Anbernic (ejemplo dado: "dos Pokémon Pinball") | `web/builders/duplicates.py::_review_groups_for_repo` (motor, sin tocar), `services/ra_duplicates_service.py::resolve_duplicate_ra` (aplicado) | ✅ **verificado y aplicado 2026-09-29** — la lógica de detección funciona bien: de 92 volcados legacy `[E]`/`[U]`/`[J]` en `gba/`, **82 ya estaban correctamente agrupados por SHA1** en la cola de revisión (incluido el caso exacto de Pokémon Pinball — mismo SHA1 `b8b7881e...` entre `RZ [E].gba` y `(Europe)...gba`); los 10 restantes no son falsos negativos (contenido genuinamente distinto pese al mismo tamaño, o sin ninguna copia canónica en la biblioteca contra la que comparar — verificado caso a caso). **146 grupos GBA totales en la Anbernic, 1,65 GB** — backup de `library_android.db` antes de tocar nada, **137 grupos aplicados de verdad por ADB: 138 archivos descartados, 0 errores, 1,53 GB liberados**, verificado en el dispositivo real (`Pokemon Pinball RZ [E].gba` ya no existe, solo sus `.sav`/`.sgm`). **9 grupos excluidos a propósito** — ver `ANDROID-DUP-SORT-TIEBREAK-1` abajo, el bug que los afecta |
| ANDROID-DUP-SORT-TIEBREAK-1 | Hallazgo real durante `ANDROID-DUP-GBA-1`, ampliado a petición del usuario a **todas las plataformas** de la Anbernic (2026-09-29): el desempate de "recomendado" en `_review_entry_sort_key` cae a comparar el nombre de archivo como texto plano cuando todos los criterios tipados empatan (caso normal en un duplicado SHA1 exacto) — un espacio (`0x20`) ordena antes que un punto (`0x2E`), así que cualquier sufijo entre paréntesis/corchetes ("... (Japan) [T-En...]", "... (USA) (conflicto-inbox...)") gana alfabéticamente al nombre limpio sin que eso tenga ningún sentido semántico | `web/builders/duplicates.py:313-410` (`_review_entry_sort_key`, nuevo `variant_tier`) | ✅ **arreglado 2026-09-29, a petición del usuario, misma sesión** — nuevo `variant_tier` insertado justo antes del fallback de nombre: reutiliza `is_non_canonical_variant()` (ya usada en otro sitio del código para el mismo tipo de señal, `[T+`/`[T-`/`(hack`/`subset`/`[h\d*]`) + un check aparte para `conflicto-inbox` (artefacto del Inbox, no relacionado con traducciones/hacks). Deliberadamente NO toca `(Beta)`/`(Proto)`/`(Demo)`/`(Sample)` — confirmado con datos reales que esas etiquetas describen contenido genuino. 4 tests nuevos (`tests/test_builders_duplicates.py`): 2 confirman que el sort key ahora penaliza los dos patrones reales encontrados, 1 confirma que `(Beta)`/`(Proto)` NO se penalizan, 1 end-to-end reproduciendo el caso real de Mother 3 a través de `_build_review_queue`. Suite completa 1492/1492, ruff+format limpios. Metodología (investigación original, antes del fix): recorrida la cola de revisión real completa (`_build_review_queue`) agrupada por plataforma, filtrado a grupos con SHA1 idéntico donde el "recomendado" lleva `[T-` o `conflicto-inbox` y existe una alternativa sin esa etiqueta en el mismo grupo — cada caso verificado por SHA1 real, no por sospecha. Un barrido más amplio con `(Beta)`/`(Proto)`/`(Demo)`/`(Sample)` dio **falsos positivos**: esas etiquetas sí describen el contenido real (mismo dump beta/proto, solo con nombre No-Intro correcto vs. un volcado legacy mal escrito) — descartadas del hallazgo, no es el mismo bug.<br>**GBA**: 6 parches `[T-...]` falsos (`Mother 3`, `Oriental Blue - Ao no Tengai`, `Magical Vacation`, `Dragon Quest Monsters - Caravan Heart`, `Super Robot Taisen R`, `Tomato Adventure`) + 3 `(conflicto-inbox 2026-08-13)` (`Boktai 2`, `Crash Nitro Kart`, `Klonoa - Empire of Dreams`) — de 146 grupos totales, excluidos de la aplicación real en `ANDROID-DUP-GBA-1`.<br>**NES**: 9 parches `[T-...]` falsos, mismo patrón exacto (SHA1 idéntico al original japonés sin traducir): `Big Strategy Pachinko`, `Mitsume ga Tooru`, `Perman`, `Sweet Home`, `Fire Emblem Gaiden`, `Brave Fighter of the Sun - Fighbird`, `Hinotori - Houou Hen`, `Famicom Wars`, `Family Trainer 8`.<br>**Game Gear**: 1 caso, `Sylvan Tale (Japan) [T-En by Aeon Genesis v1.01].gg` = mismo SHA1 que `Sylvan Tale (Japan).gg` sin traducir.<br>**Aplicado el resto (2026-09-29, mismo backup previo de `library_android.db`)**: filtro conservador (excluye cualquier grupo cuyo "recomendado" contenga `[T-`/`conflicto-inbox`, sin exigir que exista alternativa limpia — más estricto que el hallazgo exacto, así que excluyó 20 grupos en total en vez de los 10 confirmados, dejando también sin tocar algunos casos ambiguos tipo "dos parches distintos del mismo hack"). **NES: 1563/1582 grupos aplicados, 1865 filas borradas, 0,40 GB liberados. Game Gear: 183/184 grupos aplicados, 184 filas borradas, 0,07 GB liberados. 0 errores en ambos.** Verificado por dos vías: `ls` real en el dispositivo confirma que los 10 casos `[T-...]` originales siguen intactos (ambas copias), y el recuento de filas en `library_android.db` coincide exacto con lo aplicado (NES 4971→3106 = −1865, Game Gear 939→755 = −184).<br>**Resto de plataformas con datos en el dispositivo, sin ningún caso del bug** (0 sospechosos tras el mismo barrido): Game Boy Color (1268 grupos, 1,95 GB), PlayStation (124 grupos, 14,33 GB), Sega Mega Drive (65 grupos, 0,12 GB — los 2 casos `(Beta)`/`(Proto)` del barrido amplio son correctos, no bug), Game Boy (25 grupos, 0,01 GB), SNES (5 grupos), Nintendo 64DD (1 grupo). Arcade, Nintendo DS, Master System, PlayStation 2, Nintendo 64, PSP, Atari 2600, GameCube, PC Engine y Famicom Disk System no tienen ningún grupo de duplicados con entradas en el dispositivo ahora mismo.<br>**Aplicado tras el fix (2026-09-29, mismo backup previo de `library_android.db`)**: reconstruida la cola real con el `variant_tier` ya en producción — confirmado primero en seco que los 16 casos falsos ahora recomiendan el nombre limpio (`Mother 3 (Japan).gba`, `Sylvan Tale (Japan).gg`, etc.), sin exclusión manual esta vez (el propio motor ya elige bien). **29 grupos restantes en GBA/NES/Game Gear (los 20 previos + 9 nuevos que solo aparecieron al dejar de excluirlos a mano), 33 archivos descartados, 0 errores, 0,119 GB liberados** (GBA 0,114 GB, NES 0,005 GB, Game Gear 0,001 GB — números pequeños porque la mayoría de esos grupos son el propio archivo `[T-...]`/`conflicto-inbox` de 1 sola entrada extra, no discos completos). Verificado en el dispositivo real por ADB: `Mother 3 (Japan) [T-En...].gba` y `Sylvan Tale (Japan) [T-En...].gg` ya no existen, solo las copias limpias. Con esto, `ANDROID-DUP-GBA-1`/`ANDROID-DUP-SORT-TIEBREAK-1` quedan completamente cerrados para las 3 plataformas investigadas |

### ANDROID-DUP-PSX-1 — PlayStation en la Anbernic: verificación por pareja real de SHA1 antes de aplicar, no fiarse del `reasons` a nivel de grupo (hallazgo real 2026-09-29)

Al intentar repetir el mismo patrón GBA/NES/Game Gear contra PlayStation (124 grupos, 14,33 GB), **hallazgo real antes de tocar nada**: `_review_groups_for_repo` une por Union-Find — un grupo puede quedar contaminado con discos genuinamente distintos si comparten un `canonical_title`/nombre mal resuelto por el catálogo, aunque el `reasons` del grupo incluya `sha1`. Caso confirmado con datos reales: `Metal Gear Solid (World) (4B4E083C) (Addon).chd` existía en 3 ubicaciones con **3 SHA1 distintos** (raíz `psx/`, `Metal Gear Solid (Spain) (Disc 1) (v1.1)/`, `Metal Gear Solid (Spain) (Disc 2) (v1.1)/`) — 3 discos reales y distintos con el mismo nombre genérico sin identificar, agrupados como "duplicados" por título exacto. Aplicar `resolve_duplicate_ra` a nivel de grupo (como se hizo en GBA/NES) habría borrado los 2 discos españoles reales creyéndolos copias redundantes.

**Fix aplicado en esta sesión, sin tocar código** (verificación adicional en el script de aplicación, no en `_review_groups_for_repo`): en vez de confiar en `reasons`, comparar el SHA1 real de cada candidato a descartar contra el SHA1 del "recomendado" uno a uno — solo se descarta si coinciden exactamente. De **149 pares evaluados** (41 grupos con `sha1` en razones), **110 fueron rechazados por SHA1 distinto** (contenido genuinamente diferente pese a compartir grupo) y solo **39 verificados como duplicados reales**.

**Aplicado contra la Anbernic real** (backup previo de `library_android.db`): **37/38 grupos aplicados, 0 errores reales, 7,51 GB liberados**. El único grupo no resuelto (`Ninpuu Sentai Hurricanger...`) lo bloqueó el guard de seguridad ya existente (`DUP-CROSSFMT-6`) porque su "recomendado" (`Enemy Engaged - Apache-Havoc...`) ya no existe en el dispositivo — fila obsoleta, nada descartado, correcto. Verificado en el dispositivo real: `Metal Gear Solid (World)(Addon).chd` de la raíz (el único SHA1 realmente duplicado, coincide con `USA (Disc 1).chd`) desaparecido; los dos discos españoles siguen íntegros. Recuento de filas en BD coincide exacto (PlayStation 1580→1543, −37).

**Hallazgo colateral, no bloqueante**: los `.chd`/`.cue` de los 2 discos españoles siguen en `library_android.db` pero **ya no existen físicamente en el dispositivo** (`ls -la` real lo confirma) — filas fantasma de antes de esta sesión, no causadas por este apply (el filtro por pareja las excluyó correctamente al no compartir SHA1 con nada). Indica que `library_android.db` necesita un rescan ADB completo para depurar filas obsoletas — candidato a tarea propia, no urgente.

**Pendiente**: los **83 grupos PSX restantes con razón `crossfmt` únicamente** (4,58 GB, mismo hueco que `ANDROID-DUP-CROSSFMT-VERIFY-1` — agrupados por título normalizado sin ningún hash, `.chd` vs `.bin`/`.cue` del mismo disco en contenedores distintos) necesitan la verificación completa por hash RA de disco (`compute_psx_ra_hash`, descargando cada candidato vía ADB) antes de aplicar nada — mismo método ya usado el 2026-09-25 para los 53 pares `.chd`+`.bin` de esa tarea. No abordado en esta sesión por el volumen de datos a descargar.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ANDROID-DUP-PSX-1 | Verificación por pareja SHA1 antes de aplicar dedup en PSX/Anbernic | `services/ra_duplicates_service.py::resolve_duplicate_ra` (motor, sin tocar) | ✅ 37/38 grupos verificados y aplicados, 7,51 GB liberados, 0 errores reales. 83 grupos `crossfmt`-solo (4,58 GB) pendientes de verificación por hash RA real — ver `ANDROID-DUP-CROSSFMT-VERIFY-1` |

**Hallazgo colateral real: `SAGE-1` murió con `"database is locked"`**
mientras `zip-route-apply` corría en paralelo (ambos escriben en
`library_pc.db` — el pipeline de organizar hace escrituras masivas,
choque de concurrencia SQLite). Progreso real antes de morir: cobertura
de descripciones 27,78%→38,36% (no se perdió, quedó guardado). Relanzado
tras terminar el job pesado, corriendo limpio de nuevo. **Candidato a
backlog aparte** si se repite: serializar jobs de escritura pesada
(`scrape`/`apply`/`inbox`) en vez de permitirlos en paralelo, o que
`_do_scrape` reintente en vez de abortar ante `sqlite3.OperationalError:
database is locked`.

---

### HEALTH-CHECK-RUBEN-1 — El Health Check semanal marcó 2 "corrupted" que en realidad son falsos positivos: el `sha1` guardado en BD es el de otra variante regional, el archivo real está bien (hallazgo 2026-09-28, máquina "Ruben", `F:\Juegos Retro`)

Origen: el daemon de Health Check (semanal, `web/daemons.py`) ya estaba
corriendo al empezar esta sesión (no lanzado a propósito). Resultado real:
**24.527 OK, 0 missing, 2 "corrupted"**:

- `gbc/Mr. Driller (Japan).gbc` — `stored_sha1=3BFDA5EDB7D1...`, `computed_sha1=B0D725DACEA7...`
- `gbc/Ultimate Fighting Championship (Europe).gbc` — `stored_sha1=8A02015E399A...`, `computed_sha1=5036626B9723...`

`check_library_health()` (`utils/health_checker.py:201-223`) etiqueta
`"corrupted"` cualquier fila donde `computed_sha1 != stored_sha1` — no
distingue "el archivo está dañado de verdad" de "la BD tiene guardado el
hash equivocado". Investigado a fondo (solo lectura, sin tocar nada):

1. **El contenido real de ambos archivos está perfecto**, no corrupto. La
   cabecera interna del cartucho de `Mr. Driller (Japan).gbc` dice
   literalmente `"MR. DRILLERBMDJ"` (coincide con su propio nombre de
   archivo) y su `sha1` **real** (`B0D725DACEA7...`) coincide EXACTO con la
   entrada `"Mr. Driller (Japan)"` del DAT No-Intro real
   (`.rommgr/catalogs/nointro/Nintendo - Game Boy Color.dat`, cargado con
   `catalog_loader.load_dat_file()`, 1.427 entradas). Mismo patrón exacto
   para `Ultimate Fighting Championship (Europe).gbc` — su `sha1` real
   coincide con la entrada `"Ultimate Fighting Championship (Europe)"`.
2. **El `sha1` guardado en `games.sha1` para ambas filas no es basura
   aleatoria — es el `sha1` real de la variante "(USA)" del mismo juego**:
   `3BFDA5EDB7D1...` = `"Mr. Driller (USA)"` en el DAT; `8A02015E399A...` =
   `"Ultimate Fighting Championship (USA)"` en el DAT. Confirmado cruzando
   las 5 entradas del DAT para ambos títulos (JPN/USA/EUR) — no es una
   coincidencia, apunta a un bug real de asignación cruzada entre variantes
   regionales del mismo juego, no a corrupción de disco.
3. `file_operations` (BD) **no tiene ninguna fila para ninguno de los dos
   `game_id`** (43070, 43556) — lo que pasó no fue a través del pipeline de
   rename/organize de la app (que sí registra cada operación,
   `INBOX-ATOMIC-1`/regla del proyecto "Toda operación sobre archivos se
   registra en SQLite"). Causa raíz real **sin determinar** — candidatos sin
   confirmar: un bug de scanner/upsert que cruzó el `sha1` de dos filas
   cercanas al escribir, o un import/migración de datos anterior a esta
   sesión que ya traía el dato mal.
4. `canonical_title`/`match_confidence` son `NULL` en ambas filas pese a que
   el `sha1` guardado SÍ tiene match en el catálogo (la entrada "(USA)") —
   el matcher nunca llegó a correr sobre estas dos filas con ese hash, otra
   pista de que el dato llegó así desde fuera del flujo normal de
   scan→match.

**Conclusión**: no hay corrupción real ni riesgo de pérdida de datos — son
2 falsos positivos del Health Check. Sin arreglar a propósito (regla del
proyecto: documentar con archivo:línea, no implementar en la misma sesión
salvo petición explícita). Posible fix futuro de dos partes independientes:
(a) re-escanear/re-hashear estas 2 filas para que el `sha1` guardado
vuelva a ser el real (arregla el síntoma, dispara el match automático) y
(b) investigar si el bug de asignación cruzada es sistémico (otras filas
con el mismo patrón silenciosas porque su "sha1 equivocado" no dispara
"corrupted" por casualidad) — candidato a un chequeo tipo "¿el `sha1`
guardado coincide con OTRA entrada del catálogo bajo un título distinto al
propio `canonical_title`/nombre de archivo?" en vez de solo comparar
`computed == stored`.

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

### MATCH-FIX-3 — Descomprimir y rehashear no resuelve las colisiones de nombre cuando el catálogo tampoco conoce el hash real (hallazgo 2026-09-12)

Plan de implementación (junto a los follow-ups pendientes de `MATCH-HEADER-1`)
en `.claude/roadmaps/14-matcher-coverage-gaps.md`.

Origen: sesión 2026-09-12, máquina "Ruben" (`F:\Juegos Retro`) — el objetivo
era confirmar si los ~963 conflictos de `plan` en `.zip`/`.nes`/`.gb`/`.gbc`
(mismo problema de fondo que `MATCH-FIX-1`/`MATCH-FIX-2`: `_match_by_title()`
adivinando sin señal fuerte) se resolvían solos tras `decompress --apply`
(4.977 ZIPs descomprimidos) + `scan` completo (rehash real) + `match`. **No
se resolvieron**: tras el rehash real, `plan` sigue mostrando 1.276
conflictos, de los cuales 947 son la misma familia (`.zip` 696, `.nes` 141,
`.gbc` 57, `.gb` 53) — prácticamente igual que antes de descomprimir.
Verificado contra la BD real: de 12.897 juegos, 3.377 siguen en
`match_confidence='low'` y 3.789 sin `canonical_title`; `match` de hoy solo
resolvió 71 de 4.163 pendientes por SHA1. Causa raíz confirmada: la mayoría
de estos archivos no son solo "ZIP sin hashear" como se asumía — su SHA1
real (ya calculado) tampoco está en los catálogos No-Intro/Redump (hacks,
traducciones, romsets no oficiales), así que tener el hash correcto no
cambia nada: `_match_by_title()` (`catalog/matcher.py:233-262`) sigue
cayendo al fallback por título y sigue colisionando exactamente igual que
con el ZIP sin descomprimir. El cuello de botella es cobertura de catálogo,
no formato de archivo.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-FIX-3 | **✅ Decidido y hecho 2026-09-19** (roadmap 14, `fix/matcher-coverage-gaps`): el usuario eligió la opción conservadora — sin match si hay ambigüedad real, en vez de desambiguar por tamaño. `_match_by_title()` ya no devuelve `candidates[0]` a ciegas cuando, tras todo el filtro por plataforma/extensión/carpeta/serial, siguen quedando >1 candidatos y ningún número de disco los distingue — devuelve `None`. El caso donde el número de disco SÍ distingue (`GAMECUBE-DISC-BUG-1e`) sigue devolviendo el match real, sin cambios ahí. 3 tests existentes actualizados (`test_name_fallback_low_confidence_ambiguous`→`..._returns_none_when_genuinely_ambiguous`, `test_ambiguous_title_falls_back_to_first_hit_without_extension_signal`→`..._returns_none_without_extension_signal`, `test_ambiguous_extension_prefers_platform_of_containing_folder`) para reflejar el nuevo comportamiento — el caso con `source_path` real que sí desambigua por carpeta sigue devolviendo match, sin tocar. **✅ Medido en real 2026-09-19** contra `F:\Juegos Retro`/`library_pc.db` (backup previo en `.rommgr/db-backup/library_pc.20260919T203805Z.db`): `rommgr match` equivalente con `include_low_confidence=True`, 16.176 filas re-evaluadas (9.481 sin match + 6.695 con `low` viejo) en ~26 min (dominado por desambiguación PSX vía `chdman`, que descomprime el disco completo por candidato ambiguo). De las 6.695 `low`: **5.593 (83,5%) eran adivinanzas incorrectas**, ahora correctamente sin match; **1.102 (16,5%) sí estaban bien resueltas** por otra señal real, sin cambios. El total `unmatched` de esas 16.176 filas sube a 13.548 — no es regresión, es visibilidad real de un problema que ya existía oculto tras `match_confidence='low'` | `catalog/matcher.py` (`_match_by_title`) | ✅ política decidida, implementada y medida contra producción |

---

### MATCH-ZIP-HASH-1 — La mayoría de las "adivinanzas corregidas" de `MATCH-FIX-3` son en realidad ZIPs de consola sin descomprimir cuyo SHA1 nunca puede calzar con el catálogo (hallazgo 2026-09-19, durante la medición real de `MATCH-FIX-3`)

Origen: los ejemplos de la medición real de `MATCH-FIX-3` (arriba) eran
casi todos `.zip` de Game Boy con colisión de región (`(USA)` adivinado como
`(Europe)`/`(Japan)`). Primera hipótesis — "el catálogo No-Intro de Game Boy
tiene huecos de cobertura para dumps USA" — **descartada por evidencia
directa**: verificado que `Nintendo - Game Boy.dat` SÍ tiene una entrada
`"Addams Family, The (USA)"` real (SHA1 `8710CEECBE3E...`, 131.072 bytes).

**Causa raíz real, confirmada con hashes reales, no supuesta**: en la propia
biblioteca (`F:\Juegos Retro\gb\`) conviven `Addams Family, The (USA).gb`
(SHA1 `8710ceecbe3e...` — coincide exacto con el catálogo, `match_confidence
='high'`) y `Addams Family, The (USA).zip` (SHA1 almacenado
`4eb0e158519d...`, **completamente distinto**). Verificado abriendo el ZIP:
contiene un único `Addams Family, The (USA).gb` de 131.072 bytes cuyo SHA1
**es exactamente `8710ceecbe3e...`** — el mismo juego, byte a byte idéntico
al ya reconocido. El SHA1 guardado en la BD para el `.zip` es el hash del
**contenedor ZIP completo**, no del ROM que contiene —
`hashing/hash_calculator.py::calculate_hashes()` (línea 29-53) abre el
archivo y hashea sus bytes crudos sin ninguna conciencia de ZIP, a
diferencia del ruteo arcade (`load_arcade_crc_index()`, `ZIP-ROUTE`) que sí
lee el CRC32 de cada entrada sin descomprimir. Un ROM de consola guardado
sin descomprimir (viola la regla del Pilar 1 "ZIPs descomprimidos") **nunca
puede** matchear por SHA1 exacto contra el catálogo, sin importar lo
correcto que sea su contenido — antes caía al fallback por título y
adivinaba mal (el bug de `MATCH-FIX-3`); ahora, correctamente, no matchea
en absoluto — pero la respuesta *correcta* sería reconocerlo con
`confidence='high'` iguialmente, no dejarlo sin match.

**Alcance medido a escala completa (2026-09-19, script de solo lectura sobre
los 4.257 `.zip` sin match reales)**: abriendo cada ZIP y comparando el SHA1
de su único archivo interno contra el catálogo No-Intro/Redump ya cargado:

| Categoría | Filas | % |
|---|---|---|
| `catalog_match` — contenido interno coincide exacto con el catálogo | 3.245 | 76,2% |
| `no_match` — contenido genuinamente sin catalogar (hacks/homebrew/BIOS boot ROMs por nombre) | 682 | 16,0% |
| `multi_entry` — ZIP con >1 archivo (sets arcade, no el caso de este hallazgo) | 329 | 7,7% |
| `unreadable` (1 archivo corrupto/no-ZIP real) | 1 | ~0% |

**0 casos de "hermano ya reconocido"** — ninguno de estos `.zip` duplica el
contenido de un archivo ya descomprimido en la biblioteca; son copias
zip-only genuinas, no basura residual de una extracción a medias.

**Decisión del usuario (2026-09-19)**: los tres caminos NO son excluyentes,
uno por categoría:
1. **`catalog_match` (3.245, 76%) → descomprimir vía `rommgr decompress`**.
   **✅ ejecutado y cerrado 2026-09-20.** `rommgr decompress "F:\Juegos Retro"`
   (dry-run: 7.419 a descomprimir / 1.430 saltados arcade+multi-disco / 1
   fallido — `GBA ROMs Pack (Romspack.Com).zip`, ya conocido, no es un ZIP
   real). `--apply` (sin `--delete-source`): 7.419 descomprimidos, 0 nuevos
   errores. `rommgr scan "F:\Juegos Retro"`: 30.976 ROMs detectados, 0
   errores. Re-match (backup previo en `.rommgr/db-backup/`, sobre las
   15.613 filas sin match tras el scan): 1.798 nuevas filas
   `match_confidence='high'` + 131 medium/low. **Segunda pasada —
   `--delete-source`** (dry-run + `--apply`, ambos autorizados explícitamente
   por el usuario tras el bloqueo inicial del sandbox): movió los 7.419 ZIP
   ahora redundantes a sus `_descartados/` respectivos vía
   `discard_to_trash()` (verificado en disco: solo los ZIP de hoy, nada
   sobrescrito). `rommgr scan` final: **5.131 filas huérfanas podadas**
   (los `.zip` movidos ya no existen en su ruta original). **Resultado neto
   verificado en `library_pc.db` real**: total juegos 31.028 → 25.897 (solo
   limpieza de contenedores redundantes, ningún archivo real perdido); total
   sin match 13.685 → 9.749; `.zip` sin match 4.004 → **68** (quedan solo
   sets arcade/multi-disco genuinamente sin catalogar, no contenedores
   redundantes).
2. **`multi_entry` (329, 7,7%) → catálogo arcade desactualizado, no un hueco
   de cobertura real** — ver `MATCH-ARCADE-DAT-1` abajo. **✅ hecho y medido
   2026-09-19.**
3. **`no_match` (682, 16%) → fuera de esta tarea**, por diseño No-Intro/Redump
   no cubren hacks/homebrew/BIOS boot ROMs; el retorno de bajar un DAT
   adicional de "hacks" sería marginal. Sin implementar, sin decisión de
   revisitar todavía.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-ZIP-HASH-1 | Medir a escala + decidir los 3 caminos (arriba) | `hashing/hash_calculator.py:29-53` (`calculate_hashes`, sin conciencia de ZIP — sigue sin tocarse, la vía elegida fue descomprimir, no hashear-sin-descomprimir), `converters/zip_extractor.py` (`extract_zip`/`extract_directory`), `utils/trash.py` (`discard_to_trash`) | ✅ cerrado 2026-09-20. 2/3 caminos hechos y medidos en real (`MATCH-ARCADE-DAT-1` + descompresión/limpieza/rematch); 1/3 (`no_match`) descartado por bajo retorno. `.zip` sin match: 4.004 → 68 |

---

### MATCH-ARCADE-DAT-1 — `load_fbneo_dat()` nunca parseó nada: el catálogo arcade de FBNeo llevaba 0 entradas desde siempre (hallazgo + fix 2026-09-19, durante MATCH-ZIP-HASH-1)

Origen: investigando por qué 329 sets arcade multi-archivo (`captcommb.zip`,
`19xxd.zip`, `armwar1d.zip`... casi todos en `cps1/`) no matcheaban pese a
que sus sets *parent* (`captcomm`, `19xx`, `armwar`) sí estaban en el
catálogo cargado. Verificado a mano con `load_arcade_dir()`: los parents
venían todos de `"MAME 2003-Plus XML.xml"` — ninguno de `"FBNeo - Arcade
Games.dat"`, el segundo archivo del directorio `catalogs/arcade/`.

**Causa raíz confirmada**: el `.dat` que llevaba años en
`.rommgr/catalogs/arcade/FBNeo - Arcade Games.dat` **no era XML** — formato
texto plano ClrMamePro (`clrmamepro ( name "..." )`, `game ( name "..." rom
( ... ) )`). `load_fbneo_dat()` (`catalog/mame_loader.py:57-78`) hace
`ET.parse(path)` directo — con este archivo, lanza `ET.ParseError`,
capturado en silencio por el `except (ET.ParseError, OSError): pass` y
devuelve `{}`. Verificado en vivo: `load_fbneo_dat()` sobre el archivo real
→ **0 entradas**; el total de 4.858 entradas "arcade" que reportaba el
matcher venía **al 100% de MAME 2003-Plus** (un fork ligero/antiguo de MAME
usado en handhelds retro, sin buena parte de los clones/bootlegs que sí
lista el MAME oficial actual o FBNeo). El pass arcade (`_match_arcade()`,
`catalog/matcher.py:450-480`) llevaba funcionando así desde el origen del
proyecto sin que nadie lo notara — ni tests ni uso normal lo habrían
detectado, porque un `{}` es indistinguible de "catálogo vacío mientras
carga" salvo comparando cuenta de entradas a mano.

**Bug secundario, mismo archivo**: aunque se sustituya por un `.dat` real en
XML, `load_fbneo_dat()` leía `description`/`year`/`manufacturer` como
**atributos** del tag `<game>` (`game.get("description")`), pero el `.dat`
oficial de FBNeo (github.com/libretro/FBNeo, `dats/FinalBurn Neo (ClrMame
Pro XML, Arcade only).dat`) los lleva como **elementos hijos**
(`<game><description>...</description></game>`), igual que `load_mame_xml()`
ya maneja correctamente. Sin el fix, un `.dat` FBNeo real sí habría cargado
(no habría lanzado excepción) pero con `description=""` para las 8.380
entradas — degradando el título a solo el stem (`match_confidence='medium'`
seguiría siendo correcto, pero cualquier UI que muestre el título perdería
la descripción real).

**Hallazgo aparte, no arreglado hoy**: `catalog/dat_downloader.py`
(DAT-DL-1/2) ya tiene un downloader completo con mapeo plataforma→URL
(`libretro-database`) para No-Intro/Redump/FBNeo/MAME — pero **no está
conectado a ningún comando CLI ni handler web** (verificado: 0 llamadas a
`download_dat()` fuera de sus propios tests). Probado en vivo hoy: las URLs
de `libretro-database` para `"FBNeo Arcade"` y `"MAME 2003 Plus"` devuelven
**404** (el repo debió reestructurar `metadat/fbneo`/`metadat/mame`) — el
downloader está roto para arcade además de no estar conectado. No
investigado si las URLs de No-Intro/Redump (mismo `_BASE`) siguen vivas.

**Corrección importante (encontrada al revisar `/progreso` el mismo día)**:
el downloader que **sí está conectado y es el que usa el botón real "Descargar
DAT" de la web** es otro, independiente — `_LIBRETRO_DAT_CATALOG` +
`_run_dat_download()` en `web/handlers/scan.py`, no `catalog/dat_downloader.py`.
Ese downloader real ya tuvo su propio bug de URL (`ARCADE-DAT-URL-STALE-1`,
arreglado 2026-09-15: `metadat/fbneo` → `metadat/fbneo-split`) — pero ese fix
solo corrigió el **404**, nunca verificó el **contenido**. Comprobado hoy en
vivo: `metadat/fbneo-split/FBNeo - Arcade Games.dat` responde `200` pero es
el mismo formato texto plano ClrMamePro (`clrmamepro ( ... )`, `game ( name
"..." rom (...) )`) que causó este mismo bug — **no es XML, `load_fbneo_dat()`
seguirá devolviendo 0 entradas aunque se descargue de nuevo desde la web**,
pese a los dos fixes de hoy. Es decir: **si alguien pulsa "Descargar DAT" →
FBNeo Arcade desde la pestaña Herramientas, revierte silenciosamente el
arreglo de hoy** (catálogo 10.212 → 0 entradas FBNeo otra vez, sin ningún
aviso — mismo patrón exacto de fallo silencioso que el bug original). El
`.dat` de MAME 2003-Plus sí es XML real y no tiene este problema (`metadat/
mame/MAME 2003-Plus XML.xml` → `200`, formato correcto). Ver `MATCH-ARCADE-DAT-2`.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-ARCADE-DAT-1 | `load_fbneo_dat()` ahora lee description/year/manufacturer como elemento hijo primero (fallback a atributo, mismo patrón que `load_mame_xml()`). Sustituido `.rommgr/catalogs/arcade/FBNeo - Arcade Games.dat` (texto plano, 0 entradas reales) por el `.dat` XML oficial actual descargado de `github.com/libretro/FBNeo/blob/master/dats/FinalBurn Neo (ClrMame Pro XML, Arcade only).dat` (backup del original en `.rommgr/catalogs/arcade_backup_20260919/`). 3 tests nuevos (`tests/test_mame_loader.py`): lee child-element real, fallback a atributo, y el `.dat` texto-plano anterior sigue devolviendo `{}` sin lanzar. 1398/1398 tests, ruff+format limpios | `catalog/mame_loader.py` (`load_fbneo_dat`) | ✅ hecho 2026-09-19. Catálogo arcade cargado: 4.858 → 10.212 entradas. **Re-match ejecutado contra `library_pc.db` real** (backup previo en `.rommgr/db-backup/library_pc.20260919T214730Z.db`, 13.548 filas sin match re-evaluadas): **253 filas nuevas resueltas** vía el catálogo FBNeo ahora real (`match_confidence='medium'`), incluyendo 251/329 de los sets multi-archivo de `MATCH-ZIP-HASH-1`. `dat_downloader.py` sigue sin conectar y con URLs de arcade rotas — no arreglado, candidato a tarea aparte si se decide automatizar la descarga de DATs |
| MATCH-ARCADE-DAT-2 | **✅ Arreglado 2026-09-20** — camino elegido: apuntar la entrada del catálogo a la fuente XML real de FBNeo (`raw.githubusercontent.com/libretro/FBNeo/master/dats/FinalBurn Neo (ClrMame Pro XML, Arcade only).dat`, nuevo campo `"url"` override en `_LIBRETRO_DAT_CATALOG`, `_run_dat_download` lo usa en vez de `{metadat_base}/{source}/{filename}` cuando está presente) en vez de la ruta rota de `libretro-database`. **Cerrado también el hueco de verificación real** que dejó pasar el bug: la validación post-descarga usaba `catalog_loader.load_dat_file()` (genérico, SHA1-keyed, acepta ClrMamePro texto) en vez del parser que de verdad consume el archivo una vez en `catalogs_arcade_dir` (`load_arcade_dir()` dispatcha por extensión a `load_mame_xml`/`load_fbneo_dat`, ninguno de los dos con fallback ClrMamePro-texto) — ahora `_run_dat_download` valida con ese mismo parser para `catalog in ("fbneo", "mame")`. Verificado en vivo: descarga real (14 MB, 8.380 entradas vía `load_fbneo_dat`) y regresión confirmada (payload ClrMamePro-texto ahora reportado como error, no como "downloaded"). 2 tests nuevos (`tests/test_dat_catalog_age.py::TestFbneoArcadeDatDownload`), 1400/1400 en verde, ruff limpio | `web/handlers/scan.py` (`_LIBRETRO_DAT_CATALOG`, `_run_dat_download`), `tests/test_dat_catalog_age.py` | ✅ hecho y mergeado a `develop` (`ee883ebc`, PR #334) — re-verificado 2026-09-22 (Día69) con `git merge-base --is-ancestor`, la nota "pendiente PR/merge" estaba desincronizada |

---

### MATCH-FIX-4 — `resolve-duplicates` calcula logros RA con la plataforma de un solo miembro del grupo, ciega copias reales en grupos cross-plataforma (hallazgo 2026-09-12, BLOQUEANTE para `--apply`)

Origen: sesión 2026-09-12, revisando `resolve-duplicates` (dry-run, sin
aplicar) mientras corría `convert-chd` de fondo. Verificado contra la BD
real (`F:\Juegos Retro`): 3 grupos "plain" (auto-resolubles, no conflicto de
disco) mezclan plataformas reales distintas — `Game Boy` vs `Game Boy
Color` (mismo título, mismo contenido exacto: MD5 idéntico entre ambos
archivos) — y los 3 son justo 3 de los 20 juegos marcados/enviados hoy a la
Anbernic por tener logros RA (`Tetris DX`, `Tony Hawk's Pro Skater`, `Men in
Black - The Series`).

Causa raíz confirmada leyendo el código: `_review_groups_for_repo`
(`web/builders/duplicates.py:860`) calcula `plat = next((r["platform"] for
r in members if r["platform"]), None)` — **una sola plataforma para todo el
grupo** (la del primer miembro con `platform` no nulo) — y la usa para
cargar `hash_map` (`:861`, `_load_ra_hash_map(cache_dir, plat, hash_cache)`)
aplicado a **todos** los miembros del grupo en el bucle de `:862-866`, en
vez de resolver la caché RA propia de cada fila con su propio `platform`.
Verificado con `get_ra_achievements`: el mismo MD5 de "Tony Hawk's Pro
Skater (USA, Europe).gbc" da `-1` (desconocido) contra la caché de "Game
Boy" y `12` (logros reales) contra la de "Game Boy Color" — el grupo eligió
`plat="Game Boy"` (por orden de fila), así que la copia `.gbc` real quedó
marcada `ra_supported=False` igual que la `.gb`, empatando en
`_review_entry_sort_key` (`:227-233`) y cayendo al desempate por nombre de
archivo, donde `"0204 Tony Hawk..."` (dígito inicial) ordena antes que
`"Tony Hawk's..."` alfabéticamente — ganando el archivo de un pack bulk sin
depurar (`gb/Classic Game/`) sobre la copia bien nombrada de
`gb/GB official game ROM complete works/`.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-FIX-4 | `_review_groups_for_repo` debe resolver la caché RA **por fila** (`r["platform"]` de cada miembro, no el `plat` compartido del grupo) antes de puntuar `scored`/`ra_supported` — mismo patrón que `get_ra_achievements` ya usa correctamente en `ra_duplicates_service.py`. Mientras no se arregle, **no ejecutar `resolve-duplicates --apply` sin revisar antes los grupos que mezclan extensiones/plataformas distintas** (dry-run + inspección manual, como se hizo hoy) — riesgo real de descartar copias RA-verificadas a favor de duplicados peores. Alcance medido hoy: 3 grupos afectados de 376 "plain", pero puede crecer si se decompress/rescan más colecciones bulk con solapamiento GB/GBC (u otras familias, p. ej. NES/Famicom) | `web/builders/duplicates.py:860-866` (`_review_groups_for_repo`) | ✅ hecho 2026-09-12 — el bucle de puntuación ahora carga `_load_ra_hash_map(cache_dir, r["platform"] or plat, hash_cache)` **por fila** en vez de una sola vez con el `plat` compartido del grupo; `plat` se conserva para la clave del grupo y el chequeo de carpeta correcta (sin cambio ahí). Verificado contra la BD real: los 3 grupos GB/GBC afectados ahora recomiendan correctamente el `.gbc` (15/12/39 logros reales) sobre el duplicado bulk. 1 test nuevo (`test_ra_cross_platform_group_scores_each_entry_by_its_own_platform`, `tests/test_builders_duplicates.py`), 30/30 pass en el archivo, ruff+format limpios |

---

### MATCH-FIX-5 — El catálogo carga DATs de PC/Xbox sin ningún filtro de plataforma, contaminando el título de ROMs de consola reales (hallazgo 2026-09-12, sin implementar)

Origen: sesión 2026-09-12, investigando en paralelo (mientras corría
`convert-chd` de fondo) 16 conflictos de `plan` sueltos en `.gba`/`.nds`/
`.iso`/`.md` no explicados por `MATCH-FIX-3`. Consulta directa a la BD real
reveló la causa: **1.285 juegos** tienen `catalog_source = "IBM - PC
compatible - Datfile (57444)..."` y **88 más** vienen de
`"Microsoft - Xbox - Datfile (2675)..."` — DATs de PC/Xbox, plataformas que
este proyecto **no gestiona** (`CLAUDE.md`: "no es un launcher/front-end de
emuladores", los 3 pilares son consolas retro). Reparto real por
plataforma (solo IBM): PlayStation 339, Game Boy 336, GBA 163, GBC 131, NES
87, SNES 73, Mega Drive 64, NDS 35, Game Gear 31, Arcade 18, PS2 6,
Dreamcast 1, GameCube 1 — prácticamente todas las plataformas de la
biblioteca tienen ROMs con el `canonical_title` sacado de un catálogo de PC
o Xbox, no del suyo propio.

Causa raíz confirmada leyendo el código: `_load_dir()`
(`catalog/matcher.py:157-177`) hace `sorted(directory.glob("*.dat"))` sobre
`nointro_dir`/`redump_dir` **sin ningún filtro de plataforma** — carga
literalmente cualquier `.dat` presente en esas carpetas (confirmado:
`.rommgr/catalogs/nointro/` tiene 126 DATs, incluyendo "IBM - PC compatible
- Datfile", "IBM - PC compatible - SBI Subchannels", "Microsoft - Xbox -
Datfile", "Microsoft - Xbox - BIOS Datfile", 3× "Microsoft - XBOX 360 -
..."). `_build_title_index()` (`:179-188`) indexa **cada entrada de cada
DAT cargado** por título normalizado, sin descartar las de plataformas
ajenas al alcance del proyecto. Cuando `_match_by_title()` (Pass 2) solo
encuentra un único hit para un título (sin ambigüedad real entre varios
candidatos, el caso que `MATCH-FIX-2` sí sabe desambiguar), lo acepta tal
cual aunque ese único hit venga de un DAT de PC/Xbox — ejemplo real
confirmado: `"God of War II (Europe).iso"` (PS2 real) y `"God of War II
(USA).iso"` (PS2 real, región distinta) **ambos** terminan con
`canonical_title = "God of War II (Europe)... (Press Materials)"`
(entrada del DAT de PC), lo que además genera colisión de nombre entre las
dos regiones reales al intentar renombrar.

Root cause probable de cómo llegaron esos DATs ahí: el job `download_dats`
(descarga masiva de No-Intro/Redump) no filtra por plataforma — descarga
"todo lo que hay", incluyendo sistemas fuera del alcance del proyecto.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-FIX-5 | Filtrar el cargador de catálogos por plataforma, reutilizando la lista ya curada del proyecto. Tras filtrar, **re-lanzar `match` con `include_low_confidence: true`** (patrón ya usado en `MATCH-FIX-2`) sobre las plataformas afectadas para recalcular `canonical_title` de los 1.373 juegos contaminados — puede generar renombrados reales, no solo un cambio de metadatos | `catalog/matcher.py:157-177` (`_load_dir`), `:179-188` (`_build_title_index`) | ✅ hecho 2026-09-12 en dos partes. **Parte 1** (código): `_load_dir()` ahora salta cualquier `.dat` que `_platform_from_dat_name()` (ya existente, `catalog/matcher.py:31-86`) no reconozca — reutiliza la lista curada de plataformas del proyecto en vez de mantener una lista negra nueva. Verificado: No-Intro pasa de 287.030 a 67.131 entradas cargadas, Redump de 210.217 a 6.637 (fuera: IBM PC, Xbox/360, PS3, PSP/Vita, Wii U, Macintosh, Amiga CDTV, FM-Towns...). 3 tests del fixture `dirs_with_arcade`/`test_crc_index_drops_cross_dat_collisions` usaban DATs fuera de alcance como relleno (FM-7 real de MATCH-FIX-1, Evercade) — actualizados a DATs reconocidos (Amiga) sin cambiar la intención del test. 1273 tests, 1 fallo no relacionado (contención real con `chdman.exe` corriendo de fondo en la misma sesión). ruff+format limpios. **Parte 2** (datos reales, `POST /api/match {"include_low_confidence": true}`): 7.166 filas re-evaluadas (730 SHA1 alto, 2.021 título bajo — ahora limpio, sin PC/Xbox —, 4.415 sin match). **Hallazgo aparte durante la verificación**: 563 de los 1.373 originales seguían con `catalog_source` IBM/Xbox tras el re-match — `_do_match()` (`web/handlers/scan.py:551-566`) solo escribe cuando `matcher.match()` devuelve un resultado nuevo, nunca limpia los campos cuando la re-evaluación ahora no encuentra nada (nunca puede pasar antes de este fix, porque el catálogo de PC/Xbox siempre "encontraba algo"). Verificado uno a uno con `matcher.match()` en vivo que esas 563 filas ya no matchean con nada — limpiadas a mano (`canonical_title`/`match_confidence`/`catalog_source` → `NULL`, con confirmación explícita del usuario) para que queden como "sin match" real en vez de con datos obsoletos. **Resultado final verificado**: 0 juegos con `catalog_source` IBM/Xbox; `plan` baja de 1.276 a **842 conflictos** (2.334 para renombrar, 5.369 ya correctos) |

---

### MATCH-HEADER-1 — Identidad por header interno del ROM para NDS/GBA (feature nueva, petición usuario 2026-09-12)

Origen: al revisar a mano los 7 conflictos NDS/GBA sueltos de `MATCH-FIX-3`
(Castlevania, Kirby, Naruto, From the Abyss), el usuario preguntó si no
sería mejor implementar una solución general en vez de arreglos caso a
caso. Los DATs No-Intro de este proyecto no traen número de serie —
`_build_review_queue` (`web/builders/duplicates.py`) solo puede enlazar
duplicados por SHA1 exacto o por coincidencia de título — así que un
archivo cuyo SHA1 no está en catálogo y cuyo nombre no coincide con nada
(un parche de traducción, un dump malo/incompleto) es invisible para
siempre, por muy claro que sea que es copia de un juego ya presente.

NDS y GBA sí llevan una identidad real y verificable en el propio header
del cartucho: un código de juego de 4 caracteres asignado por Nintendo,
globalmente único por edición — leerlo del archivo es un hecho, no una
suposición por nombre.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-HEADER-1 | `detection/rom_header.py` (nuevo): `extract_internal_id(path, extension)` lee el header NDS (código en offset `0x0C`), GBA (offset `0xAC`) y GB/GBC (título interno en `0x134`, sin código corto fiable). `_review_groups_for_repo` (`web/builders/duplicates.py`) añade una unión nueva por `(platform, internal_id)` — **solo para `.nds`/`.gba`**: el código de 4 caracteres es fiable para unir sin revisión humana; el título de GB/GBC (16 caracteres, puede truncar el texto que distingue dos juegos reales) se dejó fuera para no arriesgar falsos positivos que alimenten el "auto-resolver sin revisión" de `resolve-duplicates`. Deliberadamente **no** excluye nombres con marca de hack/traducción (`is_non_canonical_variant`) como sí hace la unión crossfmt — son exactamente el caso a rescatar. Razón nueva `"header"` en el grupo, con chequeo separado (`has_real_title_dup`, distinto del `has_title_dup` ya existente, más laxo) para no reclamarla cuando el grupo ya está explicado por sha1 o por título real compartido. **Hallazgo del usuario durante la revisión** ("¿puede ser que en GBA haya juegos de GBC?"): confirmado contra la BD real — 2 filas con `platform='Game Boy Advance'` cuyo `source_path` apunta a un `.md` de Sega Mega Drive real (mismo tipo de problema, aunque no era literalmente GBC). Sin el chequeo, esos bytes ajenos podrían leerse como un "código" válido y colisionar por casualidad. Blindado con dos filtros: GBA valida el byte fijo `0xB2 == 0x96` (constante real de todo cartucho GBA) antes de confiar en el código, y ambos (NDS+GBA) exigen que el código extraído sean 4 caracteres `[A-Z0-9]` — cualquier otra cosa se descarta como basura | `detection/rom_header.py` (nuevo), `web/builders/duplicates.py` | ✅ hecho 2026-09-12. 11 tests (`tests/test_rom_header.py`, incluye el caso real de blindaje), 3 tests (`tests/test_builders_duplicates.py`: rescata un parche sin match, no une juegos distintos, no duplica razón cuando ya hay sha1/título real). 1287 tests, ruff+format limpios. **Verificado contra la biblioteca real** (`F:\Juegos Retro`): 15 grupos nuevos encontrados, invisibles hasta hoy — ej. `"Megaman Zero 1 [E].gba"` ↔ `"Mega Man Zero (USA, Europe).gba"`, `"4832 - Pokemon - Edicion Oro HeartGold (S).nds"` ↔ `"Pokemon - Edicion Oro HeartGold.nds"` — y confirmado que las 2 filas Mega Drive mal etiquetadas ya no producen falso match. Solo agrupa (superficie para revisión/`apply_ra_conflicts`); no fuerza `canonical_title` ni borra nada por sí solo. **Follow-up no implementado**: investigar por qué esas 2 filas tienen `platform` incorrecto en primer lugar (bug de detección aparte, no tocado hoy); extender a GB/GBC con una señal más fuerte que el título truncado; usar el tamaño esperado del DAT como desempate de calidad de dump en `_review_entry_sort_key` |
| MATCH-FIX-14 | **✅ Hecho 2026-09-19** (roadmap 14, `fix/matcher-coverage-gaps`, solo Pasos 3-4 — Pasos 1-2 de `MATCH-FIX-3` siguen bloqueados por decisión del usuario). Resuelve los 2 follow-ups de arriba: **(a) GB/GBC** — `_read_gb_id` (`detection/rom_header.py`) ahora valida el checksum de cabecera estándar de Game Boy (offset `0x14D`, calculado sobre `0x134-0x14C` — tipo de cartucho, tamaño ROM/RAM, región, versión, licencia) y devuelve `título:checksum` en vez de solo el título truncado; si el checksum no coincide con los propios bytes del fichero, se trata como cabecera no fiable (`None`) — mismo criterio conservador que el byte fijo `0xB2==0x96` de GBA. `.gb`/`.gbc` añadidos a `_HEADER_EXTENSIONS` (`web/builders/duplicates.py`), antes solo `.nds`/`.gba`. **(b) Desempate por tamaño** — en vez de repetir una consulta al catálogo en cada carga de la cola de revisión (obligaría a cachear/instanciar `CatalogMatcher` ahí, sin patrón existente para eso), `_reference_size_bytes()` reutiliza un dato que ya vive en la fila: el tamaño de cualquier miembro del propio grupo con `match_confidence="high"` (un SHA1 exacto ya implica que su tamaño es el correcto) — nuevo `size_tier` en `_review_entry_sort_key`, justo tras `integrity_tier` | `detection/rom_header.py`, `web/builders/duplicates.py` (`_HEADER_EXTENSIONS`, `_reference_size_bytes`, `_review_entry_sort_key`) | ✅ 1395/1395 tests en verde (6 nuevos: 2 en `test_rom_header.py`, 3 en `test_builders_duplicates.py`), ruff+format limpios |

---

### MDFOLDER-FIX-1 — `detect_platform()` no reconocía "Sega Mega Drive" (dos palabras) como carpeta válida para `.md` (hallazgo 2026-09-12, petición usuario "investígalo")

Origen: investigando por qué 2 filas tenían `platform='Game Boy Advance'`
apuntando a archivos `.md` reales de Mega Drive (hallazgo de `MATCH-HEADER-1`,
el usuario preguntó "¿puede ser que en GBA haya juegos de GBC?"). Causa
raíz confirmada leyendo el código: `PLATFORM_CONTEXT_BY_EXTENSION[".md"]`
(`detection/platform_detector.py:66-68`) solo reconocía las carpetas
`{"megadrive", "genesis", "sega genesis", "md"}` — la carpeta real de esta
biblioteca es **"Sega Mega Drive"** (nombre oficial occidental, dos
palabras), que tokeniza a `{"sega","mega","drive"}` y no es superconjunto
de ninguna de las combinaciones aceptadas. `detect_platform()` devolvía
`None` para cualquier `.md` ahí, dejando el fallback por título de
`_match_by_title()` sin señal de plataforma real para desambiguar —
cualquier `.md` cuyo SHA1 no calzara exacto con el catálogo (bootlegs,
hacks, revisiones no catalogadas) podía terminar matcheado por título
contra **cualquier plataforma**, no solo GBA (confirmado: título colisionó
con el catálogo de Game Boy Advance por coincidencia). Alcance medido: 14
de 462 `.md` en esa carpeta.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MDFOLDER-FIX-1 | Añadir `"mega drive"` y `"sega mega drive"` al set de `PLATFORM_CONTEXT_BY_EXTENSION[".md"]` | `detection/platform_detector.py:66-68` | ✅ hecho 2026-09-12. 2 tests nuevos (`tests/test_platform_detector.py`), 89 tests del archivo en verde, 1289 tests totales, ruff+format limpios. **Re-matcheadas las 14 filas reales**: 13 recuperaron su plataforma y título correctos de Mega Drive (incluye `Micro Machines (USA).md`, que además destrababa uno de los conflictos de nombre medidos en `MATCH-FIX-5`); 1 (`Super Mario Bros. (Unl) [f1].md`, bootleg sin entrada real en el catálogo) se dejó sin match — mejor que un título GBA falso — y su `platform` corregido a `Sega Mega Drive` de todas formas (el campo describe el archivo, no si hubo match). 0 filas `.md` de esa carpeta con plataforma incorrecta tras el fix |
| MDFOLDER-FIX-2 | Generalizado tras `MDFOLDER-FIX-1`: `PLATFORM_BY_FOLDER` (`detection/platform_detector.py`, usado por `detect_platform()` para **toda** extensión ambigua — `.bin`/`.cue`/`.iso`/`.zip`/`.chd`/`.img`, no solo `.md`) solo tenía slugs cortos ("ps2", "nds", "gba"...) como claves — **7 de 11 carpetas reales de esta biblioteca no se reconocían en absoluto** (`PlayStation 2`, `Nintendo DS`, `Game Boy Advance`, `Game Boy Color`, `Game Boy`, `Sega Mega Drive`, `Sega Saturn`, `Game Gear` — verificado uno a uno contra `F:\Juegos Retro`). `_build_tables()` ahora registra también el nombre canónico completo en minúsculas como clave adicional (`by_folder.setdefault(canonical.lower(), canonical)` por cada valor distinto ya cargado) — nunca pisa una clave slug ya existente, solo añade | `detection/platform_detector.py:36-53` (`_build_tables`) | ✅ hecho 2026-09-12. 6 tests nuevos (parametrizados), 95 tests del archivo, 1295 tests totales, ruff+format limpios. **Medido contra la biblioteca real** tras `MATCH-STALE-1` (abajo): 8 archivos `.bin`/`.cue`/`.iso` en `PlayStation 2\` que estaban mal etiquetados como GameCube/Wii/Nintendo DS/PSP por la misma causa que `MDFOLDER-FIX-1` (títulos reales multi-plataforma — Crash Bandicoot, Sonic Heroes, Viewtiful Joe — coincidiendo por nombre con la versión de otra consola) corregidos a `PlayStation 2`. Los aparentes casos de Game Boy Color/Game Gear investigados aparte resultaron ser falsos positivos de la medición (texto "Game Boy Color" en el nombre de archivo, no la carpeta; `.sms` en carpeta `Game Gear\` es organización real intencional de esta biblioteca, no un bug) |

### MATCH-STALE-1 — El job de `match` nunca limpiaba un match viejo cuando la re-evaluación ya no encuentra nada (hallazgo 2026-09-12, patrón repetido 3 veces en la misma sesión)

Origen: mismo patrón encontrado y parcheado a mano tres veces hoy
(`MATCH-FIX-5`: 563 filas IBM/Xbox; `MDFOLDER-FIX-1`: 1 fila Mega Drive;
`MDFOLDER-FIX-2`: 8 filas PlayStation 2) — cada vez que un fix del matcher
hacía que una fila previamente mal-matcheada ahora correctamente no
matchee con nada, la fila se quedaba con el `canonical_title`/
`match_confidence`/`catalog_source` viejo para siempre, porque tanto
`rommgr match` (`cli.py:704`) como `POST /api/match`
(`web/handlers/scan.py`, `_do_match`) solo llaman `update_match()` cuando
`matcher.match()` devuelve un resultado nuevo — el caso "ya no hay match"
nunca escribe nada.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-STALE-1 | Nuevo `repository.clear_match(source_path)` (`database/repositories/games.py`) — resetea `canonical_title`/`match_confidence`/`catalog_source` a `NULL`, deja `platform` intacto a propósito (describe el archivo, no si hubo match de catálogo). Llamado en la rama `else` de ambos loops de match (CLI y handler web) en vez de solo incrementar `unmatched` | `database/repositories/games.py`, `cli.py:704` (`match`), `web/handlers/scan.py` (`_do_match`) | ✅ hecho 2026-09-12. 1 test nuevo (`tests/test_repository.py::test_clear_match_resets_to_unmatched`), 1296 tests totales, ruff+format limpios. Verificado en vivo: tras el fix, un nuevo re-match (`include_low_confidence`) ya limpia solo cualquier fila que deje de matchear — no hará falta repetir la limpieza manual la próxima vez que se ajuste el matcher |

---

### PSX-CUE-DESYNC-1 — `rename_rom_with_saves` no reescribe la referencia `FILE` interna del `.cue` al renombrar — corrupción real, silenciosa desde 2026-03-21 (hallazgo CRÍTICO 2026-09-12, durante `convert-chd`)

Plan de implementación para los 11 casos multi-track restantes (`-1b`), junto
con `PSX-STRUCTURE-4`, en `.claude/roadmaps/archivo/15-psx-cue-multitrack-integrity.md`.

Origen: `convert-chd --apply` sobre `F:\Juegos Retro\PlayStation` reportó
**33 fallos** de 122 sets con el mismo patrón: `Bin file(s) not found`.
Investigado en vez de descartarlo como ruido — **32 de los 99 `.cue` de la
biblioteca activa (32%) tienen su referencia interna `FILE "..."` apuntando
a un `.bin` que no existe con ese nombre**, aunque el `.bin` real sí está
en la misma carpeta con otro nombre. Esos juegos **no cargarían en ningún
emulador real** — corrupción silenciosa, invisible hasta hoy porque nada
había vuelto a leer el contenido de esos `.cue` desde que se rompieron.

Causa raíz confirmada contra `file_operations` (ejemplo real, "Chicken
Run"): el 2026-03-21T23:47:18 (el `apply` más grande de la historia de esta
BD, 736 renombrados) se renombraron el `.bin` (id 656) y el `.cue` (id 657)
de "Chicken Run (Europe) (Fr,De,Es,It)" → "Chicken Run (China)" como **dos
operaciones independientes** — cada una un `os.rename()` plano vía
`rename_rom_with_saves` (`renamer/file_renamer.py:116`), que solo sabe
renombrar saves compañeros (`.srm`/`.sav`/`.state`) y **nunca reescribe el
texto interno del `.cue`** cuando el `.cue` o cualquiera de sus `.bin`
referenciados cambia de nombre. Viola directamente la regla ya documentada
en `CLAUDE.md` ("PSX siempre por sets: nunca renombrar `.bin` sin
reescribir el `.cue`") — el código nunca implementó esa regla para el caso
de renombrado plano (`plan`/`apply`), solo existe protección parcial en
`move_disc_set_to_subfolder` (mueve sin renombrar, por eso no rompe nada).
**El bug sigue vivo en el código actual** — cualquier `apply` futuro que
toque un set PSX multi-archivo puede reproducir esta misma corrupción.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| PSX-CUE-DESYNC-1a | Reparar los `.cue` de un solo track ya rotos: reescribir la línea `FILE "..."` con el nombre real del `.bin` presente en la misma carpeta (candidato único y sin ambigüedad en los 21 casos) | `F:\Juegos Retro\PlayStation\*.cue` (datos, no código) | ✅ hecho 2026-09-12 con confirmación explícita del usuario. Backup del `.cue` original de cada uno en `.rommgr/backup_cue_repair_2026-09-12/` antes de tocar nada. Verificado tras cada reescritura con `parse_bins_from_cue()` (auto-rollback si la verificación fallaba — no hizo falta ningún rollback). 21/21 reparados, 0 omitidos. Sanity check adicional: conversión real con `chdman.exe` sobre uno de ellos ("Chicken Run (China)") |
| PSX-CUE-DESYNC-1b | **Investigado y parcialmente reparado 2026-09-15** (rama `fix/psx-cue-multitrack-integrity`, roadmap `.claude/roadmaps/archivo/15-psx-cue-multitrack-integrity.md`). El diagnóstico original (emparejar `TRACK`↔`.bin` por número) resultó no aplicar tal cual: los `.cue` de estos sets **ya referenciaban el nombre correcto** — lo que faltaba eran los propios ficheros `.bin` de las últimas pistas de audio, no un desajuste de nombre. Encontrados en `_descartados/` **8 archivos huérfanos mal etiquetados como "Frenzy! (Europe) (Track NN).bin"** (un juego que no existe en ninguna otra parte de la biblioteca) — mismo incidente de renombrado masivo del 2026-03-21 que causó `PSX-CUE-DESYNC-1`. Por número de pista, coincidían sin ambigüedad con 5 de los 11 casos: **Darkstalkers (17, 46), Gundam Battle Assault (21), Street Fighter Alpha (51), Super Pang Collection (61)** — restaurados y verificados con `chdman createcd` real (conversión completa sin error, borrada después, solo verificación). **Street Fighter Collection recuperó 2 de sus 5 pistas que faltaban (66, 68)** del mismo lote. **Dino Crisis (Japan)** resultó ser un caso distinto: ya tenía un `.chd` funcional de una sola pista (verificado por coincidencia exacta de frames, `.bin`/2352 = frames del `.chd`) — el `.cue`/`.ccd`/`.img`/`.sub` sueltos eran redundantes, movidos a `_descartados/` (mismo patrón que `PSX-CHD-REDUNDANT-1`). **MediEvil 2 y Dino Crisis 2 igual** (ver fila propia abajo). **No recuperables, sin candidato encontrado en la biblioteca**: Street Fighter Collection (pistas 70 y 72 — además de la 62 ambigua con Mortal Kombat 3, sin asignar), Mortal Kombat 3 (pista 62), Warhammer (pista 6), y la pista 2 (audio) de ambas variantes de Magical Tetris Challenge (Europe/Germany). **Movidos a `_descartados/`** los 5 sets completos (142 archivos: 63 Street Fighter Collection, 61 Mortal Kombat 3, 6 Warhammer, 2+2 Magical Tetris Challenge ×2) — recuperable, no borrado permanente. `rommgr scan` re-corrido: 142 huérfanos limpiados, 0 errores. Acción pedida explícitamente por el usuario en el momento ("borra aquellos juegos que no puedan recuperarse") | `F:\Juegos Retro\PlayStation\*.cue` (datos) | 🟡 5/11 reparados y verificados, 3 casos (Dino Crisis Japan, MediEvil 2, Dino Crisis 2) resueltos como redundantes, 5 sets irrecuperables descartados a papelera a petición del usuario |
| MEDIEVIL2-DINOCRISIS2-RAW-REDUNDANT-1 | Hallazgo 2026-09-15 durante `PSX-CUE-DESYNC-1b`: `MediEvil 2 (Europe) (En,Fr,De).cue` y `Dino Crisis 2 (France) (Xplosiv).cue` referenciaban nombres de otra variante regional (`(Es,It,Pt)`/`(Spain)`) que no existe en ningún sitio de la biblioteca — no reparables. Ambos ya tenían un `.chd` funcional de una sola pista de datos (sin la pista de audio que el `.cue` roto asumía), y el `.bin` suelto coincidía exactamente en número de frames (`tamaño/2352`) con los frames reportados por `chdman info` para cada `.chd` — mismo patrón que `PSX-CHD-REDUNDANT-1`. Movidos `.cue`+`.bin` de ambos a `_descartados/` (recuperable, no borrado) | `F:\Juegos Retro\PlayStation\` | ✅ resuelto 2026-09-15 — raw redundante apartado, `.chd` de cada uno intacto |
| PSX-CUE-DESYNC-1c | **Arreglar la causa raíz en el código** para que esto no vuelva a pasar: `rename_rom_with_saves`/el planner deben detectar cuándo el archivo a renombrar es un `.cue`/`.gdi` (o uno de sus `.bin`/track referenciados) y reescribir la línea `FILE` correspondiente como parte de la misma operación atómica — mismo patrón que ya protege los saves compañeros, extendido a la referencia interna del sheet | `renamer/file_renamer.py` (`rename_rom_with_saves`), posiblemente `planner/operation_planner.py` | ✅ hecho 2026-09-12, a petición explícita del usuario. Nueva `_update_disc_sheet_references()` en `file_renamer.py` — cuando se renombra un `.bin`/`.img`, busca cualquier `.cue`/`.gdi` de la misma carpeta que lo referencie (por nombre base, no por ruta completa — limpia también rutas absolutas obsoletas de paso) y reescribe esa línea al nuevo nombre. Funciona en cualquier orden (bin-antes-que-cue o al revés, porque busca por contenido, no por nombre del propio `.cue`). Enganchado como "Step 1.5" tras el rename principal, best-effort (nunca bloquea el rename si falla la reescritura del sheet — solo log). El rollback (si falla el renombrado de un save compañero) también revierte la referencia del sheet, para no dejar el set desincronizado ni siquiera en el camino de fallo. 6 tests nuevos (`tests/test_file_renamer.py`): actualiza `.cue`, actualiza `.gdi`, no toca un `.cue` no relacionado, revierte en rollback, y confirma que renombrar el propio `.cue` no necesita (ni debe) reescribir su contenido. 1301 tests totales, ruff+format limpios. **Nota de alcance**: cubre `.bin`/`.img`; los 11 casos multi-track ya rotos (`PSX-CUE-DESYNC-1b`) siguen sin repararse — este fix solo previene que se rompan *nuevos* sets a partir de ahora |
| PSX-CUE-DESYNC-1e | **Bug encontrado 2026-09-15 revisando `PSX-CUE-DESYNC-1c` en vivo**: `_update_disc_sheet_references()` comparaba `ref_name == old_name`/`r.name == old_name` (case-sensitive) en vez de case-insensitive — en NTFS un `.cue` que referencia `"Game.BIN"` con el archivo real `"Game.bin"` sigue resolviendo bien vía `parse_bins_from_cue()` (NTFS ignora mayúsculas), pero la función nunca detectaba que ese `.cue` necesitaba actualizarse al renombrar el `.bin`, dejándolo apuntando al nombre viejo en silencio — el mismo bug que `PSX-CUE-DESYNC-1c` se escribió para prevenir, reintroducido por un caso sin cubrir. El propio archivo ya usa `same_file()` para el mismo tipo de problema en otras dos comparaciones (líneas 292/302) — aquí no se aplicó. Confirmado que ningún `.cue` reparado en `PSX-CUE-DESYNC-1b` tenía este problema (bug latente, no disparado) | `renamer/file_renamer.py:123,139` (`_update_disc_sheet_references`) | ✅ arreglado 2026-09-15 — `.lower()` en ambas comparaciones (no `same_file()`, que requiere paths existentes en disco; aquí son nombres sueltos). 1 test nuevo (`test_rename_bin_updates_sibling_cue_reference_case_insensitive`), 1326 tests totales, ruff+format limpios |
| PSX-CUE-DESYNC-1d | Medido 2026-09-13 con los parsers reales del proyecto (`parse_bins_from_cue`, `parse_tracks_from_gdi` de `converters/chd_converter.py`) sobre `F:\Juegos Retro\saturn` y `\dreamcast`. **Resultado: el bug no tiene superficie en esta biblioteca para estas 2 plataformas** — `saturn/` no tiene ningún juego (solo una subcarpeta `media/` vacía, 0 `.cue`), y `dreamcast/` no usa ningún formato con hoja de referencias (0 `.cue`, 0 `.gdi` — los 5 juegos reales son `.cdi` de archivo único; los 6 `.bin` sueltos son saves de VMU — `dc_nvmem.bin`, `vmu_save_A1/A2.bin`, `*.A1.bin` por juego — no discos). GameCube tampoco aplica (formato de archivo único `.iso`/`.rvz`, sin hoja). Conclusión: la corrupción de `PSX-CUE-DESYNC-1` es exclusiva de PSX en esta biblioteca, no por falta de que el `apply` del 2026-03-21 tocara esas plataformas, sino porque Saturn/Dreamcast/GameCube nunca tuvieron sets multi-archivo aquí que pudieran desincronizarse | `F:\Juegos Retro\saturn`, `\dreamcast` | ✅ medido — sin riesgo real en Saturn/Dreamcast/GameCube para esta biblioteca |

---

### ADB-TIMEOUT-1 — `push()`/`pull()` usaban el timeout genérico de 60s de comandos shell, abortaban transferencias grandes (hallazgo + petición usuario 2026-09-13)

Origen: probando el envío de un par de juegos de Dreamcast/PS2 a la
Anbernic para verificar el trabajo de hoy, el Cable Sync real (vía
`/api/cable-sync`) abortó el lote entero al llegar a un `.cdi` de 787 MB:
`Command [...] timed out after 60 seconds`. Causa confirmada leyendo el
código: `AdbTransport.push()`/`pull()` (`sync/adb_transport.py`) llaman
`self._run("push"/"pull", ...)` sin pasar un `timeout=` propio, así que
heredan el default de `AdbTransport.__init__` (60s) — pensado para comandos
shell rápidos (`ls`, `stat`, `mkdir`), no para copiar un archivo de cientos
de MB o varios GB por USB. Confirmado en vivo con `adb push` directo (sin
el límite de la app): el mismo archivo tardó 36s a 19.8 MB/s en condiciones
normales, pero más con contención de disco (el `organize-source` de esta
sesión compitiendo por el mismo disco) — cualquier variación real de
velocidad USB/dispositivo puede superar los 60s con ROMs de este tamaño
(hay `.iso` de PS2 de hasta 8 GB en esta biblioteca).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ADB-TIMEOUT-1 | Nuevo `_transfer_timeout(size_bytes)` en `adb_transport.py`: presupuesto de tiempo proporcional al tamaño (suelo de 2 MB/s + 60s de margen fijo, mínimo 120s) en vez de un valor fijo. `push()` ya conoce el tamaño local sin coste extra; `pull()` hace un `stat` remoto antes de tirar del archivo para conocerlo (mismo patrón que ya usaba para el tamaño de retorno, solo que ahora también antes de empezar) | `sync/adb_transport.py` (`push`, `pull`) | ✅ hecho 2026-09-13. 4 tests nuevos (`tests/test_adb_transport_transfer_timeout.py`, dispositivo falso que graba el `timeout` pasado a cada llamada). 1305 tests totales, ruff+format limpios. Verificado en vivo: los 4 juegos de prueba (Sonic Adventure, Crazy Taxi 2 — Dreamcast —, Viewtiful Joe 2, Dark Cloud — PS2 —) llegaron completos a la Anbernic tras el arreglo, confirmados por tamaño exacto en el dispositivo |

---

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
| AUD-4 | **Formaliza el "posible ZIP-ROUTE-FIX-4" de arriba**: identificar los `.md` ambiguos del Inbox (sin contexto de carpeta) por CRC32 contra los DATs, igual que ZIP-ROUTE-1 hace con ZIPs sueltos | `web/inbox_pipeline.py` (`_resolve_ambiguous_md`) | ✅ **implementado 2026-07-13, PR #115** — nuevo paso 1.7 del pipeline (`inbox_pipeline.py:423-490`, llamado en `inbox_pipeline.py:1070`): para cada `.md` de la raíz sin contexto (`is_rom_file` = False) calcula su CRC32 y consulta `CatalogMatcher.crc_index()` (misma infra de ZIP-ROUTE-1, cero heurística nueva) — hit de Mega Drive → mueve a `inbox/megadrive/` (el resto del pipeline lo procesa sin código nuevo); miss → se deja quieto (posible markdown real); hit de otra plataforma o colisión en destino → warning, no se toca. Contador `md_identified` en el resultado del job. 5 tests en `tests/test_inbox_md_crc.py` (hit Mega Drive, markdown real intacto, CRC ajeno intacto, con contexto previo no es candidato, colisión no sobreescribe) — **confirmados en verde 2026-09-07** (Día56, Ronda 3). **Pendiente desde el PR original y sigue pendiente hoy**: ejecutar el pipeline sobre la biblioteca real para reorganizar los 177 `.md` varados — no verificable desde esta máquina, `F:\Juegos Retro\inbox` está vacío aquí (0 archivos), los 177 viven en el Inbox de otra máquina (`H:\ROMs`/`E:\Carpetas anbernic`) |
| RA-CONFLICT-1 | **Los conflictos "mismo nombre, contenido distinto" del organize del Inbox usan RA para decidir el ganador** — antes se limitaba a reportar en `organize_errors` y dejar todo para revisión manual. La lógica de "quedarse con la versión que tiene logros RA" ya existía para conflictos del *plan* (`apply_ra_conflicts` en `services/ra_duplicates_service.py`), pero el organize del Inbox usa su propio chequeo de colisión (`inbox_pipeline.py`, `dest_file.exists()` + `_same_content`) y no llamaba a esa lógica — rutas de código independientes. Petición del usuario 2026-07-10 tras encontrar 20 conflictos reales de este tipo en la biblioteca. | `services/ra_duplicates_service.py`, `web/inbox_pipeline.py` | ✅ rama `feature/ra-conflict-resolution-inbox-organize` — refactor: `apply_ra_conflicts` exponía la lógica de lookup RA como closures internos (`_hash_lib_for`/`_ra_for_path`); se extrajeron a funciones de módulo reutilizables `get_ra_hash_lib()`/`get_ra_achievements()`/`get_ra_achievements_for_path()` (mismo comportamiento, 4 tests existentes en verde sin cambios). Nueva función `_resolve_organize_conflict()` en `inbox_pipeline.py`: mismo criterio de desempate que `apply_ra_conflicts` (más logros gana; empate o ambos sin datos RA → sin resolver, igual que antes); reutiliza `_discard_file()` (soft-discard a `_descartados/` + borra fila BD) para el perdedor. Contador nuevo `ra_resolved` en el resultado del job "inbox". 3 tests nuevos (`test_inbox_ra_conflict.py`): source gana, dest gana, sin datos RA → sin tocar. 653 pass. **Ejecutado de verdad 2026-07-10** (backup previo de `library_pc.db`): `ra_resolved: 3` sobre los conflictos reales de la biblioteca; quedan 20 sin resolver por falta de datos RA para esa plataforma/hash — comportamiento idéntico al anterior para esos casos, nada perdido. |
| RA-CONFLICT-2 | **Revisar/resolver a mano desde la UI los conflictos que RA no puede decidir** — RA-CONFLICT-1 resuelve solo los que tienen datos RA; el resto (sin caché para esa plataforma/hash) quedaban solo como texto en `organize_errors`, sin forma de actuar salvo tocar archivos a mano. Petición del usuario 2026-07-10. | `web/inbox_pipeline.py`, `web/handlers/inbox.py`, `web/static/partials/tab-inbox.html`, `web/static/js/tabs/inbox.js`, `web/static/js/main.js` | ✅ rama `feature/ra-conflict-ui-resolution` — nuevas funciones puras `find_organize_conflicts()` (listado de solo lectura: recorre `games` bajo el Inbox, mismo cálculo de destino que el Step 6 real vía `_organize_dest_file()` extraído para no duplicarlo, incluye tamaños y logros RA de ambos lados) y `resolve_inbox_conflict()` (re-verifica que el conflicto sigue existiendo y llama a `_resolve_organize_conflict()` con el nuevo parámetro `force_keep` — mismo mecanismo de discard/move que la resolución automática, decisión inyectada en vez de calculada). Endpoints `GET /api/inbox-conflicts` + `POST /api/inbox-conflicts/resolve`. UI: sección nueva en la pestaña Inbox con botón "Revisar" → tabla (archivo, plataforma, tamaño+logros de cada lado, botones "Quedarme con Inbox"/"Quedarme con existente"). 5 tests nuevos (`test_inbox_conflicts_ui.py`), 658 pass. Verificado el endpoint de lectura contra la biblioteca real (40 conflictos con datos correctos); el de escritura solo verificado con tests (no se resolvió ningún conflicto real de la biblioteca desde este endpoint — queda para que el usuario lo use desde la UI). |
| ZIP-ROUTE-5 | **Retirar la heurística de colección por nombre** — sustituir `" - " in stem` + `>1 GB` (`web/builders/folders.py:259,276`) por "multi-entrada de `.zip`/`.chd`" (el ZIP ya se abre para ROUTE-1, es gratis). Elimina los ~39 falsos positivos. | `web/builders/folders.py` | ✅ rama `feature/zip-route-5-collection-by-content` (apilada sobre ROUTE-1) — colección = >1 entrada y mayoría `.zip`/`.chd` (`_is_source_collection`); fuera `" - "` y `_COLLECTION_MIN_BYTES`. Verificado contra biblioteca real: colecciones 47→**16, exactamente los contenedores reales** (incl. `MAME BIOS 0.277.zip`); los ~31 ex-falsos (T-En, FM77AV, Super Pocket) caen a "ZIPs no-ROM" (122→153) a la espera de ROUTE-2/3. 2 tests nuevos + 3 adaptados (635 pass) |
| ZIP-ROUTE-7 | **Feedback usuario 2026-08-29**: en la pestaña Juegos hay entradas sin portada, posiblemente `.zip` que no deberían aparecer como juego (mal clasificados: algunos se extraen y no deberían, otros deberían extraerse y no se hizo). **Causa parcial resuelta 2026-08-29 vía DEDUP-RENAME-3**: 1.508 filas fantasma (residuo del bug INBOX-CFG-1, `source_path` bajo una ruta MTP que ya no existe) purgadas de `library_pc.db` — `id=65864` (`unknown\10192n.rom`, sin portada) confirmado desaparecido de `/api/games` tras la purga. **Segunda mitad investigada 2026-10-02** contra `library_pc.db` real (ver detalle abajo) | `web/builders/folders.py`, `web/zip_router.py`, `config.py:606-624`, `detection/file_classifier.py:18-29` | 🟡 causa fantasma resuelta (ver DEDUP-RENAME-3); investigación de la segunda mitad completa, 3 hallazgos reales — ver `ZIP-ROUTE-8` |

**Investigación 2026-10-02 — 303 filas `extension='.zip' AND platform IS NULL`, desglose real:**

- **275** en `ROMS\Unknown\` sin `canonical_title` — comportamiento esperado (ZIPs no identificados por CRC, categoría "ZIPs no-ROM" de JUNK-SMART), no es un bug, nada que hacer salvo que el usuario quiera triarlos a mano.
- **13** en `ROMS\Unknown\` **con `canonical_title` ya puesto** (ej. `Kung Fu (Europe).zip`→"Kung Fu (Europe)", `Lemmings (United Kingdom).zip`, `Pac-Man - Championship Edition (World) (XBLA).zip`, `Arkanoid (USA).zip`…) — identificados por CRC (ZIP-ROUTE-1) pero **nunca movidos a su carpeta de plataforma**: `zip-route-apply` solo se ejecutó una vez de verdad (2026-07-10, ver `ZIP-ROUTE-4` arriba) y no se ha vuelto a correr desde entonces sobre los que fueron cayendo nuevos en `Unknown\`. No es un bug de código — falta volver a lanzar el apply.
- **8 falsos positivos reales — "BIOS/assets tratados como ROM" (viola el pilar `BIOS, assets y carpetas Android nunca se tratan como ROMs` de `CLAUDE.md`)**: `E:\carpetas memoria\DraStic\drastic_bios.zip` + 3 skins de `virtual_controller\` (Neon/Simple/Simple-II), `E:\Emuladores\Duckstation\resources\{cheats,patches}.zip`, `E:\Emuladores\PCSX2\resources\patches.zip`, `E:\Emuladores\Retroarch\shaders\...\LICENSE.zip`. Causa raíz: `excluded_directories` (`config.py:606-624`) solo excluía nombres genéricos (`"bios"`, `"saves"`, `"media"`…) — nunca nombres de carpeta de instalación de emulador; `classify_path()` (`detection/file_classifier.py:18-29`) no tenía ninguna otra señal para excluirlos, así que cualquier `.zip` dentro de una carpeta de emulador se clasificaba `FileCategory.ROM` solo por extensión. **Arreglado, ver `ZIP-ROUTE-8`**.
- **3 archivos totalmente ajenos** bajo `E:\carpetas memoria\ra-saves\Bootcamp\...\.venv\...` (paquetes de un curso de programación, `store.zip`/`tiny-data.zip`/`UltimaSemanaVSC-...zip`) — misma causa raíz que `JUEGOS-FIX-4` parte 2 (residuo de un scan antiguo con `library_root` más amplio que la carpeta de ROMs real, nunca podado porque un scan con la raíz ya estrecha no visita rutas fuera de ella). Fuera de alcance de `ZIP-ROUTE-8`.
- **4** en `ROMS\_ARCADE_CONFLICTOS_REVISAR_MANO\_processed\` (sets arcade reales: `champglf`, `champtns`, `gpworlda`, `safarircj`) con `platform=NULL` — quedaron en el flujo manual de resolución de conflictos arcade sin plataforma asignada; menor, no urgente.
| ZIP-ROUTE-8 | **Excluir carpetas de instalación de emulador del scan** (hallazgo de `ZIP-ROUTE-7`, segunda mitad) — añadir nombres de carpeta de emulador conocidos a `excluded_directories` (`config.py:606-624`). Cubre los falsos positivos reales encontrados (BIOS/skins/cheats/patches tratados como ROM) | `config.py:606-624`, `detection/file_classifier.py:18-39` | ✅ hecho 2026-10-02 — `emulator_paths` solo mapea rutas Android (paquete→ruta de saves en el dispositivo), no instalaciones PC, así que no servía para derivar la lista; añadidos `Emuladores`/`DraStic`/`Duckstation`/`PCSX2` a la tupla ya existente (mismo patrón que el resto, comparación ya es case-insensitive vía `casefold()`). **`RetroArch` queda fuera a propósito**: CI reventó `test_scan_sd_card_path` (`tests/test_scanner.py`) porque es el nombre real de la raíz de ROMs en la SD de Android (`/storage/emulated/0/RetroArch`) — excluirlo habría roto el escaneo normal de cualquier SD de Anbernic. Cubre 7 de los 8 falsos positivos (queda sin resolver `E:\Emuladores\Retroarch\shaders\...\LICENSE.zip`, caso de borde aceptado). 4 casos nuevos en el `parametrize` de `test_excluded_directory` (`tests/test_file_classifier.py`), 51 pass. Las filas ya existentes en `library_pc.db` se autolimpian en el próximo scan completo de esa raíz (`prune_stale_entries` las verá como no-vistas); sin DELETE manual — los 3 archivos ajenos del Bootcamp y los 4 arcade `_processed` quedan fuera de alcance de esta tarea (causas distintas, ver detalle arriba) |
| ZIP-ROUTE-6 | **Colecciones con subcarpetas internas por sub-plataforma se extraen sin separar** — `_extract_collection` (`web/zip_router.py:47-72`) llama `zf.extract(m, dest_dir)` conservando la ruta interna de cada miembro (`m.filename`); para un contenedor plano (todos los `.zip` sueltos en la raíz, el único caso probado hasta ahora) da igual, pero para un bestset con subcarpetas por sub-sistema — caso real: `fbneo_1003_bestset` de archive.org, 4,67 GB / 636 sets bajo `games/<cps1\|cps2\|cps3\|neogeo\|fbneo\|toaplan_cave_stg>/` — el resultado sería `arcade/games/cps1/sf2.zip` en vez de separar por plataforma: mezcla cps1/cps2/cps3/neogeo (carpetas y sistemas Daijishō ya distintos hoy, ver `docs/arcade-setup.md`) todo anidado bajo `arcade/`, y `toaplan_cave_stg/` no tiene carpeta equivalente en la convención del proyecto. La clasificación previa (`_is_source_collection`) sí es correcta — cae en "Colección fuente (revisar)" como debe. Hallazgo del usuario 2026-08-28 con una descarga real, solo inspección de código + listado del ZIP (`Compress.ZipFile`), sin llegar a ejecutar el apply | `web/zip_router.py:47-72` (`_extract_collection`) | ✅ `docs/arcade-setup.md` confirma que la convención del proyecto es un único `arcade\` plano (un mismo core FBNeo cubre cps1/cps2/cps3/neogeo/cave) — la subcarpeta interna del ZIP nunca es una plataforma real, así que la carpeta más simple y correcta es aplanar, no mapear cada subsistema a un destino propio (esto también resuelve de paso el caso `toaplan_cave_stg` sin carpeta equivalente: deja de hacer falta un mapeo). `_extract_collection()` acepta `flatten: bool` — con `flatten=True` extrae cada miembro por su nombre base (`Path(m.filename).name`) directo bajo `dest_dir`, ignorando la ruta interna del ZIP; `_route_identified()` solo lo activa para el destino arcade (`is_arcade = _majority(stems, arcade_names)`), el destino Inbox conserva la ruta interna sin cambios (la necesita ZIP-ROUTE-FIX-3 para el contexto de carpeta). 2 tests nuevos en `tests/test_zip_router.py` (bestset con 4 subcarpetas → 4 archivos planos en `arcade/`, sin `arcade/games/`; colisión por nombre aplanado no sobreescribe). Solo verificado con datos sintéticos — sin biblioteca real montada en esta máquina. Suite completa 1222/1222 |

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
| INBOX-RA-HASH-GAP | Hallazgo derivado de INBOX-ORPHAN-4: `games.md5` (`hashing/hash_calculator.py:41`, `hashlib.md5()` sobre los bytes crudos del archivo) es un hash de **archivo completo**, pero el hash que usa RetroAchievements para GameCube/Wii (y cualquier formato de disco comprimido: RVZ, CHD) se calcula sobre datos específicos extraídos del **disco descomprimido** (boot.bin/apploader/dol vía `rc_hash`), no sobre el contenedor comprimido. Verificado contra `ra_cache/ra_hashes_16.json` (236 juegos, 332 hashes únicos): ninguno de los 8 md5 de las 4 parejas de INBOX-ORPHAN-4 aparece en la caché — ni la copia "buena" ni la "mala". Consecuencia real: `ra_duplicates_service.py` (`get_ra_achievements`, `apply_ra_conflicts`, `filter_duplicate_winners`) siempre devuelve -1 (sin RA) para cualquier `.rvz`/`.chd` de disco, aunque el juego sí tenga logros en RA — la comparación por RA solo funciona hoy para ROMs de cartucho sin comprimir. Implementar el hash real de RA para discos requeriría parsear el filesystem GameCube/Wii (o el `.chd`) para extraer las regiones exactas que hashea `rc_hash` — feature nueva, no un fix puntual. | `hashing/hash_calculator.py`, `services/ra_duplicates_service.py` (`get_ra_achievements`) | ✅ hecho 2026-09-15 (roadmap `17-inbox-pending-features.md`, rama `feature/inbox-ra-hash-gap`), con alcance acotado tras investigar (Paso 6): **algoritmo real** (`src/rhash/hash_disc.c` de rcheevos, descargado y leído verbatim, no resumido) reimplementado en `retroachievements/ra_hash_gamecube_wii.py` — GameCube hashea la cabecera del apploader + los 18 segmentos no vacíos de `main.dol`; Wii hashea cabecera principal + código de región + por partición (saltando la de tipo `1`, "update") la metadata (TMD) + los datos, leídos **sin necesidad de AES**: si el disco sigue cifrado, RA hashea los bytes cifrados tal cual (solo salta los 0x400 bytes de cabecera de hash de cada cluster de 0x8000) — solo si ya está descifrado se reusa el mismo algoritmo de apploader/DOL que GameCube, con el offset desplazado 2 bits. **Verificado con datos reales**: 2 de los 8 `.iso` de `gamecube/` (Wind Waker, Metroid Prime 2: Echoes) hashean exactamente al MD5 real cacheado en `ra_cache/ra_hashes_16.json` — mismo método de prueba que `ra_hash_psx.py`. GameCube es el confirmado; Wii se implementó fiel a la fuente pero **sin verificar contra datos reales** — esta biblioteca no tiene ningún disco Wii comercial (`wii/` solo tiene un WAD homebrew). **Alcance real acotado tras medir la biblioteca**: de 20 juegos en `gamecube/`, 15 son `.iso` (crudo, soportado) y 5 son `.rvz` (formato comprimido de Dolphin) — `.rvz` devuelve `None` deliberadamente, no hay herramienta de descompresión en este proyecto (a diferencia de `.chd`, que ya usa `chdman`) y añadir una violaría "sin dependencias externas de runtime". Integrado en `ra_checker.py` (`_DISC_HASH_CONSOLE_IDS` ahora incluye 16/20 además de 12) y en `ra_duplicates_service.py::get_ra_achievements_for_path` (usada por `apply_ra_conflicts`) — mismo patrón de caché por archivo que ya usaba PSX (`ra_disc_hash_cache.py`, nuevo `gamecube_wii_disc_hashes.json` separado). **Hallazgo colateral, arreglado 2026-09-15 (misma rama, a petición explícita del usuario)**: `filter_duplicate_winners` recibía cada entrada como un `dict` con `md5` ya calculado, sin pasar por `source_path` — parecía requerir cambiar su firma, pero los `dict` reales que le llega (`repository.get_games_paginated(...)`, el único caller real en `web/handlers/sync_cable.py`) **ya traen `source_path`**, solo que la función no lo usaba. Se añadió el mismo dispatch por `console_id` (PSX/GameCube/Wii → `get_ra_achievements_for_path`, el resto sigue usando el `md5` ya calculado sin consulta extra a la BD) dentro del propio `_key()` de la función, sin tocar su firma pública. 1 test nuevo (`test_ra_bulk_send_dedup.py`, GameCube con hash real vs. archivo no reconocido). 1340 tests totales, ruff+format limpios |
| INBOX-ORPHAN-5 | **Investigado 2026-09-08 contra `E:\Carpetas anbernic` real** — de las 9 carpetas display originales solo **5 siguen existiendo** (`Master System`, `Game Boy`, `Game Boy Advance`, `Game Boy Color` ya no están, limpiadas en algún momento entre el hallazgo y hoy, sin rastro de cuándo). De las 5 restantes, **no son todas del mismo caso** — comparado archivo por archivo (ruta relativa dentro de `media/`) contra la carpeta slug real: `Nintendo DS` (6 archivos) **sí es duplicado exacto** de `nds/media/images` — mismo nombre, ya presente, seguro de descartar. `Game Gear` (58: 29 imágenes+29 wheels), `Atari 2600` (12: 6+6), `NGC`→`gamecube` (42: 21+21) y `Famicom Disk System`→`fds` (4: 2+2) **NO son duplicados — son artwork real que falta en la carpeta slug**: confirmado que el ROM sí existe en la carpeta real (p. ej. `gamegear/Ristar (World).gg`, `atari2600/Asteroids (Japan, USA) (En).a26`, `gamecube/Pikmin (Europe)...iso`, `fds/Super Mario Bros. 2 (Japan) (En).fds`) pero su imagen no está en `<slug>/media/images/` — `gamecube/media/` y `fds/media/` ni siquiera existen hoy (0 imágenes para esas 2 plataformas en toda la biblioteca), y `gamegear`/`atari2600` solo tienen scrapeadas 239/1599 y 47/729 ROMs respectivamente. Cero colisiones de nombre entre orphan y real en los 4 casos (ninguna ruta relativa coincide), así que un merge sería seguro sin sobreescribir nada. Origen: casi seguro un scrape viejo hecho antes de renombrar esas carpetas al slug (ES-DE usaba el nombre display), nunca migrado. **Ejecutado 2026-09-08, con confirmación explícita del usuario antes del borrado**: movidas las 116 imágenes únicas (`Game Gear`→`gamegear` 58, `Atari 2600`→`atari2600` 12, `NGC`→`gamecube` 42, `Famicom Disk System`→`fds` 4) con `mv -n` (verificado después que las 4 carpetas quedaron con 0 archivos, ningún `mv` saltó por colisión); verificados los 6 archivos de `Nintendo DS` byte a byte (`cmp`) contra `nds/media/images` antes de darlos por duplicado exacto. Borradas las 5 carpetas display-name completas — ninguna contenía ROMs. Único efecto colateral esperado: `gamecube/media/` y `fds/media/` pasan de no existir a tener su primer artwork (42 y 4 archivos respectivamente); esas dos plataformas seguían con 0 imágenes en el resto de sus ROMs. Solo movimiento/borrado de archivos de artwork en el filesystem — sin tocar `library_pc.db`/`library_android.db` (la media no está indexada en SQLite). | `E:\Carpetas anbernic\{gamegear,atari2600,gamecube,fds,nds}\media\` | ✅ hecho 2026-09-08 |

---

### INBOX-ANBERNIC-1 — Checkbox opt-in en el Inbox para enviar el ROM recién organizado a la Anbernic (petición usuario 2026-09-12)

Plan de implementación (junto a `INBOX-ATOMIC-1` e `INBOX-RA-HASH-GAP`) en
`.claude/roadmaps/archivo/17-inbox-pending-features.md`.

Origen: conversación 2026-09-12 — el usuario preguntó si el Inbox podía pasar
juegos directamente a la Anbernic. Hoy el Inbox (Pilar 2) solo organiza en el
PC; llevar el juego a la consola exige pasar aparte por Juegos (marcar tag
`anbernic`, `ANBERNIC-PICK-1`) + Cable Sync (`ANBERNIC-PICK-2`) o por el botón
"Enviar" de Juegos (`ANBERNIC-PICK-8`, `direction="send_selected"` en
`_do_cable_sync`, `web/handlers/sync_cable.py`). Decisión explícita del
usuario: **no automático** — checkbox opt-in por corrida (o por archivo) en
la UI del Inbox, no un push silencioso de todo lo que se organiza.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| INBOX-ANBERNIC-1 | Checkbox "Enviar a la Anbernic tras organizar" en la pestaña Inbox — global por corrida (confirmado con el usuario 2026-09-17), opt-in, sin persistir entre corridas. En vez de reutilizar el job `direction="send_selected"` de `_do_cable_sync` (habría levantado un segundo panel de progreso, fuera de alcance), se reutiliza el primitivo de más bajo nivel `AdbTransport.push()` directamente dentro del propio job de Inbox — misma verificación MD5 condicional (`should_verify`), mismo registro en `save_sync_log` (`log_sync_event`). Nueva función `_send_organized_to_anbernic()` en `inbox_pipeline.py`, llamada al final del paso "organize" sobre la lista de archivos recién movidos con éxito. Sin dispositivo único conectado (`resolve_single_device_transport`): aviso (`anbernic_warning`), el resto del job de Inbox sigue igual. Cualquier fallo (push individual o resolución de dispositivo) queda capturado — nunca tumba el pipeline completo, que ya organizó con éxito en el PC. 4 tests nuevos (`test_inbox_anbernic_send.py`), 1347 tests totales, ruff+format limpios | `web/inbox_pipeline.py`, `web/handlers/inbox.py`, `web/static/partials/tab-inbox.html`, `web/static/js/tabs/inbox.js`, `tests/test_inbox_anbernic_send.py` | ✅ hecho 2026-09-17 (roadmap `17-inbox-pending-features.md`) |

---

### INBOX-ATOMIC-1 — Mover el archivo y actualizar la fila de BD no son atómicos en `_organize_matched_games` (hallazgo roadmap 08 `fix/error-handling`, 2026-09-13)

Origen: investigación del roadmap `.claude/roadmaps/archivo/08-fix-error-handling.md`
(hallazgo 3, revisión de bloques `except Exception` reales del proyecto).
Plan de implementación del fix en `.claude/roadmaps/archivo/17-inbox-pending-features.md`.
`inbox_pipeline.py` (paso "Move to platform folders"):

```python
try:
    _shutil.move(str(source_file), str(dest_file))
    dest_path_str = str(dest_file.resolve())
    with repository.batch() as conn:
        cascade_delete_games_by_source_path(conn, dest_path_str, exclude_id=game_id)
        conn.execute(
            "UPDATE games SET source_path=?, original_filename=? WHERE id=?",
            (dest_path_str, dest_file.name, game_id),
        )
    organized += 1
except Exception as exc:
    organize_errors.append(f"{source_file.name}: {exc}")
```

Si `_shutil.move` tiene éxito pero el `UPDATE`/`cascade_delete` que sigue
falla (SQLite bloqueada, disco lleno, lo que sea), el archivo físico ya está
en `dest_file` pero la fila de `games` **sigue apuntando al `source_path`
viejo dentro del Inbox, que ya no existe**. Viola "toda operación sobre
archivos se registra en SQLite" (`CLAUDE.md`) de forma silenciosa: el
usuario solo ve `"nombre.zip: <mensaje de excepción sqlite>"` en
`organize_errors` — nada le dice que el archivo SÍ se movió y que ahora hay
un descuadre real entre disco y BD para ese juego concreto. No es un caso de
"excepción tragada" (el error llega a la UI), es un **hueco de atomicidad**
con un mensaje de error que no transmite el riesgo real.

**Arreglado 2026-09-15** — el código ahora invierte el orden y mete el move
dentro del propio bloque `batch()`:

```python
try:
    dest_path_str = str(dest_file.resolve())
    with repository.batch() as conn:
        cascade_delete_games_by_source_path(conn, dest_path_str, exclude_id=game_id)
        conn.execute(
            "UPDATE games SET source_path=?, original_filename=? WHERE id=?",
            (dest_path_str, dest_file.name, game_id),
        )
        _shutil.move(str(source_file), str(dest_file))
    organized += 1
except Exception as exc:
    organize_errors.append(f"{source_file.name}: {exc}")
```

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| INBOX-ATOMIC-1 | Decidir la política: (a) reintentar el `UPDATE`/`cascade_delete` en un `finally` separado antes de dar el archivo por fallido, (b) revertir el `_shutil.move` (mover el archivo de vuelta al Inbox) si el paso de BD falla, o (c) como mínimo, mejorar el mensaje de `organize_errors` para que nombre explícitamente el riesgo real (`"archivo movido a {dest_file} pero la base de datos no se pudo actualizar — revisar a mano"`) en vez del mensaje crudo de la excepción SQLite. No implementar sin decisión explícita del usuario — cambia el comportamiento del Pilar 2 en el camino de fallo | `web/inbox_pipeline.py` (paso "Move to platform folders") | ✅ hecho 2026-09-15, a petición explícita del usuario (rama `feature/inbox-atomic-1`). Variante de (a) más simple que reintentar en un `finally`: se invierte el orden (`UPDATE`/`cascade_delete` primero, `_shutil.move` al final) **dentro del mismo bloque `repository.batch()`** — una excepción en cualquier punto del bloque (incluido el propio move) hace que `batch()` haga rollback de la BD antes de propagar, así que un fallo del move deja la fila tal y como estaba (apuntando a donde el archivo sigue estando de verdad), y un fallo de la BD nunca llega a intentar el move. Único hueco residual no evitable sin una transacción distribuida real: que el `commit()` en sí falle *después* de un move ya exitoso (ej. disco lleno en el commit) — caso mucho más raro que el original (que se disparaba con cualquier fallo de BD tras el move). 2 tests nuevos (`test_inbox_pipeline_organize.py`: fallo del move tras el `UPDATE` revierte la BD; fallo de la BD nunca llega a llamar al move), 1332 tests totales, ruff+format limpios |

---

### INBOX-UX — Cierre visible de sesión y metadata al vuelo (idea usuario 2026-09-22)

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| INBOX-SESSION-SUMMARY-1 | Resumen visible al terminar un job de Inbox/organize (N organizados, N con conflicto, N sin match) en vez de tener que revisar logs | `web/inbox_pipeline.py`, `web/static/js/tabs/inbox.js` | ✅ hecho 2026-09-22 (rama `feature/inbox-ux-summary-metadata`) — investigado primero: el panel de resumen (`_renderInboxResult`) y casi todos los contadores ya existían; solo faltaba destacar "sin match" (`unmatched`, juegos organizados sin `platform`), añadido junto a `scraped` |
| INBOX-METADATA-INLINE-1 | Confirmar si portada/metadata ya se aplican automáticamente al organizar desde el Inbox (el scraper existe pero no está claro si dispara en el mismo job); si no, integrarlo | `services/scrape_service.py` (nuevo), `web/inbox_pipeline.py`, `web/handlers/scraper.py`, `config.py` | ✅ hecho 2026-09-22 — confirmado que no se aplicaba automáticamente. `_do_scrape_single` extraído a `scrape_game_metadata()` (servicio reutilizable, sin `ctx` HTTP) y enganchado al organize vía `_scrape_organized_games()`, opt-in (`config.inbox.scrape_on_organize`, apagado por defecto). Un solo `ScreenScraperClient` para todo el lote (su throttle es por instancia). 12 tests nuevos, 1452 pass, ruff+format limpios |

---

---

## Pilar 3 — Sync de saves PC ↔ Anbernic — → #204

Jugar en cualquiera de los dos lados y que la partida aparezca sola en el
otro, sin miedo a sobrescribir — el valor diferencial real del proyecto.

### NATIVE-SAVE-SYNC-1 — Estructura RetroVault en E:\ + sync de saves de juegos nativos (petición usuario 2026-09-26)

Petición del usuario: unificar en `E:\RetroVault\` la biblioteca, los
emuladores, ES-DE y los "juegos nativos" (ports PC hechos por la comunidad
de juegos de consola — p. ej. Twilight Princess vía **Dusklight**, que lee
el ISO original en vivo en vez de traer sus propios assets), y sincronizar
también las partidas de esos juegos nativos a Dropbox, no solo las de
RetroArch/DuckStation/PCSX2/Dolphin.

Al investigar antes de mover nada se descubrió que **no era crear carpetas
vacías**: `E:\Carpetas anbernic` era el `library_root` real en uso
(36.271 ROMs en BD), `E:\Emuladores` tenía las instalaciones reales de
RetroArch/Dolphin/DuckStation/PCSX2/etc., y `E:\Emulation Station` resultó
ser un build de 2014 de EmulationStation (Aloshi) abandonado — el ES-DE real
está instalado en `C:\Program Files\ES-DE` (fuera de alcance de este move,
con datos de usuario en `C:\Users\rammu\ES-DE\`), pendiente de decidir con
el usuario si esa carpeta vieja se borra o se deja.

Hecho: **(1)** `E:\Carpetas anbernic` → `E:\RetroVault\ROMS`,
`E:\Emuladores` → `E:\RetroVault\EMULADORES`, `E:\Juegos nativos` →
`E:\RetroVault\JUEGOS NATIVOS` (move a nivel de archivo vía
`robocopy /MOVE`, con backup previo de `library_pc.db`/`library_android.db`/
`config.toml`/`retroarch.cfg` en `.rommgr/backup_pre_retrovault_move/`).
Bloqueante real durante el move: **Dusklight** tenía abierto en vivo
`gamecube\Legend of Zelda, The - Twilight Princess (Europe)...iso` — el
`robocopy` movió todo lo demás y dejó ese único archivo atrás hasta que el
usuario cerró el juego. **(2)** Reescritas 129.654 filas en `library_pc.db`
(`games.source_path`, `saves.original_path`, `assets.source_path`,
`file_operations.source_path/target_path`, `save_sync_log.local_path`,
`scan_runs.source_root`, `game_metadata.box_art_path/wheel_path`) con el
prefijo `E:\Carpetas anbernic` → `E:\RetroVault\ROMS`, en una única
transacción con verificación de 0 filas restantes antes del commit +
comprobación de que las rutas migradas existen en disco. **(3)** Reescritas
las rutas absolutas en `config.toml` (`library_root`, `inbox.path`,
`launchers.retroarch`, `sync.sources` de RetroArch) y en las configs propias
de cada emulador/frontend: `C:\Users\rammu\ES-DE\settings\es_settings.xml`
(`ROMDirectory`), `retroarch.cfg` (`savefile_directory`/`savestate_directory`),
`DuckStation\settings.ini` (4 rutas), `PCSX2\inis\PCSX2.ini` (4 rutas),
`ppsspp.ini` (`CurrentDirectory`), `Dolphin.ini` (3× `ISOPath*` +
`MemcardAPath`) — ninguna de ellas se detecta ni se corrige sola, cada
emulador guarda su propia copia de la ruta absoluta. **(4)** Nueva entrada
`[[sync.sources]]` para Dusklight: `local_dir` apunta a
`%APPDATA%\TwilitRealm\Dusklight\EUR` (el `.gci` de memory card,
`EUR\Card A\01-GZ2P-gczelda2.gci`, mismo patrón que las memcards de Dolphin
GC), `remote = "dropbox:/RetroSync/saves/native/dusklight"`,
`sync_all = true` — reutiliza el motor de sync existente (`save_syncer.py`)
sin código nuevo, exactamente igual que cualquier otra fuente de la lista.

**Pendiente / hallazgo para otra sesión**: no hay UI todavía para añadir
`[[sync.sources]]` — `sync.js` ya avisa que el modo multi-fuente es
"avanzado, vía config.toml" (línea 74). Añadir un juego nativo nuevo hoy
significa (a) localizar a mano su carpeta de save (varía por juego:
`Documents\My Games\...`, `%APPDATA%\<Estudio>\<Juego>\...`, junto al .exe)
y (b) editar `config.toml`. Sería razonable un formulario en la pestaña Sync
para esto — no implementado, sin ID de tarea todavía. **(5)** `E:\Emulation
Station\` (el EmulationStation 2014 abandonado, sin relación con el ES-DE
real) — borrado a petición del usuario, no aportaba nada y confundía el
nombre con la carpeta `ES-DE` real (`C:\Users\rammu\ES-DE\`).

**(6)** Petición de seguimiento del usuario: aplicar lo mismo a la otra
máquina y que la app cree esta estructura sola. `wizard.py`
(`_ensure_retrovault_structure`, llamada desde `run_wizard` tras pedir la
carpeta raíz) ahora crea `<carpeta elegida>` + hermanas `EMULADORES`/
`JUEGOS NATIVOS` bajo el mismo padre en cualquier instalación nueva (`rommgr
init-config`) — cubre el caso "primera vez" en una máquina nueva, con test
(`tests/test_wizard_retrovault.py`). Para una máquina que **ya** tiene
biblioteca (el caso real de la otra máquina, PC2 "Ruben" con RetroArch en
`F:\Emuladores\Retroarch`), el wizard no aplica — se generalizó el
procedimiento manual de este hallazgo en `scripts/migrate_to_retrovault.py`
(backup, `robocopy /MOVE`, reescritura de `library_pc.db` + `config.toml` +
las mismas 6 configs de emulador, dry-run por defecto) para que se ejecute
allí sin repetir la investigación a mano — no se ha ejecutado contra esa
máquina porque esta sesión no tiene acceso a ella.

**(7) Dusklight en esta máquina (2026-09-28)**: petición del usuario de
traer el save de Dropbox — investigado antes de tocar nada. **No hay nada
que traer**: `dropbox:/RetroSync/saves/` solo tiene `dolphin`/`duckstation`/
`pcsx2`/`retroarch`, sin `native/` — el save de Dusklight de rammu nunca
llegó a subirse de verdad (solo se añadió la entrada de config, no se
confirma un `sync --apply` real con datos). Tampoco hay save local todavía
en esta máquina (`%APPDATA%\TwilitRealm\Dusklight\` existe, instalación
reciente, sin ninguna carpeta de región/`.gci`). `rommgr sync` (dry-run)
del resto de fuentes confirmó todo al día (↑2 ↓0, 0 conflictos, 0 errores)
— Pilar 3 sano en esta máquina, nada perdido. Añadida la entrada
`[[sync.sources]]` para Dusklight en `config.toml` (gitignored, solo local)
apuntando a `...\Dusklight\USA` — **región inferida sin verificar** (la ISO
de esta biblioteca es (USA), no (Europe) como en rammu; corregir
`local_dir` si el nombre real de carpeta resulta ser otro) — listo para
cuando el juego cree el save real.

### EMU-SYNC-WATCH-1 — Cloud sync automático al cerrar un emulador PC (petición usuario 2026-09-19, máquina "Ruben" = PC2)

Petición del usuario: quiere sync entre sus 3 dispositivos (PC principal,
PC2 — esta máquina — y Anbernic). Al revisar el estado real: cable-sync
PC↔Anbernic y la app Android nativa (`ANDROID-SYNC`) ya están completos en
código; lo que faltaba en este PC2 era (a) el primer sync real contra
Dropbox (nunca se había hecho — cuenta correcta pero vacía, confirmado por
el usuario) y (b) RetroArch, recién instalado a petición del usuario
(`F:\Emuladores\Retroarch`, build standalone vía instalador gráfico oficial),
sin `[[sync.sources]]` configuradas todavía.

Hecho: **(1)** primer sync real de este PC2 ejecutado (`rommgr sync --apply`)
— 6 archivos subidos (Dolphin Wii, DuckStation, PCSX2), 0 errores, verificado
en Dropbox. **(2)** `[[sync.sources]]` de RetroArch (saves/states) + `[launchers] retroarch`
añadidas a `config.toml` de este PC2 (gitignored, no en el PR). **(3)**
`EMU-SYNC-WATCH-1`: petición explícita del usuario de que el sync se dispare
solo al cerrar RetroArch/PCSX2/DuckStation/Dolphin, no solo manual/al abrir
la app — daemon nuevo `_emulator_sync_watcher_loop` (`web/daemons.py`), opt-in
vía `config.sync.watch_processes` (vacío = desactivado), sondea `tasklist`
cada 10s (stdlib, sin dependencia nueva) y lanza el job `sync` existente al
detectar que un proceso vigilado pasó de corriendo a cerrado. Refactor previo
sin cambio de comportamiento: la lógica de `POST /api/sync` (antes un closure
anónimo en `_do_sync`) se extrajo a `run_cloud_sync_job()`
(`web/handlers/sync_cloud.py`), compartida ahora por el endpoint web y el
daemon nuevo.

**Descartado explícitamente**: el mismo patrón para la Anbernic (Android) —
requeriría un servicio en segundo plano + permiso especial `PACKAGE_USAGE_STATS`
(concesión manual en Ajustes), justo el patrón de daemon que `ANDROID-SYNC-9/10/11`
ya descartó a propósito por batería/complejidad. El sync periódico cada 15 min
que ya existe (`ANDROID-SYNC-12`) cubre el caso de uso sin ese coste | `web/daemons.py`
(`_emulator_sync_watcher_loop`, `_list_running_process_names`,
`_closed_watched_processes`), `web/handlers/sync_cloud.py` (`run_cloud_sync_job`,
extraída de `_do_sync`), `config.py` (`SyncConfig.watch_processes`) | ✅ mergeado
a `develop` (PR #321, 2026-09-19), 6 tests nuevos, 1355 tests totales. ✅
**verificado en vivo el mismo día**: partida real de Dragon Ball Budokai 3 en
PCSX2 → al cerrar el emulador, log `Emulador cerrado (pcsx2-qt.exe) —
lanzando cloud sync` 3s después → `Mcd001.ps2` subido a Dropbox con el
timestamp exacto del cierre, 0 errores. **Tarea programada de Windows**
(`RetroVault-AutoStart`, `pythonw.exe -m rom_manager serve --tray` al inicio
de sesión) creada y probada (`Start-ScheduledTask`) para que el watcher esté
vivo sin depender de arrancar `serve` a mano. **12 cores de RetroArch**
instalados según `platforms.toml` (`[cores.pc]`, primera opción documentada
por plataforma) directo del buildbot oficial de libretro, sin pasar por el
Online Updater: `fceumm`/`snes9x`/`mupen64plus_next`/`gambatte`/`mgba`/
`melonds`/`genesis_plus_gx`/`flycast`/`mame`/`fbneo`/`ppsspp` + `pcsx_rearmed`
para PSX (`duckstation` ya no existe en el buildbot — el fork activo es
`swanstation` — se usó la 2ª opción documentada). GameCube/Wii/3DS/PS2
deliberadamente fuera (usan los standalone ya configurados, no RetroArch) |

### CABLE-SYNC-WATCH-1 — Cable-sync automático al cerrar un emulador en la propia Anbernic (petición usuario 2026-09-19, PC2, con la RG556 conectada)

Petición del usuario: ahora que la Anbernic estaba conectada por USB, ¿el
mismo patrón de `EMU-SYNC-WATCH-1` pero para el lado Android? La razón por la
que ese roadmap **descartó explícitamente** un daemon en el propio
dispositivo (servicio + permiso `PACKAGE_USAGE_STATS`, mismo coste que
`ANDROID-SYNC-9/10/11` ya rechazó) no aplica aquí: el sondeo lo hace el PC
por ADB, no un servicio en el móvil — mismo principio que ya usa
`_auto_sync_loop` para detectar la propia conexión del cable, solo que ahora
también sondea qué paquete Android sigue vivo. Cero coste cuando el cable
está desconectado (ahí sigue cubriendo el caso de uso el sync periódico de
`ANDROID-SYNC-12`).

Extiende `_auto_sync_loop` (`web/cable_sync_daemon.py`, ya sondeaba ADB cada
10s para detectar conexión) para también sondear `adb shell ps -A` en busca
de paquetes vigilados (`config.sync.watch_android_packages`, opt-in, vacío =
desactivado — mismo patrón que `watch_processes`) y lanzar un cable-sync real
al detectar que uno se cerró, reutilizando `_closed_watched_processes()` de
`daemons.py` (misma función genérica de `EMU-SYNC-WATCH-1`, sin duplicar
lógica). `serial`/`reason` generalizados en el bucle para que la conexión y
el cierre de emulador compartan exactamente el mismo camino de disparo
(guard de reloj, prompt si auto-sync está desactivado, cooldown...).

**Hallazgo real de paso**: `EMULATOR_SAVE_PATHS_DEFAULT["com.retroarch.aarch64"]`
(`config.py`) llevaba el paquete equivocado — `docs/emulador-canonico-rg556.md`
(investigación previa, mismo dispositivo) ya había determinado que el
RetroArch real en uso es `com.retroarch` (19h28m de partida real frente a 2 min
del `.aarch64`), pero la tabla nunca se actualizó con esa decisión. Sin este
fix, la detección por nombre de paquete nunca habría encontrado el proceso
real. Corregido | `web/cable_sync_daemon.py` (`_list_running_android_packages`,
`_auto_sync_loop`), `config.py` (`SyncConfig.watch_android_packages`,
`EMULATOR_SAVE_PATHS_DEFAULT["com.retroarch"]` corregido) | ✅ 4 tests nuevos
(`test_cable_sync_android_watch.py`), 1374 tests totales, ruff limpio.
**Verificado en vivo contra la RG556 real** (serial `RG556006101273`, conectada
por USB): lanzado `com.retroarch` por ADB, confirmado corriendo (`ps -A`),
cerrado con `am force-stop` — log real: `Auto-sync: emulador Android cerrado
(com.retroarch) en RG556006101273 — lanzando sync`, cable-sync disparado y
completado (`cable_sync_ops.log`, `copied=5, errors=11` — los errores son
carpetas privadas de otras apps sin permiso de lectura vía ADB sin root, ya
documentado como limitación conocida en varias entradas de `EMULATOR_SAVE_PATHS_DEFAULT`,
no un fallo de esta feature). Sin PR todavía |

### ANDROID-SYNC — App Android nativa de sync de saves (diseño 2026-08-18)

→ #374

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
| ANDROID-SYNC-9 | `SaveFileObserverManager`: `FileObserver` multi-path, debounce | 3 — Instantáneo | M | ✅ **implementado y validado en hardware real 2026-09-25** — el usuario confirmó explícitamente el cambio de postura de producto (ya no es solo complemento del PC) antes de tocar código. Un `FileObserver` por cada subcarpeta ya existente bajo `saves/`/`states/` (no recursivo nativamente, ver `collectWatchDirs` — pure, testeado en JVM); debounce 3s con `Handler`, no coroutines. **Ceiling conocido** (comentario `ponytail:` en el código): un core nuevo que aparezca después de arrancar el servicio no se observa hasta el próximo restart — no hay watch dinámico de carpetas nuevas. `SaveFileObserverManagerTest` (JVM) cubre el recorrido. Validado en la RG556 real (ver `ANDROID-SYNC-10`): disparo por `adb push`/borrado real detectado con la app en background y con la pantalla apagada 10 min |
| ANDROID-SYNC-10 | `SyncForegroundService` + notificación | 3 — Instantáneo | S | ✅ **implementado y validado en hardware real 2026-09-25** — servicio foreground (`foregroundServiceType="dataSync"`, API 34+), notificación persistente reutilizando `ic_launcher_foreground` (sin asset nuevo), `START_STICKY`. Dispara `SyncOrchestrator.runFullSync(..., SyncTrigger.INSTANT)` en el callback debounced de `SaveFileObserverManager`. Toggle en Ajustes (`SettingsRepository.instantSyncEnabled`) independiente del sync periódico (12) — **a propósito no mutuamente excluyentes**: el periódico queda como red de seguridad si el foreground muere. **Riesgo real sin validar**: gestores de batería agresivos (RG556 y similares) pueden matar el servicio con la pantalla apagada sin avisar — no se puede afirmar "instantáneo" sin matices hasta probarlo en el dispositivo real. Checklist generado con el agente `hardware-validator`: `Tareas/Validacion-Sync-Instantaneo-Historial.md` (10 pasos). **Estado real tras 3 intentos de ejecución en la RG556 el 2026-09-25**: los dos primeros bloqueos (pantalla bloqueada; luego el bug `ANDROID-SYNC-FIX-2`) ya están resueltos — el fix de `ANDROID-SYNC-FIX-2` está confirmado funcionando en vivo (app arranca sin crash, `ps -A` con proceso estable, sin `FATAL`/`AndroidRuntime` en logcat, permiso de notificaciones concedido con éxito por UI automation). **Tercer bloqueo, esperado y no un bug nuevo**: el fix de `ANDROID-SYNC-FIX-2` borra el `EncryptedSharedPreferences` corrupto como parte de su recuperación, así que el token OAuth de Dropbox que ya estaba conectado en la RG556 se perdió con él — Ajustes ahora muestra "No conectado". Los pasos 2-10 del checklist (todo lo que dispara un sync real) necesitan Dropbox conectado, así que la validación completa sigue pendiente hasta que el usuario reconecte Dropbox a mano en el dispositivo (login OAuth, no automatizable — regla ya establecida en `Tareas/Roadmap-Android-Sync.md` §6, sin QR/emparejamiento). `screen_off_timeout` del dispositivo quedó en 1800000ms (30 min) de intentos anteriores — valor original desconocido, no tocado en esta pasada.

**Retomado el mismo día tras reconexión manual de Dropbox por el usuario (login OAuth
en el dispositivo)** — resultado real de los 10 pasos, verificado por `adb`/SQL
directo contra `retrovault.db`/`-wal` (no por la UI, ver bloqueo nuevo abajo):
Paso 1 no aplica (reinstall limpio, `sync_history` ya existe desde el primer
arranque). **Paso 5 ✅ PASS**: notificación real confirmada por
`dumpsys notification --noredact` (título "Retro Vault Sync", texto "Vigilando
saves y states para sincronizar al instante", canal `instant_sync` importancia
2/LOW) + `SyncForegroundService` vivo en `dumpsys activity services`. **Paso 6 ✅
PASS**: `adb push` a `saves/Snes9x/` (carpeta preexistente) disparó un sync real;
tardó ~5,5 min en insertar la fila de historial (no los 3-4s documentados) porque
era el primer sync real de esta instalación — el reinstall de `ANDROID-SYNC-FIX-2`
también había borrado `sync_watermark` junto con las credenciales, así que tuvo
que subir de golpe toda la biblioteca nunca sincronizada (`sync_history`:
`trigger=INSTANT, uploaded=237, downloaded=1, errorCount=0`) — no es un bug, es el
catch-up inicial esperado. **Paso 8 (el crítico) ✅ PASS DEFINITIVO, sin necesitar
whitelist (8c)**: primer intento con sondeo `adb` cada 30s durante los 10 min
despertó la pantalla por sí solo (confirmado por ráfagas
`PowerManagerService: userActivityNoUpdateLocked` justo en la ventana de cada
sondeo — artefacto de la propia metodología de comprobación, no un hallazgo de
batería real, descartado). Repetido limpio — pantalla apagada, `adb push` de un
archivo de prueba, y **cero comandos adb durante los 10 minutos completos** (solo
espera pura): al terminar, pantalla seguía "Asleep", servicio y proceso vivos,
notificación presente, y 2 filas nuevas de historial "Instantáneo" con timestamp
dentro de la ventana dormida (sync completado mientras la pantalla estaba
realmente apagada, sin tocar el dispositivo en ningún momento).
`dumpsys deviceidle whitelist | grep retrovault` vacío — el modo Instantáneo
sobrevive 10 min reales de pantalla apagada en la RG556 de fábrica, sin
necesidad de eximirlo del gestor de batería. (`dumpsys deviceidle get deep` =
ACTIVE toda la prueba — Doze no llegó a activarse, probablemente por la
depuración USB conectada; el resultado positivo cubre el gestor de batería del
fabricante en 10 min de pantalla apagada, no un Doze profundo aislado). **Paso 9
✅ PASS**: `am force-stop` mató servicio y proceso (confirmado ausentes),
relanzado con `monkey -c android.intent.category.LAUNCHER` → `SyncForegroundService`
reaparece solo (`MainActivity.kt:87-92` funciona), sin volver a tocar el switch.
**Retomado por segunda vez el mismo día (2026-09-25), autorizado explícitamente por
el usuario** — se arregló primero `ANDROID-SYNC-FIX-3` (scroll) y se añadió un
indicador de estado en vivo (`SyncOrchestrator.isSyncing: StateFlow<Boolean>`,
notificación dinámica "Vigilando…"/"Sincronizando…") a petición del usuario ("no
podemos solo inferir qué está pasando"). Con eso, `uiautomator`/`input tap` sí
llegan a los controles reales (sin coordenadas ciegas). **Paso 2 ✅ PASS**: tap en
"Sincronizar ahora" → notificación cambió a "Sincronizando…" en vivo (confirmado por
`dumpsys notification`) y apareció la fila "Manual" en el historial de la propia UI.
**Paso 3 ✅ PASS**: switch "Sync automático" activado por tap, diagnóstico de
WorkManager devolvió `periodic_dropbox_sync` (`RUNNING`). **Paso 7 ✅ PASS**: ambos
switches (`Sync automático` + `Sync instantáneo`) confirmados `checked="true"`
simultáneamente por `uiautomator dump`, ninguno desactivó al otro. **Paso 10 ✅
PASS** (`adb reboot` autorizado por el usuario): tras el boot, el servicio NO
arrancaba y `run-as` fallaba con `couldn't stat /data/user/0/...` —
`dumpsys user` reveló la causa real: `State: RUNNING_LOCKED` (almacenamiento
cifrado del usuario 0 sin desbloquear tras el reboot; un receiver normal no recibe
`BOOT_COMPLETED` hasta el primer desbloqueo real de pantalla — comportamiento
esperado de Android FBE/CE, no un bug). En cuanto el usuario desbloqueó la
pantalla a mano (`RUNNING_UNLOCKED`), `SyncForegroundService` apareció solo en
`dumpsys activity services` con `code:BOOT_COMPLETED`, sin abrir la app — confirma
que `BootRestartReceiver` funciona correctamente una vez el almacenamiento está
disponible. **Paso 4 (conflicto/error) sin ejecutar** — sigue siendo best-effort/no
bloqueante por diseño del checklist, pendiente si se quiere cerrar por completitud.
**Checklist completo (excepto Paso 4) en verde.** Dispositivo quedó con ambos
switches ON, historial con filas Manual/Automático/Instantáneo mezcladas, archivos
de prueba limpiados. Detalle paso a paso en
`Tareas/Validacion-Sync-Instantaneo-Historial.md` |
| ANDROID-SYNC-11 | `BootRestartReceiver` | 3 — Instantáneo | XS | ✅ **implementado y validado en hardware real 2026-09-25** — relanza `SyncForegroundService` tras `BOOT_COMPLETED` si `instantSyncEnabled` seguía activo. Permisos `FOREGROUND_SERVICE`/`FOREGROUND_SERVICE_DATA_SYNC`/`RECEIVE_BOOT_COMPLETED` (retirados en ANDROID-SYNC-12) devueltos al manifest con la justificación actualizada. `./gradlew testDebugUnitTest`/`assembleDebug` en verde. **Reboot real en la RG556** (`adb reboot`, autorizado por el usuario): el servicio no arranca hasta que el usuario desbloquea la pantalla por primera vez tras el boot (almacenamiento cifrado del usuario en `RUNNING_LOCKED` hasta entonces — comportamiento esperado de Android, no un bug); en cuanto se desbloquea, `SyncForegroundService` aparece solo con `code:BOOT_COMPLETED`, sin abrir la app — confirmado con `dumpsys activity services`/`dumpsys user` |
| ANDROID-SYNC-12 | `SyncWorker` (`CoroutineWorker`, 15 min mínimo, `NetworkType.CONNECTED`) + interruptor en Ajustes | 4 — Periódico | S | ✅ rama `feature/android-sync-12-periodic-sync` (PR #237) — `SyncOrchestrator` (nuevo, dependencias de `SyncEngine`/Dropbox/settings construidas desde un `Context`, punto compartido entre "Sincronizar ahora" y `SyncWorker`), `SyncWorker`/`PeriodicSyncScheduler`, `autoSyncEnabled` en `SettingsRepository`, interruptor en `SettingsScreen` (con la fase instantánea descartada, el "selector de modo" se simplifica a on/off). Permisos muertos de 9/10/11 (`FOREGROUND_SERVICE*`, `RECEIVE_BOOT_COMPLETED`) retirados del manifest. Verificado con `./gradlew test` y `./gradlew assembleDebug` reales (toolchain portable instalado en esta máquina, ver `Tareas/Roadmap-Android-Sync.md` §8) — ambos en verde, incluye 2 tests JVM nuevos de `SyncResult.plus()`. Falta el flujo manual en emulador/dispositivo (checklist: `Tareas/Validacion-ANDROID-SYNC-12.md`) |
| ANDROID-SYNC-13 | ~~`DeltaCache` (SHA1 skip-si-no-cambió)~~ | 5 — Optimización | S | ❌ descartado — optimización prematura sin datos de uso real que la justifiquen |
| ANDROID-SYNC-14 | Pantalla de estado/historial | 5 — Optimización | S | ✅ **reabierto y hecho 2026-09-25** (razón original ya no aplica — se necesita depurar fallos de sync). `SyncHistoryEntity`/`SyncHistoryDao` (Room, migración aditiva 1→2 en `AppDatabase`, no destruye `sync_watermark`) + `SyncOrchestrator.runFullSync(context, trigger: SyncTrigger)` graba un evento por pase (MANUAL/PERIODIC), cubre "Sincronizar ahora" y `SyncWorker` desde el mismo punto de entrada. `SettingsScreen` lista los últimos 10 eventos con `StatusBadge` (tono por `SyncOutcome`: éxito/conflictos/errores). Solo lectura, sin edición/borrado (alcance mínimo pedido). `SyncHistoryEntityTest` (JVM) cubre `outcome()`/`summary()`. Verificado con `./gradlew testDebugUnitTest` y `assembleDebug` reales — ambos en verde |
| SYNC-STRUCT-RAMMU-1 | Ejecutar en esta máquina (rammu) el checklist de `Tareas/Estructura-Estandarizada-Sync.md`, diseñado 2026-09-19 sin acceso a ella — petición del usuario 2026-09-22 ("algo más que podamos ir haciendo con respecto a la app [Android]") | `config.toml`, `retroarch.cfg` | ✅ **hecho 2026-09-22** — 6/7 puntos del checklist confirmados u OK de antes (convención `dropbox:/RetroSync/saves/<emulador>/<tipo>` ya aplicada en `[[sync.sources]]` y `saves_remote`/`states_remote`, slugs de plataforma en minúscula). **Bug real encontrado y arreglado**: `GET /api/retroarch-check` reportó `savefile_drift: true` — `savestate_directory` en `retroarch.cfg` corrupto (`":\states"`, sin unidad) desde al menos marzo. Corregido con `POST /api/retroarch-apply-savefile-layout` (backup automático `retroarch.cfg.bak`). Con la ruta rota, RetroArch llevaba escribiendo savestates en su propio fallback (`E:\Emuladores\Retroarch\states\`, 9 cores, actividad hasta el día anterior) — **nunca respaldados en Dropbox**. Migrados (copiados, sin borrar el origen) a `E:\Carpetas anbernic\states\`. Retirada `MelonDS (NDS)` de `[[sync.sources]]` (`local_dir` apuntaba a una carpeta inexistente, app no instalada en este PC — confirmado por el usuario). **`rommgr sync --apply` real ejecutado** (confirmado por el usuario): 14 archivos subidos a Dropbox (incluye los savestates recién migrados), 0 descargados, 0 conflictos, 0 errores; re-verificado tras retirar MelonDS: 255/255 ya al día, 0 errores. Punto 7 original del checklist (comparar contra PC2/Ruben) sin hacer, no hay acceso a esa máquina desde aquí. Desbloquea el round-trip real de `ANDROID-SYNC-15` (solo falta interacción manual del usuario en el dispositivo — login Dropbox en la app) |
| ANDROID-SYNC-15 | Checklist RG556: instalar, permisos, anidado real por-core, round-trip cruzado con `rommgr sync-saves`, reboot, batería | 6 — Validación hardware | M | 🟡 en progreso (2026-09-19, RG556 ya conectada) — checklist completo en `Tareas/Validacion-ANDROID-SYNC-15.md` (generado con el agente `hardware-validator`). Permisos comprobados en vivo: `MANAGE_EXTERNAL_STORAGE: allow`; `POST_NOTIFICATIONS` declarado pero no concedido (la app tiene banner propio para pedirlo, sin acción todavía). Confirmado por `dumpsys package` que la build instalada (v0.1.0) no tiene `SyncForegroundService`/`BootRestartReceiver` — el recorte de alcance de 2026-08-18 (solo sync manual + periódico) sigue vigente, los pasos de reboot/batería del checklist genérico hay que adaptarlos a eso. Round-trip cruzado con `rommgr sync-saves`, reboot y batería sin ejecutar todavía — pospuesto a propósito hasta aplicar `Tareas/Estructura-Estandarizada-Sync.md` en rammu, para no repetir la validación tras alinear rutas. **Prerrequisito cumplido 2026-09-22** (ver `SYNC-STRUCT-RAMMU-1`) — el checklist de estandarización ya está ejecutado en esta máquina, desbloqueado seguir con el round-trip real cuando el usuario esté delante del dispositivo (login Dropbox en la app, no automatizable) |
| ANDROID-SYNC-FIX-1 | **Bug: el primer sync de una cuenta/carpeta Dropbox nueva fallaba siempre** — `DropboxTransport.listFolderRecursive()` propagaba `ListFolderErrorException` (`path/not_found`) como error fatal cuando la carpeta remota simplemente no existe todavía (cuenta nueva, nunca se subió nada ahí); eso es un listado vacío legítimo, no un fallo. Sin este fix ningún usuario Android nuevo podía completar su primer sync. Hallado validando Dropbox sync a mano contra una cuenta real (AVD `retrovault_test`, API 34) | `android/app/src/main/java/com/retrovault/android/sync/DropboxTransport.kt` | ✅ captura `ListFolderErrorException` y devuelve lista vacía si `errorValue.isPath && errorValue.pathValue.isNotFound`; cualquier otro error se relanza igual que antes. Verificado contra la cuenta real: antes "Errores: 2", después "Errores: 0" |
| ANDROID-SYNC-FIX-2 | **Bug: la app crashea en cada arranque tras reinstalar (release↔debug o restore de backup) — `AEADBadTagException` sin capturar al leer `EncryptedSharedPreferences`** — `DropboxCredentialStore.<init>` (`DropboxCredentialStore.kt:21`, `EncryptedSharedPreferences.create(...)`) descifra un `SharedPreferences` existente con una `MasterKey` de Android Keystore; si el blob cifrado en disco no cuadra con la clave del Keystore disponible (p. ej. tras desinstalar+instalar con otra firma, o un restore de `android:allowBackup="true"`), `Cipher.doFinal()` lanza `javax.crypto.AEADBadTagException` sin capturar. Se llama sin try/catch desde `MainActivity.onCreate()` → `refreshDropboxState()` — la Activity nunca llega a `setContent{}`, crash-loop permanente. **Reproducido en vivo en la RG556 real** (2026-09-25, validando ANDROID-SYNC-9/10/11) tras el intento previo de reinstalar release→debug | `android/app/src/main/java/com/retrovault/android/data/auth/DropboxCredentialStore.kt:14-45` | ✅ **arreglado 2026-09-25** — usuario pidió arreglarlo en esta misma sesión en vez de solo borrar datos a mano. `createPrefs()`/`buildEncryptedPrefs()`: `EncryptedSharedPreferences.create(...)` envuelto en `runCatching`; si falla, `context.deleteSharedPreferences(PREFS_NAME)` (borra el blob corrupto, API de plataforma, sin manejo manual de rutas) y se recrea vacío. Solo se pierde el token OAuth (hay que reconectar Dropbox), no saves/states. Verificado con `./gradlew testDebugUnitTest`/`compileDebugKotlin` reales (ambos en verde) — sin test JVM dedicado (clase 100% Android-framework, `EncryptedSharedPreferences`/`Context`, sin Robolectric en el proyecto, mismo criterio que el resto de `data/auth/`); la validación real del camino de fallback queda cubierta por la propia re-ejecución del checklist en la RG556 a continuación |
| ANDROID-SYNC-FIX-3 | **Bug: `SettingsScreen` no tiene scroll — en la RG556 real, "Sincronizar ahora", ambos switches y todo el Historial de sync quedan fuera del viewport visible, inalcanzables al tacto** — `SettingsScreen.kt:66-69` montaba el contenido en un `Column(modifier = modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(16.dp))` sin `Modifier.verticalScroll(rememberScrollState())`. En el viewport real de la RG556 en landscape (1920×1023 px tras las barras del sistema) el contenido (título, badge Dropbox, botón desconectar, 2 campos de ruta, botón "Guardar rutas", botón "Sincronizar ahora", 2 switches, sección Historial con hasta 10 filas) desbordaba ese alto y no había forma de desplazarse. Hallado validando `ANDROID-SYNC-10` en hardware real (2026-09-25): los switches solo se pudieron accionar enviando toques por coordenadas obtenidas de `uiautomator dump`, no viable para un usuario real con solo la pantalla táctil | `android/app/src/main/java/com/retrovault/android/ui/settings/SettingsScreen.kt:66-69` | ✅ **arreglado 2026-09-25** — usuario pidió arreglarlo en la misma sesión. `Column` raíz envuelto en `Modifier.verticalScroll(rememberScrollState())`, sin cambiar layout ni estructura. `./gradlew compileDebugKotlin`/`testDebugUnitTest` en verde — **confirmado en la RG556 real el mismo día**: con el fix instalado, `uiautomator`/`input tap` llegaron sin problema a "Sincronizar ahora" y a ambos switches (ver `ANDROID-SYNC-10`) |
| ANDROID-SYNC-CRITICAL-1 | **CRÍTICO — el sync PC↔Android nunca ha compartido datos de verdad, por dos razones apiladas, encontradas intentando el Paso 4 (best-effort) del checklist de `ANDROID-SYNC-10`** | `android/app/src/main/java/com/retrovault/android/data/auth/DropboxAuthManager.kt` | 🟡 **causa raíz 1 arreglada 2026-09-25, causa raíz 2 documentada, sin arreglar** — ver detalle abajo |

**Causa raíz 1 (arreglada): cuenta de Dropbox equivocada.** La app Android estaba conectada a `rubitobus.shin@gmail.com`; el PC (`rclone`/`rommgr sync`) usa `r.cerezo26@gmail.com`. Mismo dueño, dos cuentas Dropbox distintas — cada sync "exitoso" desde el móvil (0 errores, contadores de archivos subidos reales) aterrizaba en una cuenta que el PC nunca lee. Diagnosticado subiendo un archivo de prueba único desde el móvil y buscándolo con `rclone lsf dropbox: --recursive` (acceso Full Dropbox de `rclone`, cuenta `r.cerezo26@gmail.com`) — no aparecía en ningún sitio de esa cuenta. Confirmado con certeza comparando `account_id` reales de ambos lados (no solo el email, que en teoría podría repetirse entre espacios personal/equipo): PC vía `users/get_current_account` con el token de `rclone` (`dbid:AACD3NTx...`) vs Android tras añadir el mismo diagnóstico (ver abajo) — coincidían exactamente tras reconectar. **Fix**: usuario reconectó Dropbox en la app eligiendo `r.cerezo26@gmail.com` explícitamente (el selector de Google/Dropbox saltaba por defecto a la cuenta ya guardada en el dispositivo — hubo que cerrar esa sesión en Dropbox.com primero). Bloqueo intermedio real: la app de Dropbox (App Key en `local.properties`) está en modo Desarrollo con tope de usuarios autorizados, y ya lo había alcanzado (acumulado de reconexiones de sesiones de prueba anteriores) — "This app has reached its user limit" al intentar añadir la cuenta nueva; se liberó revocando cuentas de prueba viejas desde la Dropbox App Console (usuario, fuera de esta sesión).

**Diagnóstico añadido permanentemente**: `DropboxAuthManager.fetchAccountLabel()` (nuevo) llama a `users/get_current_account` y `SettingsScreen` muestra `email · account_id` bajo el badge "Conectado" — para comparar sin ambigüedad la próxima vez, en vez de asumir por el nombre de la cuenta. Requirió añadir el scope `account_info.read` a `SCOPES` en `DropboxAuthManager` (las credenciales ya emitidas no lo tenían — hace falta reconectar una vez más tras este cambio para que el diagnóstico funcione; confirmado con logging temporal in-session que la llamada fallaba con `missing_scope` antes del fix, retirado antes de commitear).

**Causa raíz 2 (sin arreglar, más profunda): la app de Dropbox de Android es de tipo "App folder", no "Full Dropbox".** Confirmado empíricamente: tras corregir la cuenta, un archivo subido a `savesRemote="/RetroSync/saves"` aterrizó realmente en `Aplicaciones/Retrovault/RetroSync/saves/...` (carpeta sandbox de la app, con nombre localizado al idioma de la cuenta — "Aplicaciones" en vez de "Apps") — invisible para `rclone`/`rommgr` en el PC, que usan una app "Full Dropbox" y leen/escriben directamente en la raíz real `/RetroSync/...`. **Con esto, incluso con la cuenta ya correcta, el móvil y el PC nunca comparten el mismo árbol de carpetas** — el pilar 3 (sync de saves, "cualquier bug aquí es prioridad absoluta") sigue sin cumplirse de verdad hasta arreglar esto. Pendiente decidir en la Dropbox App Console si el tipo de acceso de la app existente se puede cambiar a Full Dropbox (no confirmado si es editable post-creación para scoped apps) o si hace falta registrar una app nueva con ese tipo y actualizar `dropbox.appKey` en `local.properties` + reconectar. Hasta entonces, cualquier sync validado hoy en la RG556 (incluyendo el Paso 8 del checklist) es real y funcional **dentro del sandbox de la app**, pero no representa todavía el sync cruzado con el PC que promete el pilar 3.

**Recurrencia 2026-09-26**: al retomar la sesión, Ajustes mostraba "No conectado" (la sesión OAuth de la app se había perdido). Al pulsar "Conectar Dropbox" en la RG556, Dropbox volvió a devolver "This app has reached its user limit" en el mismo paso (`dropbox.com/1/connect_submit`) — el tope de usuarios de la app en modo Desarrollo se llena de nuevo con cada ciclo de reconexión/prueba, no es un evento aislado. El usuario liberó cuentas y reconectó con éxito (`r.cerezo26@gmail.com`, `dbid:AACD3NTx...` — coincide con `rclone`).

**Causa raíz 3 (encontrada 2026-09-26, distinta de la 1 y la 2): a la app Dropbox le faltan scopes de archivo en la pestaña Permissions de la App Console.** Tras reconectar con la cuenta correcta, "Sincronizar ahora" en la RG556 dio **Subidos: 0 · Descargados: 0 · Al día: 0 · Errores: 8** — 8 fallos de `files/list_folder` (uno por carpeta local con actividad). Confirmado leyendo `errorsText` directo del Room DB del dispositivo (`adb exec-out run-as com.retrovault.android cat databases/retrovault.db[-wal]`, tabla `sync_history`, sin modificar nada — solo lectura): mensaje real de la API de Dropbox: *"Your app (ID: 8660947) is not permitted to access this endpoint because it does not have the required scope 'files.metadata.read'. The owner of the app can enable the scope for the app using the Permissions tab on the App Console."* Coincide con la pantalla de consentimiento OAuth vista en el navegador, que solo pedía "Visualizar la información básica de tu cuenta" (`account_info.read`) — ningún permiso de archivos. `DropboxAuthManager.SCOPES` (`android/app/src/main/java/com/retrovault/android/data/auth/DropboxAuthManager.kt:75`) ya pide `files.metadata.read`/`files.content.read`/`files.content.write`/`account_info.read`, pero Dropbox solo concede los scopes que la app tiene habilitados en su pestaña Permissions — ahí solo está marcado `account_info.read`. **Fix pendiente (usuario, fuera de esta sesión)**: marcar los 3 scopes de archivo en Permissions → Submit → desconectar/reconectar Dropbox en la app (los scopes nuevos solo aplican a un token emitido después del cambio). Con esto resuelto, queda pendiente repetir el test de causa raíz 2 (App folder vs Full Dropbox) para confirmar si el usuario ya lo dejó en Full Dropbox como cree.

---

| ANDROID-DRIVE-1 | **Idea para el futuro (2026-09-25, motivada por el límite de usuarios de la app Dropbox de ANDROID-SYNC-CRITICAL-1): añadir Google Drive como proveedor alternativo en la app Android**, igual que ya existe en el PC. El lado PC (`web/handlers/cloud_auth.py`, `_PROVIDERS = {"dropbox": ..., "gdrive": ("drive", "gdrive")}` + wizard OAuth ya cableado en `sync.js`/`tab-sync.html`) es agnóstico de proveedor porque delega en `rclone` — Drive ya funciona ahí sin código nuevo, solo eligiendo el provider en la UI. El lado Android **no** es agnóstico: `DropboxTransport`/`DropboxAuthManager`/`DropboxCredentialStore` usan directamente el SDK de Dropbox (`DbxClientV2`), sin capa de abstracción — añadir Drive requeriría una implementación paralela completa (SDK de Google Drive, su propio flujo OAuth con Google Identity Services, y su propio modelo de direcciones por `fileId`+carpetas en vez de rutas POSIX planas, bastante distinto de cómo `SyncEngine`/`ConflictResolver` asumen hoy `relative: String` sobre una raíz). No es un cambio pequeño — antes de implementarlo, decidir si vale la pena frente a simplemente resolver `ANDROID-SYNC-CRITICAL-1` (pasar la app Dropbox actual a Full Dropbox) | `android/app/src/main/java/com/retrovault/android/sync/DropboxTransport.kt`, `.../data/auth/Dropbox*.kt` | 🟡 **en marcha 2026-09-29** — roadmap completo en `.claude/roadmaps/28-android-gdrive-provider.md` (5 fases: `CloudTransport` genérico, auth Google Sign-In + Picker con scope `drive.file` para evitar la revisión de scopes sensibles de Google, `GoogleDriveTransport` con resolución de carpeta→ID cacheada, selector de proveedor en Ajustes, validación en hardware). Fase 1 mergeada (PR #357, `CloudTransport` extraído sin regresiones). Fase 2 en curso en `feature/android-drive-2-signin`: `GoogleDriveCredentialStore`/`GoogleDriveAuthManager` (solo Sign-In con `GoogleSignIn` clásico, compila + `testDebugUnitTest` en verde). Investigado el Picker (2026-09-29, contra la doc real de Google, no asumido): no es un WebView — es `Identity.getAuthorizationClient()`/`AuthorizationRequest` (API distinta de `GoogleSignIn`, ver nota en el roadmap 28), scope `drive.file` + parámetros `trigger_onepick`/`allow_folder_selection`. Sin código todavía — la firma Kotlin exacta para pasar esos parámetros no está confirmada en ninguna fuente consultada, y adivinarla sin poder compilar/probar contra Drive real (Fase 0 pendiente) es más riesgo que valor. Nada de esto es verificable de extremo a extremo hasta completar la Fase 0 (proyecto en Google Cloud Console, `GDRIVE_CLIENT_ID` real en `local.properties`) **Avance 2026-10-03**: Fase 0 completada por el usuario (proyecto Google Cloud, clientes OAuth Android release+debug, usuario de prueba) y **Sign-In verificado en la RG556** (botón en Ajustes, PR #406; el 403 inicial era una cuenta no incluida como usuario de prueba). Motivación reforzada: la cuenta de Dropbox superó su cuota de 2,25 GiB (ver SYNC-REMOTE-TREE-1c). Pendiente: Picker, `GoogleDriveTransport` (REST), selector de proveedor, validación; el PC ya soporta gdrive vía rclone pero `config.toml` apunta a `dropbox:` |

---

| DESIGN-1 | Portar el design system "RetroVault Sync" (tokens de color/tipografía/spacing del artifact https://claude.ai/artifact/Er8gzxt15ZF8nLAws7QqYL, calcado del `web/static/app.css` del PC) a Jetpack Compose/Material3 | `ui/theme/` | ✅ `Color.kt`/`Theme.kt`/`Type.kt` (PR #346) + aplicado a `PickScreen` (PR #346). ✅ **extendido 2026-09-24**: `ScanScreen` (card de stats con `mono-data`) y `SettingsScreen` (estado Dropbox) usaban `Text` plano sin tokens — corregido; nuevo componente compartido `ui/components/StatusBadge.kt` (pill de estado semántico, reutilizado en Settings y en el flujo de conexión de `PickScreen`); `rvSuccessColor()` movido de privado-en-`PickScreen` a `ui/theme/Theme.kt` para evitar duplicado. `./gradlew compileDebugKotlin` en verde |
| ANDROID-RELEASE-1 | **Primer release firmado del APK** — hasta ahora solo `assembleDebug` + `adb install` para pruebas en la RG556 (ver `ANDROID-SYNC-15`), nunca un build `release` firmado ni publicado. Sin `signingConfig`, `assembleRelease` producía un APK sin firmar (no instalable) | `android/app/build.gradle.kts` | ✅ **hecho 2026-09-24**: keystore de producción generado (`android/keystore/retrovault-release.jks`, PKCS12, alias `retrovault`, validez 10000 días — gitignored, contraseñas solo en `android/local.properties` local, nunca versionadas). `signingConfigs.release` en `build.gradle.kts` leído de `local.properties` con el mismo patrón que `dropbox.appKey` (degrada con gracia: sin las 4 claves, `release` compila igual pero sin firmar, no rompe CI/otras máquinas). `./gradlew assembleRelease` real → `BUILD SUCCESSFUL`, firma verificada con `apksigner verify --print-certs` (keytool -printcert no la detecta, usa el esquema v2/v3, falso negativo esperado). versionName se mantiene en `0.1.0` (primer release real, coincide con el tag `android-v0.1.0`) |

---

### EMULATOR-COMPAT — Save compatibility PC ↔ Android

Lista de pendientes de hardware (máquina "rammu"/RG556, `-2`/`-3`/`-4`, junto
con `SAVES-FRAGMENT-6`/`-9` y `TRASH-FIX-5b`) en
`.claude/roadmaps/20-rammu-machine-pending.md`.

Verify that synced saves from PC actually load on Android and vice versa, for each emulator pair.

| ID | Task | Notes |
|----|------|-------|
| EMULATOR-COMPAT-1 | Create compatibility matrix — PC emulator, Android emulator, save format, save path per platform | `docs/emulator-compat.md` ✅ |
| EMULATOR-COMPAT-2 | **Parcial 2026-09-08**: confirmado que la convención de nombre/tamaño de memcard DuckStation coincide byte a byte entre PC y Android para el mismo juego — `Crash Bandicoot (USA)_1.mcd` existe en ambos lados, mismo tamaño exacto (131.072 bytes, memcard PS1 estándar) en `C:\Users\rammu\Documents\DuckStation\memcards\` (PC) y `Android/data/com.github.stenzek.duckstation/files/memcards/` (RG556, mtime 2026-09-06 — jugado hace 2 días). **No se pudo verificar el contenido ni el "→ load" real**: `adb pull` del archivo Android da `Permission denied` (scoped storage sobre `Android/data/`, mismo límite ya documentado en `SAVES-FRAGMENT-9` — ni root ni copia pública) y la pantalla de la RG556 no se mantiene despierta vía ADB para confirmar visualmente que el save carga en la app. El round-trip completo sigue sin cerrar — necesita al usuario delante del dispositivo (o acceso root) | Hardware test with RG556 |
| EMULATOR-COMPAT-3 | Test PS2 round-trip: PCSX2 PC → sync → AetherSX2/NetherSX2 Android → load | Hardware test |
| EMULATOR-COMPAT-4 | Test remaining platforms (GBA, SNES, GBC, NDS…) and document any format mismatches | Update matrix per result |
| EMULATOR-COMPAT-6 | **Syncthing corría en paralelo sobre `RetroArch/saves` y `RetroArch/states` en la RG556** — hallazgo 2026-08-25 (`saves/.stfolder`, `states/.stfolder`, anidados en `saves/Beetle PSX/` y `states/LRPS2/`; tombstone `saves/.stfolder.removed-20250708-230136/DO_NOT_DELETE.txt` de un intento previo de desactivarlo sin completar). Dos motores de sync tocando los mismos archivos de save = riesgo de conflicto/corrupción. **Mitigado en caliente**: `com.github.catfriend1.syncthingandroid` parado (`am force-stop`) y deshabilitado (`pm disable-user`, reversible con `pm enable-user`) por ADB — cero archivos borrados. Pendiente: decidir si se reactiva alguna vez y para qué (no se investigó su propósito original). Hay además un tercer sync app instalado (`dk.tacit.android.foldersync.lite`, FolderSync Lite) — parado y deshabilitado también por ADB (misma operación reversible, cero borrados); propósito original sin investigar, posible origen de la carpeta huérfana `ra-saves` (ver ROADMAP-IDEAS / limpieza 2026-08-25) | Hardware | S | ✅ ambos apps mitigados |
| SAVES-FRAGMENT-1 | **Saves del mismo juego fragmentados entre esquemas por-core y por-plataforma dentro de RetroArch** — `sort_savefiles_by_content_enable` se ha activado/desactivado en distintos momentos en la RG556; conviven `saves/Snes9x 2010/Earthbound (1).srm`, `saves/bsnes2014/...`, `saves/Snes9x/...`, `saves/Snes9x 2005 Plus/...` Y `saves/snes/Earthbound.srm` — mismo juego, hasta 4-5 copias, sin saber cuál es la más reciente sin comparar fechas. NO fusionar a ciegas: puede pisar progreso más reciente (regla del proyecto — backup antes de mover). Alcance: comparar mtime/hash de cada grupo, consolidar en el esquema por-plataforma (el único que además es sincronizable de forma predecible), backup automático de lo descartado | Hardware + diseño propio | M | 🟡 **inventario y diagnóstico hechos 2026-08-25** → `Tareas/Informe-SAVES-FRAGMENT-1.md` (+ datos crudos `Tareas/SAVES-FRAGMENT-1-inventario-rg556.tsv`, 424 archivos con mtime/tamaño/md5). Nada movido ni borrado. Riesgo real acotado a **8 grupos divergentes** (Earthbound ×7 copias/3 versiones, `Mcd001.ps2`, 5 juegos GBA); 42 grupos idénticos + 3 todo-vacío + 2 con ganador obvio son dedupe seguro (~190 MB en `saves/nds/states/`). Tres hallazgos que invalidan el plan original: (a) la copia **más reciente de Earthbound está en el esquema por-core** (`saves/Snes9x/`), consolidar hacia `saves/snes/` a ciegas pisa progreso; (b) hay **dos ejes más** de fragmentación — extensión distinta por core (`.srm` VBA Next 139264 vs `.sav` mGBA 32/64/131072, md5 nunca comparable entre cores) y mismo juego con dos nombres de ROM; (c) 37 archivos son **plantillas en blanco `0xFF`** con mtime posterior al save real — un consolidador que solo mire fecha elige la copia vacía en 3 de 5 casos. `states/` NO está fragmentado. Pendiente: decisión del usuario sobre los 8 divergentes antes de mover nada |
| SAVES-FRAGMENT-2 | **Formato de memcard confirmado compatible 2026-09-08** (ADB pull real de las 3 copias, RG556 conectada): las 3 (`RetroArch/saves/LRPS2/Mcd001.ps2`, `RetroArch/saves/ps2/Mcd001.ps2`, `RetroArch/emulator_saves/xyz.aethersx2.android/saves/Mcd001.ps2`) comparten el mismo header binario exacto (`Sony PS2 Memory Card Format 1.2`, 8.650.752 bytes) y contienen los mismos 6 juegos (`BESLES-50386/51950/52445/52822/53777/54915`) — el formato es intercambiable sin conversión entre AetherSX2 y los cores PCSX2 de RetroArch, hipótesis original confirmada. **Pero el contenido ya divergió**: MD5 distinto en las 3 (progreso de partida distinto), mtimes muy separados — AetherSX2 (`emulator_saves/`) 2026-07-13 (la más reciente, coincide con que el usuario juega ahí hoy según `dumpsys usagestats` de SAVES-FRAGMENT-9), `saves/ps2/` 2025-11-21, `saves/LRPS2/` 2025-06-29 (la más vieja). Mcd002.ps2 sí es idéntico byte a byte en las 3 (plantilla en blanco sin usar). **Consolidado 2026-09-08** (decisión del usuario: "consolidar a AetherSX2"): backup local (`adb pull` de las 3 antes de tocar nada) + backup on-device de las 2 copias sobrescritas (`Mcd001.ps2.bak_20260908` junto a cada original, recuperable) antes de `adb push` de la copia de AetherSX2 sobre `saves/LRPS2/Mcd001.ps2` y `saves/ps2/Mcd001.ps2`. Verificado con `md5sum` tras el push: las 3 rutas dan el mismo hash (`3d16447882314806d6104860bec4bcd4`) — consolidación confirmada sin pérdida de datos | `RetroArch/saves/LRPS2/`, `RetroArch/saves/ps2/`, `RetroArch/emulator_saves/xyz.aethersx2.android/saves/` | ✅ consolidado y verificado 2026-09-08 |
| SAVES-FRAGMENT-3 | **NVRAM de arcade repartido en 5 ubicaciones en la misma RG556** — `RetroArch/mame/*.nv` (junto a ROMs), `RetroArch/saves/mame/*.nv`, `RetroArch/saves/Unknown/*.nv` (~40 archivos que RetroArch no logró emparejar con ninguna plataforma — revisar también como síntoma de matching roto), `RetroArch/saves/mame2003/{nvram,hi,cfg}/`, `RetroArch/saves/cps1/`+`cps2/`. Ninguna se sincroniza hoy — ver EMULATOR-COMPAT-5 | Hardware + diseño propio | M | ⬜ documentado 2026-08-25 |
| SAVES-FRAGMENT-4 | **GameCube/Wii en 3 ubicaciones**: core Dolphin de RetroArch (`saves/gamecube/{EUR,USA}`, `saves/User/{GC,Wii}` — un perfil Dolphin completo anidado dentro de la carpeta de RetroArch) vs. standalone mmjr-revamp (`GC/{EUR,JAP,USA}`, `Wii/title/`) | Hardware + diseño propio | S | ⬜ documentado 2026-08-25 |
| SAVES-FRAGMENT-5 | **Cada standalone usa su propio path público/privado, ninguno coincide entre sí ni con RetroArch** — DuckStation (`/storage/emulated/0/duckstation/` + `Android/data/com.github.stenzek.duckstation/files/`), AetherSX2 (`Android/data/xyz.aethersx2.android/files/`), Redream (`Android/data/io.recompiled.redream/files/`), DraStic (`/storage/emulated/0/DraStic/backup/`, `savestates/`). Una vez resuelto DEVPROFILE-0 en su alcance reducido, decidir si el sync de Retro Vault amplía sus raíces vigiladas a estas carpetas o si se le pide al usuario redirigir cada app (vía su propio menú de ajustes) a una ruta pública común | Hardware + diseño propio | M | ⬜ documentado 2026-08-25, depende de DEVPROFILE-1 (mapa core→plataforma como base) |
| SAVES-FRAGMENT-6 | **Emulador canónico por plataforma + esquema de saves congelado** — mitad preventiva de SAVES-FRAGMENT-1: sin esto, cualquier consolidación se vuelve a fragmentar. Política completa en `docs/emulador-canonico-rg556.md` (tabla de 15 plataformas con emulador ganador, ruta de save y qué se jubila; decidida con `dumpsys usagestats` real del dispositivo, no por suposición). Hallazgos nuevos: (a) **hay DOS RetroArch instalados** (`com.retroarch` 19 h vs `com.retroarch.aarch64` 2 min, ambos arm64, cfg y cores separados) — segunda fuente de fragmentación, Daijishō debe apuntar al primero; (b) **PSX se juega en DuckStation standalone (68 h, 221 lanzamientos)** pero hay memcards del core Beetle PSX en `saves/psx/` — fragmentación PSX invisible al informe porque cae fuera de `saves/`; (c) **melonDS escribe junto a las ROMs en `RetroArch/nds/`** — sexta ubicación, mismo patrón que el `.nv` de EMULATOR-COMPAT-5; (d) hay **tres** juegos de memcards PS2, no dos (`saves/ps2/`, `saves/LRPS2/`, `emulator_saves/xyz.aethersx2.android/`). Ajustes RetroArch a congelar: `sort_savefiles_enable=false`, `sort_savefiles_by_content_enable=true`, `savefiles_in_content_dir_enable=false`, `savestates_in_content_dir_enable=false`; los de savestates NO se tocan (`states/` no está fragmentado, migrar 68 archivos a cambio de nada). ⚠️ **No automatizable por ADB**: `retroarch.cfg` y la config de Daijishō viven en `/data/data/`, sin root y sin copia pública (verificado con `find`) — hay que hacerlo en los menús. Vía alternativa documentada: Daijishō importa platform JSON con `playerList`/`amStartArguments`, se podrían generar los 15 archivos si el usuario exporta uno de muestra. **Ausencia de root confirmada** 2026-08-25 (`su` no existe, sin Magisk/KernelSU, `/data/data` = `Permission denied`, shell = `uid=2000`). **Requisito añadido por el usuario: RetroAchievements en todas las plataformas** — manda sobre el resto de criterios y cambia 4 filas: PS2 pasa de AetherSX2 a **ARMSX2** (RA soporta PCSX2/ARMSX2/XBSX2, AetherSX2 y NetherSX2 no están en la lista; hay que instalarlo); **PPSSPP 1.11.3 es de 2021 y no tiene RA** (actualizar); **GameCube pasa al standalone Dolphin 2606a** porque RA no existe en el core `dolphin-emu` — y eso implica renunciar al sync en esa plataforma (saves en `Android/data/`, sin root); **3DS queda fuera del criterio** (RetroAchievements no soporta 3DS como consola). DraStic, Redream y MMJR quedan descartados también por no tener RA. Nota: el modo hardcore de RA desactiva los save states, lo que refuerza dar prioridad al save de batería sobre `states/` | Hardware + diseño propio | S | ✅ política documentada 2026-08-25 (v2 con RA), aplicada en el dispositivo 2026-09-27 — **corrección 2026-09-27**: la mitad de iiSU sí es ADB-automatable (`emulator_options.json` vive en `Android/media/com.iisulauncher/...`, almacenamiento público, no en `/data/data/`) — aplicado: `gb`→Gambatte core, `n64`→Mupen64Plus-Next core, `dreamcast`→Flycast core (los 3 estaban en un standalone sin RA o en modo "Ask"), `ps2`→ARMSX2 Refresh (Standalone) (AetherSX2 no tiene RA). Detalle completo, incluida la trampa de nombres "ARMSX2" vs "ARMSX2 Refresh", en `docs/emulador-canonico-rg556.md` §6.7. Daijishō sigue bloqueado sin root (confirmado otra vez: no hay `Android/media/com.magneticchen.daijishou/` en la SD). **Corrección 2026-09-27b**: la vía de "exportar una plataforma como JSON" nunca existió — comprobado a fondo en la UI y contra el repo oficial (closed-source, solo Importar). Hecho en su lugar: **las 32 plataformas de Daijishō revisadas a mano** (`Examinar sistemas → Ajustes del emulador`), 12 corregidas (Wii, CPS1/2/3, Neo Geo, Neo Geo CD, GB, GBC, N64, Genesis, Master System, Atari 2600 — todas apuntaban a un standalone sin RA o a un paquete `RetroArch 64` huérfano), el resto ya estaba bien o queda fuera de alcance (Arcade MAME, 3DS, niche de 1 emulador). Detalle completo en `docs/emulador-canonico-rg556.md` §6.8. **Con esto, la tarea queda cerrada** — Daijishō e iiSU alineados con el canónico de §3 |
| SAVES-FRAGMENT-7 | **Re-investigado 2026-09-08 con la RG556 conectada por ADB — causa raíz corregida, NO es un bug de `rename_rom_with_saves()`**. Escaneo real de las 12 carpetas `saves/<plataforma>/` de `RetroArch/` contra las ROMs reales de la SD (`/storage/521D-04EA/ROMs/<plataforma>/`, activas **y** `_descartados/`): de 218 saves comparados, **70 OK** (ROM activa con ese nombre), **74 `DESCARTADO`** (el save no calza con ninguna ROM activa pero SÍ con una que vive hoy en `_descartados/` de esa plataforma — recuperable) y **74 sin ninguna ROM en absoluto**, ni activa ni descartada (gba 48, nds 13, psx 5, snes 3, ps2 2, nes 1, gamegear 1, fbneo 1). El caso testigo original (`EarthBound (USA).sfc`) es del segundo grupo: la ROM fue movida a `snes/_descartados/EarthBound (USA).sfc` el **2026-09-02 13:14**, dentro de un lote de **611 archivos SNES** movidos en el mismo minuto — comparado contra `file_operations` en `library_pc.db`/`library_android.db`: **0 filas ese día para esta consola**, así que no pasó por el pipeline de renombrado/reorganización de la app. Único mecanismo del proyecto que discarda ROMs en el lado Android sin loguear en `file_operations` (ese log solo cubre el pipeline de renombrado/organize, no Cable Sync): **Cable Sync en modo "Espejo completo" (`delete_extra=true`, `web/handlers/sync_cable.py:794` y ss.)** — mueve a `_descartados/` en el propio dispositivo cualquier ROM Android que no calce con el conjunto etiquetado/sincronizado desde el PC, sin arrastrar saves sueltos con el mismo nombre. Los 74 saves realmente huérfanos (sin ROM en ningún sitio) tienen nombres en convención vieja pre-No-Intro (`Advance Wars 2 [E].sav`, `Mega Man - Zero Collection.nds.sav`, títulos en español sin acentos) — son saves de una biblioteca anterior a la reorganización canónica del proyecto, sin ROM equivalente que los reclame hoy ni descartada ni activa. **Conclusión**: no hay bug que arreglar en `rename_rom_with_saves()` — el gap real es que ni el discard de Cable Sync ni ningún otro paso mueve/avisa de saves sueltos huérfanos cuando su ROM desaparece del árbol activo. Sin cambios de código ni de archivos en esta sesión (solo lectura vía ADB + consulta a `file_operations`). **Decisión del usuario 2026-09-08**: (1) los 74 `DESCARTADO` — dejar Cable Sync como está por ahora, no implementar arrastre automático de saves al descartar una ROM; (2) los 74 sin ROM en absoluto — dejarlos documentados sin tocar, sin sesión de re-emparejado caso a caso. Backlog cerrado como diagnóstico puro, sin trabajo de código pendiente derivado | `web/handlers/sync_cable.py:794-906` (`delete_extra`), `.rommgr/library_pc.db`/`library_android.db` (`file_operations`) | ✅ causa raíz diagnosticada 2026-09-08 — usuario decide no tocar nada por ahora |
| SAVES-FRAGMENT-8b | **Cierre real de la brecha de cobertura, 2026-09-22 (Día68, objetivo 8)**: el `newest` de `pc_to_anbernic`/objetivo 6 solo cubría `android_path=/storage/emulated/0/RetroArch` (raíces 1, 2 y 5 del inventario original — saves/states internos + leftover por plataforma). Las raíces 3 y 4 (tarjeta SD, `/storage/521D-04EA/`) nunca habían pasado por ningún sync — verificado con `find`/mtimes reales vía ADB: raíz 3 (`saves/`, antes atribuida solo a AetherSX2) resultó ser una **carpeta pública de saves por plataforma compartida por varios emuladores** (`psx/` 390 archivos — no solo `memcards/`+`sstates/` de AetherSX2 como asumía el inventario original —, `nds/` 40, `gba/` 21, `dreamcast/` 2, `gamegear/` 4, `gb/`+`snes/` 1 c/u), última actividad real 2026-08-27 (26 días sin backup hasta hoy). Decisión (usuario, 2026-09-22): extender el Cable Sync a estas raíces adicionales en vez de reconfigurar apps o mover archivos en el dispositivo — **cero cambios de código**, mismo endpoint `/api/cable-sync` `direction=newest` ya usado en objetivo 6, solo con `android_path` distinto. Dry-run + apply real en ambas: `android_path=/storage/521D-04EA/saves` → **430/430 copiados, 0 errores, 454 MB** (todo PC→consola, nada se sobreescribió en el PC); `android_path=/storage/521D-04EA/ROMs` (raíz 4, sueltos junto a ROMs) → **385/385 copiados, 0 errores, 296 MB** (incluye 48 archivos donde la consola tenía la versión más reciente, traídos al PC). Con esto las 5 raíces del inventario original quedan cubiertas por el sync real (1/2/5 vía objetivo 6, 3/4 vía esto) — el problema práctico (partidas sin backup) queda resuelto sin necesidad de la "consolidación" física original (mover/fusionar carpetas en el dispositivo), que se descarta como innecesaria dado que extender la cobertura del sync ya cierra el riesgo real | `web/handlers/sync_cable.py` (sin cambios — reutilizado tal cual con `android_path` distinto) | ✅ hecho 2026-09-22 — raíces 3 y 4 cerradas (815 archivos, ~750 MB), 0 errores en ambas pasadas |
| SAVES-FRAGMENT-8 | **Inventario de las 5 raíces rehecho 2026-09-08 con la RG556 conectada por ADB** (`find`+`wc -l` real contra cada raíz, no estimación): (1) `RetroArch/saves` interno **440** archivos, (2) `RetroArch/states` interno **76**, (3) SD `/storage/521D-04EA/saves` **498**, (4) sueltos junto a ROMs en la SD **130** (nds 81, gba 32, psx 6, gamegear 5, snes 4, gb 1, dreamcast 1 — cifras reales de hoy, distintas a las estimadas a mano el 2026-08-25 porque la biblioteca se ha movido desde entonces), (5) `RetroArch/<plataforma>/` en memoria interna (leftover) **142** (nds 50, gba 31, mame 24, cps2 19, psx 6, gamegear 5, cps1 4, snes 3 — el arcade de aquí es el mismo hueco que documenta `EMULATOR-COMPAT-5`; nds/gba coincide con el hallazgo de `SAVES-FRAGMENT-6` de que melonDS escribe junto a las ROMs). Total real: **1.286** archivos de save/state repartidos en 5 raíces, antes de consolidar nada. Solo lectura vía ADB, sin cambios. El caso de anidado `_descartados/_descartados/` sí existe hoy pero es **2 niveles, no 7**, y solo en `dreamcast/` (no en `snes/`, que se investigó primero por error de la estimación original) — causa raíz identificada y separada como `TRASH-FIX-2` | `/storage/521D-04EA/saves`, `/storage/521D-04EA/ROMs/*`, `RetroArch/saves`, `RetroArch/states`, `RetroArch/<plataforma>/` | 🟡 inventario real completo 2026-09-08 — consolidación en sí sigue sin implementar |
| TRASH-FIX-2 | **Anidado `_descartados/_descartados/` reproducible en modo ADB — `TRASH-FIX-1` (2026-07-13) solo cubrió el modo FS/SD.** Encontrado real en `dreamcast/_descartados/_descartados/` (18 archivos arcade Naomi/Atomiswave: `252-c1.c1`, `ggw.*`, `Ganryu (USA, Japan) (Unl).zip`, `GigaWing (Japan).zip`) dentro de `/storage/521D-04EA/ROMs/`, confirmado con `adb shell find`. Causa raíz: `_iter_files()` (`web/handlers/sync_cable.py:500-508`, modo FS) sí excluye `TRASH_DIR_NAME` del `os.walk` desde `TRASH-FIX-1` (comentario propio en el código lo explica), pero el modo ADB nunca recibió el mismo guard — `AdbTransport.ls_recursive()` (`sync/adb_transport.py:198-239`) solo filtra segmentos que empiezan por `.` y por extensión, nunca por nombre de carpeta; `_wanted_info()`/`_wanted_name()` (`web/handlers/sync_cable.py:441-448` y `683-696`), que deciden qué entra en `ab_index`/el plan de copia/descarte a partir de esa lista, tampoco filtran `_descartados` como segmento de ruta. Con Cable Sync en modo ADB + "Espejo completo" (`delete_extra`), el contenido ya descartado del lado Android puede volver a copiarse/descartarse en la siguiente pasada, anidando la carpeta una vez por cada ciclo — mismo mecanismo que ya arregló `TRASH-FIX-1` para el otro modo. **Fix aplicado 2026-09-09**: mismo guard de `TRASH-FIX-1` portado a `AdbTransport.ls_recursive()` (`sync/adb_transport.py`) — excluye cualquier ruta con un segmento igual a `TRASH_DIR_NAME`, junto al filtro ya existente de segmentos ocultos. Como `_wanted_info()`/`_wanted_name()` (ambos modos de Cable Sync) consumen la lista que devuelve `ls_recursive()`, un único fix en la función compartida basta — no hacía falta tocar `sync_cable.py`. 1 test nuevo (`tests/test_adb_transport_ls_recursive.py`, mockea `_shell` con un listado que incluye `_descartados/` anidado 2 niveles y confirma que solo sobrevive el archivo fuera de la papelera). Suite completa 1235/1235 (más los mismos 3 fallos preexistentes no relacionados, tests que asumen "sin ADB" con la RG556 conectada hoy) | `sync/adb_transport.py:198-246` (`ls_recursive`) | ✅ arreglado y testeado 2026-09-09 |
| TRASH-FIX-3 | **Hallazgo real 2026-09-09 — la papelera del dispositivo Android nunca se purga, y eso genera "duplicados" visibles en DuckStation/otros emuladores.** El usuario reportó ver muchas versiones distintas del mismo juego en la Anbernic. Causa raíz: `trash_roots()` (`utils/trash.py:112-119`) solo cubre `library_root`/`inbox.path` — rutas de PC — nunca se extendió al dispositivo por ADB, así que nada purga `_descartados/` en la SD. Confirmado con `adb shell find`: **170 carpetas `_descartados/` en toda la SD, 11.896 archivos, 247,92 GB** — muchas anidadas dentro de la carpeta de cada juego individual, no solo a nivel de plataforma (ej. `psx/Castlevania - Symphony of the Night (USA)/_descartados/` con una versión `(Asia)` y otra `(Japan)...(XBLA)` del mismo juego, justo al lado de la activa). Con **68 carpetas de juego en `psx/` afectadas (614 archivos, 93,35 GB)** — el caso concreto que reportó el usuario, ya que DuckStation escanea `psx/` de forma recursiva y no distingue `_descartados/` de una carpeta normal. **Fix implementado**: `AdbTransport.purge_trash()` (`sync/adb_transport.py:198-247`) — mismo contrato que `utils.trash.purge_trash()` del lado PC (borra archivos con más de `trash_purge_days` de antigüedad, limpia carpetas vacías), pero vía `adb shell find`/`rm -f`/`rmdir`, con auto-descubrimiento de todos los volúmenes montados (`/storage/*/`) si no se pasan raíces explícitas. Conectado al daemon existente (`web/daemons.py`, mismo bloque diario que ya purgaba PC) vía `resolve_single_device_transport()` — si hay un dispositivo conectado, se purga también; si no, se salta sin error. 2 tests nuevos (`tests/test_adb_transport_purge_trash.py`: solo borra lo más antiguo del umbral, nunca toca rutas de saves). Suite completa 1237/1237 (más los 3 fallos preexistentes de siempre por tener la RG556 conectada). **Limpieza puntual de lo ya acumulado (2026-09-09, decisión del usuario: "si son duplicados me los cargaría, lo único que no debemos romper son los saves")**: backup vía `adb pull` de los 11.896 archivos a `E:\Carpetas anbernic\_backup_android_descartados_20260909\` (PSX primero) + `rm -rf` de cada `_descartados/` en el dispositivo tras verificar que el backup coincide en número de archivos — nunca borra sin confirmar el pull completo (0 saltados). Solo toca `ROMs/*/_descartados/`, nunca `RetroArch/saves`/`states`/SD `saves/`. **Completado 2026-09-09**: 103 carpetas `_descartados/` encontradas, **101 respaldadas y borradas del dispositivo, 1 ya no existía** (borrada como parte de una carpeta padre ya procesada), **1 con error de pull** (`gb/GB official game ROM complete works/M/_descartados` — nombre de archivo demasiado largo para Windows, `adb: error: cannot create '...Mani 4 in 1 - Genki Bakuhatsu Gambaruger + Zettai Muteki Raijin...'`) — esa carpeta se dejó intacta en el dispositivo sin borrar nada en ese momento (mismo criterio de seguridad del script: sin backup completo — 0 saltados —, no se ejecuta el `rm`). ~247 GB liberados en la SD. **Incidente 2026-09-09 (batch 2, tarea 2)**: al intentar retomar esta carpeta pendiente se encontró que **ya no existe en el dispositivo — fue borrada sin querer durante la verificación en hardware de `TRASH-FIX-4`**, que llamó a `POST /api/trash-empty-android` directamente contra la RG556 real (mismo endpoint, `older_than_days=0`, sin ningún paso de backup a PC — mismo diseño que el botón "Vaciar ahora" de PC, pensado para vaciar la papelera al momento, no para el respaldo puntual que sí hacía el script de limpieza). Esa llamada fue la que efectivamente vació la carpeta `M/_descartados` que quedó pendiente aquí, sin retomar antes el script de backup. **Solo 112 de los archivos de esa carpeta llegaron a respaldarse** en `E:\Carpetas anbernic\_backup_android_descartados_20260909\gb\GB official game ROM complete works\M\_descartados\` (el `adb pull` se detuvo en el archivo de nombre largo sin completar el resto de la carpeta; no se pudo determinar el total exacto que había en el dispositivo en ese momento, la carpeta ya no existe para consultarlo). **Verificado 2026-09-09**: ninguno de los 112 títulos comprobados (muestra: "Metal Gear Solid (USA).gbc", "Mario Golf (Europe).gbc") tiene una copia activa en el dispositivo hoy (ni en `gb/` ni en `gbc/`) — solo quedan huérfanos los metadatos de scraping (`M/media/images/...jpg`) de algunos; no se pudo comprobar si existe copia en la biblioteca de PC porque `F:\Juegos Retro` no está montado en esta máquina ahora mismo. **No hay fix de código pendiente** — el endpoint hizo exactamente lo que su diseño documenta (vaciar ahora, igual que su gemelo de PC); el hueco fue de secuencia dentro de la sesión (verificar `TRASH-FIX-4` antes de retomar el backup pendiente de esta tarea), no un bug. **Decisión del usuario 2026-09-09: aceptada la pérdida** de lo no respaldado (~112 títulos de esa carpeta sí están a salvo en `E:\...`; el resto, cantidad exacta desconocida, se da por perdido sin más verificación) | `sync/adb_transport.py:198-247` (`purge_trash`), `web/daemons.py` (wiring), `utils/trash.py:112-119` (equivalente PC, sin cambios), `web/handlers/esde/maintenance.py:78` (`POST /api/trash-empty-android`, comportamiento verificado correcto por diseño) | ✅ cerrado 2026-09-09 — limpieza puntual del backlog acumulado completada; la carpeta `M` se purgó sin completar su backup durante la verificación de `TRASH-FIX-4`, pérdida aceptada por el usuario, sin acción de código pendiente |
| TRASH-FIX-4 | **Exponer la purga de `_descartados/` Android como opción de la app, no solo el daemon diario silencioso.** Petición del usuario tras la limpieza puntual de `TRASH-FIX-3`. Implementado: `AdbTransport.trash_stats()` (`sync/adb_transport.py`, solo lectura, reutiliza `_trash_dirs()` factorizada de `purge_trash`), `POST /api/trash-empty-android` + `GET /api/trash-status` ahora incluye `android: {files, bytes, connected}` (`web/handlers/esde/maintenance.py`), y `state.record_trash_purge(side, result)` (`web/state.py`) guarda ts/deleted/bytes de la última purga (PC y Android, automática o manual) para mostrarla en el panel. UI: fila Android en el panel "Papelera" ya existente de Ajustes (`tab-settings.html`), oculta si no hay dispositivo conectado, con su propio botón "Vaciar en Android"; ambas filas muestran ahora "última purga: fecha, N archivos, X GB" (`config.js`). 1 test nuevo (`tests/test_adb_transport_purge_trash.py::test_trash_stats_counts_without_deleting`), suite de papelera 8/8 | `sync/adb_transport.py` (`trash_stats`, `_trash_dirs`), `web/state.py` (`record_trash_purge`), `web/daemons.py`, `web/handlers/esde/maintenance.py`, `tab-settings.html`, `config.js`, `main.js` | ✅ implementado, testeado y verificado en hardware real 2026-09-09 — `POST /api/trash-empty-android` probado contra la RG556 real (217 archivos, 223 MB, la última carpeta pendiente de `TRASH-FIX-3` tras el fallo de pull), `GET /api/trash-status` confirma `android.files: 0` y `last_purge` correcto tras la purga; verificado además con `adb shell find` que no queda ninguna carpeta `_descartados/` en el dispositivo. No se pudo probar el clic del botón en sí (extensión de Chrome sin conectar en esta sesión) — se llamó al mismo endpoint directamente (dispositivo ocupado con el `adb pull` masivo). **Clic verificado en el navegador real 2026-09-09 (batch 2, tarea 3)**: el botón dispara primero un `confirm()` nativo (`config.js:979`, "¿Vaciar la papelera del dispositivo Android?...") — al aceptar, llama a `POST /api/trash-empty-android` y muestra el resultado en la UI ("✓ 0 archivos eliminados (0KB)", esperado porque la papelera Android ya se había vaciado hoy durante esta misma sesión). Flujo completo confirmado end-to-end: diálogo → llamada → resultado renderizado |
| TRASH-FIX-5 | **Restauración parcial de la purga de `TRASH-FIX-3` en psx/ps2/nds — la purga original comparó por nombre/antigüedad, no por contenido, y descartó archivos únicos como duplicados.** El usuario reportó el 2026-09-10 huecos grandes en la Anbernic (PSX 130→32, PS2 30→2, `Final Fantasy III` desaparecido de NDS). Investigado contra el backup real (`E:\Carpetas anbernic\_backup_android_descartados_20260909\`) y contra el dispositivo conectado por ADB, comparando por **SHA1** (no por nombre) cada archivo respaldado contra los 1.132 archivos activos hoy en `psx/ps2/nds` del dispositivo: de los 1.368 archivos purgados el 2026-09-09 en esas 3 plataformas, **solo 206 (todos PSX) eran duplicados reales** — el resto, **1.162 archivos (248,6 GB), tenían contenido único sin ninguna copia activa equivalente**. PS2 y NDS: **0 duplicados reales de 379 purgados entre ambas** — prácticamente todo lo borrado ahí era contenido único mal etiquetado como "papelera". **Restaurado 2026-09-10**: los 1.162 archivos únicos copiados de vuelta a su ruta original en el dispositivo (`adb push` por archivo, reconstruyendo la ruta quitando el segmento `_descartados`), verificado sin colisión de ruta contra lo ya activo antes de escribir. 1.159/1.162 a la primera, 3 fallos por corte transitorio del daemon ADB (mismo patrón que el "BIOS shader" de `TRASH-FIX-3`), reintentados con éxito — **1.162/1.162 final**. `Final Fantasy III (Europe)` verificado de vuelta en `nds/`. Espacio en SD tras restaurar: 119 GB libres (de 281 GB antes). Los 206 duplicados reales de PSX se quedan descartados (la purga acertó ahí). **No se tocó código** — la causa raíz de fondo (por qué el proceso que llenó `_descartados/` en primer lugar juntaba contenido único con duplicados reales, especialmente en PS2/NDS donde el acierto fue 0%) sigue sin diagnosticar; documentado como pendiente, no investigado en esta sesión (fuera de alcance: el pedido era restaurar, no encontrar por qué se generó la papelera mal poblada). Resto de plataformas afectadas por la purga original (arcade, wii, dreamcast, etc. — 103 carpetas totales menos las 3 cubiertas aquí) sin auditar todavía con este mismo método | `E:\Carpetas anbernic\_backup_android_descartados_20260909\{psx,ps2,nds}`, dispositivo RG556 vía ADB (`ROMs/{psx,ps2,nds}`) | ✅ restaurado y verificado 2026-09-10 — pendiente auditar el resto de plataformas de la purga original con el mismo método SHA1 |
| TRASH-FIX-5b | **Continuación 2026-09-11 — auditadas casi todas las ~28 plataformas restantes de la purga original**, mismo método SHA1 (backup vs. activos en dispositivo), en un agente en background. **Interrumpida a petición del usuario antes de que reportara sus números exactos por plataforma** (no se pudo capturar el resumen final) — evidencia indirecta de que el trabajo fue real y extenso: espacio libre en la SD bajó de 119 GB (tras `TRASH-FIX-5`, 2026-09-10) a **58 GB** hoy (`df -h /storage/521D-04EA`), ~61 GB restaurados. Por `mtime` de las carpetas (orden cronológico) se procesaron en este orden: `3ds, Atari 2600, atari5200, atari7800, atarijaguar, atarilynx, atarist, colecovision, Famicom Disk System, fds, Game Gear` (antes del corte de ADB `unauthorized`), luego `intellivision, c64, amiga, famicom, n64, megadrive, nes, atari2600, snes, gamegear, mastersystem, arcade, gb, gbc, gba, wii, dreamcast, psp, gamecube` (tras reautorizar) — es decir, **todas las plataformas de la lista original excepto `mame_infra`/BIOS quedaron tocadas**. **Punto exacto de corte**: dentro de `gamecube` (la última), verificado a mano contra el backup (`_backup_android_descartados_20260909\gamecube\`, 13 archivos) — en orden alfabético, `Bomberman Generation` → `Metroid Prime 2 - Echoes` ya estaban activos en el dispositivo con contenido idéntico (mtime `2026-09-09`, duplicados reales, correctamente descartados) y `Paper Mario - The Thousand-Year Door` se restauró de verdad (mtime `2026-09-11 09:57`, único). **Sin comprobar todavía**: `Pikmin`, `Soulcalibur II`, `Super Mario Sunshine`, `Super Smash Bros. Melee` (4 de los 13 de `gamecube`) — estos 4 son el único punto de retomada conocido con precisión; el resto de plataformas no tiene un registro tan fino de cuáles de sus archivos se completaron, solo la evidencia agregada de espacio libre. **No se tocó ningún archivo tras el corte** (parada limpia, sin `adb push` a medias verificado) | `.rommgr/_backup_android_descartados_20260909\gamecube\` vs dispositivo, `.rommgr/missing_games_report_20260911.md` (informe de juegos ausentes del todo, sesión aparte, ver `TRASH-FIX-5c`) | 🟡 interrumpida por el usuario 2026-09-11 — retomar por `gamecube` (4 títulos) y luego confirmar con un resumen agregado si el resto de plataformas quedó completo |
| TRASH-FIX-5c | **Informe de juegos completamente ausentes en el dispositivo (no relacionado con la purga — huecos de cobertura de siempre)**, generado 2026-09-11 comparando por nombre de archivo (sin extensión) el PC (`E:\Carpetas anbernic\`) contra el dispositivo (ADB) en las plataformas nunca sincronizadas por completo desde el Día59: **ps2 54/72 ausentes, psx 15/292, gamecube 46/61, wii 85/87, nds 97/465, arcade 14.067/15.891**. Guardado completo (con la lista de arcade) en `.rommgr/missing_games_report_20260911.md` (no versionado). Comparación por nombre exacto de archivo sin extensión — no detecta el mismo juego con nombre ligeramente distinto entre PC y dispositivo (falsos positivos posibles), y no distingue "ausente de verdad" de "presente pero en otro formato" (ver `CABLE-ROM-FIX-6` para el caso PSX `.chd` vs `.cue`/`.bin`, que aquí cuenta como "ausente" aunque el juego sí está, solo que en otro formato — los 15 "ausentes" de psx probablemente son en su mayoría ese caso, no huecos reales) | `.rommgr/missing_games_report_20260911.md` | 🟡 informe generado, sin depurar falsos positivos de formato/nombre |
| PSX-CONTAM-1 | **Alcance medido 2026-09-11** — confirmado en ambos lados (PC `E:\Carpetas anbernic\psx\` y dispositivo `ROMs/psx/`, mismos archivos): **117 archivos sueltos, ~5,0 GB**, con extensiones nunca reconocidas por `PLATFORM_BY_EXTENSION`/`AMBIGUOUS_EXTENSIONS` (`detection/platform_detector.py:39-40`, p.ej. `.ic1`, `.u32`, `.u96`) — `is_rom_file()` devuelve `False` para todas, así que el escáner del proyecto nunca las trata como ROM. Por `mtime` son **al menos 2 sets de MAME distintos y no relacionados**: uno del 2026-08-29 15:41 (`atdp.*`, `1.ic1`…`9.ic22`, `316-00xx.u*`, `lh538xx.u*` — pinta a placa Sega tipo System24/X-Board) y otro del 2026-09-02 11:22 (`qs1001a.u96`/`prgu.u29`/`cc.u*`/`82s123.10k` — set Capcom CPS2 con sonido QSound), más `readme.txt` (fecha interna 2004, típica de un ZIP de MAME sin recomprimir). **Verificado contra `library_pc.db`**: cero filas en `games` o `file_operations` para cualquiera de estos 117 nombres — el pipeline de la app (scan/rename/organize) nunca los tocó ni los registró, contradiciendo que sea un bug de organización per-archivo (esos siempre dejan rastro en `file_operations`). Pista real encontrada pero sin confirmar como causa: `file_operations` sí tiene **551 operaciones el mismo 2026-08-29**, incluyendo renombrados de ZIPs de MAME en `E:\Carpetas anbernic\inbox\mame_20240311\MAME\` (un volcado bruto de un romset MAME completo) — mismo día que uno de los dos lotes de contaminación, lo que sugiere que el origen fue esa sesión de Inbox, pero no se pudo trazar el mecanismo exacto que dejó los archivos sueltos dentro de `psx/` sin generar ningún registro en BD (candidatos sin confirmar: copia manual fuera de la app directamente a `psx/`, o algún camino de `_extract_collection()` en `web/zip_router.py:47-94` — copia archivos con `shutil.copyfileobj`/`zf.extract` sin tocar la BD — que no se pudo reproducir el escenario exacto con los datos disponibles). Sin tocar nada, solo investigado | `E:\Carpetas anbernic\psx\`, `/storage/521D-04EA/ROMs/psx/` (dispositivo, mismos 117 archivos), `detection/platform_detector.py:82-87` (`is_rom_file`, por qué el escáner los ignora), `web/zip_router.py:47-94` (`_extract_collection`, candidato sin confirmar — copia sin registro en BD) | 🟡 alcance medido y descartada causa "bug de organización per-archivo" (sin rastro en BD) — mecanismo exacto de origen sin confirmar, fix no decidido (son basura inofensiva para el escaneo de la app, pero DuckStation/otros emuladores que listan `psx/` recursivamente sí las verán) |
| DUP-CROSSFMT-5 | 🔴 **Mismo bug que `DUP-CROSSFMT-2/3` (sidecar sin su archivo de datos), encontrado en el formato CloneCD (`.ccd`+`.img`+`.sub`) al auditar el dry run antes de ejecutar `--apply` por primera vez.** `_is_cue_sibling_bin`/`parse_bins_from_cue` solo cubrían `.cue`/`.bin` — nunca se extendieron a `.ccd`, así que un `.ccd` y su propio `.img` podían unirse como "duplicado" y recomendar descartar el `.img`, dejando el `.ccd` sin datos. **4 casos reales confirmados en vivo antes del fix** (ambos archivos existían en disco): `Resident Evil 2 CD1`/`CD2`, `Rival Schools Evolution`, `clocktower2`, `NEW`. **Arreglado 2026-09-09**: `_is_ccd_sibling_data()` nueva (`web/builders/duplicates.py`, misma lógica que `_is_cue_sibling_bin` para `.img`/`.sub` con `.ccd` hermano) + `_is_disc_data_sibling()` combinador usado en los 2 puntos de unión (antes solo `_is_cue_sibling_bin`); `_discard_file` (`services/ra_duplicates_service.py`) ahora también arrastra `.img`/`.sub` al descartar un `.ccd` (mismo mecanismo que el `.cue`→`.bin` de `DUP-CROSSFMT-4`, sin parseo de contenido — sidecars por convención de mismo nombre). 2 tests nuevos, suite de duplicados 44/44 | `web/builders/duplicates.py` (`_is_ccd_sibling_data`, `_is_disc_data_sibling`), `services/ra_duplicates_service.py::_discard_file` | ✅ arreglado y testeado 2026-09-09, verificado contra la biblioteca real (los 4 casos ya no aparecen como grupo tras el fix) |
| DUP-CROSSFMT-6 | 🔴🔴 **INCIDENTE REAL 2026-09-09 — `resolve-duplicates --apply` descartó la única copia real de 10 juegos** (7 PSX: `Twisted Metal - World Tour (Europe)`, `Namco Museum Vol. 4`, `Mortal Kombat Trilogy`, `Guilty Gear (Europe)`, `Twisted Metal (Europe)`, `Namco Demo (Europe)`, `Crash Bash (USA)`; 3 Game Gear: `Royal Stone`, `Coca-Cola Kid`, `Phantasy Star Adventure`) — tras arreglar `DUP-CROSSFMT-4`/`-5` y verificar el dry run contra disco (no solo contra BD), se ejecutó `--apply` sobre la biblioteca real por primera vez. **Causa raíz**: el motor de recomendación (`_review_groups_for_repo`/`_review_entry_sort_key`) elige un "ganador" solo a partir de las filas de BD, sin comprobar que el archivo realmente exista en disco. Esta biblioteca tiene muchas filas obsoletas de limpiezas manuales previas (mismo patrón ya documentado como colateral en `DUP-CROSSFMT-3`: desincronización de contenido entre `library_pc.db`/`library_android.db` para el mismo `source_path`); en estos 10 casos una fila fantasma (`.bin` suelto, sin archivo real en ningún sitio) "ganó" la comparación contra un `.chd`/`.zip`/`.bin` real y bueno, que se descartó como si fuera el "perdedor" — sin ninguna copia sustituta real. **Detectado antes de causar pérdida permanente**: verificación post-apply cruzando cada "ganador" recomendado contra el disco real (`Path.rglob`) + timestamp de descarte (`_descartados/` guarda la hora exacta vía `os.utime`) para distinguir descartes reales de limpieza de filas ya muertas de antes. **Restaurado 2026-09-09**: los 10 archivos movidos de vuelta de `_descartados/` a su carpeta activa + `rommgr scan` sobre `psx/` y `gamegear/` para repoblar sus filas de BD — verificado con `sha1` tras el rescan, las 10 filas están de vuelta. **Fix de la causa raíz**: `resolve_duplicate_ra()` (`services/ra_duplicates_service.py`) ahora comprueba que `keep_path` exista de verdad (filesystem o `adb_transport.file_exists()` si es ruta de dispositivo) **antes** de tocar ningún perdedor del grupo — si el "ganador" no existe, el grupo entero se omite (0 descartes, error explicativo) en vez de ejecutar la recomendación a ciegas. 1 test nuevo que reproduce el incidente exacto (ganador fantasma + perdedor real), suite de duplicados 45/45. **Auditoría de `apply_ra_conflicts()` completada 2026-09-09 — ya es segura, sin bug equivalente**: revisados los dos tipos de conflicto (`planner/operation_planner.py::build_plan`, `services/ra_duplicates_service.py::apply_ra_conflicts`). "disk": el `target.exists()` que decide si hay conflicto ya es un `Path.exists()` real contra disco en el momento de construir el plan (`operation_planner.py:178`, no una fila de BD), y `apply_ra_conflicts` además exige `op.source_path.exists()` (línea 412) antes de comparar RA — ambos candidatos (ganador y perdedor) son siempre archivos reales. "collision": `scored = [(op, ra) for op in ops if op.source_path.exists()]` (línea 478) filtra cualquier fila fantasma **antes** de puntuar por RA, así que una fila sin archivo real nunca puede entrar en la comparación ni "ganar" contra un archivo real. Verificado con test nuevo que reproduce el escenario exacto del incidente (fila fantasma con RA=50 vs. archivo real con RA=5, misma colisión): el archivo real gana pese a tener menos logros, porque la fila fantasma nunca llega a puntuarse (`tests/test_apply_ra_conflicts.py::test_collision_ghost_row_never_beats_real_file`). **Conclusión: no hace falta ningún fix aquí** — la causa raíz de fondo (filas de BD obsoletas) sigue sin atacarse, pero `apply_ra_conflicts` ya está protegido contra sus efectos por un camino distinto al de `resolve_duplicate_ra`. Sigue pendiente, sin relación con la seguridad de este flujo: un rescan completo de la biblioteca para reducir el ruido de filas obsoletas de fondo | `services/ra_duplicates_service.py::resolve_duplicate_ra` (fix previo), `services/ra_duplicates_service.py::apply_ra_conflicts` (auditado, ya seguro), `planner/operation_planner.py:178` (`build_plan`, existencia real de `target` ya verificada), `web/builders/duplicates.py::_review_groups_for_repo` (causa raíz de fondo, sin tocar — nunca valida existencia al elegir "ganador") | ✅ daño real restaurado y verificado 2026-09-09; ✅ causa raíz parcheada en `resolve_duplicate_ra`; ✅ `apply_ra_conflicts` auditado 2026-09-09 — ya seguro, sin fix necesario, 1 test nuevo (53/53 en `test_apply_ra_conflicts.py`+`test_ra_duplicates_service.py`+`test_builders_duplicates.py`) |
| LIBRARY-ANDROID-STALE-1 | 🔴 **Diagnóstico 2026-09-09 (batch 2, tarea 4) — causa raíz de la nota colateral de `DUP-CROSSFMT-4` ("Guilty Gear (Europe).chd" con tamaño/sha1 distinto entre `library_pc.db`/`library_android.db`), y mucho más grande de lo que esa nota sugería.** `_repo_for_path()` (`web/builders/common.py:141-167`) decide en cada escritura si una ruta es "PC" o "Android" comparándola **contra el `config.library_root` actual** (`E:\Carpetas anbernic` hoy, según `config.toml:4`) — dentro → `library_pc.db`, fuera → `library_android.db`. El problema: esa clasificación es dinámica sobre un valor que ha cambiado con el tiempo, y nada migra ni purga `library_android.db` cuando `library_root` se reapunta — igual que ya pasó una vez con el prefijo `H:` (purgado en `DUP-CROSSFMT-2`, 2026-09-08). **Medido en vivo contra las BDs reales**: `library_android.db` tiene **12.499 de sus 13.164 filas totales (95%)** bajo el `library_root` de hoy (`E:\Carpetas anbernic%`) — deberían vivir todas en `library_pc.db`, no ahí. De esas 12.499: **5.639** tienen una fila hermana en `library_pc.db` con el mismo `source_path` pero potencialmente desincronizada (el caso `Guilty Gear (Europe).chd`: `library_pc.db` tiene 184.012.303 bytes/sha1 `437e203a...`, que coincide exactamente con el archivo real en disco verificado con `sha1sum`; `library_android.db` tiene 200.760.292 bytes/sha1 `d4c6c921...`, un dump antiguo que ya no existe) — cada una de estas parejas es una trampa para cualquier lógica de duplicados/RA-conflicts que consulte ambas BDs sin saber cuál es la vigente. Las otras **6.860** son huérfanas puras: rutas bajo carpetas con nombre antiguo en mayúsculas (`E:\Carpetas anbernic\Game Boy\`, `\Game Boy Advance\`, `\Game Boy Color\`) que **ya no existen en el disco real** (`ls "E:\Carpetas anbernic"` de hoy solo tiene `gb/`, `gba/`, `gbc/` en minúscula) — sobras de antes de que la biblioteca se reorganizara a slugs canónicos de plataforma, nunca limpiadas de `library_android.db` porque esa BD no pasa por las herramientas de reorganización de Pilar 1 (que operan contra `library_pc.db`). **Purgado 2026-09-09**, mismo patrón que la purga de `H:` (`DUP-CROSSFMT-2`): backup completo primero (`.rommgr/backup_library_android_before_libraryroot_purge_20260909/library_android.db`), luego borrado por `game_id`/prefijo de `source_path` de **12.499 `games`** + sus hijos (`game_metadata`/`game_tags`/`file_operations`/`saves` — 0 filas en estas cuatro para este prefijo, no había metadata/saves asociadas) + **4.189 `assets`**. Verificado tras borrar: 0 huérfanos en `game_metadata`/`game_tags`/`file_operations`/`saves` para los `game_id` eliminados, 0 filas restantes bajo el prefijo, servidor local (`GET /api/trash-status`, puerto 7777) sigue respondiendo 200 sin reinicio. `library_android.db` queda con **665 filas** legítimas (rutas de otras máquinas/prefijos, configs de emuladores) | `web/builders/common.py:141-167` (`_repo_for_path`, causa raíz — no migra ni purga al cambiar `library_root`), `config.toml:4` (`library_root` actual) | ✅ diagnosticado y purgado 2026-09-09 — 12.499 `games` + 4.189 `assets` eliminados, 0 huérfanos, backup completo conservado |
| SAVE-CONSOLIDATOR-1 | **Escáner de fragmentación de saves** — convierte la metodología manual de SAVES-FRAGMENT-1 en módulo reutilizable: agrupa por stem normalizado + extensión-por-familia-de-core (§2 del informe), detecta plantilla en blanco por relleno uniforme y no solo por hash repetido (§5, evita el falso positivo de Metal Gear Solid), reporta grupos divergentes sin tocarlos — mismo principio que Duplicados de ROM (nunca auto-resuelve, solo informa) | `sync/save_consolidator.py` (`scan_save_groups`), 11 tests en `tests/test_save_consolidator.py` | ✅ módulo hecho y validado 2026-08-27 contra el TSV real de la RG556 (`SAVES-FRAGMENT-1-inventario-rg556.tsv`, vía script de scratchpad, no commiteado): con una lista de extensiones de save-de-batería curada reproduce **exactamente** los 8 grupos divergentes del informe (Earthbound 7 copias, `Mcd001.ps2`, 5 GBA — mismos md5). **Hallazgo real**: usar el agregado global `config.save_extensions` en vez de una lista curada añade ~9 falsos positivos porque mezcla savestate-como-archivo (`.ml1`, `.hi`, `.nv`) con save de batería real bajo el mismo stem — documentado como contrato de la función, no arreglado con más código (ver docstring de `scan_save_groups`). **Job web hecho 2026-08-27**: `GET /api/save-fragmentation` (`web/handlers/sync.py` + `web/builders/save_consolidator.py`, escanea `library_root/saves` y `/states` como raíces separadas) + sección "Fragmentación de saves" en la pestaña Sync (`tab-sync.html`, botón "Analizar" → `doSaveFragmentation()` en `sync.js`). Probado de extremo a extremo contra la biblioteca real montada en `E:\Carpetas anbernic` (servidor real en `:7799`, `curl` al endpoint): 2,76 s, resultado correcto (`9 divergentes`, `29 solo-plantilla`, `32 idénticos`), HTML servido con el botón y el contenedor de resultado presentes. **Verificado en navegador real 2026-08-29** (Chrome vía extensión, servidor real `:7777`): clic real en "Analizar" en la pestaña Cloud → mismos contadores (`9 divergentes · 29 solo-plantilla · 32 idénticos`) y tabla con los grupos esperados (Donkey Kong - Jungle Climber, Castlevania - Dawn of Sorrow…) — ✅ listo para cerrar |
| SAVES-FRAGMENT-9 | **Progreso real de PS2 perdido en AetherSX2 — hallazgo 2026-08-29, en vivo en la RG556.** `dumpsys usagestats` confirma que el usuario sigue jugando en **AetherSX2** (sesión hoy 02:29-02:34, `appLaunchCount` alto histórico) y que **ARMSX2 nunca se ha abierto** (`idle=y`, sin `lastTimeUsed`) pese a estar instalado desde el 2026-08-25 — la migración de SAVES-FRAGMENT-6 no se aplicó de hecho. A las 02:29:41 AetherSX2 lanzó un `PickActivity` (SAF) justo antes de jugar. La memcard que hoy está activa en `/storage/521D-04EA/saves/memcards/Mcd001.ps2` (mtime 2026-08-27 13:35:58, junto a `Mcd002.ps2` y un tercer archivo `1.ps2` con el mismo mtime exacto → copia en bloque, no partidas jugadas) **no contiene ningún save de juego** (`grep -a -o -E "B[A-Z]?[SXE]LE?S-[0-9]{5}"` → 0 resultados), mientras que las dos copias ya conocidas por SAVES-FRAGMENT-2 (`RetroArch/saves/ps2/Mcd001.ps2` y `RetroArch/saves/LRPS2/Mcd001.ps2`) sí tienen 6 juegos cada una (BESLES-50386/51950/52445/52822/53777/54915). Esa misma carpeta `/storage/521D-04EA/saves/` replica 1:1 la estructura interna de AetherSX2 (`bios/`, `covers/`, `gamesettings/`, `sstates/`) y tiene al lado `duckstation_backup_2026-08-27.zip` (129 MB, 13:20) — es un **backup manual hecho el 27**, y ese backup ya capturó la memcard vacía. La memcard privada real de AetherSX2 (`Android/data/xyz.aethersx2.android/files/memcards/Mcd001.ps2`) tiene mtime 2026-08-13 pero su contenido es ilegible por ADB (scoped storage, `Permission denied` en `md5sum`/`grep`, igual que el resto de `/data/data` — no es root). No se ha tocado ni movido nada. **Hipótesis más probable, sin confirmar dentro de la app**: el progreso se perdió en AetherSX2 alrededor del 2026-08-13 (coincide con el mtime), no hoy — probablemente por crear/formatear una memcard nueva desde el menú de AetherSX2 sobre las mismas ranuras Mcd001/Mcd002, no por reinstalación (`versionName=v1.5-4248`, sin actualizar desde 2025-05-30). Pendiente: (1) abrir AetherSX2 y comprobar en Settings → Memory Cards qué carpeta usa hoy y si hay copias `.bak`/exportadas dentro de la app; (2) si se confirma que el progreso ya no existe en ningún sitio accesible, importar manualmente `RetroArch/saves/ps2/Mcd001.ps2` (la copia más reciente conocida, 2025-11-21) a AetherSX2 — backup previo obligatorio, memcard multi-juego = nunca automático (regla 7 de `docs/emulador-canonico-rg556.md` §5) | Hardware + investigación | S | 🟡 **punto 1 hecho 2026-09-27**: AetherSX2 abierto en modo solo-lectura, sin jugar nada — Settings → Memory Cards → Memory Card 1 = `Mcd001.ps2` (PS2/8MB), habilitada, "Filtrar Carpeta" activo. Coincide por nombre con las copias buenas conocidas, pero sigue sin poder leerse el binario real sin root — **no se puede confirmar si coincide o no, cuarentena**, tal como pide la regla 5. ARMSX2 abierto por primera vez sin arrancar nada: su carpeta de memcards aún no existe (se crea perezosamente al primer boot de juego/BIOS) — la migración por `adb push` queda lista para ejecutar en cuanto exista esa carpeta (confirmado que `Android/data/com.armsx2/files/` sí es accesible por ADB, a diferencia de AetherSX2), pero requiere que el usuario abra un juego una vez en ARMSX2 primero.

**Migración completada 2026-09-27**: el usuario abrió *Burnout 3 - Takedown* en ARMSX2 y creó un perfil real (save `BASLUS-21050`, confirmado con `strings` — no es plantilla). La config real de ARMSX2 vive en `/storage/521D-04EA/saves/memcards/` (SD — `bios/`, `cheats/`, `PCSX2-Android.ini` — no en `Android/data/` como se pensaba), accesible por ADB sin problema. Al inspeccionar la copia buena conocida con `mymcplus` (librería Python que entiende el formato real de superblock/FAT de una memcard PS2 — instalada aparte en el scratchpad de la sesión con `pip install --target`, **no** añadida como dependencia del proyecto) resultó tener **13 juegos, no 6** (el número de `SAVES-FRAGMENT-2` quedó desactualizado por syncs posteriores a 2026-09-08). Entre esos 13 ya había **otro** save de Burnout 3 (`BASLUS-21050`, creado 2025-05-22, modificado 2025-06-08) — conflicto real con el de hoy, mismo juego, dos partidas distintas. Caso de la regla 5 de §5 (divergencia real entre orígenes, nunca automático): preguntado al usuario, decidió quedarse con el save de 2025. Con esa decisión no hizo falta fusionar nada — la copia de 13 juegos se empujó tal cual al **slot 1** (`mcd001.ps2`, md5 `c229c932d6c18d87303c3ed5f7aebc8d`, verificado con `md5sum` tras copiar). El perfil de hoy no se perdió: queda respaldado en el propio dispositivo (`mcd001.ps2.bak-burnout3-perfil-hoy-20260927`, junto al slot 1) y en `E:\RetroVault\ROMS\_backup_android_cleanup_20260927\armsx2_memcards\`. El slot 2 (usado como zona de pruebas mientras se investigaba) se devolvió a su plantilla en blanco original. La memcard privada real de AetherSX2 sigue sin poder leerse sin root — no se pudo confirmar si su contenido coincidía con estos 13 juegos, pero deja de bloquear nada: ARMSX2 ya tiene el estado bueno conocido activo | `docs/emulador-canonico-rg556.md` §7 tiene el mismo detalle |

### ANDROID-APP-CLEANUP-1 — Desinstaladas las 4 apps sin uso ni RA (hecho 2026-09-27)

Petición directa del usuario. `pm list packages` confirmó que `com.retroarch.aarch64` ya no
estaba instalado (se quitó en alguna sesión anterior sin dejar rastro en el backlog).
Desinstaladas por ADB: `com.dsemu.drastic` (DraStic — tenía 69 MB de datos públicos en
`/storage/emulated/0/DraStic/`, incluyendo 7 saves `.dsv` con progreso real de NDS;
respaldado completo con `adb pull` a `E:\RetroVault\ROMS\_backup_android_cleanup_20260927\DraStic_publicdata\`
antes de desinstalar — la carpeta pública sobrevive a la desinstalación de todos modos, pero
mejor con backup fuera del dispositivo también), `io.recompiled.redream` y
`org.dolphinemu.mmjr` (ninguno tenía datos públicos que respaldar). Verificado con
`pm list packages` tras cada desinstalación: los 3 paquetes ya no aparecen | Dispositivo real (RG556) | ✅ hecho 2026-09-27 |

### DAIJISHO-IISU-PATHS-1 — Las rutas de Daijishō e iiSU a `SD:/ROMs/` ya funcionan, se resolvieron solas (verificado 2026-09-27)

El pendiente del 2026-08-25 (`docs/emulador-canonico-rg556.md` §7) asumía que ambos
launchers seguían apuntando a las rutas viejas tras el move de `SD:/` a `SD:/ROMs/`.
Verificado en vivo por ADB: **Daijishō** muestra "Arcade (FinalBurn Neo) · 779 elementos"
(el contenido real vive en `ROMs/arcade/fbneo/`, 867 archivos — la diferencia son
elementos sin vincular, filtrados por un ajuste propio de la app). **iiSU** abierto y
navegado hasta el tile "fbneo": carga juegos reales sin error. Ninguno de los dos necesita
ningún cambio. **Hallazgo colateral, sin relación con el bug de rutas**: dentro de `ROMs/`
(no en la raíz de la SD, que ya se limpió) sobreviven 4 carpetas sueltas Title-Case con
poco contenido — `Atari 2600/` (6 archivos), `Famicom Disk System/` (2), `Game Gear/` (28),
`Master System/` (0) — junto a sus pares canónicos en minúsculas con contenido real y
activo (`atari2600/`, `fds/`, `gamegear/`, `mastersystem/`). Ninguno de los dos launchers
parece leer de ahí (las cifras que muestran cuadran con las carpetas canónicas) — basura
inofensiva, no bloquea nada, limpieza opcional para otra sesión. También hay
`ROMs/fbneo/`, `ROMs/mame/`, `ROMs/cps1/2/3/`, `ROMs/neogeo/` **vacíos** en el nivel
superior de `ROMs/` — el contenido real vive anidado en
`ROMs/arcade/{mame,fbneo,fba,mame2003-plus}/`, que es donde apuntan ambos launchers |
Dispositivo real (RG556), Daijishō + iiSU vía ADB | ✅ verificado 2026-09-27 — sin acción necesaria |
| SAVES-FRAGMENT-9b | **Comprobado el mismo día que el caso de PS2 es aislado, no sistémico.** Mismo método (contenido real + `dumpsys usagestats`) aplicado a los otros 4 standalone: **DuckStation** (PSX) ok — 27 memcards en su sandbox privado, fechas repartidas todo el año hasta 2026-08-24, sin patrón de reseteo (pendiente real es el ya conocido de SAVES-FRAGMENT-5: nunca se redirigió a ruta pública). **melonDS** (NDS) ok — la sesión de hoy duró 19 s (abrir/cerrar, no hubo partida), saves reales más recientes de octubre 2025, normal. **Dolphin** (GC/Wii) — `files/GC/` y `files/Wii/` están completamente vacías, pero coincide con el uso total ya documentado (~4 min): nunca hubo progreso que perder, no es un caso de pérdida. **PPSSPP** (PSP) — señal débil, solo una carpeta de save (`ULES009150`, abril 2025) y uso histórico muy bajo; no hay suficiente para concluir pérdida ni descartarla, queda abierto si el usuario juega más PSP. Arcade NVRAM (`.nv`) también revisado: tamaños y fechas normales | Hardware + investigación | XS | ✅ verificado 2026-08-29, sin acción necesaria salvo PPSSPP (bajo uso, inconcluso) |
| EMULATOR-COMPAT-5 | **El progreso de arcade nunca se sincroniza** — confirmado en hardware real 2026-08-25 (RG556 conectada por cable). Las extensiones sí están cubiertas (`.nv` en `config.py:562` y `SaveExtensions.kt:16`), pero el problema es la **carpeta**: en esta RG556 el `.nv` (NVRAM/dipswitches) no vive en `saves/`, `states/` ni `system/<core>/` — vive **directamente en `RetroArch/<carpeta-de-plataforma>/`, junto a las propias ROMs** (verificado: 24 archivos en `RetroArch/mame/*.nv` — TMNT2, Simpsons, X-Men, Vendetta…; también `cps1/punisher.nv`, `cps1/wofch.nv`, `cps2/1944.nv` — patrón sistemático, no un caso aislado). El scanner de sync solo recorre `saves_path`/`states_path` (`config.py`) / `RetroArchPaths.kt:11-12` — nunca las carpetas de ROMs. Fix: el scan de arcade tiene que recorrer las carpetas de plataforma arcade completas (mame, fbneo, cps1, cps2, cps3…) filtrando por extensión, no asumir una raíz `saves/states` separada de las ROMs | Hardware + fix | S | 🟡 fix implementado 2026-08-29 en el lado Android (único que corría sin este fix — el sync PC↔consola por cable ya recorre árboles completos por extensión, sin este hueco): `RetroArchPaths.ARCADE_FOLDERS` (`android/.../sync/RetroArchPaths.kt`, mame/cps1/cps2/cps3/fbneo/arcade — mismas claves "Arcade" que `platforms.toml`) + `SyncOrchestrator.runFullSync` ahora sincroniza cada carpeta arcade contra `"$savesRemote/$platform"` (subcarpeta propia en Dropbox, sin colisión con `saves/`); `LocalFileScanner` ya filtraba por `SaveExtensions.isTracked`, así que las ROMs de esas carpetas nunca se suben — sin cambios ahí. Test nuevo `RetroArchPathsTest.kt`. **Compilado e instalado en la RG556 real 2026-09-09**: toolchain portable localizada en `C:\Users\rammu\android-build-tools\` (`jdk17`, `sdk` — la misma usada en `ANDROID-SYNC-1`/`FTP-PICK-2`, no en el repo). `./gradlew test` → `RetroArchPathsTest` y el resto en verde (build ya al día desde 2026-08-29, sin cambios de fuente pendientes). `./gradlew assembleDebug` + `adb install -r app-debug.apk` → éxito en `RG556006101273`. **Verificación del upload real bloqueada, no por ADB**: `SyncOrchestrator.runFullSync()` (`android/.../sync/SyncOrchestrator.kt:20-22`) devuelve `null` si no hay sesión Dropbox activa (`DropboxCredentialStore`) — sin OAuth ya vinculado en el dispositivo no hay forma de disparar el sync (ni por `am start`/intent expuesto: `syncNow()` solo vive en `MainActivity.kt:187`, sin acción exportada) y vincular Dropbox exige el flujo OAuth en pantalla. `dumpsys jobscheduler` confirma 0 jobs de `com.retrovault.android` registrados hoy (nunca se ha ejecutado un sync en este dispositivo). Mismo patrón que `FTP-PICK-2`/`DEVPROFILE-6`: requiere al usuario delante de la pantalla (vincular Dropbox + pulsar "Sincronizar ahora" + confirmar visualmente o via `adb shell find .../saves/mame` que aparecen los `.nv`) |

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

Plan de implementación para los pendientes `-5`/`-6` en
`.claude/roadmaps/16-cable-sync-format-gaps.md`.

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
| CABLE-ROM-FIX-4 | La allowlist de carpetas por plataforma usada en CABLE-ROM-FIX-3 fue manual/ad-hoc (script de orquestación de esa sesión, no persistido). Añadir selector de plataformas incluir/excluir en la UI de Cable Sync (o config), reutilizando `PLATFORM_BY_FOLDER`/`_ES_PLATFORM_FOLDERS` ya existentes, para no tener que rehacerla a mano cada vez que la SD no tenga espacio para todo | `web/handlers/sync_cable.py`, frontend Cable Sync | ✅ nuevo campo `exclude_platform_folders` (lista de carpetas en minúscula, p.ej. `["arcade"]`) en `POST /api/cable-sync` — aplica en `_wanted()` (lado PC/SD, ambos roots) y en el nuevo `_wanted_info()` (lado Android/ADB, junto a `_wanted_name`), cubriendo las 3 direcciones y el espejo (`delete_extra`: una plataforma excluida nunca cuenta como "extra"). `GET /api/platform-folders` nuevo expone `_STANDARD_PLATFORM_FOLDERS` para poblar el `<select multiple>` "Excluir plataformas" en `tab-cable.html`, cargado una vez por sesión de pestaña (`_loadCablePlatformFolders()`, mismo patrón que `_cableModeAutoSelected`). 6 tests nuevos (`tests/test_sync_cable_exclude_platforms.py`); verificado además con smoke test HTTP real contra el servidor (`pc_to_anbernic`, excluyendo `arcade`: solo copió `psx/`). Suite completa 1220/1220 |
| CABLE-ROM-FIX-6 | **Alcance medido 2026-09-11** — el Día59 (2026-09-10) bloqueó Cable Sync en espejo de `ps2`/`psx`/`gamecube` por un desajuste `.chd` vs `.bin`/`.cue` sin cuantificar. Medido por título (extensión aparte) cruzando PC (`E:\Carpetas anbernic\`) contra el dispositivo (ADB, `ROMs/`): **el problema es exclusivo de PSX** — PC tiene `ps2/`/`gamecube/` en `.iso`/`.rvz` en ambos lados (mismo formato), sin ningún `.chd` en ninguno de los dos para esas 2 plataformas salvo un único caso en `ps2/` (`Crash Bandicoot - The Wrath of Cortex.chd`, solo en el dispositivo, sin ninguna versión equivalente en el PC en ningún formato — no es un mismatch de formato, es contenido exclusivo del dispositivo, categoría de riesgo distinta e inherente a cualquier espejo). En PSX sí es real y grande: de los **129 títulos que el dispositivo tiene como `.cue`/`.bin`**, **70 (54%) ya están convertidos a `.chd` en el PC** — esos 70 (**127 archivos `.bin`/`.cue`, 32,75 GB**) son exactamente el patrón que causó el incidente de `TRASH-FIX-5` (`Castlevania - Symphony of the Night`, `Crash Bandicoot`, etc., están en esta lista) y que un espejo `delete_extra=true` seguiría interpretando como "extra" a borrar por comparar solo ruta/nombre exacto, no contenido. Conclusión: `gamecube`/`ps2` **no tienen el bloqueante de formato** — solo espacio (`CABLE-ROM-FIX-3`); **solo `psx` sigue bloqueado** hasta que el espejo (o una conversión previa a `.chd` en el dispositivo) reconozca `.chd`≡`.cue`/`.bin` del mismo juego.

**Implementado (2026-09-22, Día69, roadmap 16)**: opción (b) elegida por el
usuario — comparación cross-formato en el espejo, sin mover ni convertir
nada. `normalize_title_cross_format()` (antes `_normalize_title_cross_format`,
privada de `web/builders/duplicates.py`, movida a `utils/disc_tag.py` para
poder compartirla con `sync_cable.py` sin acoplar el módulo de sync al de
duplicados) normaliza el stem quitando el tag de disco; nuevo
`_DISC_IMAGE_EXTENSIONS` (`.chd`/`.cue`/`.gdi`/`.ccd`/`.iso`) acota el guard
solo a formatos de imagen de disco — un cartucho (`.gb`/`.gba`/...) con el
mismo título tras quitar el tag nunca debe suprimir su propio borrado, ahí sí
importa el nombre exacto. Antes de marcar cualquier archivo como "extra" en
los 4 sitios de `web/handlers/sync_cable.py` (`delete_extra`, modo ADB y modo
filesystem/SD, ambas direcciones), se comprueba si el otro lado ya tiene un
archivo de imagen de disco con el mismo título normalizado, en cualquier
formato — si lo tiene, no se borra. Fallo asimétrico a propósito: en el peor
caso dos discos distintos con el mismo título salvo el número de disco (un
set multi-disco real) coinciden por error y uno se queda sin sincronizar
silenciosamente — nunca se borra nada real, mismo criterio que "ante duda, no
sobreescribir" del proyecto. 2 tests nuevos (`tests/test_sync_cable_cross_format.py`,
modo filesystem, ambas direcciones): confirmados en rojo contra el código
anterior (`git stash`) y en verde tras el fix. Suite completa: 1430 tests, 0
regresiones. Paso 1 del roadmap (sync real de `gamecube`) sigue pendiente —
es solo ejecución, no código, fuera de esta sesión (requiere ADB conectado). | `utils/disc_tag.py` (`normalize_title_cross_format`, movida), `web/builders/duplicates.py` (import actualizado), `web/handlers/sync_cable.py` (`_DISC_IMAGE_EXTENSIONS`, `_cross_format_stems`, `_is_cross_format_equivalent`, aplicado en los 4 sitios `delete_extra`), `tests/test_sync_cable_cross_format.py` | ✅ hecho 2026-09-22 (Paso 2-3 del roadmap 16) — desbloquea el espejo completo de `psx`; Paso 1 (ejecutar el sync de `gamecube` pendiente) sigue por hacer, requiere hardware |

### CABLE-ROOT-1 — El Cable Sync por ADB apuntaba a almacenamiento interno vacío, no a la SD real del dispositivo (hallazgo 2026-09-13, máquina "Ruben")

Origen: el usuario preguntó por qué "Dark Cloud" (PS2), enviado la noche
anterior a mano por `adb push` (workaround de `ADB-TIMEOUT-1`), no aparecía
en la Anbernic. Verificado en el dispositivo real (mismo `RG556006101273`
usado en `CABLE-ROM-FIX`, hoy conectado a esta máquina en vez de a
`rammu`/`E:\Carpetas anbernic`):

- El archivo está físicamente en el dispositivo, tamaño exacto correcto
  (1.797.980.160 bytes), en `/storage/emulated/0/RetroArch/PlayStation
  2/Dark Cloud (USA).iso` — **almacenamiento interno**, carpeta con nombre
  no canónico (`PlayStation 2`, no `ps2`).
- La biblioteca real que usa el launcher (Daijishō) vive en la **SD
  externa**, `/storage/521D-04EA/ROMs/<plataforma>/` (mismo ID de SD que ya
  aparece en `CABLE-ROM-FIX`) — cientos de ROMs reales con `mtime` reciente
  (hasta 2026-09-09), `ps2/` con 20 títulos, `gba/` con 471, `dreamcast/`
  con 68. `/storage/emulated/0/RetroArch/<plataforma>/` en cambio solo tiene
  saves sueltas y el `gamelist.xml` de caché de Daijishō — prácticamente
  sin ROMs reales (confirmado en `ps2/`: 0 ROMs, solo el `gamelist.xml`).
- Los 2 juegos de Dreamcast enviados la misma noche (`Sonic Adventure
  (Europe)`, `Crazy Taxi 2 (Europe)`) tienen el mismo problema aunque la
  carpeta sí tuviera nombre canónico (`dreamcast/`) — el root de
  almacenamiento (interno, no SD) es la causa, no solo el nombre de
  carpeta. La SD ya tiene versiones de ambos juegos con otra región
  (`Crazy Taxi 2 (Japan)`, `Sonic Adventure (World) (XBLA)`) — no son el
  mismo archivo, así que copiar las versiones Europe no sería un duplicado
  exacto, pero sí conviene decidirlo a propósito, no por accidente.
- Causa raíz en código: `config.sync.auto_sync_android_path`
  (`src/rom_manager/config.py:199`, default `/storage/emulated/0/RetroArch`)
  es el valor que cae por defecto en `POST /api/cable-sync` cuando no se
  pasa `android_path` explícito (`web/handlers/sync_cable.py:259-263`) —
  exactamente lo que pasó en el intento real de anoche (log real en
  `.rommgr/cable_sync_ops.log`, entrada `22:44:06Z`, ya calculaba destino
  `/storage/emulated/0/RetroArch/PlayStation 2/...` antes de abortar por
  `ADB-TIMEOUT-1`). El `adb push` manual de después repitió el mismo root
  por costumbre/no verificación, no por el código. Nada valida que
  `android_path` (explícito o default) coincida con dónde vive realmente la
  biblioteca del dispositivo — un push puede "tener éxito" (tamaño exacto,
  0 errores) y quedar completamente invisible para el usuario.
- Relacionado: `cable_engine.plan_direction()` (`sync/cable_engine.py:63`)
  espeja el nombre de carpeta del PC tal cual (`ab_root /
  src.relative_to(pc_root)`), sin traducir a slug canónico — si la carpeta
  del PC sigue con nombre antiguo (`PlayStation 2`, `Game Boy Advance`, ver
  `MDFOLDER-FIX-2`/`MATCH-FIX-5`, aún sin renombrar físicamente), el
  espejo reproduce ese mismo nombre no-canónico en el lado Android incluso
  apuntando al root correcto.

**Resuelto en vivo (2026-09-13), con confirmación explícita del usuario para cada paso:**

- PS2: verificado que ni `Dark Cloud (USA)` ni `Viewtiful Joe 2 (USA)` existen
  ya en la SD real (`ls` completo de `ps2/`, 20 títulos, ninguno coincide) —
  movidos con `adb shell mv` (mismo dispositivo, entre `/storage/emulated/0`
  y `/storage/521D-04EA`, sin pasar por el PC) a
  `/storage/521D-04EA/ROMs/ps2/`. Carpeta `PlayStation 2/` (interna, ya
  vacía) eliminada.
- Dreamcast: la política pedida por el usuario ("comprobar qué versión tiene
  logros y quedarse con esa, aplicar también a GBA y a todo lo que se mande
  desde Inbox") resultó innecesaria aquí por un hallazgo más fuerte —
  **hash real, no solo tamaño**: se descargó (`adb pull`) la copia ya
  presente en la SD y se comparó SHA1 contra la copia huérfana del interno.
  `Sonic Adventure (World) (XBLA).cdi` (SD) = `14c6fb4f...` = idéntico byte
  a byte a `Sonic Adventure (Europe)` (interno/PC). `Crazy Taxi 2 (Japan)
  (En,Ja).cdi` (SD) = `64c48ecc...` = idéntico a `Crazy Taxi 2 (Europe)`
  (interno/PC). **Son el mismo dump exacto con la etiqueta de región mal
  puesta en la SD** — no duplicados reales, el mismo archivo. Las 2 carpetas
  huérfanas del interno se borraron (`rm -rf`), nada que mover: el
  contenido ya estaba en la SD.
- `config.toml` (máquina "Ruben"): añadido `[sync] auto_sync_android_path =
  "/storage/521D-04EA/ROMs"` — corrige el default para que cualquier Cable
  Sync ADB futuro desde esta máquina apunte a la SD real, no al interno.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-ROOT-1a | Mover los 4 archivos huérfanos de anoche a la SD real | dispositivo (ADB) | ✅ hecho 2026-09-13 — PS2 movidos, Dreamcast resultaron duplicados exactos del mismo dump ya presente (etiqueta de región distinta), solo se borró el huérfano |
| CABLE-ROOT-1b | Fijar `auto_sync_android_path` a la SD real para esta máquina | `config.toml` (máquina "Ruben") | ✅ hecho 2026-09-13 |
| CABLE-ROOT-1c | Validación real: antes de un Cable Sync ADB, comparar cuántos archivos ya existen bajo `android_path` vs. el tamaño esperado de la plataforma — si el destino está sospechosamente vacío comparado con el origen, avisar en vez de copiar en silencio a un sitio que el launcher no vigila | `web/handlers/sync_cable.py` | ✅ hecho 2026-09-13 (roadmap `11-cable-sync-android-root-canonical.md`, rama `fix/cable-sync-android-root-canonical`). Antes de una corrida real (`dry_run=False`, `pc_to_anbernic`) por ADB, por cada carpeta de plataforma del PC con ≥20 archivos cuyo slug canónico en el dispositivo tiene 0 archivos, se registra un evento `WARN` en `cable_sync_ops.log` (no bloquea el job) — reutiliza el `ab_index` ya calculado, sin viaje ADB extra. 3 tests nuevos (`tests/test_cable_sync_root_canonical.py`: avisa sobre el umbral, no avisa bajo el umbral, no avisa si el dispositivo ya tiene archivos). Mergeado a `develop` en
`fc29e09` (2026-09-13) — este backlog seguía diciendo "pendiente" por error,
corregido 2026-09-15 |
| CABLE-ROOT-1d | `plan_direction()` debería traducir el nombre de carpeta del PC a su slug canónico de Android (reutilizar `PLATFORM_BY_FOLDER`/`_ES_PLATFORM_FOLDERS`) en vez de espejar el nombre literal — evita que carpetas del PC aún no renombradas (`MDFOLDER-FIX-2`) contaminen el nombre de carpeta en el dispositivo aunque el root ya sea correcto | `sync/cable_engine.py:51-107` | ✅ hecho 2026-09-13 (mismo roadmap/rama que `CABLE-ROOT-1c`). Nuevo `sync/android_paths.py::canonical_rel_posix()` (reusa `PLATFORM_BY_FOLDER`+`_ES_PLATFORM_FOLDERS`, sin tabla nueva) aplicado en los 3 call sites ADB de `sync_cable.py` que construyen `rel_posix` desde el PC (líneas ~781, 932/938, 1134 antes del fix) y en `cable_engine.plan_direction()` (ramas `pc_to_anbernic` y `newest` cuando gana el PC, nuevo parámetro `es_platform_folders` con default `{}` — sin romper callers existentes). Efecto colateral bueno: `_skip_existing_device()` ahora compara contra la clave android-canónica real, no la ruta cruda del PC (estaba comparando mal para carpetas no renombradas). Verificado con "PlayStation 2" → "ps2": 5 tests nuevos (`test_android_paths.py`, `test_cable_engine.py`, `test_sync_cable_exclude_platforms.py` modo filesystem, `test_cable_sync_root_canonical.py` modo ADB). 1323 tests totales, ruff+format limpios. **Fuera de alcance deliberadamente**: el caller de `cable_sync_daemon.py:478` (SD-auto-sync de *saves*, no ROMs — Pilar 3, máxima sensibilidad) no se tocó — mismo `plan_direction()` pero sin pasar `es_platform_folders` (default preserva el comportamiento actual); decidir aparte si aplica ahí, con su propia verificación. Mergeado a
`develop` en `fc29e09` (2026-09-13) — este backlog seguía diciendo
"pendiente" por error, corregido 2026-09-15 |
| CABLE-ROOT-1e | Medido 2026-09-13 sobre `dreamcast/gamecube/ps2/psx/wii/psp` (comparando tamaño exacto SD vs `library_pc.db`, 1.671 archivos ≥20 MB, 52 candidatos con tamaño idéntico + título distinto). **Conclusión: el tamaño solo no basta como señal — verificado por SHA1 real en 3 casos**: `GameCube` descartado por completo como método (1.459.978.240 bytes es el tamaño fijo del disco GC — 16 títulos distintos comparten ese tamaño, colisión total, no aporta nada). `PlayStation` (tracks `.bin` sueltos) también con muchos falsos positivos — tracks de audio CD de duración redonda (37.396.800 bytes aparece en 6 juegos sin relación). De los 2 candidatos únicos verdaderamente sospechosos (`Silent Hill (USA)` vs `New (Slovakia) (Art Assets)`; `Resident Evil 3 - Nemesis (USA)` vs `Resident Evil 3 (Australia)`), **ninguno resultó ser el mismo contenido** (SHA1 distinto en ambos, `adb pull` + `sha1sum` real) — coincidencia de tamaño, no mismo dump. En cambio, en `PlayStation 2`/`PSP` sí se confirmó contenido real: `Dragon Ball Z - Budokai Tenkaichi 3` (SD, con región) y `DragonBall Z - Budokai Tenkaichi 3.iso` (PC, sin espacio/región) son **el mismo archivo exacto** (SHA1 idéntico verificado) — no es una región mal etiquetada, es el mismo dump con dos nombres, el del PC sin pasar aún por el renombrador (mismo patrón que `Prince of Persia TTT.iso`/`WW.iso`, `SLUS-21386 (1.00).iso`/Tales of the Abyss, `Tenchu Fatal Shadows.iso` — todos con tamaño único coincidente, no verificados uno a uno pero con alta confianza tras confirmar el primero). **No se encontraron más casos de región mal etiquetada como el de Dreamcast de hoy** en esta pasada — el patrón parece limitado a esos 2 títulos, no generalizado en la biblioteca | `.rommgr/library_pc.db` + SD (ADB) | ✅ medido — sin más casos de mislabel confirmados; ver `CABLE-ROOT-1f` para la lección de método |
| CABLE-ROOT-1f | Política pedida por el usuario para futuros envíos desde Inbox/GBA: cuando haya candidatos a duplicado entre plataformas/regiones, decidir cuál conservar por **logros de RA reales** (`services/ra_duplicates_service.get_ra_achievements`, ya usado en `resolve-duplicates`) en vez de por nombre/región — extender ese criterio a cualquier comparación PC↔Anbernic, no solo a duplicados dentro de una misma biblioteca. **Lección de método de `CABLE-ROOT-1e`**: el tamaño exacto de archivo NO basta para decidir "es el mismo juego" — falsos positivos reales confirmados (discos GameCube de tamaño fijo, tracks de audio CD de duración redonda). Cualquier implementación de esta política debe confirmar por **hash real** (SHA1 ya calculado en `games.sha1`, o el hash RA vía `compute_dreamcast_ra_hash`/equivalente por plataforma) antes de decidir cuál copia conservar — nunca por tamaño o nombre solos | `services/ra_duplicates_service.py` | 🟡 **re-investigado 2026-09-14**: la política ya existe y ya es genérica por plataforma — `filter_duplicate_winners()` (`services/ra_duplicates_service.py:318`, docstring dice explícitamente "used before a bulk push to the Anbernic") agrupa por `(platform, canonical_title)` exacto y elige ganador por logros RA (`get_ra_achievements`, parametrizado por `platform`, no hardcodeado a PSX), y ya está conectada al endpoint real de envío masivo `send_selected` (`web/handlers/sync_cable.py:1084`, "ANBERNIC-BULK-SEND") con `dedupe_by_ra=True` por defecto — este endpoint también compara con lo ya existente en el dispositivo por **ruta relativa completa** (`_skip_existing_device`, línea 727), no solo por nombre de archivo (a diferencia del bug real del script ad-hoc de ayer). **Gap real que queda** (la parte de `CABLE-ROOT-1e` que sí sigue sin cubrir): esto agrupa por `canonical_title` exacto **dentro de la biblioteca del PC antes de enviar** — no compara contra archivos que YA están en el dispositivo bajo un nombre/región distinto (el caso real de Dreamcast Sonic Adventure Europe/World de ayer), porque no existe hash remoto (`_do_adb_scan` no calcula sha1/md5 en el dispositivo, ver hallazgo ya documentado en Día62). Sin ese hash remoto, ese caso concreto seguiría sin detectarse automáticamente hoy — bajo riesgo para GBA (cartuchos, dumps casi siempre únicos), pero sigue abierto como diseño si se quiere cerrar del todo |

---

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
> `what` explícitamente | `web/handlers/sync_cable.py:372-382` | ✅ `_cat_name()` ahora
> resuelve contra `ROM_EXTENSIONS` (`detection/platform_detector.py`, la misma
> tabla ya fiable del Inbox y de `LIB-MISPLACED-1`) en vez de asumir "rom" por
> descarte: extensión de save → `"save"`, extensión de ROM reconocida →
> `"rom"`, cualquier otra cosa → `"other"`. `_wanted_name()` solo considera
> `"other"` deseado si `"assets"` está explícitamente en `what` — con
> `what=["roms"]` (el caso real del incidente), carátulas/metadatos ya no
> cuentan como "extra" ni se copian ni se borran. `_category()` (usado solo
> para gating de backup de saves) no se tocó — sigue siendo binario
> save/rom, sin riesgo porque solo protege la rama "save". 3 tests nuevos
> (`tests/test_sync_cable_other_category.py`): reproduce el incidente exacto
> (espejo con `what=["roms"]` no borra `.jpg`/`.txt`/`.xml`/`.ini` huérfanos),
> confirma que el espejo real de ROMs sigue funcionando, y que pedir
> `"assets"` explícitamente sí permite espejar "other" |
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
| FTP-PICK-2 | **Pantalla "Elegir ROMs" en la app Android (ANDROID-SYNC)** — decisión final del usuario: quería el flujo dentro de la app nativa que ya se está construyendo, no solo un enlace en el navegador. En vez de repetir el error del primer intento (protocolo FTP a mano + cliente Kotlin a medida, descartado), la app llama por HTTP normal a los mismos dos endpoints ya probados en el lado Python (`GET /api/games` para buscar/filtrar, `GET /api/download-rom` para bajar) — cero protocolo nuevo, cero librería nueva (`HttpURLConnection`/`org.json` son parte de la plataforma Android, igual que el SDK de Dropbox ya en uso). `PcApiClient.kt` nuevo: `listPlatforms()`/`listGames()` parsean el JSON ya devuelto por el PC, `downloadRom()` guarda en `<romsDestPath>/<carpeta-de-plataforma-real-del-PC>/<nombre>` — la carpeta se deduce del propio `source_path` que ya devuelve `/api/games` (segmento inmediatamente anterior al nombre de archivo), sin necesitar conocer `library_root` del PC. Pantalla `ui/pick/PickScreen.kt` (formulario IP:puerto → lista de plataformas + buscador + lista de juegos con descarga y progreso), tercera pestaña en `MainActivity.kt`. Ajustes nuevos en `SettingsRepository.kt` (`pcHost`, `romsDestPath`). `usesCleartextTraffic="true"` en el manifest (HTTP plano, no HTTPS — mismo modelo de confianza de LAN doméstica que `allow_lan` en el PC; sin login, asume el PC sin PIN activo, limitación conocida documentada en el propio código) | `android/app/src/main/java/com/retrovault/android/sync/PcApiClient.kt` (nuevo), `ui/pick/PickScreen.kt` (nuevo), `data/prefs/SettingsRepository.kt`, `ui/MainActivity.kt`, `AndroidManifest.xml` | ✅ **compilado y verificado 2026-08-29** con toolchain portable (`JAVA_HOME`=jdk17, `./gradlew test assembleDebug`, ambos en verde). Encontrado y arreglado un bug real de compilación: `PickScreen.kt:9` importaba `androidx.compose.foundation.layout.weight` como función de paquete — `weight` es en realidad un método miembro de las interfaces `RowScope`/`ColumnScope` (no una función top-level importable), así que el import resolvía a un símbolo interno no relacionado y rompía `compileDebugKotlin`/`compileReleaseKotlin`. Fix: eliminar el import — los dos usos de `.weight(1f)` ya están dentro de lambdas `Row{}`/`Column{}`, se resuelven solos por receiver implícito sin necesitar import. `./gradlew test` (incluye `PcApiClientTest.kt`, 3 tests) en verde. **2026-09-08 — instalación real confirmada, interacción manual bloqueada**: `app-debug.apk` del 2026-08-30 (coincide byte a byte con el HEAD actual, working tree limpio en `android/`) instalado con `adb install -r` en la RG556 real — éxito. `rommgr serve` real levantado en `192.168.1.160:7777` (misma red que el WiFi de la RG556, `192.168.1.165`), API respondiendo (`GET /api/games` → 200). `am start -n com.retrovault.android/.ui.MainActivity` confirma que la Activity ya está en primer plano sin crash ("Warning: Activity not started, its current task has been brought to the front" = ya estaba arriba). **No se pudo completar la prueba interactiva** (introducir IP, listar juegos, descargar): la pantalla de la RG556 vuelve a dormirse casi al instante pese a `KEYCODE_WAKEUP`/`wm dismiss-keyguard` (settings dice `screen_off_timeout=1800000`, no explica el comportamiento) — 3 de 4 capturas salieron en negro (10.608 bytes, tamaño idéntico = mismo frame vacío), sin margen para tocar la UI a ciegas por ADB. Sin cambios de código; validación de tap-through sigue pendiente de hacerse a mano por el usuario frente al dispositivo |

---

### GAME-BLOCKLIST — Eliminar un juego de ambas bibliotecas y evitar que un sync lo recupere (feedback usuario 2026-08-29)

Plan de implementación en `.claude/roadmaps/18-game-blocklist.md`.

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
| GAME-BLOCKLIST-1 | Diseñar la marca de exclusión permanente (tabla dedicada `blocklist`: sha1, canonical_title, reason, created_at — decisión confirmada con el usuario 2026-09-24, no el patrón `game_tags`) + acción "Eliminar de ambas bibliotecas" (PC → papelera `_descartados/`, Anbernic → `AdbTransport.remove`, mismo patrón de `STORAGE-MGR-3`/`services/storage_service.py`, marcando ANTES de borrar) | `database/schema.py`, `database/repositories/blocklist.py` (nuevo), `services/storage_service.py` (`block_and_delete_game`), `web/handlers/collection.py` (`POST /api/blocklist/block`), UI: `web/static/partials/_foot.html` + `web/static/js/tabs/games.js` (`gpBlockAndDelete`) | ✅ hecho (2026-09-24) |
| GAME-BLOCKLIST-2 | Hacer que el scan/match/Inbox respeten la marca — un archivo con SHA1 bloqueado no se re-organiza ni se re-cuenta como pendiente si reaparece (p. ej. tras un sync `anbernic_to_pc` o un `adb pull` manual); decisión confirmada con el usuario 2026-09-24: se avisa una vez y se deja para revisión manual (nunca auto-descarte silencioso) | `database/repositories/games.py` (`get_unresolved_games`/`get_matched_games` excluyen sha1 bloqueados), `web/inbox_pipeline.py` (paso "organizar" salta bloqueados + `blocked_found` en el resultado), `web/handlers/collection.py` (`/api/sync-roms` rechaza sha1 bloqueado en ambas direcciones), `web/static/js/tabs/inbox.js` (aviso en el resultado del job) | ✅ hecho (2026-09-24) |

---

### SYNC-WII-SCOPE-1 — `SyncSource` no puede acotar solo los saves reales de Dolphin (Wii) (hallazgo rammu, 2026-09-21)

Al reestructurar `sync.sources` en rammu siguiendo `Tareas/Estructura-Estandarizada-Sync.md`
(convenio `dropbox:/RetroSync/saves/<emulador>/<tipo>` de PC2, `dolphin/gc` +
`dolphin/wii`), la fuente `Dolphin (Wii)` con `local_dir` apuntando a la
carpeta `Wii/` completa (`sync_all=true`) empezó a subir el NAND emulado
entero (`title/<tipo>/<id>/content/` = IOS, System Menu, apps de canales
instalados — `.app`, certificados `.pem`, `fst.bin`), no solo los saves.
Medido en rammu: **96 MB en `Wii/` total, de los que solo 0.29 MB son saves
reales** (`title/*/*/data/`, el equivalente NAND del save real por juego —
`title/00010000/<gameid-hex>/data/`). `SyncSource` solo soporta un
`local_dir` plano (sin include/exclude), así que no hay forma de acotar hoy
a "todas las subcarpetas `data/` bajo `title/*/*`" sin sincronizar también
`content/` (las apps instaladas). Parado a mitad de sync real (`--apply`)
antes de subir más basura; fuente `Dolphin (Wii)` desactivada en
`config.toml` (comentada, con la medición) hasta que se diseñe bien.
**GC no tiene este problema** — su carpeta ya es 100% saves (`.gci` +
`.raw`), se dejó activa. **Limpieza pendiente**: revisar
`dropbox:/RetroSync/saves/dolphin/wii` — puede tener algunos `.app`/`.pem`
subidos antes de parar el proceso (no es sensible ni gran volumen, pero es
basura que no debería estar ahí).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| SYNC-WII-SCOPE-1 | Sincronizar solo `title/*/*/data/` de Dolphin (Wii) | `config.py` (`SyncSource.include_glob`), `sync/save_syncer.py` (`list_local_saves`, `sync_saves`), `cli.py` (x2), `web/handlers/sync_cloud.py` | ✅ hecho 2026-09-21 — opción (a): campo `include_glob: str = "**/*"` en `SyncSource` (compatible hacia atrás, resto de fuentes sin cambio de comportamiento), usado en `saves_dir.glob(include_glob)` en vez del `rglob("*")` fijo. `config.toml` reactivado con `include_glob = "title/*/*/data/**/*"`. Test `test_list_local_saves_include_glob_scopes_dolphin_wii_nand` en `tests/test_save_syncer.py`. Verificado en dry-run real contra el NAND de rammu: 10 archivos detectados (todos bajo `data/`), `content/`/`shared1/`/etc. excluidos — antes eran 96 MB, ahora ~0.29 MB reales. Pendiente aplicar en PC2 y reactivar allí también |
| SYNC-WII-SCOPE-2 | Limpiar `dropbox:/RetroSync/saves/dolphin/wii` de archivos de sistema subidos por error antes de detectar SYNC-WII-SCOPE-1 (`.app`, `.pem`, `fst.bin` — no saves) | — (limpieza manual en Dropbox o vía `rclone delete`) | ✅ hecho 2026-09-21 — `tools/rclone.exe purge` sobre la carpeta entera, confirmado vacía (53 archivos, 17.4 MB, 0 saves reales entre ellos) |

---

### CABLE-SYNC-DUP-PATHS-1 — investigación cable-sync ADB con la Anbernic real (rammu, 2026-09-21) — cerrada, no era un bug

Con la Anbernic conectada por USB (autorizada, `adb devices` → `device`), se
probó `POST /api/cable-sync` (`direction=pc_to_anbernic`, `use_adb=true`,
`dry_run=true`). Primer intento con `pc_path=E:\Carpetas anbernic` (raíz de
la biblioteca): **528/528 marcados para copiar, 0 ya coincidentes** —
sospecha inicial de bug real de matching, **descartada tras seguir la
cadena hasta la causa raíz** (regla "Investigar antes de arreglar",
CLAUDE.md):

1. **Error de test #1 — `pc_path` incorrecto**: se pasó la raíz de la
   biblioteca (`E:\Carpetas anbernic`) en vez de la carpeta de saves
   (`E:\Carpetas anbernic\saves`). En Android, RetroArch guarda los saves
   planos junto a la plataforma (`RetroArch/mame/fixeight.nv`), sin
   subcarpeta `saves/` — con `pc_path` mal puesto, TODAS las rutas
   relativas quedaban desalineadas por ese segmento de más. Repetido con
   `pc_path=.../saves`: bajó a 229/229 copiar, seguía en 0 skipped.
2. **Error de test #2 — falta `skip_existing: true`**: `_skip_existing_device()`
   (`web/handlers/sync_cable.py:729`) devuelve `False` sin comprobar nada
   si `skip_existing` no viene en el payload — **por defecto es `false`**,
   así que cualquier dry-run sin ese flag marca todo como "a copiar" aunque
   ya exista igual en el dispositivo. No es un bug, es un parámetro opt-in
   de la propia API (ver `openapi.json` — no aparece en el ejemplo de
   payload, por eso se me pasó la primera vez). Con
   `pc_path=.../saves` + `skip_existing=true`: **123 ya coinciden (mismo
   tamaño), 106 realmente faltan, 0 errores** — número coherente, cierra
   la investigación.

**Hallazgo secundario real, menor**: 8 nombres de save duplicados en 2-3
rutas distintas del dispositivo (19 de 288 archivos totales) — restos de un
`savefile_directory` mal configurado en el pasado en la Anbernic (mismo
patrón de drift que `retroarch_cfg_writer.py` en PC, ver commit `ac9e905`
de hoy), ejemplo verificado con `adb shell find ... -iname 'punisher.nv'`:
`RetroArch/saves/cps1/punisher.nv` (convenio nuevo) +
`RetroArch/cps1/punisher.nv` + `RetroArch/cps1/fbneo/punisher.nv`
(legado). Solo 19 archivos, no bloquea nada — separado en su propia tarea.

**No se ejecutó ningún `--apply` real** en esta sesión (quedó todo en
dry-run) — 106 archivos / ~230 MB reales pendientes de subir a la
Anbernic, listos para aplicar en la próxima sesión con los parámetros ya
correctos (`pc_path=.../saves`, `android_path=/storage/emulated/0/RetroArch`,
`skip_existing=true`).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
**Mapeo completo + backup hechos 2026-09-21** (rammu, con la Anbernic real
por ADB) — **no se borró nada del dispositivo**, decisión del usuario
("informe + backup, sin borrar todavía"). 823 archivos de save/state en el
dispositivo, **289 nombres duplicados en rutas legado (706 archivos
implicados)** — mucho mayor que la estimación original de 8. Clasificados
en `.rommgr/legacy_dups_report_2026-09-21.csv` (gitignored, local):

| Clasificación | Grupos | Criterio |
|---|---|---|
| `junk_zero_bytes` | 14 | Todas las copias son 0 bytes — basura, sin riesgo de pérdida |
| `safe_same_copy_event` | 145 | Mismo tamaño, mtimes a ≤60s entre sí — típico de una migración puntual (mismo patrón que `CABLE-SYNC-SAVES-PREFIX-1`: "Advance Wars 2 [E].sav", 2s de diferencia) |
| `review_time_gap` | 123 | Mismo tamaño pero mtimes separados >60s — mismo tamaño no garantiza mismo contenido, revisar caso a caso antes de decidir |
| `CONFLICT_diff_size` | 7 | Tamaño distinto entre copias — divergencia real de contenido, **nunca borrar automáticamente** |

**Por qué no se automatizó el borrado ni con criterio "más reciente":**
uno de los 7 grupos conflictivos (`Pokemon - Edicion Plata SoulSilver
(Spain).sav`) tiene 3 copias — dos idénticas de 512KB (`nds/` y
`saves/nds/`, duplicado real y seguro) y una tercera de **0 bytes** en
`emulator_saves/me.magnum.melonds/saves/` con el mtime más reciente
(2026-08-28). Un criterio ciego de "quedarse con la copia más nueva por
fecha" habría elegido el archivo vacío y descartado la partida real de
512KB — la razón por la que esta tarea sigue sin automatizar el borrado
(Pilar 3: "cualquier bug aquí es prioridad absoluta, pérdida de progreso").
Los otros 6 grupos conflictivos son el mismo patrón: saves antiguos del
core `VBA Next` (abandonado) junto a saves mucho más recientes del core
`gba` actual — casi seguro seguros de borrar, pero no decidido
automáticamente sin revisión humana.

**Backup completo**: los 706 archivos de los 289 grupos (TODAS las
copias, no solo las "candidatas a borrar") están en
`.rommgr/legacy_dups_backup_2026-09-21/` (gitignored, local, misma
estructura relativa que el dispositivo) — 706/706 ok, 0 errores.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-LEGACY-DUPS-1 | Limpiar en la Anbernic los saves duplicados en rutas legado — no bloquea el cable-sync normal (`CABLE-SYNC-SAVES-PREFIX-2` ya lo hace robusto a esto), solo deja basura residual | — (limpieza manual en el dispositivo, sin tocar código) | ✅ **completo 2026-09-21**. Primera pasada (bajo riesgo, tamaño/fecha): 159 grupos/240 archivos (`junk_zero_bytes` + `safe_same_copy_event`) borrados, backup previo intacto, 0 errores — ver detalle abajo. **Segunda pasada (los 130 grupos restantes, `review_time_gap` + `CONFLICT_diff_size`) resuelta por contenido real**: en vez de decidir por tamaño/fecha (arriesgado — el `size_bytes` de un save GBA de tamaño fijo no dice nada del contenido), se calculó el SHA1 real de cada copia contra el backup local ya hecho (sin tocar el dispositivo, que estaba ocupado con el rescan `ps2` de `ANDROID-DUP-2`). Resultado: de 321 archivos en esos 130 grupos, **174 eran copias byte-idénticas de verdad** (mismo contenido exacto, solo cambiaba la ruta/fecha) — borradas vía `adb shell rm`, 0 errores, verificado post-borrado que las 147 rutas canónicas conservadas (una por cada contenido realmente distinto) siguen intactas. **Ningún archivo de contenido único se tocó** — incluye casos con saves reales de un core distinto (p. ej. `Metroid - Zero Mission [E].srm` tiene un save propio bajo `saves/mGBA/` además del de `VBA Next`/`gba`), que quedan sin resolver a propósito, decisión del usuario si alguna vez hace falta. **Hallazgo colateral nuevo, sin implementar**: 2 grupos tenían copias bajo `saves/.stversions/<core>/` — carpeta de versionado de Syncthing (herramienta de terceros en el dispositivo, no creada por este proyecto), debería excluirse del escaneo/legacy-dup igual que `_descartados/`/`emulator_saves/`, no se ha tocado. Backup completo de las 3 pasadas sigue en `.rommgr/legacy_dups_backup_2026-09-21/` |
| CABLE-SYNC-APPLY-1 | Ejecutar el `--apply` real de `pc_to_anbernic` con los parámetros ya validados (`pc_path=E:\Carpetas anbernic\saves`, `android_path=/storage/emulated/0/RetroArch`, `skip_existing=true`, `safe_mode=true`) — 106 archivos / ~230 MB pendientes de subir | — | ✅ hecho 2026-09-21 — 106 subidos, 123 ya coincidían, 0 errores, 232 MB, coincide exacto con el dry-run |

---

### CABLE-SYNC-SAVES-PREFIX-1 — cable-sync ADB no reconoce el convenio D2 `saves/` del PC — afecta a la UI real, no solo al test de arriba (rammu, 2026-09-21)

Al ejecutar `CABLE-SYNC-APPLY-1` con `pc_path` apuntando **directamente** a
`E:\Carpetas anbernic\saves` (no a la raíz de la biblioteca) tuvo que
usarse a propósito para que el matching funcionara. Pero **la UI real
(`sync.js:940`, `_setIfEmpty('cable-pc-path', ... cfg.library_root ...)`)
por defecto pone `pc_path = library_root`** (la raíz completa, no
`.../saves`) — necesario porque el mismo campo también sirve para
sincronizar ROMs, no solo saves. Con ese valor por defecto, cualquier
usuario que haya centralizado sus saves con el convenio D2
(`savefile_directory = library_root/saves`, el mismo botón "Aplicar
layout de saves" arreglado hoy en `ac9e905`) sufriría el mismo problema
que el primer intento de `CABLE-SYNC-DUP-PATHS-1`: **todos los saves se
marcarían como "nuevos"** en vez de detectarse como ya sincronizados,
porque la ruta relativa del lado PC lleva el prefijo `saves/` y la del
lado Android no.

**Causa raíz confirmada en código**: `canonical_rel_posix()`
(`sync/android_paths.py`) traduce el primer segmento (carpeta de
plataforma) usando `PLATFORM_BY_FOLDER`/`_ES_PLATFORM_FOLDERS`, pero por
diseño explícito (su propio docstring) **no toca segmentos que no
reconoce como plataforma — y `saves` es uno de ellos**: `"no inventa una
carpeta nueva para algo que no reconoce (p. ej. carpetas de sistema como
BIOS/ o saves/)"`.

**No es un fix trivial de una línea** — verificado en el dispositivo real
(`adb shell find`/`ls_recursive` sin filtro) que **el propio Android
mezcla convenios según el core**: algunos escriben el save plano junto a
la plataforma (`RetroArch/mame/fixeight.nv`), otros ya usan su propia
subcarpeta `saves/<core>/` (`RetroArch/saves/mame2003/nvram/mk3.nv`,
`RetroArch/saves/bsnes2014/Earthbound (1).srm`) — quitar sin más el
prefijo `saves/` del lado PC rompería el matching para los cores que sí
lo tienen en Android. Necesita diseño, no un parche a ciegas, en el pilar
de mayor riesgo del proyecto ("cualquier bug aquí es prioridad absoluta",
CLAUDE.md).

**Mapeo real completado (rammu, 2026-09-21, `adb shell find`/`stat` sobre la
Anbernic conectada)** — el problema es mucho más grande que los "8
duplicados" estimados en `CABLE-SYNC-LEGACY-DUPS-1`: hay carpeta plana
(`RetroArch/<plataforma>/`) Y carpeta `saves/` para prácticamente todas las
plataformas probadas, con solapamiento de nombre de archivo casi total y
**ambas copias con actividad reciente** (no es basura histórica de una
migración puntual — algunos juegos escriben en un lado, otros en el otro,
en la misma sesión de uso):

| Plataforma | Archivos en plano | Archivos en `saves/` | Mismo nombre en ambos |
|---|---|---|---|
| mame | 25 | 24 | 24 |
| gba | 47 | 115 | 46 |
| psx | 7 | 9 | 6 |
| snes | 4 | 3 | 3 |
| nes | 2 | 3 | 1 |
| cps1 | 3 | 2 | 2 |
| cps2 | 2 | 1 | 1 |

Verificado con `stat` en `Advance Wars 2 [E].sav` (gba): mismo tamaño
(65536 B) en plano y en `saves/`, mtimes a 2 segundos de diferencia
(2025-03-09) — copia puntual antigua, no reescritura activa de ese archivo
concreto. Pero `ls -t` muestra archivos con mtime reciente en **ambas**
ubicaciones (`Pokémon Rojo fuego [E].sav` en plano, `Pokemon WaterBlue.srm`
y `Final Fantasy Tactics [E].srm` en `saves/gba`) — confirma que hoy en
día se sigue escribiendo en los dos sitios según qué core/config se use
por partida, no es solo arrastre histórico.

**El nombre de la subcarpeta bajo `saves/` no es consistente**: a veces es
el nombre canónico de plataforma ya reconocido por `PLATFORM_BY_FOLDER`
(`saves/gba`, `saves/psx`, `saves/snes`, `saves/mame`, y por coincidencia
`saves/cps1`/`saves/cps2`/`saves/fbneo`, que están en `platforms.toml`
como alias de "Arcade"), y a veces es el nombre del core de RetroArch tal
cual, que **no** está en `PLATFORM_BY_FOLDER` (`saves/mame2003`,
`saves/bsnes2014`, `saves/Snes9x`, `saves/Snes9x 2005 Plus`,
`saves/VBA Next`, `saves/FCEUmm`, `saves/mGBA`, `saves/PPSSPP`,
`saves/Citra`, `saves/LRPS2`, `saves/Beetle PSX`). No hay mapeo core→plataforma
completo hoy en el código — haría falta construirlo y mantenerlo para
poder confiar en el segundo segmento de la ruta.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-SAVES-PREFIX-1 | Mapear en el dispositivo real qué cores usan `saves/<core>/` vs plano junto a la plataforma | — (investigación en el dispositivo real, sin tocar código) | ✅ hecho 2026-09-21 — ver tabla y hallazgos arriba |

**Hallazgos relacionados, fuera de alcance de este fix** (revisado el código
alrededor de `_skip_existing_device`/`_skip_existing_pc` al implementar,
sin tocarlos — CLAUDE.md "Investigar antes de arreglar"):

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-DOWNLOAD-DEST-1 | Canonicalizar el destino de descarga (`anbernic_to_pc`/`newest`), que escribía en `pc_root / rel_posix` usando la ruta cruda del dispositivo sin canonicalizar | `sync/android_paths.py` (`canonical_download_rel_posix`, nueva), `web/handlers/sync_cable.py` (`_adb_copy_to_pc`, delete_extra ×2), `sync/cable_engine.py` (`plan_direction`, ramas `anbernic_to_pc`/`newest`), `web/cable_sync_daemon.py` (`_adb_copy_to_pc` legacy) | ✅ hecho 2026-09-21 — decisión de diseño confirmada con el usuario: (1) con carpeta intermedia reconocible (`saves/psx/foo.sav`, "psx" SÍ es plataforma conocida) → aterriza en la ruta canónica sin `saves/` (`psx/foo.sav`), igual criterio que ya usa la subida; (2) con carpeta intermedia ambigua (`saves/mame2003/...`, core sin mapear) → se mantiene la ruta cruda, no se arriesga a adivinar mal. Nueva función `canonical_download_rel_posix()` en `android_paths.py`, usada en los 3 sitios que escriben destino de descarga — incluye actualizar los 2 bloques `delete_extra`/espejo que comparaban por ruta cruda (si no, un archivo recién bajado a su ruta canónica se leía como "extra" y se borraba). 8 tests unitarios nuevos (4 en `test_android_paths.py`, 2 en `test_cable_engine.py`, más los de `canonical_download_rel_posix` en sí) cubriendo exactamente el caso `saves/gba/mario.sav → gba/mario.sav` y el caso ambiguo sin tocar. Suite completa (1417 tests) sin regresiones nuevas. **Validado en real 2026-09-22** (Día68 continuación): `--apply` real de `newest` con `pc_path=library_root`, `android_path=/storage/emulated/0/RetroArch`, 96/96 copiados, 0 errores. Verificado con mtimes tras la operación: `ps2/Mcd001.ps2` (carpeta reconocible en origen) bajó 1:1 sin pasar por `saves/`, confirmando el caso (1). Casos con carpeta intermedia `Unknown/` en origen (`sailormn_europe.nv`, `Kid Dracula (World)...sav`) se preservaron tal cual en destino (`Unknown/...`) — no es un fallo de nuestra canonicalización, es RetroArch en el propio dispositivo el que ya guarda esos saves bajo `Unknown/` (core sin mapear a contenido), confirmando el caso (2) también funciona en real |
| CABLE-SYNC-NEWEST-CANON-1 | Corregir la dirección `newest` en modo ADB, que comparaba `pc_index`/`ab_index` por ruta relativa cruda de ambos lados | `web/handlers/sync_cable.py` (bloque `elif direction == "newest":`) | ✅ hecho 2026-09-21 — reescrito para reusar el `ab_index`/`ab_by_name` ya construidos arriba (eliminada la reconstrucción redundante) con el mismo fallback por nombre de `CABLE-SYNC-SAVES-PREFIX-2`: solo hace match por nombre si hay un único candidato del lado Android (ambiguo con >1 candidato → se trata como archivo distinto, comportamiento anterior conservado como fallback seguro). Test nuevo `test_newest_direction_skips_file_under_different_device_prefix_same_mtime`. **Validado en real** con `pc_path=library_root`, `direction=newest`: 405/597 reconocidos como ya sincronizados; los 192 restantes son casos legítimos (BIOS/defaults solo en un lado, diferencias reales de mtime), sin ruido del problema de prefijos |
| CABLE-SYNC-NEWEST-CANON-2 | Mismo problema de fondo en las otras 2 reimplementaciones independientes de "newest": (a) `sync/cable_engine.py:plan_direction()` — compartido por el sync manual en modo filesystem/SD montada y el daemon SD-auto; (b) el fallback "RetroArch (legacy)" del daemon auto-sync ADB (activo cuando `get_adb_sync_sources()` no devuelve fuentes — usuarios sin `emulator_paths` configurado) | `sync/cable_engine.py` (`plan_direction`, rama `newest`), `web/cable_sync_daemon.py` (fallback "RetroArch (legacy)") | ✅ hecho 2026-09-21 — en vez de parchear cada reimplementación por separado, se extrajo la lógica de matching (ya escrita 3 veces con el mismo bug) a una función única y testeada: `reconcile_newest_by_name()` en `sync/android_paths.py` — empareja por clave exacta, con fallback por nombre solo si hay un único candidato del lado Android (ambiguo → sin emparejar, comportamiento seguro). Las 3 implementaciones (`sync_cable.py`, `cable_engine.py`, `cable_sync_daemon.py`) ahora son consumidores delgados de la misma función — evita que el mismo bug reaparezca una cuarta vez. 4 tests unitarios nuevos en `tests/test_android_paths.py` + 2 tests nuevos en `test_cable_engine.py`. Suite completa (1414 tests) sin regresiones (los 3 fallos que aparecen son ambientales — dispositivo ADB real conectado, no relacionados). **Revalidado en real tras el refactor**: mismo resultado exacto que antes (405/597 reconocidos, 192 candidatos legítimos, 0 errores) — el refactor no cambió comportamiento. El fallback per-emulador ADB del daemon (`adb_sources` con `local_saves`/`android_saves` dedicados) no tiene este problema — son carpetas 1:1 sin ambigüedad de plataforma, no se tocó |

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-SAVES-PREFIX-2 | Matching correcto ignorando el prefijo/carpeta intermedia del lado Android | `web/handlers/sync_cable.py` (`_skip_existing_device`, `_skip_existing_pc`) | ✅ hecho 2026-09-21 — implementada la opción de "matchear por nombre de archivo, ignorando segmentos intermedios", con tamaño como criterio de colisión (mismo patrón ya usado en todo el archivo para "ya existe"). Índice secundario `ab_by_name`/`_pc_by_name()` construido a partir de los índices existentes (`ab_index`, `_iter_files(pc_root)`) — sin mapeo core→plataforma, sin tocar `android_paths.py`. Tests nuevos en `tests/test_cable_sync_rom_skip_existing.py` (prefijo `saves/` en ambas direcciones). **Validado en real** contra la Anbernic con `pc_path=library_root` (el caso que antes fallaba, `CABLE-SYNC-DUP-PATHS-1`): antes 0/528 reconocidos, ahora **522/528 saltados como ya sincronizados, solo 6 genuinamente nuevos** (dry-run, `pc_to_anbernic`, `skip_existing=true`) |

---

### CABLE-SYNC-EMULATOR-SAVES-LEAK-1 — `emulator_saves/` (carpeta interna del PC) se filtra al dispositivo (rammu, 2026-09-21)

Investigando por qué `Pokemon - Edicion Plata SoulSilver (Spain).sav`
aparecía como conflicto en `CABLE-SYNC-LEGACY-DUPS-1` (una copia de 0
bytes con el mtime más reciente de las 3): **no es un conflicto real de
partidas**. El save de verdad está en `nds/Pokemon - Edicion Plata
SoulSilver (Spain).sav` (512KB, el que usa el core normal de RetroArch).
La copia sospechosa vive en
`/storage/emulated/0/RetroArch/emulator_saves/me.magnum.melonds/saves/...`
— y `emulator_saves/<package>/` es una carpeta que `get_adb_sync_sources()`
(`config.py`) usa **solo en el PC** para bajar saves por-emulador vía
ADB; nunca debería existir tal cual dentro del árbol `RetroArch/` del
dispositivo.

**Confirmado que no es un caso aislado**: hay **54 archivos** bajo
`/storage/emulated/0/RetroArch/emulator_saves/` en el dispositivo real
(toda la carpeta de estados de DuckStation incluida), todos con mtime a
pocos segundos entre sí — una única subida masiva, no uso real de la app.

**Causa raíz**: cuando `get_adb_sync_sources()` devuelve una lista vacía
(`adb_sources`), el daemon de auto-sync (`web/cable_sync_daemon.py`,
`_run_auto_sync`) cae al fallback `"RetroArch (legacy)"` con
`local_saves = config.library_root` (la biblioteca **entera**) contra
`android_saves = config.sync.auto_sync_android_path` — sin excluir
`emulator_saves/`, que es puramente contabilidad interna del propio
proyecto, no algo que ningún core de RetroArch en Android reconozca. El
mismo problema aplica al endpoint manual `/api/cable-sync`
(`web/handlers/sync_cable.py`) cuando `pc_path=library_root`: `_iter_files`
solo excluye dotfiles y `_descartados/`, no `emulator_saves/`. El archivo
de origen en el PC ya estaba a 0 bytes (melonDS nunca llegó a guardar esa
partida concreta — se jugó con otro core), así que la copia subida
también salió vacía; sin pérdida de progreso real, pero explica varios de
los 289 grupos de `CABLE-SYNC-LEGACY-DUPS-1` (al menos los 54 confirmados
+ los que generaron por round-trip de vuelta al PC, como el `saves/saves/`
doblemente anidado visto en `Castlevania - Dawn of Sorrow`).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-EMULATOR-SAVES-LEAK-1 | Excluir `emulator_saves/` del árbol que camina `pc_to_anbernic`/`newest` cuando `pc_path`/`local_saves` es la raíz de la biblioteca | `config.py` (`EMULATOR_SAVES_DIR_NAME`, nueva), `web/handlers/sync_cable.py` (`_iter_files`), `sync/cable_engine.py` (`iter_files`), `web/cable_sync_daemon.py` (walk de `_iter_local` en el fallback legacy) | ✅ hecho 2026-09-21 — mismo patrón que la exclusión ya existente de `_descartados/`/`TRASH_DIR_NAME`: nueva constante `EMULATOR_SAVES_DIR_NAME = "emulator_saves"` en `config.py` (reemplaza el literal ya usado en `get_adb_sync_sources()`), excluida en los 3 walks (`dirs[:] = [...]`) igual que `TRASH_DIR_NAME`. Aplica a ambos lados del walk (PC y Anbernic) — inocuo si el dispositivo está limpio, corta la fuga si no. 2 tests nuevos (`test_iter_files_skips_emulator_saves` en `test_cable_engine.py`, `test_pc_to_anbernic_never_uploads_emulator_saves_folder` en `test_cable_sync_rom_skip_existing.py`). Suite completa (1419 tests) sin regresiones nuevas. **No limpia los 54 archivos ya filtrados en el dispositivo real** — eso sigue en `CABLE-SYNC-LEGACY-DUPS-1` (ya respaldados en `.rommgr/legacy_dups_backup_2026-09-21/`), este fix solo corta la fuga hacia adelante |

---

### ANDROID-APP-PRIVATE-STORAGE-1 — DuckStation y AetherSX2 guardan en `Android/data/<paquete>/` (RG556): ni ADB ni rclone/Termux pueden leerlo ni escribirlo, sin root (hallazgo 2026-09-26, RG556 `RG556006101273`, ADB en vivo)

Origen: petición del usuario de traer a PC los saves de PS2 (AetherSX2) y
PSX (DuckStation) de la Anbernic, y de llevar de vuelta un savestate de
*Prince of Persia: Warrior Within* (`SLES-52822 (105CC366)`, confirmado por
el serial embebido en el ISO) más reciente en PC (PCSX2 standalone,
`.01.p2s` del 2025-07-20) que en Android (AetherSX2, mismo archivo del
2025-07-11).

**Causa raíz confirmada en ambas direcciones**: `xyz.aethersx2.android` y
`com.github.stenzek.duckstation` guardan memcards/savestates bajo
`/storage/emulated/0/Android/data/<paquete>/files/` — protegido por scoped
storage de Android (SELinux), no por permisos Unix (`ls -la` engaña: se ve
`drwxrwxrwx`, pero el contenido es ilegible/inescribible igualmente).
Confirmado con 4 pruebas en vivo, todas con el mismo resultado:
- `adb pull` de un archivo → `remote open failed: Permission denied`.
- `adb shell cp` (leer con el propio UID `shell`) → `Permission denied`
  igual, no es una limitación del protocolo sync de `adb pull` en concreto.
- `adb push` de un archivo de prueba → reporta "1 file pushed" pero
  **falla silenciosamente**: `remote fchown failed: Operation not
  permitted`, y el archivo no llega a existir en destino (verificado con
  `ls`/`cat` después — limpiado, no quedó rastro).
- `adb shell run-as <paquete> id` → `package not debuggable` en ambas apps
  (sin esto, ni siquiera vale para depurar, mucho menos para copiar).
- `adb backup -f ... <paquete>` → no falla al momento (a diferencia de una
  app con `allowBackup=false`), imprime "Now unlock your device and
  confirm..." y se queda esperando un diálogo en pantalla — probado 2 veces
  con la consola desbloqueada, el diálogo **nunca llegó a aparecer en
  pantalla** (posible fallo de la actividad de confirmación en esta ROM/
  versión de Android). Sin repro de éxito, descartado como vía fiable.
- Sin root: `su` no existe (`inaccessible or not found`).

Pista real para la vía de reconfiguración: existe
`/storage/emulated/0/duckstation/` (almacenamiento público, **fuera** de
`Android/data`) con solo `bios/`+`inputprofiles/` — carpeta obsoleta que
sugiere que DuckStation **ya estuvo alguna vez** configurado en modo
"carpeta de datos personalizada" (pública) y volvió al valor por defecto
(`Android/data`) tras una reinstalación/actualización. Si esa opción de
ajustes sigue existiendo en la app, es la vía de arreglo sin fork ni root.

Rechazado explícitamente por el usuario: copiar a mano con el explorador de
archivos del dispositivo cada vez — rompe el objetivo del proyecto (Pilar 3:
sync sin intervención manual). Un movimiento manual puntual para
*reconfigurar* la carpeta de datos (una vez) es aceptable; una rutina manual
recurrente por cada sync no lo es.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ANDROID-APP-PRIVATE-STORAGE-1a | Comprobar en los Ajustes de DuckStation y AetherSX2 (en la propia Anbernic) si existe una opción de "carpeta de datos"/modo portable que apunte a almacenamiento público en vez de `Android/data` — requiere tocar la consola, no verificable por ADB | UI de cada app en el dispositivo | ✅ resuelto 2026-09-26 por otra vía: en vez de reconfigurar DuckStation/AetherSX2 (ninguna de las dos ofrecía la opción), el usuario cambió de app — `com.nanodata.armsx` (ARMSX1, PS1) y `com.armsx2` (ARMSX2, PS2), mismos devs, con "Custom folder" (SAF) real. `config.py`/`test_config.py` actualizados (`EMULATOR_SAVE_PATHS_DEFAULT`), confirmado legible por ADB sin root |
| ANDROID-APP-PRIVATE-STORAGE-1b | Si 1a confirma la opción: migrar (copia única) los memcards/savestates actuales de `Android/data/<paquete>/files/` a la carpeta pública elegida antes de cambiar el ajuste, para no perder progreso | Manual, una vez | ✅ resuelto — no hizo falta migrar `Android/data/`, ARMSX1/ARMSX2 parten con su propia carpeta pública en `/storage/521D-04EA/saves/psx/` y `/storage/521D-04EA/saves/memcards/` |
| ANDROID-APP-PRIVATE-STORAGE-1c | Si 1a no ofrece esa opción para alguna de las dos apps: única alternativa real es rootear la RG556 (Magisk) — decisión del usuario, fuera de alcance de este proyecto | — | ✅ ya no aplica, ver 1a |
| ANDROID-APP-PRIVATE-STORAGE-1d | *Prince of Persia: Warrior Within* (`SLES-52822`) sigue con el savestate más nuevo solo en PC (`C:\Users\rammu\Documents\PCSX2\sstates\`) — llevarlo a la Anbernic depende de 1a/1b/1c. Aviso aparte: el tamaño difiere entre el `.p2s` de PC (16,3 MB) y el de Android (15,08 MB) para el mismo serial — posible divergencia de versión de motor entre PCSX2 desktop y AetherSX2 móvil, confirmar que carga antes de asumir compatibilidad total | — | 🟡 el aviso de este task era acertado — ver `ANDROID-APP-PRIVATE-STORAGE-1e` (Día70): un filtro verde persistente en este mismo juego en ARMSX2 sobrevivió a cambiar renderer/BIOS/resolución, lo que apunta a datos de GS corruptos (VRAM/paleta), no a un ajuste — coherente con una migración de savestate entre motores/versiones distintas |
| ANDROID-APP-PRIVATE-STORAGE-1e | **Nuevo (Día70, 2026-09-27)**: confirmar si el filtro verde en paredes de *Warrior Within* en ARMSX2 viene de un savestate/estado GS corrupto en vez de un ajuste gráfico. Se agotaron 6 hipótesis de configuración sin efecto (ver diario Día70) — probar arrancando el juego desde cero (Fast Boot, sin cargar ningún savestate ni resume-state) en una zona nueva no visitada; si sale limpio, el estado guardado es la causa y la única vía es recuperar progreso desde la memory card (no desde un savestate) o rehacer el tramo | Requiere consola física (RG556) | 🔴 pendiente — bloqueado por acceso al hardware, siguiente sesión |

---

### SYNC-WII-SCOPE-1 — `SyncSource` no puede acotar solo los saves reales de Dolphin (Wii) (hallazgo rammu, 2026-09-21)

Al reestructurar `sync.sources` en rammu siguiendo `Tareas/Estructura-Estandarizada-Sync.md`
(convenio `dropbox:/RetroSync/saves/<emulador>/<tipo>` de PC2, `dolphin/gc` +
`dolphin/wii`), la fuente `Dolphin (Wii)` con `local_dir` apuntando a la
carpeta `Wii/` completa (`sync_all=true`) empezó a subir el NAND emulado
entero (`title/<tipo>/<id>/content/` = IOS, System Menu, apps de canales
instalados — `.app`, certificados `.pem`, `fst.bin`), no solo los saves.
Medido en rammu: **96 MB en `Wii/` total, de los que solo 0.29 MB son saves
reales** (`title/*/*/data/`, el equivalente NAND del save real por juego —
`title/00010000/<gameid-hex>/data/`). `SyncSource` solo soporta un
`local_dir` plano (sin include/exclude), así que no hay forma de acotar hoy
a "todas las subcarpetas `data/` bajo `title/*/*`" sin sincronizar también
`content/` (las apps instaladas). Parado a mitad de sync real (`--apply`)
antes de subir más basura; fuente `Dolphin (Wii)` desactivada en
`config.toml` (comentada, con la medición) hasta que se diseñe bien.
**GC no tiene este problema** — su carpeta ya es 100% saves (`.gci` +
`.raw`), se dejó activa. **Limpieza pendiente**: revisar
`dropbox:/RetroSync/saves/dolphin/wii` — puede tener algunos `.app`/`.pem`
subidos antes de parar el proceso (no es sensible ni gran volumen, pero es
basura que no debería estar ahí).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| SYNC-WII-SCOPE-1 | Sincronizar solo `title/*/*/data/` de Dolphin (Wii) | `config.py` (`SyncSource.include_glob`), `sync/save_syncer.py` (`list_local_saves`, `sync_saves`), `cli.py` (x2), `web/handlers/sync_cloud.py` | ✅ hecho 2026-09-21 — opción (a): campo `include_glob: str = "**/*"` en `SyncSource` (compatible hacia atrás, resto de fuentes sin cambio de comportamiento), usado en `saves_dir.glob(include_glob)` en vez del `rglob("*")` fijo. `config.toml` reactivado con `include_glob = "title/*/*/data/**/*"`. Test `test_list_local_saves_include_glob_scopes_dolphin_wii_nand` en `tests/test_save_syncer.py`. Verificado en dry-run real contra el NAND de rammu: 10 archivos detectados (todos bajo `data/`), `content/`/`shared1/`/etc. excluidos — antes eran 96 MB, ahora ~0.29 MB reales. Pendiente aplicar en PC2 y reactivar allí también |
| SYNC-WII-SCOPE-2 | Limpiar `dropbox:/RetroSync/saves/dolphin/wii` de archivos de sistema subidos por error antes de detectar SYNC-WII-SCOPE-1 (`.app`, `.pem`, `fst.bin` — no saves) | — (limpieza manual en Dropbox o vía `rclone delete`) | ✅ hecho 2026-09-21 — `tools/rclone.exe purge` sobre la carpeta entera, confirmado vacía (53 archivos, 17.4 MB, 0 saves reales entre ellos) |

---

### CABLE-SYNC-DUP-PATHS-1 — investigación cable-sync ADB con la Anbernic real (rammu, 2026-09-21) — cerrada, no era un bug

Con la Anbernic conectada por USB (autorizada, `adb devices` → `device`), se
probó `POST /api/cable-sync` (`direction=pc_to_anbernic`, `use_adb=true`,
`dry_run=true`). Primer intento con `pc_path=E:\Carpetas anbernic` (raíz de
la biblioteca): **528/528 marcados para copiar, 0 ya coincidentes** —
sospecha inicial de bug real de matching, **descartada tras seguir la
cadena hasta la causa raíz** (regla "Investigar antes de arreglar",
CLAUDE.md):

1. **Error de test #1 — `pc_path` incorrecto**: se pasó la raíz de la
   biblioteca (`E:\Carpetas anbernic`) en vez de la carpeta de saves
   (`E:\Carpetas anbernic\saves`). En Android, RetroArch guarda los saves
   planos junto a la plataforma (`RetroArch/mame/fixeight.nv`), sin
   subcarpeta `saves/` — con `pc_path` mal puesto, TODAS las rutas
   relativas quedaban desalineadas por ese segmento de más. Repetido con
   `pc_path=.../saves`: bajó a 229/229 copiar, seguía en 0 skipped.
2. **Error de test #2 — falta `skip_existing: true`**: `_skip_existing_device()`
   (`web/handlers/sync_cable.py:729`) devuelve `False` sin comprobar nada
   si `skip_existing` no viene en el payload — **por defecto es `false`**,
   así que cualquier dry-run sin ese flag marca todo como "a copiar" aunque
   ya exista igual en el dispositivo. No es un bug, es un parámetro opt-in
   de la propia API (ver `openapi.json` — no aparece en el ejemplo de
   payload, por eso se me pasó la primera vez). Con
   `pc_path=.../saves` + `skip_existing=true`: **123 ya coinciden (mismo
   tamaño), 106 realmente faltan, 0 errores** — número coherente, cierra
   la investigación.

**Hallazgo secundario real, menor**: 8 nombres de save duplicados en 2-3
rutas distintas del dispositivo (19 de 288 archivos totales) — restos de un
`savefile_directory` mal configurado en el pasado en la Anbernic (mismo
patrón de drift que `retroarch_cfg_writer.py` en PC, ver commit `ac9e905`
de hoy), ejemplo verificado con `adb shell find ... -iname 'punisher.nv'`:
`RetroArch/saves/cps1/punisher.nv` (convenio nuevo) +
`RetroArch/cps1/punisher.nv` + `RetroArch/cps1/fbneo/punisher.nv`
(legado). Solo 19 archivos, no bloquea nada — separado en su propia tarea.

**No se ejecutó ningún `--apply` real** en esta sesión (quedó todo en
dry-run) — 106 archivos / ~230 MB reales pendientes de subir a la
Anbernic, listos para aplicar en la próxima sesión con los parámetros ya
correctos (`pc_path=.../saves`, `android_path=/storage/emulated/0/RetroArch`,
`skip_existing=true`).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
**Mapeo completo + backup hechos 2026-09-21** (rammu, con la Anbernic real
por ADB) — **no se borró nada del dispositivo**, decisión del usuario
("informe + backup, sin borrar todavía"). 823 archivos de save/state en el
dispositivo, **289 nombres duplicados en rutas legado (706 archivos
implicados)** — mucho mayor que la estimación original de 8. Clasificados
en `.rommgr/legacy_dups_report_2026-09-21.csv` (gitignored, local):

| Clasificación | Grupos | Criterio |
|---|---|---|
| `junk_zero_bytes` | 14 | Todas las copias son 0 bytes — basura, sin riesgo de pérdida |
| `safe_same_copy_event` | 145 | Mismo tamaño, mtimes a ≤60s entre sí — típico de una migración puntual (mismo patrón que `CABLE-SYNC-SAVES-PREFIX-1`: "Advance Wars 2 [E].sav", 2s de diferencia) |
| `review_time_gap` | 123 | Mismo tamaño pero mtimes separados >60s — mismo tamaño no garantiza mismo contenido, revisar caso a caso antes de decidir |
| `CONFLICT_diff_size` | 7 | Tamaño distinto entre copias — divergencia real de contenido, **nunca borrar automáticamente** |

**Por qué no se automatizó el borrado ni con criterio "más reciente":**
uno de los 7 grupos conflictivos (`Pokemon - Edicion Plata SoulSilver
(Spain).sav`) tiene 3 copias — dos idénticas de 512KB (`nds/` y
`saves/nds/`, duplicado real y seguro) y una tercera de **0 bytes** en
`emulator_saves/me.magnum.melonds/saves/` con el mtime más reciente
(2026-08-28). Un criterio ciego de "quedarse con la copia más nueva por
fecha" habría elegido el archivo vacío y descartado la partida real de
512KB — la razón por la que esta tarea sigue sin automatizar el borrado
(Pilar 3: "cualquier bug aquí es prioridad absoluta, pérdida de progreso").
Los otros 6 grupos conflictivos son el mismo patrón: saves antiguos del
core `VBA Next` (abandonado) junto a saves mucho más recientes del core
`gba` actual — casi seguro seguros de borrar, pero no decidido
automáticamente sin revisión humana.

**Backup completo**: los 706 archivos de los 289 grupos (TODAS las
copias, no solo las "candidatas a borrar") están en
`.rommgr/legacy_dups_backup_2026-09-21/` (gitignored, local, misma
estructura relativa que el dispositivo) — 706/706 ok, 0 errores.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-LEGACY-DUPS-1 | Limpiar en la Anbernic los saves duplicados en rutas legado — no bloquea el cable-sync normal (`CABLE-SYNC-SAVES-PREFIX-2` ya lo hace robusto a esto), solo deja basura residual | — (limpieza manual en el dispositivo, sin tocar código) | ✅ **completo 2026-09-21**. Primera pasada (bajo riesgo, tamaño/fecha): 159 grupos/240 archivos (`junk_zero_bytes` + `safe_same_copy_event`) borrados, backup previo intacto, 0 errores — ver detalle abajo. **Segunda pasada (los 130 grupos restantes, `review_time_gap` + `CONFLICT_diff_size`) resuelta por contenido real**: en vez de decidir por tamaño/fecha (arriesgado — el `size_bytes` de un save GBA de tamaño fijo no dice nada del contenido), se calculó el SHA1 real de cada copia contra el backup local ya hecho (sin tocar el dispositivo, que estaba ocupado con el rescan `ps2` de `ANDROID-DUP-2`). Resultado: de 321 archivos en esos 130 grupos, **174 eran copias byte-idénticas de verdad** (mismo contenido exacto, solo cambiaba la ruta/fecha) — borradas vía `adb shell rm`, 0 errores, verificado post-borrado que las 147 rutas canónicas conservadas (una por cada contenido realmente distinto) siguen intactas. **Ningún archivo de contenido único se tocó** — incluye casos con saves reales de un core distinto (p. ej. `Metroid - Zero Mission [E].srm` tiene un save propio bajo `saves/mGBA/` además del de `VBA Next`/`gba`), que quedan sin resolver a propósito, decisión del usuario si alguna vez hace falta. **Hallazgo colateral nuevo, sin implementar**: 2 grupos tenían copias bajo `saves/.stversions/<core>/` — carpeta de versionado de Syncthing (herramienta de terceros en el dispositivo, no creada por este proyecto), debería excluirse del escaneo/legacy-dup igual que `_descartados/`/`emulator_saves/`, no se ha tocado. Backup completo de las 3 pasadas sigue en `.rommgr/legacy_dups_backup_2026-09-21/` |
| CABLE-SYNC-APPLY-1 | Ejecutar el `--apply` real de `pc_to_anbernic` con los parámetros ya validados (`pc_path=E:\Carpetas anbernic\saves`, `android_path=/storage/emulated/0/RetroArch`, `skip_existing=true`, `safe_mode=true`) — 106 archivos / ~230 MB pendientes de subir | — | ✅ hecho 2026-09-21 — 106 subidos, 123 ya coincidían, 0 errores, 232 MB, coincide exacto con el dry-run |

---

### CABLE-SYNC-SAVES-PREFIX-1 — cable-sync ADB no reconoce el convenio D2 `saves/` del PC — afecta a la UI real, no solo al test de arriba (rammu, 2026-09-21)

Al ejecutar `CABLE-SYNC-APPLY-1` con `pc_path` apuntando **directamente** a
`E:\Carpetas anbernic\saves` (no a la raíz de la biblioteca) tuvo que
usarse a propósito para que el matching funcionara. Pero **la UI real
(`sync.js:940`, `_setIfEmpty('cable-pc-path', ... cfg.library_root ...)`)
por defecto pone `pc_path = library_root`** (la raíz completa, no
`.../saves`) — necesario porque el mismo campo también sirve para
sincronizar ROMs, no solo saves. Con ese valor por defecto, cualquier
usuario que haya centralizado sus saves con el convenio D2
(`savefile_directory = library_root/saves`, el mismo botón "Aplicar
layout de saves" arreglado hoy en `ac9e905`) sufriría el mismo problema
que el primer intento de `CABLE-SYNC-DUP-PATHS-1`: **todos los saves se
marcarían como "nuevos"** en vez de detectarse como ya sincronizados,
porque la ruta relativa del lado PC lleva el prefijo `saves/` y la del
lado Android no.

**Causa raíz confirmada en código**: `canonical_rel_posix()`
(`sync/android_paths.py`) traduce el primer segmento (carpeta de
plataforma) usando `PLATFORM_BY_FOLDER`/`_ES_PLATFORM_FOLDERS`, pero por
diseño explícito (su propio docstring) **no toca segmentos que no
reconoce como plataforma — y `saves` es uno de ellos**: `"no inventa una
carpeta nueva para algo que no reconoce (p. ej. carpetas de sistema como
BIOS/ o saves/)"`.

**No es un fix trivial de una línea** — verificado en el dispositivo real
(`adb shell find`/`ls_recursive` sin filtro) que **el propio Android
mezcla convenios según el core**: algunos escriben el save plano junto a
la plataforma (`RetroArch/mame/fixeight.nv`), otros ya usan su propia
subcarpeta `saves/<core>/` (`RetroArch/saves/mame2003/nvram/mk3.nv`,
`RetroArch/saves/bsnes2014/Earthbound (1).srm`) — quitar sin más el
prefijo `saves/` del lado PC rompería el matching para los cores que sí
lo tienen en Android. Necesita diseño, no un parche a ciegas, en el pilar
de mayor riesgo del proyecto ("cualquier bug aquí es prioridad absoluta",
CLAUDE.md).

**Mapeo real completado (rammu, 2026-09-21, `adb shell find`/`stat` sobre la
Anbernic conectada)** — el problema es mucho más grande que los "8
duplicados" estimados en `CABLE-SYNC-LEGACY-DUPS-1`: hay carpeta plana
(`RetroArch/<plataforma>/`) Y carpeta `saves/` para prácticamente todas las
plataformas probadas, con solapamiento de nombre de archivo casi total y
**ambas copias con actividad reciente** (no es basura histórica de una
migración puntual — algunos juegos escriben en un lado, otros en el otro,
en la misma sesión de uso):

| Plataforma | Archivos en plano | Archivos en `saves/` | Mismo nombre en ambos |
|---|---|---|---|
| mame | 25 | 24 | 24 |
| gba | 47 | 115 | 46 |
| psx | 7 | 9 | 6 |
| snes | 4 | 3 | 3 |
| nes | 2 | 3 | 1 |
| cps1 | 3 | 2 | 2 |
| cps2 | 2 | 1 | 1 |

Verificado con `stat` en `Advance Wars 2 [E].sav` (gba): mismo tamaño
(65536 B) en plano y en `saves/`, mtimes a 2 segundos de diferencia
(2025-03-09) — copia puntual antigua, no reescritura activa de ese archivo
concreto. Pero `ls -t` muestra archivos con mtime reciente en **ambas**
ubicaciones (`Pokémon Rojo fuego [E].sav` en plano, `Pokemon WaterBlue.srm`
y `Final Fantasy Tactics [E].srm` en `saves/gba`) — confirma que hoy en
día se sigue escribiendo en los dos sitios según qué core/config se use
por partida, no es solo arrastre histórico.

**El nombre de la subcarpeta bajo `saves/` no es consistente**: a veces es
el nombre canónico de plataforma ya reconocido por `PLATFORM_BY_FOLDER`
(`saves/gba`, `saves/psx`, `saves/snes`, `saves/mame`, y por coincidencia
`saves/cps1`/`saves/cps2`/`saves/fbneo`, que están en `platforms.toml`
como alias de "Arcade"), y a veces es el nombre del core de RetroArch tal
cual, que **no** está en `PLATFORM_BY_FOLDER` (`saves/mame2003`,
`saves/bsnes2014`, `saves/Snes9x`, `saves/Snes9x 2005 Plus`,
`saves/VBA Next`, `saves/FCEUmm`, `saves/mGBA`, `saves/PPSSPP`,
`saves/Citra`, `saves/LRPS2`, `saves/Beetle PSX`). No hay mapeo core→plataforma
completo hoy en el código — haría falta construirlo y mantenerlo para
poder confiar en el segundo segmento de la ruta.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-SAVES-PREFIX-1 | Mapear en el dispositivo real qué cores usan `saves/<core>/` vs plano junto a la plataforma | — (investigación en el dispositivo real, sin tocar código) | ✅ hecho 2026-09-21 — ver tabla y hallazgos arriba |

**Hallazgos relacionados, fuera de alcance de este fix** (revisado el código
alrededor de `_skip_existing_device`/`_skip_existing_pc` al implementar,
sin tocarlos — CLAUDE.md "Investigar antes de arreglar"):

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-DOWNLOAD-DEST-1 | Canonicalizar el destino de descarga (`anbernic_to_pc`/`newest`), que escribía en `pc_root / rel_posix` usando la ruta cruda del dispositivo sin canonicalizar | `sync/android_paths.py` (`canonical_download_rel_posix`, nueva), `web/handlers/sync_cable.py` (`_adb_copy_to_pc`, delete_extra ×2), `sync/cable_engine.py` (`plan_direction`, ramas `anbernic_to_pc`/`newest`), `web/cable_sync_daemon.py` (`_adb_copy_to_pc` legacy) | ✅ hecho 2026-09-21 — decisión de diseño confirmada con el usuario: (1) con carpeta intermedia reconocible (`saves/psx/foo.sav`, "psx" SÍ es plataforma conocida) → aterriza en la ruta canónica sin `saves/` (`psx/foo.sav`), igual criterio que ya usa la subida; (2) con carpeta intermedia ambigua (`saves/mame2003/...`, core sin mapear) → se mantiene la ruta cruda, no se arriesga a adivinar mal. Nueva función `canonical_download_rel_posix()` en `android_paths.py`, usada en los 3 sitios que escriben destino de descarga — incluye actualizar los 2 bloques `delete_extra`/espejo que comparaban por ruta cruda (si no, un archivo recién bajado a su ruta canónica se leía como "extra" y se borraba). 8 tests unitarios nuevos (4 en `test_android_paths.py`, 2 en `test_cable_engine.py`, más los de `canonical_download_rel_posix` en sí) cubriendo exactamente el caso `saves/gba/mario.sav → gba/mario.sav` y el caso ambiguo sin tocar. Suite completa (1417 tests) sin regresiones nuevas. **Validado en real 2026-09-22** (Día68 continuación): `--apply` real de `newest` con `pc_path=library_root`, `android_path=/storage/emulated/0/RetroArch`, 96/96 copiados, 0 errores. Verificado con mtimes tras la operación: `ps2/Mcd001.ps2` (carpeta reconocible en origen) bajó 1:1 sin pasar por `saves/`, confirmando el caso (1). Casos con carpeta intermedia `Unknown/` en origen (`sailormn_europe.nv`, `Kid Dracula (World)...sav`) se preservaron tal cual en destino (`Unknown/...`) — no es un fallo de nuestra canonicalización, es RetroArch en el propio dispositivo el que ya guarda esos saves bajo `Unknown/` (core sin mapear a contenido), confirmando el caso (2) también funciona en real |
| CABLE-SYNC-NEWEST-CANON-1 | Corregir la dirección `newest` en modo ADB, que comparaba `pc_index`/`ab_index` por ruta relativa cruda de ambos lados | `web/handlers/sync_cable.py` (bloque `elif direction == "newest":`) | ✅ hecho 2026-09-21 — reescrito para reusar el `ab_index`/`ab_by_name` ya construidos arriba (eliminada la reconstrucción redundante) con el mismo fallback por nombre de `CABLE-SYNC-SAVES-PREFIX-2`: solo hace match por nombre si hay un único candidato del lado Android (ambiguo con >1 candidato → se trata como archivo distinto, comportamiento anterior conservado como fallback seguro). Test nuevo `test_newest_direction_skips_file_under_different_device_prefix_same_mtime`. **Validado en real** con `pc_path=library_root`, `direction=newest`: 405/597 reconocidos como ya sincronizados; los 192 restantes son casos legítimos (BIOS/defaults solo en un lado, diferencias reales de mtime), sin ruido del problema de prefijos |
| CABLE-SYNC-NEWEST-CANON-2 | Mismo problema de fondo en las otras 2 reimplementaciones independientes de "newest": (a) `sync/cable_engine.py:plan_direction()` — compartido por el sync manual en modo filesystem/SD montada y el daemon SD-auto; (b) el fallback "RetroArch (legacy)" del daemon auto-sync ADB (activo cuando `get_adb_sync_sources()` no devuelve fuentes — usuarios sin `emulator_paths` configurado) | `sync/cable_engine.py` (`plan_direction`, rama `newest`), `web/cable_sync_daemon.py` (fallback "RetroArch (legacy)") | ✅ hecho 2026-09-21 — en vez de parchear cada reimplementación por separado, se extrajo la lógica de matching (ya escrita 3 veces con el mismo bug) a una función única y testeada: `reconcile_newest_by_name()` en `sync/android_paths.py` — empareja por clave exacta, con fallback por nombre solo si hay un único candidato del lado Android (ambiguo → sin emparejar, comportamiento seguro). Las 3 implementaciones (`sync_cable.py`, `cable_engine.py`, `cable_sync_daemon.py`) ahora son consumidores delgados de la misma función — evita que el mismo bug reaparezca una cuarta vez. 4 tests unitarios nuevos en `tests/test_android_paths.py` + 2 tests nuevos en `test_cable_engine.py`. Suite completa (1414 tests) sin regresiones (los 3 fallos que aparecen son ambientales — dispositivo ADB real conectado, no relacionados). **Revalidado en real tras el refactor**: mismo resultado exacto que antes (405/597 reconocidos, 192 candidatos legítimos, 0 errores) — el refactor no cambió comportamiento. El fallback per-emulador ADB del daemon (`adb_sources` con `local_saves`/`android_saves` dedicados) no tiene este problema — son carpetas 1:1 sin ambigüedad de plataforma, no se tocó |

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-SAVES-PREFIX-2 | Matching correcto ignorando el prefijo/carpeta intermedia del lado Android | `web/handlers/sync_cable.py` (`_skip_existing_device`, `_skip_existing_pc`) | ✅ hecho 2026-09-21 — implementada la opción de "matchear por nombre de archivo, ignorando segmentos intermedios", con tamaño como criterio de colisión (mismo patrón ya usado en todo el archivo para "ya existe"). Índice secundario `ab_by_name`/`_pc_by_name()` construido a partir de los índices existentes (`ab_index`, `_iter_files(pc_root)`) — sin mapeo core→plataforma, sin tocar `android_paths.py`. Tests nuevos en `tests/test_cable_sync_rom_skip_existing.py` (prefijo `saves/` en ambas direcciones). **Validado en real** contra la Anbernic con `pc_path=library_root` (el caso que antes fallaba, `CABLE-SYNC-DUP-PATHS-1`): antes 0/528 reconocidos, ahora **522/528 saltados como ya sincronizados, solo 6 genuinamente nuevos** (dry-run, `pc_to_anbernic`, `skip_existing=true`) |

---

### CABLE-SYNC-EMULATOR-SAVES-LEAK-1 — `emulator_saves/` (carpeta interna del PC) se filtra al dispositivo (rammu, 2026-09-21)

Investigando por qué `Pokemon - Edicion Plata SoulSilver (Spain).sav`
aparecía como conflicto en `CABLE-SYNC-LEGACY-DUPS-1` (una copia de 0
bytes con el mtime más reciente de las 3): **no es un conflicto real de
partidas**. El save de verdad está en `nds/Pokemon - Edicion Plata
SoulSilver (Spain).sav` (512KB, el que usa el core normal de RetroArch).
La copia sospechosa vive en
`/storage/emulated/0/RetroArch/emulator_saves/me.magnum.melonds/saves/...`
— y `emulator_saves/<package>/` es una carpeta que `get_adb_sync_sources()`
(`config.py`) usa **solo en el PC** para bajar saves por-emulador vía
ADB; nunca debería existir tal cual dentro del árbol `RetroArch/` del
dispositivo.

**Confirmado que no es un caso aislado**: hay **54 archivos** bajo
`/storage/emulated/0/RetroArch/emulator_saves/` en el dispositivo real
(toda la carpeta de estados de DuckStation incluida), todos con mtime a
pocos segundos entre sí — una única subida masiva, no uso real de la app.

**Causa raíz**: cuando `get_adb_sync_sources()` devuelve una lista vacía
(`adb_sources`), el daemon de auto-sync (`web/cable_sync_daemon.py`,
`_run_auto_sync`) cae al fallback `"RetroArch (legacy)"` con
`local_saves = config.library_root` (la biblioteca **entera**) contra
`android_saves = config.sync.auto_sync_android_path` — sin excluir
`emulator_saves/`, que es puramente contabilidad interna del propio
proyecto, no algo que ningún core de RetroArch en Android reconozca. El
mismo problema aplica al endpoint manual `/api/cable-sync`
(`web/handlers/sync_cable.py`) cuando `pc_path=library_root`: `_iter_files`
solo excluye dotfiles y `_descartados/`, no `emulator_saves/`. El archivo
de origen en el PC ya estaba a 0 bytes (melonDS nunca llegó a guardar esa
partida concreta — se jugó con otro core), así que la copia subida
también salió vacía; sin pérdida de progreso real, pero explica varios de
los 289 grupos de `CABLE-SYNC-LEGACY-DUPS-1` (al menos los 54 confirmados
+ los que generaron por round-trip de vuelta al PC, como el `saves/saves/`
doblemente anidado visto en `Castlevania - Dawn of Sorrow`).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-EMULATOR-SAVES-LEAK-1 | Excluir `emulator_saves/` del árbol que camina `pc_to_anbernic`/`newest` cuando `pc_path`/`local_saves` es la raíz de la biblioteca | `config.py` (`EMULATOR_SAVES_DIR_NAME`, nueva), `web/handlers/sync_cable.py` (`_iter_files`), `sync/cable_engine.py` (`iter_files`), `web/cable_sync_daemon.py` (walk de `_iter_local` en el fallback legacy) | ✅ hecho 2026-09-21 — mismo patrón que la exclusión ya existente de `_descartados/`/`TRASH_DIR_NAME`: nueva constante `EMULATOR_SAVES_DIR_NAME = "emulator_saves"` en `config.py` (reemplaza el literal ya usado en `get_adb_sync_sources()`), excluida en los 3 walks (`dirs[:] = [...]`) igual que `TRASH_DIR_NAME`. Aplica a ambos lados del walk (PC y Anbernic) — inocuo si el dispositivo está limpio, corta la fuga si no. 2 tests nuevos (`test_iter_files_skips_emulator_saves` en `test_cable_engine.py`, `test_pc_to_anbernic_never_uploads_emulator_saves_folder` en `test_cable_sync_rom_skip_existing.py`). Suite completa (1419 tests) sin regresiones nuevas. **No limpia los 54 archivos ya filtrados en el dispositivo real** — eso sigue en `CABLE-SYNC-LEGACY-DUPS-1` (ya respaldados en `.rommgr/legacy_dups_backup_2026-09-21/`), este fix solo corta la fuga hacia adelante |

---

### SAVES-UX — Historial de saves y contexto en resolución de conflictos (idea usuario 2026-09-22)

Reducir el "miedo a sobrescribir" del pilar 3 más allá del backup-antes-de-
sobrescribir ya existente: dejar ver y restaurar versiones anteriores, y dar
más contexto que solo el timestamp al resolver un conflicto.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| SAVES-HISTORY-1 | **Replanteada tras investigar (2026-09-22)**: el historial+restauración ya existía y funcionaba (`rom_manager/backup/save_backup.py`, `GET /api/save-backups`, `POST /api/restore-backup`, UI en la ficha de juego `games.js:877-885,1090-1113`) para Cloud Sync, Cable Sync manual y renombrado. El gap real era el daemon SD auto-sync (`CABLE-UX-9a`), que usaba un segundo sistema aislado (`.rommgr/cable_sync_backups/<fecha>/`) invisible en esa UI | `web/cable_sync_daemon.py` (`_run_sd_auto_sync`), `rom_manager/backup/save_backup.py` | ✅ hecho 2026-09-22 (rama `feature/saves-ux-history-context`): daemon migrado a `backup_save()`, mismo patrón que `sync_cable.py`. Verificado contra el sistema de archivos real: `.rommgr/cable_sync_backups/` no existía (el daemon nunca disparó esa rama en la práctica) — nada que migrar. 1430 tests pass (3 ambientales), ruff+format limpios |
| SAVES-CONFLICT-CTX-1 | Al resolver un conflicto de sync, mostrar contexto además del timestamp (playtime asociado, tamaño). Solo Cloud Sync (Cable Sync no detecta conflictos hoy) | `sync/conflict_resolver.py`, `sync/save_syncer.py`, `web/handlers/sync_cloud.py`, `web/static/js/tabs/sync.js` | ✅ hecho 2026-09-22 (rama `feature/saves-ux-history-context`): `SyncDecision` con tamaños, `_decision_payload()` añade mtime/tamaño/playtime best-effort (match por stem contra `games`) solo para conflictos, UI pinta la línea de contexto bajo cada fila. 4 tests nuevos, 1434 pass, ruff+format limpios |
| SYNC-CONFLICT-MANUAL-1 | Revisión manual de conflictos de Cloud Sync desde la UI antes de sincronizar — por archivo, elegir PC/Consola/omitir en vez de que `conflict_policy` global decida siempre por todos. No aplica a Cable Sync (sin detección de conflictos hoy) | `sync/save_syncer.py`, `web/handlers/sync_cloud.py`, `web/static/js/tabs/sync.js` | ✅ hecho 2026-09-22 (rama `feature/saves-ux-history-context`): `sync_saves()` acepta `conflict_overrides` (gana sobre `conflict_policy` por archivo, `skip` no toca nada); selector por fila en el plan de dry-run, recogido al pulsar Sincronizar. 3 tests nuevos, 1437 pass, ruff+format limpios |

---

### SYNC-WII-SCOPE-1 — `SyncSource` no puede acotar solo los saves reales de Dolphin (Wii) (hallazgo rammu, 2026-09-21)

Al reestructurar `sync.sources` en rammu siguiendo `Tareas/Estructura-Estandarizada-Sync.md`
(convenio `dropbox:/RetroSync/saves/<emulador>/<tipo>` de PC2, `dolphin/gc` +
`dolphin/wii`), la fuente `Dolphin (Wii)` con `local_dir` apuntando a la
carpeta `Wii/` completa (`sync_all=true`) empezó a subir el NAND emulado
entero (`title/<tipo>/<id>/content/` = IOS, System Menu, apps de canales
instalados — `.app`, certificados `.pem`, `fst.bin`), no solo los saves.
Medido en rammu: **96 MB en `Wii/` total, de los que solo 0.29 MB son saves
reales** (`title/*/*/data/`, el equivalente NAND del save real por juego —
`title/00010000/<gameid-hex>/data/`). `SyncSource` solo soporta un
`local_dir` plano (sin include/exclude), así que no hay forma de acotar hoy
a "todas las subcarpetas `data/` bajo `title/*/*`" sin sincronizar también
`content/` (las apps instaladas). Parado a mitad de sync real (`--apply`)
antes de subir más basura; fuente `Dolphin (Wii)` desactivada en
`config.toml` (comentada, con la medición) hasta que se diseñe bien.
**GC no tiene este problema** — su carpeta ya es 100% saves (`.gci` +
`.raw`), se dejó activa. **Limpieza pendiente**: revisar
`dropbox:/RetroSync/saves/dolphin/wii` — puede tener algunos `.app`/`.pem`
subidos antes de parar el proceso (no es sensible ni gran volumen, pero es
basura que no debería estar ahí).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| SYNC-WII-SCOPE-1 | Sincronizar solo `title/*/*/data/` de Dolphin (Wii) | `config.py` (`SyncSource.include_glob`), `sync/save_syncer.py` (`list_local_saves`, `sync_saves`), `cli.py` (x2), `web/handlers/sync_cloud.py` | ✅ hecho 2026-09-21 — opción (a): campo `include_glob: str = "**/*"` en `SyncSource` (compatible hacia atrás, resto de fuentes sin cambio de comportamiento), usado en `saves_dir.glob(include_glob)` en vez del `rglob("*")` fijo. `config.toml` reactivado con `include_glob = "title/*/*/data/**/*"`. Test `test_list_local_saves_include_glob_scopes_dolphin_wii_nand` en `tests/test_save_syncer.py`. Verificado en dry-run real contra el NAND de rammu: 10 archivos detectados (todos bajo `data/`), `content/`/`shared1/`/etc. excluidos — antes eran 96 MB, ahora ~0.29 MB reales. Pendiente aplicar en PC2 y reactivar allí también |
| SYNC-WII-SCOPE-2 | Limpiar `dropbox:/RetroSync/saves/dolphin/wii` de archivos de sistema subidos por error antes de detectar SYNC-WII-SCOPE-1 (`.app`, `.pem`, `fst.bin` — no saves) | — (limpieza manual en Dropbox o vía `rclone delete`) | ✅ hecho 2026-09-21 — `tools/rclone.exe purge` sobre la carpeta entera, confirmado vacía (53 archivos, 17.4 MB, 0 saves reales entre ellos) |

---

### CABLE-SYNC-DUP-PATHS-1 — investigación cable-sync ADB con la Anbernic real (rammu, 2026-09-21) — cerrada, no era un bug

Con la Anbernic conectada por USB (autorizada, `adb devices` → `device`), se
probó `POST /api/cable-sync` (`direction=pc_to_anbernic`, `use_adb=true`,
`dry_run=true`). Primer intento con `pc_path=E:\Carpetas anbernic` (raíz de
la biblioteca): **528/528 marcados para copiar, 0 ya coincidentes** —
sospecha inicial de bug real de matching, **descartada tras seguir la
cadena hasta la causa raíz** (regla "Investigar antes de arreglar",
CLAUDE.md):

1. **Error de test #1 — `pc_path` incorrecto**: se pasó la raíz de la
   biblioteca (`E:\Carpetas anbernic`) en vez de la carpeta de saves
   (`E:\Carpetas anbernic\saves`). En Android, RetroArch guarda los saves
   planos junto a la plataforma (`RetroArch/mame/fixeight.nv`), sin
   subcarpeta `saves/` — con `pc_path` mal puesto, TODAS las rutas
   relativas quedaban desalineadas por ese segmento de más. Repetido con
   `pc_path=.../saves`: bajó a 229/229 copiar, seguía en 0 skipped.
2. **Error de test #2 — falta `skip_existing: true`**: `_skip_existing_device()`
   (`web/handlers/sync_cable.py:729`) devuelve `False` sin comprobar nada
   si `skip_existing` no viene en el payload — **por defecto es `false`**,
   así que cualquier dry-run sin ese flag marca todo como "a copiar" aunque
   ya exista igual en el dispositivo. No es un bug, es un parámetro opt-in
   de la propia API (ver `openapi.json` — no aparece en el ejemplo de
   payload, por eso se me pasó la primera vez). Con
   `pc_path=.../saves` + `skip_existing=true`: **123 ya coinciden (mismo
   tamaño), 106 realmente faltan, 0 errores** — número coherente, cierra
   la investigación.

**Hallazgo secundario real, menor**: 8 nombres de save duplicados en 2-3
rutas distintas del dispositivo (19 de 288 archivos totales) — restos de un
`savefile_directory` mal configurado en el pasado en la Anbernic (mismo
patrón de drift que `retroarch_cfg_writer.py` en PC, ver commit `ac9e905`
de hoy), ejemplo verificado con `adb shell find ... -iname 'punisher.nv'`:
`RetroArch/saves/cps1/punisher.nv` (convenio nuevo) +
`RetroArch/cps1/punisher.nv` + `RetroArch/cps1/fbneo/punisher.nv`
(legado). Solo 19 archivos, no bloquea nada — separado en su propia tarea.

**No se ejecutó ningún `--apply` real** en esta sesión (quedó todo en
dry-run) — 106 archivos / ~230 MB reales pendientes de subir a la
Anbernic, listos para aplicar en la próxima sesión con los parámetros ya
correctos (`pc_path=.../saves`, `android_path=/storage/emulated/0/RetroArch`,
`skip_existing=true`).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
**Mapeo completo + backup hechos 2026-09-21** (rammu, con la Anbernic real
por ADB) — **no se borró nada del dispositivo**, decisión del usuario
("informe + backup, sin borrar todavía"). 823 archivos de save/state en el
dispositivo, **289 nombres duplicados en rutas legado (706 archivos
implicados)** — mucho mayor que la estimación original de 8. Clasificados
en `.rommgr/legacy_dups_report_2026-09-21.csv` (gitignored, local):

| Clasificación | Grupos | Criterio |
|---|---|---|
| `junk_zero_bytes` | 14 | Todas las copias son 0 bytes — basura, sin riesgo de pérdida |
| `safe_same_copy_event` | 145 | Mismo tamaño, mtimes a ≤60s entre sí — típico de una migración puntual (mismo patrón que `CABLE-SYNC-SAVES-PREFIX-1`: "Advance Wars 2 [E].sav", 2s de diferencia) |
| `review_time_gap` | 123 | Mismo tamaño pero mtimes separados >60s — mismo tamaño no garantiza mismo contenido, revisar caso a caso antes de decidir |
| `CONFLICT_diff_size` | 7 | Tamaño distinto entre copias — divergencia real de contenido, **nunca borrar automáticamente** |

**Por qué no se automatizó el borrado ni con criterio "más reciente":**
uno de los 7 grupos conflictivos (`Pokemon - Edicion Plata SoulSilver
(Spain).sav`) tiene 3 copias — dos idénticas de 512KB (`nds/` y
`saves/nds/`, duplicado real y seguro) y una tercera de **0 bytes** en
`emulator_saves/me.magnum.melonds/saves/` con el mtime más reciente
(2026-08-28). Un criterio ciego de "quedarse con la copia más nueva por
fecha" habría elegido el archivo vacío y descartado la partida real de
512KB — la razón por la que esta tarea sigue sin automatizar el borrado
(Pilar 3: "cualquier bug aquí es prioridad absoluta, pérdida de progreso").
Los otros 6 grupos conflictivos son el mismo patrón: saves antiguos del
core `VBA Next` (abandonado) junto a saves mucho más recientes del core
`gba` actual — casi seguro seguros de borrar, pero no decidido
automáticamente sin revisión humana.

**Backup completo**: los 706 archivos de los 289 grupos (TODAS las
copias, no solo las "candidatas a borrar") están en
`.rommgr/legacy_dups_backup_2026-09-21/` (gitignored, local, misma
estructura relativa que el dispositivo) — 706/706 ok, 0 errores.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-LEGACY-DUPS-1 | Limpiar en la Anbernic los saves duplicados en rutas legado — no bloquea el cable-sync normal (`CABLE-SYNC-SAVES-PREFIX-2` ya lo hace robusto a esto), solo deja basura residual | — (limpieza manual en el dispositivo, sin tocar código) | ✅ **completo 2026-09-21**. Primera pasada (bajo riesgo, tamaño/fecha): 159 grupos/240 archivos (`junk_zero_bytes` + `safe_same_copy_event`) borrados, backup previo intacto, 0 errores — ver detalle abajo. **Segunda pasada (los 130 grupos restantes, `review_time_gap` + `CONFLICT_diff_size`) resuelta por contenido real**: en vez de decidir por tamaño/fecha (arriesgado — el `size_bytes` de un save GBA de tamaño fijo no dice nada del contenido), se calculó el SHA1 real de cada copia contra el backup local ya hecho (sin tocar el dispositivo, que estaba ocupado con el rescan `ps2` de `ANDROID-DUP-2`). Resultado: de 321 archivos en esos 130 grupos, **174 eran copias byte-idénticas de verdad** (mismo contenido exacto, solo cambiaba la ruta/fecha) — borradas vía `adb shell rm`, 0 errores, verificado post-borrado que las 147 rutas canónicas conservadas (una por cada contenido realmente distinto) siguen intactas. **Ningún archivo de contenido único se tocó** — incluye casos con saves reales de un core distinto (p. ej. `Metroid - Zero Mission [E].srm` tiene un save propio bajo `saves/mGBA/` además del de `VBA Next`/`gba`), que quedan sin resolver a propósito, decisión del usuario si alguna vez hace falta. **Hallazgo colateral nuevo, sin implementar**: 2 grupos tenían copias bajo `saves/.stversions/<core>/` — carpeta de versionado de Syncthing (herramienta de terceros en el dispositivo, no creada por este proyecto), debería excluirse del escaneo/legacy-dup igual que `_descartados/`/`emulator_saves/`, no se ha tocado. Backup completo de las 3 pasadas sigue en `.rommgr/legacy_dups_backup_2026-09-21/` |
| CABLE-SYNC-APPLY-1 | Ejecutar el `--apply` real de `pc_to_anbernic` con los parámetros ya validados (`pc_path=E:\Carpetas anbernic\saves`, `android_path=/storage/emulated/0/RetroArch`, `skip_existing=true`, `safe_mode=true`) — 106 archivos / ~230 MB pendientes de subir | — | ✅ hecho 2026-09-21 — 106 subidos, 123 ya coincidían, 0 errores, 232 MB, coincide exacto con el dry-run |

---

### CABLE-SYNC-SAVES-PREFIX-1 — cable-sync ADB no reconoce el convenio D2 `saves/` del PC — afecta a la UI real, no solo al test de arriba (rammu, 2026-09-21)

Al ejecutar `CABLE-SYNC-APPLY-1` con `pc_path` apuntando **directamente** a
`E:\Carpetas anbernic\saves` (no a la raíz de la biblioteca) tuvo que
usarse a propósito para que el matching funcionara. Pero **la UI real
(`sync.js:940`, `_setIfEmpty('cable-pc-path', ... cfg.library_root ...)`)
por defecto pone `pc_path = library_root`** (la raíz completa, no
`.../saves`) — necesario porque el mismo campo también sirve para
sincronizar ROMs, no solo saves. Con ese valor por defecto, cualquier
usuario que haya centralizado sus saves con el convenio D2
(`savefile_directory = library_root/saves`, el mismo botón "Aplicar
layout de saves" arreglado hoy en `ac9e905`) sufriría el mismo problema
que el primer intento de `CABLE-SYNC-DUP-PATHS-1`: **todos los saves se
marcarían como "nuevos"** en vez de detectarse como ya sincronizados,
porque la ruta relativa del lado PC lleva el prefijo `saves/` y la del
lado Android no.

**Causa raíz confirmada en código**: `canonical_rel_posix()`
(`sync/android_paths.py`) traduce el primer segmento (carpeta de
plataforma) usando `PLATFORM_BY_FOLDER`/`_ES_PLATFORM_FOLDERS`, pero por
diseño explícito (su propio docstring) **no toca segmentos que no
reconoce como plataforma — y `saves` es uno de ellos**: `"no inventa una
carpeta nueva para algo que no reconoce (p. ej. carpetas de sistema como
BIOS/ o saves/)"`.

**No es un fix trivial de una línea** — verificado en el dispositivo real
(`adb shell find`/`ls_recursive` sin filtro) que **el propio Android
mezcla convenios según el core**: algunos escriben el save plano junto a
la plataforma (`RetroArch/mame/fixeight.nv`), otros ya usan su propia
subcarpeta `saves/<core>/` (`RetroArch/saves/mame2003/nvram/mk3.nv`,
`RetroArch/saves/bsnes2014/Earthbound (1).srm`) — quitar sin más el
prefijo `saves/` del lado PC rompería el matching para los cores que sí
lo tienen en Android. Necesita diseño, no un parche a ciegas, en el pilar
de mayor riesgo del proyecto ("cualquier bug aquí es prioridad absoluta",
CLAUDE.md).

**Mapeo real completado (rammu, 2026-09-21, `adb shell find`/`stat` sobre la
Anbernic conectada)** — el problema es mucho más grande que los "8
duplicados" estimados en `CABLE-SYNC-LEGACY-DUPS-1`: hay carpeta plana
(`RetroArch/<plataforma>/`) Y carpeta `saves/` para prácticamente todas las
plataformas probadas, con solapamiento de nombre de archivo casi total y
**ambas copias con actividad reciente** (no es basura histórica de una
migración puntual — algunos juegos escriben en un lado, otros en el otro,
en la misma sesión de uso):

| Plataforma | Archivos en plano | Archivos en `saves/` | Mismo nombre en ambos |
|---|---|---|---|
| mame | 25 | 24 | 24 |
| gba | 47 | 115 | 46 |
| psx | 7 | 9 | 6 |
| snes | 4 | 3 | 3 |
| nes | 2 | 3 | 1 |
| cps1 | 3 | 2 | 2 |
| cps2 | 2 | 1 | 1 |

Verificado con `stat` en `Advance Wars 2 [E].sav` (gba): mismo tamaño
(65536 B) en plano y en `saves/`, mtimes a 2 segundos de diferencia
(2025-03-09) — copia puntual antigua, no reescritura activa de ese archivo
concreto. Pero `ls -t` muestra archivos con mtime reciente en **ambas**
ubicaciones (`Pokémon Rojo fuego [E].sav` en plano, `Pokemon WaterBlue.srm`
y `Final Fantasy Tactics [E].srm` en `saves/gba`) — confirma que hoy en
día se sigue escribiendo en los dos sitios según qué core/config se use
por partida, no es solo arrastre histórico.

**El nombre de la subcarpeta bajo `saves/` no es consistente**: a veces es
el nombre canónico de plataforma ya reconocido por `PLATFORM_BY_FOLDER`
(`saves/gba`, `saves/psx`, `saves/snes`, `saves/mame`, y por coincidencia
`saves/cps1`/`saves/cps2`/`saves/fbneo`, que están en `platforms.toml`
como alias de "Arcade"), y a veces es el nombre del core de RetroArch tal
cual, que **no** está en `PLATFORM_BY_FOLDER` (`saves/mame2003`,
`saves/bsnes2014`, `saves/Snes9x`, `saves/Snes9x 2005 Plus`,
`saves/VBA Next`, `saves/FCEUmm`, `saves/mGBA`, `saves/PPSSPP`,
`saves/Citra`, `saves/LRPS2`, `saves/Beetle PSX`). No hay mapeo core→plataforma
completo hoy en el código — haría falta construirlo y mantenerlo para
poder confiar en el segundo segmento de la ruta.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-SAVES-PREFIX-1 | Mapear en el dispositivo real qué cores usan `saves/<core>/` vs plano junto a la plataforma | — (investigación en el dispositivo real, sin tocar código) | ✅ hecho 2026-09-21 — ver tabla y hallazgos arriba |

**Hallazgos relacionados, fuera de alcance de este fix** (revisado el código
alrededor de `_skip_existing_device`/`_skip_existing_pc` al implementar,
sin tocarlos — CLAUDE.md "Investigar antes de arreglar"):

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-DOWNLOAD-DEST-1 | Canonicalizar el destino de descarga (`anbernic_to_pc`/`newest`), que escribía en `pc_root / rel_posix` usando la ruta cruda del dispositivo sin canonicalizar | `sync/android_paths.py` (`canonical_download_rel_posix`, nueva), `web/handlers/sync_cable.py` (`_adb_copy_to_pc`, delete_extra ×2), `sync/cable_engine.py` (`plan_direction`, ramas `anbernic_to_pc`/`newest`), `web/cable_sync_daemon.py` (`_adb_copy_to_pc` legacy) | ✅ hecho 2026-09-21 — decisión de diseño confirmada con el usuario: (1) con carpeta intermedia reconocible (`saves/psx/foo.sav`, "psx" SÍ es plataforma conocida) → aterriza en la ruta canónica sin `saves/` (`psx/foo.sav`), igual criterio que ya usa la subida; (2) con carpeta intermedia ambigua (`saves/mame2003/...`, core sin mapear) → se mantiene la ruta cruda, no se arriesga a adivinar mal. Nueva función `canonical_download_rel_posix()` en `android_paths.py`, usada en los 3 sitios que escriben destino de descarga — incluye actualizar los 2 bloques `delete_extra`/espejo que comparaban por ruta cruda (si no, un archivo recién bajado a su ruta canónica se leía como "extra" y se borraba). 8 tests unitarios nuevos (4 en `test_android_paths.py`, 2 en `test_cable_engine.py`, más los de `canonical_download_rel_posix` en sí) cubriendo exactamente el caso `saves/gba/mario.sav → gba/mario.sav` y el caso ambiguo sin tocar. Suite completa (1417 tests) sin regresiones nuevas. **Validado en real 2026-09-22** (Día68 continuación): `--apply` real de `newest` con `pc_path=library_root`, `android_path=/storage/emulated/0/RetroArch`, 96/96 copiados, 0 errores. Verificado con mtimes tras la operación: `ps2/Mcd001.ps2` (carpeta reconocible en origen) bajó 1:1 sin pasar por `saves/`, confirmando el caso (1). Casos con carpeta intermedia `Unknown/` en origen (`sailormn_europe.nv`, `Kid Dracula (World)...sav`) se preservaron tal cual en destino (`Unknown/...`) — no es un fallo de nuestra canonicalización, es RetroArch en el propio dispositivo el que ya guarda esos saves bajo `Unknown/` (core sin mapear a contenido), confirmando el caso (2) también funciona en real |
| CABLE-SYNC-NEWEST-CANON-1 | Corregir la dirección `newest` en modo ADB, que comparaba `pc_index`/`ab_index` por ruta relativa cruda de ambos lados | `web/handlers/sync_cable.py` (bloque `elif direction == "newest":`) | ✅ hecho 2026-09-21 — reescrito para reusar el `ab_index`/`ab_by_name` ya construidos arriba (eliminada la reconstrucción redundante) con el mismo fallback por nombre de `CABLE-SYNC-SAVES-PREFIX-2`: solo hace match por nombre si hay un único candidato del lado Android (ambiguo con >1 candidato → se trata como archivo distinto, comportamiento anterior conservado como fallback seguro). Test nuevo `test_newest_direction_skips_file_under_different_device_prefix_same_mtime`. **Validado en real** con `pc_path=library_root`, `direction=newest`: 405/597 reconocidos como ya sincronizados; los 192 restantes son casos legítimos (BIOS/defaults solo en un lado, diferencias reales de mtime), sin ruido del problema de prefijos |
| CABLE-SYNC-NEWEST-CANON-2 | Mismo problema de fondo en las otras 2 reimplementaciones independientes de "newest": (a) `sync/cable_engine.py:plan_direction()` — compartido por el sync manual en modo filesystem/SD montada y el daemon SD-auto; (b) el fallback "RetroArch (legacy)" del daemon auto-sync ADB (activo cuando `get_adb_sync_sources()` no devuelve fuentes — usuarios sin `emulator_paths` configurado) | `sync/cable_engine.py` (`plan_direction`, rama `newest`), `web/cable_sync_daemon.py` (fallback "RetroArch (legacy)") | ✅ hecho 2026-09-21 — en vez de parchear cada reimplementación por separado, se extrajo la lógica de matching (ya escrita 3 veces con el mismo bug) a una función única y testeada: `reconcile_newest_by_name()` en `sync/android_paths.py` — empareja por clave exacta, con fallback por nombre solo si hay un único candidato del lado Android (ambiguo → sin emparejar, comportamiento seguro). Las 3 implementaciones (`sync_cable.py`, `cable_engine.py`, `cable_sync_daemon.py`) ahora son consumidores delgados de la misma función — evita que el mismo bug reaparezca una cuarta vez. 4 tests unitarios nuevos en `tests/test_android_paths.py` + 2 tests nuevos en `test_cable_engine.py`. Suite completa (1414 tests) sin regresiones (los 3 fallos que aparecen son ambientales — dispositivo ADB real conectado, no relacionados). **Revalidado en real tras el refactor**: mismo resultado exacto que antes (405/597 reconocidos, 192 candidatos legítimos, 0 errores) — el refactor no cambió comportamiento. El fallback per-emulador ADB del daemon (`adb_sources` con `local_saves`/`android_saves` dedicados) no tiene este problema — son carpetas 1:1 sin ambigüedad de plataforma, no se tocó |

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-SAVES-PREFIX-2 | Matching correcto ignorando el prefijo/carpeta intermedia del lado Android | `web/handlers/sync_cable.py` (`_skip_existing_device`, `_skip_existing_pc`) | ✅ hecho 2026-09-21 — implementada la opción de "matchear por nombre de archivo, ignorando segmentos intermedios", con tamaño como criterio de colisión (mismo patrón ya usado en todo el archivo para "ya existe"). Índice secundario `ab_by_name`/`_pc_by_name()` construido a partir de los índices existentes (`ab_index`, `_iter_files(pc_root)`) — sin mapeo core→plataforma, sin tocar `android_paths.py`. Tests nuevos en `tests/test_cable_sync_rom_skip_existing.py` (prefijo `saves/` en ambas direcciones). **Validado en real** contra la Anbernic con `pc_path=library_root` (el caso que antes fallaba, `CABLE-SYNC-DUP-PATHS-1`): antes 0/528 reconocidos, ahora **522/528 saltados como ya sincronizados, solo 6 genuinamente nuevos** (dry-run, `pc_to_anbernic`, `skip_existing=true`) |

---

### CABLE-SYNC-EMULATOR-SAVES-LEAK-1 — `emulator_saves/` (carpeta interna del PC) se filtra al dispositivo (rammu, 2026-09-21)

Investigando por qué `Pokemon - Edicion Plata SoulSilver (Spain).sav`
aparecía como conflicto en `CABLE-SYNC-LEGACY-DUPS-1` (una copia de 0
bytes con el mtime más reciente de las 3): **no es un conflicto real de
partidas**. El save de verdad está en `nds/Pokemon - Edicion Plata
SoulSilver (Spain).sav` (512KB, el que usa el core normal de RetroArch).
La copia sospechosa vive en
`/storage/emulated/0/RetroArch/emulator_saves/me.magnum.melonds/saves/...`
— y `emulator_saves/<package>/` es una carpeta que `get_adb_sync_sources()`
(`config.py`) usa **solo en el PC** para bajar saves por-emulador vía
ADB; nunca debería existir tal cual dentro del árbol `RetroArch/` del
dispositivo.

**Confirmado que no es un caso aislado**: hay **54 archivos** bajo
`/storage/emulated/0/RetroArch/emulator_saves/` en el dispositivo real
(toda la carpeta de estados de DuckStation incluida), todos con mtime a
pocos segundos entre sí — una única subida masiva, no uso real de la app.

**Causa raíz**: cuando `get_adb_sync_sources()` devuelve una lista vacía
(`adb_sources`), el daemon de auto-sync (`web/cable_sync_daemon.py`,
`_run_auto_sync`) cae al fallback `"RetroArch (legacy)"` con
`local_saves = config.library_root` (la biblioteca **entera**) contra
`android_saves = config.sync.auto_sync_android_path` — sin excluir
`emulator_saves/`, que es puramente contabilidad interna del propio
proyecto, no algo que ningún core de RetroArch en Android reconozca. El
mismo problema aplica al endpoint manual `/api/cable-sync`
(`web/handlers/sync_cable.py`) cuando `pc_path=library_root`: `_iter_files`
solo excluye dotfiles y `_descartados/`, no `emulator_saves/`. El archivo
de origen en el PC ya estaba a 0 bytes (melonDS nunca llegó a guardar esa
partida concreta — se jugó con otro core), así que la copia subida
también salió vacía; sin pérdida de progreso real, pero explica varios de
los 289 grupos de `CABLE-SYNC-LEGACY-DUPS-1` (al menos los 54 confirmados
+ los que generaron por round-trip de vuelta al PC, como el `saves/saves/`
doblemente anidado visto en `Castlevania - Dawn of Sorrow`).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-EMULATOR-SAVES-LEAK-1 | Excluir `emulator_saves/` del árbol que camina `pc_to_anbernic`/`newest` cuando `pc_path`/`local_saves` es la raíz de la biblioteca | `config.py` (`EMULATOR_SAVES_DIR_NAME`, nueva), `web/handlers/sync_cable.py` (`_iter_files`), `sync/cable_engine.py` (`iter_files`), `web/cable_sync_daemon.py` (walk de `_iter_local` en el fallback legacy) | ✅ hecho 2026-09-21 — mismo patrón que la exclusión ya existente de `_descartados/`/`TRASH_DIR_NAME`: nueva constante `EMULATOR_SAVES_DIR_NAME = "emulator_saves"` en `config.py` (reemplaza el literal ya usado en `get_adb_sync_sources()`), excluida en los 3 walks (`dirs[:] = [...]`) igual que `TRASH_DIR_NAME`. Aplica a ambos lados del walk (PC y Anbernic) — inocuo si el dispositivo está limpio, corta la fuga si no. 2 tests nuevos (`test_iter_files_skips_emulator_saves` en `test_cable_engine.py`, `test_pc_to_anbernic_never_uploads_emulator_saves_folder` en `test_cable_sync_rom_skip_existing.py`). Suite completa (1419 tests) sin regresiones nuevas. **No limpia los 54 archivos ya filtrados en el dispositivo real** — eso sigue en `CABLE-SYNC-LEGACY-DUPS-1` (ya respaldados en `.rommgr/legacy_dups_backup_2026-09-21/`), este fix solo corta la fuga hacia adelante |

---

### SAVES-UX — Historial de saves y contexto en resolución de conflictos (idea usuario 2026-09-22)

Reducir el "miedo a sobrescribir" del pilar 3 más allá del backup-antes-de-
sobrescribir ya existente: dejar ver y restaurar versiones anteriores, y dar
más contexto que solo el timestamp al resolver un conflicto.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| SAVES-HISTORY-1 | **Replanteada tras investigar (2026-09-22)**: el historial+restauración ya existía y funcionaba (`rom_manager/backup/save_backup.py`, `GET /api/save-backups`, `POST /api/restore-backup`, UI en la ficha de juego `games.js:877-885,1090-1113`) para Cloud Sync, Cable Sync manual y renombrado. El gap real era el daemon SD auto-sync (`CABLE-UX-9a`), que usaba un segundo sistema aislado (`.rommgr/cable_sync_backups/<fecha>/`) invisible en esa UI | `web/cable_sync_daemon.py` (`_run_sd_auto_sync`), `rom_manager/backup/save_backup.py` | ✅ hecho 2026-09-22 (rama `feature/saves-ux-history-context`): daemon migrado a `backup_save()`, mismo patrón que `sync_cable.py`. Verificado contra el sistema de archivos real: `.rommgr/cable_sync_backups/` no existía (el daemon nunca disparó esa rama en la práctica) — nada que migrar. 1430 tests pass (3 ambientales), ruff+format limpios |
| SAVES-CONFLICT-CTX-1 | Al resolver un conflicto de sync, mostrar contexto además del timestamp (playtime asociado, tamaño). Solo Cloud Sync (Cable Sync no detecta conflictos hoy) | `sync/conflict_resolver.py`, `sync/save_syncer.py`, `web/handlers/sync_cloud.py`, `web/static/js/tabs/sync.js` | ✅ hecho 2026-09-22 (rama `feature/saves-ux-history-context`): `SyncDecision` con tamaños, `_decision_payload()` añade mtime/tamaño/playtime best-effort (match por stem contra `games`) solo para conflictos, UI pinta la línea de contexto bajo cada fila. 4 tests nuevos, 1434 pass, ruff+format limpios |
| SYNC-CONFLICT-MANUAL-1 | Revisión manual de conflictos de Cloud Sync desde la UI antes de sincronizar — por archivo, elegir PC/Consola/omitir en vez de que `conflict_policy` global decida siempre por todos. No aplica a Cable Sync (sin detección de conflictos hoy) | `sync/save_syncer.py`, `web/handlers/sync_cloud.py`, `web/static/js/tabs/sync.js` | ✅ hecho 2026-09-22 (rama `feature/saves-ux-history-context`): `sync_saves()` acepta `conflict_overrides` (gana sobre `conflict_policy` por archivo, `skip` no toca nada); selector por fila en el plan de dry-run, recogido al pulsar Sincronizar. 3 tests nuevos, 1437 pass, ruff+format limpios |

### SAVE-GUARD — No dejar que un save dañado gane un conflicto (idea 2026-10-03)

Pilar 3, prioridad alta (pérdida de progreso). Hoy `conflict_policy` decide por mtime; un save de 0 bytes o truncado reciente podría machacar uno bueno antiguo. El backup previo (`backup_save()`) mitiga pero no evita el sobrescrito.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| SAVE-GUARD-1 | **Investigar primero** (regla "investigar antes de arreglar"): confirmar en `sync/conflict_resolver.py` / `sync/save_syncer.py` si hoy hay alguna guarda de tamaño; documentar archivo:línea y caso real reproducible | `sync/conflict_resolver.py`, `sync/save_syncer.py` | ✅ 2026-10-03 — **hueco confirmado por lectura de código, sin caso real**: (1) `decide()` (`conflict_resolver.py:22-61`) solo mira mtimes; ninguna guarda de tamaño en todo `save_syncer.py` (el tamaño solo se copia a `SyncDecision` como contexto, `:178-179`). (2) **Upload normal** (`save_syncer.py:207-216`): un local de 0 bytes/truncado con mtime más nuevo sobrescribe el remoto bueno y **no hay backup del remoto** (a diferencia del download, `:250-259`, que sí respalda el local). rclone `copyto` solo verifica checksum de la transferencia, no la validez del contenido. (3) **Conflicto `newest`** (`:346-352`): gana el mtime más nuevo aunque sea 0 bytes; el perdedor sí queda como `.conflict-<ts>`, así que no se pierde pero el dañado pasa a canónico. (4) **Android** (`SyncEngine.kt:88-94`): `DOWNLOAD` sobrescribe el local **sin backup**; el conflicto sí respalda (`:136`). Subida local-gana sin backup remoto (`:134`) apoyada en el versionado de Dropbox. (5) Cable Sync compara tamaños solo para saltar copias idénticas (`sync_cable.py:793-823`), no como guarda. **Datos reales (2026-10-03, disco E: conectado, `config.toml` real: saves en `E:\RetroVault\ROMS\saves`)**: escaneadas las 8 `local_dir` de `sync.sources` — **14 de 249** saves de RetroArch tienen 0 bytes, todos `.sav` de `nds/` con mtime de 2025 (HeartGold, Dragon Ball Origins, GoldenEye, Nintendogs, Robots, TWEWY, Trace Memory…); el resto de fuentes (states, DuckStation, Dolphin GC/Wii, Dusklight) 0. `rclone lsl` de `dropbox:/RetroSync/saves/retroarch/saves/nds` muestra **los mismos 14 a 0 bytes con el mismo mtime** → ya están sincronizados, **no se ha detectado pérdida real** (ningún save bueno sobrescrito por uno vacío). Qué los crea (¿melonDS escribe un `.sav` vacío al abrir un juego sin guardar?) no verificado. Riesgo vigente: un `.sav` vacío recién creado en un lado (mtime nuevo) ganaría al guardado real más antiguo del otro. **Lado consola (RG556 por ADB, 2026-10-03)**: `H:` sigue sin montar pero `tools/adb.exe` ve el dispositivo. Mismos 0 bytes en `.sav` NDS en `RetroArch/saves/nds` (los 14 del PC, mismas fechas 2025) y en copias duplicadas por varias rutas (`/storage/521D-04EA/ROMs/nds`, `/saves/nds`, `RetroArch/saves/retroarch/...`). **Caso de riesgo real localizado, pero fuera de sync**: `Pokemon - Edicion Plata SoulSilver (Spain).sav` — el bueno (524.288 B, 2026-09-26) está en `RetroArch/saves/nds`, mientras `me.magnum.melonds/files/saves/` tiene uno de **0 bytes con mtime 2026-10-02 12:05** (más nuevo; igual para HeartGold y Oro/4832, mismo minuto → escritura en bloque, causa no determinada). Esa carpeta de melonDS **no es fuente de sync** ni en `config.toml` ni en la app Android, así que no hay exposición hoy; si alguien la añadiera, el vacío ganaría por mtime. Ningún save bueno sobrescrito detectado en ningún lado **`save_sync_log` revisado 2026-10-04** (`library_pc.db`, 35.992 filas, solo lectura): 32.667 rutas con alguna subida; **30 hoy miden 0 bytes** (los `.sav` NDS ya conocidos, en `ROMS/nds/` y `ROMS/saves/nds/`), todas subidas por primera vez el **2026-08-14 08:46-08:48** (siembra inicial, antes de la guarda). Ninguna fila `suspect`/`skipped_suspect` (aún no ha habido ninguna). **Limitación**: la tabla no guarda el tamaño subido, así que no se puede probar que ninguna fue un save bueno sobrescrito; coherente con la comprobación del 2026-10-03 (mismos 0 bytes en el remoto, mismo mtime). Sin hallazgo nuevo; pendiente menor cerrado |
| SAVE-GUARD-2 | **Decisiones (2026-10-03, acordadas con el usuario)**: (1) save sospechoso → no tocar ningún lado, `sync_log` `skipped_suspect`, fila de conflicto en la UI resuelta con el selector por archivo de `SYNC-CONFLICT-MANUAL-1` (mismo camino que el override `skip`, `save_syncer.py:302-315`); `decide()` sigue solo con mtimes, la guarda va justo después. (2) Umbral: solo 0 bytes frente a >0 en el otro lado; sin % de reducción (0 de 231 saves comunes PC/Dropbox cambian de tamaño, y `.nv/.sgm/.ml1/.dat` son de tamaño variable → falsos positivos); un 0 bytes sin pareja se sigue subiendo. Orden: lado PC con test primero, luego Android. Alcance según SAVE-GUARD-1: guarda en `save_syncer.py` (upload y conflicto) **y** espejo en `SyncEngine.kt`; backup del remoto antes de sobrescribir en upload; backup local en `DOWNLOAD` de Android. Un save de 0 bytes, o mucho más pequeño que el anterior, nunca sobrescribe a uno válido — se marca como conflicto para revisión manual (reusa `SYNC-CONFLICT-MANUAL-1`). Test con save de 0 bytes más reciente | `sync/conflict_resolver.py` | ✅ 2026-10-03 (PR #400): PC en `save_syncer.py` (`SyncDecision.suspect`, `skipped_suspect`, respeta override) con 4 tests; Android en `SyncEngine.kt` (`ConflictResolver.isSuspectEmpty`, se omite y cuenta como conflicto) + respaldo `<nombre>.bak` antes de `DOWNLOAD`. Backup del remoto en upload **descartado** (el remoto es Dropbox, que versiona). **Android sin probar en la RG556** — ver plan bajo ANDROID-BATTERY-1; el APK instalado hoy es de antes de #400 |
| ANDROID-BATTERY-1 | **Investigar consumo de batería de la app Android** (petición del usuario 2026-10-03). **Medición real NO conseguida**: al reinstalar la app (`adb uninstall`, necesario por firma distinta) se perdieron sus estadísticas de batería; ventana restante = 8h38m en batería con pantalla apagada, 950-1000 mAh de 5000 de los cuales `com.retrovault.android` ya no aparece (el mayor consumidor de apps era `app.gamenative`, ~5 mAh; el grueso es sistema: wakelocks del kernel 92 mAh, wifi 148 mAh, idle 113 mAh). **Candidatos por lectura de código, sin medir**: (1) modo Instantáneo (`SaveFileObserverManager.kt`, debounce 3 s): cada escritura en saves/states lanza un `runFullSync` **completo** (`SyncOrchestrator.kt:53-65`: `listFolderRecursive` de Dropbox para saves + states + 6 carpetas arcade = 8 listados de red por evento) — con un autosave de RetroArch durante una partida es red constante; además los DOWNLOAD propios disparan el observer otra vez (eco). (2) Periódico 15 min (`PeriodicSyncScheduler.kt`, mínimo de WorkManager) = 96 pases/día × 8 listados, sin `setRequiresBatteryNotLow`, y sigue activo con el Instantáneo encendido (red de seguridad). **Palancas propuestas, por orden de impacto/esfuerzo**: a) en Instantáneo, sincronizar solo la carpeta afectada en vez de las 8 y ampliar el debounce (p. ej. 30-60 s); b) periódico a 30-60 min cuando el Instantáneo está activo, y `setRequiresBatteryNotLow(true)`; c) ignorar eventos del propio sync. **Antes de tocar nada: medir** — login Dropbox, activar los modos, usar unas horas y volcar `dumpsys batterystats` filtrado por la app (`adb shell dumpsys batterystats --charged \| grep -A3 u0a158`) | `sync/SaveFileObserverManager.kt`, `sync/SyncOrchestrator.kt`, `sync/PeriodicSyncScheduler.kt` | 🟡 optimización mergeada 2026-10-03 (PR #401: Instantáneo por raíz + throttle 30 s, periódico 30 min + batería no baja); **sin medir** el efecto real — plan de medición debajo |

#### Plan de medición ANDROID-BATTERY-1 / SAVE-GUARD-2 Android (próxima sesión con la RG556)

Estado al dejarlo (2026-10-03): en la RG556 está instalado el release firmado de la rama `perf/android-sync-battery` (PR #401: Instantáneo por raíz + throttle 30 s, periódico 30 min + batería no baja) **sin** la guarda de 0 bytes de SAVE-GUARD-2 (PR #400): ese APK se compiló desde `develop`, donde #400 aún no estaba mergeado. La prueba de SAVE-GUARD-2 en Android exige antes un APK de una rama que incluya #400 (y #401). Dropbox con login hecho. Sin medición previa válida (la reinstalación borró las estadísticas).

**Requisitos:** consola **desenchufada** (en USB `batterystats` no atribuye consumo a apps), `adb devices` visible al empezar y al terminar, anotar hora y % de batería de inicio.

**Tramo A — solo periódico (Instantáneo apagado)**, ≥3-4 h de uso normal / reposo:
1. Al terminar: `adb shell "dumpsys batterystats --charged"` → buscar el UID de `com.retrovault.android` (`pm list packages -U`), anotar mAh, `cpu`, `wifi`, `wakelock`.
2. `adb shell "dumpsys jobscheduler | grep 'com.retrovault.android'"` → nº de pases y duración media de cada START/STOP (esperado ≈ 1 cada 30 min; 1 listado… ver 8 listados en `SyncOrchestrator.kt`).
3. En la app, pestaña de historial: filas `PERIODIC`, errores y conflictos.

**Tramo B — Instantáneo encendido**, una sesión de juego de ~1 h con autosave de RetroArch:
1. Mismas mediciones + comprobar que el servicio foreground corre (`dumpsys activity services com.retrovault.android`).
2. Historial: filas `INSTANT` — esperado como mucho 1 cada ~30 s por raíz tocada, no una por escritura; ninguna debería traer los 8 listados.
3. Latencia real: guardar en juego y medir cuánto tarda el save en aparecer en Dropbox/PC (esperado ≤ ~30-40 s).

**Criterio de decisión:** si la app queda por debajo de ~2-3 % de la batería gastada en el tramo, dar ANDROID-BATTERY-1 por cerrado. Si no, siguientes palancas: periódico a 60 min con Instantáneo activo, ignorar eventos del propio sync, o `setRequiresCharging`/Wi-Fi-only.

**Prueba SAVE-GUARD-2 en Android** (con la app que incluya la guarda): elegir un juego de prueba con save bueno en Dropbox y local; dejar su `.sav` local en 0 bytes con mtime posterior (`adb shell` + `touch`), sincronizar manualmente y comprobar que: el save de Dropbox sigue intacto, el local vacío no se sube, y el pase cuenta 1 conflicto. Restaurar el save bueno después.

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
| HERR-FIX-4 | **UI: la pestaña "Herramientas" oculta el menú lateral de pestañas en algunos de sus paneles** — bug de layout, no investigado | `web/static/css/app.css` o partials de Herramientas | 🔵 **investigado 2026-09-24, no reproducido — hipótesis original descartada**. La hipótesis previa (tablas sueltas en `esde.js` sin `overflow-x:auto`) no se sostiene: `app.css:496` ya tiene una regla global `td { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:320px }` que protege TODAS las tablas de la app (confirmado por `git blame`: la regla es del 2026-03-18, anterior al reporte del bug — no es que algo cambiara después, la hipótesis estaba mal formulada desde el principio). Probado en vivo con la extensión de Chrome contra la biblioteca real: Library Doctor (rutas/nombres reales largos), detección de perfil de dispositivo, Análisis de carpeta (Formatos, 1723 extensiones) — sidebar intacto en los tres. Forzada además una ruta artificialmente larguísima vía DOM en el panel de perfil de dispositivo (el único punto sin protección de tabla que se identificó) — la regla global de `app.css:496` la contuvo igual, sin desbordar. Sin repro tras cubrir los paneles más probables — si el usuario lo ve reaparecer, hace falta el panel exacto + pasos para reabrir esta tarea |

---

### JUEGOS-FIX-2 — El filtro de plataforma en Juegos es casi inútil en bibliotecas grandes (hallado 2026-08-29)

Origen: feedback del usuario tras probar el buscador — "no puedo filtrar por plataforma".

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| JUEGOS-FIX-2 | **El desplegable "Plataforma" de Juegos solo se rellena con las plataformas presentes en la página actual de resultados** (`loadGames()`, `games.js:452-460` aprox., máx. 100 filas) — con el orden por defecto (`platform, canonical_title, original_filename`) y una biblioteca de 28k+ juegos con muchos sin plataforma (`NULL` ordena primero en SQLite), **la primera página cae entera en "Unknown"** — verificado en vivo: `/api/games?limit=100` real devuelve una única plataforma distinta (`Unknown`) en sus 100 filas, así que el filtro no ofrecía ninguna otra opción. `GET /api/games/filter-options` ya devuelve las 43 plataformas reales distintas de la BD (usado para género/año, `games.py` repositorio, consulta `SELECT DISTINCT platform...`) pero `loadFilterOptions()` (`games.js:129-145`) nunca lo usaba para rellenar `games-platform` | `web/static/js/tabs/games.js:129-145` (`loadFilterOptions`) | ✅ `loadFilterOptions()` rellena también `games-platform` desde `r.platforms` (mismo endpoint ya usado para género/año, sin llamada nueva) y marca `platformsLoaded=true` para que el muestreo antiguo de `loadGames()` no lo pise; ese muestreo queda como fallback solo si `filter-options` fallara. Verificado contra la biblioteca real: `filter-options` devuelve las 43 plataformas reales (Amiga, Arcade, Atari 2600...). No verificado en navegador (extensión Chrome no disponible esta sesión) |

| JUEGOS-FIX-3 | **"El nombre del juego no aparece en la tabla del frontend"** (feedback usuario 2026-08-29, tras confirmar que no era caché de navegador). Causa raíz real: `applyColVisibility()` (`games.js`, columnas opcionales Región/Identificación/Tamaño/SHA1 del selector ⚙) ocultaba celdas por **índice fijo** (`tr.cells[3..6]`, comentario "0=platform,1=title,2=filename..." — ya desactualizado antes de esta sesión, no contaba ni con la ★ favorito ni con la miniatura). Al añadir hoy la columna 📦 Anbernic (`ANBERNIC-PICK-7`), cada índice se desplazó una posición más: `COL.match=4` pasó de apuntar al badge de Identificación a apuntar directamente a la celda de **Título canónico** — con la preferencia de columnas del usuario guardada en `localStorage` (p.ej. "Identificación" desmarcado en algún momento), `applyColVisibility()` ocultaba el título en cada render sin que nada más pareciera roto | `web/static/js/tabs/games.js` (`applyColVisibility`, fila de la tabla) | ✅ cada `<td>` opcional lleva ahora `data-col="region\|match\|size\|sha1"` fijo en el propio template de la fila; `applyColVisibility()` selecciona por ese atributo (`tr.querySelector('[data-col=...]')`) en vez de por índice — inmune a que se añadan o quiten columnas en el futuro. De paso confirmado con los valores por defecto (`size:false, sha1:false`) que el bug de índice YA escondía "Archivo original"/"Estado" en vez de "Tamaño"/"SHA1" para todo el mundo, no solo para quien tocara el selector ⚙ — corregido igual. 1037 pass |
| JUEGOS-FIX-4 | **El nombre no aparece porque la página 1 (orden por defecto) cae entera en juegos sin `canonical_title`** (feedback usuario 2026-09-26, verificado en vivo contra `library_pc.db` real vía navegador). Causa raíz distinta de `JUEGOS-FIX-3` (ese ya está resuelto): el orden por defecto "Título" (`database/repositories/games.py:597,605,607` — `ORDER BY canonical_title, original_filename` / fallback `platform, canonical_title, original_filename`) no usa `COALESCE`, y SQLite ordena `NULL` **primero** en `ASC` — con 3.994 ROMs sin match de 36.271 (`canonical_title IS NULL`), la tabla/galería muestra "—" en Título canónico durante varias páginas antes de llegar al primer juego identificado. Se agrava con un hallazgo de higiene de datos aparte: 7 de esas filas (`$I1P4IQH.iso`, `$I4LFZWH.iso`, `$I5BX7IZ.iso`, `$I8W3737.iso`, `$IDIVEYU.iso`, `$IGMP334.bin`, `$IU7H240.cue`, `platform=NULL`) son restos de la Papelera de Windows (`source_path` bajo `E:\$RECYCLE.BIN\S-1-5-21-...\`), probablemente de un scan antiguo de `E:\` completo hecho antes de fijar `library_root` a `E:\Carpetas anbernic` — el guard `_EXCLUDED_DIR_NAMES` (`scanner/rom_scanner.py:27-28`, ya incluye `"$recycle.bin"`) evita que un scan futuro los vuelva a indexar, pero un scan con `source_path=library_root` nunca visita ni poda filas fuera de esa raíz, así que las 7 quedan huérfanas para siempre | `database/repositories/games.py:592-607` (todas las claves `_order`, con y sin `need_meta`) | ✅ **(1) hecho 2026-09-28** — `COALESCE(canonical_title, original_filename)` aplicado a las 5 claves de `_order` (con y sin `need_meta`), 2 tests nuevos (`tests/test_games_order_coalesce.py`, rojo→verde confirmado), suite `games`/`repository` completa en verde, ruff+format limpios. **(2) hecho 2026-10-02** — confirmados los 7 ids exactos (`26531-26537`) en `.rommgr/library_pc.db` de la máquina rammu, sin filas hijas en `game_metadata`/`game_tags`/`file_operations`, `DELETE FROM games WHERE source_path LIKE '%$RECYCLE.BIN%'` ejecutado, 0 filas restantes verificado. Tarea cerrada del todo |

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

---

### MOBILE-UI — UI usable desde el móvil (idea usuario 2026-09-22)

Gestionar la biblioteca desde el móvil en la misma red — hoy el layout está
pensado para desktop.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MOBILE-UI-1 | Layout responsive (sidebar colapsable, tablas con scroll horizontal, controles táctiles) para las pestañas de uso más frecuente | `web/static/css/app.css`, `web/static/templates/*.html` | ⬜ sin diseñar |

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

### RA-LIVE — Progreso de logros en la ficha del juego (idea usuario 2026-09-22)

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| RA-PROGRESS-UI-1 | Mostrar progreso de logros (desbloqueados/totales) en la ficha de cada juego | `ra_client.py`, `web/static/js/tabs/games.js` | ⬜ bloqueado por la validación pendiente de la API key real (ver memoria `phases.md`) |

---

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: JUEGOS-UX-1..9 (logros individuales por juego + playtime automático PC/Anbernic — completo, 2026-07-13).

---

## Estandarización de biblioteca multi-launcher (ES-DE + ROM hacks/fan projects) — → #337

Carpeta y convención de nombres única para PC/Anbernic que también sea
compatible con ES-DE (no solo RetroArch) y que sepa colocar ROM hacks/fan
projects (parchean una ROM oficial pero no matchean ningún hash No-Intro/
Redump — ej. "Twilight Princess - Dusklight" sobre la ROM base de Wii/
GameCube) en su plataforma real en vez de caer en `Unknown/`. Fusiona la idea
abierta `ESDE-CONFIG-CHECK` de `Roadmap-212-Ideas-Futuras.md` (movida aquí).

### ESDE-FOLDER-STD-1 — Confirmar y cerrar el hueco real de integración ES-DE (idea usuario 2026-09-22)

El proyecto ya genera `gamelist.xml` (`scraper/gamelist_writer.py`), metadata
Pegasus (`scraper/pegasus_writer.py`) y sistemas/cores
(`esde/systems_generator.py`, en uso hoy para iiSU vía `IISU-CONFIG-1`) — la
suposición de que "no hay nada" (ROADMAP-IDEAS, 2026-08-29) era incorrecta.
Falta decidir con el usuario qué hueco concreto queda: ¿`es_systems.cfg`/
rutas específicas de ES-DE en Android? (ver `DEVPROFILE-4`, marcado "sin
cambio" en su momento) ¿o ya está cerrado y solo falta documentarlo?

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ESDE-FOLDER-STD-1 | Sesión de decisión con el usuario: listar qué genera hoy el proyecto para ES-DE contra lo que ES-DE necesita realmente en Android/PC, y cerrar la brecha si la hay | `scraper/gamelist_writer.py`, `scraper/pegasus_writer.py`, `esde/systems_generator.py` | ⬜ pendiente, decisión del usuario primero |

### ROMHACK-ORG-1 — Organizar ROM hacks / fan projects que no matchean catálogo oficial (idea usuario 2026-09-22)

Origen: `E:\Juegos nativos` contiene proyectos como "Twilight Princess -
Dusklight", un hack de fans sobre la ROM base de Wii/GameCube — no es un
dump oficial, no tiene entrada en No-Intro/Redump, así que no matchea por
hash. El usuario confirma que **no** quiere un catálogo propio de hacks
(demasiados proyectos de fans para mantenerlo) — el alcance real es que la
herramienta reconozca "esto no matchea pero tampoco es basura" y lo organice
en la carpeta de su plataforma real en vez de dejarlo en `Unknown/`.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ROMHACK-ORG-1 | Definir heurística para detectar ROM hacks sin catálogo (¿extensión+tamaño de la plataforma base, nombre, carpeta de origen?) y decidir destino: ¿misma carpeta de plataforma que el juego base, o subcarpeta `<plataforma>/hacks/`? Sin matching por hash — solo organización | `catalog/matcher.py`, `web/inbox_pipeline.py` | ⬜ sin diseñar — decisión de convención pendiente con el usuario antes de tocar código |

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
`Tareas/diario/archivo/Roadmap-DEVPROFILE-1-4-completado.md`.

**DEVPROFILE-8b/9** (archivos sueltos): resuelto — ver
`.claude/roadmaps/archivo/19-device-profile-loose-data.md`.

**Diseño de DEVPROFILE-5/6** (botones de restauración PC/Android,
verificado contra el código real — incluye un hueco real encontrado: nadie
sube el manifiesto de perfil al remoto todavía): ver
`Tareas/diario/archivo/Roadmap-DEVPROFILE-5-6-completado.md`.

| ID | Task | Esfuerzo | Estado |
|----|------|----------|--------|
| DEVPROFILE-0 | **Bloqueante**: verificar dónde vive `retroarch.cfg` en la RG556 (por cable, `tools/adb.exe`) | XS | ✅ resuelto 2026-08-25 en hardware real — **NO accesible sin root**: `/data/data/com.retroarch/` da `Permission denied`, `run-as` falla (`package not debuggable`, build Play Store), y no hay ningún `retroarch*.cfg` en almacenamiento público. Sí son accesibles `config/<Core>/*.opt`, `retroarch-core-options.cfg`, `config/remaps/` y `system/`. Ver comentario en #238 |
| DEVPROFILE-1 | `docs/architecture/platforms-cores.md` (prosa) → JSON de datos, fuente única de `lpl_generator.py`, `esde/systems_generator.py`, `bios_checker.py` y la asignación de core por defecto | S | ✅ 2026-08-31 — ver `Tareas/diario/archivo/Roadmap-DEVPROFILE-1-4-completado.md` §2 para el detalle. `lpl_generator.py` no necesitaba cambio (usa `DETECT` a propósito, no un hueco real). Migrados `bios_checker.KNOWN_BIOS` (22 entradas) y `systems_generator._SYSTEMS` (20 cores PC) a `platforms.toml` (`[[bios]]` / `[cores.pc]`), vía `platform_detector.bios_definitions()`/`pc_cores_by_system()`. `mame`/`fbneo` mantienen listas de cores distintas a propósito (comparten canónico "Arcade" pero no deben fusionarse). Verificado con 4 tests nuevos (`tests/test_systems_generator.py`) + paridad exacta de los 22 valores de BIOS; suite completa en verde (1094 pasan, mismos 3 fallos preexistentes de ADB sin relación) |
| DEVPROFILE-2 | Escribir `savefile_directory` / `savestate_directory` / `sort_savefiles_by_content_enable` / `sort_savestates_by_content_enable` en `retroarch.cfg` del **PC únicamente** (en Android no es viable sin root, ver DEVPROFILE-0). Sigue siendo el ítem de más valor en el lado PC: hoy el sync *adivina* el layout; escribir esas claves lo hace idéntico por construcción → prevención de pérdida de progreso, pilar 3 | S | ✅ 2026-09-01 — ver `Tareas/diario/archivo/Roadmap-DEVPROFILE-1-4-completado.md` §3. `retroarch_cfg_writer.py` (`apply_savefile_layout`/`default_savefile_layout`) + botón manual "Aplicar layout de saves" en Settings (`POST /api/retroarch-apply-savefile-layout`), destino `library_root/saves`+`/states` (mismo convenio que `sync.saves_remote`/`states_remote`). 11 tests en verde |
| DEVPROFILE-3 | Tokenizador de rutas: `{ROMS}` / `{SAVES}` / `{SYSTEM}` al guardar, sustitución por las del dispositivo destino al restaurar | S | ✅ 2026-09-01 — `services/path_tokenizer.py` (`tokenize`/`resolve`, puras). 6 tests. Ver `Tareas/diario/archivo/Roadmap-DEVPROFILE-1-4-completado.md` §4 |
| DEVPROFILE-4 | Manifiesto Tier A + backup del perfil al remoto — **alcance recortado tras DEVPROFILE-0**: `config/<core>/*.cfg`, `retroarch-core-options.cfg`, `config/remaps/`, `autoconfig/`, shaders, `.opt` en bulk, BIOS/`system/`; `retroarch.cfg` solo en el lado PC. Standalones de PC sin cambio: `duckstation/settings.ini`, `PCSX2/inis/`, `Dolphin/Config/`, `es_systems.cfg` | M | ✅ 2026-09-01 — backend (`services/device_profile.py`, 5 tests) + pantalla de Settings "Perfil del dispositivo" (`GET /api/device-profile-detect`, reusa `POST /api/config` con `sync.sources` para guardar). Rama `feature/devprofile-4a-settings-ui`. Ver Roadmap §5 |
| DEVPROFILE-5 | Botón PC — `rommgr restore`: `download-tools.ps1` → `config.toml` desde el perfil (sustituye media `wizard.py`) → Tier A con rutas reescritas → regenerar Tier B → `bios_checker` y reportar lo que falta | M | ✅ 2026-09-01, ver `Tareas/diario/archivo/Roadmap-DEVPROFILE-5-6-completado.md` — 5a (subir manifiesto) + 5b-5f (comando `rommgr restore` completo) en la misma rama `feature/devprofile-5a-export-manifest`. `restore` (nuevo subparser en `cli.py`) descarga `device-profile.json` (`RcloneTransport.download`, fallback-remote), pide `library_root`/ruta de RetroArch (reusa `_ask`/`_ask_yn`/`_detect_tool` de `wizard.py`), resuelve los tokens con `import_profile_sources()` (ya existía, sin caller hasta ahora) y escribe `config.toml` con `write_config_toml()` — mismo aviso de sobreescritura que el wizard. Crea cada `local_dir` con `mkdir(parents=True)` y llama a `sync_saves()` por fuente (dry-run por defecto, `--apply` para bajar de verdad — mismo patrón que `rommgr sync`). Si hay RetroArch configurado y ES-DE está instalado, regenera `custom_systems/es_systems.xml` con `generate_es_systems_xml()`. Termina con `check_bios()` sobre `library_root`/`library_root/bios`/`retroarch/system` y lista las BIOS requeridas que faltan. Test nuevo `tests/test_cli_restore.py` (manifiesto+config.toml de punta a punta con `RcloneTransport._run` fake, sin tocar rclone real). Suite completa 1127 en verde |
| DEVPROFILE-6 | Botón Android — "Restaurar este dispositivo" tras el login de Dropbox: restaura core options/remaps/BIOS (no el cfg global, ver DEVPROFILE-0); el sync periódico ya arranca solo (ANDROID-SYNC-12). El Core Downloader sigue siendo manual | S | 🟡 **implementado 2026-09-28, alcance recortado por segunda vez tras nueva investigación**: el manifiesto `device-profile.json` (Tier A, `services/device_profile.py`) solo lleva `autoconfig/`+`shaders/`+`system/` (BIOS) + 2 playlists — **"core options/remaps" NO viaja en él** (van por `sync.ra_config_dir`/`ra_config_remote`, remoto separado, sin configurar hoy en el PC de esta máquina). Decisión del usuario: implementar solo lo que ya hay en el manifiesto, dejar core options/remaps documentado como bloqueado en vez de rediseñar el lado PC en la misma sesión. Nuevo `sync/DeviceProfileRestore.kt` (Android): descarga `device-profile.json` desde `remoteBaseFrom(savesRemote)` (mismo criterio que `web/handlers/system.py:543`), aplica las carpetas conocidas vía `SyncEngine.sync()` reutilizado (local vacío en un dispositivo nuevo → todo `DOWNLOAD`, sin riesgo) y los 2 archivos sueltos vía `DropboxTransport.download()`; entradas sin destino Android conocido (catálogos, `library_pc.db`/`library_android.db`) van a `skipped`, no son error. Botón "Restaurar este dispositivo" en `SettingsScreen.kt` (sección "Perfil del dispositivo", visible con Dropbox conectado) + wiring en `MainActivity.kt`. 6 tests nuevos (`DeviceProfileRestoreTest.kt`, funciones puras `remoteBaseFrom`/`parseManifest`) — requirió añadir `testImplementation("org.json:json:20240303")` a `build.gradle.kts` (el stub de `org.json` en unit tests JVM lanza en cada llamada sin una implementación real; `PcApiClient.kt` ya usaba `org.json` en producción sin que ningún test lo ejercitara). `./gradlew testDebugUnitTest`/`assembleDebug` reales en verde (toolchain portátil `C:\Users\Ruben\android-build-tools\`). **No verificado en hardware real** (sin RG556 conectada esta sesión) — pendiente probar el botón contra un `device-profile.json` real subido por `DEVPROFILE-5a`. **Pendiente aparte**: si se quiere cerrar "core options/remaps" de verdad, hace falta (a) configurar `ra_config_dir`/`ra_config_remote` en el PC y (b) decidir si viajan en el mismo manifiesto o por un mecanismo propio en Android — no decidido |
| DEVPROFILE-7 | Detección de deriva: comparar el `retroarch.cfg` vivo contra el del perfil y avisar si cambian los directorios de save ("tus partidas nuevas no se están sincronizando"). Sale gratis una vez existe DEVPROFILE-4 | S | ✅ 2026-09-01 — `_handle_retroarch_check()` compara `savefile_directory`/`savestate_directory` contra `default_savefile_layout(library_root)` (convenio D2, ya existente desde DEVPROFILE-2) y añade `savefile_drift`+issue accionable si no coincide. Sin endpoint ni UI nuevos — reusa `/api/retroarch-check` y el panel de issues ya existente. **Detectó deriva real en este PC**: `savefile_directory` apuntaba a `E:\ROMs\saves` (ruta obsoleta) en vez de `E:\Carpetas anbernic\saves` — pulsar "Aplicar layout de saves" en Settings lo corrige. 2 tests (`tests/test_retroarch_check_drift.py`) |
| DEVPROFILE-8 | Restaurar lo que evita retrabajo caro en un PC nuevo: BD SQLite (evita rehashear la biblioteca entera, horas), caché de ScreenScraper (cuota diaria de API) y DATs No-Intro/Redump | S | ✅ 2026-09-24 — **hallazgo real** (2026-09-06): no existe una "caché de ScreenScraper" separada, los metadatos scrapeados viven como columnas en `library_pc.db` (mismo archivo que evita el rehash). DATs vía `detect_data_sources()` (carpeta completa, ya existente); **DEVPROFILE-8b** (`library_pc.db`/`library_android.db`, archivos sueltos) resuelto con `SyncSource.single_file` + `sync_single_file()` (`sync/save_syncer.py`) — decisión de diseño: single-file source kind nuevo. Ver `.claude/roadmaps/archivo/19-device-profile-loose-data.md` |
| DEVPROFILE-9 | Datos de usuario que deberían seguirte entre dispositivos: `content_history.lpl` (recientes), `content_favorites.lpl`, `.lrtl` (playtime, ver MEJ-1), credenciales RA (`cheevos_*`, en almacenamiento cifrado) | S | ✅ 2026-09-24 — `content_history.lpl`/`content_favorites.lpl` vía `detect_tier_a_sources()` + `single_file=True` (mismo mecanismo que DEVPROFILE-8b). `.lrtl` ya estaba cubierto por JUEGOS-UX-7 (`build_cloud_sync_sources()`, carpeta completa) — no duplicado. Credenciales RA (`cheevos_*`) siguen fuera de alcance: accesibilidad sin root no confirmada (mismo límite que DEVPROFILE-0) |

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
| ESDE-CONFIG-CHECK | **Movida** a `ESDE-FOLDER-STD-1`, sección "Estandarización de biblioteca multi-launcher" (→ #337), 2026-09-22 — misma idea, fusionada con la propuesta de carpetas estandarizadas del usuario | — |
| LIBRARY-MANAGER-UI | Pantalla única "gestionar ambas bibliotecas a discreción" — copiar y borrar PC↔Anbernic con control fino, en vez de repartido entre Cable Sync (copiar), `ANBERNIC-PICK` (marcar) y `STORAGE-MGR` (borrar en bloque, archivado). El usuario pide explícitamente esto tras no encontrar cómo hacerlo hoy (2026-08-29) | Fusiona 3 mecanismos ya existentes en una sola UI — no es una feature nueva de backend, es una consolidación de UX; valorar junto con `ANBERNIC-PICK-7` (sync guiado) y `GAME-BLOCKLIST` (borrado permanente) antes de diseñar, pueden compartir la misma pantalla |
| HEALTH-SCORE | Puntuación única de salud de la biblioteca en el dashboard (% con nombre canónico, % con logros RA, duplicados pendientes) para ver el progreso sin abrir cada herramienta | Idea 2026-10-03. Solo agrega datos que ya calculan health check/duplicados/RA — sin lógica nueva de detección. ⬜ sin diseñar |
| DEVICE-PROFILES-MULTI | Soporte de más portátiles (Miyoo, Retroid, Steam Deck): mismo sync, otra ruta de saves/BIOS por dispositivo | Idea 2026-10-03. Depende de que `platforms.toml`/`device_profile.py` (DEVPROFILE-1..4) ya abstraigan el dispositivo — verificar eso antes de diseñar; sin hardware a mano no hay validación posible. ⬜ sin diseñar |
| COLLECTION-EXPORT | Exportar la colección (CSV/HTML con portadas) para compartir o tener un inventario fuera de la BD | Idea 2026-10-03. Barato: reusa `GET /api/export-history` y las portadas ya scrapeadas. ⬜ sin diseñar |

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: STORAGE-MGR-1..5 (gestor de almacenamiento PC/Android, borrado en bloque — completo y validado en hardware, 2026-08-14/2026-08-29).

---

## Transversal — Calidad de código, DX y referencia (sin epic)

Auditorías y limpieza que cruzan varios pilares a la vez (calidad de código,
onboarding, tests) — no tienen una épica de GitHub propia porque no son
roadmap de producto. Mayoría ya completada; se mantiene como referencia
histórica.

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: MEJORAS MEJ-1..6, AUD-1..6, TEST-CLEAN-1..3 + TEST-GAP-1, ONB-1..9, REV43-1..53 (calidad de código, onboarding, tests — completas, 2026-07-02 a 2026-07-15).

### JOBS-SQLITE-LOCK-1 — Dos jobs de escritura pesada en paralelo (`scrape` + `apply`/`inbox`) chocan por `database is locked` (hallazgo 2026-09-28, máquina "Ruben")

Origen: durante `JUNK-SCAN-RUBEN-1`, el scrape de `SAGE-1` (muchas
escrituras pequeñas, una por juego) y `zip-route-apply`/Inbox (escrituras
masivas: 3.301 archivos organizados) corrieron **a la vez** contra el mismo
`library_pc.db` — el scrape murió con `{"error": "database is locked"}` a
mitad de cola. No hubo pérdida de datos (lo ya escrito quedó guardado,
cobertura real subió de 27,78% a 38,36% antes de morir) y el job se
relanzó sin problema tras terminar el job pesado — pero es un fallo
silencioso: ningún otro job avisa "hay otro job pesado corriendo, esto
puede fallar", el usuario solo ve `scrape_running: false` sin explicación
si no revisa `scrape_result.error` a mano.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| JOBS-SQLITE-LOCK-1 | Ningún job de escritura (`scrape`, `apply`, `inbox`, `zip-route-apply`) comprueba si ya hay otro corriendo antes de empezar — `job_manager` sí lleva un flag `_running` por nombre de job, pero no hay coordinación **entre** jobs distintos. Dos caminos posibles, sin decidir: (a) que `_do_scrape`/otros escritores reintenten con backoff ante `sqlite3.OperationalError: database is locked` en vez de abortar (SQLite ya soporta `PRAGMA busy_timeout`, comprobar si `LibraryRepository.connect()` ya lo fija); (b) un guard simple "no lances un job de escritura pesada si `apply`/`inbox`/`scrape` ya están corriendo", igual que ya existe para el mismo job (`job_manager.cancel_event`) pero cruzado entre nombres | `web/jobs/manager.py`, `database/repository.py` (`connect()`), `web/handlers/scraper.py` (`_do_scrape`) | ✅ opción (a) implementada 2026-09-28 — confirmado que `LibraryRepository.connect()`/`_open_conn()` ya fijaba `PRAGMA busy_timeout=30000` + `sqlite3.connect(..., timeout=30)`, pero una ráfaga de escrituras de otro job (`zip-route-apply`, cientos de transacciones cortas seguidas) puede agotar igualmente esos 30s. `_commit_with_retry()` nuevo en `scraper.py`: reintenta solo `sqlite3.OperationalError` con "locked" en el mensaje (5 intentos, 2s de espera), aplicado en los 3 `commit()` de la ruta de escritura. 3 tests con conexión falsa (sin BD real). Opción (b) (guard cruzado entre jobs) descartada por ahora — el retry ya resuelve el síntoma real sin añadir coordinación nueva entre nombres de job |

---

### JUNK-SCAN-EXCLUDE-TRASH-1 — El junk-scan re-escanea su propia papelera `_descartados/` como basura activa (hallazgo 2026-09-28, máquina "Ruben", durante `JUNK-SCAN-RUBEN-1`)

`utils/trash.py::_iter_trash_files()` (línea 64-66) se protege explícitamente
contra re-procesar contenido ya descartado — en cuanto el `os.walk` entra en
una carpeta `_descartados`, corta `dirnames[:] = []` con el comentario
`# no anidar`. Esa misma protección **nunca se aplicó** al walker del
junk-scan (`web/builders/folders.py:321`, `_excluded_dirs = {"saves", "bios",
"android", "system volume information"}` — falta `_descartados`).

**Consecuencia real, verificada contra la biblioteca real**: 94 de 120
archivos del bucket "review" de `JUNK-SCAN-RUBEN-1` ya estaban dentro de
alguna `_descartados/` — re-contados como basura activa en cada scan, sin
poder resolverse nunca (`zip-route-apply` no toca contenido ya descartado,
así que el bucket parece "atascado" sin estarlo de verdad). Peor: repetir
`junk-delete`/extracciones sobre contenido ya en `_descartados` crea
`_descartados/_descartados/` anidado — **111 carpetas así confirmadas hoy**
en la biblioteca real — y esos archivos quedan **invisibles para
`purge_trash()`** (el mismo corte de `os.walk` que protege contra
re-listarlos también impide verlos un nivel más adentro), huérfanos para
siempre sin limpiarse solos. Sin pérdida de datos, pero desperdicia espacio
en disco y falsea cualquier medición de junk-scan futura.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| JUNK-SCAN-EXCLUDE-TRASH-1a | Añadir `_descartados` a `_excluded_dirs` en `_build_junk_scan()` — mismo patrón de una línea que `saves`/`bios`/`android` | `web/builders/folders.py:321` | ✅ arreglado 2026-09-28 — referencia `utils/trash.TRASH_DIR_NAME` en vez de hardcodear el string; test nuevo `test_junk_scan_skips_descartados_trees`. Suite completa 1457/1457, ruff+format limpios |
| JUNK-SCAN-EXCLUDE-TRASH-1b | Limpiar las 111 carpetas `_descartados/_descartados/` ya existentes — mover su contenido un nivel arriba (al `_descartados/` padre) antes de que `purge_trash()` pueda verlas, o extender `purge_trash()`/`_iter_trash_files()` para que si encuentra un `_descartados` anidado lo trate como parte del mismo padre en vez de ignorarlo | `utils/trash.py` o script de sesión (dato, no código) | ✅ hecho 2026-09-28 — script de sesión (no productizado): recorridas las 111 carpetas anidadas (más profundas primero, por si había más de un nivel), movido cada archivo al `_descartados/` padre con el mismo criterio de colisión que `discard_to_trash()` (sufijo numérico si el destino ya existe). **3.661 archivos recuperados, 0 colisiones, 111 carpetas anidadas eliminadas** (verificado: `find` real confirma 0 `_descartados/_descartados` restantes). Ahora sí visibles para `purge_trash()` |

---

### DOCS-AUDIT-1 — Seguimiento de la auditoría de documentación (2026-09-20)

Plan en `.claude/roadmaps/archivo/24-docs-audit-followups.md` (roadmap
archivado — ambas tareas cerradas). Surgido de una
auditoría completa de la documentación del proyecto: se corrigieron ya los
hallazgos "rompe confianza"/"desactualizado" (roadmap 23, `docs/ci-cd.md`,
`Roadmap-212-Ideas-Futuras.md`, `Validacion-STORAGE-MGR.md`) y se archivaron
`Día56`/`Día57`, `Roadmap-DEVPROFILE-1-4/5-6.md` y `docs/Feedback/29/8.md`.
Quedan 2 puntos cosméticos que requerían una decisión de convención en vez
de solo corregir un dato:

| ID | Task | Esfuerzo | Estado |
|----|------|----------|--------|
| DOCS-AUDIT-1a | Decidir convención de archivo para informes puntuales sueltos en `Tareas/` (`zip-route-identificacion.md`, `psx-cue-rotos-2026-08-30.md`) — ¿carpeta `Tareas/archivo/` nueva, o nota de cierre en cabecera igual que `Validacion-STORAGE-MGR.md`? Aplicar retroactivamente y documentar en regla 5 de `.claude/roadmaps/INDEX.md` | XS | ✅ hecho (2026-09-28) — decisión del usuario: nota de cierre en cabecera, sin carpeta nueva. Aplicada a los 2 archivos existentes (`zip-route-identificacion.md`, `psx-cue-rotos-2026-08-30.md`) y documentada en la regla 5 de `.claude/roadmaps/INDEX.md` |
| DOCS-AUDIT-1b | Actualizar 8 comentarios de código que citan la ruta vieja de `Roadmap-DEVPROFILE-1-4.md`/`-5-6.md` (movidos a `Tareas/diario/archivo/*-completado.md` el 2026-09-20) — `esde/systems_generator.py:28`, `detection/platform_detector.py:70`, `detection/platforms.toml:242`, `web/handlers/system.py:493,583`, `services/device_profile.py:137`, `services/path_tokenizer.py:8`, `services/retroarch_cfg_writer.py:5` | XS | ✅ hecho (2026-09-24) — 8/8 comentarios apuntan ahora a `Tareas/diario/archivo/Roadmap-DEVPROFILE-{1-4,5-6}-completado.md`; 1451 tests + ruff limpios |

### SUBPROCESS-WINDOW-1 — Todas las llamadas a herramientas externas abrían una consola visible en modo headless (hallazgo usuario 2026-09-19, PC2)

Encontrado en vivo justo al activar el auto-arranque de `rommgr serve --tray`
vía tarea programada de Windows (`pythonw.exe`, sin consola propia, ver
`EMU-SYNC-WATCH-1` en Pilar 3). El usuario reportó una ventana abriéndose
cada 10 segundos.

**Primer intento insuficiente**: se arregló solo `tasklist.exe` (el watcher
nuevo de `EMU-SYNC-WATCH-1`) — el usuario confirmó que la ventana seguía
apareciendo. **Causa raíz real**: `adb.exe`/`rclone.exe`/`chdman.exe`/
`maxcso`/`netsh` se lanzaban sin `creationflags=CREATE_NO_WINDOW` en absolutamente
ningún sitio del proyecto excepto `utils/notifier.py` — nunca se notó porque
la app siempre se había ejecutado con una consola visible (`python.exe`); con
`pythonw.exe` (sin consola), cada llamada de los daemons periódicos (auto-sync
cada 10s, SD-card cada 8s, verify chd semanal...) abría una consola nueva y
visible para el proceso hijo.

**Segundo problema, esta vez en CI**: `subprocess.CREATE_NO_WINDOW` no existe
fuera de Windows — referenciarlo directamente tumbó 30+ tests en el CI (Linux)
con `AttributeError` antes de que el mock de `subprocess.run` llegara a
ejecutarse. Arreglado con una constante compartida nueva,
`utils/subprocess_flags.py::NO_WINDOW` (el flag real en `win32`, `0` en
cualquier otra plataforma — `0` es el valor por defecto de `creationflags`,
nunca lanza en POSIX) | `web/daemons.py`, `sync/adb_transport.py` (×2),
`sync/device_detector.py`, `sync/rclone_transport.py`, `converters/chd_converter.py`
(×2), `retroachievements/ra_cd_image.py`, `utils/health_checker.py`,
`utils/notifier.py`, `web/handlers/esde/conversions.py`, `web/lan.py`,
`web/handlers/cloud_auth.py` (×4), `utils/subprocess_flags.py` (nuevo) |
✅ mergeado a `develop` (PR #324, 2026-09-19) en 3 iteraciones — 1358 tests
totales, verificado en vivo por el usuario tras cada iteración. Deliberadamente
sin tocar: `games.py` (lanza RetroArch para jugar, su ventana debe verse) y
el `CREATE_NEW_CONSOLE` de `sync_cloud.py` (abre a propósito una consola
interactiva para `rclone config`) |

### RETROARCH-THUMBS-1 — Publicar carátulas/capturas ya escaneadas en el árbol `thumbnails/` de RetroArch (petición usuario 2026-09-19, PC2)

Petición del usuario: que RetroArch, ES-DE y la propia app usen las mismas
imágenes ya scrapeadas sin duplicarlas. Investigación previa en
`docs/config/retroarch-thumbnails.md` confirmó que ES-DE y la app ya
comparten un único archivo por juego (`media/images|screenshots/` junto al
ROM, referenciado directamente en `box_art_path`/`screenshot_path` de
`game_metadata`) — cero duplicación ahí. RetroArch es el caso distinto: solo
lee `<RetroArch>/thumbnails/<db_name>/Named_Boxarts|Named_Snaps/<label>.png`,
solo acepta PNG, y no conoce la carpeta `media/` de ES-DE en absoluto.

Implementado `utils/retroarch_thumbnails.py::publish_retroarch_thumbnails()`:
origen ya PNG → enlace duro al árbol de RetroArch (mismo inodo, 0 bytes
duplicados, un rescrape que sobreescribe el origen mantiene el enlace
sincronizado); origen JPG (RetroArch lo rechaza) → conversión única vía
PowerShell + `System.Drawing` a una caché por mtime
(`.rommgr/retroarch_thumbnails_cache/`), evitando duplicar trabajo en cada
corrida aunque no evita el archivo PNG adicional que RetroArch exige. Corre
como job en background (patrón `convert_chd`) — a escala real, las
conversiones JPG→PNG tardan minutos y una llamada síncrona habría podido
retrasar el watcher de sync (Pilar 3). Botón "Publicar carátulas en
RetroArch" en la pestaña Formatos | `utils/retroarch_thumbnails.py` (nuevo),
`utils/lpl_generator.py` (`_platform_db_name` → `platform_db_name`, pública
al reutilizarse desde dos módulos), `web/handlers/esde/reports.py`
(`POST /api/publish-retroarch-thumbnails`, `GET
/api/publish-retroarch-thumbnails-status`), `web/jobs/manager.py`
(`JOB_NAMES`), `web/static/js/tabs/tools.js` + `tab-formats.html` | ✅
implementado y verificado en vivo contra la biblioteca real de esta máquina
(938 juegos con media escaneada) — 9 tests nuevos, 1367 tests totales.
Hallazgo de la verificación en vivo: el primer intento de conversión falló
en masa por `PATH` restringido del proceso de pruebas (no del código real),
documentado en `docs/config/retroarch-thumbnails.md`. Pendiente sin ID
propio: publicar también `generate_lpl_playlists()` a
`<RetroArch>/playlists/` (hoy solo escribe a `.rommgr/playlists/`, fuera de
alcance de esta tarea) |

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

### CHDMAN-TEST-COMPRESS-1 — `chdman.exe` local falla comprimiendo CHDs de test sintéticos diminutos (hallazgo 2026-09-06)

Investigado tras bloquear el pre-push hook de `feature/anbernic-pick-5-other-category`
tres sesiones seguidas (Día54, Día55 rondas 1 y 2) con el mismo fallo en
`tests/test_chd_converter.py::test_convert_bin_to_chd_end_to_end`,
`test_convert_directory_apply_picks_up_bare_bins` y
`test_convert_bin_to_chd_rejects_on_ra_hash_mismatch` — siempre dado por
"preexistente, sin relación con el cambio de turno" pero nunca investigado
hasta la raíz.

| ID | Task | Files | Status |
|----|------|-------|--------|
| CHDMAN-TEST-COMPRESS-1 | **Causa raíz confirmada**: los 3 tests comparten la imagen PSX sintética de `_build_psx_image()` (`tests/test_ra_hash_psx.py:53`, 23 sectores / 54.096 bytes — deliberadamente mínima para hashear un solo sector). Reproducido **fuera de Python**, invocando `tools/chdman.exe createcd` directamente sobre el `.cue`/`.bin` sintéticos: `chdman - MAME... 0.251` falla con `Error during compression: Compression error` / `Fatal error occurred: 1` en los 3 codecs por defecto (`cdlz`/`cdzl`/`cdfl`), pero **crea el CHD sin error con `-c none`** (`chdman info` confirma: Hunk Size 19.584 B, 3 hunks, Total Units 24) — es un bug/límite de esta versión de `chdman.exe` comprimiendo discos de un puñado de hunks, no algo en `_run_chdman_createcd()`/`convert_bin_to_chd()` (`converters/chd_converter.py:278-297,399-451`, que ya propaga correctamente el stderr de chdman). **No afecta a la biblioteca real** — ningún juego real tiene un `.bin` de 54 KB, así que el bug nunca se dispara fuera de estos 3 tests | `tests/test_chd_converter.py`, `tests/test_ra_hash_psx.py:53`, `tools/chdman.exe` (v0.251) | ✅ barrido binario a mano (23/24 fallan, 28+ ya funciona) confirmó el umbral real ≈28 sectores; `_build_psx_image()` ahora usa `total_sectors = 64` (margen de sobra) en vez de 23, con relleno de sectores 23..63 (solo header, sin datos — el hash RA solo lee hasta el sector 22, tamaño de EXE declarado 0, así que no afecta a ningún test de hash). Sin tocar `chd_converter.py` ni `_run_chdman_createcd()` — el bug es 100% del binario `chdman.exe` local, el fix vive solo en el fixture de test. Suite completa 1204/1204 en verde (antes 1201/1204, los 3 de siempre fallando) |

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
| GAMECUBE-DISC-BUG-1f | **Hallazgo 2026-08-30, sin arreglar a propósito** — mismo mismatch de nombres que 1d pero en `_DISC_SUBFOLDER_PLATFORMS` (`operation_planner.py:146,150`, layout de subcarpeta por juego): `game.platform.lower() in _DISC_SUBFOLDER_PLATFORMS` (línea 146) nunca coincide para PSX/Saturn reales (`"PlayStation"`/`"Sega Saturn"` ≠ `"psx"`/`"saturn"`) — confirmado en vivo que los PSX de la biblioteca real viven planos (`psx/Juego.chd`, `psx/Juego.cue`), nunca en subcarpeta (`psx/Juego/Juego.cue`) pese a que el código pretende crearla para "disc platforms". Arreglarlo (usar nombres de catálogo también aquí) haría que la próxima vez que se ejecute "Organizar" con PSX/Saturn reales, cientos de archivos empiecen a moverse a subcarpetas por primera vez — cambio de layout grande e intencional, no un bugfix silencioso. Requiere decisión explícita del usuario antes de tocarlo.

**Implementado (2026-09-22, Día69)**: confirmado con el usuario que sí quiere
el cambio de layout. Mismo patrón que `GAMECUBE-DISC-BUG-1d`: nuevo frozenset
separado `_DISC_SUBFOLDER_CATALOG_PLATFORMS` (nombres de catálogo —
`"playstation"`, `"sega saturn"`, `"dreamcast"`, `"wii"`, excluye PS2/GameCube
a propósito, mismo motivo `INBOX-ORPHAN-3`) para el chequeo de `game.platform`
(línea 173 tras el fix); `_DISC_SUBFOLDER_PLATFORMS` (slugs de carpeta —
`"psx"`, `"saturn"`...) se queda tal cual, sigue siendo correcto para el otro
uso en la misma función (detectar si el archivo de origen ya está en una
subcarpeta comparando contra el nombre real de la carpeta padre en disco,
línea 177) — los dos chequeos comparaban dominios distintos (nombre de
catálogo vs. slug de carpeta) contra el mismo set, esa mezcla era la causa
raíz real. 2 tests actualizados (`platform="psx"` → `"PlayStation"`, dato
irreal que "funcionaba" antes solo por la propia colisión del bug) + 1 test
nuevo (`test_real_catalog_platform_name_gets_subfoldered`, PSX y Saturn con
el nombre de catálogo real) — confirmado en rojo contra el código anterior
(`git stash`) y en verde tras el fix. Suite completa: 1432 tests, 0
regresiones. **Efecto real**: la próxima vez que se ejecute "Organizar" (`rommgr
apply`/`plan`) sobre una biblioteca con PSX/Saturn reales, esos juegos
empezarán a moverse de `psx/Juego.chd` a `psx/Juego/Juego.chd` por primera
vez — cambio de layout esperado y confirmado, no un efecto colateral. No
ejecutado contra ninguna biblioteca real todavía (esta sesión fue solo
código + tests) | `planner/operation_planner.py` (`_DISC_SUBFOLDER_CATALOG_PLATFORMS` nuevo, línea 173), `tests/test_operation_planner.py` | ✅ hecho 2026-09-22 — el `apply` real contra una biblioteca PSX/Saturn queda para cuando el usuario decida ejecutar "Organizar" |
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
| ARCADE-RENAME-BUG-1a | **✅ Arreglado 2026-09-04**: `load_mame_xml` encadenaba mal la detección de tag hijo por `root.tag` — `itertools.chain(root.iter("machine"), root.iter("game"))` cubre ambos formatos sin adivinar. Verificado contra el DAT real: `MAME 2003-Plus.dat` pasa de **0 a 4.858 machines cargadas**. Test nuevo `test_load_mame_xml_reads_game_tag_under_mame_root`. 1158/1158 en verde, ruff limpio | `catalog/mame_loader.py:19-49` | ✅ arreglado |
| ARCADE-RENAME-BUG-1b | **✅ Arreglado 2026-09-04** (causa raíz principal): `_match_arcade()` (`catalog/matcher.py:370-388`) devolvía la `description` del DAT (p.ej. "Street Fighter II") como `MatchResult.title` en vez del `stem` corto (`sf2`) — cualquier archivo que pasara por este match se renombraba al título descriptivo, exactamente lo que rompe la carga en MAME/FBNeo. Ahora `title=stem`. Test `test_mame_style_zip_prefers_arcade_over_title_fallback` actualizado para reflejar el comportamiento correcto (antes afirmaba el bug como esperado). **Nota de alcance**: este fix solo previene el problema para contenido NUEVO que todavía conserve su stem corto — no repara retroactivamente los 2.766 ya renombrados (para eso, `ARCADE-RENAME-BUG-1c`, sin tocar, requiere CRC-match + plan + backup sobre la biblioteca real). 1158/1158 en verde, ruff limpio | `catalog/matcher.py:370-388` | ✅ causa raíz arreglada, backfill pendiente (`-1c`) |
| ARCADE-RENAME-BUG-1c | **🟡 Parcialmente ejecutado 2026-09-04** (lote de alta confianza, con confirmación del usuario). Diagnóstico real contra `arcade/` en ambas unidades (~21.600 ZIPs con nombre no-corto, script de sesión: intersección de CRCs de las entradas de cada ZIP contra `load_arcade_crc_index()` para identificar el set único, `load_arcade_manifest()` para medir cobertura): **7.648 ya tenían nombre corto**, **5.218 identificados con candidato único**, de los cuales solo **1.057 con el set COMPLETO** (el resto, 4.161, cobertura parcial — renombrarlos solos no arreglaría la carga, faltan chips). **2.746 sin ningún match de contenido arcade** — muchos con pinta de ser ROMs de consola mal archivadas en `arcade/` (ej. `3ds__Ikki (Japan) (Virtual Console).zip`, `Aladdin (Europe) (AGA).zip`), no arcade con nombre solo descriptivo — sin investigar todavía. **1.280 ambiguos** (el contenido coincide con varios sets a la vez, parent/clone/bootleg comparten chips). De los 1.057 "completos": **648 resultaron duplicados exactos** (SHA1 idéntico a un `.zip` de nombre corto ya existente) → descartados a `_descartados/`. **336 renombrados de verdad** (target nunca existía, sin colisión) → nombre corto aplicado in-place. **73 dejados sin tocar** (colisión de 2+ orígenes proponiendo el mismo nombre destino, o target existente con SHA1 distinto — necesitan mirada caso a caso, no automatizable con este criterio). `rommgr scan` de refresco en ambas `arcade/`: 984 huérfanos limpiados (961 `E:` + 23 `H:`, coincide exacto con 648+336). **Quedan sin abordar**: los 4.161 parciales, 2.746 sin match, 1.280 ambiguos y los 73 casos especiales — cada bucket necesita un criterio distinto, no es una sola tarea de rename | Biblioteca real (`arcade/` en `E:` y `H:`) | 🟡 984/~10.400 procesados (648 descartados, 336 renombrados); 8.187 sin tocar, documentados por bucket |
| ARCADE-RENAME-BUG-1d | **✅ Ya resuelto de rebote 2026-09-04**: el fix de `CATALOG-MATCH-BUG-1` (desambiguación por carpeta real para extensión ambigua, mergeado hoy en PR #289) cubre exactamente este caso. Verificado contra la BD real: `E:\Carpetas anbernic\arcade\Outzone (Europe).zip` y `H:\ROMs\arcade\Silkworm (Europe).zip` ya resuelven `platform='Arcade'` (antes `'Amiga'`/`'Atari ST'`). Filas viejas en `inbox/Unknown` (staging, no la carpeta real) siguen con el valor stale porque son filas de BD sin re-escanear, no bug de código | `catalog/matcher.py:298-314` | ✅ resuelto por `CATALOG-MATCH-BUG-1` (PR #289), sin código nuevo necesario |
| ARCADE-RENAME-BUG-1e | Separar `arcade`/`cps1/2/3`/`neogeo` en `emulator_options.json` de iiSU por core real (FBNeo vs MAME 2003-Plus) en vez de forzar FBNeo para todo — solo tiene sentido después de 1b/1c, para los 44 sets confirmados solo-MAME | Config del dispositivo (iiSU) | 🔴 pendiente, depende de 1b/1c |
| ARCADE-RENAME-BUG-1f | **✅ Re-medido y aplicado 2026-09-20**, tras `MATCH-ARCADE-DAT-1` (catálogo FBNeo real 4.858→10.212 entradas). Las unidades originales `E:`/`H:` de `-1c` ya no existen tal cual en esta máquina; la Anbernic (RG556006101273) sigue conectada por **ADB** (no como unidad de Windows) — diagnóstico corrido en real contra `/storage/521D-04EA/ROMs/arcade/` (incluye subcarpetas `mame/` y `fbneo/`, 10.021 ZIPs) vía script `adb shell` (`unzip -v` por archivo, solo lectura, sin pull) + mismo criterio de intersección de CRCs que `-1c`. Resultado: **7.924 ya con nombre corto** (79%), **1.792 sin ningún match** (a investigar aparte, algunos con pinta de sub-placas mahjong/BIOS por prefijo `mag_`/`mf_`), **223 parciales** (faltan chips, no renombrables solos), **70 candidatos únicos y completos**, **12 ambiguos** (CRCs compartidos entre variantes clon/bootleg — mismo patrón que `-1c`). **Aplicado con confirmación del usuario**: los 70 renombrados vía `adb shell mv` (script generado con verificación de colisión `[ -e destino ]` antes de mover) — **67 renombrados**, **3 con colisión real dejados intactos** (`emeraldaja.zip`, `TwinBee (Japan)...zip`, `Batman (Europe)...zip` — el nombre corto destino ya existía, contenido no verificado, requieren mirada caso a caso). **Nota histórica**: el hallazgo original de `-1c` citaba FBNeo con "8.136 machines" en 2026-09-04 — contradice el catálogo roto (0 entradas) encontrado al inicio de la sesión de hoy; el `.dat` bueno debió sustituirse por el formato ClrMamePro-texto-plano en algún punto entre ambas fechas, sin detectarse por falta de un chequeo de cuenta de entradas. **Pendiente**: los 1.792 sin match, 223 parciales y 12 ambiguos — mismo criterio que `-1c`, cada bucket necesita trato distinto | `.claude/roadmaps` n/a — script de sesión (no productizado), mismas funciones `catalog/mame_loader.py` (`load_arcade_crc_index`, `load_arcade_manifest`) | ✅ re-medido con catálogo arreglado; 67/10.021 renombrados en el dispositivo real; resto documentado por bucket |
| ARCADE-RENAME-BUG-1g | **Verificado en vivo 2026-09-27, en la propia UI de Daijishō (RG556 conectada): el nombrado corto está bien — lo que falla es la metadata, no el renamer.** Navegado el sistema "Arcade (FinalBurn Neo)" (779 elementos listados) y buscado "metal slug" en el buscador global: todas las entradas FBNEO muestran el `shortName` crudo (`sf2amf5`, `sf2ceuab3`…) con icono placeholder, sin carátula ni título — cero metadata scrapeada. `Arcade (MAME)` mixto: algunas entradas sí tienen título real (`'88 Games`, `'99: The Last War`) pero otras no (`mslug`, `metalb` aparecen igual de crudas que en FBNEO). **Conclusión: no hace falta afinar `rename_rom_with_saves()`/el matcher** — el fix de causa raíz de `-1b` (`title=stem`) ya está en producción y `-1f` confirma ~79-80% de los ZIPs con nombre corto correcto (lo que MAME/FBNeo necesitan para cargar). Lo que se ve mal en pantalla es que **Daijishō no tiene scraper propio de arcade con cobertura completa** — es un hueco de metadata/carátulas, no de nombrado, y el scraper es pilar secundario del proyecto (`vision_core.md`). Sin cambios de código; documentado para no confundir "se ve feo en Daijishō" con "el renamer falla" en sesiones futuras | Dispositivo real (Daijishō UI, búsqueda global) | ✅ verificado — sin fix necesario en el renamer; el hueco real (scraping arcade) queda fuera de alcance salvo que el usuario lo priorice |

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
| LIBRARY-SYNC-STALE-1d | **Verificado 2026-09-08 contra `library_pc.db` real (backup previo en `.rommgr/backup_library_sync_stale_1d_20260908/`)**: resulta que **no hace falta ningún re-match** — los 4 casos GameCube nombrados en `GAMECUBE-DISC-BUG-1e` (`Metal Gear Solid - The Twin Snakes`, `Resident Evil Zero`, `Resident Evil (World) (Proto 1)`, `Resident Evil 4 (World) (GOD)`) y `Shadow Hearts - Covenant` (PS2) **ya tienen hoy `canonical_title` correcto y distinto por disco** en la BD real (`Disc 1`/`Disc 2` bien separados) — igual al que produciría el matcher ya corregido. Comprobado ejecutando `matcher.match()` en vivo sobre las 281 filas de plataformas de riesgo con número de disco en el nombre y comparando contra lo ya guardado: 0 diferencias en GameCube/PS2. No hay evidencia de cuándo se corrigieron estos datos (ningún diario documenta un re-scan explícito desde el merge del fix el 2026-08-30) — probablemente un rescan/rematch posterior de otra tarea (p. ej. `GAMECUBE-DISC-BUG-1b`/`INBOX-ORPHAN-3`) ya los dejó al día como efecto colateral. Sin cambios en la BD (no hizo falta escribir nada). Hallazgo colateral (no aplicado aquí, pertenece a `CATALOG-MATCH-REGION-2`): la misma comparación encontró 13 filas **PSX** con número de disco cuyo `canonical_title` sí cambiaría por la mejora de prefijo de serial — ver esa tarea | `library_pc.db` (verificado, sin escritura) | ✅ verificado 2026-09-08 — nada que reaplicar |

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
| GBA-SAVE-PATH-1c | Corregir `EMULATOR_SAVE_PATHS_DEFAULT["com.explusalpha.GbaEmu"]` (`config.py:107-113`) — la ruta real en esta Anbernic es "junto a las ROMs" (`ROMs/gba/`), no `Android/data/.../EmuEx/GBA/saves` (ese árbol no existe) — mismo patrón que `SAVES-FRAGMENT-8`, revisar si aplica también a GBC/NES/MD.emu (misma familia EmuEx) | `config.py` | ✅ confirmado y corregido 2026-09-06 en hardware real (RG556006101273, ADB ya autorizado tras copiar `AdbWinApi.dll`/`AdbWinUsbApi.dll`) — `pm list packages` confirma las 4 apps instaladas, pero `files/` está completamente vacío en las 4 (nunca han escrito ni un `EmuEx/`), a diferencia de `Snes9xPlus` que sí tiene datos reales. Se extiende el hallazgo a las 4 (no solo GBA): `GbaEmu`/`GbcEmu`/`NesEmu`/`MdEmu` pasan a `adb_required: False` (mismo tratamiento que RetroArch/PPSSPP) — sus saves reales viven junto a las ROMs (`SAVES-FRAGMENT-8`), ya cubiertos por el Cable Sync de carpeta normal; el pull ADB especial por-paquete nunca sincronizó nada real para estos 4. 1 test nuevo (`tests/test_config.py::test_get_adb_sync_sources_excludes_emuex_families_with_no_real_path`) |
| SD-ORPHAN-FOLDERS-1 | **Verificado 2026-09-27, sin acción necesaria — hallazgo del 2026-08-25 (`NGC` vs `gamecube` + 8 carpetas huérfanas en la raíz de la SD) ya no existe.** `find` completo sobre `/storage/521D-04EA/` (raíz, `maxdepth 1`) y búsqueda case-insensitive de `NGC`/`gamecube` en todo el volumen: ninguna de las 9 carpetas (`NGC`, `Game Boy`, `Game Boy Color`, `Game Boy Advance`, `Nintendo DS`, `Atari 2600`, `Master System`, `Famicom Disk System`, `Game Gear`) existe ya ahí — solo queda `ROMs/gamecube/` (21 archivos) en su sitio canónico. Se resolvió de rebote en algún punto entre el 2026-08-25 y hoy (probablemente la reorganización de `E:\RetroVault\`, commit `NATIVE-SAVE-SYNC-1`), sin marcarse en su momento — mismo patrón de checklist desactualizado que ya se corrigió hoy en `docs/emulador-canonico-rg556.md` §7. Sin archivos movidos, sin backup necesario (no había nada que tocar) | `/storage/521D-04EA/` (raíz), `E:\RetroVault\ROMS\gamecube\` | ✅ verificado, checklist puesto al día |
| GBA-SAVE-PATH-1d | **Core VBA Next jubilado en el dispositivo, 2026-09-27** — petición directa del usuario ("los juegos de gba en vba next se pueden jubilar"). Como `GBA-SAVE-PATH-1b` ya había confirmado 2026-08-31 que las 50 partidas de `saves/VBA Next/` están replicadas byte a byte en `saves/gba/` (0 huecos, 0 discrepancias), no hacía falta revisión de progreso — **backup completo primero** (`adb pull` de los 50 `.srm`, 6,96 MB, a `E:\RetroVault\ROMS\_backup_android_cleanup_20260927\vba_next_saves\`), luego movidos (no borrados) a `RetroArch/saves/_jubilado_vba_next_20260927/` en el propio dispositivo — reversible, nada se pierde, la carpeta `VBA Next/` activa queda vacía y se elimina. Nota: el pedido original hablaba de "5 juegos" (`SAVES-FRAGMENT-1`) pero la carpeta real tenía 50 — sin problema porque `-1b` ya había verificado los 50, no solo los 5 | Dispositivo (RG556006101273), `E:\RetroVault\ROMS\_backup_android_cleanup_20260927\vba_next_saves\` | ✅ jubilado y respaldado 2026-09-27 |
| AETHERSX2-SAVE-PATH-1 | Petición del usuario 2026-09-22, sesión de Día68 ("arreglar las rutas para PSX y cualquier emulador que no funcione") — mismo patrón que `GBA-SAVE-PATH-1c`: `EMULATOR_SAVE_PATHS_DEFAULT["xyz.aethersx2.android"]` apuntaba a `Android/data/xyz.aethersx2.android/files/{memcards,sstates}` (carpeta privada, scoped storage — genera los mismos 18 errores "sin permiso de lectura" en cada auto-sync, confirmado en el log de sync desde al menos 2026-09-21). Verificado que existe una copia real y accesible de los mismos datos (mismos nombres `Mcd001.ps2`/`Mcd002.ps2`, mismos `.p2s`) en `/storage/521D-04EA/saves/{memcards,sstates}` — descubierta hoy mismo al investigar `SAVES-FRAGMENT-8b`. Investigados también Dolphin/Dolphin MMJ (`org.dolphinemu.*`) buscando el mismo patrón: **sin alternativa** — ni carpeta pública GC/Wii en la SD, ni `run-as` puede leer su carpeta privada ("package not debuggable") — confirmado que siguen genuinamente bloqueados sin root. Redream (`io.recompiled.redream`) tiene una carpeta `saves/dreamcast/` con 3 `.state1` (extensión distinta a la configurada, `.sav`) — evidencia más débil (solo 3 archivos, formato distinto), no aplicado hoy | `config.py:47-54` (`EMULATOR_SAVE_PATHS_DEFAULT["xyz.aethersx2.android"]`) | ✅ redirigido a la ruta pública de la SD. Suite completa 1430/1430 (3 ambientales), ruff limpio. **Validado en real, mismo día**: servidor reiniciado con el fix cargado, auto-sync disparado solo al detectar el dispositivo — errores **18 → 2** (los 2 restantes son 100% Redream, sin relación con este fix), y ahora sí copia datos reales de AetherSX2 (antes solo lograba los 5 de melonDS). `com.github.stenzek.duckstation` queda con nota aclaratoria (su propia ruta sigue sin ser legible, pero el contenido real ya lo cubre el Cable Sync genérico contra `/storage/521D-04EA/saves`, ver `SAVES-FRAGMENT-8b`) |

---

### LIBRARY-CLEANUP-GAPS-1 — Huecos reales encontrados al limpiar PSX a mano (hallazgo 2026-08-31)

Origen: para que `psx/` cupiera en la Anbernic (`LIBRARY-SYNC-STALE-1b/c`) se
hizo a mano una limpieza de 195 GB → 81 GB reales. La detección de saves
divergentes de GBA (`GBA-SAVE-PATH-1`) ya la hace la app
(`SAVE-CONSOLIDATOR-1`) — lo que no existe es la parte de actuar sobre ello.
Cuatro huecos concretos, ninguno cubierto hoy por ninguna feature existente:

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CHD-CLEANUP-1 | **El hueco más grande (93 GB solo en PSX real).** Tras convertir un `.bin`/`.cue` a `.chd` con `chdman`, el `.bin`/`.cue` original nunca se limpia — se queda para siempre ocupando espacio | Módulo de conversión CHD (buscar dónde vive hoy `chdman createcd`) | ✅ implementado 2026-09-06 — **causa raíz real**: la verificación por hash RA + `delete_source` ya existían en `converters/chd_converter.py` (`_verify_ra_hash`, nunca borra sin confirmar que el `.chd` coincide con el origen — más estricto que el `chdman extractcd` a mano propuesto originalmente) y el checkbox "Eliminar .cue/.bin tras convertir" ya estaba en la UI (`tab-formats.html`), pero el endpoint `POST /api/convert-chd` (`web/handlers/esde/conversions.py`) solo recorría `find_cue_files()` — nunca `find_bare_bin_files()`, que es la forma más común de dump PS1 en esta biblioteca (single-track, sin `.cue` sidecar). Los `.bin` sueltos convertidos desde la UI nunca entraban por ese endpoint, así que el checkbox de borrado jamás se les aplicaba. Fix: el handler ahora recorre también `bare_bins` con `convert_bin_to_chd()`, mismo criterio de verificación y `delete_source`. 3 tests nuevos (`tests/web/test_convert_chd_handler.py`, con `chdman.exe` real) + suite completa 1207/1207 |
| DUP-CROSSFMT-1 | Detección de duplicados no compara entre formatos distintos del mismo juego — un `.zip` que contiene exactamente el mismo disco que ya existe como `.chd` no se detecta hoy (encontrados 41 casos, 13,5 GB, solo comparando título normalizado a mano). Extender `ra_duplicates_service`/`_build_review_queue` para que agrupe también por normalized_title+disco cruzando extensiones, no solo por SHA1 exacto dentro del mismo formato | `services/ra_duplicates_service.py`, `web/builders/duplicates.py` | ✅ implementado en `web/builders/duplicates.py` (`_review_groups_for_repo`) — nuevo `_normalize_title_cross_format()` (a propósito más estrecho que el normalizador fuzzy de `ra_checker`: solo quita la etiqueta de disco vía `strip_disc_tag()` nueva en `utils/disc_tag.py`, conserva región/idioma como tokens — ese normalizador fuzzy completo ya causó una fusión falsa de 18 ediciones regionales de FFVII, documentada en el comentario del union por `canonical_title`). Union nuevo en el Union-Find existente: mismo `(platform, título fuzzy)` **cruzando ≥2 extensiones distintas** (mismo formato ya lo cubre SHA1/título exacto). Razón nueva `"crossfmt"` en el grupo, gateada por el mismo guard `_is_disc_set()` que ya protege la razón `"title"` contra falsos positivos de sets multi-disco. Badge nuevo en `review_copies.js` (`_REASON_LABELS.crossfmt`); sin cambios de flujo — mismo "Aplicar recomendación"/"Copia intencional" que ya usa la razón `"title"` (soft-discard a `_descartados/`, recuperable 30 días). 6 tests nuevos (2 en `tests/test_disc_tag.py` para `strip_disc_tag`, 4 en `tests/test_builders_duplicates.py`: detecta el caso real .zip/.chd, no fusiona regiones distintas, no fusiona un set multi-disco real, no marca "crossfmt" cuando ambos lados son el mismo formato). **Validado contra biblioteca real 2026-09-07** (`F:\Juegos Retro`, la biblioteca real SÍ estaba montada en esta máquina — el diario de Día56 daba por hecho que no, corregido al comprobarlo): llamando a `_build_review_queue` directamente contra `library_pc.db`/`library_android.db` reales (sin UI, sin extensión de Chrome), **2.684 grupos `crossfmt` reales, 17,28 GB** — muy por encima de los 41 casos/13,5 GB estimados a mano, repartidos Game Boy 1.417, NES 982, Game Gear 185, PlayStation 97, GBA 2, PS2 1. La cifra alta se explica en gran parte por un hallazgo colateral real: `F:\Juegos Retro\gb\GB official game ROM complete works\A\` es una subcarpeta que duplica TODO el contenido de `gb\` un nivel más adentro (5.590 archivos, 3,22 GB) — no es un bug de la detección, es basura real de organización (Pilar 1) que la función ahora expone correctamente para que el usuario la limpie desde "Revisar copias". Suite completa 1228/1228 |
| DUP-CROSSFMT-2 | 🔴 **BUG CRÍTICO encontrado 2026-09-08 — `resolve-duplicates`/"Aplicar recomendación" puede descartar un disco real y completo de un set multi-disco, o un `.cue` cuyo `.bin` sigue vivo, dejando el juego roto.** Causa raíz: `_is_disc_set()` (`web/builders/duplicates.py:27-40`) asumía un archivo por número de disco — cuando hay **más de un archivo compartiendo el mismo número** (`.cue`+`.bin`+`.chd` del mismo disco, o una copia en `library_pc.db` y otra en `library_android.db`), `len(set(disc_nums)) == len(disc_nums)` daba `False` y la función interpretaba "esto NO es un set multi-disco" — exactamente al revés. Caso real: grupo `Parasite Eve II (Spain)` recomendaba conservar Disc 1 y descartar Disc 2, ambos reales. Segundo patrón, mismo mecanismo pero sin números de disco: pares `.cue`/`.bin` del mismo disco en la misma carpeta (`Wipeout 3 (Japan)`, `Wild Arms (USA)`, `Rayman (Japan)`) agrupados como "crossfmt" y recomendados para descartar el `.cue` — no es una copia alternativa, es la hoja de pistas que su `.bin` necesita. **Fix 2026-09-08**: `_is_disc_set` ahora exige >1 número de disco *distinto* entre los miembros (no unicidad estricta) — un mismo número repetido en varios archivos (`.cue`+`.bin`+`.chd` del mismo disco) sigue contando como "ese disco", pero ≥2 números distintos activa el guard aunque haya varios archivos por número. Nueva `_is_cue_sibling_bin()` excluye de la unión crossfmt cualquier `.bin` que tenga un `.cue` hermano (mismo directorio, mismo nombre base) — ese `.bin` es el fichero de datos del `.cue`, no un formato independiente. 2 tests nuevos en `tests/test_builders_duplicates.py` (`test_crossfmt_multidisc_with_per_disc_siblings_not_flagged`, `test_crossfmt_cue_bin_sibling_pair_not_flagged`), suite completa 1234/1234 (más 3 fallos preexistentes no relacionados: tests de detección ADB que asumen "sin dispositivo" y en esta máquina hay uno conectado). **Purga `H:` en Android, 2026-09-08**: mismo hallazgo que en `library_pc.db` (filas fantasma de la otra máquina, no montada aquí) — backup en `.rommgr/backup_library_android_before_H_purge_20260908/library_android.db`, purgadas 211 `games` + 302 `saves` + 4158 `assets` con prefijo `H:` (sin filas huérfanas en `game_metadata`/`game_tags`/`file_operations`, verificado antes de borrar). **Re-corrido 2026-09-09** (`DUP-CROSSFMT-1`, solo lectura, `_build_review_queue` en vivo contra `library_pc.db`/`library_android.db` reales): **1.092 grupos `crossfmt`** (antes 2.684, -59%) tras el fix + la reorganización de `ARCADE-DAT-CONTAMINATION-8` + la purga `H:`, 33,68 GB (PlayStation bajó de 97 a 46 tras excluir pares `.cue`/`.bin` hermanos). De esos, solo **70** llevan `crossfmt` como única razón — el resto ya comparte grupo con `title`/`sha1` exacto, así que el fix está descartando correctamente los falsos positivos de sets multi-disco. Seguro aplicar dedup crossfmt real sobre estos grupos | `web/builders/duplicates.py:27-51` (`_is_disc_set`, `_is_cue_sibling_bin`) | ✅ arreglado 2026-09-08, re-validado en vivo 2026-09-09 — 1.092 grupos `crossfmt` reales. ⚠️ **Corrección 2026-09-09**: al intentar aplicar `resolve-duplicates --apply` se encontró que el mismo patrón sobrevive por la unión de `canonical_title` exacto, que no pasa por el guard de este fix — ver `DUP-CROSSFMT-3`. **No ejecutar `--apply` todavía**, ni siquiera sobre estos 1.092 grupos (el comando no distingue por razón) |
| DUP-CROSSFMT-3 | 🔴 **BUG CRÍTICO encontrado 2026-09-09 — el mismo patrón que `DUP-CROSSFMT-2` sobrevive por una ruta distinta que su fix no cubrió.** `_is_cue_sibling_bin()` (`web/builders/duplicates.py:79-90`) solo gatea la unión "crossfmt" (línea 752, dentro del bucle que rellena `crossfmt_groups`) — pero el union-find por `canonical_title` exacto (líneas 738-740, `first_by_title`) no pasa por ese guard en absoluto. Cuando el catálogo matchea tanto el `.cue` como su `.bin` hermano al mismo `canonical_title`, ambos caen en el mismo clúster por esa vía; `has_title_dup` (línea 803-807) sale `True` porque `distinct_sha1 > 1` (contenido distinto) y `_is_disc_set()` da `False` en un juego de un solo disco (sin tag `(Disc N)`). El desempate final (`_review_entry_sort_key`, líneas 180-212) empata en integridad/RA/carpeta/idioma para un `.cue` y su propio `.bin`, y cae al string plano del nombre — `"...bin" < "...cue"` alfabéticamente — así que el `.bin` siempre "gana" y el `.cue` siempre se marca para descartar, dejando el `.bin` huérfano e injugable. **Verificado en vivo** con `rommgr resolve-duplicates` (dry run, sin `--apply`, biblioteca real): de 30 líneas que descartan un `.cue`, **26 son pares hermanos exactos** (mismo nombre base, solo cambia la extensión) — `Wild Arms (USA).bin` se queda, `Wild Arms (USA).cue` se descarta; mismo patrón en `Street Fighter Collection (Europe) (Disc 1)`, `Mortal Kombat 3 (Europe)`, `Dino Crisis (Spain)`, etc. **No se aplicó nada** — parado antes de `--apply` al detectar el patrón, sin tocar archivos. La CLI (`resolve-duplicates --apply`) procesa todas las razones (`title`/`sha1`/`crossfmt`/`ra`) en una sola pasada, así que hoy no hay forma de aplicar solo los 1.092 grupos `crossfmt` seguros de `DUP-CROSSFMT-2` sin arrastrar también estos grupos `title` rotos. **Arreglado 2026-09-09**: el guard `_is_cue_sibling_bin()` ahora se aplica también al bucle que rellena `first_by_sha1`/`first_by_title` (`web/builders/duplicates.py:727-734`, antes del `if row["sha1"]`/`if row["canonical_title"]`) — un `.bin` con `.cue` hermano queda fuera de CUALQUIER unión (sha1, título exacto, crossfmt), no solo la crossfmt. 1 test nuevo (`tests/test_builders_duplicates.py::test_title_union_cue_bin_sibling_pair_not_flagged`, mismo caso Wild Arms (USA) pero forzando la unión por `canonical_title` en vez de por crossfmt). Suite completa 1238/1238 (+3 fallos preexistentes de siempre, RG556 conectada). **Re-verificado en vivo contra la biblioteca real tras el fix**: de los 30 casos originales, **0 quedan con ambos archivos vivos en disco** — 14 eran filas de BD obsoletas (archivo ya no existe en ninguna ruta, `resolve-duplicates --apply` solo limpiaría la fila, sin tocar disco) y el resto ya no se agrupan. **Hallazgo colateral, NO arreglado — ver `DUP-CROSSFMT-4`**: un segundo patrón distinto (el ganador es un `.chd`/región distinta, no el propio hermano) sigue dejando `.bin` huérfanos vivos en 4-5 casos reales (`Twisted Metal 4`, `Guilty Gear`, `Twisted Metal`, `Tekken 3`) | `web/builders/duplicates.py:727-734` (guard aplicado a las 3 uniones), `:79-90` (`_is_cue_sibling_bin`, sin cambios) | ✅ arreglado y testeado 2026-09-09 — el patrón original (hermano recomendado sobre su propio `.cue`) ya no ocurre con archivos reales |
| DUP-CROSSFMT-4B | **Intento de `--apply` filtrado a PlayStation, 2026-09-09**: script ad-hoc (`_build_review_queue` filtrada a `platform == "PlayStation"`, sin tocar el resto de plataformas) encontró **0 grupos "planos" aplicables** — los 5 grupos PSX de la cola son todos `disk`/`collision`, y ese tipo nunca se auto-resuelve en plataformas de `_MULTI_DISC_RISK_PLATFORMS` (por diseño, correcto). De esos 5, uno (`Crash Bandicoot`) resultó ser el hallazgo `CATALOG-MATCH-BUG-2` (bootlegs NES mal etiquetados como `PlayStation`), otro (`Tomb Raider II` Europe/USA) es simple diferencia de región agrupada por `title` — ninguno es un duplicado real aplicable. Conclusión: **no hay nada seguro que aplicar hoy para PSX** con la lógica actual; forzar el `--apply` global tocaría otras plataformas fuera de alcance | script de sesión, no versionado — filtra `queue['groups']` por `platform` antes de llamar a `resolve_duplicate_ra` | 🔵 investigado 2026-09-09, sin cambios de código — nada que aplicar hoy |
| DUP-CROSSFMT-4 | 🔴 **Segundo patrón encontrado al verificar el fix de `DUP-CROSSFMT-3`, distinto y sin arreglar.** Cuando el "ganador" de un grupo `title`/`crossfmt` es un archivo *distinto* del hermano del perdedor (p. ej. un `.chd` de otra región/dump, no el propio `.bin` del `.cue` que se descarta), el `_discard_file` solo mueve el `.cue` perdedor — su `.bin` hermano, que no forma parte del clúster (normalmente porque solo el `.cue` matcheó ese `canonical_title`/`crossfmt` key), se queda vivo y huérfano en la carpeta activa. **4 casos reales confirmados en vivo** (ambos archivos existen en disco hoy, `web/builders/duplicates.py` + `_build_review_queue` reales contra `library_pc.db`): `Twisted Metal 4 (USA) (Rev 1).chd` gana, `Twisted Metal 4 (USA, Canada).cue` se descarta (su `.bin` hermano sigue en `psx/`); mismo patrón con `Guilty Gear (Europe).chd`/`Guilty Gear (USA) (Rev 1).cue`, `Twisted Metal (Europe).chd`/`Twisted Metal (Japan).cue`, `Tekken 3 (Asia) (En) (Pirate).chd`/`Tekken 3 (USA).cue`. Nota aparte, sin relación con este bug: el grupo real de `Guilty Gear (Europe).bin`/`.chd` (`web/builders/duplicates.py`, razón `crossfmt`) muestra **dos filas distintas para el mismo `source_path` `Guilty Gear (Europe).chd` con tamaño/sha1 diferentes** entre `library_pc.db` y `library_android.db` — posible desincronización entre ambas BDs que merece su propio diagnóstico, no mezclar con este hallazgo. **Arreglado 2026-09-09**: `_discard_file` (`services/ra_duplicates_service.py`) ahora, al descartar un `.cue`, parsea sus `FILE` referenciados con `parse_bins_from_cue()` (ya existente, reutilizada de `CHD-CLEANUP-1`/`cleanup-cue-bin`) **antes** de moverlo, y tras el discard del `.cue` descarta también cada `.bin` referenciado que siga en disco — mismo mecanismo (`_discard_file` recursivo), solo en PC (`is_device_path` lo excluye en Android, sin cambio ahí). Best-effort: si falla el discard del `.bin` hermano, se loguea pero no revierte el `.cue` (ya movido con éxito). 2 tests nuevos (`tests/test_ra_duplicates_service.py::test_discard_ra_duplicate_cue_takes_its_sibling_bin_with_it`, `..._without_bin_on_disk_still_succeeds`), suite de duplicados 42/42 | `services/ra_duplicates_service.py::_discard_file` | ✅ arreglado y testeado 2026-09-09 — **no se ha ejecutado todavía `resolve-duplicates --apply` sobre la biblioteca real**, pendiente de decisión del usuario antes de aplicar sobre los grupos PlayStation |
| DUP-CROSSFMT-7 | **Intento de extender el `--apply` a Game Boy/NES/Game Gear/Sega Mega Drive, 2026-09-09.** Cola de duplicados en vivo (`_build_review_queue`, `library_pc.db`/`library_android.db` reales): **2.530 grupos totales**, muy distinto al reparto de `DUP-CROSSFMT-1` (aquella medición fue contra `F:\Juegos Retro`, una biblioteca **distinta**, no la activa `E:\Carpetas anbernic` — no comparable). En las 4 plataformas objetivo: **2.289 grupos** (`Sega Mega Drive` 1.407, `NES` 660, `Game Gear` 194, `Game Boy` 28), de los cuales **2.286 son `disk`/`collision`** (conflictos de plan, no duplicados "planos") y solo **3 son planos** (2 `crossfmt`, 1 `title`, los 3 en Game Gear). Investigado por qué hay tantísimo conflicto `disk`/`collision` en estas plataformas (ninguna es `_MULTI_DISC_RISK_PLATFORMS`, así que si tuvieran RA se auto-resolverían): muestreados 400/2.286 grupos vía `get_ra_achievements_for_path`, **0 con datos de RA en cualquiera de los dos lados** — `apply_ra_conflicts()` los dejaría todos en `skipped_no_ra`, aplicar hoy sería un no-op sobre estos 2.286. Inspección manual de una muestra de grupos Mega Drive confirma que la mayoría no son duplicados simples: mezclan versión oficial + parche de traducción + parche de hack + versión arcade + `.bin`/`.md`/`.zip` del mismo dump, sin ninguna señal automática hoy para distinguir "mismo contenido, contenedor distinto" (seguro) de "contenido genuinamente distinto que comparte título fuzzy" (hack/traducción, inseguro) — bloque de trabajo bastante más grande que "extender el crossfmt ya validado", necesita su propia investigación dedicada, no forzado hoy. **Hallazgo colateral real, confirmado con datos**: de los 3 grupos planos, 2 (`Royal Stone`, `Coca-Cola Kid`, ambos `.gg` vs `.zip` del mismo `.gg`, CRC interno del `.zip` idéntico al `.gg`, verificado) eran duplicados reales — **aplicados** (`.zip` descartado a `_descartados/`). El 3º (`Phantasy Star Adventure`, razón `title`) es un **falso positivo confirmado por SHA1 y tamaño**: `Phantasy Star Adventure (Japan) [T-En by Aeon Genesis v1.00].gg` (parche de traducción al inglés) vs `phantasy star adventure (japan).bin` (el original japonés sin traducir) — mismo tamaño (131072 bytes) pero SHA1 distinto, contenido real diferente. **No aplicado** — la recomendación del sistema marcaba el `.gg` traducido como "conservar" y el `.bin` original como descartable, lo que habría perdido la versión sin traducir. Causa raíz: `normalize_for_match()` (`detection/filename_normalizer.py:24-49`, paso 2 "Remove annotations") quita **cualquier** anotación entre corchetes/paréntesis sin distinguir región de parche de traducción — `[T-En by Aeon Genesis v1.00]` se borra igual que `(Japan)`, así que ambos ficheros colapsan al mismo `canonical_title`/clave de título vía el fallback de `CatalogMatcher._match_by_title()`, y `_build_review_queue()` los agrupa como si fueran copias del mismo juego. Alcance no medido (cuántos grupos más de la biblioteca mezclan traducción/original vía este mecanismo) — solo se encontró este caso al verificar los 3 grupos planos de Game Gear, no una búsqueda dedicada | `detection/filename_normalizer.py:24-49` (`normalize_for_match`, paso 2) | 🔵 2 aplicados (verificados con CRC interno), 1 detectado y bloqueado (falso positivo traducción/original), 2.286 conflictos `disk`/`collision` investigados y confirmados no-aplicables hoy (0% cobertura RA) — sin tocar código, alcance completo del bug de traducción sin medir |
| DUP-CROSSFMT-8 | **Investigación pedida por el usuario 2026-09-09 sobre los 1.407 grupos de conflicto Mega Drive de `DUP-CROSSFMT-7` — categorizados y 772 aplicados.** Usando el `sha1` ya guardado por fila en la BD (sin re-hashear) para las entradas en formato crudo (`.bin`/`.md`/`.gen`/`.smd`) más verificación de CRC interno para cualquier `.zip` del grupo (misma técnica que `ARCADE-DAT-CONTAMINATION-12`): **772 grupos (55%) verificados al 100%** como el mismo contenido real en todas sus entradas — aplicados con `resolve_duplicate_ra` usando la entrada `recommended` ya calculada por `_build_review_queue` como la que se conserva (backup previo de `library_pc.db` en `.rommgr/backup_megadrive_dupcrossfmt7_20260909/`). **773 archivos descartados** (algunos grupos tenían 3-4 copias idénticas), 0 errores. Re-consulta tras aplicar: **635 grupos restantes** (1.407 − 772), cuadra exacto. Resto categorizado sin tocar: **590 con tag hack/traducción/beta/proto** (regex sobre el nombre: `hack`, `trad`, `t-en`, `spanish`, `voice`, `beta`, `proto`, `unl`, `pirate`, `patch`... — 470 son pares limpios "oficial+hack" sin nada que fusionar, pero **70 sí tienen un sub-duplicado real entre las entradas NO-hackeadas** que necesitaría resolución por entrada, no por grupo — `resolve_duplicate_ra` descarta TODO lo no-recomendado, tocaría el hack); **40 con sha1 crudo genuinamente distinto** (variante/revisión real, no duplicado); 3 con una entrada que no verifica por CRC (posible versión distinta colada, ej. `Klax (version 6).zip`); 1 cruce arcade (`G-LOC`); 1 sin clasificar. NES/Game Boy/Game Gear (el resto de plataformas objetivo de `DUP-CROSSFMT-7`, 858 grupos de conflicto) sin categorizar todavía con este método | script de sesión, no versionado (misma lógica que `apply_megadrive_safe.py`, reutilizable para el resto de plataformas) | ✅ 772/1.407 aplicados y verificados; ✅ **resolución por entrada hecha 2026-09-09** (tras mergear `CATALOG-MATCH-VARIANT-1`/`CATALOG-MATCH-BUG-2`, backup en `.rommgr/backup_megadrive_subdup_20260909/`): de los 418 conflictos que quedaban tras el fix, **356 tenían un sub-duplicado verificable (sha1 crudo/CRC interno) entre sus entradas NO marcadas como variante** — resueltos por entrada (conserva la primera de cada cluster de contenido idéntico ya ordenada por `_review_entry_sort_key`, descarta el resto del cluster, nunca toca la entrada hack/traducción del mismo grupo). **367 archivos descartados, 0 errores**. Re-consulta: Mega Drive pasó de 418 a **67 conflictos** (+53 planos nuevos, ninguno con sha1 crudo idéntico entre pares — diferencia real de dump/cabecera, no verificable con la técnica actual, dejados para otra sesión). Script de sesión reutilizable, mismo patrón que el resto de aplicaciones de hoy | 🔴 NES/Game Boy/Game Gear (495/26/178 conflictos) sin la misma pasada de resolución por entrada — mismo patrón esperable, no hecho todavía |
| DUP-CROSSFMT-10 | 🔴 **BUG encontrado 2026-09-22, objetivo 7 de Día68**: al revisar la cola de duplicados solo-dispositivo (`/api/review-queue`, `library_android.db` real, 96 grupos tras `DUP-DISC-SET-2`/`DUP-DISC-TRACK-1`) para continuar `ANDROID-DUP-2-APPLY-1`, los 12 grupos con `platform="unknown"` resultaron ser **chips de ROM arcade sueltos (MAME), no duplicados** — p. ej. `ggw.01`/`ggw.05`/`ggw.11m`/`ggw.12m`... (7 chips de un mismo set arcade, cada uno con SHA1 distinto = contenido real distinto), agrupados como si fueran el mismo juego en formatos distintos y con "descartar todos menos uno" recomendado. Causa raíz: `web/builders/duplicates.py:973-976` — `stem = Path(original_filename).stem` corta en el ÚLTIMO punto, así que `ggw.01`/`ggw.05` colapsan al mismo `cf_title="ggw"` vía `normalize_title_cross_format()`; la comprobación de `len(exts) >= 2` en la línea 980 no filtra el caso porque cada chip SÍ tiene una "extensión" distinta (`.01`, `.05`, `.11m`...) aunque en realidad sea parte del nombre del chip, no un formato de contenedor. Mismo patrón de fondo que `NULL-PLATFORM-1` (estos archivos ya se sabía que quedan con `platform=NULL`/`canonical_title=NULL` por vivir en `Unknown/`) pero nunca se había verificado que la cola de duplicados los agrupe mal — `_is_disc_set()` no protege este caso porque no hay patrón `(Disc N)`, solo protege sets multi-disco reales. **No aplicado nada de estos 12 grupos** — excluidos a mano de la revisión de hoy (`platform != "unknown"` como filtro). Alcance no medido más allá de estos 12 (cuántos grupos así hay en el resto de la biblioteca PC, ~1829 grupos combinados sin revisar) | `web/builders/duplicates.py:973-976` (`crossfmt_groups`, construcción de `cf_title`/`exts`) | ✅ **arreglado 2026-09-22, misma sesión**: nueva constante `_CROSSFMT_CONTAINER_EXTS` (allowlist de extensiones reales de disco/ROM — `.zip`, `.chd`, `.bin`, `.cue`, `.img`, `.ccd`, `.sub`, `.mdf`, `.mds`, `.gdi`, `.cdi`, `.iso`, `.nrg`, `.cso`) — el union crossfmt ahora exige que **todas** las "extensiones" del grupo pertenezcan a esa lista antes de comprobar `len(exts) >= 2`, así que un chip MAME (`.01`, `.u32`, `.ic3`...) nunca puede satisfacer la condición aunque su stem colisione. 1 test nuevo (`test_crossfmt_mame_split_rom_chips_not_flagged`), confirmado en rojo contra el código anterior (`git stash`) y en verde con el fix. Suite completa 1430/1430 (3 fallos ambientales preexistentes, dispositivo ADB conectado), ruff limpio. **Alcance medido en el resto de la biblioteca, misma sesión**: `_build_review_queue` en vivo contra `library_pc.db`/`library_android.db` reales (solo lectura) — de los 1.828 grupos solo-PC, 14 tienen `platform=unknown`, pero **ninguno con `crossfmt` como única razón** (todos `collision`/`title`/`region` — variantes reales de ROM `.zip`, no chips MAME). El bug no tenía alcance práctico fuera del dispositivo — los 12 grupos ya encontrados eran el 100% del impacto real |
| DUP-SHA1-JUNK-1 | 🔴 **Hallazgo 2026-09-22, mismo repaso que `DUP-CROSSFMT-10`**: grupo `sha1` en la cola de duplicados solo-dispositivo agrupa 3 archivos de 37.396.800 bytes con el mismo SHA1 pero **3 nombres/ubicaciones sin relación real** — `/storage/521D-04EA/ROMs/psx/Enemy Engaged - Apache-Havoc (Italy) (Rerelease) (1998-12-08).bin`, `/storage/521D-04EA/ROMs/psx/Darkstalkers - The Night Warriors (Europe)/Ninpuu Sentai Hurricanger & Kamen Rider Ryuuki (Japan) (2-dai Hero Special Disc Taikenban).bin` (nótese: dentro de la carpeta de OTRO juego) y una tercera copia suelta del mismo nombre directamente en `psx/`. 37,4 MB es demasiado pequeño para un disco PSX completo (~400-700 MB) — no parecen discos reales, más bien restos corruptos/truncados o contenido placeholder que coincide por casualidad (o por corrupción idéntica) entre 3 nombres de juegos distintos. La recomendación automática marca "conservar Enemy Engaged, descartar los 2 Ninpuu Sentai" basándose solo en SHA1 igual, sin verificar si alguno de los 3 es en realidad el disco real de su juego correspondiente truncado a este tamaño (en cuyo caso ninguno de los 3 sirve como sustituto de los otros dos). **Investigado a fondo 2026-09-22 (misma sesión)**: consultado `library_pc.db`/`library_android.db` — ni "Ninpuu Sentai" ni "Enemy Engaged" tienen ninguna otra entrada en ninguna de las dos bibliotecas (0 filas), así que no hay una copia completa real con la que comparar. El archivo `Enemy Engaged...bin` se descargó del dispositivo (`adb pull`) y se inspeccionó byte a byte: **37.396.800 bytes, el 100% son `0x00`** — 0 bytes distintos de cero en toda la muestra (primer MB, sectores intermedios, últimos 64 bytes), 0 coincidencias del patrón de sincronización de sector CD-ROM. **No son discos reales ni contenido corrupto de un juego — son 3 archivos placeholder completamente vacíos** (probablemente de una copia/dump interrumpida que reservó el archivo sin escribir datos), coincidiendo por SHA1 solo porque "todo ceros del mismo tamaño" siempre da el mismo hash. `Darkstalkers - The Night Warriors (Europe)/` (la carpeta donde vive una de las copias) es un set completo y correcto por sí mismo (`.cue`+45 `.bin` de pista, Track 01-45 completas) — el archivo intruso no pertenece al set, es basura suelta sin relación. **Seguro borrar las 3 copias** — no hay pérdida de datos real, cero contenido útil en ninguna | `library_android.db` (`games`, grupo sha1 `d9f92af296360772e62caa4cb276de3fa74f5538`), dispositivo real (3 rutas listadas arriba) | ✅ **borrado 2026-09-22, misma sesión** (confirmado por el usuario): backup previo de `library_android.db` (`.rommgr/library_android.db.bak_junk_20260922_152556`), `adb shell rm` de los 3 archivos (verificado con `find` tras borrar, 0 resultados), 3 filas correspondientes borradas de `games`. ~112 MB liberados en la Anbernic, 0 pérdida real |
| DUP-CROSSFMT-9 | **Continuación de `DUP-CROSSFMT-8` a NES/Game Boy/Game Gear, 2026-09-09.** Misma metodología (sha1 crudo + CRC interno de zip) aplicada a los 660+28+191=879 grupos de conflicto restantes de esas 3 plataformas. **168 verificados al 100% y aplicados** (NES 156, Game Boy 1, Game Gear 11; backup previo en `.rommgr/backup_nes_gb_gg_dupcrossfmt9_20260909/`) — **263 archivos descartados, 0 errores**. Re-consulta: NES 504 restantes (660−156), Game Boy 27 (28−1), Game Gear 180 (191−11), cuadra exacto. **Cobertura mucho menor que Mega Drive (55%) — solo 19% de estas 3 juntas** porque el resto es mucho más "sucio": dos hallazgos nuevos que explican por qué. **(1) NES, 391 grupos con sha1 crudo genuinamente distinto**: el regex de detección de hack/traducción de la sesión (`hack|trad|translat|t-en|t\+eng|t-esp|t-spa|spanish|voice|beta|proto|...`) solo cazaba una fracción — inspección manual confirma que **96/391 llevan tag `[T+xxx]`/`[T-xxx]` de traducción con código de idioma de 2-3 letras que el regex no cubría** (`Bra`, `Dut`, `Fre`, `Gre`, `Pol`, `Swe`, `Nor`, `Ar`, `ES`, `ita`, `Irish`, `Romanian`, `Rus`... decenas de idiomas distintos, convención estándar de romhacking.net) — un solo juego (`Legend of Zelda`) tiene **22 variantes de traducción** agrupadas como "conflicto" entre sí. Los otros 295 son región/revisión `(PRG0)`/`(PRG1)`/`(CHR0)`/`(CHR1)` genuinamente distintas o hacks/subsets sin tag reconocible (`[Subset - Item Drops]`). Esto **confirma y amplía a mucha mayor escala** el bug de `normalize_for_match()` ya documentado en `DUP-CROSSFMT-7` (colapsa cualquier anotación entre corchetes, traducción incluida, a la misma clave de título) — aquí no es 1 caso aislado, son cientos de grupos NES enteros construidos sobre ese fallo. **(2) Game Boy, grupo "Asterix" real**: mezcla el juego real de Game Boy (`Asterix (Europe)...gb`, 131.072 bytes) con el juego de **arcade** "Asterix" de Konami (`arcade\Asterix (ver EAD).zip`, `arcade\asterix.zip`, 3.669.047 bytes, mismo sha1 en 4 copias) — mismo mecanismo de colisión de título fuzzy que `CATALOG-MATCH-BUG-2`, esta vez cruzando Game Boy↔Arcade en vez de NES↔PlayStation. **Hallazgo colateral, sin relación con dedup**: ese mismo grupo revela restos sin procesar en `E:\Carpetas anbernic\inbox\arcade\`, `inbox\mame_20240311\MAME\`, `inbox\fbneo_1003_bestset\games\fbneo\` — contenido de Inbox (Pilar 2) que nunca se organizó, mismo patrón que `ARCADE-DAT-CONTAMINATION-8`/`Unknown\` pero en otra carpeta, sin auditar todavía | `detection/filename_normalizer.py:24-49` (`normalize_for_match`, mismo hallazgo que `DUP-CROSSFMT-7` pero con alcance medido en NES), script de sesión no versionado | ✅ 168/879 aplicados y verificados (0 restantes de esa categoría); ✅ **causa raíz arreglada 2026-09-09** (rama `fix/catalog-match-noncanonical-variants`, ver `CATALOG-MATCH-VARIANT-1` — nuevo `is_non_canonical_variant()`, aplicado en `catalog/matcher.py` (deja de asignar canonical_title mal por debilidad, indirectamente), `web/builders/duplicates.py` (excluye la unión por título/crossfmt) y, causa real del "collision", `planner/operation_planner.py::_canonical_filename()` (ya no calcula el mismo target para el parche y el original)); ✅ **re-corrido tras mergear el fix, mismo día**: la cola bajó de 711 a 622 grupos de conflicto (Mega Drive 635→418, NES 504→495, Game Boy 27→26, Game Gear 180→178) y aparecieron **111 grupos "planos" nuevos** — duplicados reales que antes quedaban enterrados detrás del falso conflicto de renombrado. De esos, **87 verificados al 100% por sha1 crudo + CRC interno de zip y aplicados** (backup previo en `.rommgr/backup_postfix_plain_groups_20260909/`), 24 correctamente descartados (17 con contenido crudo realmente distinto, 7 con una entrada extra que no verificó) — 0 errores. Confirma que el fix funciona en datos reales: gran parte del ruido de "colisión" era exactamente el bug arreglado; 🔵 `E:\Carpetas anbernic\inbox\` con restos sin auditar, hallazgo nuevo sin ID propio |
| INBOX-STALE-1 | **Auditoría inicial 2026-09-09 (solo lectura, sin tocar el disco mientras corría un Cable Sync en paralelo) del Inbox sin procesar encontrado hoy al investigar `DUP-CROSSFMT-9`.** `E:\Carpetas anbernic\inbox\` tiene **44.611 archivos físicos, 185 GB**, de los que solo **450 (1%, 1,4 GB) están indexados en `library_pc.db`** — el resto nunca pasó por ningún paso del pipeline (mismo patrón que `Unknown\` antes de `ARCADE-DAT-CONTAMINATION-8`, pero sin auditar todavía). 35 carpetas de primer nivel, mezcla heterogénea: **colecciones bulk sin organizar** (`mame_20240311`, `fbneo_1003_bestset`, `retro-roms-best-set` — mismos nombres que aparecieron en el hallazgo de `DUP-CROSSFMT-9`/Asterix); **carpetas ya organizadas por plataforma al estilo No-Intro pero nunca movidas a su sitio** (`Nintendo - DS`, `Nintendo - Game Boy`, `Nintendo - Game Boy Advance`, `Nintendo - Game Boy Color`, `Nintendo - NES`, `NES-Famicom`, `sg1000`, `ngp`, `arcade`, `megadrive`, `gamegear`); **residuo de investigaciones pasadas** (una docena de carpetas nombradas por juego individual con su propia `_descartados/`, ej. `Ashura (Japan) (SMS) (Virtual Console)`, `Grobda (Japan) (Arcade) (Virtual Console)` — mismo patrón que `ARCADE-DAT-CONTAMINATION` de sesiones anteriores); **contenido claramente ajeno al retro** (`Prince of Persia The Two Thrones [PAL]...` — un juego PS2/PSP moderno, no debería estar en ningún inbox de ROMs retro); y una carpeta `media\` (probablemente artwork de scraper, no ROMs). Los 450 ya indexados se repartieron: MAME 309, Arcade 48, NES 34, Amiga 15, Atari 2600 11, Commodore 64 11, resto <10 c/u. **No se corrió `organize-source` (ni dry-run)** — el disco `E:` estaba bajo carga por un Cable Sync ADB en curso en paralelo, evitado a propósito para no competir por I/O con una operación de mayor prioridad (Pilar 3) | `E:\Carpetas anbernic\inbox\` | ✅ **verificado resuelto 2026-09-20** — la Anbernic ya no monta como unidad de Windows en esta máquina (conectada por ADB, ver `ARCADE-RENAME-BUG-1f`); comprobado el `inbox/` real del dispositivo (`/storage/521D-04EA/inbox`, misma SD) y está **completamente vacío** (0 archivos, 768K). Se limpió en algún punto fuera de lo documentado en este backlog — no hay evidencia de cuándo ni por qué mecanismo. Sin acción pendiente |
| INBOX-STALE-2 | **Revisión pedida por el usuario 2026-09-20 ("revisa el inbox")** del inbox real de esta máquina, `F:\Juegos Retro\inbox\` (3.014 archivos, 605 MB) — distinto del de `INBOX-STALE-1` (ese era el de la Anbernic, ya vacío). Mezcla de un pack antiguo (fechas Jun-2025) con ROMs + un volcado completo de emuladores/frontend (MAME32, DeSmuME, VBA-M, ZSNES, Kaillera, iconos `.ico` de un pack de 2.586 archivos, `.dat`/`.chm`/`.ini`/`.cfg` de soporte, APKs de emuladores Android) — nada de esto es ROM/save/asset de plataforma. **Dry-run `organize-source`**: 52 ROMs detectados (48 NES + 4 Game Boy). **Aplicado**: solo **1 se organizó limpio** (sin colisión) — **51 tienen el mismo nombre que un archivo ya existente en su carpeta de plataforma real (`gb`/`nes`) pero con SHA1 distinto** (verificado a mano en 4 muestras: `Bubble Bobble (Japan).gb`, `Lemmings (Europe).gb`, `Parodius (Europe).nes` mismo tamaño/SHA1 distinto; `Hebereke (Japan).nes` tamaño distinto 262.160 vs 393.232) — el pipeline correctamente no los tocó (`INBOX-FIX-*`/regla del proyecto "ante duda no sobreescribir"), quedan en el inbox para revisión manual, **sin decisión tomada sobre si son hacks/revisiones legítimas o el pack antiguo es simplemente peor que la biblioteca actual**. 2 ROMs más (`Aleste - Full Metal Fighter Ellinor (J) [!].smd`, `NHL93.SMD`) **no fueron detectados por `organize-source`** porque `.smd` no está en `PLATFORM_BY_EXTENSION` (`detection/platform_detector.py`) — hallazgo nuevo, gap de formato real para Mega Drive; verificado a mano que ambos son probablemente el mismo contenido que ya existe en `megadrive/` bajo otro nombre/formato (`Aleste...bin` ya existe, SHA1 distinto pero mismo tamaño; `NHL93.SMD` es 512 bytes más grande que `NHLPA Hockey 93 (USA, Europe).md` — diferencia típica del header de formato `.smd` interleaved). **Basura no-gaming borrada** (con lista explícita de nombres revisados uno a uno, no un borrado por extensión ciego): 2.586 `.ico`, 42 fragmentos de chip arcade sueltos (`.ic27`/`.ic31`/`.mrom1-4`/`.fmem1`/`.4x`/`.6x`/`.2f`), 48 archivos de soporte de emulador (instaladores `.exe`, APKs, `.cfg`/`.ini` de frontend, `.dat`/`.chm`/`.ddb`/`.inf`/`.lst`/`.mo` de MAME/DeSmuME/Kega, documentación `README`/`COPYING`/`AUTHORS`/`ChangeLog`) — inbox pasa de 605 MB a 69 MB. **Dejados sin tocar a propósito, requieren decisión separada** (no son basura, son casos ambiguos): `dcnaodev.bios` (parece BIOS real de Naomi/Dreamcast — las BIOS nunca se tratan como basura ni como ROM, regla del proyecto), `sfa3.hi`/`sfz3a.hi`/`sfz3j.hi` (`.hi` es una extensión de save reconocida por el propio proyecto, aunque aquí parecen ser hi-scores de MAME de fábrica, no partidas reales), `Sonic 2 - Sonic 2 Adventure Edition (v2.0) (MainMemory).bps` (parche de ROM hack, contenido deseable para quien hackea ROMs, no basura), `zukinver0930.ipl` (propósito no identificado). **Hallazgo aparte, no relacionado con ROMs**: `Menu_semanal_desde_martes.docx` — documento personal (menú semanal) sin relación con el proyecto, mezclado por error en el inbox — dejado intacto, el usuario debe moverlo él mismo | `F:\Juegos Retro\inbox\`, `detection/platform_detector.py` (`PLATFORM_BY_EXTENSION`, falta `.smd`) | 🟡 basura borrada (536 MB liberados), 1 ROM organizado. **Decisiones del usuario aplicadas 2026-09-20**: los 51 conflictos de nombre movidos (no borrados) a `F:\Juegos Retro\_inbox_conflictos\` — inbox limpio, revisión manual pendiente ahí, sin decisión sobre su destino final. Gap `.smd` documentado como tarea propia, ver `MDFOLDER-FIX-3` (hecho 2026-09-22). Los 4 archivos ambiguos investigados a fondo: `dcnaodev.bios` y `zukinver0930.ipl` resultaron ser copias EXACTAS por SHA1 de chips ya presentes en `BIOS\naomi\` (`boot_rom_64b8.ic606`, `zukinver0930.ic25`) — **borrados del inbox** (duplicados verificados, cero riesgo), feature de auto-enrutado BIOS pedida y documentada aparte en `INBOX-BIOS-ROUTE-1`. `sfa3.hi` tiene ROM real en `arcade\sfa3.zip` — **movido a `arcade\sfa3.hi`** para que cargue junto al juego (mismo patrón que `CPS3\fbneo\sfiii2.hi`/`.fs` ya existente en la biblioteca). `sfz3a.hi`/`sfz3j.hi` son clones de `sfa3` (`romof="sfa3"`, verificado en el DAT FBNeo) sin romset propio en la biblioteca — **sin ROM al que acompañar, se quedan en el inbox** hasta que exista `sfz3a.zip`/`sfz3j.zip`. `Sonic 2 Adventure Edition.bps` (parche de hack) dejado intacto, `Menu_semanal...docx` sigue intacto (el usuario debe moverlo) |
| INBOX-BIOS-ROUTE-1 | **Petición del usuario 2026-09-20**, surgida al investigar `dcnaodev.bios`/`zukinver0930.ipl` en `INBOX-STALE-2`: el Inbox no reconoce BIOS/chips de devkit y los deja sueltos sin clasificar (hoy se investigan a mano). Feature pedida: que el pipeline del Inbox detecte estos archivos y los enrute solo a su carpeta (`BIOS/<sistema>/`, convención ya existente en la biblioteca real — `BIOS/naomi/`, `BIOS/dc/`, `BIOS/mame/`...). **Bloqueante real**: identificar un archivo suelto como "BIOS de sistema X" con confianza requiere el listxml completo de MAME (`isbios="yes"`, `romof`/`cloneof` para mapear chip→set→sourcefile→sistema) — el catálogo `mame_xml` (`_LIBRETRO_DAT_CATALOG`, ~300 MB) ya existe como entrada descargable pero no se ha bajado todavía en esta máquina, y el MAME2003-Plus/FBNeo dat que sí tenemos excluyen expresamente BIOS/devices (`load_mame_xml` los salta a propósito, ver docstring). **Verificación real del caso concreto que lo motivó** (no bloqueada por lo anterior, resuelta sin la feature): `dcnaodev.bios` y `zukinver0930.ipl` del inbox resultaron ser copias EXACTAS por SHA1 de `BIOS/naomi/boot_rom_64b8.ic606` y `BIOS/naomi/zukinver0930.ic25` ya presentes en la biblioteca — no eran huérfanas, eran redundantes; borradas del inbox, nada que enrutar en este caso concreto | `web/inbox_pipeline.py` (o módulo nuevo `bios_router.py`), depende de descargar `mame_xml` primero | 🔵 pedido, sin diseñar ni implementar — requiere sesión dedicada (descarga de listxml + mapeo BIOS→carpeta), el caso concreto que lo motivó ya se resolvió sin la feature |
| MDFOLDER-FIX-3 | `.smd` (Mega Drive, formato interleaved) no está en `PLATFORM_BY_EXTENSION`/`platforms.toml` — `organize-source` nunca detecta estos archivos, se quedan invisibles en el Inbox sin error ni aviso. Hallazgo de `INBOX-STALE-2` (2026-09-20): 2 archivos reales bloqueados por esto (`Aleste - Full Metal Fighter Ellinor (J) [!].smd`, `NHL93.SMD`), ambos probablemente ya duplicados en `megadrive/` con otro formato/nombre (`Aleste...bin` mismo tamaño SHA1 distinto; `NHL93.SMD` 512 bytes más grande que `NHLPA Hockey 93 (USA, Europe).md`, diferencia típica de cabecera interleaved) — sin verificar por hash todavía. **Nota de numeración**: esta tarea se documentó originalmente como "MDFOLDER-FIX-2" (2026-09-20), reutilizando por error un ID ya usado por la generalización de `PLATFORM_BY_FOLDER` (línea de arriba, hecha 2026-09-12) — renombrada a `MDFOLDER-FIX-3` el 2026-09-22 para deshacer la colisión, sin cambiar contenido. **Implementado 2026-09-22 (Día69)**: `".smd" = "Sega Mega Drive"` añadido a `detection/platforms.toml` (junto a `.gen`/`.68k`/`.sgd`) — `PLATFORM_BY_EXTENSION`/`ROM_EXTENSIONS` se derivan de ese TOML en `_build_tables()`, sin más cambios de código necesarios. 1 test nuevo (`tests/test_platform_detector.py::TestDetectPlatformUnambiguous::test_extension[.smd-...]`), confirmado en rojo contra el código anterior (`git stash`) y en verde tras el fix. Suite completa: 1431 tests, 0 regresiones. **Los 2 archivos reales de `INBOX-STALE-2` siguen sin verificar por hash** — ese paso sigue pendiente, requiere acceso a `F:\Juegos Retro\_inbox_conflictos\`, fuera de esta sesión | `detection/platforms.toml`, `tests/test_platform_detector.py` | ✅ hecho 2026-09-22 — desbloquea que `organize-source` detecte `.smd` en el Inbox; verificación por hash de los 2 archivos concretos de `INBOX-STALE-2` sigue pendiente |
| DISC-HEALTH-1 | No existe un chequeo repetible de "sets de disco rotos" — `Tareas/psx-cue-rotos-2026-08-30.md` fue investigación 100% manual (parsear `.cue`, comprobar que el `FILE` referenciado existe, y si no, buscar si ya hay un `.chd`/`.pbp` del mismo juego en la biblioteca). Convertir esto en una función reutilizable (mismo espíritu que `check_library_health`, pero para integridad de sets multi-archivo, no solo "existe la ruta") | `utils/health_checker.py` (candidato) o módulo nuevo | ✅ implementado 2026-09-06: `check_disc_set_health()` en `utils/health_checker.py`; extraída `is_broken_cue_set()` a `converters/chd_converter.py` como primitiva compartida con REPAIR-TOOL-4 (`_is_broken_disc_entry` ahora delega ahí, una sola definición de "roto") |
| LIB-MISPLACED-1 | El Inbox solo audita archivos **nuevos** que entran — nada revisa archivos ya sueltos dentro de una carpeta de plataforma ya organizada. Hoy mismo aparecieron chips de MAME sueltos en `gba/` (TMNT, `963-*.*`) y ROMs de otra plataforma (`.md`, `.nes`) mezclados en `gba/`, más una carpeta `_descartados/_descartados` con chips de arcade sueltos dentro de `psx/` — todo encontrado a mano antes de cada Cable Sync. Falta un escaneo de salud que recorra las carpetas de plataforma ya organizadas buscando extensiones que no pertenecen a esa plataforma (reutilizar `detect_platform()`/`PLATFORM_BY_EXTENSION`, ya fiables) | `scanner/rom_scanner.py` o `utils/health_checker.py` (punto de entrada exacto por confirmar) | ✅ implementado 2026-09-06: `check_misplaced_extensions_health()` en `utils/health_checker.py`, mismo espíritu que `check_disc_set_health()` (función reutilizable, aún sin wiring a CLI/web). Limitación conocida documentada en el docstring: extensiones ambiguas (`.zip`, `.bin`...) se resuelven por contexto de carpeta en `detect_platform()`, así que no detectan mezcla de contenido arcade dentro de `psx/` — solo extensiones no ambiguas de otra plataforma (caso real cubierto: `.nes`/`.sfc` sueltos en `gba/`) |
| LIB-MISPLACED-2 | **Confirmación a mucha mayor escala, 2026-09-20** (sesión de reclasificar `DUALFOLDER-12`, mientras se verificaba que ya no quedaran pendientes ese tipo). Ya existe un comando CLI (`rommgr relocate-misplaced <root>`, dry-run por defecto) que sí resuelve el "sin wiring a CLI/web" que `LIB-MISPLACED-1` daba como pendiente en 2026-09-06 — no está documentado en ese hallazgo, parece haberse implementado después sin actualizar el registro. Dry-run contra `F:\Juegos Retro` real: 1.500 archivos moverían de carpeta (extensión no coincide con su carpeta de plataforma), 5 duplicados exactos a descartar, 1 conflicto. El grueso venía de `gb/`, con subcarpetas nunca procesadas por el Inbox: `GB official game ROM complete works/` (2.650 archivos: 1.342 `.gbc` + 1.307 `.gb` + 1 `.zip`), `Classic Game/` (165 `.gb`), `Featured Games/` (19 `.gb`), `backup/` (1 `.xml`), `_descartados/` (812 archivos). **Corrección a la hipótesis de `DUP-CROSSFMT-1`/`LIBRARY-CLEANUP-GAPS-1`** (que asumía que esta subcarpeta "duplica TODO el contenido de `gb\`"): comparando por SHA1 y por título normalizado (`normalize_for_match()`) contra la raíz canónica de `gb/`+`gbc/`, de los 2.650 archivos del pack solo ~1.205 son duplicado exacto real — **1.278 no tienen ningún título equivalente en la biblioteca** (es la colección real de Game Boy Color, que nunca llegó a `gbc/` — esa carpeta solo tenía 77 archivos) y 167 comparten título con SHA1 distinto (revisión/región/dump diferente, no duplicado limpio). **Aplicado** (confirmado por el usuario): `relocate-misplaced --apply` sobre `F:\Juegos Retro` — 1.356 movidos a su carpeta correcta (`gbc/`, `mastersystem/`...), 147 duplicados exactos descartados a `_descartados/` (más que en el dry-run: el recuento del dry-run no refleja duplicados *dentro del propio lote* que solo se detectan al mover secuencialmente), 3 conflictos reales sin tocar (`Antz Racing (Europe)`, `Mr. Driller (Japan)`, `Ultimate Fighting Championship (Europe)`, contenido distinto al ya existente — revisión manual pendiente). **🔴 Bug real encontrado al re-ejecutar por accidente**: `check_misplaced_extensions_health()` (`utils/health_checker.py:91`, `folder.rglob("*")`) no excluye las carpetas `_descartados/` de su propio escaneo — al volver a correr `--apply` sobre una carpeta que ya tiene `_descartados/` con contenido, se auto-detecta como "mal ubicado" y lo anida un nivel más (`_descartados/_descartados/...`, hasta 6 niveles vistos en `GB official game ROM complete works/B/`). Mismo mecanismo que ya explicaba el `_descartados/_descartados` suelto encontrado en `psx/` (`LIB-MISPLACED-1`, sin diagnosticar entonces) — ahora con causa raíz confirmada. Sin pérdida de datos (`discard_to_trash` nunca sobrescribe, renombra con sufijo numérico ante colisión) pero sí "anidados restantes" ya existentes de antes en `gamegear/`/`nes/` (2 niveles, no relacionados con esta sesión). **Aplanado manualmente** (script de sesión, no versionado) en `gb/`, `gbc/`, `gamegear/`, `nes/` — 0 carpetas `_descartados` anidadas en toda la biblioteca tras el aplanado. Reescaneo completo con hash relanzado en segundo plano tras el `scan --quick` inicial (el quick-scan por sí solo deja `sync`/`match` no operativos, inaceptable dado que el sync de saves es la prioridad absoluta del proyecto) | `utils/health_checker.py:91` (`check_misplaced_extensions_health`, causa raíz del bug de anidación — fix pendiente: excluir `_descartados` del `rglob`), `F:\Juegos Retro\gb\` (subcarpetas ya movidas/vaciadas) | ✅ aplicado y verificado 2026-09-20 — 1.356 archivos reubicados, 147 duplicados descartados, `_descartados` anidados aplanados en toda la biblioteca. **Las 3 tareas pendientes, resueltas la misma sesión (petición explícita del usuario "haz esas 3 tareas")**:

(1) ✅ **Bug de anidación arreglado** — PR [#336](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/336) (`fix/relocate-misplaced-skip-trashed`, rama propia). `check_misplaced_extensions_health()` no cambia (sigue auditando `_descartados/` a propósito, test `test_nested_misplaced_file_is_found` lo exige); el fix va en `relocate_misplaced_files()` (`web/inbox_pipeline.py`): ignora cualquier resultado cuyo path ya contenga `TRASH_DIR_NAME` — la papelera es un estado ya decidido, no algo que esta pasada deba reorganizar. 1 test nuevo, suite 1401/1401.

(2) ✅ **Deduplicados los `.gb` de las subcarpetas basura** — tras el rescan completo con hash, comparación SHA1 real (no estimada) contra la raíz canónica de `gb/`: de 1.486 archivos restantes en `GB official game ROM complete works/`+`Classic Game/`+`Featured Games/`, **1.320 eran duplicado exacto** (descartados a `_descartados/` vía `discard_to_trash`, mismo mecanismo del proyecto, recuperables) y **166 sin duplicado exacto** se dejaron intactos (revisión/región distinta, ninguna decisión automática sin el DAT).

(3) ✅ **2 de los 3 conflictos resueltos con evidencia objetiva, 1 dejado sin resolver**. Comparando el código de producto interno de la cabecera GBC (offset `0x13F`, más fiable que el nombre de archivo) contra las copias regionales hermanas ya activas en `gbc/`: **`Mr. Driller (Japan).gbc`** y **`Ultimate Fighting Championship (Europe).gbc`**, los dos archivos ya activos en `gbc/`, resultaron ser duplicados exactos (mismo SHA1) de sus hermanos `(USA).gbc` — mal etiquetados como región distinta, probablemente desde el pack original. Las copias que estaban en la papelera SÍ tenían el código de región correcto (`MDJ`=Japón, `BUCP`=Europa). Se descartó la copia mal etiquetada (a `_descartados/`, recuperable) y se restauró desde la papelera la copia con el código correcto al mismo nombre de archivo. **`Antz Racing (Europe)`** queda sin resolver: mismo código de producto (`BAZP`, Europa real) en ambos lados pero SHA1 distinto — sin el DAT No-Intro de Game Boy Color no hay forma objetiva de elegir cuál es la buena, así que se deja como conflicto documentado, sin tocar ninguna de las dos copias. **Hallazgo colateral, sin medir su alcance**: el patrón "región mal etiquetada, contenido real = otra región ya presente" encontrado 2/2 veces que se pudo verificar sugiere que el pack (`GB official game ROM complete works/`) puede tener más casos similares entre los 166 "(2)" sin duplicado exacto — no auditado, candidato a sesión propia si se quiere ir más allá de los 3 conflictos que bloqueaban `relocate-misplaced`.

**(4) Cerrado, petición explícita del usuario ("vamos a tratar de cerrar este tema")**: de los 166 "sin duplicado exacto", investigado a fondo qué eran realmente antes de decidir — dos grupos con naturaleza muy distinta que no se habían distinguido hasta ahora:
- **124 en `GB official game ROM complete works/`**: nombres con convención No-Intro real (betas/protos/variantes regionales genuinas — `Darkwing Duck (Germany)`, `Donkey Kong Land III (Beta)`, `4 in 1 (Europe) (Sachen) (Unl)`...) — contenido de biblioteca legítimo, nunca duplicado. **Movidos a `gb/`** (109 sin colisión). De los 15 con colisión de nombre (mismo nombre ya activo en `gb/` con contenido distinto), verificado por checksum de cabecera GB: **2 casos objetivos** (`FIFA Soccer '97`, `Battle Arena Toshinden`) tenían en `gb/` un dump con cabecera de copiadora vieja pegada (+512 bytes, checksum inválido) — sustituidos por la copia limpia del pack (la vieja, descartada a `_descartados/`, recuperable). **13 casos quedan sin resolver** (checksum válido en ambos lados, contenido genuinamente distinto, sin DAT No-Intro para decidir cuál es la buena — mismo criterio que `Antz Racing`, ahora son 14 conflictos de este tipo documentados en vez de 1).
- **40 en `Classic Game/`+`Featured Games/`**: nombres tipo `0022 Ranch boy.gb`, `0059 The devil is 1.gb` — multicart pirata chino sin catálogo No-Intro real. **Descartados a `_descartados/`** (recuperables 30 días).
- **375 `.jpg`** (box art scraper antiguo, sin relación con los assets ya scrapeados de la biblioteca activa) + **1 `gamelist_20200331-2004.xml`** (backup ES-DE de 2020) — no son ROM/save/asset de plataforma activa. **Borrados permanentemente** (política ya establecida del proyecto: basura no-gaming se borra, no se archiva), 97 MB liberados.
- **1 archivo de otra plataforma completamente distinta**, encontrado al revisar: `Indiana Jones and the Infernal Machine (USA, Europe) (Disc 1).zip` dentro de `GB official game ROM complete works/I/` — es PSX/disco, no Game Boy. **Movido a `psx/`** (no existía ya ahí, sin colisión).
- Carpetas ya genuinamente vacías (`backup/`) **borradas**. `Classic Game/`/`Featured Games/`/las letras de `GB official game ROM complete works/` con solo `_descartados/` dentro se dejan tal cual (mismo criterio que el resto de la biblioteca — la papelera no se toca).

Rescaneado `gb/` y `psx/` tras cada paso, sin errores.

**Cierre final de los 14 conflictos**: los DAT No-Intro de Game Boy (1.613 entradas) y Game Boy Color (1.427 entradas) ya estaban descargados en `.rommgr/catalogs/nointro/` — no hizo falta bajar nada, solo cargarlos (`catalog_loader.load_dat_file`) y comparar el SHA1 real de cada lado contra el catálogo. Resultado: **12 de los 14 casos, la copia activa era mala** — o no matcheaba ninguna entrada del DAT (dump corrupto/no reconocido: `Jurassic Park`, `Mega Man IV`, `Momotarou Collection 2`, `Monster Race`, `Radar Mission`, `Super B-Daman`, `Taz-Mania`, `Trump Boy`, `Twin`, `Antz Racing`) o matcheaba la **región equivocada** (`Bubble Bobble (Japan).gb` era en realidad la ROM USA/Europe; `Lemmings (Europe).gb` era en realidad la ROM USA) — mientras la copia del pack coincidía por SHA1 exacto con la entrada del DAT que su propio nombre de archivo afirma ser. **Sustituidas las 12** (descartada la copia activa mala a `_descartados/`, restaurada la del pack verificada). Los otros 2: **`Pac-In-Time (Europe)`** — la copia activa YA era correcta (matchea su propia entrada del DAT); la copia del pack resultó ser la ROM USA mal etiquetada como Europa, y como `Pac-In-Time (USA) (SGB Enhanced).gb` ya existe en `gb/`, era simplemente redundante — descartada sin más. **`Road Rash (USA) (Rerelease) (1997-07-28)`** — el DAT no tiene una entrada separada para "Rerelease" (solo `(USA, Europe)` y `(USA, Europe) (Beta)`), y la copia del pack resultó coincidir con la Beta, no con ninguna variante que respalde el nombre "Rerelease" del archivo — **sigue como el único conflicto sin resolver**, ninguna de las dos copias se tocó.

Rescaneado `gb/`+`gbc/` tras el cierre, sin errores. Tema cerrado — solo queda `Road Rash` documentado como ambigüedad real, no bug |

### PSX-CATALOG-MISSING-1 — Falta el datfile Redump de PlayStation: 872/885 juegos (98%) sin `canonical_title` (hallazgo 2026-09-14, máquina "Ruben", `F:\Juegos Retro`)

Origen: petición del usuario de investigar por qué `PlayStation/` tiene nombrado
"raro" (mezcla `Alundra (Spain).chd` con `Crash Bandicoot [U] [SCUS-94900].ccd`,
`Chrono.Cross.NTSC.US.CD1.CCD`) y sospecha de duplicados por región.
Investigado contra `library_pc.db` real (885 filas `platform='PlayStation'`,
`file_type='rom'`): **872 sin `canonical_title`**, incluidos archivos ya
perfectamente nombrados en convención Redump (`Alundra (Spain).chd`) — es
decir, no es que el nombre esté mal formado, es que el matcher nunca ha podido
confirmarlos contra ningún catálogo. **Causa raíz confirmada**:
`.rommgr/catalogs/redump/` no tiene ningún "Sony - PlayStation - Datfile"
(el DAT principal de juegos) — solo existen `Sony - PlayStation - BIOS
Datfile (24).dat` y `Sony - PlayStation - SBI Subchannels Datfile (233).dat`,
ninguno de los cuales cubre juegos reales. Comparación de control: GBA sí
tiene su catálogo (`Nintendo - Game Boy Advance.dat`) y matchea 2018/2037
(99%) — mismo matcher, mismo código, la única diferencia es la ausencia del
DAT. Esto explica en cadena: (1) el nombrado "raro" — sin match no hay
`canonical_title`, y sin eso el renamer nunca toca el archivo, así que
sobreviven nombres de origen (scene `[SCUS-94900]`, `NTSC.US`, sin espacios);
(2) los 717 `.bin` sueltos + 99 `.cue` sin convertir a `.chd` (solo 106 `.chd`
de 885) — la conversión/organización real depende de tener primero un match;
(3) duplicados por región **invisibles para las herramientas de dedup
existentes** (`DUP-CROSSFMT-*`, ya maduras y probadas en la otra biblioteca —
ver `LIBRARY-CLEANUP-GAPS-1`) porque la unión por `canonical_title` exacto
necesita el match; la unión `crossfmt`/`sha1` (por nombre normalizado o
contenido) no depende del catálogo y debería seguir funcionando, pero no se
ha corrido `_build_review_queue` contra esta biblioteca para confirmarlo.
**No se encontraron subcarpetas por juego** en `PlayStation/` hoy (solo
`_descartados/`, verificado con `Get-ChildItem -Force`) — el mecanismo existe
en código (`move_disc_set_to_subfolder`, `file_renamer.py:346`, activado para
sets multi-pista en psx/saturn/dreamcast/wii) pero no se ha activado aquí
porque nada se ha renombrado todavía. Si el usuario recuerda haber visto
carpetas por juego, puede que sea de otra sesión/máquina o de un estado
anterior — pendiente de que el usuario confirme un ejemplo concreto antes de
asumir que es un bug distinto | `.rommgr/catalogs/redump/` (dato externo
faltante, no código); `catalog/matcher.py` (sin bug, ya verificado con GBA
como control); `renamer/file_renamer.py:346` (`move_disc_set_to_subfolder`,
mecanismo existente sin activar aquí) | ✅ **arreglado 2026-09-14**: descargado
`Sony - PlayStation.dat` (Redump, 10.270 entradas) con la herramienta ya
existente (`catalog/dat_downloader.py::download_dat`, mismo código que el
botón "Descargar DAT" de la web) a `.rommgr/catalogs/redump/`. Re-corrido
`rommgr match`: PSX pasó de **872 → 38 sin match** (847/885 matcheados) —
confirma la causa raíz. Desglose de confianza: 92 alta (SHA1 exacto), 153
media, 602 baja (nombre, ambiguo) — la mayoría del match es por nombre, no
por hash, así que muchos quedan como candidatos a revisión, no confirmados
al 100%. Nota menor sin investigar: 5 filas matchearon contra el datfile de
**Dreamcast** en vez de PlayStation — posible colisión de título entre
catálogos, mismo patrón que `CATALOG-MATCH-BUG-2`, sin cuantificar. Siguiente
paso: correr `_build_review_queue`/`resolve-duplicates` (dry-run) para medir
duplicados por región reales, mismo método que `DUP-CROSSFMT-1..9` en la
otra biblioteca |

### LIBRARY-AUDIT-1 — Estado de match por plataforma y huecos reales encontrados (auditoría 2026-09-14, `F:\Juegos Retro`)

Petición del usuario tras arreglar `PSX-CATALOG-MISSING-1`: "¿hay algo más que se pueda hacer observando la biblioteca?". Medido `canonical_title` matcheado/total por plataforma sobre `library_pc.db` real (29.422 juegos). Tabla completa y hallazgos:

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| PS2-CATALOG-MISSING-1 | **Mismo patrón exacto que `PSX-CATALOG-MISSING-1`**: PS2 (26 juegos) está al 0% de match. `.rommgr/catalogs/redump/` solo tiene "Sony - PlayStation 2 - BIOS Datfile" — falta el datfile principal "Sony - PlayStation 2 - Datfile" (el mapeo ya existe en `catalog/dat_downloader.py:45`, solo falta ejecutarlo, igual que se hizo hoy para PSX) | `.rommgr/catalogs/redump/` (dato externo, no código) | ✅ **arreglado 2026-09-15**: `POST /api/download-dats` con `Sony - PlayStation 2` descargó el datfile principal. Re-match: **26/26 matcheados (100%)** |
| ARCADE-CATALOG-MISSING-1 | **Arcade (1.511 juegos) al 0,7% y Neo Geo (88 juegos) al 1,1%** — no hay ningún catálogo MAME/FBNeo en absoluto: `.rommgr/catalogs/` solo tiene `nointro/` y `redump/`, ninguna carpeta `arcade/`/`mame/`/`fbneo/`. El mecanismo de descarga ya existe (`_download_mame_listxml` en `web/handlers/scan.py`, usado por el catálogo `_LIBRETRO_DAT_CATALOG` con entradas "FBNeo - Arcade Games"/"MAME 2003-Plus") — nunca se ha ejecutado en esta máquina. Palanca más grande de toda la auditoría: 1.599 juegos sin identificar | `.rommgr/catalogs/` (falta `arcade/`), `web/handlers/scan.py` (`_download_mame_listxml`, ya existe) | ✅ **arreglado 2026-09-15**, con dos bugs nuevos encontrados y corregidos de paso (ver `ARCADE-MATCH-PLATFORM-1` y `ARCADE-STEM-COLLISION-1` abajo). `POST /api/download-dats` con `FBNeo - Arcade Games`/`MAME 2003-Plus` dio 404 — las rutas están rotas (ver hallazgo), descargados a mano a `.rommgr/catalogs/arcade/` desde las URLs reales del repo. Re-match: **Arcade 1.156/1.511 (76,5%), Neo Geo 78/88 (88,6%)** — sí cubre Neo Geo (MVS/AES), confirmado |
| DREAMCAST-FORMAT-MISMATCH-1 | Dreamcast (11 juegos) al 0% — **no es un bug, es un hueco real de formato**: el datfile Redump descargado es "Sega - Dreamcast - GDI Files", pero los 11 juegos de esta biblioteca están en `.cdi` (DiscJuggler), no `.gdi` — formatos de dump distintos, el datfile GDI no tiene entradas para hashes de `.cdi`. Sin arreglo dentro de este proyecto (no hay conversor `.cdi`→`.gdi` ni datfile Redump de `.cdi`) — o se acepta sin match, o se convierte fuera de la herramienta. ✅ **investigado a fondo 2026-09-15**: (1) probado si `chdman createcd -i archivo.cdi` acepta el `.cdi` directamente (saltándose la conversión a `.gdi`) — sí lo intenta, pero se quedó **25+ min consumiendo CPU real sin producir un `.chd` utilizable** (124 bytes, solo cabecera) sobre un solo disco de prueba; abortado. (2) búsqueda web: consenso de la comunidad es que no existe un conversor `.cdi`→`.gdi` automatizado y fiable — DiscJuggler no tiene una estructura de tracks tan explícita como `.gdi`, la conversión que existe es manual por-juego (extraer el `.gdi` de una fuente distinta y reemplazar el contenido). Confirma la conclusión de ayer: sin arreglo viable dentro de este proyecto | `tools/chdman.exe` (soporte `.cdi` poco fiable/lento, probado hoy) | 🔵 investigado a fondo, **sin arreglo disponible** — la única vía real sería re-descargar esos 11 juegos como dump Redump `.gdi` desde otra fuente, no convertir el `.cdi` existente |
| NULL-PLATFORM-1 | **3.642 filas con `platform=NULL`** (12% de la biblioteca). ✅ **causa raíz confirmada 2026-09-15** (consulta completa sobre las 3.642 filas, no muestra): **100% de las 2.900 filas con `canonical_title` poblado están en `Unknown\`** (0 en cualquier otra carpeta) — no es una inconsistencia rara, es el comportamiento esperado: `detect_platform()` no reconoce "Unknown" como token de plataforma (`platforms.toml` no tiene entrada para ello) así que el platform se queda `NULL` al escanear, pero `rommgr match` es agnóstico de carpeta/platform — identifica el contenido por SHA1/nombre contra TODOS los DAT a la vez, así que estos 2.900 archivos SÍ se identifican (son ROMs reales sin organizar) aunque su fila no tenga platform. Son candidatos directos a `organize-source` (mecanismo ya existente, mismo pipeline del Inbox) para moverlos a su carpeta de plataforma real usando el match ya hecho. Las 742 filas restantes (`canonical_title` también NULL) SÍ se explican por las causas (1)/(2) ya documentadas: 545 en `Unknown\` (BIOS/config sueltos: `awbios.zip`, `naomi.zip`, `config.zip`, `data.zip`, + 1 `.iso` sin match) y 197 en `Neo Geo\` (chips de romset sueltos sin zipear, `003-c1.rom`...`003-c5.rom`) | `Unknown\` (2.900 archivos identificados sin organizar), `Neo Geo\` (197 chips sueltos), `detection/platform_detector.py` (sin entrada "unknown" en `platforms.toml`, comportamiento correcto — no es un bug) | 🟢 causa raíz explicada, sin ejecutar — siguiente paso natural: `organize-source` (dry-run primero) sobre `Unknown\` para los 2.900 ya identificados; los 742 restantes necesitan triage manual (BIOS/config se descartan, el `.iso` sin match se investiga aparte, los chips Neo Geo sueltos no se pueden organizar sin el resto del romset) |
| PSX-CHD-REDUNDANT-1 | **60,18 GB de archivos raw (`.bin`/`.cue`/`.ccd`/`.img`/`.sub`/`.ecm`/`.mdf`, 865 archivos) que son copias redundantes** — `convert-chd` (dry-run) confirma que 90 de los 94 `.cue` con nombre válido ya tienen su `.chd` (0 conversiones pendientes). ⚠️ la entrada original decía que `--apply --delete-source` "ya hace verificación RA-hash antes de borrar" — **falso para este caso concreto**, ver `CHD-DELETE-NO-VERIFY-1`. ✅ **arreglado 2026-09-15**: verificación de solo lectura propia (hash RA `.cue`+`.bin` origen vs. `.chd` existente, mismo `compute_psx_ra_hash` del conversor) sobre los 90 sets → **87 OK (hash idéntico), 0 discrepancias, 3 no verificables** (`Crash 2.cue`, `Dino Crisis 2 (France) (Xplosiv).cue`, `MediEvil 2 (Europe) (En,Fr,De).cue` — hash de origen no computable, sin evidencia de problema, simplemente no comprobable con la lógica actual). Borrado dirigido (script propio, no el CLI genérico) de los 87 sets verificados: **490 archivos, 44,21 GB liberados**. `rommgr scan` re-corrido después: 490 filas huérfanas podadas de la BD, limpio. Los 3 no verificables y los 4 rotos de `PSX-CUE-BROKEN-1` **no se tocaron**. Los formatos `.ccd`/`.ecm`/`.mdf` (~49 archivos) siguen sin confirmar (fuera de este flujo) | `converters/chd_converter.py`, CLI `convert-chd` (ya existe) | ✅ hecho — 44,21 GB liberados de forma segura; quedan 3 sets sin verificar por si se quiere investigar por qué su hash de origen no es computable (no urgente) |
| CHD-DELETE-NO-VERIFY-1 | **`convert_to_chd(..., delete_source=True)` NO verifica el hash RA cuando el `.chd` de destino ya existía de antes** — solo verifica (`_verify_ra_hash`, línea 380) en la rama de conversión fresca (chdman acaba de crear el `.chd`). Si `chd_path.exists()` es `True` al entrar (el caso de la inmensa mayoría de `PSX-CHD-REDUNDANT-1`: 90/94 sets), la rama de `if chd_path.exists(): if delete_source: borra sin más` se salta `_verify_ra_hash` por completo — borra el `.cue`+`.bin` origen dando por bueno un `.chd` preexistente sin comprobar que sea el mismo contenido. El diario de ayer asumió que la verificación cubría este caso; no es así | `converters/chd_converter.py:337-350` (rama `chd_path.exists()` de `convert_to_chd`, contrastar con la rama de conversión fresca en `:380-389` que sí llama a `_verify_ra_hash`) | ✅ **código arreglado 2026-09-15** (rama `fix/arcade-match-chd-verify-bugs`) — `convert_to_chd` y `convert_bin_to_chd` verifican el hash RA origen-vs-chd antes de borrar en la rama `chd_path.exists()`; a diferencia de `_verify_ra_hash` (pensada para la conversión fresca), en discrepancia **no se borra el `.chd` preexistente** (podría ser bueno para otra cosa), solo se rehúsa a borrar el raw. 4 tests nuevos (`tests/test_chd_converter.py`), 1325/1325 en verde |
| PSX-CUE-BROKEN-1 | **4 sets `.cue` reales rotos** encontrados por `convert-chd` (dry-run): `Street Fighter Alpha - Warriors' Dreams (Germany).cue` referencia `...(Europe) (Track 51).bin` (no existe — nombre de región no coincide entre el `.cue` y su `.bin`); `Street Fighter Collection (Europe) (Disc 1).cue` referencia 5 tracks que no existen; `Super Pang Collection (Europe).cue` referencia 1 track que no existe; `Warhammer - Shadow of the Horned Rat (Europe).cue` referencia 1 track que no existe. ⚠️ **corrección 2026-09-15**: la entrada de ayer decía "los 4 SÍ tienen ya un `.chd`, sin pérdida real" — **verificado hoy que es falso**: ninguno de los 4 tiene un `.chd` con ese nombre exacto (`Test-Path` sobre los 4 → `False`), ni existe ningún `.chd` alternativo para esos títulos/discos concretos en la carpeta (solo hay `Street Fighter Alpha 2`/`Alpha 3`, juegos distintos de la saga). Son la **única copia** de esos 4 juegos y están genuinamente incompletos (faltan pistas `.bin` reales, no es un problema de nombrado) | `F:\Juegos Retro\PlayStation\` (4 `.cue` concretos) | 🔴 **NO limpiar** — no son basura redundante, son dumps rotos sin backup. Requiere re-descargar/re-dumpear esos 4 juegos si se quieren jugables; hasta entonces no tocar (ni con `PSX-CHD-REDUNDANT-1` ni con ninguna limpieza) |
| UNKNOWN-BULK-GROWTH-1 | **`Unknown\` creció de ~2.900 archivos identificados (auditoría `NULL-PLATFORM-1`, 2026-09-15) a 80.518 archivos / 247,66 GB reales en disco (verificado 2026-09-24, `Get-ChildItem -Recurse`)** — pero `library_pc.db` solo tiene **755 filas** con `source_path` bajo `Unknown\` (88 identificadas, 752 con `platform` vacío): la inmensa mayoría de esos 80.518 archivos **nunca ha pasado por `rommgr scan`**, no es que el matcher fallara. Desglose por extensión: 38.441 `.zip`, 11.695 `.bin`, 7.609 `.jpg`, 2.909 `.nes`, 2.338 `.png`, ~830 `.rom`, 657 `.wav`, más cientos de extensiones numéricas (`.5`,`.10`,`.11`,`.2`...) típicas de chips MAME sueltos sin zipear. **Causa raíz de la fecha confirmada** (`Get-ChildItem -Directory` con `CreationTime`): las carpetas `arcade\`, `MAME\`, `games\`, `roms 1\`, `NES-Famicom\`, `megadrive\`, `gamegear\`, `sg1000\`, `ngp\`, `samples\`, `Imgs\` se crearon **todas el 2026-08-29 entre las 15:41:40 y las 15:50:24** (ventana de 9 min) — un solo evento de extracción masiva, no un goteo orgánico; la app no tiene ninguna función que descargue/extraiga packs así. **Usuario confirma que el volcado es totalmente inesperado** (2026-09-24) — no reconoce haberlo hecho. Sin identificar el proceso/origen externo responsable (pendiente si se quiere seguir esa vía). `E:\` tiene 452 GB libres, no es emergencia de espacio | `E:\Carpetas anbernic\Unknown\` (biblioteca real, sin tocar) | 🔴 origen externo sin identificar (decisión del usuario: no investigar más por ahora, pasar a `organize-source`) — ver `UNKNOWN-SCAN-GAP-1` (bloqueante nuevo encontrado al intentarlo) |
| UNKNOWN-SCAN-GAP-1 | ~~`rommgr scan` sobre `Unknown\` cuenta solo 22.250 de los 80.518 archivos reales~~ **descartado como bug, 2026-09-24**: los 58.393 archivos que el scan no cuenta viven dentro de **652 carpetas `_descartados\` anidadas** por toda `Unknown\` (`arcade\_descartados` 9.499, `megadrive\_descartados` 11.586, `MAME\_descartados` 1.942, `gamegear\_descartados` 1.894, `roms 1\_descartados` 1.877, `sg1000\_descartados` 435, `ngp\_descartados` 255, `samples\_descartados` 39, `games\{cps1,cps2,cps3,fbneo,neogeo,toaplan_cave_stg}\_descartados` ~950, más **cientos de carpetas `NES-Famicom\<Juego>\_descartados\`, una por título** con 1-12 archivos cada una) — `scan_library` las excluye correctamente por diseño (`_is_excluded()`/`TRASH_DIR_NAME`, `VAL-FIX-1`), no es un fallo del escáner. Suma verificada: 58.393 ≈ exactamente el hueco (80.518 − 22.250 = 58.268, diferencia por redondeo de una pasada anterior). **Esto SÍ es un hallazgo nuevo relevante**: el patrón "una carpeta por juego con su propio `_descartados\`" es exactamente lo que produce el propio pipeline de deduplicación/organize de esta app (mismo patrón que `psx\_descartados\` de `LIBRARY-SYNC-STALE-1b`) — indica que **algo (no documentado en ningún diario) ya ejecutó una limpieza/dedup real sobre este volcado**, triando duplicados a `_descartados` por juego/set, pero sin mover nunca el contenido "ganador" fuera de `Unknown\` a su carpeta de plataforma real ni dejar rastro en la BD (sigue en 755 filas) | `E:\Carpetas anbernic\Unknown\**\_descartados\` (652 carpetas, 58.393 archivos) | 🔵 hallazgo cerrado (no es bug) — pendiente decidir qué hacer con las 652 carpetas `_descartados` (¿son basura real triada y lista para borrar, o quedó a medias una operación que nunca movió lo bueno a su sitio?) |

| ARCADE-DAT-URL-STALE-1 | **Las URLs hardcodeadas de `FBNeo - Arcade Games` y `MAME 2003-Plus` en `_LIBRETRO_DAT_CATALOG` ya no existen en libretro-database** — devuelven 404. El repo renombró `metadat/fbneo/` → `metadat/fbneo-split/` (mismo nombre de archivo dentro) y el DAT de MAME real es `metadat/mame/MAME 2003-Plus XML.xml`, no `metadat/mame/MAME 2003-Plus.dat` (la entrada del catálogo no tiene `"file"` override, así que construye el nombre viejo). Encontrado al ejecutar `ARCADE-CATALOG-MISSING-1`; descargado a mano con la URL/nombre correctos como workaround, sin tocar código | `web/handlers/scan.py:59-60` (`_LIBRETRO_DAT_CATALOG`, entradas "FBNeo - Arcade Games"/"MAME 2003-Plus"), `web/handlers/scan.py:76` (`_CATALOG_TO_SOURCE`, `"fbneo": "fbneo"` debería ser `"fbneo-split"`) | ✅ **código arreglado 2026-09-15** (rama `fix/arcade-match-chd-verify-bugs`) — `_CATALOG_TO_SOURCE["fbneo"]` → `"fbneo-split"`, entrada `MAME 2003-Plus` con `"file": "MAME 2003-Plus XML.xml"`. El descargador automático de la web ya apunta a las URLs reales |
| ARCADE-MATCH-PLATFORM-1 | **`_match_arcade()` asigna `platform="MAME"`/`"FBNeo"` (nombre del catálogo fuente) en vez del platform canónico `"Arcade"`/`"Neo Geo"`** que usa el resto del proyecto (`platforms.toml`: `"mame"/"cps1"/"cps2"/"arcade"/"fbneo"` → `"Arcade"`, `"neogeo"` → `"Neo Geo"`). Al correr `POST /api/match` tras añadir el catálogo arcade (que sí pasa `arcade_dir`, a diferencia del CLI `match`), **1.225 filas reales de `library_pc.db` quedaron con `platform='MAME'`** — un valor que ningún otro sitio del código reconoce (folders, `fix-platforms`, detección). Corregido en caliente en la misma sesión (sin tocar código, solo datos): recalculado el platform real desde `source_path` con `detect_platform()` para las 1.225 filas — 1.222 pasaron a `Arcade`/`Neo Geo` correctamente (eran matches legítimos, solo mal etiquetados), 3 eran colisiones falsas (ver `ARCADE-STEM-COLLISION-1`). Verificado: `Arcade` 1.156/1.511, `Neo Geo` 78/88, `MAME`/`FBNeo` ahora en 0 filas | `catalog/matcher.py:435` (`arcade_platform = "MAME" if source.lower().endswith(".xml") else "FBNeo"`) | ✅ **código arreglado 2026-09-15** (rama `fix/arcade-match-chd-verify-bugs`) — `_match_arcade()` ya no inventa un platform, devuelve `platform=None` (el `update_match()` de la fila deja la columna intacta cuando es `None`). Test actualizado (`test_mame_style_zip_prefers_arcade_over_title_fallback`) |
| ARCADE-STEM-COLLISION-1 | **`_match_arcade()` (pass 3, stem lookup) no comprueba el platform del archivo antes de matchear por nombre de fichero contra el catálogo MAME/FBNeo** — 3 archivos de OTRAS plataformas cuyo nombre de archivo coincide por casualidad con un nombre corto de set arcade fueron matcheados y reclasificados como arcade: `nes\Arabian.nes` → set MAME "arabian" (Arabian de Sun Electronics), `nes\Macross.nes` → set MAME "macross", `Sega Mega Drive\Berzerk.md` → set MAME "berzerk". Mismo patrón de colisión ya documentado para otros catálogos (`CATALOG-MATCH-BUG-2`). Corregido en caliente en la BD real (match limpiado, platform restaurado a NES/Sega Mega Drive) | `catalog/matcher.py:421-441` (`_match_arcade`, sin guard de extensión/platform antes del stem lookup) | ✅ **código arreglado 2026-09-15** (rama `fix/arcade-match-chd-verify-bugs`) — `_match_arcade()` exige `.zip` antes del stem lookup (los sets MAME/FBNeo son siempre `.zip`, nunca un `.nes`/`.md` suelto). Test nuevo `test_non_zip_stem_collision_with_arcade_set_does_not_match` |

**Contraste de confianza — plataformas con catálogo presente pero match parcial** (no urgente, probablemente hacks/traducciones legítimos, mismo patrón que `DUP-CROSSFMT-9`, sin verificar caso a caso): NES 73,0% (12.126), Game Boy 73,7% (5.042), SNES 53,0% (1.290) — las tres tienen datfile No-Intro real, así que el hueco no es "falta catálogo" sino contenido que genuinamente no está en el DAT oficial (bootlegs, hacks, traducciones, homebrew) | — | 🔵 sin verificar caso a caso, baja prioridad |

---

### ANDROID-ARCADE-ZIP-1 — El ADB scan nunca indexaba arcade de verdad (hallado 2026-10-02, Anbernic conectada)

Origen: petición del usuario ("los arcade tienen nombres extraños, no los está
cogiendo bien") con la Anbernic conectada por USB. `library_android.db` tenía
551 filas `platform='Arcade'` — **las 551 eran residuo fantasma de un scan de
`H:\` de 2026-03-23** (`source_path` tipo `E:\Emuladores\MAME\bgfx\shaders\...`,
rutas de Windows). **0 filas apuntaban a una ruta real del dispositivo** — la
app nunca había escaneado `/storage/521D-04EA/ROMs/arcade` (ningún `scan_run`
con ese `source_root` en los 15 registrados).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ANDROID-ARCADE-ZIP-1 | **Causa raíz real, no solo "nunca escaneado"**: el ADB scan (`_do_adb_scan`) tenía `.zip` metido en la lista de extensiones a ignorar siempre (pensada para ZIPs del Inbox sin extraer) — pero en arcade/MAME/FBNeo el ZIP **es** el ROM, nunca se extrae (`converters/zip_extractor.py::_ARCADE_FOLDER_NAMES`, mismo criterio ya usado en otras partes). Primer escaneo real de `arcade/` tras conectar la Anbernic: `roms_detected=388` de `files_seen=10643` — **0 de los 1.746 `.zip` reales se indexaron**, solo los 267 `.rom`+111 `.bin`+9 `.chd`+1 `.ini` sueltos que ensuciaban la carpeta (coincide exacto con `SELECT extension, COUNT(*)` contra la BD tras el scan) | `web/handlers/scan.py:519-558` (`_do_adb_scan`, rama de skip-list) | ✅ **arreglado y verificado en vivo 2026-10-02** — `.zip` solo se ignora si NINGÚN segmento de la ruta está en `_ARCADE_FOLDER_NAMES` (reutilizada, no reinventada); dentro de una carpeta arcade se trata como ROM igual que el resto. Test nuevo (`test_adb_scan_arcade_zip_is_rom_not_skipped`, `tests/web/test_adb_scan_hashing.py`) reproduce el caso exacto. Re-escaneado contra la Anbernic real tras el fix: **`roms_detected` 388 → 10.409** — descubre de paso 2 colecciones completas nunca vistas antes, anidadas una carpeta más abajo de lo esperado: `arcade/mame/` (7.423 `.zip` reales) y `arcade/fbneo/` (852 `.zip` + 14 `.nv` + 1 `.hi`) — no son basura, el fix ya las indexa bien |

**Limpieza real ejecutada en el dispositivo (misma sesión, con confirmación explícita del usuario sobre el alcance)**: de los 378 `.rom`/`.bin` sueltos en la raíz de `arcade/`, clasificados por CRC32 contra `load_arcade_crc_index()` (mismo catálogo de `ZIP-ROUTE-2`) cruzado con los `.zip` ya presentes en la carpeta:
- **110 `.bin`** (`fs_*`/`vs_*`) = shaders bgfx de MAME, misma contaminación que `ZIP-ROUTE-8` pero copiada físicamente al dispositivo — **borrados**.
- **33 `.rom`** cuyo CRC32 coincide con un set que ya tiene su `.zip` en la misma carpeta = duplicado exacto redundante — **borrados**.
- 3 carpetas vacías (`gpu_drivers/`, `MAME 2003-Plus/`, `FinalBurn Neo/` con su `fbneo/` anidado también vacío) — **borradas**.
- Verificado antes y después por recuento exacto (`ls | grep -c`): 2.147→2.001 archivos en la raíz, 110→0 shaders, 267→234 `.rom` (−33 exacto).
- **235 `.rom` restantes (80 juegos reales identificados por CRC: Pole Position, 64th Street, Rock'n Rage, Gunforce, Tetris, EDF, Puzzle Bobble 3, DoDonPachi 2…) NO tienen `.zip` en el dispositivo — decisión explícita del usuario: no tocar hoy.** 27 de 30 comprobados al azar ya existen como `.zip` en `library_pc.db`, pero no verificado al 100% para los 80 — **candidato a `ANDROID-ARCADE-ORPHAN-CHIPS-1`** si se quiere cerrar del todo (verificar los 50 restantes + decidir si se borran del dispositivo o se re-sincroniza el `.zip` bueno desde el PC).
- Nota de herramienta: el borrado por ADB vía bucle en el host (`while read ... | adb shell rm`, uno por archivo) dio falsos positivos de éxito — la causa real fue CRLF en el fichero de lista (`Path.write_text()` en Windows sin `newline=""`) haciendo que tanto el `rm` como el `[ -e ]` de verificación comprobaran una ruta con un `\r` colgando que nunca existió. Solución real: `adb push` de la lista (LF puro) + un único `adb shell` que borra todo en un bucle del propio dispositivo — mucho más robusto que N invocaciones de `adb shell` desde el host.

---

### DC-GDROM-FIRST-SECTOR-1 — Los logros de Dreamcast no se reconocían pese a dumps correctos (hallado 2026-10-02)

Origen: petición del usuario ("añadí Sonic Adventure pero RetroArch no reconoce
que tenga logros, y creo que debería"), misma sesión que `ANDROID-ARCADE-ZIP-1`
con la Anbernic conectada.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DC-GDROM-FIRST-SECTOR-1 | **`_hash_dreamcast_from_cd_image()`/`_hash_track1_header()` leían siempre "sector 0" literal y `_root_dir_location()` siempre "sector 16" literal** — correcto para PSX/Saturn (`first_sector≈0`), pero roto para Dreamcast: un GD-ROM real codifica las direcciones MSF embebidas y los punteros de directorio ISO9660 en la dirección **absoluta del disco** (el área de alta densidad empieza en LBA ~45000), no relativa al inicio del archivo de la pista 3 — `_CdImage._detect_geometry()` ya detectaba `first_sector≈45000` correctamente, pero el resto del código nunca lo usaba para leer el IP.BIN ni el PVD. Descargado de verdad el track 3 de "Sonic Adventure (USA)" de la Anbernic (1,1 GB) para verificar: `compute_dreamcast_ra_hash()` devolvía `None` sobre un dump perfectamente válido | `retroachievements/ra_cd_image.py:116` (`_root_dir_location`), `retroachievements/ra_hash_saturn_dreamcast.py:60,96` (`_hash_track1_header`, `_hash_dreamcast_from_cd_image`) | ✅ **arreglado y verificado contra el hash real de RetroAchievements 2026-10-02** — las 3 lecturas ahora usan `cd.first_sector` en vez de un literal (`cd.first_sector` siempre resuelve a offset de archivo 0 sin importar su valor, así que PSX/Saturn con `first_sector≈0` no cambian de comportamiento; `cd.first_sector + 16` para el PVD sigue el mismo esquema de direccionamiento que ya usan los punteros de directorio). **Verificación con datos reales, no solo tests sintéticos**: el hash calculado tras el fix para el track 3 real de "Sonic Adventure (USA)" (`cb73faf2595353269a7846a034517420`) coincide EXACTO con uno de los 3 hashes registrados en RA para ese juego (`.rommgr/ra_cache/ra_hashes_40.json`, ConsoleID 40 = Dreamcast, 100 logros). 1 test de regresión nuevo (`test_compute_dreamcast_ra_hash_gdrom_high_density_offset`, reproduce el offset de 45000 con una imagen sintética), suite PSX/Saturn/Dreamcast completa en verde (20 pass) sin regresión. **No explica necesariamente el síntoma original en RetroArch** (RetroArch/Flycast calculan el hash con su propio código en C, independiente de esta reimplementación en Python usada solo para el caché/dedup interno de esta app) — pero confirma que el dump de Sonic Adventure del usuario es válido y tiene logros reales disponibles, así que el problema real está en la configuración de RetroArch/Flycast (logros activados, sesión iniciada, versión del core), no en el archivo |

**Comprobación de config real por ADB (misma sesión)**: `cheevos_enable=true`, `cheevos_username="kroq"`, `cheevos_token` presente (sesión real iniciada), `cheevos_hardcore_mode_enable=false`, `cheevos_verbose_enable=true` en `/storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg` — la configuración de RetroArch está bien. Hallazgo más probable: **hay 4 copias de Sonic Adventure en el dispositivo** (`(World) (XBLA).cdi`, `(USA)...gdi`, `(Europe)...gdi`, `Sonic Adventure 2 (Europe)...gdi`) — la `.cdi` de XBLA es un relanzamiento digital, build distinta del juego, casi seguro sin hash registrado en RA aunque el usuario la haya lanzado pensando que era la misma copia. No se pudo verificar la carpeta `logs/` de RetroArch (vacía, puede que este firmware la redirija a logcat) ni la versión del core Flycast (en almacenamiento privado de la app, sin acceso por ADB sin root). → ver `DUP-ALT-RELEASE-1` abajo, la detección de duplicados ahora sí vincula este caso.

---

### DUP-ALT-RELEASE-1 — Detectar relanzamientos digitales (XBLA/PSN/Virtual Console...) como posible duplicado (petición del usuario, 2026-10-02)

Origen: tras `DC-GDROM-FIRST-SECTOR-1`, petición directa del usuario ("puedes modificar la lógica para que detectemos también este tipo de duplicados").

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-ALT-RELEASE-1 | `Sonic Adventure (World) (XBLA).cdi` nunca aparecía vinculado a `Sonic Adventure (USA)...gdi`/`(Europe)...gdi` en la cola de revisión de duplicados — no comparte sha1 (build distinta) ni `canonical_title` (XBLA no está en ningún DAT No-Intro/Redump, así que `canonical_title=None` para siempre, sin importar cuántas veces se re-escanee). La unión fuzzy por región (`DUP-REGION-1`) tampoco lo cubre: excluye Dreamcast a propósito por estar en `_MULTI_DISC_RISK_PLATFORMS` (riesgo de fusionar discos reales de un multi-disco) | `detection/filename_normalizer.py` (`is_alternate_release_tag`, nueva), `web/builders/duplicates.py::_review_groups_for_repo` (nueva pasada `alt_release_groups`), `web/static/js/tabs/review_copies.js` (etiqueta `alt_release`) | ✅ **hecho 2026-10-02** — nueva pasada deliberadamente separada de `DUP-REGION-1`: agrupa por `(platform, normalize_for_match(canonical_title o filename))` igual que el resto, pero **solo une un grupo si al menos un miembro lleva una etiqueta explícita de relanzamiento digital** (`(XBLA)`/`(PSN)`/`(Virtual Console)`/`(Arcade Archives)`/`(eShop)`/`(Switch Online)`/`(GOG)`/`(Steam)`, mismo patrón acotado que `is_non_canonical_variant()`) — un multi-disco real nunca lleva esa etiqueta en un disco sí y en otro no, así que no reabre el riesgo que excluye Dreamcast de la unión por región. También se añade a `variant_tier` (mismo mecanismo de `ANDROID-DUP-SORT-TIEBREAK-1`) para que el dump original se recomiende sobre el relanzamiento aunque ninguno tenga todavía logros RA puntuados. Reproducido el caso exacto end-to-end (2 tests nuevos en `tests/test_builders_duplicates.py` + 2 en `tests/test_filename_normalizer.py`), suite completa 1528/1531 (los 3 fallos son tests preexistentes no relacionados que esperan "sin ADB conectado" — fallan solo porque la Anbernic sigue físicamente conectada en esta sesión, pasan bien en CI). **Hueco relacionado — arreglado también 2026-10-02, misma sesión** (el usuario pidió seguir): nueva `get_saturn_dreamcast_disc_hash()` en `ra_disc_hash_cache.py` (análoga a `get_psx_disc_hash()`/`get_gamecube_wii_disc_hash()`, mismo patrón de caché por `(mtime, size)`, console IDs 33=Saturn/40=Dreamcast), conectada en 2 sitios: `ra_checker._DISC_HASH_CONSOLE_IDS` (ahora `{12, 16, 20, 33, 40}`, cubre también el chequeo RA normal vía `check_library()`) y `_review_groups_for_repo`'s unión por hash de disco. **Hallazgo más grande de lo esperado al implementarlo**: el desempate `ra_tier`/`score_by_idx` (el que de verdad decide qué entrada se recomienda) usaba `r["md5"]` — un hash de archivo completo genérico (`hash_calculator.py`/`AdbTransport.md5_recursive`, el mismo paso para cualquier plataforma) — para **las 5 consolas de disco (PSX incluida)**, no solo Dreamcast/Saturn; RA hashea datos de arranque, no el contenedor, así que esa comparación nunca podía coincidir para ningún disco, nunca se había notado porque la mayoría de grupos de discos no llevan ninguna entrada con logros reales para notar la diferencia. Arreglado enrutando `score_by_idx` por `get_ra_console_id()` + los mismos getters de hash de disco que ya usa la unión, para las 5 consolas. 9 tests nuevos (4 en `tests/test_ra_disc_hash_cache.py` para la función nueva, 1 end-to-end en `tests/test_builders_duplicates.py` reproduciendo Sonic Adventure USA vs XBLA con caché RA real simulada — confirma que `ra_supported`/`recommended` ahora sí distinguen la copia con logros). Suite completa 1533/1536 (mismos 3 fallos preexistentes de "sin ADB" por tener la Anbernic conectada, no relacionados) |

---

### DUP-ALT-RELEASE-2 — Un relanzamiento digital que cae en el mismo clúster que un set multi-disco real desaparece entero de la cola de revisión (hallazgo 2026-10-02, auditoría completa de `DUP-ALT-RELEASE-1` sobre `library_pc.db`/`library_android.db` reales, a petición del usuario)

Origen: auditoría pedida por el usuario sobre toda la biblioteca (no solo Dreamcast) buscando relanzamientos digitales sin emparejar. 239 ROMs con tag de relanzamiento en total (223 PC / 16 Android). La mayoría de los "sin pareja" son falsos positivos esperados (inyecciones Virtual Console de Wii/3DS de OTRA plataforma — SMS/MD/NeoGeo/Arcade/PCEngine — archivadas bajo `platform=Wii`/`platform=Nintendo 3DS`; el agrupamiento por `(platform, fuzzy_key)` es correcto en no unirlas, la pareja real si existe está en otra plataforma). Pero uno de los casos sí es un bug real.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-ALT-RELEASE-2 | `has_alt_release_dup = any(i in alt_release_linked_idxs for i in idxs) and not is_disc_set` (`web/builders/duplicates.py:1304`) usa el mismo guard `not is_disc_set` que `has_region_dup`/`has_crossfmt_dup`/`has_disc_hash_dup` — pero `_is_disc_set()` (líneas 78-111) solo necesita ≥2 números de disco distintos en TODO el clúster para activarse, y al activarse apaga las 4 razones a la vez para el clúster completo, no solo para el par de discos. Un relanzamiento digital de un juego multi-disco que cae en el mismo clúster que sus discos reales pierde su única razón posible (`alt_release`) y el grupo sale con `reasons=set()` → `if not reasons: continue` (línea 1477-1481) lo descarta entero. Caso real en `library_android.db`: `Magical Drop III (Europe) (Disc 1)...chd` + `(Disc 2)...chd` + `Magical Drop III (USA) (NG) (Virtual Console).chd` — el VC nunca aparece en `/api/duplicates` | `web/builders/duplicates.py:1304` (`has_alt_release_dup`), `:78-111` (`_is_disc_set`), `:1120-1153` (unión `alt_release_groups`), `:1477` (`if not reasons: continue`) | ✅ **arreglado y verificado 2026-10-02**, petición explícita del usuario ("añade tanto como puedas a la lógica del programa"). **Causa raíz real, más profunda de lo que parecía al documentar**: no era solo el guard final — `normalize_for_match()` quita `(Disc N)` junto con región/tag de relanzamiento, así que el `fuzzy_key` de la unión `alt_release_groups` (línea 1142) colapsa Disc 1, Disc 2 Y el relanzamiento en el mismo bucket, y la unión los fusiona a los TRES como "duplicados entre sí" antes incluso de llegar al guard final — fusión semánticamente incorrecta independientemente de cómo se calculen luego las razones. **Fix de dos partes**: (1) `_is_disc_set()` ahora excluye los miembros con `is_alternate_release_tag()` del recuento de números de disco (un relanzamiento nunca es "disco N" de nada, mismo patrón que ya excluye miembros sin tag de disco — `DUP-DISC-SET-1`); (2) la unión `alt_release_groups` ahora llama a `_is_disc_set()` sobre cada bucket antes de fusionarlo, y si el bucket ya es un set multi-disco real, **no fusiona nada por fuzzy_key** — deja que el paso de `disc_hash` (más abajo, basado en hash RA real, no en nombre) vincule el relanzamiento solo con el disco específico que de verdad coincide. Reproducido end-to-end con los 2 archivos reales descargados por ADB de la Anbernic + el hash RA real: antes del fix, `total_groups: 0`; después, `total_groups: 1` con `reasons: ['disc_hash', 'title']`, exactamente `{Disc 1, Virtual Console}` (Disc 2 correctamente fuera del grupo, sin tocar). 2 tests nuevos en `tests/test_builders_duplicates.py` (`test_alt_release_in_a_real_multi_disc_set_links_only_the_matching_disc`, con `get_psx_disc_hash` monkeypatcheado igual que el test ya existente de Dreamcast). Suite completa: 1534 pass / 10 skip / 3 fail — los 3 fallos son los mismos preexistentes "sin ADB conectado" de siempre (la Anbernic seguía físicamente conectada en esta sesión), no relacionados |

**Verificación de hash RA real (los 5 consolas de disco, pedida explícitamente por el usuario) — y giro importante al bajar los archivos reales de Android por ADB**: `Magical Drop III (USA) (NG) (Virtual Console).chd` (PC) hashea (`519b1420d26175106d0459cdb40bdb7a`) EXACTO IGUAL que el Disc 1 real de Android (`Magical Drop III (Europe)...(Disc 1)...chd`, descargado y hasheado para confirmar) — **no es un relanzamiento digital genuino, es el mismo Disc 1 con una etiqueta "(Virtual Console)" puesta mal** (probable mal etiquetado de un release de scene), corrigiendo la hipótesis inicial ("un relanzamiento con logros, contradice la asunción del código"). El Disc 2 de Android no tiene hash RA propio (normal, RA solo registra el disco de arranque). `Castlevania - Symphony of the Night (Japan)...(XBLA).chd` (Android) también hashea exacto igual (`bf7e0e90d8e8d5738c7332bc6af666da`) que `(USA).chd`, que ya existe nativamente en el propio Android. `Sonic Adventure (World) (XBLA).cdi`: `library_android.db` no tenía fila para `Sonic Adventure (USA)/(Europe)` — **no es un hueco de biblioteca, es la BD desactualizada**: el dispositivo sí tiene el `.gdi` completo (4 pistas, ~1,2 GB, verificado por `adb ls`), y `DC-GDROM-FIRST-SECTOR-1` (sesión anterior) ya había confirmado sus logros RA reales descargando la pista 3. `library_android.db` necesita un rescan ADB para que ese `.gdi` aparezca — pendiente, no abordado en esta sesión. `.rvz` (GameCube) y `.cdi` como único dump (Dreamcast) siguen sin ser formatos soportados por `compute_gamecube_ra_hash`/`compute_dreamcast_ra_hash` — no verificables sin convertir antes.

**Limpieza aplicada en Android (confirmación explícita del usuario, "sí, bórralas"), 2026-10-02**: borradas por ADB (`rm`, hard delete directo — no fue el flujo normal de soft-discard a `_descartados/` de `ra_duplicates_service.py`, fue una limpieza puntual pedida en la conversación) las 3 copias redundantes confirmadas por hash: `Sonic Adventure (World) (XBLA).cdi`, `Castlevania - Symphony of the Night (Japan)...(XBLA).chd`, `Magical Drop III (USA) (NG) (Virtual Console).chd` — las 3 verificadas por hash RA real contra la copia que se queda, no por nombre. Filas correspondientes borradas de `library_android.db` con `cascade_delete_games_by_source_path` (mismo helper que usa `ra_duplicates_service._delete_row`), confirmado 0 filas restantes para esas `source_path`. **No se tocó nada en PC**: ahí cada uno de esos 2 archivos (`Sonic Adventure XBLA`, `Magical Drop III VC`) es la ÚNICA copia existente — borrarlos habría dejado esos juegos sin nada. `Magical Drop III` en PC le falta el Disc 2 para estar completo (candidato futuro: traer el set de 2 discos real desde Android).

**Segunda ronda, mismo día**: tras el fix, se relanzó el rescan ADB real contra el servidor web ya corriendo (`POST /api/adb-scan`, igual que haría la UI) para `dreamcast/` (85 ROMs, 0 podados — confirma que el `.gdi` real de Sonic Adventure ya estaba limpio en BD) y `psx/` (1432 ROMs, 57 filas obsoletas podadas, incluidas las 3 borradas arriba). Se verificaron por hash RA real los 2 casos `(Virtual Console)` de PSX que quedaban sin comprobar: **ambos resultaron ser el mismo patrón de mal etiquetado que `Magical Drop III`**, no relanzamientos reales — `Metal Slug X (USA) (NG) (Virtual Console).chd` hashea exacto igual (`c40bd37eaa2b2cc2f037a8d0318bcc26`) que `Metal Slug X (Europe).chd`; `Street Fighter Alpha 2 (Europe) (Virtual Console) (New 3DS).chd` hashea exacto igual (`079d330187f5770b109e58840479424e`) que `(USA).chd` y que `(Europe) (Track 1).bin`. Las 3 copias `(NG) (Virtual Console)` de este lote PSX concreto resultaron ser mal etiquetado, 0 de 3 relanzamientos genuinos — borradas las 2 restantes en Android (confirmación explícita del usuario), filas limpiadas igual que las anteriores.

