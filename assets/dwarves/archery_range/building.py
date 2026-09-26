"""Dwarven archery range (DwarvenArcheryRange), second pass: EA's timber hall rebuilt as Dwarven
masonry and its tower given a fortress crown.

- the hall's gable roof disappears under a stepped stone roof (the fortress's stepped language:
  a gold rune eave course, five stone tiers, a ridge block with a chevron crest); its south end is
  a crow-stepped stone gable between two corner turrets with gilded points;
- the hall walls stand on a battered stone plinth, with pilasters between the windows and a
  corbelled hexagon cornice under the eave;
- the east door becomes a gatehouse front: a deep stepped pointed portal with a rune tympanum and
  rune lintel between two battered pylons with gilded caps, under a stepped crown with a gilded
  point that rises out of the roof;
- the tower top gets a battered crown ring with a gold rune belt, a stepped gable with a gilded
  point on each outer side, and stone bastions round the four timber posts; the posts stand on
  battered stone plinths and keep their rune collars;
- the gallery keeps its chevron parapets, rune fascia and corbel table.

What stays usable: the archer (gallery deck, x -21, y 40..49) and the smith (x -7..-2) and their
line of fire south over the yard, the two ladders (ARCHERYRANGE's, west face y 31..40; V2's,
y 40.6..49.7), the bow and quiver props on the tower top, the door opening, the bones, and the
level-3 storey V2 (from z 80) over the crown. Footprint and height unchanged.

All measurements in ARCHERYRANGE mesh coordinates, taken from the original model
(build/assets/dwarves/archery_range/src/dbarchrnge_skn.w3d)."""
from sagekit.building import Building

from ..style import DwarvenStyle

# meshes left out of the bakes (and the renders): the animated archer and smith, their props,
# the ground plate and the night windows - none of them should shade the sheet, and their
# textures are not extracted
NOT_BAKED = ("SHIELD_PROP", "BOW_PROP", "QUIVER_PROP", "QUIVER", "SHIELD", "DWARF", "ARROW_A01", "BODY_A01",
             "SHOULDER_A01", "HELMET_A01", "LINE03_A01", "SPHERE01_A01", "QUIVER_A01", "ARROW05", "AXE01",
             "AXE02", "AXE03", "AXE04", "AXE05", "AXE06", "ARCHERYBASE", "N_WINDOW")

# the footprint (the original's bounding box): nothing new may pass it
X_MAX, Y_MIN, Y_MAX = 50.2, -24.999, 54.84
# the hall: wall faces x 19.6 (west) / 43.6 (east) / y -22.6 (south), a stone base course to z 5.5
# out to x 18.2 / 45.3 / y -25.0, timber corner pillars (x 18.7..22.3 and 40.4..44.1, y -24..-20.6,
# to z 28.7), windows (frames z 8.8..23.9) west at y -14.1 / -3.5 / 10.0 / 20.4, east at y -14.2 /
# 19.2, south at x 26.5 / 36.0; eave fascia z 26.1..27.6 at x 17.1 / 45.6; the roof: west plane
# x 17.1 (z 27.5) .. 31.5 (z 44.2), east plane x 32.6 (44.2) .. 45.6 (27.5), y -25.0..27.7
HALL_W, HALL_E, HALL_S, HALL_N = 19.6, 43.6, -22.6, 26.0


def roof_xw(z):
    return 17.1 + (z - 27.5) / 1.16


def roof_xe(z):
    return 32.6 + (44.2 - z) / 1.285


