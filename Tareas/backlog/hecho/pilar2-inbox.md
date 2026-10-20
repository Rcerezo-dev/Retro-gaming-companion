# Hecho — Pilar 2 — Inbox automático — → #203

> Secciones ✅ de `Tareas/backlog/pilar2-inbox.md` (todas sus tareas cerradas). Referencia.

### INBOX-FIX — Bugs del pipeline de extracción/organización (hallados en JUNK-REVIEW-1, 2026-07-08)

Origen: al categorizar los 5.774 ZIPs de `Unknown\` para JUNK-REVIEW-1 se detectaron
tres fallos de raíz en el pipeline de Inbox/setup que explican por qué tantos
archivos quedan varados sin extraer/organizar. Detalle de la investigación:
`Tareas/diario/Día39.md` (sección JUNK-REVIEW-1) y conversación 2026-07-08.
INBOX-FIX-1/2/3 → PRs #85/#87/#88, todas mergeadas. Aplicados manualmente sobre
la biblioteca real 2026-07-08 con el código de esas 3 ramas antes del merge:
20 BIOS movidas a `bios/<slug>/` (+20 filas basura eliminadas de `games`),
1.606 juegos con `platform` recuperado por backfill desde `catalog_source`,
4.515 archivos organizados a su carpeta de plataforma, 139 re-matches (solo 2
genuinamente nuevos, ambos correctos). `Unknown\` pasa de ~6.021 a 1.437 filas
en BD (mayoría categoría 5: componentes MAME + las 15 colecciones de categoría
2, aún pendientes de tu decisión). **INBOX-FIX-5** (PR #90) surgió al verificar
esa aplicación: el borrado por "duplicado" (organize + BIOS intercept) solo
comparaba nombre de archivo, no contenido — 22 archivos reales borrados sin ser
duplicados de verdad (SHA1 distinto). Ya arreglado: compara SHA1 antes de borrar.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| INBOX-FIX-1 | **`extract_zip` aborta el ZIP entero por una sola colisión + el setup wizard nunca borra el origen** — `converters/zip_extractor.py:106-114`: si un solo archivo de destino ya existe, se salta la extracción de **todo** el ZIP (sin avisar, sin extraer el resto). `web/inbox_pipeline.py:294` (`_run_setup_pipeline`) llama `extract_zip(..., delete_source=False)` hardcodeado. Confirmado en biblioteca real: `Nintendo - SNES.zip` (325 juegos) tiene algunos ya extraídos sueltos en `Unknown\` y el resto (`Blackthorne`, `BioMetal`...) nunca extraído por la colisión con uno solo. Fix: extraer archivo por archivo saltando solo los que colisionan (no abortar el ZIP completo); exponer `delete_source` como opción real del wizard. | `converters/zip_extractor.py`, `web/inbox_pipeline.py` | ✅ `extract_zip` ahora extrae miembro a miembro (solo salta los que colisionan, ya no aborta el ZIP); el original solo se borra si todo su contenido queda confirmado en disco sin errores. Checkbox nuevo "Borrar el ZIP original..." en el wizard (`wiz-delete-zips`, desmarcado por defecto). 4 tests nuevos (`tests/test_zip_extractor.py`) — PR #85 |
| INBOX-FIX-2 | **El catalog match nunca escribe `platform` en la BD** — `repository.update_match()` (`database/repositories/games.py:182`) ya soporta `platform=`, pero ninguno de los dos call-sites lo pasa (`web/inbox_pipeline.py:332` en setup, `:473` en inbox). Consecuencia: el 96% de los juegos individuales sueltos en `Unknown\` ya tienen `canonical_title` matched (1.658/1.727) pero quedan con `platform=NULL` para siempre, así que el paso "organize" nunca sabe a qué carpeta moverlos. Fix: derivar `platform` del nombre del DAT (`catalog_source`, p.ej. `"Nintendo - Super Nintendo Entertainment System.dat"`) vía un mapeo DAT→plataforma, poblar `MatchResult.platform` también en la rama No-Intro/Redump (hoy solo se pone en la rama arcade, `catalog/matcher.py:20`), y pasar `platform=m.platform` en ambos call-sites. | `catalog/matcher.py`, `web/inbox_pipeline.py` | ✅ `_platform_from_dat_name()` + 18 tests — PR #87 |
| INBOX-FIX-3 | **Categoría 5 de JUNK-REVIEW-1 (1.105 ZIPs sueltos en `Unknown\`) son mayoritariamente infraestructura MAME, no juegos** — `catalog/mame_loader.py:32` ya excluye `isbios`/`isdevice` al indexar, así que la mayoría (`c1541.zip`, `kb_pcat101.zip`, `sb16.zip`...) nunca podrá matchear porque no son juegos jugables por sí solos (mismo perfil que los chips ya borrados en JUNK-CLEAN-1, Día39). Los más grandes sí son BIOS de sistema con nombre reconocible (`naomi.zip`, `chihiro.zip`, `triforce.zip`, `hikaru.zip`, `aristmk5/6.zip`, `hod2bios.zip`, `lindbios.zip`, `f355bios.zip`, `galgbios.zip`, `airlbios.zip`, `ar_bios.zip`, `cdibios.zip`, `macsbios.zip`, `alg_bios.zip`, `crysbios.zip`, `v4bios.zip`) pero **faltan en `_KNOWN_BIOS_MAP`** (`web/inbox_pipeline.py:54-112` — hoy solo tiene `stvbios.zip`→saturn y `awbios.zip`→naomi de este grupo). Además el "Step 1.5: Intercept BIOS files" que mueve BIOS conocidas a `bios/<plataforma>/` **solo corre en `_run_inbox_pipeline`, no en `_run_setup_pipeline`** — el asistente de primera configuración (que probablemente procesó `Unknown\` originalmente) nunca ejecuta ese paso. Fix: ampliar `_KNOWN_BIOS_MAP` con estas entradas y extraer el intercept a una función compartida que también llame `_run_setup_pipeline`. Tras INBOX-FIX-2, re-lanzar el match arcade sobre el resto (los `.zip` sin nombre de BIOS conocido) para ver qué queda genuinamente sin identificar antes de decidir si se borra. | `web/inbox_pipeline.py` | ✅ `_intercept_bios_files()` compartida por ambos pipelines + 16 BIOS arcade nuevas en el mapa; 5 tests (`tests/test_bios_intercept.py`) — PR #88 |
| INBOX-FIX-4 | **`_run_setup_pipeline` construye el plan de renombrado pero nunca lo aplica** — a diferencia de `_run_inbox_pipeline` (extract→scan→match→plan→**rename→organize**→cleanup, todo automático), el asistente de primera configuración se para en "build plan" (Step 5) y deja el resto para una acción manual aparte. Es la razón de fondo por la que `Unknown\` quedó con miles de archivos sin categorizar tras el primer scan de la biblioteca real — nadie ejecutó nunca el equivalente de los Steps 5-6 del pipeline de Inbox sobre ella, así que hubo que aplicar los fixes con scripts manuales en vez de con la app. **Decisión de diseño (2026-07-23): NO auto-aplicar** — mantener la revisión manual (regla `rommgr plan siempre antes de apply` intacta); el wizard debe dirigir explícitamente al usuario a un botón "Aplicar plan" al terminar el Step 5 en vez de dejarlo ahí sin más pasos. | `web/inbox_pipeline.py` (`_run_setup_pipeline`) | ✅ **ya implementado, sin código nuevo** — verificado 2026-07-23: `_showSetupResult()` (`overview.js`) ya muestra en la página 3 del wizard "Siguiente paso: revisa el plan de renombrado y aprueba los cambios" + un botón primario destacado "Ir a Organizar y renombrar ▶" (`wizardGoToOrganize()`, `_banners.html`) que navega directo a la pestaña Organizar/Renombrar. Esta UI viene de FLOW-WIZARD (`2e4dba0`, 2026-04-14) — **anterior** a que se documentara este hallazgo (JUNK-REVIEW-1, 2026-07-08); el episodio real de `Unknown\` sin categorizar ocurrió con una versión de la app previa a que existiera este wizard. Nada que tocar hoy: el flujo actual ya cumple la decisión de diseño acordada |
| INBOX-FIX-5 | **El borrado por "duplicado" (organize + BIOS intercept) solo comparaba nombre de archivo, no contenido** — bug de pérdida de datos real: aplicado a la biblioteca real, 22 archivos "duplicados" borrados resultaron tener SHA1 distinto del superviviente (dumps/revisiones distintas que solo compartían nombre). `Path.unlink()` en Windows no pasa por la Papelera — no recuperable. | `web/inbox_pipeline.py` | ✅ `_same_content()` (tamaño + SHA1) antes de borrar en ambos sitios; si difiere, no se toca ninguno y se reporta para revisión manual. 8 tests — PR #90 |
| MATCH-FIX-1 | **`CatalogMatcher.match()` — Pass 2 (nombre) da falsos positivos en ficheros arcade sin tag de región** — nombres cortos estilo MAME (`flicky.zip`, `frogger.zip`, `dw.zip`…) sin `(Region)` colisionan por coincidencia de título normalizado contra catálogos No-Intro/Redump de plataformas completamente ajenas (`flicky.zip` → "Fujitsu - FM-7", `frogger.zip` → "APF - Imagination Machine") con confianza `low`, en vez de matchear contra el catálogo arcade correcto (Pass 3, que nunca llega a probarse porque Pass 2 ya "acertó"). Detectado 2026-07-08 al re-lanzar el match sobre `Unknown\` — son matches **preexistentes**, no introducidos hoy. Fix: para nombres sin región/paréntesis, probar primero el catálogo arcade (Pass 3) antes que el name-fallback No-Intro/Redump (Pass 2), o exigir una señal más fuerte que la sola coincidencia de título normalizado. | `catalog/matcher.py` | ✅ rama `fix/match-fix-1-arcade-before-name-fallback` — para `.zip` sin `(` en el nombre (estilo MAME) el pass arcade corre antes que el fallback por título; el resto conserva el orden actual. Passes 2/3 extraídos a `_match_by_title()`/`_match_arcade()`. 4 tests nuevos (caso real flicky.zip vs FM-7; 635 pass). **Pendiente aparte**: los falsos matches preexistentes en BD no se corrigen solos — re-lanzar el match sobre `Unknown\` tras mergear |
| MATCH-FIX-2 | **Caso real 2026-08-29, buscando "Final Fantasy III" en Juegos**: 36 archivos `.nes`/.zip completamente distintos (romhacks/traducciones fan en inglés v1.0, v3.1, francés, italiano, portugués de Brasil, uno con "Final Fantasy VI Font"…) reciben **el mismo** `canonical_title` — "Final Fantasy III (Japan) (Virtual Console)" — y encima **`platform: "Nintendo 3DS"` para archivos `.nes`**, con `match_confidence: "low"`. Causa raíz confirmada leyendo el código: `_build_title_index()` (`catalog/matcher.py:152-161`) mezcla entradas de **todos los DATs de todas las plataformas** en un único índice por título normalizado, sin separar por plataforma; `_match_by_title()` (`catalog/matcher.py:233-255`) cuando hay varios `hits` para la misma clave (ambiguo) **siempre devolvía `hits[0]`** — el que haya quedado primero en la lista, que depende de qué archivo `.dat` cargó antes en `sorted(directory.glob("*.dat"))` (`catalog/matcher.py:142`, orden alfabético) — "Nintendo - Nintendo **3**DS..." ordena antes que "Nintendo - Nintendo **E**ntertainment System...", así que el título del NES real perdía sistemáticamente contra el de la re-edición de 3DS. Mismo patrón de fondo que MATCH-FIX-1 (Pass 2 sin señal fuerte) pero más amplio: cualquier título reutilizado entre plataformas (remakes, Virtual Console, romhacks) heredaba la plataforma equivocada. | `catalog/matcher.py:152-161` (`_build_title_index`), `:233-262` (`_match_by_title`), `:142` (orden de carga de DATs) | ✅ `_match_by_title` ahora, ante ambigüedad, prefiere el `hit` cuya plataforma (`_platform_from_dat_name`) coincide con la extensión real del archivo vía `PLATFORM_BY_EXTENSION` (`detection/platform_detector.py`, ya existente, import a nivel de módulo — sin ciclo, `platform_detector.py` no importa nada de `rom_manager`); si ninguno coincide (p.ej. `.zip`, ambiguo por diseño — no está en `PLATFORM_BY_EXTENSION`) cae al comportamiento anterior (`hits[0]`). 2 tests nuevos en `tests/test_catalog_matcher.py` (reproducen el caso real con los mismos nombres de `.dat`; 1038 pass). **Verificado contra los DATs reales de la biblioteca**: `Final Fantasy III (J) [T+Bra1.0_Hexagon].nes` y `Final Fantasy III (Japan) (Virtual Console).nes` ahora resuelven a `platform: NES` / `Nintendo - Nintendo Entertainment System (Headered)...dat` (antes `Nintendo 3DS`); el mismo título en `.zip` (sin señal de extensión) sigue cayendo en 3DS, limitación conocida y documentada — necesitaría inspección de contenido, no solo nombre. **Ejecutado de verdad 2026-08-29** (backup previo en `.rommgr/backup_matchfix2_2026-08-29/library_pc.db`): `get_unresolved_games()` (`database/repositories/games.py`) ganó el parámetro `include_low_confidence` — sin él, `/api/match` solo re-evalúa filas con `match_confidence IS NULL`, así que las ya matcheadas mal (`match_confidence='low'`, como las 36 de Final Fantasy III) eran invisibles para siempre una vez matcheadas, por mucho que se relanzara "Identificar (catálogos)" desde la UI. `POST /api/match {"include_low_confidence": true}` (nuevo body opcional, mismo endpoint) re-evalúa también esas. Corrida real sobre la biblioteca completa: `total=26.152, matched_low=20.961, unmatched=5.191, matched_high=0` (esperado — estas filas ya habían fallado el Pass 1 SHA1 antes). Verificado en la propia BD: los 11 `.nes` de Final Fantasy III pasan de `platform: Nintendo 3DS` a `platform: NES` con título correcto `"Final Fantasy III (Japan)"`; los `.zip` del mismo juego (sin extensión que desambigüe) siguen en `Nintendo 3DS` — limitación conocida, no arreglada (necesitaría mirar el contenido, no el nombre) |

### MATCH-FIX-3 — Descomprimir y rehashear no resuelve las colisiones de nombre cuando el catálogo tampoco conoce el hash real (hallazgo 2026-09-12)

Plan de implementación (junto a los follow-ups pendientes de `MATCH-HEADER-1`)
en `.claude/roadmaps/14-matcher-coverage-gaps.md`.

Origen: sesión 2026-09-12, máquina "Ruben" (`F:\Juegos Retro`) — el objetivo
era confirmar si los ~963 conflictos de `plan` en `.zip`/`.nes`/`.gb`/`.gbc`
(mismo problema de fondo que `MATCH-FIX-1`/`MATCH-FIX-2`: `_match_by_title()`
adivinando sin señal fuerte) se resolvían solos tras `decompress --apply`
(4.977 ZIPs descomprimidos) + `scan` completo (rehash real) + `match`. **No
se resolvieron**: tras el rehash real, `plan` sigue mostrando 1.276
conflictos, de los cuales 947 son la misma familia (`.zip` 696, `.nes` 141,
`.gbc` 57, `.gb` 53) — prácticamente igual que antes de descomprimir.
Verificado contra la BD real: de 12.897 juegos, 3.377 siguen en
`match_confidence='low'` y 3.789 sin `canonical_title`; `match` de hoy solo
resolvió 71 de 4.163 pendientes por SHA1. Causa raíz confirmada: la mayoría
de estos archivos no son solo "ZIP sin hashear" como se asumía — su SHA1
real (ya calculado) tampoco está en los catálogos No-Intro/Redump (hacks,
traducciones, romsets no oficiales), así que tener el hash correcto no
cambia nada: `_match_by_title()` (`catalog/matcher.py:233-262`) sigue
cayendo al fallback por título y sigue colisionando exactamente igual que
con el ZIP sin descomprimir. El cuello de botella es cobertura de catálogo,
no formato de archivo.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-FIX-3 | **✅ Decidido y hecho 2026-09-19** (roadmap 14, `fix/matcher-coverage-gaps`): el usuario eligió la opción conservadora — sin match si hay ambigüedad real, en vez de desambiguar por tamaño. `_match_by_title()` ya no devuelve `candidates[0]` a ciegas cuando, tras todo el filtro por plataforma/extensión/carpeta/serial, siguen quedando >1 candidatos y ningún número de disco los distingue — devuelve `None`. El caso donde el número de disco SÍ distingue (`GAMECUBE-DISC-BUG-1e`) sigue devolviendo el match real, sin cambios ahí. 3 tests existentes actualizados (`test_name_fallback_low_confidence_ambiguous`→`..._returns_none_when_genuinely_ambiguous`, `test_ambiguous_title_falls_back_to_first_hit_without_extension_signal`→`..._returns_none_without_extension_signal`, `test_ambiguous_extension_prefers_platform_of_containing_folder`) para reflejar el nuevo comportamiento — el caso con `source_path` real que sí desambigua por carpeta sigue devolviendo match, sin tocar. **✅ Medido en real 2026-09-19** contra `F:\Juegos Retro`/`library_pc.db` (backup previo en `.rommgr/db-backup/library_pc.20260919T203805Z.db`): `rommgr match` equivalente con `include_low_confidence=True`, 16.176 filas re-evaluadas (9.481 sin match + 6.695 con `low` viejo) en ~26 min (dominado por desambiguación PSX vía `chdman`, que descomprime el disco completo por candidato ambiguo). De las 6.695 `low`: **5.593 (83,5%) eran adivinanzas incorrectas**, ahora correctamente sin match; **1.102 (16,5%) sí estaban bien resueltas** por otra señal real, sin cambios. El total `unmatched` de esas 16.176 filas sube a 13.548 — no es regresión, es visibilidad real de un problema que ya existía oculto tras `match_confidence='low'` | `catalog/matcher.py` (`_match_by_title`) | ✅ política decidida, implementada y medida contra producción |

---

### MATCH-ZIP-HASH-1 — La mayoría de las "adivinanzas corregidas" de `MATCH-FIX-3` son en realidad ZIPs de consola sin descomprimir cuyo SHA1 nunca puede calzar con el catálogo (hallazgo 2026-09-19, durante la medición real de `MATCH-FIX-3`)

Origen: los ejemplos de la medición real de `MATCH-FIX-3` (arriba) eran
casi todos `.zip` de Game Boy con colisión de región (`(USA)` adivinado como
`(Europe)`/`(Japan)`). Primera hipótesis — "el catálogo No-Intro de Game Boy
tiene huecos de cobertura para dumps USA" — **descartada por evidencia
directa**: verificado que `Nintendo - Game Boy.dat` SÍ tiene una entrada
`"Addams Family, The (USA)"` real (SHA1 `8710CEECBE3E...`, 131.072 bytes).

**Causa raíz real, confirmada con hashes reales, no supuesta**: en la propia
biblioteca (`F:\Juegos Retro\gb\`) conviven `Addams Family, The (USA).gb`
(SHA1 `8710ceecbe3e...` — coincide exacto con el catálogo, `match_confidence
='high'`) y `Addams Family, The (USA).zip` (SHA1 almacenado
`4eb0e158519d...`, **completamente distinto**). Verificado abriendo el ZIP:
contiene un único `Addams Family, The (USA).gb` de 131.072 bytes cuyo SHA1
**es exactamente `8710ceecbe3e...`** — el mismo juego, byte a byte idéntico
al ya reconocido. El SHA1 guardado en la BD para el `.zip` es el hash del
**contenedor ZIP completo**, no del ROM que contiene —
`hashing/hash_calculator.py::calculate_hashes()` (línea 29-53) abre el
archivo y hashea sus bytes crudos sin ninguna conciencia de ZIP, a
diferencia del ruteo arcade (`load_arcade_crc_index()`, `ZIP-ROUTE`) que sí
lee el CRC32 de cada entrada sin descomprimir. Un ROM de consola guardado
sin descomprimir (viola la regla del Pilar 1 "ZIPs descomprimidos") **nunca
puede** matchear por SHA1 exacto contra el catálogo, sin importar lo
correcto que sea su contenido — antes caía al fallback por título y
adivinaba mal (el bug de `MATCH-FIX-3`); ahora, correctamente, no matchea
en absoluto — pero la respuesta *correcta* sería reconocerlo con
`confidence='high'` iguialmente, no dejarlo sin match.

**Alcance medido a escala completa (2026-09-19, script de solo lectura sobre
los 4.257 `.zip` sin match reales)**: abriendo cada ZIP y comparando el SHA1
de su único archivo interno contra el catálogo No-Intro/Redump ya cargado:

| Categoría | Filas | % |
|---|---|---|
| `catalog_match` — contenido interno coincide exacto con el catálogo | 3.245 | 76,2% |
| `no_match` — contenido genuinamente sin catalogar (hacks/homebrew/BIOS boot ROMs por nombre) | 682 | 16,0% |
| `multi_entry` — ZIP con >1 archivo (sets arcade, no el caso de este hallazgo) | 329 | 7,7% |
| `unreadable` (1 archivo corrupto/no-ZIP real) | 1 | ~0% |

**0 casos de "hermano ya reconocido"** — ninguno de estos `.zip` duplica el
contenido de un archivo ya descomprimido en la biblioteca; son copias
zip-only genuinas, no basura residual de una extracción a medias.

**Decisión del usuario (2026-09-19)**: los tres caminos NO son excluyentes,
uno por categoría:
1. **`catalog_match` (3.245, 76%) → descomprimir vía `rommgr decompress`**.
   **✅ ejecutado y cerrado 2026-09-20.** `rommgr decompress "F:\Juegos Retro"`
   (dry-run: 7.419 a descomprimir / 1.430 saltados arcade+multi-disco / 1
   fallido — `GBA ROMs Pack (Romspack.Com).zip`, ya conocido, no es un ZIP
   real). `--apply` (sin `--delete-source`): 7.419 descomprimidos, 0 nuevos
   errores. `rommgr scan "F:\Juegos Retro"`: 30.976 ROMs detectados, 0
   errores. Re-match (backup previo en `.rommgr/db-backup/`, sobre las
   15.613 filas sin match tras el scan): 1.798 nuevas filas
   `match_confidence='high'` + 131 medium/low. **Segunda pasada —
   `--delete-source`** (dry-run + `--apply`, ambos autorizados explícitamente
   por el usuario tras el bloqueo inicial del sandbox): movió los 7.419 ZIP
   ahora redundantes a sus `_descartados/` respectivos vía
   `discard_to_trash()` (verificado en disco: solo los ZIP de hoy, nada
   sobrescrito). `rommgr scan` final: **5.131 filas huérfanas podadas**
   (los `.zip` movidos ya no existen en su ruta original). **Resultado neto
   verificado en `library_pc.db` real**: total juegos 31.028 → 25.897 (solo
   limpieza de contenedores redundantes, ningún archivo real perdido); total
   sin match 13.685 → 9.749; `.zip` sin match 4.004 → **68** (quedan solo
   sets arcade/multi-disco genuinamente sin catalogar, no contenedores
   redundantes).
2. **`multi_entry` (329, 7,7%) → catálogo arcade desactualizado, no un hueco
   de cobertura real** — ver `MATCH-ARCADE-DAT-1` abajo. **✅ hecho y medido
   2026-09-19.**
3. **`no_match` (682, 16%) → fuera de esta tarea**, por diseño No-Intro/Redump
   no cubren hacks/homebrew/BIOS boot ROMs; el retorno de bajar un DAT
   adicional de "hacks" sería marginal. Sin implementar, sin decisión de
   revisitar todavía.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-ZIP-HASH-1 | Medir a escala + decidir los 3 caminos (arriba) | `hashing/hash_calculator.py:29-53` (`calculate_hashes`, sin conciencia de ZIP — sigue sin tocarse, la vía elegida fue descomprimir, no hashear-sin-descomprimir), `converters/zip_extractor.py` (`extract_zip`/`extract_directory`), `utils/trash.py` (`discard_to_trash`) | ✅ cerrado 2026-09-20. 2/3 caminos hechos y medidos en real (`MATCH-ARCADE-DAT-1` + descompresión/limpieza/rematch); 1/3 (`no_match`) descartado por bajo retorno. `.zip` sin match: 4.004 → 68 |

---

### MATCH-ARCADE-DAT-1 — `load_fbneo_dat()` nunca parseó nada: el catálogo arcade de FBNeo llevaba 0 entradas desde siempre (hallazgo + fix 2026-09-19, durante MATCH-ZIP-HASH-1)

Origen: investigando por qué 329 sets arcade multi-archivo (`captcommb.zip`,
`19xxd.zip`, `armwar1d.zip`... casi todos en `cps1/`) no matcheaban pese a
que sus sets *parent* (`captcomm`, `19xx`, `armwar`) sí estaban en el
catálogo cargado. Verificado a mano con `load_arcade_dir()`: los parents
venían todos de `"MAME 2003-Plus XML.xml"` — ninguno de `"FBNeo - Arcade
Games.dat"`, el segundo archivo del directorio `catalogs/arcade/`.

**Causa raíz confirmada**: el `.dat` que llevaba años en
`.rommgr/catalogs/arcade/FBNeo - Arcade Games.dat` **no era XML** — formato
texto plano ClrMamePro (`clrmamepro ( name "..." )`, `game ( name "..." rom
( ... ) )`). `load_fbneo_dat()` (`catalog/mame_loader.py:57-78`) hace
`ET.parse(path)` directo — con este archivo, lanza `ET.ParseError`,
capturado en silencio por el `except (ET.ParseError, OSError): pass` y
devuelve `{}`. Verificado en vivo: `load_fbneo_dat()` sobre el archivo real
→ **0 entradas**; el total de 4.858 entradas "arcade" que reportaba el
matcher venía **al 100% de MAME 2003-Plus** (un fork ligero/antiguo de MAME
usado en handhelds retro, sin buena parte de los clones/bootlegs que sí
lista el MAME oficial actual o FBNeo). El pass arcade (`_match_arcade()`,
`catalog/matcher.py:450-480`) llevaba funcionando así desde el origen del
proyecto sin que nadie lo notara — ni tests ni uso normal lo habrían
detectado, porque un `{}` es indistinguible de "catálogo vacío mientras
carga" salvo comparando cuenta de entradas a mano.

**Bug secundario, mismo archivo**: aunque se sustituya por un `.dat` real en
XML, `load_fbneo_dat()` leía `description`/`year`/`manufacturer` como
**atributos** del tag `<game>` (`game.get("description")`), pero el `.dat`
oficial de FBNeo (github.com/libretro/FBNeo, `dats/FinalBurn Neo (ClrMame
Pro XML, Arcade only).dat`) los lleva como **elementos hijos**
(`<game><description>...</description></game>`), igual que `load_mame_xml()`
ya maneja correctamente. Sin el fix, un `.dat` FBNeo real sí habría cargado
(no habría lanzado excepción) pero con `description=""` para las 8.380
entradas — degradando el título a solo el stem (`match_confidence='medium'`
seguiría siendo correcto, pero cualquier UI que muestre el título perdería
la descripción real).

**Hallazgo aparte, no arreglado hoy**: `catalog/dat_downloader.py`
(DAT-DL-1/2) ya tiene un downloader completo con mapeo plataforma→URL
(`libretro-database`) para No-Intro/Redump/FBNeo/MAME — pero **no está
conectado a ningún comando CLI ni handler web** (verificado: 0 llamadas a
`download_dat()` fuera de sus propios tests). Probado en vivo hoy: las URLs
de `libretro-database` para `"FBNeo Arcade"` y `"MAME 2003 Plus"` devuelven
**404** (el repo debió reestructurar `metadat/fbneo`/`metadat/mame`) — el
downloader está roto para arcade además de no estar conectado. No
investigado si las URLs de No-Intro/Redump (mismo `_BASE`) siguen vivas.

**Corrección importante (encontrada al revisar `/progreso` el mismo día)**:
el downloader que **sí está conectado y es el que usa el botón real "Descargar
DAT" de la web** es otro, independiente — `_LIBRETRO_DAT_CATALOG` +
`_run_dat_download()` en `web/handlers/scan.py`, no `catalog/dat_downloader.py`.
Ese downloader real ya tuvo su propio bug de URL (`ARCADE-DAT-URL-STALE-1`,
arreglado 2026-09-15: `metadat/fbneo` → `metadat/fbneo-split`) — pero ese fix
solo corrigió el **404**, nunca verificó el **contenido**. Comprobado hoy en
vivo: `metadat/fbneo-split/FBNeo - Arcade Games.dat` responde `200` pero es
el mismo formato texto plano ClrMamePro (`clrmamepro ( ... )`, `game ( name
"..." rom (...) )`) que causó este mismo bug — **no es XML, `load_fbneo_dat()`
seguirá devolviendo 0 entradas aunque se descargue de nuevo desde la web**,
pese a los dos fixes de hoy. Es decir: **si alguien pulsa "Descargar DAT" →
FBNeo Arcade desde la pestaña Herramientas, revierte silenciosamente el
arreglo de hoy** (catálogo 10.212 → 0 entradas FBNeo otra vez, sin ningún
aviso — mismo patrón exacto de fallo silencioso que el bug original). El
`.dat` de MAME 2003-Plus sí es XML real y no tiene este problema (`metadat/
mame/MAME 2003-Plus XML.xml` → `200`, formato correcto). Ver `MATCH-ARCADE-DAT-2`.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-ARCADE-DAT-1 | `load_fbneo_dat()` ahora lee description/year/manufacturer como elemento hijo primero (fallback a atributo, mismo patrón que `load_mame_xml()`). Sustituido `.rommgr/catalogs/arcade/FBNeo - Arcade Games.dat` (texto plano, 0 entradas reales) por el `.dat` XML oficial actual descargado de `github.com/libretro/FBNeo/blob/master/dats/FinalBurn Neo (ClrMame Pro XML, Arcade only).dat` (backup del original en `.rommgr/catalogs/arcade_backup_20260919/`). 3 tests nuevos (`tests/test_mame_loader.py`): lee child-element real, fallback a atributo, y el `.dat` texto-plano anterior sigue devolviendo `{}` sin lanzar. 1398/1398 tests, ruff+format limpios | `catalog/mame_loader.py` (`load_fbneo_dat`) | ✅ hecho 2026-09-19. Catálogo arcade cargado: 4.858 → 10.212 entradas. **Re-match ejecutado contra `library_pc.db` real** (backup previo en `.rommgr/db-backup/library_pc.20260919T214730Z.db`, 13.548 filas sin match re-evaluadas): **253 filas nuevas resueltas** vía el catálogo FBNeo ahora real (`match_confidence='medium'`), incluyendo 251/329 de los sets multi-archivo de `MATCH-ZIP-HASH-1`. `dat_downloader.py` sigue sin conectar y con URLs de arcade rotas — no arreglado, candidato a tarea aparte si se decide automatizar la descarga de DATs |
| MATCH-ARCADE-DAT-2 | **✅ Arreglado 2026-09-20** — camino elegido: apuntar la entrada del catálogo a la fuente XML real de FBNeo (`raw.githubusercontent.com/libretro/FBNeo/master/dats/FinalBurn Neo (ClrMame Pro XML, Arcade only).dat`, nuevo campo `"url"` override en `_LIBRETRO_DAT_CATALOG`, `_run_dat_download` lo usa en vez de `{metadat_base}/{source}/{filename}` cuando está presente) en vez de la ruta rota de `libretro-database`. **Cerrado también el hueco de verificación real** que dejó pasar el bug: la validación post-descarga usaba `catalog_loader.load_dat_file()` (genérico, SHA1-keyed, acepta ClrMamePro texto) en vez del parser que de verdad consume el archivo una vez en `catalogs_arcade_dir` (`load_arcade_dir()` dispatcha por extensión a `load_mame_xml`/`load_fbneo_dat`, ninguno de los dos con fallback ClrMamePro-texto) — ahora `_run_dat_download` valida con ese mismo parser para `catalog in ("fbneo", "mame")`. Verificado en vivo: descarga real (14 MB, 8.380 entradas vía `load_fbneo_dat`) y regresión confirmada (payload ClrMamePro-texto ahora reportado como error, no como "downloaded"). 2 tests nuevos (`tests/test_dat_catalog_age.py::TestFbneoArcadeDatDownload`), 1400/1400 en verde, ruff limpio | `web/handlers/scan.py` (`_LIBRETRO_DAT_CATALOG`, `_run_dat_download`), `tests/test_dat_catalog_age.py` | ✅ hecho y mergeado a `develop` (`ee883ebc`, PR #334) — re-verificado 2026-09-22 (Día69) con `git merge-base --is-ancestor`, la nota "pendiente PR/merge" estaba desincronizada |

---

### MATCH-FIX-4 — `resolve-duplicates` calcula logros RA con la plataforma de un solo miembro del grupo, ciega copias reales en grupos cross-plataforma (hallazgo 2026-09-12, BLOQUEANTE para `--apply`)

Origen: sesión 2026-09-12, revisando `resolve-duplicates` (dry-run, sin
aplicar) mientras corría `convert-chd` de fondo. Verificado contra la BD
real (`F:\Juegos Retro`): 3 grupos "plain" (auto-resolubles, no conflicto de
disco) mezclan plataformas reales distintas — `Game Boy` vs `Game Boy
Color` (mismo título, mismo contenido exacto: MD5 idéntico entre ambos
archivos) — y los 3 son justo 3 de los 20 juegos marcados/enviados hoy a la
Anbernic por tener logros RA (`Tetris DX`, `Tony Hawk's Pro Skater`, `Men in
Black - The Series`).

Causa raíz confirmada leyendo el código: `_review_groups_for_repo`
(`web/builders/duplicates.py:860`) calcula `plat = next((r["platform"] for
r in members if r["platform"]), None)` — **una sola plataforma para todo el
grupo** (la del primer miembro con `platform` no nulo) — y la usa para
cargar `hash_map` (`:861`, `_load_ra_hash_map(cache_dir, plat, hash_cache)`)
aplicado a **todos** los miembros del grupo en el bucle de `:862-866`, en
vez de resolver la caché RA propia de cada fila con su propio `platform`.
Verificado con `get_ra_achievements`: el mismo MD5 de "Tony Hawk's Pro
Skater (USA, Europe).gbc" da `-1` (desconocido) contra la caché de "Game
Boy" y `12` (logros reales) contra la de "Game Boy Color" — el grupo eligió
`plat="Game Boy"` (por orden de fila), así que la copia `.gbc` real quedó
marcada `ra_supported=False` igual que la `.gb`, empatando en
`_review_entry_sort_key` (`:227-233`) y cayendo al desempate por nombre de
archivo, donde `"0204 Tony Hawk..."` (dígito inicial) ordena antes que
`"Tony Hawk's..."` alfabéticamente — ganando el archivo de un pack bulk sin
depurar (`gb/Classic Game/`) sobre la copia bien nombrada de
`gb/GB official game ROM complete works/`.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-FIX-4 | `_review_groups_for_repo` debe resolver la caché RA **por fila** (`r["platform"]` de cada miembro, no el `plat` compartido del grupo) antes de puntuar `scored`/`ra_supported` — mismo patrón que `get_ra_achievements` ya usa correctamente en `ra_duplicates_service.py`. Mientras no se arregle, **no ejecutar `resolve-duplicates --apply` sin revisar antes los grupos que mezclan extensiones/plataformas distintas** (dry-run + inspección manual, como se hizo hoy) — riesgo real de descartar copias RA-verificadas a favor de duplicados peores. Alcance medido hoy: 3 grupos afectados de 376 "plain", pero puede crecer si se decompress/rescan más colecciones bulk con solapamiento GB/GBC (u otras familias, p. ej. NES/Famicom) | `web/builders/duplicates.py:860-866` (`_review_groups_for_repo`) | ✅ hecho 2026-09-12 — el bucle de puntuación ahora carga `_load_ra_hash_map(cache_dir, r["platform"] or plat, hash_cache)` **por fila** en vez de una sola vez con el `plat` compartido del grupo; `plat` se conserva para la clave del grupo y el chequeo de carpeta correcta (sin cambio ahí). Verificado contra la BD real: los 3 grupos GB/GBC afectados ahora recomiendan correctamente el `.gbc` (15/12/39 logros reales) sobre el duplicado bulk. 1 test nuevo (`test_ra_cross_platform_group_scores_each_entry_by_its_own_platform`, `tests/test_builders_duplicates.py`), 30/30 pass en el archivo, ruff+format limpios |

---

### MATCH-FIX-5 — El catálogo carga DATs de PC/Xbox sin ningún filtro de plataforma, contaminando el título de ROMs de consola reales (hallazgo 2026-09-12, sin implementar)

Origen: sesión 2026-09-12, investigando en paralelo (mientras corría
`convert-chd` de fondo) 16 conflictos de `plan` sueltos en `.gba`/`.nds`/
`.iso`/`.md` no explicados por `MATCH-FIX-3`. Consulta directa a la BD real
reveló la causa: **1.285 juegos** tienen `catalog_source = "IBM - PC
compatible - Datfile (57444)..."` y **88 más** vienen de
`"Microsoft - Xbox - Datfile (2675)..."` — DATs de PC/Xbox, plataformas que
este proyecto **no gestiona** (`CLAUDE.md`: "no es un launcher/front-end de
emuladores", los 3 pilares son consolas retro). Reparto real por
plataforma (solo IBM): PlayStation 339, Game Boy 336, GBA 163, GBC 131, NES
87, SNES 73, Mega Drive 64, NDS 35, Game Gear 31, Arcade 18, PS2 6,
Dreamcast 1, GameCube 1 — prácticamente todas las plataformas de la
biblioteca tienen ROMs con el `canonical_title` sacado de un catálogo de PC
o Xbox, no del suyo propio.

Causa raíz confirmada leyendo el código: `_load_dir()`
(`catalog/matcher.py:157-177`) hace `sorted(directory.glob("*.dat"))` sobre
`nointro_dir`/`redump_dir` **sin ningún filtro de plataforma** — carga
literalmente cualquier `.dat` presente en esas carpetas (confirmado:
`.rommgr/catalogs/nointro/` tiene 126 DATs, incluyendo "IBM - PC compatible
- Datfile", "IBM - PC compatible - SBI Subchannels", "Microsoft - Xbox -
Datfile", "Microsoft - Xbox - BIOS Datfile", 3× "Microsoft - XBOX 360 -
..."). `_build_title_index()` (`:179-188`) indexa **cada entrada de cada
DAT cargado** por título normalizado, sin descartar las de plataformas
ajenas al alcance del proyecto. Cuando `_match_by_title()` (Pass 2) solo
encuentra un único hit para un título (sin ambigüedad real entre varios
candidatos, el caso que `MATCH-FIX-2` sí sabe desambiguar), lo acepta tal
cual aunque ese único hit venga de un DAT de PC/Xbox — ejemplo real
confirmado: `"God of War II (Europe).iso"` (PS2 real) y `"God of War II
(USA).iso"` (PS2 real, región distinta) **ambos** terminan con
`canonical_title = "God of War II (Europe)... (Press Materials)"`
(entrada del DAT de PC), lo que además genera colisión de nombre entre las
dos regiones reales al intentar renombrar.

Root cause probable de cómo llegaron esos DATs ahí: el job `download_dats`
(descarga masiva de No-Intro/Redump) no filtra por plataforma — descarga
"todo lo que hay", incluyendo sistemas fuera del alcance del proyecto.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-FIX-5 | Filtrar el cargador de catálogos por plataforma, reutilizando la lista ya curada del proyecto. Tras filtrar, **re-lanzar `match` con `include_low_confidence: true`** (patrón ya usado en `MATCH-FIX-2`) sobre las plataformas afectadas para recalcular `canonical_title` de los 1.373 juegos contaminados — puede generar renombrados reales, no solo un cambio de metadatos | `catalog/matcher.py:157-177` (`_load_dir`), `:179-188` (`_build_title_index`) | ✅ hecho 2026-09-12 en dos partes. **Parte 1** (código): `_load_dir()` ahora salta cualquier `.dat` que `_platform_from_dat_name()` (ya existente, `catalog/matcher.py:31-86`) no reconozca — reutiliza la lista curada de plataformas del proyecto en vez de mantener una lista negra nueva. Verificado: No-Intro pasa de 287.030 a 67.131 entradas cargadas, Redump de 210.217 a 6.637 (fuera: IBM PC, Xbox/360, PS3, PSP/Vita, Wii U, Macintosh, Amiga CDTV, FM-Towns...). 3 tests del fixture `dirs_with_arcade`/`test_crc_index_drops_cross_dat_collisions` usaban DATs fuera de alcance como relleno (FM-7 real de MATCH-FIX-1, Evercade) — actualizados a DATs reconocidos (Amiga) sin cambiar la intención del test. 1273 tests, 1 fallo no relacionado (contención real con `chdman.exe` corriendo de fondo en la misma sesión). ruff+format limpios. **Parte 2** (datos reales, `POST /api/match {"include_low_confidence": true}`): 7.166 filas re-evaluadas (730 SHA1 alto, 2.021 título bajo — ahora limpio, sin PC/Xbox —, 4.415 sin match). **Hallazgo aparte durante la verificación**: 563 de los 1.373 originales seguían con `catalog_source` IBM/Xbox tras el re-match — `_do_match()` (`web/handlers/scan.py:551-566`) solo escribe cuando `matcher.match()` devuelve un resultado nuevo, nunca limpia los campos cuando la re-evaluación ahora no encuentra nada (nunca puede pasar antes de este fix, porque el catálogo de PC/Xbox siempre "encontraba algo"). Verificado uno a uno con `matcher.match()` en vivo que esas 563 filas ya no matchean con nada — limpiadas a mano (`canonical_title`/`match_confidence`/`catalog_source` → `NULL`, con confirmación explícita del usuario) para que queden como "sin match" real en vez de con datos obsoletos. **Resultado final verificado**: 0 juegos con `catalog_source` IBM/Xbox; `plan` baja de 1.276 a **842 conflictos** (2.334 para renombrar, 5.369 ya correctos) |

---

### MATCH-HEADER-1 — Identidad por header interno del ROM para NDS/GBA (feature nueva, petición usuario 2026-09-12)

Origen: al revisar a mano los 7 conflictos NDS/GBA sueltos de `MATCH-FIX-3`
(Castlevania, Kirby, Naruto, From the Abyss), el usuario preguntó si no
sería mejor implementar una solución general en vez de arreglos caso a
caso. Los DATs No-Intro de este proyecto no traen número de serie —
`_build_review_queue` (`web/builders/duplicates.py`) solo puede enlazar
duplicados por SHA1 exacto o por coincidencia de título — así que un
archivo cuyo SHA1 no está en catálogo y cuyo nombre no coincide con nada
(un parche de traducción, un dump malo/incompleto) es invisible para
siempre, por muy claro que sea que es copia de un juego ya presente.

NDS y GBA sí llevan una identidad real y verificable en el propio header
del cartucho: un código de juego de 4 caracteres asignado por Nintendo,
globalmente único por edición — leerlo del archivo es un hecho, no una
suposición por nombre.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-HEADER-1 | `detection/rom_header.py` (nuevo): `extract_internal_id(path, extension)` lee el header NDS (código en offset `0x0C`), GBA (offset `0xAC`) y GB/GBC (título interno en `0x134`, sin código corto fiable). `_review_groups_for_repo` (`web/builders/duplicates.py`) añade una unión nueva por `(platform, internal_id)` — **solo para `.nds`/`.gba`**: el código de 4 caracteres es fiable para unir sin revisión humana; el título de GB/GBC (16 caracteres, puede truncar el texto que distingue dos juegos reales) se dejó fuera para no arriesgar falsos positivos que alimenten el "auto-resolver sin revisión" de `resolve-duplicates`. Deliberadamente **no** excluye nombres con marca de hack/traducción (`is_non_canonical_variant`) como sí hace la unión crossfmt — son exactamente el caso a rescatar. Razón nueva `"header"` en el grupo, con chequeo separado (`has_real_title_dup`, distinto del `has_title_dup` ya existente, más laxo) para no reclamarla cuando el grupo ya está explicado por sha1 o por título real compartido. **Hallazgo del usuario durante la revisión** ("¿puede ser que en GBA haya juegos de GBC?"): confirmado contra la BD real — 2 filas con `platform='Game Boy Advance'` cuyo `source_path` apunta a un `.md` de Sega Mega Drive real (mismo tipo de problema, aunque no era literalmente GBC). Sin el chequeo, esos bytes ajenos podrían leerse como un "código" válido y colisionar por casualidad. Blindado con dos filtros: GBA valida el byte fijo `0xB2 == 0x96` (constante real de todo cartucho GBA) antes de confiar en el código, y ambos (NDS+GBA) exigen que el código extraído sean 4 caracteres `[A-Z0-9]` — cualquier otra cosa se descarta como basura | `detection/rom_header.py` (nuevo), `web/builders/duplicates.py` | ✅ hecho 2026-09-12. 11 tests (`tests/test_rom_header.py`, incluye el caso real de blindaje), 3 tests (`tests/test_builders_duplicates.py`: rescata un parche sin match, no une juegos distintos, no duplica razón cuando ya hay sha1/título real). 1287 tests, ruff+format limpios. **Verificado contra la biblioteca real** (`F:\Juegos Retro`): 15 grupos nuevos encontrados, invisibles hasta hoy — ej. `"Megaman Zero 1 [E].gba"` ↔ `"Mega Man Zero (USA, Europe).gba"`, `"4832 - Pokemon - Edicion Oro HeartGold (S).nds"` ↔ `"Pokemon - Edicion Oro HeartGold.nds"` — y confirmado que las 2 filas Mega Drive mal etiquetadas ya no producen falso match. Solo agrupa (superficie para revisión/`apply_ra_conflicts`); no fuerza `canonical_title` ni borra nada por sí solo. **Follow-up no implementado**: investigar por qué esas 2 filas tienen `platform` incorrecto en primer lugar (bug de detección aparte, no tocado hoy); extender a GB/GBC con una señal más fuerte que el título truncado; usar el tamaño esperado del DAT como desempate de calidad de dump en `_review_entry_sort_key` |
| MATCH-FIX-14 | **✅ Hecho 2026-09-19** (roadmap 14, `fix/matcher-coverage-gaps`, solo Pasos 3-4 — Pasos 1-2 de `MATCH-FIX-3` siguen bloqueados por decisión del usuario). Resuelve los 2 follow-ups de arriba: **(a) GB/GBC** — `_read_gb_id` (`detection/rom_header.py`) ahora valida el checksum de cabecera estándar de Game Boy (offset `0x14D`, calculado sobre `0x134-0x14C` — tipo de cartucho, tamaño ROM/RAM, región, versión, licencia) y devuelve `título:checksum` en vez de solo el título truncado; si el checksum no coincide con los propios bytes del fichero, se trata como cabecera no fiable (`None`) — mismo criterio conservador que el byte fijo `0xB2==0x96` de GBA. `.gb`/`.gbc` añadidos a `_HEADER_EXTENSIONS` (`web/builders/duplicates.py`), antes solo `.nds`/`.gba`. **(b) Desempate por tamaño** — en vez de repetir una consulta al catálogo en cada carga de la cola de revisión (obligaría a cachear/instanciar `CatalogMatcher` ahí, sin patrón existente para eso), `_reference_size_bytes()` reutiliza un dato que ya vive en la fila: el tamaño de cualquier miembro del propio grupo con `match_confidence="high"` (un SHA1 exacto ya implica que su tamaño es el correcto) — nuevo `size_tier` en `_review_entry_sort_key`, justo tras `integrity_tier` | `detection/rom_header.py`, `web/builders/duplicates.py` (`_HEADER_EXTENSIONS`, `_reference_size_bytes`, `_review_entry_sort_key`) | ✅ 1395/1395 tests en verde (6 nuevos: 2 en `test_rom_header.py`, 3 en `test_builders_duplicates.py`), ruff+format limpios |

---

### MDFOLDER-FIX-1 — `detect_platform()` no reconocía "Sega Mega Drive" (dos palabras) como carpeta válida para `.md` (hallazgo 2026-09-12, petición usuario "investígalo")

Origen: investigando por qué 2 filas tenían `platform='Game Boy Advance'`
apuntando a archivos `.md` reales de Mega Drive (hallazgo de `MATCH-HEADER-1`,
el usuario preguntó "¿puede ser que en GBA haya juegos de GBC?"). Causa
raíz confirmada leyendo el código: `PLATFORM_CONTEXT_BY_EXTENSION[".md"]`
(`detection/platform_detector.py:66-68`) solo reconocía las carpetas
`{"megadrive", "genesis", "sega genesis", "md"}` — la carpeta real de esta
biblioteca es **"Sega Mega Drive"** (nombre oficial occidental, dos
palabras), que tokeniza a `{"sega","mega","drive"}` y no es superconjunto
de ninguna de las combinaciones aceptadas. `detect_platform()` devolvía
`None` para cualquier `.md` ahí, dejando el fallback por título de
`_match_by_title()` sin señal de plataforma real para desambiguar —
cualquier `.md` cuyo SHA1 no calzara exacto con el catálogo (bootlegs,
hacks, revisiones no catalogadas) podía terminar matcheado por título
contra **cualquier plataforma**, no solo GBA (confirmado: título colisionó
con el catálogo de Game Boy Advance por coincidencia). Alcance medido: 14
de 462 `.md` en esa carpeta.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MDFOLDER-FIX-1 | Añadir `"mega drive"` y `"sega mega drive"` al set de `PLATFORM_CONTEXT_BY_EXTENSION[".md"]` | `detection/platform_detector.py:66-68` | ✅ hecho 2026-09-12. 2 tests nuevos (`tests/test_platform_detector.py`), 89 tests del archivo en verde, 1289 tests totales, ruff+format limpios. **Re-matcheadas las 14 filas reales**: 13 recuperaron su plataforma y título correctos de Mega Drive (incluye `Micro Machines (USA).md`, que además destrababa uno de los conflictos de nombre medidos en `MATCH-FIX-5`); 1 (`Super Mario Bros. (Unl) [f1].md`, bootleg sin entrada real en el catálogo) se dejó sin match — mejor que un título GBA falso — y su `platform` corregido a `Sega Mega Drive` de todas formas (el campo describe el archivo, no si hubo match). 0 filas `.md` de esa carpeta con plataforma incorrecta tras el fix |
| MDFOLDER-FIX-2 | Generalizado tras `MDFOLDER-FIX-1`: `PLATFORM_BY_FOLDER` (`detection/platform_detector.py`, usado por `detect_platform()` para **toda** extensión ambigua — `.bin`/`.cue`/`.iso`/`.zip`/`.chd`/`.img`, no solo `.md`) solo tenía slugs cortos ("ps2", "nds", "gba"...) como claves — **7 de 11 carpetas reales de esta biblioteca no se reconocían en absoluto** (`PlayStation 2`, `Nintendo DS`, `Game Boy Advance`, `Game Boy Color`, `Game Boy`, `Sega Mega Drive`, `Sega Saturn`, `Game Gear` — verificado uno a uno contra `F:\Juegos Retro`). `_build_tables()` ahora registra también el nombre canónico completo en minúsculas como clave adicional (`by_folder.setdefault(canonical.lower(), canonical)` por cada valor distinto ya cargado) — nunca pisa una clave slug ya existente, solo añade | `detection/platform_detector.py:36-53` (`_build_tables`) | ✅ hecho 2026-09-12. 6 tests nuevos (parametrizados), 95 tests del archivo, 1295 tests totales, ruff+format limpios. **Medido contra la biblioteca real** tras `MATCH-STALE-1` (abajo): 8 archivos `.bin`/`.cue`/`.iso` en `PlayStation 2\` que estaban mal etiquetados como GameCube/Wii/Nintendo DS/PSP por la misma causa que `MDFOLDER-FIX-1` (títulos reales multi-plataforma — Crash Bandicoot, Sonic Heroes, Viewtiful Joe — coincidiendo por nombre con la versión de otra consola) corregidos a `PlayStation 2`. Los aparentes casos de Game Boy Color/Game Gear investigados aparte resultaron ser falsos positivos de la medición (texto "Game Boy Color" en el nombre de archivo, no la carpeta; `.sms` en carpeta `Game Gear\` es organización real intencional de esta biblioteca, no un bug) |

### MATCH-STALE-1 — El job de `match` nunca limpiaba un match viejo cuando la re-evaluación ya no encuentra nada (hallazgo 2026-09-12, patrón repetido 3 veces en la misma sesión)

Origen: mismo patrón encontrado y parcheado a mano tres veces hoy
(`MATCH-FIX-5`: 563 filas IBM/Xbox; `MDFOLDER-FIX-1`: 1 fila Mega Drive;
`MDFOLDER-FIX-2`: 8 filas PlayStation 2) — cada vez que un fix del matcher
hacía que una fila previamente mal-matcheada ahora correctamente no
matchee con nada, la fila se quedaba con el `canonical_title`/
`match_confidence`/`catalog_source` viejo para siempre, porque tanto
`rommgr match` (`cli.py:704`) como `POST /api/match`
(`web/handlers/scan.py`, `_do_match`) solo llaman `update_match()` cuando
`matcher.match()` devuelve un resultado nuevo — el caso "ya no hay match"
nunca escribe nada.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| MATCH-STALE-1 | Nuevo `repository.clear_match(source_path)` (`database/repositories/games.py`) — resetea `canonical_title`/`match_confidence`/`catalog_source` a `NULL`, deja `platform` intacto a propósito (describe el archivo, no si hubo match de catálogo). Llamado en la rama `else` de ambos loops de match (CLI y handler web) en vez de solo incrementar `unmatched` | `database/repositories/games.py`, `cli.py:704` (`match`), `web/handlers/scan.py` (`_do_match`) | ✅ hecho 2026-09-12. 1 test nuevo (`tests/test_repository.py::test_clear_match_resets_to_unmatched`), 1296 tests totales, ruff+format limpios. Verificado en vivo: tras el fix, un nuevo re-match (`include_low_confidence`) ya limpia solo cualquier fila que deje de matchear — no hará falta repetir la limpieza manual la próxima vez que se ajuste el matcher |

---

### ADB-TIMEOUT-1 — `push()`/`pull()` usaban el timeout genérico de 60s de comandos shell, abortaban transferencias grandes (hallazgo + petición usuario 2026-09-13)

Origen: probando el envío de un par de juegos de Dreamcast/PS2 a la
Anbernic para verificar el trabajo de hoy, el Cable Sync real (vía
`/api/cable-sync`) abortó el lote entero al llegar a un `.cdi` de 787 MB:
`Command [...] timed out after 60 seconds`. Causa confirmada leyendo el
código: `AdbTransport.push()`/`pull()` (`sync/adb_transport.py`) llaman
`self._run("push"/"pull", ...)` sin pasar un `timeout=` propio, así que
heredan el default de `AdbTransport.__init__` (60s) — pensado para comandos
shell rápidos (`ls`, `stat`, `mkdir`), no para copiar un archivo de cientos
de MB o varios GB por USB. Confirmado en vivo con `adb push` directo (sin
el límite de la app): el mismo archivo tardó 36s a 19.8 MB/s en condiciones
normales, pero más con contención de disco (el `organize-source` de esta
sesión compitiendo por el mismo disco) — cualquier variación real de
velocidad USB/dispositivo puede superar los 60s con ROMs de este tamaño
(hay `.iso` de PS2 de hasta 8 GB en esta biblioteca).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ADB-TIMEOUT-1 | Nuevo `_transfer_timeout(size_bytes)` en `adb_transport.py`: presupuesto de tiempo proporcional al tamaño (suelo de 2 MB/s + 60s de margen fijo, mínimo 120s) en vez de un valor fijo. `push()` ya conoce el tamaño local sin coste extra; `pull()` hace un `stat` remoto antes de tirar del archivo para conocerlo (mismo patrón que ya usaba para el tamaño de retorno, solo que ahora también antes de empezar) | `sync/adb_transport.py` (`push`, `pull`) | ✅ hecho 2026-09-13. 4 tests nuevos (`tests/test_adb_transport_transfer_timeout.py`, dispositivo falso que graba el `timeout` pasado a cada llamada). 1305 tests totales, ruff+format limpios. Verificado en vivo: los 4 juegos de prueba (Sonic Adventure, Crazy Taxi 2 — Dreamcast —, Viewtiful Joe 2, Dark Cloud — PS2 —) llegaron completos a la Anbernic tras el arreglo, confirmados por tamaño exacto en el dispositivo |

---

> Quedan pendientes: INBOX-FIX-4 (decisión de diseño sobre auto-apply del wizard)
> y la decisión del usuario sobre las 15 colecciones completas de
> JUNK-REVIEW-1 (categoría 2). MATCH-FIX-1/2 cerrados y re-match ya ejecutado
> sobre la biblioteca real (2026-08-29).

---

### INBOX-FIX-6 — ZIPs de consola (PS2 confirmado) se renombran/colocan pero nunca se descomprimen (hallazgo usuario 2026-08-29)

Origen: el usuario reporta que tras organizar la biblioteca con el Inbox, varios
`.zip` de PS2 (y sospecha que de otras plataformas) quedaron en su carpeta de
plataforma correcta, con nombre canónico, pero **sin descomprimir** — inútiles
para el emulador (PCSX2/AetherSX2 no leen un `.iso` dentro de un `.zip`).
Verificado en la biblioteca real (`library_pc.db`): 20 `.zip` en `ps2\` con
`platform: PlayStation 2` y nombre canónico correcto, `created_at` repartido en
varias tandas (2026-03-24, 2026-08-28 en tres lotes) — no es un caso aislado ni
antiguo, sigue ocurriendo con datos recientes.

Causa raíz confirmada leyendo el código: hay **dos únicos caminos que
descomprimen un ZIP** en toda la app — `_run_inbox_pipeline` (`web/inbox_pipeline.py:955`,
`find_zip_files(inbox)`) y `_run_setup_pipeline` (`:818`) — **ambos escanean
solo dentro de una carpeta concreta** (`inbox/`, o la carpeta de origen del
wizard). El flujo general de Organizar/Renombrar (`web/handlers/organize.py::_do_apply`,
líneas 92-162) **no tiene ninguna llamada a `extract_zip` en todo el archivo**
— solo `rename_rom_with_saves` (mover + renombrar, nunca descomprimir). Un
`.zip` de consola identificado por CRC (`CatalogMatcher.crc_index()`, ZIP-ROUTE-1)
o que ya vivía suelto dentro de `ps2\` antes de pasar por match/plan/apply
termina con nombre y ubicación correctos pero **sigue siendo un `.zip` para
siempre** — el diseño original de ZIP-ROUTE-1 ya lo advertía ("el mover/renombrar
queda para cuando exista plan/apply de misplaced") pero esa segunda mitad
(descomprimir tras colocar) nunca se cerró para el flujo general, solo para el
que pasa por el Inbox real.

**Respuesta a la pregunta del usuario sobre arcade**: no, con arcade NO hay que
descomprimir — es una decisión de diseño ya tomada y correcta (`zip_router.py`,
regla documentada en `.claude/CLAUDE.md`: "un ZIP arcade nunca se extrae, el ZIP
es el ROM" — los cores MAME/FBNeo leen el `.zip` directamente). El problema es
específico de plataformas que necesitan el archivo crudo (PS2, GameCube y
cualquier otra fuera de `arcade`/`mame`/`cps1-3`/`fbneo`/`neogeo`).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| INBOX-FIX-6 | `_do_apply` ahora llama a `extract_zip(target_path, delete_source=True)` tras cada rename exitoso a `.zip` — reutiliza el guard de `extract_zip` (arcade/MAME por carpeta destino, se auto-excluye). Causa raíz secundaria encontrada al testear con datos reales de PS2: el guard de `extract_zip` rechazaba **cualquier** ZIP con `.iso` dentro ("usa el conversor CHD"), que es exactamente el caso PS2 reportado — no hay pipeline de CHD para PS2/GameCube en la app (solo `.cue`/`.gdi` de PSX/Saturn/Dreamcast lo tienen), así que un `.iso` suelto sin `.cue`/`.gdi` compañero es un archivo reproducible por sí solo. Guard reducido a solo `.cue`/`.gdi` (sets multi-track reales) — un `.iso`/`.bin` sin ninguno de esos dos ya se extrae. 8 tests nuevos (`test_zip_extractor.py`, `test_organize_apply_zip_extract.py`), suite completa en verde salvo los 3 fallos preexistentes de ADB (dependen de que no haya dispositivo conectado) | `web/handlers/organize.py::_do_apply`, `converters/zip_extractor.py` (`extract_zip`, guard `_DISC_SET_EXTENSIONS`) | ✅ hecho 2026-08-30 |

---

### INBOX-ORPHAN-3 — Carpetas vacías con nombre de juego directamente en la raíz de la biblioteca (hallazgo usuario 2026-08-29)

Origen: el usuario encontró carpetas como `Legend of Zelda, The - Twilight
Princess (USA)` directamente en `E:\Carpetas anbernic\` (fuera de `gamecube\`),
vacías o con solo una subcarpeta `media\` residual, en vez de tener el juego
organizado dentro de su plataforma. Verificado: **~40 carpetas** de este tipo
en la biblioteca real, la mayoría creadas el 2026-08-13 22:10 (mismo incidente
de `INBOX-CFG-1`, ya archivado), pero **siguen apareciendo nuevas** — 3 el
2026-08-28 y **2 hoy mismo, 2026-08-29** (`Monster World IV`, `X-Men Legends II
- Rise of Apocalypse`, creadas justo después de la corrida real de re-match de
`MATCH-FIX-2` sobre toda la biblioteca) — no es solo un residuo histórico, el
mecanismo que las genera sigue activo.

Causa raíz confirmada leyendo el código: `_DISC_SUBFOLDER_PLATFORMS`
(`planner/operation_planner.py:15-24`) incluye `gamecube`, `ps2` y `wii` junto
a las plataformas que sí son sets multi-track (`psx`, `saturn`, `dreamcast`)
que necesitan una subcarpeta por juego (`psx/Juego/Juego.cue` + sus `.bin`).
GameCube/PS2/Wii casi siempre son una imagen única (`.iso`/`.rvz`/`.chd`) que
**no necesita ninguna subcarpeta** — al tratarlas igual, `build_plan()`
(`operation_planner.py:136-142`) calcula el destino como
`source.parent.parent / folder_name / new_filename` cuando el archivo ya vive
en una carpeta mal ubicada (ni bajo el nombre de la plataforma ni ya en
subcarpeta), lo que **preserva y reproduce la ubicación equivocada** en vez de
corregirla a `platform/Juego.ext` plano. Y como ningún código de renombrado
(`rename_rom_with_saves`, `move_disc_set_to_subfolder`) borra el directorio de
origen tras dejarlo vacío (comportamiento normal de mover un archivo, no un
bug en sí), cada vez que un juego mal ubicado se corrige a mano o se vuelve a
tocar (re-match, re-organize) la carpeta vieja se queda huérfana para siempre
en la raíz.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| INBOX-ORPHAN-3 | Quitar `gamecube`/`ps2` de `_DISC_SUBFOLDER_PLATFORMS` (Wii confirmado que sí necesita subcarpeta — mezcla real de Virtual Console + dumps nativos multi-archivo, se deja igual que psx/saturn/dreamcast). Causa raíz real: ningún código de rename limpiaba la carpeta origen tras dejarla vacía — se añadió `_cleanup_empty_source_dir()` en `file_renamer.py`, compartida por `rename_rom_with_saves`/`move_disc_set_to_subfolder`, con guard que solo actúa si origen y destino son hermanos dentro de la misma plataforma (nunca toca la carpeta raíz de una plataforma). Barrido one-off ejecutado sobre la biblioteca real: 63 carpetas vacías dentro de plataforma (`dreamcast` 7, `ps2` 2, `wii` 54) + 39 carpetas huérfanas en la **raíz** de la biblioteca (mismo bug, casos donde el juego ya vivía mal ubicado) + 2 carpetas con solo `media/` residual (artwork movido a `dreamcast/media/{images,wheels}/` antes de borrar, no descartado) — 104 carpetas eliminadas en total, 0 restantes. 8 tests nuevos (`test_operation_planner.py`, `test_file_renamer.py`), 1067 tests en verde (3 fallos preexistentes en `tests/web/test_retroarch_override_*`/`test_detect_android_ra_config_dir_endpoint.py` no relacionados — dependen de que NO haya un dispositivo ADB conectado, y la RG556 está conectada). | `planner/operation_planner.py:15-24`, `renamer/file_renamer.py` | ✅ hecho 2026-08-30 |
| INBOX-ORPHAN-4 | Confirmado leyendo el header RVZ (`iso_file_size` en offset 36, formato WIA/RVZ): las 4 parejas comparten el mismo tamaño de ISO original sin comprimir (1.459.978.240 B, tamaño estándar de disco GameCube) — mismo dump, la copia de la raíz solo está peor comprimida (nivel RVZ distinto, creada 2026-08-13 en el mismo incidente que INBOX-ORPHAN-3/CFG-1; la de `gamecube/` es de 2025-02-23). Comparación por RA descartada — ver hallazgo INBOX-RA-HASH-GAP, ningún `.rvz` de esta librería puede compararse por RA hoy. Backup de `library_pc.db` en `.rommgr/backup_inbox_orphan4_2026-08-30/` antes de tocar nada; borrados los 4 `.rvz` de la raíz + sus filas de BD (`cascade_delete_games_by_source_path`) + las 4 carpetas ya vacías. Copias de `gamecube/` verificadas intactas tras el borrado. | — | ✅ hecho 2026-08-30 |
| INBOX-RA-HASH-GAP | Hallazgo derivado de INBOX-ORPHAN-4: `games.md5` (`hashing/hash_calculator.py:41`, `hashlib.md5()` sobre los bytes crudos del archivo) es un hash de **archivo completo**, pero el hash que usa RetroAchievements para GameCube/Wii (y cualquier formato de disco comprimido: RVZ, CHD) se calcula sobre datos específicos extraídos del **disco descomprimido** (boot.bin/apploader/dol vía `rc_hash`), no sobre el contenedor comprimido. Verificado contra `ra_cache/ra_hashes_16.json` (236 juegos, 332 hashes únicos): ninguno de los 8 md5 de las 4 parejas de INBOX-ORPHAN-4 aparece en la caché — ni la copia "buena" ni la "mala". Consecuencia real: `ra_duplicates_service.py` (`get_ra_achievements`, `apply_ra_conflicts`, `filter_duplicate_winners`) siempre devuelve -1 (sin RA) para cualquier `.rvz`/`.chd` de disco, aunque el juego sí tenga logros en RA — la comparación por RA solo funciona hoy para ROMs de cartucho sin comprimir. Implementar el hash real de RA para discos requeriría parsear el filesystem GameCube/Wii (o el `.chd`) para extraer las regiones exactas que hashea `rc_hash` — feature nueva, no un fix puntual. | `hashing/hash_calculator.py`, `services/ra_duplicates_service.py` (`get_ra_achievements`) | ✅ hecho 2026-09-15 (roadmap `17-inbox-pending-features.md`, rama `feature/inbox-ra-hash-gap`), con alcance acotado tras investigar (Paso 6): **algoritmo real** (`src/rhash/hash_disc.c` de rcheevos, descargado y leído verbatim, no resumido) reimplementado en `retroachievements/ra_hash_gamecube_wii.py` — GameCube hashea la cabecera del apploader + los 18 segmentos no vacíos de `main.dol`; Wii hashea cabecera principal + código de región + por partición (saltando la de tipo `1`, "update") la metadata (TMD) + los datos, leídos **sin necesidad de AES**: si el disco sigue cifrado, RA hashea los bytes cifrados tal cual (solo salta los 0x400 bytes de cabecera de hash de cada cluster de 0x8000) — solo si ya está descifrado se reusa el mismo algoritmo de apploader/DOL que GameCube, con el offset desplazado 2 bits. **Verificado con datos reales**: 2 de los 8 `.iso` de `gamecube/` (Wind Waker, Metroid Prime 2: Echoes) hashean exactamente al MD5 real cacheado en `ra_cache/ra_hashes_16.json` — mismo método de prueba que `ra_hash_psx.py`. GameCube es el confirmado; Wii se implementó fiel a la fuente pero **sin verificar contra datos reales** — esta biblioteca no tiene ningún disco Wii comercial (`wii/` solo tiene un WAD homebrew). **Alcance real acotado tras medir la biblioteca**: de 20 juegos en `gamecube/`, 15 son `.iso` (crudo, soportado) y 5 son `.rvz` (formato comprimido de Dolphin) — `.rvz` devuelve `None` deliberadamente, no hay herramienta de descompresión en este proyecto (a diferencia de `.chd`, que ya usa `chdman`) y añadir una violaría "sin dependencias externas de runtime". Integrado en `ra_checker.py` (`_DISC_HASH_CONSOLE_IDS` ahora incluye 16/20 además de 12) y en `ra_duplicates_service.py::get_ra_achievements_for_path` (usada por `apply_ra_conflicts`) — mismo patrón de caché por archivo que ya usaba PSX (`ra_disc_hash_cache.py`, nuevo `gamecube_wii_disc_hashes.json` separado). **Hallazgo colateral, arreglado 2026-09-15 (misma rama, a petición explícita del usuario)**: `filter_duplicate_winners` recibía cada entrada como un `dict` con `md5` ya calculado, sin pasar por `source_path` — parecía requerir cambiar su firma, pero los `dict` reales que le llega (`repository.get_games_paginated(...)`, el único caller real en `web/handlers/sync_cable.py`) **ya traen `source_path`**, solo que la función no lo usaba. Se añadió el mismo dispatch por `console_id` (PSX/GameCube/Wii → `get_ra_achievements_for_path`, el resto sigue usando el `md5` ya calculado sin consulta extra a la BD) dentro del propio `_key()` de la función, sin tocar su firma pública. 1 test nuevo (`test_ra_bulk_send_dedup.py`, GameCube con hash real vs. archivo no reconocido). 1340 tests totales, ruff+format limpios |
| INBOX-ORPHAN-5 | **Investigado 2026-09-08 contra `E:\Carpetas anbernic` real** — de las 9 carpetas display originales solo **5 siguen existiendo** (`Master System`, `Game Boy`, `Game Boy Advance`, `Game Boy Color` ya no están, limpiadas en algún momento entre el hallazgo y hoy, sin rastro de cuándo). De las 5 restantes, **no son todas del mismo caso** — comparado archivo por archivo (ruta relativa dentro de `media/`) contra la carpeta slug real: `Nintendo DS` (6 archivos) **sí es duplicado exacto** de `nds/media/images` — mismo nombre, ya presente, seguro de descartar. `Game Gear` (58: 29 imágenes+29 wheels), `Atari 2600` (12: 6+6), `NGC`→`gamecube` (42: 21+21) y `Famicom Disk System`→`fds` (4: 2+2) **NO son duplicados — son artwork real que falta en la carpeta slug**: confirmado que el ROM sí existe en la carpeta real (p. ej. `gamegear/Ristar (World).gg`, `atari2600/Asteroids (Japan, USA) (En).a26`, `gamecube/Pikmin (Europe)...iso`, `fds/Super Mario Bros. 2 (Japan) (En).fds`) pero su imagen no está en `<slug>/media/images/` — `gamecube/media/` y `fds/media/` ni siquiera existen hoy (0 imágenes para esas 2 plataformas en toda la biblioteca), y `gamegear`/`atari2600` solo tienen scrapeadas 239/1599 y 47/729 ROMs respectivamente. Cero colisiones de nombre entre orphan y real en los 4 casos (ninguna ruta relativa coincide), así que un merge sería seguro sin sobreescribir nada. Origen: casi seguro un scrape viejo hecho antes de renombrar esas carpetas al slug (ES-DE usaba el nombre display), nunca migrado. **Ejecutado 2026-09-08, con confirmación explícita del usuario antes del borrado**: movidas las 116 imágenes únicas (`Game Gear`→`gamegear` 58, `Atari 2600`→`atari2600` 12, `NGC`→`gamecube` 42, `Famicom Disk System`→`fds` 4) con `mv -n` (verificado después que las 4 carpetas quedaron con 0 archivos, ningún `mv` saltó por colisión); verificados los 6 archivos de `Nintendo DS` byte a byte (`cmp`) contra `nds/media/images` antes de darlos por duplicado exacto. Borradas las 5 carpetas display-name completas — ninguna contenía ROMs. Único efecto colateral esperado: `gamecube/media/` y `fds/media/` pasan de no existir a tener su primer artwork (42 y 4 archivos respectivamente); esas dos plataformas seguían con 0 imágenes en el resto de sus ROMs. Solo movimiento/borrado de archivos de artwork en el filesystem — sin tocar `library_pc.db`/`library_android.db` (la media no está indexada en SQLite). | `E:\Carpetas anbernic\{gamegear,atari2600,gamecube,fds,nds}\media\` | ✅ hecho 2026-09-08 |

---

### INBOX-ANBERNIC-1 — Checkbox opt-in en el Inbox para enviar el ROM recién organizado a la Anbernic (petición usuario 2026-09-12)

Plan de implementación (junto a `INBOX-ATOMIC-1` e `INBOX-RA-HASH-GAP`) en
`.claude/roadmaps/archivo/17-inbox-pending-features.md`.

Origen: conversación 2026-09-12 — el usuario preguntó si el Inbox podía pasar
juegos directamente a la Anbernic. Hoy el Inbox (Pilar 2) solo organiza en el
PC; llevar el juego a la consola exige pasar aparte por Juegos (marcar tag
`anbernic`, `ANBERNIC-PICK-1`) + Cable Sync (`ANBERNIC-PICK-2`) o por el botón
"Enviar" de Juegos (`ANBERNIC-PICK-8`, `direction="send_selected"` en
`_do_cable_sync`, `web/handlers/sync_cable.py`). Decisión explícita del
usuario: **no automático** — checkbox opt-in por corrida (o por archivo) en
la UI del Inbox, no un push silencioso de todo lo que se organiza.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| INBOX-ANBERNIC-1 | Checkbox "Enviar a la Anbernic tras organizar" en la pestaña Inbox — global por corrida (confirmado con el usuario 2026-09-17), opt-in, sin persistir entre corridas. En vez de reutilizar el job `direction="send_selected"` de `_do_cable_sync` (habría levantado un segundo panel de progreso, fuera de alcance), se reutiliza el primitivo de más bajo nivel `AdbTransport.push()` directamente dentro del propio job de Inbox — misma verificación MD5 condicional (`should_verify`), mismo registro en `save_sync_log` (`log_sync_event`). Nueva función `_send_organized_to_anbernic()` en `inbox_pipeline.py`, llamada al final del paso "organize" sobre la lista de archivos recién movidos con éxito. Sin dispositivo único conectado (`resolve_single_device_transport`): aviso (`anbernic_warning`), el resto del job de Inbox sigue igual. Cualquier fallo (push individual o resolución de dispositivo) queda capturado — nunca tumba el pipeline completo, que ya organizó con éxito en el PC. 4 tests nuevos (`test_inbox_anbernic_send.py`), 1347 tests totales, ruff+format limpios | `web/inbox_pipeline.py`, `web/handlers/inbox.py`, `web/static/partials/tab-inbox.html`, `web/static/js/tabs/inbox.js`, `tests/test_inbox_anbernic_send.py` | ✅ hecho 2026-09-17 (roadmap `17-inbox-pending-features.md`) |

---

### INBOX-ATOMIC-1 — Mover el archivo y actualizar la fila de BD no son atómicos en `_organize_matched_games` (hallazgo roadmap 08 `fix/error-handling`, 2026-09-13)

Origen: investigación del roadmap `.claude/roadmaps/archivo/08-fix-error-handling.md`
(hallazgo 3, revisión de bloques `except Exception` reales del proyecto).
Plan de implementación del fix en `.claude/roadmaps/archivo/17-inbox-pending-features.md`.
`inbox_pipeline.py` (paso "Move to platform folders"):

```python
try:
    _shutil.move(str(source_file), str(dest_file))
    dest_path_str = str(dest_file.resolve())
    with repository.batch() as conn:
        cascade_delete_games_by_source_path(conn, dest_path_str, exclude_id=game_id)
        conn.execute(
            "UPDATE games SET source_path=?, original_filename=? WHERE id=?",
            (dest_path_str, dest_file.name, game_id),
        )
    organized += 1
except Exception as exc:
    organize_errors.append(f"{source_file.name}: {exc}")
```

Si `_shutil.move` tiene éxito pero el `UPDATE`/`cascade_delete` que sigue
falla (SQLite bloqueada, disco lleno, lo que sea), el archivo físico ya está
en `dest_file` pero la fila de `games` **sigue apuntando al `source_path`
viejo dentro del Inbox, que ya no existe**. Viola "toda operación sobre
archivos se registra en SQLite" (`CLAUDE.md`) de forma silenciosa: el
usuario solo ve `"nombre.zip: <mensaje de excepción sqlite>"` en
`organize_errors` — nada le dice que el archivo SÍ se movió y que ahora hay
un descuadre real entre disco y BD para ese juego concreto. No es un caso de
"excepción tragada" (el error llega a la UI), es un **hueco de atomicidad**
con un mensaje de error que no transmite el riesgo real.

**Arreglado 2026-09-15** — el código ahora invierte el orden y mete el move
dentro del propio bloque `batch()`:

```python
try:
    dest_path_str = str(dest_file.resolve())
    with repository.batch() as conn:
        cascade_delete_games_by_source_path(conn, dest_path_str, exclude_id=game_id)
        conn.execute(
            "UPDATE games SET source_path=?, original_filename=? WHERE id=?",
            (dest_path_str, dest_file.name, game_id),
        )
        _shutil.move(str(source_file), str(dest_file))
    organized += 1
except Exception as exc:
    organize_errors.append(f"{source_file.name}: {exc}")
```

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| INBOX-ATOMIC-1 | Decidir la política: (a) reintentar el `UPDATE`/`cascade_delete` en un `finally` separado antes de dar el archivo por fallido, (b) revertir el `_shutil.move` (mover el archivo de vuelta al Inbox) si el paso de BD falla, o (c) como mínimo, mejorar el mensaje de `organize_errors` para que nombre explícitamente el riesgo real (`"archivo movido a {dest_file} pero la base de datos no se pudo actualizar — revisar a mano"`) en vez del mensaje crudo de la excepción SQLite. No implementar sin decisión explícita del usuario — cambia el comportamiento del Pilar 2 en el camino de fallo | `web/inbox_pipeline.py` (paso "Move to platform folders") | ✅ hecho 2026-09-15, a petición explícita del usuario (rama `feature/inbox-atomic-1`). Variante de (a) más simple que reintentar en un `finally`: se invierte el orden (`UPDATE`/`cascade_delete` primero, `_shutil.move` al final) **dentro del mismo bloque `repository.batch()`** — una excepción en cualquier punto del bloque (incluido el propio move) hace que `batch()` haga rollback de la BD antes de propagar, así que un fallo del move deja la fila tal y como estaba (apuntando a donde el archivo sigue estando de verdad), y un fallo de la BD nunca llega a intentar el move. Único hueco residual no evitable sin una transacción distribuida real: que el `commit()` en sí falle *después* de un move ya exitoso (ej. disco lleno en el commit) — caso mucho más raro que el original (que se disparaba con cualquier fallo de BD tras el move). 2 tests nuevos (`test_inbox_pipeline_organize.py`: fallo del move tras el `UPDATE` revierte la BD; fallo de la BD nunca llega a llamar al move), 1332 tests totales, ruff+format limpios |

---

### INBOX-UX — Cierre visible de sesión y metadata al vuelo (idea usuario 2026-09-22)

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| INBOX-SESSION-SUMMARY-1 | Resumen visible al terminar un job de Inbox/organize (N organizados, N con conflicto, N sin match) en vez de tener que revisar logs | `web/inbox_pipeline.py`, `web/static/js/tabs/inbox.js` | ✅ hecho 2026-09-22 (rama `feature/inbox-ux-summary-metadata`) — investigado primero: el panel de resumen (`_renderInboxResult`) y casi todos los contadores ya existían; solo faltaba destacar "sin match" (`unmatched`, juegos organizados sin `platform`), añadido junto a `scraped` |
| INBOX-METADATA-INLINE-1 | Confirmar si portada/metadata ya se aplican automáticamente al organizar desde el Inbox (el scraper existe pero no está claro si dispara en el mismo job); si no, integrarlo | `services/scrape_service.py` (nuevo), `web/inbox_pipeline.py`, `web/handlers/scraper.py`, `config.py` | ✅ hecho 2026-09-22 — confirmado que no se aplicaba automáticamente. `_do_scrape_single` extraído a `scrape_game_metadata()` (servicio reutilizable, sin `ctx` HTTP) y enganchado al organize vía `_scrape_organized_games()`, opt-in (`config.inbox.scrape_on_organize`, apagado por defecto). Un solo `ScreenScraperClient` para todo el lote (su throttle es por instancia). 12 tests nuevos, 1452 pass, ruff+format limpios |

---

---

