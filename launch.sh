#!/usr/bin/env bash
# Launch and manage the Spirograph-2 web UI, bootstrapping a virtualenv if needed.
#
#   ./launch.sh [start] [port]   start in the background (default; port 8890)
#   ./launch.sh stop             stop the running server
#   ./launch.sh restart [port]   stop then start
#   ./launch.sh status           report whether it's running, and where
#   ./launch.sh fg [port]        run in the foreground (Ctrl-C to quit)
#
# A bare port also works, so the old `./launch.sh 9000` still starts on 9000.
set -euo pipefail

cd "$(dirname "$0")"

VENV=".venv"
DEPS=(fastapi uvicorn numpy)
PIDFILE=".server.pid"
LOG="server.log"
DEFAULT_PORT=8890
AXIDRAW_URL="https://cdn.evilmadscientist.com/dl/ad/public/AxiDraw_API.zip"

# ---- argument parsing -------------------------------------------------------
# Accept `start|stop|restart|status|fg`, a bare port, or a command plus a port.
CMD="start"
PORT=""
for arg in "$@"; do
    case "$arg" in
        start|stop|restart|status|fg|foreground) CMD="$arg" ;;
        ''|*[!0-9]*)
            echo "launch.sh: unrecognized argument '$arg'" >&2
            echo "  usage: ./launch.sh [start|stop|restart|status|fg] [port]" >&2
            exit 2 ;;
        *) PORT="$arg" ;;
    esac
done
[ "$CMD" = "foreground" ] && CMD="fg"

# ---- process helpers --------------------------------------------------------

# Echo the command line of $1 if that pid is one of our servers, else nothing.
server_cmdline() {
    local pid="$1" args
    [ -n "$pid" ] || return 1
    args="$(ps -o args= -p "$pid" 2>/dev/null)" || return 1
    case "$args" in
        *server.py*) printf '%s\n' "$args" ;;
        *) return 1 ;;
    esac
}

# Echo the live pid from the pidfile, or nothing. Removes a stale pidfile.
# A pid is only trusted if it still belongs to a server.py process — pids get
# recycled, and we must never signal an unrelated one.
running_pid() {
    local pid
    [ -f "$PIDFILE" ] || return 1
    pid="$(tr -dc '0-9' < "$PIDFILE")"
    if [ -n "$pid" ] && server_cmdline "$pid" >/dev/null; then
        printf '%s\n' "$pid"
        return 0
    fi
    rm -f "$PIDFILE"
    return 1
}

# Echo the --port a running server was started with (falls back to the default).
port_of() {
    local args port
    args="$(server_cmdline "$1")" || return 1
    port="$(printf '%s\n' "$args" | sed -n 's/.*--port[ =]\([0-9]\{1,\}\).*/\1/p')"
    printf '%s\n' "${port:-$DEFAULT_PORT}"
}