# stepped roof: tier k spans z TIERS[k]..TIERS[k+1]; each tier's inner corner sits on EA's roof
# plane, so the old roof is inside the stone
TIERS = (25.6, 28.4, 31.6, 34.8, 38.0, 41.2, 44.4)
RIDGE = (30.0, 34.1, 44.4, 46.8)            # x0, x1, z0, z1 of the ridge block
ROOF_N = 30.2                               # the tower's south wall is at y 30.35
# the east door: opening y -4.6..9.3 between two posts, lintel underside z 19.8, wall front x 45.4
DOOR_AXIS, DOOR_BACK = 2.25, 45.4
DOOR_ARCH = [(7.4, 0.0), (7.4, 20.6), (5.0, 26.0), (0.0, 28.6)]     # half outline from the axis
PORTAL_U, PYLON_U, LINTEL = 12.4, 14.6, 36.5                          # |u| from the axis
# wall plinth, string course and cornice: (d out of the wall, z)
PLINTH = [(0, 0), (3.0, 0), (3.0, 0.8), (1.8, 7.2), (0, 7.6)]
PLINTH_S = [(0, 0), (2.4, 0), (2.4, 5.8), (1.5, 7.2), (0, 7.6)]       # south: the footprint edge
PLINTH_TAGS = [None, "stoneB", "stoneA", "top", None]
COURSE = [(0, 7.0), (2.1, 7.0), (2.1, 8.1), (1.8, 8.5), (0, 8.5)]
COURSE_TAGS = ["trim", "trim", "trim", "top", None]
CORNICE = [(0, 23.2), (1.0, 24.0), (1.0, 24.4), (1.8, 24.4), (1.8, 25.6), (0, 25.6)]
CORNICE_TAGS = ["stoneB", "trim", "trim", "hex", None, None]
# the tower base (x 19..42.88, y 30.35..50.68, walls to z 49.5, archers' floor z 53.8, plank
# railing to z 56.7); its four corner posts (to z 72, V2's legs above at level 3)
TOWER = (19.0, 42.88, 30.35, 50.68)
POSTS = [(14.8, 19.95, 26.02, 31.53), (42.12, 47.27, 26.02, 31.53),
         (42.12, 47.27, 49.4, 54.9), (14.8, 19.95, 49.4, 54.9)]      # footprint at z ~37
# how far each post's stone may grow per side (-x, +x, -y, +y), at its foot and at the tower head:
# the north posts stand on the footprint's edge; up top the SW post's +y face is the ladder's and
# its -x side meets the ladder's rails. A clamped side gets square rings (a chamfer on a side that
# does not grow would leave slivers)
BIG = 9.0
POST_FOOT = [(BIG, BIG, BIG, BIG), (BIG, BIG, BIG, BIG), (BIG, BIG, BIG, 0.0), (BIG, BIG, BIG, 0.0)]
POST_HEAD = [(0.5, BIG, BIG, 0.0), (BIG, BIG, BIG, BIG), (BIG, BIG, BIG, 0.0), (BIG, BIG, BIG, 0.0)]
# cornice under the parapet: corbel, hexagon frieze, bronze drip, walk-top; d out of the wall
TOWER_HEAD = [(0, 44.4), (1.2, 45.4), (1.2, 45.9), (2.6, 47.1), (2.6, 49.9), (3.6, 50.5), (3.6, 51.1), (0, 51.1)]
TOWER_HEAD_TAGS = ["trim", "stoneB", "trim", "hex", "trim", "trim", "top", None]
# crown ring outside the plank railing (d >= 1.7 keeps the bow prop, x <= 44.5, clear): battered
# face, gold rune belt, bronze coping
CROWN = [(1.7, 51.1), (3.6, 51.1), (3.3, 56.2), (3.7, 56.2), (3.7, 58.4), (3.9, 58.4), (3.9, 59.2),
         (3.5, 59.6), (1.7, 59.6)]
CROWN_TAGS = [None, "stoneA", "trim", "rune", "trim", "trim", "top", "top", "stoneB"]
# the gallery (x -30..19, y 29.6..52.5): deck z 27.5, fascia boards z 23.2..29.0
GALLERY_S, GALLERY_N, GALLERY_BOARD = 29.59, 52.47, (23.24, 28.97)


def chevrons(a, t, n, L, z, d0, d1, w=8.0, g=(1.2, 2.4), tip="stoneA"):
    """A solid parapet of stepped-triangle slabs along u = 0..L (the fortress's chevron parapet
    at any height): z = (foot, slab top, step 1, step 2, point); d0..d1 its thickness along n."""
    from sagekit.blender.geometry import prism_uz
    z0, zb, z1, z2, za = z
    k = max(1, round(L / w))
    w = L / k
    out = []
    for i in range(k):
        u0, u1 = i * w, (i + 1) * w
        eL = "stoneB" if i == 0 else None
        eR = "stoneB" if i == k - 1 else None
        g1, g2 = g
        out.append(prism_uz(a, t, n, [(u0, z0), (u1, z0), (u1, zb), (u0, zb)], d0, d1,
                            [None, eR, "top", eL], "stoneB", "stoneA", bat=0.03))
        out.append(prism_uz(a, t, n, [(u0 + g1, zb), (u1 - g1, zb), (u1 - g1, z1), (u0 + g1, z1)], d0 + 0.2, d1 - 0.35,
                            [None, "stoneB", "top", "stoneB"], "stoneA", "stoneA"))
        out.append(prism_uz(a, t, n, [(u0 + g2, z1), (u1 - g2, z1), (u1 - g2, z2), (u0 + g2, z2)], d0 + 0.4, d1 - 0.6,
                            [None, "stoneB", "top", "stoneB"], "trim", "stoneA"))
        out.append(prism_uz(a, t, n, [(u0 + g2, z2), (u1 - g2, z2), ((u0 + u1) / 2, za)], d0 + 0.4, d1 - 0.6,
                            [None, tip, tip], "stoneA", "stoneA"))
    return out


