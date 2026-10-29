"""Live statistics dashboard with a clean, uncluttered 2x2 metric layout."""
from __future__ import annotations
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from core.task import CompressionTask


class StatsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = "dark"
        self._reset_data()
        self._build_ui()
        self.set_theme("dark")
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

    def _reset_data(self):
        self._total = 0
        self._working = 0
        self._done = 0
        self._errors = 0
        self._skipped = 0
        self._saved = 0
        self._orig_sum = 0
        self._new_sum = 0
        self._start_time: float = 0.0
        self._files_per_min: float = 0.0

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # Card container wrapping all stats
        self._card = QFrame()
        self._card.setObjectName("card")
        card_lay = QVBoxLayout(self._card)
        card_lay.setContentsMargins(12, 10, 12, 10)
        card_lay.setSpacing(8)

        # Header with title and progress bar
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        self._title = QLabel("STATISTICS")
        top_row.addWidget(self._title)
        top_row.addStretch()
        self._summary_pct = QLabel("0%")
        top_row.addWidget(self._summary_pct)
        card_lay.addLayout(top_row)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        self._progress.setObjectName("overall")
        card_lay.addWidget(self._progress)

        # 2x2 Metric Grid for scannable overview
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)
        grid.setContentsMargins(0, 2, 0, 2)

        # (0, 0) Saved
        c_saved, self._v_saved, self._l_saved = self._create_metric_cell("SAVED", "0 B (0%)")
        grid.addWidget(c_saved, 0, 0)

        # (0, 1) Files
        c_files, self._v_files, self._l_files = self._create_metric_cell("PROCESSED", "0 / 0")
        grid.addWidget(c_files, 0, 1)

        # (1, 0) Speed
        c_speed, self._v_speed, self._l_speed = self._create_metric_cell("SPEED", "-")
        grid.addWidget(c_speed, 1, 0)

        # (1, 1) Time
        c_time, self._v_time, self._l_time = self._create_metric_cell("ELAPSED", "0s")
        grid.addWidget(c_time, 1, 1)

        card_lay.addLayout(grid)

        # Divider
        self._div = QFrame()
        self._div.setFrameShape(QFrame.HLine)
        self._div.setFixedHeight(1)
        card_lay.addWidget(self._div)

        # Footer row: Active / Errors / Size change
        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(0, 0, 0, 0)
        footer_row.setSpacing(8)

        self._lbl_status = QLabel("Ready")
        footer_row.addWidget(self._lbl_status)
        footer_row.addStretch()

        self._lbl_sizes = QLabel("- -> -")
        footer_row.addWidget(self._lbl_sizes)

        card_lay.addLayout(footer_row)
        root.addWidget(self._card)

    def _create_metric_cell(self, title: str, default_val: str) -> tuple[QWidget, QLabel, QLabel]:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

        lbl = QLabel(title)
        val = QLabel(default_val)
        lay.addWidget(lbl)
        lay.addWidget(val)
        return w, val, lbl

    def set_theme(self, theme: str):
        self._theme = theme
        is_dark = theme == "dark"

        title_color = "#a1a1aa" if is_dark else "#64748b"
        lbl_color = "#71717a" if is_dark else "#64748b"
        val_color = "#f4f4f5" if is_dark else "#0f172a"
        saved_color = "#10b981" if is_dark else "#059669"
        speed_color = "#38bdf8" if is_dark else "#0284c7"
        div_color = "#38383e" if is_dark else "#e2e8f0"

        self._title.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {title_color}; "
            "letter-spacing: 0.8px; background: transparent; border: none;"
        )
        self._summary_pct.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {saved_color}; "
            "background: transparent; border: none;"
        )
        self._div.setStyleSheet(f"background: {div_color}; border: none;")

        for lbl in (self._l_saved, self._l_files, self._l_speed, self._l_time):
            lbl.setStyleSheet(
                f"font-size: 9px; font-weight: 700; color: {lbl_color}; "
                "letter-spacing: 0.5px; background: transparent; border: none;"
            )

        self._v_saved.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {saved_color}; "
            "background: transparent; border: none;"
        )
        self._v_files.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {val_color}; "
            "background: transparent; border: none;"
        )
        self._v_speed.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {speed_color}; "
            "background: transparent; border: none;"
        )
        self._v_time.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {val_color}; "
            "background: transparent; border: none;"
        )

        self._lbl_status.setStyleSheet(
            f"font-size: 10px; font-weight: 500; color: {lbl_color}; "
            "background: transparent; border: none;"
        )
        self._lbl_sizes.setStyleSheet(
            f"font-size: 10px; font-weight: 500; color: {lbl_color}; "
            "background: transparent; border: none;"
        )

    def start_session(self, total: int):
        self._reset_data()
        self._total = total
        self._start_time = time.time()
        self._refresh()

    def record_done(self, orig: int, new_size: int):
        self._done += 1
        self._orig_sum += orig
        self._new_sum += new_size
        self._saved += max(0, orig - new_size)
        self._refresh()

    def record_error(self):
        self._errors += 1
        self._refresh()

    def record_skipped(self, orig: int):
        self._skipped += 1
        self._orig_sum += orig
        self._new_sum += orig
        self._refresh()

    def set_working(self, n: int):
        if self._working != n:
            self._working = n
            self._refresh()

    def _tick(self):
        if self._start_time:
            self._refresh()

    def _refresh(self):
        ratio = (self._saved / self._orig_sum * 100) if self._orig_sum else 0
        self._v_saved.setText(f"{CompressionTask.fmt_size(self._saved)} ({ratio:.0f}%)")
        self._summary_pct.setText(f"{ratio:.1f}%")

        finished = self._done + self._errors + self._skipped
        self._v_files.setText(f"{finished} / {self._total}")

        elapsed = int(time.time() - self._start_time) if self._start_time else 0
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        elapsed_str = f"{h}h{m:02d}m" if h else f"{m}m{s:02d}s" if m else f"{s}s"

        remaining = self._total - finished
        if finished > 0 and elapsed > 0:
            rate = finished / elapsed * 60
            self._files_per_min = rate
            self._v_speed.setText(f"{rate:.1f}/min")
            if remaining > 0:
                eta = int(remaining / (finished / elapsed))
                eh, er = divmod(eta, 3600)
                em, es = divmod(er, 60)
                eta_str = f"{eh}h{em:02d}m" if eh else f"{em}m{es:02d}s" if em else f"{es}s"
                self._v_time.setText(f"{elapsed_str} (ETA {eta_str})")
            else:
                self._v_time.setText(f"{elapsed_str} (Done)")
        else:
            self._v_speed.setText("-")
            self._v_time.setText(elapsed_str)

        # Progress bar
        if self._total > 0:
            self._progress.setValue(int(finished / self._total * 100))

        # Status text
        parts = []
        if self._working > 0:
            parts.append(f"Active: {self._working}")
        if self._errors > 0:
            parts.append(f"Errors: {self._errors}")
        if self._skipped > 0:
            parts.append(f"Skipped: {self._skipped}")
        self._lbl_status.setText(" | ".join(parts) if parts else ("Idle" if finished == self._total else "Ready"))

        # Sizes text
        if self._orig_sum > 0:
            self._lbl_sizes.setText(
                f"{CompressionTask.fmt_size(self._orig_sum)} -> {CompressionTask.fmt_size(self._new_sum)}"
            )
        else:
            self._lbl_sizes.setText("- -> -")
