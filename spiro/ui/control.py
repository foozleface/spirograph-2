"""Driving the running window from outside: a small local control API.

The window listens on a Unix socket in the user's runtime directory --
``$XDG_RUNTIME_DIR/spirograph-2.sock``, which only that user can reach --
for one JSON object per line, and answers each with one JSON line:

    {"cmd": "add", "type": "ellipse"}         ->  {"ok": true, "step": 0}
    {"cmd": "set", "step": 0, "key": "cycles", "value": 468.25}
    {"cmd": "state"}                          ->  {"ok": true, "document": ...}
    {"cmd": "frobnicate"}                     ->  {"ok": false, "error": "..."}

Every command goes through the same methods the buttons do, so what is
built this way is built the way a person builds it: it redraws, it is on
the undo history, it is kept in the session. ``spiroctl`` at the top of
the repository is the command-line end of it.

Commands
--------
ping                         the window is there
state                        Build's pattern, the selected step, the quality,
                             whether the drawing is up to date, the paper
new [blank]                  start a pattern (a gear, or nothing)
open path                    open a pattern or a sheet
add type [after]             put a step after the selected one (or `after`)
remove step                  take a step out
select step                  pick a step in Build
set step key value           change one setting of one step; a null value
                             removes it (a drift's oscillation, a slip)
quality label                Draft / Fine / Ultra
render                       redraw now
place                        put the pattern on the paper
unplace [name]               take patterns off the paper: every one of that
                             name, or Build's own copy when no name is given
save path                    save the pattern as an .ini
undo / redo
screenshot path [what]       what: window (default), build, render, paper
"""

import json
import os
import tempfile
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from spiro.pipeline.registry import MODULE_DEFS

SOCKET_NAME = "spirograph-2.sock"


def socket_path():
    """Where the window listens: the user's runtime directory, private to
    them, or the temp directory when there is none."""
    base = os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()
    return str(Path(base) / SOCKET_NAME)


