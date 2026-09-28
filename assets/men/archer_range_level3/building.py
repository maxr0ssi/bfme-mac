"""Men archer range, level 3 (Upgrade_GondorArcheryRangeLevel3: ShowSubObjects V1 V2): the arcades,
the north-west turret and the archer's statue V2, redesigned on the finished level 2 (`base`,
levels.py).

EA's V2 (model coordinates): an octagonal turret on the yard's north-west corner, centre
(-29.76, 48.97), vertices at 0, 45, ... degrees (circumradius 10.3 at the foot, 9.9 at 36.9, a set-
back to 8.59 at 39.9, the drum 8.26 to 59, a dome to 66.1), a painted arched window on each face
(sill 46.7, crown 58; the level-3 arrows' bones ARROW_01..08 in them at z 52); two arcades across
the yard (y -29.8..-24.8 and 8.9..13.9, x -31.7..30.6, top 34.9) with end piers to z 46; the
archer's statue on its plinth on the tower's dome (z 96..139). What stands on it here:

    turret   a ledge with merlons on the set-back, a steel-framed surround on each window (sill,
             voussoirs, keystone), a steel band and merlons round the dome's foot, steel ribs up
             the dome's edges, a steel mast, gilt orb and spike
    arcades  square merlons along both arcades' tops, a frieze of gilt stars on the middle
             arcade's south face, pinnacles on the end piers

The statue and its plinth stay EA's. No cloth, no night lights (levels.py).
"""
from ..archer_range.building import NOT_BAKED
from ..barracks.levels import LevelMesh, chain, level_textures

TUR = (-29.76, 48.97)
R_LEDGE, R_DRUM, R_TOP = 9.9, 8.59, 8.26
DOME = [(59.0, 8.26), (62.4, 6.77), (64.9, 4.28), (66.1, 0.35)]
ARCADES = [(8.9, 13.9), (-29.8, -24.8)]         # (south face y, north face y)
PIERS = [(-29.9, -27.0), (-29.9, 11.65), (28.8, 11.65)]


class ArcherRangeLevel3(LevelMesh):
    source = "GBArcheryN_SKN"
    target = "V2"
    base = chain("archer_range", 3)
    level = 3
    own_textures = level_textures("A", 3)
    bake_hidden = NOT_BAKED[:-2]
    views = {
        "rts": ((5.2, 0.4, 52.2), 356, 50, -38, 50),
        "close": ((-5, 20, 35), 180, 26, -40, 45),
        "turret": ((-29.8, 49.0, 52.0), 70, 15, -60, 45),
        "ingame": ((5.2, 0.4, 52.2), 809, 53, -62, 50),
    }

    def design(self, kit):
        from ..barracks.motifs import closed
        return closed(self._turret(kit) + self._arcades(kit))

    @staticmethod
    def _faces(r_vertex):
        """(anchor at the face's middle, t, n) of the turret's eight faces (circumradius r_vertex)."""
        import math

        from mathutils import Vector as V
        ap = r_vertex * math.cos(math.pi / 8)
        out = []
        for k in range(8):
            th = math.pi / 8 + k * math.pi / 4
            n = V((math.cos(th), math.sin(th), 0))
            out.append((V((TUR[0] + n.x * ap, TUR[1] + n.y * ap, 0)), V((-n.y, n.x, 0)), n, 2 * r_vertex * math.sin(math.pi / 8)))
        return out

    def _turret(self, kit):
        import math

        from ..barracks.motifs import knob, window_surround
        from ..shapes import rail, turned
        cx, cy = TUR
        out = [turned(cx, cy, [(R_LEDGE + 0.1, 37.6), (R_LEDGE + 0.1, 39.9)], ["course"], k=8, phase=0.0,
                      cap0=("stoneB", True), cap1=("top", True))]
        for a, t, n, L in self._faces(R_LEDGE + 0.1):
            out += kit.merlons(a - t * (L / 2), t, n, 0.35, L - 0.35, 39.9, -1.2, 0.0, w=1.5, gap=1.1, h=2.2, cap=0.45)
        for a, t, n, L in self._faces(R_DRUM):
            out += window_surround(kit, a, t, n, 0.0, 2.45, 46.7, 55.0, w=0.45, d=0.35, count=7)
        out.append(turned(cx, cy, [(R_TOP + 0.35, 58.6), (R_TOP + 0.35, 59.5)], ["trim"], k=8, phase=0.0,
                          cap0=("trim", True), cap1=("trim", True)))
        for a, t, n, L in self._faces(R_TOP + 0.35):
            out += kit.merlons(a - t * (L / 2), t, n, 0.4, L - 0.4, 59.5, -0.9, 0.0, w=1.3, gap=1.0, h=1.8, cap=0.4)
        for k in range(8):                       # ribs up the dome's edges (its vertices)
            th = k * math.pi / 4
            pts = [(cx + (r + 0.18) * math.cos(th), cy + (r + 0.18) * math.sin(th), z + 0.08) for z, r in DOME]
            out.append(rail(pts, 0.26, "trim", 0.16))
        out += knob(cx, cy, 65.8, 74.0, r=0.7)
        return out

    @staticmethod
    def _arcades(kit):
        from mathutils import Vector as V

        from ..barracks.motifs import star_frieze
        out = []
        for ys, yn in ARCADES:
            x0, x1 = (-26.4, 25.3) if ys > 0 else (-26.4, 22.8)
            for y, t, n in ((ys, V((1, 0, 0)), V((0, -1, 0))), (yn, V((-1, 0, 0)), V((0, 1, 0)))):
                a = V((0, y, 0))
                u0, u1 = sorted((x0 * t.x, x1 * t.x))
                out += kit.merlons(a, t, n, u0, u1, 34.9, -1.2, 0.2, w=1.8, gap=1.3, h=2.2, cap=0.45)
        out += star_frieze(kit, V((0, 8.9, 0)), V((1, 0, 0)), V((0, -1, 0)), -26.0, 25.0, 31.6, h=1.5, d1=0.35, count=13)
        for x, y in PIERS:
            out += kit.pinnacle(x, y, 46.0, 47.4, half=1.0, spire=4.2)
        return out

    def decals(self):
        from ..barracks.paintkit import Slate                # the turret's dome in charcoal slate
        return [Slate(58.8, box=(-41.0, -18.5, 37.5, 60.5))]

    def emphasis(self, c, n):
        if c.y > 36 and c.x < -15:
            return 1.35                      # the turret
        return 1.0
