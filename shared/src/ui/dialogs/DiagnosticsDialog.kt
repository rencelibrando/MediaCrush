package org.example.project.ui.dialogs

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
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import org.example.project.models.DiagnosticsResult
import org.example.project.platform.PlatformBridge
import org.example.project.theme.AppColors
import org.example.project.theme.AppIcons
import org.example.project.ui.components.SupabasePrimaryButton
import org.example.project.ui.components.SupabaseSecondaryButton

@Composable
fun DiagnosticsDialog(
    onDismiss: () -> Unit,
    isDark: Boolean = true
) {
    val scope = rememberCoroutineScope()
    var isLoading by remember { mutableStateOf(true) }
    var result by remember { mutableStateOf<DiagnosticsResult?>(null) }

    fun runDiag(force: Boolean = false) {
        isLoading = true
        scope.launch(Dispatchers.IO) {
            val res = PlatformBridge.runDiagnostics(force)
            result = res
            isLoading = false
        }
    }

    LaunchedEffect(Unit) {
        runDiag(force = false)
    }

    val bg = if (isDark) AppColors.DarkSurface else AppColors.LightSurface
    val cardBg = if (isDark) AppColors.DarkCard else AppColors.LightCard
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder
    val textPrimary = if (isDark) AppColors.DarkTextPrimary else AppColors.LightTextPrimary
    val textSecondary = if (isDark) AppColors.DarkTextSecondary else AppColors.LightTextSecondary

    Dialog(onDismissRequest = onDismiss) {
        Surface(
            modifier = Modifier
                .width(620.dp)
                .wrapContentHeight()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, borderCol, RoundedCornerShape(12.dp)),
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
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = AppIcons.Diagnostics,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp),
                            tint = AppColors.SupabaseGreen
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "System Diagnostics",
                            fontSize = 17.sp,
                            fontWeight = FontWeight.Bold,
                            color = textPrimary
                        )
                    }
                    SupabaseSecondaryButton(
                        text = "Re-run All Checks",
                        icon = AppIcons.Refresh,
                        onClick = { runDiag(force = true) },
                        enabled = !isLoading,
                        isDark = isDark
                    )
                }

                Spacer(modifier = Modifier.height(14.dp))

                if (isLoading) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(260.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            CircularProgressIndicator(color = AppColors.SupabaseGreen)
                            Spacer(modifier = Modifier.height(10.dp))
                            Text("Running hardware probes...", fontSize = 12.sp, color = textSecondary)
                        }
                    }
                } else {
                    val r = result ?: DiagnosticsResult()
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(380.dp)
                            .verticalScroll(rememberScrollState())
                    ) {
                        // Section: Binaries & System
                        Text("CORE BINARIES & SYSTEM", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = textSecondary, letterSpacing = 0.5.sp)
                        Spacer(modifier = Modifier.height(6.dp))
                        DiagStatusRow("FFmpeg Binary", if (r.ffmpegOk) "v${r.ffmpegVersion}" else "Not Found", r.ffmpegOk, textPrimary, textSecondary)
                        DiagStatusRow("FFprobe Binary", if (r.ffprobeOk) "v${r.ffprobeVersion}" else "Not Found", r.ffprobeOk, textPrimary, textSecondary)
                        DiagStatusRow("GPU Acceleration", r.hwInfo.hwSummary, r.hwInfo.hasAnyGpu, textPrimary, textSecondary)
                        DiagStatusRow("CPU", "${r.hwInfo.cpuName} (${r.hwInfo.cpuThreads} threads)", true, textPrimary, textSecondary)
                        DiagStatusRow("Total RAM", "${(r.totalRamGb * 10).toLong() / 10.0} GB", true, textPrimary, textSecondary)
                        DiagStatusRow("OS / Platform", "${r.osName} (${r.osArch})", true, textPrimary, textSecondary)

                        if (r.driDevices.isNotEmpty()) {
                            DiagStatusRow("DRI Render Devices", r.driDevices.joinToString(", "), true, textPrimary, textSecondary)
                        }

                        Spacer(modifier = Modifier.height(14.dp))

                        // Section: Encoders
                        Text("ENCODERS STATUS", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = textSecondary, letterSpacing = 0.5.sp)
                        Spacer(modifier = Modifier.height(6.dp))

                        val colCount = 2
                        val entries = r.supportedEncoders.entries.toList()
                        for (i in entries.indices step colCount) {
                            Row(modifier = Modifier.fillMaxWidth()) {
                                val e1 = entries[i]
                                Box(modifier = Modifier.weight(1f)) {
                                    DiagStatusRow(e1.key, if (e1.value) "Supported" else "Missing", e1.value, textPrimary, textSecondary)
                                }
                                if (i + 1 < entries.size) {
                                    val e2 = entries[i + 1]
                                    Box(modifier = Modifier.weight(1f)) {
                                        DiagStatusRow(e2.key, if (e2.value) "Supported" else "Missing", e2.value, textPrimary, textSecondary)
                                    }
                                } else {
                                    Spacer(modifier = Modifier.weight(1f))
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(14.dp))

                        // Section: Probe Log
                        Text("HARDWARE PROBE LOG", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = textSecondary, letterSpacing = 0.5.sp)
                        Spacer(modifier = Modifier.height(6.dp))
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(6.dp))
                                .background(cardBg)
                                .border(1.dp, borderCol, RoundedCornerShape(6.dp))
                                .padding(8.dp)
                        ) {
                            Column {
                                r.hwInfo.diagLog.forEach { logLine ->
                                    val logCol = when {
                                        logLine.contains("OK", ignoreCase = true) -> AppColors.SupabaseGreen
                                        logLine.contains("FAIL", ignoreCase = true) -> AppColors.StatusError
                                        else -> textSecondary
                                    }
                                    Text(
                                        text = logLine,
                                        fontSize = 11.sp,
                                        fontFamily = FontFamily.Monospace,
                                        color = logCol
                                    )
                                }
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))
                HorizontalDivider(color = borderCol)
                Spacer(modifier = Modifier.height(10.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End
                ) {
                    SupabasePrimaryButton(
                        text = "Close",
                        onClick = onDismiss,
                        isDark = isDark
                    )
                }
            }
        }
    }
}

@Composable
private fun DiagStatusRow(
    label: String,
    value: String,
    ok: Boolean,
    textPrimary: Color,
    textSecondary: Color
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 3.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        val dotCol = if (ok) AppColors.SupabaseGreen else AppColors.StatusError
        Box(
            modifier = Modifier
                .size(7.dp)
                .clip(CircleShape)
                .background(dotCol)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = label,
            fontSize = 11.sp,
            fontWeight = FontWeight.Medium,
            color = textSecondary,
            modifier = Modifier.width(140.dp)
        )
        Text(
            text = value,
            fontSize = 12.sp,
            fontWeight = FontWeight.SemiBold,
            color = textPrimary
        )
    }
}
