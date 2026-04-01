# ROM Manager Local — Día 7: Fixes y mejoras (Roadmap)

*Generado: 2026-03-11 — A partir de FIXES_necesarios.md*

---

## Diagnóstico de cada problema

### F1. Falsos positivos en duplicados (Sistema Completo)

**Síntoma reportado:**
```
Resident Evil (World) (Proto 1) · SHA1: B25935416666…
  E:\Carpetas anbernic\psx\Resident Evil (World) (Proto 1).bin   ← Anbernic
  H:\psx\Resident Evil [Director's Cut] [Dual Shock].bin         ← PC

Driver (Europe) · SHA1: 44B09F2260AD…
  E:\Carpetas anbernic\psx\Driver (Europe)...(En,Fr,De,Es,It).img ← Anbernic
  H:\psx\Driver [SLUS-00842].img                                  ← PC
```

**Causa raíz probable:** El filtro cross-device en `_build_duplicates()` compara prefijos
(`pc_root.lower()` y `ab_root.lower()`), pero si esos valores no coinciden exactamente
con los prefijos de `source_path` en BD (ej. trailing slash, mayúsculas, ruta distinta a
la que se pasó en "Sistema completo"), las entradas no quedan correctamente clasificadas
como PC o Anbernic, y ambas caen en el mismo bucket → se muestran como duplicados.

**Causa secundaria:** Es posible que estos ROMs tengan SHA1 idéntico (mismo dump, diferente
nombre de archivo). Eso los hace duplicados reales de contenido, pero el usuario los trata
como copias intencionales entre dispositivos. Se necesita un mecanismo para marcarlos como
"copia intencional" y excluirlos permanentemente.

**Fix:**
- Añadir logging del filtro en `_build_duplicates()` para ver qué raíz matchea cada entrada
- Normalizar siempre los prefijos (resolve + rstrip + lower) antes de comparar
- Añadir botón "Marcar como copia intencional" por grupo → guarda la exclusión en BD

---

### F2. Tarjetas de Overview no son clicables

**Síntoma:** Los números en las cards (Games, Matched, Saves, Assets, Duplicados)
se ven pero no llevan a ningún sitio. Solo "Games" y "Matched" tienen `onclick`.

**Fix:** Hacer todas las cards navegables:
- Games → Games tab (sin filtro)
- Matched → Games tab filtrado por `matched`
- Unmatched → Games tab filtrado por `unmatched`
- Saves → Games tab filtrado por `filetype=save`
- Assets → pestaña Assets (ya existe)
- Duplicados → pestaña Duplicates
- Último scan → mostrar detalle del último scan_run

---

### F3. Cable Sync no iguala los conteos de ambos dispositivos

**Síntoma:** Después de hacer Cable Sync en modo "Igualar ambos dispositivos",
el número de juegos en PC y Anbernic es diferente.

**Causas posibles:**
1. El Cable Sync copia archivos al disco, pero la BD no se actualiza hasta hacer un Scan.
   El aviso "haz un Scan" existe, pero el usuario puede confundir "archivos copiados"
   con "BD sincronizada".
2. El modo `newest` solo sincroniza archivos con el mismo `rel_posix`. Si PC tiene
   `gba/Mario.gba` y Anbernic tiene `roms/gba/Mario.gba`, no se consideran el mismo archivo.
3. Algunos archivos fallan al copiarse (error OSError) sin aviso prominente.

**Fix:**
- En el resultado del Cable Sync, mostrar explícitamente si hubo errores y qué archivos fallaron
- Añadir botón "Lanzar scan ahora" directamente en el resultado del Cable Sync
  (no solo el aviso amarillo)
- Documentar en la UI que "igualar" significa misma estructura de carpetas relativa

---

### F4. Limpiador de archivos no relacionados con gaming

**Síntoma:** La Anbernic tiene archivos basura (Jupyter notebooks, Office, etc.)
que aparecen en el scanner y contaminan la biblioteca.

**Fix nuevo:** Nueva pestaña o sección en Tools — **"Limpieza de archivos"**:
- Escanear una carpeta y clasificar todos los archivos en:
  - ✅ Gaming (ROM, save, asset, BIOS, gamelist)
  - ⚠️ Gaming-adyacente (config RetroArch, screenshots, cheats)
  - 🗑️ No relacionado — agrupado por tipo: Documentos, Notebooks, Imágenes personales,
    Archivos comprimidos no-ROM, Ejecutables, etc.
- Mostrar tamaño total por categoría
- Permitir seleccionar categorías y eliminar de golpe (con confirmación y dry-run)

---

### F5. Plan no renombra todos los archivos / nombre confuso

**Síntoma A — Nombre:** El usuario no entiende qué es "Plan".
**Síntoma B — No renombra todo:** Quedan 1001 archivos sin renombrar tras múltiples intentos.

