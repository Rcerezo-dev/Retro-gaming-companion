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
