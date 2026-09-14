# Spirograph-2 → desktop app: work plan

The instructions this plan implements, verbatim:

> integrate the axidraw control from busy python here - it should be standalone.
> Also include the homeassistant notification engine. Each plot added to the canvas
> should be plottable using a different pen. Also, each plot right now starts off
> centered no matter where it is on the canvas initially, but moving it around seems
> to do random things. In any case, it's clearly not 1:1 and correct with the print
> area. Also, move this from a web server to a direct display (like busy-python).
> Clean it up and make it more modular. First, take these instructions, put them in
> a md file, and iterate over them until they are complete, as these are large tasks.
> Commit and push when each major task succeeds.

## Where things stand today

`server.py` is 4035 lines: a module registry (33–470), ~30 FastAPI routes, the
pipeline bridge, and a ~2700-line React single-file frontend served as a string.
The generator modules (`main.py` + `arc.py`, `harmonograph.py`, …) are fine and
stay as they are. The plotter code is ~250 lines of inline `pyaxidraw` calls with
no layer model, no progress, and no notifications.

### The placement bug, diagnosed

Two independent and disagreeing transforms:

* **Canvas (`drawCanvas`, server.py:2456)** scales a placed pattern by
  `drawH / pp.config.height` — fit to *paper height*, ignoring width — and puts
  its top-left at `pp.x%`/`pp.y%` of the paper.
* **Plot (`api_plot`, server.py:881)** scales by
  `min(draw_w/actual_w, draw_h/actual_h)` — fit to *both* — then treats
  `plotter_x/y` as the top-left of the *scaled* box and derives a centre from it.

So the drawn size and the plotted size differ whenever the pattern's aspect ratio
is not the paper's, and the position drifts by half the difference. On top of that
`addToPlotter` (server.py:1803) always computes `cy = 50 - 100/2 = 0` and a width
from the aspect ratio, so every pattern lands full-paper-height at the top edge —
"centred no matter where it was". Dragging (server.py:2333) then moves it in
percent-of-paper units against a canvas scaled by height only, which is the
"random things".

**Fix:** one placement model, in millimetres, used by both the canvas and the
plot path. No percentages, no aspect-ratio guessing, no second scale rule.

## Target architecture

```
spiro/                    the application package (new)
  pipeline/
    registry.py           MODULE_DEFS, lifted out of server.py unchanged
    ini.py                pipeline spec  <->  INI text
    engine.py             INI text -> list[path arrays] + bounds, no I/O
  scene/
    paper.py              AxiDraw bed table, paper sizes, all in mm
    item.py               PlacedItem: paths + placement (mm) + pen index
    scene.py              Scene: items, pens, mm<->px, SVG per pen layer
  ui/
    app.py                QApplication entry point
    main_window.py        top bar, tabs, status
    canvas_view.py        QGraphicsView paper canvas at true mm scale
    palette_panel.py      module palette + pipeline tree
    params_panel.py       parameter editors, drift controls
    pens_panel.py         pen list, per-item pen assignment
    plot_panel.py         AxiDraw settings, plot/preview/stop, progress
    notify_panel.py       Home Assistant / MQTT / webhook settings
axiplot/                  vendored from busy-python, standalone, unmodified
```

`server.py` stays until the desktop app reaches parity, then goes.

## Tasks

Each task ends with a commit and a push.

- [x] **T0 — this plan.** Write `PLAN.md`, keep it updated as tasks land.

- [x] **T1 — vendor `axiplot`.** Copy the package from `~/busy-python/axiplot`
  verbatim (it already has zero dependencies outside itself). Bring its tests
  (`tests/test_axiplot.py`) too so the vendored copy stays honest. Confirm
  `driver.available()` is True against the `axidrawinternal` already in `.venv`.
  *Done when:* `pytest tests/test_axiplot.py` passes in this repo.

- [x] **T2 — extract the generation core.** Move `MODULE_DEFS` to
  `spiro/pipeline/registry.py`, the INI builder (`_build_ini`, `_emit_mod`) to
  `spiro/pipeline/ini.py`, and `_run_pipeline_points` to `spiro/pipeline/engine.py`,
  returning paths in *source units* plus their bounds — no normalising to a
  target box, that is the scene's job now. `server.py` imports these instead of
  defining them, so the web UI keeps working through the refactor.
  *Done when:* the web UI still generates, and `spiro.pipeline` has no FastAPI
  or Qt import.

