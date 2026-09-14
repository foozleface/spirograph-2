"""Colours, spacing and the few widget helpers every panel repeats.

Dark chrome around a white sheet, because the sheet is the only thing in the
window that is pretending to be paper and it should be the brightest thing in
it. Kept as plain constants rather than a stylesheet file so a panel can use a
colour in a QPainter as easily as in CSS.
"""

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QFrame, QLabel

BG = "#16171b"            # window
PANEL = "#1e2026"         # side panels
PANEL_HI = "#272a32"      # inputs, hovered rows
LINE = "#33363f"          # hairlines
TEXT = "#e6e7ea"
MUTED = "#8d919c"
ACCENT = "#7c5cfc"        # selection, focus
ACCENT_DIM = "#4c3aa8"
OK = "#3fb950"
WARN = "#d29922"
ERR = "#f85149"

PAPER = QColor("#ffffff")
PAPER_EDGE = QColor("#000000")
CANVAS_BG = QColor("#101116")
GRID = QColor(0, 0, 0, 18)
GRID_MAJOR = QColor(0, 0, 0, 38)
MARGIN_LINE = QColor(0, 0, 0, 55)
SELECT = QColor(124, 92, 252)

STYLESHEET = """
QWidget { background: %(BG)s; color: %(TEXT)s;
          font-family: "Inter", "Segoe UI", system-ui, sans-serif; font-size: 12px; }
QScrollArea, QScrollArea > QWidget > QWidget { background: %(PANEL)s; }
QFrame#panel { background: %(PANEL)s; }
QLabel#h1 { font-size: 15px; font-weight: 600; }
QLabel#h2 { font-size: 12px; font-weight: 600; color: %(TEXT)s;
            text-transform: uppercase; letter-spacing: 0.06em; }
QLabel#muted { color: %(MUTED)s; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QListWidget {
    background: %(PANEL_HI)s; border: 1px solid %(LINE)s; border-radius: 4px;
    padding: 3px 6px; selection-background-color: %(ACCENT)s; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: %(ACCENT)s; }
QComboBox::drop-down { border: none; width: 16px; }
QComboBox QAbstractItemView { background: %(PANEL_HI)s; border: 1px solid %(LINE)s;
    selection-background-color: %(ACCENT)s; }
QPushButton { background: %(PANEL_HI)s; border: 1px solid %(LINE)s; border-radius: 4px;
              padding: 5px 11px; }
QPushButton:hover { border-color: %(ACCENT)s; }
QPushButton:pressed { background: %(ACCENT_DIM)s; }
QPushButton:disabled { color: %(MUTED)s; border-color: %(LINE)s; background: %(PANEL)s; }
QPushButton#primary { background: %(ACCENT)s; border-color: %(ACCENT)s; color: white;
                      font-weight: 600; }
QPushButton#primary:hover { background: #8f74ff; }
QPushButton#danger { border-color: %(ERR)s; color: %(ERR)s; }
QPushButton#flat { background: transparent; border: none; padding: 2px 6px; color: %(MUTED)s; }
QPushButton#flat:hover { color: %(TEXT)s; }
QGroupBox { border: 1px solid %(LINE)s; border-radius: 5px; margin-top: 14px;
            padding: 8px 8px 6px 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px;
                   color: %(MUTED)s; font-weight: 600; }
QGroupBox#finishing::title { color: %(TEXT)s; }
QGroupBox#finishing::indicator { width: 15px; height: 15px; border: 1px solid %(MUTED)s;
                                 border-radius: 3px; background: %(PANEL_HI)s; }
QGroupBox#finishing::indicator:checked { background: %(ACCENT)s; border-color: %(ACCENT)s; }
QGroupBox#finishing:checked { border-color: %(ACCENT_DIM)s; }
QListWidget::item { padding: 4px 6px; border-radius: 3px; }
QListWidget::item:selected { background: %(ACCENT_DIM)s; color: white; }
QTabBar::tab { background: transparent; padding: 6px 14px; color: %(MUTED)s;
               border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: %(TEXT)s; border-bottom-color: %(ACCENT)s; }
QTabWidget::pane { border: none; }
QProgressBar { background: %(PANEL_HI)s; border: 1px solid %(LINE)s; border-radius: 4px;
               text-align: center; height: 16px; }
QProgressBar::chunk { background: %(ACCENT)s; border-radius: 3px; }
QCheckBox::indicator, QRadioButton::indicator { width: 13px; height: 13px; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: %(LINE)s; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: %(MUTED)s; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QSplitter::handle { background: %(LINE)s; }
QToolTip { background: %(PANEL_HI)s; color: %(TEXT)s; border: 1px solid %(LINE)s; }
""" % globals()


def h1(text):
    label = QLabel(text)
    label.setObjectName("h1")
    return label


def h2(text):
    label = QLabel(text)
    label.setObjectName("h2")
    return label


def muted(text, wrap=False):
    label = QLabel(text)
    label.setObjectName("muted")
    label.setWordWrap(wrap)
    return label


def hline():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color: %s; background: %s; max-height: 1px;" % (LINE, LINE))
    return line


def mono(size=11):
    font = QFont("JetBrains Mono, DejaVu Sans Mono, monospace")
    font.setStyleHint(QFont.Monospace)
    font.setPointSize(size)
    return font
