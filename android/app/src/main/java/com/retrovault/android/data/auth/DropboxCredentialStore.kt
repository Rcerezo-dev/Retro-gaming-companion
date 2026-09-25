package com.retrovault.android.data.auth

import android.content.Context
import android.content.SharedPreferences
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

    private val prefs = createPrefs(context)

    // ANDROID-SYNC-FIX-2: si el blob cifrado en disco no cuadra con la clave
    // de Keystore disponible (reinstall con otra firma release/debug,
    // restore de `allowBackup`), Cipher.doFinal() lanza
    // `AEADBadTagException` sin capturar y la Activity nunca llega a
    // `setContent{}` — crash-loop permanente sin recuperación visible para
    // el usuario. Se pierde solo el token OAuth (hay que reconectar
    // Dropbox), no saves ni states, así que borrar y recrear es seguro.
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
