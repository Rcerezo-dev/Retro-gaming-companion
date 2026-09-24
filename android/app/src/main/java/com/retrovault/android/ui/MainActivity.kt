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
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.lifecycleScope
import com.retrovault.android.data.auth.DropboxAuthManager
import com.retrovault.android.data.auth.DropboxCredentialStore
import com.retrovault.android.data.prefs.SettingsRepository
import com.retrovault.android.permissions.StoragePermissionManager
import com.retrovault.android.permissions.StoragePermissionPolicy
import com.retrovault.android.sync.PeriodicSyncScheduler
import com.retrovault.android.sync.SyncOrchestrator
import com.retrovault.android.sync.SyncResult
import com.retrovault.android.ui.pick.PickScreen
import com.retrovault.android.ui.settings.SettingsScreen
import com.retrovault.android.ui.theme.RetroVaultSyncTheme
import kotlinx.coroutines.launch

private enum class AppTab { SCAN, PICK, SETTINGS }

/**
 * Punto de entrada de la app. Antes de conceder el permiso de storage
 * muestra [StoragePermissionScreen]; una vez concedido, alterna entre
 * [ScanScreen] y [SettingsScreen] (ANDROID-SYNC-8) mediante un selector
 * simple — sin librería de navegación, v1 solo tiene dos pantallas.
 */
class MainActivity : ComponentActivity() {
    private var hasStorageAccess by mutableStateOf(false)
    private var hasNotificationAccess by mutableStateOf(false)
    private var selectedTab by mutableStateOf(AppTab.SCAN)
    private var isDropboxConnected by mutableStateOf(false)
    private var isSyncing by mutableStateOf(false)
    private var lastSyncSummary by mutableStateOf<String?>(null)

    private val credentialStore by lazy { DropboxCredentialStore(this) }
    private val authManager by lazy { DropboxAuthManager(this, credentialStore) }
    private val settingsRepository by lazy { SettingsRepository(this) }

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
        refreshDropboxState()
        setContent {
            RetroVaultSyncTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    if (!hasStorageAccess) {
                        StoragePermissionScreen(
                            modifier = Modifier.padding(innerPadding),
                            onRequestStorageAccess = ::requestStorageAccess,
                        )
                    } else {
                        Column(modifier = Modifier.padding(innerPadding)) {
                            if (!hasNotificationAccess) {
                                NotificationPermissionBanner(onRequestNotificationAccess = ::requestNotificationAccess)
                            }
                            TabSelector(selected = selectedTab, onSelect = { selectedTab = it })
                            when (selectedTab) {
                                AppTab.SCAN -> ScanScreen()
                                AppTab.PICK -> {
                                    val pcHost by settingsRepository.pcHost.collectAsState(initial = "")
                                    val romsDestPath by settingsRepository.romsDestPath
                                        .collectAsState(initial = SettingsRepository.DEFAULT_ROMS_DEST)
                                    PickScreen(
                                        initialHost = pcHost,
                                        romsDestPath = romsDestPath,
                                        onSaveHost = { host ->
                                            lifecycleScope.launch { settingsRepository.setPcHost(host) }
                                        },
                                    )
                                }
                                AppTab.SETTINGS -> {
                                    val savesRemote by settingsRepository.savesRemote
                                        .collectAsState(initial = SettingsRepository.DEFAULT_SAVES_REMOTE)
                                    val statesRemote by settingsRepository.statesRemote
                                        .collectAsState(initial = SettingsRepository.DEFAULT_STATES_REMOTE)
                                    val autoSyncEnabled by settingsRepository.autoSyncEnabled
                                        .collectAsState(initial = false)
                                    SettingsScreen(
                                        isDropboxConfigured = authManager.isAppKeyConfigured(),
                                        isDropboxConnected = isDropboxConnected,
                                        savesRemote = savesRemote,
                                        statesRemote = statesRemote,
                                        isSyncing = isSyncing,
                                        lastSyncSummary = lastSyncSummary,
                                        autoSyncEnabled = autoSyncEnabled,
                                        onConnectDropbox = authManager::startAuth,
                                        onDisconnectDropbox = ::disconnectDropbox,
                                        onSaveRemotes = ::saveRemotes,
                                        onSyncNow = ::syncNow,
                                        onAutoSyncToggle = ::setAutoSyncEnabled,
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        // El redirect a Ajustes (MANAGE_EXTERNAL_STORAGE) y el del navegador
        // OAuth de Dropbox no siempre disparan el callback del launcher de
        // forma fiable — se recomprueba aquí en ambos casos.
        refreshPermissionState()
        authManager.finishAuthIfPending()
        refreshDropboxState()
    }

    private fun refreshPermissionState() {
        hasStorageAccess = StoragePermissionManager.hasStorageAccess(this)
        hasNotificationAccess = StoragePermissionManager.hasNotificationPermission(this)
    }

    private fun refreshDropboxState() {
        isDropboxConnected = authManager.isSignedIn()
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

    private fun disconnectDropbox() {
        authManager.signOut()
        refreshDropboxState()
    }

    private fun saveRemotes(
        saves: String,
        states: String,
    ) {
        lifecycleScope.launch {
            settingsRepository.setSavesRemote(saves)
            settingsRepository.setStatesRemote(states)
        }
    }

    private fun syncNow() {
        isSyncing = true
        lifecycleScope.launch {
            val result = SyncOrchestrator.runFullSync(this@MainActivity)
            lastSyncSummary = if (result != null) summarize(result) else "Dropbox no conectado"
            isSyncing = false
        }
    }

    private fun setAutoSyncEnabled(enabled: Boolean) {
        if (enabled) PeriodicSyncScheduler.enable(this) else PeriodicSyncScheduler.disable(this)
        lifecycleScope.launch { settingsRepository.setAutoSyncEnabled(enabled) }
    }

    private fun summarize(result: SyncResult): String {
        val base = "Subidos: ${result.uploaded} · Descargados: ${result.downloaded} · Al día: ${result.upToDate}"
        val extra =
            buildString {
                if (result.conflicts > 0) append(" · Conflictos: ${result.conflicts}")
                if (result.errors.isNotEmpty()) append(" · Errores: ${result.errors.size}")
            }
        return base + extra
    }
}

@Composable
private fun TabSelector(
    selected: AppTab,
    onSelect: (AppTab) -> Unit,
) {
    Row {
        TabButton(label = "Escaneo", isSelected = selected == AppTab.SCAN, onClick = { onSelect(AppTab.SCAN) })
        TabButton(label = "Elegir ROMs", isSelected = selected == AppTab.PICK, onClick = { onSelect(AppTab.PICK) })
        TabButton(label = "Ajustes", isSelected = selected == AppTab.SETTINGS, onClick = { onSelect(AppTab.SETTINGS) })
    }
}

@Composable
private fun TabButton(
    label: String,
    isSelected: Boolean,
    onClick: () -> Unit,
) {
    if (isSelected) {
        Button(onClick = onClick) { Text(label) }
    } else {
        TextButton(onClick = onClick) { Text(label) }
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
