package org.example.project.models

import kotlinx.serialization.Serializable

@Serializable
data class ImageSettings(
    val preset: String = "balanced",
    val quality: Int = 85,
    val stripMetadata: Boolean = false,
    val resizeMaxPx: Int? = null
)

@Serializable
data class VideoSettings(
    val codec: String = "h265",
    val quality: Int = 28,
    val resolution: String = "original",
    val fps: String = "original",
    val skipHevc: Boolean = true
)

@Serializable
data class EngineSettings(
    val perfMode: String = "max",
    val gpuWorkers: Int = 4,
    val cpuWorkers: Int = 4,
    val cpuThreads: Int = 0,
    val gpuAsyncDepth: Int = 4,
    val hybridDistribution: Boolean = true,
    val outputMode: String = "inplace", // inplace | alongside | custom
    val outputDir: String = ""
)

@Serializable
data class UiSettings(
    val theme: String = "dark", // dark | light
    val lastDir: String = ""
)

@Serializable
data class AppSettings(
    val image: ImageSettings = ImageSettings(),
    val video: VideoSettings = VideoSettings(),
    val engine: EngineSettings = EngineSettings(),
    val ui: UiSettings = UiSettings()
) {
    companion object {
        val PRESET_QUALITIES = mapOf(
            "lossless" to 100,
            "high" to 92,
            "balanced" to 85,
            "small" to 70,
            "tiny" to 55
        )

        fun defaultQualityForPreset(preset: String): Int {
            return PRESET_QUALITIES[preset] ?: 85
        }
    }
}
