# Retro Vault — Backlog

> Single source of truth for pending work. Updated every session.
> Last updated: 2026-07-12 (AUD-1…6: auditoría funcional → `Tareas/Roadmap-Auditoria.md`)
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
| MEJ-1 | **Playtime real desde logs `.lrtl` de RetroArch** — scanner stdlib-json de `playlists/logs/<Core>/<rom>.lrtl` (`runtime` + `last_played`) que puebla `play_history`; elimina la entrada manual de horas. Fase 2: sync de los `.lrtl` de Android (mismo pipeline que saves) → playtime unificado PC+consola. Alimenta el recomendador NLP. | `scanner/` (nuevo módulo), `database/repositories/play_history.py`, endpoint | ⬜ |
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
estimaciones: `Tareas/Roadmap-Onboarding.md`.

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

> **Completado 9/9** (PRs #71–#74 + ONB-9). Detalle: `Tareas/Roadmap-Onboarding.md`.

---

## AUD — Auditoría funcional (2026-07-12)

Funciones nuevas detectadas en auditoría de la app completa. Detalle, archivos
y criterios de "hecho" en `Tareas/Roadmap-Auditoria.md`. Orden: 1→6.

| ID | Task | Pilar | Esfuerzo | Estado |
|----|------|-------|----------|--------|
| AUD-1 | **Sync Doctor** — detectar desviación de reloj PC↔consola (mtime gana → reloj mal = pérdida silenciosa), saves con mtime futuro, saves solo en un lado, último sync por juego | Sync | M | ⬜ |
| AUD-2 | **Verificación post-transferencia** — hash origen/destino tras cada push/pull (`adb shell md5sum`); si difiere, no propagar y reportar; columna `verified` en `save_sync_log` | Sync | S-M | ⬜ |
| AUD-3 | **Papelera unificada con purga** — todo borrado masivo pasa por `_descartados/` (helper `_discard_file` ya existe); purga >30 días en el health-check daemon; contador+vaciar en Settings. Evita repetir INBOX-FIX-5 | Seguridad | M | ⬜ |
| AUD-4 | **`.md` ambiguos del Inbox por CRC** — los 177 varados: lookup contra `crc_index()` ya existente; hit=Mega Drive, miss=quieto. Formaliza el "ZIP-ROUTE-FIX-4" informal | Inbox | S | ⬜ |
| AUD-5 | **Informe de completitud por plataforma (1G1R)** — cruzar `games` matched vs DATs: "SNES: 412/1.748 (24 %)" + CSV de faltantes | Biblioteca | M | ⬜ |
| AUD-6 | **`chdman verify` en health check** — verificación interna de CHDs, checkbox off por defecto | Biblioteca | S | ⬜ |

---

## DEVSEL-FIX — Selector de dispositivo (auditoría 2026-07-12)

El selector global PC / Sistema completo / Consola (`_nav.html:69-71`, `setDevice()` en
`main.js:412`, `_deviceRoot()` en `main.js:428`) filtra por `source_root`; el backend elige
BD con `_repo_for_path()` (`builders/common.py:141`): **path vacío → BD del PC**. De ahí
salen todos los fallos. Orden: 1→2 son pérdida de datos potencial, prioridad absoluta.

| ID | Task | Pilar | Esfuerzo | Estado |
|----|------|-------|----------|--------|
| DEVSEL-FIX-1 | **Acciones de duplicados ignoran el dispositivo** — la vista sí lee ambas BDs (`_build_duplicates_two_repos`, `handlers/duplicates.py:50`) pero TODAS las acciones usan `repository` (PC) fijo: `/api/duplicates/delete` (`duplicates.py:70` → `delete_duplicate` borra el archivo por path pero `delete_game(game_id)` contra la BD PC con un id de la BD Android, `services/duplicates_service.py:65`); `/api/duplicates/delete-all` (`duplicates.py:80`) — **en modo consola la UI muestra y confirma duplicados Android pero el backend borra los del PC** (`delete_all_duplicates` recorre `repository.get_duplicate_groups()`); `/api/duplicates/exclude` y los 6 endpoints RA-duplicates, ídem. Fix: enrutar por `get_repo_fn(source_path)` en delete, y pasar `source_root` a delete-all/exclude | Seguridad | M | 🟡 rama `feature/devsel-fix-1` — `register()` recibe `get_repo_fn`; delete enruta por `source_path`, delete-all/exclude por `source_root` del body (vacío = "Sistema completo" → ambas BDs: `delete_all_duplicates_multi()`, exclude en ambas con INSERT OR IGNORE); RA discard/resolve enrutan por path (los llama también la tab de duplicados normal). Frontend envía `_deviceRoot()` en delete-all/exclude. 6 tests handler con 2 repos reales (664 pass) |
| DEVSEL-FIX-2 | **Favoritos/tags/notas/metadatos escriben siempre en la BD del PC** — `/api/toggle-favorite` (`handlers/games.py:502`), `/api/tag` (`games.py:516-519`), `/api/set-metadata` (`games.py:482-491`) usan `repository` fijo; en modo consola el `game_id` viene de la BD Android → escriben en el juego equivocado del PC o en ninguno. El frontend ni envía `source_path` (`games.js:160,686,715,725,784,818`). `/api/set-play-status` sí enruta bien (`games.py:468`) pero el panel de juego llama con `source_path: ''` (`games.js:659`) → siempre PC. Fix: enviar `source_path` desde el frontend y usar `get_repo_fn()` en los 3 handlers | Biblioteca | S-M | 🟡 rama `feature/devsel-fix-2` — los 3 handlers enrutan con `get_repo_fn(data["source_path"])`; el panel de juego envía `_gpSrc()` (lee `dataset.sourcePath`, ya existente) en favorite/tag/notes/metadata/play-status, y la estrella de la lista lleva `data-path`. 4 tests con 2 repos y mismo game_id en ambas BDs (662 pass) |
| DEVSEL-FIX-3 | **"Sistema completo" = solo PC en la práctica** — `_deviceRoot()` devuelve `null` en modo `both` → sin `source_root` → `get_repo_fn("")` → BD PC. Afecta a `/api/plan` y `/api/apply` (`handlers/organize.py:35,107` — la barra dice "Viendo: Sistema completo (PC + consola)", `organize.js:68`, pero solo planifica/renombra el PC), `/api/games` (`games.py:121`), platform-stats/assets/export/disk-usage (`collection.py:35,64,126,159,181,348`), unmatched/completeness (`games.py:640,701`). Única vista correcta: duplicados. Fix: en modo `both`, o consultar/fusionar ambos repos o eliminar el modo si no aporta | Biblioteca | M-L | ⬜ |
| DEVSEL-FIX-4 | **Botón "Consola" habilitado por ruta, no por detección** — `dev-anbernic` se habilita si hay `abPath` configurada (`overview.js:424-425`, `config.js:709`) aunque la consola no esté conectada; `deviceConnected` (polling `/api/device-status`, `state.js:52`) solo gatea el badge del Overview, el botón Apply (`organize.js:27-46`) y `doApply` (`organize.js:455`) — `applyKeepBoth` (`organize.js:309`) no comprueba nada. Además `dev-both` nunca se deshabilita, ni sin ruta. Fix pedido: deshabilitar "Consola" (y "Sistema completo") cuando `!deviceConnected`, con tooltip del motivo; decidir si se permite modo solo-lectura de la BD Android offline | UX | S | ⬜ |

---

## User actions (no code needed)

| ID | Task |
|----|------|
| STRUCT-4 | Configure RetroArch PC: Saving → Savefile Directory → `E:\Carpetas anbernic\saves\` |
| STRUCT-3 | Update `config.toml`: `local_dir = "E:\\Carpetas anbernic\\saves"` (after STRUCT-4) |
| ES-1 | Download `genesis_plus_gx` core in RetroArch → Online Updater |
| ES-2 | Configure Citra (3DS) in EmulationStation |
