package com.retrovault.android.sync

/**
 * Rutas por defecto de RetroArch en Android — mismas que
 * `src/rom_manager/config.py:18-19,186` (`saves_path`/`states_path`,
 * `auto_sync_android_path`). No configurables hasta que exista Ajustes
 * (ANDROID-SYNC-8), que las hará sustituibles vía `SettingsRepository`.
 */
object RetroArchPaths {
    const val ROOT = "/storage/emulated/0/RetroArch"
    const val SAVES = "$ROOT/saves"
    const val STATES = "$ROOT/states"
}
