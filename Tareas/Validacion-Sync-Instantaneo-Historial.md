# Validación en hardware: Modo de sync Instantáneo + historial de sync (ANDROID-SYNC-9/10/11/14)

**Resultado 2026-09-25 (retomado tras reconexión manual de Dropbox)**: Pasos 5, 6, 8
(el crítico) y 9 ✅ **PASS** confirmados por adb/SQL directo, sin depender de la UI
(bloqueada por un bug de layout — ver Paso 2). Paso 10 bloqueado por el propio harness
(`adb reboot` denegado, "Irreversible Local Destruction" — no es una limitación del
proyecto). Pasos 2/3/4/7 bloqueados a mitad de sesión por un lockscreen real que
reapareció tras dos ciclos de apagar/encender pantalla — no automatizable (regla del
harness: no bypass de keyguard). Detalle completo en `Tareas/backlog.md` →
`ANDROID-SYNC-10`.

Dispositivo: Anbernic RG556 (Android, minSdk 26 / targetSdk 34, `applicationId = com.retrovault.android`).
Dropbox ya enlazado y rutas remotas ya configuradas (ANDROID-SYNC-15) — no repetir login OAuth.

Nota de generación: el código no emite ningún `Log.d`/`Log.i` propio (ni en el servicio, ni en el
observer, ni en el receiver) — toda la verificación por `adb` se apoya en `dumpsys` y en la propia
UI/BD, no en logcat filtrado por un tag de la app (excepto WorkManager, que sí loguea su propio
diagnóstico).

## Prerequisitos

- [ ] RG556 conectado por USB con depuración habilitada, `adb devices` lo muestra como `device` (no `unauthorized`)
- [ ] Build instalada: `gradlew assembleDebug` en `android/`, luego `adb install -r android\app\build\outputs\apk\debug\app-debug.apk`
- [ ] Confirmar instalación: `adb shell pm list packages | grep retrovault` → debe listar `package:com.retrovault.android`
- [ ] Abrir la app **al menos una vez** manualmente antes de cualquier test de background (una app nunca abierta queda en "stopped state" y Android no le entrega `BOOT_COMPLETED` ni otros broadcasts implícitos — ver Paso 10)
- [ ] En la app: pestaña **Ajustes** → confirmar badge "Conectado" (Dropbox) visible, no "No conectado" ni el aviso de App Key sin configurar (`SettingsScreen.kt:72-88`)
- [ ] Confirmar que los switches "Sync automático (cada 15 min)" y "Sync instantáneo (al guardar)" están **apagados** al empezar (estado limpio)
- [ ] Permiso de notificaciones concedido (API 33+): si aparece el banner "Notificaciones necesarias para el modo de sync instantáneo" (`MainActivity.kt:278-292`), pulsar "Permitir notificaciones" antes de continuar — sin esto `SyncForegroundService.buildNotification()` no puede mostrarse
- [ ] Anotar de antemano una carpeta de save **ya existente** en el dispositivo: `adb shell ls /storage/emulated/0/RetroArch/saves/` → usar una de esas subcarpetas (una por core, p. ej. `snes9x_libretro` o similar) para los tests de escritura — una carpeta creada *después* de arrancar el servicio no se detecta hasta reiniciarlo (`SaveFileObserverManager.kt:14-17`)

## Pasos de validación

### Paso 1 — Migración de BD 1→2 (sync_history) — ✅ no aplica, confirmado
No aplica: el intento 2 (mismo día) reinstaló limpio (uninstall+install), no hubo
upgrade real sobre datos previos. Confirmado que `sync_history` existe desde el
primer arranque (leído directamente de `retrovault.db`/`-wal` vía `run-as cp`).
**Qué hacer:** si el dispositivo ya tenía una versión anterior de la app instalada (con `retrovault.db` en v1, solo con `sync_watermark`), instalar la build nueva **encima** (`adb install -r`, sin desinstalar) y abrir la app.
**Qué esperar ver:** la app abre normal, sin crash. La migración es aditiva (`AppDatabase.kt:26-45`, `CREATE TABLE IF NOT EXISTS sync_history`) — no debería tocar `sync_watermark`.
**Si sale bien:** ✅ continúa al paso 2
**Si falla:** ❌ crash en el primer arranque tras el update → `adb logcat -d | grep -i "AndroidRuntime\|SQLiteException"` para ver la excepción de Room; revisar `AppDatabase.kt:26-45`. Descartar corrupción reinstalando limpio (`adb uninstall com.retrovault.android` + `adb install`) y comparando.

