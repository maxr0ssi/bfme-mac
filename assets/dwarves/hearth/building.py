"""Dwarven hearth (DwarvenHearth): the economy building - a walled fire bed under a diagonal
gabled gantry on two pillars, on a star-pointed plate. Measurements in DWARFHEARTH mesh
coordinates, taken from the original model (see README)."""
import math

from sagekit.building import Building

from ..style import DwarvenStyle

R2 = math.sqrt(0.5)
# the gantry runs diagonally, pillar (-8, 8) to pillar (8, -8): u along T, w across (along N)
T, N = (R2, -R2), (R2, R2)
PILLARS = [(-7.95, 7.95), (7.95, -7.95)]        # pillar centres (4 x 4, z 7.7 .. 21.7)
BEAM_TOP, BEAM_FLAT = 33.8, 5.1                  # flat top at z 33.8 for |u| <= 5.1, sloping to the caps
RIM_OUT, SIDE = 10.55, 7.0                         # fire ring: outer faces, straight half-length
STAR_POINTS = [(20.0, 0.0), (-20.0, 0.0), (0.0, 20.0), (0.0, -20.0)]   # diamond pads on the plate's axes
BANNER_DIAG = 22.6                 # banner poles at +-(16, 16): distance along the (1, 1) diagonal


class Hearth(Building):
    style = DwarvenStyle()
    source = "DBHearth"
    target = "DWARFHEARTH"
    sheet = "DBHearth.tga"
    sheet_normal = None            # DBHearth has no normal map

    def design(self, kit):
        solids = []
        solids += self._gantry_crown()
        solids += self._rim()
        for cx, cy in STAR_POINTS:
            solids += self._marker(cx, cy)
        solids += self._banners(kit)
        return solids

    @staticmethod
    def _banners(kit):
        """Two Erebor-blue banner poles on the plate's free diagonal corners (+,+) and (-,-), left and
        right of the fire ring as the camera sees it, their banners facing the camera (+X, -Y). The
        feet stand outside the ring's corner buttresses (x + y <= 27 at the ground) and inside the
        tile border (17.7); the house-colour banner's corner (+X, -Y) and the fire bed stay clear."""
        from mathutils import Vector as V
        n, t = V((R2, -R2, 0)), V((R2, R2, 0))
        s = []
        for sgn in (1, -1):
            s += kit.banner_pole(V((0, 0, 0)), t, n, sgn * BANNER_DIAG, 26.0, 4.2, 13.0)
        return s

    @staticmethod
    def _rim():
        """The fire ring (a 3.1-wide wall, top z 7.8, outer faces x/y = +-10.5, inner +-7.4): a bronze
        coping on each straight side with a small stepped-triangle parapet at its middle; stepped
        pedestals round the pillar feet and stepped pyramids on the two free corners."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import loft, prism_uz
        out = []
        for nx, ny in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = V((nx, ny, 0))
            t = V((-ny, nx, 0))
            a = n * RIM_OUT
            out.append(prism_uz(a, t, n, [(-SIDE, 7.5), (SIDE, 7.5), (SIDE, 8.5), (-SIDE, 8.5)], -3.4, 0.35,
                                [None, "trim", "top", "trim"], "trim|a", "trim|a"))
            out.append(prism_uz(a, t, n, [(-3.2, 8.5), (3.2, 8.5), (3.2, 9.7), (-3.2, 9.7)], -1.6, 0.2,
                                [None, "stoneB", "top", "stoneB"], "tri|a", "stoneA"))
            out.append(prism_uz(a, t, n, [(-2.0, 9.7), (2.0, 9.7), (2.0, 10.7), (-2.0, 10.7)], -1.3, 0.0,
                                [None, "stoneB", "top", "stoneB"], "stoneA", "stoneA"))
            out.append(prism_uz(a, t, n, [(-2.0, 10.7), (2.0, 10.7), (0.0, 12.3)], -1.3, 0.0,
                                [None, "top", "top"], "stoneA", "stoneA"))

        def block(c, q, p, tiers, apex=None):
            """Stacked battered boxes in the frame (q radial, p across) round c; optional point."""
            res = []

            def ring(hq, hp, z):
                return [c + q * (sq * hq) + p * (sp * hp) + V((0, 0, z)) for sq, sp in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            for (hq0, hp0, z0), (hq1, hp1, z1), tg in tiers:
                res.append(loft([ring(hq0, hp0, z0), ring(hq1, hp1, z1)], [tg], cap0=("stoneB", False), cap1=("top", True)))
            if apex:
                hq, hp, z = tiers[-1][1]
                res.append(loft([ring(hq, hp, z), [c + V((0, 0, apex))] * 4], ["trim"], cap0=("top", False), cap1=("top", False)))
            return res
        for (cx, cy), sgn in (((-8.6, -8.7), -1), ((8.6, 8.5), 1)):       # free corners: over the old tips
            q = V((sgn * R2, sgn * R2, 0))
            c = V((cx, cy, 0)) - q * 0.4
            out += block(c, q, V((-q.y, q.x, 0)), [((1.5, 2.2, 7.5), (1.35, 2.0, 9.7), "stoneB"),
                                                  ((1.0, 1.5, 9.7), (0.9, 1.35, 11.0), "stoneA")], apex=12.9)
        t = V((T[0], T[1], 0))
        for s in (1, -1):                                                  # pillar feet: stepped pedestals
            c = t * (s * -11.4)
            out += block(c, t, V((N[0], N[1], 0)), [((1.75, 2.0, 7.5), (1.65, 1.9, 9.6), "stoneB"),
                                                    ((1.8, 2.05, 9.6), (1.8, 2.05, 10.2), "trim"),
                                                    ((1.6, 1.8, 10.2), (1.55, 1.75, 11.0), "stoneA")])
        return out

    @staticmethod
    def _marker(cx, cy):
        """A squat stepped pyramid on a star point (the fortress's crown corner, at ground scale)."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import box_rings, loft
        out = []
        tiers = [(2.9, 2.6, -0.5, 3.6, "stoneB"), (2.1, 1.95, 3.6, 5.4, "stoneA"), (1.45, 1.35, 5.4, 6.6, "stoneA")]
        for h0, h1, z0, z1, tg in tiers:
            r0 = box_rings((cx - h0, cx + h0), (cy - h0, cy + h0), z0, 0.3)
            r1 = box_rings((cx - h1, cx + h1), (cy - h1, cy + h1), z1, 0.3)
            out.append(loft([r0, r1], [tg], cap0=("top", False), cap1=("top", True)))
        r0 = box_rings((cx - 1.35, cx + 1.35), (cy - 1.35, cy + 1.35), 6.6, 0.25)
        out.append(loft([r0, [V((cx, cy, 8.2))] * len(r0)], ["trim"], cap0=("top", False), cap1=("top", False)))
        return out

    @staticmethod
    def _gantry_crown():
        """A stepped gable over the gantry's flat top and stepped shoulders down its slopes."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import loft, prism_uz
        a, t, n = V((0, 0, 0)), V((T[0], T[1], 0)), V((N[0], N[1], 0))
        z0 = BEAM_TOP
        out = [
            prism_uz(a, t, n, [(-5.8, z0 - 1.2), (5.8, z0 - 1.2), (5.8, z0 + 1.0), (-5.8, z0 + 1.0)], -2.8, 2.8,
                     ["stoneB", "trim", "top", "trim"], "rune|a", "rune|a"),
            prism_uz(a, t, n, [(-4.4, z0 + 1.0), (4.4, z0 + 1.0), (4.4, z0 + 2.6), (-4.4, z0 + 2.6)], -2.0, 2.0,
                     [None, "stoneB", "top", "stoneB"], "tri|a", "tri|a"),
            prism_uz(a, t, n, [(-4.4, z0 + 2.6), (4.4, z0 + 2.6), (0.0, z0 + 5.6)], -1.7, 1.7,
                     [None, "top", "top"], "stoneA", "stoneA"),
        ]
        for s in (1, -1):
            for u0, u1, zb, zt in ((5.8, 7.2, 28.5, 32.4), (7.2, 8.9, 26.0, 29.8)):
                poly = [(s * u0, zb), (s * u1, zb), (s * u1, zt), (s * u0, zt)]
                if s < 0:
                    poly = [(s * u1, zb), (s * u0, zb), (s * u0, zt), (s * u1, zt)]
                out.append(prism_uz(a, t, n, poly, -2.9, 2.9, ["stoneB", "stoneB", "top", "stoneB"], "stoneA", "stoneA"))
            uc = s * 10.8                               # over each pillar's capital: a stepped finial
            for h0, h1, w0, w1, zb, zt, tg in ((1.7, 1.6, 2.7, 2.6, 25.2, 26.9, "trim"),
                                               (1.2, 1.1, 2.0, 1.9, 26.9, 28.2, "stoneA")):
                rings = [[a + t * (uc + du * h) + n * (dw * w) + V((0, 0, z)) for du, dw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                         for h, w, z in ((h0, w0, zb), (h1, w1, zt))]
                out.append(loft(rings, [tg], cap0=("stoneB", False), cap1=("top", True)))
            top = [a + t * (uc + du * 1.1) + n * (dw * 1.9) + V((0, 0, 28.2)) for du, dw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            out.append(loft([top, [a + t * uc + V((0, 0, 30.4))] * 4], ["trim"], cap0=("top", False), cap1=("top", False)))
        return out
