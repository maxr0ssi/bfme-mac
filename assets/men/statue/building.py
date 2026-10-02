"""The Gondor statue (GondorStatue, GondorHeroStatue): EA's guardsman in his cloak, sword planted,
kept whole with the White Tree relief on his pedestal's front; the pedestal becomes a monument of
Minas Tirith. Four corner piers stand out from the die (a moulded base, a steel band, a capital
under the cornice's flare), a moulded frame with a steel keystone rings EA's relief panel, a
moulded step lifts the figure's plinth, White Tree shields hang on the die's plain sides, steel
braziers with gilt flames stand on the front corners of the cornice and pinnacles with steel orbs
on the back ones, and a house-colour banner hangs on the back face of the die. The figure is not
touched.

EA's GPHealstue.GPHEALSTUE (mesh = model coordinates; the figure faces -y): a base block filling
the footprint x -7.86..9.0, y -8.44..9.37 up to z 3.58, sloping in to the die (x -6.5..7.63, y
-6.99..7.92) at 5.1; the die to 20.27, its front holding a recessed panel (x -4.91..6.04, z
6.97..18.41, the White Tree relief); a cornice flaring back out to the footprint by 23.35, upright
to 25.37; a plate (x -5.35..6.48, y -5.78..6.71) and the figure's plinth (x -4.55..5.69, y
-4.94..5.87) to 26.57; the figure from 26.2 to 65.2, its cloak's hem out to x -6.75..7.14, y
-4.11..6.15 at z 27..30, so the cornice's corners stay free."""
from sagekit.building import Building

from ..style import MenStyle

DIE = (-6.5, 7.63, -6.99, 7.92)
FOOT = (-7.86, 9.0, -8.44, 9.37)
PANEL = (-4.91, 6.04, 6.97, 18.41)          # x0, x1, z0, z1 on the die's front (y = -6.99)
TOP = 25.37


