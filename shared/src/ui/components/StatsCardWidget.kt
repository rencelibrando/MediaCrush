package org.example.project.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.example.project.models.CompressionTask
import org.example.project.models.SessionStats
import org.example.project.theme.AppColors

@Composable
fun StatsCardWidget(
    stats: SessionStats,
    overallProgress: Float,
    statusText: String,
    modifier: Modifier = Modifier,
    isDark: Boolean = true
) {
    val bg = if (isDark) AppColors.DarkCard else AppColors.LightCard
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder
    val textPrimary = if (isDark) AppColors.DarkTextPrimary else AppColors.LightTextPrimary
    val textSecondary = if (isDark) AppColors.DarkTextSecondary else AppColors.LightTextSecondary

    val savedStr = "${CompressionTask.formatSize(stats.savedBytesSum)} (${(stats.savedPctOverall * 10).toLong() / 10.0}%)"
    val processedStr = "${stats.processedFiles} / ${stats.totalFiles}"

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .background(bg)
            .border(1.dp, borderCol, RoundedCornerShape(8.dp))
            .padding(12.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "STATISTICS",
                fontSize = 10.5.sp,
                fontWeight = FontWeight.Bold,
                color = textSecondary,
                letterSpacing = 0.5.sp
            )
            Text(
                text = "${(overallProgress * 10).toLong() / 10.0}%",
                fontSize = 11.5.sp,
                fontWeight = FontWeight.Bold,
                color = AppColors.SupabaseGreen
            )
        }

        Spacer(modifier = Modifier.height(6.dp))

        LinearProgressIndicator(
            progress = { overallProgress / 100f },
            modifier = Modifier
                .fillMaxWidth()
                .height(3.dp)
                .clip(RoundedCornerShape(1.5.dp)),
            color = AppColors.SupabaseGreen,
            trackColor = if (isDark) Color(0xFF2E2E2E) else Color(0xFFE4E4E7)
        )

        Spacer(modifier = Modifier.height(10.dp))

        // 2x2 Grid
        Row(modifier = Modifier.fillMaxWidth()) {
            MetricCell(
                label = "Saved",
                value = savedStr,
                modifier = Modifier.weight(1f),
                isDark = isDark
            )
            Spacer(modifier = Modifier.width(8.dp))
            MetricCell(
                label = "Processed",
                value = processedStr,
                modifier = Modifier.weight(1f),
                isDark = isDark
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        Row(modifier = Modifier.fillMaxWidth()) {
            MetricCell(
                label = "Working",
                value = "${stats.workingFiles} active",
                modifier = Modifier.weight(1f),
                isDark = isDark
            )
            Spacer(modifier = Modifier.width(8.dp))
            MetricCell(
                label = "Errors",
                value = "${stats.errorFiles}",
                modifier = Modifier.weight(1f),
                isDark = isDark
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        HorizontalDivider(color = borderCol, thickness = 1.dp)

        Spacer(modifier = Modifier.height(6.dp))

        Text(
            text = statusText,
            fontSize = 11.sp,
            color = textSecondary,
            maxLines = 1
        )
    }
}
