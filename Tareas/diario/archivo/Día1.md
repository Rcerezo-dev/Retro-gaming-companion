# ROM Manager Local

## 1. Vision del proyecto

Crear una herramienta local en Python para:

- escanear carpetas con ROMs
- identificar cada juego de forma fiable
- renombrar ROMs y saves con una convención estable
- mover los archivos a una estructura ordenada por plataforma
- guardar el estado de la biblioteca en SQLite
- poder reanudar procesos sin rehacer trabajo innecesario

El objetivo principal no es solo "renombrar archivos", sino construir una biblioteca consistente, repetible y segura.


## 2. Objetivos operativos

La herramienta debe permitir:

- procesar colecciones grandes de ROMs
- evitar renombrados incorrectos cuando haya dudas
- funcionar totalmente en local una vez preparados los catálogos
- registrar cada decisión en base de datos y logs
- ejecutar un modo vista previa antes de tocar archivos
- recuperar el estado si el proceso se interrumpe


## 3. Principios de diseño

- seguridad primero: no renombrar nada sin trazabilidad
- idempotencia: ejecutar dos veces no debe romper la biblioteca
- modularidad: escaneo, hash, matching, renombrado y catalogación separados
- prioridad a matching fiable por hash
- fallback por nombre solo cuando sea razonable
- todo cambio de archivos debe poder auditarse


## 4. Alcance funcional

### Incluido en el MVP

- escaneo recursivo de carpetas de entrada
- clasificación de archivos por tipo: `rom`, `save`, `frontend_asset`, `system_support`, `unknown`
- detección de plataforma por extensión
- cálculo de hashes `SHA1`, `MD5` y `CRC32`
- extracción del nombre base del archivo original
- matching local por hash contra catálogos preparados
- propuesta de nombre normalizado
- modo `dry-run`
- renombrado y movimiento de ROMs
- detección y renombrado de saves asociados
- almacenamiento en SQLite
- logs de operaciones y errores

### Fuera del MVP

- descarga automática de carátulas
- scraping en vivo de APIs externas
- conversión real de formatos sin herramientas externas instaladas
- deduplicación avanzada entre dumps equivalentes
- soporte perfecto para sets arcade complejos
- importación automática de colecciones comprimidas no estándar


## 5. Formato de nombre

Formato objetivo:

`Game Title [Region] (SHA1).extension`

Ejemplos:

- `Super Mario World [USA] (3A1F2E4C9A8F0D7E...).sfc`
- `Super Mario World [UNK] (3A1F2E4C9A8F0D7E...).sfc`

Reglas:

- `Game Title` debe ser el nombre canónico confirmado
- `Region` usa códigos controlados: `USA`, `EUR`, `JPN`, `WORLD`, `UNK`
- `SHA1` en mayúsculas
- conservar la extensión original en minúsculas si es posible
- sanitizar caracteres no válidos para Windows: `<>:"/\|?*`
- recortar espacios sobrantes y puntos finales

Si no hay identificación fiable:

- no se renombra automáticamente
- se marca como pendiente para revisión manual


## 6. Estructura de carpetas objetivo

Estructura propuesta:

```text
retro-library/
  incoming/
  library/
    Nintendo Entertainment System/
    Super Nintendo Entertainment System/
    Nintendo 64/
    Game Boy/
    Game Boy Color/
    Game Boy Advance/
    Nintendo DS/
    Nintendo 3DS/
    GameCube/
    Wii/
    Wii U/
    Nintendo Switch/
    Sega Master System/
    Sega Game Gear/
    Sega Genesis/
    Sega CD/
    Sega Saturn/
    Sega Dreamcast/
    PlayStation/
    PlayStation 2/
    PlayStation Portable/
    PlayStation Vita/
    Atari 2600/
    Atari 5200/
    Atari 7800/
    Atari Lynx/
    Atari Jaguar/
    Arcade/
  saves/
    <platform>/
  metadata/
    catalog/
    cache/
  database/
    library.sqlite
  logs/
```

