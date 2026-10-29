"""Stylesheets for dark and light themes using neutral industry palettes."""

DARK = """
QMainWindow, QDialog {
    background-color: #18181b;
    color: #f4f4f5;
}
QWidget {
    background-color: #18181b;
    color: #f4f4f5;
    font-family: "Inter", "Segoe UI", "SF Pro Display", sans-serif;
    font-size: 13px;
}
QFrame#panel {
    background-color: #1f1f23;
    border: 1px solid #2e2e33;
    border-radius: 10px;
}
QFrame#card {
    background-color: #27272a;
    border: 1px solid #38383e;
    border-radius: 8px;
}
QFrame#sidebar {
    background-color: #18181b;
    border-right: 1px solid #2e2e33;
    border-radius: 0;
}
QFrame#drop_zone[dragOver="true"] {
    background-color: #242730;
    border: 2px dashed #3b82f6;
    border-radius: 10px;
}
QToolBar {
    background-color: #18181b;
    border-bottom: 1px solid #2e2e33;
    padding: 6px 10px;
    spacing: 6px;
}
QToolBar::separator {
    background: #2e2e33;
    width: 1px;
    margin: 4px 6px;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:pressed {
    background-color: #1e40af;
}
QPushButton:disabled {
    background-color: #27272a;
    color: #52525b;
    border: 1px solid #333338;
}
QPushButton#btn_secondary {
    background-color: #242427;
    border: 1px solid #38383e;
    color: #d4d4d8;
    font-weight: 500;
}
QPushButton#btn_secondary:hover {
    border-color: #52525b;
    color: #f4f4f5;
    background-color: #2f2f35;
}
QPushButton#btn_secondary:disabled {
    background-color: #1f1f23;
    border-color: #2e2e33;
    color: #52525b;
}
QPushButton#btn_start {
    background-color: #065f46;
    border: 1px solid #10b981;
    color: #ecfdf5;
    font-weight: 600;
}
QPushButton#btn_start:hover {
    background-color: #047857;
}
QPushButton#btn_start:disabled {
    background-color: #202424;
    border-color: #2e3535;
    color: #525b5b;
}
QPushButton#btn_pause {
    background-color: #78350f;
    border: 1px solid #f59e0b;
    color: #fffbeb;
    font-weight: 600;
}
QPushButton#btn_pause:hover {
    background-color: #92400e;
}
QPushButton#btn_pause:disabled {
    background-color: #262320;
    border-color: #38332c;
    color: #5c554e;
}
QPushButton#btn_cancel {
    background-color: #7f1d1d;
    border: 1px solid #ef4444;
    color: #fef2f2;
    font-weight: 600;
}
QPushButton#btn_cancel:hover {
    background-color: #991b1b;
}
QPushButton#btn_cancel:disabled {
    background-color: #272020;
    border-color: #382c2c;
    color: #5c4e4e;
}
QPushButton#btn_danger {
    background-color: transparent;
    border: 1px solid #7f1d1d;
    color: #f87171;
    font-weight: 500;
}
QPushButton#btn_danger:hover {
    background-color: #7f1d1d33;
    border-color: #ef4444;
}
QPushButton#btn_icon {
    background: transparent;
    border: 1px solid transparent;
    padding: 4px;
    border-radius: 6px;
    min-height: 0;
}
QPushButton#btn_icon:hover {
    background: #27272a;
    border-color: #38383e;
}
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #242427;
    border: 1px solid #38383e;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f4f4f5;
    selection-background-color: #2563eb;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #3b82f6;
}
QComboBox {
    background-color: #242427;
    border: 1px solid #38383e;
    border-radius: 6px;
    padding: 5px 10px;
    color: #f4f4f5;
    min-height: 28px;
}
QComboBox:focus {
    border-color: #3b82f6;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
    border-left: 1px solid #38383e;
}
QComboBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #a1a1aa;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #242427;
    border: 1px solid #38383e;
    border-radius: 6px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    color: #f4f4f5;
    outline: none;
    padding: 4px;
}
QSlider::groove:horizontal {
    height: 4px;
    background: #2e2e33;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    background: #3b82f6;
    border-radius: 7px;
    margin: -5px 0;
}
QSlider::handle:horizontal:hover {
    background: #60a5fa;
}
QSlider::sub-page:horizontal {
    background: #2563eb;
    border-radius: 2px;
}
QProgressBar {
    background-color: #27272a;
    border: none;
    border-radius: 3px;
    height: 5px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: #3b82f6;
    border-radius: 3px;
}
QProgressBar#overall {
    height: 8px;
    border-radius: 4px;
    color: #a1a1aa;
    font-size: 10px;
    text-align: right;
    margin-right: 4px;
}
QProgressBar#overall::chunk {
    background: #10b981;
    border-radius: 4px;
}
QListWidget {
    background-color: #18181b;
    border: none;
    outline: none;
}
QListWidget::item {
    border-radius: 6px;
}
QListWidget::item:selected {
    background-color: transparent;
}
QScrollBar:vertical {
    width: 6px;
    background: transparent;
    border: none;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #38383e;
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #52525b;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QLabel#app_title {
    font-size: 15px;
    font-weight: 700;
    color: #f4f4f5;
    letter-spacing: 0.3px;
}
QLabel#section_title {
    font-size: 11px;
    font-weight: 700;
    color: #a1a1aa;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}
QLabel#panel_title {
    font-size: 14px;
    font-weight: 700;
    color: #f4f4f5;
}
QLabel#panel_subtitle {
    font-size: 12px;
    color: #a1a1aa;
}
QLabel#status_label {
    font-size: 11px;
    color: #a1a1aa;
}
QLabel#hw_badge {
    font-size: 11px;
    color: #10b981;
    font-weight: 600;
}
QCheckBox {
    spacing: 8px;
    color: #d4d4d8;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #52525b;
    border-radius: 4px;
    background: #242427;
}
QCheckBox::indicator:checked {
    background: #2563eb;
    border-color: #2563eb;
}
QTabBar::tab {
    background: transparent;
    color: #a1a1aa;
    padding: 8px 16px;
    margin-right: 4px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
}
QTabBar::tab:selected {
    color: #60a5fa;
    border-bottom: 2px solid #3b82f6;
}
QTabBar::tab:hover {
    color: #f4f4f5;
}
QTabWidget::pane {
    border: 1px solid #2e2e33;
    border-radius: 8px;
    top: -1px;
}
QTextEdit {
    background-color: #141416;
    color: #e4e4e7;
    border: 1px solid #2e2e33;
    border-radius: 8px;
    font-family: "Cascadia Code", "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
    padding: 8px;
}
QStatusBar {
    background: #18181b;
    color: #a1a1aa;
    border-top: 1px solid #2e2e33;
    font-size: 11px;
    padding: 0 10px;
    min-height: 28px;
}
QStatusBar::item {
    border: none;
}
QGroupBox {
    border: 1px solid #2e2e33;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    color: #a1a1aa;
    font-weight: 600;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    color: #a1a1aa;
}
QSplitter::handle:horizontal {
    background: transparent;
    width: 12px;
}
QSplitter::handle:horizontal:hover {
    background: #27272a;
    border-radius: 6px;
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QToolTip {
    background-color: #27272a;
    color: #f4f4f5;
    border: 1px solid #38383e;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
}
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #2e2e33;
    background: #2e2e33;
    max-height: 1px;
    border: none;
}
"""

