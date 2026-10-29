"""Main application window with integrated perf, logs, diagnostics, and dynamic theming."""
from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QProgressBar, QFileDialog,
    QComboBox, QToolBar, QStatusBar, QFrame,
    QSizePolicy, QApplication, QTabWidget, QSplitter,
    QScrollArea
)
from PySide6.QtCore import Qt, QSize, Slot, Signal, QTimer
from PySide6.QtGui import QIcon

from core.task import CompressionTask, TaskStatus, IMAGE_EXTS, VIDEO_EXTS
from core.engine import CompressionEngine
from config.settings import Settings
from utils.logger import get_logger

from gui.styles import get_style
from gui.icons import icon
from gui.widgets.drop_zone import DropZone
from gui.widgets.queue_widget import QueueWidget
from gui.widgets.stats_widget import StatsWidget
from gui.widgets.logs_widget import LogsWidget
from gui.widgets.perf_widget import PerfWidget
from gui.dialogs.settings_dialog import SettingsDialog
from gui.dialogs.diagnostics_dialog import DiagnosticsDialog


class MainWindow(QMainWindow):
    _paths_ready = Signal(list)

    def __init__(self):
        super().__init__()
        self._settings = Settings()
        self._engine = CompressionEngine()
        self._logger = get_logger()
        self._paused = False
        self._running = False

        self.setWindowTitle("MediaCrush")
        self.setMinimumSize(720, 500)
        self._restore_geometry()
        self._build_ui()
        self._connect_engine()
        self._apply_theme()
        self._paths_ready.connect(self._add_paths)
        self._engine.detect_hardware_async()

    def _build_ui(self):
        tb = QToolBar("Main", self)
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        title = QLabel("MediaCrush")
        title.setObjectName("app_title")
        tb.addWidget(title)
        tb.addWidget(self._vsep())

        preset_lbl = QLabel("Preset")
        preset_lbl.setObjectName("section_title")
        self.preset_cb = QComboBox()
        self.preset_cb.addItems(["balanced", "high", "small", "lossless", "tiny"])
        self.preset_cb.setFixedWidth(110)
        self.preset_cb.setToolTip("Quality preset for all new tasks")

        saved_preset = self._settings.get("image.preset", "balanced")
        self.preset_cb.blockSignals(True)
        self.preset_cb.setCurrentText(saved_preset)
        self.preset_cb.blockSignals(False)
        self.preset_cb.currentTextChanged.connect(self._on_quick_preset)

        tb.addWidget(preset_lbl)
        tb.addWidget(self.preset_cb)
        tb.addWidget(self._vsep())

        self.btn_start = QPushButton("Start")
        self.btn_start.setObjectName("btn_start")
        self.btn_start.clicked.connect(self._start)

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setObjectName("btn_pause")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self._pause)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("btn_cancel")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel)

        for b in (self.btn_start, self.btn_pause, self.btn_cancel):
            tb.addWidget(b)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer.setStyleSheet("background: transparent;")
        tb.addWidget(spacer)

        self.hw_lbl = QLabel("Detecting...")
        self.hw_lbl.setObjectName("hw_badge")
        self.hw_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        tb.addWidget(self.hw_lbl)
        tb.addWidget(self._vsep())

        self.btn_diag = self._icon_btn(icon("error", "#a1a1aa"), "Diagnostics",
                                       self._open_diagnostics)
        self.btn_settings = self._icon_btn(icon("settings", "#a1a1aa"), "Settings",
                                           self._open_settings)
        self.btn_theme = self._icon_btn(icon("sun", "#a1a1aa"), "Toggle theme",
                                         self._toggle_theme)

        for b in (self.btn_diag, self.btn_settings, self.btn_theme):
            tb.addWidget(b)
        tb.addWidget(QWidget())

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(12)
        root.addWidget(splitter)

        sidebar_outer = QFrame()
        sidebar_outer.setObjectName("panel")
        sidebar_outer.setMinimumWidth(260)
        sidebar_outer.setMaximumWidth(360)
        sidebar_outer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        so_lay = QVBoxLayout(sidebar_outer)
        so_lay.setContentsMargins(0, 0, 0, 0)
        so_lay.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        sidebar_inner = QWidget()
        sidebar_inner.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        s_lay = QVBoxLayout(sidebar_inner)
        s_lay.setContentsMargins(10, 10, 10, 10)
        s_lay.setSpacing(12)

        self.drop_zone = DropZone()
        self.drop_zone.setMinimumHeight(100)
        self.drop_zone.files_dropped.connect(self._add_paths)
        s_lay.addWidget(self.drop_zone)

        self.btn_add_files = QPushButton("Add Files")
        self.btn_add_files.setObjectName("btn_secondary")
        self.btn_add_files.setFixedHeight(30)
        self.btn_add_files.clicked.connect(self._add_files)

        self.btn_add_folder = QPushButton("Add Folder")
        self.btn_add_folder.setObjectName("btn_secondary")
        self.btn_add_folder.setFixedHeight(30)
        self.btn_add_folder.clicked.connect(self._add_folder)

        file_btn_row = QHBoxLayout()
        file_btn_row.setSpacing(8)
        file_btn_row.addWidget(self.btn_add_files)
        file_btn_row.addWidget(self.btn_add_folder)
        s_lay.addLayout(file_btn_row)

        self.stats = StatsWidget()
        self.stats.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        s_lay.addWidget(self.stats)

        self.perf = PerfWidget()
        self.perf.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        s_lay.addWidget(self.perf)
        s_lay.addStretch()

        scroll.setWidget(sidebar_inner)
        so_lay.addWidget(scroll)
        splitter.addWidget(sidebar_outer)

        right = QFrame()
        right.setObjectName("panel")
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        r_lay = QVBoxLayout(right)
        r_lay.setContentsMargins(14, 14, 14, 14)
        r_lay.setSpacing(10)

        tab_hdr = QHBoxLayout()
        q_title = QLabel("Compression")
        q_title.setObjectName("panel_title")

        self.queue_count = QLabel("0 files")
        self.queue_count.setObjectName("panel_subtitle")

        self.btn_clear_q = QPushButton("Clear Queue")
        self.btn_clear_q.setObjectName("btn_danger")
        self.btn_clear_q.setFixedHeight(26)
        self.btn_clear_q.clicked.connect(self._clear_queue)

        tab_hdr.addWidget(q_title)
        tab_hdr.addStretch()
        tab_hdr.addWidget(self.queue_count)
        tab_hdr.addWidget(self.btn_clear_q)
        r_lay.addLayout(tab_hdr)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("main_tabs")
        self._tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._tabs.currentChanged.connect(self._on_tab_changed)

        queue_container = QWidget()
        queue_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        q_lay = QVBoxLayout(queue_container)
        q_lay.setContentsMargins(0, 4, 0, 0)
        self.queue_widget = QueueWidget()
        self.queue_widget.cancel_task.connect(self._engine.cancel_task)
        q_lay.addWidget(self.queue_widget)
        self._tabs.addTab(queue_container, "Queue")

        self.logs_widget = LogsWidget()
        self.logs_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._tabs.addTab(self.logs_widget, "Logs")

        r_lay.addWidget(self._tabs)
        splitter.addWidget(right)

        splitter.setSizes([280, 9999])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        sb = QStatusBar()
        self.setStatusBar(sb)

        self.overall_bar = QProgressBar()
        self.overall_bar.setObjectName("overall")
        self.overall_bar.setRange(0, 100)
        self.overall_bar.setValue(0)
        self.overall_bar.setFixedWidth(240)
        self.overall_bar.setTextVisible(True)
        self.overall_bar.setFormat("%p%")

        self.status_lbl = QLabel("Ready")
        self.status_lbl.setObjectName("status_label")

        sb.addWidget(self.status_lbl)
        sb.addPermanentWidget(self.overall_bar)

    def _vsep(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.VLine)
        return f

    def _hsep(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        return f

    def _icon_btn(self, ico: QIcon, tooltip: str, slot) -> QPushButton:
        b = QPushButton()
        b.setIcon(ico)
        b.setIconSize(QSize(16, 16))
        b.setObjectName("btn_icon")
        b.setFixedSize(30, 30)
        b.setToolTip(tooltip)
        b.clicked.connect(slot)
        return b

    def _connect_engine(self):
        sig = self._engine.signals
        sig.task_progress.connect(self._on_task_progress)
        sig.task_status.connect(self._on_task_status)
        sig.task_done.connect(self._on_task_done)
        sig.task_error.connect(self._on_task_error)
        sig.log_message.connect(self._on_log)
        sig.all_done.connect(self._on_all_done)
        sig.hw_detected.connect(self._on_hw_detected)
        sig.stats_update.connect(self._on_stats_update)

    @Slot(str, float)
    def _on_task_progress(self, task_id: str, pct: float):
        self.queue_widget.set_progress(task_id, pct)
        self._update_overall()

    @Slot(str, str)
    def _on_task_status(self, task_id: str, status: str):
        self.queue_widget.set_status(task_id, status)

    @Slot(str, int, int, str)
    def _on_task_done(self, task_id: str, orig: int, new_size: int, encoder: str):
        self.queue_widget.set_status(task_id, "Done", encoder)
        self.queue_widget.set_sizes(task_id, orig, new_size)
        if encoder.startswith("Skipped"):
            self.stats.record_skipped(orig)
        else:
            self.stats.record_done(orig, new_size)
        self._update_overall()

    @Slot(str, str)
    def _on_task_error(self, task_id: str, msg: str):
        first_line = msg.splitlines()[0] if msg else "Failed"
        self.queue_widget.set_status(task_id, "Error", encoder=first_line)
        self.stats.record_error()
        self._update_overall()

    @Slot(str)
    def _on_log(self, msg: str):
        self._logger.append(msg)
        self.logs_widget.append_line(msg)
        self.status_lbl.setText(msg[-100:] if len(msg) > 100 else msg)
        if self._tabs.currentIndex() != 1:
            cur = self._tabs.tabText(1)
            if not cur.endswith("*"):
                self._tabs.setTabText(1, cur + " *")

    @Slot()
    def _on_all_done(self):
        self._running = False
        self._paused = False
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.stats.set_working(0)
        self.overall_bar.setValue(100)

        tasks = self._engine.get_tasks()
        errors = sum(1 for t in tasks if t.status == TaskStatus.ERROR)
        done = sum(1 for t in tasks if t.status == TaskStatus.DONE)
        if errors and not done:
            self.status_lbl.setText(f"Finished with {errors} error(s) — check Logs tab")
        elif errors:
            self.status_lbl.setText(f"Finished: {done} succeeded, {errors} error(s)")
        else:
            self.status_lbl.setText("All tasks completed successfully")

    @Slot(str)
    def _on_hw_detected(self, summary: str):
        self.hw_lbl.setText(summary)

    @Slot(int, int, int)
    def _on_stats_update(self, gpu: int, cpu: int, queued: int):
        self.perf.update_workers(gpu, cpu, queued)
        self.stats.set_working(gpu + cpu)

    def _on_tab_changed(self, idx: int):
        if idx == 1:
            cur = self._tabs.tabText(1)
            if cur.endswith(" *"):
                self._tabs.setTabText(1, cur[:-2])

    def _start(self):
        tasks = [t for t in self._engine.get_tasks()
                 if t.status.value in ("Queued", "Paused")]
        if not tasks:
            self.status_lbl.setText("No queued tasks - add files first")
            return
        self._running = True
        self._paused = False
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.stats.start_session(len(tasks))
        self._engine.start(self._settings.compression_settings())
        self.status_lbl.setText("Compressing...")

    def _pause(self):
        theme = self._settings.get("ui.theme", "dark")
        pause_ico_color = "#f59e0b" if theme == "dark" else "#d97706"
        if not self._paused:
            self._engine.pause()
            self.btn_pause.setIcon(icon("play", pause_ico_color))
            self.btn_pause.setText("Resume")
            self._paused = True
            self.status_lbl.setText("Paused")
        else:
            self._engine.resume()
            self.btn_pause.setIcon(icon("pause", pause_ico_color))
            self.btn_pause.setText("Pause")
            self._paused = False
            self.status_lbl.setText("Compressing...")

    def _cancel(self):
        self._engine.cancel()
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self._running = False
        self._paused = False
        self.status_lbl.setText("Cancelled")

    def _clear_queue(self):
        self._engine.clear_queue()
        self.queue_widget.clear_all()
        self.queue_count.setText("0 files")
        self.overall_bar.setValue(0)
        self.status_lbl.setText("Queue cleared")

    def _add_files(self):
        last = self._settings.get("ui.last_dir", str(Path.home()))
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select media files", last,
            "Media Files (*.jpg *.jpeg *.png *.webp *.heic *.heif *.bmp "
            "*.tiff *.tif *.gif *.avif *.mp4 *.mkv *.avi *.mov *.webm "
            "*.flv *.wmv *.m4v *.mpeg *.mpg)"
        )
        if paths:
            self._settings.set("ui.last_dir", str(Path(paths[0]).parent))
            self._settings.save()
            self._add_paths([Path(p) for p in paths])

    def _add_folder(self):
        import threading
        last = self._settings.get("ui.last_dir", str(Path.home()))
        d = QFileDialog.getExistingDirectory(self, "Select folder", last)
        if not d:
            return
        self._settings.set("ui.last_dir", d)
        self._settings.save()
        self.status_lbl.setText(f"Scanning {d}...")

        def _scan():
            exts = IMAGE_EXTS | VIDEO_EXTS
            paths = [f for f in Path(d).rglob("*")
                     if f.is_file() and f.suffix.lower() in exts]
            self._paths_ready.emit(paths)

        threading.Thread(target=_scan, daemon=True).start()

    def _add_paths(self, paths: list[Path]):
        out_mode = self._settings.get("engine.output_mode", "inplace")
        out_dir = (Path(self._settings.get("engine.output_dir", ""))
                   if out_mode == "custom" else None)

        existing = {t.path for t in self._engine.get_tasks()}
        new_tasks: list[CompressionTask] = []
        for p in paths:
            if p not in existing:
                try:
                    task = CompressionTask(path=p, output_dir=out_dir)
                    new_tasks.append(task)
                    existing.add(p)
                except Exception:
                    pass

        if not new_tasks:
            return

        self._engine.add_tasks(new_tasks)

        def _add_batch(items, idx=0):
            batch = items[idx:idx + 250]
            self.queue_widget.add_tasks(batch)
            if idx + 250 < len(items):
                QTimer.singleShot(0, lambda: _add_batch(items, idx + 250))
            else:
                total = len(self._engine.get_tasks())
                self.queue_count.setText(
                    f"{total} file{'s' if total != 1 else ''}"
                )
                self.status_lbl.setText(
                    f"Added {len(new_tasks)} file(s) - total {total}"
                )

        QTimer.singleShot(0, lambda: _add_batch(new_tasks))

    def _open_settings(self):
        dlg = SettingsDialog(self._settings, self._engine.hw, self)
        dlg.settings_saved.connect(self._apply_theme)
        dlg.settings_saved.connect(self._sync_preset_cb)
        dlg.exec()

    def _open_diagnostics(self):
        dlg = DiagnosticsDialog(self)
        dlg.exec()

    def _toggle_theme(self):
        cur = self._settings.get("ui.theme", "dark")
        new = "light" if cur == "dark" else "dark"
        self._settings.set("ui.theme", new)
        self._settings.save()
        self._apply_theme()

    def _apply_theme(self):
        theme = self._settings.get("ui.theme", "dark")
        is_dark = theme == "dark"
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_style(theme))

        self.btn_theme.setIcon(
            icon("sun", "#a1a1aa") if is_dark else icon("moon", "#475569")
        )
        self.btn_start.setIcon(
            icon("play", "#ecfdf5" if is_dark else "#047857")
        )
        pause_color = "#fffbeb" if is_dark else "#b45309"
        self.btn_pause.setIcon(
            icon("play" if self._paused else "pause", pause_color)
        )
        self.btn_cancel.setIcon(
            icon("stop", "#fef2f2" if is_dark else "#b91c1c")
        )

        icon_color = "#a1a1aa" if is_dark else "#64748b"
        self.btn_diag.setIcon(icon("error", icon_color))
        self.btn_settings.setIcon(icon("settings", icon_color))
        self.btn_add_files.setIcon(icon("file_add", icon_color))
        self.btn_add_folder.setIcon(icon("folder_open", icon_color))
        self.btn_clear_q.setIcon(icon("delete", "#f87171" if is_dark else "#dc2626"))

        self.queue_widget.set_theme(theme)
        self.drop_zone.set_theme(theme)
        self.stats.set_theme(theme)
        self.perf.set_theme(theme)
        self.logs_widget.set_theme(theme)

    def _on_quick_preset(self, name: str):
        quality_map = {"lossless": 100, "high": 92, "balanced": 85, "small": 70, "tiny": 55}
        vid_map = {"lossless": 18, "high": 22, "balanced": 28, "small": 33, "tiny": 40}
        self._settings.set("image.preset", name)
        self._settings.set("image.quality", quality_map.get(name, 85))
        self._settings.set("video.quality", vid_map.get(name, 28))
        self._settings.save()

    def _sync_preset_cb(self):
        saved = self._settings.get("image.preset", "balanced")
        self.preset_cb.blockSignals(True)
        self.preset_cb.setCurrentText(saved)
        self.preset_cb.blockSignals(False)

    def _update_overall(self):
        tasks = self._engine.get_tasks()
        if not tasks:
            return
        done = sum(
            1 for t in tasks
            if t.status.value in ("Done", "Error", "Skipped", "Cancelled")
        )
        running_progress = sum(
            t.progress / 100
            for t in tasks if t.status.value == "Running"
        )
        total_pct = int((done + running_progress) / len(tasks) * 100)
        self.overall_bar.setValue(total_pct)

    def _restore_geometry(self):
        geo = self._settings.get("ui.window_geometry")
        if geo:
            try:
                from PySide6.QtCore import QByteArray
                self.restoreGeometry(QByteArray.fromBase64(geo.encode()))
                return
            except Exception:
                pass
        self.resize(1200, 760)

    def closeEvent(self, event):
        try:
            self.perf._poller.stop()
        except Exception:
            pass
        if self._running:
            self._engine.cancel()
        geo = self.saveGeometry().toBase64().data().decode()
        self._settings.set("ui.window_geometry", geo)
        self._settings.save()
        self._logger.close()
        super().closeEvent(event)