Decision:

- las ROMs se almacenan por plataforma
- los saves van en carpeta separada por plataforma para simplificar backups y sincronización
- `incoming/` sirve como zona de importación antes de catalogar
- las bibliotecas reales pueden incluir assets y ficheros del dispositivo; no todo debe tratarse como ROM
- el usuario debe poder elegir desde interfaz qué carpeta quiere reorganizar
- la herramienta debe poder mantener subcarpetas cuando esa sea la estrategia deseada


## 6.4 Preservacion de subcarpetas

No todas las reorganizaciones deben aplanar la biblioteca.

El sistema debe soportar dos modos:

- `flatten`: reorganizar según la estructura objetivo del sistema
- `preserve_subfolders`: mantener la jerarquía relativa de subcarpetas dentro de la carpeta seleccionada

Ejemplo:

Si el usuario selecciona:

`E:\Carpetas anbernic\gb\GB official game ROM complete works`

y existe:

`E:\Carpetas anbernic\gb\GB official game ROM complete works\A\Aladdin.gb`

en modo `preserve_subfolders` el sistema debe conservar la `A` como parte de la estructura final.

Regla:

- el frontend debe permitir elegir si se mantienen subcarpetas o si se reorganiza todo a una estructura plana por plataforma


## 6.1 Bibliotecas mixtas tipo Anbernic

Una biblioteca real puede mezclar:

- ROMs
- saves
- imágenes y vídeos de frontend
- `gamelist.xml`
- BIOS
- carpetas del sistema Android o del dispositivo

Ejemplo real observado:

- carpetas de sistemas como `gb`, `famicom`, `psx`, `nds`
- metadata visual dentro de cada sistema: `downloaded_images`, `downloaded_videos`, `images`
- archivos de frontend como `gamelist.xml`
- carpetas ajenas a la biblioteca de juegos: `Android`, `BIOS`, `DCIM`, `Movies`, `Music`, `Documents`

Conclusión:

- la herramienta debe soportar bibliotecas mixtas, no solo carpetas limpias de ROMs
- el escaneo debe clasificar antes de intentar organizar


## 6.2 Clasificacion de archivos

Tipos lógicos que debe manejar el sistema:

- `rom`: juego jugable
- `save`: progreso, memoria o estado
- `frontend_asset`: imágenes, vídeos, `gamelist.xml`, logos
- `system_support`: BIOS, configuraciones, logs del dispositivo, archivos del sistema
- `unknown`: cualquier fichero que no encaje aún

Archivos que deben detectarse como `frontend_asset`:

- `.png`
- `.jpg`
- `.jpeg`
- `.mp4`
- `.xml`

Archivos o carpetas que suelen ser `system_support`:

- `BIOS`
- `Android`
- `DCIM`
- `Documents`
- `Movies`
- `Music`
- `Notifications`
- `System Volume Information`
- `backup`
- `recovery_log`


## 6.3 Exclusiones por defecto

Carpetas a excluir del escaneo de ROMs por defecto:

- `Android`
- `BIOS`
- `DCIM`
- `Documents`
- `Movies`
- `Music`
- `Notifications`
- `System Volume Information`
- `backup`
- `recovery_log`

Estas exclusiones deben ser configurables.


## 7. Plataformas soportadas

Soporte inicial recomendado:

