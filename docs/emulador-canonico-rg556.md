# Emulador canónico por plataforma — RG556

Política para que **cada consola se abra siempre con el mismo emulador** y el save de
cada juego viva **siempre en la misma ruta**. Es la mitad preventiva de SAVES-FRAGMENT-1:
sin esto, cualquier consolidación se vuelve a fragmentar en un mes.

Complementa `docs/emulator-compat.md` (que cubre la compatibilidad PC ↔ Android).
Aquí se decide, de entre los emuladores instalados en la RG556, **cuál gana**.

---

## 1. La regla, y la parte que no es configurable

> **Un emulador por plataforma + una ruta de saves fija + una consolidación única
> que deja el save ganador en esa ruta.**

Hay que ser claro con la segunda mitad de la pregunta: **ningún launcher ni emulador
sabe "tirar hacia el save más reciente"**. Ni Daijishō ni RetroArch ni DuckStation
eligen entre copias — leen una ruta calculada y cargan lo que haya allí. No existe
ese ajuste en ninguno de los tres.

Lo que sí se consigue, y es equivalente en la práctica:

1. **Fijar el emulador** ⇒ la ruta de save deja de depender de con qué core arrancaste hoy.
2. **Fijar el esquema de carpetas de RetroArch** ⇒ la ruta deja de depender de qué ajuste
   estaba activo ese día.
3. **Consolidar una vez** dejando el save ganador en esa ruta.

A partir de ahí "el más reciente" y "el que hay en la ruta" son el mismo archivo
**por construcción**, porque solo un emulador escribe allí. La regla automática es
esa consolidación (§5), no un ajuste del launcher.

---

## 2. Evidencia: qué usa realmente esta consola

Datos reales del dispositivo (`dumpsys usagestats`, 2026-08-25), no suposiciones.
Se cita el bucket acumulado mayor de cada app:

| App | Tiempo de uso | Lanzamientos | Último uso |
|---|---|---|---|
| DuckStation | **68 h 30 m** | 221 | 2026-08-24 |
| RetroArch (`com.retroarch`) | **19 h 28 m** | 174 | 2026-08-24 |
| melonDS (`me.magnum.melonds`) | **7 h 38 m** | 52 | 2026-08-25 |
| Daijishō | 3 h 46 m | 301 | 2026-08-25 |
| Flycast standalone | 2 h 40 m | 5 | 2026-08-14 |
| AetherSX2 | 36 m | 7 | 2026-08-13 |
| Redream | 4 m | 2 | 2026-08-14 |
| Dolphin (`dolphinemu`) | 4 m | 2 | 2026-08-14 |
| RetroArch AArch64 (`com.retroarch.aarch64`) | **2 m** | 18 | 2026-08-14 |
| Dolphin MMJR | 18 s | 7 | 2026-08-14 |
| Citra standalone | 5 s | 1 | 2026-05-08 |
| DraStic | 0 s | 1 | 2026-08-23 |

Tres cosas saltan a la vista:

- **Hay dos RetroArch instalados** (`com.retroarch` y `com.retroarch.aarch64`), ambos
  `arm64-v8a`, versiones 1.21.0 y 1.20.0. Cada uno tiene **su propio `retroarch.cfg` y su
  propio juego de cores**, así que son dos fuentes de fragmentación independientes.
  El que se usa es `com.retroarch` (19 h contra 2 min). → **desinstalar o ignorar el AArch64,
  y asegurarse de que Daijishō apunta a `com.retroarch`.**
- **PSX se juega en DuckStation standalone**, no en RetroArch. Sin embargo `saves/psx/`
  contiene memcards `.srm` del core Beetle PSX. Eso es fragmentación PSX que no aparecía
  en el informe SAVES-FRAGMENT-1 porque los saves de DuckStation viven fuera de `saves/`.
- Citra, DraStic, MMJR, Redream y Dolphin MMJR son ruido: instalados, nunca usados.
  DraStic y Redream se pueden desinstalar sin pensarlo.

Cores que han llegado a escribir configuración en `RetroArch/config/`: Citra, FB Alpha 2012
CPS-3, FCEUmm, Flycast, Genesis Plus GX, Genesis Plus GX Wide, Geolith, MAME 2003 (0.78),
NXEngine, PCSX-ReARMed, PicoDrive, Snes9x, Snes9x 2005 Plus, Snes9x 2010, VBA Next,
dolphin-emu, mGBA. Hardware: Unisoc T820 (1×A76 2.7 + 3×A76 2.3 + 4×A55 2.1, Mali-G57,
8 GB), Android 13 — cómodo hasta Dreamcast/PSP/Saturn, justo en PS2 y GameCube.

---

## 3. Tabla canónica

`RA` = core dentro de RetroArch (`com.retroarch`). `SA` = app standalone.
"Jubilar" = dejar de usarlo; sus saves pasan a histórico, no se borran hasta consolidar.

**RetroAchievements es requisito duro**, así que manda sobre cualquier otra consideración:
si un emulador no soporta RA, no puede ser el canónico por bueno que sea. La columna
**RA** dice si el elegido lo soporta.

