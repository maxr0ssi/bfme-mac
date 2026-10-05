"""The Dwarf's two sheets: SKCAH_DWGEAR.tga (the serious Erebor gear, from the Dwarven palette
of assets/dwarves) and SKCAH_DWFUN.tga (the fun choices), tile tables for the kit's painter
(assets/cah/kit/paint.py). Tinted areas (G our blue enamel and cloth, R the leather wraps, B the
gems, and the "enamel" fields behind the friezes and runes) all follow the Paint picker (B) on the CaH
sheets (docs/CAH.md); the jester's red follows it too, its yellow stays yellow.
"""
import math
from pathlib import Path

from ..kit import ornament as O
from ..kit.paint import BLUE, GREEN, RED, RAMPS as R, paint_sheet
from sagekit.units.paint import ramp_colour

S = O.S
RAINBOW = [(.85, .08, .08), (.98, .48, .05), (.98, .85, .1), (.15, .65, .2), (.1, .35, .85), (.3, .12, .6), (.62, .18, .7)]

# tag: (ramp, mid, grain, edges, tint channel, {layer: (strokes, width)}); special texels below
TILES = {
    0: ("bronze", .5, .3, "v", None, {}), 1: ("gold", .64, .25, "v", None, {}), 2: ("blacki", .55, .45, "v", None, {}),
    3: ("steel", .6, .3, "v", None, {}), 4: ("mithril", .66, .3, "v", None, {}), 5: ("ground", .6, .2, "", GREEN, {}),
    6: ("cloth", .5, .2, "", GREEN, {}), 7: ("cloth", .32, .2, "", RED, {}), 8: ("wood", .5, .25, "", None, {}),
    9: ("ground", .58, .2, "", GREEN, {"inlay": (O.runes(8, 9) + ["line 0,30 256,30", "line 0,226 256,226"], 6)}),
    10: ("ground", .56, .2, "", GREEN, {"inlay": (O.device(), 6)}),
    11: ("steel", .55, .2, "", None, {}), 12: ("gem", .5, .1, "", BLUE, {}),
    13: ("mithril", .62, .3, "", None, {"engrave": (["line %d,0 %d,256" % (32 * k, 32 * k) for k in range(9)] +
                                                   ["line %d,40 %d,200" % (32 * k + 16, 32 * k + 16) for k in range(8)], 2)}),
    14: ("bronze", .5, .3, "v", None, {}), 15: ("fur", .45, .5, "", None, {}),
    16: ("gold", .62, .3, "uv", None, {"engrave": (O.chevrons(6, 128, 50) + O.chevrons(6, 128, 20) + O.border(14), 4)}),
    17: ("blacki", .55, .45, "uv", None, {"rivet": (O.rivets_row(14, 9) + O.rivets_row(242, 9), 2), "engrave": (O.border(26), 2),
                                          "enamel": (["rectangle 40,72 216,184"], 1)}),
    18: ("steel", .7, .25, "u", None, {"inlay": (O.knot(3), 3)}),
    19: ("horn", .55, .35, "", None, {"engrave": (["line 0,%d 256,%d" % (y, y + 6) for y in range(6, 256, 15)], 3)}),
    20: ("gold", .6, .2, "", None, {"engrave": (["line %d,0 %d,256" % (x, x + 40) for x in range(-40, 256, 12)], 2)}),
    21: ("bronze", .52, .3, "uv", None, {"engrave": (O.border(16) + O.border(30), 3), "inlay": (O.tri_frieze(100, 156, 4), 3),
                                          "enamel": (["rectangle 30,96 226,160"], 1),
                                          "rivet": (["circle 20,20 26,20", "circle 236,20 242,20", "circle 20,236 26,236",
                                                     "circle 236,236 242,236"], 2)}),
    22: ("blacki", .55, .45, "v", None, {"engrave": (["line %d,0 %d,256" % (32 * k, 32 * k) for k in range(9)], 3),
                                         "rivet": (["circle %d,%d %d,%d" % (32 * k + 6, y, 32 * k + 10, y) for k in range(8)
                                                    for y in (24, 80, 136, 192)], 2)}),
    23: ("bronze", .5, .3, "v", None, {"inlay": (O.tri_frieze(205, 240, 16) + ["line 0,200 256,200", "line 0,246 256,246"], 3),
                                       "enamel": (["rectangle 0,201 256,245"], 1),
                                       "engrave": (["line %d,0 %d,190" % (16 * k, 16 * k + 8) for k in range(17)], 1)}),
    24: ("leather", .5, .35, "", None, {"engrave": (O.border(10), 2)}),
    25: ("mithril", .66, .25, "", None, {"inlay": (O.runes(16, 25, 60, 196) + ["line 0,30 256,30", "line 0,226 256,226"], 5),
                                         "enamel": (["rectangle 0,32 256,224"], 1)}),
    26: ("bluesteel", .6, .3, "v", None, {"engrave": (["line %d,0 %d,256" % (64 * k, 64 * k) for k in range(5)], 2),
                                          "enamel": (["rectangle %d,0 %d,256" % (64 * k - 12, 64 * k + 12) for k in range(5)], 1)}),
    27: ("bronze", .55, .3, "", None, {"engrave": (["line 128,0 128,256"] + ["line 128,%d %d,%d" % (y, x, y + 26)
                                                    for y in range(10, 240, 18) for x in (20, 236)], 2)}),
    28: ("wood", .45, .3, "", None, {"engrave": (["line 0,%d 256,%d" % (y, y) for y in range(0, 256, 36)], 3)}),
    # the crown-helm's fixed-colour variants: gold-plated dome and rune band, hot pink metal
    29: ("gold", .62, .3, "v", None, {"engrave": (O.tri_frieze(205, 240, 16) + ["line %d,0 %d,190" % (16 * k, 16 * k + 8)
                                                                               for k in range(17)], 2)}),
    30: ("gold", .6, .2, "", None, {"engrave": (O.runes(8, 9) + ["line 0,30 256,30", "line 0,226 256,226"], 6)}),
    31: ("hotpink", .55, .3, "v", None, {"inlay": (O.sparkles(31, 40), 1)}),
}
INLAY = {9: "gold", 10: "gold", 18: "gold", 21: "gold", 23: "gold", 25: "gold", 31: "white"}

