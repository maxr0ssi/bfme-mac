"""Dwarven castle-wall postern (DwarvenWallPosternGate): the old castle wall's postern upgrade as
a small Erebor gatehouse front on each face of the wall. EA's object draws Gondor's placeholder
GBWallPG (a box labelled "postern gate" across a wall section), which Men and Arnor draw too, so
ours ships as a model of its own, DBWallPG2 (sagekit/owncopy.py; EA's unused DBWallPG is filed in
BFME2's cache).

The old castle wall's section (oldwall_segment/upgrade.py) runs unbroken along |y| <= 99.5 with a
Dwarven stair down EA's ramp at each end, two statue pilasters and four banners per face. Against
each face stands a porch (x 23.77 .. 47, y +-18, EA's label box is x +-52.05, y +-23.26, to 37.04):
battered plinth, a stepped pointed frame round a bronze-strapped stone door (two rings with the
triangle frieze and bronze reveals, then a frame slab), a banner either side, a corbelled hexagon
cornice, a stepped gable (top 41.9, under the wall's corbels, which stop over the porch), stepped
pyramids on the front corners.

The postern is a pass-through: units leave by EA's bones POST01..04 at x +-52.3 / +-77.8 on the
ground, outside the porches (the plinth ends at 49.3). EA's GBWALLUPGRD and BOX01 are taken over by
our target GBWALLGATE and dropped from our copy. All numbers are model coordinates."""
from sagekit.building import Building

from ..style import DwarvenStyle

PX, PY, PT = 47.0, 18.0, 32.0     # porch front, half width, body top
ARCH = [(6.5, 0.0), (6.5, 17.0), (4.6, 24.5), (0.0, 27.0)]
RINGS, RING_X = (0.0, 1.3, 2.6), (0.6, 1.2, 1.8)   # ring offsets; their fronts out of the porch face
FRAME_Y = 11.0
RELIEFS = 60.0                    # |y| of the statue pilasters on the wall faces


