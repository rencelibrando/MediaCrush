"""Live performance monitor with unified card layout and optimized polling."""
from __future__ import annotations
import os
import threading
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QObject


class _PollSignals(QObject):
    update = Signal(float, float, float, float, float)


class _PerfPoller:
    def __init__(self, interval_ms: int = 2000):
        self._interval = interval_ms / 1000.0
        self.signals = _PollSignals()
        self._stop = threading.Event()
        self._alive = True
        self._last_win_gpu_check = 0.0
        self._cached_win_gpu = (-1.0, 0.0)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._alive = False
        self._stop.set()

    def _run(self):
        try:
            import psutil
            psutil.cpu_percent(interval=None)
        except ImportError:
            pass

        while not self._stop.wait(self._interval):
            if not self._alive:
                break
            try:
                cpu = self._cpu()
                ram_u, ram_t = self._ram()
                gpu, vram = self._gpu()
                if self._alive:
                    self.signals.update.emit(cpu, ram_u, ram_t, gpu, vram)
            except RuntimeError:
                break
            except Exception:
                pass

    @staticmethod
    def _cpu() -> float:
        try:
            import psutil
            return psutil.cpu_percent(interval=None)
        except ImportError:
            return 0.0

    @staticmethod
    def _ram() -> tuple[float, float]:
        try:
            import psutil
            m = psutil.virtual_memory()
            return m.used / 1e9, m.total / 1e9
        except ImportError:
            return 0.0, 0.0

    def _gpu(self) -> tuple[float, float]:
        try:
            import pynvml
            pynvml.nvmlInit()
            h = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = float(pynvml.nvmlDeviceGetUtilizationRates(h).gpu)
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            return util, mem.used / 1e9
        except Exception:
            pass

        if os.name == "nt":
            now = time.time()
            if now - self._last_win_gpu_check >= 6.0:
                self._last_win_gpu_check = now
                self._cached_win_gpu = self._windows_gpu()
            return self._cached_win_gpu

        return -1.0, 0.0

    @staticmethod
    def _windows_gpu() -> tuple[float, float]:
        try:
            from utils.process import hidden_subprocess_kwargs
            import subprocess
            cmd = [
                "powershell", "-NoProfile", "-Command",
                "$s = (Get-Counter '\\GPU Engine(*)\\Utilization Percentage' -ErrorAction SilentlyContinue).CounterSamples; "
                "$u = ($s | Measure-Object -Property CookedValue -Sum).Sum; "
                "$m = (Get-Counter '\\GPU Adapter Memory(*)\\Dedicated Usage' -ErrorAction SilentlyContinue).CounterSamples | Measure-Object -Property CookedValue -Sum; "
                "Write-Output ('{0}|{1}' -f [math]::Round([math]::Min(100, [double]$u), 1), [math]::Round(([double]$m.Sum / 1GB), 2))"
            ]
            r = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3,
                **hidden_subprocess_kwargs()
            )
            if r.returncode == 0 and "|" in r.stdout:
                parts = r.stdout.strip().split("|")
                return float(parts[0] or 0), float(parts[1] or 0)
        except Exception:
            pass
        return -1.0, 0.0


class PerfWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = "dark"
        self._poller = _PerfPoller(interval_ms=2000)
        self._build_ui()
        self.set_theme("dark")
        self._poller.signals.update.connect(self._on_update)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # Single unified card container
        self._card = QFrame()
        self._card.setObjectName("card")
        card_lay = QVBoxLayout(self._card)
        card_lay.setContentsMargins(12, 10, 12, 10)
        card_lay.setSpacing(8)

        self._title = QLabel("SYSTEM MONITOR")
        card_lay.addWidget(self._title)

        # Resource meters
        self._cpu_row, self._cpu_bar, self._cpu_val, self._cpu_lbl = self._create_bar_row("CPU")
        self._ram_row, self._ram_bar, self._ram_val, self._ram_lbl = self._create_bar_row("RAM")
        self._gpu_row, self._gpu_bar, self._gpu_val, self._gpu_lbl = self._create_bar_row("GPU")

        card_lay.addWidget(self._cpu_row)
        card_lay.addWidget(self._ram_row)
        card_lay.addWidget(self._gpu_row)

        # Divider
        self._div = QFrame()
        self._div.setFrameShape(QFrame.HLine)
        self._div.setFixedHeight(1)
        card_lay.addWidget(self._div)

        # Workers summary row with colored dots
        w_row = QHBoxLayout()
        w_row.setContentsMargins(0, 0, 0, 0)
        w_row.setSpacing(10)

        self._dot_gpu, self._lbl_gpu, self._val_gpu = self._create_worker_indicator("GPU", "#10b981")
        self._dot_cpu, self._lbl_cpu, self._val_cpu = self._create_worker_indicator("CPU", "#3b82f6")
        self._dot_que, self._lbl_que, self._val_que = self._create_worker_indicator("Queued", "#71717a")

        for dot, lbl, val in [
            (self._dot_gpu, self._lbl_gpu, self._val_gpu),
            (self._dot_cpu, self._lbl_cpu, self._val_cpu),
            (self._dot_que, self._lbl_que, self._val_que),
        ]:
            item_box = QHBoxLayout()
            item_box.setSpacing(4)
            item_box.addWidget(dot)
            item_box.addWidget(lbl)
            item_box.addWidget(val)
            w_row.addLayout(item_box)

        w_row.addStretch()
        card_lay.addLayout(w_row)
        root.addWidget(self._card)

    def _create_bar_row(self, name: str) -> tuple[QWidget, QProgressBar, QLabel, QLabel]:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        lbl = QLabel(name)
        lbl.setFixedWidth(28)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setFixedHeight(4)
        bar.setTextVisible(False)
        bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        val = QLabel("-")
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val.setFixedWidth(64)

        lay.addWidget(lbl)
        lay.addWidget(bar)
        lay.addWidget(val)
        return w, bar, val, lbl

    def _create_worker_indicator(self, label: str, dot_color: str) -> tuple[QLabel, QLabel, QLabel]:
        dot = QLabel()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet(
            f"background: {dot_color}; border-radius: 3px; "
            "min-width: 6px; max-width: 6px; min-height: 6px; max-height: 6px; border: none;"
        )
        lbl = QLabel(label)
        val = QLabel("0")
        return dot, lbl, val

    def set_theme(self, theme: str):
        self._theme = theme
        is_dark = theme == "dark"

        title_color = "#a1a1aa" if is_dark else "#64748b"
        lbl_color = "#71717a" if is_dark else "#475569"
        val_color = "#f4f4f5" if is_dark else "#0f172a"
        div_color = "#38383e" if is_dark else "#e2e8f0"
        bar_bg = "#242427" if is_dark else "#e2e8f0"

        self._title.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {title_color}; "
            "letter-spacing: 0.8px; background: transparent; border: none;"
        )
        self._div.setStyleSheet(f"background: {div_color}; border: none;")

        for lbl in (self._cpu_lbl, self._ram_lbl, self._gpu_lbl, self._lbl_gpu, self._lbl_cpu, self._lbl_que):
            lbl.setStyleSheet(
                f"font-size: 10px; font-weight: 600; color: {lbl_color}; "
                "background: transparent; border: none;"
            )

        for val in (self._cpu_val, self._ram_val, self._gpu_val):
            val.setStyleSheet(
                f"font-size: 11px; font-weight: 600; color: {val_color}; "
                "background: transparent; border: none;"
            )

        for val, color in [
            (self._val_gpu, "#10b981" if is_dark else "#059669"),
            (self._val_cpu, "#3b82f6" if is_dark else "#2563eb"),
            (self._val_que, "#a1a1aa" if is_dark else "#64748b"),
        ]:
            val.setStyleSheet(
                f"font-size: 11px; font-weight: 700; color: {color}; "
                "background: transparent; border: none;"
            )

        for bar, color in [
            (self._cpu_bar, "#3b82f6" if is_dark else "#2563eb"),
            (self._ram_bar, "#38bdf8" if is_dark else "#0284c7"),
            (self._gpu_bar, "#10b981" if is_dark else "#059669"),
        ]:
            bar.setStyleSheet(
                f"QProgressBar {{ background: {bar_bg}; border: none; border-radius: 2px; }}"
                f"QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}"
            )

    def update_workers(self, gpu: int, cpu: int, queued: int):
        self._val_gpu.setText(str(gpu))
        self._val_cpu.setText(str(cpu))
        self._val_que.setText(str(queued))

    def _on_update(self, cpu: float, ram_u: float, ram_t: float,
                   gpu: float, vram: float):
        self._cpu_bar.setValue(int(cpu))
        self._cpu_val.setText(f"{cpu:.0f}%")

        if ram_t > 0:
            ram_pct = ram_u / ram_t * 100
            self._ram_bar.setValue(int(ram_pct))
            self._ram_val.setText(f"{ram_u:.1f}/{ram_t:.0f}GB")
        else:
            self._ram_val.setText("N/A")

        if gpu >= 0:
            self._gpu_bar.setValue(int(gpu))
            vram_txt = f" {vram:.1f}G" if vram > 0 else ""
            self._gpu_val.setText(f"{gpu:.0f}%{vram_txt}")
        else:
            self._gpu_bar.setValue(0)
            self._gpu_val.setText("Active")

    def closeEvent(self, event):
        self._poller.stop()
        super().closeEvent(event)

    def __del__(self):
        try:
            self._poller.stop()
        except Exception:
            pass
