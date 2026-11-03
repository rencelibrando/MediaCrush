package org.example.project.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.example.project.engine.CompressionEngine
import org.example.project.models.AppSettings
import org.example.project.models.CompressionTask
import org.example.project.models.HardwareInfo
import org.example.project.models.PerfStats
import org.example.project.models.SessionStats
import org.example.project.theme.AppColors
import org.example.project.theme.AppIcons
import org.example.project.ui.components.*

@Composable
fun DesktopMainLayout(
    engine: CompressionEngine,
    tasks: List<CompressionTask>,
    logs: List<String>,
    sessionStats: SessionStats,
    perfStats: PerfStats,
    hwInfo: HardwareInfo,
    settings: AppSettings,
    statusMessage: String,
    overallProgress: Float,
    isRunning: Boolean,
    isPaused: Boolean,
    isDarkTheme: Boolean,
    selectedTab: Int,
    onSelectTab: (Int) -> Unit,
    unreadLogs: Boolean,
    onToggleTheme: () -> Unit,
    onOpenSettings: () -> Unit,
    onOpenDiagnostics: () -> Unit,
    onPickFiles: () -> Unit,
    onPickFolder: () -> Unit
) {
    val surface = if (isDarkTheme) AppColors.DarkSurface else AppColors.LightSurface
    val cardBg = if (isDarkTheme) AppColors.DarkCard else AppColors.LightCard
    val borderCol = if (isDarkTheme) AppColors.DarkBorder else AppColors.LightBorder
    val textPrimary = if (isDarkTheme) AppColors.DarkTextPrimary else AppColors.LightTextPrimary
    val textSecondary = if (isDarkTheme) AppColors.DarkTextSecondary else AppColors.LightTextSecondary

    Column(modifier = Modifier.fillMaxSize().windowInsetsPadding(WindowInsets.safeDrawing)) {
        // TOP TOOLBAR
        Surface(
            color = surface,
            modifier = Modifier.fillMaxWidth().height(52.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 14.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // MediaCrush Brand Logo & Title
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(28.dp)
                            .clip(RoundedCornerShape(7.dp))
                            .background(Color(0x1F3ECF8E))
                            .border(1.dp, Color(0x333ECF8E), RoundedCornerShape(7.dp)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = AppIcons.MediaCrushLogo,
                            contentDescription = "MediaCrush Logo",
                            modifier = Modifier.size(16.dp),
                            tint = AppColors.SupabaseGreen
                        )
                    }
                    Spacer(modifier = Modifier.width(9.dp))
                    Text(
                        text = "MediaCrush",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = textPrimary
                    )
                }

                Spacer(modifier = Modifier.width(16.dp))
                Box(modifier = Modifier.width(1.dp).height(24.dp).background(borderCol))
                Spacer(modifier = Modifier.width(14.dp))

                // Quick Preset Dropdown
                Text("Preset:", fontSize = 12.sp, color = textSecondary)
                Spacer(modifier = Modifier.width(6.dp))

                var presetExpanded by remember { mutableStateOf(false) }
                Box {
                    SupabaseSecondaryButton(
                        text = settings.image.preset.replaceFirstChar { it.uppercase() },
                        onClick = { presetExpanded = true },
                        isDark = isDarkTheme
                    )
                    DropdownMenu(
                        expanded = presetExpanded,
                        onDismissRequest = { presetExpanded = false }
                    ) {
                        listOf("lossless", "high", "balanced", "small", "tiny").forEach { p ->
                            DropdownMenuItem(
                                text = { Text(p, fontSize = 12.sp) },
                                onClick = {
                                    presetExpanded = false
                                    val q = AppSettings.defaultQualityForPreset(p)
                                    engine.updateSettings(
                                        settings.copy(image = settings.image.copy(preset = p, quality = q))
                                    )
                                }
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.width(14.dp))
                Box(modifier = Modifier.width(1.dp).height(24.dp).background(borderCol))
                Spacer(modifier = Modifier.width(14.dp))

                // Actions: Start / Pause / Cancel
                SupabasePrimaryButton(
                    text = "Start",
                    icon = AppIcons.Play,
                    onClick = { engine.start() },
                    enabled = !isRunning && tasks.isNotEmpty(),
                    isDark = isDarkTheme
                )

                Spacer(modifier = Modifier.width(8.dp))

                SupabaseSecondaryButton(
                    text = if (isPaused) "Resume" else "Pause",
                    icon = if (isPaused) AppIcons.Play else AppIcons.Pause,
                    onClick = {
                        if (isPaused) engine.resume() else engine.pause()
                    },
                    enabled = isRunning,
                    isDark = isDarkTheme
                )

                Spacer(modifier = Modifier.width(8.dp))

                SupabaseDangerButton(
                    text = "Cancel",
                    icon = AppIcons.Stop,
                    onClick = { engine.cancel() },
                    enabled = isRunning,
                    isDark = isDarkTheme
                )

                Spacer(modifier = Modifier.weight(1f))

                // Hardware status badge
                Row(
                    modifier = Modifier
                        .clip(RoundedCornerShape(6.dp))
                        .background(cardBg)
                        .border(1.dp, borderCol, RoundedCornerShape(6.dp))
                        .padding(horizontal = 10.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = AppIcons.Cpu,
                        contentDescription = null,
                        modifier = Modifier.size(13.dp),
                        tint = AppColors.SupabaseGreen
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = hwInfo.hwSummary,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = textPrimary
                    )
                }

                Spacer(modifier = Modifier.width(10.dp))

                // Diagnostics Button
                SupabaseIconButton(
                    icon = AppIcons.Diagnostics,
                    onClick = onOpenDiagnostics,
                    tooltip = "Diagnostics",
                    isDark = isDarkTheme
                )

                Spacer(modifier = Modifier.width(6.dp))

                // Settings Button
                SupabaseIconButton(
                    icon = AppIcons.Settings,
                    onClick = onOpenSettings,
                    tooltip = "Settings",
                    isDark = isDarkTheme
                )

                Spacer(modifier = Modifier.width(6.dp))

                // Theme Toggle Button
                SupabaseIconButton(
                    icon = if (isDarkTheme) AppIcons.Sun else AppIcons.Moon,
                    onClick = onToggleTheme,
                    tooltip = if (isDarkTheme) "Switch to Light Mode" else "Switch to Dark Mode",
                    isDark = isDarkTheme
                )
            }
        }

        HorizontalDivider(color = borderCol, thickness = 1.dp)

        // MAIN CONTENT AREA (Sidebar + Right Content)
        Row(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(12.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // LEFT SIDEBAR
            Column(
                modifier = Modifier
                    .width(300.dp)
                    .fillMaxHeight()
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                DropZoneWidget(
                    onAddFiles = onPickFiles,
                    isDark = isDarkTheme
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Box(modifier = Modifier.weight(1f)) {
                        SupabaseSecondaryButton(
                            text = "Add Files",
                            icon = AppIcons.Plus,
                            onClick = onPickFiles,
                            isDark = isDarkTheme,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }

                    Box(modifier = Modifier.weight(1f)) {
                        SupabaseSecondaryButton(
                            text = "Add Folder",
                            icon = AppIcons.Folder,
                            onClick = onPickFolder,
                            isDark = isDarkTheme,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }

                StatsCardWidget(
                    stats = sessionStats,
                    overallProgress = overallProgress,
                    statusText = statusMessage,
                    isDark = isDarkTheme
                )

                PerfCardWidget(
                    perf = perfStats,
                    hwInfo = hwInfo,
                    isDark = isDarkTheme
                )
            }

            // RIGHT PANEL (Queue and Logs tabs)
            Surface(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight()
                    .clip(RoundedCornerShape(8.dp))
                    .border(1.dp, borderCol, RoundedCornerShape(8.dp)),
                color = surface
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(12.dp)
                ) {
                    // TAB SELECTOR
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        TabRow(
                            selectedTabIndex = selectedTab,
                            containerColor = Color.Transparent,
                            contentColor = AppColors.SupabaseGreen,
                            divider = {},
                            modifier = Modifier.width(220.dp)
                        ) {
                            Tab(
                                selected = selectedTab == 0,
                                onClick = { onSelectTab(0) },
                                text = {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Text(
                                            text = "Queue",
                                            fontSize = 12.sp,
                                            fontWeight = if (selectedTab == 0) FontWeight.Bold else FontWeight.Normal,
                                            color = if (selectedTab == 0) AppColors.SupabaseGreen else textSecondary
                                        )
                                        if (tasks.isNotEmpty()) {
                                            Spacer(modifier = Modifier.width(6.dp))
                                            Box(
                                                modifier = Modifier
                                                    .clip(RoundedCornerShape(10.dp))
                                                    .background(if (selectedTab == 0) AppColors.SupabaseGreen else borderCol)
                                                    .padding(horizontal = 5.dp, vertical = 1.dp)
                                            ) {
                                                Text(
                                                    text = "${tasks.size}",
                                                    fontSize = 9.5.sp,
                                                    fontWeight = FontWeight.Bold,
                                                    color = if (selectedTab == 0) Color.Black else textPrimary
                                                )
                                            }
                                        }
                                    }
                                }
                            )

                            Tab(
                                selected = selectedTab == 1,
                                onClick = { onSelectTab(1) },
                                text = {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Text(
                                            text = "Logs",
                                            fontSize = 12.sp,
                                            fontWeight = if (selectedTab == 1) FontWeight.Bold else FontWeight.Normal,
                                            color = if (selectedTab == 1) AppColors.SupabaseGreen else textSecondary
                                        )
                                        if (unreadLogs) {
                                            Spacer(modifier = Modifier.width(5.dp))
                                            Box(
                                                modifier = Modifier
                                                    .size(6.dp)
                                                    .clip(CircleShape)
                                                    .background(AppColors.StatusRunning)
                                            )
                                        }
                                    }
                                }
                            )
                        }

                        Spacer(modifier = Modifier.weight(1f))

                        if (selectedTab == 0 && tasks.isNotEmpty()) {
                            SupabaseSecondaryButton(
                                text = "Clear Queue",
                                icon = AppIcons.Trash,
                                onClick = { engine.clearQueue() },
                                isDark = isDarkTheme
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(10.dp))
                    HorizontalDivider(color = borderCol, thickness = 1.dp)
                    Spacer(modifier = Modifier.height(10.dp))

                    // TAB CONTENT
                    if (selectedTab == 0) {
                        if (tasks.isEmpty()) {
                            Box(
                                modifier = Modifier.fillMaxSize(),
                                contentAlignment = Alignment.Center
                            ) {
                                Column(
                                    horizontalAlignment = Alignment.CenterHorizontally,
                                    verticalArrangement = Arrangement.Center
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .size(48.dp)
                                            .clip(RoundedCornerShape(10.dp))
                                            .background(if (isDarkTheme) Color(0x1F3ECF8E) else Color(0x153ECF8E)),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Icon(
                                            imageVector = AppIcons.Folder,
                                            contentDescription = null,
                                            modifier = Modifier.size(24.dp),
                                            tint = AppColors.SupabaseGreen
                                        )
                                    }
                                    Spacer(modifier = Modifier.height(12.dp))
                                    Text(
                                        text = "Queue is empty",
                                        fontSize = 13.5.sp,
                                        fontWeight = FontWeight.SemiBold,
                                        color = textPrimary
                                    )
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(
                                        text = "Drag and drop media files or click 'Add Files' to get started",
                                        fontSize = 11.5.sp,
                                        color = textSecondary
                                    )
                                }
                            }
                        } else {
                            LazyColumn(
                                modifier = Modifier.fillMaxSize(),
                                verticalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                items(tasks, key = { it.id }) { task ->
                                    TaskCardWidget(
                                        task = task,
                                        onCancelTask = { engine.cancelTask(it) },
                                        isDark = isDarkTheme
                                    )
                                }
                            }
                        }
                    } else {
                        LogsWidget(
                            logs = logs,
                            onClearLogs = { engine.clearLogs() },
                            isDark = isDarkTheme
                        )
                    }
                }
            }
        }

        HorizontalDivider(color = borderCol, thickness = 1.dp)

        // BOTTOM STATUS BAR
        Surface(
            color = surface,
            modifier = Modifier.fillMaxWidth().height(32.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 14.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Status dot indicator
                val statusDotCol = if (isRunning) {
                    if (isPaused) AppColors.StatusWarning else AppColors.SupabaseGreen
                } else {
                    Color(0xFF666666)
                }

                Box(
                    modifier = Modifier
                        .size(7.dp)
                        .clip(CircleShape)
                        .background(statusDotCol)
                )

                Spacer(modifier = Modifier.width(8.dp))

                Text(
                    text = statusMessage,
                    fontSize = 11.sp,
                    color = textSecondary,
                    maxLines = 1,
                    modifier = Modifier.weight(1f)
                )

                if (isRunning) {
                    Spacer(modifier = Modifier.width(14.dp))

                    LinearProgressIndicator(
                        progress = { overallProgress / 100f },
                        modifier = Modifier
                            .width(200.dp)
                            .height(6.dp)
                            .clip(RoundedCornerShape(3.dp)),
                        color = AppColors.SupabaseGreen,
                        trackColor = if (isDarkTheme) Color(0xFF262626) else Color(0xFFE5E7EB)
                    )

                    Spacer(modifier = Modifier.width(8.dp))

                    Text(
                        text = "${(overallProgress * 10).toLong() / 10.0}%",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = textPrimary
                    )
                }
            }
        }
    }
}
