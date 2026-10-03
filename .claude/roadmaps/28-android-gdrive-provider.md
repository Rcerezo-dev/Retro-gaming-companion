# Roadmap 28 — Google Drive como proveedor alternativo en Android

**Rama:** sin asignar — se corta `feature/android-drive-1-cloud-transport` (o
similar) cuando arranque la Fase 1.
**Base:** `develop`
**Prioridad:** 🟡 P3 — mejora de robustez del Pilar 3 (más opciones de
proveedor), no un bloqueante activo hoy. Reevaluar prioridad si
`ANDROID-SYNC-CRITICAL-1` (causa raíz 3, scopes de Dropbox) sigue sin
resolverse varias sesiones más.
**Esfuerzo estimado:** L (varias sesiones) — desglose por fase abajo.
**Riesgo:** Medio — toca autenticación (superficie de seguridad) y el motor
de sync que ya protege partidas reales; cada fase debe mantener Dropbox
funcionando sin cambios de comportamiento mientras se construye Drive en
paralelo.

---

## Origen y motivación

`ANDROID-DRIVE-1` (`Tareas/backlog.md`, sección `ANDROID-SYNC`, hallazgo
2026-09-25): la app Dropbox de Android (modo Desarrollo) tiene un tope de
usuarios autorizados que se llena con cada ciclo de reconexión/prueba
(`ANDROID-SYNC-CRITICAL-1`, "This app has reached its user limit"). Añadir
Google Drive como alternativa evitaría depender de ese límite.

**Contexto que cambia la urgencia real (2026-09-28)**: de las 3 causas raíz
de `ANDROID-SYNC-CRITICAL-1`, la 1 (cuenta equivocada) y la 2 (App folder vs
Full Dropbox) ya están resueltas. Solo queda la 3 (faltan scopes de archivo
en la pestaña Permissions de la App Console de Dropbox) — un solo clic del
usuario, no un límite estructural. Si se resuelve, la motivación original de
"Dropbox se queda sin cupo" pierde peso. Este roadmap se documenta igual
como **plan disponible**, no como trabajo comprometido para hoy — decisión
de priorizarlo o no, sesión a sesión.

---

## Estado actual (verificado contra el código real, no asumido)

### Lado PC — ya es agnóstico de proveedor, gratis

`web/handlers/cloud_auth.py` — `_PROVIDERS = {"dropbox": ("dropbox",
"dropbox"), "gdrive": ("drive", "gdrive")}`, todo delega en `rclone
authorize <provider>`. gdrive ya funciona en el PC hoy, sin código nuevo,
solo eligiendo el provider en el wizard OAuth de la UI (`sync.js`/
`tab-sync.html`).

### Lado Android — todo es Dropbox-específico

| Pieza | Archivo | Por qué no es agnóstica |
|---|---|---|
| Transporte | `sync/DropboxTransport.kt` | Usa `DbxClientV2` (SDK de Dropbox) directamente — `listFolderRecursive`/`upload`/`download` llaman a la API de Dropbox, no hay interfaz intermedia |
| Auth | `data/auth/DropboxAuthManager.kt` | `Auth.startOAuth2PKCE()` (SDK de Dropbox), `DbxCredential`, scopes de Dropbox |
| Credencial | `data/auth/DropboxCredentialStore.kt` | `EncryptedSharedPreferences` serializando un `DbxCredential` — formato específico del SDK |
| Motor de sync | `sync/SyncEngine.kt` | **Ya es agnóstico de facto** — solo conoce `DropboxTransport` por el tipo del constructor, pero su lógica (comparar `LocalFileScanner` vs `transport.listFolderRecursive()`, decidir con `ConflictResolver`) no asume nada Dropbox-específico. Cambiar el tipo del parámetro a una interfaz es mecánico |
| Resolución de conflictos | `sync/ConflictResolver.kt` | **100% agnóstico ya** — solo compara mtimes (`localMtimeMillis`/`remoteMtimeMillis`/`lastSyncMillis`), sin tocar nada del transporte. No necesita cambios |
| Ajustes | `data/prefs/SettingsRepository.kt` | Sin concepto de "proveedor" — solo `savesRemote`/`statesRemote` como texto libre |
| Orquestación | `sync/SyncOrchestrator.kt` | Construye `DropboxClientProvider`/`DropboxTransport` a mano, sin punto de extensión |

