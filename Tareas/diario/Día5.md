# ROM Manager Local — Día 5

## Contexto

Al cierre del Día 4 el proyecto estaba completo en funcionalidad principal. Esta sesión
se centró en dos cosas: documentación retroactiva de los días anteriores, y dos nuevas
funcionalidades orientadas a la transferencia de archivos entre PC y Anbernic por cable.

---

## Objetivos del día

1. Actualizar los diarios de trabajo de días anteriores con el estado real de cada tarea
2. Añadir pestaña "Cable Sync" para copiar ROMs y saves entre PC y Anbernic por USB
3. Resolver el problema de la BD desincronizada cuando se borran archivos del disco

---

## Trabajo realizado

### Documentación retroactiva

Se rellenaron los archivos de tareas que estaban incompletos o sin estado:

| Archivo | Qué faltaba | Qué se añadió |
|---------|-------------|---------------|
| `Día3-2.md` | Todas las secciones "_(Se irá rellenando)_" vacías | Trabajo completo: ScreenScraper, gamelist.xml, rename atómico, bugs corregidos, estado al finalizar |
| `Día2-3.md` | Sin marcadores de estado en ninguna tarea | ✅/❌/⚠️ por bloque; commits de referencia; tabla de orden actualizada |

### Pestaña "Cable Sync" (`web/frontend.py` + `web/server.py`)

Nueva pestaña en el frontend para sincronizar archivos entre PC y Anbernic mediante USB
(o cualquier ruta accesible: SD card montada, red local, etc.).

**UI:**
- Panel de instrucciones paso a paso (conectar cable → elegir modo File Transfer)
- Nota técnica con 3 opciones para hacer la ruta accesible desde Windows (SD card, Termux SFTP, WinFsp)
- Checkboxes: qué sincronizar (saves/states, ROMs, o ambos)
- 3 modos de dirección:
  - **PC → Anbernic** — copia todo del PC a la consola (recomendado tras renombrar)
  - **Anbernic → PC** — copia todo de la consola al PC
  - **Más reciente gana** — bidireccional por mtime, con warning explícito sobre el problema post-rename
- Checkbox dry run
- Barra de progreso con contador en tiempo real
- Tabla de resultados con los archivos procesados

**Backend (`_handle_cable_sync`):**
- Job en background con el mismo patrón de polling que el resto
- Copia con `shutil.copy2` (preserva mtime)
- Modo "más reciente": construye mapa de archivos de ambos lados, compara mtime, copia en la dirección correcta; también copia archivos que solo existen en un lado
- Filtrado por extensión: saves = `config.save_extensions`, roms = todo lo demás

**Por qué tres modos:** tras renombrar archivos en el PC, `os.rename` preserva el mtime original, pero si el archivo fue copiado/movido entre unidades el mtime se resetea. El modo "más reciente gana" fallaría en ese caso eligiendo siempre el PC. El modo "PC → Anbernic" lo resuelve sin comparar fechas.

### Purgado de entradas huérfanas en la BD (`scanner/rom_scanner.py` + `database/repository.py`)

**Problema:** cuando se borran archivos del disco, sus registros quedan en SQLite indefinidamente. Esto rompe el conteo de ROMs, los duplicados y (futuro) la deduplicación por SHA1 en el Cable Sync.

**Solución:** al final de cada scan, purgar automáticamente los registros cuyo archivo ya no existe.

`ScanResult` — nuevo campo `pruned: int = 0`

`scan_library()` — rastrea todos los paths encontrados en `seen_paths` (antes de `classify_path`, para incluir todos los archivos independientemente de su categoría). Al terminar llama a `prune_stale_entries`.

`repository.prune_stale_entries(source_root, seen_paths)`:
- Carga todas las rutas de `games`, `saves` y `assets` de la BD
- Filtra solo las que están bajo `source_root` (no toca otras raíces — si se escanea la SD de la Anbernic, no borra registros del PC y viceversa)
- Borra en una sola transacción las entradas que no aparecieron en disco
- Devuelve el total de registros eliminados

El resultado del scan ahora muestra `| Eliminados de BD: N` si se purgaron entradas.

---

## Archivos modificados

