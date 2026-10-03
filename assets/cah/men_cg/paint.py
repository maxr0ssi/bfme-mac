"""The Men of the West's sheets (both subclasses paint the same tiles under their own names:
SKCAH_HWCG*/SKCAH_HWSM*): the serious gear in Gondor's language (assets/men/style.py: bright
steel, white, sable fields, sparing gold) plus Rohan's gilding and green, Dol Amroth's sea-blue and
Arnor's night-blue; and the fun sheet, whose first tiles the Wizards' fun sheet shares.

Tints: G is the cloth, the enamel and the heraldic fields (the White Tree's sable, Rohan's green),
R the second cloth (the ranger's hood and mask, grip wraps), B the gems; horsehair stays as painted.
"""
import math
from pathlib import Path

from ..kit import ornament as O
from ..kit.paint import BLUE, GREEN, RED, paint_sheet
from sagekit.units.paint import ramp_colour

S = O.S
(STEEL, GOLD, ENAMEL, MITHRIL, GOLDBAND, GEM, WINGS, HOODCLOTH, MASK, FEATHER, SEABAND, BLACKG, STARBAND, WHITE, HORSEHAIR,
 KNOTGOLD, GILT, WHITEHAIR, MAIL, CLOAK, TREE, SUN, LEATHER, PLANKS, BLADE, GRIP, FUR, TREECLOAK, MARKCLOAK, GOLDPLATE,
 PINKHAIR, IRON) = range(32)

RAMPS = {
    "steel": [(0, (.07, .08, .09)), (.3, (.30, .33, .36)), (.6, (.60, .64, .67)), (.85, (.83, .86, .88)), (1, (.97, .98, .99))],
    "sable": [(0, (.012, .014, .018)), (.5, (.06, .065, .075)), (.8, (.16, .17, .19)), (1, (.36, .37, .4))],
    "cloth": [(0, (.02, .03, .08)), (.4, (.06, .10, .25)), (.7, (.12, .19, .43)), (1, (.30, .38, .63))],
    "ground": [(0, (.02, .05, .02)), (.4, (.06, .16, .07)), (.7, (.12, .3, .13)), (1, (.3, .5, .28))],
    "seablue": [(0, (.01, .04, .1)), (.45, (.05, .2, .42)), (.8, (.2, .45, .7)), (1, (.6, .8, .95))],
    "night": [(0, (.01, .01, .05)), (.5, (.04, .06, .2)), (1, (.2, .25, .5))],
    "white": [(0, (.5, .52, .56)), (.6, (.9, .91, .93)), (1, (1, 1, 1))],
    "feather": [(0, (.42, .44, .48)), (.5, (.82, .84, .86)), (.85, (.96, .97, .98)), (1, (1, 1, 1))],
    "hair": [(0, (.1, .07, .05)), (.5, (.55, .45, .33)), (1, (.92, .86, .74))],
    "pinkhair": [(0, (.3, .0, .12)), (.45, (.95, .18, .55)), (.8, (1, .55, .8)), (1, (1, .9, .96))],
}

def _star5(x, y, r):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + math.pi * k / 5
        rr = r if k % 2 == 0 else r * .42
        pts.append("%d,%d" % (x + rr * math.cos(a), y + rr * math.sin(a)))
    return "polygon " + " ".join(pts)


def _tree(stars=True, crown=True):
    """The White Tree of Gondor beneath seven stars and the crown (planar shield face, centre
    128,128, up = image top): a tapered trunk, branches forking upward, roots; only lines and
    filled polygons, so the filled inlay never closes a branch into a blob."""
    out = ["polygon 121,222 135,222 132,170 131,120 128,92 125,120 124,170"]
    def branch(x0, y0, ang, length, depth):
        x1, y1 = x0 + length * math.cos(ang), y0 - length * math.sin(ang)
        out.append("line %d,%d %d,%d" % (x0, y0, x1, y1))
        if depth:
            branch(x1, y1, ang + .42, length * .62, depth - 1)
            branch(x1, y1, ang - .3, length * .7, depth - 1)
    for s in (1, -1):
        for y0, ln, a in ((176, 40, .5), (152, 42, .75), (130, 36, 1.0), (110, 26, 1.25)):
            ang = a if s > 0 else math.pi - a
            branch(128 + s * 3, y0, ang, ln, 2)
        out.append("line %d,222 %d,232" % (128 + s * 5, 128 + s * 26))
        out.append("line %d,226 %d,240" % (128 + s * 12, 128 + s * 44))
    if stars:
        for k in range(7):
            a = math.pi * (1.18 + .64 * k / 6)
            out.append(_star5(128 + 70 * math.cos(a), 96 + 50 * math.sin(a), 9))
    if crown:
        out.append("polygon 108,44 112,30 120,38 128,24 136,38 144,30 148,44")
        out.append("polygon 106,44 150,44 150,50 106,50")
    return out


