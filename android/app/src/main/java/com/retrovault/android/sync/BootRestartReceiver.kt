package com.retrovault.android.sync

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.retrovault.android.data.prefs.SettingsRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

/**
 * Relanza el servicio foreground del modo Instantáneo tras un reboot
 * (ANDROID-SYNC-11, reabierto 2026-09-25) — a diferencia de WorkManager
 * (ANDROID-SYNC-12), que se re-programa solo, un `Service` no sobrevive un
 * reboot sin esto.
 */
class BootRestartReceiver : BroadcastReceiver() {
    override fun onReceive(
        context: Context,
        intent: Intent,
    ) {
        if (intent.action != Intent.ACTION_BOOT_COMPLETED) return
        val pendingResult = goAsync()
        CoroutineScope(Dispatchers.Default).launch {
            try {
                if (SettingsRepository(context).instantSyncEnabled.first()) {
                    SyncForegroundService.start(context)
                }
            } finally {
                pendingResult.finish()
            }
        }
    }
}