- [x] **T3 — the scene model, in millimetres.** `spiro/scene/`: paper table,
  `PlacedItem` (paths, `x_mm`, `y_mm` of the item's *centre*, `w_mm`, `h_mm`,
  rotation, pen index), and a `Scene` that renders to SVG at 1 user unit = 1 mm.
  One `item_transform()` function is the only place a placement becomes a
  transform; the canvas and the plotter both call it.
  *Done when:* unit tests assert a round trip — place an item at a known mm
  position, render the SVG, and read the path bounds back within a tolerance.

- [x] **T4 — the desktop app.** PySide6, launched by `run_gui.sh`, same shape as
  busy-python's GUI: palette + pipeline on the left, paper canvas in the middle
  showing the real bed with a mm ruler, plot side on the right. Drag moves an
  item by real millimetres; what you see is what gets drawn.
  *Done when:* generate a pattern, drop it on the paper, drag it, and the plot
  preview bounds match the on-screen position to under a millimetre.

- [x] **T5 — pens.** A pen list (label, colour, include). Every placed item
  carries a pen index; the scene emits one SVG layer per pen; `axiplot.run.plot_job`
  plots the layers in order and `LayerState` remembers which are on the paper.
  *Done when:* two items on two pens plot as two layers with a pause between them.

- [x] **T6 — notifications.** Wire `axiplot.notify` in: settings for Home
  Assistant (URL, token or token file, service, level), MQTT and webhook, a Test
  button, and `plot_job(notifier=…)` so each finished layer buzzes a phone.
  *Done when:* the Test button reports success against the configured service,
  and a two-layer plot sends "layer 1/2 done, swap to …".

- [x] **T7 — retire the web server.** Once the desktop app has parity, delete
  `server.py`, rewrite `launch.sh` to launch the GUI, and update the README.

## Notes

* PySide6 is not in `.venv` yet — `run_gui.sh` installs it, as busy-python's does.
* `QT_QPA_PLATFORM=xcb;wayland` is the proven backend on this machine.
* Never open the serial port from two processes; `axiplot`'s preview path never
  connects, so use it for anything speculative.

## Done

All seven tasks are in. What changed, in one line each:

* `axiplot/` — the pen plotter, vendored standalone from busy-python.
* `spiro/pipeline/` — the mathematics, with no server or Qt anywhere near it.
* `spiro/scene/` — the sheet in millimetres, and the single transform that
  places a pattern on it. This is the placement fix.
* `spiro/ui/` — the window: build, effects, paper, sheet, plot, alerts.
* Pens: one layer each, a real pause between them, resume where it stopped.
* Alerts: Home Assistant, MQTT, webhook — per layer and at the end.
* `server.py` is gone; `launch.sh` opens the window.

`./run_tests.sh` — 324 checks across eight gates, no hardware and no network.

### Not carried over from the web UI

* **Draw animation.** The old canvas could animate the pen tracing the curve.
  Worth having back as a canvas overlay; nothing depends on it.
* **Randomize.** The old UI could invent a pipeline. It was a large table of
  hand-tuned recipes living inside the React app; it belongs in
  `spiro/pipeline/` as data if it comes back, not in a panel.
* **Per-pattern tabs.** Replaced by placing several patterns on one sheet,
  which is what they were being used for.

---

# Round two

Asked for after the first seven landed:

> ok - I want a "clear" button for the current plot. I also want distinct
> screens for the paper so we can have a larger screen view of the current
> plot. I also like the file browser, but it would be nice to have a quicker
> way to choose from the existing plots.

- [x] **R1 — clear the paper.** A button that takes everything off the sheet,
  asking first when there is something to lose, plus the menu item and the
  shortcut. Distinct from File > New, which clears the *pattern* being built.

- [x] **R2 — room for the paper.** Two ways, because "a larger screen view"
  can mean either:
  * *Paper only* — hide both side panels, so the sheet has the whole window.
  * *Paper in its own window* — detach the canvas into a top-level window that
    can be dragged to a second monitor and made fullscreen. The same widget
    is reparented, never a copy, so there is still one canvas and one truth.

