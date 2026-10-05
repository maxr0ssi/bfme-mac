"""The Evil classes' sheets: one serious table (Mordor's F2 iron, steel and ember, Isengard's black
iron, silver and White Hand, Angmar's blue iron and frozen tips, Goblin crimson and bone, Harad
brass and Easterling lacquer) and one fun table, painted by the kit's painter (kit/paint.py) into
each class's own sheet pair. Ramps come from the factions' own palettes (assets/<faction>/style.py).

The 3-colour mask: the cloth (war cloaks, turbans, sashes), the leather wraps and second cloth, the
gems, the Easterling lacquer, the Goblins' crimson war paint (not its chips) and Angmar's cold enamel
all follow the Paint picker (B) on the CaH sheets (docs/CAH.md); metal, bone and fixed fun colours
stay as painted.
"""
import math

from assets.angmar.style import PALETTE as ANGMAR
from assets.goblins.style import PALETTE as GOBLINS
from assets.isengard.style import PALETTE as ISENGARD
from assets.mordor.style import PALETTE as MORDOR
from sagekit import paths
from sagekit.units.paint import ramp_colour

from ..kit import ornament as O
from ..kit.paint import BLUE, GREEN, PAINT, RED, RAMPS as KR, paint_sheet

RAMPS = {
    "m_iron": [(0, (.01, .01, .01)), (.3, (.06, .055, .05)), (.6, (.15, .14, .13)), (.85, (.30, .28, .26)), (1, (.48, .46, .43))],
    "m_steel": MORDOR.ramps["steel"], "m_fire": MORDOR.ramps["fire"], "m_witch": MORDOR.ramps["witch"],
    "brass": MORDOR.ramps["brass"], "warpaint": MORDOR.ramps["warpaint"], "ivory": MORDOR.ramps["ivory"],
    "i_iron": ISENGARD.ramps["iron"], "i_silver": ISENGARD.ramps["silver"], "i_mark": ISENGARD.ramps["mark"],
    "a_iron": ANGMAR.ramps["iron"], "a_trim": ANGMAR.ramps["trim"], "a_ice": ANGMAR.ramps["ice"],
    "g_hide": GOBLINS.ramps["hide"], "g_bone": GOBLINS.ramps["bone"],
    "green": [(0, (.02, .08, .02)), (.5, (.18, .52, .14)), (1, (.7, .95, .5))],
    "zinc": [(0, (.12, .13, .14)), (.4, (.42, .45, .48)), (.75, (.72, .75, .78)), (1, (.95, .97, 1.0))],
    "lilac": [(0, (.12, .06, .2)), (.5, (.55, .38, .85)), (1, (.92, .85, 1.0))],
    "sky": [(0, (.04, .1, .25)), (.5, (.3, .6, .95)), (1, (.85, .95, 1.0))],
    "wood": KR["wood"], "cloth": KR["cloth"],
    "darkwood": [(0, (.015, .012, .01)), (.5, (.13, .095, .065)), (.85, (.3, .23, .16)), (1, (.45, .36, .26))],
}
RAINBOW = [(.85, .08, .08), (.98, .48, .05), (.98, .85, .1), (.15, .65, .2), (.1, .35, .85), (.3, .12, .6), (.62, .18, .7)]


def hand():
    """Saruman's White Hand (planar tile): a palm, four fingers and a thumb, filled."""
    out = ["roundrectangle 84,120 172,214 18,18"]
    for k, (x, top) in enumerate(((88, 56), (110, 40), (132, 44), (154, 62))):
        out.append("roundrectangle %d,%d %d,%d 9,9" % (x, top, x + 18, 140))
    out.append("polygon 84,170 46,130 36,138 70,196 96,206")
    return out


def lamellae():
    """Rows of small lacquered plates laced with gold (Easterling lamellar)."""
    out = []
    for r in range(6):
        y = 8 + r * 42
        out.append("line 0,%d 256,%d" % (y + 36, y + 36))
        for c in range(9):
            x = c * 30 + (15 if r % 2 else 0) - 10
            out.append("roundrectangle %d,%d %d,%d 5,5" % (x, y, x + 26, y + 34))
    return out


def hug_me():
    """The sign: HUG ME in fat letters over a heart (planar tile)."""
    font = "font '%s' font-size 66 " % paths.FONT
    return [font + "text 28,112 'HUG'", font + "text 48,190 'ME'"]


