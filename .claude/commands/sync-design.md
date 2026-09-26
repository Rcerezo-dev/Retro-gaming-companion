Presenta el diseño técnico REAL (ya implementado) del sistema de sincronización de saves entre PC y Anbernic — Pilar 3, el valor diferencial del proyecto.

Este sistema lleva construido y en iteración mucho tiempo (`rclone` ya en uso vía `tools/rclone.exe`, Cable Sync por ADB, `save_sync_log` ya existe) — este comando NO es para diseñarlo desde cero, es para explicarlo tal como está hoy.

Pasos:

1. Lee `docs/architecture/architecture.md` (arquitectura actual, fuente de verdad) y `CLAUDE.md`.
2. Lee el módulo `src/rom_manager/sync/` completo (estructura de archivos y responsabilidad de cada uno).
3. Lee el schema de la tabla `save_sync_log` en `database/schema.py`.
4. Lee `web/handlers/sync_cable.py` y `web/cable_sync_daemon.py` para el flujo de Cable Sync (ADB).

Responde con:

1. **Estructura de carpetas en la nube**: cómo están organizados los saves hoy (rutas reales de `config.toml`, `[[sync.sources]]`).
2. **Protocolo de sync real**: qué criterio usa el código hoy para decidir el más reciente y detectar conflicto (mtime, hash, `save_sync_log`) — cita el archivo:función exacto.
3. **Transporte**: `rclone` para cloud sync, ADB (`sync/adb_transport.py`) para Cable Sync — cuándo se usa cada uno.
4. **Política de conflictos actual**: qué hace el código hoy, no qué podría hacer.
5. **`sync/` — archivos y responsabilidades reales**, no una propuesta.
6. **`save_sync_log` — columnas reales** tal como están en `schema.py`.

Si al leer el código encuentras algo que parece un bug o una decisión sin resolver (no un vacío de diseño — el diseño ya existe), documéntalo en `Tareas/backlog.md` siguiendo la regla de "investigar antes de arreglar" de `CLAUDE.md`, no lo propongas como pregunta abierta.
