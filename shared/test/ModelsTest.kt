package org.example.project

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue
import org.example.project.models.*

class ModelsTest {
    @Test
    fun testMediaTypeDetection() {
        assertEquals(MediaType.IMAGE, MediaType.fromPath("photo.jpg"))
        assertEquals(MediaType.IMAGE, MediaType.fromPath("IMAGE.PNG"))
        assertEquals(MediaType.IMAGE, MediaType.fromPath("/path/to/sample.webp"))
        assertEquals(MediaType.VIDEO, MediaType.fromPath("movie.mp4"))
        assertEquals(MediaType.VIDEO, MediaType.fromPath("clip.MKV"))
        assertEquals(MediaType.UNKNOWN, MediaType.fromPath("notes.txt"))
    }

    @Test
    fun testCompressionTaskSavings() {
        val task = CompressionTask(
            id = "test-1",
            path = "/tmp/test.mp4",
            fileName = "test.mp4",
            origSize = 1000L,
            newSize = 400L,
            status = TaskStatus.DONE
        )
        assertEquals(600L, task.savedBytes)
        assertEquals(60.0f, task.savedPct)
        assertEquals("1000 B", CompressionTask.formatSize(1000L))
        assertEquals("1.0 MB", CompressionTask.formatSize(1024L * 1024L))
    }

    @Test
    fun testHardwareInfoProperties() {
        val hw = HardwareInfo(
            hasVaapi = true,
            vaapiDevice = "/dev/dri/renderD128",
            hasNvenc = true,
            cpuThreads = 8,
            cpuName = "AMD Ryzen",
            gpuName = "NVIDIA GeForce RTX"
        )
        assertTrue(hw.hasAnyGpu)
        assertEquals("nvenc", hw.bestVideoEncoder)
        assertTrue(hw.hwSummary.contains("NVENC"))
        assertTrue(hw.hwSummary.contains("VAAPI"))
    }

    @Test
    fun testDefaultSettings() {
        val s = AppSettings()
        assertEquals("balanced", s.image.preset)
        assertEquals(85, s.image.quality)
        assertEquals("h265", s.video.codec)
        assertEquals(28, s.video.quality)
        assertEquals("inplace", s.engine.outputMode)
    }
}
