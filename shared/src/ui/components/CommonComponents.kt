package org.example.project.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.example.project.theme.AppColors

@Composable
fun SupabasePrimaryButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    icon: ImageVector? = null,
    isDark: Boolean = true
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        shape = RoundedCornerShape(6.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = AppColors.SupabaseGreen,
            contentColor = Color.Black,
            disabledContainerColor = if (isDark) Color(0xFF262626) else Color(0xFFE5E7EB),
            disabledContentColor = if (isDark) Color(0xFF666666) else Color(0xFF9CA3AF)
        ),
        modifier = modifier.height(34.dp),
        contentPadding = PaddingValues(horizontal = 14.dp, vertical = 4.dp)
    ) {
        if (icon != null) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                modifier = Modifier.size(15.dp),
                tint = if (enabled) Color.Black else if (isDark) Color(0xFF666666) else Color(0xFF9CA3AF)
            )
            Spacer(modifier = Modifier.width(6.dp))
        }
        Text(
            text = text,
            fontSize = 12.sp,
            fontWeight = FontWeight.SemiBold
        )
    }
}

@Composable
fun SupabaseSecondaryButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    icon: ImageVector? = null,
    isDark: Boolean = true
) {
    val bg = if (isDark) AppColors.DarkCard else AppColors.LightCard
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder
    val textCol = if (isDark) AppColors.DarkTextPrimary else AppColors.LightTextPrimary

    Button(
        onClick = onClick,
        enabled = enabled,
        shape = RoundedCornerShape(6.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = bg,
            contentColor = textCol,
            disabledContainerColor = if (isDark) Color(0xFF1F1F1F) else Color(0xFFF4F4F5),
            disabledContentColor = if (isDark) Color(0xFF666666) else Color(0xFFA1A1AA)
        ),
        border = androidx.compose.foundation.BorderStroke(1.dp, borderCol),
        modifier = modifier.height(34.dp),
        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
    ) {
        if (icon != null) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                modifier = Modifier.size(14.dp),
                tint = if (enabled) textCol else (if (isDark) Color(0xFF666666) else Color(0xFFA1A1AA))
            )
            Spacer(modifier = Modifier.width(6.dp))
        }
        Text(
            text = text,
            fontSize = 12.sp,
            fontWeight = FontWeight.Medium
        )
    }
}

@Composable
fun SupabaseDangerButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    icon: ImageVector? = null,
    isDark: Boolean = true
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        shape = RoundedCornerShape(6.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = Color(0x1DEF4444),
            contentColor = Color(0xFFF87171),
            disabledContainerColor = if (isDark) Color(0xFF1F1F1F) else Color(0xFFF4F4F5),
            disabledContentColor = if (isDark) Color(0xFF666666) else Color(0xFFA1A1AA)
        ),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0x40EF4444)),
        modifier = modifier.height(34.dp),
        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
    ) {
        if (icon != null) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                modifier = Modifier.size(14.dp),
                tint = if (enabled) Color(0xFFF87171) else (if (isDark) Color(0xFF666666) else Color(0xFFA1A1AA))
            )
            Spacer(modifier = Modifier.width(6.dp))
        }
        Text(
            text = text,
            fontSize = 12.sp,
            fontWeight = FontWeight.Medium
        )
    }
}

@Composable
fun SupabaseIconButton(
    icon: ImageVector,
    onClick: () -> Unit,
    tooltip: String,
    modifier: Modifier = Modifier,
    isDark: Boolean = true
) {
    val bg = if (isDark) AppColors.DarkCard else AppColors.LightCard
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder
    val iconTint = if (isDark) AppColors.DarkTextSecondary else AppColors.LightTextSecondary

    Box(
        modifier = modifier
            .size(32.dp)
            .clip(RoundedCornerShape(6.dp))
            .background(bg)
            .border(1.dp, borderCol, RoundedCornerShape(6.dp))
            .clickable { onClick() },
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = icon,
            contentDescription = tooltip,
            modifier = Modifier.size(16.dp),
            tint = iconTint
        )
    }
}

@Composable
fun StatusBadge(
    status: String,
    modifier: Modifier = Modifier
) {
    val (dotCol, bgCol, textCol) = when (status.lowercase()) {
        "done" -> Triple(AppColors.SupabaseGreen, Color(0x1A3ECF8E), AppColors.SupabaseGreen)
        "running" -> Triple(AppColors.StatusRunning, Color(0x1A38BDF8), AppColors.StatusRunning)
        "queued" -> Triple(Color(0xFF888888), Color(0x1A888888), Color(0xFFA1A1AA))
        "error" -> Triple(AppColors.StatusError, Color(0x1AEF4444), Color(0xFFF87171))
        "skipped" -> Triple(AppColors.StatusWarning, Color(0x1AF59E0B), Color(0xFFFBBF24))
        "cancelled" -> Triple(Color(0xFF666666), Color(0x1A666666), Color(0xFF888888))
        "paused" -> Triple(AppColors.StatusWarning, Color(0x1AF59E0B), Color(0xFFFBBF24))
        else -> Triple(Color(0xFF888888), Color(0x1A888888), Color(0xFFA1A1AA))
    }

    Row(
        modifier = modifier
            .clip(RoundedCornerShape(4.dp))
            .background(bgCol)
            .border(1.dp, dotCol.copy(alpha = 0.3f), RoundedCornerShape(4.dp))
            .padding(horizontal = 7.dp, vertical = 2.5.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(6.dp)
                .clip(CircleShape)
                .background(dotCol)
        )
        Spacer(modifier = Modifier.width(5.dp))
        Text(
            text = status,
            color = textCol,
            fontSize = 11.sp,
            fontWeight = FontWeight.Medium
        )
    }
}

@Composable
fun MetricCell(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    isDark: Boolean = true
) {
    val bg = if (isDark) AppColors.DarkBackground else AppColors.LightBackground
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder
    val labelCol = if (isDark) AppColors.DarkTextSecondary else AppColors.LightTextSecondary
    val valCol = if (isDark) AppColors.DarkTextPrimary else AppColors.LightTextPrimary

    Column(
        modifier = modifier
            .clip(RoundedCornerShape(6.dp))
            .background(bg)
            .border(1.dp, borderCol, RoundedCornerShape(6.dp))
            .padding(horizontal = 9.dp, vertical = 7.dp)
    ) {
        Text(
            text = label.uppercase(),
            fontSize = 9.5.sp,
            fontWeight = FontWeight.Bold,
            color = labelCol,
            letterSpacing = 0.5.sp
        )
        Spacer(modifier = Modifier.height(3.dp))
        Text(
            text = value,
            fontSize = 13.sp,
            fontWeight = FontWeight.SemiBold,
            color = valCol
        )
    }
}
