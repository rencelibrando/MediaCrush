"""Compression engine — true parallel GPU + CPU worker pools."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import threading
import time
import queue as qmod
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QObject, Signal

from .task import CompressionTask, TaskStatus, MediaType
from .hardware import HardwareInfo, detect_hardware
from .image_compressor import compress_image
from .video_compressor import compress_video


class EngineSignals(QObject):
    """Thread-safe Qt signals for UI updates."""
    task_progress = Signal(str, float)          # task_id, pct
    task_status   = Signal(str, str)            # task_id, status_str
    task_done     = Signal(str, int, int, str)  # task_id, orig, new, encoder
    task_error    = Signal(str, str)            # task_id, msg
    log_message   = Signal(str)
    all_done      = Signal()
    hw_detected   = Signal(str)
    stats_update  = Signal(int, int, int)       # active_gpu, active_cpu, queued


class CompressionEngine:
    def __init__(self):
        self.signals   = EngineSignals()
        self.hw: Optional[HardwareInfo] = None
        self._tasks:   list[CompressionTask] = []
        self._lock     = threading.Lock()
        self._paused   = threading.Event()
        self._paused.set()        # set = not paused
        self._cancelled = threading.Event()
        self._running  = False
        self._settings: dict = {}

        # Live counters (read from UI thread safely)
        self._active_gpu = 0
        self._active_cpu = 0
        self._counter_lock = threading.Lock()

    # ── Public API ───────────────────────────────────────────────────────────

    def detect_hardware_async(self):
        def _detect():
            self._log("Detecting hardware…")
            self.hw = detect_hardware()
            self._log(
                f"Hardware: {self.hw.hw_summary} | "
                f"CPU threads: {self.hw.cpu_threads}"
            )
            self.signals.hw_detected.emit(self.hw.hw_summary)
        threading.Thread(target=_detect, daemon=True).start()

    def add_task(self, task: CompressionTask):
        with self._lock:
            self._tasks.append(task)
        self.signals.task_status.emit(task.id, TaskStatus.QUEUED.value)

    def add_tasks(self, tasks: list[CompressionTask]):
        for t in tasks:
            self.add_task(t)

    def start(self, settings: dict):
        if self._running:
            return
        self._cancelled.clear()
        self._paused.set()
        self._running  = True
        self._settings = settings

        if self.hw is None:
            self.hw = detect_hardware()

        gpu_workers = settings.get("gpu_workers", 4)
        cpu_workers = settings.get("cpu_workers", 8)

        # If no GPU available, redirect all workers to CPU
        if not self.hw.has_any_gpu:
            gpu_workers = 0
            cpu_workers = settings.get("cpu_workers", self.hw.cpu_threads)

        threading.Thread(
            target=self._run_all,
            args=(gpu_workers, cpu_workers),
            daemon=True
        ).start()

    def pause(self):
        self._paused.clear()
        self._log("Paused.")

    def resume(self):
        self._paused.set()
        self._log("Resumed.")

    def cancel(self):
        self._cancelled.set()
        self._paused.set()   # unblock if paused
        # Immediately mark all still-queued tasks as cancelled
        with self._lock:
            for t in self._tasks:
                if t.status == TaskStatus.QUEUED:
                    t.status = TaskStatus.CANCELLED
                    self.signals.task_status.emit(t.id, TaskStatus.CANCELLED.value)
        self._log("Cancelling…")

    def cancel_task(self, task_id: str):
        with self._lock:
            for t in self._tasks:
                if t.id == task_id and t.status == TaskStatus.QUEUED:
                    t.status = TaskStatus.CANCELLED
                    self.signals.task_status.emit(task_id, TaskStatus.CANCELLED.value)
                    break

    def clear_queue(self):
        with self._lock:
            for t in self._tasks:
                if t.status == TaskStatus.QUEUED:
                    t.status = TaskStatus.CANCELLED
        self._log("Queue cleared.")

    def get_tasks(self) -> list[CompressionTask]:
        with self._lock:
            return list(self._tasks)

    @property
    def active_gpu_workers(self) -> int:
        with self._counter_lock:
            return self._active_gpu

    @property
    def active_cpu_workers(self) -> int:
        with self._counter_lock:
            return self._active_cpu

    # ── Internal ─────────────────────────────────────────────────────────────

    def _log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.signals.log_message.emit(f"[{ts}] {msg}")

    def _emit_stats(self, queued: int):
        with self._counter_lock:
            g, c = self._active_gpu, self._active_cpu
        self.signals.stats_update.emit(g, c, queued)

    def _run_all(self, gpu_workers: int, cpu_workers: int):
        """
        True parallel execution:
        - GPU workers pull from shared queue, encode with GPU.
        - CPU workers pull from shared queue, encode with CPU.
        - Both pools run simultaneously — no blocking between them.
        """
        with self._lock:
            pending = [t for t in self._tasks if t.status == TaskStatus.QUEUED]

        if not pending:
            self._running = False
            self.signals.all_done.emit()
            return

        # Cap workers to number of actual tasks — no idle threads
        n = len(pending)
        gpu_workers = min(gpu_workers, n)
        cpu_workers = min(cpu_workers, max(0, n - gpu_workers))
        total_workers = max(1, gpu_workers + cpu_workers)

        # Shared queue fed to both worker pools
        task_q: qmod.Queue[Optional[CompressionTask]] = qmod.Queue()
        for t in pending:
            task_q.put(t)

        self._log(
            f"Starting {total_workers} workers "
            f"({gpu_workers} GPU, {cpu_workers} CPU) "
            f"on {len(pending)} tasks"
        )

        def gpu_worker():
            while not self._cancelled.is_set():
                self._paused.wait()
                try:
                    task = task_q.get_nowait()
                except qmod.Empty:
                    break
                if task is None:
                    break
                with self._counter_lock:
                    self._active_gpu += 1
                try:
                    if task.status != TaskStatus.QUEUED:
                        continue
                    self._run_task(task, use_hw=True)
                finally:
                    with self._counter_lock:
                        self._active_gpu = max(0, self._active_gpu - 1)
                    task_q.task_done()
                    self._emit_stats(task_q.qsize())

        def cpu_worker():
            while not self._cancelled.is_set():
                self._paused.wait()
                try:
                    task = task_q.get_nowait()
                except qmod.Empty:
                    break
                if task is None:
                    break
                with self._counter_lock:
                    self._active_cpu += 1
                try:
                    if task.status != TaskStatus.QUEUED:
                        continue
                    self._run_task(task, use_hw=False)
                finally:
                    with self._counter_lock:
                        self._active_cpu = max(0, self._active_cpu - 1)
                    task_q.task_done()
                    self._emit_stats(task_q.qsize())

        futures = []
        with ThreadPoolExecutor(max_workers=total_workers or 1) as ex:
            for _ in range(gpu_workers):
                futures.append(ex.submit(gpu_worker))
            for _ in range(cpu_workers):
                futures.append(ex.submit(cpu_worker))
            # Wait for all
            for f in futures:
                try:
                    f.result()
                except Exception as e:
                    self._log(f"Worker error: {e}")

        self._running = False
        self._log("All tasks completed.")
        self.signals.all_done.emit()

    def _run_task(self, task: CompressionTask, use_hw: bool):
        if self._cancelled.is_set() or task.status == TaskStatus.CANCELLED:
            task.status = TaskStatus.CANCELLED
            self.signals.task_status.emit(task.id, TaskStatus.CANCELLED.value)
            return

        self._paused.wait()

        settings = {**self._settings, "use_hw": use_hw}

        def _prog(pct: float):
            task.progress = pct
            self.signals.task_progress.emit(task.id, pct)

        encoder_hint = "GPU" if use_hw else "CPU"
        self._log(f"[{encoder_hint}] Starting {task.path.name}")
        self.signals.task_status.emit(task.id, TaskStatus.RUNNING.value)

        try:
            if task.media_type == MediaType.IMAGE:
                compress_image(task, settings, _prog, self._cancelled)
            elif task.media_type == MediaType.VIDEO:
                compress_video(task, settings, self.hw, _prog, self._cancelled)
            else:
                task.status   = TaskStatus.SKIPPED
                task.new_size = task.orig_size
                _prog(100.0)

            if task.status == TaskStatus.DONE:
                self._log(
                    f"[OK] {task.path.name} | "
                    f"{CompressionTask.fmt_size(task.orig_size)} → "
                    f"{CompressionTask.fmt_size(task.new_size)} "
                    f"({task.saved_pct:.1f}% saved) [{task.encoder_used}]"
                )
                self.signals.task_done.emit(
                    task.id, task.orig_size, task.new_size, task.encoder_used
                )
            elif task.status == TaskStatus.SKIPPED:
                self._log(f"[SKIP] {task.path.name} — {task.encoder_used}")
                self.signals.task_done.emit(
                    task.id, task.orig_size, task.orig_size, task.encoder_used
                )
            elif task.status == TaskStatus.CANCELLED:
                self._log(f"[CANCELLED] {task.path.name}")
            elif task.status == TaskStatus.ERROR:
                self._log(f"[ERR] {task.path.name}: {task.error_msg}")
                self.signals.task_error.emit(task.id, task.error_msg)

        except Exception as e:
            task.status    = TaskStatus.ERROR
            task.error_msg = str(e)
            self._log(f"[ERR] Unexpected: {task.path.name}: {e}")
            self.signals.task_error.emit(task.id, str(e))

        self.signals.task_status.emit(task.id, task.status.value)
