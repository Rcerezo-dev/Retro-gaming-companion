package com.retrovault.android.permissions

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.Settings
import androidx.core.content.ContextCompat

/**
 * Puente entre [StoragePermissionPolicy] y las APIs reales de Android.
 * Depende de `Context`/`Build.VERSION.SDK_INT` — no es testeable en JVM
 * plano (necesita Robolectric o un emulador), por eso la decisión de qué
 * rama tomar vive separada en [StoragePermissionPolicy].
 */
object StoragePermissionManager {
    val legacyStoragePermissions: Array<String> =
        arrayOf(
            Manifest.permission.READ_EXTERNAL_STORAGE,
            Manifest.permission.WRITE_EXTERNAL_STORAGE,
        )

    fun hasStorageAccess(context: Context): Boolean =
        if (StoragePermissionPolicy.needsManageExternalStorage(Build.VERSION.SDK_INT)) {
            Environment.isExternalStorageManager()
        } else {
            legacyStoragePermissions.all { permission ->
                ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
            }
        }

    /** Intent de redirect a Ajustes para conceder "Acceso a todos los archivos" (API 30+). */
    fun manageAllFilesAccessIntent(context: Context): Intent =
        Intent(
            Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION,
            Uri.parse("package:${context.packageName}"),
        )

    fun hasNotificationPermission(context: Context): Boolean =
        if (!StoragePermissionPolicy.needsNotificationPermission(Build.VERSION.SDK_INT)) {
            true
        } else {
            ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) ==
                PackageManager.PERMISSION_GRANTED
        }
}
