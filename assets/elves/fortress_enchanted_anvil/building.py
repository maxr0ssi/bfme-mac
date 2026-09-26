"""The fortress's enchanted anvil (Draw ModuleTag_DrawEnchantedAnvil of ElvenCitadel): the smithy on
the back of the ring - a work platform over the ring's cap with the anvil, the weapon rack and the
smith, and the tall forge chimney that stands in the courtyard. The chimney is crowned with a gilt
leaf crown round a starlight crystal in its flue, and two banner poles fly the player's colours
over the platform.

EA's model (EBFANVIL1, 999 triangles, drawn at the fortress's origin; mesh coordinates): the
platform x -50.26..-29, |y| 17.04 (chamfered to x -33.5 at |y| 11.5), top z 58.2; the chimney round
(-22.01, 0.23) from the ground, its pointed buttresses to z 56, a decorated bulge to r 8.6 (z 66..90)
and a slender top to z 106.19 (outer r 3.9, the hexagonal flue r 2.7). EA's anvil (EBFANVIL2, on its
bone at (-43.24, 8.2, 61.8)), the rack (x -44..-32, y -16..-4, z 58..85) and the smith's
PositionBone (the fortress's, (-29.69, 9.38, 55.84)) keep their space: the poles stand at
(-47, -5.5) and (-36, 11.5), clear of all three."""
import math

from sagekit.building import Building

from ..style import ElvenStyle



FLUE = (-22.01, 0.23)             # the chimney's axis
TOP = 106.19                      # its rim
PLATFORM = 58.2
# banner poles: (x, y, n): the banner faces n (both sides are cloth), the pennant flies along t
# (t x n = -z), toward the platform's middle: inside the footprint (|y| <= 17.04)
POLES = [(-47.0, -5.5, (1, 0, 0)), (-36.0, 11.5, (-1, 0, 0))]
POLE_TOP = 94.0


class FortressEnchantedAnvil(Building):
    style = ElvenStyle()
    source = "EBFAnvil"
    target = "EBFANVIL1"
    facet_islands = 20                  # EA's organic mallorn wood: seams at EA's islands and 20-degree turns
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresL.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawEnchantedAnvil",)
    tri_budget = 5000
    views = {
        "rts": ((-31.0, 0.0, 53.1), 260, 50, -38, 50),
        "close": ((-31.0, 0.0, 80.0), 120, 20, -30, 45),
        "ingame": ((-31.0, 0.0, 53.1), 590, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V
        from sagekit.blender.geometry import sweep
        from ..shapes import arc
        cx, cy = FLUE
        out = []
        # 1. a moulded collar round the chimney's rim, open over the flue
        path = arc(cx, cy, 4.05, 0, 360, 12)
        path[-1] = path[0]
        prof = [(-1.3, TOP - 2.4), (0.75, TOP - 2.4), (1.05, TOP - 1.7), (0.85, TOP - 0.9), (-1.3, TOP - 0.9)]
        out += sweep(path, prof, [None, "coping", "trim", "top", "enamel"], center=(cx, cy))[0]
        # 2. the leaf crown: six upright gilt blades round the rim (the kit builds any blade over the
        #    gilt tile's height in pieces, so their length is a free design choice)
        for k in range(6):
            a = math.radians(30 + 60 * k)
            r = V((math.cos(a), math.sin(a), 0))
            tn = V((-r.y, r.x, 0))
            out.append(kit.leaf_blade(V((cx, cy, 0)), r, tn, 3.9, TOP - 1.2, 4.2, 1.5, lean=0.0, thick=0.22))
        # 3. the starlight crystal in the flue
        out += kit.crystal_lantern(cx, cy, TOP - 3.6, h=9.5, r=1.55)
        # 4. banner poles over the platform
        for x, y, nn in POLES:
            out += self._pole(kit, x, y, V(nn))
        return out

    @staticmethod
    def _pole(kit, x, y, n):
        from mathutils import Vector as V
        from ..shapes import turned
        t = V((-n.y, n.x, 0))
        c = V((x, y, 0))
        out = [turned(x, y, [(1.25, PLATFORM - 0.3), (1.25, PLATFORM + 0.6), (0.95, PLATFORM + 0.9), (0.75, PLATFORM + 1.6)],
                      ["stoneB", "coping", "trim"], 10, cap0=("stoneB", False), cap1=("top", True)),
               turned(x, y, [(0.26, PLATFORM + 1.5), (0.2, POLE_TOP)], ["gilt"], 8, cap0=("gilt", False), cap1=("gilt", True))]
        out += kit.leaf_finial(x, y, POLE_TOP - 0.1, 2.5, 0.9)
        out += kit.leaf_banner(c, t, n, 0.0, POLE_TOP - 2.6, 5.6, 15.0, d=0.45, free=True)
        out += kit.pennant(c, t, n, 0.3, POLE_TOP - 0.4, 11.0, 1.7)
        return out

    def emphasis(self, c, n):
        return 1.4 if c.z > 95 else 1.0
