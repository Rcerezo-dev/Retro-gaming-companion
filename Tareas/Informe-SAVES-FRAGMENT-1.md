# SAVES-FRAGMENT-1 — Informe de fragmentación de saves (RG556)

**Fecha:** 2026-08-25 · **Dispositivo:** `RG556006101273` · **Alcance:** solo inventario y
diagnóstico. **No se ha movido, borrado ni fusionado ningún archivo.**

Datos crudos completos (424 filas, mtime + tamaño + md5 + ruta):
`Tareas/SAVES-FRAGMENT-1-inventario-rg556.tsv`

---

## 1. Resumen

| Métrica | Valor |
|---|---|
| Archivos bajo `RetroArch/saves` + `RetroArch/states` | 424 (453 MB + 243 MB) |
| Restos de Syncthing / config de Dolphin (excluidos del análisis) | 23 |
| Juegos (grupos) tras normalizar carpeta, sufijo `(N)` y extensión | 330 |
| Grupos con más de una copia | 55 |
| **Divergentes — hay progreso real distinto en cada copia** | **8** |
| Solo una copia con contenido (la otra está en blanco) | 2 |
| Todas las copias en blanco (0xFF) | 3 |
| Idénticos (mismo md5, deduplicar es seguro) | 42 |

**Titular:** el riesgo real está acotado a **8 juegos**. Todo lo demás son copias
idénticas o saves vacíos. Pero uno de esos 8 (Earthbound) demuestra que la regla
"consolidar en el esquema por-plataforma" tal y como está escrita en el backlog
**habría destruido progreso**.

---

## 2. Los tres ejes de fragmentación (no uno, tres)

El backlog solo describe el eje 1. El inventario destapa dos más:

1. **Por-core vs. por-plataforma vs. raíz** — el esperado. `sort_savefiles_by_content_enable`
   on/off: `saves/Snes9x 2010/`, `saves/bsnes2014/` … vs. `saves/snes/` vs. `saves/` a pelo.
2. **Extensión distinta según el core, mismo juego, misma plataforma.** VBA Next y mGBA
   escriben `.srm`; lo que hay en `saves/gba/` son `.sav`. Un agrupado por nombre exacto
   de archivo **no los ve como el mismo juego**. Afecta a 11 de los 13 grupos GBA con copias.
   Tamaños canónicos observados: 32768 / 65536 / 131072 (mGBA, `.sav`) y **139264** (VBA Next,
   = 131072 + 8192 de RTC/cabecera). El md5 nunca coincidirá entre cores aunque el progreso
   sea el mismo — **comparar md5 entre cores distintos no sirve como criterio**.
3. **Mismo juego con dos nombres de ROM.** `Metroid Fusion [E].sav` y
   `Metroid Fusion (Europe) (En,Fr,De,Es,It).sav` conviven con md5 idéntico. Hay ~20 pares así.
   El renombrado canónico No-Intro dejó atrás el save del nombre viejo.

Además, **`states/` no está fragmentado**: solo existe el esquema por-core
(`states/Beetle PSX/` 54, `states/LRPS2/` 13, `states/FCEUmm/` 1). Cero duplicados.
El problema es exclusivo de `saves/`.

---

## 3. Riesgo 1 — DIVERGENTES: decisión tuya, no toco nada

Ordenados por gravedad. `<VACÍO>` = md5 que aparece en ≥3 juegos distintos, verificado
como relleno `0xFF` — es la plantilla que escribe el core al arrancar, no hay progreso.

### 3.1 Earthbound (SNES) — 7 copias, 3 versiones reales ⚠️ el caso grave

```
2025-07-24 01:23   8192  09d957805785  saves/Snes9x/Earthbound (1).srm          ← MÁS RECIENTE
2025-05-20 01:39   8192  9b0ff6ceba59  saves/Snes9x 2005 Plus/Earthbound (1).srm
2025-05-20 01:37   8192  9b0ff6ceba59  saves/Snes9x 2010/Earthbound (1).srm
2025-05-20 01:30   8192  9b0ff6ceba59  saves/Earthbound (1).srm
2025-05-20 01:30   8192  9b0ff6ceba59  saves/bsnes2014/Earthbound (1).srm
2025-05-20 01:10   8192  9b0ff6ceba59  saves/snes/Earthbound.srm
2025-05-20 00:53   8192  55d11bff7568  saves/snes/Earthbound (1).srm
```

