# Checklist de validación en hardware — ANDROID-SYNC-15

**Dispositivo:** Anbernic RG556, serial `RG556006101273`, ADB accesible vía `tools/adb.exe -s RG556006101273 ...`.
**App:** `com.retrovault.android`, versionName 0.1.0 / versionCode 1, instalada 2026-09-08.

## Prerequisitos

- [ ] RG556 conectada por USB, depuración ADB autorizada (`tools/adb.exe -s RG556006101273 get-state` → `device`).
- [ ] Confirmar versión Android real del dispositivo (no asumir):
  ```
  tools/adb.exe -s RG556006101273 shell getprop ro.build.version.sdk
  tools/adb.exe -s RG556006101273 shell getprop ro.build.version.release
  ```
  Esto determina qué rama del modelo de permisos aplica (tabla Roadmap §3): API 30+ → `MANAGE_EXTERNAL_STORAGE`; API 26-29 → legacy runtime + `requestLegacyExternalStorage`; `POST_NOTIFICATIONS` solo si API ≥ 33; `FOREGROUND_SERVICE_DATA_SYNC` solo si API ≥ 34.
- [ ] Confirmar build instalada:
  ```
  tools/adb.exe -s RG556006101273 shell dumpsys package com.retrovault.android | grep -E "versionName|versionCode|firstInstallTime|lastUpdateTime"
  ```
- [ ] En `config.toml` del PC: `saves_remote`/`states_remote` apuntan al mismo path de Dropbox que en Ajustes de la app Android (mismo path relativo, p. ej. `/RetroSync/saves` vs `dropbox:/RetroSync/saves` en el PC — son equivalentes, el prefijo `dropbox:` es solo el nombre del remote rclone).
- [ ] En RetroArch de la RG556: **"Sort Saves/States by core"** activado (`Settings → Saving`) — si está apagado, el punto 2 de este checklist no tiene nada real que verificar y hay que activarlo antes de continuar.
- [ ] Misma cuenta de Dropbox conectada en la app Android y en el PC.
- [ ] Anota carpetas de `saves_dir`/`states_dir` locales del PC para comparar rutas relativas más adelante.

---

## 1. Permisos de almacenamiento

**[ADB]** Comprobar estado actual del permiso (API 30+):
```
tools/adb.exe -s RG556006101273 shell appops get com.retrovault.android MANAGE_EXTERNAL_STORAGE
```
Salida esperada si está concedido: `MANAGE_EXTERNAL_STORAGE: allow`. Si dice `default` o `ignore`/`deny`, no está concedido.

Si el dispositivo resultó ser API 26-29 (legacy), en su lugar:
```
tools/adb.exe -s RG556006101273 shell dumpsys package com.retrovault.android | grep -E "READ_EXTERNAL_STORAGE|WRITE_EXTERNAL_STORAGE" -A1
```
Busca `granted=true` en ambos.

**[Manual, pantalla física]** Abre la app Retro Vault Sync en la consola.
- Si el permiso NO está concedido, debe mostrar una pantalla de onboarding pidiéndolo explícitamente (no debe intentar escanear silenciosamente y fallar). Toca el botón de conceder — te lleva a Ajustes del sistema (`ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION`), activa el toggle "Permitir acceso para gestionar todos los archivos" y vuelve atrás con el botón físico/gesto de retroceso.
- Si el dispositivo es Android 13+ (API 33+), debe aparecer también el prompt runtime de `POST_NOTIFICATIONS` — acéptalo.
- Re-lanza la app: debe ir directa a la pantalla principal (Estado/Ajustes), sin volver a pedir permisos.

**Bien:** `appops get` → `allow` (o legacy `granted=true` en ambos), la app no vuelve a mostrar la pantalla de permisos al reabrir, y un "Sincronizar ahora" manual no falla.
**Mal:**
- `appops get` sigue en `default` tras "conceder" en pantalla → revisa que tocaste el toggle correcto en Ajustes del sistema (hay dos pantallas similares en Android, "Acceso a todos los archivos" es la que importa, no permisos normales de la app).
- La app no muestra pantalla de onboarding y en su lugar falla en silencio al escanear → mirar `adb logcat -d | grep -iE "retrovault|SecurityException"` justo tras abrir la app; probable falta de chequeo de permiso antes de `LocalFileScanner` (Roadmap §3, tabla de permisos).

---

