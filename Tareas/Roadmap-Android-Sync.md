# App Android nativa de sync de saves (Retro Vault)

> Diseñado 2026-08-18. Ver `Tareas/backlog.md` sección `ANDROID-SYNC` para
> la tabla de tareas con estado actualizado — este documento es el detalle
> de diseño, no se edita tarea a tarea.

## Contexto

Hoy el sync de saves entre el PC y la Anbernic RG556 depende de que el PC
esté encendido (`rommgr sync-saves` / cable/cloud sync desde la web app), o
de un script Termux+rclone en la propia consola
(`docs/sync/Guia-Termux-Anbernic.md`, generado dinámicamente por
`src/rom_manager/web/handlers/sync_cloud.py:725` vía `/s`) que solo se
autoejecuta una vez al arrancar (Termux:Boot) — si juegas sin reiniciar, los
saves no suben hasta el próximo boot o un `~/sync-saves.sh` manual.

Objetivo del usuario: que el sync de saves sea lo más automático posible, y
que no dependa de que el PC esté encendido. Decisión tomada: construir una
**app Android nativa** instalada en la propia consola que sincronice
directamente con Dropbox, sustituyendo al script Termux.

Decisiones confirmadas con el usuario (2026-08-18):
1. **Background**: ambos modos, configurable — servicio en primer plano con
   `FileObserver` (sync casi instantáneo, notificación persistente discreta)
   y `WorkManager` periódico (cada 15 min, sin notificación).
2. **Dropbox**: SDK oficial de Dropbox API v2 para Android, OAuth nativo en
   la app (navegador del sistema, sin copiar tokens a mano) vía PKCE.
3. **Repo**: carpeta nueva `android/` dentro de este mismo repo.
4. **Distribución**: APK sideload / `adb install`, sin Google Play.
5. **Package/App ID**: `com.retrovault.android`.
6. **Permisos de storage**: `MANAGE_EXTERNAL_STORAGE` (no SAF).
7. **Persistencia local**: Room/SQLite (no JSON plano) — el servicio
   foreground y el WorkManager periódico pueden disparar sync casi a la vez;
   SQLite evita carreras que un JSON plano no evita gratis.
8. **minSdk**: bajo, pensando en otras consolas Android además de la RG556
   (no solo API 33) — fijado en **API 26 (Android 8.0)** al implementar
   ANDROID-SYNC-1: cubre virtualmente todas las handhelds retro Android
   modernas (RG35XX H, Odin2, Retroid Pocket, la propia RG556...) sin cargar
   con compatibilidad para versiones realmente antiguas. Ver §3 para el
   manejo de compatibilidad multi-versión que esto exige (API 26 vs 29 vs 30
   vs 33 vs 34 tienen comportamientos distintos relevantes aquí).

**Lo más importante de este plan**: la app debe ser un **peer compatible**
del sync Python existente (`src/rom_manager/sync/`) — mismos paths remotos,
misma semántica de mtime, misma lógica de conflictos — para que lo que suba
el móvil y lo que sincronice `rommgr sync-saves` en el PC se vean como "el
mismo archivo" por ambos lados, sin duplicados ni sync fights.

---

## 1. Contrato de sync a replicar (verificado en el código real)

**Construcción del path remoto** (`src/rom_manager/sync/rclone_transport.py:290,415`,
`save_syncer.py:66`):
```python
relative = local_path.relative_to(saves_dir).as_posix()
remote_dest = f"{chosen_remote.rstrip('/')}/{relative}"
```
Plano, separado por `/`, sin anidar por emulador más allá de lo que el
propio RetroArch cree (p. ej. `saves/SNES9x/Chrono Trigger.srm`).

