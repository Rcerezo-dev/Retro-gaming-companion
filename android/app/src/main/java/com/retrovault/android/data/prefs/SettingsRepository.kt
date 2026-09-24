package com.retrovault.android.data.prefs

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "retrovault_settings")

/**
 * Paths remotos de Dropbox para saves/states — convención documentada en
 * `Tareas/Roadmap-Android-Sync.md` §1 (`/RetroSync/saves`, `/RetroSync/states`),
 * la misma que ya usa el script Termux que esta app sustituye.
 */
class SettingsRepository(context: Context) {
    private val dataStore = context.applicationContext.dataStore

    val savesRemote: Flow<String> = dataStore.data.map { it[SAVES_REMOTE_KEY] ?: DEFAULT_SAVES_REMOTE }
    val statesRemote: Flow<String> = dataStore.data.map { it[STATES_REMOTE_KEY] ?: DEFAULT_STATES_REMOTE }

    /** ANDROID-SYNC-12: sync automático cada 15 min vía WorkManager, off por defecto. */
    val autoSyncEnabled: Flow<Boolean> = dataStore.data.map { it[AUTO_SYNC_ENABLED_KEY] ?: false }

    // FTP-PICK-2 (rediseñado a HTTP): IP:puerto del PC (`rommgr serve`) y
    // carpeta destino de los ROMs elegidos.
    val pcHost: Flow<String> = dataStore.data.map { it[PC_HOST_KEY] ?: "" }
    val romsDestPath: Flow<String> = dataStore.data.map { it[ROMS_DEST_KEY] ?: DEFAULT_ROMS_DEST }

    suspend fun setPcHost(value: String) {
        dataStore.edit { it[PC_HOST_KEY] = value }
    }

    suspend fun setRomsDestPath(value: String) {
        dataStore.edit { it[ROMS_DEST_KEY] = value }
    }

    suspend fun setSavesRemote(value: String) {
        dataStore.edit { it[SAVES_REMOTE_KEY] = stripRcloneRemotePrefix(value) }
    }

    suspend fun setStatesRemote(value: String) {
        dataStore.edit { it[STATES_REMOTE_KEY] = stripRcloneRemotePrefix(value) }
    }

    suspend fun setAutoSyncEnabled(value: Boolean) {
        dataStore.edit { it[AUTO_SYNC_ENABLED_KEY] = value }
    }

    companion object {
        private val SAVES_REMOTE_KEY = stringPreferencesKey("saves_remote")
        private val STATES_REMOTE_KEY = stringPreferencesKey("states_remote")
        private val AUTO_SYNC_ENABLED_KEY = booleanPreferencesKey("auto_sync_enabled")
        private val PC_HOST_KEY = stringPreferencesKey("pc_host")
        private val ROMS_DEST_KEY = stringPreferencesKey("roms_dest_path")
        const val DEFAULT_SAVES_REMOTE = "/RetroSync/saves"
        const val DEFAULT_STATES_REMOTE = "/RetroSync/states"
        // HERR-FIX-3: convención ya adoptada para ROMs en la SD (`<raíz>/ROMs/<plataforma>`,
        // ver DEVICE-DUP-1) — de todas formas editable, cada dispositivo monta la SD distinto.
        const val DEFAULT_ROMS_DEST = "/storage/emulated/0/ROMs"
    }
}
