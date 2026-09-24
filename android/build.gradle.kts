// Root build file: declares plugin versions once, applied per-module (only ":app" today).
plugins {
    id("com.android.application") version "8.5.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.24" apply false
    // KSP para el procesador de anotaciones de Room (ANDROID-SYNC-7) — el
    // sufijo tras el "-" es la versión de KSP, no de Kotlin; debe existir
    // una build para la versión exacta de Kotlin de arriba (1.9.24).
    id("com.google.devtools.ksp") version "1.9.24-1.0.20" apply false
}
