"""Lórien journeyman: the Elven construction worker in the master craftsman's colours.

EUWorker_SKN is the builder's Elf (the porter draws the same sheet), so the crew shares the
builder's ivory tunic and green wrap, on the builder's own atlas paint. The worker adds a long
cloak in player colour pinned by two gold mallorn leaves, a mithril circlet with a gold leaf, and
a silver belt with a gold buckle. EA's Elf, hammer, skeleton (GUWorker_SKL, shared with the Men's
worker) and animations are kept; every piece follows one of EA's bones.
python3 -m sagekit unit elves/worker --render (docs/UNITS.md).
"""
import math

from assets.elves.porter.design import GOLD, SILVER, Porter, leaf
from sagekit.units import Unit, View
from sagekit.units.cloth import HC, check_patch, drape, patch_uv

# EA's coat (HC_EUWorker tints it) in the atlas' unused top-left tile; the builder's paint makes it
# ivory there, as on the body, so the cloak takes the player colour exactly as the tunic does.
HC_BOX = (52, 36, 96, 50)    # a plain stretch of the wrap, below the embroidered collar
RIBS, PELVIS, HEAD = "BAT_RIBS", "ROOT DUMMY", "BAT_HEAD"


def cloak_row(z, half, lift, fold, cols=11):
    """A row across the back's curve (x = -1.9 + 0.1 y^2, off EA's Elf), `lift` behind it, with
    folds deepening toward the hem."""
    out = []
    for i in range(cols):
        y = -half + 2 * half * i / (cols - 1)
        out.append((-1.92 + .1 * y * y - lift - fold * (.5 + .5 * math.cos(y * math.pi / .8)), y, z))
    return out


def cloak(m):
    """From the shoulders to the backs of the knees; the hem half follows the pelvis."""
    rows = [(RIBS, cloak_row(17.1, 1.45, .02, 0)), (RIBS, cloak_row(15.6, 1.7, .08, .08)),
            (RIBS, cloak_row(13.2, 1.95, .16, .18)), (PELVIS, cloak_row(10.8, 2.15, .3, .28)),
            (PELVIS, cloak_row(8.0, 2.45, .5, .36))]
    drape(m, rows, HC, depth=.12)
    hem = cloak_row(8.05, 2.45, .58, .36)
    for a, b in zip(hem, hem[1:]):                                      # silver-weighted hem
        m.tube(a, b, .07, SILVER, PELVIS, sides=6)
    for s in (-1, 1):                                                   # cords over the shoulders
        m.tube((-1.75, s * 1.4, 17.15), (.2, s * 1.55, 17.25), .09, SILVER, RIBS, sides=6)
        m.tube((.2, s * 1.55, 17.25), (1.0, s * 1.3, 16.55), .09, SILVER, RIBS, sides=6)
        leaf(m, (1.12, s * 1.3, 16.25), .62, 1.0, GOLD, RIBS)            # mallorn-leaf clasps


def ring(m, centre, rx, ry, r, tag, bone, n=16):
    cx, cy, cz = centre
    pts = [(cx + rx * math.cos(i * math.tau / n), cy + ry * math.sin(i * math.tau / n), cz) for i in range(n + 1)]
    for a, b in zip(pts, pts[1:]):
        m.tube(a, b, r, tag, bone, sides=6)


def circlet(m):
    ring(m, (.05, 0, 19.95), 1.5, 1.2, .09, SILVER, HEAD)
    leaf(m, (1.58, 0, 19.9), .42, .7, GOLD, HEAD)


def belt(m):
    ring(m, (.15, 0, 11.35), 1.95, 2.55, .14, SILVER, PELVIS, n=20)
    m.box((1.98, -.42, 10.95), (2.18, .42, 11.75), GOLD, PELVIS)


class Worker(Unit):
    """ElvenWorker (and its NoSelect, Farm and Fortress children) draws EUWorker_SKN: in place."""
    model, skeleton = "EUWorker_SKN", "GUWorker_SKL"
    anims = ("idla", "wlka", "wrka", "wrkb", "diea")
    expected = {"euworker_skn": "e2e35779299c8a15bdc7ff5d650be279eb0c05e75fea57d57a8e8420d4b384c7",
                "guworker_skl": "60ca370dfc46ddfafdc8878ec312d43e909ce1267b342209a45d28610501fc1f"}
    textures = {"euworker.tga": "EUWorkCr.tga"}
    house = {"EUWorkCr.tga": "HC_EUWorkCr.tga"}
    mask = ("HC_EUWorker.tga", "HC_EUWorkCr.tga")
    sources = ("GUPorter_Cart.tga",)                          # the builder's paint reads it
    archive = "!!!!!!!!!!!!sagekit-elf-worker.big"
    bone = RIBS
    smooth = ("ELF",)
    opaque = True                       # EA's legacy opaque mesh: the preview ignores texture alpha
    views = {"portrait": View("idla", 0, elevation=18, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.6),
             "back": View("wlka", 8, elevation=26, azimuth=150, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.6),
             "work": View("wrkb", 30, elevation=24, azimuth=-120, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.6),
             "rts": View("idla", 0, elevation=52, size=(520, 420), fit=True, fit_min=170, fit_scale=1),
             "death": View("diea", 30, elevation=40, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.6)}
    labels = ("EA'S ELVEN WORKER", "LORIEN JOURNEYMAN - REVIEW")
    label_colour = "#17251dcc"

    def design(self, w, sk):
        elf = self.mesh(w, sk, "ELF", keep=True)
        elf.uv_for = patch_uv(HC_BOX)
        cloak(elf)
        circlet(elf)
        belt(elf)
        return {"ELF": elf}

    def check(self, b, original, new, sk):
        assert new.meshes["HAMMER"].bytes == original.meshes["HAMMER"].bytes, "HAMMER"
        check_patch(b.src / self.mask[0].lower(), HC_BOX)

    def paint(self, b):
        """The builder's atlas, painted the same way: one crew, one set of materials."""
        return Porter.paint(self, b)
