package com.retrovault.android.data.auth

import android.content.Context
import com.google.android.gms.auth.api.identity.AuthorizationRequest
import com.google.android.gms.auth.api.identity.AuthorizationResult
import com.google.android.gms.auth.api.identity.Identity
import com.google.android.gms.common.api.Scope
import com.google.android.gms.tasks.Tasks

/**
 * Access token de Drive (scope `drive.file`) para [com.retrovault.android.sync.DriveRestApi]
 * vía `AuthorizationClient` — el mecanismo vigente de Google en Android; no hace falta el
 * Picker porque la app crea ella misma su carpeta `RetroSync/` (ver `ensureDriveRootFolder`).
 *
 * Bloqueante a propósito: el transporte y [com.retrovault.android.sync.SyncEngine] ya corren en
 * `Dispatchers.IO`, igual que el SDK de Dropbox. Una vez concedido el permiso, `authorize()` devuelve
 * el token en silencio (también desde WorkManager); si Google pide pantalla de consentimiento
 * ([authorize] con `hasResolution()`), un pase en segundo plano no puede mostrarla.
 */
class GoogleDriveTokenProvider(private val context: Context) {
    private fun request(): AuthorizationRequest =
        AuthorizationRequest.builder().setRequestedScopes(listOf(Scope(DRIVE_FILE_SCOPE))).build()

    /** Resultado crudo, para que la UI pueda lanzar la pantalla de consentimiento si hace falta. */
    fun authorize(): AuthorizationResult = Tasks.await(Identity.getAuthorizationClient(context).authorize(request()))

    fun accessToken(): String {
        val result = authorize()
        check(!result.hasResolution()) { "Drive necesita que vuelvas a autorizar: desconecta y reconecta Google Drive en Ajustes" }
        return checkNotNull(result.accessToken) { "Google no devolvió access token" }
    }

    private companion object {
        const val DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file"
    }
}
