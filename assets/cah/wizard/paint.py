"""The Wizards' sheets: SKCAH_WZGEAR.tga (the Istari's felts in Grey, White, Brown and the Blue
Wizards' blue, silver, rune-carved wood and crystal, travelling cloth) and SKCAH_WZFUN.tga (the
Men's fun tiles, assets/cah/men_cg/paint.py, so the cheese crown and the umbrella draw the same).

Tints: G is the hat bands and the travelling cloak, R the cloak's lining and the staff's wraps,
B the crystals; the felts stay their order's colour.
"""
import math
from pathlib import Path

from ..kit import ornament as O
from ..kit.paint import BLUE, GREEN, RED, paint_sheet
from ..men_cg import paint as MP

S = O.S
(GREYFELT, WHITEFELT, BROWNFELT, BLUEFELT, BAND, SILVER, STEEL, GOLD, GEM, WOOD, DARKWOOD, RUNES, CLOAK, LINING, LEATHER,
 FEATHER, NEST, EGG, BIRD, STARS, BRASS, GLASS, WRAP, PINKFELT, SPANGLE, HOTPINK, GLITTER, BLACK, WHITE, BEAK, ROPE,
 HEMSTARS) = range(32)

RAMPS = {
    "greyfelt": [(0, (.1, .1, .11)), (.45, (.42, .42, .43)), (.8, (.68, .68, .69)), (1, (.86, .86, .87))],
    "whitefelt": [(0, (.42, .43, .46)), (.5, (.84, .85, .87)), (.85, (.95, .96, .97)), (1, (1, 1, 1))],
    "brownfelt": [(0, (.08, .05, .02)), (.45, (.34, .22, .11)), (.8, (.55, .4, .22)), (1, (.75, .6, .4))],
    "bluefelt": [(0, (.01, .03, .1)), (.45, (.06, .16, .45)), (.8, (.2, .36, .72)), (1, (.5, .65, .95))],
    "cloth": [(0, (.1, .1, .11)), (.45, (.38, .38, .4)), (1, (.78, .78, .8))],
    "nest": [(0, (.06, .04, .02)), (.5, (.36, .26, .14)), (1, (.7, .58, .4))],
    "egg": [(0, (.2, .4, .45)), (.6, (.55, .82, .86)), (1, (.9, 1, 1))],
    "bird": [(0, (.02, .08, .25)), (.5, (.1, .35, .8)), (1, (.55, .8, 1))],
    "brass": [(0, (.15, .09, .02)), (.45, (.55, .38, .12)), (.8, (.86, .7, .35)), (1, (1, .93, .7))],
    "glass": [(0, (.4, .3, .05)), (.5, (1, .82, .35)), (1, (1, 1, .85))],
    "spangle": MP.FUN_RAMPS["spangle"],
}


def _hemstars():
    return [MP._star5(x, 196, 17) for x in range(16, 256, 32)] + [MP._star5(x, 150, 9) for x in range(32, 256, 32)] + \
        ["line 0,222 256,222", "line 0,248 256,248"]


