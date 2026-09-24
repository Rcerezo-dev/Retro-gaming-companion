# Roadmap 15 — `fix/psx-cue-multitrack-integrity`

**Rama:** `fix/psx-cue-multitrack-integrity`
**Base:** `develop`
**Prioridad:** 🔴 P1 — riesgo real de pérdida/corrupción de datos de juego (discos PSX multi-pista que no cargan en ningún emulador)
**Esfuerzo estimado:** M (~4-6 h, sobre todo verificación manual pista a pista)
**Riesgo:** Alto si se hace mal — desordenar pistas de un `.cue` multi-track puede dejar el disco peor que como está hoy (sin cargar, en vez de con solo la parte de datos corrupta). Bajo si se sigue el patrón ya usado en `PSX-CUE-DESYNC-1a` (backup + verificación con `parse_bins_from_cue()` + rollback automático)

---

## Origen — dos hallazgos relacionados, dos máquinas distintas

### 1. `PSX-CUE-DESYNC-1b` — máquina "Ruben" (`F:\Juegos Retro`)

Continuación de `PSX-CUE-DESYNC-1` (hallazgo CRÍTICO 2026-09-12): un
`apply` de renombrado del 2026-03-21 rompió la referencia interna `FILE
"..."` de 32 de los 99 `.cue` de la biblioteca activa sin reescribirla,
dejando esos discos incapaces de cargar en ningún emulador real. La causa
raíz de código ya está arreglada (`PSX-CUE-DESYNC-1c`, ✅ 2026-09-12 —
`_update_disc_sheet_references()` en `renamer/file_renamer.py` reescribe la
línea `FILE` como parte de la misma operación atómica de renombrado), y los
21 casos de un solo track ya están reparados (`PSX-CUE-DESYNC-1a`, ✅).

**Quedan 11 casos multi-track sin reparar**: Darkstalkers, Dino Crisis, Dino
Crisis 2, Gundam Battle Assault, Magical Tetris Challenge ×2, MediEvil 2,
Mortal Kombat 3, Street Fighter Alpha, Street Fighter Collection, Super Pang
Collection, Warhammer. Estos necesitan emparejar cada `TRACK` del `.cue` con
su `.bin` real **por número de pista**, no por nombre — el riesgo de
desordenar pistas si se hace mal es mayor que en el caso de un solo track ya
resuelto.

### 2. `PSX-STRUCTURE-4` — máquina "rammu" (`H:\ROMs`, `E:\Carpetas anbernic`)

**Nota de alcance**: esta parte usa las rutas de la máquina "rammu"/RG556
(activa en paralelo, confirmado por el usuario 2026-09-15), no la biblioteca
`F:\Juegos Retro` de la parte 1. Son dos tareas relacionadas por tocar el
mismo subsistema (`.cue`/multi-disco PSX) pero sobre datos físicamente
distintos — no se pueden ejecutar con el mismo backup/verificación.

Decisión ya confirmada 2026-09-02: subcarpeta por juego para `psx/` (y el
resto de `_DISC_SUBFOLDER_PLATFORMS` en `planner/operation_planner.py:19-22`
— saturn, dreamcast, wii), ya implementada como convención
(`move_disc_set_to_subfolder`, `renamer/file_renamer.py:211`). El bloqueo:
de los 456 casos PSX ambiguos originales, solo 167 (37%) resuelven región
correcta tras `CATALOG-MATCH-REGION-1`/`-2` — **quedan 289 (63%) sin
resolver**. Migrar `psx/` a subcarpeta-por-juego ahora usaría el título
ambiguo/incorrecto de esos 289 como nombre de carpeta destino.

**🟡 Decisión pendiente del usuario**: ejecutar la migración ya (aceptando
que 289 sets quedarán con nombre de carpeta potencialmente erróneo,
corregible después) vs. esperar a resolver más región primero
(`CATALOG-MATCH-REGION-2` ya aplicó lo "limpio" — 65/291 — dejando 226 sin
serial-match; no hay un plan concreto para bajar ese número más).

---

## Objetivo

1. Reparar los 11 sets multi-track de `PSX-CUE-DESYNC-1b` sin desordenar
   ninguna pista (máquina "Ruben").
