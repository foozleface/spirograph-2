"""The sheet, in millimetres: paper, placed items, pens, and the SVG.

    paper  paper and AxiDraw bed sizes, all in mm
    item   PlacedItem — a drawing's box on the paper, and the one function
           that turns a placement into geometry
    scene  Scene — the document: paper + pens + items -> one SVG, or an
           axiplot job — and the sheet file that saves the whole arrangement

One millimetre is one unit here and one user unit in the SVG. No percentages,
no pixels, no second opinion about how big a pattern is.
"""

from spiro.scene.item import PlacedItem
from spiro.scene.paper import AXIDRAW_MODELS, PAPER_PRESETS, Paper
from spiro.scene.scene import (DEFAULT_PEN_COLORS, SHEET_SUFFIX, Pen, Scene,
                               default_pens, item_inis)

__all__ = ["Paper", "AXIDRAW_MODELS", "PAPER_PRESETS", "PlacedItem", "Scene",
           "Pen", "default_pens", "DEFAULT_PEN_COLORS", "SHEET_SUFFIX",
           "item_inis"]
