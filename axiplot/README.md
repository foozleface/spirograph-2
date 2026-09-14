# axiplot

The pen-plotter layer, on its own: everything between *here is an SVG* and
*the AxiDraw drew it*, with no dependency on whatever generated the drawing.

```python
from axiplot import colorsplit, plotter, run, notify
from axiplot.driver import InProcessDriver

job = {"svg": svg, "mode": "color", "pens": pens,
       "paperSize": {"width_mm": 500, "height_mm": 217}}

driver = InProcessDriver(on_progress=lambda **p: print("%.0f%%" % (100 * p["fraction"])))
summary = run.plot_job(job, driver,
                       notifier=notify.Async(notify.HomeAssistantNotifier(url, token, service)))
```

## What is in it

| Module | What it does |
|---|---|
| `plotter` | Bed table, option flags, preview parsing, layer preparation, and the `axidraw_control` subprocess driver |
| `driver` | The **same machine in-process**, via the AxiDraw Python sources — live progress, a resumable pause, previews in milliseconds |
| `run` | The layer loop: `LayerState` (which layers of which drawing are already on the paper) and `plot_job` |
| `notify` | Where "layer 3 of 7 is done, swap to magenta" goes — Home Assistant, webhook, any callable, fan-out, async |
| `calibration` | The pen-registration sheet: a bullseye, a fan and a stack, one pen at a time, N columns per run |
| `colorsplit` | One layer per stroke colour, or per pen group |
| `optimize` | dedup / reorder / elide / merge, plus an SVG bridge |
| `svgutil` | viewBox, physical size in mm, fit-to-bed |

## The two things worth knowing

**The in-process driver is where the progress comes from.** The AxiDraw
software ships as plain Python beside its frozen binary (Inkscape's
`axidraw_deps/axidrawinternal`). Importing it means the CLI's progress bar —
a dry run to total the travel, then a millimetre counter — becomes callbacks,
and a pause becomes an event the plotter can be resumed from rather than a
killed process. It is optional: `driver.available()` is False when the sources
are not installed, and `plotter.Plotter` plots exactly the same without live
progress. Point `AXIDRAW_PY_DEPS` at the sources if they are somewhere unusual.

**Layer state is what stops a sheet being drawn on twice.** `LayerState` is
keyed by a stamp of the drawing — token, physical size, pen set — so a new
drawing clears the marks and the same drawing keeps them. A stopped run
resumes at the first layer still pending.

## Safety

Anything that opens the serial port can wreck a plot running in another
process; Linux does not lock it. Preview (`driver.preview`, `plotter.preview`)
is safe — it motion-plans and never connects. `Plotter.stop()` is **not**: it
raises the pen and homes the head with manual commands even when the calling
process has no plot of its own. Tests must stub it.

## Tests

`tests/test_axiplot.py` — 44 checks, no hardware and no network: the driver in
preview mode, the progress feed driven through the same calls a real plot
makes, layer state, the run loop with a recorder in place of the machine, and
every notifier pointed at a recorder.

The string and geometry transforms (`colorsplit`, `optimize`, `svgutil`,
`calibration`) are ports of the BUSY Plotter app's JavaScript and are gated
byte-for-byte against a fixture captured from it — which is why `_jsnum.py`
exists. The machine side is not a port of anything.