2. Decidir y, si procede, ejecutar la migración a subcarpeta-por-juego de
   `PSX-STRUCTURE-4` (máquina "rammu").

---

## Pasos

### Paso 1 — Emparejar TRACK↔`.bin` por número, no por nombre (11 casos)

Para cada uno de los 11 sets: leer el `.cue` roto (línea `FILE "..." BINARY`
+ bloques `TRACK NN AUDIO`/`MODE1/2352`) y comparar contra los `.bin` reales
presentes en la carpeta. A diferencia del caso de un solo track
(`PSX-CUE-DESYNC-1a`, candidato único sin ambigüedad), aquí puede haber
varios `.bin` candidatos por pista — el criterio de emparejamiento correcto
es el **tamaño exacto** de cada `.bin` (una pista de audio/datos tiene un
tamaño determinista una vez extraída, no cambia entre re-nombrados) cruzado
con el orden numérico de pista. Reutilizar los parsers ya existentes
(`parse_bins_from_cue`, `converters/chd_converter.py`) para no reimplementar
el parseo del `.cue`.

### Paso 2 — Backup y verificación (mismo patrón que `PSX-CUE-DESYNC-1a`)

Backup del `.cue` original de cada uno antes de tocar nada (mismo directorio
`.rommgr/backup_cue_repair_<fecha>/` ya usado). Tras reescribir cada línea
`FILE`, verificar con `parse_bins_from_cue()` que el resultado es coherente
(todas las pistas referencian un `.bin` que existe, en el orden correcto) —
auto-rollback si la verificación falla, igual que en `PSX-CUE-DESYNC-1a` (no
hizo falta ningún rollback esa vez, pero el mecanismo debe estar activo aquí
también por el mayor riesgo).

### Paso 3 — Sanity check con `chdman`

Tras reparar cada `.cue`, una conversión real de prueba con `chdman.exe`
(dry-run o a un archivo temporal, sin sobrescribir nada) confirma que el set
es legible de principio a fin — mismo sanity check que ya se hizo con
"Chicken Run (China)" en `PSX-CUE-DESYNC-1a`.

### Paso 4 — Decisión y ejecución de `PSX-STRUCTURE-4` (máquina rammu)

Presentar al usuario la decisión pendiente (ejecutar ya con 63% de región sin
resolver, vs. esperar). Si se decide ejecutar: usar `move_disc_set_to_subfolder`
tal cual ya existe (no requiere código nuevo), backup implícito vía
`_descartados/` para cualquier colisión. Los 289 casos con región ambigua
quedarán en una subcarpeta con el título que tengan hoy en BD — documentar
cuáles son para poder corregir el nombre de carpeta más adelante si
`CATALOG-MATCH-REGION-2` mejora la resolución de región.

### Paso 5 — Verificación final

```bash
python -m pytest tests/ -q
```

Verificación manual (no automatizable): los 11 sets reparados deben cargar
en un emulador PSX real (RetroArch/DuckStation) antes de dar la tarea por
cerrada — mismo criterio que "PSX siempre por sets" de `CLAUDE.md`.

---

## Fuera de alcance

- Cualquier cambio de código nuevo — `PSX-CUE-DESYNC-1c` (la causa raíz) ya
  está arreglada; este roadmap es reparación de datos + una decisión de
  ejecución, no desarrollo.
- Resolver más región PSX de la que ya dejó `CATALOG-MATCH-REGION-2` — si
  hace falta bajar el 63% sin resolver de `PSX-STRUCTURE-4` antes de migrar,
  eso es una investigación aparte, no parte de este roadmap.

---

## Checklist

- [ ] Paso 1 — 11 sets multi-track emparejados por número de pista
- [ ] Paso 2 — backup + verificación automática por set
- [ ] Paso 3 — sanity check con `chdman` por set
- [ ] Paso 4 — decisión de `PSX-STRUCTURE-4` confirmada y, si procede, ejecutada
- [ ] Paso 5 — verificación manual en emulador real
- [ ] Commit en rama (si hubiera cambio de código; si es solo reparación de datos, documentar en el backlog sin PR) — pendiente, requiere confirmación explícita del usuario
