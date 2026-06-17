# Roadmap 04 — `refactor/consolidate-state`

**Rama:** `refactor/consolidate-state`  
**Base:** `refactor/eliminate-late-imports`  
**Prioridad:** 🟠 P2  
**Esfuerzo estimado:** ~45 min  
**Riesgo:** Bajo — solo reorganización de imports, sin cambio de lógica

---

## Estado tras ramas 01-03

`state.py` existe y contiene todo el estado global. Los handlers lo acceden de dos formas inconsistentes:

| Patrón | Archivos | Problema |
|--------|----------|---------|
| `import rom_manager.web.state as _state` a nivel de módulo | `cable_sync_daemon.py`, `daemons.py`, `server.py` | ✅ Correcto |
| `import rom_manager.web.state as _xxx` **dentro de funciones** | `sync_cloud.py` (×4), `scraper.py` (×1), `esde.py` (×1) | ❌ Inconsistente |
| Acceso vía `srv_mod.*` (= state) | handlers varios | ✅ Funciona pero indirecto |

---

## Objetivo

Unificar el acceso a `state` con imports a nivel de módulo en todos los archivos que hoy lo importan dentro de funciones. No tocar la firma de `register()` ni el parámetro `srv_mod` (hacerlo sería una refactorización mayor fuera de alcance).

---

## Pasos

### Paso 1 — `sync_cloud.py`: 4 late imports → 1 módulo-level

Añadir en la cabecera del archivo (después de los TYPE_CHECKING):

```python
import rom_manager.web.state as _state
```

Luego reemplazar dentro de las funciones:
- `run()` en `_do_sync` (líneas 187, 380): eliminar los `import rom_manager.web.state as _srv13/e`; usar `_state.*`
- closure `post_auto_sync_toggle` (línea 76): eliminar `import rom_manager.web.state as _state` dentro del closure
- `_do_auto_sync_save` (línea 392): eliminar `import rom_manager.web.state as _srv`; usar `_state.*`

### Paso 2 — `scraper.py`: 1 late import → módulo-level

Añadir en la cabecera del archivo:
```python
import rom_manager.web.state as _state
```
Eliminar el `import rom_manager.web.state as _state_s` dentro de `run()` (línea 87).  
Renombrar `_state_s` → `_state` en los usos posteriores.

### Paso 3 — `esde.py`: mover el import de `register()` al módulo

El `import rom_manager.web.state as _state` dentro de `register()` (añadido en rama 03) puede subir al bloque de imports del módulo.

### Paso 4 — Verificación

```bash
# No debe haber late imports de state dentro de funciones:
grep -n "import rom_manager.web.state" src/rom_manager/web/handlers/*.py
# Solo deben aparecer en las primeras líneas de cada archivo (nivel módulo)

python -m pytest tests/ -q
```

---

## Checklist

- [x] Paso 1 — `sync_cloud.py` usa import módulo-level
- [x] Paso 2 — `scraper.py` usa import módulo-level
- [x] Paso 3 — `esde.py` usa import módulo-level
- [x] Paso 4 — 390+ tests pasan
- [ ] Commit en rama, PR a main
