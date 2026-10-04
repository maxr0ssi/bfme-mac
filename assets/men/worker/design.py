"""Gondor mason's labourer: the Men's construction worker in the stone-mason's colours.

GUWorker_SKN (GondorWorker and ArnorWorker, and the neutral and civilian sites that call Gondor
workers) is EA's low-detail BFME man on a 64-pixel sheet. The sheet is painted at 256 pixels in
Gondor sable; his coat keeps EA's house mask (a darker player colour on sable wool). Over it he
wears a short livery tabard in bright player colour with the White Tree, and a dark tool belt with
a steel buckle, a pouch and a chisel, like the builder's. EA's mesh, skeleton
and animations are kept; every piece follows one of EA's bones.
python3 -m sagekit unit men/worker --render (docs/UNITS.md).
"""
import math
import random

from assets.men.porter.design import CROPS, DARK, GOLD, LEATHER, STEEL, SWATCHES, TIMBER, ramp, white_tree
from sagekit.units import Unit, View
from sagekit.units.cloth import HC, check_patch, drape, patch_uv
from sagekit.units.paint import crop_rgb, magick, raw

# EA's coat (HC_GUWorker tints it), 64-pixel grid, in the atlas' unused top-left tile.
HC_BOX = (11, 6, 20, 40)
RIBS, PELVIS = "BAT_RIBS", "ROOT DUMMY"
SKIN = [(36, 38, 64, 64), (39, 20, 51, 38)]     # the face and the bare forearms: never recoloured
CX = -.84                                       # the body's front-back centre at the waist


def front_row(z, x, half=1.55, cols=7):
    return [(x - .14 * y * y, -half + 2 * half * i / (cols - 1), z) for i in range(cols)
            for y in [-half + 2 * half * i / (cols - 1)]]


def back_row(z, x, half=1.65, cols=7):
    return [(x + .14 * y * y, -half + 2 * half * i / (cols - 1), z) for i in range(cols)
            for y in [-half + 2 * half * i / (cols - 1)]]


def tabard(m):
    """Front and back panels from the collar to the hips (the hem on the pelvis), shoulder straps."""
    front = [(RIBS, front_row(16.7, .75, 1.3)), (RIBS, front_row(15.0, 1.12, 1.8)), (RIBS, front_row(12.6, 1.32, 1.85)),
             (PELVIS, front_row(10.4, 1.55, 1.9)), (PELVIS, front_row(9.2, 1.62, 1.95))]
    back = [(RIBS, back_row(16.7, -2.8, 1.3)), (RIBS, back_row(14.5, -3.0)), (RIBS, back_row(12.3, -3.15)),
            (PELVIS, back_row(10.4, -3.22)), (PELVIS, back_row(9.2, -3.28))]
    drape(m, front, HC, depth=-.1)
    drape(m, back, HC, depth=.1)
    for s in (-1, 1):                                   # straps over the shoulders
        strap = [(RIBS, [(.75 - .14 * 1.44, s * 1.0, 16.7), (.75 - .14 * 1.44, s * 1.75, 16.7)]),
                 (RIBS, [(-1.0, s * 1.0, 17.35), (-1.0, s * 1.75, 17.3)]),
                 (RIBS, [(-2.8 + .14 * 1.69, s * 1.0, 16.7), (-2.8 + .14 * 1.69, s * 1.75, 16.7)])]
        drape(m, strap, HC, depth=0, axis=2)
        drape(m, strap, HC, depth=-.1, axis=2)
    for row, bone, r in [(front_row(9.25, 1.67, 1.95), PELVIS, .07), (back_row(9.25, -3.34), PELVIS, .07)]:
        for a, b in zip(row, row[1:]):                  # steel-weighted hems
            m.tube(a, b, r, STEEL, bone, sides=5)
    # The White Tree on the front panel, white on the player colour, raised off the cloth.
    def at(u, v, d=0):
        z = 13.0 + v
        x = 1.32 + (1.55 - 1.32) * (12.6 - z) / 2.2 if z < 12.6 else 1.12 + .2 * (15.0 - z) / 2.4
        return (x + .06 + d - .14 * u * u, u, z)
    white_tree(m, at, .62, RIBS, stars=(-1, 0, 1))


def toolbelt(m):
    n, pts = 20, []
    for i in range(n + 1):
        a = i * math.tau / n
        pts.append((CX + 2.42 * math.cos(a), 2.62 * math.sin(a)))
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        m.face([(ax, ay, 10.55), (bx, by, 10.55), (bx, by, 11.25), (ax, ay, 11.25)], DARK, PELVIS)
        m.face([(ax, ay, 11.25), (bx, by, 11.25), (bx, by, 10.55), (ax, ay, 10.55)], DARK, PELVIS)
    m.box((1.52, -.4, 10.45), (1.68, .4, 11.35), STEEL, PELVIS)          # buckle
    m.box((-1.4, 2.35, 9.2), (.1, 2.85, 10.7), LEATHER, PELVIS)          # pouch on the left hip
    m.box((-1.48, 2.3, 10.25), (.18, 2.9, 10.75), DARK, PELVIS)
    m.box((-.9, -2.95, 9.9), (-.4, -2.7, 11.1), DARK, PELVIS)            # chisel loop, right hip
    m.tube((-.65, -3.0, 8.6), (-.65, -3.0, 10.2), .08, STEEL, PELVIS, sides=5)
    m.tube((-.65, -3.0, 10.2), (-.65, -3.0, 11.2), .16, TIMBER, PELVIS, sides=6)
    m.tube((CX + .2, 0, 17.35), (CX + .2, 0, 17.55), .05, GOLD, RIBS, sides=4)


