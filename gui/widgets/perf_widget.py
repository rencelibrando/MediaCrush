"""Live performance monitor — CPU, RAM, GPU, active workers."""
from __future__ import annotations
import threading
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject


# ── Poller runs in a background thread ───────────────────────────────────────

class _PollSignals(QObject):
    update = Signal(float, float, float, float, float)
    # cpu_pct, ram_used_gb, ram_total_gb, gpu_pct, vram_gb


class _PerfPoller:
    def __init__(self, interval_ms: int = 2000):
        self._interval = interval_ms / 1000.0
        self.signals   = _PollSignals()
        self._stop     = threading.Event()
        self._alive    = True        # guarded flag
        self._thread   = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._alive = False
        self._stop.set()

    def _run(self):
        import time
        # Warm up psutil cpu_percent
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
                if self._alive:          # check again after blocking calls
                    self.signals.update.emit(cpu, ram_u, ram_t, gpu, vram)
            except RuntimeError:
                break                    # Qt object destroyed — exit quietly
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

    @staticmethod
    def _gpu() -> tuple[float, float]:
        try:
            import pynvml
            pynvml.nvmlInit()
            h    = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = float(pynvml.nvmlDeviceGetUtilizationRates(h).gpu)
            mem  = pynvml.nvmlDeviceGetMemoryInfo(h)
            return util, mem.used / 1e9
        except Exception:
            pass
        return -1.0, 0.0  # -1 = GPU present but no util metric


# ── UI helpers ────────────────────────────────────────────────────────────────

def _meter(label: str, color: str) -> tuple[QFrame, QProgressBar, QLabel]:
    """Returns (container, bar, value_label)."""
    frame = QFrame()
    frame.setObjectName("card")
    lay   = QVBoxLayout(frame)
    lay.setContentsMargins(10, 8, 10, 8)
    lay.setSpacing(4)

    top = QHBoxLayout()
    top.setContentsMargins(0, 0, 0, 0)
    lbl_w = QLabel(label)
    lbl_w.setStyleSheet(
        "font-size: 10px; font-weight: 700; color: #475569; "
        "letter-spacing: 0.8px; background: transparent; border: none;"
    )
    val_w = QLabel("—")
    val_w.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    val_w.setStyleSheet(
        f"font-size: 11px; font-weight: 700; color: {color}; "
        "background: transparent; border: none;"
    )
    top.addWidget(lbl_w)
    top.addStretch()
    top.addWidget(val_w)
    lay.addLayout(top)

    bar = QProgressBar()
    bar.setRange(0, 100)
    bar.setValue(0)
    bar.setFixedHeight(4)
    bar.setTextVisible(False)
    bar.setStyleSheet(
        "QProgressBar { background: #1c1c30; border: none; border-radius: 2px; }"
        f"QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}"
    )
    lay.addWidget(bar)
    return frame, bar, val_w


def _worker_row(label: str, color: str) -> tuple[QWidget, QLabel]:
    w   = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 2, 0, 2)
    lay.setSpacing(6)

    dot = QLabel()
    dot.setFixedSize(8, 8)
    dot.setStyleSheet(
        f"background: {color}; border-radius: 4px; min-width: 8px; "
        f"max-width: 8px; min-height: 8px; max-height: 8px; border: none;"
    )
    lbl = QLabel(label)
    lbl.setStyleSheet(
        "font-size: 11px; color: #64748b; background: transparent; border: none;"
    )
    val = QLabel("0")
    val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    val.setStyleSheet(
        f"font-size: 12px; font-weight: 700; color: {color}; "
        "background: transparent; border: none;"
    )
    lay.addWidget(dot)
    lay.addWidget(lbl)
    lay.addStretch()
    lay.addWidget(val)
    return w, val


# ── Main widget ───────────────────────────────────────────────────────────────

class PerfWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._poller = _PerfPoller(interval_ms=1500)
        self._build_ui()
        self._poller.signals.update.connect(self._on_update)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(0, 0, 0, 0)

        title = QLabel("PERFORMANCE")
        title.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #334155; "
            "letter-spacing: 1.2px; background: transparent; border: none;"
        )
        root.addWidget(title)

        # CPU
        cpu_f, self._cpu_bar, self._cpu_val = _meter("CPU", "#a78bfa")
        root.addWidget(cpu_f)

        # RAM
        ram_f, self._ram_bar, self._ram_val = _meter("RAM", "#38bdf8")
        root.addWidget(ram_f)

        # GPU
        gpu_f, self._gpu_bar, self._gpu_val = _meter("GPU", "#10b981")
        root.addWidget(gpu_f)
        self._gpu_frame = gpu_f

        # Worker counts
        worker_frame = QFrame()
        worker_frame.setObjectName("card")
        wlay = QVBoxLayout(worker_frame)
        wlay.setContentsMargins(10, 8, 10, 8)
        wlay.setSpacing(2)

        wt = QLabel("WORKERS")
        wt.setStyleSheet(
            "font-size: 9px; font-weight: 700; color: #334155; "
            "letter-spacing: 1px; background: transparent; border: none;"
        )
        wlay.addWidget(wt)

        gpu_row, self._w_gpu = _worker_row("GPU active", "#10b981")
        cpu_row, self._w_cpu = _worker_row("CPU active", "#a78bfa")
        que_row, self._w_que = _worker_row("Queued",     "#475569")
        for row in (gpu_row, cpu_row, que_row):
            wlay.addWidget(row)
        root.addWidget(worker_frame)

    # ── Public API ────────────────────────────────────────────────────────────

    def update_workers(self, gpu: int, cpu: int, queued: int):
        self._w_gpu.setText(str(gpu))
        self._w_cpu.setText(str(cpu))
        self._w_que.setText(str(queued))

    # ── Slots ─────────────────────────────────────────────────────────────────

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
            vram_txt = f"  {vram:.1f}GB VRAM" if vram > 0 else ""
            self._gpu_val.setText(f"{gpu:.0f}%{vram_txt}")
        else:
            # GPU present via VAAPI but no utilization metric
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
