"""Diagnostics dialog — FFmpeg, GPU, encoder status and hardware report."""
from __future__ import annotations
import threading
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFrame, QScrollArea, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui  import QFont


# ── Status row helper ─────────────────────────────────────────────────────────

def _status_row(label: str, value: str = "Checking…",
                ok: bool | None = None) -> tuple[QWidget, QLabel, QLabel]:
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(12, 5, 12, 5)
    lay.setSpacing(10)

    # Status dot
    dot = QLabel()
    dot.setFixedSize(8, 8)
    color = "#334155" if ok is None else ("#10b981" if ok else "#f87171")
    dot.setStyleSheet(
        f"background: {color}; border-radius: 4px; "
        "min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px; border: none;"
    )
    lbl_w = QLabel(label)
    lbl_w.setFixedWidth(180)
    lbl_w.setStyleSheet(
        "font-size: 12px; color: #94a3b8; background: transparent; border: none;"
    )
    val_w = QLabel(value)
    val_w.setStyleSheet(
        "font-size: 12px; color: #e2e8f0; background: transparent; border: none;"
    )
    val_w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    lay.addWidget(dot)
    lay.addWidget(lbl_w)
    lay.addWidget(val_w)
    return row, dot, val_w


def _update_dot(dot: QLabel, ok: bool):
    color = "#10b981" if ok else "#f87171"
    dot.setStyleSheet(
        f"background: {color}; border-radius: 4px; "
        "min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px; border: none;"
    )


def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "font-size: 10px; font-weight: 700; color: #475569; "
        "letter-spacing: 1.2px; background: transparent; border: none; "
        "padding: 8px 12px 4px 12px;"
    )
    return lbl


# ── Background diagnostics runner ─────────────────────────────────────────────

class _DiagSignals(QObject):
    done = Signal(dict)


