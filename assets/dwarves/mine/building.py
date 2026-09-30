"""Dwarven mine (MineShaft_Interface, dwarvenmineshaft.ini): the octagonal gate hall built into the
rock becomes a monumental Erebor mine gate - a deep stepped pointed portal round the tunnel mouth
with a gold rune tympanum, two battered gate pylons carrying gold braziers, a rune lintel and the
fortress's stepped gable between them (a three-peaked stepped crown), and a bronze coping with
solid chevron parapets round the visible roof edge.

The model (DBMine_SKN, skeleton dbmine_skl) is a rock (DBMINE01), this hall (DBMINE02), a watch
tower (V2), the skinned bucket-wheel digger (DIGGER), the ore cart (BODY) and its rails. The hall is
the target: it is the mine's entrance, faces the RTS camera and is rigid on a static bone
(DBMINE02: a pure translation, world = local + (10.915, -3.439, 0)). The digger, the cart, the rails,
the tower and the weapon bones (ARROW01-04, on the tower) are untouched and nothing new comes near
them.

All numbers are DBMINE02 mesh coordinates measured on the original (the gate faces +X):
  walls: back x -10.77, sides y +-23.33 to x 10.76, chamfers to the front face x 18.22 (|y| <= 13.9)
  tunnel mouth: |y| <= 10.87 up to z 21.0, shoulders |y| 6.3 (-Y) / 6.83 (+Y) at 26.9, point 28.4
  rune cornice z 30.5..35.9 (a prow over the gate to x 21.55), roof plane z 37.7, eave at 35.9
  buttress stones in front of the chamfers: inner x 13.1..22.0 |y| 15.2..20.3 (top 13.3), outer
    x 19.1..25.6 |y| 16.05..19.4 (top 12.1, x 19.1..22.9)
  the chamfers carry the night windows (N_WINDOW, z 17.3..25.7) and their glow cards (N_GLOW, a
    plane 2.8 in front of each chamfer): nothing new stands on the chamfers or through the cards
  the rock (DBMINE01) lies over the roof's back half (x < ~3): the crown sits on the front half
Footprint x -10.77..25.64, y -23.33..23.34; height 37.8 (limit +30 %, see max_z_growth: 49.1).
"""
from sagekit.building import Building

from ..style import DwarvenStyle

FRONT = 18.22                     # the gate wall's face
MOUTH_TOP = 21.0                  # jamb top of the tunnel mouth
MOUTH_SHOULDER = {1: 6.83, -1: 6.3}   # shoulder |y| at z 26.9, per side
MOUTH_POINT = 28.4
# the portal's inner outline (half, from the axis y 0): just outside the tunnel mouth's jambs,
# then a taller pointed head than the mouth's flat one; the gap is filled by a rune tympanum
ARCH = [(11.1, 0.0), (11.1, MOUTH_TOP), (7.5, 27.7), (0.0, 30.4)]
PORTAL_BACK, LINTEL = 15.4, 35.4
# two recessed rings (triangle frieze fronts) and the outer ring; every front stands just past the
# cornice prow over the gate (x 21.55, z 30.5..35.9), which the portal swallows; the pylons stand
# 2.6 further forward (to the footprint's edge, x 25.6)
PORTAL_FRONTS, PORTAL_DEPTHS = (21.6, 22.3, 23.0), (0.0, 1.0, 2.0)
PORTAL_OUT = 13.1                 # the outer ring's |y| (= its jamb): the pylons stand outside it
PYLON_Y = (13.1, 17.0)            # the gate pylons' |y|; x from inside the wall (15.4) to ~25
# roof edge runs carrying the coping and chevron parapet (from where the rock leaves the roof to
# the gate crown); the chamfer's parapet runs into the pylon
EAVE = 35.9
RUNS = [[(-3.6, 23.33), (10.76, 23.33), (FRONT, 13.93)], [(-6.0, -23.32), (10.76, -23.32), (FRONT, -13.93)]]
CHAMFER_VISIBLE = 8.0              # along the chamfer to |y| 17.0, the pylon's outer side
COPING = [(0.0, EAVE), (0.0, 38.0), (-0.3, 38.3), (-2.4, 38.3), (-2.4, 36.9)]
COPING_TAGS = ["trim", "top", "top", "stoneA", None]
CHEVRON_Z = (38.3, 40.2, 41.1, 42.0, 43.4)
# banner poles: x of the pole (its banner hangs 0.6 in front, the rod reaching x 25.0 < 25.64), |y|
BANNER_X, BANNER_Y = 23.4, 20.2
BRAZIER = (21.4, 14.65, 46.4)     # the pylons' brazier bowls: centre x, |y|, fire bed (the bowl's top)
HALL_AT = (10.915, -3.449)        # DBMINE02's bone: model = hall coordinates + this