| Plataforma | Canónico | Tipo | RA | Save cae en | Jubilar | Por qué |
|---|---|---|---|---|---|---|
| NES / Famicom / FDS | FCEUmm | RA | ✅ | `saves/nes/` | — | Ya es el único; el PC usa FCEUmm ⇒ `.srm` idéntico |
| SNES | **Snes9x** | RA | ✅ | `saves/snes/` | Snes9x 2010, Snes9x 2005 Plus, bsnes2014 | Snes9x es el recomendado para portátiles (bsnes es para PC); además es donde está el Earthbound bueno |
| Game Boy / GBC | Gambatte | RA | ✅ | `saves/gb/`, `saves/gbc/` | — | Mismo core que el PC |
| **GBA** | **mGBA** | RA | ✅ | `saves/gba/` | **VBA Next** | mGBA es el estándar actual; VBA-M/VBA Next ya no tiene ventaja. El PC también usa mGBA ⇒ `.srm` intercambiable |
| Mega Drive / Master System / Game Gear | Genesis Plus GX | RA | ✅ | `saves/megadrive/`, etc. | Genesis Plus GX **Wide**, PicoDrive | "Wide" es una variante de pantalla ancha con save dir propio, sin ganancia aquí |
| PC Engine | Beetle PCE | RA | ✅ | `saves/pcengine/` | — | |
| N64 | Mupen64Plus-Next | RA | ✅ | `saves/n64/` | Mupen64Plus SA | Mejor opción N64 dentro de RetroArch; el standalone no se usa |
| Atari 2600 | Stella 2023 | RA | ✅ | `saves/atari2600/` | — | |
| Arcade (mame, fbneo, cps1/2/3, neogeo) | **FBNeo** | RA | ✅ | ver nota ⚠️ | MAME 2003, FB Alpha 2012 CPS-3 | FBNeo es el core arcade con RA; además un solo core elimina el NVRAM repartido en 5 sitios |
| Dreamcast | **Flycast** | RA | ✅ | `saves/dreamcast/` | Redream (desinstalar), Flycast SA | RA soporta Flycast como core **y** standalone. Redream **no tiene RA** y además usa formato VMU distinto |
| **NDS** | **melonDS Android** | **SA** | ✅ | ver nota ⚠️ | **DraStic** (sin RA, desinstalar) | Único standalone de DS que RA soporta oficialmente. Ya es el que usas (7 h, hoy) |
| **PSX** | **DuckStation** | **SA** | ✅ | ver nota ⚠️ | Beetle PSX, PCSX-ReARMed, SwanStation | 68 h de uso y RA oficial. Igual que en PC ⇒ memcards intercambiables |
| **PS2** | **ARMSX2** ⚠️ | **SA** | ✅ | ver nota ⚠️ | **AetherSX2** (sin RA), **LRPS2** (core) | **Cambio respecto a la v1 de este documento.** RA soporta PCSX2 / ARMSX2 / XBSX2 — AetherSX2 y NetherSX2 **no están en la lista**. ARMSX2 es el port Android mantenido con RA. **No está instalado** |
| **PSP** | PPSSPP | SA | ⚠️ | `/storage/emulated/0/PSP/SAVEDATA/` | core PPSSPP | Ruta pública, sincroniza sin ADB. **Tu build es la 1.11.3 (2021), anterior al soporte RA — hay que actualizarla** |
| **GameCube / Wii** | **Dolphin standalone** | **SA** | ✅ | `Android/data/org.dolphinemu.dolphinemu/` ❌ | **MMJR** (fork viejo, sin RA), core dolphin-emu | **RA solo existe en Dolphin standalone, no en el core de RetroArch.** Tu build es la **2606a**, por encima del mínimo (2407-68 para GC, 2603a para Wii) ✅. Ver el conflicto de §3.5 |
| 3DS | — | — | ❌ | `saves/Citra/…` | — | **RetroAchievements no soporta 3DS**: no existe esa consola en RA. Citra queda fuera del criterio; decídelo por rendimiento (el T820 va justo) |
| Atari 800 / C64 / ColecoVision / Lynx / PC-FX / N64DD | el core que ya haya | RA | varía | por plataforma | — | Sin duplicados, no hay nada que decidir |

⚠️ **Las cuatro plataformas de standalone no guardan dentro de `RetroArch/saves/`.**
Ahí está SAVES-FRAGMENT-5. Situación actual verificada hoy:

- **melonDS** escribe `.sav` y `.ml1` **junto a las ROMs**, en `RetroArch/nds/`, y además hay
  copias en `saves/nds/` y una suelta en `emulator_saves/me.magnum.melonds/saves/saves/`.
  Es el mismo patrón que el `.nv` de arcade de EMULATOR-COMPAT-5: **una sexta ubicación
  que el scanner de sync no mira**.
- **DuckStation**: 47 savestates en `emulator_saves/com.github.stenzek.duckstation/states/`
  (ruta pública ✅), pero las memcards siguen en su sandbox — `/sdcard/duckstation/` solo
  tiene `bios/` e `inputprofiles/`. Falta aplicar el workaround de `emulator-compat.md`:
  Settings → Memory Cards → Directory → carpeta pública.
- **AetherSX2**: `emulator_saves/xyz.aethersx2.android/saves/Mcd00{1,2}.ps2` — **tercer**
  juego de memcards PS2, además de `saves/ps2/` y `saves/LRPS2/`.
- **Arcade**: el `.nv` vive junto a las ROMs (`RetroArch/mame/`, `cps1/`, `cps2/`).

Fijar el emulador **no** arregla esto por sí solo; hace falta además redirigir cada
standalone a una ruta pública fija (o ampliar las raíces que vigila el sync). Es el
alcance de SAVES-FRAGMENT-5 y EMULATOR-COMPAT-5, no de aquí.

