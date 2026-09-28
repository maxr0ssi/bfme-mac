"""Elven vigilant ent (ElvenVigilantEntExpansion, model EBFVEntHol): the planted ring the fortress's
ent stands guard in, its arm reaching back to the fortress over a pointed arch.

EA's body (EBFVENTBUD, 260 triangles): a twelve-sided planter ring round an earth bed, centre
(-1.9, 0), its rim 2.95 wide at z 5.76 (outer corners 21.93 out, inner 18.98, at 15 + 30k degrees);
the arm (faces y -3.44 / 2.44, x -43.91..-6.57, its top falling from 53.0 to 38.1) with the
expansions' arch (axis x -31.4, assets/elves/floodgate/pad.py); a slab across the arm's end
(x -15.85..-11.29, |y| 7.0, a gable to 37.84). The ent stands in the bed: nothing new enters it.

The redesign, the citadel's recipe on the ent's ring: EA's body kept whole and a handful of
additions - an ivory balustrade round the rim with a silver rail, six newels carrying slender
leaf-capital columns and crystal lanterns, a mithril cap along the arm's sweeping top (the
citadel's ridges) ending in a crystal beacon over the ent, silver copings on the slab's shoulders
with a gilt leaf finial on each, and the pointed silver frame round the arm's arch. Two banners,
one on each end of the slab. All in EBFVENTBUD mesh coordinates."""
import math

from sagekit.building import Building

from ..floodgate import pad
from ..style import ElvenStyle

RING_C = (-1.9, 0.0)
RIM_Z = 5.76
RIM_R = 20.45                       # the rim's middle line, at a corner (outer 21.93, inner 18.98)
# the balustrade runs round every side but the arm's (165 -> -165 through 0), clockwise
RAIL_ANGLES = [165 - 30 * i for i in range(12)]
POSTS = (165, 105, 45, -45, -105, -165)   # newels: the ends and every other corner between
ARM_FACES = [(-3.44, -1), (2.44, 1)]
ARM_Y = (-3.44, 2.44)
ARCH_X = -31.4
# the arm's top (x, z), from the fortress end (just inside EA's -43.91: the footprint) down to its end over the ring
ARM_TOP = [(-43.86, 52.98), (-40.78, 51.61), (-36.12, 50.58), (-31.4, 50.74), (-26.68, 48.96), (-22.01, 45.63),
           (-18.89, 42.47), (-12.73, 38.81), (-6.57, 38.13)]
CAP = (0.35, 0.3, 0.45)             # the cap: out past the arm's faces, into its top, above it
# the slab across the arm (x -15.85..-11.29): its top falls from 37.84 over the arm's middle to 34.14
# at its ends (y +-7); the shoulders either side of the arm carry a coping (y along, (y, z))
SLAB_X = (-15.85, -11.29)
SHOULDERS = [[(-7.3, 33.98), (-3.0, 36.25)], [(2.0, 36.78), (7.3, 33.98)]]
SLAB_FINIAL = (6.55, 3.6)           # |y| of the finials over the slab's ends, their height
# leaf banners on the slab's ends (anchor, t, n, u along t, z_top, width, length): faces at y -7 / +7
BANNERS = [((0.0, -7.0), (1, 0), (0, -1), -13.57, 30.5, 3.0, 17.0),
           ((0.0, 7.0), (-1, 0), (0, 1), 13.57, 30.5, 3.0, 17.0)]
BEACON = (-8.9, -0.5)               # a crystal lantern on the arm's end, over the ent


def corner(angle, r=RIM_R):
    a = math.radians(angle)
    return RING_C[0] + r * math.cos(a), RING_C[1] + r * math.sin(a)


class VigilantEnt(Building):
    style = ElvenStyle()
    source = "EBFVEntHol"
    target = "EBFVENTBUD"
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresN.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCVigilantEnt"
    views = {
        "rts": ((-12.3, 0.0, 26.5), 204, 50, -38, 50),
        "close": ((-12.3, 0.0, 26.5), 121, 24, -30, 45),
        "ingame": ((-12.3, 0.0, 26.5), 464, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V
        solids = kit.balustrade([corner(a) for a in RAIL_ANGLES], RIM_Z, height=3.0, pitch=1.7, center=RING_C)
        for a in POSTS:                                                         # 1. balustrade and lanterns
            solids += self._lantern_post(kit, a)
        out_, into, above = CAP                                                 # 2. the arm's mithril cap
        y0, y1 = ARM_Y
        solids += pad.ridge_cap(ARM_TOP, y0 - out_, y1 + out_, below=into, above=above)
        solids += self._beacon(kit)
        x0, x1 = SLAB_X                                                         # 3. the slab's shoulders
        for pts in SHOULDERS:
            solids += pad.ridge_cap(pts, x0 - 0.3, x1 + 0.3, below=0.3, above=0.4, x_axis=False)
        yf, hf = SLAB_FINIAL
        for s in (-1, 1):
            solids += kit.leaf_finial((x0 + x1) / 2, s * yf, SHOULDERS[0][0][1] + 0.3, hf)
        solids += pad.arch(kit, ARCH_X, ARM_FACES)                              # 4. the arch's frame
        for (ax, ay), t, n, u, z_top, width, length in BANNERS:                 # 5. two banners
            solids += kit.leaf_banner(V((ax, ay, 0)), V((t[0], t[1], 0)), V((n[0], n[1], 0)), u, z_top, width, length,
                                      d=0.02)
        return solids

    @staticmethod
    def _beacon(kit):
        """A starlight crystal on a short silver post on the cap's end, over the ent."""
        from ..shapes import turned
        x, y = BEACON
        (xa, za), (xb, zb) = ARM_TOP[-2:]
        z = za + (zb - za) * (x - xa) / (xb - xa) + CAP[2] - 0.05
        out = [turned(x, y, [(0.95, z - 0.2), (0.95, z + 0.3), (0.6, z + 0.7), (0.45, z + 1.6), (0.8, z + 2.0)],
                      ["trim"] * 4, 10, cap0=("trim", False), cap1=("trim", True))]
        return out + kit.crystal_lantern(x, y, z + 1.9, h=5.6, r=1.15)

    @staticmethod
    def _lantern_post(kit, angle):
        """A square ivory newel on the rim (the rail runs into it) under a silver cap, a slender
        leaf-capital column on it and a crystal lantern on top."""
        from sagekit.blender.geometry import loft
        from ..shapes import ring
        cx, cy = corner(angle)
        ph = math.radians(angle + 45)

        def sq(h, z):
            return ring(cx, cy, h, z, 4, sq=8.0, phase=ph)
        z0, z1 = RIM_Z, RIM_Z + 4.4
        out = [loft([sq(1.05, z0), sq(1.05, z1 - 0.7), sq(1.3, z1 - 0.45), sq(1.3, z1)],
                    ["stoneA", "trim", "trim"], cap0=("stoneB", False), cap1=("trim", True))]
        out += kit.column(cx, cy, z1, z1 + 5.2, r=0.42, k=10, leaves=5)
        out += kit.crystal_lantern(cx, cy, z1 + 5.2, h=3.4, r=0.75)
        return out

    def emphasis(self, c, n):
        if c.z > RIM_Z + 3.5 and math.hypot(c.x - RING_C[0], c.y - RING_C[1]) > 17:
            return 1.3                        # the lantern posts
        if c.z > 33:
            return 1.2                        # the arm's cap, the beacon, the slab's finials
        return 1.0
