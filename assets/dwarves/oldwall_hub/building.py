"""Dwarven castle-wall hub (DwarvenCastleWallHub, model DBWallRmprt): EA's twelve-sided bastion
where the old castle walls meet, given the new wall hub's crown (wall_hub) at this hub's size: a
battered plinth, stepped corbels carrying the overhanging upper drum, a rune band with
Erebor-blue enamel, the walls' bronze-banded coping and chevron parapet round the rim, stepped
corner blocks with gilded points on six corners, a stepped crown with a rune belt and a triangle
frieze in the middle of the platform, four banner poles round it, and a banner on each diagonal
face.

EA's model is an unfinished stand-in (one mesh GBWALLRAMPART, 82 triangles, painted from the
placeholder sheet "Dwarven Wall"): a regular twelve-sided drum about (-2.01, 0), vertices at
0, 30, ... degrees, circumradius 51.17 from z 0.26 to 30.83, then an upper drum overhanging to
circumradius 59.09 up to a flat platform at z 53.52 (the walls' walkway is 51.91). Its faces are
removed and every volume rebuilt on the faction atlas (oldwall_segment/wall.clear_target). The
footprint is EA's to the hundredth (x -61.10..57.08, y +-59.09): nothing stands out of the upper
drum's twelve faces, whose planes the walls run into from any side.

Height: EA's flat drum is only as high as the walls' walkway; the new walls' hub rises 12 above
theirs to its crown. Here the corner points reach 69.4 and the crown 74.4: +39 % on EA's 53.26
(max_z_growth 0.40; the default 0.20 would stop the crown at 64.2, level with the walls' parapet).

All numbers are GBWALLRAMPART mesh coordinates (its pivot is the identity)."""
from sagekit.building import Building

from ..style import DwarvenStyle

C = (-2.0097, 0.0)                # the drum's axis
R_LOW, R_UP = 51.17, 59.085       # circumradii (vertices at 0, 30, ... degrees)
TOP = 53.52                       # EA's platform
# the drum's outline: (circumradius, z) rings, tags per interval
BODY = [(54.0, 0.27), (54.0, 1.2), (51.9, 7.4), (R_LOW, 7.8), (R_LOW, 30.82), (58.5, 30.82), (58.5, 44.4),
        (58.8, 44.4), (58.8, 51.2), (R_UP, 51.5), (R_UP, 52.6), (58.95, 52.7), (58.95, 56.6), (58.5, 57.0),
        (55.4, 57.0), (55.4, TOP)]
BODY_TAGS = ["stoneB", "stoneA", "top", "stoneA", "stoneB", "stoneA", "trim", "rune", "trim", "trim", "trim",
             "stoneA", "trim", "top", "stoneA"]
PATH_R = 57.3                     # chevron path; slab fronts flush with the coping face (58.95)
# the crown in the middle of the platform: (circumradius, z) rings, then a gilded point
CROWN = [(21.0, TOP), (20.4, 59.0), (21.4, 59.0), (21.4, 60.0), (17.6, 60.0), (17.0, 64.6), (17.7, 64.6),
         (17.7, 65.3), (13.0, 65.3), (12.6, 68.8), (9.0, 68.8), (8.6, 70.8), (5.6, 70.8)]
CROWN_TAGS = ["rune", "trim", "trim", "top", "tri", "trim", "trim", "top", "stoneA", "top", "stoneA", "top"]
CROWN_POINT = 74.4                # height limit: 0.26 + 53.26 x 1.40 = 74.82
# stepped corner blocks on the even vertices: (half0, half1, z0, z1, tag), radially centred at 55.9
CORNER_R = 55.9
CORNER_TIERS = [(3.1, 2.8, TOP, 62.6, "stoneB"), (2.3, 2.15, 62.6, 65.0, "stoneA"), (1.6, 1.5, 65.0, 66.7, "stoneA")]
CORNER_POINT = 69.4
# corbels under the overhang: three per lower face, three stepped blocks (z0, z1, depth, half width)
CORBEL_BLOCKS = [(21.2, 24.4, 2.4, 1.6), (24.4, 27.6, 4.7, 1.5), (27.6, 30.82, 7.0, 1.4)]
BANNER = (43.4, 7.0, 12.4)        # on the diagonal upper faces, under the rune band
BANNER_SIDES = (1, 4, 7, 10)      # sides from vertex i to i+1: centred at 45, 135, 225, 315 degrees
POLE_R, POLE_TOP = 28.0, 70.0     # banner poles on the platform, at the diagonals


