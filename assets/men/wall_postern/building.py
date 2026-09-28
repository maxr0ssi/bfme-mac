"""Men wall postern (MenWallPosternGateSmall, and Arnor's; model GBWallPGN): the door arch drawn over
a wall segment (the object draws GBWallN too, men/wall_segment's redesign). EA's two deep portals
are kept whole - their splayed round arches through the wall, the gabled tops - and each front is
given the citadel gate's language (men/fortress/gate.py) at the postern's size:

- a voussoir archivolt of nine wedge stones round the arch, a raised keystone;
- pilasters either side of the arch with moulded capitals at the springing and plinths;
- a moulded coping along the gabled top, pinnacles on its shoulders and the guard's winged-helm
  crest on the apex;
- a steel portcullis's teeth showing under the crown of the arch.

No banners (the wall run's two hang on the gate).

EA's GBFDOTOWA01 (mesh coordinates; the model turns it 180 degrees about z, symmetric): two
portals, x 4.72..14.17 either side of the wall's axis, y +-11.17; the front (|x| 14.17) opening
spring 26.15 at |y| 8.3, crown 31.22 (the splay narrows it to |y| 6.66, crown 29.51 at |x|
13.07); the top gabled from 28.47 at |y| 11.17 to 32.62 at |y| 6.48 and 34.59 on the axis. The
fronts lie on the footprint's edge (x +-14.17): the archivolt, pilasters and coping stand up to
1.0 proud of them (`footprint_margin`; collision is the INI's, the segment's).
"""
from sagekit.building import Building

from ..style import MenStyle

FRONT = 14.17
OPEN = (8.3, 5.07, 26.15)          # the front opening: half width, rise, spring
ARCH_OUT = (10.55, 7.25)           # the archivolt's outer half width and rise
GABLE = [(-11.17, 28.47), (-6.48, 32.62), (0.0, 34.59), (6.48, 32.62), (11.17, 28.47)]
PIL = (8.75, 10.95)                # the pilasters' |y|


class WallPostern(Building):
    style = MenStyle()
    source = "GBWallPGN"
    target = "GBFDOTOWA01"
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressD.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DoorDraw",)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallPostern"
    house_tags = ()                 # no banners on the wall pieces but the gate
    footprint_margin = 1.0          # the portals' fronts are the footprint's edge
    views = {
        "rts": ((0.0, 0.0, 17.3), 120, 50, -38, 50),
        "close": ((-4.0, 0.0, 22.0), 72, 18, -60, 45),
        "ingame": ((0.0, 0.0, 17.3), 250, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V
        out = []
        for s in (1, -1):
            a, t, n = V((s * FRONT, 0, 0)), V((0, s, 0)), V((s, 0, 0))
            out += self._front(kit, a, t, n)
        return out

    @staticmethod
    def _front(kit, a, t, n):
        import math

        from sagekit.blender.geometry import prism_uz
        out = []
        half, rise, spring = OPEN
        oh, orise = ARCH_OUT
        out += kit.voussoirs(a, t, n, (half, rise, spring), (oh, orise, spring), -0.4, 0.75, count=9, gap=0.1,
                             key=(0.85, spring + orise + 0.55, 0.2))
        for e in (-1, 1):                              # pilasters, plinths and capitals
            y0, y1 = sorted((e * PIL[0], e * PIL[1]))
            out.append(prism_uz(a, t, n, [(y0 - 0.2, 0.0), (y1 + 0.2, 0.0), (y1 + 0.2, 2.6), (y0 - 0.2, 2.6)], -0.4, 0.95,
                                ["stoneB", "stoneB", "top", "stoneB"], "stoneB", None))
            out.append(prism_uz(a, t, n, [(y0, 2.6), (y1, 2.6), (y1, spring - 1.6), (y0, spring - 1.6)], -0.4, 0.6,
                                [None, "stoneB", None, "stoneB"], "stoneA", None))
            out.append(prism_uz(a, t, n, [(y0 - 0.15, spring - 1.6), (y1 + 0.2, spring - 1.6), (y1 + 0.2, spring),
                                          (y0 - 0.15, spring)], -0.4, 0.9, ["stoneB", "course", "top", "course"], "course", None))
        for i in range(7):                             # the portcullis's teeth under the crown
            y = -4.8 + 1.6 * i
            zt = spring + rise * math.sqrt(max(0.0, 1 - (y / half) ** 2)) + 0.4
            zb = spring + 1.2 - 0.25 * abs(y)
            out.append(prism_uz(a, t, n, [(y - 0.2, zb), (y + 0.2, zb), (y + 0.2, zt), (y - 0.2, zt)], -1.3, -0.95,
                                [None, "iron", None, "iron"], "iron", None))
            out.append(prism_uz(a, t, n, [(y - 0.3, zb), (y + 0.3, zb), (y, zb - 0.7)], -1.3, -0.9,
                                ["iron", "iron", "iron"], "iron", None))
        out.append(prism_uz(a, t, n, [(-6.0, spring + 1.6), (6.0, spring + 1.6), (6.0, spring + 2.1), (-6.0, spring + 2.1)],
                            -1.35, -0.85, ["iron"] * 4, "iron", None))
        for p, q in zip(GABLE, GABLE[1:]):             # the coping along the gable
            poly = [(p[0], p[1] - 0.25), (q[0], q[1] - 0.25), (q[0], q[1] + 0.6), (p[0], p[1] + 0.6)]
            out.append(prism_uz(a, t, n, poly, -9.6, 0.5, ["stoneB", "course", "stoneA", "course"], "course", "stoneB"))
        for e in (-1, 1):                              # pinnacles on the shoulders
            c = a + t * (e * 9.9) - n * 1.3
            out += kit.pinnacle(c.x, c.y, 29.2, 31.9, half=0.85, spire=3.0, orb=True)
        out += kit.winged_crest(a, t, n, 0.0, 34.9, -2.8, -0.2, s=0.9)
        return out

    def decals(self):
        from ..wall_segment.paintwall import wall_layers
        return [wall_layers()()]                  # EA's joints crisp on the white stone

    def emphasis(self, c, n):
        return 1.35 if abs(c.x) > 12.5 or c.z > 28 else 1.0
