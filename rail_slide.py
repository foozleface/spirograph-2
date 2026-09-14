#!/usr/bin/env python3
"""Rail slide: back-and-forth translation along a straight rail, as a module
type of its own.

The class lives in spirograph_rail.py beside the generator that rolls a
gear along the same rail; the loader finds a module by the type name, so
this file gives it one.
"""

from spirograph_rail import SpirographRailTransformModule as RailSlideModule  # noqa: F401
