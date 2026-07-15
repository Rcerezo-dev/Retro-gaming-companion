# Retro Vault — Backlog

> Single source of truth for pending work. Updated every session.
> Last updated: 2026-07-14 (ANBERNIC-UX 1-8: pestaña Anbernic — generador único, token efímero, panel Android real)
> Completed tasks → `Tareas/diario/archivo/archivo.md`
> Arquitectura actual: `docs/architecture/architecture.md`

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

## Roadmap App Universal

> Phases 1–5 (first run, DATs, sync, UX no-técnica, auth) **completadas** →
> detalle en `Tareas/diario/archivo/archivo.md`.

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

## Roadmap — Ideas from Idea_final.md

Extracted from `docs/ideas/Idea_final.md` and broken into actionable tasks.
COL-REVIEW, FLOW-WIZARD, CLOUD-RESEARCH, ANBERNIC-TV y NLP-REC **completados** → archivo.

### EMULATOR-COMPAT — Save compatibility PC ↔ Android

Verify that synced saves from PC actually load on Android and vice versa, for each emulator pair.

| ID | Task | Notes |
|----|------|-------|
| EMULATOR-COMPAT-1 | Create compatibility matrix — PC emulator, Android emulator, save format, save path per platform | `docs/emulator-compat.md` ✅ |
| EMULATOR-COMPAT-2 | Test PS1 round-trip: DuckStation PC → sync → DuckStation Android → load | Hardware test with RG556 |
| EMULATOR-COMPAT-3 | Test PS2 round-trip: PCSX2 PC → sync → AetherSX2/NetherSX2 Android → load | Hardware test |
| EMULATOR-COMPAT-4 | Test remaining platforms (GBA, SNES, GBC, NDS…) and document any format mismatches | Update matrix per result |

### ARCADE-SETUP — Research arcade ROM config (no code)

| ID | Task | Notes |
|----|------|-------|
| ARCADE-SETUP-1 | Research MAME vs FBNeo ROM set version compatible with Anbernic RG556 RetroArch | Check RG556 community guides |
| ARCADE-SETUP-2 | Identify target arcade systems and map each to the correct RetroArch core | e.g. CPS1/2/3, Neo-Geo, MAME 2003 Plus |
| ARCADE-SETUP-3 | Document config additions: `config.toml`, library-structure, DAT sources for arcade | `docs/arcade-setup.md` ✅ + descarga de DATs arcade cableada (runtime: `_run_dat_download` en `web/handlers/scan.py` + `scan.js`; installer: `catalog/dat_downloader.py` vía `installer/download_dats.py`) |
| ARCADE-SETUP-4 | Test a sample ROM end-to-end: scan → rename → launch on device | Hardware test |

---

## Hardware validation (requires console or SD card)

| ID | Task |
|----|------|
| V1 | SD card auto-sync — configure `anbernic_root`, insert SD, verify banner + log |
| V2 | Two-database migration — Settings → "Migrate DB" → verify separate PC/Android counts |
| V3 | Inbox end-to-end — configure `inbox_path`, drop ZIP, verify extraction + rename + move |
| V4 | RetroAchievements with real API key |
| V5 | Termux guide on console — prereq for WiFi sync |
| B1-hw | Android renamer doesn't reduce queue — test with SD inserted |

---

## DÍA37 — Distribuible completo + prueba en PC limpio (2026-07-02)

Objetivo cumplido salvo la validación en hardware ajeno: `RetroVault-Setup.exe`
autocontenido publicado en el release `v1.0.0` (detalle D37-1…D37-10 → archivo).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| D37-8 | **Prueba en PC limpio** — hardware test: instalar en máquina sin Python siguiendo la sección 0 de la guía; ejecutar checklist funcional (§5); valida PHASE6-1b | otro PC | ⬜ |

---

