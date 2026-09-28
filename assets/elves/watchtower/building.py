"""Elven watchtower (ElvenWatchtowerExpansion, model EBFWTower): the tallest of the fortress's pad
buildings, a slender lantern tower on a square base.

EA's body (EBFWTOWER, 476 triangles), in its mesh coordinates, round the axis (-5.8, 0): a square
base (x -18.2..6.46, |y| 12.2, to 45.75) with a pointed door recess on each flank (x -11.98..0.25,
jambs to 33.93, point 41.5) and a carved relief on the +x front; a knotwork cornice flaring out
to 52.31 (half 13.54) and sloping in to the shaft (57.82); the shaft tapering from half 9.88 to
5.72 (101.5); the lantern head from 104.75 (four dormer bays, 4.2 wide, standing 2.7 out: their
ledges are the head's underside) to its gabled scale roof, whose four ridges sweep up into horns
(137.1) round a steep square pyramid (corners on the axes, 11.9 out at 134.2) ending at 151.88.
The eight ARROW bones fire from the dormers at 121.76: nothing new is near them. The arm reaches
back to the fortress over the expansions' arch (axis x -30.02; floodgate/pad.py).

The redesign, the citadel's recipe on the watchtower: EA's body kept whole (head, roof, horns,
knotwork) and a handful of additions - the pyramid runs on into a needle spire with swan-neck eaves
and a gilt leaf finial, mithril ribs up the pyramid's corners and on up the spire's (the flèche's
ribs), gilt leaf tips on the four horns (the citadel's gable finials), a mithril coping round the
cornice's edge with a crystal lantern on a silver post at each corner, pointed silver frames round
the flank doors and the arm's arch. Two banners, one down each flank of the shaft."""
from sagekit.building import Building

from ..floodgate import pad
from ..style import ElvenStyle

AXIS = (-5.8, 0.0)
# the needle: from where the pyramid is 4.0 out at its corners (z 146), eaves a little wider
SPIRE = dict(r=4.8, z=146.0, h=23.0, k=4, per_side=3, upturn=0.9, lip=0.35, sweep_pow=1.5)
# EA's pyramid: its corners on the axes, 11.95 out at 134.15, to the point at 151.88
PYRAMID = (11.95, 134.15, 151.88)
# the horns' tips (on the axes, 18.43 out at 137.11; the +x one 12.73 x, 18.53 out): the leaf tip
# stands 0.6 in from each, on the horn's rising top
HORNS = [((12.73, 0.0), (1, 0)), ((-24.22, 0.0), (-1, 0)), ((-5.75, 18.44), (0, 1)), ((-5.75, -18.42), (0, -1))]
HORN_TIP = (0.6, 136.8, 3.2)           # in from the tip, the finial's foot, its height
# banners under the dormers: the plane 7.2 out of the axis (the shaft is 5.72..6.7 out over the
# banner's length), rod just under the ledge (104.75); on the two flanks
BANNER = (7.2, 104.2, 3.6, 24.0)       # d from the axis, z_top, width, length
BANNER_SIDES = ((0, -1), (0, 1))
# the cornice's edge at 52.31 (x -19.36..7.71, |y| 13.54): the flare below it nearly upright (in
# 0.2 a unit), the slope above it going in 0.66 a unit; the arm meets its -x side at |y| < 4.58
CORNICE = [(-19.36, -4.62), (-19.36, -13.54), (7.71, -13.54), (7.71, 13.54), (-19.36, 13.54), (-19.36, 4.62)]
COPING = [(-0.6, 51.2), (0.3, 51.2), (0.45, 51.6), (0.45, 52.6), (0.25, 52.95), (-0.9, 52.95)]
COPING_TAGS = ["trim", "trim", "trim", "trim", "trim", None]
CORNERS = [(7.71, -13.54), (7.71, 13.54), (-19.36, 13.54), (-19.36, -13.54)]
DOOR = dict(half=6.12, z0=0.0, spring=33.93, apex=41.5)
DOOR_X = -5.87
FLANKS = [(-12.25, -1), (12.22, 1)]     # the base's flank faces (y, side)
ARM_FACES = [(-4.58, -1), (4.58, 1)]
ARCH_X = -30.02


