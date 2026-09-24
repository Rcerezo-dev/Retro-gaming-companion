package com.retrovault.android.util

import java.util.Locale

/**
 * Formato legible de tamaños de archivo para la UI (B/KB/MB).
 *
 * Fuerza [Locale.ROOT] — sin esto, `String.format` usa la locale por
 * defecto del dispositivo y en locales con coma decimal (es-ES incluida)
 * "1.0 KB" saldría como "1,0 KB", inconsistente entre dispositivos.
 */
fun formatBytes(bytes: Long): String =
    when {
        bytes < 1024 -> "$bytes B"
        bytes < 1024 * 1024 -> String.format(Locale.ROOT, "%.1f KB", bytes / 1024.0)
        else -> String.format(Locale.ROOT, "%.1f MB", bytes / (1024.0 * 1024.0))
    }
