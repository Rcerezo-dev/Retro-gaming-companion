Planifica e implementa una tarea del backlog (`Tareas/backlog.md` es el índice; el detalle vive en `Tareas/backlog/<epic>.md`).

El argumento del comando es el ID de la tarea (ej: `CABLE-SYNC-EMULATOR-SAVES-LEAK-1`, `JUEGOS-FIX-4`). Si no se proporciona argumento, pregunta al usuario cuál quiere implementar mostrando la tabla "Pendiente y por revisar" de `Tareas/backlog.md` (secciones `pendiente`; las `revisar` no tienen estado fiable).

Pasos:

1. **Leer contexto**: Localiza la tarea con `grep -rn "<ID>" Tareas/backlog/` (incluye `hecho/` por si ya está cerrada) y lee **solo esa sección** del archivo de epic, nunca el archivo entero (hasta 1.300 líneas). Lee también `CLAUDE.md` para recordar las convenciones del proyecto.

2. **Analizar impacto**: Identifica todos los archivos que necesitarán cambios:
   - `src/rom_manager/database/schema.py` — ¿nuevas columnas o tablas?
   - `src/rom_manager/database/repository.py` / `database/repositories/*.py` — ¿nuevos métodos?
   - `src/rom_manager/web/handlers/*.py` — ¿nuevos endpoints?
   - `web/static/js/tabs/*.js` + `web/static/partials/*.html` — ¿nueva UI?
   - ¿Nuevos módulos?

3. **Plan detallado**: Antes de tocar código, escribe el plan completo:
   ```
   ## Plan para [F_N — Nombre]
   ### Cambios en BD
   ### Nuevos endpoints
   ### Cambios en UI
   ### Casos borde a manejar
   ### Riesgos
   ```
   Muestra el plan al usuario y espera confirmación antes de implementar.

4. **Implementar**: Aplica los cambios siguiendo las convenciones:
   - `from __future__ import annotations` en módulos nuevos
   - `@dataclass(slots=True)` para structs
   - Migraciones en `_GAMES_MIGRATIONS` (no crear tablas nuevas sin discutirlo)
   - Verificar compilación al terminar: `python -c "import py_compile; ..."`

5. **Actualizar tracking**: Marca la tarea como ✅ en su archivo de epic `Tareas/backlog/<epic>.md` con descripción de cómo se implementó. Si con ello todas las filas de la sección quedan ✅, mueve la sección a `Tareas/backlog/hecho/<epic>.md` y quita su fila de la tabla "Pendiente y por revisar" de `Tareas/backlog.md`. Si la tarea pertenece a un epic con issue de GitHub (`→ #NNN` en la cabecera de sección), marca también su checkbox en el issue.

6. **Actualizar diario**: Añade las entradas correspondientes al archivo `Tareas/diario/Día*.md` más reciente.
