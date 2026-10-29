package org.example.project.engine

import org.example.project.models.*
import org.example.project.platform.PlatformBridge
import java.io.File
import java.time.LocalTime
import java.time.format.DateTimeFormatter
import java.util.UUID
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

class CompressionEngine(
    private val scope: CoroutineScope = CoroutineScope(Dispatchers.Default + SupervisorJob())
) {
    private val _tasks = MutableStateFlow<List<CompressionTask>>(emptyList())
    val tasks: StateFlow<List<CompressionTask>> = _tasks.asStateFlow()

    private val _logs = MutableStateFlow<List<String>>(emptyList())
    val logs: StateFlow<List<String>> = _logs.asStateFlow()

    private val _sessionStats = MutableStateFlow(SessionStats())
    val sessionStats: StateFlow<SessionStats> = _sessionStats.asStateFlow()

    private val _perfStats = MutableStateFlow(PerfStats())
    val perfStats: StateFlow<PerfStats> = _perfStats.asStateFlow()

    private val _statusMessage = MutableStateFlow("Ready")
    val statusMessage: StateFlow<String> = _statusMessage.asStateFlow()

    private val _overallProgress = MutableStateFlow(0f)
    val overallProgress: StateFlow<Float> = _overallProgress.asStateFlow()

    private val _isRunning = MutableStateFlow(false)
    val isRunning: StateFlow<Boolean> = _isRunning.asStateFlow()

    private val _isPaused = MutableStateFlow(false)
    val isPaused: StateFlow<Boolean> = _isPaused.asStateFlow()

    private val _hardwareInfo = MutableStateFlow(HardwareInfo())
    val hardwareInfo: StateFlow<HardwareInfo> = _hardwareInfo.asStateFlow()

    private val _settings = MutableStateFlow(AppSettings())
    val settings: StateFlow<AppSettings> = _settings.asStateFlow()

    private var cancelFlag = false
    private var pauseFlag = false
    private val pauseMutex = Mutex()
    private val timeFormatter = DateTimeFormatter.ofPattern("HH:mm:ss")

    private var activeGpuCount = 0
    private var activeCpuCount = 0
    private val counterMutex = Mutex()

    init {
        // Load initial settings
        scope.launch(Dispatchers.IO) {
            val loaded = PlatformBridge.loadSettings()
            _settings.value = loaded
            detectHardwareAsync()
        }
        // Start background polling for perf stats
        startPerfMonitor()
    }

    fun updateSettings(newSettings: AppSettings) {
        _settings.value = newSettings
        scope.launch(Dispatchers.IO) {
            PlatformBridge.saveSettings(newSettings)
        }
    }

    fun detectHardwareAsync(force: Boolean = false) {
        scope.launch(Dispatchers.IO) {
            log("Detecting hardware encoders & system capabilities...")
            val hw = PlatformBridge.getHardwareInfo(force)
            _hardwareInfo.value = hw
            log("Hardware detected: ${hw.hwSummary} | CPU threads: ${hw.cpuThreads}")
        }
    }

    fun log(msg: String) {
        val now = LocalTime.now().format(timeFormatter)
        val formatted = "[$now] $msg"
        val current = _logs.value.toMutableList()
        current.add(formatted)
        if (current.size > 5000) {
            current.removeAt(0)
        }
        _logs.value = current
        _statusMessage.value = msg.takeLast(100)
    }

    fun clearLogs() {
        _logs.value = emptyList()
    }

    fun addTasks(filePaths: List<String>) {
        val existingPaths = _tasks.value.map { it.path }.toSet()
        val newItems = mutableListOf<CompressionTask>()

        for (fp in filePaths) {
            if (!existingPaths.contains(fp)) {
                val file = File(fp)
                if (file.exists() && file.isFile) {
                    val mediaType = MediaType.fromPath(fp)
                    val id = UUID.randomUUID().toString().take(8)
                    val task = CompressionTask(
                        id = id,
                        path = fp,
                        fileName = file.name,
                        outputDir = if (_settings.value.engine.outputMode == "custom") _settings.value.engine.outputDir else null,
                        status = TaskStatus.QUEUED,
                        mediaType = mediaType,
                        origSize = file.length()
                    )
                    newItems.add(task)
                }
            }
        }

        if (newItems.isNotEmpty()) {
            _tasks.value = _tasks.value + newItems
            log("Added ${newItems.size} file(s) to queue")
            updateSessionStats()
        }
    }

    fun clearQueue() {
        if (_isRunning.value) {
            cancel()
        }
        _tasks.value = emptyList()
        _overallProgress.value = 0f
        _statusMessage.value = "Queue cleared"
        log("Queue cleared")
        updateSessionStats()
    }

    fun cancelTask(taskId: String) {
        _tasks.value = _tasks.value.map {
            if (it.id == taskId && (it.status == TaskStatus.QUEUED || it.status == TaskStatus.PAUSED)) {
                it.copy(status = TaskStatus.CANCELLED)
            } else it
        }
        updateSessionStats()
    }

    fun start() {
        if (_isRunning.value) return
        val pending = _tasks.value.filter { it.status == TaskStatus.QUEUED || it.status == TaskStatus.PAUSED }
        if (pending.isEmpty()) {
            _statusMessage.value = "No queued tasks - add files first"
            return
        }

        cancelFlag = false
        pauseFlag = false
        _isRunning.value = true
        _isPaused.value = false
        _statusMessage.value = "Compressing..."

        val s = _settings.value
        val hw = _hardwareInfo.value

        var gpuWorkers = s.engine.gpuWorkers
        var cpuWorkers = s.engine.cpuWorkers

        if (!hw.hasAnyGpu) {
            gpuWorkers = 0
            cpuWorkers = if (cpuWorkers > 0) cpuWorkers else hw.cpuThreads
        }

        val totalPending = pending.size
        val hybrid = s.engine.hybridDistribution
        if (hybrid && gpuWorkers > 0 && cpuWorkers > 0 && totalPending > 1) {
            gpuWorkers = maxOf(1, minOf(gpuWorkers, (totalPending + 1) / 2))
            cpuWorkers = maxOf(1, minOf(cpuWorkers, totalPending - gpuWorkers))
        } else {
            gpuWorkers = minOf(gpuWorkers, totalPending)
            cpuWorkers = minOf(cpuWorkers, maxOf(0, totalPending - gpuWorkers))
        }

        log("Starting parallel workers ($gpuWorkers GPU, $cpuWorkers CPU) on $totalPending tasks")
        startProcessing(pending, gpuWorkers, cpuWorkers)
    }

    private fun startProcessing(pending: List<CompressionTask>, gpuWorkers: Int, cpuWorkers: Int) {
        scope.launch(Dispatchers.Default) {
            val taskChannel = Channel<CompressionTask>(Channel.UNLIMITED)
            pending.forEach { taskChannel.trySend(it) }
            taskChannel.close()

            val workerJobs = mutableListOf<Job>()

            // GPU Workers
            repeat(gpuWorkers) {
                workerJobs.add(launch {
                    for (task in taskChannel) {
                        if (cancelFlag) break
                        checkPause()
                        if (cancelFlag) break
                        counterMutex.withLock { activeGpuCount++ }
                        try {
                            processTask(task, useHw = true)
                        } finally {
                            counterMutex.withLock { activeGpuCount = maxOf(0, activeGpuCount - 1) }
                        }
                    }
                })
            }

            // CPU Workers
            repeat(cpuWorkers) {
                workerJobs.add(launch {
                    for (task in taskChannel) {
                        if (cancelFlag) break
                        checkPause()
                        if (cancelFlag) break
                        counterMutex.withLock { activeCpuCount++ }
                        try {
                            processTask(task, useHw = false)
                        } finally {
                            counterMutex.withLock { activeCpuCount = maxOf(0, activeCpuCount - 1) }
                        }
                    }
                })
            }

            workerJobs.joinAll()

            _isRunning.value = false
            _isPaused.value = false
            updateOverallProgress()
            updateSessionStats()

            val tasksList = _tasks.value
            val doneCount = tasksList.count { it.status == TaskStatus.DONE }
            val errorCount = tasksList.count { it.status == TaskStatus.ERROR }

            if (cancelFlag) {
                _statusMessage.value = "Compression cancelled"
                log("Compression cancelled.")
            } else if (errorCount > 0 && doneCount == 0) {
                _statusMessage.value = "Finished with $errorCount error(s) - check Logs tab"
                log("Finished with $errorCount error(s).")
            } else if (errorCount > 0) {
                _statusMessage.value = "Finished: $doneCount succeeded, $errorCount error(s)"
                log("Finished: $doneCount succeeded, $errorCount error(s).")
            } else {
                _statusMessage.value = "All tasks completed successfully"
                _overallProgress.value = 100f
                log("All tasks completed successfully.")
            }
        }
    }

    private suspend fun checkPause() {
        while (pauseFlag && !cancelFlag) {
            delay(150)
        }
    }

    private suspend fun processTask(task: CompressionTask, useHw: Boolean) {
        val currentStatus = _tasks.value.find { it.id == task.id }?.status
        if (currentStatus == TaskStatus.CANCELLED || cancelFlag) {
            updateTask(task.id) { it.copy(status = TaskStatus.CANCELLED) }
            return
        }

        checkPause()
        if (cancelFlag) return

        val startTime = System.currentTimeMillis()
        val encoderType = if (useHw) "GPU" else "CPU"
        log("[$encoderType] Starting ${task.fileName}")

        updateTask(task.id) {
            it.copy(
                status = TaskStatus.RUNNING,
                startTime = startTime,
                progress = 2f
            )
        }

        val result = PlatformBridge.compressItem(
            task = task,
            settings = _settings.value,
            useHw = useHw,
            hwInfo = _hardwareInfo.value,
            onProgress = { pct ->
                updateTask(task.id) { it.copy(progress = pct) }
                updateOverallProgress()
            },
            isCancelled = { cancelFlag || _tasks.value.find { it.id == task.id }?.status == TaskStatus.CANCELLED }
        )

        val endTime = System.currentTimeMillis()
        if (cancelFlag || _tasks.value.find { it.id == task.id }?.status == TaskStatus.CANCELLED) {
            updateTask(task.id) {
                it.copy(
                    status = TaskStatus.CANCELLED,
                    endTime = endTime,
                    progress = 100f
                )
            }
            log("[CANCELLED] ${task.fileName}")
        } else if (result.skipped) {
            updateTask(task.id) {
                it.copy(
                    status = TaskStatus.SKIPPED,
                    newSize = it.origSize,
                    encoderUsed = result.encoderUsed,
                    endTime = endTime,
                    progress = 100f
                )
            }
            log("[SKIP] ${task.fileName} - ${result.encoderUsed}")
        } else if (result.success) {
            updateTask(task.id) {
                it.copy(
                    status = TaskStatus.DONE,
                    newSize = result.newSize,
                    encoderUsed = result.encoderUsed,
                    endTime = endTime,
                    progress = 100f
                )
            }
            val origStr = CompressionTask.formatSize(task.origSize)
            val newStr = CompressionTask.formatSize(result.newSize)
            val savedPct = if (task.origSize > 0) ((1.0 - result.newSize.toDouble() / task.origSize.toDouble()) * 100.0) else 0.0
            log("[OK] ${task.fileName} | $origStr -> $newStr (${(savedPct * 10).toLong() / 10.0}% saved) [${result.encoderUsed}]")
        } else {
            val err = result.errorMsg ?: "Compression failed"
            updateTask(task.id) {
                it.copy(
                    status = TaskStatus.ERROR,
                    errorMsg = err,
                    endTime = endTime,
                    progress = 100f
                )
            }
            val firstLine = err.lines().firstOrNull() ?: "Unknown error"
            log("[ERR] ${task.fileName}: $firstLine")
        }

        updateOverallProgress()
        updateSessionStats()
    }

    private fun updateTask(taskId: String, block: (CompressionTask) -> CompressionTask) {
        _tasks.value = _tasks.value.map {
            if (it.id == taskId) block(it) else it
        }
    }

    private fun updateOverallProgress() {
        val list = _tasks.value
        if (list.isEmpty()) {
            _overallProgress.value = 0f
            return
        }
        val sum = list.sumOf { it.progress.toDouble() }
        _overallProgress.value = (sum / list.size.toDouble()).toFloat()
    }

    private fun updateSessionStats() {
        val list = _tasks.value
        val total = list.size
        val done = list.count { it.status == TaskStatus.DONE }
        val err = list.count { it.status == TaskStatus.ERROR }
        val skip = list.count { it.status == TaskStatus.SKIPPED }
        val running = list.count { it.status == TaskStatus.RUNNING }
        val processed = done + err + skip

        var origSum = 0L
        var newSum = 0L
        var savedSum = 0L

        for (t in list) {
            if (t.status == TaskStatus.DONE || t.status == TaskStatus.SKIPPED) {
                origSum += t.origSize
                newSum += t.newSize
                savedSum += t.savedBytes
            }
        }

        val pct = if (origSum > 0) ((savedSum.toDouble() / origSum.toDouble()) * 100.0).toFloat() else 0f

        _sessionStats.value = _sessionStats.value.copy(
            totalFiles = total,
            processedFiles = processed,
            workingFiles = running,
            doneFiles = done,
            errorFiles = err,
            skippedFiles = skip,
            origBytesSum = origSum,
            newBytesSum = newSum,
            savedBytesSum = savedSum,
            savedPctOverall = pct
        )
    }

    fun pause() {
        if (!_isRunning.value) return
        pauseFlag = true
        _isPaused.value = true
        _statusMessage.value = "Paused"
        log("Paused.")
    }

    fun resume() {
        if (!_isRunning.value) return
        pauseFlag = false
        _isPaused.value = false
        _statusMessage.value = "Compressing..."
        log("Resumed.")
    }

    fun cancel() {
        cancelFlag = true
        pauseFlag = false
        _isRunning.value = false
        _isPaused.value = false
        _statusMessage.value = "Cancelling..."
        _tasks.value = _tasks.value.map {
            if (it.status == TaskStatus.QUEUED || it.status == TaskStatus.PAUSED) {
                it.copy(status = TaskStatus.CANCELLED)
            } else it
        }
        log("Cancelling ongoing tasks...")
    }

    private fun startPerfMonitor() {
        scope.launch(Dispatchers.IO) {
            while (isActive) {
                try {
                    val p = PlatformBridge.getLivePerfStats()
                    val queued = _tasks.value.count { it.status == TaskStatus.QUEUED }
                    _perfStats.value = p.copy(
                        activeGpuWorkers = activeGpuCount,
                        activeCpuWorkers = activeCpuCount,
                        queuedTasks = queued
                    )
                } catch (_: Exception) {}
                delay(1500)
            }
        }
    }
}
