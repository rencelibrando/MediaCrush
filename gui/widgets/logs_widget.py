"""Logs panel with real-time streaming, search, and theme-aware formatting."""
from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QFileDialog, QLineEdit
)
from PySide6.QtGui import QTextCursor, QFont


_HTML_COLORS_DARK = {
    "ok":    "#10b981",
    "error": "#ef4444",
    "skip":  "#f59e0b",
    "gpu":   "#38bdf8",
    "cpu":   "#60a5fa",
    "info":  "#a1a1aa",
    "warn":  "#f59e0b",
    "start": "#f4f4f5",
}

_HTML_COLORS_LIGHT = {
    "ok":    "#059669",
    "error": "#dc2626",
    "skip":  "#d97706",
    "gpu":   "#0284c7",
    "cpu":   "#2563eb",
    "info":  "#475569",
    "warn":  "#d97706",
    "start": "#0f172a",
}


def _classify(msg: str) -> str:
    ml = msg.lower()
    if "[ok]" in ml or "done" in ml or "completed" in ml:
        return "ok"
    if "[err]" in ml or "error" in ml or "failed" in ml or "exception" in ml or "traceback" in ml or "lacks" in ml:
        return "error"
    if "[skip]" in ml or "skipped" in ml or "skip" in ml:
        return "skip"
    if "gpu" in ml or "vaapi" in ml or "nvenc" in ml or "qsv" in ml or "amf" in ml:
        return "gpu"
    if "[cpu]" in ml or "starting [cpu]" in ml or "cpu" in ml:
        return "cpu"
    if "warn" in ml or "fallback" in ml:
        return "warn"
    if "starting" in ml:
        return "start"
    return "info"


def _to_html(msg: str, theme: str = "dark") -> str:
    palette = _HTML_COLORS_DARK if theme == "dark" else _HTML_COLORS_LIGHT
    color = palette.get(_classify(msg), palette["info"])
    safe = msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("  ", "&nbsp;&nbsp;")
    return f'<span style="color:{color};">{safe}</span>'


class LogsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = "dark"
        self._lines: list[str] = []
        self._filtered: list[str] = []
        self._auto_scroll = True
        self._filter_text = ""
        self._max_lines = 5000
        self._build_ui()
        self.set_theme("dark")

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter logs...")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_filter_change)
        self._search.setFixedHeight(28)
        toolbar.addWidget(self._search)

        self._btn_scroll = QPushButton("Auto-scroll ON")
        self._btn_scroll.setCheckable(True)
        self._btn_scroll.setChecked(True)
        self._btn_scroll.setObjectName("btn_secondary")
        self._btn_scroll.setFixedHeight(28)
        self._btn_scroll.toggled.connect(self._toggle_scroll)
        toolbar.addWidget(self._btn_scroll)

        btn_clear = QPushButton("Clear")
        btn_clear.setObjectName("btn_secondary")
        btn_clear.setFixedHeight(28)
        btn_clear.clicked.connect(self._clear)
        toolbar.addWidget(btn_clear)

        btn_export = QPushButton("Export")
        btn_export.setObjectName("btn_secondary")
        btn_export.setFixedHeight(28)
        btn_export.clicked.connect(self._export)
        toolbar.addWidget(btn_export)

        root.addLayout(toolbar)

        self._count_lbl = QLabel("0 entries")
        root.addWidget(self._count_lbl)

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.document().setMaximumBlockCount(3000)
        font = QFont("Cascadia Code", 10)
        font.setStyleHint(QFont.Monospace)
        self._text.setFont(font)
        self._text.setLineWrapMode(QTextEdit.NoWrap)
        root.addWidget(self._text)

    def set_theme(self, theme: str):
        self._theme = theme
        lbl_color = "#a1a1aa" if theme == "dark" else "#64748b"
        self._count_lbl.setStyleSheet(
            f"font-size: 11px; color: {lbl_color}; background: transparent; border: none;"
        )
        self.load_lines(self._lines)

    def append_line(self, msg: str):
        self._lines.append(msg)
        if len(self._lines) > self._max_lines:
            self._lines = self._lines[-self._max_lines:]

        if self._filter_text and self._filter_text.lower() not in msg.lower():
            self._count_lbl.setText(
                f"{len(self._lines)} total | {len(self._filtered)} shown"
            )
            return

        self._filtered.append(msg)
        if len(self._filtered) > self._max_lines:
            self._filtered = self._filtered[-self._max_lines:]

        self._text.append(_to_html(msg, self._theme))
        self._count_lbl.setText(
            f"{len(self._lines)} total | {len(self._filtered)} shown"
        )
        if self._auto_scroll:
            self._text.moveCursor(QTextCursor.End)

    def load_lines(self, lines: list[str]):
        self._lines = list(lines)[-self._max_lines:]
        self._filtered = []
        self._text.clear()
        for msg in self._lines:
            if not self._filter_text or self._filter_text.lower() in msg.lower():
                self._filtered.append(msg)
                self._text.append(_to_html(msg, self._theme))
        self._count_lbl.setText(
            f"{len(self._lines)} total | {len(self._filtered)} shown"
        )
        if self._auto_scroll:
            self._text.moveCursor(QTextCursor.End)

    def _on_filter_change(self, text: str):
        self._filter_text = text
        self.load_lines(self._lines)

    def _toggle_scroll(self, checked: bool):
        self._auto_scroll = checked
        self._btn_scroll.setText(f"Auto-scroll {'ON' if checked else 'OFF'}")

    def _clear(self):
        self._lines.clear()
        self._filtered.clear()
        self._text.clear()
        self._count_lbl.setText("0 entries")

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs",
            str(Path.home() / "mediacrush_logs.txt"),
            "Text Files (*.txt)"
        )
        if path:
            Path(path).write_text("\n".join(self._lines), encoding="utf-8")


class LogsDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("MediaCrush - Logs")
        self.setMinimumSize(820, 560)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        self._widget = LogsWidget()
        root.addWidget(self._widget)

    def append(self, msg: str):
        self._widget.append_line(msg)

    def load_lines(self, lines: list[str]):
        self._widget.load_lines(lines)
