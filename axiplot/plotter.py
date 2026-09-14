"""``app/plotter.js`` + the plot pipeline from ``app/main.js``.

Drives the SAME toolchain the Electron app uses: the ``axidraw_control``
PyInstaller binary from the Inkscape AxiDraw extension (spawned with cwd =
the extension dir, which the binary requires to resolve ``axidrawinternal``),
and vpype from the app's own venv. ``pyaxidraw`` stays a seam: if it ever
becomes importable, a native backend can replace ``_run`` without touching
the callers.

The pure parts -- ``option_flags``, ``parse_preview``, ``connect_failed``,
``predict_layer_sec``, ``bed_mm``, ``size_for_plot``, ``layer_work``,
``prepare_layers`` -- are importable without hardware and are what the gate
tests. Everything that moves the pen requires the machine.
"""

import os
import re
import subprocess
import tempfile
import time

from axiplot import colorsplit, optimize as optmod, svgutil

HOME = os.path.expanduser("~")
DEFAULT_EXT_DIR = os.path.join(HOME, ".config", "inkscape", "extensions")
DEFAULT_BIN = os.path.join(DEFAULT_EXT_DIR, "build_deps", "axidraw_control")
DEFAULT_VPYPE = os.path.join(HOME, "busy-onchain", "app", ".venv", "bin", "vpype")

AXIDRAW_MODELS = {
    1: {"label": "AxiDraw V2 / V3 (A4)", "width": 11.81, "height": 8.58},
    2: {"label": "AxiDraw V3/A3 or SE/A3", "width": 16.93, "height": 11.69},
    3: {"label": "AxiDraw V3 XLX", "width": 23.42, "height": 8.58},
    4: {"label": "AxiDraw MiniKit", "width": 6.3, "height": 4.0},
    5: {"label": "AxiDraw SE/A1", "width": 34.02, "height": 23.39},
    6: {"label": "AxiDraw SE/A2", "width": 23.39, "height": 17.01},
}

DEFAULTS = {
    "model": 3,
    "port": "/dev/ttyACM0",
    "penlift": 3,
    "speedPenDown": 25,
    "speedPenUp": 75,
    "accel": 75,
    "penPosUp": 60,
    "penPosDown": 30,
    "penRateLower": 50,
    "penRateRaise": 75,
    "constSpeed": False,
    "autoRotate": True,
    "reordering": 2,
    "copies": 1,
}


def bed_mm(model):
    m = AXIDRAW_MODELS.get(model, AXIDRAW_MODELS[3])
    return {"wMm": m["width"] * 25.4, "hMm": m["height"] * 25.4,
            "label": m["label"]}


def connect_failed(text):
    return bool(re.search(r"Failed to connect to AxiDraw", text or "", re.I))


def parse_preview(text):
    """``parsePreview`` -- the binary's --preview/--report_time output."""
    def num(pattern):
        m = re.search(pattern, text, re.I)
        return float(m.group(1)) if m else None

    est_time_sec = None
    sec_m = re.search(r"Estimated print time:\s*([\d.]+)\s*Seconds", text, re.I)
    if sec_m:
        est_time_sec = float(sec_m.group(1))
    else:
        clk = re.search(r"Estimated print time:\s*(?:(\d+):)?(\d+):(\d+)", text, re.I)
        if clk:
            h = int(clk.group(1)) if clk.group(1) else 0
            est_time_sec = h * 3600 + int(clk.group(2)) * 60 + int(clk.group(3))
    return {
        "estTimeSec": est_time_sec,
        "drawLenM": num(r"Length of path to draw:\s*([\d.]+)\s*m"),
        "penUpLenM": num(r"Pen-up travel distance:\s*([\d.]+)\s*m"),
        "totalLenM": num(r"Total movement distance:\s*([\d.]+)\s*m"),
    }


def option_flags(opts=None, defaults=None):
    """``optionFlags`` -- the common --flag list shared by plot/preview."""
    p = dict(defaults or DEFAULTS)
    p.update(opts or {})
    flags = [
        "--model=%s" % p["model"],
        "--penlift=%s" % p["penlift"],
        "--speed_pendown=%s" % p["speedPenDown"],
        "--speed_penup=%s" % p["speedPenUp"],
        "--accel=%s" % p["accel"],
        "--pen_pos_up=%s" % p["penPosUp"],
        "--pen_pos_down=%s" % p["penPosDown"],
        "--pen_rate_lower=%s" % p["penRateLower"],
        "--pen_rate_raise=%s" % p["penRateRaise"],
        "--const_speed=%s" % ("true" if p["constSpeed"] else "false"),
        "--auto_rotate=%s" % ("true" if p["autoRotate"] else "false"),
        "--reordering=%s" % p["reordering"],
        "--copies=%s" % p["copies"],
    ]
    if p.get("port"):
        flags.append("--port=%s" % p["port"])
    return flags


