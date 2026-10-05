"""The CaH sheet painter: a 2048 x 1024 sheet of 8 x 4 tiles of 256 px and its 3-colour mask.

A tile is (ramp, mid, grain, edges, tint channel, {layer: (strokes, width)}): a palette ramp shaded
by seeded grain, scratches, worn bright edges ("u"/"v") and rim grime, with ornament strokes
(ornament.py) bevelled in as "inlay" (a ramp per tile, `inlay`), "engrave" or raised "rivet". A
class adds its own ramps and a special() for folds, rings, fluff and fixed colours.

The mask (512 x 256 TGA) follows EA's CaH masks (HC_CHDW_TM.tga): alpha marks what takes a
colour; R, G and B carry the shading for the colour each stands for. The CaH pickers drive Hair -> R,
Skin -> G, Paint -> B (docs/CAH.md "Hero colours"). A tile's tint says what kind of area it is (G
cloth and enamel, R leather and second cloth, B gems, PAINT tinted on CaH sheets only); the Create-a-
Hero sheets pass to=BLUE, so every tinted texel follows the Paint picker. The heroes' sheets
(assets/heroes) paint the same tables without `to`: R/G/B stay where they are, PAINT tiles and
"enamel" layers are left out, so their sheets do not change. Tiles with tint None, inlay over half
covered, and fixed colours stay as painted.
"""
import random

from assets.dwarves.style import PALETTE
from sagekit.units.paint import ramp_colour

from . import ornament as O

GREEN, RED, BLUE = 1, 0, 2
PAINT = 3                       # a tile tinted on the CaH sheets only (the Paint picker, B); untinted elsewhere
S = O.S
RAMPS = dict(PALETTE.ramps)
RAMPS.update({
    "steel": [(0, (.05, .06, .07)), (.4, (.28, .30, .33)), (.75, (.60, .63, .67)), (1, (.92, .94, .97))],
    "mithril": [(0, (.16, .18, .22)), (.35, (.46, .50, .57)), (.7, (.78, .83, .90)), (.9, (.93, .96, 1.0)), (1, (1, 1, 1))],
    "blacki": [(0, (.02, .02, .02)), (.5, (.09, .085, .08)), (.8, (.22, .21, .2)), (1, (.5, .48, .45))],
    "fur": [(0, (.08, .06, .05)), (.5, (.33, .27, .21)), (1, (.72, .64, .54))],
    "gem": [(0, (.02, .05, .16)), (.5, (.12, .30, .70)), (.85, (.45, .70, 1.0)), (1, (.9, .97, 1.0))],
    "horn": [(0, (.16, .12, .08)), (.4, (.42, .35, .26)), (.75, (.72, .65, .52)), (1, (.92, .88, .78))],
    "leather": [(0, (.06, .04, .03)), (.5, (.24, .15, .09)), (1, (.52, .36, .22))],
    "bluesteel": [(0, (.04, .06, .09)), (.45, (.22, .30, .40)), (.8, (.55, .64, .76)), (1, (.86, .92, 1.0))],
    "pink": [(0, (.22, .02, .10)), (.45, (.85, .20, .55)), (.8, (1, .55, .80)), (1, (1, .88, .95))],
    "hotpink": [(0, (.25, .0, .1)), (.4, (.78, .08, .45)), (.75, (1, .45, .75)), (.92, (1, .82, .93)), (1, (1, 1, 1))],
    "red": [(0, (.12, .01, .01)), (.5, (.70, .07, .05)), (1, (1, .55, .45))],
    "yellow": [(0, (.30, .20, .0)), (.5, (.95, .78, .10)), (.85, (1, .95, .55)), (1, (1, 1, .9))],
    "orange": [(0, (.30, .08, .0)), (.5, (.98, .45, .05)), (1, (1, .85, .55))],
    "black": [(0, (0, 0, 0)), (.7, (.05, .05, .06)), (1, (.45, .45, .5))],
    "white": [(0, (.55, .55, .58)), (.6, (.92, .92, .94)), (1, (1, 1, 1))],
    "scales": [(0, (.08, .14, .12)), (.45, (.38, .52, .46)), (.8, (.74, .82, .78)), (1, (.95, .98, .96))],
    "copper": [(0, (.12, .04, .02)), (.4, (.55, .22, .10)), (.75, (.86, .48, .28)), (1, (1, .82, .66))],
    # champleve enamel under the Paint colour (the mask carries the shading; the base shows in previews)
    "enamel": [(0, (.02, .04, .10)), (.45, (.08, .16, .38)), (.8, (.20, .32, .62)), (1, (.45, .58, .85))],
})