# Is anything listening on port $1?
port_in_use() {
    if command -v ss >/dev/null 2>&1; then
        ss -ltn 2>/dev/null | awk '{print $4}' | grep -qE "[:.]$1\$"
    elif command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:"$1" -sTCP:LISTEN -t >/dev/null 2>&1
    else
        (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null
    fi
}

wait_for_port() {
    local port="$1" i
    for i in $(seq 1 100); do
        (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null && return 0
        sleep 0.1
    done
    return 1
}

# ---- commands ---------------------------------------------------------------

do_status() {
    local pid p
    if pid="$(running_pid)"; then
        p="$(port_of "$pid")"
        echo "spirograph-2: running (pid $pid) — http://127.0.0.1:${p}/"
        return 0
    fi
    echo "spirograph-2: not running"
    # A server we don't own can still hold the port; say so rather than letting
    # a later start fail with an opaque "address already in use".
    local check="${PORT:-$DEFAULT_PORT}"
    if port_in_use "$check"; then
        echo "  note: something else is listening on port $check"
    fi
    return 1
}

do_stop() {
    local pid i
    if ! pid="$(running_pid)"; then
        echo "spirograph-2: not running"
        return 0
    fi
    echo "Stopping spirograph-2 (pid $pid) ..."
    kill "$pid" 2>/dev/null || true
    for i in $(seq 1 100); do
        server_cmdline "$pid" >/dev/null || break
        sleep 0.1
    done
    if server_cmdline "$pid" >/dev/null; then
        echo "  didn't exit after 10s; sending SIGKILL"
        kill -9 "$pid" 2>/dev/null || true
        sleep 0.5
    fi
    rm -f "$PIDFILE"
    echo "Stopped."
}

# Resolve $PY and make sure the server's dependencies are importable.
bootstrap() {
    # Prefer an already-built venv, else the newest usable system interpreter.
    PY=""
    if [ -x "$VENV/bin/python" ]; then
        PY="$VENV/bin/python"
    else
        for candidate in python3 python python3.13 python3.12 python3.11; do
            cmd="$(command -v "$candidate" 2>/dev/null)" || continue
            if "$cmd" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
                PY="$cmd"
                break
            fi
        done
    fi

    if [ -z "$PY" ]; then
        echo "launch.sh: no Python 3.8+ interpreter found on PATH." >&2
        echo "  Install one, e.g.: sudo apt install python3 python3-venv" >&2
        exit 1
    fi

    # If the chosen interpreter can't import the server deps, build/populate the venv.
    if ! "$PY" -c 'import fastapi, uvicorn, numpy' 2>/dev/null; then
        if [ ! -x "$VENV/bin/python" ]; then
            echo "Creating virtualenv in $(pwd)/$VENV ..."
            if ! "$PY" -m venv "$VENV"; then
                echo "launch.sh: '$PY -m venv' failed." >&2
                echo "  On Debian/Ubuntu: sudo apt install python3-venv" >&2
                exit 1
            fi
        fi
        PY="$VENV/bin/python"
        echo "Installing ${DEPS[*]} into $VENV ..."
        "$PY" -m pip install --quiet --upgrade pip
        "$PY" -m pip install --quiet "${DEPS[@]}"
    fi

    # AxiDraw plotting needs Evil Mad Scientist's API package. It's a big separate
    # download, so it gets its own idempotent check instead of riding on DEPS —
    # that way an already-built venv picks it up too.
    if ! "$PY" -c 'import pyaxidraw' 2>/dev/null; then
        if [ "$PY" = "$VENV/bin/python" ]; then
            echo "Installing AxiDraw API into $VENV (plotter support) ..."
            "$PY" -m pip install --quiet "$AXIDRAW_URL" \
                || echo "launch.sh: AxiDraw API install failed; plotting will be unavailable." >&2
        else
            echo "launch.sh: pyaxidraw missing from $PY; plotting will be unavailable." >&2
            echo "  Install with: $PY -m pip install $AXIDRAW_URL" >&2
        fi
    fi
}

do_start() {
    local pid p
    if pid="$(running_pid)"; then
        p="$(port_of "$pid")"
        echo "spirograph-2: already running (pid $pid) — http://127.0.0.1:${p}/"
        echo "  use './launch.sh restart' to pick up code changes"
        return 0
    fi
    PORT="${PORT:-$DEFAULT_PORT}"
    if port_in_use "$PORT"; then
        echo "launch.sh: port $PORT is already in use by another process." >&2
        echo "  pick another port: ./launch.sh start <port>" >&2
        exit 1
    fi

    bootstrap

    echo "--- $(date '+%Y-%m-%d %H:%M:%S') starting on port $PORT ---" >> "$LOG"
    nohup "$PY" server.py --port "$PORT" >> "$LOG" 2>&1 &
    pid=$!
    echo "$pid" > "$PIDFILE"

    if wait_for_port "$PORT"; then
        echo "spirograph-2: started (pid $pid) — http://127.0.0.1:${PORT}/"
        echo "  log: $(pwd)/$LOG    stop: ./launch.sh stop"
        return 0
    fi
    # Never claim a start that didn't take: say what happened and show the log.
    if server_cmdline "$pid" >/dev/null; then
        echo "spirograph-2: pid $pid is up but port $PORT isn't answering yet." >&2
        echo "  check $LOG" >&2
        return 1
    fi
    rm -f "$PIDFILE"
    echo "launch.sh: server exited immediately. Last lines of $LOG:" >&2
    tail -n 20 "$LOG" >&2
    exit 1
}

do_fg() {
    local pid
    if pid="$(running_pid)"; then
        echo "launch.sh: already running in the background (pid $pid); stop it first." >&2
        exit 1
    fi
    PORT="${PORT:-$DEFAULT_PORT}"
    bootstrap
    echo "http://127.0.0.1:${PORT}/"
    exec "$PY" server.py --port "$PORT"
}

case "$CMD" in
    start)   do_start ;;
    stop)    do_stop ;;
    restart) do_stop; do_start ;;
    status)  do_status ;;
    fg)      do_fg ;;
esac