- [x] **R3 — pick a pattern quickly.** A Files tab beside Build and Effects:
  every `.ini` in the project, what its pipeline is, filtered as you type,
  one click to load. Plus a recent-files list in the File menu.

- [x] **R4 — the randomizer.** The web UI could invent a pipeline: a table of
  hand-tuned recipes with sane ranges per module, so what came out was worth
  looking at rather than noise. It went out with `server.py`. Bring it back as
  data in `spiro/pipeline/`, not as a panel — then the button is three lines
  and the recipes are testable.

### Round two, done

* **Clear** on the Sheet panel and in the Pattern menu (`Ctrl+Shift+Backspace`).
  It asks first and touches nothing but the sheet.
* **`F11`** for paper-only, **`Ctrl+Shift+P`** for the paper in its own window.
  One canvas, reparented — `takeCentralWidget`, not `setCentralWidget(None)`,
  which deletes it.
* **Files** tab: every `.ini` in the project with its pipeline beside it,
  filtered as you type.
* **Surprise me** (`Ctrl+R`): 61 recipes in `spiro/pipeline/recipes.py`, each
  one run by the gate.

`./run_tests.sh` — 324 checks across eight gates.

---

# Round three

> I want a tab for rendering and a separate tab (and paper) for placement. I
> want to be able to place designs (multiple) on the paper with their
> configurations and save the whole thing — so I can recreate the set of
> designs and their rotation, placement, and size.

- [x] **P1 — two tabs in the middle.** *Render* is the pattern being built,
  alone, at whatever size the widget allows and redrawn on every edit — before
  this the only way to see a pattern was to place it. *Paper* is the sheet, as
  before. Placing switches to Paper; opening, randomising or editing switches
  to Render. Paper-only and the detached paper window still work on the Paper
  tab's canvas — the same widget, reparented.

- [x] **P2 — the sheet as a file.** `Scene.save` / `Scene.read` /
  `Scene.apply_dict` in `spiro/scene/scene.py`: a `.sheet.json` holding the
  paper, the pens, and each item's INI, centre, height (the width is derived),
  angle, pen and visibility — plus how the paper was chosen, so the combos come
  back too. Opening one regenerates every INI in the background at the preview
  quality; the plot path upgrades them to Ultra as it always has. Listed in the
  Files tab beside the patterns.

- [x] **P3 — rotation, and placement in numbers.** `PlacedItem.rotate_to` /
  `rotate_by`, kept in [0, 360). The Sheet panel edits the selected item's
  centre, width and angle; `[` / `]` turn on the canvas; the resize handle
  measures along the item's own axis so a turned item resizes along its turned
  edge.

- [x] **P4 — edit a placed pattern.** An item opened from a sheet has no
  document behind it. Selecting it — in the list or on the canvas — loads
  its INI into Build and links the two, so the arrangement is a starting
  point rather than a snapshot. Opening a file from Files lands in Build.
  Draft sampling went from 3,000 to 8,000 points: the first thing on screen
  has to be recognisable.

### Round three, done

* Render / Paper tabs, `Ctrl+1` / `Ctrl+2`.
* `File > Save sheet` (`Ctrl+Shift+S`), `Open sheet…` (`Ctrl+Shift+O`), and the
  same two buttons on the Sheet panel; `run_gui.sh some.sheet.json` too.
* Centre, width and angle editors under the item list; selection edits.
* `run_gui.sh` no longer forces xcb on macOS, which only has cocoa.

`./run_tests.sh` — the scene gate checks the file round trip against the SVG
the plotter would get; the window gate saves, clears, reopens and edits.

---

# Round four: the engine, and what the window says about it

> Look at all these calculation engines — does grouping them make sense? Are
> they well constructed? Would there be another better way to compose them?
> Is the underlying data structure sensible? It seems like the ideas of
> simultaneous/grouping don't really work or do anything. If these are good
> ideas, make them more functional in the GUI. Make test suites to ensure we
> don't get unintentional code drift as you rewrite. Are there operations we
> left out? Could we have a better GUI — maybe it's not clear what each thing
> is, and we should make that clearer with visual aids.

## What the engine actually is

