# Roadmap 03 — `refactor/eliminate-late-imports`

**Rama:** `refactor/eliminate-late-imports`  
**Base:** `refactor/split-sync-handler`  
**Prioridad:** 🟠 P2  
**Esfuerzo estimado:** ~1 h  
**Riesgo:** Bajo — cambios mecánicos, sin lógica nueva

---

## Estado tras ramas 01 y 02

Las ramas anteriores ya eliminaron todos los `import rom_manager.web.server` de módulos externos.
`grep -r "import rom_manager.web.server" src/` devuelve solo 2 resultados, ambos en `server.py`.

| Línea | Descripción |
|-------|-------------|
| `server.py:87` | `import rom_manager.web.server as _srv_mod` — server se importa a sí mismo para pasarlo como `srv_mod` a los handlers |
| `server.py:462` | `import rom_manager.web.server as _srv` — import muerto (nunca se usa `_srv` en la función) |

---

## Problema residual

`srv_mod` se pasa a todos los handlers apuntando al módulo `server.py`, pero todo el estado que los handlers necesitan ya vive en `state.py`. Además, `esde.py` llama a funciones de `system.py` a través de `srv_mod` en lugar de importarlas directamente.

**Casos que requieren cambio:**

| Archivo | Acceso actual | Debe ser |
|---------|--------------|----------|
| `server.py:87` | `import server as _srv_mod` | `import state as _srv_mod` |
| `server.py:462` | `import server as _srv` (sin uso) | Eliminar |
| `esde.py:804` | `srv_mod._handle_system_status(config)` | import directo de `system.py` |
| `esde.py:809` | `srv_mod._handle_detect_cloud_folder()` | import directo de `system.py` |
| `esde.py:814` | `srv_mod._handle_library_doctor(config, repository)` | import directo de `system.py` |
| `esde.py:819` | `srv_mod._handle_retroarch_check(config)` | import directo de `system.py` |
| `scraper.py:398` | `srv_mod._ES_PLATFORM_FOLDERS` | import directo de `system.py` |

---

## Pasos

### Paso 1 — `server.py`: apuntar `_srv_mod` a `state`

```python
# Antes (línea 87):
import rom_manager.web.server as _srv_mod  # used by set_auto_sync_fn

# Después:
import rom_manager.web.state as _srv_mod
```

Eliminar el import muerto en `_on_sync_from_tray` (línea 462):
```python
# Eliminar esta línea (nunca se usa _srv):
import rom_manager.web.server as _srv
```

### Paso 2 — `esde.py`: imports directos de `system.py`

```python
# Añadir al bloque de imports de la función register():
from rom_manager.web.handlers.system import (
    _handle_system_status,
    _handle_detect_cloud_folder,
    _handle_library_doctor,
    _handle_retroarch_check,
)

# Reemplazar:
srv_mod._handle_system_status(config)    → _handle_system_status(config)
srv_mod._handle_detect_cloud_folder()    → _handle_detect_cloud_folder()
srv_mod._handle_library_doctor(...)      → _handle_library_doctor(...)
srv_mod._handle_retroarch_check(config)  → _handle_retroarch_check(config)
srv_mod._httpd_instance                  → (ya funciona vía state, se deja igual)
```

### Paso 3 — `scraper.py`: import directo de `system.py`

```python
# Antes (línea 398 dentro de _do_export_gamelists):
es_folders = srv_mod._ES_PLATFORM_FOLDERS

# Después:
from rom_manager.web.handlers.system import _ES_PLATFORM_FOLDERS
es_folders = _ES_PLATFORM_FOLDERS
```

### Paso 4 — Verificación

```bash
# Debe devolver 0 resultados fuera de server.py:
grep -r "import rom_manager.web.server" src/ --include="*.py"
# Solo server.py debe quedar (si queda alguno)

# Tests
python -m pytest tests/ -q
```

---

## Checklist

- [x] Paso 1 — `server.py` apunta a `state` en lugar de `server`
- [x] Paso 2 — `esde.py` importa directamente de `system.py`
- [x] Paso 3 — `scraper.py` importa directamente de `system.py`
- [x] Paso 4 — 390+ tests pasan, 0 late imports circulares
- [ ] Commit en rama, PR a main
