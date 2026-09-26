"""Dwarven wall gate (DwarvenWallGateSmall, model DBWallGateN_SKN): an Erebor gate. EA's two gate
towers keep their shafts, their pointed door reliefs and their heads of bronze shield panels; the
new gatehouse spans the gap between them over the door: a bridge block carrying a deep stepped
pointed arch on both faces (two recessed rings with the triangle frieze and bronze reveals, then a
frame out to the towers), a rune lintel with Erebor-blue enamel over the door and a stepped relief
in the tympanum, a hexagon cornice, chevron merlons, and a stepped rune crown with a gilded point
over the middle, flanked by two banner poles on the walkway. The towers get the fortress's crown
(battered crown ring, stepped pyramids on the corners, a chevron merlon mid-side, a stepped roof
with a gilded point over EA's timber roof) and a long banner on each face that looks out of the wall.

Skinned model: the door (mesh DOOR on bone DOOR, x +-4, y +-40, z 0..45) drops 42.7 into the
ground to open (DBWallGateN_SKL.DBWallGateN_OPN) and rises again to close; it never moves up or
sideways. Everything new stays above z 45.6 over it or outside x +-4.4 beside it, so the door and
its travel stay clear; the passage units use when the gate is open (y +-20) stays clear too.

All numbers are DBWALLGATEN mesh coordinates (its pivot is the identity) measured on the original.
The wall runs along Y and meets the towers' outer faces at y +-58.2 (x +-8.3, up to z 53): nothing
is added there.
"""
from sagekit.building import Building

from ..style import DwarvenStyle

TOWER_IN, TOWER_OUT = 39.8, 58.2         # the towers' inner / outer faces (|y|), shafts x +-9.2 to z 71
TOWER_Y = 49.0                           # tower centre line
HEAD_TOP = 96.8                          # head rim (x +-12.2, |y| 36.8..61.2); roof floor 94.8
SHAFT_X = 9.2
DOOR_X, DOOR_TOP = 4.0, 45.0
BRIDGE = (45.6, 66.0)                    # the new bridge block over the door, x +-9.2
# the arch (half outline from the axis y 0): jamb foot, spring, shoulder, point
ARCH = [(33.0, 0.0), (33.0, 46.5), (22.0, 54.5), (0.0, 59.0)]
RINGS = (0.0, 2.2, 4.4)                  # ring offsets; the frame fills from 4.4 out to the towers
RING_X = (10.0, 10.8, 11.6)              # ring fronts (and the frame's)
JAMB_BACK = 4.4                          # the jamb blocks reach back to just in front of the door
LINTEL = 27.5                            # the rune lintel's half length
CORNICE_X = 12.15                        # the cornice's front, over the arch frame (x +-11.6)
# tower crowns: the fortress CROWN lowered onto the head rim, round a square path +-9.85
CROWN_PATH = 9.85
DZ = HEAD_TOP - 110.8
CROWN = [(-2.9, 110.8), (2.3, 110.8), (1.6, 114.8), (1.6, 115.3), (0.6, 115.3), (0.2, 117.4), (-0.6, 117.4),
         (-1.6, 116.2), (-2.9, 116.2)]
CROWN_TAGS = [None, "stoneB", "trim", "top", "stoneA", "top", "top", "top", "stoneA"]
ROOF = [(6.6, 6.4, 3.8, "rune"), (6.8, 6.8, 0.6, "trim"), (5.2, 5.0, 4.0, "tri"), (5.4, 5.4, 0.6, "trim"),
        (4.0, 3.8, 3.0, "stoneA")]
# banners: one down each tower face that looks out of the wall (x +-9.2), hung free 1.9 out,
# the rod under the head's flare, the point above the door relief's peak (z 41)
TOWER_BANNER = (70.6, 7.0, 26.0, 1.9)    # (z_top, width, length, d)
POLE_Y, POLE_TOP = 15.0, 94.0            # banner poles on the walkway either side of the crown
MERLONS = [(17.3, 24.8), (24.8, 32.3), (32.3, 39.8)]   # |y| spans of the chevron merlons


