package com.retrovault.android.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext

private val RvDarkColorScheme =
    darkColorScheme(
        primary = RvAccentDark,
        onPrimary = RvAccentOnDark,
        secondary = RvInfoDark,
        onSecondary = RvAccentOnDark,
        tertiary = RvWarningDark,
        onTertiary = RvAccentOnDark,
        error = RvDangerDark,
        onError = RvAccentOnDark,
        background = RvBgBaseDark,
        onBackground = RvTextPrimaryDark,
        surface = RvBgPanelDark,
        onSurface = RvTextPrimaryDark,
        surfaceVariant = RvBgInputDark,
        onSurfaceVariant = RvTextSecondaryDark,
        outline = RvBorderStrongDark,
        outlineVariant = RvBorderDark,
    )

private val RvLightColorScheme =
    lightColorScheme(
        primary = RvAccentLight,
        onPrimary = RvAccentOnLight,
        secondary = RvInfoLight,
        onSecondary = RvAccentOnLight,
        tertiary = RvWarningLight,
        onTertiary = RvAccentOnLight,
        error = RvDangerLight,
        onError = RvAccentOnLight,
        background = RvBgBaseLight,
        onBackground = RvTextPrimaryLight,
        surface = RvBgPanelLight,
        onSurface = RvTextPrimaryLight,
        surfaceVariant = RvBgInputLight,
        onSurfaceVariant = RvTextSecondaryLight,
        outline = RvBorderStrongLight,
        outlineVariant = RvBorderLight,
    )

@Composable
fun RetroVaultSyncTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    // DESIGN-1: Material You (wallpaper-derived color) defaults OFF —
    // RetroVault ported its own brand palette from the PC app; letting the
    // OS wallpaper override it on API 31+ would defeat the point. Left as
    // an explicit opt-in rather than removed, in case that's ever wanted.
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit,
) {
    val colorScheme =
        when {
            dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
                val context = LocalContext.current
                if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
            }
            darkTheme -> RvDarkColorScheme
            else -> RvLightColorScheme
        }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = RvTypography,
        content = content,
    )
}
