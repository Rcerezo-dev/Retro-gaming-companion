# Roadmap 17 — `feature/inbox-pending-features`

**Rama:** `feature/inbox-pending-features` (o una rama por sub-tarea, ver nota de alcance — son 3 features independientes, no una unidad de cambio única)
**Base:** `develop`
**Prioridad:** 🟠 P2 — Pilar 2 (Inbox, día a día) es el segundo pilar en prioridad real del proyecto
**Esfuerzo estimado:** L (`INBOX-ANBERNIC-1` M, `INBOX-ATOMIC-1` S, `INBOX-RA-HASH-GAP` L — feature nueva de hashing de discos)
**Riesgo:** Bajo-medio — ninguna toca el camino crítico de pérdida de saves (Pilar 3), pero `INBOX-ATOMIC-1` sí toca la escritura de BD del Inbox

---

## Origen

Tres tareas del epic Pilar 2 (`Tareas/backlog.md`, → #203) sin implementar,
sin relación de dependencia directa entre ellas más allá de compartir
módulo (`web/inbox_pipeline.py`) — agrupadas aquí por afinidad de área, no
porque deban entrar en la misma rama.

### `INBOX-ANBERNIC-1` — checkbox "enviar a la Anbernic" (2026-09-12)

Petición explícita del usuario: el Inbox hoy solo organiza en el PC; llevar
un juego recién organizado a la consola exige pasar aparte por Juegos +
Cable Sync. Decisión ya confirmada: **no automático** — checkbox opt-in por
corrida, no un push silencioso de todo lo que se organiza. 🔴 sin diseñar en
detalle.

### `INBOX-ATOMIC-1` — mover archivo + actualizar BD no es atómico

Hallazgo del roadmap `08-fix-error-handling.md` (revisión de bloques
`except Exception`, 2026-09-13). `_organize_matched_games`
(`web/inbox_pipeline.py`): si `shutil.move()` tiene éxito pero el
`UPDATE`/`cascade_delete` que sigue falla, el archivo físico ya está en el
destino pero la fila de `games` sigue apuntando al `source_path` viejo dentro
del Inbox, que ya no existe. Viola "toda operación sobre archivos se
registra en SQLite" (`CLAUDE.md`) de forma silenciosa — el usuario solo ve el
mensaje de excepción SQLite en `organize_errors`, nada le dice que el archivo
SÍ se movió.

### `INBOX-RA-HASH-GAP` — RA no compara discos comprimidos (2026-08-30)

Hallazgo derivado de `INBOX-ORPHAN-4`. `games.md5`
(`hashing/hash_calculator.py:41`) es un hash de archivo completo, pero el
hash que usa RetroAchievements para GameCube/Wii (y cualquier formato de
disco comprimido: RVZ, CHD) se calcula sobre datos específicos extraídos del
disco descomprimido (boot.bin/apploader/dol vía `rc_hash`), no sobre el
contenedor comprimido. Consecuencia real: `ra_duplicates_service.py`
(`get_ra_achievements`, `filter_duplicate_winners`) siempre devuelve -1 (sin
RA) para cualquier `.rvz`/`.chd` de disco, aunque el juego sí tenga logros en
RA — la comparación por RA solo funciona hoy para ROMs de cartucho sin
comprimir. Implementar el hash real de RA para discos requeriría parsear el
filesystem GameCube/Wii (o el `.chd`) para extraer las regiones exactas que
hashea `rc_hash` — **feature nueva, no un fix puntual**.

---

## Objetivo

1. `INBOX-ANBERNIC-1`: checkbox funcional en la UI del Inbox.
2. `INBOX-ATOMIC-1`: hacer el paso "mover + actualizar BD" atómico o, si no
   es posible con SQLite en este punto, al menos detectable/recuperable.
3. `INBOX-RA-HASH-GAP`: implementar el hash real de RA para discos
   GameCube/Wii comprimidos (alcance grande, puede dividirse en su propia
   sub-rama).

---

## Pasos

### `INBOX-ANBERNIC-1`

#### Paso 1 — Diseño (bloqueante)

Definir si el checkbox es global para la corrida completa o por archivo
individual — probablemente global, como los demás checkboxes del wizard del
Inbox (confirmar con el usuario antes de implementar). Definir el
comportamiento si no hay dispositivo ADB conectado: avisar y dejar el
archivo solo organizado en el PC sin bloquear el resto del job (no debe
fallar el Inbox completo por falta de cable).

#### Paso 2 — Implementación

Reutilizar la infraestructura ya existente (`direction="send_selected"` en
`_do_cable_sync`, `web/handlers/sync_cable.py`, ya usada por
`ANBERNIC-PICK-8`) sobre el `source_path` recién movido — no reimplementar
el push por ADB desde cero. Checkbox nuevo en `web/static/partials/
tab-inbox.html` + wiring en `tabs/inbox.js` + parámetro nuevo en el endpoint
del Inbox (`web/inbox_pipeline.py`) que, si está activo, llama a la lógica
de envío al terminar `organize` sobre cada archivo (o al final de la corrida,
según lo decidido en el Paso 1).

#### Paso 3 — Tests

Checkbox activo + dispositivo conectado (mock) → el archivo organizado se
envía. Checkbox activo + sin dispositivo → aviso, resto del job sigue sin
bloquearse.

### `INBOX-ATOMIC-1`

#### Paso 4 — Hacer atómica la escritura de BD tras el move

`_organize_matched_games` (`web/inbox_pipeline.py`): el `try`/`except`
actual solo captura la excepción y la añade a `organize_errors`, sin
distinguir "el move falló" (nada cambió) de "el move tuvo éxito pero la BD
falló" (archivo movido, BD desincronizada). Opciones a evaluar: (a) mover el
archivo DESPUÉS de que el `UPDATE`/`cascade_delete` haya tenido éxito en vez
de antes (invierte el orden — si la BD falla, el archivo nunca se movió,
estado consistente); (b) si el move debe ir primero por alguna razón técnica,
capturar el fallo de BD por separado y dejar un mensaje explícito
("archivo movido a X pero BD no actualizada, ejecutar `rommgr scan` para
reparar") en vez del mensaje de excepción SQLite crudo. (a) es más simple y
más seguro — preferir esa opción salvo que haya una razón real para el orden
actual.

#### Paso 5 — Tests

Mock de `UPDATE`/`cascade_delete` que falla tras el move (o, si se invierte
el orden, mock del move que falla tras la BD) → confirmar que el estado
final es consistente (archivo y BD de acuerdo) en cualquiera de los dos
caminos de fallo.

### `INBOX-RA-HASH-GAP`

#### Paso 6 — Investigación del algoritmo real de `rc_hash` para discos

Antes de escribir código: documentar exactamente qué regiones del disco
GameCube/Wii hashea `rc_hash` (boot.bin, apploader, dol — offsets y tamaños
exactos) contra la especificación real de RetroAchievements, no una
suposición. Esto es una feature nueva de tamaño considerable — candidata a
su propio roadmap más detallado una vez investigado, este paso solo confirma
el alcance real antes de comprometerse a la estimación L.

#### Paso 7 — Implementación (alcance a confirmar tras el Paso 6)

`hashing/hash_calculator.py` (nueva función de hash específica para discos) +
`services/ra_duplicates_service.py::get_ra_achievements` (usarla en vez del
MD5 de archivo completo cuando la extensión es `.rvz`/`.chd`/`.iso` de
GameCube/Wii). Mismo patrón que `detect_psx_boot_serial()`/`_extract_chd()`
ya usan para PSX — parsear el contenedor sin necesidad de descomprimirlo
completo a disco.

#### Paso 8 — Tests y verificación

Contra al menos un `.rvz`/`.chd` real de la biblioteca con logros RA
conocidos — confirmar que el hash calculado coincide con la entrada real de
RA (mismo patrón de verificación que `RA-HASH-SUBDIR-1` usó para PSX).

```bash
python -m pytest tests/ -q
ruff check src/rom_manager/web/inbox_pipeline.py src/rom_manager/hashing/ src/rom_manager/services/ra_duplicates_service.py
```

---

## Fuera de alcance

- Cualquier UI nueva más allá del checkbox de `INBOX-ANBERNIC-1` (sin panel
  de progreso separado, reutiliza el mismo panel de progreso del Inbox ya
  existente).
- Extender `INBOX-RA-HASH-GAP` a otras plataformas de disco más allá de
  GameCube/Wii en esta rama — si el algoritmo resulta reutilizable para
  PS2/PSP, eso es una extensión aparte una vez validado el caso base.

---

## Checklist

- [ ] `INBOX-ANBERNIC-1` Paso 1 — diseño confirmado (global vs. por archivo)
- [ ] `INBOX-ANBERNIC-1` Paso 2 — checkbox + wiring implementados
- [ ] `INBOX-ANBERNIC-1` Paso 3 — tests
- [x] `INBOX-ATOMIC-1` Paso 4 — orden corregido (2026-09-15, rama `feature/inbox-atomic-1`): BD primero, move al final, ambos dentro del mismo `batch()` — una excepción en cualquier punto revierte la BD, el move nunca se intenta si la BD falla primero
- [x] `INBOX-ATOMIC-1` Paso 5 — 2 tests nuevos en `test_inbox_pipeline_organize.py`, 1332 tests totales, ruff+format limpios
- [x] `INBOX-RA-HASH-GAP` Paso 6 — algoritmo `rc_hash` investigado (fuente real de rcheevos descargada y leída verbatim, no resumida) y documentado en `ra_hash_gamecube_wii.py`
- [x] `INBOX-RA-HASH-GAP` Paso 7 — implementación: GameCube+Wii en `ra_hash_gamecube_wii.py`, integrado en `ra_checker.py` y `ra_duplicates_service.py::get_ra_achievements_for_path` vía `ra_disc_hash_cache.py`. Alcance acotado a `.iso`/`.gcm` crudos (15/20 juegos reales de `gamecube/`) — `.rvz` (5/20) fuera de alcance, sin herramienta de descompresión disponible
- [x] `INBOX-RA-HASH-GAP` Paso 8 — 9 tests nuevos + verificación real: 2 `.iso` de la biblioteca (Wind Waker, Metroid Prime 2) hashean exacto al MD5 cacheado en `ra_cache/ra_hashes_16.json`. Wii implementado fiel a la fuente pero sin verificar contra datos reales (0 discos Wii comerciales en esta biblioteca)
- [ ] Commits en rama(s), PR(s) a `develop` — `INBOX-ATOMIC-1` ya mergeado; `INBOX-RA-HASH-GAP` commiteado en `feature/inbox-ra-hash-gap`, pendiente de mergear; `INBOX-ANBERNIC-1` sigue sin empezar (bloqueada en su propio Paso 1 de diseño)
