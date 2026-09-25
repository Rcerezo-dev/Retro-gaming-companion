package com.retrovault.android.data.db

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Snapshot de un pase de sync completo (ANDROID-SYNC-14, reabierta
 * 2026-09-25) — un registro por invocación de
 * [com.retrovault.android.sync.SyncOrchestrator.runFullSync], disparada
 * manualmente o por [com.retrovault.android.sync.SyncWorker] periódico.
 */
@Entity(tableName = "sync_history")
data class SyncHistoryEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val timestampMillis: Long,
    /** Nombre de [com.retrovault.android.sync.SyncTrigger] ("MANUAL"/"PERIODIC"/"INSTANT") — guardado como texto para no arrastrar un `TypeConverter` de Room por un enum de 3 valores. */
    val trigger: String,
    val uploaded: Int,
    val downloaded: Int,
    val upToDate: Int,
    val conflicts: Int,
    val errorCount: Int,
    val errorsText: String?,
)

enum class SyncOutcome { SUCCESS, WARNING, ERROR }

fun SyncHistoryEntity.outcome(): SyncOutcome =
    when {
        errorCount > 0 -> SyncOutcome.ERROR
        conflicts > 0 -> SyncOutcome.WARNING
        else -> SyncOutcome.SUCCESS
    }

fun SyncHistoryEntity.triggerLabel(): String =
    when (trigger) {
        "MANUAL" -> "Manual"
        "PERIODIC" -> "Automático"
        "INSTANT" -> "Instantáneo"
        else -> trigger
    }

fun SyncHistoryEntity.summary(): String {
    val base = "Subidos: $uploaded · Descargados: $downloaded · Al día: $upToDate"
    return buildString {
        append(base)
        if (conflicts > 0) append(" · Conflictos: $conflicts")
        if (errorCount > 0) append(" · Errores: $errorCount")
    }
}
