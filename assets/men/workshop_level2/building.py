"""The Gondor siege workshop at level 2 (Upgrade_StructureLevel2): V1, redesigned on the finished
workshop (`base`; the chain and its rules: assets/men/barracks/levels.py). EA's V1 is the yard's
wall ring - two thick battered walls with a walk and a corbel arcade, diagonal returns to two
octagonal bastions flanking the yard's open end - plus a block against each tower's outer face
and a ribbed slate cap on each tower top. Now:

    walls       a crenellated parapet (square merlons with capstones) along the walk's outer
                edge, straight runs and diagonal returns (EA's lip on the yard edge stays)
    bastions    merlons round each bastion's rim and a watch turret on it: a drum with slit
                windows, a steel-banded cornice, a slate cone, a steel spike and a gilt knob
    blocks      merlons round the tower blocks' tops and a pinnacle on each outer corner
    caps        steel ribs up EA's caps (eight hips and four middles); the body's mast, with its
                gilt orb, stands through each apex and the body's crenellated parapet rings it

No cloth and no lights (a level mesh: levels.py). V1's frame is the model's (identity); the
body's is offset by (11.62, -0.16), so its towers stand at x -40.7..-17.8 here.

EA's V1 (model coordinates, mirrored in y): the walk at z 18.9 between the inner edge y 33.1
and the outer edge y 43.68 (battered to 44.7 at the foot), from x -43 to the corner at x 34.3,
the return's outer edge on x + y = 78.0 to the bastion; the bastion's top at 21.76 over x
40.2..52.4, y 13.8..25.3 (outer corners chamfered); the tower block's top at 30.89 over x
-36.0..-22.4, y 30.3..41.2 (it runs into the tower's face at y 34.5); the cap from a
chamfered square (half 10.1, chamfer 2.9) at 51.09 through octagons to its apex (-29.37, 26.51,
58.70)."""
from ..barracks.levels import LevelMesh, chain, level_textures

WALK, OUTER, CORNER = 18.9, 43.68, 34.3
RETURN = 78.0                                   # the returns' outer edge: x + |y| = 78
BASTION = (40.2, 52.4, 13.8, 25.3, 21.76, 2.2)  # x0, x1, |y|0, |y|1, top, outer chamfer
BLOCK = (-36.0, -22.4, 34.4, 41.2, 30.89)       # x0, x1, |y| from the tower face, |y| out, top
CAP = (-29.37, 26.51, [(51.2, 10.1, 2.9), (53.77, 8.4, 2.5), (55.94, 6.5, 1.9), (57.31, 4.82, 1.27), (57.98, 3.24, 0.63)])
MERLONS = dict(h=0.9, merlon=2.3, w=2.0, gap=1.5, cap=0.5)


