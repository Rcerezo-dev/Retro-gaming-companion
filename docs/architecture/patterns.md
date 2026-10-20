# Patrones críticos del código

> Movido desde `.claude/CLAUDE.md` (DOCS-AUDIT-2d). Léelo antes de tocar el área correspondiente.

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

### Estado compartido vía web/state.py (CLEAN-1)
```python
# El estado mutable global vive en rom_manager.web.state, importado a nivel
# de módulo (NO late import). server.py importa los handlers también a nivel
# de módulo (ninguno importa server → sin ciclo).
import rom_manager.web.state as _state

def _auto_sync_loop(config, get_repo_fn):
    _state._auto_sync_status = {"state": "syncing"}  # reasignación → siempre via _state.xxx
    _cable_progress = _state._cable_progress          # mutación → binding local válido
# srv_mod= que reciben los handlers es un alias legado de web.state (se elimina en ARC-JM-6).
```

### ZIPs sueltos: identidad por contenido (ZIP-ROUTE)
```python
# El header del ZIP ya trae el CRC32 de cada entrada → identificar SIN descomprimir:
# CatalogMatcher.crc_index() (consola) y load_arcade_crc_index() (votación arcade).
# Los tags del nombre ("(XBLA)", "(Disk 1)") mienten: el contenido manda.
# Un ZIP arcade NUNCA se extrae ni pasa por el Inbox — el ZIP es el ROM.
# Colocación en un paso: web/zip_router.py (job "inbox", delete_source=True).
```

### Static files
```
GET /static/app.css  →  src/rom_manager/web/static/app.css
GET /static/app.js   →  src/rom_manager/web/static/app.js
```