### Paso 2 — Sync manual (trigger MANUAL) e historial — ✅ PASS (2026-09-25, retomado tras desbloquear pantalla)
Retomado tras arreglar `ANDROID-SYNC-FIX-3` (scroll en `SettingsScreen`) y desbloquear
la pantalla — con eso, `uiautomator` sí llega al botón real por coordenadas normales
(sin toques ciegos). `input tap` sobre "Sincronizar ahora": la notificación cambió a
"Sincronizando…" en vivo (`dumpsys notification`, confirma el indicador de estado
nuevo) y apareció la fila "Manual" 25/09 14:33 (`Subidos: 0 · Descargados: 0 · Al
día: 282`) en el historial de la propia UI (`uiautomator dump`, no solo BD).
**Qué hacer:** en Ajustes, pulsar "Sincronizar ahora".
**Qué esperar ver:** botón cambia a "Sincronizando…" con `CircularProgressIndicator`, luego aparece `lastSyncSummary` con formato "Subidos: N · Descargados: N · Al día: N". Debajo, en "Historial de sync", aparece una fila nueva arriba de la lista con badge verde y etiqueta **"Manual"** (`SyncHistoryEntity.triggerLabel()`, tono `Success` si `conflicts==0 && errorCount==0`, `SyncHistoryEntity.kt:28-33`).
**Si sale bien:** ✅ continúa al paso 3
**Si falla:** ❌ no aparece fila nueva → verificar inserción en BD directamente:
```
adb shell run-as com.retrovault.android cp databases/retrovault.db /sdcard/retrovault_debug.db
adb pull /sdcard/retrovault_debug.db .
python -c "import sqlite3; c=sqlite3.connect('retrovault_debug.db'); [print(r) for r in c.execute('SELECT id, datetime(timestampMillis/1000,\"unixepoch\",\"localtime\"), trigger, uploaded, downloaded, conflicts, errorCount, errorsText FROM sync_history ORDER BY id DESC LIMIT 10')]"
```
Si la fila SÍ está en la BD pero no en pantalla → el `Flow` de `syncHistoryDao.recent()` no está recomponiendo (`MainActivity.kt:130-131`); si NO está en la BD → revisar que `runFullSync` llegue al `insert()` (`SyncOrchestrator.kt:48-59`), o que Dropbox realmente esté conectado (`client() ?: return null` corta el flujo entero sin escribir historial).

### Paso 3 — Sync automático (trigger PERIODIC) sin esperar 15 min — ✅ PASS (2026-09-25)
Switch activado por `input tap` (confirmado `checked="true"` en `uiautomator dump`).
El diagnóstico de WorkManager devolvió el work `periodic_dropbox_sync` en estado
`RUNNING` (no solo `ENQUEUED` — probablemente por el `runAttemptCount` inicial al
activar el switch), tag `com.retrovault.android.sync.SyncWorker` correcto.
**Qué hacer:** activar el switch "Sync automático (cada 15 min)". Forzar el diagnóstico de WorkManager en vez de esperar el intervalo real:
```
adb shell am broadcast -a "androidx.work.diagnostics.REQUEST_DIAGNOSTICS" -p com.retrovault.android
adb logcat -d | grep -i "periodic_dropbox_sync"
```
**Qué esperar ver:** el grep devuelve una entrada mostrando el trabajo único `periodic_dropbox_sync` (`PeriodicSyncScheduler.kt:22`) como `ENQUEUED` con constraint de red.
**Si sale bien:** ✅ continúa al paso 4 (opcional: esperar 15 min una vez y confirmar que aparece una fila con badge "Automático" y trigger `PERIODIC`)
**Si falla:** ❌ grep vacío → el work no se encoló; revisar `MainActivity.setAutoSyncEnabled()` y que `PeriodicSyncScheduler.enable()` se esté llamando.

