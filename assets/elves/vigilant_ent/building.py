"""Elven vigilant ent (ElvenVigilantEntExpansion, model EBFVEntHol): the planted ring the fortress's
ent stands guard in, its arm reaching back to the fortress over a pointed arch.

EA's body (EBFVENTBUD, 260 triangles): a twelve-sided planter ring round an earth bed, centre
(-1.9, 0), its rim 2.95 wide at z 5.76 (outer corners 21.93 out, inner 18.98, at 15 + 30k degrees);
the arm (faces y -3.44 / 2.44, x -43.91..-6.57, its top falling from 53.0 to 38.1) with the
expansions' arch (axis x -31.4, assets/elves/floodgate/pad.py); a slab across the arm's end
(x -15.85..-11.29, |y| 7.0, a gable to 37.84). The ent stands in the bed: nothing new enters it.

The redesign: a moonstone balustrade round the rim (turned balusters, a silver rail), newel posts
at its corners carrying slender columns with Lórien crystal lanterns, the pointed silver frame
round the arm's arch on both faces, a crystal beacon on the arm's end and three leaf banners in
the player's colour (the arm's end and the slab's two faces) - so the ent's ring reads as an
Elven garden rather than a bare planter. All in EBFVENTBUD mesh coordinates."""
import math

from sagekit.building import Building

from ..floodgate import pad
from ..style import ElvenStyle

RING_C = (-1.9, 0.0)
RIM_Z = 5.76
RIM_R = 20.45                       # the rim's middle line, at a corner (outer 21.93, inner 18.98)
# the balustrade runs round every side but the arm's (165 -> -165 through 0), clockwise
RAIL_ANGLES = [165 - 30 * i for i in range(12)]
POSTS = (165, 135, 75, 15, -15, -75, -135, -165)   # newels: the ends and every other corner, the 0 axis framed
ARM_FACES = [(-3.44, -1), (2.44, 1)]
ARCH_X = -31.4
# leaf banners (anchor, t, n, u along t, z_top, width, length): the arm's end faces +x (x -6.57,
# y -3.44..2.44); the slab's faces at y -7 / +7 (x -15.85..-11.29, up to 34.14 at their edges)
BANNERS = [((-6.57, 0.0), (0, 1), (1, 0), -0.5, 33.5, 4.2, 21.0),
           ((0.0, -7.0), (1, 0), (0, -1), -13.57, 30.5, 3.0, 17.0),
           ((0.0, 7.0), (-1, 0), (0, 1), 13.57, 30.5, 3.0, 17.0)]
BEACON = (-8.6, -0.5, 38.3)         # a crystal lantern on the arm's end, over the ent


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
        for a in POSTS:
            solids += self._lantern_post(kit, a)
        solids += pad.arch(kit, ARCH_X, ARM_FACES)
        for (ax, ay), t, n, u, z_top, width, length in BANNERS:
            solids += kit.leaf_banner(V((ax, ay, 0)), V((t[0], t[1], 0)), V((n[0], n[1], 0)), u, z_top, width, length,
                                      d=0.02)
        solids += kit.crystal_lantern(*BEACON, h=4.6, r=1.0)
        return solids

    @staticmethod
    def _lantern_post(kit, angle):
        """A square moonstone newel on the rim (the rail runs into it), a slender leaf-capital
        column on it and a crystal lantern on top."""
        from sagekit.blender.geometry import loft
        from ..shapes import ring
        cx, cy = corner(angle)
        ph = math.radians(angle + 45)

        def sq(h, z):
            return ring(cx, cy, h, z, 4, sq=8.0, phase=ph)
        z0, z1 = RIM_Z, RIM_Z + 4.4
        out = [loft([sq(1.05, z0), sq(1.05, z1 - 0.7), sq(1.3, z1 - 0.45), sq(1.3, z1)],
                    ["stoneA", "coping", "trim"], cap0=("stoneB", False), cap1=("top", True))]
        out += kit.column(cx, cy, z1, z1 + 5.2, r=0.42, k=10, leaves=5)
        out += kit.crystal_lantern(cx, cy, z1 + 5.2, h=3.4, r=0.75)
        return out

    def emphasis(self, c, n):
        if c.z > RIM_Z + 3.5 and math.hypot(c.x - RING_C[0], c.y - RING_C[1]) > 17:
            return 1.3                        # the lantern posts
        return 1.0
