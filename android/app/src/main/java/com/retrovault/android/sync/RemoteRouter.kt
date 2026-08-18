package com.retrovault.android.sync

/**
 * A qué remoto (saves/states) pertenece un archivo por su extensión.
 * Espejo de `_resolve_remote()` en
 * `src/rom_manager/sync/rclone_transport.py:61-71`: `state_extensions` se
 * comprueba ANTES que `save_extensions` — varias extensiones aparecen en
 * ambas listas (`.state`, `.fcs`, `.sps`, `.psv`, `.hi`, `.brmc`, `.ml1`) y
 * para esas gana `states_remote`. En Android esto es menos crítico porque
 * `saves/` y `states/` ya son carpetas físicamente separadas en el
 * dispositivo, pero se mantiene como espejo exacto de la lógica del PC —
 * necesario, además, para el orden de merge de listados remotos del motor
 * de sync (ANDROID-SYNC-7).
 */
enum class RemoteCategory { SAVES, STATES, UNKNOWN }

object RemoteRouter {
    fun categorize(extension: String): RemoteCategory {
        val ext = extension.lowercase()
        return when {
            ext in SaveExtensions.state -> RemoteCategory.STATES
            ext in SaveExtensions.save -> RemoteCategory.SAVES
            else -> RemoteCategory.UNKNOWN
        }
    }
}
