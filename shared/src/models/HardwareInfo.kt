package org.example.project.models

import kotlinx.serialization.Serializable

@Serializable
data class HardwareInfo(
    val hasVaapi: Boolean = false,
    val vaapiDevice: String = "/dev/dri/renderD128",
    val hasNvenc: Boolean = false,
    val hasAmf: Boolean = false,
    val hasQsv: Boolean = false,
    val hasD3d11va: Boolean = false,
    val hasVideoToolbox: Boolean = false,
    val cpuThreads: Int = 4,
    val cpuName: String = "Unknown CPU",
    val gpuName: String = "Unknown GPU",
    val osPlatform: String = "unknown",
    val diagLog: List<String> = emptyList()
) {
    val hasAnyGpu: Boolean
        get() = hasNvenc || hasAmf || hasVaapi || hasQsv || hasVideoToolbox

    val bestVideoEncoder: String
        get() = when {
            hasNvenc -> "nvenc"
            hasAmf -> "amf"
            hasVaapi -> "vaapi"
            hasQsv -> "qsv"
            hasVideoToolbox -> "videotoolbox"
            else -> "cpu"
        }

    val cleanGpuName: String
        get() {
            if (gpuName.isEmpty() || gpuName == "Unknown GPU") return ""
            return when {
                gpuName.contains("Radeon", ignoreCase = true) || gpuName.contains("AMD", ignoreCase = true) -> "AMD Radeon"
                gpuName.contains("NVIDIA", ignoreCase = true) || gpuName.contains("GeForce", ignoreCase = true) -> "NVIDIA GPU"
                gpuName.contains("Intel", ignoreCase = true) -> "Intel Graphics"
                gpuName.contains("Apple", ignoreCase = true) -> "Apple Silicon GPU"
                gpuName.contains("[") && gpuName.contains("]") -> {
                    val sub = gpuName.substringAfter("[").substringBefore("]")
                    sub.take(25)
                }
                else -> gpuName.take(25)
            }
        }

    val hwSummary: String
        get() {
            val parts = mutableListOf<String>()
            if (hasNvenc) parts.add("NVIDIA NVENC")
            if (hasAmf) parts.add("AMD AMF")
            if (hasVideoToolbox) parts.add("Apple VideoToolbox")
            if (hasVaapi) {
                val devName = vaapiDevice.substringAfterLast('/')
                parts.add("VAAPI ($devName)")
            }
            if (hasQsv) parts.add("Intel QSV")
            if (hasD3d11va) parts.add("DirectX (D3D11VA)")

            return when {
                parts.isNotEmpty() -> parts.joinToString(" + ")
                cleanGpuName.isNotEmpty() -> "CPU ($cleanGpuName)"
                else -> "CPU only"
            }
        }

    val encoderList: List<String>
        get() {
            val enc = mutableListOf<String>()
            if (hasNvenc) enc.addAll(listOf("hevc_nvenc", "h264_nvenc"))
            if (hasAmf) enc.addAll(listOf("hevc_amf", "h264_amf"))
            if (hasVideoToolbox) enc.addAll(listOf("hevc_videotoolbox", "h264_videotoolbox"))
            if (hasVaapi) enc.addAll(listOf("hevc_vaapi", "h264_vaapi"))
            if (hasQsv) enc.addAll(listOf("hevc_qsv", "h264_qsv"))
            enc.addAll(listOf("libx265", "libx264"))
            return enc
        }
}