**Precedencia de routing por extensión** (`rclone_transport.py::_resolve_remote()`,
líneas 61-71): **`state_extensions` se comprueba antes que `save_extensions`**.
Varias extensiones aparecen en ambas listas (`.state`, `.fcs`, `.sps`, `.psv`,
`.hi`, `.brmc`, `.ml1`) — para esas, gana `states_remote`. En Android esto es
menos relevante porque `saves/` y `states/` ya son carpetas físicamente
separadas en el dispositivo (RetroArch las escribe así), pero se mantiene
`RemoteRouter` como espejo exacto de la lógica del PC, por paridad y para el
merge de listados remotos (ver más abajo).

**Extensiones** (`src/rom_manager/config.py:544-576`), constantes Kotlin
byte-a-byte idénticas a las del PC:
- `save_extensions`: `.sav .srm .state .st0 .st1 .st2 .st3 .st4 .st5 .fcs .dsv .sps .psv .mcr .mem .vmp .eep .fla .sra .sgm .brm .nv .hi .state1 .state2 .brmc .ml1 .mcd .ps2 .gci`
- `state_extensions`: `.state .state1 .state2 .st0 .st1 .st2 .st3 .st4 .st5 .ppst .fcs .sps .psv .hi .brmc .ml1`

**Orden de merge de listados remotos** (`save_syncer.py:101-112`): se listan
primero las entradas de `saves_remote` en un dict y luego se hace `.update()`
con las de `states_remote` — si colisiona el mismo `relative`, gana la
entrada de `states_remote`. Replicar este mismo orden en el motor Android.

**Convención de config** (`config.toml.example:33-35`, generador canónico
`sync_cloud.py:733-739,802-803`): `saves_remote = "dropbox:/RetroSync/saves"`,
`states_remote = "dropbox:/RetroSync/states"`. **Detalle importante**: el
prefijo `dropbox:` es el nombre del remote de *rclone*, no parte del path
real de Dropbox — rclone lo quita antes de hablar con la API. Como la app
Android habla con la API de Dropbox directamente (sin rclone), el campo de
Ajustes debe guardar solo el path relativo a Dropbox (`/RetroSync/saves`),
pero debe aceptar un valor pegado tal cual del `config.toml` del PC y
recortar automáticamente todo hasta el primer `:` — si no, un usuario que
copia/pega su valor del PC se encuentra con un path roto.

**Raíces en el dispositivo** (`config.py:18-19,186`):
`/storage/emulated/0/RetroArch/saves` y `/storage/emulated/0/RetroArch/states`,
anidadas por carpeta de core cuando "sort saves by core" está activo en
RetroArch. Hay que recorrerlas recursivamente.

**Semántica de mtime** (`rclone_transport.py:471-489`, backend Dropbox de
rclone): el mtime que usa rclone es el `client_modified` de Dropbox, **no**
`server_modified`. El SDK de Dropbox para Android expone esto directamente:
`FileMetadata.getClientModified()` al listar/descargar, y
`uploadBuilder(path).withClientModified(Date)` al subir. La app debe fijar
siempre `client_modified` = `file.lastModified()` local al subir, y leer
siempre `client_modified` (nunca `server_modified`) al listar — si esto
falla, todas las comparaciones de mtime contra archivos sincronizados por el
PC son incorrectas.

**Resolución de conflictos** (`src/rom_manager/sync/conflict_resolver.py:16-55`,
`decide()`, verificado línea a línea):
- Un lado ausente → upload/download trivial.
- Ambos presentes + hay `last_sync_at` conocido: si **ambos** mtimes son
  posteriores a `last_sync_at` por más de `tolerance_seconds` (2s) →
  **conflict**.
- Si no: `abs(local_mtime - remote_mtime) <= 2s` → up_to_date; si no, gana
  el más nuevo (`upload` si local es más nuevo, `download` si lo es el
  remoto).
- Política por defecto en contexto background: `"newest"` — el perdedor se
  respalda con sufijo `.conflict-<timestamp>` antes de sobrescribir
  (`save_syncer.py:293-355`). v1 de la app Android solo implementa `newest`
  (igual que el default del PC en background); `keep_pc`/`keep_android`/`ask`
  quedan fuera de alcance v1, añadibles después exponiendo el mismo enum en
  Ajustes.
