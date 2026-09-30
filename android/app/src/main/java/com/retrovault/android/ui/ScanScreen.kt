package com.retrovault.android.ui

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicText
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.retrovault.android.sync.LocalFileScanner
import com.retrovault.android.sync.RetroArchPaths
import com.retrovault.android.ui.theme.RetroVaultSyncTheme
import com.retrovault.android.ui.theme.RvMonoData
import com.retrovault.android.util.formatBytes
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

/**
 * Pantalla de escaneo (ANDROID-SYNC-4): cuenta cuántos saves/states hay bajo
 * las carpetas de RetroArch, sin tocar red. Sin sync todavía — eso llega
 * con `SyncEngine` (ANDROID-SYNC-7).
 *
 * UI ported from the RetroVault design system
 * (https://claude.ai/artifact/Er8gzxt15ZF8nLAws7QqYL) — counts render as
 * `mono-data` inside a `bg-panel`/`border` card, same "numbers are
 * instrumentation" treatment `PickScreen` already gives file sizes.
 */
data class ScanCounts(val savesCount: Int, val statesCount: Int, val totalBytes: Long)

@Composable
fun ScanScreen(modifier: Modifier = Modifier) {
    var counts by remember { mutableStateOf<ScanCounts?>(null) }

    LaunchedEffect(Unit) {
        counts =
            withContext(Dispatchers.IO) {
                val saves = LocalFileScanner.scan(File(RetroArchPaths.SAVES))
                val states = LocalFileScanner.scan(File(RetroArchPaths.STATES))
                ScanCounts(
                    savesCount = saves.size,
                    statesCount = states.size,
                    totalBytes = (saves + states).sumOf { it.size },
                )
            }
    }

    ScanScreenContent(counts = counts, modifier = modifier)
}

@Composable
private fun ScanScreenContent(
    counts: ScanCounts?,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(text = "Escaneo de saves/states", style = MaterialTheme.typography.titleLarge)
        if (counts == null) {
            CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
        } else {
            Card(
                shape = RoundedCornerShape(10.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                modifier =
                    Modifier
                        .fillMaxWidth()
                        .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(10.dp)),
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    ScanStatRow(label = "Saves", value = counts.savesCount.toString())
                    ScanStatRow(label = "States", value = counts.statesCount.toString())
                    ScanStatRow(label = "Tamaño total", value = formatBytes(counts.totalBytes))
                }
            }
        }
    }
}

@Composable
private fun ScanStatRow(
    label: String,
    value: String,
) {
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        BasicText(text = value, style = RvMonoData.copy(color = MaterialTheme.colorScheme.primary))
    }
}

@Preview(showBackground = true)
@Composable
fun ScanScreenPreview() {
    RetroVaultSyncTheme {
        ScanScreenContent(counts = ScanCounts(savesCount = 42, statesCount = 17, totalBytes = 5 * 1024 * 1024))
    }
}
