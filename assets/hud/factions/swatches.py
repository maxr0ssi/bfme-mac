"""Each faction palantir's materials, cut from its citadel (docs/HUD.md, "Cut from the citadel").

Stdlib: sagekit/hud/swatch.py crops these out of the built sheets into
build/assets/_hud/factions/swatch/<faction>/<name>.png, and the painter (sagekit/paint/palantir)
lays them along the rings as the frame's surfaces: the same stone, metal, friezes and roofs the
citadel is painted with, so the palantir reads as a piece of the fortress.

SOURCES  per faction: {key: path under build/assets} of the sheets the citadel is built from (the
         faction atlas as our painter recoloured it; the Men's citadel has its own sheet).
SWATCHES per faction: {name: (source key, (x0, y0, x1, y1) in that file's pixels, rot)}; rot 90
         turns a vertical strip so it runs along the ring.
CITADEL  per faction: the citadel's close render and the crop of it shown on the review sheet.
"""

_TEX = "%s/_sheets/out/art/compiledtextures/%s/%s.dds"

SOURCES = {
    "dwarves": {"atlas": _TEX % ("dwarves", "db", "dbfortress1")},
    "elves": {"atlas": _TEX % ("elves", "eb", "ebfortress")},
    "men": {"citadel": "men/fortress/out/art/compiledtextures/gb/gbfortressh.dds"},
    "goblins": {"atlas": _TEX % ("goblins", "wb", "wbfortress")},
    "isengard": {"atlas": _TEX % ("isengard", "ib", "ibfortress")},
    "mordor": {"atlas": _TEX % ("mordor", "mb", "mbfortress")},
    "angmar": {"atlas": _TEX % ("angmar", "kb", "kbfortress")},
}

SWATCHES = {
    "dwarves": {                                       # DBFortress1 at 2048 (atlas.py's rects x4)
        "rune": ("atlas", (120, 1444, 1048, 1548), 0),       # the rune frieze: gold runes on blue
        "tri": ("atlas", (1104, 1440, 1584, 1548), 0),       # the triangle frieze, 3 periods
        "granite": ("atlas", (288, 1600, 1616, 2032), 0),    # honey granite under the frieze
        "hex": ("atlas", (772, 224, 1596, 312), 0),          # the gold-edged hexagon chain
        "top": ("atlas", (232, 12, 752, 176), 0),            # the walk-top stone (lighter)
    },
    "elves": {                                         # EBFortress at 2048 (atlas.py's rects x2)
        "ashlar": ("atlas", (216, 1480, 472, 1648), 0),      # dressed ivory ashlar
        "coping": ("atlas", (0, 1346, 400, 1404), 0),        # the white torus moulding
        "scallop": ("atlas", (800, 1476, 1052, 1520), 0),    # the little arcade frieze, 6 arches
        "roof": ("atlas", (1656, 892, 1868, 1104), 0),       # slate scale roof
        "window": ("atlas", (836, 1628, 1016, 1976), 0),     # the lancet window, teal glass
        "knot": ("atlas", (1940, 1500, 2048, 1564), 0),      # knotwork band
    },
    "men": {                                           # GBFortressH (the citadel's own 4096 sheet)
        "ashlar": ("citadel", (760, 2160, 915, 2370), 0),    # white Minas Tirith ashlar
        "corbel": ("citadel", (760, 2068, 940, 2118), 0),    # the corbel table under the battlements
        "stars": ("citadel", (2690, 1128, 2930, 1162), 0),   # the sable band of stars
    },
    "goblins": {                                       # WBFortress at 1024 (atlas.py's rects x2)
        "beam": ("atlas", (0, 700, 470, 762), 0),            # the blood-red horn beam
        "hide": ("atlas", (560, 300, 1000, 520), 0),         # the dragon's scaled red plates
        "blocks": ("atlas", (484, 800, 650, 1000), 0),       # black iron scales
        "bone": ("atlas", (872, 112, 894, 248), 90),         # the long pale tusk
    },
    "isengard": {                                      # IBFortress at 1024
        "lancets": ("atlas", (205, 640, 395, 760), 0),       # the lancet arcade under spikes
        "ribs": ("atlas", (240, 500, 480, 600), 0),          # fluted black wall plates
        "coping": ("atlas", (210, 600, 490, 640), 0),        # the bright silver coping beam
        "hand": ("atlas", (80, 205, 140, 260), 0),           # the White Hand
        "teeth": ("atlas", (620, 745, 745, 830), 0),         # silver teeth
    },
    "mordor": {                                        # MBFortress at 1024
        "fluted": ("atlas", (445, 730, 620, 1020), 0),       # black fluted iron
        "plates": ("atlas", (445, 640, 625, 730), 0),        # riveted plates
        "windows": ("atlas", (840, 255, 945, 380), 0),       # a crown's fire-rimmed windows
        "lava": ("atlas", (0, 85, 240, 205), 0),             # the lava band
    },
    "angmar": {                                        # KBFortress at 1024
        "blocks": ("atlas", (300, 500, 780, 600), 0),        # blue-black stone blocks
        "planks": ("atlas", (520, 150, 815, 340), 0),        # the warm timber walk
        "scales": ("atlas", (830, 10, 925, 245), 0),        # blue steel scale roof
        "horn": ("atlas", (150, 0, 345, 450), 0),            # the frost-lined dark horn
    },
}

CITADEL = {   # (close render under build/assets/<faction>/fortress/renders, the building in it: WxH+X+Y)
    "dwarves": ("_new_close.png", "1516x1040+0+40"),
    "elves": ("_new_close.png", "1545x1060+0+40"),
    "men": ("_new_close.png", "1290x888+272+168"),
    "goblins": ("_new_close.png", "1550x1060+27+40"),
    "isengard": ("_new_close.png", "1555x1060+36+40"),
    "mordor": ("_new_close.png", "1398x963+194+137"),
    "angmar": ("_new_close.png", "1458x1004+147+96"),
}
