package com.retrovault.android.ui.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
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
import com.retrovault.android.data.db.SyncHistoryEntity
import com.retrovault.android.data.db.SyncOutcome
import com.retrovault.android.data.db.outcome
import com.retrovault.android.data.db.summary
import com.retrovault.android.data.db.triggerLabel
import com.retrovault.android.ui.components.StatusBadge
import com.retrovault.android.ui.components.StatusTone
import com.retrovault.android.ui.theme.RetroVaultSyncTheme
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

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
    dropboxAccountLabel: String? = null,
    savesRemote: String,
    statesRemote: String,
    isSyncing: Boolean,
    lastSyncSummary: String?,
    autoSyncEnabled: Boolean,
    instantSyncEnabled: Boolean = false,
    syncHistory: List<SyncHistoryEntity> = emptyList(),
    onConnectDropbox: () -> Unit,
    onDisconnectDropbox: () -> Unit,
    onSaveRemotes: (saves: String, states: String) -> Unit,
    onSyncNow: () -> Unit,
    onAutoSyncToggle: (Boolean) -> Unit,
    onInstantSyncToggle: (Boolean) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    var savesField by remember(savesRemote) { mutableStateOf(savesRemote) }
    var statesField by remember(statesRemote) { mutableStateOf(statesRemote) }

    Column(
        modifier = modifier.padding(24.dp).verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(text = "Ajustes", style = MaterialTheme.typography.titleLarge)

        if (!isDropboxConfigured) {
            Text(
                text = "Sin App Key de Dropbox configurada — ver android/local.properties.example",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        } else if (isDropboxConnected) {
            StatusBadge(text = "Conectado", tone = StatusTone.Success)
            dropboxAccountLabel?.let {
                Text(text = it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            OutlinedButton(onClick = onDisconnectDropbox) {
                Text("Desconectar Dropbox")
            }
        } else {
            StatusBadge(text = "No conectado", tone = StatusTone.Danger)
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
                CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
            }
            lastSyncSummary?.let {
                Text(text = it, style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }

            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(text = "Sync automático (cada 15 min)", style = MaterialTheme.typography.bodyLarge)
                Switch(checked = autoSyncEnabled, onCheckedChange = onAutoSyncToggle)
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(text = "Sync instantáneo (al guardar)", style = MaterialTheme.typography.bodyLarge)
                Switch(checked = instantSyncEnabled, onCheckedChange = onInstantSyncToggle)
            }

            if (syncHistory.isNotEmpty()) {
                Text(text = "Historial de sync", style = MaterialTheme.typography.titleMedium)
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    syncHistory.forEach { event -> SyncHistoryRow(event) }
                }
            }
        }
    }
}

private val historyTimestampFormat: DateTimeFormatter = DateTimeFormatter.ofPattern("dd/MM HH:mm")

private fun SyncOutcome.toTone(): StatusTone =
    when (this) {
        SyncOutcome.SUCCESS -> StatusTone.Success
        SyncOutcome.WARNING -> StatusTone.Warning
        SyncOutcome.ERROR -> StatusTone.Danger
    }

@Composable
private fun SyncHistoryRow(event: SyncHistoryEntity) {
    Column {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            StatusBadge(text = event.triggerLabel(), tone = event.outcome().toTone())
            Text(
                text = Instant.ofEpochMilli(event.timestampMillis).atZone(ZoneId.systemDefault()).format(historyTimestampFormat),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Text(text = event.summary(), style = MaterialTheme.typography.bodyMedium)
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