Tres puntos importantes:

- La versión **más nueva vive en el esquema por-core** (`saves/Snes9x/`), no en el
  por-plataforma. Consolidar hacia `saves/snes/` copiando lo que ya hay allí, o
  resolviendo por "el que está en la carpeta destino gana", **pisa 2 meses de partida**.
- `saves/snes/` tiene **dos** archivos del mismo juego (`Earthbound.srm` y
  `Earthbound (1).srm`) con contenido distinto — el propio destino ya está fragmentado.
- Todas son de 8192 bytes y del mismo core-family, así que aquí **sí** se pueden comparar
  por md5 y por mtime con confianza.
- `55d11bff7568` coincide con `saves/Unknown/Earthbound (World) (Virtual Console) (New 3DS).srm`
  — la copia más vieja de `snes/` viene de la versión de Virtual Console.

**Recomendación:** conservar `saves/Snes9x/Earthbound (1).srm` como ganador. Necesito tu OK.

### 3.2 Memcards PS2 `Mcd001` — 2 copias, ambas con progreso (→ SAVES-FRAGMENT-2)

```
2025-11-21 23:48  8650752  c229c932d6c1  saves/ps2/Mcd001.ps2
2025-06-29 13:50  8650752  3212c5ca11d2  saves/LRPS2/Mcd001.ps2
```

Una memcard PS2 contiene **varios juegos a la vez**. Elegir una descarta las partidas
de todos los juegos que solo estén en la otra. No es un "quién gana" — hay que abrirlas
y mirar qué guarda cada una antes de decidir. `Mcd002` sí es idéntica en ambas rutas.

### 3.3 GBA — copias de dos cores, formatos incomparables

| Juego | VBA Next (`.srm`) | mGBA / `saves/gba` (`.sav`) |
|---|---|---|
| Castlevania - Harmony of Dissonance (Europe) | 2026-04-03 · 139264 · `9ea5da689b31` | 2025-03-09 · 32768 · `dda3f0717dc6` |
| Castlevania - Harmony Of Dissonance [E] | 2025-08-04 · 139264 · `7d2ab23c0d9c` | 2025-03-09 · 32768 · `dda3f0717dc6` |
| Metroid - Zero Mission [E] | 2025-06-29 · 139264 · `ab744ab11fdd` | 2025-07-08 · 32768 · `f484f414725d` (mGBA) |
| Pokemon Pinball - Ruby & Sapphire (Europe) | 2026-07-25 · 139264 · `296d57313f25` | 2025-03-01 · 32768 · `60049de99afb` |
| Pokemon Pinball RZ [E] | 2025-07-25 · 139264 · `b7f6aeeb19d0` | 2025-03-01 · 32768 · `60049de99afb` |
| Pokémon Rojo fuego [E] | 2025-07-08 · 139264 · `9917037dc9bf` | 2025-06-05 · 65536 · `fcd6bcb56c16` · (mGBA: `<VACÍO>`) |

En todos, la copia de VBA Next es más reciente salvo en Metroid Zero Mission (gana mGBA
por 9 días). Ojo: las dos filas de Castlevania son **el mismo juego con dos nombres de ROM**
(eje 3), y los `.sav` de ambas son el mismo archivo — hay que resolverlas juntas.

**No puedo decidir por ti:** un `.srm` de VBA Next y un `.sav` de mGBA no se comparan por
hash, y el criterio "el más nuevo gana" en GBA es frágil — un core que arranca el juego y
lo cierra reescribe el save con la plantilla y actualiza el mtime sin que haya progreso.
Lo correcto es abrir cada uno en su emulador y mirar la partida. Son 5 juegos.

---

## 4. Riesgo 2 — copias huérfanas de Syncthing con contenido único

Los `.stversions` no son solo basura: hay **versiones que no existen en ninguna otra parte**.

