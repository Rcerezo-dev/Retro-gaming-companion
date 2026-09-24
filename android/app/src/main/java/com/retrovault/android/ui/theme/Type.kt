package com.retrovault.android.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// ponytail: the design system pairs Space Mono (display/data) with Inter
// (body) — both Google Fonts. Bundling the real .ttf files is the correct
// long-term move (README already calls for res/font/, since these
// handhelds are often offline until they reach the PC's Wi-Fi and can't
// rely on a downloadable-font fetch), but that's binary assets this
// change doesn't carry. FontFamily.Monospace/Default are the closest
// always-available system stand-ins — same weights/sizes/spacing, just
// not the exact typeface. Upgrade path: add Space Mono + Inter under
// res/font/, swap the two FontFamily values below, nothing else changes.
private val RvDisplayFont = FontFamily.Monospace
private val RvBodyFont = FontFamily.Default

/** `mono-data` from the design system — file sizes, percentages, speeds.
 * No Material3 slot fits this (it's used inline next to labels, not as a
 * whole-text-block style), so it's exposed directly for call sites. */
val RvMonoData =
    TextStyle(
        fontFamily = RvDisplayFont,
        fontWeight = FontWeight.Normal,
        fontSize = 13.sp,
        lineHeight = 18.sp,
    )

val RvTypography =
    Typography(
        // wordmark
        headlineSmall =
            TextStyle(
                fontFamily = RvDisplayFont,
                fontWeight = FontWeight.Bold,
                fontSize = 22.sp,
                lineHeight = 26.sp,
                letterSpacing = 0.5.sp,
            ),
        // stat-value
        displaySmall =
            TextStyle(
                fontFamily = RvDisplayFont,
                fontWeight = FontWeight.Bold,
                fontSize = 28.sp,
                lineHeight = 32.sp,
            ),
        // title
        titleLarge =
            TextStyle(
                fontFamily = RvBodyFont,
                fontWeight = FontWeight.SemiBold,
                fontSize = 18.sp,
                lineHeight = 24.sp,
            ),
        // body
        bodyLarge =
            TextStyle(
                fontFamily = RvBodyFont,
                fontWeight = FontWeight.Normal,
                fontSize = 14.sp,
                lineHeight = 20.sp,
            ),
        // label
        labelLarge =
            TextStyle(
                fontFamily = RvBodyFont,
                fontWeight = FontWeight.Medium,
                fontSize = 12.sp,
                lineHeight = 16.sp,
                letterSpacing = 0.3.sp,
            ),
        // caption
        labelSmall =
            TextStyle(
                fontFamily = RvBodyFont,
                fontWeight = FontWeight.Normal,
                fontSize = 11.sp,
                lineHeight = 14.sp,
            ),
    )