class Statue(Building):
    style = MenStyle()
    source = "GPHealstue"
    target = "GPHEALSTUE"
    sheet = "GUHeroStat.tga"
    sheet_normal = "GUHeroStat_NRM.tga"
    own_textures = {"GUHeroStat.tga": "GUHeroStaH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    # cut along EA's build-up pieces, the figure kept slivers and 2.9% open backs (sagekit/lifecycle.py `fill`)
    lifecycle = {"GPHealstue_A": {"fill": True}}
    # the figure is an organic body: unwrapped whole, its cloak's folds flip over one another in our
    # layout (0.24 % of texels twice); seamed at EA's own island borders and turns over 20 degrees
    facet_islands = 20
    views = {
        "rts": ((0.6, 0.5, 32.6), 153, 50, -38, 50),
        "close": ((0.6, 0.5, 30.0), 100, 24, -30, 45),
        "pedestal": ((0.6, 0.5, 15.0), 62, 14, -75, 45),
        "back": ((0.6, 0.5, 18.0), 70, 18, 105, 45),
        "ingame": ((0.6, 0.5, 32.6), 348, 53, -62, 50),
    }

    def design(self, kit):
        out = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                out += self._pier(sx, sy)
        out += self._frame(kit)
        out += self._top(kit)
        out += self._banner(kit)
        out += self._shields(kit)
        return out

    @staticmethod
    def _pier(sx, sy):
        """A corner pier standing out from the die, inside the footprint (0.08 in): a moulded base
        on the plinth's slope, the shaft, a steel band, a capital tucked under the cornice's flare."""
        from sagekit.blender.geometry import box_rings, loft
        x0, x1 = (DIE[1] - 1.0, FOOT[1] - 0.08) if sx > 0 else (FOOT[0] + 0.08, DIE[0] + 1.0)
        y0, y1 = (DIE[3] - 1.0, FOOT[3] - 0.08) if sy > 0 else (FOOT[2] + 0.08, DIE[2] + 1.0)

        def R(e, z):
            return box_rings((x0 + e, x1 - e), (y0 + e, y1 - e), z, 0.0)
        rings = [R(0.0, 3.3), R(0.0, 4.3), R(0.12, 4.6), R(0.28, 4.6), R(0.28, 11.9), R(0.18, 11.9), R(0.18, 12.7),
                 R(0.28, 12.7), R(0.28, 20.6), R(0.15, 20.6), R(0.0, 21.3), R(0.0, 22.2)]
        tags = ["stoneB", "course", "top", "stoneA", "top", "trim", "trim", "stoneA", "top", "course", "course"]
        return [loft(rings, tags, cap0=("stoneB", False), cap1=("top", True))]

    @staticmethod
    def _frame(kit):
        """A moulded frame round EA's relief panel on the die's front, a steel keystone at its head."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz
        A, T, N = V((0.0, DIE[2], 0)), V((1, 0, 0)), V((0, -1, 0))
        x0, x1, z0, z1 = PANEL
        w, d = 0.45, 0.4
        out = [prism_uz(A, T, N, [(x0 - w, z0 - w), (x0, z0 - w), (x0, z1 + w), (x0 - w, z1 + w)], -0.2, d,
                        ["stoneB", "stoneB", "top", "stoneB"], "course", None),
               prism_uz(A, T, N, [(x1, z0 - w), (x1 + w, z0 - w), (x1 + w, z1 + w), (x1, z1 + w)], -0.2, d,
                        ["stoneB", "stoneB", "top", "stoneB"], "course", None),
               prism_uz(A, T, N, [(x0, z1), (x1, z1), (x1, z1 + w), (x0, z1 + w)], -0.2, d,
                        ["stoneB", None, "top", None], "course", None),
               prism_uz(A, T, N, [(x0 - w - 0.2, z0 - w - 0.5), (x1 + w + 0.2, z0 - w - 0.5), (x1 + w + 0.2, z0 - w),
                                  (x0 - w - 0.2, z0 - w)], -0.2, d + 0.2, ["stoneB", "stoneB", "top", "stoneB"], "course", None)]
        u = (x0 + x1) / 2
        out.append(prism_uz(A, T, N, [(u - 0.55, z1 - 0.4), (u + 0.55, z1 - 0.4), (u + 0.75, z1 + 1.1), (u - 0.75, z1 + 1.1)],
                            -0.2, d + 0.25, ["trim"] * 4, "trim", None))
        return out

    @staticmethod
    def _top(kit):
        """A moulded step under the figure's plinth; braziers on the front corners, pinnacles on the
        back ones (the figure's hem stays inside |y| 4.1..6.2 there)."""
        from sagekit.blender.geometry import box, box_rings, loft

        from ..shapes import turned
        out = [box(-5.95, 7.08, -6.38, 7.3, TOP - 0.2, TOP + 0.55, ["stoneB", "course", "course", "course"], cap1=("top", True))]
        for sx in (-1, 1):
            cx = FOOT[1] - 1.3 if sx > 0 else FOOT[0] + 1.3
            cy = FOOT[3] - 1.3
            out += kit.pinnacle(cx, cy, TOP - 0.1, TOP + 4.2, half=0.95, spire=4.8)
            cy = FOOT[2] + 1.3
            h = 0.9
            rings = [box_rings((cx - h, cx + h), (cy - h, cy + h), z, 0.2) for z in (TOP - 0.1, TOP + 2.4)]
            rings += [box_rings((cx - h - 0.3, cx + h + 0.3), (cy - h - 0.3, cy + h + 0.3), z, 0.25) for z in (TOP + 2.4, TOP + 3.0)]
            out.append(loft(rings, ["stoneA", "course", "course"], cap0=("stoneB", False), cap1=("top", True)))
            zb = TOP + 3.0
            out.append(turned(cx, cy, [(0.45, zb - 0.1), (0.45, zb + 0.5), (1.2, zb + 1.6), (1.2, zb + 2.0), (0.9, zb + 2.0)],
                              ["trim", "trim", "trim", "trim"], k=8, cap0=("trim", False), cap1=("iron", True)))
            out.append(turned(cx, cy, [(0.85, zb + 1.9), (0.55, zb + 3.3), (0.0, zb + 5.2)], ["gilt", "gilt"], k=6,
                              cap0=("gilt", False), cap1=("gilt", False)))
        return out

    @staticmethod
    def _shields(kit):
        """White Tree shields on the die's plain side faces, between the piers."""
        from mathutils import Vector as V

        from ..keep import tower
        yc = (DIE[2] + DIE[3]) / 2
        out = []
        for x, n in ((DIE[1], V((1, 0, 0))), (DIE[0], V((-1, 0, 0)))):
            out += tower.shield(kit, V((x, yc, 0)), V((-n.y, n.x, 0)), n, 0.0, 8.4, 2.6, 8.6, d=-0.2)
        return out

    @staticmethod
    def _banner(kit):
        """The house-colour banner on the back face of the die, between the back piers."""
        from mathutils import Vector as V
        a, t, n = V((0.57, DIE[3], 0)), V((-1, 0, 0)), V((0, 1, 0))
        return kit.banner(a, t, n, 0.0, 19.4, 5.0, 12.5, d=0.6)

    def emphasis(self, c, n):
        return 1.3 if c.z < 32 else 1.0
