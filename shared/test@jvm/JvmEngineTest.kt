package org.example.project

import kotlin.test.Test
import kotlin.test.assertNotNull
import kotlin.test.assertTrue
import org.example.project.engine.CompressionEngine
import org.example.project.models.AppSettings
import org.example.project.platform.JvmHardwareDetector
import org.example.project.platform.JvmSettingsStore
import org.example.project.platform.PlatformBridge

class JvmEngineTest {

    @Test
    fun testHardwareDetectionExecution() {
        val hw = JvmHardwareDetector.detectHardware(force = true)
        assertNotNull(hw)
        assertTrue(hw.cpuThreads > 0, "CPU threads must be > 0")
        assertNotNull(hw.cpuName)
        assertNotNull(hw.osPlatform)
        println("Detected HW: ${hw.hwSummary}")
        println("Diag log: ${hw.diagLog.joinToString("; ")}")
    }

    @Test
    fun testLiveMetrics() {
        val cpu = JvmHardwareDetector.getCpuUsage()
        val (ramUsed, ramTotal) = JvmHardwareDetector.getRamUsage()
        val (gpu, vram) = JvmHardwareDetector.getGpuUsage()

        println("Live Metrics: CPU=$cpu%, RAM=$ramUsed/$ramTotal GB, GPU=$gpu%, VRAM=$vram GB")
        assertTrue(cpu >= 0f)
        assertTrue(ramTotal >= 0.0)
    }

    @Test
    fun testSettingsPersistence() {
        val initial = JvmSettingsStore.loadSettings()
        assertNotNull(initial)

        val modified = initial.copy(
            video = initial.video.copy(quality = 25),
            image = initial.image.copy(preset = "high")
        )
        JvmSettingsStore.saveSettings(modified)

        val reloaded = JvmSettingsStore.loadSettings()
        assertTrue(reloaded.video.quality == 25)
        assertTrue(reloaded.image.preset == "high")

        // Restore original
        JvmSettingsStore.saveSettings(initial)
    }

    @Test
    fun testCompressionEngineLifecycle() {
        val engine = CompressionEngine()
        assertNotNull(engine.tasks.value)
        assertNotNull(engine.logs.value)
        assertNotNull(engine.statusMessage.value)

        engine.log("Test log entry")
        assertTrue(engine.logs.value.isNotEmpty())
        assertTrue(engine.logs.value.last().contains("Test log entry"))

        engine.clearLogs()
        assertTrue(engine.logs.value.isEmpty())
    }
}
