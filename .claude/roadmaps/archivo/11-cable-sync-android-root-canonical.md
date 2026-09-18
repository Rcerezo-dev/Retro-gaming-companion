# Roadmap 11 — `fix/cable-sync-android-root-canonical`

**Rama:** `fix/cable-sync-android-root-canonical`
**Base:** `develop`
**Prioridad:** 🔴 P1 — un Cable Sync ADB puede "tener éxito" (0 errores, tamaño exacto) y dejar el archivo invisible para el launcher del dispositivo
**Esfuerzo estimado:** ~2-3 h
**Riesgo:** Bajo-medio — toca la ruta de escritura de Cable Sync ADB, pero es aditivo (traduce nombres, no cambia qué se copia) + un aviso, no bloquea nada

---

## Origen

Hallazgo real 2026-09-13 (`CABLE-ROOT-1` en `Tareas/backlog.md`, epic Pilar 3
`#204`): 4 juegos enviados por ADB a la Anbernic (2 PS2 vía `adb push`
manual, 2 Dreamcast vía intento real de `/api/cable-sync` que abortó por
`ADB-TIMEOUT-1`) quedaron en `/storage/emulated/0/RetroArch/...`
(almacenamiento interno, el launcher del dispositivo — Daijishō — no lo
vigila) en vez de `/storage/521D-04EA/ROMs/...` (la SD real, con cientos de
ROMs y `mtime` reciente). Verificado con el dispositivo real conectado
(serial `RG556006101273`, mismo que ya aparece en `CABLE-ROM-FIX`).

Dos causas de código independientes, ambas confirmadas leyendo
`web/handlers/sync_cable.py` y `sync/cable_engine.py`:

1. **Nombre de carpeta espejado sin canonicalizar.** `_adb_copy_to_device`
   (`sync_cable.py:639-674`) construye el destino como
   `android_path.rstrip("/") + "/" + rel_posix`, donde `rel_posix` viene de
   `local_src.relative_to(pc_root).as_posix()` (4 call sites: líneas 781,
   932/938, 1134; el quinto, línea 830, es la rama `newest`/bidireccional y
   ya viene de un `android_path` real, no del PC — no aplica aquí). Si la
   carpeta del PC todavía tiene el nombre viejo estilo Android
   (`PlayStation 2`, `Game Boy Advance` — pendiente de renombrar físicamente,
   ver `MDFOLDER-FIX-2`/`MATCH-FIX-5`), ese mismo nombre no-canónico
   aterriza en el dispositivo, sin importar que el `android_path` (root) sea
   correcto. Mismo patrón de bug ya arreglado para el Inbox en el roadmap
   `05-consolidate-platform-dict.md` — aquí falta el equivalente para Cable
   Sync ADB. `sync/cable_engine.py:63` (modo sistema de archivos/SD montada)
   tiene el mismo problema, pero con menor prioridad porque ese modo no se
   usa en la máquina donde se detectó el bug (usa ADB) — se cubre igual en
   este roadmap por completitud.
2. **Ninguna validación de que el destino tiene sentido.** Nada compara
   "cuántos archivos ya hay bajo `android_path/<plataforma>`" contra lo
   que cabría esperar antes de escribir — un root apuntando por error al
   almacenamiento interno vacío no genera ninguna señal, el job termina con
   `errors=0` igual que un éxito real.

---

## Objetivo

1. Traducir el primer segmento de `rel_posix` (la carpeta de plataforma) a
   su slug canónico de Android antes de construir `android_dst`, reusando
   las tablas ya existentes (`PLATFORM_BY_FOLDER` +
   `_ES_PLATFORM_FOLDERS`) — mismo mecanismo que ya usa el Inbox desde el
   roadmap 05, no una tabla nueva.
2. Antes de un Cable Sync ADB real (`dry_run=False`, dirección
   `pc_to_anbernic`), avisar (no bloquear) si el destino de una plataforma
   está sospechosamente vacío comparado con lo que el PC va a enviar —
   visible en el mismo log de eventos que ya usa la UI (`details`/
   `cable_sync_ops.log`), sin frontend nuevo.

No tocar: la lógica de `skip_existing`/`skip_sha1_dups`
(`CABLE-ROM-FIX-1`, ya correcta), el guard de espacio libre
(`CABLE-ROM-FIX-2`, ya correcto), ni la resolución de duplicados por RA
(`CABLE-ROOT-1f` — diseño aparte, no entra en este roadmap).

---

## Pasos

### Paso 1 — Helper de canonicalización compartido

Nuevo archivo pequeño, `src/rom_manager/sync/android_paths.py` (evita que
`cable_engine.py`, que no depende de `web/`, tenga que importar de
`web/handlers/system.py` — ver riesgo de ciclo más abajo):

