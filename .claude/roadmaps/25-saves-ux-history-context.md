# Roadmap 25 — `feature/saves-ux-history-context`

**Rama:** `feature/saves-ux-history-context`
**Base:** `develop`
**Prioridad:** 🟠 P2 — Pilar 3 (sync de saves, "valor diferencial real" del proyecto); no es un bug pero reduce directamente el "miedo a sobrescribir" que CLAUDE.md marca como el riesgo central de este pilar
**Esfuerzo estimado:** L (~9-12 h — tres piezas: historial+restauración, contexto en conflictos, y revisión manual de conflictos)
**Riesgo:** Medio — toca el camino de backup/restore de saves; cualquier regresión aquí es prioridad absoluta según CLAUDE.md (pérdida de progreso)

---

## Origen

`SAVES-HISTORY-1`, `SAVES-CONFLICT-CTX-1`, `SYNC-CONFLICT-MANUAL-1`
(`Tareas/backlog.md`, sección Pilar 3 → #204, idea usuario 2026-09-22, la
tercera añadida el mismo día tras revisar el código real). Tres mejoras de
UX sobre el mecanismo de sync ya existente, ninguna cambia la lógica de
detección de conflictos en sí — solo cómo se resuelven y se ven:

- **`SAVES-HISTORY-1`**: **replanteada tras investigar (Paso 1, 2026-09-22)**
  — la premisa original era incorrecta. Ya existe un sistema de backup
  versionado completo con UI funcionando: `rom_manager/backup/save_backup.py`
  (`<data_dir>/saves-backup/<plataforma>/<juego>/<timestamp>.<ext>`, poda
  `keep_n`), usado por Cloud Sync (`save_syncer.py`), Cable Sync manual
  (`sync_cable.py`) y el renombrado de ROMs (`file_renamer.py`) — con
  timeline + botón "Restaurar" ya en la ficha de juego
  (`GET /api/save-backups`, `POST /api/restore-backup`,
  `games.js:882,1090-1113`). El gap real: el daemon de auto-sync por SD
  (`cable_sync_daemon.py:591-592`, `CABLE-UX-9a`) usa un segundo sistema
  aislado, `.rommgr/cable_sync_backups/<fecha>/`, invisible en esa misma UI.
- **`SAVES-CONFLICT-CTX-1`**: al resolver un conflicto de sync hoy solo se
  ve el timestamp de cada lado — no hay señal de cuál partida tiene más
  progreso real.
