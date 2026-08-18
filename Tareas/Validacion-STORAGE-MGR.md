# Validación en hardware: STORAGE-MGR (borrado en bloque PC/Android)

PR #213 (2026-08-17), pendiente de probar contra Anbernic RG556 antes de confiar
en él para uso real. Vive dentro del panel "Comparar" de la pestaña Colección
(no es pestaña nueva) — reutiliza `_build_library_diff()` con `size_bytes` +
totales, y añade borrado en bloque vía `POST /api/storage/delete-bulk`.

## Prerequisitos

- [ ] RG556 conectada por cable USB, depuración USB activada, prompt "Allow USB
      debugging" aceptado en el dispositivo.
- [ ] `adb devices -l` (usando `tools/adb.exe`) muestra la RG556 con estado
      `device` (no `unauthorized`/`offline`). Si hay más de un dispositivo ADB
      conectado a la vez (emulador, otro móvil…), desconéctalo — la resolución
      del transporte exige exactamente un dispositivo listo
      (`resolve_single_device_transport`, `src/rom_manager/sync/adb_transport.py:98-111`,
      llamado por request en `src/rom_manager/web/handlers/collection.py:33-36`).
- [ ] En la pestaña **Colección** aún no has probado el panel "Comparar" contra
      hardware real — si ya tienes ROMs reales en PC y Android, dejarlos en paz;
      todo lo de este checklist se hace con archivos basura desechables (ver
      Paso 2).
- [ ] Backup rápido de `library_pc.db` y `library_android.db` (copia de los
      ficheros) antes de empezar — el borrado hace `cascade_delete_games_by_source_path`,
      es decir sí toca la BD real aunque el archivo PC vaya a papelera.

## Preparar archivos de prueba

Usa una extensión de ROM ya reconocida por un escaneo normal (p. ej. `.gba`,
Game Boy Advance) para que el escáner los indexe con `file_type = 'rom'` —
la query de `/api/library-diff` filtra explícitamente por eso
(`src/rom_manager/web/builders/diff.py:33`). El contenido no importa (no se
valida cabecera de ROM, solo se hashea), pero debe ser único por archivo para
que cada uno tenga SHA1 distinto y no se empareje como "en ambas".