| Plataforma | Extensiones |
|---|---|
| NES | `.nes` |
| SNES | `.sfc`, `.smc` |
| Nintendo 64 | `.n64`, `.z64`, `.v64` |
| Game Boy | `.gb` |
| Game Boy Color | `.gbc` |
| Game Boy Advance | `.gba` |
| Nintendo DS | `.nds` |
| Nintendo 3DS | `.3ds`, `.cia` |
| GameCube | `.iso`, `.gcm` |
| Wii | `.iso`, `.wbfs` |
| Wii U | `.wud`, `.wux` |
| Switch | `.nsp`, `.xci` |
| Master System | `.sms` |
| Game Gear | `.gg` |
| Mega Drive / Genesis | `.md`, `.bin`, `.gen` |
| Sega CD | `.iso`, `.cue` |
| Sega Saturn | `.iso`, `.bin`, `.cue` |
| Dreamcast | `.cdi`, `.gdi`, `.chd` |
| PlayStation | `.bin`, `.cue`, `.iso`, `.pbp`, `.chd` |
| PlayStation 2 | `.iso`, `.chd` |
| PSP | `.iso`, `.cso` |
| PS Vita | `.vpk` |
| Atari 2600 | `.a26` |
| Atari 5200 | `.a52` |
| Atari 7800 | `.a78` |
| Atari Lynx | `.lnx` |
| Atari Jaguar | `.j64`, `.jag` |
| Arcade | `.zip` |

Nota importante:

- algunas extensiones son ambiguas, especialmente `.bin`, `.iso`, `.cue`, `.zip`
- la plataforma no debe depender solo de la extensión cuando el contexto sea insuficiente
- para formatos ambiguos, conviene usar una regla combinada: extensión + carpeta + archivos compañeros


## 8. Saves soportados

Extensiones comunes:

- `.sav`
- `.srm`
- `.state`
- `.st0`
- `.st1`
- `.st2`
- `.st3`
- `.st4`
- `.st5`
- `.fcs`
- `.dsv`
- `.sps`
- `.psv`
- `.mcr`
- `.mem`
- `.vmp`
- `.eep`
- `.fla`
- `.sra`
- `.dat`

Regla de asociación:

- un save se considera asociado si comparte nombre base con la ROM original
- también debe permitirse detectar variantes comunes del emulador
- el renombrado del save debe ocurrir en la misma operación lógica que el de la ROM
- en bibliotecas reales, algunos saves viven en subcarpetas específicas del emulador
- no todos los saves deben moverse en el MVP si la relación no es fiable

Ejemplo:

- `mario.sfc`
- `mario.srm`

Resultado:

- `Super Mario World [USA] (SHA1).sfc`
- `Super Mario World [USA] (SHA1).srm`


## 9. Fuentes de metadatos

Orden de prioridad recomendado:

1. catálogos locales No-Intro
2. catálogos locales Redump
3. alias y heurísticas locales por nombre
4. integración opcional posterior con IGDB o TheGamesDB

Decisión técnica:

- el matching fiable debe hacerse por hash usando datasets locales
- las APIs externas no deben ser un requisito para el MVP
- IGDB y TheGamesDB se pueden añadir después para enriquecer metadatos, no para definir el nombre principal


## 10. Flujo de procesamiento

### Fase A. Descubrimiento

- recorrer la carpeta de entrada
- excluir carpetas del sistema configuradas
- detectar archivos candidatos a ROM
- detectar archivos candidatos a save
- detectar assets de frontend
- detectar ficheros de sistema o soporte
- registrar tamaño, fecha y ruta

### Fase B. Identificacion tecnica

- determinar plataforma probable
- calcular hashes
- normalizar nombre de archivo original
- detectar si el archivo forma parte de un set multiarchivo
- detectar si el archivo forma parte de un juego organizado por carpeta

### Fase C. Matching

- buscar coincidencia por hash en catálogos locales
- si falla, intentar heurísticas por nombre
- asignar nivel de confianza: `high`, `medium`, `low`, `none`

### Fase D. Plan de cambios

- generar nombre destino
- generar rutas destino de ROM y saves
- detectar conflictos de nombres
- validar que la operación es segura
- decidir si el elemento debe renombrarse, moverse, ignorarse o marcarse para revisión

### Fase E. Ejecucion

- mover o renombrar archivos
- actualizar base de datos
- escribir logs
- nunca tratar assets o BIOS como si fueran ROMs

### Fase F. Revision

