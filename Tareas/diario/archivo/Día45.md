# ROM Manager Local — Día 45 (roadmap)

## Contexto

Día44 cerró VAL-FIX-1/2 y TABS-FIX-1 (causa raíz común: rutas de
dispositivo tratadas como "no existe"). Desde entonces, sin diario propio,
se cerraron SETTINGS-UX-1/2/4/5 (#150), SCRAPER-UX-1..7 (#151), TV-UX-1..5
(#152), REV43-33/34/35/39/40/42 (#153) y HERR-UX-1..11 (rama
`feature/herr-ux`, ya reflejado en el backlog). La rama actual
`fix/tabs-fix-1a` acaba de completar también la parte (a) de TABS-FIX-1
(borrado real vía ADB) — con esto **TABS-FIX-1 queda 100% cerrado**.

Quedan sueltos de la revisión TABS-FIX (2026-07-13) los hallazgos 2, 3, 4, 5
y 6, con orden ya decidido en el propio backlog: **5 primero** (fix aislado
de seguridad), **6 después** (absorbe 2, 3 y 4).

## Objetivos de hoy

1. ~~**TABS-FIX-5**~~ ✅ — verificado contra el código real: es un duplicado
   de `DUPLICADOS-UX-1` (mismo bug, mismas líneas), ya arreglado en PR #132
   (`fix/duplicados-ux`, `023aafe`). `deleteAllDuplicates()` ya manda
   `platform` en el payload y `delete_all_duplicates()` ya filtra los grupos
   por plataforma antes de borrar. Nada que implementar — solo se corrigió
   la entrada del backlog (mismo patrón que DAT-FIX-1/INICIO-FIX-1 en
   Día44).
2. ~~**TABS-FIX-6**~~ ✅ — pantalla única "Revisar copias" (rama
   `feature/tabs-fix-6-revisar-copias`, sin PR todavía). Fusiona duplicados
   SHA1, duplicados semánticos, versiones RA y colisiones del plan en una
   cola por juego (Union-Find por SHA1 o `canonical_title` exacto — nunca
   mezcla PC/Android). Absorbe TABS-FIX-2/3, y TABS-FIX-4 resultó tener
   menos alcance real del esperado (solo un texto engañoso, el resto ya
   estaba bien redactado). Backend con plan de agente (Explore ×2 + Plan),
   luego implementación propia. **2 bugs de severidad alta encontrados
   probando contra la biblioteca real de datos** (no sintética) antes de dar
   la tarea por cerrada: agrupar por título normalizado fusionaba 18
   versiones regionales de un mismo juego en un "duplicado" (corregido a
   coincidencia exacta de `canonical_title`), y la recomendación de grupos
   `disk`/`collision` podía caer a orden alfabético en vez de al criterio RA
   por un campo (`conflict_role`) que depende de que el archivo exista en
   disco. Encontrado de paso un bug preexistente del planner con sets
   multi-disco (**TABS-FIX-6-DISC**, documentado en el backlog, no
   arreglado — fuera de alcance de hoy). 897 tests (22 nuevos), suite
   completa en verde.
3. **Si queda tiempo, quick wins de Sync (Pilar 3, prioridad real del
   proyecto):**
   - VAL-FIX-3 — rutas relativas de `tools/adb.exe` con `/` rompen
     `subprocess` en Windows (`CreateProcess` exige `\`); fix en
     `config.py` (`load_config()`), cubre adb/chdman/rclone de golpe.
   - VAL-FIX-6 — aviso de ruta SD se muestra también en modo ADB
     (`sync.js:795-796`).
4. **Si sobra margen:** ANBERNIC-UX-9 (cachear check de firewall en
   `/api/local-url`) o ANBERNIC-UX-10 (token de setup por sesión, no
   global) — ambos XS.

## Referencia (backlog)

| ID | Task | Esfuerzo |
|----|------|----------|
| TABS-FIX-5 | Borrado masivo ignora filtro de plataforma | S |
| TABS-FIX-6 | Pantalla única "Revisar copias" (absorbe 2/3/4) | L |
| VAL-FIX-3 | Rutas de tools con `/` rompen subprocess en Windows | S |
| VAL-FIX-6 | Aviso SD/MTP visible en modo ADB | S |
| ANBERNIC-UX-9 | `_check_firewall` sin cachear en cada `/api/local-url` | XS |
| ANBERNIC-UX-10 | Token de setup: slot global en vez de por sesión | XS |

No entran hoy (quedan para otra sesión): VAL-FIX-4/5/7 (sync por cable,
menor prioridad que 3/6), MEJ-2..5, SAGE-2/3 (bloqueantes de una fase de
Sage que aún no ha llegado), TEST-GAP-1, REV43-52, D37-8 (requiere PC
ajeno).

## Trabajo realizado

Rama `feature/tabs-fix-6-revisar-copias` (creada desde `fix/tabs-fix-1a`,
sin PR todavía), 4 commits desde el inicio de la sesión:

1. `864e06d` — doc: TABS-FIX-5 = duplicado de DUPLICADOS-UX-1 (ya cerrado
   en PR #132) + creación de este roadmap.
2. `fe18899` — backend de TABS-FIX-6: `_build_review_queue()`/
   `_review_groups_for_repo()` en `web/builders/duplicates.py` (Union-Find
   por repo: dos archivos son "el mismo juego" si comparten SHA1 o
   `(plataforma, canonical_title exacto)` — nunca mezcla PC/Android); tabla
   nueva `excluded_duplicate_groups` + métodos en `DuplicatesMixin`
   (`database/repositories/duplicates.py`, `database/schema.py`);
   `apply_all_review_recommendations()` en `services/ra_duplicates_service.py`
   (compone `resolve_duplicate_ra` + `apply_ra_conflicts` sin tocarlos);
   endpoints `GET /api/review-queue`, `POST /api/review-queue/exclude`,
   `POST /api/review-queue/apply-all` en `web/handlers/duplicates.py`.
3. `9f82ea6` — frontend: `tabs/review_copies.js` (nuevo) montado como
   sección "2. Revisar copias" en `tab-plan.html`; `tab-duplicates.html` +
   entrada de nav eliminados; `duplicates.js` reducido al selector de
   contexto PC/Android de Herramientas (lo único que seguía vivo);
   `organize.js` pierde `deleteCollisionDuplicates()` (contradecía el
   criterio RA) y el botón suelto "Resolver con RA". Este mismo commit
   incluye 2 bugs de severidad alta encontrados **probando contra la
   biblioteca real del usuario** (no solo datos sintéticos) antes de dar la
   tarea por cerrada:
   - Agrupar por título normalizado (sin tags de región, como hace RA)
     fusionó 18 versiones regionales distintas de Final Fantasy VII en un
     solo grupo "duplicado" — habría permitido borrar 17 juegos legítimos
     de un click. Corregido a coincidencia **exacta** de `canonical_title`
     (mismo criterio que ya usaba `get_title_duplicate_groups()`).
   - La recomendación de grupos `disk`/`collision` usaba `conflict_role`
     (que depende de que el archivo exista físicamente en disco) en vez del
     `ra_supported` ya calculado — podía caer a orden alfabético en vez del
     criterio RA. `_review_entry_sort_key()` simplificado a un único
     criterio uniforme.
4. `b196477` — doc: TABS-FIX-2/3/4/6 marcados `✅` en el backlog +
   **TABS-FIX-6-DISC** documentado (bug preexistente del planner con sets
   multi-disco: canonical_title idéntico entre discos hace que
   `collision_resolver` los marque como colisión, y "Resolver con RA"
   podría descartar Disc 2/3 pensando que son copias alternativas —
   encontrado al probar TABS-FIX-6 contra la biblioteca real, **no
   arreglado**, fuera de alcance de hoy).

897 tests en verde (22 nuevos), lint y formato limpios (`ruff check` +
`ruff format --check`) antes de cada commit.

## Archivos modificados

- Backend: `database/schema.py`, `database/repositories/duplicates.py`,
  `services/ra_duplicates_service.py`, `web/builders/duplicates.py`,
  `web/handlers/duplicates.py`.
- Frontend: `web/static/js/tabs/review_copies.js` (nuevo),
  `web/static/js/tabs/duplicates.js` (reducido), `web/static/js/tabs/organize.js`,
  `web/static/js/tabs/overview.js`, `web/static/js/main.js`, `web/static/js/api.js`,
  `web/static/partials/tab-plan.html`, `web/static/partials/_nav.html`,
  `web/static/index.html`; borrado `web/static/partials/tab-duplicates.html`.
- Tests: `tests/test_builders_duplicates.py` (nuevo), `tests/test_ra_duplicates_service.py`,
  `tests/web/test_duplicates_handler.py`.
- `Tareas/backlog.md`, `Tareas/diario/dia45.md` (este archivo).

## Estado al finalizar

Objetivo 1 (TABS-FIX-5) y objetivo 2 (TABS-FIX-6) completos y commiteados
en `feature/tabs-fix-6-revisar-copias` — **rama sin PR ni merge a
`develop` todavía**. No se llegó a los objetivos 3 (VAL-FIX-3/6) ni 4
(ANBERNIC-UX-9/10) — la sesión se llenó con TABS-FIX-6 (esfuerzo L
confirmado) más el tiempo extra de investigar y arreglar los 2 bugs reales
encontrados al probar contra la biblioteca real.

Verificado con: suite completa (`pytest`, 897 tests), servidor real
(`rommgr serve`) + `curl` contra la biblioteca real del usuario en modo
solo-lectura (nunca se invocó ningún endpoint destructivo contra sus datos
reales), y comprobación estática del HTML/JS servido. **No se pudo probar
en un navegador real** — la extensión de Chrome no estaba conectada en
esta sesión.

Pendiente antes de mergear: revisión visual en navegador de la pantalla
"Revisar copias" (confirmar aspecto de badges, `<details>`, y que los 3
botones por grupo funcionan de extremo a extremo).

## Siguiente sesión recomendada

1. **Revisión visual en navegador** de `feature/tabs-fix-6-revisar-copias`
   antes de abrir el PR (ver "Pendiente" arriba).
2. **VAL-FIX-3** — rutas de `tools/adb.exe` con `/` rompen `subprocess` en
   Windows (`config.py`, `load_config()`).
3. **VAL-FIX-6** — aviso de ruta SD visible en modo ADB (`sync.js:795-796`).
4. Si sobra margen: ANBERNIC-UX-9/10 (ambos XS).
5. **TABS-FIX-6-DISC** (nuevo, encontrado hoy) — bug preexistente del
   planner con sets multi-disco, ver backlog para el fix propuesto
   (`operation_planner.py`/`_canonical_filename` o excluir sets multi-disco
   en `collision_resolver`/`apply_ra_conflicts`).