class OldWallPostern(Building):
    style = DwarvenStyle()
    source = "GBWallPG"
    own_model = "DBWallPG2"
    replaces = ("GBWALLUPGRD", "BOX01")
    target = "GBWALLGATE"
    sheet = "GBWall.tga"                                # Gondor's placeholder; no face samples it
    sheet_normal = None
    own_textures = {"GBWall.tga": "DBWalP.tga"}
    bake_hidden = ("P1", "R1", "R2")
    tri_budget = 12000
    views = {
        "rts": ((0, 0, 30), 480, 50, -38, 50),
        "close": ((20, 0, 25), 200, 18, -24, 45),
        "ingame": ((0, 0, 30), 950, 53, -62, 50),
    }

    def design(self, kit):
        from ..oldwall_segment.upgrade import END, FOOT, UP_WALK, bays, pilasters, stairs
        from ..oldwall_segment.wall import clear_target, run
        clear_target(self.target)
        cs, p = bays(-END, END)
        corbels = [c for c in cs if abs(c) > PY + 4.0]
        ys = [min(cs, key=lambda c: abs(c - e * RELIEFS)) for e in (-1, 1)]
        banners = [(y + e * 1.5 * p, UP_WALK - 13.71, 4.4, 17.0) for y in ys for e in (-1, 1)]
        s = run(kit, -END, END, UP_WALK, foot=FOOT, corbels=corbels, banners=banners)
        s += pilasters(ys) + stairs()
        for sx in (1, -1):
            s += self._porch(kit, sx)
        return s

    @staticmethod
    def _porch(kit, sx):
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft, prism_uz, sweep

        from ..oldwall_segment.upgrade import FOOT
        from ..oldwall_segment.wall import CORE_X
        from ..wall_tower.crown import step_pyramid
        xs = sorted((sx * (CORE_X - 0.5), sx * PX))
        out = [loft([box_rings(xs, (-PY, PY), FOOT, 0), box_rings(xs, (-PY, PY), PT, 0)], ["stoneA"],
                    cap0=("stoneB", False), cap1=("top", False))]
        path = [(sx * CORE_X, -PY), (sx * PX, -PY), (sx * PX, PY), (sx * CORE_X, PY)]
        out += sweep(path, [(0.0, FOOT), (2.3, FOOT), (2.3, 0.8), (0.8, 5.8), (0.0, 6.3)],
                     [None, "stoneB", "stoneA", "top", None])[0]
        # the cornice: a corbelled hexagon band round the front and sides (box_rings side 1 is +X)
        wall_side = 3 if sx > 0 else 1

        def ring(d, z):
            return box_rings(sorted((sx * (CORE_X - 0.5), sx * (PX + d))), (-PY - d, PY + d), z, 0)

        def tg(t):
            return [None if k == wall_side else t for k in range(4)]
        c = [ring(0.0, PT - 1.4), ring(1.8, PT), ring(1.8, PT + 1.6), ring(2.0, PT + 1.6), ring(2.0, PT + 2.2)]
        out.append(loft(c, [tg("stoneB"), tg("hex"), tg("top"), tg("trim")], cap0=("stoneB", False), cap1=("top", True)))
        # the stepped gable over the door
        a, t, n = V((sx * CORE_X, 0, 0)), V((0, sx, 0)), V((sx, 0, 0))
        z, d1 = PT + 2.2, PX + 1.4 - CORE_X
        for h, dz, tag, e in ((13.0, 1.4, "trim", 0.0), (10.5, 1.8, "tri|a", 0.4)):
            out.append(prism_uz(a, t, n, [(-h, z), (h, z), (h, z + dz), (-h, z + dz)], 0.0, d1 - e,
                                [None, "stoneB", "top", "stoneB"], tag, None))
            z += dz
        out.append(prism_uz(a, t, n, [(-10.5, z), (10.5, z), (0.0, z + 4.5)], 0.0, d1 - 0.8, [None, "top", "top"],
                            "stoneA", None))
        for sy in (1, -1):
            out += step_pyramid(sx * (PX - 2.4), sy * (PY - 2.4), PT + 2.2, 0.6)
        out += OldWallPostern._door(kit, sx)
        for u in (-14.6, 14.6):                                      # banners either side of the frame
            out += kit.banner(V((sx * PX, 0, 0)), V((0, sx, 0)), V((sx, 0, 0)), u, PT - 2.2, 4.2, 15.0, d=0.05)
        return out

    @staticmethod
    def _door(kit, sx):
        """The stepped pointed frame on the porch front round a stone door with bronze straps."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft, prism_uz
        out = []

        def piece(poly, xf, tags, front):
            for sy in (1, -1):
                r0 = [V((sx * PX, sy * y, z)) for y, z in poly]
                r1 = [V((sx * (PX + xf), sy * y, z)) for y, z in poly]
                out.append(loft([r0, r1], [tags], cap0=("stoneB", False), cap1=(front, True)))
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
                piece([j0, (FRAME_Y, 0.0), (FRAME_Y, j1[1]), j1], xf, ["top", "stoneB", None, "trim|a"], "stoneB")
                piece([j1, (FRAME_Y, j1[1]), (FRAME_Y, PT - 1.4), (sh[0], PT - 1.4), sh], xf,
                      [None, "stoneB", "top", None, "trim|a"], "stoneB")
                piece([sh, (sh[0], PT - 1.4), (0.0, PT - 1.4), ap], xf, [None, "top", None, "trim|a"], "stoneB")
        a, t, n = V((sx * PX, 0, 0)), V((0, sx, 0)), V((sx, 0, 0))
        door = [(-6.5, 0.0), (6.5, 0.0), (6.5, 17.0), (4.6, 24.5), (0.0, 27.0), (-4.6, 24.5), (-6.5, 17.0)]
        out.append(prism_uz(a, t, n, door, -0.2, 0.25, [None] + ["stoneB"] * 6, "stoneB", None))
        for z0, h in ((4.0, 6.3), (12.0, 6.3), (19.2, 5.6)):           # bronze straps and the meeting stile
            out.append(prism_uz(a, t, n, [(-h, z0), (h, z0), (h, z0 + 1.0), (-h, z0 + 1.0)], 0.0, 0.5,
                                ["trim", "trim", "top", "trim"], "trim", None))
        out.append(prism_uz(a, t, n, [(-0.45, 0.0), (0.45, 0.0), (0.45, 26.2), (-0.45, 26.2)], 0.0, 0.45,
                            [None, "trim", "trim", "trim"], "trim", None))
        return out

    def emphasis(self, c, n):
        if c.z < -2:
            return 0.15
        if abs(c.x) > 44 and c.z < 34:
            return 1.5                        # the doors and their frames
        return 1.4 if c.z > 50 else 1.0
