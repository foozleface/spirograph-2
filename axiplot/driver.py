"""The AxiDraw, driven in-process instead of through a subprocess.

``plotter.Plotter`` shells out to the frozen ``axidraw_control`` binary and can
only report what a finished process printed. The same software ships as plain
Python next to it (``axidraw_deps/axidrawinternal``, 3.9.5 here), and importing
that buys three things the subprocess cannot give:

* **Live progress.** The CLI's progress bar works by doing a dry run first to
  total up the travel, then counting millimetres as the plot goes. Both halves
  are just method calls on ``plot_status.progress`` -- so a subclass that emits
  callbacks instead of drawing a TQDM bar turns them into a real progress feed.
* **A graceful stop.** ``set_up_pause_receiver`` takes a threading Event; when
  it is set the plotter finishes its segment, raises the pen and writes resume
  data. That is a pause you can come back from, not a killed process.
* **Estimates that cost 3 ms** rather than a 1-2 s process launch, because a
  preview is the same call with ``preview=True``.

The import is optional and the failure mode is boring: ``available()`` returns
False and callers fall back to ``plotter.Plotter``. Nothing here is a port of
anything -- it drives Evil Mad Scientist's own code.
"""

import os
import sys
import threading
import time

DEFAULT_DEPS = os.path.expanduser(
    "~/.config/inkscape/extensions/axidraw_deps")

# lxml and pyserial are what the AxiDraw sources need and what a bare venv is
# missing; on Debian/Ubuntu the Inkscape packages put them here, built for the
# same interpreter. Appended, never prepended: the venv still wins.
SYSTEM_SITE = "/usr/lib/python3/dist-packages"

_MODULES = None


def deps_dir():
    return os.environ.get("AXIDRAW_PY_DEPS") or DEFAULT_DEPS


def _load():
    """Import the AxiDraw sources once, or return None. Never raises."""
    global _MODULES
    if _MODULES is not None:
        return _MODULES or None
    # LOCAL CHANGE (spirograph-2): this repo installs the AxiDraw API into its
    # own venv, so axidrawinternal is already importable and is the version
    # pyaxidraw elsewhere in the process would use. Prefer it; prepending
    # Inkscape's copy would shadow it with a different release of the same
    # package inside one interpreter.
    mods = _import_modules()
    if mods:
        _MODULES = mods
        return mods
    path = deps_dir()
    if not os.path.isdir(path):
        _MODULES = False
        return None
    for entry in (path, SYSTEM_SITE):
        if entry not in sys.path and os.path.isdir(entry):
            sys.path.append(entry) if entry == SYSTEM_SITE else sys.path.insert(0, entry)
    mods = _import_modules()
    if not mods:                            # any import problem: stay optional
        _MODULES = False
        return None
    _MODULES = mods
    return mods


def _import_modules():
    """The three AxiDraw modules, or None if they are not importable."""
    try:
        from importlib import import_module
        return {
            "axidraw": import_module("axidrawinternal.axidraw"),
            "conf": import_module("axidrawinternal.axidraw_conf"),
            "plot_status": import_module("axidrawinternal.plot_status"),
        }
    except Exception:
        return None


def available():
    return _load() is not None


def version():
    mods = _load()
    return getattr(mods["axidraw"], "__version__", "?") if mods else None


# The options axidraw_control hands down to a unit, same list, same names.
PASS_THROUGH = [
    "mode", "speed_pendown", "speed_penup", "accel", "pen_pos_up",
    "pen_pos_down", "pen_rate_raise", "pen_rate_lower", "pen_delay_up",
    "pen_delay_down", "no_rotate", "const_speed", "report_time", "manual_cmd",
    "dist", "layer", "copies", "page_delay", "preview", "rendering", "model",
    "penlift", "setup_type", "resume_type", "auto_rotate", "resolution",
    "hiding", "reordering", "random_start", "webhook", "webhook_url",
    "digest", "progress",
]

# our option dict (the one option_flags speaks) -> the AxiDraw option name
FROM_JOB = {
    "speedPenDown": "speed_pendown", "speedPenUp": "speed_penup",
    "accel": "accel", "penPosUp": "pen_pos_up", "penPosDown": "pen_pos_down",
    "penRateRaise": "pen_rate_raise", "penRateLower": "pen_rate_lower",
    "penDelayUp": "pen_delay_up", "penDelayDown": "pen_delay_down",
    "constSpeed": "const_speed", "autoRotate": "auto_rotate",
    "reordering": "reordering", "copies": "copies", "model": "model",
    "penlift": "penlift", "pageDelay": "page_delay",
    "randomStart": "random_start", "hiding": "hiding",
}