1. En PC, dentro de una carpeta de plataforma ya escaneada (p. ej.
   `<library_root>\Game Boy Advance\`), crea 3 archivos:
   `RV_TEST_PC_1.gba`, `RV_TEST_PC_2.gba`, `RV_TEST_PC_3.gba`, cada uno con
   contenido distinto (PowerShell: `[byte[]](1..200|%{Get-Random -Max 256}) | Set-Content -Path RV_TEST_PC_1.gba -Encoding Byte` o simplemente texto único por archivo).
2. Localiza la carpeta GBA real en la RG556 (la misma que usa RetroArch, ver
   `EMULATOR_SAVE_PATHS_DEFAULT` en `src/rom_manager/config.py` para rutas de
   referencia — normalmente algo como `/storage/emulated/0/RetroArch/roms/gba/`
   o `/storage/emulated/0/roms/gba/`, comprueba con
   `adb shell ls /storage/emulated/0/RetroArch/roms/`).
3. Crea 3 archivos locales distintos y súbelos con `adb push`:
   ```
   adb -s <SERIAL> push RV_TEST_AND_1.gba /storage/emulated/0/RetroArch/roms/gba/
   adb -s <SERIAL> push RV_TEST_AND_2.gba /storage/emulated/0/RetroArch/roms/gba/
   adb -s <SERIAL> push RV_TEST_AND_3.gba /storage/emulated/0/RetroArch/roms/gba/
   ```
4. Confirma con `adb shell ls -la /storage/emulated/0/RetroArch/roms/gba/RV_TEST_AND_*.gba`
   que los 3 están ahí antes de seguir.

## Pasos de validación

### Paso 1 — Escanear PC y Android para catalogar los archivos de prueba

**Qué hacer:** Pestaña Overview → sección "Gestión de biblioteca". Marca
`scan-include-pc` (PC) y `scan-include-adb` ("Consola Android por ADB"). Pulsa
**Detectar** (`detectAdbDevicesForScan()`) hasta que `scan-adb-device` muestre
el serial de la RG556, verifica que `scan-android-path` apunta a
`/storage/emulated/0` (o la ruta correcta si difiere). Pulsa **Escanear**
(`btn-scan`, `doScan()`).

**Qué esperar ver:** barra de progreso `scan-progress-wrap`, y al terminar
`job-result-scan` con un resumen (archivos vistos / ROMs detectados) que
incluye tus 6 archivos de prueba.

**Si sale bien:** ✅ continúa al Paso 2.
**Si falla:** ❌ Si el escaneo Android da 0 archivos → revisa `scan-adb-status`
(mensaje de error) y que `scan-android-path` sea la carpeta correcta, no la
raíz completa (escaneo completo de `/storage/emulated/0` puede tardar mucho).
Si los `.gba` de prueba no aparecen como ROM tras el escaneo, comprueba con
sqlite `SELECT file_type FROM games WHERE original_filename LIKE 'RV_TEST%'`
en ambas DB — si salen como `file_type != 'rom'`, la extensión no está en la
lista reconocida para esa plataforma.

### Paso 2 — Abrir "Comparar" y validar tamaños/totales (punto 1)

**Qué hacer:** Pestaña Colección → botón **🔀 Comparar** (`btn-col-diff`,
`toggleDiff()`). El panel `col-diff-panel` se abre y llama automáticamente a
`loadLibraryDiff()` → `GET /api/library-diff`.

**Qué esperar ver:** en `diff-summary`: `PC: N ROMs (X GB) | Android: N ROMs
(Y GB) | En ambas: Z | ...`. Columna **Solo PC** (`diff-pc-count`/`diff-pc-list`)
debe listar tus 3 `RV_TEST_PC_*.gba`; columna **Solo Android**
(`diff-and-count`/`diff-and-list`) tus 3 `RV_TEST_AND_*.gba`.

**Verificación cruzada de tamaño (hardware real):**
```
adb shell find /storage/emulated/0/RetroArch/roms/gba -maxdepth 1 -name "*.gba" -exec stat -c '%n %s' {} +
```
Suma manualmente los bytes de tus 3 archivos y compáralos con la diferencia
entre el total Android mostrado antes/después, o directamente con lo que
muestra al pasar el ratón sobre cada fila (`title="{source_path}"`, ver
`collection.js:321`). **No uses `adb shell du -sh`** para el total exacto —
`du` redondea a bloques de filesystem; `size_bytes` en la BD es el `st_size`
exacto capturado en el escaneo (mismo mecanismo que `ls_recursive()` en
`src/rom_manager/sync/adb_transport.py:198-239`), así que la comparación
correcta es contra `stat -c '%s'`, no contra `du`.

**Si sale bien:** ✅ los totales cuadran (± unos bytes de redondeo si usaste `du`) → continúa al Paso 3.
**Si falla:** ❌ Total Android en 0 pese a escaneo OK → revisa que `repo_android`
apunte a `library_android.db` (etiqueta `ov-ab-db-label` en Overview) y no a
una DB vacía de otro perfil.

### Paso 3 — Borrar 2-3 archivos solo-PC → papelera (punto 2)

**Qué hacer:** En la columna **Solo PC**, marca los checkboxes (`.diff-sel`,
`data-side="pc"`) de `RV_TEST_PC_1.gba` y `RV_TEST_PC_2.gba`. Pulsa
**🗑 Borrar seleccionados** (`deleteSelectedStorage()`).

**Qué esperar ver:** modal de confirmación (`#confirm-modal`, título "Borrar
seleccionados") con el texto: *"¿Borrar 2 archivo(s) seleccionado(s)?"* +
**una sola** nota: *"Los archivos de PC se moverán a `_descartados/` (se
purgan a los 30 días)."* (`_STORAGE_TRASH_NOTE`, `collection.js:359`) — sin
mención de Android, porque la selección es 100% PC. Pulsa **Borrar**
(`confirm-ok`).