def corbel(a, t, n, s, top, half=0.7, depth=1.25, height=3.1):
    """The kit's corbel with its back kept: under the open gallery its back is seen from below."""
    from sagekit.blender.geometry import loft

    def P(u, d, z):
        return (a.x + t.x * u + n.x * d, a.y + t.y * u + n.y * d, z)

    def ring(u):
        return [P(u, 0.0, top - height), P(u, depth, top), P(u, 0.0, top)]
    return loft([ring(s - half), ring(s + half)], [["stoneB", None, "stoneB"]], cap0=("stoneB", True), cap1=("stoneB", True))


def box(x0, x1, y0, y1, z0, z1, sides, top="top", bottom=True):
    """An axis-aligned block; sides: one tag or [south, east, north, west]."""
    from sagekit.blender.geometry import box_rings, loft
    return loft([box_rings((x0, x1), (y0, y1), z0, 0), box_rings((x0, x1), (y0, y1), z1, 0)], [sides],
                cap0=("stoneB", bottom), cap1=(top, top is not None))


def point(x0, x1, y0, y1, z0, z1, tag="trim"):
    """A squat gilded point on a rectangle: a pyramid, or a hipped ridge along the longer side."""
    from mathutils import Vector as V
    from sagekit.blender.geometry import box_rings, loft
    r = box_rings((x0, x1), (y0, y1), z0, 0)
    cx, cy, h = (x0 + x1) / 2, (y0 + y1) / 2, min(x1 - x0, y1 - y0) / 2
    if x1 - x0 >= y1 - y0:
        a, b = V((x0 + h, cy, z1)), V((x1 - h, cy, z1))
        top = [a, b, b, a]
    else:
        a, b = V((cx, y0 + h, z1)), V((cx, y1 - h, z1))
        top = [a, a, b, b]
    return loft([r, top], [tag], cap0=("top", False), cap1=("top", False))


def portal(kit, arch, axis, back, fronts, depths, outer_u, lintel_z):
    """A free-standing stepped pointed portal on a wall facing +X: rings following `arch` (half
    outline from the axis, jamb foot to point), each from the wall plane `back` out to its own
    front (inner rings recessed, fronts carrying the triangle frieze and bronze reveals), the last
    ring filling out to +-outer_u and up to lintel_z (its top left for a cornice to cover). The
    kit's pointed_arch assumes a recess in existing masonry (its outer faces are buried); this one
    stands proud of the wall."""
    from mathutils import Vector as V
    from sagekit.blender.geometry import loft
    out = []

    def piece(poly, x1, tags, front, back_tag="stoneB"):
        for side in (1, -1):
            r0 = [V((back, axis + side * u, z)) for u, z in poly]
            r1 = [V((x1, axis + side * u, z)) for u, z in poly]
            out.append(loft([r0, r1], [tags], cap0=(back_tag, True), cap1=(front, True)))
    for i, x1 in enumerate(fronts):
        inner = kit.arch_offset(arch, depths[i])
        if i < len(fronts) - 1:
            outer = kit.arch_offset(arch, depths[i + 1])
            for k in range(3):
                piece([inner[k], outer[k], outer[k + 1], inner[k + 1]], x1, [None, None, None, "trim|a"], "tri|a")
        else:
            j0, j1, sh, ap = inner
            piece([j0, (outer_u, 0.0), (outer_u, j1[1]), j1], x1, [None, "stoneB", None, "trim|a"], "stoneB")
            piece([j1, (outer_u, j1[1]), (outer_u, lintel_z), (sh[0], lintel_z), sh], x1,
                  [None, "stoneB", None, None, "trim|a"], "stoneB")
            piece([sh, (sh[0], lintel_z), (0.0, lintel_z), ap], x1, [None, None, None, "trim|a"], "stoneB")
    return out


