# Roadmap 32 — Próximas actividades (2026-10-03)

**Rama:** sin rama única — cada tarea se corta en la suya (`fix/…`, `feature/…`), PR a `develop`
**Prioridad:** orden de los 3 pilares (CLAUDE.md): sync de saves > Inbox > organización inicial > resto
**Estado de cada tarea:** solo en `Tareas/backlog.md` (este archivo es plan, no checklist)

> Cierra la sesión de SAVE-GUARD / ANDROID-BATTERY (PRs #399-#402). El índice por
> rama del backlog (`## Índice por rama`) tiene filas 🔴/🟡 **desincronizadas** (p. ej.
> `ANDROID-DUP-2` ya está aplicado): **antes de empezar cualquier tarea de este
> roadmap, verificar su estado real en su sección del backlog.**

---

## Fase 0 — Cerrar lo ya mergeado (requiere hardware y al usuario)

| Actividad | Qué | Bloqueo |
|-----------|-----|---------|
| ANDROID-BATTERY-1 (medir) | Tramos A/B del plan bajo la fila en el backlog; criterio: app < ~2-3 % de la batería gastada | Consola desenchufada varias horas |
| SAVE-GUARD-2 (probar en Android) | `.sav` de 0 bytes con mtime posterior sobre un juego de prueba; Dropbox intacto, 1 conflicto contado | APK de `develop` ya instalado (17:38 del 2026-10-03) |
| SAVE-GUARD-1 (pendiente menor) | Revisar `sync_log` de la BD por si hubo algún 0 bytes subido antes de la guarda | Ninguno |
| V1-V5 (backlog, "Validación en hardware") | SD auto-sync, Inbox end-to-end, RA con API key real, guía Termux | Usuario con hardware / API key |

## Fase 1 — Pilar 3: blindar el sync (prioridad absoluta)

1. **SAVES-FRAGMENT-3/4/5** — arcade NVRAM en 5 ubicaciones, GameCube/Wii en 3, cada standalone con su path: el riesgo es *progreso que no viaja*. Verificar si siguen abiertos; decidir un convenio único antes de tocar código (regla: investigar antes de arreglar).
2. **GBA-SAVE-PATH-1 / LIBRARY-SYNC-STALE-1** — saves "perdidos" tras corregir la biblioteca sin sincronizar a la consola. Confirmar estado.
3. **CABLE-ROOT-1** (🟡) y **CABLE-ROM-FIX** (roadmap 16): Cable Sync no compara con el destino.
4. Si la medición de batería no cumple el criterio: periódico a 60 min con Instantáneo activo, ignorar eventos del propio sync, Wi-Fi-only.

## Fase 2 — Pilar 2: Inbox

5. **ZIP-ROUTE** (🟡) — cerrar lo pendiente tras `web/zip_router.py`.
6. Roadmap 14 (`MATCH-FIX-3`): colisiones de nombre cuando el catálogo no conoce el hash.

## Fase 3 — Pilar 1: biblioteca (solo lo que siga abierto tras verificar)

7. `ARCADE-RENAME-BUG-1`, `LIBRARY-CLEANUP-GAPS-1`, `HEALTH-CHECK-1`, `GAMECUBE-DISC-BUG-1`, `DUALFOLDER-12`, `JUNK-SCAN-RUBEN-1` (6.072 archivos / 34,97 GB medidos, nada aplicado; dry-run primero).
8. Roadmap 29 (estandarización de carpetas ES-DE / ROM hacks): arranca con la sesión de decisión `ESDE-FOLDER-STD-1`, no con código.

## Fase 4 — Secundario y nuevas ideas (cuando 1-3 estén estables)

| Idea | Nota |
|------|------|
| `RA-PROGRESS-UI-1` (roadmap 31) | Bloqueada hasta validar la API key de RA real |
| `SAGE-4` recomendador | Propuestas A+C sin ML; "qué jugar" por playtime + logros pendientes cabe aquí; el NLP pesado va a su repo (retro-sage) por la regla "solo stdlib" |
| `HEALTH-SCORE`, `COLLECTION-EXPORT` | Baratas, reusan datos ya calculados |
| `DEVICE-PROFILES-MULTI` | Solo con hardware a mano; comprobar primero que `platforms.toml`/`device_profile.py` abstraen el dispositivo |
| `MOBILE-UI-1` (roadmap 30), `ANDROID-DRIVE-1` (roadmap 28), `MODS-AUTO`, `LIBRARY-MANAGER-UI`, `TRUST-MODE` | Roadmap general de ideas: `Tareas/Roadmap-212-Ideas-Futuras.md`; `TRUST-MODE` choca con la decisión INBOX-FIX-4 — replantear con el usuario |
| Distribución | `D37-8` (probar `RetroVault-Setup.exe` en PC limpio, vigilar gap de adb/chdman) |

## Orden recomendado para las próximas 3 sesiones

1. Medición de batería + prueba de la guarda (Fase 0) — corta, con la consola.
2. Auditoría de estado real del backlog (Índice por rama) para limpiar filas obsoletas — evita trabajar sobre hallazgos ya resueltos.
3. SAVES-FRAGMENT-3/4/5 (Fase 1.1): decisión de convenio con el usuario, luego rama.

## No hacer

- Convertir Retro Vault en launcher/front-end.
- Más herramientas secundarias antes de blindar el sync.
- Repo nuevo: el único candidato (retro-sage) ya tiene el suyo.