- **`SYNC-CONFLICT-MANUAL-1`**: verificado contra el código real
  (`sync/conflict_resolver.py`, `sync/save_syncer.py:286-377`) — un
  conflicto (ambos lados cambiaron desde el último sync) se auto-resuelve
  siempre por `config.sync.conflict_policy` (global: `newest`/`keep_pc`/
  `keep_android`), nunca archivo por archivo. La vista de plan en dry-run ya
  existente (`sync.js` `_renderSyncDecisions`, `CLOUD-UX-12`) destaca los
  conflictos con &#x26A0; pero es de solo lectura — no hay forma de decidir
  "este archivo PC, este otro consola" antes de sincronizar. Solo aplica a
  Cloud Sync: Cable Sync (`sync_cable.py`) no tiene detección de conflictos
  hoy, ni siquiera automática (fuera de alcance de esta rama, ver "Fuera de
  alcance").

---

## Objetivo

1. ~~Timeline de versiones de saves por juego, con restauración desde la
   UI~~ — **ya existe** (ver Origen). Objetivo real: unificar el backup del
   daemon SD auto-sync en el mismo sistema para que también aparezca ahí.
2. Contexto adicional (playtime, tamaño) junto al timestamp al resolver un
   conflicto de sync.
3. Revisión manual de conflictos antes de sincronizar: por archivo, elegir
   PC / Consola / omitir, en vez de que la política global decida siempre
   por todos.

---

## Pasos

### Paso 1 — ✅ Investigado (2026-09-22): inventario de backups existentes

Confirmado contra el código real, no asumido. Dos sistemas:

1. `rom_manager/backup/save_backup.py` — versionado por juego, con
   `list_backups()`/`restore_backup()`/`backup_save()` (poda `keep_n`). Ya
   integrado en Cloud Sync, Cable Sync manual y renombrado de ROMs. Ya tiene
   endpoints (`GET /api/save-backups`, `POST /api/restore-backup`,
   `web/handlers/games.py:361-399,746-769`) y UI completa en la ficha de
   juego (`games.js:877-885,1090-1113`).
2. `.rommgr/cable_sync_backups/<fecha>/` — solo el daemon SD auto-sync
   (`cable_sync_daemon.py:591-592`). Sin listado, sin UI, sin restauración
   — un backup ahí solo es recuperable a mano desde el sistema de archivos.

### Paso 2 — ✅ Hecho (2026-09-22): migrar el daemon SD auto-sync al sistema unificado

`cable_sync_daemon.py:_run_sd_auto_sync` — reemplazada la carpeta ad-hoc
`.rommgr/cable_sync_backups/<fecha>/` (`shutil.copy2` manual con
`side`/`rel`) por `backup_save(item.dst, _bk_root)`, exactamente el mismo
patrón que ya usa `sync_cable.py:398,623` para el cable sync manual
(`_bk_root = config.data_dir if config.backup.saves_enabled else None`). No
hizo falta guard adicional para ROMs — `_wanted()` (línea 585-586) ya
filtra el plan de copia a solo extensiones de save antes de llegar al loop.

Bug de test detectado y corregido de paso: `_make_config()` en
`tests/test_cable_sync_daemon.py` pisaba `cfg.project_root` pero no
`cfg.data_dir` — con el código viejo daba igual (usaba `project_root`
directamente), pero con `backup_save(item.dst, config.data_dir)` los tests
habrían escrito backups en el `.rommgr` real del repo en vez de `tmp_path`.
Corregido fijando también `cfg.data_dir = tmp_path / ".rommgr"`.
`test_overwrite_backs_up_destination_first` actualizado a la ruta nueva
(`<data_dir>/saves-backup/gba/mario/<timestamp>.sav`). Suite completa:
1430 pass (3 fallos ambientales preexistentes, ADB conectado), ruff+format
limpios en ambos ficheros.

### Paso 3 — ✅ Resuelto (2026-09-22): no hay nada que migrar

Verificado contra el sistema de archivos real (no asumido): `.rommgr/
cable_sync_backups/` **no existe** en este PC — `find` no encuentra ni un
solo fichero ni fecha. El daemon SD auto-sync nunca llegó a disparar la
rama `item.dst.exists()` en la práctica (la mayoría de syncs de este
proyecto son archivos nuevos, no overwrites), así que la carpeta ad-hoc de
`CABLE-UX-9a` quedó siempre vacía. Nada que reorganizar — el usuario
confirmó seguir adelante ("sí, por favor") pero la migración resultó
innecesaria una vez verificado el estado real. De paso, confirmado que el
sistema unificado (`saves-backup/`) ya tiene 123 backups reales de otras
vías (Cloud Sync, Cable Sync manual, renombrados), visibles ya en la UI —
el Paso 2 no introdujo una tabla rasa, se integra en un sistema ya en uso.

### Paso 4 — ✅ Hecho (2026-09-22): `SAVES-CONFLICT-CTX-1`, contexto en conflictos

Solo aplica a Cloud Sync (`sync_cable.py` no detecta conflictos, ver "Fuera
de alcance"). Premisa también corregida en la práctica: la UI no mostraba
ningún timestamp para conflictos hasta este paso — no había "el timestamp
que ya se muestra hoy", el payload solo mandaba `{action, relative}`.

- `sync/conflict_resolver.py`: `SyncDecision` gana `local_size`/`remote_size`
  (opcionales, `None` por defecto).
- `sync/save_syncer.py`: los rellena tras `decide()` con `local.size`/
  `remote.size` (ya estaban disponibles en el loop, sin lookup nuevo).
- `web/handlers/sync_cloud.py`: nuevo helper `_decision_payload(d, repository)`
  — para `action == "conflict"` añade `local_mtime`/`remote_mtime` (ISO),
  `local_size`/`remote_size`, y playtime best-effort (`playtime_minutes_pc`/
  `_android`) buscando en `games` un juego cuyo `source_path` comparta stem
  con la ruta del save (mismo supuesto que ya usa `GET /api/save-backups` y
  `set_playtime_minutes`, `JUEGOS-UX-5/6`) — sin match o con error, esas
  claves simplemente no aparecen, nunca rompe el sync. Usado en los dos
  puntos donde se construye `decisions` (fuentes explícitas y el bloque D2
  de remotes implícitos).
- `web/static/js/tabs/sync.js`: `_renderSyncDecisions` pinta una línea de
  contexto bajo cada fila de conflicto (mtime+tamaño de cada lado, y
  playtime si hay datos) — sin tocar la lógica de decisión, solo más
  información visible.

### Paso 5 — ✅ Ya satisfecho por el Paso 4 (2026-09-22)

`_decision_payload()` (Paso 4) ya expone `local_mtime`/`remote_mtime`/
`local_size`/`remote_size`/playtime para `action == "conflict"` — el Paso 4
terminó cubriendo exactamente lo que este paso pedía. Sin trabajo adicional.

### Paso 6 — ✅ Hecho (2026-09-22): `sync_saves`/`save_syncer.py` acepta overrides por archivo

`sync_saves()` gana el parámetro `conflict_overrides: dict[str, str] | None`
(`relative → "keep_local"|"keep_remote"|"skip"`). Dentro de la rama
`decision.action == "conflict"`: un override `"skip"` sale por `continue`
antes de tocar backup/transport — no se sobrescribe nada, se registra
`log_sync_event(..., result="skipped")` (no cuenta como watermark `ok`, así
que el conflicto se re-evalúa en el próximo sync si sigue sin resolver) y
`result.conflicts += 1`. Un override `keep_local`/`keep_remote` se comprueba
**antes** que `conflict_policy` en la cadena de decisión del ganador — gana
solo para ese archivo, el resto de conflictos sin entrada en el dict siguen
la política global sin cambios. Mismo backup-antes-de-sobrescribir que ya
hacía el código (`sync_saves`, línea ~296) para los casos no-skip.

### Paso 7 — ✅ Hecho (2026-09-22): UI de revisión antes de sincronizar

`_renderSyncDecisions` (`sync.js`): cada fila de conflicto gana un
`<select>` (Auto / Mantener PC / Mantener consola / Omitir) — **solo
quando `result.dry_run` es true** (el plan, no el resultado ya aplicado).
Nueva `_collectConflictOverrides()` lee todos los `.conflict-override-select`
tocados al pulsar "Sincronizar" (`doSync(false)`) y los manda como
`conflict_overrides` en el body de `/api/sync`; sin overrides, el body es
idéntico al de antes (no rompe el flujo para quien no revisa nada). Backend:
`_do_sync()` los lee de `data.get("conflict_overrides")` y los reenvía a
`run_cloud_sync_job()` → las dos llamadas a `sync_saves()` (fuentes
explícitas y remotes implícitos D2). El watcher de emuladores
(`web/daemons.py`) nunca los pasa — sigue resolviendo solo por política,
como antes.

### Paso 8 — ✅ Tests (2026-09-22)

- `tests/test_cable_sync_daemon.py`: backup del daemon SD vía `backup_save()`
  en el layout unificado (Paso 2).
- `tests/test_sync_cloud_conflict_ctx.py`: payload de conflicto con/sin
  playtime, sin romper el flujo sin match (Paso 4/5).
- `tests/test_save_syncer.py`: override gana sobre política global;
  `"skip"` no toca ningún lado (ni transport ni backup); un conflicto sin
  entrada en el dict sigue la política global sin cambios (Paso 6).

### Paso 9 — ✅ Verificación (2026-09-22)

```bash
python -m pytest tests/ -q     # 1437 pass, 3 fallos ambientales preexistentes (ADB conectado)
ruff check src/rom_manager/sync/ src/rom_manager/web/handlers/sync_cloud.py   # limpio
ruff format --check ...                                                       # limpio
```

---

## Fuera de alcance

- Screenshot del savestate en el conflicto (mencionado como idea original,
  depende de soporte por core — investigar viabilidad en una sesión aparte
  si se pide explícitamente).
- Purga automática de backups antiguos — no hay política de retención
  definida; no inventar una sin pedirla.
- Detección de conflictos en Cable Sync (`sync_cable.py`) — hoy no existe
  (solo mtime "newest"/skip-existing); añadirla es un cambio de mecanismo
  más grande, candidato a su propia rama si se pide.

---

## Checklist

- [x] Paso 1 — inventario de fuentes de backup confirmado contra el código real (2026-09-22)
- [x] Paso 2 — migrar el daemon SD auto-sync a `backup_save()` (2026-09-22)
- [x] Paso 3 — verificado: no había backups históricos que migrar (2026-09-22)
- [x] Paso 4 — contexto (playtime/tamaño) en conflictos (2026-09-22)
- [x] Paso 5 — payload de conflicto expone mtimes/contexto (ya cubierto por el Paso 4)
- [x] Paso 6 — `conflict_overrides` por archivo en `save_syncer.py` (2026-09-22)
- [x] Paso 7 — UI de revisión manual antes de sincronizar (2026-09-22)
- [x] Paso 8 — tests nuevos (2026-09-22)
- [x] Paso 9 — suite completa + ruff limpios (2026-09-22)
- [ ] Commit en rama, PR a `develop` — pendiente, requiere confirmación explícita del usuario