- Clave del watermark: por `(relative, remote_root)`, no solo `relative`
  (`sync_log.py:100-121`) — así, si el usuario cambia el path de Dropbox en
  Ajustes, no se reutiliza un watermark obsoleto contra un remote distinto.

**Delta cache** (`delta_cache.py`): optimización local — SHA1 del último
contenido sincronizado por `relative`, para saltar el upload si el contenido
no cambió aunque el mtime sí (común cuando un emulador toca el archivo sin
escribir datos nuevos). No es necesaria para la corrección, solo para
eficiencia — Fase 5.

---

## 2. Estructura del proyecto (`android/`)

```
android/
├── settings.gradle.kts              # incluye ":app"
├── build.gradle.kts                 # raíz: solo versiones de plugins
├── gradle.properties
├── gradle/wrapper/...
├── local.properties.example         # plantilla de SDK path
├── README.md                        # cómo abrir en Android Studio
└── app/
    ├── build.gradle.kts             # applicationId com.retrovault.android, Compose, Dropbox SDK, Room, WorkManager
    ├── proguard-rules.pro
    └── src/
        ├── main/
        │   ├── AndroidManifest.xml
        │   ├── java/com/retrovault/android/
        │   │   ├── RetroVaultApp.kt              # Application: WorkManager Configuration.Provider
        │   │   ├── data/
        │   │   │   ├── db/
        │   │   │   │   ├── AppDatabase.kt
        │   │   │   │   ├── SyncCacheEntity.kt      # (relative_path, remote_root) → último hash/mtime/rev
        │   │   │   │   ├── SyncCacheDao.kt
        │   │   │   │   ├── SyncEventEntity.kt       # historial para la pantalla de estado
        │   │   │   │   └── SyncEventDao.kt
        │   │   │   ├── prefs/SettingsRepository.kt  # DataStore: remotes, modo de sync, último sync
        │   │   │   └── auth/
        │   │   │       ├── DropboxAuthManager.kt    # PKCE, EncryptedSharedPreferences
        │   │   │       └── DropboxClientProvider.kt
        │   │   ├── sync/
        │   │   │   ├── SaveExtensions.kt             # constantes save_extensions/state_extensions
        │   │   │   ├── RemoteRouter.kt                # espejo de _resolve_remote()
        │   │   │   ├── LocalFileScanner.kt             # recorrido recursivo → LocalSave
        │   │   │   ├── DropboxTransport.kt             # list/upload/download con client_modified
        │   │   │   ├── ConflictResolver.kt             # espejo de decide(), tolerancia 2s
        │   │   │   ├── SyncEngine.kt                   # orquesta un pase completo → SyncResult
        │   │   │   └── DeltaCache.kt                   # Fase 5
        │   │   ├── service/
        │   │   │   ├── SyncForegroundService.kt
        │   │   │   ├── SaveFileObserverManager.kt      # multi-path FileObserver + fallback pre-API29
        │   │   │   ├── BootRestartReceiver.kt
        │   │   │   └── SyncWorker.kt                   # CoroutineWorker, modo periódico
        │   │   └── ui/
        │   │       ├── MainActivity.kt
        │   │       ├── settings/SettingsScreen.kt
        │   │       └── status/SyncStatusScreen.kt
        │   └── res/...
        ├── test/                    # unit tests JVM: RemoteRouter, ConflictResolver, paths — sin dispositivo
        └── androidTest/             # instrumentados: FileObserver, Room, WorkManager (emulador)
```

---

## 3. Modelo de permisos (compatibilidad multi-versión, minSdk 26)

