package com.retrovault.android.sync

import android.content.Context
import com.retrovault.android.data.auth.DropboxClientProvider
import com.retrovault.android.data.auth.DropboxCredentialStore
import com.retrovault.android.data.db.AppDatabase
import com.retrovault.android.data.prefs.SettingsRepository
import kotlinx.coroutines.flow.first
import java.io.File

/**
 * Un pase completo de sync (saves + states) contra Dropbox, construyendo
 * sus propias dependencias a partir de un [Context]. Punto de entrada
 * compartido entre "Sincronizar ahora" (MainActivity) y [SyncWorker]
 * (ANDROID-SYNC-12) — este último no tiene una Activity de la que tomar
 * instancias ya construidas.
 */
object SyncOrchestrator {
    /** `null` si no hay sesión de Dropbox. */
    suspend fun runFullSync(context: Context): SyncResult? {
        val appContext = context.applicationContext
        val client = DropboxClientProvider(DropboxCredentialStore(appContext)).client() ?: return null
        val settingsRepository = SettingsRepository(appContext)
        val engine = SyncEngine(DropboxTransport(client), AppDatabase.getInstance(appContext).syncWatermarkDao())

        val savesResult = engine.sync(File(RetroArchPaths.SAVES), settingsRepository.savesRemote.first())
        val statesResult = engine.sync(File(RetroArchPaths.STATES), settingsRepository.statesRemote.first())
        return savesResult + statesResult
    }
}