def chevrons(a, t, n, L, z, d0, d1, w=7.2, g=(1.1, 2.2)):
    """A solid parapet of stepped-triangle slabs along u = 0..L (the fortress's chevron parapet at
    any height): z = (foot, slab top, step 1, step 2, point); d0..d1 its thickness along n."""
    from sagekit.blender.geometry import prism_uz
    z0, zb, z1, z2, za = z
    k = max(1, round(L / w))
    w = L / k
    g1, g2 = g
    out = []
    for i in range(k):
        u0, u1 = i * w, (i + 1) * w
        eL = "stoneB" if i == 0 else None
        eR = "stoneB" if i == k - 1 else None
        out.append(prism_uz(a, t, n, [(u0, z0), (u1, z0), (u1, zb), (u0, zb)], d0, d1,
                            [None, eR, "top", eL], "stoneB", "stoneA", bat=0.03))
        out.append(prism_uz(a, t, n, [(u0 + g1, zb), (u1 - g1, zb), (u1 - g1, z1), (u0 + g1, z1)], d0 + 0.2, d1 - 0.3,
                            [None, "stoneB", "top", "stoneB"], "stoneA", "stoneA"))
        out.append(prism_uz(a, t, n, [(u0 + g2, z1), (u1 - g2, z1), (u1 - g2, z2), (u0 + g2, z2)], d0 + 0.4, d1 - 0.5,
                            [None, "stoneB", "top", "stoneB"], "trim", "stoneA"))
        out.append(prism_uz(a, t, n, [(u0 + g2, z2), (u1 - g2, z2), ((u0 + u1) / 2, za)], d0 + 0.4, d1 - 0.5,
                            [None, "top", "top"], "stoneA", "stoneA"))
    return out


def portal(kit, arch, axis, back, fronts, depths, outer_u, lintel_z, reveals=None):
    """A stepped pointed portal on a wall facing +X: rings following `arch` (half outline from the
    axis, jamb foot to point), each from the plane `back` (inside the wall) out to its own front -
    inner rings recessed, carrying the triangle frieze, with bronze reveals (reveals[i]: ring i's
    reveal tag) - the last ring filling out to +-outer_u (its outer sides and top are left for the
    pylons and the lintel to cover) and up to lintel_z."""
    from mathutils import Vector as V

    from sagekit.blender.geometry import loft
    out = []

    def piece(poly, x1, tags, front):
        for side in (1, -1):
            r0 = [V((back, axis + side * u, z)) for u, z in poly]
            r1 = [V((x1, axis + side * u, z)) for u, z in poly]
            out.append(loft([r0, r1], [tags], cap0=("stoneB", True), cap1=(front, True)))
    for i, x1 in enumerate(fronts):
        inner = kit.arch_offset(arch, depths[i])
        rv = (reveals or {}).get(i, "trim|a")
        if i < len(fronts) - 1:
            outer = kit.arch_offset(arch, depths[i + 1])
            for k in range(3):
                piece([inner[k], outer[k], outer[k + 1], inner[k + 1]], x1, [None, None, None, rv], "tri|a")
        else:
            j0, j1, sh, ap = inner
            if outer_u - j0[0] > 1e-3:
                piece([j0, (outer_u, 0.0), (outer_u, j1[1]), j1], x1, [None, None, None, rv], "stoneB")
            piece([j1, (outer_u, j1[1]), (outer_u, lintel_z), (sh[0], lintel_z), sh], x1,
                  [None, None, None, None, rv], "stoneB")
            piece([sh, (sh[0], lintel_z), (0.0, lintel_z), ap], x1, [None, None, None, rv], "stoneB")
    return out