## 2. Anidado por-core real

**[ADB]** Verificar el layout físico real en el dispositivo (esto es lo único que se puede confirmar solo con hardware, ver Roadmap §7):
```
tools/adb.exe -s RG556006101273 shell find /storage/emulated/0/RetroArch/saves -maxdepth 2
tools/adb.exe -s RG556006101273 shell find /storage/emulated/0/RetroArch/states -maxdepth 2
```
Salida esperada: subcarpetas con nombre de core (p. ej. `saves/Beetle PSX/`, `saves/SNES9x/`, `saves/mGBA/`), y dentro de cada una los archivos de save reales. Si en cambio ves los `.srm`/`.state` directamente bajo `saves/` sin subcarpeta, "sort by core" no está realmente aplicado en esta build/firmware pese al ajuste de RetroArch — anótalo, es un hallazgo sobre el firmware, no un bug de la app.

**[Manual]** En la app, pulsa "Sincronizar ahora" en la pantalla de Estado tras confirmar que hay saves nested.

**[ADB]** Revisa el log de eventos que generó ese sync (pantalla de estado en la app muestra lo mismo, pero para capturarlo con precisión):
```
tools/adb.exe -s RG556006101273 logcat -d -t 300 | grep -i "SyncEngine\|uploaded\|relative"
```

**Bien:** las rutas que se loguean/muestran en el evento incluyen el segmento de carpeta del core (p. ej. `Beetle PSX/ChronoTrigger.srm` subido), y al revisar Dropbox (app o web, carpeta `/RetroSync/saves`) aparece la misma estructura anidada, no aplanada.
**Mal:**
- Localmente los archivos están anidados pero en Dropbox aparecen todos sueltos en la raíz de `saves/` (p. ej. `ChronoTrigger.srm` sin `Beetle PSX/` delante) → bug real en la construcción de `relative`/path remoto → mirar `android/app/src/main/java/com/retrovault/android/sync/LocalFileScanner.kt` (cálculo de `relative` respecto a `saves_dir`) y `RemoteRouter.kt` (espejo de `rclone_transport.py:290,415`).
- Colisión de nombres entre cores (dos juegos con el mismo nombre de archivo en cores distintos) que se pisan en Dropbox → mismo punto del código, confirma que el `relative` incluye SIEMPRE el nombre de core, nunca solo el nombre de archivo.

---

## 3. Round-trip cruzado con `rommgr sync-saves` (la prueba central)

### 3a. Android → PC

**[Manual]** Juega un rato en la RG556 y crea/actualiza un save o savestate real (que quede con mtime nuevo).

**[Manual o ADB]** Dispara el sync: espera el modo instantáneo (unos segundos tras el debounce de ~1.5s) o pulsa "Sincronizar ahora" en la app.

**[ADB]** Confirma en el dispositivo que el contador de "Subidos" incrementó y "Errores: 0" en la pantalla de Estado (visual, o vía logcat):
```
tools/adb.exe -s RG556006101273 logcat -d -t 200 | grep -i "SyncResult\|uploaded"
```

**[PC]** Ejecuta el sync del lado PC:
```
rommgr sync-saves
```
**Qué esperar ver:** en la salida del comando, una entrada de descarga (`downloaded: 1` o equivalente) correspondiente exactamente al archivo que acabas de guardar en la consola, con la misma ruta relativa (incluida la carpeta de core) dentro de la carpeta local de saves del PC.

### 3b. PC → Android

**[Manual/PC]** Genera un save nuevo o modificado desde el lado PC (otra partida en RetroArch de PC, o cualquier archivo dentro de `save_extensions`/`state_extensions` con mtime nuevo dentro de la carpeta de saves del PC).

**[PC]**
```
rommgr sync-saves
```
Esperado: `uploaded: 1` en la salida, referido a ese archivo.

**[ADB/Manual]** En la consola, espera el ciclo periódico (hasta 15 min) o fuerza "Sincronizar ahora". Verifica que el archivo llegó:
```
tools/adb.exe -s RG556006101273 shell ls -la "/storage/emulated/0/RetroArch/saves/<core>/"
```
y que el contador "Descargados" de la app incrementó.

### 3c. Idempotencia / sin duplicados ni conflictos falsos

**[PC + Manual]** Sin tocar ningún archivo, repite inmediatamente `rommgr sync-saves` en el PC y "Sincronizar ahora" en la app. Ambos deben reportar 0 subidos / 0 descargados / 0 conflictos (up-to-date).

