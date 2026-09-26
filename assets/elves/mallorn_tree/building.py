"""The mallorn tree (ElvenMallornTree, elvenmallorntree.ini): EA's golden mallorn stays a living tree -
its trunk, roots, branches and gold leaves are EA's, the leaves on EA's own cards (and the style's
Foliage layer keeps whatever green the sheet has green). What the Elves built at its foot becomes
finer: EA's spiral stair of boards round the trunk gains a silver balustrade (turned balusters and
a rounded rail following the flight up to the talan), two newel columns with crystal lanterns at its
foot, three slender lantern columns stand among the roots, and two leaf banners hang from the
talan's rail on the camera's side.

EA's EBMalTree lies on a bone turned 90 degrees (world_space: every number here is in model axes).
The target EBMALTREE is the trunk, roots and branches (x -59.2..41.8, y -30.0..39.7, z 0.2..110.9; the
trunk's axis is near (-5, 1.3), radius about 9 at z 15); the stair is EA's V2, a ribbon rising round
S (-7.5, -4.5) from angle -70 degrees at the ground to 146 degrees at the talan (z 36.6), between
radius ~16 and ~27 (outer edge measured below, STAIR); the talan is V2A, a railed platform
x -34.4..-16.6, y -17.7..6.9, z 36.6..40.7; the lamp-bearing maiden on her pedestal is V1
(x -15.2..-6.1, y -31.7..-19.4). All of those stay EA's.

It ships as its own copy, EBMalTree2 (Arnor and a map piece draw EBMalTree); its house flag model
EBHCMalTree is Arnor's too, so the house step ships an own copy of it, EBHCMalTree2, which carries
our banners in the player's colour.
"""
import math

from sagekit.building import Building

from ..style import ElvenStyle

SC = (-7.5, -4.5)            # the stair's axis
# the stair's outer edge: (angle deg round SC, radius, top of the boards)
STAIR = [(-59, 28.7, 1.4), (-42, 26.4, 5.8), (-22, 26.1, 10.2), (-2, 26.8, 13.7), (17, 27.3, 16.5), (34, 27.8, 18.9),
         (52, 27.2, 20.9), (69, 25.9, 23.3), (89, 24.8, 26.2), (108, 24.2, 29.3), (127, 23.3, 32.8), (146, 21.5, 36.6)]
TRUNK = (-5.0, 1.3)
LAMPS = (-25, 45, 160)       # lantern columns among the roots: angles round the trunk, 30 out
# EA's night-only lamps in the tree (N_WINDOW, with a glow card each in N_GLOW): our crystal lanterns
# hang there by day and night, and carry the night light
HUNG = [(24.2, -26.4, 74.8), (0.1, 8.8, 40.2), (-25.9, -15.4, 73.5)]


def stair_point(ang, r, z, inset=0.0):
    a = math.radians(ang)
    return (SC[0] + (r - inset) * math.cos(a), SC[1] + (r - inset) * math.sin(a), z)


def rail(points, r, tag, k=6):
    """A round rail through 3D points: rings across the path, lofted, capped."""
    from mathutils import Vector as V
    from sagekit.blender.geometry import loft
    P = [V(p) for p in points]
    rings = []
    for i, p in enumerate(P):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        s = t.cross(V((0, 0, 1))).normalized()
        u = s.cross(t)
        rings.append([p + r * (math.cos(2 * math.pi * j / k) * s + math.sin(2 * math.pi * j / k) * u) for j in range(k)])
    return loft(rings, [tag] * (len(rings) - 1), cap0=(tag, True), cap1=(tag, True))


