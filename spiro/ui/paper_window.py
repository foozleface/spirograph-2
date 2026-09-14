"""The paper, on its own.

A sheet 600 mm across does not want to share a 1600-pixel window with two
panels. Two ways out, and they are different enough to be worth both:

* **Paper only** hides the side panels, so the sheet has the whole window.
* **Its own window** puts the canvas in a top-level window that can be dragged
  to a second monitor and made fullscreen while the controls stay where they
  are — which is the arrangement you want while a plot is being arranged.

Both move the *same* canvas widget by reparenting it. Never a copy: two
canvases would be two opinions about where a pattern is, which is the bug this
whole program was rewritten to stop having.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QStatusBar, QLabel

from spiro.ui import theme


class PaperWindow(QMainWindow):
    """A window whose whole job is to hold the canvas."""

    closed = Signal()

    def __init__(self, canvas, title="Spirograph — paper", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setCentralWidget(canvas)
        self.canvas = canvas
        self.resize(1200, 800)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.readout = QLabel("")
        self.status.addPermanentWidget(self.readout)
        self.status.showMessage(
            "F11 fullscreen · Esc to leave it · close this window to put the "
            "paper back")

        for label, shortcut, fn in (
                ("Fullscreen", "F11", self.toggle_fullscreen),
                ("Leave fullscreen", QKeySequence(Qt.Key_Escape), self.leave_fullscreen),
                ("Fit the sheet", "Ctrl+0", lambda: self.canvas.fit()),
                ("Zoom in", QKeySequence.ZoomIn, lambda: self.canvas.zoom_by(1.2)),
                ("Zoom out", QKeySequence.ZoomOut, lambda: self.canvas.zoom_by(1 / 1.2))):
            action = QAction(label, self)
            action.setShortcut(shortcut)
            action.triggered.connect(fn)
            self.addAction(action)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def leave_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()

    def show_position(self, text):
        self.readout.setText(text)

    def release_canvas(self):
        """Give the canvas back, un-parented and still alive.

        takeCentralWidget, not setCentralWidget(None): a QMainWindow OWNS its
        central widget and deletes it when it is replaced or when the window
        goes. Taking it transfers ownership back, which is the difference
        between the canvas coming home and the canvas being destroyed under
        everything that still holds a reference to it.
        """
        taken = self.takeCentralWidget()
        if taken is not None:
            taken.setParent(None)
        return taken

    def closeEvent(self, event):
        self.release_canvas()
        self.closed.emit()
        super().closeEvent(event)
