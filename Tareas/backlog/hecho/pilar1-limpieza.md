# Hecho — Pilar 1 — Limpieza y organización inicial de la biblioteca — → #202

> Secciones ✅ de `Tareas/backlog/pilar1-limpieza.md` (todas sus tareas cerradas). Referencia.

### ARCADE-DAT-CONTAMINATION — DATs de consola mezclados en el catálogo arcade causan falsos positivos (hallazgo real 2026-09-02, BLOQUEANTE)

**BUG DE SEVERIDAD ALTA** — descubierto en vivo durante un piloto de `organize-source` contra
`H:\ROMs\amiga`, con datos reales movidos por error (revertido en el momento, sin pérdida).

Causa raíz: `.rommgr/catalogs/arcade/` contiene, junto a los DAT arcade legítimos (MAME,
"FinalBurn Neo (ClrMame Pro XML, Arcade only).dat"), **15 DAT de FBNeo que son núcleos de
CONSOLA, no arcade**: `FDS`, `Game Gear`, `Master System`, `SNES`, `Megadrive`, `NES`,
`PC-Engine`, `ColecoVision`, `Fairchild Channel F`, `MSX 1`, `NeoGeo Pocket`, `Neogeo`,
`SG-1000`, `SuprGrafx`, `TurboGrafx16`, `ZX Spectrum` — nombrados "(ClrMame Pro XML, X only)"
pero viviendo en la carpeta `arcade/`, probablemente descargados junto a los DAT arcade sin
reparar en que FBNeo también emula consolas.

`load_arcade_crc_index()` (`catalog/mame_loader.py:122-150`) lee **todos** los `.dat` de ese
directorio sin distinguir sistema — indexa cada CRC de cada DAT en un único diccionario
`crc32 -> {set names}`. `_is_arcade_zip_container()` (`web/inbox_pipeline.py:429-445`), usado por
el paso 1 del pipeline de Inbox/organize-source para decidir "esto es un set MAME completo, no
extraer, mover a `arcade/`", solo comprueba si el CRC de cada entrada del ZIP está en ese índice
contaminado — sin verificar de qué DAT viene.

**Reproducido en real**: `organize-source "H:\ROMs\amiga" --apply` movió 23 ZIPs a `arcade/`.
Inspeccionados uno a uno (contenido real del ZIP, no el nombre):
- **4 sí son arcade de verdad** (`batman.zip`, `Hook (Europe)...zip`, `legend.zip`,
  `Batman (Europe) (Budget - The Hit Squad) (conflicto-inbox 2026-08-13).zip` — sets multi-chip
  MAME reales) — correctamente en `arcade/`.
- **19 NO son arcade ni Amiga** — son ROMs de SNES (`.sfc`), Genesis (`.md`) y Master System
  (`.sms`)/PC Engine (`.pce`) con nombre "estilo Amiga" que mentía sobre el contenido real
  (`Aladdin (Europe) (AGA).zip` contenía literalmente `Aladdin (USA).sfc`). Revertidos a mano de
  vuelta a `amiga/` — **siguen mal ubicados ahí** (su plataforma real es SNES/Genesis/SMS/PCE, no
  Amiga), pendientes de mover a su carpeta correcta una vez ADT-2 esté resuelto.