```
2025-07-08 23:21  131072  f7d8aa22c74c  saves/.stversions/mGBA/Metroid - Zero Mission [E].srm
2025-07-08 23:25  139264  1e074aee07d6  saves/.stversions/VBA Next/Sonic Advance 2 [E].srm
2025-03-06 23:42 16006513  1af16bd85006  states/.stversions/LRPS2/.stversions/SLES-52822 (105CC366).01.p2s~...backup
```

- Metroid Zero Mission tiene así **una tercera versión** (mismo minuto que la copia viva de
  mGBA, tamaño distinto: es el archivo que Syncthing apartó al sobrescribir).
- Sonic Advance 2 tiene una copia apartada (`1e074aee`) distinta de la viva (`d9754f004596`),
  del mismo minuto.
- El savestate PS2 apartado es **más grande** que el vivo (16.0 MB vs 14.7 MB) y de fecha
  anterior — dos savestates de sesiones distintas.

**No borrar `.stversions` hasta cerrar el punto 3.** Es la única red de seguridad que queda
de las sobrescrituras que ya ocurrieron.

---

## 5. Riesgo 3 — saves en blanco: se descartan sin pensar

4 md5 son plantillas verificadas (`od` sobre el archivo: relleno `0xFF`, o 0 bytes):

| md5 | Tamaño | Juegos afectados | Origen |
|---|---|---|---|
| `d41d8cd98f00…` | 0 | 14 | archivo vacío (13 en `saves/nds/`) |
| `afefe025db90…` | 139264 | 11 | VBA Next recién arrancado |
| `41d2e2c0c0ed…` | 131072 | 7 | mGBA recién arrancado |
| `84d04c9d6cc8…` | 8192 | 5 | Game Gear recién arrancado |

Un quinto candidato, `0f57c483c0e8…` (131072 B, 3 juegos), resultó **falso positivo**:
empieza por `4d 43` = `"MC"`, la firma de una memcard PSX con datos. Son las tres copias de
la misma partida de Metal Gear Solid bajo tres nombres de ROM distintos (eje 3), todas en
`saves/psx/`, todas idénticas — no afecta a ningún veredicto. **La heurística "mismo hash en
≥3 juegos ⇒ plantilla" no basta por sí sola**: hay que confirmar el contenido antes de
descartar nada (el consolidador debería comprobar relleno uniforme, no solo repetición).

Consecuencias directas:

- **3 grupos donde TODAS las copias están vacías** — Pokemon Edición Rojo Fuego,
  Pokemon Edición Verde Hoja (Spain), Pokémon Verde hoja [E]. Se pueden borrar enteros:
  no hay ninguna partida ahí.
- **2 grupos con un solo ganador obvio** — Megaman Zero 1 [E] (gana `saves/gba/*.sav`) y
  Pokemon Edición Esmeralda (Spain) (gana `saves/VBA Next/*.srm`). La otra copia está vacía.

Un consolidador que solo mire mtime elegiría **la copia vacía** en 3 de estos 5 casos,
porque el core la reescribió después. Detectar la plantilla es obligatorio antes de mover nada.

---

## 6. Riesgo 4 — 42 grupos idénticos: deduplicar es seguro

| Nº grupos | Ubicaciones | Causa |
|---|---|---|
| 15 | `saves/gba/` ↔ `saves/gba/states/` | `savestate_directory` apuntó dentro de `saves/` |
| 11 | `saves/Unknown/` ↔ `saves/mame/` | NVRAM arcade duplicado (→ SAVES-FRAGMENT-3) |
| 10 | `saves/nds/` ↔ `saves/nds/states/` | ídem, savestates melonDS `.ml1` de 19 MB cada uno |
| 2 | `saves/dreamcast/` ↔ `saves/dreamcast/states/` | ídem |
| 1 | `saves/LRPS2/` ↔ `saves/ps2/` | `Mcd002.ps2` (la 001 sí diverge, ver 3.2) |
| 1 | `saves/Unknown/` ↔ `saves/nes/` | Kid Dracula |
| 1 | 10 carpetas distintas | `steam_autocloud.vdf` — **no es un save**, basura de Steam |
| 1 | dentro de `saves/nds/` | mismo juego, dos nombres de ROM |

Espacio recuperable inmediato: los 10 `.ml1` duplicados de `saves/nds/states/` son
**~190 MB**, y las 15 parejas `.sgm` de `saves/gba/states/` otros ~0,5 MB.

