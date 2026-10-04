"""Erebor mason: the construction worker in the master builder's colours and gear.

DUWorker_SKN is the builder's dwarf without the cart (same meshes, the same rest pose to 1e-6), so
the crew shares the builder's leather apron, shoulder guards, beard bindings and forged hammer, on
the builder's own atlas paint. The worker adds a short mantle and back cape in player colour with a
bronze chevron. EA's dwarf, helm, pouches, skeleton and animations are kept; every piece follows
one of EA's bones. python3 -m sagekit unit dwarves/worker --render (docs/UNITS.md).
"""
import math

from assets.dwarves.porter.design import BRONZE, GOLD, IRON, LEATHER, OAK, STEEL, Porter
from sagekit.units import Unit, View
from sagekit.units.cloth import HC, check_patch, drape, patch_uv

# The cloth samples a clean patch of EA's tunic (HC_DUPorter tints it) in the atlas' unused
# top-left tile: the game tints it with the player colour as it tints the tunic.
HC_BOX = (20, 185, 140, 228)    # x0, y0, x1, y1 in the 256-pixel sheet


def cape_row(z, half, lift, fold, cols=9):
    """One row of the cape: across the back's curve (x = 16.1 + 0.11 y^2, measured off EA's dwarf),
    `lift` behind it, with folds that deepen toward the hem."""
    out = []
    for i in range(cols):
        y = -half + 2 * half * i / (cols - 1)
        x = 16.12 + .11 * y * y - lift - fold * (.5 + .5 * math.cos(y * math.pi / .9))
        out.append((x, y, z))
    return out


def mantle(m):
    """A short cape in player colour pinned below the nape: it follows the back's curve, flares and
    folds toward the hem, and bends at the waist (upper rows on the upper spine, the hem on the
    lower). Narrower than the shoulders, so the swinging arms pass outside it."""
    up, low = "B_SPINE2_01", "B_SPINE1_01"
    rows = [(up, cape_row(13.85, 1.95, .02, 0)), (up, cape_row(12.4, 2.3, .12, .04)),
            (up, cape_row(10.6, 2.5, .2, .1)), (low, cape_row(9.0, 2.7, .3, .16)),
            (low, cape_row(7.7, 2.85, .42, .2))]
    drape(m, rows, HC)
    for s in (-1, 1):                                                   # bronze brooches
        m.tube((16.3, s * 1.95, 13.45), (15.95, s * 1.95, 13.45), .36, BRONZE, up, sides=10)
    # Erebor chevrons on the back, raised off the cloth (read from the RTS camera behind him).
    for z in (11.0, 11.8):
        for s in (-1, 1):
            m.tube((15.88 + .11 * .9, s * .95, z), (15.88, 0, z + .7), .11, GOLD, up, sides=6)
    rail = cape_row(7.75, 2.85, .5, .2)                                 # bronze-weighted hem
    for a, b in zip(rail, rail[1:]):
        m.tube(a, b, .1, BRONZE, low, sides=6)


def outfit(m):
    """The builder's apron, shoulder guards and beard bindings; the inlays in player colour."""
    m.box((20.78, -1.9, 10.2), (21.02, 1.9, 11.7), LEATHER, "B_SPINE2_01")
    m.box((20.85, -2.7, 8.85), (21.5, 2.7, 9.5), LEATHER, "B_SPINE1_01")
    for s, bone in [(-1, "BAT_THIGHR_01"), (1, "BAT_THIGHL_01")]:
        lo, hi = sorted((s * .16, s * 2.65))
        m.box((21.13, lo, 6.0), (21.45, hi, 8.7), LEATHER, bone)
        m.box((21.46, lo + .08, 6.15), (21.5, hi - .08, 6.3), BRONZE, bone)
    m.box((21.5, -.65, 8.92), (21.67, .65, 9.52), BRONZE, "B_SPINE1_01")
    m.box((21.68, -.43, 9.04), (21.7, .43, 9.39), HC, "B_SPINE1_01")
    for s, b in [(-1, "B_UARMR_01"), (1, "B_UARML_01")]:
        m.tube((18.65, s * 3.25, 12.0), (18.65, s * 4.0, 11.2), 1.22, LEATHER, b, sides=10, r1=1.15)
        m.tube((18.65, s * 3.94, 11.26), (18.65, s * 4.07, 11.13), 1.19, BRONZE, b, sides=10)
    for y in (-.82, .82):
        m.tube((21.75, y, 10.15), (21.5, y, 11.1), .33, BRONZE, "BONE02_01", sides=8)
        m.tube((21.7, y, 10.45), (21.63, y, 10.72), .35, HC, "BONE02_01", sides=8)


