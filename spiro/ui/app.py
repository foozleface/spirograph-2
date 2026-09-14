"""Start the window.

    ./run_gui.sh          or      .venv/bin/python -m spiro.ui.app [file.ini | file.sheet.json]

A pattern file opens in Build; a sheet file opens on the paper.

On Linux, xcb is the proven Qt backend; the native Wayland plugin has focus
trouble for windows launched from a background shell. run_gui.sh sets it there
(macOS has only cocoa), and this respects QT_QPA_PLATFORM if it is already set.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from spiro.scene import SHEET_SUFFIX
from spiro.ui import theme
from spiro.ui.main_window import MainWindow


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    app = QApplication(argv)
    # Fusion everywhere: the same widgets the eyetest renders offscreen, and
    # sliders with a visible track (the native macOS style draws a bare knob).
    app.setStyle("Fusion")
    app.setApplicationName("Spirograph")
    app.setOrganizationName("spirograph-2")
    app.setStyleSheet(theme.STYLESHEET)

    window = MainWindow()
    window.show()
    window.canvas.fit()
    for arg in argv[1:]:
        if (arg.endswith(".ini") or arg.endswith(SHEET_SUFFIX)) and Path(arg).exists():
            window._open_path(arg)
            break
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
