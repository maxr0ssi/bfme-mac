"""Dwarven castle-wall gate (DwarvenCastleWallGate, model DBWallGate): the old castle walls' gate as
an Erebor gatehouse matching the new wall gate (wall_gate): the two gate towers and a bridge over
the passage under one projecting head - stepped corbels, a rune band with Erebor-blue enamel,
the walls' bronze-banded coping and chevron merlons - a deep stepped pointed arch on both faces
round the passage (two rings with the triangle frieze and bronze reveals, then a frame), a rune
lintel and a stepped relief in the tympanum, stepped pyramids on the four outer corners, a
stepped rune roof on each tower, the gate's stepped crown with a gilded point over the passage,
two banner poles beside it and a long banner down each tower face. The wall stubs at both ends
are the old castle wall segment's section (oldwall_segment/wall.py) at this model's heights.

EA's model is an unfinished stand-in (one mesh GBWALLGATE, 210 triangles, painted from the
placeholder sheet "Dwarven Wall"; no door, no bones but its own): two gatehouse blocks
(|y| 53.4..98.39, x +-33.13, chamfered to x +-23.77 at the wall end; an upper storey overhanging
to x +-37.21 from z 42.77 to a roof at 71.25 that ramps down to the walkway) with the passage
between them open to the sky (|y| < 53.4 up to z 42.77, |y| < 43.0 above), and a wall stub at
each end (|y| 98.39..136.89, EA's castle-wall section with its walkway at 51.78). Its faces are
removed and every volume rebuilt on the faction atlas (oldwall_segment/wall.clear_target).

The passage stays clear: nothing new stands in |y| < 53.4 below z 42.8, and the arch opening
contains EA's (its jambs are the towers' inner faces, it springs at 42.8 where EA's opening
ends and rises over EA's sloped soffit); the new bridge over it starts at 45.96, the top of EA's
opening. The footprint is EA's (x +-37.21, y +-136.89) and the stubs' ends are the segment's
section. Height 71.3 -> 85.4 (+19.7 %).

All numbers are GBWALLGATE mesh coordinates (its pivot is the identity)."""
from sagekit.building import Building

from ..style import DwarvenStyle

FACE_X = 33.13                    # the towers' and bridge's face (EA's towers' lower face)
PASS_Y = 53.4                     # the passage's half width (the towers' inner faces)
BRIDGE_Z = 45.96                  # the bridge's underside: the top of EA's opening
CORNER_Y, END_Y, END_X = 86.09, 98.39, 23.77   # the towers' chamfers run to the wall end (EA's)
STUB_END = 136.88
WALK = 51.78                      # the stubs' walkway (EA's; the segment's is 51.91)
H = 60.0                          # the head's underside
ROOF = 66.0                       # the gatehouse roof
# the head round the front and the chamfers, (d out of the face, z) profiles with tags per edge, in
# three convex pieces (a sweep's end caps are fanned from their first point): the band, the bronze
# drip band, the coping. Their backs run inside the body.
HEAD = [
    ([(-1.2, H), (3.77, H), (3.77, H + 6.0), (-1.2, H + 6.0)], ["stoneB", "rune", None, None]),
    ([(-1.2, H + 6.0), (3.77, H + 6.0), (4.08, H + 6.3), (4.08, H + 7.4), (-1.2, H + 7.4)], [None, "trim", "trim", "trim", "stoneA"]),
    ([(-1.2, H + 7.4), (3.98, H + 7.4), (3.98, H + 11.0), (3.58, H + 11.4), (-1.2, H + 11.4)],
     [None, "stoneA", "trim", "top", "stoneA"]),
]
# the arch (half outline from the axis): jamb foot, spring, shoulder, point
ARCH = [(PASS_Y, -0.05), (PASS_Y, 42.8), (33.0, 51.4), (0.0, 56.0)]
RINGS = (0.0, 1.7, 3.4)           # ring offsets; the frame fills from 3.4 out to FRAME_Y
RING_X = (34.1, 35.0, 35.9)       # ring fronts (and the frame's)
FRAME_Y = 61.0
CORBELS = (64.5, 71.0, 77.5, 84.0)             # |y| of the head's corbels on the tower fronts
MERLONS = 8                       # chevron merlons per half face, |y| 18.6 .. 80.0
TOWER_Y = 74.0                    # tower roofs' centre
TOWER_ROOF = [(12.5, 12.2, 4.4, "rune"), (12.9, 12.9, 0.7, "trim"), (10.0, 9.7, 4.4, "tri"), (10.4, 10.4, 0.7, "trim"),
              (7.6, 7.3, 3.0, "stoneA")]      # then a gilded point (5.0, 4.8): top 84.0
