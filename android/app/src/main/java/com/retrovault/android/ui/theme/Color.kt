package com.retrovault.android.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * RetroVault design-system tokens (https://claude.ai/artifact/Er8gzxt15ZF8nLAws7QqYL),
 * ported verbatim from the PC app's own palette (`web/static/app.css` --bg/--accent/
 * --fg/... custom properties) so the Android companion reads as the same product,
 * not a second brand. One `Rv*Dark`/`Rv*Light` pair per token; [Theme.kt] assembles
 * them into a Material3 `ColorScheme` per theme.
 *
 * `accent` deliberately shifts hue between themes (cyan in dark, teal in light) —
 * that's the source app's own fix for cyan failing contrast on a white ground, not
 * a mistake to unify into one hex.
 */

// bg
val RvBgBaseDark = Color(0xFF02020E)
val RvBgBaseLight = Color(0xFFF0F2F5)
val RvBgPanelDark = Color(0xFF07071F)
val RvBgPanelLight = Color(0xFFFFFFFF)
val RvBgInputDark = Color(0xFF0F0F0F)
val RvBgInputLight = Color(0xFFFFFFFF)

// border
val RvBorderDark = Color(0xFF1A1A40)
val RvBorderLight = Color(0xFFCED2E8)
val RvBorderStrongDark = Color(0xFF2D2D60)
val RvBorderStrongLight = Color(0xFF9098B4)

// text
val RvTextPrimaryDark = Color(0xFFC8D8FF)
val RvTextPrimaryLight = Color(0xFF1A1A2E)
val RvTextSecondaryDark = Color(0xFF6878A8)
val RvTextSecondaryLight = Color(0xFF505570)
val RvTextMutedDark = Color(0xFF303058)
val RvTextMutedLight = Color(0xFF808AB0)

// accent + semantic
val RvAccentDark = Color(0xFF00E5FF)
val RvAccentLight = Color(0xFF0D9B78)
val RvAccentOnDark = Color(0xFF000010)
val RvAccentOnLight = Color(0xFFFFFFFF)
val RvInfoDark = Color(0xFF4D79FF)
val RvInfoLight = Color(0xFF1A6AB8)
val RvWarningDark = Color(0xFFFF6B00)
val RvWarningLight = Color(0xFFC05020)
val RvDangerDark = Color(0xFFFF2060)
val RvDangerLight = Color(0xFFCC1111)
val RvSuccessDark = Color(0xFF39FF14)
val RvSuccessLight = Color(0xFF1A7830)
