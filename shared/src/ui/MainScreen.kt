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
import kotlinx.coroutines.launch
import org.example.project.engine.CompressionEngine
import org.example.project.models.AppSettings
import org.example.project.models.MediaType
import org.example.project.platform.PlatformBridge
import org.example.project.theme.AppColors
import org.example.project.theme.AppIcons
import org.example.project.theme.MediaCrushTheme
import org.example.project.ui.components.*
import org.example.project.ui.dialogs.DiagnosticsDialog
import org.example.project.ui.dialogs.SettingsDialog

@Composable
fun MainScreen(
    engine: CompressionEngine = remember { CompressionEngine() }
) {
    val scope = rememberCoroutineScope()

    val tasks by engine.tasks.collectAsState()
    val logs by engine.logs.collectAsState()
    val sessionStats by engine.sessionStats.collectAsState()
    val perfStats by engine.perfStats.collectAsState()
    val statusMessage by engine.statusMessage.collectAsState()
    val overallProgress by engine.overallProgress.collectAsState()
    val isRunning by engine.isRunning.collectAsState()
    val isPaused by engine.isPaused.collectAsState()
    val hwInfo by engine.hardwareInfo.collectAsState()
    val settings by engine.settings.collectAsState()

    var isDarkTheme by remember { mutableStateOf(settings.ui.theme == "dark") }
    LaunchedEffect(settings.ui.theme) {
        isDarkTheme = (settings.ui.theme == "dark")
    }

    var selectedTab by remember { mutableStateOf(0) }
    var unreadLogs by remember { mutableStateOf(false) }
    var lastLogCount by remember { mutableStateOf(0) }

    LaunchedEffect(logs.size) {
        if (selectedTab != 1 && logs.size > lastLogCount) {
            unreadLogs = true
        }
        lastLogCount = logs.size
    }

    var showSettingsDialog by remember { mutableStateOf(false) }
    var showDiagnosticsDialog by remember { mutableStateOf(false) }

    val bg = if (isDarkTheme) AppColors.DarkBackground else AppColors.LightBackground
    val surface = if (isDarkTheme) AppColors.DarkSurface else AppColors.LightSurface
    val cardBg = if (isDarkTheme) AppColors.DarkCard else AppColors.LightCard
    val borderCol = if (isDarkTheme) AppColors.DarkBorder else AppColors.LightBorder
    val textPrimary = if (isDarkTheme) AppColors.DarkTextPrimary else AppColors.LightTextPrimary
    val textSecondary = if (isDarkTheme) AppColors.DarkTextSecondary else AppColors.LightTextSecondary

    fun pickAndAddFiles() {
        scope.launch {
            val exts = (MediaType.IMAGE_EXTS + MediaType.VIDEO_EXTS).map { it.removePrefix(".") }
            val picked = PlatformBridge.pickFiles("Select media files", exts)
            if (picked.isNotEmpty()) {
                engine.addTasks(picked)
            }
        }
    }

    fun pickAndAddFolder() {
        scope.launch {
            val folder = PlatformBridge.pickFolder("Select media folder")
            if (folder != null) {
                engine.log("Scanning folder: $folder...")
                val mediaExts = MediaType.IMAGE_EXTS + MediaType.VIDEO_EXTS
                val scanned = PlatformBridge.scanFolder(folder, mediaExts)
                if (scanned.isNotEmpty()) {
                    engine.addTasks(scanned)
                } else {
                    engine.log("No supported media files found in $folder")
                }
            }
        }
    }

    MediaCrushTheme(isDark = isDarkTheme) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = bg
        ) {
            Column(modifier = Modifier.fillMaxSize()) {
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
                            onClick = { showDiagnosticsDialog = true },
                            tooltip = "Diagnostics",
                            isDark = isDarkTheme
                        )

                        Spacer(modifier = Modifier.width(6.dp))

                        // Settings Button
                        SupabaseIconButton(
                            icon = AppIcons.Settings,
                            onClick = { showSettingsDialog = true },
                            tooltip = "Settings",
                            isDark = isDarkTheme
                        )

                        Spacer(modifier = Modifier.width(6.dp))

                        // Theme Toggle Button
                        SupabaseIconButton(
                            icon = if (isDarkTheme) AppIcons.Sun else AppIcons.Moon,
                            onClick = {
                                val nextTheme = if (isDarkTheme) "light" else "dark"
                                isDarkTheme = (nextTheme == "dark")
                                engine.updateSettings(
                                    settings.copy(ui = settings.ui.copy(theme = nextTheme))
                                )
                            },
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
                            onAddFiles = { pickAndAddFiles() },
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
                                    onClick = { pickAndAddFiles() },
                                    isDark = isDarkTheme,
                                    modifier = Modifier.fillMaxWidth()
                                )
                            }

                            Box(modifier = Modifier.weight(1f)) {
                                SupabaseSecondaryButton(
                                    text = "Add Folder",
                                    icon = AppIcons.Folder,
                                    onClick = { pickAndAddFolder() },
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
                            // Header: Tab switches + Queue count + Clear
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                SecondaryTabRow(
                                    selectedTabIndex = selectedTab,
                                    modifier = Modifier.width(220.dp),
                                    containerColor = Color.Transparent,
                                    contentColor = AppColors.SupabaseGreen,
                                    divider = {}
                                ) {
                                    Tab(
                                        selected = selectedTab == 0,
                                        onClick = { selectedTab = 0 },
                                        text = { Text("Queue", fontSize = 12.sp, fontWeight = FontWeight.SemiBold) }
                                    )
                                    Tab(
                                        selected = selectedTab == 1,
                                        onClick = {
                                            selectedTab = 1
                                            unreadLogs = false
                                        },
                                        text = {
                                            Row(verticalAlignment = Alignment.CenterVertically) {
                                                Text("Logs", fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                                                if (unreadLogs) {
                                                    Spacer(modifier = Modifier.width(5.dp))
                                                    Box(
                                                        modifier = Modifier
                                                            .size(6.dp)
                                                            .clip(CircleShape)
                                                            .background(AppColors.SupabaseGreen)
                                                    )
                                                }
                                            }
                                        }
                                    )
                                }

                                Spacer(modifier = Modifier.weight(1f))

                                Text(
                                    text = "${tasks.size} files",
                                    fontSize = 12.sp,
                                    color = textSecondary
                                )

                                Spacer(modifier = Modifier.width(10.dp))

                                SupabaseDangerButton(
                                    text = "Clear Queue",
                                    icon = AppIcons.Trash,
                                    onClick = { engine.clearQueue() },
                                    enabled = tasks.isNotEmpty(),
                                    isDark = isDarkTheme
                                )
                            }

                            Spacer(modifier = Modifier.height(10.dp))
                            HorizontalDivider(color = borderCol, thickness = 1.dp)
                            Spacer(modifier = Modifier.height(10.dp))

                            // Tab view content
                            if (selectedTab == 0) {
                                if (tasks.isEmpty()) {
                                    Box(
                                        modifier = Modifier.fillMaxSize(),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                            Box(
                                                modifier = Modifier
                                                    .size(56.dp)
                                                    .clip(RoundedCornerShape(12.dp))
                                                    .background(if (isDarkTheme) Color(0xFF1E1E1E) else Color(0xFFF4F4F5))
                                                    .border(1.dp, borderCol, RoundedCornerShape(12.dp)),
                                                contentAlignment = Alignment.Center
                                            ) {
                                                Icon(
                                                    imageVector = AppIcons.Folder,
                                                    contentDescription = null,
                                                    modifier = Modifier.size(28.dp),
                                                    tint = AppColors.SupabaseGreen
                                                )
                                            }
                                            Spacer(modifier = Modifier.height(12.dp))
                                            Text(
                                                "Queue is empty",
                                                fontSize = 14.sp,
                                                fontWeight = FontWeight.SemiBold,
                                                color = textPrimary
                                            )
                                            Spacer(modifier = Modifier.height(4.dp))
                                            Text(
                                                "Drag and drop media files or click 'Add Files' to get started",
                                                fontSize = 12.sp,
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
                    modifier = Modifier.fillMaxWidth().height(34.dp)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(horizontal = 14.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = statusMessage,
                            fontSize = 11.sp,
                            color = textSecondary,
                            maxLines = 1,
                            modifier = Modifier.weight(1f)
                        )

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

            // MODALS
            if (showSettingsDialog) {
                SettingsDialog(
                    initialSettings = settings,
                    hwInfo = hwInfo,
                    onSave = { updated ->
                        engine.updateSettings(updated)
                    },
                    onDismiss = { showSettingsDialog = false },
                    onReprobeHw = { engine.detectHardwareAsync(force = true) },
                    isDark = isDarkTheme
                )
            }

            if (showDiagnosticsDialog) {
                DiagnosticsDialog(
                    onDismiss = { showDiagnosticsDialog = false },
                    isDark = isDarkTheme
                )
            }
        }
    }
}