**Conclusión clave**: el núcleo de sync (`SyncEngine`+`ConflictResolver`) no
hay que tocarlo. El trabajo real es (a) una interfaz `CloudTransport` que
`DropboxTransport` ya implementa sin cambiar su comportamiento, y (b) una
implementación nueva `GoogleDriveTransport` + su propio auth/credential
store, más el cableado de selección de proveedor en Ajustes/Orchestrator.

---

## Decisión de diseño: scope de Drive — `drive.file` + Picker, no `drive` completo

Google exige revisión de seguridad (verificación de app, a veces semanas)
para scopes "sensibles/restringidos" como `drive` (acceso completo). El
scope `drive.file` (**Scopes.DRIVE_FILE**, "solo archivos que esta app cree
o abra explícitamente") **no requiere esa verificación** — pero con
consecuencia real: la app Android **no vería** una carpeta `RetroSync/`
creada por `rclone` en el PC, porque no la "abrió" ella.

**Solución recomendada**: usar el **Drive Picker** (`Google Drive Picker
API`, vía `com.google.android.gms:play-services-drive` o el picker
web-based embebido) para que el usuario, una sola vez, **elija la carpeta
`RetroSync/` ya existente en su Drive** — el Picker concede acceso
`drive.file` con alcance a esa carpeta y su contenido sin pedir el scope
completo. Mismo principio de "vinculación explícita una vez" que ya se usa
para Dropbox (login OAuth una vez) — no es fricción nueva, es equivalente.

**Alternativa descartada por ahora**: pedir el scope `drive` completo. Válido
técnicamente, pero mete al proyecto en el proceso de verificación de Google
(due diligence, posible auditoría de seguridad pagada para scopes
"restringidos") — coste desproporcionado para una app de un solo usuario.

---

## Objetivo

1. `CloudTransport`: interfaz que capture la forma de `DropboxTransport`
   (`listFolderRecursive`/`upload`/`download`) para que `SyncEngine` deje de
   depender del tipo concreto.
2. `GoogleDriveTransport`: implementación sobre la Drive API v3, con
   resolución de carpeta→ID cacheada (Drive direcciona por `fileId`, no por
   ruta plana como Dropbox).
3. `GoogleDriveAuthManager`/`GoogleDriveCredentialStore`: flujo Sign-In +
   Picker (una vez) + persistencia de la cuenta elegida — mismo contrato
   público que `DropboxAuthManager` para que `MainActivity` no necesite
   lógica condicional profusa.
4. Selector de proveedor en Ajustes (`SettingsRepository`/`SettingsScreen`)
   y `SyncOrchestrator` construyendo el transporte/auth correctos según el
   proveedor guardado.

---

## Fases

### Fase 0 — Prerrequisito manual (usuario, fuera de código)

Antes de escribir una sola línea de `GoogleDriveTransport`: crear un
proyecto en Google Cloud Console, habilitar la Drive API, configurar la
pantalla de consentimiento OAuth (modo "Testing" con el propio email como
usuario de prueba — evita la revisión de Google mientras sea de un solo
usuario, igual que Dropbox en modo Desarrollo hoy), registrar un cliente
OAuth Android con el SHA-1 del keystore de debug **y** del de release
(`android/keystore/retrovault-release.jks`, ya existe de `ANDROID-RELEASE-1`).
Mismo patrón que `DROPBOX_APP_KEY` en `local.properties` — nueva entrada
`GDRIVE_CLIENT_ID` (o equivalente), nunca hardcodeada ni versionada.

**Bloqueante real a anotar**: si el usuario no completa esta fase, nada de
lo siguiente es verificable en hardware — mismo patrón que
`DROPBOX_APP_KEY` ausente hoy (`isAppKeyConfigured()` en
`DropboxAuthManager`).

### Fase 1 — `CloudTransport`: extraer la interfaz sin cambiar comportamiento

```kotlin
// sync/CloudTransport.kt (nuevo)
interface CloudTransport {
    fun listFolderRecursive(remoteRoot: String): List<RemoteSave>
    fun upload(localFile: File, remoteRoot: String, relative: String, clientModifiedMillis: Long): RemoteSave
    fun download(remoteRoot: String, relative: String, destFile: File): Long
}
```

`DropboxTransport` pasa a `class DropboxTransport(...) : CloudTransport`
(constructor y cuerpo sin cambios). `SyncEngine(private val transport:
CloudTransport, ...)` — un cambio de tipo, cero cambios de lógica. Riesgo
prácticamente nulo: los tests existentes (`ConflictResolverTest`,
`LocalFileScannerTest`, `DropboxTransportPathsTest`) siguen en verde sin
tocarlos.

**Verificación**: `./gradlew testDebugUnitTest`/`assembleDebug` en verde,
0 cambios de comportamiento — PR solo de refactor, revisable en minutos.

### Fase 2 — Auth: Sign-In + Picker + credential store

- `GoogleDriveCredentialStore.kt`: mismo patrón que
  `DropboxCredentialStore.kt` (`EncryptedSharedPreferences` +
  `runCatching`/recreate-si-falla, ver `ANDROID-SYNC-FIX-2` — el mismo
  `AEADBadTagException` puede pasar aquí igual) — pero lo que se guarda es
  la cuenta Google elegida (`GoogleSignInAccount.email`) más el `fileId` de
  la carpeta `RetroSync/` resuelta por el Picker, no un token OAuth manual
  (Google Sign-In + `GoogleAccountCredential` gestionan el refresh solos,
  vía `AccountManager` — no hay un `DbxCredential` equivalente que
  serializar a mano).
- `GoogleDriveAuthManager.kt`: `startAuth()` lanza `GoogleSignIn` pidiendo
  `Scopes.DRIVE_FILE`; tras el login, lanza el Picker para elegir/crear
  `RetroSync/` y guarda su `fileId`. `isSignedIn()`/`signOut()`/
  `fetchAccountLabel()` con la misma forma pública que
  `DropboxAuthManager` (incluida la lección de `ANDROID-SYNC-CRITICAL-1`:
  mostrar email + un identificador inequívoco de cuenta, nunca fiarse solo
  del nombre visible).

**Verificación**: solo compila + tests de las partes puras (parsing,
serialización del `fileId` guardado) — el flujo real de Sign-In/Picker
necesita hardware y la Fase 0 completa, no verificable en CI.

### Fase 3 — `GoogleDriveTransport`: la pieza más distinta de Dropbox

Drive direcciona por `fileId`, no por ruta — hay que traducir el modelo
`relative: String` de `SyncEngine` a IDs:

- **Resolución carpeta→ID cacheada**: para cada segmento de una ruta
  relativa (`"mame/sf2.nv"` → `mame`, luego el archivo), consultar
  `files.list(q = "name='mame' and 'ROOT_ID' in parents and
  mimeType='application/vnd.google-apps.folder'")`; si no existe, crearla
  (`files.create`). Cachear `path segment → fileId` en memoria durante un
  pase de sync (la estructura de carpetas no cambia a mitad de un sync) —
  evita re-resolver el mismo prefijo por cada archivo de una carpeta con
  muchos saves.
- **Listado recursivo**: la Drive API v3 no tiene un "listar recursivo"
  nativo como Dropbox — hay que recorrer el árbol de carpetas con BFS/DFS
  propio (una llamada `files.list` por carpeta), acumulando
  `RemoteSave(relative, clientModifiedMillis=modifiedTime, size, rev=fileId)`.
  Más llamadas que Dropbox (1 por carpeta en vez de 1 total), pero dentro
  de la cuota por defecto de la Drive API (1.000 queries/100s/usuario) para
  el volumen de carpetas de este proyecto (core/plataforma, no miles).
- **Upload/download**: `files.create`/`files.update` con
  `setModifiedTime()` explícito (Drive permite fijar el mtime igual que
  Dropbox con `client_modified` — necesario para que `ConflictResolver`
  compare mtimes reales, no el momento de subida) y `files.get` +
  `MediaHttpDownloader` para bajar.

**Verificación**: tests unitarios de la resolución de rutas (con un
`DriveClient` fake/mock, sin red real) + los reales existentes en verde.
Round-trip contra una cuenta Drive real queda para hardware (Fase 5).

### Fase 4 — Selector de proveedor (Ajustes + Orchestrator)

- `SettingsRepository`: nueva `syncProvider: Flow<String>` (`"dropbox"` por
  defecto, para no romper instalaciones existentes; `"gdrive"` como
  alternativa) + `setSyncProvider()`.
- `SettingsScreen.kt`: selector (p. ej. `Row` de dos `FilterChip`/
  `RadioButton`) antes del botón "Conectar" — visible solo si ninguno de
  los dos está ya conectado (cambiar de proveedor con una sesión activa
  exige desconectar primero, mismo criterio que Dropbox hoy con
  `onDisconnectDropbox`).
- `SyncOrchestrator.runFullSync()`: en vez de construir
  `DropboxClientProvider`/`DropboxTransport` fijo, resuelve el
  `CloudTransport`+auth manager según `settingsRepository.syncProvider`.
  Puede necesitar una pequeña fábrica (`CloudProviderFactory` o similar) en
  vez de un `when` disperso por todo `MainActivity`/`SyncOrchestrator`.

### Fase 5 — Tests + validación en hardware real

Mismo patrón que `ANDROID-SYNC-15`/`DEVPROFILE-6`: checklist con el agente
`hardware-validator` contra una RG556 real con la Fase 0 completada —
primer sync real con Drive, verificar que el archivo aparece en
`drive.google.com` dentro de `RetroSync/`, reboot/background, y
confirmar que Dropbox sigue funcionando sin regresión para quien no cambie
de proveedor.

---

## Riesgos y notas para la implementación

- **No romper Dropbox mientras se construye Drive** — cada fase debe dejar
  `./gradlew testDebugUnitTest`/`assembleDebug` en verde y el flujo Dropbox
  intacto; el selector de proveedor (Fase 4) es el único punto que cambia
  comportamiento visible, y por defecto debe seguir siendo Dropbox.
- **Refresh de credenciales**: verificar en la Fase 2 que
  `GoogleAccountCredential` refresca el token silenciosamente sin
  intervención — si no, hace falta un `runCatching` + relanzar Sign-In
  igual que `ANDROID-SYNC-FIX-2` hizo para el `AEADBadTagException` de
  Dropbox.
- **Cuota de la Drive API**: el BFS de la Fase 3 hace más llamadas que
  Dropbox para el mismo árbol — vigilar en la validación de hardware
  (Fase 5) que no se acerque a los límites por-usuario/100s con el volumen
  real de carpetas (`saves/<core>/`, `states/<core>/`, `arcade/<mame,cps1,
  cps2,cps3,fbneo>/`).

## Fuera de alcance

- Pedir el scope `drive` completo (ver decisión de diseño arriba).
- Tocar el lado PC — ya funciona con gdrive vía `rclone`, sin cambios.
- Migrar datos ya sincronizados de Dropbox a Drive o viceversa — el
  usuario elige un proveedor por dispositivo, sin herramienta de migración
  cruzada en este roadmap.
- Resolver `ANDROID-SYNC-CRITICAL-1` (causa raíz 3) — es independiente y
  más barato; si se resuelve primero, este roadmap pasa a "nice to have"
  en vez de urgente.

---

## Checklist

- [x] Fase 0 — prerrequisito manual (Google Cloud Console, `GDRIVE_CLIENT_ID` en `local.properties`) completado por el usuario — 2026-10-03: proyecto + clientes OAuth Android (release y debug) + usuario de prueba; Sign-In verificado en la RG556
- [x] Fase 1 — `CloudTransport` extraído, `DropboxTransport` lo implementa, cero regresiones (PR #357)
- [ ] Fase 2 — `GoogleDriveAuthManager`/`GoogleDriveCredentialStore` (Sign-In + Picker)
  - [x] Sign-In (**verificado en hardware 2026-10-03**: botón "Conectar Google Drive" en Ajustes, PR #406; un 403 inicial era la cuenta fuera de la lista de usuarios de prueba) (`GoogleDriveCredentialStore`, `GoogleDriveAuthManager.signInIntent()`/`handleSignInResult()`, dependencia `play-services-auth`) — compila y `testDebugUnitTest` en verde; **no verificable de extremo a extremo sin Fase 0** (`GDRIVE_CLIENT_ID` real)
  - [ ] Picker para elegir la carpeta `RetroSync/` ya existente (`GoogleDriveCredentialStore.folderId()` sigue siempre `null` hasta esto) — pendiente, ver nota de complejidad abajo
- [ ] Fase 3 — `GoogleDriveTransport` (resolución de carpetas + BFS + upload/download) — código y 11 tests con un `DriveApi` falso hechos 2026-10-03 (`DriveApi`, `GoogleDriveTransport`, `DriveRestApi` con `HttpURLConnection`, sin dependencias nuevas); **`DriveRestApi` sin probar contra Drive real**: falta el token (Picker/autorización) para ejercitarlo
- [ ] Fase 4 — selector de proveedor en Ajustes + `SyncOrchestrator` genérico
- [ ] Fase 5 — tests + validación en hardware real (RG556), Dropbox sigue intacto

**Nota 2026-09-29 sobre el Picker (investigado contra la documentación real
de Google, no asumido)**: la API nativa de Picker vía `play-services-drive`
está deprecada desde 2022. El mecanismo vigente para apps de escritorio/
móviles **no es el WebView** que se apuntaba aquí antes — es un flujo de
navegador que redirige de vuelta a la app
([guía oficial](https://developers.google.com/workspace/drive/picker/guides/desktop-mobile-picker)):

- Scope: **solo** `drive.file` (no se puede combinar con otros).
- URL de autorización: `https://accounts.google.com/o/oauth2/v2/auth` con
  `client_id`, `scope=.../drive.file`, `redirect_uri`, `response_type=code`,
  `access_type=offline`, `prompt=consent`, **`trigger_onepick=true`** (activa
  el Picker) y, para carpetas, **`allow_folder_selection=true`**.
- Vuelta a la app: el navegador redirige a `redirect_uri` con
  `picked_file_ids` (los IDs elegidos) + `code` (a canjear por tokens).
- Lado Android: la doc apunta a la API nueva `AuthorizationClient`
  (`com.google.android.gms.auth.api.identity.Identity.getAuthorizationClient()`
  + `AuthorizationRequest`), **no** al `GoogleSignIn` clásico usado en el
  incremento de Sign-In ya commiteado — son dos APIs distintas de
  `play-services-auth` (confirmado también contra una migración real de
  terceros, PR
  [Pingue/note-app#25](https://github.com/Pingue/note-app/pull/25), que
  reemplaza `GoogleSignIn` por `Identity.getAuthorizationClient(context)
  .authorize(AuthorizationRequest.builder()...build())` +
  `getAuthorizationResultFromIntent(data)`).

**Lo que queda sin verificar**: la doc menciona pasar `PICKER_OAUTH_TRIGGER`/
`PICKER_ALLOW_FOLDER_SELECTION` como "resource parameter" del
`AuthorizationRequest.Builder`, pero ninguna fuente consultada (docs oficiales
ni el PR de referencia) trae el método/firma Kotlin exacto para eso — no se
ha escrito código para esta parte porque adivinar la firma de una API externa
sin poder compilarla/probarla contra una cuenta real (Fase 0 pendiente) es
más riesgo que valor. Próximo paso: revisar
`AuthorizationRequest`/`AuthorizationRequest.Builder` en el
[Android reference](https://developers.google.com/android/reference/com/google/android/gms/auth/api/identity/AuthorizationClient)
con la Fase 0 ya completa para poder compilar y probar contra Drive real en
el mismo ciclo.

**Consecuencia para el Sign-In ya commiteado**: `GoogleDriveAuthManager`
(clásico `GoogleSignIn`) sigue siendo válido para el login/email — pero la
autorización del scope `drive.file` + el Picker en sí necesitarán
`AuthorizationClient` en paralelo, no una extensión del mismo manager. Revisar
si compensa unificar ambos en `AuthorizationClient` (cubre también el login,
según el PR de referencia) antes de construir más encima del `GoogleSignIn`
actual — decisión para el próximo incremento, no tomada todavía.
