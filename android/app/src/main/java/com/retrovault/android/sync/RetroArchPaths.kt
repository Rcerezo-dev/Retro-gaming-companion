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

    /**
     * EMULATOR-COMPAT-5: el NVRAM de arcade (`.nv`) no vive en `saves/` ni
     * `states/` — vive junto a las propias ROMs en `$ROOT/<carpeta>`
     * (verificado en hardware real: RetroArch/mame con extension .nv,
     * cps1 con extension .nv…).
     * Mismos nombres de carpeta que las claves "Arcade" de
     * `src/rom_manager/detection/platforms.toml` (mame/cps1/cps2/cps3/
     * fbneo/arcade) — sin fuente compartida entre Python y Kotlin, igual
     * que `SaveExtensions`.
     */
    val ARCADE_FOLDERS = listOf("mame", "cps1", "cps2", "cps3", "fbneo", "arcade")
}