---

## 3.5 RetroAchievements: lo que cambia y lo que choca

### Versiones instaladas hoy (verificado con `dumpsys package`)

| App | Versión | RA |
|---|---|---|
| RetroArch | 1.21.0_GIT | ✅ (RA nativo, un login para todos los cores) |
| DuckStation | 0.1-8969 | ✅ |
| melonDS Android | 2.0.1 | ✅ (confirmar que aparece la sección RetroAchievements en Ajustes) |
| Dolphin | **2606a** | ✅ supera el mínimo (2407-68 GC / 2603a Wii) |
| Flycast standalone | V2.1 | ✅ |
| **PPSSPP** | **1.11.3** (2021) | ❌ **anterior al soporte RA — actualizar** |
| **AetherSX2** | v1.5-4248 | ❌ **no está en la lista de RA — sustituir por ARMSX2** |
| Dolphin MMJR | 2.0-16805 | ❌ fork antiguo |
| DraStic / Redream / Citra | — | ❌ |

### El único conflicto real: GameCube/Wii, RA contra sync

- **RA solo funciona en Dolphin standalone**, no en el core `dolphin-emu` de RetroArch.
- Dolphin standalone guarda en `Android/data/org.dolphinemu.dolphinemu/` — scoped storage,
  **inaccesible por ADB sin root** (ya documentado en `emulator-compat.md` y confirmado hoy:
  no hay `su`, no hay gestor de root, `/data/data` da `Permission denied`).

O sea: **en GameCube no se puede tener logros y sync a la vez.** Hay que elegir:

| Opción | Logros | Sync de saves |
|---|---|---|
| Dolphin standalone (2606a) | ✅ | ❌ manual, con la función de export/import de Dolphin |
| Core `dolphin-emu` en RetroArch | ❌ | ✅ los saves caen en la SD |

Dado que RA es requisito duro, **la recomendación es Dolphin standalone** y aceptar que
GameCube/Wii queda fuera del sync automático hasta que se resuelva SAVES-FRAGMENT-4/5.
Es una plataforma con 4 minutos de uso registrado: el coste real es bajo.

### Modo hardcore

El modo hardcore de RA **desactiva los save states** (y los rewinds, cheats y cámara lenta).
Si vas a jugar en hardcore, `states/` deja de importar para esas partidas y todo el peso
del progreso cae en el save de batería — justo el que este documento fija. Refuerza la
política, no la contradice, pero conviene saberlo antes de invertir en sincronizar states.

### Configuración de RA en RetroArch

Settings → Achievements → **Enable Achievements** + usuario y contraseña. Es **un solo
login para todos los cores**, no hay que repetirlo por plataforma. En los standalone
(DuckStation, melonDS, Dolphin, PPSSPP, ARMSX2) hay que loguearse una vez en cada uno.

> Las credenciales las metes tú. No las pidas ni me las pases: quedarían en el historial
> de esta sesión y en los logs de ADB.

### Verificación por core

Los cores de la tabla son los que RA soporta de forma estándar, pero la lista oficial por
core no me la ha dejado consultar la web de RA (403 / redirección infinita). Comprobación
de 5 segundos en el propio dispositivo: carga un juego y abre el menú rápido — si el core
soporta RA aparece la entrada **Achievements**; si no, no aparece.

---

## 4. Ajustes a congelar

### 4.1 En Daijishō (una vez por plataforma)

Platform card → icono del lápiz → **Player Settings** → **Default Player**.
Elegir el de la tabla de §3. Para los standalone, el player es el paquete de la app;
para los cores, la entrada de RetroArch con ese core.

Comprobar además que el player de RetroArch apunta a **`com.retroarch`** y no a
`com.retroarch.aarch64` — si no, Daijishō lanzará el RetroArch que casi no has usado,
con otro `retroarch.cfg` y otros cores, y la fragmentación vuelve por esa puerta.

Si un juego concreto necesita otro emulador, **Custom Player** por juego, no cambiar el
default de la plataforma. Un default que se toca es exactamente lo que produjo este lío.

### 4.2 En RetroArch (`com.retroarch`) — Settings → Saving

| Ajuste | Valor | Clave en `retroarch.cfg` |
|---|---|---|
| Sort Saves Into Folders By Core Name | **OFF** | `sort_savefiles_enable` |
| Sort Saves Into Folders By Content Directory | **ON** | `sort_savefiles_by_content_enable` |
| Write Saves to Content Directory | **OFF** | `savefiles_in_content_dir_enable` |
| Write Save States to Content Directory | **OFF** | `savestates_in_content_dir_enable` |

Resultado: todo save de batería cae en `saves/<carpeta-de-la-ROM>/`, que es
**independiente del core** — el único esquema que sobrevive a cambiar de emulador y el
único que el sync de Retro Vault puede mapear a plataforma de forma predecible.

Los dos "Write … to Content Directory" son los responsables de que el `.nv` de arcade
acabe junto a las ROMs (EMULATOR-COMPAT-5). Apagarlos corta la hemorragia; los archivos
que ya están allí siguen ahí hasta que se consoliden.

**Lo que NO hay que tocar: los dos ajustes equivalentes de save states.**
`states/` **no está fragmentado** — solo existe el esquema por-core
(`states/Beetle PSX/` 54, `states/LRPS2/` 13, `states/FCEUmm/` 1) y cero duplicados.
Cambiarlo obligaría a migrar 68 archivos a cambio de nada: un savestate es específico
del core *y de su versión*, así que en cuanto fijes un core por plataforma la carpeta
por-core ya es estable. Se deja como está.