def predict_layer_sec(layer, opts=None):
    """``predictLayerSec`` -- the binary reports nothing while plotting, so
    within-layer progress is a clock against this prediction (calibrated by
    what earlier layers really took)."""
    opts = opts or {}
    MAX_MM_S = 380
    LIFT_S = 0.16

    def pct(v, d):
        try:
            n = float(v)
        except (TypeError, ValueError):
            n = 0
        if not n:
            n = d
        return max(1, min(110, n)) / 100

    v_down = MAX_MM_S * pct(opts.get("speedPenDown"), 25)
    v_up = MAX_MM_S * pct(opts.get("speedPenUp"), 75)
    return ((layer.get("drawLenMm") or 0) / v_down
            + (layer.get("penUpLenMm") or 0) / v_up
            + (layer.get("paths") or 0) * LIFT_S)


# ---- the layer pipeline (from main.js) ------------------------------------- #

def size_for_plot(svg, job):
    """``sizeForPlot`` -- restate a layer SVG at physical mm."""
    vb = svgutil.get_view_box(svg)
    aspect = vb["w"] / vb["h"]
    paper = job.get("paperSize") or {}
    w_mm = paper.get("width_mm") or svgutil.px_to_mm(vb["w"])
    h_mm = paper.get("height_mm") or (w_mm / aspect)
    sized = svgutil.set_physical_size_mm(svg, w_mm, h_mm)
    return {"svg": sized["svg"], "widthMm": w_mm, "heightMm": h_mm}


def layer_work(svg, sized):
    """``layerWork`` -- paths / draw / pen-up, measured off the SVG that will
    actually be plotted (post-optimize)."""
    st = optmod.stats(optmod.parse_svg_paths(svg)["paths"])
    vb = svgutil.get_view_box(svg)
    upm = vb["w"] / sized["widthMm"] if sized["widthMm"] > 0 else 1
    return {"paths": st["paths"], "drawLenMm": st["drawLen"] / upm,
            "penUpLenMm": st["penUpLen"] / upm}


def prepare_layers(job, plotter=None, tmp_dir=None):
    """``prepareLayers`` -- split, size, optimize and measure each layer.

    ``job``: {svg, mode: "mono"|"color", pens, paperSize, opts, optimizer,
    vpype}. Uses the JS optimizer unless a ``plotter`` with working vpype is
    passed and the job allows it ("auto" prefers vpype, like the app).
    """
    opts = dict(DEFAULTS)
    opts.update(job.get("opts") or {})
    if job.get("mode") == "color":
        pens = [p for p in (job.get("pens") or []) if p.get("include") is not False]
        pens.sort(key=lambda p: p.get("order") or 0)
        groups = [{"colors": p["colors"] if p.get("colors") else [p["color"]],
                   "label": p.get("label")} for p in pens]
        if not groups:
            raise ValueError("no color layers selected")
        layers_out = colorsplit.split_by_groups(job["svg"], groups)
        raw = [{"color": l["colors"][0],
                "hex": colorsplit.rgb_to_hex(l["colors"][0]),
                "label": l["label"] or l["colors"][0],
                "count": l["count"], "svg": l["svg"]} for l in layers_out]
    else:
        raw = [{"color": None, "hex": None, "label": "single-pen",
                "svg": job["svg"]}]

    optimizer = job.get("optimizer") or (
        "none" if (job.get("vpype") or {}).get("enabled") is False else "auto")
    vpype_ok = plotter.vpype_available() if plotter else False
    use_vpype = (optimizer in ("vpype", "auto") and vpype_ok
                 and (job.get("vpype") or {}).get("enabled") is not False)
    use_js = not use_vpype and optimizer in ("js", "auto")

    if tmp_dir is None:
        tmp_dir = tempfile.mkdtemp(prefix="busy-plotter-")
    layers = []
    for i, L in enumerate(raw):
        s = size_for_plot(L["svg"], job)
        svg_path = os.path.join(
            tmp_dir, "layer-%d-%s.svg" % (i, re.sub(r"[^\w]", "", L["color"] or "mono")))
        with open(svg_path, "w") as fh:
            fh.write(s["svg"])
        optimized = False
        method = "none"
        final_svg = s["svg"]
        if use_vpype:
            out_path = svg_path[:-4] + ".opt.svg"
            try:
                plotter.optimize(svg_path, out_path, job.get("vpype") or {})
                svg_path = out_path
                with open(svg_path) as fh:
                    final_svg = fh.read()
                optimized, method = True, "vpype"
            except Exception:
                pass
        elif use_js:
            vb = svgutil.get_view_box(s["svg"])
            upm = vb["w"] / s["widthMm"]
            tol_mm = (job.get("vpype") or {}).get("toleranceMm") or 0.3
            r = optmod.optimize_svg(s["svg"], {
                "pointJoinRadius": 0.1 * upm,
                "sort": True,
                "minPathLength": 0.1 * upm,
                "pathJoinRadius": tol_mm * upm,
            })
            final_svg = r["svg"]
            with open(svg_path, "w") as fh:
                fh.write(final_svg)
            optimized, method = True, "js"
        layer = dict(L)
        layer.update({"svgPath": svg_path, "optimized": optimized,
                      "method": method, "widthMm": s["widthMm"],
                      "heightMm": s["heightMm"]})
        layer.update(layer_work(final_svg, s))
        layers.append(layer)
    return {"opts": opts, "layers": layers}


