"""Drag-and-drop zone widget with theme-aware states."""
from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Signal, QByteArray
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer


def _make_upload_icon(size: int = 40, color: str = "#3b82f6") -> QPixmap:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                 width="{size}" height="{size}" fill="none" stroke="{color}"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="17 8 12 3 7 8"/>
      <line x1="12" y1="3" x2="12" y2="15"/>
    </svg>"""
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return pix


class DropZone(QFrame):
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("drop_zone")
        self.setAcceptDrops(True)
        self.setMinimumSize(140, 105)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._theme = "dark"
        self._build_ui()
        self.set_theme("dark")

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)
        lay.setContentsMargins(12, 12, 12, 12)

        self._icon_lbl = QLabel(self)
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setStyleSheet("background: transparent; border: none;")

        self._title = QLabel("Drop files or folders", self)
        self._title.setAlignment(Qt.AlignCenter)

        self._sub = QLabel("Images and videos | Unlimited depth", self)
        self._sub.setAlignment(Qt.AlignCenter)

        lay.addWidget(self._icon_lbl)
        lay.addWidget(self._title)
        lay.addWidget(self._sub)

    def set_theme(self, theme: str):
        self._theme = theme
        accent = "#3b82f6" if theme == "dark" else "#2563eb"
        title_color = "#f4f4f5" if theme == "dark" else "#0f172a"
        sub_color = "#a1a1aa" if theme == "dark" else "#64748b"

        self._icon_lbl.setPixmap(_make_upload_icon(36, accent))
        self._title.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {title_color}; "
            "background: transparent; border: none;"
        )
        self._sub.setStyleSheet(
            f"font-size: 11px; color: {sub_color}; "
            "background: transparent; border: none;"
        )

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.setProperty("dragOver", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, e):
        self.setProperty("dragOver", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, e: QDropEvent):
        self.setProperty("dragOver", False)
        self.style().unpolish(self)
        self.style().polish(self)

        import threading
        urls = [url.toLocalFile() for url in e.mimeData().urls()]

        def _scan():
            paths: list[Path] = []
            for loc in urls:
                p = Path(loc)
                if p.is_dir():
                    paths.extend(self._scan_dir(p))
                elif p.is_file():
                    paths.append(p)
            if paths:
                self.files_dropped.emit(paths)

        threading.Thread(target=_scan, daemon=True).start()

    @staticmethod
    def _scan_dir(d: Path) -> list[Path]:
        from core.task import IMAGE_EXTS, VIDEO_EXTS
        exts = IMAGE_EXTS | VIDEO_EXTS
        return [f for f in d.rglob("*")
                if f.is_file() and f.suffix.lower() in exts]
