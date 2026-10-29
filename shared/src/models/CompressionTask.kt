package org.example.project.models

import kotlin.math.abs
import kotlin.math.max

data class CompressionTask(
    val id: String,
    val path: String,
    val fileName: String,
    val outputDir: String? = null,
    val status: TaskStatus = TaskStatus.QUEUED,
    val mediaType: MediaType = MediaType.UNKNOWN,
    val progress: Float = 0.0f,
    val origSize: Long = 0L,
    val newSize: Long = 0L,
    val errorMsg: String = "",
    val startTime: Long = 0L,
    val endTime: Long = 0L,
    val encoderUsed: String = ""
) {
    val savedBytes: Long
        get() = max(0L, origSize - newSize)

    val savedPct: Float
        get() = if (origSize <= 0L || newSize <= 0L || newSize >= origSize) 0.0f
                else ((1.0 - (newSize.toDouble() / origSize.toDouble())) * 100.0).toFloat()

    val durationSec: Double
        get() = if (endTime > startTime) (endTime - startTime) / 1000.0 else 0.0

    companion object {
        fun formatSize(bytes: Long): String {
            if (bytes <= 0) return "0 B"
            var b = bytes.toDouble()
            val units = arrayOf("B", "KB", "MB", "GB", "TB")
            for (u in units) {
                if (abs(b) < 1024.0 || u == "TB") {
                    return if (u == "B") "${b.toLong()} $u" else "${(b * 10.0).toLong() / 10.0} $u"
                }
                b /= 1024.0
            }
            return "$bytes B"
        }
    }
}
