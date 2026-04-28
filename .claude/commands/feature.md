Planifica e implementa la siguiente feature del archivo `Tareas/Día10-Mejoras-Pendientes.md`.

El argumento del comando es el identificador de la feature (ej: `F5`, `F7`, `F9`). Si no se proporciona argumento, pregunta al usuario cuál quiere implementar mostrando la lista de pendientes.

Pasos:

1. **Leer contexto**: Lee `Tareas/Día10-Mejoras-Pendientes.md` para encontrar la descripción de la feature. Lee también `CLAUDE.md` para recordar las convenciones del proyecto.

2. **Analizar impacto**: Identifica todos los archivos que necesitarán cambios:
   - `src/rom_manager/database/schema.py` — ¿nuevas columnas o tablas?
   - `src/rom_manager/database/repository.py` — ¿nuevos métodos?
   - `src/rom_manager/web/server.py` — ¿nuevos endpoints?
   - `src/rom_manager/web/frontend.py` — ¿nueva UI?
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

5. **Actualizar tracking**: Marca la feature como ✅ en `Tareas/Día10-Mejoras-Pendientes.md` con descripción de cómo se implementó.

6. **Actualizar diario**: Añade las entradas correspondientes al archivo `Tareas/Día10.md` (o el más reciente).
