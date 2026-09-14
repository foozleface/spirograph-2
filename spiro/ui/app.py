"""Start the window.

    ./run_gui.sh          or      .venv/bin/python -m spiro.ui.app [file.ini]

xcb is the proven Qt backend on this machine; the native Wayland plugin has
focus trouble for windows launched from a background shell. run_gui.sh sets it,
and this respects QT_QPA_PLATFORM if it is already set.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from spiro.ui import theme
from spiro.ui.main_window import MainWindow


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    app = QApplication(argv)
    app.setApplicationName("Spirograph")
    app.setOrganizationName("spirograph-2")
    app.setStyleSheet(theme.STYLESHEET)

    window = MainWindow()
    for arg in argv[1:]:
        if arg.endswith(".ini") and Path(arg).exists():
            from spiro.pipeline.document import Document
            window.document.__dict__.update(Document.load(arg).__dict__)
            window.design.refresh(select=0)
            window._update_title()
            window._schedule_render()
            break
    window.show()
    window.canvas.fit()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
