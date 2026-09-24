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

        val savesRemote = settingsRepository.savesRemote.first()
        val savesResult = engine.sync(File(RetroArchPaths.SAVES), savesRemote)
        val statesResult = engine.sync(File(RetroArchPaths.STATES), settingsRepository.statesRemote.first())
        // EMULATOR-COMPAT-5: NVRAM de arcade, un pase por carpeta de
        // plataforma (mezcladas con las ROMs) contra un subdirectorio propio
        // de savesRemote — LocalFileScanner ya filtra por SaveExtensions, así
        // que las ROMs de cada carpeta nunca se suben.
        val arcadeResult = RetroArchPaths.ARCADE_FOLDERS
            .map { platform -> engine.sync(File(RetroArchPaths.ROOT, platform), "$savesRemote/$platform") }
            .fold(SyncResult()) { acc, r -> acc + r }
        return savesResult + statesResult + arcadeResult
    }
}
