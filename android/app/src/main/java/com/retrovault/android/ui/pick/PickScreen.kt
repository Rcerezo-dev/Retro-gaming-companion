package com.retrovault.android.ui.pick

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicText
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.retrovault.android.sync.PcApiClient
import com.retrovault.android.sync.RemoteGame
import com.retrovault.android.ui.theme.RetroVaultSyncTheme
import com.retrovault.android.ui.theme.RvMonoData
import com.retrovault.android.ui.theme.RvSuccessDark
import com.retrovault.android.ui.theme.RvSuccessLight
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
 *
 * UI ported from the RetroVault design system
 * (https://claude.ai/artifact/Er8gzxt15ZF8nLAws7QqYL) — GameRow's three
 * states (idle/downloading/done), platform tag, and mono-data numerals for
 * size/progress all come from there; the color/type tokens themselves live
 * in `ui/theme/`.
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
    var downloadedIds by remember { mutableStateOf<Set<Long>>(emptySet()) }
    var lastMessage by remember { mutableStateOf<String?>(null) }
    var lastMessageOk by remember { mutableStateOf(true) }

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
            result.fold(
                onSuccess = {
                    downloadedIds = downloadedIds + game.id
                    lastMessageOk = true
                    lastMessage = "✓ ${game.originalFilename} guardado en ${game.platformFolder}/"
                },
                onFailure = {
                    lastMessageOk = false
                    lastMessage = "✗ Fallo al descargar ${game.originalFilename}: ${it.message}"
                },
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
            downloadedIds = downloadedIds,
            lastMessage = lastMessage,
            lastMessageOk = lastMessageOk,
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
        Text(text = "Elegir ROMs del PC", style = MaterialTheme.typography.titleLarge)
        Text(
            text = "Con rommgr serve corriendo en el PC, escribe su IP (Ajustes → Local URL en la app de escritorio)",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        OutlinedTextField(
            value = host,
            onValueChange = onHostChange,
            label = { Text("IP:puerto del PC (p.ej. 192.168.1.50:7777)") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        errorMessage?.let {
            Text(text = it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodyLarge)
        }
        Button(onClick = onConnect, enabled = !connecting) {
            Text(if (connecting) "Conectando…" else "Conectar")
        }
        if (connecting) CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
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
    downloadedIds: Set<Long>,
    lastMessage: String?,
    lastMessageOk: Boolean,
    onDownload: (RemoteGame) -> Unit,
    onDisconnect: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(text = "Elegir ROMs", style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
            OutlinedButton(onClick = onDisconnect) { Text("Desconectar") }
        }
        OutlinedTextField(
            value = searchText,
            onValueChange = onSearchChange,
            label = { Text("Buscar título o archivo…") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        LazyRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            item {
                FilterChip(
                    selected = selectedPlatform == null,
                    onClick = { onSelectPlatform(null) },
                    label = { Text("Todas") },
                )
            }
            items(platforms) { plat ->
                FilterChip(
                    selected = plat == selectedPlatform,
                    onClick = { onSelectPlatform(plat) },
                    label = { Text(plat) },
                )
            }
        }
        lastMessage?.let {
            Text(
                text = it,
                color = if (lastMessageOk) rvSuccessColor() else MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodyLarge,
            )
        }
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(games, key = { it.id }) { game ->
                GameRow(
                    game = game,
                    state =
                        when {
                            downloadingId == game.id -> GameRowState.Downloading(downloadProgress)
                            downloadedIds.contains(game.id) -> GameRowState.Done
                            else -> GameRowState.Idle
                        },
                    downloadsBlocked = downloadingId != null,
                    onClick = { onDownload(game) },
                )
            }
        }
    }
}

private sealed interface GameRowState {
    data object Idle : GameRowState

    data class Downloading(val progress: Float) : GameRowState

    data object Done : GameRowState
}

/**
 * The design system's `GameRow` component
 * (https://claude.ai/artifact/Er8gzxt15ZF8nLAws7QqYL — Components → GameRow),
 * built for real against `PickScreen`'s actual state instead of the static
 * HTML preview: idle (download arrow) / downloading (inline progress + live
 * percentage) / done (checkmark, row dims). Same layout across all three so
 * a row never changes height mid-transition — see the component's own
 * README for why.
 */
@Composable
private fun GameRow(
    game: RemoteGame,
    state: GameRowState,
    downloadsBlocked: Boolean,
    onClick: () -> Unit,
) {
    val borderColor =
        if (state is GameRowState.Downloading) MaterialTheme.colorScheme.outline else MaterialTheme.colorScheme.outlineVariant
    Card(
        onClick = onClick,
        enabled = state is GameRowState.Idle && !downloadsBlocked,
        shape = RoundedCornerShape(10.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        modifier =
            Modifier
                .fillMaxWidth()
                .border(1.dp, borderColor, RoundedCornerShape(10.dp)),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            PlatformTag(label = game.platform ?: "?")

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = game.canonicalTitle ?: game.originalFilename,
                    style = MaterialTheme.typography.bodyLarge,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                when (state) {
                    is GameRowState.Downloading ->
                        LinearProgressIndicator(
                            progress = { state.progress },
                            color = MaterialTheme.colorScheme.primary,
                            trackColor = MaterialTheme.colorScheme.surfaceVariant,
                            modifier = Modifier.fillMaxWidth().padding(top = 4.dp),
                        )
                    else ->
                        BasicText(text = formatBytes(game.sizeBytes), style = RvMonoData.copy(color = MaterialTheme.colorScheme.onSurfaceVariant))
                }
            }

            when (state) {
                is GameRowState.Idle ->
                    IconButton(onClick = onClick, enabled = !downloadsBlocked) {
                        Text(text = "↓", color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.titleLarge)
                    }
                is GameRowState.Downloading ->
                    BasicText(
                        text = "${(state.progress * 100).toInt()}%",
                        style = RvMonoData.copy(color = MaterialTheme.colorScheme.primary),
                    )
                is GameRowState.Done ->
                    Text(text = "✓", color = rvSuccessColor(), style = MaterialTheme.typography.titleLarge)
            }
        }
    }
}

@Composable
private fun PlatformTag(label: String) {
    Text(
        text = label.uppercase(),
        style = RvMonoData.copy(fontWeight = FontWeight.Bold, fontSize = RvMonoData.fontSize.times(0.8)),
        color = MaterialTheme.colorScheme.secondary,
        modifier =
            Modifier
                .background(MaterialTheme.colorScheme.secondary.copy(alpha = 0.14f), RoundedCornerShape(4.dp))
                .padding(horizontal = 6.dp, vertical = 3.dp),
    )
}

/** `success` isn't part of Material3's ColorScheme — RetroVault's tokens keep
 * it as a fourth semantic color alongside primary/secondary/error. One-line
 * lookup rather than a CompositionLocal: it's used in two places today. */
@Composable
private fun rvSuccessColor() = if (isSystemInDarkTheme()) RvSuccessDark else RvSuccessLight

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

@Preview(showBackground = true)
@Composable
fun PickScreenBrowserPreview() {
    val sample =
        listOf(
            RemoteGame(
                id = 1,
                platform = "SNES",
                canonicalTitle = "Super Metroid",
                originalFilename = "Super Metroid (USA).sfc",
                sourcePath = "E:/Carpetas anbernic/snes/Super Metroid (USA).sfc",
                sizeBytes = 3_100_000L,
            ),
            RemoteGame(
                id = 2,
                platform = "GBA",
                canonicalTitle = "Metroid Fusion",
                originalFilename = "Metroid Fusion (USA).gba",
                sourcePath = "E:/Carpetas anbernic/gba/Metroid Fusion (USA).gba",
                sizeBytes = 8_400_000L,
            ),
            RemoteGame(
                id = 3,
                platform = "NES",
                canonicalTitle = "Castlevania",
                originalFilename = "Castlevania (USA).nes",
                sourcePath = "E:/Carpetas anbernic/nes/Castlevania (USA).nes",
                sizeBytes = 512_000L,
            ),
        )
    RetroVaultSyncTheme {
        PickScreenBrowser(
            platforms = listOf("SNES", "GBA", "NES"),
            selectedPlatform = null,
            onSelectPlatform = {},
            searchText = "",
            onSearchChange = {},
            games = sample,
            downloadingId = 2L,
            downloadProgress = 0.38f,
            downloadedIds = setOf(3L),
            lastMessage = "✓ Castlevania (USA).nes guardado en nes/",
            lastMessageOk = true,
            onDownload = {},
            onDisconnect = {},
        )
    }
}
