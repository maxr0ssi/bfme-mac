"""The fortress's oil-cask upgrade (FORTRESS_IMPROVEMENT_2, Draw ModuleTag_MainOilStruct of
DwarvenFortressCitadel): the four corner towers become oil batteries.

On each tower head: a stepped oil well round EA's hatch (bronze step, rune band, gold rim), a
great upright cask on a stone plinth (gold hoops, a rune belt) and a stone cradle holding three
bronze-hooped casks lying with their gilded lids toward the well. On each tower's outer face, where
the burning oil pours out: a stepped oil gate from the ground to z 57.2 - plinth, a stone prow, a
hexagon belt, a bronze spout housing with a rune belt, a pouring window behind a gold grille, a
bronze hood, a rune lintel and a pointed gable with a gold finial (under the fortress's tower
banners, which end at z 58).

EA's add-on (mesh DBFRBARREL, drawn at the fortress's origin, no skinning) per tower: an octagonal
hatch frame on the head's floor (z 104.07..106.01), an upright octagonal cask in the inner corner
(to z 111.57), and on the outer face a pointed slab (|u| 9.2, 1.77 proud, to z 53.07) with a
pouring window (|u| 6.41, z 32.0..42.57), a sill, a niche and a ground spike (the bounding box's
|y| limit). Every new piece encloses EA's, so none of it shows but the hatch's dark mouth and the
window. The oil dwarves (DUMMY bones, z 104.05) stand at (-1.95, +5.9) in tower-local (a, b) below:
nothing new within 2.4 of them. The fortress's head floor is z 104.4, its crown's inner faces at
|a|, |b| 10.85, its corner step pyramids start at z 110.8 above |a|, |b| > 8.95; the other
fortress banners hang on the shaft faces above z 58. All measurements in DBFRBARREL mesh
coordinates (= the fortress's), taken from the original model."""
import math

from sagekit.atlas import Region
from sagekit.building import Building

from ..atlas import DwarvenAtlas
from ..style import DwarvenStyle


class CaskAtlas(DwarvenAtlas):
    """The faction atlas plus three painted motifs of DBFortress1 (appended, so the faction's own tag
    indices are unchanged): the plank boards (the tower roofs' wood) for cask staves, the wooden
    door with its gold hexagon for cask lids, and the gold grille over darkness for the pouring
    window (EA's dark window is repainted as stone by the paint stack, so it is covered)."""
    regions = dict(DwarvenAtlas.regions,
                   cask=Region((55, 133, 89, 167), Region.STRETCH),
                   lid=Region((432, 18, 485, 80), Region.STRETCH),
                   grate=Region((141, 187, 192, 225), Region.STRETCH))


class CaskStyle(DwarvenStyle):
    """The Dwarven style (palette, layers, shapes) with the cask atlas."""
    atlas = CaskAtlas()


# per tower: centre, a/b axis signs (a toward EA's cask, b toward the courtyard), EA's hatch centre
# and cask centre (world), the outer face's plane y, its outward sign, the face's centre x and the
# depth the bounding box leaves in front of it
TOWERS = [
    dict(c=(35.95, -39.25), sa=1, sb=1, hatch=(35.95, -44.72), cask=(44.15, -32.245), fy=-52.92, out=-1, fx=35.95, dmax=6.0),
    dict(c=(35.95, 38.6), sa=-1, sb=-1, hatch=(35.95, 44.185), cask=(27.695, 31.71), fy=52.29, out=1, fx=35.95, dmax=6.01),
    dict(c=(-37.45, 38.6), sa=-1, sb=-1, hatch=(-37.46, 44.185), cask=(-45.715, 31.71), fy=52.29, out=1, fx=-37.475, dmax=6.01),
    dict(c=(-37.45, -39.25), sa=1, sb=1, hatch=(-37.48, -44.72), cask=(-29.22, -32.245), fy=-52.92, out=-1, fx=-37.475, dmax=6.0),
]
FLOOR = 104.4


