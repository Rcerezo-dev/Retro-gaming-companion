# Retro Vault — Backlog

> Single source of truth for pending work. Updated every session.
> Last updated: 2026-07-07 (SAGE-1…3: tareas de soporte para Retro Sage desde su ROADMAP.md)
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
| Renombrado PSX roto | `cue_rewriter.py` + `operation_planner.py` |
| ADB no encuentra saves | `adb_transport.py` (mapeo de rutas por emulador) |
| Circular import al arrancar | Late imports en `cable_sync_daemon.py` / `inbox_pipeline.py` |
| 404 en rutas registradas | `router.dispatch()` — ver BUG-ROUTING-404 en `archivo.md` |

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
| ARCADE-SETUP-3 | Document config additions: `config.toml`, library-structure, DAT sources for arcade | `docs/arcade-setup.md` ✅ + DAT downloader wired (scan.js/dat_downloader.py/scan.py) |
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
| MATCH-FIX-1 | **`CatalogMatcher.match()` — Pass 2 (nombre) da falsos positivos en ficheros arcade sin tag de región** — nombres cortos estilo MAME (`flicky.zip`, `frogger.zip`, `dw.zip`…) sin `(Region)` colisionan por coincidencia de título normalizado contra catálogos No-Intro/Redump de plataformas completamente ajenas (`flicky.zip` → "Fujitsu - FM-7", `frogger.zip` → "APF - Imagination Machine") con confianza `low`, en vez de matchear contra el catálogo arcade correcto (Pass 3, que nunca llega a probarse porque Pass 2 ya "acertó"). Detectado 2026-07-08 al re-lanzar el match sobre `Unknown\` — son matches **preexistentes**, no introducidos hoy. Fix: para nombres sin región/paréntesis, probar primero el catálogo arcade (Pass 3) antes que el name-fallback No-Intro/Redump (Pass 2), o exigir una señal más fuerte que la sola coincidencia de título normalizado. | `catalog/matcher.py` | ⬜ |

> Quedan pendientes: INBOX-FIX-4 (decisión de diseño sobre auto-apply del wizard),
> MATCH-FIX-1 (prioridad del matcher), y la decisión del usuario sobre las 15
> colecciones completas de JUNK-REVIEW-1 (categoría 2).

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
| ONB-9 | ⚪ Bajo | **Decisión de idioma/audiencia del README** — todo en español; si el repo también sirve de portfolio internacional, añadir un TL;DR en inglés al inicio (qué es, stack, screenshot) sin traducir el resto. Decisión del usuario. | `README.md` | ⬜ |

> **Completado 8/9** (PRs #71–#74). Solo queda **ONB-9** (TL;DR en inglés del README —
> decisión del usuario). Detalle: `Tareas/Roadmap-Onboarding.md`.

---

## User actions (no code needed)

| ID | Task |
|----|------|
| STRUCT-4 | Configure RetroArch PC: Saving → Savefile Directory → `E:\Carpetas anbernic\saves\` |
| STRUCT-3 | Update `config.toml`: `local_dir = "E:\\Carpetas anbernic\\saves"` (after STRUCT-4) |
| ES-1 | Download `genesis_plus_gx` core in RetroArch → Online Updater |
| ES-2 | Configure Citra (3DS) in EmulationStation |
