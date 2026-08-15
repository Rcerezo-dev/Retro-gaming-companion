# Retro Vault — Contexto del proyecto

Herramienta local Python + interfaz web (`http://127.0.0.1:7777`) para gestionar ROMs retro y sincronizar saves entre PC y consola Android.
Backlog activo: `Tareas/backlog.md`. Estado de fases: memoria `phases.md`.
CI/CD y GitHub Actions: `docs/ci-cd.md` (lint+format+pytest, branch protection, CodeRabbit, hooks pre-commit/pre-push, recetas y gotchas).

## Los 3 pilares (en orden de prioridad real)

1. **Primera vez** — limpiar y organizar una biblioteca caótica (basura fuera, ZIPs descomprimidos, ROMs renombrados con nombre canónico No-Intro/Redump, en su carpeta de plataforma).
2. **Día a día** — Inbox: soltar un juego sin organizar y que la herramienta detecte plataforma, descomprima, empareje con catálogo y lo mueva solo, sin intervención manual.
3. **Uso cotidiano — sync de saves** (**valor diferencial real**): jugar en Anbernic o PC, que la partida aparezca sola en el otro lado, sin miedo a sobreescribir. Cualquier bug aquí es prioridad absoluta (pérdida de progreso).

Todo lo demás (RA checker, scraper, health check, duplicados, informes) es secundario. No es un launcher/front-end de emuladores — no reemplaza RetroArch/EmulationStation. Detalle: memoria `vision_core.md`.

---

## Entorno de ejecución

- Conda: `C:\Users\rammu\anaconda3\envs\rom_manager` (Python 3.12)
- Lanzador: `scripts\rommgr.cmd`
- Directo: `C:\Users\rammu\anaconda3\envs\rom_manager\python.exe -m rom_manager <cmd>`
- `chdman` en `tools/chdman.exe` — NO en PATH
- `adb` en `tools/adb.exe`

---

## Gestión de tareas: Issues (roadmap) + Backlog (detalle)

Dos capas, cada una con su rol — no duplicar contenido entre ellas:

- **GitHub Issues, label `epic`** — roadmap de alto nivel. Un issue por tema/pilar
  (p. ej. "Pilar 2 — Inbox automático", "Distribución / Release"). Se usan para
  visibilidad y discusión, no para el detalle de implementación.
- **`Tareas/backlog.md`** — desglose operativo. Cada epic tiene una sección propia
  con una tabla de tareas con ID (mismo patrón que `PHASE6-*` o `EMULATOR-COMPAT-*`
  ya existentes), y la sección enlaza al issue: `→ #NNN`. Este archivo sigue siendo
  la fuente de verdad para el trabajo del día a día.

Flujo al surgir un tema nuevo:
1. Crear el issue en GitHub con label `epic` (alto nivel, sin desglosar).
2. Añadir una sección correspondiente en `backlog.md` con tabla de tareas ID-tagged,
   enlazando al número de issue.
3. Trabajar siempre contra `backlog.md` (rama por tarea, PR a `develop`, como ya
   se describe abajo). El issue se mantiene como estado agregado: se puede comentar
   o cerrar cuando todas las tareas de su sección estén ✅, pero no se edita tarea
   a tarea.

No confundir con `.claude/roadmaps/*.md` — esos son roadmaps técnicos paso a paso
para una rama de refactor concreta (ver `.claude/roadmaps/INDEX.md`), un nivel de
detalle distinto y con su propio índice.

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

### Investigar antes de arreglar

Cuando aparece un síntoma (archivos que no deberían estar donde están, un
número que no cuadra, un flujo que se queda a medias): verifica primero contra
la biblioteca real o la BD, no contra suposiciones — y sigue la cadena hasta la
causa raíz en el código, no solo el síntoma. No implementes el fix en la misma
sesión salvo que el usuario lo pida explícitamente: documenta el hallazgo con
archivo:línea exactos y añádelo al backlog (`Tareas/backlog.md`) para que se
implemente en su propia rama. Patrón ya usado en JUNK-FIX-*/INBOX-FIX-* (Día39).

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
