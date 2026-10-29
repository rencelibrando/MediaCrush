package org.example.project.theme

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

object AppColors {
    // Supabase Signature Green
    val SupabaseGreen = Color(0xFF3ECF8E)
    val SupabaseGreenHover = Color(0xFF34B27B)
    val SupabaseGreenPressed = Color(0xFF2E9F6E)
    val SupabaseGreenDark = Color(0xFF1F5C40)
    val SupabaseGreenSubtle = Color(0x1F3ECF8E)
    val SupabaseGreenBorder = Color(0x4D3ECF8E)

    // Supabase Dark Theme (Carbon & Deep Neutral)
    val DarkBackground = Color(0xFF121212)
    val DarkSurface = Color(0xFF171717)
    val DarkCard = Color(0xFF1F1F1F)
    val DarkHover = Color(0xFF262626)
    val DarkBorder = Color(0xFF2E2E2E)
    val DarkBorderSubtle = Color(0xFF222222)
    val DarkTextPrimary = Color(0xFFEDEDED)
    val DarkTextSecondary = Color(0xFFA1A1A1)
    val DarkTextMuted = Color(0xFF707070)

    // Supabase Light Theme (Clean White & Slate)
    val LightBackground = Color(0xFFFFFFFF)
    val LightSurface = Color(0xFFFAFAFA)
    val LightCard = Color(0xFFF4F4F5)
    val LightHover = Color(0xFFE4E4E7)
    val LightBorder = Color(0xFFE4E4E7)
    val LightBorderSubtle = Color(0xFFEEEEEE)
    val LightTextPrimary = Color(0xFF09090B)
    val LightTextSecondary = Color(0xFF71717A)
    val LightTextMuted = Color(0xFFA1A1AA)

    // Status Colors (Supabase inspired)
    val StatusDone = SupabaseGreen
    val StatusRunning = Color(0xFF38BDF8)
    val StatusError = Color(0xFFEF4444)
    val StatusWarning = Color(0xFFF59E0B)
    val StatusQueued = Color(0xFF888888)
}

@Composable
fun MediaCrushTheme(
    isDark: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = if (isDark) {
        darkColorScheme(
            primary = AppColors.SupabaseGreen,
            onPrimary = Color.Black,
            primaryContainer = AppColors.DarkCard,
            onPrimaryContainer = AppColors.DarkTextPrimary,
            background = AppColors.DarkBackground,
            onBackground = AppColors.DarkTextPrimary,
            surface = AppColors.DarkSurface,
            onSurface = AppColors.DarkTextPrimary,
            surfaceVariant = AppColors.DarkCard,
            onSurfaceVariant = AppColors.DarkTextSecondary,
            outline = AppColors.DarkBorder
        )
    } else {
        lightColorScheme(
            primary = AppColors.SupabaseGreen,
            onPrimary = Color.Black,
            primaryContainer = AppColors.LightCard,
            onPrimaryContainer = AppColors.LightTextPrimary,
            background = AppColors.LightBackground,
            onBackground = AppColors.LightTextPrimary,
            surface = AppColors.LightSurface,
            onSurface = AppColors.LightTextPrimary,
            surfaceVariant = AppColors.LightCard,
            onSurfaceVariant = AppColors.LightTextSecondary,
            outline = AppColors.LightBorder
        )
    }

    MaterialTheme(
        colorScheme = colorScheme,
        content = content
    )
}
