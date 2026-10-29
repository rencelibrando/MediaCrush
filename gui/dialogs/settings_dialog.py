"""Settings and presets dialog."""
from __future__ import annotations
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QSlider, QSpinBox, QComboBox, QCheckBox,
    QPushButton, QLineEdit, QFileDialog, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from config.settings import Settings


class SettingsDialog(QDialog):
    settings_saved = Signal()

    def __init__(self, settings: Settings, hw_info=None, parent=None):
        super().__init__(parent)
        self._s = settings
        self._hw = hw_info
        self.setWindowTitle("MediaCrush - Settings")
        self.setMinimumWidth(520)
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        tabs = QTabWidget()
        root.addWidget(tabs)

        tabs.addTab(self._make_image_tab(), "Images")
        tabs.addTab(self._make_video_tab(), "Videos")
        tabs.addTab(self._make_engine_tab(), "Engine")
        tabs.addTab(self._make_output_tab(), "Output")

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("btn_secondary")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save Settings")
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        root.addLayout(btn_row)

    def _make_image_tab(self) -> QWidget:
        w = QWidget()
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

        lay.addRow("Preset:", self.img_preset)
        lay.addRow("Quality:", q_row)
        lay.addRow("Max size:", self.img_resize)
        lay.addRow("", self.img_strip)

        return w

    def _make_video_tab(self) -> QWidget:
        w = QWidget()
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

        note = QLabel("Lower = better quality / bigger file | 14-51")
        note.setObjectName("status_label")

        self.vid_res = QComboBox()
        self.vid_res.addItems(["original", "4k", "1080p", "720p", "480p"])

        self.vid_fps = QComboBox()
        self.vid_fps.addItems(["original", "60", "30", "24"])

        self.vid_skip_hevc = QCheckBox("Skip files already encoded in HEVC/AV1")

        lay.addRow("Codec:", self.vid_codec)
        lay.addRow("CRF / QP:", vq_row)
        lay.addRow("", note)
        lay.addRow("Resolution:", self.vid_res)
        lay.addRow("Frame rate:", self.vid_fps)
        lay.addRow("", self.vid_skip_hevc)

        return w

    def _make_engine_tab(self) -> QWidget:
        w = QWidget()
        lay = QFormLayout(w)
        lay.setSpacing(12)
        lay.setContentsMargins(16, 16, 16, 16)

        hw_summary = self._hw.hw_summary if self._hw else "Not detected yet"
        threads = self._hw.cpu_threads if self._hw else (os.cpu_count() or 4)
        self.hw_lbl = QLabel(f"{hw_summary}  |  {threads} CPU threads")
        self.hw_lbl.setObjectName("hw_badge")

        # Performance Mode Selector
        self.perf_mode = QComboBox()
        self.perf_mode.addItems([
            "⚡ Maximum Performance (All CPU & GPU Cores)",
            "⚖️ Balanced (Recommended)",
            "🌱 Power Saver / Quiet",
            "🛠️ Custom",
        ])
        self.perf_mode.currentIndexChanged.connect(self._on_perf_mode_changed)

        self.gpu_workers = QSpinBox()
        self.gpu_workers.setRange(0, 16)
        self.gpu_workers.setToolTip("Parallel GPU encoding streams (VAAPI/NVENC/AMF/QSV)")
        self.gpu_workers.valueChanged.connect(self._on_custom_tweak)

        self.cpu_workers = QSpinBox()
        self.cpu_workers.setRange(1, 64)
        self.cpu_workers.setToolTip(f"Concurrent CPU compression tasks (Recommended: all {threads} cores)")
        self.cpu_workers.valueChanged.connect(self._on_custom_tweak)

        self.cpu_threads = QSpinBox()
        self.cpu_threads.setRange(0, 64)
        self.cpu_threads.setSpecialValueText("0 (All Cores / Auto)")
        self.cpu_threads.setToolTip("FFmpeg CPU encoder threads per task. 0 allocates all available CPU cores.")
        self.cpu_threads.valueChanged.connect(self._on_custom_tweak)

        self.gpu_async = QSpinBox()
        self.gpu_async.setRange(1, 8)
        self.gpu_async.setToolTip("Hardware pipeline queue depth for GPU encoders (VAAPI)")
        self.gpu_async.valueChanged.connect(self._on_custom_tweak)

        self.hybrid_proc = QCheckBox("Engage both GPU and CPU simultaneously on task queue")
        self.hybrid_proc.setToolTip("Distributes tasks to both GPU and CPU workers concurrently to maximize throughput")
        self.hybrid_proc.toggled.connect(self._on_custom_tweak)

        btn_box = QHBoxLayout()
        max_btn = QPushButton("⚡ Maximize Performance Now")
        max_btn.setObjectName("btn_secondary")
        max_btn.setToolTip("Configure all sliders to 100% capacity for GPU & CPU")
        max_btn.clicked.connect(self._set_max)

        reprobe_btn = QPushButton("🔄 Re-detect Hardware")
        reprobe_btn.setObjectName("btn_secondary")
        reprobe_btn.setToolTip("Re-probe GPU and CPU hardware encoders")
        reprobe_btn.clicked.connect(self._reprobe_hw)

        btn_box.addWidget(max_btn)
        btn_box.addWidget(reprobe_btn)

        lay.addRow("Hardware:", self.hw_lbl)
        lay.addRow("Performance Mode:", self.perf_mode)
        lay.addRow("GPU workers:", self.gpu_workers)
        lay.addRow("CPU workers:", self.cpu_workers)
        lay.addRow("CPU threads / task:", self.cpu_threads)
        lay.addRow("GPU async depth:", self.gpu_async)
        lay.addRow("", self.hybrid_proc)
        lay.addRow("", btn_box)

        return w

    def _make_output_tab(self) -> QWidget:
        w = QWidget()
        lay = QFormLayout(w)
        lay.setSpacing(14)
        lay.setContentsMargins(16, 16, 16, 16)

        self.out_mode = QComboBox()
        self.out_mode.addItems([
            "inplace - replace originals",
            "alongside - same folder, new name",
            "custom - choose folder",
        ])
        self.out_mode.currentIndexChanged.connect(self._on_out_mode)

        dir_row = QHBoxLayout()
        self.out_dir = QLineEdit()
        self.out_dir.setPlaceholderText("Select output directory...")
        browse = QPushButton("Browse")
        browse.setObjectName("btn_secondary")
        browse.clicked.connect(self._browse_out)
        dir_row.addWidget(self.out_dir)
        dir_row.addWidget(browse)

        lay.addRow("Mode:", self.out_mode)
        lay.addRow("Directory:", dir_row)

        return w

    def _on_preset_change(self, name: str):
        q = {"lossless": 100, "high": 92, "balanced": 85, "small": 70, "tiny": 55}
        self.img_quality.setValue(q.get(name, 85))

    def _on_out_mode(self, idx: int):
        self.out_dir.setEnabled(idx == 2)

    def _on_perf_mode_changed(self, idx: int):
        if getattr(self, "_updating_perf_mode", False):
            return
        self._updating_perf_mode = True
        try:
            threads = self._hw.cpu_threads if self._hw else (os.cpu_count() or 4)
            if idx == 0:  # Maximum Performance
                self.gpu_workers.setValue(4)
                self.cpu_workers.setValue(threads)
                self.cpu_threads.setValue(0)
                self.gpu_async.setValue(4)
                self.hybrid_proc.setChecked(True)
            elif idx == 1:  # Balanced
                self.gpu_workers.setValue(2)
                self.cpu_workers.setValue(max(2, threads // 2))
                self.cpu_threads.setValue(0)
                self.gpu_async.setValue(2)
                self.hybrid_proc.setChecked(True)
            elif idx == 2:  # Power Saver
                self.gpu_workers.setValue(1)
                self.cpu_workers.setValue(2)
                self.cpu_threads.setValue(2)
                self.gpu_async.setValue(1)
                self.hybrid_proc.setChecked(False)
        finally:
            self._updating_perf_mode = False

    def _on_custom_tweak(self):
        if getattr(self, "_updating_perf_mode", False):
            return
        self._updating_perf_mode = True
        try:
            self.perf_mode.setCurrentIndex(3)  # Custom
        finally:
            self._updating_perf_mode = False

    def _set_max(self):
        self.perf_mode.setCurrentIndex(0)
        self._on_perf_mode_changed(0)

    def _reprobe_hw(self):
        from core.hardware import detect_hardware
        self._hw = detect_hardware(force=True)
        threads = self._hw.cpu_threads or (os.cpu_count() or 4)
        self.hw_lbl.setText(f"{self._hw.hw_summary}  |  {threads} CPU threads")

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

        perf_mode = self._s.get("engine.perf_mode", "max")
        mode_indices = {"max": 0, "balanced": 1, "power_save": 2, "custom": 3}
        self.perf_mode.blockSignals(True)
        self.perf_mode.setCurrentIndex(mode_indices.get(perf_mode, 0))
        self.perf_mode.blockSignals(False)

        threads = self._hw.cpu_threads if self._hw else (os.cpu_count() or 4)
        self.gpu_workers.blockSignals(True)
        self.gpu_workers.setValue(self._s.get("engine.gpu_workers", 4))
        self.gpu_workers.blockSignals(False)

        self.cpu_workers.blockSignals(True)
        self.cpu_workers.setValue(self._s.get("engine.cpu_workers", threads))
        self.cpu_workers.blockSignals(False)

        self.cpu_threads.blockSignals(True)
        self.cpu_threads.setValue(self._s.get("engine.cpu_threads", 0))
        self.cpu_threads.blockSignals(False)

        self.gpu_async.blockSignals(True)
        self.gpu_async.setValue(self._s.get("engine.gpu_async_depth", 4))
        self.gpu_async.blockSignals(False)

        self.hybrid_proc.blockSignals(True)
        self.hybrid_proc.setChecked(self._s.get("engine.hybrid_distribution", True))
        self.hybrid_proc.blockSignals(False)

        mode_map = {"inplace": 0, "alongside": 1, "custom": 2}
        self.out_mode.setCurrentIndex(
            mode_map.get(self._s.get("engine.output_mode", "inplace"), 0)
        )
        self.out_dir.setText(self._s.get("engine.output_dir", ""))

    def _save(self):
        self._s.set("image.preset", self.img_preset.currentText())
        self._s.set("image.quality", self.img_quality.value())
        self._s.set("image.resize_max_px", self.img_resize.value() or None)
        self._s.set("image.strip_metadata", self.img_strip.isChecked())

        self._s.set("video.codec", self.vid_codec.currentText())
        self._s.set("video.quality", self.vid_quality.value())
        self._s.set("video.resolution", self.vid_res.currentText())
        self._s.set("video.fps", self.vid_fps.currentText())
        self._s.set("video.skip_hevc", self.vid_skip_hevc.isChecked())

        mode_keys = {0: "max", 1: "balanced", 2: "power_save", 3: "custom"}
        self._s.set("engine.perf_mode", mode_keys.get(self.perf_mode.currentIndex(), "custom"))
        self._s.set("engine.gpu_workers", self.gpu_workers.value())
        self._s.set("engine.cpu_workers", self.cpu_workers.value())
        self._s.set("engine.cpu_threads", self.cpu_threads.value())
        self._s.set("engine.gpu_async_depth", self.gpu_async.value())
        self._s.set("engine.hybrid_distribution", self.hybrid_proc.isChecked())

        mode_map = {0: "inplace", 1: "alongside", 2: "custom"}
        self._s.set("engine.output_mode", mode_map[self.out_mode.currentIndex()])
        self._s.set("engine.output_dir", self.out_dir.text())

        self._s.save()
        self.settings_saved.emit()
        self.accept()