```python
"""Traduce una ruta relativa de PC a su equivalente canónico en Android."""

from __future__ import annotations

from rom_manager.detection.platform_detector import PLATFORM_BY_FOLDER


def canonical_rel_posix(rel_posix: str, es_platform_folders: dict[str, str]) -> str:
    """Traduce el primer segmento (carpeta de plataforma) a su slug canónico.

    Si el primer segmento no coincide con ningún alias/nombre conocido, se
    devuelve tal cual — no inventa una carpeta nueva para algo que no
    reconoce (p. ej. carpetas de sistema como ``BIOS/`` o ``saves/``).
    """
    parts = rel_posix.split("/", 1)
    if len(parts) < 2:
        return rel_posix
    folder, rest = parts
    canonical = PLATFORM_BY_FOLDER.get(folder.lower(), folder)
    slug = es_platform_folders.get(canonical, folder)
    return f"{slug}/{rest}"
```

Se pasa `es_platform_folders` como parámetro (no se importa `system.py`
directamente desde aquí) para que `sync/` siga sin depender de `web/` —
`cable_engine.py` ya declara explícitamente esa separación en su
docstring (línea 1-9).

### Paso 2 — Aplicar en `sync_cable.py` (modo ADB)

Import nuevo (junto a los existentes, línea ~9):

```python
from rom_manager.sync.android_paths import canonical_rel_posix
from rom_manager.web.handlers.system import _ES_PLATFORM_FOLDERS
```

En los 3 call sites que construyen `rel_posix` desde el lado PC (líneas
781, 932/938 y 1134 — comparten la misma variable local `rel_posix` justo
antes de `_adb_copy_to_device(...)`), envolver:

```python
# Antes:
rel_posix = rel.as_posix()
...
_adb_copy_to_device(src, rel_posix, "→ ADB")

# Después:
rel_posix = canonical_rel_posix(rel.as_posix(), _ES_PLATFORM_FOLDERS)
...
_adb_copy_to_device(src, rel_posix, "→ ADB")
```

Repetir el mismo cambio de una línea en los otros 2 call sites (932/938
comparten `rel_posix`, 1134 es independiente). No tocar la línea 830 (rama
`newest`, ya parte de un `android_path` real).

### Paso 3 — Aplicar en `cable_engine.py` (modo filesystem/SD montada)

`plan_direction()` (líneas 51-107): en la rama `pc_to_anbernic` (línea
60-64) y en la rama `newest` cuando gana el PC (línea 93-94, 102), el
destino se construye con `ab_root / src.relative_to(pc_root)`. Cambiar a:

```python
# pc_to_anbernic:
rel = src.relative_to(pc_root)
dst = ab_root / canonical_rel_posix(rel.as_posix(), es_platform_folders)
yield CopyPlanItem(src, dst, "-> Anbernic")
```

`plan_direction()` necesita un nuevo parámetro `es_platform_folders:
dict[str, str]` (con default `{}` para no romper callers existentes que
no lo pasen — en ese caso `canonical_rel_posix` devuelve la ruta sin
tocar, comportamiento actual preservado). Actualizar los 2 callers
conocidos de `plan_direction` para pasarlo (buscar con `grep -rn
"plan_direction("`).

### Paso 4 — Aviso de destino sospechosamente vacío

En `sync_cable.py`, justo antes de empezar la fase de copia real
(`dry_run=False`, dirección `pc_to_anbernic` — buscar el punto donde ya se
calcula `ab_adb_files`/`_pre_files` por plataforma, líneas ~699-700):

```python
# Por cada carpeta de plataforma en el lado PC con >= 20 archivos,
# si el equivalente canónico en ab_adb_files tiene 0 archivos, es más
# probable que android_path esté mal que que el usuario esté vaciando
# esa plataforma a propósito por primera vez — avisar, no bloquear.
_pc_platform_counts: dict[str, int] = {}
for f in cable_engine.iter_files(pc_root):
    if _wanted(f):
        top = f.relative_to(pc_root).as_posix().split("/", 1)[0]
        _pc_platform_counts[top] = _pc_platform_counts.get(top, 0) + 1

_ab_platform_counts: dict[str, int] = {}
for info in ab_adb_files:
    if _wanted_info(info):
        top = info.android_path.removeprefix(android_prefix).split("/", 1)[0]
        _ab_platform_counts[top] = _ab_platform_counts.get(top, 0) + 1

for pc_folder, pc_count in _pc_platform_counts.items():
    slug = canonical_rel_posix(f"{pc_folder}/x", _ES_PLATFORM_FOLDERS).split("/", 1)[0]
    if pc_count >= 20 and _ab_platform_counts.get(slug, 0) == 0:
        _log(
            "WARN",
            f"{pc_folder}/ ({pc_count} archivos en PC)",
            f"{android_path}/{slug}/ (0 archivos)",
            "destino vacío — revisa que android_path apunte a la biblioteca real del dispositivo",
        )
```

