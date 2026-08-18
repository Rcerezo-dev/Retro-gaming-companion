# Roadmap — Issue #212 (Roadmap: Ideas futuras)

> Roadmap general de lo que queda vivo en la épica #212. Sirve de base para
> trocear en roadmaps por día — no es un plan día a día en sí mismo.
> Estado a 2026-08-17: `GHA-OPT-1` y `STORAGE-MGR` (diseño+código) ya ✅ en
> `Tareas/backlog.md`. `CFG-PORGAME` ya tiene alcance decidido (B0 resuelto
> con el usuario) y está en implementación (CFG-PORGAME-5 arrancado). Frente
> A (validación STORAGE-MGR) **en pausa — sin RG556 a mano**, checklist
> queda listo para cuando haya consola disponible. Quedan 3 frentes: cerrar
> la validación de `STORAGE-MGR` (pausado), implementar `CFG-PORGAME` (en
> curso), e investigar/diseñar `MODS-AUTO` (sin empezar).

---

## Frente A — Cerrar STORAGE-MGR (validación en hardware)

**⏸ En pausa (2026-08-17): sin RG556 a mano.** Retomar cuando haya consola
conectada — no requiere nada más de diseño ni código, solo ejecutar el
checklist.

Lo único que falta del feature ya implementado (PR #213, mergeado
2026-08-17): probarlo contra la RG556 real antes de confiar en el borrado
Android (irreversible, sin papelera — decisión de diseño ya tomada).

Checklist paso a paso listo para ejecutar: `Tareas/Validacion-STORAGE-MGR.md`
(comandos ADB, selectores de UI y criterios de éxito/fallo por cada punto,
generado contra el código real).

| ID | Task | Esfuerzo | Bloqueante |
|----|------|----------|-----------|
| STORAGE-MGR-VAL-1 | Con la RG556 conectada por ADB: comparar PC↔Android en el panel "Comparar" de Colección, verificar que `size_bytes`/totales por plataforma son correctos contra `adb shell du` | XS | Consola conectada |
| STORAGE-MGR-VAL-2 | Borrar 2-3 archivos de prueba solo-PC (verificar que van a `_descartados/`, recuperables) | XS | — |
| STORAGE-MGR-VAL-3 | Borrar 2-3 archivos de prueba solo-Android (verificar aviso de irreversibilidad se muestra, y que `adb shell ls` confirma el borrado real) | XS | Consola conectada |
| STORAGE-MGR-VAL-4 | Selección mixta PC+Android: verificar que el modal distingue las dos notas (papelera vs irreversible) y no las mezcla | XS | Consola conectada |

Esto es un roadmap de 1 sesión corta, no necesita más desglose.

---

## Frente B — CFG-PORGAME (configuraciones por juego)

**Estado:** investigado 2026-08-14, decisiones de alcance cerradas con el
usuario 2026-08-17 (B0). Lista para pasar a diseño (B1) e implementación (B2).

### B0 — Decisiones (RESUELTO 2026-08-17)

Las 3 preguntas abiertas de la investigación 2026-08-14 tenían un supuesto
que no se sostenía: que "configs verificadas" tenía que venir de una fuente
externa. Investigación adicional antes de decidir:

- **No existe una BD/API pública de configs verificadas para la RG556.**
  ROCKNIX/ArkOS sí publican configs curadas en GitHub, pero son para los
  Anbernic **Linux** (RG351/RG552/R36S...) — la RG556 es Android con el
  RetroArch APK normal, no directamente reutilizable.
