"""The Dwarven summoned citadel (DwarvenSummonedCitadelKeep): a rock spire with three tower heads
breaking out of it and a gate at its foot. It takes the redesigned fortress's language so the two
read as one family: battered crown rings with stepped-pyramid corners and stepped gables on every
tower head, a gilded stepped pinnacle on the shield tower, a deep stepped pointed portal with a
rune lintel and a stepped crown at the gate, and two Erebor-blue banner poles before it.

Model DBCitadel, redesigned mesh TOWER (the tower heads, the tower plinth and the gate; the rock
STONEA and the three statues are EA's, untouched). The citadel's object has no house-colour model,
so the banners stay palette blue. Nothing leaves TOWER's bounding box (x -50.47..52.92,
y -40.71..52.5): the crown rings are pulled in where a head touches it (the keep's +Y face, the
round tower's -X corner). All measurements in TOWER mesh coordinates, taken from the original.

The flame upgrade (DBFFlam, drawn at the same origin) stands its two braziers on open ground at
x 80.8..90.4, |y| <= 19.6, beside the rock: nothing here comes near them."""
import math

from sagekit.building import Building

from ..style import DwarvenStyle

S2 = math.sqrt(0.5)

# the keep: an irregular octagon (flat sides 14 long on the axes, chamfers 24.7), its head a rune
# band z 100.3..110.3 over an overhanging flare, a 2.4-wide rim at 110.3 round a bronze disc
# (108.0). The +Y flat is the bounding box, so the crown's path is pulled 1.3 in there.
KEEP_C = (0.3, 28.0)
KEEP = [(7.3, 3.5), (24.8, 21.0), (24.8, 35.0), (7.3, 51.2), (-6.8, 51.2), (-24.2, 35.0), (-24.2, 21.0),
        (-6.8, 3.5), (7.3, 3.5)]
KEEP_TOP = 110.3
# crown ring (d outward from the head's face, z) on the rim: a bronze corbel, a triangle-frieze
# band, a battered parapet; the inner face stands on the rim's inner edge
CROWN = [(-2.4, 110.3), (0.0, 110.3), (1.2, 111.3), (1.2, 114.1), (0.7, 114.6), (0.4, 114.6), (0.1, 116.6),
         (-0.7, 116.6), (-1.5, 115.5), (-2.4, 115.5)]
CROWN_TAGS = [None, "trim", "tri", "trim", "top", "stoneA", "top", "top", "top", "stoneA"]
CROWN_TOP = 116.6

# the shield tower: a square head turned 45 degrees about (32.6, -4.4) (u, v its own axes): bronze
# shields out to 15.9 (tops at 89.6, their double windows z 77.4..86.6), corner posts to 94.4 and a
# stone cap (87.0 -> 97.5, |u|,|v| 8.3 at the top, a vent in it). Its crown is the fortress's tower
# crown (head: corbel + hexagon frieze; stepped crown ring) lowered 18.5, just clear of the
# windows, on the shields' outline with its corners cut on the posts (axis-aligned faces here).
SHIELD_C = (32.6, -4.4)
SHIELD_UV = [(15.9, -9.0), (15.9, 9.0), (9.0, 15.9), (-9.0, 15.9), (-15.9, 9.0), (-15.9, -9.0), (-9.0, -15.9),
             (9.0, -15.9)]
SHIELD_DZ = -18.5
CAP_TOP = 97.5
TOWER_HEAD = [(0, 105.2), (1.1, 106.2), (1.1, 106.6), (2.3, 107.6), (2.3, 110.4), (1.9, 110.8), (-2.9, 110.8),
              (-2.9, 108.7)]
TOWER_HEAD_TAGS = ["trim", "stoneB", "trim", "hex", "trim", None, "stoneA", "stoneB"]
TOWER_CROWN = [(-2.9, 110.8), (2.3, 110.8), (1.6, 114.8), (1.6, 115.3), (0.6, 115.3), (0.2, 117.4), (-0.6, 117.4),
               (-1.6, 116.2), (-2.9, 116.2)]
TOWER_CROWN_TAGS = [None, "stoneB", "trim", "top", "stoneA", "top", "top", "top", "stoneA"]

