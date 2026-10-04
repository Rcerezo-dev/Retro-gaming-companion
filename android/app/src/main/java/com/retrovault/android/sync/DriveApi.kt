package com.retrovault.android.sync

import java.io.File

/** Archivo o carpeta de Drive tal como lo necesita [GoogleDriveTransport]. */
data class DriveItem(
    val id: String,
    val name: String,
    val isFolder: Boolean,
    val modifiedMillis: Long,
    val size: Long,
)

/**
 * Capa mínima de la API REST de Drive v3 que usa [GoogleDriveTransport]
 * (roadmap 28, Fase 3). Separada del transporte para poder testear la
 * resolución de rutas→IDs sin red; la implementación real es [DriveRestApi].
 */
interface DriveApi {
    /** Hijos directos de [parentId] (sin papelera). Puede haber nombres repetidos: Drive los permite. */
    fun listChildren(parentId: String): List<DriveItem>

    fun createFolder(
        parentId: String,
        name: String,
    ): DriveItem

    /** Crea ([existingId] `null`) o reemplaza el contenido de un archivo, fijando su `modifiedTime`. */
    fun uploadFile(
        parentId: String,
        existingId: String?,
        name: String,
        file: File,
        modifiedMillis: Long,
    ): DriveItem

    fun downloadFile(
        fileId: String,
        dest: File,
    )
}
