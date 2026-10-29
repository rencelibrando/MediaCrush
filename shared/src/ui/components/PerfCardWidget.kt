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
import org.example.project.models.HardwareInfo
import org.example.project.models.PerfStats
import org.example.project.theme.AppColors

@Composable
fun PerfCardWidget(
    perf: PerfStats,
    hwInfo: HardwareInfo,
    modifier: Modifier = Modifier,
    isDark: Boolean = true
) {
    val bg = if (isDark) AppColors.DarkCard else AppColors.LightCard
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder
    val textPrimary = if (isDark) AppColors.DarkTextPrimary else AppColors.LightTextPrimary
    val textSecondary = if (isDark) AppColors.DarkTextSecondary else AppColors.LightTextSecondary
    val trackCol = if (isDark) Color(0xFF2E2E2E) else Color(0xFFE4E4E7)

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
                text = "PERFORMANCE",
                fontSize = 10.5.sp,
                fontWeight = FontWeight.Bold,
                color = textSecondary,
                letterSpacing = 0.5.sp
            )
            Text(
                text = "${hwInfo.cpuThreads} Threads",
                fontSize = 11.sp,
                color = textSecondary
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        // CPU Metric
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(text = "CPU", fontSize = 11.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
            Text(text = "${perf.cpuPercent.toInt()}%", fontSize = 11.sp, color = textSecondary)
        }
        Spacer(modifier = Modifier.height(3.dp))
        LinearProgressIndicator(
            progress = { minOf(1f, maxOf(0f, perf.cpuPercent / 100f)) },
            modifier = Modifier
                .fillMaxWidth()
                .height(3.dp)
                .clip(RoundedCornerShape(1.5.dp)),
            color = AppColors.SupabaseGreen,
            trackColor = trackCol
        )

        Spacer(modifier = Modifier.height(8.dp))

        // RAM Metric
        val ramUsedStr = "${(perf.ramUsedGb * 10).toLong() / 10.0} GB"
        val ramTotalStr = "${(perf.ramTotalGb * 10).toLong() / 10.0} GB"
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(text = "RAM", fontSize = 11.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
            Text(text = "$ramUsedStr / $ramTotalStr", fontSize = 11.sp, color = textSecondary)
        }
        Spacer(modifier = Modifier.height(3.dp))
        val ramFraction = if (perf.ramTotalGb > 0) (perf.ramUsedGb / perf.ramTotalGb).toFloat() else 0f
        LinearProgressIndicator(
            progress = { minOf(1f, maxOf(0f, ramFraction)) },
            modifier = Modifier
                .fillMaxWidth()
                .height(3.dp)
                .clip(RoundedCornerShape(1.5.dp)),
            color = AppColors.StatusRunning,
            trackColor = trackCol
        )

        Spacer(modifier = Modifier.height(8.dp))

        // GPU / HW Acceleration Status
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(text = "GPU Acceleration", fontSize = 11.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
            val gpuText = if (perf.gpuPercent >= 0) "${perf.gpuPercent.toInt()}%" else if (hwInfo.hasAnyGpu) "Active" else "N/A"
            Text(text = gpuText, fontSize = 11.sp, color = if (hwInfo.hasAnyGpu) AppColors.SupabaseGreen else textSecondary)
        }
        Spacer(modifier = Modifier.height(3.dp))
        if (perf.gpuPercent >= 0) {
            LinearProgressIndicator(
                progress = { minOf(1f, maxOf(0f, perf.gpuPercent / 100f)) },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(3.dp)
                    .clip(RoundedCornerShape(1.5.dp)),
                color = AppColors.SupabaseGreen,
                trackColor = trackCol
            )
            Spacer(modifier = Modifier.height(8.dp))
        }

        HorizontalDivider(color = borderCol, thickness = 1.dp)
        Spacer(modifier = Modifier.height(6.dp))

        // Workers summary
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = "GPU Streams: ${perf.activeGpuWorkers}",
                fontSize = 11.sp,
                color = if (perf.activeGpuWorkers > 0) AppColors.SupabaseGreen else textSecondary
            )
            Text(
                text = "CPU Workers: ${perf.activeCpuWorkers}",
                fontSize = 11.sp,
                color = if (perf.activeCpuWorkers > 0) AppColors.SupabaseGreen else textSecondary
            )
        }
    }
}
