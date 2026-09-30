package com.retrovault.android.sync

import java.io.File

/**
 * Roadmap 28, Fase 1: forma común de un transporte de nube para [SyncEngine]
 * — extraída de [DropboxTransport] sin cambiar su comportamiento, para que
 * un proveedor nuevo (Google Drive, `GoogleDriveTransport`) pueda
 * implementarla sin tocar el motor de sync ni [ConflictResolver] (ya son
 * agnósticos de transporte, ver `.claude/roadmaps/28-android-gdrive-provider.md`).
 */
interface CloudTransport {
    /** Listado recursivo de [remoteRoot], solo archivos, `relative` POSIX a esa raíz. */
    fun listFolderRecursive(remoteRoot: String): List<RemoteSave>

    /** Sube [localFile] a `[remoteRoot]/[relative]`, fijando el mtime remoto al mtime local. */
    fun upload(
        localFile: File,
        remoteRoot: String,
        relative: String,
        clientModifiedMillis: Long,
    ): RemoteSave

    /** Descarga `[remoteRoot]/[relative]` a [destFile]; devuelve el mtime remoto. */
    fun download(
        remoteRoot: String,
        relative: String,
        destFile: File,
    ): Long
}
