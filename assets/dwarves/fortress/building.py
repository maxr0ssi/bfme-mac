"""The Dwarven fortress (DwarvenFortressCitadel): solid chevron parapets, stepped tower crowns,
battered gatehouse pylons with king pillars, and a deep pointed gate arch. All measurements are
in DBFORTRESS mesh coordinates, taken from the original model."""
from sagekit.building import Building
from sagekit.taxonomy import Tier

from ..style import DwarvenStyle

TOWERS = [(22.2, 49.7, 24.8, 52.4), (22.2, 49.7, -53.0, -25.5),
          (-51.2, -23.7, 24.8, 52.4), (-51.2, -23.7, -53.0, -25.5)]   # tower-head core boxes, top 108.7
TOWER_CENTRES = [(35.95, 38.6), (35.95, -39.25), (-37.45, 38.6), (-37.45, -39.25)]
# wall runs: (path, segments that carry a chevron parapet)
WALLS = [
    ([(-26.5, -50.3), (25.0, -50.3)], [0]),
    ([(-26.5, 49.7), (25.0, 49.7)], [0]),
    ([(46.0, -50.3), (49.1, -50.3), (75.13, -24.0)], [1]),
    ([(46.0, 49.7), (49.1, 49.7), (74.55, 24.0)], [1]),
    ([(-47.5, -50.3), (-50.9, -50.3), (-91.3, -9.5), (-91.3, 8.9), (-50.9, 49.7), (-47.5, 49.7)], [1, 2, 3]),
]
LONG_WALLS = [[(-26.5, -50.3), (25.0, -50.3)], [(-26.5, 49.7), (25.0, 49.7)]]
LOW_WALLS = [[(49.1, -50.3), (75.13, -24.0)], [(49.1, 49.7), (74.55, 24.0)],
             [(-50.9, -50.3), (-91.3, -9.5), (-91.3, 8.9), (-50.9, 49.7)]]
# tower head: two-step corbel + hexagon frieze, then a battered, stepped crown ring
TOWER_HEAD = [(0, 105.2), (1.1, 106.2), (1.1, 106.6), (2.3, 107.6), (2.3, 110.4), (1.9, 110.8), (-2.9, 110.8),
              (-2.9, 108.7)]
TOWER_HEAD_TAGS = ["trim", "stoneB", "trim", "hex", "trim", None, "stoneA", "stoneB"]
CROWN = [(-2.9, 110.8), (2.3, 110.8), (1.6, 114.8), (1.6, 115.3), (0.6, 115.3), (0.2, 117.4), (-0.6, 117.4),
         (-1.6, 116.2), (-2.9, 116.2)]
CROWN_TAGS = [None, "stoneB", "trim", "top", "stoneA", "top", "top", "top", "stoneA"]
# the gate: axis 0.3 off y=0, lintel underside 44.2; half the original arch from the axis (jamb
# foot, jamb top, shoulder top, point). The flame upgrade (DBFFlam) stands a brazier column on each
# side at x 80.8..90.4, |y| 10.7..19.6, cups at z 48..56: the jambs take the columns, the lintel
# and crown stop inside them (GATE_Y) and the pylons start outside them (BRAZIER_Y)
GATE_Y, BRAZIER_Y = 10.4, 19.8
GATE_AXIS, GATE_OUT, GATE_LINTEL = -0.3, BRAZIER_Y, 44.2
ARCH = [(11.8, 0.0), (11.8, 21.5), (8.5, 35.0), (0.0, 38.0)]
# the shield sigil: a double chevron under a bar, on each tower's bronze shields
SIGIL = [((-2.3, 91.0), (0.0, 86.4)), ((0.0, 86.4), (2.3, 91.0)), ((-1.2, 91.0), (0.0, 88.6)), ((0.0, 88.6), (1.2, 91.0)),
         ((-2.7, 91.9), (2.7, 91.9)), ((0.0, 91.9), (0.0, 93.0))]


