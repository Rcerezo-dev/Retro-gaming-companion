# Roadmap 20 — Pendientes de hardware, máquina "rammu" / RG556

**Rama:** ninguna por defecto — la mayoría son acciones manuales en el dispositivo o investigación, no cambios de código. Si algún punto requiere código, se corta rama propia en ese momento.
**Base:** `develop`
**Prioridad:** varía por punto (ver cada uno) — agrupados aquí solo por compartir máquina/hardware, no por urgencia común
**Esfuerzo estimado:** variable, mayoría requiere tener la RG556 conectada y al usuario delante de la pantalla
**Riesgo:** bajo en general (son investigaciones o pasos manuales ya acotados), salvo donde se indica

---

## Nota de alcance

Esta máquina ("rammu", consola RG556, rutas `E:\Carpetas anbernic`/
`H:\ROMs`) **sigue activa en paralelo** con la máquina actual ("Ruben",
`F:\Juegos Retro`) — confirmado por el usuario 2026-09-15. No bajar prioridad
a estos puntos por estar en una máquina distinta a la de uso diario reciente.
A diferencia del resto de roadmaps (12-19, orientados a cambios de código en
`develop`), este es una lista de acciones pendientes — no un plan de
implementación único.

---

## `SAVES-FRAGMENT-6` — Emulador canónico por plataforma, aplicar la política

**Prioridad:** 🟠 P2 — es la mitad preventiva de `SAVES-FRAGMENT-1`
(consolidación de saves fragmentados); sin esto, cualquier consolidación
futura se vuelve a fragmentar.

Política completa ya documentada en `docs/emulador-canonico-rg556.md` (tabla
de 15 plataformas con emulador ganador, ruta de save y qué se jubila —
decidida con `dumpsys usagestats` real del dispositivo, priorizando
RetroAchievements en todas las plataformas donde sea posible). **⚠️ No
automatizable por ADB**: `retroarch.cfg` y la config de Daijishō viven en
`/data/data/`, sin root y sin copia pública — hay que aplicarla a mano en los
menús del dispositivo.

**Acción pendiente**: sesión con el usuario delante de la RG556, aplicando
la tabla de `docs/emulador-canonico-rg556.md` menú por menú. Ajustes
RetroArch a congelar: `sort_savefiles_enable=false`,
`sort_savefiles_by_content_enable=true`, `savefiles_in_content_dir_enable=false`,
`savestates_in_content_dir_enable=false` (los de savestates NO se tocan,
`states/` no está fragmentado).

---

## `SAVES-FRAGMENT-9` — Progreso de PS2 en AetherSX2, posible pérdida

**Prioridad:** 🔴 P1 — riesgo real de progreso de partida perdido (Pilar 3,
prioridad absoluta según `CLAUDE.md`).

Hallazgo 2026-08-29: la memcard activa hoy en AetherSX2
(`/storage/521D-04EA/saves/memcards/Mcd001.ps2`) no contiene ningún save de
juego real (0 resultados al buscar patrones de serial PS2), mientras que
copias más antiguas conocidas (`RetroArch/saves/ps2/`, `RetroArch/saves/LRPS2/`)
sí tienen 6 juegos cada una. Hipótesis más probable sin confirmar: el
progreso se perdió alrededor del 2026-08-13 (coincide con el mtime de la
memcard privada real de AetherSX2, ilegible por ADB sin root), probablemente
por crear/formatear una memcard nueva desde el propio menú de la app.

**Acción pendiente** (requiere al usuario delante del dispositivo):
1. Abrir AetherSX2 → Settings → Memory Cards, comprobar qué carpeta usa hoy y
   si hay copias `.bak`/exportadas dentro de la propia app.
2. Si se confirma que el progreso ya no existe en ningún sitio accesible,
   importar manualmente `RetroArch/saves/ps2/Mcd001.ps2` (la copia más
   reciente conocida, 2025-11-21) a AetherSX2 — **backup previo
   obligatorio**, memcard multi-juego = nunca automático (regla 7 de
   `docs/emulador-canonico-rg556.md` §5).

---

