package com.retrovault.android

import android.app.Application

/**
 * Application class. A partir de ANDROID-SYNC-12 implementará
 * [androidx.work.Configuration.Provider] para el modo periódico de
 * WorkManager — sin código de sync todavía en este scaffold (ANDROID-SYNC-1).
 */
class RetroVaultApp : Application()
