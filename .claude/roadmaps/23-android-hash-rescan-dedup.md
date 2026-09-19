# Roadmap 23 — Rescan ADB con hash real + dedup en la Anbernic, en 3 fases

**Rama:** ninguna por defecto — es una operación de datos sobre `library_android.db`
reutilizando código ya existente (`ANDROID-DUP-2`, PR #330, mergeado). Si al
ejecutar aparece un bug real de código, se corta rama propia en ese momento.
**Base:** `develop`
**Prioridad:** 🟠 P2 — mejora real de detección de duplicados (Pilar 1), no es
pérdida de datos ni bloqueante como Pilar 3.
**Esfuerzo estimado:** Fase 1 ~20 min, Fase 2 ~10 min más, Fase 3 varias horas
(requiere trocear, ver nota de riesgo).
**Riesgo:** bajo en Fases 1-2 (alcance medido en real, ver abajo). Medio en
Fase 3 — un intento anterior de escanear TODO de una vez ya falló.

---

## Contexto — por qué en 3 fases, no un único rescan

`ANDROID-DUP-2` (PR #330, 2026-09-19) añadió `AdbTransport.sha1_recursive`/
`md5_recursive` a `_do_adb_scan` (`web/handlers/scan.py:396-455`, ruta `POST
/api/adb-scan`) — el hash se computa **en el propio dispositivo**
(`find ... -exec sha1sum {} +`), solo el dígest cruza USB. Motivación real:
en la RG556 se encontraron duplicados invisibles para toda detección
(`Final Fantasy Tactics [E].gba` / `Pokemon Pinball RZ [E].gba`, mismo
tamaño que su homólogo canónico) porque el escaneo ADB nunca calculaba
`sha1`/`md5` — sin eso, ni la unión por SHA1 ni `canonical_title` (el
matcher tampoco corre sobre `library_android.db`) podían agruparlos.

**Primer intento de rescan completo, fallido (2026-09-19, ver
`ANDROID-DUP-2` en `Tareas/backlog.md`)**: se lanzó `sha1_recursive` sobre
toda la raíz `/storage/521D-04EA/ROMs` (21.608 archivos) en background.
Falló a los **3600s exactos** — el timeout que `_do_adb_scan` pasa por
defecto (`web/handlers/scan.py:453,455`, uno por hash) — sin haber
terminado. `_do_adb_scan` solo escribe en `library_android.db` **al final**,
tras completar sha1 Y md5 (`:457` en adelante) — un timeout a mitad de la
primera pasada no deja ningún dato aprovechable, `scan_run_id=6` se quedó
con `finished_at=NULL` para siempre.

**Medido en real hoy (2026-09-20)**, antes de repetir el mismo error:

- Biblioteca completa: **456 GB, 48.026 archivos**.
- Throughput real de `sha1sum` en el propio dispositivo: **~78 MB/s**
  (medido con `find .../gb -exec sha1sum {} +`: 5,0 GB en 64,3s).
- A ese ritmo, los 456 GB completos (sha1 **+** md5, dos pasadas) tardarían
  **3+ horas** — muy por encima de cualquier timeout razonable en una sola
  llamada, y coincide con por qué el intento anterior no llegó a tiempo.
- Desglose por plataforma (`du -s` real sobre `/storage/521D-04EA/ROMs/*/`):

  | Grupo | Plataformas | Tamaño aprox. | Tiempo hash estimado (sha1+md5, ~78 MB/s) |
  |---|---|---|---|
  | **Cartucho** (Fase 1) | gba 15,7G, megadrive 7,5G, gb 5,0G, nes 3,1G, famicom 2,0G, gbc 1,9G, gamegear 0,84G, snes 0,84G, n64 0,49G | **~37,4 GB** | ~15-20 min |
  | **Arcade** (Fase 2) | arcade | **~33,4 GB** | ~10-15 min más |
  | **Disco** (Fase 3) | psx 215G, ps2 89,5G, nds 20,6G, gamecube 20,5G, dreamcast 16,2G, 3ds 14G, psp 6,2G | **~382 GB** | 3+ horas — requiere trocear por plataforma, no una sola llamada |

  El resto de plataformas (BIOS, atari*, c64, colecovision, intellivision,
  mastersystem, saves…) son residuales, se incluyen gratis en cualquiera de
  las fases que las contenga o se dejan fuera — no mueven la aguja.

- Los duplicados reales que motivaron `ANDROID-DUP-2` (Final Fantasy
  Tactics, Pokemon Pinball) eran **ambos GBA** — es decir, exactamente el
  grupo "Cartucho" de la Fase 1. Empezar ahí prueba el concepto con el
  menor riesgo y el mayor retorno esperado.

---

## Cómo lanzar cada fase

`_do_adb_scan` (`web/handlers/scan.py:396`) acepta `android_path` como
parámetro del body — **ya soporta escanear un subárbol concreto sin tocar
código**, así que cada fase es la misma llamada con una raíz distinta.
Necesita el servidor local corriendo (`rommgr serve` o `scripts\rommgr.cmd
serve`) y la RG556 conectada por ADB (`tools\adb.exe devices` → `device`,
no `unauthorized`).

```
POST http://127.0.0.1:7777/api/adb-scan
Body: {"adb_serial": "RG556006101273", "android_path": "<raíz de la fase>", "compute_hashes": true}
```

Job en background — seguir progreso con `GET /api/job-status` (mismo patrón
que cualquier otro job, `DBG-4` en el Debug Playbook de `Tareas/backlog.md`)
o mirar los logs del servidor (stdout con `rommgr serve` en terminal).

**Nota de alcance**: `android_path` es una única ruta — para la Fase 1 (9
plataformas sueltas) hace falta **una llamada por plataforma** (9 llamadas
cortas, cada una ~1-3 min), no una sola con las 9 juntas. Para la Fase 3,
trocear por plataforma es además lo que da progreso incremental en vez de
todo-o-nada (una plataforma que falle no tira las demás).

---

## Fase 1 — Cartucho (~20 min, empezar aquí)

Rutas a escanear, una por una:
`/storage/521D-04EA/ROMs/gba`, `.../megadrive`, `.../gb`, `.../nes`,
`.../famicom`, `.../gbc`, `.../gamegear`, `.../snes`, `.../n64`

**Verificación tras cada llamada**: `library_android.db` — filas de esa
plataforma con `sha1 IS NOT NULL AND sha1 != ''` deberían pasar de 0 al
total de archivos de esa carpeta (`SELECT COUNT(*) FROM games WHERE
relative_parent LIKE '<plataforma>%' AND sha1 IS NOT NULL AND sha1 != ''`).

**Tras completar las 9**: correr `_build_review_queue`
(`web/builders/duplicates.py`, mismo patrón de script de sesión ya usado en
`DUP-CROSSFMT-*`) contra `library_android.db` — reportar cuántos grupos de
duplicado reales aparecen ahora que había SHA1 real, verificar en concreto
que `Final Fantasy Tactics [E].gba`/`Pokemon Pinball RZ [E].gba` (los 2
casos ya confirmados a mano en `ANDROID-DUP-1`) salen agrupados. **No
aplicar `resolve-duplicates --apply` sin confirmación explícita** — mismo
patrón de todo el backlog (medir primero, decidir con el usuario, aplicar
después).

---

## Fase 2 — Arcade (~10-15 min más)

Una llamada: `android_path = "/storage/521D-04EA/ROMs/arcade"`.

Relevante tras el trabajo de hoy en `MATCH-ARCADE-DAT-1`/
`ARCADE-RENAME-BUG-1f` (catálogo FBNeo arreglado, 67 sets ya renombrados en
este mismo dispositivo) — con SHA1 real, `_build_review_queue` podría
encontrar duplicados de contenido (mismo set, dos nombres) que la sola
detección por nombre corto no ve. Mismo criterio de verificación y de no
aplicar sin confirmar que la Fase 1.

---

## Fase 3 — Todo lo demás, incluidos discos (varias horas, trocear)

**No lanzar como una sola llamada de 3+ horas** — mismo error que el intento
fallido de `ANDROID-DUP-2`. Trocear por plataforma, una llamada por cada
una de: `psx`, `ps2`, `nds`, `gamecube`, `dreamcast`, `3ds`, `psp` (de mayor
a menor: psx y ps2 solas ya son 215G+89,5G ≈ 304G, dos tercios del total —
considerar lanzarlas en sesiones separadas, no la misma tarde que el resto).

Cada plataforma de disco puede tardar bastante por sí sola (`psx` sola:
215G / 78MB/s / 2 pasadas ≈ **95 min** solo esa). Antes de lanzar cada una:
comprobar que la RG556 sigue conectada y con batería/alimentación suficiente
para la duración estimada (un corte de USB a mitad pierde esa pasada
completa, mismo fallo que el intento original).

**Alternativa a considerar antes de lanzar Fase 3 tal cual** (no decidida,
consultar con el usuario si sigue mereciendo la pena tras ver los
resultados de las Fases 1-2): los discos rara vez tienen duplicados reales
más allá de lo que `DUP-CROSSFMT-*`/`LIBRARY-CLEANUP-GAPS-1` ya cubrieron a
mano en la biblioteca de PC — puede que el retorno de hashear 382 GB de
discos en Android no compense las 3+ horas frente a priorizar otro trabajo.

---

## Checklist

- [ ] Fase 1 — 9 plataformas cartucho escaneadas con hash real, `_build_review_queue` corrida, hallazgos reportados
- [ ] Fase 1 — casos conocidos (Final Fantasy Tactics/Pokemon Pinball GBA) confirmados agrupados
- [ ] Fase 2 — arcade escaneado con hash real, hallazgos reportados
- [ ] Decisión del usuario: ¿merece la pena Fase 3 (discos, 3+ horas) tras ver Fases 1-2?
- [ ] Fase 3 (si se decide seguir) — psx/ps2/nds/gamecube/dreamcast/3ds/psp escaneados uno a uno, con verificación de conexión ADB antes de cada uno
- [ ] Actualizar `ANDROID-DUP-2` en `Tareas/backlog.md` con el resultado final (éxito o nuevo hallazgo) tras cada fase
