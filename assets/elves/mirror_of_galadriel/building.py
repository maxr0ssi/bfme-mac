"""The Mirror of Galadriel (ElvenMirrorOfGaladriel, elvenmirrorofgaladriel.ini): EA's silver basin on
its tall knotwork pedestal keeps its water and carving, its octagonal dais keeps the mallorn roots
that grip it; the stair that climbs to it becomes Galadriel's. Each of EA's two flights of chevron
slabs gains a silver balustrade down both sides (turned balusters on every tread, a rounded rail
falling with the flight), a lantern column with a crystal lantern at each corner of its foot, and
where the flights meet, on the landing's point, a taller lantern column; two gilt banner poles on
the landing's back corners fly leaf banners in the player's colour over the approach
to the dais.

EA's model is four meshes on identity bones (mesh = model coordinates): EBGALMIRR3 the pedestal and
basin (round (-13.85, 0), radius 7.8, z 5.6..28.0), EBGALMIRR2 the octagonal dais (corners on the
axes at radius 10.45, z 0..5.6), EBGALMIRR4 the roots, and EBGALMIRR1, the stair: the target. The
stair is a landing (top z 4.9, its point at (9.6, 0)) and two mirrored flights of five chevron slabs
0.7 apart (4.2 .. 1.3) running out to y +-31.6 (x -3.4..24.2): the footprint. Each flight's outer
side runs along the slabs' points (TIPS), its inner side along their tails (TAILS), measured from
EA's vertices (the +y flight; the -y flight is its mirror).

The stair is 4.9 high but the model is the basin's 28.0: max_z_growth lets the stair's lanterns and
poles rise to 20.8 (the model's height is unchanged).
"""
import math

from sagekit.building import Building

from ..style import ElvenStyle

# the +y flight's sides: (x, y, top of the slab there), from the top down to the foot (the outer side
# starts on the first slab: the landing's point, (9.6, 0), is shared by both flights)
TIPS = [(10.2, 1.7, 4.2), (12.9, 7.6, 3.5), (16.6, 12.0, 2.7), (20.3, 15.9, 2.0), (24.2, 19.6, 1.3)]
TAILS = [(-3.1, 3.7, 4.9), (-1.8, 8.2, 4.2), (-0.7, 12.7, 3.5), (2.9, 19.1, 2.7), (6.3, 24.9, 2.0), (10.2, 30.5, 1.3)]
FLIGHT_MID = (10.5, 16.0)          # a point inside the +y flight (the insets turn towards it)
RAIL = 2.5                         # rail height over the treads


