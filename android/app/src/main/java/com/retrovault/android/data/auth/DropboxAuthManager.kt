package com.retrovault.android.data.auth

import android.content.Context
import com.dropbox.core.DbxRequestConfig
import com.dropbox.core.android.Auth
import com.dropbox.core.oauth.DbxCredential
import com.retrovault.android.BuildConfig

/**
 * Flujo OAuth PKCE de Dropbox (`Auth.startOAuth2PKCE`, navegador del
 * sistema — sin App Secret embebido en el APK, PKCE no lo necesita) y
 * persistencia de la credencial resultante.
 *
 * La App Key real se inyecta vía `local.properties` → `BuildConfig`
 * (ver `app/build.gradle.kts` y `local.properties.example`) — nunca
 * hardcodeada ni versionada. Sin ella, [isAppKeyConfigured] es `false` y la
 * UI debe deshabilitar el flujo en vez de lanzar un `Auth.startOAuth2PKCE`
 * que fallaría igualmente contra la API de Dropbox.
 */
class DropboxAuthManager(
    context: Context,
    private val credentialStore: DropboxCredentialStore = DropboxCredentialStore(context),
) {
    private val appContext = context.applicationContext
    private val requestConfig: DbxRequestConfig = DbxRequestConfig.newBuilder(CLIENT_IDENTIFIER).build()

    fun isAppKeyConfigured(): Boolean = BuildConfig.DROPBOX_APP_KEY.isNotBlank()

    fun startAuth() {
        check(isAppKeyConfigured()) { "DROPBOX_APP_KEY no configurada — ver local.properties.example" }
        Auth.startOAuth2PKCE(appContext, BuildConfig.DROPBOX_APP_KEY, requestConfig, SCOPES)
    }

    /**
     * Llamar desde `onResume()` de la Activity que lanzó [startAuth] —
     * `Auth.getDbxCredential()` solo devuelve algo distinto de `null` justo
     * después de volver del navegador tras un login completado.
     */
    fun finishAuthIfPending(): DbxCredential? {
        val credential = Auth.getDbxCredential() ?: return null
        credentialStore.save(credential)
        return credential
    }

    fun currentCredential(): DbxCredential? = credentialStore.load()

    fun isSignedIn(): Boolean = currentCredential() != null

    fun signOut() {
        credentialStore.clear()
    }

    private companion object {
        const val CLIENT_IDENTIFIER = "retrovault-android"
        val SCOPES = listOf("files.metadata.read", "files.content.read", "files.content.write")
    }
}