| Permiso | Propósito | Rama por versión |
|---|---|---|
| `MANAGE_EXTERNAL_STORAGE` | Acceso recursivo a `saves/`/`states/` desde background | **API 30+**: permiso especial, redirect a Ajustes vía `ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION` |
| `WRITE_EXTERNAL_STORAGE`/`READ_EXTERNAL_STORAGE` + `android:requestLegacyExternalStorage="true"` | Mismo acceso en versiones antiguas | **API 26-29**: scoped storage no aplicaba aún; permiso runtime clásico + el flag legacy en el manifest |
| `POST_NOTIFICATIONS` | Notificación persistente del servicio foreground | **Solo API 33+** — versiones anteriores no lo requieren, no pedir el runtime prompt si `Build.VERSION.SDK_INT < 33` |
| `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_DATA_SYNC` | Servicio de sync instantáneo | `FOREGROUND_SERVICE_DATA_SYNC` es **API 34+**; en versiones anteriores basta `FOREGROUND_SERVICE` sin el tipo específico |
| `RECEIVE_BOOT_COMPLETED` | Relanzar el servicio foreground tras reboot si el modo instantáneo estaba activo | Todas las versiones |
| `INTERNET`, `ACCESS_NETWORK_STATE` | Llamadas a la API de Dropbox; constraint `NetworkType.CONNECTED` de WorkManager | Todas |
| Intent-filter de esquema `db-<APP_KEY>://2/token` | Captura del redirect OAuth PKCE de Dropbox | Todas |

`FileObserver`: el constructor multi-path `FileObserver(List<File>, int)`
(un solo fd de inotify para todas las subcarpetas) solo existe desde API 29.
En API 26-28, `SaveFileObserverManager` cae a registrar una instancia del
constructor `FileObserver(String, int)` (deprecado pero funcional) por cada
subcarpeta conocida — mismo comportamiento funcional, sin ventaja de "un
solo fd" pero sin limitación real dado el número modesto de subcarpetas
(pocas decenas de cores, no miles de directorios).

---

## 4. Motor de sync (`SyncEngine.runSync()`)

1. `LocalFileScanner` recorre `saves/` y `states/`, filtrando solo a
   extensiones en `state_extensions ∪ save_extensions` (espejo del filtro
   `ext_set` de `list_local_saves()` — nunca recoge archivos de extensión
   desconocida).
2. `DropboxTransport.listFolderRecursive(savesRemote)` y luego
   `listFolderRecursive(statesRemote)`, fusionando en un solo mapa por
   `relative` — **las entradas de `statesRemote` sobrescriben** las de
   `savesRemote` en caso de colisión (mismo orden que `save_syncer.py:105-112`).
3. Unión de claves `relative` locales ∪ remotas → por cada una, se busca el
   watermark Room `(relative, remoteRoot)` y se llama a
   `ConflictResolver.decide(localMtime, remoteMtime, lastSyncAt, tolerance=2s)`
   — puerto 1:1 de `conflict_resolver.py`.
4. Aplicar:
   - `upload` → `DropboxTransport.upload(local, relative, remote)` con
     `withClientModified(file.lastModified())`.
   - `download` → escribir el archivo y luego `File.setLastModified(remoteClientModified)`
     para que el próximo escaneo local reporte el mtime correcto.
   - `conflict` → política `newest`, respaldo del perdedor como
     `<nombre>.conflict-<timestamp>` antes de sobrescribir (espejo de
     `save_syncer.py:293-355`).
5. Tras cada transferencia, upsert del watermark Room (y, Fase 5, del hash
   del delta-cache).
6. Devuelve `SyncResult(uploaded, downloaded, upToDate, conflicts, errors, deltaSkipped)`,
   consumido por la pantalla de estado.

---

## 5. Mecanismos de background