```
src/rom_manager/scanner/rom_scanner.py      MODIFICADO  (seen_paths + prune_stale_entries)
src/rom_manager/database/repository.py     MODIFICADO  (nuevo método prune_stale_entries)
src/rom_manager/web/server.py               MODIFICADO  (job cable_sync, endpoint /api/cable-sync)
src/rom_manager/web/frontend.py             MODIFICADO  (tab Cable Sync, JS loadCableSync/doCableSync)
Tareas/Día3-2.md                            RELLENADO
Tareas/Día2-3.md                            ACTUALIZADO (marcadores de estado)
```

---

## Decisiones de diseño tomadas

### Cable Sync: Opción A (scan previo + SHA1) para deduplicar ROMs Anbernic→PC

El usuario planteó cómo evitar copiar ROMs que ya están en el PC aunque tengan nombres distintos.
Se acordó el flujo:

1. Conectar SD card de la Anbernic al PC
2. Escanear la SD card (ya funciona — añadir ruta en Overview)
3. Los ROMs de la Anbernic quedan en la BD con su SHA1
4. La pestaña Duplicates muestra automáticamente qué ROMs de la Anbernic ya están en el PC
5. Cable Sync puede filtrar por SHA1 usando la BD (sin re-hashear)

Este flujo aprovecha la arquitectura existente sin cambios adicionales al escáner.
La implementación del filtro SHA1 en Cable Sync queda pendiente para la siguiente sesión.

---

## Estado al finalizar

- Cable Sync operativo para los 3 modos de dirección ✅
- BD se limpia automáticamente tras cada scan ✅
- Tests: no verificados en esta sesión ⚠️
- Flujo de deduplicación Anbernic→PC: diseñado, pendiente de implementar ⏳

---

## Siguiente sesión recomendada

Ver `Tareas/Siguientes-pasos.md` para la lista completa actualizada.

## Cambios vistos:
⏳ en overview, debería dar más instrucciones al usuario
⏳ No estoy seguro de si la pestaña "acciones" tiene sentido ahora (ya que las rutas se las has dado antes) aunque los botones scan, match catálogos y fix plataformas sí que tienen sentido
✅ en pestañas como plan, duplicates, assets y sync, hay que especificar muy bien si estamos haciendo esas acciones en la anbernic o en el pc — Implementado: selector de dispositivo global (PC / Sistema completo / Anbernic) en la barra de navegación; filtra Plan, Duplicates y Assets por dispositivo activo; context bars actualizados
en tools:
  ⏳ Descomprimir zips debería detectar todos los zips dentro de carpetas que estén dentro de otras carpetas, y al descomprimir, respetar la ruta
  ✅ generar playlists debería detectar automáticamente las carpetas donde puede haber archivos multidisco — Implementado: botón "Autodetectar carpetas" que llama a /api/disc-folders y rellena el input (o muestra selector si hay varias)
  ⏳ verificar sets multi disco ya hace eso, quizá el mismo algoritmo valdría?
  ✅ saves huérfanos nos debería dar la opción de borrar estos — Ya estaba implementado; mejorado: añadido "Seleccionar todos", estimación de espacio a liberar en el diálogo de confirmación
  ✅ convertir a chd nos debería dar una idea de por qué ha fallado una conversión — Mejorado: los errores de conversión se muestran ahora en negrita con el mensaje de error en cursiva roja destacada

⏳ También, creo que podría molar hacer una cosa: y si planteamos lo siguiente?
⏳ Al final de la pestaña tools, podríamos hacer un informe con acciones a hacer por el usuario, en html
⏳ ahí podemos incluir varias pestañas, se me ocurre:
⏳ zips descomprimidos
⏳ playlists generadas
⏳ sets multidisco (con el set completo y sin completar)
⏳ saves huérfanos
⏳ retro achievements: (juegos CON logros, sin logros, y aquellos que nuestra versión no permite logros pero Sí podría tener, fácil de seleccionar además en qué consola visualizar
⏳ juegos que no se han podido convertir a chd y una razón


la ruta de ambernic Este equipo\RG556\Ambernic no funciona =S 
Creo además que deberías rehacer las pestañas porque no queda muy clara esta interfaz. 
el primer consejo que puedo dar, es que para la fila de "games, matched, unmatched"... debería haber una segunda columna igual para los datos en la anbernic, si está conectada. por otro lado, creo que deberías permitir que, al pulsar sobre cada una de estas, me lleve a la lista de estos archivos 
comprueba, en cada una de las pestañas, si alguna parte o pestaña no está bien implementada (o incluso, su nombre no pega). De ser así, modifícalo 