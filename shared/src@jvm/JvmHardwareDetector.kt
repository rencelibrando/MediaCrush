package org.example.project.platform

import org.example.project.models.HardwareInfo
import java.io.File
import java.lang.management.ManagementFactory
import java.util.concurrent.TimeUnit
import kotlinx.serialization.json.Json

object JvmHardwareDetector {
    private val json = Json { ignoreUnknownKeys = true; prettyPrint = true }

    private val isWindows: Boolean
        get() = System.getProperty("os.name").lowercase().contains("win")

    private val isMac: Boolean
        get() = System.getProperty("os.name").lowercase().contains("mac")

    private val isLinux: Boolean
        get() = !isWindows && !isMac

    val platformName: String
        get() = when {
            isWindows -> "windows"
            isMac -> "darwin"
            else -> "linux"
        }

    private val cacheFile: File
        get() {
            return if (isWindows) {
                val appData = System.getenv("APPDATA") ?: System.getProperty("user.home")
                File(appData, "MediaCrush/hw_cache.json")
            } else {
                val home = System.getProperty("user.home")
                File(home, ".config/mediacrush/hw_cache.json")
            }
        }

    data class CommandResult(val exitCode: Int, val stdout: String, val stderr: String)

    fun runCommand(cmd: List<String>, timeoutSec: Long = 15): CommandResult {
        return try {
            val pb = ProcessBuilder(cmd)
            pb.environment()["LANG"] = "C"
            val proc = pb.start()

            val stdoutBuilder = StringBuilder()
            val stderrBuilder = StringBuilder()

            val tOut = Thread {
                try {
                    proc.inputStream.bufferedReader().useLines { lines ->
                        lines.forEach { stdoutBuilder.appendLine(it) }
                    }
                } catch (_: Exception) {}
            }
            val tErr = Thread {
                try {
                    proc.errorStream.bufferedReader().useLines { lines ->
                        lines.forEach { stderrBuilder.appendLine(it) }
                    }
                } catch (_: Exception) {}
            }
            tOut.start()
            tErr.start()

            val finished = proc.waitFor(timeoutSec, TimeUnit.SECONDS)
            if (!finished) {
                proc.destroyForcibly()
                return CommandResult(-1, "", "Timeout expired ($timeoutSec s)")
            }
            tOut.join(1000)
            tErr.join(1000)
            CommandResult(proc.exitValue(), stdoutBuilder.toString().trim(), stderrBuilder.toString().trim())
        } catch (e: Exception) {
            CommandResult(-1, "", e.message ?: "Execution error")
        }
    }

    private fun testEncode(cmd: List<String>, outPath: String): Pair<Boolean, String> {
        val r = runCommand(cmd, timeoutSec = 20)
        try { File(outPath).delete() } catch (_: Exception) {}
        return Pair(r.exitCode == 0, r.stderr)
    }

    private fun probeEncoder(info: HardwareInfo, label: String, encoders: List<String>, extraArgs: List<String> = emptyList()): Pair<Boolean, String?> {
        val errors = mutableListOf<String>()
        val tmpDir = System.getProperty("java.io.tmpdir")
        for (encoder in encoders) {
            val tmp = File(tmpDir, "_mc_${label.lowercase()}_${ProcessHandle.current().pid()}.mp4").absolutePath
            val cmd = mutableListOf(
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "testsrc=duration=0.1:size=256x144:rate=5",
                "-c:v", encoder
            )
            cmd.addAll(extraArgs)
            cmd.addAll(listOf("-loglevel", "error", tmp))

            val (ok, stderr) = testEncode(cmd, tmp)
            if (ok) {
                return Pair(true, encoder)
            }
            errors.add("$encoder: ${stderr.take(100)}")
        }
        return Pair(false, null)
    }

    private fun probeVaapi(diagLog: MutableList<String>): Pair<Boolean, String> {
        if (!isLinux) return Pair(false, "/dev/dri/renderD128")
        val driDir = File("/dev/dri")
        val devices = if (driDir.isDirectory) {
            driDir.listFiles { _, name -> name.startsWith("renderD") }?.sortedBy { it.name }?.map { it.absolutePath } ?: emptyList()
        } else emptyList()

        if (devices.isEmpty()) {
            diagLog.add("VAAPI: no /dev/dri/renderD* devices found")
            return Pair(false, "/dev/dri/renderD128")
        }

        val tmpDir = System.getProperty("java.io.tmpdir")
        for (dev in devices) {
            for (enc in listOf("hevc_vaapi", "h264_vaapi")) {
                val tmp = File(tmpDir, "_mc_vaapi_${ProcessHandle.current().pid()}.mp4").absolutePath
                val cmd = listOf(
                    "ffmpeg", "-y",
                    "-vaapi_device", dev,
                    "-f", "lavfi", "-i", "testsrc=duration=0.1:size=256x144:rate=5",
                    "-vf", "format=nv12,hwupload",
                    "-c:v", enc, "-qp", "30",
                    "-loglevel", "error",
                    tmp
                )
                val (ok, stderr) = testEncode(cmd, tmp)
                if (ok) {
                    diagLog.add("VAAPI: OK ($enc) on $dev")
                    return Pair(true, dev)
                } else {
                    diagLog.add("VAAPI: FAIL ($enc) on $dev - ${stderr.take(100)}")
                }
            }
        }
        return Pair(false, "/dev/dri/renderD128")
    }