> ✅ **Sí se automatiza por ADB — corrección de la v1 de este documento.**
> El `retroarch.cfg` de Android **no** está en `/data/data/`: vive en
> `/storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg`, que el shell de ADB
> sí puede leer y escribir (pertenece al grupo `ext_data_rw`, y el archivo es `rw` de grupo).
> La v1 afirmaba lo contrario porque el `find` de comprobación llevaba `-maxdepth 4` y el
> archivo está a profundidad 5. Los nombres de clave reales tampoco eran los que documenté:
> son `savefiles_in_content_dir` y `savestates_in_content_dir`, sin el sufijo `_enable`.
>
> Método seguro para escribirlo (preserva propietario y permisos, que `adb push` directo no):
> ```
> adb -s RG556006101273 shell am force-stop com.retroarch      # si no, lo reescribe al salir
> adb -s RG556006101273 push nuevo.cfg /storage/emulated/0/_ra.cfg
> adb -s RG556006101273 shell 'cp /storage/emulated/0/_ra.cfg \
>     /storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg && rm /storage/emulated/0/_ra.cfg'
> ```
>
> ⚠️ El `retroarch.cfg` contiene `cheevos_token` y `cheevos_username` **en texto plano**.
> Cuidado con dónde acaban las copias de seguridad de ese archivo.

La config de Daijishō sí sigue siendo inaccesible (base de datos en `/data/data/`), pero se
puede alimentar por import de platform JSON — ver §7.

---

## 5. La regla automática de consolidación

Esta sí es código, y es la que responde a "que tire hacia el save más reciente".
Se aplica **por grupo de copias del mismo juego**:

1. **Descartar plantillas.** Archivo de 0 bytes, o relleno uniforme (`0xFF` / `0x00`).
   Verificar el contenido, no basta con "este md5 se repite en varios juegos" — esa
   heurística sola dio un falso positivo con una memcard de MGS (ver informe §5).
2. Si queda **una sola** copia con contenido → gana.
3. Si las que quedan tienen **el mismo md5** → gana cualquiera; el resto es dedupe.
4. Si quedan varias divergentes **del mismo emulador y mismo tamaño** → gana el `mtime`
   más reciente. Backup de las demás antes de mover.
5. Si quedan varias divergentes **de emuladores distintos** (tamaño distinto ⇒ formato
   distinto) → **cuarentena, nunca automático.** Preguntar.
6. **Nunca comparar `mtime` entre formatos distintos.** Un core que arranca el juego y lo
   cierra reescribe el save con la plantilla y actualiza la fecha sin que haya progreso:
   en 3 de los 5 casos observados, "el más nuevo" era el archivo vacío.
7. **Memcards multi-juego** (PS1, PS2, GameCube) → nunca automático, ni siquiera con
   md5 distinto. Una memcard contiene partidas de varios juegos; elegir una descarta
   las de todos los que solo estén en la otra.

El punto clave: **fijar el emulador convierte el caso 5 (no automatizable) en el caso 4
(automatizable)**, porque a partir de la consolidación solo un formato escribe por
plataforma. La regla se vuelve trivial precisamente porque se fijó el emulador antes.

---

## 6. Qué le pasa a los 8 grupos divergentes del informe

Aplicando §3 + §5, la mayoría deja de ser una decisión:

| Grupo | Resuelve la regla | Cómo |
|---|---|---|
| Megaman Zero 1, Pokemon Esmeralda (Spain) | ✅ auto | La otra copia es plantilla (regla 1) |
| Pokemon Rojo Fuego, Verde Hoja (Spain), Verde hoja [E] | ✅ auto | **Las dos** copias son plantilla: no hay partida, se borra el grupo entero |
| Castlevania HoD (×2 nombres), Metroid Zero Mission, Pokemon Pinball (×2 nombres), Pokémon Rojo fuego [E] | ⚠️ manual **una vez** | Al fijar mGBA hay que abrir la copia de VBA Next y ver si tiene progreso que valga la pena antes de jubilarla. 5 juegos, una tarde |
| **Earthbound** | ⚠️ tu decisión | Al fijar Snes9x, la copia de `saves/Snes9x/` (2025-07-24) es la canónica y las de 2010 / 2005 Plus / bsnes2014 se jubilan. Coincide con la recomendación del informe |
| **Mcd001.ps2** | ❌ nunca auto | Regla 7. Y hay **tres** juegos de memcards, no dos (`saves/ps2/`, `saves/LRPS2/`, `emulator_saves/xyz.aethersx2.android/saves/`). Al fijar AetherSX2, la más reciente (`saves/ps2/`, 2025-11-21, del core) hay que **importarla** a AetherSX2, no al revés |

---

## 6.5 Aplicado en el dispositivo el 2026-08-25

**Backup previo** (regla del proyecto): `saves/` completo, 351 archivos, en
`saves-backup-20260825.tgz` — copia en el dispositivo (`/storage/emulated/0/`) y en PC.
Verificado abriendo el tar y contando los 351. Más `retroarch.cfg.orig` sin tocar.

