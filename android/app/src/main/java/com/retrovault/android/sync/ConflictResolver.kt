package com.retrovault.android.sync

/** Acción a tomar para un archivo tras comparar mtimes local/remoto. */
enum class SyncAction { UPLOAD, DOWNLOAD, UP_TO_DATE, CONFLICT }

data class SyncDecision(
    val action: SyncAction,
    val relative: String,
    val localMtimeMillis: Long?,
    val remoteMtimeMillis: Long?,
)

/**
 * Puerto 1:1 de `decide()` en `src/rom_manager/sync/conflict_resolver.py:16-55`
 * — verificado línea a línea antes de portar (`Tareas/Roadmap-Android-Sync.md` §1).
 *
 * Reglas:
 * - Un lado ausente → upload/download trivial.
 * - Ambos presentes + hay `lastSyncMillis` conocido: si AMBOS mtimes son
 *   posteriores a `lastSyncMillis` por más de `toleranceMillis` → CONFLICT.
 * - Si no: diferencia `<= toleranceMillis` → UP_TO_DATE; si no, gana el más
 *   nuevo (UPLOAD si local es más nuevo, DOWNLOAD si lo es el remoto).
 */
object ConflictResolver {
    private const val DEFAULT_TOLERANCE_MILLIS = 2_000L

    fun decide(
        relative: String,
        localMtimeMillis: Long?,
        remoteMtimeMillis: Long?,
        lastSyncMillis: Long?,
        toleranceMillis: Long = DEFAULT_TOLERANCE_MILLIS,
    ): SyncDecision {
        if (localMtimeMillis == null && remoteMtimeMillis == null) {
            return SyncDecision(SyncAction.UP_TO_DATE, relative, null, null)
        }
        if (localMtimeMillis == null) {
            return SyncDecision(SyncAction.DOWNLOAD, relative, null, remoteMtimeMillis)
        }
        if (remoteMtimeMillis == null) {
            return SyncDecision(SyncAction.UPLOAD, relative, localMtimeMillis, null)
        }

        if (lastSyncMillis != null) {
            val localChanged = localMtimeMillis - lastSyncMillis > toleranceMillis
            val remoteChanged = remoteMtimeMillis - lastSyncMillis > toleranceMillis
            if (localChanged && remoteChanged) {
                return SyncDecision(SyncAction.CONFLICT, relative, localMtimeMillis, remoteMtimeMillis)
            }
        }

        val diff = localMtimeMillis - remoteMtimeMillis
        if (kotlin.math.abs(diff) <= toleranceMillis) {
            return SyncDecision(SyncAction.UP_TO_DATE, relative, localMtimeMillis, remoteMtimeMillis)
        }

        val action = if (diff > 0) SyncAction.UPLOAD else SyncAction.DOWNLOAD
        return SyncDecision(action, relative, localMtimeMillis, remoteMtimeMillis)
    }
}
