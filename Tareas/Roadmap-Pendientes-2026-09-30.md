# Roadmap — Procesos sin terminar (a fecha 2026-09-30)

> Generado comprobando el estado real (branches, PRs, CI, `git merge-tree`)
> contra lo que dice `Tareas/diario/Día71.md` y `Tareas/backlog.md`. No es un
> roadmap de una sola rama — agrupa todo lo que quedó a medias más lo
> siguiente por prioridad del backlog. Sirve de punto de entrada para las
> próximas sesiones; el detalle de estado por tarea sigue viviendo solo en
> `Tareas/backlog.md`.

> ✅ **Frente 0 y Frente 1 cerrados en la misma sesión (2026-09-30)**: #375 y
> #373 mergeadas directo; #338 y #339 rescatadas (rebase real contra
> `develop`, 9 y 12 conflictos resueltos respectivamente, suites 1503/1503 y
> 1515/1515 en verde) y mergeadas — Pilar 3 (`SYNC-CONFLICT-MANUAL-1`,
> `SAVES-CONFLICT-CTX-1`) y Pilar 2 (`INBOX-SESSION-SUMMARY-1`,
> `INBOX-METADATA-INLINE-1`) al día. Hallazgo colateral del rescate: el
> merge de #339 reintrodujo 4 roadmaps duplicados sin renumerar (limpiado en
> PR #382). `docs/native-save-sync-1-dusklight-ruben` sigue sin PR — no
> abordado esta sesión. Frentes 2-4 (crossfmt PSX, GBC dedup, ARMSX2,
> bloqueados) siguen tal cual, ver debajo.

---

## Frente 0 — PRs abiertas ahora mismo (verificado con `gh pr list` + `git merge-tree`)

4 PRs open. 2 listas para mergear ya, 2 con conflictos reales sin resolver
desde hace más de una semana — y una investigación sin ni siquiera PR abierta.

| PR | Rama | Estado real | Acción |
|----|------|-------------|--------|
| #375 | `docs/dup-region-2-stale-status` | ✅ CI verde (lint+pytest), **0 conflictos** con `develop` | Mergear directo — solo corrige backlog desactualizado |
| #373 | `feature/android-drive-2-signin` | ✅ CI verde (lint+pytest+claude-review), **0 conflictos** | Mergear directo — Google Sign-In (Fase 2 del roadmap 28), sin dependencia de las otras 2 |
| #339 | `feature/inbox-ux-summary-metadata` (roadmap 26) | ⚠️ Sin CI ejecutado, **20 conflictos** con `develop` (`git merge-tree`) | Rebase sobre `develop` antes de nada — ver Frente 1 |
| #338 | `feature/saves-ux-history-context` (roadmap 25) | ⚠️ Sin CI ejecutado, **17 conflictos** con `develop` (`git merge-tree`) | Rebase sobre `develop` antes de nada — ver Frente 1, va primero (Pilar 3) |

Además: rama `docs/native-save-sync-1-dusklight-ruben` (push hecho a origin,
commit `b9237c6`, investigación NATIVE-SAVE-SYNC-1 "sin datos que recuperar"
en la máquina Ruben) **nunca llegó a abrir PR**. Cierre trivial: abrir PR,
mergear.

---

## Frente 1 — Rescatar #338 y #339 (Pilar 3 + Pilar 2, máxima prioridad real)

Estas dos ramas llevan **abiertas desde el 22-25/09**, con trabajo completo,
testeado (1437/1452 tests en verde en su momento) y documentado — no son
prototipos, son features cerradas del roadmap 25 (`SAVES-HISTORY-1`,
`SAVES-CONFLICT-CTX-1`, `SYNC-CONFLICT-MANUAL-1`) y 26
(`INBOX-SESSION-SUMMARY-1`, `INBOX-METADATA-INLINE-1`). Se quedaron
bloqueadas simplemente porque nadie volvió a por ellas mientras `develop`
seguía avanzando (28 commits, PRs #363-#380, todo el trabajo de dedup real
del Día71 incluido) — de ahí los conflictos.

**#338 depende de nada, #339 está apilada sobre #338** (su propio PR body lo
dice: "el diff mostrado aquí incluirá el de #338 hasta que se mergee
primero").