FUN_TILES = {
    0: ("gold", .64, .25, "v", None, {}), 1: ("blacki", .55, .45, "v", None, {}), 2: ("wood", .5, .25, "", None, {}),
    3: ("steel", .6, .3, "v", None, {}), 4: ("pink", .55, .2, "", None, {}), 5: ("white", .6, .15, "", None, {}),
    6: ("pink", .6, .5, "", None, {}), 7: ("red", .55, .25, "", GREEN, {}), 8: ("yellow", .55, .25, "", None, {}),
    9: ("red", .55, .2, "", GREEN, {}), 10: ("red", .55, .45, "", None, {}), 11: ("yellow", .58, .12, "", None, {}),
    12: ("orange", .55, .15, "", None, {}), 13: ("black", .45, .1, "", None, {}),
    14: ("hotpink", .58, .3, "v", None, {"inlay": (O.sparkles(14), 1)}),
    15: ("hotpink", .5, .2, "", None, {"inlay": (O.heart() + O.sparkles(15, 50), 4), "engrave": (["circle 128,128 128,22"], 6)}),
    16: ("yellow", .6, .15, "", None, {"engrave": (O.smiley() + ["circle 128,128 128,22"], 9)}),
    17: ("scales", .55, .3, "", None, {"engrave": (O.scales(), 2)}),
    18: ("orange", .55, .3, "", None, {"engrave": (["line %d,0 %d,256" % (x, x) for x in range(8, 256, 22)], 3)}),
    19: ("blacki", .45, .4, "", None, {"engrave": (["circle 128,128 128,30", "circle 128,128 128,112"], 5)}),
    20: ("white", .65, .5, "", None, {}), 21: ("horn", .55, .35, "", None, {"engrave": (["line 0,%d 256,%d" % (y, y + 6)
                                                                                         for y in range(6, 256, 15)], 3)}),
    22: ("bronze", .5, .3, "v", None, {}), 23: ("hotpink", .62, .15, "", None, {}), 24: ("copper", .55, .4, "v", None, {}),
    25: ("white", .7, .1, "", None, {}),
}
FUN_INLAY = {14: "white", 15: "red"}


def special(sheet, tag, u, v, x, y, g, n1):
    """Extra shading per tile (folds, rings, fluff, bands); returns (value offset, rgb or None)."""
    if sheet == "gear":
        if tag == 6:                                # wool: seven folds, worn hem
            return .16 * math.sin(u * 14 * math.pi) - .1 * max(0, .15 - v) / .15 + .03 * math.sin(x * 2.1) * math.sin(y * 2.1), None
        if tag == 11:                               # riveted mail rings
            cx, cy = (x % 10) - 5, ((y + (5 if (x // 10) % 2 else 0)) % 10) - 5
            return (.35 if 2.2 < math.hypot(cx, cy) < 4.4 else -.3), None
        if tag == 15:
            return .25 * math.sin(x * .9 + 3 * math.sin(y * .15)) * n1, None
        if tag == 12:
            return .55 * (v - .5), None
        if tag == 7:
            return (.12 if ((u * 6 + v * 3) % 1.0) < .8 else -.16), None
        return 0, None
    if tag in (4, 5):                               # pink and rainbow cloth: seven folds
        fold = .16 * math.sin(u * 14 * math.pi) + .03 * math.sin(x * 2.1) * math.sin(y * 2.1)
        if tag == 5:
            c = RAINBOW[min(6, int(u * 7))]
            k = 1 + fold * 1.6 + g
            return 0, [max(0, min(1, q * k)) for q in c]
        return fold, None
    if tag in (6, 20):                              # fluff
        return .3 * math.sin(x * 1.3 + 4 * math.sin(y * .23)) * n1 + .15 * math.sin(y * 1.7 + x * .3), None
    if tag == 9:                                    # party stripes (white) and dots
        if ((u + v) * 5) % 1.0 < .3:
            return 0, ramp_colour(R["white"], .7 + g * .3)
        return (.2 if math.hypot((x % 32) - 16, (y % 32) - 16) < 5 else 0), None
    if tag == 10:                                   # horsehair
        return .35 * math.sin(x * .8 + 2 * math.sin(y * .05)) * (.5 + n1 * .5), None
    if tag in (11, 13, 23):                         # gloss: a bright band
        return .35 * math.exp(-((v - .7) / .08) ** 2), None
    if tag == 17:                                   # a pale belly
        return .25 * max(0, math.cos(u * 2 * math.pi + math.pi)), None
    if tag == 19:                                   # burnt centre, polished rim
        d = math.hypot(u - .5, v - .5)
        return -.2 * max(0, .3 - d) / .3 + .25 * max(0, d - .44) / .06, None
    return 0, None


def paint(work):
    """Both sheets and masks into `work`: {texture: (dds path, mask path)}."""
    work = Path(work)
    (work / "paint").mkdir(parents=True, exist_ok=True)
    return {"skcah_dwgear": paint_sheet(work, "skcah_dwgear", TILES, INLAY, "gear", special, to=BLUE),
            "skcah_dwfun": paint_sheet(work, "skcah_dwfun", FUN_TILES, FUN_INLAY, "fun", special, fill={("fun", 15, "inlay")}, to=BLUE)}
