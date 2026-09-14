#!/usr/bin/env bash
# Launch the Spirograph desktop app.
#
#   ./run_gui.sh              open an empty pattern
#   ./run_gui.sh some.ini     open a pattern file
#
# First run builds .venv and installs PySide6, NumPy and the AxiDraw API.
set -euo pipefail
cd "$(dirname "$0")"

VENV=".venv"
AXIDRAW_URL="https://cdn.evilmadscientist.com/dl/ad/public/AxiDraw_API.zip"

if [ ! -x "$VENV/bin/python" ]; then
    echo "Creating $VENV ..."
    python3 -m venv "$VENV"
fi

need() { "$VENV/bin/python" -c "import $1" >/dev/null 2>&1 || return 0; return 1; }

if need PySide6 || need numpy; then
    echo "Installing PySide6 and NumPy ..."
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet PySide6 numpy
fi
if need pyaxidraw; then
    echo "Installing the AxiDraw API (pen-plotter support) ..."
    "$VENV/bin/pip" install --quiet "$AXIDRAW_URL" \
        || echo "  ... failed; the app runs, the plotter controls will not."
fi

# xcb (XWayland) is the proven backend here: input is verified, while the
# native wayland plugin showed focus trouble for windows launched from a
# background shell. Override with QT_QPA_PLATFORM to experiment.
# macOS ships only the cocoa plugin, so leave Qt to its default there.
if [ -z "${QT_QPA_PLATFORM:-}" ] && [ "$(uname -s)" != "Darwin" ]; then
    export QT_QPA_PLATFORM="xcb;wayland"
fi

exec "$VENV/bin/python" -m spiro.ui.app "$@"
