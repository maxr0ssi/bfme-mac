"""Dwarven fortress hall expansion (DwarvenHallExpansion): the fortress's tower crown on the hall's
head (battered crown ring, stepped-pyramid corners, stepped gables), a stepped ziggurat roof with
a gold rune belt in place of the flat carved pyramid, a stepped pointed frame round the door, rune
panels on the flanks and battered plinths at the foot of the side buttress slabs.

The hall stands on an expansion pad against the fortress: its -X side (the low connecting wall
x -55..-27) faces the fortress and is left as it is; nothing leaves the original bounding box.
All measurements in DBFGBUNK mesh coordinates, taken from the original model."""
from sagekit.building import Building

from ..style import DwarvenStyle

# the overhanging head: x -29.9..0.6, y -15.4..15.5, flat top at 85.1 (roof slope inside it rises
# to a plateau at 88.2, x -25.1..-4.2, |y| 10.5; the carved pyramid on it tops out at 93.9)
HEAD_TOP = 85.1
CORE = (-26.9, -2.4, -12.4, 12.5)            # crown path: 3.0 inside the head's edge
CORE_C = ((CORE[0] + CORE[1]) / 2, (CORE[2] + CORE[3]) / 2)
DZ = HEAD_TOP - 110.8                        # the fortress's tower-crown numbers, lowered onto the head
# crown ring profile (d outward from the core box, z): the fortress CROWN with a shallower inner
# face (the roof slope starts 1.6 in)
CROWN = [(-1.6, 85.1), (2.3, 85.1), (1.6, 89.1), (1.6, 89.6), (0.6, 89.6), (0.2, 91.7), (-0.6, 91.7),
         (-1.2, 90.6), (-1.6, 90.6)]
CROWN_TAGS = [None, "stoneB", "trim", "top", "stoneA", "top", "top", "top", "stoneA"]
# the door: a painted recess at x -0.2 (half outline from the axis y 0: |y| 6.6 up to 30.6,
# shoulders to 3.3/34.4) on a gabled slab (|y| 10, 33.7 -> 42.9); the new frame steps forward to
# x 0.6 (the head's front, the bounding box) with its inner ring just outside the opening
DOOR_ARCH = [(6.8, 0.0), (6.8, 30.8), (3.6, 35.2), (0.0, 37.4)]
DOOR_OUT, DOOR_LINTEL = 10.0, 42.4


