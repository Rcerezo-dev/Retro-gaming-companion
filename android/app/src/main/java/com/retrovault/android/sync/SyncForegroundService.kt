package com.retrovault.android.sync

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import com.retrovault.android.R
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.io.File

/**
 * Modo Instantáneo (ANDROID-SYNC-10, reabierto 2026-09-25): servicio
 * foreground que mantiene vivo [SaveFileObserverManager] mientras la app
 * está en background — Android exige foreground service para trabajo
 * continuo desde API 26+, con notificación obligatoria (`startForeground`).
 *
 * Riesgo conocido, no mitigable en código: gestores de batería agresivos
 * (Anbernic/RG556 y similares) pueden matar este servicio sin avisar con la
 * pantalla apagada — el sync periódico (ANDROID-SYNC-12) sigue activo en
 * paralelo como red de seguridad. Sin validar todavía en hardware real
 * (ver `Tareas/backlog.md`, ANDROID-SYNC-9).
 */
class SyncForegroundService : Service() {
    private val job = SupervisorJob()
    private val scope = CoroutineScope(Dispatchers.Default + job)
    private var observerManager: SaveFileObserverManager? = null

    override fun onCreate() {
        super.onCreate()
        startForeground(NOTIFICATION_ID, buildNotification())
        observerManager =
            SaveFileObserverManager(
                roots = listOf(File(RetroArchPaths.SAVES), File(RetroArchPaths.STATES)),
                onChange = {
                    scope.launch { SyncOrchestrator.runFullSync(applicationContext, SyncTrigger.INSTANT) }
                },
            ).also { it.start() }
    }

    override fun onStartCommand(
        intent: Intent?,
        flags: Int,
        startId: Int,
    ): Int = START_STICKY

    override fun onDestroy() {
        observerManager?.stop()
        job.cancel()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun buildNotification(): Notification {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(CHANNEL_ID, "Sync instantáneo", NotificationManager.IMPORTANCE_LOW)
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Retro Vault Sync")
            .setContentText("Vigilando saves y states para sincronizar al instante")
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setOngoing(true)
            .build()
    }

    companion object {
        private const val CHANNEL_ID = "instant_sync"
        private const val NOTIFICATION_ID = 1001

        fun start(context: Context) {
            ContextCompat.startForegroundService(context, Intent(context, SyncForegroundService::class.java))
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, SyncForegroundService::class.java))
        }
    }
}
