package org.example.project.platform

import org.example.project.models.*

data class CompressionResult(
    val success: Boolean,
    val newSize: Long,
    val encoderUsed: String,
    val errorMsg: String? = null,
    val skipped: Boolean = false
)

expect object PlatformBridge {
    fun getHardwareInfo(force: Boolean = false): HardwareInfo
    fun getLivePerfStats(): PerfStats
    fun runDiagnostics(force: Boolean = false): DiagnosticsResult
    fun loadSettings(): AppSettings
    fun saveSettings(settings: AppSettings)
    suspend fun pickFiles(title: String, extensions: List<String>): List<String>
    suspend fun pickFolder(title: String): String?
    suspend fun scanFolder(folderPath: String, extensions: Set<String>): List<String>
    suspend fun compressItem(
        task: CompressionTask,
        settings: AppSettings,
        useHw: Boolean,
        hwInfo: HardwareInfo,
        onProgress: (Float) -> Unit,
        isCancelled: () -> Boolean
    ): CompressionResult
}