## `TRASH-FIX-5b` — Auditoría SHA1 de la purga original, interrumpida

**Prioridad:** 🟡 P3 — no hay riesgo de pérdida activa (la purga ya pasó,
esto es verificar si quedó algo real sin restaurar), pero hay un punto de
retomada conocido con precisión.

Continuación de `TRASH-FIX-5` (restauración de contenido único mal
descartado como "duplicado" en la purga de `_descartados/` de 2026-09-09).
Auditadas casi todas las ~28 plataformas restantes por el mismo método SHA1
(backup vs. activos en dispositivo), interrumpida a petición del usuario
antes de reportar números exactos. Evidencia indirecta de trabajo real y
extenso: espacio libre bajó de 119 GB a 58 GB (~61 GB restaurados).

**Punto de retomada exacto**: dentro de `gamecube` (la última plataforma
procesada), 4 títulos sin comprobar — `Pikmin`, `Soulcalibur II`,
`Super Mario Sunshine`, `Super Smash Bros. Melee` (de los 13 totales de esa
carpeta en el backup `.rommgr\_backup_android_descartados_20260909\gamecube\`).

**Acción pendiente**:
1. Retomar `gamecube` — comprobar por SHA1 (backup vs. dispositivo) esos 4
   títulos y restaurar los que sean contenido único (no duplicados reales).
2. Confirmar con un resumen agregado si el resto de plataformas ya
   auditadas (`3ds, Atari 2600, atari5200, atari7800, atarijaguar, atarilynx,
   atarist, colecovision, Famicom Disk System, fds, Game Gear, intellivision,
   c64, amiga, famicom, n64, megadrive, nes, atari2600, snes, gamegear,
   mastersystem, arcade, gb, gbc, gba, wii, dreamcast, psp`) quedó completo
   o si hay más huecos sin restaurar — el informe original se interrumpió
   antes de generar ese resumen.

---

## `EMULATOR-COMPAT-2` — Round-trip DuckStation PSX, verificación bloqueada

**Prioridad:** 🟡 P3.

Confirmado que la convención de nombre/tamaño de memcard DuckStation
coincide byte a byte entre PC y Android para el mismo juego (2026-09-08).
**No se pudo verificar el contenido ni el "→ load" real**: `adb pull` da
`Permission denied` (scoped storage sobre `Android/data/`) y la pantalla de
la RG556 no se mantiene despierta vía ADB para confirmar visualmente.

**Acción pendiente**: sesión con el usuario delante del dispositivo — cargar
el save real en DuckStation Android y confirmar visualmente que el progreso
coincide con el de PC.

## `EMULATOR-COMPAT-3` — Round-trip PS2 (PCSX2 → AetherSX2/NetherSX2)

**Prioridad:** 🟡 P3. Sin investigar todavía — mismo tipo de test que
`EMULATOR-COMPAT-2`, requiere hardware y al usuario delante de la pantalla.
Nota: con `SAVES-FRAGMENT-6` (RA en todas las plataformas) PS2 pasa de
AetherSX2 a ARMSX2 — probablemente conviene resolver eso primero para no
testear un emulador que va a dejar de ser el canónico.

## `EMULATOR-COMPAT-4` — Round-trip resto de plataformas (GBA, SNES, GBC, NDS...)

**Prioridad:** 🟡 P3. Sin investigar. Actualizar `docs/emulator-compat.md`
con cualquier mismatch de formato encontrado.

---

## Checklist

- [ ] `SAVES-FRAGMENT-6` — política aplicada en el dispositivo (manual)
- [ ] `SAVES-FRAGMENT-9` — memcard AetherSX2 investigada y, si procede, restaurada
- [ ] `TRASH-FIX-5b` — 4 títulos de `gamecube` comprobados + resumen agregado del resto
- [ ] `EMULATOR-COMPAT-2` — round-trip DuckStation PSX verificado visualmente
- [ ] `EMULATOR-COMPAT-3` — round-trip PS2 verificado (tras decidir el emulador canónico)
- [ ] `EMULATOR-COMPAT-4` — resto de plataformas verificadas, matriz actualizada
