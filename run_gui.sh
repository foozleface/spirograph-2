#!/usr/bin/env bash
# Launch the Spirograph desktop app.
#
#   ./run_gui.sh              open an empty pattern
#   ./run_gui.sh some.ini     open a pattern file
#
# First run builds .venv and installs PySide6, NumPy, the Hershey fonts, the
# AxiDraw API and the axiplot engine. axiplot is a separate local package: it
# is installed (editable) from $AXIPLOT_SRC, which defaults to ~/axiplot.
set -euo pipefail
cd "$(dirname "$0")"

VENV=".venv"
AXIDRAW_URL="https://cdn.evilmadscientist.com/dl/ad/public/AxiDraw_API.zip"
AXIPLOT_SRC="${AXIPLOT_SRC:-$HOME/axiplot}"

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
if need HersheyFonts; then
    echo "Installing the Hershey fonts (single-line text for the plotter) ..."
    "$VENV/bin/pip" install --quiet Hershey-Fonts \
        || echo "  ... failed; text will offer outline fonts only."
fi
if need pyaxidraw; then
    echo "Installing the AxiDraw API (pen-plotter support) ..."
    "$VENV/bin/pip" install --quiet "$AXIDRAW_URL" \
        || echo "  ... failed; the app runs, the plotter controls will not."
fi

if need axiplot; then
    if [ ! -f "$AXIPLOT_SRC/pyproject.toml" ]; then
        echo "run_gui.sh: the axiplot engine is not installed in $VENV and its" >&2
        echo "            source was not found at $AXIPLOT_SRC" >&2
        echo "            Put the axiplot package there, or set AXIPLOT_SRC to" >&2
        echo "            the directory that holds its pyproject.toml." >&2
        exit 1
    fi
    echo "Installing the axiplot engine from $AXIPLOT_SRC ..."
    "$VENV/bin/pip" install --quiet -e "$AXIPLOT_SRC"
fi

# xcb (XWayland) is the proven backend here: input is verified, while the
# native wayland plugin showed focus trouble for windows launched from a
# background shell. Override with QT_QPA_PLATFORM to experiment.
# macOS ships only the cocoa plugin, so leave Qt to its default there.
if [ -z "${QT_QPA_PLATFORM:-}" ] && [ "$(uname -s)" != "Darwin" ]; then
    export QT_QPA_PLATFORM="xcb;wayland"
fi

exec "$VENV/bin/python" -m spiro.ui.app "$@"