class ArcheryRange(Building):
    style = DwarvenStyle()
    source = "DBArchRnge_SKN"
    target = "ARCHERYRANGE"
    sheet = "dbarchrnge.tga"
    bake_hidden = NOT_BAKED
    views = {                                   # the whole building, the level-3 storey V2 included
        "rts": ((14, 4, 52), 350, 50, -38, 50),
        "close": ((20, 8, 64), 300, 22, -34, 45),
        "ingame": ((10, 0, 35), 800, 53, -62, 50),
    }

    def design(self, kit):
        s = []
        s += self._roof()                      # 1. stepped stone roof, crow-stepped south gable
        s += self._ridge()                     # 2. chevron crest on the ridge block
        s += self._walls()                     # 3. plinth, string course, pilasters, cornice
        s += self._corner_turrets()            # 4. the gable's corner turrets, gilded points
        s += self._portal(kit)                 # 5. the east gatehouse front
        s += self._tower_head(kit)             # 6. cornice, crown ring, gables
        s += self._post_bastions()             # 7. stone round the posts: plinths, bastions
        s += self._post_collars()              # 8. rune collars on the four tower posts
        s += self._gallery()                   # 9. gallery parapets, rune fascia, corbels
        s += self._banners(kit)                # 10. Erebor-blue banners
        return s

    @staticmethod
    def _banners(kit):
        """Two banners on the tower's east face under the cornice (z 44.4), clear of the post
        bastions; one down the south wall's central pilaster (face d 1.3), under its capital."""
        from mathutils import Vector as V
        east = (V((TOWER[1], 0, 0)), V((0, 1, 0)), V((1, 0, 0)))
        s = []
        for y in (37.2, 43.8):
            s += kit.banner(*east, y, 43.6, 5.0, 16.0)
        s += kit.banner(V((0, HALL_S, 0)), V((1, 0, 0)), V((0, -1, 0)), 31.25, 21.2, 3.9, 11.0, d=1.3)
        # two banner poles flanking the gatehouse, in front of the east wall's plinth (x <= 46.6) and
        # clear of the eave strips (x <= 47.6) and the footprint (x <= 50.2)
        for u in (-17.5, 17.5):
            s += kit.banner_pole(V((48.4, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), DOOR_AXIS + u, 40.0, 5.6, 17.0)
        return s

    # ------------------------------------------------------------------ 1. roof
    @staticmethod
    def _roof():
        """One stepped solid: tier 0 is the eave course (gold runes all round, overhanging the
        cornice), tiers 1-5 step in with EA's roof planes, then the ridge block; the treads are
        rings, so no face is hidden under the tier above. Its south end is the crow-stepped gable,
        flush with the footprint. The eave stops short of the portal on the east and continues
        either side of it as separate strips."""
        from sagekit.blender.geometry import box_rings, loft
        y0, y1 = Y_MIN, ROOF_N

        def R(x0, x1, z):
            return box_rings((x0, x1), (y0, y1), z, 0)
        steps = [(16.2, 45.3)] + [(roof_xw(z) - 0.25, roof_xe(z) + 0.25) for z in TIERS[1:6]] + [RIDGE[:2]]
        tops = list(TIERS[1:6]) + [RIDGE[2], RIDGE[3]]
        fronts = ["rune", "stoneA", "tri", "stoneA", "hex", "stoneA", "trim"]
        sides = ["rune", "stoneB", "stoneA", "stoneB", "stoneA", "stoneB", "hex|a"]
        rings = [box_rings((HALL_W, HALL_E), (HALL_S, y1), TIERS[0], 0), R(*steps[0], TIERS[0])]
        tags = ["stoneB"]                                        # the eave's underside
        for k, (x0, x1) in enumerate(steps):
            z0 = TIERS[0] if k == 0 else tops[k - 1]
            if k:
                rings.append(R(x0, x1, z0))
                tags.append("top")                               # the tread of the tier below
            rings.append(R(x0, x1, tops[k]))
            tags.append([fronts[k], sides[k], "stoneB", sides[k]])
        s = [loft(rings, tags, cap0=("stoneB", False), cap1=("top", True))]
        for ya, yb in ((y0, 2.25 - PYLON_U), (2.25 + PYLON_U, y1)):     # east eave either side of the gate
            s.append(box(45.3, 47.6, ya, yb, TIERS[0], TIERS[1], ["rune", "rune", "rune", None]))
        return s

    # ------------------------------------------------------------------ 2. ridge crest
    @staticmethod
    def _ridge():
        from mathutils import Vector as V
        x0, x1, _, top = RIDGE
        cx, y0, y1 = (x0 + x1) / 2, -21.5, 25.0
        a, t, n = V((cx, y0, 0)), V((0, 1, 0)), V((1, 0, 0))
        return chevrons(a, t, n, y1 - y0, (top, top + 1.4, top + 2.6, top + 3.8, top + 6.4), -1.45, 1.45, w=11.6,
                        g=(1.4, 2.8), tip="trim")

    # ------------------------------------------------------------------ 3. walls
    @staticmethod
    def _walls():
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz, sweep
        s = []
        cen = (31.6, 2.0)
        south_door, north_door = 2.25 - PYLON_U, 2.25 + PYLON_U
        runs = [([(HALL_W, -21.0), (HALL_W, HALL_N)], PLINTH),                   # west: turret to post
                ([(22.3, HALL_S), (40.4, HALL_S)], PLINTH_S),                    # south: turret to turret
                ([(HALL_E, -21.0), (HALL_E, south_door)], PLINTH),               # east, either side of
                ([(HALL_E, north_door), (HALL_E, HALL_N)], PLINTH)]              # the gatehouse
        for path, prof in runs:
            s += sweep(path, prof, PLINTH_TAGS, center=cen)[0]
            s += sweep(path, COURSE if prof is PLINTH else [(d * 0.8, z) for d, z in COURSE], COURSE_TAGS,
                       center=cen)[0]
            s += sweep(path, CORNICE, CORNICE_TAGS, center=cen)[0]
        # pilasters between the windows: (wall anchor, t, n, u centre, half width)
        pil = [(V((HALL_W, 0, 0)), V((0, 1, 0)), V((-1, 0, 0)), y, 1.4) for y in (-8.8, 2.95, 15.25)]
        pil += [(V((HALL_E, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), y, h) for y, h in ((-18.05, 1.15), (23.5, 1.3))]
        pil += [(V((0, HALL_S, 0)), V((1, 0, 0)), V((0, -1, 0)), 31.25, 1.4)]
        for a, t, n, u, h in pil:
            s.append(prism_uz(a, t, n, [(u - h, 8.5), (u + h, 8.5), (u + h, 22.2), (u - h, 22.2)], -0.2, 1.3,
                              [None, "stoneB", None, "stoneB"], "pilaster", None))
            s.append(prism_uz(a, t, n, [(u - h - 0.3, 22.2), (u + h + 0.3, 22.2), (u + h + 0.3, 23.2), (u - h - 0.3, 23.2)],
                              -0.2, 1.7, ["trim", "trim", "top", "trim"], "trim", None))
        return s

    # ------------------------------------------------------------------ 4. corner turrets
    @staticmethod
    def _corner_turrets():
        """Square turrets over the south corner pillars, battered, with a rune belt under a bronze
        cap and a gilded point: the feet of the crow-stepped gable."""
        from sagekit.blender.geometry import box_rings, loft
        s = []
        for x0, x1 in ((17.0, 22.8), (39.9, 45.7)):
            y0, y1 = Y_MIN, -20.0

            def R(z, e, ch=0.0, south=0.0):
                return box_rings((x0 - e, x1 + e), (y0 + south, y1 + e), z, ch)
            rings = [R(0.0, 0.4), R(1.2, 0.4), R(1.2, 0.0), R(31.0, -0.4, 0, 0.4), R(31.0, 0.0), R(33.6, 0.0),
                     R(33.6, -0.4, 0, 0.4), R(34.4, -0.4, 0, 0.4), R(34.4, 0.2, 0, 0.0), R(35.4, 0.2, 0, 0.0),
                     R(35.4, -0.8, 0, 0.8), R(37.6, -1.1, 0, 1.1)]
            tags = ["stoneB", "top", "stoneA", "trim", "rune", "trim", "stoneB", "trim", "trim", "top", "stoneA"]
            s.append(loft(rings, tags, cap0=("top", False), cap1=("top", True)))
            s.append(point(x0 + 1.3, x1 - 1.3, y0 + 1.3, y1 - 1.3, 37.6, 42.6))
        return s

    # ------------------------------------------------------------------ 5. gatehouse front
    def _portal(self, kit):
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        s = portal(kit, DOOR_ARCH, DOOR_AXIS, DOOR_BACK, fronts=(47.0, 48.2, 49.4), depths=(0.0, 1.4, 2.8),
                   outer_u=PORTAL_U, lintel_z=LINTEL)
        a, t, n = V((DOOR_BACK, DOOR_AXIS, 0)), V((0, 1, 0)), V((1, 0, 0))
        tym = [(-7.4, 20.4), (7.4, 20.4), (7.4, 20.6), (5.0, 26.0), (0.0, 28.6), (-5.0, 26.0), (-7.4, 20.6)]
        s.append(prism_uz(a, t, n, tym, 0.0, 0.8, ["trim", None, None, None, None, None, None], "rune", "stoneB"))
        d = 49.4 - DOOR_BACK                              # the outer ring's front
        s.append(prism_uz(a, t, n, [(-PORTAL_U, 33.0), (PORTAL_U, 33.0), (PORTAL_U, 35.9), (-PORTAL_U, 35.9)],
                          d - 0.1, d + 0.45, ["trim", "trim", None, "trim"], "rune", None))
        # the crown: from the roof (its back inside the tiers) out over the lintel
        back = 37.5 - DOOR_BACK
        for poly, d1, tags, front in (
                ([(-13.2, LINTEL), (13.2, LINTEL), (13.2, 37.7), (-13.2, 37.7)], 4.7, ["trim", "trim", "top", "trim"], "trim"),
                ([(-11.0, 37.7), (11.0, 37.7), (11.0, 41.3), (-11.0, 41.3)], 4.1, [None, "stoneB", "top", "stoneB"], "rune"),
                ([(-8.4, 41.3), (8.4, 41.3), (8.4, 44.3), (-8.4, 44.3)], 3.6, [None, "stoneB", "top", "stoneB"], "tri"),
                ([(-5.8, 44.3), (5.8, 44.3), (5.8, 47.3), (-5.8, 47.3)], 3.1, [None, "stoneA", "top", "stoneA"], "stoneA"),
                ([(-5.8, 47.3), (5.8, 47.3), (0.0, 53.4)], 3.1, [None, "top", "top"], "tri|a")):
            s.append(prism_uz(a, t, n, poly, back, d1, tags, front, "stoneB"))
        s.append(box(DOOR_BACK + 0.6, DOOR_BACK + 2.9, DOOR_AXIS - 1.3, DOOR_AXIS + 1.3, 51.6, 54.2, "trim"))
        s.append(point(DOOR_BACK + 0.6, DOOR_BACK + 2.9, DOOR_AXIS - 1.3, DOOR_AXIS + 1.3, 54.2, 57.6))
        for side in (1, -1):
            s += self._pylon(side)
        return s

    @staticmethod
    def _pylon(side):
        """A battered pylon beside the portal (u 12.4..14.6 from its axis, window frames just
        outside): stepped plinth, rune belt, bronze cap, gilded point."""
        from sagekit.blender.geometry import box_rings, loft
        ui, uo = PORTAL_U, PYLON_U

        def R(z, fx, e=0.0):
            ys = sorted((DOOR_AXIS + side * ui, DOOR_AXIS + side * (uo + e)))
            return box_rings((HALL_E, fx), ys, z, 0)
        rings = [R(0.0, 50.1, 0.5), R(2.0, 50.1, 0.5), R(2.0, 49.6), R(29.5, 49.0), R(29.5, 49.3, 0.3),
                 R(32.9, 49.3, 0.3), R(32.9, 48.95), R(38.4, 48.8), R(38.4, 49.4, 0.4), R(39.6, 49.4, 0.4),
                 R(39.6, 48.4, -0.6), R(42.0, 48.1, -0.9)]
        o = 0 if side < 0 else 2                        # the pylon's outer side (away from the door)
        belt = ["rune" if k in (1, o) else "stoneB" for k in range(4)]
        body = ["stoneA" if k in (1, o) else "stoneB" for k in range(4)]
        tags = ["stoneB", "top", body, "trim", belt, "trim", body, "trim", "trim", "top", "stoneA"]
        out = [loft(rings, tags, cap0=("top", False), cap1=("top", True))]
        ys = sorted((DOOR_AXIS + side * (ui + 0.1), DOOR_AXIS + side * (uo - 1.0)))
        out.append(point(HALL_E + 0.3, 47.8, ys[0], ys[1], 42.0, 45.6))
        return out

    # ------------------------------------------------------------------ 6. tower head
    @staticmethod
    def _tower_head(kit):
        """Each side between the post bastions: the corbelled hexagon cornice, then the battered
        crown ring with its rune belt; on the east, north and south sides a stepped gable with a
        gilded point and a stepped merlon either side. The west ring stops north of the ladder
        (y 31..40) and carries no gable (V2's ladder leans there at level 3)."""
        from sagekit.blender.geometry import prism_uz, sweep
        x0, x1, y0, y1 = TOWER
        cen = ((x0 + x1) / 2, (y0 + y1) / 2)
        sides = [((x1, 31.0), (x1, 49.9), None),                    # east
                 ((42.3, y1), (19.8, y1), None),                    # north
                 ((19.8, y0), (42.3, y0), None),                    # south
                 ((x0, 49.9), (x0, 31.0), (x0, 41.0))]              # west: the ladder climbs at y 31..40
        s = []
        for p, q, stop in sides:
            ss, segs = sweep([p, q], TOWER_HEAD, TOWER_HEAD_TAGS, cap_start=False, cap_end=False, center=cen)
            s += ss
            s += sweep([p, stop or q], CROWN, CROWN_TAGS, cap_start=False, cap_end=False, center=cen)[0]
            if stop:                                # the ring ends in a pier north of the ladder
                s.append(box(x0 - 4.1, x0 - 1.5, 40.4, 41.8, 51.1, 61.2, ["stoneA", "stoneB", "stoneB", "stoneA"]))
                s.append(point(x0 - 4.1, x0 - 1.5, 40.4, 41.8, 61.2, 63.4))
                continue
            a, b, t, n = segs[0]
            L = (b - a).length
            m = L / 2
            for poly, dd, tags, front in (
                    ([(m - 6.6, 59.6), (m + 6.6, 59.6), (m + 6.6, 61.0), (m - 6.6, 61.0)], (1.7, 4.1),
                     ["top", "trim", "top", "trim"], "trim"),
                    ([(m - 4.8, 61.0), (m + 4.8, 61.0), (m + 4.8, 64.0), (m - 4.8, 64.0)], (1.9, 3.8),
                     [None, "stoneB", "top", "stoneB"], "tri"),
                    ([(m - 4.8, 64.0), (m + 4.8, 64.0), (m, 69.4)], (1.9, 3.8), [None, "top", "top"], "stoneA")):
                s.append(prism_uz(a, t, n, poly, dd[0], dd[1], tags, front, "stoneB"))
            s.append(prism_uz(a, t, n, [(m - 0.9, 68.0), (m + 0.9, 68.0), (m + 0.9, 69.8), (m - 0.9, 69.8)], 2.0, 3.7,
                              ["stoneB", "trim", "top", "trim"], "trim", "trim"))
            s.append(prism_uz(a, t, n, [(m - 0.9, 69.8), (m + 0.9, 69.8), (m, 71.8)], 2.0, 3.7,
                              [None, "trim", "trim"], "trim", "trim"))
            gap = m - 6.6 - 1.6                     # between the gable and the bastion
            if gap >= 2.6:
                for u in (1.6 + gap / 2, L - 1.6 - gap / 2):
                    s.append(prism_uz(a, t, n, [(u - 1.2, 59.6), (u + 1.2, 59.6), (u + 1.2, 61.8), (u - 1.2, 61.8)],
                                      1.9, 3.7, [None, "stoneB", "top", "stoneB"], "stoneA", "stoneB"))
                    s.append(prism_uz(a, t, n, [(u - 1.2, 61.8), (u + 1.2, 61.8), (u, 63.8)], 1.9, 3.7,
                                      [None, "trim", "trim"], "stoneA", "stoneB"))
        return s

    # ------------------------------------------------------------------ 7. post bastions
    @staticmethod
    def _post_bastions():
        """Stone round each timber post: a battered plinth at its foot and, at the tower head, a
        bastion (stone shaft, rune belt, bronze coping, battered top) that the post rises out of.
        Growth per side is limited by the footprint and the ladder (POST_GROW)."""
        from sagekit.blender.geometry import box_rings, loft
        s = []
        for (xa, xb, ya, yb), gf, gh in zip(POSTS, POST_FOOT, POST_HEAD):
            yb = min(yb, Y_MAX)

            def R(z, e, ch, g):
                ex = [min(e, gi) if e > 0 else e for gi in g]
                return box_rings((xa - ex[0], xb + ex[1]), (ya - ex[2], min(yb + ex[3], Y_MAX)), z,
                                 ch if min(g) >= BIG else 0.0)
            foot = [R(0.0, 2.0, 0.5, gf), R(1.4, 2.0, 0.5, gf), R(1.4, 1.5, 0.4, gf), R(10.6, 0.7, 0.3, gf),
                    R(10.6, 1.1, 0.3, gf), R(11.8, 1.1, 0.3, gf), R(12.4, 0.0, 0.1, gf)]
            s.append(loft(foot, ["stoneB", "top", "stoneA", "trim", "trim", "top"], cap0=("top", False),
                          cap1=("top", False)))
            head = [R(43.6, 0.0, 0.1, gh), R(44.4, 0.9, 0.3, gh), R(55.6, 0.9, 0.3, gh), R(55.6, 1.3, 0.4, gh),
                    R(58.0, 1.3, 0.4, gh), R(58.0, 1.5, 0.45, gh), R(58.9, 1.5, 0.45, gh), R(58.9, 0.9, 0.3, gh),
                    R(61.4, 0.5, 0.2, gh)]
            s.append(loft(head, ["trim", "stoneB", "trim", "rune", "trim", "trim", "top", "stoneA"],
                          cap0=("top", False), cap1=("top", True)))
        return s

    # ------------------------------------------------------------------ 8. post collars
    @staticmethod
    def _post_collars():
        from sagekit.blender.geometry import box_rings, loft
        s = []
        for xa, xb, ya, yb in POSTS:
            rings = [box_rings((xa - e, xb + e), (ya - e, min(yb + e, Y_MAX)), z, ch)
                     for z, e, ch in ((35.2, -0.05, 0.1), (35.8, 0.75, 0.45), (38.6, 0.75, 0.45), (39.2, -0.05, 0.1))]
            s.append(loft(rings, ["trim", "rune", "trim"], cap0=("stoneB", False), cap1=("stoneB", False)))
        return s

    # ------------------------------------------------------------------ 9. gallery
    @staticmethod
    def _gallery():
        """South parapet from east of the ground ladder (the archer, at x -21 on the north deck,
        shoots south over it at z ~34), north parapet post to post."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        s = []
        zb0, zb1 = GALLERY_BOARD
        for y, xs, xe in ((GALLERY_S, -16.2, 15.0), (GALLERY_N, -29.05, 15.0)):
            ny = -1 if y < 40 else 1
            a, t, n = V((xs, y, 0)), V((1, 0, 0)), V((0, ny, 0))
            L = xe - xs
            s += chevrons(a, t, n, L, (zb1 - 0.05, 31.6, 32.4, 33.2, 34.7), -1.0, 0.5, w=7.8, g=(1.0, 2.0), tip="trim")
            s.append(prism_uz(a, t, n, [(0.0, zb0 + 0.9), (L, zb0 + 0.9), (L, zb1 - 0.75), (0.0, zb1 - 0.75)],
                              -0.1, 0.3, ["trim", "stoneB", "trim", "stoneB"], "rune", None))
            s.append(prism_uz(a, t, n, [(0.0, zb0 - 0.9), (L, zb0 - 0.9), (L, zb0 + 0.3), (0.0, zb0 + 0.3)],
                              -0.1, 1.3, ["trim", "stoneB", "top", "stoneB"], "trim", "stoneB"))  # corbel table
            k = max(1, round(L / 6.2))
            for i in range(k):
                s.append(corbel(a, t, n, (i + 0.5) * L / k, zb0 - 0.9))
        return s

    # ------------------------------------------------------------------ night lights
    @staticmethod
    def night_lights(kit):
        """EA's hall windows (kept in our walls between the pilasters, under the cornice), the
        tower's windows under the crown, and the gatehouse door: forge light from inside."""
        from sagekit.nightlights import Light
        X, Y, mX, mY = (1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0)
        out = []
        for x, n, ys in ((HALL_W, mX, (-14.1, -3.5, 10.0, 20.4)), (HALL_E, X, (-14.2, 19.2))):
            out += [Light.rect((x, 0, 0), Y, n, y - 1.7, y + 1.7, 10.0, 21.0, reach=3.0, name="hall %+.0f" % y) for y in ys]
        out += [Light.rect((0, HALL_S, 0), X, mY, x - 1.7, x + 1.7, 10.0, 21.0, reach=3.0, name="gable %.0f" % x)
                for x in (26.5, 36.0)]
        out += [Light.rect((TOWER[1], 0, 0), Y, X, y - 1.7, y + 1.7, 30.4, 40.4, reach=3.0, name="tower E %.0f" % y)
                for y in (36.2, 44.7)]
        out += [Light.rect((0, TOWER[3], 0), X, Y, x - 1.7, x + 1.7, 30.4, 40.4, reach=3.0, name="tower N %.0f" % x)
                for x in (26.8, 35.5)]
        out.append(Light.rect((DOOR_BACK, DOOR_AXIS, 0), Y, X, -6.9, 6.9, 0.3, 19.8, kind="door", reach=5.0, name="gate"))
        return out

    def emphasis(self, c, n):
        if c.x > 45.0 and abs(c.y - DOOR_AXIS) < 18:
            return 1.5                       # the gatehouse front
        if c.z > 50.0:
            return 1.45                      # tower crown, ridge crest
        if c.y < -24.0 or c.z > 25.0:
            return 1.25                      # the stepped gable and roof
        return 1.0
