# ROM Manager Local — Día 6 (Roadmap)

*Generado: 2026-03-11 — Continuación del Día 5-3*

---

## Contexto

Primer uso real con la SD card de la Anbernic conectada. Se detectan cuatro tipos de problemas:
errores de código concretos (import roto, scan lento), problemas de UX (archivos basura en Games,
duplicados RA que no funcionan), y una tarea de investigación (estructura de archivos PSX).

---

## Problemas identificados

### P1. Bug crítico: import `PLATFORM_TO_CONSOLE_ID` no existe

`_build_ra_duplicates()` en `server.py` importa `PLATFORM_TO_CONSOLE_ID` desde
`ra_platform_ids.py`, pero ese nombre no existe. El dict interno se llama `_RA_CONSOLE_IDS`
(privado). La función pública es `get_ra_console_id(platform)`.

**Error exacto:**
```
{"error": "cannot import name 'PLATFORM_TO_CONSOLE_ID' from
'rom_manager.retroachievements.ra_platform_ids'"}
```

**Fix**: reemplazar la importación y uso directo por `get_ra_console_id()`.

---

### P2. Games — todavía aparecen archivos que no son juegos

A pesar de que `get_games_paginated` filtra por `file_type = 'rom'`, el usuario sigue
viendo archivos extraños. Posibles causas:
- Archivos escaneados antes de que el filtro existiera (registros con `file_type != 'rom'`)
- La tabla `games` contiene saves o assets mal clasificados en scans anteriores
- El usuario quiere ver también saves (`.sav`, `.srm`) junto a sus ROMs

**Fix**:
1. Añadir columna `file_type` visible en la tabla Games (ROM / save / asset / unknown)
2. Añadir filtro desplegable en la UI: "Mostrar: Solo ROMs | ROMs + saves | Todo"
3. Por defecto mostrar solo ROMs, pero permitir ampliar la vista

---

### P3. RA duplicates — no detecta "Castlevania Portrait of Ruin (En,Fr,De,Es,It)" vs. sin región

El usuario tiene:
- `Castlevania - Portrait of Ruin (En,Fr,De,Es,It).nds` → sin logros RA
- `Castlevania - Portrait of Ruin.nds` → con logros RA

Ambos deberían normalizar al mismo título y aparecer como grupo en la sección
"Duplicados por versión — sin logros RA".

Posibles causas:
- El MD5 de la versión sin región **sí** está en la caché RA (y por tanto ambas tienen logros)
- La caché RA no se ha descargado aún para NDS (console_id = 18)
- La normalización de títulos produce strings distintos por el guión " - "

**Fix**:
1. Añadir endpoint de diagnóstico `/api/ra-duplicates/debug` que muestre MD5 de cada ROM
   y si está o no en la caché RA, para el caso NDS
2. Revisar que `_normalize_title` trata " - " y guiones correctamente
3. Si la caché no existe para NDS: mostrar mensaje en la UI "Ejecuta la comprobación RA primero"

---

### P4. Scan lento — 4600 juegos, +20 minutos sin terminar

El scan completo calcula SHA1+MD5+CRC32 para cada ROM. Para una biblioteca grande (miles de
archivos, varios GB cada PSX/CHD), esto puede tardar horas en un primer scan.

Análisis:
- SHA1 de un CHD de 700 MB → ~10-30 segundos en un HDD
- 100 juegos PSX en CHD → 15-50 minutos solo para PSX
- El incremento (mtime-cache) solo funciona en el **segundo** scan

**Fixes**:
1. **Progress granular**: el progreso en frontend solo se actualiza cada 100 archivos;
   reducir a cada 10 para dar feedback más frecuente durante scans lentos
2. **Quick scan como default opcional**: mostrar advertencia si la biblioteca tiene > 500 ROMs
   y quick=False, sugiriendo activar Quick scan
3. **Mostrar archivo actual** mientras escanea (no solo el conteo)
4. **Diagnóstico de velocidad**: al finalizar, informar cuántos archivos se hashearon vs.
   cuántos se saltaron por mtime-cache

---

### P5. Investigación: tipos de archivo PSX en H:\psx

El usuario tiene una carpeta PSX (`H:\psx`) con archivos de tipos desconocidos o no
gestionados actualmente. Hay que:
1. Listar todos los tipos de extensión presentes
2. Documentar cuáles se clasifican como ROM, cuáles como unknown, cuáles se ignoran
3. Detectar si hay sets incompletos (`.cue` sin su `.bin`, o `.bin` sin `.cue`)
4. Detectar si hay formatos que necesiten soporte: `.img`, `.mdf/.mds`, `.ccd/.img/.sub`

**Resultado esperado**: informe de extensiones y recomendaciones (convertir a CHD, renombrar, etc.)

---

### P6. Stale entries — confirmar que funciona tras scan

El usuario recuerda que hay que quitar archivos que ya no estén en disco tras un scan.
`prune_stale_entries()` ya está implementado y se llama al final de cada `scan_library()`.
Hay que verificar que:
1. Funciona correctamente (test de integración)
2. El resultado del scan muestra cuántos registros se podaron en el resultado
3. La UI muestra el número de entradas prunificadas en el banner de resultado del scan

---

## Bloque A — Fix import RA duplicates (P1) — PRIORITARIO

```python
# server.py — _build_ra_duplicates()
# Cambiar:
from rom_manager.retroachievements.ra_platform_ids import PLATFORM_TO_CONSOLE_ID
console_id = PLATFORM_TO_CONSOLE_ID.get(plat_key)

# Por:
from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id
console_id = get_ra_console_id(plat)  # ya normaliza internamente
```

