package org.example.project.ui.dialogs

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
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
import androidx.compose.ui.window.Dialog
import kotlinx.coroutines.launch
import org.example.project.models.*
import org.example.project.platform.PlatformBridge
import org.example.project.theme.AppColors
import org.example.project.theme.AppIcons
import org.example.project.ui.components.SupabasePrimaryButton
import org.example.project.ui.components.SupabaseSecondaryButton

@Composable
fun SettingsDialog(
    initialSettings: AppSettings,
    hwInfo: HardwareInfo,
    onSave: (AppSettings) -> Unit,
    onDismiss: () -> Unit,
    onReprobeHw: () -> Unit,
    isDark: Boolean = true
) {
    var selectedTab by remember { mutableStateOf(0) }
    var currentSettings by remember { mutableStateOf(initialSettings) }
    val scope = rememberCoroutineScope()

    val bg = if (isDark) AppColors.DarkSurface else AppColors.LightSurface
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder
    val textPrimary = if (isDark) AppColors.DarkTextPrimary else AppColors.LightTextPrimary
    val textSecondary = if (isDark) AppColors.DarkTextSecondary else AppColors.LightTextSecondary

    Dialog(onDismissRequest = onDismiss) {
        Surface(
            modifier = Modifier
                .width(560.dp)
                .wrapContentHeight()
                .clip(RoundedCornerShape(8.dp))
                .border(1.dp, borderCol, RoundedCornerShape(8.dp)),
            color = bg
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp)
            ) {
                // Header
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Settings",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = textPrimary
                    )
                    IconButton(
                        onClick = onDismiss,
                        modifier = Modifier.size(24.dp)
                    ) {
                        Icon(
                            imageVector = AppIcons.Close,
                            contentDescription = "Close",
                            modifier = Modifier.size(14.dp),
                            tint = textSecondary
                        )
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Tab Row
                SecondaryTabRow(
                    selectedTabIndex = selectedTab,
                    containerColor = Color.Transparent,
                    contentColor = AppColors.SupabaseGreen,
                    divider = { HorizontalDivider(color = borderCol) }
                ) {
                    Tab(
                        selected = selectedTab == 0,
                        onClick = { selectedTab = 0 },
                        text = { Text("Images", fontSize = 12.sp, fontWeight = FontWeight.Medium) }
                    )
                    Tab(
                        selected = selectedTab == 1,
                        onClick = { selectedTab = 1 },
                        text = { Text("Videos", fontSize = 12.sp, fontWeight = FontWeight.Medium) }
                    )
                    Tab(
                        selected = selectedTab == 2,
                        onClick = { selectedTab = 2 },
                        text = { Text("Engine", fontSize = 12.sp, fontWeight = FontWeight.Medium) }
                    )
                    Tab(
                        selected = selectedTab == 3,
                        onClick = { selectedTab = 3 },
                        text = { Text("Output", fontSize = 12.sp, fontWeight = FontWeight.Medium) }
                    )
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Tab Content (Scrollable)
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(320.dp)
                        .verticalScroll(rememberScrollState())
                ) {
                    when (selectedTab) {
                        0 -> ImageSettingsTab(
                            settings = currentSettings.image,
                            onChange = { currentSettings = currentSettings.copy(image = it) },
                            textPrimary = textPrimary,
                            textSecondary = textSecondary,
                            isDark = isDark
                        )
                        1 -> VideoSettingsTab(
                            settings = currentSettings.video,
                            onChange = { currentSettings = currentSettings.copy(video = it) },
                            textPrimary = textPrimary,
                            textSecondary = textSecondary,
                            isDark = isDark
                        )
                        2 -> EngineSettingsTab(
                            settings = currentSettings.engine,
                            hwInfo = hwInfo,
                            onChange = { currentSettings = currentSettings.copy(engine = it) },
                            onReprobeHw = onReprobeHw,
                            textPrimary = textPrimary,
                            textSecondary = textSecondary,
                            isDark = isDark
                        )
                        3 -> OutputSettingsTab(
                            settings = currentSettings.engine,
                            onChange = { currentSettings = currentSettings.copy(engine = it) },
                            onBrowseFolder = {
                                scope.launch {
                                    val picked = PlatformBridge.pickFolder("Select output directory")
                                    if (picked != null) {
                                        currentSettings = currentSettings.copy(
                                            engine = currentSettings.engine.copy(outputDir = picked)
                                        )
                                    }
                                }
                            },
                            textPrimary = textPrimary,
                            textSecondary = textSecondary,
                            isDark = isDark
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))
                HorizontalDivider(color = borderCol)
                Spacer(modifier = Modifier.height(14.dp))

                // Bottom Buttons
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End
                ) {
                    SupabaseSecondaryButton(
                        text = "Cancel",
                        onClick = onDismiss,
                        isDark = isDark
                    )
                    Spacer(modifier = Modifier.width(10.dp))
                    SupabasePrimaryButton(
                        text = "Save Settings",
                        onClick = {
                            onSave(currentSettings)
                            onDismiss()
                        },
                        icon = AppIcons.Check,
                        isDark = isDark
                    )
                }
            }
        }
    }
}

