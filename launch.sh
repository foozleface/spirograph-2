#!/usr/bin/env bash
# Spirograph used to be a web server; it is a desktop app now.
#
# This is kept so `./launch.sh` still starts the thing. It hands over to
# run_gui.sh, which is the real launcher.
cd "$(dirname "$0")"

for arg in "$@"; do
    case "$arg" in
        start|stop|restart|status|fg|foreground|''|*[0-9])
            cat >&2 <<'NOTE'
launch.sh: there is no server to start, stop or restart any more — the app
           draws its own window, so it lives and dies with its terminal.
           Starting it now; close the window to quit.
NOTE
            break ;;
    esac
done

exec ./run_gui.sh
