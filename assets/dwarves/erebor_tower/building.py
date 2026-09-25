"""Dwarven Erebor tower fortress expansion (DwarvenEreborTowerTowerExpansion): the tallest of the
fortress's pad buildings, given the fortress towers' own head - corbelled cornice with the hexagon
frieze over the bronze shields, battered crown ring, stepped-pyramid corners and stepped gables -
and a gilded stepped pinnacle on its roof; rune panels on the flanks and battered plinths at the
foot of the side slabs.

The head is EA's fortress-tower head (core 28.7 square, shields 1.6 proud, inner parapet walls 2.9
in, shield tops 108.9), so the fortress's TOWER_HEAD and CROWN profiles fit it lifted by 0.2.
The -X side (the low connecting wall x -56..-17) faces the fortress and is left as it is. The eight
ARROW bones fire from the shield windows (z 99.5): the cornice starts above them (105.4).
All measurements in DBFTOWER mesh coordinates, taken from the original model."""
from sagekit.building import Building

from ..style import DwarvenStyle

HEAD = (-19.8, 8.9, -14.3, 14.3)            # the head's core box (shields and posts stand on it)
HEAD_C = ((HEAD[0] + HEAD[1]) / 2, (HEAD[2] + HEAD[3]) / 2)
DZ = 108.9 - 108.7                          # the fortress tower-head numbers, onto this head
# the fortress's tower head and crown ring (assets/dwarves/fortress/building.py)
TOWER_HEAD = [(0, 105.2), (1.1, 106.2), (1.1, 106.6), (2.3, 107.6), (2.3, 110.4), (1.9, 110.8), (-2.9, 110.8),
              (-2.9, 108.7)]
TOWER_HEAD_TAGS = ["trim", "stoneB", "trim", "hex", "trim", None, "stoneA", "stoneB"]
CROWN = [(-2.9, 110.8), (2.3, 110.8), (1.6, 114.8), (1.6, 115.3), (0.6, 115.3), (0.2, 117.4), (-0.6, 117.4),
         (-1.6, 116.2), (-2.9, 116.2)]
CROWN_TAGS = [None, "stoneB", "trim", "top", "stoneA", "top", "top", "top", "stoneA"]
ROOF_TOP = (-5.4, 0.0, 125.0)               # the roof's flat top ring: x -12.3..1.5, |y| 6.9


def lifted(profile, dz):
    return [(d, z + dz) for d, z in profile]


class EreborTower(Building):
    style = DwarvenStyle()
    source = "DBFTower"
    target = "DBFTOWER"
    sheet = None                                                # the faction atlas DBFortress1
    own_textures = {"DBFortress1.tga": "DBFortressE.tga"}
    views = {
        "rts": ((-14, 0, 66), 380, 50, -38, 50),
        "close": ((-8, 0, 80), 285, 22, -34, 45),
        "ingame": ((-18, 0, 50), 850, 53, -62, 50),
    }

    def design(self, kit):
        from sagekit.blender.geometry import sweep
        solids = []
        xa, xb, ya, yb = HEAD                                           # 1. head and crown
        path = [(xa, ya), (xb, ya), (xb, yb), (xa, yb), (xa, ya)]
        ss, segs = sweep(path, lifted(TOWER_HEAD, DZ), TOWER_HEAD_TAGS, center=HEAD_C)
        solids += ss
        solids += sweep(path, lifted(CROWN, DZ), CROWN_TAGS, center=HEAD_C)[0]
        for cx, sx in ((xa, -1), (xb, 1)):
            for cy, sy in ((ya, -1), (yb, 1)):
                solids += kit.step_pyramid(cx - sx * 0.9, cy - sy * 0.9, dz=DZ)
        for a, b, t, n in segs:
            solids += kit.step_gable(a, t, n, (b - a).length / 2, dz=DZ)
        solids += self._pinnacle()                                      # 2. roof pinnacle
        for sy in (-1, 1):
            solids += self._flank(sy)                                   # 3. rune panels
            y = sy * 16.1                                               # 4. battered plinths
            for x0, x1 in ((-13.9, -8.3), (-2.5, 3.1)):   # the slab: x -13.9..3.1
                solids += kit.talus([(x0, y), (x1, y)], course=False, low=True)
        return solids

    @staticmethod
    def _pinnacle():
        """A gilded stepped pinnacle on the roof's flat top (over its square vent): hexagon-chain
        tier, bronze step, a tier with the triangle frieze, a plain tier and a squat point."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft
        cx, cy, z0 = ROOF_TOP

        def R(h, z, ch):
            return box_rings((cx - h, cx + h), (cy - h, cy + h), z, ch)

        def sides(tag, other="stoneB"):              # chamfered ring: odd sides are the chamfers
            return [tag if k % 2 == 0 else other for k in range(8)]
        rings = [R(6.6, z0 - 0.2, 0.8), R(6.1, z0 + 4.6, 0.7), R(6.5, z0 + 4.6, 0.7), R(6.5, z0 + 5.8, 0.7),
                 R(4.8, z0 + 5.8, 0.6), R(4.4, z0 + 9.8, 0.5), R(3.2, z0 + 9.8, 0.4), R(2.9, z0 + 12.6, 0.35),
                 R(2.0, z0 + 12.6, 0.3)]
        tags = [sides("hex"), "trim", "trim", "top", sides("tri"), "top", "stoneA", "top"]
        out = [loft(rings, tags, cap0=("top", False), cap1=("top", False))]
        top = rings[-1]
        out.append(loft([top, [V((cx, cy, z0 + 17.0))] * len(top)], ["trim"], cap0=("top", False), cap1=("top", False)))
        return out

    @staticmethod
    def _flank(sy):
        """A rune panel between bronze bands on the tower's side, above the stepped slabs and
        between the chamfered corners (x -11.4..0.6, wall at |y| 12.0)."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        a, t, n = V((-5.4, sy * 12.0, 0)), V((1, 0, 0)), V((0, sy, 0))
        return [
            prism_uz(a, t, n, [(-5.4, 61.0), (5.4, 61.0), (5.4, 62.0), (-5.4, 62.0)], -0.4, 1.1,
                     ["stoneB", "trim", "top", "trim"], "trim", None),
            prism_uz(a, t, n, [(-5.1, 62.0), (5.1, 62.0), (5.1, 67.0), (-5.1, 67.0)], -0.4, 0.8,
                     [None, "stoneB", None, "stoneB"], "rune", None),
            prism_uz(a, t, n, [(-5.4, 67.0), (5.4, 67.0), (5.4, 68.0), (-5.4, 68.0)], -0.4, 1.1,
                     ["stoneB", "trim", "top", "trim"], "trim", None),
            prism_uz(a, t, n, [(-3.0, 68.0), (3.0, 68.0), (0.0, 71.2)], -0.4, 0.7,
                     [None, "top", "top"], "tri|a", None),
        ]

    def emphasis(self, c, n):
        if c.z > 104:
            return 1.45                       # head, crown and pinnacle: what the RTS camera sees
        return 1.0
