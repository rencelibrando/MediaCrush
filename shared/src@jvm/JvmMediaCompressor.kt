package org.example.project.platform

import org.example.project.models.*
import java.io.File
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import java.util.ArrayDeque
import java.util.regex.Pattern
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext

object JvmMediaCompressor {

    private fun getVideoDuration(path: String): Double {
        val r = JvmHardwareDetector.runCommand(listOf(
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", path
        ), timeoutSec = 20)
        if (r.exitCode == 0 && r.stdout.isNotBlank()) {
            val durMatch = Pattern.compile("\"duration\"\\s*:\\s*\"([0-9.]+)\"").matcher(r.stdout)
            if (durMatch.find()) {
                durMatch.group(1).toDoubleOrNull()?.let { if (it > 0) return it }
            }
        }
        return 0.0
    }

    private fun getVideoCodec(path: String): String {
        val r = JvmHardwareDetector.runCommand(listOf(
            "ffprobe", "-v", "quiet", "-select_streams", "v:0",
            "-show_entries", "stream=codec_name", "-of", "json", path
        ), timeoutSec = 15)
        if (r.exitCode == 0 && r.stdout.isNotBlank()) {
            val m = Pattern.compile("\"codec_name\"\\s*:\\s*\"([^\"]+)\"").matcher(r.stdout)
            if (m.find()) return m.group(1).lowercase()
        }
        return "unknown"
    }

