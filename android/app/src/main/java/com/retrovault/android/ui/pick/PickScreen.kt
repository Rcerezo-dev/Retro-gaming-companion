package com.retrovault.android.ui.pick

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.retrovault.android.sync.PcApiClient
import com.retrovault.android.sync.RemoteGame
import com.retrovault.android.ui.theme.RetroVaultSyncTheme
import com.retrovault.android.util.formatBytes
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * FTP-PICK-2 (rediseñado): elegir ROMs del PC por HTTP en vez de FTP —
 * reutiliza `GET /api/games`/`GET /api/download-rom`, ya probados en
 * `tests/web/test_download_rom.py`. Sin sesión/login: asume PIN desactivado
 * en el PC (`allow_lan=true` por defecto, mismo modelo de confianza que ya
 * usa el resto de la app para la LAN doméstica); si el PC tiene PIN activo,
 * el PC devuelve 302/lo que sea y `PcApiClient` lo reporta como error legible,
 * sin intentar un login aquí (fuera de alcance de esta primera versión).
 */
@Composable
fun PickScreen(
    initialHost: String,
    romsDestPath: String,
    onSaveHost: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    var host by remember { mutableStateOf(initialHost) }
    var connectedBaseUrl by remember { mutableStateOf<String?>(null) }
    var connecting by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var platforms by remember { mutableStateOf<List<String>>(emptyList()) }
    var selectedPlatform by remember { mutableStateOf<String?>(null) }
    var searchText by remember { mutableStateOf("") }
    var games by remember { mutableStateOf<List<RemoteGame>>(emptyList()) }
    var downloadingId by remember { mutableStateOf<Long?>(null) }
    var downloadProgress by remember { mutableStateOf(0f) }
    var lastMessage by remember { mutableStateOf<String?>(null) }

    val coroutineScope = rememberCoroutineScope()

    fun normalizeHost(raw: String): String {
        val trimmed = raw.trim().trimEnd('/')
        return if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) trimmed else "http://$trimmed"
    }

    suspend fun refreshGames(baseUrl: String) {
        games =
            withContext(Dispatchers.IO) {
                runCatching { PcApiClient.listGames(baseUrl, selectedPlatform, searchText.ifBlank { null }) }
                    .getOrElse {
                        errorMessage = it.message
                        emptyList()
                    }
            }
    }

    fun connect() {
        val baseUrl = normalizeHost(host)
        onSaveHost(host)
        connecting = true
        errorMessage = null
        coroutineScope.launch {
            val result =
                withContext(Dispatchers.IO) {
                    runCatching {
                        val plats = PcApiClient.listPlatforms(baseUrl)
                        val list = PcApiClient.listGames(baseUrl, null, null)
                        plats to list
                    }
                }
            connecting = false
            result.onSuccess { (plats, list) ->
                connectedBaseUrl = baseUrl
                platforms = plats
                games = list
            }.onFailure { e ->
                errorMessage = e.message ?: "No se pudo conectar con el PC"
            }
        }
    }

    fun download(baseUrl: String, game: RemoteGame) {
        coroutineScope.launch {
            downloadingId = game.id
            downloadProgress = 0f
            val result =
                withContext(Dispatchers.IO) {
                    runCatching {
                        PcApiClient.downloadRom(baseUrl, game, romsDestPath) { transferred, total ->
                            if (total > 0) downloadProgress = transferred.toFloat() / total.toFloat()
                        }
                    }
                }
            downloadingId = null
            lastMessage =
                result.fold(
                    onSuccess = { "✓ ${game.originalFilename} guardado en ${game.platformFolder}/" },
                    onFailure = { "✗ Fallo al descargar ${game.originalFilename}: ${it.message}" },
                )
        }
    }

    if (connectedBaseUrl == null) {
        PickScreenConnectForm(
            host = host,
            onHostChange = { host = it },
            connecting = connecting,
            errorMessage = errorMessage,
            onConnect = ::connect,
            modifier = modifier,
        )
    } else {
        val baseUrl = connectedBaseUrl!!
        LaunchedEffect(selectedPlatform, searchText) { refreshGames(baseUrl) }
        PickScreenBrowser(
            platforms = platforms,
            selectedPlatform = selectedPlatform,
            onSelectPlatform = { selectedPlatform = it },
            searchText = searchText,
            onSearchChange = { searchText = it },
            games = games,
            downloadingId = downloadingId,
            downloadProgress = downloadProgress,
            lastMessage = lastMessage,
            onDownload = { download(baseUrl, it) },
            onDisconnect = { connectedBaseUrl = null },
            modifier = modifier,
        )
    }
}

