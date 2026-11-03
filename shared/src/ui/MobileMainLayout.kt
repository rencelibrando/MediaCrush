package org.example.project.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.example.project.engine.CompressionEngine
import org.example.project.models.AppSettings
import org.example.project.models.CompressionTask
import org.example.project.models.HardwareInfo
import org.example.project.models.PerfStats
import org.example.project.models.SessionStats
import org.example.project.models.TaskStatus
import org.example.project.theme.AppColors
import org.example.project.theme.AppIcons
import org.example.project.ui.components.*

@Composable
fun MobileMainLayout(
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
    isDark: Boolean,
    onToggleTheme: () -> Unit,
    onOpenSettings: () -> Unit,
    onOpenDiagnostics: () -> Unit,
    onPickFiles: () -> Unit,
    onPickFolder: () -> Unit
) {
    var selectedTab by remember { mutableStateOf(0) }
    var unreadLogs by remember { mutableStateOf(false) }
    var lastLogCount by remember { mutableStateOf(0) }

    LaunchedEffect(logs.size) {
        if (selectedTab != 3 && logs.size > lastLogCount) {
            unreadLogs = true
        }
        lastLogCount = logs.size
    }

    LaunchedEffect(selectedTab) {
        if (selectedTab == 3) {
            unreadLogs = false
        }
    }

    val bg = if (isDark) AppColors.DarkBackground else AppColors.LightBackground
    val surface = if (isDark) AppColors.DarkSurface else AppColors.LightSurface
    val cardBg = if (isDark) AppColors.DarkCard else AppColors.LightCard
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder
    val textPrimary = if (isDark) AppColors.DarkTextPrimary else AppColors.LightTextPrimary
    val textSecondary = if (isDark) AppColors.DarkTextSecondary else AppColors.LightTextSecondary

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        containerColor = bg,
        contentWindowInsets = WindowInsets.safeDrawing,
        topBar = {
            MobileTopAppBar(
                hwInfo = hwInfo,
                isDark = isDark,
                onToggleTheme = onToggleTheme,
                onOpenSettings = onOpenSettings,
                onOpenDiagnostics = onOpenDiagnostics
            )
        },
        bottomBar = {
            NavigationBar(
                containerColor = surface,
                contentColor = textPrimary,
                tonalElevation = 0.dp,
                modifier = Modifier
                    .fillMaxWidth()
                    .border(
                        width = 1.dp,
                        color = borderCol,
                        shape = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp)
                    )
            ) {
                NavigationBarItem(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    icon = {
                        Icon(
                            imageVector = AppIcons.Bolt,
                            contentDescription = "Compress",
                            modifier = Modifier.size(20.dp)
                        )
                    },
                    label = { Text("Compress", fontSize = 11.sp, fontWeight = FontWeight.Medium) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = AppColors.SupabaseGreen,
                        selectedTextColor = AppColors.SupabaseGreen,
                        indicatorColor = if (isDark) Color(0x243ECF8E) else Color(0x183ECF8E),
                        unselectedIconColor = textSecondary,
                        unselectedTextColor = textSecondary
                    )
                )

                NavigationBarItem(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    icon = {
                        BadgedBox(
                            badge = {
                                if (tasks.isNotEmpty()) {
                                    Badge(
                                        containerColor = AppColors.SupabaseGreen,
                                        contentColor = Color.Black
                                    ) {
                                        Text("${tasks.size}")
                                    }
                                }
                            }
                        ) {
                            Icon(
                                imageVector = AppIcons.Queue,
                                contentDescription = "Queue",
                                modifier = Modifier.size(20.dp)
                            )
                        }
                    },
                    label = { Text("Queue", fontSize = 11.sp, fontWeight = FontWeight.Medium) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = AppColors.SupabaseGreen,
                        selectedTextColor = AppColors.SupabaseGreen,
                        indicatorColor = if (isDark) Color(0x243ECF8E) else Color(0x183ECF8E),
                        unselectedIconColor = textSecondary,
                        unselectedTextColor = textSecondary
                    )
                )

                NavigationBarItem(
                    selected = selectedTab == 2,
                    onClick = { selectedTab = 2 },
                    icon = {
                        Icon(
                            imageVector = AppIcons.Dashboard,
                            contentDescription = "Dashboard",
                            modifier = Modifier.size(20.dp)
                        )
                    },
                    label = { Text("Dashboard", fontSize = 11.sp, fontWeight = FontWeight.Medium) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = AppColors.SupabaseGreen,
                        selectedTextColor = AppColors.SupabaseGreen,
                        indicatorColor = if (isDark) Color(0x243ECF8E) else Color(0x183ECF8E),
                        unselectedIconColor = textSecondary,
                        unselectedTextColor = textSecondary
                    )
                )

                NavigationBarItem(
                    selected = selectedTab == 3,
                    onClick = { selectedTab = 3 },
                    icon = {
                        BadgedBox(
                            badge = {
                                if (unreadLogs) {
                                    Badge(
                                        containerColor = AppColors.StatusRunning,
                                        modifier = Modifier.size(6.dp)
                                    )
                                }
                            }
                        ) {
                            Icon(
                                imageVector = AppIcons.Terminal,
                                contentDescription = "Logs",
                                modifier = Modifier.size(20.dp)
                            )
                        }
                    },
                    label = { Text("Logs", fontSize = 11.sp, fontWeight = FontWeight.Medium) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = AppColors.SupabaseGreen,
                        selectedTextColor = AppColors.SupabaseGreen,
                        indicatorColor = if (isDark) Color(0x243ECF8E) else Color(0x183ECF8E),
                        unselectedIconColor = textSecondary,
                        unselectedTextColor = textSecondary
                    )
                )
            }
        },
        floatingActionButton = {
            if (selectedTab == 0 || selectedTab == 1) {
                ExtendedFloatingActionButton(
                    text = { Text("Add Media", fontWeight = FontWeight.SemiBold, fontSize = 13.sp) },
                    icon = { Icon(AppIcons.Plus, contentDescription = null, modifier = Modifier.size(18.dp)) },
                    onClick = onPickFiles,
                    containerColor = AppColors.SupabaseGreen,
                    contentColor = Color.Black,
                    shape = RoundedCornerShape(14.dp),
                    elevation = FloatingActionButtonDefaults.elevation(defaultElevation = 3.dp)
                )
            }
        }
    ) { contentPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(contentPadding)
        ) {
            when (selectedTab) {
                0 -> MobileCompressScreen(
                    engine = engine,
                    tasks = tasks,
                    settings = settings,
                    isRunning = isRunning,
                    isPaused = isPaused,
                    hwInfo = hwInfo,
                    isDark = isDark,
                    onPickFiles = onPickFiles,
                    onPickFolder = onPickFolder,
                    onNavigateToQueue = { selectedTab = 1 }
                )
                1 -> MobileQueueScreen(
                    engine = engine,
                    tasks = tasks,
                    isRunning = isRunning,
                    isPaused = isPaused,
                    isDark = isDark,
                    onPickFiles = onPickFiles
                )
                2 -> MobileDashboardScreen(
                    sessionStats = sessionStats,
                    perfStats = perfStats,
                    hwInfo = hwInfo,
                    overallProgress = overallProgress,
                    statusMessage = statusMessage,
                    isDark = isDark
                )
                3 -> LogsWidget(
                    logs = logs,
                    onClearLogs = { engine.clearLogs() },
                    isDark = isDark,
                    modifier = Modifier.fillMaxSize().padding(12.dp)
                )
            }
        }
    }
}