1. `git fetch && git checkout feature/saves-ux-history-context && git rebase origin/develop` — resolver los 17 conflictos (probablemente en `sync/conflict_resolver.py`, `sync/save_syncer.py`, `web/handlers/sync_cloud.py`, `web/static/js/tabs/sync.js` — ninguno de esos ficheros lo tocó el Día71, así que los conflictos vienen de que `develop` avanzó alrededor, no de choque directo de lógica; confirmar igual línea a línea).
2. Suite completa + ruff en verde tras el rebase, push, esperar CI real (ahora mismo "no checks reported" porque el workflow nunca corrió sobre estos commits).
3. Mergear #338.
4. Rebase `feature/inbox-ux-summary-metadata` sobre el nuevo `develop` (ya con #338 dentro) — los 20 conflictos deberían reducirse al quedar resuelta la base compartida.
5. Mergear #339.
6. Los roadmaps `25-saves-ux-history-context.md` y `26-inbox-ux-summary-metadata.md` solo existen dentro de estas ramas (no están en `.claude/roadmaps/` de `develop` todavía) — al mergear, archivarlos según la convención del INDEX (sin tareas pendientes en el backlog → `archivo/`).

**Por qué primero**: `SYNC-CONFLICT-MANUAL-1`/`SAVES-CONFLICT-CTX-1` tocan
directamente el sync de saves (Pilar 3, "cualquier bug aquí es prioridad
absoluta" — CLAUDE.md). Cuanto más tiempo pasa sin mergear, más conflictos
acumula contra un `develop` que no para de moverse.

---

## Frente 2 — Pendiente real dejado por Día71 (dedup Anbernic)

Textual desde el cierre de `Tareas/diario/Día71.md` — nada de esto se ha
tocado desde entonces:

1. **83 grupos `crossfmt`-only de PSX sin verificar** (~4,5 GB) — la función
   ya existe (`verify_group_by_disc_hash`, PR #379), solo falta repetir la
   pasada con el código integrado (la pasada real se hizo con el script
   previo) y decidir a mano los `.img`/`.mdf` que quedan en
   `unverifiable_paths`.
2. **La instancia real del servidor (puerto 7777) sigue sin reiniciar** desde
   antes de los PRs #376-#379 — el botón de verificación por hash no
   aparece todavía en el navegador real. Reiniciar y probar una vez contra
   la biblioteca real (~11.500 ROMs, carga puede tardar).
3. **`ANDROID-DUP-1` resto** — volcados legacy con nombre de serial, carpetas
   Title Case/slug paralelas en la Anbernic (fuera de PSX/GBA/NES), sin
   tocar.
4. **Game Boy Color sin aplicar** — 1268 grupos, 1,95 GB, el segundo bloque
   más grande sin tocar tras PSX (medido durante la investigación del
   desempate, mismo patrón ya probado y verificado hoy en NES/Game Gear).
   PlayStation, Sega Mega Drive, Game Boy y SNES también quedaron solo
   medidos, no aplicados.
5. **Filas fantasma en `library_android.db`** (los 2 discos españoles de
   Metal Gear Solid ya no existen en el dispositivo pero siguen en la BD) —
   indica que hace falta un rescan ADB completo en algún momento; sin
   investigar la causa raíz todavía.

---

## Frente 3 — Arrastrado de Día70, sin retomar en ningún momento

6. **Filtro verde persistente en *Warrior Within* (ARMSX2)** —
   `ANDROID-APP-PRIVATE-STORAGE-1e` en el backlog, 🔴 pendiente. 6 hipótesis
   de configuración agotadas sin efecto; siguiente paso ya decidido: arrancar
   el juego desde cero con Fast Boot (sin cargar ningún savestate) en zona
   nueva, para confirmar si la causa es un savestate/estado GS corrupto.
   Requiere la RG556 física.
7. **`JUEGOS-FIX-4` parte 2** — el fix de `COALESCE` en el orden ya está
   mergeado (parte 1, ✅). Queda un `DELETE ... WHERE source_path LIKE
   '%$RECYCLE.BIN%'` sobre `library_pc.db`, pero **en la máquina "rammu"**
   (esta máquina, "Ruben", ya confirmó 0 filas equivalentes) — no accionable
   desde aquí, anotar para la próxima sesión en esa máquina.

---

## Frente 4 — Bloqueados (no accionables sin el usuario / hardware externo)

- **`ANDROID-SYNC-CRITICAL-1`** — causa raíz 1 arreglada, causa raíz 2
  documentada sin arreglar (scope de Dropbox App Console, requiere acción
  del usuario en la consola de Dropbox).
- **RetroAchievements con API key real** — bloqueado igual desde hace
  varias sesiones.
- **`ANDROID-DRIVE-1` Fase 0** — prerrequisito manual (proyecto en Google
  Cloud Console + `GDRIVE_CLIENT_ID` real) antes de poder validar #373 en
  hardware de extremo a extremo.

---

## Orden recomendado para la próxima sesión

1. Mergear #375 y #373 (5 min, cero riesgo).
2. Abrir PR para `docs/native-save-sync-1-dusklight-ruben` y mergear.
3. Rescatar #338 (rebase + resolver conflictos) — Frente 1, punto más
   valioso pendiente porque toca Pilar 3 directamente.
4. Rescatar #339 sobre el `develop` ya con #338 dentro.
5. Reiniciar la instancia real (puerto 7777) y repetir la verificación de
   los 83 grupos `crossfmt` de PSX (Frente 2.1/2.2) — ya con el hash-check
   de #379 visible en el navegador real.
6. Si queda tiempo/energía: GBC dedup (Frente 2.4) o retomar ARMSX2
   (Frente 3.6) si hay acceso a la RG556 esa sesión.
