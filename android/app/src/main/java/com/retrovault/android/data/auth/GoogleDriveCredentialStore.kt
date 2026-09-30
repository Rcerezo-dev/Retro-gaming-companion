package com.retrovault.android.data.auth

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * Persistencia de la sesión Google Drive — a diferencia de Dropbox, el SDK
 * de Google Sign-In no expone un `DbxCredential` equivalente para
 * serializar a mano (`GoogleAccountCredential` gestiona el refresh solo vía
 * `AccountManager`, ver roadmap 28 Fase 2); lo único que hace falta guardar
 * aquí es qué cuenta eligió el usuario y, cuando el Picker (incremento
 * posterior de esta fase) resuelva la carpeta `RetroSync/`, su `fileId`.
 * Mismo cifrado con Android Keystore que [DropboxCredentialStore] —
 * ninguna de las dos cosas en texto plano.
 */
class GoogleDriveCredentialStore(context: Context) {
    private val masterKey =
        MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

    private val prefs = createPrefs(context)

    // Mismo riesgo que ANDROID-SYNC-FIX-2 documentó para Dropbox: un blob
    // cifrado que ya no cuadra con la clave de Keystore disponible (reinstall
    // con otra firma, restore de allowBackup) lanza AEADBadTagException sin
    // capturar. Se pierde solo la cuenta/carpeta elegidas (hay que reconectar
    // Drive), no saves ni states.
    private fun createPrefs(context: Context): SharedPreferences =
        runCatching { buildEncryptedPrefs(context) }
            .getOrElse {
                context.deleteSharedPreferences(PREFS_NAME)
                buildEncryptedPrefs(context)
            }

    private fun buildEncryptedPrefs(context: Context): SharedPreferences =
        EncryptedSharedPreferences.create(
            context,
            PREFS_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )

    fun saveAccountEmail(email: String) {
        prefs.edit().putString(KEY_ACCOUNT_EMAIL, email).apply()
    }

    fun accountEmail(): String? = prefs.getString(KEY_ACCOUNT_EMAIL, null)

    /** `fileId` de la carpeta `RetroSync/` resuelta por el Picker — `null` hasta ese incremento. */
    fun saveFolderId(fileId: String) {
        prefs.edit().putString(KEY_FOLDER_ID, fileId).apply()
    }

    fun folderId(): String? = prefs.getString(KEY_FOLDER_ID, null)

    fun clear() {
        prefs.edit().remove(KEY_ACCOUNT_EMAIL).remove(KEY_FOLDER_ID).apply()
    }

    private companion object {
        const val PREFS_NAME = "gdrive_credential_store"
        const val KEY_ACCOUNT_EMAIL = "account_email"
        const val KEY_FOLDER_ID = "folder_id"
    }
}
