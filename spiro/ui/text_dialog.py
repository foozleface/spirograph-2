"""Add text to the paper, or change text already on it.

The words, the font, how big, which way round, how the lines line up and
how far apart — with the result drawn as it will be plotted, updating as
you type. Single-line fonts come first because they are what a pen draws
best: each stroke of a letter once. Any installed font can be used too,
drawn as its outline.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFontDatabase, QStandardItemModel
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox,
                               QDoubleSpinBox, QGridLayout, QLabel,
                               QPlainTextEdit, QVBoxLayout)

from spiro import text as textlib
from spiro.ui import theme, thumbs

PREVIEW_W, PREVIEW_H = 560, 200


class TextDialog(QDialog):
    """The words and how they look. ``result()`` after ``exec()``."""

    def __init__(self, parent=None, spec=None, size_mm=10.0, rotation_deg=0.0,
                 editing=False):
        super().__init__(parent)
        spec = dict(spec or {})
        self.setWindowTitle("Edit the text" if editing else "Add text to the paper")
        self.resize(620, 560)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.words = QPlainTextEdit(spec.get("text", ""))
        self.words.setPlaceholderText("Type the words — Enter starts a new line")
        self.words.setFixedHeight(96)
        layout.addWidget(self.words)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)
        self.font = QComboBox()
        self.font.setMaxVisibleItems(24)
        self._fill_fonts(spec.get("font", textlib.DEFAULT_FONT))
        self.size = QDoubleSpinBox()
        self.size.setRange(1.0, 500.0)
        self.size.setDecimals(1)
        self.size.setSuffix(" mm")
        self.size.setValue(size_mm)
        self.size.setToolTip("The height of a capital letter")
        self.rotation = QDoubleSpinBox()
        self.rotation.setRange(-360.0, 360.0)
        self.rotation.setDecimals(1)
        self.rotation.setSuffix("°")
        self.rotation.setWrapping(True)
        self.rotation.setValue(rotation_deg)
        self.align = QComboBox()
        for name in textlib.ALIGNS:
            self.align.addItem(name.capitalize(), name)
        self.align.setCurrentIndex(max(0, self.align.findData(spec.get("align", "left"))))
        self.spacing = QDoubleSpinBox()
        self.spacing.setRange(1.0, 5.0)
        self.spacing.setSingleStep(0.1)
        self.spacing.setDecimals(2)
        self.spacing.setValue(float(spec.get("line_spacing", textlib.LINE_SPACING)))
        self.spacing.setToolTip("Baseline to baseline, in capital heights")
        grid.addWidget(QLabel("Font"), 0, 0)
        grid.addWidget(self.font, 0, 1, 1, 3)
        grid.addWidget(QLabel("Size"), 1, 0)
        grid.addWidget(self.size, 1, 1)
        grid.addWidget(QLabel("Turn"), 1, 2)
        grid.addWidget(self.rotation, 1, 3)
        grid.addWidget(QLabel("Lines"), 2, 0)
        grid.addWidget(self.align, 2, 1)
        grid.addWidget(QLabel("Spacing"), 2, 2)
        grid.addWidget(self.spacing, 2, 3)
        layout.addLayout(grid)

        self.preview = QLabel()
        self.preview.setFixedSize(PREVIEW_W, PREVIEW_H)
        self.preview.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview, 0, Qt.AlignHCenter)
        self.note = theme.muted("", wrap=True)
        layout.addWidget(self.note)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(
            "Change it" if editing else "Put it on the paper")
        self.buttons.button(QDialogButtonBox.Ok).setObjectName("primary")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._redraw)
        for signal in (self.words.textChanged, self.font.currentIndexChanged,
                       self.align.currentIndexChanged, self.spacing.valueChanged,
                       self.size.valueChanged):
            signal.connect(self._timer.start)
        self.drawing = None
        self._redraw()
        self.words.setFocus()

    # -- the font list ----------------------------------------------------------- #

    def _fill_fonts(self, current):
        model = QStandardItemModel(self.font)
        self.font.setModel(model)

        def header(words):
            self.font.addItem(words, None)
            item = model.item(model.rowCount() - 1)
            item.setEnabled(False)
            item.setForeground(QColor(theme.MUTED))

        header("Single line — the pen draws each stroke once")
        for name, label in textlib.HERSHEY_FONTS:
            self.font.addItem("    " + label, textlib.HERSHEY_PREFIX + name)
        header("Outline — any installed font, drawn round each letter")
        for family in sorted(set(QFontDatabase.families())):
            if QFontDatabase.isPrivateFamily(family):
                continue
            self.font.addItem("    " + family, textlib.OUTLINE_PREFIX + family)
        index = self.font.findData(current)
        self.font.setCurrentIndex(index if index >= 0 else self.font.findData(
            textlib.DEFAULT_FONT))

    # -- what it will be ---------------------------------------------------------- #

    def spec(self):
        return {"text": self.words.toPlainText().rstrip("\n"),
                "font": self.font.currentData() or textlib.DEFAULT_FONT,
                "align": self.align.currentData(),
                "line_spacing": self.spacing.value()}

    def ini(self):
        spec = self.spec()
        return textlib.build_text_ini(spec["text"], spec["font"], spec["align"],
                                      spec["line_spacing"])

    def _redraw(self):
        ok = self.buttons.button(QDialogButtonBox.Ok)
        try:
            self.drawing = textlib.render(self.ini())
        except ValueError as exc:
            self.drawing = None
            self.preview.setPixmap(thumbs.pixmap([], 10, background=theme.CANVAS_BG)
                                   .scaled(PREVIEW_W, PREVIEW_H))
            self.note.setText(str(exc).capitalize() + ".")
            ok.setEnabled(False)
            return
        ok.setEnabled(True)
        cap = self.drawing.style["cap_height"]
        mm = self.size.value() / cap
        self.note.setText("%.0f x %.0f mm on the paper — %s, %s"
                          % (self.drawing.width * mm, self.drawing.height * mm,
                             textlib.font_label(self.spec()["font"]),
                             "single line" if self.spec()["font"].startswith(
                                 textlib.HERSHEY_PREFIX) else "outline"))
        missing = textlib.missing_letters(self.spec()["text"], self.spec()["font"])
        if missing:
            self.note.setText(self.note.text() + "\nNot in this font, so left out: "
                              + "  ".join(missing))
        self.preview.setPixmap(_wide_pixmap(self.drawing))


def _wide_pixmap(drawing):
    """The text fitted into the preview's wide box rather than a square."""
    from PySide6.QtGui import QPainter, QPainterPath, QPen, QPixmap
    pix = QPixmap(PREVIEW_W, PREVIEW_H)
    pix.fill(QColor("#f4f1ea"))
    pad = 14
    placed = drawing.fitted(PREVIEW_W - 2 * pad, PREVIEW_H - 2 * pad)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.translate(pad, pad)
    pen = QPen(QColor("#1a1a1a"), 1.2)
    painter.setPen(pen)
    for points in placed:
        path = QPainterPath()
        path.moveTo(points[0].real, points[0].imag)
        for z in points[1:]:
            path.lineTo(z.real, z.imag)
        painter.drawPath(path)
    painter.end()
    return pix
