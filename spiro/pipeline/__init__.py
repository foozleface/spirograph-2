"""Pattern generation: what the modules are, how a pipeline is spelled, and
how to run one.

    registry  the module table — types, parameters, defaults, descriptions
    ini       a pipeline spec <-> INI text
    engine    INI text -> a Drawing: curves in their own units, plus bounds

Nothing in here imports Qt, FastAPI or the plotter. It is the part of the
program that knows about mathematics and nothing else.
"""

from spiro.pipeline.engine import Drawing, normalize, run
from spiro.pipeline.ini import PLOT_SAMPLING, build_ini
from spiro.pipeline.registry import MODULE_DEFS, defaults_for, module_names

__all__ = ["Drawing", "run", "normalize", "build_ini", "PLOT_SAMPLING",
           "MODULE_DEFS", "defaults_for", "module_names"]