class ControlServer(QObject):
    """Answers control commands for one window."""

    def __init__(self, window, path=None, parent=None):
        super().__init__(parent or window)
        self.window = window
        self.path = path or socket_path()
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.UserAccessOption)
        QLocalServer.removeServer(self.path)            # a stale one from a crash
        self.listening = self.server.listen(self.path)
        self.server.newConnection.connect(self._connected)
        self._buffers = {}

    def close(self):
        self.server.close()
        QLocalServer.removeServer(self.path)

    # -- the wire ------------------------------------------------------------------ #

    def _connected(self):
        while self.server.hasPendingConnections():
            sock = self.server.nextPendingConnection()
            self._buffers[sock] = b""
            sock.readyRead.connect(lambda s=sock: self._read(s))
            sock.disconnected.connect(lambda s=sock: self._buffers.pop(s, None))
            sock.disconnected.connect(sock.deleteLater)

    def _read(self, sock):
        self._buffers[sock] = self._buffers.get(sock, b"") + bytes(sock.readAll())
        while b"\n" in self._buffers[sock]:
            line, self._buffers[sock] = self._buffers[sock].split(b"\n", 1)
            if line.strip():
                reply = self.handle_line(line.decode("utf-8", "replace"))
                sock.write((json.dumps(reply) + "\n").encode())
                sock.flush()

    def handle_line(self, line):
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("send one JSON object per line")
            return self.handle(request)
        except Exception as exc:                        # an answer, never a crash
            return {"ok": False, "error": str(exc)}

    # -- the commands -------------------------------------------------------------- #

    def handle(self, request):
        cmd = str(request.get("cmd", "")).strip().lower()
        fn = getattr(self, "cmd_" + cmd, None)
        if fn is None:
            raise ValueError("unknown command %r — try: %s" % (cmd, ", ".join(
                sorted(n[4:] for n in dir(self) if n.startswith("cmd_")))))
        out = fn(request) or {}
        return dict({"ok": True}, **out)

    def _step(self, request):
        steps = self.window.document.steps
        index = int(request["step"])
        if not 0 <= index < len(steps):
            raise ValueError("no step %d — the machine has %d" % (index, len(steps)))
        return index, steps[index]

    def cmd_ping(self, _r):
        return {"socket": self.path}

    def cmd_state(self, _r):
        w = self.window
        doc = w.document
        return {
            "document": {"name": doc.name,
                         "path": str(doc.path) if doc.path else None,
                         "steps": [dict(step.get("params", {}), kind=step.get("kind"))
                                   for step in doc.steps]},
            "selected": w.design.selected_step,
            "quality": w.design.quality.currentText(),
            "drawn": w.drawing is not None and w._rendered_token == w.render_token
                     and not w._render_timer.isActive(),
            "points": w.drawing.point_count if w.drawing is not None else 0,
            "paper": [{"name": i.name, "x_mm": i.x_mm, "y_mm": i.y_mm, "w_mm": i.w_mm,
                       "h_mm": i.h_mm, "rotation_deg": i.rotation_deg, "pen": i.pen,
                       "linked": i.source == doc.token} for i in w.scene.items],
        }

    def cmd_new(self, r):
        self.window._new_document(blank=bool(r.get("blank")))
        return {"steps": len(self.window.document.steps)}

    def cmd_open(self, r):
        path = Path(os.path.expanduser(str(r["path"])))
        if not path.exists():
            raise ValueError("no such file: %s" % path)
        self.window._open_path(str(path))
        return {"name": self.window.document.name}

    def cmd_add(self, r):
        kind = str(r["type"])
        if kind not in MODULE_DEFS:
            raise ValueError("no step called %r" % kind)
        design = self.window.design
        if "after" in r:
            design.selected_step = int(r["after"])
        design.insert_module(kind)
        return {"step": design.selected_step}

    def cmd_remove(self, r):
        index, _ = self._step(r)
        design = self.window.design
        design.selected_step = index
        design._remove()
        return {"steps": len(self.window.document.steps)}

    def cmd_select(self, r):
        index, _ = self._step(r)
        self.window.design.strip.select(index)
        self.window.design._select_step(index)
        return {"step": index}

    def cmd_set(self, r):
        index, step = self._step(r)
        key, value = str(r["key"]), r.get("value")
        design = self.window.design
        design._set_param(step["params"], key, value)
        # Show it in the panel, as if typed there.
        design.refresh(select=design.selected_step if design.selected_step is not None
                       else index)
        return {"step": index, "key": key, "value": value}

    def cmd_quality(self, r):
        label = str(r["label"]).capitalize()
        combo = self.window.design.quality
        if combo.findText(label) < 0:
            raise ValueError("quality is one of: %s" % ", ".join(
                combo.itemText(i) for i in range(combo.count())))
        combo.setCurrentText(label)
        return {"quality": label}

    def cmd_render(self, _r):
        self.window._render_timer.stop()
        self.window._render_now()
        return {"token": self.window.render_token}

    def cmd_place(self, _r):
        if self.window.drawing is None:
            raise ValueError("nothing drawn yet — render first, and wait for it")
        self.window._place()
        item = self.window.scene.items[-1]
        return {"name": item.name, "w_mm": item.w_mm, "h_mm": item.h_mm}

    def cmd_unplace(self, r):
        w = self.window
        name = r.get("name")
        items = ([i for i in w.scene.items if i.name == str(name)] if name
                 else w._linked_items())
        if not items:
            raise ValueError("nothing on the paper called %r" % name if name
                             else "Build's pattern is not on the paper")
        w._take_off(items)
        return {"removed": len(items), "left": len(w.scene.items)}

    def cmd_save(self, r):
        path = Path(os.path.expanduser(str(r["path"])))
        if path.suffix != ".ini":
            path = path.with_suffix(".ini")
        self.window.document.save(str(path))
        self.window.library.refresh()
        self.window._update_title()
        return {"path": str(path)}

    def cmd_undo(self, _r):
        self.window._undo()
        return {"status": self.window.status_left.text()}

    def cmd_redo(self, _r):
        self.window._redo()
        return {"status": self.window.status_left.text()}

    def cmd_screenshot(self, r):
        w = self.window
        widget = {"window": w, "build": w.design, "render": w.render_panel,
                  "paper": w.paper_host}.get(str(r.get("what", "window")))
        if widget is None:
            raise ValueError("what is one of: window, build, render, paper")
        path = os.path.expanduser(str(r["path"]))
        if not widget.grab().save(path):
            raise ValueError("could not write %s" % path)
        return {"path": path}


def send(request, path=None, timeout_ms=5000):
    """Send one command to a running window and return its answer."""
    sock = QLocalSocket()
    sock.connectToServer(path or socket_path())
    if not sock.waitForConnected(timeout_ms):
        raise ConnectionError("no window is listening on %s — is the app running?"
                              % (path or socket_path()))
    sock.write((json.dumps(request) + "\n").encode())
    sock.flush()
    data = b""
    while b"\n" not in data:
        if not sock.waitForReadyRead(timeout_ms):
            raise TimeoutError("the window did not answer")
        data += bytes(sock.readAll())
    sock.disconnectFromServer()
    return json.loads(data.split(b"\n", 1)[0])