def _fire_points():
    """The two brazier bowls on the gate pylons, just above their fire beds (the gilded flame point
    stands inside the flame), in model coordinates."""
    x, y, z = BRAZIER
    return [(round(x + HALL_AT[0], 1), round(sy * y + HALL_AT[1], 1), round(z + 0.1, 1), "brazier") for sy in (1, -1)]


class Mine(Building):
    style = DwarvenStyle()
    source = "DBMine_SKN"
    target = "DBMINE02"
    sheet = "DBMineA.tga"                     # own texture DBMineH.tga (+ _NRM, _D1, _Snow)
    bake_hidden = ("N_WINDOW", "N_GLOW")      # the night windows and their glow cards
    # braziers on the two gate pylons' bowls: (32.3, 11.2, 46.5), (32.3, -18.1, 46.5); nothing in
    # the tunnel mouth (units use it)
    fire_points = _fire_points()
    # the hall is not what sets the building's height - the watch tower (V2) stands 72.9 high, the
    # hall 37.8 - so its gate crown may rise 30 % (to 48.6) and stay far under the tower
    max_z_growth = 0.30
    views = {                                 # world coordinates (the hall is at +10.9, -3.4)
        "rts": ((14, -8, 22), 250, 50, -38, 50),
        "close": ((31, -4, 24), 125, 22, -28, 45),
        "ingame": ((6, -8, 20), 600, 53, -62, 50),
        "gate": ((33, -3, 22), 95, 8, 4, 40),
    }

    def design(self, kit):
        s = []
        s += portal(kit, ARCH, 0.0, PORTAL_BACK, PORTAL_FRONTS, PORTAL_DEPTHS, PORTAL_OUT, LINTEL,
                    reveals={0: "stoneA"})                      # 1. the stepped pointed portal
        s += self._tympanum()                                   # 2. rune tympanum over the mouth
        s += self._lintel_and_gable()                           # 3. rune lintel + stepped gable
        for sy in (1, -1):
            s += self._pylon(sy)                                # 4. battered pylons with braziers
        s += self._parapets()                                   # 5. coping + chevron parapets
        s += self._banners(kit)                                 # 6. Erebor-blue banner poles
        return s

    # ------------------------------------------------------------------ 6. banners
    @staticmethod
    def _banners(kit):
        """Two banner poles flanking the gate outside the pylons, facing the camera (+X): in front of
        the chamfers (and their glow cards, x <= ~16) at |y| 20.2, their feet butting the outer
        buttress stones; the rods end at |y| 23.3, inside the footprint (23.33). The digger's wheel
        turns at y -32 (hall coordinates) and the cart runs behind the hall: both far off."""
        from mathutils import Vector as V
        s = []
        for sy in (1, -1):
            s += kit.banner_pole(V((BANNER_X, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), sy * BANNER_Y, 37.0, 4.4, 18.0)
        return s

    # ------------------------------------------------------------------ 2. tympanum
    @staticmethod
    def _tympanum():
        """The wall between the tunnel mouth's flat head and the portal's pointed one, faced with a
        gold rune panel standing 0.7 proud of the wall, deep inside the rings."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz
        out = []
        for sy in (1, -1):
            a, t, n = V((FRONT, 0.0, 0)), V((0, sy, 0)), V((1, 0, 0))
            o = MOUTH_SHOULDER[sy]
            j, sh, ap = ARCH[1], ARCH[2], ARCH[3]
            out.append(prism_uz(a, t, n, [(10.87, MOUTH_TOP), (j[0], MOUTH_TOP), sh, (o, 26.9)], 0.0, 0.7,
                                ["stoneB", None, None, "stoneB"], "rune|a", None))
            out.append(prism_uz(a, t, n, [(o, 26.9), sh, ap, (0.0, MOUTH_POINT)], 0.0, 0.7,
                                [None, None, None, "stoneB"], "rune|a", None))
        return out

    # ------------------------------------------------------------------ 3. lintel and gable
    @staticmethod
    def _lintel_and_gable():
        """Between the pylons: a rune lintel over the portal, a bronze cornice, and the fortress's
        stepped gable (triangle-frieze slab, bronze tier, stone gable) - with the two brazier-topped
        pylons it gives the gate a three-peaked stepped crown."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import box_rings, loft, prism_uz

        def R(x0, x1, hy, z):
            return box_rings((x0, x1), (-hy, hy), z, 0)
        Y = PORTAL_OUT
        out = [
            loft([R(PORTAL_BACK, 23.4, Y, LINTEL), R(PORTAL_BACK, 23.4, Y, 38.0)],
                 [[None, "rune", None, "stoneB"]], cap0=("stoneB", True), cap1=("top", False)),
            loft([R(15.0, 24.0, Y, 38.0), R(15.0, 24.0, Y, 38.8)], ["trim"], cap0=("trim", True), cap1=("top", True)),
        ]
        a, t, n = V((0.0, 0.0, 0)), V((0, 1, 0)), V((1, 0, 0))
        for poly, d0, d1, tags, front in (
                ([(-11.0, 38.8), (11.0, 38.8), (11.0, 40.8), (-11.0, 40.8)], 15.8, 23.4, [None, "stoneB", "top", "stoneB"], "tri"),
                ([(-8.4, 40.8), (8.4, 40.8), (8.4, 42.2), (-8.4, 42.2)], 16.4, 22.8, [None, "trim", "top", "trim"], "trim"),
                ([(-8.4, 42.2), (8.4, 42.2), (0.0, 48.6)], 16.4, 22.8, [None, "top", "top"], "stoneA")):
            out.append(prism_uz(a, t, n, poly, d0, d1, tags, front, "stoneA"))
        return out

    # ------------------------------------------------------------------ 4. pylons
    @staticmethod
    def _pylon(sy):
        """A battered gate pylon beside the portal (its inner face is the portal's outer jamb):
        stepped plinth, pilaster rib, rune belt between bronze bands at the cornice's height,
        corbelled triangle frieze, and a gold brazier bowl on its cap. It swallows the inner ends
        of EA's buttress stones; it stays inside the chamfer's night-glow card except for the
        card's outer corner (see README)."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import box_rings, loft, prism_uz
        yi = PYLON_Y[0]

        def R(x1, yo, z, x0=PORTAL_BACK, ch=0.4):
            return box_rings((x0, x1), sorted((sy * yi, sy * yo)), z, ch)
        outer = 4 if sy > 0 else 0          # chamfered ring sides: 0 y0, 2 front, 4 y1, 6 back
        band = lambda tag: [tag if k in (2, outer) else "stoneB" for k in range(8)]  # noqa: E731
        rings = [R(25.6, 17.6, 0.0), R(25.6, 17.6, 2.2),                     # plinth
                 R(25.2, 17.0, 2.2), R(24.6, 16.5, 30.6),                    # battered body
                 R(25.0, 16.9, 30.6), R(25.0, 16.9, 31.2),                   # bronze band
                 R(24.6, 16.5, 31.2), R(24.6, 16.5, 33.8),                   # rune belt (the cornice's height)
                 R(25.0, 16.9, 33.8), R(25.0, 16.9, 34.4),                   # bronze band
                 R(24.5, 16.4, 34.4), R(24.3, 16.2, 41.0),                   # upper body
                 R(25.1, 17.0, 41.0), R(25.1, 17.0, 41.8),                   # corbel
                 R(24.9, 16.8, 41.8), R(24.9, 16.8, 43.6),                   # triangle frieze
                 R(24.3, 16.2, 43.6)]                                        # cap
        tags = ["stoneB", "top", "stoneB", "trim", "trim", "top", band("rune"), "trim", "trim", "top",
                "stoneB", "trim", "trim", "top", band("tri"), "top"]
        out = [loft(rings, tags, cap0=("stoneB", False), cap1=("top", True))]
        a, t, n = V((25.2, sy * (yi + 16.9) / 2, 0)), V((0, 1, 0)), V((1, 0, 0))
        out.append(prism_uz(a, t, n, [(-0.8, 2.2), (0.8, 2.2), (0.8, 30.6), (-0.8, 30.6)], -1.6, 0.4,
                            [None, "stoneB", "top", "stoneB"], "pilaster", None, bat=0.6 / 28.4))
        cx, cy, bed = BRAZIER[0], sy * BRAZIER[1], BRAZIER[2]              # the brazier
        bowl = [box_rings((cx - 1.4, cx + 1.4), (cy - 1.1, cy + 1.1), 43.6, 0.3),
                box_rings((cx - 2.3, cx + 2.3), (cy - 1.75, cy + 1.75), 46.0, 0.4),
                box_rings((cx - 2.3, cx + 2.3), (cy - 1.75, cy + 1.75), bed, 0.4)]
        out.append(loft(bowl, ["trim", "trim"], cap0=("trim", False), cap1=("trim", True)))
        top = box_rings((cx - 1.8, cx + 1.8), (cy - 1.3, cy + 1.3), bed, 0.3)
        out.append(loft([top, [V((cx, cy, 47.8))] * len(top)], ["trim"], cap0=("trim", False), cap1=("trim", False)))
        return out

    # ------------------------------------------------------------------ 5. parapets
    @staticmethod
    def _parapets():
        from sagekit.blender.geometry import sweep
        out = []
        for path in RUNS:
            ss, segs = sweep(path, COPING, COPING_TAGS, cap_start=True, cap_end=False, center=(4.0, 0.0))
            out += ss
            for i, (a, b, t, n) in enumerate(segs):
                L = (b - a).length if i == 0 else CHAMFER_VISIBLE
                out += chevrons(a, t, n, L, CHEVRON_Z, -2.1, -0.3)
        return out

    night_surfaces = ("DBMINE01",)            # the rock carries EA's back window

    @staticmethod
    def night_lights(kit):
        """The tunnel mouth (forge light from the mine), a window on each chamfer where EA's night
        windows were (beside the pylons), and EA's window in the rock at the back."""
        from sagekit.nightlights import Light
        mouth = [(-10.87, 0.2), (10.87, 0.2), (10.87, MOUTH_TOP), (MOUTH_SHOULDER[1], 26.9), (0.0, MOUTH_POINT),
                 (-MOUTH_SHOULDER[-1], 26.9), (-10.87, MOUTH_TOP)]
        out = [Light((FRONT, 0, 0), (0, 1, 0), (1, 0, 0), mouth, kind="door", reach=7.0, name="tunnel mouth")]
        for s in (1, -1):                     # the chamfer from the front face (18.22, +-13.93) back
            out.append(Light.rect((FRONT, s * 13.93, 0), (-0.622, s * 0.783, 0), (0.783, s * 0.622, 0), 3.7, 8.5,
                                  19.0, 24.4, reach=3.0, name="chamfer %+d" % s))
        out.append(Light.rect((-37.3, 1.34, 0), (0, 1, 0), (-1, 0, 0), -2.4, 2.4, 24.2, 29.4, reach=4.0, name="rock"))
        return out

    def emphasis(self, c, n):
        if c.x > 14.5 and abs(c.y) < 18.0:
            return 1.5                        # portal, pylons, gable, braziers: the RTS camera's view
        if c.z > 35.5:
            return 1.3                        # roof parapets
        return 1.0
