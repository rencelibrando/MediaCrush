"""Live statistics dashboard — responsive row-based layout, no grid distortion."""
from __future__ import annotations
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from core.task import CompressionTask


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setStyleSheet("color: #1e1e35; background: #1e1e35; max-height: 1px; border: none;")
    return f


def _stat_row(label: str, value: str = "—",
              val_color: str = "#a78bfa") -> tuple[QWidget, QLabel]:
    row = QWidget()
    row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 3, 0, 3)
    lay.setSpacing(4)

    lbl = QLabel(label)
    lbl.setStyleSheet(
        "font-size: 10px; font-weight: 600; color: #475569; "
        "background: transparent; border: none; "
        "letter-spacing: 0.5px;"
    )
    lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    lbl.setMinimumWidth(64)
    lbl.setFixedWidth(84)

    val = QLabel(value)
    val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    val.setStyleSheet(
        f"font-size: 12px; font-weight: 700; color: {val_color}; "
        "background: transparent; border: none;"
    )
    val.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    lay.addWidget(lbl)
    lay.addWidget(val)
    return row, val


class StatsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._reset_data()
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

    def _reset_data(self):
        self._total    = 0
        self._working  = 0
        self._done     = 0
        self._errors   = 0
        self._skipped  = 0
        self._saved    = 0
        self._orig_sum = 0
        self._new_sum  = 0
        self._start_time: float = 0.0
        self._files_per_min: float = 0.0

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Title ─────────────────────────────────────────────────────────────
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 6)
        t = QLabel("Statistics")
        t.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #64748b; "
            "letter-spacing: 1px; background: transparent; border: none;"
        )
        title_row.addWidget(t)
        title_row.addStretch()
        root.addLayout(title_row)

        # ── Progress bar ──────────────────────────────────────────────────────
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        self._progress.setObjectName("overall")
        root.addWidget(self._progress)
        root.addSpacing(8)

        # ── Stat rows ─────────────────────────────────────────────────────────
        rows_data = [
            ("TOTAL",    "0",   "#a78bfa"),
            ("WORKING",  "0",   "#f59e0b"),
            ("DONE",     "0",   "#10b981"),
            ("ERRORS",   "0",   "#f87171"),
            ("SKIPPED",  "0",   "#fbbf24"),
            ("SAVED",    "0 B", "#38bdf8"),
            ("RATIO",    "0%",  "#a78bfa"),
            ("ELAPSED",  "0s",  "#64748b"),
            ("ETA",      "—",   "#64748b"),
            ("RATE",     "—",   "#64748b"),
        ]

        self._vals: dict[str, QLabel] = {}
        for i, (lbl, val, color) in enumerate(rows_data):
            if i in (5, 7):                     # separator before SAVED, ELAPSED
                root.addWidget(_sep())
            w, v = _stat_row(lbl, val, color)
            root.addWidget(w)
            self._vals[lbl] = v

        root.addWidget(_sep())

        # ── Before / After block ──────────────────────────────────────────────
        ba = QFrame()
        ba.setObjectName("card")
        ba_lay = QVBoxLayout(ba)
        ba_lay.setContentsMargins(10, 6, 10, 6)
        ba_lay.setSpacing(2)

        ba_title = QLabel("SIZE CHANGE")
        ba_title.setStyleSheet(
            "font-size: 9px; font-weight: 700; color: #334155; "
            "letter-spacing: 1px; background: transparent; border: none;"
        )
        ba_lay.addWidget(ba_title)

        row_b, self._v_before = _stat_row("BEFORE", "—", "#64748b")
        row_a, self._v_after  = _stat_row("AFTER",  "—", "#10b981")
        ba_lay.addWidget(row_b)
        ba_lay.addWidget(row_a)
        root.addWidget(ba)

    # ── Public API ────────────────────────────────────────────────────────────

    def start_session(self, total: int):
        self._reset_data()
        self._total      = total
        self._start_time = time.time()
        self._refresh()

    def record_done(self, orig: int, new_size: int):
        self._done     += 1
        self._orig_sum += orig
        self._new_sum  += new_size
        self._saved    += max(0, orig - new_size)
        self._refresh()

    def record_error(self):
        self._errors += 1
        self._refresh()

    def record_skipped(self, orig: int):
        self._skipped  += 1
        self._orig_sum += orig
        self._new_sum  += orig
        self._refresh()

    def set_working(self, n: int):
        """Called with active worker count from engine stats_update signal."""
        if self._working != n:
            self._working = n
            self._vals["WORKING"].setText(str(n) if n > 0 else "—")

    # ── Internal ─────────────────────────────────────────────────────────────

    def _tick(self):
        # Always refresh while a session is active (start_time set)
        if self._start_time:
            self._refresh()

    def _refresh(self):
        v = self._vals
        v["TOTAL"].setText(str(self._total))
        v["WORKING"].setText(str(self._working) if self._working > 0 else "—")
        v["DONE"].setText(str(self._done))
        v["ERRORS"].setText(str(self._errors))
        v["SKIPPED"].setText(str(self._skipped))
        v["SAVED"].setText(CompressionTask.fmt_size(self._saved))

        ratio = (self._saved / self._orig_sum * 100) if self._orig_sum else 0
        v["RATIO"].setText(f"{ratio:.1f}%")

        elapsed = int(time.time() - self._start_time) if self._start_time else 0
        h, rem = divmod(elapsed, 3600)
        m, s   = divmod(rem, 60)
        v["ELAPSED"].setText(
            f"{h}h{m:02d}m" if h else f"{m}m{s:02d}s" if m else f"{s}s"
        )

        finished = self._done + self._errors + self._skipped
        remaining = self._total - finished
        if finished > 0 and elapsed > 0:
            rate = finished / elapsed * 60     # files/min
            self._files_per_min = rate
            v["RATE"].setText(f"{rate:.1f}/min")
            if remaining > 0:
                eta = int(remaining / (finished / elapsed))
                eh, er = divmod(eta, 3600)
                em, es = divmod(er, 60)
                v["ETA"].setText(
                    f"{eh}h{em:02d}m" if eh else
                    f"{em}m{es:02d}s" if em else f"{es}s"
                )
            else:
                v["ETA"].setText("Done")
        else:
            v["RATE"].setText("—")
            v["ETA"].setText("—")

        # Progress bar
        if self._total > 0:
            self._progress.setValue(int(finished / self._total * 100))

        # Before / After
        self._v_before.setText(CompressionTask.fmt_size(self._orig_sum))
        self._v_after.setText(CompressionTask.fmt_size(self._new_sum))