TOWER_BANNER = (53.6, 8.0, 28.0, 1.9)          # (z_top, width, length, d) down each tower face
POLE_Y, POLE_TOP = 30.0, 80.0


class OldWallGate(Building):
    style = DwarvenStyle()
    source = "DBWallGate"
    target = "GBWALLGATE"
    sheet = "DBWall.tga"                                # EA's placeholder; no face samples it
    sheet_normal = None
    own_textures = {"DBWall.tga": "DBWalG.tga"}
    tri_budget = 12000
    views = {
        "rts": ((0, 0, 35), 480, 50, -38, 50),
        "close": ((0, 0, 48), 250, 18, -24, 45),
        "ingame": ((0, 0, 35), 950, 53, -62, 50),
    }

    def design(self, kit):
        from ..oldwall_segment.wall import clear_target, run
        clear_target(self.target)
        s = self._body()
        for sy in (1, -1):                                               # wall stubs
            y0, y1 = sorted((sy * END_Y, sy * STUB_END))
            c0, c1 = sorted((sy * 101.5, sy * STUB_END))
            pitch = (c1 - c0) / 4
            s += run(kit, y0, y1, WALK, foot=-0.05, corbels=[c0 + pitch * (i + 0.5) for i in range(4)], chev=(c0, c1))
        for sx in (1, -1):
            s += self._head(sx)
            s += self._arch(kit, sx)
            s += self._tympanum(sx)
            s += self._merlons(sx)
        s += self._top(kit)
        return s

    # ------------------------------------------------------------------ masses
    @staticmethod
    def _body():
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft, sweep
        out = []
        for sy in (1, -1):
            plan = [(FACE_X, PASS_Y), (FACE_X, CORNER_Y), (END_X, END_Y), (-END_X, END_Y), (-FACE_X, CORNER_Y), (-FACE_X, PASS_Y)]
            r0 = [V((x, sy * y, -0.05)) for x, y in plan]
            r1 = [V((x, sy * y, ROOF)) for x, y in plan]
            out.append(loft([r0, r1], [["stoneA", "stoneA", "stoneA", "stoneA", "stoneA", "stoneB"]],
                            cap0=("stoneB", False), cap1=("top", True)))
            for sx in (1, -1):                                           # plinth along the tower fronts
                path = [(sx * FACE_X, sy * FRAME_Y), (sx * FACE_X, sy * CORNER_Y), (sx * END_X, sy * END_Y)]
                prof = [(0.0, -0.05), (2.3, -0.05), (2.3, 0.8), (0.8, 5.8), (0.0, 6.3)]
                out += sweep(path, prof, [None, "stoneB", "stoneA", "top", None])[0]
            # the tower's end over the wall stub's walkway: a flush coping
            path = [(END_X, sy * END_Y), (-END_X, sy * END_Y)]
            prof = [(0.0, ROOF), (0.0, H + 11.0), (-0.4, H + 11.4), (-2.6, H + 11.4), (-2.6, ROOF)]
            out += sweep(path, prof, ["stoneA", "trim", "top", "stoneA", None])[0]
        r0 = [V((FACE_X, -PASS_Y, BRIDGE_Z)), V((FACE_X, PASS_Y, BRIDGE_Z)), V((-FACE_X, PASS_Y, BRIDGE_Z)),
              V((-FACE_X, -PASS_Y, BRIDGE_Z))]
        r1 = [V((p.x, p.y, ROOF)) for p in r0]
        out.append(loft([r0, r1], [["stoneA", None, "stoneA", None]], cap0=("stoneB", True), cap1=("top", True)))
        return out

    @staticmethod
    def _head(sx):
        """The projecting head along the front and the chamfers, with stepped corbels under it on
        the tower fronts."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz, sweep
        path = [(sx * END_X, -END_Y), (sx * FACE_X, -CORNER_Y), (sx * FACE_X, CORNER_Y), (sx * END_X, END_Y)]
        out = []
        for prof, tags in HEAD:
            out += sweep(path, prof, tags)[0]
        a, t, n = V((sx * FACE_X, 0, 0)), V((0, 1, 0)), V((sx, 0, 0))
        for yc in CORBELS:
            for y in (yc, -yc):
                for k, (z0, z1, d, hw) in enumerate(((H - 5.6, H - 3.6, 1.4, 1.35), (H - 3.6, H - 1.8, 2.6, 1.25),
                                                     (H - 1.8, H, 3.72, 1.15))):
                    out.append(prism_uz(a, t, n, [(y - hw, z0), (y + hw, z0), (y + hw, z1), (y - hw, z1)], -0.5, d,
                                        ["stoneB", "stoneB", None if k == 2 else "top", "stoneB"], "stoneB", None))
        return out

    # ------------------------------------------------------------------ the arch
    @staticmethod
    def _arch(kit, sx):
        """The stepped pointed frame on the sx face, standing on the face plane: rings stepping
        forward round the arch (triangle frieze on their fronts, bronze reveals), then a frame out to
        FRAME_Y and up to the head. Pieces over the passage keep their backs (seen from inside)."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft
        out = []

        def piece(poly, xf, tags, front, back):
            for sy in (1, -1):
                r0 = [V((sx * FACE_X, sy * y, z)) for y, z in poly]
                r1 = [V((sx * xf, sy * y, z)) for y, z in poly]
                out.append(loft([r0, r1], [tags], cap0=(back or "stoneB", back is not None),
                                cap1=(front or "stoneB", front is not None)))
        for i in range(len(RINGS)):
            inner = kit.arch_offset(ARCH, RINGS[i])
            xf = RING_X[i]
            if i < len(RINGS) - 1:
                outer = kit.arch_offset(ARCH, RINGS[i + 1])
                for k in range(3):
                    jamb = k == 0
                    piece([inner[k], outer[k], outer[k + 1], inner[k + 1]], xf,
                          [None, None, None, "trim|a"], "tri|a",
                          None if jamb else "stoneB")
            else:
                j0, j1, sh, ap = inner
                oy = FRAME_Y
                piece([j0, (oy, j0[1]), (oy, j1[1]), j1], xf, [None, "stoneB", None, "trim|a"], "stoneB", None)
                piece([j1, (oy, j1[1]), (oy, H), (sh[0], H), sh], xf, [None, "stoneB", None, None, "trim|a"], "stoneB", "stoneB")
                piece([sh, (sh[0], H), (0.0, H), ap], xf, [None, None, None, "trim|a"], "stoneB", "stoneB")
        return out

    @staticmethod
    def _tympanum(sx):
        """Inside the arch over the passage: a rune lintel (Erebor-blue enamel, gold runes) between
        bronze edges and a stepped relief over it, on the bridge's face."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        a, t, n = V((sx * FACE_X, 0, 0)), V((0, sx, 0)), V((sx, 0, 0))
        z0, L = BRIDGE_Z, 30.0
        out = [prism_uz(a, t, n, [(-L, z0), (L, z0), (L, z0 + 0.6), (-L, z0 + 0.6)], 0, 0.75,
                        ["stoneB", "trim", "top", "trim"], "trim", None),
               prism_uz(a, t, n, [(-L, z0 + 0.6), (L, z0 + 0.6), (L, z0 + 3.2), (-L, z0 + 3.2)], 0, 0.6,
                        [None, "trim", None, "trim"], "rune", None),
               prism_uz(a, t, n, [(-L, z0 + 3.2), (L, z0 + 3.2), (L, z0 + 3.8), (-L, z0 + 3.8)], 0, 0.75,
                        [None, "trim", "top", "trim"], "trim", None)]
        zs = z0 + 3.8
        for h, dz, tag, d in ((26.0, 1.1, "stoneA", 0.6), (19.0, 1.0, "tri|a", 0.5), (12.0, 0.9, "trim", 0.4)):
            out.append(prism_uz(a, t, n, [(-h, zs), (h, zs), (h, zs + dz), (-h, zs + dz)], 0, d,
                                [None, "stoneB", "top", "stoneB"], tag, None))
            zs += dz
        out.append(prism_uz(a, t, n, [(-12.0, zs), (12.0, zs), (0.0, zs + 2.5)], 0, 0.4, [None, "top", "top"], "stoneA", None))
        return out

    # ------------------------------------------------------------------ the top
    @staticmethod
    def _merlons(sx):
        from mathutils import Vector as V

        from ..wall_tower.crown import chevron
        a, t, n = V((sx * FACE_X, 0, 0)), V((0, sx, 0)), V((sx, 0, 0))
        y0, y1 = 18.6, 80.0
        w = (y1 - y0) / MERLONS
        out = []
        for i in range(MERLONS):
            for sy in (1, -1):
                out += chevron(a, t, n, sx * sy * (y0 + (i + 0.5) * w), H + 11.0, w, -1.0, 3.98)
        return out

    @staticmethod
    def _top(kit):
        """Corner pyramids, the towers' stepped roofs, the gate's crown, banners and poles."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft

        from ..wall_gate.building import pole
        from ..wall_tower.crown import step_pyramid, ziggurat
        out = []
        for sy in (1, -1):
            for sx in (1, -1):
                out += step_pyramid(sx * 31.0, sy * 86.6, ROOF, 1.5)
            out += ziggurat(0.0, sy * TOWER_Y, ROOF, TOWER_ROOF, (5.0, 4.8))[0]
            out += pole(kit, V((0, sy * POLE_Y, 0)), V((0, 1, 0)), V((1, 0, 0)), ROOF, POLE_TOP, 5.5, 15.0)

        def R(hx, hy, z, ch=0.6):
            return box_rings((-hx, hx), (-hy, hy), z, ch)
        z = ROOF
        rings = [R(16.2, 17.4, z), R(16.0, 17.2, z + 5.6), R(17.0, 18.2, z + 5.6), R(17.0, 18.2, z + 6.5),
                 R(12.5, 13.7, z + 6.5), R(12.2, 13.4, z + 11.0), R(12.9, 14.1, z + 11.0), R(12.9, 14.1, z + 11.7),
                 R(9.2, 9.7, z + 11.7), R(9.0, 9.5, z + 15.0), R(6.7, 7.0, z + 15.0, 0.5)]

        def f(tg, other="stoneB"):            # chamfered ring: sides 2 (+X) and 6 (-X) face out of the wall
            return [tg if k in (2, 6) else other for k in range(8)]
        tags = [f("rune"), "top", "trim", "top", f("tri"), "top", "trim", "top", ["hex" if k % 2 == 0 else "stoneB" for k in range(8)], "top"]
        out.append(loft(rings, tags, cap0=("top", False), cap1=("top", False)))
        out.append(loft([rings[-1], [V((0, 0, z + 19.3))] * len(rings[-1])], ["trim"], cap0=("top", False), cap1=("top", False)))
        z_top, width, length, d = TOWER_BANNER
        for sx in (1, -1):
            a, t, n = V((sx * FACE_X, 0, 0)), V((0, sx, 0)), V((sx, 0, 0))
            for sy in (1, -1):
                out += kit.banner(a, t, n, sx * sy * TOWER_Y, z_top, width, length, d=d, free=True)
        return out

    def emphasis(self, c, n):
        if c.z > 60:
            return 1.4                        # head, merlons, roofs and crown
        if abs(c.y) < FRAME_Y and c.z > 38:
            return 1.5                        # the arch, tympanum and bridge front
        return 1.0
