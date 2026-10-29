"""Diagnostics dialog with hardware and encoder status reporting."""
from __future__ import annotations
import threading
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFrame, QScrollArea, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont


def _status_row(label: str, value: str = "Checking...",
                ok: bool | None = None) -> tuple[QWidget, QLabel, QLabel, QLabel]:
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(12, 5, 12, 5)
    lay.setSpacing(10)

    dot = QLabel()
    dot.setFixedSize(8, 8)
    color = "#52525b" if ok is None else ("#10b981" if ok else "#ef4444")
    dot.setStyleSheet(
        f"background: {color}; border-radius: 4px; "
        "min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px; border: none;"
    )
    lbl_w = QLabel(label)
    lbl_w.setFixedWidth(180)
    lbl_w.setObjectName("diag_label")

    val_w = QLabel(value)
    val_w.setObjectName("diag_val")
    val_w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    lay.addWidget(dot)
    lay.addWidget(lbl_w)
    lay.addWidget(val_w)
    return row, dot, val_w, lbl_w


def _update_dot(dot: QLabel, ok: bool):
    color = "#10b981" if ok else "#ef4444"
    dot.setStyleSheet(
        f"background: {color}; border-radius: 4px; "
        "min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px; border: none;"
    )


def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("section_title")
    lbl.setStyleSheet("padding: 10px 12px 4px 12px;")
    return lbl


class _DiagSignals(QObject):
    done = Signal(dict)


class _DiagRunner:
    def __init__(self):
        self.signals = _DiagSignals()
        self._force = False

    def run_async(self, force: bool = False):
        self._force = force
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        from core.hardware import (
            detect_hardware, get_ffmpeg_version, list_ffmpeg_encoders
        )
        from utils.process import hidden_subprocess_kwargs
        import subprocess
        import os

        results: dict = {}
        results["ffmpeg_version"] = get_ffmpeg_version()
        results["ffmpeg_ok"] = results["ffmpeg_version"] != "not found"

        try:
            r = subprocess.run(
                ["ffprobe", "-version"], capture_output=True, text=True, timeout=5,
                **hidden_subprocess_kwargs()
            )
            v = r.stdout.splitlines()[0].replace("ffprobe version", "").strip().split()[0] \
                if r.returncode == 0 else "not found"
        except Exception:
            v = "not found"
        results["ffprobe_version"] = v
        results["ffprobe_ok"] = v != "not found"

        hw = detect_hardware(force=self._force)
        results["hw"] = hw
        results["hw_ok"] = hw.has_any_gpu

        all_enc = set(list_ffmpeg_encoders())
        enc_check = [
            "hevc_vaapi", "h264_vaapi",
            "hevc_nvenc", "h264_nvenc",
            "hevc_amf",   "h264_amf",
            "hevc_qsv",   "h264_qsv",
            "libx265",    "libx264",
            "libaom-av1",
        ]
        results["encoders"] = {e: (e in all_enc) for e in enc_check}

        dri_dir = "/dev/dri"
        dri_devs = []
        if os.path.isdir(dri_dir):
            dri_devs = sorted(os.listdir(dri_dir))
        results["dri_devices"] = dri_devs

        try:
            import psutil
            results["psutil_version"] = psutil.__version__
            results["psutil_ok"] = True
        except ImportError:
            results["psutil_version"] = "not installed"
            results["psutil_ok"] = False

        self.signals.done.emit(results)


class DiagnosticsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MediaCrush - Diagnostics")
        self.setMinimumSize(600, 680)
        self._runner = _DiagRunner()
        self._runner.signals.done.connect(self._on_done)
        self._rows: dict[str, tuple[QLabel, QLabel]] = {}
        self._build_ui()
        self._run_diag()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        hdr = QFrame()
        hdr.setObjectName("panel")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(16, 12, 16, 12)

        title = QLabel("System Diagnostics")
        title.setObjectName("app_title")

        self._status_lbl = QLabel("Running checks...")
        self._status_lbl.setObjectName("status_label")

        btn_rerun = QPushButton("Re-run")
        btn_rerun.setObjectName("btn_secondary")
        btn_rerun.setFixedHeight(28)
        btn_rerun.clicked.connect(lambda: self._run_diag(force=True))

        hdr_lay.addWidget(title)
        hdr_lay.addStretch()
        hdr_lay.addWidget(self._status_lbl)
        hdr_lay.addWidget(btn_rerun)
        root.addWidget(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        self._body_lay = QVBoxLayout(body)
        self._body_lay.setSpacing(0)
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

        self._body_lay.addWidget(_section_title("SOFTWARE"))
        self._add_check("ffmpeg", "FFmpeg")
        self._add_check("ffprobe", "FFprobe")
        self._add_check("psutil", "psutil (monitoring)")

        self._body_lay.addWidget(_section_title("GPU ACCELERATION"))
        self._add_check("gpu_overall", "Any GPU encoder")
        self._add_check("vaapi", "VAAPI (AMD/Intel)")
        self._add_check("nvenc", "NVIDIA NVENC")
        self._add_check("amf", "AMD AMF")
        self._add_check("qsv", "Intel Quick Sync")

        self._body_lay.addWidget(_section_title("FFMPEG ENCODERS"))
        for enc in [
            "hevc_vaapi", "h264_vaapi",
            "hevc_nvenc", "h264_nvenc",
            "hevc_amf",   "h264_amf",
            "hevc_qsv",   "h264_qsv",
            "libx265",    "libx264",
            "libaom-av1",
        ]:
            self._add_check(f"enc_{enc}", enc)

        self._body_lay.addWidget(_section_title("DRI DEVICES"))
        self._dri_lbl = QLabel("Detecting...")
        self._dri_lbl.setObjectName("status_label")
        self._dri_lbl.setStyleSheet("padding: 4px 12px 8px 32px;")
        self._body_lay.addWidget(self._dri_lbl)

        self._body_lay.addWidget(_section_title("DETECTION LOG"))
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFixedHeight(150)
        self._log_text.setFont(QFont("Cascadia Code", 10))
        self._log_text.setStyleSheet("margin: 0 12px 12px 12px;")
        self._body_lay.addWidget(self._log_text)
        self._body_lay.addStretch()

        footer = QHBoxLayout()
        footer.setContentsMargins(16, 8, 16, 12)
        footer.addStretch()
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        root.addLayout(footer)

    def _add_check(self, key: str, label: str):
        row, dot, val, _ = _status_row(label)
        self._rows[key] = (dot, val)
        self._body_lay.addWidget(row)

    def _run_diag(self, force: bool = False):
        self._status_lbl.setText("Running checks...")
        for dot, val in self._rows.values():
            dot.setStyleSheet(
                "background: #52525b; border-radius: 4px; "
                "min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px; border: none;"
            )
            val.setText("Checking...")
        self._log_text.clear()
        self._runner.run_async(force=force)

    def _on_done(self, r: dict):
        hw = r.get("hw")

        def _set(key: str, ok: bool, text: str):
            if key not in self._rows:
                return
            dot, val = self._rows[key]
            _update_dot(dot, ok)
            val.setText(text)

        _set("ffmpeg", r.get("ffmpeg_ok", False), r.get("ffmpeg_version", "N/A"))
        _set("ffprobe", r.get("ffprobe_ok", False), r.get("ffprobe_version", "N/A"))
        _set("psutil", r.get("psutil_ok", False), r.get("psutil_version", "N/A"))

        if hw:
            _set("gpu_overall", hw.has_any_gpu, hw.hw_summary)
            _set("vaapi", hw.has_vaapi, hw.vaapi_device if hw.has_vaapi else "not available")
            _set("nvenc", hw.has_nvenc, "Available" if hw.has_nvenc else "not available")
            _set("amf", getattr(hw, "has_amf", False), "Available" if getattr(hw, "has_amf", False) else "not available")
            _set("qsv", hw.has_qsv, "Available" if hw.has_qsv else "not available")

            for entry in hw.diag_log:
                self._log_text.append(entry)

        encs = r.get("encoders", {})
        for enc, ok in encs.items():
            _set(f"enc_{enc}", ok, "Available" if ok else "not built")

        dri = r.get("dri_devices", [])
        self._dri_lbl.setText("  ".join(dri) if dri else "No /dev/dri devices found")

        all_ok = r.get("ffmpeg_ok", False) and r.get("hw_ok", False)
        self._status_lbl.setText(
            "All systems ready" if all_ok else "Some checks failed - see below"
        )
