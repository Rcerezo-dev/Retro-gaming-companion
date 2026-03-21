# ROM Manager Local — Día 2

## Resumen

Revisión completa del código actual. Se identifican bugs reales, problemas de diseño y los próximos pasos prioritarios.

El proyecto tiene una base sólida: estructura modular, SQLite con upsert, hashing correcto, clasificación por categoría. Los problemas son concretos y corregibles.


---

## Bugs activos (rompen comportamiento real)

### 1. Formatos de disco PSX no se detectan como ROM

**Archivo:** `detection/platform_detector.py`

`ROM_EXTENSIONS` solo incluye:

```python
AMBIGUOUS_EXTENSIONS = {".md", ".bin", ".cue", ".iso", ".zip", ".chd"}
```

Los formatos `.ecm`, `.mdf`, `.mds`, `.ccd`, `.sub`, `.img` no están en `ROM_EXTENSIONS`.

Consecuencia: cuando el escáner encuentra un archivo `.mdf` o `.ecm`, `is_rom_file()` devuelve `False` y `file_classifier.py` lo manda a `UNKNOWN` en lugar de `ROM`. El `set_detector.py` los conoce perfectamente pero nunca los recibe.

**Solución:** añadir estos formatos a `AMBIGUOUS_EXTENSIONS` o a `ROM_EXTENSIONS`:

```
.img, .ecm, .mdf, .mds, .ccd, .sub, .7z
```

---

### 2. Doble clasificación en `asset_scanner.py`

**Archivos:** `scanner/rom_scanner.py` y `scanner/asset_scanner.py`

En `rom_scanner.py`, `_store_asset()` solo se llama cuando `classify_path()` ya devolvió `FRONTEND_ASSET`. Pero `inspect_asset()` en `asset_scanner.py` vuelve a llamar `classify_path()` por dentro y retorna `None` si no es un asset.

Esto significa que cada asset es clasificado dos veces. Además, la función puede silenciosamente no registrar el asset si las dos llamadas discrepan (aunque en la práctica no ocurre, el código es frágil).

**Solución:** eliminar la llamada interna a `classify_path` en `inspect_asset`. La función debe recibir solo el `path` y devolver tipo y plataforma, sin re-clasificar.

---

### 3. Extensiones de save duplicadas e inconsistentes

**Archivos:** `detection/platform_detector.py` y `config.py`

`platform_detector.py` tiene su propio `SAVE_EXTENSIONS` hardcodeado. `config.py` tiene `save_extensions` con más entradas (`.sgm`, `.brm`, `.nv`, `.hi`, `.fs`, `.state1`, `.state2`).

En `file_classifier.py` se consultan ambas:

```python
if is_save_file(path) or extension in config.save_extensions:
```

Hay dos fuentes de verdad para lo mismo. Si alguien añade una extensión al config no la verá `is_save_file()`. Si alguien añade a `platform_detector.py` no la verá el config.

**Solución:** eliminar `SAVE_EXTENSIONS` de `platform_detector.py`. `is_save_file()` debe consultar solo `config.save_extensions`, igual que hacen otras partes del código.

---

## Problemas de diseño (no son bugs pero limitan el crecimiento)

### 4. Sin soporte de config.toml

**Archivo:** `config.py`

Todo está hardcodeado en `load_config()`. El plan de diseño menciona explícitamente un `config.toml` con parámetros como carpetas excluidas, extensiones, política de conflictos, umbral de confianza para renombrado automático, etc.

Sin config externo, el usuario no puede personalizar nada sin tocar el código.

**Solución propuesta:** añadir soporte para leer un `config.toml` opcional en el directorio de datos `.rommgr/`. Los valores del toml sobreescriben los valores por defecto de `load_config()`. Usar `tomllib` (disponible desde Python 3.11, sin dependencias externas).

---

### 5. Conexión SQLite por operación

**Archivo:** `database/repository.py`

Cada `upsert_game()`, `upsert_save()` y `upsert_asset()` abre y cierra una conexión SQLite y hace un `commit()` inmediato. Para un escaneo de 5.000 ROMs esto produce 5.000+ transacciones individuales, lo que es muy lento.

**Solución propuesta:** añadir un método de contexto `batch()` al repositorio que mantenga la conexión abierta durante el escaneo y haga commit al final. El `scan_library()` lo usaría para procesar todos los archivos en una sola transacción.

