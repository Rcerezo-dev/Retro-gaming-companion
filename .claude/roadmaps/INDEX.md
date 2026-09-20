# Roadmaps — Retro Vault

Índice de planes de trabajo por rama. Cada archivo tiene el roadmap completo con pasos, código de ejemplo, commits y criterios de verificación.

Referencia de mejoras (histórico, análisis de 2026-06-15 — las 10 ramas propuestas ya están completadas, ver tabla de abajo): [`../.claude/mejoras-por-rama.md`](../mejoras-por-rama.md)

---

## Cómo usar este roadmap

Este archivo es el **roadmap general** — el punto de entrada de cada sesión de trabajo. Flujo:

1. **Lee este roadmap general** y mira la tabla de abajo: busca una fila "Pendiente" (o "En curso") ordenando por prioridad. Esa es la rama a coger.
2. **Lee el roadmap específico de esa rama** (`.claude/roadmaps/NN-nombre.md`, o `archivo/NN-nombre.md` si ya está completada y solo quieres contexto histórico) — tiene el plan paso a paso, código de ejemplo y criterios de verificación.
3. **Crea `Tareas/diario/DíaXX.md`** para la sesión de hoy **solo si el trabajo no cabe entero en el roadmap específico** (p. ej. si aparece un hallazgo colateral no previsto, o si la sesión toca más de una rama). Si el roadmap específico ya tiene todo el detalle necesario, no hace falta diario aparte.
4. **Al completar una tarea**, márcala hecha en los tres sitios: el checklist del roadmap específico, la fila de este roadmap general (columna Estado), y la entrada correspondiente en `Tareas/backlog.md` (tanto el índice por rama como la sección de la tarea).
5. **Archiva los archivos sin tareas pendientes**: un roadmap específico 100% completado se mueve a `.claude/roadmaps/archivo/`; un diario de una sesión ya cerrada se mueve a `Tareas/diario/archivo/`. Actualiza los enlaces de este índice para que apunten a la ruta archivada.
6. **Documenta lo que quede pendiente** — en el backlog si es una tarea nueva derivada, o en la nota de verificación de este archivo si afecta al propio roadmap general.

**Hallazgos en vivo (bug encontrado investigando, no planificado)**: no necesitan roadmap propio en esta tabla — se documentan directamente en `Tareas/backlog.md` (sección del epic correspondiente), como ya se hace. Si el hallazgo termina en una rama con commit real, se añade una fila aquí a posteriori (ver filas 21/22) para que el registro de ramas quede completo, pero no hace falta planificarlo de antemano en un archivo `NN-nombre.md`.

---

## Ramas planificadas