def _ring(cx, cy, r, n=48):
    """A circle as line segments (a filled inlay layer would fill a circle primitive)."""
    p = [(cx + r * math.cos(TAU * k / n), cy + r * math.sin(TAU * k / n)) for k in range(n + 1)]
    return ["line %d,%d %d,%d" % (a[0], a[1], b[0], b[1]) for a, b in zip(p, p[1:])]


def _sun():
    """Rohan's sun-wheel for the round shield: twenty gold rays from the boss, two rings and a ring
    of beads at the rim (planar face, centre 128,128)."""
    out = _ring(128, 128, 56) + _ring(128, 128, 100)
    for k in range(20):
        a = TAU * k / 20
        b = TAU * (k + .5) / 20
        out.append("polygon %d,%d %d,%d %d,%d" % (128 + 30 * math.cos(a - .08), 128 + 30 * math.sin(a - .08),
                                                  128 + 94 * math.cos(b - .02), 128 + 94 * math.sin(b - .02),
                                                  128 + 30 * math.cos(a + .08), 128 + 30 * math.sin(a + .08)))
    for k in range(32):
        a = TAU * k / 32
        out.append("circle %d,%d %d,%d" % (128 + 110 * math.cos(a), 128 + 110 * math.sin(a), 128 + 110 * math.cos(a) + 4,
                                           128 + 110 * math.sin(a)))
    return out


TAU = 2 * math.pi


def _stars(n=7, y=128, r=13):
    out = []
    for k in range(n):
        x = (k + .5) * S / n
        for j in range(4):
            b = math.pi * j / 4
            out.append("line %d,%d %d,%d" % (x - r * math.cos(b), y - r * math.sin(b), x + r * math.cos(b), y + r * math.sin(b)))
    return out


def _waves():
    return ["polyline " + " ".join("%d,%d" % (x, 128 + 22 * math.sin(x / 256 * 6 * TAU) + dy) for x in range(0, 257, 8))
            for dy in (-34, 0, 34)]


def _knot(n=4):
    """Rohan's running interlace: two crossing waves with rings at the crossings."""
    pts = lambda ph: "polyline " + " ".join("%d,%d" % (x, 128 + 60 * math.sin(x / 256 * n * TAU + ph)) for x in range(0, 257, 6))
    out = [pts(0), pts(math.pi)]
    out += ["circle %d,128 %d,128" % (S / n * (k + .5) - S / n / 4, S / n * (k + .5) - S / n / 4 + 9) for k in range(n)]
    return out + ["line 0,40 256,40", "line 0,216 256,216"]


def _feathers(n=7):
    return ["line %d,0 %d,256" % (S * (k + .5) / n, S * (k + .5) / n) for k in range(n)] + \
        ["line %d,%d %d,%d" % (S * (k + .5) / n, y, S * (k + .5) / n + 14, y - 10) for k in range(n) for y in range(20, 256, 26)]