@Composable
private fun MobileTopAppBar(
    hwInfo: HardwareInfo,
    isDark: Boolean,
    onToggleTheme: () -> Unit,
    onOpenSettings: () -> Unit,
    onOpenDiagnostics: () -> Unit
) {
    val surface = if (isDark) AppColors.DarkSurface else AppColors.LightSurface
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder
    val textPrimary = if (isDark) AppColors.DarkTextPrimary else AppColors.LightTextPrimary

    Surface(
        color = surface,
        modifier = Modifier.fillMaxWidth().height(56.dp)
    ) {
        Column {
            Row(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 14.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(30.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color(0x1F3ECF8E))
                        .border(1.dp, Color(0x333ECF8E), RoundedCornerShape(8.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = AppIcons.MediaCrushLogo,
                        contentDescription = "Logo",
                        modifier = Modifier.size(17.dp),
                        tint = AppColors.SupabaseGreen
                    )
                }

                Spacer(modifier = Modifier.width(10.dp))

                Text(
                    text = "MediaCrush",
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                    color = textPrimary
                )

                Spacer(modifier = Modifier.width(8.dp))

                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(6.dp))
                        .background(if (isDark) Color(0xFF242424) else Color(0xFFEAEAEA))
                        .padding(horizontal = 7.dp, vertical = 3.dp)
                ) {
                    Text(
                        text = if (hwInfo.hasAnyGpu) hwInfo.bestVideoEncoder.uppercase() else "CPU",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = AppColors.SupabaseGreen
                    )
                }

                Spacer(modifier = Modifier.weight(1f))

                SupabaseIconButton(
                    icon = if (isDark) AppIcons.Sun else AppIcons.Moon,
                    onClick = onToggleTheme,
                    tooltip = "Toggle theme",
                    isDark = isDark,
                    modifier = Modifier.size(36.dp)
                )

                Spacer(modifier = Modifier.width(6.dp))

                SupabaseIconButton(
                    icon = AppIcons.Diagnostics,
                    onClick = onOpenDiagnostics,
                    tooltip = "Diagnostics",
                    isDark = isDark,
                    modifier = Modifier.size(36.dp)
                )

                Spacer(modifier = Modifier.width(6.dp))

                SupabaseIconButton(
                    icon = AppIcons.Settings,
                    onClick = onOpenSettings,
                    tooltip = "Settings",
                    isDark = isDark,
                    modifier = Modifier.size(36.dp)
                )
            }
            HorizontalDivider(color = borderCol, thickness = 1.dp)
        }
    }
}