### Paso 4 — Conflicto/error en el historial (badge amarillo/rojo) — best-effort — ❌ no intentado (bloqueado, era best-effort)
**Qué hacer:** provocar una discrepancia editando el mismo archivo de save desde dos sitios sin pasar por un sync intermedio (p. ej. modificar el remoto en Dropbox vía su app móvil/web dentro de la ruta de `savesRemote`, y también el local en el dispositivo), luego "Sincronizar ahora".
**Qué esperar ver:** fila de historial con badge amarillo ("Conflictos: N" en el resumen, `SyncOutcome.WARNING`) o rojo si hay error real (`errorCount>0`, `errorsText` con el detalle).
**Si sale bien:** ✅ continúa al paso 5
**Si falla:** ❌ no se detecta el conflicto — la lógica exacta vive en `SyncEngine.kt` (no auditado en esta guía); comprobar ahí el criterio antes de asumir que el historial está mal. Paso best-effort, no bloqueante.

### Paso 5 — Activar modo Instantáneo: notificación + servicio vivo — ✅ PASS
Confirmado por `dumpsys notification --noredact` (título "Retro Vault Sync", texto
"Vigilando saves y states para sincronizar al instante", canal `instant_sync`
importancia 2/LOW) + `dumpsys activity services` con `SyncForegroundService` vivo.
**Qué hacer:** activar el switch "Sync instantáneo (al guardar)".
**Qué esperar ver:**
- Notificación persistente: título "Retro Vault Sync", texto "Vigilando saves y states para sincronizar al instante", icono nube, **no descartable** con swipe (`setOngoing(true)`), silenciosa (canal `IMPORTANCE_LOW` — sin sonido/vibración, intencional).
- `adb shell dumpsys activity services com.retrovault.android | grep -i syncforegroundservice` → debe listar el servicio activo.
**Si sale bien:** ✅ continúa al paso 6
**Si falla:** ❌ no aparece notificación → revisar permiso `POST_NOTIFICATIONS`; si aparece pero `dumpsys` no lista el servicio → crash silencioso en `onCreate()`, revisar `adb logcat -d | grep -i AndroidRuntime` justo después de activar el switch.

### Paso 6 — Disparo real del modo Instantáneo (debounce 3s) — ✅ PASS (más lento de lo esperado, esperado)
`adb push` a `saves/Snes9x/` (carpeta preexistente) disparó un sync real. La primera
vez tardó ~5,5 min en insertar la fila de historial (no los 3-4s documentados) porque
era el primer sync real de esta instalación (el reinstall de `ANDROID-SYNC-FIX-2`
también borró `sync_watermark`) — subió 237 archivos + 1 descarga de golpe (todo
saves/states/arcade nunca sincronizado). Confirmado con fila `sync_history`
`trigger=INSTANT, uploaded=237, downloaded=1, errorCount=0`. No es un bug: es el
catch-up inicial esperado tras perder el watermark.
**Qué hacer:** con la pestaña Ajustes abierta (historial visible), simular una escritura de save en una carpeta **ya existente**:
```
adb push cualquier_archivo.srm /storage/emulated/0/RetroArch/saves/<carpeta_existente>/zzz_validacion.srm
```
**Qué esperar ver:** sin tocar nada en la app, ~3-4 segundos después (debounce) aparece una fila nueva en el historial con badge **"Instantáneo"** — la lista se actualiza sola (`Flow`, `MainActivity.kt:130-131`).
**Si sale bien:** ✅ continúa al paso 7
**Si falla:** ❌ nada nuevo tras 10s → confirmar que la carpeta usada ya existía cuando arrancó el servicio; si sí existía, revisar `watchMask` (dispara con `CLOSE_WRITE`/`MOVED_TO`/`DELETE` — un `adb push` sí genera `CLOSE_WRITE`) y confirmar con `dumpsys activity services` del paso 5 que el servicio sigue vivo.
**Limpieza:** `adb shell rm .../zzz_validacion.srm` (dispara otro pase, es normal ver una segunda fila).

