package org.example.project.platform

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Build
import android.provider.OpenableColumns
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import org.example.project.models.*
import java.io.Closeable
import java.io.File
import java.io.FileOutputStream
import java.io.InputStream
import java.io.OutputStream

actual object PlatformBridge {
    private var appContext: Context? = null
    private var pickFilesHandler: ((List<String>, (List<String>) -> Unit) -> Unit)? = null
    private var pickFolderHandler: (((String?) -> Unit) -> Unit)? = null

    private val json = Json {
        ignoreUnknownKeys = true
        prettyPrint = true
        encodeDefaults = true
    }

    fun init(
        context: Context,
        onPickFiles: ((List<String>, (List<String>) -> Unit) -> Unit)? = null,
        onPickFolder: (((String?) -> Unit) -> Unit)? = null
    ) {
        appContext = context.applicationContext
        pickFilesHandler = onPickFiles
        pickFolderHandler = onPickFolder
    }

    fun copyUriToAppStorage(context: Context, uri: Uri): String? {
        return try {
            var displayName = "file_${System.currentTimeMillis()}"
            context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                val nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if (nameIndex != -1 && cursor.moveToFirst()) {
                    val n = cursor.getString(nameIndex)
                    if (!n.isNullOrBlank()) displayName = n
                }
            }
            val cacheDir = File(context.cacheDir, "picked_media")
            cacheDir.mkdirs()
            val targetFile = File(cacheDir, displayName)
            val inputStream: InputStream? = context.contentResolver.openInputStream(uri)
            if (inputStream != null) {
                inputStream.use { input ->
                    val outputStream: OutputStream = FileOutputStream(targetFile)
                    outputStream.use { output ->
                        input.copyTo(output)
                    }
                }
                targetFile.absolutePath
            } else {
                null
            }
        } catch (_: Exception) {
            null
        }
    }

    fun resolveTreeUri(context: Context, uri: Uri): String? {
        return uri.path
    }

    actual fun getHardwareInfo(force: Boolean): HardwareInfo {
        val totalMemMb = Runtime.getRuntime().totalMemory() / (1024 * 1024)
        val threads = Runtime.getRuntime().availableProcessors()
        return HardwareInfo(
            osPlatform = "android",
            cpuThreads = threads,
            cpuName = "${Build.MANUFACTURER} ${Build.HARDWARE}",
            gpuName = Build.MODEL,
            diagLog = listOf(
                "Android Release: ${Build.VERSION.RELEASE}",
                "API Level: ${Build.VERSION.SDK_INT}",
                "Device: ${Build.MANUFACTURER} ${Build.MODEL}",
                "Architecture: ${Build.SUPPORTED_ABIS.firstOrNull() ?: "unknown"}",
                "Available Memory: ${totalMemMb}MB"
            )
        )
    }

    actual fun getLivePerfStats(): PerfStats {
        val runtime = Runtime.getRuntime()
        val totalGb = runtime.totalMemory() / (1024.0 * 1024.0 * 1024.0)
        val usedGb = (runtime.totalMemory() - runtime.freeMemory()) / (1024.0 * 1024.0 * 1024.0)
        return PerfStats(
            cpuPercent = 0f,
            ramUsedGb = usedGb,
            ramTotalGb = totalGb
        )
    }

    actual fun runDiagnostics(force: Boolean): DiagnosticsResult {
        val runtime = Runtime.getRuntime()
        val totalGb = runtime.totalMemory() / (1024.0 * 1024.0 * 1024.0)
        return DiagnosticsResult(
            ffmpegVersion = "Not bundled (using Android Native Bitmap)",
            ffmpegOk = false,
            ffprobeVersion = "Not bundled",
            ffprobeOk = false,
            hwInfo = getHardwareInfo(force),
            supportedEncoders = mapOf("AndroidBitmap (JPEG, PNG, WEBP)" to true),
            osName = "Android ${Build.VERSION.RELEASE}",
            osArch = Build.SUPPORTED_ABIS.firstOrNull() ?: "unknown",
            jvmVersion = "ART ${System.getProperty("java.vm.version") ?: ""}",
            totalRamGb = totalGb
        )
    }

    private val settingsFile: File?
        get() {
            val ctx = appContext ?: return null
            return File(ctx.filesDir, "settings.json")
        }

    actual fun loadSettings(): AppSettings {
        return try {
            val f = settingsFile
            if (f != null && f.exists()) {
                json.decodeFromString<AppSettings>(f.readText())
            } else {
                AppSettings()
            }
        } catch (_: Exception) {
            AppSettings()
        }
    }

    actual fun saveSettings(settings: AppSettings) {
        try {
            val f = settingsFile ?: return
            f.parentFile?.mkdirs()
            f.writeText(json.encodeToString(AppSettings.serializer(), settings))
        } catch (_: Exception) {}
    }

    actual suspend fun pickFiles(title: String, extensions: List<String>): List<String> = withContext(Dispatchers.Main) {
        val handler = pickFilesHandler ?: return@withContext emptyList()
        val deferred = CompletableDeferred<List<String>>()
        handler(extensions) { paths ->
            deferred.complete(paths)
        }
        deferred.await()
    }

    actual suspend fun pickFolder(title: String): String? = withContext(Dispatchers.Main) {
        val handler = pickFolderHandler ?: return@withContext null
        val deferred = CompletableDeferred<String?>()
        handler { path ->
            deferred.complete(path)
        }
        deferred.await()
    }

    actual suspend fun scanFolder(folderPath: String, extensions: Set<String>): List<String> = withContext(Dispatchers.IO) {
        val dir = File(folderPath)
        if (!dir.exists() || !dir.isDirectory) return@withContext emptyList()
        dir.walkTopDown()
            .filter { it.isFile && extensions.contains("." + it.extension.lowercase()) }
            .map { it.absolutePath }
            .toList()
    }

    actual suspend fun compressItem(
        task: CompressionTask,
        settings: AppSettings,
        useHw: Boolean,
        hwInfo: HardwareInfo,
        onProgress: (Float) -> Unit,
        isCancelled: () -> Boolean
    ): CompressionResult = withContext(Dispatchers.IO) {
        if (task.mediaType == MediaType.IMAGE) {
            compressImage(task, settings, onProgress, isCancelled)
        } else {
            compressVideo(task, settings, onProgress, isCancelled)
        }
    }

    private fun compressImage(
        task: CompressionTask,
        settings: AppSettings,
        onProgress: (Float) -> Unit,
        isCancelled: () -> Boolean
    ): CompressionResult {
        val srcFile = File(task.path)
        if (!srcFile.exists()) {
            return CompressionResult(success = false, newSize = task.origSize, encoderUsed = "Error", errorMsg = "Source file not found")
        }

        onProgress(10f)
        val bitmap = BitmapFactory.decodeFile(srcFile.absolutePath)
            ?: return CompressionResult(success = false, newSize = task.origSize, encoderUsed = "Error", errorMsg = "Unable to decode image bitmap")

        if (isCancelled()) {
            return CompressionResult(success = false, newSize = task.origSize, encoderUsed = "Cancelled", errorMsg = "Cancelled by user")
        }

        onProgress(35f)
        val maxPx = settings.image.resizeMaxPx
        val scaled = if (maxPx != null && maxPx > 0 && (bitmap.width > maxPx || bitmap.height > maxPx)) {
            val ratio = minOf(maxPx.toFloat() / bitmap.width, maxPx.toFloat() / bitmap.height)
            val newW = (bitmap.width * ratio).toInt().coerceAtLeast(1)
            val newH = (bitmap.height * ratio).toInt().coerceAtLeast(1)
            Bitmap.createScaledBitmap(bitmap, newW, newH, true)
        } else {
            bitmap
        }

        if (isCancelled()) {
            return CompressionResult(success = false, newSize = task.origSize, encoderUsed = "Cancelled", errorMsg = "Cancelled by user")
        }

        onProgress(65f)
        val ext = srcFile.extension.lowercase()
        val outExt = when (ext) {
            "heic", "heif", "bmp", "tiff", "tif", "avif" -> "jpg"
            else -> ext
        }

        val targetDir = when (settings.engine.outputMode) {
            "custom" -> File(settings.engine.outputDir.ifBlank { srcFile.parent ?: "." })
            else -> srcFile.parentFile ?: File(".")
        }
        targetDir.mkdirs()

        val destFile = if (settings.engine.outputMode == "alongside") {
            File(targetDir, "${srcFile.nameWithoutExtension}_compressed.$outExt")
        } else {
            File(targetDir, "${srcFile.nameWithoutExtension}.$outExt")
        }
        val tmpFile = File(targetDir, ".tmp_mc_${task.id}_${srcFile.nameWithoutExtension}.$outExt")

        val quality = settings.image.quality.coerceIn(1, 100)
        val (format, extLabel) = when (outExt) {
            "png" -> Pair(Bitmap.CompressFormat.PNG, "PNG")
            "webp" -> {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    Pair(Bitmap.CompressFormat.WEBP_LOSSY, "WEBP")
                } else {
                    @Suppress("DEPRECATION")
                    Pair(Bitmap.CompressFormat.WEBP, "WEBP")
                }
            }
            else -> Pair(Bitmap.CompressFormat.JPEG, "JPEG")
        }

        val outputStream: OutputStream = FileOutputStream(tmpFile)
        outputStream.use { fos ->
            scaled.compress(format, quality, fos)
        }

        val newSize = tmpFile.length()
        if (newSize < task.origSize || destFile.absolutePath != srcFile.absolutePath || task.origSize == 0L) {
            tmpFile.renameTo(destFile)
        } else {
            tmpFile.delete()
        }

        onProgress(100f)
        return CompressionResult(
            success = true,
            newSize = if (destFile.exists()) destFile.length() else newSize,
            encoderUsed = "Android Native Bitmap ($extLabel q$quality)"
        )
    }

    private fun compressVideo(
        task: CompressionTask,
        settings: AppSettings,
        onProgress: (Float) -> Unit,
        isCancelled: () -> Boolean
    ): CompressionResult {
        val srcFile = File(task.path)
        if (!srcFile.exists()) {
            return CompressionResult(success = false, newSize = task.origSize, encoderUsed = "Error", errorMsg = "Source video not found")
        }

        val targetDir = when (settings.engine.outputMode) {
            "custom" -> File(settings.engine.outputDir.ifBlank { srcFile.parent ?: "." })
            else -> srcFile.parentFile ?: File(".")
        }
        targetDir.mkdirs()

        val destFile = if (settings.engine.outputMode == "alongside") {
            File(targetDir, "${srcFile.nameWithoutExtension}_compressed.mp4")
        } else {
            File(targetDir, "${srcFile.nameWithoutExtension}.mp4")
        }

        onProgress(50f)
        srcFile.copyTo(destFile, overwrite = true)
        onProgress(100f)

        return CompressionResult(
            success = true,
            newSize = destFile.length(),
            encoderUsed = "Android Storage Copy"
        )
    }
}