@Composable
private fun MobileCompressScreen(
    engine: CompressionEngine,
    tasks: List<CompressionTask>,
    settings: AppSettings,
    isRunning: Boolean,
    isPaused: Boolean,
    hwInfo: HardwareInfo,
    isDark: Boolean,
    onPickFiles: () -> Unit,
    onPickFolder: () -> Unit,
    onNavigateToQueue: () -> Unit
) {
    val cardBg = if (isDark) AppColors.DarkCard else AppColors.LightCard
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder
    val textPrimary = if (isDark) AppColors.DarkTextPrimary else AppColors.LightTextPrimary
    val textSecondary = if (isDark) AppColors.DarkTextSecondary else AppColors.LightTextSecondary

    val presets = listOf("lossless", "high", "balanced", "small", "tiny")
    val currentPreset = settings.image.preset.lowercase()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Hero Media Picker Card
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .background(cardBg)
                .border(1.dp, Color(0x4D3ECF8E), RoundedCornerShape(12.dp))
                .padding(18.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(Color(0x1F3ECF8E)),
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
                text = "Select Media to Compress",
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                color = textPrimary,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "Supports MP4, MKV, MOV, JPG, PNG, and WebP",
                fontSize = 12.sp,
                color = textSecondary,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                SupabasePrimaryButton(
                    text = "Pick Files",
                    icon = AppIcons.Plus,
                    onClick = onPickFiles,
                    isDark = isDark,
                    modifier = Modifier.weight(1f).height(44.dp)
                )

                SupabaseSecondaryButton(
                    text = "Scan Folder",
                    icon = AppIcons.Folder,
                    onClick = onPickFolder,
                    isDark = isDark,
                    modifier = Modifier.weight(1f).height(44.dp)
                )
            }
        }

        // Active Queue Quick Summary
        if (tasks.isNotEmpty()) {
            val queuedCount = tasks.count { it.status == TaskStatus.QUEUED }
            val doneCount = tasks.count { it.status == TaskStatus.DONE }
            val workingCount = tasks.count { it.status == TaskStatus.RUNNING }

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(10.dp))
                    .background(cardBg)
                    .border(1.dp, borderCol, RoundedCornerShape(10.dp))
                    .padding(14.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "QUEUE STATUS",
                        fontSize = 10.5.sp,
                        fontWeight = FontWeight.Bold,
                        color = textSecondary,
                        letterSpacing = 0.5.sp
                    )

                    Text(
                        text = "View all (${tasks.size})",
                        fontSize = 11.5.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = AppColors.SupabaseGreen,
                        modifier = Modifier.clickable { onNavigateToQueue() }
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "$workingCount running · $queuedCount pending · $doneCount finished",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium,
                    color = textPrimary
                )

                Spacer(modifier = Modifier.height(12.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    SupabasePrimaryButton(
                        text = "Start All",
                        icon = AppIcons.Play,
                        onClick = { engine.start() },
                        enabled = !isRunning && queuedCount > 0,
                        isDark = isDark,
                        modifier = Modifier.weight(1f).height(40.dp)
                    )

                    if (isRunning) {
                        SupabaseSecondaryButton(
                            text = if (isPaused) "Resume" else "Pause",
                            icon = if (isPaused) AppIcons.Play else AppIcons.Pause,
                            onClick = { if (isPaused) engine.resume() else engine.pause() },
                            isDark = isDark,
                            modifier = Modifier.weight(1f).height(40.dp)
                        )

                        SupabaseDangerButton(
                            text = "Cancel",
                            icon = AppIcons.Stop,
                            onClick = { engine.cancel() },
                            isDark = isDark,
                            modifier = Modifier.weight(1f).height(40.dp)
                        )
                    }
                }
            }
        }

        // Compression Preset Selector
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(10.dp))
                .background(cardBg)
                .border(1.dp, borderCol, RoundedCornerShape(10.dp))
                .padding(14.dp)
        ) {
            Text(
                text = "COMPRESSION PROFILE",
                fontSize = 10.5.sp,
                fontWeight = FontWeight.Bold,
                color = textSecondary,
                letterSpacing = 0.5.sp
            )

            Spacer(modifier = Modifier.height(10.dp))

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                presets.forEach { preset ->
                    val isSelected = (preset == currentPreset)
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(
                                if (isSelected) Color(0x1F3ECF8E)
                                else if (isDark) Color(0xFF262626) else Color(0xFFE5E7EB)
                            )
                            .border(
                                width = 1.dp,
                                color = if (isSelected) AppColors.SupabaseGreen else Color.Transparent,
                                shape = RoundedCornerShape(8.dp)
                            )
                            .clickable {
                                val q = AppSettings.defaultQualityForPreset(preset)
                                val vq = when (preset) {
                                    "lossless" -> 16
                                    "high" -> 22
                                    "balanced" -> 28
                                    "small" -> 34
                                    "tiny" -> 40
                                    else -> 28
                                }
                                engine.updateSettings(
                                    settings.copy(
                                        image = settings.image.copy(preset = preset, quality = q),
                                        video = settings.video.copy(quality = vq)
                                    )
                                )
                            }
                            .padding(horizontal = 14.dp, vertical = 9.dp)
                    ) {
                        Text(
                            text = preset.replaceFirstChar { it.uppercase() },
                            fontSize = 12.5.sp,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
                            color = if (isSelected) AppColors.SupabaseGreen else textPrimary
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            val presetDescription = when (currentPreset) {
                "lossless" -> "Mathematically lossless compression. Identical pixels with maximum size preservation."
                "high" -> "Visually indistinguishable quality with modest 20-40% file size reduction."
                "balanced" -> "Optimal balance of visual fidelity and speed (~50-70% reduction). Recommended default."
                "small" -> "Noticeable space reduction for web sharing (~70-85% size savings)."
                "tiny" -> "Maximum compression for bandwidth constraints. May introduce visible smoothing."
                else -> "Custom tuned compression parameters."
            }

            Text(
                text = presetDescription,
                fontSize = 11.5.sp,
                color = textSecondary,
                lineHeight = 16.sp
            )
        }

        // Hardware Acceleration Info Card
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(10.dp))
                .background(cardBg)
                .border(1.dp, borderCol, RoundedCornerShape(10.dp))
                .padding(14.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "ACCELERATION",
                    fontSize = 10.5.sp,
                    fontWeight = FontWeight.Bold,
                    color = textSecondary,
                    letterSpacing = 0.5.sp
                )

                Text(
                    text = "${hwInfo.cpuThreads} CPU Threads",
                    fontSize = 11.sp,
                    color = textSecondary
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = hwInfo.cpuName,
                fontSize = 12.5.sp,
                fontWeight = FontWeight.SemiBold,
                color = textPrimary,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = if (hwInfo.hasAnyGpu) "Hardware Encoder: ${hwInfo.bestVideoEncoder.uppercase()} active" else "Software CPU encoding active",
                fontSize = 11.5.sp,
                color = if (hwInfo.hasAnyGpu) AppColors.SupabaseGreen else textSecondary
            )
        }

        Spacer(modifier = Modifier.height(40.dp))
    }
}