**[ADB]** Confirma que no se crearon archivos de conflicto espurios:
```
tools/adb.exe -s RG556006101273 shell find /storage/emulated/0/RetroArch -name "*.conflict-*"
```
Debe salir vacío. Revisa también la carpeta de saves del PC y el listado de Dropbox (web) por si hay algún `.conflict-<timestamp>` inesperado.

**Bien:** propagación en ambos sentidos correcta, contadores coinciden con lo esperado, cero archivos `.conflict-*` cuando solo un lado cambió, y una segunda pasada inmediata en ambos lados da 0/0/0.

**Mal — dónde mirar:**
| Síntoma | Causa probable | Dónde mirar |
|---|---|---|
| El PC no ve nunca el save subido desde Android | Paths de `saves_remote`/`states_remote` no coinciden entre `config.toml` (PC) y Ajustes (app) | Roadmap §1, recorte del prefijo `remotename:` en Ajustes de la app |
| Conflicto falso en cada sync aunque solo cambió un lado | mtime mal fijado: la app está leyendo/escribiendo `server_modified` en vez de `client_modified` de Dropbox | `DropboxTransport.kt` (`withClientModified`/`getClientModified()`) vs `rclone_transport.py:471-489` |
| Archivo duplicado con ruta ligeramente distinta (mayúsculas, separador, con/sin carpeta de core) | Construcción de `relative` distinta entre PC y Android | `LocalFileScanner.kt`/`RemoteRouter.kt` vs `rclone_transport.py:290,415`, `save_syncer.py:66` |
| La app Android nunca descarga lo que subió el PC en modo periódico | `WorkManager` no se está ejecutando o falta conectividad | `adb shell dumpsys jobscheduler \| grep -i retrovault`; confirmar `NetworkType.CONNECTED` satisfecho (WiFi activo) |

---

## 4. Comportamiento tras reboot

**[Manual]** En Ajustes de la app, pon el modo de sync en "Instantáneo" o "Ambos" (el modo foreground+FileObserver es el que depende del boot receiver; el periódico sobrevive solo via WorkManager).

**[ADB]** Reinicia el dispositivo:
```
tools/adb.exe -s RG556006101273 reboot
```
**Aviso:** esto reinicia la consola física completa, cierra cualquier juego en curso.

**[ADB]** Espera a que vuelva a estar disponible:
```
tools/adb.exe -s RG556006101273 wait-for-device
tools/adb.exe -s RG556006101273 shell getprop sys.boot_completed
```
Repite el segundo comando hasta que devuelva `1`.

**[ADB, sin abrir la app manualmente]**
```
tools/adb.exe -s RG556006101273 shell dumpsys activity services com.retrovault.android
```
**Qué esperar ver:** `SyncForegroundService` listado como servicio en ejecución, sin que hayas tocado la pantalla de la consola.

**[Manual]** Desliza la barra de notificaciones en la pantalla física de la RG556 — debe aparecer la notificación persistente "Retro Vault — vigilando saves" sin haber abierto la app tras el reboot.

**[ADB, justo tras el reboot antes de que rote el buffer de log]**
```
tools/adb.exe -s RG556006101273 logcat -d -t 300 | grep -i "BootRestartReceiver"
```
Debe verse el receiver disparándose y arrancando el servicio.

**[Manual]** Juega y genera un save nuevo sin abrir la app en ningún momento; repite una versión ligera del punto 3a para confirmar que ese save sigue subiendo solo.

**Bien:** notificación presente tras reboot sin intervención, servicio listado en `dumpsys`, log del receiver disparándose, y el save post-reboot sincroniza igual que antes.
**Mal:**
- No hay notificación / servicio no listado → revisar que `AndroidManifest.xml` registra el receiver para `BOOT_COMPLETED` y que `RECEIVE_BOOT_COMPLETED` está concedido (`adb shell dumpsys package com.retrovault.android | grep RECEIVE_BOOT_COMPLETED`).
- El receiver se dispara pero el servicio crashea justo después → revisar `adb logcat -d -t 300 | grep -i retrovault` buscando excepciones al arrancar — causa típica descrita en Roadmap §7: el almacenamiento externo aún no está montado en el instante exacto del `BOOT_COMPLETED`.
- Si el modo era solo "Periódico": no debe aparecer notificación ni servicio foreground (comportamiento correcto, WorkManager no necesita receiver) — confirma en su lugar que el worker periódico sigue programado: `adb shell dumpsys jobscheduler | grep -i retrovault`.

