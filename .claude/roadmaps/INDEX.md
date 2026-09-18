# Roadmaps — Retro Vault

Índice de planes de trabajo por rama. Cada archivo tiene el roadmap completo con pasos, código de ejemplo, commits y criterios de verificación.

Referencia de mejoras: ver [`../.claude/mejoras-por-rama.md`](../mejoras-por-rama.md)

---

## Ramas planificadas

| # | Archivo | Rama git | Estado | Prioridad |
|---|---------|----------|--------|-----------|
| 01 | [01-split-server-monolith.md](01-split-server-monolith.md) | `refactor/split-server-monolith` | **Completado** ✅ | 🔴 P1 |
| 02 | [02-split-sync-handler.md](02-split-sync-handler.md) | `refactor/split-sync-handler` | **Completado** ✅ | 🔴 P1 |
| 03 | [03-eliminate-late-imports.md](03-eliminate-late-imports.md) | `refactor/eliminate-late-imports` | **Completado** ✅ | 🟠 P2 |
| 04 | [04-consolidate-state.md](04-consolidate-state.md) | `refactor/consolidate-state` | **Completado** ✅ | 🟠 P2 |
| 05 | [05-consolidate-platform-dict.md](05-consolidate-platform-dict.md) | `refactor/consolidate-platform-dict` | **Completado** ✅ | 🟠 P2 |
| 06 | [06-tests-api-endpoints.md](06-tests-api-endpoints.md) | `tests/api-endpoints` | **Completado** ✅ | 🟠 P2 |
| 07 | — | `fix/remove-debug-prints` | **Obsoleto** — verificado 2026-09-13, sin superficie (ver nota) | 🟡 P3 |
| 08 | [08-fix-error-handling.md](08-fix-error-handling.md) | `fix/error-handling` | **Completado** ✅ (mergeado a `develop`, `84b05f7`) | 🟠 P2 |
| 09 | [09-config-handler-split.md](09-config-handler-split.md) | `refactor/config-handler-split` | **Completado** ✅ (mergeado a `develop`, `6952b37`) | 🟡 P3 |
| 10 | [10-i18n-translate-remaining-strings.md](10-i18n-translate-remaining-strings.md) | `i18n/translate-remaining-strings` | **Completado** ✅ (mergeado a `develop`, `0e430fb`) | 🟡 P3 |
| 11 | [11-cable-sync-android-root-canonical.md](11-cable-sync-android-root-canonical.md) | `fix/cable-sync-android-root-canonical` | **Completado** ✅ (mergeado a `develop`, `fc29e09` — checklist y backlog `CABLE-ROOT-1c/1d` seguían diciendo "pendiente de commit", corregido 2026-09-15) | 🔴 P1 |
| 12 | [12-dual-folder-title-case-slug.md](12-dual-folder-title-case-slug.md) | `fix/dual-folder-title-case-slug` | **Completado** ✅ (rama local, 2026-09-17 — pendiente confirmación del usuario para commit/PR a `develop`) | 🟠 P2 |
| 13 | [13-match-chdman-robustness.md](13-match-chdman-robustness.md) | `fix/match-chdman-robustness` | **Completado** ✅ (rama local, 2026-09-15 — pendiente PR a `develop`, ver nota abajo) | 🟠 P2 |
| 14 | [14-matcher-coverage-gaps.md](14-matcher-coverage-gaps.md) | `fix/matcher-coverage-gaps` | Pendiente | 🟡 P3 |
| 15 | [15-psx-cue-multitrack-integrity.md](15-psx-cue-multitrack-integrity.md) | `fix/psx-cue-multitrack-integrity` | **Completado** ✅ (mergeado a `develop`, `5bc4e06` — ver `PSX-CUE-DESYNC-1b` en el backlog) | 🔴 P1 |
| 16 | [16-cable-sync-format-gaps.md](16-cable-sync-format-gaps.md) | `fix/cable-sync-format-gaps` | Pendiente | 🟡 P3 |
| 17 | [17-inbox-pending-features.md](17-inbox-pending-features.md) | `feature/inbox-pending-features` | **Completado** ✅ — las 3 tareas hechas: `INBOX-ATOMIC-1`/`INBOX-RA-HASH-GAP` mergeadas a `develop` (2026-09-15), `INBOX-ANBERNIC-1` implementada 2026-09-17 (pendiente de commit/PR, ver checklist) | 🟠 P2 |
| 18 | [18-game-blocklist.md](18-game-blocklist.md) | `feature/game-blocklist` | Pendiente | 🟡 P3 |
| 19 | [19-device-profile-loose-data.md](19-device-profile-loose-data.md) | `feature/device-profile-loose-data` | Pendiente | 🟡 P3 |
| 20 | [20-rammu-machine-pending.md](20-rammu-machine-pending.md) | — (acciones manuales/hardware, sin rama única) | Pendiente | mixta |

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
