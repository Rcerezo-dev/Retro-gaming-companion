package com.retrovault.android.sync

import java.io.File

/**
 * Un save/state encontrado en el filesystem local, con su path relativo a
 * la raíz de escaneo (saves/ o states/) — mismo campo `relative` que usará
 * el motor de sync (ANDROID-SYNC-7) para comparar contra el listado remoto
 * de Dropbox, espejo de `relative` en `save_syncer.py:66`.
 */
data class LocalSave(
    val relative: String,
    val absolute: File,
    val mtimeMillis: Long,
    val size: Long,
)

/**
 * Recorrido recursivo de una raíz (saves/ o states/ de RetroArch), filtrando
 * solo a extensiones reconocidas — espejo del filtro `ext_set` de
 * `list_local_saves()` en `src/rom_manager/sync/save_syncer.py:51-68`: nunca
 * se recogen archivos de extensión desconocida.
 */
object LocalFileScanner {
    fun scan(root: File): List<LocalSave> {
        if (!root.isDirectory) return emptyList()
        val rootPath = root.toPath()
        return root
            .walkTopDown()
            .filter { it.isFile }
            .filter { SaveExtensions.isTracked(it.extensionWithDot()) }
            .map { file ->
                LocalSave(
                    relative =
                        rootPath.relativize(file.toPath()).toString()
                            .replace(File.separatorChar, '/'),
                    absolute = file,
                    mtimeMillis = file.lastModified(),
                    size = file.length(),
                )
            }
            .toList()
    }
}

private fun File.extensionWithDot(): String {
    val ext = extension
    return if (ext.isEmpty()) "" else ".$ext"
}
