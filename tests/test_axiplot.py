"""Gate for the axiplot layer: driver, layer state, the run loop, notifiers.

No hardware and no network. The AxiDraw is exercised in preview mode (motion
planning only, never opens a port), the progress feed is driven through the
same calls the real plot makes, and every notifier is pointed at a recorder.

Run:  python3 tests/test_axiplot.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from axiplot import driver, notify, plotter, run  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  %-54s %s %s" % (name, "ok" if cond else "FAIL",
                             detail if not cond else ""))


SQUARE = ('<svg xmlns="http://www.w3.org/2000/svg" width="100mm" '
          'height="100mm" viewBox="0 0 100 100"><g fill="none" stroke="black">'
          '<path d="M10,10 L90,10 L90,90 L10,90 Z"/>'
          '<path d="M20,20 L80,80"/></g></svg>')


def write(tmp, name, text):
    path = os.path.join(tmp, name)
    with open(path, "w") as fh:
        fh.write(text)
    return path


def test_driver(tmp):
    print("driver (preview only -- never opens the port):")
    check("AxiDraw python sources found", driver.available(),
          "looked in %s" % driver.deps_dir())
    if not driver.available():
        return
    check("version reported", (driver.version() or "").startswith("3."),
          str(driver.version()))

    d = driver.InProcessDriver()
    path = write(tmp, "square.svg", SQUARE)
    r = d.preview(path, {"model": 3})
    check("preview estimates a time", r["estTimeSec"] > 1, str(r["estTimeSec"]))
    check("preview measures the draw length",
          abs(r["drawLenM"] - 0.405) < 0.02, str(r["drawLenM"]))
    check("preview measures pen-up travel", r["penUpLenM"] > 0, str(r["penUpLenM"]))
    check("preview is fast enough to run per layer", r["tookSec"] < 0.5,
          "%.3f s" % r["tookSec"])
    check("preview did not leave the driver busy", not d.busy())

    # the same numbers the subprocess parser would have produced
    parsed = plotter.parse_preview(r["raw"])
    check("in-process output still parses as CLI output",
          parsed["estTimeSec"] is not None
          and abs(parsed["estTimeSec"] - r["estTimeSec"]) < 0.5,
          str(parsed))

    # options reach the machine layer: a slower pen must plan a longer plot
    slow = driver.InProcessDriver().preview(path, {"model": 3, "speedPenDown": 10})
    check("plot options change the plan", slow["estTimeSec"] > r["estTimeSec"] * 1.2,
          "%.1f vs %.1f" % (slow["estTimeSec"], r["estTimeSec"]))

    d.stop()
    check("stop is safe with nothing running", d.pause_event.is_set())


def test_progress_feed():
    print("progress feed:")
    if not driver.available():
        return
    seen = []
    feed = driver.ProgressFeed(lambda **kw: seen.append(kw))
    check("it IS the AxiDraw's ProgressBar",
          isinstance(feed, driver._load()["plot_status"].ProgressBar))

    class Stats:
        down_travel_inch = 0.0
        up_travel_inch = 0.0
        pt_estimate = 20000

    class AD:
        class plot_status:
            stats = Stats()

    feed.enable = True
    feed.total = 1000.0
    feed.launch(AD)
    stats = Stats()
    for inch in (5, 10, 19.685):          # 127 mm, 254 mm, 500 mm
        stats.down_travel_inch = inch
        feed.update_auto(stats)
    feed.close()

    phases = [s["phase"] for s in seen]
    check("start / plot / done all reported",
          phases[0] == "start" and phases[-1] == "done"
          and phases.count("plot") == 3, str(phases))
    fracs = [round(s["fraction"], 3) for s in seen]
    check("fraction climbs to 1.0",
          fracs == sorted(fracs) and fracs[-1] == 1.0, str(fracs))
    check("millimetres, not inches",
          abs(seen[2]["done_mm"] - 254) < 0.5, str(seen[2]["done_mm"]))
    check("time remaining is offered", seen[1]["remaining"] is not None)
    check("a disabled feed stays silent",
          (lambda f: (setattr(f, "enable", False), f.update_auto(stats),
                      len(f.seen))[-1] == 0)(
              type("F", (), {"seen": [], "enable": True,
                             "update_auto": driver.ProgressFeed.update_auto})()))


def test_layer_state():
    print("layer state:")
    job = {"hash": "0xabc", "mode": "color",
           "paperSize": {"width_mm": 500, "height_mm": 217},
           "pens": [{"label": "a", "color": "rgb(1,2,3)"},
                    {"label": "b", "color": "rgb(4,5,6)"}]}
    st = run.LayerState()
    check("a fresh drawing clears nothing it does not have",
          st.sync(run.job_stamp(job), 2) is True and st.pending() == [0, 1])

    st.mark(0)
    check("a plotted layer is marked", st.is_done(0) and st.pending() == [1])
    check("the same drawing keeps its marks",
          st.sync(run.job_stamp(job), 2) is False and st.pending() == [1])

    other = dict(job, hash="0xdef")
    check("a different token clears them",
          st.sync(run.job_stamp(other), 2) is True and st.pending() == [0, 1])

    st.mark(0)
    st.mark(1)
    check("all layers done reads complete", st.complete())
    resized = dict(job, paperSize={"width_mm": 400, "height_mm": 217})
    check("a resize clears them too",
          st.sync(run.job_stamp(resized), 2) is True and not st.complete())

    st.mark(1)
    round_trip = run.LayerState.from_dict(st.to_dict())
    check("state survives a save/load",
          round_trip.done == st.done and round_trip.stamp == st.stamp
          and round_trip.total == st.total)

    dropped = dict(job, pens=[dict(job["pens"][0]), dict(job["pens"][1],
                                                        include=False)])
    st2 = run.LayerState()
    st2.sync(run.job_stamp(job), 2)
    st2.mark(0)
    check("de-selecting a pen is a different drawing",
          st2.sync(run.job_stamp(dropped), 1) is True)


class Recorder:
    """Stands in for the machine. Records what it was asked to plot, and can
    be told to report a stop."""

    def __init__(self, stop_at=None, progress_steps=2):
        self.plotted = []
        self.stop_at = stop_at
        self.on_progress = None
        self.progress_steps = progress_steps

    def plot(self, svg_path, opts=None, progress=True):
        self.plotted.append(svg_path)
        for i in range(self.progress_steps):
            if self.on_progress:
                self.on_progress(phase="plot", done_mm=100.0 * (i + 1),
                                 total_mm=100.0 * self.progress_steps,
                                 fraction=(i + 1) / self.progress_steps,
                                 elapsed=1.0, remaining=1.0)
        stopped = self.stop_at is not None and len(self.plotted) > self.stop_at
        return {"stopped": stopped, "code": 1 if stopped else 0}


def a_job(tmp):
    from axiplot import colorsplit
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
           '<path stroke="rgb(1,2,3)" d="M0,0 L10,10"></path>'
           '<path stroke="rgb(4,5,6)" d="M0,10 L10,0"></path>'
           '<path stroke="rgb(7,8,9)" d="M5,0 L5,10"></path></svg>')
    colors = [l["color"] for l in colorsplit.split_by_color(svg)["layers"]]
    return {"svg": svg, "hash": "0xfeed", "mode": "color",
            "paperSize": {"width_mm": 100, "height_mm": 100},
            "pens": [{"color": c, "label": "pen%d" % i}
                     for i, c in enumerate(colors)],
            "optimizer": "js"}


def test_run_loop(tmp):
    print("run loop:")
    job = a_job(tmp)
    prep = plotter.prepare_layers(job, tmp_dir=tmp)
    check("three pens, three layers", len(prep["layers"]) == 3,
          str(len(prep["layers"])))

    sent, starts, progress = [], [], []
    notifier = notify.CallableNotifier(
        lambda t, m, d: sent.append((t, m, d)))
    rec = Recorder()
    state = run.LayerState()
    out = run.plot_job(job, rec, state=state, prepared=prep, notifier=notifier,
                       on_layer_start=lambda i, l, p, n: starts.append(i),
                       on_progress=lambda **kw: progress.append(kw))
    check("every layer plotted once", len(rec.plotted) == 3 and starts == [0, 1, 2])
    check("state says complete", out["complete"] and state.pending() == [])
    check("progress carries the layer index",
          len(progress) == 6 and progress[-1]["layer"] == 2
          and progress[-1]["layers"] == 3, str(len(progress)))
    check("one notification per layer, plus the finish",
          len(sent) == 4 and sent[0][0].startswith("Layer 1/3")
          and sent[-1][0] == "Plot finished", str([s[0] for s in sent]))
    check("the layer note says which pen to swap to",
          "swap to" in sent[0][1] and "pen1" in sent[0][1], sent[0][1])
    check("the last layer says the plot is complete",
          "plot complete" in sent[2][1], sent[2][1])

    # resume: the same job, two layers already marked
    rec2 = Recorder()
    out2 = run.plot_job(job, rec2, state=state, prepared=prep)
    check("nothing left to plot on a finished drawing", rec2.plotted == [])

    state.mark(1, False)
    rec3 = Recorder()
    run.plot_job(job, rec3, state=state, prepared=prep)
    check("only the un-plotted layer runs again",
          len(rec3.plotted) == 1 and rec3.plotted[0].endswith(
              os.path.basename(prep["layers"][1]["svgPath"])),
          str(rec3.plotted))

    # a stop leaves the rest pending
    state2 = run.LayerState()
    rec4 = Recorder(stop_at=1)   # the machine stops during the SECOND layer
    out4 = run.plot_job(job, rec4, state=state2, prepared=prep)
    check("a stop ends the run", out4["stopped"] and len(rec4.plotted) == 2)
    check("the stopped layer is NOT marked done",
          state2.done == {0} and state2.pending() == [1, 2],
          str(state2.to_dict()))

    # an operator who declines the pen swap stops the run
    state3 = run.LayerState()
    rec6 = Recorder()
    out6 = run.plot_job(job, rec6, state=state3, prepared=prep,
                        on_layer_start=lambda i, l, p, n: i < 1)
    check("declining the pen change stops the run",
          out6["stopped"] and len(rec6.plotted) == 1
          and state3.pending() == [1, 2], str(state3.to_dict()))

    # a new drawing wipes the marks
    other = dict(job, hash="0xbeef")
    rec5 = Recorder()
    run.plot_job(other, rec5, state=state2, prepared=prep)
    check("a new drawing re-plots everything", len(rec5.plotted) == 3)


def test_optimizer_output_is_parseable():
    """The optimizer rebuilds a document; it has to rebuild a valid one.

    The JS never closes a <path> and drops the </g> the head opened, so its
    output nests every path inside the previous one -- 256 deep, which strict
    parsers refuse outright. The in-process AxiDraw driver is a strict parser,
    so this is the difference between a plottable file and an exception.
    """
    print("optimizer output:")
    import xml.etree.ElementTree as ET
    from axiplot import colorsplit, optimize

    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
           '<g fill="none">'
           + "".join('<path stroke="rgb(1,2,3)" d="M%d,0 L%d,10"></path>'
                     % (i, i + 1) for i in range(12))
           + '</g></svg>')
    layer = colorsplit.split_by_color(svg)["layers"][0]["svg"]
    out = optimize.optimize_svg(layer, {"sort": True})["svg"]
    try:
        ET.fromstring(out)
        parsed = True
    except ET.ParseError as exc:
        parsed = False
        detail = str(exc)
    check("optimized output is well-formed XML", parsed,
          "" if parsed else detail)
    check("paths are closed", out.count("<path") == out.count("</path>"),
          "%d open, %d closed" % (out.count("<path"), out.count("</path>")))
    check("the group the head opened is closed too",
          out.count("<g") == out.count("</g>"),
          "%d open, %d closed" % (out.count("<g"), out.count("</g>")))

    optimize.JS_UNCLOSED_PATHS = True
    try:
        js = optimize.optimize_svg(layer, {"sort": True})["svg"]
        check("the JS spelling is still reachable, and still unclosed",
              "</path>" not in js and js.endswith("</svg>"), js[-40:])
    finally:
        optimize.JS_UNCLOSED_PATHS = False


def test_calibration():
    """The registration sheet is pure geometry -- it does not need the GUI
    that used to be the only thing checking it."""
    print("calibration sheet:")
    from axiplot import calibration as cal
    bed = plotter.bed_mm(3)

    geo = cal.layout({"pens": 7})
    check("seven pens, seven rings", geo["n"] == 7)
    check("the block is as wide as its widest figure",
          geo["blockW"] >= geo["lineLenMm"] and geo["blockW"] >= 2 * geo["bull"]["rMax"],
          str(geo["blockW"]))
    check("columns are pitched a gap apart",
          abs(geo["setPitch"] - (geo["blockW"] + geo["setGapMm"])) < 1e-9,
          str(geo["setPitch"]))
    check("it fits the XLX", cal.fits_bed(geo, bed["wMm"], bed["hMm"])["fits"])

    col3 = cal.layout({"pens": 7, "set": 3})
    check("column 3 sits three pitches right",
          abs(col3["originX"] - (geo["originX"] + 3 * geo["setPitch"])) < 1e-9,
          "%s vs %s" % (col3["originX"], geo["originX"]))

    paths = cal.pen_paths(0, geo)
    check("each pen draws a ring, a vertical and a horizontal", len(paths) == 3)
    def radius(path):                 # "M29,35A6,6 0 1 0 ..." -> 6.0
        return float(path.split("A", 1)[1].split(",", 1)[0])
    r0 = radius(cal.pen_paths(0, geo)[0])
    r6 = radius(cal.pen_paths(6, geo)[0])
    check("each pen rings one spacing wider than the last",
          abs((r6 - r0) - 6 * geo["spacingMm"]) < 1e-9
          and abs(r0 - geo["innerRadiusMm"]) < 1e-9,
          "%s -> %s" % (r0, r6))

    one = cal.pen_svg(geo, bed, 0)
    check("a pen sheet is three paths", one.count("<path") == 3)
    check("sized in millimetres for the bed",
          ('width="%smm"' % bed["wMm"]).split(".")[0] in one, one[:120])
    many = cal.pen_svg_sets(geo, bed, 0, sets=[0, 1, 2])
    check("three columns is nine paths", many.count("<path") == 9,
          str(many.count("<path")))
    check("and starts with the single-column drawing",
          many.startswith(one[:one.index("<path")]))
    sheet = cal.sheet_svg(geo, bed)
    check("the whole sheet is every pen", sheet.count("<path") == 3 * geo["n"],
          str(sheet.count("<path")))

    try:
        cal.pen_svg(geo, bed, 7)
        check("a pen off the end of the sheet is refused", False)
    except ValueError:
        check("a pen off the end of the sheet is refused", True)


def test_awake():
    """The inhibitor: taken, listed by logind, and gone when released."""
    import shutil
    import subprocess
    import time
    print("sleep inhibitor:")
    from axiplot import awake
    inh = awake.SleepInhibitor(why="axiplot gate", who="axiplot gate")
    if not shutil.which("systemd-inhibit"):
        check("no systemd-inhibit: starting says so and does not raise",
              inh.start() is False and not inh.active()
              and "no systemd-inhibit" in inh.reason)
        return
    def rows(who, want=True, timeout=4.0):
        """logind registers the lock a moment after the process starts, so
        poll for the state we are expecting rather than racing it."""
        end = time.time() + timeout
        while True:
            out = subprocess.run(["systemd-inhibit", "--list"],
                                 capture_output=True, text=True).stdout
            found = [l for l in out.splitlines() if l.startswith(who)]
            if bool(found) == want or time.time() > end:
                return found
            time.sleep(0.2)

    check("the lock is taken", inh.start() and inh.active())
    row = rows("axiplot gate")
    check("logind lists it, blocking both idle and sleep",
          len(row) == 1 and "block" in row[0]
          and "idle" in row[0] and "sleep" in row[0], str(row))
    check("starting twice keeps the one lock",
          inh.start() and len(rows("axiplot gate")) == 1)
    inh.stop()
    check("releasing gives it back",
          not inh.active() and not rows("axiplot gate", want=False))
    # The guarantee that matters: a process that dies without cleaning up
    # still drops the lock, because the pipe dies with it.
    inh2 = awake.SleepInhibitor(why="axiplot gate kill", who="axiplot gate kill")
    inh2.start()
    rows("axiplot gate kill")
    inh2.proc.kill()
    inh2.proc.wait(timeout=5)
    check("a killed holder does not leak the lock",
          not rows("axiplot gate kill", want=False))
    check("and it knows it is no longer holding", not inh2.active())


def test_notifiers():
    print("notifiers:")
    layer = {"label": "cyan", "hex": "#00ffff", "paths": 412}
    title, msg = notify.layer_message(layer, 0, 4, 91,
                                      {"label": "magenta", "estSec": 300})
    check("title names the layer and the count",
          title == "Layer 1/4 done -- cyan", title)
    check("message has duration, paths, next pen and the time left",
          "1 min 31 s" in msg and "412 paths" in msg
          and "swap to magenta" in msg and "5 min" in msg, msg)
    _, last = notify.layer_message(layer, 3, 4, 10)
    check("the final layer says so", "plot complete" in last, last)

    ha = notify.HomeAssistantNotifier("", "", "")
    check("an unconfigured HA notifier is a no-op",
          ha.configured() is False and ha.send("a", "b") is False)
    ha2 = notify.HomeAssistantNotifier("http://127.0.0.1:1", "tok",
                                       "notify/phone", timeout=0.2)
    check("an unreachable HA notifier fails quietly",
          ha2.configured() and ha2.send("a", "b") is False
          and ha2.last_error is not None)

    check("a dotted service is turned into HA's REST path",
          notify.HomeAssistantNotifier("u", "t", "notify.phone").service
          == "notify/phone")
    check("a script service is sent the level, a notify service is not",
          "level" in notify.HomeAssistantNotifier(
              "u", "t", "script.send_alert", level="warning")._payload_probe()
          and "level" not in notify.HomeAssistantNotifier(
              "u", "t", "notify.phone", level="warning")._payload_probe())

    # -- MQTT: the transport for a machine with no HA token -- #
    mq = notify.MqttNotifier("")
    check("an unconfigured MQTT notifier is a no-op",
          mq.configured() is False and mq.send("a", "b") is False)
    mq2 = notify.MqttNotifier("127.0.0.1", "u", "p", "alerts/raise",
                              port=1, timeout=0.2)
    check("an unreachable broker fails quietly",
          mq2.configured() and mq2.send("a", "b") is False
          and mq2.last_error is not None)
    conn, pub = mq2._packets('{"a":1}')
    check("CONNECT is MQTT 3.1.1 with a username and password",
          conn[0] == 0x10 and b"MQTT" in conn and conn[8] == 4
          and conn[9] == 0xC2 and b"\x00\x01u" in conn and b"\x00\x01p" in conn,
          conn.hex())
    check("PUBLISH is QoS 0 and carries topic then payload",
          pub[0] == 0x30 and pub[2:4] == b"\x00\x0c"
          and pub[4:16] == b"alerts/raise" and pub.endswith(b'{"a":1}'),
          pub.hex())
    check("every connection gets its own client id -- two alerts can leave "
          "at the same instant",
          mq2._packets("x")[0] != mq2._packets("x")[0])
    check("the level rides in the payload",
          b'"level": "warning"' in notify.MqttNotifier(
              "h", level="warning")._packets(
                  __import__("json").dumps({"level": "warning"}))[1])

    got = []
    multi = notify.MultiNotifier(ha2, notify.CallableNotifier(
        lambda t, m, d: got.append(t)))
    check("one dead transport does not stop the others",
          multi.send("x", "y") is True and got == ["x"])

    fired = []
    async_n = notify.Async(notify.CallableNotifier(
        lambda t, m, d: fired.append(t)))
    async_n.send("z", "w")
    for _ in range(200):
        if fired:
            break
        import time as _t
        _t.sleep(0.005)
    check("async delivery still arrives", fired == ["z"])


def main():
    tmp = tempfile.mkdtemp(prefix="axiplot-gate-")
    test_driver(tmp)
    test_progress_feed()
    test_layer_state()
    test_run_loop(tmp)
    test_optimizer_output_is_parseable()
    test_calibration()
    test_awake()
    test_notifiers()
    print("\naxiplot: %d passed, %d failed" % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