---

### 6. `load_config` usa `Path.cwd()` como raíz

**Archivo:** `config.py`

Si el usuario ejecuta `rommgr scan E:\coleccion` desde `C:\Users\rammu`, la base de datos se crea en `C:\Users\rammu\.rommgr\library.sqlite`, no junto a la colección.

Esto puede ser intencionado (un único `.rommgr` global), pero no está documentado ni es configurable.

**Solución propuesta:** decidir explícitamente la estrategia y documentarla. Opciones:

- `.rommgr/` siempre en `%APPDATA%\rommgr\` (un único punto de datos global)
- `.rommgr/` en el directorio desde el que se lanza el CLI (comportamiento actual)
- `--data-dir` como argumento opcional en el CLI

---

### 7. `region_parser.py` muy limitado

**Archivo:** `detection/region_parser.py`

Solo detecta: Spain, USA, Europe, PAL, Japan. No detecta: France, Germany, Italy, Korea, China, Brazil, Australia, World, ni variantes comunes como `[EUR]`, `[GER]`, `[FRA]`, `(World)`, etc.

Además, el plan especifica usar `UNK` cuando la región es desconocida, pero el código devuelve `None`.

**Solución propuesta:** ampliar con al menos las regiones más comunes de No-Intro y devolver `"UNK"` en lugar de `None` para archivos sin región detectada.

Regiones a añadir mínimo:

```
France, Germany, Italy, Korea, China, Brazil, Australia, World,
[EUR], [GER], [FRA], [ITA], [KOR], [CHN], [BRA], [AUS]
```

---

### 8. Extensiones ambiguas sin contexto de carpeta

**Archivo:** `detection/platform_detector.py`

Solo `.md` tiene lógica de contexto de carpeta (`PLATFORM_CONTEXT_BY_EXTENSION`). Las extensiones `.bin`, `.iso`, `.zip`, `.chd` se clasifican siempre como ROM independientemente de dónde estén.

Un archivo `README.bin` o `patch.zip` sería clasificado como ROM.

**Solución propuesta:** añadir al menos reglas de exclusión básicas para estos casos, o extender `PLATFORM_CONTEXT_BY_EXTENSION` con pistas de carpeta para las extensiones más problemáticas.

---

### 9. Sin progreso visible durante el escaneo

**Archivo:** `scanner/rom_scanner.py`

El bucle en `scan_library()` itera con `rglob("*")` sin ningún feedback. En colecciones de miles de archivos el usuario no ve nada hasta que termina.

**Solución propuesta:** imprimir una línea de progreso cada N archivos (por ejemplo cada 100), o usar el logger para emitir un mensaje periódico. No requiere librerías externas.

---

### 10. Tabla `games` incompleta respecto al diseño

**Archivo:** `database/schema.py`

La tabla `games` en el esquema actual le faltan campos previstos en el diseño:

| Campo | Estado |
|---|---|
| `canonical_title` | Ausente |
| `match_confidence` | Ausente |
| `catalog_source` | Ausente |
| `library_path` | Ausente |
| `year` | Ausente |
| `developer` | Ausente |
| `genre` | Ausente |

La tabla `file_operations` (historial de renombrados y movimientos) tampoco existe aún.

Estos campos son necesarios para las Fases 2 y 3 (matching y renombrado).

**Solución propuesta:** añadir las columnas que se necesitarán pronto en una migración limpia, antes de que haya datos de producción que proteger. Las columnas de metadatos (`year`, `developer`, `genre`) pueden esperar a la Fase 5.

Columnas a añadir antes de la Fase 2:

```sql
canonical_title TEXT,
match_confidence TEXT,
catalog_source TEXT,
library_path TEXT
```

Y crear la tabla `file_operations`.

---

### 11. CLI solo tiene `scan` y `status`

**Archivo:** `cli.py`

El plan define estos comandos:

```
scan, plan, apply, status, unresolved, duplicates,
inspect-platform, inspect-assets
```

Solo están implementados `scan` y `status`. Para avanzar a la Fase 2 habrá que añadir al menos `unresolved` (lista ROMs sin identificar) como primer paso de revisión.

---

### 12. Sin tests

No existe ningún directorio `tests/` ni ningún archivo de prueba.

El plan menciona tests en la Fase 4, pero hay funciones con lógica compleja que deberían cubrirse antes de ampliar el código:

- `region_parser.parse_region_from_name()` — muchas variantes posibles
- `file_classifier.classify_path()` — lógica de exclusión por directorio
- `filename_normalizer.sanitize_filename()` — caracteres especiales de Windows
- `hash_calculator.calculate_hashes()` — verificar salida conocida

---

## Orden de trabajo recomendado para el Día 2

### Bloque A — Arreglar bugs antes de tocar nada más ✓ COMPLETADO

1. ~~Añadir `.img`, `.ecm`, `.mdf`, `.mds`, `.ccd`, `.sub`, `.7z` a `ROM_EXTENSIONS`~~ — hecho
2. ~~Eliminar `SAVE_EXTENSIONS` de `platform_detector.py` y hacer que `is_save_file()` use `config`~~ — hecho
3. ~~Simplificar `inspect_asset()` para que no reclasifique~~ — hecho

### Bloque B — Mejorar la base de datos ✓ COMPLETADO

4. ~~Añadir columnas `canonical_title`, `match_confidence`, `catalog_source`, `library_path` a `games`~~ — hecho
5. ~~Crear tabla `file_operations`~~ — hecho
6. ~~Añadir batch commit al repositorio para escaneos grandes~~ — hecho
   - `repository.batch()` context manager: una sola transacción para todo el escaneo
   - `upsert_game/save/asset` aceptan `connection` opcional; si se pasa, no hacen commit propio
   - Migración automática de BD existente con `PRAGMA table_info` + `ALTER TABLE`

### Bloque C — Mejorar detección ✓ COMPLETADO

7. ~~Ampliar `region_parser.py` con más regiones y devolver `"UNK"` en lugar de `None`~~ — hecho
   - 28 regiones No-Intro (parentheses), 14 códigos GoodTools (brackets), fallbacks de texto plano
   - Devuelve `"UNK"` en lugar de `None` en todos los casos sin región detectada
8. ~~Añadir progreso de escaneo (log cada 100 archivos)~~ — hecho (con el Bloque B)

### Bloque D — Preparar la Fase 2 ✓ COMPLETADO

9. ~~Crear `catalog/__init__.py` con la estructura básica del cargador de catálogos~~ — hecho
10. ~~Definir formato esperado: DAT de No-Intro (XML Logiqx)~~ — implementado en `catalog_loader.py`
11. ~~Implementar `catalog_loader.py`~~ — hecho; `load_nointro_dat()` construye `sha1 → CatalogEntry`; `load_dat_directory()` carga una carpeta entera de DATs
12. ~~Añadir comando `unresolved` al CLI~~ — hecho; agrupa por plataforma, muestra región si conocida

### Bloque E — Tests mínimos ✓ COMPLETADO

13. ~~Crear `tests/`~~ — hecho; 3 archivos de test:
    - `test_region_parser.py` — 25 casos parametrizados (No-Intro, GoodTools, fallbacks, UNK)
    - `test_filename_normalizer.py` — 16 casos (caracteres inválidos, espacios, puntos finales)
    - `test_file_classifier.py` — ROMs, saves, assets, `gamelist.xml`, unknown, carpetas excluidas
    - `pytest` añadido como dependencia de desarrollo en `pyproject.toml`

---

## Lo que no hay que tocar hoy

- `planner/`, `renamer/`, `converters/` — todavía no toca
- Lógica PSX detallada — esperar a que el matching básico funcione
- Frontend — Fase 6
- Conversión a CHD — necesita `chdman` y es Fase 6
- `sync/` — Fase 5


---


## Segunda iteración del roadmap — visión completa actualizada

La visión del proyecto ha evolucionado. Ya no es solo un gestor de biblioteca local: es una herramienta que mantiene una biblioteca compartida entre PC y Anbernic RG 556, con sincronización automática de saves en la nube.

### Contexto nuevo incorporado

- La biblioteca debe ser compatible con RetroArch en Android (RG 556), no solo con emuladores de PC.
- Los saves y save states se sincronizan en Dropbox (o proveedor configurable) vía `rclone` en el PC.
- La Anbernic usa Android nativo; la solución más práctica para el lado de la consola es Termux + rclone.
- El frontend web local (Fase 6) se podrá usar desde el navegador de la Anbernic cuando estén en la misma red WiFi.
- App Android nativa (Flutter) queda como opción futura si el proyecto madura y la necesita.


### Roadmap revisado

```
Fase 1 — Fundación          [activa]
Fase 2 — Matching           [pendiente]
Fase 3 — Plan + Apply       [pendiente]
Fase 4 — Calidad            [pendiente]
Fase 5 — Sync de saves      [pendiente]
Fase 6 — Frontend web       [pendiente]
```

---

### Fase 1 — Fundación (estado actual + pendientes de hoy)

Lo que ya funciona: escaneo recursivo, hashing, clasificación, SQLite, CLI básico.

**Pendientes del Bloque B (para hoy):**

| # | Tarea | Archivo principal |
|---|---|---|
| 1 | Añadir columnas `canonical_title`, `match_confidence`, `catalog_source`, `library_path` a `games` | `database/schema.py` |
| 2 | Crear tabla `file_operations` (historial de operaciones) | `database/schema.py` |
| 3 | Batch commit en el repositorio para escaneos grandes | `database/repository.py` |

**Pendientes del Bloque C (para hoy):**

| # | Tarea | Archivo principal |
|---|---|---|
| 4 | Ampliar `region_parser.py` con regiones No-Intro + devolver `"UNK"` en vez de `None` | `detection/region_parser.py` |
| 5 | Progreso de escaneo visible cada 100 archivos | `scanner/rom_scanner.py` |

**Pendientes del Bloque D (para hoy si queda tiempo):**

| # | Tarea | Archivo principal |
|---|---|---|
| 6 | Estructura básica de `catalog/catalog_loader.py` | `catalog/` |
| 7 | Comando `rommgr unresolved` en el CLI | `cli.py` |

**Pendientes del Bloque E (tests mínimos):**

| # | Tarea |
|---|---|
| 8 | `tests/test_region_parser.py` |
| 9 | `tests/test_file_classifier.py` |
| 10 | `tests/test_filename_normalizer.py` |

---

### Fase 2 — Matching fiable

Objetivo: identificar ROMs por hash contra catálogos locales No-Intro y Redump.

| Tarea | Notas |
|---|---|
| `catalog/catalog_loader.py` | Leer archivos DAT de No-Intro (formato XML Logiqx) y construir dict `sha1 → {title, region, ...}` |
| `catalog/nointro_matcher.py` | Buscar SHA1 en el catálogo cargado; devolver resultado con nivel de confianza |
| `catalog/redump_matcher.py` | Igual pero para catálogos Redump (útil para PSX, Saturn, Dreamcast) |
| Niveles de confianza | `high` (match por SHA1), `medium` (match por nombre normalizado), `low` (heurística), `none` |
| Persistir matching en BD | Actualizar `canonical_title`, `match_confidence`, `catalog_source` en `games` |
| `rommgr unresolved` | Listar juegos con `match_confidence = none` |

---

### Fase 3 — Plan y renombrado

Objetivo: proponer y ejecutar la reorganización de forma segura.

| Tarea | Notas |
|---|---|
| `planner/operation_planner.py` | Genera lista de operaciones (rename/move/skip/flag) sin tocar nada |
| `planner/conflict_resolver.py` | Detecta colisiones de nombres destino; aplica política skip/duplicate/suffix |
| `planner/psx_set_planner.py` | Trata sets PSX como unidad lógica; no renombra `.bin` sin reescribir `.cue` |
| `renamer/rom_renamer.py` | Ejecuta el plan; registra en `file_operations` |
| `renamer/save_renamer.py` | Renombra el save asociado en la misma operación que la ROM |
| `renamer/cue_rewriter.py` | Reescribe las referencias internas del `.cue` tras renombrar los `.bin` |
| `rommgr plan <ruta>` | Genera y muestra el plan sin ejecutar nada |
| `rommgr plan --preserve-subfolders` | Mantiene jerarquía relativa de subcarpetas |
| `rommgr apply` | Ejecuta el último plan confirmado |
| `rommgr duplicates` | Lista ROMs con SHA1 repetido |

La estructura de carpetas destino debe ser compatible tanto con RetroArch en PC como con RetroArch en Android (RG 556). Esto condiciona los nombres de carpeta de plataforma.

---

### Fase 4 — Calidad

Objetivo: herramienta robusta para colecciones grandes.

| Tarea | Notas |
|---|---|
| Reanudación incremental | Saltar archivos cuyo `source_path` ya está en BD con el mismo `size_bytes` (skip de hash) |
| Suite de tests automatizados | Cubrir clasificador, region parser, sanitizador, planner, conflict resolver |
| `rommgr inspect-platform psx` | Resumen de formatos, sets y anomalías de PSX |
| `rommgr inspect-assets` | Lista assets y metadatos detectados |
| Validación de archivos `.cue` | Detectar `.cue` con referencias rotas antes de renombrar |
| Reportes exportables | JSON o CSV con el estado de la biblioteca |
| `config.toml` externo | Personalización de exclusiones, extensiones, política de conflictos, umbral de confianza |

---

### Fase 5 — Sincronización de saves

Objetivo: PC y Anbernic RG 556 tienen siempre el save más reciente, sin intervención manual.

**Qué se sincroniza:** saves de batería (`.sav`, `.srm`, `.mcr`, etc.) y save states (`.state`, `.state0`–`.state9`, etc.)

**Transporte en el PC:** `rclone` como binario externo. La herramienta Python lo invoca como subprocess. Soporta Dropbox, OneDrive, Google Drive, S3 y más con la misma configuración.

**Transporte en la Anbernic (Android):** Termux + rclone. Configurado igual que en el PC. Termux:Boot lanza la sync al arrancar la consola cuando hay WiFi.

**Estructura en la nube (propuesta):**
```
rommgr-sync/
  saves/
    Game Boy/
      Tetris [World] (SHA1).sav
    SNES/
      Super Mario World [USA] (SHA1).srm
  states/
    Game Boy/
      Tetris [World] (SHA1).state
      Tetris [World] (SHA1).state1
