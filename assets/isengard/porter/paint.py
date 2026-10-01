"""The Isengard builder's atlas (2048 x 1024): EA's orc re-dyed, the swatches, the house-colour cloth.

Left half: EA's MUOrcPorter sheet tiled 4 x 4 (mesh.keep_uv), its maroon robe dyed charcoal, the
apron darkened to leather; tile 0 also holds the light cloth under the
house-colour patch (kit.HOUSE_BOX). Right half: 16 swatches from palette A's ramps, grain from EA's
own painted planks (sagekit/units/paint.py).
"""
import math
import random

from assets.isengard.style import PALETTE
from sagekit.units.paint import crop_rgb, magick, ramp_colour

from .kit import HOUSE_BOX

R = PALETTE.ramps
# (ramp, mid, finish) per swatch tag, in design.py's order
SWATCHES = [("wood", .56, "plank"), ("wood", .62, "bark"), ("iron", .56, "rivet"), ("silver", .56, "brushed"),
            ("wood", .80, "rings"), ("wood", .28, "smooth"), ("mark", .9, "smooth"), ("silver", .5, "brushed"),
            ("silver", .36, "cast"), ("iron", .84, "cast"), ("stone", .42, "smooth"), ("wood", .36, "plank"),
            ("iron", .46, "rivet"), ("iron", .46, "rivet"), ("iron", .46, "rivet"), ("iron", .46, "rivet")]


def lerp(a, b, t):
    return [x * (1 - t) + y * t for x, y in zip(a, b)]


def dye_orc(src, work):
    """EA's orc sheet with the robe charcoal and the apron dark leather; returns its path. (No emblem:
    the sheet's apron is mirrored across the chest, so a painted White Hand shows twice.)"""
    magick(src / "muorcporter.dds", "-alpha", "off", "-depth", "8", "rgb:" + str(work / "orc.rgb"))
    px = bytearray((work / "orc.rgb").read_bytes())
    for y in range(256):
        for x in range(256):
            i = (y * 256 + x) * 3
            r, g, b = px[i:i + 3]
            lum = (r + g + b) / 765
            if r > g + 6 and b >= g - 3:                                    # the maroon robe and rags
                c = ramp_colour(R["iron"], .12 + lum * 1.2)
            elif x < 80 and 52 < y < 190:                                  # the apron
                c = lerp(ramp_colour(R["wood"], .12 + lum * .75), ramp_colour(R["iron"], .2 + lum), .35)
            else:
                continue
            px[i:i + 3] = bytes(round(255 * v) for v in c)
    (work / "orc.ppm").write_bytes(b"P6\n256 256\n255\n" + px)
    return work / "orc.ppm"


def swatches(b):
    """The right half: 16 tiles of 256 px, painted from the palette with grain."""
    plank = crop_rgb(b.src / "guporter_cart.dds", (40, 40, 220, 118), b.work / "grain_plank.rgb")
    rng = random.Random(41)
    px = bytearray()
    for y in range(1024):
        for x in range(1024):
            tag = (y // 256) * 4 + x // 256
            ramp, mid, finish = SWATCHES[tag]
            u, v = x % 256, y % 256
            edge = min(u, v, 255 - u, 255 - v) / 255
            noise = rng.uniform(-.03, .03)
            value, colour = mid + noise, None
            if finish == "plank":
                i = (v * 256 + u) * 3
                value += (sum(plank[i:i + 3]) / 765 - .4) * .9 - (.12 if edge < .02 else 0)
            elif finish == "bark":
                furrow = math.sin(u * .32 + 2.2 * math.sin(v * .021 + u * .05))
                value += .16 * furrow - (.14 if furrow < -.55 else 0)
            elif finish == "rings":
                d = math.hypot(u - 128, v - 128) / 128
                value += .07 * math.sin(d * 42) - .25 * max(0, d - .82) * 4 - .1 * d
                crack = abs(math.atan2(v - 128, u - 128) - .6) < .025 and d > .25
                value -= .3 if crack else 0
                colour = lerp(ramp_colour(R["wood"], value), ramp_colour(R["rock"], value * .85), .35)
            elif finish == "brushed":
                value += .05 * math.sin(v * 1.7 + math.sin(u * .05) * 3) + (.14 if edge < .02 else 0)
            elif finish in ("rivet", "cast"):
                value += (.18 if edge < .02 else -.08 if edge < .035 else 0)
                if finish == "rivet" and min(abs(u - 22), abs(u - 234), abs(v - 22), abs(v - 234)) < 8:
                    # round rivet heads along the plate's edges, lit on top
                    side = lambda t: 22 if t < 128 else 234                       # noqa: E731
                    grid = lambda t: min(234, round((t - 22) / 53) * 53 + 22)     # noqa: E731
                    for a, c in ((side(u), grid(v)), (grid(u), side(v))):
                        d = math.hypot(u - a, v - c)
                        if d < 7:
                            value = mid + .34 - d * .03 - (.1 if v > c + 2 else 0)
            if colour is None:
                colour = ramp_colour(R[ramp], value)
            if ramp == "wood" and finish == "bark":
                colour = lerp(colour, ramp_colour(R["leaf"], value * .8), .22)
            px.extend(round(255 * c) for c in colour)
    path = b.work / "materials.ppm"
    path.write_bytes(b"P6\n1024 1024\n255\n" + px)
    return path


def house_cloth(work):
    """The light woven cloth under the house-colour patch (tile 0 of the left half)."""
    x0, y0, x1, y1 = HOUSE_BOX
    w, h = x1 - x0 + 12, y1 - y0 + 12
    rng = random.Random(5)
    px = bytearray()
    for y in range(h):
        for x in range(w):
            weave = .04 * ((x + y) % 2) + rng.uniform(-.03, .03)
            px.extend(round(255 * c) for c in ramp_colour(R["mark"], .18 + weave))
    path = work / "house_cloth.ppm"
    path.write_bytes(b"P6\n%d %d\n255\n" % (w, h) + px)
    return path, x0 - 6, y0 - 6


def atlas(b):
    orc = dye_orc(b.src, b.work)
    cloth, cx, cy = house_cloth(b.work)
    out = b.work / "iucrafts.png"
    magick("-size", "1024x1024", "tile:" + str(orc), cloth, "-geometry", "+%d+%d" % (cx, cy), "-composite",
           swatches(b), "+append", out)
    return out
