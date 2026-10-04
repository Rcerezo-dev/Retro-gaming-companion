package com.retrovault.android.sync

import android.content.Context
import com.retrovault.android.data.db.AppDatabase
import com.retrovault.android.data.db.SyncHistoryEntity
import com.retrovault.android.data.prefs.SettingsRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import java.io.File
import java.util.concurrent.atomic.AtomicInteger

/** Quién disparó el pase — se persiste en [SyncHistoryEntity.trigger] (ANDROID-SYNC-14). */
enum class SyncTrigger { MANUAL, PERIODIC, INSTANT }

/**
 * Qué raíces recorre un pase. [ALL] = saves + states + NVRAM arcade (8 listados
 * de Dropbox). El modo Instantáneo pasa solo la raíz que cambió ([SAVES] o
 * [STATES]: 1 listado) — un autosave de RetroArch ya no dispara los 8.
 */
enum class SyncScope { ALL, SAVES, STATES }

/**
 * Un pase completo de sync (saves + states) contra Dropbox, construyendo
 * sus propias dependencias a partir de un [Context]. Punto de entrada
 * compartido entre "Sincronizar ahora" (MainActivity) y [SyncWorker]
 * (ANDROID-SYNC-12) — este último no tiene una Activity de la que tomar
 * instancias ya construidas. También el punto único donde se escribe el
 * historial de sync (ANDROID-SYNC-14), así cubre ambos disparadores sin
 * duplicar lógica.
 */
object SyncOrchestrator {
    // Contador, no un simple booleano: manual/periódico/instantáneo pueden
    // solaparse (p. ej. el periódico dispara justo cuando el usuario pulsa
    // "Sincronizar ahora") — con un booleano, el primero en terminar
    // apagaría el indicador mientras el segundo sigue corriendo.
    private val activeSyncs = AtomicInteger(0)
    private val _isSyncing = MutableStateFlow(false)

    /** Hay al menos un pase de sync en curso (cualquier trigger) — para mostrar estado real en vez de inferirlo por ADB. */
    val isSyncing: StateFlow<Boolean> = _isSyncing.asStateFlow()

    /** `null` si no hay sesión de Dropbox. */
    suspend fun runFullSync(
        context: Context,
        trigger: SyncTrigger,
        scope: SyncScope = SyncScope.ALL,
    ): SyncResult? {
        _isSyncing.value = activeSyncs.incrementAndGet() > 0
        try {
            val appContext = context.applicationContext
            val settingsRepository = SettingsRepository(appContext)
            val db = AppDatabase.getInstance(appContext)
            val provider = settingsRepository.syncProvider.first()
            val transport = CloudProviderFactory.create(appContext, provider) ?: return null
            val namespace = if (provider == SettingsRepository.PROVIDER_GDRIVE) "gdrive:" else ""
            val engine = SyncEngine(transport, db.syncWatermarkDao(), namespace)

            val savesRemote = settingsRepository.savesRemote.first()
            var result = SyncResult()
            if (scope != SyncScope.STATES) {
                result += engine.sync(File(RetroArchPaths.SAVES), savesRemote)
            }
            if (scope != SyncScope.SAVES) {
                result += engine.sync(File(RetroArchPaths.STATES), settingsRepository.statesRemote.first())
            }
            if (scope == SyncScope.ALL) {
                // EMULATOR-COMPAT-5: NVRAM de arcade, un pase por carpeta de
                // plataforma (mezcladas con las ROMs) contra un subdirectorio propio
                // de savesRemote — LocalFileScanner ya filtra por SaveExtensions, así
                // que las ROMs de cada carpeta nunca se suben.
                RetroArchPaths.ARCADE_FOLDERS.forEach { platform ->
                    result += engine.sync(File(RetroArchPaths.ROOT, platform), "$savesRemote/$platform")
                }
            }

            db.syncHistoryDao().insert(
                SyncHistoryEntity(
                    timestampMillis = System.currentTimeMillis(),
                    trigger = trigger.name,
                    uploaded = result.uploaded,
                    downloaded = result.downloaded,
                    upToDate = result.upToDate,
                    conflicts = result.conflicts,
                    errorCount = result.errors.size,
                    errorsText = result.errors.takeIf { it.isNotEmpty() }?.joinToString("; "),
                ),
            )
            return result
        } finally {
            _isSyncing.value = activeSyncs.decrementAndGet() > 0
        }
    }
}