Ajustar nombres de variables reales tras leer el bloque completo
(`sync_cable.py:676-730`) — el pseudocódigo de arriba asume que
`ab_adb_files`, `_wanted`, `_wanted_info` y `android_prefix` ya existen en
ese scope (confirmado por los usos ya vistos en el archivo). `_log(...)`
ya existe y escribe tanto a `cable_sync_ops.log` como a `details` — no
hace falta tocar el frontend para que el aviso sea visible.

### Paso 5 — Tests

- `tests/test_sync_cable_*.py` (el archivo existente de exclusión de
  plataformas, `test_sync_cable_exclude_platforms.py`, es el patrón más
  cercano): caso con carpeta PC `PlayStation 2/` → confirmar que
  `android_dst` construido usa `ps2/`, no `PlayStation 2/`.
- Test para `canonical_rel_posix`: carpeta reconocida se traduce: carpeta
  desconocida (`BIOS/algo.bin`) se deja igual; ruta de un solo segmento
  (sin subcarpeta) se deja igual.
- Test para el aviso del Paso 4: PC con 25 archivos en una carpeta,
  dispositivo con 0 en su slug canónico → aparece un evento `WARN` en
  `details`/log; con 3 archivos en PC (bajo el umbral) no aparece aviso.
- `cable_engine.py`: extender `tests/test_cable_engine.py` (si existe;
  si no, crear) con un caso `pc_to_anbernic` donde `pc_root` tiene una
  carpeta con nombre no-canónico y `es_platform_folders` la traduce.

### Paso 6 — Verificación

```bash
grep -rn "relative_to(pc_root).as_posix()" src/rom_manager/web/handlers/sync_cable.py
# cada resultado debe estar envuelto en canonical_rel_posix() antes de _adb_copy_to_device

python -m pytest tests/ -q
ruff check src/rom_manager/sync/ src/rom_manager/web/handlers/sync_cable.py
ruff format --check src/rom_manager/sync/ src/rom_manager/web/handlers/sync_cable.py
```

No requiere hardware para validar (todo es lógica pura sobre paths), pero
si hay una Anbernic conectada al terminar, un dry-run real de
`pc_to_anbernic` sobre una carpeta con nombre viejo (si queda alguna sin
renombrar) es la confirmación definitiva de que el destino ya sale en
minúsculas/slug.

---

## Fuera de alcance (documentado aparte, no entra en esta rama)

- `CABLE-ROOT-1e` — medir si hay más títulos en la SD del dispositivo con
  etiqueta de región incorrecta (requiere hash real contra el dispositivo,
  no es un cambio de código).
- `CABLE-ROOT-1f` — usar logros de RA para decidir qué versión conservar
  al detectar candidatos a duplicado entre PC y Anbernic — es una decisión
  de diseño (qué umbral, qué hacer con empates) antes de escribir código.
- Renombrado físico de las carpetas del PC que aún tienen nombre viejo
  (`PlayStation 2`, `Game Boy Advance`, etc. — `MDFOLDER-FIX-2`/
  `MATCH-FIX-5`) — este roadmap hace que Cable Sync sea tolerante a que
  sigan así, no las renombra.

---

## Checklist

- [x] Paso 1 — `sync/android_paths.py` con `canonical_rel_posix()`
- [x] Paso 2 — 3 call sites de `sync_cable.py` (ADB) traducen antes de copiar
- [x] Paso 3 — `cable_engine.plan_direction()` acepta `es_platform_folders` y traduce en `pc_to_anbernic`/`newest` (2 callers en `sync_cable.py` filesystem mode actualizados; `cable_sync_daemon.py` SD-auto-sync de saves deliberadamente fuera de alcance, ver nota abajo)
- [x] Paso 4 — aviso de destino vacío antes de una corrida real `pc_to_anbernic` (ADB)
- [x] Paso 5 — tests nuevos, suite completa en verde (1323 tests)
- [x] Paso 6 — ruff + format limpios
- [ ] Commit en rama, PR a `develop` — **pendiente, requiere confirmación explícita del usuario**

**Nota de alcance no prevista originalmente**: `cable_sync_daemon.py:478` (SD-auto-sync
de *saves*, Pilar 3) es un 4º caller de `plan_direction()` no contemplado en el
Paso 3 original ("2 callers conocidos") — se dejó sin tocar a propósito por la
sensibilidad de ese código (pérdida de progreso de partidas es prioridad
absoluta según `CLAUDE.md`); el default `es_platform_folders={}` preserva su
comportamiento actual sin cambios. Decidir aparte si conviene extenderlo ahí.
