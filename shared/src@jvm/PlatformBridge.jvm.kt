package org.example.project.platform

import org.example.project.models.*
import java.io.File

actual object PlatformBridge {
    actual fun getHardwareInfo(force: Boolean): HardwareInfo {
        return JvmHardwareDetector.detectHardware(force)
    }

    actual fun getLivePerfStats(): PerfStats {
        val cpu = JvmHardwareDetector.getCpuUsage()
        val (ramUsed, ramTotal) = JvmHardwareDetector.getRamUsage()
        val (gpu, vram) = JvmHardwareDetector.getGpuUsage()
        return PerfStats(
            cpuPercent = cpu,
            ramUsedGb = ramUsed,
            ramTotalGb = ramTotal,
            gpuPercent = gpu,
            vramUsedGb = vram
        )
    }

    actual fun runDiagnostics(force: Boolean): DiagnosticsResult {
        val ffmpegVer = JvmHardwareDetector.getFfmpegVersion()
        val ffprobeVer = JvmHardwareDetector.getFfprobeVersion()
        val hw = JvmHardwareDetector.detectHardware(force)
        val allEnc = JvmHardwareDetector.listFfmpegEncoders().toSet()

        val checkEnc = listOf(
            "hevc_vaapi", "h264_vaapi",
            "hevc_nvenc", "h264_nvenc",
            "hevc_amf", "h264_amf",
            "hevc_qsv", "h264_qsv",
            "hevc_videotoolbox", "h264_videotoolbox",
            "libx265", "libx264",
            "libsvtav1", "libopenh264",
            "libaom-av1"
        )
        val encMap = checkEnc.associateWith { it in allEnc }

        val driDir = File("/dev/dri")
        val driDevices = if (driDir.isDirectory) {
            driDir.list { _, name -> name.startsWith("renderD") }?.sorted()?.toList() ?: emptyList()
        } else emptyList()

        val (_, ramTotal) = JvmHardwareDetector.getRamUsage()

        return DiagnosticsResult(
            ffmpegVersion = ffmpegVer,
            ffmpegOk = ffmpegVer != "not found",
            ffprobeVersion = ffprobeVer,
            ffprobeOk = ffprobeVer != "not found",
            hwInfo = hw,
            supportedEncoders = encMap,
            driDevices = driDevices,
            osName = System.getProperty("os.name") ?: "",
            osArch = System.getProperty("os.arch") ?: "",
            jvmVersion = System.getProperty("java.version") ?: "",
            totalRamGb = ramTotal
        )
    }

    actual fun loadSettings(): AppSettings {
        return JvmSettingsStore.loadSettings()
    }

    actual fun saveSettings(settings: AppSettings) {
        JvmSettingsStore.saveSettings(settings)
    }

    actual suspend fun pickFiles(title: String, extensions: List<String>): List<String> {
        return JvmFileDialogs.pickFiles(title, extensions)
    }

    actual suspend fun pickFolder(title: String): String? {
        return JvmFileDialogs.pickFolder(title)
    }

    actual suspend fun scanFolder(folderPath: String, extensions: Set<String>): List<String> {
        return JvmFileDialogs.scanFolder(folderPath, extensions)
    }

    actual suspend fun compressItem(
        task: CompressionTask,
        settings: AppSettings,
        useHw: Boolean,
        hwInfo: HardwareInfo,
        onProgress: (Float) -> Unit,
        isCancelled: () -> Boolean
    ): CompressionResult {
        return when (task.mediaType) {
            MediaType.VIDEO -> JvmMediaCompressor.compressVideo(task, settings, hwInfo, useHw, onProgress, isCancelled)
            MediaType.IMAGE -> JvmMediaCompressor.compressImage(task, settings, onProgress, isCancelled)
            else -> CompressionResult(
                success = true,
                newSize = task.origSize,
                encoderUsed = "Skipped (unrecognized format)",
                skipped = true
            )
        }
    }
}