class WorkshopLevel2(LevelMesh):
    source = "GBWorkshop"
    target = "V1"
    base = chain("workshop", 2)
    own_textures = level_textures("W", 2)
    bake_hidden = ("V2", "V1HIDE", "N_WINDOW")      # level 2: V1HIDE gone, V2 not yet
    views = {
        "rts": ((5.0, 0.0, 24.8), 300, 50, -38, 50),
        "close": ((30.0, -25.0, 20.0), 120, 24, -40, 45),
        "towers": ((-29.4, 0.0, 40.0), 130, 26, -20, 45),
        "ingame": ((5.0, 0.0, 24.8), 660, 53, -62, 50),
    }

    @property
    def sheet_atlas(self):
        from ..workshop.prodkit import VET_TILES, with_tiles
        return with_tiles(super().sheet_atlas, VET_TILES)       # EA's slate caps stay slate

    def design(self, kit):
        out = []
        for s in (1, -1):
            out += self._walls(kit, s)
            out += self._bastion(kit, s)
            out += self._block(kit, s)
            cx, cy, levels = CAP
            out += kit.ribs(cx, s * cy, levels, r=(0.3, 0.16), proud=0.15)
        return out

    @staticmethod
    def _walls(kit, s):
        from mathutils import Vector as V

        from ..barracks import motifs as M
        out = []
        a, t, n = M.face((0.0, s * OUTER), (0, s))
        u0, u1 = sorted((t.x * -20.8, t.x * CORNER))
        out += M.parapet(kit, a, t, n, u0, u1, WALK, -1.1, 0.0, **MERLONS)
        # the return: from the corner (CORNER, OUTER) down x + |y| = RETURN to the bastion's rim
        p0 = V((CORNER + 0.4, s * (RETURN - CORNER - 0.4), 0))
        p1 = V((BASTION[1] - 1.0, s * (RETURN - BASTION[1] + 1.0), 0))
        nrm = V((1, s, 0)).normalized()
        a, t, n = M.face((p0.x, p0.y), (nrm.x, nrm.y))
        L = (p1 - p0).dot(t)
        u0, u1 = sorted((0.0, L))
        out += M.parapet(kit, a, t, n, u0 + 0.3, u1 - 0.3, WALK, -1.1, 0.0, **MERLONS)
        return out

    @staticmethod
    def _bastion(kit, s):
        """Merlons round the rim (not where the wall's return comes in) and a watch turret."""
        from sagekit.blender.geometry import box_rings

        from ..barracks import motifs as M
        import math

        from ..shapes import beam, turned
        x0, x1, y0, y1, z, ch = BASTION
        ya, yb = sorted((s * y0, s * y1))
        ring = box_rings((x0, x1), (ya, yb), z, ch)
        pts = [(p.x, p.y) for p in ring]
        cx, cy = (x0 + x1) / 2, (ya + yb) / 2
        out = []
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            if mid[0] < x0 + 0.6 * ch or s * mid[1] > y1 - 0.3:
                continue                            # the inner side and the wall's return
            L = math.dist(p, q)
            nx, ny = (q[1] - p[1]) / L, -(q[0] - p[0]) / L
            if nx * (mid[0] - cx) + ny * (mid[1] - cy) < 0:
                nx, ny = -nx, -ny
            a, t, n = M.face(mid, (nx, ny))
            if L > 3.0:
                out += M.parapet(kit, a, t, n, -L / 2 + 0.2, L / 2 - 0.2, z, -1.0, 0.0, **MERLONS)
            else:
                out += M.parapet(kit, a, t, n, -L / 2 - 0.3, L / 2 + 0.3, z, -1.0, 0.0, h=0.9, merlon=2.3, w=L + 0.6, gap=1.0, cap=0.5)
        # the watch turret
        r = 3.4
        tz = z + 7.2
        slit = ["slit" if i % 2 == 0 else "stoneA" for i in range(8)]
        out.append(turned(cx, cy, [(r + 0.5, z - 0.1), (r + 0.5, z + 0.9), (r, z + 1.2), (r, tz), (r + 0.45, tz + 0.5), (r + 0.45, tz + 1.3)],
                          ["course", "stoneB", slit, "trim", "trim"], k=8, cap0=("stoneB", False), cap1=("top", True)))
        zc = tz + 1.3
        out.append(turned(cx, cy, [(r + 0.25, zc), (0.0, zc + 8.5)], ["slate"], k=8, cap0=("slate", True), cap1=("slate", False)))
        out.append(beam((cx, cy, zc + 7.2), (cx, cy, zc + 11.5), 0.2, "trim", 0.0))
        out.append(turned(cx, cy, [(0.2, zc + 8.1), (0.5, zc + 8.6), (0.5, zc + 9.1), (0.18, zc + 9.5)],
                          ["gilt"] * 3, k=6, cap0=("gilt", True), cap1=("gilt", True)))
        return out

    @staticmethod
    def _block(kit, s):
        from ..barracks import motifs as M
        x0, x1, yi, yo, z = BLOCK
        out = []
        ym = s * (yi + yo) / 2
        for x, nx in ((x0, -1), (x1, 1)):             # the sides, from the tower's face to the corner pinnacle
            a, t, n = M.face((x, ym), (nx, 0))
            u0, u1 = sorted(((s * yi - ym) * t.y + 0.2, (s * (yo - 1.3) - ym) * t.y))
            out += M.parapet(kit, a, t, n, u0, u1, z, -1.0, 0.0, **MERLONS)
        a, t, n = M.face(((x0 + x1) / 2, s * yo), (0, s))
        h = (x1 - x0) / 2 - 1.3
        out += M.parapet(kit, a, t, n, -h, h, z, -1.0, 0.0, **MERLONS)
        for cx in (x0 + 1.1, x1 - 1.1):
            out += kit.pinnacle(cx, s * (yo - 1.1), z, z + 3.2, half=1.05, spire=3.8)
        return out
