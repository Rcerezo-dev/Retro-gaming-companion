# Roadmaps — Retro Vault

Índice de planes de trabajo por rama. Cada archivo tiene el roadmap completo con pasos, código de ejemplo, commits y criterios de verificación.

Referencia de mejoras (histórico, análisis de 2026-06-15 — las 10 ramas propuestas ya están completadas, ver tabla de abajo): [`../.claude/mejoras-por-rama.md`](../mejoras-por-rama.md)

---

## Cómo usar este roadmap

Este archivo es el **roadmap general** — el punto de entrada de cada sesión de trabajo. Flujo:

1. **Lee este roadmap general** y mira la tabla de abajo: busca una fila "Activo" ordenando por prioridad. Luego confirma en `Tareas/backlog.md` qué tareas de esa rama siguen sin ✅ — esta tabla ya no repite ese detalle, solo dice si la rama está abierta o archivada.
2. **Lee el roadmap específico de esa rama** (`.claude/roadmaps/NN-nombre.md`, o `archivo/NN-nombre.md` si ya está archivada y solo quieres contexto histórico) — tiene el plan paso a paso, código de ejemplo y criterios de verificación. No lleva su propio checklist de estado.
3. **Crea `Tareas/diario/DíaXX.md`** para la sesión de hoy **solo si el trabajo no cabe entero en el roadmap específico** (p. ej. si aparece un hallazgo colateral no previsto, o si la sesión toca más de una rama). Si el roadmap específico ya tiene todo el detalle necesario, no hace falta diario aparte.
4. **Al completar una tarea**, márcala hecha en un único sitio: `Tareas/backlog.md` (fuente de verdad). Si la tarea tiene issue de GitHub asociado, marca también su checkbox ahí. El roadmap específico y esta tabla no llevan estado propio que sincronizar.
5. **Archiva los archivos sin tareas pendientes**: cuando ya no quede ninguna tarea sin ✅ en `Tareas/backlog.md` para esa rama, mueve el roadmap específico a `.claude/roadmaps/archivo/`, actualiza el enlace en la tabla de abajo y pon su fila en "Archivado". Un diario de una sesión ya cerrada se mueve igual a `Tareas/diario/archivo/`.
6. **Documenta lo que quede pendiente** en `Tareas/backlog.md` — es el único sitio que necesita reflejarlo.

**Hallazgos en vivo (bug encontrado investigando, no planificado)**: no necesitan roadmap propio en esta tabla — se documentan directamente en `Tareas/backlog.md` (sección del epic correspondiente), como ya se hace. Si el hallazgo termina en una rama con commit real, se añade una fila aquí a posteriori (ver filas 21/22) para que el registro de ramas quede completo, pero no hace falta planificarlo de antemano en un archivo `NN-nombre.md`.

---

## Ramas planificadas

Estado real (qué falta, qué se mergeó, número de PR) vive en `Tareas/backlog.md`,
sección del epic correspondiente — esta tabla solo dice si el roadmap sigue
abierto o ya se archivó.

| # | Archivo | Rama git | Estado | Prioridad |
|---|---------|----------|--------|-----------|
| 01 | [archivo/01-split-server-monolith.md](archivo/01-split-server-monolith.md) | `refactor/split-server-monolith` | Archivado | 🔴 P1 |
| 02 | [archivo/02-split-sync-handler.md](archivo/02-split-sync-handler.md) | `refactor/split-sync-handler` | Archivado | 🔴 P1 |
| 03 | [archivo/03-eliminate-late-imports.md](archivo/03-eliminate-late-imports.md) | `refactor/eliminate-late-imports` | Archivado | 🟠 P2 |
| 04 | [archivo/04-consolidate-state.md](archivo/04-consolidate-state.md) | `refactor/consolidate-state` | Archivado | 🟠 P2 |
| 05 | [archivo/05-consolidate-platform-dict.md](archivo/05-consolidate-platform-dict.md) | `refactor/consolidate-platform-dict` | Archivado | 🟠 P2 |
| 06 | [archivo/06-tests-api-endpoints.md](archivo/06-tests-api-endpoints.md) | `tests/api-endpoints` | Archivado | 🟠 P2 |
| 07 | — | `fix/remove-debug-prints` | Obsoleto (ver nota) | 🟡 P3 |
| 08 | [archivo/08-fix-error-handling.md](archivo/08-fix-error-handling.md) | `fix/error-handling` | Archivado | 🟠 P2 |
| 09 | [archivo/09-config-handler-split.md](archivo/09-config-handler-split.md) | `refactor/config-handler-split` | Archivado | 🟡 P3 |
| 10 | [archivo/10-i18n-translate-remaining-strings.md](archivo/10-i18n-translate-remaining-strings.md) | `i18n/translate-remaining-strings` | Archivado | 🟡 P3 |
| 11 | [archivo/11-cable-sync-android-root-canonical.md](archivo/11-cable-sync-android-root-canonical.md) | `fix/cable-sync-android-root-canonical` | Archivado | 🔴 P1 |
| 12 | [archivo/12-dual-folder-title-case-slug.md](archivo/12-dual-folder-title-case-slug.md) | `fix/dual-folder-title-case-slug` | Archivado | 🟠 P2 |
| 13 | [archivo/13-match-chdman-robustness.md](archivo/13-match-chdman-robustness.md) | `fix/match-chdman-robustness` | Archivado | 🟠 P2 |
| 14 | [archivo/14-matcher-coverage-gaps.md](archivo/14-matcher-coverage-gaps.md) | `fix/matcher-coverage-gaps` | Archivado | 🟡 P3 |
| 15 | [archivo/15-psx-cue-multitrack-integrity.md](archivo/15-psx-cue-multitrack-integrity.md) | `fix/psx-cue-multitrack-integrity` | Archivado | 🔴 P1 |
| 16 | [16-cable-sync-format-gaps.md](16-cable-sync-format-gaps.md) | `fix/cable-sync-format-gaps` | Activo | 🟡 P3 |
| 17 | [archivo/17-inbox-pending-features.md](archivo/17-inbox-pending-features.md) | `feature/inbox-pending-features` | Archivado | 🟠 P2 |
| 18 | [archivo/18-game-blocklist.md](archivo/18-game-blocklist.md) | `feature/game-blocklist` | Archivado | 🟡 P3 |
| 19 | [archivo/19-device-profile-loose-data.md](archivo/19-device-profile-loose-data.md) | `feature/device-profile-loose-data` | Archivado | 🟡 P3 |
| 20 | [20-rammu-machine-pending.md](20-rammu-machine-pending.md) | — (acciones manuales/hardware, sin rama única) | Activo | mixta |
| 21 | — (sin roadmap dedicado, hallazgo en vivo) | `fix/catalog-match-subset-hack` | Archivado | 🔴 P1 |
| 22 | — (sin roadmap dedicado, hallazgo en vivo) | `fix/dup-winners-non-canonical-guard` | Archivado | 🟠 P2 |
| 23 | [23-android-hash-rescan-dedup.md](23-android-hash-rescan-dedup.md) | — (operación de datos, sin rama por defecto) | Activo (parcial) | 🟠 P2 |
| 24 | [24-docs-audit-followups.md](24-docs-audit-followups.md) | — (limpieza de documentación, sin rama por defecto) | Activo | 🟡 P3 |
| 27 | [archivo/27-library-ux-dashboard-duplicates.md](archivo/27-library-ux-dashboard-duplicates.md) | `feature/library-ux-dashboard-duplicates` | Archivado | 🟡 P3 |