```

| Tarea | Notas |
|---|---|
| `sync/rclone_transport.py` | Wrapper sobre el binario `rclone`; abstrae el proveedor |
| `sync/save_syncer.py` | Detecta qué save es más reciente por mtime; decide subir o bajar |
| `sync/conflict_resolver.py` | El más reciente gana; si hay ambigüedad, guarda backup con timestamp |
| `sync/sync_log.py` | Registra cada operación de sync en tabla `save_sync_log` de SQLite |
| `rommgr sync-saves` | Sync bidireccional de saves y states |
| `rommgr sync-status` | Muestra qué saves están desactualizados en cada lado |
| Guía de configuración Termux | Pasos para instalar rclone en Termux y configurar Termux:Boot |

---

### Fase 6 — Frontend web local

Objetivo: interfaz visual accesible desde PC y desde el navegador de la Anbernic (misma red WiFi).

| Tarea | Notas |
|---|---|
| Backend ligero (FastAPI o similar) | Expone la BD y los comandos del CLI como API REST |
| Página principal | Estado de la biblioteca: totales por plataforma, pendientes, errores |
| Selector de carpeta | Elegir qué carpeta escanear u organizar |
| Vista previa del plan | Muestra el plan de cambios antes de aplicarlo; permite activar/desactivar elementos |
| Modo flatten / preserve_subfolders | Toggle visible en la UI |
| Panel de sync | Estado de saves: última sync, saves desactualizados, historial |
| Accesible desde la Anbernic | El servidor corre en el PC; la consola accede desde el navegador Android cuando están en la misma WiFi |
| App Android nativa (Flutter) | Opcional, fase posterior si el proyecto madura. Requiere gestionar permisos `MANAGE_EXTERNAL_STORAGE` en Android 11+. |

---

### Resumen visual del roadmap

```
HOY
 └─ Fase 1 [completar]: BD mejorada, region_parser, progreso, catalog básico, tests

PRÓXIMA SESIÓN
 └─ Fase 2: matching por hash con catálogos No-Intro/Redump

DESPUÉS
 └─ Fase 3: plan + apply, renombrado seguro, soporte PSX por sets
 └─ Fase 4: tests completos, reanudación, reportes, config.toml

MÁS ADELANTE
 └─ Fase 5: sync de saves con Dropbox via rclone + Termux en la Anbernic
 └─ Fase 6: frontend web accesible desde PC y navegador de la consola
```