class Watchtower(Building):
    style = ElvenStyle()
    source = "EBFWTower"
    target = "EBFWTOWER"
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresP.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWatchtower"
    views = {
        "rts": ((-14.9, 0.0, 80.0), 380, 50, -38, 50),
        "close": ((-8.0, 0.0, 95.0), 230, 24, -30, 45),
        "ingame": ((-14.9, 0.0, 80.0), 829, 53, -62, 50),
    }

    def design(self, kit):
        import math

        from mathutils import Vector as V

        from sagekit.blender.geometry import sweep
        cx, cy = AXIS
        solids = kit.swept_roof(cx, cy, **SPIRE)                                # 1. the needle spire
        # its soffit (the flat birch cap) lies inside EA's pyramid, out of sight: buried
        next(p for p in solids[0].polys if p[1] == "birch" and max(q.z for q in p[0]) - min(q.z for q in p[0]) < 1e-6)[2] = False
        solids += self._ribs()                                                  # 2. mithril ribs
        u, z, h = HORN_TIP                                                      # 3. gilt leaf tips on the horns
        for (x, y), (dx, dy) in HORNS:
            solids += kit.leaf_finial(x - dx * u, y - dy * u, z - 0.3, h)
        solids += sweep(CORNICE, COPING, COPING_TAGS, center=AXIS)[0]           # 4. the cornice's coping
        for x, y in CORNERS:                                                    #    and its corner lanterns
            solids += self._corner_lantern(kit, x - 0.55 * math.copysign(1, x - cx), y - 0.55 * math.copysign(1, y))
        d, z_top, width, length = BANNER                                        # 5. two banners
        for nx, ny in BANNER_SIDES:
            n = V((nx, ny, 0))
            t = V((-n.y, n.x, 0))
            a = V((cx + n.x * d, cy + n.y * d, 0))
            solids += kit.leaf_banner(a, t, n, 0.0, z_top, width, length, d=0.0, free=True)
        for y, side in FLANKS:                                                  # 6. the door and arch frames
            a, t, n = pad.face(y, side)
            solids += kit.arch(a, t, n, -side * DOOR_X, w=0.9, d0=0.0, d1=0.7, ogee=pad.OGEE, **DOOR)
        solids += pad.arch(kit, ARCH_X, ARM_FACES)
        return solids

    @staticmethod
    def _ribs(size=0.3, steps=6):
        """Mithril ribs up the four corners: straight up EA's pyramid from its eaves to the spire's
        foot, then riding the spire's swept corners (its sweep and up-turned eave) to near the tip."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import loft
        cx, cy = AXIS
        r0, z0, apex = PYRAMID
        sp = SPIRE
        out = []
        for c, s_ in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            rad, tan = V((c, s_, 0)), V((-s_, c, 0))

            def sect(rr, zz, lift=1.4):
                p = V((cx + rr * c, cy + rr * s_, zz))
                return [p - tan * size, p - tan * size + rad * size * lift, p + tan * size + rad * size * lift, p + tan * size]
            def edge(rr):                        # the pyramid's corner edge: z at radius rr
                return z0 + (r0 - rr) * (apex - z0) / r0
            zs = sp["z"] + 0.8                   # inside the spire's foot
            rs = r0 * (apex - zs) / (apex - z0)
            out.append(loft([sect(r0 - 0.45, edge(r0 - 0.3)), sect(rs - 0.15, zs)], ["trim"], cap0=("trim", True),
                            cap1=("trim", False)))
            rings = []
            for j in range(steps + 1):
                f = j / steps * 0.9
                rr = sp["r"] * (1 - f) ** sp["sweep_pow"] - 0.05
                zz = sp["z"] + sp["lip"] + sp["h"] * f + sp["upturn"] * max(0.0, 1 - 3 * f)
                rings.append(sect(rr, zz))
            out.append(loft(rings, ["trim"] * steps, cap0=("trim", True), cap1=("trim", True)))
        return out

    @staticmethod
    def _corner_lantern(kit, x, y):
        """A crystal lantern on a slender silver post on the coping's corner: the citadel's ring
        lantern, sized for the tower."""
        from ..shapes import turned
        z = COPING[-1][1] - 0.1
        out = [turned(x, y, [(0.95, z), (0.95, z + 0.4), (0.65, z + 0.75), (0.42, z + 1.3), (0.36, z + 3.4), (0.75, z + 3.8)],
                      ["trim"] * 5, 10, cap0=("trim", False), cap1=("trim", True))]
        return out + kit.crystal_lantern(x, y, z + 3.7, h=6.4, r=1.2)

    def emphasis(self, c, n):
        if c.z > 132:
            return 1.4                        # the spire, its ribs and the horns' tips
        if 78 < c.z < 105:
            return 1.2                        # the banners
        return 1.0