def hammer(m):
    """The builder's forged hammer, EA's grip and swing: oak haft, iron head, steel faces."""
    b = "B_HANDR_01"
    m.tube((18.9, -6.35, 7.1), (22.5, -7.35, 5.65), .22, OAK, b, sides=8)
    m.box((21.6, -8.4, 4.65), (23.25, -6.1, 6.55), IRON, b)
    for y in (-8.45, -6.1):
        m.box((21.55, y, 4.6), (23.3, y + .16, 6.6), STEEL, b)
    m.box((21.5, -7.5, 4.58), (23.35, -7.0, 6.62), BRONZE, b)


class Worker(Unit):
    """DwarvenWorker (and its NoSelect, Farm and Fortress children) draws DUWorker_SKN: in place."""
    model, skeleton = "DUWorker_SKN", "DUWorker_SKL"
    anims = ("wrkd", "wrke", "wlka", "dieb")
    expected = {"duworker_skn": "0cc1c31776acb9bcf480ccf32106feb3ec177a0880bf26038ad3a0c842bd3388",
                "duworker_skl": "0837eb8c9ab211d3f31cf8d81b468ecb8b9e7875ed2bbc6a3be73579bc454613"}
    textures = {"duporter.tga": "DUWorkCr.tga"}
    house = {"DUWorkCr.tga": "HC_DUWorkCr.tga"}
    mask = ("HC_DUPorter.tga", "HC_DUWorkCr.tga")
    sources = ("GUPorter_Cart.tga", "DBFortress1.tga")      # the builder's paint reads these
    archive = "!!!!!!!!!!!!sagekit-dwarf-worker.big"
    bone = "B_SPINE2_01"
    smooth = ("DWARF", "HELM", "POUCHES")
    views = {"portrait": View("wrkd", 0, elevation=18, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.9),
             "back": View("wlka", 8, elevation=26, azimuth=150, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.9),
             "work": View("wrkd", 20, elevation=24, azimuth=-120, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.9),
             "swing": View("wrke", 40, elevation=20, azimuth=160, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.9),
             "rts": View("wrkd", 0, elevation=52, size=(520, 420), fit=True, fit_min=170, fit_scale=1),
             "death": View("dieb", 60, elevation=40, size=(900, 1000), fit=True, fit_min=40, fit_scale=1.9)}
    labels = ("EA'S DWARVEN WORKER", "EREBOR MASON - REVIEW")

    def design(self, w, sk):
        meshes = {n: self.mesh(w, sk, n, keep=n == "DWARF") for n in ("DWARF", "HAMMER")}
        for m in meshes.values():
            m.uv_for = patch_uv(HC_BOX)
        outfit(meshes["DWARF"])
        mantle(meshes["DWARF"])
        hammer(meshes["HAMMER"])
        return meshes

    def check(self, b, original, new, sk):
        for n in ("HELM", "POUCHES"):
            assert new.meshes[n].bytes == original.meshes[n].bytes, n
        check_patch(b.src / self.mask[0].lower(), HC_BOX)

    def paint(self, b):
        """The builder's atlas, painted the same way: one crew, one set of materials."""
        return Porter.paint(self, b)
