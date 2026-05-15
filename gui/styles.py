"""QSS stylesheets — dark and light themes, no emojis."""

DARK = """
QMainWindow, QDialog {
    background-color: #0d0d17;
    color: #e2e8f0;
}
QWidget {
    background-color: #0d0d17;
    color: #e2e8f0;
    font-family: "Inter", "Segoe UI", "SF Pro Display", sans-serif;
    font-size: 13px;
}

/* ── Panels / Cards ─────────────────────────────────────────── */
QFrame#panel {
    background-color: #161625;
    border: 1px solid #252540;
    border-radius: 10px;
}
QFrame#card {
    background-color: #1c1c30;
    border: 1px solid #252540;
    border-radius: 8px;
}
QFrame#sidebar {
    background-color: #111120;
    border-right: 1px solid #252540;
    border-radius: 0;
}

/* ── Toolbar ────────────────────────────────────────────────── */
QToolBar {
    background-color: #111120;
    border-bottom: 1px solid #252540;
    padding: 4px 8px;
    spacing: 4px;
}
QToolBar::separator {
    background: #252540;
    width: 1px;
    margin: 4px 6px;
}

/* ── Buttons ────────────────────────────────────────────────── */
QPushButton {
    background-color: #6d28d9;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 13px;
    min-height: 30px;
}
QPushButton:hover   { background-color: #5b21b6; }
QPushButton:pressed { background-color: #4c1d95; }
QPushButton:disabled { background-color: #1e1e35; color: #3d3d5c; }

QPushButton#btn_secondary {
    background-color: transparent;
    border: 1px solid #2d2d50;
    color: #94a3b8;
    font-weight: 500;
}
QPushButton#btn_secondary:hover {
    border-color: #4a4a70;
    color: #e2e8f0;
    background-color: #1c1c30;
}

QPushButton#btn_success {
    background-color: transparent;
    border: 1.5px solid #059669;
    color: #10b981;
    font-weight: 600;
}
QPushButton#btn_success:hover { background-color: #05966915; }
QPushButton#btn_success:disabled { border-color: #1e1e35; color: #1e1e35; }

QPushButton#btn_warning {
    background-color: transparent;
    border: 1.5px solid #b45309;
    color: #f59e0b;
    font-weight: 600;
}
QPushButton#btn_warning:hover { background-color: #b4530915; }
QPushButton#btn_warning:disabled { border-color: #1e1e35; color: #1e1e35; }

QPushButton#btn_danger {
    background-color: transparent;
    border: 1.5px solid #991b1b;
    color: #f87171;
    font-weight: 600;
}
QPushButton#btn_danger:hover { background-color: #991b1b20; }
QPushButton#btn_danger:disabled { border-color: #1e1e35; color: #1e1e35; }

QPushButton#btn_icon {
    background: transparent;
    border: none;
    padding: 4px;
    border-radius: 4px;
    min-height: 0;
}
QPushButton#btn_icon:hover { background: #1c1c30; }

/* ── Inputs ─────────────────────────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #1c1c30;
    border: 1px solid #2d2d50;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e2e8f0;
    selection-background-color: #6d28d9;
}
QLineEdit:focus, QSpinBox:focus { border-color: #6d28d9; }

QComboBox {
    background-color: #1c1c30;
    border: 1px solid #2d2d50;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e2e8f0;
    min-height: 30px;
}
QComboBox:focus { border-color: #6d28d9; }
QComboBox::drop-down {
    border: none; width: 28px;
    border-left: 1px solid #2d2d50;
}
QComboBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #64748b;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #1c1c30;
    border: 1px solid #2d2d50;
    border-radius: 6px;
    selection-background-color: #6d28d9;
    color: #e2e8f0;
    outline: none;
    padding: 4px;
}

/* ── Slider ─────────────────────────────────────────────────── */
QSlider::groove:horizontal {
    height: 3px; background: #2d2d50; border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 14px; height: 14px;
    background: #6d28d9; border-radius: 7px; margin: -6px 0;
}
QSlider::handle:horizontal:hover { background: #7c3aed; }
QSlider::sub-page:horizontal { background: #6d28d9; border-radius: 2px; }

/* ── Progress bars ───────────────────────────────────────────── */
QProgressBar {
    background-color: #1c1c30;
    border: none;
    border-radius: 3px;
    height: 5px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #6d28d9, stop:1 #0284c7);
    border-radius: 3px;
}
QProgressBar#overall {
    height: 8px;
    border-radius: 4px;
}
QProgressBar#overall::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #059669, stop:1 #0284c7);
    border-radius: 4px;
}

/* ── List ───────────────────────────────────────────────────── */
QListWidget {
    background-color: #0d0d17;
    border: none;
    outline: none;
}
QListWidget::item { border-radius: 6px; }
QListWidget::item:selected { background-color: transparent; }

/* ── Scrollbar ───────────────────────────────────────────────── */
QScrollBar:vertical {
    width: 6px; background: transparent; border: none; margin: 0;
}
QScrollBar::handle:vertical {
    background: #252540; border-radius: 3px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #3d3d60; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

/* ── Labels ─────────────────────────────────────────────────── */
QLabel#app_title {
    font-size: 16px; font-weight: 800; color: #a78bfa;
    letter-spacing: 0.5px;
}
QLabel#section_title {
    font-size: 11px; font-weight: 700; color: #475569;
    letter-spacing: 1.2px; text-transform: uppercase;
}
QLabel#stat_val {
    font-size: 22px; font-weight: 700; color: #a78bfa;
}
QLabel#stat_lbl {
    font-size: 10px; color: #475569; font-weight: 500;
    letter-spacing: 0.5px; text-transform: uppercase;
}
QLabel#hw_badge { font-size: 10px; color: #10b981; font-weight: 500; }
QLabel#status_running { color: #38bdf8; font-size: 12px; font-weight: 500; }
QLabel#status_idle    { color: #475569; font-size: 12px; }

/* ── Checkbox ───────────────────────────────────────────────── */
QCheckBox { spacing: 8px; color: #94a3b8; }
QCheckBox::indicator {
    width: 15px; height: 15px;
    border: 1.5px solid #3d3d60; border-radius: 3px;
    background: #1c1c30;
}
QCheckBox::indicator:checked {
    background: #6d28d9; border-color: #6d28d9;
}

/* ── Tabs ───────────────────────────────────────────────────── */
QTabBar::tab {
    background: transparent; color: #64748b;
    padding: 8px 16px; margin-right: 2px;
    border-bottom: 2px solid transparent; font-weight: 500;
}
QTabBar::tab:selected {
    color: #a78bfa; border-bottom: 2px solid #6d28d9;
}
QTabBar::tab:hover { color: #e2e8f0; }
QTabWidget::pane {
    border: 1px solid #252540; border-radius: 8px;
    top: -1px;
}
QTabWidget::tab-bar { alignment: left; }

/* ── TextEdit (logs) ────────────────────────────────────────── */
QTextEdit {
    background-color: #0a0a12;
    color: #64748b;
    border: 1px solid #252540;
    border-radius: 8px;
    font-family: "Cascadia Code", "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
    padding: 8px;
}

/* ── StatusBar ──────────────────────────────────────────────── */
QStatusBar {
    background: #0a0a12;
    color: #475569;
    border-top: 1px solid #1a1a2e;
    font-size: 11px;
    padding: 0 8px;
    min-height: 28px;
}
QStatusBar::item { border: none; }

/* ── GroupBox ───────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #252540; border-radius: 8px;
    margin-top: 12px; padding-top: 12px;
    color: #475569; font-weight: 600; font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 12px;
    color: #475569; letter-spacing: 0.8px;
}

/* ── FormLayout ─────────────────────────────────────────────── */
QFormLayout { spacing: 12px; }

/* ── Splitter ───────────────────────────────────────────────── */
QSplitter::handle { background: #1a1a2e; width: 4px; height: 4px; }
QSplitter::handle:hover { background: #6d28d9; }

/* ── ScrollArea used in sidebar ─────────────────────────────── */
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }

/* ── Tooltip ────────────────────────────────────────────────── */
QToolTip {
    background-color: #1c1c30; color: #e2e8f0;
    border: 1px solid #2d2d50; border-radius: 5px;
    padding: 5px 10px; font-size: 12px;
}

/* ── Separator ──────────────────────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #252540;
    background: #252540;
    max-height: 1px;
}
"""