# tag: (ramp, mid, grain, edges, tint channel, {layer: (strokes, width)})
TILES = {
    0: ("m_iron", .62, .4, "v", None, {}),
    1: ("m_iron", .6, .45, "uv", None, {"rivet": (O.rivets_row(16, 8) + O.rivets_row(240, 8), 2), "engrave": (O.border(28), 2)}),
    2: ("m_steel", .62, .3, "v", None, {}),
    3: ("m_fire", .72, .2, "", None, {}),
    4: ("m_iron", .55, .3, "", None, {}),
    5: ("cloth", .5, .25, "", GREEN, {}),
    6: ("leather", .45, .35, "", RED, {}),
    7: ("i_iron", .62, .35, "v", None, {}),
    8: ("i_silver", .62, .25, "v", None, {}),
    9: ("i_iron", .58, .3, "", None, {"inlay": (hand(), 2)}),
    10: ("a_iron", .62, .35, "v", None, {}),
    11: ("a_ice", .72, .15, "", None, {}),
    12: ("a_iron", .55, .3, "", None, {}),
    13: ("g_hide", .55, .35, "v", PAINT, {}),
    14: ("g_bone", .55, .3, "", None, {"engrave": (["line 40,30 70,110", "line 70,110 60,170", "line 190,60 170,140"], 2)}),
    15: ("brass", .6, .3, "v", None, {}),
    16: ("cloth", .55, .2, "", GREEN, {}),
    17: ("cloth", .42, .2, "", RED, {}),
    18: ("blacki", .55, .3, "", PAINT, {"inlay": (lamellae(), 2)}),
    19: ("gold", .62, .3, "v", None, {}),
    20: ("steel", .5, .2, "", None, {}),
    21: ("darkwood", .5, .35, "", None, {"engrave": (["line %d,0 %d,256" % (x, x + 8) for x in range(4, 256, 21)], 2)}),
    22: ("gem", .5, .1, "", BLUE, {}),
    23: ("m_steel", .66, .25, "u", None, {"engrave": (["line 0,128 256,128"], 5)}),
    24: ("fur", .4, .5, "", None, {}),
    25: ("m_witch", .7, .2, "", None, {}),
    26: ("enamel", .5, .2, "v", PAINT, {"engrave": (O.border(12), 2)}),          # Angmar's cold enamel (crown band, lame)
    27: ("brass", .58, .25, "uv", None, {"engrave": (O.border(14), 3), "inlay": (O.tri_frieze(96, 160, 8), 2)}),
    28: ("gold", .6, .25, "", None, {"engrave": (["line 128,20 128,236"] + O.chevrons(5, 60, 18) + O.chevrons(5, 200, 18), 3)}),
    29: ("hotpink", .55, .3, "v", None, {"inlay": (O.sparkles(29, 50), 1)}),
    30: ("pink", .72, .2, "v", None, {}),
    31: ("m_iron", .6, .4, "", None, {"engrave": (O.chevrons(6, 128, 40) + O.border(10), 3)}),
}
INLAY = {9: "i_mark", 18: "gold", 27: "warpaint", 29: "white"}

FUN_TILES = {
    0: ("gold", .64, .25, "v", None, {}), 1: ("black", .5, .15, "", None, {}), 2: ("cloth", .5, .1, "", GREEN, {}),
    3: ("white", .75, .05, "", None, {}), 4: ("pink", .55, .2, "", None, {}), 5: ("white", .6, .15, "", None, {}),
    6: ("red", .55, .2, "", GREEN, {}), 7: ("white", .65, .5, "", None, {}), 8: ("yellow", .6, .1, "", None, {}),
    9: ("red", .55, .15, "", None, {}), 10: ("orange", .55, .15, "", None, {}), 11: ("black", .4, .1, "", None, {}),
    12: ("white", .72, .1, "", None, {}), 13: ("pink", .6, .1, "", None, {}), 14: ("white", .7, .1, "", None, {}),
    15: ("pink", .62, .45, "", None, {}), 16: ("white", .7, .2, "", None, {}), 17: ("yellow", .62, .2, "", None, {}),
    18: ("pink", .66, .2, "", None, {}), 19: ("sky", .6, .2, "", None, {}), 20: ("green", .5, .3, "", None, {}),
    21: ("zinc", .58, .35, "v", None, {}), 22: ("zinc", .45, .3, "", None, {}),
    23: ("white", .55, .3, "uv", None, {"inlay": (hug_me() + O.heart(128, 226, 22), 2)}),
    24: ("wood", .5, .3, "", None, {"engrave": (["line 0,%d 256,%d" % (y, y) for y in range(0, 256, 64)], 3)}),
    25: ("hotpink", .58, .3, "v", None, {"inlay": (O.sparkles(25), 1)}), 26: ("pink", .78, .15, "", None, {}),
    27: ("wood", .35, .3, "", None, {}), 28: ("gold", .6, .5, "", None, {}), 29: ("steel", .6, .3, "v", None, {}),
    30: ("m_iron", .6, .4, "v", None, {}), 31: ("lilac", .6, .2, "", None, {}),
}
FUN_INLAY = {23: "red", 25: "white"}


