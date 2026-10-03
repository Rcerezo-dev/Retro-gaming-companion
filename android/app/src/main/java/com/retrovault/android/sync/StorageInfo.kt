package com.retrovault.android.sync

import com.dropbox.core.v2.DbxClientV2
import java.util.Locale

/** Cuota de una cuenta gratuita de Dropbox: por encima, la biblioteca de saves ya no cabe. */
const val DROPBOX_FREE_BYTES: Long = 2L * 1024 * 1024 * 1024

private const val KIB = 1024L
private const val MIB = KIB * 1024
private const val GIB = MIB * 1024

/** `540 MB`, `2,27 GB`… con coma decimal (UI en español). */
fun formatBytes(bytes: Long): String =
    when {
        bytes >= GIB -> String.format(Locale.forLanguageTag("es-ES"), "%.2f GB", bytes.toDouble() / GIB)
        bytes >= MIB -> String.format(Locale.forLanguageTag("es-ES"), "%.0f MB", bytes.toDouble() / MIB)
        else -> String.format(Locale.forLanguageTag("es-ES"), "%.0f KB", bytes.toDouble() / KIB)
    }

/** Resumen para Ajustes: tamaño de la biblioteca de saves, límite de Dropbox y, si no cabe, el aviso hacia Drive. */
data class StorageInfo(val summary: String, val hint: String?)

/**
 * [dropboxUsed]/[dropboxTotal] son `null` si Dropbox no está conectado o no respondió. El aviso
 * salta cuando la biblioteca supera los 2 GB gratuitos de Dropbox ([DROPBOX_FREE_BYTES]).
 */
fun storageInfo(
    libraryBytes: Long,
    dropboxUsed: Long?,
    dropboxTotal: Long?,
): StorageInfo {
    val lines = mutableListOf("Biblioteca de saves: ${formatBytes(libraryBytes)}")
    if (dropboxUsed != null && dropboxTotal != null) {
        lines += "Dropbox: ${formatBytes(dropboxUsed)} usados de ${formatBytes(dropboxTotal)}"
    }
    val hint =
        if (libraryBytes > DROPBOX_FREE_BYTES) {
            "Tu biblioteca de saves (${formatBytes(libraryBytes)}) supera los ${formatBytes(DROPBOX_FREE_BYTES)} gratuitos de Dropbox: " +
                "te conviene pasar a Google Drive (15 GB)."
        } else {
            null
        }
    return StorageInfo(lines.joinToString("\n"), hint)
}

/** Espacio usado y asignado de la cuenta de Dropbox, o `null` si la consulta falla (sin red, sin sesión). */
fun fetchDropboxQuota(client: DbxClientV2): Pair<Long, Long>? =
    runCatching {
        val usage = client.users().spaceUsage
        val allocation = usage.allocation
        val total =
            when {
                allocation.isIndividual -> allocation.individualValue.allocated
                allocation.isTeam -> allocation.teamValue.allocated
                else -> return@runCatching null
            }
        usage.used to total
    }.getOrNull()
