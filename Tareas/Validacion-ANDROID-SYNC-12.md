# Validación manual: ANDROID-SYNC-12 (sync periódico)

PR #237 (2026-08-18), verificada por `./gradlew test`/`assembleDebug` reales
pero no por el flujo manual en emulador/dispositivo. Toolchain ya instalado
en esta máquina (`Tareas/Roadmap-Android-Sync.md` §8): JDK 17 + Android SDK
en `C:\Users\rammu\android-build-tools\sdk`, Android Studio portable en
`C:\Users\rammu\android-build-tools\android-studio\` (acceso directo
"Android Studio" en el escritorio).

## Prerequisitos

- [ ] Android Studio abierto al menos una vez, SDK Location apuntado a
      `C:\Users\rammu\android-build-tools\sdk` (Custom setup, no Standard —
      para no descargar un segundo SDK duplicado).
- [ ] Proyecto abierto desde `android/` (no la raíz del repo).
- [ ] Rama `feature/android-sync-12-periodic-sync` activa (o ya mergeada a
      `develop` si la PR #237 se cerró primero).
- [ ] App Key de Dropbox en `android/local.properties` (`dropbox.appKey=...`,
      generada en https://www.dropbox.com/developers/apps) — sin ella el
      botón "Conectar Dropbox" queda deshabilitado y no se puede probar el
      sync real, solo el interruptor/persistencia.

## Pasos

1. **Crear un AVD** — Tools → Device Manager → Create Device → cualquier
   perfil de teléfono → system image **API 26+** (coincide con `minSdk`) →
   Finish → arrancar con ▶️.
2. **Instalar la app** — con el emulador corriendo, ▶️ "Run 'app'" en
   Android Studio. Conceder el permiso de almacenamiento cuando lo pida.
3. **Conectar Dropbox** — pestaña Ajustes → "Conectar Dropbox" → completar
   el login en el navegador del emulador → confirmar que vuelve a la app con
   "✓ Dropbox conectado".
4. **Activar el interruptor** "Sync automático (cada 15 min)".
5. **Confirmar que WorkManager programó el trabajo** (terminal, con el
   emulador como único dispositivo ADB conectado):
   ```
   adb shell dumpsys jobscheduler | grep -A 8 retrovault
   ```
   Debe aparecer un job de `com.retrovault.android` con constraint de red.
6. **Forzar el trabajo sin esperar 15 min** — dos opciones:
   - `adb shell cmd jobscheduler run -f com.retrovault.android <JOB_ID>`
     (el `JOB_ID` sale del paso 5).
   - O más simple: dejar pasar los 15 min con la app en segundo plano y
     comprobar después el resultado.
7. **Verificar el resultado del sync** — comprobar en la cuenta de Dropbox
   de prueba que los archivos de `saves/`/`states/` subieron, o pulsar
   "Sincronizar ahora" en Ajustes y comparar el resumen contra lo que
   debería haber subido/bajado.
8. **Prueba de reboot** — Device Manager → menú ⋮ del AVD → Cold Boot Now.
   Tras el arranque, repetir el paso 5: el job periódico debe seguir
   programado sin haber vuelto a abrir la app ni tocar el interruptor —
   es la garantía central de ANDROID-SYNC-12 (WorkManager re-programa solo
   tras reboot, sin necesitar `BootRestartReceiver`, que por eso se
   descartó en el recorte de alcance de esta sesión).

## Si algo falla

Documentar el hallazgo con archivo:línea exacto en `Tareas/backlog.md`
(sección `ANDROID-SYNC`) siguiendo el patrón `ANDROID-SYNC-FIX-N`, no
arreglarlo directamente sobre `develop` — misma regla que el resto del
backlog (rama por tarea).
