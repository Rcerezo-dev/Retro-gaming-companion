package com.retrovault.android.data.auth

import com.dropbox.core.DbxRequestConfig
import com.dropbox.core.v2.DbxClientV2

/** Construye un [DbxClientV2] a partir de la credencial guardada, o `null` si no hay sesión. */
class DropboxClientProvider(private val credentialStore: DropboxCredentialStore) {
    private val requestConfig: DbxRequestConfig = DbxRequestConfig.newBuilder(CLIENT_IDENTIFIER).build()

    fun client(): DbxClientV2? {
        val credential = credentialStore.load() ?: return null
        return DbxClientV2(requestConfig, credential)
    }

    private companion object {
        const val CLIENT_IDENTIFIER = "retrovault-android"
    }
}