# the round tower: a hexagon of bronze shields about (-33.75, -6.0), rim at 78.2 round a bronze
# floor (76.5). Its -X corner (-50.5, -1.5) is the bounding box: the path is pulled 1.5 in there.
ROUND_C = (-33.75, -6.0)
ROUND = [(-49.05, -1.89), (-46.0, -18.2), (-29.3, -22.7), (-17.0, -10.5), (-21.5, 6.3), (-38.2, 10.7), (-49.05, -1.89)]
ROUND_TOP = 78.2

# the gate faces -Y: axis x 10.1; EA's frame (front y -29.6, back in the rock at -22.8) round an
# opening |x - 10.1| <= 11.8 up to 23.1, shouldered to 8.5 at 35.0, flat top 35.0; the rock face
# stands at y -22.8..-25 up to z ~48. Bollards in front: |x - 10.1| 12.2..17.8 to y -38.2 and
# 13.2..16.9 to y -40.7 (z <= 14.9), kept. The new portal runs from inside the rock (y -22.0)
# forward in four steps; its half outline (from the axis: jamb foot, jamb top, shoulder, point)
# is EA's opening closed in a point over the flat top.
GATE_X = 10.1
ARCH = [(11.8, 0.0), (11.8, 23.1), (8.5, 35.0), (0.0, 38.6)]
PORTAL_BACK = -22.0
PORTAL_DEPTHS = (-0.15, 1.5, 3.0, 4.4)                  # ring offsets out of the opening
PORTAL_FRONTS = (-30.6, -31.6, -32.6, -33.4)             # each ring's front (the outer rings stand forward)
PORTAL_OUT, PORTAL_TOP = 19.2, 45.0
# two banner poles before the gate, beside the bollards, inside the bounding box (y >= -40.71;
# the statues stand at x <= -37 and x >= 42.4): (height, banner width, length)
POLES_Y, POLES_X, POLE = -39.0, (GATE_X - 22.5, GATE_X + 22.5), (40.0, 6.0, 17.0)


def shield_xy(u, v):
    return (SHIELD_C[0] + (u + v) * S2, SHIELD_C[1] + (u - v) * S2)


def closed_bottoms(solids):
    """Keep the bottom faces of solids that overhang open air (the kit drops them): the keep's
    corner pyramids reach over the rim's inner edge."""
    for s in solids:
        zmin = min(p.z for poly, _, _ in s.polys for p in poly)
        for e in s.polys:
            if all(abs(p.z - zmin) < 1e-4 for p in e[0]):
                e[2] = True
    return solids