def cask(c, axis, L, R, n, lying, belt="trim"):
    """A bulging cask of n staves along `axis` (unit), centre c: gold end hoops, wood staves, a
    middle belt (`belt` tag), gilded wooden lids. Lying casks keep a flat stave at the bottom
    (n even). Hexagonal like EA's casks and the Dwarven kit's other shapes."""
    from mathutils import Vector as V
    from sagekit.blender.geometry import loft
    axis = V(axis).normalized()
    e1 = V((1, 0, 0)) if abs(axis.z) > 0.9 else V((0, 0, 1))
    e2 = axis.cross(e1).normalized()
    e1 = e2.cross(axis).normalized()
    c = V(c)

    def ring(s, r):
        return [c + axis * s + (e1 * math.cos(2 * math.pi * (k + 0.5) / n) + e2 * math.sin(2 * math.pi * (k + 0.5) / n)) * r * R
                for k in range(n)]
    h = L / 2
    st = [(-h, 0.88), (-h + 0.11 * L, 0.97), (-0.11 * L, 1.0), (-0.11 * L, 1.03), (0.11 * L, 1.03), (0.11 * L, 1.0),
          (h - 0.11 * L, 0.97), (h, 0.88)]
    wood = "cask|v" if not lying else "cask|a"
    tags = ["trim", wood, "trim", belt, "trim", wood, "trim"]
    return loft([ring(s, r) for s, r in st], tags, cap0=("lid", True), cap1=("lid", True))


