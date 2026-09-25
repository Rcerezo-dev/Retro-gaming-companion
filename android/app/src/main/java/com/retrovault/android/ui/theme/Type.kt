package com.retrovault.android.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.retrovault.android.R

// Space Mono (display/data) + Inter (body) — real .ttf files under
// res/font/, same Google Fonts the PC app loads (web/static/index.html).
// Offline-safe: these handhelds are often disconnected until they reach
// the PC's Wi-Fi, so a downloadable-font fetch isn't an option.
private val RvDisplayFont =
    FontFamily(
        Font(R.font.space_mono_regular, FontWeight.Normal),
        Font(R.font.space_mono_bold, FontWeight.Bold),
    )
private val RvBodyFont =
    FontFamily(
        Font(R.font.inter_regular, FontWeight.Normal),
        Font(R.font.inter_medium, FontWeight.Medium),
        Font(R.font.inter_semibold, FontWeight.SemiBold),
    )

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
