"""The command-line end of the control API (spiro.ui.control)."""

import json
import sys
import time

from PySide6.QtCore import QCoreApplication

from spiro.ui.control import send


def parse(args):
    """['set', 'step=0', 'key=cycles', 'value=468.25'] -> a request dict."""
    if len(args) == 1 and args[0].lstrip().startswith("{"):
        return json.loads(args[0])
    request = {"cmd": args[0]}
    for arg in args[1:]:
        key, _, raw = arg.partition("=")
        try:
            request[key] = json.loads(raw)
        except ValueError:
            request[key] = raw
    return request


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(__doc__ + "\n\nusage: spiroctl <cmd> [key=value ...] | spiroctl wait | "
              "spiroctl '<json>'")
        return 2
    QCoreApplication.instance() or QCoreApplication([])
    if args[0] == "wait":
        # Until the drawing matches the pattern: a redraw is queued, then run
        # on a worker thread, and lands a moment later.
        limit = time.time() + float(parse(args).get("seconds", 120))
        while time.time() < limit:
            state = send({"cmd": "state"})
            if state.get("drawn"):
                print(json.dumps({"ok": True, "points": state.get("points")}))
                return 0
            time.sleep(0.3)
        print(json.dumps({"ok": False, "error": "still drawing"}))
        return 1
    # A command may have real work behind it -- a job runs the ink guard
    # over the whole sheet -- so the command line waits as long as it takes.
    reply = send(parse(args), timeout_ms=600000)
    print(json.dumps(reply, indent=1))
    return 0 if reply.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
