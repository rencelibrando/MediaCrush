package org.example.project.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.example.project.theme.AppColors
import org.example.project.theme.AppIcons

@Composable
fun DropZoneWidget(
    onAddFiles: () -> Unit,
    modifier: Modifier = Modifier,
    isDark: Boolean = true
) {
    val bg = if (isDark) AppColors.DarkCard else AppColors.LightCard
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder
    val textPrimary = if (isDark) AppColors.DarkTextPrimary else AppColors.LightTextPrimary
    val textSecondary = if (isDark) AppColors.DarkTextSecondary else AppColors.LightTextSecondary

    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(110.dp)
            .clip(RoundedCornerShape(8.dp))
            .background(bg)
            .border(1.dp, borderCol, RoundedCornerShape(8.dp))
            .clickable { onAddFiles() }
            .padding(12.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Box(
                modifier = Modifier
                    .size(36.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(if (isDark) Color(0x1F3ECF8E) else Color(0x153ECF8E)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = AppIcons.Folder,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp),
                    tint = AppColors.SupabaseGreen
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Drop media files here",
                fontSize = 12.5.sp,
                fontWeight = FontWeight.Medium,
                color = textPrimary,
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = "or click to browse",
                fontSize = 11.sp,
                color = textSecondary,
                textAlign = TextAlign.Center
            )
        }
    }
}
