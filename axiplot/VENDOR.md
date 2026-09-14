# Vendored from busy-python

`axiplot/` is a verbatim copy of `~/busy-python/axiplot`, the pen-plotter layer
that sits between "here is an SVG" and "the AxiDraw drew it". It depends on
nothing outside itself, which is the point: it is the plotter, not the app.

Upstream: `busy-python`, commit at the time of copying — see `git log` there.
Tests came with it: `tests/test_axiplot.py`, 75 checks, no hardware, no network.

## Local changes

* `driver._load()` now tries a plain `import axidrawinternal` **before** the
  Inkscape extensions directory. This repo installs the AxiDraw API into its own
  `.venv`, so the sources are already importable and are the same release
  `pyaxidraw` would use; prepending Inkscape's copy shadowed it with a different
  version of the same package inside one interpreter (3.9.5 over 3.9.6).
  The Inkscape path stays as the fallback, which is what a bare system Python
  still finds.

Keep this list short. A fix that is not specific to this repo belongs upstream.