| Acción | Estado |
|---|---|
| `sort_savefiles_enable` → `false` | ✅ |
| `sort_savefiles_by_content_enable` → `true` | ✅ |
| `savestates_in_content_dir` → `false` | ✅ |
| `savefiles_in_content_dir` (ya estaba en `false`) | — sin cambios |
| Ajustes de savestates por-core | — sin tocar, a propósito (§4.2) |
| ARMSX2 2.6.6.8.4 (`com.armsx2`), APK oficial de GitHub | ✅ instalado |
| PPSSPP 1.11.3 → **1.20.4**, APK oficial de ppsspp.org | ✅ actualizado |
| 23 platform JSON en `/storage/emulated/0/Download/daijisho-platforms/` | ✅ generados, **sin importar** |

**RetroAchievements ya estaba configurado**: `cheevos_enable = true`, sesión iniciada y
**modo hardcore activado** — o sea que los savestates ya estaban desactivados en RetroArch.

### Rescate posterior al cambio de config

Cambiar a por-plataforma dejó **47 saves fuera del alcance de RetroArch** (vivían en carpetas
de core sin equivalente por-plataforma), entre ellos **41 de VBA Next con partidas del
15-16 de agosto**. Se copiaron 45 a su carpeta por-plataforma — copia, no movimiento, y con
guarda de "no sobrescribir si el destino existe": 0 sobrescrituras. Los 2 restantes:

- `Metroid - Zero Mission [E]` — mGBA y VBA Next competían por el mismo destino con formatos
  distintos (32768 vs 139264). Es la regla 5 de §5 funcionando: excluido, decisión pendiente.
- `Sonic & Knuckles + Sonic The Hedgehog 3` — falló por el `&` del nombre y porque
  `saves/megadrive/` no existía todavía. Repetido a mano: ✅.

## 6.6 Dos hallazgos que bloquean la consolidación automática

El dedupe "quedarse solo el más reciente" se preparó, se hizo dry-run sobre 96 grupos /
102 archivos… y **se detuvo sin ejecutar**, por dos motivos descubiertos en la comprobación:

### a) Hay cinco árboles de saves, no dos

El informe SAVES-FRAGMENT-1 inventarió `RetroArch/saves` y `RetroArch/states`. Faltaban:

1. `/storage/521D-04EA/` — **microSD donde viven realmente las ROMs** (611 SNES, 1376 NES,
   1115 PSX, 395 GBA, 378 NDS…). Tiene **su propio `saves/`** con 459 archivos.
2. Saves sueltos **junto a las ROMs** en la SD: 41 en `gba/`, 6 en `psx/`, 3 en `snes/`,
   62 en `nds/`, 3 en `dreamcast/`.
3. `RetroArch/<plataforma>/` en memoria interna (`RetroArch/gba/`, `RetroArch/snes/`…) —
   restos de cuando `savefile_directory` apuntaba a `RetroArch/` en vez de a `RetroArch/saves`.

### b) Los nombres de los saves ya no coinciden con los de las ROMs

De los saves que hay en carpetas por-plataforma, **69 no tienen ninguna ROM con ese nombre**.
El caso claro es Earthbound: la ROM es `EarthBound (USA).sfc` (No-Intro) y los tres saves se
llaman `Earthbound.srm`, `Earthbound (1).srm` y `Earthbound (World) (Virtual Console)…`.
RetroArch busca `<nombre-de-la-ROM>.srm`, así que **ninguno de los tres se carga hoy**, ni
antes ni después del cambio de config.

Esto no es fragmentación de carpetas: es un **renombrado canónico de ROMs hecho sin arrastrar
los saves** — justo lo que `rename_rom_with_saves()` existe para evitar. Consolidar carpetas
sin arreglar los nombres no recupera esas partidas.

Por eso el dedupe queda parado: su "ganador" se quedaría en la carpeta del core (p. ej.
`saves/Snes9x/Earthbound (1).srm`), que ya no es donde RetroArch mira, y con un nombre que
tampoco empareja. Mover 102 archivos con esa base habría empeorado la situación.

---

## 6.7 iiSU alineado con el canónico por ADB (2026-09-27)

`emulator_options.json` de iiSU (`Android/media/com.iisulauncher/iiSULauncher/Emuladores/`,
almacenamiento público — **sin root, escribible por ADB**, a diferencia de Daijishō) tenía
4 plataformas apuntando a un emulador distinto del canónico de §3. Corregido directamente
en el dispositivo, con backup previo (`emulator_options.json.bak-2026-09-27`, método
force-stop + push, mismo patrón que retroarch.cfg en §4.2):

| Plataforma | Antes | Ahora | Por qué |
|---|---|---|---|
| `gb` | RetroArch / `Default` / **Ask** (pedía elegir cada vez, sin core fijo) | RetroArch / `Gambatte core` | Gambatte es el canónico (RA ✅); "Ask" no fija nada, vuelve a fragmentar |
| `n64` | M64Plus FZ (Standalone) — **sin RA** | RetroArch / `Mupen64Plus-Next core` | Canónico de §3, y el standalone no soporta logros |
| `dreamcast` | Flycast (Standalone) | RetroArch / `Flycast core` | Alinea con Daijishō (`dreamcast-retroarch-flycast`, confirmado 2026-09-26 en §7) — con el standalone habría dos configs de Flycast y dos posibles rutas de save |
| `ps2` | AetherSX2 (Standalone) — **sin RA** | `ARMSX2 Refresh (Standalone)` | AetherSX2 no está en la lista de RA; ver aviso de nombres abajo |

