"""Drag-and-drop zone widget."""
from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore    import Qt, Signal
from PySide6.QtGui     import QDragEnterEvent, QDropEvent, QPixmap, QPainter
from PySide6.QtSvg     import QSvgRenderer
from PySide6.QtCore    import QByteArray


_UPLOAD_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"
     width="48" height="48" fill="none">
  <path d="M24 32V16M24 16L17 23M24 16L31 23" stroke="#4c1d95" stroke-width="2.5"
        stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M8 36c0 2.2 1.8 4 4 4h24c2.2 0 4-1.8 4-4" stroke="#4c1d95"
        stroke-width="2.5" stroke-linecap="round"/>
</svg>"""


def _make_upload_icon(size: int = 48) -> QPixmap:
    renderer = QSvgRenderer(QByteArray(_UPLOAD_SVG.encode()))
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return pix


class DropZone(QFrame):
    files_dropped = Signal(list)  # list[Path]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setAcceptDrops(True)
        self.setMinimumSize(140, 100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)

        icon_lbl = QLabel(self)
        icon_lbl.setPixmap(_make_upload_icon(40))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")

        title = QLabel("Drop files or folders", self)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 13px; font-weight: 600; "
            "color: #64748b; background: transparent; border: none;"
        )

        sub = QLabel("Images & videos  •  Unlimited depth", self)
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(
            "font-size: 10px; color: #334155; "
            "background: transparent; border: none;"
        )

        lay.addWidget(icon_lbl)
        lay.addWidget(title)
        lay.addWidget(sub)

    # ── Drag & drop ──────────────────────────────────────────────────────────

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.setStyleSheet(
                "QFrame#panel { background-color: #1e1b4b; "
                "border: 2px dashed #6d28d9; border-radius: 10px; }"
            )

    def dragLeaveEvent(self, e):
        self.setStyleSheet("")

    def dropEvent(self, e: QDropEvent):
        self.setStyleSheet("")
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