**Modo instantáneo (servicio foreground)**: `SyncForegroundService` arranca
`SaveFileObserverManager`, que enumera subcarpetas y registra el
`FileObserver` (multi-path en API 29+, uno por carpeta si es anterior) para
`CREATE|MODIFY|CLOSE_WRITE|MOVED_TO|DELETE`. Eventos debounced por archivo
(~1.5s, porque un core puede escribir un save en varias operaciones
pequeñas) antes de disparar `SyncEngine.runSync()` (empezar con "cualquier
evento dispara un pase incremental completo" — el motor ya es incremental
por mtime, optimizar a sync de un solo archivo más adelante solo si hace
falta por batería/rendimiento). La creación de una carpeta nueva a nivel
raíz dispara re-enumeración. Rescan de seguridad cada 10-15 min incluso con
el servicio activo (inotify puede perder eventos bajo carga). Notificación
persistente de baja prioridad: "Retro Vault — vigilando saves" +
última sincronización.

**Modo periódico (WorkManager)**: `SyncWorker` (`CoroutineWorker`) como
`PeriodicWorkRequest`, intervalo mínimo de Android (15 min),
`NetworkType.CONNECTED`, llama a `SyncEngine.runSync()` una vez, sin
notificación salvo fallo.

Ajustes permite elegir: Apagado / Instantáneo / Periódico / Ambos — "Ambos"
es válido, el periódico actúa de red de seguridad para lo que el
`FileObserver` pudiera perder (los pases de `SyncEngine` son idempotentes).

`WorkManager` sobrevive a un reboot automáticamente (receiver interno
propio). El servicio foreground con `FileObserver` **no** — Android mata
todos los servicios al reiniciar. `BootRestartReceiver`
(`RECEIVE_BOOT_COMPLETED`) relanza el servicio si el modo instantáneo estaba
activo — si no, la promesa de "automático, sin depender del PC" se rompe
igual que con el script Termux:Boot que esta app sustituye.

---

## 6. Ajustes / UI (v1, mínima)

- **Conectar/desconectar Dropbox**: un botón, OAuth PKCE vía navegador del
  sistema, muestra la cuenta conectada una vez enlazada.
- **Selector de modo de sync**: Apagado / Instantáneo / Periódico / Ambos.
- **Paths remotos**: dos campos de texto, prerellenados con
  `/RetroSync/saves` y `/RetroSync/states`, aceptando un valor pegado estilo
  rclone (`dropbox:/RetroSync/saves`) y recortando automáticamente el
  prefijo `remotename:` al guardar.
- **Pantalla de estado**: última sincronización, últimos contadores
  (subidos/descargados/conflictos/errores), botón manual "Sincronizar
  ahora" (corre un pase de `SyncEngine` sin importar el modo configurado),
  lista breve de eventos recientes desde `SyncEventEntity`.

Sin mecanismo de QR/emparejamiento en v1 — el path de Dropbox ya es una
convención documentada y fija, así que un pegado manual una sola vez es
fricción suficientemente baja.

---

## 7. Estrategia de testing — qué se puede validar ya vs qué espera al hardware

**Sin dispositivo, tests JVM (`app/src/test/`)**:
- Precedencia de `RemoteRouter` (state-antes-que-save, solape) contra las
  listas de extensión exactas.
- `ConflictResolver.decide()` — portar los casos existentes de
  `test_save_syncer.py`/conflict-resolver del PC como equivalentes Kotlin,
  incluyendo los bordes de tolerancia de 2s y el caso "ambos cambiaron desde
  el último sync → conflict".
- Cálculo de `relative` y construcción del path remoto (rstrip, join).
- Recorte del prefijo `remotename:` en los campos de Ajustes.
- DAOs de Room vía Robolectric o una BD Room en memoria (sigue siendo
  JVM-only).

**Con emulador Android (imagen API 26+), sin necesitar la RG556 física**:
- Registro multi-path de `FileObserver` y detección de subcarpeta nueva.
- Flujo de concesión de `MANAGE_EXTERNAL_STORAGE` / legacy storage,
  `POST_NOTIFICATIONS` (solo si API ≥ 33).