def vertex(r, k, z=0.0):
    import math

    from mathutils import Vector as V
    a = math.radians(30 * k)
    return V((C[0] + r * math.cos(a), C[1] + r * math.sin(a), z))


def ring(r, z):
    return [vertex(r, k, z) for k in range(12)]


def side(r, i):
    """(a, t, n, L) of side i (vertex i to i+1) of the 12-gon of circumradius r, at z 0."""
    from mathutils import Vector as V
    a, b = vertex(r, i), vertex(r, i + 1)
    t = (b - a).normalized()
    n = V((t.y, -t.x, 0))
    if n.dot((a + b) / 2 - V((C[0], C[1], 0))) < 0:
        n = -n
    return a, t, n, (b - a).length


class OldWallHub(Building):
    style = DwarvenStyle()
    source = "DBWallRmprt"
    target = "GBWALLRAMPART"
    sheet = "DBWall.tga"                                # EA's placeholder; no face samples it
    sheet_normal = None
    own_textures = {"DBWall.tga": "DBWalR.tga"}
    tri_budget = 8000
    max_z_growth = 0.40
    views = {
        "rts": ((-2, 0, 30), 330, 48, -30, 50),
        "close": ((-2, 0, 42), 200, 20, -24, 45),
        "ingame": ((-2, 0, 25), 650, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft, prism_uz

        from ..oldwall_segment.wall import clear_target
        from ..wall_gate.building import pole
        clear_target(self.target)
        out = [loft([ring(r, z) for r, z in BODY], BODY_TAGS, cap0=("stoneB", False), cap1=("top", True))]
        apo = lambda r: r * 0.9659258                   # noqa: E731  (apothem of circumradius r)
        for i in range(12):                                              # chevron parapet
            a, t, n, L = side(PATH_R, i)
            out += kit.chevron_parapet(a, t, n, L, d0=apo(55.4) + 0.2 - apo(PATH_R), d1=apo(58.95) - apo(PATH_R))
        for k in range(0, 12, 2):                                        # corner blocks
            out += self._corner(k)
        rings = [ring(r, z) for r, z in CROWN]                           # the crown
        out.append(loft(rings, CROWN_TAGS, cap0=("top", False), cap1=("top", False)))
        out.append(loft([rings[-1], [V((C[0], C[1], CROWN_POINT))] * 12], ["trim"], cap0=("top", False),
                        cap1=("top", False)))
        for i in range(12):                                              # corbels
            a, t, n, L = side(R_LOW, i)
            for u in (L / 6, L / 2, 5 * L / 6):
                for k, (z0, z1, d, hw) in enumerate(CORBEL_BLOCKS):
                    out.append(prism_uz(a, t, n, [(u - hw, z0), (u + hw, z0), (u + hw, z1), (u - hw, z1)], -0.5, d,
                                        ["stoneB", "stoneB", None if k == 2 else "top", "stoneB"], "stoneB", None))
        z_top, width, length = BANNER                                    # banners
        for i in BANNER_SIDES:
            a, t, n, L = side(58.5, i)
            out += kit.banner(a, t, n, L / 2, z_top, width, length, d=0.05)
            m = vertex(POLE_R, i + 0.5, 0)                               # a pole on the same diagonal
            out += pole(kit, V((m.x, m.y, 0)), t, n, TOP, POLE_TOP, 5.0, 13.0)
        return out

    @staticmethod
    def _corner(k):
        """A stepped block on vertex k, square to the radius, ending in a gilded point."""
        import math

        from mathutils import Vector as V
        from sagekit.blender.geometry import loft
        a = math.radians(30 * k)
        rad, tan = V((math.cos(a), math.sin(a), 0)), V((-math.sin(a), math.cos(a), 0))
        c = V((C[0], C[1], 0)) + rad * CORNER_R

        def sq(h, z):
            return [V((p.x, p.y, z)) for p in (c - rad * h - tan * h, c + rad * h - tan * h, c + rad * h + tan * h,
                                               c - rad * h + tan * h)]
        out = [loft([sq(h0, z0), sq(h1, z1)], [tg], cap0=("top", False), cap1=("top", True))
               for h0, h1, z0, z1, tg in CORNER_TIERS]
        top = sq(CORNER_TIERS[-1][1], CORNER_TIERS[-1][3])
        out.append(loft([top, [V((c.x, c.y, CORNER_POINT))] * 4], ["trim"], cap0=("top", False), cap1=("top", False)))
        return out

    def emphasis(self, c, n):
        if c.z > 52:
            return 1.4                        # crown and parapet: what the RTS camera sees
        return 1.0
