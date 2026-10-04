"""EA's orc labourer (MUOrcLabor_SKN) as the base of each evil faction's construction worker.

Mordor's MordorWorker, the Goblins' WildLaborer and Angmar's AngmarWorker all draw this one model
(Isengard's buildings call MordorWorkerNoSelect). Each faction's worker recipe subclasses
`Labourer`: it ships EA's orc under a model name of its own (`own_model`) and repoints its own
worker object's Draw to it (`objects`), so every faction keeps its own look. EA's body, skeleton,
skin weights, animations and LOG are kept; the body takes the faction's dye on a private sheet and
its gear (`gear`); the HAMMER and AXE (rigid sub-objects the INI shows and hides by name) are
rebuilt in the faction's style on their own bones, along EA's grip lines.

Measured off EA's rest pose (the orc faces +x, hunched): head on BAT_HEAD, crown z 20.4, face
x 1.8; NECK the opening (-0.95, 0, 16.15) rising 0.6 at the sides; SHOULDER the cap (-1.0, +-3.0,
15.9) sloping to z 15.1 at y +-3.7; ELBOW and WRIST on the forearm; hands (0, +-6.8, 9.4); waist
z 11, front x 1.9, back x -2.05, sides y +-2.2. The sheet (256 px): apron x 0-75 y 40-180 and belt band
x 75-152 y 98-123 (EA's house mask: player colour); dark fur FUR; skin x 152-256 y 0-150 and the
face below it; mail x 0-64 y 210-256; rust x 64-152 y 210-256.
"""
import math
import random

from . import Unit, View
from .cloth import check_patch, patch_uv
from .paint import crop_rgb, magick, ramp_bytes, raw

HC_BOX = (18, 66, 62, 170)                   # EA's apron, fully under the mask
FUR = [(55, 0, 152, 98), (75, 123, 152, 210), (0, 180, 75, 210), (196, 0, 256, 150)]
MAIL, RUST = (0, 210, 64, 256), (64, 210, 152, 256)
PELVIS, SPINE, HEAD = "BAT_PELVIS", "BAT_SPINE2", "BAT_HEAD"
NECK, SHOULDER = (-.95, 0, 16.15), (-1.0, 3.0, 15.9)           # SHOULDER: the left (+y) one
ELBOW, WRIST = (-1.2, 5.25, 12.0), (-.1, 6.85, 9.35)           # the left forearm's axis
HAMMER_GRIP = ((-1.6, -7.45, 7.95), (3.75, -6.85, 9.05))     # EA's haft, butt to head
HAMMER_HEAD = ((3.55, -5.25, 11.05), (4.35, -8.45, 8.2))      # EA's head axis, top face to bottom
AXE_GRIP = ((-2.08, -7.45, 7.75), (5.86, -6.9, 9.6))
AXE_BLADE = [(5.92, -5.96, 11.25), (7.36, -7.53, 9.12), (7.23, -9.32, 6.66), (2.88, -9.68, 5.47),
             (5.35, -8.3, 7.85)]                               # EA's blade outline

# Swatch tags (the atlas' right half); each faction maps them to its ramps in SWATCHES.
IRON, DARK, STEEL, LEATHER, WOOD, BONE, TRIM, CLOTH, GLOW, ACCENT, HIDE, ROPE = range(12)


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def spike(m, base, tip, r, tag, bone=None, sides=5):
    m.tube(base, tip, r, tag, bone, sides=sides, r1=r * .08)


def ring(m, centre, rx, ry, r, tag, bone=None, n=16, saddle=0):
    """A tube ring about a vertical axis (collars, belts, crowns); saddle lifts its sides (a
    neck's opening is higher at the shoulders than at the throat and nape)."""
    cx, cy, cz = centre
    pts = [(cx + rx * math.cos(i * math.tau / n), cy + ry * math.sin(i * math.tau / n),
            cz + saddle * math.sin(i * math.tau / n) ** 2) for i in range(n + 1)]
    for a, b in zip(pts, pts[1:]):
        m.tube(a, b, r, tag, bone, sides=6)
    return pts[:-1]


def slab(m, outline, thick, tag, bone=None):
    """A flat polygon (any convex outline, roughly planar) given thickness: blades, plates."""
    n = len(outline)
    c = [sum(p[k] for p in outline) / n for k in range(3)]
    a, b = [outline[1][k] - outline[0][k] for k in range(3)], [outline[2][k] - outline[0][k] for k in range(3)]
    nrm = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    ln = math.sqrt(sum(x * x for x in nrm)) or 1
    off = [x / ln * thick / 2 for x in nrm]
    top = [tuple(p[k] + off[k] for k in range(3)) for p in outline]
    bot = [tuple(p[k] - off[k] for k in range(3)) for p in outline]
    for i in range(n):
        j = (i + 1) % n
        m.face([tuple(c[k] + off[k] for k in range(3)), top[i], top[j]], tag, bone)
        m.face([tuple(c[k] - off[k] for k in range(3)), bot[j], bot[i]], tag, bone)
        m.face([top[j], top[i], bot[i], bot[j]], tag, bone)


def haft(m, grip, tag, r=.2, cap=None):
    """EA's grip line as a haft, a little past both ends; an optional pommel cap."""
    a, b = lerp(grip[1], grip[0], 1.04), lerp(grip[0], grip[1], 1.02)
    m.tube(a, b, r, tag, sides=7)
    if cap is not None:
        m.tube(a, lerp(a, b, .05), r * 1.5, cap, sides=7)


