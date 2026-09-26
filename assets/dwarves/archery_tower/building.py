"""Dwarven archery range, level 3 (Upgrade_StructureLevel3): the tower storey V2, redesigned on the
finished archery range (`base`), so it matches the stone range below it and the fortress towers.

EA's V2 is a timber storey on four tall legs over the tower top, with gothic windows, a shingle
pyramid spire and horned eaves, and a ladder from the gallery deck up its west side. Now:

- the four legs rise out of the range's post bastions as stone piers (bronze foot, rune belt at
  the loggia, a second rune belt at the arrow slits), up into the crown;
- the storey stands on a stepped stone course (bronze fillet, hexagon frieze, bronze coping) and
  is walled in stone, with a pointed arrow slit in a proud stepped frame at each of EA's six
  arrow bones (ARROW_01..12: the level-3 arrows leave through them), and an Erebor-blue banner
  between the slits on each of the three faces the arrows use;
- over it a corbelled cornice (bronze band, hexagon frieze) carries a crown ring overhanging east
  and west (EA's eave horns live inside it), with a gold rune belt on blue enamel and bronze coping;
- on the crown: a step pyramid on each corner and a stepped gable on each side (the fortress
  crown), and in the middle a stepped stone spire round EA's pyramid - six tiers (triangle and
  hexagon friezes), a bronze collar and a gilded point.

What stays usable: the arrow bones (the slits frame them; nothing new in front of them), V2's
ladder (y 40.6..49.7: the storey course's west face is at x 17.9, where the ladder meets the
wall), the open loggia on the tower top (props, crown finials <= 71.8: V2's course starts at
76.2), the bones. Footprint = V2's; height +9 %.

All measurements in V2 mesh coordinates (= the model's), taken from the archery range's finished
model (build/assets/dwarves/archery_range/out/art/w3d/db/dbarchrnge_skn.w3d)."""
from sagekit.building import Building

from ..archery_range.building import NOT_BAKED, point
from ..style import DwarvenStyle

# V2's footprint (its bounding box; the ladder sets x min)
X_MIN, X_MAX, Y_MIN, Y_MAX = 6.61, 50.24, 26.03, 54.845
# EA's storey: timber box x 19.0..42.9, y 30.4..50.7, z 81..110.9; floor beams to x 18.2 / 43.9,
# y 28.9 / 51.2 (z 80.2..87.4); pointed windows z 91.9..107.2, frames 1 proud (to x 43.9, y 29.0 /
# 51.7). The pyramid spire: base z 110.37, x 18.57..43.3, y 29.59..51.21, apex (30.93, 40.4, 136.68).
# The eave horns reach x 12.0 / 50.2 at z 114.2..115 (y 28.2..29.4 and 51.4..52.6).
PYR = (30.93, 40.40, 110.37, 136.68, 12.37, 10.81)       # cx, cy, z base, z apex, half x, half y
# the four legs (flared to these at z 80.3; tapered to x 15.6..20.0 etc. at 65.1 and 108.2) and
# the sides each pier may grow on (-x, +x, -y, +y): not past the footprint, not toward the
# ladder (NW: y < 49.4, x < 14.8) or the bow prop (NE: y < 49.4)
PIERS = [((14.8, 20.8, Y_MIN, 31.5), (1, 1, 0, 1)), ((41.3, 47.3, Y_MIN, 31.5), (1, 1, 0, 1)),
         ((41.3, 47.3, 49.4, Y_MAX), (1, 1, 0, 0)), ((14.8, 20.8, 49.4, Y_MAX), (0, 1, 0, 0))]
# the storey course (on the tower top's open loggia), the stone skin, the crown ring
COURSE = (17.9, 45.0, 28.0, 52.8)
SKIN = (18.6, 44.4, 28.6, 52.2)
CROWN = (11.9, X_MAX, Y_MIN, Y_MAX)
Z_COURSE, Z_SKIN, Z_CORNICE, Z_CROWN, Z_TOP = 76.2, 87.8, 103.6, 108.4, 117.0
# arrow slits: sill, jamb top, point (the bones are at z 96.1..99.9), half width; centres per face
SLIT = (92.5, 100.9, 102.4, 0.9)
SLITS = {"E": (36.2, 44.8), "S": (27.2, 35.8), "N": (26.85, 35.5)}
# the spire: tier bottoms (the last tier ends at 137.2, over EA's apex)
TIERS = (117.0, 120.6, 124.2, 127.8, 131.4, 135.0, 137.2)
TIER_TAGS = ("stoneA", "tri", "stoneA", "hex", "stoneA", "trim")


