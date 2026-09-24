package com.retrovault.android.data.auth

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.dropbox.core.oauth.DbxCredential

/**
 * Persistencia de la credencial de Dropbox (access + refresh token, PKCE)
 * cifrada con Android Keystore — nunca en `SharedPreferences` en texto
 * plano. `DbxCredential` ya trae su propio `Writer`/`Reader` JSON
 * (`dropbox-core-sdk`), reutilizado aquí sin serialización manual.
 */
class DropboxCredentialStore(context: Context) {
    private val masterKey =
        MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

    private val prefs =
        EncryptedSharedPreferences.create(
            context,
            PREFS_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )

    fun save(credential: DbxCredential) {
        prefs.edit().putString(KEY_CREDENTIAL_JSON, DbxCredential.Writer.writeToString(credential)).apply()
    }

    fun load(): DbxCredential? {
        val json = prefs.getString(KEY_CREDENTIAL_JSON, null) ?: return null
        return runCatching { DbxCredential.Reader.readFully(json) }.getOrNull()
    }

    fun clear() {
        prefs.edit().remove(KEY_CREDENTIAL_JSON).apply()
    }

    private companion object {
        const val PREFS_NAME = "dropbox_credential_store"
        const val KEY_CREDENTIAL_JSON = "credential_json"
    }
}