- listar pendientes sin identificar
- listar conflictos
- listar duplicados


## 11. Reglas de seguridad

- soportar `dry-run` obligatorio antes del primer uso real
- no sobrescribir archivos existentes sin una política explícita
- si existe conflicto, marcar y continuar con el resto
- guardar siempre la ruta original
- cada operación debe registrarse en una tabla de historial
- si el matching tiene confianza baja, no renombrar automáticamente

Politicas de conflicto recomendadas:

- `skip`: no tocar el archivo
- `duplicate`: marcar como duplicado si el hash ya existe
- `suffix`: añadir sufijo temporal solo si el usuario lo permite


## 12. Duplicados y casos especiales

Casos a resolver:

- misma ROM con distinto nombre
- misma ROM en distintas carpetas
- multi-disc
- archivos `.cue` con varios `.bin`
- sets `.ccd/.img/.sub`
- sets `.mdf/.mds`
- imágenes comprimidas `.ecm`
- dumps incompletos o corruptos
- ROMs comprimidas dentro de `.zip` o `.7z`
- bibliotecas con metadata visual mezclada con juegos

Decision para el MVP:

- soportar bien archivos simples y formatos comunes
- tratar los sets multi-archivo como una segunda fase
- no modificar automáticamente archivos comprimidos no inspeccionados
- no modificar automáticamente sets PSX problemáticos o incompletos


## 13. Base de datos local

Base de datos: SQLite

### Tabla `games`

- `id`
- `canonical_title`
- `original_filename`
- `platform`
- `file_type`
- `region`
- `sha1`
- `md5`
- `crc32`
- `size_bytes`
- `source_path`
- `library_path`
- `status`
- `match_confidence`
- `catalog_source`
- `set_type`
- `parent_group`
- `year`
- `developer`
- `genre`
- `created_at`
- `updated_at`

### Tabla `saves`

- `id`
- `game_id`
- `original_path`
- `library_path`
- `extension`
- `created_at`
- `updated_at`

### Tabla `assets`

- `id`
- `platform`
- `asset_type`
- `source_path`
- `related_game_hint`
- `created_at`
- `updated_at`

### Tabla `scan_runs`

- `id`
- `started_at`
- `finished_at`
- `source_root`
- `files_seen`
- `roms_detected`
- `saves_detected`
- `errors`

### Tabla `file_operations`

- `id`
- `game_id`
- `operation_type`
- `source_path`
- `target_path`
- `result`
- `message`
- `created_at`


## 14. Arquitectura propuesta

```text
rom_manager/
  main.py
  cli.py
  config.py

  scanner/
    rom_scanner.py
    save_scanner.py
    asset_scanner.py

  hashing/
    hash_calculator.py

  detection/
    platform_detector.py
    filename_normalizer.py
    region_parser.py
    file_classifier.py
    set_detector.py

  catalog/
    catalog_loader.py
    nointro_matcher.py
    redump_matcher.py

  planner/
    operation_planner.py
    conflict_resolver.py
    psx_set_planner.py

  renamer/
    rom_renamer.py
    save_renamer.py
    cue_rewriter.py

  converters/
    converter_registry.py
    psx_converter.py

  database/
    schema.py
    repository.py

  logging/
    logger.py

  utils/
    paths.py
    text.py
```

Decision:

- separar `planner` de `renamer` evita mezclar la decision con la ejecucion
- primero se construye un plan de cambios, luego se aplica
- PSX necesita una estrategia específica por set, no un renombrado genérico de archivos sueltos


## 15. CLI propuesta

Comandos iniciales:

```bash
rommgr scan <source_path>
rommgr plan <source_path>
rommgr apply
rommgr status
rommgr unresolved
rommgr duplicates
rommgr inspect-platform psx
rommgr inspect-assets
rommgr plan <source_path> --preserve-subfolders
```

Descripcion:

