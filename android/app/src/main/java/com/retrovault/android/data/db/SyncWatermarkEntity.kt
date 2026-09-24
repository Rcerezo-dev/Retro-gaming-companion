package com.retrovault.android.data.db

import androidx.room.Entity

/**
 * Watermark de la última sincronización exitosa de un archivo — clave
 * compuesta `(relative, remoteRoot)`, no solo `relative`: si el usuario
 * cambia el path remoto en Ajustes, un watermark viejo contra otro remote
 * no debe reutilizarse (espejo de `sync_log.py:100-121`, `get_last_sync`).
 */
@Entity(tableName = "sync_watermark", primaryKeys = ["relative", "remoteRoot"])
data class SyncWatermarkEntity(
    val relative: String,
    val remoteRoot: String,
    val lastSyncMillis: Long,
)
