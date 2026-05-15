#!/usr/bin/env python3
"""MediaCrush — entry point."""
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore    import Qt
from PySide6.QtGui     import QFont

from gui.main_window import MainWindow
from gui.styles      import get_style
from config.settings import Settings


def main():
    # High-DPI support
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("MediaCrush")
    app.setOrganizationName("MediaCrush")
    app.setApplicationVersion("1.0.0")

    # Default font
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.PreferDefaultHinting)
    app.setFont(font)

    # Apply initial theme
    s = Settings()
    app.setStyleSheet(get_style(s.get("ui.theme", "dark")))

    win = MainWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
