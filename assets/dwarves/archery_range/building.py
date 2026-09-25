"""Dwarven archery range (DwarvenArcheryRange): the timber hall, the archers' tower base and the
raised gallery re-dressed in the fortress's vocabulary - a deep stepped pointed portal on the
hall's east door, a chevron crest on the roof ridge, a stepped relief in the south gable, a
corbelled hexagon cornice and chevron parapet round the tower top, bronze rune collars on the
four tower posts, a chevron parapet with rune fascia and corbels on the gallery, battered
plinths along the hall. All measurements are in ARCHERYRANGE mesh coordinates, taken from the
original model (build/assets/dwarves/archery_range/src/dbarchrnge_skn.w3d)."""
from sagekit.building import Building

from ..style import DwarvenStyle

# meshes left out of the bakes (and the renders): the animated archer and smith, their props,
# the ground plate and the night windows - none of them should shade the sheet, and their
# textures are not extracted
NOT_BAKED = ("SHIELD_PROP", "BOW_PROP", "QUIVER_PROP", "QUIVER", "SHIELD", "DWARF", "ARROW_A01", "BODY_A01",
             "SHOULDER_A01", "HELMET_A01", "LINE03_A01", "SPHERE01_A01", "QUIVER_A01", "ARROW05", "AXE01",
             "AXE02", "AXE03", "AXE04", "AXE05", "AXE06", "ARCHERYBASE", "N_WINDOW")

# the hall (x 18..45.5, y -25..29): walls to z 26-28.7, gable roof, ridge x 31.47..32.59 at z 44.2
RIDGE_X, RIDGE_Z, ROOF_SLOPE = 32.03, 44.18, 1.187
# its east door: opening y -4.6..9.3 between two posts, lintel underside z 19.8, wall front x 45.5
DOOR_AXIS, DOOR_BACK = 2.25, 45.4
DOOR_ARCH = [(7.4, 0.0), (7.4, 20.6), (5.0, 26.0), (0.0, 28.6)]     # half outline from the axis
# the tower base (x 19..42.88, y 30.35..50.68, walls to z 49.5, archers' floor z 53.8, plank
# railing to z 56.7); its four corner posts (to z 71, V2's legs above) cover the corners
TOWER = (19.0, 42.88, 30.35, 50.68)
POSTS = [(14.8, 19.95, 26.02, 31.53), (42.12, 47.27, 26.02, 31.53),
         (42.12, 47.27, 49.4, 54.9), (14.8, 19.95, 49.4, 54.9)]      # footprint at z ~37
# cornice under the parapet: corbel, hexagon frieze, bronze drip, walk-top; d out of the wall
TOWER_HEAD = [(0, 44.4), (1.2, 45.4), (1.2, 45.9), (2.6, 47.1), (2.6, 49.9), (3.6, 50.5), (3.6, 51.1), (0, 51.1)]
TOWER_HEAD_TAGS = ["trim", "stoneB", "trim", "hex", "trim", "trim", "top", None]
# the gallery (x -30..19, y 29.6..52.5): deck z 27.5, fascia boards z 23.2..29.0
GALLERY_S, GALLERY_N, GALLERY_BOARD = 29.59, 52.47, (23.24, 28.97)
Y_MAX = 54.84                           # the footprint's north edge (the north posts' faces)


def chevrons(a, t, n, L, z, d0, d1, w=8.0, g=(1.2, 2.4)):
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
                            [None, "top", "top"], "stoneA", "stoneA"))
    return out