LIGHT = """
QMainWindow, QDialog {
    background-color: #f8fafc;
    color: #0f172a;
}
QWidget {
    background-color: #f8fafc;
    color: #0f172a;
    font-family: "Inter", "Segoe UI", "SF Pro Display", sans-serif;
    font-size: 13px;
}
QFrame#panel {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}
QFrame#card {
    background-color: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}
QFrame#sidebar {
    background-color: #f8fafc;
    border-right: 1px solid #e2e8f0;
    border-radius: 0;
}
QFrame#drop_zone[dragOver="true"] {
    background-color: #eff6ff;
    border: 2px dashed #2563eb;
    border-radius: 10px;
}
QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 6px 10px;
    spacing: 6px;
}
QToolBar::separator {
    background: #e2e8f0;
    width: 1px;
    margin: 4px 6px;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:pressed {
    background-color: #1e40af;
}
QPushButton:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
    border: 1px solid #e2e8f0;
}
QPushButton#btn_secondary {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    color: #334155;
    font-weight: 500;
}
QPushButton#btn_secondary:hover {
    border-color: #94a3b8;
    color: #0f172a;
    background-color: #f8fafc;
}
QPushButton#btn_secondary:disabled {
    background-color: #f8fafc;
    border-color: #e2e8f0;
    color: #94a3b8;
}
QPushButton#btn_start {
    background-color: #ecfdf5;
    border: 1.5px solid #059669;
    color: #047857;
    font-weight: 600;
}
QPushButton#btn_start:hover {
    background-color: #d1fae5;
}
QPushButton#btn_start:disabled {
    background-color: #f8fafc;
    border-color: #e2e8f0;
    color: #94a3b8;
}
QPushButton#btn_pause {
    background-color: #fffbeb;
    border: 1.5px solid #d97706;
    color: #b45309;
    font-weight: 600;
}
QPushButton#btn_pause:hover {
    background-color: #fef3c7;
}
QPushButton#btn_pause:disabled {
    background-color: #f8fafc;
    border-color: #e2e8f0;
    color: #94a3b8;
}
QPushButton#btn_cancel {
    background-color: #fef2f2;
    border: 1.5px solid #dc2626;
    color: #b91c1c;
    font-weight: 600;
}
QPushButton#btn_cancel:hover {
    background-color: #fee2e2;
}
QPushButton#btn_cancel:disabled {
    background-color: #f8fafc;
    border-color: #e2e8f0;
    color: #94a3b8;
}
QPushButton#btn_danger {
    background-color: transparent;
    border: 1px solid #fca5a5;
    color: #dc2626;
    font-weight: 500;
}
QPushButton#btn_danger:hover {
    background-color: #fee2e2;
    border-color: #dc2626;
}
QPushButton#btn_icon {
    background: transparent;
    border: 1px solid transparent;
    padding: 4px;
    border-radius: 6px;
    min-height: 0;
}
QPushButton#btn_icon:hover {
    background: #f1f5f9;
    border-color: #e2e8f0;
}
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #0f172a;
    selection-background-color: #2563eb;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #2563eb;
}
QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 5px 10px;
    color: #0f172a;
    min-height: 28px;
}
QComboBox:focus {
    border-color: #2563eb;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
    border-left: 1px solid #e2e8f0;
}
QComboBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #64748b;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    color: #0f172a;
    outline: none;
    padding: 4px;
}
QSlider::groove:horizontal {
    height: 4px;
    background: #e2e8f0;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    background: #2563eb;
    border-radius: 7px;
    margin: -5px 0;
}
QSlider::handle:horizontal:hover {
    background: #1d4ed8;
}
QSlider::sub-page:horizontal {
    background: #2563eb;
    border-radius: 2px;
}
QProgressBar {
    background-color: #e2e8f0;
    border: none;
    border-radius: 3px;
    height: 5px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: #2563eb;
    border-radius: 3px;
}
QProgressBar#overall {
    height: 8px;
    border-radius: 4px;
    color: #64748b;
    font-size: 10px;
    text-align: right;
    margin-right: 4px;
}
QProgressBar#overall::chunk {
    background: #059669;
    border-radius: 4px;
}
QListWidget {
    background-color: #f8fafc;
    border: none;
    outline: none;
}
QListWidget::item {
    border-radius: 6px;
}
QListWidget::item:selected {
    background-color: transparent;
}
QScrollBar:vertical {
    width: 6px;
    background: transparent;
    border: none;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QLabel#app_title {
    font-size: 15px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: 0.3px;
}
QLabel#section_title {
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}
QLabel#panel_title {
    font-size: 14px;
    font-weight: 700;
    color: #0f172a;
}
QLabel#panel_subtitle {
    font-size: 12px;
    color: #64748b;
}
QLabel#status_label {
    font-size: 11px;
    color: #64748b;
}
QLabel#hw_badge {
    font-size: 11px;
    color: #059669;
    font-weight: 600;
}
QCheckBox {
    spacing: 8px;
    color: #334155;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #cbd5e1;
    border-radius: 4px;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #2563eb;
    border-color: #2563eb;
}
QTabBar::tab {
    background: transparent;
    color: #64748b;
    padding: 8px 16px;
    margin-right: 4px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
}
QTabBar::tab:selected {
    color: #2563eb;
    border-bottom: 2px solid #2563eb;
}
QTabBar::tab:hover {
    color: #0f172a;
}
QTabWidget::pane {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    top: -1px;
}
QTextEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-family: "Cascadia Code", "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
    padding: 8px;
}
QStatusBar {
    background: #ffffff;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
    font-size: 11px;
    padding: 0 10px;
    min-height: 28px;
}
QStatusBar::item {
    border: none;
}
QGroupBox {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    color: #64748b;
    font-weight: 600;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    color: #64748b;
}
QSplitter::handle:horizontal {
    background: transparent;
    width: 12px;
}
QSplitter::handle:horizontal:hover {
    background: #e2e8f0;
    border-radius: 6px;
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QToolTip {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
}
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #e2e8f0;
    background: #e2e8f0;
    max-height: 1px;
    border: none;
}
"""


def get_style(theme: str) -> str:
    return DARK if theme == "dark" else LIGHT
