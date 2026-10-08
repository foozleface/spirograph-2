"""Gate for the alerts: the right words, to the right places, at the right time.

A plot is a sequence of unattended stretches separated by moments that need a
person. This checks that those moments produce a message that actually tells
someone what to do — which layer finished, which nib goes in next, how long is
left — and that a transport failing never touches the plot.

No network: every transport is pointed at a recorder or at a port nothing is
listening on. Run:  .venv/bin/python tests/test_notify.py
"""

import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from axiplot import notify  # noqa: E402
from spiro.pipeline import build_ini, run  # noqa: E402
from spiro.scene import Paper, Pen, Scene  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %-60s %s %s" % (name, "ok" if cond else "FAIL",
                             detail if not cond else ""))


class Recorder(notify.Notifier):
    def __init__(self, fail=False):
        self.sent = []
        self.fail = fail

    def configured(self):
        return True

    def send(self, title, message, data=None):
        if self.fail:
            raise RuntimeError("no route to host")
        self.sent.append((title, message, data or {}))
        return True


class PlotRecorder:
    def __init__(self):
        self.plotted = []

    def plot(self, svg_path, opts=None, progress=True):
        self.plotted.append(svg_path)
        return {"stopped": 0, "stats": {}, "raw": ""}

    def preview(self, svg_path, opts=None):
        return {"estTimeSec": 1.0, "drawLenM": 0.0, "penUpLenM": 0.0,
                "totalLenM": 0.0, "tookSec": 0.0, "raw": ""}


def time_send(notifier):
    """How long a send blocks the caller — the whole point of Async."""
    start = time.time()
    notifier.send("t", "m")
    return time.time() - start


def drawing(gear=35, samples=400):
    return run(build_ini(
        steps=[{"kind": "single", "params": {"type": "spirograph_gear",
                                             "fixed_teeth": 96,
                                             "rolling_teeth": gear}}],
        sampling={"initial_samples": samples * 12, "output_samples": samples}))


# -- the words ---------------------------------------------------------------- #

print("what a person is told:")
title, message = notify.layer_message(
    {"label": "Black", "paths": 12}, 0, 2, seconds=95,
    next_layer={"label": "Red", "estSec": 300})
check("the title says which layer finished, and of how many",
      title == "Layer 1/2 done -- Black", title)
check("the message says how long it took", "took 1 min 35 s" in message, message)
check("and which nib goes in next", "swap to Red" in message, message)
check("and how long that one will take", "~5 min 00 s to go" in message, message)

title, message = notify.layer_message({"label": "Red"}, 1, 2, seconds=300)
check("the last layer says the plot is done, not what to swap to",
      "plot complete" in message and "swap" not in message, message)

# -- a whole plot ---------------------------------------------------------------- #

print("a two-pen plot:")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication([])
from spiro.ui.workers import PlotWorker  # noqa: E402

scene = Scene(paper=Paper.from_axidraw(3))
scene.pens = [Pen("#000000", "Black"), Pen("#c0392b", "Red")]
first = scene.add(drawing(), name="one")
second = scene.add(drawing(gear=37), name="two")
first.move_to(120, 80)
first.set_width(80)
second.move_to(430, 110)
second.set_width(80)

alerts = Recorder()
worker = PlotWorker(make_driver=lambda progress, message: PlotRecorder())
finished = []
worker.finished.connect(finished.append)
worker.penChange.connect(lambda i, l, p: worker.resume_after_pen_change(True))

thread = threading.Thread(
    target=worker.plot, args=(scene.job(), {"model": 3}),
    kwargs={"notifier": alerts}, daemon=True)
thread.start()
deadline = time.time() + 30
while time.time() < deadline and not finished:
    app.processEvents()
    time.sleep(0.02)
thread.join(5)

check("the plot ran to the end", bool(finished) and finished[0]["complete"])
check("two alerts went out: the pen change, then the finish (not both for the last layer)",
      len(alerts.sent) == 2, [t for t, _, _ in alerts.sent])
check("the first names layer 1 of 2 and the pen to swap to",
      alerts.sent[0][0] == "Layer 1/2 done -- Black"
      and "swap to Red" in alerts.sent[0][1],
      alerts.sent[0][:2] if alerts.sent else None)
check("and the last is the finish, with the layer count",
      len(alerts.sent) > 1 and alerts.sent[1][0] == "Plot finished"
      and "2 layers" in alerts.sent[1][1],
      alerts.sent[1][:2] if len(alerts.sent) > 1 else None)
# -- short work is not worth a phone buzz ---------------------------------------- #

print()
print("the ninety-second bar:")
seen = []
bar = notify.Threshold(notify.CallableNotifier(lambda t, m, d: seen.append(t)), 90)
LAYERS = [{"label": "Black", "hex": "#000"}, {"label": "Red", "hex": "#c00"}]

bar.plot_done(LAYERS, 15)
check("a fifteen-second plot sends nothing", seen == [], seen)
bar.plot_done(LAYERS, 120)
check("a two-minute one does", seen == ["Plot finished"], seen)

