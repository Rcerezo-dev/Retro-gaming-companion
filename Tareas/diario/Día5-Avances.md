# Avances del 8 de marzo de 2026

## Contexto

Objetivo del proyecto:

- construir una herramienta local en Python para analizar, identificar, renombrar y reorganizar colecciones de ROMs
- soportar bibliotecas reales, no solo carpetas limpias
- preparar un frontend futuro para elegir la carpeta a reorganizar y decidir si se conservan subcarpetas

Documento principal de planificación:

- `Tareas/Día1.md`


## Lo que se hizo hoy

### 1. Planificación del proyecto

Se rehizo `Tareas/Día1.md` para convertirlo en un plan real de ejecución.

Se definieron:

- alcance del MVP
- flujo `scan -> plan -> apply`
- estructura de carpetas objetivo
- modelo de datos en SQLite
- arquitectura modular
- roadmap por fases
- reglas de seguridad

### 2. Análisis de una biblioteca real

Se inspeccionó:

- `E:\Carpetas anbernic`

Conclusiones importantes:

- no es una carpeta solo de ROMs
- mezcla sistemas, BIOS, Android, imágenes, vídeos, `gamelist.xml`, saves y archivos del dispositivo
- hay que clasificar archivos antes de reorganizarlos
- varias carpetas incluyen metadata visual dentro de la propia plataforma

Decisiones tomadas:

- introducir categorías lógicas de archivo:
  - `rom`
  - `save`
  - `frontend_asset`
  - `system_support`
  - `unknown`
- excluir por defecto carpetas como `Android`, `BIOS`, `DCIM`, `Movies`, `Music`, `Documents`, `backup`

### 3. Análisis específico de PSX

Se inspeccionó:

- `E:\Carpetas anbernic\psx`

Patrones detectados:

- mezcla de juegos en carpetas y archivos sueltos en raíz
- formatos mezclados: `.bin/.cue`, `.img/.ccd/.sub`, `.pbp`, `.mdf/.mds`, `.ecm`
- notaciones inconsistentes de disco: `(Disc 1)`, `[CD1]`, `[Disc1of2]`, `[Disco 2]`
- regiones e idiomas expresados de forma desigual
- algunos nombres corruptos o dudosos

Decisiones tomadas:

- PSX debe tratarse por sets, no por archivos sueltos
- conservar variantes de región e idioma
- conservar códigos `SLUS/SLES/SCUS/SCES` cuando aporten diferenciación
- unificar la notación a `Disc N`
- no renombrar `.bin` sin reescribir el `.cue`
- dejar `.ecm` y sets dudosos para revisión manual

### 4. Conversión de formatos

Se planteó preparar la herramienta para conversión futura, especialmente en PSX.

Conclusiones:

- la conversión razonable a futuro es `CHD`
- hace falta una herramienta externa real, previsiblemente `chdman`
- en esta máquina no se detectó `chdman`, `maxcso` ni `7z` en `PATH`
- por tanto, hoy no se implementó conversión real; solo se dejó como diseño futuro

### 5. Frontend futuro

Se añadió al plan que debe existir un frontend local donde el usuario pueda:

- elegir la carpeta concreta que quiere reorganizar
- ver una vista previa
- decidir si mantiene o no las subcarpetas

Se definieron dos modos:

- `flatten`
- `preserve_subfolders`

### 6. Implementación de la Fase 1

Se creó la estructura base del proyecto Python:

- `src/rom_manager`
- subpaquetes para `database`, `detection`, `hashing`, `scanner`
- placeholders para `catalog`, `planner`, `renamer`, `converters`, `utils`, `logging`

Se implementó:

- configuración base
- logging a archivo y consola
- SQLite con tablas iniciales
- CLI con `scan` y `status`
- hashing `SHA1`, `MD5`, `CRC32`
- detección básica de plataforma por extensión
- clasificación inicial de archivos
- exclusiones por defecto
- persistencia de ROMs, saves y assets
- campos para `relative_parent`, `region` y `set_type`


## Archivos relevantes creados o tocados

- `pyproject.toml`
- `README.md`
- `Tareas/Día1.md`
- `src/rom_manager/cli.py`
- `src/rom_manager/config.py`
- `src/rom_manager/database/schema.py`
- `src/rom_manager/database/repository.py`
- `src/rom_manager/detection/file_classifier.py`
- `src/rom_manager/detection/platform_detector.py`
- `src/rom_manager/detection/region_parser.py`
- `src/rom_manager/detection/set_detector.py`
- `src/rom_manager/hashing/hash_calculator.py`
- `src/rom_manager/scanner/rom_scanner.py`
- `src/rom_manager/scanner/asset_scanner.py`


## Estado actual del código

La Fase 1 está iniciada y útil como inventario, pero todavía incompleta respecto al objetivo total.

Ya existe:

- un CLI mínimo
- una base SQLite local
- clasificación inicial de biblioteca
- escaneo recursivo con exclusiones

Todavía no existe:

- matching por hash con catálogos
- plan de cambios
- aplicación de cambios reales
- reescritura de `.cue`
- tratamiento específico de PSX
- frontend


## Limitaciones encontradas hoy

- no hay un intérprete Python funcional disponible en `PATH` dentro de este entorno
- `python.exe` apunta al alias de `WindowsApps` y falla
- `py` no está disponible

Consecuencia:

- no se pudo ejecutar una verificación real del CLI desde esta sesión
- el código se ha validado por inspección estructural, no por ejecución


## Siguiente paso recomendado

El siguiente bloque de trabajo debería ser:

1. reforzar el escaneo con mejor clasificación y exclusiones configurables si hace falta
2. implementar importación de catálogos y matching por hash
3. añadir un inspector específico para PSX
4. construir `plan` antes de tocar cualquier archivo real

Si se quiere priorizar el caso más sensible de la colección, entonces el siguiente paso debería ser:

1. inspector de sets PSX
2. normalización de nombres PSX
3. detección de sets convertibles a futuro


## Decisiones que no deben olvidarse

- no reducir la colección a una sola región por juego
- conservar idiomas cuando estén presentes
- conservar variantes conscientes del usuario
- no tratar una biblioteca Anbernic como si fuese una carpeta limpia de ROMs
- no romper `.cue` por renombrar `.bin`
- no prometer conversión real sin herramienta externa disponible
- el frontend debe permitir elegir carpeta y preservar subcarpetas