    fun detectGpuName(): String {
        if (isLinux) {
            val rMm = runCommand(listOf("lspci", "-mm"))
            if (rMm.exitCode == 0) {
                for (line in rMm.stdout.lines()) {
                    val ll = line.lowercase()
                    if (ll.contains("vga") || ll.contains("3d controller") || ll.contains("display")) {
                        val parts = line.split("\"").map { it.trim() }
                        val name = parts.filterIndexed { idx, _ -> idx in 3..5 }.joinToString(" ")
                        if (name.isNotBlank()) return name.trim()
                    }
                }
            }
            val rPlain = runCommand(listOf("lspci"))
            if (rPlain.exitCode == 0) {
                for (line in rPlain.stdout.lines()) {
                    val ll = line.lowercase()
                    if (ll.contains("vga") || ll.contains("3d") || ll.contains("display")) {
                        return line.substringAfterLast(":").trim()
                    }
                }
            }
            for (path in listOf("/sys/class/drm/card0/device/product_name", "/sys/class/drm/card1/device/product_name")) {
                val f = File(path)
                if (f.exists()) {
                    return f.readText().trim()
                }
            }
        } else if (isWindows) {
            val r = runCommand(listOf("powershell", "-NoProfile", "-Command",
                "Get-CimInstance Win32_VideoController | Where-Object { \$_.Name } | ForEach-Object { \$_.Name }"))
            if (r.exitCode == 0 && r.stdout.isNotBlank()) {
                val names = r.stdout.lines().map { it.trim() }.filter { it.isNotEmpty() }
                if (names.isNotEmpty()) return names.joinToString(" + ")
            }
        } else if (isMac) {
            val r = runCommand(listOf("system_profiler", "SPDisplaysDataType"))
            if (r.exitCode == 0) {
                for (line in r.stdout.lines()) {
                    if (line.contains("Chipset Model:") || line.contains("Device Name:")) {
                        return line.substringAfter(":").trim()
                    }
                }
            }
        }
        return "Unknown GPU"
    }

    fun detectCpuName(): String {
        if (isLinux) {
            val cpuInfo = File("/proc/cpuinfo")
            if (cpuInfo.exists()) {
                val found = cpuInfo.useLines { lines ->
                    lines.firstOrNull { it.startsWith("model name") }
                }
                if (found != null) {
                    return found.substringAfter(":").trim()
                }
            }
        } else if (isWindows) {
            val r = runCommand(listOf("powershell", "-NoProfile", "-Command",
                "Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name"))
            if (r.exitCode == 0 && r.stdout.isNotBlank()) {
                return r.stdout.trim()
            }
        } else if (isMac) {
            val r = runCommand(listOf("sysctl", "-n", "machdep.cpu.brand_string"))
            if (r.exitCode == 0 && r.stdout.isNotBlank()) {
                return r.stdout.trim()
            }
        }
        return System.getProperty("os.arch") ?: "Unknown CPU"
    }

    fun listFfmpegEncoders(): List<String> {
        val r = runCommand(listOf("ffmpeg", "-encoders", "-v", "quiet"), timeoutSec = 10)
        if (r.exitCode != 0) return emptyList()
        val enc = mutableListOf<String>()
        for (line in r.stdout.lines()) {
            val stripped = line.trim()
            if (stripped.isNotEmpty() && stripped[0] in listOf('V', 'A', 'S')) {
                val parts = stripped.split("\\s+".toRegex())
                if (parts.size > 1) {
                    enc.add(parts[1])
                }
            }
        }
        return enc
    }