def corbel(a, t, n, s, top, half=0.7, depth=1.25, height=3.1):
    """The kit's corbel with its back kept: under the open gallery its back is seen from below."""
    from sagekit.blender.geometry import loft

    def P(u, d, z):
        return (a.x + t.x * u + n.x * d, a.y + t.y * u + n.y * d, z)

    def ring(u):
        return [P(u, 0.0, top - height), P(u, depth, top), P(u, 0.0, top)]
    return loft([ring(s - half), ring(s + half)], [["stoneB", None, "stoneB"]], cap0=("stoneB", True), cap1=("stoneB", True))


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

    def design(self, kit):
        s = []
        s += self._portal(kit)                 # 1. the east door's stepped pointed portal
        s += self._ridge()                     # 2. chevron crest on the hall ridge
        s += self._gable_relief()              # 3. stepped relief in the south gable
        s += self._tower_head()                # 4. corbelled cornice + chevron parapet
        s += self._post_collars()              # 5. rune collars on the four tower posts
        s += self._gallery()                   # 6. gallery parapets, rune fascia, corbels
        s += self._plinths()                   # 7. battered plinths along the hall
        return s

    # ------------------------------------------------------------------ 1. portal
    def _portal(self, kit):
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        s = portal(kit, DOOR_ARCH, DOOR_AXIS, DOOR_BACK, fronts=(47.0, 48.2, 49.4), depths=(0.0, 1.4, 2.8),
                   outer_u=12.4, lintel_z=35.0)
        a, t, n = V((DOOR_BACK, DOOR_AXIS, 0)), V((0, 1, 0)), V((1, 0, 0))
        tym = [(-7.4, 20.4), (7.4, 20.4), (7.4, 20.6), (5.0, 26.0), (0.0, 28.6), (-5.0, 26.0), (-7.4, 20.6)]
        s.append(prism_uz(a, t, n, tym, 0.0, 0.8, ["trim", None, None, None, None, None, None], "rune", "stoneB"))
        d = 49.4 - DOOR_BACK                              # the outer ring's front
        s.append(prism_uz(a, t, n, [(-12.4, 32.6), (12.4, 32.6), (12.4, 35.0), (-12.4, 35.0)], d - 0.1, d + 0.4,
                          ["trim", "trim", None, "trim"], "rune", None))
        for poly, d1, tags, front in (
                ([(-13.0, 35.0), (13.0, 35.0), (13.0, 36.2), (-13.0, 36.2)], 4.6, ["trim", "trim", "top", "trim"], "trim"),
                ([(-9.2, 36.2), (9.2, 36.2), (9.2, 38.8), (-9.2, 38.8)], 3.5, [None, "stoneB", "top", "stoneB"], "tri"),
                ([(-6.2, 38.8), (6.2, 38.8), (6.2, 40.8), (-6.2, 40.8)], 2.9, [None, "stoneB", "top", "stoneB"], "stoneA"),
                ([(-6.2, 40.8), (6.2, 40.8), (0.0, 44.5)], 2.9, [None, "top", "top"], "stoneA")):
            s.append(prism_uz(a, t, n, poly, 0.0, d1, tags, front, "stoneB"))
        return s

    # ------------------------------------------------------------------ 2. ridge crest
    @staticmethod
    def _ridge():
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft
        y0, y1, hw, top = -21.5, 25.0, 2.03, 45.3
        foot = RIDGE_Z - (31.47 - (RIDGE_X - hw)) * ROOF_SLOPE - 0.15    # just under the roof at its sides
        s = [loft([box_rings((RIDGE_X - hw, RIDGE_X + hw), (y0, y1), foot, 0),
                   box_rings((RIDGE_X - hw, RIDGE_X + hw), (y0, y1), top, 0)],
                  [["stoneB", "hex|a", "stoneB", "hex|a"]], cap0=("top", False), cap1=("top", True))]
        a, t, n = V((RIDGE_X, y0, 0)), V((0, 1, 0)), V((1, 0, 0))
        s += chevrons(a, t, n, y1 - y0, (top, top + 1.4, top + 2.6, top + 3.8, top + 6.2), -1.25, 1.25, w=11.6,
                      g=(1.4, 2.8))
        return s

    # ------------------------------------------------------------------ 3. gable relief
    @staticmethod
    def _gable_relief():
        """Three stepped tiers and a point on the south gable, under the crossed barge boards."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        a, t, n = V((31.84, -22.55, 0)), V((1, 0, 0)), V((0, -1, 0))
        s = []
        for poly, d1, front in (
                ([(-7.5, 28.0), (7.5, 28.0), (7.5, 30.5), (-7.5, 30.5)], 1.45, "rune"),
                ([(-5.3, 30.5), (5.3, 30.5), (5.3, 33.0), (-5.3, 33.0)], 1.2, "trim"),
                ([(-3.2, 33.0), (3.2, 33.0), (3.2, 35.5), (-3.2, 35.5)], 1.0, "stoneA"),
                ([(-3.2, 35.5), (3.2, 35.5), (0.0, 38.5)], 1.0, "trim")):
            tags = ["trim", "stoneB", "top", "stoneB"] if len(poly) == 4 else [None, "top", "top"]
            s.append(prism_uz(a, t, n, poly, 0.0, d1, tags, front, None))
        return s

    # ------------------------------------------------------------------ 4. tower head
    @staticmethod
    def _tower_head():
        """Each side between the corner posts: a corbelled cornice with the hexagon frieze, then a
        solid chevron parapet outside the plank railing (the west one only north of the ladder)."""
        from sagekit.blender.geometry import sweep
        x0, x1, y0, y1 = TOWER
        cen = ((x0 + x1) / 2, (y0 + y1) / 2)
        sides = [((x1, 31.0), (x1, 49.9), None),                 # east
                 ((42.3, y1), (19.8, y1), None),                 # north
                 ((19.8, y0), (42.3, y0), None),                 # south
                 ((x0, 49.9), (x0, 31.0), 49.9 - 41.0)]          # west: the ladder climbs at y 31..40
        s = []
        for p, q, parapet in sides:
            ss, segs = sweep([p, q], TOWER_HEAD, TOWER_HEAD_TAGS, cap_start=False, cap_end=False, center=cen)
            s += ss
            a, b, t, n = segs[0]
            L = parapet or (b - a).length
            s += chevrons(a, t, n, L, (51.1, 56.8, 58.2, 59.6, 62.6), 1.7, 3.5, w=8.0 if parapet is None else 9.0,
                          g=(1.0, 2.0))
        return s

    # ------------------------------------------------------------------ 5. post collars
    @staticmethod
    def _post_collars():
        from sagekit.blender.geometry import box_rings, loft
        s = []
        for xa, xb, ya, yb in POSTS:
            rings = [box_rings((xa - e, xb + e), (ya - e, min(yb + e, Y_MAX)), z, ch)
                     for z, e, ch in ((35.2, -0.05, 0.1), (35.8, 0.75, 0.45), (38.6, 0.75, 0.45), (39.2, -0.05, 0.1))]
            s.append(loft(rings, ["trim", "rune", "trim"], cap0=("stoneB", False), cap1=("stoneB", False)))
        return s

    # ------------------------------------------------------------------ 6. gallery
    @staticmethod
    def _gallery():
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        s = []
        zb0, zb1 = GALLERY_BOARD
        # south: from east of the ground ladder to the tower post; north: post to post
        for y, xs, xe in ((GALLERY_S, -16.2, 15.0), (GALLERY_N, -29.05, 15.0)):
            ny = -1 if y < 40 else 1
            a, t, n = V((xs, y, 0)), V((1, 0, 0)), V((0, ny, 0))
            L = xe - xs
            s += chevrons(a, t, n, L, (zb1 - 0.05, 31.6, 32.4, 33.2, 34.7), -1.0, 0.5, w=7.8, g=(1.0, 2.0))
            s.append(prism_uz(a, t, n, [(0.0, zb0 + 0.9), (L, zb0 + 0.9), (L, zb1 - 0.75), (0.0, zb1 - 0.75)],
                              -0.1, 0.3, ["trim", "stoneB", "trim", "stoneB"], "rune", None))
            s.append(prism_uz(a, t, n, [(0.0, zb0 - 0.9), (L, zb0 - 0.9), (L, zb0 + 0.3), (0.0, zb0 + 0.3)],
                              -0.1, 1.3, ["trim", "stoneB", "top", "stoneB"], "trim", "stoneB"))  # corbel table
            k = max(1, round(L / 6.2))
            for i in range(k):
                s.append(corbel(a, t, n, (i + 0.5) * L / k, zb0 - 0.9))
        return s

    # ------------------------------------------------------------------ 7. plinths
    @staticmethod
    def _plinths():
        from sagekit.blender.geometry import sweep
        from ..shapes import LOW_TALUS, TALUS_TAGS
        s = []
        for path in ([(19.3, -24.0), (19.3, 26.0)],                      # west, to the tower post
                     [(44.2, -24.0), (44.2, -10.0)], [(44.2, 14.5), (44.2, 26.0)]):   # east, round the portal
            s += sweep(path, LOW_TALUS, TALUS_TAGS, center=(31.8, 2.0))[0]
        return s

    def emphasis(self, c, n):
        if c.x > 45.3 and abs(c.y - DOOR_AXIS) < 14:
            return 1.5                       # the portal
        if c.z > 44.0:
            return 1.4                       # ridge crest, tower head, parapets
        return 1.15 if c.z > 26 else 1.0