- Programación/constraints de `WorkManager` periódico (`TestListenableWorkerBuilder`,
  sin dispositivo real).
- Round-trip OAuth PKCE de Dropbox contra una cuenta de prueba real.

**Bloqueado hasta tener la RG556 física** (mismo patrón que
`CFG-PORGAME-10`/`STORAGE-MGR` Frente A en `Tareas/backlog.md` y
`Tareas/Roadmap-212-Ideas-Futuras.md` — documentar el checklist ahora,
ejecutar cuando haya consola a mano):
- Confirmar que el anidado real por-core de RetroArch en esta build/firmware
  coincide con lo asumido (`saves/SNES9x/...`).
- Impacto en batería/temperatura del servicio foreground + inotify en una
  sesión de juego larga real.
- Interop real: el PC sube un save vía `rommgr sync-saves`, la app Android
  lo recoge (modo instantáneo y periódico), y viceversa — la prueba de
  correctitud cruzada que es la razón de ser de esta app.
- Comportamiento tras un reboot real del dispositivo (timing del boot
  receiver, disponibilidad de storage al arrancar).

---

## 8. Nota sobre el entorno de desarrollo

Ninguna de las dos máquinas de desarrollo tenía Android Studio instalado. En
vez de instalar el IDE completo, se instalaron solo las herramientas de
línea de comandos necesarias para compilar y testear de verdad (no solo
revisión de código): JDK 17 (Temurin), Android SDK command-line tools
(`platform-tools`, `platforms;android-34`, `build-tools;34.0.0`) y Gradle
8.7 — todo portable, fuera del repo, no versionado. Con eso se generó el
Gradle Wrapper real del proyecto (`android/gradlew`, versionado).

- PC 1 (`Ruben`): toolchain en `C:\Users\Ruben\android-build-tools\`;
  verificó `ANDROID-SYNC-1` con `./gradlew assembleDebug`/`test` reales.
- PC 2 (`rammu`): toolchain en `C:\Users\rammu\android-build-tools\`
  (2026-08-18, mismo procedimiento: JDK 17 vía API de Adoptium y Android
  cmdline-tools 22.0 vía `dl.google.com`, checksum SHA1 verificado);
  verificó `ANDROID-SYNC-12` con `./gradlew test` y `./gradlew assembleDebug`
  reales, ambos en verde.

`android/local.properties` (gitignored) apunta al `sdk.dir` de cada máquina
— no versionado, cada desarrollador genera el suyo desde
`local.properties.example`. Sigue haciendo falta Android Studio (o un
emulador arrancado a mano) para lo que este toolchain de línea de comandos
no cubre: instrumented tests (`connectedAndroidTest`), previews de Compose,
y probar la app instalada de verdad en un emulador/dispositivo. Cada PR de
fase debe seguir dejando constancia explícita de qué se verificó por
compilación/tests reales y qué quedó solo por revisión de código.

---

## 9. Verificación end-to-end (cuando haya entorno Android)

- **Fases 0-2**: `./gradlew test` (JVM, sin emulador) para
  `RemoteRouter`/`ConflictResolver`/paths — deben pasar en verde antes de
  cada PR de esas fases. `./gradlew assembleDebug` debe compilar sin errores
  en cada fase.
- **Fases 3-4**: `./gradlew connectedAndroidTest` contra un emulador (imagen
  API 26+) para `FileObserver`/`WorkManager`/permisos. Instalar el APK debug
  (`adb install -r app-debug.apk`) en el emulador y verificar manualmente el
  flujo de conexión Dropbox + un sync de ida y vuelta contra una cuenta de
  prueba.
- **Fase 6 (cuando haya RG556)**: seguir el checklist de ANDROID-SYNC-15;
  criterio de "hecho" = un save escrito en la Anbernic aparece en el PC (y
  viceversa) sin duplicados ni conflictos falsos, tras un ciclo completo
  instantáneo y uno periódico, y tras un reboot del dispositivo.
