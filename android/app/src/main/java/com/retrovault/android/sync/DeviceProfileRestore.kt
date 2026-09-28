package com.retrovault.android.sync

import org.json.JSONArray
import java.io.File

/**
 * DEVPROFILE-6: botón "Restaurar este dispositivo" — lee el
 * `device-profile.json` que sube el PC (`services/device_profile.py`,
 * DEVPROFILE-5a) y descarga a las rutas públicas de [RetroArchPaths] las
 * entradas Tier A que Android puede usar: `autoconfig/`, `shaders/`,
 * `system/` (BIOS) + las 2 playlists (`content_history`/`content_favorites`).
 *
 * **Alcance recortado (decidido 2026-09-28)**: el manifiesto no lleva
 * `config/` (core options/remaps) todavía — esas rutas dependen de
 * `sync.ra_config_dir`/`ra_config_remote` (PC), un remoto separado sin
 * configurar hoy. Entradas del manifiesto sin destino Android conocido
 * (catálogos, `library_pc.db`/`library_android.db` — datos propios del PC)
 * quedan en [RestoreResult.skipped], no son un error.
 */
object DeviceProfileRestore {
    private const val MANIFEST_FILENAME = "device-profile.json"

    private val FOLDER_TARGETS =
        mapOf(
            "autoconfig" to RetroArchPaths.AUTOCONFIG,
            "shaders" to RetroArchPaths.SHADERS,
            "system" to RetroArchPaths.SYSTEM,
        )
    private val SINGLE_FILE_TARGETS =
        mapOf(
            "content_history.lpl" to "${RetroArchPaths.PLAYLISTS}/content_history.lpl",
            "content_favorites.lpl" to "${RetroArchPaths.PLAYLISTS}/content_favorites.lpl",
        )

    data class RestoreResult(
        val applied: List<String> = emptyList(),
        val skipped: List<String> = emptyList(),
        val sync: SyncResult = SyncResult(),
        val error: String? = null,
    )

    internal data class ManifestEntry(val name: String, val remote: String, val singleFile: Boolean)

    /**
     * Deriva la carpeta padre de `savesRemote` — mismo criterio que el PC
     * (`web/handlers/system.py:543`, `remote.rsplit("/", 1)[0]`) para que
     * ambos lados calculen el mismo `remote_base` a partir del mismo dato
     * ya guardado en Ajustes, sin duplicar configuración nueva.
     */
    fun remoteBaseFrom(savesRemote: String): String {
        val trimmed = savesRemote.trimEnd('/')
        val idx = trimmed.lastIndexOf('/')
        return if (idx >= 0) trimmed.substring(0, idx) else trimmed
    }

    internal fun parseManifest(json: String): List<ManifestEntry> {
        val array = JSONArray(json)
        return (0 until array.length()).map { i ->
            val obj = array.getJSONObject(i)
            ManifestEntry(
                name = obj.getString("name"),
                remote = obj.getString("remote"),
                singleFile = obj.optBoolean("single_file", false),
            )
        }
    }

    suspend fun restore(
        transport: DropboxTransport,
        engine: SyncEngine,
        remoteBase: String,
    ): RestoreResult {
        if (remoteBase.isBlank()) {
            return RestoreResult(error = "Ruta remota de saves no configurada")
        }
        val manifestFile = File.createTempFile("device-profile", ".json")
        val entries =
            try {
                transport.download(remoteBase, MANIFEST_FILENAME, manifestFile)
                parseManifest(manifestFile.readText())
            } catch (e: Exception) {
                return RestoreResult(error = e.message ?: "No se pudo descargar $MANIFEST_FILENAME")
            } finally {
                manifestFile.delete()
            }

        val applied = mutableListOf<String>()
        val skipped = mutableListOf<String>()
        var total = SyncResult()

        for (entry in entries) {
            val key = entry.remote.trimEnd('/').substringAfterLast('/')
            if (entry.singleFile) {
                val targetRelative = SINGLE_FILE_TARGETS[key]
                if (targetRelative == null) {
                    skipped += entry.name
                    continue
                }
                try {
                    val remoteDir = entry.remote.trimEnd('/').substringBeforeLast('/')
                    val destFile = File(targetRelative)
                    val mtime = transport.download(remoteDir, key, destFile)
                    destFile.setLastModified(mtime)
                    total += SyncResult(downloaded = 1)
                    applied += entry.name
                } catch (e: Exception) {
                    total += SyncResult(errors = listOf("${entry.name}: ${e.message}"))
                }
            } else {
                val targetDir = FOLDER_TARGETS[key]
                if (targetDir == null) {
                    skipped += entry.name
                    continue
                }
                total += engine.sync(File(targetDir), entry.remote)
                applied += entry.name
            }
        }
        return RestoreResult(applied, skipped, total)
    }
}