class WallGate(Building):
    style = DwarvenStyle()
    source = "DBWallGateN_SKN"
    target = "DBWALLGATEN"
    own_textures = {"DBFortress1.tga": "DBFortressQ.tga"}
    views = {
        "rts": ((0, 0, 50), 420, 50, -38, 50),
        "close": ((0, 0, 58), 210, 18, -24, 45),
        "ingame": ((0, 0, 45), 900, 53, -62, 50),
    }

    def design(self, kit):
        s = []
        s += self._bridge()                                              # 1. bridge, cornice
        for sx in (-1, 1):
            s += self._arch(kit, sx)                                     # 2. pointed arch frames
            s += self._tympanum(sx)                                      # 3. rune lintel, relief
            s += self._merlons(sx)                                       # 4. chevron merlons
        s += self._crown()                                               # 5. the gate's crown
        for sy in (-1, 1):
            s += self._tower_crown(kit, sy)                              # 6. tower crowns
        s += self._banners(kit)                                          # 7. banners, poles
        return s

    # ------------------------------------------------------------------ gatehouse
    @staticmethod
    def _bridge():
        from sagekit.blender.geometry import box_rings, loft
        z0, z1 = BRIDGE
        y = TOWER_IN
        out = [loft([box_rings((-SHAFT_X, SHAFT_X), (-y, y), z0, 0), box_rings((-SHAFT_X, SHAFT_X), (-y, y), z1, 0)],
                    [["stoneB", "stoneA", "stoneB", "stoneA"]], cap0=("stoneB", True), cap1=("top", False))]
        f = RING_X[-1]                       # the cornice stands on the arch frame's top
        c = [box_rings((-f, f), (-y, y), z1 - 1.6, 0), box_rings((-f - 0.3, f + 0.3), (-y, y), z1 - 1.0, 0),
             box_rings((-f - 0.3, f + 0.3), (-y, y), z1 + 0.8, 0), box_rings((-CORNICE_X, CORNICE_X), (-y, y), z1 + 0.8, 0),
             box_rings((-CORNICE_X, CORNICE_X), (-y, y), z1 + 1.5, 0)]
        side = lambda tg: ["stoneB", tg, "stoneB", tg]                  # noqa: E731  (ends: past the towers' x +-9.2)
        out.append(loft(c, [side("trim"), side("hex"), side("trim"), side("trim")], cap0=("top", False), cap1=("top", True)))
        return out

    @staticmethod
    def _arch(kit, sx):
        """The stepped pointed frame on the sx face: rings stepping forward round the arch outline
        (triangle frieze on their fronts, bronze reveals), then a frame out to the towers and up to
        the cornice, every piece standing on the plane of the towers' faces (x +-9.2): on the
        bridge above the spring, on a stone jamb block (back to the door) below it."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft
        out = []
        z_top = BRIDGE[1] - 1.6

        def piece(poly, xf, tags, front, jamb, xb=SHAFT_X, back=False):
            for sy in (1, -1):
                r0 = [V((sx * xb, sy * y, z)) for y, z in poly]
                r1 = [V((sx * xf, sy * y, z)) for y, z in poly]
                out.append(loft([r0, r1], [tags], cap0=("stoneB", back), cap1=(front or "stoneB", front is not None)))
        j = ARCH[0][0]                        # the jamb block: plain stone from the door to the rings
        piece([(j, 0.0), (TOWER_IN, 0.0), (TOWER_IN, BRIDGE[0] + 0.4), (j, BRIDGE[0] + 0.4)], SHAFT_X,
              ["top", "stoneB", "stoneB", "stoneB"], None, True, xb=JAMB_BACK, back=True)
        for i in range(len(RINGS)):
            inner = kit.arch_offset(ARCH, RINGS[i])
            xf = RING_X[i]
            if i < len(RINGS) - 1:
                outer = kit.arch_offset(ARCH, RINGS[i + 1])
                for k in range(3):
                    jamb = k == 0
                    out_tag = "stoneB" if jamb else None
                    piece([inner[k], outer[k], outer[k + 1], inner[k + 1]], xf,
                          [None if not jamb else "top", out_tag, None, "trim|a"], "tri|a", jamb)
            else:
                j0, j1, sh, ap = inner
                oy = TOWER_IN
                # the towers' inner faces (y +-39.8) stop at x +-9.2: the frame's outer sides show beyond
                piece([j0, (oy, 0.0), (oy, j1[1]), j1], xf, [None, "stoneB", "top", "trim|a"], "stoneB", True)
                piece([j1, (oy, j1[1]), (oy, z_top), (sh[0], z_top), sh], xf, [None, "stoneB", None, None, "trim|a"],
                      "stoneB", False)
                piece([sh, (sh[0], z_top), (0.0, z_top), ap], xf, [None, None, None, "trim|a"], "stoneB", False)
        return out

    @staticmethod
    def _tympanum(sx):
        """Inside the arch over the door: a rune lintel (Erebor-blue enamel, gold runes) between
        bronze edges, and a stepped triangle relief over it, all on the bridge's face."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        a, t, n = V((sx * SHAFT_X, 0, 0)), V((0, sx, 0)), V((sx, 0, 0))
        z0 = BRIDGE[0]
        L = LINTEL                            # inside the arch's shoulders at its top (z 49.4)
        out = [prism_uz(a, t, n, [(-L, z0), (L, z0), (L, z0 + 0.6), (-L, z0 + 0.6)], 0, 0.75,
                        ["stoneB", "trim", "top", "trim"], "trim", None),
               prism_uz(a, t, n, [(-L, z0 + 0.6), (L, z0 + 0.6), (L, z0 + 3.2), (-L, z0 + 3.2)], 0, 0.6,
                        [None, "trim", None, "trim"], "rune", None),
               prism_uz(a, t, n, [(-L, z0 + 3.2), (L, z0 + 3.2), (L, z0 + 3.8), (-L, z0 + 3.8)], 0, 0.75,
                        [None, "trim", "top", "trim"], "trim", None)]
        zs = z0 + 3.8
        for h, dz, tag, d in ((17.0, 2.1, "stoneA", 0.6), (11.5, 2.0, "tri|a", 0.5), (6.5, 1.8, "trim", 0.4)):
            out.append(prism_uz(a, t, n, [(-h, zs), (h, zs), (h, zs + dz), (-h, zs + dz)], 0, d,
                                [None, "stoneB", "top", "stoneB"], tag, None))
            zs += dz
        out.append(prism_uz(a, t, n, [(-6.5, zs), (6.5, zs), (0.0, zs + 2.6)], 0, 0.4, [None, "top", "top"], "stoneA", None))
        return out

    @staticmethod
    def _merlons(sx):
        from mathutils import Vector as V

        from ..wall_tower.crown import chevron
        a, t, n = V((sx * (CORNICE_X - 0.25), 0, 0)), V((0, sx, 0)), V((sx, 0, 0))
        z0 = BRIDGE[1] + 1.5
        out = []
        for y0, y1 in MERLONS:
            for sy in (-1, 1):
                u = sx * sy * (y0 + y1) / 2
                out += chevron(a, t, n, u, z0, y1 - y0, -2.2, 0.0, s=0.85)
        return out

    @staticmethod
    def _crown():
        """The gate's crown over the middle of the bridge: a rune tier, bronze cornice, a tier with
        the triangle frieze, a hexagon tier, then a gilded point."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft
        z = BRIDGE[1] + 1.5

        def R(hx, hy, zz, ch=0.5):
            return box_rings((-hx, hx), (-hy, hy), zz, ch)
        rings = [R(11.2, 12.0, z), R(11.0, 11.8, z + 5.2), R(11.6, 12.4, z + 5.2), R(11.6, 12.4, z + 6.0),
                 R(8.2, 9.6, z + 6.0), R(8.0, 9.4, z + 10.6), R(8.5, 9.9, z + 10.6), R(8.5, 9.9, z + 11.3),
                 R(6.4, 6.6, z + 11.3), R(6.2, 6.4, z + 14.8), R(4.6, 4.8, z + 14.8, 0.35)]

        def f(tg, other="stoneB"):            # chamfered ring: sides 2 (+X) and 6 (-X) face out of the wall
            return [tg if k in (2, 6) else other for k in range(8)]
        tags = [f("rune"), "top", "trim", "top", f("tri"), "top", "trim", "top", ["hex" if k % 2 == 0 else "stoneB" for k in range(8)], "top"]
        out = [loft(rings, tags, cap0=("top", False), cap1=("top", False))]
        top = rings[-1]
        out.append(loft([top, [V((0, 0, z + 21.5))] * len(top)], ["trim"], cap0=("top", False), cap1=("top", False)))
        return out

    # ------------------------------------------------------------------ towers
    @staticmethod
    def _tower_crown(kit, sy):
        from sagekit.blender.geometry import sweep

        from ..wall_tower.crown import chevron, step_pyramid, ziggurat
        cy, h = sy * TOWER_Y, CROWN_PATH
        path = [(-h, cy - h), (h, cy - h), (h, cy + h), (-h, cy + h), (-h, cy - h)]
        ring, segs = sweep(path, [(d, z + DZ) for d, z in CROWN], CROWN_TAGS, center=(0, cy))
        out = list(ring)
        for a, b, t, n in segs:
            out += chevron(a, t, n, (b - a).length / 2, 117.4 + DZ - 0.4, 10.0, -1.8, 0.6)
        for px in (-1, 1):
            for py in (-1, 1):
                out += step_pyramid(px * (h - 0.5), cy + py * (h - 0.5), HEAD_TOP + 8.1, 0.7)
        roof, _ = ziggurat(0, cy, HEAD_TOP, ROOF, (2.8, 4.5))
        return out + roof

    # ------------------------------------------------------------------ cloth
    @staticmethod
    def _banners(kit):
        from mathutils import Vector as V
        z_top, width, length, d = TOWER_BANNER
        out = []
        for sx in (-1, 1):
            a, t, n = V((sx * SHAFT_X, 0, 0)), V((0, sx, 0)), V((sx, 0, 0))
            for sy in (-1, 1):
                out += kit.banner(a, t, n, sx * sy * TOWER_Y, z_top, width, length, d=d, free=True)
        for sy in (-1, 1):
            out += pole(kit, V((0, sy * POLE_Y, 0)), V((0, 1, 0)), V((1, 0, 0)), BRIDGE[1] + 1.5, POLE_TOP, 5.0, 14.0)
        return out

    def emphasis(self, c, n):
        if c.z > 90:
            return 1.4                        # tower crowns
        if abs(c.y) < TOWER_IN and c.z > 40:
            return 1.5                        # the gatehouse front and crown
        return 1.0


def pole(kit, a, t, n, z0, top, width, length):
    """shapes.banner_pole standing on z0 (the kit's stands on the ground): a stepped stone foot, a
    bronze pole with a gilded point, a banner hung free in front of it (facing n) from a crossbar.
    `a` is the pole's foot; t runs along the banner, t x n = -z."""
    from sagekit.blender.geometry import prism_uz

    def box(u0, u1, za, zb, d0, d1, tags, cap):
        return prism_uz(a, t, n, [(u0, za), (u1, za), (u1, zb), (u0, zb)], d0, d1, tags, cap, cap)
    out = [box(-1.6, 1.6, z0, z0 + 1.4, -1.6, 1.6, [None, "stoneB", "top", "stoneB"], "stoneB"),
           box(-1.1, 1.1, z0 + 1.4, z0 + 2.6, -1.1, 1.1, [None, "trim", "top", "trim"], "trim"),
           box(-0.45, 0.45, z0 + 2.6, top, -0.45, 0.45, [None, "trim", None, "trim"], "trim"),
           prism_uz(a, t, n, [(-0.8, top), (0.8, top), (0, top + 2.4)], -0.8, 0.8, ["trim", "trim", "trim"], "trim", "trim")]
    out += kit.banner(a, t, n, 0.0, top - 1.2, width, length, d=0.6, free=True)
    return out