---

## Estados posibles

Solo tres — el detalle de qué falta vive en `Tareas/backlog.md`, no aquí:

- **Activo** — el roadmap sigue en `.claude/roadmaps/`, con trabajo pendiente
  (mira el backlog para saber cuánto). Cubre lo que antes eran "Pendiente" y
  "En curso" — esa distinción ya no se sincroniza en dos sitios.
- **Archivado** — 100% completado, movido a `.claude/roadmaps/archivo/`. El
  backlog tiene el enlace a la PR/commit si hace falta el detalle.
- **Obsoleto** — verificado contra el código real y el problema original ya no
  existe (resuelto sin querer por otro cambio, o nunca fue tan extendido como
  se documentó).

---

## Notas de verificación

**2026-09-24 — simplificación de convención:** las notas de abajo (08-11/15,
17) son todas el mismo patrón: el mismo hecho ("¿está mergeado?") vivía en el
checklist del roadmap, en esta tabla y en `Tareas/backlog.md`, y bastaba con
que uno de los tres no se actualizara para que el registro mintiera. A partir
de hoy `Tareas/backlog.md` es la única fuente de estado; esta tabla solo
distingue Activo/Archivado/Obsoleto (ver "Estados posibles" arriba) y los
roadmaps específicos ya no llevan checklist de estado propio. Las notas
históricas se dejan tal cual como registro de por qué se cambió.

**08/09/10/11/15 (2026-09-15):** esta tabla decía "Pendiente" para las cinco,
pero el código ya estaba mergeado a `develop` desde el 2026-09-13 (08, 09, 10,
11) y el 2026-09-15 (15) — verificado con `git log --oneline develop` y
`grep` de los símbolos que cada roadmap introduce, no asumido del propio
índice. La causa más probable: el checklist de cada roadmap y las filas
correspondientes de `Tareas/backlog.md` se quedaron con "pendiente de
commit/PR" después de que el commit y merge sí ocurrieran — la actualización
de estado dependía de un paso manual que no se hizo. Ver también la nota de
atribución de `PSX-CUE-DESYNC-1b` (sesión de hoy) — mismo patrón general de
que el registro puede desincronizarse del código real, razón de más para
verificar contra `git log`/el código antes de confiar en esta tabla.

**17 — `feature/inbox-pending-features` (2026-09-17):** mismo patrón que la
nota de abajo — el checklist de `INBOX-RA-HASH-GAP` decía "pendiente de
mergear" pero ya estaba en `develop` desde `c6e19f9` (más un hallazgo
colateral ya mergeado por separado, `241b1ae`), verificado con
`git log --oneline --all | grep inbox-ra-hash`. `INBOX-ANBERNIC-1` (la única
tarea real pendiente) se implementó en esta sesión: diseño confirmado con el
usuario (checkbox global, no persistido), función `_send_organized_to_anbernic()`
sobre el primitivo `AdbTransport.push()` en vez del job completo de
cable-sync, 4 tests nuevos.

**07 — `fix/remove-debug-prints` (2026-09-13):** el problema original de
`mejoras-por-rama.md` (`server.py:831-835`, 4 `print(f"[DEBUG] ...")`) ya no
existe — `grep -rn "\[DEBUG\]" src/rom_manager/` no encuentra nada, y
`grep -rln "print(" src/rom_manager/ --include="*.py"` solo devuelve
`cli.py`/`wizard.py` (salida de terminal legítima de la CLI, no restos de
depuración — `web/` no tiene ningún `print()`). Probablemente se resolvió
durante los refactors de `server.py` (roadmaps 01-05, completados). No se
creó roadmap para esta rama — no hay nada que implementar.
