"""Logs panel — real-time, searchable, colored severity levels."""
from __future__ import annotations
import re
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QFileDialog, QLineEdit, QFrame, QSizePolicy
)
from PySide6.QtCore    import Qt, QTimer
from PySide6.QtGui     import QTextCursor, QFont, QColor, QTextCharFormat


# ── Color scheme for log levels ───────────────────────────────────────────────

_LEVEL_COLORS = {
    "ok":      "#10b981",   # [OK]  / Done / success
    "error":   "#f87171",   # [ERR] / Error
    "skip":    "#fbbf24",   # [SKIP] / Skipped
    "gpu":     "#38bdf8",   # GPU / VAAPI / NVENC
    "cpu":     "#a78bfa",   # CPU
    "info":    "#94a3b8",   # default
    "warn":    "#fb923c",   # Warning
    "start":   "#e2e8f0",   # Starting…
}

_HTML_COLORS = {
    "ok":    "#10b981",
    "error": "#f87171",
    "skip":  "#fbbf24",
    "gpu":   "#38bdf8",
    "cpu":   "#c084fc",
    "info":  "#64748b",
    "warn":  "#fb923c",
    "start": "#e2e8f0",
}


def _classify(msg: str) -> str:
    ml = msg.lower()
    if "[ok]" in ml or "done" in ml or "✓" in ml:
        return "ok"
    if "[err]" in ml or "error" in ml or "✗" in ml or "failed" in ml:
        return "error"
    if "[skip]" in ml or "skipped" in ml or "skip" in ml:
        return "skip"
    if "gpu" in ml or "vaapi" in ml or "nvenc" in ml or "qsv" in ml:
        return "gpu"
    if "[cpu]" in ml or "starting [cpu]" in ml or "cpu" in ml:
        return "cpu"
    if "warn" in ml or "fallback" in ml:
        return "warn"
    if "starting" in ml:
        return "start"
    return "info"


def _to_html(msg: str) -> str:
    color = _HTML_COLORS[_classify(msg)]
    safe  = msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<span style="color:{color};">{safe}</span>'


# ── Inline (sidebar/tab) logs widget ─────────────────────────────────────────

class LogsWidget(QWidget):
    """Embeddable log viewer with search, auto-scroll, and export."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lines:    list[str]  = []
        self._filtered: list[str]  = []
        self._auto_scroll = True
        self._filter_text = ""
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter logs…")
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

        # ── Log count badge ───────────────────────────────────────────────────
        self._count_lbl = QLabel("0 entries")
        self._count_lbl.setStyleSheet(
            "font-size: 10px; color: #334155; background: transparent; border: none;"
        )
        root.addWidget(self._count_lbl)

        # ── Text area ─────────────────────────────────────────────────────────
        self._text = QTextEdit()
        self._text.setReadOnly(True)
        font = QFont("Cascadia Code", 10)
        font.setStyleHint(QFont.Monospace)
        self._text.setFont(font)
        self._text.setLineWrapMode(QTextEdit.NoWrap)
        root.addWidget(self._text)

    # ── Public API ────────────────────────────────────────────────────────────

    def append_line(self, msg: str):
        self._lines.append(msg)
        if self._filter_text and self._filter_text.lower() not in msg.lower():
            self._count_lbl.setText(
                f"{len(self._lines)} total  •  {len(self._filtered)} shown"
            )
            return
        self._filtered.append(msg)
        self._text.append(_to_html(msg))
        self._count_lbl.setText(
            f"{len(self._lines)} total  •  {len(self._filtered)} shown"
        )
        if self._auto_scroll:
            self._text.moveCursor(QTextCursor.End)

    def load_lines(self, lines: list[str]):
        self._lines    = list(lines)
        self._filtered = []
        self._text.clear()
        for msg in lines:
            if not self._filter_text or self._filter_text.lower() in msg.lower():
                self._filtered.append(msg)
                self._text.append(_to_html(msg))
        self._count_lbl.setText(
            f"{len(self._lines)} total  •  {len(self._filtered)} shown"
        )
        if self._auto_scroll:
            self._text.moveCursor(QTextCursor.End)

    # ── Slots ─────────────────────────────────────────────────────────────────

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


# ── Standalone dialog wrapper (kept for backward compat) ─────────────────────

class LogsDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("MediaCrush — Logs")
        self.setMinimumSize(820, 560)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        self._widget = LogsWidget()
        root.addWidget(self._widget)

    def append(self, msg: str):
        self._widget.append_line(msg)

    def load_lines(self, lines: list[str]):
        self._widget.load_lines(lines)