    private fun buildVideoCommand(
        src: String,
        dst: String,
        hw: HardwareInfo,
        settings: AppSettings,
        useHw: Boolean
    ): Pair<List<String>, String> {
        val vid = settings.video
        val eng = settings.engine
        val codec = vid.codec
        val quality = vid.quality
        val resolution = vid.resolution
        val fps = vid.fps

        val vfFilters = mutableListOf<String>()
        if (resolution != "original") {
            val (w, h) = when (resolution) {
                "4k" -> Pair(3840, 2160)
                "1080p" -> Pair(1920, 1080)
                "720p" -> Pair(1280, 720)
                "480p" -> Pair(854, 480)
                else -> Pair(0, 0)
            }
            if (w > 0) {
                vfFilters.add("scale=$w:$h:force_original_aspect_ratio=decrease")
            }
        }
        if (fps != "original") {
            vfFilters.add("fps=$fps")
        }

        val audioArgs = listOf("-c:a", "aac", "-b:a", "128k")

        // 1. NVENC
        if (useHw && hw.hasNvenc && (codec == "h265" || codec == "h264")) {
            val enc = if (codec == "h265") "hevc_nvenc" else "h264_nvenc"
            val cmd = mutableListOf("ffmpeg", "-y", "-i", src)
            if (vfFilters.isNotEmpty()) {
                cmd.addAll(listOf("-vf", vfFilters.joinToString(",")))
            }
            cmd.addAll(listOf("-c:v", enc, "-cq", quality.toString(), "-preset", "p4"))
            cmd.addAll(audioArgs)
            cmd.addAll(listOf("-movflags", "+faststart", "-loglevel", "error", "-progress", "pipe:1", dst))
            return Pair(cmd, "NVENC ($enc)")
        }

        // 2. AMF
        if (useHw && hw.hasAmf && (codec == "h265" || codec == "h264")) {
            val enc = if (codec == "h265") "hevc_amf" else "h264_amf"
            val cmd = mutableListOf("ffmpeg", "-y", "-i", src)
            if (vfFilters.isNotEmpty()) {
                cmd.addAll(listOf("-vf", vfFilters.joinToString(",")))
            }
            cmd.addAll(listOf(
                "-c:v", enc, "-quality", "speed", "-rc", "cqp",
                "-qp_i", quality.toString(), "-qp_p", quality.toString()
            ))
            cmd.addAll(audioArgs)
            cmd.addAll(listOf("-movflags", "+faststart", "-loglevel", "error", "-progress", "pipe:1", dst))
            return Pair(cmd, "AMF ($enc)")
        }

        // 3. Apple VideoToolbox
        if (useHw && hw.hasVideoToolbox && (codec == "h265" || codec == "h264")) {
            val enc = if (codec == "h265") "hevc_videotoolbox" else "h264_videotoolbox"
            val cmd = mutableListOf("ffmpeg", "-y", "-i", src)
            if (vfFilters.isNotEmpty()) {
                cmd.addAll(listOf("-vf", vfFilters.joinToString(",")))
            }
            cmd.addAll(listOf("-c:v", enc, "-q:v", quality.toString()))
            cmd.addAll(audioArgs)
            cmd.addAll(listOf("-movflags", "+faststart", "-loglevel", "error", "-progress", "pipe:1", dst))
            return Pair(cmd, "VideoToolbox ($enc)")
        }

        // 4. VAAPI
        if (useHw && hw.hasVaapi && (codec == "h265" || codec == "h264")) {
            val enc = if (codec == "h265") "hevc_vaapi" else "h264_vaapi"
            val allVf = vfFilters.toMutableList()
            allVf.add("format=nv12")
            allVf.add("hwupload")
            val vfStr = allVf.joinToString(",")
            val asyncDepth = eng.gpuAsyncDepth

            val cmd = mutableListOf(
                "ffmpeg", "-y",
                "-vaapi_device", hw.vaapiDevice,
                "-i", src,
                "-vf", vfStr,
                "-c:v", enc,
                "-async_depth", asyncDepth.toString(),
                "-qp", quality.toString()
            )
            cmd.addAll(audioArgs)
            cmd.addAll(listOf("-movflags", "+faststart", "-loglevel", "error", "-progress", "pipe:1", dst))
            return Pair(cmd, "VAAPI ($enc)")
        }

        // 5. QSV
        if (useHw && hw.hasQsv && (codec == "h265" || codec == "h264")) {
            val enc = if (codec == "h265") "hevc_qsv" else "h264_qsv"
            val cmd = mutableListOf("ffmpeg", "-y", "-i", src)
            if (vfFilters.isNotEmpty()) {
                cmd.addAll(listOf("-vf", vfFilters.joinToString(",")))
            }
            cmd.addAll(listOf("-c:v", enc, "-global_quality", quality.toString()))
            cmd.addAll(audioArgs)
            cmd.addAll(listOf("-movflags", "+faststart", "-loglevel", "error", "-progress", "pipe:1", dst))
            return Pair(cmd, "QSV ($enc)")
        }

        // 6. CPU Fallback
        var enc = when (codec) {
            "h265" -> "libx265"
            "h264" -> "libx264"
            "av1" -> "libaom-av1"
            else -> "libx265"
        }

        val available = JvmHardwareDetector.listFfmpegEncoders().toSet()
        var fallbackNote = ""
        if (codec == "h265" && !available.contains("libx265")) {
            if (available.contains("libsvtav1")) {
                enc = "libsvtav1"
                fallbackNote = " (h265 -> SVT-AV1 fallback)"
            } else if (available.contains("libopenh264")) {
                enc = "libopenh264"
                fallbackNote = " (h265 -> OpenH264 fallback)"
            }
        } else if (codec == "av1") {
            if (available.contains("libsvtav1")) {
                enc = "libsvtav1"
            }
        } else if (codec == "h264" && !available.contains("libx264") && available.contains("libopenh264")) {
            enc = "libopenh264"
            fallbackNote = " (h264 -> OpenH264 fallback)"
        }

        val cmd = mutableListOf("ffmpeg", "-y", "-i", src)
        if (vfFilters.isNotEmpty()) {
            cmd.addAll(listOf("-vf", vfFilters.joinToString(",")))
        }

        val threads = eng.cpuThreads
        val threadArgs = listOf("-threads", threads.toString())

        when (enc) {
            "libsvtav1" -> cmd.addAll(listOf("-c:v", enc, "-crf", quality.toString(), "-preset", "8") + threadArgs)
            "libopenh264" -> cmd.addAll(listOf("-c:v", enc, "-b:v", "2M") + threadArgs)
            "libaom-av1" -> cmd.addAll(listOf("-c:v", enc, "-crf", quality.toString(), "-cpu-used", "4") + threadArgs)
            else -> cmd.addAll(listOf("-c:v", enc, "-crf", quality.toString(), "-preset", "fast") + threadArgs)
        }

        cmd.addAll(audioArgs)
        cmd.addAll(listOf("-movflags", "+faststart", "-loglevel", "error", "-progress", "pipe:1", dst))
        return Pair(cmd, "CPU ($enc$fallbackNote)")
    }