| # | Archivo | Rama git | Estado | Prioridad |
|---|---------|----------|--------|-----------|
| 01 | [archivo/01-split-server-monolith.md](archivo/01-split-server-monolith.md) | `refactor/split-server-monolith` | **Completado** ✅ | 🔴 P1 |
| 02 | [archivo/02-split-sync-handler.md](archivo/02-split-sync-handler.md) | `refactor/split-sync-handler` | **Completado** ✅ | 🔴 P1 |
| 03 | [archivo/03-eliminate-late-imports.md](archivo/03-eliminate-late-imports.md) | `refactor/eliminate-late-imports` | **Completado** ✅ | 🟠 P2 |
| 04 | [archivo/04-consolidate-state.md](archivo/04-consolidate-state.md) | `refactor/consolidate-state` | **Completado** ✅ | 🟠 P2 |
| 05 | [archivo/05-consolidate-platform-dict.md](archivo/05-consolidate-platform-dict.md) | `refactor/consolidate-platform-dict` | **Completado** ✅ | 🟠 P2 |
| 06 | [archivo/06-tests-api-endpoints.md](archivo/06-tests-api-endpoints.md) | `tests/api-endpoints` | **Completado** ✅ | 🟠 P2 |
| 07 | — | `fix/remove-debug-prints` | **Obsoleto** — verificado 2026-09-13, sin superficie (ver nota) | 🟡 P3 |
| 08 | [archivo/08-fix-error-handling.md](archivo/08-fix-error-handling.md) | `fix/error-handling` | **Completado** ✅ (mergeado a `develop`, `84b05f7`) | 🟠 P2 |
| 09 | [archivo/09-config-handler-split.md](archivo/09-config-handler-split.md) | `refactor/config-handler-split` | **Completado** ✅ (mergeado a `develop`, `6952b37`) | 🟡 P3 |
| 10 | [archivo/10-i18n-translate-remaining-strings.md](archivo/10-i18n-translate-remaining-strings.md) | `i18n/translate-remaining-strings` | **Completado** ✅ (mergeado a `develop`, `0e430fb`) | 🟡 P3 |
| 11 | [archivo/11-cable-sync-android-root-canonical.md](archivo/11-cable-sync-android-root-canonical.md) | `fix/cable-sync-android-root-canonical` | **Completado** ✅ (mergeado a `develop`, `fc29e09` — checklist y backlog `CABLE-ROOT-1c/1d` seguían diciendo "pendiente de commit", corregido 2026-09-15) | 🔴 P1 |
| 12 | [archivo/12-dual-folder-title-case-slug.md](archivo/12-dual-folder-title-case-slug.md) | `fix/dual-folder-title-case-slug` | **Completado** ✅ (mergeado a `develop`, PR #316, 2026-09-18) | 🟠 P2 |
| 13 | [archivo/13-match-chdman-robustness.md](archivo/13-match-chdman-robustness.md) | `fix/match-chdman-robustness` | **Completado** ✅ (mergeado a `develop`, `fcf83b1`) | 🟠 P2 |
| 14 | [14-matcher-coverage-gaps.md](14-matcher-coverage-gaps.md) | `fix/matcher-coverage-gaps` | Pendiente | 🟡 P3 |
| 15 | [archivo/15-psx-cue-multitrack-integrity.md](archivo/15-psx-cue-multitrack-integrity.md) | `fix/psx-cue-multitrack-integrity` | **Completado** ✅ (mergeado a `develop`, `5bc4e06` — ver `PSX-CUE-DESYNC-1b` en el backlog) | 🔴 P1 |
| 16 | [16-cable-sync-format-gaps.md](16-cable-sync-format-gaps.md) | `fix/cable-sync-format-gaps` | Pendiente | 🟡 P3 |
| 17 | [archivo/17-inbox-pending-features.md](archivo/17-inbox-pending-features.md) | `feature/inbox-pending-features` | **Completado** ✅ — las 3 tareas mergeadas a `develop`: `INBOX-ATOMIC-1`/`INBOX-RA-HASH-GAP` (2026-09-15), `INBOX-ANBERNIC-1` (PR #315, 2026-09-18) | 🟠 P2 |
| 18 | [18-game-blocklist.md](18-game-blocklist.md) | `feature/game-blocklist` | Pendiente | 🟡 P3 |
| 19 | [19-device-profile-loose-data.md](19-device-profile-loose-data.md) | `feature/device-profile-loose-data` | Pendiente | 🟡 P3 |
| 20 | [20-rammu-machine-pending.md](20-rammu-machine-pending.md) | — (acciones manuales/hardware, sin rama única) | Pendiente | mixta |
| 21 | — (sin roadmap dedicado, hallazgo en vivo) | `fix/catalog-match-subset-hack` | **Completado** ✅ (mergeado a `develop`, PR #317, 2026-09-18 — ver `CATALOG-MATCH-SUBSET-1` en `Tareas/backlog.md`) | 🔴 P1 |
| 22 | — (sin roadmap dedicado, hallazgo en vivo) | `fix/dup-winners-non-canonical-guard` | **Completado** ✅ (mergeado a `develop`, PR #318, 2026-09-18 — ver `CATALOG-MATCH-SUBSET-1` en `Tareas/backlog.md`) | 🟠 P2 |
| 23 | [23-android-hash-rescan-dedup.md](23-android-hash-rescan-dedup.md) | — (operación de datos, sin rama por defecto) | **Fases 1-2 completadas** ✅ (2026-09-20 — ver `ANDROID-DUP-2` en `Tareas/backlog.md`); Fase 3 (discos) pendiente de decisión del usuario | 🟠 P2 |
| 24 | [24-docs-audit-followups.md](24-docs-audit-followups.md) | — (limpieza de documentación, sin rama por defecto) | Pendiente | 🟡 P3 |

---

## Estados posibles

- **Pendiente** — roadmap listo, trabajo no iniciado
- **En curso** — rama creada, trabajo en progreso
- **Completado** — PR mergeado a main
- **Sin roadmap** — entrada en mejoras-por-rama.md pero roadmap no redactado aún
- **Obsoleto** — verificado contra el código real y el problema original ya no existe (resuelto sin querer por otro cambio, o nunca fue tan extendido como se documentó)

---

## Notas de verificación

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