**Causas de B:**
- La mayoría probablemente son **conflictos** (colisiones o conflictos de disco). El botón
  "Apply" solo procesa los `pending`, no los `conflicts`.
- Si hay 1001 conflictos del tipo "colisión" (dos ROMs → mismo nombre canónico), el botón
  "Resolver automáticamente (keep_both)" debería resolverlos, pero puede que el usuario
  no lo haya usado o no lo haya visto.
- Si son conflictos de disco: hay archivos con el nombre destino ya ocupado. Requiere
  intervención manual.

**Fix:**
- Renombrar la pestaña "Plan" → **"Renombrar"** (o "Organizar")
- Añadir un resumen al tope: `X listos · Y conflictos · Z sin match` con explicación clara
- Dividir el botón Apply en dos:
  - "Aplicar renombrados sin conflicto" (solo pending)
  - "Resolver todos los conflictos" (keep_both automático)
- Mostrar progreso durante el apply (cuántos procesados de cuántos totales)

---

### F6. BD SQLite solo refleja stats del PC

**Síntoma:** La BD está en el PC. Al mirar stats de la Anbernic, depende de que la
Anbernic haya sido escaneada desde el PC (SD card conectada o ADB). Si el usuario
escanea solo el PC, la Anbernic no tiene entradas.

**Aclaración técnica:** Hay UNA sola BD. Tanto ROMs del PC como de la Anbernic
se guardan en ella, distinguiéndose por `source_path`. El problema es de flujo de trabajo:
el usuario no sabe que tiene que escanear la Anbernic explícitamente.

**Fix:**
- En Overview: indicador visual claro de "última vez que se escaneó la Anbernic"
  (distinto al último scan del PC)
- Si la Anbernic nunca se ha escaneado: banner amarillo explicándolo
- Opción "Scan automático de Anbernic al conectar la SD" (detectar nueva unidad)

---

### F7. Tools no recuerda las carpetas usadas

**Síntoma:** Cada vez que el usuario abre Tools tiene que escribir la ruta de la carpeta
en cada sección (CHD converter, ZIP extractor, folder analysis...).

**Fix:**
- Persistir el valor de cada input de ruta en `localStorage` con clave por sección
  (ej. `tool_path_chd`, `tool_path_zip`, `tool_path_analysis`)
- Al cargar la página, restaurar los valores guardados
- Botón "Usar library_root" como acceso rápido en cada input

---

### F8. Informe con navegación lateral y elementos interactivos

**Síntoma:** El informe generado (Library Report) es un scroll infinito hacia abajo.
Además, las secciones son estáticas (sin links, sin filtros).

**Fix:**
- Navegación lateral fija (sidebar con las secciones: Resumen, Plataformas, Multidisc,
  Huérfanos, RetroAchievements, CHD) — al hacer click, scroll suave a la sección
- En la sección RetroAchievements:
  - Link directo a cada juego en retroachievements.org
  - Filtro por plataforma (dropdown o botones)
  - Columna "Tienes la versión con logros / sin logros"
- En la sección de plataformas: barra de progreso visual de completado de la colección

---

### F9. Barras de progreso y cancelación en procesos largos

**Síntoma:** Cable Sync muestra progreso aleatorio. No se ven MB/GB procesados.
No hay forma de cancelar sin cerrar el servidor.

**Fix (aplica a TODOS los jobs largos: scan, match, scrape, CHD, zip, health, RA, cable):**
- Barra de progreso con porcentaje (`X / total archivos`)
- Tamaño procesado vs total (MB/GB) donde aplique (cable sync, CHD)
- Velocidad de transferencia en tiempo real (MB/s) en cable sync
- Tiempo estimado restante (ETA)
- El botón que lanzó el job cambia a **"Cancelar"** mientras el job corre
- Todos los jobs ya tienen `stop_event` — solo falta conectarlo a un botón

---

### F10. Games sigue mostrando .zip después de extraer y re-escanear

**Síntoma:** El usuario extrae ZIPs, re-escanea, y la pestaña Games sigue mostrando
los archivos `.zip` originales.

**Causa probable:** La extracción de ZIPs coloca los ROMs en la misma carpeta y borra
el ZIP. Al re-escanear, `prune_stale_entries` debería eliminar la entrada del `.zip`
de la BD. Pero si el scan se lanzó sobre una ruta distinta a la que se usó en
la extracción (o si el `.zip` no fue borrado), la entrada persiste.

**Fix:**
- Verificar que la tool de extracción ZIP borra el archivo origen cuando la opción
  "Eliminar .zip tras extraer" está activa
