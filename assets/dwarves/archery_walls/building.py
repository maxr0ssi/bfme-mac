"""Dwarven archery range, level 2 (Upgrade_StructureLevel2): the yard walls V1A, redesigned on the
finished level-3 tower (`base`, itself on the archery range), in the fortress's wall language.

EA's V1A is four plain battered walls round the shooting yard (west x -32.7..-27.4, south y
-52.4..-47.4, east x 18.5..23.8 up to the hall, north y 47.6..52.5 under the gallery), 16.9 high
with a ridged top, and a stepped plaque on the west and south walls. Now:

- a coping over every wall's ridge (a gold rune band on blue enamel between bronze edges) carries
  a crest of solid stepped chevrons with gilded tips - the fortress's chevron parapet, scaled to a
  low yard wall (within the 20 % height limit);
- a battered plinth with a bronze string course runs along the faces the footprint allows (the
  outer north and east faces are EA's footprint edge; the ground ladder leans on the west wall's
  inner face north of y 16);
- EA's two plaques become reliefs in stepped niches: stone pilasters with bronze capitals and
  gilded points either side, a stepped lintel with the triangle frieze over them;
- Erebor-blue banners hang from the coping on the south and west outer faces.

Footprint = V1A's. The V1 obelisks at the yard's south corners, the gallery post the west wall
ends in (y 27.6) and the hall's corner turret the east wall meets (y -25.4) are left alone; the
chevron crest stops short of each. All measurements in V1A mesh coordinates (= the model's), taken
from the archery range's finished model."""
from sagekit.building import Building

from ..archery_range.building import NOT_BAKED, chevrons
from ..style import DwarvenStyle

X_MIN, X_MAX, Y_MIN, Y_MAX = -34.35, 23.83, -54.2, 52.54
# the walls' ridge lines (centre of each wall) and the stretches the crest may use
RIDGE_W, RIDGE_S, RIDGE_E, RIDGE_N = -30.05, -49.9, 21.15, 50.05
# the coping: over the ridge (z 16.8) and the battered top (half width 1.6 at z 14.3)
COPING = [(-2.0, 14.3), (2.0, 14.3), (2.2, 14.8), (2.2, 16.4), (2.0, 16.95), (-2.0, 16.95), (-2.2, 16.4), (-2.2, 14.8)]
COPING_TAGS = ["stoneB", "trim", "rune", "trim", "top", "trim", "rune", "trim"]
CREST = (16.95, 18.0, 18.7, 19.4, 20.2)      # chevron slab foot, slab top, step 1, step 2, point
# battered plinth and string course on a vertical wall face (d out of it, z)
PLINTH = [(0, 0), (1.5, 0), (1.5, 0.6), (0.5, 4.0), (0, 4.3)]
PLINTH_TAGS = [None, "stoneB", "stoneA", "top", None]
COURSE = [(-1.0, 8.4), (0.5, 8.4), (0.5, 9.3), (0.25, 9.7), (-1.0, 9.7)]     # its back in the wall (battered above 9.1)
COURSE_TAGS = ["trim", "trim", "trim", "top", "stoneB"]      # back kept: EA's east wall is open where it meets the hall
# EA's plaques: (face, extent along the face in world x or y, how far they stand out of it): west
# (face x -32.7, y -6.7..3.6, to z 13.3, out to x -34.35) and south (face y -52.4, x -8.0..2.3, to -54.2)
PLAQUES = [("W", (-6.7, 3.6), 1.65), ("S", (-8.0, 2.3), 1.8)]


def wall_frame(name):
    """(anchor, t, n) of a wall's outer face: t x n = -z (bands and banners read the right way)."""
    from mathutils import Vector as V
    if name == "W":
        return V((-32.7, 0, 0)), V((0, -1, 0)), V((-1, 0, 0))
    return V((0, -52.4, 0)), V((1, 0, 0)), V((0, -1, 0))


