# Fixes necesarios — Roadmap activo

> Este archivo es el tracking activo de los 10 fixes reportados originalmente.
> Cada fix se marca ✅ en cuanto queda implementado.
> Para el detalle técnico de cada bloque ver `Día7-Fixes.md`.

---

## Estado general

| # | Fix | Estado |
|---|-----|--------|
| 1 | Falsos positivos en duplicados (Sistema Completo) | ✅ Hecho |
| 2 | Cards de Overview no son clicables | ⏳ Pendiente |
| 3 | Cable Sync no iguala los conteos de ambos dispositivos | ⏳ Pendiente |
| 4 | Limpiador de archivos no relacionados con gaming | ⏳ Pendiente |
| 5 | Pestaña "Plan" confusa / no renombra todos los archivos | ✅ Hecho |
| 6 | BD SQLite solo refleja stats del PC | ✅ Hecho (parcial) |
| 7 | Tools no recuerda las carpetas usadas | ⏳ Pendiente |
| 8 | Informe sin navegación lateral ni elementos interactivos | ⏳ Pendiente |
| 9 | Cable Sync sin barra de progreso real ni botón cancelar | ✅ Hecho |
| 10 | Games sigue mostrando .zip tras extraer y re-escanear | ✅ Hecho (parcial) |

---

## Detalle por fix

### ✅ Fix 1 — Falsos positivos en duplicados (Sistema Completo)
**Síntoma original:**
```
Resident Evil (World) (Proto 1) · SHA1: B25935416666…
  E:\Carpetas anbernic\psx\Resident Evil (World) (Proto 1).bin   ← Anbernic
  H:\psx\Resident Evil [Director's Cut] [Dual Shock].bin         ← PC
```
**Qué se hizo:**
- Normalización de rutas con `os.path.normcase + os.path.normpath + trailing sep` en `_build_duplicates()` — elimina diferencias de mayúsculas y separadores en Windows
- Fix del bug de "localStorage vacío": `loadDuplicates()` ahora siempre envía `pc_root` al servidor usando el valor del input `ov-pc-path` o `cfg.library_root` como fallback; antes podía no enviar nada y el servidor devolvía todos los duplicados sin filtrar
- Nueva tabla `excluded_duplicates` en BD + botón "Copia intencional ✓" por grupo → el SHA1 queda excluido permanentemente de la lista de duplicados

---

### ⏳ Fix 2 — Cards de Overview no son clicables
**Síntoma original:** Los números en las cards (Games, Matched, Saves, Assets, Duplicados) se ven pero no llevan a ningún sitio.
**Pendiente:** Bloque D — todas las cards deben navegar a la pestaña correspondiente con el filtro correcto.

---

### ⏳ Fix 3 — Cable Sync no iguala los conteos de ambos dispositivos
**Síntoma original:** Después de Cable Sync en modo "Igualar ambos", el número de juegos en PC y Anbernic es diferente.
**Pendiente:** Bloque H — diagnóstico de causas (BD no actualizada hasta nuevo Scan, diferencias en rutas relativas) y mejora del resumen post-sync.

---

### ⏳ Fix 4 — Limpiador de archivos no relacionados con gaming
**Síntoma original:** La consola Android tiene archivos basura (Jupyter notebooks, Office, etc.) mezclados con los ROMs.
**Pendiente:** Bloque F — nueva sección "Limpieza" en Tools con clasificación por categorías, tamaño por grupo, y eliminación por lotes con dry-run.

---

### ✅ Fix 5 — Pestaña "Plan" confusa / no renombra todos los archivos
**Síntoma original:** El usuario no entiende qué es "Plan". Quedan 1001 archivos sin renombrar tras múltiples intentos.
**Qué se hizo:**
- Pestaña renombrada a **"Organizar"**
- Barra de resumen al tope: `X listos · Y conflictos · Z sin match`
- Dos botones separados: "Aplicar X renombrados" (solo pendientes sin conflicto) y "Resolver Y conflictos" (keep_both automático)
- El apply es ahora un job en background con barra de progreso en tiempo real (archivo actual + contador)

---

### ✅ Fix 6 — BD SQLite solo refleja stats del PC *(parcial)*
**Síntoma original:** La BD solo tiene datos del PC si no se ha escaneado la Anbernic explícitamente.
**Qué se hizo:**
- Indicador "Último scan" en las tarjetas de la consola Android en Overview — muestra la fecha del último scan para esa ruta
- Si la consola nunca se ha escaneado: mensaje de aviso amarillo en sus tarjetas
**Pendiente completo:** Bloque A3 / banner prominente si nunca se escaneó; opción de auto-scan al conectar SD.

