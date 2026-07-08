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
| SAGE-1 | **Scraping masivo de descripciones** (bloqueante Sage v0.2) — completar las descripciones de la biblioteca por lotes desde la fuente del scraper puntual. Reanudable (no re-scrapear lo ya descargado), rate-limit razonable, descripciones visibles en `GET /api/export-history`. Hecho cuando >90% de los juegos tienen descripción no vacía en el export. | `database/repositories/metadata.py`, `web/handlers/scraper.py`, `web/builders/misc.py`, `tab-scraper.html`, `scraper.js` | 🟡 código listo (rama `feature/sage-1-mass-descriptions`): el job `/api/scrape` ya era reanudable+rate-limited; añadido modo `missing_descriptions` (re-scrapea metadata con descripción vacía sin machacar imágenes), cobertura en `/api/scrape-summary` + UI (hoy 70.0%). Pasada real 2026-07-07: 964 en cola, 860 match, 0 errores (tras fix `_loads_lenient`, PR #79) pero cobertura 70,0→70,1% — los re-scrapeados no tienen sinopsis en SS. Para >90% hay que resetear `metadata_scraped` de los ~4.700 sin match histórico y re-scrapear (~89% de acierto hoy), o usar otra fuente. **Experimento reset 2026-07-07: fallido** — la cola de 4.692 era basura no-juego (chips de romsets arcade, shaders RetroArch, restos de Papelera `$I*.iso`, firmware): 415 procesados, 6 match. Flags revertidos. **Camino real al >90%: limpiar la basura de la biblioteca** (junk-scan restaurado en PR #80) — al quitar ~4.700 no-juegos del denominador, 13.217/~14.150 ≈ 93% |
| SAGE-2 | **Migración `genres_list` / `players` persistidos** (bloqueante Sage v0.2) — persistir ambos campos en la BD (hoy derivados al vuelo) con backfill de registros existentes, y exponerlos en el export. Hecho cuando aparecen estables en `/api/export-history` y el contrato queda documentado en `play_history.py`. Detalle: `docs/ideas/propuestas-recomendador-nlp.md`. | `database/`, `database/repositories/play_history.py` | ⬜ |
| SAGE-3 | **Registro de recomendaciones mostradas/clicadas** (futuro, Sage v0.4) — para el bucle de feedback de Sage: registrar qué recomendaciones se mostraron en el panel y cuáles se clicaron, y exponerlo (export o endpoint nuevo). **No implementar todavía**: el diseño se negocia cuando Sage llegue a v0.4. | — | ⬜ |

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