**Qué esperar tras confirmar:** `diff-sync-status` y toast muestran
`✓ 2 a papelera`. El panel se recarga solo (`loadLibraryDiff()` se relanza
porque `r.trashed > 0`) y `diff-pc-count` baja en 2.

**Verificación en disco:**
```
dir "<library_root>\Game Boy Advance\_descartados\"
```
Debe contener `RV_TEST_PC_1.gba` y `RV_TEST_PC_2.gba`, y ya **no** existir en
la carpeta original. Para confirmar que es recuperable: mueve uno de vuelta
manualmente a la carpeta de plataforma — debe abrir/copiar sin error (es un
`shutil.move`, no una copia corrupta).

**Verificación en BD:**
```sql
SELECT COUNT(*) FROM games WHERE original_filename LIKE 'RV_TEST_PC_%';
```
sobre `library_pc.db` → debe dar **1** (el tercero, `RV_TEST_PC_3.gba`, que no
borraste). Los dos borrados ya no tienen fila (borrado en cascada,
`cascade_delete_games_by_source_path`).

**Si sale bien:** ✅ continúa al Paso 4.
**Si falla:** ❌ Si el archivo desaparece sin pasar por `_descartados/` →
revisa `discard_to_trash()` (`src/rom_manager/utils/trash.py:28-51`), puede
que el destino ya existiera y el sufijo numérico `(1)` no se vea a simple
vista — busca `RV_TEST_PC_1 (1).gba`.

### Paso 4 — Borrar 2-3 archivos solo-Android → borrado real vía ADB (punto 3)

**Antes de borrar**, confirma existencia real:
```
adb shell ls -la /storage/emulated/0/RetroArch/roms/gba/RV_TEST_AND_1.gba
adb shell ls -la /storage/emulated/0/RetroArch/roms/gba/RV_TEST_AND_2.gba
```

**Qué hacer:** En la columna **Solo Android**, marca `RV_TEST_AND_1.gba` y
`RV_TEST_AND_2.gba` (`data-side="android"`). Pulsa **🗑 Borrar seleccionados**.

**Qué esperar ver ANTES de confirmar:** el modal muestra *solo* la nota roja
de Android: *"Los archivos de Android se borran directamente del dispositivo
— no hay papelera ahí, no se pueden recuperar."* (`_STORAGE_DEVICE_NOTE`,
`collection.js:360`, en `<span style="color:var(--c-pink)">`) — sin la nota de
papelera de PC, porque `hasPc` es `false` en esta selección
(`collection.js:369-374`). **Este es el punto crítico a validar**: el aviso de
irreversibilidad debe verse en pantalla antes de pulsar "Borrar", no después.

Pulsa **Borrar**.

**Qué esperar tras confirmar:** `✓ 0 a papelera · 2 borrado(s) en Android`.

**Verificación en el dispositivo (borrado real, no simulado):**
```
adb shell ls /storage/emulated/0/RetroArch/roms/gba/RV_TEST_AND_1.gba
```
Debe devolver `No such file or directory` (o equivalente de toybox). Repite
para el segundo.

**Verificación en BD:** sobre `library_android.db`,
`SELECT COUNT(*) FROM games WHERE original_filename LIKE 'RV_TEST_AND_%'` →
debe dar **1** (el tercero, que no tocaste).

**Qué pasa si un borrado Android falla a medias (importante, es irreversible):**
`AdbTransport.remove()` (`src/rom_manager/sync/adb_transport.py:185-194`) ya
tiene una red de seguridad: ejecuta `rm -f` y **después verifica**
`file_exists()`; si el archivo sigue ahí, lanza `RuntimeError`.
`delete_storage_items()` (`src/rom_manager/services/storage_service.py:77-86`)
captura esa excepción **antes** de incrementar `deleted_device` y **antes** de
llamar a `cascade_delete_games_by_source_path` — así que un fallo real nunca
deja una fila fantasma en BD con el archivo aún vivo, ni un archivo borrado
con fila viva: o se borra y se limpia la fila, o falla y ambos (archivo +
fila) se quedan como estaban, con el motivo en `errors`.