# tag: (ramp, mid, grain, edges, tint, {layer: (strokes, width)})
TILES = {
    STEEL: ("steel", .62, .25, "v", None, {}), GOLD: ("gold", .62, .25, "v", None, {}),
    ENAMEL: ("sable", .5, .25, "v", GREEN, {}), MITHRIL: ("mithril", .66, .25, "v", None, {}),
    GOLDBAND: ("gold", .6, .25, "", None, {"engrave": (O.border(26) + ["circle %d,128 %d,128" % (32 * k + 16, 32 * k + 26)
                                                                     for k in range(8)], 3)}),
    GEM: ("gem", .5, .1, "", BLUE, {}),
    WINGS: ("feather", .7, .2, "", None, {"engrave": (_feathers(), 2)}),
    HOODCLOTH: ("ground", .5, .25, "", RED, {}), MASK: ("ground", .36, .25, "", RED, {}),
    FEATHER: ("feather", .74, .15, "", None, {"engrave": (["arc %d,%d %d,%d 20,160" % (x - 18, y - 12, x + 18, y + 12)
                                                         for x in range(16, 256, 32) for y in range(14, 256, 22)], 1)}),
    SEABAND: ("seablue", .55, .2, "", GREEN, {"inlay": (_waves(), 5)}),
    BLACKG: ("black", .3, .1, "", None, {}),
    STARBAND: ("night", .55, .2, "", GREEN, {"inlay": (_stars(), 4)}),
    WHITE: ("white", .78, .1, "", None, {}),
    HORSEHAIR: ("hair", .55, .5, "", None, {}),
    KNOTGOLD: ("gold", .6, .25, "uv", None, {"engrave": (_knot(), 5)}),
    GILT: ("gold", .62, .3, "v", None, {"engrave": (["line %d,0 %d,256" % (x, x + 30) for x in range(-30, 256, 14)], 1)}),
    WHITEHAIR: ("white", .7, .5, "", None, {}),
    MAIL: ("steel", .55, .2, "", None, {}),
    CLOAK: ("cloth", .5, .2, "", GREEN, {}),
    TREE: ("sable", .5, .2, "", GREEN, {"inlay": (_tree(), 4)}),
    SUN: ("ground", .55, .2, "", GREEN, {"inlay": (_sun(), 4)}),
    LEATHER: ("leather", .5, .35, "", None, {"engrave": (O.border(10), 2)}),
    PLANKS: ("wood", .45, .3, "", None, {"engrave": (["line 0,%d 256,%d" % (y, y) for y in range(0, 256, 36)], 3)}),
    BLADE: ("steel", .74, .15, "u", None, {"engrave": (["line 0,128 256,128"], 6)}),
    GRIP: ("leather", .4, .3, "", RED, {}),
    FUR: ("fur", .45, .5, "", None, {}),
    TREECLOAK: ("sable", .5, .2, "", GREEN, {"inlay": (_tree(crown=False), 4)}),
    MARKCLOAK: ("ground", .5, .2, "", GREEN, {"inlay": (["line 0,222 256,222", "line 0,248 256,248"] +
                                                        ["polygon %d,235 %d,226 %d,235 %d,244" % (x, x + 8, x + 16, x + 8)
                                                         for x in range(0, 256, 16)], 3)}),
    GOLDPLATE: ("gold", .66, .25, "v", None, {"inlay": (O.sparkles(29, 30), 1)}),
    PINKHAIR: ("pinkhair", .6, .5, "", None, {}),
    IRON: ("blacki", .5, .4, "v", None, {}),
}
INLAY = {SEABAND: "white", STARBAND: "white", TREE: "white", SUN: "gold", TREECLOAK: "white", MARKCLOAK: "gold",
         GOLDPLATE: "white"}
FILL = {("gear", TREE, "inlay"), ("gear", TREECLOAK, "inlay"), ("gear", SUN, "inlay"), ("gear", MARKCLOAK, "inlay")}

# ------------------------------------------------------------------ fun (the Wizards' fun sheet starts with these)
(F_GOLD, F_IRON, F_OAK, F_STEEL, F_PINK, F_RAINBOW, F_FLUFF, F_CHEESE, F_RIND, F_CANOPY, F_BLACK, F_PIZZA, F_CRUST, F_ROAST,
 F_BONE, F_HOTPINK, F_PINKGEM, F_PAN, F_DARKWOOD, F_SPANGLE, F_PINKFELT, F_LOLLY, F_GLITTER, F_LEAF, F_FRILL, F_WHITE) = range(26)
RAINBOW = [(.85, .08, .08), (.98, .48, .05), (.98, .85, .1), (.15, .65, .2), (.1, .35, .85), (.3, .12, .6), (.62, .18, .7)]
FUN_RAMPS = {"cheese": [(0, (.45, .3, .02)), (.5, (.98, .78, .2)), (.85, (1, .92, .55)), (1, (1, 1, .85))],
             "rind": [(0, (.35, .15, .0)), (.5, (.9, .55, .08)), (1, (1, .85, .45))],
             "crust": [(0, (.25, .1, .02)), (.5, (.78, .5, .2)), (1, (1, .85, .55))],
             "roast": [(0, (.12, .04, .01)), (.45, (.55, .25, .07)), (.8, (.85, .5, .18)), (1, (1, .8, .5))],
             "bone": [(0, (.5, .45, .38)), (.6, (.92, .88, .8)), (1, (1, 1, .97))],
             "spangle": [(0, (.01, .02, .1)), (.5, (.06, .12, .45)), (1, (.3, .45, .9))],
             "leaf": [(0, (.02, .12, .02)), (.5, (.15, .5, .12)), (1, (.55, .85, .4))]}