class Hall(Building):
    style = DwarvenStyle()
    source = "DBFGBunk"
    target = "DBFGBUNK"
    sheet = None                                                # the faction atlas DBFortress1
    own_textures = {"DBFortress1.tga": "DBFortressG.tga"}       # the fortress owns DBFortressH
    views = {
        "rts": ((-18, 0, 48), 300, 50, -38, 50),
        "close": ((-14, 0, 58), 210, 22, -34, 45),
        "ingame": ((-18, 0, 40), 700, 53, -62, 50),
    }

    def design(self, kit):
        from sagekit.blender.geometry import sweep
        solids = []
        xa, xb, ya, yb = CORE                                           # 1. the tower crown
        path = [(xa, ya), (xb, ya), (xb, yb), (xa, yb), (xa, ya)]
        ring, segs = sweep(path, CROWN, CROWN_TAGS, center=CORE_C)
        solids += ring
        for cx, sx in ((xa, -1), (xb, 1)):
            for cy, sy in ((ya, -1), (yb, 1)):
                solids += kit.step_pyramid(cx - sx * 0.9, cy - sy * 0.9, dz=DZ)
        for a, b, t, n in segs:
            solids += kit.step_gable(a, t, n, (b - a).length / 2, dz=DZ)
        solids += self._ziggurat()                                      # 2. stepped roof
        solids += self._door_frame(kit)                                 # 3. door frame
        for sy in (-1, 1):
            solids += self._flank(sy)                                   # 4. rune panels
            y = sy * 15.8                                               # 5. battered plinths
            for x0, x1 in ((-23.3, -17.1), (-12.1, -6.1)):
                solids += kit.talus([(x0, y), (x1, y)], course=False, low=True)
        return solids

    @staticmethod
    def _ziggurat():
        """A battered, stepped roof block over the carved pyramid: rune belt, bronze step, a tier
        with the triangle frieze, a plain tier and a squat gilded point."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft
        cx, cy = CORE_C

        def R(h, z, ch):
            return box_rings((cx - h, cx + h), (cy - h, cy + h), z, ch)

        def sides(tag, other="stoneB"):              # chamfered ring: odd sides are the chamfers
            return [tag if k % 2 == 0 else other for k in range(8)]
        rings = [R(7.3, 88.0, 0.8), R(6.9, 93.0, 0.7), R(7.2, 93.0, 0.7), R(7.2, 94.2, 0.7),
                 R(5.6, 94.2, 0.6), R(5.2, 98.0, 0.5), R(3.8, 98.0, 0.45), R(3.5, 101.0, 0.4),
                 R(2.4, 101.0, 0.3)]
        tags = [sides("rune"), "trim", "trim", "top", sides("tri"), "top", "stoneA", "top"]
        out = [loft(rings, tags, cap0=("top", False), cap1=("top", False))]
        top = rings[-1]
        out.append(loft([top, [V((cx, cy, 104.5))] * len(top)], ["trim"], cap0=("top", False), cap1=("top", False)))
        return out

    @staticmethod
    def _door_frame(kit):
        """The pointed stepped door frame (the fortress gate's, in the 0.8 units the head's front
        leaves): two recessed rings with the triangle frieze and bronze reveals, then a frame slab
        out to the door slab's edges, capped by a lintel. Every piece starts on the slab (x -0.2),
        so no step leaves a gap; outer sides, tops and backs are real faces (nothing abuts them, and
        with only 0.4-0.8 of depth an open back would be seen from the sky past the slab's edge)."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft
        x0 = -0.2
        out = []

        def piece(poly, x1, tags, front):
            for side in (1, -1):
                r0 = [V((x0, side * y, z)) for y, z in poly]
                r1 = [V((x1, side * y, z)) for y, z in poly]
                out.append(loft([r0, r1], [tags], cap0=("stoneB", True), cap1=(front, True)))
        depths, xs = (0.0, 1.3, 2.6), (0.2, 0.4)
        for i in range(2):
            inner, outer = kit.arch_offset(DOOR_ARCH, depths[i]), kit.arch_offset(DOOR_ARCH, depths[i + 1])
            for k in range(3):
                piece([inner[k], outer[k], outer[k + 1], inner[k + 1]], xs[i], [None, None, None, "trim|a"], "tri|a")
        j0, j1, sh, ap = kit.arch_offset(DOOR_ARCH, depths[-1])
        oy, lz = DOOR_OUT, DOOR_LINTEL
        piece([j0, (oy, 0.0), (oy, j1[1]), j1], 0.6, [None, "stoneB", None, "trim|a"], "stoneB")
        piece([j1, (oy, j1[1]), (oy, lz), (sh[0], lz), sh], 0.6, [None, "stoneB", "top", None, "trim|a"], "stoneB")
        piece([sh, (sh[0], lz), (0.0, lz), ap], 0.6, [None, "top", None, "trim|a"], "stoneB")
        return out

    @staticmethod
    def _flank(sy):
        """A rune panel between bronze bands on the tower's side, over the stepped slabs and
        between the chamfered corners (x -20.7..-8.5, wall at |y| 12.2)."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        a, t, n = V((-14.6, sy * 12.2, 0)), V((1, 0, 0)), V((0, sy, 0))
        return [
            prism_uz(a, t, n, [(-5.9, 47.6), (5.9, 47.6), (5.9, 48.6), (-5.9, 48.6)], -0.4, 1.1,
                     ["stoneB", "trim", "top", "trim"], "trim", None),
            prism_uz(a, t, n, [(-5.6, 48.6), (5.6, 48.6), (5.6, 53.4), (-5.6, 53.4)], -0.4, 0.8,
                     [None, "stoneB", None, "stoneB"], "rune", None),
            prism_uz(a, t, n, [(-5.9, 53.4), (5.9, 53.4), (5.9, 54.4), (-5.9, 54.4)], -0.4, 1.1,
                     ["stoneB", "trim", "top", "trim"], "trim", None),
            prism_uz(a, t, n, [(-3.2, 54.4), (3.2, 54.4), (0.0, 57.6)], -0.4, 0.7,
                     [None, "top", "top"], "tri|a", None),
        ]

    def emphasis(self, c, n):
        if c.z > 84:
            return 1.45                       # crown and roof: what the RTS camera sees
        if c.x > -2.0 and c.z < 46:
            return 1.3                        # the door frame
        return 1.0