**Cómo forzar y comprobar este caso hoy mismo:** desconecta el cable USB (o
apaga pantalla si eso corta ADB) justo antes de pulsar "Borrar" con la
selección Android marcada.
**Qué esperar ver:** `✓ 0 a papelera · 0 borrado(s) en Android · 1 error(es)`
(o 2, según cuántos ítems Android había) — mira la consola del navegador
(F12) para el detalle exacto por archivo:
`console.error('Storage delete errors:', r.errors)` (`collection.js:385`).
Verifica que el archivo sigue existiendo en el dispositivo (reconecta y
`adb shell ls`) y que la fila sigue en `library_android.db` — nada se perdió.

**Si sale bien:** ✅ continúa al Paso 5.
**Si falla de otra forma** (p. ej. el archivo desaparece del dispositivo pero
la fila de BD permanece, o viceversa): ❌ eso sí sería un bug real de
atomicidad — anótalo con el mensaje exacto de `errors` y
`src/rom_manager/services/storage_service.py:81-93` como referencia, no lo
arregles en caliente.

### Paso 5 — Selección mixta PC + Android en la misma acción (punto 4)

**Preparación:** deja o crea un archivo PC-only (`RV_TEST_PC_3.gba`, el que
sobrevivió) y un archivo Android-only (`RV_TEST_AND_3.gba`) sin borrar de los
pasos anteriores.

**Qué hacer:** marca **a la vez** el checkbox de `RV_TEST_PC_3.gba` en la
columna Solo PC **y** el de `RV_TEST_AND_3.gba` en la columna Solo Android.
Pulsa **🗑 Borrar seleccionados**.

**Qué esperar ver:** el modal debe mostrar **DOS párrafos `<p>` separados**
(`collection.js:372-375`: `notes.push(...)` condicional por `hasPc`/`hasAndroid`,
luego `notes.map(n => \`<p>${n}</p>\`).join('')`) — no una frase genérica
única. Para comprobarlo sin ambigüedad, abre DevTools (F12) → Elements →
inspecciona `#confirm-body` y confirma que hay dos elementos `<p>` distintos
dentro, el primero con el texto de papelera (PC) y el segundo, en rosa, con el
texto de irreversibilidad (Android).

Pulsa **Borrar**.

**Qué esperar tras confirmar:** `✓ 1 a papelera · 1 borrado(s) en Android`.