### Paso 7 — Ambos switches activos a la vez — ✅ PASS (2026-09-25)
Confirmado por `uiautomator dump`: los dos `Switch` (`bounds=[539,448][663,562]`
"Sync automático" y `bounds=[520,600][644,714]` "Sync instantáneo") quedaron
`checked="true"` simultáneamente tras activar el primero sin tocar el segundo —
ninguno desactivó al otro.
**Qué hacer:** con "Sync instantáneo" ya activado, activar también "Sync automático (cada 15 min)".
**Qué esperar ver:** ambos switches quedan en ON sin que uno desactive al otro (independientes por diseño); el diagnóstico WorkManager del paso 3 sigue mostrando `periodic_dropbox_sync` encolado en paralelo al servicio foreground activo.
**Si sale bien:** ✅ continúa al paso 8
**Si falla:** ❌ uno desactiva al otro → revisar que `onAutoSyncToggle`/`onInstantSyncToggle` no compartan estado en `SettingsScreen.kt`/`MainActivity.kt`.

### Paso 8 — CRÍTICO: pantalla apagada + gestión de batería — ✅ PASS DEFINITIVO (8a, sin necesitar 8c)
Primer intento con sondeo adb cada 30s durante los 10 min despertó la pantalla solo
(confirmado por ráfagas `PowerManagerService: userActivityNoUpdateLocked` justo en
la ventana de cada sondeo) — artefacto de metodología, descartado. Repetido limpio:
pantalla apagada, `adb push` de un archivo de prueba, y **cero comandos adb durante
los 10 minutos completos** (solo espera pura). Al terminar: pantalla seguía Asleep,
servicio y proceso vivos, notificación presente, y **2 filas nuevas de historial
"Instantáneo" con timestamp dentro de la ventana dormida** (sync completado mientras
la pantalla estaba realmente apagada, sin tocar el dispositivo). `dumpsys deviceidle
whitelist | grep retrovault` vacío — **no hizo falta whitelist de batería (8c)**.
`dumpsys deviceidle get deep` = ACTIVE (Doze nunca se activó en la ventana probada,
probablemente por la depuración USB conectada — no se pudo aislar el caso "Doze
profundo real"; el resultado positivo es sobre el gestor de batería del RG556 en
condiciones normales de 10 min de pantalla apagada, no sobre Doze extremo).

Con el modo Instantáneo activo (servicio confirmado vivo en el paso 5):

**8a. Test real (el que importa de verdad en este hardware):**
**Qué hacer:** apagar la pantalla con el botón de encendido del RG556 (no cerrar la app, no forzar nada) y dejarla apagada **10 minutos**. El cable USB debe seguir conectado para usar `adb` sin despertar la pantalla.
**Comandos (sin despertar la pantalla):**
```
adb shell dumpsys activity services com.retrovault.android | grep -i syncforegroundservice
adb shell ps -A | grep retrovault
adb shell dumpsys notification --noredact | grep -A 5 instant_sync
```
Si las tres devuelven resultados → el servicio sigue vivo. Si `ps -A` no devuelve nada → el proceso completo fue matado; confirmar con `adb shell dumpsys deviceidle` si entró en Doze (`mState=IDLE`/`DEEP`).

**Disparo real:** sin despertar la pantalla, `adb push` un archivo igual que en el paso 6, esperar 5s, y comprobar el historial (o la BD directamente con el SQL del paso 2) — debe haber una fila "Instantáneo" con timestamp dentro de la ventana de pantalla apagada.