---

### ⏳ Fix 7 — Tools no recuerda las carpetas usadas
**Síntoma original:** Cada vez que el usuario abre Tools tiene que volver a escribir la ruta en cada sección.
**Pendiente:** Bloque E — persistir rutas en `localStorage` por sección de Tools; botón "Usar library_root" en cada input.

---

### ⏳ Fix 8 — Informe sin navegación lateral ni elementos interactivos
**Síntoma original:** El Library Report es un scroll infinito. Sin links, sin filtros.
**Pendiente:** Bloque G — sidebar de navegación fija, links a retroachievements.org, filtro por plataforma en sección RA, barras de progreso de completado por plataforma.

---

### ✅ Fix 9 — Cable Sync sin barra de progreso real ni botón cancelar
**Síntoma original:** Barra de progreso aleatoria, sin MB/GB, sin forma de cancelar salvo cerrar el servidor.
**Qué se hizo:**
- Pre-scan antes de copiar para calcular `bytes_total` y `total_files` (modo FS y modo ADB)
- Barra de progreso real: `MB copiados / MB totales`, velocidad en MB/s, ETA calculado
- **Todos** los botones de job largo se convierten en "Cancelar" (rojo) mientras corren: Cable Sync, CHD, ZIP, Health, RA, Scrape, Match
- Cada job tiene su `threading.Event` de cancelación; se activa desde `POST /api/stop-job`

---

### ✅ Fix 10 — Games sigue mostrando .zip tras extraer y re-escanear *(parcial)*
**Síntoma original:** Tras extraer ZIPs y re-escanear, los archivos `.zip` siguen apareciendo en la pestaña Games.
**Qué se hizo:**
- Botón **"Escanear ahora"** en el resultado del ZIP Extractor (lanza un scan del PC automáticamente sin ir a Overview)
- El scan al finalizar ejecuta `prune_stale_entries` que elimina de la BD los archivos que ya no existen en disco
**Pendiente completo:** Verificar que la tool de extracción borra el `.zip` origen cuando la opción "Eliminar .zip" está activa; si el `.zip` sigue en disco (error o dry-run), mostrar advertencia en la UI.

---

## Estado de implementación (actualizado esta sesión)

| # | Fix | Estado |
|---|-----|--------|
| 2  | Cards de Overview no son clicables | ✅ Ya estaba hecho |
| 7  | Tools no recuerda las carpetas usadas | ✅ Ya estaba hecho |
| 8  | Informe sin navegación lateral | ✅ Hecho — sidebar fija en HTML report |
| 11 | Sección Tools: botón "Aplicar todas" a todas las carpetas | ✅ Hecho |
| 12 | Informe salud: Parasite Eve 2 con 3 discos faltantes | ✅ Hecho — regex fix en _DISC_RE |
| 13 | Problemas detectados: añadir columna Plataforma | ✅ Hecho |
| 14 | Informes separados PC/Android + botón regenerar | ✅ Parcial — botones PC/Android en Tools |
| 15 | Saves huérfanos: emparejar con sus ROMs | ✅ Hecho — fuzzy match + botón Mover |
| 16 | Duplicados: eliminar la versión sin logros RA | ✅ Hecho — botón Eliminar en RA duplicates |
| 17 | RA Checker: informe HTML no se muestra | ✅ Hecho — bug clave "alternatives" vs "results" |
| 18 | Pérdida de juegos en consola Android — logging | 🔄 En progreso (agente) |
| 19 | Archivos sin match: explicar razón | ✅ Hecho — badges no_sha1 / no_dat / hash_not_found |
| 20 | Acceso directo para lanzar la app | ✅ Hecho — Crear_acceso_directo.ps1 en raíz |

**Pendientes reales:**
- Fix 3: Cable Sync count mismatch (diagnóstico profundo)
- Fix 18: Cable Sync logging persistente (agente en background)
- Fix 14: Auto-generación de informe tras scan/sync (parcial)

---

### ⏳ Fix 11 — Sección Tools: botón "Aplicar todas"
**Síntoma:** El usuario tiene que ir sección por sección en Tools introduciendo cada ruta.
**Pendiente:** Bloque I — añadir un botón global "Ejecutar todas las herramientas sobre la biblioteca" que corra en orden: ZIP extractor → CHD converter → Renombrador → Health check. Con confirmación previa y log unificado.

---

