package com.retrovault.android.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import com.retrovault.android.ui.theme.RetroVaultSyncTheme

/**
 * Punto de entrada de la app. Placeholder del scaffold (ANDROID-SYNC-1) —
 * la pantalla de escaneo (ANDROID-SYNC-4), Ajustes (ANDROID-SYNC-8) y estado
 * (ANDROID-SYNC-14) sustituyen este contenido en fases posteriores.
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            RetroVaultSyncTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    Greeting(modifier = Modifier.padding(innerPadding))
                }
            }
        }
    }
}

@Composable
fun Greeting(modifier: Modifier = Modifier) {
    Text(text = "Retro Vault Sync — en construcción", modifier = modifier)
}

@Preview(showBackground = true)
@Composable
fun GreetingPreview() {
    RetroVaultSyncTheme {
        Greeting()
    }
}
