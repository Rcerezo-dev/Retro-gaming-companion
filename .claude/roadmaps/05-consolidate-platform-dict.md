# Roadmap 05 — `refactor/consolidate-platform-dict`

**Rama:** `refactor/consolidate-platform-dict`
**Base:** `refactor/consolidate-state`
**Prioridad:** 🟠 P2
**Esfuerzo estimado:** ~1 h
**Riesgo:** Bajo — consolidación de tablas estáticas, pero corrige un bug real de nombres de carpeta

---

## Estado actual

Hay **dos tablas independientes** que mapean "plataforma" → "carpeta", con propósitos casi idénticos:

| Tabla | Archivo | Claves | Usado por |
|-------|---------|--------|-----------|
| `_ES_PLATFORM_FOLDERS` | `web/handlers/system.py:11-72` | Nombres canónicos del detector (`"PlayStation"`, `"Sega Mega Drive"`, `"Nintendo 64"`, ...) | `organize.py` (`_do_organize_library`), `scraper.py` (export ES-DE) |
| `_STANDARD_PLATFORM_FOLDERS` | `web/handlers/system.py:74-88` | Tupla de slugs ES-DE estándar | `organize.py` (`_do_create_library_structure`) |
| `_PLATFORM_FOLDERS` | `web/inbox_pipeline.py:19-47` | Códigos cortos en minúscula (`"gba"`, `"ps1"`, `"genesis"`, `"mame"`, ...) | solo `_platform_folder_name()` (Step 6 del Inbox) |

`games.platform` en SQLite siempre contiene el **nombre canónico** que devuelve `detect_platform()` (p.ej. `"PlayStation"`, `"Sega Mega Drive"`, `"Nintendo 64"`) — son las claves de `_ES_PLATFORM_FOLDERS`, definidas en `detection/platforms.toml`.

---

## Bug encontrado

`_platform_folder_name()` (`inbox_pipeline.py:90-102`) hace `platform.lower()` y busca en `_PLATFORM_FOLDERS`, cuyas claves son códigos cortos (`"psx"`, `"n64"`, `"genesis"`...), **no** nombres canónicos en minúscula. Para la mayoría de plataformas no hay coincidencia (`"playstation"`, `"nintendo 64"`, `"sega mega drive"`, `"game boy advance"` no están como claves) y la función cae al `return platform` final, **devolviendo el nombre canónico sin normalizar**.

Resultado: el Step 6 del Inbox (`_run_inbox_pipeline`, línea ~492) crea carpetas como `PlayStation/`, `Nintendo 64/`, `Sega Mega Drive/`, `Game Boy Advance/` — con mayúsculas y espacios — mientras que "Organizar biblioteca" (`organize.py`, vía `_ES_PLATFORM_FOLDERS`) usa `psx/`, `n64/`, `megadrive/`, `gba/`. Un juego que entra por el Inbox y otro de la misma plataforma añadido manualmente terminan en **carpetas distintas** para ES-DE/RetroArch.

(Solo `"NES"` y `"SNES"` funcionan por coincidencia, porque `"nes".lower() == "nes"` está en ambas tablas.)

---

## Objetivo

Una sola tabla canónica (`_ES_PLATFORM_FOLDERS` en `system.py`, ya usada por `organize.py`/`scraper.py`) + reutilizar `PLATFORM_BY_FOLDER` (de `detection/platform_detector.py`, ya fuente de verdad para alias de carpeta como `"genesis"`, `"ps1"`, `"mame"`, `"lynx"`...) para normalizar **cualquier** identificador de plataforma (canónico o alias corto) antes de mapearlo a un slug ES-DE. Eliminar `_PLATFORM_FOLDERS` y `_platform_folder_name()`.

No tocar `_STANDARD_PLATFORM_FOLDERS` ni la lógica de `organize.py`/`scraper.py` — ya están correctos.

---

## Pasos

### Paso 1 — Completar `_ES_PLATFORM_FOLDERS` (system.py)

`"Neo Geo Pocket Color"` es la única plataforma que puede devolver `detect_platform()` (vía `platforms.toml [folders]`, claves `"neogeopocket"`/`"ngpc"`) y que falta en `_ES_PLATFORM_FOLDERS`. Añadir junto a las entradas de Neo Geo (línea ~41):

```python
"Neo Geo":              "neogeo",
"Neo Geo Pocket Color": "ngpc",
```

`tests/test_platform_detector.py::test_all_folder_platforms_have_es_mapping` ya trata `"Neo Geo Pocket Color"` como `unmapped_ok` — añadirla no rompe ese test (solo falla si falta Y no está en `unmapped_ok`).

### Paso 2 — `inbox_pipeline.py`: imports a nivel de módulo

Añadir en la cabecera (junto a los imports existentes, línea ~12):

```python
from rom_manager.detection.platform_detector import PLATFORM_BY_FOLDER
from rom_manager.web.handlers.system import _ES_PLATFORM_FOLDERS
```

Sin riesgo de import circular: `detection/` no importa de `web/`, y `system.py` ya es importado a nivel de módulo por `server.py` (rama 04).

### Paso 3 — Eliminar `_PLATFORM_FOLDERS` y `_platform_folder_name()`

Borrar el dict `_PLATFORM_FOLDERS` (líneas 19-47) y la función `_platform_folder_name()` (líneas 90-102) completos.

### Paso 4 — Nuevo resolver, reemplaza el call site (línea ~492)

```python
# Antes:
folder_name = _platform_folder_name(platform or "Unknown")

# Después:
canonical    = PLATFORM_BY_FOLDER.get((platform or "").lower(), platform or "")
folder_name  = _ES_PLATFORM_FOLDERS.get(canonical, "unknown")
```

Esto cubre:
- Nombres canónicos (`"PlayStation"` → no está en `PLATFORM_BY_FOLDER` → se usa tal cual → `_ES_PLATFORM_FOLDERS["PlayStation"]` = `"psx"`)
- Alias cortos heredados (`"genesis"` → `PLATFORM_BY_FOLDER["genesis"]` = `"Sega Mega Drive"` → `"megadrive"`; `"mame"` → `"Arcade"` → `"arcade"`)
- Plataforma vacía/desconocida → `"unknown"` (slug en minúscula, consistente con el resto)

### Paso 5 — Verificación

```bash
# No debe quedar ninguna referencia a la tabla eliminada:
grep -rn "_PLATFORM_FOLDERS\b" src/rom_manager/web/inbox_pipeline.py
# (solo deben aparecer _ES_PLATFORM_FOLDERS y _STANDARD_PLATFORM_FOLDERS en otros archivos)

python -m pytest tests/ -q
```

Si hay datos de prueba disponibles, ejecutar el agente `inbox-watchdog` para confirmar que el Step 6 ("organizing") coloca los juegos en carpetas `psx/`, `megadrive/`, `n64/`, etc. (no `PlayStation/`, `Sega Mega Drive/`, `Nintendo 64/`).

---

## Checklist

- [x] Paso 1 — `_ES_PLATFORM_FOLDERS` incluye `"Neo Geo Pocket Color": "ngpc"`
- [x] Paso 2 — `inbox_pipeline.py` importa `PLATFORM_BY_FOLDER` y `_ES_PLATFORM_FOLDERS` a nivel de módulo
- [x] Paso 3 — `_PLATFORM_FOLDERS` y `_platform_folder_name()` eliminados
- [x] Paso 4 — Step 6 del Inbox usa el nuevo resolver de dos pasos
- [x] Paso 5 — 390 tests pasan (2 fallos preexistentes no relacionados, sin cambios)
- [ ] Commit en rama, PR a main
