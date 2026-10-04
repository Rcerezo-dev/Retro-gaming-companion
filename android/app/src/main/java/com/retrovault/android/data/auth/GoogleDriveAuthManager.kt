package com.retrovault.android.data.auth

import android.content.Context
import android.content.Intent
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInAccount
import com.google.android.gms.auth.api.signin.GoogleSignInClient
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.common.api.ApiException
import com.google.android.gms.common.api.Scope
import com.retrovault.android.BuildConfig

/**
 * Sign-In de Google con el scope `drive.file` (roadmap 28, Fase 2) — a
 * diferencia de [DropboxAuthManager.startAuth] (navegador del sistema vía
 * `Auth.startOAuth2PKCE`, sin resultado de Activity), Google Sign-In se
 * resuelve con un [Intent] que la Activity/Composable que llama debe lanzar
 * con su propio `ActivityResultLauncher` y devolver aquí a
 * [handleSignInResult] — no hay callback estático equivalente a
 * `Auth.getDbxCredential()`.
 *
 * El cliente OAuth Android (`GDRIVE_CLIENT_ID`) no se pasa explícitamente al
 * SDK: Google lo resuelve del lado del servidor por `applicationId` +
 * huella SHA-1 del APK firmante (registrados en la Fase 0). Su único uso
 * aquí es como bandera de "¿completó el usuario la Fase 0?" — igual que
 * `DROPBOX_APP_KEY` para Dropbox.
 *
 * La selección de la carpeta `RetroSync/` ya existente (Picker) es un
 * incremento posterior de esta misma fase; hasta entonces
 * [GoogleDriveCredentialStore.folderId] es siempre `null` y no hay forma de
 * sincronizar de verdad contra Drive — este manager solo cubre el login.
 */
class GoogleDriveAuthManager(
    context: Context,
    private val credentialStore: GoogleDriveCredentialStore = GoogleDriveCredentialStore(context),
) {
    private val appContext = context.applicationContext

    /** Motivo del último fallo de [handleSignInResult] (p. ej. "código 10" = DEVELOPER_ERROR: SHA-1/paquete no coinciden), o `null`. */
    var lastError: String? = null
        private set

    fun isClientIdConfigured(): Boolean = BuildConfig.GDRIVE_CLIENT_ID.isNotBlank()

    private fun signInClient(): GoogleSignInClient {
        check(isClientIdConfigured()) { "GDRIVE_CLIENT_ID no configurada — ver local.properties.example" }
        val options =
            GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
                .requestEmail()
                .requestScopes(Scope(DRIVE_FILE_SCOPE))
                .build()
        return GoogleSignIn.getClient(appContext, options)
    }

    /** Intent a lanzar con `ActivityResultContracts.StartActivityForResult()` desde quien llama. */
    fun signInIntent(): Intent = signInClient().signInIntent

    /** Llamar desde el callback del `ActivityResultLauncher` que lanzó [signInIntent]. */
    fun handleSignInResult(data: Intent?): GoogleSignInAccount? {
        val task = GoogleSignIn.getSignedInAccountFromIntent(data)
        lastError = null
        val account =
            runCatching { task.getResult(ApiException::class.java) }
                .onFailure { lastError = (it as? ApiException)?.let { e -> "código ${e.statusCode}" } ?: it.message }
                .getOrNull() ?: return null
        val email = account.email ?: return null
        credentialStore.saveAccountEmail(email)
        return account
    }

    fun isSignedIn(): Boolean = credentialStore.accountEmail() != null

    fun signOut() {
        credentialStore.clear()
        runCatching { signInClient().signOut() }
    }

    /**
     * Mismo criterio que `DropboxAuthManager.fetchAccountLabel()` (hallazgo
     * ANDROID-SYNC-CRITICAL-1): mostrar un identificador de cuenta
     * inequívoco, nunca fiarse solo del nombre visible. A diferencia de
     * Dropbox, Google Sign-In no expone un `account_id` propio — el email ya
     * es el identificador único de cuenta aquí.
     */
    fun fetchAccountLabel(): String? = credentialStore.accountEmail()

    private companion object {
        const val DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file"
    }
}
