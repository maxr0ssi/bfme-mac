"""The fortress's enchanted anvil (Draw ModuleTag_DrawEnchantedAnvil of ElvenCitadel): the smithy on
the back of the ring - a work platform over the ring's cap with the anvil, the weapon rack and the
smith, and the tall forge chimney that stands in the courtyard. It takes the citadel's crown where
the citadel leaves off (its ring has no lantern on the anvil's face, 180): the ring's silver coping
runs on round the platform's parapet and the ring's crystal lantern stands on its front. The
chimney is crowned with a gilt leaf crown round a starlight crystal in its flue (the "enchanted"
forge), and one gilt pole flies the player's colour over the platform.

EA's model (EBFANVIL1, 999 triangles, drawn at the fortress's origin; mesh coordinates): the
platform's parapet, 1.1..1.3 thick, its outer line from the chimney (-22.74, -8.64), (-30.8, -17.02), (-44.78, -17.02), (-48.39,
-11.49), (-49.75, -5.96), (-50.26, 0) and mirrored, the floor at z 56, the top at 58.2; the chimney
round (-22.01, 0.23) from the ground, its pointed buttresses to z 56, a decorated bulge to r 8.6 (z
66..90) and a slender top to z 106.19 (outer r 3.9, the hexagonal flue r 2.7). EA's anvil
(EBFANVIL2, on its bone at (-43.24, 8.2, 61.8)), the rack (x -44..-32, y -16..-4, z 58..85) and the
smith's PositionBone (the fortress's, (-29.69, 9.38, 55.84)) keep their space: the pole stands at
(-47, -5.5) and the lantern on the parapet's front at (-49.73, 0), clear of all three."""
import math

from sagekit.building import Building

from ..style import ElvenStyle

FLUE = (-22.01, 0.23)             # the chimney's axis
TOP = 106.19                      # its rim
PLATFORM = 58.2                   # the parapet's top (the floor is at 56)
PARAPET = [(-22.74, -8.64), (-30.8, -17.02), (-44.78, -17.02), (-48.39, -11.49), (-49.75, -5.96), (-50.26, 0.01),
           (-49.75, 5.98), (-48.39, 11.51), (-44.78, 17.04), (-30.8, 17.04), (-22.74, 8.66)]
# the coping, (d from the parapet's outer face, z), as the citadel's: its underside buried in the
# parapet (inner face at d -1.1..-1.3), a silver nose 0.5 proud, a silver top over the whole wall
COPING = [(-1.05, 58.0), (0.0, 57.35), (0.35, 57.35), (0.5, 57.75), (0.5, 58.65), (0.28, 59.0), (-1.05, 59.0)]
COPING_TAGS = [None, "trim", "trim", "trim", "trim", "trim", "trim"]
COPING_TOP = 59.0
LANTERN = (-49.73, 0.01)          # on the parapet's front, over the middle of the ring's face 180
POLE = (-47.0, -5.5)              # the banner faces +x, over the platform, toward the courtyard
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
    footprint_margin = 0.8              # the coping's nose (0.5) and the lantern's foot over the parapet's front:
                                        # the anvil stands on the citadel's ring, whose own coping reaches x -53.1
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
        out = sweep(PARAPET, COPING, COPING_TAGS, center=(-38.0, 0.0))[0]    # 1. the citadel's coping
        out += self._lantern(kit)                                             # 2. and its lantern
        # 3. a moulded silver collar round the chimney's rim, open over the flue
        path = arc(cx, cy, 4.05, 0, 360, 12)
        path[-1] = path[0]
        prof = [(-1.3, TOP - 2.4), (0.75, TOP - 2.4), (1.05, TOP - 1.7), (0.85, TOP - 0.9), (-1.3, TOP - 0.9)]
        out += sweep(path, prof, [None, "trim", "trim", "trim", "enamel"], center=(cx, cy))[0]
        # 4. the leaf crown: six upright gilt blades round the rim
        for k in range(6):
            a = math.radians(30 + 60 * k)
            r = V((math.cos(a), math.sin(a), 0))
            tn = V((-r.y, r.x, 0))
            out.append(kit.leaf_blade(V((cx, cy, 0)), r, tn, 3.9, TOP - 1.2, 4.2, 1.5, lean=0.0, thick=0.22))
        # 5. the starlight crystal in the flue
        out += kit.crystal_lantern(cx, cy, TOP - 3.6, h=9.5, r=1.55)
        out += self._pole(kit, *POLE)                                         # 6. one banner
        return out

    @staticmethod
    def _lantern(kit):
        """The citadel's ring lantern (Fortress._ring_lantern): a starlight crystal in a gilt cup on
        a slender silver post, a gilt leaf on its tip, on the coping's top."""
        from ..shapes import turned
        cx, cy = LANTERN
        z = COPING_TOP - 0.1
        out = [turned(cx, cy, [(1.0, z), (1.0, z + 0.5), (0.8, z + 0.9), (0.58, z + 1.6), (0.48, z + 4.2), (0.95, z + 4.8)],
                      ["trim"] * 5, 10, cap0=("trim", False), cap1=("trim", True))]
        return out + kit.crystal_lantern(cx, cy, z + 4.7, h=6.4, r=1.25)

    @staticmethod
    def _pole(kit, x, y):
        """A slender gilt pole on a moulded silver foot, a leaf finial on its head and a leaf banner
        (house colour) facing the courtyard."""
        from mathutils import Vector as V

        from ..shapes import turned
        n = V((1, 0, 0))
        t = V((-n.y, n.x, 0))
        out = [turned(x, y, [(1.25, PLATFORM - 2.5), (1.25, PLATFORM - 1.6), (0.95, PLATFORM - 1.3), (0.75, PLATFORM - 0.6)],
                      ["trim", "trim", "trim"], 10, cap0=("stoneB", False), cap1=("top", True)),
               turned(x, y, [(0.26, PLATFORM - 0.7), (0.2, POLE_TOP)], ["gilt"], 8, cap0=("gilt", False), cap1=("gilt", True))]
        out += kit.leaf_finial(x, y, POLE_TOP - 0.1, 2.5, 0.9)
        out += kit.leaf_banner(V((x, y, 0)), t, n, 0.0, POLE_TOP - 2.6, 5.6, 15.0, d=0.45, free=True)
        return out

    def emphasis(self, c, n):
        return 1.4 if c.z > 95 else 1.0
