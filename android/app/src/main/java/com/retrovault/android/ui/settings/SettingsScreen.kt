package com.retrovault.android.ui.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.retrovault.android.ui.theme.RetroVaultSyncTheme

/**
 * Ajustes (ANDROID-SYNC-8): conectar/desconectar Dropbox, paths remotos de
 * saves/states (auto-recorte de prefijo rclone al guardar, ver
 * [com.retrovault.android.data.prefs.stripRcloneRemotePrefix]) y sync
 * manual. Sin QR/emparejamiento en v1 — un pegado manual una sola vez es
 * fricción suficientemente baja (decisión ya tomada, ver
 * `Tareas/Roadmap-Android-Sync.md` §6).
 */
@Composable
fun SettingsScreen(
    isDropboxConfigured: Boolean,
    isDropboxConnected: Boolean,
    savesRemote: String,
    statesRemote: String,
    isSyncing: Boolean,
    lastSyncSummary: String?,
    autoSyncEnabled: Boolean,
    onConnectDropbox: () -> Unit,
    onDisconnectDropbox: () -> Unit,
    onSaveRemotes: (saves: String, states: String) -> Unit,
    onSyncNow: () -> Unit,
    onAutoSyncToggle: (Boolean) -> Unit,
    modifier: Modifier = Modifier,
) {
    var savesField by remember(savesRemote) { mutableStateOf(savesRemote) }
    var statesField by remember(statesRemote) { mutableStateOf(statesRemote) }

    Column(
        modifier = modifier.padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(text = "Ajustes")

        if (!isDropboxConfigured) {
            Text(text = "Sin App Key de Dropbox configurada — ver android/local.properties.example")
        } else if (isDropboxConnected) {
            Text(text = "✓ Dropbox conectado")
            OutlinedButton(onClick = onDisconnectDropbox) {
                Text("Desconectar Dropbox")
            }
        } else {
            Text(text = "Dropbox no conectado")
            Button(onClick = onConnectDropbox) {
                Text("Conectar Dropbox")
            }
        }

        OutlinedTextField(
            value = savesField,
            onValueChange = { savesField = it },
            label = { Text("Ruta remota de saves") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = statesField,
            onValueChange = { statesField = it },
            label = { Text("Ruta remota de states") },
            modifier = Modifier.fillMaxWidth(),
        )
        Button(onClick = { onSaveRemotes(savesField, statesField) }) {
            Text("Guardar rutas")
        }

        if (isDropboxConnected) {
            Button(onClick = onSyncNow, enabled = !isSyncing) {
                Text(if (isSyncing) "Sincronizando…" else "Sincronizar ahora")
            }
            if (isSyncing) {
                CircularProgressIndicator()
            }
            lastSyncSummary?.let { Text(text = it) }

            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(text = "Sync automático (cada 15 min)")
                Switch(checked = autoSyncEnabled, onCheckedChange = onAutoSyncToggle)
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
fun SettingsScreenPreview() {
    RetroVaultSyncTheme {
        SettingsScreen(
            isDropboxConfigured = true,
            isDropboxConnected = true,
            savesRemote = "/RetroSync/saves",
            statesRemote = "/RetroSync/states",
            isSyncing = false,
            lastSyncSummary = "Subidos: 2 · Descargados: 0 · Al día: 41",
            autoSyncEnabled = true,
            onConnectDropbox = {},
            onDisconnectDropbox = {},
            onSaveRemotes = { _, _ -> },
            onSyncNow = {},
            onAutoSyncToggle = {},
        )
    }
}
