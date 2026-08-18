package com.retrovault.android.data.prefs

import android.content.Context
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

    suspend fun setSavesRemote(value: String) {
        dataStore.edit { it[SAVES_REMOTE_KEY] = stripRcloneRemotePrefix(value) }
    }

    suspend fun setStatesRemote(value: String) {
        dataStore.edit { it[STATES_REMOTE_KEY] = stripRcloneRemotePrefix(value) }
    }

    companion object {
        private val SAVES_REMOTE_KEY = stringPreferencesKey("saves_remote")
        private val STATES_REMOTE_KEY = stringPreferencesKey("states_remote")
        const val DEFAULT_SAVES_REMOTE = "/RetroSync/saves"
        const val DEFAULT_STATES_REMOTE = "/RetroSync/states"
    }
}
