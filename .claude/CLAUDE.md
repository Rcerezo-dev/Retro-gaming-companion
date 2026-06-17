# Retro Vault — Contexto del proyecto

Herramienta local Python + interfaz web (`http://127.0.0.1:7777`) para gestionar ROMs retro y sincronizar saves entre PC y consola Android.
Backlog activo: `Tareas/backlog.md`. Estado de fases: memoria `phases.md`.
CI/CD y GitHub Actions: `docs/ci-cd.md` (lint+format+pytest, branch protection, CodeRabbit, hooks pre-commit/pre-push, recetas y gotchas).

---

## Entorno de ejecución

- Conda: `C:\Users\Ruben\anaconda3\envs\rom_manager` (Python 3.12)
- Lanzador: `scripts\rommgr.cmd`
- Directo: `C:\Users\Ruben\anaconda3\envs\rom_manager\python.exe -m rom_manager <cmd>`
- `chdman` en `tools/chdman.exe` — NO en PATH
- `adb` en `tools/adb.exe`

---

## Reglas de trabajo

- `rommgr plan` siempre antes de `rommgr apply`
- Nunca eliminar ni sobreescribir sin política de conflictos documentada
- PSX siempre por sets: nunca renombrar `.bin` sin reescribir el `.cue`
- BIOS, assets y carpetas Android nunca se tratan como ROMs
- Toda operación sobre archivos se registra en SQLite
- La biblioteca debe ser compatible con RetroArch en Android Y en PC
- En sync: ante duda, no sobreescribir; guardar backup primero
- Sin dependencias externas de runtime (solo stdlib)
- Usa Siempre los principios SOLID 
        El Principio de responsabilidad única (Single Responsibility Principle)
        El Principio Abierto-Cerrado (Open-Closed Principle)
        El Principio de sustitución de Liskov (Liskov Substitution Principle)
        El Principio de segregación de interfaz (Interface Segregation Principle)
        El Principio de inversión de dependencia (Dependency Inversion Principle) 
- **No vuelvas a leer archivos ya leídos en esta sesión a menos que te lo pida. Minimiza las llamadas a herramientas y trabaja con lo que ya tienes en contexto.**

---

## Patrones críticos

### Jobs en background (web)
```python
# _job_lock, _jobs dict, _xxx_progress dict, _job_results dict
# Frontend: startPolling() cada 2s → /api/job-status → _applyJobStatus(s)
# result_ts en cada resultado para evitar toasts infinitos (_shownResultTs)
```

### Rename atómico
```python
from rom_manager.renamer.file_renamer import rename_rom_with_saves
outcome = rename_rom_with_saves(source_path, target_path, save_extensions)
# outcome.success, outcome.saves_renamed, outcome.error
```

### Fix renames solo-mayúsculas en Windows (NTFS)
```python
# operation_planner.py — _same_file() con Path.samefile()
# Conflicto solo si target.exists() AND NOT _same_file(source, target)
```

### Config: recarga en memoria obligatoria tras guardar
```python
# _handle_save_config() DEBE recargar load_config() y actualizar todos los campos
# Sin esto los cambios no se aplican hasta reiniciar el servidor
```

### SQLite
```python
with repository.connect() as conn:  # lecturas
    rows = conn.execute("SELECT ...").fetchall()
# repository.batch() para escrituras en bulk
```

### Late imports (evitar circular imports)
```python
# cable_sync_daemon.py e inbox_pipeline.py importan server.py dentro de la función:
def _auto_sync_loop(config, get_repo_fn):
    import rom_manager.web.server as _srv
    _srv._auto_sync_status = {"state": "syncing"}  # reasignación → siempre via _srv.xxx
    _cable_progress = _srv._cable_progress          # mutación → binding local válido
```

### Static files
```
GET /static/app.css  →  src/rom_manager/web/static/app.css
GET /static/app.js   →  src/rom_manager/web/static/app.js
```