- `scan`: descubre archivos y calcula hashes
- `plan`: genera la propuesta de organización sin tocar nada
- `apply`: ejecuta el último plan confirmado
- `status`: resume biblioteca, pendientes y errores
- `unresolved`: lista juegos sin identificar
- `duplicates`: lista hashes repetidos
- `inspect-platform psx`: resume formatos, sets y anomalías de PSX
- `inspect-assets`: lista assets y metadatos detectados fuera de la lógica de ROMs
- `plan --preserve-subfolders`: genera un plan manteniendo la jerarquía relativa de la carpeta elegida

Comandos posteriores:

```bash
rommgr import-catalog <catalog_path>
rommgr enrich-metadata
rommgr export-report
rommgr convert psx --tool chdman
```


## 16. Configuracion

Archivo sugerido: `config.toml`

Parametros clave:

- rutas base
- plataformas activas
- extensiones soportadas
- politica de conflictos
- politica de duplicados
- modo de movimiento o copia
- umbral minimo de confianza para auto-renombrado
- codificacion y sanitizacion de nombres
- carpetas excluidas por defecto
- estrategias por plataforma
- ruta a herramientas externas de conversión
- comportamiento por defecto respecto a subcarpetas


## 16.1 Estrategia especifica para PSX

PSX no debe tratarse como un conjunto de ROMs simples.

El sistema debe reconocer:

- juegos en carpeta propia
- archivos sueltos en la raíz
- sets `.bin + .cue`
- sets `.img + .ccd + .sub`
- sets `.mdf + .mds`
- juegos en `.pbp`
- discos múltiples
- ficheros comprimidos `.ecm`

Objetivo de organización para PSX:

```text
psx/
  Titulo [Region] [Idiomas opcional] [GameID opcional]/
    Titulo [Region] [Idiomas opcional] [GameID opcional].cue
    Titulo [Region] [Idiomas opcional] [GameID opcional] (Track 01).bin
    Titulo [Region] [Idiomas opcional] [GameID opcional] (Track 02).bin
```

Para multidisco:

```text
psx/
  Final Fantasy VII [Spain] [v1.1]/
    Final Fantasy VII [Spain] [v1.1] (Disc 1).cue
    Final Fantasy VII [Spain] [v1.1] (Disc 1).bin
    Final Fantasy VII [Spain] [v1.1] (Disc 2).cue
    Final Fantasy VII [Spain] [v1.1] (Disc 2).bin
```

Reglas PSX:

- conservar región
- conservar idiomas si aparecen
- conservar códigos `SLUS`, `SLES`, `SCUS`, `SCES` si ayudan a distinguir variantes
- unificar notación de disco a `Disc N`
- priorizar `.cue` como descriptor principal cuando exista
- si se renombra un `.bin`, hay que reescribir el `.cue`
- no tocar automáticamente sets incompletos o ambiguos

Casos que deben marcarse para revisión manual:

- nombres corruptos o sospechosos
- sets sin `.cue` claro
- ficheros `.ecm`
- ficheros temporales o de origen incierto como `NEW.*`


## 16.2 Conversión futura de formatos

La herramienta debe quedar preparada para automatizar conversiones en el futuro, aunque no formen parte del MVP inicial.

Objetivo principal para PSX:

- conversión de sets limpios a `CHD`

Reglas:

- no asumir que la conversión está disponible
- detectar si existe una herramienta externa compatible, por ejemplo `chdman`
- si no existe, generar un plan de conversión pero no ejecutarlo
- separar los sets convertibles de los problemáticos

Convertibles en una fase posterior:

- `.bin + .cue`
- `.img + .ccd + .sub`, según herramienta y validez del set
- `.mdf + .mds`, con más validaciones

No convertibles automáticamente sin pasos previos:

- `.ecm`
- sets incompletos
- nombres o referencias internas rotas


## 17. Roadmap por fases

### Fase 1. Fundacion del proyecto

- estructura del paquete Python
- configuración base
- logging
- esquema SQLite
- comandos `scan` y `status`