def lerp(a, b, f):
    return tuple(x + (y - x) * f for x, y in zip(a, b))


def inset(r, e):
    return (r[0] + e, r[1] - e, r[2] + e, r[3] - e)


def ring(r, z):
    from sagekit.blender.geometry import box_rings
    return box_rings((r[0], r[1]), (r[2], r[3]), z, 0)


def faces():
    """The storey's four faces between the piers: (name, anchor, t, n, u0, u1, d of EA's wall).
    t x n = -z on every face (the kit's convention: bands and banners read the right way)."""
    from mathutils import Vector as V
    x0, x1, y0, y1 = SKIN
    return [("E", V((x1, 0, 0)), V((0, 1, 0)), V((1, 0, 0)), 31.5, 49.4, 42.9 - x1),
            ("S", V((0, y0, 0)), V((1, 0, 0)), V((0, -1, 0)), 20.8, 41.3, y0 - 30.4),
            ("N", V((0, y1, 0)), V((-1, 0, 0)), V((0, 1, 0)), -41.3, -20.8, 50.7 - y1),
            ("W", V((x0, 0, 0)), V((0, -1, 0)), V((-1, 0, 0)), -49.4, -31.5, x0 - 19.0)]


class ArcheryTower(Building):
    style = DwarvenStyle()
    base = "dwarves/archery_range"
    source = "DBArchRnge_SKN"
    target = "V2"
    sheet = "dbarchrnge.tga"
    own_textures = {"dbarchrnge.tga": "DBArchRngT.tga"}
    house_tags = ()                 # the cloth stays in V2: the house-colour model is shown at every level
    bake_hidden = NOT_BAKED
    views = {                                   # the whole building at level 3, and the tower close
        "rts": ((16, 6, 62), 400, 50, -38, 50),
        "close": ((31, 40, 104), 175, 16, -34, 45),
        "ingame": ((10, 0, 45), 900, 53, -62, 50),
    }

    def design(self, kit):
        s = []
        s += self._piers()                     # 1. the legs in stone piers, rune belts
        s += self._course()                    # 2. the storey's stepped course, hexagon frieze
        s += self._skin()                      # 3. stone walls with pointed arrow slits
        s += self._crown()                     # 4. corbelled cornice, crown ring, rune belt
        s += self._crown_top(kit)              # 5. corner step pyramids, crown gables
        s += self._spire()                     # 6. stepped spire, bronze collar, gilded point
        s += self._banners(kit)                # 7. banners between the slits
        return s

    # ------------------------------------------------------------------ 1. piers
    @staticmethod
    def _piers():
        """From the post bastions' tops (z 61.4) into the crown: a bronze foot, a rune belt at the
        loggia (z 70..72.6) and one at the arrow slits (z 97.2..99.8), stone between; bands grow
        only on the sides allowed (PIERS)."""
        from sagekit.blender.geometry import box_rings, loft
        out = []
        for (x0, x1, y0, y1), (gx0, gx1, gy0, gy1) in PIERS:
            def R(z, e):
                return box_rings((x0 - e * gx0, x1 + e * gx1), (y0 - e * gy0, y1 + e * gy1), z, 0)
            rings, tags = [R(61.0, 0.0), R(61.0, 0.45), R(62.4, 0.45), R(62.4, 0.0)], ["stoneB", "trim", "top"]
            for za, zb, zc, zd in ((69.4, 70.0, 72.6, 73.2), (96.6, 97.2, 99.8, 100.4)):
                rings += [R(za, 0.0), R(za, 0.35), R(zb, 0.35), R(zc, 0.35), R(zd, 0.35), R(zd, 0.0)]
                tags += ["stoneB" if za < 80 else "stoneA", "stoneB", "trim", "rune", "trim", "top"]
            rings.append(R(113.0, 0.0))
            tags.append("stoneA")
            out.append(loft(rings, tags, cap0=("stoneB", False), cap1=("top", False)))
        return out

    # ------------------------------------------------------------------ 2. storey course
    @staticmethod
    def _course():
        """Under the storey, spanning the piers over the open loggia: a stepped soffit, a bronze
        fillet, stone, the hexagon frieze and a bronze coping the walls stand on."""
        from sagekit.blender.geometry import loft
        c = COURSE
        r1, r2 = inset(c, 1.3), inset(c, 0.6)
        rings = [ring(r1, Z_COURSE), ring(r1, 77.4), ring(r2, 77.4), ring(r2, 78.4), ring(c, 78.4), ring(c, 84.6),
                 ring(c, 87.2), ring(inset(c, -0.2), 87.2), ring(inset(c, -0.2), 87.8)]
        tags = ["trim", "stoneB", "stoneB", "stoneB", "stoneA", "hex", "trim", "trim"]
        return [loft(rings, tags, cap0=("stoneB", True), cap1=("top", True))]

    # ------------------------------------------------------------------ 3. walls, arrow slits
    @staticmethod
    def _skin():
        """Each face between the piers: a stone wall from the course to the cornice, over EA's
        timber wall, cut by a pointed arrow slit at each pair of arrow bones (EA's window shows
        through, dark), with a bronze reveal and a proud stepped frame: sill, jambs, pointed hood."""
        from sagekit.blender.geometry import prism_uz
        s0, s1, s2, h = SLIT
        z0, z1 = Z_SKIN, Z_CORNICE
        out = []
        for name, a, t, n, u0, u1, back in faces():
            cs = sorted(c if t.x + t.y > 0 else -c for c in SLITS.get(name, ()))

            def P(poly, tags, d0=back, d1=0.0, front="stoneA", rear=None):
                out.append(prism_uz(a, t, n, poly, d0, d1, tags, front, rear))
            if not cs:
                P([(u0, z0), (u1, z0), (u1, z1), (u0, z1)], [None, None, None, None])
                continue
            P([(u0, z0), (u1, z0), (u1, s0), (u0, s0)], [None, None, "top", None])
            edges = [u0] + [x for c in cs for x in (c - h, c + h)] + [u1]
            for i in range(0, len(edges), 2):         # the wall between openings, to the jamb tops
                e, f = edges[i], edges[i + 1]
                P([(e, s0), (f, s0), (f, s1), (e, s1)], [None, None if f == u1 else "trim", None, None if e == u0 else "trim"])
            for i in range(len(cs) + 1):              # the spandrels: jamb tops, arch, up to the cornice
                left, right = (cs[i - 1] if i else None), (cs[i] if i < len(cs) else None)
                poly, tags = [], []
                if left is None:
                    poly, tags = [(u0, s1)], [None]
                else:
                    poly, tags = [(left, s2), (left + h, s1)], ["trim", None]
                if right is None:
                    poly += [(u1, s1), (u1, z1)]
                    tags += [None, None]
                else:
                    poly += [(right - h, s1), (right, s2), (right, z1)]
                    tags += ["trim", None, None]
                poly.append((left if left is not None else u0, z1))
                tags.append(None)
                P(poly, tags)
            for c in cs:                              # the frame round each slit
                P([(c - h - 1.0, s0 - 0.7), (c + h + 1.0, s0 - 0.7), (c + h + 1.0, s0), (c - h - 1.0, s0)],
                  ["stoneB", "stoneB", "top", "stoneB"], d0=0.0, d1=1.0, front="trim")
                for sg in (-1, 1):                    # jambs (inner side: the bronze reveal) and hood halves
                    P([(c + sg * h, s0), (c + sg * (h + 0.8), s0), (c + sg * (h + 0.8), s1), (c + sg * h, s1)],
                      [None, "stoneB", None, "trim"], d0=0.0, d1=0.8, front="stoneB")
                    P([(c + sg * h, s1), (c + sg * (h + 0.8), s1), (c, s2 + 1.0), (c, s2)],
                      [None, "trim", None, "trim"], d0=0.0, d1=0.8, front="stoneB")
        return out

    # ------------------------------------------------------------------ 4. crown
    @staticmethod
    def _crown():
        """One stepped solid from the walls' top: a corbelled cornice (bronze band, hexagon frieze)
        out to the crown ring - over the piers, far over the east and west faces, where EA's eave
        horns end - then its wall, the gold rune belt on blue enamel, and a sloped bronze coping."""
        from sagekit.blender.geometry import loft
        C, Ci = CROWN, inset(CROWN, 0.3)
        rings = [ring(SKIN, Z_CORNICE), ring(lerp(SKIN, Ci, 0.3), 104.6), ring(lerp(SKIN, Ci, 0.3), 105.4),
                 ring(lerp(SKIN, Ci, 0.65), 106.4), ring(lerp(SKIN, Ci, 0.65), 107.2), ring(Ci, Z_CROWN),
                 ring(Ci, 113.0), ring(C, 113.0), ring(C, 113.6), ring(C, 115.8), ring(C, 116.4),
                 ring(inset(C, 0.35), Z_TOP)]
        tags = ["stoneB", "trim", "stoneB", "hex", "stoneB", "stoneA", "stoneB", "trim", "rune", "trim", "top"]
        return [loft(rings, tags, cap0=("stoneB", False), cap1=("top", True))]

    @staticmethod
    def _crown_top(kit):
        """The fortress crown: a step pyramid at each corner; mid-side, the range's own tower-crown
        gable at this crown's scale (bronze band, triangle-frieze tier, stone point, gilded finial),
        narrower east and west where the pyramids are closer. All inside the coping; the spire
        stands clear of them."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        x0, x1, y0, y1 = inset(CROWN, 0.35)
        out = []
        for cx in (x0 + 4.0, x1 - 4.0):
            for cy in (y0 + 4.0, y1 - 4.0):
                out += kit.step_pyramid(cx, cy, dz=Z_TOP - 110.8)
        z = Z_TOP
        for a, t, n, L, w in ((V((x0, y0, 0)), V((1, 0, 0)), V((0, -1, 0)), x1 - x0, 7.4),
                              (V((x1, y1, 0)), V((-1, 0, 0)), V((0, 1, 0)), x1 - x0, 7.4),
                              (V((x1, y0, 0)), V((0, 1, 0)), V((1, 0, 0)), y1 - y0, 5.8),
                              (V((x0, y1, 0)), V((0, -1, 0)), V((-1, 0, 0)), y1 - y0, 5.8)):
            m, v = L / 2, w - 1.8
            for poly, dd, tags, front in (
                    ([(m - w, z), (m + w, z), (m + w, z + 1.4), (m - w, z + 1.4)], (-2.6, 0.0),
                     [None, "trim", "top", "trim"], "trim"),
                    ([(m - v, z + 1.4), (m + v, z + 1.4), (m + v, z + 4.6), (m - v, z + 4.6)], (-2.4, -0.2),
                     [None, "stoneB", "top", "stoneB"], "tri"),
                    ([(m - v, z + 4.6), (m + v, z + 4.6), (m, z + 4.6 + v * 1.1)], (-2.4, -0.2),
                     [None, "top", "top"], "stoneA")):
                out.append(prism_uz(a, t, n, poly, dd[0], dd[1], tags, front, "stoneB"))
            zf = z + 4.6 + v * 1.1
            out.append(prism_uz(a, t, n, [(m - 0.9, zf - 1.6), (m + 0.9, zf - 1.6), (m + 0.9, zf + 0.2), (m - 0.9, zf + 0.2)],
                                -2.2, -0.4, ["stoneB", "trim", "top", "trim"], "trim", "trim"))
            out.append(prism_uz(a, t, n, [(m - 0.9, zf + 0.2), (m + 0.9, zf + 0.2), (m, zf + 2.2)], -2.2, -0.4,
                                [None, "trim", "trim"], "trim", "trim"))
        return out

    # ------------------------------------------------------------------ 6. spire
    @staticmethod
    def _spire():
        """Tiers stepping in with EA's pyramid (each tier's foot 0.45 outside it, so the shingles
        are inside the stone), a bronze collar and a gilded point."""
        from sagekit.blender.geometry import loft
        cx, cy, zb, za, hx, hy = PYR

        def R(z):
            k = (za - z) / (za - zb)
            return (cx - hx * k - 0.45, cx + hx * k + 0.45, cy - hy * k - 0.45, cy + hy * k + 0.45)
        rings, tags = [], []
        for i, (z0, z1) in enumerate(zip(TIERS, TIERS[1:])):
            r = R(z0) if i < len(TIERS) - 2 else inset(R(z0), -0.2)     # the last: a bronze collar
            if rings:
                tags.append("top")                      # the tread of the tier below
            rings += [ring(r, z0), ring(r, z1)]
            tags.append(TIER_TAGS[i])
        out = [loft(rings, tags, cap0=("stoneB", False), cap1=("top", True))]
        z = TIERS[-1]
        out.append(point(cx - 1.25, cx + 1.25, cy - 1.25, cy + 1.25, z, z + 9.3))
        return out

    # ------------------------------------------------------------------ 7. banners
    @staticmethod
    def _banners(kit):
        """A banner between the two slits of each face the arrows use, under the cornice."""
        out = []
        for name, a, t, n, u0, u1, back in faces():
            cs = SLITS.get(name)
            if not cs:
                continue
            u = sum(c if t.x + t.y > 0 else -c for c in cs) / 2
            out += kit.banner(a, t, n, u, 102.6, 3.0, 12.0)
        return out

    def emphasis(self, c, n):
        if c.z > 103.0:
            return 1.45                      # cornice, crown, spire: what the RTS camera sees most
        if c.z > 87.0:
            return 1.3                       # the storey walls and slits
        return 1.0
