package com.retrovault.android.sync

import android.content.Context
import com.retrovault.android.data.auth.DropboxClientProvider
import com.retrovault.android.data.auth.DropboxCredentialStore
import com.retrovault.android.data.auth.GoogleDriveCredentialStore
import com.retrovault.android.data.auth.GoogleDriveTokenProvider
import com.retrovault.android.data.prefs.SettingsRepository

/**
 * ANDROID-DRIVE-1 Fase 4: construye el [CloudTransport] del proveedor elegido en Ajustes.
 * `null` si ese proveedor no tiene sesión (mismo significado que antes con Dropbox: no hay nada que sincronizar).
 *
 * Bloqueante en Drive (token + carpeta raíz): se llama desde el pase de sync, que ya corre en IO.
 */
object CloudProviderFactory {
    fun create(
        context: Context,
        provider: String,
    ): CloudTransport? =
        when (provider) {
            SettingsRepository.PROVIDER_GDRIVE -> createDrive(context)
            else -> DropboxClientProvider(DropboxCredentialStore(context)).client()?.let(::DropboxTransport)
        }

    private fun createDrive(context: Context): CloudTransport? {
        val store = GoogleDriveCredentialStore(context)
        if (store.accountEmail() == null) return null
        val tokens = GoogleDriveTokenProvider(context)
        val api = DriveRestApi { tokens.accessToken() }
        val rootId = ensureDriveRootFolder(api, store.folderId()).also { store.saveFolderId(it) }
        return GoogleDriveTransport(api, rootId)
    }
}