class Fortress(Building):
    style = DwarvenStyle()
    source = "DBFortress"
    target = "DBFORTRESS"
    tier = Tier.HERO
    own_textures = {"DBFortress1.tga": "DBFortressH.tga"}      # already in players' caches
    bake_hidden = ("DBFBANNER", "P1")
    views = {                                                   # round 1's cameras (the before shots)
        "rts": ((20, 0, 40), 560, 50, -38, 50),
        "close": ((68, -14, 62), 330, 24, -30, 45),
        "ingame": ((20, 0, 30), 1300, 53, -62, 50),
        "gate": ((86, -2, 30), 120, 8, 12, 40),
        "tower": ((36, -40, 106), 60, 28, -55, 45),
    }

    def design(self, kit):
        from sagekit.blender.geometry import loft, rect_ring, sweep
        solids = []
        for path, segments in WALLS:                                       # 1. solid chevron parapets
            solids += kit.parapet_run(path, segments)
        prof = [(0, 3.6), (16, 3.6), (19, 2.4), (33, 2.4), (36, 1.2), (52.2, 1.2)]
        for y0, ny in ((-50.3, -1), (49.7, 1)):                            # 2. stepped buttresses
            for xc in (-8.85, 8.35):
                rings = [rect_ring((xc, y0), (1, 0), (0, ny), -2.0, 2.0, -0.6, d, z, 0.4) for z, d in prof]
                solids.append(loft(rings, ["stoneB", "trim", "stoneB", "trim", "stoneA"],
                                   cap0=("top", False), cap1=("top", False)))
        for xa, xb, ya, yb in TOWERS:                                      # 3. tower crowns
            cen = ((xa + xb) / 2, (ya + yb) / 2)
            path = [(xa, ya), (xb, ya), (xb, yb), (xa, yb), (xa, ya)]
            ss, segs = sweep(path, TOWER_HEAD, TOWER_HEAD_TAGS, center=cen)
            solids += ss
            solids += sweep(path, CROWN, CROWN_TAGS, center=cen)[0]
            for cx, sx in ((xa, -1), (xb, 1)):
                for cy, sy in ((ya, -1), (yb, 1)):
                    solids += kit.step_pyramid(cx - sx * 0.9, cy - sy * 0.9)
            for a, b, t, n in segs:
                solids += kit.step_gable(a, t, n, (b - a).length / 2)
        for sy in (-1, 1):                                                 # 4. gatehouse pylons
            solids += self._pylon(sy)
        solids += self._lintel_and_crown()
        solids += kit.pointed_arch(ARCH, GATE_AXIS, GATE_OUT, GATE_LINTEL,  # 5. the pointed gate arch
                                   depths=(0.0, 1.9, 3.8, 5.4), xs=(83.1, 84.6, 86.1, 87.6, 88.0))
        for sy in (-1, 1):                                                 # 6. king pillars
            y0, y1 = sorted((sy * 20.2, sy * 27.0))
            solids += kit.king_pillar(92.2, y0, y1)
        for path in LONG_WALLS:                                            # 7. battered plinths
            solids += kit.talus(path)
        for path in LOW_WALLS:
            solids += kit.talus(path, course=False, low=True)
        return solids

    @staticmethod
    def _pylon(sy):
        """A battered gatehouse pylon: stepped plinth, rune belt at the walls' band height, pilaster
        ribs following the batter, corbelled frieze and a stepped squat cap."""
        from sagekit.blender.geometry import box_rings, loft

        def ring(x0, x1, y0, y1, z, ch):
            return box_rings((x0, x1), sorted((sy * y0, sy * y1)), z, ch)

        def body(z, e=0.0):                  # battered front x and outer |y| at height z
            return 95.0 - 1.5 * z / 56.0 + e, 28.5 - z / 56.0 + e
        out = []
        P = []
        for z, e in ((0.0, 1.8), (2.4, 1.8), (2.4, 0.9), (4.8, 0.9), (5.6, -0.05)):
            fx, oy = body(z, e)
            P.append(ring(68.0, fx, BRAZIER_Y, oy, z, 0.6))
        out.append(loft(P, ["stoneB", "top", "stoneB", "trim"], cap0=("top", False), cap1=("top", False)))
        B = []
        for z, e in ((43.3, -0.05), (44.0, 0.6), (51.0, 0.6), (51.7, -0.05)):
            fx, oy = body(z, e)
            B.append(ring(68.0, fx, BRAZIER_Y, oy, z, 0.5))
        outer = 4 if sy > 0 else 0          # chamfered ring sides: 0 y0-face, 2 front, 4 y1-face, 6 back
        out.append(loft(B, ["trim", ["rune" if k in (2, outer) else "stoneA" for k in range(8)], "trim"],
                        cap0=("top", False), cap1=("top", False)))
        for side, rect in ((2, lambda fx, oy: (fx - 1.0, fx + 0.7, 22.3, 24.7)),
                           (outer, lambda fx, oy: (81.4, 84.0, oy - 1.0, oy + 0.7))):
            rib = []
            for z in (5.6, 43.3):
                x0, x1, y0, y1 = rect(*body(z))
                rib.append(ring(x0, x1, y0, y1, z, 0.3))
            out.append(loft(rib, [["stoneB" if k != side else "pilaster" for k in range(8)]],
                            cap0=("top", False), cap1=("top", False)))
        R = [ring(69.0, 95.0, BRAZIER_Y, 28.5, 0.0, 0.8), ring(69.0, 93.5, BRAZIER_Y, 27.5, 56.0, 0.8),
             ring(68.3, 94.4, BRAZIER_Y, 28.4, 56.9, 0.8), ring(68.3, 94.4, BRAZIER_Y, 28.4, 59.6, 0.8),
             ring(68.9, 93.8, BRAZIER_Y + 0.2, 27.8, 60.2, 0.7), ring(71.5, 91.8, 20.2, 26.2, 60.2, 0.6),
             ring(71.5, 91.8, 20.2, 26.2, 65.6, 0.6), ring(73.0, 90.3, 21.2, 25.2, 65.6, 0.5),
             ring(77.5, 86.0, 22.0, 24.4, 69.2, 0.3)]
        out.append(loft(R, ["stoneB", "trim", "tri", "trim", "top", "stoneA", "top", "stoneA"],
                        cap0=("top", False), cap1=("top", True)))
        return out

    @staticmethod
    def _lintel_and_crown():
        """A lintel carrying a rune frieze over the gate, and a stepped crown. Both stop at the flame
        upgrade's brazier columns (DBFFlam), which stand between the lintel and the pylons."""
        from sagekit.blender.geometry import box_rings, loft
        Y = GATE_Y
        out = [loft([box_rings((83.3, 90.7), (-Y, Y), 44.2, 0), box_rings((83.3, 90.7), (-Y, Y), 51.0, 0)],
                    [["stoneA", "rune", "stoneA", "stoneA"]], cap0=("stoneA", True), cap1=("top", False))]

        def front(t):
            return ["stoneA", t, "stoneA", "stoneA"]
        crown = [box_rings((83.3, 90.7), (-Y, Y), 51.0, 0), box_rings((83.3, 91.5), (-Y, Y), 51.8, 0),
                 box_rings((83.3, 91.5), (-Y, Y), 59.0, 0), box_rings((83.3, 90.9), (-Y, Y), 59.6, 0),
                 box_rings((84.3, 90.0), (-8.6, 8.6), 59.6, 0), box_rings((84.3, 90.0), (-8.6, 8.6), 64.2, 0),
                 box_rings((84.6, 89.7), (-8.3, 8.3), 64.6, 0), box_rings((85.3, 89.2), (-6.0, 6.0), 64.6, 0),
                 box_rings((85.3, 89.2), (-6.0, 6.0), 68.4, 0), box_rings((86.0, 88.5), (-4.4, 4.4), 70.0, 0)]
        out.append(loft(crown, [front("trim"), front("tri"), "trim", "top", front("hex"), "trim", "top", "stoneB", "trim"],
                        cap0=("top", False), cap1=("top", True)))
        for sy in (-1, 1):                  # a capping slab on each jamb: the brazier cups' seat
            ys = sorted((sy * GATE_Y, sy * BRAZIER_Y))
            out.append(loft([box_rings((83.1, 88.6), ys, GATE_LINTEL, 0), box_rings((83.1, 88.6), ys, GATE_LINTEL + 0.8, 0)],
                            ["trim"], cap0=("top", False), cap1=("top", True)))
        return out

    def emphasis(self, c, n):
        if c.z > 85:
            return 1.45                       # tower heads and crowns
        if c.x > 60 and abs(c.y) < 36:
            return 1.45                       # gatehouse
        return 1.1 if c.z > 40 else 1.0

    def decals(self):
        from sagekit.paint.layers import StrokeSigil
        return [StrokeSigil(TOWER_CENTRES, SIGIL, zrange=(84, 94))]
