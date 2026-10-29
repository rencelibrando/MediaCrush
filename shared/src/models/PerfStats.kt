package org.example.project.models

data class PerfStats(
    val cpuPercent: Float = 0f,
    val ramUsedGb: Double = 0.0,
    val ramTotalGb: Double = 0.0,
    val gpuPercent: Float = -1f,
    val vramUsedGb: Double = 0.0,
    val activeGpuWorkers: Int = 0,
    val activeCpuWorkers: Int = 0,
    val queuedTasks: Int = 0
)

data class SessionStats(
    val totalFiles: Int = 0,
    val processedFiles: Int = 0,
    val workingFiles: Int = 0,
    val doneFiles: Int = 0,
    val errorFiles: Int = 0,
    val skippedFiles: Int = 0,
    val origBytesSum: Long = 0L,
    val newBytesSum: Long = 0L,
    val savedBytesSum: Long = 0L,
    val savedPctOverall: Float = 0f,
    val startTimeMs: Long = 0L,
    val filesPerMinute: Double = 0.0
)
