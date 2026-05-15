"""Per-task row widget + queue list."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QProgressBar, QPushButton, QListWidget, QListWidgetItem, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui  import QColor

from core.task  import CompressionTask, TaskStatus
from gui.icons  import icon

STATUS_COLORS = {
    "Queued":    "#475569",
    "Running":   "#38bdf8",
    "Done":      "#10b981",
    "Error":     "#f87171",
    "Skipped":   "#fbbf24",
    "Cancelled": "#64748b",
    "Paused":    "#a78bfa",
}

STATUS_DOT = {
    "Queued":    "#334155",
    "Running":   "#38bdf8",
    "Done":      "#10b981",
    "Error":     "#f87171",
    "Skipped":   "#fbbf24",
    "Cancelled": "#475569",
    "Paused":    "#a78bfa",
}


class _TypeBadge(QLabel):
    """Colored badge showing IMG or VID."""
    _IMG_STYLE = (
        "background: #1e1b4b; color: #a78bfa; font-size: 9px; font-weight: 700; "
        "letter-spacing: 0.5px; border-radius: 3px; padding: 2px 5px; border: none;"
    )
    _VID_STYLE = (
        "background: #0c1a2e; color: #38bdf8; font-size: 9px; font-weight: 700; "
        "letter-spacing: 0.5px; border-radius: 3px; padding: 2px 5px; border: none;"
    )

    def __init__(self, media_type: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 16)
        self.setAlignment(Qt.AlignCenter)
        if media_type == "image":
            self.setText("IMG")
            self.setStyleSheet(self._IMG_STYLE)
        else:
            self.setText("VID")
            self.setStyleSheet(self._VID_STYLE)


class _StatusDot(QLabel):
    """Tiny filled circle indicating task status."""
    _TMPL = (
        "border-radius: 5px; min-width: 10px; max-width: 10px; "
        "min-height: 10px; max-height: 10px; background: {color}; border: none;"
    )

    def __init__(self, status: str = "Queued", parent=None):
        super().__init__(parent)
        self.set_status(status)

    def set_status(self, status: str):
        color = STATUS_DOT.get(status, "#334155")
        self.setStyleSheet(self._TMPL.format(color=color))


class TaskRow(QWidget):
    cancel_requested = Signal(str)

    def __init__(self, task: CompressionTask, parent=None):
        super().__init__(parent)
        self.task_id = task.id
        self._build(task)

    def _build(self, task: CompressionTask):
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 8, 10, 8)
        root.setSpacing(10)

        # Type badge
        badge = _TypeBadge(task.media_type.value)

        # Center column
        center = QVBoxLayout()
        center.setSpacing(3)

        name_row = QHBoxLayout()
        name_row.setSpacing(6)

        self.name_lbl = QLabel(task.path.name)
        self.name_lbl.setStyleSheet(
            "font-weight: 600; color: #e2e8f0; background: transparent; border: none; "
            "font-size: 13px;"
        )
        self.name_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._dot = _StatusDot(task.status.value)
        name_row.addWidget(self.name_lbl)
        name_row.addStretch()
        name_row.addWidget(self._dot)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(10)

        self.status_lbl = QLabel(task.status.value)
        self.status_lbl.setStyleSheet(
            f"color: {STATUS_COLORS.get(task.status.value, '#475569')}; "
            "font-size: 11px; font-weight: 500; background: transparent; border: none;"
        )

        self.size_lbl = QLabel(CompressionTask.fmt_size(task.orig_size))
        self.size_lbl.setStyleSheet(
            "color: #475569; font-size: 11px; background: transparent; border: none;"
        )

        meta_row.addWidget(self.status_lbl)
        meta_row.addWidget(self.size_lbl)
        meta_row.addStretch()

        self.prog = QProgressBar()
        self.prog.setRange(0, 100)
        self.prog.setValue(0)
        self.prog.setFixedHeight(3)
        self.prog.setTextVisible(False)

        center.addLayout(name_row)
        center.addLayout(meta_row)
        center.addWidget(self.prog)

        # Cancel btn (X icon)
        self.cancel_btn = QPushButton()
        self.cancel_btn.setIcon(icon("close", color="#475569", size=14))
        self.cancel_btn.setIconSize(QSize(14, 14))
        self.cancel_btn.setFixedSize(24, 24)
        self.cancel_btn.setObjectName("btn_icon")
        self.cancel_btn.setToolTip("Cancel task")
        self.cancel_btn.clicked.connect(lambda: self.cancel_requested.emit(self.task_id))

        root.addWidget(badge)
        root.addLayout(center)
        root.addWidget(self.cancel_btn)

    def update_progress(self, pct: float):
        self.prog.setValue(int(pct))

    def update_status(self, status_str: str, encoder: str = ""):
        color = STATUS_COLORS.get(status_str, "#475569")
        self.status_lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; font-weight: 500; "
            "background: transparent; border: none;"
        )
        text = status_str
        if encoder:
            text += f"  [{encoder}]"
        self.status_lbl.setText(text)
        self._dot.set_status(status_str)

        if status_str in ("Done", "Error", "Skipped", "Cancelled"):
            self.cancel_btn.setVisible(False)
            self.prog.setValue(100 if status_str not in ("Error",) else 0)

    def update_sizes(self, orig: int, new_size: int):
        saved = max(0, orig - new_size)
        pct   = (saved / orig * 100) if orig else 0
        self.size_lbl.setText(
            f"{CompressionTask.fmt_size(orig)} → {CompressionTask.fmt_size(new_size)}"
            f"  ({pct:.1f}% saved)"
        )


class QueueWidget(QListWidget):
    cancel_task = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: dict[str, tuple[QListWidgetItem, TaskRow]] = {}
        self.setSpacing(2)
        self.setUniformItemSizes(False)

    def add_task(self, task: CompressionTask):
        row = TaskRow(task)
        row.cancel_requested.connect(self.cancel_task)

        item = QListWidgetItem(self)
        item.setSizeHint(QSize(0, 62))
        self.addItem(item)
        self.setItemWidget(item, row)
        self._rows[task.id] = (item, row)
        self.scrollToBottom()

    def set_progress(self, task_id: str, pct: float):
        if task_id in self._rows:
            self._rows[task_id][1].update_progress(pct)

    def set_status(self, task_id: str, status: str, encoder: str = ""):
        if task_id in self._rows:
            self._rows[task_id][1].update_status(status, encoder)

    def set_sizes(self, task_id: str, orig: int, new_size: int):
        if task_id in self._rows:
            self._rows[task_id][1].update_sizes(orig, new_size)

    def clear_all(self):
        self._rows.clear()
        self.clear()