### ⏳ Fix 12 — Informe salud: Parasite Eve 2 multi-disco incorrecto
**Síntoma:** Parasite Eve 2 aparece como si le faltaran 3 discos, y el juego aparece varias veces en el informe.
**Pendiente:** Bug en la detección de sets multi-disco — probablemente el `multidisc_verifier` o el `m3u_generator` no agrupa correctamente los discos de este título. Revisar la lógica de agrupación por nombre base.

---

### ⏳ Fix 13 — Problemas detectados: añadir columna Plataforma
**Síntoma:** En la pestaña "Problemas detectados" del informe, los juegos aparecen sin indicar a qué plataforma pertenecen.
**Pendiente:** Añadir columna "Plataforma" a la tabla de problemas detectados en el informe HTML.

---

### ⏳ Fix 14 — Informes separados PC/Android + auto-generación
**Síntoma:** El informe actual mezcla datos de ambos dispositivos sin distinción.
**Propuesta:**
- Generar el informe automáticamente al finalizar cada Scan (sin que el usuario lo pida).
- El informe siempre está disponible (no hay que pulsar "Generar").
- Dos vistas: "PC" y "Consola Android" con pestaña o selector.
- Botón "Regenerar informe" disponible también tras Cable Sync.
**Pendiente:** Bloque I — diseño del flujo auto-generación + split por dispositivo.

---

### ⏳ Fix 15 — Saves huérfanos: emparejar con sus ROMs
**Síntoma:** Hay saves en la carpeta "huérfanos" que podrían pertenecer a ROMs que existen con distinto nombre.
**Pendiente:** En la vista de saves huérfanos, añadir lógica de sugerencia: si el stem del save hace match fuzzy con el stem de una ROM en la BD, proponer el emparejamiento y mover el save junto a la ROM.

---

### ⏳ Fix 16 — Duplicados: eliminar la versión sin logros RA
**Síntoma:** En la vista "Duplicados por versión" se puede ver qué ROMs no tienen logros en RetroAchievements, pero no hay botón para eliminar la versión sin logros.
**Pendiente:** Añadir botón "Eliminar sin logros" en cada grupo de duplicados — mueve el archivo a papelera/carpeta `_eliminados` (nunca borrado directo), registra en BD.

---

### ⏳ Fix 17 — RA Checker: informe HTML no funciona al exportar
**Síntoma:** Al ejecutar "Comprobar RA" en Tools el resultado se muestra inline, pero al exportar el HTML y abrirlo, el informe RA no aparece.
**Pendiente:** El HTML exportado probablemente no incluye la sección de resultados RA generada dinámicamente por JS. Revisar `gamelist_writer.py` o la lógica de exportación para que los datos RA queden embebidos en el HTML estático.

---

### 🔴 Fix 18 — Pérdida de juegos en consola Android (CRÍTICO)
**Síntoma:** Tras operaciones recientes, Megadrive y Nintendo 64 tienen 0 juegos en la consola Android, mientras PSX se mantiene. Se han perdido también saves. No se sabe qué operación los eliminó.
**Hipótesis:**
- Cable Sync en modo "Igualar" pudo haber sobreescrito/eliminado archivos en la dirección incorrecta.
- El `prune_stale_entries` pudo haber marcado como eliminados archivos que sí existen en la consola pero no en el último scan.
**Pendiente (urgente):**
1. Añadir log detallado de TODAS las operaciones de copia/borrado en Cable Sync (qué archivo, dirección, resultado).
2. Revisar si `prune_stale_entries` elimina registros de rutas de la consola cuando se escanea solo el PC.
3. Añadir confirmación explícita antes de cualquier operación destructiva en la consola Android.
4. Considerar modo "solo añadir, nunca eliminar" como opción de Cable Sync.

---

### ⏳ Fix 19 — Archivos sin match: explicar razón
**Síntoma:** Muchos archivos no hacen match con el catálogo pero no se sabe por qué (nombre muy diferente, hash no en DAT, plataforma sin DAT cargado...).
**Pendiente:** En la pestaña Organizar (o en el informe), añadir sección desplegable "Sin match" con columnas: archivo, plataforma detectada, razón estimada (no DAT cargado / hash no encontrado / nombre muy diferente). Ayuda al usuario a saber qué importar o corregir manualmente.

---

### ⏳ Fix 20 — Acceso directo para lanzar la app
**Síntoma:** El usuario tiene que navegar a `scripts\rommgr.cmd` cada vez para arrancar la app.
**Pendiente:** Crear un acceso directo `.lnk` en el escritorio (o en la raíz del proyecto) que ejecute `scripts\rommgr.cmd` directamente. Instrucciones para crearlo o script PowerShell que lo genere automáticamente.
 