LIGHT = """
QMainWindow, QDialog { background-color: #f1f5f9; color: #0f172a; }
QWidget {
    background-color: #f1f5f9; color: #0f172a;
    font-family: "Inter", "Segoe UI", "SF Pro Display", sans-serif;
    font-size: 13px;
}

QFrame#panel {
    background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
}
QFrame#card {
    background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
}
QFrame#sidebar {
    background-color: #f8fafc; border-right: 1px solid #e2e8f0; border-radius: 0;
}
QToolBar {
    background-color: #ffffff; border-bottom: 1px solid #e2e8f0;
    padding: 4px 8px; spacing: 4px;
}
QToolBar::separator { background: #e2e8f0; width: 1px; margin: 4px 6px; }

QPushButton {
    background-color: #6d28d9; color: #fff; border: none;
    border-radius: 6px; padding: 7px 16px;
    font-weight: 600; min-height: 30px;
}
QPushButton:hover   { background-color: #5b21b6; }
QPushButton:pressed { background-color: #4c1d95; }
QPushButton:disabled { background-color: #e2e8f0; color: #94a3b8; }

QPushButton#btn_secondary {
    background-color: transparent;
    border: 1px solid #cbd5e1; color: #64748b;
}
QPushButton#btn_secondary:hover {
    border-color: #94a3b8; color: #0f172a; background: #f1f5f9;
}

QPushButton#btn_success {
    background: transparent; border: 1.5px solid #059669; color: #059669;
}
QPushButton#btn_success:hover { background: #05966910; }
QPushButton#btn_success:disabled { border-color: #e2e8f0; color: #e2e8f0; }

QPushButton#btn_warning {
    background: transparent; border: 1.5px solid #d97706; color: #d97706;
}
QPushButton#btn_warning:hover { background: #d9770610; }
QPushButton#btn_warning:disabled { border-color: #e2e8f0; color: #e2e8f0; }

QPushButton#btn_danger {
    background: transparent; border: 1.5px solid #dc2626; color: #dc2626;
}
QPushButton#btn_danger:hover { background: #dc262610; }
QPushButton#btn_danger:disabled { border-color: #e2e8f0; color: #e2e8f0; }

QPushButton#btn_icon {
    background: transparent; border: none; padding: 4px; border-radius: 4px; min-height: 0;
}
QPushButton#btn_icon:hover { background: #f1f5f9; }

QLineEdit, QSpinBox, QDoubleSpinBox {
    background: #fff; border: 1px solid #cbd5e1; border-radius: 6px;
    padding: 6px 10px; color: #0f172a;
}
QLineEdit:focus, QSpinBox:focus { border-color: #6d28d9; }

QComboBox {
    background: #fff; border: 1px solid #cbd5e1; border-radius: 6px;
    padding: 6px 10px; color: #0f172a; min-height: 30px;
}
QComboBox:focus { border-color: #6d28d9; }
QComboBox::drop-down { border: none; width: 28px; border-left: 1px solid #e2e8f0; }
QComboBox::down-arrow {
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid #94a3b8; margin-right: 8px;
}
QComboBox QAbstractItemView {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 6px;
    selection-background-color: #6d28d9; color: #0f172a; padding: 4px;
}

QSlider::groove:horizontal { height: 3px; background: #e2e8f0; border-radius: 2px; }
QSlider::handle:horizontal {
    width: 14px; height: 14px; background: #6d28d9; border-radius: 7px; margin: -6px 0;
}
QSlider::sub-page:horizontal { background: #6d28d9; border-radius: 2px; }

QProgressBar {
    background: #e2e8f0; border: none; border-radius: 3px; height: 5px; color: transparent;
}
QProgressBar::chunk { background: #6d28d9; border-radius: 3px; }
QProgressBar#overall { height: 8px; border-radius: 4px; }
QProgressBar#overall::chunk { background: #059669; border-radius: 4px; }

QListWidget { background: #f1f5f9; border: none; outline: none; }
QListWidget::item { border-radius: 6px; }
QListWidget::item:hover { background: #f8fafc; }

QScrollBar:vertical { width: 6px; background: transparent; border: none; }
QScrollBar::handle:vertical { background: #cbd5e1; border-radius: 3px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #94a3b8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QLabel#app_title { font-size: 16px; font-weight: 800; color: #6d28d9; letter-spacing: 0.5px; }
QLabel#section_title { font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 1.2px; }
QLabel#stat_val { font-size: 22px; font-weight: 700; color: #6d28d9; }
QLabel#stat_lbl { font-size: 10px; color: #94a3b8; font-weight: 500; letter-spacing: 0.5px; }
QLabel#hw_badge { font-size: 10px; color: #059669; font-weight: 500; }

QCheckBox { spacing: 8px; color: #64748b; }
QCheckBox::indicator { width: 15px; height: 15px; border: 1.5px solid #cbd5e1; border-radius: 3px; background: #fff; }
QCheckBox::indicator:checked { background: #6d28d9; border-color: #6d28d9; }

QTabBar::tab {
    background: transparent; color: #94a3b8;
    padding: 8px 16px; border-bottom: 2px solid transparent; font-weight: 500;
}
QTabBar::tab:selected { color: #6d28d9; border-bottom: 2px solid #6d28d9; }
QTabBar::tab:hover { color: #0f172a; }
QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 8px; top: -1px; }

QTextEdit {
    background: #1e293b; color: #64748b;
    border: 1px solid #e2e8f0; border-radius: 8px;
    font-family: monospace; font-size: 11px; padding: 8px;
}
QStatusBar {
    background: #fff; color: #94a3b8;
    border-top: 1px solid #e2e8f0; font-size: 11px; padding: 0 8px;
    min-height: 28px;
}
QStatusBar::item { border: none; }
QGroupBox {
    border: 1px solid #e2e8f0; border-radius: 8px;
    margin-top: 12px; padding-top: 12px;
    color: #94a3b8; font-weight: 600; font-size: 11px;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; color: #94a3b8; }
QSplitter::handle { background: #e2e8f0; width: 4px; height: 4px; }
QSplitter::handle:hover { background: #6d28d9; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QToolTip {
    background: #fff; color: #0f172a;
    border: 1px solid #e2e8f0; border-radius: 5px; padding: 5px 10px;
}
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #e2e8f0; background: #e2e8f0; max-height: 1px;
}
"""


def get_style(theme: str) -> str:
    return DARK if theme == "dark" else LIGHT
