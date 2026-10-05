"""The Archers' two sheets (both archer folders paint their own copy under their own names): the
serious gear in the Elven buildings' Moonsilver palette (assets/elves/style.py: mithril silver,
mallorn gold, pale birch, sea-glass and slate, the cloth the player's colour) plus the Rangers'
fixed green-brown camo, and the fun sheet. Tile tables for the kit's painter (kit/paint.py).

Tinting: the cloth (hoods, cloaks, the leaf shield), the linings and leather (grips, the Mirkwood
leaf-leather), the crystal gems, the Noldor enamel (behind the circlet's vine), the Mirkwood
circlet's autumn leaves and one of the Rangers' five camo colours all follow the Paint picker (B) on
the CaH sheets (docs/CAH.md). Metal stays metal; the camo keeps its other four colours.
"""
import math
from pathlib import Path

from assets.elves.style import GOLD as EGOLD, MITHRIL as EMITHRIL, PALETTE as EP, SLATE, VERDIGRIS
from sagekit.units.paint import ramp_colour

from ..kit import ornament as O
from ..kit.paint import BLUE, GREEN, PAINT, RED, paint_sheet

RAMPS = {
    "emithril": EMITHRIL, "egold": EGOLD, "slate": SLATE, "seaglass": VERDIGRIS,
    "birch": EP.ramps["wood"], "gem": EP.ramps["crystal"],
    # cloth under the hero's colour: a soft silver-grey (the mask carries the shading)
    "cloth": [(0, (.05, .06, .06)), (.35, (.17, .19, .19)), (.65, (.32, .34, .33)), (.9, (.5, .52, .51)), (1, (.7, .72, .71))],
    "leather": [(0, (.04, .05, .03)), (.45, (.18, .24, .13)), (.8, (.40, .46, .27)), (1, (.62, .66, .46))],
    "antler": [(0, (.18, .14, .10)), (.4, (.48, .40, .30)), (.75, (.80, .74, .62)), (1, (.96, .93, .85))],
    "darkwood": [(0, (.05, .03, .02)), (.45, (.22, .14, .08)), (.8, (.45, .32, .18)), (1, (.70, .55, .34))],
    "autumn": [(0, (.18, .03, .01)), (.4, (.62, .16, .04)), (.7, (.90, .48, .10)), (1, (1, .86, .45))],
    "ground": [(0, (.06, .07, .04)), (.5, (.25, .27, .16)), (1, (.55, .53, .36))],            # camo base
    "silk": [(0, (.55, .55, .52)), (.6, (.90, .89, .85)), (1, (1, 1, 1))],
    "pearl": [(0, (.55, .52, .60)), (.5, (.88, .86, .92)), (.85, (.98, .97, 1.0)), (1, (1, 1, 1))],
    "fur": [(0, (.25, .08, .02)), (.45, (.80, .40, .10)), (.8, (.98, .70, .35)), (1, (1, .92, .75))],
    "green": [(0, (.02, .08, .02)), (.45, (.12, .45, .12)), (.8, (.40, .75, .25)), (1, (.80, .95, .55))],
    "lavender": [(0, (.15, .08, .25)), (.5, (.62, .45, .88)), (1, (.95, .90, 1.0))],
    "blue": [(0, (.02, .06, .20)), (.5, (.25, .50, .95)), (1, (.85, .93, 1.0))],
    "twine": [(0, (.12, .08, .04)), (.5, (.55, .42, .25)), (1, (.85, .75, .55))],
}
CAMO = [(.17, .19, .11), (.30, .32, .17), (.36, .28, .17), (.22, .20, .13), (.42, .40, .26)]
CAMO_PAINT = 2                          # the camo blotch that takes the Paint colour (the tile's ramp under it)


