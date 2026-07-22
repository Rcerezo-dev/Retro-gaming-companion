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
2. **TABS-FIX-6** — pantalla única "Revisar copias": fusiona duplicados
   SHA1, duplicados semánticos, versiones RA y colisiones del plan en una
   cola por juego con recomendación precalculada (RA > mejor nombrada >
   primera, lógica ya en `ra_duplicates_service.py`). Absorbe de paso
   TABS-FIX-2 (3 UIs para el mismo criterio RA), TABS-FIX-3 (botón que
   ignora RA) y TABS-FIX-4 (textos de borrado que mienten sobre
   `_descartados/`). Esfuerzo L — es el grueso de la sesión.
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
