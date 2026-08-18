package com.retrovault.android.sync

import com.retrovault.android.data.db.SyncWatermarkDao
import com.retrovault.android.data.db.SyncWatermarkEntity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

/** Política de resolución de conflictos. v1 solo implementa [NEWEST] (mismo
 * default que el PC en contexto background) — `keep_pc`/`keep_android`/`ask`
 * quedan fuera de alcance v1, añadibles después sin cambiar la firma de
 * [SyncEngine.sync] (`Tareas/Roadmap-Android-Sync.md` §1). */
enum class ConflictPolicy { NEWEST }

data class SyncResult(
    val uploaded: Int = 0,
    val downloaded: Int = 0,
    val upToDate: Int = 0,
    val conflicts: Int = 0,
    val errors: List<String> = emptyList(),
)

/**
 * Orquesta un pase completo de sync para una raíz local (`saves/` o
 * `states/`) contra su remoto de Dropbox correspondiente. Un pase = una
 * raíz; el llamador (`SyncForegroundService`/`SyncWorker`, Fases 3/4)
 * invoca dos veces (saves + states) y suma los resultados.
 */
class SyncEngine(
    private val transport: DropboxTransport,
    private val watermarkDao: SyncWatermarkDao,
) {
    // withContext(IO): listFolderRecursive/upload/download son llamadas de
    // red bloqueantes (el SDK de Dropbox no es suspend-aware) — se despachan
    // aquí para que el llamador (servicio foreground / WorkManager, Fases
    // 3/4) no tenga que acordarse de hacerlo él mismo.
    suspend fun sync(
        localRoot: File,
        remoteRoot: String,
        conflictPolicy: ConflictPolicy = ConflictPolicy.NEWEST,
    ): SyncResult = withContext(Dispatchers.IO) {
        val localByRelative = LocalFileScanner.scan(localRoot).associateBy { it.relative }
        val remoteByRelative =
            runCatching { transport.listFolderRecursive(remoteRoot) }
                .getOrElse {
                    return@withContext SyncResult(errors = listOf(it.message ?: "listFolderRecursive failed"))
                }
                .associateBy { it.relative }

        var uploaded = 0
        var downloaded = 0
        var upToDate = 0
        var conflicts = 0
        val errors = mutableListOf<String>()

        for (relative in localByRelative.keys + remoteByRelative.keys) {
            val local = localByRelative[relative]
            val remote = remoteByRelative[relative]
            val lastSync = watermarkDao.getLastSync(relative, remoteRoot)

            val decision =
                ConflictResolver.decide(
                    relative = relative,
                    localMtimeMillis = local?.mtimeMillis,
                    remoteMtimeMillis = remote?.clientModifiedMillis,
                    lastSyncMillis = lastSync,
                )

            try {
                when (decision.action) {
                    SyncAction.UP_TO_DATE -> upToDate++
                    SyncAction.UPLOAD -> {
                        val localFile = local?.absolute ?: continue
                        transport.upload(localFile, remoteRoot, relative, localFile.lastModified())
                        touchWatermark(relative, remoteRoot)
                        uploaded++
                    }
                    SyncAction.DOWNLOAD -> {
                        val destFile = File(localRoot, relative)
                        val remoteMtime = transport.download(remoteRoot, relative, destFile)
                        destFile.setLastModified(remoteMtime)
                        touchWatermark(relative, remoteRoot)
                        downloaded++
                    }
                    SyncAction.CONFLICT -> {
                        resolveConflict(conflictPolicy, local, remote, localRoot, remoteRoot, relative)
                        touchWatermark(relative, remoteRoot)
                        conflicts++
                    }
                }
            } catch (e: Exception) {
                errors += "$relative: ${e.message}"
            }
        }

        SyncResult(uploaded, downloaded, upToDate, conflicts, errors)
    }

    /**
     * Política `newest`: gana el mtime más reciente. Si gana el remoto se
     * respalda el local antes de sobrescribirlo (`<nombre>.conflict-<ts>`,
     * espejo de `save_syncer.py:293-355`) — si gana local, no hace falta
     * respaldo manual del lado remoto porque Dropbox ya versiona sus propios
     * archivos (a diferencia del PC, que usa rclone/filesystem plano sin
     * versionado nativo).
     */
    private fun resolveConflict(
        policy: ConflictPolicy,
        local: LocalSave?,
        remote: RemoteSave?,
        localRoot: File,
        remoteRoot: String,
        relative: String,
    ) {
        // El "when" exhaustivo sobre el enum obliga a decidir esta función
        // explícitamente el día que se añada keep_pc/keep_android/ask, en
        // vez de que el nuevo valor caiga en silencio por el mismo camino
        // que NEWEST.
        when (policy) {
            ConflictPolicy.NEWEST -> {
                val localMtime = local?.mtimeMillis ?: 0
                val remoteMtime = remote?.clientModifiedMillis ?: 0
                if (localMtime >= remoteMtime) {
                    local?.let { transport.upload(it.absolute, remoteRoot, relative, it.mtimeMillis) }
                } else {
                    backupLocalFile(localRoot, relative)
                    val destFile = File(localRoot, relative)
                    val remoteClientModified = transport.download(remoteRoot, relative, destFile)
                    destFile.setLastModified(remoteClientModified)
                }
            }
        }
    }

    private fun backupLocalFile(
        localRoot: File,
        relative: String,
    ) {
        val file = File(localRoot, relative)
        if (!file.exists()) return
        val backup = File(file.parentFile, "${file.name}.conflict-${System.currentTimeMillis()}")
        file.copyTo(backup, overwrite = true)
    }

    private suspend fun touchWatermark(
        relative: String,
        remoteRoot: String,
    ) {
        watermarkDao.upsert(SyncWatermarkEntity(relative, remoteRoot, System.currentTimeMillis()))
    }
}