- Si el `.zip` sigue en disco (dry-run o error), la entrada es correcta — mostrar una
  advertencia en la UI indicando que el .zip aún existe
- Añadir botón "Lanzar scan ahora" en el resultado de la extracción ZIP
  (igual que en el Cable Sync)

---

## Bloques de implementación

### Bloque A — Fixes críticos de datos (F1, F6, F10)
*Prioridad: Alta — afectan a la fiabilidad de la información*

**A1.** Normalizar prefijos en `_build_duplicates()` + logging para diagnosticar F1
**A2.** Botón "Marcar como copia intencional" + tabla `excluded_duplicates` en BD
**A3.** Indicador "última vez escaneada la Anbernic" en Overview (F6)
**A4.** Botón "Lanzar scan ahora" en resultado de ZIP extractor y Cable Sync (F10/F3)

### Bloque B — UX de procesos largos (F9)
*Prioridad: Alta — la espera sin feedback es frustrante*

**B1.** Cable Sync: pasar tamaño total de archivos a copiar antes de empezar
**B2.** Cable Sync: actualizar `_cable_progress` con `bytes_copied`, `bytes_total`, `speed`
**B3.** Conectar `stop_event` a botón "Cancelar" visible mientras el job corre (todos los jobs)
**B4.** ETA calculado en frontend a partir de velocidad actual

### Bloque C — Renombrar / Plan (F5)
*Prioridad: Alta — es la función core del producto*

**C1.** Renombrar pestaña "Plan" → "Organizar"
**C2.** Resumen al tope: `X listos · Y conflictos · Z sin match`
**C3.** Separar "Aplicar pendientes" de "Resolver conflictos" en dos botones
**C4.** Progreso durante el apply (contador de archivos procesados)

### Bloque D — Overview clicable (F2)
*Prioridad: Media — mejora de navegación*

**D1.** Todas las cards de Overview llevan a la pestaña correspondiente con filtro correcto

### Bloque E — Tools: memoria de rutas (F7)
*Prioridad: Media — mejora de ergonomía diaria*

**E1.** Persistir rutas en `localStorage` por sección de Tools
**E2.** Botón "Usar library_root" en cada input de ruta

### Bloque F — Limpiador de archivos no-gaming (F4)
*Prioridad: Media — muy útil para la Anbernic*

**F1.** Nuevo endpoint `GET /api/junk-scan?path=...`
**F2.** Clasificación: ROM/save/asset/config/junk con subcategorías para junk
**F3.** Nueva sección en Tools "Limpieza" con tabla agrupada por categoría y tamaño
**F4.** Dry-run + confirmación antes de eliminar

### Bloque G — Informe interactivo (F8)
*Prioridad: Baja — mejora visual del informe*

**G1.** Sidebar de navegación fija en el Library Report
**G2.** Links a retroachievements.org en sección RA
**G3.** Filtro por plataforma en sección RA
**G4.** Barras de progreso visual en sección de plataformas

### Bloque H — Diagnóstico F3 (Cable Sync ≠ conteos)
*Prioridad: Baja — necesita más información del usuario*

**H1.** Investigar por qué los conteos difieren (puede ser consecuencia de F1 o F6)
**H2.** Mejorar resumen post-sync: errores prominentes + archivos que fallaron

---

## Estado

| Bloque | Descripción | Estado | Prioridad |
|--------|-------------|--------|-----------|
| A — Fixes de datos | Duplicados falsos, scan Anbernic, stale ZIPs | ✅ Hecho | Alta |
| B — Progreso y cancelación | Barras, ETA, botón cancelar | ✅ Hecho | Alta |
| C — Organizar (Plan) | Renombrar pestaña, separar botones, progreso apply | ✅ Hecho | Alta |
| D — Overview clicable | Todas las cards navegan | ⏳ Pendiente | Media |
| E — Tools recuerda rutas | localStorage por sección | ⏳ Pendiente | Media |
| F — Limpiador no-gaming | Nueva sección en Tools | ⏳ Pendiente | Media |
| G — Informe interactivo | Sidebar + links RA | ⏳ Pendiente | Baja |
| H — Cable Sync conteos | Diagnóstico y mejora de resumen | ⏳ Pendiente | Baja |

## Orden de implementación recomendado

```
Sesión 1:  C                    # Renombrar + UX de apply — impacto inmediato
Sesión 2:  A1 → A2 → A4        # Duplicados falsos + scan triggers
Sesión 3:  B1 → B2 → B3        # Progreso Cable Sync + cancelación global
Sesión 4:  D → E                # Overview clicable + Tools recuerda rutas
Sesión 5:  F                    # Limpiador de archivos
Sesión 6:  A3 → H              # Indicador Anbernic + Cable Sync conteos
Sesión 7:  B4 → G              # ETA + informe interactivo
```