**Aviso de nombres — hay dos apps distintas llamadas "ARMSX2" en el catálogo de iiSU**
(`emuladores.json`, `supported_emulators.json`): `ARMSX2 (Standalone)` es el paquete
`come.nanodata.armsx2` (**no instalado**), y `ARMSX2 Refresh (Standalone)` es el paquete
`com.armsx2` (**el que se instaló en §6.5**, APK oficial de GitHub). El nombre exacto que
espera `emulator_options.json` es `ARMSX2 Refresh (Standalone)` / commandLabel
`ARMSX2 Refresh` — usar el otro apuntaría a una app que no existe en el dispositivo.

Verificado antes de escribir: `com.armsx2` instalado (`pm list packages`), y los cores
Gambatte/Flycast/Mupen64Plus-Next presentes en `com.retroarch` (carpetas
`RetroArch/config/{Gambatte,Flycast}/` con contenido propio de un core ya ejecutado, y
`RetroArch/downloads/core_backups/mupen64plus_next_gles{2,3}_libretro/` con backup del
actualizador, señal de que el core ya se descargó/actualizó antes).

**No tocado — arcade/psx/gc/wii/nds/psp** ya coincidían con el canónico en `emulator_options.json`.
`gc`/`n3ds` quedan fuera del criterio RA (ver §3.5 y la fila de 3DS en §3).

**Pendiente real que esto no resuelve**: el login de RetroAchievements en cada standalone
(DuckStation, melonDS, Dolphin, PPSSPP, ARMSX2 Refresh) sigue siendo manual — no hay archivo
de config que se pueda rellenar por ADB sin pedir credenciales, y este proyecto no las pide
ni las transporta (§3.5). RetroArch (`com.retroarch`) ya tenía el login hecho desde §6.5, así
que los 4 cores que ahora apuntan a él (Gambatte, Mupen64Plus-Next, Flycast, y ya antes
FBNeo/mGBA/Snes9x/etc.) heredan ese único login sin nada que hacer.

Los **Default Player de Daijishō** siguen bloqueados por ADB (base de datos en
`/data/data/`, sin root — confirmado otra vez hoy: no existe `Android/media/com.magneticchen.daijishou/`
en la SD, a diferencia de iiSU).

**Corrección importante 2026-09-27 — la vía de "exportar una plataforma" de §7 no existe.**
Comprobado a fondo en el dispositivo real (`Ajustes → Biblioteca`: Opciones, sección
Importar completa, Añadir y examinar, `Examinar sistemas → Editar el sistema` de dos
plataformas distintas) y confirmado además contra el repo oficial
(`github.com/TapiocaFox/Daijishou`, wiki `Settings-Page`/`How-to-Use-Daijishō`, README):
**Daijishō es closed-source y solo tiene Importar, nunca Exportar.** El flujo oficial de
la app es "descarga una plataforma pregenerada desde la lista del propio Settings e
impórtala" — no "exporta la tuya y repártela". No hay ningún archivo JSON local que sacar
por ADB ni por la UI. La única vía real para fijar el Default Player de las ~28 plataformas
que faltan sigue siendo manual, plataforma por plataforma, en `Examinar sistemas → (ícono
ojo) → Ajustes del emulador → Emulador por defecto → Guardar` — exactamente el mismo
camino ya usado para confirmar PS1/PS2/Arcade-FBNeo/Dreamcast. Sin atajo por ADB posible
mientras no haya root.

---

## 7. Pendiente

**Bloqueado por falta de root** (verificado 2026-08-25: `su` no existe, no hay Magisk/KernelSU,
`/data/data` da `Permission denied`, el shell corre como `uid=2000(shell)`). Tanto
`retroarch.cfg` como la base de datos de Daijishō viven ahí. Estos hay que hacerlos a mano:

- [x] Login de RetroAchievements en RetroArch (§3.5) — hecho, ver §6.5. **Queda pendiente
  en cada standalone** (DuckStation, melonDS, Dolphin, PPSSPP, ARMSX2 Refresh) — manual,
  sin atajo por ADB (§6.7).
- [x] Fijar los 4 ajustes de Saving en RetroArch (§4.2) — hecho 2026-08-25, ver tabla de §6.5.
- [x] Fijar los Default Player en Daijishō — **completado 2026-09-27, las 32 plataformas
  revisadas, ver §6.8 para el detalle de qué cambió y qué ya estaba bien.**
- [x] **Re-apuntar Daijishō a `SD:/ROMs/<plataforma>`** — **verificado 2026-09-27, ya
      funciona, sin acción necesaria.** Comprobado en vivo: Daijishō muestra "Arcade
      (FinalBurn Neo) · 779 elementos" y el contenido real vive en
      `ROMs/arcade/fbneo/` (867 archivos — la diferencia son elementos sin vincular,
      filtrados por el ajuste "Descartar los elementos sin vincular al sincronizar").
      El problema del 2026-08-25 se resolvió solo en algún punto de las últimas 4 semanas.
- [x] **Configurar iiSU apuntando a `SD:/ROMs/`** — **verificado 2026-09-27, ya funciona.**
      Abierto por ADB, el tile "fbneo" carga 9+ juegos reales sin error. Mismo caso que
      Daijishō: no hace falta tocar nada.
