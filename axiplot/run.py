"""The layer loop: prepare, plot each layer, say where you are as you go.

This is the part every plotting program rewrites badly. It owns three things
the GUI used to own inline:

* **which layers are already done**, so a plot that was stopped, or a nib that
  needed re-inking, resumes where it left off instead of drawing a layer twice;
* **progress**, both within a layer (from ``driver.InProcessDriver``, in
  millimetres of travel) and across the job;
* **who gets told** when a layer finishes -- the moment a person has to walk
  over and swap a pen.

Every report is a callback, so this module knows nothing about Qt, and a
headless script gets the same behaviour as the app.
"""

import time

from axiplot import plotter as plotmod


class LayerState:
    """Which layers of WHICH drawing have been plotted.

    Keyed by a stamp of the drawing (its hash, size and pen set): a new
    drawing clears the marks, the same drawing keeps them. That is the whole
    trick -- the alternative, trusting the operator to remember, is how a
    sheet gets a layer drawn on it twice.
    """

    def __init__(self, stamp=None, done=None, total=0):
        self.stamp = stamp
        self.done = set(done or ())
        self.total = total

    # -- lifecycle ---------------------------------------------------------- #

    def sync(self, stamp, total):
        """Point at a drawing. Returns True if the marks were cleared because
        it is a different one."""
        changed = (stamp != self.stamp) or (total != self.total and self.done
                                            and max(self.done) >= total)
        if changed:
            self.done = set()
        self.stamp = stamp
        self.total = total
        return changed

    def mark(self, index, done=True):
        if done:
            self.done.add(int(index))
        else:
            self.done.discard(int(index))

    def clear(self):
        self.done = set()

    # -- queries ------------------------------------------------------------ #

    def is_done(self, index):
        return int(index) in self.done

    def pending(self):
        return [i for i in range(self.total) if i not in self.done]

    def complete(self):
        return self.total > 0 and len(self.pending()) == 0

    def to_dict(self):
        return {"stamp": self.stamp, "done": sorted(self.done),
                "total": self.total}

    @classmethod
    def from_dict(cls, raw):
        raw = raw or {}
        return cls(raw.get("stamp"), raw.get("done") or (), raw.get("total") or 0)


def job_stamp(job):
    """What makes this drawing THIS drawing, for the purposes of "have we
    already plotted layer 3?": the token, the physical size, and the pen set.
    Change any of those and the marks no longer mean anything."""
    paper = job.get("paperSize") or {}
    pens = job.get("pens") or []
    return "|".join(str(x) for x in [
        job.get("hash") or "",
        job.get("mode") or "mono",
        round(float(paper.get("width_mm") or 0), 3),
        round(float(paper.get("height_mm") or 0), 3),
        ";".join("%s:%s" % (p.get("label") or p.get("color"),
                            "1" if p.get("include") is not False else "0")
                 for p in pens),
    ])


def estimate_layers(layers, driver=None, opts=None, on_layer=None):
    """Per-layer seconds, measured by motion-planning each one. With the
    in-process driver this is milliseconds per layer, so it is worth doing up
    front rather than guessing."""
    out = []
    for i, layer in enumerate(layers):
        est = None
        if driver is not None:
            try:
                est = driver.preview(layer["svgPath"], opts)["estTimeSec"]
            except Exception:
                est = None
        if est is None:
            est = plotmod.predict_layer_sec(layer, opts)
        layer["estSec"] = est
        out.append(est)
        if on_layer:
            on_layer(i, est)
    return out


def plot_job(job, driver, state=None, prepared=None, notifier=None,
             on_prepare=None, on_layer_start=None, on_progress=None,
             on_layer_done=None, on_done=None, opts=None, skip_done=True):
    """Plot every layer that is not already marked done.

    ``driver`` is anything with ``.plot(svg_path, opts, progress=...)`` and
    optionally ``.preview``; both ``driver.InProcessDriver`` and
    ``plotter.Plotter`` fit (the latter without live progress).

    Returns a summary dict. Raises nothing on a stop: a stopped layer is
    reported and the loop ends, leaving the marks intact so the next run
    resumes.
    """
    started = time.time()
    prep = prepared or plotmod.prepare_layers(job)
    layers = prep["layers"]
    opts = dict(prep.get("opts") or {}, **(opts or {}))

    state = state or LayerState()
    cleared = state.sync(job_stamp(job), len(layers))
    if on_prepare:
        on_prepare(layers, cleared)

    todo = state.pending() if skip_done else list(range(len(layers)))
    results = []
    stopped = False

    for pos, index in enumerate(todo):
        layer = layers[index]
        if on_layer_start:
            # Returning False is how a caller says "the operator aborted at the
            # pen-change prompt" -- the loop stops without marking anything.
            if on_layer_start(index, layer, pos, len(todo)) is False:
                stopped = True
                break

        if on_progress:
            def report(**kw):
                kw["layer"] = index
                kw["layers"] = len(layers)
                kw["layer_position"] = pos
                kw["layers_to_plot"] = len(todo)
                on_progress(**kw)
            if hasattr(driver, "on_progress"):
                driver.on_progress = report

        t0 = time.time()
        result = driver.plot(layer["svgPath"], opts)
        seconds = time.time() - t0
        result = dict(result or {}, seconds=seconds, index=index)
        results.append(result)

        if result.get("stopped"):
            stopped = True
            if on_layer_done:
                on_layer_done(index, layer, result, False)
            break

        state.mark(index)
        nxt = None
        for later in todo[pos + 1:]:
            nxt = layers[later]
            break
        if on_layer_done:
            on_layer_done(index, layer, result, True)
        if notifier is not None:
            try:
                notifier.layer_done(layer, index, len(layers), seconds, nxt)
            except Exception:
                pass

    summary = {"layers": layers, "results": results, "stopped": stopped,
               "cleared": cleared, "seconds": time.time() - started,
               "state": state, "complete": state.complete()}
    if not stopped and notifier is not None and state.complete():
        try:
            notifier.plot_done(layers, summary["seconds"])
        except Exception:
            pass
    if on_done:
        on_done(summary)
    return summary
