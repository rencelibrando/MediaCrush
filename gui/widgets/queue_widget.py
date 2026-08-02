"""Queue widget with model/view for efficient large-queue rendering."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QListView, QStyledItemDelegate, QSizePolicy, QWidget, QVBoxLayout,
    QStyle,
)
from PySide6.QtCore import Qt, Signal, QSize, QRect, QAbstractListModel, QModelIndex
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QFontMetrics, QMouseEvent,
)

from core.task import CompressionTask


STATUS_COLORS = {
    "Queued":    "#475569",
    "Running":   "#38bdf8",
    "Done":      "#10b981",
    "Error":     "#f87171",
    "Skipped":   "#14b8a6",
    "Cancelled": "#64748b",
    "Paused":    "#a78bfa",
}

STATUS_DOT = {
    "Queued":    "#334155",
    "Running":   "#38bdf8",
    "Done":      "#10b981",
    "Error":     "#f87171",
    "Skipped":   "#14b8a6",
    "Cancelled": "#475569",
    "Paused":    "#a78bfa",
}

# ── Model roles ──────────────────────────────────────────────────────────────
_TASK_ID   = Qt.UserRole + 1
_TASK_NAME = Qt.UserRole + 2
_TASK_TYPE = Qt.UserRole + 3
_TASK_ST   = Qt.UserRole + 4  # status string
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


# ── Delegate ──────────────────────────────────────────────────────────────────

class TaskDelegate(QStyledItemDelegate):
    cancel_requested = Signal(str)

    ROW_H  = 62
    _FONT_NAME   = QFont("Segoe UI", 13)
    _FONT_META   = QFont("Segoe UI", 11)
    _FONT_BADGE  = QFont("Segoe UI", 9)
    _FONT_NAME.setWeight(QFont.Weight.DemiBold)
    _FONT_META.setWeight(QFont.Weight.Medium)
    _FONT_BADGE.setWeight(QFont.Weight.Bold)

    _IMG_BG   = QColor("#1e1b4b")
    _IMG_FG   = QColor("#a78bfa")
    _VID_BG   = QColor("#0c1a2e")
    _VID_FG   = QColor("#38bdf8")
    _NAME_COLOR  = QColor("#e2e8f0")
    _SIZE_COLOR  = QColor("#475569")
    _CANCEL_COLOR = QColor("#475569")
    _BAR_BG   = QColor("#1e293b")
    _PROGRESS_COLORS = {
        "Queued":    QColor("#334155"),
        "Running":   QColor("#38bdf8"),
        "Done":      QColor("#10b981"),
        "Error":     QColor("#f87171"),
        "Skipped":   QColor("#14b8a6"),
        "Cancelled": QColor("#64748b"),
        "Paused":    QColor("#a78bfa"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)

    def sizeHint(self, option, index):
        return QSize(0, self.ROW_H)

    def _status_color(self, status: str) -> QColor:
        c = STATUS_COLORS.get(status, "#475569")
        return QColor(c)

    def _dot_color(self, status: str) -> QColor:
        c = STATUS_DOT.get(status, "#334155")
        return QColor(c)

    def _progress_color(self, status: str, pct: float) -> QColor:
        c = self._PROGRESS_COLORS.get(status)
        if c:
            return c
        return QColor("#38bdf8")

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        r      = option.rect
        status = index.data(_TASK_ST)
        pct    = index.data(_TASK_PCT) or 0.0
        name   = index.data(_TASK_NAME) or ""
        mtype  = index.data(_TASK_TYPE) or "image"
        orig   = index.data(_TASK_ORIG) or 0
        new_s  = index.data(_TASK_NEW) or 0
        enc    = index.data(_TASK_ENC) or ""

        is_done   = status in ("Done", "Error", "Skipped", "Cancelled")
        is_hover  = option.state & QStyle.State_MouseOver

        # ── Background (subtle hover) ────────────────────────────────────────
        if is_hover:
            painter.fillRect(r, QColor("#ffffff08"))

        # ── Layout positions ─────────────────────────────────────────────────
        ml, mr, mt, mb = 12, 10, 8, 8
        cx = r.x() + ml
        content_top = r.y() + mt
        content_h   = self.ROW_H - mt - mb

        # Cancel button
        cancel_size = 24
        cancel_x = r.right() - mr - cancel_size
        self._cancel_rect = QRect(cancel_x, content_top + (content_h - cancel_size) // 2,
                                  cancel_size, cancel_size)

        # Badge: IMG / VID
        badge_w, badge_h = 30, 16
        badge_x = cx
        badge_y = content_top + (content_h - badge_h) // 2
        badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)

        # Content area between badge and cancel
        text_l = badge_rect.right() + 10
        text_r = self._cancel_rect.left() - 6

        # Name line
        fmn = QFontMetrics(self._FONT_NAME)
        name_y = content_top + 1
        name_h = fmn.height()  # ~18

        # Dot position
        dot_s = 10
        dot_x = text_r - dot_s
        dot_y = name_y + (name_h - dot_s) // 2

        # Name text available width
        name_max_w = dot_x - text_l - 4

        # Meta line
        fmm = QFontMetrics(self._FONT_META)
        meta_y = name_y + name_h + 1
        meta_h = fmm.height()  # ~14

        # Progress bar
        bar_y = meta_y + meta_h + 3
        bar_h = 3

        # ── Draw badge ───────────────────────────────────────────────────────
        painter.save()
        painter.setPen(Qt.NoPen)
        if mtype == "image":
            painter.setBrush(self._IMG_BG)
        else:
            painter.setBrush(self._VID_BG)
        painter.drawRoundedRect(badge_rect, 3, 3)
        painter.restore()

        painter.save()
        painter.setFont(self._FONT_BADGE)
        painter.setPen(self._IMG_FG if mtype == "image" else self._VID_FG)
        painter.drawText(badge_rect, Qt.AlignCenter, "IMG" if mtype == "image" else "VID")
        painter.restore()

        # ── Draw name (with ellipsis) ────────────────────────────────────────
        painter.save()
        painter.setFont(self._FONT_NAME)
        painter.setPen(self._NAME_COLOR)
        elided = fmn.elidedText(name, Qt.ElideRight, name_max_w)
        painter.drawText(text_l, name_y, name_max_w, name_h,
                         Qt.AlignLeft | Qt.AlignVCenter, elided)
        painter.restore()

        # ── Draw status dot ───────────────────────────────────────────────────
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._dot_color(status))
        painter.drawEllipse(dot_x, dot_y, dot_s, dot_s)
        painter.restore()

        # ── Draw meta text ────────────────────────────────────────────────────
        meta_text = status
        if enc:
            meta_text += f"  [{enc}]"
        painter.save()
        painter.setFont(self._FONT_META)
        painter.setPen(self._status_color(status))
        painter.drawText(text_l, meta_y, text_r - text_l, meta_h,
                         Qt.AlignLeft | Qt.AlignVCenter, meta_text)
        painter.restore()

        # Size text
        size_str = CompressionTask.fmt_size(orig)
        if is_done and new_s > 0:
            saved = max(0, orig - new_s)
            spct  = (saved / orig * 100) if orig else 0
            size_str = f"{CompressionTask.fmt_size(orig)} → {CompressionTask.fmt_size(new_s)}  ({spct:.1f}% saved)"
        painter.save()
        painter.setFont(self._FONT_META)
        painter.setPen(self._SIZE_COLOR)
        tw = fmm.horizontalAdvance(size_str)
        painter.drawText(text_r - tw, meta_y, tw, meta_h,
                         Qt.AlignLeft | Qt.AlignVCenter, size_str)
        painter.restore()

        # ── Draw progress bar ────────────────────────────────────────────────
        bar_l = text_l
        bar_w = text_r - text_l
        bar_rect = QRect(bar_l, bar_y, bar_w, bar_h)
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._BAR_BG)
        painter.drawRoundedRect(bar_rect, 1, 1)
        if pct > 0:
            fill_w = int(bar_w * pct / 100.0)
            fill_rect = QRect(bar_l, bar_y, fill_w, bar_h)
            painter.setBrush(self._progress_color(status, pct))
            painter.drawRoundedRect(fill_rect, 1, 1)
        painter.restore()

        # ── Draw cancel button ───────────────────────────────────────────────
        if not is_done:
            cancel_rect = self._cancel_rect
            if is_hover:
                painter.save()
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor("#ffffff10"))
                painter.drawRoundedRect(cancel_rect, 4, 4)
                painter.restore()
            # Draw X mark
            painter.save()
            painter.setPen(QPen(self._CANCEL_COLOR, 1.5))
            margin = 5
            painter.drawLine(cancel_rect.left() + margin, cancel_rect.top() + margin,
                             cancel_rect.right() - margin, cancel_rect.bottom() - margin)
            painter.drawLine(cancel_rect.left() + margin, cancel_rect.bottom() - margin,
                             cancel_rect.right() - margin, cancel_rect.top() + margin)
            painter.restore()

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QMouseEvent.Type.MouseButtonRelease:
            status = index.data(_TASK_ST)
            if status and status in ("Done", "Error", "Skipped", "Cancelled"):
                return False
            r = option.rect
            cancel_x = r.right() - 10 - 24
            cancel_y = r.y() + 8 + (62 - 8 - 8 - 24) // 2
            cancel_rect = QRect(cancel_x, cancel_y, 24, 24)
            if cancel_rect.contains(event.pos()):
                tid = index.data(_TASK_ID)
                if tid:
                    self.cancel_requested.emit(tid)
                return True
        return super().editorEvent(event, model, option, index)


# ── Queue widget ─────────────────────────────────────────────────────────────

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

        self._view.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                background: transparent; width: 8px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #334155; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #475569; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0; background: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)

    def add_task(self, task: CompressionTask):
        self._model.add_task(task)

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
