package com.retrovault.android.sync

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters

/**
 * Ejecuta [SyncOrchestrator.runFullSync] en segundo plano — programado por
 * [PeriodicSyncScheduler] (ANDROID-SYNC-12). Sin sesión de Dropbox no tiene
 * sentido reintentar solo; con errores parciales (p. ej. red inestable) se
 * reintenta, WorkManager decide el backoff.
 */
class SyncWorker(
    context: Context,
    params: WorkerParameters,
) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val result = SyncOrchestrator.runFullSync(applicationContext) ?: return Result.failure()
        return if (result.errors.isEmpty()) Result.success() else Result.retry()
    }
}