FUN_TILES = {
    F_GOLD: ("gold", .64, .25, "v", None, {}), F_IRON: ("blacki", .5, .4, "v", None, {}), F_OAK: ("wood", .5, .25, "", None, {}),
    F_STEEL: ("steel", .62, .25, "v", None, {}), F_PINK: ("pink", .55, .2, "", None, {}), F_RAINBOW: ("white", .6, .15, "", None, {}),
    F_FLUFF: ("white", .65, .5, "", None, {}),
    F_CHEESE: ("cheese", .55, .2, "", None, {}), F_RIND: ("rind", .55, .2, "", None, {}),
    F_CANOPY: ("red", .55, .15, "", None, {}), F_BLACK: ("black", .4, .1, "", None, {}),
    F_PIZZA: ("cheese", .6, .25, "", None, {}), F_CRUST: ("crust", .55, .35, "", None, {}),
    F_ROAST: ("roast", .55, .35, "", None, {}), F_BONE: ("bone", .62, .2, "", None, {}),
    F_HOTPINK: ("hotpink", .58, .3, "v", None, {"inlay": (O.sparkles(14), 1)}), F_PINKGEM: ("hotpink", .62, .15, "", None, {}),
    F_PAN: ("steel", .3, .35, "", None, {"engrave": (["circle 128,128 128,30", "circle 128,128 128,112"], 5)}),
    F_DARKWOOD: ("wood", .3, .3, "", None, {}),
    F_SPANGLE: ("spangle", .5, .2, "", None, {"inlay": (O.sparkles(19, 26), 1)}),
    F_PINKFELT: ("pink", .5, .25, "", None, {"inlay": (O.sparkles(20, 60), 1)}),
    F_LOLLY: ("white", .7, .1, "", None, {}), F_GLITTER: ("white", .7, .2, "", None, {"inlay": (O.sparkles(22, 120), 1)}),
    F_LEAF: ("leaf", .5, .2, "", None, {}), F_FRILL: ("white", .75, .2, "", None, {"engrave": (["line %d,0 %d,256" % (x, x)
                                                                                             for x in range(4, 256, 12)], 2)}),
    F_WHITE: ("white", .72, .1, "", None, {}),
}
FUN_INLAY = {F_HOTPINK: "white", F_SPANGLE: "gold", F_PINKFELT: "white", F_GLITTER: "white"}


def _star(x, y, r):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + math.pi * k / 5
        rr = r if k % 2 == 0 else r * .42
        pts.append("%d,%d" % (x + rr * math.cos(a), y + rr * math.sin(a)))
    return "polygon " + " ".join(pts)


