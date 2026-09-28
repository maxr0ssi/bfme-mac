"""The boiling-oil pot (UPGRADE_BOILING_OIL, Draw ModuleTag_OilGuyDraw of MenFortressCitadel): the
iron cauldron the man-at-arms tips over the hearth on the back wall walk. EA's pot is kept whole
and bound in the citadel's bright steel: a band round its rim under the flared lip, a hoop round
its belly and one low down, four straps up its lower half, and a gilt seven-pointed star on each
side under the lugs. EA's pot stays dark iron (the stone recolour would whiten it).

EA's GBFBOILPOT (164 triangles) hangs on its bone GBFBOILPOT at (-41.22, 0.4, 56.23) (no
rotation; design coordinates are the mesh's, about the axle): the axle along y (|x|, |z| <
0.7, y +-9.49), two crossed levers at y 8.37..8.88, the body an octagon round (0, -0.4) - at
z -4.42 x +-4.5, y -4.86..4.06; at -0.93 (its widest) x -5.3..5.19, y -5.59..4.79; the outer
wall at 2.29 (r 3.7..4.7, the spout's root at +x); the lip flaring to r 5.4 at 3.16, the spout
at +x to 6.02 (z 2.0..2.9), the lugs at 4.6 over y -4.7 and 3.9. The oil's surface is at 0.59
(the OIL mesh, kept). The pot turns about the axle (ATKA): everything added hugs the body, so it
sweeps nothing new. The belly hoop passes EA's x -5.3 by 0.3 (footprint_margin 0.4).
"""
from sagekit.building import Building

from ..style import MenStyle

C = (0.0, -0.4)                                 # the body's axis
LOW = [(-3.07, -3.47), (-0.0, -4.86), (3.07, -3.47), (4.5, -0.4), (3.07, 2.66), (-0.0, 4.06), (-3.07, 2.66), (-4.5, -0.4)]
BELLY = [(-3.55, -3.94), (-0.0, -5.59), (3.55, -3.94), (5.19, -0.4), (3.55, 3.14), (-0.0, 4.79), (-3.55, 3.14), (-5.3, -0.4)]
Z_LOW, Z_BELLY = -4.42, -0.93
UPPER = [(-2.91, -3.31), (-0.0, -4.66), (2.13, -4.09), (4.73, -1.74), (4.73, 0.94), (2.13, 3.28), (-0.0, 3.86),
         (-2.91, 2.5), (-4.37, -0.4)]
Z_UPPER = 2.29


def at(z):
    """The body's outline at z between the low ring and the belly (straight between them)."""
    k = (z - Z_LOW) / (Z_BELLY - Z_LOW)
    return [(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k) for a, b in zip(LOW, BELLY)]


class FortressOilGuy(Building):
    style = MenStyle()
    source = "GBFBOil_SKN"
    target = "GBFBOILPOT"
    sheet = "gbfortress1.tga"
    sheet_normal = "gbfortress1_nrm.tga"
    own_textures = {"GBFortress1.tga": "GBFortressP.tga"}      # keyed by the atlas name (the sheet is the atlas); free in EA's files
    parts = ("ModuleTag_OilGuyDraw",)
    footprint_margin = 0.4
    tri_budget = 1500
    views = {
        "rts": ((-40.9, 0.4, 55.6), 54, 50, -38, 50),
        "close": ((-40.9, 0.4, 55.6), 32, 24, -30, 45),
        "ingame": ((-40.9, 0.4, 55.6), 123, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import sweep

        from ..shapes import rail

        def hoop(path, z0, z1, out=0.28):
            prof = [(-0.3, z0), (out * 0.6, z0), (out, z0 + 0.15), (out, z1 - 0.15), (out * 0.6, z1), (-0.3, z1)]
            return sweep(path + [path[0]], prof, ["trim", "trim", "trim", "trim", "trim", None], center=C)[0]
        out = hoop(BELLY, Z_BELLY - 0.45, Z_BELLY + 0.3, out=0.3)
        out += hoop(at(-3.75), -4.05, -3.45, out=0.25)
        out += hoop(UPPER, 1.75, 2.35, out=0.25)
        for k in (0, 2, 4, 6):                      # straps up the lower half, on the diagonals
            pts = [V((x, y, z)) for (x, y), z in ((LOW[k], Z_LOW + 0.2), (at(-2.7)[k], -2.7), (BELLY[k], Z_BELLY))]
            c = V((C[0], C[1], 0))
            pts = [p + (V((p.x, p.y, 0)) - c).normalized() * 0.18 for p in pts]
            out.append(rail(pts, 0.2, "trim", 0.2))
        for y, s in ((-5.3, -1), (4.52, 1)):         # gilt stars on the sides, under the lugs
            a, t, n = V((0, y, 0)), V((-s, 0, 0)), V((0, s, 0))
            out += kit.star(a, t, n, 0.0, -2.35, 0.95, -0.35, 0.3)
        return out

    def decals(self):
        """EA's pot stays a dark iron pot (the stone recolour would whiten it) and its axle and
        levers wood; the new steel stands bright against it."""
        return [_iron_pot_layer()]

    def emphasis(self, c, n):
        return 1.35


def _iron_pot_layer():
    import numpy as np

    from sagekit.paint.fields import ramp
    from sagekit.paint.layers import Layer

    class IronPot(Layer):
        def apply(self, col, cv, pal):
            old = (cv.tag_is("old") & (cv.covm > 0.5)).astype(np.float32)
            body = (np.abs(cv.pos[..., 1] - C[1]) < 6.2).astype(np.float32)
            L = np.clip(cv.lum * 1.25 + 0.05, 0, 1)
            iron, wood = ramp(L, pal["iron"]), ramp(np.clip(L * 1.1, 0, 1), pal["wood"])
            m, w = (old * body)[..., None], (old * (1 - body))[..., None]
            return col * (1 - m - w) + iron * m + wood * w
    return IronPot()
