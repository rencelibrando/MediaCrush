package org.example.project.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.example.project.models.CompressionTask
import org.example.project.models.MediaType
import org.example.project.models.TaskStatus
import org.example.project.theme.AppColors
import org.example.project.theme.AppIcons

@Composable
fun TaskCardWidget(
    task: CompressionTask,
    onCancelTask: (String) -> Unit,
    modifier: Modifier = Modifier,
    isDark: Boolean = true
) {
    val bg = if (isDark) AppColors.DarkCard else AppColors.LightCard
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder
    val textPrimary = if (isDark) AppColors.DarkTextPrimary else AppColors.LightTextPrimary
    val textSecondary = if (isDark) AppColors.DarkTextSecondary else AppColors.LightTextSecondary

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .background(bg)
            .border(1.dp, borderCol, RoundedCornerShape(8.dp))
            .padding(10.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Standard Vector Icon
            val (iconVector, iconTint) = when (task.mediaType) {
                MediaType.VIDEO -> Pair(AppIcons.Video, AppColors.StatusRunning)
                MediaType.IMAGE -> Pair(AppIcons.Image, AppColors.SupabaseGreen)
                MediaType.UNKNOWN -> Pair(AppIcons.File, textSecondary)
            }

            Box(
                modifier = Modifier
                    .size(28.dp)
                    .clip(RoundedCornerShape(6.dp))
                    .background(if (isDark) Color(0xFF171717) else Color(0xFFEAEAEA)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = iconVector,
                    contentDescription = null,
                    modifier = Modifier.size(15.dp),
                    tint = iconTint
                )
            }

            Spacer(modifier = Modifier.width(10.dp))

            // File Name & Details
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = task.fileName,
                    fontSize = 12.5.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = textPrimary,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )

                Spacer(modifier = Modifier.height(2.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    val origStr = CompressionTask.formatSize(task.origSize)
                    if (task.status == TaskStatus.DONE) {
                        val newStr = CompressionTask.formatSize(task.newSize)
                        Text(
                            text = "$origStr → $newStr",
                            fontSize = 11.sp,
                            color = textSecondary
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        if (task.savedPct > 0) {
                            Text(
                                text = "(${(task.savedPct * 10).toLong() / 10.0}% saved)",
                                fontSize = 11.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = AppColors.SupabaseGreen
                            )
                        }
                    } else {
                        Text(
                            text = origStr,
                            fontSize = 11.sp,
                            color = textSecondary
                        )
                    }

                    if (task.encoderUsed.isNotBlank()) {
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "• ${task.encoderUsed}",
                            fontSize = 10.sp,
                            color = textSecondary,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.width(8.dp))

            // Status Badge
            StatusBadge(status = task.status.label)

            // Cancel action
            if (task.status == TaskStatus.QUEUED || task.status == TaskStatus.RUNNING) {
                Spacer(modifier = Modifier.width(6.dp))
                IconButton(
                    onClick = { onCancelTask(task.id) },
                    modifier = Modifier.size(24.dp)
                ) {
                    Icon(
                        imageVector = AppIcons.Close,
                        contentDescription = "Cancel task",
                        modifier = Modifier.size(12.dp),
                        tint = textSecondary
                    )
                }
            }
        }

        // Progress bar if running
        if (task.status == TaskStatus.RUNNING) {
            Spacer(modifier = Modifier.height(6.dp))
            LinearProgressIndicator(
                progress = { task.progress / 100f },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(2.5.dp)
                    .clip(RoundedCornerShape(1.25.dp)),
                color = AppColors.SupabaseGreen,
                trackColor = if (isDark) Color(0xFF2E2E2E) else Color(0xFFE4E4E7)
            )
        }

        // Error message if error
        if (task.status == TaskStatus.ERROR && task.errorMsg.isNotBlank()) {
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = task.errorMsg,
                fontSize = 11.sp,
                color = AppColors.StatusError,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}