@Composable
private fun PickScreenConnectForm(
    host: String,
    onHostChange: (String) -> Unit,
    connecting: Boolean,
    errorMessage: String?,
    onConnect: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(text = "Elegir ROMs del PC")
        Text(text = "Con rommgr serve corriendo en el PC, escribe su IP (Ajustes → Local URL en la app de escritorio)")
        OutlinedTextField(
            value = host,
            onValueChange = onHostChange,
            label = { Text("IP:puerto del PC (p.ej. 192.168.1.50:7777)") },
            modifier = Modifier.fillMaxWidth(),
        )
        errorMessage?.let { Text(text = it) }
        Button(onClick = onConnect, enabled = !connecting) {
            Text(if (connecting) "Conectando…" else "Conectar")
        }
        if (connecting) CircularProgressIndicator()
    }
}

@Composable
private fun PickScreenBrowser(
    platforms: List<String>,
    selectedPlatform: String?,
    onSelectPlatform: (String?) -> Unit,
    searchText: String,
    onSearchChange: (String) -> Unit,
    games: List<RemoteGame>,
    downloadingId: Long?,
    downloadProgress: Float,
    lastMessage: String?,
    onDownload: (RemoteGame) -> Unit,
    onDisconnect: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(text = "Elegir ROMs", modifier = Modifier.weight(1f))
            OutlinedButton(onClick = onDisconnect) { Text("Desconectar") }
        }
        OutlinedTextField(
            value = searchText,
            onValueChange = onSearchChange,
            label = { Text("Buscar título o archivo…") },
            modifier = Modifier.fillMaxWidth(),
        )
        Row(modifier = Modifier.padding(vertical = 4.dp)) {
            PlatformChip(label = "Todas", selected = selectedPlatform == null, onClick = { onSelectPlatform(null) })
        }
        LazyColumn(verticalArrangement = Arrangement.spacedBy(2.dp)) {
            items(platforms) { plat ->
                Row(modifier = Modifier.fillMaxWidth().clickable { onSelectPlatform(plat) }.padding(vertical = 4.dp)) {
                    Text(text = if (plat == selectedPlatform) "▶ $plat" else plat)
                }
            }
        }
        downloadingId?.let {
            LinearProgressIndicator(progress = downloadProgress, modifier = Modifier.fillMaxWidth())
        }
        lastMessage?.let { Text(text = it) }
        LazyColumn(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            items(games) { game ->
                Row(
                    modifier =
                        Modifier
                            .fillMaxWidth()
                            .clickable(enabled = downloadingId == null) { onDownload(game) }
                            .padding(vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(text = "🎮", modifier = Modifier.padding(end = 8.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(text = game.canonicalTitle ?: game.originalFilename)
                        Text(text = "${game.platform ?: "?"} · ${formatBytes(game.sizeBytes)}")
                    }
                    Text(text = if (downloadingId == game.id) "…" else "⬇")
                }
            }
        }
    }
}

@Composable
private fun PlatformChip(
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
) {
    OutlinedButton(onClick = onClick) {
        Text(text = if (selected) "▶ $label" else label)
    }
}

@Preview(showBackground = true)
@Composable
fun PickScreenConnectFormPreview() {
    RetroVaultSyncTheme {
        PickScreenConnectForm(
            host = "192.168.1.50:7777",
            onHostChange = {},
            connecting = false,
            errorMessage = null,
            onConnect = {},
        )
    }
}