    private suspend fun runFfmpegWithProgress(
        cmd: List<String>,
        duration: Double,
        basePct: Float,
        onProgress: (Float) -> Unit,
        isCancelled: () -> Boolean
    ): Pair<Int, String> = withContext(Dispatchers.IO) {
        val pb = ProcessBuilder(cmd)
        pb.environment()["LANG"] = "C"
        val proc = pb.start()

        val stderrLines = ArrayDeque<String>(100)
        val timePattern = Pattern.compile("out_time_ms=(\\d+)")

        val stderrThread = Thread {
            try {
                proc.errorStream.bufferedReader().useLines { lines ->
                    lines.forEach { line ->
                        synchronized(stderrLines) {
                            if (stderrLines.size >= 100) stderrLines.removeFirst()
                            stderrLines.add(line)
                        }
                    }
                }
            } catch (_: Exception) {}
        }
        stderrThread.isDaemon = true
        stderrThread.start()

        val stdoutThread = Thread {
            try {
                proc.inputStream.bufferedReader().useLines { lines ->
                    for (line in lines) {
                        val m = timePattern.matcher(line)
                        if (m.find() && duration > 0) {
                            val curSec = m.group(1).toLongOrNull()?.let { it / 1_000_000.0 } ?: 0.0
                            val pct = minOf(98f, basePct + (curSec / duration * (98.0 - basePct)).toFloat())
                            onProgress(pct)
                        }
                    }
                }
            } catch (_: Exception) {}
        }
        stdoutThread.isDaemon = true
        stdoutThread.start()

        try {
            while (proc.isAlive) {
                if (isCancelled()) {
                    proc.destroyForcibly()
                    break
                }
                delay(80)
            }
            proc.waitFor()
        } finally {
            try { proc.inputStream.close() } catch (_: Exception) {}
            try { proc.errorStream.close() } catch (_: Exception) {}
        }

        try { stdoutThread.join(1000) } catch (_: Exception) {}
        try { stderrThread.join(1000) } catch (_: Exception) {}

        val err = synchronized(stderrLines) { stderrLines.joinToString("\n").trim() }
        Pair(proc.exitValue(), err)
    }

    suspend fun compressVideo(
        task: CompressionTask,
        settings: AppSettings,
        hw: HardwareInfo,
        useHw: Boolean,
        onProgress: (Float) -> Unit,
        isCancelled: () -> Boolean
    ): CompressionResult = withContext(Dispatchers.IO) {
        val srcFile = File(task.path)
        if (!srcFile.exists()) {
            return@withContext CompressionResult(false, task.origSize, "", "Input file does not exist")
        }

        onProgress(2f)
        if (isCancelled()) return@withContext CompressionResult(false, task.origSize, "", "Cancelled")

        // Skip HEVC check
        if (settings.video.skipHevc) {
            val codec = getVideoCodec(task.path)
            if (codec == "hevc" || codec == "h265" || codec == "av1") {
                onProgress(100f)
                return@withContext CompressionResult(
                    success = true,
                    newSize = task.origSize,
                    encoderUsed = "Skipped (already $codec)",
                    skipped = true
                )
            }
        }

        if (isCancelled()) return@withContext CompressionResult(false, task.origSize, "", "Cancelled")

        val duration = getVideoDuration(task.path)
        onProgress(5f)

        val targetDir = when (settings.engine.outputMode) {
            "custom" -> File(settings.engine.outputDir.ifBlank { srcFile.parent })
            else -> srcFile.parentFile ?: File(".")
        }
        targetDir.mkdirs()

        val destFile = if (settings.engine.outputMode == "alongside") {
            val baseName = srcFile.nameWithoutExtension
            File(targetDir, "${baseName}_compressed.mp4")
        } else {
            File(targetDir, "${srcFile.nameWithoutExtension}.mp4")
        }

        val tmpFile = File(targetDir, ".tmp_mc_${task.id}_${srcFile.nameWithoutExtension}.mp4")

        try {
            var (cmd, label) = buildVideoCommand(task.path, tmpFile.absolutePath, hw, settings, useHw)
            var (exitCode, errOut) = runFfmpegWithProgress(cmd, duration, 5f, onProgress, isCancelled)

            if (isCancelled()) {
                tmpFile.delete()
                return@withContext CompressionResult(false, task.origSize, "", "Cancelled")
            }

            // Fallback to CPU if GPU failed
            if (exitCode != 0 && useHw) {
                tmpFile.delete()
                val (cpuCmd, _) = buildVideoCommand(task.path, tmpFile.absolutePath, hw, settings, useHw = false)
                label = "CPU (GPU fallback)"
                val (cpuExit, cpuErr) = runFfmpegWithProgress(cpuCmd, duration, 5f, onProgress, isCancelled)
                exitCode = cpuExit
                errOut = cpuErr
            }

            if (isCancelled()) {
                tmpFile.delete()
                return@withContext CompressionResult(false, task.origSize, "", "Cancelled")
            }

            if (exitCode != 0 || !tmpFile.exists()) {
                val meaningful = errOut.lines().filter { l ->
                    val ll = l.lowercase()
                    ll.contains("error") || ll.contains("failed") || ll.contains("cannot") || ll.contains("invalid")
                }.takeLast(5)
                val detail = if (meaningful.isNotEmpty()) meaningful.joinToString("\n") else errOut.takeLast(300)
                return@withContext CompressionResult(false, task.origSize, label, "FFmpeg error ($exitCode):\n$detail")
            }

            val newSize = tmpFile.length()
            val shouldReplace = (newSize < task.origSize) || (task.origSize == 0L)

            if (shouldReplace) {
                if (settings.engine.outputMode == "inplace" && destFile.absolutePath != srcFile.absolutePath) {
                    srcFile.delete()
                }
                Files.move(tmpFile.toPath(), destFile.toPath(), StandardCopyOption.REPLACE_EXISTING)
                onProgress(100f)
                return@withContext CompressionResult(true, newSize, label)
            } else {
                tmpFile.delete()
                onProgress(100f)
                return@withContext CompressionResult(true, task.origSize, "$label (Kept original - size was smaller)")
            }
        } catch (e: Exception) {
            tmpFile.delete()
            return@withContext CompressionResult(false, task.origSize, "", "${e::class.simpleName}: ${e.message}")
        }
    }