class Citadel(Building):
    style = DwarvenStyle()
    source = "DBCitadel"
    target = "TOWER"
    sheet = None                                                # the faction atlas DBFortress1
    own_textures = {"DBFortress1.tga": "DBFortressK.tga"}       # H C E F M B S G are taken
    tri_budget = 15000
    views = {
        "rts": ((8, -2, 62), 440, 50, -38, 50),
        "close": ((12, -8, 72), 300, 24, -42, 45),
        "ingame": ((8, 0, 50), 1050, 53, -62, 50),
        "gate": ((GATE_X, -30, 34), 150, 12, -78, 40),
    }

    # ------------------------------------------------------------------ framework work-arounds
    def texture_names(self):
        """EA's DBCitadel files name the sheet in lower case (dbfortress1.tga): the derived-model
        check looks the name up case-sensitively, so hand it a dict that ignores case."""
        return _AnyCase(super().texture_names())

    # ------------------------------------------------------------------ design
    def design(self, kit):
        solids = []
        solids += self._keep_crown(kit)
        solids += self._shield_crown(kit)
        solids += self._pinnacle()
        solids += self._round_crown(kit)
        solids += self._portal(kit)
        solids += self._gate_crown()
        solids += self._poles(kit)
        return solids

    @staticmethod
    def _keep_crown(kit):
        """The keep: a crown ring on the rim, stepped pyramids on the four flats, stepped gables on
        the four long chamfers."""
        from sagekit.blender.geometry import sweep
        out, segs = sweep(KEEP, CROWN, CROWN_TAGS, center=KEEP_C)
        dz = KEEP_TOP - 110.8
        for a, b, t, n in segs:
            L = (b - a).length
            if L < 20:                                  # a flat: a stepped pyramid over it
                m = (a + b) / 2 - n * 2.7
                p = kit.step_pyramid(m.x, m.y, dz=dz)
                out += closed_bottoms(p[:1]) + p[1:]
            else:
                out += kit.step_gable(a, t, n, L / 2, dz=CROWN_TOP - 117.4)
        return out

    @staticmethod
    def _shield_crown(kit):
        """The shield tower: the fortress's tower head and crown on the shields' outline, stepped
        pyramids on the four cut corners (over the posts), stepped gables on the four shields."""
        from sagekit.blender.geometry import sweep
        path = [shield_xy(u, v) for u, v in reversed(SHIELD_UV)]
        path.append(path[0])
        out, segs = sweep(path, [(d, z + SHIELD_DZ) for d, z in TOWER_HEAD], TOWER_HEAD_TAGS, center=SHIELD_C)
        out += sweep(path, [(d, z + SHIELD_DZ) for d, z in TOWER_CROWN], TOWER_CROWN_TAGS, center=SHIELD_C)[0]
        for a, b, t, n in segs:
            L = (b - a).length
            if L < 12:                                  # a cut corner
                m = (a + b) / 2 - n * 1.5
                out += kit.step_pyramid(m.x, m.y, dz=SHIELD_DZ)
            else:
                out += kit.step_gable(a, t, n, L / 2, dz=SHIELD_DZ)
        return out

    @staticmethod
    def _pinnacle():
        """A gilded stepped pinnacle on the shield tower's cap (over its vent), turned with the
        tower: hexagon-chain tier, bronze step, triangle-frieze tier, plain tier, squat point."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft, rect_ring
        t, n = (S2, S2), (S2, -S2)
        z0 = CAP_TOP

        def R(h, z, ch):
            return rect_ring(SHIELD_C, t, n, -h, h, -h, h, z, ch)

        def sides(tag, other="stoneB"):
            return [tag if k % 2 == 0 else other for k in range(8)]
        rings = [R(6.8, z0 - 0.3, 0.8), R(6.3, z0 + 4.4, 0.7), R(6.7, z0 + 4.4, 0.7), R(6.7, z0 + 5.6, 0.7),
                 R(5.0, z0 + 5.6, 0.6), R(4.6, z0 + 9.6, 0.5), R(3.3, z0 + 9.6, 0.4), R(3.0, z0 + 12.4, 0.35),
                 R(2.1, z0 + 12.4, 0.3)]
        tags = [sides("hex"), "trim", "trim", "top", sides("tri"), "top", "stoneA", "top"]
        out = [loft(rings, tags, cap0=("top", False), cap1=("top", False))]
        top = rings[-1]
        out.append(loft([top, [V((SHIELD_C[0], SHIELD_C[1], z0 + 16.8))] * len(top)], ["trim"],
                        cap0=("top", False), cap1=("top", False)))
        return out

    @staticmethod
    def _round_crown(kit):
        """The round tower: the keep's crown ring on its rim and a stepped gable on each side."""
        from sagekit.blender.geometry import sweep
        dz = ROUND_TOP - KEEP_TOP
        out, segs = sweep(ROUND, [(d, z + dz) for d, z in CROWN], CROWN_TAGS, center=ROUND_C)
        for a, b, t, n in segs:
            out += kit.step_gable(a, t, n, (b - a).length / 2, dz=CROWN_TOP + dz - 117.4)
        return out

    @staticmethod
    def _portal(kit):
        """The gate's deep pointed portal: rings stepping forward round EA's opening (triangle
        frieze on their fronts, bronze reveals), the last filling out to |x - 10.1| 19.2 and up to
        45.0; all run back into the rock, so no side shows a hollow."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import loft
        out = []

        def piece(poly, y1, tags, front):
            for side in (1, -1):
                def X(s):
                    return GATE_X + side * s
                r0 = [V((X(s), PORTAL_BACK, z)) for s, z in poly]
                r1 = [V((X(s), y1, z)) for s, z in poly]
                out.append(loft([r0, r1], [tags], cap0=("stoneB", True), cap1=(front, True)))
        D, F = PORTAL_DEPTHS, PORTAL_FRONTS
        for i in range(len(D) - 1):
            inner, outer = kit.arch_offset(ARCH, D[i]), kit.arch_offset(ARCH, D[i + 1])
            for k in range(3):
                piece([inner[k], outer[k], outer[k + 1], inner[k + 1]], F[i], [None, None, None, "trim|a"], "tri|a")
        j0, j1, sh, ap = kit.arch_offset(ARCH, D[-1])
        o, top = PORTAL_OUT, PORTAL_TOP
        piece([j0, (o, 0.0), (o, j1[1]), j1], F[-1], [None, "stoneB", None, "trim|a"], "stoneB")
        piece([j1, (o, j1[1]), (o, top), (sh[0], top), sh], F[-1], [None, "stoneB", "top", None, "trim|a"], "stoneB")
        piece([sh, (sh[0], top), (0.0, top), ap], F[-1], [None, "top", None, "trim|a"], "stoneB")
        return out

    @staticmethod
    def _gate_crown():
        """Over the portal: a lintel carrying the rune frieze, a bronze cornice, a triangle-frieze
        tier, a hexagon-chain tier and a stepped gable facing out, all run back into the rock."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft, prism_uz
        x, back = GATE_X, PORTAL_BACK

        def B(h, front, z):
            return box_rings((x - h, x + h), (front, back), z, 0)

        def front(tag):                                   # box sides: 0 front (-Y), 1 +X, 2 back, 3 -X
            return [tag, "stoneA", "stoneA", "stoneA"]
        rings = [B(19.2, -33.4, 45.0), B(19.2, -33.4, 51.2),            # rune lintel
                 B(19.9, -34.1, 51.2), B(19.9, -34.1, 52.0),            # bronze cornice
                 B(19.4, -33.7, 52.0), B(19.4, -33.7, 56.2),            # triangle-frieze tier
                 B(19.8, -34.1, 56.2), B(19.8, -34.1, 56.8),            # bronze step
                 B(15.2, -33.2, 56.8), B(15.2, -33.2, 61.0),            # hexagon tier
                 B(15.6, -33.6, 61.0), B(15.6, -33.6, 61.6)]            # bronze step
        def step(tag):                                    # a ledge: its back side is a line on the rock
            return [tag, tag, None, tag]
        tags = [front("rune"), step("trim"), "trim", step("top"), front("tri"), step("trim"), "trim", step("top"),
                front("hex"), step("trim"), "trim"]
        out = [loft(rings, tags, cap0=("stoneA", False), cap1=("top", True))]
        a, t, n = V((x, 0, 0)), V((1, 0, 0)), V((0, -1, 0))   # u = x - axis, d = -y
        d0 = -back
        for poly, tg, d1, face in (
                ([(-12.0, 61.6), (12.0, 61.6), (12.0, 63.4), (-12.0, 63.4)], [None, "stoneB", "top", "stoneB"], 33.0, "trim"),
                ([(-8.4, 63.4), (8.4, 63.4), (8.4, 65.4), (-8.4, 65.4)], [None, "stoneB", "top", "stoneB"], 32.6, "stoneA"),
                ([(-8.4, 65.4), (8.4, 65.4), (0.0, 71.8)], [None, "top", "top"], 32.6, "tri|a")):
            out.append(prism_uz(a, t, n, poly, d0, d1, tg, face, "stoneA"))
        return out

    @staticmethod
    def _poles(kit):
        """Two banner poles before the gate, either side of the approach, banners facing out."""
        from mathutils import Vector as V
        a, t, n = V((0, POLES_Y, 0)), V((1, 0, 0)), V((0, -1, 0))
        out = []
        h, w, L = POLE
        for x in POLES_X:
            out += kit.banner_pole(a, t, n, x, h, w, L)
        return out

    def emphasis(self, c, n):
        if c.z > 104:
            return 1.45                       # the keep's head and crown, the pinnacle
        if c.z > 84 and c.x > 8:
            return 1.35                       # the shield tower's crown
        if c.y < -20 and c.z < 72:
            return 1.3                        # the gate
        return 1.0


class _AnyCase(dict):
    def get(self, k, d=None):
        return next((v for kk, v in self.items() if kk.lower() == k.lower()), d)
