"""Main application window — tabbed layout with integrated perf/logs/diagnostics."""
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
from PySide6.QtGui  import QIcon

from core.task    import CompressionTask, IMAGE_EXTS, VIDEO_EXTS
from core.engine  import CompressionEngine
from config.settings import Settings
from utils.logger    import get_logger

from gui.styles                           import get_style
from gui.icons                            import icon
from gui.widgets.drop_zone                import DropZone
from gui.widgets.queue_widget             import QueueWidget
from gui.widgets.stats_widget             import StatsWidget
from gui.widgets.logs_widget              import LogsWidget
from gui.widgets.perf_widget              import PerfWidget
from gui.dialogs.settings_dialog          import SettingsDialog
from gui.dialogs.diagnostics_dialog       import DiagnosticsDialog


class MainWindow(QMainWindow):
    _paths_ready = Signal(list)

    def __init__(self):
        super().__init__()
        self._settings = Settings()
        self._engine   = CompressionEngine()
        self._logger   = get_logger()
        self._paused   = False
        self._running  = False

        self.setWindowTitle("MediaCrush")
        self.setMinimumSize(680, 480)
        self._restore_geometry()
        self._build_ui()
        self._connect_engine()
        self._apply_theme()
        self._paths_ready.connect(self._add_paths)
        self._engine.detect_hardware_async()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Toolbar ──────────────────────────────────────────────────────────
        tb = QToolBar("Main", self)
        tb.setMovable(False)
        tb.setIconSize(QSize(15, 15))
        self.addToolBar(tb)

        # App title
        title = QLabel("  MediaCrush  ")
        title.setStyleSheet(
            "font-size: 16px; font-weight: 800; color: #a78bfa; "
            "background: transparent; border: none; letter-spacing: 0.3px;"
        )
        tb.addWidget(title)
        tb.addWidget(self._vsep())

        # Preset selector
        preset_lbl = QLabel("Preset")
        preset_lbl.setStyleSheet(
            "color: #475569; font-size: 11px; font-weight: 600; "
            "background: transparent; border: none; letter-spacing: 0.5px;"
        )
        self.preset_cb = QComboBox()
        self.preset_cb.addItems(["balanced", "high", "small", "lossless", "tiny"])
        self.preset_cb.setFixedWidth(120)
        self.preset_cb.setToolTip("Quality preset for all new tasks")
        # Initialize from saved setting without triggering _on_quick_preset
        saved_preset = self._settings.get("image.preset", "balanced")
        self.preset_cb.blockSignals(True)
        self.preset_cb.setCurrentText(saved_preset)
        self.preset_cb.blockSignals(False)
        self.preset_cb.currentTextChanged.connect(self._on_quick_preset)
        tb.addWidget(preset_lbl)
        tb.addWidget(self.preset_cb)
        tb.addWidget(self._vsep())

        # Action buttons
        self.btn_start  = self._action_btn(
            "Start",  icon("play",  "#10b981"), "#10b981", self._start)
        self.btn_pause  = self._action_btn(
            "Pause",  icon("pause", "#f59e0b"), "#f59e0b", self._pause)
        self.btn_cancel = self._action_btn(
            "Cancel", icon("stop",  "#f87171"), "#f87171", self._cancel)
        self.btn_pause.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        for b in (self.btn_start, self.btn_pause, self.btn_cancel):
            tb.addWidget(b)

        # Push right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer.setStyleSheet("background: transparent;")
        tb.addWidget(spacer)

        # HW badge — hides itself when toolbar is too narrow
        self.hw_lbl = QLabel("Detecting…")
        self.hw_lbl.setStyleSheet(
            "font-size: 10px; color: #10b981; font-weight: 500; "
            "background: transparent; border: none; padding: 0 8px;"
        )
        self.hw_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        tb.addWidget(self.hw_lbl)
        tb.addWidget(self._vsep())

        # Diagnostics, Settings, Theme
        self.btn_diag = self._icon_btn(icon("error", "#64748b"), "Diagnostics",
                                       self._open_diagnostics)
        self.btn_settings = self._icon_btn(icon("settings", "#94a3b8"), "Settings",
                                           self._open_settings)
        self.btn_theme    = self._icon_btn(icon("sun", "#94a3b8"), "Toggle theme",
                                           self._toggle_theme)
        for b in (self.btn_diag, self.btn_settings, self.btn_theme):
            tb.addWidget(b)
        tb.addWidget(QWidget())   # right padding

        # ── Central widget ────────────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(0)

        # ── Splitter: sidebar | main ──────────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(
            "QSplitter::handle { background: #1a1a2e; }"
            "QSplitter::handle:hover { background: #6d28d9; }"
        )
        root.addWidget(splitter)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar_outer = QFrame()
        sidebar_outer.setObjectName("panel")
        sidebar_outer.setMinimumWidth(180)
        sidebar_outer.setMaximumWidth(320)
        sidebar_outer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        so_lay = QVBoxLayout(sidebar_outer)
        so_lay.setContentsMargins(0, 0, 0, 0)
        so_lay.setSpacing(0)

        # Scrollable inner content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        sidebar_inner = QWidget()
        sidebar_inner.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        s_lay = QVBoxLayout(sidebar_inner)
        s_lay.setContentsMargins(12, 14, 12, 14)
        s_lay.setSpacing(8)

        # Drop zone
        self.drop_zone = DropZone()
        self.drop_zone.setMinimumHeight(110)
        self.drop_zone.files_dropped.connect(self._add_paths)
        s_lay.addWidget(self.drop_zone)

        # File / folder buttons
        for ico_name, txt, slot, obj in [
            ("file_add",    "  Add Files",   self._add_files,   "btn_secondary"),
            ("folder_open", "  Add Folder",  self._add_folder,  "btn_secondary"),
            ("delete",      "  Clear Queue", self._clear_queue, "btn_danger"),
        ]:
            b = QPushButton()
            b.setIcon(icon(ico_name,
                           "#f87171" if obj == "btn_danger" else "#94a3b8"))
            b.setIconSize(QSize(13, 13))
            b.setText(txt)
            b.setObjectName(obj)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.clicked.connect(slot)
            s_lay.addWidget(b)

        s_lay.addWidget(self._hsep())

        # Stats
        self.stats = StatsWidget()
        self.stats.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        s_lay.addWidget(self.stats)
        s_lay.addWidget(self._hsep())

        # Performance monitor
        self.perf = PerfWidget()
        self.perf.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        s_lay.addWidget(self.perf)
        s_lay.addStretch()

        scroll.setWidget(sidebar_inner)
        so_lay.addWidget(scroll)
        splitter.addWidget(sidebar_outer)

        # ── Right panel ───────────────────────────────────────────────────────
        right = QFrame()
        right.setObjectName("panel")
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        r_lay = QVBoxLayout(right)
        r_lay.setContentsMargins(12, 12, 12, 12)
        r_lay.setSpacing(8)

        # Header row
        tab_hdr = QHBoxLayout()
        q_title = QLabel("Compression")
        q_title.setStyleSheet(
            "font-size: 14px; font-weight: 700; color: #e2e8f0; "
            "background: transparent; border: none;"
        )
        self.queue_count = QLabel("0 files")
        self.queue_count.setStyleSheet(
            "color: #475569; font-size: 12px; background: transparent; border: none;"
        )
        tab_hdr.addWidget(q_title)
        tab_hdr.addStretch()
        tab_hdr.addWidget(self.queue_count)
        r_lay.addLayout(tab_hdr)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setObjectName("main_tabs")
        self._tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._tabs.currentChanged.connect(self._on_tab_changed)

        # Tab 0: Queue
        queue_container = QWidget()
        queue_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        q_lay = QVBoxLayout(queue_container)
        q_lay.setContentsMargins(0, 4, 0, 0)
        self.queue_widget = QueueWidget()
        self.queue_widget.cancel_task.connect(self._engine.cancel_task)
        q_lay.addWidget(self.queue_widget)
        self._tabs.addTab(queue_container, "Queue")

        # Tab 1: Logs (embedded)
        self.logs_widget = LogsWidget()
        self.logs_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._tabs.addTab(self.logs_widget, "Logs")

        r_lay.addWidget(self._tabs)
        splitter.addWidget(right)

        # Splitter proportions: sidebar ~220px, rest to queue
        splitter.setSizes([220, 9999])
        splitter.setStretchFactor(0, 0)   # sidebar: don't grow
        splitter.setStretchFactor(1, 1)   # queue: take all extra space

        # ── Status bar ────────────────────────────────────────────────────────
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
        self.status_lbl.setStyleSheet(
            "font-size: 11px; color: #475569; background: transparent; border: none;"
        )

        sb.addWidget(self.status_lbl)
        sb.addPermanentWidget(self.overall_bar)

    # ── Widget helpers ────────────────────────────────────────────────────────

    def _vsep(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.VLine)
        f.setStyleSheet("color: #252540; max-height: 22px; margin: 0 4px;")
        return f

    def _hsep(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setStyleSheet("color: #1e1e35; background: #1e1e35; max-height: 1px; border: none;")
        return f

    def _action_btn(self, text: str, ico: QIcon, color: str, slot) -> QPushButton:
        b = QPushButton()
        b.setIcon(ico)
        b.setIconSize(QSize(14, 14))
        b.setText(f"  {text}")
        b.setStyleSheet(
            f"QPushButton {{ background: transparent; border: 1.5px solid {color}40; "
            f"color: {color}; border-radius: 6px; padding: 5px 14px; font-weight: 600; "
            f"min-height: 26px; }}"
            f"QPushButton:hover {{ background: {color}18; border-color: {color}; }}"
            f"QPushButton:disabled {{ border-color: #252540; color: #2d2d50; }}"
        )
        b.clicked.connect(slot)
        return b

    def _icon_btn(self, ico: QIcon, tooltip: str, slot) -> QPushButton:
        b = QPushButton()
        b.setIcon(ico)
        b.setIconSize(QSize(16, 16))
        b.setObjectName("btn_icon")
        b.setFixedSize(30, 30)
        b.setToolTip(tooltip)
        b.clicked.connect(slot)
        return b

    # ── Engine signals ────────────────────────────────────────────────────────

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
        # Truly skipped = engine chose not to process (e.g. already HEVC)
        if encoder.startswith("Skipped"):
            self.stats.record_skipped(orig)
        else:
            # Always record as Done — record_done uses max(0, saved) so
            # zero-improvement files correctly show 0% savings, not "Skipped"
            self.stats.record_done(orig, new_size)
        self._update_overall()

    @Slot(str, str)
    def _on_task_error(self, task_id: str, msg: str):
        self.queue_widget.set_status(task_id, "Error")
        self.stats.record_error()

    @Slot(str)
    def _on_log(self, msg: str):
        self._logger.append(msg)
        self.logs_widget.append_line(msg)
        self.status_lbl.setText(msg[-100:] if len(msg) > 100 else msg)
        # Badge on Logs tab when not focused
        if self._tabs.currentIndex() != 1:
            cur = self._tabs.tabText(1)
            if not cur.endswith("*"):
                self._tabs.setTabText(1, cur + " *")

    @Slot()
    def _on_all_done(self):
        self._running = False
        self._paused  = False
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.status_lbl.setText("All tasks completed")
        self.overall_bar.setValue(100)
        self.stats.set_working(0)

    @Slot(str)
    def _on_hw_detected(self, summary: str):
        self.hw_lbl.setText(f"  {summary}  ")

    @Slot(int, int, int)
    def _on_stats_update(self, gpu: int, cpu: int, queued: int):
        self.perf.update_workers(gpu, cpu, queued)
        self.stats.set_working(gpu + cpu)

    # ── Tab management ────────────────────────────────────────────────────────

    def _on_tab_changed(self, idx: int):
        # Clear "new log" badge when switching to Logs tab
        if idx == 1:
            cur = self._tabs.tabText(1)
            if cur.endswith(" *"):
                self._tabs.setTabText(1, cur[:-2])

    # ── Controls ─────────────────────────────────────────────────────────────

    def _start(self):
        tasks = [t for t in self._engine.get_tasks()
                 if t.status.value in ("Queued", "Paused")]
        if not tasks:
            self.status_lbl.setText("No queued tasks — add files first")
            return
        self._running = True
        self._paused  = False
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        # Only count tasks that will actually run in this session
        self.stats.start_session(len(tasks))
        self._engine.start(self._settings.compression_settings())
        self.status_lbl.setText("Compressing…")

    def _pause(self):
        if not self._paused:
            self._engine.pause()
            self.btn_pause.setIcon(icon("play", "#f59e0b"))
            self.btn_pause.setText("  Resume")
            self._paused = True
            self.status_lbl.setText("Paused")
        else:
            self._engine.resume()
            self.btn_pause.setIcon(icon("pause", "#f59e0b"))
            self.btn_pause.setText("  Pause")
            self._paused = False
            self.status_lbl.setText("Compressing…")

    def _cancel(self):
        self._engine.cancel()
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self._running = False
        self._paused  = False
        self.status_lbl.setText("Cancelled")

    def _clear_queue(self):
        self._engine.clear_queue()
        self.queue_widget.clear_all()
        self.queue_count.setText("0 files")
        self.overall_bar.setValue(0)
        self.status_lbl.setText("Queue cleared")
        self._engine._tasks.clear()

    # ── File / folder pickers ─────────────────────────────────────────────────

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
        self.status_lbl.setText(f"Scanning {d}…")

        def _scan():
            exts  = IMAGE_EXTS | VIDEO_EXTS
            paths = [f for f in Path(d).rglob("*")
                     if f.is_file() and f.suffix.lower() in exts]
            self._paths_ready.emit(paths)

        threading.Thread(target=_scan, daemon=True).start()

    def _add_paths(self, paths: list[Path]):
        out_mode = self._settings.get("engine.output_mode", "inplace")
        out_dir  = (Path(self._settings.get("engine.output_dir", ""))
                    if out_mode == "custom" else None)

        existing  = {t.path for t in self._engine.get_tasks()}
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
            batch = items[idx:idx + 100]
            for task in batch:
                self.queue_widget.add_task(task)
            if idx + 100 < len(items):
                QTimer.singleShot(0, lambda: _add_batch(items, idx + 100))
            else:
                total = len(self._engine.get_tasks())
                self.queue_count.setText(
                    f"{total} file{'s' if total != 1 else ''}"
                )
                self.status_lbl.setText(
                    f"Added {len(new_tasks)} file(s) — total {total}"
                )

        QTimer.singleShot(0, lambda: _add_batch(new_tasks))

    # ── Dialogs ───────────────────────────────────────────────────────────────

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
        QApplication.instance().setStyleSheet(get_style(theme))
        self.btn_theme.setIcon(
            icon("sun", "#94a3b8") if theme == "dark"
            else icon("moon", "#475569")
        )

    def _on_quick_preset(self, name: str):
        quality_map = {"lossless": 100, "high": 92, "balanced": 85, "small": 70, "tiny": 55}
        vid_map     = {"lossless": 18,  "high": 22, "balanced": 28, "small": 33, "tiny": 40}
        self._settings.set("image.preset",   name)
        self._settings.set("image.quality",  quality_map.get(name, 85))
        self._settings.set("video.quality",  vid_map.get(name, 28))
        self._settings.save()

    def _sync_preset_cb(self):
        """Pull saved preset into the toolbar combo without firing the change signal."""
        saved = self._settings.get("image.preset", "balanced")
        self.preset_cb.blockSignals(True)
        self.preset_cb.setCurrentText(saved)
        self.preset_cb.blockSignals(False)

    # ── Overall progress ──────────────────────────────────────────────────────

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

    # ── Geometry persistence ──────────────────────────────────────────────────

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
        # Stop background threads before Qt tears down widgets
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