class _DiagRunner:
    def __init__(self):
        self.signals = _DiagSignals()

    def run_async(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        force = getattr(self, '_force', False)
        from core.hardware import (
            detect_hardware, get_ffmpeg_version, list_ffmpeg_encoders
        )
        from utils.process import hidden_subprocess_kwargs
        import subprocess, os

        results: dict = {}

        # FFmpeg
        results["ffmpeg_version"] = get_ffmpeg_version()
        results["ffmpeg_ok"] = results["ffmpeg_version"] != "not found"

        # FFprobe
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

        # Hardware
        hw = detect_hardware(force=force)
        results["hw"] = hw
        results["hw_ok"] = hw.has_any_gpu

        # Available encoders (relevant subset)
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

        # DRI devices
        dri_dir = "/dev/dri"
        dri_devs = []
        if os.path.isdir(dri_dir):
            dri_devs = sorted(os.listdir(dri_dir))
        results["dri_devices"] = dri_devs

        # psutil
        try:
            import psutil
            results["psutil_version"] = psutil.__version__
            results["psutil_ok"] = True
        except ImportError:
            results["psutil_version"] = "not installed"
            results["psutil_ok"] = False

        self.signals.done.emit(results)


# ── Main dialog ───────────────────────────────────────────────────────────────

class DiagnosticsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MediaCrush — Diagnostics")
        self.setMinimumSize(600, 680)
        self._runner = _DiagRunner()
        self._runner.signals.done.connect(self._on_done)
        self._rows: dict[str, tuple[QLabel, QLabel]] = {}  # key -> (dot, val)
        self._build_ui()
        self._run_diag()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet("background: #111120; border-bottom: 1px solid #1e1e35;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(16, 12, 16, 12)
        title = QLabel("System Diagnostics")
        title.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #a78bfa; "
            "background: transparent; border: none;"
        )
        self._status_lbl = QLabel("Running checks…")
        self._status_lbl.setStyleSheet(
            "font-size: 11px; color: #475569; background: transparent; border: none;"
        )
        btn_rerun = QPushButton("Re-run")
        btn_rerun.setObjectName("btn_secondary")
        btn_rerun.setFixedHeight(28)
        btn_rerun.clicked.connect(lambda: self._run_diag(force=True))
        hdr_lay.addWidget(title)
        hdr_lay.addStretch()
        hdr_lay.addWidget(self._status_lbl)
        hdr_lay.addWidget(btn_rerun)
        root.addWidget(hdr)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        self._body_lay = QVBoxLayout(body)
        self._body_lay.setSpacing(0)
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

        # ── Software section ──────────────────────────────────────────────────
        self._body_lay.addWidget(_section_title("SOFTWARE"))
        self._add_check("ffmpeg",    "FFmpeg")
        self._add_check("ffprobe",   "FFprobe")
        self._add_check("psutil",    "psutil (monitoring)")

        # ── GPU section ───────────────────────────────────────────────────────
        self._body_lay.addWidget(_section_title("GPU ACCELERATION"))
        self._add_check("gpu_overall", "Any GPU encoder")
        self._add_check("vaapi",       "VAAPI (AMD/Intel)")
        self._add_check("nvenc",       "NVIDIA NVENC")
        self._add_check("amf",         "AMD AMF")
        self._add_check("qsv",         "Intel Quick Sync")

        # ── Encoders section ──────────────────────────────────────────────────
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

        # ── DRI devices (raw text) ────────────────────────────────────────────
        self._body_lay.addWidget(_section_title("DRI DEVICES"))
        self._dri_lbl = QLabel("Detecting…")
        self._dri_lbl.setStyleSheet(
            "font-size: 11px; color: #64748b; padding: 4px 12px 8px 32px; "
            "background: transparent; border: none;"
        )
        self._body_lay.addWidget(self._dri_lbl)

        # ── Detailed log ──────────────────────────────────────────────────────
        self._body_lay.addWidget(_section_title("DETECTION LOG"))
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFixedHeight(150)
        self._log_text.setFont(QFont("Cascadia Code", 10))
        self._log_text.setStyleSheet(
            "margin: 0 12px 12px 12px; border-radius: 6px;"
        )
        self._body_lay.addWidget(self._log_text)
        self._body_lay.addStretch()

        # ── Footer ────────────────────────────────────────────────────────────
        footer = QHBoxLayout()
        footer.setContentsMargins(16, 8, 16, 12)
        footer.addStretch()
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        root.addLayout(footer)

    def _add_check(self, key: str, label: str):
        row, dot, val = _status_row(label)
        self._rows[key] = (dot, val)
        self._body_lay.addWidget(row)

    def _run_diag(self, force: bool = False):
        self._force = force
        self._runner._force = force
        self._status_lbl.setText("Running checks…")
        for dot, val in self._rows.values():
            color = "#334155"
            dot.setStyleSheet(
                f"background: {color}; border-radius: 4px; "
                "min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px; border: none;"
            )
            val.setText("Checking…")
        self._log_text.clear()
        self._runner.run_async()

    def _on_done(self, r: dict):
        hw = r.get("hw")

        def _set(key: str, ok: bool, text: str):
            if key not in self._rows:
                return
            dot, val = self._rows[key]
            _update_dot(dot, ok)
            val.setText(text)

        _set("ffmpeg",  r.get("ffmpeg_ok", False),
             r.get("ffmpeg_version", "N/A"))
        _set("ffprobe", r.get("ffprobe_ok", False),
             r.get("ffprobe_version", "N/A"))
        _set("psutil",  r.get("psutil_ok", False),
             r.get("psutil_version", "N/A"))

        if hw:
            _set("gpu_overall", hw.has_any_gpu, hw.hw_summary)
            _set("vaapi", hw.has_vaapi,
                 hw.vaapi_device if hw.has_vaapi else "not available")
            _set("nvenc", hw.has_nvenc,
                 "Available" if hw.has_nvenc else "not available")
            _set("amf", getattr(hw, "has_amf", False),
                 "Available" if getattr(hw, "has_amf", False) else "not available")
            _set("qsv",   hw.has_qsv,
                 "Available" if hw.has_qsv   else "not available")

            for entry in hw.diag_log:
                self._log_text.append(
                    f'<span style="color:#64748b;">{entry}</span>'
                )

        encs = r.get("encoders", {})
        for enc, ok in encs.items():
            _set(f"enc_{enc}", ok, "Available" if ok else "not built")

        dri = r.get("dri_devices", [])
        self._dri_lbl.setText(
            "  ".join(dri) if dri else "No /dev/dri devices found"
        )

        all_ok = r.get("ffmpeg_ok", False) and r.get("hw_ok", False)
        self._status_lbl.setText(
            "All systems ready" if all_ok else "Some checks failed — see below"
        )
        self._status_lbl.setStyleSheet(
            f"font-size: 11px; color: {'#10b981' if all_ok else '#f87171'}; "
            "background: transparent; border: none;"
        )