Eliminar también la normalización manual `plat_key = plat.lower().replace(...)` que ya
hace `get_ra_console_id` internamente.

---

## Bloque B — Games: columna file_type + filtro (P2)

### B1. Backend
Extender `get_games_paginated` para aceptar `file_type: str | None = None`:
- `'rom'` (default) → solo ROMs
- `'save'` → solo saves (join con tabla saves)
- `None` → todo

### B2. Frontend
- Añadir `<select>` en la toolbar de Games: "Tipo: ROMs | ROMs + saves | Todo"
- La columna "Ext." ya muestra la extensión; añadir columna "Tipo" con badge de color

---

## Bloque C — Diagnóstico RA duplicates (P3)

### C1. Debug endpoint
`GET /api/ra-duplicates/debug?platform=nds` → devuelve lista de todos los ROMs de esa
plataforma con: `{filename, md5, ra_found: bool, ra_achievements: int}`.

### C2. Mensaje de caché ausente
Si no hay caché RA para ninguna plataforma → mostrar en la sección un banner:
"Ejecuta la comprobación RA en Tools antes de usar esta sección."

### C3. Normalización de títulos
Revisar `_normalize_title` con casos como:
- `"Castlevania - Portrait of Ruin (En,Fr,De,Es,It)"` → `"castlevania portrait of ruin"`
- `"Castlevania - Portrait of Ruin"` → `"castlevania portrait of ruin"`
El guión ` - ` debe eliminarse (ya lo hace `[^a-z0-9 ]`) pero dobles espacios pueden
quedar → añadir `re.sub(r" +", " ", t).strip()` al final.

---

## Bloque D — Scan: progress granular + archivo actual (P4)

### D1. Reducir intervalo de progreso
`_PROGRESS_INTERVAL = 100` → `_PROGRESS_INTERVAL = 10` en `rom_scanner.py`.

### D2. Mostrar archivo actual en progreso
En `_progress_cb`, añadir `current_file` al `_scan_progress`:
```python
_scan_progress.update({
    "files_seen": files_seen, "roms_detected": roms,
    "current_path": str(source), "current_file": str(path.name),
})
```
Esto requiere pasar el path actual al callback → cambiar firma de `progress_cb`
a `Callable[[int, int, Path], None]`.

### D3. Estadística de hash en resultado
El resultado del scan ya incluye `files_seen` y `roms_skipped` (mtime-cache hit).
Añadir `roms_hashed = roms_detected - roms_skipped` al banner de resultado.

### D4. Advertencia quick scan en biblioteca grande
Antes de lanzar el scan, si `quick=False` y hay > 500 ROMs ya en BD → mostrar
un aviso en la UI: "Tienes X ROMs. Un scan completo puede tardar mucho.
Considera activar Quick scan para actualizaciones rápidas."

---

## Bloque E — Investigación PSX (P5)

### E1. Nuevo endpoint de análisis de carpeta
`GET /api/folder-analysis?path=H:\psx` → lista todas las extensiones encontradas,
con conteo y clasificación (ROM / save / asset / unknown / excluded).

### E2. Detección de sets CUE incompletos
Ya existe `validate_cue()`. Añadir al análisis: sets con `.bin` huérfano (sin `.cue`),
o `.cue` que referencia un `.bin` que no existe.

### E3. Soporte a formatos alternativos PSX
Revisar si `.img`, `.mdf`, `.mds`, `.ccd` ya están en `ROM_EXTENSIONS`.
Si no, añadirlos con nota de que necesitan conversión a CHD.

---

## Bloque F — Stale entries: verificación y UI (P6)

### F1. Test de integración
Añadir test en `test_scanner.py`: escanear carpeta, borrar un archivo, volver a escanear,
verificar que el registro desaparece de la BD.

### F2. Mostrar pruned en resultado del scan
El campo `pruned` ya está en `_job_results["scan"]`. Añadirlo al banner de resultado
en el frontend: "X ROMs detectadas, Y eliminadas de BD (ya no en disco)".

---

## Orden de implementación

```
Sesión 1:  A              # Fix import — CRÍTICO, desbloquea RA duplicates
Sesión 2:  C3 → C2        # Fix normalización + mensaje caché ausente
Sesión 3:  D1 → D2 → D3  # Scan progress granular + archivo actual
Sesión 4:  B1 → B2        # Games filter por tipo
Sesión 5:  C1             # Debug endpoint RA
Sesión 6:  E1 → E2 → E3  # Investigación PSX
Sesión 7:  F1 → F2        # Stale entries test + UI
Sesión 8:  D4             # Advertencia quick scan
```

---

## Estado

| Bloque | Estado |
|--------|--------|
| A — Fix import RA | ⏳ Pendiente |
| B — Games filter por tipo | ⏳ Pendiente |
| C — RA duplicates debug + normalización | ⏳ Pendiente |
| D — Scan progress granular | ⏳ Pendiente |
| E — Investigación PSX | ⏳ Pendiente |
| F — Stale entries test + UI | ⏳ Pendiente |
No entiendo por qué, pero al usar cable sync para copiar juegos desde mi anbernic al pc, debería cambiar el numero de juegos en PC, pero re escaneo y no pasa nada (se están copiando de verdad?)
Además, cuando hago un scan, no deja de salir un aviso abajo a la derecha de scan completado, cuando solo debería salir uno, no infinitamente
por último, creo que al usar cable sync, al final debería haber los mismos archivos (games, matched, saves, etc) en ambos dispositivos