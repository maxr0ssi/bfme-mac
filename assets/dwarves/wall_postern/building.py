"""Dwarven postern gate (DwarvenWallPosternGateSmall, model DBWallPGN): a small gate that straddles a
wall segment. The model is only the two porches (mesh OBJECT01); the wall through them is the wall
segment's own model DBWallN, drawn by the same object (ModuleTag_DrawWall, wall_segment's recipe).
Each porch keeps EA's shouldered doorway with its triangle-frieze reveal and gains a small Erebor
gatehouse front: a stepped pointed frame round the doorway (two recessed rings with the triangle
frieze and bronze reveals, then a frame slab), a corbelled hexagon cornice, a stepped gable with a
gilded point; its corner pillars are crowned with stepped pyramids, and a banner pole stands on
each of the low blocks either side of the door.

All numbers are OBJECT01 mesh coordinates measured on the original, symmetric in x and y. The
wall runs along Y through x +-8.3 up to z 53: the porches (x +-3.3..+-15.7, |y| <= 10.6, top 40.8)
stand against both its faces, so nothing new sits inside |x| < 8.3 and nothing rises to the
wall's top (the height limit, +20 %, is z 48.96 anyway).
"""
from sagekit.building import Building

from ..style import DwarvenStyle

FRONT = 15.7                    # porch front (x), EA's doorway reveal from 13.3 to here
TOP = 40.7                      # porch top (|y| <= 7.9; the sides lean in from |y| 10.6 at z 25)
WALL = 8.3                      # the wall's faces
# the doorway at the porch front: |y| 7.6 up to z 21.5, shoulders in to 5.5 at z 35, flat top.
# The new frame's inner outline stands just outside it, rising to a point over the flat top
ARCH = [(7.8, 0.0), (7.8, 21.2), (5.8, 35.1), (0.0, 36.9)]
RINGS, RING_X = (0.0, 1.3, 2.6), (16.3, 16.9, 17.5)
FRAME_Y = 11.4                  # the frame slab's outer edge (the rings end at 10.4)
PILLAR = (19.65, 14.8, 13.5)    # front corner blocks (x 16.6..22.7, |y| 12.1..17.5): centre, top
POLE = (12.0, 14.8, 14.9)       # banner poles on the low side blocks (x 4.5..16.8, |y| 10.6..19, top 14.9)


class WallPostern(Building):
    style = DwarvenStyle()
    source = "DBWallPGN"
    target = "OBJECT01"
    own_textures = {"DBFortress1.tga": "DBFortressP.tga"}
    views = {
        "rts": ((0, 0, 20), 190, 50, -38, 50),
        "close": ((12, 0, 24), 110, 20, -30, 45),
        "ingame": ((0, 0, 20), 450, 53, -62, 50),
    }

    def design(self, kit):
        s = []
        for sx in (-1, 1):
            s += self._frame(kit, sx)
            s += self._crown(sx)
            for sy in (-1, 1):
                from ..wall_tower.crown import step_pyramid
                s += step_pyramid(sx * PILLAR[0], sy * PILLAR[1], PILLAR[2], 0.6)
            s += self._poles(kit, sx)
        return s

    @staticmethod
    def _frame(kit, sx):
        """The stepped pointed frame on the porch front: every piece stands on the front face."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft
        out = []

        def piece(poly, xf, tags, front):
            for sy in (1, -1):
                r0 = [V((sx * FRONT, sy * y, z)) for y, z in poly]
                r1 = [V((sx * xf, sy * y, z)) for y, z in poly]
                out.append(loft([r0, r1], [tags], cap0=("stoneB", True), cap1=(front, True)))   # the porch narrows: backs show
        for i in range(len(RINGS)):
            inner = kit.arch_offset(ARCH, RINGS[i])
            xf = RING_X[i]
            if i < len(RINGS) - 1:
                outer = kit.arch_offset(ARCH, RINGS[i + 1])
                for k in range(3):
                    piece([inner[k], outer[k], outer[k + 1], inner[k + 1]], xf,
                          ["top" if k == 0 else None, None, None, "trim|a"], "tri|a")
            else:
                j0, j1, sh, ap = inner
                oy, lz = FRAME_Y, TOP
                piece([j0, (oy, 0.0), (oy, j1[1]), j1], xf, ["top", "stoneB", None, "trim|a"], "stoneB")
                piece([j1, (oy, j1[1]), (oy, lz), (sh[0], lz), sh], xf, [None, "stoneB", None, None, "trim|a"], "stoneB")
                piece([sh, (sh[0], lz), (0.0, lz), ap], xf, [None, None, None, "trim|a"], "stoneB")
        return out

    @staticmethod
    def _crown(sx):
        """A corbelled cornice with the hexagon frieze on the porch top, then a stepped gable over
        the door (bronze step, triangle-frieze tier, stone point) with a gilded finial."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft, prism_uz, rect_ring

        def ring(x0, x1, hy, z, ch=0.3):
            xs = sorted((sx * x0, sx * x1))
            return rect_ring((0, 0), (1, 0), (0, 1), xs[0], xs[1], -hy, hy, z, ch)
        # sides of rect_ring (chamfered): 0 y-, 2 +X, 4 y+, 6 -X. The wall (another model) is not
        # there for the checks: the side against it stays a face

        def tags(tg):
            return [tg if k in (0, 2, 4, 6) else "stoneB" for k in range(8)]
        c = [ring(WALL, FRONT + 0.2, 8.2, TOP - 1.4), ring(WALL, FRONT + 2.2, 11.8, TOP),
             ring(WALL, FRONT + 2.2, 11.8, TOP + 1.5), ring(WALL, FRONT + 2.4, 12.0, TOP + 1.5),
             ring(WALL, FRONT + 2.4, 12.0, TOP + 2.1)]
        out = [loft(c, [tags("stoneB"), tags("hex"), tags("trim"), tags("trim")], cap0=("stoneB", True), cap1=("top", True))]
        a, t, n = V((sx * WALL, 0, 0)), V((0, sx, 0)), V((sx, 0, 0))
        z = TOP + 2.1
        d1 = FRONT + 1.6 - WALL
        for h, dz, tg, e in ((8.6, 1.4, "trim", 0.0), (6.6, 1.8, "tri|a", 0.4)):
            out.append(prism_uz(a, t, n, [(-h, z), (h, z), (h, z + dz), (-h, z + dz)], 0.0, d1 - e,
                                [None, "stoneB", "top", "stoneB"], tg, "stoneB"))
            z += dz
        out.append(prism_uz(a, t, n, [(-6.6, z), (6.6, z), (0.0, z + 2.3)], 0.0, d1 - 0.8, [None, "top", "top"], "stoneA", "stoneB"))
        return out

    @staticmethod
    def _poles(kit, sx):
        from mathutils import Vector as V

        from ..wall_gate.building import pole
        out = []
        for sy in (-1, 1):
            a, t, n = V((sx * POLE[0], sy * POLE[1], 0)), V((0, sx, 0)), V((sx, 0, 0))
            out += pole(kit, a, t, n, POLE[2], 42.0, 4.4, 14.0)
        return out

    def emphasis(self, c, n):
        return 1.3 if abs(c.x) > 12 else 1.0