---

## 5. Consumo de batería (spot-check, no prueba de horas)

**[Manual]** Desconecta el cable USB de la RG556 (si tu setup de ADB depende del cable, puedes reconectarlo solo para leer las stats al final; el reinicio de stats y la sesión de juego deben ser con la consola a batería, no cargando).

**[ADB, antes de la sesión, con USB puesto momentáneamente]**
```
tools/adb.exe -s RG556006101273 shell dumpsys batterystats --reset
```

**[Manual]** Juega ~20-30 min con el modo de sync "Instantáneo" activo (uso representativo: guarda partida varias veces durante la sesión).

**[ADB, al terminar]**
```
tools/adb.exe -s RG556006101273 shell dumpsys batterystats com.retrovault.android
```
Busca la sección "Estimated power use"/consumo estimado para `com.retrovault.android`, y el tiempo de wakelock/"Awake" de la app.

**[Manual, opcional para tener referencia]** Repite una sesión de duración similar con el modo de sync en "Apagado" o "Periódico" para tener un baseline de comparación.

**Bien:** el consumo estimado de Retro Vault es una fracción pequeña frente al consumo total de la sesión (no debería competir con el propio emulador/core como principal consumidor), y el wakelock/tiempo "despierto" es intermitente (segundos por evento de guardado + el rescan cada 10-15 min), no continuo durante toda la sesión.
**Mal:** Retro Vault aparece como consumidor top comparable o superior al emulador, o mantiene un wakelock activo durante toda la sesión → indica que el `FileObserver`/debounce no está funcionando (se dispara un sync completo en bucle) o que hay reintentos agresivos contra la API de Dropbox en error → revisar el debounce (~1.5s) en `SaveFileObserverManager.kt` y el intervalo de rescan de seguridad (10-15 min) en `SyncForegroundService.kt`, y buscar excepciones repetidas en `adb logcat -d | grep -i retrovault`.

---

## Verificaciones finales

- [ ] Pantalla de Estado de la app: última sincronización reciente, contadores acumulados coherentes con las pruebas hechas, sin errores.
- [ ] `tools/adb.exe -s RG556006101273 shell find /storage/emulated/0/RetroArch -name "*.conflict-*"` vacío al final de toda la sesión de pruebas.
- [ ] Dropbox (web o app) muestra la misma estructura `saves/<core>/...` y `states/<core>/...` que el dispositivo y que el PC, sin archivos sueltos fuera de sitio.
- [ ] `rommgr sync-saves` en el PC, ejecutado una última vez, reporta 0/0/0 (todo ya converge).

## Resultado esperado al finalizar

Un save o savestate escrito en la RG556 (con la app en modo Instantáneo, Periódico o tras un reboot) aparece en el PC tras `rommgr sync-saves` sin intervención manual más allá de jugar y guardar; lo mismo en sentido inverso. Los permisos de almacenamiento quedan concedidos de forma persistente sin repreguntar en cada arranque de la app. La estructura de carpetas por-core se preserva en las tres puntas (dispositivo, Dropbox, PC) sin aplanarse. Tras un reboot, el servicio se relanza solo si el modo instantáneo estaba activo, sin que el usuario tenga que reabrir la app. El consumo de batería del servicio de sync es marginal frente al de jugar, sin wakelocks continuos.

## Nota de alcance (2026-08-18)

El diseño recortado de `ANDROID-SYNC` (ver `Tareas/backlog.md`) descartó
explícitamente el modo instantáneo (`FileObserver`/foreground service,
tareas 9-11) — la app cubre sync manual + periódico cada 15 min, no un
servicio en segundo plano permanente. **Antes de ejecutar el punto 4
(reboot) y partes del punto 2/5 de este checklist tal cual están escritas
(que asumen `SyncForegroundService`/`BootRestartReceiver`/modo
"Instantáneo"), confirmar contra el código real de esta build qué modos
existen de verdad** — si el recorte de alcance sigue vigente en la versión
instalada (0.1.0), esas piezas no existen y esos pasos hay que adaptarlos a
"sync periódico + manual" únicamente (ver `ANDROID-SYNC-12`, WorkManager).