class Labourer(Unit):
    """EA's orc labourer; a faction's recipe sets own_model, objects, textures, house, mask[1],
    archive, labels, SWATCHES, DYE, palette, and draws gear / hammer / axe."""
    model, skeleton, anim_family = "MUOrcLabor_SKN", "MUGblnSlv_SKL", "MUOrcLabor"
    anims = ("idla", "idlb", "runa", "wrka", "wrkl", "diea")
    expected = {"muorclabor_skn": "8874c5897f1c9f4f747c572c6ac83e6cce41151cf34070da6b172a748271356c",
                "mugblnslv_skl": "962c0119c1cf08b66ce4e48a1d878bf2638308e188557d4927877cd1c920793a"}
    bone = SPINE
    smooth = ("MUGBLNSLV1",)
    views = {"portrait": View("idla", 0, elevation=18, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.5),
             "back": View("runa", 8, elevation=26, azimuth=150, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.5),
             "rear": View("idla", 0, elevation=20, azimuth=180, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.5),
             "work": View("wrka", 18, elevation=24, azimuth=-120, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.5),
             "rts": View("idla", 0, elevation=52, size=(520, 420), fit=True, fit_min=170, fit_scale=1),
             "death": View("diea", 40, elevation=40, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.5)}
    palette = None              # the faction's Palette
    DYE = None                  # ramp stops the dark fur is dyed with
    MAIL_DYE = None             # ramp for the mail and rust patches (None: EA's)
    SWATCHES = ()               # 16 x (ramp name, middle value)
    SEED = 7

    # ---------------------------------------------------------------- the faction's part
    def gear(self, body):
        """Pieces on the body (a skin: any bone)."""

    def hammer(self, m):
        """The HAMMER sub-object (rigid on its bone): shown while the orc builds."""

    def axe(self, m):
        """The AXE sub-object (rigid on its bone): shown while he idles, runs and chops."""

    # ---------------------------------------------------------------- shared
    def design(self, w, sk):
        meshes = {"MUGBLNSLV1": self.mesh(w, sk, "MUGBLNSLV1", keep=True),
                  "HAMMER": self.mesh(w, sk, "HAMMER"), "AXE": self.mesh(w, sk, "AXE")}
        for m in meshes.values():
            m.uv_for = patch_uv(HC_BOX)
        self.gear(meshes["MUGBLNSLV1"])
        self.hammer(meshes["HAMMER"])
        self.axe(meshes["AXE"])
        return meshes

    def check(self, b, original, new, sk):
        assert new.meshes["LOG"].bytes == original.meshes["LOG"].bytes, "LOG"
        check_patch(b.src / self.mask[0].lower(), HC_BOX)

    def ramp(self, name):
        return self.palette.ramps[name]

    def paint(self, b):
        work = b.work
        magick(b.src / "muorclabor.dds", "-alpha", "off", "-depth", "8", "rgb:" + str(work / "orc.rgb"))
        orc = bytearray((work / "orc.rgb").read_bytes())
        mask = raw(b.src / self.mask[0].lower())
        regions = [(r, self.DYE) for r in FUR] + ([(MAIL, self.MAIL_DYE), (RUST, self.MAIL_DYE)] if self.MAIL_DYE else [])
        for (x0, y0, x1, y1), stops in regions:
            for y in range(y0, y1):
                for x in range(x0, x1):
                    if mask[(y * 256 + x) * 4 + 3]:
                        continue                                    # EA's player colour stays EA's
                    i = (y * 256 + x) * 3
                    orc[i:i + 3] = ramp_bytes(stops, .06 + sum(orc[i:i + 3]) / 765 * 1.3)
        (work / "orc.ppm").write_bytes(b"P6\n256 256\n255\n" + bytes(orc))
        (work / "corner.ppm").write_bytes(b"P6\n256 256\n255\n" + (work / "orc.rgb").read_bytes())
        # Grain for the swatches: EA's own fur, mail and leather, about their means.
        grains = []
        for k, box in enumerate([(60, 10, 150, 90), MAIL, (5, 70, 70, 170), RUST]):
            g = crop_rgb(b.src / "muorclabor.dds", box, work / ("grain_%d.rgb" % k))
            grains.append((g, sum(g) / len(g) / 255))
        which = [1, 0, 1, 2, 2, 3, 1, 0, 3, 2, 0, 2, 1, 0, 2, 3]
        rng, pixels = random.Random(self.SEED), bytearray()
        for y in range(1024):
            for x in range(1024):
                tag = (y // 256) * 4 + x // 256
                name, mid = self.SWATCHES[tag]
                data, mean = grains[which[tag]]
                u, v = x % 256, y % 256
                o = (v * 256 + u) * 3
                edge = min(u, v, 255 - u, 255 - v)
                value = mid + (sum(data[o:o + 3]) / 765 - mean) * .55 + rng.uniform(-.02, .02) \
                    + (.07 if edge < 5 else -.05 if edge < 9 else 0)
                pixels += ramp_bytes(self.ramp(name), value)
        (work / "materials.ppm").write_bytes(b"P6\n1024 1024\n255\n" + pixels)
        atlas = work / "labourer.png"
        # Left half: the dyed orc 4 x 4; the unused top-left tile keeps EA's apron for the HC cloth.
        magick("-size", "1024x1024", "tile:" + str(work / "orc.ppm"), work / "corner.ppm", "-geometry", "+0+0",
               "-composite", work / "materials.ppm", "+append", atlas)
        return atlas
