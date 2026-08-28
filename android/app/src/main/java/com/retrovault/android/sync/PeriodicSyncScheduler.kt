package com.retrovault.android.sync

import android.content.Context
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import java.util.concurrent.TimeUnit

/**
 * Enciende/apaga el sync periódico (ANDROID-SYNC-12) — 15 min es el mínimo
 * que WorkManager admite para trabajo periódico. WorkManager persiste el
 * trabajo encolado en su propia BD y lo re-programa solo tras un reboot, sin
 * necesitar un `BroadcastReceiver` propio (a diferencia del modo instantáneo
 * descartado, que sí lo habría necesitado).
 */
object PeriodicSyncScheduler {
    private const val UNIQUE_WORK_NAME = "periodic_dropbox_sync"
    private val INTERVAL_MINUTES = 15L

    fun enable(context: Context) {
        val request =
            PeriodicWorkRequestBuilder<SyncWorker>(INTERVAL_MINUTES, TimeUnit.MINUTES)
                .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
                .build()
        WorkManager.getInstance(context)
            .enqueueUniquePeriodicWork(UNIQUE_WORK_NAME, ExistingPeriodicWorkPolicy.UPDATE, request)
    }

    fun disable(context: Context) {
        WorkManager.getInstance(context).cancelUniqueWork(UNIQUE_WORK_NAME)
    }
}