seen.clear()
bar.layer_done(LAYERS[0], 0, 2, seconds=12, next_layer={"estSec": 9})
check("a pen change between two quick layers stays quiet", seen == [], seen)
bar.layer_done(LAYERS[0], 0, 2, seconds=12, next_layer={"estSec": 600})
check("but one with a long layer coming up gets through", len(seen) == 1, seen)
seen.clear()
bar.layer_done(LAYERS[0], 0, 2, seconds=300, next_layer={"estSec": 5})
check("and so does one you have been waiting five minutes for", len(seen) == 1, seen)

seen.clear()
bar.plot_done(LAYERS, None)
check("an unknown duration is treated as short, not as forever", seen == [], seen)

off = notify.Threshold(notify.CallableNotifier(lambda t, m, d: seen.append(t)), 0)
off.plot_done(LAYERS, 1)
check("a bar of zero lets everything through", len(seen) == 1, seen)

check("each alert carries the layer numbers for a receiver to act on",
      alerts.sent[0][2].get("layer") == 1 and alerts.sent[0][2].get("layers") == 2)

# -- a dead transport must not stop a plot -------------------------------------------- #

print("when a phone is unreachable:")
good, bad = Recorder(), Recorder(fail=True)
fan = notify.MultiNotifier(bad, good)
check("one dead transport does not stop the others",
      fan.send("t", "m") and len(good.sent) == 1)

alerts = Recorder(fail=True)
worker = PlotWorker(make_driver=lambda progress, message: PlotRecorder())
finished = []
worker.finished.connect(finished.append)
worker.penChange.connect(lambda i, l, p: worker.resume_after_pen_change(True))
thread = threading.Thread(target=worker.plot, args=(scene.job(), {"model": 3}),
                          kwargs={"notifier": alerts}, daemon=True)
thread.start()
deadline = time.time() + 30
while time.time() < deadline and not finished:
    app.processEvents()
    time.sleep(0.02)
thread.join(5)
check("a notifier that throws every time still leaves the plot finished",
      bool(finished) and finished[0]["complete"])

unreachable = notify.MqttNotifier("127.0.0.1", topic="alerts/raise", port=1, timeout=1)
check("an unreachable broker fails quietly rather than raising",
      unreachable.send("t", "m") is False and unreachable.last_error)

# -- the panel ------------------------------------------------------------------------- #

print("the panel:")
from PySide6.QtCore import QSettings  # noqa: E402

from spiro.ui.notify_panel import NotifyPanel  # noqa: E402

settings = QSettings("spirograph-2-test", "notify-gate")
settings.clear()
panel = NotifyPanel(settings)
check("with alerts off there is no notifier at all", panel.notifier() is None)

panel.enabled.setChecked(True)
check("switched on but with no transport, still none", panel.notifier() is None)

panel.mqtt_enabled.setChecked(True)
panel.mqtt_host.setText("192.0.2.1")
panel.mqtt_topic.setText("alerts/raise")
notifier = panel.notifier()
check("a configured transport gives a thresholded, async, fanned-out notifier",
      isinstance(notifier, notify.Threshold)
      and isinstance(notifier.inner, notify.Async)
      and isinstance(notifier.inner.inner, notify.MultiNotifier))
check("and the bar is ninety seconds unless it was changed",
      notifier.min_seconds == 90.0, notifier.min_seconds)
check("async sending returns at once, whatever the network does",
      time_send(notifier) < 0.2)

panel.ha_enabled.setChecked(True)
panel.ha_url.setText("http://192.0.2.1:8123")
panel.ha_token.setText("token")
panel.ha_service.setText("notify.phone")
def fan_out(notifier):
    """The MultiNotifier inside however many wrappers the panel put round it."""
    while not isinstance(notifier, notify.MultiNotifier):
        notifier = notifier.inner
    return notifier


def transport(panel, kind):
    """The one transport of a given class inside the panel's fan-out."""
    for entry in fan_out(panel.notifier()).notifiers:
        if isinstance(entry, kind):
            return entry
    return None


check("two transports switched on means two in the fan-out",
      len(fan_out(panel.notifier()).notifiers) == 2)
check("both kinds are there",
      transport(panel, notify.HomeAssistantNotifier) is not None
      and transport(panel, notify.MqttNotifier) is not None)
check("a dotted service becomes Home Assistant's REST path",
      transport(panel, notify.HomeAssistantNotifier).service == "notify/phone")

panel.ha_service.setText("script.send_alert")
panel.ha_level.setCurrentText("critical")
check("a script service is sent the level, which is what makes a phone buzz",
      transport(panel, notify.HomeAssistantNotifier)
      ._payload_probe().get("level") == "critical")
panel.ha_service.setText("notify.phone")
check("a notify service is not, because it rejects unknown keys",
      "level" not in transport(panel, notify.HomeAssistantNotifier)._payload_probe())

settings.clear()
print()
print("notify: %d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    for name in FAIL:
        print("  FAILED: %s" % name)
sys.exit(1 if FAIL else 0)
