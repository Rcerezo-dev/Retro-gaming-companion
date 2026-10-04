package com.retrovault.android.sync

import java.io.File
import java.io.FileNotFoundException

/**
 * Roadmap 28, Fase 3: [CloudTransport] sobre Google Drive. Drive direcciona
 * por `fileId`, no por ruta, así que aquí se traduce `<remoteRoot>/<relative>`
 * a IDs recorriendo desde [rootFolderId] (la carpeta `RetroSync/` elegida por
 * el usuario; con el scope `drive.file` es lo único que la app ve).
 *
 * Una ruta como `/RetroSync/saves/retroarch/saves` se interpreta relativa a
 * esa carpeta: un primer segmento igual a [rootFolderName] se descarta, así los
 * mismos ajustes que usa Dropbox (`/RetroSync/...`) valen aquí.
 *
 * mtime: `modifiedTime` de Drive, fijado explícitamente al subir — es lo que
 * compara [ConflictResolver], no el momento de la subida.
 *
 * ponytail: la caché de carpetas/archivos vive lo que dure la instancia (un
 * pase de sync) y no se invalida; si otro cliente cambia el árbol a mitad de
 * pase, el siguiente pase lo corrige. Con nombres duplicados en Drive gana el
 * más reciente — no se avisa del duplicado.
 */
class GoogleDriveTransport(
    private val api: DriveApi,
    private val rootFolderId: String,
    private val rootFolderName: String = "RetroSync",
) : CloudTransport {
    private val folderIds = HashMap<String, String>()
    private val files = HashMap<String, DriveItem>()

    internal fun segmentsOf(path: String): List<String> {
        val parts = path.split('/').filter { it.isNotEmpty() }
        return if (parts.firstOrNull()?.equals(rootFolderName, ignoreCase = true) == true) parts.drop(1) else parts
    }

    private fun resolveFolder(
        segments: List<String>,
        create: Boolean,
    ): String? {
        var id = rootFolderId
        var key = ""
        for (segment in segments) {
            key = if (key.isEmpty()) segment else "$key/$segment"
            val cached = folderIds[key]
            if (cached != null) {
                id = cached
                continue
            }
            val found = api.listChildren(id).filter { it.isFolder && it.name == segment }.maxByOrNull { it.modifiedMillis }
            id = found?.id ?: if (create) api.createFolder(id, segment).id else return null
            folderIds[key] = id
        }
        return id
    }

    private fun findFile(
        folderId: String,
        name: String,
    ): DriveItem? =
        files["$folderId/$name"]
            ?: api.listChildren(folderId).filter { !it.isFolder && it.name == name }.maxByOrNull { it.modifiedMillis }
                ?.also { files["$folderId/$name"] = it }

    override fun listFolderRecursive(remoteRoot: String): List<RemoteSave> {
        val baseSegments = segmentsOf(remoteRoot)
        val startId = resolveFolder(baseSegments, create = false) ?: return emptyList()
        val found = LinkedHashMap<String, RemoteSave>()
        val queue = ArrayDeque<Triple<String, String, String>>() // id, prefijo relativo, clave de caché
        queue.add(Triple(startId, "", baseSegments.joinToString("/")))
        while (queue.isNotEmpty()) {
            val (folderId, prefix, cacheKey) = queue.removeFirst()
            for (item in api.listChildren(folderId)) {
                if (item.isFolder) {
                    val childKey = if (cacheKey.isEmpty()) item.name else "$cacheKey/${item.name}"
                    // Con nombres repetidos, la última carpeta vista gana la caché; ambas se recorren.
                    folderIds[childKey] = item.id
                    queue.add(Triple(item.id, "$prefix${item.name}/", childKey))
                } else {
                    files["$folderId/${item.name}"] = item
                    val relative = "$prefix${item.name}"
                    val previous = found[relative]
                    if (previous == null || item.modifiedMillis >= previous.clientModifiedMillis) {
                        found[relative] = RemoteSave(relative, item.modifiedMillis, item.size, item.id)
                    }
                }
            }
        }
        return found.values.toList()
    }

    override fun upload(
        localFile: File,
        remoteRoot: String,
        relative: String,
        clientModifiedMillis: Long,
    ): RemoteSave {
        val segments = segmentsOf(remoteRoot) + relative.split('/').filter { it.isNotEmpty() }
        val name = segments.last()
        val folderId = resolveFolder(segments.dropLast(1), create = true)!!
        val existing = findFile(folderId, name)
        val item = api.uploadFile(folderId, existing?.id, name, localFile, clientModifiedMillis)
        files["$folderId/$name"] = item
        return RemoteSave(relative, item.modifiedMillis, item.size, item.id)
    }

    override fun download(
        remoteRoot: String,
        relative: String,
        destFile: File,
    ): Long {
        val segments = segmentsOf(remoteRoot) + relative.split('/').filter { it.isNotEmpty() }
        val folderId = resolveFolder(segments.dropLast(1), create = false)
        val item = folderId?.let { findFile(it, segments.last()) } ?: throw FileNotFoundException("Drive: no existe $remoteRoot/$relative")
        destFile.parentFile?.mkdirs()
        api.downloadFile(item.id, destFile)
        return item.modifiedMillis
    }
}

/**
 * Carpeta raíz `RetroSync/` en Drive. Con `drive.file` la app solo ve lo que ella creó, así que
 * en vez del Picker (que adopta una carpeta ajena) la crea ella la primera vez: [cachedId] si ya
 * se guardó, si no una `RetroSync` visible para la app, si no una nueva bajo `root`.
 *
 * Consecuencia: si el PC (rclone) ya creó su propia `RetroSync` en Drive, la app no la ve y crearía
 * una segunda con el mismo nombre — crear primero desde la app (o desde ella adoptar la del PC con
 * el Picker, no implementado).
 */
fun ensureDriveRootFolder(
    api: DriveApi,
    cachedId: String?,
    name: String = "RetroSync",
): String =
    cachedId
        ?: api.listChildren("root").filter { it.isFolder && it.name == name }.maxByOrNull { it.modifiedMillis }?.id
        ?: api.createFolder("root", name).id
