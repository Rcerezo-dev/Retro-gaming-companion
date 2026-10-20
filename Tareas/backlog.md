# Retro Vault — Backlog

> **Punto de entrada.** Este archivo es solo el índice: lo pendiente está en la tabla de abajo; el detalle de cada tarea vive en `Tareas/backlog/<epic>.md`. **No leas un epic entero**: busca el ID con `grep -rn "ID" Tareas/backlog/` y lee solo esa sección.
> Tareas con todas sus filas ✅ → `Tareas/backlog/hecho/<epic>.md`. Notas históricas de sesión (cabecera antigua) → `Tareas/backlog/hecho/cabecera-historial.md`. Completadas antiguas → `Tareas/diario/archivo/archivo.md`.
> Arquitectura: `docs/architecture/architecture.md`. Convención de épicas/issues: `.claude/CLAUDE.md` § Gestión de tareas. Al cerrar una tarea, márcala ✅ en su archivo de epic (fuente de verdad).

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
| `fix/matcher-coverage-gaps` | [14](../.claude/roadmaps/archivo/14-matcher-coverage-gaps.md) | [MATCH-FIX-3](backlog/hecho/pilar2-inbox.md) | Pilar 1 |
| `fix/cable-sync-format-gaps` | [16](../.claude/roadmaps/16-cable-sync-format-gaps.md) | [CABLE-ROM-FIX](backlog/hecho/pilar3-sync.md) | Pilar 3 |
| `feature/device-profile-loose-data` | [19](../.claude/roadmaps/archivo/19-device-profile-loose-data.md) | Sección "Hardware validation" (línea ~1284) | Perfil de dispositivo |
| — (acciones manuales/hardware) | [20](../.claude/roadmaps/20-rammu-machine-pending.md) | mixta, ver roadmap | mixta |
| — (limpieza de documentación, sin rama por defecto) | [24](../.claude/roadmaps/archivo/24-docs-audit-followups.md) | [DOCS-AUDIT-1](backlog/hecho/transversal.md) | Transversal |
| `feature/inbox-ux-summary-metadata` | [26](../.claude/roadmaps/26-inbox-ux-summary-metadata.md) | `INBOX-SESSION-SUMMARY-1`, `INBOX-METADATA-INLINE-1` | Pilar 2 — fase 3 de 6 — ✅ completo, PR [#339](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/339) abierto |
| `feature/saves-ux-history-context` | [25](../.claude/roadmaps/25-saves-ux-history-context.md) | `SAVES-HISTORY-1`, `SAVES-CONFLICT-CTX-1`, `SYNC-CONFLICT-MANUAL-1` | Pilar 3 — fase 4 de 6 — ✅ completo, PR [#338](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/338) abierto |
| `feature/library-folder-standardization` | [29](../.claude/roadmaps/29-library-folder-standardization.md) | `ESDE-FOLDER-STD-1`, `ROMHACK-ORG-1` | Multi-launcher (#337) — fase 2 de 6 |
| `feature/mobile-responsive-ui` | [30](../.claude/roadmaps/30-mobile-responsive-ui.md) | `MOBILE-UI-1` | UX — fase 5 de 6 |
| `feature/ra-achievements-live-progress` | [31](../.claude/roadmaps/31-ra-achievements-live-progress.md) | `RA-PROGRESS-UI-1` | RA/Scraper/SAGE — fase 6 de 6, bloqueado (API key real) |
| `feature/android-drive-2-signin` (Fase 1 en `main`/`develop` vía PR #357) | [28](../.claude/roadmaps/28-android-gdrive-provider.md) | [ANDROID-DRIVE-1](backlog/pilar3-sync.md) | Android Sync |

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
| Distribución | **Verificado 2026-10-04:** solo `PHASE6-1b` 🟡 y `D37-8` ⬜ — son la misma prueba (instalar `RetroVault-Setup.exe` en un PC sin Python); `PHASE6-1a/2a/2b/3a/3b/4` ✅. Hardware ajeno, no código |
| RA/Scraper/SAGE | **Verificado 2026-10-04:** `SAGE-1` 🟡 (cobertura de descripciones 75,5 %, objetivo >90 %, queda re-scrape), `SAGE-3` ⬜ (diferido a Sage v0.4 a propósito), `SAGE-4` 🟡 (backend de la propuesta A hecho; falta el panel "¿Qué quiero jugar hoy?" en el frontend), `RA-PROGRESS-UI-1` ⬜ bloqueado por la API key real. `SAGE-2` ✅ |
| Android Sync (nativo, no cable) | **Verificado 2026-10-04 contra las filas `ANDROID-*` de su sección:** abiertas de verdad `ANDROID-SYNC-15` 🟡 (checklist RG556), `ANDROID-SYNC-CRITICAL-1` 🟡 (causa raíz 2 sin arreglar), `ANDROID-DRIVE-1` 🟡 (roadmap 28), `ANDROID-BATTERY-1` 🟡 (medición = `HW-5`); `ANDROID-SYNC-13` ❌ descartada; el resto (`-1…-12`, `-14`) ✅ |

**2026-10-04** (auditoría, roadmap 33): filas de Pilar 1/2/3 de la tabla de arriba contrastadas con las tablas de sus secciones (estado de las sub-tareas, no solo el título). `ANDROID-DUP-2` ya no es 🔴: el escaneo ADB tiene fase 3 aplicada (`ANDROID-DUP-2-APPLY-1`, 25,08 GB liberados). Distribución, RA/Scraper/SAGE y Android Sync reverificadas después (misma fecha). Las 4 tareas de Pilar 1 sin reverificar siguen igual. Además se eliminaron ~518 líneas duplicadas por un merge antiguo (bloque `SYNC-WII-SCOPE-1` … `CABLE-SYNC-EMULATOR-SAVES-LEAK-1` ×3 y `SAVES-UX` ×2).

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

## Verificaciones pendientes con la RG556 conectada

Todo lo que se pospuso por no tener la consola enchufada (acumulado 2026-10-04, roadmap 33). Hacerlas en una sola sesión con `toolsdb.exe devices` mostrando el dispositivo.

| ID | Verificación | Origen | Estado |
|----|--------------|--------|--------|
| HW-1 | **83 grupos `crossfmt` de PSX (~4,5 GB)**: repetir la verificación por hash con `verify_group_by_disc_hash` (botón de duplicados o script; baja cada disco por ADB) y aplicar solo lo verificado. Decidir a mano los `.img`/`.mdf` que `compute_psx_ra_hash` no soporta | Día71, pendiente 1-2 | ⬜ |
| HW-2 | **Arcade `.nv` en Android** (`SAVES-FRAGMENT-3`/`EMULATOR-COMPAT-5`): con Dropbox/Drive vinculado en la app y "Sincronizar ahora", comprobar que suben los `.nv` de `mame/cps1/cps2` (`RetroArchPaths.ARCADE_FOLDERS`); revisar los ~40 `.nv` de `saves/Unknown/` | Decisión 2026-10-04 | ⬜ |
| HW-3 | **Redirigir standalones a ruta pública** (`SAVES-FRAGMENT-5`): DuckStation → Memory Cards → Directory, ARMSX2 y melonDS; checklist en `docs/emulador-canonico-rg556.md:497`. Dolphin standalone queda fuera (`SAVES-FRAGMENT-4`) | Decisión 2026-10-04 | ⬜ |
| HW-4 | **SAVE-GUARD-2 en Android**: `.sav` de 0 bytes con mtime posterior sobre un juego de prueba; el save bueno del remoto debe quedar intacto y contarse 1 conflicto (APK de `develop`) | Roadmap 32, Fase 0 | ⬜ |
| HW-5 | **ANDROID-BATTERY-1**: medir tramos A/B con la consola desenchufada varias horas (criterio: app < ~2-3 % de batería) | Roadmap 32, Fase 0 | ⬜ |
| HW-6 | **Filas fantasma en `library_android.db`** (2 discos españoles de MGS): rescan ADB completo | Día71, pendiente 5 | ⬜ |
| HW-7 | **Reconciliar la RG556 con la limpieza del PC del Día74** (con la consola conectada): (1) rescan ADB completo para que `library_android.db` refleje la biblioteca limpia — 4.683 piezas arcade sin ZIP y 308,5 GB de papelera purgados (incluido `_backup_android_descartados_20260909`); (2) ejecutar el junk-scan también sobre la copia de la consola (ya exige el ZIP del set, JUNK-ZIP-PIEZA-1) y comprobar que no hay piezas sueltas ni `Unknown\` allí; (3) enviar los ~92 ZIPs reorganizados (NGPC, NES, Master System) a su carpeta en la Anbernic; (4) confirmar que ningún save ni referencia apunta a lo purgado | Día74 | ⬜ |

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

## Epics

| Epic | Archivo | Secciones abiertas / hechas |
|---|---|---|
| Pilar 1 — Limpieza y organización inicial de la biblioteca — → #202 | [`backlog/pilar1-limpieza.md`](backlog/pilar1-limpieza.md) | 18 / 12 |
| Pilar 2 — Inbox automático — → #203 | [`backlog/pilar2-inbox.md`](backlog/pilar2-inbox.md) | 2 / 15 |
| Pilar 3 — Sync de saves PC ↔ Anbernic — → #204 | [`backlog/pilar3-sync.md`](backlog/pilar3-sync.md) | 11 / 11 |
| UX — Auditorías por pestaña — → #206 | [`backlog/ux.md`](backlog/ux.md) | 1 / 3 |
| Distribución / Release — → #207 | [`backlog/distribucion.md`](backlog/distribucion.md) | 2 / 0 |
| RA, Scraper y Recomendador (SAGE) — → #208 | [`backlog/ra-scraper-sage.md`](backlog/ra-scraper-sage.md) | 2 / 0 |
| Estandarización de biblioteca multi-launcher (ES-DE + ROM hacks/fan projects) — → #337 | [`backlog/estandarizacion-biblioteca.md`](backlog/estandarizacion-biblioteca.md) | 2 / 0 |
| Validación en hardware — → #211 | [`backlog/validacion-hardware.md`](backlog/validacion-hardware.md) | 1 / 0 |
| Perfil de dispositivo — provisioning con un botón — → #238 | [`backlog/perfil-dispositivo.md`](backlog/perfil-dispositivo.md) | 0 / 0 |
| Roadmap — Ideas futuras — → #212 | [`backlog/ideas-futuras.md`](backlog/ideas-futuras.md) | 1 / 0 |
| Transversal — Calidad de código, DX y referencia (sin epic) | [`backlog/transversal.md`](backlog/transversal.md) | 12 / 10 |

## Pendiente y por revisar

`pendiente` = alguna fila sin ✅. `revisar` = sección sin tabla de estado (prosa); comprobar a mano si sigue abierta. Generado el 2026-10-20 (DOCS-AUDIT-2b); se mantiene a mano al abrir/cerrar secciones.

| Sección | Epic | Estado |
|---|---|---|
| PSX-STRUCTURE — Auditoría de estructura de `psx/` (2026-09-02, a petición del usuario) | [pilar1-limpieza](backlog/pilar1-limpieza.md) | pendiente |
| RA-DEDUP-UNSAFE-1 — Borrar duplicados "sin soporte RA pero con alternativa" no se puede automatizar (hallazgo  | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| PSX-ORPHAN — Carpetas huérfanas de scraping en `psx/` (hallazgo 2026-08-26) | [pilar1-limpieza](backlog/pilar1-limpieza.md) | pendiente |
| ANDROID-DUP-1 — Duplicados reales en la propia Anbernic (DaijiShō/iSuu), nunca comprobados: dedup solo se ha e | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| ANDROID-DUP-2 — El escaneo ADB nunca calcula SHA1/MD5: matcher nunca corre sobre `library_android.db`, duplica | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| ANDROID-DUP-CROSSFMT-VERIFY-1 — los 61 grupos `crossfmt` restantes (53 pares `.chd`+`.bin` + 8 más, ~26,5 GB)  | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| ANDROID-STVERSIONS-1 — `saves/.stversions/<core>/` (carpeta de versionado de Syncthing) se trata como save rea | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| ANDROID-DUP-3 — `famicom/` es una segunda carpeta-plataforma paralela a `nes/` (86% de solapamiento por nombre | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| ANDROID-FDS-CLEANUP-1 — Limpieza de `fds/` verificada por SHA1: 0 bytes de contenido único, todo duplicado o m | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| ANDROID-ORGANIZE-ADB-1 — `organize-source` ya tiene el motor de dedup+ruteo arcade necesario; el hueco real es | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| GBA-DUAL-FOLDER-1 — `Game Boy Advance/` y `gba/` son dos carpetas activas paralelas con 881 títulos duplicados | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| PS2-DUAL-FOLDER-1 — `organize-source` crea un segundo `ps2/` en vez de usar `PlayStation 2/` ya existente (hal | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| CATALOG-MATCH-SUBSET-1 — `_match_by_title()` no comprobaba `is_non_canonical_variant()`, asignando el `canonic | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| DUALFOLDER-12 — 11 pares Title Case/slug restantes consolidados + guard en el Inbox (2026-09-17, máquina "Rube | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| MATCH-HANG-CHDMAN-1 — el job `match` (CLI y web) puede colgarse decenas de minutos sin avisar, sin poder cance | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| GDI-ORGANIZE-1 — Organizar los 9 sets Dreamcast/Naomi extraídos: 2 bugs reales encontrados antes de poder move | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| ANDROID-DUP-PSX-1 — PlayStation en la Anbernic: verificación por pareja real de SHA1 antes de aplicar, no fiar | [pilar1-limpieza](backlog/pilar1-limpieza.md) | pendiente |
| HEALTH-CHECK-RUBEN-1 — El Health Check semanal marcó 2 "corrupted" que en realidad son falsos positivos: el `s | [pilar1-limpieza](backlog/pilar1-limpieza.md) | revisar |
| PSX-CUE-DESYNC-1 — `rename_rom_with_saves` no reescribe la referencia `FILE` interna del `.cue` al renombrar — | [pilar2-inbox](backlog/pilar2-inbox.md) | pendiente |
| ZIP-ROUTE — Colocar los ZIPs sueltos por CRC del header (diseño 2026-07-10) | [pilar2-inbox](backlog/pilar2-inbox.md) | pendiente |
| NATIVE-SAVE-SYNC-1 — Estructura RetroVault en E:\ + sync de saves de juegos nativos (petición usuario 2026-09- | [pilar3-sync](backlog/pilar3-sync.md) | revisar |
| EMU-SYNC-WATCH-1 — Cloud sync automático al cerrar un emulador PC (petición usuario 2026-09-19, máquina "Ruben | [pilar3-sync](backlog/pilar3-sync.md) | revisar |
| CABLE-SYNC-WATCH-1 — Cable-sync automático al cerrar un emulador en la propia Anbernic (petición usuario 2026- | [pilar3-sync](backlog/pilar3-sync.md) | revisar |
| ANDROID-SYNC — App Android nativa de sync de saves (diseño 2026-08-18) | [pilar3-sync](backlog/pilar3-sync.md) | pendiente |
| EMULATOR-COMPAT — Save compatibility PC ↔ Android | [pilar3-sync](backlog/pilar3-sync.md) | pendiente |
| ANDROID-APP-CLEANUP-1 — Desinstaladas las 4 apps sin uso ni RA (hecho 2026-09-27) | [pilar3-sync](backlog/pilar3-sync.md) | revisar |
| DAIJISHO-IISU-PATHS-1 — Las rutas de Daijishō e iiSU a `SD:/ROMs/` ya funcionan, se resolvieron solas (verific | [pilar3-sync](backlog/pilar3-sync.md) | pendiente |
| CABLE-ROOT-1 — El Cable Sync por ADB apuntaba a almacenamiento interno vacío, no a la SD real del dispositivo  | [pilar3-sync](backlog/pilar3-sync.md) | pendiente |
| ANDROID-APP-PRIVATE-STORAGE-1 — DuckStation y AetherSX2 guardan en `Android/data/<paquete>/` (RG556): ni ADB n | [pilar3-sync](backlog/pilar3-sync.md) | pendiente |
| SAVE-GUARD — No dejar que un save dañado gane un conflicto (idea 2026-10-03) | [pilar3-sync](backlog/pilar3-sync.md) | pendiente |
| SYNC-REMOTE-TREE-1 — PC y Android parecen sincronizar RetroArch en árboles distintos de Dropbox (hallazgo 2026 | [pilar3-sync](backlog/pilar3-sync.md) | pendiente |
| MOBILE-UI — UI usable desde el móvil (idea usuario 2026-09-22) | [ux](backlog/ux.md) | pendiente |
| Phase 6 — Distribution | [distribucion](backlog/distribucion.md) | pendiente |
| DÍA37 — Distribuible completo + prueba en PC limpio (2026-07-02) | [distribucion](backlog/distribucion.md) | pendiente |
| SAGE — Soporte para Retro Sage (recomendador NLP) | [ra-scraper-sage](backlog/ra-scraper-sage.md) | pendiente |
| RA-LIVE — Progreso de logros en la ficha del juego (idea usuario 2026-09-22) | [ra-scraper-sage](backlog/ra-scraper-sage.md) | pendiente |
| ESDE-FOLDER-STD-1 — Confirmar y cerrar el hueco real de integración ES-DE (idea usuario 2026-09-22) | [estandarizacion-biblioteca](backlog/estandarizacion-biblioteca.md) | pendiente |
| ROMHACK-ORG-1 — Organizar ROM hacks / fan projects que no matchean catálogo oficial (idea usuario 2026-09-22) | [estandarizacion-biblioteca](backlog/estandarizacion-biblioteca.md) | pendiente |
| Hardware validation (requires console or SD card) | [validacion-hardware](backlog/validacion-hardware.md) | revisar |
| ROADMAP-IDEAS — Propuestas del usuario (2026-08-13, sin diseñar aún) | [ideas-futuras](backlog/ideas-futuras.md) | revisar |
| DOCS-AUDIT-2 — Documentación optimizada para sesiones con Claude (auditoría 2026-10-20) | [transversal](backlog/transversal.md) | pendiente |
| DOCS-AUDIT-3 — Adaptar commands y agent al backlog partido (seguimiento de 2b, 2026-10-20) | [transversal](backlog/transversal.md) | pendiente |
| SUBPROCESS-WINDOW-1 — Todas las llamadas a herramientas externas abrían una consola visible en modo headless ( | [transversal](backlog/transversal.md) | revisar |
| RETROARCH-THUMBS-1 — Publicar carátulas/capturas ya escaneadas en el árbol `thumbnails/` de RetroArch (petició | [transversal](backlog/transversal.md) | revisar |
| User actions (no code needed) | [transversal](backlog/transversal.md) | revisar |
| GBA-MISPLACED-1 — Archivos de otras plataformas mal ubicados en `gba/` con metadatos corruptos (hallazgo 2026- | [transversal](backlog/transversal.md) | pendiente |
| GAMECUBE-DISC-BUG-1 — Juegos multi-disco de GameCube marcados como "duplicado" (bug serio, riesgo real de pérd | [transversal](backlog/transversal.md) | pendiente |
| ARCADE-RENAME-BUG-1 — MAME/FBNeo no cargan ~2.766 ROMs de `arcade/` por nombre de archivo (hallazgo 2026-08-31 | [transversal](backlog/transversal.md) | pendiente |
| LIBRARY-SYNC-STALE-1 — Biblioteca corregida el 08-30 (GBA/PSX/GameCube) nunca llegó a la Anbernic (hallazgo 20 | [transversal](backlog/transversal.md) | pendiente |
| GBA-SAVE-PATH-1 — GBA "no encuentra los saves anteriores" tras instalar emuladores nuevos (investigado en vivo | [transversal](backlog/transversal.md) | pendiente |
| LIBRARY-CLEANUP-GAPS-1 — Huecos reales encontrados al limpiar PSX a mano (hallazgo 2026-08-31) | [transversal](backlog/transversal.md) | pendiente |
| PSX-CATALOG-MISSING-1 — Falta el datfile Redump de PlayStation: 872/885 juegos (98%) sin `canonical_title` (ha | [transversal](backlog/transversal.md) | revisar |
| LIBRARY-AUDIT-1 — Estado de match por plataforma y huecos reales encontrados (auditoría 2026-09-14, `F:\Juegos | [transversal](backlog/transversal.md) | pendiente |