def _star(cx=128, cy=128, r0=24, r1=104, n=8):
    """The rayed star of the Dunedain (planar brooch face): long and short rays and a ring."""
    out = ["circle %d,%d %d,%d" % (cx, cy, cx + r0, cy)]
    for k in range(n * 2):
        a = math.pi * k / n
        r = r1 if k % 2 == 0 else r1 * .55
        out.append("line %d,%d %d,%d" % (cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def _leaf_veins(cx=128):
    """A leaf's midrib and paired veins along v (planar on a leaf plate)."""
    out = ["line %d,10 %d,246" % (cx, cx)]
    for y in range(40, 230, 26):
        out += ["line %d,%d %d,%d" % (cx, y, cx - 70, y - 34), "line %d,%d %d,%d" % (cx, y, cx + 70, y - 34)]
    return out


def _vine(y0, y1, n=4):
    """A gold vine with leaves along u (circlet bands, the bow's limbs)."""
    pts = " ".join("%d,%d" % (x, (y0 + y1) / 2 + (y1 - y0) * .3 * math.sin(x / 256 * n * 2 * math.pi)) for x in range(0, 257, 8))
    out = ["polyline " + pts]
    for k in range(n * 2):
        x = 256 * (k + .5) / (n * 2)
        y = (y0 + y1) / 2 + (y1 - y0) * .3 * math.sin(x / 256 * n * 2 * math.pi)
        s = 1 if k % 2 else -1
        out.append("ellipse %d,%d 10,5 %d,%d" % (x + 8, y + s * 12, 0, 360))
    return out


def _mallorn():
    """A mallorn leaf device for the leaf shield's face (planar): a leaf with veins in a ring."""
    out = _leaf_veins()
    out += ["circle 128,128 128,16", "polyline 128,14 196,90 210,150 170,220 128,246 86,220 46,150 60,90 128,14"]
    return out


# tag: (ramp, mid, grain, edges, tint channel, {layer: (strokes, width)})
TILES = {
    0: ("emithril", .62, .25, "v", None, {}), 1: ("egold", .62, .25, "v", None, {}),
    2: ("cloth", .55, .18, "", GREEN, {}),
    3: ("cloth", .5, .15, "", GREEN, {"inlay": (_vine(110, 150, 5) + ["line 0,40 256,40", "line 0,216 256,216"], 4)}),
    4: ("egold", .62, .25, "", None, {"engrave": (_leaf_veins(), 4)}),
    5: ("emithril", .64, .2, "", None, {"inlay": (_vine(70, 186, 4) + ["line 0,24 256,24", "line 0,232 256,232"], 6),
                                        "enamel": (["rectangle 0,60 256,196"], 1)}),
    6: ("gem", .55, .1, "", BLUE, {}),
    7: ("leather", .5, .35, "", RED, {"engrave": (O.border(12), 3)}),
    8: ("antler", .58, .35, "", None, {"engrave": (["line 0,%d 256,%d" % (y, y + 10) for y in range(4, 256, 22)], 2)}),
    9: ("egold", .6, .25, "v", None, {"engrave": (["line %d,0 %d,256" % (x, x) for x in range(16, 256, 32)], 5)}),
    10: ("slate", .55, .15, "", BLUE, {"inlay": (O.sparkles(10, 14) + ["line 0,30 256,30", "line 0,226 256,226"], 5)}),
    11: ("ground", .5, .3, "", PAINT, {}), 12: ("ground", .35, .35, "", PAINT, {"engrave": (O.border(14), 3)}),
    13: ("emithril", .66, .2, "", None, {"engrave": (_star(), 7)}),
    14: ("birch", .6, .25, "", None, {"inlay": (_vine(90, 166, 3), 5)}),
    15: ("leather", .45, .3, "", RED, {"engrave": (["line %d,0 %d,256" % (x, x + 64) for x in range(-64, 256, 20)], 3)}),
    16: ("emithril", .7, .2, "u", None, {"engrave": (_leaf_veins(), 2)}),
    17: ("emithril", .64, .25, "", None, {"engrave": (["line 128,0 128,256"] + ["line 128,%d %d,%d" % (y, x, y + 30)
                                                       for y in range(0, 250, 16) for x in (10, 246)], 2)}),
    18: ("leather", .5, .3, "", RED, {"engrave": (O.scales(6, 5), 3)}),
    19: ("cloth", .5, .15, "", GREEN, {"inlay": (_mallorn(), 6)}),
    20: ("birch", .55, .3, "", None, {"engrave": (["line 0,%d 256,%d" % (y, y) for y in range(0, 256, 40)], 2)}),
    21: ("silk", .7, .1, "", None, {}), 22: ("slate", .45, .25, "v", None, {}),
    23: ("seaglass", .55, .2, "", None, {}), 24: ("darkwood", .5, .35, "", None, {}),
    25: ("autumn", .55, .3, "", PAINT, {"engrave": (_leaf_veins(), 3)}),
    26: ("emithril", .62, .2, "", None, {"engrave": (O.border(10) + ["line 128,0 128,256"], 3)}),
    27: ("cloth", .38, .15, "", RED, {}),
}
INLAY = {3: "egold", 5: "egold", 10: "egold", 14: "egold", 19: "egold"}

FUN_TILES = {
    0: ("egold", .64, .25, "v", None, {}), 1: ("emithril", .64, .25, "v", None, {}),
    2: ("pink", .58, .2, "", None, {}), 3: ("pink", .42, .2, "", None, {}),
    4: ("white", .6, .15, "", None, {}), 5: ("white", .66, .5, "", None, {}),
    6: ("emithril", .72, .2, "v", None, {"inlay": (O.sparkles(6, 60), 1)}),
    7: ("hotpink", .62, .1, "", None, {}), 8: ("fur", .55, .45, "", None, {}), 9: ("pink", .7, .25, "", None, {}),
    10: ("pink", .66, .15, "", None, {}), 11: ("yellow", .62, .12, "", None, {}), 12: ("white", .72, .1, "", None, {}),
    13: ("blue", .6, .12, "", None, {}), 14: ("green", .45, .25, "", None, {}), 15: ("pearl", .6, .15, "", None, {}),
    16: ("orange", .58, .25, "", None, {}), 17: ("green", .5, .35, "", None, {}), 18: ("white", .7, .1, "", None, {}),
    19: ("red", .58, .1, "", None, {}),
    20: ("hotpink", .5, .15, "", None, {"inlay": (O.heart(128, 132, 60) + O.sparkles(20, 40), 4), "engrave": (O.border(6), 2)}),
    21: ("silk", .7, .1, "", None, {}), 22: ("twine", .5, .4, "", None, {}), 23: ("black", .4, .1, "", None, {}),
    24: ("hotpink", .58, .3, "v", None, {"inlay": (O.sparkles(24), 1)}), 25: ("orange", .62, .3, "", None, {}),
    26: ("hotpink", .6, .15, "", None, {}), 27: ("lavender", .62, .15, "", None, {}),
}
FUN_INLAY = {6: "white", 20: "red", 24: "white"}
RAINBOW = [(.85, .08, .08), (.98, .48, .05), (.98, .85, .1), (.15, .65, .2), (.1, .35, .85), (.3, .12, .6), (.62, .18, .7)]


def special(sheet, tag, u, v, x, y, g, n1):
    """Folds, camo, fur, stripes and gloss per tile; returns (value offset, fixed rgb or None)."""
    fold = .15 * math.sin(u * 12 * math.pi) + .03 * math.sin(x * 2.1) * math.sin(y * 2.1)
    if sheet == "gear":
        if tag in (2, 3, 19, 27):                      # cloth folds (the shield face flat)
            return (fold if tag != 19 else 0), None
        if tag in (11, 12):                            # camo: four colours in blotches, leaf-dappled
            k = n1 * 3.2 + .8 * math.sin(x * .09 + 2 * math.sin(y * .07)) + .5 * math.sin(y * .13 - x * .05)
            n = int(abs(k) * 1.7) % len(CAMO)
            f = 1 + g * 1.4 + (fold * .8 if tag == 11 else 0) - (.25 if tag == 12 else 0)
            if n == CAMO_PAINT:                        # a fixed rgb is never tinted: this blotch takes the ramp
                return (fold * .8 if tag == 11 else 0), None
            return 0, [max(0, min(1, q * f)) for q in CAMO[n]]
        if tag == 6:
            return .5 * (v - .5), None
        if tag == 15:
            return (.1 if ((u * 6 + v * 2) % 1.0) < .75 else -.18), None
        if tag == 21:
            return .1 * math.sin(v * 40), None
        return 0, None
    if tag in (2, 3):                                  # pink cloth folds
        return fold, None
    if tag == 4:                                       # rainbow folds: a colour per fold
        c = RAINBOW[min(6, int(u * 7))]
        k = 1 + fold * 1.6 + g
        return 0, [max(0, min(1, q * k)) for q in c]
    if tag == 5:                                       # fluff
        return .3 * math.sin(x * 1.3 + 4 * math.sin(y * .23)) * n1 + .15 * math.sin(y * 1.7 + x * .3), None
    if tag == 8:                                       # tabby stripes and fluff
        return -.3 * (math.sin(v * 9 * math.pi + 2 * math.sin(u * 6)) > .3) + .15 * math.sin(x * 1.1) * n1, None
    if tag == 15:                                      # the pearl horn's spiral groove and rainbow sheen
        s = math.sin((u * 2 + v * 6) * 2 * math.pi)
        c = RAINBOW[int((v * 7 + u * 2) * 3) % 7]
        base = ramp_colour(RAMPS["pearl"], .62 + g)
        k = .8 + .2 * s
        return 0, [max(0, min(1, (b * .8 + cc * .2) * k + .06)) for b, cc in zip(base, c)]
    if tag == 16:                                      # carrot rings
        return -.25 * (math.sin(v * 70) > .75) + .08 * math.sin(u * 30), None
    if tag == 18:                                      # candy stripes: red spirals on white
        if ((u * 2 + v * 9) % 1.0) < .45:
            return 0, ramp_colour(RAMPS_FUN_RED, .55 + g * .5)
        return 0, None
    if tag in (7, 19, 26):                             # gloss
        return .35 * math.exp(-((v - .7) / .1) ** 2), None
    if tag in (10, 11, 12, 13, 27):                    # petals: a pale centre line
        return .18 * math.exp(-((u - .5) / .12) ** 2) - .15 * (1 - v), None
    return 0, None


RAMPS_FUN_RED = [(0, (.25, .0, .02)), (.5, (.86, .06, .10)), (1, (1, .55, .55))]


def paint(work, gear, fun):
    """Both sheets and masks into `work` under the class's names (lower case, no extension)."""
    work = Path(work)
    (work / "paint").mkdir(parents=True, exist_ok=True)
    return {gear: paint_sheet(work, gear, TILES, INLAY, "gear", special, ramps=RAMPS, to=BLUE),
            fun: paint_sheet(work, fun, FUN_TILES, FUN_INLAY, "fun", special, ramps=RAMPS, fill={("fun", 20, "inlay")}, to=BLUE)}
