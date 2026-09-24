package com.retrovault.android.permissions

import android.os.Build

/**
 * Decide qué mecanismo de permiso aplica para un nivel de API dado.
 *
 * Aislado de `Build.VERSION.SDK_INT` (recibe el nivel como parámetro) para
 * poder testear la decisión en un test JVM plano, sin Robolectric ni
 * emulador — ver `Tareas/Roadmap-Android-Sync.md` §3 para el porqué de cada
 * corte de versión.
 */
object StoragePermissionPolicy {
    /** API 30+: permiso especial `MANAGE_EXTERNAL_STORAGE`, redirect a Ajustes. */
    fun needsManageExternalStorage(sdkInt: Int): Boolean = sdkInt >= Build.VERSION_CODES.R

    /** API 26-29: permisos runtime clásicos + `requestLegacyExternalStorage`. */
    fun needsLegacyStoragePermission(sdkInt: Int): Boolean = sdkInt < Build.VERSION_CODES.R

    /** Solo API 33+ exige el runtime prompt de `POST_NOTIFICATIONS`. */
    fun needsNotificationPermission(sdkInt: Int): Boolean = sdkInt >= Build.VERSION_CODES.TIRAMISU
}
