package org.example.project.platform

import org.example.project.models.*

actual object PlatformBridge {
    actual fun getHardwareInfo(force: Boolean): HardwareInfo = HardwareInfo(osPlatform = "ios", hasVideoToolbox = true)
    actual fun getLivePerfStats(): PerfStats = PerfStats()
    actual fun runDiagnostics(force: Boolean): DiagnosticsResult = DiagnosticsResult()
    actual fun loadSettings(): AppSettings = AppSettings()
    actual fun saveSettings(settings: AppSettings) {}
    actual suspend fun pickFiles(title: String, extensions: List<String>): List<String> = emptyList()
    actual suspend fun pickFolder(title: String): String? = null
    actual suspend fun scanFolder(folderPath: String, extensions: Set<String>): List<String> = emptyList()
    actual suspend fun compressItem(
        task: CompressionTask,
        settings: AppSettings,
        useHw: Boolean,
        hwInfo: HardwareInfo,
        onProgress: (Float) -> Unit,
        isCancelled: () -> Boolean
    ): CompressionResult = CompressionResult(success = false, newSize = task.origSize, encoderUsed = "iOS stub")
}