@Composable
private fun ImageSettingsTab(
    settings: ImageSettings,
    onChange: (ImageSettings) -> Unit,
    textPrimary: Color,
    textSecondary: Color,
    isDark: Boolean
) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Text("Preset", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
        Spacer(modifier = Modifier.height(6.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            val presets = listOf("lossless", "high", "balanced", "small", "tiny")
            presets.forEach { p ->
                FilterChip(
                    selected = settings.preset == p,
                    onClick = {
                        val q = AppSettings.defaultQualityForPreset(p)
                        onChange(settings.copy(preset = p, quality = q))
                    },
                    label = { Text(p, fontSize = 11.sp) },
                    shape = RoundedCornerShape(6.dp),
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = if (isDark) Color(0x1F3ECF8E) else Color(0x153ECF8E),
                        selectedLabelColor = AppColors.SupabaseGreen
                    )
                )
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text("Quality", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
            Text("${settings.quality}", fontSize = 12.sp, color = AppColors.SupabaseGreen)
        }
        Slider(
            value = settings.quality.toFloat(),
            onValueChange = { onChange(settings.copy(quality = it.toInt())) },
            valueRange = 1f..100f,
            colors = SliderDefaults.colors(
                thumbColor = AppColors.SupabaseGreen,
                activeTrackColor = AppColors.SupabaseGreen
            )
        )

        Spacer(modifier = Modifier.height(14.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Checkbox(
                checked = settings.stripMetadata,
                onCheckedChange = { onChange(settings.copy(stripMetadata = it)) },
                colors = CheckboxDefaults.colors(checkedColor = AppColors.SupabaseGreen)
            )
            Spacer(modifier = Modifier.width(6.dp))
            Text("Strip metadata (EXIF)", fontSize = 12.sp, color = textPrimary)
        }

        Spacer(modifier = Modifier.height(10.dp))

        Text("Max size (longest edge in px, 0 = no resize)", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
        Spacer(modifier = Modifier.height(4.dp))
        OutlinedTextField(
            value = (settings.resizeMaxPx ?: 0).toString(),
            onValueChange = { str ->
                val v = str.toIntOrNull()
                onChange(settings.copy(resizeMaxPx = if (v != null && v > 0) v else null))
            },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(6.dp)
        )
    }
}

@Composable
private fun VideoSettingsTab(
    settings: VideoSettings,
    onChange: (VideoSettings) -> Unit,
    textPrimary: Color,
    textSecondary: Color,
    isDark: Boolean
) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Text("Codec", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
        Spacer(modifier = Modifier.height(6.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            val codecs = listOf("h265", "h264", "av1")
            codecs.forEach { c ->
                FilterChip(
                    selected = settings.codec == c,
                    onClick = { onChange(settings.copy(codec = c)) },
                    label = { Text(c.uppercase(), fontSize = 11.sp) },
                    shape = RoundedCornerShape(6.dp),
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = if (isDark) Color(0x1F3ECF8E) else Color(0x153ECF8E),
                        selectedLabelColor = AppColors.SupabaseGreen
                    )
                )
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text("CRF / QP (Quality)", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
            Text("${settings.quality} (Lower = better quality)", fontSize = 11.sp, color = textSecondary)
        }
        Slider(
            value = settings.quality.toFloat(),
            onValueChange = { onChange(settings.copy(quality = it.toInt())) },
            valueRange = 14f..51f,
            colors = SliderDefaults.colors(
                thumbColor = AppColors.SupabaseGreen,
                activeTrackColor = AppColors.SupabaseGreen
            )
        )

        Spacer(modifier = Modifier.height(14.dp))

        Text("Resolution", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
        Spacer(modifier = Modifier.height(6.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            listOf("original", "4k", "1080p", "720p", "480p").forEach { r ->
                FilterChip(
                    selected = settings.resolution == r,
                    onClick = { onChange(settings.copy(resolution = r)) },
                    label = { Text(r, fontSize = 11.sp) },
                    shape = RoundedCornerShape(6.dp),
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = if (isDark) Color(0x1F3ECF8E) else Color(0x153ECF8E),
                        selectedLabelColor = AppColors.SupabaseGreen
                    )
                )
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        Text("Frame Rate", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
        Spacer(modifier = Modifier.height(6.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            listOf("original", "60", "30", "24").forEach { f ->
                FilterChip(
                    selected = settings.fps == f,
                    onClick = { onChange(settings.copy(fps = f)) },
                    label = { Text(if (f == "original") f else "$f fps", fontSize = 11.sp) },
                    shape = RoundedCornerShape(6.dp),
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = if (isDark) Color(0x1F3ECF8E) else Color(0x153ECF8E),
                        selectedLabelColor = AppColors.SupabaseGreen
                    )
                )
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Checkbox(
                checked = settings.skipHevc,
                onCheckedChange = { onChange(settings.copy(skipHevc = it)) },
                colors = CheckboxDefaults.colors(checkedColor = AppColors.SupabaseGreen)
            )
            Spacer(modifier = Modifier.width(6.dp))
            Text("Skip files already encoded in HEVC/AV1", fontSize = 12.sp, color = textPrimary)
        }
    }
}

@Composable
private fun EngineSettingsTab(
    settings: EngineSettings,
    hwInfo: HardwareInfo,
    onChange: (EngineSettings) -> Unit,
    onReprobeHw: () -> Unit,
    textPrimary: Color,
    textSecondary: Color,
    isDark: Boolean
) {
    val cardBg = if (isDark) AppColors.DarkCard else AppColors.LightCard
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder

    Column(modifier = Modifier.fillMaxWidth()) {
        // Hardware summary card
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(6.dp))
                .background(cardBg)
                .border(1.dp, borderCol, RoundedCornerShape(6.dp))
                .padding(10.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text("Hardware Encoders:", fontSize = 10.5.sp, color = textSecondary)
                Text(hwInfo.hwSummary, fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
            }
            SupabaseSecondaryButton(
                text = "Re-detect",
                onClick = onReprobeHw,
                icon = AppIcons.Refresh,
                isDark = isDark
            )
        }

        Spacer(modifier = Modifier.height(14.dp))

        Text("Performance Mode", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
        Spacer(modifier = Modifier.height(6.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            val modes = listOf("max", "balanced", "power_save", "custom")
            val labels = mapOf("max" to "Maximum", "balanced" to "Balanced", "power_save" to "Quiet", "custom" to "Custom")
            modes.forEach { m ->
                FilterChip(
                    selected = settings.perfMode == m,
                    onClick = {
                        val threads = hwInfo.cpuThreads
                        val updated = when (m) {
                            "max" -> settings.copy(perfMode = m, gpuWorkers = 4, cpuWorkers = threads, cpuThreads = 0, gpuAsyncDepth = 4, hybridDistribution = true)
                            "balanced" -> settings.copy(perfMode = m, gpuWorkers = 2, cpuWorkers = maxOf(2, threads / 2), cpuThreads = 0, gpuAsyncDepth = 2, hybridDistribution = true)
                            "power_save" -> settings.copy(perfMode = m, gpuWorkers = 1, cpuWorkers = 2, cpuThreads = 2, gpuAsyncDepth = 1, hybridDistribution = false)
                            else -> settings.copy(perfMode = m)
                        }
                        onChange(updated)
                    },
                    label = { Text(labels[m] ?: m, fontSize = 11.sp) },
                    shape = RoundedCornerShape(6.dp),
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = if (isDark) Color(0x1F3ECF8E) else Color(0x153ECF8E),
                        selectedLabelColor = AppColors.SupabaseGreen
                    )
                )
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // Worker sliders
        Row(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.weight(1f)) {
                Text("GPU Parallel Streams: ${settings.gpuWorkers}", fontSize = 11.sp, color = textPrimary)
                Slider(
                    value = settings.gpuWorkers.toFloat(),
                    onValueChange = { onChange(settings.copy(gpuWorkers = it.toInt(), perfMode = "custom")) },
                    valueRange = 0f..16f,
                    colors = SliderDefaults.colors(
                        thumbColor = AppColors.SupabaseGreen,
                        activeTrackColor = AppColors.SupabaseGreen
                    )
                )
            }
            Spacer(modifier = Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text("CPU Concurrent Tasks: ${settings.cpuWorkers}", fontSize = 11.sp, color = textPrimary)
                Slider(
                    value = settings.cpuWorkers.toFloat(),
                    onValueChange = { onChange(settings.copy(cpuWorkers = it.toInt(), perfMode = "custom")) },
                    valueRange = 1f..32f,
                    colors = SliderDefaults.colors(
                        thumbColor = AppColors.SupabaseGreen,
                        activeTrackColor = AppColors.SupabaseGreen
                    )
                )
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Checkbox(
                checked = settings.hybridDistribution,
                onCheckedChange = { onChange(settings.copy(hybridDistribution = it, perfMode = "custom")) },
                colors = CheckboxDefaults.colors(checkedColor = AppColors.SupabaseGreen)
            )
            Spacer(modifier = Modifier.width(6.dp))
            Text("Engage both GPU and CPU simultaneously on task queue", fontSize = 12.sp, color = textPrimary)
        }
    }
}

@Composable
private fun OutputSettingsTab(
    settings: EngineSettings,
    onChange: (EngineSettings) -> Unit,
    onBrowseFolder: () -> Unit,
    textPrimary: Color,
    textSecondary: Color,
    isDark: Boolean
) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Text("Output Mode", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
        Spacer(modifier = Modifier.height(6.dp))

        val modes = listOf(
            Pair("inplace", "Replace original files (inplace)"),
            Pair("alongside", "Same folder with _compressed suffix"),
            Pair("custom", "Save to custom directory")
        )

        modes.forEach { (mode, label) ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                RadioButton(
                    selected = settings.outputMode == mode,
                    onClick = { onChange(settings.copy(outputMode = mode)) },
                    colors = RadioButtonDefaults.colors(selectedColor = AppColors.SupabaseGreen)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(label, fontSize = 12.sp, color = textPrimary)
            }
        }

        if (settings.outputMode == "custom") {
            Spacer(modifier = Modifier.height(14.dp))
            Text("Custom Directory", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = textPrimary)
            Spacer(modifier = Modifier.height(6.dp))
            Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                OutlinedTextField(
                    value = settings.outputDir,
                    onValueChange = { onChange(settings.copy(outputDir = it)) },
                    placeholder = { Text("Select folder...", fontSize = 12.sp) },
                    singleLine = true,
                    shape = RoundedCornerShape(6.dp),
                    modifier = Modifier.weight(1f)
                )
                Spacer(modifier = Modifier.width(8.dp))
                SupabaseSecondaryButton(
                    text = "Browse",
                    onClick = onBrowseFolder,
                    icon = AppIcons.Folder,
                    isDark = isDark
                )
            }
        }
    }
}