**Verificación de mecanismo correcto por lado:**
- `RV_TEST_PC_3.gba` → debe aparecer en `<library_root>\Game Boy Advance\_descartados\`
  (papelera, recuperable). **No** debe haber tocado `library_android.db`.
- `RV_TEST_AND_3.gba` → `adb shell ls .../RV_TEST_AND_3.gba` debe fallar
  (borrado real, irrecuperable). **No** debe haber tocado `library_pc.db`.

Esto corresponde exactamente a `test_mixed_selection_only_touches_matching_repo`
en `tests/test_storage_service.py:111-135` — el objetivo de este paso es
confirmar en hardware real lo que el test ya garantiza en software: cada item
solo toca su propio repo/mecanismo, nunca el otro.

**Si sale bien:** ✅ STORAGE-MGR validado en hardware real.
**Si falla:** ❌ si el archivo PC acaba borrado "de verdad" (sin pasar por
`_descartados/`) o el Android acaba en alguna papelera inesperada → revisa el
switch `location == "pc"` vs `else` en
`src/rom_manager/services/storage_service.py:66-86`, y que el checkbox
(`data-side`) coincide con la columna real donde se pulsó (bug de UI, no de
backend, si el dato no cuadra con la columna visual).

## Verificaciones finales

- [ ] `SELECT sha1, original_filename FROM games WHERE original_filename LIKE 'RV_TEST%'`
      en `library_pc.db` y `library_android.db` — solo debe quedar el registro
      del archivo PC que fue a papelera si no lo restauraste, ninguno de los
      Android borrados.
- [ ] `<library_root>\Game Boy Advance\_descartados\` contiene exactamente los
      archivos PC que borraste en esta sesión (2 del Paso 3 + 1 del Paso 5) —
      ninguno más, ninguno menos.
- [ ] `adb shell ls /storage/emulated/0/RetroArch/roms/gba/RV_TEST_AND_*.gba`
      no devuelve nada (todos los de prueba borrados, salvo si dejaste alguno
      pendiente a propósito).
- [ ] Consola del navegador (F12) sin errores JS al abrir/recargar el panel
      "Comparar" ni al ejecutar los 4 borrados.
- [ ] Revisa `GET /api/logs` (o `config.logs_dir / rommgr.log` directamente) por
      si `delete_storage_items` dejó algún `_log.warning`/`error` no visible en
      la UI (el módulo define `_log = logging.getLogger(__name__)` en
      `src/rom_manager/services/storage_service.py:22` aunque en esta versión
      no se usa aún para loguear cada borrado — anota como posible mejora si
      quieres trazabilidad en `.rommgr/` además del toast).
- [ ] Limpieza: borra manualmente los restos de prueba en `_descartados/`
      (papelera) para no ensuciar la purga automática de 30 días con archivos
      basura.

## Problemas conocidos

| Síntoma | Causa probable | Fix / dónde mirar |
|---|---|---|
| "Borrar seleccionados" no hace nada | Ningún checkbox marcado | Toast "Selecciona al menos un juego" — `collection.js:365` |
| Modal muestra solo nota de PC aunque seleccionaste Android también | El checkbox Android no tiene `data-side="android"` correcto, o se generó en la tabla equivocada | Revisar `_renderDiffTable()` — `collection.js:304-329` |
| `N error(es)` tras borrar Android | Dispositivo se desconectó a mitad, o el `rm` no pudo (permisos, ruta con espacios mal escapada) | Ver detalle exacto en consola del navegador: `console.error('Storage delete errors:', r.errors)` — `collection.js:385` |
| El archivo sigue en "Solo Android" tras un borrado con errores | El panel solo se recarga si `r.trashed \|\| r.deleted_device` es > 0 — si todo falló, no se refresca (comportamiento esperado, no bug) | `collection.js:386` |
| `size_bytes`/total no coincide exactamente con `adb shell du -sh` | `du` redondea a bloques de filesystem; la BD guarda `st_size` exacto | Comparar contra `stat -c '%s'` por archivo, no contra `du` — mismo criterio que `ls_recursive()`, `adb_transport.py:198-239` |
| `POST /api/storage/delete-bulk` responde "dispositivo no conectado" para ítems Android aunque la RG556 está enchufada | Hay 0 o 2+ dispositivos ADB `ready` simultáneos — `resolve_single_device_transport` exige exactamente 1 | `adb_transport.py:98-111`, resuelto por request en `collection.py:33-36` |
| Archivo Android "desaparece" del dispositivo pero la fila sigue en BD (o al revés) | Esto **no** debería pasar por diseño — sería un bug real de atomicidad | Revisar orden borrado→verificación→cascade en `storage_service.py:77-93` y `adb_transport.py:185-194`; documentar con el `errors[]` exacto, no arreglar en caliente |
| Panel "Comparar" muestra 0 en ambos lados tras escanear | El escaneo ADB apuntó a una ruta sin ROMs (`scan-android-path` incorrecto) o `repo_android` no es `library_android.db` | Revisar `scan-adb-status` tras el escaneo; etiqueta `ov-ab-db-label` en Overview confirma qué DB se está usando |

## Resultado esperado al finalizar

Con la RG556 conectada, el panel "Comparar" de Colección refleja con
precisión (± redondeo de `du`) los ROMs y bytes reales en ambos lados. Los
borrados PC quedan siempre recuperables en `_descartados/` durante 30 días y
desaparecen de la BD de inmediato; los borrados Android son reales e
irreversibles en el dispositivo, con un aviso explícito e inequívoco (nota
propia, no genérica) antes de confirmar cuando la selección mezcla ambos
lados. Ningún escenario de fallo (dispositivo desconectado, `rm` fallido a
medias) deja un estado inconsistente entre el archivo físico y la fila de
BD — el sistema falla "seguro": o se borra todo (archivo + fila), o no se
borra nada y se reporta el error.