FUN_TILES[F_SPANGLE] = ("spangle", .5, .2, "", None, {"inlay": ([_star(x + (16 if (y // 48) % 2 else 0), y, 13)
                                                                 for y in range(24, 256, 48) for x in range(16, 256, 64)], 1)})
FUN_FILL = {("fun", F_SPANGLE, "inlay")}


def _fold(u, x, y, n=7):
    return .16 * math.sin(u * 2 * n * math.pi) + .03 * math.sin(x * 2.1) * math.sin(y * 2.1)


def special(sheet, tag, u, v, x, y, g, n1):
    """Extra shading per tile (folds, rings, hair, fluff, food); (value offset, fixed rgb or None)."""
    if sheet == "gear":
        if tag in (CLOAK, TREECLOAK, MARKCLOAK, HOODCLOTH):
            return _fold(u, x, y) - .1 * max(0, .12 - v) / .12, None
        if tag == MAIL:
            cx, cy = (x % 10) - 5, ((y + (5 if (x // 10) % 2 else 0)) % 10) - 5
            return (.35 if 2.2 < math.hypot(cx, cy) < 4.4 else -.3), None
        if tag in (HORSEHAIR, WHITEHAIR, PINKHAIR):
            return .3 * math.sin(x * .9 + 2 * math.sin(y * .05)) * (.5 + n1 * .5), None
        if tag == FUR:
            return .25 * math.sin(x * .9 + 3 * math.sin(y * .15)) * n1, None
        if tag == GEM:
            return .55 * (v - .5), None
        if tag == GRIP:
            return (.12 if ((u * 6 + v * 3) % 1.0) < .8 else -.16), None
        return 0, None
    return fun_special(tag, u, v, x, y, g, n1)


def fun_special(tag, u, v, x, y, g, n1):
    if tag in (F_PINK, F_RAINBOW, F_GLITTER):
        f = _fold(u, x, y)
        if tag == F_RAINBOW:
            c = RAINBOW[min(6, int(u * 7))]
            return 0, [max(0, min(1, q * (1 + f * 1.6 + g))) for q in c]
        if tag == F_GLITTER:
            c = RAINBOW[min(6, int(((u + v) * 3.5) % 7))]
            k = 1 + g + .4 * max(0, n1 - .8) / .2
            return 0, [max(0, min(1, (.55 * q + .45) * k)) for q in c]
        return f, None
    if tag == F_FLUFF:
        return .3 * math.sin(x * 1.3 + 4 * math.sin(y * .23)) * n1 + .15 * math.sin(y * 1.7 + x * .3), None
    if tag == F_CHEESE:                                     # holes
        for cx, cy, r in ((40, 60, 18), (150, 40, 12), (200, 150, 22), (90, 170, 15), (30, 220, 10), (170, 230, 14),
                          (120, 110, 9), (230, 70, 10)):
            d = math.hypot(x - cx, y - cy)
            if d < r:
                return -.32 + .2 * (d / r), None
        return 0, None
    if tag == F_CANOPY:                                     # red and white gores
        if int(u * 8) % 2:
            return 0, ramp_colour([(0, (.6, .6, .62)), (.6, (.94, .94, .95)), (1, (1, 1, 1))], .7 + g * .3)
        return 0, None
    if tag == F_PIZZA:                                      # planar: crust rim, sauce, cheese, pepperoni, basil
        d = math.hypot(u - .5, v - .5)
        if d > .44:
            return 0, ramp_colour(FUN_RAMPS["crust"], .55 + g - 1.2 * (d - .47) + .15 * math.sin(x * .3))
        for cx, cy in ((.32, .35), (.62, .3), (.7, .6), (.4, .66), (.52, .5), (.25, .55), (.58, .78)):
            e = math.hypot(u - cx, v - cy)
            if e < .075:
                return 0, ramp_colour([(0, (.25, .02, .02)), (.6, (.72, .12, .08)), (1, (.95, .4, .3))], .55 + g - 2 * e)
        sauce = .45 + .25 * math.sin(x * .11) * math.sin(y * .13) + g
        if sauce > .62 or d > .41:
            return 0, ramp_colour([(0, (.3, .02, .0)), (.5, (.8, .15, .05)), (1, (1, .45, .25))], .5 + g)
        return .1 * math.sin(x * .7 + y * .4), None
    if tag == F_ROAST:
        return .2 * math.sin(v * 9 + 2 * math.sin(u * 7)) + .1 * n1, None
    if tag == F_PAN:
        d = math.hypot(u - .5, v - .5)
        return -.2 * max(0, .3 - d) / .3 + .25 * max(0, d - .44) / .06, None
    if tag == F_LOLLY:                                      # a rainbow spiral (planar)
        a = math.atan2(v - .5, u - .5)
        d = math.hypot(u - .5, v - .5)
        k = int(((a / TAU) * 6 + d * 14) % 6)
        c = [(.95, .1, .35), (1, 1, 1), (.98, .6, .1), (1, 1, 1), (.25, .7, .95), (1, 1, 1)][k]
        return 0, [max(0, min(1, q * (.82 + .25 * (1 - d) + g * .3))) for q in c]
    if tag in (F_SPANGLE, F_PINKFELT):
        return _fold(u, x, y, 5) * .6, None
    return 0, None


def paint(work, prefix):
    """Both sheets and masks into `work`: {texture: (dds path, mask path)}. prefix: skcah_hwcg."""
    work = Path(work)
    (work / "paint").mkdir(parents=True, exist_ok=True)
    ramps = dict(RAMPS, **FUN_RAMPS)
    return {prefix + "gear": paint_sheet(work, prefix + "gear", TILES, INLAY, "gear", special, ramps=ramps, fill=FILL),
            prefix + "fun": paint_sheet(work, prefix + "fun", FUN_TILES, FUN_INLAY, "fun", special, ramps=ramps, fill=FUN_FILL)}