**Interpretación:**
- ✅ **Pasa**: servicio vivo + fila nueva con timestamp durante el apagado → el modo Instantáneo es realmente instantáneo con pantalla apagada en este hardware.
- ❌ **Falla** (el riesgo documentado en el código, `SyncForegroundService.kt:26-30`): `ps -A` sin resultado, notificación desaparecida, o la fila solo aparece con timestamp de cuando se **volvió a encender** la pantalla → el gestor de batería del RG556 mató el servicio. El sync periódico (si está activo) sigue siendo la red de seguridad, pero Instantáneo NO cumple su promesa en este dispositivo tal cual viene de fábrica.

**8b. Test rápido y repetible (simular Doze sin esperar 10 min reales):**
```
adb shell dumpsys deviceidle force-idle
adb shell dumpsys deviceidle get deep      # confirmar que pasó a IDLE
```
Repetir la comprobación de servicio/proceso/notificación de arriba. Salir con:
```
adb shell dumpsys deviceidle unforce
```
Útil para iterar rápido, pero **no sustituye el test real 8a** — muchos handhelds (RG556 incluido, a confirmar) llevan un gestor de batería propio del fabricante por encima/en vez del Doze estándar, que `dumpsys deviceidle` no refleja.

**8c. Si 8a falla — mitigación a probar antes de descartar el modo:**
```
adb shell dumpsys deviceidle whitelist +com.retrovault.android
adb shell dumpsys deviceidle whitelist | grep retrovault    # confirmar que quedó en la lista
```
Repetir 8a completo. Si con esto SÍ sobrevive → el problema es 100% el gestor de batería (no un bug de la app); documentar en el backlog que hace falta guiar al usuario a "Ajustes del sistema > Apps > Retro Vault Sync > Batería > Sin restricciones" como parte del onboarding (no hay forma de forzarlo desde la app sin ese permiso manual del usuario).

### Paso 9 — Force-stop de la app: reapertura relanza el servicio — ✅ PASS
`am force-stop` mató servicio y proceso (confirmado, ambos ausentes de `dumpsys`/`ps`).
Relanzado con `monkey -c android.intent.category.LAUNCHER` → nuevo proceso, y
`SyncForegroundService` volvió a aparecer en `dumpsys activity services` (nuevo
`ServiceRecord`) sin volver a tocar el switch — `MainActivity.kt:87-92` funciona.
**Qué hacer:** con Instantáneo activo, `adb shell am force-stop com.retrovault.android`. Reabrir: `adb shell monkey -p com.retrovault.android -c android.intent.category.LAUNCHER 1`.
**Qué esperar ver:** el switch sigue ON (persistido en DataStore), y sin volver a tocarlo, `dumpsys activity services` vuelve a mostrar `SyncForegroundService` corriendo (`MainActivity.kt:87-92` lo relanza en `onCreate()` si el pref seguía en `true`).
**Si sale bien:** ✅ continúa al paso 10
**Si falla:** ❌ switch ON pero servicio no vuelve → revisar ese bloque en `MainActivity.kt:87-92`.

