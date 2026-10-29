package org.example.project.models

enum class MediaType(val label: String) {
    IMAGE("image"),
    VIDEO("video"),
    UNKNOWN("unknown");

    companion object {
        val IMAGE_EXTS = setOf(
            ".jpg", ".jpeg", ".png", ".webp", ".avif", ".heic", ".heif",
            ".bmp", ".tiff", ".tif", ".gif"
        )
        val VIDEO_EXTS = setOf(
            ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv",
            ".wmv", ".m4v", ".mpeg", ".mpg"
        )

        fun fromPath(filePath: String): MediaType {
            val idx = filePath.lastIndexOf('.')
            if (idx == -1 || idx == filePath.length - 1) return UNKNOWN
            val ext = filePath.substring(idx).lowercase()
            return when {
                IMAGE_EXTS.contains(ext) -> IMAGE
                VIDEO_EXTS.contains(ext) -> VIDEO
                else -> UNKNOWN
            }
        }
    }
}