## MEJORAS — Propuestas 2026-07-02 (ordenadas por valor/esfuerzo)

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MEJ-1 | **Playtime real desde logs `.lrtl` de RetroArch** — scanner stdlib-json de `playlists/logs/<Core>/<rom>.lrtl` (`runtime` + `last_played`) que puebla `play_history`; elimina la entrada manual de horas (confirmado: `gpLogPlaytime()` hoy no persiste nada, solo hace `alert()`, `games.js:531-542`). Fase 2: sync de los `.lrtl` de Android (mismo pipeline que saves) → playtime unificado PC+consola. Alimenta el recomendador NLP. Diseño detallado en `Tareas/Roadmap-Juegos-UX.md` (JUEGOS-UX-4..9) | `scanner/` (nuevo módulo), `database/repositories/play_history.py`, endpoint | ⬜ |
| MEJ-2 | **Deshacer último apply** — endpoint que invierte los renames de la última operación usando `file_operations` (ya registrado en SQLite); reutiliza `rename_rom_with_saves` en dirección inversa. | `planner/`, `web/handlers/` | ⬜ |
| MEJ-3 | **Backup automático de la DB antes de apply/migraciones** — `sqlite3.Connection.backup()` (stdlib, ~5 líneas) antes de cada apply. | `planner/operation_planner.py` o `database/repository.py` | ⬜ |
| MEJ-4 | **Sync de cheats (`.cht`)** — un `SyncSource` más apuntando al dir `cheats/` de RetroArch, mismo patrón que NEW-8 (`.opt`). ~10 líneas. | `config.py`, `sync/sync_cloud.py` | ⬜ |
| MEJ-5 | **"¿A qué juego hoy?"** — botón en Overview: `random.choices` ponderado por status Pendiente + rating + no jugado recientemente. Recomendador v0 mientras no exista el modelo NLP. | `web/handlers/`, `tab-overview.html` | ⬜ |
| MEJ-6 | **UI del junk-scan (tarea 2i-1)** — el endpoint `POST /api/junk-scan` fue restaurado (PR #80, se perdió en el refactor `487aa91`) pero el frontend sigue en stubs: `_renderJunkResult`, selección por categoría y borrado vía `/api/junk-delete` son TODOs en `esde.js`. | `web/static/js/tabs/esde.js` | ✅ rama `feature/mej-6-junk-scan-ui` — stubs implementados (render con `<details>`, selección por categoría, borrado con confirm + re-scan); `doJunkScan` corregido (id del contenedor, input `#junk-path`, endpoint síncrono sin job); builder expone `paths` completos por categoría (antes el borrado solo cubría los 50 mostrados). Verificado e2e con servidor real |

> **Orden sugerido:** MEJ-1 → MEJ-2 → MEJ-3 → MEJ-4 → MEJ-5

---

## SAGE — Soporte para Retro Sage (recomendador NLP)

Origen: `ROADMAP.md` de Retro Sage. SAGE-1 y SAGE-2 son **bloqueantes** para su
fase 2 (embeddings). Contexto adicional: `docs/ideas/propuestas-recomendador-nlp.md`.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| SAGE-1 | **Scraping masivo de descripciones** (bloqueante Sage v0.2) — completar las descripciones de la biblioteca por lotes desde la fuente del scraper puntual. Reanudable (no re-scrapear lo ya descargado), rate-limit razonable, descripciones visibles en `GET /api/export-history`. Hecho cuando >90% de los juegos tienen descripción no vacía en el export. | `database/repositories/metadata.py`, `web/handlers/scraper.py`, `web/builders/misc.py`, `tab-scraper.html`, `scraper.js` | 🟡 código listo (rama `feature/sage-1-mass-descriptions`): el job `/api/scrape` ya era reanudable+rate-limited; añadido modo `missing_descriptions` (re-scrapea metadata con descripción vacía sin machacar imágenes), cobertura en `/api/scrape-summary` + UI (hoy 70.0%). Pasada real 2026-07-07: 964 en cola, 860 match, 0 errores (tras fix `_loads_lenient`, PR #79) pero cobertura 70,0→70,1% — los re-scrapeados no tienen sinopsis en SS. Para >90% hay que resetear `metadata_scraped` de los ~4.700 sin match histórico y re-scrapear (~89% de acierto hoy), o usar otra fuente. **Experimento reset 2026-07-07: fallido** — la cola de 4.692 era basura no-juego (chips de romsets arcade, shaders RetroArch, restos de Papelera `$I*.iso`, firmware): 415 procesados, 6 match. Flags revertidos. **Camino real al >90%: limpiar la basura de la biblioteca** (junk-scan restaurado en PR #80) — al quitar ~4.700 no-juegos del denominador, 13.217/~14.150 ≈ 93%. **Limpieza ejecutada 2026-07-08 (Día39)**: 28.718 archivos borrados (chips arcade de `Unknown\`, ~15,4 GB) + fixes del clasificador (PRs #82/#83) → cobertura **70,1% → 84,3%** (13.136/15.591). Para >90% queda JUNK-REVIEW-1 (revisar 5.771 ZIPs de `Unknown\`: colecciones fuente vs juegos individuales — decisión usuario) y re-scrape de los ~2.455 sin descripción restantes |
| SAGE-2 | **Migración `genres_list` / `players` persistidos** (bloqueante Sage v0.2) — persistir ambos campos en la BD (hoy derivados al vuelo) con backfill de registros existentes, y exponerlos en el export. Hecho cuando aparecen estables en `/api/export-history` y el contrato queda documentado en `play_history.py`. Detalle: `docs/ideas/propuestas-recomendador-nlp.md`. | `database/`, `database/repositories/play_history.py` | ⬜ |
| SAGE-3 | **Registro de recomendaciones mostradas/clicadas** (futuro, Sage v0.4) — para el bucle de feedback de Sage: registrar qué recomendaciones se mostraron en el panel y cuáles se clicaron, y exponerlo (export o endpoint nuevo). **No implementar todavía**: el diseño se negocia cuando Sage llegue a v0.4. | — | ⬜ |

---

## INBOX-FIX — Bugs del pipeline de extracción/organización (hallados en JUNK-REVIEW-1, 2026-07-08)

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
| INBOX-FIX-4 | **`_run_setup_pipeline` construye el plan de renombrado pero nunca lo aplica** — a diferencia de `_run_inbox_pipeline` (extract→scan→match→plan→**rename→organize**→cleanup, todo automático), el asistente de primera configuración se para en "build plan" (Step 5) y deja el resto para una acción manual aparte. Es la razón de fondo por la que `Unknown\` quedó con miles de archivos sin categorizar tras el primer scan de la biblioteca real — nadie ejecutó nunca el equivalente de los Steps 5-6 del pipeline de Inbox sobre ella, así que hubo que aplicar los fixes con scripts manuales en vez de con la app. Objetivo: que el wizard también renombre+organice automáticamente (o, si se prefiere mantener el review manual por seguridad, que la UI dirija explícitamente al usuario a "aplicar el plan" en vez de dejarlo ahí sin más pasos). Decisión de diseño: ¿auto-aplicar sin revisión rompe la regla `rommgr plan siempre antes de apply`? | `web/inbox_pipeline.py` (`_run_setup_pipeline`) | ⬜ |
| INBOX-FIX-5 | **El borrado por "duplicado" (organize + BIOS intercept) solo comparaba nombre de archivo, no contenido** — bug de pérdida de datos real: aplicado a la biblioteca real, 22 archivos "duplicados" borrados resultaron tener SHA1 distinto del superviviente (dumps/revisiones distintas que solo compartían nombre). `Path.unlink()` en Windows no pasa por la Papelera — no recuperable. | `web/inbox_pipeline.py` | ✅ `_same_content()` (tamaño + SHA1) antes de borrar en ambos sitios; si difiere, no se toca ninguno y se reporta para revisión manual. 8 tests — PR #90 |
| MATCH-FIX-1 | **`CatalogMatcher.match()` — Pass 2 (nombre) da falsos positivos en ficheros arcade sin tag de región** — nombres cortos estilo MAME (`flicky.zip`, `frogger.zip`, `dw.zip`…) sin `(Region)` colisionan por coincidencia de título normalizado contra catálogos No-Intro/Redump de plataformas completamente ajenas (`flicky.zip` → "Fujitsu - FM-7", `frogger.zip` → "APF - Imagination Machine") con confianza `low`, en vez de matchear contra el catálogo arcade correcto (Pass 3, que nunca llega a probarse porque Pass 2 ya "acertó"). Detectado 2026-07-08 al re-lanzar el match sobre `Unknown\` — son matches **preexistentes**, no introducidos hoy. Fix: para nombres sin región/paréntesis, probar primero el catálogo arcade (Pass 3) antes que el name-fallback No-Intro/Redump (Pass 2), o exigir una señal más fuerte que la sola coincidencia de título normalizado. | `catalog/matcher.py` | ✅ rama `fix/match-fix-1-arcade-before-name-fallback` — para `.zip` sin `(` en el nombre (estilo MAME) el pass arcade corre antes que el fallback por título; el resto conserva el orden actual. Passes 2/3 extraídos a `_match_by_title()`/`_match_arcade()`. 4 tests nuevos (caso real flicky.zip vs FM-7; 635 pass). **Pendiente aparte**: los falsos matches preexistentes en BD no se corrigen solos — re-lanzar el match sobre `Unknown\` tras mergear |

> Quedan pendientes: INBOX-FIX-4 (decisión de diseño sobre auto-apply del wizard),
> MATCH-FIX-1 (prioridad del matcher), y la decisión del usuario sobre las 15
> colecciones completas de JUNK-REVIEW-1 (categoría 2).

---

## JUNK-SMART — Clasificador de basura basado en evidencia (diseño 2026-07-08)

Origen: Día39 demostró que la whitelist de extensiones de `_build_junk_scan`
(`web/builders/folders.py:37`) falla en las dos direcciones — falsos positivos
que exigieron 3 rondas de parches (JUNK-FIX-1/2/3: `.rvz`, `.sms`, `.sgm`,
`.nv`…) y falsos negativos (3.309 chips arcade con extensión gaming
`.bin`/`.rom` pasaron limpios y hubo que borrarlos con criterio manual:
≤8 MB + nombre de chip + cero `.cue` en el árbol). La app ya tiene el
conocimiento para decidir sola; hoy no lo usa.

**Fuentes de evidencia ya existentes (todas gratis, sin hashear de nuevo):**

1. **BD `games`** — `sha1` indexado (`database/schema.py:41,62`) para todo
   archivo con extensión gaming ya escaneado. Un archivo con match de catálogo
   (`canonical_title`/`catalog_source`) **nunca** es basura.
2. **Catálogos DAT** — tablas keyed por SHA1 (`database/schema.py:178,185`).
   SHA1 presente en No-Intro/Redump → ROM real, da igual la extensión.
3. **MAME XML** — `catalog/mame_loader.py:32` parsea `isbios`/`isdevice`/
   `runnable=no` y los **descarta**. Guardarlos en un set aparte identifica
   directamente la categoría 5 de JUNK-REVIEW-1 (`c1541.zip`,
   `kb_pcat101.zip`, `sb16.zip`… = infraestructura MAME, no juegos).
4. **`_KNOWN_BIOS_MAP`** (`web/inbox_pipeline.py`) — ZIPs BIOS con destino
   conocido → "mover a bios/", no borrar.
5. **Señales de contexto validadas en JUNK-CLEAN-1**: nombre de chip
   (`u082.bin`, `c1`, `ic12`…), tamaño ≤8 MB, ausencia de `.cue` hermano.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| JUNK-SMART-1 | **Tier de evidencia sobre la whitelist** — mantener la whitelist actual como filtro barato (tier 0: `.pdf`, `.exe`… siguen siendo basura obvia); añadir tier 1 para extensiones ambiguas (`.bin`, `.rom`, `.zip` fuera de carpeta de plataforma): join por ruta contra `games` → con match = skip; sin match + patrón de nombre de chip + sin `.cue` en el árbol → categoría nueva "Chips sueltos (sin match en catálogo)". `_build_junk_scan` recibe `repository` como parámetro (sigue siendo función pura, el handler se lo pasa). | `web/builders/folders.py`, `web/handlers/` (call-site) | ✅ rama `feature/junk-smart-1-evidence-tier` — el builder recibe `matched_paths` (set de rutas con `canonical_title` en BD, lo consulta el handler; con `None` el tier queda apagado → el setup pipeline, que borra lo devuelto, no cambia). Señales: sin match + stem de chip + sin `.cue` en la carpeta + ≤8 MB. Verificado contra biblioteca real: 93 chips `.rom` en `arcade\` detectados (antes invisibles), 0 falsos positivos. 3 tests nuevos (625 pass) |
| JUNK-SMART-2 | **Clasificar ZIPs sueltos por nombre de set MAME** — `load_mame_xml` devuelve además el set de nombres bios/device excluidos (o loader hermano); el junk-scan clasifica `.zip` de `Unknown\`: stem en catálogo arcade jugable → "ROM arcade sin organizar (no borrar)"; stem en set bios/device → "Infraestructura MAME"; stem en `_KNOWN_BIOS_MAP` → "BIOS (mover)"; patrón `Vendor - Plataforma.zip` o >1 GB → "Colección fuente (revisar)". Resuelve de raíz la categoría más grande del scan actual ("ZIPs no-ROM", 5.852 falsos en Día38). | `catalog/mame_loader.py`, `web/builders/folders.py` | ✅ rama `feature/junk-smart-2-mame-zip-classes` (apilada sobre JUNK-SMART-1) — loader nuevo `load_arcade_infra_names()` (los nombres que `load_mame_xml` descarta); el builder recibe `arcade_names`/`mame_infra_names`/`known_bios_files` (los construye el handler; con `None` no cambia nada). Verificado contra biblioteca real: los 1.305 "ZIPs no-ROM" se separan en 1.036 infraestructura MAME + 56 colecciones (27 GB) + 5 arcade + 208 genuinamente sin identificar. 5 tests nuevos (630 pass) |
| JUNK-SMART-3 | **Confianza por categoría en la UI** — cada categoría lleva etiqueta `safe_delete` / `review` / `misplaced` (esto es "no borrar, organizar/mover"); el botón de borrado masivo solo se habilita para `safe_delete`, el resto exige expandir y confirmar. Evita repetir el susto de INBOX-FIX-5. | `web/builders/folders.py`, `web/static/js/tabs/esde.js` | ✅ rama `feature/junk-smart-3-confidence-labels` (apilada sobre JUNK-SMART-2) — campo `confidence` en cada categoría (`_CATEGORY_CONFIDENCE`, default `safe_delete`); en la UI: badge por categoría, checkbox deshabilitado para `misplaced`, las `review` se habilitan solo al abrir "Ver archivos" (`junkRevealCat`), "Seleccionar todo" solo coge habilitadas y el confirm avisa si la selección incluye categorías `review`. 1 test nuevo (631 pass) |

> Orden: 1 → 2 → 3 (cada una es útil sola; 3 depende de que 1-2 emitan la etiqueta).

---

## ZIP-ROUTE — Colocar los ZIPs sueltos por CRC del header (diseño 2026-07-10)

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
| DAT-FIX-1 | **El DAT de Wii U (Digital) nunca carga** — `load_nointro_dat` revienta con `int('')` en `catalog_loader.py:135` (`size=""` en algunos `<rom>`); `_load_dir` lo captura y **salta el DAT entero** con un warning. Fix trivial: `int(rom.get("size") or 0)`. Descubierto al verificar ZIP-ROUTE-1. | `catalog/catalog_loader.py:135` | ⬜ |
| ZIP-ROUTE-2 | **Identificar sets arcade por votación de CRCs** — índice `crc → {sets}` de los DATs arcade (`MAME 0.286 (arcade).dat` + FBNeo, iterparse); cobertura 100 % → renombrar al nombre de set y mover a `arcade\` (79, incluye los 5 "arcade sin organizar" y los 48 clones mame-stem que el XML local no lista); 1-99 % → `review` con candidato sugerido (29, otra versión de romset). | `catalog/mame_loader.py` (o loader hermano), `web/builders/folders.py` | ✅ rama `feature/zip-route-2-arcade-crc-voting` (apilada sobre ROUTE-5) — `load_arcade_crc_index()` (solo `.dat`, iterparse, +2,4 s, 162k CRCs) + `_vote_arcade_set()` (ignora entradas vacías, CRC 0 espurio). Categorías nuevas: "ROMs arcade identificadas (renombrar al set y mover)" (`misplaced`, con `identified_as`) y "Sets arcade de otra versión (revisar)" (`review`, con `coverage`). Verificado contra biblioteca real: 78 al 100 % + 28 parciales; ZIPs no-ROM 153→47. **Ojo para el mover futuro**: los DATs FBNeo de consola también votan (Gleylancer [T-En]→`gleylance`) — el destino no siempre es `arcade\`, hay que mapear DAT→carpeta al mover. 4 tests (639 pass) |
| ZIP-ROUTE-3 | **Romhacks: plataforma por extensión interna** — sin match CRC pero 1 entrada con extensión inequívoca (`.nes`/`.sfc`/`.md`/`.gba`/`.gg`/`.pce`…) → mover a la carpeta de esa plataforma conservando el nombre (49 T-En/hacks; siguen sin `canonical_title`, correcto — no están en ningún DAT). | `web/builders/folders.py` | ✅ rama `feature/zip-route-3-romhack-inner-ext` (apilada sobre ROUTE-2) — `_single_rom_platform()` usa `PLATFORM_BY_EXTENSION` (vía módulo, no import directo — reload_platforms rebindea); `.md` y demás extensiones con contexto se excluyen (¿Mega Drive o markdown? sin carpeta no se desambigua). Categoría "ROMs/romhacks por extensión (mover a su plataforma)" (`misplaced`, con `platform`). Verificado: 44 romhacks con plataforma; **"ZIPs no-ROM" queda en 3** (2 romhacks `.md` + 1 addon) de los 208 originales. 2 tests nuevos + 2 adaptados (641 pass) |
| ZIP-ROUTE-4 | **Colecciones → extraer al Inbox** — para las 16 colecciones reales (multi-entrada `.zip`/`.chd`, ~26 GB: `Nintendo - GBA.zip` 150 zips, `Arcade - Mame 2003 Plus.zip` 375, `NEC - TurboGrafx CD.zip` 25 .chd…): botón "Extraer al Inbox" que descomprime los miembros en el Inbox y deja que el pipeline existente haga hash → match → rename → organize (el intercept de BIOS ya rutea `MAME BIOS 0.277.zip`). Guard de espacio libre ≥ tamaño descomprimido; borrar el contenedor solo tras extraer con éxito, una colección por job. **Requisito (usuario, 2026-07-10): cero duplicados** — tras organizar, ni el ZIP contenedor ni copias intermedias pueden quedar en el Inbox; verificar que el organize del pipeline mueve (no copia) y limpia el Inbox al terminar. **Requisito (usuario, 2026-07-10): UN solo paso** — el usuario no extrae ni pulsa un segundo botón. | `web/inbox_pipeline.py`, `web/handlers/esde/maintenance.py`, UI | ✅ rama `feature/zip-route-4-one-step-apply` (apilada sobre ROUTE-3) — módulo nuevo `web/zip_router.py`: `_route_identified()` (arcade → directo a `arcade\` renombrando al set, **nunca por el Inbox** — el pipeline extraería el ZIP y un set arcade extraído está roto; colecciones → por mayoría de miembros: sets arcade → extraer a `arcade\` [salva a `SNK - NEO GEO.zip` y `Arcade - Mame 2003 Plus.zip`], BIOS/infra → no tocar [`MAME BIOS 0.277.zip`], consola → extraer al Inbox; contenedor borrado solo con todos los miembros en disco; consola+romhacks → mover al Inbox) y `_run_zip_route_apply()` que encadena `_run_inbox_pipeline(delete_source=True)` bajo el mismo job "inbox" (nuevo param `extra_result`). Conflictos: destino existente → no tocar y reportar. Endpoint `POST /api/zip-route-apply` + botón "Organizar identificados (1 paso)" en el junk-scan (muestra `identified_as`/`platform` por archivo). Dry-run contra biblioteca real: 83 arcade directo, 2 colecciones a arcade, 13 al Inbox, 1 skip BIOS, 139 zips al Inbox. 4 tests (645 pass). **Ejecutado de verdad 2026-07-10** (backup previo de `library_pc.db`): 77 arcade movidos, 15/16 colecciones extraídas (1.746 miembros), 139 zips al Inbox, 1.636 zips extraídos de colecciones, 3.134 ROMs escaneados, 2.915 matched, 1.062 renombrados, 136 organizados (la mayoría del resto eran duplicados exactos ya en la biblioteca → borrados por política de deduplicación, no "organizados"). 6 conflictos arcade ya existentes + 1 pack BIOS omitidos (esperado). **3 hallazgos reales durante la ejecución → ver ZIP-ROUTE-FIX-1/2/3.** |
| ZIP-ROUTE-FIX-1 | **`rename_rom_with_saves` no crea el directorio destino** — a diferencia de `move_disc_set_to_subfolder` (que sí llama `target_dir.mkdir(parents=True, exist_ok=True)` antes de mover), `rename_rom_with_saves` va directo a `os.rename(source, target)` sin asegurar que `target.parent` existe. Cuando el plan de renombrado manda un ROM a una subcarpeta nueva (p. ej. "Virtual Console"), falla con `WinError 3` (ruta no encontrada). **Sin pérdida de datos** — el fallo es atómico, el archivo se queda donde estaba y el organize posterior lo mueve igualmente (con el nombre viejo, no el canónico). Descubierto al ejecutar ZIP-ROUTE-4 sobre la biblioteca real: 20 renombrados fallidos (límite de la lista de errores, puede haber más). | `renamer/file_renamer.py:76` (antes de `os.rename`) | ✅ rama `feature/zip-route-fix-1-mkdir-target-dir` — `target.parent.mkdir(parents=True, exist_ok=True)` antes de `os.rename`, mismo patrón que `move_disc_set_to_subfolder`. `tests/test_file_renamer.py` (nuevo, 2 tests: subcarpeta nueva + mismo directorio). 647 pass |
| ZIP-ROUTE-FIX-2 | **`UNIQUE constraint failed: games.source_path` al organizar** — el `UPDATE games SET source_path=...` tras mover el archivo (inbox_pipeline.py:646-650) falla cuando ya existe otra fila en `games` con ese `source_path` exacto, aunque el `dest_file.exists()` de la línea 622 no lo detectó antes de mover (filas "fantasma" que apuntan a una ruta sin archivo real, probablemente de una sesión anterior nunca limpiada). El archivo físico SÍ queda movido a su destino final — el problema es solo de consistencia de la BD (fila vieja huérfana + el `UPDATE` de la fila nueva no se aplica). Descubierto al ejecutar ZIP-ROUTE-4: 20 casos (límite de la lista, puede haber más). Investigar de dónde salen esas filas fantasma antes de decidir el fix (¿borrar huérfanas al detectarlas? ¿`INSERT OR REPLACE`?). | `web/inbox_pipeline.py:643-653` | ✅ rama `feature/zip-route-fix-2-ghost-row-cleanup` — `DELETE FROM games WHERE source_path=? AND id!=?` en la misma transacción `batch()` justo antes del `UPDATE`; el físico ya se había movido de todas formas, así que borrar la fila fantasma es seguro (no puede haber dos archivos reales en la misma ruta). `tests/test_inbox_pipeline_organize.py` (nuevo). 646 pass |
| ZIP-ROUTE-FIX-3 | **La ambigüedad de `.md` (ZIP-ROUTE-3) deja cientos de ROMs de Mega Drive sin clasificar, no solo "2-3"** — el diseño original asumía pocos casos (`"ZIPs no-ROM" queda en 3"`); al extraer de verdad las colecciones "Sega - Genesis"/"Sega - Genesis (Update 1)" sus miembros `.md` sueltos entran al Inbox y el pipeline normal hereda la misma ambigüedad (¿Mega Drive o markdown?) sin la ventaja de contexto de carpeta que sí tenía el ZIP. Resultado real: **345 archivos `.md`** quedaron sin organizar en el Inbox tras ZIP-ROUTE-4 (de un total de 458 archivos restantes). No hay pérdida — siguen en el Inbox — pero el "un solo paso" prometido no cubre este caso. Posible fix: dentro del Inbox (con contexto de carpeta/colección de origen conocido) desambiguar `.md`→Mega Drive cuando el resto de la carpeta ya se resolvió a esa plataforma. | `web/builders/folders.py` (`_single_rom_platform`), `web/inbox_pipeline.py` (platform detection) | ✅ rama `feature/zip-route-fix-3-md-context-tokenize` — causa raíz real: `_has_platform_context` (`detection/platform_detector.py:93`) exigía coincidencia EXACTA de una parte de la ruta contra "genesis"/"megadrive"/"md"/"sega genesis"; ZIP-ROUTE-4 extrae la colección a una carpeta con el nombre literal del ZIP ("Sega - Genesis"), que nunca iguala ninguno de esos nombres aunque los contenga. Fix: tokenizar cada parte de **carpeta** (`path.parent.parts`, nunca el nombre de archivo — si no, el propio ".md" del archivo se autoconfundiría con el token "md") por separadores no alfanuméricos. 2 tests nuevos + los 5 existentes de `.md` siguen en verde. 647 pass. **Ejecutado de verdad 2026-07-10** (backup previo de `library_pc.db`): 573 `.md` organizados en `megadrive\` (antes 0). Quedan 177 `.md` sueltos en la raíz del Inbox sin carpeta que los desambigüe — genuinamente ambiguos por diseño, no un bug; posible ZIP-ROUTE-FIX-4 futuro: identificarlos por CRC/tamaño en vez de contexto de carpeta. |
| RA-CONFLICT-1 | **Los conflictos "mismo nombre, contenido distinto" del organize del Inbox usan RA para decidir el ganador** — antes se limitaba a reportar en `organize_errors` y dejar todo para revisión manual. La lógica de "quedarse con la versión que tiene logros RA" ya existía para conflictos del *plan* (`apply_ra_conflicts` en `services/ra_duplicates_service.py`), pero el organize del Inbox usa su propio chequeo de colisión (`inbox_pipeline.py`, `dest_file.exists()` + `_same_content`) y no llamaba a esa lógica — rutas de código independientes. Petición del usuario 2026-07-10 tras encontrar 20 conflictos reales de este tipo en la biblioteca. | `services/ra_duplicates_service.py`, `web/inbox_pipeline.py` | ✅ rama `feature/ra-conflict-resolution-inbox-organize` — refactor: `apply_ra_conflicts` exponía la lógica de lookup RA como closures internos (`_hash_lib_for`/`_ra_for_path`); se extrajeron a funciones de módulo reutilizables `get_ra_hash_lib()`/`get_ra_achievements()`/`get_ra_achievements_for_path()` (mismo comportamiento, 4 tests existentes en verde sin cambios). Nueva función `_resolve_organize_conflict()` en `inbox_pipeline.py`: mismo criterio de desempate que `apply_ra_conflicts` (más logros gana; empate o ambos sin datos RA → sin resolver, igual que antes); reutiliza `_discard_file()` (soft-discard a `_descartados/` + borra fila BD) para el perdedor. Contador nuevo `ra_resolved` en el resultado del job "inbox". 3 tests nuevos (`test_inbox_ra_conflict.py`): source gana, dest gana, sin datos RA → sin tocar. 653 pass. **Ejecutado de verdad 2026-07-10** (backup previo de `library_pc.db`): `ra_resolved: 3` sobre los conflictos reales de la biblioteca; quedan 20 sin resolver por falta de datos RA para esa plataforma/hash — comportamiento idéntico al anterior para esos casos, nada perdido. |
| RA-CONFLICT-2 | **Revisar/resolver a mano desde la UI los conflictos que RA no puede decidir** — RA-CONFLICT-1 resuelve solo los que tienen datos RA; el resto (sin caché para esa plataforma/hash) quedaban solo como texto en `organize_errors`, sin forma de actuar salvo tocar archivos a mano. Petición del usuario 2026-07-10. | `web/inbox_pipeline.py`, `web/handlers/inbox.py`, `web/static/partials/tab-inbox.html`, `web/static/js/tabs/inbox.js`, `web/static/js/main.js` | ✅ rama `feature/ra-conflict-ui-resolution` — nuevas funciones puras `find_organize_conflicts()` (listado de solo lectura: recorre `games` bajo el Inbox, mismo cálculo de destino que el Step 6 real vía `_organize_dest_file()` extraído para no duplicarlo, incluye tamaños y logros RA de ambos lados) y `resolve_inbox_conflict()` (re-verifica que el conflicto sigue existiendo y llama a `_resolve_organize_conflict()` con el nuevo parámetro `force_keep` — mismo mecanismo de discard/move que la resolución automática, decisión inyectada en vez de calculada). Endpoints `GET /api/inbox-conflicts` + `POST /api/inbox-conflicts/resolve`. UI: sección nueva en la pestaña Inbox con botón "Revisar" → tabla (archivo, plataforma, tamaño+logros de cada lado, botones "Quedarme con Inbox"/"Quedarme con existente"). 5 tests nuevos (`test_inbox_conflicts_ui.py`), 658 pass. Verificado el endpoint de lectura contra la biblioteca real (40 conflictos con datos correctos); el de escritura solo verificado con tests (no se resolvió ningún conflicto real de la biblioteca desde este endpoint — queda para que el usuario lo use desde la UI). |
| ZIP-ROUTE-5 | **Retirar la heurística de colección por nombre** — sustituir `" - " in stem` + `>1 GB` (`web/builders/folders.py:259,276`) por "multi-entrada de `.zip`/`.chd`" (el ZIP ya se abre para ROUTE-1, es gratis). Elimina los ~39 falsos positivos. | `web/builders/folders.py` | ✅ rama `feature/zip-route-5-collection-by-content` (apilada sobre ROUTE-1) — colección = >1 entrada y mayoría `.zip`/`.chd` (`_is_source_collection`); fuera `" - "` y `_COLLECTION_MIN_BYTES`. Verificado contra biblioteca real: colecciones 47→**16, exactamente los contenedores reales** (incl. `MAME BIOS 0.277.zip`); los ~31 ex-falsos (T-En, FM77AV, Super Pocket) caen a "ZIPs no-ROM" (122→153) a la espera de ROUTE-2/3. 2 tests nuevos + 3 adaptados (635 pass) |

> Orden: 1 → 5 → 2 → 3 → 4 (1 crea el índice y el open del ZIP que reutilizan
> los demás; 4 es la única que toca disco en masa y va la última).
> Scripts de la investigación en scratchpad Día41: `identify_zips.py`,
> `identify_arcade.py` (reproducibles).

---

## TEST-CLEAN — Tests que prueban código muerto (auditoría 2026-07-09)

Origen: auditoría de la suite (625 tests / 463 funciones; el resto es
parametrización de funciones puras — sano). Cero skips, todo pasa en ~12 s.
El único problema real: 3 módulos de `src/` sin **ningún** call-site en `src/`
(solo los referencian sus tests), es decir, 29 tests en verde validando código
que la app nunca ejecuta. **Corrección al implementar (2026-07-09)**: la
auditoría solo miró `src/` — `dat_downloader.py` sí tiene consumidor vivo en
`installer/download_dats.py` (build del instalador), así que TEST-CLEAN-1 se
re-alcanzó a solo corregir la doc. Moraleja: buscar consumidores en todo el
repo (installer/, scripts/), no solo en `src/`.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| TEST-CLEAN-1 | ~~Borrar `catalog/dat_downloader.py` + sus 17 tests~~ **Re-alcance: NO borrar** — la auditoría solo buscó consumidores en `src/`; el módulo lo usa `installer/download_dats.py:17` para bundlear DATs en el instalador (PHASE6-2b). Sus 17 tests protegen tooling vivo. Lo que sí era falso: la nota de ARCADE-SETUP-3 mezclaba runtime e installer — corregida. Queda como candidato de consolidación futura: `_run_dat_download` (`web/handlers/scan.py:590`) reimplementa descarga+TTL en runtime; podría importar de `dat_downloader` (refactor, valor bajo). | `catalog/dat_downloader.py` | ✅ (sin borrado — módulo vivo; nota ARCADE-SETUP-3 corregida, rama `chore/test-clean-dead-modules`) |
| TEST-CLEAN-2 | **Borrar `renamer/cue_rewriter.py` + sus 6 tests, y corregir la doc** — la estrategia PSX actual es `move_disc_set_to_subfolder` (`renamer/file_renamer.py:126`): mueve cue+bins a subcarpeta **conservando los nombres de los bins**, así que nunca reescribe el `.cue`. `rewrite_cue` es la estrategia antigua, sin call-sites. Ojo: el Debug Playbook (este archivo) aún decía "Renombrado PSX roto → `cue_rewriter.py`" — pista falsa. | `renamer/cue_rewriter.py`, `tests/test_cue_rewriter.py`, backlog, docs | ✅ módulo+tests borrados; Debug Playbook, `docs/architecture/architecture.md` (árbol + patrón PSX), `docs/glossary.md` y `docs/onboarding.md` actualizados a la estrategia real (rama `chore/test-clean-dead-modules`). `CLAUDE.md` no lo mencionaba |
| TEST-CLEAN-3 | **Borrar `scanner/save_scanner.py`** — sin referencias en `src/` ni tests; los saves los gestiona `sync/`. Código muerto sin más. | `scanner/save_scanner.py` | ✅ borrado + árbol de architecture.md actualizado (rama `chore/test-clean-dead-modules`) |
| TEST-GAP-1 | **`renamer/file_renamer.py` no tiene tests directos** — descubierto al borrar `test_cue_rewriter.py` (el único test "de renombrado PSX" probaba la estrategia muerta). `rename_rom_with_saves` (rename atómico con rollback, patrón crítico de CLAUDE.md) y `move_disc_set_to_subfolder` (sets de disco) solo se ejercitan indirectamente. Añadir tests directos: éxito, rollback ante fallo a mitad, y set cue+bin movido íntegro. | `tests/test_file_renamer.py` (nuevo) | ⬜ |

---

## ONB — Onboarding / Developer Experience (audit 2026-07-04)

Origen: auditoría del proyecto desde la perspectiva de un desarrollador nuevo que no
conoce el proyecto ni el dominio retro-gaming. Roadmap detallado con orden y
estimaciones: `Tareas/diario/archivo/Roadmap-Onboarding.md` (archivado — completado).

| ID | Severidad | Task | Archivo | Estado |
|----|-----------|------|---------|--------|
| ONB-1 | 🔴 Alto | **Falta el archivo `LICENSE`** — el README declara "MIT" pero no existía `LICENSE` en la raíz. Sin él, legalmente el código NO es open source y GitHub no muestra la licencia. | `LICENSE` | ✅ texto MIT estándar (rama `chore/onb-phase1-license-docs-index`, PR #71) |
| ONB-2 | 🔴 Alto | **No hay `CONTRIBUTING.md`** — un dev nuevo no sabe que los PRs van a `develop` (no a `main`), ni los check names de CI, ni que hay pre-commit hooks. Esa info existe pero está en `docs/ci-cd.md` redactada "para Claude". | `CONTRIBUTING.md` | ✅ setup + ramas + checks CI + convenciones + checklist de PR; enlazado desde README (rama `chore/onb-phase2-contributing-config`, PR #72) |
| ONB-3 | 🟠 Medio | **`docs/architecture/architecture.md` desactualizado** — describía `web/response_builders.py` (hoy `web/builders/`), `repository.py` monolítico (hoy mixins), `app.js` monolítico (hoy `static/js/` + `partials/`), BD `library.db` (hoy `library_pc.db` + android), rutas de usuario hardcodeadas y patrones obsoletos (globales de jobs + late imports, sustituidos por `JobManager` + `web/state.py`). | `docs/architecture/architecture.md` | ✅ regenerado desde el código: árbol de módulos real, 2 BDs + 10 tablas, patrones actuales (JobManager, state, seguridad), API → `openapi.json`, historial de refactors (rama `chore/onb-phase3-arch-backlog`) |
| ONB-4 | 🟠 Medio | **`config.toml.example` incompleto** — faltaban secciones que `config.py` ya soporta: `retroachievements.username`, `[inbox]`, `[backup]`, `auto_sync_*`, `[launchers]`, `[notifications]`, `session_ttl`, `[[emulator_paths]]`. Además difería del ejemplo embebido en el README (dos fuentes de verdad, y el del README con el default `host` obsoleto). | `config.toml.example`, `README.md` | ✅ example regenerado desde `load_config()` con todas las claves; README reducido a snippet mínimo + enlace al example (rama `chore/onb-phase2-contributing-config`, PR #72) |
| ONB-5 | 🟡 Medio | **No hay guía de orientación para devs nuevos** — un recién llegado no sabe por dónde empezar a leer, ni que puede levantar el app con datos sintéticos. | `docs/onboarding.md` | ✅ "primeros 30 minutos": pipeline central, mapa de lectura en 6 pasos, flujo request→handler→service→repo, e2e sintético + `/test-pipeline`, Debug Playbook, tests como documentación, primer cambio (rama `chore/onb-phase4-onboarding-glossary`) |
| ONB-6 | 🟡 Medio | **Glosario de dominio inexistente** — el proyecto asume jerga retro que un dev nuevo no domina. | `docs/glossary.md` | ✅ ~30 términos en 4 bloques (identificación, formatos de disco, saves/emulación, infraestructura), cada uno con su "por qué importa en este código"; enlazado desde README, índice de docs y onboarding (rama `chore/onb-phase4-onboarding-glossary`) |
| ONB-7 | ⚪ Bajo | **Índice `docs/README.md` incompleto** — no listaba `ci-cd.md`, `SKILLS-QUICK-START.md`, `arcade-setup.md`, `emulator-compat.md` ni `sync-wifi-sftp.md`; el README raíz tampoco enlazaba al índice de docs. | `docs/README.md`, `README.md` | ✅ sección "Desarrollo" + docs faltantes en índice; sección "Documentación" + licencia enlazada en README (rama `chore/onb-phase1-license-docs-index`, PR #71) |
| ONB-8 | ⚪ Bajo | **Backlog difícil de escanear para alguien nuevo** — mezclaba secciones enteras ya completadas ✅ (SRP, ARC, SEC, UR, REPORT-FIX, DESIGN, PONT, NEW-FEAT…) con lo pendiente. | `Tareas/backlog.md` | ✅ ~440 líneas de secciones completadas movidas a `Tareas/diario/archivo/archivo.md`; el backlog queda solo con pendientes + Debug Playbook (rama `chore/onb-phase3-arch-backlog`) |
| ONB-9 | ⚪ Bajo | **Decisión de idioma/audiencia del README** — todo en español; si el repo también sirve de portfolio internacional, añadir un TL;DR en inglés al inicio (qué es, stack, screenshot) sin traducir el resto. Decisión del usuario. | `README.md` | ✅ TL;DR en inglés (qué es + stack) al inicio del README; sin screenshot porque el repo no tiene ninguno (rama `docs/onb9-readme-english-tldr`) |

> **Completado 9/9** (PRs #71–#74 + ONB-9). Detalle: `Tareas/diario/archivo/Roadmap-Onboarding.md`.

---

## AUD — Auditoría funcional (2026-07-12)

Funciones nuevas detectadas en auditoría de la app completa. Detalle, archivos
y criterios de "hecho" en `Tareas/diario/archivo/Roadmap-Auditoria.md`
(archivado — 6/6 completadas). Orden: 1→6.

| ID | Task | Pilar | Esfuerzo | Estado |
|----|------|-------|----------|--------|
| AUD-1 | **Sync Doctor** — detectar desviación de reloj PC↔consola (mtime gana → reloj mal = pérdida silenciosa), saves con mtime futuro, saves solo en un lado, último sync por juego | Sync | M | ✅ rama `aud-1-sync-doctor` — pendiente validar con consola real |
| AUD-2 | **Verificación post-transferencia** — hash origen/destino tras cada push/pull (`adb shell md5sum`); si difiere, no propagar y reportar; columna `verified` en `save_sync_log` | Sync | S-M | ✅ rama `aud-2-sync-verify` — pendiente validar con consola real |
| AUD-3 | **Papelera unificada con purga** — todo borrado masivo pasa por `_descartados/` (helper `_discard_file` ya existe); purga >30 días en el health-check daemon; contador+vaciar en Settings. Evita repetir INBOX-FIX-5 | Seguridad | M | ✅ rama `aud-3-papelera-unificada` |
| AUD-4 | **`.md` ambiguos del Inbox por CRC** — los 177 varados: lookup contra `crc_index()` ya existente; hit=Mega Drive, miss=quieto. Formaliza el "ZIP-ROUTE-FIX-4" informal | Inbox | S | ✅ rama `aud-4-md-por-crc` — ejecutar el pipeline sobre el Inbox real para los 177 |
| AUD-5 | **Informe de completitud por plataforma (1G1R)** — cruzar `games` matched vs DATs: "SNES: 412/1.748 (24 %)" + CSV de faltantes | Biblioteca | M | ✅ rama `aud-5-completitud-1g1r` (extendió `/api/collection-completeness` ya existente) |
| AUD-6 | **`chdman verify` en health check** — verificación interna de CHDs, checkbox off por defecto | Biblioteca | S | ✅ rama `aud-6-chdman-verify` |

---

## DEVSEL-FIX — Selector de dispositivo (auditoría 2026-07-12)

El selector global PC / Sistema completo / Consola (`_nav.html:69-71`, `setDevice()` en
`main.js:412`, `_deviceRoot()` en `main.js:428`) filtra por `source_root`; el backend elige
BD con `_repo_for_path()` (`builders/common.py:141`): **path vacío → BD del PC**. De ahí
salen todos los fallos. Orden: 1→2 son pérdida de datos potencial, prioridad absoluta.

| ID | Task | Pilar | Esfuerzo | Estado |
|----|------|-------|----------|--------|
| DEVSEL-FIX-1 | **Acciones de duplicados ignoran el dispositivo** — la vista sí lee ambas BDs (`_build_duplicates_two_repos`, `handlers/duplicates.py:50`) pero TODAS las acciones usan `repository` (PC) fijo: `/api/duplicates/delete` (`duplicates.py:70` → `delete_duplicate` borra el archivo por path pero `delete_game(game_id)` contra la BD PC con un id de la BD Android, `services/duplicates_service.py:65`); `/api/duplicates/delete-all` (`duplicates.py:80`) — **en modo consola la UI muestra y confirma duplicados Android pero el backend borra los del PC** (`delete_all_duplicates` recorre `repository.get_duplicate_groups()`); `/api/duplicates/exclude` y los 6 endpoints RA-duplicates, ídem. Fix: enrutar por `get_repo_fn(source_path)` en delete, y pasar `source_root` a delete-all/exclude | Seguridad | M | ✅ PR #118 mergeada — `register()` recibe `get_repo_fn`; delete enruta por `source_path`, delete-all/exclude por `source_root` del body (vacío → ambas BDs: `delete_all_duplicates_multi()`, exclude en ambas con INSERT OR IGNORE); RA discard/resolve enrutan por path. Tras FIX-3 el frontend envía siempre `source_root: ''` (la vista muestra ambos dispositivos). 6 tests handler con 2 repos reales |
| DEVSEL-FIX-2 | **Favoritos/tags/notas/metadatos escriben siempre en la BD del PC** — `/api/toggle-favorite` (`handlers/games.py:502`), `/api/tag` (`games.py:516-519`), `/api/set-metadata` (`games.py:482-491`) usan `repository` fijo; en modo consola el `game_id` viene de la BD Android → escriben en el juego equivocado del PC o en ninguno. El frontend ni envía `source_path` (`games.js:160,686,715,725,784,818`). `/api/set-play-status` sí enruta bien (`games.py:468`) pero el panel de juego llama con `source_path: ''` (`games.js:659`) → siempre PC. Fix: enviar `source_path` desde el frontend y usar `get_repo_fn()` en los 3 handlers | Biblioteca | S-M | ✅ PR #119 mergeada — los 3 handlers enrutan con `get_repo_fn(data["source_path"])`; el panel de juego envía `_gpSrc()` en favorite/tag/notes/metadata/play-status, y la estrella de la lista lleva `data-path`. 4 tests con 2 repos y mismo game_id en ambas BDs |
| DEVSEL-FIX-3 | **"Sistema completo" = solo PC en la práctica** — `_deviceRoot()` devuelve `null` en modo `both` → sin `source_root` → `get_repo_fn("")` → BD PC. Afecta a `/api/plan` y `/api/apply` (`handlers/organize.py:35,107` — la barra dice "Viendo: Sistema completo (PC + consola)", `organize.js:68`, pero solo planifica/renombra el PC), `/api/games` (`games.py:121`), platform-stats/assets/export/disk-usage (`collection.py:35,64,126,159,181,348`), unmatched/completeness (`games.py:640,701`). Única vista correcta: duplicados. **Decisión (2026-07-13): eliminar el modo** — el usuario solo lo usa para duplicados, y esa vista ya cruza ambas BDs por sí sola (`_build_duplicates_two_repos`). Quitar "Sistema completo" del selector (`_nav.html:69-71`, `setDevice()`/`_deviceRoot()` en `main.js:412,428`) y verificar que duplicados no depende del modo `both`. Si algún día se quiere visión global fusionada, se reabre como feature | Biblioteca | S | ✅ PR #120 mergeada — botón eliminado, `setDevice`/estado solo `pc\|anbernic`, duplicados cruza siempre ambas BDs; delete-all/exclude envían `source_root: ''` (ambas BDs), integración con FIX-1 aplicada en el merge |
| DEVSEL-FIX-4 | **Botón "Consola" habilitado por ruta, no por detección** — `dev-anbernic` se habilita si hay `abPath` configurada (`overview.js:424-425`, `config.js:709`) aunque la consola no esté conectada; `deviceConnected` (polling `/api/device-status`, `state.js:52`) solo gatea el badge del Overview, el botón Apply (`organize.js:27-46`) y `doApply` (`organize.js:455`) — `applyKeepBoth` (`organize.js:309`) no comprueba nada. Fix pedido: deshabilitar "Consola" cuando `!deviceConnected`, con tooltip del motivo; decidir si se permite modo solo-lectura de la BD Android offline. (El modo "Sistema completo"/`dev-both` ya no existe — eliminado en FIX-3). **Hecho (2026-07-13)**: gating centralizado en `state.js::updateDeviceButton()` (ruta configurada Y `deviceConnected`, tooltip con el motivo); Overview/Settings marcan `data-has-path`, el polling refresca. Decisión: sin modo solo-lectura offline explícito — si la consola se desconecta estando seleccionada, la vista actual se mantiene pero el botón queda deshabilitado | UX | S | ✅ |

---

## CLOUD-UX — Wizard "Conexión cloud" poco claro (auditoría 2026-07-12)

El asistente OAuth existe (Sync → "Conexión cloud") pero no comunica qué hace ni para qué sirve.

- [ ] **CLOUD-UX-1** — El panel no explica nada: solo "Dropbox — No configurado \[Conectar\]".
  Añadir una línea de contexto: "Conecta tu cuenta para sincronizar saves con la nube.
  Se abrirá el navegador para autorizar — no necesitas API key propia."
  (`web/static/partials/tab-sync.html:3-14`)
- [ ] **CLOUD-UX-2** — El badge "✓ Conectado" solo comprueba que el remote existe en rclone,
  no que su nombre coincida con `saves_remote`/`states_remote` del config. Puedes estar
  "conectado" y que el sync use otro remoto (o ninguno). Mostrar aviso si el remote
  conectado no aparece en las rutas del config. (`web/static/js/tabs/sync.js:1400-1415`)
- [ ] **CLOUD-UX-3** — **Bug**: `_pollCloudAuth()` finaliza con "el primer provider no
  configurado" en vez del que el usuario pulsó. Con Dropbox y GDrive ambos sin configurar,
  pulsar "Conectar" en Google Drive guardaría el token bajo el remote `dropbox`.
  Fix: guardar el `providerId` en `startCloudAuth()` (variable de módulo) y usarlo en el
  finalize. (`web/static/js/tabs/sync.js:1453`)

## VAL-FIX — Hallazgos de la validación con consola real (2026-07-13)

Origen: validación V-AUD-1/V-AUD-2 y smoke DEVSEL con la RG556 por USB (Día42,
sección "Continuación 2026-07-13"). AUD-1 y AUD-2 **validadas** con hardware:
Sync Doctor OK (desviación −1,9 s), sync por cable con 373 copiados / 0 errores
(~338 saves verificados MD5), sin `.part` residuales. Los fallos de abajo
salieron durante esa validación. Orden: 1→2 rompen borrado de duplicados y
papelera — prioridad alta.

| ID | Task | Pilar | Esfuerzo | Estado |
|----|------|-------|----------|--------|
| VAL-FIX-1 | **El scanner no excluye `_descartados/` ni `$RECYCLE.BIN`** — `scanner/rom_scanner.py` no tiene ninguna exclusión de directorios: la papelera de AUD-3 se re-indexa en cada scan (937 filas `_descartados\...` ya en la BD PC, 7-8 filas `$RECYCLE.BIN` en cada BD). Rompe el borrado de duplicados: "eliminar" mueve a `_descartados/`, el siguiente scan lo re-añade y el duplicado reaparece. Fix: excluir `_descartados`, `$RECYCLE.BIN` y `System Volume Information` en el walk del scanner + purga one-shot de las filas existentes | Seguridad | S | ⬜ |
| VAL-FIX-2 | **`library_android.db` contaminada con filas del PC** — 13.164 de 13.376 filas tienen rutas `E:\` (solo 211 son de la SD `H:\`); 6.958 rutas están en AMBAS BDs; 100 % unmatched (el match nunca corrió ahí). Consecuencias: duplicados fantasma imposibles de borrar (la vista empareja el mismo archivo físico consigo mismo y el delete enruta por ruta `E:\` → siempre a la BD PC, la fila Android sobrevive) y acciones de FIX-2 no-op sobre filas contaminadas (la estrella "muerta" del smoke test — el código DEVSEL-FIX-2 funciona, verificado por API con un juego real `H:\`). Fix: (a) limpieza con backup previo — borrar de la BD android las filas cuya ruta no sea de consola (`NOT LIKE 'H:%'` y `NOT LIKE '/storage%'`); (b) investigar el origen (¿la migración V2 copió todo?); (c) guard de dominio al escribir: la BD android solo acepta rutas bajo `anbernic_root`/`/storage` | Seguridad | M | ⬜ |
| VAL-FIX-3 | **Rutas relativas de tools con `/` rompen `subprocess` en Windows** — `CreateProcess` no acepta `tools/adb.exe` (WinError 2 → "consola no conectada" con la consola conectada); sí acepta `tools\adb.exe` o `./tools/adb.exe`. El comentario de `config.py:305` sugiere justo la forma mala. Fix de raíz: normalizar a ruta absoluta contra `project_root` en `load_config()` (`config.py:427-429`, cubre adb/chdman/rclone de golpe). El `config.toml` local ya está parcheado a mano (`tools\\adb.exe`) | Sync | S | ⬜ |
| VAL-FIX-4 | **Auto-sync: 96 `Permission denied` en memcards de DuckStation** — `Android/data/com.github.stenzek.duckstation/` no es accesible por ADB en Android 11+ sin root (scoped storage); el auto-sync lo reintenta en cada conexión (ya fallaba en marzo con 49). Sin pérdida: los pulls fallan y nada se sobreescribe. Fix: excluir/avisar ese mapping en modo ADB y documentar la alternativa (DuckStation Android → exportar memcards a carpeta pública) en `docs/emulator-compat.md` | Sync | S | ⬜ |
| VAL-FIX-5 | **Preview del sync por cable hardcodea "no accesible en modo ADB"** — `_build_cable_sync_preview` (`web/builders/misc.py:81`) nunca implementó el conteo remoto por ADB; el Sync Doctor de AUD-1 ya lo hace bien (226 saves). Fix: reutilizar ese conteo o esconder el preview en modo ADB | UX | S | ⬜ |
| VAL-FIX-6 | **El aviso de ruta SD/MTP se muestra en modo ADB** — al cargar la pestaña, `testCablePath('ab')` valida el campo de ruta SD aunque el Modo ADB esté activo (aviso "Este equipo\RG556\... NO es compatible" irrelevante en ADB). Fix: no validar/ocultar los avisos de la sección SD cuando `_isAdbMode()` (`sync.js:795-796`) | UX | S | ⬜ |
| VAL-FIX-7 | **El sync por cable no registra en `save_sync_log`** — solo `SaveSyncer` (sync cloud) escribe esa tabla; el job de cable verifica MD5 en el transporte (`handlers/sync_cable.py:394,425`, solo saves) pero no deja rastro por archivo, así que el "último sync por juego" del Sync Doctor no refleja syncs por cable. Fix: llamar `log_sync_event(..., verified=)` también desde el job de cable (valor bajo, el resultado del job ya reporta) | Sync | S | ⬜ |

---

## TABS-FIX — Revisión UX/lógica pestañas Juegos/Organizar/Duplicados (2026-07-13)

Revisión pedida por el usuario: solapes entre Organizar y Duplicados, y "borra de la BD
pero no de la carpeta". Juegos está limpia (sin acciones destructivas ni solapes — solo
metadatos/tags/launch). El resto confirmado con archivo:línea. Orden: 1, 5 y 7 primero
(borrados engañosos y saves huérfanos al renombrar); 6 (pantalla única "Revisar copias")
absorbe 2 y 3 — si se hace 6, saltar 2/3; 4 es cosmético y puede ir dentro de 6.

| ID | Task | Pilar | Esfuerzo | Estado |
|----|------|-------|----------|--------|
| TABS-FIX-1 | **Borrado fantasma: si el archivo no existe localmente, se borra solo la fila de BD y se reporta éxito** — `delete_duplicate` (`services/duplicates_service.py:49-59`): `if p.exists()` → mueve a papelera; si no existe, borra la fila igualmente y devuelve `{"deleted": path}`. Mismo patrón en `_discard_file` (`ra_duplicates_service.py:45-51`, "file already gone → clean DB row") y `delete_all_duplicates` (`duplicates_service.py:114-127`, cuenta "skipped"). Las entradas Android escaneadas por ADB guardan rutas de consola (`/storage/...`, `handlers/scan.py:451`) que **nunca** existen como `Path` en Windows → todo "Eliminar" sobre ellas borra solo la BD, el archivo queda en la consola y el siguiente scan lo re-añade (mismo síntoma de reaparición que VAL-FIX-1). También aplica a rutas PC obsoletas. Fix: (a) entradas con ruta de dispositivo → borrar vía ADB (`tools/adb.exe shell rm` con confirmación) o deshabilitar el botón con tooltip "solo accesible con la consola conectada"; (b) ruta local inexistente → devolver aviso "el archivo ya no está en esa ruta; ejecuta un scan" en vez de éxito silencioso | Seguridad | M | ⬜ |
| TABS-FIX-2 | **"Quedarse con la versión con logros RA" existe 3 veces con 3 endpoints** — (1) Organizar → botón "Resolver con RA" (`tab-plan.html:38` → `doResolveRaConflicts`, `duplicates.js:277` → `/api/apply-ra-conflicts`); (2) Duplicados → sección "Duplicados por versión — sin logros RA" (`tab-duplicates.html:14-24` → `/api/ra-duplicates` + discard/discard-all); (3) Duplicados → duplicados semánticos con "Resolver: mantener éste" (`duplicates.js:140-166,424-462` → `/api/resolve-duplicate-ra`). (2) y (3) detectan lo mismo (mismo título normalizado, distinto hash, uno con RA) en la **misma pestaña** con dos UIs y dos endpoints. Fix: fusionar (2)+(3) en una sola lista "mismo juego, versiones distintas" con el criterio RA integrado (lógica canónica ya en `ra_duplicates_service.py`); (1) se queda en Organizar (resuelve conflictos del plan, contexto distinto) pero mover `doResolveRaConflicts` de `duplicates.js` a `organize.js` | UX | M | ⬜ |
| TABS-FIX-3 | **Dos botones vecinos con criterio de conservación contradictorio en colisiones** — en el aviso de colisión de Organizar, "Eliminar duplicados" (`organize.js:364-425`, `deleteCollisionDuplicates`) conserva el índice 0 del DOM **arbitrariamente**, ignorando RA, mientras el botón "Resolver con RA" de al lado prioriza logros (preferencia registrada del usuario). Además borra en bucle llamando a `/api/duplicates/delete` por fila. Fix: eliminar el botón "Eliminar duplicados" (el flujo RA + "Descartar" por fila ya cubren el caso) o hacer que conserve por criterio RA | UX | S | ⬜ |
| TABS-FIX-4 | **Los textos de borrado mienten desde AUD-3** — "Se eliminarán N archivos del disco… Esta operación no se puede deshacer" (`duplicates.js:70,117,145`, `tab-duplicates.html:4,9,20`) cuando en realidad todo va a `_descartados/` (recuperable, purga a 30 días); solo el confirm de `deleteRaDuplicate` (`duplicates.js:255`) lo dice bien. Y el toast "Liberados: X" (`duplicates.js:89`) usa `freed_bytes` que no se libera hasta la purga (mover dentro del mismo volumen no libera nada). Fix: unificar todos los confirms/toasts a "se moverán a `_descartados/` (recuperable 30 días)" y renombrar "Liberados" a "Recuperables tras purga" | UX | S | ⬜ |
| TABS-FIX-5 | **"Eliminar todos los duplicados" ignora el filtro de plataforma** — el confirm cuenta los botones visibles en el DOM (`duplicates.js:65`) pero envía siempre `source_root: ''` (`duplicates.js:76`) → `delete_all_duplicates_multi` recorre TODOS los grupos de ambas BDs (`handlers/duplicates.py:87-93`). Con el filtro en "SNES" el usuario confirma "3 archivos" y se descartan los duplicados de todas las plataformas. Fix: pasar la plataforma filtrada al endpoint y filtrar en `delete_all_duplicates`, o contar server-side antes del confirm | Seguridad | S | ⬜ |
| TABS-FIX-6 | **Pantalla única "Revisar copias" (diseño 2026-07-13)** — fusionar en una sola vista los 4 solapes actuales (duplicados SHA1, duplicados semánticos, versiones RA, colisiones del plan): una cola de revisión agrupada **por juego**, cada grupo con sus copias listadas (badge del motivo: "idéntico SHA1" / "otra versión" / "colisión de nombre", badge 🏆 RA, badge dispositivo), una **recomendación precalculada** con criterio único (RA gana > mejor nombrada > primera; lógica ya en `ra_duplicates_service.py`) y acciones [Aplicar] [Elegir otra] [Copia intencional] + "Aplicar todas las recomendaciones (N)" arriba. Organizar pasa a 2 pasos: "Renombrar" y "Revisar copias"; la pestaña Duplicados desaparece. Backend: endpoint agregador que fusione `/api/duplicates` + `/api/ra-duplicates` + conflictos del plan; los endpoints de acción actuales sirven tal cual. **Implementa TABS-FIX-2 y TABS-FIX-3 de golpe** y resuelve de paso TABS-FIX-5 (el "aplicar todo" opera sobre los grupos renderizados). Diseño detallado: sesión 2026-07-13 | UX | L | ⬜ |
| TABS-FIX-7 | **El rename no renombra saves/states en carpetas centrales de RetroArch** — `rename_rom_with_saves` solo busca compañeros en `source.parent` (`renamer/file_renamer.py:49-53`); si RetroArch usa Savefile/Savestate Directory central (su default, y lo que pide STRUCT-4: `E:\Carpetas anbernic\saves\`), el save/state conserva el stem viejo → huérfano, RetroArch crea uno vacío = pérdida de progreso percibida (Pilar 3). La app ya conoce esas rutas (`_state_search_dirs`, `handlers/games.py:22-35`, busca en `retroarch_path/states` para miniaturas) pero el renamer no. Extras: `.state.auto` nunca casa (suffix parseado `.auto`, stem `X.state`) y solo hay `.state1`/`.state2` en la lista (`config.py:529-530`) — slots 3+ huérfanos. Fix: en `rename_rom_with_saves`, buscar compañeros también en las carpetas centrales de config (saves/states de RetroArch + `local_dir` del sync), y matching por prefijo de stem para cubrir `.state.auto`/`.stateN` | Sync/Seguridad | M | ✅ |

---

## CABLE-UX — Auditoría de Cable Sync: simplificar la experiencia (2026-07-13)

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

## INICIO-UX — Auditoría de la pestaña Inicio (2026-07-13)

Auditoría UX de Inicio (`tab-overview.html`, `js/tabs/overview.js`) desde la
perspectiva de un usuario nuevo. Detalle completo, archivo:línea y fases en
`Tareas/Roadmap-Inicio-UX.md`. Hallazgos clave: los 3 botones rápidos del
dashboard están **rotos** (comillas `\'` estilo Python servidas tal cual al
navegador → SyntaxError), los canvas usan `var(--c-*)` como fillStyle (canvas
no resuelve variables CSS → heatmap y gráfico mensual pintan colores
incorrectos), y hay dos heatmaps de actividad duplicados. Incluye la petición
del usuario: tarjetas explicando los archivos no-gaming (BIOS, assets, saves,
infra MAME, basura) reutilizando las categorías de `builders/folders.py`.

| ID | Task | Esfuerzo | Estado |
|----|------|----------|--------|
| INICIO-UX-F1 | Fase 1 — bugs visibles: onclick rotos del dashboard (`tab-overview.html:26-28`), hex literales en canvas (`overview.js:166,270`), eliminar heatmap canvas duplicado (S36-2) | XS | ⬜ |
| INICIO-UX-F2 | Fase 2 — idioma: tarjetas "Games/Matched/Unmatched/wasted" → español (`overview.js:449-455,537-543`), unificar "Escanear", "Corregir plataformas" | S | ⬜ |
| INICIO-UX-F3 | Fase 3 ⭐ — sección "Además de juegos…": tarjetas explicativas de BIOS / assets / saves / infra MAME / basura con qué es + NO borrar/borrable + link al tab correspondiente; conteos desde `/api/status` y junk-scan (`builders/folders.py:51-96`) | M | ⬜ |
| INICIO-UX-F4 | Fase 4 — errores accionables: mensajes en español + Reintentar (`overview.js:514,546,668`), wizard sin `alert()` (`:811,836`), CTA en "salud: sin datos" | S | ⬜ |
| INICIO-UX-F5 | Fase 5 — rendimiento y pulido: un solo fetch de `/api/status` (hoy 3) y `/api/games?limit=10000` (hoy 3), hover en tarjetas clicables, placeholder de imagen | S-M | ⬜ |

---

## CLOUD-UX — Auditoría de la pestaña Cloud: UX/UI y lógica (2026-07-13)

Auditoría de la pestaña Cloud (`tab-sync.html`, `js/tabs/sync.js`, `main.js`,
`jobs.js`, `handlers/sync_cloud.py`, `handlers/cloud_auth.py`). Hallazgo
central: **el camino recomendado está roto de punta a punta** — el botón
"Usar para saves + states (recomendado)" lanza ReferenceError; si existiera,
guardaría un remote sin `:`; y si guardara bien, "Sincronizar" fallaría porque
el backend exige `[[sync.sources]]` antes de mirar los remotes implícitos.
Detalle, archivos y criterios de "hecho" en `Tareas/Roadmap-Cloud-UX.md`.
Orden: 1-6 son bugs, 7-12 UX. Todo pilar 3.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| CLOUD-UX-1 | **Tres funciones inexistentes en `window`** — `applyRcloneSavesStates()` (botón "recomendado", `tab-sync.html:165`) existe en `sync.js:556` pero no está exportada ni en `main.js`; `backupNow()` (`tab-sync.html:42`) no existe (solo `API.backupNow`, `api.js:142`); `loadManualBackups` no existe → `main.js:479` lanza ReferenceError (`?.()` no protege identificadores no declarados) y **`loadCloudAuthStatus()` nunca corre al abrir la pestaña** ("Comprobando…" eterno); `jobs.js:439` TypeError tras cada backup. Fix: escribir `backupNow`/`loadManualBackups`, exportar las tres + window | Bug | S | ⬜ |
| CLOUD-UX-2 | **Los botones "Guardar" del panel rclone escriben remotes sin `:`** — `/api/rclone-status` devuelve remotes con `rstrip(":")` (`sync_cloud.py:143`) y `applyRcloneRemote`/`applyRcloneSavesStates` concatenan `remote + path` (`sync.js:543,562-563`) → guardan `dropboxRetroSync/saves`. "Verificar conexión" sí funciona (backend re-añade `:`, `sync_cloud.py:196`): test OK + guardado roto. La preselección (`sync.js:489-491`) compara con `:` y nunca coincide | Bug | XS | ⬜ |
| CLOUD-UX-3 | **"Sincronizar" falla con la config recomendada** — `_do_sync` corta con "No hay fuentes de sync configuradas… [[sync.sources]]" (`sync_cloud.py:246-251`) ANTES del bloque D2 de remotes implícitos `saves_remote`/`states_remote` (`:346-366`). El aviso del frontend tiene el mismo punto ciego (`sync.js:34-43`). Fix: error solo si no hay ni sources ni remotes implícitos | Bug | S | ⬜ |
| CLOUD-UX-4 | **El wizard OAuth puede escribir el token en el provider equivocado** — `_pollCloudAuth` finaliza contra "el primer provider no configurado" (`sync.js:1532-1543`); con ambos sin configurar, conectar Google Drive escribe el token bajo el remote `dropbox` (`_PROVIDERS` lista dropbox primero, `cloud_auth.py:23-26`). Fix: retener el provider iniciado (mejor en `/api/cloud-auth/poll`); de paso, guard de flujo concurrente y cancel que mate el subprocess | Bug | S | ⬜ |
| CLOUD-UX-5 | **`sync_result` sin guard `result_ts`** — `jobs.js:104-105` llama `_renderSyncResult` en cada tick (scan/match/backup sí usan `_shownResultTs`); la notificación de escritorio "Sync completado" (`sync.js:1452-1462`) se re-dispara cada 2 s mientras el polling siga vivo por otro job. Fix: mismo guard + refrescar `loadSync()` al consumir resultado | Bug | XS | ⬜ |
| CLOUD-UX-6 | **Modo TV roto** — `tvStartSync` postea a `/api/do-sync` (`sync.js:334`); el endpoint real es `/api/sync` (`sync_cloud.py:90`). El flujo táctil ANBERNIC-TV muere con error siempre | Bug | XS | ✅ (arreglado en feature/anbernic-ux — `/api/sync`) |
| CLOUD-UX-7 | **Script bootstrap Termux hardcodea `dropbox:/RetroSync/saves`** — `_build_bootstrap_script` (`sync_cloud.py:666`) ignora `config.sync.saves_remote` y `save_extensions`; con gdrive u otra carpeta la consola bisync-ea contra un remote inexistente. Además `rclone bisync` vs `SaveSyncer` = dos motores con políticas de conflicto distintas. Fix mínimo: inyectar remote y extensiones reales | Sync | S | ✅ (resuelto por ANBERNIC-UX-1: generador canónico con remotes de config y `copy --update`) |
| CLOUD-UX-8 | **Reordenar la pestaña** — la config imprescindible (remote+carpeta) está al fondo tras "⚙ Verificar rclone" (`tab-sync.html:106-178`); 4 superficies de configuración solapadas; los comparadores PC-vs-consola (`:62-104`) son herramientas de dispositivo, no de cloud. Fix: checklist de setup arriba (Conectar → Carpeta → Probar, colapsable cuando todo verde), luego Sincronizar+estado, backup al final; comparadores a Cable/Herramientas | UX | M | ⬜ |
| CLOUD-UX-9 | **"Conectado" ≠ "sync configurado"** — el wizard OAuth acaba en "✓ Conectado" pero nadie configura `saves_remote`: verde + error de fuentes al sincronizar. Fix: tras finalize, ofrecer "Usar `<remote>:RetroSync` para saves+states" a un clic (reutiliza `applyRcloneSavesStates` tras CLOUD-UX-1/2) y mostrar el destino activo en la tarjeta (`_rcloneActiveTargetHtml` ya lo calcula, `sync.js:447-459`) | UX | S | ⬜ |
| CLOUD-UX-10 | **Mensajes que mandan a editar config.toml / a Settings** — "configura [[sync.sources]] en config.toml" (`sync.js:38,43`) y el error de `loadSync` enlaza a Settings (`sync.js:65`) cuando el panel rclone está en esta misma pestaña. Fix (tras CLOUD-UX-3): apuntar al bloque de setup de la propia pestaña | UX | XS | ⬜ |
| CLOUD-UX-11 | **"Estado de saves" y backups no cargan solos** — exigen clic "↻ Cargar" (`tab-sync.html:56`) siendo lecturas locales baratas (`/api/save-comparison`, `games.py:367`). Fix: auto-cargar en `showTab('sync')`, ↻ queda para refrescar | UX | XS | ⬜ |
| CLOUD-UX-12 | **`sync-decisions` muerto: el resultado no dice qué archivos se movieron** — el backend envía las decisiones por archivo (`sync_cloud.py:323-327`) y el div existe (`tab-sync.html:33`) pero nadie lo rellena; `_renderSyncResult` solo pinta totales (`sync.js:1440-1466`). Fix: listar acción+ruta por fuente, conflictos destacados; en dry run es el "plan" antes de sincronizar | UX | S | ⬜ |

---

## ANBERNIC-UX — Auditoría de la pestaña Anbernic: UX/UI, lógica y seguridad (2026-07-13)

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
| ANBERNIC-UX-9 | **`/api/local-url` gasta un `subprocess` en cada llamada** — `_check_firewall` (`web/lan.py:52`, invocado desde `handlers/esde/system.py:59,66`) lanza `netsh advfirewall firewall show rule` (spawn de proceso, decenas de ms en Windows) en cada `GET /api/local-url`; tras ANBERNIC-UX-7 ese endpoint se llama también desde `loadAnbernicTab()` y `tvToggleSetup()` (`sync.js:410,283`), no solo desde Settings. Fix: cachear el resultado unos segundos/minutos en memoria (el estado del firewall no cambia entre refrescos de pestaña) o solo comprobarlo si `lan_bound=true` y ha pasado un TTL desde la última comprobación | Rendimiento | XS | ⬜ |
| ANBERNIC-UX-10 | **Token de setup: un solo slot global, no por sesión** — `_mint_setup_token` (`handlers/sync_cloud.py:141`) sobreescribe `_state._anbernic_setup_token` (`web/state.py:40`) en cada llamada a `GET /api/anbernic-setup-token`; si se abre la pestaña Anbernic en dos pestañas del navegador a la vez, el segundo mint invalida el comando ya copiado del primero (403 al ejecutarlo). Bajo impacto (app de un solo usuario/escritorio) pero fix barato: token efímero por request en vez de global, o lista de tokens válidos con TTL en vez de un único slot | Bug | XS | ⬜ |

Validación en hardware pendiente: comprobar en la RG556 si Termux limpio trae
`curl` (el one-liner `curl -s …/s \| bash` falla si no; la guía manual
`docs/sync/Guia-Termux-Anbernic.md` no lo usa).

---

## HERR-UX — Auditoría de la pestaña Herramientas: UX/UI (2026-07-13)

Auditoría de la pestaña Herramientas (`tab-tools.html` + JS repartido en
`esde.js`, `config.js`, `duplicates.js`, `sync.js`, `jobs.js`). Patrón
dominante: **la migración de frontend.py a parciales dejó HTML y JS apuntando
a IDs distintos** — tres paneles enteros tienen botones que no hacen nada al
pulsarlos (`getElementById` → null → return silencioso): Informe de
biblioteca, Saves huérfanos y el render de resultados del Health Check.
Detalle, archivo:línea y fases en `Tareas/Roadmap-Herramientas-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| HERR-UX-1 | **Panel "Informe de biblioteca" desconectado** — `generateReport` renderiza en `library-report-content` (no existe en ningún parcial, `esde.js:1207-1348`); el HTML usa `report-content`/`rpt-tab-*` (`tab-tools.html:116-150`) y sus 6 sub-tabs pasan `'zips'…'chd'` mientras el switch JS solo maneja `'overview'…'orphans'`; `btn-export-report` nunca se des-oculta. "Generar informe" no hace nada visible. Fix: reconectar a una sola versión o dejar solo los botones de informe HTML servidor (que sí funcionan, `main.js:583`) | Bug | M | ⬜ |
| HERR-UX-2 | **"Buscar huérfanos" no hace nada** — `doFindOrphans` es un stub TODO que además escribe en `orphans-result-content` (HTML: `orphan-result`, `esde.js:903`); `orphan-path` no lo lee nadie; las acciones Mover/Eliminar existen pero son inalcanzables (`esde.js:916-980`). El dato ya está en `/api/library-report` (clave `orphans`) — reutilizar | Bug | S | ⬜ |
| HERR-UX-3 | **Resultados del Health Check nunca se muestran** — todo el render va a `health-result-content`; el HTML tiene `health-result` (`esde.js:495,512,530` vs `tab-tools.html:75`). La barra de progreso funciona (jobs.js usa IDs correctos) y al terminar el resultado desaparece sin rastro. Fix de 1 línea: unificar el ID | Bug | XS | ⬜ |
| HERR-UX-4 | **"Resolver todos" del Library Doctor invisible para siempre** — nace `class="btn hidden"` (`.hidden` con `!important`, `app.css:1225`) y el JS intenta mostrarlo con `style.display` (`esde.js:1039`), que no vence al `!important`. `doctorResolveAll` es código muerto. Fix: `classList.toggle('hidden', …)` | Bug | XS | ⬜ |
| HERR-UX-5 | **"¿Qué catálogos me faltan?" descarga TODOS los DATs sin preguntar** — tras el diagnóstico lanza `POST /api/download-dats {all:true}` automáticamente (`esde.js:1160-1166`). Fix: dos pasos — diagnóstico puro + botón "Descargar catálogos que faltan (N)" + CTA hacia Identificar al acabar | UX | S | ⬜ |
| HERR-UX-6 | **Mojibake «ྠltimo»** — `&#xfa0;` (letra tibetana) en vez de `Ú` en la programación del Health Check (`config.js:241`) | Bug | XS | ⬜ |
| HERR-UX-7 | **Contexto PC/Android incompleto** — `setToolsContext` (`duplicates.js:345-372`) rellena el ID inexistente `health-path`, toca inputs de la pestaña Formatos (`zip-path`, `chd-path`) sin que se vea, no actualiza `report-path`/`m3u-path`/`verify-multidisc-path`, y pisa rutas escritas a mano sin avisar. Mover la función a `tools.js` al tocarla | UX | S | ⬜ |
| HERR-UX-8 | **Doctor: "✓ Resolución completada" aunque haya fallos** — `doctorResolveAll` traga errores y no recalcula el resumen; filas solo se atenúan (`esde.js:1095-1117`). Fix: contar ok/fallos y relanzar `doLibraryDoctor()` | UX | XS | ⬜ |
| HERR-UX-9 | **Batch "Aplicar todo": sin cancelar ni progreso real** — `alert()` nativos, botón deshabilitado sin cambiar texto, sin "paso 2 de 5", polling sin timeout, Scraper sin validar credenciales SS (`config.js:312-395`) | UX | S | ⬜ |
| HERR-UX-10 | **Labels inconsistentes** — «Iniciar Health Check» vs «Comprobar biblioteca» (error path `esde.js:507,519`); «Settings» vs «Ajustes» (`tab-tools.html:92` vs `:183`); títulos en inglés (Library Doctor, Health Check) | UX | XS | ⬜ |
| HERR-UX-11 | **Estados de carga eternos + pulido** — «Verificando API key…» nunca cambia si `/api/config` falla (`config.js:302` catch silencioso); toasts con tipos inexistentes `'success'`/`'warn'` sin color (`app.css:646-648`); export HTML con `var(--c-*)` sin definir fuera de la app (`esde.js:1372`); patch list no auto-escanea y su 📂 abre selector de carpetas para elegir una ROM | UX | S | ⬜ |

---

## FORMATOS-UX — Auditoría de la pestaña Formatos: UX/UI (2026-07-13)

Auditoría de la pestaña Formatos (`tab-formats.html` + JS repartido en
`tools.js`, `esde.js`, `config.js`, `duplicates.js`). A diferencia de
Herramientas, aquí casi todos los botones sí están conectados; los problemas
son un panel-stub ("Análisis de carpeta"), el selector de contexto
PC/Android pisando rutas de esta pestaña sin avisar en cada apertura, y
diálogos nativos (`alert`/`confirm`) en vez de los componentes propios de la
app. Detalle, archivo:línea y fases en `Tareas/Roadmap-Formatos-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| FORMATOS-UX-1 | **Selector de contexto pisa rutas sin avisar** — `setToolsContext` (`duplicates.js:345-367`) sobrescribe incondicionalmente `zip-path`/`chd-path`/`folder-analysis-path` cada vez que se abre Formatos o Herramientas (`main.js:485-486`), rellena el ID muerto `health-path` y deja huérfanos `cso-path`/`verify-chd-path`/`m3u-path`. Relacionado con HERR-UX-7 (misma función). Fix: solo rellenar si está vacío + cubrir todos los paths | Bug | S | ⬜ |
| FORMATOS-UX-2 | **"Análisis de carpeta" es un panel-stub** — `doFolderAnalysis` (`esde.js:1120-1131`) ignora la ruta y siempre renderiza «Funcionalidad pendiente», pese a tener input, botón y persistencia completos (`tab-formats.html:192-204`). Mismo patrón que HERR-UX-2. Fix: implementar `/api/folder-analysis` o retirar el panel | Bug | M | ⬜ |
| FORMATOS-UX-3 | **`alert()`/`confirm()` nativos en 9+ sitios** — `doConvertChd/doConvertCso/doExtractZip/doCleanupZips/doCleanupCueBin/doGenerateM3U/doVerifyMultidisc/doVerifyChd` (`tools.js`) usan diálogos nativos pese a existir `showToast` y `_showConfirm` propios de la app. Fix: sustituir por los componentes propios | UX | S | ⬜ |
| FORMATOS-UX-4 | **Botón "library_root" muestra el nombre de la variable interna** — literal en inglés/snake_case en 5 paneles (`tab-formats.html:16,58,88,148,198`) en vez de una etiqueta legible en español | UX | XS | ⬜ |
| FORMATOS-UX-5 | **Escaneos síncronos sin bloqueo de botón** — "Generar M3U", "Verificar" (multi-disco), "Escanear" (N64) y "Generar .lpl" no deshabilitan su botón durante el fetch, a diferencia de CHD/CSO/ZIP (jobs con polling) y de `autodetectM3UFolders`, que sí lo hace bien | UX | S | ⬜ |
| FORMATOS-UX-6 | **Filtro "solo errores" con default distinto entre paneles gemelos** — CHD conversión: marcado solo si hay fallos; CHD verificación: siempre marcado (`tab-formats.html:75` vs `tools.js:76-78`) | UX | XS | ⬜ |
| FORMATOS-UX-7 | **Pulido: mensajes de error sin guía, resultados vacíos sin sugerencia, botón "library_root" silencioso en fallo, persistencia de rutas incompleta** — `doConvertChd/doConvertCso/doExtractZip/doVerifyChd` sin pista accionable en el catch (a diferencia de los cleanup); "sin resultados" en M3U/N64 sin sugerir revisar ruta o nomenclatura; `fillToolPath` traga errores en silencio (`config.js:406-411`); `_initToolPath` no cubre `cso-path/verify-chd-path/verify-multidisc-path/lpl-output-dir/n64-path` (`config.js:295-301`) | UX | S | ⬜ |

---

## JUEGOS-UX — Roadmap: logros por juego + playtime automático (2026-07-13)

Roadmap de feature nueva (no auditoría de bugs) para la pestaña Juegos.
Verificado en código: el resumen de logros (`X/Y logros`) ya existe vía
`/api/ra-user-progress`, pero RA devuelve la lista completa de logros
individuales y el backend la descarta (`games.py:507-514`) — nunca se
guardó ni parseó en ningún punto de `retroachievements/`. Y el control de
"Tiempo jugado" del panel de juego (`gp-playtime-wrap`) es una simulación
total: `gpLogPlaytime()` (`games.js:531-542`) no llama a ninguna API, solo
hace `alert()` y limpia los campos — no hay columna de minutos en la BD
(`play_history.py` solo tiene `play_count`/`last_played_at`). Detalle,
archivo:línea y fases en `Tareas/Roadmap-Juegos-UX.md`. Sustituye/desarrolla
`MEJ-1`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| JUEGOS-UX-1 | **Backend: exponer logros individuales** — `/api/ra-user-progress` (`games.py:461-516`) ya recibe el array `Achievements` de RA (título, descripción, puntos, badge, fecha de desbloqueo) y lo descarta; añadirlo a la respuesta manteniendo el cache 1h existente | Feature | S | ⬜ |
| JUEGOS-UX-2 | **Frontend: lista de logros desbloqueados/pendientes en el panel de juego** — nuevo bloque bajo `gp-ra-user-progress` (`_foot.html:138`), reutilizando el patrón de lista colapsable ya usado en `tools.js:444` (`_faCollapsibleList`) | Feature | M | ⬜ |
| JUEGOS-UX-3 | **Perf: lazy-load de iconos de logros** — `loading="lazy"` en los badges; reutilizar el patrón TTL de `.rommgr/ra_cache/` en vez de un cache nuevo | Feature | XS | ⬜ |
| JUEGOS-UX-4 | **🔴 El control manual de playtime no guarda nada** — `gpLogPlaytime()` solo hace `alert()`, sin `apiPost` (`games.js:531-542`); ocultarlo o marcarlo como no persistente hasta que exista el tracking automático | Bug | XS | ⬜ |
| JUEGOS-UX-5 | **Esquema de datos: minutos separados por origen (PC/Android)** — `playtime_minutes_pc` + `playtime_minutes_android` en vez de un total único, para poder sumar sin duplicar ni sobrescribir al sincronizar | Feature | S | ⬜ |
| JUEGOS-UX-6 | **Scanner `.lrtl` de RetroArch (PC)** — módulo stdlib-json sobre `playlists/logs/<Core>/<rom>.lrtl`, mismo matching que `record_play_session` (`play_history.py:26-27`), como job de background con polling | Feature | M | ⬜ |
| JUEGOS-UX-7 | **Sync de `.lrtl` desde Anbernic** — nuevo `SyncSource` (mismo patrón que MEJ-4 para `.cht`); los `.lrtl` de Android acumulan en `playtime_minutes_android`, nunca sobrescriben `_pc` | Feature | S | ⬜ |
| JUEGOS-UX-8 | **UI: total automático PC+Anbernic sin inputs** — sustituir `gp-playtime-wrap` (`_foot.html:163-175`) por "X h Y m totales · PC: A h · Anbernic: B h", recalculado solo tras cada sync/scan | Feature | S | ⬜ |
| JUEGOS-UX-9 | **No aparentar precisión mientras el scanner no esté completo** — indicar en la UI si el dato es parcial (solo PC, sin datos de Anbernic aún) | UX | XS | ⬜ |

---

## ASSETS-UX — Auditoría de la pestaña Assets: UX/UI (2026-07-13)

Auditoría de la pestaña Assets (`tab-assets.html` + `loadAssets()` en
`sync.js:70-111`, la pestaña más pequeña auditada hasta ahora). Hallazgo
central: `_deviceRoot()` (`main.js:430-435`) no tiene el mismo fallback a
localStorage que ya usa el texto de la barra de contexto (`sync.js:85`) —
la cabecera puede decir "Viendo: Android" mientras la tabla muestra datos
del PC, sin ninguna pista de que no coinciden. Es una función compartida:
el mismo bug aplica a Colección, Organizar y Juegos. Detalle, archivo:línea
y fases en `Tareas/Roadmap-Assets-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| ASSETS-UX-1 | **La ruta mostrada como "Viendo: X" puede no ser la que se consulta** — `_deviceRoot()` (`main.js:430-435`) no tiene fallback a `localStorage('anbernic_path')` a diferencia del texto de la barra (`sync.js:85`); afecta también a `collection.js`, `organize.js`, `games.js` que usan la misma función | Bug | S | ⬜ |
| ASSETS-UX-2 | **"Ejecuta un Scan" también sale cuando el filtro simplemente no tiene resultados** — el filtro se aplica antes de comprobar vacío (`sync.js:92-94`); "Solo huérfanos" sin ninguno (buena noticia) muestra el mismo mensaje que "nunca escaneado" | UX | XS | ⬜ |
| ASSETS-UX-3 | **Error sin guía, a diferencia del resto del mismo archivo** — catch de `loadAssets` (`sync.js:108-109`) solo muestra `e.message`; el catch de `loadSync` unas líneas arriba (`sync.js:65`) sí da pista + enlace a Ajustes | UX | XS | ⬜ |
| ASSETS-UX-4 | **Columna "Huérfanos" sin ninguna acción asociada** — solo informativo, sin enlace para ver/mover/eliminar los archivos concretos (`sync.js:104`) | UX | S | ⬜ |
| ASSETS-UX-5 | **Estado vacío sin enlace a la acción que lo resuelve** — "Ejecuta un Scan" es texto plano sin botón a Organizar (`sync.js:94`) | UX | XS | ⬜ |

---

## COLECCION-UX — Auditoría de la pestaña Colección + ¿fusión con Juegos? (2026-07-13)

El usuario preguntó si Colección y Juegos deberían fusionarse. Comparando el
código: ambas pintan una galería casi idéntica (mismo endpoint `/api/games`,
mismo panel de detalle `openGamePanel`), pero Colección solo expone 3 de los
9 filtros de Juegos — es un subconjunto duplicado, no una vista distinta. Lo
que Colección aporta de verdad son sus paneles de análisis agregado (Stats,
Disco, Diff PC/Android, Completitud, Wishlist), que no tienen sentido dentro
de la ficha de un juego. **Recomendación: no fusionar mecánicamente — retirar
la galería duplicada de Colección y dejar la pestaña como dashboard de
análisis puro.** Razonamiento completo y hallazgos de bugs en
`Tareas/Roadmap-Coleccion-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| COLECCION-UX-1 | **Botón "🏥 Health" no hace nada** — `togglePlatformHealth()` se llama sin argumento (`tab-collection.html:22`), nunca alterna el panel (a diferencia de sus hermanos en `collection.js`), y escribe en `#platform-health-content` que no existe (real: `#ph-table`); `loadPlatformHealth()` es además un TODO puro (`esde.js:632-661`). Cuarta ocurrencia del patrón HTML/JS-ID-mismatch (HERR-UX-1/2/3, FORMATOS-UX-2) | Bug | S | ⬜ |
| COLECCION-UX-2 | **Dos galerías divergentes del mismo dato** — Colección (`col-grid`) y la vista cuadrícula de Juegos comparten endpoint y panel de detalle pero Colección solo tiene 3 de los 9 filtros de Juegos; decisión de producto antes de tocar código (ver recomendación de fusión) | Decisión | M | ⬜ |
| COLECCION-UX-3 | **"Exportar CSV" da resultados distintos según la pestaña** — el export de Juegos no manda `root` (`tab-games.html:46-47`), el de Colección sí (`collection.js:311-313`); mismo botón, mismo texto, distinto resultado sin avisar | Bug | XS | ⬜ |
| COLECCION-UX-4 | **"ROMs faltantes" es código muerto con mejor funcionalidad que el panel activo** — `missing-section`/`loadMissingRoms()` (`tab-collection.html:113-124`, `collection.js:65-88`) nunca se invoca desde ningún botón, pero tiene wishlist + enlace IA + copiar búsqueda que el panel "Completitud" vivo no tiene | UX | S | ⬜ |
| COLECCION-UX-5 | **Pulido: 5 acordeones sin "cerrar todos" + filtro de plataforma duplicado con estilo distinto al de Juegos** (`collection.js:182-197` vs `games-platform` select) | UX | XS | ⬜ |

---

## DUPLICADOS-UX — Auditoría de la pestaña Duplicados: UX/UI (2026-07-13)

Auditoría de la pestaña Duplicados (`tab-duplicates.html` +
`js/tabs/duplicates.js`). A diferencia de otras pestañas, aquí no hay
botones muertos — el problema central es un desajuste real entre lo que se
confirma y lo que se borra: el filtro de plataforma es solo visual,
`deleteAllDuplicates()` cuenta filas del DOM ya filtrado para el diálogo de
confirmación pero el backend borra duplicados de **toda** la biblioteca sin
recibir ningún filtro. Detalle, archivo:línea y fases en
`Tareas/Roadmap-Duplicados-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| DUPLICADOS-UX-1 | **"Eliminar todos" borra más de lo que confirma con un filtro de plataforma activo** — el filtro solo afecta al render (`duplicates.js:381-386`); `deleteAllDuplicates()` cuenta filas del DOM filtrado para el diálogo pero llama a `/api/duplicates/delete-all` con `source_root:''` (`duplicates.js:64-109`), que borra duplicados de toda la biblioteca sin filtro de plataforma posible en el backend (`services/duplicates_service.py:90`) | Bug | S | ⬜ |
| DUPLICADOS-UX-2 | **Toasts rotos: `showToast(msg, true/false)` en vez del string esperado** — `deleteAllDuplicates` (líneas 67,103) y `deleteDuplicate` (línea 134); el resto del mismo archivo usa `'ok'/'err'/'info'` correctamente | Bug | XS | ⬜ |
| DUPLICADOS-UX-3 | **Mensajes contradictorios sobre si el borrado se puede deshacer** — 4 acciones dicen "no se puede deshacer" pese a usar la misma papelera `_descartados/` (AUD-3) que `deleteRaDuplicate`, cuyo mensaje sí lo menciona ("difícil de deshacer") | UX | S | ⬜ |
| DUPLICADOS-UX-4 | **`confirm()` nativo en 2 de 6 sitios pese a tener `_showConfirm` ya importado** — `deleteRaDuplicate` (línea 255) y `discardAllRaDuplicates` (línea 323) | UX | XS | ⬜ |
| DUPLICADOS-UX-5 | **"Copia intencional ✓" es permanente sin UI para revisarla o deshacerla** — `markAsIntentionalCopy` excluye un grupo para siempre; no existe ninguna lista de grupos excluidos en la app | UX | S | ⬜ |
| DUPLICADOS-UX-6 | **"Tools" en inglés (y nombre de pestaña incorrecto) en 2 sitios** — `tab-duplicates.html:22` y `duplicates.js:331`; la pestaña real se llama "Herramientas" | UX | XS | ⬜ |
| DUPLICADOS-UX-7 | **Estado vacío filtrado sin botón para quitar el filtro** — a diferencia del estado vacío general, que sí usa el componente `_emptyState` con CTA (`duplicates.js:390-392`) | UX | XS | ⬜ |

---

## PLAN-UX — Auditoría de la pestaña Plan/Organizar: UX/UI (2026-07-13)

Auditoría de la pestaña Plan (`tab-plan.html` + `js/tabs/organize.js`) — la
más madura de las auditadas hasta ahora (resumen, progreso, panel de
errores, buena distinción colisión-de-plan vs conflicto-de-disco con enlace
a Duplicados). El usuario preguntó si podía fusionarse con otra pestaña:
**no hay una duplicación clara que lo justifique** — el solapamiento con
Duplicados ya está bien explicado en la propia UI; el candidato real para
una futura revisión es Inbox (su pipeline automático ya hace internamente
lo que Plan hace a mano), pendiente de auditar. Detalle, archivo:línea y
fases en `Tareas/Roadmap-Plan-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| PLAN-UX-1 | **"La operación es reversible" sin que exista ningún "Deshacer"** — `doApply()` lo afirma en su confirmación (`organize.js:458`) pese a que `MEJ-2` (deshacer último apply) sigue pendiente; `applyKeepBoth()` ni lo menciona | UX | XS | ⬜ |
| PLAN-UX-2 | **Las dos acciones de mayor riesgo usan `confirm()` nativo; las de menor riesgo, el modal propio** — `doApply`/`applyKeepBoth` (líneas 458,310) vs `deleteCollisionDuplicates`/`_discardCollisionEntry` (líneas 401,429), mismo archivo | UX | XS | ⬜ |
| PLAN-UX-3 | **"Filtrar por dispositivo" quedó sin función útil tras DEVSEL-FIX-3** — `/api/plan` ya resuelve un único repositorio por dispositivo activo; el dropdown (`tab-plan.html:29-34`) filtra sobre datos que ya son de un solo dispositivo, vaciando la tabla sin explicación si se elige el que no se está viendo | UX | S | ⬜ |
| PLAN-UX-4 | **Mismo bug de `_deviceRoot()` que ASSETS-UX-1** — `organize.js:52,322,469`; se resuelve con el mismo fix compartido en `main.js` | Bug | — | ⬜ (cubierto por ASSETS-UX-1) |
| PLAN-UX-5 | **Conflictos "unknown" sin ninguna explicación** — a diferencia de los tipos `collision`/`disk`, que sí tienen contexto y acciones (`organize.js:164,265-272`) | UX | XS | ⬜ |

---

## SCRAPER-UX — Auditoría de la pestaña Scraper: UX/UI (2026-07-13)

Auditoría de la pestaña Scraper (`tab-scraper.html` + `js/tabs/scraper.js`).
Sin botones muertos ni riesgo de datos (solo lee/escribe metadatos). El
problema central: la funcionalidad de ScreenScraper está repartida entre
Scraper y Settings sin puente entre ellas — la cuota de peticiones diarias
solo se ve en Settings, y exportar `gamelist.xml` existe por duplicado en
ambas pestañas con el mismo endpoint. Detalle, archivo:línea y fases en
`Tareas/Roadmap-Scraper-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| SCRAPER-UX-1 | **Cuota de ScreenScraper solo visible en Settings** — `loadSsQuota()` (`scraper.js:71-98`) solo se llama al abrir Settings (`main.js:483`); sus elementos no existen en `tab-scraper.html`, pese a que aquí es donde se necesita mientras se scrapea | UX | S | ⬜ |
| SCRAPER-UX-2 | **Exportar gamelist.xml duplicado en dos pestañas** — panel completo en Scraper (`tab-scraper.html:56-79`) + botón suelto en el widget ES-DE de Settings (`esde.js:29`, `doExportGamelistsAll`), mismo endpoint `/api/export-gamelists`, sin relación visible entre ambos | UX | S | ⬜ |
| SCRAPER-UX-3 | **Sin comprobación proactiva de credenciales SS** — el usuario solo se entera de que faltan al pulsar "Iniciar scraping" y recibir un error (`doScrape`, `scraper.js:146-151`); Herramientas ya tiene este chequeo proactivo para la API key de RA como referencia | UX | S | ⬜ |
| SCRAPER-UX-4 | **Mensajes de error sin guía** — `doScrape`/`doExportGamelists` (líneas 148,178) muestran `e.message` crudo | UX | XS | ⬜ |
| SCRAPER-UX-5 | **Jerga interna "SAGE-1"/"Sage" filtrada a la UI** — tooltip (`tab-scraper.html:23`) y texto de cobertura (`scraper.js:63`) mencionan el código interno de una tarea del backlog sin explicarlo | UX | XS | ⬜ |
| SCRAPER-UX-6 | **`useEsdeGamelistDir()` es código muerto** — exportada pero ningún botón la llama (`scraper.js:28-33`) | UX | XS | ⬜ |
| SCRAPER-UX-7 | **Exportar gamelists no deshabilita su botón durante la llamada** — inconsistente con `doScrape`, riesgo bajo | UX | XS | ⬜ |

---

## INBOX-UX — Auditoría de la pestaña Inbox: UX/UI (2026-07-13)

Auditoría de la pestaña Inbox (`tab-inbox.html` + `js/tabs/inbox.js`,
Pilar 2). Cierra el hilo abierto en `Tareas/Roadmap-Plan-UX.md`: **no se
fusiona con Plan** — el pipeline de Inbox incluye pasos que Plan no tiene
(extraer, escanear, cotejar) precisamente porque parte de archivos aún no
escaneados; son dos pilares distintos, no una duplicación. Hallazgo
principal propio: "Organizar todo" es la única acción masiva de todo el
proyecto auditado hasta ahora sin ningún paso de confirmación. Detalle,
archivo:línea y fases en `Tareas/Roadmap-Inbox-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| INBOX-UX-1 | **"Organizar todo" sin ninguna confirmación** — `runInbox()` (`inbox.js:160-186`) lanza extraer+escanear+cotejar+renombrar+organizar sobre toda la carpeta Inbox sin `confirm()`/`_showConfirm`, a diferencia de toda acción masiva equivalente ya auditada (Duplicados, Plan, Formatos) | Bug | S | ⬜ |
| INBOX-UX-2 | **"Analizar carpeta" no muestra un plan real, solo clasificación** — sin nombres de destino ni conflictos previstos, a diferencia de la tabla equivalente en Plan; conviene resolver junto con INBOX-UX-1 (la confirmación necesita estos datos) | UX | M | ⬜ |
| INBOX-UX-3 | **`confirm()` nativo en `resolveInboxConflict`** (`inbox.js:321-336`) — mismo patrón ya señalado en Duplicados y Plan | UX | XS | ⬜ |
| INBOX-UX-4 | **Checkbox "Procesar automáticamente" sin relación visible con "Guardar ajustes"** — toggle silencioso que no hace nada hasta pulsar un botón en otra fila (`tab-inbox.html:31-34,40`) | UX | XS | ⬜ |
| INBOX-UX-5 | **"No reconocidos" sin explicar qué pasará con esos archivos** (`inbox.js:128`) | UX | XS | ⬜ |
| INBOX-UX-6 | **Errores sin guía en `loadInboxConflicts`** (`inbox.js:314-316`) | UX | XS | ⬜ |

---

## TV-UX — Auditoría del Modo TV: UX/UI (2026-07-13)

Auditoría del Modo TV (`tab-tv.html` + `games.js:904-976` +
`main.js:737-782`). Modo de navegación legítimamente distinto (foco por
teclado, pantalla completa) — no candidato a fusión. Dos hallazgos
críticos: la colección se corta en 120 juegos sin forma de cargar más
(`_TV_LIMIT`, paginación soportada por el backend pero nunca disparada), y
la barra de filtro por plataforma existe en el HTML pero ninguna función
la rellena jamás — planeada pero nunca conectada. Detalle, archivo:línea y
fases en `Tareas/Roadmap-TV-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| TV-UX-1 | **La colección se corta en 120 juegos sin forma de cargar más** — `loadTvGrid` soporta `offset` (`games.js:918-934`) pero nada lo dispara nunca con offset > 0; `_tvMoveFocus` simplemente deja de avanzar al llegar al final sin avisar | Bug | S | ⬜ |
| TV-UX-2 | **Barra de filtro por plataforma nunca rellenada** — `tv-platform-bar`/`tv-platform-label` (`tab-tv.html:3-4`) vacíos para siempre; `loadTvGrid` ya acepta `platform` pero `enterTvMode()` siempre llama con `''` (`games.js:905-910`) | Bug | S | ⬜ |
| TV-UX-3 | **"Salir" siempre vuelve a Colección, ignorando de dónde viniste** — `exitTvMode()` hace `showTab('collection')` fijo (`games.js:912-916`) pese a que `t` es un atajo global desde cualquier pestaña | UX | XS | ⬜ |
| TV-UX-4 | **Fallo de red deja la rejilla en blanco sin ningún aviso** — catch de `loadTvGrid` solo hace `console.error` (`games.js:933`), sin mensaje visible en un modo a pantalla completa | UX | XS | ⬜ |
| TV-UX-5 | **Pulido: fallo de pantalla completa silencioso + `_tvCols` no se recalcula al redimensionar** (`games.js:908,959`) | UX | XS | ⬜ |

---

## SETTINGS-UX — Auditoría de la pestaña Settings: UX/UI (2026-07-13)

Auditoría de la pestaña Settings (`tab-settings.html`, ~500 líneas/20+
paneles, + `js/tabs/config.js`, ~870 líneas) — la más grande de la app.
Hallazgo principal, verificado de forma independiente en frontend y
backend: el campo "ES-DE carpeta" nunca ha podido guardar nada porque el
backend filtra `launchers.esde` de su lista de claves permitidas (a
diferencia de `launchers.retroarch`, que sí está) — fix de una línea.
Detalle, archivo:línea y fases en `Tareas/Roadmap-Settings-UX.md`.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| SETTINGS-UX-1 | **"ES-DE carpeta" nunca se guarda, para nadie** — el frontend envía `launchers.esde` (`config.js:621-622`) pero el `allowed` set del backend no lo incluye (`handlers/config.py:242-272`, comparar con `launchers.retroarch` que sí está); se descarta en silencio antes de escribir `config.toml` | Bug | XS | ⬜ |
| SETTINGS-UX-2 | **4 campos se guardan bien pero nunca muestran "✓ Guardado"** — `sync.saves_remote`/`sync.states_remote`/`sync.ra_config_remote`/`retroachievements.username` faltan en el mapa `_CFG_CHECK` (`config.js:645-656`) pese a tener el mismo `<span class="cfg-saved">` que sus vecinos en el HTML | UX | XS | ⬜ |
| SETTINGS-UX-3 | **Panel "Configurar consola Android" (QR) — ya cubierto por ANBERNIC-UX-2** — mismo endpoint 404 (`/api/anbernic-setup.sh`), aplica también a esta copia del panel (`tab-settings.html:12-39`) | Bug | — | ✅ (panel eliminado en feature/anbernic-ux) |
| SETTINGS-UX-4 | **"Migrar BD a dos DBs" sin confirmación** — única operación de BD sin `confirm()`/`_showConfirm` en la pestaña, a diferencia de "Vaciar papelera" y "Cerrar Retro Vault" (`config.js:111-124`) | UX | XS | ⬜ |
| SETTINGS-UX-5 | **Pulido: la mayoría de campos no tienen confirmación inline** — solo dependen del toast genérico al guardar | UX | XS | ⬜ |

---

## REV43 — Auditoría de calidad de código (`/revisar`, 2026-07-15)

Origen: revisión completa de `src/rom_manager/` (26.9k líneas) con 6 agentes
en paralelo por área (sync, database, web/handlers core, web/server+builders,
detection/scanner/catalog/patch/converters/renamer, retroachievements/
scraper/utils/cli). Ningún fix aplicado todavía — solo documentado, según la
regla "investigar antes de arreglar" de `CLAUDE.md`. Prioridad de orden:
primero todo lo que toca sync de saves (Pilar 3 — riesgo de pérdida de
progreso), luego integridad de BD, luego web, luego el resto.

| ID | Severidad | Task | Archivo(s) | Estado |
|----|-----------|------|-----------|--------|
| REV43-1 | 🔴 Alto | **`AdbTransport.push` sin staging ni backup — borra el remoto si el MD5 no coincide** — a diferencia de `pull()` (que sí usa `.part`), un push corrupto destruye para siempre un save del Anbernic aún no bajado al PC | `sync/adb_transport.py:245-279` | ✅ rama `feature/cable-ux` — sube a `<dst>.part`, verifica MD5 y solo entonces mueve sobre el destino final (`mv -f`); si no coincide, borra solo el `.part` y el original queda intacto. 2 tests nuevos |
| REV43-2 | 🔴 Alto | **Ninguna ruta de sync por cable/ADB llama a `backup_save()`** — solo la ruta rclone (`save_syncer.py`) hace backup-antes-de-sobrescribir; `cable_engine.copy_item` y sus callers (`sync_cable.py`, `cable_sync_daemon.py`) no, violando "ante duda, no sobreescribir; guardar backup primero" | `sync/cable_engine.py:101-144` | ✅ rama `feature/cable-ux` — backup a nivel de caller en `web/handlers/sync_cable.py` (filesystem y pull ADB), mismo patrón que el SD-auto daemon (CABLE-UX-9a); push ADB sin backup remoto a propósito (evitaría un pull extra), mitigado por REV43-1. 1 test nuevo |
| REV43-3 | 🔴 Alto | **`UnboundLocalError` en el `except` de `sync_saves()`** — `remote_path` solo se asigna tras un upload/download exitoso; si el primer archivo falla, revienta toda la sincronización; en fallos posteriores registra en el log de auditoría la ruta remota de un archivo anterior | `sync/save_syncer.py:190,242` | ✅ rama `feature/cable-ux` — `remote_path` se calcula al principio de cada iteración, antes de cualquier transferencia; eliminadas las 3 asignaciones duplicadas/tardías. 1 test nuevo |
| REV43-4 | 🔴 Alto | **Rama `"newest"` compara `st_mtime` en crudo sin tolerancia de clock-skew** (a diferencia de `conflict_resolver.decide()`, que sí usa `tolerance_seconds`) — en SD FAT32/exFAT puede sobrescribir en silencio una partida más nueva sin marcarlo como conflicto | `sync/cable_engine.py:60-85` | ✅ rama `feature/cable-ux` — `plan_direction()` acepta `tolerance_seconds` (default `DEFAULT_MTIME_TOLERANCE_S=2`, igual que `conflict_resolver.decide()`). Hallazgo extra: el modo ADB "newest" en `sync_cable.py:623-650` es una segunda implementación independiente con el mismo bug — misma tolerancia aplicada ahí también; unificar ambas queda como limpieza futura. 2 tests nuevos |
| REV43-5 | 🔴 Alto | **Migración a dos BDs borra la fila origen aunque el upsert al destino haya fallado** — una fila cuya migración falló igualmente se elimina de la BD PC → pérdida permanente de metadatos de catálogo (tags, RA, stats) | `web/handlers/sync_cloud.py:602-657` | ✅ rama `feature/cable-ux` — `migrated_paths`/`migrated_save_paths` trackean éxito por fila; el DELETE en origen solo cubre esas rutas. 1 test nuevo |
| REV43-6 | 🔴 Alto | **`dry_run` ignorado en modo ADB con `skip_sha1_dups`** — `transport.pull(..., dry_run=False)` hardcodeado hace transferencias ADB reales aunque el usuario pidiera solo previsualizar | `web/handlers/sync_cable.py:554` | ✅ rama `feature/cable-ux` — en dry-run el chequeo SHA1 ya no se evalúa (exigiría pull real); se cuenta como "se copiaría" sin transferir nada. 1 test nuevo |
| REV43-7 | 🟠 Medio | **Sync filesystem no valida que `pc_root`/`ab_root` existan** — una SD no montada produce "sync exitoso" con `copied=0, errors=0` en vez de error explícito (inconsistente con `_do_tree_diff`, que sí valida) | `web/handlers/sync_cable.py:638` | ✅ rama `feature/cable-ux` — `raise OSError` explícito si `pc_root`/`ab_root` no existen, capturado por el except genérico de `run()`. 2 tests nuevos |
| REV43-8 | 🟠 Medio | **`_do_sync` (cloud) nunca setea `result_ts`** — el frontend (`flow_wizard.js:342`) hace check truthy sobre ese campo → el paso "Sync" del wizard nunca deja de hacer polling | `web/handlers/sync_cloud.py:497` | ✅ rama `feature/cable-ux` — `result_ts` añadido a los 3 `job_result` posibles (éxito, sin fuentes, except). 1 test nuevo |
| REV43-9 | 🔴 Alto | **`PRAGMA foreign_keys` nunca se activa en ningún sitio del proyecto** — las FKs de `schema.py` (`ON DELETE SET NULL`/cascada) son decorativas, sin integridad referencial real | `database/repositories/base.py` | ✅ rama `fix/db-integrity` — `PRAGMA foreign_keys=ON` en `_open_conn()`. Al comprobar la BD real (`.rommgr/library_pc.db`) aparecieron 4 sitios más con `DELETE FROM games` directo sin cascada (`ra_duplicates_service.py`, `inbox_pipeline.py` x2, `sync_cloud.py`) que habrían roto duplicados/inbox/migración cloud al activar el enforcement — mismo bug que REV43-10 replicado 4 veces; unificado en `cascade_delete_games_by_source_path()` (`games.py`), reutilizado por los 4. 1 test nuevo (`test_foreign_keys_enforced`) |
| REV43-10 | 🟠 Medio | **`delete_game()` solo borra la fila de `games`** — deja huérfanas `game_metadata`/`game_tags`/`file_operations`; se llama desde `duplicates_service.py` e `inbox_pipeline.py:868` al borrar duplicados/ROMs reemplazados | `database/repositories/games.py:309-313` | ✅ rama `fix/db-integrity` — `delete_game()` borra también `game_metadata`/`game_tags`/`file_operations` antes de `games` (helper compartido `_delete_game_children`). Decisión explícita del usuario: se borra el historial de `file_operations` del juego eliminado (no `SET NULL`) — prioriza limpieza sobre preservar auditoría de un archivo que ya no existe. 1 test nuevo (`test_delete_game_removes_children`) |
| REV43-11 | 🟠 Medio | **`get_games_paginated` revienta con `ambiguous column name: id`** al combinar filtro `tag` + `genre`/`year` a la vez (columna `id` sin cualificar choca entre `games` y `game_metadata`); reproducible desde `web/builders/library.py:346-374` | `database/repositories/games.py:410-443` | ✅ rama `fix/db-integrity` — la condición `"id IN"` ya no queda excluida del rewrite a `g.id IN` cuando hay JOIN con `game_metadata`. 1 test nuevo (`test_get_games_paginated_tag_and_genre_together`) |
| REV43-12 | 🟡 Bajo | **`get_save_sync_history` escapa `_`/`%` para LIKE pero la query no lleva `ESCAPE '\'`** — el escapado es un no-op silencioso (sí está bien hecho en `games.py:399-403`) | `database/repositories/sync.py:94-98` | ✅ rama `fix/db-integrity` — añadido `ESCAPE '\\'`. Hallazgo extra: el patrón de `games.py` no basta aquí porque `game_dir` es una ruta real de Windows con `\` como separador, que choca con el propio carácter de escape; se escapan primero las `\` literales del path antes de escapar `_`. 1 test nuevo (`test_get_save_sync_history_escapes_underscore`) |
| REV43-13 | 🔴 Alto | **`_httpd_instance` se guarda como global de `server.py`, no de `_state`** — `/api/shutdown` y `/api/update/apply` leen `_state._httpd_instance` (siempre `None`) → `AttributeError` al invocarlos | `web/server.py:612-615` (vs `web/state.py:44`) | ✅ rama `fix/web-httpd-shutdown` — `serve()` asigna `_state._httpd_instance = httpd` directamente (eliminado el `global _httpd_instance` local, que creaba un atributo de módulo distinto nunca leído por nadie). Smoke test manual: arrancado el servidor real, confirmado `AttributeError` antes del fix y `shutdown()` funcionando después |
| REV43-14 | 🟠 Medio | **Health Check (Tools) siempre falla** — importa `_write_health_schedule` desde `server.py`, pero esa función vive en `daemons.py`; el `ImportError` queda silenciado por el `except Exception` del propio job | `web/handlers/esde/maintenance.py:94` | ✅ rama `fix/web-health-check-import` — import corregido a `rom_manager.web.daemons`. Test nuevo (`tests/test_health_check_job.py`) que ejercita `/api/health-check` de extremo a extremo vía `Router`/`JobManager` reales; confirmado que reproduce el `ImportError` exacto sin el fix y pasa con él |
| REV43-15 | 🟠 Medio | **Con PIN activo, el setup de Anbernic se rompe** — el auth gate no exime `/s` ni `/api/rclone-export-config`, pero ambos están pensados para `curl` sin sesión desde Termux; con PIN, la respuesta es un 302 vacío en vez del script | `web/server.py:256-263` | ✅ rama `fix/web-pin-anbernic-setup` — `/s` y `/api/rclone-export-config` exentos del gate de sesión/PIN (mismo `if` que ya exime `/static/`); ambas rutas ya se protegían solas con `_setup_token_ok()` (loopback o `?t=` válido), así que no quedan abiertas. 4 tests nuevos (`tests/web/test_anbernic_setup_with_pin.py`) — confirmado que 3 reproducen el 302 real sin el fix, y uno confirma que el resto de rutas (`/api/config`) sigue exigiendo sesión |
| REV43-16 | 🟠 Medio | **`post_restore_backup` — path traversal por comparación de prefijo de string** — `not str(tp).startswith(str(config.library_root))` deja pasar `"C:\GamesEvil\..."` si `library_root="C:\Games"`; falta normalizar separador/límite de ruta | `web/handlers/games.py:653` | ✅ rama `fix/web-restore-path-traversal` — sustituido por `Path.resolve()` + `is_relative_to()`. 2 tests nuevos (`tests/web/test_restore_backup_path_traversal.py`); confirmado que sin el fix el caso `GamesEvil` no solo pasaba el check sino que restauraba de verdad el archivo fuera de la biblioteca (`ok: True`) |
| REV43-17 | 🟡 Bajo | **`/api/stop-job` no cancela un escaneo ADB en curso** — `_do_adb_scan` no comprueba el flag de cancelación, a diferencia de `_do_scan` (que sí pasa `stop_event`) | `web/handlers/scan.py:401-469` | ✅ rama `fix/web-adb-scan-cancel` — `_do_adb_scan` obtiene el mismo `cancel_event("scan")` que `_do_scan` (comparten job_id) y corta el bucle de archivos en el siguiente boundary; `cancelled` añadido al `job_result`. Test nuevo (`tests/web/test_adb_scan_cancel.py`) que simula `/api/stop-job` llegando a mitad del escaneo; confirmado que sin el fix el resultado ni siquiera trae la clave `cancelled` |
| REV43-18 | 🟡 Bajo | **`.ups` truncado lanza `IndexError` sin capturar** — `_read_vlq` no comprueba `pos >= len(data)`, a diferencia del mismo helper en `bps_applier.py` que sí lo hace; rompe el contrato de "error controlado, nunca corrupción silenciosa" | `patch/ups_applier.py:14-16` | ✅ rama `fix/patch-ups-truncated` — mismo guard que `bps_applier._read_vlq` (`raise PatchError` si `pos >= len(data)`). Test nuevo; confirmado que sin el fix lanza `IndexError` real, no `PatchError` |
| REV43-19 | 🟡 Bajo | **Offsets negativos de `SourceCopy`/`TargetCopy` no se validan** — un patch BPS corrupto con offset negativo indexa desde el final del array (válido en Python) en vez de fallar con `PatchError`, corrompiendo el resultado en silencio | `patch/bps_applier.py:87-103` | ✅ rama `fix/patch-bps-negative-offset` — `raise PatchError` si `src_rel`/`tgt_rel` quedan negativos tras aplicar el delta. 2 tests nuevos; confirmado que sin el fix no había ninguna excepción — el output salía mal en silencio (`source[-1]` envuelto al final del array) |
| REV43-20 | 🟡 Bajo | **Conversión N64 sobrescribe destino sin comprobar si ya existe** (a diferencia de `chd_converter`, que sí rechaza sobrescribir) | `converters/n64_converter.py:84-85` | ✅ rama `fix/n64-converter-overwrite` — `target.exists()` rechaza la conversión igual que `chd_converter`. 2 tests nuevos (`tests/test_n64_converter.py`, no existía archivo de test previo); confirmado que sin el fix el destino se sobrescribía de verdad (`success=True`) |
| REV43-21 | 🟢 Menor | **Padding de relleno del último chunk se escribe también al archivo de salida** — un `.v64`/`.n64` cuyo tamaño no es múltiplo de 2/4 produce un `.z64` con bytes basura al final | `converters/n64_converter.py:90-103` | ✅ rama `fix/n64-converter-padding` — el padding solo se usa para que el swap esté bien definido; se escriben solo los primeros `orig_len` bytes del resultado. 2 tests nuevos; confirmado que sin el fix el `.z64` salía con 1 byte de más (8 en vez de 7) |
| REV43-22 | 🟡 Bajo | **`LIKE` sin escapar `_`/`%` del propio nombre de archivo** puede actualizar `last_played_at` de un juego equivocado si el nombre contiene `_` | `scanner/rom_scanner.py:145-148` | ✅ rama `fix/scanner-like-escape` — escapado `\`/`%`/`_` + `ESCAPE '\'` (mismo ajuste de barras invertidas de rutas Windows que REV43-12). Test nuevo; confirmado que sin el fix un ROM señuelo (`ZeldaXofXTime.gba`) recibía `last_played_at` de un save de `Zelda_of_Time.srm` |
| REV43-23 | 🟢 Menor | **`cue_validator` no reconoce líneas `FILE` sin comillas** (a diferencia de `chd_converter.parse_bins_from_cue`, que sí) — un `.cue` con `.bin` ausente pasa sin warning durante el scan | `detection/cue_validator.py:6` | ✅ rama `fix/cue-validator-unquoted-file` — mismo patrón de dos regex (comillas → fallback sin comillas) que `chd_converter.parse_bins_from_cue`, sin crear una dependencia inversa `detection`→`converters`. 2 tests nuevos; confirmado que sin el fix un `.bin` ausente referenciado sin comillas pasaba con 0 errores |
| REV43-24 | 🟢 Menor | **Rollback de `move_disc_set_to_subfolder` traga `OSError` en silencio**, sin registrar qué archivo no pudo revertirse (a diferencia de `rename_rom_with_saves`, que sí reporta `rollback_failures`) | `renamer/file_renamer.py:264-273` | ✅ rama `fix/renamer-rollback-failures` — `_rollback()` devuelve la lista de fallos, incluida en el error con el mismo formato "rollback INCOMPLETE — manual fix needed" que `rename_rom_with_saves`. 1 test nuevo (rollback de un BIN forzado a fallar); confirmado que sin el fix el error no mencionaba nada del rollback fallido |
| REV43-25 | 🟢 Menor | **Backup de seguridad puede degenerar en no-op en reintentos** — si `bak` ya existe de un intento previo, `os.replace(bak, bak)` no respalda el save actual antes del siguiente intento de move | `renamer/file_renamer.py:169-171` | ✅ rama `fix/renamer-bak-retry-noop` — siempre busca un nombre `.bak`/`.bak1`/`.bak2`... libre en vez de reemplazar `bak` por sí mismo. 1 test nuevo; confirmado que sin el fix el save actual se sobrescribía sin backup real (`New.srm.bak1` ni siquiera se creaba) |
| REV43-26 | 🟡 Bajo | **`verify_multidisc()` revienta con `IndexError`** si un grupo de set tiene solo archivos sidecar (`.cue`/`.m3u` sin `.bin`/`.chd`/`.iso`) — rompe la verificación de toda la biblioteca, no solo ese set | `utils/multidisc_verifier.py:84` | ⬜ |
| REV43-27 | 🟠 Medio | **Fallo de red en RA trata la plataforma entera como "0 juegos con logros"** — `except Exception: hash_lib = {}` puede inducir a que la resolución de duplicados descarte la versión correcta por un error transitorio | `retroachievements/ra_checker.py:94-97` | ⬜ |
| REV43-28 | 🟡 Bajo | **Camino alternativo de lectura de caché RA bypasea el TTL de 1 semana** — `get_ra_hash_lib` solo comprueba `cache_file.exists()`, sin el chequeo de antigüedad que sí aplica `ra_client.fetch_hash_library` | `services/ra_duplicates_service.py:180-190` | ⬜ |
| REV43-29 | 🟡 Bajo | **Dedup de `gamelist_writer` colapsa discos distintos del mismo set**, no solo `.m3u` vs `.cue` individuales — la clave de dedup no incluye número de disco | `scraper/gamelist_writer.py:142-166` | ⬜ |
| REV43-30 | 🟢 Menor | **`except OSError: pass` al escribir `metadata.pegasus.txt`** — una plataforma entera puede no escribirse sin que el caller se entere | `scraper/pegasus_writer.py:76-77` | ⬜ |
| REV43-31 | 🟢 Menor | **Contador `errors` del comando `scrape` nunca se incrementa** — el resumen final siempre imprime "Errors: 0" aunque el comando falle a mitad | `cli.py:737-784` | ⬜ |
| REV43-32 | 🟢 Menor | **`_EXCLUDED_DIR_NAMES`/`_iter_files` definidos dos veces (copia exacta) en el mismo archivo** — resto de un merge/copiado, la segunda definición pisa a la primera sin efecto funcional | `utils/orphan_finder.py:8-14,32-39` | ⬜ |
| REV43-33 | 🟡 Bajo | **`cable_engine`/`adb_transport` nunca escriben en `save_sync_log`** — "toda operación sobre archivos se registra en SQLite" solo se cumple en la capa rclone | `sync/cable_engine.py`, `sync/adb_transport.py` | ⬜ |
| REV43-34 | 🟢 Menor | **Lógica de enrutado por extensión (states→saves→fallback) triplicada** entre `diagnose_routing`/`upload`/`download` | `sync/rclone_transport.py:52-123,199-252,323-376` | ⬜ |
| REV43-35 | 🟢 Menor | **Watermark de conflicto se busca solo por `local_path`, ignorando el remoto** — si `saves_remote`/`states_remote` cambian en config, puede usarse un `last_sync_at` que ya no corresponde | `sync/sync_log.py:100-117` | ⬜ |
| REV43-36 | 🟢 Menor | **Late import de `utc_now` para evitar ciclo** — invierte la dependencia (capa de datos dependiendo de la capa de escaneo) en vez de import a nivel de módulo | `database/repositories/metadata.py:149` | ⬜ |
| REV43-37 | 🟢 Menor | **"Escape" de LIKE con `prefix.replace("%", "%%")` es un no-op** (`%%` sigue siendo dos comodines, no un `%` literal) — repetido en 3 sitios sin la corrección que sí existe en `games.py:399-403` | `database/repositories/base.py:117`, `assets.py:65`, `games.py:397` | ⬜ |
| REV43-38 | 🟢 Menor | **`record_play_session` no acepta `connection` opcional**, a diferencia del resto de métodos de escritura del paquete — no puede participar en un `batch()` externo | `database/repositories/play_history.py:13-47` | ⬜ |
| REV43-39 | 🟢 Menor | **Clasificación imagen/vídeo por extensión duplicada en 3 capas** | `database/repositories/assets.py:62-63`, `web/handlers/esde/system.py`, `web/builders/folders.py` | ⬜ |
| REV43-40 | 🟢 Menor | **Descarga de DATs implementa su propio sistema de jobs** (lock/dict/thread propios) en vez de registrarse en `job_manager`/`/api/job-status` | `web/handlers/scan.py:69-70,188-209` | ⬜ |
| REV43-41 | 🟢 Menor | **`_do_organize_library` hace `commit()` por fila** en vez de `repository.batch()`, contradice la convención documentada | `web/handlers/organize.py:330-366` | ⬜ |
| REV43-42 | 🟢 Menor | **Export/status de config rclone implementado dos veces con lógica divergente** | `web/handlers/sync_cloud.py:166-215` vs `web/handlers/system.py:193-256` | ⬜ |
| REV43-43 | 🟢 Menor | **Lookup de caché RA duplicado entre el enriquecido bulk y el individual** | `web/handlers/games.py:97-143` vs `:411-442` | ⬜ |
| REV43-44 | 🟢 Menor | **`print()` de depuración a nivel de módulo** en vez de `logging` | `web/handlers/collection.py:28` | ⬜ |
| REV43-45 | 🟢 Menor | **Late import de `web.state`** dentro de la función, contradice CLEAN-1 | `web/handlers/update.py:90` | ⬜ |
| REV43-46 | 🟢 Menor | **Bloque de serialización de grupos de duplicados duplicado 4 veces en el mismo archivo** | `web/builders/duplicates.py` | ⬜ |
| REV43-47 | 🟢 Menor | **`DatDownloadResult` sin `slots=True`** e importa el símbolo privado `_load_dat_file` de otro módulo | `catalog/dat_downloader.py:11,90` | ⬜ |
| REV43-48 | 🟢 Menor | **`KNOWN_BIOS` modelado como `list[dict]`** en vez de `@dataclass(slots=True)` como el resto del archivo | `detection/bios_checker.py:17` | ⬜ |
| REV43-49 | 🟢 Menor | **`_same_file()` duplicado carácter por carácter** en dos archivos | `planner/operation_planner.py:11-21`, `renamer/file_renamer.py:98-102` | ⬜ |
| REV43-50 | 🟢 Menor | **`pegasus_writer` no aplica dedup multi-disco** (a diferencia de `gamelist_writer`) — salidas incoherentes entre formatos para los mismos datos | `scraper/pegasus_writer.py` | ⬜ |
| REV43-51 | 🟢 Menor | **`GeneratedSystem`/`GeneratorResult` sin `slots=True`** | `esde/systems_generator.py:214-229` | ⬜ |
| REV43-52 | 🟢 Menor | **`cli.py` mete lógica de negocio completa inline** (`scrape`, `convert-chd`, `sync`, `health`) en vez de delegar a `services/`, rompiendo el patrón ya establecido (ARC-SVC-1) | `cli.py` | ⬜ |

> Orden sugerido de ataque: REV43-1…8 (sync, riesgo de pérdida de datos) →
> REV43-9…12 (integridad de BD) → REV43-13…17 (bugs de web) → resto por
> valor/esfuerzo. Cada fix en su propia rama, siguiendo el patrón ya usado en
> INBOX-FIX-*/ZIP-ROUTE-FIX-*/DEVSEL-FIX-*.

---

## User actions (no code needed)

| ID | Task |
|----|------|
| STRUCT-4 | Configure RetroArch PC: Saving → Savefile Directory → `E:\Carpetas anbernic\saves\` |
| STRUCT-3 | Update `config.toml`: `local_dir = "E:\\Carpetas anbernic\\saves"` (after STRUCT-4) |
| ES-1 | Download `genesis_plus_gx` core in RetroArch → Online Updater |
| ES-2 | Configure Citra (3DS) in EmulationStation |
| PC2-1 | Añadir el segundo PC (otra ciudad) al sync de saves vía Dropbox/rclone — seguir `Tareas/Guia-Segundo-PC.md` (no requiere código; NO sincronizar las BDs SQLite) |