class FortressBarrels(Building):
    style = CaskStyle()
    source = "DBFRBarrel"
    target = "DBFRBARREL"
    sheet = None                                                # the faction atlas DBFortress1
    own_textures = {"DBFortress1.tga": "DBFortressB.tga"}
    parts = ("ModuleTag_MainOilStruct",)
    tri_budget = 5000
    views = {
        "rts": ((0, 0, 60), 330, 50, -38, 50),
        "close": ((36, -39, 106), 48, 42, -58, 45),
        "gate": ((36, -54, 28), 95, 12, -72, 40),
        "ingame": ((0, 0, 50), 900, 53, -62, 50),
    }

    def design(self, kit):
        solids = []
        for tw in TOWERS:
            solids += self._head(tw)
            solids += self._oil_gate(tw)
        return solids

    # ------------------------------------------------------------------ tower head
    @staticmethod
    def _head(tw):
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft
        cx, cy = tw["c"]
        sa, sb = tw["sa"], tw["sb"]

        def W(a, b):                                    # tower-local (a, b) -> world (x, y)
            return cx + sa * a, cy + sb * b

        def box(a0, a1, b0, b1, z, ch):
            (x0, y0), (x1, y1) = W(a0, b0), W(a1, b1)
            return box_rings(sorted((x0, x1)), sorted((y0, y1)), z, ch)

        out = []
        # the oil well round EA's hatch (octagon |x| 7.23, |y| 4.23): base course, bronze step,
        # rune band, gold rim, and a bronze reveal down to EA's frame, whose dark mouth stays open
        hx, hy = tw["hatch"]

        def H(ex, ey, z, ch):
            return box_rings((hx - ex, hx + ex), (hy - ey, hy + ey), z, ch)
        rings = [H(8.45, 5.28, FLOOR, 1.3), H(8.45, 5.28, 105.2, 1.3), H(8.15, 5.02, 105.2, 1.25),
                 H(8.15, 5.02, 106.5, 1.25), H(8.4, 5.26, 106.5, 1.3), H(8.4, 5.26, 107.1, 1.3),
                 H(7.36, 4.36, 107.1, 1.1), H(7.36, 4.36, FLOOR, 1.1)]
        out.append(loft(rings, ["stoneB", "top", ["rune" if k % 2 == 0 else "trim" for k in range(8)], "trim", "trim",
                                "top", "trim"], cap0=("stoneB", False), cap1=("stoneB", False)))
        for sx in (-1, 1):                              # gold points on the well's two ends
            px, py = hx + sx * 7.9, hy
            r0 = box_rings((px - 0.5, px + 0.5), (py - 0.5, py + 0.5), 107.1, 0)
            out.append(loft([r0, [V((px, py, 108.9))] * 4], ["trim"], cap0=("trim", False), cap1=("trim", False)))

        # the great cask, enclosing EA's upright one (a hexagon: flats |x| 2.82, vertices |y| 3.25 at
        # z 106.78..109.18, 2.73 at its ends z 104.39 / 111.57) on a stepped plinth in the inner
        # corner. EA's cask sets the bounding box on the wall side, so there both keep one flat
        # (inside the crown's wall) and the new cask swells toward the tower's middle only.
        kx, ky = tw["cask"]
        wall = kx + sa * 2.814                  # EA's flat (46.968) less a hair
        pl = [box_rings(sorted((wall, wall - sa * 7.4)), (ky - 4.3, ky + 4.3), FLOOR, 0.9),
              box_rings(sorted((wall, wall - sa * 7.4)), (ky - 4.3, ky + 4.3), 105.0, 0.9),
              box_rings(sorted((wall, wall - sa * 7.0)), (ky - 4.0, ky + 4.0), 105.0, 0.8),
              box_rings(sorted((wall, wall - sa * 7.0)), (ky - 4.0, ky + 4.0), 105.6, 0.8)]
        out.append(loft(pl, ["stoneB", "top", "trim"], cap0=("stoneB", False), cap1=("top", True)))
        ap = 2.96

        def hx6(s, z):                          # hexagon, flats toward ±x, wall-side flat fixed
            r, c = ap * s / math.cos(math.pi / 6), wall - sa * ap * s
            return [V((c + r * math.cos(math.radians(30 + 60 * k)), ky + r * math.sin(math.radians(30 + 60 * k)), z))
                    for k in range(6)]
        st = [(0.92, 105.6), (0.97, 106.4), (1.0, 107.4), (1.04, 107.4), (1.04, 109.2), (1.0, 109.2),
              (0.97, 110.9), (0.92, 111.9)]
        out.append(loft([hx6(sc, z) for sc, z in st], ["trim", "cask|v", "trim", "rune", "trim", "cask|v", "trim"],
                        cap0=("lid", False), cap1=("lid", True)))

        # the cradle in the other inner corner: a stone bed, two saddles, three casks lying along b
        # (lids toward the well), clear of the oil dwarf at (-1.95, 5.9)
        out.append(loft([box(-10.85, -4.35, 3.7, 10.85, FLOOR, 0.5), box(-10.85, -4.35, 3.7, 10.85, 105.1, 0.5)],
                        ["stoneB"], cap0=("stoneB", False), cap1=("top", True)))
        for b0 in (4.8, 8.6):
            out.append(loft([box(-10.85, -4.6, b0, b0 + 1.0, 105.1, 0.2), box(-10.85, -4.6, b0, b0 + 1.0, 105.9, 0.2)],
                            ["trim"], cap0=("trim", False), cap1=("trim", True)))
        R, L = 1.5, 5.6
        ax = V((0, sb, 0))
        for a, z in ((-9.2, 107.17), (-6.1, 107.17), (-7.65, 109.6)):
            x, y = W(a, 7.2)
            out.append(cask((x, y, z), ax, L, R, 6, lying=True))
        return out

    # ------------------------------------------------------------------ outer face
    @staticmethod
    def _oil_gate(tw):
        """The oil gate on the tower's outer face, in (u along +x, d out of the face) from EA's slab
        plane: every piece encloses EA's (slab, niche, sill, window box, spike) but the window. The
        backs against the tower stay closed: the checks cast sky rays at this model alone."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import prism_uz
        a = V((tw["fx"], tw["fy"], 0))
        t, n = V((1, 0, 0)), V((0, tw["out"], 0))
        dm = tw["dmax"] - 0.005

        def P(poly, d0, d1, tags, front, back="stoneB", bat=0.0):
            return prism_uz(a, t, n, poly, d0, d1, tags, front, back, bat)

        def R(u0, u1, z0, z1):
            return [(u0, z0), (u1, z0), (u1, z1), (u0, z1)]
        S4 = [None, "stoneB", "top", "stoneB"]
        T4 = [None, "trim", "trim", "trim"]
        out = [
            P(R(-10.2, 10.2, 0.0, 2.8), 0, 3.4, S4, "stoneB"),                         # plinth
            P(R(-9.9, 9.9, 2.8, 3.6), 0, 3.2, T4, "trim"),
            P(R(-9.6, -6.4, 3.6, 44.2), 0, 2.4, S4, "pilaster"),                       # side pilasters
            P(R(6.4, 9.6, 3.6, 44.2), 0, 2.4, S4, "pilaster"),
            P(R(-6.4, 6.4, 3.6, 44.2), 0, 2.0, S4, "stoneA"),                          # the slab behind
            P(R(-5.4, 5.4, 3.6, 23.3), 0, 3.9, [None, "stoneB", None, "stoneB"], "stoneA"),  # lower panel
            P(R(-5.9, 5.9, 17.8, 20.6), 0, 4.3, ["trim"] * 4, "hex"),                  # hexagon belt
            P(R(-6.3, 6.3, 23.3, 24.1), 0, 4.5, T4, "trim"),                           # spout housing
            P(R(-6.0, 6.0, 24.1, 26.6), 0, 4.3, [None, "stoneB", None, "stoneB"], "stoneB"),
            P(R(-6.4, 6.4, 26.6, 29.4), 0, 4.6, ["trim", "trim", "trim", "trim"], "rune"),
            P(R(-6.0, 6.0, 29.4, 31.0), 0, 4.3, [None, "stoneB", None, "stoneB"], "stoneB"),
            P(R(-7.0, 7.0, 31.0, 31.7), 0, 4.8, T4, "trim"),                           # sill
            P(R(-2.2, 2.2, 30.4, 31.7), 4.3, 5.9, ["trim"] * 4, "trim"),                 # pouring lip
            P(R(-6.0, 6.0, 31.7, 43.0), 0, 3.3, [None] * 4, "grate"),                  # oil port grille
            P(R(-8.4, -6.0, 31.7, 43.0), 0, 4.0, [None, "trim", None, "stoneB"], "stoneA"),   # window jambs
            P(R(6.0, 8.4, 31.7, 43.0), 0, 4.0, [None, "stoneB", None, "trim"], "stoneA"),
            P(R(-8.9, 8.9, 43.0, 44.2), 0, 4.8, ["trim"] * 4, "trim"),  # hood
            P(R(-8.5, 8.5, 44.2, 47.4), 0, 4.2, [None, "stoneB", None, "stoneB"], "rune"),  # rune lintel
            P(R(-8.9, 8.9, 47.4, 48.2), 0, 4.6, ["trim", "trim", "top", "trim"], "trim"),
            P(R(-7.6, 7.6, 48.2, 49.6), 0, 3.6, S4, "stoneB"),                         # pointed gable
            P([(-7.6, 49.6), (7.6, 49.6), (0.0, 55.6)], 0, 3.2, [None, "top", "top"], "stoneA"),
            P([(-1.1, 54.6), (1.1, 54.6), (0.0, 57.2)], 2.6, 3.7, [None, "trim", "trim"], "trim", "trim"),  # finial
        ]
        # the stone prow at the foot (over EA's spike, whose tip is the bounding box's limit)
        prow = [(0.0, 0.0), (dm, 0.0), (dm, 8.0), (4.2, 14.2), (0.0, 15.2)]
        out.append(prism_uz(a, n, t, prow, -3.8, 3.8, [None, "stoneB", "top", "trim", "stoneB"], "stoneB", "stoneB"))
        return out

    def emphasis(self, c, n):
        return 1.35 if c.z > 100 else 1.0      # the tower heads: what the RTS camera sees