**Trampa a evitar:** los duplicados de Kid Dracula tienen mtime **1996-12-24** en
`saves/gb/` y `saves/nes/`, y 2026-03-22 en `saves/Unknown/` — mismo contenido exacto.
El mtime en esta tarjeta no es fiable como fuente de verdad; cuando el md5 coincide, da igual,
pero confirma que **mtime nunca puede ser el único criterio**.

---

## 7. Restos a limpiar (no urgente, no hay riesgo)

- Syncthing: `saves/.stfolder/`, `states/.stfolder/`, `saves/Beetle PSX/.stfolder/`,
  `states/LRPS2/.stfolder/`, y el tombstone `saves/.stfolder.removed-20250708-230136/`
  (ver EMULATOR-COMPAT-6 — ambos apps ya deshabilitados).
- Perfil Dolphin completo anidado: `saves/User/{Config,Cache,Logs}/` (14 archivos de
  configuración y shaders, no son saves) → material de SAVES-FRAGMENT-4.
- `steam_autocloud.vdf` ×10.
- `saves/Citra/…` usa ID de título como ruta, no nombre de juego: el basename colisiona
  siempre (`00000001.metadata` ×3, contenido distinto, son juegos distintos). Cualquier
  consolidador tiene que tratar la **ruta completa** como identidad para Citra, no el nombre.

---

## 8. Qué falta para poder consolidar (SAVES-FRAGMENT-2…5)

Lo que este inventario obliga a añadir al diseño antes de escribir el consolidador:

1. **Detección de plantilla en blanco** antes de comparar mtime (§5), verificando relleno
   uniforme y no solo "hash repetido" — esa heurística sola da falsos positivos (§5, MGS).
   Sin esto se pisa progreso.
2. **La identidad del juego no es el nombre de archivo**: hay que normalizar extensión por
   familia de core y reconciliar nombres de ROM alternativos (§2, ejes 2 y 3).
3. **mtime no es fiable** en esta tarjeta (§6) — usarlo solo como desempate, nunca como criterio único.
4. **Las memcards multi-juego (PS2, GC) no admiten "el más nuevo gana"** (§3.2) — necesitan
   inspección de contenido o quedar fuera del alcance automático.
5. **Citra se indexa por ruta completa**, no por basename (§7).
6. `.stversions` es una fuente de versiones reales, no ruido: leerla antes de borrarla (§4).

---

> **Actualización 2026-08-25:** la mitad preventiva (un emulador fijo por plataforma y el
> esquema de carpetas congelado) está resuelta en `docs/emulador-canonico-rg556.md`
> (SAVES-FRAGMENT-6). Allí está también la regla automática de ganador, y el efecto que
> tiene sobre los 8 grupos divergentes de §3: 5 se resuelven solos, 5 juegos GBA quedan en
> una revisión manual única, y solo Earthbound y `Mcd001.ps2` siguen necesitando decisión.

## 9. Lo que necesito de ti para pasar a la fase de movimiento

- [ ] **Earthbound** (§3.1): ¿confirmo `saves/Snes9x/Earthbound (1).srm` como ganador?
- [ ] **Mcd001.ps2** (§3.2): ¿abrimos las dos memcards para ver qué guarda cada una, o lo dejo
      para SAVES-FRAGMENT-2?
- [ ] **Los 5 juegos GBA** (§3.3): ¿los revisas tú en el emulador, o prefieres una regla
      automática asumiendo el riesgo (p. ej. "gana VBA Next salvo Metroid")?
- [ ] ¿Empiezo por lo seguro (§5 vacíos + §6 idénticos + §7 restos: ~190 MB, cero riesgo)
      dejando los 8 divergentes intactos hasta que decidas?

### Método de reproducción

```
tools/adb.exe -s RG556006101273 shell 'find /storage/emulated/0/RetroArch/saves \
  /storage/emulated/0/RetroArch/states -type f -exec stat -c "%Y|%s|%n" {} +'
tools/adb.exe -s RG556006101273 shell 'find … -type f -exec md5sum {} +'
```
(en Git Bash: `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'` antes de cada `adb shell`)
