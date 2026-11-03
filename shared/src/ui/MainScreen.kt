package org.example.project.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import org.example.project.engine.CompressionEngine
import org.example.project.models.MediaType
import org.example.project.platform.PlatformBridge
import org.example.project.theme.AppColors
import org.example.project.theme.MediaCrushTheme
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
            BoxWithConstraints(modifier = Modifier.fillMaxSize()) {
                if (maxWidth < 600.dp) {
                    MobileMainLayout(
                        engine = engine,
                        tasks = tasks,
                        logs = logs,
                        sessionStats = sessionStats,
                        perfStats = perfStats,
                        hwInfo = hwInfo,
                        settings = settings,
                        statusMessage = statusMessage,
                        overallProgress = overallProgress,
                        isRunning = isRunning,
                        isPaused = isPaused,
                        isDark = isDarkTheme,
                        onToggleTheme = {
                            val nextTheme = if (isDarkTheme) "light" else "dark"
                            isDarkTheme = (nextTheme == "dark")
                            engine.updateSettings(
                                settings.copy(ui = settings.ui.copy(theme = nextTheme))
                            )
                        },
                        onOpenSettings = { showSettingsDialog = true },
                        onOpenDiagnostics = { showDiagnosticsDialog = true },
                        onPickFiles = { pickAndAddFiles() },
                        onPickFolder = { pickAndAddFolder() }
                    )
                } else {
                    DesktopMainLayout(
                        engine = engine,
                        tasks = tasks,
                        logs = logs,
                        sessionStats = sessionStats,
                        perfStats = perfStats,
                        hwInfo = hwInfo,
                        settings = settings,
                        statusMessage = statusMessage,
                        overallProgress = overallProgress,
                        isRunning = isRunning,
                        isPaused = isPaused,
                        isDarkTheme = isDarkTheme,
                        selectedTab = selectedTab,
                        onSelectTab = { selectedTab = it },
                        unreadLogs = unreadLogs,
                        onToggleTheme = {
                            val nextTheme = if (isDarkTheme) "light" else "dark"
                            isDarkTheme = (nextTheme == "dark")
                            engine.updateSettings(
                                settings.copy(ui = settings.ui.copy(theme = nextTheme))
                            )
                        },
                        onOpenSettings = { showSettingsDialog = true },
                        onOpenDiagnostics = { showDiagnosticsDialog = true },
                        onPickFiles = { pickAndAddFiles() },
                        onPickFolder = { pickAndAddFolder() }
                    )
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