class MallornTree(Building):
    style = ElvenStyle()
    source = "EBMalTree"
    target = "EBMALTREE"
    own_model = "EBMalTree2"            # men draws EBMalTree too (sagekit/ownership.py)
    sheet = "EBMalTree.tga"
    sheet_normal = "EBMalTree_NRM.tga"
    own_textures = {"EBMalTree.tga": "EBMalTreH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    world_space = True                  # its bone is tilted 90 degrees
    facet_islands = True                # the trunk's smooth shells unwrap onto themselves (sagekit/blender/layout.py)
    views = {
        "rts": ((-8.7, 4.9, 50.0), 300, 50, -38, 50),
        "close": ((-6.0, -6.0, 16.0), 150, 12, -38, 45),       # under the canopy's edge: the stair and lanterns
        "ingame": ((-8.7, 4.9, 55.5), 826, 53, -62, 50),
    }

    def design(self, kit):
        s = []
        s += self._stair_rail(kit)          # 1. balustrade up EA's spiral stair, newel lanterns
        for ang in LAMPS:                   # 2. lantern columns among the roots
            a = math.radians(ang)
            s += self._lamp(kit, TRUNK[0] + 30.0 * math.cos(a), TRUNK[1] + 30.0 * math.sin(a))
        s += self._banners(kit)             # 3. leaf banners on the talan's rail
        for x, y, z in HUNG:                # 4. crystal lanterns hanging in the tree where EA's lamps were
            s += self._hung(kit, x, y, z)
        return s

    # ------------------------------------------------------------------ 1. stair
    @staticmethod
    def _stair_rail(kit):
        """Turned balusters every ~1.5 along the stair's outer edge (0.7 in), standing on the boards,
        and a rounded silver rail 2.7 over them; at the foot, a newel column with a crystal lantern
        either side of the first board."""
        from ..shapes import turned
        out, tops = [], []
        prof = [(0.2, 0.0), (0.3, 0.7), (0.15, 1.8), (0.22, 2.55), (0.18, 2.95)]     # the top inside the rail
        for (a0, r0, z0), (a1, r1, z1) in zip(STAIR, STAIR[1:]):
            x0, y0, _ = stair_point(a0, r0, z0)
            x1, y1, _ = stair_point(a1, r1, z1)
            m = max(1, round(math.hypot(x1 - x0, y1 - y0) / 1.5))
            for i in range(m):
                f = i / m
                ang, r, z = a0 + (a1 - a0) * f, r0 + (r1 - r0) * f, z0 + (z1 - z0) * f
                x, y, _ = stair_point(ang, r, z, 0.7)
                out.append(turned(x, y, [(w, z - 0.3 + dz) for w, dz in prof], ["trim", "stoneB", "trim", "trim"], k=6,
                                  cap0=("top", False), cap1=("top", False)))
                tops.append((x, y, z + 2.55))
        x, y, _ = stair_point(*STAIR[-1], 0.7)
        tops.append((x, y, STAIR[-1][2] + 2.55))
        out.append(rail(tops, 0.24, "trim"))
        # newels at the foot: outer (the first edge point) and inner (EA's inner edge at -70 deg, r 17.1)
        for ang, r in ((-59, 28.7 - 0.7), (-70, 17.1 + 0.9)):
            x, y, _ = stair_point(ang, r, 1.4)
            out.append(turned(x, y, [(0.95, 0.25), (0.95, 1.6), (1.1, 1.85), (0.8, 2.2)], ["stoneA", "coping", "trim"], k=8,
                              cap0=("stoneB", False), cap1=("top", True)))
            out += kit.column(x, y, 2.2, 7.4, r=0.5, k=8, leaves=5)
            out += kit.crystal_lantern(x, y, 7.4, h=4.2, r=0.65)
        return out

    # ------------------------------------------------------------------ 2. lanterns
    @staticmethod
    def _lamp(kit, x, y):
        """A lantern column among the roots: pedestal, slender shaft, leaf capital, crystal lantern."""
        from ..shapes import turned
        out = [turned(x, y, [(1.2, 0.25), (1.2, 1.4), (1.35, 1.7), (1.0, 2.1)], ["stoneA", "coping", "trim"], k=8,
                      cap0=("stoneB", False), cap1=("top", True))]
        out += kit.column(x, y, 2.1, 11.2, r=0.6, k=8, leaves=5)
        out += kit.crystal_lantern(x, y, 11.2, h=5.0, r=0.8)
        return out

    # ------------------------------------------------------------------ 3. banners
    @staticmethod
    def _banners(kit):
        """Two leaf banners from the talan's south rail (y -17.7, rail top 40.6), facing -y."""
        from mathutils import Vector as V
        a, t, n = V((0, -17.95, 0)), V((1, 0, 0)), V((0, -1, 0))
        out = []
        for u in (-29.5, -21.5):
            out += kit.leaf_banner(a, t, n, u, 40.2, 3.0, 9.0, d=0.2, free=True)
        return out

    # ------------------------------------------------------------------ 4. lanterns in the tree
    @staticmethod
    def _hung(kit, x, y, z):
        """A big crystal lantern (EA's lamps are 6 x 10) centred where EA's night lamp hangs, on a
        gilt rod up into the branches over it."""
        from ..shapes import turned
        h = 7.0
        z0 = z - 0.5 * h
        out = kit.crystal_lantern(x, y, z0, h=h, r=1.5, finial=False)
        out.append(turned(x, y, [(0.16, z0 + 0.9 * h), (0.12, z0 + h + 4.0)], ["gilt"], k=6, cap0=("gilt", False),
                          cap1=("gilt", True)))
        return out

    # ------------------------------------------------------------------ night
    @staticmethod
    def night_lights(kit):
        """Every crystal: the three lanterns in the tree (in place of EA's night lamps, with EA's glow
        cards round them), the stair's newels and the three lantern columns - each lit on the two facets the RTS camera sees (the
        crystal is an octagon with corners at 0, 45, 90... degrees: facets face -22.5 and -67.5),
        within the facet's width."""
        from sagekit.nightlights import Light
        spots = [(x, y, z - 3.5 + 0.36 * 7.0, z - 3.5 + 0.64 * 7.0, 1.5) for x, y, z in HUNG]
        for ang, r in ((-59, 28.7 - 0.7), (-70, 17.1 + 0.9)):
            x, y, _ = stair_point(ang, r, 1.4)
            spots.append((x, y, 7.4 + 0.36 * 4.2, 7.4 + 0.64 * 4.2, 0.65))
        for ang in LAMPS:
            a = math.radians(ang)
            x, y = TRUNK[0] + 30.0 * math.cos(a), TRUNK[1] + 30.0 * math.sin(a)
            spots.append((x, y, 11.2 + 0.36 * 5.0, 11.2 + 0.64 * 5.0, 0.8))
        out = []
        for i, (x, y, z0, z1, r) in enumerate(spots):
            w = 0.3 * r
            for deg in (-22.5, -67.5):
                n = (math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0.0)
                t = (-n[1], n[0], 0.0)
                # no halo: a crystal hanging or standing free has no wall round it to spill light on
                out.append(Light.rect((x + 3.0 * n[0], y + 3.0 * n[1], 0.0), t, n, -w, w, z0, z1, reach=3.0, halo=False,
                                      name="crystal %d %+.0f" % (i, deg)))
        # EA's three canopy glow cards (N_GLOW, 24 across, flat) round the hanging lanterns, kept
        return out + [Light.glow((x, y, z), 24.0, name="canopy glow %d" % i) for i, (x, y, z) in enumerate(HUNG)]

    def emphasis(self, c, n):
        return 1.3 if c.z < 42.0 else 1.0