Resultado esperado:

- inventario local de archivos con hashes y plataforma probable

### Fase 2. Matching fiable

- cargador de catálogos locales
- matching por hash
- niveles de confianza
- almacenamiento del resultado de matching

Resultado esperado:

- el sistema identifica de forma segura una parte relevante de la colección

### Fase 3. Planificacion y renombrado

- generador de nombres destino
- detección de conflictos
- comando `plan`
- comando `apply`
- renombrado de saves asociados
- clasificación de assets y exclusiones
- estrategia específica para PSX y otros sets multiarchivo

Resultado esperado:

- biblioteca organizada sin sobrescrituras peligrosas

### Fase 4. Calidad y productividad

- reanudación incremental
- detección de duplicados
- reportes
- pruebas automatizadas
- inspección por plataforma
- validación de `.cue`

Resultado esperado:

- herramienta robusta para colecciones grandes

### Fase 5. Enriquecimiento opcional

- metadatos extendidos
- carátulas
- interfaz web local
- automatización de conversión a `CHD` cuando existan herramientas externas

Resultado esperado:

- un frontend local donde el usuario pueda seleccionar una carpeta concreta a reorganizar y decidir si quiere mantener o no sus subcarpetas


## 18. Riesgos principales

- extensiones ambiguas que llevan a una plataforma incorrecta
- catálogos incompletos o desactualizados
- archivos multi-disc difíciles de tratar como unidad lógica
- bibliotecas mixtas con assets y datos de sistema confundidos con ROMs
- diferencias entre nombre comercial y nombre del dump
- conflictos con saves generados por múltiples emuladores
- costes de hash en archivos muy grandes
- sets PSX rotos por renombrar `.bin` sin corregir `.cue`
- conversiones de formato dependientes de herramientas externas no instaladas

Mitigaciones:

- priorizar hash sobre nombre
- no ejecutar renombrado automático con baja confianza
- registrar siempre el origen y el motivo de cada decisión
- cubrir con tests las reglas de sanitización y conflictos
- clasificar antes de actuar
- tratar PSX por sets y no por archivos aislados


## 19. Criterios de exito del MVP

El MVP se considera listo si:

- escanea una carpeta recursivamente
- clasifica correctamente ROMs, saves, assets y soporte de sistema
- detecta ROMs y saves comunes
- calcula `SHA1`, `MD5` y `CRC32`
- identifica por hash usando un catálogo local
- genera un plan seguro de cambios
- renombra y mueve archivos sin sobrescribir
- registra la operación en SQLite y logs
- deja aparte los casos no resueltos para revisión manual
- no intenta reorganizar automáticamente BIOS, assets o sets PSX dudosos


## 19.1 Criterios de exito del frontend futuro

El frontend se considera válido si:

- permite seleccionar una carpeta concreta del disco
- muestra una vista previa del plan de cambios
- permite activar o desactivar la preservación de subcarpetas
- deja claro qué archivos se van a mover, renombrar, ignorar o marcar
- no ejecuta cambios sin confirmación explícita


## 20. Orden recomendado de implementacion

1. `config`, `logging` y `database`
2. `scanner` y `hashing`
3. clasificador de archivos y exclusiones
4. `platform_detector` y normalización de nombres
5. `catalog_loader` y matching por hash
6. `operation_planner`
7. `renamer`
8. soporte de saves
9. estrategia PSX por sets
10. comandos de revisión y reportes


## 21. Siguiente paso practico

La mejor siguiente tarea no es empezar por APIs externas.

La mejor siguiente tarea es construir un MVP con este flujo:

1. `scan` una carpeta
2. clasificar cada archivo por tipo
3. guardar hashes y estructura en SQLite
4. cargar un catálogo local mínimo
5. resolver títulos por hash
6. generar `plan`
7. ejecutar `apply` en modo seguro

Si esta base funciona bien, el resto del proyecto se vuelve una extensión natural y no un sistema frágil.