- [ ] **Hallazgo nuevo 2026-09-27, menor**: dentro de `ROMs/` (no en la raíz de la SD) hay
      carpetas sueltas con nombre Title-Case y poco contenido — `Atari 2600/` (6 archivos),
      `Famicom Disk System/` (2), `Game Gear/` (28), `Master System/` (0) — junto a sus
      pares canónicos en minúsculas (`atari2600/`, `fds/`, `gamegear/`, `mastersystem/`,
      con contenido real y activo). Ninguno de los dos launchers parece leer de ahí (las
      cifras que muestran cuadran con las carpetas canónicas), así que es basura inofensiva,
      no un problema de rutas — pendiente de limpieza en una sesión futura si se quiere.
      También hay `ROMs/fbneo/`, `ROMs/mame/`, `ROMs/cps1/2/3/`, `ROMs/neogeo/` **vacíos**
      en el nivel superior de `ROMs/` — el contenido real vive anidado en
      `ROMs/arcade/{mame,fbneo,fba,mame2003-plus}/` (que es donde apuntan ambos launchers).
- [x] Revisar `NGC` vs `gamecube` en la raíz de la SD — **resuelto de rebote, verificado
      2026-09-27**: ninguna de las dos existe ya en la raíz de `/storage/521D-04EA/`
      (`find` completo sin resultados), ni en `E:\RetroVault\ROMS` del PC. Solo queda
      `ROMs/gamecube/` con 21 archivos. Se ve que esto se consolidó en algún punto entre
      el 2026-08-25 (fecha de este hallazgo) y hoy — probablemente en la reorganización de
      `E:\RetroVault\` (commit `NATIVE-SAVE-SYNC-1`) — sin que se marcara aquí. Sin acción
      necesaria, checklist puesto al día.
- [x] Revisar y limpiar las 9 carpetas huérfanas que quedaron en la raíz de la SD sin mover
      — **mismo caso, resuelto de rebote, verificado 2026-09-27**: `Game Boy Advance`,
      `Nintendo DS`, `Atari 2600`, `Master System`, `Famicom Disk System`, `Game Boy`,
      `Game Boy Color`, `Game Gear` — ninguna existe ya en la raíz de la SD (`find
      -maxdepth 1 -type d` sobre `/storage/521D-04EA/` no las lista). Sin acción necesaria.

Acciones sobre apps (requieren tu OK, son instalaciones/desinstalaciones):

- [x] **Actualizar PPSSPP** — hecho 2026-08-25, 1.11.3 → 1.20.4 (ver §6.5).
- [x] **Instalar ARMSX2** — hecho 2026-08-25 (`com.armsx2`, ver §6.5). **Migración completada
  2026-09-27**: el usuario abrió Burnout 3 - Takedown en ARMSX2 y creó un perfil real (save
  `BASLUS-21050`, confirmado con `strings`, no plantilla). Config real de ARMSX2 en
  `/storage/521D-04EA/saves/memcards/` (SD, `bios/`, `cheats/`, `PCSX2-Android.ini` — no en
  `Android/data/`), **sí accesible por ADB**, a diferencia de AetherSX2 (sigue sin poder
  leerse sin root). La copia buena conocida de `SAVES-FRAGMENT-2` resultó tener **13 juegos**,
  no 6 (el número viejo estaba desactualizado) — inspeccionada con la librería `mymcplus`
  (formato real de memcard PS2, instalada aparte en el scratchpad de la sesión, no como
  dependencia del proyecto). Descubierto un conflicto real: esa copia de 13 ya incluía **otro**
  save de Burnout 3, de 2025-05-22/06-08 — mismo juego, save distinto al de hoy. Caso de
  divergencia real entre orígenes (regla 5 de §5: nunca automático) → preguntado al usuario,
  que eligió **quedarse con el de 2025** (el de hoy se archiva). Con esa decisión no hacía
  falta fusionar nada: la copia de 13 juegos (con su Burnout 3 de 2025) se empujó tal cual al
  **slot 1** (`mcd001.ps2`, md5 `c229c932d6c18d87303c3ed5f7aebc8d`, verificado tras copiar).
  El perfil de hoy quedó a salvo en el propio dispositivo como
  `mcd001.ps2.bak-burnout3-perfil-hoy-20260927` junto al slot 1, y el slot 2 se devolvió a su
  plantilla en blanco original (ya no hace falta como staging). Backups adicionales en
  `E:\RetroVault\ROMS\_backup_android_cleanup_20260927\armsx2_memcards\`. La memcard privada
  real de AetherSX2 sigue sin poderse leer sin root — sigue sin confirmarse si el progreso que
  había ahí coincidía con estos 13 juegos o era distinto/más reciente, pero deja de ser
  bloqueante: ARMSX2 ya tiene el estado bueno conocido en su slot activo.
- [x] Desinstalar lo que no se usa ni tiene RA: RetroArch AArch64, DraStic, Redream, Dolphin MMJR
  — **hecho 2026-09-27**. RetroArch AArch64 ya no estaba instalado (se ve que se quitó en
  una sesión anterior sin marcar aquí). DraStic tenía 69 MB de datos públicos con progreso
  real (`/storage/emulated/0/DraStic/backup/`, 7 `.dsv`) — respaldados completos a
  `E:\RetroVault\ROMS\_backup_android_cleanup_20260927\DraStic_publicdata\` antes de
  desinstalar (la carpeta pública no se borra al desinstalar, pero se respaldó igual).
  Redream y Dolphin MMJR no tenían datos públicos que respaldar.
- [x] Decidir GameCube: logros (Dolphin standalone) **o** sync (core de RetroArch) — §3.5.
  **Decidido y aplicado 2026-09-27**: Dolphin standalone (logros), tanto en Daijishō (§6.8)
  como ya reflejaba §3. GameCube/Wii quedan fuera del sync automático a cambio de RA —
  asumido, uso histórico muy bajo (~4 min).

Trabajo de consolidación (pendiente de tus decisiones):

- [ ] Confirmar Earthbound y decidir Mcd001 (informe SAVES-FRAGMENT-1 §9).
- [ ] Revisar los 5 juegos GBA de VBA Next antes de jubilar el core.
- [ ] Redirigir memcards de DuckStation a ruta pública (SAVES-FRAGMENT-5).
- [ ] Implementar §5 en el consolidador (SAVES-FRAGMENT-2…5).

### Vía de automatización de Daijishō — descartada 2026-09-27

Esta sección asumía que se podía exportar una plataforma ya configurada como JSON y generar
el resto de forma masiva. **No es así**: Daijishō es closed-source (confirmado en su propio
`README`) y su UI solo tiene *Importar* (sistema/favoritos/Pegasus) — ninguna opción de
*Exportar*, comprobado a fondo en el dispositivo real. El flujo oficial es descargar
plataformas pregeneradas desde la lista del propio Settings, no exportar la tuya. Sin export
que leer, no hay esquema que reproducir ni forma de generar los 28 archivos restantes de
golpe. Queda solo la vía manual, plataforma por plataforma — ver el aviso en §6.7.

## 6.8 Daijishō — las 32 plataformas revisadas a mano (2026-09-27)

Sin atajo posible (§6.7/§7), se hizo manual: `Examinar sistemas → ícono ojo → Ajustes del
emulador → Emulador por defecto → Guardar`, plataforma por plataforma, comparando el valor
actual contra la tabla canónica de §3. Ya estaban confirmadas de antes (sin tocar): PS1
(DuckStation), PS2 (ARMSX2), Arcade/FBNeo, Dreamcast (RetroArch → Flycast core).

**Cambiadas (apuntaban a un standalone sin RA, a un paquete `RetroArch 64`/`RetroArch 32`
huérfano, o al core equivocado):**

| Plataforma | Antes | Ahora |
|---|---|---|
| Wii | Dolphin mmjr | Dolphin (Official) |
| CP System I | NEO.EMU | RetroArch - fbneo |
| CP System II | NEO.EMU | RetroArch - fbneo |
| CP System III | RetroArch 64 - fbalpha2012_cps3 | RetroArch - fbneo |
| Neo Geo | RetroArch - fbalpha 2012 | RetroArch - fbneo |
| Neo Geo CD | RetroArch 64 - neocd | RetroArch - neocd (mismo core, paquete correcto) |
| Game Boy | com.explusalpha.GbcEmu | RetroArch - gambatte |
| Game Boy Color | com.explusalpha.GbcEmu | RetroArch - gambatte |
| N64 | Mupen64Plus FZ (standalone, sin RA) | RetroArch - mupen64plus_next_gles3 |
| Mega Drive/Genesis | RetroArch 64 - picodrive | RetroArch - genesis_plus_gx |
| Master System | com.explusalpha.MdEmu | RetroArch - genesis_plus_gx |
| Atari 2600 | RetroArch 64 - stella | RetroArch - stella2023 |

**Ya estaban bien, sin tocar:** NES (fceumm), GBA (mgba), NDS (melonDS standalone), GameCube
(Dolphin Official), PSP (PPSSPP), SNES (snes9x).

**Dejadas intactas a propósito:**
- **Arcade (MAME)** — sistema separado de Arcade (FBNeo) en Daijishō, para los sets
  MAME-only que FBNeo no puede cargar (ver `ARCADE-RENAME-BUG-1e`). No se fuerza FBNeo aquí.
- **Nintendo 3DS** — fuera de criterio RA (RetroAchievements no soporta 3DS, §3).
- **3DO, Atari ST, Cave Story Game Engine, ScummVM, Sega Genesis-MSU, Sega Pico,
  Sega Saturn, Sega SG-1000** — "el core que ya haya, sin duplicados" (§3); ninguno tiene
  una fila canónica explícita en la tabla, así que no había nada que decidir.

**Nota técnica del campo "Emulador por defecto"**: no es un desplegable simple — es un
`AutoCompleteTextView`. Tocar el texto abre el teclado y edita el campo directamente (sin
lista); hay que tocar específicamente el icono ▼ de la derecha para que aparezca el listado
de opciones reales del sistema. Escribir texto libre ahí sin elegir de la lista deja un
valor que no coincide con ningún emulador real — cuidado si se automatiza esto en el futuro.

---

*Fuentes de la recomendación de cores: [RetroArch Best Cores by System (2026)](https://retrohandheldhq.com/posts/retroarch-cores/),
[Libretro Core List](https://docs.libretro.com/guides/core-list/),
[melonDS DS core docs](https://docs.libretro.com/library/melonds_ds/),
[Daijishō Wiki — Players and File Extensions](https://github.com/TapiocaFox/Daijishou/wiki/Players-and-File-Extensions),
[Daijisho Setup Guide (Joey's Retro Handhelds)](https://www.joeysretrohandhelds.com/guides/daijisho-setup-guide/),
[RG556 / T820 rendimiento](https://retrogametalk.com/threads/about-ps2-and-gc-emulation-on-t820-anbernic-devices-rg406h-rg476h-rg-cube.17094/).*
*Datos del dispositivo: `dumpsys usagestats`, `pm list packages`, `find` sobre `/storage/emulated/0` — RG556006101273, 2026-08-25.*
*Última actualización: 2026-08-25*
