package org.example.project.models

import kotlinx.serialization.Serializable

@Serializable
data class DiagnosticsResult(
    val ffmpegVersion: String = "not found",
    val ffmpegOk: Boolean = false,
    val ffprobeVersion: String = "not found",
    val ffprobeOk: Boolean = false,
    val hwInfo: HardwareInfo = HardwareInfo(),
    val supportedEncoders: Map<String, Boolean> = emptyMap(),
    val driDevices: List<String> = emptyList(),
    val osName: String = "",
    val osArch: String = "",
    val jvmVersion: String = "",
    val totalRamGb: Double = 0.0
)