- **Pero RetroArch ya genera él solo el `.opt` con las claves reales** al
  guardar opciones desde su propio menú (Quick Menu → Options → "Game
  Options File", confirmado contra `docs.libretro.com/guides/overrides/`).
  La app no necesita conocer ni importar claves de antemano — se tratan
  como texto opaco, igual que ya hace con saves/states.

**Decisión con el usuario:** "verificado" = confirmado por el propio usuario
jugando (guarda el override desde el emulador), no importado de un tercero.
El valor de Retro Vault aquí es **detectar, respaldar y sincronizar** lo que
el usuario ya verificó en PC o RG556 — no autor/importar configs. Esto
resuelve B0-1 y B0-2 a la vez (sin fuente externa que integrar, sin claves
que inventar).

**Hallazgo adicional (2026-08-17, aportado por el usuario): PC y RG556 no
tienen la misma potencia — no todo override es transferible entre los dos.**
Contra `docs/architecture/platforms-cores.md`:

- **Mismo core en PC y RG556** (mismo binario, mismos nombres de clave):
  NES (FCEUmm), GB/GBC (Gambatte), GBA (mGBA), NDS (melonDS),
  MegaDrive/SMS/Game Gear (Genesis Plus GX), Saturn (Yaba Sanshiro 2 Pro),
  PSP (PPSSPP), Atari 2600 (Stella 2023). Para estas plataformas, un
  `.opt` sí es *técnicamente* aplicable en el otro lado — pero un ajuste
  pensado para la potencia del PC (resolución interna, filtros, sin límite
  de frameskip) puede no rendir igual en la RG556. **Nunca copiar sin que
  el usuario lo pida explícitamente por juego.**
- **Core distinto por plataforma** (nombre de carpeta `.opt` distinto, ni
  siquiera coincide): SNES (Snes9x 2010 vs Snes9x), N64 (Mupen64Plus
  standalone vs Mupen64Plus-Next), GameCube/Wii (Dolphin standalone vs
  Dolphin-core), PS1 (DuckStation vs PCSX ReARMed), PS2 (PCSX2 vs
  AetherSX2/NetherSX2), Dreamcast (Flycast standalone vs Flycast-core),
  Arcade (MAME vs MAME2003 Plus), Neo Geo (Geolith vs FBNeo). Aquí un
  override de un lado **no tiene ni sentido** en el otro (carpeta de core
  distinta, claves distintas) — no hay riesgo de transplante accidental,
  pero tampoco nada que sincronizar.

**Decisión de diseño consecuente:** el mecanismo de sync de carpeta completa
que ya existe (`sync.ra_config_dir`/`ra_config_remote`, pensado para otra
cosa — respaldo en la nube de la config global) **no se reutiliza para
overrides por juego**. En su lugar: PC y Android son **dos almacenes
independientes por defecto**; la UI muestra qué override existe en cada
lado (con el core y la plataforma visibles) y una acción explícita opcional
"Copiar a [PC|Android]" **solo quando el core coincide**, con aviso de que
el rendimiento puede no trasladarse igual — mismo principio "ante duda, no
sobrescribir" que ya rige el sync de saves. Sin copia automática nunca.

Queda B0-3 (rutas) como único requisito técnico real, y con solución
concreta: **auto-detección**, no configuración manual —

| # | Decisión | Cómo | Estado |
|---|----------|------|--------|
| B0-3a/b | PC: escaneo de `retroarch_path` (APPDATA, C/D/E, Steam vía `libraryfolders.vdf`, RetroBat) — **ya existía** (`_detect_retroarch_install()`, `web/handlers/config.py`, botón "🔍 Detectar" en Settings), no era nuevo. Solo faltaba derivar `ra_config_dir` desde ahí | `<ra_dir>/config`, mismo directorio que ya usa `_handle_retroarch_check` para `cores/` | ✅ 2026-08-17 — campo `ra_config_dir` añadido al detector + auto-relleno en `detectRetroArch()` (config.js). Validado contra instalación real de este PC (Steam, `F:\SteamLibrary\...`). 3 tests nuevos (`tests/test_detect_retroarch.py`) |
| B0-3c | RG556: `/storage/emulated/0/RetroArch/config/` vía ADB — mismo prefijo ya validado en producción para `saves`/`states` de este dispositivo (`config.py` `EMULATOR_MAP`) | Sondeo ADB, igual que `anbernic_root` | ⬜ pendiente — no bloquea CFG-PORGAME-6/7 en PC, hace falta para leer overrides Android |
| B0-3d | Botón "🔍 Detectar automáticamente" en Settings, junto a los campos `retroarch_path`/`ra_config_dir`/Android | Mismo patrón UX ya usado en la app (ADB devices, LAN IP) | ✅ el de PC ya existía y ahora también rellena `ra_config_dir`; falta el de Android (ligado a B0-3c) |

### B1 — Diseño

| ID | Task | Esfuerzo | Estado |
|----|------|----------|--------|
| CFG-PORGAME-1 | Diseño de la auto-detección de rutas (B0-3a..d) — orden de fallback PC, sondeo ADB Android, qué pasa si no se encuentra nada (pedir al usuario, no bloquear) | S | 🟡 mitad PC resuelta al implementar CFG-PORGAME-5 directamente (el fallback ya existía); falta el diseño de la parte Android |
| CFG-PORGAME-2 | Documentar formato final `<rom>.opt` y dónde vive por core/plataforma (base: `docs.libretro.com/guides/overrides/` + estructura ya usada por RetroArch) | XS | ⬜ |
| CFG-PORGAME-3 | Diseño de "copiar a [PC\|Android]" por juego — **no** reutiliza `sync.ra_config_dir`/`ra_config_remote` (eso es respaldo de la config global completa, otro caso de uso); acción explícita, un juego a la vez, deshabilitada si el core no coincide entre PC y RG556, con aviso de rendimiento cuando sí coincide | S | ✅ 2026-08-18 — decidido con el usuario. **Regla de habilitación**: un único criterio, sin consultar la plataforma del ROM — el botón "Copiar" aparece junto a cada core listado en el panel Overrides (mismos enlaces por-core de CFG-PORGAME-7) solo si ese core está en el set de 8 compartidos confirmado contra `docs/architecture/platforms-cores.md` (mismo nombre de carpeta en PC y RG556): **FCEUmm, Gambatte, mGBA, melonDS, Genesis Plus GX, Yaba Sanshiro 2 Pro, PPSSPP, Stella 2023**. Válido para "Solo PC"/"Solo Android" (crear el override por primera vez en el otro lado) y para "En ambos" (sobrescribir explícitamente un lado con el otro, ya cubierto por `core_match`). **Confirmación**: simple con aviso de rendimiento si el destino no tiene override aún; de sobrescritura si ya lo tiene. **Backup antes de sobrescribir**: aplica la regla ya existente del proyecto ("ante duda, no sobrescribir; guardar backup primero", `CLAUDE.md`) — antes de pisar un `.opt` existente en el destino, se guarda `<rom>.opt.bak-<timestamp>` junto al original. **Backend**: reutiliza `read_override()`/`write_override()` de CFG-PORGAME-7 sin I/O nuevo, solo orquestación + backup + comprobación del set de cores compartidos |
| CFG-PORGAME-4 | Diseño de UI: ¿pestaña nueva, o panel dentro de Juegos/Colección como STORAGE-MGR reutilizó "Comparar"? | XS | ✅ 2026-08-18 — decidido con el usuario: panel dentro de **Colección**, mismo patrón que `col-diff-panel`/`btn-col-diff` (toggle en la toolbar, `tab-collection.html`). Se descartó pestaña nueva (sub-feature aún pequeña, solo listado sin editor) y panel en Juegos (sin precedente de panel-toggle ahí). Overrides comparte el mismo eje PC↔Android que el diff de STORAGE-MGR, así que reutiliza también el layout de 3 columnas (Solo PC / Solo Android / En ambos) |

### B2 — Implementación (una vez cerrado B1)

| ID | Task | Esfuerzo | Estado |
|----|------|----------|--------|
| CFG-PORGAME-5 | Backend: auto-detección de rutas | M | ✅ mitad PC (B0-3a/b) — 2026-08-17. ⬜ falta mitad Android (B0-3c/d, sondeo ADB) |
| CFG-PORGAME-6 | Backend: lectura/listado de overrides existentes por juego, en PC y Android por separado (nunca fusionados) — incluye el nombre del core de cada lado para saber si coinciden | M | ✅ 2026-08-18 — `services/retroarch_overrides_service.py::list_overrides()`, una sola función para PC (filesystem) y Android (`AdbTransport.ls_recursive()`, ya existente, reutilizado sin ADB shell nuevo); agrupa por stem de ROM, reporta todos los cores si hay más de uno. Endpoint `GET /api/retroarch-overrides` (`web/handlers/collection.py`, builder puro en `web/builders/overrides.py`) combina ambos lados en `only_pc`/`only_android`/`in_both` (+ `core_match` cuando el nombre de core coincide). UI: panel "⚙️ Overrides" en Colección (CFG-PORGAME-4), mismo patrón toggle que `col-diff-panel` (`toggleOverrides()`/`loadOverrides()` en `collection.js`). 12 tests nuevos (`tests/test_retroarch_overrides_service.py` + `tests/test_overrides_builder.py`, transporte Android simulado — sin RG556 a mano para probarlo en real todavía). Verificado el endpoint contra el servidor real (`rommgr serve` + curl); UI no verificada visualmente en navegador (extensión Chrome de Claude Code no conectada esta sesión) |
| CFG-PORGAME-7 | Backend: editor (lectura/escritura del `.opt`, sin interpretar claves) | M | ✅ 2026-08-18 — `read_override()`/`write_override()` en `retroarch_overrides_service.py` (PC: filesystem directo; Android: `AdbTransport.pull()`/`push(verify=True)` a un fichero temporal, texto opaco de principio a fin). Guarda contra path-traversal en `rom`/`core` (`_safe_component()`). Endpoints `GET`/`POST /api/retroarch-override` (`web/handlers/collection.py`). UI: cada core listado en el panel Overrides es ahora un enlace que abre un editor inline (textarea + Guardar) dentro del mismo panel — cubre también la mitad "editor" de CFG-PORGAME-9, sin el botón de copia (eso sigue en CFG-PORGAME-3/8, sin diseñar). 20 tests nuevos (`tests/test_retroarch_overrides_service.py` + `tests/web/test_retroarch_override_editor.py`, éste último a nivel de router/handler). Verificado extremo a extremo en el servidor real: lectura de un `.opt` real, edición y guardado confirmados contra el archivo en disco vía navegador |
| CFG-PORGAME-8 | Backend: "copiar a [PC\|Android]" por juego (CFG-PORGAME-3) — copia puntual vía ADB o filesystem, valida que el core coincide antes de permitirlo, nunca sobreescribe sin confirmación | M | ✅ 2026-08-18 — `copy_override()` en `retroarch_overrides_service.py`, reutiliza `read_override()`/`write_override()` de CFG-PORGAME-7 sin I/O nuevo. Rechaza cores fuera de `SHARED_CORES` (`ValueError`). Si el destino ya tiene un override, lo respalda como `<rom>.opt.bak-<timestamp>` antes de sobrescribir (`backed_up`/`backup_filename` en la respuesta). Endpoint `POST /api/retroarch-override/copy` (`web/handlers/collection.py`) — valida el core compartido **antes** de exigir ADB, para no pedir conectar el dispositivo en una copia que de todas formas iba a ser inválida (bug encontrado y corregido durante la verificación en vivo: el orden inicial de los checks enmascaraba el mensaje real). 15 tests nuevos (5 en `retroarch_overrides_service.py`, incluye PC↔PC y Android→PC vía ADB simulado; 5 handler-level en `test_retroarch_override_copy.py`) |
| CFG-PORGAME-9 | Frontend: UI del editor + botón de copia puntual con aviso de rendimiento | M | ✅ 2026-08-18 — editor (CFG-PORGAME-7) + botón de copia (⇄) junto a cada core del panel Overrides, visible solo si el core está en `shared_cores` (expuesto por el builder, un único criterio sin duplicar lógica en JS). Confirmación vía `_showConfirm` con aviso de rendimiento y de backup automático si el destino ya tiene override. Verificado en el servidor real: el icono ⇄ solo aparece en cores compartidos (Gambatte sí, Snes9x no), el diálogo de confirmación muestra el texto correcto, y el rechazo por "sin ADB conectado" funciona extremo a extremo |
| CFG-PORGAME-10 | Tests + validación en hardware (RG556) — incluye probar que un override copiado de un core compartido (p. ej. Gambatte) no rompe rendimiento en la consola | S | ⬜ |

---

## Frente C — MODS-AUTO (añadir/instalar mods automáticamente)

**Estado:** idea sin diseñar, alcance grande. Viable en PS1/PS2/N64/GameCube
(formatos más estandarizados); no viable en consolas muy antiguas (sin
ecosistema de mods). No hay nada construido todavía — ni investigación.

### C0 — Investigación por plataforma (antes de diseñar nada)

Recomendación: empezar por **GameCube/Wii vía Dolphin**, es el ecosistema
más maduro y estandarizado (carpetas por Game ID, sin necesidad de una
fuente de datos externa verificada — el propio usuario aporta el mod). Deja
PS2/PS1/N64 para después de validar el patrón con un caso real.

| ID | Task | Esfuerzo | Notas |
|----|------|----------|-------|
| MODS-AUTO-1 | Investigar formato de texture packs + Gecko/AR codes de Dolphin (carpetas `<GameID>/` bajo `Load/Textures` y `Load/GraphicMods`, o `.gct`/`GeckoCodes.txt`) | S | Prioridad — mejor candidato a MVP |
| MODS-AUTO-2 | Investigar `.pnach` de PCSX2 (PS2) — formato de texto, ya vinculado al CRC del juego, bien documentado | S | Segundo candidato |
| MODS-AUTO-3 | Investigar ISO patching genérico (xdelta/IPS/BPS) — aplica a cualquier plataforma con imagen de disco/cartucho, pero requiere el ISO/ROM original intacto como base | M | Transversal, no por plataforma |
| MODS-AUTO-4 | Investigar ecosistema de mods PS1 y N64 — formatos menos estandarizados, prioridad baja | S | Puede quedar fuera de v1 |
| MODS-AUTO-5 | Decisión: ¿v1 cubre solo Dolphin (C0-1), o Dolphin+PCSX2 juntos? | — | Decisión tuya tras C0-1/C0-2 |

### C1 — Diseño (tras C0, con alcance ya decidido)

No desglosado todavía — depende directamente de qué salga de C0. Se
desglosa en el roadmap del día que toque empezar este frente.

---

## Orden recomendado para trocear en días

1. **Frente A** (STORAGE-MGR-VAL-1..4) — 1 sesión corta, cierra trabajo ya
   hecho, requiere la RG556 conectada.
2. **Frente B0** — ✅ resuelto 2026-08-17, no requiere sesión propia.
3. **Frente B1→B2** — listo para trocear en días de implementación
   siguiendo el orden de las tablas (B1 primero, es diseño ligero; B2 es
   donde está el grueso del trabajo, empezando por CFG-PORGAME-5 ya que
   todo lo demás depende de tener las rutas resueltas).
4. **Frente C0** — investigación pura, sin hardware, se puede hacer en
   paralelo a B en cualquier momento.
5. **Frente C1+** — se planifica cuando C0 tenga resultado y tú decidas el
   alcance de v1 (MODS-AUTO-5).