def _rings(x, y):
    cx, cy = (x % 10) - 5, ((y + (5 if (x // 10) % 2 else 0)) % 10) - 5
    return (.35 if 2.2 < math.hypot(cx, cy) < 4.4 else -.3), None


def special(sheet, tag, u, v, x, y, g, n1):
    """Each tile's own shading (folds, glows, the Eye, frost, swirls); (value offset, fixed rgb)."""
    if sheet == "gear":
        if tag in (5, 16, 17):                     # cloth: folds; the war cloak darkens and frays at the hem
            fold = .16 * math.sin(u * 14 * math.pi) + .03 * math.sin(x * 2.1) * math.sin(y * 2.1)
            if tag == 16:                          # a turban's wrapped bands
                fold = .18 * math.sin((u * 3 + v * 9) * math.pi)
            return fold - .25 * max(0, .2 - v) / .2, None
        if tag == 3:                               # ember: hot core
            return .25 * math.exp(-((u - .5) ** 2 + (v - .5) ** 2) * 6), None
        if tag == 4:                               # the Eye: a lidless almond of fire, a black slit
            du, dv = (u - .5) * 2, (v - .5) * 2
            lid = 1 - abs(du) ** 1.6
            inside = abs(dv) < .62 * lid
            if inside:
                r = math.hypot(du * .8, dv * 1.4)
                slit = abs(du) < .1 * (1 - abs(dv) / .7)
                if slit:
                    return 0, ramp_colour(RAMPS["m_fire"], .12)
                return 0, ramp_colour(RAMPS["m_fire"], 1.0 - .45 * r + g * .3)
            return (.25 if abs(abs(dv) - .62 * lid) < .05 else 0), None
        if tag == 12:                              # a tine: blue iron frosting to rime at the tip
            f = max(0, min(1, (v - .45) / .4))
            iron = ramp_colour(RAMPS["a_iron"], .55 + g)
            ice = ramp_colour(RAMPS["a_ice"], .75 + g * .5 + .2 * (n1 - .5))
            return 0, [a * (1 - f) + b * f for a, b in zip(iron, ice)]
        if tag == 11:
            return .3 * (n1 - .5) + (.4 if (x * 7 + y * 13) % 97 == 0 else 0), None
        if tag == 13:                              # crimson paint chipped to iron
            if n1 > .72:
                return 0, ramp_colour(RAMPS["m_iron"], .55 + g)
            return 0, None
        if tag == 20:
            return _rings(x, y)
        if tag == 22:
            return .55 * (v - .5), None
        if tag == 24:
            return .25 * math.sin(x * .9 + 3 * math.sin(y * .15)) * n1, None
        if tag in (25, 3):
            return .2 * math.exp(-((v - .5) / .3) ** 2), None
        return 0, None
    if tag in (4, 2):                              # pink cloth, the top hat's band: folds
        return .14 * math.sin(u * 14 * math.pi), None
    if tag == 5:                                   # rainbow: a stripe per fold
        c = RAINBOW[min(6, int(u * 7))]
        k = 1 + .16 * math.sin(u * 14 * math.pi) * 1.6 + g
        return 0, [max(0, min(1, q * k)) for q in c]
    if tag == 6:                                   # party stripes and dots
        if ((u + v) * 5) % 1.0 < .3:
            return 0, ramp_colour(KR["white"], .7 + g * .3)
        return (.2 if math.hypot((x % 32) - 16, (y % 32) - 16) < 5 else 0), None
    if tag in (7, 28):                             # fluff
        return .3 * math.sin(x * 1.3 + 4 * math.sin(y * .23)) * n1, None
    if tag in (8, 3, 25):                          # rubber and glass: a gloss band
        return .35 * math.exp(-((v - .7) / .08) ** 2), None
    if tag == 13:                                  # the lollipop: a pink-and-white spiral, rainbow rim
        du, dv = u - .5, v - .5
        r, a = math.hypot(du, dv), math.atan2(dv, du)
        if r > .44:
            return 0, RAINBOW[int((a / (2 * math.pi) + .5) * 7) % 7]
        if ((a / (2 * math.pi)) * 2 + r * 9) % 1.0 < .5:
            return 0, ramp_colour(RAMPS["lilac"] if r < .2 else KR["hotpink"], .62 + g)
        return 0, ramp_colour(KR["white"], .8 + g * .2)
    if tag == 15:                                  # tulle: ruffles
        return .2 * math.sin(u * 40 * math.pi) * (.6 + .4 * n1) + .1 * math.sin(v * 9), None
    if tag in (16, 17, 18, 19, 31):                # petals: pale at the tip, a dark heart
        return .25 * v - .15 * max(0, .25 - v) / .25, None
    if tag == 21:                                  # galvanised: spangles and pressed ridges
        return .12 * math.sin(v * 9 * math.pi) + .08 * (n1 - .5), None
    return 0, None


def paint(work, gear, fun):
    """The class's two sheets and masks into `work` (gear and fun: sheet stems, lower case)."""
    work.joinpath("paint").mkdir(parents=True, exist_ok=True)
    return {gear: paint_sheet(work, gear, TILES, INLAY, "gear", special, ramps=RAMPS, fill={("gear", 9, "inlay")}, to=BLUE),
            fun: paint_sheet(work, fun, FUN_TILES, FUN_INLAY, "fun", special, ramps=RAMPS, fill={("fun", 23, "inlay")}, to=BLUE)}