# ---- the machine driver ---------------------------------------------------- #

class Plotter:
    def __init__(self, bin_path=None, ext_dir=None, blank_svg=None,
                 vpype_bin=None, defaults=None, on_state=None, on_output=None):
        self.bin = bin_path or os.environ.get("AXIDRAW_BIN") or DEFAULT_BIN
        self.ext_dir = ext_dir or os.environ.get("AXIDRAW_EXT_DIR") \
            or os.path.dirname(os.path.dirname(self.bin))
        self.blank_svg = blank_svg or os.path.join(
            HOME, "busy-onchain", "app", "assets", "blank.svg")
        self.vpype_bin = vpype_bin or os.environ.get("VPYPE_BIN") or DEFAULT_VPYPE
        self.defaults = dict(DEFAULTS, **(defaults or {}))
        self.on_state = on_state or (lambda s: None)
        self.on_output = on_output or (lambda o: None)
        self._active = None
        self._stop_requested = False

    def available(self):
        return os.path.exists(self.bin) and os.path.exists(self.ext_dir)

    def vpype_available(self):
        return os.path.exists(self.vpype_bin)

    def optimize(self, in_path, out_path, opts=None):
        """vpype linemerge/linesort/reloop/multipass, like plotter.js."""
        opts = opts or {}
        if not self.vpype_available():
            raise RuntimeError("vpype not found at %s" % self.vpype_bin)
        tol = opts.get("toleranceMm", 0.3)
        args = [self.vpype_bin, "read", in_path,
                "linemerge", "--tolerance", "%smm" % tol]
        if opts.get("linesort") is not False:
            args.append("linesort")
        if opts.get("reloop"):
            args.append("reloop")
        if opts.get("multipass", 0) > 1:
            args += ["multipass", "--count", str(opts["multipass"])]
        args += ["write", out_path]
        proc = subprocess.run(args, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError("vpype failed (exit %d): %s"
                               % (proc.returncode, proc.stderr))
        return {"in": in_path, "out": out_path}

    def _run(self, args, kind="run", timeout=None):
        if not self.available():
            raise RuntimeError("axidraw_control not found at %s (set AXIDRAW_BIN)"
                               % self.bin)
        proc = subprocess.Popen([self.bin] + args, cwd=self.ext_dir,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        self._active = {"proc": proc, "kind": kind}
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            self._active = None
            raise RuntimeError("%s timed out" % kind)
        self._active = None
        if stdout:
            self.on_output({"kind": kind, "stream": "stdout", "text": stdout})
        if stderr:
            self.on_output({"kind": kind, "stream": "stderr", "text": stderr})
        return proc.returncode, stdout, stderr

    def preview(self, svg_path, opts=None):
        opts = opts or {}
        args = (["--mode=plot", "--preview=true", "--report_time=true",
                 "--rendering=3"]
                + option_flags(opts, self.defaults) + [svg_path])
        code, stdout, stderr = self._run(args, kind="preview",
                                         timeout=opts.get("previewTimeoutSec", 120))
        if connect_failed(stderr + stdout):
            raise RuntimeError("AxiDraw not connected -- check USB/power and port.")
        if code != 0:
            raise RuntimeError("preview failed (exit %d): %s" % (code, stderr or stdout))
        out = parse_preview(stderr + "\n" + stdout)
        out["raw"] = stderr
        return out

    def plot(self, svg_path, opts=None):
        if self._active:
            raise RuntimeError("plotter is busy")
        self._stop_requested = False
        args = ["--mode=plot"] + option_flags(opts, self.defaults) + [svg_path]
        code, stdout, stderr = self._run(args, kind="plot")
        if self._stop_requested:
            return {"stopped": True}
        if connect_failed(stderr + stdout):
            raise RuntimeError("AxiDraw not connected -- check USB/power and port.")
        if code != 0:
            raise RuntimeError("plot failed (exit %d): %s" % (code, stderr or stdout))
        return {"stopped": False, "raw": stdout}

    def manual(self, cmd, opts=None, dist=None):
        if self._active and self._active["kind"] == "plot":
            raise RuntimeError("plotter is busy")
        p = dict(self.defaults, **(opts or {}))
        args = ["--mode=manual", "--manual_cmd=%s" % cmd,
                "--model=%s" % p["model"], "--penlift=%s" % p["penlift"],
                "--pen_pos_up=%s" % p["penPosUp"],
                "--pen_pos_down=%s" % p["penPosDown"],
                "--pen_rate_lower=%s" % p["penRateLower"],
                "--pen_rate_raise=%s" % p["penRateRaise"]]
        if p.get("port"):
            args.append("--port=%s" % p["port"])
        if dist is not None:
            args.append("--dist=%s" % dist)
        args.append(self.blank_svg)
        code, stdout, stderr = self._run(args, kind="manual", timeout=60)
        if connect_failed(stderr + stdout):
            raise RuntimeError("AxiDraw not connected -- check USB/power and port.")
        if code != 0:
            raise RuntimeError("manual %s failed (exit %d): %s"
                               % (cmd, code, stderr or stdout))
        return (stderr + stdout).strip()

    def pen_up(self, opts=None):
        return self.manual("raise_pen", opts)

    def pen_down(self, opts=None):
        return self.manual("lower_pen", opts)

    def home(self, opts=None):
        return self.manual("walk_home", opts)

    def enable_motors(self, opts=None):
        return self.manual("enable_xy", opts)

    def disable_motors(self, opts=None):
        return self.manual("disable_xy", opts)

    def fw_version(self, opts=None):
        return self.manual("fw_version", opts)

    def stop(self):
        """Emergency stop: kill the active plot, raise the pen ASAP, home."""
        self._stop_requested = True
        active = self._active
        self._active = None
        if active and active["kind"] == "plot":
            try:
                active["proc"].kill()
            except OSError:
                pass
        self.on_state({"phase": "stopping"})
        for _ in range(10):
            try:
                self.pen_up()
                break
            except Exception:
                time.sleep(0.15)
        self.on_state({"phase": "stopped"})
        try:
            self.home()
        except Exception:
            pass

    def plot_layers(self, layers, opts=None, wait_for_pen_change=None):
        """``plotLayers`` -- plot color layers in order, pausing for a pen
        swap between each. ``wait_for_pen_change(state)`` blocks until the
        user confirms (return False to stop); defaults to input()."""
        opts = opts or {}
        if wait_for_pen_change is None:
            def wait_for_pen_change(state):
                input("Pen change: install %s (pen %s) and press Enter... "
                      % (state.get("nextLabel"), state.get("nextPen")))
                return True
        total = len(layers)
        self._stop_requested = False
        paths_total = sum(L.get("paths") or 0 for L in layers)
        paths_done = 0
        calib = None
        for i, L in enumerate(layers):
            if self._stop_requested:
                break
            predicted = predict_layer_sec(L, opts) * (calib or 1)
            self.on_state({"phase": "plotting", "layer": i, "total": total,
                           "label": L.get("label"), "pen": L.get("pen"),
                           "color": L.get("color"), "pathsDone": paths_done,
                           "pathsTotal": paths_total,
                           "layerPaths": L.get("paths") or 0,
                           "layerSec": predicted,
                           "calibrated": calib is not None})
            t0 = time.time()
            res = self.plot(L["svgPath"], opts)
            if res.get("stopped") or self._stop_requested:
                self.on_state({"phase": "stopped", "layer": i, "total": total,
                               "pathsDone": paths_done, "pathsTotal": paths_total})
                return {"stopped": True}
            paths_done += L.get("paths") or 0
            raw_predicted = predict_layer_sec(L, opts)
            if raw_predicted > 1:
                observed = time.time() - t0
                ratio = observed / raw_predicted
                calib = ratio if calib is None else (calib + ratio) / 2
            self.on_state({"phase": "layer_done", "layer": i, "total": total,
                           "pathsDone": paths_done, "pathsTotal": paths_total})
            if i < total - 1:
                nxt = layers[i + 1]
                state = {"phase": "awaiting_pen_change", "layer": i,
                         "total": total, "nextLayer": i + 1,
                         "nextLabel": nxt.get("label"), "nextPen": nxt.get("pen"),
                         "nextColor": nxt.get("color"),
                         "pathsDone": paths_done, "pathsTotal": paths_total}
                self.on_state(state)
                if not wait_for_pen_change(state) or self._stop_requested:
                    self.on_state({"phase": "stopped", "layer": i + 1,
                                   "total": total, "pathsDone": paths_done,
                                   "pathsTotal": paths_total})
                    return {"stopped": True}
        self.on_state({"phase": "done", "total": total,
                       "pathsDone": paths_done, "pathsTotal": paths_total})
        return {"stopped": False}