def inset(path, d, mid=FLIGHT_MID):
    """Each point of a side moved d into the flight (along the side's normal towards `mid`)."""
    out = []
    for i, (x, y, z) in enumerate(path):
        a, b = path[max(i - 1, 0)], path[min(i + 1, len(path) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L, tx / L
        if nx * (mid[0] - x) + ny * (mid[1] - y) < 0:
            nx, ny = -nx, -ny
        out.append((x + nx * d, y + ny * d, z))
    return out


def mirror(path):
    return [(x, -y, z) for x, y, z in path]


class MirrorOfGaladriel(Building):
    style = ElvenStyle()
    source = "EBGalMirr"
    target = "EBGALMIRR1"                   # the stair
    sheet = "EBGalMirr.tga"
    sheet_normal = "EBGalMirr_NRM.tga"
    own_textures = {"EBGalMirr.tga": "EBGalMirH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    max_z_growth = 3.4                      # the stair's 4.9 -> 20.8; the model stays the basin's 28.0
    tri_budget = 11000
    views = {
        "rts": ((2.0, 0.0, 8.0), 150, 50, -38, 50),
        "close": ((8.0, -8.0, 5.0), 80, 26, -30, 45),
        "ingame": ((0.0, 0.0, 8.0), 316, 53, -62, 50),
        "stair": ((10.0, 0.0, 4.0), 72, 16, 5, 45),
    }

    @property
    def sheet_atlas(self):
        """EA's sheet with the stair's slabs hinted as plain stone: their olive grime is not metal
        (colour alone flecked the new ivory slabs with orange)."""
        a = super().sheet_atlas
        a.mask_hints = {"stone": [(420, 0, 2048, 1860)]}
        return a

    def design(self, kit):
        s = []
        for sy in (1, -1):
            s += self._flight(kit, sy)          # 1. balustrades and foot lanterns of each flight
        s += self._landing(kit)                 # 2. the landing's lantern and banner poles
        return s

    # ------------------------------------------------------------------ 1. flights
    @staticmethod
    def _flight(kit, sy):
        out = []
        for side in (TIPS, TAILS):
            path = inset(side, 0.75)
            out += balustrade_down(path if sy > 0 else mirror(path))
        for x, y, z in (inset(TIPS, 1.9)[-1], inset(TAILS, 1.4)[-1]):     # lanterns at the foot's corners
            out += lantern_column(kit, x, sy * y, z, 6.0, 4.4)
        return out

    # ------------------------------------------------------------------ 2. landing
    @staticmethod
    def _landing(kit):
        """A taller lantern column on the landing's point, where the flights part, and two gilt
        banner poles on its back corners facing the approach (+x), without extra pennants."""
        from mathutils import Vector as V
        out = lantern_column(kit, 6.6, 0.0, 4.9, 7.6, 5.0)
        t, n = V((0, 1, 0)), V((1, 0, 0))
        for y in (2.0, -2.0):
            out += raised(kit.banner_pole(V((-1.95, y, 0)), t, n, 0.0, 18.3, 2.6, 7.2, pennant=False), 0.05)
        return out

    def emphasis(self, c, n):
        return 1.3


def raised(solids, dz):
    """Solids moved up dz (the kit's banner pole stands on z 0; EA's stair starts at 0.01)."""
    from mathutils import Vector as V
    for s in solids:
        for e in s.polys:
            e[0] = [p + V((0, 0, dz)) for p in e[0]]
    return solids


def lantern_column(kit, x, y, z0, height, lamp):
    """A moulded pedestal on the tread, a slender column with a leaf capital, a crystal lantern."""
    from ..shapes import turned
    out = [turned(x, y, [(0.95, z0 - 0.3), (0.95, z0 + 1.0), (1.08, z0 + 1.25), (0.75, z0 + 1.6)], ["stoneA", "coping", "trim"],
                  k=8, cap0=("stoneB", False), cap1=("top", True))]
    out += kit.column(x, y, z0 + 1.6, z0 + height, r=0.5, k=8, leaves=5)
    out += leaf_collar(kit, x, y, z0 + 1.45, 0.5, 6, 1.5)          # gold leaves round the shaft's foot
    out.append(turned(x, y, [(0.62, z0 + 0.52 * height - 0.2), (0.7, z0 + 0.52 * height), (0.62, z0 + 0.52 * height + 0.2)],
                      ["gilt", "gilt"], k=8, cap0=("gilt", True), cap1=("gilt", True)))      # a gilt ring mid-shaft
    out += kit.crystal_lantern(x, y, z0 + height, h=lamp, r=0.7)
    return out


def leaf_collar(kit, x, y, z, r, count, length):
    """A ring of gilt leaf blades round a shaft of radius r, rising from z and leaning out a little."""
    from mathutils import Vector as V
    out = []
    for i in range(count):
        ang = 2 * math.pi * (i + 0.25) / count
        t, n = V((math.cos(ang), math.sin(ang), 0)), V((-math.sin(ang), math.cos(ang), 0))
        out.append(kit.leaf_blade(V((x, y, 0)), t, n, 0.85 * r, z, length, 0.9 * r * 1.6, lean=0.3, thick=0.1))
    return out


def balustrade_down(path):
    """A balustrade down a stair side: turned balusters every ~1.55 on the treads (each standing on
    the slab under it: the side's points are the slabs' corners, a baluster takes the nearer one's),
    and a rounded silver rail RAIL over the treads falling straight from the top to the foot, the
    balusters' tops inside it; gilt caps on its ends."""
    from ..mallorn_tree.building import rail
    from ..shapes import turned
    out, tops = [], []
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:]))
    z_top, z_foot = path[0][2] + RAIL, path[-1][2] + RAIL
    run = 0.0
    for j, ((x0, y0, z0), (x1, y1, z1)) in enumerate(zip(path, path[1:])):
        L = math.hypot(x1 - x0, y1 - y0)
        m = max(1, round(L / 1.55))
        for i in range(m + 1 if j == len(path) - 2 else m):
            f = i / m
            x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
            zr = z_top + (z_foot - z_top) * (run + f * L) / total
            zt = z0 if f < 0.5 else z1
            out.append(turned(x, y, [(0.2, zt - 0.25), (0.28, zt + 0.55), (0.14, zr - 0.8), (0.2, zr - 0.2), (0.16, zr + 0.1)],
                              ["trim", "trim", "trim", "trim"], k=6, cap0=("top", False), cap1=("top", False)))
            tops.append((x, y, zr))
        run += L
    out.append(rail(tops, 0.24, "trim"))
    for x, y, z in (tops[0], tops[-1]):
        out.append(turned(x, y, [(0.3, z - 0.2), (0.38, z + 0.15), (0.2, z + 0.45)], ["trim", "gilt"], k=6,
                          cap0=("top", False), cap1=("gilt", True)))
    return out
