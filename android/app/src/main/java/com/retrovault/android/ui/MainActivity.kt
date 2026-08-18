package com.retrovault.android.ui

import android.Manifest
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.retrovault.android.permissions.StoragePermissionManager
import com.retrovault.android.permissions.StoragePermissionPolicy
import com.retrovault.android.ui.theme.RetroVaultSyncTheme

/**
 * Punto de entrada de la app. Antes de conceder el permiso de storage
 * muestra [StoragePermissionScreen]; una vez concedido, muestra
 * [ScanScreen] (ANDROID-SYNC-4). Ajustes (ANDROID-SYNC-8) y estado
 * (ANDROID-SYNC-14) sustituyen este contenido en fases posteriores.
 */
class MainActivity : ComponentActivity() {
    private var hasStorageAccess by mutableStateOf(false)
    private var hasNotificationAccess by mutableStateOf(false)

    private val manageStorageSettingsLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {
            refreshPermissionState()
        }

    private val legacyStoragePermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {
            refreshPermissionState()
        }

    private val notificationPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) {
            refreshPermissionState()
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        refreshPermissionState()
        setContent {
            RetroVaultSyncTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    if (hasStorageAccess) {
                        Column {
                            if (!hasNotificationAccess) {
                                NotificationPermissionBanner(
                                    modifier = Modifier.padding(innerPadding),
                                    onRequestNotificationAccess = ::requestNotificationAccess,
                                )
                            }
                            ScanScreen(modifier = Modifier.padding(innerPadding))
                        }
                    } else {
                        StoragePermissionScreen(
                            modifier = Modifier.padding(innerPadding),
                            onRequestStorageAccess = ::requestStorageAccess,
                        )
                    }
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        // El redirect a Ajustes (MANAGE_EXTERNAL_STORAGE) no siempre dispara
        // el callback del launcher de forma fiable — se recomprueba aquí.
        refreshPermissionState()
    }

    private fun refreshPermissionState() {
        hasStorageAccess = StoragePermissionManager.hasStorageAccess(this)
        hasNotificationAccess = StoragePermissionManager.hasNotificationPermission(this)
    }

    private fun requestStorageAccess() {
        if (StoragePermissionPolicy.needsManageExternalStorage(Build.VERSION.SDK_INT)) {
            manageStorageSettingsLauncher.launch(StoragePermissionManager.manageAllFilesAccessIntent(this))
        } else {
            legacyStoragePermissionLauncher.launch(StoragePermissionManager.legacyStoragePermissions)
        }
    }

    private fun requestNotificationAccess() {
        if (StoragePermissionPolicy.needsNotificationPermission(Build.VERSION.SDK_INT)) {
            notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }
}

@Composable
fun StoragePermissionScreen(
    onRequestStorageAccess: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(text = "Retro Vault Sync")
        Text(text = "Necesita acceso a las carpetas de saves/states de RetroArch")
        Button(onClick = onRequestStorageAccess) {
            Text("Conceder acceso a almacenamiento")
        }
    }
}

@Composable
fun NotificationPermissionBanner(
    onRequestNotificationAccess: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.padding(horizontal = 24.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(text = "Notificaciones necesarias para el modo de sync instantáneo")
        Button(onClick = onRequestNotificationAccess) {
            Text("Permitir notificaciones")
        }
    }
}

@Preview(showBackground = true)
@Composable
fun StoragePermissionScreenPreview() {
    RetroVaultSyncTheme {
        StoragePermissionScreen(onRequestStorageAccess = {})
    }
}
