"""Settings / presets dialog."""
from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QSlider, QSpinBox, QComboBox, QCheckBox,
    QPushButton, QLineEdit, QFileDialog, QGroupBox, QFormLayout, QFrame
)
from PySide6.QtCore import Qt, Signal
from config.settings import Settings


class SettingsDialog(QDialog):
    settings_saved = Signal()

    def __init__(self, settings: Settings, hw_info=None, parent=None):
        super().__init__(parent)
        self._s  = settings
        self._hw = hw_info
        self.setWindowTitle("MediaCrush — Settings")
        self.setMinimumWidth(520)
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        tabs = QTabWidget()
        root.addWidget(tabs)

        tabs.addTab(self._make_image_tab(),    "Images")
        tabs.addTab(self._make_video_tab(),    "Videos")
        tabs.addTab(self._make_engine_tab(),   "Engine")
        tabs.addTab(self._make_output_tab(),   "Output")

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("btn_secondary")
        cancel.clicked.connect(self.reject)
        save   = QPushButton("Save Settings")
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        root.addLayout(btn_row)

    # ── Tab builders ─────────────────────────────────────────────────────────

    def _make_image_tab(self) -> QWidget:
        w   = QWidget()
        lay = QFormLayout(w)
        lay.setSpacing(14)
        lay.setContentsMargins(16, 16, 16, 16)

        self.img_preset = QComboBox()
        self.img_preset.addItems(["lossless", "high", "balanced", "small", "tiny"])
        self.img_preset.currentTextChanged.connect(self._on_preset_change)

        self.img_quality = QSlider(Qt.Horizontal)
        self.img_quality.setRange(1, 100)
        self.img_quality.setTickInterval(10)
        self.img_quality_lbl = QLabel("85")

        def _upd_q(v):
            self.img_quality_lbl.setText(str(v))
        self.img_quality.valueChanged.connect(_upd_q)

        q_row = QHBoxLayout()
        q_row.addWidget(self.img_quality)
        q_row.addWidget(self.img_quality_lbl)

        self.img_strip = QCheckBox("Strip metadata (EXIF)")
        self.img_resize = QSpinBox()
        self.img_resize.setRange(0, 16000)
        self.img_resize.setSpecialValueText("No resize")
        self.img_resize.setSuffix(" px (longest edge)")

        lay.addRow("Preset:",       self.img_preset)
        lay.addRow("Quality:",      q_row)
        lay.addRow("Max size:",     self.img_resize)
        lay.addRow("",              self.img_strip)

        return w

    def _make_video_tab(self) -> QWidget:
        w   = QWidget()
        lay = QFormLayout(w)
        lay.setSpacing(14)
        lay.setContentsMargins(16, 16, 16, 16)

        self.vid_codec = QComboBox()
        self.vid_codec.addItems(["h265", "h264", "av1"])

        self.vid_quality = QSlider(Qt.Horizontal)
        self.vid_quality.setRange(14, 51)
        self.vid_quality_lbl = QLabel("28")
        def _upd_vq(v):
            self.vid_quality_lbl.setText(str(v))
        self.vid_quality.valueChanged.connect(_upd_vq)

        vq_row = QHBoxLayout()
        vq_row.addWidget(self.vid_quality)
        vq_row.addWidget(self.vid_quality_lbl)

        note = QLabel("Lower = better quality / bigger file  |  14–51")
        note.setStyleSheet("color: #64748b; font-size: 11px; background: transparent; border: none;")

        self.vid_res = QComboBox()
        self.vid_res.addItems(["original", "4k", "1080p", "720p", "480p"])

        self.vid_fps = QComboBox()
        self.vid_fps.addItems(["original", "60", "30", "24"])

        self.vid_skip_hevc = QCheckBox("Skip files already encoded in HEVC/AV1")

        lay.addRow("Codec:",        self.vid_codec)
        lay.addRow("CRF / QP:",     vq_row)
        lay.addRow("",              note)
        lay.addRow("Resolution:",   self.vid_res)
        lay.addRow("Frame rate:",   self.vid_fps)
        lay.addRow("",              self.vid_skip_hevc)

        return w

    def _make_engine_tab(self) -> QWidget:
        w   = QWidget()
        lay = QFormLayout(w)
        lay.setSpacing(14)
        lay.setContentsMargins(16, 16, 16, 16)

        hw_lbl = QLabel(
            self._hw.hw_summary if self._hw else "Not detected yet"
        )
        hw_lbl.setObjectName("hw_badge")
        hw_lbl.setStyleSheet("background: transparent; border: none;")

        self.gpu_workers = QSpinBox()
        self.gpu_workers.setRange(0, 16)

        self.cpu_workers = QSpinBox()
        self.cpu_workers.setRange(1, 64)

        max_btn = QPushButton("Maximum Performance")
        max_btn.setToolTip("Set GPU=4, CPU=8 (all cores)")
        max_btn.clicked.connect(self._set_max)

        lay.addRow("Hardware:",     hw_lbl)
        lay.addRow("GPU workers:",  self.gpu_workers)
        lay.addRow("CPU workers:",  self.cpu_workers)
        lay.addRow("",              max_btn)

        return w

    def _make_output_tab(self) -> QWidget:
        w   = QWidget()
        lay = QFormLayout(w)
        lay.setSpacing(14)
        lay.setContentsMargins(16, 16, 16, 16)

        self.out_mode = QComboBox()
        self.out_mode.addItems([
            "inplace — replace originals",
            "alongside — same folder, new name",
            "custom — choose folder",
        ])
        self.out_mode.currentIndexChanged.connect(self._on_out_mode)

        dir_row = QHBoxLayout()
        self.out_dir = QLineEdit()
        self.out_dir.setPlaceholderText("Select output directory…")
        browse = QPushButton("Browse")
        browse.setObjectName("btn_secondary")
        browse.clicked.connect(self._browse_out)
        dir_row.addWidget(self.out_dir)
        dir_row.addWidget(browse)

        lay.addRow("Mode:",         self.out_mode)
        lay.addRow("Directory:",    dir_row)

        return w

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _on_preset_change(self, name: str):
        q = {"lossless": 100, "high": 92, "balanced": 85, "small": 70, "tiny": 55}
        self.img_quality.setValue(q.get(name, 85))

    def _on_out_mode(self, idx: int):
        self.out_dir.setEnabled(idx == 2)

    def _set_max(self):
        self.gpu_workers.setValue(4)
        self.cpu_workers.setValue(8)

    def _browse_out(self):
        d = QFileDialog.getExistingDirectory(self, "Select output directory")
        if d:
            self.out_dir.setText(d)

    def _load(self):
        self.img_preset.setCurrentText(self._s.get("image.preset", "balanced"))
        self.img_quality.setValue(self._s.get("image.quality", 85))
        self.img_resize.setValue(self._s.get("image.resize_max_px") or 0)
        self.img_strip.setChecked(self._s.get("image.strip_metadata", False))

        self.vid_codec.setCurrentText(self._s.get("video.codec", "h265"))
        self.vid_quality.setValue(self._s.get("video.quality", 28))
        self.vid_res.setCurrentText(self._s.get("video.resolution", "original"))
        self.vid_fps.setCurrentText(self._s.get("video.fps", "original"))
        self.vid_skip_hevc.setChecked(self._s.get("video.skip_hevc", True))

        self.gpu_workers.setValue(self._s.get("engine.gpu_workers", 4))
        self.cpu_workers.setValue(self._s.get("engine.cpu_workers", 8))

        mode_map = {"inplace": 0, "alongside": 1, "custom": 2}
        self.out_mode.setCurrentIndex(
            mode_map.get(self._s.get("engine.output_mode", "inplace"), 0)
        )
        self.out_dir.setText(self._s.get("engine.output_dir", ""))

    def _save(self):
        self._s.set("image.preset",        self.img_preset.currentText())
        self._s.set("image.quality",       self.img_quality.value())
        self._s.set("image.resize_max_px",
                    self.img_resize.value() or None)
        self._s.set("image.strip_metadata", self.img_strip.isChecked())

        self._s.set("video.codec",         self.vid_codec.currentText())
        self._s.set("video.quality",       self.vid_quality.value())
        self._s.set("video.resolution",    self.vid_res.currentText())
        self._s.set("video.fps",           self.vid_fps.currentText())
        self._s.set("video.skip_hevc",     self.vid_skip_hevc.isChecked())

        self._s.set("engine.gpu_workers",  self.gpu_workers.value())
        self._s.set("engine.cpu_workers",  self.cpu_workers.value())

        mode_map = {0: "inplace", 1: "alongside", 2: "custom"}
        self._s.set("engine.output_mode",
                    mode_map[self.out_mode.currentIndex()])
        self._s.set("engine.output_dir", self.out_dir.text())

        self._s.save()
        self.settings_saved.emit()
        self.accept()