**Por qué era bloqueante**: `Game Gear`, `Famicom Disk System` y `Master System` — 3 de los 4
huérfanos pendientes de `LIBRARY-AUDIT-6`/`ANBERNIC-ROMTREE` en `H:\ROMs` — son exactamente
plataformas cuyo DAT contaminaba el índice. **Resuelto 2026-09-02** (ARCADE-DAT-CONTAMINATION-1 y
-2): ya es seguro volver a ejecutar `organize-source`/Inbox contra cualquier carpeta.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ARCADE-DAT-CONTAMINATION-1 | **Hecho**: los 16 DAT de núcleos de consola (Neogeo y NeoGeo Pocket contados aparte) movidos de `.rommgr/catalogs/arcade/` a `.rommgr/catalogs/_fbneo_console_unused/` — dato local, no versionado (`.rommgr/catalogs/*` está en `.gitignore`), sin commit necesario para esta parte | `.rommgr/catalogs/arcade/*.dat` | ✅ 2026-09-02 |
| ARCADE-DAT-CONTAMINATION-2 | **Hecho**: `_is_console_only_dat()` nuevo filtra por nombre de fichero (`"...only)"` que no sea `"Arcade only)"`) en ambos bucles de `load_arcade_crc_index()`/`load_arcade_manifest()` — defensa en profundidad aunque el directorio vuelva a contaminarse. Verificado contra los ficheros reales que causaron el fallo (`Aladdin (Europe) (AGA).zip` ya no vota como arcade, `batman.zip` sigue detectándose bien). Tests: `test_arcade_crc_index_ignores_console_only_fbneo_dats`, `test_arcade_manifest_ignores_console_only_fbneo_dats` | `catalog/mame_loader.py:122-193` | ✅ (`fix/arcade-dat-contamination`) |
| ARCADE-DAT-CONTAMINATION-3 | **Hecho 2026-09-02**: los 19 ZIPs aislados en una carpeta temporal fuera de `amiga/` (para no sesgar la detección por ruta) y pasados por `organize-source --apply` — 8 a `snes/`, 2 a `mastersystem/`, 2 a `pcengine/`, 7 resultaron ser duplicados exactos de Genesis ya presente en `megadrive/` (descartados de forma segura a `megadrive/_descartados/`, nunca borrados). 0 falsos positivos de arcade. Verificado archivo por archivo contra el log real (el contador "Organizados: 31" del comando no cuadraba con los 19 originales — investigado y confirmado que no hay pérdida: son operaciones internas del pipeline, no archivos perdidos) | `H:\ROMs\amiga\` → `snes/`, `mastersystem/`, `pcengine/`, `megadrive/_descartados/` | ✅ 2026-09-02 |
| ARCADE-DAT-CONTAMINATION-4 | **Auditoría hecha 2026-09-02** (heurística: ZIPs de 1 sola entrada con extensión de consola no ambigua, sobre las carpetas `arcade/` de ambas bibliotecas — el sitio con más exposición histórica al bug). `H:\ROMs\arcade`: 1.372 ZIPs revisados, **0 sospechosos**. `E:\Carpetas anbernic\arcade`: 15.952 ZIPs revisados, **706 sospechosos** (661 NES, 17 SNES, 14 Nintendo 64DD, 5 Master System, 4 PC Engine, 3 Famicom Disk System, 2 Commodore 64). **47 de los 706 resultaron ser falsos positivos de la propia heurística de investigación** (no de la app): chips arcade reales nombrados con sufijo de socket tipo `.u1`/`.prg` que coincide por casualidad con extensión de N64DD/Commodore 64/NES — el pipeline real (CRC de verdad, ya con el fix) los identificó correctamente como arcade y los dejó donde estaban, confirmando que el fix funciona bien incluso con nombres engañosos. Los ~659 restantes eran genuinos, nombres estilo No-Intro/Goodtools sin mentir sobre el contenido (a diferencia de los de `amiga/`). **672 de los 706 originales tienen fecha de modificación 2026-08-28/29** (semanas antes de esta sesión) — confirma que el bug llevaba tiempo afectando también al Inbox del día a día (`zip_router.py` usa el mismo `load_arcade_crc_index()` contaminado, no solo `organize-source`), 9 del 2026-09-01. Sin auditar aún el resto de carpetas de ambas bibliotecas más allá de `arcade/` y `amiga/` | `E:\Carpetas anbernic\arcade\` | ✅ auditoría |
| ARCADE-DAT-CONTAMINATION-5 | **Hecho 2026-09-02**: los 706 aislados en carpeta temporal fuera de `arcade/` y pasados por `organize-source --apply`. Resultado real (verificado contra el log completo, no solo el resumen): **293 organizados** a su plataforma real, **753 duplicados exactos** descartados de forma segura (`_same_content()` verificado antes de descartar — quedan recuperables en `_ARCADE_CONFLICTOS_REVISAR_MANO/_descartados/`), **47 vueltos a `arcade/`** correctamente (ver -4, falsos positivos de mi heurística), **240 conflictos de nombre** (mismo nombre en destino, contenido distinto — no se tocan, dejados intactos para revisión manual). Carpeta temporal renombrada a `_ARCADE_CONFLICTOS_REVISAR_MANO` para que quede visible, sin borrar nada — sigue conteniendo los 240 conflictos + los duplicados descartados. 0 pérdida de datos | `E:\Carpetas anbernic\arcade\` → `nes/`, `snes/`, etc. + `_ARCADE_CONFLICTOS_REVISAR_MANO/` | ✅ 2026-09-02 |
| ARCADE-DAT-CONTAMINATION-6 | **✅ Resuelto 2026-09-04** (con confirmación del usuario). De los 232 ficheros en el nivel superior (240 nominales, 8 ya en `_processed/`): **64 `.zip`** resultaron NO ser arcade en absoluto — son ROMs NES/FDS de dump Goodtools (`[!]`) que por casualidad comparten nombre de fichero con un set MAME de `arcade/` (coincidencia de título entre plataformas, no contaminación). De esos 64: 10 con CRC de entrada idéntico a un `.zip` ya en `nes/`/`fds/` (duplicado exacto), y **54 verificados por `normalize_for_match()` contra toda la biblioteca — el mismo título ya existe** (casi siempre el mismo nombre+región exacto como `.nes` suelto, ej. `Donkey Kong (USA).zip` → `nes\Donkey Kong (USA).nes`). Los **168 no-`.zip` restantes** (`.nes`/`.fds`) verificados con el mismo método: **168/168 también tienen contraparte por título ya en la biblioteca**. **Resultado: 232/232 (100%) son redundantes**, ninguno resultó ser contenido nuevo. Movidos a `_ARCADE_CONFLICTOS_REVISAR_MANO\_descartados\` (ya existía esa subcarpeta desde `ARCADE-DAT-CONTAMINATION-5`, mismo criterio — nunca borrados, recuperables). `rommgr scan` de refresco: 232 huérfanos limpiados. Scripts de sesión, no versionados (candidato a `REPAIR-TOOL-8`/nuevo comando de "detectar redundante por título" reutilizando `normalize_for_match()`) | `E:\Carpetas anbernic\_ARCADE_CONFLICTOS_REVISAR_MANO\` | ✅ 232/232 descartados a `_descartados/`, 0 contenido nuevo encontrado |
| ARCADE-DAT-CONTAMINATION-7 | **Hecho 2026-09-03**: hallazgo de `DECOMPRESS-ARCADE-GAP-4` — 190 ZIPs intactos + 203 carpetas de residuo suelto (206 detectadas, 3 resultaron ser la raíz completa de `atari5200/`/`intellivision/`/`wonderswan/` — no se aislaron enteras, solo los 57 ficheros sueltos individuales que votaban arcade en esa raíz, para no arrastrar contenido legítimo) aislados en `E:\Carpetas anbernic\_ARCADE_MISFILED_STAGING\` (fuera de `Unknown/`, ver -8) y pasados por `organize-source --apply`: **190/190 ZIPs reclasificados** a `arcade/` sin incidentes (incluye `psx__Raystorm (Japan).zip` — confirma la corrección de `DECOMPRESS-ARCADE-GAP-1` de que el set base `raystorm` sí existe, solo estaba mal etiquetado), 26 conflictos de nombre sin resolver (ficheros sueltos tipo `1.bin`/`7.bin` con nombre duplicado en destino). Los residuos sueltos (`organize-source` no los reconoce — solo detecta arcade por CRC en ZIPs intactos, no en ficheros sueltos) se resolvieron en 2 pasadas con scripts de sesión: (1) 134/242 items con backup 100% íntegro en un único ZIP de `arcade/` → descartados a papelera; 26 carpetas vacías (residuo del propio aislamiento) → eliminadas tras confirmar que no tenían contenido. (2) Los 82 restantes, diagnosticados contra el DAT primario (`MAME 0.286`) con herencia `romof`/`cloneof` real, no solo comparación 1:1 de ZIP: **2 recuperados de verdad** (`grobda`, `sonson` — Wii Virtual Console, sets completos que nunca habían llegado a `arcade/`, re-empaquetados y movidos), **45 descartados** (confirmado que `arcade/` YA los cubre al 100% sin depender del residuo — split-set de MAME, chips compartidos con el padre/otro clon ya presentes). **Quedan 35 sin tocar** — **diagnóstico fino completado 2026-09-03** (sesión aparte, solo lectura: parseo completo del DAT primario con cadena `romof` resuelta hasta la raíz + CRC real de `arcade/` leído de cabecera de ZIP sin descomprimir, 16.101 ZIPs, 70.697 CRCs únicos). Los "6 sin nombre reconocido" bajan a **2**: los 3 `wii__*` usan el título del juego en vez del nombre de set MAME en el nombre de carpeta — 2 no calzaban por nombre literal (`Chelnov (Japan)...`, `Ironclad (USA)...`), identificados por votación de CRC de contenido real contra el índice del DAT primario (`chelnov`: 19/19 ficheros coinciden exacto, `ironclad`: 8/9); el tercero (`chelnovjbl`) ya llevaba el nombre de set correcto. Categorización final de los 35 (mismo criterio que los 47 ya resueltos: solo descartable si `arcade/` por sí solo, sin el residuo, ya cubre el 100% del set exigido por el DAT con herencia `romof`):
- **6 descartables** (`arcade/` ya cubre el 100% sin el residuo): `commandoj`, `firetrapbl`, `rastsagaa`, `springbd`, `chelnov` (identificado por CRC, `wii__Chelnov (Japan)...`) — 5/5 con `covered_by_arcade_alone=True` confirmado.
- **1 caso límite, NO descartado bajo el criterio estricto**: `ironclad` (`wii__Ironclad (USA)...`) — el residuo no aporta ningún chip único (0 de sus 9 ficheros son necesarios-y-ausentes-de-otro-sitio), pero el set completo sigue incompleto en toda la biblioteca (faltan 6 chips en cualquier parte) — `arcade/` solo no llega al 100%, así que no cumple el criterio estricto pese a que borrarlo no perdería nada real. Decisión pendiente del usuario: ¿aplicar aquí el mismo criterio de "sin aporte único = descartable" o tratarlo aparte?
- **15 recuperables por combinación** (residuo aporta chip(s) únicos + `arcade/` ya tiene el resto → juntos llegan al 100% del set exigido, mismo patrón que `grobda`/`sonson` pero sin ser autosuficientes solos — necesitan re-empaquetar combinando con chips ya existentes en el ZIP de `arcade/`): `badlandsb` (15/35 chips únicos), `eswatbl2` (38/53), `pangba` (16/25), `carnivalca` (15/35), `carnivalh` (8/29), `carnivalmm` (1/24), `popeyeb2` (1/25), `blasterkit` (8/29), `hydrap2` (9/51), `hustlerb2` (2/11), `hustlerb3` (2/11), `hustlerb4` (6/16), `hustlerb6` (3/12), `hustlerd` (3/11), `cadashso` (4/16).
- **14 realmente incompletos en toda la biblioteca** (ni el residuo ni `arcade/` juntos llegan al 100% exigido por el DAT — mismo patrón que `raystormj/o/u`, no recuperables sin re-descargar el chip que falta): `badlandsm` (falta 1 chip), `betafrce` (6), `pangbc` (15), `spinner` (13), `venture4` (8), `venture5a` (8), `venture5b` (15), `clowns1` (6), `starfirea` (11), `bsebman` (8), `bsebmanbl2` (8), `exerionb2` (6), `exerionba` (10), `chelnovjbl` (2).

Nada tocado en disco — solo lectura. Ver `ARCADE-DAT-CONTAMINATION-10` para ejecutar las 4 acciones derivadas | `E:\Carpetas anbernic\_ARCADE_MISFILED_STAGING\` | ✅ mayormente resuelto (277/312 items); 🟡 diagnóstico de los 35 restantes completo, ejecución pendiente (`ARCADE-DAT-CONTAMINATION-10`) |
| ARCADE-DAT-CONTAMINATION-10 | **✅ Hecho 2026-09-03** (confirmación del usuario "hazlas todas"), acciones 1-3 ejecutadas con script de sesión (solo lectura hasta el momento de escribir, verificación de CRC antes y después de cada escritura, nunca sobreescribe un ZIP existente): **(1) 6 descartados** — `commandoj`, `firetrapbl`, `rastsagaa`, `springbd`, `chelnov` (criterio estricto original) + `ironclad` (criterio ampliado: 0 aporte único, aunque el set siga incompleto en el resto de la biblioteca — tratado igual con el "sí, todas" del usuario) — movidos a `_ARCADE_MISFILED_STAGING\_descartados\` (papelera, recuperable, nunca borrados). **(2) 15 re-empaquetados**: para cada set, ZIP nuevo en `arcade/` combinando los chips únicos del residuo + los chips ya existentes en algún ZIP de `arcade/` (extraídos de su fuente real, sin descomprimir a disco), con el nombre interno exacto que exige el DAT — `badlandsb.zip` (35 roms: 15+20), `eswatbl2.zip` (53: 38+15), `pangba.zip` (25: 16+9), `carnivalca.zip` (35: 16+19), `carnivalh.zip` (29: 9+20), `carnivalmm.zip` (24: 4+20), `popeyeb2.zip` (25: 11+14), `blasterkit.zip` (29: 8+21), `hydrap2.zip` (51: 9+42), `hustlerb2.zip` (11: 2+9), `hustlerb3.zip` (11: 3+8), `hustlerb4.zip` (16: 8+8), `hustlerb6.zip` (12: 3+9), `hustlerd.zip` (11: 3+8), `cadashso.zip` (16: 4+12) — los 15 verificados íntegros (`zipfile.testzip()` sin corrupción) tras escribir, residuo original movido a `_descartados/` en cada caso. **(3) 14 aparcados** en `_ARCADE_MISFILED_STAGING\_incompletos_pendiente_redescarga\` (sin tocar contenido, solo reubicados para que el estado quede visible — mismo patrón que `raystormj/o/u`, ninguno recuperable sin re-descargar el chip que falta en toda la biblioteca): `badlandsm`, `betafrce`, `pangbc`, `spinner`, `venture4`, `venture5a`, `venture5b`, `clowns1`, `starfirea`, `bsebman`, `bsebmanbl2`, `exerionb2`, `exerionba`, `chelnovjbl`. `rommgr scan` de refresco: 100.909 archivos, 0 errores, 16 huérfanos limpiados. **(4) `H:\ROMs` sin ejecutar** — disco no montado en esta sesión (solo `C:`, `D:`, `E:`), queda igual que `ARCADE-DAT-CONTAMINATION-9` | `E:\Carpetas anbernic\_ARCADE_MISFILED_STAGING\`, `E:\Carpetas anbernic\arcade\` | 🟢 E: hecho (1-3), 🔴 H: pendiente (disco no conectado, ver -9) |
| ARCADE-DAT-CONTAMINATION-8 | **Diagnosticado 2026-09-08 — causa raíz confirmada**: `Unknown/` (11.090 items en la raíz + subcarpetas tipo `cprogolf18/`, `geminib/`, `MAME/`, `games/`, `roms 1/`... con chips arcade sueltos ya descomprimidos) no es una bandeja gestionada por ningún paso del pipeline — es solo un nombre de carpeta fuera de `_RECOGNIZED_PLATFORM_FOLDERS` (`web/builders/folders.py:33-35`), mismo caso que `_ARCADE_MISFILED_STAGING`/`_ARCADE_CONFLICTOS_REVISAR_MANO` antes de que `ARCADE-DAT-CONTAMINATION-5/7/9/10` corrieran `organize-source --apply` sobre ellas: nadie lo había ejecutado nunca contra `Unknown/`. `rommgr organize-source "E:\Carpetas anbernic\Unknown"` (dry-run, dato real) confirma que el pipeline ya sabe clasificar casi todo: de los archivos recorridos, **19.483 se organizarían** — `MAME` 8.605, `Arcade` 2.419, `FBNeo` 839 (11.863 arcade en total, más que los 3.039 *ZIPs* con voto mayoritario del hallazgo original porque el dry-run cuenta también los chips sueltos ya descomprimidos dentro de las subcarpetas tipo `cprogolf18/`, no solo ZIPs intactos), `Sega Mega Drive` 2.390, `NES` 1.002, `Game Gear` 490, y 16 plataformas más con volumen menor. **3.503 quedan `(sin identificar)`** — se quedan donde están, el pipeline nunca mueve algo sin match. **Aplicado 2026-09-08** (confirmación del usuario): `organize-source --apply` real sobre `Unknown/`. Resultado: **3.631 organizados** (movidos a su plataforma real), **15.750 duplicados exactos descartados** (ya existían en destino, soft-discard a `_descartados/`, recuperables — la mayor parte de lo que parecía "biblioteca por organizar" era en realidad una copia redundante ya existente), **3.648 conflictos sin resolver** (mismo nombre, contenido distinto — no se tocan, quedan para revisión manual, ejemplos: varios ZIPs arcade con hash distinto al ya presente en `arcade/`). Quedan 81.058 archivos en el origen (conflictos + no identificados + no-ROM). Rescan completo de la biblioteca tras aplicar (593 ROMs nuevos, 332 registros huérfanos podados).

**Conflictos resueltos 2026-09-09** (vía `find_organize_conflicts`/`_resolve_organize_conflict`, `force_keep`, solo lectura previa + backup de `library_pc.db` en `.rommgr/backup_arcade_dat_contamination8_conflicts_20260909/`): re-medidos en vivo, **3.589** conflictos reales (leve deriva desde el 08-09, ninguno con datos de RA en ningún lado — 0/3.589, el criterio habitual de prioridad RA no aplicaba). Agrupados por casuística y decididos por el usuario: **Arcade+MAME** (3.155, 88% — mayoría con tamaño muy distinto entre origen/destino, patrón de romsets MAME de versión distinta, ej. `bagman.zip` 23 KB vs 188 KB) → criterio "el archivo más grande gana"; **NES** (329 — 280 con tamaño exacto igual pero hash distinto, más compatible con header iNES/revisión que con versión de romset) → gana siempre lo ya organizado; **Resto** (105, 17 plataformas) → mismo criterio que Arcade. Aplicado: **544** ganó Unknown/ (reemplazó lo organizado, con soft-discard del perdedor a `_descartados/`), **2.896** ganó lo ya organizado (Unknown/ descartado a papelera), **145** empatados en tamaño exacto sin criterio aplicable → sin tocar, quedan para revisión manual caso a caso. 4 entradas duplicadas en el listado (mismo archivo aparecía dos veces) se saltaron sin dejar estado a medias — verificado con re-consulta tras aplicar (145 conflictos restantes, cuadra exacto con los empates) | `E:\Carpetas anbernic\Unknown\` | ✅ aplicado y verificado 2026-09-08/09 — los empates de tamaño exacto quedaron resueltos el 2026-09-09, ver `ARCADE-DAT-CONTAMINATION-12` |
| ARCADE-DAT-CONTAMINATION-12 | **Re-medición 2026-09-09 de los 145 empates pendientes — deriva y hallazgo nuevo.** `find_organize_conflicts()` en vivo ya no da 145: da **168** (109 con tamaño distinto + 59 empatados en tamaño exacto — composición distinta a ayer, deriva esperable tras cada rescan/organize). Al investigar por qué tantos casos "con tamaño distinto" seguían sin resolverse pese al criterio ya aprobado ("el más grande gana"), se encontró la causa: `_same_content()` (`web/inbox_pipeline.py:23-37`) compara SHA1 del ZIP completo (bytes crudos), no el CRC32 de cada entrada interna — así que dos ZIPs con **exactamente el mismo contenido de ROM pero re-empaquetados con otra herramienta/timestamp** (mismo patrón que el ZIP-ROUTE ya documentado para el resto de la app: "el header del ZIP ya trae el CRC32 de cada entrada, el contenido manda, no los bytes del contenedor") se marcan como "conflicto" cuando no lo son. Verificado abriendo cada `.zip` de los 168 con `zipfile` y comparando `{(nombre, CRC) por entrada}`: **90 de 168 (54%) son 100% idénticos por CRC interno** — falsos positivos puros, ninguna pérdida posible al quedarse con cualquiera de los dos. Solo **78 tienen contenido realmente distinto** (39 `.zip` con CRC interno distinto + 39 no-zip donde la comparación de bytes ya era correcta, todos con tamaño exacto igual — mismo patrón "header/revisión" que el bloque NES original de `ARCADE-DAT-CONTAMINATION-8`: `Sega Mega Drive` 32, `Nintendo 64DD` 5, `Famicom Disk System` 1, `Game Gear` 1). **Aplicado 2026-09-09** (confirmación del usuario, backup previo en `.rommgr/backup_arcade_dat_contamination12_20260909/library_pc.db`), criterio: CRC interno idéntico → gana lo ya organizado (sin riesgo, contenido probado idéntico); `NES` → gana siempre lo ya organizado (mismo criterio ya aprobado en `ARCADE-DAT-CONTAMINATION-8`); tamaño distinto (resto de plataformas) → gana el más grande; tamaño igual y contenido realmente distinto, no-NES → gana lo ya organizado por defecto (mismo criterio que NES, extendido por consistencia — ningún criterio de tamaño puede desempatar cuando literalmente son iguales). Resultado: **160 `kept_dest`** (90 CRC-idénticos + 5 NES + 52 empates no-NES + 13 del criterio de tamaño), **8 `kept_source`** (tamaño distinto, ganó Unknown/), **0 errores**. Re-consulta tras aplicar: **0 conflictos restantes** en `Unknown/` | `web/inbox_pipeline.py:23-37` (`_same_content`, sin arreglar — el bug de raíz sigue ahí para el próximo lote de conflictos), script de sesión no versionado | ✅ los 168 conflictos de hoy resueltos y verificados (0 restantes); 🔵 `_same_content()` documentado como causa raíz pero sin arreglar (afectaría también a la detección de conflictos genérica, no solo arcade) |
| ARCADE-DAT-CONTAMINATION-11 | **Pregunta abierta desde `Día51` resuelta 2026-09-04**: "¿fusionar `mame/`/`fbneo/`/`cps1-3/` con `arcade/`, o dejarlos separados?" — ya no aplica, el pipeline ya unificó todos los ROMs en `arcade/` sin que nadie lo decidiera explícitamente (`E:` 16.491 archivos en `arcade/` vs 25/1/77/96/26 en `mame/fbneo/cps1/cps2/cps3`; `H:` 11.045 vs 24/0/7/19/1). Verificado el contenido de las carpetas viejas: **0 ROMs**, solo saves (`.nv`/`.hi`/`.fs`), configs de mando (`.cfg`) y media de scraper — residuo de antes de la unificación. **Hallazgo real derivado**: el sync SÍ cubre esos saves hoy (`sync.sources` "RetroArch" apunta a la biblioteca entera, `sync_saves()` hace `rglob` recursivo filtrando solo por extensión — da igual la carpeta), pero **`.fs` (savestate de FBNeo para CPS3: `sfiii3.fs`, `redearth.fs`, `jojoba.fs`, `sfiii2.fs`) no estaba en `save_extensions` ni `state_extensions`** (`config.py`) — nunca se subía/bajaba. **Arreglado en la misma sesión** (fix de una línea, causa raíz clara): `.fs` añadido a `state_extensions` (`config.py:591-594`). 1157/1157 tests en verde, ruff limpio. `.cfg` (remap de mando, no progreso de partida) queda fuera a propósito, no es un gap | `config.py:591-594` | ✅ pregunta cerrada + gap `.fs` arreglado |
| ARCADE-DAT-CONTAMINATION-9 | **✅ Hecho 2026-09-04** (lector SD conectado). Auditoría de solo lectura (script de sesión, reutiliza `is_arcade_zip_container()` ya versionada — `DECOMPRESS-ARCADE-GAP-3` — en vez de reimplementar el voto CRC): **562 ZIPs fuera de `arcade/`** revisados, **118 con TODAS las entradas votando arcade**, 0 corruptos. **Hallazgo antes de tocar nada**: 89 de los 118 ya vivían dentro de `_descartados/` de su plataforma (basura ya perdedora del dedup, ej. `amiga\_descartados\Badlands (Europe).zip`) — no son contenido activo, se dejaron intactos en su sitio (no se "revive" basura). Solo **29 estaban en uso real** (sirviéndose desde la carpeta de plataforma). Aislados en `H:\ROMs\_ARCADE_MISFILED_STAGING\` y pasados por `organize-source --apply`: **19 movidos** directo a `arcade/` (set completo, sin extraer), **10 ya existían en `arcade/`** con ese nombre — de esos, 2 (`Phoenix`, `Pooyan`) el propio pipeline los descartó bien (SHA1 exacto ya conocido), pero **8 quedaron mal**: el resto del pipeline (scan+match+organize tras el paso de ruteo arcade) los reclasificó de vuelta a su carpeta de consola original en vez de descartarlos — bug de proceso, no de los datos (mismo contenido por CRC de entrada, SHA1 de archivo distinto por empaquetado/compresión, así que el dedup por SHA1 exacto no los pilla). Verificado 1 a 1 (SHA1 de cada par `arcade/` vs `consola/`, todos `DIFFERENT` a nivel de archivo pero coinciden en contenido por CRC) y movidos a mano a `_descartados/` de su plataforma (`atari2600`×3, `atari7800`×1, `atarilynx`×2, `c64`×2). `rommgr scan` de refresco sobre `H:\ROMs` completo: 27.068 archivos, 0 errores, 29 huérfanos limpiados. **Hallazgo de proceso para ARCADE-DAT-CONTAMINATION-10-like runs futuros**: cuando `organize-source` encuentra un ZIP arcade que "ya existe" en destino, el archivo se queda en el origen y el resto del pipeline lo reclasifica por plataforma de carpeta en vez de descartarlo — revisar a mano el resultado de cada "ya existe" (WARNING en el log) antes de dar la tarea por cerrada | `H:\ROMs\` | ✅ 118/118 procesados (89 basura ya descartada sin tocar, 29 activos reclasificados a `arcade/` o `_descartados/`) |

---

### ARCADE-SETUP — Research arcade ROM config (no code)

| ID | Task | Notes |
|----|------|-------|
| ARCADE-SETUP-1 | Research MAME vs FBNeo ROM set version compatible with Anbernic RG556 RetroArch | ✅ `docs/arcade-setup.md` §1 — FBNeo primera opción, MAME 2003 Plus segunda |
| ARCADE-SETUP-2 | Identify target arcade systems and map each to the correct RetroArch core | ✅ `docs/arcade-setup.md` §2 — tabla sistema→core→ROM set |
| ARCADE-SETUP-3 | Document config additions: `config.toml`, library-structure, DAT sources for arcade | `docs/arcade-setup.md` ✅ + descarga de DATs arcade cableada (runtime: `_run_dat_download` en `web/handlers/scan.py` + `scan.js`; installer: `catalog/dat_downloader.py` vía `installer/download_dats.py`) |
| ARCADE-SETUP-4 | Test a sample ROM end-to-end: scan → rename → launch on device | Hardware test |

---

### DEDUP-RENAME — Colisiones de nombre en Organizar: sufijo _1/_2 en vez de borrar (feedback usuario 2026-08-29)

Origen: `docs/ideas/Idea_final.md` + `docs/Feedback/29/8.md` — el usuario reporta que,
cuando dos juegos piden el mismo nombre canónico, Organizar les añade sufijo `_1`/`_2`
en vez de quedarse con uno solo. Pide el mismo criterio que ya usa el resto de la app
para duplicados: conservar la versión con logros en RetroAchievements y descartar
la otra (patrón ya implementado en `ra_duplicates_service.py`/`apply_ra_conflicts`,
ver TABS-FIX-2/DUP-RA-COLLISION-1 en `archivo.md`). No investigado a fondo todavía —
puede ser que el flujo de colisión simple (mismo `canonical_title`, sin ser sets
multi-disco) nunca llegue a pasar por `apply_ra_conflicts`, a diferencia de los
casos `disk`/`collision` que sí lo hacen.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DEDUP-RENAME-1 | Investigar por qué una colisión de nombre simple (no multi-disco) en Organizar termina en sufijo `_1`/`_2` en vez de resolverse por RA — confirmar con archivo:línea si pasa por `collision_resolver`/`apply_ra_conflicts` o por una ruta distinta sin ese criterio. No arreglar en la misma sesión, documentar hallazgo | `planner/collision_resolver.py`, `services/ra_duplicates_service.py` | ✅ **investigado 2026-08-29 — no es un bug, el sufijo es una acción manual explícita, no automática**. `collision_resolver.resolve()` (`planner/collision_resolver.py:44-46`) por defecto (`keep_both=False`) marca las colisiones `status='conflict'` — **no** las renombra ni les pone sufijo; `_do_apply` (`web/handlers/organize.py:111,123`) llama a `build_plan(..., keep_both=keep_both)` con `keep_both` sacado del body de la request, `False` por defecto. El sufijo `_1`/`_2` solo se aplica si el usuario pulsa el botón explícito **"Renombrar (añadir sufijo _1 _2)"** (`organize.js:164` → `applyKeepBoth()`, `organize.js:285-303`, que confirma con un modal propio y manda `keep_both:true`) — un escape hatch a propósito para "quiero quedarme con ambas copias", no el camino por defecto. El camino RA ya existe en el mismo panel de colisiones, sin tener que ir a otro sitio: si hay datos de RA para el título (`hasRaData`, `organize.js:157`), la tabla ya muestra "✓ Ganador RA" / "→ _descartados/" por fila (`organize.js:167-190`) y el texto de ayuda dirige a "2. Revisar copias" (`organize.js:165`) para aplicarlo. Conclusión: si el usuario ve sufijo `_1`/`_2` es porque (a) pulsó ese botón a propósito, o (b) no había caché de RA para esa plataforma/hash (`hasRaData=false`) y por tanto no hay señal con la que decidir un ganador — comportamiento correcto, no un fallo de `apply_ra_conflicts`. Nada que arreglar en el mecanismo; si el usuario confirma que fue (b), el hueco real sería de cobertura de caché RA (relacionado con SAGE-1), no de esta lógica |
| DEDUP-RENAME-2 | **El usuario no encuentra cómo aplicar la función de duplicados a la Anbernic** (feedback 2026-08-29, aclarado tras TABS-FIX-6 archivar la pestaña Duplicados en favor de "Revisar copias" dentro de Organizar). `DEVSEL-FIX-1` (`archivo.md`) dice que las acciones de duplicados ya enrutan por dispositivo — investigar si "Revisar copias" realmente expone/filtra por Anbernic en la UI actual o si el selector de dispositivo lo oculta; confirmar con archivo:línea antes de arreglar | `web/builders/duplicates.py` (`_build_review_queue`), `web/static/js/tabs/review_copies.js` | ✅ **investigado 2026-09-07 — no es un bug de filtrado: "Revisar copias" ya incluye los duplicados de la Anbernic automáticamente, sin selector que los oculte; la confusión probable es de UI/descubribilidad, documentada abajo.** `GET /api/review-queue` (`web/handlers/duplicates.py:161-165`) no acepta ningún parámetro de dispositivo/`source_root` — siempre llama a `_build_review_queue(repository, repo_android, config)` con ambos repos fijos (`repository_android` es `LibraryRepository(config.database_path_android)`, creado incondicionalmente en `cli.py:467`, nunca `None`). `_build_review_queue`/`_review_groups_for_repo` (`web/builders/duplicates.py:602-663`) consulta siempre los dos repos y **fusiona el resultado en una sola cola** — PC y Android nunca se agrupan como "el mismo duplicado" entre sí (ver docstring), pero sí aparecen juntos en la lista. `apiFetch` (`web/static/js/api.js:15-19`) es un `fetch()` desnudo, no inyecta ningún filtro de dispositivo. Confirmado que no hay ningún selector de dispositivo en `tab-plan.html` cerca de "Revisar copias" (`review-queue-content`, línea 68) que pudiera ocultar nada — la sección no tiene ningún control de filtro. **Causa probable real de la confusión (UX, no lógica)**: la sección "1. Plan de renombrado", justo encima en la misma pestaña, sí está filtrada por dispositivo y muestra un banner explícito "Viendo: PC — ..." / "Viendo: {consola} — ..." (`web/static/js/tabs/organize.js:48-67`, vía `window._activeDevice`/`_deviceRoot()`). "Revisar copias" no tiene ningún banner equivalente — el único indicio de que una entrada vive en la consola es una etiqueta pequeña por fila (`web/static/js/tabs/review_copies.js:111-113`, `e.is_device` → badge con `_devName`), fácil de pasar por alto. Un usuario viendo "PC" en la sección de arriba puede asumir razonablemente que la de abajo también está filtrada a PC. Otra causa probable, no descartable sin biblioteca real: si la Anbernic nunca se escaneó desde la app web (`/api/scan` con una ruta fuera de `library_root` — ver `_repo_for_path`, `web/builders/common.py:141-167`), `library_android.db` está vacío y "Revisar copias" no tendría nada de consola que mostrar, con razón. Sin cambio de código en esta sesión (regla del proyecto de investigar antes de arreglar) — posible follow-up de UX: un banner o nota en "Revisar copias" aclarando que ya cubre PC + Anbernic combinados, en vez de depender solo de la etiqueta por fila |
| DEDUP-RENAME-2b | **Follow-up de UX de `DEDUP-RENAME-2`**: banner explícito en "Revisar copias" aclarando que la sección combina PC + Anbernic (a diferencia de "1. Renombrar" arriba, que sí sigue el selector global de dispositivo) — para que el usuario no asuma que también está filtrada al dispositivo activo | `web/static/partials/tab-plan.html`, `web/static/js/tabs/review_copies.js` | ✅ implementado 2026-09-07 — nuevo `<div id="review-queue-context-bar">` en `tab-plan.html` (mismo patrón visual que `plan-context-bar`, oculto por defecto), poblado en `loadReviewQueue()` con "Combinando PC + {consola}" usando el `window._devName` global ya existente (sin fetch extra). Verificado sirviendo HTML/JS por curl (sin extensión de Chrome disponible en esta máquina para captura de pantalla). Sin tests nuevos — cambio puramente visual/textual, sin lógica que testear; suite completa 1228/1228 sin cambios |
| DEDUP-RENAME-3 | **Caso real encontrado 2026-08-29 buscando "Mario Kart DS" en Juegos**: 8 filas para el mismo juego, 3 con **el mismo SHA1** (`691E00D9A5...`). **Investigado — causa raíz encontrada, no es un bug de "Revisar copias"**: consulté `/api/review-queue` en vivo y el grupo SHA1 de Mario Kart DS **sí existe y sí tiene recomendación** (`reasons:["sha1"]`, `recommended:true` en la copia de `E:\Carpetas anbernic\nds\...(USA)...`) — el mecanismo funciona. El problema real es que de las 3 filas, **una es un registro fantasma**: `source_path` apunta a `C:\Users\rammu\Documents\projects\Retro_gaming_app\Este equipo\RG556\Ambernic\nds\Mario Kart DS (USA, Australia)...nds` — la ruta MTP fantasma del bug **INBOX-CFG-1** (`archivo.md`, "arreglado" 2026-08-13), que **ya no existe en disco** (confirmado, `ls` falla) pero la fila de BD nunca se borró. Motivo: `prune_stale_entries()` (`database/repositories/games.py:328-340`) solo borra filas bajo el `source_root` que se está escaneando — como esta fila vive bajo una ruta completamente distinta (dentro del propio repo del proyecto, nunca bajo `E:\Carpetas anbernic`), **ningún scan de la biblioteca real la toca jamás**, quedó huérfana para siempre. **Alcance real, no solo Mario Kart DS**: `SELECT COUNT(*) FROM games WHERE source_path LIKE '%Este equipo%'` → **1.508 filas fantasma** en `library_pc.db`. Estas mismas filas también explican **ZIP-ROUTE-7** (confirmado: `id=65864`, `unknown\10192n.rom`, aparece en `/api/games` con `canonical_title: null` — exactamente "entradas sin portada" que reportó el usuario) — mismo origen, no dos bugs distintos. **Purgado de verdad 2026-08-29** (backup previo en `.rommgr/backup_ghost_purge_2026-08-29/library_pc.db`): script one-off reutilizando `repository.delete_game(id)` ya existente (cascada limpia de `game_metadata`/`game_tags`/`file_operations`, mismo mecanismo de REV43-10) — verificado primero que ninguna de las 1.508 rutas existe en disco (`Path.exists()`) antes de borrar ninguna, cero falsos positivos. Resultado: **1.508/1.508 borradas**, 0 restantes. Verificado en vivo: el grupo de Mario Kart DS en `/api/review-queue` pasó de 3 a 2 entradas (las 2 reales); `total_groups` de la cola bajó de 13.969 a 13.545 (grupos que solo eran fantasma+1 real dejaron de contar como duplicado); `id=65864` (`10192n.rom`) ya no aparece en `/api/games` | `database/repositories/games.py:328-340` (`prune_stale_entries`, scoping por `source_root` — causa de que nunca se autolimpiaran) | ✅ causa raíz documentada y purga ejecutada; sin cambio de código (el diseño de `prune_stale_entries` es correcto para su propósito, el problema era datos huérfanos de un incidente ya cerrado) |

---

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: JUNK-SMART-1/2/3, TABS-FIX-1..7 (+ TABS-FIX-6-DISC, DUP-RA-COLLISION-1), DEVSEL-FIX-1..4 (clasificador de basura por evidencia, auditoría UX Juegos/Organizar/Duplicados, selector de dispositivo — completas, 2026-07-08 a 2026-07-13).

---

### DUP-REGION-1/2 — Duplicados por región (mismo juego, distinta release No-Intro) + preferencias configurables (WIP retomado, pausado durante el roadmap 12)

`DUP-DISC-RA-1` (abajo) ya lo cita como origen aunque nunca tuvo sección
propia — quedó como WIP sin commitear en `git stash` desde antes del Día64
(roadmap 12 tuvo prioridad), retomado en rama propia a petición del usuario.

En plataformas de un solo archivo (GBA/GB/GBC/NES/SNES/...) el mismo juego
publicado en varias regiones No-Intro (`Tetris (USA)` vs `Tetris (Spain)`)
nunca se agrupaba en "Revisar copias" porque `canonical_title` incluye el
tag de región — son strings distintas, así que la unión por título exacto
nunca los enlazaba. Deliberadamente **excluido en `_MULTI_DISC_RISK_PLATFORMS`**
(PSX/Saturn/Dreamcast/Wii...): el propio comentario de la unión por título
exacto documenta por qué la coincidencia difusa es insegura ahí — la única
vez que se probó sin ese guard fusionó 18 discos regionales reales de Final
Fantasy VII en un solo grupo "duplicado" falso positivo.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-REGION-1 | Detectar el grupo (título difuso + plataforma, solo fuera de `_MULTI_DISC_RISK_PLATFORMS`) y añadir el motivo `"region"` a la cola de revisión — nunca auto-fusiona ni borra, solo recomienda cuál conservar (empate: integridad > soporte RA > carpeta correcta > región preferida > nombre) | `web/builders/duplicates.py` (`_review_groups_for_repo`, `region_linked_idxs`, `has_region_dup`) | ✅ implementado — confirmado contra la biblioteca real (2026-09-15, mencionado en el hallazgo original de Día64): 94 títulos GBA / 188 archivos, solo pares de región, ninguna secuela distinta fusionada por error (el tag de región es siempre un grupo `(...)` final, nunca parte del título) |
| DUP-REGION-2 | El desempate por idioma de `_review_entry_sort_key` era fijo (solo "¿es español?"); para el motivo `"region"` se necesita un ranking configurable por el usuario, no solo español-o-no. Nueva `DuplicatesConfig` (`config.py`): `preferred_regions` (lista ordenada, por defecto `["Spain", "Europe"]`) y `keep_both_regions` (si `True`, el motivo `"region"` no se dispara nunca — el usuario conserva todas las regiones a propósito) | `config.py` (`DuplicatesConfig`), `detection/region_parser.py` (`KNOWN_REGIONS`, para el selector de la UI), `web/builders/duplicates.py` (`_review_entry_sort_key` con `region_tiebreak`/`preferred_regions`), `web/builders/misc.py` (`_build_config`), `web/handlers/config.py` (`_save_config`, campos `duplicates.*`), `web/static/js/tabs/config.js` + `tab-settings.html` (picker de regiones con reordenar/quitar, checkbox "mantener todas") | ✅ implementado con tests (`test_same_title_cross_region_flagged_for_review`, `test_keep_both_regions_config_suppresses_region_groups`, `test_preferred_regions_config_overrides_default_ranking`) — 1370 tests totales, ruff limpio. ✅ **mergeado** (PR #327, `2173ff1`) — el backlog seguía diciendo "sin PR todavía" pese a estar ya en `develop` |

---

### DUP-DISC-RA-1 — Hash RA de discos (PS1 primero) para poder descartar copias sin logros (pedido usuario 2026-08-30)

Origen: tras DUP-REGION-1, el usuario pidió que las copias duplicadas en
plataformas de disco (PSX/Saturn/Dreamcast/Wii) también se puedan descartar
prefiriendo la que tiene soporte RetroAchievements — igual que ya se hace en
GBA. Investigado primero: **0 de 474 juegos PSX con MD5 calculado coincidían
con el caché de RA** (`ra_hashes_12.json`, 1.318 hashes) — 0/29 en Dreamcast
también. Causa: RA no hashea el archivo completo del disco para PS1/Saturn/
Dreamcast, usa un algoritmo específico (localiza `SYSTEM.CNF` en el
filesystem ISO9660, extrae el ejecutable de arranque de la línea `BOOT=`, y
hashea `nombre_exe + bytes_del_exe`) — nuestro MD5 de archivo completo nunca
iba a coincidir, independientemente de la lógica de agrupación.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-DISC-RA-1a | **Implementado y verificado 2026-08-30**: reimplementación en Python del algoritmo de hash PSX de RetroAchievements (`rc_hash_psx`, fuente consultada directamente en github.com/RetroAchievements/rcheevos `src/rhash/hash_disc.c`+`cdreader.c` — no es un port del C, pero fiel byte a byte, incluyendo sus particularidades case-sensitive en "BOOT"/"cdrom:", porque una reimplementación "más limpia" daría un hash *distinto* que nunca coincidiría con el de RA). Soporta `.bin` suelto, `.cue`+`.bin` (primer FILE) y `.chd` (vía `chdman extractcd`, `tools/chdman.exe` ya en el proyecto). **Validado contra caché RA real, no solo con datos sintéticos**: de 259 archivos `.bin`/`.cue` reales de la biblioteca PSX, 124 coincidieron EXACTAMENTE con un hash ya presente en `ra_hashes_12.json` (47,9%) — prueba directa de que el algoritmo es correcto. CHD también probado en vivo (3/15 de una muestra, el resto son juegos fuera del caché de 1.318 o casos sin `SYSTEM.CNF` estándar) — más lento (~7s/archivo, `chdman` descomprime el CHD entero a un `.bin` temporal cada vez, sin caché todavía). Test unitario con imagen ISO9660 sintética mínima construida a mano (`tests/test_ra_hash_psx.py`, 3/3) — no depende de archivos reales | `retroachievements/ra_hash_psx.py` (nuevo), `tests/test_ra_hash_psx.py` (nuevo) | ✅ algoritmo implementado y verificado contra datos reales |
| DUP-DISC-RA-1b | **Parte 1 implementada 2026-08-30**: `ra_checker.check_library()` ya usa el hash de disco (vía `ra_disc_hash_cache.get_psx_disc_hash`, cacheado en `.rommgr/ra_cache/psx_disc_hashes.json` por `(source_path, mtime, size)`) en vez de `row["md5"]` para consolas con `console_id in _DISC_HASH_CONSOLE_IDS` (por ahora solo PSX, 12). Wireado hasta `/api/ra-check` (`web/handlers/sync.py`, pasa `config.chdman`). Test `test_playstation_uses_disc_hash_not_stored_md5`. **Parte 2 implementada 2026-09-21** (rammu): nueva pasada de unión en `_review_groups_for_repo` (mismo patrón que `crossfmt`/`region`, pero uniendo por hash de disco RA en vez de título difuso) — dos filas de la cola de duplicados con el mismo hash de disco RA se tratan como la misma edición aunque no compartan SHA1 ni `canonical_title`. Alcance real: `_DISC_HASH_CONSOLE_IDS` (`ra_checker.py`) ya trae hash cacheado para PSX **y también GameCube/Wii** (`get_gamecube_wii_disc_hash`, más completo de lo que decía esta fila — Saturn/Dreamcast siguen sin cache wireada, `DUP-DISC-RA-1c` dejó explícitamente esa parte fuera). Nuevo motivo `"disc_hash"` en la cola (`reasons`), etiqueta añadida en `review_copies.js` (`_REASON_LABELS`). Cubre exactamente el caso real de `ANDROID-DUP-1` (`Crash Bandicoot (USA)` en `.bin+.cue`/`.chd`/carpeta CloneCD legacy con nombre de serial, sin `canonical_title` en la copia legacy — invisible a `sha1`/`title`/`crossfmt` hasta ahora). 2 tests nuevos (`test_disc_hash_union_links_legacy_dump_with_no_catalog_match`, `test_disc_hash_union_skips_when_hashes_differ`), suite completa 1424 tests (3 fallos son los ambientales ya conocidos de ADB conectado). **Validado contra `library_pc.db` real 2026-09-21** (345 PlayStation + 59 GameCube + 118 Wii, la biblioteca real de `E:\Carpetas anbernic`): 3 min de ejecución (la caché de hashes ya cubría casi todo), 1829 grupos totales en la cola, **1 grupo nuevo vía `disc_hash`** — `Resident Evil 3 - Nemesis (USA, Canada).chd` enlazado con `resident evil 3.chd` (nombre no canónico), confirmando que el hash de disco RA funciona en producción sin errores. **Matiz**: el escenario que motivó la tarea (`ANDROID-DUP-1` — volcado legacy CloneCD con nombre de serial `[SCUS-nnnnn]`, invisible a sha1/title/crossfmt) vive en la RG556 vía ADB (`/storage/521D-04EA/ROMs/`), un medio físico distinto de `E:\Carpetas anbernic` — validar ese caso exacto requeriría copiar esos archivos legacy localmente primero (el hash de disco RA necesita leer el archivo directo, ADB no sirve sin montar el dispositivo), sesión aparte, sin hacer todavía | `retroachievements/ra_checker.py`, `retroachievements/ra_disc_hash_cache.py`, `web/handlers/sync.py`, `web/builders/duplicates.py` (`_review_groups_for_repo`, parte 2 nueva), `web/static/js/tabs/review_copies.js` | ✅ hash-check + agrupado por edición implementados y validados contra datos reales; caso legacy CloneCD de la RG556 (ADB) sigue sin validar |
| DUP-DISC-RA-1c | **Implementado 2026-09-07**: mismo algoritmo pero para Saturn/Dreamcast — Wii sigue sin aplicar (no es un CD, RA lo hashea distinto, formato propio). Investigado directamente en la fuente de rcheevos (`github.com/RetroAchievements/rcheevos`, `src/rhash/hash_disc.c` — `rc_hash_sega_cd()` para Saturn, `rc_hash_dreamcast()` para Dreamcast — y `cdreader.c`, fetch directo con `curl`). Hallazgo que simplificó bastante el trabajo: Saturn NO hace boot-exe lookup como PSX — RA solo hashea el header crudo de 512 bytes al principio de la pista 1 (comentario propio de rcheevos: "hashing the volume and ROM headers is sufficient"), sin tocar el sistema de archivos. Dreamcast sí es más parecido a PSX: hashea 256 bytes de IP.BIN (pista 3, no la 1 — GD-ROM) + el ejecutable de arranque (nombre en el offset 96 de IP.BIN), localizado por el mismo lookup ISO9660 genérico que ya usaba PSX (confirmado en la fuente: `rc_cd_find_file_sector` es la misma función para todas las consolas, PSX incluida — nunca fue específica de PSX). **Refactor previo sin cambio de comportamiento**: el lector de sectores CD + el buscador ISO9660 (antes solo en `ra_hash_psx.py`) se extrajeron a `retroachievements/ra_cd_image.py` nuevo, compartido — evita triplicar la misma lógica ya que las tres consolas usan literalmente el mismo algoritmo de lectura de sectores/geometría. 7 tests de `ra_hash_psx` siguen en verde tras la extracción. Módulo nuevo `retroachievements/ra_hash_saturn_dreamcast.py`: `compute_saturn_ra_hash()` (`.bin`/`.cue`/`.chd`) y `compute_dreamcast_ra_hash()` (`.bin`/`.cue`/`.chd`/`.gdi` — parser propio de `.gdi` para resolver la pista 3 por número, ya que en GD-ROM cada pista es normalmente su propio archivo). 7 tests nuevos con imágenes sintéticas (mismo patrón que `test_ra_hash_psx.py`) — a diferencia de PSX, **sin verificar todavía contra caché RA real** (sin biblioteca Saturn/Dreamcast en esta máquina): la corrección del parseo de bytes está probada, la fidelidad al hash real de RA no. Wireado hasta `ra_checker.py`/`ra_disc_hash_cache.py` (equivalente a la "parte 1" de `DUP-DISC-RA-1b` para PSX) queda **fuera de esta tarea a propósito** — el pedido original decía "mismo algoritmo", no el wiring; candidato natural para una `DUP-DISC-RA-1d` si se quiere activar en la comprobación RA real. Suite completa 1235/1235 | `retroachievements/ra_cd_image.py` (nuevo), `retroachievements/ra_hash_saturn_dreamcast.py` (nuevo), `retroachievements/ra_hash_psx.py` (refactorizado, sin cambio de comportamiento), `tests/test_ra_hash_saturn_dreamcast.py` (nuevo) | ✅ algoritmo implementado y probado con datos sintéticos; sin verificar contra caché RA real ni wireado a `ra_checker.py` todavía |
| DUP-DISC-RA-1e | **Intento de validación real 2026-09-07 bloqueado por gap de formato**: al intentar validar `compute_saturn_ra_hash`/`compute_dreamcast_ra_hash` contra la biblioteca real (`F:\Juegos Retro`, sí montada en esta máquina) se encontró que Saturn no tiene ningún ROM real ahí (solo `saturn\media\images`/`videos`, artefactos del scraper) y que los 5 juegos reales de Dreamcast están **todos en `.cdi`** (`Crazy Taxi 2`, `Dead or Alive 2 (Beta)`, `Legacy of Kain - Soul Reaver`, `Marvel Vs Capcom 2` [además tiene `.A1.bin`, que es un save de VMU, no la imagen del disco], `Sonic Adventure`). `compute_dreamcast_ra_hash()` (`retroachievements/ra_hash_saturn_dreamcast.py:145-162`) solo reconoce `.gdi`/`.cue`/`.bin`/`.chd` — devuelve `None` para `.cdi` sin intentarlo siquiera, así que la validación contra la caché RA real de `DUP-DISC-RA-1c` sigue sin poder hacerse en esta máquina hasta que se añada un parser de `.cdi` (formato DiscJuggler — cabecera y layout de pistas distintos de un `.bin`/`.cue` crudo, no es un simple alias). **Investigado a fondo 2026-09-07 (segunda pasada) y cerrado sin implementar**: se probó primero convertir con `chdman createcd` (la propia herramienta del proyecto) — la conversión se quedó colgada sin avanzar (>15 min, salida de 124 bytes). Investigando la causa en el código fuente real de MAME (`src/tools/chdman.cpp` → `cdrom_file::parse_toc`, `src/lib/util/cdrom.cpp:2966-2990`, descargado con `curl` vía `raw.githubusercontent.com`): **`chdman` tampoco soporta `.cdi`** — el dispatcher por extensión solo reconoce `.gdi`/`.cue`/`.nrg`/`.iso`/`.cdr`/`.toast`; cualquier otra extensión cae al parser de texto genérico CDRDAO `.toc`, que intenta leer el archivo binario `.cdi` como líneas de texto (de ahí el cuelgue, no lentitud). Y **`rcheevos` (la librería de referencia de RA) tampoco soporta `.cdi`**: su propio dispatcher (`src/rhash/cdreader.c:777-788`, ya consultado para `DUP-DISC-RA-1c`) solo reconoce `.cue`/`.gdi` por extensión — cualquier otra cosa (incluido `.cdi`) se abre como `.bin` crudo de una sola pista, lo que daría un hash **silenciosamente incorrecto**, no un "no soportado" limpio. Con ni RA ni chdman soportando el formato, escribir un parser propio de DiscJuggler no tendría ningún oráculo contra el que validar que el hash resultante coincide con el real de RA — el riesgo de dar por buena una implementación que en realidad nunca coincidiría es alto. **Decisión (discutida con el usuario 2026-09-07): no implementar por ahora** — se retoma si aparece una vía de validación independiente (chdman añade soporte `.cdi` en una versión futura, o se publican hashes RA de Dreamcast conocidos de la comunidad) | `retroachievements/ra_hash_saturn_dreamcast.py:145-162` (`compute_dreamcast_ra_hash`) | ⚪ investigado y cerrado sin implementar — ni RA ni chdman soportan `.cdi`, sin oráculo para validar un parser propio; Saturn sigue sin ningún ROM real que validar en esta biblioteca |
| DUP-DISC-RA-2 | **Implementado y verificado 2026-08-30** (pedido explícito del usuario: "usa chd como formato de psx"). Recomendación confirmada: **CHD**, un archivo por disco, soportado nativamente por RetroArch/`chdman` (ya en `tools/`). Descubierto que ya existía un conversor sin usar (`rommgr convert-chd` / `converters/chd_converter.py`) que solo cubría `.cue`+`.bin` reales — **extendido** en vez de duplicado: (1) `find_bare_bin_files()` descubre `.bin` sueltos sin `.cue` (el caso mayoritario real, ver DUP-DISC-RA-2b) validando con `compute_psx_ra_hash()` que de verdad son un disco legible, no una pista de audio huérfana; (2) `synthesize_cue_text()` genera un `.cue` mínimo de una pista reutilizando `detect_bin_cue_mode()` (nuevo en `ra_hash_psx.py`); (3) `parse_bins_from_cue()` arreglado para resolver solo por nombre base (bug real encontrado: `.cue` con ruta absoluta rota, ver DUP-DISC-RA-2b, hacía que el `cwd=` existente no sirviera de nada); (4) **cada conversión se verifica comparando el hash RA de disco antes/después** (`_verify_ra_hash`) — si no coincide, se borra el `.chd` y el original queda intacto, nunca se sobreescribe a ciegas. `chdman createcd` necesita la palabra `BINARY` en la línea `FILE` del `.cue` sintético (bug propio encontrado y arreglado — sin ella da "Unhandled track type"). 13/13 tests en `test_chd_converter.py` (incluye conversión real de punta a punta con `chdman.exe` y un caso de mismatch de hash forzado). **Dry-run contra la biblioteca PSX real** (`rommgr convert-chd "E:\Carpetas anbernic\psx"`): **181 convertibles** (bare-bin + 0 cue reales, los 18-22 `.cue` reales están todos rotos, ver DUP-DISC-RA-2b), 22 fallos (cue roto), 1 ya convertido. **No ejecutado con `--apply`** contra la biblioteca real — pedido explícito del usuario de construir la herramienta y ejecutarla aparte; nota de rendimiento: un solo disco de ~600MB tardó >10 min con la compresión por defecto de `chdman` en esta máquina, así que los 181 son horas, no minutos — pensar en correrlo en background/durante la noche | `converters/chd_converter.py`, `retroachievements/ra_hash_psx.py` (`detect_bin_cue_mode`), `tests/test_chd_converter.py`, `cli.py` (ayuda actualizada) | ✅ herramienta lista y verificada; ejecución real pendiente, la lanza el usuario |
| DUP-DISC-RA-2b | **Ya no aplica — verificado 2026-09-08 contra `E:\Carpetas anbernic\psx` real**: los 18-22 `.cue` rotos del hallazgo original (2026-08-30) ya no existen tal cual. Reutilizando `parse_bins_from_cue()` (el mismo parser de `DUP-DISC-RA-2`, solo lectura) sobre los **33 `.cue` reales de hoy: 0 rotos** — confirmado además con `rommgr convert-chd "E:\Carpetas anbernic\psx"` (dry-run): `Would convert: 33 | Would skip: 0`. Los dos casos citados en el hallazgo original (`Chrono Cross (Japan).cue`, `Crash 2.cue`) ni siquiera existen ya en la carpeta — `Chrono Cross` ahora vive como `Chrono Cross (USA, Canada) (Disc 2).chd` (ya convertido). La biblioteca cambió entre el hallazgo y hoy (probable limpieza/conversión de otra sesión, sin diario que lo documente explícitamente) y el problema desapareció como efecto colateral — mismo patrón que `LIBRARY-SYNC-STALE-1d` esta misma sesión. Sin cambios de archivos en esta verificación (solo lectura) | `psx/*.cue` | ✅ verificado 2026-09-08 — ya no hay `.cue` rotos |

---

### DUP-DISC-SET-1 — `_is_disc_set()` no protege un set multi-disco cuando una edición regional sin tag `(Disc N)` se mezcla con los discos sueltos de otra edición (hallazgo 2026-09-21, datos PSX reales vía ADB, Fase 3 de `ANDROID-DUP-2`)

Origen: al correr `_build_review_queue` contra `library_android.db` con
hash real de PSX/PS2 por primera vez, el grupo `Xenogears` unió
`Xenogears (Japan).chd` (edición japonesa, un solo disco, sin tag `(Disc
N)` en el nombre) con `Xenogears (USA) (Disc 1).chd` y `(Disc 2).chd` —
tres discos con contenido distinto tratados como "duplicados", con riesgo
real de que "Aplicar recomendación" descarte un disco necesario del set
USA. Mismo patrón visto en `Metal Gear Solid`/`Final Fantasy VIII`/
`Parasite Eve` (149 grupos psx/ps2 en total, 94 `crossfmt` + 67 `sha1`).

Causa raíz confirmada: `_is_disc_set()` (`web/builders/duplicates.py:56-80`)
devuelve `False` (guard desactivado, el clúster se trata como duplicado
normal) en cuanto **un solo miembro** del clúster no tiene número de disco
parseable (`find_disc_number()` → `None`, línea 77-78). Protege bien un
set donde *todos* los miembros llevan tag de disco (`(Disc 1)`/`(Disc 2)`),
pero no cuando una edición regional single-disc (sin tag, p. ej. la
japonesa) queda unida al mismo clúster que los discos individuales de una
edición multi-disco vía `crossfmt`/`sha1` — el guard nunca llega a
evaluarse como "sí es un set multi-disco" porque el miembro sin tag rompe
la condición `for r in members: if num is None: return False`.

**Implementado (2026-09-21, Día68)**: `_is_disc_set()` ya no descarta el
guard de golpe ante un miembro sin número de disco parseable — ahora
excluye ese miembro del cómputo y sigue exigiendo ≥2 números distintos
*entre los miembros que sí llevan tag*. Test de regresión con el caso real
exacto (`Xenogears (Japan).chd` + `(USA) (Disc 1/2).chd`, mismo
`canonical_title`) confirmado en rojo contra el código anterior y en verde
tras el fix. Suite completa (1423 tests) sin regresiones nuevas (3 fallos
ambientales preexistentes, dispositivo ADB conectado).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-DISC-SET-1 | Arreglar `_is_disc_set()` para no perder la protección de set multi-disco cuando un miembro del clúster no lleva tag de disco (edición regional single-disc mezclada con discos sueltos de otra edición) | `web/builders/duplicates.py:56-84` (`_is_disc_set`), `tests/test_builders_duplicates.py` | ✅ hecho 2026-09-21 — desbloquea aplicar `resolve-duplicates --apply` sobre los 149 grupos psx/ps2 de `ANDROID-DUP-2` Fase 3 (revisión manual sigue recomendada antes de aplicar, no es automático) |

---

### DUP-DISC-SET-2 — `has_sha1_dup` no está protegido por `_is_disc_set()`: un duplicado real dentro de un clúster arrastra discos legítimos de un set multi-disco al mismo grupo "descartar" (hallazgo 2026-09-21, Día68, al aplicar `resolve-duplicates` real sobre los 149 grupos psx/ps2 recién desbloqueados)

Origen: tras `DUP-DISC-SET-1`, al inspeccionar el grupo real `Xenogears`
contra `library_android.db` (`_build_review_queue`), seguía recomendando
descartar `Xenogears (USA) (Disc 2).chd` — un disco real, no un duplicado.
Causa: `Xenogears (Japan).chd` y `Xenogears (USA) (Disc 1).chd` son
literalmente byte-idénticos (mismo SHA1, probable mal etiquetado regional)
— duplicado real y correcto de detectar. Pero `has_sha1_dup`
(`web/builders/duplicates.py:1151`) no está gateado por `_is_disc_set()`
como sí lo están `has_title_dup`/`has_crossfmt_dup`/`has_region_dup`/
`has_disc_hash_dup` — así que el union-find ya mezcló Disc 1 y Disc 2 en el
mismo componente (vía `crossfmt`, correctamente ignorado como *razón* por
el guard, pero el `union()` en sí ya ocurrió antes de que se evalúe
`_is_disc_set`), y el motor de recomendación elige UN solo "conservar"
para todo el componente, marcando Disc 2 como "descartar" pese a no ser
duplicado de nada.

**Medido en real (Día68)**: 6 de 156 grupos psx/ps2 tienen este patrón
compuesto (`Xenogears`, `Final Fantasy VIII`, `Parasite Eve` — perderían
Disc 2/3/4 reales — más 3 clústeres de pistas `.bin` sueltas sin tag de
disco, ver `DUP-DISC-TRACK-1`). **Excluidos manualmente del apply de hoy**
(`repository.exclude_duplicate_group` no usado — se filtraron fuera de la
`queue` pasada a `apply_all_review_recommendations`, ver
`DUP-DISC-SET-1`/Día68 para el detalle). Sin arreglar en el motor — la
detección de `_is_disc_set` necesita aplicarse también a la selección de
qué entradas puede marcar "descartar" dentro de un componente, no solo a
qué *razón* se etiqueta.

**Implementado (2026-09-22, Día69)**: cuando un clúster es un set multi-disco
real (`_is_disc_set()` True) Y además tiene un `has_sha1_dup` real, ya no se
trata el clúster entero como un único grupo de revisión. En su lugar se
agrupan los miembros por SHA1 dentro del propio clúster — solo los
subconjuntos con SHA1 realmente compartido (≥2 archivos) se emiten como su
propio grupo de duplicado (razón `sha1`, `group_key` con sufijo por SHA1 para
no colisionar); un miembro con SHA1 único dentro del set (un disco legítimo
sin duplicado) no entra en ningún grupo — nunca puede ser "recomendado
descartar". Refactor: la construcción de `entries`/`recommended`/`wasted`
(antes ~55 líneas inline por clúster) se extrajo a una función anidada
`emit_group()`, reutilizada tanto por el camino normal como por cada
sub-grupo SHA1 de un set multi-disco — evita duplicar esa lógica ya probada.
Test de regresión con el caso real exacto (Xenogears Japan+Disc1 mismo SHA1,
Disc2 SHA1 propio): confirmado en rojo contra el código anterior (`git
stash`) y en verde tras el fix — el grupo resultante contiene solo
Japan+Disc1, Disc2 no aparece en ningún grupo. Suite completa (1427 tests):
0 regresiones. `Final Fantasy VIII`/`Parasite Eve` (mismo patrón, sin caso de
test dedicado) quedan cubiertos por la misma lógica genérica, no por un fix
específico de Xenogears.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-DISC-SET-2 | Arreglar el motor de recomendación para que un componente que mezcla un duplicado SHA1 real con discos legítimos de un set multi-disco no marque esos discos como "descartar" — probablemente separar sub-clústeres por número de disco antes de elegir "recomendado" | `web/builders/duplicates.py` (`_review_groups_for_repo`, `emit_group` nuevo, rama `is_disc_set and has_sha1_dup`), `tests/test_builders_duplicates.py` | ✅ hecho 2026-09-22 — desbloquea revisar/aplicar `Xenogears`/`Final Fantasy VIII`/`Parasite Eve` sin riesgo de perder un disco real (revisión manual sigue recomendada antes de aplicar) |

---

### DUP-DISC-TRACK-1 — Pistas de audio CD silenciosas/genéricas en `.bin` sueltos (sin `.cue`/contexto de set) producen SHA1 idéntico entre juegos completamente distintos, falso positivo de duplicado (hallazgo 2026-09-21, Día68, mismo repaso que `DUP-DISC-SET-2`)

Origen: al revisar (muestreo manual, 35 de 146 grupos) los candidatos a
`resolve-duplicates --apply` antes de ejecutarlo, aparecieron varios
grupos donde dos **juegos sin relación** comparten SHA1 en un único
archivo `.bin` con sufijo `(Track N)` — ej. `Ninja - Shadow of Darkness
(Europe) (Track 44).bin` == `Ultraman Zearth (Japan).bin`; `Guilty Gear
(Europe) (Track 2).bin` == `Guilty Gear (USA) (Rev 1).bin` (aquí sí
mismo juego pero probablemente solo la pista coincide, no el disco
completo); `Magical World of Disney...(Track 3).bin` ==
`Nestle Disney Demo (Europe).bin`. Estos son volcados PSX multi-pista
donde cada pista de audio se trackeó como archivo independiente (sin
`.cue` que las agrupe) — una pista de audio silenciosa o genérica
(intro/logo) puede ser byte-idéntica entre discos de juegos distintos sin
que el contenido real (los datos del juego) tenga nada que ver.

**Medido en real (Día68)**: 46 de 146 grupos candidatos (~31%) tenían al
menos un miembro `.bin`; de esos, 39 llevaban sufijo `(Track N)` (patrón de
pista suelta, alto riesgo) y 7 eran `.bin` de archivo completo sin sufijo
de pista (mismo título que su `.chd`/`.cue` — esos sí se verificaron uno a
uno y se aplicaron). **Ninguno de los 46 se aplicó hoy** — se excluyeron
todos por precaución hasta diseñar una regla fiable.

**Implementado (2026-09-22, Día69)**: se eligió el segundo enfoque propuesto
(excluir pistas de audio del union-find por completo) por ser el más simple
y seguro — reordenar para exigir un link `crossfmt`/`canonical_title` previo
habría requerido mover el union por SHA1 después de esas pasadas, más riesgo
para el mismo resultado. Cualquier fichero cuyo nombre lleve un tag
`(Track N)` (`_is_loose_track_file()`, regex `\(track\s*\d+\)`) nunca entra
en el union por SHA1 (`web/builders/duplicates.py`, pase inicial de
`first_by_sha1`) — ni como primer miembro ni como candidato a unirse a otro.
No distingue Track 1 (dato) de Track N>1 (audio) porque el N por sí solo no
es fiable como señal (ver ejemplos reales arriba, algunos con Track bajo);
la protección se aplica a cualquier `(Track N)`. Test de regresión con el
caso real exacto (`Ninja - Shadow of Darkness (Track 44).bin` ==
`Ultraman Zearth (Japan).bin`, mismo SHA1): confirmado en rojo contra el
código anterior (`git stash`) y en verde tras el fix. Suite completa (1428
tests): 0 regresiones.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-DISC-TRACK-1 | Evitar que un SHA1 compartido entre pistas de audio CD sueltas (`.bin` con `(Track N)`, sin `.cue` de contexto) una en el mismo clúster de duplicados a juegos sin relación | `web/builders/duplicates.py` (`_is_loose_track_file`, union por sha1), `tests/test_builders_duplicates.py` | ✅ hecho 2026-09-22 — desbloquea revisar los 46 grupos excluidos en Día68 sin riesgo de falso positivo entre juegos sin relación (revisión manual sigue recomendada antes de aplicar) |

---

### ANDROID-DUP-2 Fase 3 — aplicado el primer lote seguro de duplicados psx/ps2/Dreamcast contra la Anbernic real (Día68, 2026-09-21)

Tras `DUP-DISC-SET-1`, revisión manual completa de los 149 grupos psx/ps2 +
7 Dreamcast desbloqueados: excluidos los 6 de `DUP-DISC-SET-2`, el grupo
`disc_hash` de Resident Evil 3 (pendiente decisión del usuario, Día67 punto
9), los 2 `vmu_save_*.bin` (necesitan rescan tras el fix de clasificación
de hoy), `Dead or Alive 2`/`Legacy of Kain` (nombres de región ambiguos,
mismo contenido pero el "recomendado" automático no siempre elige el
nombre correcto) y los 46 de `DUP-DISC-TRACK-1`. De los 108 grupos
restantes (105 PlayStation + 3 Dreamcast, todo `.chd`/`.cue`/`.ccd`
completos o duplicados literales byte-idénticos, verificados con 2
muestreos aleatorios de 15+20 grupos), se aplicó vía `apply_all_review_
recommendations` con `AdbTransport` real (cola filtrada a mano, sin pasar
por el endpoint web/CLI genérico para no tocar los ~1850 grupos restantes
de la biblioteca PC, fuera de alcance de hoy) — backup previo de
`library_pc.db`/`library_android.db`.

**Resultado**: 132 archivos borrados en la Anbernic, 13,02 GB liberados, 0
errores. Verificado por dos vías independientes (resultado de la función +
diff directo de `library_android.db` antes/después): ambas coinciden
exactamente en 132 archivos / 13,02 GB. Los 6 grupos de `DUP-DISC-SET-2`
confirmados intactos tras la operación (7/9 entradas cada uno, sin tocar).

**Pendiente**: quedan ~40 pares adicionales mismo-título `.chd`+`.bin`
(ej. `Vagrant Story`, `Crash Bandicoot`, `Tony Hawk's Pro Skater 2/4`) sin
aplicar — excluidos por el filtro conservador de hoy (cualquier grupo con
un miembro `.bin` quedó fuera salvo los 7 revisados a mano), candidatos
para una revisión uno-a-uno en otra sesión.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ANDROID-DUP-2-APPLY-1 | Revisar uno a uno y aplicar (si procede) los ~40 pares restantes mismo-título `.chd`+`.bin` no incluidos en el lote seguro de hoy | — (revisión manual + `apply_all_review_recommendations` con cola filtrada) | ✅ **hecho 2026-09-25** — 68 grupos aplicados en total (22 sha1 puro + 46 `.chd`+`.bin` verificados por hash RA real), 25,08 GB liberados, 0 errores. 5 MISMATCH reales y 2 no-hasheables sin tocar, ver `ANDROID-DUP-CROSSFMT-VERIFY-1` |

**Sesión 2026-09-25**: recalculada la cola (`/api/review-queue`, `library_android.db`
real con la Anbernic conectada) — **83 grupos solo-dispositivo, 35,88 GB**
(antes 96 el Día68; la bajada de 13 grupos es exactamente `DUP-CROSSFMT-10`
+ `DUP-SHA1-JUNK-1` ya resueltos, confirma que esos fixes surtieron efecto
sin regresión). De los 83: **22 tienen `reasons == ["sha1"]` puro** (par de
2 entradas, hash SHA1 verificado byte-idéntico entre `keep` y `discard`) —
aplicados con `POST /api/resolve-duplicate-ra` uno a uno (cola filtrada a
mano, backup previo de `library_android.db`): **22/22 borrados, 0 errores,
2,30 GB liberados**, verificado por fila de BD (0/22 filas descartadas
siguen en la BD) y por archivo real en el dispositivo (`adb shell test -e`
sobre 2 casos). Incluye los `Xenogears`/`Final Fantasy VIII`/`Parasite Eve`
que `DUP-DISC-SET-2` desbloqueó. **Hallazgo colateral, no bloqueante**: 3
de los 22 "keep" recomendados son el nombre correcto del juego pero viven
anidados dentro de la carpeta de OTRO juego (`Twisted Metal (Europe)/
AirAssault - The Red Mercury Missions (Japan).bin`, mismo patrón con
`Jet Moto '98`/`Interactive CD Sampler...`) — contenido verificado idéntico
así que no hay pérdida de datos, pero la ubicación final queda rara
(posible resto del mismo volcado sin explicar de `UNKNOWN-BULK-GROWTH-1`,
sin investigar más por ahora).

### LIBRARY-HEALTH-DASH-1 / DUP-VISUAL-UI-1 — Panel de salud + duplicados side-by-side (idea usuario 2026-09-22)

Consolidar en Inicio los números ya calculados en pestañas sueltas (% organizada,
GB en duplicados, carpetas huérfanas, ZIPs sin organizar) y mostrar los grupos de
duplicados con portada + flag RA en vez de solo tabla de texto. Roadmap:
`.claude/roadmaps/archivo/27-library-ux-dashboard-duplicates.md`, rama
`feature/library-ux-dashboard-duplicates` (PR #340).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| LIBRARY-HEALTH-DASH-1 | Panel de salud en Inicio: % organizada, GB duplicados, carpetas huérfanas, ZIPs sin organizar — cada tarjeta enlaza a su reporte existente | `web/handlers/esde/maintenance.py` (`misplaced_zips` nuevo en `/api/library-extras`), `web/static/partials/tab-overview.html` (`ov-health-dash`), `web/static/js/tabs/overview.js` (`_loadLibraryHealth`) | ✅ hecho 2026-09-22 — sin endpoint agregado nuevo, compone `/api/status` + `/api/library-doctor` + `/api/library-extras` en frontend; test `tests/web/test_library_extras.py::test_library_extras_misplaced_zips` |
| DUP-VISUAL-UI-1 | Vista side-by-side de duplicados con portada + flag RA (fallback a tabla de texto sin portada) | `web/static/js/tabs/review_copies.js` (`_renderReviewEntry` — la vista real de duplicados desde TABS-FIX-6, `duplicates.js` quedó solo como selector PC/Android), `web/builders/duplicates.py` (`id` nuevo en entries del review-queue) | ✅ hecho 2026-09-22 — el roadmap apuntaba a `duplicates.js` (desactualizado); flag RA ya existía, solo faltaba la portada. Sin portada en copias de la consola (limitación preexistente de `/api/asset-image`, solo resuelve contra la BD del PC) |

---

### JUNK-SCAN-RUBEN-1 — Primer junk-scan real de esta máquina: 6.072 archivos / 34,97 GB sin clasificar (hallazgo 2026-09-28, máquina "Ruben", `F:\Juegos Retro`)

**Por qué se lanzó**: durante `JUEGOS-FIX-4`/`SAGE-1` de hoy se vio que esta
máquina diverge fuerte de los números que ya tenía el backlog (cobertura de
scraper real 27,78% vs. 75-90% esperado; los 7 huérfanos de `$RECYCLE.BIN`
de `JUEGOS-FIX-4` resultaron ser de otra máquina, 0 aquí). Sospecha: esta
biblioteca nunca pasó por el junk-scan/limpieza inicial de Pilar 1 que sí
tuvieron otras (`JUNK-SMART-1/2/3`, `JUNK-REVIEW-1`, Día39 — todo eso corrió
contra bibliotecas de otras máquinas). Se lanzó `POST /api/junk-scan` real
(solo lectura, sin borrar/mover nada) para confirmarlo antes de asumir nada.

**Resultado real** (`F:\Juegos Retro`, 291 categorías agrupadas por
confianza):

| Confianza | Archivos | Tamaño | Qué es |
|---|---|---|---|
| `safe_delete` | 3.659 | 4,93 GB | Basura real: chips sueltos sin match, extensiones no-ROM residuales (`.app`, `.tmd`, `.tik`, numéricas sueltas tipo `.03`/`.04`...) — mismo patrón que Día39 |
| `misplaced` | 2.176 | 13,87 GB | ROMs identificadas por CRC pero en la carpeta equivocada — **1.825** por match directo de catálogo ("ROMs de consola identificadas"), **347** por extensión interna de romhack — mismo mecanismo ya construido en `ZIP-ROUTE-1`/`ZIP-ROUTE-3`, sin ejecutar nunca aquí |
| `review` | 237 | 16,18 GB | Necesita decisión: **120 "ZIPs no-ROM" (10,24 GB)** — probablemente colecciones reales (zip-de-zips), mismo caso que `ZIP-ROUTE-4`; **8 "7-Zips" (5,27 GB)** sin manejar por el pipeline actual (solo entiende `.zip`); **108 chips arcade sin match de catálogo**; 1 set arcade de otra versión (0,62 GB) |
| **Total** | **6.072** | **34,97 GB** | |

**Siguiente paso propuesto (sin ejecutar todavía, pendiente de tu confirmación)**:
1. `safe_delete` (4,93 GB): dry-run de `/api/junk-delete` primero, igual que
   Día39/`JUNK-REVIEW-1` — reporta qué borraría, confirmas, luego real
   (va a `_descartados/`, deshacible ~30 días, no es un borrado directo).
2. `misplaced` (13,87 GB): mismo motor de `ZIP-ROUTE-1`/`-3` ya construido
   — mover/renombrar a su carpeta de plataforma real. Sin riesgo de
   pérdida (son ROMs identificadas, no basura), pero sí mueve 2.176
   archivos de sitio.
3. `review` (16,18 GB): requiere mirar caso a caso — **revisados los
   nombres reales de ambos sub-buckets (2026-09-28), no son lo que
   parecían**:
   - **120 "ZIPs no-ROM" NO son colecciones** — son ZIPs de un solo juego
     con nombre canónico No-Intro/Redump ya puesto (`Crash Bandicoot 2 -
     Cortex Strikes Back (USA).zip`, `Bushido Blade (USA).zip`, `Jet Set
     Radio (Europe).zip`...), todos sueltos en `Unknown\` — candidato
     directo para `ZIP-ROUTE-1` (identificación por CRC32 del header, sin
     descomprimir), no para `ZIP-ROUTE-4` (extraer colección). El junk-scan
     los cuenta como "no-ROM" porque su extensión (`.zip`) no delata la
     plataforma por sí sola, no porque sean contenedores multi-juego.
   - **8 "7-Zips" confirmado hueco real**: `converters/zip_extractor.py`
     solo importa `zipfile` (stdlib) — cero soporte de `.7z`, y no hay
     ningún `7z*.exe` en `tools/` (solo `adb.exe`/`chdman.exe`/`rclone.exe`).
     Con la regla del proyecto de "sin dependencias externas de runtime
     (solo stdlib)", la vía correcta sería bundlear `7za.exe` (freeware,
     mismo patrón que `chdman.exe`) e invocarlo por `subprocess`, no una
     librería Python (`py7zr` violaría la regla) — sin implementar,
     documentado como hueco.

**Dry-run de `POST /api/junk-delete` confirmado (2026-09-28)**: los 3.659
paths de `safe_delete` (extraídos del propio `paths` de cada categoría del
junk-scan, no de `files` — ese último viene truncado a 50 por categoría
para la respuesta) → `{"deleted": 3659, "failed": 0, "freed_bytes":
4925918329, "dry_run": true, "errors": []}`. Coincide exacto con lo medido
(3.659 archivos, 4,93 GB), 0 fallos.

**Borrado real ejecutado (2026-09-28), con confirmación explícita del
usuario**: mismo payload con `dry_run: false` → `{"deleted": 3659,
"failed": 0, "freed_bytes": 4925918329, "errors": []}`, idéntico al
dry-run. Verificado: `discard_to_trash()` (`utils/trash.py:29`) mueve cada
archivo a una carpeta `_descartados/` **hermana** (junto a su propio
padre, no un único directorio en la raíz) — soft-discard, deshacible
~30 días (`library.trash_purge_days`, `purge_trash()`). 4,93 GB
liberados de `safe_delete`. Quedan `misplaced` (2.176 archivos/13,87 GB,
mover con el motor de `ZIP-ROUTE-1`/`-3`) y `review` (237/16,18 GB) sin
tocar — ver arriba.

**`misplaced` aplicado (2026-09-28), con confirmación explícita del
usuario**: el mecanismo real disponible no es `ZIP-ROUTE`/`zip-route-apply`
(eso es solo arcade + colecciones) sino el `plan`/`apply` general de la app
(`GET /api/plan` → `POST /api/apply`) — bastante más amplio de lo
documentado arriba: **13.298 juegos matched en total** (no solo los 2.176
de `Unknown\`), de los cuales **1.555 "pending"** (movibles solos, sin
ambigüedad) y **4.119 "conflicts"** (mismo destino propuesto por 2+
orígenes, o destino ya ocupado con contenido distinto — `_do_apply()`,
`web/handlers/organize.py:124`, **nunca los toca**, solo procesa
`plan.pending`). Decisión del usuario: aplicar solo lo sin conflicto.
`POST /api/apply` real (con backup automático de `library_pc.db` antes de
tocar nada, `apply_repo.backup_database()`) → `{"renamed": 1554, "failed":
0, "skipped": 1, "saves_renamed": 8, "zips_extracted": 1, "conflicts":
4119}`. El único `skipped` fue una fila de BD obsoleta (`Digimon World 3
[U] [SLUS-01436].sub`, el archivo de origen ya no existe en disco — no es
un fallo real). Reversible vía `POST /api/undo-last-apply` si hiciera
falta. **Los 4.119 conflictos siguen sin resolver** — requieren revisión
caso a caso (mismo destino propuesto por 2+ orígenes o colisión con
contenido distinto), no automatizable con este mecanismo.

**`review` — intentado con `zip-route-apply`, real y verificado contra un
segundo junk-scan (2026-09-28), con confirmación explícita del usuario**:
`POST /api/zip-route-apply` (job "inbox", extract→match→renombrar→
organizar→limpiar) → `{"zips_to_inbox": 2172, "roms_scanned": 4341,
"matched": 3980, "renamed": 1136, "organized": 3301,
"duplicates_removed": 1036, "conflicts_unresolved": 4}`. Solo 2
`route_skipped` (`Hook.zip`/`Tetris.zip`, ya existían en `arcade\`, no
sobreescritos) y 4 `organize_errors` reales (mismo nombre/carpeta,
contenido distinto — intactos, revisar a mano: `Pokemon - Emerald Version
(USA, Europe).gba`, `Premier Manager 97 (Europe).bin`, `Snow Bros. - Nick &
Tom (Japan).bin`, `Twinkle Tale (Japan).bin`).

**Efecto real, medido con un junk-scan de después contra el de antes**:

| Bucket | Antes | Después | |
|---|---|---|---|
| `safe_delete` | 3.659 / 4,93 GB | 3.699 / 4,95 GB | +40 archivos nuevos (residuos expuestos por las extracciones) |
| `misplaced` | 2.176 / 13,87 GB | 1.650 / 10,52 GB | -526, organizados entre `apply` + `zip-route-apply` |
| `review` | 237 / 16,18 GB | **237 / 16,18 GB — exactamente igual** | confirma que estos 237 no eran resolubles por CRC/contenido con el catálogo ya cargado, la hipótesis original de "candidato a ZIP-ROUTE-1" no se sostuvo con datos reales |

**Total: 6.072/34,97 GB → 5.586/31,65 GB.**

**Segunda ronda de `safe_delete` aplicada (2026-09-28), con confirmación
explícita del usuario**: los 3.699 `safe_delete` de después de
`zip-route-apply` (incluye los 40 nuevos expuestos por las extracciones) —
dry-run (`{"deleted": 3699, "failed": 0, "freed_bytes": 4949875483}`) seguido
del borrado real, idéntico (`dry_run: false`), 0 fallos. **4,95 GB
adicionales liberados** (soft-discard, mismo mecanismo que la primera
ronda). **Total acumulado de `safe_delete` borrado hoy: 7.358 archivos,
~9,88 GB.**

**`review` investigado a mano (2026-09-28), 2 hallazgos reales antes de
llegar a los archivos en sí:**

1. **Bug real en el propio junk-scan: no excluye `_descartados/`**
   (`web/builders/folders.py:321`, `_excluded_dirs = {"saves", "bios",
   "android", "system volume information"}` — falta `_descartados`).
   `utils/trash.py` sí se protege contra esto (`_iter_trash_files()`, línea
   65-66, corta el `os.walk` con el comentario `# no anidar` en cuanto entra
   en una carpeta `_descartados`), pero esa misma protección nunca se aplicó
   al walker del junk-scan. Consecuencia real, verificada: **94 de los 120
   "ZIPs no-ROM" ya estaban dentro de alguna `_descartados/`** (descartados
   en sesiones anteriores), re-contados como basura activa en cada scan —
   por eso el bucket `review` salió "exactamente igual" antes/después de
   `zip-route-apply`, nada de eso era realmente tocable. Peor: repetir
   `junk-delete`/extracciones sobre contenido ya descartado crea
   `_descartados/_descartados/` anidado (**111 carpetas así confirmadas
   hoy en la biblioteca real**) — esos archivos quedan **invisibles para
   `purge_trash()`** (mismo corte de `os.walk` que los protege de
   re-listarse también les impide ser vistos si están un nivel más
   adentro), huérfanos para siempre sin limpiarse solos. Sin pérdida de
   datos (nada se borra de verdad), pero desperdicia espacio en disco.
   Recuento real filtrando `_descartados/` de las 4 categorías: **142
   archivos activos de verdad, no 237** (26 ZIPs no-ROM activos, 8
   7-Zips, 108 chips arcade, 0 del set arcade "otra versión" — ese único
   ítem también estaba ya en `_descartados`). Sin arreglar el walker
   todavía — documentado, candidato a tarea propia (`JUNK-SCAN-EXCLUDE-TRASH-1`
   o similar).
2. **Causa raíz real de por qué las 26 ZIPs Dreamcast activas nunca
   matcheaban**: no eran basura sin catalogar — **el catálogo entero de
   Dreamcast cargaba 0 entradas** por un bug de BOM en
   `_detect_dat_format()` (`catalog/catalog_loader.py:22-28`): abría con
   `encoding="utf-8"`, un BOM inicial (común en exports de Redump) quedaba
   pegado a `<?xml`, así que `startswith("<")` daba `False` y el DAT XML
   real se clasificaba como clrmamepro, sin ningún error visible. Afectaba
   a **9 catálogos reales** (18 archivos, `nointro/`+`redump/`): Dreamcast
   (1.420 juegos), Naomi, Naomi 2, Triforce, PC (SBI Subchannels), Wii U
   (Disc Keys), PlayStation (SBI Subchannels), PlayStation 3 (Disc Keys
   ×2) — **arreglado y mergeado hoy** (`fix/catalog-bom-detection`,
   `encoding="utf-8-sig"`, test `test_detects_xml_with_leading_bom`, 9
   catálogos verificados con entradas reales tras el fix).

   **Re-aplicado contra la biblioteca real (2026-09-28), con confirmación
   explícita del usuario**: `rommgr serve` reiniciado (parado el proceso
   viejo, `python -m rom_manager serve` de nuevo — necesario para cargar
   el código nuevo) y `POST /api/match` real sobre los 11.532 juegos sin
   resolver → `{"total": 11532, "matched_high": 0, "matched_low": 2,
   "unmatched": 11530}`. **Confirmado con datos reales**: `Jet Set Radio
   (Europe).zip` (una de las ZIPs Dreamcast activas del bucket "review")
   pasó de `canonical_title=NULL` a `canonical_title="Jet Set Radio
   (Europe)"`, `match_confidence="medium"` — el catálogo Dreamcast
   arreglado sí funciona en producción. Rendimiento modesto en esta pasada
   (solo 2 matches nuevos de 11.532): la mayoría de la cola restante
   parece genuinamente difícil de identificar (hacks, dumps no estándar,
   sin equivalente en ningún DAT) — sesiones anteriores ya habían agotado
   los matches fáciles antes de que este catálogo existiera de verdad, así
   que el fix no iba a desbloquear miles de golpe, pero sí corrige la
   identificación de cualquier contenido Dreamcast/Naomi/Naomi2/Triforce
   futuro de forma permanente. `SAGE-1` relanzado tras el `match` (cola
   17.634→16.937→15.681, sin errores).

`review` recontado sin `_descartados/`: **142 archivos reales (~15,1 GB)**
de los cuales una parte desconocida (Dreamcast + arcade Naomi/Naomi2/
Triforce) probablemente se resuelva sola en el próximo `match` con el
catálogo ya arreglado. Los 8 `.7z` siguen siendo el único hueco confirmado
sin solución disponible (formato no soportado) — **actualizado**, ver
`JUNK-7Z-SUPPORT-1`.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| JUNK-7Z-SUPPORT-1 | **Soporte `.7z` en el Inbox** — `converters/zip_extractor.py` solo importa `zipfile` (stdlib), cero soporte de `.7z`; sin `7z*.exe` en `tools/` | `src/rom_manager/converters/sevenzip_extractor.py` (nuevo), `config.py` (campo `sevenzip`, mismo patrón `_default_tool`/`_resolve_tool_path` que `chdman`/`adb`), `web/inbox_pipeline.py` (`_run_inbox_pipeline`, extracción junto a los `.zip`), `cli.py` (`rommgr decompress` extrae también `.7z`), `scripts/download-tools.ps1` (descarga 7-Zip desde GitHub `ip7z/7zip`, extrae el `.msi` con `msiexec /a` sin necesitar 7z para desempaquetarlo — sin huevo-o-gallina) | ✅ implementado 2026-09-29 — `extract_7z()`/`find_7z_files()`/`list_7z_members()` (parseo de `7z l -slt`), mismas garantías que `extract_zip()`: nunca sobreescribe (`-aos`), solo borra el origen si todos los miembros quedan confirmados en disco. **Mismo guard de sets multi-disco que `extract_zip()`** (`.cue`/`.gdi` entre los miembros → skip, "usa el conversor CHD") — añadido tras verificar contra los archivos reales de esta biblioteca (ver abajo), no estaba en la primera versión. 10 tests (`tests/test_sevenzip_extractor.py`, contra el `7z.exe` real de `tools/`, skip si no está presente). Suite completa 1469/1469, ruff+format limpios. **Sin arcade-CRC-detection para `.7z`** (a diferencia de `is_arcade_zip_container` para ZIP) — solo el guard por nombre de carpeta, documentado como límite conocido |

**Aplicado contra la biblioteca real (2026-09-29), con confirmación explícita del usuario** — primero un dry-run de `rommgr decompress "F:\Juegos Retro"` para localizar los `.7z` reales (13 en total, no solo 8: 8 en `Unknown\` + **5 en `PlayStation 2\`**, estos últimos ya colocados en su carpeta correcta con nombre canónico, nunca contados por el junk-scan porque no son "review" — simplemente nadie los había extraído). Inspeccionado el contenido de cada uno con `7z l -slt` antes de tocar nada: **9 de los 13 son sets Dreamcast/Naomi multi-track** (`.gdi` + varios `.bin` de audio/datos) — `Crazy Taxi`, `Jet Set Radio`, `Marvel vs. Capcom`, `Mortal Kombat Gold`, `Resident Evil - Code Veronica (Disc 1)`, `Sonic Adventure` (Europe/USA), `Sonic Adventure 2`, `Street Fighter III - 3rd Strike` — el guard nuevo los saltó correctamente a los 9, tal cual se diseñó. **4 son `.7z` de un solo `.iso` de PS2** (`Dragon Ball Z - Budokai 3`, `Kingdom Hearts`, `Kingdom Hearts II`, `Metal Gear Solid 2`) — aplicados de verdad (`extract_7z_directory(..., delete_source=True)`, script de sesión acotado a `Unknown\`+`PlayStation 2\`, sin tocar el resto de la biblioteca ni los `.zip`): 3 resultaron ser contenedores completamente redundantes (el `.iso` ya existía en disco, subido por separado el 2026-09-15) — soft-discard a `_descartados/`, cero archivos nuevos; 1 (`Dragon Ball Z - Budokai 3`) extrajo un `.iso` nuevo y distinto del ya existente (`Dragon Ball Z - Budokai 3 (USA).iso`, 4,66 GB — la copia previa era "(Greatest Hits)", posible duplicado real a revisar con `DUP-REGION-2`/matcher, sin decidir todavía) antes de descartar el `.7z`. Los 9 sets Dreamcast/Naomi restantes se retoman a continuación en `GDI-ORGANIZE-1` — **corrección**: no hace falta `chdman`/CHD para ellos, el `.gdi`+`.bin` crudo ya es un formato de primera clase en este pipeline (`move_disc_set_to_subfolder`, `_DISC_SUBFOLDER_PLATFORMS`, RA hash vía `ra_hash_saturn_dreamcast.py`) — CHD es opcional (ahorro de espacio), no un requisito |

### GDI-ORGANIZE-1 (continuación) — `/api/review-queue` no responde en tiempo razonable contra la biblioteca real de hoy (hallazgo 2026-09-29)

Al intentar relanzar la limpieza de duplicados de la Anbernic (petición del usuario, pendiente de una sesión anterior sin cerrar) — 3 intentos reales de `GET /api/review-queue` (sin parámetro `repo=`, pese a que la UI antigua lo sugería: el endpoint siempre construye la cola contra `repository` PC + `repo_android` juntos, `web/handlers/duplicates.py:165`, `_build_review_queue`) **no devolvieron respuesta**: dos con timeout explícito de 60s/90s (`curl --max-time`, error 28 = timeout, no error de conexión), uno en background que tardó ~35 min y solo terminó porque maté el proceso `curl` a mano. Descartado que fuera el job `ra_check` (llevaba corriendo en paralelo, cancelado a mitad de la investigación) — el hang persistió igual después de pararlo. La CPU del proceso del servidor no se pudo comparar en dos instantes de forma concluyente (medición de sesión insuficiente, no una prueba real).

**Hipótesis más probable, sin confirmar todavía**: no necesariamente un cuelgue real — `_review_groups_for_repo`/`_build_review_queue` (`web/builders/duplicates.py`) construye varias uniones (crossfmt/sha1/región/disc_hash) sobre el PC + Android combinados; el PC pasó hoy de su tamaño habitual a **27.874 ROMs / 11.510+ ya-correctos** tras el rescan de esta sesión — si alguna de esas uniones es O(n²) o peor sobre el título normalizado, a esta escala podría tardar decenas de minutos de verdad, no estar bloqueado. Sin perfilar, así que sigue siendo hipótesis. Cualquiera que sea la causa, **un endpoint de UI que no contesta en 35+ minutos es un problema real de UX/rendimiento** para una biblioteca de este tamaño, no solo un contratiempo de esta sesión.

**✅ Causa raíz real encontrada y arreglada (2026-09-29, misma sesión, retomada tras el mensaje del usuario "no, ahora")**: perfilado `_review_groups_for_repo` directamente (sin HTTP, `cProfile` contra la BD PC real) — 245 s para el repo PC solo, nada patológico algorítmicamente (nada de O(n²) real). El verdadero bloqueo: **`ra_disc_hash_cache.get_psx_disc_hash()` encontró `psx_disc_hashes.json` corrupta** (`json.decoder.JSONDecodeError` real en el log) — con la caché ilegible, cada comparación de hash de disco PSX/GameCube/Wii recalculaba de cero vía `chdman` (~16,6 s cada extracción de `.chd` real, 6 de esas en el perfil = 100 s solo ahí) en vez de una lectura de caché instantánea.

**Causa de la corrupción, confirmada por el patrón temporal**: `_save()` (`retroachievements/ra_disc_hash_cache.py:44`) escribía con `Path.write_text()` directo, **no atómico** — el job `ra_check` (corriendo en paralelo toda la sesión) y mis propios intentos de `review-queue` escriben/leen el mismo archivo sin ningún lock; dos escrituras solapadas dejan un JSON a medio escribir. Mismo patrón de riesgo que `JOBS-SQLITE-LOCK-1` pero para un archivo JSON en vez de SQLite. **✅ arreglado**: `_save()` ahora escribe a un temporal y usa `os.replace()` (atómico en POSIX y Windows) — un lector nunca puede ver un archivo a medias. 4 tests nuevos (`tests/test_ra_disc_hash_cache.py`). Suite completa 1476/1476 en verde.

**Verificado en real tras el fix**: `GET /api/review-queue` real (con la caché ya regenerada, 1256 entradas válidas) → **200 OK en 28,7 segundos** (antes: sin respuesta en 3 intentos, uno de 35 min matado a mano). Sigue habiendo un coste real no-patológico de ~113 s (en el perfil PC-solo) en `extract_internal_id` (`MATCH-HEADER-1`, abre cada archivo `.nds`/`.gba` real de la biblioteca para leer su código interno) — candidato a cachear igual que los hashes de disco si se quiere bajar más, pero no bloqueante, sin tocar hoy.

**Resultado del pedido original (dedup PSX tipo "Final Fantasy VII, quedarse con la copia con logros")**: revisada la cola real (7.745 grupos, 55,46 GB desperdiciados combinando PC+Anbernic) — **no hay ningún grupo "Final Fantasy VII" de PSX pendiente** en `review-queue` (solo un romhack de NES con ese nombre, 2 copias, y un par no relacionado de **Final Fantasy VIII** PSX — `Final Fantasy VIII (Europe).chd` vs `(USA) (Disc 1).chd`, sha1 idéntico, 468 MB desperdiciados, **ninguna de las dos marca soporte RA** en la cola — no hay copia "con logros" que preferir en este par tal cual está hoy).

**El usuario aclaró: se refería a la Anbernic directamente, no a la cola de duplicados** — tiene sentido, `_review_groups_for_repo` **excluye a propósito** las variantes regionales PSX multi-disco de la unión difusa por región (comentario en `web/builders/duplicates.py:1019-1037`, el propio ejemplo documentado ahí es "18 discos reales de Final Fantasy VII fusionados por error" — la razón exacta por la que este caso es invisible para la herramienta). Revisado `psx/` en la Anbernic real por ADB — **más lío del recordado, no "3 copias" limpias**:

- `Final Fantasy VII (Disc 1/2/3).bin/.cue` — sin etiqueta de región, dump propio (tamaños ligeramente distintos a los demás).
- `Final Fantasy VII (Europe).cue` + `(2).cue` + `(3).cue` — **rotos**: apuntan a `"...(Spain)...(v1.1).bin"`, pero el `.bin` real se llama `(Rev 1).bin` — no coincide el nombre, nunca cargarían. No son una copia real, son sheets basura.
- `Final Fantasy VII (Spain) (Disc 1/2/3) (Rev 1).bin` — sin ningún `.cue` válido que los referencie (solo los rotos de arriba los mencionaban).
- `Final Fantasy VII (USA) (Disc 1/2/3)` — tiene **tanto** `.bin`+`.cue` crudo **como** `.chd` ya convertido (fecha posterior) — ~2 GB de crudo redundante con su propio `.chd`, sin limpiar tras la conversión.
- `Final Fantasy VII (USA) (Install Disc) (Rerelease).chd` — disco de instalación PC aparte, no es el juego.

**Aplicado, con confirmación explícita del usuario (2026-09-29)**: borrados por ADB los 3 `.cue` rotos de "Europe" (`rm` directo — Android no tiene papelera, irreversible, pero eran sheets sin ningún `.bin` real al que apuntar, cero riesgo de contenido jugable). Verificado que ya no están en el dispositivo.

**Crudo USA vs `.chd` — verificado y resuelto**: descargados los 3 discos completos (`.bin`+`.cue`+`.chd`, ~3,4 GB) a esta máquina para verificar antes de borrar nada, mismo patrón que `CHD-DELETE-NO-VERIFY-1`/`convert_to_chd(delete_source=True)` ya usa: `chdman verify` (integridad del `.chd`) + comparar el hash RA (`compute_psx_ra_hash`) del `.cue`/`.bin` crudo contra el del `.chd`. **Los 3 discos verifican perfecto** — `chdman verify: ok=True` e ídem hash RA exacto en los 3 (`665933b4...`/`22e74595...`/`f0bab449...`, origen y `.chd` coinciden byte a byte en contenido jugable). Borrados por ADB los 6 archivos crudos (`.bin`+`.cue` × 3 discos) de la Anbernic — confirmado que solo quedan los `.chd` ya verificados. **~2 GB liberados**, cero riesgo (contenido confirmado idéntico antes de borrar).

**Spain y el dump sin etiqueta — investigado y resuelto**: descargados los 6 `.bin` restantes (~4,3 GB) y comparado el hash RA de cada uno (`compute_psx_ra_hash`) contra el hash USA ya confirmado — **los 3 dumps (USA/Spain/sin etiqueta) tienen hash distinto entre sí en los 3 discos**: no son duplicados byte-a-byte del mismo contenido, son ediciones/revisiones genuinamente distintas (Spain casi seguro la edición europea traducida; el dump sin etiqueta no coincide con ninguno de los otros dos, identidad exacta sin determinar). Con confirmación explícita del usuario ("el que juego es el de USA, porque tiene logros" — no necesita las otras ediciones), **borrados por ADB los 6 archivos** (3 `.bin` de Spain + 3 `.bin`/`.cue` sin etiqueta). Verificado: solo quedan los 3 `.chd` de USA + el install disc. `psx/Final Fantasy VII` queda limpio del todo — de 4 ediciones + 3 sheets rotos a solo la USA verificada.

**Además, mientras se investigaba**: resueltos los 2 duplicados Dreamcast que había dejado pendientes arriba (`Jet Set Radio` y `Sonic Adventure (Europe)`) — verificado por SHA1 que las 3 pistas de `Jet Set Radio` (`.gdi` del `.7z` vs `.cue` del `.zip`) son **byte a byte idénticas**; sin diferencia real de contenido, se conserva el `.gdi` (formato que este proyecto sí soporta de fondo para organizar/renombrar/hashear Dreamcast — el soporte `.cue` coge el track 1, no el de datos, ver `ra_hash_saturn_dreamcast.py:154` `_first_cue_bin`). `.zip`/`.cdi` descartados a `_descartados/`, `.gdi` movido a `dreamcast\<Título>\` y enviado a la Anbernic (mismo mecanismo `send_selected` que los otros 6, 4 archivos cada uno, 0 errores).

**Hallazgo colateral verificando esto**: `_CdImage._detect_geometry()` (`retroachievements/ra_cd_image.py:44-69`) calcula mal `header_size` para un sector MODE1 de 2352 bytes cuando cae en su rama de respaldo por módulo exacto (línea 61-62: `if size % 2352 == 0: return 2352, 24, 0` — `24` es el header de MODE2 FORM1, un MODE1 real necesita `16`). Confirmado con el `.bin` de track 3 real de `Jet Set Radio`: el magic `"SEGA SEGAKATANA "` vive en el byte 16 exacto (sync 12 + header 4), pero con `header_size=24` la lectura cae 8 bytes tarde y el hash de logros de Dreamcast devuelve `None` incluso para un dump limpio y completo. Afecta potencialmente a cualquier dump MODE1 de PSX/Saturn/Dreamcast que no tenga un PVD ISO9660 detectable en el sector 16 (la ruta de detección primaria). **Arreglado 2026-10-02** (rama `fix/ra-cd-image-mode1-short-track`): el fallback ahora relee el sector 0 (garantizado si `size>0`) y mira el byte de modo real del header (offset 15, justo tras sync+MSF) en vez de asumir siempre `header_size=24`; si no hay patrón de sync ni en sector 16 ni en sector 0, mantiene el default antiguo (24) por no tener ninguna evidencia positiva de MODE1. 3 tests nuevos (`tests/test_ra_cd_image.py`): MODE1 corto detecta 16, MODE2 corto detecta 24, imagen sin evidencia mantiene el default. Suite PSX/Saturn/Dreamcast completa en verde (19 pass).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| GDI-ORGANIZE-1 | Ver descripción arriba | `planner/operation_planner.py:195-201` (bug 1), `converters/chd_converter.py:237-268` (bug 2) | ✅ **ambos bugs arreglados** — bug 2 el mismo día; bug 1 arreglado 2026-09-29 (PR #377, rama `fix/gdi-organize-1-subfolder-platform-target`): `build_plan()` acepta `library_root: Path \| None = None` (retrocompatible), con él calcula el destino de una plataforma subfolder directo como `library_root/<slug>/<carpeta>/<archivo>` en vez de adivinar por `source.parent`/`source.parent.parent` — conectado en los 7 puntos de llamada reales (`cli.py` plan/apply, `web/builders/library.py::_build_plan`, `web/handlers/organize.py::_do_apply`, `web/inbox_pipeline.py` ×2, `services/ra_duplicates_service.py`, `web/builders/duplicates.py`). 4 tests nuevos, suite 1488/1488. Jet Set Radio y Sonic Adventure Europe ya resueltos el mismo día (ver arriba); solo queda `Mortal Kombat Gold` sin match (causa no investigada) |
| CHD-CLEANUP-1 | Generalizar la limpieza de FFVII: 195 títulos PSX reales en la Anbernic con `.chd` convertido y su `.bin`/`.cue` crudo sin borrar tras la conversión | `converters/chd_cleanup.py` (nuevo), `cli.py` (`rommgr clean-redundant-chd <ruta-android> [--apply]`) | ✅ **implementado y aplicado 2026-09-29** (PR #376, mergeado en `feature/junk-7z-support-1`) — agrupa por (directorio, stem exacto) `.cue`+`.chd`, verifica `chdman verify` + hash RA del crudo contra el `.chd` antes de borrar nada; deliberadamente NO cruza ediciones/regiones distintas (decisión humana aparte). 2 bugs reales corregidos tras review de Claude en el PR (extracción truncada de `.7z` tratada como completa + charset no-ASCII en `sevenzip_extractor.py`, ver `JUNK-7Z-SUPPORT-1`). Ejecutado real contra `psx/` en la Anbernic (RG556006101273): 19 candidatos encontrados, **17 verificados y borrados (11,49 GB liberados, 0 errores)**, 2 saltados de forma segura sin tocar nada (`Lunar - Silver Star Story Complete (USA) (Disc 2)` y `Guilty Gear (Europe)`: sus `.cue` referencian un `(Track N).bin` que no existe en el dispositivo — sheets rotas, mismo patrón que las de FFVII). Verificado en el dispositivo real por ADB que solo quedan los `.chd`. Quedan ~176 títulos sin auditar del total de 195 (el resto de la biblioteca Android, no solo `psx/` explorado hoy) — candidato a repetir contra el resto de carpetas/plataformas en otra sesión |
| ANDROID-DUP-GBA-1 | Petición del usuario: comprobar si la lógica de duplicados detecta bien los legacy `[E]`/`[U]`/`[J]` de GBA en la Anbernic (ejemplo dado: "dos Pokémon Pinball") | `web/builders/duplicates.py::_review_groups_for_repo` (motor, sin tocar), `services/ra_duplicates_service.py::resolve_duplicate_ra` (aplicado) | ✅ **verificado y aplicado 2026-09-29** — la lógica de detección funciona bien: de 92 volcados legacy `[E]`/`[U]`/`[J]` en `gba/`, **82 ya estaban correctamente agrupados por SHA1** en la cola de revisión (incluido el caso exacto de Pokémon Pinball — mismo SHA1 `b8b7881e...` entre `RZ [E].gba` y `(Europe)...gba`); los 10 restantes no son falsos negativos (contenido genuinamente distinto pese al mismo tamaño, o sin ninguna copia canónica en la biblioteca contra la que comparar — verificado caso a caso). **146 grupos GBA totales en la Anbernic, 1,65 GB** — backup de `library_android.db` antes de tocar nada, **137 grupos aplicados de verdad por ADB: 138 archivos descartados, 0 errores, 1,53 GB liberados**, verificado en el dispositivo real (`Pokemon Pinball RZ [E].gba` ya no existe, solo sus `.sav`/`.sgm`). **9 grupos excluidos a propósito** — ver `ANDROID-DUP-SORT-TIEBREAK-1` abajo, el bug que los afecta |
| ANDROID-DUP-SORT-TIEBREAK-1 | Hallazgo real durante `ANDROID-DUP-GBA-1`, ampliado a petición del usuario a **todas las plataformas** de la Anbernic (2026-09-29): el desempate de "recomendado" en `_review_entry_sort_key` cae a comparar el nombre de archivo como texto plano cuando todos los criterios tipados empatan (caso normal en un duplicado SHA1 exacto) — un espacio (`0x20`) ordena antes que un punto (`0x2E`), así que cualquier sufijo entre paréntesis/corchetes ("... (Japan) [T-En...]", "... (USA) (conflicto-inbox...)") gana alfabéticamente al nombre limpio sin que eso tenga ningún sentido semántico | `web/builders/duplicates.py:313-410` (`_review_entry_sort_key`, nuevo `variant_tier`) | ✅ **arreglado 2026-09-29, a petición del usuario, misma sesión** — nuevo `variant_tier` insertado justo antes del fallback de nombre: reutiliza `is_non_canonical_variant()` (ya usada en otro sitio del código para el mismo tipo de señal, `[T+`/`[T-`/`(hack`/`subset`/`[h\d*]`) + un check aparte para `conflicto-inbox` (artefacto del Inbox, no relacionado con traducciones/hacks). Deliberadamente NO toca `(Beta)`/`(Proto)`/`(Demo)`/`(Sample)` — confirmado con datos reales que esas etiquetas describen contenido genuino. 4 tests nuevos (`tests/test_builders_duplicates.py`): 2 confirman que el sort key ahora penaliza los dos patrones reales encontrados, 1 confirma que `(Beta)`/`(Proto)` NO se penalizan, 1 end-to-end reproduciendo el caso real de Mother 3 a través de `_build_review_queue`. Suite completa 1492/1492, ruff+format limpios. Metodología (investigación original, antes del fix): recorrida la cola de revisión real completa (`_build_review_queue`) agrupada por plataforma, filtrado a grupos con SHA1 idéntico donde el "recomendado" lleva `[T-` o `conflicto-inbox` y existe una alternativa sin esa etiqueta en el mismo grupo — cada caso verificado por SHA1 real, no por sospecha. Un barrido más amplio con `(Beta)`/`(Proto)`/`(Demo)`/`(Sample)` dio **falsos positivos**: esas etiquetas sí describen el contenido real (mismo dump beta/proto, solo con nombre No-Intro correcto vs. un volcado legacy mal escrito) — descartadas del hallazgo, no es el mismo bug.<br>**GBA**: 6 parches `[T-...]` falsos (`Mother 3`, `Oriental Blue - Ao no Tengai`, `Magical Vacation`, `Dragon Quest Monsters - Caravan Heart`, `Super Robot Taisen R`, `Tomato Adventure`) + 3 `(conflicto-inbox 2026-08-13)` (`Boktai 2`, `Crash Nitro Kart`, `Klonoa - Empire of Dreams`) — de 146 grupos totales, excluidos de la aplicación real en `ANDROID-DUP-GBA-1`.<br>**NES**: 9 parches `[T-...]` falsos, mismo patrón exacto (SHA1 idéntico al original japonés sin traducir): `Big Strategy Pachinko`, `Mitsume ga Tooru`, `Perman`, `Sweet Home`, `Fire Emblem Gaiden`, `Brave Fighter of the Sun - Fighbird`, `Hinotori - Houou Hen`, `Famicom Wars`, `Family Trainer 8`.<br>**Game Gear**: 1 caso, `Sylvan Tale (Japan) [T-En by Aeon Genesis v1.01].gg` = mismo SHA1 que `Sylvan Tale (Japan).gg` sin traducir.<br>**Aplicado el resto (2026-09-29, mismo backup previo de `library_android.db`)**: filtro conservador (excluye cualquier grupo cuyo "recomendado" contenga `[T-`/`conflicto-inbox`, sin exigir que exista alternativa limpia — más estricto que el hallazgo exacto, así que excluyó 20 grupos en total en vez de los 10 confirmados, dejando también sin tocar algunos casos ambiguos tipo "dos parches distintos del mismo hack"). **NES: 1563/1582 grupos aplicados, 1865 filas borradas, 0,40 GB liberados. Game Gear: 183/184 grupos aplicados, 184 filas borradas, 0,07 GB liberados. 0 errores en ambos.** Verificado por dos vías: `ls` real en el dispositivo confirma que los 10 casos `[T-...]` originales siguen intactos (ambas copias), y el recuento de filas en `library_android.db` coincide exacto con lo aplicado (NES 4971→3106 = −1865, Game Gear 939→755 = −184).<br>**Resto de plataformas con datos en el dispositivo, sin ningún caso del bug** (0 sospechosos tras el mismo barrido): Game Boy Color (1268 grupos, 1,95 GB), PlayStation (124 grupos, 14,33 GB), Sega Mega Drive (65 grupos, 0,12 GB — los 2 casos `(Beta)`/`(Proto)` del barrido amplio son correctos, no bug), Game Boy (25 grupos, 0,01 GB), SNES (5 grupos), Nintendo 64DD (1 grupo). Arcade, Nintendo DS, Master System, PlayStation 2, Nintendo 64, PSP, Atari 2600, GameCube, PC Engine y Famicom Disk System no tienen ningún grupo de duplicados con entradas en el dispositivo ahora mismo.<br>**Aplicado tras el fix (2026-09-29, mismo backup previo de `library_android.db`)**: reconstruida la cola real con el `variant_tier` ya en producción — confirmado primero en seco que los 16 casos falsos ahora recomiendan el nombre limpio (`Mother 3 (Japan).gba`, `Sylvan Tale (Japan).gg`, etc.), sin exclusión manual esta vez (el propio motor ya elige bien). **29 grupos restantes en GBA/NES/Game Gear (los 20 previos + 9 nuevos que solo aparecieron al dejar de excluirlos a mano), 33 archivos descartados, 0 errores, 0,119 GB liberados** (GBA 0,114 GB, NES 0,005 GB, Game Gear 0,001 GB — números pequeños porque la mayoría de esos grupos son el propio archivo `[T-...]`/`conflicto-inbox` de 1 sola entrada extra, no discos completos). Verificado en el dispositivo real por ADB: `Mother 3 (Japan) [T-En...].gba` y `Sylvan Tale (Japan) [T-En...].gg` ya no existen, solo las copias limpias. Con esto, `ANDROID-DUP-GBA-1`/`ANDROID-DUP-SORT-TIEBREAK-1` quedan completamente cerrados para las 3 plataformas investigadas |

### RA-DEDUP-UNSAFE-1 — Borrar duplicados "sin soporte RA pero con alternativa" no se puede automatizar (hallazgo 2026-09-02)
> **Estado (revisado 2026-10-20):** ✅ cerrada — decisión tomada: no implementar el auto-borrado (documentado como no seguro)

A petición del usuario, se intentó borrar automáticamente los ROMs sin soporte RA cuando la versión
con logros ya está en la misma biblioteca (no solo "existe según RA"). Con el criterio más
conservador posible (misma unidad + mismo tamaño de fichero + sin palabra clave de hack/traducción
en el nombre) **igual aparecieron falsos positivos reales**: `deer hunter.bin` (ver
`CATALOG-MATCH-BUG-1` arriba), `show do milhao volume 2 (bra) (alt).bin` (etiqueta `(alt)` de
No-Intro = dump alternativo preservado a propósito, no basura), y varios más con mismo tamaño pero
MD5 distinto sin garantía real de ser el mismo contenido. Un primer intento sin restringir a "misma
unidad" habría borrado 7 ROMs de N64 de `H:\ROMs` (`Super Mario 64`, `Donkey Kong 64`...) usando
como excusa que `E:\` tenía la misma ROM en formato `.z64` (mismo juego, solo orden de bytes
distinto) — la Anbernic se habría quedado sin esos juegos jugables localmente. Todo restaurado
antes de que el usuario lo confirmara, nada se perdió.

**Conclusión: no implementar borrado automático de este tipo.** Después de `resolve-duplicates`,
cualquier pareja que comparta título canónico pero no SHA1 es, por definición, contenido distinto
de verdad (aunque a veces trivial) — distinguir "diferencia trivial" de "traducción que hay que
conservar" requiere abrir el fichero, no hay atajo fiable. El listado completo (204 candidatos)
queda en `.rommgr/ra_no_support_alternative.csv` (fuera del repo) para revisión manual del usuario.

| ID | Task | Notas |
|----|------|-------|
| RA-DEDUP-UNSAFE-1 | No implementar auto-borrado de "duplicado sin RA con alternativa en biblioteca" — documentado que no es seguro ni con el criterio más conservador probado. Si se quiere una herramienta de ayuda, debería presentar los pares candidatos para confirmación manual uno a uno (con tamaño, MD5 y ambos nombres visibles), nunca borrar sin esa confirmación | ⚪ decisión tomada, no implementar automatización |

---

### ANDROID-FDS-CLEANUP-1 — Limpieza de `fds/` verificada por SHA1: 0 bytes de contenido único, todo duplicado o mal ubicado (implementa la conclusión de `ANDROID-DUP-3`) → #TBD
> **Estado (revisado 2026-10-20):** ✅ cerrada — ejecutado y verificado 2026-09-19 en la RG556

**✅ Ejecutado 2026-09-19** directamente sobre la RG556 vía ADB (`adb shell
rm`/`mv`, sin pasar por `rommgr plan`/`apply` — no existe hoy un flujo de la
herramienta para operaciones ad hoc sobre `library_android.db`, ver
`ANDROID-ORGANIZE-ADB-1`; toda la evidencia de verificación por SHA1 queda
documentada en `ANDROID-DUP-3`):

1. **Borrados** 6 ZIPs regionales (`Balloon Fight (Japan) (En) (Proto).zip`,
   `Ice Climber (Japan) (En) (Disk Writer).zip`, `Metroid (Japan) (Rev
   1).zip`, `Super Mario Bros. (Japan) (En).zip`, `Super Mario Bros. 2
   (Japan) (En).zip`, `Super Mario Bros. 2 (USA) (Rev 1).zip`) — SHA1
   idéntico confirmado contra el `.nes`/`.fds` ya suelto en la misma carpeta.
2. **Borrados** los 10 volcados de chip sueltos (`400-*.fse/.10l/.15l/.5l/.12l/.17l`,
   `mds-gn chr e.u4`, `mds-gn prg e.u7`, `rp2c04-0003.pal`) — SHA1 idéntico
   confirmado contra el contenido interno de `Goonies...zip`/`TwinBee...zip`.
3. **Movidos** `Goonies (Japan) (Disk Writer).zip` y `TwinBee (Japan) (En)
   (Disk Writer).zip` a `arcade/mame/` — son ROM arcade MAME (Nintendo VS.
   System) legítimos, no basura ni contenido de FDS. Verificado que no
   chocaban con nada ya existente (`arcade/fbneo/vsgoonies.zip` es un `.nes`
   convertido para FBNeo, contenido distinto byte a byte; `arcade/mame/twinbee.zip`
   es el TwinBee normal no-VS, y `arcade/fbneo/twinbeeb.zip` es otro bootleg
   parcialmente solapado pero no idéntico — ningún nombre de fichero chocaba)
   y llegada confirmada con `ls -la` post-mv.
4. **Borrados** los 2 `.fds` duplicados de `fds/` (quedan en `Famicom Disk
   System/`, verificado intacto tras el borrado) y los 5 `.nes` duplicados
   de `fds/` (quedan en `nes/`, verificado intacto tras el borrado) — SHA1
   idéntico confirmado en ambos casos.
5. `gamelist.xml` sin tocar (metadata de frontend, fuera de alcance).

**Resultado verificado con `ls -la` tras la limpieza**: `fds/` solo contiene
`gamelist.xml` (3364 bytes) — 0 contenido propio, tal como predecía el
análisis. `Famicom Disk System/` conserva sus 2 `.fds`, `nes/` conserva las
5 copias canónicas, `arcade/mame/` tiene ahora `Goonies...zip` y
`TwinBee...zip`. 0 pérdida de datos, 23 archivos borrados + 2 movidos.

Pendiente: PR a `develop` con el commit de documentación ya hecho en
`fix/android-fds-cleanup` (`68a4563`) — confirmar con el usuario antes de
mergear, como de costumbre | Evidencia SHA1 completa en `ANDROID-DUP-3` |
✅ ejecutado y verificado 2026-09-19

---

### GBA-DUAL-FOLDER-1 — `Game Boy Advance/` y `gba/` son dos carpetas activas paralelas con 881 títulos duplicados (hallazgo 2026-09-14, máquina "Ruben", `F:\Juegos Retro`)
> **Estado (revisado 2026-10-20):** ✅ cerrada — limpiado y purgado 2026-09-15

Encontrado al preparar el envío de GBA a la Anbernic. `F:\Juegos Retro` tiene
**dos** carpetas con contenido GBA real (no confundir con `GBA-MISPLACED-1`,
que era sobre archivos de OTRAS plataformas coladas en `gba/` en la otra
biblioteca — aquí ambas carpetas son GBA legítimo): `Game Boy Advance/` (985
archivos, 7,5 GB, nombrado canónico) y `gba/` (1054 archivos, 11,9 GB, slug
en minúsculas — mismo patrón que usan RetroBat/EmulationStation, ambos
instalados en este mismo disco `F:\`). Ambas están indexadas bajo el mismo
`platform='Game Boy Advance'` en `library_pc.db` (2037 filas totales), y
**881 `canonical_title` distintos existen en ambas carpetas a la vez** —
probablemente `gba/` es la carpeta legada de antes de que este proyecto
organizara la biblioteca en carpetas de nombre canónico, nunca limpiada
después. No bloquea el envío de hoy (`filter_duplicate_winners`, ya genérico
por plataforma, colapsa correctamente estos duplicados antes de enviar por
RA), pero es 11,9 GB de posible redundancia real en el PC sin confirmar si
`gba/` tiene algo que `Game Boy Advance/` no tenga (173 títulos exclusivos de
`gba/`, sin verificar si son copias con otro nombre o contenido genuino
distinto) | `F:\Juegos Retro\gba\` vs `F:\Juegos Retro\Game Boy Advance\` |
✅ limpiado y purgado 2026-09-15 (diario Día63) — reutilizado
`filter_duplicate_winners()` (mismo motor que el envío GBA→Anbernic) para
identificar ganador/perdedor: 898 duplicados reales (11,57 GB) descartados a
`_descartados/` (reversible), y luego purgados de verdad a petición
explícita del usuario ("purga descartados, ya que son juegos repetidos") —
900 archivos, 11,58 GB (incluye 2 más antiguos de la misma carpeta). La
sospecha de que el patrón afectaba a más plataformas se confirmó: ver
`PS2-DUAL-FOLDER-1` y `DUALFOLDER-12` (11 pares más, resueltos 2026-09-17) |

### PS2-DUAL-FOLDER-1 — `organize-source` crea un segundo `ps2/` en vez de usar `PlayStation 2/` ya existente (hallazgo 2026-09-15, máquina "Ruben", `F:\Juegos Retro`)
> **Estado (revisado 2026-10-20):** ✅ cerrada — resuelto, decisión 2026-09-15

Plan de implementación (medición de las 11 carpetas duplicadas restantes +
pasos) en `.claude/roadmaps/archivo/12-dual-folder-title-case-slug.md`, junto con
`GBA-DUAL-FOLDER-1`.

Confirma la predicción de `GBA-DUAL-FOLDER-1` ("verificar si hay pares
`ps2/`+`PlayStation 2/`"). Al organizar 21 juegos de PS2 encontrados sin
identificar en `Unknown\` (Kingdom Hearts, Kingdom Hearts II, GTA San Andreas,
Metal Gear Solid 2, Grandia II/III, Gradius V, Dark Cloud, Shadow Hearts, Dead
or Alive 2, Street Fighter III 3rd Strike — todos con `canonical_title`
poblado, `platform` seteado a mano vía `CatalogMatcher` directo tras un
cuelgue del job `match` general, ver más abajo), `rommgr organize-source
--apply` los movió (y renombró a su nombre canónico) a `F:\Juegos
Retro\ps2\` — carpeta que hasta hoy solo tenía un `media/` vacío — en vez de
`PlayStation 2\`, donde ya viven los otros 26 juegos de PS2 del PC.

**Causa raíz, no es un bug**: `web/handlers/system.py:34`
(`_ES_PLATFORM_FOLDERS["PlayStation 2"] = "ps2"`) es el mapeo que usa
`inbox_pipeline.py::_platform_folder_name()` (línea 40-43) para decidir dónde
organiza el Inbox — deliberadamente el slug en minúsculas que reconocen
RetroArch/EmulationStation (mismo criterio que ya usa `canonical_rel_posix()`
en el cable-sync tras `CABLE-ROOT-1`). La carpeta `PlayStation 2\` (Title
Case) con los 26 juegos existentes **no la creó este proyecto** —
`operation_planner.py::build_plan()` solo renombra el archivo dentro de su
carpeta actual (`target = source.parent / new_filename`, línea 181), nunca
mueve entre carpetas de plataforma — así que es una carpeta legada de antes
de esta herramienta, igual que `Game Boy Advance\` en `GBA-DUAL-FOLDER-1`.
El Inbox siempre va a preferir el slug Android; cualquier carpeta legada
Title Case queda huérfana y nunca vuelve a recibir contenido nuevo del
pipeline salvo consolidación manual.

**Corregido en caliente hoy** (sin cambiar código): los 21 archivos movidos a
mano de `ps2\` a `PlayStation 2\` (`shutil.move`, sin conflictos de nombre)
para mantener consistencia con el resto de la biblioteca PS2 del PC, y
`rommgr scan` re-corrido para actualizar `source_path` en la BD | `ps2\`
(vacío tras la consolidación, solo queda `media/`) vs `PlayStation 2\` (ahora
47 juegos) | `web/handlers/system.py:34` (`_ES_PLATFORM_FOLDERS`),
`web/inbox_pipeline.py:40-43` (`_platform_folder_name`),
`planner/operation_planner.py:181` (`build_plan`, nunca mueve entre
carpetas) | ✅ resuelto — decisión tomada 2026-09-15 (el slug Android es el
canónico también en el PC) y ejecutada en `DUALFOLDER-12` (2026-09-17): los
11 pares restantes consolidados + guard `_platform_folder_name()` en el
Inbox para que no vuelva a pasar en silencio con una plataforma futura |

### CATALOG-MATCH-SUBSET-1 — `_match_by_title()` no comprobaba `is_non_canonical_variant()`, asignando el `canonical_title` del original a hacks/parches de traducción (hallazgo 2026-09-17/18, máquina "Ruben", `F:\Juegos Retro`) → rama `fix/catalog-match-subset-hack`
> **Estado (revisado 2026-10-20):** ✅ cerrada — arreglado en fix/dup-winners-non-canonical-guard (2026-09-18)

Investigando un aviso del usuario ("Pokemon Fire Red ahora es el Professor
Oak Challenge, los logros son peores, también en la Anbernic"). Verificado
por hash MD5 que los `.gba` reales de Fire Red **no estaban tocados** ni en
PC ni en Anbernic (coinciden con los hashes conocidos del original) — el
hack nunca llegó al dispositivo, seguía sin organizar en `Unknown\`. El
Charizard negro en los logros de la Anbernic no se explica por nada de esta
biblioteca (probable caché de badges del lado RetroArch/RA, fuera del
alcance de esta herramienta).

Causa raíz real encontrada: `catalog/matcher.py::_match_by_title()` (Pass 2,
fallback por título cuando el SHA1 no está en el catálogo — el caso de
cualquier hack/parche, que nunca tiene su propio SHA1 en No-Intro/Redump) no
llamaba a `is_non_canonical_variant()` (`detection/filename_normalizer.py`),
el mismo guard que **sí** ya usan `planner/operation_planner.py:121` (evita
renombrar el hack con el nombre del original) y
`web/builders/duplicates.py:786,800` (evita agruparlo como duplicado en la
cola de revisión) — el guard existía pero solo se aplicaba río abajo, no en
el origen donde se asigna `canonical_title`. `normalize_for_match()` trata
`[Subset - Professor Oak Challenge]` como una anotación benigna más (igual
que `(USA)` o `[!]`), así que el hack matcheaba por título contra el
catálogo del original con confianza "medium".

Efecto ya real en la biblioteca (no solo teórico): `Pokemon - Ruby Version
[Subset - Professor Oak Challenge].gba` **ya estaba organizado** en `gba\`
con `canonical_title = "Pokemon - Ruby Version (Europe) (Rev 1)"` — el mismo
título que el Ruby real, sin organizar en `Unknown\`. El guard de
renombrado evitó que el hack robara el nombre de archivo del real, pero
`filter_duplicate_winners()` (`services/ra_duplicates_service.py`, usado por
el envío GBA→Anbernic y por el dedup de `DUALFOLDER-12`) tampoco comprobaba
`is_non_canonical_variant()` — un futuro dedup de GBA podría confundirlos.
✅ Arreglado en `fix/dup-winners-non-canonical-guard` (2026-09-18): el hack
ahora se trata como `single` (nunca entra en el grupo por título del
original), mismo guard que `_match_by_title()` y `duplicates.py`. Test
`test_filter_duplicate_winners_never_discards_real_copy_for_hack`, 1342
tests en verde.

**Arreglado en `fix/catalog-match-subset-hack`**: `_match_by_title()` ahora
llama a `is_non_canonical_variant()` al principio y devuelve `None` si el
filename es un hack/parche — no vuelve a pasar con archivos nuevos. Se
limpió a mano (sin mover/borrar nada) el `canonical_title` de los 4
registros ya afectados por los hacks de Pokémon (FireRed/Ruby/Emerald
"Professor Oak Challenge", el Ruby cuenta 2 veces: `Unknown\` + `gba\`).

**Alcance mayor detectado, fuera de esta rama**: al buscar todas las filas
con `canonical_title` poblado + `is_non_canonical_variant(original_filename)`
aparecieron **1183 filas** en toda la biblioteca — mayoría parches de
traducción NES (`[T+Por...]`, `[T-Por]`...), el mismo patrón que ya
documentó `CATALOG-MATCH-VARIANT-1` (hallazgo de 22 parches de Zelda,
2026-09-09) sin llegar a limpiarse en la BD. Decisión del usuario
2026-09-18: dejar esas 1179 filas restantes sin tocar por ahora — no hay
evidencia de que hayan causado daño real (a diferencia del Ruby, ninguna
está ya organizada bajo un nombre prestado). Revertida el mismo día: el
usuario pidió limpiarlas también | `catalog/matcher.py:281-296`
(`_match_by_title`), `detection/filename_normalizer.py:65-74`
(`is_non_canonical_variant`), `services/ra_duplicates_service.py`
(`filter_duplicate_winners`) | ✅ guard en `filter_duplicate_winners()`
arreglado en `fix/dup-winners-non-canonical-guard`. ✅ limpieza de las 1179
filas ejecutada 2026-09-18 sobre `library_pc.db` (`library_android.db`: 0
filas afectadas). Backup previo (`library_pc.db.bak-20260918-223238`,
gitignored). Verificado primero: de las 1179, **1175 eran del fallback por
título** (`match_confidence` `low`/`medium`, el bug real) y **4 eran matches
legítimos por SHA1** (`match_confidence high`, No-Intro sí cataloga esos 4
hacks `[h1]`/`[h3]` por su propio hash) — las 4 se dejaron intactas, solo se
limpiaron `canonical_title`/`match_confidence`/`catalog_source` (a `NULL`)
de las 1175 restantes. También verificado: **0 de las 1175 tenían el
archivo ya renombrado** en disco al nombre prestado (`source_path` basename
== `original_filename` en todos los casos) — el guard de
`operation_planner.py` ya las había protegido, a diferencia del caso Ruby.
Quedan sin `canonical_title` (correcto: un hack/parche no tiene entrada
propia en No-Intro/Redump, así que no debe matchear) |

### DUALFOLDER-12 — 11 pares Title Case/slug restantes consolidados + guard en el Inbox (2026-09-17, máquina "Ruben", `F:\Juegos Retro`) → roadmap 12
> **Estado (revisado 2026-10-20):** ✅ cerrada — 11 pares consolidados + guard en el Inbox (2026-09-17/18)

Plan e implementación completos en
`.claude/roadmaps/archivo/12-dual-folder-title-case-slug.md`. Resuelve la dirección
que `GBA-DUAL-FOLDER-1`/`PS2-DUAL-FOLDER-1` dejaron sin decidir: el slug es
el canónico también en el PC (misma tabla `_ES_PLATFORM_FOLDERS` que ya usa
el cable-sync).

5 pares triviales (`Game Boy`→`gb`, `Game Gear`→`gamegear`,
`Master System`→`mastersystem`, `Neo Geo`→`neogeo`, `PlayStation`→`psx`) +
6 pares con posible dedup (`Game Boy Color`, `Nintendo 3DS`, `Nintendo 64`,
`Nintendo DS`, `Sega Mega Drive`, `Super Nintendo`/`snes`). Hallazgo: 3 de
los 6 últimos no eran duplicados de ROM reales — `nds/` tenía 84 saves `.sav`
huérfanos + 2 ROMs (no "3 ROMs" como decía la medición de origen) mientras
los 338 ROMs reales vivían en `Nintendo DS/`; `3ds/Rockman X3...bin` es un
ROM de SNES mal clasificado, no un duplicado del `.3ds` real; `gbc/` tenía
13 betas/prototipos únicos sin solapar. Los otros 3 pares (168 archivos)
usaron `filter_duplicate_winners`/`resolve_duplicate_ra`
(`services/ra_duplicates_service.py`), el mismo motor que ya usa el sync
GBA→Anbernic, filtrando primero a solo grupos con **todas** sus entradas
dentro del par (una pasada inicial incluía por error cientos de grupos que
tocaban `Unknown/`, fuera de alcance).

Guard nuevo en `_platform_folder_name()` (`web/inbox_pipeline.py:40-43` →
ahora acepta `target_root` opcional): si el slug de destino tiene junto a él
una carpeta Title Case legada con contenido real, loguea un warning
(`DUALFOLDER-12`) sin bloquear — conectado en el Paso 6 real de organización.
3 tests nuevos en `test_inbox_scan_preview.py` | `web/inbox_pipeline.py`
(`_platform_folder_name`, `_folder_has_real_content`) |
✅ commit/PR a `develop` confirmado por el usuario 2026-09-18, rebasado sobre
`develop` (incluye `CATALOG-MATCH-SUBSET-1`, sin conflicto real de código).
**Corrección 2026-09-20**: el hallazgo original decía "SNES mal detectado"
para `3ds/Rockman X3 (Unl) [c][!].bin` — verificado a mano (tabla de
vectores 68k en offset 0x0 + firma `"SEGA"` en offset 0x100, tamaño 2 MiB),
en realidad es una ROM de **Sega Genesis/Mega Drive** (bootleg no
licenciado), no de SNES. Reclasificado y movido a `megadrive/` (carpeta
canónica, sin colisión de nombre), rescaneadas ambas carpetas (`3ds/`,
`megadrive/`) para que SQLite refleje la nueva ubicación. Fuera de alcance
del matcher (`(Unl)` sin `canonical_title` en el DAT, no renombrable) |

### MATCH-HANG-CHDMAN-1 — el job `match` (CLI y web) puede colgarse decenas de minutos sin avisar, sin poder cancelarse (hallazgo 2026-09-15)
> **Estado (revisado 2026-10-20):** ✅ cerrada — arreglado

Plan de implementación en `.claude/roadmaps/archivo/13-match-chdman-robustness.md`.

Al re-lanzar `POST /api/match` sobre las 7.738 filas sin resolver (tras añadir
el catálogo arcade), el job se quedó `running=true` más de 30 minutos sin
avance visible. `Get-Process python` mostró **CPU casi plano** (35,4s → 35,6s
en 10+ minutos reales) — el proceso Python en sí no estaba calculando nada,
solo bloqueado esperando un `subprocess.run()`; el trabajo real ocurre en un
`chdman.exe` hijo cuyo tiempo de CPU no aparece en `Get-Process python`.
`POST /api/stop-job` (`job_manager.cancel_event`) no lo paró — el bucle de
`match()` solo comprueba `_cancel.is_set()` entre filas, nunca dentro de una
llamada bloqueante. Mismo síntoma que la prueba de `.cdi` de hoy
(`DREAMCAST-FORMAT-MISMATCH-1`): `chdman` puede tardar minutos/no completar
nunca sobre un archivo concreto sin que el timeout individual (300s en
`_extract_chd`, `ra_cd_image.py:207`) ayude si hay **varias** filas PSX
ambiguas en la cola que disparan `detect_psx_boot_serial()` →
`_extract_chd()` una tras otra — cada una puede consumir hasta 5 min sin que
el job progrese ni pueda cancelarse antes de que termine la fila actual.
Recuperado matando el proceso del servidor y reiniciándolo (sin pérdida de
datos — `update_match` corre dentro de un único `batch()`/transacción por el
run completo, así que nada se comiteó a medias) | `catalog/matcher.py`
(`_match_by_title`, dispara `detect_psx_boot_serial` para desambiguar región
PSX), `retroachievements/ra_hash_psx.py:181-184`
(`detect_psx_boot_serial`, rama `.chd`), `retroachievements/ra_cd_image.py:207`
(`_extract_chd`, timeout de 300s por llamada, no por job), `web/handlers/scan.py`
(`_do_match`, el bucle solo comprueba `_cancel` entre filas) | ✅ arreglado
2026-09-15 (roadmap `13-match-chdman-robustness.md`, rama
`fix/match-chdman-robustness`). **(a)** `_extract_chd()` acepta ahora un
parámetro `timeout` (default 300s, sin cambios para la conversión real);
`detect_psx_boot_serial()` pasa `_BOOT_SERIAL_TIMEOUT = 60` — medido con
`chdman extractcd` real contra la biblioteca (~22s el disco de un solo track
más grande, ~17s el multi-track más grande), 60s deja margen de sobra sin
acercarse a los 300s de una conversión real. **(b)** `_do_match` reporta
`job_manager.update_progress("match", {"current", "total", "current_file"})`
por fila, expuesto como `match_progress` en `/api/job-status`
(`JobManager.get_status()`) — mismo patrón que `scan_progress`/`chd_progress`;
barra de progreso nueva en la pestaña Overview (`match-progress-wrap`,
`jobs.js`). **(c)** cancelación real: no hizo falta matar el subprocess —
con el timeout de (a) más el `_cancel.is_set()` que ya se comprueba entre
filas, la espera máxima por fila bajó de 300s a 60s, suficiente para que
cancelar sea cuestión de segundos, no de 30+ minutos. Verificado contra la
biblioteca real: `rommgr match` sobre las 6.518 filas sin resolver actuales
(42 PSX) terminó en 13.4s, sin cuelgue. 5 tests nuevos (`test_ra_hash_psx.py`
×2, `test_jobs_manager.py`, `test_handlers_scan.py`). 1330 tests totales,
ruff+format limpios. **Fuera de alcance deliberadamente**: localizar el
`.chd` exacto que disparó el cuelgue original — no reproducible ahora (la
cola de 7.738 filas de aquel momento ya no existe) y no bloqueante, según lo
previsto en el propio roadmap |

---