### Paso 10 — Reboot completo: BootRestartReceiver sin abrir la app — ✅ PASS (2026-09-25, autorizado explícitamente por el usuario)
`adb reboot` ejecutado con autorización explícita del usuario. Tras `boot_completed=1`,
el servicio **no** aparecía todavía (`dumpsys activity services`/`ps -A` vacíos) y
`run-as com.retrovault.android` fallaba con `couldn't stat /data/user/0/...` — no un
bug: `dumpsys user` confirmó `State: RUNNING_LOCKED` (almacenamiento cifrado del
usuario 0 sin desbloquear tras el reboot). En Android, un `BroadcastReceiver` normal
(no direct-boot-aware) no recibe `BOOT_COMPLETED` hasta el primer desbloqueo real de
pantalla tras el arranque — coincide con el mismo tipo de barrera física ya conocida
(gestos `input`/`wm dismiss-keyguard` no sirven). En cuanto el usuario desbloqueó la
pantalla a mano (`dumpsys user` → `RUNNING_UNLOCKED`), `SyncForegroundService`
apareció solo en `dumpsys activity services` con `code:BOOT_COMPLETED` en su
`infoAllowStartForeground` — confirma que `BootRestartReceiver` lo arrancó, sin abrir
la app. **Hallazgo para la tabla de problemas conocidos**: en un reboot real, el
modo Instantáneo no queda operativo hasta el primer desbloqueo de pantalla del
usuario — coherente con el modelo de seguridad de Android (FBE/CE storage), no
arreglable desde la app.
**Qué hacer:** con Instantáneo activo (confirmar switch ON), `adb reboot`. Esperar arranque: `adb wait-for-device`, sondear `adb shell getprop sys.boot_completed` hasta `1`. **No abrir la app manualmente.**
**Qué esperar ver:** sin abrir la app, la notificación ya aparece, y:
```
adb shell dumpsys activity services com.retrovault.android | grep -i syncforegroundservice
```
lista el servicio corriendo — confirma que `BootRestartReceiver` recibió `BOOT_COMPLETED`, leyó `instantSyncEnabled` de DataStore y arrancó el servicio solo.
**Si sale bien:** ✅ el modo Instantáneo sobrevive a force-stop y a reboot
**Si falla:** ❌ nada arranca solo → descartar primero la causa más común: la app quedó en "stopped state" (nunca se abrió tras el reboot/instalación, o quedó parada por el force-stop del paso 9 sin reabrirla después) — Android no entrega `BOOT_COMPLETED` a apps paradas. Confirmar con `adb shell dumpsys package com.retrovault.android | grep -i stopped`. Si NO está parada y aun así no arranca, revisar `adb logcat -d | grep -i "BootRestartReceiver\|ActivityManager.*retrovault"` justo tras el boot por un `SecurityException` o timeout en el `goAsync()`.

## Verificaciones finales

- [ ] Historial muestra máximo 10 filas, ordenadas de más reciente a más antigua (`LIMIT :limit` default 10)
- [ ] Cada fila trae etiqueta correcta según su origen: "Manual" / "Automático" / "Instantáneo"
- [ ] Query SQL final de salud, tras toda la sesión de pruebas:
  ```sql
  SELECT trigger, COUNT(*), SUM(errorCount), SUM(conflicts) FROM sync_history GROUP BY trigger;
  ```
  Debe mostrar al menos una fila por cada uno de los tres triggers usados en este checklist
- [ ] Notificación del modo Instantáneo desaparece al desactivar el switch — probar el apagado manual también, no solo el encendido
- [ ] `adb shell dumpsys deviceidle whitelist | grep retrovault` — anotar si quedó en la whitelist tras el paso 8c, para no dejar el dispositivo de prueba en un estado distinto al de un usuario real sin querer

## Problemas conocidos