class Worker(Unit):
    """GondorWorker and ArnorWorker (and their children) draw GUWorker_SKN: in place."""
    model, skeleton = "GUWorker_SKN", "GUWorker_SKL"
    anims = ("idla", "wlka", "wrka", "wrkb", "diea")
    expected = {"guworker_skn": "96749021d716e9c3019b255a856e1839e3b6245ab2684cd9098fbcbda57d3752",
                "guworker_skl": "60ca370dfc46ddfafdc8878ec312d43e909ce1267b342209a45d28610501fc1f"}
    textures = {"GUWorker.tga": "GUWrkCr.tga"}
    house = {"GUWrkCr.tga": "HC_GUWrkCr.tga"}
    mask = ("HC_GUWorker.tga", "HC_GUWrkCr.tga")
    mask_source = "art\\compiledtextures\\hc\\hc_guworker.png"     # EA ships it as PNG and JPG only
    mask_scale = 256                                                # the 64-pixel sheet painted at 256
    sources = ("GUPorter.tga", "GUPorter_Cart.tga", "GUPorter_Build.tga")   # the builder's grain
    archive = "!!!!!!!!!!!!sagekit-men-worker.big"
    bone = RIBS
    smooth = ("RUSAM01",)
    views = {"portrait": View("idla", 0, elevation=18, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.6),
             "back": View("wlka", 8, elevation=26, azimuth=150, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.6),
             "rear": View("idla", 0, elevation=20, azimuth=180, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.6),
             "work": View("wrkb", 30, elevation=24, azimuth=-120, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.6),
             "rts": View("idla", 0, elevation=52, size=(520, 420), fit=True, fit_min=170, fit_scale=1),
             "death": View("diea", 30, elevation=40, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.6)}
    labels = ("EA'S MEN WORKER", "GONDOR MASON'S LABOURER - REVIEW")

    def design(self, w, sk):
        man = self.mesh(w, sk, "RUSAM01", keep=True)
        man.uv_for = patch_uv(HC_BOX, sheet=64)
        tabard(man)
        toolbelt(man)
        return {"RUSAM01": man}

    def check(self, b, original, new, sk):
        check_patch(b.src / self.mask[0].lower(), HC_BOX)

    def paint(self, b):
        work = b.work
        # Left half: EA's sheet at 256 pixels in Gondor sable, the coat (EA's mask: it still takes
        # a darker player colour) a lighter wool; the bare skin keeps EA's paint. The unused
        # top-left tile keeps EA's light coat for the tabard, which takes the player colour bright.
        magick(b.src / "guworker.dds", "-alpha", "off", "-filter", "Lanczos", "-resize", "256x256!",
               "-unsharp", "0x1", "-depth", "8", "rgb:" + str(work / "sheet.rgb"))
        sheet = bytearray((work / "sheet.rgb").read_bytes())
        mask = raw(b.src / self.mask[0].lower())
        body = bytearray(sheet)
        for y in range(256):
            for x in range(256):
                if any(x0 * 4 <= x < x1 * 4 and y0 * 4 <= y < y1 * 4 for x0, y0, x1, y1 in SKIN):
                    continue
                i = (y * 256 + x) * 3
                lum = sum(sheet[i:i + 3]) / 765
                coat = mask[((y // 4) * 64 + x // 4) * 4 + 3] / 255      # wool coat: a lighter sable
                sable = ramp("enamel", .14 + lum * (.75 + .35 * coat))
                body[i:i + 3] = bytes(round(255 * c * .85 + o * .15) for c, o in zip(sable, sheet[i:i + 3]))
        (work / "body.ppm").write_bytes(b"P6\n256 256\n255\n" + bytes(body))
        (work / "corner.ppm").write_bytes(b"P6\n256 256\n255\n" + bytes(sheet))
        samples = []
        for i, (source, box) in enumerate(CROPS):
            data = crop_rgb(b.src / (source + ".dds"), box, work / ("grain_%d.rgb" % i))
            samples.append((data, sum(data) / len(data) / 255))
        rng, pixels = random.Random(41), bytearray()
        for y in range(1024):
            for x in range(1024):
                tag = (y // 256) * 4 + x // 256
                material, mid, src = SWATCHES[tag]
                u, v = x % 256, y % 256
                data, mean = samples[src]
                lum = sum(data[(v * 256 + u) * 3:(v * 256 + u) * 3 + 3]) / 765
                edge = min(u, v, 255 - u, 255 - v)
                value = mid + (lum - mean) * (.9 if material == "wood" else .8 if material == "stone" else .45) \
                    + rng.uniform(-.02, .02) + (.08 if edge < 5 else -.05 if edge < 9 else 0)
                pixels.extend(round(255 * c) for c in ramp(material, value))
        (work / "materials.ppm").write_bytes(b"P6\n1024 1024\n255\n" + pixels)
        atlas = work / "guwrkcr.png"
        magick("-size", "1024x1024", "tile:" + str(work / "body.ppm"), work / "corner.ppm", "-geometry", "+0+0",
               "-composite", work / "materials.ppm", "+append", atlas)
        return atlas