def paint_sheet(work, name, tiles, inlay, sheet, special, ramps=None, fill=(), to=None, enamel=None):
    """Paint sheet `name` (tiles {tag: spec}) into `work`: its DDS and its mask TGA. special(sheet,
    tag, u, v, x, y, g, n1) -> (value offset, fixed rgb or None) adds a tile's own shading; a fixed
    rgb is never tinted. fill: (sheet, tag, layer) whose strokes are filled shapes.
    to: the one mask channel every tint goes to (CaH sheets: BLUE, the Paint picker); it also turns
    on PAINT tiles and the "enamel" layer (filled shapes of tinted enamel, ramp enamel.get(tag,
    "enamel"), under the engraving, inlay and rivets). Without it both are left out."""
    R = dict(RAMPS, **(ramps or {}))
    W, H = 8 * S, 4 * S
    rgb = bytearray(W * H * 3)
    mask = bytearray((W // 4) * (H // 4) * 4)
    n1, n2 = O.noise(work, 3, 1.5), O.noise(work, 11, 6)
    scr = O.scratches(work, 5)
    rng = random.Random(7)
    for tag, (ramp, mid, grain, edges, tint, orns) in tiles.items():
        if to is None:
            tint = None if tint == PAINT else tint
            orns = {k: v for k, v in orns.items() if k != "enamel"}
        elif tint is not None:
            tint = to
        layers = {k: O.draw(work, "%s%d_%s" % (sheet, tag, k), c, width=w,
                            fill=(k in ("rivet", "enamel") or (sheet, tag, k) in fill))
                  for k, (c, w) in orns.items()}
        ox, oy = (tag % 8) * S, (tag // 8) * S
        for y in range(S):
            v = 1 - y / (S - 1)
            for x in range(S):
                u = x / (S - 1)
                i = y * S + x
                g = (n1[i] / 255 - .5) * grain + (n2[i] / 255 - .5) * grain * .35
                extra, fixed = special(sheet, tag, u, v, x, y, g, n1[i] / 255)
                val = mid + g + extra
                e = 0.0
                if "v" in edges:
                    e = max(e, max(0, .06 - v) / .06, max(0, v - .94) / .06 * .6)
                if "u" in edges:
                    e = max(e, max(0, .05 - u) / .05, max(0, u - .95) / .05)
                val += .28 * e - (.12 * max(0, .25 - v) if "v" in edges else 0)
                if ramp not in ("cloth", "ground", "fur", "gem", "pink", "white", "red", "yellow"):
                    val += .12 * scr[i] / 255
                col = fixed or ramp_colour(R[ramp], val + rng.uniform(-.015, .015))
                ch = tint
                if "enamel" in layers:
                    m0 = layers["enamel"][i] / 255
                    if m0 > .05 and not fixed:
                        en = ramp_colour(R[(enamel or {}).get(tag, "enamel")], .55 + g * .6 + .1 * (n1[i] / 255 - .5))
                        col = [a * (1 - m0) + b * m0 for a, b in zip(col, en)]
                        ch = to if m0 > .5 else ch
                if "engrave" in layers:
                    m0 = layers["engrave"][i] / 255
                    m1 = layers["engrave"][min(i + S + 1, S * S - 1)] / 255
                    col = [c * (1 - .55 * m0) + .25 * max(0, m1 - m0) for c in col]
                if "inlay" in layers:
                    m0 = layers["inlay"][i] / 255
                    if m0 > .05:
                        m1 = layers["inlay"][max(i - S - 1, 0)] / 255
                        gold = ramp_colour(R[inlay.get(tag, "gold")], .62 + .3 * (m0 - m1) + g * .5)
                        col = [a * (1 - m0) + b * m0 for a, b in zip(col, gold)]
                        ch = None if m0 > .5 else ch
                if "rivet" in layers:
                    m0 = layers["rivet"][i] / 255
                    if m0 > .05:
                        m1 = layers["rivet"][max(i - 2 * S - 2, 0)] / 255
                        riv = ramp_colour(R["steel" if ramp == "blacki" else "bronze"], .55 + .45 * (m0 - m1))
                        col = [a * (1 - m0) + b * m0 for a, b in zip(col, riv)]
                o = ((oy + y) * W + ox + x) * 3
                rgb[o:o + 3] = bytes(max(0, min(255, round(255 * c))) for c in col)
                if ch is not None and x % 4 == 0 and y % 4 == 0 and not fixed:
                    lum = .3 * col[0] + .59 * col[1] + .11 * col[2]
                    mo = (((oy + y) // 4) * (W // 4) + (ox + x) // 4) * 4
                    mask[mo + ch] = max(0, min(255, round(255 * min(1, .35 + lum * 2.2))))
                    mask[mo + 3] = 255
    (work / (name + ".rgb")).write_bytes(bytes(rgb))
    (work / (name + "_mask.rgba")).write_bytes(bytes(mask))
    png, tga = work / (name + ".png"), work / ("hc_" + name + ".tga")
    O.magick("-size", "%dx%d" % (W, H), "-depth", "8", "rgb:" + str(work / (name + ".rgb")), png)
    O.magick("-size", "%dx%d" % (W // 4, H // 4), "-depth", "8", "rgba:" + str(work / (name + "_mask.rgba")), tga)
    from sagekit.formats.textures import write_dds
    write_dds(str(png), str(work / (name + ".dds")))
    return work / (name + ".dds"), tga