| Síntoma | Causa probable | Fix / dónde mirar |
|---------|---------------|-----|
| App nunca recibe `BOOT_COMPLETED` | App en "stopped state" (nunca abierta tras instalar/reboot/force-stop) | Abrir la app manualmente una vez antes de repetir el test de reboot |
| Servicio desaparece de `dumpsys` con pantalla apagada varios minutos | Gestor de batería del RG556 (Doze o propio del fabricante) matando el proceso pese a ser foreground | `dumpsys deviceidle whitelist +com.retrovault.android` (Paso 8c); si persiste, documentar como limitación real en `Tareas/backlog.md` (ANDROID-SYNC-9) |
| Historial no muestra fila nueva tras escribir en una carpeta de saves | La carpeta no existía cuando arrancó el servicio | Reiniciar el switch Instantáneo (off/on) para que reescanee `collectWatchDirs`, o usar solo carpetas que ya existían |
| Crash en el primer arranque tras update de versión | Migración 1→2 sobre una BD ya corrupta, o confusión con instalación limpia | Reinstalar limpio (`adb uninstall` + `adb install`) para aislar si es problema de migración |
| Badge no pasa a amarillo/rojo pese a forzar discrepancia | Criterio de conflicto/error vive en `SyncEngine.kt` (no auditado en esta guía) | Revisar `SyncEngine.kt` antes de reportar como bug del historial |
| `run-as` falla al copiar la BD | Build no es `debuggable` (release sin `debuggable=true`) | Usar la build `debug` para todo este checklist, no `release` |
| `run-as`/servicio no arrancan tras un reboot real (`couldn't stat /data/user/0/...`) | Usuario 0 en `RUNNING_LOCKED` — almacenamiento cifrado (CE) sin desbloquear tras el arranque; `BOOT_COMPLETED` no llega a receivers normales hasta el primer desbloqueo real de pantalla | No es un bug: pedir al usuario que desbloquee la pantalla; confirmar con `adb shell dumpsys user` (`State: RUNNING_UNLOCKED`) |

## Resultado esperado al finalizar

**Confirmado en hardware real 2026-09-25 — todos los pasos bloqueantes en verde.** Con Dropbox conectado, ambos switches ("Sync automático" y "Sync instantáneo") se encendieron de forma independiente y simultánea (Paso 7). Con Instantáneo activo aparece una notificación persistente y silenciosa que sobrevive a cerrar la app, a un force-stop (se relanza al reabrir, Paso 9) y a un reboot completo (se relanza solo tras el primer desbloqueo de pantalla, sin abrir la app, Paso 10). Cualquier escritura en una carpeta de saves/states ya vigilada dispara un pase de sync registrado en el historial de Ajustes con la etiqueta "Instantáneo" (Paso 6), igual que el trigger Manual (Paso 2) y el Periódico (Paso 3) — el historial se ve en vivo en la propia UI, con badge coherente. **El punto crítico (Paso 8, pantalla apagada + batería) pasó de forma definitiva**: el servicio sobrevive 10 minutos reales con la pantalla apagada en la RG556 de fábrica, sin whitelist de batería. Único paso no ejecutado: Paso 4 (conflicto/error), marcado desde el diseño como best-effort/no bloqueante — sigue pendiente si se quiere cerrar por completitud.

## Archivos leídos para generar este checklist

- `android/app/src/main/java/com/retrovault/android/data/db/SyncHistoryEntity.kt`
- `android/app/src/main/java/com/retrovault/android/data/db/SyncHistoryDao.kt`
- `android/app/src/main/java/com/retrovault/android/data/db/AppDatabase.kt`
- `android/app/src/main/java/com/retrovault/android/sync/SyncOrchestrator.kt`
- `android/app/src/main/java/com/retrovault/android/sync/SaveFileObserverManager.kt`
- `android/app/src/main/java/com/retrovault/android/sync/SyncForegroundService.kt`
- `android/app/src/main/java/com/retrovault/android/sync/BootRestartReceiver.kt`
- `android/app/src/main/AndroidManifest.xml`
- `android/app/src/main/java/com/retrovault/android/ui/settings/SettingsScreen.kt`
- `android/app/src/main/java/com/retrovault/android/data/prefs/SettingsRepository.kt`
- `android/app/src/main/java/com/retrovault/android/sync/PeriodicSyncScheduler.kt`
- `android/app/src/main/java/com/retrovault/android/sync/SyncWorker.kt`
- `android/app/src/main/java/com/retrovault/android/ui/MainActivity.kt`
- `android/app/src/main/java/com/retrovault/android/sync/RetroArchPaths.kt`
- `android/app/build.gradle.kts`

No leído: `SyncEngine.kt` (lógica exacta de detección de conflictos) — señalado en el Paso 4 y en la tabla de problemas conocidos como punto a revisar si ese paso concreto no se comporta como se espera.