    suspend fun compressImage(
        task: CompressionTask,
        settings: AppSettings,
        onProgress: (Float) -> Unit,
        isCancelled: () -> Boolean
    ): CompressionResult = withContext(Dispatchers.IO) {
        val srcFile = File(task.path)
        if (!srcFile.exists()) {
            return@withContext CompressionResult(false, task.origSize, "", "File does not exist")
        }

        onProgress(5f)
        if (isCancelled()) return@withContext CompressionResult(false, task.origSize, "", "Cancelled")

        val targetDir = when (settings.engine.outputMode) {
            "custom" -> File(settings.engine.outputDir.ifBlank { srcFile.parent })
            else -> srcFile.parentFile ?: File(".")
        }
        targetDir.mkdirs()

        val ext = srcFile.extension.lowercase()
        val outExt = when (ext) {
            "heic", "heif", "bmp", "tiff", "tif", "avif" -> "jpg"
            else -> ext
        }

        val destFile = if (settings.engine.outputMode == "alongside") {
            File(targetDir, "${srcFile.nameWithoutExtension}_compressed.$outExt")
        } else {
            File(targetDir, "${srcFile.nameWithoutExtension}.$outExt")
        }

        val tmpFile = File(targetDir, ".tmp_mc_${task.id}_${srcFile.nameWithoutExtension}.$outExt")

        val presetName = settings.image.preset
        val quality = settings.image.quality
        val maxPx = settings.image.resizeMaxPx
        val stripMeta = settings.image.stripMetadata

        onProgress(20f)
        try {
            val cmd = mutableListOf("ffmpeg", "-y", "-i", srcFile.absolutePath)
            val vf = mutableListOf<String>()
            if (maxPx != null && maxPx > 0) {
                vf.add("scale='if(gt(a,1),min($maxPx,iw),-2)':'if(gt(a,1),-2,min($maxPx,ih))'")
            }
            if (vf.isNotEmpty()) {
                cmd.addAll(listOf("-vf", vf.joinToString(",")))
            }
            if (stripMeta) {
                cmd.addAll(listOf("-map_metadata", "-1"))
            }

            when (outExt) {
                "jpg", "jpeg" -> {
                    // quality 1-100 -> qscale 2-31 (lower is better in ffmpeg mjpeg)
                    val qscale = maxOf(2, minOf(31, ((100 - quality) * 29 / 100) + 2))
                    cmd.addAll(listOf("-q:v", qscale.toString()))
                }
                "webp" -> {
                    cmd.addAll(listOf("-quality", quality.toString()))
                }
                "png" -> {
                    val comp = if (presetName == "lossless") 1 else 6
                    cmd.addAll(listOf("-compression_level", comp.toString()))
                }
                else -> {
                    cmd.addAll(listOf("-q:v", "3"))
                }
            }

            cmd.addAll(listOf("-loglevel", "error", tmpFile.absolutePath))
            onProgress(60f)

            val r = JvmHardwareDetector.runCommand(cmd, timeoutSec = 30)
            onProgress(85f)

            if (isCancelled()) {
                tmpFile.delete()
                return@withContext CompressionResult(false, task.origSize, "", "Cancelled")
            }

            if (r.exitCode != 0 || !tmpFile.exists()) {
                return@withContext CompressionResult(false, task.origSize, "", "Image encode error: ${r.stderr}")
            }

            val newSize = tmpFile.length()
            val shouldReplace = (newSize < task.origSize) || (destFile.absolutePath != srcFile.absolutePath) || (task.origSize == 0L)

            if (shouldReplace) {
                if (settings.engine.outputMode == "inplace" && destFile.absolutePath != srcFile.absolutePath) {
                    srcFile.delete()
                }
                Files.move(tmpFile.toPath(), destFile.toPath(), StandardCopyOption.REPLACE_EXISTING)
                onProgress(100f)
                return@withContext CompressionResult(true, newSize, "FFmpeg ($presetName)")
            } else {
                tmpFile.delete()
                onProgress(100f)
                return@withContext CompressionResult(true, task.origSize, "FFmpeg ($presetName - Kept original)")
            }
        } catch (e: Exception) {
            tmpFile.delete()
            return@withContext CompressionResult(false, task.origSize, "", "${e::class.simpleName}: ${e.message}")
        }
    }
}