    fun detectHardware(force: Boolean = false): HardwareInfo {
        if (!force && cacheFile.exists()) {
            try {
                val text = cacheFile.readText()
                val cached = json.decodeFromString<HardwareInfo>(text)
                return cached
            } catch (_: Exception) {}
        }

        val diagLog = mutableListOf<String>()
        val cpuThreads = Runtime.getRuntime().availableProcessors()
        val cpuName = detectCpuName()
        val gpuName = detectGpuName()
        val osPlatform = platformName

        diagLog.add("Platform: $osPlatform")
        diagLog.add("CPU: $cpuName ($cpuThreads threads)")
        diagLog.add("GPU: $gpuName")

        var hasNvenc = false
        var hasVaapi = false
        var vaapiDevice = "/dev/dri/renderD128"
        var hasAmf = false
        var hasQsv = false
        var hasD3d11va = false
        var hasVideoToolbox = false

        // NVENC test
        val (nvencOk, _) = probeEncoder(HardwareInfo(), "NVENC", listOf("hevc_nvenc", "h264_nvenc"), listOf("-preset", "p1"))
        if (nvencOk) {
            hasNvenc = true
            diagLog.add("NVENC: OK (hevc_nvenc / h264_nvenc)")
        } else {
            diagLog.add("NVENC: not available")
        }

        if (isLinux) {
            val (vaapiOk, dev) = probeVaapi(diagLog)
            hasVaapi = vaapiOk
            vaapiDevice = dev

            val (qsvOk, _) = probeEncoder(HardwareInfo(), "QSV", listOf("hevc_qsv", "h264_qsv"))
            hasQsv = qsvOk
            if (qsvOk) diagLog.add("QSV: OK")
        } else if (isWindows) {
            val (amfOk, _) = probeEncoder(HardwareInfo(), "AMF", listOf("hevc_amf", "h264_amf"), listOf("-quality", "speed"))
            hasAmf = amfOk
            if (amfOk) diagLog.add("AMF: OK")

            val (qsvOk, _) = probeEncoder(HardwareInfo(), "QSV", listOf("hevc_qsv", "h264_qsv"))
            hasQsv = qsvOk

            val rD3d = runCommand(listOf("ffmpeg", "-hide_banner", "-hwaccels"))
            if (rD3d.exitCode == 0 && rD3d.stdout.lowercase().contains("d3d11va")) {
                hasD3d11va = true
                diagLog.add("D3D11VA: OK (decode)")
            }
        } else if (isMac) {
            val (vtOk, _) = probeEncoder(HardwareInfo(), "VideoToolbox", listOf("hevc_videotoolbox", "h264_videotoolbox"))
            hasVideoToolbox = vtOk
            if (vtOk) diagLog.add("VideoToolbox: OK")
        }

        val info = HardwareInfo(
            hasVaapi = hasVaapi,
            vaapiDevice = vaapiDevice,
            hasNvenc = hasNvenc,
            hasAmf = hasAmf,
            hasQsv = hasQsv,
            hasD3d11va = hasD3d11va,
            hasVideoToolbox = hasVideoToolbox,
            cpuThreads = cpuThreads,
            cpuName = cpuName,
            gpuName = gpuName,
            osPlatform = osPlatform,
            diagLog = diagLog
        )

        try {
            cacheFile.parentFile?.mkdirs()
            cacheFile.writeText(json.encodeToString(HardwareInfo.serializer(), info))
        } catch (_: Exception) {}

        return info
    }

    fun getFfmpegVersion(): String {
        val r = runCommand(listOf("ffmpeg", "-version"), timeoutSec = 5)
        return if (r.exitCode == 0 && r.stdout.isNotEmpty()) {
            val firstLine = r.stdout.lines().firstOrNull() ?: ""
            firstLine.replace("ffmpeg version", "").trim().substringBefore(" ")
        } else "not found"
    }

    fun getFfprobeVersion(): String {
        val r = runCommand(listOf("ffprobe", "-version"), timeoutSec = 5)
        return if (r.exitCode == 0 && r.stdout.isNotEmpty()) {
            val firstLine = r.stdout.lines().firstOrNull() ?: ""
            firstLine.replace("ffprobe version", "").trim().substringBefore(" ")
        } else "not found"
    }

    fun getCpuUsage(): Float {
        return try {
            val osBean = ManagementFactory.getOperatingSystemMXBean()
            if (osBean is com.sun.management.OperatingSystemMXBean) {
                val load = osBean.cpuLoad
                if (load >= 0) (load * 100.0).toFloat() else 0f
            } else 0f
        } catch (_: Exception) { 0f }
    }

    fun getRamUsage(): Pair<Double, Double> {
        return try {
            val osBean = ManagementFactory.getOperatingSystemMXBean()
            if (osBean is com.sun.management.OperatingSystemMXBean) {
                val total = osBean.totalMemorySize.toDouble() / 1e9
                val free = osBean.freeMemorySize.toDouble() / 1e9
                Pair(maxOf(0.0, total - free), total)
            } else Pair(0.0, 0.0)
        } catch (_: Exception) { Pair(0.0, 0.0) }
    }

    fun getGpuUsage(): Pair<Float, Double> {
        // Try nvidia-smi
        val r = runCommand(listOf("nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"), timeoutSec = 3)
        if (r.exitCode == 0 && r.stdout.isNotBlank()) {
            val parts = r.stdout.lines().first().split(",")
            if (parts.size >= 2) {
                val util = parts[0].trim().toFloatOrNull() ?: 0f
                val memMb = parts[1].trim().toDoubleOrNull() ?: 0.0
                return Pair(util, memMb / 1024.0)
            }
        }
        return Pair(-1f, 0.0)
    }
}
