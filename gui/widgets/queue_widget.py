"""Queue widget with model/view for efficient large-queue rendering."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QListView, QStyledItemDelegate, QWidget, QVBoxLayout, QStyle,
)
from PySide6.QtCore import Qt, Signal, QSize, QRect, QAbstractListModel, QModelIndex
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QFontMetrics, QMouseEvent,
)

from core.task import CompressionTask


STATUS_COLORS_DARK = {
    "Queued":    "#a1a1aa",
    "Running":   "#38bdf8",
    "Done":      "#10b981",
    "Error":     "#ef4444",
    "Skipped":   "#f59e0b",
    "Cancelled": "#71717a",
    "Paused":    "#a1a1aa",
}

STATUS_COLORS_LIGHT = {
    "Queued":    "#64748b",
    "Running":   "#0284c7",
    "Done":      "#059669",
    "Error":     "#dc2626",
    "Skipped":   "#d97706",
    "Cancelled": "#94a3b8",
    "Paused":    "#64748b",
}

STATUS_DOT_DARK = {
    "Queued":    "#52525b",
    "Running":   "#38bdf8",
    "Done":      "#10b981",
    "Error":     "#ef4444",
    "Skipped":   "#f59e0b",
    "Cancelled": "#52525b",
    "Paused":    "#a1a1aa",
}

STATUS_DOT_LIGHT = {
    "Queued":    "#94a3b8",
    "Running":   "#0284c7",
    "Done":      "#059669",
    "Error":     "#dc2626",
    "Skipped":   "#d97706",
    "Cancelled": "#cbd5e1",
    "Paused":    "#64748b",
}

_TASK_ID   = Qt.UserRole + 1
_TASK_NAME = Qt.UserRole + 2
_TASK_TYPE = Qt.UserRole + 3
_TASK_ST   = Qt.UserRole + 4
_TASK_ORIG = Qt.UserRole + 5
_TASK_NEW  = Qt.UserRole + 6
_TASK_PCT  = Qt.UserRole + 7
_TASK_ENC  = Qt.UserRole + 8


class TaskModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks: list[dict] = []

    def rowCount(self, parent=QModelIndex()):
        return len(self.tasks)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.tasks):
            return None
        t = self.tasks[index.row()]
        if role == _TASK_ID:   return t["id"]
        if role == _TASK_NAME: return t["name"]
        if role == _TASK_TYPE: return t["type"]
        if role == _TASK_ST:   return t["status"]
        if role == _TASK_ORIG: return t["orig"]
        if role == _TASK_NEW:  return t["new"]
        if role == _TASK_PCT:  return t["pct"]
        if role == _TASK_ENC:  return t.get("enc", "")
        return None

    def add_task(self, task: CompressionTask):
        self.beginInsertRows(QModelIndex(), len(self.tasks), len(self.tasks))
        self.tasks.append({
            "id":     task.id,
            "name":   task.path.name,
            "type":   task.media_type.value,
            "status": task.status.value,
            "orig":   task.orig_size,
            "new":    0,
            "pct":    0.0,
            "enc":    "",
        })
        self.endInsertRows()

    def add_tasks(self, tasks: list[CompressionTask]):
        if not tasks:
            return
        start_idx = len(self.tasks)
        end_idx = start_idx + len(tasks) - 1
        self.beginInsertRows(QModelIndex(), start_idx, end_idx)
        for task in tasks:
            self.tasks.append({
                "id":     task.id,
                "name":   task.path.name,
                "type":   task.media_type.value,
                "status": task.status.value,
                "orig":   task.orig_size,
                "new":    0,
                "pct":    0.0,
                "enc":    "",
            })
        self.endInsertRows()

    def _find(self, task_id: str) -> int | None:
        for i, t in enumerate(self.tasks):
            if t["id"] == task_id:
                return i
        return None

    def update_progress(self, task_id: str, pct: float):
        idx = self._find(task_id)
        if idx is None:
            return
        self.tasks[idx]["pct"] = pct
        ix = self.index(idx)
        self.dataChanged.emit(ix, ix, [_TASK_PCT])

    def update_status(self, task_id: str, status: str, encoder: str = ""):
        idx = self._find(task_id)
        if idx is None:
            return
        self.tasks[idx]["status"] = status
        self.tasks[idx]["enc"] = encoder
        if status in ("Done", "Error", "Skipped", "Cancelled"):
            self.tasks[idx]["pct"] = 100.0 if status != "Error" else 0.0
        ix = self.index(idx)
        self.dataChanged.emit(ix, ix, [_TASK_ST, _TASK_ENC, _TASK_PCT])

    def update_sizes(self, task_id: str, orig: int, new_size: int):
        idx = self._find(task_id)
        if idx is None:
            return
        self.tasks[idx]["orig"] = orig
        self.tasks[idx]["new"]  = new_size
        ix = self.index(idx)
        self.dataChanged.emit(ix, ix, [_TASK_ORIG, _TASK_NEW])

    def clear_all(self):
        self.beginResetModel()
        self.tasks.clear()
        self.endResetModel()


class TaskDelegate(QStyledItemDelegate):
    cancel_requested = Signal(str)

    ROW_H = 62
    _FONT_NAME = QFont("Segoe UI", 12)
    _FONT_META = QFont("Segoe UI", 11)
    _FONT_BADGE = QFont("Segoe UI", 9)
    _FONT_NAME.setWeight(QFont.Weight.DemiBold)
    _FONT_META.setWeight(QFont.Weight.Medium)
    _FONT_BADGE.setWeight(QFont.Weight.Bold)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = "dark"
        self._apply_palette()

    def set_theme(self, theme: str):
        self._theme = theme
        self._apply_palette()

    def _apply_palette(self):
        if self._theme == "dark":
            self._name_color = QColor("#f4f4f5")
            self._size_color = QColor("#a1a1aa")
            self._cancel_color = QColor("#71717a")
            self._cancel_hover = QColor("#3f3f46")
            self._bar_bg = QColor("#27272a")
            self._hover_bg = QColor(255, 255, 255, 12)
            self._img_bg = QColor("#1e293b")
            self._img_fg = QColor("#60a5fa")
            self._vid_bg = QColor("#1e293b")
            self._vid_fg = QColor("#38bdf8")
            self._status_colors = STATUS_COLORS_DARK
            self._dot_colors = STATUS_DOT_DARK
        else:
            self._name_color = QColor("#0f172a")
            self._size_color = QColor("#475569")
            self._cancel_color = QColor("#64748b")
            self._cancel_hover = QColor("#e2e8f0")
            self._bar_bg = QColor("#e2e8f0")
            self._hover_bg = QColor(0, 0, 0, 10)
            self._img_bg = QColor("#eff6ff")
            self._img_fg = QColor("#2563eb")
            self._vid_bg = QColor("#f0f9ff")
            self._vid_fg = QColor("#0284c7")
            self._status_colors = STATUS_COLORS_LIGHT
            self._dot_colors = STATUS_DOT_LIGHT

    def sizeHint(self, option, index):
        return QSize(0, self.ROW_H)

    def _status_color(self, status: str) -> QColor:
        return QColor(self._status_colors.get(status, "#a1a1aa"))

    def _dot_color(self, status: str) -> QColor:
        return QColor(self._dot_colors.get(status, "#52525b"))

    def _progress_color(self, status: str) -> QColor:
        if status == "Done":
            return QColor("#10b981")
        if status == "Error":
            return QColor("#ef4444")
        if status == "Skipped":
            return QColor("#f59e0b")
        return QColor("#3b82f6" if self._theme == "dark" else "#2563eb")

    def _get_cancel_rect(self, rect: QRect) -> QRect:
        btn_size = 28
        btn_x = rect.right() - 10 - btn_size
        btn_y = rect.y() + (self.ROW_H - btn_size) // 2
        return QRect(btn_x, btn_y, btn_size, btn_size)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        r = option.rect
        status = index.data(_TASK_ST)
        pct = index.data(_TASK_PCT) or 0.0
        name = index.data(_TASK_NAME) or ""
        mtype = index.data(_TASK_TYPE) or "image"
        orig = index.data(_TASK_ORIG) or 0
        new_s = index.data(_TASK_NEW) or 0
        enc = index.data(_TASK_ENC) or ""

        is_done = status in ("Done", "Error", "Skipped", "Cancelled")
        is_hover = bool(option.state & QStyle.State_MouseOver)

        if is_hover:
            painter.fillRect(r, self._hover_bg)

        ml, mr, mt, mb = 12, 10, 8, 8
        cx = r.x() + ml
        content_top = r.y() + mt
        content_h = self.ROW_H - mt - mb

        cancel_rect = self._get_cancel_rect(r)

        badge_w, badge_h = 32, 18
        badge_x = cx
        badge_y = content_top + (content_h - badge_h) // 2
        badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)

        text_l = badge_rect.right() + 10
        text_r = cancel_rect.left() - 8

        fmn = QFontMetrics(self._FONT_NAME)
        name_y = content_top + 1
        name_h = fmn.height()

        dot_s = 8
        dot_x = text_r - dot_s
        dot_y = name_y + (name_h - dot_s) // 2

        name_max_w = dot_x - text_l - 6

        fmm = QFontMetrics(self._FONT_META)
        meta_y = name_y + name_h + 1
        meta_h = fmm.height()

        bar_y = meta_y + meta_h + 3
        bar_h = 3

        # Draw type badge
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._img_bg if mtype == "image" else self._vid_bg)
        painter.drawRoundedRect(badge_rect, 4, 4)
        painter.setFont(self._FONT_BADGE)
        painter.setPen(self._img_fg if mtype == "image" else self._vid_fg)
        painter.drawText(badge_rect, Qt.AlignCenter, "IMG" if mtype == "image" else "VID")
        painter.restore()

        # Draw filename
        painter.save()
        painter.setFont(self._FONT_NAME)
        painter.setPen(self._name_color)
        elided = fmn.elidedText(name, Qt.ElideRight, name_max_w)
        painter.drawText(text_l, name_y, name_max_w, name_h,
                         Qt.AlignLeft | Qt.AlignVCenter, elided)
        painter.restore()

        # Draw status dot
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._dot_color(status))
        painter.drawEllipse(dot_x, dot_y, dot_s, dot_s)
        painter.restore()

        # Draw status label and encoder info
        meta_text = status
        if enc:
            meta_text += f" [{enc}]"
        painter.save()
        painter.setFont(self._FONT_META)
        painter.setPen(self._status_color(status))
        painter.drawText(text_l, meta_y, text_r - text_l, meta_h,
                         Qt.AlignLeft | Qt.AlignVCenter, meta_text)
        painter.restore()

        # Draw size and ratio info
        size_str = CompressionTask.fmt_size(orig)
        if is_done and new_s > 0:
            saved = max(0, orig - new_s)
            spct = (saved / orig * 100) if orig else 0
            size_str = f"{CompressionTask.fmt_size(orig)} -> {CompressionTask.fmt_size(new_s)} ({spct:.1f}% saved)"
        painter.save()
        painter.setFont(self._FONT_META)
        painter.setPen(self._size_color)
        tw = fmm.horizontalAdvance(size_str)
        painter.drawText(text_r - tw, meta_y, tw, meta_h,
                         Qt.AlignLeft | Qt.AlignVCenter, size_str)
        painter.restore()

        # Draw progress bar
        bar_l = text_l
        bar_w = text_r - text_l
        bar_rect = QRect(bar_l, bar_y, bar_w, bar_h)
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._bar_bg)
        painter.drawRoundedRect(bar_rect, 1, 1)
        if pct > 0:
            fill_w = int(bar_w * pct / 100.0)
            fill_rect = QRect(bar_l, bar_y, fill_w, bar_h)
            painter.setBrush(self._progress_color(status))
            painter.drawRoundedRect(fill_rect, 1, 1)
        painter.restore()

        # Draw cancel button for active tasks
        if not is_done:
            if is_hover:
                painter.save()
                painter.setPen(Qt.NoPen)
                painter.setBrush(self._cancel_hover)
                painter.drawRoundedRect(cancel_rect, 6, 6)
                painter.restore()
            painter.save()
            painter.setPen(QPen(self._cancel_color, 1.5))
            m = 8
            painter.drawLine(cancel_rect.left() + m, cancel_rect.top() + m,
                             cancel_rect.right() - m, cancel_rect.bottom() - m)
            painter.drawLine(cancel_rect.left() + m, cancel_rect.bottom() - m,
                             cancel_rect.right() - m, cancel_rect.top() + m)
            painter.restore()

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QMouseEvent.Type.MouseButtonRelease:
            status = index.data(_TASK_ST)
            if status and status in ("Done", "Error", "Skipped", "Cancelled"):
                return False
            cancel_rect = self._get_cancel_rect(option.rect)
            if cancel_rect.contains(event.pos()):
                tid = index.data(_TASK_ID)
                if tid:
                    self.cancel_requested.emit(tid)
                return True
        return super().editorEvent(event, model, option, index)


class QueueWidget(QWidget):
    cancel_task = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = TaskModel()
        self._delegate = TaskDelegate()
        self._delegate.cancel_requested.connect(self.cancel_task)

        self._view = QListView()
        self._view.setModel(self._model)
        self._view.setItemDelegate(self._delegate)
        self._view.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setSelectionMode(QListView.SelectionMode.NoSelection)
        self._view.setFrameShape(QListView.Shape.NoFrame)
        self._view.setMouseTracking(True)
        self._view.setStyleSheet("""
            QListView { background: transparent; border: none; }
            QListView::item { background: transparent; border: none; }
            QListView::item:hover { background: transparent; }
            QListView::item:selected { background: transparent; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)

    def set_theme(self, theme: str):
        self._delegate.set_theme(theme)
        sb_handle = "#38383e" if theme == "dark" else "#cbd5e1"
        sb_hover = "#52525b" if theme == "dark" else "#94a3b8"
        self._view.verticalScrollBar().setStyleSheet(f"""
            QScrollBar:vertical {{
                background: transparent; width: 6px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {sb_handle}; border-radius: 3px; min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {sb_hover}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0; background: none;
            }}
        """)
        self._view.viewport().update()

    def add_task(self, task: CompressionTask):
        self._model.add_task(task)

    def add_tasks(self, tasks: list[CompressionTask]):
        self._model.add_tasks(tasks)

    def set_progress(self, task_id: str, pct: float):
        self._model.update_progress(task_id, pct)

    def set_status(self, task_id: str, status: str, encoder: str = ""):
        self._model.update_status(task_id, status, encoder)
        if status == "Done":
            self._view.scrollToBottom()

    def set_sizes(self, task_id: str, orig: int, new_size: int):
        self._model.update_sizes(task_id, orig, new_size)

    def clear_all(self):
        self._model.clear_all()

    @property
    def row_count(self) -> int:
        return self._model.rowCount()