class ProgressFeed:
    """Stands in for the CLI's TQDM progress bar and calls you instead.

    Subclasses the real ``ProgressBar`` so the dry-run bookkeeping in
    ``review``/``restore`` -- which is where the total travel and the time
    estimate come from -- keeps working untouched. Only the drawing is
    replaced.
    """

    def __new__(cls, on_progress=None):
        mods = _load()
        base = mods["plot_status"].ProgressBar
        klass = type("ProgressFeed", (base,), dict(cls.__dict__))
        obj = base.__new__(klass)
        base.__init__(obj)
        obj.on_progress = on_progress or (lambda **kw: None)
        obj.started_at = None
        obj.est_seconds = None
        return obj

    def _emit(self, done_mm, phase):
        total = self.total or 0
        frac = (done_mm / total) if total > 0 else 0.0
        elapsed = time.time() - self.started_at if self.started_at else 0.0
        remaining = None
        if self.est_seconds is not None:
            remaining = max(0.0, self.est_seconds - elapsed)
        elif frac > 0.02:
            remaining = elapsed * (1 - frac) / frac
        self.on_progress(phase=phase, done_mm=done_mm, total_mm=total,
                         fraction=min(1.0, frac), elapsed=elapsed,
                         remaining=remaining)

    # -- the ProgressBar interface the AxiDraw code calls ------------------- #

    def launch(self, ad_ref):
        if not self.enable:
            return
        self.started_at = time.time()
        est = getattr(ad_ref.plot_status.stats, "pt_estimate", None)
        self.est_seconds = (est / 1000.0) if est else None
        self._emit(self.last, "start")

    def update_auto(self, status_ref):
        if not self.enable:
            return
        self.last = 25.4 * (status_ref.down_travel_inch + status_ref.up_travel_inch)
        self._emit(self.last, "plot")

    def close(self):
        if self.enable:
            self._emit(self.total, "done")
        self.last = 0

    def launch_sub(self, ad_ref, total_in, page=True):
        if self.enable:
            self.on_progress(phase="delay", done_mm=self.last,
                             total_mm=self.total, fraction=0.0,
                             elapsed=0.0, remaining=total_in / 1000.0)

    def update_sub_rel(self, update_amount):
        pass

    def close_sub(self):
        pass


class InProcessDriver:
    """The same jobs ``plotter.Plotter`` runs, without leaving the process.

    ``on_progress(phase, done_mm, total_mm, fraction, elapsed, remaining)`` is
    called from the plotting thread -- marshal it before touching a GUI.
    """

    def __init__(self, defaults=None, on_progress=None, on_message=None):
        from axiplot.plotter import DEFAULTS
        self.defaults = dict(DEFAULTS, **(defaults or {}))
        self.on_progress = on_progress
        self.on_message = on_message or (lambda text: None)
        self.pause_event = threading.Event()
        self.messages = []
        self._ad = None

    # -- setup -------------------------------------------------------------- #

    def _new(self, opts, preview, progress):
        mods = _load()
        if mods is None:
            raise RuntimeError("AxiDraw Python sources not found (looked in %s)"
                               % deps_dir())
        opts = dict(self.defaults, **(opts or {}))
        ad = mods["axidraw"].AxiDraw(params=mods["conf"], default_logging=False)
        self.pause_event.clear()
        ad.set_up_pause_receiver(self.pause_event)
        ad.getoptions([])
        for key in PASS_THROUGH:             # CLI-only options are not defaults
            if not hasattr(ad.options, key):
                setattr(ad.options, key, False if key == "progress" else None)
        ad.options.mode = "plot"
        for ours, theirs in FROM_JOB.items():
            if opts.get(ours) is not None:
                setattr(ad.options, theirs, opts[ours])
        ad.options.preview = bool(preview)
        ad.options.rendering = 3 if preview else 0
        ad.options.report_time = True
        ad.options.progress = bool(progress and not preview)
        port = opts.get("port")
        ad.options.port = port or None
        ad.options.port_config = 2 if port else 1
        ad.plot_status.cli_api = True        # unlocks the progress path
        self.messages = []

        def message(text):
            text = (text or "").strip()
            if text:
                self.messages.append(text)
                self.on_message(text)
        ad.user_message_fun = message
        if ad.options.progress:
            ad.plot_status.progress = ProgressFeed(self.on_progress)
        return ad, opts

    def _run(self, ad, svg_path):
        ad.parse(svg_path)
        ad.original_document = ad.document
        self._ad = ad
        try:
            ad.effect()
        finally:
            self._ad = None
        return ad

    # -- jobs --------------------------------------------------------------- #

    def preview(self, svg_path, opts=None):
        """Motion-plan the file without a machine. Milliseconds, no port."""
        ad, _ = self._new(opts, preview=True, progress=False)
        t0 = time.time()
        self._run(ad, svg_path)
        st = ad.plot_status.stats
        return {"estTimeSec": (st.pt_estimate or 0) / 1000.0,
                "drawLenM": st.down_travel_inch * 0.0254,
                "penUpLenM": st.up_travel_inch * 0.0254,
                "totalLenM": (st.down_travel_inch + st.up_travel_inch) * 0.0254,
                "tookSec": time.time() - t0,
                "raw": "\n".join(self.messages)}

    def plot(self, svg_path, opts=None, progress=True):
        """Plot it. Returns {stopped, stats, raw}; ``stopped`` is the AxiDraw's
        own status code, non-zero when the pause request landed."""
        ad, _ = self._new(opts, preview=False, progress=progress)
        self._run(ad, svg_path)
        st = ad.plot_status.stats
        return {"stopped": bool(ad.plot_status.stopped),
                "code": ad.plot_status.stopped,
                "drawLenM": st.down_travel_inch * 0.0254,
                "penUpLenM": st.up_travel_inch * 0.0254,
                "raw": "\n".join(self.messages)}

    def stop(self):
        """Ask for a pause: the current segment finishes, the pen goes up and
        resume data is written. Safe to call when nothing is running."""
        self.pause_event.set()

    def busy(self):
        return self._ad is not None
