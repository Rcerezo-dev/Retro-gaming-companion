Presenta el diseño técnico del sistema de sincronización de saves entre PC y Anbernic.

Lee primero `CLAUDE.md` y `MEMORY.md` para tener el contexto completo, luego responde a estas preguntas de diseño:

1. **Estructura de carpetas en la nube**: ¿cómo deberían organizarse los saves para que la ruta sea predecible desde ambos dispositivos?

2. **Protocolo de sync**: ¿qué algoritmo usar para determinar qué save es el más reciente y si hay conflicto?
   - Considera: mtime del archivo, hash del contenido, registro en SQLite de la última sync

3. **Herramienta de transporte**: compara las opciones:
   - `rclone` (CLI, multiplataforma, soporta muchos proveedores)
   - API directa del proveedor (más control, más código)
   - Para la Anbernic: ¿puede correr `rclone`? ¿qué firmware tiene?

4. **Conflictos**: ¿qué hacer si el PC y la Anbernic tienen saves distintos del mismo juego?
   - Opciones: el más reciente gana, pedir confirmación, guardar ambos como backup

5. **Estructura del módulo `sync/`**: propón los archivos y responsabilidades

6. **Tabla `save_sync_log`**: qué columnas necesita

Indica claramente qué decisiones necesitan respuesta del usuario antes de poder implementar.