Every module is `z' = f(z, t)`. A *generator* returns `z + p(t)`: it adds a
vector. A *transform* returns `T_t(z)`: it moves what it was given. The
pipeline folds the list from `z = 0`. So a chain of generators is a **vector
sum** — arms laid end to end, each turning at its own rate — and a transform
acts on the sum of every arm before it.

Measured, not assumed (`tests/test_golden.py` keeps these true):

* `group(gear | circle)` and the chain `gear, circle` differ by **0**.
* `group(gear, rotation | circle)` and `gear, rotation, circle` differ by **0**.
* Only `group(gear, rotation | circle, scale)` differs from its chain — a
  transform inside a *later* branch acts on that branch alone.

So a group is parentheses: the one thing it does is stop a transform from
reaching the arms before its branch. Everything else "simultaneous" was
already true of the plain chain, because every module sees the same `t`.
That is why grouping felt like it did nothing — most of the time it did not.

The period machinery is the other decoration. `natural_period` and the LCM
give a `period`, every module divides `t` by it, and every module then
multiplies by its own `cycles`. With `normalize = true` (the default
everywhere) the period cancels out of every result. What does the work is
`cycles` and `scroll_repeats`.

What is wrong, in order of damage:

1. **The GUI cannot see most of the knobs.** 60 real parameters are missing
   from the registry (scale's origin, arc's centre, bend's direction, the
   harmonograph's fourth pendulum, noise's mode, the line's endpoints…).
   Easing (`easing =`) and oscillating drift (`osc_<param> =`) exist in the
   base class and appear nowhere.
2. **Nothing validates a parameter.** The recipes send `arc_radius`,
   `rose.petals`, `lissajous.amp_x`, `rack.teeth`, harmonograph phases in
   radians — the modules read the defaults instead and say nothing. A third
   of Surprise-me is not drawing what its recipe says.
3. **The runner is a Python loop.** `dense_sample` calls every module once
   per sample point: 0.6 s for a Draft harmonograph, seconds for Ultra, and a
   slider that lags. Every formula here vectorises.
4. **Groups are a second data shape** (`kind: group, branches: [[…]]`) for
   what is one bit of information on a transform: *everything so far* or
   *the last arm only*.

## Tasks

- [x] **E1 — the golden gate.** Before anything moves: every module at its
  defaults, every module with every drift, every `.ini` in the repository,
  thirty seeded recipes, the three group cases, symmetry, pen lift and moiré —
  rendered and fingerprinted (bounds, path length, sixty-four points) into
  `tests/golden/`. The gate fails on a millionth of a unit. Re-recording is a
  deliberate commit that says why.

- [x] **E2 — vectorise.** `transform` takes arrays of `t` (and `z`); the
  runner evaluates the whole draw in one call per module. The engine also
  keeps the points after every step (`Drawing.stages`), which is what the
  window's visual aids are built on. Golden gate: unchanged output.

- [x] **E3 — every knob, validated.** The registry lists what the modules
  read, with the pointless ones marked hidden; `build_ini` refuses a
  parameter no module reads; easing and oscillating drift become registry
  entries. The recipes are corrected and their goldens re-recorded on purpose.

- [x] **E4 — scope instead of groups.** A transform carries `scope = all`
  (default) or `scope = last` — the arm since the previous generator. The
  runner honours it; a `group` in an old file is flattened to the same thing
  on load, so nothing old breaks and the GUI has one list instead of a tree.

- [x] **E5 — the operations that were missing.** *Tempo*, a module that
  re-clocks everything after it (reverse, ping-pong, stutter, ease, speed).
  *Pintograph*, the two-disc linkage Gandy's machines are — two cranks, two
  arms, the pen where the arms meet. *Tile* (rows × columns) and *clip to a
  circle or rectangle* as finishing passes, because the paper is a sheet.

- [ ] **G1 — a window that shows what each thing does.** The pipeline as
  stages with a thumbnail of the drawing *up to that stage*; a scrubber in
  Render that draws the linkage at any moment of the draw — each arm as a
  segment, the pen at the end, the path so far; a palette that is a gallery
  of what every module draws; Effects folded into Build as *Finishing*; a
  scope toggle on every transform; sliders beside the numbers.