class ArcheryWalls(Building):
    style = DwarvenStyle()
    base = "dwarves/archery_tower"
    source = "DBArchRnge_SKN"
    target = "V1A"
    sheet = "dbarchrnge.tga"
    own_textures = {"dbarchrnge.tga": "DBArchRngW.tga"}
    house_tags = ()                 # the cloth stays in V1A: the house-colour model is shown at every level
    # EA's lightly damaged range chips a few faces off its walls (V1A: 95 of 139 triangles, same
    # place and extent): the damaged range shows our walls whole, on the damaged sheet
    also_derived = ("DBArchRnge_D1",)
    bake_hidden = NOT_BAKED
    views = {                                   # the yard from the south-west, and the south wall close
        "rts": ((-6, 0, 20), 330, 50, -128, 50),
        "close": ((-8, -40, 10), 120, 20, -110, 45),
        "ingame": ((10, 0, 35), 850, 53, -62, 50),
    }

    def design(self, kit):
        s = []
        s += self._coping()                    # 1. rune coping on every wall
        s += self._crest()                     # 2. the chevron crest, gilded tips
        s += self._plinths()                   # 3. battered plinth, string course
        s += self._niches()                    # 4. EA's plaques in stepped niches
        s += self._banners(kit)                # 5. banners on the outer faces
        return s

    # ------------------------------------------------------------------ 1. coping
    @staticmethod
    def _coping():
        from sagekit.blender.geometry import sweep
        runs = [[(RIDGE_W, 29.0), (RIDGE_W, RIDGE_S), (RIDGE_E, RIDGE_S), (RIDGE_E, -21.7)],
                [(-28.9, RIDGE_N), (18.9, RIDGE_N)]]
        out = []
        for path in runs:
            out += sweep(path, COPING, COPING_TAGS, center=(-5.0, 0.0))[0]
        return out

    # ------------------------------------------------------------------ 2. crest
    @staticmethod
    def _crest():
        """Stepped chevrons along each ridge, between the obelisks (V1, x <= -27.6 and >= 18.5 at
        the south corners), the gallery post (y >= 27.6) and the hall's turret (y >= -25.4)."""
        from mathutils import Vector as V
        out = []
        for a, t, L in ((V((RIDGE_W, -47.0, 0)), V((0, 1, 0)), 27.2 + 47.0),
                        (V((-27.2, RIDGE_S, 0)), V((1, 0, 0)), 18.2 + 27.2),
                        (V((RIDGE_E, -47.0, 0)), V((0, 1, 0)), 47.0 - 25.8),
                        (V((-28.6, RIDGE_N, 0)), V((1, 0, 0)), 18.6 + 28.6)):
            n = V((t.y, -t.x, 0))
            out += chevrons(a, t, n, L, CREST, -1.3, 1.3, w=6.0, g=(0.9, 1.8), tip="trim")
        return out

    # ------------------------------------------------------------------ 3. plinths
    @staticmethod
    def _plinths():
        """Along each face the footprint and the ground ladder allow: (from, to, a point on the far
        side of the face - the sweep's d points away from it). The outer north and east faces are
        the footprint's edge; the ground ladder leans on the west wall's yard face north of y 16."""
        from sagekit.blender.geometry import sweep
        runs = [((-32.7, 27.6), (-32.7, -47.3), (0.0, 0.0)),               # west, outer
                ((-27.6, -52.4), (18.5, -52.4), (0.0, 0.0)),               # south, outer
                ((-27.4, 16.0), (-27.4, -47.4), (-100.0, 0.0)),            # west, yard side
                ((-27.4, -47.4), (19.5, -47.4), (0.0, -100.0)),            # south, yard side
                ((19.5, -47.4), (18.59, -24.0), (100.0, -35.0)),           # east, yard side (to the turret)
                ((-28.9, 47.6), (18.9, 47.6), (0.0, 100.0))]               # north, yard side
        out = []
        for p, q, far in runs:
            out += sweep([p, q], PLINTH, PLINTH_TAGS, center=far)[0]
            out += sweep([p, q], COURSE, COURSE_TAGS, center=far)[0]
        return out

    # ------------------------------------------------------------------ 4. niches
    @staticmethod
    def _niches():
        """Each plaque (EA's, left as it is: its face is the footprint's edge) between two stone
        pilasters with bronze capitals, under a stepped lintel with the triangle frieze that reaches
        back to the coping - a relief in a niche. Backs go deep: the wall is battered above z 9.1."""
        from sagekit.blender.geometry import prism_uz
        out = []
        for name, (w0, w1), depth in PLAQUES:
            a, t, n = wall_frame(name)
            c0, c1 = (w0, w1) if t.x + t.y > 0 else (-w1, -w0)
            d1 = depth - 0.3
            for u0, u1 in ((c0 - 2.0, c0 - 0.3), (c1 + 0.3, c1 + 2.0)):
                for poly, dd, tags, front in (
                        ([(u0 - 0.3, 0.0), (u1 + 0.3, 0.0), (u1 + 0.3, 1.2), (u0 - 0.3, 1.2)], d1 + 0.2,
                         [None, "stoneB", "top", "stoneB"], "stoneB"),
                        ([(u0, 1.2), (u1, 1.2), (u1, 12.8), (u0, 12.8)], d1, [None, "stoneB", None, "stoneB"], "pilaster"),
                        ([(u0 - 0.25, 12.8), (u1 + 0.25, 12.8), (u1 + 0.25, 13.6), (u0 - 0.25, 13.6)], d1 + 0.2,
                         ["trim", "trim", None, "trim"], "trim")):
                    out.append(prism_uz(a, t, n, poly, -1.6, dd, tags, front, None))
            out.append(prism_uz(a, t, n, [(c0 - 2.6, 13.6), (c1 + 2.6, 13.6), (c1 + 2.6, 14.9), (c0 - 2.6, 14.9)],
                                -1.6, d1 + 0.2, ["stoneB", "stoneB", "top", "stoneB"], "tri", None))
        return out

    # ------------------------------------------------------------------ 5. banners
    @staticmethod
    def _banners(kit):
        """Hung free from under the coping, in front of the battered upper wall and clear of the
        plinth; two on the south face, two on the west face either side of the plaque."""
        out = []
        for name, us in (("S", (-17.5, 10.5)), ("W", (22.0, -18.0))):
            a, t, n = wall_frame(name)
            for u in us:
                out += kit.banner(a, t, n, u, 13.6, 3.6, 7.6, d=0.6, free=True)
        return out

    def emphasis(self, c, n):
        if c.z > 14.0:
            return 1.35                      # coping and crest: what the RTS camera sees most
        return 1.0

