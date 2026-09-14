"""axiplot -- the pen-plotter layer, on its own.

Everything a program needs between "here is an SVG" and "the AxiDraw drew it",
with no dependency on whatever generated the drawing:

    calibration  the pen-registration sheet (bullseye / fan / stack), laid out
                 in millimetres, one pen at a time, N columns per run
    colorsplit   one layer per stroke colour, or per pen group
    optimize     dedup / reorder / elide / merge, plus an SVG bridge
    svgutil      viewBox, physical size in mm, fit-to-bed
    plotter      the machine: option flags, bed table, preview parsing, and
                 the axidraw_control subprocess driver
    driver       the same machine IN-PROCESS, via the AxiDraw Python sources,
                 which is what makes live progress possible
    run          the layer loop: prepare, plot each layer, report progress and
                 completion through callbacks
    notify       where those completions go (Home Assistant, webhook, or your
                 own callable)
    awake        a logind inhibitor, so an idle timer cannot suspend the
                 machine out from under a plot

The string and geometry transforms are ports of the BUSY Plotter app's
JavaScript and are gated byte-for-byte against a fixture captured from it;
that is why ``_jsnum`` exists. The machine side is not a port of anything.
"""
