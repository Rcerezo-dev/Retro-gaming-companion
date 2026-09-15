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
| 08 | [08-fix-error-handling.md](08-fix-error-handling.md) | `fix/error-handling` | Pendiente | 🟠 P2 |
| 09 | [09-config-handler-split.md](09-config-handler-split.md) | `refactor/config-handler-split` | Pendiente | 🟡 P3 |
| 10 | [10-i18n-translate-remaining-strings.md](10-i18n-translate-remaining-strings.md) | `i18n/translate-remaining-strings` | Pendiente | 🟡 P3 |
| 11 | [11-cable-sync-android-root-canonical.md](11-cable-sync-android-root-canonical.md) | `fix/cable-sync-android-root-canonical` | Pendiente | 🔴 P1 |
| 12 | [12-dual-folder-title-case-slug.md](12-dual-folder-title-case-slug.md) | `fix/dual-folder-title-case-slug` | Pendiente | 🟠 P2 |
| 13 | [13-match-chdman-robustness.md](13-match-chdman-robustness.md) | `fix/match-chdman-robustness` | Pendiente | 🟠 P2 |
| 14 | [14-matcher-coverage-gaps.md](14-matcher-coverage-gaps.md) | `fix/matcher-coverage-gaps` | Pendiente | 🟡 P3 |
| 15 | [15-psx-cue-multitrack-integrity.md](15-psx-cue-multitrack-integrity.md) | `fix/psx-cue-multitrack-integrity` | Pendiente | 🔴 P1 |
| 16 | [16-cable-sync-format-gaps.md](16-cable-sync-format-gaps.md) | `fix/cable-sync-format-gaps` | Pendiente | 🟡 P3 |
| 17 | [17-inbox-pending-features.md](17-inbox-pending-features.md) | `feature/inbox-pending-features` | Pendiente | 🟠 P2 |
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

**07 — `fix/remove-debug-prints` (2026-09-13):** el problema original de
`mejoras-por-rama.md` (`server.py:831-835`, 4 `print(f"[DEBUG] ...")`) ya no
existe — `grep -rn "\[DEBUG\]" src/rom_manager/` no encuentra nada, y
`grep -rln "print(" src/rom_manager/ --include="*.py"` solo devuelve
`cli.py`/`wizard.py` (salida de terminal legítima de la CLI, no restos de
depuración — `web/` no tiene ningún `print()`). Probablemente se resolvió
durante los refactors de `server.py` (roadmaps 01-05, completados). No se
creó roadmap para esta rama — no hay nada que implementar.