TILES = {
    GREYFELT: ("greyfelt", .5, .3, "", None, {}), WHITEFELT: ("whitefelt", .6, .2, "", None, {}),
    BROWNFELT: ("brownfelt", .5, .4, "", None, {}), BLUEFELT: ("bluefelt", .5, .3, "", None, {}),
    BAND: ("cloth", .45, .25, "", GREEN, {"engrave": (["line 0,40 256,40", "line 0,216 256,216"], 4)}),
    SILVER: ("mithril", .66, .25, "v", None, {}), STEEL: ("steel", .6, .25, "v", None, {}), GOLD: ("gold", .62, .25, "v", None, {}),
    GEM: ("gem", .55, .1, "", BLUE, {}),
    WOOD: ("wood", .5, .35, "", None, {"engrave": (["line %d,0 %d,256" % (x, x + 8) for x in range(6, 256, 22)], 2)}),
    DARKWOOD: ("wood", .3, .35, "", None, {}),
    RUNES: ("mithril", .55, .2, "", None, {"inlay": (O.runes(8, 50) + ["line 0,40 256,40", "line 0,216 256,216"], 5)}),
    CLOAK: ("cloth", .5, .2, "", GREEN, {}), LINING: ("cloth", .35, .2, "", RED, {}),
    LEATHER: ("leather", .5, .35, "", None, {"engrave": (O.border(10), 2)}),
    FEATHER: ("white", .6, .3, "", None, {"engrave": (MP._feathers(5), 2)}), NEST: ("nest", .5, .6, "", None, {}),
    EGG: ("egg", .65, .15, "", None, {}), BIRD: ("bird", .55, .2, "", None, {}),
    STARS: ("bluefelt", .45, .2, "", None, {"inlay": ([MP._star5(x, y, 11) for y in (64, 192) for x in range(16, 256, 64)] +
                                                      [MP._star5(x, 128, 8) for x in range(48, 256, 64)], 1)}),
    BRASS: ("brass", .55, .3, "v", None, {}), GLASS: ("glass", .7, .15, "", None, {}),
    WRAP: ("leather", .45, .3, "", RED, {}),
    PINKFELT: ("pink", .55, .25, "", None, {"inlay": (O.sparkles(23, 70), 1)}),
    SPANGLE: ("spangle", .5, .2, "", None, {"inlay": ([MP._star5(x + (16 if (y // 48) % 2 else 0), y, 12)
                                                       for y in range(24, 256, 48) for x in range(16, 256, 64)], 1)}),
    HOTPINK: ("hotpink", .58, .3, "v", None, {"inlay": (O.sparkles(25), 1)}), GLITTER: ("white", .7, .2, "", None, {}),
    BLACK: ("black", .35, .1, "", None, {}), WHITE: ("white", .75, .1, "", None, {}), BEAK: ("orange", .6, .1, "", None, {}),
    ROPE: ("leather", .55, .3, "", None, {"engrave": (["line %d,0 %d,256" % (x, x + 30) for x in range(-30, 256, 12)], 3)}),
    HEMSTARS: ("bluefelt", .45, .2, "", None, {"inlay": (_hemstars(), 1)}),
}
INLAY = {RUNES: "white", STARS: "gold", PINKFELT: "white", SPANGLE: "gold", HOTPINK: "white", HEMSTARS: "white"}
FILL = {("gear", STARS, "inlay"), ("gear", SPANGLE, "inlay"), ("gear", HEMSTARS, "inlay")}


def special(sheet, tag, u, v, x, y, g, n1):
    if sheet == "fun":
        return MP.fun_special(tag, u, v, x, y, g, n1)
    if tag in (GREYFELT, WHITEFELT, BROWNFELT, BLUEFELT, PINKFELT, SPANGLE):      # felt: soft creases
        return .1 * math.sin(u * 9 * math.pi + 2 * math.sin(v * 5)) + .06 * n1, None
    if tag in (CLOAK, LINING, HEMSTARS):
        return .5 * MP._fold(u, x, y, 6) - .1 * max(0, .12 - v) / .12, None
    if tag == NEST:
        return .35 * math.sin(x * .7 + 3 * math.sin(y * .2)) * math.sin(y * .5 + x * .1), None
    if tag == GEM:
        return .55 * (v - .5), None
    if tag == GLITTER:
        c = MP.RAINBOW[min(6, int(((u + v) * 3.5) % 7))]
        k = 1 + g + .5 * max(0, n1 - .78) / .22
        return 0, [max(0, min(1, (.55 * q + .45) * k)) for q in c]
    if tag == WRAP:
        return (.12 if ((u * 6 + v * 3) % 1.0) < .8 else -.16), None
    return 0, None


def paint(work):
    work = Path(work)
    (work / "paint").mkdir(parents=True, exist_ok=True)
    ramps = dict(MP.RAMPS, **MP.FUN_RAMPS)
    ramps.update(RAMPS)
    return {"skcah_wzgear": paint_sheet(work, "skcah_wzgear", TILES, INLAY, "gear", special, ramps=ramps, fill=FILL),
            "skcah_wzfun": paint_sheet(work, "skcah_wzfun", MP.FUN_TILES, MP.FUN_INLAY, "fun", special, ramps=ramps,
                                       fill=MP.FUN_FILL)}
