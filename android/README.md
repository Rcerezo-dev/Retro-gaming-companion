# Retro Vault Sync — app Android

App nativa (Kotlin + Jetpack Compose) que sincroniza los saves/states de
RetroArch directamente con Dropbox desde la propia consola Android (p. ej.
la Anbernic RG556), sin depender de que el PC esté encendido. Sustituye al
script Termux+rclone documentado en `../docs/sync/Guia-Termux-Anbernic.md`.

Diseño completo, contrato de interoperabilidad con el sync del PC
(`../src/rom_manager/sync/`) y desglose de fases:
**`../Tareas/Roadmap-Android-Sync.md`**. Estado de las tareas:
`../Tareas/backlog.md`, sección `ANDROID-SYNC`.

## Requisitos

- [Android Studio](https://developer.android.com/studio) (versión reciente,
  Ladybug o posterior) — trae el JDK y el Android SDK integrados, no hace
  falta instalarlos aparte.
- Cuenta de Dropbox (para probar el flujo de sync una vez implementado).

## Abrir el proyecto

1. Abre Android Studio → **Open** → selecciona esta carpeta (`android/`),
   no la raíz del repo.
2. Deja que el IDE sincronice Gradle la primera vez (puede tardar unos
   minutos, descarga dependencias).
3. Ejecuta la configuración `app` sobre un emulador (API 26+) o un
   dispositivo físico con depuración USB activada.

El Gradle Wrapper (`gradlew`, `gradlew.bat`, `gradle/wrapper/`) está
incluido y versionado — no hace falta tener Gradle instalado aparte,
`./gradlew` se autodescarga la versión correcta (8.7) la primera vez.

## Estructura

```
android/
├── app/
│   ├── build.gradle.kts        # applicationId com.retrovault.android, minSdk 26
│   └── src/
│       ├── main/                # código de la app
│       ├── test/                # tests JVM (sin dispositivo/emulador)
│       └── androidTest/         # tests instrumentados (emulador o dispositivo)
```

Ver `../Tareas/Roadmap-Android-Sync.md` §2 para el paquete completo previsto
(`sync/`, `service/`, `data/`, `ui/`) — se va rellenando fase a fase según
la tabla `ANDROID-SYNC-*` del backlog.

## Convenciones del proyecto

Mismas reglas de trabajo que el resto del repo (`.claude/CLAUDE.md`): una
rama por tarea (`feature/android-sync-N-*`), PR a `develop`, sin mezclar
tareas de fases distintas en el mismo PR. La tarea `ANDROID-SYNC-N` de cada
PR debe indicar explícitamente si se verificó por compilación/tests reales
o solo por revisión de código (ver nota de entorno en
`../Tareas/Roadmap-Android-Sync.md` §8).
