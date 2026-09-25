package com.retrovault.android.ui.components

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.retrovault.android.ui.theme.RvSuccessDark
import com.retrovault.android.ui.theme.RvSuccessLight

/** Semantic tones from the design system — never `accent`, a badge reports
 * app state, it isn't a call to action. */
enum class StatusTone {
    Success,
    Info,
    Warning,
    Danger,
}

/**
 * The design system's `StatusBadge`
 * (https://claude.ai/artifact/Er8gzxt15ZF8nLAws7QqYL — Components → StatusBadge):
 * radius-pill, 6px status dot, caption-weight label. The dot pulses only for
 * an in-progress state (`pulsing = true`) — motion means "waiting," not
 * "look here."
 */
@Composable
fun StatusBadge(
    text: String,
    tone: StatusTone,
    pulsing: Boolean = false,
    modifier: Modifier = Modifier,
) {
    val color =
        when (tone) {
            StatusTone.Success -> if (isSystemInDarkTheme()) RvSuccessDark else RvSuccessLight
            StatusTone.Info -> MaterialTheme.colorScheme.secondary
            StatusTone.Warning -> MaterialTheme.colorScheme.tertiary
            StatusTone.Danger -> MaterialTheme.colorScheme.error
        }
    val dotAlpha =
        if (pulsing) {
            val transition = rememberInfiniteTransition(label = "statusBadgePulse")
            val alpha by transition.animateFloat(
                initialValue = 0.3f,
                targetValue = 1f,
                animationSpec = infiniteRepeatable(tween(700), repeatMode = RepeatMode.Reverse),
                label = "statusBadgeDotAlpha",
            )
            alpha
        } else {
            1f
        }

    Surface(shape = CircleShape, color = color.copy(alpha = 0.16f), modifier = modifier) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp),
        ) {
            Box(modifier = Modifier.size(6.dp).background(color.copy(alpha = dotAlpha), CircleShape))
            Text(
                text = text,
                color = color,
                style = MaterialTheme.typography.labelSmall.copy(fontWeight = FontWeight.SemiBold),
            )
        }
    }
}