@Composable
private fun MobileQueueScreen(
    engine: CompressionEngine,
    tasks: List<CompressionTask>,
    isRunning: Boolean,
    isPaused: Boolean,
    isDark: Boolean,
    onPickFiles: () -> Unit
) {
    val textPrimary = if (isDark) AppColors.DarkTextPrimary else AppColors.LightTextPrimary
    val textSecondary = if (isDark) AppColors.DarkTextSecondary else AppColors.LightTextSecondary
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder

    Column(modifier = Modifier.fillMaxSize()) {
        // Queue Action Header
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 10.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Queue (${tasks.size})",
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold,
                color = textPrimary
            )

            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                if (tasks.isNotEmpty()) {
                    if (!isRunning) {
                        SupabasePrimaryButton(
                            text = "Start",
                            icon = AppIcons.Play,
                            onClick = { engine.start() },
                            isDark = isDark,
                            modifier = Modifier.height(34.dp)
                        )

                        SupabaseSecondaryButton(
                            text = "Clear",
                            icon = AppIcons.Trash,
                            onClick = { engine.clearQueue() },
                            isDark = isDark,
                            modifier = Modifier.height(34.dp)
                        )
                    } else {
                        SupabaseSecondaryButton(
                            text = if (isPaused) "Resume" else "Pause",
                            icon = if (isPaused) AppIcons.Play else AppIcons.Pause,
                            onClick = { if (isPaused) engine.resume() else engine.pause() },
                            isDark = isDark,
                            modifier = Modifier.height(34.dp)
                        )

                        SupabaseDangerButton(
                            text = "Stop",
                            icon = AppIcons.Stop,
                            onClick = { engine.cancel() },
                            isDark = isDark,
                            modifier = Modifier.height(34.dp)
                        )
                    }
                }
            }
        }

        HorizontalDivider(color = borderCol, thickness = 1.dp)

        if (tasks.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(32.dp),
                contentAlignment = Alignment.Center
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Box(
                        modifier = Modifier
                            .size(54.dp)
                            .clip(RoundedCornerShape(14.dp))
                            .background(if (isDark) Color(0x1F3ECF8E) else Color(0x153ECF8E)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = AppIcons.Queue,
                            contentDescription = null,
                            modifier = Modifier.size(28.dp),
                            tint = AppColors.SupabaseGreen
                        )
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    Text(
                        text = "Your Queue is Empty",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = textPrimary,
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = "Add photos or videos to begin batch compression",
                        fontSize = 12.sp,
                        color = textSecondary,
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(18.dp))

                    SupabasePrimaryButton(
                        text = "Choose Files",
                        icon = AppIcons.Plus,
                        onClick = onPickFiles,
                        isDark = isDark,
                        modifier = Modifier.height(44.dp)
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(horizontal = 14.dp, vertical = 10.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                items(tasks, key = { it.id }) { task ->
                    TaskCardWidget(
                        task = task,
                        onCancelTask = { engine.cancelTask(it) },
                        isDark = isDark
                    )
                }
                item {
                    Spacer(modifier = Modifier.height(50.dp))
                }
            }
        }
    }
}

@Composable
private fun MobileDashboardScreen(
    sessionStats: SessionStats,
    perfStats: PerfStats,
    hwInfo: HardwareInfo,
    overallProgress: Float,
    statusMessage: String,
    isDark: Boolean
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        StatsCardWidget(
            stats = sessionStats,
            overallProgress = overallProgress,
            statusText = statusMessage,
            isDark = isDark
        )

        PerfCardWidget(
            perf = perfStats,
            hwInfo = hwInfo,
            isDark = isDark
        )

        Spacer(modifier = Modifier.height(40.dp))
    }
}
