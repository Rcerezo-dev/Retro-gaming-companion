package com.retrovault.android.sync

import com.dropbox.core.v2.DbxClientV2
import com.dropbox.core.v2.files.FileMetadata
import com.dropbox.core.v2.files.ListFolderErrorException
import com.dropbox.core.v2.files.WriteMode
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.util.Date

/**
 * Entrada remota de Dropbox relevante para el motor de sync — solo
 * archivos (las carpetas del listado recursivo se descartan), con su path
 * relativo a la raíz consultada y su mtime **`client_modified`, nunca
 * `server_modified`**: rclone usa `client_modified` como mtime en su
 * backend de Dropbox (ver `Tareas/Roadmap-Android-Sync.md` §1), así que el
 * motor de sync debe comparar contra exactamente ese campo para que las
 * comparaciones de mtime contra lo que sincroniza `rommgr sync-saves` en
 * el PC sean correctas.
 */
data class RemoteSave(
    val relative: String,
    val clientModifiedMillis: Long,
    val size: Long,
    val rev: String,
)

/** Construye el path remoto completo `<root>/<relative>` — espejo del join de `rclone_transport.py:290,415`. */
internal fun remotePathFor(
    root: String,
    relative: String,
): String = "${root.trimEnd('/')}/$relative"

/** Calcula el path relativo (a [root]) de un `pathDisplay` devuelto por el listado recursivo. */
internal fun relativePathFrom(
    root: String,
    fullPath: String,
): String = fullPath.removePrefix(root.trimEnd('/')).trimStart('/')

/**
 * Wrapper fino sobre [DbxClientV2] — listado recursivo, upload y download,
 * siempre fijando/leyendo `client_modified`.
 */
class DropboxTransport(private val client: DbxClientV2) {
    /**
     * Listado recursivo de [remoteRoot], solo archivos, `relative` POSIX a
     * esa raíz. Si [remoteRoot] todavía no existe en Dropbox (primer sync
     * de la cuenta/carpeta — nunca se subió nada ahí), Dropbox devuelve
     * `path/not_found` (`ListFolderErrorException`, `LookupError.NOT_FOUND`):
     * eso es un listado vacío legítimo, no un fallo — sin este caso ningún
     * usuario Android nuevo podría completar su primer sync (ANDROID-SYNC-FIX-1).
     */
    fun listFolderRecursive(remoteRoot: String): List<RemoteSave> {
        val entries = mutableListOf<RemoteSave>()
        var result =
            try {
                client.files().listFolderBuilder(remoteRoot.trimEnd('/')).withRecursive(true).start()
            } catch (e: ListFolderErrorException) {
                if (e.errorValue.isPath && e.errorValue.pathValue.isNotFound) return emptyList()
                throw e
            }
        while (true) {
            for (entry in result.entries) {
                val file = entry as? FileMetadata ?: continue
                // path_display puede venir null en la API de Dropbox (casos límite
                // documentados por ellos); path_lower es siempre el fallback seguro.
                val path = file.pathDisplay ?: file.pathLower ?: continue
                entries +=
                    RemoteSave(
                        relative = relativePathFrom(remoteRoot, path),
                        clientModifiedMillis = file.clientModified.time,
                        size = file.size,
                        rev = file.rev,
                    )
            }
            if (!result.hasMore) break
            result = client.files().listFolderContinue(result.cursor)
        }
        return entries
    }

    /** Sube [localFile] a `[remoteRoot]/[relative]`, fijando `client_modified` al mtime local. */
    fun upload(
        localFile: File,
        remoteRoot: String,
        relative: String,
        clientModifiedMillis: Long,
    ): RemoteSave {
        val remotePath = remotePathFor(remoteRoot, relative)
        val uploaded =
            FileInputStream(localFile).use { input ->
                client
                    .files()
                    .uploadBuilder(remotePath)
                    .withMode(WriteMode.OVERWRITE)
                    .withClientModified(Date(clientModifiedMillis))
                    .start()
                    .uploadAndFinish(input)
            }
        return RemoteSave(
            relative = relative,
            clientModifiedMillis = uploaded.clientModified.time,
            size = uploaded.size,
            rev = uploaded.rev,
        )
    }

    /** Descarga `[remoteRoot]/[relative]` a [destFile]; devuelve el `client_modified` remoto. */
    fun download(
        remoteRoot: String,
        relative: String,
        destFile: File,
    ): Long {
        val remotePath = remotePathFor(remoteRoot, relative)
        destFile.parentFile?.mkdirs()
        val metadata =
            FileOutputStream(destFile).use { output ->
                client.files().downloadBuilder(remotePath).start().download(output)
            }
        return metadata.clientModified.time
    }
}
