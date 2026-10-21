## Pilar 1 — Limpieza y organización inicial de la biblioteca — → #202

Detectar basura, clasificar ZIPs sueltos y dejar la biblioteca organizada por
plataforma con nombre canónico.

### PSX-STRUCTURE — Auditoría de estructura de `psx/` (2026-09-02, a petición del usuario)

| ID | Task | Notas |
|----|------|-------|
| RA-HASH-SUBDIR-1 | **Bug encontrado 2026-09-02** verificando `Tekken 3 (USA).bin` (Anbernic) para reparación cruzada: `ra_hash_psx.py::_find_boot_executable` (línea 178) solo busca el ejecutable de arranque en el directorio raíz ISO9660. `SYSTEM.CNF` de Tekken 3 apunta a `cdrom:\TEKKEN3\SLUS_004.02;1` (subcarpeta) — `_parse_boot_exe_name` (línea 146) solo pela las barras invertidas *iniciales*, así que `exe_name` queda como `"TEKKEN3\SLUS_004.02"` con la barra interna intacta, y `_find_root_file` (línea 106, solo mira la raíz) nunca lo encuentra → `compute_psx_ra_hash` devuelve `None` en silencio para cualquier juego cuyo BOOT= viva en subcarpeta (patrón común en PS1, no es solo Tekken 3). Root cause confirmado leyendo el `SYSTEM.CNF` real del disco, no solo síntoma. **✅ Arreglado
2026-09-02** (rama `fix/ra-hash-psx-subdir-boot`, [PR #286](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/286), mergeado a `develop`): `_find_root_file` reescrito para
recorrer cada componente de ruta separado por `\` (nuevo `_root_dir_location` + `_find_entry`
genérico con flag de directorio) antes de buscar el fichero final, en vez de mirar solo el
directorio raíz. Verificado contra `Tekken 3 (USA)` real: el hash ahora coincide exactamente con la
entrada real de RA (id 11259, "Tekken 3", 81 logros) en vez de devolver `None`. Test nuevo
`test_compute_psx_ra_hash_boot_in_subdirectory`. 1132/1132 tests en verde, `ruff` limpio. Recálculo en frío contra la biblioteca PSX real (1.175 ROMs): 324 pasan a tener hash calculable y coincidente con RA | `src/rom_manager/retroachievements/ra_hash_psx.py:106-178` | ✅ arreglado y mergeado ([PR #286](https://github.com/Rcerezo-dev/Retro-gaming-companion/pull/286)) |
| PSX-STRUCTURE-1 | **Recuento exacto 2026-09-02** (parseo real de `FILE` en cada `.cue`, no solo conteo): `H:\ROMs\psx` tenía **78 `.cue` que referencian algún `.bin` inexistente**. Tras descartar los que ya tienen un `.chd` con el mismo nombre (cue obsoleto, juego ya convertido — 45 casos) y los que viven en `_descartados/` (copia ya perdedora, 6 casos), quedaban **33 sets realmente rotos/en riesgo**. **2 reparados el mismo día** usando `.bin` sanos hallados huérfanos en `E:\Carpetas anbernic\psx` (ver PSX-STRUCTURE-2): `Wild Arms (USA)` y `Tekken 3 (USA)` (ver `RA-HASH-SUBDIR-1`). Quedaban 31 sin tocar. **Revisión caso a caso completada 2026-09-02 (sesión siguiente)**: el hallazgo real es que **la inmensa mayoría (28/31) NO era pérdida de datos** — eran huérfanos de ANTES de la migración a subcarpeta-por-juego (`.cue` sueltos en la raíz de `psx/`, referenciando nombres de pista que ya no existen porque el juego se reorganizó en su subcarpeta con un `.bin` distinto), o casos donde `resolve-duplicates` de ayer descartó a `_descartados/` un `.chd` sano de otra región/edición mientras dejaba como "canónico" un set roto de otra edición — el juego seguía disponible, solo mal señalizado. Reparado con confirmación del usuario: **4 `.cue` de 1 pista regenerados** sobre `.bin` intactos que solo les faltaba el sidecar (`Hogs of War (Europe)`, `MediEvil 2 (Europe) (Es,It,Pt)`, `Dino Crisis (Spain)`, `Tomb Raider III - Adventures of Lara Croft (Spain)`); **11 `.chd` sanos restaurados** desde `_descartados/` a su propia subcarpeta (`Namco Museum Vol. 1/3/4 (USA)`, `Tekken 2 (USA) (Rev 1)`, `Twisted Metal III (USA) (Rev 1)`, `Resident Evil 2 - Dual Shock Ver. (USA) (Disc 1/2)`, `Theme Park (World)`, `Small Soldiers (USA, Europe)`, `Gundam Battle Assault (USA)`, `Darkstalkers - The Night Warriors (USA)`, `Street Fighter Alpha - Warriors' Dreams (Europe)`); **2 `.bin` de `Parasite Eve II (Spain)` Disc 1/2** reubicados desde carpetas mal nombradas a su carpeta correcta con `.cue` nuevo, más sus `.chd` USA de respaldo también restaurados. Todos los `.cue`/`.bin`/carpetas huérfanas ya superados movidos a `_descartados/` (nunca borrados). BD refrescada, 0 errores. **Quedan 3 sin tocar, documentados para re-descarga** (sin backup real en ninguna biblioteca, decisión del usuario de no mezclar pistas sueltas de otra región sin verificar): `Mortal Kombat 3 (Europe)` (59/62 pistas, sin `.chd` de respaldo en ninguna parte), `Street Fighter Collection (USA) (Disc 1) (v1.1)` y `Street Fighter Collection (Europe) (Disc 1)` (a ambos les falta justo la pista de datos; solo hay un fragmento `.chd` suelto de esa pista con nombre USA en `_descartados/`, no un disco completo verificado) | `H:\ROMs\psx\*.cue` | 🟡 en progreso, 30/33 reparados, 3 pendientes de re-descarga |
| PSX-STRUCTURE-2 | `E:\Carpetas anbernic\psx`: **0 archivos `.cue`** (formato dominante `.chd`, 214 — correcto) y tenía **93 `.bin` sueltos sin ningún `.cue`**. Clasificados 2026-09-02: **33 confirmados no-PSX por CRC32 real contra el `.dat` de MAME** (no solo por nombre) — 8 `gunbird` (backup íntegro ya en `H:\ROMs\arcade\mame\gunbird.zip`, verificado con `unzip -t`, residuo puro), y 25 más repartidos en `cosmos` (11/13 ROMs, Century Electronics 1981), `sub` (10/17 ROMs, "Submarine" de Sigma 1985), `viper` (solo EEPROM, Leland 1988), `ega` (BIOS de tarjeta gráfica compartida, no un juego) y `hc_u107.bin` (MCU compartida por ~10 juegos "hidden catch" de Universal, sin poder identificar cuál exactamente) — estos 25 sin backup en ninguna biblioteca y ya incompletos desde antes de hoy (faltaban PROMs/ROMs de programa, no es daño de `decompress`). **✅ Los 33 borrados 2026-09-02 con confirmación del usuario** (BD refrescada, 33 huérfanos limpiados, coincide exacto). Quedan **60 sí son juegos/demos PSX reales**, sin tocar. De esos 60, investigados a fondo 2026-09-02 (comprobación de tamaño de sector, no solo nombre): **59 son sectores raw MODE2/2352 válidos (tamaño múltiplo exacto de 2352 bytes)** — estructuralmente sanos, solo les falta el `.cue` sidecar, recuperables generando uno mínimo (1 pista). Solo **`D (Europe) (Disc 1).bin` está realmente roto — 1024 bytes**, no es una imagen de disco, pérdida real de ese archivo. Dos casos destacables por tamaño casi de CD completo y coinciden en nombre con sets ya rotos de `H:\ROMs\psx` (PSX-STRUCTURE-1): **`Wild Arms (USA).bin` (607,6 MB)** y **`Tekken 3 (USA).bin` (603,2 MB)** — candidatos fuertes para reparar esos mismos sets en el PC copiando el `.bin` de Anbernic. `Street Fighter Alpha - Warriors' Dreams (USA).bin` (7,7 MB) también coincide de nombre pero es demasiado pequeño para ser el mismo rip que el del PC (que usa pistas separadas) — revisar a mano antes de asumir que sirve. Wild Arms/Tekken 3 ya usados para reparar `H:\ROMs\psx` (ver PSX-STRUCTURE-1). **✅ `.cue` generados 2026-09-02 (sesión siguiente)**: nuevo comando `rommgr generate-cues <path> [--apply]` (dry-run por defecto, reutiliza `detect_bin_cue_mode`/`synthesize_cue_text` ya existentes en `chd_converter.py`, sin exigir hash RA verificado — a diferencia de `find_bare_bin_files`/`convert-chd`, aquí no hace falta porque un `.cue` sidecar es 100% reversible). Ejecutado en real: **33 `.cue` escritos** (no 59 — de los ~60 restantes, 2 ya tenían `.cue` de sesiones previas — Wild Arms, Tekken 3 — y ~24 más no aparecieron como bare-bin en esta pasada, pendiente de investigar por qué en `PSX-STRUCTURE-2b`). Bug real encontrado y arreglado de paso durante la verificación: `_detect_geometry` (`ra_hash_psx.py`) devolvía `MODE1/2048` por defecto para cualquier fichero sin evidencia real de geometría — reproducido con un chip de ROM arcade (`mpr-15574.bin`, dentro de `_descartados/`) que se detectaba como PSX válido; ahora devuelve un sentinel que hace que `detect_bin_cue_mode` devuelva `None`. También se excluyó `_descartados/` de los candidatos (nunca debe "recuperarse" algo ya descartado). Tests nuevos: `test_detect_bin_cue_mode_rejects_file_with_no_geometry_evidence`, `test_find_bins_needing_cue_*`, `test_generate_missing_cues_*`. 1137/1137 verde, ruff limpio | `E:\Carpetas anbernic\psx\*.bin`, `converters/chd_converter.py`, `retroachievements/ra_hash_psx.py`, `cli.py` | 🟡 en progreso (`feature/psx-structure-2-generate-cues`), 33 `.cue` generados, `D (Europe) (Disc 1).bin` roto sin decidir, ~24 restantes sin explicar (`PSX-STRUCTURE-2b`) |
| PSX-STRUCTURE-2b | ✅ **Investigado 2026-09-02, no es bug**: la cifra "59 sanos" (punto 12 del diario) se calculó **antes** de que los puntos 12-13 del mismo día borraran 26 demos/protos/betas + 1 stub corrupto y repararan Wild Arms/Tekken 3 — dejando ~31 candidatos reales, no 59. `generate-cues` encontró 33, dentro del margen de que la clasificación manual "sano" (múltiplo de 2352) es más laxa que el chequeo real de geometría (`detect_bin_cue_mode`). Verificado en vivo contra `E:\Carpetas anbernic\psx`: **0 `.bin` sueltos sin `.cue` restantes** (35 `.bin` totales, todos con `.cue`). `PSX-STRUCTURE-2` cerrada del todo, sin cambio de código necesario | `E:\Carpetas anbernic\psx\` | ✅ hecho |
| PSX-STRUCTURE-3 | **✅ `E:\Carpetas anbernic` resuelto 2026-09-03** (decisión del usuario: reclasificar). Recuento fresco (la biblioteca creció desde el `605` de hace unos días): **903 archivos mal ubicados por extensión** en 26 carpetas de plataforma (script ad-hoc, `PLATFORM_BY_EXTENSION`/`AMBIGUOUS_EXTENSIONS`/`PLATFORM_BY_FOLDER` de `detection/platform_detector.py`, extensión no ambigua ≠ plataforma real de la carpeta contenedora — `arcade/` excluida, se audita por CRC no por extensión). Se descartó usar `organize-source` a secas: su dry-run reprocesa y renombra **todo** el contenido de cada carpeta, no solo lo mal ubicado (p. ej. `gb/` mostraba 3176 "a organizar" cuando solo 73 eran NES mal puesto) — fuera de alcance de esta tarea, ver `LIBRARY-REPAIR-TOOLING`/`REPAIR-TOOL-8` más abajo. En su lugar, movimiento dirigido (mover sin renombrar, nunca sobreescribir): **362 movidos** a su carpeta de plataforma real ya existente (319 NES, 14 Master System, 10 SNES, 5 Game Boy, 4 PC Engine, 2 Famicom Disk System, 2 Game Boy Advance, 2 Game Gear, 2 GameCube, 1 Game Boy Color, 1 Nintendo 64 — `NES`→`nes/` y `GameCube`→`gamecube/` fijado a mano por tener 2 carpetas candidatas en disco, `NGC/` resultó ser solo scraper-art sin ROMs). **323 duplicados exactos** (mismo nombre, SHA1 idéntico al ya existente en la carpeta correcta) movidos a `<carpeta_origen>/_descartados/` (nunca borrados). `rommgr scan` de refresco tras el movimiento: 101.084 archivos, 0 errores, 561 huérfanos limpiados. **Quedan 42 sin tocar**, documentados para sesión aparte: **33 archivos `.nes`** con nombre igual a uno ya existente en `nes/` pero SHA1 distinto (repacks/(Virtual Console)/dumps regionales alternativos — requieren desambiguación por catálogo, no por extensión a ciegas) y **9 ficheros `.u1`** que `PLATFORM_BY_EXTENSION` mapea a "Nintendo 64DD" por coincidencia — inspección real: son chips arcade sueltos (mismo patrón que `REPAIR-TOOL-5`), no N64DD, no crear carpeta `n64dd/` para ellos. **✅ `H:\ROMs` resuelto 2026-09-04** (lector SD conectado, decisión del usuario confirmada para el caso ambiguo de `3ds/`). Recuento fresco al conectar: **24 mal ubicados** (más que los 8 catalogados el `Día52` — la biblioteca creció, mismo patrón que `E:`). Mismo ajuste manual de carpeta ambigua que en `E:`: `NES`→`nes/` (no `famicom/`, colección japonesa aparte confirmada: 5.184 archivos con assets de scraper) y `GameCube`→`gamecube/` (`ngc/` no existe en esta tarjeta). Con confirmación del usuario, los 4 "(Virtual Console)" de `3ds/` se trataron igual que el resto (movidos por contenido real, no dejados aparte). **19 movidos** a su carpeta real (6 GBC, 3 GameCube `.rvz`, 2 NES bootleg "Crash Bandicoot", 1 FDS, 7 `.nes` sueltos en `atari2600/atarilynx/atarist/c64/gb`). **0 duplicados exactos.** **5 conflictos reales sin tocar** (mismo nombre, SHA1 distinto — 3 de los "(Virtual Console)" de `3ds/` más `c64/Contra` y `c64/Jackal`, mismo patrón que los 33 `.nes` sin resolver de `E:`, requieren desambiguación por catálogo). `rommgr scan` de refresco: 27.076 archivos, 0 errores, 19 huérfanos limpiados (coincide con los 19 movidos) | `E:\Carpetas anbernic` (hecho), `H:\ROMs` (hecho) | ✅ E: hecho, ✅ H: hecho (5 conflictos reales documentados aparte) |
| PSX-STRUCTURE-3b | **✅ Resuelto 2026-09-04**: los 42 casos sin tocar de `E:` (reproducción fiel del criterio original — `PLATFORM_BY_EXTENSION` vs `PLATFORM_BY_FOLDER` de la carpeta contenedora, no ambigua, sobre las 47 carpetas de plataforma reconocidas excluyendo `arcade/` — dio 42 exacto, 33 `.nes` + 9 `.u1`, confirma que el criterio no cambió). **Los 33 `.nes`**: los 33 tienen un fichero con **nombre idéntico** ya en `nes/`/`fds/` (mismo tamaño en casi todos los casos, SHA1 distinto — típico de cabecera iNES distinta entre un rip de Virtual Console y el dump No-Intro estándar). Verificado con el matcher de catálogo (6 muestras): mismo título de catálogo en ambos lados en las 6 — confirma mismo juego, no mismatch; en `Darkwing Duck` la copia de `nes/` es la verificada por SHA1 exacto (`high`) y la mal ubicada no (`low`). **33/33 movidos** a `_descartados/` de su carpeta de origen. **Los 9 `.u1`**: NO todos son chips arcade — verificado contra `load_arcade_crc_index()`: solo **4/9** calzan (`epr-666.u1`→`carnival`, `epm7032.u1`→`rabbit`/variantes, `01.u1`→`candy`, `lh53882d.u1`→`mouja`); los otros 5 (4 en `megadrive/`, 1 en `gamegear/`) no calzan contra el índice cargado — 3 de ellos tienen un fichero hermano `.u2` al lado (patrón hi/lo de placa arcade), posible bootleg no cubierto por el DAT actual, sin confirmar, **dejados sin tocar**. De los 4 confirmados, verificado con `load_arcade_manifest()` cuántos ROMs exige cada set completo: `epm7032.u1` es **duplicado real** (el chip ya está cubierto por 3 sets `rabbit*` completos ya en `arcade/`) → descartado a `ps3/_descartados/`. `epr-666.u1`/`01.u1`/`lh53882d.u1` son el **único fragmento conocido** de sets (`carnival` 38 ROMs, `candy` 22, `mouja` 14) que **no existen en absoluto** en `arcade/` — no son duplicados, tratados igual que los "incompletos" de `ARCADE-DAT-CONTAMINATION-10`: movidos a `arcade/_incompletos_pendiente_redescarga/<set>/`, no descartados como basura. `rommgr scan` de refresco: 100.643 archivos, 0 errores, 37 huérfanos limpiados (33+4). **`H:\ROMs` (5 conflictos análogos) sin tocar** — pendiente de sesión aparte | `E:\Carpetas anbernic` | ✅ 37/42 resueltos (33 `.nes` + 4 `.u1`), 5 `.u1` dudosos documentados sin tocar |
| PSX-STRUCTURE-4 | **Decisión confirmada 2026-09-02**: subcarpeta por juego para `psx/` (y el resto de `_DISC_SUBFOLDER_PLATFORMS` en `operation_planner.py:19-22` — saturn, dreamcast, wii), no carpeta plana. Ya es la convención implementada (`move_disc_set_to_subfolder`, `renamer/file_renamer.py:211`; target derivado en `operation_planner.py:159-168`). Bloqueos originales ya resueltos: PSX-STRUCTURE-1 (30/33, 3 restantes documentados para re-descarga, decisión del usuario de no mezclar), PSX-STRUCTURE-2 (✅ cerrado del todo, ver PSX-STRUCTURE-2b), DECOMPRESS-ARCADE-GAP-1 (✅ hecho), `CATALOG-MATCH-BUG-1`/`GBA-MISPLACED-2` (✅ 2026-09-03), `CATALOG-MATCH-REGION-1` (✅ 2026-09-04, PR #289 mergeada). **Re-medido 2026-09-04 tras el merge**: de los 456 casos PSX ambiguos originales, 167 (37%) ya resuelven región correcta; **quedan 289 (63%) sin resolver** (`CATALOG-MATCH-REGION-2`, diagnóstico hecho, sin arreglar). Migrar `psx/` ahora usaría el título ambiguo/incorrecto de esos 289 como nombre de carpeta destino — mismo riesgo original, alcance menor pero no cero. **Decisión pendiente del usuario**: ejecutar `apply` ya (aceptando que 289 sets quedarán con nombre de carpeta potencialmente erróneo, corregible después) vs. esperar a `CATALOG-MATCH-REGION-2` | `H:\ROMs\psx`, `E:\Carpetas anbernic\psx`, `catalog/matcher.py:270` | 🟡 desbloqueada parcialmente (37% resuelto), decisión de ejecución pendiente del usuario |

---

### PSX-ORPHAN — Carpetas huérfanas de scraping en `psx/` (hallazgo 2026-08-26)

Origen: el usuario, con la Anbernic conectada, pidió revisar por qué había
juegos PSX en subcarpetas y sospechó duplicados sueltos en la raíz que
pudieran borrarse. Auditoría real de contenido (no solo nombres) sobre
`E:\Carpetas anbernic\psx`:

- **125 subcarpetas de nivel superior, 0 contienen un ROM real**
  (`.bin/.cue/.chd/.pbp/.gdi/.iso`). Los ~450 ROMs reales de PSX están
  sueltos directamente en `psx/`. `move_disc_set_to_subfolder`
  (`renamer/file_renamer.py:211`) existe y funciona, pero no hay evidencia
  de que produjera estas carpetas.
- **De los 50 casos donde un archivo suelto en la raíz coincide de nombre
  con una subcarpeta, en NINGUNO la subcarpeta tiene el ROM** — el archivo
  suelto es la única copia real. **No borrar nada de la raíz basándose en
  el nombre de una carpeta homónima.**
- Desglose de las 125 carpetas: **98 totalmente vacías**; **17 con
  `_descartados/` conteniendo una versión alternativa de región/revisión ya
  descartada** (4.333,8 MB — p.ej. `Koudelka (Spain) (Disc 2)/_descartados/
  Koudelka (USA) (Disc 1).chd`), respeta el convenio del proyecto (AUD-3,
  `_descartados/` nunca se borra solo); el resto (~2.022 archivos, 445,7 MB)
  es `media/` (carátulas) y `.m3u` huérfanos.
- Hipótesis del origen (no confirmada): un pase de dedup por juego (ver
  `ra_duplicates_service.py`) creó una carpeta por juego, descartó la
  versión perdedora en `_descartados/` y dejó `media/`+`.m3u`, pero la
  versión ganadora se devolvió después a la raíz sin limpiar la carpeta.
- Verificado con `verify_multidisc()` (`utils/multidisc_verifier.py`, ya
  existente): 66 grupos sin `.m3u` (22 juegos únicos, probablemente por el
  mismo aplanado) + 4 "gap" + 1 "mixed_ext".
  - `Metal Gear Solid (USA)`: **falso positivo** — el disco 2 sí existe
    (`Metal Gear Solid (USA) (Disc 2) (Rev 1).bin`), pero `_DISC_RE`
    (`utils/m3u_generator.py:10`) exige que `(Disc N)` sea el sufijo final
    del nombre, así que no lo reconoce con `(Rev 1)` detrás. El
    `mixed_ext` (`.bin`+`.srm`) es el mismo problema: el save
    `... (Disc 1).srm` cae en el mismo bucket porque `find_disc_groups`
    no filtra por extensión de imagen antes de agrupar.
  - `Fear Effect (USA)`: **gap real** — discos 1/3/4 existen como `.bin`
    suelto (con su `.cue` correspondiente en `_descartados/`, íntegro y
    apuntando al `.bin` correcto — parece mal ubicado, no corrupto), disco
    2 no aparece en ningún sitio de la biblioteca (búsqueda recursiva
    completa).

| ID | Task | Notas |
|----|------|-------|
| PSX-ORPHAN-1 | Borrar las 98 subcarpetas totalmente vacías de `psx/` (0 archivos) | — | ✅ borrado 2026-08-26, ver `.rommgr/psx_orphan_cleanup_2026-08-26.log` |
| PSX-ORPHAN-2 | Limpiar `media/`+`.m3u` huérfanos del resto de subcarpetas (445,7 MB) | `psx/*/media`, `psx/*/*.m3u` | ✅ borrado 2026-08-26 junto con PSX-ORPHAN-1 (mismo script, mismo log) |
| PSX-ORPHAN-2b | **Excepción a AUD-3, decisión explícita del usuario 2026-08-26**: los 4,3 GB en `_descartados/` de las 17 subcarpetas (versiones de región/revisión ya descartadas por el dedup) también se borraron, pese a la advertencia de que es irreversible y de que no libera espacio en la Anbernic (psx nunca llegó a sincronizarse — ver `CABLE-ROM-FIX-3`). El `_descartados/` de nivel superior (`psx/_descartados/`, 180 items) **no se tocó**, sigue con la política normal | `.rommgr/psx_orphan_cleanup_2026-08-26.log` (manifiesto completo: rutas + tamaños de cada archivo borrado) | ✅ borrado, sin backup adicional más allá del manifiesto |
| DEVICE-DUP-1 | **Hallazgo 2026-08-27 en la propia Anbernic** (no en el PC): la raíz de la SD (`/storage/521D-04EA/`) tenía carpetas de plataforma en dos esquemas a la vez — nombres humanos sueltos (`NGC`, `Game Boy Advance`, `Nintendo DS`, etc.) y `ROMs/<código>` (`gamecube`, `gba`, `nds`...) que es lo que usa nuestro Cable Sync. `NGC/` y `ROMs/gamecube/` eran **duplicado exacto** (25 GB, 21/22 juegos idénticos) — sin relación con nada tocado en el PC. Verificado que no hay ninguna partida de GameCube en la consola (ni en `NGC/`/`ROMs/gamecube/`, ni en `saves/`, ni en los datos privados de `org.dolphinemu.dolphinemu`/`org.dolphinemu.mmjr` en SD e interno — `GC/`/`StateSaves/` vacíos, no se ha jugado nada aún). Usuario confirmó `ROMs/` como la carpeta real; `NGC/` borrado por `adb shell rm -rf` — **25 GB liberados, la SD pasó de 53 GB a 78 GB libres** | `/storage/521D-04EA/NGC` (borrado) | ✅ hecho 2026-08-27 |
| DEVICE-DUP-2 | **Auditado 2026-08-27, NO eran duplicados — tenían contenido único.** Comparado nombre a nombre contra `ROMs/<código>`: `Atari 2600` y `Game Boy` sí eran subconjunto completo (0 archivos únicos, redundantes de verdad, **sin tocar todavía**). El resto tenía 42 juegos que no existían en `ROMs/` (Nintendo DS: Mario Kart DS, New Super Mario Bros., Pokémon SoulSilver, Pokémon Mystery Dungeon, Super Mario 64 DS, Tetris DS; Master System: 24 juegos incl. Golden Axe/Shinobi/Sonic; Game Gear: 8 con traducciones fan; Game Boy Color: 2; Game Boy Advance: Mother 3 fan-trans; Famicom Disk System: 1) — **traídos al PC por `adb pull` a `inbox/` y procesados por el pipeline real (`/api/inbox-run`)**: 42 escaneados, 39 renombrados a nombre canónico, 0 errores, verificado en disco en `ROMs/nds` y `ROMs/mastersystem`. Las 6 carpetas sueltas de origen en la SD **siguen sin borrar** (quedan como backup hasta confirmar que todo llegó bien) | `E:\Carpetas anbernic\inbox` → `ROMs/nds`, `ROMs/mastersystem`, etc. | ✅ organizado 2026-08-27; pendiente solo borrar las 6 carpetas de origen en la SD una vez confirmado, y decidir si limpiar `Atari 2600`/`Game Boy` (100% redundantes) |
| IISU-MEDIA-1 | Investigado cómo evitar carátulas duplicadas entre launchers (Daijisho/iiSU/ES-DE). Daijisho guarda su caché en `/data/data/com.magneticchen.daijishou/` (privado, sin root no se puede leer ni exportar — confirmado con `run-as` fallando por app no depurable). iiSU sí soporta "link ES-DE metadata" en ROM Import (no duplica media), pero requiere instalar ES-DE (app de pago vía Patreon, sin root, no destructivo) y volver a scrapear una vez en ese formato estándar. Se evaluó rootear la consola (GammaOS Next) para acceder a las DBs privadas — **descartado**: implica desbloquear bootloader, que resetea de fábrica el almacenamiento interno (destruiría justo los datos de Daijisho/iiSU que se querían leer) | — | 🔵 en pausa, decisión del usuario: no rootear; ES-DE pendiente de que el usuario decida instalarlo |
| IISU-CONFIG-1 | El usuario ya abrió iiSU y apuntó la carpeta de ROMs a `ROMs/` en la SD — confirmado que escanea recursivamente (incluye nuestro propio `_descartados/`) y empieza a scrapear su propia media en `Android/media/com.iisulauncher/iiSULauncher/assets/media/roms/consoles/<shortName>/<rom>/` (formato público, sin root, editable por adb). Solo tenía 2 plataformas configuradas en `Emuladores/emulator_options.json` (`gb`→RetroArch, `nds`→melonDS). Se añadieron las 17 restantes de nuestra lista (`_SYSTEMS` de `esde/systems_generator.py`), cruzando el catálogo maestro `emuladores.json` con los emuladores standalone realmente instalados (`pm list packages`): `psx`→DuckStation, `gc`/`wii`→Dolphin, `ps2`→AetherSX2, `psp`→PPSSPP, `n64`→M64Plus FZ, `n3ds`→Citra MMJ (paquete instalado es `org.citra.emu`, que en el catálogo de iiSU corresponde al id `CITRA-MMJ`, no al `CITRA` genérico), `dreamcast`→Flycast; `gba/gbc/snes/megadrive/mastersystem/gamegear/mame/fbneo/neogeo` sin standalone instalado → RetroArch (core por defecto, `mame`→MAME 2003-Plus siguiendo la preferencia ya documentada en `docs/arcade-setup.md`). **Añadido 2026-08-27**: faltaba el shortName `arcade` (distinto de `mame`/`fbneo`/`neogeo` — es el que corresponde a nuestra carpeta real `ROMs/arcade`, mientras se sincronizaba por primera vez a la consola) → RetroArch/"FinalBurn Neo core", misma preferencia FBNeo-primero de `docs/arcade-setup.md`, backup en `emulator_options.json.bak-2026-08-27b`. **Completado 2026-08-27**: las 18 plataformas restantes de `ROMs/` también añadidas (`amiga`→PUAE, `atari2600`→Stella, `atari5200`→a5200, `atari7800`→ProSystem, `atari800`→Atari800, `atarijaguar`→Virtual Jaguar, `atarilynx`→Handy, `atarist`→Hatari, `c64`→VICE x64sc Accurate, `colecovision`→blueMSX, `cps1/2/3`→FinalBurn Neo, `easyrpg`→EasyRPG, `famicom`/`fds`/`nes`→FCEUmm siguiendo la preferencia ya establecida en `_SYSTEMS` de `esde/systems_generator.py`, `intellivision`→FreeIntv), todas vía RetroArch (ningún standalone instalado para estas). **`astrocde` (Bally Astrocade) se dejó sin configurar a propósito**: el catálogo de iiSU no ofrece ningún core de RetroArch para esa plataforma, solo MAME4droid standalone, que no está instalado — no hay emulador viable en este dispositivo todavía. Backup en `emulator_options.json.bak-2026-08-27c`. **Completado 2026-08-27**: usuario instaló MAME4droid Current (`com.seleuco.mame4d2024`) vía Play Store (ojo: primero instaló por error el clásico `com.seleuco.mame4droid`, no válido para `astrocde` en el catálogo — instaló también el Current a continuación) → `astrocde`→MAME4droid Current añadido, backup en `emulator_options.json.bak-2026-08-27d`. **Total: 39 de 39 carpetas de `ROMs/` configuradas**. **Confirmado 2026-08-27, no es un problema**: iiSU usa `shortName` `gc`/`n3ds` internamente pero traduce el nombre de carpeta real sin exigir coincidencia exacta — verificado en vivo: `ROMs/3ds` (nuestra convención, sin tocar) ya aparece scrapeado bajo su ID interno `n3ds`. No hace falta renombrar `gamecube`→`gc` ni `3ds`→`n3ds` en el PC/SD/ajustes de Retro Vault | `.../Emuladores/emulator_options.json` (backup en `emulator_options.json.bak-2026-08-27` en el propio dispositivo) | ✅ hecho 2026-08-27, con backup en el dispositivo |
| PSX-ORPHAN-3 | Arreglar `_DISC_RE` (`utils/m3u_generator.py:10`) para reconocer `(Disc N)` aunque le siga otro tag (`(Rev 1)`, `(v1.1)`), y excluir extensiones no-imagen (`.srm` y otras saves) del agrupado en `find_disc_groups` — evita falsos positivos como `Metal Gear Solid (USA)` | `utils/m3u_generator.py::find_disc_groups`, `_DISC_RE` | ✅ hecho 2026-08-27 — regex con 3er grupo captura el tag final (`_parse_disc()`), rechaza `(Track N)` explícitamente (evita resucitar el falso positivo de tracks multi-bin que el ancla `$` original prevenía), y `_DISC_SET_EXTS` (imágenes + sidecars: `.bin/.img/.iso/.chd/.gdi/.pbp/.ecm/.cue/.ccd/.sub/.mds/.mdf/.sbi`) filtra cualquier extensión no-disco antes de agrupar. 5 tests nuevos en `test_m3u_generator.py` (incluye el caso real MGS + `.srm`), suite completa 1033/1033 verde. `multidisc_verifier.py` (que reimporta `_DISC_RE`) sigue funcionando sin cambios — sus 33 tests también en verde |
| PSX-ORPHAN-4 | `Fear Effect (USA)` disco 2 — confirmar si nunca se tuvo o se perdió; mientras tanto, sacar los 3 `.cue` de `_descartados/` de vuelta a `psx/` (referencian bins que sí existen, no hay conflicto de nombre). **Re-verificado 2026-09-09**: la mitad de "sacar los .cue" ya no aplica — discos 1/3/4 están hoy en `psx/` como `.chd` (no `.bin`/`.cue`) y `psx/_descartados/` no tiene ningún `.cue` (0 en toda la carpeta); entre el hallazgo original (2026-08-26) y hoy, una conversión a CHD ya reubicó y limpió esos archivos sin que este ítem se cerrara. **Confirmado con el usuario 2026-09-09: nunca se tuvo el disco 2** — gap de origen, no una pérdida | `psx/_descartados/Fear Effect (USA) (Disc {1,3,4}).cue` | ✅ cerrado 2026-09-09 — nada que mover, disco 2 nunca existió en la colección |
| PSX-ORPHAN-5 | **Decisión pendiente (feedback usuario 2026-08-29)**: consenso sobre sets PSX con muchos archivos/tracks — evitarlos o no — y si cada juego debería vivir en su propia subcarpeta o con los archivos sueltos en `psx/`. Relacionado con `move_disc_set_to_subfolder` (`renamer/file_renamer.py:211`, patrón ya documentado en `.claude/CLAUDE.md`) y con el propio hallazgo de PSX-ORPHAN (125 subcarpetas huérfanas de un aplanado previo) | `docs/ideas/Idea_final.md` | 🔴 pendiente, decisión del usuario |

---

### ANDROID-DUP-1 — Duplicados reales en la propia Anbernic (DaijiShō/iSuu), nunca comprobados: dedup solo se ha ejecutado contra bibliotecas PC (hallazgo 2026-09-19, RG556 `RG556006101273`, ADB en vivo)
> **Estado (revisado 2026-10-20):** ⏳ abierta — quedan acciones sin implementar (limpieza PSX en el dispositivo)

Origen: el usuario reporta duplicados visibles en DaijiShō e iSuu en la RG556
— PS2 con **todos** los juegos duplicados, y varios títulos sueltos en GBA/PSX
(ejemplos dados: Crash Bash, Crash 2). Sospecha propia del usuario, confirmada
por la investigación: **la función de duplicados nunca se ha ejecutado contra
la biblioteca Android real** — todo el trabajo de `DUP-REGION-1/2`,
`DUP-DISC-RA-1*`, `GBA-DUAL-FOLDER-1`, `DUALFOLDER-12` se hizo contra
bibliotecas **PC** (`F:\Juegos Retro` en "Ruben", `E:\Carpetas anbernic` en
"rammu"). El proyecto sí soporta un repo Android separado
(`library_android.db`, seleccionado por `_repo_for_path()` en
`web/builders/common.py:141-167` para cualquier ruta fuera de
`config.library_root`, documentado en `config.py:423-432`) y
`_review_groups_for_repo()` (`web/builders/duplicates.py:743`, invocado una
vez por repo en `web/builders/duplicates.py:519-537,714`) ya sabe iterar sobre
`repository_android` — pero **`library_android.db` lleva sin re-escanearse
desde 2026-09-12** (`.rommgr/library_android.db`, mtime confirmado), una
semana antes de esta sesión y antes de varios syncs recientes (GBA
2026-09-14, PSX CHD hasta 2026-09-13, PS2 hasta 2026-09-15) — cualquier pasada
de dedup contra ese snapshot habría estado desactualizada igualmente.

**Verificado en vivo por ADB contra `/storage/521D-04EA/ROMs/` de la RG556**
(no contra `library_android.db`, directamente contra el dispositivo):

| Plataforma | Hallazgo | Evidencia |
|---|---|---|
| **PSX** | El mismo disco coexiste en 2-3 formatos/nomenclaturas a la vez: `.bin`+`.cue` **y** `.chd` del mismo release (la limpieza post-conversión de `DUP-DISC-RA-2` nunca se ejecutó/completó en este dispositivo — esa tarea ya documentaba "ejecución real pendiente, la lanza el usuario"), más un tercer set de volcados **legacy con nombre de serial** (`[SCUS-94900]`, `[SCUS-94570] [bin]`, `[SCUS-94426] [bin]`, 39 entradas `[SCUS/SLUS/SCES/SLES-nnnnn]` en total) que preceden a este proyecto — mtimes de 2003/2006 en varios `.bin`/`.img`. Caso confirmado exacto del usuario: `Crash Bandicoot (USA)` existe como `.bin+.cue`, `.chd`, y carpeta legacy `Crash Bandicoot [U] [SCUS-94900]/` con `.ccd`/`.img`/`.sub` (CloneCD) — el mismo disco 3 veces. `Crash Bash` tiene además `.chd` (Europe) + `.chd` (USA) + carpeta legacy `[SCUS-94570] [bin]`. `Crash Team Racing` tiene `.chd` + carpeta legacy `[SCUS-94426] [bin]` + un tercer `CTR - Crash Team Racing (Europe).zip` sin descomprimir | 1231 entradas en `psx/`: 305 `.chd`, 490 `.bin`, 131 `.cue`, 46 CloneCD (`.img`/`.ccd`/`.sub`), 39 legacy serial, 89 subcarpetas (mayoría sets multi-disco legítimos, al menos 3 confirmadas como duplicados legacy) |
| **GBA** | Volcados legacy pre-No-Intro (formato `[E]`/`[U]`/[J]`, típico de sets GoodGBA anteriores a este proyecto — mtimes 2015, mucho antes de que existiera `rom_manager`) conviven con las copias renombradas canónicas No-Intro del mismo juego, más `.sav`/`.sgm` huérfanos ligados a esos volcados legacy. Además ZIPs sin descomprimir junto a su `.gba` ya extraído — violación del principio del Pilar 2 (aunque estos son archivos ya existentes en el dispositivo antes del proyecto, nunca pasaron por el Inbox) | 1490 entradas en `gba/`: 1297 `.gba`, 120 `.zip`, 91 con patrón `[E]`/`[U]`/`[J]` legacy, 45 `.sav`/`.sgm` |
| **Carpetas Title Case + slug paralelas** | Mismo patrón que `GBA-DUAL-FOLDER-1`/`PS2-DUAL-FOLDER-1`/`DUALFOLDER-12`, pero **nunca aplicado a este dispositivo** — esas tareas solo tocaron la máquina "Ruben". En la RG556 conviven `Atari 2600/`+`atari2600/`, `Famicom Disk System/`+`fds/`, `Game Gear/`+`gamegear/`, `Master System/`+`mastersystem/` | `ls /storage/521D-04EA/ROMs/` — 4 pares confirmados |
| **PS2 ("todos los juegos duplicados" en iSuu)** | **Sin duplicación de archivos** — `ps2/` es una sola carpeta plana, 26 `.iso`/`.chd`, sin nombres repetidos ni carpeta `PlayStation 2/` paralela. La causa no puede estar en los archivos de este proyecto; el síntoma ("todos" los juegos, no solo algunos) apunta a **configuración del propio launcher** (p. ej. dos perfiles de sistema/emulador en iSuu/DaijiShō apuntando ambos a `ROMs/ps2/`) — fuera del alcance de este repo, requiere revisar la config de iSuu en el dispositivo, no el código de `rom_manager` | `ls -la /storage/521D-04EA/ROMs/ps2/` — 26 archivos, sin duplicados |
| **Corrección 2026-09-19 (sesión de reparación)**: la afirmación original de este hallazgo ("`fds/` contiene un set casi completo de NES") era falsa — basada en un `ls` mal citado que mezcló la salida de dos comandos distintos. Re-verificado con comillas correctas: `fds/` tiene solo 27 entradas reales (mezcla de un par de ficheros tipo chip arcade sin identificar, `Balloon Fight`/`Ice Climber`/`Metroid`/`Super Mario Bros` en `.zip` y `.nes`, y 2 `.fds` genuinos), no un set NES completo. La carpeta `nes/` real sí tiene el problema — **~4022 entradas**, incluye volcados legacy `[!]`/`(J)`/`(U)` conviviendo con nombres canónicos No-Intro, parches de traducción `[T+...]` (legítimos, no son duplicados), pares `.nes`+`.zip` del mismo dump (viola Pilar 2), y ficheros sueltos tipo chip arcade (`1-5j.bin`, `10-9h.bin`) que no son NES en absoluto. Confirmado con el ejemplo del usuario: **42 entradas "Super Mario"** — algunas hacks legítimos (`[Hack] [Super Diego Bros]`, `Super Mario Bros. Extended`), pero varias duplicados reales del mismo juego bajo nomenclatura distinta (`Super Mario Bros. (W) [!].nes` vs `Super Mario Bros. (World).nes`). Un archivo está directamente mal clasificado: `Super Mario World (Asia) (En) (Pirate).nes` es un juego de **SNES**, no NES — mal colocado, ni siquiera es cuestión de duplicados | `ls /storage/521D-04EA/ROMs/nes/`, `ls /storage/521D-04EA/ROMs/fds/` |

**Por qué `DUP-REGION-1/2` y `DUP-DISC-RA-1*` no habrían bastado ni ejecutándose hoy mismo**:
`DUP-REGION-1` (`web/builders/duplicates.py`) agrupa por título difuso solo
para plataformas de un archivo, excluyendo PSX explícitamente
(`_MULTI_DISC_RISK_PLATFORMS`) — nunca iba a agrupar los casos PSX de arriba.
`DUP-DISC-RA-1b` (hash de disco RA para PSX) sí tiene el motor correcto para
esto, pero su "parte 2" (agrupar por edición completa en la cola de
duplicados) sigue **sin implementar**, tal cual quedó documentado en su
propia fila arriba. Y los volcados legacy con nombre de serial (`[SCUS-xxxx]`)
casi seguro ni siquiera matchean contra el catálogo por SHA1 (dumps de otra
fuente) — dependerían del hash de disco RA (`DUP-DISC-RA-1a`, ya implementado
y verificado) para reconocerse como el mismo juego, otra razón más para
completar `DUP-DISC-RA-1b` parte 2 antes de fiarse del todo de la cola de
duplicados en PSX.

**Recomendación (sin implementar, a decidir con el usuario)**:
1. Escanear `library_android.db` contra la RG556 real (vía ADB, ya que está
   conectada) para tener un snapshot actual antes de cualquier limpieza.
2. Completar `DUP-DISC-RA-1b` parte 2 (agrupado por edición vía hash RA en la
   cola de duplicados) — sin esto, los duplicados de formato/legacy en PSX
   seguirán invisibles para la herramienta aunque se re-escanee.
3. Extender `DUP-REGION-2`/la cola de revisión para reconocer volcados legacy
   pre-No-Intro (`[E]`/`[U]`/`[J]`, `[SCUS-nnnnn]`) como el mismo juego que su
   contraparte canónica — hoy dependen de que el matcher los reconozca, y no
   está confirmado que lo haga (`catalog/matcher.py::_match_by_title()`).
4. Verificar contenido real de `fds/` vs `Famicom Disk System/` antes de
   aplicar el criterio de `DUALFOLDER-12` a este par — no es un simple
   duplicado de nombre, puede haber NES mal ubicado.
5. `PS2` (iSuu) no es un bug de este repo — confirmar en el propio dispositivo
   si iSuu/DaijiShō tiene un sistema PS2 duplicado en su configuración.

**Primer fix en marcha** → rama `fix/duplicates-disc-format-set-integrity`
(PR #329): las comprobaciones de sibling/integridad (`_is_cue_sibling_bin`,
`_is_ccd_sibling_data`, `_is_broken_disc_entry`) usaban `Path.exists()` en el
propio `source_path` — siempre `False` para una fila escaneada por ADB, lo
que desactivaba en silencio toda la protección de siblings para el repo
Android. Explica directamente por qué el trío `.ccd`/`.img`/`.sub` de
`Crash Bandicoot [U] [SCUS-94900]` se agrupaba como si fueran 3 copias
independientes (recomendando conservar el `.ccd` de 790 bytes y descartar el
`.img`+`.sub`, los datos reales del disco), y por qué el trío
`.bin`/`.cue`/`.chd` de `Crash Bandicoot (USA)` caía al desempate
alfabético, prefiriendo el `.bin` sobre el `.chd` (contradice la decisión ya
tomada en `DUP-DISC-RA-2`). Corregido pasando un `known_paths` (los
`source_path` ya escaneados en ese repo) para verificar siblings contra la
BD en vez del filesystem local, más un tier explícito de formato de disco
(`.chd` > `.cue`/`.gdi` > `.ccd`). 4 tests nuevos, 1382 tests en verde. Sin
✅ mergeado 2026-09-19 (PR #329, squash, rama borrada) | `web/builders/common.py:141-167`
(`_repo_for_path`), `config.py:423-432` (`database_path_android`),
`web/builders/duplicates.py:519-537,714,743` (`_review_groups_for_repo`),
`retroachievements/ra_disc_hash_cache.py` (`DUP-DISC-RA-1b` parte 2
pendiente), `catalog/matcher.py::_match_by_title()` (sin confirmar
reconocimiento de volcados legacy) | 🔴 confirmado con evidencia real (ADB en
vivo), sin implementar — decisión de alcance y orden pendiente del usuario |

**Re-verificado 2026-09-30 contra `library_android.db` real (RG556 conectada), solo lectura:**

- **Causa raíz real de las filas fantasma** (los 2 discos españoles de Metal
  Gear Solid señalados en `ANDROID-DUP-PSX-1`, y probablemente más): la tabla
  `scan_runs` tiene un escaneo de `psx` (`id=19`) que **arrancó
  2026-09-28T16:09:52 y nunca terminó** (`finished_at: NULL`, `files_seen: 0`)
  — el último escaneo completo de `psx/` fue el `id=17` del 2026-09-20. Cualquier
  borrado hecho en el dispositivo entre esas dos fechas nunca se reconcilió
  contra la BD porque el escaneo que lo habría reflejado murió sin terminar.
  Causa del crash del `id=19` encontrada en `.rommgr/logs/rommgr.log`: **no
  fue un crash real** — un job de Inbox gigante (`zip-route-apply`, miles de
  operaciones) estaba corriendo justo a esa hora, y el proceso del servidor
  se reinició a las 17:16:50 (los daemons vuelven a arrancar en el log) con
  el scan de `psx/` todavía a medias — se quedó huérfano sin más.
  **Rescan de `psx/` relanzado 2026-09-30 con la Anbernic conectada**: 1579
  archivos, 1435 ROMs, 0 errores, hashes recalculados — pero **`pruned: 0`**
  pese a que el archivo de MGS España verificado seguía sin existir en el
  dispositivo (confirmado con `adb shell test -e` justo después del rescan).
  **Bug real encontrado y arreglado** (`fix/android-scan-prune-separator-bug`):
  `prune_stale_entries()` (`database/repositories/games.py:384`) construía
  `root_prefix = source_root + os.sep` — en Windows `os.sep` es `\`, pero las
  rutas de Android siempre usan `/`, así que `root_prefix` nunca coincidía
  con ninguna ruta real del dispositivo. **Esto significa que la poda nunca
  ha funcionado para ningún rescan de Android hecho desde esta máquina
  Windows**, sin ningún error visible — explica por completo por qué las
  filas fantasma se acumulan indefinidamente. Arreglado usando
  `is_device_path()` para elegir el separador correcto según el tipo de ruta,
  no según el SO anfitrión. 1 test nuevo
  (`test_prune_stale_removes_missing_android_path_on_windows`, reproduce el
  bug exacto), suite completa 1516/1516, ruff+format limpios. **Fix mergeado
  y verificado en real (PR #385)**: instancia real reiniciada con el código
  nuevo, rescan de `psx/` relanzado (sin recalcular hashes, solo listar) →
  **`pruned: 211`** (antes siempre 0). Las 8 filas fantasma de MGS España se
  quedaron en 4 — verificado que los 4 restantes (`.bin`+`.m3u` de cada
  disco) **sí existen de verdad en el dispositivo** (`adb shell test -e`); lo
  podado fueron exactamente los 4 `.chd`/`.cue` mal etiquetados como "(World)
  (4B4E083C) (Addon)" que ya se habían confirmado ausentes. Poda exacta,
  `ANDROID-DUP-PSX-1` queda resuelto del todo — no solo documentado.
- **Segundo bug real encontrado por error propio, sin arreglar todavía**: al
  verificar la poda con un segundo rescan `compute_hashes=False` (más rápido,
  solo para confirmar el fix anterior), las 1435 filas de `psx/` se quedaron
  sin `sha1`/`md5` — el upsert del scan (`web/handlers/scan.py:551-552`,
  `sha1=sha1_map.get(ap, "")`) sobrescribe siempre con cadena vacía cuando
  `compute_hashes=False`, en vez de conservar el hash ya guardado en la fila
  existente. Un rescan "rápido" (solo listar) después de uno completo borra
  todo el trabajo de hash del anterior sin avisar. Recuperado relanzando el
  rescan completo otra vez (`compute_hashes=True`) — sin arreglar el código
  todavía, candidato a tarea propia: el upsert debería hacer `COALESCE` con
  el `sha1`/`md5` ya existente en la fila cuando no se recalculan, no pisarlo
  con `""`.
  **`GAMEDB-HASH-COALESCE-1` -- arreglado 2026-10-02**: `upsert_game()`
  (`database/repositories/games.py:105-119`) ahora hace
  `sha1 = CASE WHEN excluded.sha1 != '' THEN excluded.sha1 ELSE games.sha1 END`
  (mismo patron para `md5` y `crc32`) en vez de pisar siempre con
  `excluded.*` -- un rescan rapido (`compute_hashes=False`) ya no borra el
  hash de un rescan completo anterior. Test nuevo
  (`test_upsert_game_quick_rescan_keeps_prior_hash` en `tests/test_repository.py`)
  reproduce el caso exacto (hash completo -> rescan rapido -> hash debe
  sobrevivir, otros campos si se actualizan). Sin commitear/pushear todavia.
- **Volcados legacy con nombre de serial — verificados por hash 2026-09-30**:
  tras la poda quedaron 40 filas `[SCUS-/SLUS-/SLES-/SCES-nnnnn]` en `psx/`
  (`LIKE '%[SCUS-%' OR ...`), de las cuales **solo 15 en formato hasheable**
  (`.chd`/`.bin`/`.cue` — `compute_psx_ra_hash` no soporta CloneCD
  `.img`/`.ccd`/`.sub` ni `.ecm`, los 25 restantes quedan sin poder
  verificarse con la herramienta actual). De esas 15, buscado un
  contrapartida canónica real en el resto de `psx/` para cada título:
  - **`Digimon Rumble Arena [SLUS-01404].chd`** vs `(USA).chd` — **verificado
    idéntico byte a byte, aplicado** (mismo hash MD5 RA real). 1 archivo
    descartado, verificado en el dispositivo real.
  - **`Driver 2 [Disc2of2] [SLUS-01318].chd`** vs `(USA) (Disc 2) (Rev 1).chd`
    — **MISMATCH real** pese al nombre y tamaño parecidos (342.200.657 vs
    342.287.667 bytes) — contenido genuinamente distinto, **no tocado**.
    Confirma que verificar antes de aplicar sigue mereciendo la pena incluso
    en candidatos que parecen obvios.
  - `Ehrgeiz - God Bless the Ring [SLUS-00809]` y `Crash Team Racing
    [SCUS-94426]`: cada uno tiene **2 copias, ambas con nombre legacy**, sin
    ninguna copia de nombre canónico en la biblioteca contra la que comparar
    — no hay "recomendado" obvio, sin tocar hasta decidir cuál de las dos
    conservar (o verificar si son idénticas entre sí).
  - `Crash Bash [SCUS-94570]` (USA, `.chd` de 4,4 MB sospechosamente pequeño +
    `.bin` de 178 MB) solo tiene una copia canónica de **otra región**
    (Europe, 61 MB) en la biblioteca — no comparable, regiones distintas se
    esperan distintas, sin tocar.
  - `Tekken 3 [SLUS-00402]` (set multi-pista con un `.cue` roto) sin una
    contrapartida canónica de un solo archivo clara — sin tocar.
  - Los 25 archivos `.ccd`/`.img`/`.sub`/`.ecm` restantes (CloneCD y formatos
    comprimidos con corrección de errores eliminada) quedan documentados sin
    verificar — soporte de esos formatos en `compute_psx_ra_hash` fuera de
    alcance de esta sesión.

**Estado al cerrar la sesión (2026-09-30, tarde)**: rescan completo de
`psx/` con `compute_hashes=True` **en curso** (relanzado para restaurar los
hashes borrados por el bug de arriba) — dejarlo terminar solo antes de tocar
nada más en `psx/`; comprobar con `GET /api/job-status` (`scan_running`).
**`Game Gear/` (rehash de los 28 archivos sin sha1) sin empezar** — pendiente
para la próxima sesión, una vez termine el rescan en curso (mismo job
"scan", no se puede lanzar en paralelo). Backups de `library_android.db`
hechos antes de cada tanda de borrado real de hoy, en
`.rommgr/library_android.db.bak-*`.
- **Carpetas Title Case + slug paralelas**: de los "4 pares confirmados" originales,
  hoy solo queda uno sin resolver — **`Game Gear/` (28 archivos) + `gamegear/`
  (736 archivos)**, 0% de solapamiento por SHA1 comprobado porque **las 28 filas
  de `Game Gear/` tienen `sha1=''`** (nunca se hashearon) — invisibles para
  cualquier deduplicación por hash, y sus nombres ya parecen No-Intro
  (`Ax Battler - A Legend of Golden Axe (USA, Europe, Brazil) (En).gg`), no
  claramente legacy — hace falta rehashear antes de decidir si son duplicados
  reales o contenido legítimo sin catalogar. `Atari 2600/`, `Master System/` y
  `Famicom Disk System/` ya no tienen su par Title Case (resuelto de rebote,
  mismo hallazgo que `SD-ORPHAN-FOLDERS-1` documentó para la raíz de la SD).
- **`famicom/` investigado a fondo 2026-09-30 — NO son duplicados triviales,
  sin consolidar a propósito**: 109 archivos, 0,02 GB, en paralelo a `nes/`
  (2972 archivos, 2,34 GB, ambas carpetas con `sha1` real ya calculado, a
  diferencia de `Game Gear/`). **0 coincidencias por SHA1** entre `famicom/` y
  `nes/`; **100/109 comparten nombre de archivo exacto** con algo en `nes/`,
  pero **contenido distinto** — verificado bajando un par real por ADB
  (`Little Nemo - The Dream Master (Europe).nes`, 262.160 bytes en ambas
  carpetas): cabecera iNES idéntica (mismo mapper/PRG/CHR), pero difieren a
  partir del byte 24.000 — no es una cuestión de cabecera, el contenido del
  ROM en sí es distinto pese al nombre y tamaño idénticos (revisión/hack
  distinto bajo el mismo nombre No-Intro, o un dump corrupto en alguna de las
  dos copias, sin determinar cuál). Otro caso (`Kung Fu (Europe).nes`) ni
  siquiera coincide en tamaño (40.976 vs 65.552 bytes) con el mismo nombre.
  **Conclusión: no consolidar `famicom/` en `nes/` sin revisar caso a caso**
  — mismo tipo de aviso que ya dio el hallazgo original de `ANDROID-DUP-3`
  para `fds/` ("no era lo que parecía"), confirmado ahora con datos reales
  para este par también. Los 9 archivos de `famicom/` sin ninguna
  coincidencia de nombre en `nes/` (varios dentro de subcarpetas de colección
  `# DYNAVISION #`/`# PT-BR #`/`top100`) tampoco tocados.
- **`ANDROID-DUP-CROSSFMT-VERIFY-1` repetido con la función ya integrada y
  completado 2026-09-30** (`verify_group_by_disc_hash`, PR #379): 89 grupos
  PSX `crossfmt`-only reales hoy (antes 83, la cola cambia con la biblioteca)
  — **2 verificados como seguros (mismo grupo, `Guilty Gear (Europe)`), 0
  mismatch, 102 rutas no verificables** (mismo patrón que el 2026-09-25: la
  inmensa mayoría de `.cue`/`.img` de esta biblioteca referencian un `.bin`
  que ya no existe tal cual en el dispositivo). Los 2 verificados **aplicados
  con confirmación explícita del usuario**: descartados `psx/Guilty Gear
  (Europe).chd` + `psx/Guilty Gear (Europe).bin` sueltos en la raíz,
  conservado `psx/Guilty Gear (Europe)/Guilty Gear (Europe).chd`, **0,48 GB
  liberados**, verificado en el dispositivo real. Con esto,
  `ANDROID-DUP-CROSSFMT-VERIFY-1` queda completamente cerrado — no queda
  ningún grupo PSX `crossfmt`-only sin comprobación de contenido real.
- **`ANDROID-DUP-1` GBC — aplicado 2026-09-30**: confirmado sin cambios desde
  Día71 (1268 grupos, 1,95 GB, todos `reasons == ["sha1"]` puro), mismo patrón
  ya probado en NES/Game Gear. Backup de `library_android.db` antes de tocar
  nada. **1268/1268 grupos, 1276 archivos descartados, 0 errores, ~1,95 GB
  liberados** — verificado en el dispositivo real (recomendado presente,
  descartes confirmados ausentes por `adb shell test -e`).
- **Resto de plataformas `sha1`-puro nunca aplicadas — aplicadas 2026-09-30**:
  mismo criterio estricto que GBC (solo `reasons == ["sha1"]`, nunca un grupo
  con `crossfmt` mezclado — ese patrón mixto es justo el que causó el problema
  real de `ANDROID-DUP-PSX-1`). Sega Mega Drive (65), SNES (5), Game Boy (25),
  Nintendo 64DD (1) y el único grupo PSX sin `crossfmt` en `reasons` (1) — **96
  grupos, 106 archivos descartados, 2 fallos** (el grupo PSX, bloqueado
  correctamente por el guard `DUP-CROSSFMT-6`: su "recomendado" ya no existe
  en el dispositivo, fila obsoleta, nada descartado), **~0,145 GB liberados**.
  Verificado en el dispositivo real (`adb shell test -e`) sobre una muestra.

---

### ANDROID-DUP-2 — El escaneo ADB nunca calcula SHA1/MD5: matcher nunca corre sobre `library_android.db`, duplicados legacy same-extension invisibles (hallazgo 2026-09-19, RG556, continuación de `ANDROID-DUP-1`)
> **Estado (revisado 2026-10-20):** ⏳ abierta — recomendación sin implementar, a decidir con el usuario

Origen: comprobando por qué GBA solo tenía 1 grupo `crossfmt` detectado (91
volcados legacy `[E]`/`[U]` encontrados por ADB) pese al ejemplo del usuario
(`Final Fantasy Tactics [E].gba`, `Pokemon Pinball RZ [E].gba`, ambos con el
mismo `size_bytes` que su contraparte canónica No-Intro ya presente —
`Final Fantasy Tactics Advance (Europe)...gba` y
`Pokemon Pinball - Ruby & Sapphire (Europe)...gba`, 16.777.216 bytes cada
par — casi con toda seguridad el mismo dump, distinto nombre).

Causa raíz: `_do_adb_scan()` (`web/handlers/scan.py:494-495`) escribe
**`sha1=""` y `md5=""` incondicionalmente** para cada fila — el escaneo ADB
solo lee metadata (`ls_recursive`: nombre/tamaño/mtime), nunca contenido.
Confirmado contra `library_android.db` real: las 12 filas de GBA
consultadas (Pokemon/Final Fantasy Tactics) tienen `sha1`/`md5` vacíos **y**
`canonical_title = NULL` en el 100% de los casos — el matcher de catálogo
nunca se ha ejecutado contra este repo en ninguna sesión.

Efecto en cascada, tres roturas distintas del mismo origen:
1. **Unión por SHA1** (`_review_groups_for_repo`) nunca enlaza nada en
   Android — cadena vacía siempre.
2. **Unión por `canonical_title` exacto** tampoco — nunca hay título que
   comparar.
3. **`crossfmt`** (la única vía que sí detecta algo hoy) exige **dos
   extensiones distintas** compartiendo el título normalizado — un volcado
   legacy `[E].gba` duplicando un `.gba` canónico comparte la *misma*
   extensión, así que ni siquiera esa vía lo alcanza. Resultado: un volcado
   legacy same-extension es invisible a los tres mecanismos de detección a
   la vez, pese a ser, en apariencia (mismo tamaño exacto), el caso más
   fácil de detectar de todos.

Efecto colateral, no confundir con el "iSuu dice que no hay logros pero el
emulador sí los da" que reportó el usuario (ese es el propio hash-check de
iSuu, una app de terceros en el dispositivo, fuera del alcance de este
repo) — pero **nuestra propia** lógica de "qué copia tiene soporte RA"
(`ra_supported`, vía `_load_ra_hash_map(...).get(md5_lower, ...)` en
`web/builders/duplicates.py`) también queda permanentemente `False` para
cualquier fila Android, porque el `md5` del que depende nunca se calcula —
el desempate por RA en el ranking de duplicados (`_review_entry_sort_key`)
es un no-op silencioso ahí mismo.

**Por qué no es trivial arreglarlo sin criterio**: calcular SHA1/MD5 real
requiere leer el contenido — para un `.gba`/`.nes`/`.snes` (unos pocos MB)
es barato; para un `.iso`/`.chd` de PS2/PSX (GBs) traerlo por ADB solo para
hashear sería lentísimo (ya documentado en `DUP-DISC-RA-2`: un solo disco
de PSX tarda minutos solo para `chdman`, sin contar la transferencia ADB
completa). Alternativa más barata: la mayoría de builds de Android traen
`sha1sum`/`md5sum` en el propio dispositivo (`adb shell sha1sum <ruta>`,
hash calculado en el propio teléfono, sin transferir el archivo) — viable
para el `AdbTransport` existente, pero sigue sin ser gratis a escala
(13.554 ROMs detectados en el último scan) y no se ha medido el coste real
en esta sesión.

**Recomendación (sin implementar, a decidir con el usuario)**:
1. Medir coste real de `adb shell sha1sum` sobre una muestra de plataformas
   cart-based (GBA/NES/SNES/GBC — archivos pequeños) antes de decidir si
   hashear todo o solo por debajo de un umbral de tamaño.
2. Si se activa el hash on-device, correr el matcher de catálogo contra
   `library_android.db` al menos una vez para poblar `canonical_title` —
   hoy nunca se ha ejecutado.
3. Alternativa más barata a corto plazo, sin tocar el transporte ADB:
   extender la unión `crossfmt` (`_review_groups_for_repo`,
   `web/builders/duplicates.py`) para que el título normalizado también
   enlace **misma extensión** cuando ambos lados carecen de SHA1 — con más
   riesgo de falso positivo que la vía actual (exige distinta extensión
   precisamente para evitar eso), necesitaría su propio guard cuidadoso
   antes de recomendar borrado automático.

No implementado en esta sesión | `web/handlers/scan.py:494-495`
(`_do_adb_scan`, hardcodea sha1/md5 vacíos), `web/builders/duplicates.py`
(`_review_groups_for_repo` — unión por sha1/título/crossfmt, `_load_ra_hash_map`
+ `_review_entry_sort_key` — desempate RA silenciosamente inactivo en
Android) | ✅ **implementado 2026-09-19** (PR #330, `AdbTransport.sha1_recursive`/`md5_recursive`,
hash calculado en el propio dispositivo — ver commit `7be90a7`). ✅ **Fase 1 del
roadmap 23 ejecutada 2026-09-20** (rescan con hash real, 9 plataformas
cartucho — `gba`/`megadrive`/`gb`/`nes`/`famicom`/`gbc`/`gamegear`/`snes`/`n64`,
29.657 archivos, 0 errores; troceado por plataforma tras un primer intento
fallido de escanear todo `/storage/521D-04EA/ROMs` de una vez que murió a los
3600s exactos por timeout, sin dejar nada aprovechable — ver
`.claude/roadmaps/23-android-hash-rescan-dedup.md`). `_build_review_queue`
contra `library_android.db` real: **3.270 grupos `sha1` reales en esas 9
plataformas** (antes 0, ningún matcher corría con hash vacío), **4,23 GB
desperdiciados**. Confirmados agrupados los 2 casos que motivaron el
hallazgo (`Final Fantasy Tactics [E].gba`/`Final Fantasy Tactics Advance
(Europe)...gba`, `Pokemon Pinball RZ [E].gba`/`Pokemon Pinball - Ruby &
Sapphire (Europe)...gba`, ambos razón `sha1`). De los 3.270: **1.279 son la
misma causa ya conocida** (`gb\GB official game ROM complete works\` —
subcarpeta que duplica el contenido de `gb\`/`gbc\` un nivel más adentro,
mismo patrón que `DUP-CROSSFMT-1` en PC, aquí también presente en la
Anbernic); **1.991 son duplicados genuinos distintos** (mismo contenido,
convención de nombre distinta — volcado legacy `[E]`/`(U)` vs No-Intro
completo, o variante región `(USA)`/`(USA, Australia)`). **No se ha
aplicado nada** (`resolve-duplicates --apply`) — pendiente de decisión
explícita del usuario, mismo criterio de todo el backlog. NES (1.581) y
Game Boy Color (1.268) concentran la inmensa mayoría, casi toda explicada
por la carpeta anidada | ✅ **Fase 2 completada 2026-09-20**: escaneo ADB con hash real sobre
`/storage/521D-04EA/ROMs/arcade` — 10.616 archivos vistos (la mayoría chips
sueltos de sets MAME sin comprimir, no ROMs independientes), **388 ROMs
reconocidas**, hash SHA1/MD5 calculado en las 388, 0 errores.
`_build_review_queue`-equivalente (unión por SHA1 exacto) contra
`library_android.db`: **0 grupos duplicados** — resultado limpio, coincide
con que el catálogo FBNeo se arregló y 67 sets se renombraron en este mismo
dispositivo el mismo día (`MATCH-ARCADE-DAT-2`/`ARCADE-RENAME-BUG-1f`).
Fase 3 (discos, 382 GB, 3+ horas) sigue pendiente de decisión explícita del
usuario — no lanzada | ✅ **Fase 3 parcial completada 2026-09-21**: las 5
plataformas de disco medianas (`nds` 480 archivos/385 ROMs, `gamecube` 19,
`dreamcast` 61, `3ds` 37, `psp` 7 — 971 archivos, 0 errores, hash real
calculado vía `POST /api/adb-scan` una llamada por plataforma) escaneadas
contra la RG556 real. `_build_review_queue` contra `library_android.db`:
**7 grupos duplicados reales, todos en Dreamcast, 4,79 GB desperdiciados**
(nds/gamecube/3ds/psp salieron limpios) — coincide con los 5 juegos
Dreamcast ya confirmados en `.cdi` por `DUP-DISC-RA-1e`. Ejemplos: `Dead or
Alive 2 (Europe).cdi` duplicado literal (mismo nombre, 2 copias, +1 variante
Beta); `Legacy of Kain - Soul Reaver` con la copia `(USA).cdi` byte-idéntica
a `(Europe).cdi` (mismo SHA1 — probable mal etiquetado de región, no una
versión distinta real); `Crazy Taxi 2`/`Sonic Adventure (XBLA)`/`D2 (USA)`
duplicados literales por nombre. **Hallazgo colateral — implementado 2026-09-21**:
`vmu_save_A1.bin`/`vmu_save_A2.bin` (saves de memory card Dreamcast) se
clasificaban como ROM, no como save — `.bin` no está en `save_extensions`
(`config.py:606-629`, correcto para no romper discos reales `.bin`), así
que `_do_adb_scan` (`web/handlers/scan.py`, rama `else`) los trataba como
ROM por descarte. Arreglado con una rama nueva por nombre (`suffix ==
".bin" and name.lower().startswith("vmu_save_")` → `upsert_save`, antes de
la rama de asset/ROM), caso estrecho a propósito (solo Dreamcast usa esta
convención) sin tocar `save_extensions` global. Test nuevo
`test_adb_scan_classifies_vmu_save_bin_as_save_not_rom` en
`tests/web/test_adb_scan_hashing.py`.

**Fase 3 completada al 100% (7/7 plataformas) 2026-09-21**: `psx` (215G) —
1746 archivos, 1685 ROMs, 0 errores. `ps2` (89,5G) — 27 archivos, 26 ROMs,
0 errores. `_build_review_queue` contra `library_android.db` completo:
**149 grupos duplicados en psx/ps2, 19,6 GB desperdiciados** (motivos: 94
`crossfmt`, 67 `sha1`, solapados). Casos reales: `Xenogears`,
`Metal Gear Solid`, `Final Fantasy VIII`, `Suikoden II`, `Parasite Eve`,
`Final Fantasy Tactics` (mismo disco en `.chd`+`.cue`+`.bin`+`.pbp`, o
regiones distintas mezcladas con crossfmt). **`disc_hash` no aportó nada
aquí** — a diferencia de la validación contra `library_pc.db` (rutas
Windows reales de la SD montada por lector de tarjetas), las filas de
`library_android.db` tienen rutas Android (`/storage/521D-04EA/...`) que
`get_psx_disc_hash` no puede leer desde esta máquina Windows
(`Path(source_path).stat()` falla en silencio, `None` para cada fila) —
esperado, no un bug; el caso `ANDROID-DUP-1` (CloneCD legacy) seguiría sin
validarse sin copiar esos archivos localmente primero.

**Hallazgo nuevo, real y sin implementar (riesgo real al aplicar la cola de
duplicados en PSX)**: en el grupo `Xenogears`, `_is_disc_set()`
(`web/builders/duplicates.py:56-80`) no protegió un set multi-disco real —
`Xenogears (Japan).chd` (edición japonesa, un solo disco, **sin** tag
`(Disc N)` en el nombre) quedó unido en el mismo clúster que
`Xenogears (USA) (Disc 1).chd`/`(Disc 2).chd`. Causa raíz: `_is_disc_set`
devuelve `False` (guard desactivado, se trata como duplicado normal) en
cuanto **un solo miembro** no tiene número de disco parseable
(`find_disc_number` → `None`, línea 77-78) — protege sets donde todos los
miembros llevan tag de disco, pero no cuando una edición regional
single-disc (sin tag) se mezcla con los discos individuales de una edición
multi-disco. Con datos reales de PSX vía ADB por primera vez este patrón
aparece en varios juegos reales de la biblioteca — **no aplicar
`resolve-duplicates --apply` sobre los grupos PSX/PS2 sin revisión manual**
hasta que esto se arregle, riesgo real de descartar un disco necesario de
un set multi-disco | ✅ Fases 1-2 completas; Fase 3 100% (7/7 plataformas,
149 grupos psx/ps2, 19,6 GB); hallazgo colateral `vmu_save` arreglado y
testeado; hallazgo nuevo `_is_disc_set` documentado sin implementar,
bloquea aplicar duplicados en PSX/PS2 sin revisión manual |

**Re-verificado 2026-09-21 (Día68), tras `DUP-DISC-SET-1` y el primer lote
aplicado (ver `ANDROID-DUP-2 Fase 3 — aplicado...` más abajo)**: consulta
directa de `_build_review_queue` contra `library_android.db` en solitario
(no vía CLI/servidor) confirma de nuevo `disc_hash: 0` para PSX/PS2
puramente Android — mismo motivo ya documentado arriba (rutas
`/storage/...` no legibles desde Windows). Estado tras el apply de hoy:
**99 grupos, 36,36 GB "desperdiciados"** (54 `sha1` + 59 `crossfmt`) — cifra
más alta que la original (19,6 GB) porque incluye deliberadamente sin
aplicar los 6 grupos de alto riesgo de `DUP-DISC-SET-2` (varios GB cada
uno, ej. `Final Fantasy VIII` con 4 discos) y ~46 sospechosos de
`DUP-DISC-TRACK-1`, no porque haya crecido el problema real.

**Medición real del punto 1 (2026-09-19, sesión siguiente, tras mergear
`ANDROID-DUP-2`/PR #330)**: se lanzó el rescan ADB completo con hash real
(`scan_run_id=6`, 21.608 archivos, mismo comando que ejecuta
`sha1_recursive`: `adb shell find /storage/521D-04EA/ROMs -type f -exec
sha1sum {} +`) en background. **Falló por timeout tras exactamente 3600s**
(el propio límite que `_do_adb_scan` le pasa —
`web/handlers/scan.py:453`, `transport.sha1_recursive(android_path,
timeout=3600)` — coincide con el timeout por defecto documentado en el
docstring de `sha1_recursive`, `sync/adb_transport.py`, que estimaba
"~100ms/archivo... una biblioteca de 20k archivos queda holgada" — la
estimación era optimista, el comando real no había terminado a los 3600s
exactos para 21.608 archivos). **Sin escritura parcial**: `_do_adb_scan`
solo escribe en `library_android.db` al final, tras completar tanto
`sha1_recursive` como `md5_recursive` (`web/handlers/scan.py:450-457`) — un
timeout a mitad de la primera pasada no deja ningún dato aprovechable,
`scan_run_id=6` se queda con `finished_at=NULL` para siempre. Confirma
`crc32sum`/reconsiderar el enfoque de `_hash_recursive` antes de relanzar
sin más: o (a) subir el timeout (con qué margen, sin dato de cuánto faltaba
para terminar), o (b) trocear el escaneo por subcarpeta de plataforma en
vez de un único `find` sobre toda la raíz (permite además guardar progreso
incremental en vez de todo-o-nada), o (c) medir con un subconjunto pequeño
primero (la recomendación #1 original de esta misma tarea, nunca hecha
antes de lanzar el escaneo completo — la sesión se saltó ese paso e
intentó ir directa a la escala completa). **`ANDROID-DUP-3` (famicom/ vs
nes/, 1.313 candidatos) sigue sin confirmación por SHA1 real** — toda su
evidencia sigue siendo solo nombre+tamaño, sin cambios | `web/handlers/scan.py:453`,
`sync/adb_transport.py` (`sha1_recursive`, timeout por defecto optimista) |
✅ **decisión tomada y ejecutada 2026-09-20** — opción (b) de las tres
listadas arriba: trocear el escaneo por plataforma. Ver roadmap
`.claude/roadmaps/23-android-hash-rescan-dedup.md` y el resultado real
(Fases 1-2 completadas) en el párrafo `✅ Fase 2 completada 2026-09-20` más
arriba en esta misma tarea |

---

### ANDROID-DUP-CROSSFMT-VERIFY-1 — los 61 grupos `crossfmt` restantes (53 pares `.chd`+`.bin` + 8 más, ~26,5 GB) no tienen ninguna verificación de contenido, solo coincidencia de nombre (hallazgo 2026-09-25)
> **Estado (revisado 2026-10-20):** ⏳ abierta — pendiente repetir la verificación con la función ya integrada

`reasons == ["crossfmt"]` en `_review_groups_for_repo` (`web/builders/
duplicates.py:992-1017`) agrupa por título normalizado (`normalize_title_
cross_format` sobre el stem) **sin comparar ningún hash** — a diferencia
de la unión por `sha1`. Mismo patrón de riesgo ya conocido en
`CHD-DELETE-NO-VERIFY-1` (lado PC), nunca corregido para esta cola.
Comprobación (solo lectura): para los 53 pares `.chd`+`.bin` mismo-título,
la ratio de tamaño `chd_bytes/bin_bytes` debería rondar 0,4–0,7× (compresión
CHD normal de un disco PSX) — en la práctica iba de **0,025× a 5,1×**, con
7 casos donde el `.chd` pesaba más que el `.bin` — geométricamente imposible
si fueran el mismo disco comprimido, indicio de que `crossfmt` empareja
contenido distinto bajo un título compartido | `web/builders/duplicates.py:
992-1017` (`crossfmt_groups` union, sin verificación de hash) | 🟡 **código
sin arreglar** (el bug de fondo sigue ahí para el resto de la biblioteca),
pero **los 53 pares ya verificados y resueltos con datos reales** — ver
abajo |

**Verificación real ejecutada 2026-09-25**: descargados los 53 pares completos
vía ADB (42 GB, ~17 min a 42 MB/s) y calculado el hash RA real
(`compute_psx_ra_hash`, el mismo que usa `PSX-CHD-REDUNDANT-1`/
`CHD-DELETE-NO-VERIFY-1` en PC) de cada `.chd` y cada `.bin` por separado,
comparados byte a byte (no solo tamaño):

- **46 coinciden de verdad** (hash RA idéntico) — aplicados con
  `resolve-duplicate-ra` (confirmación explícita del usuario antes de
  ejecutar, bloqueo del clasificador de modo automático por ser borrado
  irreversible en lote): **46/46 borrados, 0 errores, 22,78 GB liberados**,
  verificado por fila de BD (0/46 filas descartadas siguen en `library_
  android.db`). Sumado a los 22 del lote sha1 puro de hoy: **68 grupos
  aplicados, 25,08 GB liberados en total en la sesión de hoy.**
- **5 MISMATCH real** (hash RA distinto, contenido genuinamente distinto
  pese al nombre compartido) — **no tocados**: `Tenchu 2 - Birth of the
  Stealth Assassins (USA)`, `Spider-Man (USA)`, `Tony Hawk's Pro Skater 3
  (USA)`, `Legacy of Kain - Soul Reaver (USA)`, `Resident Evil (USA)`.
  Confirma que el riesgo era real, no teórico — un `apply-all` genérico sin
  esta verificación habría borrado contenido único en estos 5 casos.
- **2 no hasheables** (`compute_psx_ra_hash` devolvió `None`) —
  `Crash Bash (USA).chd` (el `.chd` no se pudo hashear; su `.bin` sí) y
  `Twisted Metal (Japan).bin` (el `.bin` no se pudo hashear; su `.chd` sí).
  **Hallazgo colateral en este segundo caso**: el hash del `.chd` de
  "Japan" (`31a6328a...`) es **idéntico** al de `Twisted Metal (Europe).chd`
  (par #48, ya confirmado `match` en el lote de arriba) — el archivo
  etiquetado "Japan" es casi con toda seguridad una copia mal nombrada del
  disco Europe, no una región real. Ninguno de los 2 se ha tocado.

**2026-09-29 — verificación convertida en función de backend real + botón en el frontend**
(petición explícita del usuario: "me gustaría que el backend lo hiciera" + "poder pedirlo
desde el frontend"): `services/ra_duplicates_service.py::verify_group_by_disc_hash()` —
descarga (ADB si es de consola, copia directa si es PC) el recomendado y cada candidato a
un directorio temporal, calcula `compute_psx_ra_hash` de cada uno y solo devuelve como
`safe_discard_paths` los que coinciden exactamente; nunca borra nada por sí misma. Nuevo
endpoint `POST /api/verify-duplicate-hash` (`web/handlers/duplicates.py`). En el frontend
(`review_copies.js`), el botón "Aplicar recomendación"/"Elegir esta" de cualquier grupo
`platform === 'PlayStation'` pasa primero por este endpoint (`_verifyThenResolve`) — solo
llama a `/api/resolve-duplicate-ra` con los paths ya verificados; el resto de plataformas
mantiene el flujo directo (sin el mismo riesgo confirmado). 4 tests nuevos (2 con `chdman.exe`
real + fixture PSX sintético de `test_ra_hash_psx.py`, incluido uno que reproduce el caso
exacto de 3 discos distintos con el mismo nombre mal resuelto) — suite completa 1496/1496.

Primera ejecución real (script de sesión, previa a esta implementación) contra los 89
grupos `crossfmt`-only restantes en la Anbernic: solo **1 verificado** (`Guilty Gear
(Europe)`, 0,48 GB), **0 mismatch**, **98 no verificables** — la inmensa mayoría de los
`.cue` de esta biblioteca referencian un `.bin` que ya no existe tal cual en el
dispositivo (mismo patrón de sheets rotas/legacy ya visto todo el día con FFVII/Lunar),
así que la función hace exactamente lo que debe: no tocar nada que no pueda confirmar de
verdad. Pendiente repetir con la función ya integrada (mismo resultado esperado, sin
cambios de lógica) y decidir manualmente los `.img`/`.mdf` sin soporte (`compute_psx_ra_hash`
no los reconoce, quedan siempre en `unverifiable_paths`).

**Alcance no cerrado**: el bug de fondo (`crossfmt` sin verificación de
hash) sigue sin arreglarse en `web/builders/duplicates.py` — los 8 grupos
`crossfmt`-only restantes (no `.chd`+`.bin`: `Guilty Gear (Europe).chd`,
`Driver (Europe).img`, `New (Slovakia) (Art Assets).img`, `Mortal Kombat 3
(Europe).bin` + otros del lado PC, ~1.828 grupos solo-PC nunca auditados
con este método) quedan pendientes de la misma verificación real antes de
cualquier apply.

---

### ANDROID-STVERSIONS-1 — `saves/.stversions/<core>/` (carpeta de versionado de Syncthing) se trata como save real, contamina la detección de duplicados legado (hallazgo 2026-09-21, `CABLE-SYNC-LEGACY-DUPS-1`)
> **Estado (revisado 2026-10-20):** ⏳ abierta — falta medir el alcance real en la Anbernic

Origen: al resolver por contenido (SHA1) los 130 grupos restantes de
`CABLE-SYNC-LEGACY-DUPS-1`, 2 grupos (`Metroid - Zero Mission [E].srm`,
`Sonic Advance 2 [E].srm`) tenían una copia bajo
`saves/.stversions/<core>/` — la carpeta de versionado automático de
Syncthing (herramienta de terceros instalada en el dispositivo, no creada
por este proyecto). No es un save real que el usuario gestione, es un
artefacto de sincronización ajeno a `rom_manager` — mismo tipo de ruido que
ya se excluyó para `_descartados/` (`TRASH_DIR_NAME`) y `emulator_saves/`
(`EMULATOR_SAVES_DIR_NAME`, `CABLE-SYNC-EMULATOR-SAVES-LEAK-1`).

**Re-verificado 2026-09-22 (Día69), contra el código real, no contra
suposiciones**: los 3 sitios señalados como candidatos ya excluyen
`.stversions/` hoy — no falta ningún guard nuevo.

- Los 3 walks **locales** (`cable_engine.py:56` `iter_files`,
  `cable_sync_daemon.py:432-437` `_iter_local`, `sync_cable.py:516-521`
  `_iter_files`) ya filtran `not d.startswith(".")` antes de mirar
  `TRASH_DIR_NAME`/`EMULATOR_SAVES_DIR_NAME` — cualquier directorio oculto,
  `.stversions` incluido, nunca entra.
- El lado **Android** (`sync/adb_transport.py`, `ls_recursive()` y
  `_hash_recursive()`/`sha1_recursive()`/`md5_recursive()`, usados por
  `cable_sync_daemon.py:421` y por `_do_adb_scan` en `web/handlers/scan.py:456`
  — el mismo scan que alimenta `library_android.db` para
  `DUP-DISC-SET-2`/`DUP-DISC-TRACK-1` arriba) ya excluye por defecto
  (`exclude_hidden=True`) cualquier segmento de ruta que empiece por `.`, y
  `.stversions` empieza por punto. Confirmado con `git log`: el filtro de
  `ls_recursive` existe desde marzo 2026 (`ebd9f54`) y el de
  `_hash_recursive` desde el 2026-09-19 (`7be90a7`, `ANDROID-DUP-2`) —
  **ambos ya estaban en el código antes** de que se encontrara el leak el
  2026-09-21, así que ningún camino de sync/escaneo persistente de este
  proyecto pudo haberlo producido.
- Causa real de los 2 casos encontrados: la comparación SHA1 de
  `CABLE-SYNC-LEGACY-DUPS-1` fue un script ad-hoc de esa sesión (no hay
  ningún endpoint/feature `legacy-dup*` en el código — la propia entrada de
  `CABLE-SYNC-LEGACY-DUPS-1` dice "limpieza manual en el dispositivo, sin
  tocar código"), que aparentemente sí leyó `.stversions/` sin pasar por
  `AdbTransport`. No es un gap del cable-sync/escaneo real.

**Obsoleto — sin fix de código que hacer** (mismo patrón que la rama 07 del
roadmap general, `.claude/roadmaps/INDEX.md`): el problema tal como está
descrito ya no existe en el cable-sync/escaneo persistente. Si se repite un
script ad-hoc de comparación de saves en el futuro, aplicar el mismo filtro
`exclude_hidden`/`startswith(".")` que ya usa el resto del proyecto.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ANDROID-STVERSIONS-1 | Medir el alcance real de `saves/.stversions/` en la Anbernic (ADB) y, si procede, excluirlo del cable-sync/escaneo de duplicados igual que `_descartados/`/`emulator_saves/` | `web/handlers/sync_cable.py`, `sync/cable_engine.py`, `web/cable_sync_daemon.py`, `sync/adb_transport.py` | ⚪ **obsoleto, verificado 2026-09-22** — los 3 sitios y `AdbTransport` ya excluyen directorios ocultos (`.stversions` incluido); el leak de Día67 vino de un script ad-hoc fuera del código persistente, no de un gap real |

---

### ANDROID-DUP-3 — `famicom/` es una segunda carpeta-plataforma paralela a `nes/` (86% de solapamiento por nombre+tamaño) con un pack de scraper (imágenes/vídeo) tratado como si fuera la librería; `fds/` duplica literalmente el contenido de `Famicom Disk System/` y además arrastra volcados de placa arcade y NES sueltos (hallazgo 2026-09-19, RG556, resuelve el punto 4 pendiente de `ANDROID-DUP-1`)
> **Estado (revisado 2026-10-20):** ⏳ abierta — 3 acciones distintas pendientes sobre famicom/

Origen: verificando el punto 4 de `ANDROID-DUP-1` ("verificar contenido real
de `fds/` vs `Famicom Disk System/` antes de aplicar `DUALFOLDER-12`"), por
ADB en vivo contra `/storage/521D-04EA/ROMs/` de la RG556 (misma consola,
misma sesión que `ANDROID-DUP-1/2`).

**Gotcha de tooling encontrado en el camino**: `adb.exe shell <args...>`
concatena todos sus argumentos con espacios y reenvía **una sola cadena** al
shell remoto — las comillas que Git Bash ya consumió al tokenizar no viajan.
Un comando como `adb.exe shell ls -la "/ruta/con espacios/"` llega partido en
3 tokens al dispositivo y falla o (peor) apunta a una ruta distinta que
coincide parcialmente por case-insensitivity de exFAT. Forma correcta:
pasar el comando remoto completo como **un único argumento** con sus propias
comillas simples: `adb.exe shell "ls -la 'ruta con espacios'"`. Así fue como
apareció por accidente el hallazgo de `famicom/` de abajo (un primer intento
mal citado listó esa carpeta por error, en vez de `Famicom Disk System/`).

**`fds/` vs `Famicom Disk System/` (27 vs 2 entradas)**:
`Famicom Disk System/` contiene exactamente 2 archivos reales: `Mysterious
Murasame Castle, The (Korea) (Virtual Console).fds` (131.000 bytes) y `Super
Mario Bros. 2 (Japan) (En).fds` (65.500 bytes). `fds/` (**26 entradas**,
recuento corregido — `ANDROID-DUP-1` decía 27 por un `ls` mal contado)
contiene los mismos 2 `.fds` duplicados, más **10** archivos que no son ROM
de ninguna plataforma de este proyecto (recuento corregido — se dijeron 7 en
un primer repaso: `400-a01.fse`, `400-a02.fse`, `400-a04.10l`, `400-a06.15l`,
`400-e03.5l`, `412-a05.12l`, `412-a07.17l`, `mds-gn chr e.u4`, `mds-gn prg
e.u7`, `rp2c04-0003.pal`), un `gamelist.xml` de frontend, 5 juegos NES con
pareja `.zip`+`.nes`, y 2 ZIPs adicionales sin pareja `.nes` visible
(`Goonies (Japan) (Disk Writer).zip`, `TwinBee (Japan) (En) (Disk
Writer).zip`).

**Verificación por SHA1 (no solo nombre/tamaño) — sesión de reparación,
todo el árbol de decisión de abajo confirmado con hash real, cero
suposiciones**:
- Los 6 ZIPs "regionales" (`Balloon Fight (Japan) (En) (Proto).zip`, `Ice
  Climber (Japan) (En) (Disk Writer).zip`, `Metroid (Japan) (Rev 1).zip`,
  `Super Mario Bros. (Japan) (En).zip`, `Super Mario Bros. 2 (Japan) (En).zip`,
  `Super Mario Bros. 2 (USA) (Rev 1).zip`) **no son dumps regionales
  distintos** — cada uno contiene, byte a byte (SHA1 idéntico), el mismo
  `.nes`/`.fds` que ya está suelto sin comprimir en la misma carpeta `fds/`.
  Repaquetados redundantes, nombre engañoso (el tag "(Japan)"/"(Proto)" no se
  corresponde con el contenido real).
- Los 10 "volcados de chip" **son exactamente el contenido interno,
  archivo por archivo (SHA1 idéntico), de `Goonies (Japan) (Disk
  Writer).zip` (3 ficheros: `mds-gn chr e.u4`, `mds-gn prg e.u7`,
  `rp2c04-0003.pal`) y `TwinBee (Japan) (En) (Disk Writer).zip` (7 ficheros:
  los `400-*`/`412-*`)** — ambos ZIPs son sets arcade MAME reales de Nintendo
  VS. System (VS. The Goonies / VS. TwinBee), no juegos de Famicom Disk
  System pese al tag "(Disk Writer)". Alguna herramienta los extrajo sueltos
  en `fds/` en algún momento — exactamente el patrón que el propio
  `CLAUDE.md` ya prohíbe (`ZIP-ROUTE`: "un ZIP arcade nunca se extrae, el ZIP
  es el ROM").
- Los 2 `.fds` de `fds/` son SHA1-idénticos a los de `Famicom Disk System/`.
- Los 5 `.nes` sueltos de `fds/` (`Balloon Fight (USA)`, `Ice Climber (USA,
  Europe, Korea)`, `Metroid (USA)`, `Super Mario Bros. (World)`, `Super
  Mario Bros. 2 (USA) (Rev 1)`) son SHA1-idénticos a copias ya existentes en
  `nes/` — 4 con el mismo nombre exacto, y `Ice Climber` con el mismo hash
  bajo un tag de región ligeramente distinto ya presente en `nes/`
  (`Ice Climber (USA, Europe, Asia) (En).nes`). Además, `Ice Climber (Japan)
  (En) (Disk Writer).nes` existe con SHA1 idéntico **tanto en `nes/` como en
  `famicom/`** — mismo patrón de duplicado de plataforma completa ya descrito
  más abajo.

**Conclusión**: `fds/` no tiene ni un solo byte de contenido único —
absolutamente todo lo que contiene es, o bien un duplicado confirmado por
hash de algo que ya existe en `Famicom Disk System/`/`nes/`, o bien un
repaquetado redundante de otro archivo de la misma carpeta, o bien un ZIP
arcade mal ubicado. No aplica `DUALFOLDER-12` tal cual (no es un par limpio
tipo `atari2600/`+`Atari 2600/`): hacen falta 3 acciones distintas — (a)
borrar los 6 ZIPs regionales + los 10 volcados de chip sueltos + los 2 `.fds`
+ los 5 `.nes`, todos con duplicado confirmado por hash, (b) mover
`Goonies...zip`/`TwinBee...zip` a `arcade/` (son ROM arcade legítimos, mal
ubicados, no basura), (c) dejar `gamelist.xml` tal cual (metadata de
frontend, fuera de alcance). Implementado en rama `fix/android-fds-cleanup`
— ver tarea `ANDROID-FDS-CLEANUP-1` más abajo.

**Hallazgo nuevo, mayor: `famicom/` duplica `nes/` a escala de plataforma
completa**. `famicom/` tiene **5.184 archivos** — no es solo un pack de ROMs:
3.092 `.png`, 1.530 `.nes`, 460 `.jpg`, 100 `.mp4`, 1 `.xml`, 1 `.db`, repartidos
en subcarpetas propias de un scraper de frontend: `media/` (412 `.jpg`),
`downloaded_images/` (2.992 archivos, el grueso de los `.png`),
`top100/` (18), más dos packs con nombre de curador: `# DYNAVISION #` (91
`.nes`) y `# PT-BR #` (199 `.nes`, romhacks de traducción al portugués de
Brasil, tags `[T-BR] [T-Balboa G-Monkey's Traducoes]` — **legítimos, no
duplicados**, mismo caso ya señalado en `ANDROID-DUP-1` para parches `[T+...]`).
De los 1.530 `.nes` de `famicom/` (recursivo), **1.313 (86%) comparten nombre
exacto con un archivo de `nes/`** (3.336 `.nes` en `nes/`). Muestreo de 3
coincidencias (`Bases Loaded (USA).nes`, `NFL (USA).nes`, `Championship Rally
(Europe).nes`) — mismo tamaño byte a byte en ambas carpetas. Las copias de
`nes/` datan de 2026-03-11 (pasada de renombrado canónico No-Intro de este
proyecto); las de `famicom/` son todas del mismo instante, 2026-09-09 13:16
— una única importación posterior en bloque, casi seguro un "pack" de
scraper para DaijiShō/iSuu que trajo sus propias copias de ROM junto con el
material gráfico. Como DaijiShō/iSuu normalmente mapean "Famicom" y "NES" al
mismo core/sistema, esta carpeta paralela completa es una explicación mucho
más directa de "todos los juegos NES aparecen duplicados" que el matiz de
nomenclatura legado `[!]`/`(U)` ya documentado — probablemente ambas causas
se suman.

**Recomendación (sin implementar, a decidir con el usuario)**:
1. Confirmar por SHA1 los 1.313 candidatos `famicom/`↔`nes/` en cuanto
   termine el rescan ADB con hash en curso (`ANDROID-DUP-1`/`ANDROID-DUP-2`)
   — la evidencia de esta sesión es solo nombre+tamaño, no hash.
2. Decidir con el usuario el tratamiento de `famicom/`: ¿carpeta redundante a
   fusionar/eliminar tras verificar hash (conservando el material gráfico si
   aporta valor), o cache activa de DaijiShō/iSuu que debe excluirse
   explícitamente de cualquier dedup/organize futuro (vía
   `excluded_directories` en `config.py`, ya usado para BIOS/Android)? No
   borrar unilateralmente sin confirmar que `media/`/`downloaded_images/`/
   `top100/` no los gestiona activamente un frontend de terceros.
3. Los 91 `# DYNAVISION #` y 199 `# PT-BR #` necesitan comparación de
   contenido (no solo nombre) antes de tocarlos — son candidatos a homebrew/
   romhacks legítimos, mismo criterio que los parches `[T+...]` de `nes/`.
4. Extender la recomendación de `DUALFOLDER-12` con un caso "carpeta mixta":
   ni `fds/`↔`Famicom Disk System/` ni `famicom/`↔`nes/` son pares limpios
   como `atari2600/`/`Atari 2600/` — ambos arrastran contenido ajeno a la
   plataforma nominal y necesitan triage antes de fusionar.

**Intento de investigar la config de DaijiShō/iSuu en el dispositivo (opción
elegida por el usuario para decidir el punto 1)**: bloqueado sin root.
`adb shell` corre como `shell` (uid 2000, grupo `ext_data_rw` incluido), y
`Android/data/{com.magneticchen.daijishou,com.iisulauncher}/files/` están
genuinamente vacías (no es un bloqueo de permisos — el propietario del
directorio coincide con un grupo al que `shell` pertenece). Ninguna de las
dos apps es depurable (`run-as` falla con "package not debuggable"), así que
su almacenamiento interno (`/data/data/<paquete>/databases`, donde
probablemente vive la config real de "sistemas") no es legible sin root.
Confirmar si `famicom`/`nes` (o `fds`/`Famicom Disk System`) están dados de
alta como sistemas duplicados en la propia app requiere mirarlo
**directamente en el dispositivo**, dentro de la UI de cada launcher — mismo
límite ya documentado para el caso PS2 en `ANDROID-DUP-1`.

Fds/famicom no implementado en esta sesión salvo lo indicado en
`ANDROID-FDS-CLEANUP-1` (más abajo) | Evidencia recogida por ADB en vivo
(`adb shell find/ls/sha1sum` contra `/storage/521D-04EA/ROMs/{fds,Famicom
Disk System,famicom,nes}/`) | 🟡 `fds/` resuelto y verificado por hash
(`ANDROID-FDS-CLEANUP-1`); `famicom/` vs `nes/` y la config de
DaijiShō/iSuu siguen sin decidir — pendiente de que el usuario revise la
app en el dispositivo |

---

### ANDROID-ORGANIZE-ADB-1 — `organize-source` ya tiene el motor de dedup+ruteo arcade necesario; el hueco real es que no existe transporte de escritura ADB, solo filesystem local → #275
> **Estado (revisado 2026-10-20):** ⏳ abierta — dos caminos investigados, decisión de alcance pendiente del usuario

Origen: el usuario preguntó en medio de la limpieza de `fds/`
(`ANDROID-FDS-CLEANUP-1`) si la función "organize" ya arregla este tipo de
casos, y si no, que se le añadiera.

**No hace falta construir un motor de dedup nuevo — ya existe y está muy
probado.** `organize-source` (CLI, `cli.py:258-286` registra el subcomando,
`cli.py:1133-1280` lo implementa reutilizando `_run_inbox_pipeline` de
`web/inbox_pipeline.py`) ya hace exactamente lo necesario: detecta ZIPs
arcade completos por CRC sin extraerlos (`_is_arcade_zip_container`), extrae
y organiza el resto, deduplica por SHA1/CRC interno, y resuelve conflictos de
nombre — es el mismo motor que resolvió toda la saga
`ARCADE-DAT-CONTAMINATION-*`/`PSX-STRUCTURE-*` (cientos de miles de archivos,
sesiones de 2026-09-02 a 09-04), incluida la propia Anbernic (`E:\Carpetas
anbernic`, máquina "rammu").

**El límite real es de transporte, no de lógica**: `organize-source` exige
`source_path.resolve().exists()` (`cli.py:1137-1138`) — un `pathlib.Path`
real del sistema de archivos. Eso funcionaba contra la Anbernic en la máquina
"rammu" porque ahí la SD se monta como letra de unidad. En esta máquina
("Ruben"), la RG556 no se monta como unidad (probable causa: Android
11+/MTP sin soporte de almacenamiento masivo) — el único acceso es `adb`, y
`AdbTransport` (`sync/adb_transport.py`) hoy **solo tiene lectura**
(`ls_recursive`, `sha1_recursive`, `md5_recursive`); no hay `mv`/`rm`/`push`
genérico. La versión web más simple, `_do_organize_library`
(`web/handlers/organize.py:410`), tampoco sirve de comparación — ni siquiera
tiene dedup de contenido, solo mueve por `platform` de la BD, y también
asume filesystem local (`shutil.move`).

**Dos caminos, sin implementar ninguno todavía**:
1. **Sin código nuevo**: si se puede extraer la tarjeta SD de la RG556 y
   leerla con un lector USB (monta como letra de unidad en Windows),
   `organize-source --apply` funciona hoy mismo tal cual, sin tocar una
   línea — sería la forma más rápida de limpiar `fds/`/`famicom/` con la
   herramienta real en vez de comandos `adb` sueltos como en
   `ANDROID-FDS-CLEANUP-1`.
2. **Con código nuevo**: añadir transporte de escritura a `AdbTransport`
   (`push`/`pull`/`mv`/`rm`) y un adaptador para que `organize-source` opere
   sobre él — o, más barato de construir, un modo "espejo": `adb pull` a un
   directorio temporal, correr `organize-source --apply` normal ahí (cero
   cambios a su lógica ya probada), y `adb push`+`adb rm` de vuelta solo de
   lo que cambió. El coste es red (round-trip de contenido que sí se mueve),
   no lógica nueva.

**Recomendación**: decidir con el usuario si la opción 1 (lector SD) resuelve
ya el caso concreto de esta sesión antes de invertir en la opción 2 — que sí
merecería su propio epic/issue si se decide construirla, dado que es una
pieza de infraestructura reutilizable (serviría para cualquier limpieza
futura sobre Android, no solo `fds/famicom`), no solo un fix puntual.

No implementado en esta sesión | `cli.py:1133-1280` (`organize-source`),
`web/inbox_pipeline.py` (`_run_inbox_pipeline`), `sync/adb_transport.py`
(solo lectura), `web/handlers/organize.py:410` (`_do_organize_library`, web,
tampoco sirve) | 🔵 investigado, decisión de alcance pendiente del usuario |

### GDI-ORGANIZE-1 — Organizar los 9 sets Dreamcast/Naomi extraídos: 2 bugs reales encontrados antes de poder mover nada (2026-09-29, continuación de `JUNK-7Z-SUPPORT-1`)
> **Estado (revisado 2026-10-20):** ⏳ abierta — quedan sets sin mover/sin match (Mortal Kombat Gold, Sonic Adventure, Jet Set Radio)

Tras extraer los 9 `.7z` Dreamcast/Naomi, `GET /api/plan` reveló dos bugs reales, ninguno introducido hoy:

1. **`operation_planner.build_plan()` calcula mal el destino para una plataforma "subfolder" (PSX/Saturn/Dreamcast/Wii) cuando el origen vive fuera de cualquier carpeta de plataforma** (`planner/operation_planner.py:195-201`, `_DISC_SUBFOLDER_PLATFORMS`/`_DISC_SUBFOLDER_CATALOG_PLATFORMS`): la rama `else` (`source.parent.parent / folder_name / new_filename`) asume que el origen ya vive *dentro* de la carpeta de plataforma (p. ej. corrigiendo un subcarpeta-por-juego mal hecho) — para un archivo suelto en `Unknown\`, `source.parent.parent` es la **raíz de la biblioteca**, no `dreamcast\`. Verificado contra la API real: los 8 títulos Dreamcast matched (7 en `Unknown\` + 1 en `PlayStation 2\`) proponían todos mover a `F:\Juegos Retro\<Título>\` en vez de `F:\Juegos Retro\dreamcast\<Título>\` — incluido un título Dreamcast preexistente no tocado por mí (`Skies of Arcadia (Europe)...(Disc 2).zip`), confirmando que no es un caso aislado de hoy. **Sin arreglar** — toca lógica compartida por las 4 plataformas subfolder, no es un fix para hacer con prisa; candidato a su propia rama con tests dedicados. Mientras tanto, cualquier `apply` sobre contenido recién llegado a estas 4 plataformas (vía Inbox parcial, extracción manual, etc.) debe revisarse a mano antes de confirmar — no fiarse del `target` que devuelve `/api/plan` para estos casos.
2. **`parse_tracks_from_gdi()` (`converters/chd_converter.py:237`) no soportaba nombres de pista entre comillas con espacios** — el formato real de un `.gdi` (`4 0 4 2352 "Crazy Taxi (USA) (Track 4).bin" 0`) casi siempre cita el nombre porque casi siempre tiene espacios; `line.split()` cortaba en el primer espacio (`'"Crazy'`), truncando la ruta real. Usada también por `renamer/file_renamer.py` (`move_disc_set_to_subfolder`, el mecanismo real de mover/renombrar sets Dreamcast) y `retroachievements/ra_hash_saturn_dreamcast.py` — sin ningún test hasta hoy (`tests/test_chd_converter.py` no tenía ni un caso de `.gdi`). **✅ arreglado** — regex que prioriza el nombre citado, con fallback al `split()` original para el formato sin comillas; 2 tests nuevos (`test_parse_tracks_from_gdi_quoted_filenames_with_spaces`, `..._unquoted_filename_fallback`). Suite completa 1472/1472 en verde.

**Aplicado contra la biblioteca real tras el fix del punto 2** (bug 1 evitado a mano, moviendo directamente por script de sesión en vez de vía `/api/apply`, con el mismo destino que un planner correcto habría calculado): **6 de los 9 movidos limpio** a `dreamcast\<Título>\` (`Crazy Taxi (USA)`, `Marvel vs. Capcom - Clash of Super Heroes (USA)`, `Resident Evil - Code - Veronica (USA) (Disc 1)`, `Sonic Adventure (USA) (En,Ja,Fr,De,Es)`, `Sonic Adventure 2 (Europe) (En,Ja,Fr,De,Es)`, `Street Fighter III - 3rd Strike - Fight for the Future (Japan)`). **3 sin resolver, dejados aparte a propósito**:
   - `Jet Set Radio (Europe).7z` — nunca extraído (ver `JUNK-7Z-SUPPORT-1`): tiene un `.zip` hermano con el mismo contenido exacto (mismos 3 tracks, sheet `.cue` en vez de `.gdi`) — duplicado real, decisión pendiente (cuál sheet conservar).
   - `Sonic Adventure (Europe) (En,Ja,Fr,De,Es).gdi` — extraído pero **no movido**: `dreamcast\Sonic Adventure (Europe) (En,Ja,Fr,De,Es)\` ya tiene un `.cdi` completo del mismo juego (formato distinto, mismo contenido presumible, sin verificar por hash) — duplicado real, sigue en `Unknown\`, decisión pendiente.
   - `Mortal Kombat Gold (USA).gdi` (53 tracks) — **sin match**, `match_confidence`/`canonical_title` siguen `NULL` (`unmatched_reason: hash_not_found` para las 54 filas, sheet + tracks) — causa no investigada todavía, candidato a revisar aparte (¿el catálogo Dreamcast no tiene esta entrada, o algo en el matcher falla con sets de tantas pistas?).

**Los 6 sets movidos, enviados a la Anbernic real por ADB (2026-09-29)** — `POST /api/cable-sync` (`direction=send_selected`, `search=<título exacto>`, uno a uno; verificado antes con un dry-run que el filtro no arrastraba ningún otro juego). 24 archivos, ~7,2 GB, 0 errores, verificado con `adb shell ls` en el dispositivo. **Gotcha real de la sesión, no del código**: pasar el cuerpo JSON con rutas Windows (`F:\Juegos Retro`) vía `curl -d '...'` inline falla silenciosamente en este entorno (Git Bash/curl en Windows) — cualquier backslash en el valor hace que el body llegue corrupto y el servidor lo interpreta como `{}` (así que `direction` cae a su default y el error engañoso "anbernic_path requerido" aparece aunque se haya mandado). Solución: escribir el JSON a un archivo y usar `curl --data-binary @archivo`. Dejar esto anotado para la próxima vez que alguien llame a esta API a mano desde esta máquina.

### ANDROID-DUP-PSX-1 — PlayStation en la Anbernic: verificación por pareja real de SHA1 antes de aplicar, no fiarse del `reasons` a nivel de grupo (hallazgo real 2026-09-29)

Al intentar repetir el mismo patrón GBA/NES/Game Gear contra PlayStation (124 grupos, 14,33 GB), **hallazgo real antes de tocar nada**: `_review_groups_for_repo` une por Union-Find — un grupo puede quedar contaminado con discos genuinamente distintos si comparten un `canonical_title`/nombre mal resuelto por el catálogo, aunque el `reasons` del grupo incluya `sha1`. Caso confirmado con datos reales: `Metal Gear Solid (World) (4B4E083C) (Addon).chd` existía en 3 ubicaciones con **3 SHA1 distintos** (raíz `psx/`, `Metal Gear Solid (Spain) (Disc 1) (v1.1)/`, `Metal Gear Solid (Spain) (Disc 2) (v1.1)/`) — 3 discos reales y distintos con el mismo nombre genérico sin identificar, agrupados como "duplicados" por título exacto. Aplicar `resolve_duplicate_ra` a nivel de grupo (como se hizo en GBA/NES) habría borrado los 2 discos españoles reales creyéndolos copias redundantes.

**Fix aplicado en esta sesión, sin tocar código** (verificación adicional en el script de aplicación, no en `_review_groups_for_repo`): en vez de confiar en `reasons`, comparar el SHA1 real de cada candidato a descartar contra el SHA1 del "recomendado" uno a uno — solo se descarta si coinciden exactamente. De **149 pares evaluados** (41 grupos con `sha1` en razones), **110 fueron rechazados por SHA1 distinto** (contenido genuinamente diferente pese a compartir grupo) y solo **39 verificados como duplicados reales**.

**Aplicado contra la Anbernic real** (backup previo de `library_android.db`): **37/38 grupos aplicados, 0 errores reales, 7,51 GB liberados**. El único grupo no resuelto (`Ninpuu Sentai Hurricanger...`) lo bloqueó el guard de seguridad ya existente (`DUP-CROSSFMT-6`) porque su "recomendado" (`Enemy Engaged - Apache-Havoc...`) ya no existe en el dispositivo — fila obsoleta, nada descartado, correcto. Verificado en el dispositivo real: `Metal Gear Solid (World)(Addon).chd` de la raíz (el único SHA1 realmente duplicado, coincide con `USA (Disc 1).chd`) desaparecido; los dos discos españoles siguen íntegros. Recuento de filas en BD coincide exacto (PlayStation 1580→1543, −37).

**Hallazgo colateral, no bloqueante**: los `.chd`/`.cue` de los 2 discos españoles siguen en `library_android.db` pero **ya no existen físicamente en el dispositivo** (`ls -la` real lo confirma) — filas fantasma de antes de esta sesión, no causadas por este apply (el filtro por pareja las excluyó correctamente al no compartir SHA1 con nada). Indica que `library_android.db` necesita un rescan ADB completo para depurar filas obsoletas — candidato a tarea propia, no urgente.

**Pendiente**: los **83 grupos PSX restantes con razón `crossfmt` únicamente** (4,58 GB, mismo hueco que `ANDROID-DUP-CROSSFMT-VERIFY-1` — agrupados por título normalizado sin ningún hash, `.chd` vs `.bin`/`.cue` del mismo disco en contenedores distintos) necesitan la verificación completa por hash RA de disco (`compute_psx_ra_hash`, descargando cada candidato vía ADB) antes de aplicar nada — mismo método ya usado el 2026-09-25 para los 53 pares `.chd`+`.bin` de esa tarea. No abordado en esta sesión por el volumen de datos a descargar.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ANDROID-DUP-PSX-1 | Verificación por pareja SHA1 antes de aplicar dedup en PSX/Anbernic | `services/ra_duplicates_service.py::resolve_duplicate_ra` (motor, sin tocar) | ✅ 37/38 grupos verificados y aplicados, 7,51 GB liberados, 0 errores reales. 83 grupos `crossfmt`-solo (4,58 GB) pendientes de verificación por hash RA real — ver `ANDROID-DUP-CROSSFMT-VERIFY-1` |

### DUP-CHD-RAW-1 — Mismo juego repetido en DuckStation: 53 pares de `.chd` son el *mismo disco* y la herramienta de duplicados no los ve (hallazgo 2026-10-21, solo lectura, RG556 conectada)

Origen: el usuario ve el mismo juego varias veces en la lista de DuckStation y pregunta si RetroVault no tiene ya la opción de quitar duplicados (sí: se aplicó a GBA/NES/Game Gear y a PSX el 2026-09-29, 37 grupos / 7,51 GB, ver `ANDROID-DUP-PSX-1`).

**Medido en vivo** (lista del DuckStation oficial recorrida con `uiautomator` + inventario `find` de `/storage/521D-04EA/ROMs/psx` + lectura de 124 bytes de la cabecera de cada `.chd`; nada modificado): DuckStation lista **308 entradas = 227 títulos distintos** (DuckStation identifica por serial/BD y muestra un solo título, p. ej. `Alundra (Spain)` para `Alundra (Europe).chd` y `Alundra (Spain).chd`). **74 títulos aparecen repetidos (81 entradas de más)**. De los 59 grupos con ≥2 `.chd`: **53 son el mismo disco** (`rawsha1` de la cabecera CHD v5 idéntico → mismos datos, solo cambia nombre/compresión/ubicación): **78 archivos sobrantes ≈ 20,57 GB, 30 de ellos dentro de subcarpetas**; **6 son discos distintos** con el mismo título (p. ej. `Capcom vs. SNK … (Europe)` vs `(Japan)`, `MediEvil (USA)` vs `(Europe)`, `Resident Evil 3 (USA, Canada)` vs `(Australia)`) → NO son duplicados; **15 grupos mezclan formatos** (`.chd`+`.cue`, `.chd`+`.img`, `.ecm`; los 83 `crossfmt` ya conocidos de `HW-1`).

**Causa raíz** (por qué la herramienta no los ve):
1. El SHA1 que guarda `library_android.db` es el del *fichero* `.chd`: dos CHD del mismo disco comprimidos distinto tienen SHA1 distinto (p. ej. `Hogs of War (Europe).chd` `915db429…` vs `…/Hogs of War (USA).chd` `e737231e…`, 238.459.761 vs 238.315.172 B) → `reasons` nunca incluye `sha1`.
2. PSX no tiene `canonical_title` (todas las filas PSX de la BD Android tienen `canonical_title`/`match_confidence` NULL; falta el DAT Redump, `PSX-CATALOG-MISSING-1`) → tampoco agrupa por título exacto.
3. El agrupado difuso por título/región excluye PSX a propósito (`web/builders/duplicates.py:1098`, `_MULTI_DISC_RISK_PLATFORMS`, `planner/operation_planner.py:78`; motivo en 1069-1087: 18 discos reales de FF VII fusionados).
4. El único detector de "mismo disco" en PSX es el hash RA (`retroachievements/ra_hash_psx.py:197-208`, `.chd` → `_hash_chd_file` con `chdman`, que necesita **el fichero completo**) → hay que bajar cada CHD por ADB (~300 MB) → es el bloqueo de `HW-1`.
5. Ningún código lee el `rawsha1` de la cabecera CHD (`grep rawsha1|MComprHD src/` → 0 resultados). Con 124 bytes por ADB (`adb exec-out head -c 124`, offset 64, 20 bytes, solo `version==5`) se obtiene el hash del disco sin descargar nada.
6. Evidencia colateral de nombres equivocados: `Tony Hawk's Pro Skater 3 (USA).chd` es el disco europeo (el fork creó la memcard `…(Europe)_1.mcd` y el juego guardó el serial `BESLES-03645`), igual que `Contra - Legacy of War (USA).chd`, `Hogs of War (USA).chd` o `Darkstalkers 3 (USA).chd` (DuckStation los muestra como `(Europe)`). Efecto añadido: carpetas-conjunto con nombre de otra región (`Hogs of War (Europe)/Hogs of War (USA).chd`, `Vagrant Story (Europe)/Vagrant Story (Germany).chd`) y pistas sueltas con nombres de otros discos (`Marranos en Guerra (Spain).bin`, `Euro Demo Germany…bin`) dentro de ellas: restos de una organización anterior que añaden entradas.
7. Contexto: `library_android.db` es de 2026-10-02 (sin rescan desde entonces, `HW-6/HW-7`); `excluded_duplicate_groups` tiene 7.882 grupos descartados por el usuario ("mantener ambos").

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-CHD-RAW-1a | Leer `rawsha1` (CHD v5, cabecera de 124 bytes) y usarlo como clave de "mismo disco" en la cola de duplicados PSX, por ADB sin descargar; el motor de resolución debe seguir exigiendo coincidencia exacta por pareja (como `ANDROID-DUP-PSX-1`) y quedarse con la copia de nombre canónico / con logros RA | `sync/chd_header.py` (nuevo), `sync/adb_transport.py`, `retroachievements/ra_disc_hash_cache.py`, `web/builders/duplicates.py`, `services/ra_duplicates_service.py`, `web/handlers/scan.py`, `static/js/tabs/review_copies.js` | ✅ 2026-10-21 (rama `feature/dup-chd-rawsha1`) — `AdbTransport.chd_raw_sha1()` lee 124 bytes por ADB; el escaneo ADB (`_do_adb_scan`) rellena `.rommgr/ra_cache/chd_raw_sha1.json` (solo ficheros nuevos/cambiados, clave ruta+tamaño); el constructor de duplicados enlaza los `.chd` PSX con el mismo `rawsha1` con la razón nueva `chd_raw` ("Mismo disco (CHD idéntico)"); `verify_group_by_disc_hash` acepta sin descargar los candidatos con el mismo `rawsha1` que el CHD a conservar (un `rawsha1` distinto nunca rechaza ni acepta: sigue el camino de hash RA). **Probado con datos reales (solo lectura, copia de `library_android.db` + ADB)**: 340 cabeceras en 17 s; **64 grupos nuevos `chd_raw`** (58 solo `chd_raw`, 6 con `crossfmt`), 71 archivos sobrantes; verificación rápida de los pares `.chd`↔recomendado: **65 seguros, 0 sin verificar**, sin `chdman` ni descargas. Tests: `tests/test_chd_raw_sha1.py` (nuevo), +2 en `test_builders_duplicates.py`, +3 en `test_ra_duplicates_service.py`; suite 1573 passed. **No se ha aplicado nada** en la consola |
| DUP-CHD-RAW-1b | Aplicar los 53 grupos verificados (≈20,57 GB) tras backup de `library_android.db`, dry-run primero y OK explícito; decidir qué nombre conservar (el de DuckStation/Redump) y no tocar los 6 discos distintos | consola real | 🟡 **dry-run hecho 2026-10-21, NO aplicar todavía** (solo informe, sin tocar la consola; BD de 2026-10-02 sin rescan): 64 grupos `chd_raw`, **65 descartes verificados por `rawsha1` = 17,59 GB** + 6 de otro formato (`.bin`, requieren hash RA/`HW-1`). **Problema de política**: la recomendación existente (región preferida Spain/Europe, tier RA) a menudo conserva el nombre *peor* — en 23 grupos el recomendado está dentro de una subcarpeta con nombre de otra región (`Spider-Man (Spain)/Spider-Man (USA).chd` frente a `Spider-Man (USA, Europe).chd`) y alguno conserva un nombre erróneo (`Oddworld - Abe's Oddysee (Europe)/… (USA) (Demo) (Windows).chd` frente a `Oddworld - Abe's Oddysee (USA).chd`). Como los nombres de estos CHD son poco fiables, antes de aplicar hay que decidir qué copia se conserva (p. ej. la de la raíz de `psx/` sin etiquetas Demo/Proto/Pirate, o el título que muestra DuckStation) y volver a escanear la consola para actualizar la BD. Informe: `dryrun_1b.csv` (conservar;descartar;bytes;estado), regenerable con el script de validación |
| DUP-CHD-RAW-1c | Revisar las carpetas-conjunto con nombre de otra región y las pistas sueltas con nombres ajenos (punto 6) | `file_renamer.py::move_disc_set_to_subfolder` | ⬜ |
| DUP-CHD-KEEP-1 | Política de qué copia conservar en grupos `chd_raw` (decisión del usuario 2026-10-21, opción 1): sin etiqueta Demo/Proto/Pirate/Beta/Sample/Unl/Bootleg y, entre esas, la más cercana a la raíz de la plataforma; la región ya no decide en estos grupos | `web/builders/duplicates.py` (`_review_entry_sort_key(prefer_clean_root=…)`, `_has_unofficial_dump_tag`, `_folder_depth`) | ✅ 2026-10-21 (rama `feature/dup-chd-keep-policy`, apilada sobre `feature/dup-chd-rawsha1`). Con datos reales (dry-run): las 64 copias a conservar quedan en la raíz de `psx/`, ninguna con etiqueta no oficial (antes 23 estaban en subcarpetas con otra región). `test_builders_duplicates.py` 62 passed |
| DUP-CHD-RAW-1d | **Replicar en la máquina de Ruben** (decisión del usuario 2026-10-21: lo que cambie la estructura de carpetas/duplicados hay que hacerlo en *ambas* máquinas, rammu y Ruben). El código va en el repo, pero los *datos* son por máquina: tras fusionar los PR, en la máquina de Ruben hacer `git pull`, lanzar el escaneo ADB de su consola (rellena su `chd_raw_sha1.json` y su `library_android.db`), dry-run, backup y aplicar con su OK. En su biblioteca PC (`F:\Juegos Retro`) el paso de hash RA ya ve las rutas locales, pero necesita `chdman`: **idea no implementada** — usar `read_chd_raw_sha1` también para `.chd` locales (instantáneo, sin `chdman`). El fork de DuckStation (`EMU-RETURN-DUCK-1`) solo existe en la consola de rammu | `Tareas/backlog/pilar1-limpieza.md`, `config.py` | ⏸ **aplazada a largo plazo (2026-10-21)**: la máquina de Ruben está en otra ciudad y el usuario tardará mucho en ir; mientras tanto se trabaja solo en la máquina de rammu y su Anbernic (RG556). Retomar cuando haya acceso físico a esa máquina |

**Hallazgo colateral real: `SAGE-1` murió con `"database is locked"`**
mientras `zip-route-apply` corría en paralelo (ambos escriben en
`library_pc.db` — el pipeline de organizar hace escrituras masivas,
choque de concurrencia SQLite). Progreso real antes de morir: cobertura
de descripciones 27,78%→38,36% (no se perdió, quedó guardado). Relanzado
tras terminar el job pesado, corriendo limpio de nuevo. **Candidato a
backlog aparte** si se repite: serializar jobs de escritura pesada
(`scrape`/`apply`/`inbox`) en vez de permitirlos en paralelo, o que
`_do_scrape` reintente en vez de abortar ante `sqlite3.OperationalError:
database is locked`.

**Re-escaneo 2026-10-04 (roadmap 33, solo lectura — nada borrado ni movido)**: junk-scan completo sobre `E:\RetroVault\ROMS` (misma lógica que `_full_junk_scan`, índices de catálogo + BD): **17.126 archivos / 31,70 GB**: `safe_delete` 16.531 (31,52 GB), `misplaced` 98 (0,12 GB), `review` 497. Dominan `Unknown\` (`roms 1` ~4.450 chips sueltos de romsets, `games` 1.584, `media`/`Imgs` ~8.600 imágenes de otro frontend, `samples` wav) y restos de `inboxbneo_1003_bestset\`. **`NULL-PLATFORM-1` queda obsoleto**: hoy hay solo 340 filas `platform NULL` (13 con `canonical_title`), no 3.642; las 2.900 identificadas ya se organizaron y lo que queda en `Unknown\` es residuo, no ROMs sin colocar.

**Hallazgo grave: la categoría `safe_delete` incluye datos reales que no son basura** (comprobado contra `config.save_extensions`/`PLATFORM_BY_EXTENSION` sobre los 11.653 paths listados de 16.531):
- **Saves**: 9 memcards PSX `.mcd` en `psx\memcards\` (Crash Bandicoot, Capcom vs. SNK…), 7 memcards PS2 `.ps2` (60 MB, `memcards\Mcd001.ps2`…), 7 `.dsv` de DraStic en `_backup_android_cleanup_20260927\DraStic_publicdataackup\` (Pokémon Oro HeartGold, Mario Kart DS…). **Pilar 3 — riesgo de pérdida de progreso** si se aplica `safe_delete` tal cual.
- **ROMs válidas**: 28 `.sg` (Master System/SG-1000, p. ej. `Bloktris (World) (v1.03).sg`), 5 `.unf` + 1 `.unif` (NES UNIF), 2 `.int` (Intellivision).

**Causa raíz**: `_build_junk_scan` (`web/builders/folders.py:156`) decide "es juego" con una lista fija `_GAMING_EXTS` (`:186-~255`) que no incluye `.mcd`, `.ps2`, `.dsv`, `.sg`, `.unf`, `.unif`, `.int`…; todo lo que no esté ahí ni en `_CONFIG_EXTS` cae en `Otros (<ext>)` → `safe_delete` (`:397`). Además solo se excluyen del recorrido `saves`, `bios`, `android` y `_descartados` (`:327-333`): `memcards\` y los `_backup_*` no, así que sus saves se evalúan como cualquier archivo. La lista no se alimenta de `PLATFORM_BY_EXTENSION` ni de `save_extensions`, que ya conocen estas extensiones. `junk-delete` mueve a `_descartados/` (recuperable), pero el scan marca como "seguro" algo que no lo es.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| JUNK-SAFE-1 | Que `_build_junk_scan` derive "es juego/save" de `PLATFORM_BY_EXTENSION` + `config.save_extensions`/`state_extensions` (fuente única) en vez de `_GAMING_EXTS` fija, y excluya `memcards\` y carpetas `_backup_*` del recorrido; test con `.mcd`/`.ps2`/`.dsv`/`.sg`/`.unf`/`.int` que no deben salir como `safe_delete` | `web/builders/folders.py:186-333,393-397` | ✅ 2026-10-04 (rama `fix/junk-safe-1-saves-roms`): `_data_exts()` (`PLATFORM_BY_EXTENSION` + `save_extensions`/`state_extensions` de la config) en vez de depender solo de `_GAMING_EXTS`, y carpetas `_backup*` excluidas del recorrido; test `test_junk_safe_1_saves_y_roms_validas_no_son_basura`. Re-escaneo real: 17.126 → 16.867 archivos y **0 saves/ROMs** en `safe_delete` (lista completa). Efecto colateral aceptado: `.u1` (chips de romset) cuenta como ROM de N64DD y ya no sale como basura. **`JUNK-SCAN-RUBEN-1b` desbloqueada** (dry-run y OK por bucket) |
| JUNK-SCAN-RUBEN-1b | Aplicar `safe_delete` por buckets (con dry-run y OK por bucket) **solo después de `JUNK-SAFE-1`** y re-medir | — | ⬜ desbloqueada (JUNK-SAFE-1 ✅ 2026-10-04); dry-run Día74 (16.276 piezas/31,3 GB) mostró que un tercio no tiene ZIP → antes `JUNK-ZIP-PIEZA-1`; aplicar solo con OK por bucket |
| JUNK-ZIP-PIEZA-1 | Las piezas sueltas "Otros (.ext)" solo siguen en `safe_delete` si el ZIP de su set arcade existe en la carpeta (índice `(rom, tamaño)→sets` del DAT); sin ZIP → "Chips arcade sin su ZIP" (review), sin match → "Sin identificar" (review). Dry-run real: safe_delete 16.276→11.042 (18 GB), 4.683 piezas (12 GB) sin ZIP, 551 sin identificar | `web/builders/folders.py` (`_build_junk_scan`, `_chip_sets`), `handlers/esde/maintenance.py` (`_chip_index`) | ✅ 2026-10-09 (rama `fix/junk-scan-zip-por-pieza`; test `test_junk_scan_chip_zip.py`) |
| JUNK-ZIP-NGPC-1 | `Unknown\mslug2nd.zip` y `mslug2ndd.zip` (Metal Slug 2nd Mission, **Neo Geo Pocket Color**, no arcade) caen en "ZIPs no-ROM": una sola entrada `.bin` cuyo CRC no está en el índice No-Intro y `.bin` no mapea a plataforma. Es `review`, no se borra, pero tampoco se enruta. Revisar si el dump está en el DAT con otro CRC | `web/builders/folders.py` (`_single_rom_platform`, `_build_junk_scan`) | ✅ 2026-10-09 (PR #441): causa raíz = `_platform_from_dat_name` no reconocía "NeoGeo Pocket" sin espacio, el DAT `SNK - NeoGeo Pocket Color (2024…).dat` no se cargaba (+17 CRC, entre ellos el demo `8B1647D4`). `mslug2nd.zip` (CRC `AC549144`) es otro volcado que no está en ningún DAT (el DAT lista `18E692A5`): se queda en review, no se fuerza el CRC |
| INBOX-PART-TORRENT | Ficheros sueltos del Inbox que el pipeline nunca consume (hallazgo Día74: `Breath of Fire III….zip.part`, `fbneo_1003_bestset_archive.torrent`, `mame_20240311_archive.torrent`). `_inbox_pending()` excluía `.part` pero no `.torrent`; solo la firma evitaba el relanzado en bucle | `web/daemons.py:186-209` | ✅ 2026-10-09 (rama `fix/inbox-part-torrent`): decisión del usuario = ignorar; `_INBOX_IGNORED_EXTS` (`.part`, `.torrent`) en `_inbox_pending()`, test actualizado |
| INBOX-ROMHACK-DISCARD-1 | Hallazgo Día74 (lote de 92 ZIPs `misplaced` pasados por `_run_inbox_pipeline`): los romhacks/homebrew sin match en catálogo (`.nes`/`.sg`/`.ngp` de ZIP-ROUTE-3) acaban en `_descartados/` en vez de en su plataforma. Los 22 que había ya existían en `nes/`, `mastersystem/` y `ngpc/` (duplicados), pero la regla es dudosa para romhacks nuevos. Investigar qué rama del pipeline los descarta | `web/inbox_pipeline.py` | ⬜ |
| ARCADE-CONFLICT-4 | `champglf`, `champtns`, `gpworlda`, `safarircj`: mismo nombre y tamaño que los de `unknown\` pero distinto CRC (otra versión del set). Copias nuevas en `inbox\_lote_dia74\_descartados\`; comparar con el DAT y decidir cuál queda. Además `Soukoban (Japan) (En).bin` (plataforma sin determinar) en el mismo sitio | — | ✅ 2026-10-09: sin objeto, se purgó la papelera completa (los de `unknown\` quedan como buenos) |

---

### HEALTH-CHECK-RUBEN-1 — El Health Check semanal marcó 2 "corrupted" que en realidad son falsos positivos: el `sha1` guardado en BD es el de otra variante regional, el archivo real está bien (hallazgo 2026-09-28, máquina "Ruben", `F:\Juegos Retro`)
> **Estado (revisado 2026-10-20):** ⏳ abierta — posible fix futuro, sin implementar

Origen: el daemon de Health Check (semanal, `web/daemons.py`) ya estaba
corriendo al empezar esta sesión (no lanzado a propósito). Resultado real:
**24.527 OK, 0 missing, 2 "corrupted"**:

- `gbc/Mr. Driller (Japan).gbc` — `stored_sha1=3BFDA5EDB7D1...`, `computed_sha1=B0D725DACEA7...`
- `gbc/Ultimate Fighting Championship (Europe).gbc` — `stored_sha1=8A02015E399A...`, `computed_sha1=5036626B9723...`

`check_library_health()` (`utils/health_checker.py:201-223`) etiqueta
`"corrupted"` cualquier fila donde `computed_sha1 != stored_sha1` — no
distingue "el archivo está dañado de verdad" de "la BD tiene guardado el
hash equivocado". Investigado a fondo (solo lectura, sin tocar nada):

1. **El contenido real de ambos archivos está perfecto**, no corrupto. La
   cabecera interna del cartucho de `Mr. Driller (Japan).gbc` dice
   literalmente `"MR. DRILLERBMDJ"` (coincide con su propio nombre de
   archivo) y su `sha1` **real** (`B0D725DACEA7...`) coincide EXACTO con la
   entrada `"Mr. Driller (Japan)"` del DAT No-Intro real
   (`.rommgr/catalogs/nointro/Nintendo - Game Boy Color.dat`, cargado con
   `catalog_loader.load_dat_file()`, 1.427 entradas). Mismo patrón exacto
   para `Ultimate Fighting Championship (Europe).gbc` — su `sha1` real
   coincide con la entrada `"Ultimate Fighting Championship (Europe)"`.
2. **El `sha1` guardado en `games.sha1` para ambas filas no es basura
   aleatoria — es el `sha1` real de la variante "(USA)" del mismo juego**:
   `3BFDA5EDB7D1...` = `"Mr. Driller (USA)"` en el DAT; `8A02015E399A...` =
   `"Ultimate Fighting Championship (USA)"` en el DAT. Confirmado cruzando
   las 5 entradas del DAT para ambos títulos (JPN/USA/EUR) — no es una
   coincidencia, apunta a un bug real de asignación cruzada entre variantes
   regionales del mismo juego, no a corrupción de disco.
3. `file_operations` (BD) **no tiene ninguna fila para ninguno de los dos
   `game_id`** (43070, 43556) — lo que pasó no fue a través del pipeline de
   rename/organize de la app (que sí registra cada operación,
   `INBOX-ATOMIC-1`/regla del proyecto "Toda operación sobre archivos se
   registra en SQLite"). Causa raíz real **sin determinar** — candidatos sin
   confirmar: un bug de scanner/upsert que cruzó el `sha1` de dos filas
   cercanas al escribir, o un import/migración de datos anterior a esta
   sesión que ya traía el dato mal.
4. `canonical_title`/`match_confidence` son `NULL` en ambas filas pese a que
   el `sha1` guardado SÍ tiene match en el catálogo (la entrada "(USA)") —
   el matcher nunca llegó a correr sobre estas dos filas con ese hash, otra
   pista de que el dato llegó así desde fuera del flujo normal de
   scan→match.

**Conclusión**: no hay corrupción real ni riesgo de pérdida de datos — son
2 falsos positivos del Health Check. Sin arreglar a propósito (regla del
proyecto: documentar con archivo:línea, no implementar en la misma sesión
salvo petición explícita). Posible fix futuro de dos partes independientes:
(a) re-escanear/re-hashear estas 2 filas para que el `sha1` guardado
vuelva a ser el real (arregla el síntoma, dispara el match automático) y
(b) investigar si el bug de asignación cruzada es sistémico (otras filas
con el mismo patrón silenciosas porque su "sha1 equivocado" no dispara
"corrupted" por casualidad) — candidato a un chequeo tipo "¿el `sha1`
guardado coincide con OTRA entrada del catálogo bajo un título distinto al
propio `canonical_title`/nombre de archivo?" en vez de solo comparar
`computed == stored`.

---

